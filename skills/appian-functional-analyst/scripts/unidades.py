"""Las unidades de cambio de un proyecto (analisis/cambios.md) y lo que se deriva de ellas, sin leer documentos.

  EV-nn   un evolutivo; también la construcción inicial de una aplicación nueva (EV-01) y cada fase de una refactorización
  URG-nn  un cambio urgente; su ficha es el informe de impacto impacto/URG-nn.md

analisis/cambios.md solo lo escribe proyecto.py cambio. Todo lo demás se calcula aquí:
  - fuentes de una unidad: los informes de impacto con «Cambio: EV-02» en la cabecera o, si llevan una columna «Cambio»,
    sus puntos con ese ID; sin cabecera, la única unidad Abierta (si el informe es de después de abrirla); un informe
    «sin cambios», de ninguna;
  - sus piezas: los IDs de «Aplicado» y de «Cambio propuesto» de esos puntos (sin SIN IMPACTO, PROYECTO ni descartes);
  - sus objetos: las filas de técnico §13 con su ID en la columna «Cambio» (las que no llevan ID, de EV-01 si existe);
  - la línea base: el inventario de as-is/ más los objetos de las unidades Construidas o En producción;
  - por pieza, «Construido: … · En curso: …»; por unidad, las correcciones urgentes que hay que reaplicar o que congelan
    sus objetos.
Sin analisis/cambios.md, nada de esto: el proyecto se comporta como antes. Lo usan proyecto.py, indice.py y comprobar.py.
"""
import json
import pathlib
import re
import sys
from dataclasses import dataclass
sys.dont_write_bytecode = True  # sin __pycache__ en el plugin: no se escribe fuera del proyecto

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import modelo as mo

FICHERO = "cambios.md"
RX_UNIDAD = re.compile(r"(?<![\w-])(?:EV|URG)-\d+(?![\w-])")
ABIERTA, APROBADA, CONSTRUIDA, PRODUCCION, DESCARTADA = ("Abierta", "Aprobada", "Construida", "En producción",
                                                        "Descartada")
EN_CURSO = (ABIERTA, APROBADA, CONSTRUIDA)      # no han pasado a producción ni se han descartado
CONSTRUIDAS = (CONSTRUIDA, PRODUCCION)
COLUMNAS = ["ID", "Título", "Tipo", "Estado", "Aprobada", "Construida", "En producción", "Comparte objetos / decisión"]
CAMBIAN = ("nuevo", "modifica", "sustituye")    # situaciones de §13 que construyen o cambian algo
SIN_PIEZAS = ("sin impacto", "proyecto")        # tipos de punto que no cambian el análisis
# «Cambio sobre lo construido» (references/cambios.md): el punto de la DT que pide cada tipo de objeto de §13 que se
# modifica o se sustituye y ya está construido. Las interfaces, reglas, constantes y textos no piden DT.
PUNTOS_CONSTRUIDO = [(("record type", "cdt", "tabla"), "Datos existentes"),
                     (("process model", "modelo de proceso"), "Procesos en curso"),
                     (("web api",), "Compatibilidad"), (("grupo", "seguridad"), "Permisos")]
# Tipo de §13 → tipo del inventario (el que compara verificar --esperado); el primero que casa
TIPOS_APPIAN = [("record type", "recordType"), ("cdt", "cdt"), ("interfaz", "interface"), ("interface", "interface"),
                ("regla de expresion", "expressionRule"), ("expression rule", "expressionRule"),
                ("process model", "processModel"), ("modelo de proceso", "processModel"), ("web api", "webApi"),
                ("integracion", "integration"), ("integration", "integration"), ("constante", "constant"),
                ("constant", "constant"), ("grupo", "group"), ("group", "group"), ("decision", "decision"),
                ("site", "site"), ("sistema conectado", "connectedSystem"), ("connected system", "connectedSystem"),
                ("data store", "dataStore"), ("agente", "aiAgent"), ("ai agent", "aiAgent")]
