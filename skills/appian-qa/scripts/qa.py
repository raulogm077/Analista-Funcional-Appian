#!/usr/bin/env python3
"""El QA de una unidad con SAIL CLI, sin IA: repite los guiones de <p>/qa/<U>/ y deja el resultado en un fichero.

  qa.py repetir  <p> [<U> …] [--escenario HU-01.1 …] [--sesiones <carpeta> …]
                 repite los guiones de cada unidad (sin <U>, los de todas las de qa/) y escribe qa/<U>/resultado.json
  qa.py sesiones <host> <usuario> … [--sesiones <carpeta> …]
                 la carpeta de sesión de SAIL CLI (--data-dir) de cada cuenta en este equipo, o cómo entrar si no la hay

El guion de un escenario, qa/<U>/<escenario>.json, lo escribe QA con lo que recorrió (SKILL.md «El guion»):
  {"escenario": "HU-01.1", "dice": ["Dado …", "Cuando …", "Entonces …"],   las líneas del escenario en su .feature
   "host": "<entorno de desarrollo>", "site": "<site>", "roles": {"<rol>": "<usuario de Appian>"},
   "dado": [paso, …], "cuando": [paso, …], "entonces": [paso, …]}
  paso  {"rol": "<rol>", "sail": ["interact", "Título", "QA {pasada}"], "espera": {…}}   la orden, sin el site
        {"rol": "<rol>", "selecciona": "QA {pasada}"}       marca la fila de la rejilla que lleva ese texto
  Las órdenes son load (siempre --fresh), navigate, interact, back y show; «rol» se puede omitir si hay uno solo.
  espera: "completado": true · "hay" / "no_hay": [ref o etiqueta, o su principio] · "texto" / "sin_texto": [texto]
          · "fila": {"con": "<texto de la fila>", "<columna>": "<valor>", …}
  {pasada} es distinto en cada escenario de cada repetición, para que lo que se teclea y se busca no choque con lo de
  otra vez, y {hoy} es la fecha (AAAA-MM-DD). Un paso falla si SAIL CLI da error, si el servidor no cambia nada o si no
  se cumple lo que espera. Si lo esperado aún no se ve y desde el último load solo se ha mirado (buscar en la rejilla,
  marcar una fila), se vuelve a cargar y a mirar antes de fallar: el proceso puede no haber terminado.
  Un guion que no comprueba nada en «entonces» falla: es el de un recorrido que se quedó a medias.

La sesión de cada cuenta se busca en este equipo por su usuario y su host (el session.json de cada carpeta de SAIL CLI
bajo --sesiones, o bajo $SAIL_HOME y ~/.sail): no hay que decir en ningún fichero dónde está la de cada uno. Este script
no entra ni sale: no ve contraseñas.

El resultado, qa/<U>/resultado.json, es de donde saca issues.py (appian-functional-analyst) que un escenario falla y su
issue vuelve a pendiente:
  {"unidad": "EV-01", "generadoEn": "<UTC>",
   "escenarios": {"HU-01.1": {"resultado": "pasa" | "falla" | "desfasado", "guion": "HU-01.1.json", "issue": "ISS-02",
                              "fecha": "<UTC>", "segundos": 9.1, "paso": "cuando 3", "motivo": "…",
                              "sinRepetir": "<por qué esta vez no se pudo; se queda el resultado anterior>"}},
   "sinGuion": ["HU-02.1"]}
  «desfasado»: el escenario del .feature ya no dice lo que dice el guion (QA lo rehace); no se repite ni cuenta como fallo.

Sale con 0 si todo pasa, 1 si algún escenario falla y 2 si no se pudo repetir algo (sin SAIL CLI, sin sesión, sin
guiones). SAIL_CLI, si existe, es la orden de SAIL CLI que se usa en vez de «sail» (un .py se lanza con este Python).
"""
import argparse
import datetime
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import time
import unicodedata
from urllib.parse import urlparse

