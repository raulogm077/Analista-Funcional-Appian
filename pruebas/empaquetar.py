#!/usr/bin/env python3
"""Hace el paquete del plugin, appian-analisis-funcional.plugin: la carpeta del plugin en un zip, sin lo de desarrollo.

  python3 pruebas/empaquetar.py [-o <ruta del .plugin>]

Lleva lo mismo que la orden zip del README, porque usa la misma lista que comprueba comprobar_plugin.py
(NO_VAN_EN_EL_PAQUETE, CACHES y los *.plugin): sin .git, .github/, .claude/, docs/, pruebas/, CLAUDE.md ni cachés.
Funciona igual en Windows, donde no suele haber zip. Por defecto deja el paquete al lado de la carpeta del repositorio,
fuera de ella: no se versiona.
"""
from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import comprobar_plugin as cp  # noqa: E402

NOMBRE = "appian-analisis-funcional.plugin"


def empaquetar(destino: Path) -> int:
    """Escribe el .plugin en `destino` y devuelve cuántos ficheros lleva."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporal = destino.with_name(destino.name + ".tmp")
    n = 0
    with zipfile.ZipFile(temporal, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for f in cp.ficheros_del_paquete():
            z.write(f, f.relative_to(cp.RAIZ).as_posix())
            n += 1
    temporal.replace(destino)
    return n


def main() -> int:
    for s in (sys.stdout, sys.stderr):  # consolas de Windows sin UTF-8
        s.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-o", "--out", help=f"ruta del paquete (por defecto, ../{NOMBRE} junto al repositorio)")
    a = ap.parse_args()
    destino = Path(a.out).resolve() if a.out else cp.RAIZ.parent / NOMBRE
    if cp.RAIZ in destino.parents:
        print(f"El paquete no va dentro del repositorio ({destino}): dale otra ruta con -o.", file=sys.stderr)
        return 2
    n = empaquetar(destino)
    print(f"{destino}: {n} ficheros")
    return 0


if __name__ == "__main__":
    sys.exit(main())
