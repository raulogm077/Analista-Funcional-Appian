"""Pruebas de devmcp_extract.py contra el Dev MCP simulado (variantes A y B)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from conftest import SKILL

sys.path.insert(0, str(SKILL / "scripts"))
import devmcp_extract as dx  # noqa: E402
from rutas import carpeta_objeto  # noqa: E402

WRITE_TOOLS = {"createInterface", "updateProcessModel", "deleteApplication", "startProcessModel", "sailClickButton",
               "createInterfaceObject", "removeObject", "runProcessModel"}
NEVER = WRITE_TOOLS | {"testRule", "listRecordData", "listUsers", "evaluateExpressionRule", "listRecordRows"}
EXPECTED_TYPES = {"aiAgent": 1, "cdt": 1, "connectedSystem": 2, "constant": 5, "decision": 1, "expressionRule": 2,
                  "folder": 1, "group": 4, "integration": 2, "interface": 5, "processModel": 4,
                  "processModelFolder": 1, "recordType": 2, "site": 1, "webApi": 1}


def uuid_of(key: str) -> str:
    sys.path.insert(0, str(Path(__file__).parent / "mock_devmcp"))
    import fixture
    objs, _, _ = fixture.build()
    return objs[key]["uuid"]


# ---------------------------------------------------------------- politica (unidad)

def test_policy_classification():
    pol = dx.Policy(dx.DEFAULT_POLICY)
    cases = {
        "deleteApplication": False, "createInterface": False, "sailClickButton": False, "runProcessModel": False,
        "testRule": False, "evaluateExpressionRule": False, "listRecordData": False, "listRecordRows": False,
        "listUsers": False, "getApiToken": False,
        "testInterface": True, "renderInterface": True, "getProcessModel": True, "listApplications": True,
        "getObjectDependents": True, "validateDesignObject": True, "findUsages": True,
    }
    for name, expected in cases.items():
        allowed, reason, _ = pol.safety(name, None, trusted=True)
        assert allowed is expected, f"{name}: {reason}"
    # verbo desconocido: permitido solo en modo de confianza
    assert pol.safety("computeMetrics", None, trusted=True)[0] is True
    assert pol.safety("computeMetrics", None, trusted=False)[0] is False

    class Ann:
        destructiveHint = True
        readOnlyHint = None
    assert pol.safety("getSomething", Ann(), trusted=True)[0] is False


def test_tokens_and_types():
    pol = dx.Policy(dx.DEFAULT_POLICY)
    assert dx.tokens("getWebAPIDefinition") == ["get", "web", "api", "definition"]
    assert pol.canon_type("FREEFORM_RULE") == "expressionRule"
    assert pol.canon_type("expressionRules") == "expressionRule"
    assert pol.canon_type("OUTBOUND_INTEGRATION") == "integration"
    assert pol.canon_type("webApis") == "webApi"
    assert pol.canon_type("AI_AGENT") == "aiAgent"          # tipo que la politica no conoce
    assert pol.canon_type("items") is None                   # clave contenedora


# ---------------------------------------------------------------- preflight

def test_doctor_ok(project):
    project.add_devmcp()
    p = project.run("doctor", "--json", check=0)
    rep = json.loads(p.stdout)
    assert rep["devMcp"]["status"] == "ok"
    assert rep["devMcp"]["appsVisible"] == 2
    assert rep["devMcp"]["trustedMode"] is True
    assert rep["appianMcpServer"]["status"] == "no_configurado"
    assert rep["docsMcp"]["status"] == "no_detectado_en_ficheros"
    assert all(c["mode"] == "readonly" for c in project.calls_list())


def test_doctor_not_configured(project):
    p = project.run("doctor", "--json", check=11)
    assert json.loads(p.stdout)["devMcp"]["status"] == "no_configurado"


def test_doctor_ambiguous(project):
    project.add_devmcp("appian")
    project.add_devmcp("appian-test-user", variant="b")
    project.run("doctor", "--json", check=12)
    project.run("doctor", "--json", "--server-name", "appian-test-user", check=0)


def env_of(url: str) -> str:
    """URL del entorno (LCP_URL) cuyo Appian MCP Server es `url` (<entorno>/mcp)."""
    return url.rsplit("/mcp", 1)[0]


def test_doctor_three_mcps(project, http_server):
    project.add_devmcp(LCP_URL=env_of(http_server))
    project.add_http("appian-mcp", http_server, {"Authorization": "Bearer ${APPIAN_KEY:-dummy}"})
    project.add_http("appian-public-docs", "https://appian-docs-public.mcp.kapa.ai")
    rep = json.loads(project.run("doctor", "--json", check=0).stdout)
    assert rep["appianMcpServer"]["status"] == "ok"
    assert rep["appianMcpServer"]["metadataCall"]["ok"] is True
    assert rep["appianMcpServer"]["recordTypesVisible"] == 3            # los del entorno: 2 de DEM y 1 de otra
    assert rep["docsMcp"]["status"] == "configurado"


# ---------------------------------------------------------------- extraccion

def _extract(project, *extra, check=0):
    return project.run("extract", "--app", "DEM", "--out", str(project.out), "--retry-delay", "0.1", *extra,
                       check=check)


def test_extract_variant_a_readonly_forced(project):
    project.add_devmcp(variant="a", mode="full")          # la configuracion pide full...
    _extract(project)
    calls = project.calls_list()
    assert calls and all(c["mode"] == "readonly" for c in calls)   # ...pero se fuerza readonly
    assert not NEVER & {c["tool"] for c in calls}
    objs = project.load("mcp_raw/_objects.json")
    counts = {}
    for o in objs["objects"]:
        counts[o["type"]] = counts.get(o["type"], 0) + 1
    assert counts == EXPECTED_TYPES
    assert objs["application"]["prefix"] == "DEM"
    rep = project.load("extraction_report.json")
    assert rep["server"]["toolModeForced"] == "readonly"
    assert "PASSWORD" not in json.dumps(rep)
    # definiciones de todos los tipos con herramienta, incluido el tipo nuevo AI_AGENT
    raw = project.interm() / "mcp_raw"
    assert (carpeta_objeto(raw, "aiAgent", uuid_of("AG_CLAS")) / "getAiAgent.json").exists()
    assert (carpeta_objeto(raw, "processModel", uuid_of("PM_BATCH")) / "getProcessModel.json").exists()
    assert (carpeta_objeto(raw, "interface", uuid_of("I_DASH")) / "testInterface.json").exists()
    # paginacion por startIndex: DEM Users tiene 2 grupos y 2 usuarios, en lotes de 2
    mem = json.loads((carpeta_objeto(raw, "group", uuid_of("G_USR")) / "listGroupMembers.json").read_text(encoding="utf-8"))
    assert mem["_meta"]["pages"] == 2 and len(mem["response"]["members"]) == 4
    # autodesactivacion: validateDesignObject no admite constantes
    assert any(d["tool"] == "validateDesignObject" and d["type"] == "constant" for d in rep["disabledAfterProbe"])


def test_extract_variant_b_other_names_and_shapes(project):
    project.add_devmcp(variant="b", mode="readonly")
    _extract(project)
    objs = project.load("mcp_raw/_objects.json")
    counts = {}
    for o in objs["objects"]:
        counts[o["type"]] = counts.get(o["type"], 0) + 1
    assert counts == EXPECTED_TYPES                        # paginacion offset/limit: 33 objetos en 4 paginas
    plan = project.load("extraction_plan.json")
    roles = {t["name"]: t["role"] for t in plan["tools"] if t["use"]}
    assert roles["getRuleDefinition"] == "definition"
    assert roles["findUsages"] == "dependents"
    assert roles["renderInterface"] == "screen"
    assert roles["getProcessModelHistory"] == "history"
    assert roles["listVersions"] == "versions"
    assert roles["listGroupMembersPage"] == "members"
    assert roles["computeMetrics"] == "other"              # verbo desconocido, modo de confianza
    raw = project.interm() / "mcp_raw"
    mem = json.loads((carpeta_objeto(raw, "group", uuid_of("G_USR")) / "listGroupMembersPage.json").read_text(encoding="utf-8"))
    assert mem["_meta"]["pages"] == 2                       # paginacion por cursor
    assert not NEVER & {c["tool"] for c in project.calls_list()}


def test_server_ignoring_readonly_goes_strict(project):
    project.add_devmcp(variant="b", mode="readonly", MOCK_IGNORE_READONLY=1)
    _extract(project)
    rep = project.load("extraction_report.json")
    assert rep["trustedMode"] is False
    called = {c["tool"] for c in project.calls_list()}
    assert not NEVER & called
    assert "computeMetrics" not in called                   # verbo desconocido en modo estricto
    assert "findUsages" in called                           # readOnlyHint / verbo de lectura


def test_new_tool_is_used_without_code_changes(project):
    project.add_devmcp(variant="a", MOCK_EXTRA_TOOLS=1)
    _extract(project)
    raw = project.interm() / "mcp_raw"
    files = list(raw.glob("*/*/describeSecurityRoleMap.json"))
    assert len(files) == 33                                 # todos los objetos, carpetas incluidas


def test_resume_makes_no_new_calls(project):
    project.add_devmcp()
    _extract(project)
    n = len(project.calls_list())
    _extract(project)
    assert len(project.calls_list()) == n


def test_partial_failure(project):
    project.add_devmcp(MOCK_FAIL_KEYS="I_DASH")
    _extract(project)
    rep = project.load("extraction_report.json")
    failed = {(e["tool"], e["object"]) for e in rep["errors"]}
    assert ("getInterface", uuid_of("I_DASH")) in failed
    raw = project.interm() / "mcp_raw"
    assert json.loads((carpeta_objeto(raw, "interface", uuid_of("I_FORM")) / "getInterface.json").read_text(encoding="utf-8"))["_meta"]["ok"]


def test_app_resolution(project):
    project.add_devmcp()
    project.run("plan", "--app", "noexiste", "--out", str(project.out), check=15)
    project.run("plan", "--app", "Otra", "--out", str(project.out), check=0)
    assert project.load("extraction_plan.json")["objectCount"] == 0


def test_confirmation_threshold(project, tmp_path):
    project.add_devmcp()
    pol = json.loads(dx.DEFAULT_POLICY.read_text(encoding="utf-8"))
    pol["confirmAboveCalls"] = 10
    pfile = tmp_path / "policy.json"
    pfile.write_text(json.dumps(pol), encoding="utf-8")
    _extract(project, "--policy", str(pfile), check=2)
    _extract(project, "--policy", str(pfile), "--yes", check=0)


def test_doctor_ignores_foreign_mcp_servers(project, http_server):
    """Un servidor que termina en /mcp pero no es del entorno del Dev MCP no se toma por el Appian MCP Server."""
    project.add_devmcp()  # entorno demo.appiancloud.com
    project.add_http("alphavantage", "https://mcp.alphavantage.co/mcp")
    project.add_http("otro-entorno", http_server)
    rep = json.loads(project.run("doctor", "--json", check=0).stdout)
    assert rep["appianMcpServer"]["status"] == "no_configurado"
    assert "demo.appiancloud.com/mcp" in rep["appianMcpServer"]["detail"]


def test_datafabric_ignores_foreign_mcp_servers(project, http_server):
    project.add_devmcp()
    project.add_http("otro-entorno", http_server, {"Authorization": "Bearer dummy"})
    _extract(project)
    p = project.run("datafabric", "--out", str(project.out), check=16)
    assert "demo.appiancloud.com/mcp" in p.stderr
    assert not (project.interm() / "datafabric.json").exists()


def test_datafabric_explicit_server_name(project, http_server):
    project.add_devmcp()
    project.add_http("appian-mcp", http_server, {"Authorization": "Bearer dummy"})
    _extract(project)
    project.run("datafabric", "--out", str(project.out), "--mcp-server-name", "appian-mcp", check=0)
    assert project.load("datafabric.json")["recordTypes"]


def test_datafabric_counts(project, http_server):
    project.add_devmcp(LCP_URL=env_of(http_server))
    project.add_http("appian-mcp", http_server, {"Authorization": "Bearer dummy"})
    _extract(project)
    project.run("datafabric", "--out", str(project.out), check=0)
    df = project.load("datafabric.json")
    counts = {r["name"]: r["count"] for r in df["recordTypes"]}
    assert counts == {"DEM Solicitud": 152, "DEM Estado": 4}


def test_plan_escribe_dentro_del_proyecto(project):
    """Desde la primera escritura, la extracción va en <salida>/extraccion: ni _trabajo aparte ni .gitignore."""
    project.add_devmcp()
    project.run("plan", "--app", "DEM", "--out", str(project.out), check=0)
    assert (project.out / "extraccion" / "extraction_plan.json").exists()
    assert not list(project.base.rglob(".gitignore")) and not list(project.base.rglob("_trabajo"))