CARPETA, RESULTADO = "qa", "resultado.json"
PARTES = ("dado", "cuando", "entonces")
ORDENES = {"load": "load", "navigate": "navigate", "nav": "navigate", "interact": "interact", "back": "back",
           "show": "show"}
ESPERA_SAIL = 120          # segundos que se espera a una orden de SAIL CLI
REINTENTOS, PAUSA = 3, 2   # un load que aún no muestra lo esperado se repite hasta 3 veces más, cada 2 segundos
NIVELES = 3                # hasta dónde se buscan sesiones por debajo de cada carpeta
RX_ID = re.compile(r"^[0-9a-f]{32}$")    # un _cId o una ref de un solo render (refIsPerRender): cambian en cada carga
RX_ESCENARIO = re.compile(r"^\s*(?:Escenario|Ejemplo):\s*(\S+)")
RX_PASO = re.compile(r"^\s*(?:Dad[oa]s?|Cuando|Entonces|Y|E|Pero|\*)\s")
RX_SIN_SESION = re.compile(r"no session found|status 401|authentication failed", re.I)
RX_ISSUE = re.compile(r"ISS-\d+")
# Lo que no se ve en la página: identificadores, iconos y textos que Appian solo enseña a veces (el aviso de una rejilla
# vacía, el de un campo obligatorio, la ayuda emergente, las etiquetas de paginar). Una clave que acaba en «Message» o
# en «Label» (salvo label e inlineLabel) es de esas.
NO_ES_TEXTO = {"#t", "_cId", "id", "testLabel", "icon", "conciseUiPath", "handle", "ref", "tooltip", "accessibilityText",
               "placeholder", "_actionName", "verb", "navKind", "type"}
SE_VE = {"label", "inlineLabel"}
MARCAS = "⤴⌗☐☑⇅├ "


class SinRepetir(Exception):
    """Esta vez no se ha podido repetir (sin sesión, SAIL CLI que no responde): no dice nada de la aplicación."""


class Falla(Exception):
    def __init__(self, motivo, paso=None):
        super().__init__(motivo)
        self.motivo, self.paso = motivo, paso


def ahora():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def escribe(ruta, texto):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", encoding="utf-8", newline="\n") as f:
        f.write(texto)


