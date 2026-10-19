"""Escritura de texto que conserva los finales de línea al actualizar un diagrama."""
from pathlib import Path


def escribir(ruta, contenido, referencia=None):
    """Nuevos: LF. Existentes: su salto; temporales de actualización: el de su original."""
    destino = Path(ruta)
    anterior = destino if destino.exists() else Path(referencia) if referencia else None
    datos = anterior.read_bytes() if anterior and anterior.exists() else b""
    salto = "\r\n" if b"\r\n" in datos else "\n"
    with destino.open("w", encoding="utf-8", newline="") as f:
        f.write(contenido.replace("\r\n", "\n").replace("\n", salto))
