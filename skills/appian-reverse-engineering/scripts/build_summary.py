#!/usr/bin/env python3
"""
build_summary.py - Consolida inventario, grafo, extracción y registro de hallazgos en summary.json,
la fuente de cifras de LEEME.md y de los publicadores (PDF y dashboard).

Uso:
  python3 build_summary.py <carpeta_salida>

Lee (en <trabajo> = <salida>/extraccion):
  inventory.json, graph.json, preflight.json y registro.json (si existen)

Escribe:
  <trabajo>/summary.json
"""
from __future__ import annotations

import json
import sys
sys.dont_write_bytecode = True  # sin __pycache__ en el plugin: no se escribe fuera del proyecto
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rutas import work_dir  # noqa: E402


def load_json(p: Path) -> dict:
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


NIVELES = ("Bajo", "Medio", "Alto")


def confidence(coverage: float, verified_ratio: float | None) -> tuple[str, list[str]]:
    """Nivel de confianza de la documentación y por qué. Una sola fórmula para LEEME y los publicadores.
    Alto: definiciones de al menos el 90 % de los objetos (sin carpetas) y, si hay hallazgos, al menos la mitad
    verificados. Medio: definiciones de al menos el 70 %. Bajo: el resto. Baja un nivel más si menos de un tercio
    de los hallazgos están verificados. Las llamadas que el servidor no admite para un tipo (p. ej. dependencias de
    un agente de IA) no cuentan: no son fallos de la extracción."""
    nivel = 2 if coverage >= 0.9 else 1 if coverage >= 0.7 else 0
    motivos = [f"definiciones obtenidas: {coverage:.0%} de los objetos (sin carpetas)"]
    if verified_ratio is not None:
        motivos.append(f"hallazgos verificados: {verified_ratio:.0%}")
        if nivel == 2 and verified_ratio < 0.5:
            nivel = 1
            motivos.append("no llega a Alto: menos de la mitad de los hallazgos están verificados")
        elif verified_ratio < 1 / 3 and nivel > 0:
            nivel -= 1
            motivos.append("baja un nivel: menos de un tercio de los hallazgos están verificados")
    return NIVELES[nivel], motivos


