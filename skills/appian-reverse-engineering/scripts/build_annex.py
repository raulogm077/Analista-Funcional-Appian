#!/usr/bin/env python3
"""build_annex.py - Anexo de definiciones: el código y la configuración originales, legibles y sin datos sensibles.

Uso:
  python3 scripts/build_annex.py <carpeta_salida>

Lee   <trabajo>/inventory.json y las definiciones de <trabajo>/mcp_raw/
Crea  <salida>/anexo/indice.md y <salida>/anexo/<tipo>/<slug>.md (uno por objeto con definición)

Para cada objeto:
  - las expresiones (SAIL, reglas, cuerpos de integración) en bloques con número de línea, que es lo que citan
    las evidencias «línea N»; las referencias recordType!{uuid}Nombre se muestran como recordType!Nombre;
  - en los process models, una tabla de nodos;
  - la definición completa en JSON.
Los secretos ya vienen enmascarados de la extracción; aquí además se omiten los usuarios (claves de autoría y
cualquier identificador de usuario visto en miembros, versiones o ejecuciones).
Solo librería estándar. Salida: 0 bien, 2 uso o falta el inventario.
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rutas import work_dir  # noqa: E402

MARCA = "<!-- anexo generado por build_annex.py -->"
USER_KEY = re.compile(r"(?i)^(user(name|id)?|login|initiator|startedby|starter|(created|modified|updated|lastmodified|published|saved)by|"
                      r"author|owner|creator|modifier|assignee|usuario)$")
CODE_HINT = re.compile(r"a!|rule!|cons!|local!|ri!|fv!|pv!|recordType!|\bif\(|=\s*\{")
UUID_REF = re.compile(r"(?<=[!.])\{[^{}\s]{8,}\}")
USER_PH = "‹usuario›"
TIPOS = {"interface": "Interfaz", "expressionRule": "Regla de expresión", "processModel": "Modelo de proceso",
         "recordType": "Record type", "integration": "Integración", "connectedSystem": "Connected system",
         "webApi": "Web API", "constant": "Constante", "site": "Site", "group": "Grupo", "decision": "Decisión",
         "cdt": "Tipo de datos (CDT)", "aiAgent": "Agente de IA", "folder": "Carpeta", "document": "Documento",
         "dataStore": "Data store", "application": "Aplicación"}


def load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def unwrap(x):
    while isinstance(x, dict) and len(x) == 1 and next(iter(x)) in ("result", "data", "response", "object", "definition"):
        x = next(iter(x.values()))
    return x


def users_seen(raw: Path) -> set[str]:
    """Identificadores de usuario que aparecen en miembros, versiones y ejecuciones."""
    found: set[str] = set()

    def walk(x, key=""):
        if isinstance(x, dict):
            if str(x.get("type", x.get("kind", ""))).lower() == "user":
                found.update(v for k, v in x.items() if k in ("name", "username", "id", "value") and isinstance(v, str))
            for k, v in x.items():
                walk(v, k)
        elif isinstance(x, list):
            for v in x:
                walk(v, key)
        elif isinstance(x, str) and USER_KEY.match(key or "") and 3 <= len(x) <= 80 and " " not in x.strip():
            found.add(x.strip())
    for f in raw.rglob("*.json"):
        try:
            d = load(f)
        except Exception:  # noqa: BLE001
            continue
        if isinstance(d, dict) and (d.get("_meta") or {}).get("role") in ("members", "versions", "history"):
            walk(d.get("response"))
    return {u for u in found if u != USER_PH}


def scrub(x, users: set[str]):
    if isinstance(x, dict):
        is_user = str(x.get("type", x.get("kind", ""))).lower() == "user"
        out = {}
        for k, v in x.items():
            if USER_KEY.match(k) and isinstance(v, (str, int)):
                out[k] = USER_PH
            elif is_user and k in ("name", "value", "username", "id") and isinstance(v, str):
                out[k] = USER_PH
            else:
                out[k] = scrub(v, users)
        return out
    if isinstance(x, list):
        return [scrub(v, users) for v in x]
    if isinstance(x, str):
        for u in users:
            if u in x:
                x = re.sub(rf"(?<![\w.]){re.escape(u)}(?![\w])", USER_PH, x)
        return x
    return x


def extract_code(x) -> tuple[object, list[tuple[str, str]]]:
    """Saca las cadenas que son código a bloques aparte y deja una referencia en su lugar."""
    blocks: list[tuple[str, str]] = []

    def rec(v, path):
        if isinstance(v, dict):
            return {k: rec(w, f"{path}.{k}" if path else k) for k, w in v.items()}
        if isinstance(v, list):
            return [rec(w, f"{path}[{i}]") for i, w in enumerate(v)]
        if isinstance(v, str):
            v = UUID_REF.sub("", v)
            if ("\n" in v or len(v) > 160) and CODE_HINT.search(v):
                blocks.append((path or "valor", v))
                return f"‹ver bloque {len(blocks)}›"
        return v
    return rec(x, ""), blocks


def numbered(code: str) -> str:
    lines = code.split("\n")
    w = len(str(len(lines)))
    return "\n".join(f"{i:>{w}}  {line}" for i, line in enumerate(lines, 1))


def node_table(defn) -> list[str]:
    nodes = defn.get("nodes") if isinstance(defn, dict) else None
    if not isinstance(nodes, list) or not nodes:
        return []
    rows = ["## Nodos", "", "| id | Tipo | Nombre | Siguientes |", "|---|---|---|---|"]
    for n in nodes:
        if not isinstance(n, dict):
            continue
        conns = n.get("connections") or n.get("outgoing") or []
        if isinstance(conns, list):
            conns = ", ".join(str(c.get("target", c.get("id", c)) if isinstance(c, dict) else c) for c in conns)
        pick = lambda *ks: next((n[k] for k in ks if n.get(k) not in (None, "")), "")  # noqa: E731
        name = str(pick("name", "objectName", "label")).replace("|", "/")
        rows.append(f"| {pick('id', 'nodeId')} | `{pick('type', 'objectType', 'nodeType')}` | {name} | {conns or '—'} |")
    return rows + [""]


def main(salida_dir: str) -> int:
    salida = Path(salida_dir).resolve()
    trabajo = work_dir(salida)
    inv_path = trabajo / "inventory.json"
    if not inv_path.exists():
        print(f"ERROR: falta {inv_path} (ejecuta antes build_model.py)", file=sys.stderr)
        return 2
    inv = load(inv_path)
    anexo = salida / "anexo"
    if anexo.exists():
        idx = anexo / "indice.md"
        if not idx.exists() or MARCA not in idx.read_text(encoding="utf-8"):
            print(f"ERROR: {anexo} existe y no lo generó este script; no se toca", file=sys.stderr)
            return 2
        shutil.rmtree(anexo)
    users = users_seen(trabajo / "mcp_raw")
    por_tipo: dict[str, list] = defaultdict(list)
    fecha = (inv.get("source") or {}).get("extractedAt") or inv.get("generatedAt") or ""
    for tipo, objs in inv.get("objects", {}).items():
        if tipo == "application":
            continue
        for o in objs:
            if o.get("detail") != "full" or not o.get("path"):
                continue
            src = trabajo / o["path"]
            try:
                resp = unwrap(load(src).get("response"))
            except Exception:  # noqa: BLE001
                continue
            clean = scrub(resp, users)
            body, blocks = extract_code(clean)
            slug = o.get("slug") or re.sub(r"[^A-Za-z0-9_-]", "_", o.get("name", "objeto"))
            rel = Path(tipo) / f"{slug}.md"
            lines = [MARCA, f"# {o.get('name')}", "",
                     f"> {TIPOS.get(tipo, tipo)}. Definición tal como la devolvió el entorno (solo lectura)"
                     f"{', ' + fecha[:10] if fecha else ''}. Secretos enmascarados y usuarios omitidos.", ""]
            lines += node_table(body if isinstance(body, dict) else {})
            if blocks:
                lines += ["## Expresiones", ""]
                for i, (path, code) in enumerate(blocks, 1):
                    lines += [f"### Bloque {i}: `{path}`", "", "```text", numbered(code), "```", ""]
            lines += ["## Definición completa", "", "```json", json.dumps(body, ensure_ascii=False, indent=2), "```", ""]
            (anexo / tipo).mkdir(parents=True, exist_ok=True)
            (anexo / rel).write_text("\n".join(lines), encoding="utf-8")
            por_tipo[tipo].append((o.get("name"), rel.as_posix()))
    anexo.mkdir(parents=True, exist_ok=True)
    idx = [MARCA, "# Anexo: definiciones originales", "",
           "> El código y la configuración de cada objeto tal como están en el entorno, para consultar el detalle sin "
           "abrir Appian. Las evidencias «mcp:<tipo>/<nombre>#…» de los documentos apuntan a estos ficheros; "
           "«línea N» es la numeración de los bloques de expresiones.", ""]
    for tipo in sorted(por_tipo):
        idx += [f"## {TIPOS.get(tipo, tipo)}", "", "| Objeto | Fichero |", "|---|---|"]
        idx += [f"| {n} | [{Path(r).name}](./{r}) |" for n, r in sorted(por_tipo[tipo], key=lambda x: str(x[0]).lower())]
        idx.append("")
    (anexo / "indice.md").write_text("\n".join(idx), encoding="utf-8")
    total = sum(len(v) for v in por_tipo.values())
    print(f"anexo: {total} objetos en {len(por_tipo)} tipos; {len(users)} identificadores de usuario omitidos")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
