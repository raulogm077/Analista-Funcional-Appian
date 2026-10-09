#!/usr/bin/env python3
"""devmcp_extract.py - Extrae una aplicacion Appian a disco a traves del Appian Dev MCP, en solo lectura.

No contiene nombres de herramientas: lee el catalogo del servidor en cada ejecucion, clasifica cada
herramienta por su firma y aplica la politica de scripts/devmcp_policy.json.

Ejecucion (uv instala el SDK MCP al vuelo; uv ya es requisito del Dev MCP):
  uv run --no-project --with "mcp>=1.2,<2" python "<skill>/scripts/devmcp_extract.py" <subcomando> [opciones]
  (desde la carpeta del usuario, donde esta su .mcp.json; <skill> es la carpeta de la skill)

Subcomandos:
  doctor      Estado de los 3 MCP: Dev MCP (obligatorio), Appian MCP Server y Docs MCP (opcionales).
  apps        Lista las aplicaciones visibles para el usuario del Dev MCP.
  plan        Catalogo + clasificacion + objetos de la app + estimacion de llamadas. No llama por objeto.
  extract     Ejecuta el plan y vuelca las respuestas en <out>/extraccion/mcp_raw/, dentro del proyecto.
  datafabric  Metadatos y COUNT(*) por record type de la app a traves del Appian MCP Server.

Las respuestas se guardan tal cual las devuelve el Dev MCP, con rutas cortas (Windows y OneDrive).

Codigos de salida:
  0 ok | 2 uso incorrecto | 11 Dev MCP no configurado | 12 varias configuraciones posibles
  13 el Dev MCP no arranca o no autentica | 14 no hay aplicaciones visibles
  15 app no encontrada o ambigua, o la carpeta ya tiene otra app u otro entorno (usa otra --out;
     para la misma app de otro entorno, tambien --refresh)
  16 Appian MCP Server no disponible (solo datafabric)
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import re
import sys
sys.dont_write_bytecode = True  # sin __pycache__ en el plugin: no se escribe fuera del proyecto
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rutas import carpeta_objeto, work_dir  # noqa: E402

EXIT_OK, EXIT_USAGE, EXIT_NO_CONFIG, EXIT_AMBIGUOUS, EXIT_START, EXIT_NO_APPS, EXIT_APP, EXIT_NO_MCPSERVER = \
    0, 2, 11, 12, 13, 14, 15, 16

HERE = Path(__file__).resolve().parent
DEFAULT_POLICY = HERE / "devmcp_policy.json"


# --------------------------------------------------------------------------- utilidades

_CAMEL = re.compile(r"[A-Z]+(?=[A-Z][a-z]|\d|$)|[A-Z]?[a-z]+|[A-Z]+|\d+")


def singular(tok: str) -> str:
    if len(tok) <= 3:
        return tok
    if tok.endswith("ies"):
        return tok[:-3] + "y"
    if tok.endswith(("ss", "us", "sis")):
        return tok
    if tok.endswith("s"):
        return tok[:-1]
    return tok


def tokens(name: str) -> list[str]:
    out: list[str] = []
    for part in re.split(r"[_\-\s\.:/]+", name or ""):
        out.extend(singular(t.lower()) for t in _CAMEL.findall(part))
    return out


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def safe_name(s: str, maximo: int = 48) -> str:
    """Nombre de fichero de una herramienta, corto para que la ruta quepa en Windows y en OneDrive: si no cabe, se
    recorta y lleva 8 hex del sha1 del nombre, para que dos nombres largos no se pisen. _meta.tool guarda el nombre."""
    limpio = re.sub(r"[^A-Za-z0-9_.\-]", "_", s)
    if len(limpio) <= maximo:
        return limpio
    return f"{limpio[:maximo - 9]}-{hashlib.sha1(s.encode('utf-8')).hexdigest()[:8]}"


def is_transient(error: str | None) -> bool:
    return bool(re.search(r"(?i)timeout|timed out|\b50[0-9]\b|temporar|connection|reset|unavailable|rate limit|429",
                          error or ""))


def eprint(*a):
    print(*a, file=sys.stderr, flush=True)


def expand_vars(value, env: dict):
    """Expande ${VAR} y ${VAR:-def} como hace Claude Code en .mcp.json."""
    if isinstance(value, str):
        def rep(m):
            var, _, default = m.group(1).partition(":-")
            return env.get(var, default)
        return re.sub(r"\$\{([^}]+)\}", rep, value)
    if isinstance(value, list):
        return [expand_vars(v, env) for v in value]
    if isinstance(value, dict):
        return {k: expand_vars(v, env) for k, v in value.items()}
    return value


# --------------------------------------------------------------------------- politica

class Policy:
    def __init__(self, path: Path):
        d = json.loads(Path(path).read_text(encoding="utf-8"))
        self.raw = d
        self.write = set(d["writeVerbs"])
        self.interaction = set(d["interactionTokens"])
        self.evaluation = set(d["evaluationVerbs"])
        self.read = set(d["readVerbs"])
        self.exceptions = [(re.compile(x["pattern"]), x["role"], x["reason"]) for x in d["allowExceptions"]]
        self.excludes = [(re.compile(x["pattern"]), x["reason"]) for x in d["excludePatterns"]]
        self.exclude_tokens = d.get("excludeTokens", [])
        self.roles = [(r["role"], set(r["tokens"])) for r in d["roles"]]
        self.def_verbs = set(d["definitionVerbs"])
        self.def_suffixes = set(d["definitionSuffixes"])
        self.syn: dict[str, list[list[str]]] = {k: [p.split() for p in v] for k, v in d["typeSynonyms"].items()}
        self.phrase_to_type = {" ".join(p): t for t, ps in self.syn.items() for p in ps}
        self.container_keys = set(d["listContainerKeys"])
        self.generic_skip = set(d["genericToolsSkipTypes"])
        self.pag = d["pagination"]
        self.probe = int(d["adaptiveDisable"]["probeCalls"])
        self.confirm_above = int(d["confirmAboveCalls"])

    def is_writeish(self, name: str, ann) -> bool:
        toks = tokens(name)
        return bool((toks and toks[0] in self.write) or self.interaction.intersection(toks)
                    or (ann is not None and getattr(ann, "destructiveHint", None) is True))

    def excluded_by_tokens(self, toks: list[str]) -> str | None:
        """Reglas por palabras del nombre, escriba como se escriba (queryRecordType, list_record_data…)."""
        ts = set(toks)
        for r in self.exclude_tokens:
            if (set(r.get("all", [])) <= ts and (not r.get("any") or ts & set(r["any"]))
                    and not ts & set(r.get("none", [])) and (not r.get("first") or (toks and toks[0] in r["first"]))
                    and (not r.get("last") or (toks and toks[-1] in r["last"]))):
                return r["reason"]
        return None

    def safety(self, name: str, ann, trusted: bool) -> tuple[bool, str, str | None]:
        toks = tokens(name)
        first = toks[0] if toks else ""
        unido = "".join(t.capitalize() for t in toks)   # list_record_data → ListRecordData: las reglas valen igual
        if ann is not None and getattr(ann, "destructiveHint", None) is True:
            return False, "El servidor la declara destructiva (destructiveHint).", None
        if first in self.write:
            return False, f"Verbo de escritura '{first}'.", None
        hit = self.interaction.intersection(toks)
        if hit:
            return False, f"Interaccion con la interfaz ('{sorted(hit)[0]}').", None
        motivo = self.excluded_by_tokens(toks)
        if motivo:
            return False, motivo, None
        for rx, reason in self.excludes:
            if rx.search(name) or rx.search(unido):
                return False, reason, None
        for rx, role, reason in self.exceptions:
            if rx.search(name) or rx.search(unido):
                return True, reason, role
        if first in self.evaluation:
            return False, f"Evalua o prueba logica ('{first}'): puede ejecutar integraciones o efectos reales.", None
        if ann is not None and getattr(ann, "readOnlyHint", None) is True:
            return True, "El servidor la declara de solo lectura (readOnlyHint).", None
        if first in self.read:
            return True, f"Verbo de lectura '{first}'.", None
        if trusted:
            return True, "Modo de confianza: el catalogo no expone herramientas de escritura.", None
        return False, f"Verbo desconocido '{first}' y el servidor no respeta el modo readonly (modo estricto).", None

    def canon_type(self, s: str | None) -> str | None:
        if not s:
            return None
        toks = tokens(s)
        if not toks:
            return None
        phrase = " ".join(toks)
        if phrase in self.phrase_to_type:
            return self.phrase_to_type[phrase]
        if len(toks) == 1 and toks[0] in self.container_keys:
            return None
        return toks[0] + "".join(t.capitalize() for t in toks[1:])


# --------------------------------------------------------------------------- configuracion de servidores

def home_dir() -> Path:
    return Path(os.environ.get("APPIAN_RE_HOME") or Path.home())


def config_files(cwd: Path, extra: list[str]) -> list[Path]:
    h = home_dir()
    files = [Path(p) for p in extra]
    for d in [cwd, *cwd.parents]:
        files.append(d / ".mcp.json")
    files += [h / ".claude.json",
              h / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json",
              Path(os.environ.get("APPDATA", h / "AppData" / "Roaming")) / "Claude" / "claude_desktop_config.json",
              h / ".config" / "Claude" / "claude_desktop_config.json",
              h / ".cursor" / "mcp.json", cwd / ".cursor" / "mcp.json",
              cwd / ".kiro" / "settings" / "mcp.json", h / ".kiro" / "settings" / "mcp.json",
              cwd / ".vscode" / "mcp.json"]
    seen, out = set(), []
    for f in files:
        k = str(f.resolve()) if f.exists() else str(f)
        if k not in seen and f.is_file():
            seen.add(k)
            out.append(f)
    return out


def server_entries(cwd: Path, extra: list[str]) -> list[tuple[Path, str, dict]]:
    out = []
    for f in config_files(cwd, extra):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        blocks = [data.get("mcpServers"), data.get("servers")]
        projects = data.get("projects")
        if isinstance(projects, dict):
            cwd_norm = str(cwd.resolve()).replace("\\", "/").lower().rstrip("/")
            for pk, pv in projects.items():
                if str(pk).replace("\\", "/").lower().rstrip("/") == cwd_norm and isinstance(pv, dict):
                    blocks.append(pv.get("mcpServers"))
        for b in blocks:
            if isinstance(b, dict):
                for name, entry in b.items():
                    if isinstance(entry, dict):
                        out.append((f, name, entry))
    return out


def is_devmcp(entry: dict) -> bool:
    blob = " ".join([str(entry.get("command", ""))] + [str(a) for a in entry.get("args", []) or []])
    return "lcp_mcp_server" in blob


def is_docs_mcp(entry: dict) -> bool:
    return "appian-docs" in str(entry.get("url", "")).lower()


def is_http(entry: dict) -> bool:
    return bool(entry.get("url")) and not entry.get("command")


@dataclass
class ServerChoice:
    source: str
    name: str
    command: str
    args: list[str]
    env: dict
    cwd: str | None = None


def choose_devmcp(args) -> tuple[ServerChoice | None, int, str]:
    cwd = Path.cwd()
    if args.bundle_dir and args.url:
        return ServerChoice("argumentos", "appian", "uv",
                            ["run", "--directory", str(Path(args.bundle_dir).resolve()), "python", "-m", "lcp_mcp_server"],
                            {"LCP_URL": args.url}), EXIT_OK, ""
    entries = server_entries(cwd, args.config or [])
    if args.server_name:
        cands = [e for e in entries if e[1] == args.server_name and e[2].get("command")]
    else:
        cands = [e for e in entries if is_devmcp(e[2])]
    uniq = {}
    for f, n, e in cands:
        uniq.setdefault((n, json.dumps(e, sort_keys=True)), (f, n, e))
    cands = list(uniq.values())
    if not cands:
        return None, EXIT_NO_CONFIG, ("No se ha encontrado la configuracion del Dev MCP (servidor con 'lcp_mcp_server'). "
                                      "Revisados: " + ", ".join(str(p) for p in config_files(cwd, args.config or [])) +
                                      ". Consulta references/devmcp-setup.md o usa --bundle-dir y --url.")
    if len(cands) > 1:
        return None, EXIT_AMBIGUOUS, ("Hay varias configuraciones del Dev MCP; elige una con --server-name: " +
                                      ", ".join(f"{n} ({f})" for f, n, _ in cands))
    f, n, e = cands[0]
    env = dict(e.get("env") or {})
    return ServerChoice(str(f), n, e["command"], list(e.get("args") or []), env, e.get("cwd")), EXIT_OK, ""


# --------------------------------------------------------------------------- cliente MCP

@dataclass
class CallResult:
    ok: bool
    data: Any = None
    error: str | None = None
    pages: int = 1
    seconds: float = 0.0


def parse_result(res) -> tuple[bool, Any, str | None]:
    text = "\n".join(getattr(c, "text", "") for c in (res.content or []) if getattr(c, "type", "") == "text")
    if res.isError:
        return False, None, (text or "Error sin mensaje")[:2000]
    if text:
        try:
            return True, json.loads(text), None
        except Exception:
            pass
    sc = getattr(res, "structuredContent", None)
    if isinstance(sc, dict):
        if set(sc) == {"result"} and isinstance(sc["result"], str):
            try:
                return True, json.loads(sc["result"]), None
            except Exception:
                return True, {"_text": sc["result"]}, None
        return True, sc, None
    return True, {"_text": text}, None


class McpSession:
    """Sesion stdio o http con el SDK oficial de MCP (importado de forma diferida)."""

    def __init__(self, *, stdio: ServerChoice | None = None, http_url: str | None = None,
                 headers: dict | None = None, call_timeout: float = 120, login_timeout: float = 600):
        self.stdio, self.http_url, self.headers = stdio, http_url, headers or {}
        self.call_timeout, self.login_timeout = call_timeout, login_timeout
        self._stack = None
        self.session = None
        self._first_call_done = False

    async def __aenter__(self):
        from contextlib import AsyncExitStack
        from mcp import ClientSession
        self._stack = AsyncExitStack()
        if self.stdio:
            from mcp.client.stdio import StdioServerParameters, stdio_client
            env = dict(os.environ)
            env.update(expand_vars(self.stdio.env, dict(os.environ)))
            env["LCP_TOOL_MODE"] = "readonly"  # siempre, aunque la configuracion diga full
            params = StdioServerParameters(command=expand_vars(self.stdio.command, env),
                                           args=expand_vars(self.stdio.args, env), env=env, cwd=self.stdio.cwd)
            read, write = await self._stack.enter_async_context(stdio_client(params, errlog=sys.stderr))
        else:
            from mcp.client.streamable_http import streamablehttp_client
            read, write, _ = await self._stack.enter_async_context(
                streamablehttp_client(self.http_url, headers=self.headers))
        self.session = await self._stack.enter_async_context(ClientSession(read, write))
        await asyncio.wait_for(self.session.initialize(), timeout=self.login_timeout)
        return self

    async def __aexit__(self, *exc):
        await self._stack.aclose()

    async def list_tools(self):
        tools, cursor = [], None
        while True:
            res = await asyncio.wait_for(self.session.list_tools(cursor=cursor) if cursor else self.session.list_tools(),
                                         timeout=self.login_timeout)
            tools.extend(res.tools)
            cursor = getattr(res, "nextCursor", None)
            if not cursor:
                return tools

    async def call(self, name: str, args: dict) -> CallResult:
        timeout = self.call_timeout if self._first_call_done else self.login_timeout
        t0 = time.monotonic()
        try:
            res = await self.session.call_tool(name, args, read_timeout_seconds=timedelta(seconds=timeout))
            ok, data, err = parse_result(res)
            self._first_call_done = True
            return CallResult(ok, data, err, 1, time.monotonic() - t0)
        except Exception as ex:  # timeouts, errores de transporte
            return CallResult(False, None, f"{type(ex).__name__}: {ex}"[:2000], 1, time.monotonic() - t0)


# --------------------------------------------------------------------------- analisis del catalogo

UUID_TOKENS = {"uuid", "guid"}
UUID_EXACT = {"id", "objectid", "identifier", "designobjectid"}


@dataclass
class ToolInfo:
    name: str
    description: str
    schema: dict
    annotations: dict | None
    toks: list[str]
    allowed: bool = False
    safety_reason: str = ""
    role: str = "other"
    scope: str = "manual"      # env | app | object | manual
    scope_reason: str = ""
    params: dict = field(default_factory=dict)   # nombre -> tipo de parametro
    types: list[str] = field(default_factory=list)  # tipos canonicos (alcance object); [] = generica
    generic: bool = False

    def to_json(self):
        return {"name": self.name, "description": self.description[:500], "allowed": self.allowed,
                "safetyReason": self.safety_reason, "scope": self.scope, "scopeReason": self.scope_reason,
                "role": self.role, "types": self.types, "generic": self.generic, "params": self.params,
                "inputSchema": self.schema, "annotations": self.annotations}


def ann_to_dict(ann):
    if ann is None:
        return None
    try:
        return {k: v for k, v in ann.model_dump().items() if v is not None}
    except Exception:
        return None


def classify_param(pname: str, pschema: dict, pag: dict, type_phrases: dict) -> str:
    pt = tokens(pname)
    low = pname.lower()
    is_uuid = bool(UUID_TOKENS.intersection(pt)) or low in UUID_EXACT
    if not is_uuid and len(pt) > 1 and pt[-1] == "id":
        before = pt[:-1]
        is_uuid = any(before[-len(ph):] == ph for phs in type_phrases.values() for ph in phs) or before[-1] in ("object", "design")
    if is_uuid:
        return "app_uuid" if ("app" in pt or "application" in pt) else "obj_uuid"
    if low in pag["offsetParams"]:
        return "offset"
    if low in pag["sizeParams"]:
        return "size"
    if low in pag["cursorParams"]:
        return "cursor"
    if low in pag["pageParams"]:
        return "page"
    if "type" in pt and isinstance(pschema, dict) and pschema.get("enum"):
        return "type_enum"
    return "other"


def match_types(toks: list[str], type_phrases: dict[str, list[list[str]]]) -> list[str]:
    best, score = [], 0
    tokset = set(toks)
    for t, phrases in type_phrases.items():
        s = max((len(p) for p in phrases if set(p) <= tokset), default=0)
        if s > score:
            best, score = [t], s
        elif s == score and s > 0:
            best.append(t)
    return best


def analyze_tool(tool, policy: Policy, trusted: bool, type_phrases: dict) -> ToolInfo:
    schema = tool.inputSchema or {}
    ti = ToolInfo(tool.name, tool.description or "", schema, ann_to_dict(tool.annotations), tokens(tool.name))
    ti.allowed, ti.safety_reason, exc_role = policy.safety(tool.name, tool.annotations, trusted)
    props = schema.get("properties") or {}
    required = list(schema.get("required") or [])
    ti.params = {p: classify_param(p, props.get(p, {}), policy.pag, type_phrases) for p in props}
    kinds = [ti.params.get(p, "other") for p in required]
    toks_set = set(ti.toks)
    others = [p for p in required if ti.params.get(p) == "other"]
    if others:
        ti.scope, ti.scope_reason = "manual", f"Requiere parametros que no se pueden deducir: {', '.join(others)}."
    elif kinds.count("obj_uuid") > 1 or kinds.count("app_uuid") > 1 or (kinds.count("obj_uuid") and kinds.count("app_uuid")):
        ti.scope, ti.scope_reason = "manual", "Requiere varios identificadores a la vez."
    elif kinds.count("obj_uuid") == 1:
        req_obj = next(p for p in required if ti.params[p] == "obj_uuid")
        own = match_types(ti.toks[1:] + tokens(req_obj), {k: v for k, v in type_phrases.items() if k != "application"})
        if ("application" in toks_set or "app" in toks_set) and not own:
            ti.scope, ti.scope_reason = "app", "Recibe el uuid de la aplicacion."
        else:
            ti.scope, ti.scope_reason = "object", f"Recibe el uuid de un objeto ('{req_obj}')."
            ti.types = own
            ti.generic = not own
    elif kinds.count("app_uuid") == 1:
        ti.scope, ti.scope_reason = "app", "Recibe el uuid de la aplicacion."
    elif "type_enum" in kinds:
        ti.scope, ti.scope_reason = "manual", "Requiere un tipo sin identificador de objeto."
    elif any(k == "app_uuid" for k in ti.params.values()):
        ti.scope, ti.scope_reason = "app", "Admite filtrar por aplicacion."
    else:
        ti.scope, ti.scope_reason = "env", "Sin parametros obligatorios: contexto del entorno."
    # rol
    if exc_role:
        ti.role = exc_role
    else:
        for role, rtoks in policy.roles:
            if rtoks.intersection(ti.toks):
                ti.role = role
                break
        else:
            if ti.scope == "object" and ti.toks and ti.toks[0] in policy.def_verbs:
                matched = set()
                for t in ti.types:
                    for ph in type_phrases.get(t, []):
                        if set(ph) <= toks_set:
                            matched |= set(ph)
                rest = [x for x in ti.toks[1:] if x not in matched and x not in policy.def_suffixes]
                if ti.types and not rest:
                    ti.role = "definition"
    return ti


# --------------------------------------------------------------------------- respuestas genericas

UUID_KEYS = ("uuid", "objectUuid", "designObjectUuid", "guid", "id", "objectId")
NAME_KEYS = ("name", "objectName", "displayName", "label", "title")
TYPE_KEYS = ("type", "objectType", "designObjectType", "typeName", "kind")


def pick(d: dict, keys) -> Any:
    for k in keys:
        v = d.get(k)
        if isinstance(v, str) and v:
            return v
    return None


def looks_uuid(v: Any) -> bool:
    return isinstance(v, str) and len(v) >= 8 and ("-" in v or "_" in v) and " " not in v


def harvest_items(data: Any, context: str | None = None, depth: int = 0):
    """Recorre una respuesta y devuelve (item, clave_de_lista) para elementos con uuid y nombre."""
    if depth > 8:
        return
    if isinstance(data, list):
        for it in data:
            if isinstance(it, dict):
                u, n = pick(it, UUID_KEYS), pick(it, NAME_KEYS)
                if looks_uuid(u) and n:
                    yield it, context
                    continue
            yield from harvest_items(it, context, depth + 1)
    elif isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, (list, dict)):
                yield from harvest_items(v, k, depth + 1)


def find_primary_list(data: Any, path=(), depth=0):
    """Devuelve (ruta, lista, dict_padre) de la lista mas larga (profundidad <= 4)."""
    best = (None, None, None)
    if depth > 4:
        return best
    if isinstance(data, list):
        return path, data, None
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, list):
                if best[1] is None or len(v) > len(best[1]):
                    best = (path + (k,), v, data)
            elif isinstance(v, dict):
                p, lst, parent = find_primary_list(v, path + (k,), depth + 1)
                if lst is not None and (best[1] is None or len(lst) > len(best[1])):
                    best = (p, lst, parent)
    return best


def find_key_ci(data: Any, keys: list[str], depth=0):
    if depth > 4 or not isinstance(data, dict):
        return None
    for k, v in data.items():
        if k.lower() in keys and v not in (None, "", []):
            return v
    for v in data.values():
        if isinstance(v, dict):
            r = find_key_ci(v, keys, depth + 1)
            if r is not None:
                return r
    return None


def set_path(data: Any, path: tuple, value: Any):
    if not path:
        return value
    cur = data
    for k in path[:-1]:
        cur = cur[k]
    cur[path[-1]] = value
    return data


# --------------------------------------------------------------------------- extractor

def error_de(ti: "ToolInfo", scope: str, obj: dict | None, error: str | None) -> dict:
    return {"tool": ti.name, "scope": scope, "object": (obj or {}).get("uuid"), "objectType": (obj or {}).get("type"),
            "error": error}


def extraccion_guardada(raw: Path) -> dict:
    """mcp_raw/_objects.json de la extracción que ya hay en esta carpeta ({} si no hay ninguna)."""
    try:
        d = json.loads((raw / "_objects.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return d if isinstance(d, dict) else {}


def aplicacion_extraida(raw: Path) -> dict:
    """La aplicación que ya está extraída en esta carpeta ({} si no hay ninguna)."""
    app = extraccion_guardada(raw).get("application")
    return app if isinstance(app, dict) else {}


def entorno(url: str) -> str:
    """LCP_URL sin la barra final: así se guarda y se compara el entorno de una extracción."""
    return (url or "").strip().rstrip("/")


class Extractor:
    def __init__(self, sess: McpSession, policy: Policy, out: Path | None, *, concurrency=4, refresh=False,
                 retries=2, retry_delay=1.5, only: str | None = None, skip: str | None = None,
                 retry_failed=False):
        self.sess, self.policy, self.out = sess, policy, out
        self.retry_failed = retry_failed
        self.sem = asyncio.Semaphore(max(1, concurrency))
        self.refresh, self.retries, self.retry_delay = refresh, retries, retry_delay
        self.only = re.compile(only) if only else None
        self.skip = re.compile(skip) if skip else None
        self.raw = (work_dir(out, crear=True) / "mcp_raw") if out else None
        self.stats = defaultdict(lambda: defaultdict(int))
        self.escritas: set[Path] = set()   # respuestas guardadas en esta ejecución
        self.anteriores = 0                # respuestas reutilizadas de una ejecución anterior
        self.mas_antigua = ""              # fetchedAt de la más antigua de ellas
        self.errors: list[dict] = []
        self.disabled: list[dict] = []
        self.tools: list[ToolInfo] = []
        self.trusted = False
        self.catalog = []

    # ---- catalogo
    async def load_catalog(self, type_phrases=None):
        self.catalog = await self.sess.list_tools()
        self.trusted = not any(self.policy.is_writeish(t.name, t.annotations) for t in self.catalog)
        self.classify(type_phrases or self.base_type_phrases())

    def base_type_phrases(self) -> dict:
        return {t: list(ps) for t, ps in self.policy.syn.items()}

    def classify(self, type_phrases: dict):
        self.tools = [analyze_tool(t, self.policy, self.trusted, type_phrases) for t in self.catalog]
        for ti in self.tools:
            if ti.allowed and self.only and not self.only.search(ti.name):
                ti.allowed, ti.safety_reason = False, "Excluida por --only."
            if ti.allowed and self.skip and self.skip.search(ti.name):
                ti.allowed, ti.safety_reason = False, "Excluida por --skip."

    def usable(self, scope: str) -> list[ToolInfo]:
        return [t for t in self.tools if t.allowed and t.scope == scope]

    # ---- llamadas
    def build_args(self, ti: ToolInfo, *, app_uuid=None, obj=None) -> dict | None:
        req = set((ti.schema.get("required") or []))
        args = {}
        for p, kind in ti.params.items():
            if kind == "app_uuid" and app_uuid:
                args[p] = app_uuid
            elif kind == "obj_uuid" and p in req:
                args[p] = obj["uuid"] if obj else app_uuid
            elif kind == "type_enum" and p in req:
                enum = (ti.schema.get("properties", {}).get(p) or {}).get("enum") or []
                mt = (obj or {}).get("mcpType")
                if mt in enum:
                    args[p] = mt
                else:
                    return None
        return args

    async def call_paginated(self, ti: ToolInfo, args: dict) -> CallResult:
        res = await self.call_with_retry(ti.name, args)
        if not res.ok or ti.role in self.policy.pag["noPaginateRoles"]:
            return res
        pag = self.policy.pag
        offset_p = next((p for p, k in ti.params.items() if k == "offset"), None)
        cursor_p = next((p for p, k in ti.params.items() if k == "cursor"), None)
        page_p = next((p for p, k in ti.params.items() if k == "page"), None)
        path, first_list, _ = find_primary_list(res.data)
        if first_list is None:
            return res
        collected = list(first_list)
        seen = {json.dumps(x, sort_keys=True, default=str) for x in collected}
        pages, page_no, last = 1, 1, res.data
        while pages < pag["maxPages"] and len(collected) < pag["maxItems"]:
            total = find_key_ci(last, pag["totalKeys"])
            cursor = find_key_ci(last, pag["cursorKeys"])
            nxt = None
            if cursor_p and isinstance(cursor, str) and cursor:
                nxt = {**args, cursor_p: cursor}
            elif offset_p and isinstance(total, (int, float)) and total > len(collected):
                nxt = {**args, offset_p: len(collected)}
            elif page_p and isinstance(total, (int, float)) and total > len(collected):
                page_no += 1
                nxt = {**args, page_p: page_no}
            if not nxt:
                break
            r2 = await self.call_with_retry(ti.name, nxt)
            if not r2.ok:
                break
            _, lst, _ = find_primary_list(r2.data)
            new = [x for x in (lst or []) if json.dumps(x, sort_keys=True, default=str) not in seen]
            if not new:
                break
            for x in new:
                seen.add(json.dumps(x, sort_keys=True, default=str))
            collected.extend(new)
            pages += 1
            last = r2.data
        if pages > 1:
            res.data = set_path(res.data, path, collected)
            res.pages = pages
        return res

    async def call_with_retry(self, name: str, args: dict) -> CallResult:
        res = CallResult(False, error="sin ejecutar")
        for attempt in range(self.retries + 1):
            async with self.sem:
                res = await self.sess.call(name, args)
            if res.ok:
                return res
            if not is_transient(res.error) or attempt == self.retries:
                return res
            await asyncio.sleep(self.retry_delay * (attempt + 1))
        return res

    def target_file(self, ti: ToolInfo, scope: str, obj: dict | None) -> Path | None:
        if not self.raw:
            return None
        if scope == "env":
            return self.raw / "_env" / f"{safe_name(ti.name)}.json"
        if scope == "app":
            return self.raw / "_app" / f"{safe_name(ti.name)}.json"
        return carpeta_objeto(self.raw, obj["type"], obj["uuid"]) / f"{safe_name(ti.name)}.json"

    async def run_call(self, ti: ToolInfo, scope: str, *, app_uuid=None, obj=None) -> CallResult:
        f = self.target_file(ti, scope, obj)
        if f and f.exists() and not self.refresh:
            try:
                cached = json.loads(f.read_text(encoding="utf-8"))
                meta = cached.get("_meta", {})
                if meta.get("ok"):
                    self.stats[ti.name]["cached"] += 1
                    self.reusada(f, meta)
                    return CallResult(True, cached.get("response"), None, meta.get("pages", 1))
                if not meta.get("transient", True) and not self.retry_failed:
                    self.stats[ti.name]["cachedFailed"] += 1
                    self.reusada(f, meta)
                    self.errors.append(error_de(ti, scope, obj, meta.get("error")))   # el informe, igual al retomar
                    return CallResult(False, None, meta.get("error"))
            except Exception:
                pass
        args = self.build_args(ti, app_uuid=app_uuid, obj=obj)
        if args is None:
            self.stats[ti.name]["notApplicable"] += 1
            return CallResult(False, error="No aplicable a este objeto.")
        res = await self.call_paginated(ti, args)
        self.stats[ti.name]["ok" if res.ok else "failed"] += 1
        if not res.ok:
            self.errors.append(error_de(ti, scope, obj, res.error))
        if f:
            self.guarda(f, ti, scope, obj, args, res)
        return res

    def reusada(self, f: Path, meta: dict) -> None:
        """Cuenta una respuesta guardada por otra ejecución y recuerda la fecha de la más antigua."""
        if f in self.escritas:
            return
        self.anteriores += 1
        fecha = str(meta.get("fetchedAt") or "")
        if fecha and (not self.mas_antigua or fecha < self.mas_antigua):
            self.mas_antigua = fecha

    def guarda(self, f: Path, ti: ToolInfo, scope: str, obj: dict | None, args: dict, res: CallResult) -> None:
        """Escribe la respuesta tal cual, con su _meta."""
        meta = {"tool": ti.name, "args": args, "scope": scope, "role": ti.role, "ok": res.ok,
                "error": res.error, "transient": bool(not res.ok and is_transient(res.error)),
                "pages": res.pages, "fetchedAt": now_iso(), "seconds": round(res.seconds, 2)}
        if obj:
            meta.update({"objectUuid": obj["uuid"], "objectName": obj.get("name"), "objectType": obj["type"],
                         "mcpType": obj.get("mcpType")})
        f.parent.mkdir(parents=True, exist_ok=True)
        self.escritas.add(f)
        f.write_text(json.dumps({"_meta": meta, "response": res.data}, ensure_ascii=False, indent=1, default=str),
                     encoding="utf-8")

    # ---- aplicaciones y objetos
    async def env_calls(self) -> dict[str, CallResult]:
        tools = self.usable("env")
        results = await asyncio.gather(*(self.run_call(t, "env") for t in tools))
        return {t.name: r for t, r in zip(tools, results)}

    async def list_apps(self) -> list[dict]:
        tools = [t for t in self.usable("env") if {"application", "app"}.intersection(t.toks)]
        results = await asyncio.gather(*(self.run_call(t, "env") for t in tools))
        apps: dict[str, dict] = {}
        for t, r in zip(tools, results):
            if not r.ok:
                continue
            for it, _ctx in harvest_items(r.data):
                u = pick(it, UUID_KEYS)
                apps.setdefault(u, {"uuid": u, "name": pick(it, NAME_KEYS), "prefix": it.get("prefix"),
                                    "source": t.name})
        return list(apps.values())

    async def app_calls(self, app_uuid: str) -> dict[str, CallResult]:
        tools = self.usable("app")
        results = await asyncio.gather(*(self.run_call(t, "app", app_uuid=app_uuid) for t in tools))
        return {t.name: r for t, r in zip(tools, results)}

    def harvest_objects(self, app_uuid: str, app_results: dict[str, CallResult]) -> tuple[dict, list[dict]]:
        objs: dict[str, dict] = {}
        app_obj = {"uuid": app_uuid, "type": "application", "mcpType": "APPLICATION", "name": None, "sources": []}
        skip_roles = {"members", "history", "versions", "dependents", "dependencies", "validation"}
        by_name = {t.name: t for t in self.tools}
        for tname, r in app_results.items():
            if not r.ok:
                continue
            ti = by_name.get(tname)
            if ti and ti.role in skip_roles:
                continue
            # la propia aplicacion
            stack = [r.data]
            while stack:
                d = stack.pop()
                if isinstance(d, dict):
                    if pick(d, UUID_KEYS) == app_uuid:
                        app_obj["name"] = app_obj["name"] or pick(d, NAME_KEYS)
                        for k in ("prefix", "description", "urlIdentifier"):
                            if d.get(k) and not app_obj.get(k):
                                app_obj[k] = d[k]
                    stack.extend(v for v in d.values() if isinstance(v, (dict, list)))
                elif isinstance(d, list):
                    stack.extend(d)
            tool_type = self.policy.canon_type(" ".join((ti.toks[1:] if ti else [])))
            for it, ctx in harvest_items(r.data):
                u = pick(it, UUID_KEYS)
                if u == app_uuid:
                    continue
                mcp_type = pick(it, TYPE_KEYS)
                ctype = self.policy.canon_type(mcp_type) or self.policy.canon_type(ctx) or tool_type or "unknown"
                cur = objs.get(u)
                if cur is None:
                    cur = objs[u] = {"uuid": u, "name": pick(it, NAME_KEYS), "type": ctype,
                                     "mcpType": mcp_type, "sources": []}
                else:
                    if mcp_type and not cur.get("mcpType"):
                        cur["mcpType"] = mcp_type
                    if cur["type"] == "unknown" and ctype != "unknown":
                        cur["type"] = ctype
                if tname not in cur["sources"]:
                    cur["sources"].append(tname)
        return app_obj, sorted(objs.values(), key=lambda o: (o["type"], o["name"] or ""))

    def type_phrases_for(self, objects: list[dict]) -> dict:
        tp = self.base_type_phrases()
        for o in objects + [{"type": "application", "mcpType": "APPLICATION"}]:
            t = o["type"]
            phrases = tp.setdefault(t, [])
            for src in (t, o.get("mcpType")):
                if src:
                    ph = tokens(src)
                    if ph and ph not in phrases:
                        phrases.append(ph)
        return tp

    def plan_object_calls(self, objects: list[dict]) -> list[tuple[ToolInfo, str, list[dict]]]:
        by_type = defaultdict(list)
        for o in objects:
            by_type[o["type"]].append(o)
        groups = []
        for ti in self.usable("object"):
            targets = ti.types if not ti.generic else [t for t in by_type if t not in self.policy.generic_skip]
            for t in targets:
                if by_type.get(t):
                    groups.append((ti, t, by_type[t]))
        return groups

    async def run_group(self, ti: ToolInfo, typ: str, objs: list[dict]):
        probe = objs[: self.policy.probe]
        rest = objs[self.policy.probe:]
        results = await asyncio.gather(*(self.run_call(ti, "object", obj=o) for o in probe))
        if probe and not any(r.ok for r in results):
            if rest:
                self.disabled.append({"tool": ti.name, "type": typ, "skippedCalls": len(rest),
                                      "reason": (results[0].error or "")[:300]})
                self.stats[ti.name]["disabled"] += len(rest)
            return
        await asyncio.gather(*(self.run_call(ti, "object", obj=o) for o in rest))


# --------------------------------------------------------------------------- flujo comun

def write_json(p: Path, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def resolve_app(apps: list[dict], wanted: str) -> tuple[dict | None, str]:
    w = wanted.strip().lower()
    for key in ("uuid", "prefix", "name"):
        hits = [a for a in apps if str(a.get(key) or "").lower() == w]
        if len(hits) == 1:
            return hits[0], ""
    hits = [a for a in apps if w in str(a.get("name") or "").lower()]
    if len(hits) == 1:
        return hits[0], ""
    if not hits:
        return None, f"No se encuentra la aplicacion '{wanted}'."
    return None, "Varias aplicaciones coinciden: " + "; ".join(f"{a['name']} ({a['uuid']})" for a in hits)


def catalog_json(ex: Extractor) -> dict:
    return {"generatedAt": now_iso(), "toolMode": "readonly", "trustedMode": ex.trusted, "toolCount": len(ex.tools),
            "tools": [t.to_json() for t in ex.tools]}


def plan_json(ex: Extractor, app: dict, objects: list[dict], groups) -> dict:
    counts = defaultdict(int)
    for o in objects:
        counts[o["type"]] += 1
    est = defaultdict(int)
    for ti, _t, objs in groups:
        est[ti.name] += len(objs)
    tools = []
    for t in ex.tools:
        entry = {"name": t.name, "use": t.allowed and t.scope != "manual", "scope": t.scope, "role": t.role,
                 "types": t.types if not t.generic else ["*"], "reason": t.safety_reason if not t.allowed else t.scope_reason}
        if t.allowed and t.scope == "object":
            entry["estimatedCalls"] = est.get(t.name, 0)
            if est.get(t.name, 0) == 0:
                entry["use"] = False
                entry["reason"] = "No hay objetos de los tipos a los que aplica."
        elif t.allowed and t.scope in ("env", "app"):
            entry["estimatedCalls"] = 1
        tools.append(entry)
    total = sum(e.get("estimatedCalls", 0) for e in tools if e["use"])
    return {"generatedAt": now_iso(), "app": app, "trustedMode": ex.trusted, "objectCount": len(objects),
            "objectsByType": dict(sorted(counts.items())), "estimatedCalls": total,
            "confirmAboveCalls": ex.policy.confirm_above, "needsConfirmation": total > ex.policy.confirm_above,
            "tools": sorted(tools, key=lambda e: (not e["use"], e["scope"], e["name"]))}


async def prepare(ex: Extractor, args) -> tuple[dict, list[dict], list]:
    """Catalogo -> app -> llamadas de app -> objetos -> reclasificacion con los tipos reales."""
    await ex.load_catalog()
    apps = await ex.list_apps()
    if not apps:
        raise SystemExit(EXIT_NO_APPS)
    app, msg = resolve_app(apps, args.app)
    if not app:
        eprint(msg)
        raise SystemExit(EXIT_APP)
    antes = aplicacion_extraida(ex.raw)
    if antes.get("uuid") not in (None, app["uuid"]):   # las respuestas guardadas serían las de la otra
        eprint(f"Esta carpeta ya tiene la extraccion de '{antes.get('name')}': para otra aplicacion, usa otra carpeta.")
        raise SystemExit(EXIT_APP)
    app_results = await ex.app_calls(app["uuid"])
    app_obj, objects = ex.harvest_objects(app["uuid"], app_results)
    app_obj["name"] = app_obj["name"] or app["name"]
    app_obj["prefix"] = app_obj.get("prefix") or app.get("prefix")
    ex.classify(ex.type_phrases_for(objects))
    # con la clasificacion final puede haber nuevas herramientas de app (p. ej. con tipos de la app)
    extra = [t for t in ex.usable("app") if t.name not in app_results]
    if extra:
        more = await asyncio.gather(*(ex.run_call(t, "app", app_uuid=app["uuid"]) for t in extra))
        app_results.update({t.name: r for t, r in zip(extra, more)})
        app_obj2, objects = ex.harvest_objects(app["uuid"], app_results)
        for k, v in app_obj2.items():
            app_obj.setdefault(k, v)
    groups = ex.plan_object_calls(objects)
    return app_obj, objects, groups


def open_session(args) -> tuple[McpSession | None, ServerChoice | None, int, str]:
    choice, code, msg = choose_devmcp(args)
    if not choice:
        return None, None, code, msg
    return McpSession(stdio=choice, call_timeout=args.call_timeout, login_timeout=args.login_timeout), choice, EXIT_OK, ""


def server_info(choice: ServerChoice) -> dict:
    env = expand_vars(choice.env, dict(os.environ))
    url = env.get("LCP_URL", "")
    return {"configFile": choice.source, "serverName": choice.name, "url": url,
            "authMethod": env.get("LCP_AUTH_METHOD", "browser"),
            "envKeys": sorted(env.keys()), "toolModeForced": "readonly"}


# --------------------------------------------------------------------------- subcomandos

async def cmd_apps(args) -> int:
    sess, choice, code, msg = open_session(args)
    if not sess:
        eprint(msg)
        return code
    try:
        async with sess:
            ex = Extractor(sess, Policy(args.policy), None)
            await ex.load_catalog()
            apps = await ex.list_apps()
    except SystemExit as se:
        return int(se.code)
    except Exception as ex_:
        eprint(f"No se pudo arrancar o autenticar el Dev MCP: {type(ex_).__name__}: {ex_}")
        return EXIT_START
    if args.json:
        print(json.dumps(apps, ensure_ascii=False, indent=2))
    else:
        for a in sorted(apps, key=lambda a: a["name"] or ""):
            print(f"{a.get('prefix') or '-':8} {a['name']}  [{a['uuid']}]")
    return EXIT_OK if apps else EXIT_NO_APPS


async def cmd_plan_or_extract(args, execute: bool) -> int:
    out = Path(args.out).resolve()
    sess, choice, code, msg = open_session(args)
    if not sess:
        eprint(msg)
        return code
    policy = Policy(args.policy)
    t0 = time.monotonic()
    inicio = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    try:
        async with sess:
            ex = Extractor(sess, policy, out, concurrency=args.concurrency, refresh=args.refresh,
                           retries=args.retries, retry_delay=args.retry_delay, only=args.only, skip=args.skip,
                           retry_failed=args.retry_failed)
            return await plan_o_extrae(ex, args, execute, choice, inicio, t0)
    except Exception as ex_:
        eprint(f"No se pudo arrancar o autenticar el Dev MCP: {type(ex_).__name__}: {ex_}")
        return EXIT_START


async def plan_o_extrae(ex: "Extractor", args, execute: bool, choice: "ServerChoice", inicio: str, t0: float) -> int:
    out, policy = ex.out, ex.policy
    url, antes = entorno(server_info(choice)["url"]), entorno(extraccion_guardada(ex.raw).get("entorno"))
    if url and antes and url.lower() != antes.lower() and not ex.refresh:   # misma app, mismo uuid, otro entorno
        eprint(f"Esta carpeta tiene la extraccion de {antes}: para {url}, usa otra carpeta o repite con --refresh.")
        return EXIT_APP
    try:
        app_obj, objects, groups = await prepare(ex, args)
    except SystemExit as se:
        return int(se.code)
    interm = work_dir(out, crear=True)
    write_json(interm / "mcp_catalog.json", catalog_json(ex))
    plan = plan_json(ex, app_obj, objects, groups)
    write_json(interm / "extraction_plan.json", plan)
    write_json(interm / "mcp_raw" / "_objects.json", {"application": app_obj, "entorno": url, "objects": objects})
    if not execute:
        print(json.dumps(plan, ensure_ascii=False, indent=1)) if args.json else print_plan(plan)
        return EXIT_OK
    if plan["needsConfirmation"] and not args.yes:
        print_plan(plan)
        eprint(f"\nEl plan supera {policy.confirm_above} llamadas. Repite con --yes para confirmar.")
        return EXIT_USAGE
    await ex.env_calls()
    await asyncio.gather(*(ex.run_group(ti, t, objs) for ti, t, objs in groups))
    report = {
        "startedAt": inicio,
        "durationSeconds": round(time.monotonic() - t0, 1),
        "server": server_info(choice), "trustedMode": ex.trusted,
        "app": app_obj, "objectCount": len(objects), "objectsByType": plan["objectsByType"],
        "toolsUsed": sorted({t.name for t in ex.tools if t.allowed and t.scope != "manual"}),
        "toolsExcluded": [{"name": t.name, "reason": t.safety_reason} for t in ex.tools if not t.allowed],
        "toolsManual": [{"name": t.name, "reason": t.scope_reason} for t in ex.tools
                        if t.allowed and t.scope == "manual"],
        "callStats": {k: dict(v) for k, v in sorted(ex.stats.items())},
        "callStatsByRole": por_rol(ex),
        "disabledAfterProbe": ex.disabled,
        "errors": ex.errors[:300], "errorCount": len(ex.errors),
    }
    write_json(interm / "extraction_report.json", report)
    (interm / "LEEME.md").write_text(
        "# Extracción\n\nRespuestas del Dev MCP de la aplicación, tal cual. Es la fuente de la documentación de la "
        "carpeta superior; para consultar un objeto, su ficha de `anexo/`.\n", encoding="utf-8")
    ok = sum(v.get("ok", 0) + v.get("cached", 0) for v in ex.stats.values())
    print(f"Extraccion terminada: {len(objects)} objetos, {ok} respuestas correctas, "
          f"{len(ex.errors)} errores, {len(ex.disabled)} herramientas desactivadas por tipo. "
          f"Informe: {interm / 'extraction_report.json'}")
    hace_una_hora = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(timespec="seconds")
    if ex.anteriores and ex.mas_antigua and ex.mas_antigua < hace_una_hora:   # lo de hace un rato (p. ej. plan) no avisa
        print(f"Reutilizadas {ex.anteriores} respuestas ya descargadas, la mas antigua del "
              f"{ex.mas_antigua[:16].replace('T', ' ')} (UTC): si la aplicacion ha cambiado desde entonces, "
              f"repite con --refresh.")
    return EXIT_OK


def por_rol(ex) -> dict:
    """Llamadas correctas y fallidas por rol (definition, dependents…): el umbral de la fase 2 se mira en definition."""
    rol = {t.name: t.role for t in ex.tools}
    out: dict[str, dict[str, int]] = {}
    for name, st in ex.stats.items():
        r = out.setdefault(rol.get(name) or "other", {"ok": 0, "failed": 0})
        r["ok"] += st.get("ok", 0) + st.get("cached", 0)
        r["failed"] += st.get("failed", 0) + st.get("cachedFailed", 0)
    return out


def print_plan(plan: dict):
    print(f"Aplicacion: {plan['app'].get('name')} [{plan['app'].get('uuid')}]")
    print(f"Objetos: {plan['objectCount']}  " + ", ".join(f"{k}={v}" for k, v in plan["objectsByType"].items()))
    print(f"Modo de confianza: {'si' if plan['trustedMode'] else 'no (estricto)'}")
    print(f"Llamadas estimadas: {plan['estimatedCalls']}")
    for t in plan["tools"]:
        mark = "USA " if t["use"] else "NO  "
        calls = f" ~{t['estimatedCalls']}" if t.get("estimatedCalls") and t["use"] else ""
        print(f"  {mark}{t['name']:40} {t['scope']:7} {t['role']:12}{calls}  {t['reason']}")


async def probe_http_server(url: str, headers: dict, timeout: float, policy: "Policy") -> dict:
    info = {"url": url, "reachable": False}
    try:
        async with McpSession(http_url=url, headers=headers, login_timeout=timeout, call_timeout=timeout) as s:
            tools = await s.list_tools()
            info.update({"reachable": True, "toolCount": len(tools), "tools": [t.name for t in tools]})
            tools = [t for t in tools if not policy.is_writeish(t.name, getattr(t, "annotations", None))]
            meta = next((t for t in tools if "metadata" in tokens(t.name)
                         and not (t.inputSchema or {}).get("required")), None)
            if meta:
                r = await s.call(meta.name, {})
                info["metadataCall"] = {"tool": meta.name, "ok": r.ok, "error": r.error}
                if r.ok:
                    info["recordTypesVisible"] = sum(1 for _ in harvest_items(r.data)) or len(
                        (find_primary_list(r.data)[1] or []))
    except Exception as ex_:
        info["error"] = f"{type(ex_).__name__}: {ex_}"[:500]
    return info


def http_candidates(args, predicate) -> list[tuple[Path, str, dict]]:
    return [e for e in server_entries(Path.cwd(), args.config or []) if is_http(e[2]) and predicate(e[2])]


def is_appian_mcp_server(entry: dict, host: str) -> bool:
    """El Appian MCP Server del entorno es <URL del entorno>/mcp: mismo host que el Dev MCP y ruta /mcp.
    Que la URL termine en /mcp no basta: muchos conectores ajenos a Appian también terminan así."""
    u = urlparse(str(entry.get("url", "")))
    return (u.hostname or "").lower() == host and u.path.rstrip("/") == "/mcp"


def env_host(args) -> str | None:
    """Host del entorno Appian según la configuración del Dev MCP (LCP_URL), sin arrancarlo."""
    choice, _code, _msg = choose_devmcp(args)
    url = server_info(choice).get("url") if choice else ""
    host = urlparse(url).hostname if url else None
    return host.lower() if host else None


def appian_mcp_candidates(args) -> tuple[list[tuple[Path, str, dict]], str]:
    """Solo el Appian MCP Server del mismo entorno que el Dev MCP, o el que se nombre con --mcp-server-name.
    Nunca otro servidor de la configuración."""
    http = [e for e in server_entries(Path.cwd(), args.config or []) if is_http(e[2])]
    if args.mcp_server_name:
        cands = [e for e in http if e[1] == args.mcp_server_name]
        return cands, ("" if cands else f"No hay ningun servidor http llamado '{args.mcp_server_name}' en la configuracion.")
    host = env_host(args)
    if not host:
        return [], ("Sin la configuracion del Dev MCP no se sabe cual es el entorno: "
                    "indica el Appian MCP Server con --mcp-server-name.")
    cands = [e for e in http if is_appian_mcp_server(e[2], host)]
    return cands, ("" if cands else f"No hay ningun servidor http 'https://{host}/mcp' en la configuracion. "
                                    "Sin el no habra metadatos ni recuentos del data fabric.")


async def cmd_doctor(args) -> int:
    report = {"checkedAt": now_iso(), "devMcp": {}, "appianMcpServer": {}, "docsMcp": {}}
    code = EXIT_OK
    # 1. Dev MCP
    choice, c, msg = choose_devmcp(args)
    if not choice:
        report["devMcp"] = {"status": "no_configurado" if c == EXIT_NO_CONFIG else "ambiguo", "detail": msg}
        code = c
    else:
        dev = {"status": "error", **server_info(choice)}
        try:
            async with McpSession(stdio=choice, call_timeout=args.call_timeout, login_timeout=args.login_timeout) as s:
                ex = Extractor(s, Policy(args.policy), None)
                await ex.load_catalog()
                apps = await ex.list_apps()
                dev.update({"status": "ok" if apps else "sin_apps", "toolCount": len(ex.tools),
                            "readTools": sum(1 for t in ex.tools if t.allowed),
                            "excludedTools": sum(1 for t in ex.tools if not t.allowed),
                            "trustedMode": ex.trusted, "appsVisible": len(apps),
                            "apps": [{"name": a["name"], "prefix": a.get("prefix"), "uuid": a["uuid"]} for a in apps][:50]})
                if len(apps) > 50:
                    dev["appsNote"] = f"Se muestran 50 de {len(apps)}: la lista completa, con 'apps --json'."
                if not ex.trusted:
                    dev["warning"] = ("El servidor expone herramientas de escritura aunque se pidio readonly. "
                                      "La politica las bloquea y solo se usan herramientas de lectura evidentes.")
                if not apps:
                    code = EXIT_NO_APPS
        except Exception as ex_:
            dev["detail"] = f"No arranca o no autentica: {type(ex_).__name__}: {ex_}"[:800]
            code = EXIT_START
        report["devMcp"] = dev
    # 2. Appian MCP Server (opcional)
    cands, why = appian_mcp_candidates(args)
    if not cands:
        report["appianMcpServer"] = {"status": "no_configurado", "detail": why}
    else:
        f, n, e = cands[0]
        headers = expand_vars(e.get("headers") or {}, dict(os.environ))
        info = await probe_http_server(e["url"], headers, min(args.login_timeout, 60), Policy(args.policy))
        info.update({"configFile": str(f), "serverName": n})
        info["status"] = "ok" if info.get("reachable") else "error"
        report["appianMcpServer"] = info
    # 3. Docs MCP (opcional; OAuth en el cliente)
    docs = http_candidates(args, is_docs_mcp)
    report["docsMcp"] = ({"status": "configurado", "configFile": str(docs[0][0]), "serverName": docs[0][1],
                          "url": docs[0][2].get("url"),
                          "detail": "Requiere OAuth en el cliente: la skill lo confirma con una consulta de prueba."}
                         if docs else
                         {"status": "no_detectado_en_ficheros",
                          "detail": "No aparece en los ficheros de configuracion. Puede estar anadido desde la interfaz "
                                    "del cliente: la skill lo comprueba desde la sesion."})
    if args.out:
        write_json(work_dir(args.out, crear=True) / "preflight.json", report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        d = report["devMcp"]
        print(f"Dev MCP ............ {d.get('status')}  {d.get('detail', '')}")
        if d.get("status") == "ok":
            print(f"   {d['toolCount']} herramientas ({d['readTools']} usables, {d['excludedTools']} excluidas), "
                  f"{d['appsVisible']} apps visibles, modo de confianza: {'si' if d['trustedMode'] else 'no'}")
        s = report["appianMcpServer"]
        print(f"Appian MCP Server .. {s.get('status')}  {s.get('detail', s.get('error', ''))}")
        dm = report["docsMcp"]
        print(f"Docs MCP ........... {dm.get('status')}  {dm.get('detail', '')}")
    return code


async def cmd_datafabric(args) -> int:
    out = Path(args.out).resolve()
    objs_file = work_dir(out) / "mcp_raw" / "_objects.json"
    if not objs_file.exists():
        eprint("Falta _objects.json: ejecuta antes 'extract'.")
        return EXIT_USAGE
    objs = json.loads(objs_file.read_text(encoding="utf-8"))
    rts = [o for o in objs["objects"] if o["type"] == "recordType"]
    cands, why = appian_mcp_candidates(args)
    if not cands:
        eprint(f"Appian MCP Server no configurado. {why}")
        return EXIT_NO_MCPSERVER
    f, n, e = cands[0]
    headers = expand_vars(e.get("headers") or {}, dict(os.environ))
    result = {"generatedAt": now_iso(), "server": {"configFile": str(f), "serverName": n, "url": e["url"]},
              "recordTypes": [], "unmatchedRecordTypes": []}
    try:
        async with McpSession(http_url=e["url"], headers=headers, login_timeout=60, call_timeout=60) as s:
            tools = await s.list_tools()
            pol = Policy(args.policy)
            tools = [t for t in tools if not pol.is_writeish(t.name, getattr(t, "annotations", None))]
            tools.sort(key=lambda t: not {"data", "fabric"} <= set(tokens(t.name)))   # las del data fabric, primero
            meta = next((t for t in tools if "metadata" in tokens(t.name)), None)
            sql = next((t for t in tools if {"sql", "query"} & set(tokens(t.name))
                        and any("query" in tokens(p) or "sql" in tokens(p)
                                for p in ((t.inputSchema or {}).get("required") or []))), None)
            if not meta:
                eprint("El Appian MCP Server no ofrece una herramienta de metadatos.")
                return EXIT_NO_MCPSERVER
            r = await s.call(meta.name, {})
            if not r.ok:
                eprint(f"Error en metadatos: {r.error}")
                return EXIT_NO_MCPSERVER
            _, lst, _ = find_primary_list(r.data)
            entries = [x for x in (lst or []) if isinstance(x, dict)]
            by_name = {str(pick(x, NAME_KEYS) or "").lower(): x for x in entries}
            by_uuid = {pick(x, UUID_KEYS): x for x in entries if pick(x, UUID_KEYS)}
            qparam = None
            if sql:
                qparam = next(p for p in (sql.inputSchema or {}).get("required") or []
                              if "query" in tokens(p) or "sql" in tokens(p))
            for rt in rts:
                m = by_uuid.get(rt["uuid"]) or by_name.get(str(rt["name"]).lower())
                if not m:
                    result["unmatchedRecordTypes"].append(rt["name"])
                    continue
                ref = next((v for k, v in m.items() if "sql" in k.lower() and isinstance(v, str)), None) \
                    or pick(m, ("tableName", "referenceName"))
                fields = next((v for k, v in m.items() if k.lower() == "fields" and isinstance(v, list)), [])
                rels = next((v for k, v in m.items() if "relationship" in k.lower() and isinstance(v, list)), [])
                item = {"name": rt["name"], "uuid": rt["uuid"], "sqlReference": ref, "fieldCount": len(fields),
                        "relationshipCount": len(rels), "count": None}
                if sql and qparam and ref and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", ref):
                    rq = await s.call(sql.name, {qparam: f"SELECT COUNT(*) AS total FROM {ref}"})
                    if rq.ok:
                        _, rows, _ = find_primary_list(rq.data)
                        val = None
                        if rows and isinstance(rows[0], dict):
                            val = next((v for v in rows[0].values() if isinstance(v, (int, float))), None)
                        item["count"] = val
                    else:
                        item["countError"] = rq.error
                elif not sql:
                    item["countError"] = "El servidor no ofrece consultas SQL."
                result["recordTypes"].append(item)
            result["metadataRaw"] = r.data
    except Exception as ex_:
        eprint(f"Appian MCP Server no disponible: {type(ex_).__name__}: {ex_}")
        return EXIT_NO_MCPSERVER
    write_json(work_dir(out, crear=True) / "datafabric.json", result)
    print(f"Data fabric: {len(result['recordTypes'])} record types con metadatos, "
          f"{sum(1 for x in result['recordTypes'] if x['count'] is not None)} con recuento.")
    return EXIT_OK


# --------------------------------------------------------------------------- CLI

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(sp):
        sp.add_argument("--server-name", help="Nombre del servidor en la configuracion MCP (si hay varios).")
        sp.add_argument("--config", action="append", help="Fichero de configuracion MCP adicional.")
        sp.add_argument("--bundle-dir", help="Carpeta del bundle del Dev MCP (alternativa a la configuracion).")
        sp.add_argument("--url", help="URL del entorno Appian (con --bundle-dir).")
        sp.add_argument("--policy", default=str(DEFAULT_POLICY))
        sp.add_argument("--call-timeout", type=float, default=120)
        sp.add_argument("--login-timeout", type=float, default=600,
                        help="Tiempo maximo para el primer acceso (puede abrir el navegador para SSO).")
        sp.add_argument("--mcp-server-name",
                        help="Nombre del Appian MCP Server en la configuracion, si no esta en <entorno>/mcp.")
        sp.add_argument("--json", action="store_true")

    sp = sub.add_parser("doctor")
    common(sp)
    sp.add_argument("--out")
    sp = sub.add_parser("apps")
    common(sp)
    for name in ("plan", "extract"):
        sp = sub.add_parser(name)
        common(sp)
        sp.add_argument("--app", required=True, help="uuid, prefijo o nombre de la aplicacion")
        sp.add_argument("--out", required=True, help="Carpeta de salida de la documentacion")
        sp.add_argument("--concurrency", type=int, default=4)
        sp.add_argument("--refresh", action="store_true", help="Lo pide todo otra vez: app cambiada u otro entorno")
        sp.add_argument("--retry-failed", action="store_true",
                        help="Reintenta tambien los fallos no transitorios de ejecuciones anteriores")
        sp.add_argument("--retries", type=int, default=2)
        sp.add_argument("--retry-delay", type=float, default=1.5)
        sp.add_argument("--only", help="Regex: usar solo herramientas cuyo nombre coincida")
        sp.add_argument("--skip", help="Regex: no usar herramientas cuyo nombre coincida")
        sp.add_argument("--yes", action="store_true", help="Confirma planes por encima del umbral de llamadas")
    sp = sub.add_parser("datafabric")
    common(sp)
    sp.add_argument("--out", required=True)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd == "doctor":
        return asyncio.run(cmd_doctor(args))
    if args.cmd == "apps":
        return asyncio.run(cmd_apps(args))
    if args.cmd in ("plan", "extract"):
        return asyncio.run(cmd_plan_or_extract(args, execute=args.cmd == "extract"))
    if args.cmd == "datafabric":
        return asyncio.run(cmd_datafabric(args))
    return EXIT_USAGE


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):  # consolas de Windows sin UTF-8: «→» o «✓» no caben en cp1252
        _s.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