# Tipo de un campo de técnico §3 → el que entiende verificar (sus sinónimos); los demás no se comparan
TIPOS_CAMPO = {"texto": "Text", "text": "Text", "entero": "Integer", "numero (entero)": "Integer", "integer": "Integer",
               "decimal": "Decimal", "numero (decimal)": "Decimal", "booleano": "Boolean", "boolean": "Boolean",
               "si/no": "Boolean", "fecha y hora": "Datetime", "datetime": "Datetime", "fecha": "Date", "date": "Date",
               "hora": "Time", "usuario": "User", "user": "User", "grupo": "Group"}


@dataclass
class Unidad:
    id: str
    titulo: str = ""
    tipo: str = "Evolutivo"
    estado: str = ABIERTA
    aprobada: str = "—"
    construida: str = "—"
    produccion: str = "—"
    comparte: str = "—"
    desde: tuple = None     # versión del análisis al abrirla (<!-- desde 1.3 --> en su celda ID)

    @property
    def urgente(self):
        return self.id.startswith("URG")

    def fila(self):
        desde = f" <!-- desde {self.desde[0]}.{self.desde[1]} -->" if self.desde else ""
        celdas = [self.id + desde, self.titulo, self.tipo, self.estado, self.aprobada, self.construida, self.produccion,
                  self.comparte]
        return "| " + " | ".join((c or "—").replace("|", "/").replace("\n", " ") for c in celdas) + " |"


def orden(pid):
    return (mo.tipo_de(pid), [int(x) for x in re.findall(r"\d+", pid)])


def vacio(celda):
    return not mo.sin_comentarios(celda or "").strip(" —-")


def version(texto):
    mv = re.search(r"v?(\d+)\.(\d+)", texto or "")
    return (int(mv.group(1)), int(mv.group(2))) if mv else None


def ruta(raiz):
    return pathlib.Path(raiz) / "analisis" / FICHERO


def leer(raiz):
    """Las unidades de analisis/cambios.md, en su orden, o None si el fichero no existe."""
    f = ruta(raiz)
    if not f.is_file():
        return None
    out = []
    for l in f.read_text(encoding="utf-8").split("\n"):
        c = mo.celdas(l) if l.startswith("|") else []
        if not c or not RX_UNIDAD.match(mo.sin_comentarios(c[0]).strip()):
            continue
        c += [""] * (len(COLUMNAS) - len(c))
        desde = re.search(r"desde\s+(\d+\.\d+)", c[0])
        out.append(Unidad(mo.sin_comentarios(c[0]).strip(), *[x.strip() or "—" for x in c[1:8]],
                          desde=version(desde.group(1)) if desde else None))
    return out


def escribir(raiz, unidades, plantilla):
    """Reescribe la tabla de analisis/cambios.md (lo de fuera de la tabla se queda); si no existe, desde la plantilla."""
    f = ruta(raiz)
    if f.is_file():
        texto = f.read_text(encoding="utf-8")
    else:
        pm = pathlib.Path(raiz) / "proyecto.md"
        titulo = pm.read_text(encoding="utf-8").split("\n", 1)[0][2:].strip() if pm.is_file() else pathlib.Path(raiz).name
        texto = pathlib.Path(plantilla).read_text(encoding="utf-8").replace("{proyecto}", titulo)
    lineas = texto.rstrip("\n").split("\n")
    ini = next((i for i, l in enumerate(lineas) if l.startswith("| ID |")), None)
    if ini is None:
        lineas += ["", "| " + " | ".join(COLUMNAS) + " |", "|" + "---|" * len(COLUMNAS)]
        ini = len(lineas) - 2
    fin = ini + 2
    while fin < len(lineas) and lineas[fin].startswith("|"):
        fin += 1
    lineas[ini + 2:fin] = [u.fila() for u in unidades]
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("\n".join(lineas) + "\n", encoding="utf-8")


