#!/usr/bin/env python3
"""build_datos.py - <salida>/datos/: lo que las demás skills leen de la ingeniería inversa.

Uso:
  python3 <skill>/scripts/build_datos.py <carpeta_salida>

Lee   <trabajo>/inventory.json, graph.json, registro.json y la definición de cada record type
Crea  <salida>/datos/inventario.json, dependencias.json, hallazgos.json y procesos.json (formato en
      references/datos.md). Las demás skills leen estos ficheros, nunca <trabajo>/.
Solo librería estándar. Salida: 0 bien, 2 uso o falta el inventario.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_model import find_list, load, pick, unwrap  # noqa: E402
from rutas import work_dir  # noqa: E402

CAMPOS_HALLAZGO = ("id", "titulo", "area", "severidad", "certeza", "objetos", "documento", "evidencia")


def _json(p: Path) -> dict:
    return load(p) if p.exists() else {}


def _nombres(lista: list, claves: tuple[str, ...]) -> list[str]:
    return [n for n in (pick(x, claves) for x in lista) if n]


def tambien(o: dict, trabajo: Path) -> list[str]:
    """Lo que se cita con un record type sin ser un objeto: su tabla, vistas, campos, relaciones y acciones."""
    if o.get("type") != "recordType":
        return []
    out = [o["tableName"]] if o.get("tableName") else []
    if o.get("detail") == "full" and o.get("path"):
        try:
            d = unwrap(load(trabajo / o["path"]).get("response"))
        except (OSError, ValueError, AttributeError):
            d = None
        if d is not None:
            out += _nombres(find_list(d, ("views",)), ("name", "viewName", "label", "displayName"))
            out += _nombres(find_list(d, ("fields",)), ("fieldName", "name"))
            out += _nombres(find_list(d, ("relationships",)), ("relationshipName", "name"))
            out += _nombres(find_list(d, ("actions",)), ("displayName", "name", "key"))
    return list(dict.fromkeys(out))


def _relativa(salida: Path, rel: str) -> str | None:
    return rel if (salida / rel).is_file() else None


def construir(salida: Path) -> dict:
    """Escribe los cuatro ficheros de <salida>/datos/ y los devuelve ({nombre del fichero: contenido})."""
    salida = Path(salida).resolve()
    trabajo = work_dir(salida)
    inv = load(trabajo / "inventory.json")
    por_tipo = inv.get("objects", {})
    app = (por_tipo.get("application") or [{}])[0]
    objs = [o for t, lista in por_tipo.items() if t != "application" for o in lista]
    nombre = {o["uuid"]: o.get("name") for o in objs + [app] if o.get("uuid")}

    inventario = {
        "aplicacion": {"nombre": app.get("name"), "prefijo": app.get("prefix"), "uuid": app.get("uuid")},
        "objetos": sorted(({"nombre": o.get("name"), "tipo": o["type"], "uuid": o.get("uuid"),
                            "anexo": _relativa(salida, f"anexo/{o['type']}/{o['slug']}.md") if o.get("slug") else None,
                            "tambien": tambien(o, trabajo)} for o in objs),
                          key=lambda x: (x["tipo"], str(x["nombre"]).lower())),
    }
    aristas = [{"de": nombre[e["source"]], "a": nombre[e["target"]],
                "donde": " · ".join(e.get("evidence") or []) or e.get("refType")}
               for e in _json(trabajo / "graph.json").get("edges", [])
               if nombre.get(e.get("source")) and nombre.get(e.get("target"))]
    hallazgos = [{k: h.get(k, [] if k == "objetos" else None) for k in CAMPOS_HALLAZGO}
                 for h in _json(trabajo / "registro.json").get("hallazgos", []) if not h.get("duplicadoDe")]
    procesos = [{"nombre": o.get("name"),
                 "json": _relativa(salida, f"08-procesos-bpmn/{o['slug']}.json") if o.get("slug") else None,
                 "nodos": o.get("nodeCount"), "ejecuciones": (o.get("usage") or {}).get("executions")}
                for o in por_tipo.get("processModel", [])]
    datos = {"inventario.json": inventario,
             "dependencias.json": {"aristas": sorted(aristas, key=lambda a: (a["de"], a["a"], a["donde"] or ""))},
             "hallazgos.json": {"hallazgos": sorted(hallazgos, key=lambda h: h["id"] or "")},
             "procesos.json": {"procesos": sorted(procesos, key=lambda p: str(p["nombre"]).lower())}}
    carpeta = salida / "datos"
    carpeta.mkdir(parents=True, exist_ok=True)
    for fichero, contenido in datos.items():
        (carpeta / fichero).write_text(json.dumps(contenido, ensure_ascii=False, indent=1), encoding="utf-8")
    return datos


def main(salida_dir: str) -> int:
    salida = Path(salida_dir).resolve()
    if not (work_dir(salida) / "inventory.json").exists():
        print(f"ERROR: falta {work_dir(salida) / 'inventory.json'} (ejecuta antes build_model.py)", file=sys.stderr)
        return 2
    d = construir(salida)
    print(f"datos/: {len(d['inventario.json']['objetos'])} objetos, {len(d['dependencias.json']['aristas'])} aristas, "
          f"{len(d['hallazgos.json']['hallazgos'])} hallazgos, {len(d['procesos.json']['procesos'])} procesos")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
