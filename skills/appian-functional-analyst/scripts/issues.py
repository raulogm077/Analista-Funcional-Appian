"""Las issues de construcción de una unidad de cambio (references/cambios.md §5), en <p>/construccion/<U>/:

  indice.md                  cada issue con sus requisitos, de cuáles depende, con cuáles puede ir a la vez, sus objetos
                             y quién la tiene reservada; y las pruebas que una persona ha marcado como no necesarias
                             para avanzar, con su motivo (--sin-prueba)
  ISS-nn.md                  lo que necesita quien la construye y nada más: qué se pide, sus escenarios y cómo se
                             comprueba cada uno, sus objetos, lo que dice de ellos el técnico y lo que no debe tocar
  ISS-nn.feature             sus escenarios en Gherkin: los criterios de sus historias que la unidad construye o cambia
  ISS-nn-esperado.json       lo que comprueba «verificar --esperado» (ingeniería inversa) y de qué versión de la issue es
  verificacion/ISS-nn.json   lo deja «verificar»: dice si la issue está hecha

Salen del análisis y no se editan: se vuelven a generar. Una issue por requisito de técnico §13 (columna «Para»); los
requisitos que comparten pantalla o proceso van juntos, y lo «Base», lo primero. Con los mismos datos salen las mismas, con
el mismo número; si el análisis cambia, cada una conserva el suyo (lo lee del índice). No hay estado que mantener a mano:
una issue está hecha cuando su última verificación pasa y es de su versión de ahora. Lo único que se guarda es la reserva,
en el índice, que se confirma y se sube con git para que dos no se lleven la misma.

Lo esperado y la verificación, que es de donde sale si una issue está hecha (estado()):
  ISS-nn-esperado.json      {"_issue": {"id": "ISS-03", "unidad": "EV-01", "version": "<12 hex>", "pruebas": true},
                             "<objeto>": {"tipo": "interface"},
                             "<record type o CDT>": {"tipo": "recordType", "campos": [{"nombre": "x", "tipo": "Text"}]},
                             "<record type de una acción>": {"acciones": [{"nombre": "Pedir material", "tipo": "De lista"}]}}
                            «version» es la huella de lo que hay que construir y comprobar (redacta()): cambia si cambia
                            la issue, no si cambian su orden o su reserva. «pruebas» es false si la issue no cambia
                            criterios ni reglas: «verificar» no ejecuta entonces ningún caso de prueba.
  verificacion/ISS-nn.json  el resultado de «verificar --esperado»: {"generadoEn", "entorno", "issue": <la de _issue, tal
                            cual>, "aplicacion", "objetos": [{"pedido", "existe", "tipo", "diferencias": {…}, …}],
                            "faltan", "conDiferencias", "pruebas": {"ejecutadas", "motivo" o "objetos": [{"objeto",
                            "de": issue | usa, "casos", "pasan", "fallan": [{"caso", "error"}], "noEvaluables", "error"}]}}.
                            Hecha: «issue» es la de ahora (id y version), cada objeto suyo está en «objetos» con «existe»
                            y sin diferencias (de uno que se modifica, «sobranCampos» no cuenta; «camposSinLeer» y
                            «accionesSinLeer» son no haberlo podido leer) y, si tiene pruebas, no falla ningún caso de sus
                            objetos («de»: issue) que una persona no haya marcado como no necesario. Lo que falla en lo
                            que la usa («de»: usa) es un aviso, y si el Dev MCP no ejecuta casos, esperan a la regresión.
  qa/<U>/resultado.json     lo deja appian-qa al repetir los guiones del QA de la unidad: {"escenarios": {"HU-01.1":
                            {"resultado": "pasa" | "falla" | "desfasado" | "guion por terminar", "paso", "motivo", …}}}.
                            Un escenario suyo que «falla» la devuelve a pendiente, salvo que una persona lo haya marcado
                            como no necesario (en el índice, como un caso de prueba, con «QA» por objeto); sin QA, o con
                            su guion desfasado o por terminar, no cuenta, y avisos_qa() lo dice al marcar la unidad.

Lo usan indice.py issues (generar, dar la siguiente) y proyecto.py cambio (al aprobar la unidad y al marcarla construida).
"""
import datetime
import hashlib
import json
import os
import pathlib
import re
import shutil
import sys
import time
from dataclasses import dataclass, field
from urllib.parse import urlparse
sys.dont_write_bytecode = True  # sin __pycache__ en el plugin: no se escribe fuera del proyecto

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import modelo as mo
import unidades as un

SKILL = pathlib.Path(__file__).resolve().parents[1]
VERIFICAR = SKILL.parent / "appian-reverse-engineering" / "scripts" / "devmcp_extract.py"   # junto a esta skill, en el plugin
CARPETA, INDICE = "construccion", "indice.md"
COLUMNAS = ["Issue", "Requisitos", "Título", "Depende de", "En paralelo con", "Objetos", "Reservada"]
TIPOS = ["HU", "INT", "PAN", "ACT"]                    # lo que puede llevar «Para», en el orden en que se enseña
PANTALLA_O_PROCESO = ("interfaz", "interface", "process model", "modelo de proceso")
REGLAS = ("regla de expresion", "expression rule", "decision")
SIN_APARTADO = ("", "0", "1", "2", "13", "14", "15")   # del técnico, lo que no es de ningún objeto (las DT van aparte)
INTENTOS = 5            # veces que se vuelve a mirar si otro sube su reserva antes
ESPERA_REMOTO = 30      # segundos que se espera al remoto en cada orden
# segundos que se espera a otra sesión de esta carpeta (menos que los 120 que deja Claude Code a una orden), y cuándo
# se da por muerta
ESPERA_CANDADO, CANDADO_VIEJO = 20, 300
RX_ISSUE = re.compile(r"ISS-(\d+)")
RX_NOMBRE = re.compile(r"`([^`]+)`")
RX_SEPARADOR = re.compile(r"^\|[\s:|-]+\|?\s*$")
RX_NO_SE_CONSTRUYE = re.compile(r"!\[|historias?:")   # de una ficha: la captura (va aparte) y «Historias: …»


class NoSePuede(Exception):
    """La unidad no tiene issues que generar: no está aprobada, ha crecido o no tiene objetos en técnico §13."""


@dataclass
class Issue:
    filas: list                                    # sus filas de técnico §13
    requisitos: list = field(default_factory=list)  # HU, INT, PAN y ACT, en orden
    comun: bool = False                            # lo «Base» y lo que no dice «Para»: se construye lo primero
    id: str = ""
    titulo: str = ""
    objetos: list = field(default_factory=list)    # los que construye o cambia, sin la parte («X — acción…» es X)
    situacion: dict = field(default_factory=dict)  # objeto → nuevo | modifica
    criterios: list = field(default_factory=list)  # los que construye o cambia la unidad: sus escenarios
    nombra: set = field(default_factory=set)       # objetos de la unidad que nombra el técnico al hablar de ella
    depende: list = field(default_factory=list)
    paralelo: list = field(default_factory=list)
    sin_pruebas: bool = False                      # no cambia criterios ni reglas: no hay pruebas que ejecutar
    sin_gherkin: list = field(default_factory=list)
    version: str = ""
    texto: str = ""                                # ISS-nn.md
    feature: str = ""                              # ISS-nn.feature, o "" sin escenarios
    esperado: dict = field(default_factory=dict)   # ISS-nn-esperado.json
    sueltas: set = field(default_factory=set)      # líneas del técnico que no son de ninguna issue y van en esta

    @property
    def para(self):
        """Lo que va en «Requisitos»: «Base», los requisitos o los dos."""
        return ", ".join((["Base"] if self.titulo == "Base" else []) + self.requisitos) or "—"


@dataclass
class Plan:
    uid: str
    titulo: str
    app: str
    issues: list
    avisos: list
    reservas: dict = field(default_factory=dict)   # issue → «quién · desde cuándo», del índice
    marcas: list = field(default_factory=list)     # pruebas no necesarias para avanzar: [{issue, objeto, caso, motivo,
    #                                                quien, cuando}], del índice (--sin-prueba)
    revisar: list = field(default_factory=list)    # lo que una persona revisa antes de construir (T14, unidades.py)


def clave(pid):
    pre = pid.split("-")[0]
    return (TIPOS.index(pre) if pre in TIPOS else 9, pre, [int(x) for x in re.findall(r"\d+", pid)])


def numero(iid):
    return int(RX_ISSUE.search(iid).group(1))


def carpeta(raiz, uid):
    return pathlib.Path(raiz) / CARPETA / uid


def lista(xs, vacio="—"):
    return ", ".join(xs) or vacio


def limpio(texto):
    return re.sub(r"\s+", " ", mo.sin_comentarios(texto)).strip()


def nombrados(texto, de):
    """Los objetos de `de` que un texto nombra: entre comillas invertidas (sin la parte ni el prefijo de tipo) o en
    negrita, como el nombre de un process model encima de su tabla de nodos."""
    en_comillas = {un.objeto(o) for o in un.objetos_celda(texto)} if "`" in texto else set()
    return (en_comillas | {x.strip() for x in re.findall(r"\*\*([^*\n]+)\*\*", texto)}) & de


def bloques(D):
    """De cada línea de un documento, el título en negrita bajo el que está en su apartado («**AUT Tramitar Solicitud**
    (…)» encima de sus nodos), normalizado; "" si no está bajo ninguno. Dos procesos tienen nodos con el mismo nombre."""
    out, actual = [], ""
    for l in D.lineas:
        actual = "" if l.startswith("#") else actual
        t = re.match(r"^\*\*([^*\n]+)\*\*", l)
        actual = mo.normaliza(t.group(1)) if t else actual
        out.append(actual)
    return out


def aplicacion(m):
    """El nombre de la aplicación: el del inventario de as-is/ o el de la fila «Aplicación» de técnico §0."""
    inv = m.raiz / "as-is" / "datos" / "inventario.json"
    app = json.loads(inv.read_text(encoding="utf-8")).get("aplicacion", {}).get("nombre") if inv.is_file() else None
    if not app:
        fila = next((f for _, _, fs in m.tablas("T", "0") for f in fs if f and mo.normaliza(f[0]) == "aplicacion"), None)
        if fila and len(fila) > 1 and not un.vacio(fila[1]):
            app = (RX_NOMBRE.findall(fila[1]) or [limpio(fila[1])])[0]
    return app


# La fila de cada entorno en técnico §0 (tecnico-plantilla.md §0), con su etiqueta exacta: «URL de preproducción» no es
# la de producción
URL_DE = {"desarrollo": "URL de desarrollo", "pruebas": "URL de pruebas", "producción": "URL de producción",
          "corrección": "URL del entorno de corrección"}


def url_de(m, entorno):
    """La URL de un entorno («desarrollo», «pruebas», «producción», «corrección»): la de su fila de técnico §0 (URL_DE),
    o None."""
    for _, _, filas in m.tablas("T", "0"):
        for f in filas:
            if f and len(f) > 1 and mo.normaliza(limpio(f[0]).strip("* ")) == mo.normaliza(URL_DE[entorno]):
                url = re.search(r"https?://[^\s`|<>)]+", f[1])
                if url:
                    return url.group(0).rstrip(".,;")
    return None


