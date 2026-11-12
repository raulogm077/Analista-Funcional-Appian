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
import hashlib
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
HOST_BANCO = "dev.ejemplo.test"
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
EDITADA_BAT = ("if defined SKILLS_EDITADA echo LOCAL EDITS DETECTED - not overwriting.\r\n"
               "if defined SKILLS_ENLACE echo     Skipped - la carpeta de skills is a symlink/junction.\r\n"
               'if defined SKILLS_SIN_CLIENTES if "%~1"=="" echo No AI client detected.& exit /b 1\r\n')
EDITADA_SH = ('if [ -n "${SKILLS_EDITADA:-}" ]; then echo "LOCAL EDITS DETECTED - not overwriting."; fi\n'
              'if [ -n "${SKILLS_ENLACE:-}" ]; then echo "    Skipped — la carpeta de skills is a symlink (-> /y)."; fi\n'
              'if [ -n "${SKILLS_SIN_CLIENTES:-}" ] && [ $# -eq 0 ]; then echo "No AI client detected (looked for ~/.kiro)."; '
              'exit 1; fi\n')
AVISA_BAT = ("if defined SETUP_AVISA echo [!] could not update your PATH. Add this directory manually:\r\n"
             "if defined SETUP_FALLA echo error: this machine is not one the bundle ships a binary for& exit /b 1\r\n")
AVISA_SH = ('if [ -n "${SETUP_AVISA:-}" ]; then echo "Linked, but /opt/x is not on your PATH. Either add it:"; fi\n'
            'if [ -n "${SETUP_FALLA:-}" ]; then echo "error: this machine is not one the bundle ships a binary for" >&2; '
            'exit 1; fi\n')
FALLA_BAT = 'if exist "%APPIAN_RE_HOME%\\uv-falla" exit /b 3\r\n'
FALLA_SH = 'if [ -e "$APPIAN_RE_HOME/uv-falla" ]; then echo "no se puede"; exit 3; fi\n'


def bundle_entero(carpeta, n, malo="", mas=None, sin=(), su_info=None, enlace=False, punto=False):
    """Un bundle como los de Appian, con su servidor, su skill, sus instaladores y un SAIL CLI por sistema. Para los
    que no valen: `mas` añade miembros, `sin` los quita, `su_info` cambia el BUILD-INFO y `enlace` mete un enlace."""
    ficheros = {
        "BUILD-INFO.txt": su_info or info(n), "pyproject.toml": "[project]\nname = 'servidor'\n",
        "src/servidor.py": f"# build {n}\n", f"src/solo_del_{n}.py": "", f"raiz_del_{n}/modulo.py": "",
        "skills/appian/.bundle-manifest": MANIFIESTO.get(n, MANIFIESTO[2]),
        "bin/setup-windows.bat": BAT.format(que=f"setup {n}", mas=AVISA_BAT),
        "bin/setup-mac.sh": SH.format(que=f"setup {n}", mas=AVISA_SH),
        "bin/setup-linux.sh": SH.format(que=f"setup {n}", mas=AVISA_SH),
        "bin/install-skills.bat": BAT.format(que=f"skills {n}", mas=EDITADA_BAT),
        "bin/install-skills.sh": SH.format(que=f"skills {n}", mas=EDITADA_SH),
        "bin/sail-windows-amd64.exe": f"sail falso {n}", "bin/sail-darwin-arm64": f"sail falso {n}",
        "bin/sail-linux-amd64": f"sail falso {n}"}
    ficheros = [(k, v) for k, v in ficheros.items() if k not in sin] + list(mas or [])
    f = carpeta / f"entero-{n}{'-' + malo if malo else ''}.tar.gz"
    with tarfile.open(f, "w:gz") as t:
        if punto:                                   # como lo deja `tar -C carpeta .`: la propia raíz, como entrada
            raiz = tarfile.TarInfo(".")
            raiz.type, raiz.mode = tarfile.DIRTYPE, 0o755
            t.addfile(raiz)
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


