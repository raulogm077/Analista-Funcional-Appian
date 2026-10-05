"""Lee el análisis de un proyecto como piezas con ID, estado, fuentes y referencias.

Lo usan indice.py, comprobar.py, proyecto.py y unir_modulos.py. Sin dependencias.

El análisis son tres ficheros de `analisis/`:
  funcional.md  (doc F)  lo que valida el cliente
  tecnico.md    (doc T)  lo que se construye
  decisiones.md (doc D)  versiones y decisiones del cliente

Una pieza es algo con ID estable. Solo se define en su sitio (CASA); en cualquier otro sitio, su ID es
una mención:
  ficha:    **HU-07 — Título** <!-- ✅ FU-03 00:14:32 -->  (hasta la siguiente ficha o título)
  fila:     | PC-03 | … |
  criterio: - `HU-07.1` texto   (dentro de su historia)
El comentario <!-- … --> lleva el estado (🔒 ✅ 🔶 ⚠️ ❓) y las fuentes; el Word no lo muestra.
"""
import pathlib
import re
import unicodedata
from dataclasses import dataclass, field

DOCS = {"F": "funcional.md", "T": "tecnico.md", "D": "decisiones.md"}
NOMBRE_DOC = {"F": "funcional", "T": "técnico", "D": "decisiones"}

# Dónde se define cada tipo: (doc, sección, forma)
CASA = {
    "ACT": ("F", "3", "ficha"), "ESC": ("F", "3", "ficha"),
    "HU": ("F", "4", "ficha"), "RB": ("F", "4", "fila"),
    "PAN": ("F", "5", "ficha"), "AV": ("F", "7", "fila"), "DOC": ("F", "8", "fila"),
    "INT": ("F", "9", "fila"), "PC": ("F", "11", "fila"),
    "D": ("D", "decisiones", "fila"),
    "DT": ("T", "2", "ficha"), "PT": ("T", "15", "fila"),
}
TIPOS = list(CASA) + ["CA"]
_PRE = "|".join(sorted(CASA, key=len, reverse=True))
ID_SIMPLE = rf"(?:{_PRE})-\d+"
ID_CA = r"HU-\d+\.\d+"
RX_ID = re.compile(rf"(?<![\w-])(?:{ID_CA}|{ID_SIMPLE})(?![\w-]|\.\d)")
RX_RANGO = re.compile(rf"(?<![\w-])((?:{_PRE})-)(\d+)`?\s+a\s+`?(?:\1)?(\d+)(?![\w.-])")
RX_RANGO_CA = re.compile(r"(HU-\d+)\.(\d+)`?\s+a\s+`?(?:\1\.)?(\d+)(?![\w.])")
RX_FICHA = re.compile(rf"^\*\*(~~)?({ID_SIMPLE})(~~)?\s+—\s+(.+?)\*\*(.*)$")
RX_FILA = re.compile(rf"^\|\s*(~~)?({ID_SIMPLE})(~~)?\s*\|")
RX_CRITERIO = re.compile(rf"^\s*[-*]\s+(~~)?`({ID_CA})`(~~)?")
RX_COMENTARIO = re.compile(r"<!--(.*?)-->", re.S)
RX_FUENTE = re.compile(r"FU-\d+")
RX_CITA = re.compile(r"FU-\d+(?:\s+\d{1,2}:\d{2}:\d{2})?")
RX_SECCION = re.compile(r"^## (?:(\d+)\.|(\w+))")
ESTADOS = ["🔒", "✅", "🔶", "⚠️", "❓"]
NOMBRE_ESTADO = {"🔒": "Validado", "✅": "Decidido", "🔶": "Inferido", "⚠️": "Pendiente", "❓": "No definido"}
ANULADOS = ("Anulada", "Respondida", "Sustituida")


@dataclass
class Pieza:
    id: str
    tipo: str
    forma: str            # ficha | fila | criterio
    titulo: str
    doc: str              # F | T | D
    seccion: str
    ini: int              # línea (0-based) donde empieza
    fin: int              # línea siguiente a la última
    estado: str = ""      # emoji de ESTADOS, uno de ANULADOS, "Vigente" o ""
    padre: str = ""
    refs: set = field(default_factory=set)
    fuentes: set = field(default_factory=set)
    hijos: list = field(default_factory=list)
    cabecera: str = ""    # cabecera de la tabla (piezas de tipo fila)

    @property
    def anulada(self):
        return self.estado in ANULADOS

    def donde(self):
        return f"{NOMBRE_DOC[self.doc]} §{self.seccion} l.{self.ini + 1}"


def tipo_de(pid):
    return "CA" if re.fullmatch(ID_CA, pid) else pid.split("-")[0]


def ids_en(texto):
    """IDs citados en un texto, con los rangos expandidos («HU-01 a HU-03», «HU-02.1 a HU-02.4»)."""
    out = set(RX_ID.findall(texto))
    for m in RX_RANGO.finditer(texto):
        pre, a, b = m.group(1), int(m.group(2)), int(m.group(3))
        if 0 < b - a <= 200:
            out |= {f"{pre}{n:0{len(m.group(2))}d}" for n in range(a, b + 1)}
    for m in RX_RANGO_CA.finditer(texto):
        base, a, b = m.group(1), int(m.group(2)), int(m.group(3))
        if 0 < b - a <= 50:
            out |= {f"{base}.{n}" for n in range(a, b + 1)}
    return out