def lee_json(ruta):
    try:
        return json.loads(ruta.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None


def norma(texto):
    """Para comparar como lo hace SAIL CLI: sin mayúsculas, sin las marcas que pone delante (⤴, ⌗, ☐…) y con los
    espacios de uno en uno."""
    t = unicodedata.normalize("NFC", str(texto)).casefold().lstrip(MARCAS)
    return " ".join(t.split())


# ------------------------------------------------------------------ sesiones: la carpeta de cada cuenta en este equipo
def host_de(texto):
    texto = str(texto or "").strip()
    return ((urlparse(texto).hostname if "://" in texto else texto.split("/")[0]) or "").lower()


def raices(dadas):
    if dadas:
        return [pathlib.Path(d).expanduser() for d in dadas]
    out = [pathlib.Path(os.environ["SAIL_HOME"]).expanduser()] if os.environ.get("SAIL_HOME") else []
    return out + [pathlib.Path.home() / ".sail"]


def sesiones(dadas=None):
    """{(usuario, host): carpeta} de las sesiones de SAIL CLI de este equipo: cada session.json bajo las carpetas, hasta
    NIVELES por debajo. De cada una se usan su usuario y su host; si una cuenta tiene dos, la más reciente."""
    vistas = {}
    for raiz in raices(dadas):
        for n in range(NIVELES + 1):
            for f in raiz.glob("/".join(["*"] * n + ["session.json"])):
                d = lee_json(f)
                if not isinstance(d, dict) or not d.get("username") or not d.get("hostname"):
                    continue
                clave = (str(d["username"]).casefold(), host_de(d["hostname"]))
                if clave not in vistas or f.stat().st_mtime > vistas[clave].stat().st_mtime:
                    vistas[clave] = f
    return {k: f.parent for k, f in vistas.items()}


def como_entrar(usuario, host, carpeta=None):
    donde = f'"{carpeta.as_posix()}"' if carpeta else f"<una carpeta solo para esa cuenta, p. ej. ~/.sail/<entorno>/{usuario}>"
    return (f"con SAIL_USERNAME={usuario} y SAIL_PASSWORD en el entorno, solo para esa orden y nunca en un fichero del "
            f"proyecto: sail login {host} --data-dir {donde}")


# ------------------------------------------------------------------ los escenarios de la unidad, de sus .feature
def escenarios_de(raiz, uid):
    """{escenario: {"dice": [líneas], "issue": "ISS-nn"}} de construccion/<U>/*.feature, en su orden."""
    out = {}
    carpeta = pathlib.Path(raiz) / "construccion" / uid
    orden = lambda f: [int(x) for x in re.findall(r"\d+", f.stem)] or [10 ** 6]
    for f in sorted(carpeta.glob("*.feature"), key=orden):
        actual = None
        for linea in f.read_text(encoding="utf-8").splitlines():
            m = RX_ESCENARIO.match(linea)
            if m:
                actual = out.setdefault(m.group(1), {"dice": [], "issue": (RX_ISSUE.search(f.stem) or [f.stem])[0]})
            elif actual is not None and RX_PASO.match(linea):
                actual["dice"].append(" ".join(linea.split()))
            elif linea.strip() and actual is not None and actual["dice"]:
                actual = None      # se acabó el escenario (una «Regla», otra cosa)
    return out


# ------------------------------------------------------------------ lo que hay en una página (el --json de SAIL CLI)
def textos(nodo):
    """Los textos que se ven en una página: los de sus componentes, sus valores y las filas de sus rejillas; el aviso de
    una rejilla vacía, solo si lo está."""
    if isinstance(nodo, dict):
        if nodo.get("rows") == [] and isinstance(nodo.get("emptyGridMessage"), str):
            yield nodo["emptyGridMessage"]
        for k, v in nodo.items():
            if k not in NO_ES_TEXTO and (k in SE_VE or not k.endswith(("Message", "Label"))):
                yield from textos(v)
    elif isinstance(nodo, list):
        for v in nodo:
            yield from textos(v)
    elif isinstance(nodo, str) and nodo.strip():
        yield nodo


def filas(nodo):
    """Las filas de las rejillas de una página: cada una, {columna: valor, "handle": "☐ …"}."""
    if isinstance(nodo, dict):
        for k, v in nodo.items():
            if k == "rows" and isinstance(v, list) and all(isinstance(x, dict) for x in v):
                yield from v
            else:
                yield from filas(v)
    elif isinstance(nodo, list):
        for v in nodo:
            yield from filas(v)


def con_texto(fila, buscado):
    return any(norma(buscado) in norma(v) for k, v in fila.items() if k != "handle" and isinstance(v, str))


def refs(d):
    return [x for o in d.get("options") or [] if isinstance(o, dict) for x in (o.get("ref"), o.get("label")) if x]


def hay(d, buscada):
    b = norma(buscada)
    return any(norma(r).startswith(b) for r in refs(d))


def lo_que_falta(espera, d):
    """Lo que no se cumple de «espera» en el --json de un paso; [] si todo se cumple."""
    mal = []
    if espera.get("completado") and not d.get("completed"):
        mal.append("el formulario no se ha completado" + (f" (validaciones: {'; '.join(map(str, d['validations']))})"
                                                           if d.get("validations") else ""))
    de_la_pagina = [k for k in ("hay", "no_hay", "texto", "sin_texto", "fila") if espera.get(k)]
    if de_la_pagina and d.get("viewIsStale"):
        return mal + ["la página es la de antes de enviar el formulario: compruébalo tras un «load»"]
    disponibles = sorted({r.lstrip(MARCAS) for r in refs(d)})
    for x in espera.get("hay") or []:
        if not hay(d, x):
            mal.append(f"no está «{x}»; hay: " + (", ".join(f"«{r}»" for r in disponibles[:12]) or "nada"))
    for x in espera.get("no_hay") or []:
        if hay(d, x):
            mal.append(f"está «{x}» y no debería")
    todo = [norma(t) for t in textos({"ui": d.get("ui"), "options": d.get("options"), "v": d.get("validations")})]
    for x in espera.get("texto") or []:
        if not any(norma(x) in t for t in todo):
            mal.append(f"no aparece «{x}»")
    for x in espera.get("sin_texto") or []:
        if any(norma(x) in t for t in todo):
            mal.append(f"aparece «{x}» y no debería")
    fila = espera.get("fila")
    if fila:
        busca = {k: v for k, v in fila.items() if k != "con"}
        suyas = [f for f in filas(d.get("ui")) if con_texto(f, fila.get("con", ""))]
        if not suyas:
            mal.append(f"ninguna fila lleva «{fila.get('con', '')}»")
        elif not any(all(norma(f.get(k, "")) == norma(v) for k, v in busca.items()) for f in suyas):
            f = suyas[0]
            mal.append(f"la fila con «{fila.get('con', '')}» tiene " + ", ".join(
                f"{k} «{f.get(k, '—')}»" for k in busca) + " y se esperaba " + ", ".join(f"{k} «{v}»" for k, v in busca.items()))
    return mal


# ------------------------------------------------------------------ repetir un guion
def sail_cli():
    orden = os.environ.get("SAIL_CLI")
    if orden:
        return [sys.executable, orden] if orden.endswith(".py") else [orden]
    ruta = shutil.which("sail")
    return [ruta] if ruta else None


def sustituye(x, valores):
    if isinstance(x, str):
        for k, v in valores.items():
            x = x.replace("{" + k + "}", v)
        return x
    if isinstance(x, list):
        return [sustituye(v, valores) for v in x]
    if isinstance(x, dict):
        return {k: sustituye(v, valores) for k, v in x.items()}
    return x


def solo_mira(orden):
    """Si una orden solo mira: cargar la página, buscar en una rejilla («🔍») o marcar una de sus filas."""
    sub = ORDENES[orden[0]]
    return sub in ("load", "show") or (sub == "interact" and len(orden) == 3 and orden[1] == "🔍") \
        or (sub == "interact" and len(orden) == 2 and str(orden[1])[:1] in "☐☑")


def defectos(g, nombre):
    """Lo que impide repetir un guion tal como está escrito; [] si se puede."""
    mal = [f"falta «{k}»" for k in ("escenario", "dice", "host", "site", "roles") if not g.get(k)]
    if g.get("escenario") and pathlib.Path(nombre).stem != g["escenario"]:
        mal.append(f"el fichero se llama {nombre} y el escenario es {g['escenario']}")
    roles = g.get("roles") if isinstance(g.get("roles"), dict) else {}
    for parte in PARTES:
        for k, p in enumerate(g.get(parte) or [], 1):
            donde = f"{parte} {k}"
            if not isinstance(p, dict) or ("sail" in p) == ("selecciona" in p):
                mal.append(f"{donde}: un paso lleva «sail» (la orden) o «selecciona» (una fila)")
                continue
            rol = p.get("rol") or (next(iter(roles)) if len(roles) == 1 else None)
            if rol not in roles:
                mal.append(f"{donde}: el rol «{p.get('rol')}» no está en «roles»")
            orden = p.get("sail")
            if orden is not None and (not isinstance(orden, list) or not orden or orden[0] not in ORDENES):
                mal.append(f"{donde}: la orden es una lista que empieza por {', '.join(sorted(set(ORDENES.values())))}")
            elif orden is not None:
                ids = [x for x in orden[1:] if isinstance(x, str) and RX_ID.match(x)]
                if ids:
                    mal.append(f"{donde}: «{ids[0]}» es un _cId o una ref que cambia en cada carga; usa la etiqueta")
    return mal


class Recorrido:
    """Un guion repetido una vez: las sesiones de sus roles, la última página de cada uno y lo que se sustituye."""

    def __init__(self, g, cuentas, valores):
        self.g, self.valores, self.ultima, self.tras_carga = g, valores, {}, {}
        self.host = host_de(g["host"])
        self.carpeta = {}
        for rol, usuario in g["roles"].items():
            c = cuentas.get((str(usuario).casefold(), self.host))
            if c is None:
                raise SinRepetir(f"no hay sesión de {usuario} en {self.host} en este equipo; "
                                 + como_entrar(usuario, self.host))
            self.carpeta[rol] = c

    def rol(self, p):
        return p.get("rol") or next(iter(self.g["roles"]))

    def sail(self, rol, orden):
        base = sail_cli()
        sub, args = ORDENES[orden[0]], [str(x) for x in orden[1:]]
        if sub == "load" and "--fresh" not in args:
            args.append("--fresh")
        cmd = base + ["--json", "--data-dir", str(self.carpeta[rol]), sub, self.g["site"], *args]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                               timeout=ESPERA_SAIL)
        except subprocess.TimeoutExpired:
            raise SinRepetir(f"SAIL CLI no respondió en {ESPERA_SAIL} s ({sub})")
        try:
            d = json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else None
        except ValueError:
            d = None
        if not isinstance(d, dict):     # con --json, un error sale como texto
            error = " ".join((r.stderr.strip() or r.stdout.strip() or f"código {r.returncode}").split())
            if RX_SIN_SESION.search(error):
                usuario = self.g["roles"][rol]
                raise SinRepetir(f"la sesión de {usuario} ({self.carpeta[rol].as_posix()}) ha caducado o no vale; "
                                 + como_entrar(usuario, self.host, self.carpeta[rol]))
            raise Falla(f"SAIL CLI: {error[:600]}")
        if d.get("status") not in (None, "ok"):
            raise Falla(f"SAIL CLI da «{d.get('status')}»" + (f": {'; '.join(map(str, d['validations']))}"
                                                            if d.get("validations") else ""))
        if d.get("movedNothing"):
            raise Falla("el servidor aceptó la orden y no cambió nada")
        return sub, d

    def paso(self, p):
        p = sustituye(p, self.valores)
        rol = self.rol(p)
        if "selecciona" in p:
            pagina = self.ultima.get(rol)
            if pagina is None:
                raise Falla(f"selecciona antes de cargar ninguna página como {rol}")
            suyas = [f for f in filas(pagina.get("ui")) if con_texto(f, p["selecciona"]) and f.get("handle")]
            if not suyas:
                raise Falla(f"ninguna fila lleva «{p['selecciona']}»")
            orden = ["interact", suyas[0]["handle"]]
        else:
            orden = p["sail"]
        espera = p.get("espera") or {}
        _, d = self.sail(rol, orden)
        # lo que ha hecho este rol desde su último load: si solo es mirar (cargar, buscar, marcar una fila), se puede
        # volver a hacer cuando aún no se ve lo esperado, porque el proceso puede no haber terminado
        hechas = [orden] if ORDENES[orden[0]] == "load" else self.tras_carga.get(rol, []) + [orden]
        self.tras_carga[rol], self.ultima[rol] = hechas, d
        mal = lo_que_falta(espera, d)
        intentos = 0
        while mal and intentos < REINTENTOS and ORDENES[hechas[0][0]] == "load" and all(map(solo_mira, hechas)):
            intentos += 1
            time.sleep(PAUSA)
            for o in hechas:
                _, d = self.sail(rol, o)
            self.ultima[rol] = d
            mal = lo_que_falta(espera, d)
        if mal:
            raise Falla("; ".join(mal))
        return bool(espera)

    def repite(self):
        comprueba = False
        for parte in PARTES:
            for k, p in enumerate(self.g.get(parte) or [], 1):
                try:
                    comprobado = self.paso(p)
                except Falla as e:
                    e.paso = f"{parte} {k}"
                    raise
                comprueba = comprueba or (parte == "entonces" and comprobado)
        if not comprueba:
            raise Falla("el guion no llega a comprobar el «entonces»: el recorrido se quedó a medias y QA lo termina",
                        "entonces")


