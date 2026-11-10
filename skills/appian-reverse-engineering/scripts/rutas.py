"""Rutas comunes de la skill, y cómo se escribe en ellas.

Todo va en la carpeta de salida (<p>/as-is/ del proyecto): los documentos y, en <salida>/extraccion/, la extracción y
los datos de trabajo (respuestas del Dev MCP, inventario, grafo, cachés, resumen). La extracción se escribe tal cual la
devuelve el Dev MCP y con rutas cortas, para que el proyecto quepa en Windows y en OneDrive.
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


def escribe(ruta, texto: str) -> None:
    """UTF-8: conserva CRLF al reescribir; un fichero nuevo usa LF en todos los sistemas."""
    p = Path(ruta)
    anterior = p.read_bytes() if p.exists() else b""
    salto = "\r\n" if b"\r\n" in anterior else "\n"
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write(texto.replace("\r\n", "\n").replace("\n", salto))


def safe_name(s: str, maximo: int = 48) -> str:
    """Nombre de fichero de una herramienta, corto para que la ruta quepa en Windows y en OneDrive: si no cabe, se
    recorta y lleva 8 hex del sha1 del nombre, para que dos nombres largos no se pisen. _meta.tool guarda el nombre."""
    limpio = re.sub(r"[^A-Za-z0-9_.\-]", "_", s)
    if len(limpio) <= maximo:
        return limpio
    return f"{limpio[:maximo - 9]}-{hashlib.sha1(s.encode('utf-8')).hexdigest()[:8]}"


TIPO_MAXIMO = 24   # con el nombre de herramienta de 48 (safe_name), mcp_raw/… no pasa de 100


def carpeta_objeto(raw: Path, tipo: str, uuid: str) -> Path:
    """Carpeta de las respuestas de un objeto: <raw>/<tipo>/<12 hex del sha1 del uuid>. El uuid, que alargaría la
    ruta, está en mcp_raw/_objects.json y en el _meta de cada respuesta. Un tipo de más de 24 caracteres se recorta
    y lleva 8 hex del sha1 del tipo, para que dos tipos largos no se pisen."""
    limpio = re.sub(r"[^A-Za-z0-9_-]", "_", tipo)
    if len(limpio) > TIPO_MAXIMO:
        limpio = f"{limpio[:TIPO_MAXIMO - 9]}-{hashlib.sha1(tipo.encode('utf-8')).hexdigest()[:8]}"
    return Path(raw) / limpio / hashlib.sha1(uuid.encode("utf-8")).hexdigest()[:12]
