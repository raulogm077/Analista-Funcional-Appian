#!/usr/bin/env python3
"""Comprueba que las skills del plugin encajan entre sí y que cada una lleva solo lo que usa al trabajar.

    python3 pruebas/comprobar_plugin.py                                 # comprobaciones estáticas (segundos)
    python3 pruebas/comprobar_plugin.py --completo                      # además, las pruebas de cada skill
    python3 pruebas/comprobar_plugin.py --completo --plugin <carpeta>   # lo mismo, sobre otra copia del plugin

Qué mira:
- cada SKILL.md: nombre igual a su carpeta, descripción de 1024 caracteres como mucho y que diga qué no hace;
- que ninguna skill lleve pruebas (tests/, selftest.py), ejemplos (ejemplos/, examples/) ni una carpeta con forma de
  proyecto (proyecto.md, fuentes/, analisis/, as-is/, refactorizacion/ o prototipo/): van en pruebas/<skill>/;
- que ninguna skill lleve la marca de un cliente: un brand-*.json que no sea brand-appian.json (la estándar de Appian)
  o un logo (MARCA_NEUTRA, LOGO e IMAGENES dicen qué es cada cosa); van en <p>/prototipo/ de su proyecto;
- que nada de lo que va al paquete lleve datos personales (PERSONALES; solo el autor y el dueño de .claude-plugin/,
  AUTORIA) ni, salvo el README (CON_HISTORIA), nombre a un cliente de pruebas/clientes.txt o lo que lo delata, ni en
  su contenido ni en el nombre del fichero;
- que ninguna skill use como marca el círculo azul (MARCA_ANTIGUA): la de inferido es 🔶, la misma en todas;
- que las skills que leen lo de ingeniería inversa (LEEN_AS_IS) no citen su extracción en bruto (as-is/extraccion,
  mcp_raw): leen as-is/datos/ y los documentos de as-is/;
- que las skills que se citan existan en el plugin (o estén en EXTERNAS); el README cita además el nombre anterior de
  una skill (ANTERIORES), para retirar sus copias sueltas;
- que existan los ficheros que cita cada SKILL.md y las rutas de una skill a otra;
- que los servidores MCP que se citan estén en .mcp.json;
- que la regla «Dudas de Appian» esté, igual, en las skills de REGLA_DOCS, y el MCP que nombra (appian-docs), en
  .mcp.json;
- que no haya frases largas repetidas entre SKILL.md;
- que la versión de plugin.json sea la última del README.
Con --completo pasa además las pruebas de pruebas/ (cada selftest.py y, con pytest, las de ingeniería inversa) al
plugin que se comprueba, que reciben en PLUGIN_A_PROBAR, la de su requisitos.py y prueba el propio comprobador con una
copia temporal.
Con --plugin <carpeta> todo se hace sobre esa copia del plugin (p. ej. la del paquete, que no lleva pruebas/), con
las pruebas de este repositorio.
Sale con 1 si hay errores.
"""
from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]  # el repositorio: las pruebas de cada skill están en pruebas/<skill>/
PRUEBAS = REPO / "pruebas"
RAIZ = REPO                                 # el plugin que se comprueba: este repositorio u otra copia (--plugin)
SKILLS = RAIZ / "skills"

# Skills que se citan y no están en el plugin, con el motivo.
EXTERNAS = {
    "appian-sail-generator": "skill aparte para escribir código SAIL suelto",
}
# Nombres que empiezan por appian- y no son skills (MCP, carpetas y paquetes de Appian).
NO_SKILLS = {"appian-docs", "appian-dev", "appian-analisis-funcional", "appian-dev-mcp-server",
             "appian-dev-mcp-server-bundle", "appian-mcp-server"}
