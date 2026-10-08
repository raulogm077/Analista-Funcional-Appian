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
- que las skills que se citan existan en el plugin (o estén en EXTERNAS); el README cita además el nombre anterior de
  una skill (ANTERIORES), para retirar sus copias sueltas;
- que existan los ficheros que cita cada SKILL.md y las rutas de una skill a otra;
- que los servidores MCP que se citan estén en .mcp.json;
- que la regla «Dudas de Appian» esté, igual, en las skills de REGLA_DOCS, y el MCP que nombra (appian-docs), en
  .mcp.json;
- que no haya frases largas repetidas entre SKILL.md;
- que la versión de plugin.json sea la última del README.
Con --completo pasa además las pruebas de pruebas/ (cada selftest.py y, con pytest, las de ingeniería inversa) al
plugin que se comprueba, que reciben en PLUGIN_A_PROBAR, y prueba el propio comprobador con una copia temporal.
Con --plugin <carpeta> todo se hace sobre esa copia del plugin (p. ej. la del paquete, que no lleva pruebas/), con
las pruebas de este repositorio.
Sale con 1 si hay errores.
"""
import argparse
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]  # el repositorio: las pruebas de cada skill están en pruebas/<skill>/
PRUEBAS = REPO / "pruebas"
RAIZ = REPO                                 # el plugin que se comprueba: este repositorio u otra copia (--plugin)
SKILLS = RAIZ / "skills"

# Skills que se citan y no están en el plugin, con el motivo.
EXTERNAS = {
    "appian-sail-generator": "skill aparte para escribir código SAIL suelto",
    "appian-refactorizacion": "se crea en F5",
}
# Nombres que empiezan por appian- y no son skills (MCP, carpetas y paquetes de Appian).
NO_SKILLS = {"appian-docs", "appian-dev", "appian-analisis-funcional", "appian-dev-mcp-server",
             "appian-dev-mcp-server-bundle", "appian-mcp-server"}
# Nombre anterior de una skill del plugin → el de hoy. Solo lo cita el README, para retirar las copias sueltas que
# todavía lo llevan; en las skills es un error.
ANTERIORES = {"appian-prototipos-aena": "appian-prototipos"}
# Skills que tienen que llevar la regla de dudas de Appian (appian-best-practices la lleva en *Tools*).
REGLA_DOCS = ["appian-functional-analyst", "appian-prototipos", "appian-reverse-engineering"]
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
    entorno = dict(os.environ, PLUGIN_A_PROBAR=str(RAIZ), PYTHONUTF8="1")
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
        # el nombre anterior de una skill solo lo cita el README (para retirar las copias sueltas); un SKILL.md, no
        doc = skill / "SKILL.md"
        original = doc.read_text(encoding="utf-8")
        doc.write_text(original + "\nAntes se llamaba `appian-prototipos-aena`.\n", encoding="utf-8")
        c, out = comprueba()
        espera(c == 1 and "appian-prototipos-aena" in out and "hoy appian-prototipos" in out,
               "un SKILL.md que cita el nombre anterior de una skill no da error", out)
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

    if completo:
        pruebas_de_las_skills()
        if not plugin:  # el comprobador se prueba una vez, desde el repositorio
            probar_comprobador(nombres)

    for a in avisos:
        print("Aviso ·", a)
    for e in errores:
        print("Error ·", e)
    print(f"{len(nombres)} skills · {len(errores)} errores · {len(avisos)} avisos")
    return 1 if errores else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--completo", action="store_true", help="además, las pruebas de cada skill")
    ap.add_argument("--plugin", help="otra copia del plugin, p. ej. la del paquete (por defecto, este repositorio)")
    args = ap.parse_args()
    sys.exit(main(args.completo, args.plugin))