# ------------------------------------------------------------------ el reparto: de las filas de §13 a las issues
def para_de(m, celda):
    """(es Base, requisitos, criterios) de una celda «Para» de técnico §13: lo común dice «Base»; lo demás, las piezas
    que cita. Un criterio (HU-03.2) cuenta como su historia y además se queda como escenario de la issue, cambie o no
    (el que no se cumple, en un defecto)."""
    ids = {x for x in mo.ids_en(celda) if x in m.piezas and not m.piezas[x].anulada}
    return (bool(re.search(r"(?<!\w)base(?!\w)", mo.normaliza(celda))), {m.raiz_de(x) for x in ids},
            {x for x in ids if m.piezas[x].tipo == "CA"})


class Unidad:
    """Lo que se sabe de una unidad para repartirla: sus filas de §13, sus piezas y con qué se compara lo que cambia."""

    def __init__(self, m, ctx, uid):
        self.m, self.ctx, self.uid = m, ctx, uid
        self.filas = [f for f in ctx.filas_de(uid) if f["situacion"] in un.CAMBIAN]
        self.resumen = ctx.resumen(uid)
        self.ids = ctx.piezas_de(uid)
        self.inicial = ctx.sin_id == uid       # la construcción inicial de una aplicación nueva: todo es suyo
        self.ant = None if self.inicial else ctx.copia(ctx.version_base(uid))
        if self.inicial:
            self.suyas = {p.id for p in m.piezas.values() if p.doc == "F" and p.forma != "criterio" and not p.anulada
                          and uid in sum(ctx.senales(p.id), [])}
        else:
            self.suyas = {x for x in ctx.raices_de(uid) if x in m.piezas and m.piezas[x].forma != "criterio"
                          and not m.piezas[x].anulada}
        self.estado = {x["id"]: e for e, k in (("nueva", "nuevas"), ("cambia", "cambian"))
                       for x in self.resumen["piezas"][k]}
        self.todos = {un.objeto(o) for f in self.filas for o in f["objetos"]}
        self.explicitos = set()                # criterios citados uno a uno en «Para»

    def cambia(self, cid):
        """Si la unidad construye o cambia un criterio: lo cita su «Para» o uno de sus informes, su historia es nueva,
        o su texto no es el de la copia de la versión base. En la construcción inicial, todos los de sus historias."""
        m, hu = self.m, self.m.piezas[cid].padre
        if cid in self.explicitos or cid in self.ids:
            return True
        if hu not in self.suyas:
            return False
        if self.inicial or self.ctx.nueva(hu, self.uid):
            return True
        if self.ant is not None:
            return cid not in self.ant.piezas or limpio(self.ant.criterio(cid)) != limpio(m.criterio(cid))
        return hu in self.ids and not any(h in self.ids for h in m.piezas[hu].hijos)


def reparte(d):
    """Las filas de técnico §13 de la unidad, repartidas en issues: una por requisito de «Para»; van juntos los que
    comparten una celda, una historia con su pantalla o su paso, y los que tocan la misma interfaz o el mismo process
    model. Lo «Base» y lo que no dice «Para», en una, que se construye la primera. Devuelve (issues, objetos sin «Para»)."""
    m = d.m
    paras = [para_de(m, f["para"]) for f in d.filas]
    d.explicitos = set().union(*(p[2] for p in paras))
    nodos = set().union(*(p[1] for p in paras))
    padre = {}

    def raiz(x):
        while padre.setdefault(x, x) != x:
            x = padre[x]
        return x

    def une(a, b):
        ra, rb = sorted((raiz(a), raiz(b)), key=clave)
        padre[rb] = ra
    for _, reqs, _ in paras:
        orden = sorted(reqs, key=clave)
        for x in orden[1:]:
            une(orden[0], x)
    for h in m.vigentes("HU"):      # una historia va con su pantalla y con su paso, si alguna fila es «Para» ellos
        for x in {y for k in ("pantalla", "paso") for y in mo.ids_en(m.campos(h.id).get(k, ""))} & nodos:
            if h.id in nodos or h.id in d.suyas:
                une(h.id, x)
    de_objeto = {}
    for f, (base, reqs, _) in zip(d.filas, paras):      # la misma pantalla o el mismo proceso, en la misma issue
        if not base and reqs and any(k in mo.normaliza(f["tipo"]) for k in PANTALLA_O_PROCESO):
            for o in map(un.objeto, f["objetos"]):
                une(de_objeto.setdefault(o, min(reqs, key=clave)), min(reqs, key=clave))
    comunes, sin_para, por_raiz = [], [], {}
    for f, (base, reqs, _) in zip(d.filas, paras):
        if base or not reqs:
            comunes.append(f)
            sin_para += [] if base else f["objetos"]
        else:
            por_raiz.setdefault(raiz(min(reqs, key=clave)), []).append(f)
    issues = [Issue(filas, sorted((x for x in padre if raiz(x) == r), key=clave)) for r, filas in por_raiz.items()]
    if comunes:
        de_otras = {x for i in issues for x in i.requisitos}
        sueltos = sorted((x for x in d.suyas - de_otras if x.split("-")[0] in TIPOS), key=clave) if sin_para else []
        issues.append(Issue(comunes, sueltos, comun=True))
    paso = lambda f: (int((re.findall(r"\d+", mo.sin_comentarios(f["paso"])) or [10 ** 6])[0]), f["orden"])
    issues.sort(key=lambda i: (not i.comun, min(paso(f) for f in i.filas)))
    for i in issues:
        i.filas.sort(key=paso)
        i.objetos = list(dict.fromkeys(un.objeto(o) for f in i.filas for o in f["objetos"]))
        for f in i.filas:
            for o in map(un.objeto, f["objetos"]):
                if i.situacion.get(o) != "nuevo":      # un objeto que se crea y del que además cambia una parte es nuevo
                    i.situacion[o] = "nuevo" if f["situacion"] in ("nuevo", "sustituye") else "modifica"
        con_criterios = [x for x in i.requisitos if x.split("-")[0] in mo.CON_CRITERIOS]
        i.criterios = [c for h in con_criterios for c in dict.fromkeys(m.piezas[h].hijos)
                       if not m.piezas[c].anulada and d.cambia(c)]
        i.sin_pruebas = not i.criterios and not any(k in mo.normaliza(f["tipo"]) for f in i.filas for k in REGLAS)
        if len(issues) == 1 and not any(p[0] for p in paras):
            i.titulo = d.resumen["titulo"]      # un solo cambio: la issue es la unidad
        elif i.comun:
            i.titulo = "Base"
        else:
            i.titulo = m.piezas[(con_criterios or i.requisitos)[0]].titulo
    return issues, sin_para


# ------------------------------------------------------------------ lo que dice el técnico de una issue
def lineas_del_tecnico(d):
    """Las líneas de los apartados 3 a 12 del técnico, cada una con lo que hace falta para saber de qué issue es:
    {i, donde («§7», «§3.1»), texto, cabecera (si es la fila de una tabla), titulo (la línea que precede a su tabla),
    ids que cita, objetos que nombra, de (el objeto de su apartado «### 3.n <nombre>») y estado frente a la copia de la
    versión base, en su apartado y bajo el mismo título en negrita (bloques()): "" (no hay copia), igual, nuevo o cambia
    (con «era», sus celdas de antes)}. Nombra un objeto la línea
    que lo dice entre comillas invertidas o en negrita, la fila con una celda que es su nombre, la fila de una tabla cuyo
    título lo nombra («**AUT Tramitar Solicitud** (…)» encima de sus nodos) y lo que sigue a un título en negrita que lo
    nombra, hasta el siguiente o el apartado siguiente (la cancelación y el archivado de un proceso)."""
    m = d.m
    if "T" not in m.docs:
        return []
    T = m.docs["T"]
    nombres = {mo.normaliza(o): o for o in d.todos}
    # lo de antes, por apartado y por bloque: un nodo se compara con los de su proceso, no con el del mismo nombre de otro
    antes, de_bloque = {}, bloques(T)
    if d.ant is not None and "T" in d.ant.docs:
        A = d.ant.docs["T"]
        for i, (l, b) in enumerate(zip(A.lineas, bloques(A))):
            antes.setdefault((A.seccion_de_linea[i], b), []).append(l.strip())
    out, cabecera, titulo, apartado, de, previa, bloque = [], None, None, "", None, None, set()
    for i, l in enumerate(T.lineas):
        s = T.seccion_de_linea[i]
        if l.startswith("## "):
            cabecera, apartado, de, previa, bloque = None, "", None, None, set()
        if l.startswith("### "):
            sub = re.match(r"^###\s+([\d.]+)\s+(.+)$", l)
            apartado = sub.group(1).rstrip(".") if sub else ""
            de = nombres.get(mo.normaliza(sub.group(2).strip(" `"))) if sub else None
            bloque = set()
        if re.match(r"^\*\*[^*\n]+\*\*", l):     # un título en negrita: lo que sigue es de lo que nombra
            bloque = nombrados(re.match(r"^\*\*[^*\n]+\*\*", l).group(0), d.todos)
        if not l.startswith("|"):
            cabecera = None
            previa = (i, l) if l.strip() else previa
        elif cabecera is None:      # la primera fila de una tabla es su cabecera; la línea de encima dice de qué es
            cabecera = mo.celdas(l)
            titulo = previa[0] if previa and i - previa[0] <= 3 and not previa[1].startswith("#") else None
            continue
        if s in SIN_APARTADO or not l.strip() or l.startswith("#") or RX_SEPARADOR.match(l):
            continue
        fila = mo.celdas(l) if l.startswith("|") else None
        objetos = nombrados(l, d.todos) | bloque
        if fila:
            objetos |= {nombres[mo.normaliza(c.strip(" `*"))] for c in fila if mo.normaliza(c.strip(" `*")) in nombres}
            objetos |= nombrados(T.lineas[titulo], d.todos) if titulo is not None else set()
        item = {"i": i, "donde": f"§{apartado or s}", "texto": l.strip(), "cabecera": cabecera if fila else None,
                "titulo": titulo if fila else None, "ids": mo.ids_en(mo.sin_comentarios(l)), "de": de,
                "objetos": objetos, "estado": "", "era": None}
        if antes:
            previas = antes.get((s, de_bloque[i]), ())
            if l.strip() in previas:
                item["estado"] = "igual"
            else:
                era = next((mo.celdas(x) for x in previas if fila and x.startswith("|")
                            and mo.celdas(x)[:1] == fila[:1]), None)
                item["estado"], item["era"] = ("cambia", era) if era else ("nuevo", None)
        out.append(item)
    return out


