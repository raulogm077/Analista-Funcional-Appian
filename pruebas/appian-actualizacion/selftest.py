#!/usr/bin/env python3
"""Prueba automática de appian-actualizacion: actualizar.py con una instalación del Dev MCP, un SAIL CLI y unos
bundles de mentira, sin Appian y en una carpeta personal temporal con espacios y tildes.

  python3 pruebas/appian-actualizacion/selftest.py

Prueba la skill de $PLUGIN_A_PROBAR/skills/appian-actualizacion (por defecto, la de este repositorio): sin instalación
para y dice cómo indicarla; `estado` dice el build, la versión de SAIL CLI y si un bundle es más nuevo, el instalado o
más antiguo; `foto` copia lo instalado con finales de línea de Unix; `informe` compara la foto del build anterior con
lo instalado y da, como datos y como texto, las herramientas nuevas, desaparecidas y cambiadas (un parámetro que
cambia de nombre, uno que pasa a obligatorio, uno a opcional, solo la descripción), los ficheros de la skill oficial,
las órdenes y opciones de SAIL CLI y los ficheros del plugin que citan una herramienta que cambió; una pieza que falta
en una foto sale como «sin foto» y no como «sin cambios»; dos instalaciones no mezclan sus fotos; y no queda
__pycache__ en la skill. Sale con 1 si algo falla.
"""
import io
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tarfile
import tempfile

sys.dont_write_bytecode = True

AQUI = pathlib.Path(__file__).resolve().parent
PLUGIN = pathlib.Path(os.environ.get("PLUGIN_A_PROBAR") or AQUI.parents[1]).resolve()
SKILL = PLUGIN / "skills" / "appian-actualizacion"
SCRIPT = SKILL / "scripts" / "actualizar.py"
fallos = []

# Un sail de mentira: contesta a --version, --help y <orden> --help con lo que diga el fichero de $SAIL_FALSO.
SAIL_FALSO = '''import json, os, sys
d = json.load(open(os.environ["SAIL_FALSO"], encoding="utf-8"))
a = sys.argv[1:]
sys.stdout.reconfigure(encoding="utf-8", newline="\\r\\n")   # como en Windows: la foto lo guarda con \\n
if a == ["--version"]:
    print(d["version"])
elif a == ["--help"]:
    print("sail de mentira\\n\\nAvailable Commands:")
    for o in [*d["ordenes"], "completion", "help"]:
        print(f"  {o:<11} hace {o}")
    print("\\nFlags:\\n      --json   salida para programas")
elif len(a) == 2 and a[1] == "--help" and d["ordenes"].get(a[0]):
    print(d["ordenes"][a[0]])
else:
    sys.exit(1)
'''
AYUDA = "Hace {o}.\n\nFlags:\n{flags}  -h, --help   ayuda de {o}\n"
SAIL = {
    1: {"version": "sail version 1.0.0 (aaa, built 2026-01-01)",
        "ordenes": {"load": AYUDA.format(o="load", flags=""),
                    "interact": AYUDA.format(o="interact", flags="      --confirm   confirma\n      --legacy    viejo\n"),
                    "old": AYUDA.format(o="old", flags=""), "rota": None}},      # la ayuda de «rota» falla
    2: {"version": "sail version 1.1.0 (bbb, built 2026-02-01)",
        "ordenes": {"load": AYUDA.format(o="load", flags=""),
                    "interact": AYUDA.format(o="interact", flags="      --confirm       confirma\n      --no-validate   envía igual\n")
                                + "\nVALIDA LOS ENVÍOS\nUn envío con un obligatorio vacío se rechaza.\n",
                    "tasks": AYUDA.format(o="tasks", flags=""), "rota": None}},
}
h = lambda parametros, obligatorios, descripcion="d1", esquema="e1": {
    "parametros": parametros, "obligatorios": obligatorios, "descripcion": descripcion, "esquema": esquema}
CATALOGO = {
    1: {"oldTool": h({"uuid": "string"}, ["uuid"]),
        "addThings": h({"uuid": "string", "objects": "array"}, ["objects", "uuid"]),
        "createThing": h({"name": "string", "description": ["string", "null"]}, ["name"]),
        "relaxThing": h({"name": "string", "note": "string"}, ["name", "note"]),
        "onlyEnum": h({"kind": "string"}, []),
        "describeOnly": h({"uuid": "string"}, ["uuid"]),
        "sameTool": h({"uuid": "string"}, ["uuid"]),
        "validateDesignObjects": h({"uuids": "array"}, ["uuids"])},
    2: {"listDecisions": h({"query": ["string", "null"]}, []),
        "addThings": h({"uuid": "string", "objectUuids": "array"}, ["objectUuids", "uuid"], esquema="e2"),
        "createThing": h({"name": "string", "description": "string"}, ["description", "name"], esquema="e2"),
        "relaxThing": h({"name": "string", "note": "string"}, ["name"], esquema="e2"),
        "onlyEnum": h({"kind": "string"}, [], esquema="e2"),
        "describeOnly": h({"uuid": "string"}, ["uuid"], descripcion="d2"),
        "sameTool": h({"uuid": "string"}, ["uuid"]),
        "validateDesignObjects": h({"uuids": "array", "level": "string"}, ["uuids"], esquema="e2")},
}
MANIFIESTO = {
    1: "version=v1\n" + "aaa  SKILL.md\nbbb  references/sites.md\nccc  references/old.md\n",
    2: "version=v2\n" + "aa2  SKILL.md\nbbb  references/sites.md\nddd  references/decisions.md\n",
}
BUILD = {1: "20260101-000000", 2: "20260201-000000", 3: "20260301-000000", 4: "20260401-000000"}