def unica(ultima=[""]):
    """Lo que vale {pasada}: el instante, en milésimas, y distinto del anterior aunque dos lleguen a la vez."""
    t = datetime.datetime.now().strftime("%y%m%d%H%M%S%f")[:-3]
    while t <= ultima[0]:
        t = str(int(t) + 1)
    ultima[0] = t
    return t


def repite_unidad(raiz, uid, solo, cuentas):
    """Repite los guiones de una unidad (con `solo`, nada más que esos escenarios; los demás se quedan como estaban) y
    escribe su resultado. Devuelve (resultado, lo repetido esta vez, líneas para la consola)."""
    carpeta = pathlib.Path(raiz) / CARPETA / uid
    fichero = carpeta / RESULTADO
    previo = lee_json(fichero) or {}
    antes = previo.get("escenarios") if isinstance(previo.get("escenarios"), dict) else {}
    del_feature = escenarios_de(raiz, uid)
    guiones = {f.stem: f for f in sorted(carpeta.glob("*.json")) if f.name != RESULTADO}
    orden = list(del_feature) + sorted(x for x in guiones if x not in del_feature)
    nuevos, repetidos, L = {}, {}, []
    for esc in orden:
        if esc not in guiones:
            continue
        if solo and esc not in solo:
            if esc in antes:
                nuevos[esc] = antes[esc]
            continue
        entrada = {"guion": guiones[esc].name}
        if esc in del_feature:
            entrada["issue"] = del_feature[esc]["issue"]
        g = lee_json(guiones[esc])
        mal = ["no es un JSON"] if not isinstance(g, dict) else defectos(g, guiones[esc].name)
        dice = del_feature.get(esc, {}).get("dice")
        inicio = time.time()
        if mal:
            entrada.update(resultado="falla", motivo="el guion está mal escrito: " + "; ".join(mal))
        elif dice is None:
            entrada.update(resultado="desfasado", motivo=f"{esc} ya no está en los .feature de {uid}")
        elif [" ".join(x.split()) for x in g["dice"]] != dice:
            entrada.update(resultado="desfasado", motivo="el escenario ha cambiado; ahora dice: " + " / ".join(dice))
        else:
            try:
                Recorrido(g, cuentas, {"pasada": unica(), "hoy": datetime.date.today().isoformat()}).repite()
                entrada["resultado"] = "pasa"
            except Falla as e:
                entrada.update(resultado="falla", paso=e.paso, motivo=e.motivo)
            except SinRepetir as e:
                entrada = dict(antes.get(esc) or entrada)
                entrada.setdefault("resultado", "sin repetir")
                entrada["sinRepetir"] = str(e)
        if "sinRepetir" not in entrada:
            entrada.update(fecha=ahora(), segundos=round(time.time() - inicio, 1))
        nuevos[esc] = repetidos[esc] = entrada
    resultado = {"unidad": uid, "generadoEn": ahora(), "escenarios": nuevos,
                 "sinGuion": [e for e in del_feature if e not in guiones]}
    escribe(fichero, json.dumps(resultado, ensure_ascii=False, indent=1) + "\n")
    cuenta = lambda r: sum(1 for e in repetidos.values() if e.get("resultado") == r and not e.get("sinRepetir"))
    sin = sum(1 for e in repetidos.values() if e.get("sinRepetir"))
    L.append(f"{uid} · {len(repetidos)} guiones: {cuenta('pasa')} pasan, {cuenta('falla')} fallan"
             + (f", {cuenta('desfasado')} desfasados" if cuenta("desfasado") else "")
             + (f", {sin} sin repetir" if sin else "") + f" · {fichero.as_posix()}")
    for esc, e in repetidos.items():
        if e.get("sinRepetir"):
            L.append(f"  {esc} · sin repetir esta vez ({e['sinRepetir']}); se queda: {e.get('resultado')}")
        elif e["resultado"] == "pasa":
            L.append(f"  {esc} · pasa ({e.get('segundos', 0):.0f} s)")
        elif e["resultado"] == "falla":
            L.append(f"  {esc} · falla" + (f" en «{e['paso']}»" if e.get("paso") else "") + f": {e.get('motivo')}"
                     + (f" · {e['issue']} vuelve a pendiente" if e.get("issue") else ""))
        else:
            L.append(f"  {esc} · desfasado: {e.get('motivo')}; QA rehace su guion")
    for esc in resultado["sinGuion"] if not solo else []:
        L.append(f"  {esc} · sin guion: lo recorre QA (appian-qa)")
    return resultado, repetidos, L