def decisiones(d):
    """Las decisiones técnicas vigentes, como las líneas del técnico: con las piezas de su «Necesidad», los objetos que
    nombran y si son nuevas o cambian. La de «Cambio sobre lo construido» de la unidad va en su apartado de la issue."""
    m, propia = d.m, d.ctx.dt_construido(d.uid)
    out = []
    for p in sorted(m.vigentes("DT"), key=lambda p: mo.numero(p.id)):
        if propia and p.id == propia.id:
            continue
        campos = m.campos(p.id)
        dice = f"Decisión: {limpio(campos.get('decision', '')) or '—'}"
        if not un.vacio(campos.get("verificar")):
            dice += f" · Verificar: {limpio(campos['verificar'])}"
        estado = ""
        if d.ant is not None and "T" in d.ant.docs:
            estado = "nuevo" if p.id not in d.ant.piezas else \
                "igual" if limpio(d.ant.texto(p.id)) == limpio(m.texto(p.id)) else "cambia"
        out.append({"i": p.ini, "donde": p.id, "texto": dice, "dt": f"{p.id} {p.titulo}", "cabecera": None, "titulo": None,
                    "de": None, "era": None, "ids": {m.raiz_de(x) for x in mo.ids_en(campos.get("necesidad", ""))},
                    "objetos": nombrados(m.texto(p.id), d.todos), "estado": estado})
    return out


