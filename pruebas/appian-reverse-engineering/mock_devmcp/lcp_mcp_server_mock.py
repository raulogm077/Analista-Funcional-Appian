"""Servidor Dev MCP simulado (stdio) para las pruebas de la skill.

Variables de entorno:
  MOCK_VARIANT=a|b          Variante A: nombres parecidos a los de la skill oficial de Appian.
                            Variante B: nombres y formas de respuesta distintos (prueba que la
                            skill no depende de nombres de herramientas).
  LCP_TOOL_MODE=readonly    Si no es readonly, expone también herramientas de escritura.
  MOCK_IGNORE_READONLY=1    Expone herramientas de escritura aunque LCP_TOOL_MODE=readonly
                            (simula un servidor que no respeta el modo).
  MOCK_FAIL_KEYS=K1,K2      Las herramientas de objeto fallan para esos objetos.
  MOCK_CALL_LOG=<fichero>   Registra cada llamada (jsonl).
  MOCK_APP=<módulo>         La aplicación que sirve: fixture (DEM, por defecto) o fixture_mal_hecha (MNT).
"""
from __future__ import annotations

import importlib
import json
import os
import sys
import time
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

sys.path.insert(0, str(Path(__file__).parent))
fixture = importlib.import_module(os.environ.get("MOCK_APP") or "fixture")

VARIANT = os.environ.get("MOCK_VARIANT", "a").lower()
READONLY = os.environ.get("LCP_TOOL_MODE", "full").lower() == "readonly"
EXPOSE_WRITES = (not READONLY) or os.environ.get("MOCK_IGNORE_READONLY") == "1"
FAIL_KEYS = {k for k in os.environ.get("MOCK_FAIL_KEYS", "").split(",") if k}
CALL_LOG = os.environ.get("MOCK_CALL_LOG")

OBJ, KEY_BY_UUID, NAMES = fixture.build()
APP = OBJ[fixture.APP_KEY]
OTHER_APP = {"uuid": "_a-0000e999-otr0-8000-9bb2-011c48011c48_00999", "name": "OTR Otra Aplicación", "prefix": "OTR"}

mcp = FastMCP("lcp-mock")


def log_call(tool: str, args: dict) -> None:
    if CALL_LOG:
        with open(CALL_LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"tool": tool, "args": args, "mode": os.environ.get("LCP_TOOL_MODE")}) + "\n")


def register(name: str, params: list[tuple[str, str, object]], handler, *, annotations=None, desc=""):
    """Registra una herramienta con una firma concreta (FastMCP deduce el esquema de la firma)."""
    sig = []
    for pname, ptype, default in params:
        if default is ...:
            sig.append(f"{pname}: {ptype}")
        else:
            sig.append(f"{pname}: {ptype} = {default!r}")
    names = [p[0] for p in params]
    src = f"def {name}({', '.join(sig)}) -> str:\n    return _h({{{', '.join(repr(n) + ': ' + n for n in names)}}})\n"
    ns: dict = {}

    def _h(kwargs):
        log_call(name, kwargs)
        return json.dumps(handler(**kwargs), ensure_ascii=False)

    ns["_h"] = _h
    exec(src, ns)  # noqa: S102 - solo en el mock de pruebas
    fn = ns[name]
    fn.__doc__ = desc or name
    mcp.add_tool(fn, name=name, description=desc or name, annotations=annotations)


RO = ToolAnnotations(readOnlyHint=True) if VARIANT == "b" else None
DESTRUCTIVE = ToolAnnotations(destructiveHint=True) if VARIANT == "b" else None


def obj_for(uuid: str, expected_type: str | None = None) -> dict:
    key = KEY_BY_UUID.get(uuid)
    if key is None:
        raise ValueError(f"Object not found: {uuid}")
    if key in FAIL_KEYS:
        raise RuntimeError("Simulated server error (HTTP 500)")
    o = OBJ[key]
    if expected_type and o["objType"] != expected_type:
        raise ValueError(f"Object {uuid} is not of type {expected_type}")
    return o


def public(o: dict) -> dict:
    return {k: v for k, v in o.items() if k not in ("key", "screen", "objType")}


def rename_b(d):
    """Variante B: otras claves para uuid/nombre/tipo y respuestas envueltas."""
    if isinstance(d, dict):
        out = {}
        for k, v in d.items():
            nk = {"uuid": "objectUuid", "name": "objectName", "type": "objectType"}.get(k, k)
            out[nk] = rename_b(v)
        return out
    if isinstance(d, list):
        return [rename_b(x) for x in d]
    return d