# Nombre anterior de una skill del plugin → el de hoy. Solo lo cita el README, para retirar las copias sueltas que
# todavía lo llevan; en las skills es un error.
ANTERIORES = {"appian-prototipos-aena": "appian-prototipos"}
# Skills que tienen que llevar la regla de dudas de Appian (appian-best-practices la lleva en *Tools*).
REGLA_DOCS = ["appian-functional-analyst", "appian-prototipos", "appian-refactorizacion", "appian-reverse-engineering"]
# Skills que leen lo de ingeniería inversa: as-is/datos/ y los documentos de as-is/, nunca la extracción en bruto.
LEEN_AS_IS = ("appian-functional-analyst", "appian-refactorizacion")
EXTRACCION = re.compile(r"as-is/extraccion|mcp_raw")
TITULO_REGLA = "## Dudas de Appian"
CARPETAS = ("references", "scripts", "templates", "assets", "schemas", "examples", "galerias", "runtime")
# Lo que no va en una skill: sus pruebas y ejemplos van en pruebas/<skill>/, y un proyecto, en su carpeta <p>.
PRUEBAS_EN_SKILL = ("tests", "ejemplos", "examples")
FORMA_PROYECTO = ("fuentes", "analisis", "as-is", "refactorizacion", "prototipo")  # carpetas que escribe el plugin en <p>
PLANTILLAS = ("plantillas", "templates")  # la plantilla de proyecto.md de una carpeta de plantillas no es un proyecto
CACHES = ("__pycache__", ".pytest_cache")  # restos de ejecutar, que no van en el paquete
# La marca de un cliente va en <p>/prototipo/ de su proyecto, nunca en una skill. La única marca del plugin es la estándar
# de Appian; cualquier otro brand-<id>.json, en cualquier carpeta de una skill, es la marca de un cliente.
MARCA_NEUTRA = "brand-appian.json"
MARCA = re.compile(r"^brand-.+\.json$", re.I)
# Un logo es una imagen (IMAGENES) cuyo nombre EMPIEZA por logo, logotipo, isotipo, imagotipo, símbolo o symbol, seguido de
# «-», «_», «.» o la extensión: logo-x-on-dark.svg, symbol-x.svg, logotipo.png, logo.dark.svg. Se mira el principio del
# nombre, no si lo contiene, porque «catalogo-patrones.json» y «P07-dialogo.json» contienen «logo»; los iconos del kit
# (icons.json) y sus fuentes (fonts/*.woff2) no son imágenes con esos nombres.
LOGO = re.compile(r"^(logo(tipo)?|isotipo|imagotipo|s[ií]mbolo|symbol)([-_.]|$)", re.I)
IMAGENES = (".svg", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico")
NO_VAN_EN_EL_PAQUETE = (".git", ".github", ".claude", "docs", "pruebas", "CLAUDE.md")
# La marca de inferido es 🔶 en todas las skills (la del analista); el círculo azul era la de ingeniería inversa. Se
# mira en los textos que escriben marcas: documentos, plantillas, scripts y datos.
MARCA_ANTIGUA = "\U0001F535"
TEXTOS = (".md", ".py", ".json", ".sh", ".txt", ".html")
# Nada personal en lo que va al paquete: ni el usuario ni las rutas del equipo de nadie. Palabras enteras, sin distinguir
# mayúsculas ni acentos (se compara el texto en NFKD sin marcas y en minúsculas): «Raúl», «RAUL» y «raul» sí; el HYDRAULIC
# de viewer-static.min.js, no. Un usuario con números detrás también cuenta (raulogm077), y el guion bajo separa como un
# espacio (raul_garcia, rgmoya_minsait). Una carpeta personal de Windows, macOS o Linux (C:/Users/x, /Users/x, /home/x)
# también, salvo las neutras: <usuario>, %USERNAME% y Public. Una URL con /users/ no es una ruta del equipo.
PERSONALES = re.compile(r"(?<![a-z0-9])(?:rgmoya|raulogm)\d*(?![a-z0-9])|(?<![a-z0-9])raul(?![a-z0-9])"
                        r"|(?:c:|(?<![\w.:/\\-]))(?:/|\\+)(?:users|home)(?:/|\\+)"
                        r"(?!<usuario>|&lt;usuario&gt;|%username%|public(?![\w.-]))[\w.-]+"
                        r"|(?<!\w)proyectos\s+ia(?!\w)")
PISTAS = ("rgmoya", "raul", "users", "home", "proyectos")  # una línea sin ninguna no hace falta mirarla (rapidez)
# Las únicas excepciones, el autor del plugin y el dueño del marketplace: fichero → objeto cuyo «name» no se mira.
AUTORIA = {".claude-plugin/plugin.json": "author", ".claude-plugin/marketplace.json": "owner"}
# El plugin no lleva clientes (Tarea 0b): ni su nombre ni lo que lo delata en los datos de ejemplo, que dice
# pruebas/clientes.txt. Se mira en todo el paquete y en los nombres de los ficheros, salvo el README, que cuenta su
# historia; el nombre anterior de prototipos (ANTERIORES) no cuenta: hay que poder buscarlo para retirar copias sueltas.
CLIENTES = PRUEBAS / "clientes.txt"
CON_HISTORIA = ("README.md",)

errores, avisos = [], []


def corre(orden, **kw):
    return subprocess.run(orden, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)


def comprobar_contenido(nombres):
    """Una skill solo lleva lo que usa al trabajar: ni pruebas, ni ejemplos, ni un proyecto (tampoco de ejemplo).
    Se mira lo que hay en disco, sin los restos de ejecutar (una carpeta con solo __pycache__ no cuenta)."""
    for n in nombres:
        base = SKILLS / n
        ficheros = {p.relative_to(base) for p in base.rglob("*")
                    if p.is_file() and not set(CACHES) & set(p.relative_to(base).parts)}
        carpetas = {d for f in ficheros for d in f.parents}  # con Path("."), la propia skill
        for d in sorted(carpetas):
            ruta = (Path("skills") / n / d).as_posix()
            if d.name in PRUEBAS_EN_SKILL:
                errores.append(f"{ruta}/: las pruebas y los ejemplos de una skill van en pruebas/{n}/, fuera del paquete")
            forma = (["proyecto.md"] if d / "proyecto.md" in ficheros and d.name not in PLANTILLAS else [])
            forma += [f"{m}/" for m in FORMA_PROYECTO if d / m in carpetas]
            if forma:
                errores.append(f"{ruta}: tiene forma de proyecto ({', '.join(forma)}); ninguna skill lleva un proyecto, "
                               "tampoco de ejemplo")
        for f in sorted(ficheros):
            ruta = (Path("skills") / n / f).as_posix()
            if f.name == "selftest.py":
                errores.append(f"{ruta}: las pruebas de una skill van en pruebas/{n}/")
            if MARCA.match(f.name) and f.name.lower() != MARCA_NEUTRA:
                errores.append(f"{ruta}: la marca de un cliente va en prototipo/ de su proyecto, junto al app.json; la única "
                               f"marca del plugin es assets/{MARCA_NEUTRA}")
            elif f.suffix.lower() in IMAGENES and LOGO.match(f.stem):
                errores.append(f"{ruta}: un logo es de la marca de un cliente y va en prototipo/ de su proyecto, junto a su "
                               "brand-<id>.json; la marca estándar de Appian no lleva logo")
            if f.suffix.lower() in TEXTOS:
                lineas = (base / f).read_text(encoding="utf-8", errors="replace").splitlines()
                azules = [str(i) for i, linea in enumerate(lineas, 1) if MARCA_ANTIGUA in linea]
                if azules:
                    errores.append(f"{ruta}:{','.join(azules[:5])}: usa {MARCA_ANTIGUA} como marca; la de inferido es 🔶, "
                                   "la misma en todas las skills")
                crudas = [str(i) for i, linea in enumerate(lineas, 1) if n in LEEN_AS_IS and EXTRACCION.search(linea)]
                if crudas:
                    errores.append(f"{ruta}:{','.join(crudas[:5])}: cita la extracción en bruto de ingeniería inversa; "
                                   "esta skill lee as-is/datos/ y los documentos de as-is/")
    for py in sorted(SKILLS.glob("*/scripts/*.py")):
        if py.parts[-3] in nombres and (falta := sin_bytecode(py)):
            errores.append(f"{py.relative_to(RAIZ).as_posix()}:{falta}: importa un módulo de su carpeta sin "
                           "«sys.dont_write_bytecode = True» antes: dejaría __pycache__ dentro del plugin, fuera del proyecto")
    for py in [f for f in ficheros_del_paquete() if f.suffix == ".py"]:
        if consola_sin_utf8(py):
            errores.append(f"{py.relative_to(RAIZ).as_posix()}: escribe en la consola sin pasarla a UTF-8: en un Windows "
                           "sin UTF-8 se rompe con «→» o «✓» (sys.stdout.reconfigure(encoding=\"utf-8\", errors=\"replace\"))")
        if lineas := texto_sin_codificacion(py):
            errores.append(f"{py.relative_to(RAIZ).as_posix()}:{','.join(map(str, lineas[:5]))}: lee la salida de otro "
                           "programa como texto sin encoding: en un Windows sin UTF-8 una ruta con tilde sale mal "
                           '(encoding="utf-8", errors="replace")')


def sin_bytecode(py: Path) -> int | None:
    """La línea del primer import de un módulo de la misma carpeta si no va antes «sys.dont_write_bytecode = True»."""
    locales = {p.stem for p in py.parent.glob("*.py")} - {py.stem}
    arbol = ast.parse(py.read_text(encoding="utf-8"))
    lineas = [n.lineno for n in ast.walk(arbol)
              if (isinstance(n, ast.Import) and any(a.name.split(".")[0] in locales for a in n.names))
              or (isinstance(n, ast.ImportFrom) and n.level == 0 and (n.module or "").split(".")[0] in locales)]
    marca = [n.lineno for n in arbol.body if isinstance(n, ast.Assign) and ast.unparse(n).replace(" ", "")
             == "sys.dont_write_bytecode=True"]
    if lineas and not (marca and marca[0] < min(lineas)):
        return min(lineas)
    return None


def texto_sin_codificacion(py: Path) -> list[int]:
    """Las líneas donde se lee la salida de otro programa como texto (text=True o universal_newlines=True) sin decir la
    codificación: se leería en la de la consola, cp1252 en un Windows sin PYTHONUTF8, y una ruta con tilde saldría mal."""
    lineas = []
    for n in ast.walk(ast.parse(py.read_text(encoding="utf-8"))):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in (
                "run", "check_output", "Popen", "call", "check_call"):
            claves = {k.arg: k.value for k in n.keywords if k.arg}
            como_texto = any(isinstance(claves.get(k), ast.Constant) and claves[k].value is True
                             for k in ("text", "universal_newlines"))
            if como_texto and "encoding" not in claves:
                lineas.append(n.lineno)
    return lineas


def consola_sin_utf8(py: Path) -> bool:
    """Si un script que se ejecuta (tiene «__main__») escribe en la consola sin pasarla antes a UTF-8: en un Windows sin
    PYTHONUTF8 la consola va en cp1252 y un «→» o un «✓» lo rompen. Vale reconfigure() o utf8_stdio() de prototipos."""
    texto = py.read_text(encoding="utf-8")
    if "__main__" not in texto or "reconfigure(" in texto or "utf8_stdio" in texto:
        return False
    return any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "print"
               for n in ast.walk(ast.parse(texto)))


