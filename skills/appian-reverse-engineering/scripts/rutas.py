"""Rutas comunes de la skill.

Los entregables van en <salida> (p. ej. appian-docs/DEM) y se pueden compartir.
Los datos de trabajo (respuestas en bruto, inventario, grafo, cachés) van en una carpeta hermana,
<padre>/_trabajo/<nombre> (p. ej. appian-docs/_trabajo/DEM), que NO se comparte: contiene usuarios,
hosts y definiciones completas.
"""
from __future__ import annotations

from pathlib import Path


def work_dir(out, crear: bool = False) -> Path:
    """Carpeta de trabajo de una salida: <padre>/_trabajo/<nombre>. Con crear=True la crea, con un .gitignore
    que excluye todo, antes de que se escriba nada en ella."""
    out = Path(out).resolve()
    d = out.parent / "_trabajo" / out.name
    if crear:
        d.mkdir(parents=True, exist_ok=True)
        gi = d / ".gitignore"
        if not gi.exists():
            gi.write_text("# Datos de trabajo: no se versionan ni se comparten\n*\n", encoding="utf-8")
    return d
