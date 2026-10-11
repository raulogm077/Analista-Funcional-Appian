#!/usr/bin/env python3
"""Palabras de cada documento de <as-is> y el total, como las cuenta comprobar_asis.py para su presupuesto (su función
palabras()): fuera de los bloques de código y de los comentarios, sin los títulos ni lo que escriben los scripts entre
sus marcadores, sin los destinos de los enlaces y con cada código en línea como una palabra. No cuenta anexo/,
extraccion/ ni datos/.

Uso: python3 palabras.py <as-is> [--json]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).resolve().parents[3] / "skills" / "appian-reverse-engineering" / "scripts"
sys.path.insert(0, str(SCRIPTS))
from comprobar_asis import palabras as palabras_de  # noqa: E402

FUERA = ("anexo", "extraccion", "datos")


def palabras(as_is: Path) -> dict[str, int]:
    out = {}
    for doc in sorted(as_is.rglob("*.md")):
        rel = doc.relative_to(as_is).as_posix()
        if rel.split("/", 1)[0] in FUERA:
            continue
        out[rel] = palabras_de(doc.read_text(encoding="utf-8"))
    return out


def main(argv: list[str]) -> int:
    if not argv or not Path(argv[0]).is_dir():
        print(__doc__, file=sys.stderr)
        return 2
    cuenta = palabras(Path(argv[0]).resolve())
    if "--json" in argv:
        print(json.dumps({"documentos": cuenta, "total": sum(cuenta.values())}, ensure_ascii=False, indent=1))
    else:
        for rel, n in cuenta.items():
            print(f"{n:7d}  {rel}")
        print(f"{sum(cuenta.values()):7d}  total")
    return 0


if __name__ == "__main__":
    for st in (sys.stdout, sys.stderr):
        st.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv[1:]))