def sin_acentos(texto):
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))


def ficheros_del_paquete():
    """Lo que mete en el .plugin la orden zip del README: todo menos NO_VAN_EN_EL_PAQUETE, CACHES y *.plugin."""
    for p in sorted(RAIZ.iterdir()):
        if p.name in NO_VAN_EN_EL_PAQUETE or p.name in CACHES or p.name.endswith(".plugin"):
            continue
        for f in sorted([p] if p.is_file() else p.rglob("*")):
            partes = f.relative_to(RAIZ).parts
            if f.is_file() and not set(CACHES) & set(partes) and not f.name.endswith(".plugin"):
                yield f


def terminos_de_clientes():
    """(término, pista, patrón, sin distinguir mayúsculas) de pruebas/clientes.txt: palabras enteras y sin acentos; los
    códigos de tres letras en mayúsculas, solo en mayúsculas («mad» y «bcn» en minúsculas son palabras corrientes)."""
    terminos = []
    for linea in CLIENTES.read_text(encoding="utf-8").splitlines():
        t = linea.split("#", 1)[0].strip()
        if t:
            codigo = re.fullmatch(r"[A-Z]{3}", t) is not None
            palabras = (sin_acentos(t) if codigo else sin_acentos(t).casefold()).split()
            terminos.append((t, max(palabras, key=len), re.compile(r"(?<!\w)" + r"\s+".join(map(re.escape, palabras)) + r"(?!\w)"),
                             not codigo))
    return terminos


def comprobar_personales_y_clientes():
    """Ningún fichero del paquete lleva datos personales (PERSONALES), salvo los de AUTORIA, y ninguno salvo los de
    CON_HISTORIA nombra a un cliente; tampoco en el nombre del fichero. Los binarios (imágenes, fuentes: llevan bytes nulos) no se leen; los .min.js y los HTML, sí."""
    if not CLIENTES.is_file():
        errores.append(f"falta {CLIENTES.relative_to(REPO).as_posix()}: los clientes que el plugin no puede nombrar")
    clientes = terminos_de_clientes() if CLIENTES.is_file() else []
    donde = lambda lineas: ",".join("nombre" if n == 0 else str(n) for n in lineas[:5]) + ("…" if len(lineas) > 5 else "")
    for f in ficheros_del_paquete():
        datos = f.read_bytes()
        if b"\0" in datos:
            continue
        ruta = f.relative_to(RAIZ).as_posix()
        texto = datos.decode("utf-8", errors="replace")
        if ruta in AUTORIA:  # el «name» de ese objeto se deja en blanco, sin mover las líneas
            texto = re.sub(r'("%s"\s*:\s*\{[^{}]*?"name"\s*:\s*)"(?:[^"\\]|\\.)*"' % AUTORIA[ruta], r'\1""', texto, count=1)
        personales, de_clientes = {}, {}
        # la línea 0 es el nombre del fichero: también cuenta
        for i, linea in enumerate([ruta] + texto.splitlines()):
            plana = linea if linea.isascii() else sin_acentos(linea)
            for anterior in ANTERIORES:
                plana = plana.replace(anterior, " ")
            minus = plana.casefold()
            if any(p in minus for p in PISTAS):
                for m in PERSONALES.finditer(minus):
                    personales.setdefault(m.group(0), []).append(i)
            if ruta not in CON_HISTORIA:
                for t, pista, patron, sin_mayusculas in clientes:
                    donde_mira = minus if sin_mayusculas else plana
                    if pista in donde_mira and patron.search(donde_mira):
                        de_clientes.setdefault(t, []).append(i)
        for dato, lineas in personales.items():
            errores.append(f"{ruta}:{donde(lineas)}: «{dato}» es un dato personal; el paquete no lleva datos de nadie (solo "
                           "author.name de plugin.json y owner.name de marketplace.json): usa uno neutro, como "
                           "C:/Users/<usuario> o una ruta de ejemplo")
        for t, lineas in de_clientes.items():
            errores.append(f"{ruta}:{donde(lineas)}: nombra «{t}», de un cliente ({CLIENTES.relative_to(REPO).as_posix()}); "
                           "el plugin no lleva clientes: usa datos ficticios neutros")


def anota_prueba(nombre, r, ruta, pytest=False):
    """0 bien y 1 error. Un selftest.py sale con otro código (2) si falta un requisito: aviso. Con pytest, todo lo que
    no es 0 es un fallo (2: no se pudieron recoger las pruebas)."""
    print(f"Prueba de {nombre}: {'bien' if r.returncode == 0 else f'falla (código {r.returncode})'}")
    if r.returncode == 1 or (r.returncode and pytest):
        errores.append(f"{ruta} falla:\n" + (r.stdout + r.stderr)[-1500:])
    elif r.returncode:
        avisos.append(f"{ruta} no se pudo completar (falta un requisito)")


