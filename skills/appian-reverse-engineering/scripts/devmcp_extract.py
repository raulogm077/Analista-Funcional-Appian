#!/usr/bin/env python3
"""devmcp_extract.py - Extrae una aplicacion Appian a disco a traves del Appian Dev MCP, en solo lectura.

No contiene nombres de herramientas: lee el catalogo del servidor en cada ejecucion, clasifica cada
herramienta por su firma y aplica la politica de scripts/devmcp_policy.json.

Ejecucion (uv instala el SDK MCP al vuelo; uv ya es requisito del Dev MCP):
  uv run --no-project --python ">=3.10" --with "mcp>=1.2,<2" python "<skill>/scripts/devmcp_extract.py" <subcomando> [opciones]
  (desde la carpeta del usuario, donde esta su .mcp.json; <skill> es la carpeta de la skill)

Subcomandos:
  doctor      Estado de los 3 MCP: Dev MCP (obligatorio), Appian MCP Server y Docs MCP (opcionales).
  apps        Lista las aplicaciones visibles para el usuario del Dev MCP.
  plan        Catalogo + clasificacion + objetos de la app + estimacion de llamadas. No llama por objeto.
  extract     Ejecuta el plan y vuelca las respuestas en <out>/extraccion/mcp_raw/, dentro del proyecto. Con
              --solo <objetos>, vuelve a pedir solo esos (y la lista de la aplicacion, para encontrar uno nuevo,
              que se guarda solo si alguno existe); de los demas usa lo guardado sin llamar al Dev MCP y sin sonda,
              y rehace el modelo (build_model.py). La fecha de la extraccion sigue siendo la de la completa
              (startedAt); la de la reextraccion va en reextraidoEn.
  datafabric  Metadatos y COUNT(*) por record type de la app a traves del Appian MCP Server.
  verificar   --app <app> [--objetos <nombres|@fichero>] [--esperado <fichero.json>] --out <fichero.json>: por objeto, si
              existe, su tipo, su nombre, su ultima modificacion (rol versions; un dato, no una prueba), los campos
              de record types y CDT y, si lo esperado las nombra, sus acciones de registro. Con --esperado, tambien
              sus diferencias con lo esperado (diferencias()); si lo esperado es el de una issue (su clave «_issue»,
              con su id y su version), el resultado lo lleva en «issue»: asi se sabe de que version de lo esperado es
              la verificacion. Y, si la issue no dice «pruebas»: false, en «pruebas» el resultado de los casos de
              prueba guardados de sus reglas e interfaces y de lo que las usa (los dependientes directos), sin las
              salidas de cada caso (pruebas_de()); con «pruebas»: false, solo lee lo que compara (solo_lo_esperado()).
              Por la salida, solo el resumen. No escribe en ninguna extraccion.
  regresion   --app <app> --out <fichero.json>: los casos de prueba de toda la aplicacion, objeto a objeto, con el
              resumen en el fichero y por la salida solo lo que falla. Se pasa antes de preparar el paquete.
  deriva      --out <as-is> [--objetos …] [--ignorar <nombre>@<fecha ISO>,…]: la lista de objetos de la aplicacion
              y su historial de versiones (rol versions), frente al as-is; cambiados, nuevos y retirados en
              <as-is>/datos/deriva.json. Sin historial en el Dev MCP, lo dice y no supone nada.

Las respuestas se guardan tal cual las devuelve el Dev MCP, con rutas cortas (Windows y OneDrive). verificar, regresion y
deriva no sacan el registro del servidor salvo con --registro (o si no arranca: entonces, sus ultimas lineas).

Codigos de salida (los mismos en todos los subcomandos):
  0 ok (verificar, tambien si falta algun objeto, no es lo esperado o falla una prueba: lo dice el JSON) | 1 regresion:
  algun caso falla | 2 uso incorrecto (deriva: sin as-is en --out) | 11 Dev MCP no configurado
  12 varias configuraciones posibles | 13 el Dev MCP no arranca o no autentica | 14 no hay aplicaciones visibles
  15 app no encontrada o ambigua, o la carpeta ya tiene otra app u otro entorno (usa otra --out;
     para la misma app de otro entorno, tambien --refresh; deriva: el as-is es de otro entorno)
  16 Appian MCP Server no disponible (solo datafabric) | 17 regresion: el Dev MCP no ofrece ejecutar casos de prueba
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
import tempfile
sys.dont_write_bytecode = True  # sin __pycache__ en el plugin: no se escribe fuera del proyecto
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rutas import carpeta_objeto, escribe, safe_name, work_dir  # noqa: E402
import build_model as bm  # noqa: E402  (el modelo, que rehace extract --solo, y cómo se leen las respuestas)

EXIT_OK, EXIT_USAGE, EXIT_NO_CONFIG, EXIT_AMBIGUOUS, EXIT_START, EXIT_NO_APPS, EXIT_APP, EXIT_NO_MCPSERVER = \
    0, 2, 11, 12, 13, 14, 15, 16
EXIT_FALLAN, EXIT_SIN_PRUEBAS = 1, 17

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


def terminal_auth_error(error: str | None) -> bool:
    """Errores de acceso o login, no pruebas de que un objeto falte. Formas del cliente HTTP y del login browser."""
    return bool(re.search(
        r"(?i)\bHTTP(?:/\d(?:\.\d)?)?\s*(?:status|error)?\s*[:=]?\s*[\"']?(?:401|403)\b"
        r"|\bstatus(?:_code| code)?\s*[:=]\s*(?:401|403)\b"
        r"|\b(?:401\s+unauthori[sz]ed|403\s+forbidden)\b"
        r"|\bTargetClosedError\b|Target page, context or browser has been closed"
        r"|Browser authentication timed out|Authentication failed: expected user"
        r"|Browser login appeared to succeed but no Appian session cookies",
        error or ""))


def is_transient(error: str | None) -> bool:
    return not terminal_auth_error(error) and bool(re.search(
        r"(?i)timeout|timed out|\b50[0-9]\b|temporar|connection|reset|unavailable|rate limit|429", error or ""))


class ExtractionInterrupted(RuntimeError):
    pass


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
        self.tool_types = d.get("objectToolTypes", {})
        self.pag = d["pagination"]
        self.probe = int(d["adaptiveDisable"]["probeCalls"])
        self.confirm_above = int(d["confirmAboveCalls"])
        casos = d.get("testCases") or {}
        self.run_verbs, self.test_tokens = set(casos.get("runVerbs", [])), set(casos.get("tokens", []))
        self.no_evaluable = [(x.get("type"), re.compile(x["pattern"]), x["reason"]) for x in casos.get("noEvaluable", [])]

    def runs_test_cases(self, name: str, ann) -> bool:
        """Si ejecuta casos de prueba guardados (testCases de la política): el servidor no la declara destructiva ni de
        escritura. La extracción no la usa; verificar y regresion, sí."""
        toks = tokens(name)
        return bool(self.run_verbs and toks and toks[0] in self.run_verbs and self.test_tokens <= set(toks)
                    and not (ann is not None and (getattr(ann, "destructiveHint", None) is True
                                                  or getattr(ann, "readOnlyHint", None) is False)))

    def is_writeish(self, name: str, ann) -> bool:
        toks = tokens(name)
        return bool((toks and toks[0] in self.write and not self.runs_test_cases(name, ann))
                    or self.interaction.intersection(toks)
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
        if self.runs_test_cases(name, ann):
            return False, ("Ejecuta casos de prueba guardados: evalua logica, y la extraccion no lo hace. La usan verificar "
                           "y regresion, en desarrollo."), "testRun"
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
        return False, (f"Verbo desconocido '{first}' y el catalogo trae herramientas de escritura (modo estricto: solo "
                       "las de lectura evidentes)."), None

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
    attempted: bool = True
    interrupted: bool = False


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
                 headers: dict | None = None, call_timeout: float = 120, login_timeout: float = 600, errlog=None):
        self.stdio, self.http_url, self.headers = stdio, http_url, headers or {}
        self.call_timeout, self.login_timeout = call_timeout, login_timeout
        self.errlog = errlog or sys.stderr   # a dónde va el registro del servidor (su salida de errores)
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
            # La documenta Appian, pero el Dev MCP 26.6.110 no la aplica (ofrece las mismas herramientas): no protege.
            # Lo que impide escribir es la política (devmcp_policy.json); se pide por si un Dev MCP la aplica
            env["LCP_TOOL_MODE"] = "readonly"
            params = StdioServerParameters(command=expand_vars(self.stdio.command, env),
                                           args=expand_vars(self.stdio.args, env), env=env, cwd=self.stdio.cwd)
            read, write = await self._stack.enter_async_context(stdio_client(params, errlog=self.errlog))
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
        own = policy.tool_types.get(ti.name) or match_types(
            ti.toks[1:] + tokens(req_obj), {k: v for k, v in type_phrases.items() if k != "application"})
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
    # rol (el de las que ejecutan casos de prueba, testRun, lo da la política)
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
                 retry_failed=False, solo=False):
        self.sess, self.policy, self.out = sess, policy, out
        self.retry_failed = retry_failed
        # --solo: uuids de los objetos que se vuelven a pedir (se rellena tras listar la aplicación); de los demás,
        # solo lo guardado, sin llamar al Dev MCP. None: extracción normal
        self.solo: set[str] | None = set() if solo else None
        # --solo: las respuestas de la aplicación se guardan cuando se sabe que algún objeto pedido existe
        self.aplazadas: list | None = [] if solo else None
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
        self.interruption: dict | None = None

    def check_interrupted(self):
        if self.interruption:
            raise ExtractionInterrupted(self.interruption["error"])

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
                if r2.interrupted:
                    res.ok, res.error, res.interrupted = False, r2.error, True
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
                # Se comprueba bajo el mismo semaforo que protege las llamadas: la cola no arranca tras el fallo.
                if self.interruption:
                    if attempt:
                        res.interrupted = True
                        return res   # ya hubo un intento; conservarlo, sin repetirlo
                    return CallResult(False, error=self.interruption["error"], attempted=False, interrupted=True)
                res = await self.sess.call(name, args)
                if not res.ok and terminal_auth_error(res.error):
                    res.interrupted = True
                    if self.interruption is None:
                        self.interruption = {"tool": name, "error": res.error, "at": now_iso()}
            if res.ok:
                return res
            if self.interruption:
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

    def refresca(self, scope: str, obj: dict | None) -> bool:
        """Si se pide otra vez aunque esté guardado: con --refresh, todo; con --solo, la lista de la aplicación (para
        encontrar un objeto nuevo) y los objetos de --solo."""
        return self.refresh or (self.solo is not None and (scope == "app" or (scope == "object"
                                                                              and obj["uuid"] in self.solo)))

    def fuera_de_solo(self, scope: str, obj: dict | None) -> bool:
        return self.solo is not None and scope == "object" and obj["uuid"] not in self.solo

    async def run_call(self, ti: ToolInfo, scope: str, *, app_uuid=None, obj=None) -> CallResult:
        f = self.target_file(ti, scope, obj)
        fuera = self.fuera_de_solo(scope, obj)
        if f and f.exists() and not self.refresca(scope, obj):
            try:
                cached = json.loads(f.read_text(encoding="utf-8"))
                meta = cached.get("_meta", {})
                if meta.get("ok"):
                    self.stats[ti.name]["cached"] += 1
                    self.reusada(f, meta)
                    return CallResult(True, cached.get("response"), None, meta.get("pages", 1))
                if ((not meta.get("transient", True) and not self.retry_failed
                     and not meta.get("interrupted") and not terminal_auth_error(meta.get("error"))) or fuera):
                    self.stats[ti.name]["cachedFailed"] += 1
                    self.reusada(f, meta)
                    self.errors.append(error_de(ti, scope, obj, meta.get("error")))   # el informe, igual al retomar
                    return CallResult(False, None, meta.get("error"))
            except Exception:
                pass
        if fuera:   # --solo: de los demás objetos no se llama al Dev MCP
            self.stats[ti.name]["notRequested"] += 1
            return CallResult(False, error="Fuera de --solo y sin respuesta guardada.")
        args = self.build_args(ti, app_uuid=app_uuid, obj=obj)
        if args is None:
            self.stats[ti.name]["notApplicable"] += 1
            return CallResult(False, error="No aplicable a este objeto.")
        res = await self.call_paginated(ti, args)
        if not res.attempted:
            self.stats[ti.name]["notAttempted"] += 1
            return res   # no cachear como fallo de objeto una llamada que no se hizo
        self.stats[ti.name]["ok" if res.ok else "failed"] += 1
        if not res.ok:
            self.errors.append(error_de(ti, scope, obj, res.error))
        if f and self.aplazadas is not None and scope == "app":
            self.aplazadas.append((f, ti, scope, obj, args, res))
        elif f:
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
        if res.interrupted:
            meta["interrupted"] = True
        if obj:
            meta.update({"objectUuid": obj["uuid"], "objectName": obj.get("name"), "objectType": obj["type"],
                         "mcpType": obj.get("mcpType")})
        f.parent.mkdir(parents=True, exist_ok=True)
        self.escritas.add(f)
        data = {"_meta": meta, "response": res.data}
        if res.interrupted and f.exists():
            try:
                anterior = json.loads(f.read_text(encoding="utf-8"))
                correcta = anterior if anterior.get("_meta", {}).get("ok") else anterior.get("previousSuccessfulResponse")
                if correcta:
                    data["previousSuccessfulResponse"] = correcta  # evidencia anterior, nunca respuesta actual
            except (OSError, ValueError):
                pass
        escribe(f, json.dumps(data, ensure_ascii=False, indent=1, default=str))

    # ---- aplicaciones y objetos
    async def env_calls(self) -> dict[str, CallResult]:
        tools = self.usable("env")
        results = await asyncio.gather(*(self.run_call(t, "env") for t in tools))
        return {t.name: r for t, r in zip(tools, results)}

    async def list_apps(self, de_una_vez: bool = False) -> list[dict]:
        tools = [t for t in self.usable("env") if {"application", "app"}.intersection(t.toks)]
        results = await asyncio.gather(*((self.entera(t) if de_una_vez else self.run_call(t, "env")) for t in tools))
        apps: dict[str, dict] = {}
        for t, r in zip(tools, results):
            if not r.ok:
                continue
            for it, _ctx in harvest_items(r.data):
                u = pick(it, UUID_KEYS)
                apps.setdefault(u, {"uuid": u, "name": pick(it, NAME_KEYS), "prefix": it.get("prefix"),
                                    "source": t.name})
        return list(apps.values())

    async def entera(self, ti: ToolInfo) -> CallResult:
        """Una lista del entorno, sin guardarla, en páginas tan grandes como admita el servidor (su parámetro de tamaño, a
        pagination.maxItems): las 482 aplicaciones del entorno de desarrollo, en una llamada y no en diez. Si no admite
        ese tamaño, en las suyas."""
        grande = {p: self.policy.pag["maxItems"] for p, k in ti.params.items() if k == "size"}
        res = await self.call_paginated(ti, grande) if grande else None
        return res if res is not None and res.ok else await self.run_call(ti, "env")

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
            # Una lista genérica no identifica el tipo de sus elementos: «application objects»
            # no es un tipo nuevo y no debe impedir que una lista específica lo resuelva después.
            tool_type = self.policy.canon_type(" ".join(ti.toks[1:])) if ti and "object" not in ti.toks else None
            for it, ctx in harvest_items(r.data):
                u = pick(it, UUID_KEYS)
                if u == app_uuid:
                    continue
                mcp_type = pick(it, TYPE_KEYS)
                # Una lista específica de objetos manda sobre `type`: en constantes es el tipo del valor.
                context_type = self.policy.phrase_to_type.get(" ".join(tokens(ctx or "")))
                listed_types = match_types(ti.toks[1:], {k: v for k, v in self.policy.syn.items()
                                                        if k != "application"}) if ti else []
                specific_type = listed_types[0] if len(listed_types) == 1 else None
                ctype = context_type or specific_type or self.policy.canon_type(mcp_type) or tool_type or "unknown"
                cur = objs.get(u)
                if cur is None:
                    cur = objs[u] = {"uuid": u, "name": pick(it, NAME_KEYS), "type": ctype,
                                     "mcpType": mcp_type, "sources": []}
                else:
                    if mcp_type and not cur.get("mcpType"):
                        cur["mcpType"] = mcp_type
                    if (cur["type"] == "unknown" and ctype != "unknown"
                            or cur["type"] not in self.policy.syn and ctype in self.policy.syn):
                        cur["type"] = ctype
                if tname not in cur["sources"]:
                    cur["sources"].append(tname)
        return app_obj, sorted(objs.values(), key=lambda o: (o["type"], o["name"] or ""))

    def type_phrases_for(self, objects: list[dict]) -> dict:
        tp = self.base_type_phrases()
        for o in objects + [{"type": "application", "mcpType": "APPLICATION"}]:
            t = o["type"]
            phrases = tp.setdefault(t, [])
            # El campo type de una constante describe su valor (GROUP, DOCUMENT, PROCESS_MODEL…).
            # Un alias contradictorio daría a TODAS las constantes las herramientas de esos tipos.
            mcp_type = o.get("mcpType")
            for src in (t, mcp_type if self.policy.canon_type(mcp_type) == t else None):
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
        if self.solo is not None:   # --solo: lo guardado de los demás se lee sin sonda; la sonda, solo con los pedidos
            await asyncio.gather(*(self.run_call(ti, "object", obj=o) for o in objs
                                   if o["uuid"] not in self.solo and self.target_file(ti, "object", o).exists()))
            objs = [o for o in objs if o["uuid"] in self.solo]
        probe = objs[: self.policy.probe]
        rest = objs[self.policy.probe:]
        results = await asyncio.gather(*(self.run_call(ti, "object", obj=o) for o in probe))
        if self.interruption:
            return   # no confundir autenticacion interrumpida con tipo no admitido por la herramienta
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
    escribe(p, json.dumps(data, ensure_ascii=False, indent=2, default=str))


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


def plan_json(ex: Extractor, app: dict, objects: list[dict], groups, inicio: str | None = None) -> dict:
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
    return {"generatedAt": now_iso(), "startedAt": inicio, "app": app, "trustedMode": ex.trusted,
            "objectCount": len(objects),
            "objectsByType": dict(sorted(counts.items())), "estimatedCalls": total,
            "confirmAboveCalls": ex.policy.confirm_above, "needsConfirmation": total > ex.policy.confirm_above,
            "tools": sorted(tools, key=lambda e: (not e["use"], e["scope"], e["name"]))}


async def aplicacion_de(ex: Extractor, args, de_una_vez: bool = False) -> dict:
    """Catalogo -> la aplicacion de --app, entre las del entorno (con `de_una_vez`, en una sola pagina si se puede)."""
    await ex.load_catalog()
    apps = await ex.list_apps(de_una_vez)
    ex.check_interrupted()
    if not apps:
        excluded = [f"{t.name}: {t.safety_reason}" for t in ex.tools
                    if t.scope == "env" and {"application", "app"}.intersection(t.toks) and not t.allowed]
        eprint("No se obtuvo la lista de aplicaciones." + (" " + "; ".join(excluded) if excluded else
               " Comprueba las respuestas de la lista, la conexión y los permisos del usuario."))
        raise SystemExit(EXIT_NO_APPS)
    app, msg = resolve_app(apps, args.app)
    if not app:
        eprint(msg)
        raise SystemExit(EXIT_APP)
    antes = aplicacion_extraida(ex.raw) if ex.raw else {}   # verificar y deriva no escriben: sin carpeta
    if antes.get("uuid") not in (None, app["uuid"]):   # las respuestas guardadas serían las de la otra
        eprint(f"Esta carpeta ya tiene la extraccion de '{antes.get('name')}': para otra aplicacion, usa otra carpeta.")
        raise SystemExit(EXIT_APP)
    return app


async def prepare(ex: Extractor, args, app: dict | None = None) -> tuple[dict, list[dict], list]:
    """Catalogo -> app -> llamadas de app -> objetos -> reclasificacion con los tipos reales. Con `app` (el catalogo ya
    cargado y la aplicacion resuelta), desde las llamadas de app."""
    app = app or await aplicacion_de(ex, args)
    app_results = await ex.app_calls(app["uuid"])
    ex.check_interrupted()
    app_obj, objects = ex.harvest_objects(app["uuid"], app_results)
    app_obj["name"] = app_obj["name"] or app["name"]
    app_obj["prefix"] = app_obj.get("prefix") or app.get("prefix")
    ex.classify(ex.type_phrases_for(objects))
    # con la clasificacion final puede haber nuevas herramientas de app (p. ej. con tipos de la app)
    extra = [t for t in ex.usable("app") if t.name not in app_results]
    if extra:
        more = await asyncio.gather(*(ex.run_call(t, "app", app_uuid=app["uuid"]) for t in extra))
        ex.check_interrupted()
        app_results.update({t.name: r for t, r in zip(extra, more)})
        app_obj2, objects = ex.harvest_objects(app["uuid"], app_results)
        for k, v in app_obj2.items():
            app_obj.setdefault(k, v)
    groups = ex.plan_object_calls(objects)
    return app_obj, objects, groups


async def solo_lo_esperado(ex: Extractor, args, tipos: dict[str, str], auxiliares=()) -> tuple[dict, list[dict]]:
    """Para verificar una issue sin pruebas, la aplicacion y sus objetos leyendo solo lo necesario: las aplicaciones de una
    vez y, de la aplicacion, solo las listas de los tipos esperados ({pedido: tipo canonico}; en el Dev MCP real, la de
    record types en vez de 25 listas). Si un pedido no esta en ellas (es de otro tipo o no existe), la lista entera, como
    prepare(): «falta» y un «tipo» distinto salen igual."""
    app = await aplicacion_de(ex, args, de_una_vez=True)
    sin_app = {t: ps for t, ps in ex.base_type_phrases().items() if t != "application"}
    listas = [t for t in ex.usable("app") if t.role == "other"
              and set(match_types(t.toks[1:], sin_app) or ["?"]) <= set(tipos.values()) | set(auxiliares)]
    res = await asyncio.gather(*(ex.run_call(t, "app", app_uuid=app["uuid"]) for t in listas))
    ex.check_interrupted()
    app_obj, objects = ex.harvest_objects(app["uuid"], {t.name: r for t, r in zip(listas, res)})
    por = resolver(list(tipos), objects)
    if len(por) < len(tipos) or any(o["type"] != tipos[p] for p, o in por.items()):
        app_obj, objects, _ = await prepare(ex, args, app)
        return app_obj, objects
    app_obj["name"], app_obj["prefix"] = app_obj["name"] or app["name"], app_obj.get("prefix") or app.get("prefix")
    ex.classify(ex.type_phrases_for(objects))
    return app_obj, objects


def open_session(args, errlog=None) -> tuple[McpSession | None, ServerChoice | None, int, str]:
    choice, code, msg = choose_devmcp(args)
    if not choice:
        return None, None, code, msg
    return McpSession(stdio=choice, call_timeout=args.call_timeout, login_timeout=args.login_timeout,
                      errlog=errlog), choice, EXIT_OK, ""


class Registro:
    """El registro del servidor (lo que escribe en su salida de errores; de 78 a 331 KB por objeto en el Dev MCP real):
    con --registro, a la salida de errores; si no, a un fichero temporal que se borra, del que solo se enseñan las
    últimas líneas si el servidor no arranca."""

    def __init__(self, ver: bool):
        self.f = None if ver else tempfile.TemporaryFile("w+b")

    def __enter__(self):
        return self

    def __exit__(self, *_):
        if self.f:
            self.f.close()

    @property
    def destino(self):
        return self.f or sys.stderr

    def cola(self, n: int = 12) -> str:
        if not self.f:
            return ""
        try:
            self.f.flush()
            self.f.seek(0)
            lineas = self.f.read().decode("utf-8", errors="replace").splitlines()
        except (OSError, ValueError):
            return ""
        return "\n".join(lineas[-n:])

    def no_arranca(self, ex_: Exception) -> int:
        cola = self.cola()
        eprint(f"No se pudo arrancar o autenticar el Dev MCP: {type(ex_).__name__}: {ex_}"
               + (f"\nUltimas lineas de su registro (todo, con --registro):\n{cola}" if cola else ""))
        return EXIT_START


def server_info(choice: ServerChoice) -> dict:
    env = expand_vars(choice.env, dict(os.environ))
    url = env.get("LCP_URL", "")
    return {"configFile": choice.source, "serverName": choice.name, "url": url,
            "authMethod": env.get("LCP_AUTH_METHOD", "browser"),
            "envKeys": sorted(env.keys()), "toolModeForced": "readonly"}


def interrupcion_de_lectura(destino: Path, ex: Extractor) -> int:
    """Conserva el resultado anterior y marca que la nueva lectura no permite compararlo."""
    marca = destino.with_name(destino.stem + ".interrumpido" + destino.suffix)
    write_json(marca, {"status": "partial", "generatedAt": now_iso(), "interruption": ex.interruption,
                       "previousResult": str(destino), "previousResultIsCurrent": False})
    eprint(f"Lectura interrumpida: {ex.interruption['error']}. No se deducen objetos ausentes ni retirados. "
           f"El resultado anterior se conserva, pero no es el de esta lectura. Detalle: {marca}")
    return EXIT_START


def supera_interrupcion(marca: Path):
    """Una lectura completa posterior deja constancia de que el marcador parcial ya no manda."""
    if marca.exists():
        try:
            previo = json.loads(marca.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        write_json(marca, {**previo, "status": "superseded", "supersededAt": now_iso()})


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
    solo = getattr(args, "solo", None)
    if solo and args.refresh:
        eprint("--solo y --refresh no van juntos: --solo vuelve a pedir solo esos objetos.")
        return EXIT_USAGE
    if solo and not (work_dir(out) / "mcp_raw" / "_objects.json").exists():
        eprint("--solo reextrae objetos de una extraccion que ya esta en la carpeta: haz antes extract sin --solo.")
        return EXIT_USAGE
    try:
        args.solo_pedidos = lista_de_objetos(solo)
    except OSError as ex_:
        eprint(f"No se puede leer {solo}: {ex_}")
        return EXIT_USAGE
    if solo and not args.solo_pedidos:
        eprint("--solo no trae ningun objeto.")
        return EXIT_USAGE
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
                           retry_failed=args.retry_failed, solo=bool(solo))
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
    except ExtractionInterrupted:
        # La lista puede estar incompleta: no reemplazar _objects ni deducir objetos ausentes.
        report = {"status": "partial", "startedAt": inicio, "durationSeconds": round(time.monotonic() - t0, 1),
                  "interruption": ex.interruption, "objectListComplete": False,
                  "toolsUsed": usadas(ex), "callStats": {k: dict(v) for k, v in sorted(ex.stats.items())}}
        destino = work_dir(out, crear=True) / "extraction_interrupted.json"
        write_json(destino, report)
        eprint(f"Extraccion interrumpida al listar: {ex.interruption['error']}. No se deducen objetos ausentes. "
               f"Respuestas conservadas; detalle: {destino}")
        return EXIT_START
    except SystemExit as se:
        return int(se.code)
    if ex.solo is not None:
        pedidos = args.solo_pedidos
        por = resolver(pedidos, objects)
        if len(por) < len(pedidos):
            eprint("--solo: no estan en la aplicacion: " + ", ".join(p for p in pedidos if p not in por))
        if not por:   # sin ninguno, la extraccion se queda como estaba: no se guarda ni la lista de la aplicacion
            return EXIT_USAGE
        ex.solo.update(o["uuid"] for o in por.values())
        for aplazada in ex.aplazadas:
            ex.guarda(*aplazada)
        ex.aplazadas = None
    interm = work_dir(out, crear=True)
    write_json(interm / "mcp_catalog.json", catalog_json(ex))
    anterior = inicio_anterior(interm / "extraction_plan.json")   # antes de sobrescribirlo
    plan = plan_json(ex, app_obj, objects, groups, inicio)
    write_json(interm / "extraction_plan.json", plan)
    write_json(interm / "mcp_raw" / "_objects.json", {"application": app_obj, "entorno": url, "objects": objects})
    if not execute:
        print(json.dumps(plan, ensure_ascii=False, indent=1)) if args.json else print_plan(plan)
        return EXIT_OK
    if plan["needsConfirmation"] and not args.yes and ex.solo is None:   # --solo pide solo unos objetos
        print_plan(plan)
        eprint(f"\nEl plan supera {policy.confirm_above} llamadas. Repite con --yes para confirmar.")
        return EXIT_USAGE
    await ex.env_calls()
    await asyncio.gather(*(ex.run_group(ti, t, objs) for ti, t, objs in groups))
    report = {
        "status": "partial" if ex.interruption else "complete",
        "startedAt": inicio,
        "durationSeconds": round(time.monotonic() - t0, 1),
        "server": server_info(choice), "trustedMode": ex.trusted,
        "app": app_obj, "objectCount": len(objects), "objectsByType": plan["objectsByType"],
        "toolsUsed": usadas(ex),
        "toolsOmitted": omitidas(ex, plan),
        "toolsExcluded": [{"name": t.name, "reason": t.safety_reason} for t in ex.tools if not t.allowed],
        "toolsManual": [{"name": t.name, "reason": t.scope_reason} for t in ex.tools
                        if t.allowed and t.scope == "manual"],
        "callStats": {k: dict(v) for k, v in sorted(ex.stats.items())},
        "callStatsByRole": por_rol(ex),
        "disabledAfterProbe": ex.disabled,
        "errors": ex.errors[:300], "errorCount": len(ex.errors),
    }
    if ex.interruption:
        report.update(interruption=ex.interruption, objectListComplete=True)
    if ex.solo is not None:
        report["solo"] = sorted(o.get("name") or o["uuid"] for o in objects if o["uuid"] in ex.solo)
        try:   # lo desactivado en la extracción completa sigue valiendo para los objetos que no se piden
            previo = json.loads((interm / "extraction_report.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            previo = {}
        vistos = {(d.get("tool"), d.get("type")) for d in ex.disabled}
        report["disabledAfterProbe"] = ex.disabled + [d for d in previo.get("disabledAfterProbe") or []
                                                      if (d.get("tool"), d.get("type")) not in vistos]
        # la fecha de la extracción (extractedAt del inventario, asIs de la deriva) es la de la completa
        report = {"startedAt": previo.get("startedAt") or inicio, "reextraidoEn": inicio,
                  **{k: v for k, v in report.items() if k != "startedAt"}}
    write_json(interm / "extraction_report.json", report)
    if ex.interruption:
        eprint(f"Extraccion parcial, interrumpida por acceso o login: {ex.interruption['error']}. "
               f"No se lanzan llamadas nuevas; las ya iniciadas pueden haber terminado. "
               f"Respuestas conservadas; informe: {interm / 'extraction_report.json'}")
        return EXIT_START
    supera_interrupcion(interm / "extraction_interrupted.json")
    escribe(interm / "LEEME.md",
            "# Extracción\n\nRespuestas del Dev MCP de la aplicación, tal cual. Es la fuente de la documentación de la "
            "carpeta superior; para consultar un objeto, su ficha de `anexo/`.\n")
    ok = sum(v.get("ok", 0) + v.get("cached", 0) for v in ex.stats.values())
    print(f"Extraccion terminada: {len(objects)} objetos, {ok} respuestas correctas, "
          f"{len(ex.errors)} errores, {len(ex.disabled)} herramientas desactivadas por tipo. "
          f"Informe: {interm / 'extraction_report.json'}")
    if ex.solo is not None:   # el resto es lo guardado a propósito: si cambió, lo dice la deriva
        print(f"Reextraidos {len(report['solo'])}: {', '.join(report['solo'])}. Los demas, de lo guardado. Modelo:")
        return bm.main(str(out))
    # lo que descargó la ejecución anterior (p. ej. el plan, aunque fuera hace horas) no avisa; lo de antes, sí
    if ex.anteriores and ex.mas_antigua and (not anterior or ex.mas_antigua < anterior):
        print(f"Reutilizadas {ex.anteriores} respuestas ya descargadas, la mas antigua del "
              f"{ex.mas_antigua[:16].replace('T', ' ')} (UTC): si la aplicacion ha cambiado desde entonces, "
              f"repite con --refresh.")
    return EXIT_OK


def inicio_anterior(plan: Path) -> str:
    """Cuándo empezó la ejecución anterior (plan o extract): startedAt de su extraction_plan.json; en un plan de antes
    de 0.7.0-beta.2, su generatedAt. "" si no hay plan."""
    try:
        d = json.loads(plan.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ""
    return str((d.get("startedAt") or d.get("generatedAt") or "") if isinstance(d, dict) else "")



def usadas(ex) -> list[str]:
    """Las herramientas con alguna llamada en esta ejecución: correcta, reutilizada o fallida. Las demás del catálogo,
    con su motivo, son las omitidas (omitidas())."""
    return sorted(n for n, st in ex.stats.items() if any(st.get(k) for k in bm.LLAMADAS))


def omitidas(ex, plan: dict) -> list[dict]:
    """Las herramientas del catálogo sin ninguna llamada, cada una con su motivo: el del plan si no la usaba (use: false)
    o, si la usaba, por qué no hubo llamada (con --solo, de objetos no pedidos sin respuesta guardada; o no aplicaba a
    ninguno de sus objetos). Usadas más omitidas son el catálogo, también con --solo."""
    usa = set(usadas(ex))
    del_plan = {t["name"]: t["reason"] for t in plan.get("tools", []) if not t.get("use")}
    out = []
    for t in sorted(ex.tools, key=lambda t: t.name):
        if t.name in usa:
            continue
        st = ex.stats.get(t.name, {})
        if t.name in del_plan:
            motivo = del_plan[t.name]
        elif st.get("notRequested"):
            motivo = "Con --solo, solo para objetos no pedidos y sin respuesta guardada."
        elif st.get("notApplicable"):
            motivo = "No aplicaba a ninguno de los objetos de sus tipos."
        else:
            motivo = "Sin llamadas en esta extracción."
        out.append({"name": t.name, "reason": motivo})
    return out


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
    print(f"Modo de confianza: {'si' if plan['trustedMode'] else 'no (estricto: el catalogo trae herramientas de escritura)'}")
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
                if not ex.trusted:   # el Dev MCP 26.6.110 no aplica LCP_TOOL_MODE=readonly: es lo normal
                    dev["warning"] = ("El servidor ofrece herramientas de escritura (LCP_TOOL_MODE=readonly no las "
                                      "quita). La politica no las usa: solo las de lectura evidentes.")
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
    except Exception as ex_:
        eprint(f"Appian MCP Server no disponible: {type(ex_).__name__}: {ex_}")
        return EXIT_NO_MCPSERVER
    write_json(work_dir(out, crear=True) / "datafabric.json", result)
    print(f"Data fabric: {len(result['recordTypes'])} record types con metadatos, "
          f"{sum(1 for x in result['recordTypes'] if x['count'] is not None)} con recuento.")
    return EXIT_OK


# --------------------------------------------------------------------------- verificar y deriva (atajo, solo lectura)

def lista_de_objetos(valor: str | None) -> list[str]:
    """Los objetos de --objetos, --solo o --ignorar: separados por comas, o @fichero con uno por línea (sin las líneas
    vacías ni las que empiezan por #). OSError si no se puede leer el fichero."""
    if not valor:
        return []
    if valor.startswith("@"):
        partes = [x for x in Path(valor[1:]).read_text(encoding="utf-8-sig").splitlines()   # con o sin BOM
                  if not x.strip().startswith("#")]
    else:
        partes = valor.split(",")
    return list(dict.fromkeys(x.strip() for x in partes if x.strip()))


def resolver(pedidos: list[str], objects: list[dict]) -> dict[str, dict]:
    """{pedido: objeto} de los pedidos que están en `objects`: por uuid, por nombre o por nombre sin mayúsculas."""
    por_uuid = {o["uuid"]: o for o in objects}
    por_nombre: dict[str, dict] = {}
    por_minusculas: dict[str, dict] = {}
    for o in objects:
        por_nombre.setdefault(str(o.get("name") or ""), o)
        por_minusculas.setdefault(str(o.get("name") or "").lower(), o)
    out = {}
    for p in pedidos:
        o = por_uuid.get(p) or por_nombre.get(p) or por_minusculas.get(p.lower())
        if o:
            out[p] = o
    return out


def aplica(ex: Extractor, ti: ToolInfo, o: dict) -> bool:
    return o["type"] in ti.types or (ti.generic and o["type"] not in ex.policy.generic_skip)


async def llama(ex: Extractor, tools: list[ToolInfo], o: dict) -> tuple[list, list[str]]:
    """Las respuestas correctas de las herramientas `tools` que se aplican a `o`, y los errores de las demás."""
    usar = [t for t in tools if aplica(ex, t, o)]
    res = await asyncio.gather(*(ex.run_call(t, "object", obj=o) for t in usar))
    return [r.data for r in res if r.ok], [f"{t.name}: {(r.error or '')[:200]}" for t, r in zip(usar, res) if not r.ok]


def version(data) -> dict | None:
    """La última versión de una respuesta de historial: {fecha, autor, versiones}."""
    v = bm.ultima_version(data)
    return {"fecha": v["lastModifiedOn"], "autor": v["lastModifiedBy"], "versiones": v["count"]} if v else None


def campos(data) -> list[dict]:
    """Los campos de la definición de un record type o un CDT: nombre, tipo y, si los trae, longitud y clave."""
    out = []
    for c in bm.find_list(bm.unwrap(data), ("fields",)):
        if not isinstance(c, dict):
            continue
        f = {"nombre": bm.pick(c, ("fieldName", "name", "objectName")),
             "tipo": bm.pick(c, ("fieldType", "type", "dataType", "typeName", "objectType"))}
        largo = bm.pick(c, ("length", "maxLength"), want=int)
        if largo is not None:
            f["longitud"] = largo
        if any(c.get(k) is True for k in ("isPrimaryKey", "primaryKey")):
            f["clavePrimaria"] = True
        out.append(f)
    return out


NOMBRE_ACCION, TIPO_ACCION = ("displayName", "name", "label", "title"), ("actionType", "type", "kind")


def acciones(data) -> list[dict]:
    """Las acciones de registro de una respuesta (la lista de acciones de un record type, o su definición si las trae):
    su nombre y su tipo, como los dé el Dev MCP (LIST_ACTION, RELATED_ACTION)."""
    d = bm.unwrap(data)
    lista = d if isinstance(d, list) else bm.find_list(d, ("actions", "recordActions", "recordTypeActions"))
    return [{"nombre": bm.pick(a, NOMBRE_ACCION), "tipo": bm.pick(a, TIPO_ACCION),
             **{k: a[k] for k in ("securityMode", "visibilityExpr", "securityRule") if k in a}} for a in lista
            if isinstance(a, dict) and bm.pick(a, NOMBRE_ACCION)]


ROLES_PROCESO = {"administrator", "editor", "manager", "viewer", "initiator", "deny"}
MIEMBRO_GRUPO = r"a!isUserMemberOfGroup\((?:fn!)?loggedInUser\(\),cons![A-Za-z_][A-Za-z_0-9]*\)"


def expresion_visible(texto):
    """Contrato de configuración literal acotado. No ejecuta SAIL ni afirma acceso efectivo."""
    if not isinstance(texto, str):
        return None
    valor = re.sub(r"\s*([!(),=])\s*", r"\1", texto.strip()).removeprefix("=")
    literal = re.fullmatch(r"(?:fn!)?(true|false)\(\)", valor)
    if literal:
        return {"literal": literal[1] == "true"}
    patron = rf"(?:{MIEMBRO_GRUPO}|(?:fn!)?or\({MIEMBRO_GRUPO}(?:,{MIEMBRO_GRUPO})+\))"
    if re.fullmatch(patron, valor):
        return {"constantes": sorted(set(re.findall(r"cons!([A-Za-z_][A-Za-z_0-9]*)", valor)))}
    return None


def diferencias_permisos(o, esperado):
    """Diferencias de configuración confirmadas y lo que no se puede comparar, por separado."""
    distintos, desconocidos = [], []
    if "permisosInicio" in esperado or tipo_de_objeto(esperado.get("tipo")) == "processmodel":
        pedidos = esperado.get("permisosInicio")
        if not isinstance(pedidos, list) or not pedidos:
            desconocidos.append("inicio: falta contrato explícito de roles y grupos en técnico §4")
        else:
            if {p.get("rol") for p in pedidos if isinstance(p, dict) and isinstance(p.get("rol"), str)} != ROLES_PROCESO:
                desconocidos.append("inicio: contrato parcial; los roles no declarados no se han comparado")
            seguridad = o.get("seguridadInicio")
            roles = seguridad.get("roles") if isinstance(seguridad, dict) else None
            if (not isinstance(roles, list) or seguridad.get("uuid") != o.get("uuid")
                    or seguridad.get("objectType") != "process_model"):
                desconocidos.append("inicio: seguridad del proceso no legible")
            elif seguridad.get("inheritSecurity") or seguridad.get("parentFolderUuid"):
                desconocidos.append("inicio: herencia de seguridad no comparable")
            else:
                for p in pedidos:
                    rol = p.get("rol") if isinstance(p, dict) else None
                    grupos = p.get("grupos") if isinstance(p, dict) else None
                    filas = [x for x in roles if isinstance(x, dict) and x.get("roleName") == rol]
                    if (not isinstance(rol, str) or rol not in ROLES_PROCESO or not isinstance(grupos, list) or any(not isinstance(g, str) or not g for g in grupos)
                            or sum(1 for q in pedidos if isinstance(q, dict) and q.get("rol") == rol) != 1):
                        desconocidos.append(f"inicio {rol}: contrato ilegible o duplicado")
                        continue
                    resolucion = o.get("gruposParaPermisos")
                    resolucion = resolucion if isinstance(resolucion, dict) else {}
                    sin_resolver = [g for g in grupos if not isinstance(resolucion.get(g), str) or not resolucion[g]]
                    if sin_resolver:
                        desconocidos.append(f"inicio {rol}: grupo ausente, ambiguo o externo no resuelto: "
                                            + ", ".join(sin_resolver))
                        continue
                    if (len(filas) != 1 or not isinstance(filas[0].get("groupUuids"), list)
                            or any(not isinstance(g, str) or not g.strip() for g in filas[0]["groupUuids"])
                            or filas[0].get("inheritedGroupUuids") != [] or filas[0].get("userUuids")
                            or filas[0].get("users")):
                        desconocidos.append(f"inicio {rol}: rol no legible, herencia o miembros no comparables")
                        continue
                    pedidos_uuid = sorted(set(resolucion[g] for g in grupos))
                    reales = sorted(set(filas[0]["groupUuids"]))
                    if pedidos_uuid != reales:
                        distintos.append({"comprobacion": f"inicio: rol {rol}",
                                          "esperado": {"grupos": grupos, "groupUuids": pedidos_uuid},
                                          "real": {"groupUuids": reales}})
    acciones_esperadas = esperado.get("acciones", [])
    if not isinstance(acciones_esperadas, list):
        desconocidos.append("visibilidad: contrato de acciones ilegible")
        acciones_esperadas = []
    for a in acciones_esperadas:
        if not isinstance(a, dict) or "visibilidad" not in a:
            continue
        etiqueta = "visibilidad de " + str(a.get("nombre", "?"))
        cfg = a["visibilidad"].get("configuracion", "") if isinstance(a["visibilidad"], dict) else ""
        texto = cfg.removeprefix("EXPRESSION:").strip() if isinstance(cfg, str) and cfg.startswith("EXPRESSION:") else None
        declarada = expresion_visible(texto)
        observadas = o.get("acciones")
        reales = [r for r in observadas if isinstance(r, dict) and nombre_de_accion(r.get("nombre")) == nombre_de_accion(a.get("nombre"))] if isinstance(observadas, list) else []
        if declarada is None:
            desconocidos.append(etiqueta + ": falta un contrato EXPRESSION literal soportado")
        elif len(reales) != 1:
            desconocidos.append(etiqueta + ": acción no legible o nombre ambiguo")
        else:
            real = reales[0]
            observada = expresion_visible(real.get("visibilityExpr"))
            if real.get("securityMode") != "EXPRESSION" or real.get("securityRule") or observada is None:
                desconocidos.append(etiqueta + ": RULES, regla de seguridad o expresión no decidible; no se evalúa")
            else:
                def resuelta(exp):
                    if "literal" in exp:
                        return exp
                    constantes = o.get("constantesDeVisibilidad")
                    constantes = constantes if isinstance(constantes, dict) else {}
                    valores = [constantes.get(c) for c in exp["constantes"]]
                    validos = all(isinstance(x, dict) and isinstance(x.get("uuid"), str) and x["uuid"] for x in valores)
                    return {"gruposReferenciados": sorted(set(x["uuid"] for x in valores))} if validos else None
                configurada, actual = resuelta(declarada), resuelta(observada)
                if configurada is None or actual is None:
                    desconocidos.append(etiqueta + ": constante GROUP escalar o grupo no resuelto inequívocamente")
                elif configurada != actual:
                    distintos.append({"comprobacion": "configuración de " + etiqueta,
                                      "esperado": {"securityMode": "EXPRESSION", "configuracion": configurada},
                                      "real": {"securityMode": "EXPRESSION", "configuracion": actual}})
    return {k: v for k, v in (("permisosDiferentes", distintos), ("permisosNoComprobados", desconocidos)) if v}


async def verifica(ex: Extractor, app_obj: dict, objects: list[dict], pedidos: list[str],
                   esperado: dict | None = None, ligero: bool = False) -> dict:
    """Por objeto pedido: si existe, su tipo y su nombre; la última modificación (un dato, no una prueba); los campos
    de un record type o un CDT y, si lo esperado las nombra, sus acciones de registro (la herramienta que las lista o,
    si no la hay, la definición; sin ninguna de las dos, «accionesNoDisponibles»). Lo compara diferencias(). Con
    `ligero` (una issue sin pruebas), solo lo que se compara: sin la última modificación y sin la definición si lo
    esperado no nombra campos (salvo para leer las acciones, si no hay herramienta que las liste)."""
    ex.check_interrupted()
    esperado = esperado or {}
    por = resolver(pedidos, objects)
    usables = ex.usable("object")
    versiones = [t for t in usables if t.role == "versions"]
    definiciones = [t for t in usables if t.role == "definition"]
    de_acciones = [t for t in usables if "action" in t.toks and "recordType" in t.types and t.role != "definition"]
    de_seguridad = [t for t in usables if "security" in t.toks and t.generic]
    constantes_pedidas = {}

    async def grupo_de_constante(nombre):
        candidatas = [c for c in objects if c.get("type") == "constant" and c.get("name") == nombre]
        if len(candidatas) != 1:
            return None
        datos, _ = await llama(ex, definiciones, candidatas[0])
        for dato in map(bm.unwrap, datos):
            if (not isinstance(dato, dict) or dato.get("uuid") != candidatas[0]["uuid"]
                    or dato.get("type") != "GROUP" or dato.get("multiple") is not False
                    or not isinstance(dato.get("value"), str) or not dato["value"].strip()):
                continue
            grupos = [g for g in objects if g.get("type") == "group" and g.get("name") == dato["value"]]
            if len(grupos) == 1:
                return {"grupo": dato["value"], "uuid": grupos[0]["uuid"]}
        return None

    async def constante(nombre):
        if nombre not in constantes_pedidas:
            constantes_pedidas[nombre] = asyncio.create_task(grupo_de_constante(nombre))
        return await constantes_pedidas[nombre]

    async def uno(p: str) -> dict:
        o = por.get(p)
        if not o:
            return {"pedido": p, "existe": False}
        r = {"pedido": p, "existe": True, "nombre": o.get("name"), "tipo": o["type"], "uuid": o["uuid"]}
        quiere = esperado.get(p) if isinstance(esperado.get(p), dict) else {}
        con_acciones = o["type"] == "recordType" and isinstance(quiere.get("acciones"), list)
        errores: list[str] = []
        if not ligero:
            datos, errores = await llama(ex, versiones, o)
            r["ultimaModificacion"] = next((v for v in map(version, datos) if v), None)
        definicion: list = []
        if o["type"] in ("recordType", "cdt") and (not ligero or isinstance(quiere.get("campos"), list)
                                                     or (con_acciones and not de_acciones)):
            definicion, err = await llama(ex, definiciones, o)
            errores += err
            r["campos"] = campos(max(definicion, key=lambda d: len(json.dumps(d, default=str)))) if definicion else None
        if con_acciones:
            if de_acciones:
                datos, err = await llama(ex, de_acciones, o)
                errores += err
                r["acciones"] = next((a for a in map(acciones, datos) if a), [] if datos else None)
            else:
                r["acciones"] = next((a for a in map(acciones, definicion) if a), None)
                if r["acciones"] is None:
                    r["accionesNoDisponibles"] = True
            expresiones = [a["visibilidad"]["configuracion"].removeprefix("EXPRESSION:").strip()
                           for a in quiere["acciones"] if isinstance(a, dict) and isinstance(a.get("visibilidad"), dict)
                           and isinstance(a["visibilidad"].get("configuracion"), str)]
            pedidas = {nombre_de_accion(a.get("nombre")) for a in quiere["acciones"] if isinstance(a, dict)}
            expresiones += [a.get("visibilityExpr") for a in r.get("acciones") or [] if a.get("securityMode") == "EXPRESSION"
                            and nombre_de_accion(a.get("nombre")) in pedidas]
            nombres = {c for e in expresiones for c in (expresion_visible(e) or {}).get("constantes", [])}
            if nombres:
                r["constantesDeVisibilidad"] = dict(zip(sorted(nombres), await asyncio.gather(*(constante(c) for c in sorted(nombres)))))
        if o["type"] == "processModel" and quiere.get("permisosInicio"):
            datos, err = await llama(ex, de_seguridad, o)
            errores += err
            r["seguridadInicio"] = next((d for d in map(bm.unwrap, datos) if isinstance(d, dict) and "roles" in d), None)
            nombres = {g for p in quiere["permisosInicio"] if isinstance(p, dict) and isinstance(p.get("grupos"), list)
                       for g in p["grupos"] if isinstance(g, str)} if isinstance(quiere["permisosInicio"], list) else set()
            r["gruposParaPermisos"] = {}
            for nombre in nombres:
                grupos = [g for g in objects if g.get("type") == "group" and g.get("name") == nombre]
                r["gruposParaPermisos"][nombre] = grupos[0]["uuid"] if len(grupos) == 1 else None
        if errores:
            r["errores"] = errores
        return r

    hechos = list(await asyncio.gather(*(uno(p) for p in pedidos)))
    ex.check_interrupted()
    return {"aplicacion": {"nombre": app_obj.get("name"), "prefijo": app_obj.get("prefix"), "uuid": app_obj.get("uuid")},
            "conHistorialDeVersiones": bool(versiones),
            "objetos": hechos,
            "faltan": [p for p in pedidos if p not in por]}


# --------------------------------------------------------------------------- casos de prueba (verificar y regresion)

SIN_EJECUTOR = "el Dev MCP no ofrece ejecutar casos de prueba"
# La regresión sin el Dev MCP: Manage Test Cases (y el smart service Start Rule Tests) ejecuta solo los de las reglas
EN_APPIAN = ("la regresión se pasa en Appian: los casos de las reglas, con Manage Test Cases; los de las interfaces, "
             "desde cada interfaz en Designer, que Manage Test Cases no los ejecuta")


def ejecutores(ex: Extractor) -> dict[str, ToolInfo]:
    """{tipo de objeto: herramienta} de las que ejecutan todos los casos de prueba de un objeto (rol testRun, con solo su
    uuid: las que piden además el de un caso son de alcance manual). Se reconocen por su firma (devmcp_policy.json,
    testCases), sin fijar nombres; la extracción no las usa."""
    out: dict[str, ToolInfo] = {}
    for t in ex.tools:
        if t.role == "testRun" and t.scope == "object":
            for tipo in t.types:
                out.setdefault(tipo, t)
    return out


def dependientes_de(ex: Extractor) -> ToolInfo | None:
    """La herramienta que da los dependientes directos de un objeto (rol dependents), con un solo parámetro obligatorio:
    el objeto. En el Dev MCP real ese parámetro se llama «object» y la extracción no la usa (alcance manual)."""
    return next((t for t in ex.tools if t.allowed and t.role == "dependents"
                 and len(t.schema.get("required") or []) == 1), None)


def caso(c: dict, policy: Policy) -> dict:
    """Un caso de una respuesta de ejecución: {caso, resultado: pasa | falla | noEvaluable} y, si no pasa, su error (con
    la salida obtenida, si la hay: de una regla, lo que no cumplió la aserción) o por qué el ejecutor no lo evalúa. Es
    «noEvaluable» solo si todos sus errores casan con uno de testCases.noEvaluable de la política: un fallo de verdad no
    se tapa."""
    nombre = bm.pick(c, ("name", "testCaseName", "title")) or bm.pick(c, ("testCaseUuid", "uuid")) or "?"
    exito = c.get("success", c.get("passed"))
    if exito is None and isinstance(c.get("status"), str):
        exito = c["status"].lower() in ("pass", "passed", "success", "ok")
    if exito is True:
        return {"caso": nombre, "resultado": "pasa"}
    errores = [(e.get("type"), str(e.get("details") or e.get("message") or "")) for e in c.get("testErrors") or []
               if isinstance(e, dict)] or ([(None, str(c["error"]))] if c.get("error") else [])
    motivos = [next((m for t, rx, m in policy.no_evaluable if (not t or t == tipo) and rx.search(texto)), None)
               for tipo, texto in errores]
    if errores and all(motivos):
        return {"caso": nombre, "resultado": "noEvaluable", "motivo": motivos[0]}
    out = {"caso": nombre, "resultado": "falla",
           "error": next((t for (_, t), m in zip(errores, motivos) if not m and t), "no da lo esperado")[:500]}
    if c.get("output") not in (None, ""):
        out["salida"] = str(c["output"])[:300]
    return out


async def ejecuta(ex: Extractor, ti: ToolInfo, o: dict) -> dict:
    """Los casos de prueba guardados de un objeto, ejecutados: {objeto, tipo, casos, pasan, fallan, noEvaluables}, sin
    la salida de los que pasan (de una interfaz, el árbol de componentes: 270 KB con 7 casos); o «error» si no se pudo."""
    r = {"objeto": o.get("name") or o["uuid"], "tipo": o["type"]}
    args = ex.build_args(ti, obj=o)
    res = await ex.call_with_retry(ti.name, args) if args is not None else CallResult(False, error="No aplicable.")
    if not res.ok:
        return {**r, "error": (res.error or "")[:300]}
    d = bm.unwrap(res.data)
    lista = d if isinstance(d, list) else bm.find_list(d, ("results", "testResults", "testCases", "cases"))
    casos = [caso(c, ex.policy) for c in lista if isinstance(c, dict)]
    sin = lambda c: {k: v for k, v in c.items() if k != "resultado"}   # noqa: E731
    r.update(casos=len(casos), pasan=sum(c["resultado"] == "pasa" for c in casos),
             fallan=[sin(c) for c in casos if c["resultado"] == "falla"],
             noEvaluables=[sin(c) for c in casos if c["resultado"] == "noEvaluable"])
    return r


def cuenta(objetos: list[dict]) -> dict:
    return {"casos": sum(o.get("casos", 0) for o in objetos), "pasan": sum(o.get("pasan", 0) for o in objetos),
            "fallan": sum(len(o.get("fallan", [])) for o in objetos),
            "noEvaluables": sum(len(o.get("noEvaluables", [])) for o in objetos),
            "sinEjecutar": [o["objeto"] for o in objetos if o.get("error")]}


async def pruebas_de(ex: Extractor, suyos: list[dict], app_uuid: str | None) -> dict:
    """Los casos de prueba guardados de las reglas e interfaces de una issue (`suyos`, objetos de la aplicación) y de lo
    que las usa: sus dependientes directos, que es lo que da el Dev MCP, también de otra aplicación. Un fallo en los de la
    issue («de»: issue) la deja pendiente (lo decide issues.py del analista); en lo que la usa («de»: usa), es un aviso."""
    t0 = time.monotonic()
    run = ejecutores(ex)
    if not run:
        return {"ejecutadas": False, "motivo": SIN_EJECUTOR + ": los de la issue esperan a la regresión, que se pasa en "
                                                          "Appian"}
    propios = [o for o in suyos if o["type"] in run]
    dep, usan, sin_dependientes = dependientes_de(ex), {}, []
    if dep and propios:
        clave = (dep.schema.get("required") or [])[0]
        mios = {o["uuid"] for o in propios}
        respuestas = await asyncio.gather(*(ex.call_with_retry(dep.name, {clave: o["uuid"]}) for o in propios))
        sin_dependientes = [o.get("name") or o["uuid"] for o, res in zip(propios, respuestas) if not res.ok]
        for o, res in zip(propios, respuestas):
            d = bm.unwrap(res.data) if res.ok else []
            for it in (d if isinstance(d, list) else bm.find_list(d, ("dependents", "usages", "items", "results"))):
                u = pick(it, UUID_KEYS) if isinstance(it, dict) else None
                tipo = ex.policy.canon_type(pick(it, TYPE_KEYS)) if u else None
                if u and u not in mios and u != app_uuid and tipo in run:
                    x = usan.setdefault(u, {"uuid": u, "name": pick(it, NAME_KEYS) or u, "type": tipo, "usaA": []})
                    x["usaA"] += [] if o.get("name") in x["usaA"] else [o.get("name")]
    otros = list(usan.values())
    hechos = await asyncio.gather(*(ejecuta(ex, run[o["type"]], o) for o in propios + otros))
    objetos = [{**r, "de": "issue"} for r in hechos[:len(propios)]] + \
              [{**r, "de": "usa", "usaA": o["usaA"]} for r, o in zip(hechos[len(propios):], otros)]
    out = {"ejecutadas": True, "segundos": round(time.monotonic() - t0, 1), **cuenta(objetos), "objetos": objetos}
    if not dep:
        out["nota"] = "el Dev MCP no da los dependientes de un objeto: solo se ejecutan los casos de la issue"
    elif sin_dependientes:     # lo que los usa queda sin probar: se dice
        out["sinDependientes"] = sin_dependientes
        out["nota"] = (f"no se pudieron leer los dependientes de {', '.join(sin_dependientes)}: lo que los usa no se ha "
                       "probado (repite «verificar» o lo verá la regresión)")
    return out


def resumen_de_pruebas(p: dict | None, solo_fallos: bool = False) -> list[str]:
    """Las líneas de la salida: el recuento y lo que falla, lo que no se pudo ejecutar y, salvo en la regresión
    (solo_fallos), lo que no se puede evaluar y las reglas o interfaces de la issue sin casos. El detalle, en el fichero."""
    if not p:
        return []
    if not p.get("ejecutadas", p.get("ejecutada")):
        return [f"Pruebas: ninguna; {p.get('motivo')}."]
    objetos = p.get("objetos") if isinstance(p.get("objetos"), list) else p.get("porObjeto") or []
    de = {"issue": sum(o.get("de") == "issue" for o in objetos), "usa": sum(o.get("de") == "usa" for o in objetos)}
    quien = (f"{de['issue']} de la issue y {de['usa']} que los usan" if de["issue"] or de["usa"] else
             f"{len(objetos)} reglas e interfaces")
    L = [f"Pruebas: {quien}, {p['casos']} casos: {p['pasan']} pasan, {p['fallan']} fallan, {p['noEvaluables']} no "
         f"evaluables ({p.get('segundos', 0)} s)."]
    for o in objetos:
        donde = "" if not o.get("de") else (" (de la issue)" if o["de"] == "issue" else
                                            f" (usa {', '.join(map(str, o.get('usaA', [])))}: aviso)")
        L += [f"  ✗ {o['objeto']} «{c['caso']}»{donde}: {c['error'][:200]}" for c in o.get("fallan", [])]
        if o.get("error"):
            L.append(f"  ✗ {o['objeto']}{donde}: no se pudieron ejecutar sus casos ({o['error'][:200]})")
        if not solo_fallos:
            L += [f"  · {o['objeto']} «{c['caso']}»: no evaluable, {c['motivo']}" for c in o.get("noEvaluables", [])]
            if o.get("de") == "issue" and o.get("casos") == 0 and not o.get("error"):
                L.append(f"  · {o['objeto']}: sin casos de prueba")
    if p.get("nota"):
        L.append(f"  · {p['nota']}")
    return L


# Tipos de campo que son el mismo con otro nombre (el técnico escribe uno y Appian devuelve otro)
SINONIMOS = {"integer": ("int", "number (integer)", "número (entero)", "entero"),
             "decimal": ("float", "double", "number (decimal)", "número (decimal)", "numeric"),
             "text": ("string", "varchar", "texto"), "boolean": ("bool", "booleano"),
             "datetime": ("date and time", "date time", "timestamp", "fecha y hora"), "date": ("fecha",),
             "time": ("hora",), "user": ("usuario",), "group": ("grupo",)}


def tipo_de_campo(t) -> str:
    s = " ".join(str(t or "").lower().replace("(", " (").split()).replace("( ", "(")
    return next((c for c, alias in SINONIMOS.items() if s == c or s in alias), s)


def tipo_de_objeto(t) -> str:
    return re.sub(r"[\s_-]", "", str(t or "")).lower()   # recordType = Record Type = record_type


def tipo_de_accion(t) -> str:
    """De lista o relacionada, se escriba como se escriba: «De lista» = LIST_ACTION; «Relacionada» = RELATED_ACTION."""
    s = str(t or "").lower()
    return "lista" if "list" in s else "relacionada" if re.search(r"relat|relacion", s) else s.strip()


def nombre_de_accion(n) -> str:
    return " ".join(re.sub(r"[«»\"“”`]", "", str(n or "")).split()).lower()


def diferencias(o: dict, esperado: dict) -> dict:
    """Lo que no coincide entre un objeto verificado y lo esperado ({"tipo", "campos": [{"nombre", "tipo"}], "acciones":
    [{"nombre", "tipo"}]}): {"falta": true}; o «tipo» {esperado, real}, faltanCampos, sobranCampos, camposDeOtroTipo
    [{nombre, esperado, real}], camposSinLeer (no se pudo leer la definición), faltanAcciones, accionesDeOtroTipo y
    accionesSinLeer, solo los que no están vacíos. {} si coincide. De las acciones, solo las esperadas: las demás del
    record type no son de quien lo pide. Si el Dev MCP no da las acciones, no se comparan (lo dice la salida)."""
    if not o.get("existe"):
        return {"falta": True}
    out: dict = diferencias_permisos(o, esperado)
    if esperado.get("tipo") and tipo_de_objeto(esperado["tipo"]) != tipo_de_objeto(o.get("tipo")):
        out["tipo"] = {"esperado": esperado["tipo"], "real": o.get("tipo")}
    if isinstance(esperado.get("acciones"), list) and not o.get("accionesNoDisponibles"):
        if o.get("acciones") is None:
            out["accionesSinLeer"] = True
        else:
            reales = {nombre_de_accion(a.get("nombre")): a for a in o["acciones"]}
            pedidas = [a for a in esperado["acciones"] if isinstance(a, dict) and a.get("nombre")]
            faltan = [a["nombre"] for a in pedidas if nombre_de_accion(a["nombre"]) not in reales]
            otro = [{"nombre": a["nombre"], "esperado": a["tipo"], "real": reales[nombre_de_accion(a["nombre"])].get("tipo")}
                    for a in pedidas if a.get("tipo") and nombre_de_accion(a["nombre"]) in reales
                    and tipo_de_accion(a["tipo"]) != tipo_de_accion(reales[nombre_de_accion(a["nombre"])].get("tipo"))]
            out.update({k: v for k, v in (("faltanAcciones", faltan), ("accionesDeOtroTipo", otro)) if v})
    if isinstance(esperado.get("campos"), list):
        if o.get("campos") is None:
            out["camposSinLeer"] = True
            return out
        reales = {str(c.get("nombre") or "").lower(): c for c in o["campos"]}
        pedidos = {str(c.get("nombre") or "").lower(): c for c in esperado["campos"] if isinstance(c, dict)}
        faltan = [c.get("nombre") for k, c in pedidos.items() if k not in reales]
        sobran = [c.get("nombre") for k, c in reales.items() if k not in pedidos]
        otro = [{"nombre": reales[k].get("nombre"), "esperado": c.get("tipo"), "real": reales[k].get("tipo")}
                for k, c in pedidos.items() if k in reales and c.get("tipo")
                and tipo_de_campo(c["tipo"]) != tipo_de_campo(reales[k].get("tipo"))]
        out.update({k: v for k, v in (("faltanCampos", faltan), ("sobranCampos", sobran),
                                      ("camposDeOtroTipo", otro)) if v})
    return out


async def cmd_verificar(args) -> int:
    try:
        pedidos = lista_de_objetos(args.objetos)
        esperado = json.loads(Path(args.esperado).read_text(encoding="utf-8-sig")) if args.esperado else {}
    except (OSError, ValueError) as ex_:
        eprint(f"No se puede leer --objetos o --esperado: {ex_}")
        return EXIT_USAGE
    if not isinstance(esperado, dict):
        eprint("--esperado: un JSON {objeto: {\"tipo\": …, \"campos\": [{\"nombre\", \"tipo\"}]}}.")
        return EXIT_USAGE
    issue = esperado.pop("_issue", None)   # de qué issue y de qué versión es lo esperado: no es un objeto; va al resultado
    pedidos += [p for p in esperado if p not in pedidos]
    if not pedidos:
        eprint("Sin objetos: --objetos o --esperado.")
        return EXIT_USAGE
    # lo esperado de una issue dice si tiene pruebas que ejecutar; sin ellas, solo se lee lo que se compara. Para eso,
    # el tipo de cada objeto: el suyo o, si solo nombra acciones de registro, record type
    sin_pruebas = isinstance(issue, dict) and issue.get("pruebas", True) is False
    quiere = {p: esperado[p] if isinstance(esperado.get(p), dict) else {} for p in pedidos}
    with Registro(args.registro) as reg:
        sess, choice, code, msg = open_session(args, reg.destino)
        if not sess:
            eprint(msg)
            return code
        try:
            async with sess:
                ex = Extractor(sess, Policy(args.policy), None)
                tipos = {p: ex.policy.canon_type(q.get("tipo") or ("recordType" if q.get("acciones") else None))
                         for p, q in quiere.items()}
                if sin_pruebas and all(tipos.values()):
                    visibilidad = any(a.get("visibilidad", {}).get("configuracion") for q in quiere.values()
                                      for a in q.get("acciones", []) if isinstance(a, dict) and isinstance(a.get("visibilidad"), dict))
                    auxiliares = ("group", "constant") if visibilidad else (("group",) if any(q.get("permisosInicio") for q in quiere.values()) else ())
                    app_obj, objects = await solo_lo_esperado(ex, args, tipos, auxiliares)
                else:
                    app_obj, objects, _ = await prepare(ex, args)
                resultado = await verifica(ex, app_obj, objects, pedidos, esperado, ligero=sin_pruebas)
                if isinstance(issue, dict):
                    resultado["pruebas"] = (
                        {"ejecutadas": False, "motivo": "la issue no cambia criterios ni reglas"} if sin_pruebas else
                        await pruebas_de(ex, list(resolver(list(esperado), objects).values()), app_obj.get("uuid")))
                ex.check_interrupted()
        except ExtractionInterrupted:
            return interrupcion_de_lectura(Path(args.out).resolve(), ex)
        except SystemExit as se:
            return int(se.code)
        except Exception as ex_:
            return reg.no_arranca(ex_)
    if esperado:
        for o in resultado["objetos"]:
            if isinstance(esperado.get(o["pedido"]), dict):
                o["diferencias"] = diferencias(o, esperado[o["pedido"]])
        resultado["conDiferencias"] = [o["pedido"] for o in resultado["objetos"]
                                       if any(k != "permisosNoComprobados" for k in o.get("diferencias", {}))]
        sin_permisos = [o["pedido"] for o in resultado["objetos"] if o.get("diferencias", {}).get("permisosNoComprobados")]
        if sin_permisos:
            resultado["permisosNoComprobados"] = sin_permisos
    resultado = {"generadoEn": now_iso(), "entorno": entorno(server_info(choice)["url"]),
                 **({"issue": issue} if issue is not None else {}), **resultado}
    destino = Path(args.out).resolve()
    write_json(destino, resultado)
    supera_interrupcion(destino.with_name(destino.stem + ".interrumpido" + destino.suffix))
    if args.json:
        print(json.dumps(resultado, ensure_ascii=False, indent=1))
    existen = sum(1 for o in resultado["objetos"] if o["existe"])
    print(f"Verificados {len(pedidos)} objetos: {existen} existen"
          + (f"; faltan: {', '.join(resultado['faltan'])}" if resultado["faltan"] else "")
          + (f"; distintos de lo esperado: {', '.join(resultado['conDiferencias'])}" if resultado.get("conDiferencias")
             else "") + f". Detalle: {destino}")
    for o in resultado["objetos"]:
        if o.get("accionesNoDisponibles"):
            print(f"  · {o['pedido']}: el Dev MCP no da sus acciones de registro; no se comprueban")
        for motivo in (o.get("diferencias") or {}).get("permisosNoComprobados", []):
            print(f"  · {o['pedido']}: permisos no comprobados: {motivo}")
    if any("permisosInicio" in q or tipo_de_objeto(q.get("tipo")) == "processmodel"
           or any("visibilidad" in a for a in q.get("acciones", [])) for q in quiere.values()):
        print("  · Permisos: se compara configuración declarada; el acceso efectivo exige QA con cada rol.")
    for linea in resumen_de_pruebas(resultado.get("pruebas")):
        print(linea)
    return EXIT_OK


async def cmd_regresion(args) -> int:
    """Los casos de prueba de toda la aplicación, objeto a objeto por el Dev MCP: el resumen, en --out; por la salida,
    solo lo que falla. 1 si algún caso falla; 17 si el Dev MCP no ofrece ejecutar casos (la regresión, en Appian)."""
    with Registro(args.registro) as reg:
        sess, choice, code, msg = open_session(args, reg.destino)
        if not sess:
            eprint(msg)
            return code
        try:
            async with sess:
                ex = Extractor(sess, Policy(args.policy), None)
                app_obj, objects, _ = await prepare(ex, args)
                run, t0 = ejecutores(ex), time.monotonic()
                con = [o for o in objects if o["type"] in run]
                hechos = list(await asyncio.gather(*(ejecuta(ex, run[o["type"]], o) for o in con)))
                ex.check_interrupted()
        except ExtractionInterrupted:
            return interrupcion_de_lectura(Path(args.out).resolve(), ex)
        except SystemExit as se:
            return int(se.code)
        except Exception as ex_:
            return reg.no_arranca(ex_)
    resultado = {"generadoEn": now_iso(), "entorno": entorno(server_info(choice)["url"]),
                 "aplicacion": {"nombre": app_obj.get("name"), "prefijo": app_obj.get("prefix"),
                                "uuid": app_obj.get("uuid")}}
    if not run:
        resultado.update(ejecutada=False, motivo=f"{SIN_EJECUTOR}: {EN_APPIAN}")
    else:
        resultado.update(ejecutada=True, segundos=round(time.monotonic() - t0, 1), objetos=len(hechos),
                         sinCasos=[r["objeto"] for r in hechos if r.get("casos") == 0 and not r.get("error")],
                         **cuenta(hechos), porObjeto=hechos)
    destino = Path(args.out).resolve()
    write_json(destino, resultado)
    supera_interrupcion(destino.with_name(destino.stem + ".interrumpido" + destino.suffix))
    if not run:
        print(f"Regresion sin hacer: {resultado['motivo']}. Detalle: {destino}")
        return EXIT_SIN_PRUEBAS
    print(f"Regresion de {app_obj.get('name')}: {resultado['objetos']} reglas e interfaces "
          f"({len(resultado['sinCasos'])} sin casos), {resultado['casos']} casos: {resultado['pasan']} pasan, "
          f"{resultado['fallan']} fallan, {resultado['noEvaluables']} no evaluables ({resultado['segundos']} s). "
          f"Detalle: {destino}")
    for linea in resumen_de_pruebas(resultado, solo_fallos=True)[1:]:
        print(linea)
    return EXIT_FALLAN if resultado["fallan"] or resultado["sinEjecutar"] else EXIT_OK


def instante(texto) -> datetime | None:
    """Una fecha ISO (con hora o sin ella, con Z o con desfase) como instante en UTC, para compararla."""
    t = str(texto or "").strip().replace("Z", "+00:00")
    for valor in (t, t[:10]):
        try:
            d = datetime.fromisoformat(valor)
        except ValueError:
            continue
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    return None


def ignorar_de(valor: str | None) -> dict[str, tuple[datetime, str]]:
    """--ignorar: <nombre>@<fecha ISO> separados por comas, o @fichero con uno por línea. ValueError si uno no lo es."""
    out = {}
    for x in lista_de_objetos(valor):
        nombre, _, fecha = x.rpartition("@")
        d = instante(fecha) if fecha.strip() else None
        if not nombre.strip() or d is None:
            raise ValueError(f"--ignorar: «{x}» no es <nombre>@<fecha ISO>")
        out[nombre.strip()] = (d, fecha.strip())
    return out


def version_guardada(raw: Path, o: dict, usadas: set[str] | None) -> dict | None:
    """La última versión de un objeto según el as-is: su respuesta de historial guardada en mcp_raw."""
    carpeta = carpeta_objeto(raw, o["type"], o["uuid"])
    if not carpeta.exists():
        return None
    return next((v for f in bm.read_object_files(carpeta, usadas) if f["ok"] and f["role"] == "versions"
                 for v in [version(f["response"])] if v), None)


def cambio(antes: dict, ahora: dict) -> bool:
    t0, t1 = instante(antes.get("fecha")), instante(ahora.get("fecha"))
    return bool((t0 and t1 and t1 > t0) or antes.get("versiones") != ahora.get("versiones"))


async def deriva_de(ex: Extractor, guardada: dict, objects: list[dict], pedidos: list[str],
                    ignorar: dict, raw: Path, usadas: set[str] | None) -> dict:
    """Cambiados, nuevos y retirados frente al as-is. Los de --ignorar modificados después de su fecha van aparte."""
    ex.check_interrupted()
    base = {o["uuid"]: o for o in guardada.get("objects", [])}
    ahora = {o["uuid"]: o for o in objects}
    if pedidos:
        por = resolver(pedidos, list(base.values()) + [o for u, o in ahora.items() if u not in base])
        alcance = {o["uuid"] for o in por.values()}
    else:
        por, alcance = {}, set(base) | set(ahora)
    versiones = [t for t in ex.usable("object") if t.role == "versions"]

    def ficha(o: dict, **kw) -> dict:
        return {"nombre": o.get("name"), "tipo": o["type"], "uuid": o["uuid"], **kw}
    orden = sorted((u for u in alcance if u in ahora), key=lambda u: (ahora[u]["type"], str(ahora[u].get("name"))))
    if versiones:
        respuestas = await asyncio.gather(*(llama(ex, versiones, ahora[u]) for u in orden))
    else:
        respuestas = [([], [])] * len(orden)
    ex.check_interrupted()
    nuevos, cambiados, ignorados, sin_dato = [], [], [], []
    for u, (datos, errores) in zip(orden, respuestas):
        o = ahora[u]
        actual = next((v for v in map(version, datos) if v), None)
        if u not in base:
            entrada, destino = ficha(o, ahora=actual), nuevos
        else:
            if not versiones:
                continue
            antes = version_guardada(raw, base[u], usadas)
            if actual is None or antes is None:
                sin_dato.append({"nombre": o.get("name"), "motivo": "el as-is no trae su historial" if antes is None
                                 else "el Dev MCP no devolvio su historial" + (f" ({errores[0]})" if errores else "")})
                continue
            if not cambio(antes, actual):
                continue
            entrada, destino = ficha(o, asIs=antes, ahora=actual), cambiados
        desde = ignorar.get(o.get("name")) or ignorar.get(u)
        cuando = instante((actual or {}).get("fecha"))
        if desde and cuando and cuando > desde[0]:   # de nuestras unidades: modificado después de aprobarla
            ignorados.append({**entrada, "desde": desde[1]})
        else:
            destino.append(entrada)
    out = {"conHistorialDeVersiones": bool(versiones), "alcance": pedidos or "todos",
           "cambiados": cambiados if versiones else None, "nuevos": nuevos,
           "retirados": [ficha(base[u]) for u in sorted(alcance, key=lambda u: str(base.get(u, {}).get("name")))
                         if u in base and u not in ahora],
           "ignorados": ignorados, "sinDato": sin_dato, "noEncontrados": [p for p in pedidos if p not in por]}
    if not versiones:
        out["nota"] = ("El Dev MCP no da el historial de versiones: no se sabe que objetos cambiaron y no se supone "
                       "nada. Nuevos y retirados salen de la lista de objetos de la aplicacion.")
    return out


async def cmd_deriva(args) -> int:
    salida = Path(args.out).resolve()
    interm = work_dir(salida)
    guardada = extraccion_guardada(interm / "mcp_raw")
    app = guardada.get("application") or {}
    if not app.get("uuid"):
        eprint(f"No hay extraccion en {salida}: la deriva se compara con un as-is ya extraido.")
        return EXIT_USAGE
    try:
        pedidos, ignorar = lista_de_objetos(args.objetos), ignorar_de(args.ignorar)
    except (OSError, ValueError) as ex_:
        eprint(str(ex_))
        return EXIT_USAGE
    with Registro(args.registro) as reg:
        sess, choice, code, msg = open_session(args, reg.destino)
        if not sess:
            eprint(msg)
            return code
        url, antes = entorno(server_info(choice)["url"]), entorno(guardada.get("entorno"))
        if url and antes and url.lower() != antes.lower():
            eprint(f"El as-is es de {antes} y el Dev MCP de {url}: la deriva compara con el mismo entorno.")
            return EXIT_APP
        try:
            report = json.loads((interm / "extraction_report.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            report = {}
        args.app = app["uuid"]
        try:
            async with sess:
                ex = Extractor(sess, Policy(args.policy), None)
                _, objects, _ = await prepare(ex, args)
                resultado = await deriva_de(ex, guardada, objects, pedidos, ignorar, interm / "mcp_raw",
                                            bm.herramientas_usadas(report))
        except ExtractionInterrupted:
            return interrupcion_de_lectura(salida / "datos" / "deriva.json", ex)
        except SystemExit as se:
            eprint(f"La aplicacion del as-is ({app.get('name')}) no esta visible en el entorno.")
            return int(se.code)
        except Exception as ex_:
            return reg.no_arranca(ex_)
    resultado = {"generadoEn": now_iso(), "entorno": url or antes,
                 "aplicacion": {k2: app.get(k) for k, k2 in (("name", "nombre"), ("prefix", "prefijo"), ("uuid", "uuid"))},
                 "asIs": {"extraidoEn": report.get("startedAt")}, **resultado}
    destino = salida / "datos" / "deriva.json"
    write_json(destino, resultado)
    supera_interrupcion(destino.with_name(destino.stem + ".interrumpido" + destino.suffix))
    if args.json:
        print(json.dumps(resultado, ensure_ascii=False, indent=1))
    n = lambda k: len(resultado[k] or [])  # noqa: E731
    print(f"Deriva frente al as-is del {str(resultado['asIs']['extraidoEn'] or '?')[:10]}: "
          + (f"{n('cambiados')} cambiados, " if resultado["cambiados"] is not None else "cambiados: sin historial, ")
          + f"{n('nuevos')} nuevos, {n('retirados')} retirados, {n('ignorados')} ignorados (de nuestras unidades). "
          f"Detalle: {destino}")
    if resultado.get("nota"):
        print(resultado["nota"])
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
        if name == "extract":
            sp.add_argument("--solo", help="Objetos que se vuelven a extraer (nombres o uuids separados por comas, o "
                                           "@fichero); de los demas, lo guardado, sin llamar al Dev MCP. Rehace el modelo")
    sp = sub.add_parser("datafabric")
    common(sp)
    sp.add_argument("--out", required=True)
    registro = "Saca el registro del servidor por la salida de errores (sin esto, solo si no arranca)"
    sp = sub.add_parser("verificar")
    common(sp)
    sp.add_argument("--app", required=True, help="uuid, prefijo o nombre de la aplicacion")
    sp.add_argument("--objetos", help="Nombres o uuids separados por comas, o @fichero (uno por linea)")
    sp.add_argument("--esperado", help="Fichero JSON {objeto: {\"tipo\": …, \"campos\": [{\"nombre\", \"tipo\"}], "
                                       "\"acciones\": [{\"nombre\", \"tipo\"}]}}: se verifican tambien esos objetos y "
                                       "se escriben sus diferencias. Su clave «_issue», si la lleva, pasa tal cual al "
                                       "resultado, en «issue», y con ella se ejecutan sus pruebas salvo «pruebas»: false")
    sp.add_argument("--out", required=True, help="Fichero JSON del resultado")
    sp.add_argument("--registro", action="store_true", help=registro)
    sp = sub.add_parser("regresion")
    common(sp)
    sp.add_argument("--app", required=True, help="uuid, prefijo o nombre de la aplicacion")
    sp.add_argument("--out", required=True, help="Fichero JSON del resumen")
    sp.add_argument("--registro", action="store_true", help=registro)
    sp = sub.add_parser("deriva")
    common(sp)
    sp.add_argument("--registro", action="store_true", help=registro)
    sp.add_argument("--out", required=True, help="Carpeta as-is con la extraccion con la que se compara")
    sp.add_argument("--objetos", help="Solo estos objetos (nombres o uuids separados por comas, o @fichero)")
    sp.add_argument("--ignorar", help="<nombre>@<fecha ISO>, separados por comas (o @fichero): los de nuestras "
                                      "unidades modificados despues de esa fecha no cuentan como cambiados")
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
    if args.cmd == "verificar":
        return asyncio.run(cmd_verificar(args))
    if args.cmd == "regresion":
        return asyncio.run(cmd_regresion(args))
    if args.cmd == "deriva":
        return asyncio.run(cmd_deriva(args))
    return EXIT_USAGE


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):  # consolas de Windows sin UTF-8: «→» o «✓» no caben en cp1252
        _s.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