def app_objects():
    return [o for k, o in OBJ.items() if k != fixture.APP_KEY]


def dependents_of(uuid: str):
    o = obj_for(uuid)
    if o["objType"] not in fixture.DEPENDENTS_SUPPORTED:
        raise ValueError(f"Dependency analysis is not supported for type {o['objType']}")
    tkey = KEY_BY_UUID[uuid]
    out = []
    for src, dst, crumb in fixture.REFS:
        if dst == tkey:
            s = OBJ[src]
            out.append({"uuid": s["uuid"], "type": s["objType"], "name": s["name"], "breadcrumb": crumb})
    return out


def history_of(uuid: str, limit: int = 20):
    o = obj_for(uuid, "PROCESS_MODEL")
    h = fixture.PM_HISTORY[o["key"]]
    inst = []
    for i in range(min(limit, h["total"])):
        inst.append({"processId": 900000 + i, "status": "COMPLETED" if i >= h["errors"] else "PAUSED_BY_EXCEPTION",
                     "startTime": h["last"], "initiator": h["iniciador"]})
    return {"processModelUuid": uuid, "totalCount": h["total"], "instances": inst}


def versions_of(uuid: str):
    o = obj_for(uuid)
    out = [{"versionId": v, "modifiedBy": quien, "modifiedOn": cuando}
           for v, quien, cuando in fixture.VERSIONES.get(o["key"], fixture.VERSIONES["*"])]
    out[-1]["comment"] = f"Creación de {o['name']}"
    return out


def validate(uuid: str):
    o = obj_for(uuid)
    if o["objType"] not in ("INTERFACE", "FREEFORM_RULE", "WEB_API", "PROCESS_MODEL", "RECORD_TYPE"):
        raise ValueError(f"Validation not supported for {o['objType']}")
    issues = fixture.VALIDATION_ISSUES.get(o["key"], [])
    return {"valid": not any(i["severity"] == "ERROR" for i in issues), "issues": issues}


def render(uuid: str):
    o = obj_for(uuid, "INTERFACE")
    return {"componentTree": o.get("screen", {}), "diagnostics": {"error": []}}


def members(uuid: str):
    o = obj_for(uuid, "GROUP")
    mem = [{"type": "GROUP", "uuid": g["uuid"], "name": g["name"]}
           for g in OBJ.values() if g.get("parentGroupUuid") == o["uuid"]]
    mem += [{"type": "USER", "username": u} for u in fixture.GROUP_USERS.get(o["key"], [])]
    return mem


def getter(expected: str):
    return lambda **kw: public(obj_for(next(iter(kw.values())), expected))


def con_definicion(tipo: str) -> bool:
    """Si la aplicación trae la definición de algún objeto de ese tipo, y no solo su nombre."""
    return any(o["objType"] == tipo and set(o) - {"key", "uuid", "name", "objType"} for o in OBJ.values())


GET_TYPES = [
    ("RecordType", "RECORD_TYPE"), ("Interface", "INTERFACE"), ("Constant", "CONSTANT"),
    ("ProcessModel", "PROCESS_MODEL"), ("Site", "SITE"), ("WebApi", "WEB_API"),
    ("Integration", "OUTBOUND_INTEGRATION"), ("ConnectedSystem", "CONNECTED_SYSTEM"),
    ("Group", "GROUP"), ("AiAgent", "AI_AGENT"),
]
# CDTs y data stores, solo si la aplicación trae su definición: la DEM no la trae y su catálogo no cambia.
GET_TYPES += [(n, t) for n, t in (("DataType", "DATA_TYPE"), ("DataStore", "DATA_STORE")) if con_definicion(t)]