def comprueba(nombre, condicion, detalle=""):
    print(("  ok    " if condicion else "  FALLA ") + nombre + (f"\n        {detalle}" if detalle and not condicion else ""))
    if not condicion:
        fallos.append(nombre)


def info(n):
    return f"# de mentira\nbuild_timestamp={BUILD[n]}\nmcp_src_sha=sha{n}\n"


def instala(servidor, n):
    """Deja en la carpeta del servidor lo que dejaría el bundle n."""
    (servidor / "skills" / "appian").mkdir(parents=True, exist_ok=True)
    (servidor / "BUILD-INFO.txt").write_bytes(info(n).encode("utf-8"))
    if n in MANIFIESTO:
        (servidor / "skills" / "appian" / ".bundle-manifest").write_bytes(MANIFIESTO[n].encode("utf-8"))


def bundle(carpeta, n, con_info=True):
    f = carpeta / f"bundle-{n}-{'con' if con_info else 'sin'}.tar.gz"
    with tarfile.open(f, "w:gz") as t:
        datos = info(n).encode("utf-8")
        miembro = tarfile.TarInfo("BUILD-INFO.txt" if con_info else "otro.txt")
        miembro.size = len(datos)
        t.addfile(miembro, io.BytesIO(datos))
    return f


# Lo que trae en bin/ un bundle de mentira: los instaladores apuntan lo que hacen en $APPIAN_RE_HOME/pasos.txt
BAT = '@echo off\r\n>> "%APPIAN_RE_HOME%\\pasos.txt" echo {que} %*\r\n{mas}'
SH = '#!/bin/bash\necho "{que} $*" >> "$APPIAN_RE_HOME/pasos.txt"\n{mas}'
EDITADA_BAT = "if defined SKILLS_EDITADA echo LOCAL EDITS DETECTED - not overwriting.\r\n"
EDITADA_SH = 'if [ -n "${SKILLS_EDITADA:-}" ]; then echo "LOCAL EDITS DETECTED - not overwriting."; fi\n'
FALLA_BAT = 'if exist "%APPIAN_RE_HOME%\\uv-falla" exit /b 3\r\n'
FALLA_SH = 'if [ -e "$APPIAN_RE_HOME/uv-falla" ]; then echo "no se puede"; exit 3; fi\n'


def bundle_entero(carpeta, n, malo="", mas=None, sin=(), su_info=None, enlace=False):
    """Un bundle como los de Appian, con su servidor, su skill, sus instaladores y un SAIL CLI por sistema. Para los
    que no valen: `mas` añade miembros, `sin` los quita, `su_info` cambia el BUILD-INFO y `enlace` mete un enlace."""
    ficheros = {
        "BUILD-INFO.txt": su_info or info(n), "pyproject.toml": "[project]\nname = 'servidor'\n",
        "src/servidor.py": f"# build {n}\n", f"src/solo_del_{n}.py": "", f"raiz_del_{n}/modulo.py": "",
        "skills/appian/.bundle-manifest": MANIFIESTO.get(n, MANIFIESTO[2]),
        "bin/setup-windows.bat": BAT.format(que=f"setup {n}", mas=""),
        "bin/setup-mac.sh": SH.format(que=f"setup {n}", mas=""), "bin/setup-linux.sh": SH.format(que=f"setup {n}", mas=""),
        "bin/install-skills.bat": BAT.format(que=f"skills {n}", mas=EDITADA_BAT),
        "bin/install-skills.sh": SH.format(que=f"skills {n}", mas=EDITADA_SH),
        "bin/sail-windows-amd64.exe": f"sail falso {n}", "bin/sail-darwin-arm64": f"sail falso {n}",
        "bin/sail-linux-amd64": f"sail falso {n}"}
    ficheros = [(k, v) for k, v in ficheros.items() if k not in sin] + list(mas or [])
    f = carpeta / f"entero-{n}{'-' + malo if malo else ''}.tar.gz"
    with tarfile.open(f, "w:gz") as t:
        for nombre, texto in ficheros:
            datos = texto.encode("utf-8")
            miembro = tarfile.TarInfo(nombre)
            miembro.size, miembro.mode = len(datos), 0o755
            t.addfile(miembro, io.BytesIO(datos))
        if enlace:
            miembro = tarfile.TarInfo("src/enlace")
            miembro.type, miembro.linkname = tarfile.SYMTYPE, "servidor.py"
            t.addfile(miembro)
    return f