def main(doc_root: str) -> int:
    root = Path(doc_root).resolve()
    interm = work_dir(root)
    if not interm.exists():
        print(f"ERROR: no existe {interm}", file=sys.stderr)
        return 2
    inv = load_json(interm / "inventory.json")
    graph = load_json(interm / "graph.json")
    preflight = load_json(interm / "preflight.json")
    registro = load_json(interm / "registro.json")

    counts = inv.get("counts", {})
    objects = inv.get("objects", {})
    app_meta = (objects.get("application") or [{}])[0]
    all_objs = [o for t, objs in objects.items() if t != "application" for o in objs]

    # Confianza
    with_def = sum(1 for o in all_objs if o.get("detail") == "full")
    designed = [o for o in all_objs if o.get("type") not in ("folder", "processModelFolder", "knowledgeCenter")]
    coverage = sum(1 for o in designed if o.get("detail") == "full") / len(designed) if designed else 0.0
    orden = {"Alta": 0, "Media": 1, "Baja": 2}
    vivos = sorted((h for h in registro.get("hallazgos", []) if not h.get("duplicadoDe")),
                   key=lambda h: (orden.get(h.get("severidad"), 9), h.get("id", "")))
    verified_ratio = (sum(1 for h in vivos if h.get("certeza") == "verificado") / len(vivos)) if vivos else None
    nivel, motivos = confidence(coverage, verified_ratio)

    # Procesos críticos: la criticidad la calcula build_model.py (misma fórmula para todos)
    critical = []
    for pm in objects.get("processModel", []):
        c = pm.get("criticality") or {}
        if c.get("critical"):
            critical.append({"name": pm.get("name"), "score": c.get("score"), "reasons": c.get("reasons", []),
                             "calledBy": c.get("calledBy", 0), "callsIntegrations": c.get("callsIntegrations", 0),
                             "isBatch": bool(pm.get("hasRecurrence")), "userTaskCount": pm.get("userTaskCount", 0),
                             "executions": (pm.get("usage") or {}).get("executions")})
    critical.sort(key=lambda x: -(x["score"] or 0))

    # Uso real: procesos con historial de ejecuciones, de más a menos usados
    usage = sorted(({"name": pm.get("name"), **{k: (pm.get("usage") or {}).get(k)
                                                 for k in ("executions", "lastExecution", "failed", "failedInSampleOf")}}
                    for pm in objects.get("processModel", []) if isinstance(pm.get("usage"), dict)),
                   key=lambda u: -(u["executions"] or 0))[:10]

    # Secretos: objetos con valores que parecen un secreto (secrets y secret de build_model.py)
    secret_objs = [o for o in all_objs if o.get("secrets") or o.get("secret")]

    # Señales objetivas para el registro (el orquestador decide si son hallazgos)
    signals = []
    unused = [p.get("name") for p in objects.get("processModel", [])
              if isinstance(p.get("usage"), dict) and p["usage"].get("executions") == 0]
    if unused:
        signals.append({"type": "processModelsWithoutExecutions", "objects": unused})
    invalid = [o.get("name") for o in all_objs if o.get("validationIssues")]
    if invalid:
        signals.append({"type": "validationIssues", "objects": invalid})
    big = [i.get("name") for i in objects.get("interface", []) if i.get("sailBytes", 0) > 80000]
    if big:
        signals.append({"type": "largeInterfaces", "objects": big})
    orphans = {o for o in graph.get("orphans", [])}
    if orphans:
        signals.append({"type": "orphans", "objects": [o.get("name") for o in all_objs if o.get("uuid") in orphans]})

    env = preflight.get("environment") or {}
    summary = {
        "meta": {
            "appName": app_meta.get("name", "?"), "appPrefix": app_meta.get("prefix"),
            "appDescription": app_meta.get("description"), "appUuid": app_meta.get("uuid"),
            "source": inv.get("source"),
            "environment": {"url": (inv.get("source") or {}).get("url") or env.get("url"),
                            "isProduction": env.get("isProduction"), "appianVersion": env.get("appianVersion")},
            "generatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "confidence": nivel, "confidenceBasis": motivos,
            "coverage": {"withDefinition": sum(1 for o in designed if o.get("detail") == "full"),
                         "objects": len(designed), "ratio": round(coverage, 3), "excludes": "carpetas"},
        },
        "counts": counts,
        "totals": {"objects": len(all_objs), "withDefinition": with_def,
                   "edges": graph.get("stats", {}).get("edgeCount", 0),
                   "hubs": len(graph.get("hubs", [])), "orphans": len(orphans)},
        # Las mismas capas que 02-arquitectura.md
        "layerBreakdown": {
            "Entrada y presentación": sum(counts.get(t, 0) for t in ("site", "interface", "webApi")),
            "Lógica": sum(counts.get(t, 0) for t in ("processModel", "expressionRule", "decision", "aiAgent")),
            "Datos": sum(counts.get(t, 0) for t in ("recordType", "cdt", "dataStore")),
            "Integración": sum(counts.get(t, 0) for t in ("integration", "connectedSystem")),
            "Transversal": counts.get("constant", 0),
            "Seguridad": counts.get("group", 0),
        },
        "hubs": [{"name": h.get("name"), "type": h.get("type"), "inDegree": h.get("in")} for h in graph.get("hubs", [])[:10]],
        "criticalProcesses": critical,
        "usage": usage,
        "integrations": [{"name": it.get("name"), "method": it.get("method"), "connectedSystemRef": it.get("connectedSystemRef")}
                         for it in objects.get("integration", [])],
        "secrets": {"count": len(secret_objs), "objects": [o.get("name") for o in secret_objs]},
        "findings": [{k: h.get(k) for k in ("id", "titulo", "area", "severidad", "certeza", "documento")}
                     for h in vivos],
        "findingsBySeverity": registro.get("porSeveridad", {}),
        "findingsByCertainty": registro.get("porCerteza", {}),
        "signals": signals,
        "objects": {t: [{k: o.get(k) for k in ("name", "uuid", "type", "mcpType", "slug") if o.get(k) is not None}
                        for o in objs] for t, objs in objects.items()},
    }
    out_path = interm / "summary.json"
    out_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"summary.json: {summary['meta']['appName']}, {len(all_objs)} objetos, confianza {nivel} ({'; '.join(motivos)}), "
          f"{len(critical)} procesos críticos, {len(vivos)} hallazgos, {len(secret_objs)} objetos con secretos")
    if not registro:
        print("AVISO: no hay registro.json (ejecuta build_registry.py antes)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