def lo_de_antes(antes, ahora):
    """Lo que decía una celda y ya no dice: las palabras de en medio, sin el principio ni el final que siguen igual («…
    el botón «Nueva solicitud» y…»); «—» si estaba vacía."""
    if un.vacio(antes):
        return "—"
    a, b = limpio(antes).split(), limpio(ahora).split()
    ini = next((k for k, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
    fin = next((k for k, (x, y) in enumerate(zip(reversed(a[ini:]), reversed(b[ini:]))) if x != y),
               min(len(a), len(b)) - ini)
    medio = a[max(ini - 2, 0):len(a) - max(fin - 2, 0)]      # con dos palabras de cada lado, para situarlo
    return ("… " if ini > 2 else "") + " ".join(medio) + (" …" if fin > 2 else "")


def en_palabras(item):
    """Una línea del técnico como va en la issue: la fila de una tabla, con el nombre de cada columna («Pantalla:
    PAN-03 · Qué es en Appian: …») y, si cambia, lo que decía cada celda que es distinta."""
    if not item["cabecera"]:
        return re.sub(r"^[-*]\s+", "", limpio(item["texto"]))
    celdas, era = mo.celdas(item["texto"]), item["era"] or []
    trozos = []
    for k, c in enumerate(celdas):
        if un.vacio(c):
            continue
        nombre = item["cabecera"][k] if k < len(item["cabecera"]) else ""
        de_antes = f" (antes: {lo_de_antes(era[k] if k < len(era) else '', c)})" \
            if item["estado"] == "cambia" and (k >= len(era) or era[k] != c) else ""
        trozos.append((f"{nombre}: " if nombre else "") + limpio(c) + de_antes)
    return " · ".join(trozos)


def citadas_por(m, requisitos):
    """Las reglas comunes, avisos, documentos e integraciones que citan unos requisitos o sus criterios."""
    return {x for h in requisitos for x in m.piezas[h].refs | {r for c in m.piezas[h].hijos for r in m.piezas[c].refs}
            if x in m.piezas and x not in requisitos and m.piezas[x].tipo in ("RB", "AV", "DOC", "INT")
            and not m.piezas[x].anulada}


def del_tecnico(d, issue, lineas, dts):
    """(líneas para la issue, dónde nombra el técnico cada fila suya de §13, objetos de la unidad que nombra, las líneas
    suyas). Son las líneas que nombran un objeto suyo o citan un requisito suyo o lo que este cita (sus avisos, sus
    documentos); de un objeto del que solo construye una parte («X — acción «Adjuntar informe»»), las que nombran esa
    parte, no todo lo que se dice de X. Si hay copia de la versión base y algo es nuevo o cambia, solo eso: lo que no
    cambia ya está construido."""
    m = d.m
    nombres = [o for f in issue.filas for o in f["objetos"]]
    enteros = {o for o in nombres if not un.parte(o)}
    # una parte se reconoce por lo que lleva entre comillas («Adjuntar informe») o, si no lleva nada, por su texto
    senas = {o: [mo.normaliza(x) for x in re.findall(r"«([^»]+)»", un.parte(o)) or [un.parte(o)]]
             for o in nombres if un.parte(o) and un.objeto(o) not in enteros}
    cita = set(issue.requisitos) | {c for h in issue.requisitos for c in m.piezas[h].hijos} | \
        citadas_por(m, issue.requisitos)
    de_parte = lambda x, o: any(s in mo.normaliza(x["texto"]) for s in senas[o])
    suya = lambda x: x["objetos"] & enteros or x["de"] in enteros or any(de_parte(x, o) for o in senas)
    mias = [x for x in lineas + dts if suya(x) or x["ids"] & cita or x["i"] in issue.sueltas and "dt" not in x]
    donde = {o: list(dict.fromkeys(x["donde"] for x in mias if (de_parte(x, o) if o in senas else
                                                               un.objeto(o) in x["objetos"] or x["de"] == un.objeto(o))))
             for o in nombres}
    cambian = [x for x in mias if x["estado"] in ("nuevo", "cambia")]
    hay_copia = any(x["estado"] for x in mias)
    # sin nada que cambie en el técnico (lo que cambia está en el funcional), lo que ya dice de sus objetos
    van = cambian or [x for x in mias if not hay_copia or suya(x)]
    T, puestas, out = (m.docs["T"].lineas if "T" in m.docs else []), {x["i"] for x in van if "dt" not in x}, []
    if hay_copia and van and not cambian:
        out.append(f"El técnico no cambia para esta issue con {d.uid}. Lo que ya dice de sus objetos:")
    for x in van:
        marca = {"nuevo": " (nuevo)", "cambia": " (cambia)"}.get(x["estado"], "")
        if "dt" in x:
            out.append(f"- {x['dt']}{marca} · {x['texto']}")
            continue
        if x["titulo"] is not None and x["titulo"] not in puestas:      # de qué es la tabla, una vez
            puestas.add(x["titulo"])
            out.append(f"- {x['donde']} · {limpio(T[x['titulo']])}")
        out.append(f"- {x['donde']}{marca} · {en_palabras(x)}")
    callan = len(mias) - len(van)
    if callan and cambian:
        out.append(f"- Y {callan} líneas más del técnico que no cambian con {d.uid}: lo que dicen ya está construido."
                   if callan > 1 else
                   f"- Y una línea más del técnico que no cambia con {d.uid}: lo que dice ya está construido.")
    return out, donde, set().union(*(x["objetos"] for x in van)) - set(issue.objetos), {x["i"] for x in mias if "dt" not in x}


# ------------------------------------------------------------------ el texto de una issue
def de_la_ficha(m, pid):
    """Lo que dice una ficha del funcional a quien construye: (sus frases, las filas de sus tablas con su cabecera); sin
    el título, las capturas, «Historias: …» ni los criterios, que van en «Escenarios»."""
    frases, tablas, cab, en_criterios = [], [], None, False
    for l in m.bloque(pid)[1:]:
        t = limpio(l)
        if l.startswith("|"):
            if cab is None:
                cab = mo.celdas(l)
            elif not RX_SEPARADOR.match(l):
                tablas.append((cab, mo.celdas(l)))
            continue
        cab = None
        if mo.RX_CRITERIO.match(l) or mo.normaliza(t).startswith("se acepta si"):
            en_criterios = True
        elif en_criterios and mo.RX_SIGUE.match(l):
            continue
        elif t and not RX_NO_SE_CONSTRUYE.match(mo.normaliza(t)):
            en_criterios = False
            frases.append(t)
    return frases, tablas


def captura(m, pid):
    """La captura de una pantalla en el prototipo, como ruta desde la carpeta del proyecto, o None."""
    img = re.search(r"!\[[^\]]*\]\(([^)\s]+)\)", m.texto(pid))
    partes = []
    for x in ("analisis/" + img.group(1)).replace("\\", "/").split("/") if img else []:
        if x == ".." and partes:
            partes.pop()
        elif x not in (".", "", ".."):
            partes.append(x)
    return "/".join(partes) or None


def lo_que_cambia(d, pid):
    """Las líneas de una ficha que ya no están y las que son nuevas frente a la copia de la versión base, sin los
    criterios (van en «Escenarios»); None si no hay copia o no estaba."""
    if d.ant is None or pid not in d.ant.piezas:
        return None
    dice = lambda P: [limpio(l) for l in P.bloque(pid)[1:] if limpio(l) and not mo.RX_CRITERIO.match(l)
                      and not RX_SEPARADOR.match(l) and not RX_NO_SE_CONSTRUYE.match(mo.normaliza(limpio(l)))]
    antes, ahora = dice(d.ant), dice(d.m)
    return [f"  - antes: {l}" for l in antes if l not in ahora] + [f"  - ahora: {l}" for l in ahora if l not in antes]


def que_se_pide(d, issue):
    """Lo que pide cada requisito de la issue: de lo nuevo, su ficha; de lo que cambia, el antes y el después; de lo
    demás, su título. Y las piezas que citan (reglas comunes, avisos, documentos), con su texto."""
    m, L, citadas = d.m, [], set()
    for pid in issue.requisitos:
        p = m.piezas[pid]
        estado = "" if d.inicial else d.estado.get(pid, "no cambia")
        foto = captura(m, pid) if p.tipo == "PAN" else None
        L.append(f"- **{pid} {p.titulo}**" + (f" ({estado})" if estado else "") + (f" · captura `{foto}`" if foto else ""))
        cambios = lo_que_cambia(d, pid) if estado == "cambia" else None
        if estado == "no cambia":
            continue
        if cambios is not None:
            L += cambios
        else:
            frases, tablas = de_la_ficha(m, pid)
            L += [f"  {f}" for f in frases]
            for cab, fila in tablas:
                datos = [(cab[k], c) for k, c in enumerate(fila) if k < len(cab) and not un.vacio(c)
                         and not (p.tipo == "HU" and mo.normaliza(cab[k]) in ("prioridad", "origen"))]
                L.append("  - " + " · ".join(c if k == 0 and p.tipo == "PAN" else f"{n}: {c}"
                                             for k, (n, c) in enumerate(datos)))
        citadas |= {x for x in p.refs | {r for h in p.hijos for r in m.piezas[h].refs}
                    if x in m.piezas and x not in issue.requisitos and m.piezas[x].tipo in ("RB", "AV", "DOC", "INT")
                    and not m.piezas[x].anulada}
    if citadas:
        L += ["", "Citan: " + "; ".join(f"{x} «{m.piezas[x].titulo}»" for x in sorted(citadas, key=un.orden)) + "."]
    return L


def como_se_comprueba(m):
    """{criterio: «SAIL CLI (QA de la unidad): …» o «Caso de prueba de `X`: …»} de técnico §14: su columna «Con qué»
    (un caso de prueba guardado o SAIL CLI) y «Cómo se prueba». Sin «Con qué», solo cómo se prueba."""
    out = {}
    for _, cab, filas in m.tablas("T", "14"):
        ncab = [mo.normaliza(c) for c in cab]
        if not ncab or not ncab[0].startswith("criterio"):
            continue
        con = next((k for k, c in enumerate(ncab) if c.startswith("con")), None)
        como = next((k for k, c in enumerate(ncab) if c.startswith("como")), 1)
        for f in filas:
            celda = lambda k: limpio(f[k]) if k is not None and k < len(f) and not un.vacio(f[k]) else ""
            metodo = celda(con)
            if mo.normaliza(metodo).startswith("sail"):
                metodo = "SAIL CLI (QA de la unidad)"
            dice = ": ".join(x for x in (metodo, celda(como)) if x)
            for cid in mo.ids_en(f[0] if f else ""):
                out.setdefault(cid, dice)
    return out


def escenarios(d, issue, pruebas):
    """(líneas de «Escenarios», el .feature, criterios sin dado, cuando y entonces). El .feature de una sola historia
    es el suyo; con varias, una «Regla» por historia bajo una sola «Característica», que Gherkin no admite más."""
    m = d.m
    if not issue.criterios:
        reglas = [f"`{o}`" for f in issue.filas if any(k in mo.normaliza(f["tipo"]) for k in REGLAS) for o in f["objetos"]]
        return (["Esta issue no cambia criterios ni reglas: no hay pruebas que ejecutar." if issue.sin_pruebas else
                 f"No cambia criterios, pero sí reglas ({', '.join(reglas)}): se prueban con sus casos de prueba."], "", [])
    L = [f"- `{c}` {limpio(m.criterio(c))} → {pruebas.get(c) or 'sin prueba en técnico §14'}" for c in issue.criterios]
    historias = list(dict.fromkeys(m.piezas[c].padre for c in issue.criterios))
    una = len(historias) == 1
    F = ["# language: es", f"Característica: {historias[0]} {m.piezas[historias[0]].titulo}" if una else
         f"Característica: {d.uid} {issue.id} {issue.titulo}"]
    sin = []
    for h in historias:
        lineas, s = m.escenarios(h, solo=set(issue.criterios))
        sin += s
        F += lineas if una else ["", f"  Regla: {h} {m.piezas[h].titulo}"] + [f"  {l}" if l else l for l in lineas]
    return L, "\n".join(F) + "\n", sin


def redacta(d, issue, plan, lineas, dts, pruebas):
    """Escribe la issue: su texto, su .feature, lo esperado y su versión, que es la huella de lo que hay que construir
    y comprobar (no de con quién se ordena ni de quién la tiene): si eso cambia, vuelve a estar pendiente."""
    m, ctx, uid, r = d.m, d.ctx, d.uid, d.resumen
    pide = que_se_pide(d, issue)
    esc, issue.feature, issue.sin_gherkin = escenarios(d, issue, pruebas)
    tec, donde, _, _ = del_tecnico(d, issue, lineas, dts)
    filas = []
    for f in issue.filas:
        for o in f["objetos"]:
            sust = f" (sustituye a {', '.join(f'`{x}`' for x in f['sustituye'])})" if f["sustituye"] else ""
            filas.append(f"| `{o}` | {f['tipo']} | {f['situacion'].capitalize()}{sust} | {lista(donde.get(o, []))} |")
    suyos = set(issue.objetos)
    con_comillas = lambda objs: ", ".join(f"`{o}`" for o in objs if o in suyos)
    dt = ctx.dt_construido(uid)
    campos = m.campos(dt.id) if dt else {}
    construido = [f"- **{p}** ({con_comillas(objs)}): {limpio(campos.get(mo.normaliza(p), '')) or 'falta en la DT'}"
                  for p, objs in ctx.puntos_construido(uid).items() if suyos & set(objs)]
    prueba = {g["id"]: g["prueba"] for g in r["pruebas"]["urgentes"]}
    urgentes = [f"- Reaplicar {t['urgente']} en {con_comillas(t['objetos'])}: la corrección se hizo en el entorno de "
                "corrección; cuando su prueba pase en desarrollo"
                + (f" ({prueba[t['urgente']]})" if prueba.get(t["urgente"]) else "")
                + f", se confirma al marcar la unidad con `--reaplicada {t['urgente']}`"
                for t in r["reaplicar"] if suyos & set(t["objetos"])]
    urgentes += [f"- No tocar {con_comillas(t['objetos'])} hasta el pase de {t['urgente']} (se corrige en desarrollo)"
                 for t in r["congelados"] if suyos & set(t["objetos"])]
    otras = [f"- {c['unidad']} ({c['estado']}): {con_comillas(c['objetos'])} · {c['decision'] or 'sin decisión escrita'}"
             for c in r["colisiones"] if not c["unidad"].startswith("URG") and suyos & set(c["objetos"])]
    objetos_esperados = ctx.esperado(uid, issue.filas)
    huella = json.dumps([issue.requisitos, pide, esc, issue.feature, filas, tec, construido, urgentes, objetos_esperados],
                        ensure_ascii=False, sort_keys=True)
    issue.version = hashlib.sha256(huella.encode("utf-8")).hexdigest()[:12]
    issue.esperado = {"_issue": {"id": issue.id, "unidad": uid, "version": issue.version, "pruebas": not issue.sin_pruebas},
                      **objetos_esperados}
    revisar = [un.texto_revision(uid, x, suyos) for x in plan.revisar      # T14: un aviso, no una puerta
               if suyos & set(x["objetos"]) or set(issue.requisitos) & x["requisitos"]]
    de = {}      # de qué issue es cada objeto ajeno: de la primera que lo construye
    for i in plan.issues:
        for o in i.objetos if i is not issue else []:
            de.setdefault(o, i)
    con_nombre = lambda ids: lista([x + (" (Base)" if any(i.id == x and i.titulo == "Base" for i in plan.issues) else "")
                                    for x in ids])
    L = [f"# {issue.id} · {issue.titulo} · {uid}", "",
         "<!-- Lo genera indice.py issues a partir del análisis; no se edita: se vuelve a generar. -->", "",
         f"Requisitos: {issue.para} · Depende de: {con_nombre(issue.depende)} · En paralelo con: {lista(issue.paralelo)}"
         + (f" · Aplicación `{plan.app}`" if plan.app else ""), "",
         "Se construye solo lo de «Objetos», en el orden de la skill oficial de Appian (`change-planning`) y con las "
         "puertas que da la calibración de `appian-best-practices`. Lo que hace falta del análisis está aquí: no hay que "
         "leer el funcional ni el técnico."]
    if revisar:
        L += ["", "## Antes de construir", ""] + [f"- {x}." for x in revisar]
    if pide:
        L += ["", "## Qué se pide", ""] + pide
    L += ["", f"## Escenarios{f' ({issue.id}.feature)' if issue.feature else ''} y cómo se comprueban", ""] + esc
    L += ["", "## Objetos", "", "| Objeto | Tipo | Situación | En el técnico |", "|---|---|---|---|"] + filas
    ajenos = sorted(x for x in issue.nombra if x in de)
    if ajenos:
        L += ["", "No tocar ni crear, son de otra issue: " + ", ".join(f"`{o}` ({de[o].id})" for o in ajenos) + "."]
    if tec:
        L += ["", "## Lo que dice el técnico", ""] + tec
    if construido:
        L += ["", f"## Cambio sobre lo construido ({dt.id if dt else 'sin DT: comprobar.py lo avisa'})", ""] + construido
    if urgentes:
        L += ["", "## Correcciones urgentes", ""] + urgentes
    if otras:
        L += ["", "## Otras unidades sobre los mismos objetos", ""] + otras
    L += ["", "## Terminar", "",
          "Con los objetos construidos, se verifica en desarrollo, en solo lectura. El resultado queda en "
          f"`{CARPETA}/{uid}/verificacion/{issue.id}.json`: con él la issue está hecha. La orden, lista para copiar en "
          f"cada equipo, la imprime `appian-functional-analyst/scripts/indice.py issues <p> {uid} {issue.id}` (y "
          "`--siguiente`, al dar la issue). " + (PRUEBAS_NO if issue.sin_pruebas else PRUEBAS_SI), "", ORDENES, ""]
    issue.texto = "\n".join(L)


# De dónde salen las órdenes que nombran un script sin ruta: AGENTS.md, la copia de cada flujo en el proyecto y cada
# issue, ficheros que se comparten entre equipos y no pueden llevar la ruta del plugin de nadie (proyecto.py generados)
ORDENES = ("Una ruta o un script que van con el nombre de una skill (`appian-qa/scripts/qa.py`, o `appian-qa` · `qa.py`) "
           "son de esa skill: cárgala antes, su `SKILL.md` dice cuál es su carpeta, y no busques el plugin en el disco. Un "
           "agente que no carga skills los tiene en `skills/<skill>/` del plugin instalado (los scripts, en `scripts/`), "
           "en la ruta que sepa quien trabaja.")
PRUEBAS_NO = "No hay pruebas que ejecutar: la issue no cambia criterios ni reglas."
PRUEBAS_SI = ("«verificar» ejecuta también los casos de prueba guardados de sus reglas e interfaces y de lo que las usa; "
              "si uno falla, `appian-functional-analyst/references/cambios.md` §6.")


# ------------------------------------------------------------------ el plan de una unidad y sus ficheros
def lee_indice(texto):
    """Las issues de un índice: {issue: {requisitos, objetos, reservada}}; {} sin índice."""
    out, cab = {}, None
    for l in (texto or "").split("\n"):
        if not l.startswith("|"):
            cab = None
            continue
        c = mo.celdas(l)
        if cab is None:
            cab = [mo.normaliza(x) for x in c]
        elif RX_ISSUE.fullmatch(c[0].strip()) and "requisitos" in cab:
            celda = lambda k: c[cab.index(k)] if k in cab and cab.index(k) < len(c) else ""
            out[c[0].strip()] = {"requisitos": {x.strip() for x in celda("requisitos").split(",") if x.strip(" —-")},
                                 "objetos": set(RX_NOMBRE.findall(celda("objetos"))),
                                 "reservada": "" if un.vacio(celda("reservada")) else celda("reservada").strip()}
    return out


def indice_de(raiz, uid):
    f = carpeta(raiz, uid) / INDICE
    return lee_indice(f.read_text(encoding="utf-8") if f.is_file() else "")


MARCAS = "Pruebas marcadas como no necesarias para avanzar"
COLUMNAS_MARCAS = ["Issue", "Versión", "Objeto", "Caso", "Error", "Motivo", "Quién", "Cuándo"]
CLAVES_MARCAS = ["issue", "version", "objeto", "caso", "error", "motivo", "quien", "cuando"]
QA = "QA"               # el «objeto» de un escenario que falla en el QA de la unidad, como un caso de prueba (fallos_qa)


def celda(x):
    return " ".join(str(x).replace("|", "/").split())


def error_de(e):
    """El error de un caso como se guarda en su marca: en una línea y sin «|», hasta 160 caracteres."""
    return celda(e)[:160]


def lee_marcas(texto):
    """Las pruebas marcadas del índice: [{issue, version, objeto, caso, error, motivo, quien, cuando}], de la tabla de
    MARCAS. Una marca vale para esa versión de la issue y ese error: si cambia una de las dos, ya no."""
    out, cab = [], None
    for l in (texto or "").split("\n"):
        if not l.startswith("|"):
            cab = None
            continue
        c = mo.celdas(l)
        if cab is None:
            cab = [mo.normaliza(x) for x in c]
        elif cab == CLAVES_MARCAS and RX_ISSUE.fullmatch(c[0].strip()) and len(c) >= len(cab):
            x = dict(zip(cab, c))
            out.append({**x, "issue": x["issue"].strip(), "objeto": x["objeto"].strip("` "),
                        "version": x["version"].strip("` ")})
    return out


def marcas_de(raiz, uid):
    f = carpeta(raiz, uid) / INDICE
    return lee_marcas(f.read_text(encoding="utf-8") if f.is_file() else "")


def numera(issues, previas):
    """Da a cada issue su número: el que tenía la del índice con la que más requisitos (y, a igualdad, objetos)
    comparte; a las nuevas, los siguientes al mayor. Así, si cambia el análisis, cada issue conserva el suyo."""
    senas = lambda i: set(i.requisitos) | ({"Base"} if i.comun else set())
    pares = []
    for k, i in enumerate(issues):
        for iid, p in previas.items():
            nota = (len(senas(i) & p["requisitos"]), len(set(i.objetos) & p["objetos"]))
            if nota > (0, 0):
                pares.append((-nota[0], -nota[1], numero(iid), k, iid))
    libres = set(previas)
    for *_, k, iid in sorted(pares):
        if not issues[k].id and iid in libres:
            issues[k].id = iid
            libres.discard(iid)
    n = max([numero(x) for x in previas] or [0])
    for i in issues:
        if not i.id:
            n += 1
            i.id = f"ISS-{n:02d}"


def ordena(issues):
    """De qué issues depende cada una y con cuáles puede ir a la vez. Todas dependen de la Base. Dos que comparten
    objetos (una construye lo que la otra construye, o lo que el técnico nombra al hablar de la otra) no van a la vez:
    la que va después en técnico §13 espera a la otra. Las demás pueden ir en paralelo."""
    antes = {i.id: set() for i in issues}
    for k, i in enumerate(issues):
        for j in issues[:k]:
            comparten = set(i.objetos) & set(j.objetos) or i.nombra & set(j.objetos) or j.nombra & set(i.objetos)
            if j.comun or comparten:
                antes[i.id].add(j.id)

    def todas(iid, vistas):
        for x in antes[iid] - vistas:
            vistas.add(x)
            todas(x, vistas)
        return vistas
    previas = {i.id: todas(i.id, set()) for i in issues}
    for i in issues:
        i.depende = sorted(antes[i.id], key=numero)
        i.paralelo = sorted((j.id for j in issues if j is not i and j.id not in previas[i.id]
                             and i.id not in previas[j.id]), key=numero)


def calcula(m, ctx, uid):
    """El plan de issues de una unidad aprobada, sin escribir nada. NoSePuede si no hay qué construir o no se debe."""
    u = ctx.por_id[uid]
    if u.urgente:
        raise NoSePuede(f"{uid} es una URG: se corrige con su ficha, impacto/{uid}.md (references/urgentes.md)")
    if u.estado not in (un.APROBADA, un.CONSTRUIDA):
        raise NoSePuede(f"{uid} está {u.estado}: solo se construye una unidad aprobada "
                        f"(proyecto.py cambio <p> {uid} aprobada --fuente FU-nn)")
    crecida = ctx.crecida(uid)
    if crecida:   # lo añadido después de aprobarla no se construye sin aprobarlo (references/cambios.md)
        raise NoSePuede(f"{uid} ha crecido desde que se aprobó ({'; '.join(crecida)}): vuelve a aprobarla "
                        f"(`proyecto.py cambio <p> {uid} aprobada --fuente FU-nn`) o lleva lo nuevo a otra unidad")
    d = Unidad(m, ctx, uid)
    if not d.filas:
        raise NoSePuede(f"Técnico §13 no tiene objetos de {uid} (columna «Cambio»): no hay nada que construir")
    issues, sin_para = reparte(d)
    previas = indice_de(m.raiz, uid)
    numera(issues, previas)
    plan = Plan(uid, u.titulo, aplicacion(m), issues, [],
                {i: p["reservada"] for i, p in previas.items() if p["reservada"] and any(x.id == i for x in issues)},
                [x for x in marcas_de(m.raiz, uid) if any(i.id == x["issue"] for i in issues)], ctx.revisar_antes(uid))
    lineas, dts, pruebas = lineas_del_tecnico(d), decisiones(d), como_se_comprueba(m)
    cubiertas = set()
    for i in issues:      # lo que nombra el técnico al hablar de cada una dice con cuáles comparte objetos
        _, _, i.nombra, suyas = del_tecnico(d, i, lineas, dts)
        cubiertas |= suyas
    ordena(issues)
    # lo que el técnico dice para esta unidad (todo, en la construcción inicial; lo nuevo o lo que cambia, si no) y no
    # nombra ningún objeto suyo (la matriz de seguridad de §4, una constante que falta en §13): va en la Base o, sin
    # Base, en todas, porque la issue dice que no hace falta leer el técnico. Y se avisa al analista
    perdidas = [x for x in lineas if x["i"] not in cubiertas and (d.inicial or x["estado"] in ("nuevo", "cambia"))]
    base = [i for i in issues if i.comun] or issues
    for i in base:
        i.sueltas = {x["i"] for x in perdidas}
    for i in issues:
        redacta(d, i, plan, lineas, dts, pruebas)
    if perdidas:
        corta = lambda t: (t if len(t) <= 60 else t[:57].rstrip() + "…").replace("|", "/")   # noqa: E731
        plan.avisos.append(f"{len(perdidas)} {'línea' if len(perdidas) == 1 else 'líneas'} del técnico no nombran ningún "
                           f"objeto ni requisito de las issues de {uid} y van en "
                           + (f"la Base, {base[0].id}" if base is not issues else "todas")
                           + " (que nombren su objeto, o falta en §13): "
                           + "; ".join(f"{x['donde']} «{corta(limpio(x['texto']).strip('| '))}»" for x in perdidas))
    if len(d.todos) <= 1:     # con un solo objeto no hay nada que repartir: sin aviso de «Para»
        pass
    elif not ctx.con_para:
        plan.avisos.append("técnico §13 no tiene la columna «Para» (el requisito de cada objeto, o «Base»): toda la unidad "
                           "va en una sola issue")
    elif sin_para:
        plan.avisos.append(f"sin «Para» en técnico §13 (van con lo Base): {', '.join(f'`{o}`' for o in sin_para)}")
    en_issue = {x for i in issues for x in i.requisitos}
    sueltas = sorted((h for h in d.suyas - en_issue if h.split("-")[0] in mo.CON_CRITERIOS
                      and any(not m.piezas[c].anulada and d.cambia(c) for c in m.piezas[h].hijos)), key=clave)
    if sueltas:
        plan.avisos.append(f"con criterios que construye {uid} y sin ningún objeto «Para» ellas en técnico §13 (sus "
                           f"escenarios no van en ninguna issue): {', '.join(sueltas)}")
    sin = sorted({c for i in issues for c in i.sin_gherkin}, key=clave)
    if sin:
        plan.avisos.append(f"criterios sin dado, cuando y entonces (pasan tal cual al .feature): {', '.join(sin)}")
    return plan


def texto_indice(plan, reservas):
    L = [f"# Issues de {plan.uid} · {plan.titulo}", "",
         "<!-- Lo genera indice.py issues a partir del análisis; no se edita: se vuelve a generar. «Reservada» la escribe "
         "indice.py issues --siguiente. -->", "",
         "Una issue por requisito de técnico §13. Cada una espera a las de «Depende de» y puede ir a la vez que las de «En "
         "paralelo con». Está hecha cuando su última verificación (`verificacion/ISS-nn.json`) pasa y es de su versión de "
         f"ahora. La siguiente la da, y la reserva, `indice.py issues <p> {plan.uid} --siguiente`.", "",
         "| " + " | ".join(COLUMNAS) + " |", "|" + "---|" * len(COLUMNAS)]
    for i in plan.issues:
        L.append("| " + " | ".join([i.id, i.para, i.titulo.replace("|", "/"), lista(i.depende), lista(i.paralelo),
                                    ", ".join(f"`{o}`" for o in i.objetos), reservas.get(i.id) or "—"]) + " |")
    if plan.marcas:      # lo decide una persona; se revisa al preparar el paquete
        L += ["", f"## {MARCAS}", "",
              f"Las marca una persona con `indice.py issues <p> {plan.uid} ISS-nn --sin-prueba \"<objeto> «<caso>»\" "
              "--motivo \"…\"` (un escenario que falla en el QA, con `--sin-prueba HU-nn.m`, y «QA» por objeto), nunca "
              "en una sesión desatendida, y se revisan al preparar el paquete. Cada una vale para esa versión de la issue "
              "y ese error, y se quita sola cuando el caso vuelve a pasar o cambia.", "",
              "| " + " | ".join(COLUMNAS_MARCAS) + " |", "|" + "---|" * len(COLUMNAS_MARCAS)]
        L += ["| " + " | ".join([x["issue"], f"`{x['version']}`", f"`{celda(x['objeto'])}`", celda(x["caso"]),
                                 error_de(x["error"]), celda(x["motivo"]), celda(x["quien"]), celda(x["cuando"])]) + " |"
              for x in plan.marcas]
    return "\n".join(L) + "\n"


def escribe(plan, raiz, reservas=None):
    """Escribe en construccion/<U>/ el índice y los ficheros de cada issue, solo los que cambian, y quita los de las
    issues que ya no existen (su verificación, que es de ingeniería inversa, se queda). Las reservas son las del índice,
    salvo las de las issues ya hechas, que se quitan solas. Devuelve (escritos, retirados)."""
    destino = carpeta(raiz, plan.uid)
    destino.mkdir(parents=True, exist_ok=True)
    plan.marcas = [x for x in plan.marcas if sigue_marcada(raiz, plan, x)]
    hechas = {i.id for i in plan.issues if estado(raiz, plan.uid, i, plan.marcas)[0]}
    plan.reservas = {k: v for k, v in (plan.reservas if reservas is None else reservas).items() if k not in hechas}
    ficheros = {INDICE: texto_indice(plan, plan.reservas)}
    for i in plan.issues:
        ficheros[f"{i.id}.md"] = i.texto
        ficheros[f"{i.id}-esperado.json"] = json.dumps(i.esperado, ensure_ascii=False, indent=1) + "\n"
        if i.feature:
            ficheros[f"{i.id}.feature"] = i.feature
    escritos = []
    for nombre, texto in ficheros.items():
        f = destino / nombre
        if not f.is_file() or f.read_text(encoding="utf-8") != texto:   # si ya dice eso, no se toca (R2)
            mo.escribe(f, texto)
            escritos.append(nombre)
    retirados = [f.name for f in sorted(destino.glob("ISS-*")) if f.is_file() and f.name not in ficheros]
    for nombre in retirados:
        (destino / nombre).unlink()
    return escritos, retirados


def genera(m, ctx, uid):
    """Calcula las issues de la unidad y las deja escritas: (plan, escritos, retirados)."""
    plan = calcula(m, ctx, uid)
    return (plan, *escribe(plan, m.raiz))


# ------------------------------------------------------------------ hecha o pendiente: lo dice la verificación
def verificacion(raiz, uid, issue):
    """(la verificación de una issue, o None; por qué no la hay o no vale): la de construccion/<U>/verificacion/ISS-nn.json
    si es de esta issue y de su versión de ahora."""
    f = carpeta(raiz, uid) / "verificacion" / f"{issue.id}.json"
    if not f.is_file():
        return None, "sin verificar"
    try:
        v = json.loads(f.read_text(encoding="utf-8-sig"))
    except ValueError:
        v = None
    if not isinstance(v, dict):
        return None, f"verificacion/{f.name} no es el JSON de «verificar»: repítelo"
    de = v.get("issue") or {}
    if de.get("id") != issue.id or de.get("unidad", uid) != uid:
        return None, f"verificacion/{f.name} no es de esta issue: repite «verificar» con su «esperado»"
    if de.get("version") != issue.version:
        return None, "ha cambiado desde su última verificación"
    return v, ""


def casos(v, de="issue"):
    """[(objeto, caso, error)] de los casos que fallan en las pruebas de una verificación: los de los objetos de la issue
    (de="issue") o los de lo que la usa (de="usa")."""
    pr = (v or {}).get("pruebas")
    objetos = pr.get("objetos") if isinstance(pr, dict) and isinstance(pr.get("objetos"), list) else []
    return [(o.get("objeto"), c.get("caso"), c.get("error", "")) for o in objetos if isinstance(o, dict)
            and o.get("de") == de for c in o.get("fallan") or [] if isinstance(c, dict)]


def marcado(marcas, issue, objeto, caso, error):
    """Si una persona ha marcado ese caso, con ese error, en esta versión de la issue."""
    return any(x["issue"] == issue.id and x["version"] == issue.version and x["objeto"] == objeto and x["caso"] == caso
               and x["error"] == error_de(error) for x in marcas)


def estado(raiz, uid, issue, marcas=()):
    """(hecha, por qué): una issue está hecha cuando su última verificación (construccion/<U>/verificacion/ISS-nn.json,
    que deja «verificar --esperado») es de su versión de ahora, encuentra todos sus objetos como dice el técnico, si
    tiene pruebas, no falla ningún caso de prueba de sus objetos y no falla ninguno de sus escenarios en el QA de la
    unidad (falla_en_qa), salvo los que una persona haya marcado como no necesarios (`marcas`). De un objeto que se
    modifica, que tenga más campos que los de esta unidad no cuenta. Lo que falla en lo que la usa, los casos que el
    ejecutor no evalúa, los que no se pudieron ejecutar (esperan a la regresión, como sin Dev MCP que los ejecute) y las
    pruebas marcadas son avisos: van tras «hecha · …»."""
    def hecha(*avisos):     # con lo suyo bien, falta su QA: un escenario suyo que falla, sin marcar, la deja pendiente
        qa = falla_en_qa(raiz, uid, issue, marcas)
        if qa:
            return False, (f"falla en QA: {', '.join(qa)} (qa/{uid}/resultado.json); corregido, se repiten sus guiones "
                           f"(appian-qa: qa.py repetir <p> {uid})")
        return True, " · ".join(["hecha", *avisos, *(f"marcada como no necesaria: {o} «{c}»"
                                                      for o, c, _ in fallos_qa(raiz, uid, issue))])
    v, por_que = verificacion(raiz, uid, issue)
    if v is None:
        return False, por_que
    vistos = {o.get("pedido"): o for o in v.get("objetos", []) if isinstance(o, dict)}
    sin = [o for o in issue.objetos if o not in vistos]
    if sin:
        return False, f"la verificación no incluye {', '.join(sin)}"
    malos, sin_leer = [], []
    for o in issue.objetos:
        dif = dict(vistos[o].get("diferencias") or ({} if vistos[o].get("existe") else {"falta": True}))
        if [dif.pop(k, None) for k in ("camposSinLeer", "accionesSinLeer")] != [None, None]:   # no se pudo leer
            sin_leer.append(o)
        if dif and not (issue.situacion.get(o) == "modifica" and set(dif) <= {"sobranCampos"}):
            malos.append(f"{o}: {', '.join(dif)}")
    if malos:
        return False, f"lo construido no es lo del técnico: {'; '.join(malos)}"
    if sin_leer:
        return False, f"no se pudo leer {', '.join(sin_leer)} en el entorno"
    if issue.sin_pruebas:
        return hecha()
    pr = v.get("pruebas")
    if not isinstance(pr, dict):
        return False, "la verificación no dice cómo fueron sus pruebas: repite «verificar»"
    if not pr.get("ejecutadas"):
        return hecha(f"sus pruebas no se han ejecutado: {pr.get('motivo') or 'sin motivo'}")
    fallan = [(o, c) for o, c, e in casos(v) if not marcado(marcas, issue, o, c, e)]
    if fallan:
        return False, "fallan sus pruebas: " + "; ".join(f"{o} «{c}»" for o, c in fallan)
    sin_ejecutar = [o.get("objeto") for o in pr.get("objetos") or [] if isinstance(o, dict) and o.get("de") == "issue"
                    and o.get("error")]
    avisos = [f"no se pudieron ejecutar los casos de {', '.join(sin_ejecutar)}: esperan a la regresión"] if sin_ejecutar \
        else []
    avisos += [f"marcada como no necesaria: {o} «{c}»" for o, c, _ in casos(v)]
    avisos += [f"no se sabe qué la usa (no se pudieron leer los dependientes de {', '.join(pr['sinDependientes'])})"] \
        if pr.get("sinDependientes") else []
    avisos += [f"falla lo que la usa: {o} «{c}»" for o, c, _ in casos(v, "usa")]
    noev = sum(len(o.get("noEvaluables") or []) for o in pr.get("objetos") or [] if isinstance(o, dict))
    avisos += [f"{noev} {'caso' if noev == 1 else 'casos'} que el ejecutor de Appian no evalúa"] if noev else []
    return hecha(*avisos)


def sigue_marcada(raiz, plan, marca):
    """Si una prueba marcada sigue en el índice: es de la versión de ahora de su issue y su última verificación no es de
    esa versión (no se sabe) o el caso (o el escenario de QA) sigue fallando con el mismo error. Si la issue cambia, el
    caso vuelve a pasar o falla de otra manera, la marca se quita sola."""
    issue = next((i for i in plan.issues if i.id == marca["issue"]), None)
    if issue is None or marca["version"] != issue.version:
        return False
    v, _ = verificacion(raiz, plan.uid, issue)
    return v is None or marcado([marca], issue, *next(((o, c, e) for o, c, e in casos(v) + fallos_qa(raiz, plan.uid, issue)
                                                        if o == marca["objeto"] and c == marca["caso"]), ("", "", "")))


def fallos_qa(raiz, uid, issue):
    """[(QA, escenario, error)] de los escenarios de la issue que fallan en el último resultado del QA de la unidad
    (qa/<U>/resultado.json, de appian-qa), como casos(): el error es el paso y el motivo del fallo. [] si no hay QA o no
    falla ninguno."""
    r = pathlib.Path(raiz) / "qa" / uid / "resultado.json"
    try:
        esc = json.loads(r.read_text(encoding="utf-8-sig")).get("escenarios") if r.is_file() else None
    except (ValueError, AttributeError):
        esc = None
    esc = esc if isinstance(esc, dict) else {}
    return [(QA, c, ": ".join(str(x) for x in (esc[c].get("paso"), esc[c].get("motivo")) if x))
            for c in issue.criterios if isinstance(esc.get(c), dict) and esc[c].get("resultado") == "falla"]


def falla_en_qa(raiz, uid, issue, marcas=()):
    """Los escenarios de la issue que fallan en el último resultado del QA de la unidad (qa/<U>/resultado.json, de
    appian-qa) y que una persona no ha marcado como no necesarios (`marcas`, como un caso de prueba: --sin-prueba
    HU-nn.m); [] si no hay QA o no falla ninguno."""
    return [c for o, c, e in fallos_qa(raiz, uid, issue) if not marcado(marcas, issue, o, c, e)]


def avisos_qa(raiz, plan):
    """Lo que falta del QA de una unidad con escenarios (F8, paso 8): sin resultado, o con escenarios sin guion,
    desfasados o con el guion por terminar. Son avisos: solo bloquea un escenario que falla (estado())."""
    escenarios = [c for i in plan.issues for c in i.criterios]
    r = pathlib.Path(raiz) / "qa" / plan.uid / "resultado.json"
    if not escenarios:
        return []
    if not r.is_file():
        return [f"{plan.uid} no tiene QA (qa/{plan.uid}/resultado.json): lo siguiente es el QA de la unidad, en otra "
                "sesión y solo con sus .feature (appian-qa; F8, paso 8)"]
    try:
        esc = json.loads(r.read_text(encoding="utf-8-sig")).get("escenarios") or {}
    except (ValueError, AttributeError):
        esc = {}
    de = lambda c: (esc.get(c) or {}).get("resultado") if isinstance(esc.get(c), dict) else None
    faltan = [(que, [c for c in escenarios if de(c) == res]) for que, res in
              (("sin guion", None), ("desfasados", "desfasado"), ("con el guion por terminar", "guion por terminar"))]
    faltan = [f"{que}: {', '.join(cs)}" for que, cs in faltan if cs]
    return [f"el QA de {plan.uid} no está completo ({'; '.join(faltan)}): lo hace QA (appian-qa)"] if faltan else []


def estados(plan, raiz):
    return {i.id: estado(raiz, plan.uid, i, plan.marcas) for i in plan.issues}


def elige(plan, raiz):
    """La próxima issue: la primera sin hacer y sin reservar cuyas dependencias están hechas; None si no hay."""
    e = estados(plan, raiz)
    return next((i for i in plan.issues if not e[i.id][0] and i.id not in plan.reservas
                 and all(e[x][0] for x in i.depende)), None)


def situacion(plan, raiz):
    """Una línea por issue: «ISS-02 · HU-01 · Registrar una solicitud · pendiente: sin verificar · espera a ISS-01»."""
    e, L = estados(plan, raiz), []
    for i in plan.issues:
        falta = [x for x in i.depende if not e[x][0]]
        L.append(f"  {i.id} · {i.para} · {i.titulo} · " + (e[i.id][1] if e[i.id][0] else f"pendiente: {e[i.id][1]}")
                 + (f" · espera a {', '.join(falta)}" if falta and not e[i.id][0] else "")
                 + (f" · reservada: {plan.reservas[i.id]}" if i.id in plan.reservas else ""))
    return L


# ------------------------------------------------------------------ la orden de terminar, para este equipo
def python_de_aqui():
    """La orden de Python de este equipo: python en Windows (python3 suele ser el atajo de la tienda) y python3 en los
    demás; la otra, si esa no está."""
    orden = ["python", "python3"] if os.name == "nt" else ["python3", "python"]
    return next((x for x in orden if shutil.which(x)), orden[0])


def servidor_devmcp(m, entorno="desarrollo"):
    """(nombre del servidor del Dev MCP de un entorno en la configuración de este equipo o None, nota): el que apunta a
    su URL de técnico §0 (la «URL de desarrollo» o, en una urgencia, la del entorno de corrección) o, si §0 no la dice,
    el único que hay. Lo busca donde lo busca «verificar»."""
    try:
        sys.path.append(str(VERIFICAR.parent))
        import devmcp_extract as dx      # el extractor de ingeniería inversa: dónde mira y qué es un Dev MCP
        de = {}
        for _f, nombre, e in dx.server_entries(pathlib.Path.cwd(), []):
            if dx.is_devmcp(e):
                url = dx.expand_vars(dict(e.get("env") or {}), dict(os.environ)).get("LCP_URL", "")
                de.setdefault(nombre, (urlparse(str(url)).hostname or "").lower())
    except Exception:   # noqa: BLE001 - sin el extractor, o con un Python que no lo carga, no se sabe: se dice
        return None, ("no se ha podido leer la configuración del Dev MCP de este equipo: si tiene más de uno, añade "
                      "`--server-name <el de desarrollo>`")
    if not de:
        return None, ("este equipo no tiene ningún Dev MCP configurado desde esta carpeta: sin él, construye una persona "
                      "y la unidad se marca con `--manual`")
    url = url_de(m, entorno)
    if url:
        suyos = [n for n, host in de.items() if host == (urlparse(url).hostname or "").lower()]
        return (suyos[0], "") if suyos else \
            (None, f"ningún Dev MCP de este equipo apunta a la «{URL_DE[entorno]}» ({url}, técnico §0); hay: "
                   f"{', '.join(de)}")
    if len(de) == 1:
        return next(iter(de)), ""
    return None, (f"este equipo tiene varios Dev MCP ({', '.join(de)}) y técnico §0 no dice la «{URL_DE[entorno]}»: "
                  f"añade `--server-name <el de {entorno}>`")


def orden_de_marcar(m, ctx, uid):
    reaplicar = "".join(f" --reaplicada {g}" for g, _ in ctx.reaplicar(uid))
    return (f'{python_de_aqui()} "{(SKILL / "scripts" / "proyecto.py").as_posix()}" cambio '
            f'"{pathlib.Path(m.raiz).resolve().as_posix()}" {uid} construida{reaplicar}')


def orden_de_terminar(m, ctx, plan, issue):
    """(órdenes, notas) para terminar una issue en este equipo, listas para copiar: «verificar», con sus rutas y el Dev
    MCP de desarrollo de su configuración, y, si es la última que queda, marcar la unidad; si la unidad tiene escenarios,
    antes va su QA, en otra sesión, y la orden de marcar va en una nota. Las notas dicen también lo que no se ha podido
    resolver."""
    ruta = lambda p: '"' + pathlib.Path(p).resolve().as_posix() + '"'
    aqui = carpeta(m.raiz, plan.uid)
    servidor, nota = servidor_devmcp(m)
    notas = [nota] if nota else []
    if not VERIFICAR.is_file():
        notas.append("falta la skill appian-reverse-engineering junto a esta: «verificar» es suyo")
    if not plan.app:
        notas.append("técnico §0 no dice la aplicación (fila «Aplicación»): ponla en --app")
    L = ['uv run --no-project --python ">=3.10" --with "mcp>=1.2,<2" python ' + ruta(VERIFICAR) + " verificar --app "
         f'"{plan.app or "<aplicación>"}" --esperado {ruta(aqui / (issue.id + "-esperado.json"))} --out '
         + ruta(aqui / "verificacion" / (issue.id + ".json")) + (f' --server-name "{servidor}"' if servidor else "")]
    e = estados(plan, m.raiz)
    if all(e[i.id][0] for i in plan.issues if i is not issue):
        if any(i.criterios for i in plan.issues):   # lo siguiente es el QA de la unidad, no marcarla (F8, paso 8)
            notas.append("no queda otra issue: lo siguiente es el QA de la unidad, en otra sesión y solo con sus .feature "
                         "(appian-qa; F8, paso 8). Con él, o tras corregir un fallo suyo y repetir sus guiones, se marca "
                         f"la unidad: `{orden_de_marcar(m, ctx, plan.uid)}`")
        else:
            L.append(orden_de_marcar(m, ctx, plan.uid))
    return L, notas


def para_construir(m, ctx, plan, issue):
    """La issue como la recibe quien la construye en este equipo: su texto y, en «Terminar», las órdenes para copiar."""
    ordenes, notas = orden_de_terminar(m, ctx, plan, issue)
    L = [issue.texto.split("\n## Terminar\n", 1)[0].rstrip("\n"), "", "## Terminar", "",
         "Con los objetos construidos, en este equipo y desde esta carpeta"
         + (":" if len(ordenes) == 1 else " (no queda otra issue: la segunda orden marca la unidad):"), "", "```"]
    L += ordenes + ["```"] + [f"· {n}" for n in notas]
    L.append(PRUEBAS_NO if issue.sin_pruebas else PRUEBAS_SI)
    return "\n".join(L)


def orden_de_regresion(m, uid, entorno="desarrollo"):
    """(orden, notas) de la regresión de toda la aplicación en un entorno (el de corrección, en una urgencia corregida
    allí), lista para copiar en este equipo: se pasa antes de preparar el paquete de la unidad y deja su resumen en
    construccion/<U>/regresion.json (por la salida, solo lo que falla)."""
    servidor, nota = servidor_devmcp(m, entorno)
    app = aplicacion(m)
    notas = [nota] if nota else []
    if not app:
        notas.append("técnico §0 no dice la aplicación (fila «Aplicación»): ponla en --app")
    orden = ('uv run --no-project --python ">=3.10" --with "mcp>=1.2,<2" python "' + VERIFICAR.resolve().as_posix()
             + f'" regresion --app "{app or "<aplicación>"}" --out "'
             + (carpeta(m.raiz, uid) / "regresion.json").resolve().as_posix() + '"'
             + (f' --server-name "{servidor}"' if servidor else ""))
    return orden, notas


# ------------------------------------------------------------------ reservar: un commit y un push
class Candado:
    """Una sola sesión de esta carpeta reserva a la vez: un fichero en la carpeta de git, que no se sube. Si otra lo
    tiene, se espera; si lleva demasiado (una sesión que murió), se le quita. Nunca impide seguir."""

    def __init__(self, raiz):
        d = (mo.git(raiz, "rev-parse", "--git-dir") or "").strip()
        self.f, self.mio = (pathlib.Path(raiz) / d / "issues.lock" if d else None), False

    def __enter__(self):
        fin = time.time() + ESPERA_CANDADO
        while self.f:
            try:
                os.close(os.open(str(self.f), os.O_CREAT | os.O_EXCL | os.O_WRONLY))
                self.mio = True
                break
            except FileExistsError:
                try:
                    viejo = time.time() - self.f.stat().st_mtime > CANDADO_VIEJO
                except OSError:
                    viejo = False
                if viejo or time.time() > fin:
                    try:
                        self.f.unlink()
                    except OSError:
                        break
                else:
                    time.sleep(0.2)
            except OSError:
                break
        return self

    def __exit__(self, *_):
        if self.mio:
            try:
                self.f.unlink()
            except OSError:
                pass


def quien_soy(raiz, quien=None):
    """A nombre de quién se reserva: el que se diga o, si no, el usuario de git o el del equipo."""
    nombre = quien or (mo.git(raiz, "config", "user.name") or "").strip() or os.environ.get("USERNAME") \
        or os.environ.get("USER") or "alguien"
    return " ".join(nombre.replace("|", "/").replace("·", "-").split())


def remoto_de(raiz):
    """(remoto, rama del remoto) a donde se sube esta rama: la que sigue o, si no sigue ninguna, la del mismo nombre en
    «origin» (o en el primer remoto); None sin remoto o sin rama."""
    rama = (mo.git(raiz, "symbolic-ref", "--short", "-q", "HEAD") or "").strip()
    sigue = (mo.git(raiz, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}") or "").strip()
    remotos = (mo.git(raiz, "remote") or "").split()
    if not rama or not remotos:
        return None
    if "/" in sigue and sigue.split("/", 1)[0] in remotos:
        return tuple(sigue.split("/", 1))
    return ("origin" if "origin" in remotos else remotos[0]), rama


def al_dia(raiz, remoto):
    """Trae lo del remoto y lo une a esta rama: (bien, por qué no). No falla: lo dice."""
    if mo.git(raiz, "fetch", "--quiet", remoto[0], espera=ESPERA_REMOTO, salida=False) is None:
        return False, "no se pudo consultar el remoto (sin red o sin acceso)"
    ref = f"refs/remotes/{remoto[0]}/{remoto[1]}"
    if mo.git(raiz, "rev-parse", "--verify", "--quiet", ref) is None:
        return True, ""      # la rama aún no está en el remoto: nada que traer
    if mo.git(raiz, "rev-parse", "--verify", "--quiet", "HEAD") is not None \
            and mo.git(raiz, "merge-base", "--is-ancestor", ref, "HEAD") is not None:
        return True, ""
    if mo.git(raiz, "merge", "--quiet", "--no-edit", ref) is None:
        mo.git(raiz, "merge", "--abort")
        return False, "no se pudo traer lo del remoto: lo de este equipo choca con él (git pull)"
    return True, ""


def confirma(raiz, ruta, mensaje):
    """Un commit solo con construccion/<U>/ (lo demás que haya sin confirmar no entra). El commit, o None si no hay nada
    que confirmar o git no puede (sin nombre de usuario, por ejemplo)."""
    mo.git(raiz, "add", "-A", "--", ruta)
    if not (mo.git(raiz, "status", "--porcelain", "--", ruta) or "").strip():
        return None
    if mo.git(raiz, "commit", "--quiet", "-m", mensaje, "--", ruta) is None:
        mo.git(raiz, "reset", "--quiet", "--", ruta)
        return None
    return (mo.git(raiz, "rev-parse", "HEAD") or "").strip() or None


def deshace(raiz, uid, commit):
    """Quita el commit que no se pudo subir, si sigue siendo el último, y deja el índice y las issues como estaban
    confirmados, para que lo del remoto entre sin chocar: se vuelven a generar. Las verificaciones se quedan."""
    ruta = f"{CARPETA}/{uid}"
    if (mo.git(raiz, "rev-parse", "HEAD") or "").strip() != commit:
        return
    if mo.git(raiz, "reset", "--quiet", "--soft", "HEAD~1") is None:
        mo.git(raiz, "update-ref", "-d", "HEAD")      # era el primer commit del repositorio
    mo.git(raiz, "reset", "--quiet", "--", ruta)
    confirmados = set((mo.git(raiz, "ls-files", "--", ruta) or "").split("\n"))
    for f in [carpeta(raiz, uid) / INDICE, *sorted(carpeta(raiz, uid).glob("ISS-*"))]:
        if f"{ruta}/{f.name}" in confirmados:
            mo.git(raiz, "checkout", "--quiet", "HEAD", "--", f"{ruta}/{f.name}")
        elif f.is_file():
            f.unlink()


def a_medias(raiz):
    """La operación de git que el repositorio tiene a medias (una fusión, un rebase…), o "": con una, no se toca git (un
    merge --abort se llevaría la resolución que hubiera a mano)."""
    for ref, que in (("MERGE_HEAD", "una fusión"), ("CHERRY_PICK_HEAD", "un cherry-pick"), ("REVERT_HEAD", "un revert")):
        if mo.git(raiz, "rev-parse", "-q", "--verify", ref) is not None:
            return que
    for d in ("rebase-merge", "rebase-apply"):
        ruta = (mo.git(raiz, "rev-parse", "--git-path", d) or "").strip()
        if ruta and (pathlib.Path(raiz) / ruta).exists():
            return "un rebase"
    return ""


def fuera_de_su_repositorio(raiz):
    """La carpeta del repositorio que contiene el proyecto, si no es la del proyecto (está dentro de otro), o ""."""
    arriba = (mo.git(raiz, "rev-parse", "--show-toplevel") or "").strip()
    try:
        mismo = os.path.normcase(str(pathlib.Path(arriba).resolve())) == os.path.normcase(str(pathlib.Path(raiz).resolve()))
        return arriba if arriba and not mismo else ""
    except OSError:
        return ""


def con_reserva(raiz, uid, cambia, sin_git=None, escribe_=False):
    """Cambia las reservas o las pruebas marcadas del índice de una unidad (cambia(plan) → (issue o None, reservas,
    mensaje del commit); las marcas, en plan.marcas) y lo confirma y lo sube sin pisar a nadie: antes se pone al día; si
    el push falla porque otro subió antes, quita su commit, se pone al día y vuelve a decidir. Devuelve (m, ctx, plan,
    issue, cómo ha quedado). Nunca falla por git: sin repositorio, o dentro de otro que no es el suyo, no reserva (con
    `sin_git`, lo escribe y dice eso); sin remoto no sube y sin acceso lo deja en este equipo, y lo dice. Con una fusión
    o un rebase a medias no toca git ni escribe nada: da la issue sin reservar o, si lo que se pide es escribir
    (`escribe_`: liberar, marcar una prueba), se niega."""
    raiz = pathlib.Path(raiz)
    ruta = f"{CARPETA}/{uid}"

    def decide(reservar=True):
        m = mo.Proyecto(raiz)
        ctx = un.Contexto(m)
        plan = calcula(m, ctx, uid)
        escribe(plan, raiz)
        marcas = list(plan.marcas)
        issue, reservas, mensaje = cambia(plan)
        if reservar and (reservas != plan.reservas or plan.marcas != marcas):
            escribe(plan, raiz, reservas)
        return m, ctx, plan, issue, mensaje

    sin_repo = not shutil.which("git") or mo.git(raiz, "rev-parse", "--is-inside-work-tree") is None
    otro = "" if sin_repo else fuera_de_su_repositorio(raiz)
    if sin_repo or otro:
        por_que = (f"el proyecto está dentro de otro repositorio ({otro}), que no es el suyo: el commit y el push serían "
                   "de ese" if otro else "el proyecto no es un repositorio git (`proyecto.py iniciar` lo crea)")
        if sin_git:
            return (*decide()[:4], f"{sin_git}: {por_que}")
        return (*decide(reservar=False)[:4], f"sin reservar: {por_que}, y otra persona puede llevarse la misma")
    medias = a_medias(raiz)
    if medias:     # no se toca git ni se escribe nada: se dice
        if escribe_:
            raise NoSePuede(f"el repositorio tiene {medias} a medias: termínala (git add y git commit, o git rebase "
                            "--continue) y repite")
        m = mo.Proyecto(raiz)
        ctx = un.Contexto(m)
        plan = calcula(m, ctx, uid)
        return m, ctx, plan, cambia(plan)[0], (f"sin reservar ni escribir nada: el repositorio tiene {medias} a medias; "
                                               "termínala (git add y git commit, o git rebase --continue) y vuelve a pedirla")
    with Candado(raiz):
        remoto = remoto_de(raiz)
        for _ in range(INTENTOS):
            traido, por_que = al_dia(raiz, remoto) if remoto else (True, "")
            m, ctx, plan, issue, mensaje = decide()
            commit = confirma(raiz, ruta, mensaje)
            if commit is None:      # nada que confirmar (no hay issue que dar ni nada que poner al día), o git no puede
                sin_confirmar = bool((mo.git(raiz, "status", "--porcelain", "--", ruta) or "").strip())
                return m, ctx, plan, issue, ("en el índice, sin commit: git no ha podido confirmarlo (¿falta `git config "
                                             "user.name` o `user.email`?)" if sin_confirmar else "")
            if not remoto:
                return m, ctx, plan, issue, ("con un commit, sin subir: el repositorio no tiene remoto (git remote add "
                                             "origin <URL>)")
            if not traido:
                return m, ctx, plan, issue, f"con un commit en este equipo, sin subir: {por_que}"
            if mo.git(raiz, "push", "--quiet", remoto[0], f"HEAD:refs/heads/{remoto[1]}", espera=ESPERA_REMOTO,
                      salida=False) is not None:
                return m, ctx, plan, issue, f"con un commit, subido a {remoto[0]}/{remoto[1]}"
            deshace(raiz, uid, commit)      # otro subió antes: se trae lo suyo y se vuelve a mirar
        m, ctx, plan, issue, mensaje = decide()
        confirma(raiz, ruta, mensaje)
        return m, ctx, plan, issue, (f"con un commit en este equipo, sin subir: {remoto[0]} no admite el push tras "
                                     f"{INTENTOS} intentos (git pull y git push)")


def siguiente(raiz, uid, quien=None):
    """Da la próxima issue de la unidad y la reserva a nombre de `quien` (por defecto, el usuario de git):
    (m, ctx, plan, issue o None, cómo ha quedado la reserva). Con `quien` dicho, si ya tiene una reservada a ese nombre
    que no está hecha (una sesión que se reinicia y vuelve a pedir), da esa: no se lleva otra dejando la suya colgada.
    Sin `quien`, el nombre es el de git, el mismo en todas las sesiones de una persona: dos que piden se llevan dos
    distintas."""
    nombre, suya = quien_soy(raiz, quien), []

    def cambia(plan):
        e = estados(plan, raiz)
        mia = next((i for i in plan.issues if quien and not e[i.id][0]
                    and (plan.reservas.get(i.id) or "").split(" · ")[0].strip() == nombre), None)
        if mia is not None:
            suya[:] = [mia.id]
            return mia, plan.reservas, f"{uid}: {mia.id}, ya reservada por {nombre}"
        issue = elige(plan, raiz)
        if issue is None:
            return None, plan.reservas, f"{uid}: issues al día"
        ahora = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
        return issue, {**plan.reservas, issue.id: f"{nombre} · {ahora}"}, f"{uid}: {issue.id} reservada por {nombre}"
    m, ctx, plan, issue, como = con_reserva(raiz, uid, cambia)
    if issue is not None and suya == [issue.id] and not como:
        como = "ya estaba reservada a tu nombre: es la que tenías"
    return m, ctx, plan, issue, como


def libera(raiz, uid, iid):
    """Quita la reserva de una issue (quien la tenía no va a seguir), con su commit y su push."""
    def cambia(plan):
        if iid not in {i.id for i in plan.issues}:
            raise NoSePuede(f"{uid} no tiene la issue {iid} (tiene {', '.join(i.id for i in plan.issues)})")
        return None, {k: v for k, v in plan.reservas.items() if k != iid}, f"{uid}: {iid} sin reserva"
    return con_reserva(raiz, uid, cambia, escribe_=True)


RX_CASO = re.compile(r"^\s*(.*?)\s*«(.+)»\s*$")      # «DEM_ER_Firma «Sin firma»», como lo dicen estado() y verificar


def sin_prueba(raiz, uid, iid, caso, motivo, quien=None):
    """Una persona marca un caso de prueba que falla en una issue, o uno de sus escenarios que falla en el QA de la unidad
    (HU-nn.m; su objeto es «QA»), como no necesario para avanzar, con su motivo: la issue puede darse por hecha. Va al
    índice de la unidad, con su commit y su push, y se revisa al preparar el paquete. `caso` es «<objeto> «<caso>»» o, si
    no hay dos con ese nombre, solo el caso. Solo uno que falla ahora: en un objeto de la issue y en su verificación de
    ahora, o en el último resultado del QA (qa/<U>/resultado.json)."""
    nombre, ahora = quien_soy(raiz, quien), datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")

    def cambia(plan):
        issue = next((i for i in plan.issues if i.id == iid), None)
        if issue is None:
            raise NoSePuede(f"{uid} no tiene la issue {iid} (tiene {', '.join(i.id for i in plan.issues)})")
        v, por_que = verificacion(raiz, uid, issue)
        if v is None:
            raise NoSePuede(f"{iid}: {por_que}. Se marca un caso que falla en su verificación de ahora")
        fallan = casos(v) + fallos_qa(raiz, uid, issue)
        m = RX_CASO.match(caso)
        objeto, nombre_caso = (m.group(1), m.group(2)) if m else ("", caso.strip())
        elegidos = [(o, c, e) for o, c, e in fallan if c == nombre_caso and (not objeto or o == objeto)]
        if len(elegidos) != 1:
            lista_ = "; ".join(f"{o} «{c}»" for o, c, _ in fallan) or "ninguno"
            raise NoSePuede(f"«{caso}» no es {'un caso' if not elegidos else 'un solo caso'} que falle en {iid} (fallan: "
                            f"{lista_}){': di también el objeto' if len(elegidos) > 1 else ''}")
        o, c, e = elegidos[0]
        plan.marcas = [x for x in plan.marcas if not (x["issue"] == iid and x["objeto"] == o and x["caso"] == c)] + [
            {"issue": iid, "version": issue.version, "objeto": o, "caso": c, "error": error_de(e),
             "motivo": celda(motivo), "quien": nombre, "cuando": ahora}]
        return issue, plan.reservas, f"{uid}: {iid}, {o} «{c}» no necesaria para avanzar ({nombre})"
    return con_reserva(raiz, uid, cambia, sin_git="en el índice, sin commit", escribe_=True)