def uv_falso(carpeta):
    """Un uv de mentira: apunta lo que le piden y falla si existe $APPIAN_RE_HOME/uv-falla."""
    if os.name == "nt":
        f = carpeta / "uv.bat"
        f.write_bytes(BAT.format(que="uv", mas=FALLA_BAT).encode("utf-8"))
    else:
        f = carpeta / "uv"
        f.write_bytes(SH.format(que="uv", mas=FALLA_SH).encode("utf-8"))
        f.chmod(0o755)
    return f


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if not SCRIPT.is_file():
        print(f"error: no está {SCRIPT}")
        sys.exit(1)
    with tempfile.TemporaryDirectory(prefix="actualización de prueba ") as tmp:
        tmp = pathlib.Path(tmp)
        casa, vacia = tmp / "casa", tmp / "casa vacía"
        servidor = casa / "appian-dev-mcp-server"       # donde manda la guía de Appian: se encuentra sin --servidor
        vacia.mkdir()
        instala(servidor, 1)
        sail_py, sail_json = tmp / "sail.py", tmp / "sail.json"
        sail_py.write_text(SAIL_FALSO, encoding="utf-8")
        catalogos = {}
        for n, c in CATALOGO.items():
            catalogos[n] = tmp / f"catálogo {n}.json"
            catalogos[n].write_text(json.dumps(c), encoding="utf-8")

        def sail(n):
            sail_json.write_text(json.dumps(SAIL[n]), encoding="utf-8")

        def lanza(*args, en=casa, con_sail=True, **mas):
            entorno = {**os.environ, "APPIAN_RE_HOME": str(en), "SAIL_FALSO": str(sail_json), "PYTHONIOENCODING": "utf-8",
                       "SAIL_CLI": str(sail_py if con_sail else tmp / "no-hay-sail.py"), **mas}
            r = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, env=entorno,
                               stdin=subprocess.DEVNULL, timeout=120)
            return r.returncode, r.stdout.decode("utf-8", "replace"), r.stderr.decode("utf-8", "replace")

        print("Sin instalación")
        c, out, err = lanza("estado", en=vacia)
        comprueba("para con 2 y dice cómo indicar la carpeta", c == 2 and "--servidor" in err, err)

        print("Estado")
        sail(1)
        c, out, err = lanza("estado")
        comprueba("dice el build, la versión de SAIL CLI y la de la skill oficial",
                  c == 0 and BUILD[1] in out and "sha1" in out and "1.0.0" in out and "versión v1" in out, out + err)
        comprueba("sin fotos todavía", "Fotos guardadas    ninguna" in out, out)
        for n, frase in ((2, "es más nuevo"), (1, "es el instalado")):
            c, out, err = lanza("estado", "--bundle", bundle(tmp, n))
            comprueba(f"un bundle {frase}", c == 0 and frase in out, out + err)
        instala(servidor, 2)
        c, out, err = lanza("estado", "--bundle", bundle(tmp, 1))
        comprueba("un bundle es MÁS ANTIGUO que el instalado", c == 0 and "MÁS ANTIGUO" in out, out + err)
        instala(servidor, 1)
        c, out, err = lanza("estado", "--bundle", bundle(tmp, 1, con_info=False))
        comprueba("un fichero que no es un bundle para con 2", c == 2 and "no es un bundle" in err, err)
        c, out, err = lanza("estado", con_sail=False)
        comprueba("sin SAIL CLI lo dice y sigue", c == 0 and "no está" in out, out + err)

        print("Foto")
        c, out, err = lanza("informe", "--catalogo", catalogos[1])
        comprueba("un informe sin foto de un build anterior para con 2 y dice cuándo se hace",
                  c == 2 and "antes de sustituir" in err, err)
        c, out, err = lanza("foto", "--catalogo", tmp / "no-existe.json")
        comprueba("un catálogo que no se puede leer para con 2", c == 2 and "catálogo" in err, err)
        c, out, err = lanza("foto", "--catalogo", sail_py)
        comprueba("un catálogo que no es JSON para con 2", c == 2 and "catálogo" in err, err)
        incompleto = tmp / "incompleto.json"
        incompleto.write_text('{"unaHerramienta": {}}', encoding="utf-8")
        c, out, err = lanza("foto", "--catalogo", incompleto)
        comprueba("un catálogo sin los campos de cada herramienta para con 2", c == 2 and "no es un catálogo" in err, err)
        incompleto.write_text(json.dumps({"x": dict(h({"a": "string"}, []), obligatorios=[{}])}), encoding="utf-8")
        c, out, err = lanza("foto", "--catalogo", incompleto)
        comprueba("y uno con un obligatorio que no es un nombre, también", c == 2 and "no es un catálogo" in err, err)
        c, out, err = lanza("foto", "--catalogo", catalogos[1])
        fotos = next((casa / ".appian-analisis-funcional" / "actualizaciones").glob("appian-dev-mcp-server-*"))
        foto1 = fotos / BUILD[1]
        comprueba("guarda la foto en la carpeta de su build, por instalación",
                  c == 0 and all((foto1 / f).is_file() for f in ("BUILD-INFO.txt", "skill.bundle-manifest", "devmcp.json",
                                                                 "sail-help/_general.txt", "sail-help/_version.txt",
                                                                 "sail-help/interact.txt", "sail-help/old.txt")), out + err)
        comprueba("sin las órdenes que no son de sail (completion, help)",
                  not any((foto1 / "sail-help" / f"{o}.txt").exists() for o in ("help", "completion")))
        comprueba("una orden cuya ayuda falla sigue en la foto, con una nota en vez de la ayuda",
                  "falló" in (foto1 / "sail-help" / "rota.txt").read_text(encoding="utf-8"))
        comprueba("con finales de línea de Unix aunque sail escriba los de Windows",
                  b"\r" not in (foto1 / "sail-help" / "interact.txt").read_bytes()
                  and b"--legacy" in (foto1 / "sail-help" / "interact.txt").read_bytes())
        c, out, err = lanza("estado")
        comprueba("estado enseña la foto guardada", f"Fotos guardadas    {BUILD[1]}" in out, out)

        print("Informe tras instalar el bundle 2")
        instala(servidor, 2)
        sail(2)
        c, out, err = lanza("informe", "--catalogo", catalogos[2], "--json")
        try:
            inf = json.loads(out)
        except ValueError:
            inf = {}
        d, k, s = inf.get("devmcp") or {}, inf.get("skill") or {}, inf.get("sail") or {}
        cambiadas = d.get("cambiadas", {})
        comprueba("compara la foto del build anterior con lo instalado",
                  c == 0 and inf.get("antes", {}).get("build") == BUILD[1] and inf.get("despues", {}).get("build") == BUILD[2],
                  out[:400] + err)
        comprueba("herramientas nuevas y desaparecidas",
                  d.get("nuevas") == ["listDecisions"] and d.get("desaparecidas") == ["oldTool"]
                  and (d.get("antes"), d.get("despues")) == (8, 8), str(d)[:400])
        comprueba("un parámetro que cambia de nombre: uno nuevo y obligatorio, otro quitado",
                  cambiadas.get("addThings", {}).get("parametros_nuevos") == ["objectUuids"]
                  and cambiadas["addThings"]["parametros_quitados"] == ["objects"]
                  and cambiadas["addThings"]["nuevos_obligatorios"] == ["objectUuids"]
                  and cambiadas["addThings"]["pasan_a_obligatorio"] == [], str(cambiadas.get("addThings")))
        comprueba("un parámetro que pasa a obligatorio y cambia de tipo",
                  cambiadas.get("createThing", {}).get("pasan_a_obligatorio") == ["description"]
                  and cambiadas["createThing"]["cambian_de_tipo"] == ["description"], str(cambiadas.get("createThing")))
        comprueba("un parámetro que pasa a opcional",
                  cambiadas.get("relaxThing", {}).get("pasan_a_opcional") == ["note"], str(cambiadas.get("relaxThing")))
        comprueba("un esquema que cambia sin cambiar parámetros",
                  "onlyEnum" in cambiadas and not any(cambiadas["onlyEnum"].values()), str(cambiadas.get("onlyEnum")))
        comprueba("solo la descripción, aparte; lo que no cambia, en ningún sitio",
                  d.get("solo_descripcion") == ["describeOnly"] and "sameTool" not in json.dumps(inf), str(d)[:300])
        comprueba("ficheros de la skill oficial nuevos, retirados y cambiados",
                  (k.get("nuevos"), k.get("retirados"), k.get("cambiados"))
                  == (["references/decisions.md"], ["references/old.md"], ["SKILL.md"]), str(k))
        rota = s.get("cambiadas", {}).get("rota", {})
        comprueba("la orden cuya ayuda falla en las dos fotos no sale como retirada: se dice que no se pudo comparar",
                  rota.get("sin_ayuda") is True and "rota" not in s.get("retiradas", []) + s.get("nuevas", []), str(s)[:300])
        comprueba("versión, órdenes nuevas y retiradas de SAIL CLI",
                  (s.get("antes"), s.get("despues"), s.get("nuevas"), s.get("retiradas"))
                  == ("1.0.0", "1.1.0", ["tasks"], ["old"]), str(s)[:300])
        interact = s.get("cambiadas", {}).get("interact", {})
        comprueba("opciones nuevas y quitadas de una orden, con las líneas de ayuda que cambian",
                  interact.get("opciones_nuevas") == ["--no-validate"] and interact.get("opciones_quitadas") == ["--legacy"]
                  and any("VALIDA LOS ENVÍOS" in l for l in interact.get("lineas", []))
                  and "load" not in s.get("cambiadas", {}), str(interact))
        citas = inf.get("citas", {})
        comprueba("los ficheros del plugin que citan una herramienta que cambió, y solo esas",
                  any(f.startswith("skills/appian-best-practices/") for f in citas.get("validateDesignObjects", []))
                  and "addThings" not in citas and "listDecisions" not in citas, str(citas)[:300])
        c, out, err = lanza("informe")
        comprueba("el mismo informe, en texto, con la foto que ya hay de ese build (sin volver a dar el catálogo)",
                  c == 0 and all(x in out for x in (
                      f"Foto: {BUILD[1]} · Instalado: {BUILD[2]}", "nuevas: listDecisions", "desaparecidas: oldTool",
                      "cambia addThings: parámetros nuevos: objectUuids; quitados: objects; de los nuevos, obligatorios: objectUuids",
                      "pasan a obligatorios: description", "pasan a opcionales: note",
                      "cambia onlyEnum: el esquema, con los mismos parámetros y obligatorios", "cambia solo la descripción: describeOnly",
                      "nuevos: references/decisions.md", "SAIL CLI   1.0.0 -> 1.1.0", "órdenes nuevas: tasks | retiradas: old",
                      "opciones nuevas: --no-validate; quitadas: --legacy", "validateDesignObjects: skills/")), out + err)

        print("Una pieza que falta en una foto")
        instala(servidor, 3)                             # el bundle 3: sin SAIL CLI y sin catálogo
        c, out, err = lanza("foto", con_sail=False)
        comprueba("la foto dice qué le falta", c == 0 and "sin SAIL CLI, catálogo del Dev MCP" in out, out + err)
        lanza("foto", "--catalogo", catalogos[2])
        c, out, err = lanza("foto", con_sail=False)
        comprueba("rehacer la foto no deja lo que tenía la anterior de ese build",
                  c == 0 and not (fotos / BUILD[3] / "sail-help").exists() and not (fotos / BUILD[3] / "devmcp.json").exists()
                  and (fotos / BUILD[3] / "skill.bundle-manifest").is_file(), out + err)
        c, out, err = lanza("informe", con_sail=False)
        comprueba("el informe la da como «sin foto», no como «sin cambios»",
                  c == 0 and f"Foto: {BUILD[2]} · Instalado: {BUILD[3]}" in out and "DEV MCP    sin foto" in out
                  and "SAIL CLI   sin foto" in out and "SKILL appian   3 -> 3 ficheros" in out, out + err)

        (fotos / BUILD[3] / "BUILD-INFO.txt").unlink()       # como si la foto se hubiera cortado antes de terminar
        (fotos / BUILD[3] / "devmcp.json").write_text(json.dumps(CATALOGO[1]), encoding="utf-8")
        c, out, err = lanza("informe", con_sail=False)
        comprueba("una foto que se quedó a medias no se da por hecha: se rehace entera",
                  c == 0 and (fotos / BUILD[3] / "BUILD-INFO.txt").is_file()
                  and not (fotos / BUILD[3] / "devmcp.json").exists() and "DEV MCP    sin foto" in out, out + err)

        print("Fotos dadas a mano y dos instalaciones")
        c, out, err = lanza("informe", "--antes", foto1, "--despues", fotos / BUILD[2], en=vacia)
        comprueba("con las dos fotos dadas no hace falta la instalación",
                  c == 0 and "nuevas: listDecisions" in out, out + err)
        sin_ayuda = tmp / "foto sin la ayuda de interact"
        shutil.copytree(foto1, sin_ayuda)
        (sin_ayuda / "sail-help" / "interact.txt").write_text("(sail interact --help falló al hacer la foto)", encoding="utf-8")
        c, out, err = lanza("informe", "--antes", foto1, "--despues", sin_ayuda, "--json", en=vacia)
        try:
            suya = json.loads(out)["sail"]["cambiadas"]["interact"]
        except (ValueError, KeyError, TypeError):
            suya = {}
        comprueba("si la ayuda de una orden falló en una de las fotos, no se dan sus opciones por quitadas",
                  c == 0 and suya.get("sin_ayuda") is True and suya.get("opciones_quitadas") == [], out[:300] + err)
        c, out, err = lanza("informe", "--antes", foto1, "--despues", sin_ayuda, en=vacia)
        comprueba("y el informe en texto lo dice",
                  c == 0 and "interact: en alguna de las dos fotos no se pudo leer su ayuda" in out, out + err)
        c, out, err = lanza("informe", "--antes", tmp, "--despues", foto1)
        comprueba("una carpeta que no es una foto para con 2", c == 2 and "no es una foto" in err, err)
        otra = tmp / "otra instalación" / "appian-dev-mcp-server"
        instala(otra, 1)
        c, out, err = lanza("estado", "--servidor", otra)
        comprueba("otra instalación con el mismo nombre de carpeta no ve estas fotos",
                  c == 0 and "Fotos guardadas    ninguna" in out, out + err)

        print("Instalar: lo que para sin tocar nada")
        casa2 = tmp / "otra casa"
        casa2.mkdir()
        srv2, pasos, uv = casa2 / "appian-dev-mcp-server", casa2 / "pasos.txt", uv_falso(tmp)
        enteros = {n: bundle_entero(tmp, n) for n in (1, 2, 3)}
        hechos = lambda: pasos.read_text(encoding="utf-8", errors="replace").split("\n") if pasos.is_file() else []
        instalar = lambda n, *mas, **env: lanza("instalar", enteros[n], "--uv", uv, *mas, en=casa2, **env)
        sail(1)
        c, out, err = lanza("instalar", enteros[1], "--uv", tmp / "no-hay-uv", en=casa2)
        comprueba("sin uv para con 2 y no crea la carpeta del servidor",
                  c == 2 and "uv" in err and not srv2.exists(), err)
        c, out, err = lanza("instalar", bundle(tmp, 1, con_info=False), "--uv", uv, en=casa2)
        comprueba("un fichero que no es un bundle para con 2", c == 2 and not srv2.exists(), err)
        malos = {
            "sin la forma conocida": (bundle(tmp, 1), "no tiene la forma"),
            "con un fichero que se sale de la carpeta": (
                bundle_entero(tmp, 1, "se-sale", mas=[("../fuera.txt", "x")]), "no es una ruta dentro"),
            "con una ruta de Windows que se sale": (
                bundle_entero(tmp, 1, "barras", mas=[("src\\..\\..\\fuera.txt", "x")]), "no es una ruta dentro"),
            "con un enlace": (bundle_entero(tmp, 1, "enlace", enlace=True), "no es un fichero ni una carpeta"),
            "con un fichero repetido": (bundle_entero(tmp, 1, "repetido", mas=[("src/servidor.py", "otro")]), "dos veces"),
            "que trae el entorno de uv": (bundle_entero(tmp, 1, "venv", mas=[(".venv/pyvenv.cfg", "x")]), "trae .venv"),
            "que lo trae con otras mayúsculas": (bundle_entero(tmp, 1, "mayusculas", mas=[(".VENV/pyvenv.cfg", "x")]), "trae .VENV"),
            "que trae la carpeta donde se extrae": (bundle_entero(tmp, 1, "NUEVO", mas=[(".NUEVO/x.txt", "x")]), "trae .NUEVO"),
            "con dos carpetas que solo cambian en las mayúsculas": (
                bundle_entero(tmp, 1, "BIN", mas=[("BIN/otro.txt", "x")]), "solo se distinguen en las mayúsculas"),
            "con un nombre que Windows no admite": (
                bundle_entero(tmp, 1, "punto", mas=[("src/acaba en punto.", "x")]), "valga en todos los sistemas"),
            "con un nombre de dispositivo de Windows": (
                bundle_entero(tmp, 1, "nul", mas=[("src/NUL.txt", "x")]), "valga en todos los sistemas"),
            "sin el instalador de este sistema": (
                bundle_entero(tmp, 1, "sin-setup", sin=("bin/setup-windows.bat", "bin/setup-mac.sh", "bin/setup-linux.sh")),
                "le falta bin/setup-"),
            "con un build que no es una fecha": (
                bundle_entero(tmp, 1, "build", su_info="build_timestamp=../../fuera\nmcp_src_sha=sha1\n"), "AAAAMMDD-HHMMSS"),
        }
        for que, (malo, dice) in malos.items():
            c, out, err = lanza("instalar", malo, "--uv", uv, en=casa2)
            comprueba(f"un bundle {que} para con 2 y no escribe nada",
                      c == 2 and dice in err and not srv2.exists() and not (casa2 / "fuera.txt").exists()
                      and not (tmp / "fuera.txt").exists(), err)
        ajena = tmp / "carpeta ajena"
        ajena.mkdir()
        (ajena / "algo.txt").write_text("mío", encoding="utf-8")
        c, out, err = lanza("instalar", enteros[1], "--uv", uv, "--servidor", ajena, en=casa2)
        comprueba("una carpeta con ficheros que no es una instalación para con 2 y queda como estaba",
                  c == 2 and "no es una instalación" in err and [p.name for p in ajena.iterdir()] == ["algo.txt"], err)

        print("Instalar: una instalación nueva")
        cliente = tmp / "cliente de IA"
        c, out, err = instalar(1, "--skills-dir", cliente)
        comprueba("extrae el bundle en la carpeta de la guía de Appian",
                  c == 0 and (srv2 / "src" / "servidor.py").read_text(encoding="utf-8") == "# build 1\n"
                  and "sha1" in (srv2 / "BUILD-INFO.txt").read_text(encoding="utf-8"), out + err)
        # cmd pasa con comillas lo que lleva espacios y escribe las tildes de la ruta en la codificación de la consola
        dados = [h.replace('"', "").strip() for h in hechos() if h.strip()]
        comprueba("lanza uv sync, el instalador de SAIL CLI y el de la skill, también en la carpeta que se le da",
                  dados[:3] == ["uv sync", "setup 1", "skills 1"] and len(dados) == 4
                  and dados[3].startswith("skills 1 --skills-dir ") and dados[3].endswith(cliente.name), str(hechos()))
        suyo = casa2 / ".appian-analisis-funcional"
        comprueba("sin nada anterior, ni foto ni copia; apunta lo que trajo el bundle y dice que hay que reiniciar",
                  not list(suyo.rglob("BUILD-INFO.txt")) and not list(suyo.rglob("bundle.tar.gz"))
                  and len(list(suyo.rglob("instalado.json"))) == 1 and "Reinicia tus clientes" in out, out)

        print("Instalar: una actualización")
        (srv2 / ".venv").mkdir()
        (srv2 / ".venv" / "paquete.txt").write_text("instalado por uv", encoding="utf-8")
        (srv2 / "uv.lock").write_text("candado", encoding="utf-8")
        (srv2 / "notas mías.txt").write_text("no son del bundle", encoding="utf-8")
        (srv2 / "src" / "__pycache__").mkdir()
        (srv2 / "src" / "__pycache__" / "servidor.pyc").write_bytes(b"\0")
        c, out, err = instalar(3, "--plugin-sha", "sha2")
        comprueba("un bundle que no es el del plugin del entorno para con 2 y no toca nada",
                  c == 2 and "No se ha tocado la instalación" in err
                  and "sha1" in (srv2 / "BUILD-INFO.txt").read_text(encoding="utf-8"),
                  err)
        c, out, err = instalar(2, "--plugin-sha", "sha2", "--catalogo", catalogos[1])
        fotos2 = next((casa2 / ".appian-analisis-funcional" / "actualizaciones").glob("appian-dev-mcp-server-*"), tmp)
        foto, copia = fotos2 / BUILD[1], fotos2 / BUILD[1] / "bundle.tar.gz"
        comprueba("antes de instalar hace la foto de lo que había",
                  c == 0 and all((foto / f).is_file() for f in ("BUILD-INFO.txt", "skill.bundle-manifest", "devmcp.json",
                                                                "sail-help/interact.txt")), out + err)
        nombres = set()
        if copia.is_file():
            with tarfile.open(copia) as t:
                nombres = set(t.getnames())
        comprueba("y guarda el bundle anterior, sin el entorno de uv ni restos de ejecutar",
                  {"BUILD-INFO.txt", "src/solo_del_1.py", "bin/sail-linux-amd64", "notas mías.txt"} <= nombres
                  and not any(n.startswith((".venv", ".nuevo", ".instalando")) or "__pycache__" in n for n in nombres),
                  str(sorted(nombres)))
        comprueba("sustituye lo que trae el bundle: lo del anterior que ya no viene, desaparece, también en la raíz",
                  (srv2 / "src" / "servidor.py").read_text(encoding="utf-8") == "# build 2\n"
                  and (srv2 / "src" / "solo_del_2.py").is_file() and not (srv2 / "src" / "solo_del_1.py").exists()
                  and (srv2 / "raiz_del_2").is_dir() and not (srv2 / "raiz_del_1").exists()
                  and "raiz_del_1/modulo.py" in nombres
                  and "sha2" in (srv2 / "BUILD-INFO.txt").read_text(encoding="utf-8"))
        comprueba("y deja lo demás de la carpeta: el entorno de uv y los ficheros que no son del bundle",
                  (srv2 / ".venv" / "paquete.txt").is_file() and (srv2 / "uv.lock").is_file()
                  and (srv2 / "notas mías.txt").is_file() and not (srv2 / ".nuevo").exists()
                  and not (srv2 / ".instalando").exists())
        comprueba("dice qué había antes y dónde queda",
                  "antes había el build " + BUILD[1] in out and str(foto.resolve()) in out, out)
        dentro = srv2 / "descargas"
        dentro.mkdir()
        shutil.copyfile(enteros[3], dentro / "bundle.tar.gz")
        c, out, err = lanza("instalar", dentro / "bundle.tar.gz", "--uv", uv, en=casa2)
        comprueba("un bundle guardado dentro de la carpeta del servidor para con 2 y no toca nada",
                  c == 2 and "dentro de la del servidor" in err
                  and "sha2" in (srv2 / "BUILD-INFO.txt").read_text(encoding="utf-8"), err)
        shutil.rmtree(dentro)
        gemelo = bundle_entero(tmp, 2, "gemelo", su_info=f"build_timestamp={BUILD[2]}\nmcp_src_sha=otro\n")
        c, out, err = lanza("instalar", gemelo, "--uv", uv, en=casa2)
        comprueba("un bundle con la misma fecha de build y otro sha para con 2 y no toca nada",
                  c == 2 and "misma fecha de build" in err and "sha2" in (srv2 / "BUILD-INFO.txt").read_text(encoding="utf-8"),
                  err)
        c, out, err = lanza("estado", "--bundle", gemelo, en=casa2)
        comprueba("y estado no lo da por el instalado ni por más nuevo", c == 0 and "misma fecha de build" in out, out + err)
        c, out, err = instalar(1)
        comprueba("un bundle más antiguo que lo instalado para con 2 y no toca nada",
                  c == 2 and "más antiguo" in err and "sha2" in (srv2 / "BUILD-INFO.txt").read_text(encoding="utf-8"), err)

        print("Instalar: un paso falla y se repite")
        (casa2 / "uv-falla").write_text("", encoding="utf-8")
        c, out, err = instalar(3)
        comprueba("si uv sync falla sale con 1, dice cuál y que se puede repetir, y no sigue con los demás pasos",
                  c == 1 and "uv sync: FALLA" in out and "se puede repetir" in err and "setup 3" not in "".join(hechos()),
                  out + err)
        (casa2 / "uv-falla").unlink()
        c, out, err = instalar(3)
        comprueba("la misma orden, repetida, hace los pasos que faltaban y no hace otra foto ni otra copia",
                  c == 0 and "era el build instalado" in out and not (fotos2 / BUILD[3]).exists()
                  and "setup 3" in "".join(hechos()), out + err)
        comprueba("se guarda un solo bundle anterior: el del último build",
                  [p.parent.name for p in sorted(fotos2.glob("*/bundle.tar.gz"))] == [BUILD[2]],
                  str(sorted(fotos2.glob("*/bundle.tar.gz"))))
        c, out, err = instalar(3, SKILLS_EDITADA="1")
        comprueba("si la skill oficial instalada tiene cambios de la persona, lo dice y no falla",
                  c == 0 and "skill appian: REVISAR" in out and "LOCAL EDITS" in out, out + err)

        print("Después de instalar")
        sail(2)                                          # el SAIL CLI que dejó el bundle 3
        c, out, err = lanza("informe", en=casa2)
        comprueba("el informe compara con la foto que hizo la instalación",
                  c == 0 and f"Foto: {BUILD[2]} · Instalado: {BUILD[3]}" in out and "SAIL CLI   1.0.0 -> 1.1.0" in out, out + err)
        c, out, err = lanza("sail-anterior", en=casa2)
        anterior = fotos2 / BUILD[2] / ("sail.exe" if os.name == "nt" else "sail")
        comprueba("sail-anterior saca el SAIL CLI de este sistema del bundle guardado y dice cómo usarlo",
                  c == 0 and anterior.is_file() and anterior.read_bytes() == b"sail falso 2" and "SAIL_CLI" in out
                  and str(anterior.resolve()) in out, out + err)
        c, out, err = lanza("sail-anterior")
        comprueba("sin bundle anterior guardado para con 2 y dice cuándo se guarda", c == 2 and "instalar" in err, err)

        print("Una sustitución que se quedó a medias")
        guardada = fotos2 / BUILD[2] / "bundle.tar.gz"
        antes = (guardada.stat().st_size, guardada.stat().st_mtime_ns)
        # como si se hubiera cortado al borrar
        (srv2 / ".instalando").write_text(json.dumps({"build": f"{BUILD[3]} sha3", "sobran": ["resto del anterior"]}),
                                          encoding="utf-8")
        (srv2 / "resto del anterior").mkdir()
        (srv2 / "BUILD-INFO.txt").unlink()
        (srv2 / "src" / "servidor.py").unlink()
        c, out, err = lanza("estado", en=casa2)
        comprueba("las demás órdenes paran con 2 y dicen que se repita instalar", c == 2 and "a medias" in err, err)
        c, out, err = lanza("instalar", bundle_entero(tmp, 4), "--uv", uv, en=casa2)
        comprueba("instalar con otro bundle para con 2: se termina con el mismo con el que se cortó",
                  c == 2 and "termínala con aquel" in err and (srv2 / ".instalando").is_file()
                  and not (srv2 / "raiz_del_4").exists(), err)
        c, out, err = instalar(3)
        comprueba("instalar la termina, sin tomar por «anterior» el servidor a medio borrar",
                  c == 0 and "a medias" in out and not (srv2 / ".instalando").exists()
                  and not (srv2 / "resto del anterior").exists()
                  and (srv2 / "src" / "servidor.py").read_text(encoding="utf-8") == "# build 3\n"
                  and (guardada.stat().st_size, guardada.stat().st_mtime_ns) == antes
                  and [p.parent.name for p in fotos2.glob("*/bundle.tar.gz")] == [BUILD[2]], out + err)
        with tarfile.open(guardada) as t:
            comprueba("y la marca no entra en el bundle guardado", ".instalando" not in t.getnames())

        print("Una carpeta de la raíz que cambia de mayúsculas")
        casa3 = tmp / "tercera casa"
        casa3.mkdir()
        srv3 = casa3 / "appian-dev-mcp-server"
        c, out, err = lanza("instalar", bundle_entero(tmp, 1, "Docs", mas=[("Docs/antes.txt", "")]), "--uv", uv, en=casa3)
        c2, out2, err2 = lanza("instalar", bundle_entero(tmp, 2, "docs", mas=[("docs/ahora.txt", "")]), "--uv", uv, en=casa3)
        comprueba("lo que trae el bundle nuevo no se quita por llamarse casi como lo que traía el anterior",
                  c == 0 and c2 == 0 and (srv3 / "docs" / "ahora.txt").is_file() and not (srv3 / "raiz_del_1").exists(),
                  out + err + out2 + err2)

        print("El catálogo que deja el extractor de ingeniería inversa")
        del_extractor = tmp / "mcp_catalog.json"
        del_extractor.write_text(json.dumps({"toolCount": 1, "tools": [
            {"name": "addThings", "description": "Añade cosas.", "allowed": False,
             "inputSchema": {"type": "object", "required": ["uuid"], "properties": {
                 "uuid": {"type": "string"}, "tags": {"anyOf": [{"type": "array"}, {"type": "null"}]}}}}]}), encoding="utf-8")
        c, out, err = lanza("foto", "--catalogo", del_extractor, en=casa3)
        guardado = next((casa3 / ".appian-analisis-funcional").rglob("devmcp.json"), None)
        suyo = json.loads(guardado.read_text(encoding="utf-8")).get("addThings", {}) if guardado else {}
        comprueba("la foto lo admite tal cual y lo resume: parámetros con su tipo, obligatorios y dos huellas",
                  c == 0 and suyo.get("parametros") == {"uuid": "string", "tags": ["array", "null"]}
                  and suyo.get("obligatorios") == ["uuid"] and len(suyo.get("descripcion", "")) == 12
                  and len(suyo.get("esquema", "")) == 12, out + err + str(suyo))
        del_extractor.write_text(json.dumps({"tools": [{"name": "sinEsquema"}]}), encoding="utf-8")
        c, out, err = lanza("foto", "--catalogo", del_extractor, en=casa3)
        comprueba("uno al que le falta el esquema de una herramienta para con 2", c == 2 and "no es un catálogo" in err, err)
        una = {"name": "addThings", "description": "x", "inputSchema": {"properties": {"uuid": {"type": "string"}}}}
        for que, herramientas, dice in (
                ("con una herramienta repetida", [una, una], "dos veces"),
                ("con unos obligatorios que no son una lista", [dict(una, inputSchema={"required": 1})], "con su forma"),
                ("con unos parámetros que no son un objeto", [dict(una, inputSchema={"properties": [1]})], "con su forma")):
            del_extractor.write_text(json.dumps({"tools": herramientas}), encoding="utf-8")
            c, out, err = lanza("foto", "--catalogo", del_extractor, en=casa3)
            comprueba(f"uno {que} para con 2 y dice por qué", c == 2 and dice in err and "Traceback" not in err, err)

        print("Comprobar la extracción de la aplicación del banco")
        minimos = json.loads((SKILL / "assets" / "banco" / "esperado.json").read_text(encoding="utf-8"))["objetos"]
        error = lambda herramienta, tipo: {"tool": herramienta, "objectType": tipo, "error": "API error (HTTP 404)"}

        def extraccion(nombre, **cambios):
            informe = {"status": "complete", "objectListComplete": True, "app": {"name": "BPS Banco de pruebas SAIL"},
                       "objectsByType": dict(minimos), "objectCount": sum(minimos.values()),
                       "errors": [error("listObjectVersions", "folder"), error("listObjectVersions", "group")]}
            informe.update(cambios)
            informe["errorCount"] = len(informe["errors"])
            (tmp / nombre / "extraccion").mkdir(parents=True)
            (tmp / nombre / "extraccion" / "extraction_report.json").write_text(json.dumps(informe), encoding="utf-8")
            return tmp / nombre

        c, out, err = lanza("comprobar", "--extraccion", extraccion("extracción buena"), en=vacia)
        comprueba("con los objetos esperados y errores sueltos, pasa; dice qué errores quedan y lo que aún no comprueba",
                  c == 0 and "Pasa: están los objetos de cada tipo" in out and "listObjectVersions (2 tipos)" in out
                  and "Sin comprobar: los recorridos con SAIL CLI" in out, out + err)
        c, out, err = lanza("comprobar", "--extraccion", extraccion(
            "sin procesos", objectsByType={**minimos, "processModel": 0}), en=vacia)
        comprueba("si el extractor deja de ver un tipo de objeto, falla y dice cuál",
                  c == 1 and f"processModel: 0 de {minimos['processModel']}" in out, out + err)
        c, out, err = lanza("comprobar", "--extraccion", extraccion("genérica", errors=[
            error("getTaskReport", t) for t in ("constant", "folder", "interface")]), en=vacia)
        comprueba("una herramienta con errores en tres tipos de objeto falla: se está probando en todos",
                  c == 1 and "getTaskReport" in out and "devmcp_policy.json" in out, out + err)
        c, out, err = lanza("comprobar", "--extraccion", extraccion("cortada", status="partial"), en=vacia)
        comprueba("una extracción que no terminó no es un fallo: no se pudo comprobar",
                  c == 2 and "No se pudo comprobar" in err and "partial" in err, out + err)
        c, out, err = lanza("comprobar", "--extraccion", tmp / "no hay extracción", en=vacia)
        comprueba("sin informe de extracción, tampoco, y dice cómo se hace", c == 2 and "devmcp_extract.py" in err, err)
        c, out, err = lanza("comprobar", "--extraccion", extraccion(
            "mal formado", objectsByType={**minimos, "site": "uno"}), en=vacia)
        comprueba("un informe mal formado no cuenta como fallo del extractor: no se pudo comprobar",
                  c == 2 and "no es el informe de una extracción" in err and "Traceback" not in err, out + err)

    comprueba("no queda __pycache__ en la skill", not list(SKILL.rglob("__pycache__")))
    print(f"\n{'TODO BIEN' if not fallos else f'{len(fallos)} FALLOS'}")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
