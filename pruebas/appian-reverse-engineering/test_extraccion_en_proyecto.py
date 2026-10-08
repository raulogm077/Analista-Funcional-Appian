"""La extracción vive en el proyecto, en <salida>/extraccion (D4), y se escribe ya saneada y con rutas cortas.

Saneada: sin secretos, con seudónimos en lugar de usuarios, sin correos, sin rutas locales y, de las aplicaciones del
entorno, solo la elegida. Rutas cortas, para que el proyecto quepa en Windows y en OneDrive.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

from conftest import BUILD_MODEL, SKILL

sys.path.insert(0, str(SKILL / "scripts"))
sys.path.insert(0, str(Path(__file__).parent / "mock_devmcp"))
import devmcp_extract as dx  # noqa: E402
import fixture  # noqa: E402
import privacidad  # noqa: E402
import rutas  # noqa: E402

OBJS, _, _ = fixture.build()
USUARIOS = sorted({u for us in fixture.GROUP_USERS.values() for u in us})
CORREO = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
OTRA_APP = ("OTR Otra Aplicación", "_a-0000e999-otr0")   # la otra aplicación del entorno simulado
CON_ESPACIOS = ("Carpeta con espacios", "Gestión app", "as-is")


def env_of(url: str) -> str:
    """URL del entorno (LCP_URL) cuyo Appian MCP Server es `url` (<entorno>/mcp)."""
    return url.rsplit("/mcp", 1)[0]


def extrae(project, *extra, check=0):
    return project.run("extract", "--app", "DEM", "--out", str(project.out), "--retry-delay", "0.1", *extra,
                       check=check)


def modelo(project):
    p = subprocess.run([sys.executable, str(BUILD_MODEL), str(project.out)], capture_output=True, text=True,
                       encoding="utf-8")
    assert p.returncode == 0, p.stderr


def con_mcp_server(project, http_server):
    """Dev MCP y Appian MCP Server del mismo entorno: doctor y datafabric también escriben en la extracción."""
    project.add_devmcp(LCP_URL=env_of(http_server))
    project.add_http("appian-mcp", http_server, {"Authorization": "Bearer dummy"})


# ---------------------------------------------------------------- comprobaciones

def dentro_del_proyecto(project):
    extraccion = project.out / "extraccion"
    assert project.interm() == extraccion and (extraccion / "mcp_raw" / "_objects.json").exists()
    # fuera de <salida>, solo lo que pone la prueba: la configuración MCP y el registro de llamadas del simulador
    fuera = sorted(f.relative_to(project.base).as_posix() for f in project.base.rglob("*")
                   if f.is_file() and project.out not in f.parents)
    assert fuera == ["calls.jsonl", "proj/.mcp.json"], fuera
    assert {p.name for p in project.base.iterdir()} == {"proj", "home", "calls.jsonl",
                                                       project.out.relative_to(project.base).parts[0]}
    assert not any(project.home.iterdir())                       # la carpeta home/ del conftest sigue vacía
    assert not list(project.base.rglob("_trabajo")) and not list(project.base.rglob(".gitignore"))


def sin_usuarios_ni_secretos(project):
    textos = {f.relative_to(project.out).as_posix(): f.read_text(encoding="utf-8")
              for f in project.out.rglob("*") if f.is_file()}
    for prohibido in (*USUARIOS, "sk_live_", str(project.base), *OTRA_APP):
        malos = [r for r, t in textos.items() if prohibido in t]
        assert not malos, (prohibido, malos)
    assert not [r for r, t in textos.items() if CORREO.search(t)]
    assert any("‹usuario-" in t for t in textos.values()) and any("‹correo›" in t for t in textos.values())
    detector = subprocess.run([sys.executable, str(SKILL / "scripts" / "detect_secrets.py"), str(project.out)],
                              capture_output=True, text=True, encoding="utf-8")
    assert detector.returncode == 0, detector.stdout      # el punto 4 de la validación final, con la extracción dentro
    # un mismo usuario tiene el mismo seudónimo en los miembros del grupo, en el historial y en las versiones
    raw = project.interm() / "mcp_raw"
    leer = lambda clave, tipo, herramienta: (rutas.carpeta_objeto(raw, tipo, OBJS[clave]["uuid"])  # noqa: E731
                                             / f"{herramienta}.json").read_text(encoding="utf-8")
    ana, marta = privacidad.seudonimo("ana.garcia"), privacidad.seudonimo("marta.ruiz")
    assert ana in leer("G_USR", "group", "listGroupMembers")
    assert ana in leer("PM_ALTA", "processModel", "listProcessInstances")
    assert marta in leer("G_GES", "group", "listGroupMembers")
    assert marta in leer("PM_ALTA", "processModel", "getObjectVersionHistory")
    # del fichero de configuración, solo su nombre; de las aplicaciones del entorno, cuántas hay y la elegida
    ext = project.interm()
    pre = json.loads((ext / "preflight.json").read_text(encoding="utf-8"))
    assert pre["devMcp"]["appsVisible"] == 2 and "apps" not in pre["devMcp"]
    assert pre["devMcp"]["configFile"] == pre["appianMcpServer"]["configFile"] == ".mcp.json"
    for fichero in ("extraction_report.json", "datafabric.json"):
        assert json.loads((ext / fichero).read_text(encoding="utf-8"))["server"]["configFile"] == ".mcp.json"
    assert "DEM Gestión de Solicitudes" in (raw / "_env" / "listApplications.json").read_text(encoding="utf-8")


def rutas_cortas(project):
    extraccion = project.interm()
    largas = [r for r in (f.relative_to(extraccion).as_posix() for f in extraccion.rglob("*") if f.is_file())
              if len(r) > 100]
    assert not largas, largas


def modelo_sin_fecha(project):
    inv = project.load("inventory.json")
    inv["source"].pop("extractedAt")
    return inv, project.load("graph.json")


def retomar(project):
    extrae(project)
    modelo(project)
    antes, llamadas = modelo_sin_fecha(project), len(project.calls_list())
    extrae(project)
    assert len(project.calls_list()) == llamadas                 # no vuelve a pedir lo que ya está
    modelo(project)
    assert modelo_sin_fecha(project) == antes                    # y el modelo sale igual


# ---------------------------------------------------------------- pruebas

def test_extraccion_dentro_del_proyecto(project):
    project.add_devmcp()
    extrae(project)
    dentro_del_proyecto(project)


def test_sin_usuarios_ni_secretos(project, http_server):
    con_mcp_server(project, http_server)
    project.run("doctor", "--json", "--out", str(project.out), check=0)
    extrae(project)
    project.run("datafabric", "--out", str(project.out), check=0)
    modelo(project)
    sin_usuarios_ni_secretos(project)


def test_barrido_final(project):
    """Una respuesta que cita a un usuario y se guardó antes de conocerlo (aquí, antes de extraer) queda saneada."""
    project.add_devmcp()
    raw = project.interm() / "mcp_raw"
    previa = rutas.carpeta_objeto(raw, "expressionRule", OBJS["R_ADMIN"]["uuid"]) / "getExpressionRule.json"
    previa.parent.mkdir(parents=True)
    respuesta = json.dumps({
        "_meta": {"tool": "getExpressionRule", "role": "definition", "ok": True, "objectUuid": OBJS["R_ADMIN"]["uuid"]},
        "response": {"uuid": OBJS["R_ADMIN"]["uuid"], "name": "DEM_ER_EsAdmin", "inputs": [],
                     "expression": '=or(loggedInUser() = "ana.garcia", '
                                   'a!isUserMemberOfGroup(loggedInUser(), cons!DEM_ADMIN_GROUP))'}})
    previa.write_text(respuesta, encoding="utf-8")
    extrae(project)                              # la usa tal cual y conoce a ana.garcia por los miembros de DEM Users
    texto = previa.read_text(encoding="utf-8")
    assert "ana.garcia" not in texto and privacidad.seudonimo("ana.garcia") in texto
    previa.write_text(respuesta, encoding="utf-8")                # barrido_final solo, con la lista ya guardada
    assert dx.barrido_final(raw) == 1
    assert "ana.garcia" not in previa.read_text(encoding="utf-8")
    assert dx.barrido_final(raw) == 0


def test_rutas_cortas(project):
    project.add_devmcp(MOCK_EXTRA_TOOLS=1)       # también la herramienta nueva, que se llama en todos los objetos
    extrae(project)
    modelo(project)
    rutas_cortas(project)


def test_retomar(project):
    project.add_devmcp()
    retomar(project)


def test_ruta_con_espacios(project, http_server):
    project.out = project.base.joinpath(*CON_ESPACIOS)
    con_mcp_server(project, http_server)
    project.run("doctor", "--json", "--out", str(project.out), check=0)
    retomar(project)
    project.run("datafabric", "--out", str(project.out), check=0)
    dentro_del_proyecto(project)
    sin_usuarios_ni_secretos(project)
    rutas_cortas(project)


def test_seudonimo_y_lo_que_no_es_un_usuario():
    s = privacidad.seudonimo
    assert s("Ana.Garcia") == s("ana.garcia") == "‹usuario-" + hashlib.sha256(b"ana.garcia").hexdigest()[:6] + "›"
    usuarios: set[str] = set()
    datos = {
        "inputs": [{"name": "aprobador", "type": "User"}],                      # entrada de tipo usuario: no es uno
        "processVariables": [{"name": "revisor", "type": "USER", "value": "luis.perez"}],
        "constante": {"uuid": "_a-1", "name": "DEM_SOPORTE", "type": "USER", "value": "pablo.soto"},
        "assignees": [{"type": "USER", "name": "elena.vidal"}, {"type": "GROUP", "name": "DEM Revisores"}],
        "displayName": "Solicitudes", "orderBy": "fechaAlta", "modifiedBy": "marta.ruiz",
        "nota": "Lo revisa marta.ruiz; dudas a soporte@example.org",
    }
    out = privacidad.sanea(datos, usuarios)
    assert out["inputs"] == datos["inputs"]
    assert out["processVariables"][0] == {"name": "revisor", "type": "USER", "value": s("luis.perez")}
    assert out["constante"]["name"] == "DEM_SOPORTE" and out["constante"]["value"] == s("pablo.soto")
    assert out["assignees"] == [{"type": "USER", "name": s("elena.vidal")}, {"type": "GROUP", "name": "DEM Revisores"}]
    assert out["displayName"] == "Solicitudes" and out["orderBy"] == "fechaAlta"
    assert out["modifiedBy"] == s("marta.ruiz") and out["nota"] == f"Lo revisa {s('marta.ruiz')}; dudas a ‹correo›"
    assert {"luis.perez", "pablo.soto", "elena.vidal", "marta.ruiz"} <= usuarios
    assert privacidad.sanea(out, usuarios) == out                # sanear dos veces es lo mismo que una