def pruebas_de_las_skills():
    """Las pruebas de pruebas/<skill>/ contra el plugin que se comprueba, que reciben en PLUGIN_A_PROBAR."""
    # PYTHONUTF8=1 salvo que se pida otra cosa: la matriz de GitHub prueba un Windows con PYTHONUTF8=0, como el de un
    # compañero, para que las pruebas vean la consola y los ficheros en cp1252
    entorno = dict(os.environ, PLUGIN_A_PROBAR=str(RAIZ), PYTHONUTF8=os.environ.get("PYTHONUTF8", "1"))
    for p in sorted(PRUEBAS.glob("*/selftest.py")):
        anota_prueba(p.parent.name, corre([sys.executable, str(p)], env=entorno), p.relative_to(REPO).as_posix())
    inversa = PRUEBAS / "appian-reverse-engineering"
    if all(importlib.util.find_spec(m) for m in ("pytest", "mcp")):
        orden = [sys.executable, "-m", "pytest", "-q", str(inversa)]
    elif shutil.which("uv"):
        orden = ["uv", "run", "--no-project", "--with", "pytest", "--with", "mcp>=1.2,<2",
                 "python", "-m", "pytest", "-q", str(inversa)]
    else:
        print("Prueba de appian-reverse-engineering: no se pudo completar")
        avisos.append(f"{inversa.relative_to(REPO).as_posix()} no se pudo completar: faltan pytest o mcp y no hay uv "
                      "para traerlos (pip install pytest \"mcp>=1.2,<2\")")
        return
    anota_prueba("appian-reverse-engineering", corre(orden, env=entorno, cwd=str(inversa)),
                 inversa.relative_to(REPO).as_posix(), pytest=True)


def sin_version_ni_rutas(salida):
    """La salida --json de requisitos.py sin lo que cambia de un equipo a otro: la versión de Python y las rutas."""
    datos = json.loads(salida)
    datos["python"] = "<versión>"
    for r in datos.get("requisitos", []):
        if r.get("ruta"):
            r["ruta"] = "<ruta>"
    return datos


