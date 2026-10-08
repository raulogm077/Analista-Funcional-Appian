"""Rutas comunes de la skill.

Todo va en la carpeta de salida (<p>/as-is/ del proyecto): los documentos y, en <salida>/extraccion/, la extracción y
los datos de trabajo (respuestas del Dev MCP, inventario, grafo, cachés, resumen). La extracción se escribe ya saneada
(privacidad.py) y con rutas cortas, para que el proyecto quepa en Windows y en OneDrive.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path


def work_dir(out, crear: bool = False) -> Path:
    """Carpeta de la extracción de una salida: <salida>/extraccion, dentro del proyecto. Con crear=True la crea."""
    d = Path(out).resolve() / "extraccion"
    if crear:
        d.mkdir(parents=True, exist_ok=True)
    return d


def carpeta_objeto(raw: Path, tipo: str, uuid: str) -> Path:
    """Carpeta de las respuestas de un objeto: <raw>/<tipo>/<12 hex del sha1 del uuid>. El uuid, que alargaría la
    ruta, está en mcp_raw/_objects.json y en el _meta de cada respuesta."""
    return Path(raw) / re.sub(r"[^A-Za-z0-9_-]", "_", tipo) / hashlib.sha1(uuid.encode("utf-8")).hexdigest()[:12]
