"""La aplicación ficticia mal hecha (MNT) en el simulador del Dev MCP.

La usan las evaluaciones del recién llegado y de malas prácticas: sus preguntas y sus malas prácticas sembradas están en
pruebas/evaluaciones/aplicacion-ficticia/. Con MOCK_APP=fixture_mal_hecha, el simulador sirve MNT en un entorno de
preproducción; sin MOCK_APP, la aplicación DEM de siempre, que tiene que dar lo mismo que antes.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import socket
import subprocess
import sys
import time
import unicodedata
from pathlib import Path
from urllib.parse import urlparse

import pytest

from conftest import BUILD_MODEL, HTTP_MOCK, MOCK, PLUGIN, Project, free_port

AQUI = Path(__file__).resolve().parent
EVALUACION = AQUI.parent / "evaluaciones" / "aplicacion-ficticia"
SECCION = PLUGIN / "skills" / "appian-best-practices" / "scripts" / "seccion.py"
ENTORNO = "https://pre.mnt.example.org"     # preproducción: lo que pone el .mcp.json del proyecto de prueba
MNT = {"MOCK_APP": "fixture_mal_hecha", "LCP_URL": ENTORNO}
# Los objetos del marco común (otra aplicación, prefijo CMN) que llama MNT y que no están en la extracción
CMN = {"MNT_IF_FormularioOrden": "CMN_FormatearFecha", "MNT_PM_GestionOrden": "CMN_UsuarioActual",
       "MNT_IF_Panel": "CMN_IF_Cabecera"}
# Documento de as-is/ que responde cada pregunta: al menos una por documento del 01 al 11
DOCUMENTO = {"01": ["Q-01", "Q-02"], "02": ["Q-03", "Q-04"], "03": ["Q-05", "Q-06"], "04": ["Q-07", "Q-08", "Q-09"],
             "05": ["Q-10", "Q-22"], "06": ["Q-11"], "07": ["Q-12", "Q-13"], "08": ["Q-14", "Q-15", "Q-16"],
             "09": ["Q-17", "Q-18"], "10": ["Q-19"], "11": ["Q-20"], "LEEME": ["Q-21"]}
TIPOS = {"objeto", "numero", "si-no", "lista"}
CAPAS = {"datos", "seguridad", "procesos", "pantallas", "integraciones", "reglas"}
BP = re.compile(r"^BP (\d\d) §(\S+)$")
# Lo que respondía cada herramienta del simulador DEM antes de que sirviera otras aplicaciones (huella de arnes_dem)
OTRA_APP = "_a-0000e999-otr0-8000-9bb2-011c48011c48_00999"
HUELLA_DEM = {
    "a": {"catalogo": "5c6ac094ef5e", "describeSecurityRoleMap": "2f365f4b64f6", "getAiAgent": "ffeeb9a230c3",
          "getApplication": "efe373441871", "getConnectedSystem": "f36d110c4cb8", "getConstant": "1283d1b4f72c",
          "getExpressionRule": "0757c81da56b", "getGroup": "3bac4e3716f6", "getIntegration": "9e32e4a8ad0b",
          "getInterface": "404ce25ece2f", "getObjectDependents": "328a69cf5fab",
          "getObjectVersionHistory": "fa0108c2c7ec", "getProcessModel": "f158d80f5f07",
          "getProcessModelNodeTypeSchema": "0014ad02c3d5", "getRecordType": "fbeacd4f2ec3",
          "getSite": "f16f2977dd24", "getWebApi": "5dcd60088a74", "listApplicationObjects": "ec47c3db2c23",
          "listApplications": "1398d98d74bf", "listGroupMembers": "1d6ebabf3e1e", "listNodeTypes": "24c119150aa6",
          "listProcessInstances": "42128037ba9f", "listRecordData": "be8e27b05410", "listRecordTypes": "3646ead3f43c",
          "listUsers": "6015f8356ca6", "testInterface": "a5cd326f8216", "testRule": "1469083d3e49",
          "validateDesignObject": "0b9c22bb1d62"},
    "b": {"catalogo": "ea12760a8150", "computeMetrics": "c8d4b66716e2", "describeNodeCatalog": "5d811d69cc5f",
          "evaluateExpressionRule": "190176f0edca", "findUsages": "e0f119673353",
          "getAiAgentDefinition": "f324968e1519", "getApplicationDetails": "0fed835e20f4",
          "getConnectedSystemDefinition": "ae6a6b47165f", "getConstantDefinition": "cb682964dda1",
          "getGroupDefinition": "6d88882ffe9a", "getIntegrationDefinition": "217cb5c6f672",
          "getInterfaceDefinition": "ab41a8cdc74a", "getProcessModelDefinition": "b2d330a2d7ef",
          "getProcessModelHistory": "8620a4aa8492", "getRecordTypeDefinition": "65bd5880eefd",
          "getRuleDefinition": "fac12bfd484c", "getSiteDefinition": "f56a1b21223e",
          "getWebApiDefinition": "217b49dcf650", "listGroupMembersPage": "4153c7861437",
          "listObjectsInApplication": "11db9aa0956e", "listRecordRows": "2bb04a7b6887",
          "listVersions": "79db5408c765", "renderInterface": "3f1a210bd83a", "searchApplications": "e2714d44d8bf",
          "validateObject": "0ddff87d0b6a"},
}

sys.path.insert(0, str(AQUI / "mock_devmcp"))
import fixture  # noqa: E402  (DEM)


# ---------------------------------------------------------------- utilidades

def leer(nombre: str):
    return json.loads((EVALUACION / nombre).read_text(encoding="utf-8"))


def normal(texto) -> str:
    """Como se comparan las respuestas: sin tildes, en minúscula y con un espacio entre palabras."""
    t = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode("ascii")
    return " ".join(t.lower().split())


def extrae(project: Project, variante: str = "a") -> Project:
    project.add_devmcp(variant=variante, mode="readonly", **MNT)
    project.run("extract", "--app", "MNT", "--out", str(project.out), "--retry-delay", "0.1", check=0)
    p = subprocess.run([sys.executable, str(BUILD_MODEL), str(project.out)], capture_output=True, text=True,
                       encoding="utf-8")
    assert p.returncode == 0, p.stderr
    return project


@pytest.fixture(scope="module")
def mnt(tmp_path_factory):
    """La extracción y el modelo de MNT (variante A), una vez para todas las pruebas que solo los leen."""
    return extrae(Project(tmp_path_factory.mktemp("mnt")))


def objetos(p: Project) -> dict[str, dict]:
    return {o["name"]: o for lista in p.load("inventory.json")["objects"].values() for o in lista}


def definicion(p: Project, o: dict):
    assert o["detail"] == "full", o["name"]
    return json.loads((p.interm() / o["path"]).read_text(encoding="utf-8"))["response"]


def respuesta(p: Project, o: dict, rol: str):
    f = next(f for f in o["files"] if f["role"] == rol and f["ok"])
    return json.loads((p.interm() / f["path"]).read_text(encoding="utf-8"))["response"]


def llamadas_dentro(texto: str, funcion: str) -> list[str]:
    """El texto de cada llamada a `funcion` (p. ej. «a!forEach(»), con sus paréntesis equilibrados."""
    out = []
    for m in re.finditer(re.escape(funcion), texto):
        nivel, i = 1, m.end()
        while nivel and i < len(texto):
            nivel += {"(": 1, ")": -1}.get(texto[i], 0)
            i += 1
        out.append(texto[m.start():i])
    return out


# ---------------------------------------------------------------- la aplicación

def test_aplicacion_mnt(mnt):
    inv = mnt.load("inventory.json")
    app = inv["objects"]["application"][0]
    assert app["prefix"] == "MNT" and app["name"] == "MNT Mantenimiento de Instalaciones"
    assert mnt.load("mcp_raw/_objects.json")["application"]["prefix"] == "MNT"
    assert sum(n for t, n in inv["counts"].items() if t != "application") >= 40
    assert inv["source"]["url"] == ENTORNO


def test_herramienta_de_un_tipo_que_no_tiene(mnt):
    """MNT no tiene agentes de IA: getAiAgent es de ese tipo y no se prueba en los demás (ni da errores)."""
    rep = mnt.load("extraction_report.json")
    assert [e for e in rep["errors"] if e["tool"] == "getAiAgent"] == []
    assert [d for d in rep["disabledAfterProbe"] if d["tool"] == "getAiAgent"] == []


def test_cdt_y_data_store_con_definicion(mnt):
    obj = objetos(mnt)
    cdt, almacen = obj["MNT_OrdenDTO"], obj["MNT Datos Mantenimiento"]
    assert (cdt["type"], cdt["detail"]) == ("cdt", "full") and (almacen["type"], almacen["detail"]) == ("dataStore", "full")
    assert definicion(mnt, cdt)["fields"]
    assert [e["dataTypeUuid"] for e in definicion(mnt, almacen)["entities"]] == [cdt["uuid"]]


def test_entorno_de_preproduccion_y_proveedores_de_desarrollo(mnt):
    """El entorno no es de desarrollo y MNT_CS_Proveedores, sin autenticación, apunta a uno que sí lo es."""
    assert not re.search(r"(?i)\b(dev|desa\w*)\b", urlparse(ENTORNO).hostname)
    cs = objetos(mnt)["MNT_CS_Proveedores"]
    assert cs["authType"] == "NONE" and cs["baseUrl"] == "https://proveedores-dev.example.org"
    assert re.search(r"\bdev\b", urlparse(cs["baseUrl"]).hostname)


def test_marco_comun_fuera_de_la_extraccion(mnt):
    """Los tres objetos CMN están en la definición de quien los llama y en ningún sitio más de la extracción."""
    obj = objetos(mnt)
    for quien, cmn in CMN.items():
        assert f"rule!{cmn}(" in json.dumps(definicion(mnt, obj[quien]), ensure_ascii=False), (quien, cmn)
    assert "CMN_" not in (mnt.interm() / "inventory.json").read_text(encoding="utf-8")
    assert "CMN_" not in (mnt.interm() / "mcp_raw" / "_objects.json").read_text(encoding="utf-8")


def test_referencias_de_la_aplicacion(mnt):
    """Cada rule! y cons! de una definición es un objeto de MNT o uno de los tres del marco común, y no queda ninguna
    referencia del fixture sin resolver: si no, la ingeniería inversa vería objetos de fuera que no se sembraron."""
    obj = objetos(mnt)
    for nombre, o in obj.items():
        if o["detail"] != "full":
            continue
        texto = json.dumps(definicion(mnt, o), ensure_ascii=False)
        assert "{@" not in texto and '"@' not in texto, nombre
        for m in re.finditer(r"(?:rule|cons)!(\w+)", texto):
            assert m.group(1) in obj or m.group(1) in CMN.values(), (nombre, m.group(0))


def test_variante_b(mnt, tmp_path):
    """Con nombres y formas de respuesta distintos (variante B), los mismos objetos y las mismas definiciones."""
    b = extrae(Project(tmp_path), "b")
    detalle = lambda p: {n: (o["type"], o["detail"]) for n, o in objetos(p).items()}  # noqa: E731
    assert detalle(b) == detalle(mnt)


def test_datafabric(mnt):
    """El Appian MCP Server simulado también sirve MNT, con sus recuentos."""
    puerto = free_port()
    proc = subprocess.Popen([sys.executable, str(HTTP_MOCK), str(puerto)], env=dict(os.environ, MOCK_APP=MNT["MOCK_APP"]),
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        limite = time.time() + 20
        while time.time() < limite:
            try:
                socket.create_connection(("127.0.0.1", puerto), timeout=0.5).close()
                break
            except OSError:
                time.sleep(0.2)
        mnt.add_http("appian-mcp", f"http://127.0.0.1:{puerto}/mcp", {"Authorization": "Bearer dummy"})
        mnt.run("datafabric", "--out", str(mnt.out), "--mcp-server-name", "appian-mcp", check=0)
    finally:
        proc.terminate()
        proc.wait(timeout=10)
    recuentos = {r["name"]: r["count"] for r in mnt.load("datafabric.json")["recordTypes"]}
    assert recuentos == {"MNT Orden": 2315, "MNT Técnico": 12, "MNT Estado": 6}


# ---------------------------------------------------------------- malas prácticas y preguntas

def test_formato_de_las_malas_practicas(mnt):
    malas = leer("malas-practicas.json")
    assert [m["id"] for m in malas] == [f"MP-{i:02d}" for i in range(1, 12)]
    nombres = set(objetos(mnt))
    for m in malas:
        assert set(m) == {"id", "descripcion", "objetos", "capa", "bp"}, m["id"]
        assert m["descripcion"] and m["capa"] in CAPAS and BP.match(m["bp"]), m["id"]
        assert m["objetos"] and set(m["objetos"]) <= nombres, (m["id"], set(m["objetos"]) - nombres)


def test_bp_de_cada_mala_practica():
    """La regla de cada mala práctica es una sección que existe en appian-best-practices (seccion.py la encuentra)."""
    fallan = []
    for mala in leer("malas-practicas.json"):
        doc, seccion = BP.match(mala["bp"]).groups()
        p = subprocess.run([sys.executable, str(SECCION), doc, seccion], capture_output=True, text=True,
                           encoding="utf-8")
        if p.returncode:
            fallan.append((mala["id"], mala["bp"], p.stderr.strip()))
    assert not fallan


def test_malas_practicas_se_ven_en_la_extraccion(mnt):
    """Cada mala práctica sembrada está en lo que lee la ingeniería inversa."""
    obj = objetos(mnt)
    d = lambda n: definicion(mnt, obj[n])  # noqa: E731
    texto = lambda n: json.dumps(d(n), ensure_ascii=False)  # noqa: E731
    listado = d("MNT_IF_ListadoOrdenes")["expression"]                                              # MP-01
    assert "a!queryEntity(" in listado and "batchSize: -1" in listado and "filters" not in listado
    assert "logicalExpression" not in listado
    assert obj["MNT_IF_FormularioOrden"]["sailLines"] > 3000                                         # MP-02
    panel = d("MNT_IF_Panel")["expression"]                                                          # MP-03
    assert "showWhen: local!esAdmin" in panel and "a!isUserMemberOfGroup" in panel
    assert d("MNT Orden")["recordLevelSecurity"] == {"securityRules": [], "securityExpression": None}
    gestion = obj["MNT_PM_GestionOrden"]                                                             # MP-04
    assert gestion["nodeCount"] == 130 and gestion["subProcessCount"] == 0
    recordatorio = obj["MNT_PM_Recordatorio"]                                                        # MP-05
    assert recordatorio["schedule"]["recurrence"] == {"frequency": "MINUTES", "interval": 5}
    assert "rule!MNT_ER_OrdenesPendientes()" in texto("MNT_PM_Recordatorio")
    assert "erp-pre" in obj["MNT_URL_ERP_PRE"]["value"]                                              # MP-06
    assert "cons!MNT_URL_ERP_PRE" in texto("MNT_INT_ConsultarERP")
    assert obj["MNT_ERP_API_TOKEN"]["secret"] and obj["MNT_ERP_API_TOKEN"]["secrets"] >= 1           # MP-07
    erp = d("MNT_INT_ConsultarERP")                                                                  # MP-08
    assert erp["connectedSystemUuid"] is None and erp["timeout"] is None and erp["errorHandling"] is None
    llamada = next(n for n in d("MNT_PM_GestionOrden")["nodes"] if n["type"] == "internal3.integration")
    assert [s["expression"] for s in llamada["data"]["outputs"]] == ["ac!result.body"] and "exceptions" not in llamada
    assert not obj["ReglaCalculoPlazo"]["name"].startswith("MNT") and obj["calcFecha"]["type"] == "expressionRule"  # MP-09
    bucle = llamadas_dentro(d("MNT_IF_Tecnicos")["expression"], "a!forEach(")                        # MP-10
    assert len(bucle) == 1 and "a!queryRecordType(" in bucle[0]
    proveedores = obj["MNT_CS_Proveedores"]                                                          # MP-11
    assert proveedores["authType"] == "NONE" and "-dev." in proveedores["baseUrl"]


def test_formato_de_las_preguntas(mnt):
    preguntas = leer("preguntas.json")
    assert [q["id"] for q in preguntas] == [f"Q-{i:02d}" for i in range(1, 23)]
    for q in preguntas:
        assert set(q) == {"id", "pregunta", "respuestas", "tipo"} and q["tipo"] in TIPOS and q["respuestas"], q["id"]
        assert all(isinstance(r, str) or (q["tipo"] == "lista" and isinstance(r, list) and r) for r in q["respuestas"])
    por_id = {q["id"]: q for q in preguntas}
    assert por_id["Q-21"]["tipo"] == "lista" and por_id["Q-21"]["respuestas"] == [
        "CMN_FormatearFecha", "CMN_UsuarioActual", "CMN_IF_Cabecera", ["export", "acceso"]]
    assert (por_id["Q-22"]["tipo"], por_id["Q-22"]["respuestas"]) == ("objeto", ["MNT_CS_Proveedores"])
    # al menos una por documento del 01 al 11, y ninguna sin documento
    assert {f"{i:02d}" for i in range(1, 12)} <= set(DOCUMENTO)
    assert sorted(q for qs in DOCUMENTO.values() for q in qs) == sorted(por_id)
    # cada respuesta de tipo objeto es un objeto del inventario
    nombres = set(objetos(mnt))
    for q in preguntas:
        if q["tipo"] == "objeto":
            assert set(q["respuestas"]) <= nombres, (q["id"], set(q["respuestas"]) - nombres)


def calcula_respuestas(p: Project) -> dict:
    """Las respuestas, sacadas de la extracción como lo haría quien la lee (no del fixture)."""
    obj = objetos(p)
    d = lambda n: definicion(p, obj[n])  # noqa: E731
    nombre = {o["uuid"]: n for n, o in obj.items()}
    nodos = {n["name"]: n for n in d("MNT_PM_GestionOrden")["nodes"]}
    procesos = [o for o in obj.values() if o["type"] == "processModel"]
    hubs = p.load("graph.json")["hubs"]
    assert len(hubs) < 2 or hubs[0]["in"] > hubs[1]["in"]
    accion = next(a for a in d("MNT Orden")["actions"] if a["displayName"] == "Nueva orden")
    pagina = next(x for x in d("MNT Portal Mantenimiento")["pages"] if x["name"] == "Administración")
    supervisores = respuesta(p, obj["MNT Supervisores"], "members")["members"]
    recurrencia = obj["MNT_PM_Recordatorio"]["schedule"]["recurrence"]
    return {
        "Q-01": nombre[accion["processModelUuid"]],
        "Q-02": [a["name"] for a in nodos["Asignar técnico"]["assignment"]["assignees"]],
        "Q-03": len(procesos),
        "Q-04": hubs[0]["name"],
        "Q-05": [n for n, o in obj.items() if o["type"] == "dataStore"
                 and obj["MNT_OrdenDTO"]["uuid"] in [e["dataTypeUuid"] for e in d(n)["entities"]]],
        "Q-06": obj["MNT Orden"]["fieldCount"],
        "Q-07": d(re.search(r"cons!(\w+)", pagina["visibilityExpr"]).group(1))["value"],
        "Q-08": "si" if any(d("MNT Orden")["recordLevelSecurity"].values()) else "no",
        "Q-09": [m["username"] for m in supervisores if m["type"] == "USER"],
        "Q-10": [n for n, o in obj.items() if o["type"] == "constant"
                 and re.search(r"https?://[^/\s]*\b(dev|pre|test|uat|pro)\b", str(o.get("value")))],
        "Q-11": [n for n, o in obj.items() if o["type"] == "webApi"],
        "Q-12": f'{recurrencia["interval"]} minutos' if recurrencia["frequency"] == "MINUTES" else recurrencia,
        "Q-13": obj["MNT_PM_Recordatorio"]["usage"]["executions"],
        "Q-14": [o["name"] for o in procesos if o["usage"]["executions"] == 0],
        "Q-15": obj["MNT_PM_GestionOrden"]["nodeCount"],
        "Q-16": [a.get("name") for a in nodos["Validar cierre"]["assignment"]["assignees"]],
        "Q-17": [n for n, o in obj.items() if o.get("secret") or o.get("secrets")],
        "Q-18": [n for n in obj if not n.startswith("MNT")],
        "Q-19": [n for n, o in obj.items() if o["type"] == "interface" and any(
            "a!query" in c for c in llamadas_dentro(d(n)["expression"], "a!forEach("))],
        "Q-20": re.search(r'"Urgente",\s*(\d+)', d("ReglaCalculoPlazo")["expression"]).group(1),
        "Q-22": [n for n, o in obj.items() if o["type"] == "connectedSystem" and o.get("authType") == "NONE"],
    }


def test_respuestas_salen_de_la_extraccion(mnt):
    """Lo que dice preguntas.json es lo que dice la aplicación: si el fixture cambia, las respuestas lo siguen."""
    preguntas = {q["id"]: q for q in leer("preguntas.json")}
    for qid, calculada in calcula_respuestas(mnt).items():
        q = preguntas[qid]
        if q["tipo"] == "lista" or isinstance(calculada, list):
            esperada = [e for e in q["respuestas"] if isinstance(e, str)] if q["tipo"] == "lista" else q["respuestas"][:1]
            assert sorted(map(normal, calculada)) == sorted(map(normal, esperada)), (qid, calculada)
        else:
            assert normal(calculada) in {normal(r) for r in q["respuestas"]}, (qid, calculada)


# ---------------------------------------------------------------- el simulador DEM, igual que antes

def resumen(datos) -> str:
    return hashlib.sha256(json.dumps(datos, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:12]


async def arnes_dem(variante: str) -> dict[str, str]:
    """Huella del simulador sin MOCK_APP, sin pasar por el extractor: el catálogo (con las herramientas de escritura) y
    lo que responde cada herramienta de lectura a cada objeto. No depende de la versión del SDK de MCP: del catálogo,
    los nombres de los parámetros; de un error, solo que lo es."""
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    base = {k: v for k, v in os.environ.items() if not k.startswith(("MOCK_", "LCP_"))}

    async def sesion(modo, hacer):
        env = {**base, "MOCK_VARIANT": variante, "LCP_TOOL_MODE": modo, "MOCK_EXTRA_TOOLS": "1"}
        params = StdioServerParameters(command=sys.executable, args=[str(MOCK)], env=env)
        with open(os.devnull, "w") as nulo:
            async with stdio_client(params, errlog=nulo) as (r, w), ClientSession(r, w) as s:
                await s.initialize()
                return await hacer(s)

    async def catalogo(s):
        filas = []
        for t in (await s.list_tools()).tools:
            esquema, ann = t.inputSchema or {}, t.annotations
            filas.append([t.name, t.description, sorted(esquema.get("properties") or {}), esquema.get("required") or [],
                          getattr(ann, "readOnlyHint", None), getattr(ann, "destructiveHint", None)])
        return {"catalogo": resumen(sorted(filas))}

    uuids = [o["uuid"] for o in fixture.build()[0].values()] + [OTRA_APP]

    async def llamadas(s):
        out = {}
        for t in (await s.list_tools()).tools:
            req = list((t.inputSchema or {}).get("required") or [])
            casos = [{}] if not req else [{req[0]: u, **{p: "" for p in req[1:]}} for u in uuids]
            filas = []
            for args in casos:
                r = await s.call_tool(t.name, args)
                texto = "\n".join(getattr(c, "text", "") for c in r.content or [])
                filas.append([args, bool(r.isError), None if r.isError else texto])
            out[t.name] = resumen(filas)
        return out

    return {**await sesion("full", catalogo), **await sesion("readonly", llamadas)}


@pytest.mark.parametrize("variante", ["a", "b"])
def test_simulador_dem_igual_que_antes(variante):
    ahora = asyncio.run(arnes_dem(variante))
    cambian = sorted(k for k in set(ahora) | set(HUELLA_DEM[variante]) if ahora.get(k) != HUELLA_DEM[variante].get(k))
    assert not cambian, (f"El simulador DEM (variante {variante}) ya no responde igual en: {', '.join(cambian)}. "
                         f"Si el cambio es a propósito, la huella nueva es {json.dumps(ahora, sort_keys=True)}")