def enlaza(enlace, destino):
    """Un enlace a una carpeta; dice si se pudo. En Windows, una unión de carpetas: no pide permisos, como sí los pide
    un enlace simbólico."""
    if os.name == "nt":
        return subprocess.run(["cmd", "/c", "mklink", "/J", str(enlace), str(destino)], capture_output=True).returncode == 0
    os.symlink(destino, enlace, target_is_directory=True)
    return True


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

        def lanza(*args, en=casa, con_sail=True, desde=None, script=SCRIPT, **mas):
            entorno = {**os.environ, "APPIAN_RE_HOME": str(en), "SAIL_FALSO": str(sail_json), "PYTHONIOENCODING": "utf-8",
                       "SAIL_CLI": str(sail_py if con_sail else tmp / "no-hay-sail.py"), **mas}
            r = subprocess.run([sys.executable, str(script), *map(str, args)], capture_output=True, env=entorno,
                               stdin=subprocess.DEVNULL, timeout=120, cwd=desde)
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
            "con un build escrito con otros dígitos": (
                bundle_entero(tmp, 1, "digitos", su_info="build_timestamp=２０２６０１０１-００００００\nmcp_src_sha=sha1\n"),
                "AAAAMMDD-HHMMSS"),
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
        comprueba("y dice lo que queda en una instalación nueva: los clientes y el navegador, con la guía de Appian",
                  "es una instalación nueva" in out and "docs.appian.com" in out, out)

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
        comprueba("dice qué había antes y dónde queda, y no lo de una instalación nueva",
                  "antes había el build " + BUILD[1] in out and str(foto.resolve()) in out
                  and "instalación nueva" not in out, out)
        dentro = srv2 / "descargas"
        dentro.mkdir()
        shutil.copyfile(enteros[3], dentro / "bundle.tar.gz")
        c, out, err = lanza("instalar", dentro / "bundle.tar.gz", "--uv", uv, en=casa2)
        comprueba("un bundle guardado dentro de la carpeta del servidor para con 2 y no toca nada",
                  c == 2 and "dentro de la carpeta del servidor" in err
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
        comprueba("si uv sync falla sale con 1, dice cuál y que se puede repetir, y hace los demás pasos, que no dependen de él",
                  c == 1 and "uv sync: FALLA" in out and "«uv sync»" in err and "se puede repetir" in err
                  and "SAIL CLI: bien" in out and "skill appian: bien" in out and "Reinicia" not in out, out + err)
        (casa2 / "uv-falla").unlink()
        lanzados = lambda: [h.split()[0] for h in hechos() if h.strip()]   # uv, setup o skills, por orden
        antes = len(lanzados())
        c, out, err = instalar(3)
        comprueba("la misma orden, repetida, vuelve a hacer los pasos y no hace otra foto ni otra copia",
                  c == 0 and "era el build instalado" in out and not (fotos2 / BUILD[3]).exists()
                  and lanzados()[antes:] == ["uv", "setup", "skills"], out + err + str(lanzados()[antes:]))
        antes = len(lanzados())
        c, out, err = instalar(3, SETUP_FALLA="1")
        comprueba("si el instalador de SAIL CLI se niega (un equipo sin binario en el bundle), la skill oficial se instala igual",
                  c == 1 and "SAIL CLI: FALLA" in out and "not one the bundle ships" in out and "skill appian: bien" in out
                  and "«SAIL CLI»" in err and "«skill appian»" not in err
                  and lanzados()[antes:] == ["uv", "setup", "skills"], out + err + str(lanzados()[antes:]))
        comprueba("se guarda un solo bundle anterior: el del último build",
                  [p.parent.name for p in sorted(fotos2.glob("*/bundle.tar.gz"))] == [BUILD[2]],
                  str(sorted(fotos2.glob("*/bundle.tar.gz"))))
        c, out, err = instalar(3, SKILLS_EDITADA="1")
        comprueba("si la skill oficial instalada tiene cambios de la persona, lo dice y no falla",
                  c == 0 and "skill appian: REVISAR" in out and "LOCAL EDITS" in out and "SAIL CLI: bien" in out, out + err)
        c, out, err = instalar(3, SKILLS_ENLACE="1")
        comprueba("si el instalador se salta un cliente porque su carpeta de skills es un enlace, no se da por instalada",
                  c == 0 and "skill appian: REVISAR" in out and "Skipped" in out and "SAIL CLI: bien" in out, out + err)
        c, out, err = instalar(3, SKILLS_SIN_CLIENTES="1")
        comprueba("sin ningún cliente de los que detecta Appian y sin --skills-dir, falla y enseña lo que dice su instalador",
                  c == 1 and "skill appian: FALLA" in out and "No AI client detected" in out and "«skill appian»" in err,
                  out + err)
        antes = len(lanzados())
        c, out, err = instalar(3, "--skills-dir", "cliente relativo", SKILLS_SIN_CLIENTES="1", desde=tmp)
        dados = [h.replace('"', "").strip() for h in hechos() if h.strip()][antes:]
        comprueba("con --skills-dir no es un fallo: la skill va al cliente que se da, y repetir no cambiaría nada",
                  c == 0 and "Appian no detecta ninguno de sus clientes" in out and "FALLA" not in out
                  and f"skill appian en {(tmp / 'cliente relativo').resolve()}: bien" in out, out + err)
        comprueba("y una carpeta relativa se entiende desde donde está quien lanza la orden, no desde la del servidor",
                  len(dados) == 4 and os.path.isabs(dados[3].split(" --skills-dir ")[-1])
                  and dados[3].endswith("cliente relativo") and str(srv2.name) not in dados[3].split(" --skills-dir ")[-1],
                  str(dados))
        casa_r = tmp / "casa relativa"
        casa_r.mkdir()
        c, out, err = lanza("instalar", enteros[1], "--uv", os.path.join(".", uv.name), "--servidor", "servidor relativo",
                            en=casa_r, desde=tmp)
        comprueba("una carpeta de servidor relativa que aún no existe y un uv relativo se entienden desde donde se lanza "
                  "la orden", c == 0 and (tmp / "servidor relativo" / "BUILD-INFO.txt").is_file() and "uv sync: bien" in out
                  and "SAIL CLI: bien" in out and "skill appian: bien" in out, out + err)
        con_enlace, otra = tmp / "con enlace", tmp / "otra"
        con_enlace.mkdir()
        (otra / "sub").mkdir(parents=True)
        if enlaza(con_enlace / "enlace", otra / "sub"):
            donde = con_enlace if os.name == "nt" else otra   # Windows quita el `..` antes de mirar el enlace; los demás, después
            shutil.copy(uv, donde / uv.name)
            tras_enlace = con_enlace / "enlace" / ".."
            c, out, err = lanza("instalar", enteros[1], "--uv", tras_enlace / uv.name, "--servidor", tras_enlace / "servidor",
                                en=casa_r)
            comprueba("un `..` detrás de un enlace lleva a la carpeta que dice el sistema, la del servidor y la de uv",
                      c == 0 and (donde / "servidor" / "BUILD-INFO.txt").is_file() and "uv sync: bien" in out, out + err)
            if os.name == "nt":
                os.rmdir(con_enlace / "enlace")           # quita la unión, no lo enlazado
        perfil = tmp / "perfil"
        perfil.mkdir()
        shutil.copy(enteros[1], perfil / "descarga.tar.gz")
        shutil.copy(uv, perfil / uv.name)
        en_perfil = dict(en=casa_r, HOME=str(perfil), USERPROFILE=str(perfil))
        c, out, err = lanza("instalar", "~/descarga.tar.gz", "--uv", f"~/{uv.name}", "--servidor", "~/servidor", **en_perfil)
        c2, out2, err2 = lanza("estado", "--bundle", "~/descarga.tar.gz", "--servidor", "~/servidor", **en_perfil)
        comprueba("una ruta con ~ vale en todas las órdenes, y también para uv",
                  c == 0 and "uv sync: bien" in out and (perfil / "servidor" / "BUILD-INFO.txt").is_file()
                  and c2 == 0 and "es el instalado" in out2, out + err + out2 + err2)
        c, out, err = lanza("estado", "--bundle", "~usuario-que-no-existe/descarga.tar.gz", "--servidor", "~/servidor",
                            **en_perfil)
        comprueba("una ruta que no se puede entender para con 2 y sin traza", c == 2 and "Traceback" not in err, err)
        c, out, err = instalar(3, SETUP_AVISA="1")
        comprueba("si el instalador de SAIL CLI termina bien pero avisa (sail fuera del PATH), no se da por bueno sin más",
                  c == 0 and "SAIL CLI: REVISAR" in out and "PATH" in out and "skill appian: bien" in out, out + err)

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
        (tmp / "Mayúsculas").mkdir()
        distingue = not (tmp / "mayúsculas").exists()    # Linux sí; Windows y lo habitual en macOS, no
        comprueba("y donde las mayúsculas distinguen, la carpeta antigua, que es otra, se quita",
                  not distingue or not (srv3 / "Docs").exists(), str(sorted(p.name for p in srv3.iterdir())))

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
        error = lambda herramienta, tipo, dice="API error (HTTP 404)": {"tool": herramienta, "objectType": tipo, "error": dice}
        # Las respuestas del Dev MCP de los objetos que mira el banco, como las guarda el extractor: su build_model.py
        # arma con ellas el modelo. Ficticias y con lo justo: campos, relaciones, tareas y el valor de dos constantes.
        RESPUESTAS = {
            ("recordType", "BPS Solicitud"): {"fields": [{"name": f"campo{k}"} for k in range(15)],
                                              "relationships": [{"name": f"relacion{k}"} for k in range(5)]},
            ("constant", "BPS_ESTADO_BORRADOR"): {"type": "INTEGER", "value": 1},
            ("constant", "BPS_ESTADO_RECHAZADA"): {"type": "INTEGER", "value": 4},
            ("processModel", "BPS Enviar a Aprobacion"): {"nodes": [
                {"name": "Confirmar envío", "type": "User Input Task"}, {"name": "Aprobar solicitud", "type": "User Input Task"},
                {"name": "Fin", "type": "End Event"}]},
        }

        def extraccion(nombre, respuestas=None, **cambios):
            informe = {"status": "complete", "objectListComplete": True, "app": {"name": "BPS Banco de pruebas SAIL"},
                       "objectsByType": dict(minimos), "objectCount": sum(minimos.values()),
                       "errors": [error("listObjectVersions", "folder", "No version history available for x"),
                                  error("listObjectVersions", "group", "No version history available for y"),
                                  error("getRecordEventsConfig", "recordType",
                                        "API error (HTTP 403): Record events not configured for this record type")]}
            informe.update(cambios)
            informe["errorCount"] = len(informe["errors"])
            raw = tmp / nombre / "extraccion" / "mcp_raw"
            raw.mkdir(parents=True)
            (tmp / nombre / "extraccion" / "extraction_report.json").write_text(json.dumps(informe), encoding="utf-8")
            objetos = [{"type": tipo, "uuid": f"uuid-{k}", "name": n} for k, (tipo, n) in enumerate(RESPUESTAS)]
            (raw / "_objects.json").write_text(json.dumps(
                {"application": {"uuid": "app-1", "type": "application", "name": "BPS Banco de pruebas SAIL", "prefix": "BPS"},
                 "objects": objetos}), encoding="utf-8")
            for o in objetos:   # la carpeta de cada objeto, como la nombra el extractor (rutas.carpeta_objeto)
                suya = raw / o["type"] / hashlib.sha1(o["uuid"].encode("utf-8")).hexdigest()[:12]
                suya.mkdir(parents=True)
                (suya / "get_definition.json").write_text(json.dumps(
                    {"_meta": {"tool": "get_definition", "role": "definition", "ok": True},
                     "response": {"name": o["name"], **{**RESPUESTAS, **(respuestas or {})}[(o["type"], o["name"])]}}),
                    encoding="utf-8")
            return tmp / nombre

        c, out, err = lanza("comprobar", "--extraccion", extraccion("extracción buena"), en=vacia)
        comprueba("con los objetos, el modelo y solo los errores previstos, pasa; dice cuáles quedan y lo que no se pidió",
                  c == 0 and "La extracción: PASA" in out and "getRecordEventsConfig, listObjectVersions" in out
                  and "5 hechos" in out and "Los recorridos con SAIL CLI: sin comprobar" in out, out + err)
        comprueba("y arma el modelo con el constructor del propio extractor",
                  (tmp / "extracción buena" / "extraccion" / "inventory.json").is_file())
        c, out, err = lanza("comprobar", "--extraccion", extraccion(
            "sin procesos", objectsByType={**minimos, "processModel": 0}), en=vacia)
        comprueba("si el extractor deja de ver un tipo de objeto, no pasa y dice cuál",
                  c == 1 and "La extracción: NO PASA" in out and f"processModel: 0 de {minimos['processModel']}" in out,
                  out + err)
        c, out, err = lanza("comprobar", "--extraccion", extraccion("genérica", errors=[
            error("getTaskReport", t) for t in ("constant", "folder", "interface")]), en=vacia)
        comprueba("una herramienta con errores en tres tipos de objeto no pasa: se está probando en todos",
                  c == 1 and "getTaskReport" in out and "devmcp_policy.json" in out, out + err)
        c, out, err = lanza("comprobar", "--extraccion", extraccion("no lee interfaces", errors=[
            error("getInterface", "interface", "API error (HTTP 500)")] * 5), en=vacia)
        comprueba("un error que el banco no espera no pasa, aunque sea de un solo tipo de objeto",
                  c == 1 and "errores que el banco no espera: getInterface (en interface)" in out, out + err)
        c, out, err = lanza("comprobar", "--extraccion", extraccion("otro valor", respuestas={
            ("constant", "BPS_ESTADO_RECHAZADA"): {"type": "INTEGER", "value": 9}}), en=vacia)
        comprueba("si el modelo no dice lo que dice la especificación, no pasa y dice qué",
                  c == 1 and "BPS_ESTADO_RECHAZADA: value es 9 y la especificación dice 4" in out, out + err)
        c, out, err = lanza("comprobar", "--extraccion", extraccion("booleano", respuestas={
            ("constant", "BPS_ESTADO_BORRADOR"): {"type": "BOOLEAN", "value": True}}), en=vacia)
        comprueba("un «verdadero» no vale por el 1 que dice la especificación",
                  c == 1 and "BPS_ESTADO_BORRADOR: value es True" in out, out + err)
        c, out, err = lanza("comprobar", "--extraccion", extraccion("sin permiso", errors=[error(
            "getRecordEventsConfig", "recordType",
            "API error (HTTP 401): Unauthorized; diagnostic: Record events not configured for this record type")]), en=vacia)
        comprueba("un error de permisos que menciona el texto del previsto no es el previsto",
                  c == 1 and "errores que el banco no espera: getRecordEventsConfig" in out, out + err)
        c, out, err = lanza("comprobar", "--extraccion", extraccion("sin campos", respuestas={
            ("recordType", "BPS Solicitud"): {"fields": [{"name": "id"}], "relationships": []}}), en=vacia)
        comprueba("si el extractor deja de leer los campos de un record type, no pasa",
                  c == 1 and "fieldCount es 1 y la especificación dice 15" in out, out + err)
        c, out, err = lanza("comprobar", "--extraccion", extraccion("cortada", status="partial"), en=vacia)
        comprueba("una extracción que no terminó no es un fallo: no se pudo comprobar",
                  c == 2 and "La extracción: NO SE PUDO" in out and "partial" in out, out + err)
        c, out, err = lanza("comprobar", "--extraccion", tmp / "no hay extracción", en=vacia)
        comprueba("sin informe de extracción, tampoco, y dice cómo se hace",
                  c == 2 and "NO SE PUDO" in out and "devmcp_extract.py" in out, out + err)
        c, out, err = lanza("comprobar", "--extraccion", extraccion(
            "mal formado", objectsByType={**minimos, "site": "uno"}), en=vacia)
        comprueba("un informe mal formado no cuenta como fallo del extractor: no se pudo comprobar",
                  c == 2 and "no es el informe de una extracción" in out and "Traceback" not in err, out + err)
        c, out, err = lanza("comprobar", en=vacia)
        comprueba("sin decir qué comprobar para con 2 y dice las dos cosas que se pueden pedir",
                  c == 2 and "--extraccion" in err and "--host" in err, err)

        print("Comprobar los recorridos del banco, con qa.py y el SAIL CLI simulado de appian-qa")
        simulado = AQUI.parent / "appian-qa" / "sail_simulado.py"
        sesiones = tmp / "sesiones de sail"
        (sesiones / "solicitante").mkdir(parents=True)
        (sesiones / "solicitante" / "session.json").write_text(json.dumps(
            {"hostname": HOST_BANCO, "username": "qa.solicitante", "cookies": []}), encoding="utf-8")
        (sesiones / "aprobador").mkdir()          # el SAIL CLI simulado no enseña «Nueva solicitud» a un revisor
        (sesiones / "aprobador" / "session.json").write_text(json.dumps(
            {"hostname": HOST_BANCO, "username": "qa.revisor", "cookies": []}), encoding="utf-8")
        de_qa = {"SAIL_CLI": str(simulado), "SAIL_HOME": str(sesiones), "SAIL_SIMULADO_APP": str(tmp / "app simulada.json")}
        recorre = lambda *mas, **mas_k: lanza("comprobar", "--host", HOST_BANCO, *mas, en=vacia, **de_qa, **mas_k)
        cuentas = ("--solicitante", "qa.solicitante", "--aprobador", "qa.revisor")
        # El SAIL CLI simulado es el de appian-qa, que es otra aplicación: sabe contestar a los guiones de la lista y
        # del permiso. Se repiten con una copia del plugin que solo trae esos dos; los demás, en el entorno de cada uno.
        copia = tmp / "plugin con dos guiones"
        for parte in ("appian-actualizacion", "appian-qa/scripts", "appian-functional-analyst/scripts"):
            shutil.copytree(SCRIPT.parents[2] / parte, copia / "skills" / parte, ignore=shutil.ignore_patterns("__pycache__"))
        for g in (copia / "skills" / "appian-actualizacion" / "assets" / "banco" / "guiones").glob("*.json"):
            if g.stem not in ("BPS-01.1", "BPS-06.1"):
                g.unlink()
        de_la_copia = {"script": copia / "skills" / "appian-actualizacion" / "scripts" / "actualizar.py"}
        c, out, err = recorre(*cuentas, **de_la_copia)
        comprueba("repite los guiones del banco con las cuentas que se le dan y dice lo que aún no recorre",
                  c == 0 and "Los recorridos con SAIL CLI: PASA" in out and "BPS-01.1 · pasa" in out
                  and "BPS-06.1 · pasa" in out and "aún no trae el recorrido" in out
                  and "La extracción: sin comprobar" in out, out + err)
        c, out, err = recorre("--solicitante", "qa.solicitante", "--aprobador", "qa.solicitante", **de_la_copia)
        comprueba("si quien no debe ver una acción la ve, el banco no pasa y dice en qué recorrido",
                  c == 1 and "Los recorridos con SAIL CLI: NO PASA" in out and "BPS-06.1 · falla" in out
                  and "BPS-01.1 · pasa" in out, out + err)
        c, out, err = recorre("--solicitante", "qa.solicitante")
        comprueba("sin la cuenta de un rol no se puede comprobar, y dice cuál falta",
                  c == 2 and "NO SE PUDO" in out and "--aprobador" in out and "--solicitante" not in out, out + err)
        (sesiones / "solicitante" / "session.json").write_text(json.dumps(
            {"hostname": HOST_BANCO, "username": "qa.solicitante", "cookies": [], "caducada": True}), encoding="utf-8")
        c, out, err = recorre(*cuentas)
        comprueba("con la sesión de sail caducada no es un fallo: no se pudo comprobar",
                  c == 2 and "Los recorridos con SAIL CLI: NO SE PUDO" in out and "Traceback" not in out + err, out + err)
        c, out, err = lanza("comprobar", "--extraccion", tmp / "sin procesos", "--host", HOST_BANCO, *cuentas,
                            en=vacia, **de_qa)
        comprueba("si una parte no pasa y otra no se pudo comprobar, sale con 1 y dice las dos",
                  c == 1 and "La extracción: NO PASA" in out and "Los recorridos con SAIL CLI: NO SE PUDO" in out, out + err)

        print("Entradas rotas: ni trazas de Python ni un «no se ha tocado» que no sea verdad")
        sin_traza = lambda *textos: "Traceback" not in "".join(textos)
        build3 = lambda: (srv3 / "BUILD-INFO.txt").read_text(encoding="utf-8")
        cortado, suma = tmp / "cortado.tar.gz", tmp / "suma cambiada.tar.gz"
        cortado.write_bytes(enteros[3].read_bytes()[:enteros[3].stat().st_size * 6 // 10])
        datos = bytearray(enteros[3].read_bytes())
        datos[-6] ^= 0xFF                               # la suma de comprobación del final del .gz
        suma.write_bytes(bytes(datos))
        for que, malo in (("cortado, como una descarga a medias", cortado), ("con la suma de comprobación cambiada", suma)):
            c, out, err = lanza("instalar", malo, "--uv", uv, en=casa3)
            c2, out2, err2 = lanza("estado", "--bundle", malo, en=casa3)
            comprueba(f"un bundle {que} para con 2, lo dice y no toca el servidor",
                      c == 2 and c2 == 2 and "descarga" in err and sin_traza(err, err2) and "sha2" in build3()
                      and not (srv3 / ".nuevo").exists(), err + err2)
        dentro_del_estado = casa3 / ".appian-analisis-funcional" / "un servidor"
        c, out, err = lanza("instalar", enteros[3], "--uv", uv, "--servidor", dentro_del_estado, en=casa3)
        comprueba("un servidor dentro de la carpeta donde se guardan las fotos para con 2 y no se crea",
                  c == 2 and "al revés" in err and not dentro_del_estado.exists(), err)
        casa5, fisico = tmp / "quinta casa", tmp / "servidor físico"
        (casa5 / ".appian-analisis-funcional").mkdir(parents=True)
        fisico.mkdir()
        enlace = casa5 / ".appian-analisis-funcional" / "actualizaciones"
        if enlaza(enlace, fisico):
            c, out, err = lanza("instalar", enteros[3], "--uv", uv, "--servidor", fisico, en=casa5)
            comprueba("si la carpeta de las fotos es un enlace que acaba dentro del servidor, para con 2 y no instala",
                      c == 2 and "al revés" in err and not any(fisico.iterdir()), out + err)
            if os.name == "nt":
                os.rmdir(enlace)                          # quita la unión, no lo enlazado
        sin_sha = bundle_entero(tmp, 3, "sin-sha", su_info=f"build_timestamp={BUILD[3]}\nmcp_src_sha=\n")
        c, out, err = lanza("instalar", sin_sha, "--uv", uv, en=casa3)
        comprueba("un bundle con el mcp_src_sha vacío para con 2", c == 2 and "mcp_src_sha" in err and "sha2" in build3(), err)
        c, out, err = lanza("instalar", enteros[3], "--uv", uv, "--plugin-sha", "", en=casa3)
        comprueba("un --plugin-sha vacío no se salta la comprobación", c == 2 and "No se ha tocado" in err, err)

        registro3 = next((casa3 / ".appian-analisis-funcional").rglob("instalado.json"))
        apuntado = json.loads(registro3.read_text(encoding="utf-8"))
        mio = srv3 / "notas mías.txt"
        mio.write_text("no son del bundle", encoding="utf-8")
        registro3.write_text(json.dumps({**apuntado, "raiz": apuntado["raiz"] + ["notas mías.txt"]}), encoding="utf-8")
        c, out, err = lanza("instalar", bundle_entero(tmp, 2, "docs", mas=[("docs/ahora.txt", "")]), "--uv", uv, en=casa3)
        comprueba("al repetir la instalación del mismo bundle no se quita nada: no hay copia de lo que se quitaría",
                  c == 0 and mio.is_file(), out + err)
        registro3.write_text(json.dumps({"build": apuntado["build"], "raiz": 5}), encoding="utf-8")
        c, out, err = lanza("instalar", enteros[3], "--uv", uv, en=casa3)
        comprueba("un registro de lo instalado con otra forma se ignora, sin traza",
                  c == 0 and sin_traza(out, err) and mio.is_file() and "sha3" in build3(), out + err)
        con_punto = bundle_entero(tmp, 4, "punto", punto=True)
        (srv3 / ".instalando").write_text(json.dumps({"build": f"{BUILD[4]} sha4", "sobran": 5}), encoding="utf-8")
        c, out, err = lanza("instalar", con_punto, "--uv", uv, en=casa3)
        comprueba("una marca de instalación a medias con otra forma para con 2, sin traza",
                  c == 2 and sin_traza(out, err) and "a medias" in err, out + err)
        (srv3 / ".instalando").unlink()
        c, out, err = lanza("instalar", con_punto, "--uv", uv, en=casa3)
        comprueba("un bundle que trae su propia raíz como entrada («.») se instala", c == 0 and "sha4" in build3(), out + err)

        c, out, err = lanza("informe", "--antes", fotos / BUILD[2], "--despues", foto1, en=vacia)
        comprueba("un informe con las fotos al revés lo avisa", c == 0 and "OJO" in out and "anterior" in out, out + err)
        c, out, err = lanza("informe", "--antes", foto1, "--despues", foto1, en=vacia)
        comprueba("y con dos fotos del mismo build, también", c == 0 and "mismo build" in out, out + err)
        (fotos / BUILD[2] / "sail-help" / "una carpeta.txt").mkdir()
        c, out, err = lanza("informe", "--antes", foto1, "--despues", fotos / BUILD[2], en=vacia)
        comprueba("una carpeta donde iría una ayuda no rompe el informe", c == 0 and sin_traza(out, err), out + err)

        hondo = tmp / "hondo.json"
        hondo.write_text('{"tools": ' + "[" * 100000 + "]" * 100000 + "}", encoding="utf-8")
        c, out, err = lanza("foto", "--catalogo", hondo)
        comprueba("un catálogo demasiado anidado para con 2, sin traza, y la foto que había sigue",
                  c == 2 and sin_traza(out, err) and (fotos / BUILD[3] / "BUILD-INFO.txt").is_file(), out[:300] + err[:300])
        suelto = tmp / "suelto.json"
        suelto.write_text('{"tools": [{"name": "a\\ud800b", "description": "x", "inputSchema": {}}]}', encoding="utf-8")
        c, out, err = lanza("foto", "--catalogo", suelto, con_sail=False)
        comprueba("un nombre de herramienta con un carácter que no se puede codificar no rompe la foto",
                  c == 0 and sin_traza(out, err) and (fotos / BUILD[3] / "devmcp.json").is_file()
                  and (fotos / BUILD[3] / "BUILD-INFO.txt").is_file(), out + err)

        guardada.write_bytes(guardada.read_bytes()[:200])
        c, out, err = lanza("sail-anterior", en=casa2)
        comprueba("sail-anterior con el bundle guardado dañado para con 2, sin traza",
                  c == 2 and sin_traza(out, err) and "no se pudo sacar" in err, out + err)

    comprueba("no queda __pycache__ en la skill", not list(SKILL.rglob("__pycache__")))
    print(f"\n{'TODO BIEN' if not fallos else f'{len(fallos)} FALLOS'}")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
