"""Lee un ddf.md y lo convierte en piezas con ID, estado y referencias.

Lo usan ddf_indice.py, comprobar_ddf.py y unir_modulos.py. No tiene dependencias.

Una pieza es algo con ID estable del análisis:
  - ficha:    **RF-012 — Título**, **PAN-07 — …**, **ACT-03 — …** (hasta la siguiente ficha o título)
  - fila:     | RB-031 | … |, | P-004 | … |, | D-012 | … |, | INT-001 | … | (fuera de una ficha)
  - criterio: `CA-PAN-07.3` **Dado** …  (su «padre» es la ficha en la que está)
Las secciones 7 y 16 son derivadas (las regenera ddf_indice.py derivadas) y no definen piezas.
"""
import re, unicodedata
from dataclasses import dataclass, field

PREFIJOS = ["RF", "RB", "PAN", "ACT", "CU", "INT", "NOT", "P", "S", "D"]
ID_SIMPLE = r"(?:RF|RB|PAN|ACT|CU|INT|NOT|P|S|D)-\d+"
ID_CA = r"CA-(?:PAN|ACT|RF)-\d+\.\d+|CA-E2E-\d+"
RX_ID = re.compile(rf"(?<![\w-])(?:{ID_CA}|{ID_SIMPLE})(?![\w-]|\.\d)")
RX_RANGO = re.compile(rf"(?<![\w-])((?:RF|RB|PAN|ACT|INT|NOT|P)-)(\d+)`?\s+a\s+`?(?:\1)?(\d+)(?![\w.])")
RX_RANGO_CA = re.compile(r"(CA-(?:PAN|ACT|RF)-\d+)\.(\d+)`?\s+a\s+`?(?:\1\.)?(\d+)(?![\w.])")
RX_FICHA = re.compile(r"^\*\*(~~)?((?:RF|PAN|ACT|CU|INT|NOT)-\d+)(~~)?\s+—\s+(.+?)\*\*(.*)$")
RX_FILA = re.compile(rf"^\|\s*(~~)?({ID_SIMPLE})(~~)?\s*\|")
RX_CRITERIO = re.compile(rf"`({ID_CA})`[^`\n]{{0,40}}?\*\*Dado|~~`?({ID_CA})`?~~\s*(?:—\s*)?Anulad[oa] por")
RX_FUENTE = re.compile(r"FU-\d\d")
RX_SECCION = re.compile(r"^## (\d+)\.")
RX_MODULO_H3 = re.compile(r"^### (M\d+)\b")
RX_MODULO_EN_H2 = re.compile(r"—\s*(M\d+)\s*$")
SECCIONES_DERIVADAS = {"7", "16"}
ESTADOS = ["🔒", "✅", "🔶", "⚠️", "❓"]
NOMBRE_ESTADO = {"🔒": "Validado", "✅": "Decidido", "🔶": "Inferido", "⚠️": "Pendiente", "❓": "No definido"}


@dataclass
class Pieza:
    id: str
    tipo: str
    forma: str            # ficha | fila | criterio
    titulo: str
    seccion: str
    modulo: str
    ini: int              # línea (0-based) donde empieza
    fin: int              # línea siguiente a la última
    estado: str = ""      # emoji de ESTADOS, "Anulada", "Respondida", "Vigente", "Sustituida" o ""
    padre: str = ""
    refs: set = field(default_factory=set)
    fuentes: set = field(default_factory=set)
    hijos: list = field(default_factory=list)
    cabecera: str = ""    # fila de cabecera de la tabla (piezas de tipo fila)
    frag: str = ""        # criterios que comparten línea: su trozo de texto
    apariciones: list = field(default_factory=list)  # otras filas donde el ID abre fila

    @property
    def anulada(self):
        return self.estado in ("Anulada", "Respondida", "Sustituida")


def tipo_de(i):
    if i.startswith("CA-"):
        return "CA"
    return i.split("-")[0]


def ids_en(texto):
    """IDs citados en un texto, expandiendo rangos («RF-016 a RF-020», «CA-PAN-02.1 a CA-PAN-02.6»)."""
    out = set(RX_ID.findall(texto))
    for m in RX_RANGO.finditer(texto):
        pre, a, b = m.group(1), int(m.group(2)), int(m.group(3))
        if 0 < b - a <= 200:
            w = len(m.group(2))
            out |= {f"{pre}{n:0{w}d}" for n in range(a, b + 1)}
    for m in RX_RANGO_CA.finditer(texto):
        base, a, b = m.group(1), int(m.group(2)), int(m.group(3))
        if 0 < b - a <= 50:
            out |= {f"{base}.{n}" for n in range(a, b + 1)}
    return out


