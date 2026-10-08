#!/usr/bin/env python3
"""Puntúa las respuestas del recién llegado sobre la aplicación ficticia MNT.

Uso:
  python3 puntuar.py <respuestas.json> <as-is> [--ocultas] [--minimo N] [--obligatorias Q-21,…]

respuestas.json = [{"id": "Q-01", "respuesta": "…" o ["…", …], "evidencia": "ruta#ancla"}], con la ruta relativa a
<as-is>. Las preguntas y sus respuestas aceptadas están en ../aplicacion-ficticia/preguntas.json (con --ocultas, en
../aplicacion-ficticia/ocultas/preguntas.json).

Una respuesta acierta si la evidencia es un fichero de <as-is> que existe y no está en extraccion/, y:
  - de tipo objeto o número: contiene, como palabra entera, una de las formas aceptadas (sin tildes, mayúsculas ni
    signos de alrededor);
  - de tipo sí/no: empieza por la aceptada;
  - de tipo lista: contiene todos sus elementos (de un elemento que es una lista de formas, basta una).
Imprime cada pregunta y el total. Sale 0 con --minimo aciertos o más (por defecto, el 90 % redondeado hacia arriba) y
todas las obligatorias bien; 1 si no; 2 si falta un fichero.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
import unicodedata
from pathlib import Path

FICTICIA = Path(__file__).resolve().parents[1] / "aplicacion-ficticia"


def normal(texto) -> str:
    t = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode("ascii").lower()
    return " ".join(re.sub(r"[`'\"«»“”()\[\]]", " ", t).split()).strip(" .,;:")


def contiene(texto: str, forma: str) -> bool:
    return re.search(rf"(?<![\w.]){re.escape(normal(forma))}(?![\w])", normal(texto)) is not None


def acierta(pregunta: dict, respuesta) -> bool:
    texto = " | ".join(map(str, respuesta)) if isinstance(respuesta, list) else str(respuesta or "")
    aceptadas = pregunta["respuestas"]
    if pregunta["tipo"] == "lista":
        return all(any(contiene(texto, f) for f in (e if isinstance(e, list) else [e])) for e in aceptadas)
    if pregunta["tipo"] == "si-no":
        primera = (normal(texto).split() or [""])[0]
        return primera in {normal(f) for f in aceptadas}
    return any(contiene(texto, f) for f in aceptadas)


def evidencia_valida(as_is: Path, evidencia) -> bool:
    ruta = str(evidencia or "").split("#", 1)[0].strip()
    if not ruta:
        return False
    f = (as_is / ruta).resolve()
    try:
        rel = f.relative_to(as_is)
    except ValueError:
        return False
    return f.is_file() and "extraccion" not in rel.parts


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("respuestas")
    ap.add_argument("as_is")
    ap.add_argument("--ocultas", action="store_true")
    ap.add_argument("--minimo", type=int)
    ap.add_argument("--obligatorias", default="")
    a = ap.parse_args(argv)
    fichero = FICTICIA / ("ocultas" if a.ocultas else "") / "preguntas.json"
    as_is = Path(a.as_is).resolve()
    for f in (Path(a.respuestas), fichero):
        if not f.is_file():
            print(f"ERROR: falta {f}", file=sys.stderr)
            return 2
    preguntas = json.loads(fichero.read_text(encoding="utf-8"))
    dadas = {r.get("id"): r for r in json.loads(Path(a.respuestas).read_text(encoding="utf-8"))}
    bien = []
    for p in preguntas:
        r = dadas.get(p["id"]) or {}
        ok_r, ok_e = acierta(p, r.get("respuesta")), evidencia_valida(as_is, r.get("evidencia"))
        if ok_r and ok_e:
            bien.append(p["id"])
            print(f"✓ {p['id']}")
        else:
            motivo = "sin respuesta" if not r else ("respuesta" if not ok_r else "") + \
                     (" y " if not ok_r and not ok_e else "") + ("evidencia" if not ok_e else "")
            print(f"✗ {p['id']} ({motivo}): {json.dumps(r.get('respuesta'), ensure_ascii=False)[:120]}")
    minimo = a.minimo if a.minimo is not None else math.ceil(0.9 * len(preguntas))
    obligatorias = [x.strip() for x in a.obligatorias.split(",") if x.strip()]
    faltan = [x for x in obligatorias if x not in bien]
    print(f"Aciertos: {len(bien)} de {len(preguntas)} (mínimo {minimo})"
          + (f"; obligatorias sin acertar: {', '.join(faltan)}" if faltan else ""))
    return 0 if len(bien) >= minimo and not faltan else 1


if __name__ == "__main__":
    for st in (sys.stdout, sys.stderr):
        st.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
