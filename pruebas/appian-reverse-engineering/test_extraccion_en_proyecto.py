"""La extracción vive en el proyecto, en <salida>/extraccion (D4), y se escribe ya saneada y con rutas cortas.

Saneada: sin secretos, con seudónimos en lugar de usuarios, sin correos, sin rutas locales y, de las aplicaciones del
entorno, solo la elegida. Rutas cortas, para que el proyecto quepa en Windows y en OneDrive.
"""
from __future__ import annotations

import hashlib
import hmac
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
# la otra aplicación del entorno simulado y su record type, que el Appian MCP Server ve
OTRA_APP = ("OTR Otra Aplicación", "_a-0000e999-otr0", "OTR Expediente", "OTR_EXPEDIENTE")
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
    # del data fabric, solo los record types de la aplicación
    df = json.loads((ext / "datafabric.json").read_text(encoding="utf-8"))
    assert {r["name"] for r in df["metadataRaw"]["recordTypes"]} == {"DEM Solicitud", "DEM Estado"}


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


def regla_admin(project) -> str:
    """La definición guardada de DEM_ER_EsAdmin, que cita a ana.garcia (de DEM Users)."""
    raw = project.interm() / "mcp_raw"
    return (rutas.carpeta_objeto(raw, "expressionRule", OBJS["R_ADMIN"]["uuid"]) / "getExpressionRule.json").read_text(
        encoding="utf-8")


def test_una_ejecucion_sin_barrido(project):
    """Se piden antes los miembros, versiones y ejecuciones: la regla que cita a un usuario ya se escribe saneada."""
    project.add_devmcp()
    p = extrae(project)
    assert "Barrido final" not in p.stdout                       # no hizo falta la red
    regla = regla_admin(project)
    assert "ana.garcia" not in regla and privacidad.seudonimo("ana.garcia") in regla


def test_al_retomar_se_escribe_ya_saneado(project):
    """En otra sesión, lo que se escribe sale saneado con los usuarios que se reconocen por sus huellas."""
    project.add_devmcp()
    extrae(project, "--skip", "getExpressionRule")              # sesión 1: todavía sin las reglas
    segunda = extrae(project)                                    # sesión 2: las pide; los miembros ya estaban guardados
    assert "Barrido final" not in segunda.stdout
    assert "ana.garcia" not in regla_admin(project) and privacidad.seudonimo("ana.garcia") in regla_admin(project)
    # un extractor nuevo, que aún no ha visto a nadie: el fichero que escribe guarda() ya está saneado
    ex = dx.Extractor(None, dx.Policy(dx.DEFAULT_POLICY), project.out)
    ti = dx.ToolInfo("getExpressionRule", "", {}, None, ["get", "expression", "rule"], allowed=True,
                     role="definition", scope="object")
    obj = {"uuid": "_a-nuevo-1", "type": "expressionRule", "name": "DEM_ER_Nueva"}
    f = ex.target_file(ti, "object", obj)
    ex.guarda(f, ti, "object", obj, {}, dx.CallResult(True, {"expression": '=loggedInUser() = "Ana.Garcia"'}))
    assert json.loads(f.read_text(encoding="utf-8"))["response"]["expression"] == \
        f'=loggedInUser() = "{privacidad.seudonimo("ana.garcia")}"'


def test_huellas_con_sal(tmp_path):
    raw = tmp_path / "mcp_raw"
    privacidad.Huellas(raw).añade({"ana.garcia", " Luis.Perez ", "x.y@example.org"})
    guardado = json.loads((raw / privacidad.HUELLAS).read_text(encoding="utf-8"))
    sal = bytes.fromhex(guardado["sal"])
    assert len(sal) == 32
    de = lambda u: hmac.new(sal, u.encode("utf-8"), hashlib.sha256).hexdigest()  # noqa: E731
    assert sorted(guardado["huellas"]) == sorted({de("ana.garcia"), de("luis.perez")})   # en minúsculas, sin el correo
    assert hashlib.sha256(b"ana.garcia").hexdigest() not in json.dumps(guardado)
    # otra sesión u otro equipo, con la carpeta del proyecto: reconoce a los mismos, sin distinguir mayúsculas
    assert privacidad.Huellas(raw).reconoce({"e": '= "ANA.GARCIA"', "k": {"luis.perez": 1}}) == {"ana.garcia", "luis.perez"}
    otro = tmp_path / "otro" / "mcp_raw"
    privacidad.Huellas(otro).añade({"ana.garcia"})
    assert json.loads((otro / privacidad.HUELLAS).read_text(encoding="utf-8"))["huellas"] != [de("ana.garcia")]
    assert privacidad.Huellas(tmp_path / "vacio").reconoce({"e": "ana.garcia"}) == set()