def objetos_celda(celda):
    """Los objetos de una celda: los nombres entre comillas invertidas o, si no hay, la celda; sin el prefijo de tipo
    («rule!», «recordType!», como comprobar_asis.py) ni los paréntesis del final («MNT_IF_Panel()»)."""
    t = mo.sin_comentarios(celda).strip()
    nombres = re.findall(r"`([^`]+)`", t) or ([t] if t.strip(" —-") else [])
    return [re.sub(r"\(.*\)\s*$", "", re.sub(r"^[A-Za-z]+!(\{[^}]*\})?", "", n.strip())).strip() for n in nombres]


def objeto(nombre):
    """El objeto de un nombre de §13: «MNT Orden — acción «Corregir orden»» es una parte de MNT Orden."""
    return re.split(r"\s+[—–]\s+", nombre, maxsplit=1)[0].strip()


def campos_urgencia(texto):
    """Los campos de la sección «## Urgencia» de una ficha URG: {campo normalizado: valor}."""
    sec = re.search(r"^## Urgencia\s*$(.*?)(?=^## |\Z)", texto, re.M | re.S)
    out = {}
    for l in (sec.group(1).split("\n") if sec else []):
        c = mo.celdas(l) if l.startswith("|") else []
        if len(c) >= 2 and not re.match(r"^[-:\s]+$", c[0]) and mo.normaliza(c[0]).strip("* ") != "campo":
            out[mo.normaliza(c[0]).strip("* ")] = c[1].strip()
    return out


