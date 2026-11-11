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
elif len(a) == 2 and a[1] == "--help" and a[0] in d["ordenes"]:
    print(d["ordenes"][a[0]])
else:
    sys.exit(1)
'''
AYUDA = "Hace {o}.\n\nFlags:\n{flags}  -h, --help   ayuda de {o}\n"
SAIL = {
    1: {"version": "sail version 1.0.0 (aaa, built 2026-01-01)",
        "ordenes": {"load": AYUDA.format(o="load", flags=""),
                    "interact": AYUDA.format(o="interact", flags="      --confirm   confirma\n      --legacy    viejo\n"),
                    "old": AYUDA.format(o="old", flags="")}},
    2: {"version": "sail version 1.1.0 (bbb, built 2026-02-01)",
        "ordenes": {"load": AYUDA.format(o="load", flags=""),
                    "interact": AYUDA.format(o="interact", flags="      --confirm       confirma\n      --no-validate   envía igual\n")
                                + "\nVALIDA LOS ENVÍOS\nUn envío con un obligatorio vacío se rechaza.\n",
                    "tasks": AYUDA.format(o="tasks", flags="")}},
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
BUILD = {1: "20260101-000000", 2: "20260201-000000", 3: "20260301-000000"}


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

        def lanza(*args, en=casa, con_sail=True):
            entorno = {**os.environ, "APPIAN_RE_HOME": str(en), "SAIL_FALSO": str(sail_json), "PYTHONIOENCODING": "utf-8",
                       "SAIL_CLI": str(sail_py if con_sail else tmp / "no-hay-sail.py")}
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
                  c == 2 and "antes de instalar" in err, err)
        c, out, err = lanza("foto", "--catalogo", tmp / "no-existe.json")
        comprueba("un catálogo que no se puede leer para con 2", c == 2 and "catálogo" in err, err)
        c, out, err = lanza("foto", "--catalogo", sail_py)
        comprueba("un catálogo que no es JSON para con 2", c == 2 and "catálogo" in err, err)
        c, out, err = lanza("foto", "--catalogo", catalogos[1])
        fotos = next((casa / ".appian-analisis-funcional" / "actualizaciones").glob("appian-dev-mcp-server-*"))
        foto1 = fotos / BUILD[1]
        comprueba("guarda la foto en la carpeta de su build, por instalación",
                  c == 0 and all((foto1 / f).is_file() for f in ("BUILD-INFO.txt", "skill.bundle-manifest", "devmcp.json",
                                                                 "sail-help/_general.txt", "sail-help/_version.txt",
                                                                 "sail-help/interact.txt", "sail-help/old.txt")), out + err)
        comprueba("sin las órdenes que no son de sail (completion, help)",
                  not (foto1 / "sail-help" / "help.txt").exists() and not (foto1 / "sail-help" / "completion.txt").exists())
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
        c, out, err = lanza("informe", "--catalogo", catalogos[2])
        comprueba("el mismo informe, en texto",
                  c == 0 and all(x in out for x in (
                      f"Foto: {BUILD[1]} · Instalado: {BUILD[2]}", "nuevas: listDecisions", "desaparecidas: oldTool",
                      "cambia addThings: parámetros nuevos: objectUuids; quitados: objects; de los nuevos, obligatorios: objectUuids",
                      "pasan a obligatorios: description", "pasan a opcionales: note",
                      "cambia onlyEnum: solo textos o valores admitidos", "cambia solo la descripción: describeOnly",
                      "nuevos: references/decisions.md", "SAIL CLI   1.0.0 -> 1.1.0", "órdenes nuevas: tasks | retiradas: old",
                      "opciones nuevas: --no-validate; quitadas: --legacy", "validateDesignObjects: skills/")), out + err)

        print("Una pieza que falta en una foto")
        instala(servidor, 3)                             # el bundle 3: sin SAIL CLI y sin catálogo
        c, out, err = lanza("foto", con_sail=False)
        comprueba("la foto dice qué le falta", c == 0 and "sin SAIL CLI, catálogo del Dev MCP" in out, out + err)
        c, out, err = lanza("informe", con_sail=False)
        comprueba("el informe la da como «sin foto», no como «sin cambios»",
                  c == 0 and f"Foto: {BUILD[2]} · Instalado: {BUILD[3]}" in out and "DEV MCP    sin foto" in out
                  and "SAIL CLI   sin foto" in out and "SKILL appian   3 -> 3 ficheros" in out, out + err)

        print("Fotos dadas a mano y dos instalaciones")
        c, out, err = lanza("informe", "--antes", foto1, "--despues", fotos / BUILD[2], en=vacia)
        comprueba("con las dos fotos dadas no hace falta la instalación",
                  c == 0 and "nuevas: listDecisions" in out, out + err)
        c, out, err = lanza("informe", "--antes", tmp, "--despues", foto1)
        comprueba("una carpeta que no es una foto para con 2", c == 2 and "no es una foto" in err, err)
        otra = tmp / "otra instalación" / "appian-dev-mcp-server"
        instala(otra, 1)
        c, out, err = lanza("estado", "--servidor", otra)
        comprueba("otra instalación con el mismo nombre de carpeta no ve estas fotos",
                  c == 0 and "Fotos guardadas    ninguna" in out, out + err)

    comprueba("no queda __pycache__ en la skill", not list(SKILL.rglob("__pycache__")))
    print(f"\n{'TODO BIEN' if not fallos else f'{len(fallos)} FALLOS'}")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