def normaliza(s):
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def celdas(linea):
    return [c.strip() for c in linea.strip().strip("|").split("|")]


def sin_comentarios(texto):
    return RX_COMENTARIO.sub("", texto)


def estado_en(texto):
    pos = [(texto.find(e), e) for e in ESTADOS if e in texto]
    return min(pos)[1] if pos else ""


def numero(pid):
    return int(re.search(r"(\d+)$", pid.split(".")[0]).group(1))


class Documento:
    def __init__(self, doc, texto):
        self.doc = doc
        self.lineas = texto.split("\n")
        self.secciones = []        # (clave, título, ini, fin)
        self.seccion_de_linea = []
        self._secciones()

    def _secciones(self):
        actual, en_codigo = "", False
        for i, l in enumerate(self.lineas):
            if l.startswith("```"):
                en_codigo = not en_codigo
            m = None if en_codigo else RX_SECCION.match(l)
            if m:
                actual = m.group(1) or normaliza(m.group(2))
                if self.secciones:
                    self.secciones[-1][3] = i
                self.secciones.append([actual, l[3:].strip(), i, len(self.lineas)])
            self.seccion_de_linea.append(actual)

    def seccion(self, clave):
        for k, titulo, ini, fin in self.secciones:
            if k == str(clave):
                return ini, fin
        return None

    def version(self):
        for l in self.lineas[:20]:
            m = re.search(r"Versi[oó]n:\s*v?(\d+)\.(\d+)", l)
            if m:
                return int(m.group(1)), int(m.group(2))
        return None