def repetir(a):
    raiz = pathlib.Path(a.proyecto)
    if not (raiz / CARPETA).is_dir() and not a.unidades:
        print(f"{raiz.as_posix()} no tiene {CARPETA}/: no hay guiones que repetir")
        return 2
    unidades = a.unidades or sorted(d.name for d in (raiz / CARPETA).iterdir() if d.is_dir())
    if sail_cli() is None:
        print("Sin SAIL CLI en este equipo (viene en el paquete del Dev MCP, bin/; bin/setup-* lo deja en el PATH como "
              "«sail»): no se ha repetido nada")
        return 2
    cuentas = sesiones(a.sesiones)
    codigo = 0
    for uid in unidades:
        if not any(f.name != RESULTADO for f in (raiz / CARPETA / uid).glob("*.json")):
            print(f"{uid} · sin guiones en {CARPETA}/{uid}/: su QA está por hacer (appian-qa)")
            codigo = max(codigo, 2)
            continue
        _, repetidos, L = repite_unidad(raiz, uid, set(a.escenario or []), cuentas)
        print("\n".join(L))
        if a.escenario and not repetidos:
            print(f"  {uid} no tiene guion de {', '.join(a.escenario)}")
            codigo = max(codigo, 2)
        if any(e.get("resultado") == "falla" and not e.get("sinRepetir") for e in repetidos.values()):
            codigo = 1
        elif any(e.get("sinRepetir") for e in repetidos.values()) and codigo != 1:
            codigo = 2
    return codigo