if VARIANT == "a":
    register("listApplications", [], lambda: {"applications": [
        {"uuid": APP["uuid"], "name": APP["name"], "prefix": APP["prefix"]}, OTHER_APP]})
    register("listNodeTypes", [], lambda: {"nodeTypes": [
        {"id": "core.0", "name": "Start Event"}, {"id": "core.1", "name": "End Event"},
        {"id": "core.4", "name": "XOR Gateway"}, {"id": "internal.16", "name": "Script Task"},
        {"id": "internal.17", "name": "User Input Task"},
        {"id": "internal3.write_records_to_source_23r3", "name": "Write Records"},
        {"id": "internal3.sendemail3", "name": "Send E-Mail"}, {"id": "internal3.integration", "name": "Call Integration"},
        {"id": "internal3.subprocess", "name": "Sub-Process"}]})
    register("listUsers", [], lambda: {"users": fixture.GROUP_USERS["G_USR"]})

    def _app(uuid):
        if uuid == OTHER_APP["uuid"]:
            return dict(OTHER_APP)
        return {**public(APP), "defaultObjects": {"administratorsGroupUuid": OBJ["G_ADM"]["uuid"],
                                                  "usersGroupUuid": OBJ["G_USR"]["uuid"]}}

    def _app_objects(uuid):
        if uuid != APP["uuid"]:
            return {}
        groups = {"RECORD_TYPE": "recordTypes", "INTERFACE": "interfaces", "FREEFORM_RULE": "expressionRules",
                  "CONSTANT": "constants", "PROCESS_MODEL": "processModels", "SITE": "sites", "WEB_API": "webApis",
                  "OUTBOUND_INTEGRATION": "integrations", "CONNECTED_SYSTEM": "connectedSystems", "GROUP": "groups",
                  "DECISION": "decisions", "DATA_TYPE": "dataTypes", "DATA_STORE": "dataStores",
                  "AI_AGENT": "aiAgents",
                  "RULE_FOLDER": "folders", "PROCESS_MODEL_FOLDER": "processModelFolders"}
        out: dict = {}
        for o in app_objects():
            out.setdefault(groups[o["objType"]], []).append({"uuid": o["uuid"], "name": o["name"]})
        return out

    register("getApplication", [("uuid", "str", ...)], _app)
    register("listApplicationObjects", [("uuid", "str", ...)], _app_objects)
    register("listRecordTypes", [("appUuid", "str", ...)], lambda appUuid: {"recordTypes": [
        {"uuid": o["uuid"], "name": o["name"]} for o in app_objects()
        if o["objType"] == "RECORD_TYPE" and appUuid == APP["uuid"]]})
    for tname, ttype in GET_TYPES + [("ExpressionRule", "FREEFORM_RULE")]:
        register(f"get{tname}", [("uuid", "str", ...)], getter(ttype))

    def _members(groupUuid, startIndex=0, batchSize=2):
        m = members(groupUuid)
        return {"members": m[startIndex:startIndex + batchSize], "totalCount": len(m)}

    register("listGroupMembers", [("groupUuid", "str", ...), ("startIndex", "int", 0), ("batchSize", "int", 2)], _members)
    register("getObjectDependents", [("uuid", "str", ...)], lambda uuid: {"dependents": dependents_of(uuid)})
    register("listProcessInstances", [("processModelUuid", "str", ...), ("limit", "int", 20)],
             lambda processModelUuid, limit=20: history_of(processModelUuid, limit))
    register("getObjectVersionHistory", [("uuid", "str", ...)], lambda uuid: {"versions": versions_of(uuid)})
    register("validateDesignObject", [("uuid", "str", ...)], validate)
    register("testInterface", [("uuid", "str", ...), ("inputs", "str", "")], lambda uuid, inputs="": render(uuid))
    register("testRule", [("uuid", "str", ...), ("type", "str", ...)], lambda uuid, type: {"result": "EXECUTED"})
    register("listRecordData", [("recordTypeUuid", "str", ...)], lambda recordTypeUuid: {"rows": [{"id": 1}]})
    register("getProcessModelNodeTypeSchema", [("typeId", "str", ...)], lambda typeId: {"schema": {}})
    if os.environ.get("MOCK_EXTRA_TOOLS") == "1":
        # Herramienta "nueva" que la skill no conoce: debe usarse sin tocar el codigo.
        register("describeSecurityRoleMap", [("objectUuid", "str", ...)], lambda objectUuid: {
            "object": obj_for(objectUuid)["name"],
            "roleMap": [{"group": OBJ["G_ADM"]["name"], "permission": "ADMINISTRATOR"},
                        {"group": OBJ["G_USR"]["name"], "permission": "VIEWER"}]})
    if EXPOSE_WRITES:
        register("createInterface", [("name", "str", ...), ("expression", "str", ...)], lambda name, expression: {"uuid": "new"})
        register("updateProcessModel", [("uuid", "str", ...), ("nodes", "str", "")], lambda uuid, nodes="": {"ok": True})
        register("deleteApplication", [("uuid", "str", ...)], lambda uuid: {"deleted": True})
        register("startProcessModel", [("uuid", "str", ...)], lambda uuid: {"processId": 1})
        register("sailClickButton", [("label", "str", ...)], lambda label: {"clicked": label})