def test_preflight_camino_de_la_fase_0(project):
    """Fase 0: doctor por consola; con <salida> ya decidida, doctor --out; el modelo añade lo suyo. plan y extract
    lo vuelven a sanear, por si el modelo dejó la lista de aplicaciones o una ruta."""
    project.add_devmcp()
    consola = json.loads(project.run("doctor", "--json", check=0).stdout)
    assert len(consola["devMcp"]["apps"]) == 2 and not project.out.exists()
    project.run("doctor", "--json", "--out", str(project.out), check=0)
    fichero = project.interm() / "preflight.json"
    pre = json.loads(fichero.read_text(encoding="utf-8"))
    assert "apps" not in pre["devMcp"] and pre["devMcp"]["configFile"] == ".mcp.json"
    pre["docsMcp"]["status"] = "operativo"
    pre["environment"] = {"url": "https://demo.appiancloud.com", "isProduction": False, "appianVersion": None}
    pre["devMcp"].update(apps=consola["devMcp"]["apps"], configFile=consola["devMcp"]["configFile"])   # un descuido
    fichero.write_text(json.dumps(pre, ensure_ascii=False), encoding="utf-8")
    extrae(project)
    texto = fichero.read_text(encoding="utf-8")
    pre = json.loads(texto)
    assert "apps" not in pre["devMcp"] and pre["devMcp"]["configFile"] == ".mcp.json"
    assert pre["docsMcp"]["status"] == "operativo" and pre["environment"]["isProduction"] is False
    assert str(project.base) not in texto and not [a for a in OTRA_APP if a in texto]


def test_definiciones_de_tipo_usuario_no_cambian():
    """Un parámetro, una variable o una entrada de tipo usuario no es una persona: la definición no cambia."""
    datos = {"uuid": "pm-1", "name": "DEM Revisar", "processParameters": [{"name": "revisor", "type": "User"}],
             "processVariables": [{"name": "aprobador", "type": "USER", "isParameter": True}],
             "ruleInputs": [{"name": "solicitante", "type": "User or Group"}],
             "nodes": [{"id": 2, "name": "Revisión", "assignment": {"assignees": [{"type": "EXPRESSION", "value": "pv!revisor"}]},
                        "data": {"inputs": [{"name": "Para", "expression": "=pv!revisor"}]}}]}
    usuarios: set[str] = set()
    assert privacidad.sanea(datos, usuarios) == datos and not usuarios
    # tras un dominio de SAIL (pv!, ri!, local!…) nunca hay un usuario, aunque se llame igual
    assert privacidad.sanea({"e": "=pv!revisor & ri!revisor & local!revisor.x"}, {"revisor"}) == \
        {"e": "=pv!revisor & ri!revisor & local!revisor.x"}


def test_rutas_cortas_con_tipo_largo(tmp_path):
    raw = tmp_path / "extraccion" / "mcp_raw"
    uuid = OBJS["PM_ALTA"]["uuid"]
    largo = "translationSetStringRecordTypeRelationshipFolder"   # un tipo largo del catálogo
    carpeta = rutas.carpeta_objeto(raw, largo, uuid)
    assert len((carpeta / f"{dx.safe_name('getDesignObject' * 10)}.json").relative_to(raw.parent).as_posix()) <= 100
    assert carpeta != rutas.carpeta_objeto(raw, largo + "Item", uuid)          # dos tipos largos no se pisan
    assert rutas.carpeta_objeto(raw, "processModel", uuid).parent.name == "processModel"   # los habituales, igual


