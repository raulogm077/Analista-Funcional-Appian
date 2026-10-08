#!/usr/bin/env python3
"""build_model.py - Convierte las respuestas del Dev MCP (mcp_raw) en inventory.json y graph.json.

Uso:
  python3 <skill>/scripts/build_model.py <carpeta_salida>

Lee   <trabajo>/mcp_raw/ (lo escribe devmcp_extract.py); <trabajo> = <salida>/extraccion
Crea  <trabajo>/inventory.json y graph.json (rutas "path" relativas a <trabajo>)

No depende de nombres de herramientas: cada fichero lleva en _meta.role el papel que le asigno la
politica (definition, dependents, dependencies, versions, history, validation, screen, members, other)
y el contenido se interpreta de forma tolerante (claves alternativas, respuestas envueltas).
Los objetos de fuera de la aplicacion son nodos externos del grafo (external: true): los que traen las herramientas
de dependencias, con su uuid, y los que una definicion llama con rule! o cons! y no estan en la aplicacion, sin uuid
(su id es la referencia, p. ej. rule!X). Si una herramienta de dependencias trajo uno de estos, es el mismo nodo.
Solo usa la biblioteca estandar.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from detect_secrets import buscar as secretos_en  # noqa: E402
from rutas import carpeta_objeto, work_dir  # noqa: E402

UUID_KEYS = ("uuid", "objectUuid", "designObjectUuid", "guid", "id", "objectId")
NAME_KEYS = ("name", "objectName", "displayName", "label", "title")
TYPE_KEYS = ("type", "objectType", "designObjectType", "typeName", "kind")
CRUMB_KEYS = ("breadcrumb", "location", "path", "context", "reference", "usage", "detail")
WRAPPERS = ("result", "data", "response", "object", "item", "definition", "value")
NO_SCAN_TYPES = {"application", "folder", "processModelFolder", "knowledgeCenter", "document"}
ENTRY_TYPES = {"application", "site", "webApi", "folder", "processModelFolder", "knowledgeCenter", "document"}
ORIGIN_RANK = {"dependents": 0, "dependencies": 1, "uuid": 2, "name": 3, "literal": 4, "derived": 5}
SECRET_NAME = re.compile(r"(?i)(token|secret|passw|pwd|api[_\-]?key|credential|private[_\-]?key)")
SECRET_VALUE = re.compile(r"sk_(live|test)_\w+|AKIA[0-9A-Z]{16}|(?i:bearer)\s+\S{8,}|-----BEGIN|eyJ[\w\-]{10,}\.[\w\-]{10,}"
                          r"|\b[A-Fa-f0-9]{32,}\b|\b[A-Za-z0-9+/]{40,}={0,2}")
DATE_RX = re.compile(r"^\d{4}-\d{2}-\d{2}([T ]\d{2}:\d{2}(:\d{2})?)?")
SLUG_MAXIMO = 48            # como el nombre de una herramienta (devmcp_extract.safe_name): rutas cortas en Windows
LLAMADO_CON_RULE = "llamado con rule!"   # tipo de un rule! de fuera: regla, interfaz, integracion o decision


# --------------------------------------------------------------------------- utilidades

def slugify(name: str | None, maximo: int = SLUG_MAXIMO) -> str:
    """Nombre de fichero estable para documentos por objeto: sin acentos, solo [A-Za-z0-9_-]. Nombra
    anexo/<tipo>/<slug>.md, 08-procesos-bpmn/<slug>.* y extraccion/procesos/<slug>.json: si no cabe, se recorta y
    lleva 8 hex del sha1 del nombre, para que dos nombres largos no se pisen (como devmcp_extract.safe_name)."""
    s = unicodedata.normalize("NFKD", name or "").encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^A-Za-z0-9_-]+", "_", s).strip("_")
    if not s:
        return "sin_nombre"
    if len(s) <= maximo:
        return s
    return f"{s[:maximo - 9]}-{hashlib.sha1(name.encode('utf-8')).hexdigest()[:8]}"


def desambiguar_slugs(objs: list[dict]) -> None:
    """Dos objetos del mismo tipo con el mismo slug (sin distinguir mayúsculas, como en Windows) se pisarían en
    el anexo y en 08: a los dos se les añade el principio de su uuid, sin pasar del tope."""
    vistos: dict[tuple[str, str], int] = defaultdict(int)
    for o in objs:
        vistos[(o["type"], o["slug"].lower())] += 1
    for o in objs:
        if vistos[(o["type"], o["slug"].lower())] > 1:
            o["slug"] = f'{o["slug"][:SLUG_MAXIMO - 9]}_{re.sub(r"[^A-Za-z0-9]", "", o["uuid"])[:8]}'


def load(p: Path) -> Any:
    return json.loads(p.read_text(encoding="utf-8"))


def pick(d: Any, keys, want=str) -> Any:
    if not isinstance(d, dict):
        return None
    low = {k.lower(): v for k, v in d.items()}
    for k in keys:
        v = low.get(k.lower())
        if isinstance(v, want) and v not in ("", None):
            return v
    return None


def unwrap(data: Any) -> Any:
    """Quita envoltorios de un solo nivel del tipo {"result": {...}}."""
    for _ in range(4):
        if isinstance(data, dict) and len(data) == 1:
            k = next(iter(data))
            if k.lower() in WRAPPERS and isinstance(data[k], (dict, list)):
                data = data[k]
                continue
        break
    return data


def walk(data: Any, depth=0):
    if depth > 12:
        return
    yield data
    if isinstance(data, dict):
        for v in data.values():
            yield from walk(v, depth + 1)
    elif isinstance(data, list):
        for v in data:
            yield from walk(v, depth + 1)


def find_key(data: Any, names: tuple[str, ...], want=(str, int, float, list, dict), max_depth=6):
    names_l = {n.lower() for n in names}
    for node in walk(data):
        if isinstance(node, dict):
            for k, v in node.items():
                if k.lower() in names_l and isinstance(v, want) and v not in ("", None, [], {}):
                    return v
    return None


def find_list(data: Any, names: tuple[str, ...]) -> list:
    v = find_key(data, names, want=(list,))
    return v if isinstance(v, list) else []


def primary_list(data: Any) -> list:
    best: list = []
    for node in walk(unwrap(data)):
        if isinstance(node, list) and len(node) > len(best):
            best = node
    if isinstance(unwrap(data), list) and not best:
        return unwrap(data)
    return best


def items_with_uuid(data: Any):
    for node in walk(data):
        if isinstance(node, dict):
            u = pick(node, UUID_KEYS)
            if isinstance(u, str) and len(u) >= 8:
                yield node


def dates_in(data: Any) -> list[str]:
    return [n for n in walk(data) if isinstance(n, str) and DATE_RX.match(n)]


def rel(p: Path, root: Path) -> str:
    return p.relative_to(root).as_posix()


# --------------------------------------------------------------------------- lectura de mcp_raw

def read_object_files(folder: Path) -> list[dict]:
    out = []
    for f in sorted(folder.glob("*.json")):
        try:
            d = load(f)
        except Exception:
            continue
        meta = d.get("_meta", {})
        out.append({"file": f, "tool": meta.get("tool", f.stem), "role": meta.get("role", "other"),
                    "ok": bool(meta.get("ok")), "error": meta.get("error"), "response": d.get("response")})
    return out


def choose_definition(files: list[dict]) -> dict | None:
    defs = [f for f in files if f["ok"] and f["role"] == "definition"]
    if defs:
        return max(defs, key=lambda f: len(json.dumps(f["response"], default=str)))
    return None


# --------------------------------------------------------------------------- extraccion de campos

def sail_of(defn: Any) -> str | None:
    v = find_key(defn, ("expression", "definition", "sail", "sailExpression", "body"), want=(str,))
    return v if isinstance(v, str) else None


def enrich_by_type(o: dict, defn: Any, name_by_uuid: dict):
    t = o["type"]
    desc = pick(defn, ("description",))
    if desc:
        o["description"] = desc
    if t in ("interface", "expressionRule", "webApi", "decision", "integration"):
        sail = sail_of(defn)
        if sail:
            o["sailBytes"] = len(sail.encode("utf-8"))
            o["sailLines"] = sail.count("\n") + 1
    if t == "constant":
        value = find_key(defn, ("value",), want=(str, int, float, list, bool))
        o["typeRef"] = pick(defn, ("type", "constantType", "dataType", "valueType", "objectType"))
        o["isArray"] = bool(find_key(defn, ("isArray", "multiple"), want=(bool,)))
        if SECRET_NAME.search(o.get("name") or "") or (isinstance(value, str) and SECRET_VALUE.search(value)):
            o["secret"] = True              # su nombre o su valor parecen un secreto
        if value is not None:
            o["value"] = value[:200] if isinstance(value, str) else value
        if isinstance(value, str) and value in name_by_uuid:
            o["valueRef"] = name_by_uuid[value]
    elif t == "integration":
        o["method"] = pick(defn, ("method", "httpMethod", "verb"))
        o["endpoint"] = pick(defn, ("relativePath", "endpoint", "url", "path", "uri"))
        cs = next((v for node in walk(defn) if isinstance(node, dict) for k, v in node.items()
                   if "connectedsystem" in k.lower() and isinstance(v, str)), None)
        if cs:
            o["connectedSystemRef"] = name_by_uuid.get(cs, cs)
        wr = find_key(defn, ("isWrite", "modifiesData", "writesData"), want=(bool,))
        if isinstance(wr, bool):
            o["modifiesData"] = wr
    elif t == "connectedSystem":
        o["csType"] = pick(defn, ("systemType", "connectedSystemType", "csType", "type", "objectType"))
        o["baseUrl"] = pick(defn, ("baseUrl", "baseURL", "url", "endpoint", "host"))
        o["authType"] = pick(defn, ("authType", "authenticationType", "authentication", "auth"))
    elif t == "webApi":
        o["method"] = pick(defn, ("httpMethod", "method", "verb"))
        o["endpointPath"] = pick(defn, ("urlAlias", "endpoint", "path", "url", "urlStub"))
    elif t == "processModel":
        nodes = find_list(defn, ("nodes", "activities", "flowNodes"))
        nodes = [n for n in nodes if isinstance(n, dict)]
        o["nodeCount"] = len(nodes)

        def ntype(n):
            return str(pick(n, ("type", "nodeType", "typeId", "schemaId", "objectType")) or "").lower()
        o["userTaskCount"] = sum(1 for n in nodes if (isinstance(n.get("assignment"), dict)
                                                     and n["assignment"].get("attended") is True)
                                 or "user" in ntype(n) or ntype(n) == "internal.17")
        o["subProcessCount"] = sum(1 for n in nodes if "subprocess" in ntype(n)
                                   or any("processmodeluuid" in k.lower() for node in walk(n)
                                          if isinstance(node, dict) for k in node))
        start = next((n for n in nodes if ntype(n) in ("core.0",) or "start" in ntype(n)), nodes[0] if nodes else None)
        blob = json.dumps(start or {}, default=str).lower()
        pm_blob = json.dumps(defn, default=str).lower()
        if any(k in blob for k in ("timer", "recurr", "schedule", "cron")):
            o["startType"] = "timer"
            timer = next((v for node in walk(start) if isinstance(node, dict) for k, v in node.items()
                          if any(x in k.lower() for x in ("timer", "recurr", "schedule", "cron"))), None)
            o["schedule"] = timer
        elif "message" in blob or '"receivemessage' in pm_blob:
            o["startType"] = "message"
        else:
            o["startType"] = "none"
        if o["startType"] == "timer":
            o["hasRecurrence"] = True
        sf = next((v for node in walk(defn) if isinstance(node, dict) for k, v in node.items()
                   if k.lower() == "startform" and isinstance(v, dict)), None)
        if sf:
            u = pick(sf, ("interfaceUuid", "uuid"))
            o["startFormInterface"] = name_by_uuid.get(u, u)
        grp = pick(defn, ("securityGroupName", "initiatorGroup", "securityGroup"))
        if grp:
            o["initiatorGroup"] = grp
    elif t == "site":
        pages = find_list(defn, ("pages",))
        o["pageCount"] = len(pages)
        o["urlStub"] = pick(defn, ("webAddressIdentifier", "urlStub", "urlIdentifier"))
    elif t == "group":
        parent = next((v for node in [defn] for k, v in (node.items() if isinstance(node, dict) else [])
                       if "parent" in k.lower() and isinstance(v, str)), None)
        if parent:
            o["parentGroup"] = name_by_uuid.get(parent, parent)
        o["groupType"] = pick(defn, ("groupType",))
    elif t == "recordType":
        fields = find_list(defn, ("fields",))
        o["fieldCount"] = len(fields)
        o["urlStub"] = pick(defn, ("urlStub", "urlIdentifier"))
        o["sourceType"] = pick(defn, ("sourceType", "dataSourceType", "source"))
        o["tableName"] = pick(defn, ("tableName", "table", "sourceTable"))
        o["relationshipCount"] = len(find_list(defn, ("relationships",)))


def enrich_roles(o: dict, files: list[dict], app_group_uuids: set[str], name_by_uuid: dict):
    extra = []
    for f in files:
        if not f["ok"]:
            continue
        r, data = f["role"], unwrap(f["response"])
        if r == "history":
            total = find_key(data, ("totalCount", "total", "totalResults", "count", "executions"), want=(int, float))
            lst = primary_list(data)
            failed = find_key(data, ("failed", "errors", "errorCount", "failedCount"), want=(int, float))
            sample = None
            if failed is None and lst:
                failed = sum(1 for it in lst if isinstance(it, dict)
                             and re.search(r"(?i)exception|error|fail", str(pick(it, ("status", "state")) or "")))
                if isinstance(total, (int, float)) and total > len(lst):
                    sample = len(lst)
            ds = sorted(dates_in(data))
            o["usage"] = {"executions": int(total) if isinstance(total, (int, float)) else len(lst),
                          "lastExecution": ds[-1] if ds else None, "failed": failed, "source": f["tool"]}
            if sample:
                o["usage"]["failedInSampleOf"] = sample
        elif r == "versions":
            lst = [x for x in primary_list(data) if isinstance(x, dict)]
            if lst:
                def d_of(x):
                    ds = dates_in(x)
                    return max(ds) if ds else ""
                last = max(lst, key=d_of)
                o["versions"] = {"count": len(lst), "lastModifiedOn": d_of(last) or None,
                                 "lastModifiedBy": pick(last, ("modifiedBy", "author", "user", "updatedBy", "username")),
                                 "source": f["tool"]}
        elif r == "validation":
            issues = [x for x in primary_list(data) if isinstance(x, dict)]
            o["validationIssues"] = [str(pick(x, ("message", "text", "description")) or x)[:200] for x in issues][:10]
        elif r == "screen":
            o["screen"] = rel_file(f)
        elif r == "members":
            mem = primary_list(data)
            groups = [x for x in mem if isinstance(x, dict) and (pick(x, UUID_KEYS) in app_group_uuids
                                                                 or str(pick(x, TYPE_KEYS) or "").upper() == "GROUP")]
            o["memberGroups"] = [pick(g, NAME_KEYS) or name_by_uuid.get(pick(g, UUID_KEYS)) for g in groups]
            o["userCount"] = len([x for x in mem if isinstance(x, dict)]) - len(groups)
        elif r in ("other", "dependencies", "dependents", "definition"):
            if r == "other":
                extra.append(f["tool"])
    if extra:
        o["extraTools"] = extra


_ROOT: Path = Path(".")


def rel_file(f: dict) -> str:
    return rel(f["file"], _ROOT)


# --------------------------------------------------------------------------- aristas

def ref_type(src_type: str, dst_type: str) -> str:
    if src_type == "site" and dst_type in ("interface", "recordType", "report", "processModel"):
        return "pageRef"
    if dst_type == "constant":
        return "constRef"
    if dst_type == "processModel":
        return {"processModel": "subProcess", "constant": "constValue"}.get(src_type, "startProcess")
    if dst_type == "integration":
        return "integrationCall"
    if dst_type in ("expressionRule", "interface", "decision", LLAMADO_CON_RULE):
        return "viewRef" if (src_type == "recordType" and dst_type == "interface") else "ruleRef"
    return {"recordType": "recordTypeRef", "connectedSystem": "connectedSystemRef", "group": "groupRef",
            "cdt": "typeRef", "site": "siteRef", "webApi": "webApiRef"}.get(dst_type, "ref")


def externos_de_dependencias(objs: list[dict], files_by_uuid: dict, by_uuid: dict) -> dict[str, dict]:
    """Los objetos de fuera de la aplicación que traen las herramientas de dependencias, con su uuid y su tipo
    canónico. Se reúnen antes que las aristas para unir por nombre los que una definición llama con rule! o cons!."""
    out: dict[str, dict] = {}
    for o in objs:
        for f in files_by_uuid[o["uuid"]]:
            if not f["ok"] or f["role"] not in ("dependents", "dependencies"):
                continue
            for it in items_with_uuid(unwrap(f["response"])):
                u = pick(it, UUID_KEYS)
                if u != o["uuid"] and u not in by_uuid:
                    out.setdefault(u, {"id": u, "type": canon_ext(pick(it, TYPE_KEYS)), "name": pick(it, NAME_KEYS),
                                       "external": True})
    return out


def externo(external: dict, por_nombre: dict, prefijo: str, nombre: str, tipo: str) -> str:
    """El nodo de un objeto de fuera que una definición llama por su nombre (rule!X, cons!X): el que trajo una
    herramienta de dependencias, si lo trajo; si no, uno sin uuid cuyo id es la referencia."""
    i = por_nombre.get(nombre) or f"{prefijo}{nombre}"
    external.setdefault(i, {"id": i, "type": canon_ext(tipo), "name": nombre, "external": True})
    return i


class Edges:
    def __init__(self):
        self.e: dict[tuple, dict] = {}

    def add(self, s, t, rtype, origin, evidence=None):
        if not s or not t or s == t:
            return
        k = (s, t, rtype)
        cur = self.e.get(k)
        if cur is None:
            cur = self.e[k] = {"source": s, "target": t, "refType": rtype, "origin": origin, "evidence": []}
        elif ORIGIN_RANK[origin] < ORIGIN_RANK[cur["origin"]]:
            cur["origin"] = origin
        if evidence and evidence not in cur["evidence"] and len(cur["evidence"]) < 3:
            cur["evidence"].append(evidence)

    def list(self):
        out = []
        for e in self.e.values():
            e = dict(e)
            if not e["evidence"]:
                e.pop("evidence")
            out.append(e)
        return sorted(out, key=lambda x: (x["source"], x["target"], x["refType"]))


# --------------------------------------------------------------------------- principal

def main(out_dir: str) -> int:
    global _ROOT
    interm = work_dir(out_dir)
    root = interm
    _ROOT = interm
    raw = interm / "mcp_raw"
    if not (raw / "_objects.json").exists():
        print(f"ERROR: falta {raw / '_objects.json'} (ejecuta antes devmcp_extract.py extract)", file=sys.stderr)
        return 2
    idx = load(raw / "_objects.json")
    report = load(interm / "extraction_report.json") if (interm / "extraction_report.json").exists() else {}
    app = dict(idx["application"])
    objs = [dict(o) for o in idx["objects"]]
    by_uuid = {o["uuid"]: o for o in objs}
    by_uuid[app["uuid"]] = app
    name_by_uuid = {u: o.get("name") for u, o in by_uuid.items()}
    group_uuids = {o["uuid"] for o in objs if o["type"] == "group"}

    # ---- inventario
    files_by_uuid: dict[str, list[dict]] = {}
    parse_errors = 0
    for o in objs:
        folder = carpeta_objeto(raw, o["type"], o["uuid"])
        files = read_object_files(folder) if folder.exists() else []
        files_by_uuid[o["uuid"]] = files
        defn_file = choose_definition(files)
        if any(f["role"] == "definition" and not f["ok"] for f in files) and not defn_file:
            parse_errors += 1
        o["detail"] = "full" if defn_file else "none"
        o["path"] = rel_file(defn_file) if defn_file else (rel(folder, root) if folder.exists() else None)
        o["evidenceRef"] = f"mcp:{o['type']}/{o.get('name')}"
        o["slug"] = slugify(o.get("name"))
        o["files"] = [{"tool": f["tool"], "role": f["role"], "ok": f["ok"], "path": rel_file(f)} for f in files]
        if defn_file:
            enrich_by_type(o, unwrap(defn_file["response"]), name_by_uuid)
        enrich_roles(o, files, group_uuids, name_by_uuid)
        secretos = sum(1 for f in files for _ in secretos_en(f["file"]))   # lo que encuentra detect_secrets.py
        if secretos:
            o["secrets"] = secretos
        o.pop("sources", None)
    app_files = sorted((raw / "_app").glob("*.json")) if (raw / "_app").exists() else []
    app_obj = {"type": "application", "name": app.get("name"), "uuid": app["uuid"], "prefix": app.get("prefix"),
               "description": app.get("description"), "mcpType": "APPLICATION", "detail": "full",
               "path": rel(app_files[0], root) if app_files else None, "evidenceRef": f"mcp:application/{app.get('name')}",
               "files": [{"tool": f.stem, "role": "app", "path": rel(f, root)} for f in app_files]}
    inv_objects: dict[str, list] = defaultdict(list)
    desambiguar_slugs(objs)
    inv_objects["application"].append(app_obj)
    for o in objs:
        inv_objects[o["type"]].append(o)
    counts = {t: len(v) for t, v in sorted(inv_objects.items())}
    inventory = {
        "source": {"kind": "devmcp", "url": (report.get("server") or {}).get("url"),
                   "toolMode": "readonly", "trustedMode": report.get("trustedMode"),
                   "extractedAt": report.get("startedAt"), "app": {k: app.get(k) for k in ("name", "uuid", "prefix")},
                   "toolsUsed": report.get("toolsUsed", []), "errorCount": report.get("errorCount", 0)},
        "counts": counts,
        "objects": dict(sorted(inv_objects.items())),
        "parseErrors": parse_errors,
    }

    # ---- grafo
    edges = Edges()
    type_of = {u: o["type"] for u, o in by_uuid.items()}
    external = externos_de_dependencias(objs, files_by_uuid, by_uuid)
    ext_por_nombre = {n["name"]: i for i, n in external.items() if n.get("name")}
    en_la_app = {o.get("name") for o in objs} | {app.get("name")}
    names = {}
    for o in objs:
        if o.get("name") and len(o["name"]) >= 6:
            names.setdefault(o["name"], o["uuid"])
    rule_callable = {o["name"]: o["uuid"] for o in objs
                     if o["type"] in ("expressionRule", "interface", "integration", "decision") and o.get("name")}
    const_by_name = {o["name"]: o["uuid"] for o in objs if o["type"] == "constant" and o.get("name")}
    def_text: dict[str, str] = {}
    for o in objs:
        u = o["uuid"]
        for f in files_by_uuid[u]:
            if not f["ok"]:
                continue
            data = unwrap(f["response"])
            if f["role"] in ("dependents", "dependencies"):
                for it in items_with_uuid(data):
                    other = pick(it, UUID_KEYS)
                    if other == u:
                        continue
                    crumb = pick(it, CRUMB_KEYS)
                    s, t = (other, u) if f["role"] == "dependents" else (u, other)
                    st = type_of.get(s) or external[s]["type"]
                    tt = type_of.get(t) or external[t]["type"]
                    edges.add(s, t, ref_type(st, tt), f["role"], crumb)
            elif f["role"] == "members" and o["type"] == "group":
                for it in primary_list(data):
                    g = pick(it, UUID_KEYS) if isinstance(it, dict) else None
                    if g in group_uuids:
                        edges.add(u, g, "memberGroup", "dependencies", "Miembro del grupo")
        defn = choose_definition(files_by_uuid[u])
        if defn and o["type"] not in NO_SCAN_TYPES:
            text = json.dumps(defn["response"], ensure_ascii=False, default=str)
            def_text[u] = text
            for other, ot in type_of.items():
                if other != u and ot not in NO_SCAN_TYPES and len(other) >= 8 and other in text:
                    edges.add(u, other, ref_type(o["type"], ot), "uuid")
            for m in re.finditer(r"rule!([A-Za-z0-9_]+)", text):
                if m.group(1) in rule_callable:
                    t = rule_callable[m.group(1)]
                    edges.add(u, t, ref_type(o["type"], type_of[t]), "name", f"rule!{m.group(1)}")
                elif m.group(1) not in en_la_app:
                    t = externo(external, ext_por_nombre, "rule!", m.group(1), LLAMADO_CON_RULE)
                    edges.add(u, t, ref_type(o["type"], external[t]["type"]), "name", f"rule!{m.group(1)}")
            for m in re.finditer(r"cons!([A-Za-z0-9_]+)", text):
                if m.group(1) in const_by_name:
                    edges.add(u, const_by_name[m.group(1)], "constRef", "name", f"cons!{m.group(1)}")
                elif m.group(1) not in en_la_app:
                    t = externo(external, ext_por_nombre, "cons!", m.group(1), "constant")
                    edges.add(u, t, "constRef", "name", f"cons!{m.group(1)}")
            for node in walk(unwrap(defn["response"])):
                if isinstance(node, str) and node in names and names[node] != u:
                    t = names[node]
                    if type_of[t] not in NO_SCAN_TYPES:
                        edges.add(u, t, ref_type(o["type"], type_of[t]), "literal", f'"{node}"')
    # startProcess derivado a traves de una constante de tipo process model
    elist = list(edges.e.values())
    const_to_pm = defaultdict(set)
    for e in elist:
        if e["refType"] == "constValue":
            const_to_pm[e["source"]].add(e["target"])
    for e in elist:
        if e["refType"] == "constRef" and e["target"] in const_to_pm and "startprocess" in def_text.get(e["source"], "").lower():
            for pm in const_to_pm[e["target"]]:
                edges.add(e["source"], pm, "startProcess", "derived",
                          f"a!startProcess vía cons!{by_uuid[e['target']].get('name')}")
    edge_list = edges.list()
    nodes = [{"id": app["uuid"], "type": "application", "name": app.get("name"), "path": app_obj["path"]}]
    nodes += [{"id": o["uuid"], "type": o["type"], "name": o.get("name"), "path": o.get("path")} for o in objs]
    nodes += list(external.values())
    indeg = Counter(e["target"] for e in edge_list)
    orphans = [o["uuid"] for o in objs if indeg[o["uuid"]] == 0 and o["type"] not in ENTRY_TYPES
               and not o.get("hasRecurrence")][:50]
    hubs = sorted(({"id": u, "name": name_by_uuid.get(u), "type": type_of.get(u), "in": n}
                   for u, n in indeg.items() if n >= 5 and u in type_of), key=lambda h: -h["in"])[:30]
    set_criticality(objs, edge_list)
    graph = {"nodes": nodes, "edges": edge_list,
             "stats": {"nodeCount": len(nodes), "edgeCount": len(edge_list), "orphanCount": len(orphans),
                       "hubCount": len(hubs), "externalNodes": len(external),
                       "edgesByOrigin": dict(Counter(e["origin"] for e in edge_list))},
             "orphans": orphans, "hubs": hubs}

    (interm / "inventory.json").write_text(json.dumps(inventory, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    (interm / "graph.json").write_text(json.dumps(graph, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"inventory.json: {sum(counts.values())} objetos ({parse_errors} sin definicion por error)")
    print(f"graph.json: {len(nodes)} nodos, {len(edge_list)} aristas {dict(Counter(e['origin'] for e in edge_list))}, "
          f"{len(orphans)} huerfanos, {len(hubs)} hubs")
    return 0


def set_criticality(objs: list[dict], edge_list: list[dict]) -> None:
    """Criticidad de cada process model, una sola fórmula para todos los documentos:
    2 por cada objeto que lo lanza (acción, interfaz, subproceso), 3 por cada integración que llama,
    5 si es batch y 2 si tiene tareas humanas. Crítico si suma 3 o más."""
    callers, integ = defaultdict(set), defaultdict(set)
    for e in edge_list:
        if e["refType"] in ("startProcess", "subProcess"):
            callers[e["target"]].add(e["source"])
        if e["refType"] == "integrationCall":
            integ[e["source"]].add(e["target"])
    for o in objs:
        if o["type"] != "processModel":
            continue
        u = o["uuid"]
        reasons, score = [], 0
        if callers[u]:
            score += 2 * len(callers[u])
            n = len(callers[u])
            reasons.append(f"lo lanza 1 objeto" if n == 1 else f"lo lanzan {n} objetos")
        if integ[u]:
            score += 3 * len(integ[u])
            n = len(integ[u])
            reasons.append("llama a 1 integración" if n == 1 else f"llama a {n} integraciones")
        if o.get("hasRecurrence"):
            score += 5
            reasons.append("batch programado")
        if o.get("userTaskCount"):
            score += 2
            reasons.append("1 tarea humana" if o["userTaskCount"] == 1 else f"{o['userTaskCount']} tareas humanas")
        o["criticality"] = {"score": score, "critical": score >= 3, "reasons": reasons,
                            "calledBy": len(callers[u]), "callsIntegrations": len(integ[u])}


_CAMEL = re.compile(r"[A-Z]+(?=[A-Z][a-z]|\d|$)|[A-Z]?[a-z]+|[A-Z]+|\d+")


def canon_ext(t: str | None) -> str:
    """Tipo canonico de un nodo externo, el del inventario: FREEFORM_RULE o «Expression Rule» -> expressionRule,
    CONSTANT -> constant... Un tipo ya canonico (processModel) se queda igual, y LLAMADO_CON_RULE tambien."""
    if not t:
        return "unknown"
    if t == LLAMADO_CON_RULE:
        return t
    toks = [x.lower() for parte in re.split(r"[_\s]+", str(t)) for x in _CAMEL.findall(parte)]
    phrase = " ".join(toks)
    m = {"freeform rule": "expressionRule", "expression rule": "expressionRule", "outbound integration": "integration",
         "data type": "cdt", "web api": "webApi", "rule folder": "folder"}
    if phrase in m:
        return m[phrase]
    return toks[0] + "".join(x.capitalize() for x in toks[1:]) if toks else "unknown"


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