else:  # Variante B
    def wrap(x):
        return {"result": rename_b(x)}

    register("searchApplications", [("query", "str", "")], lambda query="": wrap({"items": [
        {"uuid": APP["uuid"], "name": APP["name"], "prefix": APP["prefix"]}, OTHER_APP]}), annotations=RO)
    register("describeNodeCatalog", [], lambda: wrap([{"id": "core.0", "label": "Start Event"}]), annotations=RO)
    register("getApplicationDetails", [("applicationUuid", "str", ...)],
             lambda applicationUuid: wrap(public(APP) if applicationUuid == APP["uuid"] else OTHER_APP), annotations=RO)

    def _list_objs(applicationUuid, offset=0, limit=10):
        items = [{"uuid": o["uuid"], "name": o["name"], "type": o["objType"]} for o in app_objects()] \
            if applicationUuid == APP["uuid"] else []
        return wrap({"items": items[offset:offset + limit], "total": len(items)})

    register("listObjectsInApplication", [("applicationUuid", "str", ...), ("offset", "int", 0), ("limit", "int", 10)],
             _list_objs, annotations=RO)
    for tname, ttype in GET_TYPES:
        pname = tname[0].lower() + tname[1:] + "Uuid"
        register(f"get{tname}Definition", [(pname, "str", ...)],
                 (lambda t: (lambda **kw: wrap(public(obj_for(next(iter(kw.values())), t)))))(ttype), annotations=RO)
    register("getRuleDefinition", [("ruleUuid", "str", ...)],
             lambda ruleUuid: wrap(public(obj_for(ruleUuid, "FREEFORM_RULE"))), annotations=RO)
    register("findUsages", [("objectUuid", "str", ...)], lambda objectUuid: wrap({"usages": [
        {"uuid": d["uuid"], "type": d["type"], "name": d["name"], "location": d["breadcrumb"]}
        for d in dependents_of(objectUuid)]}), annotations=RO)

    def _hist(processModelUuid):
        h = history_of(processModelUuid, 0)
        k = KEY_BY_UUID[processModelUuid]
        return wrap({"executions": {"total": h["totalCount"], "lastStartedAt": fixture.PM_HISTORY[k]["last"],
                                    "failed": fixture.PM_HISTORY[k]["errors"]}})

    register("getProcessModelHistory", [("processModelUuid", "str", ...)], _hist, annotations=RO)
    register("listVersions", [("objectUuid", "str", ...)], lambda objectUuid: wrap([
        {"version": v["versionId"], "author": v["modifiedBy"], "date": v["modifiedOn"]} for v in versions_of(objectUuid)]),
        annotations=RO)
    register("renderInterface", [("interfaceUuid", "str", ...)],
             lambda interfaceUuid: wrap({"tree": render(interfaceUuid)["componentTree"]}), annotations=RO)
    register("validateObject", [("objectUuid", "str", ...)], lambda objectUuid: wrap(validate(objectUuid)), annotations=RO)
    # Verbo desconocido para la política: solo se usa en modo de confianza.
    register("computeMetrics", [("objectUuid", "str", ...)], lambda objectUuid: wrap(
        {"expressionLines": len(str(obj_for(objectUuid).get("expression", "")).splitlines())}))

    def _members_b(groupUuid, cursor=""):
        m = members(groupUuid)
        start = int(cursor or 0)
        nxt = str(start + 2) if start + 2 < len(m) else None
        return wrap({"members": m[start:start + 2], "nextCursor": nxt})

    register("listGroupMembersPage", [("groupUuid", "str", ...), ("cursor", "str", "")], _members_b, annotations=RO)
    register("evaluateExpressionRule", [("ruleUuid", "str", ...)], lambda ruleUuid: wrap({"value": 1}))
    register("listRecordRows", [("recordTypeUuid", "str", ...)], lambda recordTypeUuid: wrap({"rows": []}),
             annotations=RO)
    if EXPOSE_WRITES:
        register("createInterfaceObject", [("name", "str", ...)], lambda name: wrap({"uuid": "x"}), annotations=DESTRUCTIVE)
        register("removeObject", [("objectUuid", "str", ...)], lambda objectUuid: wrap({"deleted": True}))
        register("runProcessModel", [("processModelUuid", "str", ...)], lambda processModelUuid: wrap({"id": 1}))
        register("sailClickButton", [("label", "str", ...)], lambda label: wrap({"clicked": label}))


if __name__ == "__main__":
    if os.environ.get("MOCK_STARTUP_DELAY"):
        time.sleep(float(os.environ["MOCK_STARTUP_DELAY"]))
    mcp.run()