class Contexto:
    """Las unidades de un proyecto (m: modelo.Proyecto) y lo que se deriva de ellas. `hay` es False sin cambios.md."""

    def __init__(self, m):
        self.m, self.raiz = m, m.raiz
        leidas = leer(m.raiz)
        self.hay = leidas is not None
        self.unidades = leidas or []
        self.por_id = {u.id: u for u in self.unidades}
        self.informes = mo.informes(m.raiz) if self.hay else []
        inv = m.raiz / "as-is" / "datos" / "inventario.json"
        self.inventario = ({o["nombre"] for o in json.loads(inv.read_text(encoding="utf-8")).get("objetos", [])}
                           if inv.is_file() else None)
        self.filas = self._filas_13()
        self._copias = {}

    # ------------------------------------------------------------ informes → unidades
    def _de_informe(self, nombre, texto, puntos):
        """[(punto o None, [unidades])]: la columna «Cambio» de cada punto, la cabecera «Cambio:» o, sin ellas, la única
        unidad Abierta (si el informe es de después de abrirla y cambia algo: uno «sin cambios» no es de ninguna)."""
        if puntos and "cambio" in puntos[0]:
            return [(p, RX_UNIDAD.findall(p.get("cambio", ""))) for p in puntos]
        cab = re.search(r"Cambio:\s*([^·\n]+)", "\n".join(texto.splitlines()[:5]))
        if cab:
            us = RX_UNIDAD.findall(cab.group(1))
        elif mo.normaliza(mo.estado_informe(texto)).startswith("sin cambios"):
            us = []
        else:
            abiertas = [u for u in self.unidades if u.estado == ABIERTA]
            mb = re.search(r"An[aá]lisis base:\s*versi[oó]n\s*([\d.]+)", texto)
            base = version(mb.group(1)) if mb else None
            us = [abiertas[0].id] if len(abiertas) == 1 and not (
                abiertas[0].desde and base and base < abiertas[0].desde) else []
        return [(p, us) for p in puntos] or [(None, us)]

    def sin_unidad(self):
        """Los informes que cambian algo, sin «Cambio» ni columna, cuando hay más de una unidad Abierta (y son de después
        de abrirlas): ¿de cuál son?"""
        abiertas = [u for u in self.unidades if u.estado == ABIERTA]
        if len(abiertas) < 2:
            return []
        desde = min((u.desde for u in abiertas if u.desde), default=None)
        base = lambda t: version((re.search(r"An[aá]lisis base:\s*versi[oó]n\s*([\d.]+)", t) or [None, ""])[1])
        return [n for n, t, puntos, _ in self.informes
                if not re.search(r"Cambio:", "\n".join(t.splitlines()[:5])) and not (puntos and "cambio" in puntos[0])
                and not mo.normaliza(mo.estado_informe(t)).startswith("sin cambios")
                and not (desde and base(t) and base(t) < desde)]

    def puntos_de(self, uid):
        """[(nombre del informe, texto, punto o None)] de una unidad."""
        return [(n, t, p) for n, t, puntos, _ in self.informes for p, us in self._de_informe(n, t, puntos) if uid in us]

    def informes_de(self, uid):
        return list(dict.fromkeys(n for n, _, _ in self.puntos_de(uid)))

    def piezas_de(self, uid, aplicadas=True):
        """Los IDs de una unidad: «Cambio propuesto» de sus puntos y «Aplicado» de sus informes (si es el informe entero).
        Con aplicadas, solo lo de un informe aplicado y los puntos que no esperan aprobación; si no, todo lo no descartado."""
        out = set()
        for n, t, p in self.puntos_de(uid):
            aplicado = mo.normaliza(mo.estado_informe(t)).startswith("aplicado")
            if aplicadas and not aplicado:
                continue
            if p is not None:
                dec = mo.normaliza(p.get("decision", "")).strip(" *")
                tipo = mo.normaliza(p.get("tipo", "")).strip(" *`")
                if "✗" in p.get("decision", "") or tipo in SIN_PIEZAS or (aplicadas and dec.startswith("pendiente")):
                    continue
                out |= mo.ids_en(p.get("cambio propuesto", ""))
            if aplicado and (p is None or "cambio" not in p):
                ma = re.search(r"^## Aplicado\s*$(.*?)(?=^## |\Z)", t, re.M | re.S)
                out |= mo.ids_en(ma.group(1)) if ma else set()
        return out

    def raices_de(self, uid, aplicadas=True):
        """Las piezas de una unidad con sus fichas: un criterio que cambia toca su historia."""
        ids = self.piezas_de(uid, aplicadas)
        return ids | {self.m.raiz_de(x) for x in ids}

    def version_base(self, uid):
        """La versión del análisis antes de la unidad: la menor «Análisis base» de sus informes aplicados."""
        vs = [version(b.group(1)) for n, t, _ in self.puntos_de(uid)
              if mo.normaliza(mo.estado_informe(t)).startswith("aplicado")
              for b in [re.search(r"An[aá]lisis base:\s*versi[oó]n\s*([\d.]+)", t)] if b]
        return min(vs) if vs else None

    def versiones_de(self, uid):
        """Las versiones en que se aplicaron sus informes («aplicado en 1.2»)."""
        vs = {version(e.group(1)) for n, t, _ in self.puntos_de(uid)
              for e in [re.match(r"aplicado en v?([\d.]+)", mo.estado_informe(t), re.I)] if e}
        return sorted(v for v in vs if v)

    def copia(self, v):
        """El análisis de versiones/v<x.y>/ (proyecto.py copia), o None."""
        if not v:
            return None
        if v not in self._copias:
            d = self.raiz / "versiones" / f"v{v[0]}.{v[1]}"
            self._copias[v] = mo.Proyecto(d) if d.is_dir() else None
        return self._copias[v]

    # ------------------------------------------------------------ objetos (técnico §13)
    def _filas_13(self):
        """Las filas de técnico §13 (tabla con «Situación»): {objetos, tipo, situacion, sustituye, unidad, paso}; sin ID
        en «Cambio», de EV-01 si existe (la construcción inicial)."""
        out = []
        tabla = next(((cab, filas) for _, cab, filas in self.m.tablas("T", "13")
                      if "situacion" in [mo.normaliza(c) for c in cab]), None)
        if not tabla:
            return out
        cab = [mo.normaliza(c) for c in tabla[0]]
        celda = lambda f, k: f[cab.index(k)] if k in cab and cab.index(k) < len(f) else ""
        sin_id = "EV-01" if "EV-01" in self.por_id else None
        for f in tabla[1]:
            us = RX_UNIDAD.findall(celda(f, "cambio"))
            out.append({"objetos": objetos_celda(celda(f, "objeto")), "tipo": mo.sin_comentarios(celda(f, "tipo")).strip(),
                        "situacion": mo.normaliza(mo.sin_comentarios(celda(f, "situacion"))).strip(),
                        "sustituye": objetos_celda(celda(f, "sustituye a")), "unidad": us[0] if us else sin_id,
                        "paso": celda(f, "paso")})
        return out

    def filas_de(self, uid):
        return [f for f in self.filas if f["unidad"] == uid]

    def cambian(self, uid):
        """Los objetos que construye o cambia una unidad (Nuevo, Modifica, Sustituye), sin la parte («MNT Orden — …»)."""
        return list(dict.fromkeys(objeto(o) for f in self.filas_de(uid) if f["situacion"] in CAMBIAN
                                  for o in f["objetos"]))

    def linea_base(self):
        """Lo construido: el inventario de as-is/ más los objetos de las unidades Construidas o En producción."""
        hechas = {u.id for u in self.unidades if u.estado in CONSTRUIDAS}
        return set(self.inventario or ()) | {objeto(o) for f in self.filas if f["unidad"] in hechas
                                             for o in f["objetos"]}

    def puntos_construido(self, uid):
        """{punto de la DT «Cambio sobre lo construido»: [objetos]} que pide una unidad por el tipo de los objetos
        construidos que modifica o sustituye (PUNTOS_CONSTRUIDO); con alguno, también «Despliegue y vuelta atrás»."""
        base = self.linea_base()
        dep = self.raiz / "as-is" / "datos" / "dependencias.json"
        fuera = json.loads(dep.read_text(encoding="utf-8")).get("fueraDeLaAplicacion", []) if dep.is_file() else []
        usadas_fuera = {x for o in fuera for x in o.get("usa", [])}
        out = {}
        for f in self.filas_de(uid):
            objs = [objeto(o) for o in f["objetos"] if objeto(o) in base]
            if f["situacion"] not in ("modifica", "sustituye") or not objs:
                continue
            tipo = mo.normaliza(f["tipo"])
            for claves, punto in PUNTOS_CONSTRUIDO:
                if any(k in tipo for k in claves):
                    out.setdefault(punto, []).extend(objs)
            if "integracion" in tipo and set(objs) & usadas_fuera:     # una integración que usan otros
                out.setdefault("Compatibilidad", []).extend(objs)
        if out:
            out["Despliegue y vuelta atrás"] = [o for v in out.values() for o in v]
        return {k: list(dict.fromkeys(v)) for k, v in out.items()}

    def dt_construido(self, uid):
        """La DT «Cambio sobre lo construido» de una unidad (su ID en el título o en «Necesidad»), o None."""
        return next((p for p in self.m.vigentes("DT") if "cambio sobre lo construido" in mo.normaliza(p.titulo)
                     and uid in RX_UNIDAD.findall(p.titulo + " " + self.m.campos(p.id).get("necesidad", ""))), None)

    # ------------------------------------------------------------ urgentes
    def ficha_urg(self, uid):
        f = self.raiz / "impacto" / f"{uid}.md"
        return campos_urgencia(f.read_text(encoding="utf-8")) if f.is_file() else None

    def objetos_urg(self, uid):
        """Los objetos que corrige una URG: los de «Objetos» de su ficha y sus filas de §13."""
        campos = self.ficha_urg(uid) or {}
        return list(dict.fromkeys([objeto(o) for o in objetos_celda(campos.get("objetos", ""))] + self.cambian(uid)))

    def _urgentes(self, uid, donde):
        mias = set(self.cambian(uid))
        out = []
        for v in self.unidades:
            if not v.urgente or v.id == uid or v.estado == DESCARTADA:
                continue
            lugar = mo.normaliza((self.ficha_urg(v.id) or {}).get("donde se corrige", ""))
            if donde == "correccion" and "correccion" in lugar and vacio(v.construida):
                comunes = [o for o in self.objetos_urg(v.id) if o in mias]
            elif donde == "desarrollo" and "desarrollo" in lugar and "correccion" not in lugar and v.estado != PRODUCCION:
                comunes = [o for o in self.objetos_urg(v.id) if o in mias]
            else:
                comunes = []
            if comunes:
                out.append((v.id, comunes))
        return out

    def reaplicar(self, uid):
        """[(URG, objetos)]: las corregidas en el entorno de corrección sobre objetos que cambia esta unidad y que aún no
        se han reaplicado en desarrollo (su celda «Construida» vacía)."""
        return self._urgentes(uid, "correccion")

    def congelados(self, uid):
        """[(URG, objetos)]: las que se corrigen en desarrollo y no han pasado a producción: esos objetos no se tocan."""
        return self._urgentes(uid, "desarrollo")

    # ------------------------------------------------------------ lo de una unidad (DF, encargo, pruebas)
    def resumen(self, uid):
        """Lo de una unidad (indice.py cambios --json, que leen df_docx.js --cambio e indice.py encargo): piezas nuevas,
        que cambian (con un antes y después breve, frente a versiones/) y anuladas; historias que se conservan pero
        comparten pantalla o paso con ellas (T5); pantallas, diagramas, apartados del técnico, objetos, pruebas a repetir,
        colisiones y correcciones urgentes que reaplicar o que congelan objetos."""
        m, u = self.m, self.por_id[uid]
        ids = self.piezas_de(uid)
        ant = self.copia(self.version_base(uid))
        visibles = lambda bloque: [x[:160] for x in (mo.sin_comentarios(l).strip() for l in bloque) if x]
        nuevas, cambian, anuladas = [], [], []
        for pid in sorted({m.raiz_de(x) for x in ids if x in m.piezas and m.piezas[x].doc != "D"}, key=orden):
            p = m.piezas[pid]
            ficha = {"id": pid, "tipo": p.tipo, "titulo": p.titulo}
            if p.anulada:
                anuladas.append(ficha)
            elif self.nueva(pid, uid):
                nuevas.append(ficha)
            else:
                antes = visibles(ant.bloque(pid)) if ant and pid in ant.piezas else []
                ahora = visibles(m.bloque(pid))
                if ant and antes == ahora:
                    continue
                cambian.append({**ficha, "antes": [l for l in antes if l not in ahora][:3],
                                "despues": [l for l in ahora if l not in antes][:3]})
        de_tipo = lambda lista, t: [f["id"] for f in lista if f["tipo"] == t]
        tocadas = de_tipo(nuevas, "HU") + de_tipo(cambian, "HU")
        lugar = lambda h: {x for k in ("pantalla", "paso") for x in mo.ids_en(m.campos(h).get(k, ""))}
        comparten = set().union(*(lugar(h) for h in tocadas)) if tocadas else set()
        conservan = [h.id for h in sorted(m.vigentes("HU"), key=lambda p: orden(p.id))
                     if h.id not in tocadas and lugar(h.id) & comparten]
        pantallas = sorted(set(de_tipo(nuevas, "PAN") + de_tipo(cambian, "PAN"))
                           | {x for h in tocadas for x in mo.ids_en(m.campos(h).get("pantalla", "")) if x in m.piezas},
                           key=orden)
        pasos = set(de_tipo(nuevas + cambian + anuladas, "ACT"))
        diagramas = sorted(f.name for f in (m.analisis / "diagramas").glob("*") if f.suffix in (".json", ".mmd")
                           and pasos & set(re.findall(r"ACT-\d+", f.read_text(encoding="utf-8", errors="replace"))))
        suyas = ids | {f["id"] for f in nuevas + cambian + anuladas}
        tecnico = set()
        if "T" in m.docs:
            T = m.docs["T"]
            tecnico = {f"§{T.seccion_de_linea[i]}" for i, l in enumerate(T.lineas)
                       if T.seccion_de_linea[i] not in ("2", "") and mo.ids_en(mo.sin_comentarios(l)) & suyas}
            tecnico |= {p.id for p in m.vigentes("DT") if p.id in suyas or set(p.refs) & suyas}
            tecnico |= {"§13"} if self.filas_de(uid) else set()
            dt = self.dt_construido(uid)
            tecnico |= {dt.id} if dt else set()
        criterios = sorted((h for x in tocadas + de_tipo(nuevas + cambian, "INT") for h in m.piezas[x].hijos
                            if not m.piezas[h].anulada), key=orden)
        por_donde = set(tocadas) | pasos | {x for h in tocadas for x in mo.ids_en(m.campos(h).get("paso", ""))}
        escenarios = [e.id for e in m.vigentes("ESC") if set(e.refs) & por_donde]   # los que pasan por lo tocado
        mias = set(self.cambian(uid))
        r14 = m.docs["T"].seccion("14") if "T" in m.docs else None
        l14 = m.docs["T"].lineas[r14[0]:r14[1]] if r14 else []
        prueba = lambda uid_: next((" · ".join(c for c in mo.celdas(mo.sin_comentarios(l))[1:] if c.strip(" —-"))
                                    for l in l14 if l.startswith("|") and uid_ in RX_UNIDAD.findall(l)), "")
        urgentes = [{"id": v.id, "objetos": comunes, "prueba": prueba(v.id)}
                    for v in self.unidades if v.urgente and v.id != uid and v.estado != DESCARTADA
                    for comunes in [[o for o in self.objetos_urg(v.id) if o in mias]] if comunes]
        colisiones = []
        for v in self.unidades:
            if v.id == uid or v.estado not in EN_CURSO:
                continue
            comunes = [o for o in (self.objetos_urg(v.id) if v.urgente else self.cambian(v.id)) if o in mias]
            if comunes:
                decision = "; ".join(c for c in (u.comparte, v.comparte) if not vacio(c)
                                     and (v.id in RX_UNIDAD.findall(c) or uid in RX_UNIDAD.findall(c)))
                colisiones.append({"unidad": v.id, "estado": v.estado, "objetos": comunes, "decision": decision})
        return {"unidad": uid, "titulo": u.titulo, "tipo": u.tipo, "estado": u.estado, "informes": self.informes_de(uid),
                "base": "%d.%d" % self.version_base(uid) if self.version_base(uid) else None,
                "version": "%d.%d" % m.version("F") if m.version("F") else None,
                "copiaBase": bool(ant), "piezas": {"nuevas": nuevas, "cambian": cambian, "anuladas": anuladas},
                "historias": {"nuevas": de_tipo(nuevas, "HU"), "cambian": de_tipo(cambian, "HU"),
                              "anuladas": de_tipo(anuladas, "HU"), "seConservan": conservan},
                "pantallas": pantallas, "diagramas": diagramas,
                "tecnico": sorted((x for x in tecnico if x.startswith("DT")), key=orden)
                + sorted((x for x in tecnico if x.startswith("§")), key=lambda x: int(re.sub(r"\D", "", x) or 0)),
                "objetos": [{"objeto": o, "tipo": f["tipo"], "situacion": f["situacion"].capitalize(),
                             "sustituye": f["sustituye"]} for f in self.filas_de(uid) for o in f["objetos"]],
                "pruebas": {"criterios": criterios, "escenarios": escenarios, "urgentes": urgentes},
                "colisiones": colisiones,
                "reaplicar": [{"urgente": g, "objetos": o} for g, o in self.reaplicar(uid)],
                "congelados": [{"urgente": g, "objetos": o} for g, o in self.congelados(uid)]}

    def campos_3(self, P, nombre):
        """[{nombre, tipo}] de la tabla de campos del apartado de técnico §3 de un record type o CDT («### 3.n <nombre>»)
        en el análisis P, o None si no tiene apartado. El tipo, solo si verificar lo entiende (TIPOS_CAMPO)."""
        if "T" not in P.docs:
            return None
        L = P.docs["T"].lineas
        ini = next((i for i, l in enumerate(L) if P.docs["T"].seccion_de_linea[i] == "3" and l.startswith("### ")
                    and mo.normaliza(re.sub(r"^###\s+[\d.]*\s*", "", l).strip(" `")) == mo.normaliza(nombre)), None)
        if ini is None:
            return None
        out, cab = [], None
        for l in L[ini + 1:]:
            if l.startswith("#"):
                break
            c = mo.celdas(l) if l.startswith("|") else None
            if c is None or re.match(r"^[-:\s]+$", c[0]):
                cab = None if c is None else cab
                continue
            if cab is None:
                cab = [mo.normaliza(x) for x in c]
            elif cab[0] == "campo":
                tipo = TIPOS_CAMPO.get(mo.normaliza(c[1]).strip() if len(c) > 1 else "")
                out.append({"nombre": c[0].strip("` "), **({"tipo": tipo} if tipo else {})})
        return out

    def esperado(self, uid):
        """{objeto: {"tipo", "campos"}} de lo que construye o cambia una unidad, para verificar --esperado: el tipo de su
        fila de §13 y, de un record type o CDT con su apartado en técnico §3, sus campos; de uno que se modifica, solo
        los de esta unidad (los que no estaban en la copia de su versión base)."""
        out = {}
        base = self.copia(self.version_base(uid))
        vs = self.versiones_de(uid)
        despues = self.copia(vs[-1]) if vs and vs[-1] != self.m.version("F") else None
        for f in self.filas_de(uid):
            if f["situacion"] not in CAMBIAN:
                continue
            t = mo.normaliza(f["tipo"])
            tipo = next((c for k, c in TIPOS_APPIAN if k in t), None)
            for o in map(objeto, f["objetos"]):
                e = out.setdefault(o, {})
                if tipo:
                    e["tipo"] = tipo
                campos = self.campos_3(despues or self.m, o) if tipo in ("recordType", "cdt") else None
                if campos is not None:
                    antes = {c["nombre"] for c in (self.campos_3(base, o) or [])} if base and f["situacion"] == "modifica" \
                        else set()
                    e["campos"] = [c for c in campos if c["nombre"] not in antes]
        return out

    # ------------------------------------------------------------ señales por pieza
    def base(self):
        """Quién tiene lo que no es de ninguna unidad: la aplicación actual (as-is/) o la construcción inicial (EV-01)."""
        return "as-is" if self.inventario is not None else ("EV-01" if "EV-01" in self.por_id else None)

    def nueva(self, pid, uid):
        """Si la pieza no existía antes de la unidad: no está en la copia de su versión base o, sin copia, la crea un
        punto NUEVO."""
        ant = self.copia(self.version_base(uid))
        if ant is not None:
            return pid not in ant.piezas and self.m.raiz_de(pid) not in ant.piezas
        return any(mo.normaliza(p.get("tipo", "")).strip(" *`").startswith("nuevo") and pid in mo.ids_en(
            p.get("cambio propuesto", "")) for _, _, p in self.puntos_de(uid) if p)

    def senales(self, pid):
        """(construido, en curso): las unidades (y la base) en las que está la pieza, construidas o sin pasar a producción."""
        r = self.m.raiz_de(pid)
        suyas = [u for u in self.unidades if u.estado != DESCARTADA and ({pid, r} & self.raices_de(u.id, False))]
        construido, curso = [], [u.id for u in suyas if u.estado in EN_CURSO]
        base = self.base()
        if base == "EV-01" and not suyas and pid in self.m.piezas:
            suyas, curso = [self.por_id["EV-01"]], (["EV-01"] if self.por_id["EV-01"].estado in EN_CURSO else [])
        elif base == "as-is" and pid in self.m.piezas and (not suyas or not self.nueva(pid, suyas[0].id)):
            construido.append("as-is")
        construido += [u.id for u in suyas if u.estado in CONSTRUIDAS]
        return list(dict.fromkeys(construido)), curso

    def texto_senales(self, pid):
        c, e = self.senales(pid)
        return f"Construido: {', '.join(c) or '—'} · En curso: {', '.join(e) or '—'}"