def ver_sesiones(a):
    host = host_de(a.host)
    cuentas = sesiones(a.sesiones)
    falta = False
    for u in a.usuarios:
        c = cuentas.get((u.casefold(), host))
        print(f"{u} · {c.as_posix()}" if c else f"{u} · sin sesión en {host}: {como_entrar(u, host)}")
        falta = falta or c is None
    return 2 if falta else 0


def main():
    for st in (sys.stdout, sys.stderr):   # antes de leer los argumentos: la ayuda lleva tildes
        st.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("repetir", help="repite los guiones y escribe qa/<U>/resultado.json")
    r.add_argument("proyecto")
    r.add_argument("unidades", nargs="*", metavar="U")
    r.add_argument("--escenario", action="append", help="solo este escenario (se puede repetir)")
    r.add_argument("--sesiones", action="append", help="carpeta donde buscar las sesiones (por defecto, $SAIL_HOME y ~/.sail)")
    s = sub.add_parser("sesiones", help="la carpeta de sesión de cada cuenta en este equipo")
    s.add_argument("host")
    s.add_argument("usuarios", nargs="+")
    s.add_argument("--sesiones", action="append")
    a = ap.parse_args()
    return repetir(a) if a.cmd == "repetir" else ver_sesiones(a)


if __name__ == "__main__":
    sys.exit(main())