def test_sin_rutas_sin_distinguir_mayusculas_ni_separador():
    carpetas = ["C:\\Users\\Raul\\OneDrive - Empresa\\Proyectos"]
    texto = ("No se pudo leer c:\\users\\raul\\onedrive - empresa\\proyectos\\x.json ni "
             "C:/Users/Raul/OneDrive - Empresa/Proyectos/y.json")
    out = dx.sin_rutas(texto, carpetas)
    assert out == "No se pudo leer ‹carpeta local›\\x.json ni ‹carpeta local›/y.json"
    assert dx.sin_rutas("/HOME/raul/p/a.json", ["/home/raul/p"]) == "‹carpeta local›/a.json"
    assert dx.sin_rutas("/home/raul/proyectos2", ["/home/raul/proyectos"]) == "/home/raul/proyectos2"   # otra carpeta


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
    # formas corrientes en las respuestas: ningún usuario ni nombre de persona queda en claro
    usuarios = set()
    formas = {
        "versiones": {"modifiedBy": ["ana.garcia", "luis.perez"]},            # listas bajo una clave de usuario
        "assignees": ["elena.vidal"],
        "roleMap": [{"permission": "ADMINISTRATOR", "users": ["marta.ruiz"], "groups": ["DEM Administrators"]},
                    {"principal": "pablo.soto", "principalType": "USER", "permission": "EDITOR"}],
        "members": [{"uuid": "u-1", "name": "admin.dem", "type": "USER"}],     # un usuario con uuid
        "autor": {"modifiedBy": {"uuid": "u-2", "username": "ana.garcia", "displayName": "Ana García"}},
        "instancia": {"initiator": {"uuid": "u-9", "username": "luis.perez", "firstName": "Luis", "lastName": "Pérez"},
                      "initiatorName": "Luis Pérez", "createdByName": "Marta Ruiz"},
        "constantes": [{"uuid": "c-1", "name": "DEM_SOPORTE", "type": "User or Group", "value": "pablo.soto"},
                       {"uuid": "c-2", "name": "DEM_REVISOR", "type": "USER_OR_GROUP", "value": "Elena.Vidal"},
                       {"uuid": "c-3", "name": "DEM_REVISORES", "type": "USER_OR_GROUP", "value": "DEM Revisores"}],
        "ejecucionesPorUsuario": {"ana.garcia": 3},                           # un usuario como clave
        "nota": "Lo aprobó Ana.Garcia",                                       # sin distinguir mayúsculas
        "persona": {"type": "USER", "username": "x.y", "email": "x.y@example.org"},
    }
    out = privacidad.sanea(formas, usuarios)
    assert out["versiones"]["modifiedBy"] == [s("ana.garcia"), s("luis.perez")]
    assert out["assignees"] == [s("elena.vidal")]
    assert out["roleMap"] == [{"permission": "ADMINISTRATOR", "users": [s("marta.ruiz")], "groups": ["DEM Administrators"]},
                              {"principal": s("pablo.soto"), "principalType": "USER", "permission": "EDITOR"}]
    assert out["members"] == [{"uuid": "u-1", "name": s("admin.dem"), "type": "USER"}]
    assert out["autor"]["modifiedBy"] == {"uuid": "u-2", "username": s("ana.garcia"), "displayName": "‹nombre›"}
    assert out["instancia"] == {"initiator": {"uuid": "u-9", "username": s("luis.perez"), "firstName": "‹nombre›",
                                              "lastName": "‹nombre›"},
                                "initiatorName": "‹nombre›", "createdByName": "‹nombre›"}
    assert [c["value"] for c in out["constantes"]] == [s("pablo.soto"), s("elena.vidal"), "DEM Revisores"]
    assert [c["name"] for c in out["constantes"]] == ["DEM_SOPORTE", "DEM_REVISOR", "DEM_REVISORES"]
    assert out["ejecucionesPorUsuario"] == {s("ana.garcia"): 3}
    assert out["nota"] == f"Lo aprobó {s('ana.garcia')}"
    assert out["persona"] == {"type": "USER", "username": s("x.y"), "email": "‹correo›"}
    assert usuarios == {"ana.garcia", "luis.perez", "elena.vidal", "marta.ruiz", "pablo.soto", "admin.dem", "x.y"}
    assert privacidad.sanea(out, usuarios) == out