class Proyecto:
    """El análisis de un proyecto. `ruta`: la carpeta del proyecto, su carpeta analisis/ o uno de sus ficheros."""

    def __init__(self, ruta):
        ruta = pathlib.Path(ruta)
        if ruta.is_file():
            ruta = ruta.parent
        self.analisis = ruta / "analisis" if (ruta / "analisis").is_dir() else ruta
        self.raiz = self.analisis.parent if self.analisis.name == "analisis" else self.analisis
        self.docs = {}
        for d, nombre in DOCS.items():
            f = self.analisis / nombre
            if f.exists():
                self.docs[d] = Documento(d, f.read_text(encoding="utf-8"))
        self.piezas = {}
        self.duplicados = []       # (id, doc, línea)
        self.fuera_de_casa = []    # (id, doc, línea): ficha o fila con ID que se define en otro sitio
        self.menciones = {}        # id -> [(doc, línea)] fuera de su propia pieza
        for d, documento in self.docs.items():
            self._leer(documento)
        self._inversas()

    def ruta(self, doc):
        return self.analisis / DOCS[doc]

    # ---------- lectura ----------
    def _es_casa(self, pid, doc, sec, forma):
        t = tipo_de(pid)
        if t == "CA":
            return doc == "F" and sec == "4"
        casa = CASA.get(t)
        return bool(casa) and casa[0] == doc and casa[1] == sec and casa[2] == forma

    def _leer(self, D):
        L = D.lineas
        ficha, cabecera, en_tabla, en_codigo = None, "", False, False
        for i, l in enumerate(L):
            if l.startswith("```"):
                en_codigo = not en_codigo
                continue
            if en_codigo:
                continue
            sec = D.seccion_de_linea[i]
            mf = RX_FICHA.match(l)
            if ficha and (l.startswith("#") or mf):
                self._cierra(D, ficha, i)
                ficha = None
            if mf:
                pid = mf.group(2)
                if self._es_casa(pid, D.doc, sec, "ficha"):
                    resto = mf.group(5)
                    comentario = " ".join(RX_COMENTARIO.findall(resto))
                    anulada = bool(mf.group(1) or mf.group(3)) or re.search(r"Anulad[ao] por", resto)
                    p = Pieza(pid, tipo_de(pid), "ficha", mf.group(4).strip(" ~"), D.doc, sec, i, i + 1,
                              estado="Anulada" if anulada else estado_en(comentario))
                    p.fuentes = set(RX_CITA.findall(comentario))
                    ficha = self._alta(p)
                    continue
                self.fuera_de_casa.append((pid, D.doc, i))
            if l.startswith("|"):
                if not en_tabla:
                    cabecera, en_tabla = l, True
            else:
                en_tabla = False
            mr = RX_FILA.match(l)
            if mr and not ficha:
                pid = mr.group(2)
                if self._es_casa(pid, D.doc, self._sec_fila(D, sec), "fila"):
                    cel = celdas(l)
                    p = Pieza(pid, tipo_de(pid), "fila", self._titulo_fila(cel, cabecera), D.doc, sec, i, i + 1,
                              cabecera=cabecera)
                    p.estado = self._estado_fila(l, cabecera, bool(mr.group(1) or mr.group(3)))
                    p.refs = ids_en(sin_comentarios(l)) - {pid}
                    p.fuentes = set(RX_CITA.findall(l))
                    self._alta(p)
                    continue
            mc = RX_CRITERIO.match(l)
            if mc and ficha and ficha.tipo == "HU":
                cid = mc.group(2)
                anulado = bool(mc.group(1) or mc.group(3)) or bool(re.search(r"Anulad[ao] por", l))
                texto = sin_comentarios(l[mc.end():])
                p = Pieza(cid, "CA", "criterio", re.sub(r"[*~\s]+", " ", texto).strip()[:110], D.doc, sec, i, i + 1,
                          padre=ficha.id, estado="Anulada" if anulado else "")
                p.refs = ids_en(texto) - {cid, ficha.id}
                p.fuentes = set(RX_CITA.findall(l))
                self._alta(p)
                ficha.hijos.append(cid)
                continue
            if not ficha:
                for x in ids_en(sin_comentarios(l)):
                    self.menciones.setdefault(x, []).append((D.doc, i))
        if ficha:
            self._cierra(D, ficha, len(L))

    @staticmethod
    def _sec_fila(D, sec):
        return "decisiones" if D.doc == "D" and sec.startswith("decisiones") else sec

    @staticmethod
    def _titulo_fila(cel, cabecera):
        cab = [normaliza(c) for c in celdas(cabecera)]
        for nombre in ("pregunta", "regla", "decision", "duda", "cuando", "que es", "sistema"):
            if nombre in cab and cab.index(nombre) < len(cel):
                return re.sub(r"\s+", " ", sin_comentarios(cel[cab.index(nombre)])).strip("~ ")[:110]
        return sin_comentarios(cel[1]).strip()[:110] if len(cel) > 1 else ""

    @staticmethod
    def _estado_fila(l, cabecera, tachada):
        if "Respondida por" in l:
            return "Respondida"
        if tachada or re.search(r"Anulad[ao] por", l):
            return "Anulada"
        cab = [normaliza(c) for c in celdas(cabecera)]
        cel = celdas(l)
        if "vigente" in cab and cab.index("vigente") < len(cel):
            v = normaliza(cel[cab.index("vigente")])
            return "Vigente" if v.startswith(("si", "en parte")) else "Sustituida"
        return estado_en(" ".join(RX_COMENTARIO.findall(l)))

    def _alta(self, p):
        if p.id in self.piezas:
            self.duplicados.append((p.id, p.doc, p.ini + 1))
            return self.piezas[p.id] if p.forma != "ficha" else p
        self.piezas[p.id] = p
        return p

    def _cierra(self, D, f, fin):
        f.fin = fin
        bloque = sin_comentarios("\n".join(D.lineas[f.ini:fin]))
        f.refs = ids_en(bloque) - {f.id} - set(f.hijos)

    def _inversas(self):
        self.citada_por = {}
        for p in self.piezas.values():
            for r in p.refs:
                self.citada_por.setdefault(r, set()).add(p.id)

    # ---------- consultas ----------
    def lineas(self, doc):
        return self.docs[doc].lineas

    def bloque(self, pid):
        p = self.piezas[pid]
        return self.docs[p.doc].lineas[p.ini:p.fin]

    def texto(self, pid):
        return "\n".join(self.bloque(pid))

    def campos(self, pid):
        """Campos de una ficha: tabla horizontal de una fila tras el título (| Perfil | Pantalla |…) o
        tabla vertical (| **Campo** | valor |). Devuelve {nombre normalizado: valor}."""
        out = {}
        bloque = self.bloque(pid)
        filas = [l for l in bloque[1:] if l.startswith("|")]
        for l in filas:
            m = re.match(r"^\|\s*\*\*(.+?)\*\*\s*\|(.*)\|\s*$", l)
            if m:
                out[normaliza(m.group(1))] = m.group(2).strip()
        if not out and len(filas) >= 3:
            cab, val = celdas(filas[0]), celdas(filas[2])
            out = {normaliza(c): v for c, v in zip(cab, val)}
        return out

    def raiz_de(self, pid):
        p = self.piezas.get(pid)
        return p.padre if p and p.padre else pid

    def por_tipo(self, tipo):
        return [p for p in self.piezas.values() if p.tipo == tipo]

    def vigentes(self, tipo):
        return [p for p in self.por_tipo(tipo) if not p.anulada]

    def version(self, doc="F"):
        return self.docs[doc].version() if doc in self.docs else None

    def tablas(self, doc, seccion=None):
        """Tablas de un documento (o de una sección): lista de (línea de cabecera, [cabecera], [[celdas]…])."""
        if doc not in self.docs:
            return []
        D = self.docs[doc]
        ini, fin = (0, len(D.lineas)) if seccion is None else (D.seccion(seccion) or (0, 0))
        out, actual = [], None
        for i in range(ini, fin):
            l = D.lineas[i]
            if l.startswith("|"):
                if actual is None:
                    actual = (i, celdas(l), [])
                    out.append(actual)
                elif not re.match(r"^\|[\s:|-]+\|?\s*$", l):
                    actual[2].append(celdas(l))
            else:
                actual = None
        return out


def cargar(ruta):
    return Proyecto(ruta)
