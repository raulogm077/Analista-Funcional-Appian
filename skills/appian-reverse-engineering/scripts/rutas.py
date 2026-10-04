"""Rutas comunes de la skill.

Los entregables van en <salida> (p. ej. appian-docs/DEM) y se pueden compartir.
Los datos de trabajo (respuestas en bruto, inventario, grafo, cachés) van en una carpeta hermana,
<padre>/_trabajo/<nombre> (p. ej. appian-docs/_trabajo/DEM), que NO se comparte: contiene usuarios,
hosts y definiciones completas.
"""
from __future__ import annotations

from pathlib import Path


def work_dir(out) -> Path:
    """Carpeta de trabajo de una salida: <padre>/_trabajo/<nombre>."""
    out = Path(out).resolve()
    return out.parent / "_trabajo" / out.name