def normaliza(s):
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def _estado_texto(s):
    """La primera marca de estado que aparece en el texto («✅ (… 🔒 …)» es ✅)."""
    pos = [(s.find(e), e) for e in ESTADOS if e in s]
    return min(pos)[1] if pos else ""


COLUMNAS_TITULO = ("pregunta", "regla", "decision", "supuesto", "actividad", "descripcion", "sistema",
                   "evento", "aviso", "notificacion", "caso de uso", "riesgo")


def _titulo_fila(cel, cabecera):
    cab = [normaliza(c) for c in _celdas(cabecera)]
    for n in COLUMNAS_TITULO:
        if n in cab and cab.index(n) < len(cel):
            return cel[cab.index(n)]
    return cel[1] if len(cel) > 1 else ""


def _celdas(linea):
    return [c.strip() for c in linea.strip().strip("|").split("|")]


class Modelo:
    def __init__(self, texto):
        self.lineas = texto.split("\n")
        self.piezas = {}          # id -> Pieza (definición principal)
        self.duplicados = []      # (id, línea) de definiciones repetidas
        self.menciones = {}       # id -> [(línea, sección, módulo)] fuera de piezas y secciones derivadas
        self.seccion_de_linea = []
        self._leer()
        self._inversas()

    # ---------- lectura ----------
    def _leer(self):
        L = self.lineas
        sec, mod = "", ""
        ficha = None
        cabecera, en_tabla = "", False
        en_codigo = False
        for i, l in enumerate(L):
            if l.startswith("```"):
                en_codigo = not en_codigo
            m = RX_SECCION.match(l) if not en_codigo else None
            if m:
                sec, mod = m.group(1), ""
                mm = RX_MODULO_EN_H2.search(l)
                if mm:
                    mod = mm.group(1)
            elif not en_codigo:
                mm = RX_MODULO_H3.match(l)
                if mm:
                    mod = mm.group(1)
            self.seccion_de_linea.append((sec, mod))
            if en_codigo or l.startswith("```"):
                continue
            es_titulo = l.startswith("#")
            mf = RX_FICHA.match(l)
            if ficha and (es_titulo or mf):
                self._cierra(ficha, i)
                ficha = None
            derivada = sec in SECCIONES_DERIVADAS
            if mf and not derivada:
                pid = mf.group(2)
                resto = mf.group(5)
                anulada = bool(mf.group(1) or mf.group(3)) or "Anulado por" in resto
                p = Pieza(pid, tipo_de(pid), "ficha", mf.group(4).strip(" ~"), sec, mod, i, i + 1,
                          estado="Anulada" if anulada else _estado_texto(mf.group(4) + resto))
                ficha = self._alta(p)
                continue
            # tablas
            if l.startswith("|"):
                if not en_tabla:
                    cabecera, en_tabla = l, True
            else:
                en_tabla = False
            mr = RX_FILA.match(l)
            if mr and not ficha and not derivada:
                pid = mr.group(2)
                cel = _celdas(l)
                titulo = re.sub(r"\s+", " ", _titulo_fila(cel, cabecera))[:110]
                p = Pieza(pid, tipo_de(pid), "fila", titulo.strip("~ "), sec, mod, i, i + 1, cabecera=cabecera)
                p.estado = self._estado_fila(l, cabecera, bool(mr.group(1) or mr.group(3)))
                p.refs = ids_en(l) - {pid}
                p.fuentes = set(RX_FUENTE.findall(l))
                if pid in self.piezas:
                    prev = self.piezas[pid]
                    if prev.forma == "ficha" or (prev.forma == "fila" and prev.tipo == "ACT"):
                        prev.apariciones.append(i)
                        if prev.forma == "fila":
                            prev.refs |= p.refs
                        continue
                self._alta(p)
                continue
            crit = list(RX_CRITERIO.finditer(l))
            for k, mc in enumerate(crit):
                cid = mc.group(1) or mc.group(2)
                padre = ficha.id if ficha else ""
                anulado = mc.group(2) is not None or f"~~`{cid}`~~" in l or f"~~{cid}~~" in l or "Anulado por" in l
                p = Pieza(cid, "CA", "criterio", re.sub(r"[*~\s]+", " ", l[mc.end(1 if mc.group(1) else 2) + 1:])[:110].strip(),
                          sec, mod, i, i + 1, padre=padre, estado="Anulada" if anulado else _estado_texto(l))
                if len(crit) > 1:
                    p.frag = l[mc.start():crit[k + 1].start() if k + 1 < len(crit) else len(l)]
                p.refs = ids_en(p.frag or l) - {cid, padre}
                p.fuentes = set(RX_FUENTE.findall(p.frag or l))
                self._alta(p)
                if ficha:
                    ficha.hijos.append(cid)
            if not ficha and not derivada:
                for x in ids_en(l):
                    self.menciones.setdefault(x, []).append(i)
        if ficha:
            self._cierra(ficha, len(L))

    def _alta(self, p):
        prev = self.piezas.get(p.id)
        if prev and p.forma == "ficha" and prev.forma == "fila" and prev.tipo in ("ACT", "INT", "NOT"):
            # la fila de la tabla resumen y la ficha son la misma pieza: manda la ficha
            p.apariciones = [prev.ini] + prev.apariciones
            p.estado = p.estado or prev.estado
            self.piezas[p.id] = p
            return p
        if prev:
            self.duplicados.append((p.id, p.ini + 1))
            return prev if p.forma != "ficha" else p
        self.piezas[p.id] = p
        return p

    def _cierra(self, f, fin):
        f.fin = fin
        bloque = "\n".join(self.lineas[f.ini:fin])
        f.refs = ids_en(bloque) - {f.id} - set(f.hijos)
        f.fuentes = set(RX_FUENTE.findall(bloque))
        m = re.search(r"\|\s*\*\*(?:Certeza|Estado)\*\*\s*\|([^|\n]*)\|", bloque)
        if m and not f.anulada:
            f.estado = _estado_texto(m.group(1)) or f.estado

    def _estado_fila(self, l, cabecera, tachada):
        cel = _celdas(l)
        cab = [normaliza(c) for c in _celdas(cabecera)]
        if tachada or re.search(r"Anulad[ao] por", l):
            return "Respondida" if "Respondida" in l else "Anulada"
        if "Respondida por" in l:
            return "Respondida"
        for nombre in ("vigente",):
            if nombre in cab and cab.index(nombre) < len(cel):
                v = cel[cab.index(nombre)]
                return "Vigente" if normaliza(v).startswith(("si", "en parte")) else "Sustituida"
        for nombre in ("certeza", "estado"):
            if nombre in cab and cab.index(nombre) < len(cel):
                return _estado_texto(cel[cab.index(nombre)])
        return ""  # sin columna de estado no se adivina

    def _inversas(self):
        self.citada_por = {}
        for p in self.piezas.values():
            for r in p.refs:
                self.citada_por.setdefault(r, set()).add(p.id)

    # ---------- consultas ----------
    def bloque(self, pid):
        p = self.piezas[pid]
        return self.lineas[p.ini:p.fin]

    def texto(self, pid):
        p = self.piezas[pid]
        return p.frag if p.frag else "\n".join(self.bloque(pid))

    def campo(self, pid, nombre):
        """Valor de un campo de la pieza: fila «| **Nombre** | valor |» de su ficha o, si la pieza es
        una fila de tabla (p. ej. RF en tabla en modo fiel), la celda de la columna con ese nombre."""
        mm = re.search(rf"\|\s*\*\*{re.escape(nombre)}\*\*\s*\|([^\n]*?)\|\s*$", self.texto(pid), re.M)
        if mm:
            return mm.group(1).strip()
        p = self.piezas.get(pid)
        if p and p.forma == "fila" and p.cabecera:
            cols = [normaliza(c) for c in _celdas(p.cabecera)]
            cel = _celdas(self.lineas[p.ini])
            if normaliza(nombre) in cols and cols.index(normaliza(nombre)) < len(cel):
                return cel[cols.index(normaliza(nombre))]
        return ""

    def raiz(self, pid):
        """La ficha a la que pertenece un criterio (o la propia pieza)."""
        p = self.piezas.get(pid)
        return p.padre if p and p.padre else pid

    def version(self):
        for l in self.lineas[:80]:
            m = re.search(r"Versi[oó]n:\s*v?(\d+)\.(\d+)", l)
            if m:
                return int(m.group(1)), int(m.group(2))
        return None

    def por_tipo(self, tipo):
        return [p for p in self.piezas.values() if p.tipo == tipo]


def cargar(ruta):
    import pathlib
    return Modelo(pathlib.Path(ruta).read_text(encoding="utf-8"))


def numero(pid):
    return int(re.search(r"(\d+)$", pid.split(".")[0]).group(1)) if not pid.startswith("CA-") else 0