def prueba_de_requisitos():
    """requisitos.py del plugin que se comprueba, en una carpeta de trabajo y una carpeta personal temporales (con
    espacios) y con la consola en cp1252, como en Windows: con todo lo opcional ausente, su --json es el de
    pruebas/requisitos-esperado.json salvo versión y rutas; si falta algo opcional sale con 0 y si falta Python, con 1;
    avisa de la copia suelta de una skill del plugin en ~/.claude/skills/, también con el nombre que tenía antes; y
    --breve y el hook de inicio de sesión salen siempre con 0 y avisan una sola vez de lo que falta."""
    fallos = []
    script, tabla = RAIZ / "requisitos.py", RAIZ / "requisitos.json"
    if not (script.is_file() and tabla.is_file()):
        fallos.append("faltan requisitos.py o requisitos.json en la raíz del plugin")
    else:
        opcional = ",".join(r["id"] for r in json.loads(tabla.read_text(encoding="utf-8")) if not r["imprescindible"])
        with tempfile.TemporaryDirectory(prefix="requisitos-") as tmp:
            trabajo = Path(tmp) / "Carpeta con espacios" / "Gestión app"
            trabajo.mkdir(parents=True)

            def requisitos(*args, sin="", casa="vacía", orden=None):
                carpeta = Path(tmp) / "casas" / casa
                carpeta.mkdir(parents=True, exist_ok=True)
                entorno = dict(os.environ, APPIAN_RE_HOME=str(carpeta), REQUISITOS_SIN=sin, PYTHONIOENCODING="cp1252",
                               CLAUDE_PLUGIN_ROOT=str(RAIZ))
                entorno.pop("PYTHONUTF8", None)
                r = corre(orden or [sys.executable, str(script), *args], env=entorno, cwd=str(trabajo))
                return r.returncode, r.stdout, r.stdout + r.stderr

            def espera(cond, que, salida):
                if not cond:
                    fallos.append(f"{que}:\n{salida[-1500:]}")

            c, out, todo = requisitos("--json", sin=opcional)
            esperado = (PRUEBAS / "requisitos-esperado.json").read_text(encoding="utf-8")
            try:
                igual = c == 0 and sin_version_ni_rutas(out) == sin_version_ni_rutas(esperado)
            except ValueError:
                igual = False
            espera(igual, "con REQUISITOS_SIN de todo lo opcional, --json no es pruebas/requisitos-esperado.json (si el "
                   "cambio es a propósito, regenéralo desde una carpeta vacía: APPIAN_RE_HOME=<otra carpeta vacía> "
                   f"REQUISITOS_SIN={opcional} python3 requisitos.py --json > pruebas/requisitos-esperado.json)", todo)
            c, out, todo = requisitos("--json", sin="playwright,docx")
            try:
                ausentes = {r["id"] for r in json.loads(out)["requisitos"] if r["presente"] is False}
            except ValueError:
                ausentes = set()
            espera(c == 0 and {"playwright", "docx"} <= ausentes,
                   "con REQUISITOS_SIN=playwright,docx no sale con 0 o no los da por ausentes", todo)
            c, out, todo = requisitos(sin="python")
            espera(c == 1 and "Python" in out, "con REQUISITOS_SIN=python no sale con 1 diciendo que falta Python", todo)
            for suelta, hoy in (("appian-reverse-engineering", "appian-reverse-engineering"),
                                ("appian-prototipos-aena", "appian-prototipos")):
                copia = Path(tmp) / "casas" / suelta / ".claude" / "skills" / suelta / "SKILL.md"
                copia.parent.mkdir(parents=True)
                copia.write_text(f"---\nname: {suelta}\n---\n", encoding="utf-8")
                c, out, todo = requisitos("--json", casa=suelta)
                try:
                    avisos = " ".join(json.loads(out)["avisos"])
                except ValueError:
                    avisos = ""
                espera(suelta in avisos and hoy in avisos, f"una copia suelta de {suelta} en ~/.claude/skills/ no da aviso",
                       todo)
            # --breve, para el hook de inicio de sesión: sale siempre con 0 (si no, Claude no recibe el texto), dice
            # solo lo que falta y deja la marca de que ya avisó a esta versión
            version = json.loads((RAIZ / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"]
            marca = Path(tmp) / "casas" / "aviso" / ".cache" / "appian-analisis-funcional" / f"avisado-{version}"
            c, out, todo = requisitos("--breve", sin="docx", casa="aviso")
            espera(c == 0 and "Paquete docx de Node" in out and "Falta Python" not in out
                   and "Skill de PDF" not in out and marca.is_file(),
                   "--breve con REQUISITOS_SIN=docx no sale con 0 diciendo solo que falta docx y dejando la marca", todo)
            c, out, todo = requisitos("--breve", sin="docx", casa="aviso")
            espera(c == 0 and not out.strip(), "--breve avisa otra vez de lo mismo", todo)
            c, out, todo = requisitos("--breve", sin="python", casa="sin-python")
            espera(c == 0 and "Falta Python" in out, "--breve con REQUISITOS_SIN=python no sale con 0 diciendo que falta", todo)
            # el hook de hooks/hooks.json tal cual, con la carpeta del plugin en su sitio: python3 y python en la misma
            # orden (sh en macOS y Linux, PowerShell en Windows) y el aviso una sola vez
            try:
                grupos = json.loads((RAIZ / "hooks" / "hooks.json").read_text(encoding="utf-8"))["hooks"]["SessionStart"]
                ordenes = [h["command"] for g in grupos if "startup" in g.get("matcher", "").split("|") for h in g["hooks"]]
            except (OSError, ValueError, KeyError, TypeError):
                ordenes = []
            espera(len(ordenes) == 1, "hooks/hooks.json no tiene un hook SessionStart para «startup»", "")
            for orden in ordenes:
                orden = orden.replace("${CLAUDE_PLUGIN_ROOT}", RAIZ.as_posix())
                shell = (["powershell", "-NoProfile", "-NonInteractive", "-Command", orden] if os.name == "nt"
                         else ["sh", "-c", orden])
                for vez in (1, 2):
                    c, out, todo = requisitos(sin="docx", casa="hook", orden=shell)
                    espera(c == 0 and out.count("Paquete docx de Node") == (1 if vez == 1 else 0),
                           f"el hook de inicio de sesión, la {'primera' if vez == 1 else 'segunda'} vez, no sale con 0 o "
                           f"no avisa de docx {'una vez' if vez == 1 else 'ninguna vez'}", todo)
    print(f"Prueba de requisitos: {'bien' if not fallos else 'falla'}")
    errores.extend(f"Prueba de requisitos: {f}" for f in fallos)


def copia_del_plugin(destino):
    """Copia del plugin con lo que va en el paquete: sin pruebas/, docs/, CLAUDE.md ni restos."""
    destino.mkdir(parents=True)
    for p in sorted(RAIZ.iterdir()):
        if p.name in NO_VAN_EN_EL_PAQUETE or p.name in CACHES or p.name.endswith(".plugin"):
            continue
        if p.is_dir():
            shutil.copytree(p, destino / p.name, ignore=shutil.ignore_patterns(*CACHES, "*.plugin"))
        else:
            shutil.copy2(p, destino / p.name)
    return destino


def probar_comprobador(nombres):
    """Prueba del propio comprobador, con una copia temporal del plugin sin pruebas/ (como la del paquete)."""
    fallos = []
    with tempfile.TemporaryDirectory(prefix="comprobar-plugin-") as tmp:
        copia = copia_del_plugin(Path(tmp) / "Carpeta con espacios" / "plugin")
        skill = copia / "skills" / nombres[0]

        def comprueba(*extra):
            r = corre([sys.executable, str(Path(__file__).resolve()), "--plugin", str(copia), *extra],
                      env=dict(os.environ, PYTHONUTF8="1"))
            return r.returncode, r.stdout + r.stderr

        def espera(cond, que, salida):
            if not cond:
                fallos.append(f"{que}:\n{salida[-1500:]}")

        c, out = comprueba()
        espera(c == 0, "la copia sin pruebas/ no pasa las comprobaciones", out)
        caso = skill / "ejemplos" / "x" / "proyecto.md"
        caso.parent.mkdir(parents=True)
        caso.write_text("# Proyecto de ejemplo\n", encoding="utf-8")
        c, out = comprueba()
        espera(c == 1 and "ejemplos/" in out and "forma de proyecto" in out,
               "una skill con ejemplos/x/proyecto.md no da error", out)
        shutil.rmtree(skill / "ejemplos")
        prueba = skill / "tests" / "test_x.py"
        prueba.parent.mkdir()
        prueba.write_text("def test_x():\n    pass\n", encoding="utf-8")
        c, out = comprueba()
        espera(c == 1 and "tests/" in out, "una skill con tests/ no da error", out)
        shutil.rmtree(skill / "tests")
        # la marca de un cliente (su brand-*.json o su logo) va en <p>/prototipo/ del proyecto, no en una skill
        for nombre in ("brand-cliente.json", "logo-cliente-on-dark.svg", "symbol-cliente.svg"):
            marca = skill / "assets" / nombre
            marca.parent.mkdir(exist_ok=True)
            marca.write_text("{}\n" if nombre.endswith(".json") else "<svg xmlns='http://www.w3.org/2000/svg'/>\n", encoding="utf-8")
            c, out = comprueba()
            espera(c == 1 and nombre in out and "prototipo/" in out, f"una skill con assets/{nombre} no da error", out)
            marca.unlink()
        # la marca de inferido es 🔶 en todas las skills; la de antes, el círculo azul, es un error
        nota = skill / "references" / "marca-antigua.md"
        nota.parent.mkdir(exist_ok=True)
        nota.write_text(f"# Marcas\n\n{MARCA_ANTIGUA} inferido\n", encoding="utf-8")
        c, out = comprueba()
        espera(c == 1 and "marca-antigua.md:3" in out and "🔶" in out,
               "una skill que usa como marca el círculo azul no da error", out)
        nota.unlink()
        # refactorización y el analista leen as-is/datos/ y los documentos de as-is/, nunca la extracción en bruto
        cruda = copia / "skills" / "appian-functional-analyst" / "references" / "zz-extraccion.md"
        for cita in ("as-is/extraccion/inventory.json", "mcp_raw/"):
            cruda.write_text(f"# Datos\n\nLee `{cita}`.\n", encoding="utf-8")
            c, out = comprueba()
            espera(c == 1 and "zz-extraccion.md:3" in out and "as-is/datos/" in out,
                   f"el analista que cita {cita} no da error", out)
        cruda.unlink()
        # el nombre anterior de una skill solo lo cita el README (para retirar las copias sueltas); un SKILL.md, no
        doc = skill / "SKILL.md"
        original = doc.read_text(encoding="utf-8")
        doc.write_text(original + "\nAntes se llamaba `appian-prototipos-aena`.\n", encoding="utf-8")
        c, out = comprueba()
        espera(c == 1 and "appian-prototipos-aena" in out and "hoy appian-prototipos" in out,
               "un SKILL.md que cita el nombre anterior de una skill no da error", out)
        # cada SKILL.md manda comprobar el equipo con su nombre antes de la primera tarea
        doc.write_text(original.replace(f"--skill {nombres[0]}", "--skill otra"), encoding="utf-8")
        c, out = comprueba()
        espera(c == 1 and f"requisitos.py --skill {nombres[0]}" in out,
               "un SKILL.md sin la línea de requisitos.py con su nombre no da error", out)
        doc.write_text(original, encoding="utf-8")
        # la regla «Dudas de Appian» nombra el MCP appian-docs, así que tiene que estar en el .mcp.json del plugin
        mcp = copia / ".mcp.json"
        config = mcp.read_text(encoding="utf-8")
        conf = json.loads(config)
        conf["mcpServers"]["otro-nombre"] = conf["mcpServers"].pop("appian-docs", {})
        mcp.write_text(json.dumps(conf, indent=2), encoding="utf-8")
        c, out = comprueba()
        espera(c == 1 and "appian-docs, que no está en .mcp.json" in out,
               "un .mcp.json sin el servidor appian-docs no da error", out)
        mcp.write_text(config, encoding="utf-8")
        # la orden zip del README deja fuera lo de desarrollo: sin «pruebas/*», el .plugin llevaría las pruebas
        readme = copia / "README.md"
        texto = readme.read_text(encoding="utf-8")
        readme.write_text(texto.replace(' "pruebas/*"', ""), encoding="utf-8")
        c, out = comprueba()
        espera(c == 1 and "la orden zip no deja fuera pruebas/*" in out,
               "una orden zip del README que mete pruebas/ en el paquete no da error", out)
        # la tabla de requisitos del README es la salida de requisitos.py --tabla-readme, sin retoques a mano
        readme.write_text(texto.replace("<!-- requisitos:fin -->", "| a mano | | | | |\n<!-- requisitos:fin -->"),
                          encoding="utf-8")
        c, out = comprueba()
        espera(c == 1 and "la tabla de requisitos no es la salida" in out,
               "una tabla de requisitos del README retocada a mano no da error", out)
        readme.write_text(texto, encoding="utf-8")
        # un script que lee la salida de otro programa como texto sin decir la codificación la lee en la de la consola
        # (cp1252 en Windows): una ruta con tilde sale mal
        scripts = skill / "scripts"
        scripts.mkdir(exist_ok=True)
        lee = scripts / "zz_lee.py"
        lee.write_text("import subprocess\nr = subprocess.run(['npm', 'root', '-g'], capture_output=True, text=True)\n",
                       encoding="utf-8")
        c, out = comprueba()
        espera(c == 1 and "zz_lee.py:2" in out and "encoding" in out,
               "un subprocess.run(text=True) sin encoding no da error", out)
        lee.write_text("import subprocess\nr = subprocess.run(['npm', 'root', '-g'], capture_output=True, text=True,\n"
                       "                   encoding='utf-8', errors='replace')\n", encoding="utf-8")
        c, out = comprueba()
        espera(c == 0, "un subprocess.run(text=True) con encoding da error", out)
        lee.unlink()
        # un script que escribe en la consola sin pasarla a UTF-8 se rompe en un Windows sin UTF-8 con «→» o «✓»
        (scripts / "zz_dice.py").write_text('if __name__ == "__main__":\n    print("hecho \u2192 ✓")\n', encoding="utf-8")
        c, out = comprueba()
        espera(c == 1 and "zz_dice.py" in out and "UTF-8" in out, "un script que imprime sin reconfigure no da error", out)
        (scripts / "zz_dice.py").write_text('import sys\nif __name__ == "__main__":\n    for s in (sys.stdout, sys.stderr):\n'
                                            '        s.reconfigure(encoding="utf-8")\n    print("hecho \u2192 ✓")\n',
                                            encoding="utf-8")
        c, out = comprueba()
        espera(c == 0, "un script que imprime con reconfigure da error", out)
        (scripts / "zz_dice.py").unlink()
        # un script que importa otro de su carpeta deja __pycache__ en el plugin si no lo evita
        (scripts / "zz_modulo.py").write_text("X = 1\n", encoding="utf-8")
        (scripts / "zz_usa.py").write_text("import sys\nimport zz_modulo\n", encoding="utf-8")
        c, out = comprueba()
        espera(c == 1 and "zz_usa.py:2" in out and "dont_write_bytecode" in out,
               "un script que importa un módulo de su carpeta sin dont_write_bytecode no da error", out)
        (scripts / "zz_modulo.py").unlink()
        (scripts / "zz_usa.py").unlink()
        # nada personal en el paquete, con límite de palabra y sin distinguir acentos ni mayúsculas: el HYDRAULIC de
        # viewer-static.min.js (en la copia) no es «Raúl»; C:/Users/<usuario> es la ruta neutra
        personal = skill / "references" / "zz-personal.md"
        for dato in ("C:/Users/rgmoya/Documents", "C:\\Users\\otro\\Documents", "lo revisó RAÚL", "según raul",
                     "/home/claude/proyecto", "D:/Proyectos IA/app", "github.com/raulogm077/x",
                     "/Users/jgarcia/Library/x", "`/home/jgarcia/x`", "usuario raul_garcia", "rgmoya_minsait"):
            personal.write_text(f"# Notas\n\n{dato}\n", encoding="utf-8")
            c, out = comprueba()
            espera(c == 1 and "zz-personal.md:3" in out and "dato personal" in out, f"una skill que dice «{dato}» no da error", out)
        personal.write_text("# Notas\n\nC:/Users/<usuario>/Documents · ELECTRO_HYDRAULIC · C:/Users/%USERNAME%/x · "
                            "C:/Users/Public/x · https://api.example.org/users/12 · /home/<usuario>/x\n", encoding="utf-8")
        c, out = comprueba()
        espera(c == 0 and "viewer-static.min.js" not in out,
               "C:/Users/<usuario>, %USERNAME%, Public, una URL con /users/ o HYDRAULIC dan error", out)
        personal.unlink()
        # el nombre de un fichero también cuenta
        for nombre in ("rgmoya-notas.md", "aena-notas.md"):
            f = skill / "references" / nombre
            f.write_text("# Notas\n\nTexto neutro.\n", encoding="utf-8")
            c, out = comprueba()
            espera(c == 1 and nombre in out, f"un fichero que se llama {nombre} no da error", out)
            f.unlink()
        # la única excepción es author.name de plugin.json (y owner.name de marketplace.json)
        manifiesto = copia / ".claude-plugin" / "plugin.json"
        antes = manifiesto.read_text(encoding="utf-8")
        manifiesto.write_text(antes.replace('"description": "', '"description": "De Raúl: ', 1), encoding="utf-8")
        c, out = comprueba()
        espera(c == 1 and "plugin.json:" in out and "dato personal" in out,
               "un plugin.json que nombra a Raúl fuera de author.name no da error", out)
        manifiesto.write_text(antes, encoding="utf-8")
        # el plugin no lleva clientes (pruebas/clientes.txt): ni su nombre ni lo que lo delata en los datos de ejemplo;
        # los códigos de tres letras, solo en mayúsculas («mad» en minúsculas es una palabra corriente)
        galeria = copia / "skills" / "appian-prototipos" / "galerias" / "zz-galeria.json"
        for dato in ('"ubicacion": "Madrid-Barajas"', '"sede": "MAD"', '"cliente": "Aena"'):
            galeria.write_text("{\n " + dato + "\n}\n", encoding="utf-8")
            c, out = comprueba()
            espera(c == 1 and "zz-galeria.json:2" in out and "clientes.txt" in out, f"una galería que dice {dato} no da error", out)
        galeria.write_text('{\n "ruta": "datos/mad/2026",\n "antes": "appian-prototipos-aena"\n}\n', encoding="utf-8")
        c, out = comprueba()
        espera(c == 0, "un «mad» en minúsculas o el nombre anterior de prototipos dan error como cliente", out)
        galeria.unlink()
        # fuera de skills/ también: lo que va en la raíz del paquete (requisitos.json, hooks/) no nombra clientes
        gancho = copia / "hooks" / "zz-cliente.json"
        gancho.parent.mkdir(exist_ok=True)
        gancho.write_text('{\n "description": "Para el aeropuerto de Barajas"\n}\n', encoding="utf-8")
        c, out = comprueba()
        espera(c == 1 and "zz-cliente.json:2" in out and "clientes.txt" in out, "un fichero de hooks/ que nombra a un cliente no da error", out)
        gancho.unlink()
        # --completo --plugin pasa las pruebas del repositorio a la copia: con sus scripts rotos, ninguna pasa
        # (si falta un requisito, como pytest sin uv, esa prueba no se completa, pero tampoco pasa)
        for py in (copia / "skills").rglob("*.py"):
            py.write_text('raise RuntimeError("roto a propósito por la prueba del comprobador")\n', encoding="utf-8")
        c, out = comprueba("--completo")
        suites = sorted(p.parent.name for p in PRUEBAS.glob("*/selftest.py")) + ["appian-reverse-engineering"]
        espera(c == 1 and all(f"Prueba de {s}:" in out and f"Prueba de {s}: bien" not in out for s in suites),
               "--completo --plugin no pasa las pruebas del repositorio a la copia", out)
    print(f"Prueba del comprobador: {'bien' if not fallos else 'falla'}")
    errores.extend(f"Prueba del comprobador: {f}" for f in fallos)


def frontmatter(texto):
    m = re.match(r"^---\n(.*?)\n---\n", texto, re.S)
    if not m:
        return {}
    campos, actual = {}, None
    for linea in m.group(1).splitlines():
        if re.match(r"^[a-z-]+:", linea):
            actual, _, valor = linea.partition(":")
            campos[actual] = valor.strip()
        elif actual:
            campos[actual] += " " + linea.strip()
    for k, v in campos.items():
        v = v.lstrip(">|").strip()
        if len(v) > 1 and v[0] == v[-1] and v[0] in "\"'":
            v = v[1:-1]
        campos[k] = v
    return campos


def seccion(texto, titulo):
    i = texto.find(titulo + "\n")
    if i < 0:
        return None
    resto = texto[i + len(titulo) + 1:]
    fin = re.search(r"^## ", resto, re.M)
    return resto[: fin.start()] if fin else resto


def sin_urls(texto):
    return re.sub(r"https?://\S+", " ", texto)


def main(completo, plugin=None):
    global RAIZ, SKILLS
    if plugin:
        RAIZ = Path(plugin).resolve()
        SKILLS = RAIZ / "skills"
        if not SKILLS.is_dir():
            print(f"Error · {RAIZ} no es una copia del plugin: no tiene skills/")
            return 1
    nombres = sorted(p.parent.name for p in SKILLS.glob("*/SKILL.md"))
    textos = {n: (SKILLS / n / "SKILL.md").read_text(encoding="utf-8") for n in nombres}
    servidores = set(json.loads((RAIZ / ".mcp.json").read_text(encoding="utf-8")).get("mcpServers", {}))

    for n, t in textos.items():
        fm = frontmatter(t)
        d = fm.get("description", "")
        if fm.get("name") != n:
            errores.append(f"{n}: el name del SKILL.md es «{fm.get('name')}»")
        if not d:
            errores.append(f"{n}: sin descripción")
        elif len(d) > 1024:
            errores.append(f"{n}: la descripción tiene {len(d)} caracteres (máximo 1024)")
        if "<" in d or ">" in d:
            errores.append(f"{n}: la descripción lleva < o >")
        if d and not re.search(r"(^|[.:;] )(No|Not) ", d):
            errores.append(f"{n}: la descripción no dice qué no hace")

    # Lo que lleva cada skill
    comprobar_contenido(nombres)

    # Nada personal ni de un cliente en el paquete
    comprobar_personales_y_clientes()

    # Skills citadas
    documentos = [RAIZ / "README.md"] + [SKILLS / n / "SKILL.md" for n in nombres]
    for n in nombres:
        if n != "appian-best-practices":  # sus referencias citan documentación, no skills
            documentos += sorted((SKILLS / n / "references").glob("*.md"))
    for doc in documentos:
        texto = sin_urls(doc.read_text(encoding="utf-8"))
        for m in re.finditer(r"(?<![\w./-])(appian-[a-z0-9]+(?:-[a-z0-9]+)*)", texto):
            nombre = m.group(1)
            if nombre in ANTERIORES and doc == RAIZ / "README.md":
                continue
            if nombre not in nombres and nombre not in EXTERNAS and nombre not in NO_SKILLS:
                hoy = f" (hoy {ANTERIORES[nombre]})" if nombre in ANTERIORES else ""
                errores.append(f"{doc.relative_to(RAIZ)}: cita «{nombre}», que no está en el plugin{hoy}")

    # Ficheros que cita cada SKILL.md
    for n, t in textos.items():
        codigo = re.findall(r"`([^`\n]+)`", t) + re.findall(r"^```\w*\n(.*?)^```", t, re.S | re.M)
        for palabra in " ".join(codigo).split():
            ruta = re.sub(r"^(<skill>|\$KIT|<KIT>|KIT)/", "", palabra.strip("\"'()[],;:").rstrip("."))
            if not ruta.startswith(CARPETAS) or re.search(r"[*<>{}$|]", ruta):
                continue
            if not (SKILLS / n / ruta).exists():
                errores.append(f"{n}/SKILL.md cita `{ruta}`, que no existe")

    # Cada skill comprueba el equipo antes de su primera tarea (en el chat no hay hook de inicio de sesión)
    for n, t in textos.items():
        if not re.search(rf'requisitos\.py"? --skill {re.escape(n)}(?![\w-])', t):
            errores.append(f"{n}/SKILL.md: falta en «Requisitos» la línea `python3 <skill>/../../requisitos.py --skill {n}`")

    # Rutas de una skill a otra
    for py in SKILLS.glob("*/**/*.py"):
        for m in re.finditer(r'"(appian-[a-z0-9-]+)"((?:\s*/\s*"[^"]+")+)', py.read_text(encoding="utf-8")):
            if m.group(1) in nombres:
                partes = re.findall(r'"([^"]+)"', m.group(2))
                if not SKILLS.joinpath(m.group(1), *partes).exists():
                    errores.append(f"{py.relative_to(RAIZ)}: no existe {m.group(1)}/{'/'.join(partes)}")
    for doc in documentos:
        for m in re.finditer(r"(?<![\w-])(appian-[a-z0-9-]+)/([\w.-]+(?:/[\w.-]+)*)", doc.read_text(encoding="utf-8")):
            if m.group(1) in nombres and not (SKILLS / m.group(1) / m.group(2)).exists():
                errores.append(f"{doc.relative_to(RAIZ)}: no existe {m.group(1)}/{m.group(2)}")

    # MCP
    for doc in documentos:
        for s in set(re.findall(r"mcp__([a-zA-Z0-9-]+)__", doc.read_text(encoding="utf-8"))):
            if s not in servidores:
                errores.append(f"{doc.relative_to(RAIZ)}: cita el MCP «{s}», que no está en .mcp.json")

    # Regla de dudas de Appian: nombra el MCP appian-docs, que tiene que estar en .mcp.json
    if "appian-docs" not in servidores:
        errores.append(f"«{TITULO_REGLA[3:]}» nombra el MCP appian-docs, que no está en .mcp.json")
    reglas = {}
    for n in REGLA_DOCS:
        bloque = seccion(textos.get(n, ""), TITULO_REGLA)
        if bloque is None:
            errores.append(f"{n}: falta el apartado «{TITULO_REGLA[3:]}»")
            continue
        regla = bloque.split("\n\n**")[0].strip()  # lo propio de la skill va después, en párrafos con negrita
        if "appian-docs" not in regla:
            errores.append(f"{n}: «{TITULO_REGLA[3:]}» no nombra el MCP appian-docs")
        reglas[n] = regla
    if len(set(reglas.values())) > 1:
        errores.append("La regla «Dudas de Appian» no es igual en " + ", ".join(reglas))

    # Frases largas repetidas entre SKILL.md
    vistas = {}
    for n, t in textos.items():
        regla = seccion(t, TITULO_REGLA) or ""
        cuerpo = t.replace(regla, "")
        for frase in re.split(r"(?<=[.:;])\s+|\n", re.sub(r"`[^`]*`", "X", cuerpo)):
            palabras = re.findall(r"\w+", frase.lower())
            if len(palabras) >= 14:
                vistas.setdefault(" ".join(palabras), set()).add(n)
    for frase, en in vistas.items():
        if len(en) > 1:
            avisos.append(f"Frase repetida en {', '.join(sorted(en))}: «{frase[:80]}…»")

    # Versión
    version = json.loads((RAIZ / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"]
    filas = re.findall(r"^\| (\d+\.\d+\.\d+[\w.-]*) \|", (RAIZ / "README.md").read_text(encoding="utf-8"), re.M)
    if not filas or filas[0] != version:
        errores.append(f"plugin.json dice {version} y la última versión del README es {filas[0] if filas else 'ninguna'}")

    # La orden zip del README, con la que se hace el .plugin, deja fuera lo que no va en el paquete
    fuera = [n if Path(n).suffix else f"{n}/*" for n in NO_VAN_EN_EL_PAQUETE] + [f"*{c}*" for c in CACHES] + ["*.plugin"]
    ordenes = re.findall(r"`(zip [^`]+)`", (RAIZ / "README.md").read_text(encoding="utf-8"))
    if not ordenes:
        errores.append("README.md: falta la orden zip que hace el .plugin")
    for orden in ordenes:
        falta = [f for f in fuera if f'"{f}"' not in orden]
        if falta:
            errores.append(f"README.md: la orden zip no deja fuera {', '.join(falta)}")

    # La tabla de requisitos del README sale de requisitos.json, para que no diverjan
    tabla = re.search(r"^<!-- requisitos:inicio -->\n(.*?)^<!-- requisitos:fin -->",
                      (RAIZ / "README.md").read_text(encoding="utf-8"), re.S | re.M)
    generada = corre([sys.executable, str(RAIZ / "requisitos.py"), "--tabla-readme"], env=dict(os.environ, PYTHONUTF8="1"))
    if not tabla:
        errores.append("README.md: falta la tabla de requisitos entre <!-- requisitos:inicio --> y <!-- requisitos:fin -->")
    elif generada.returncode or tabla.group(1).strip() != generada.stdout.strip():
        errores.append("README.md: la tabla de requisitos no es la salida de `python3 requisitos.py --tabla-readme`; "
                       "pon esa salida entre <!-- requisitos:inicio --> y <!-- requisitos:fin -->")

    if completo:
        pruebas_de_las_skills()
        prueba_de_requisitos()
        if not plugin:  # el comprobador se prueba una vez, desde el repositorio
            probar_comprobador(nombres)

    for a in avisos:
        print("Aviso ·", a)
    for e in errores:
        print("Error ·", e)
    print(f"{len(nombres)} skills · {len(errores)} errores · {len(avisos)} avisos")
    return 1 if errores else 0


if __name__ == "__main__":
    for s_ in (sys.stdout, sys.stderr):  # consolas de Windows sin UTF-8
        s_.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--completo", action="store_true", help="además, las pruebas de cada skill")
    ap.add_argument("--plugin", help="otra copia del plugin, p. ej. la del paquete (por defecto, este repositorio)")
    args = ap.parse_args()
    sys.exit(main(args.completo, args.plugin))
