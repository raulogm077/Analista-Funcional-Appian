#!/usr/bin/env python3
"""Lo que la disciplina de evidencia (Tarea 8b) tiene que dejar en el as-is de la aplicación ficticia MNT.

Uso: python3 evidencia.py <as-is>

Comprueba, en datos/ y en los entregables:
  1. MNT_CS_Proveedores tiene un hallazgo verificado cuya evidencia («mcp:<tipo>/<nombre>#…») lleva a su ficha del
     anexo (con inventario.json → anexo);
  2. los tres objetos CMN que llama la aplicación (de otra aplicación, que no está en la extracción) están en
     dependencias.json → fueraDeLaAplicacion, con un NV de sin-verificar.json cuyo «queHaceFalta» empieza por export
     o acceso;
  3. ningún entregable dice «no existe» o «no existen» (no se miran anexo/, extraccion/ ni datos/).
Sale 0 si se cumple todo, 1 si no y 2 si falta datos/.
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

CMN = ("CMN_FormatearFecha", "CMN_UsuarioActual", "CMN_IF_Cabecera")
FUERA = ("anexo", "extraccion", "datos")


def normal(t: str) -> str:
    return unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode("ascii").lower().strip()


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__, file=sys.stderr)
        return 2
    as_is = Path(argv[0]).resolve()
    datos = as_is / "datos"
    leer = lambda n: json.loads((datos / n).read_text(encoding="utf-8")) if (datos / n).is_file() else None  # noqa: E731
    inv, hal, dep, nv = (leer(n) for n in ("inventario.json", "hallazgos.json", "dependencias.json", "sin-verificar.json"))
    if inv is None or hal is None or dep is None:
        print(f"ERROR: falta {datos}/inventario.json, hallazgos.json o dependencias.json", file=sys.stderr)
        return 2
    fallos = []

    # 1. el hallazgo verificado de MNT_CS_Proveedores, con evidencia a su ficha
    anexo = {o["nombre"]: o.get("anexo") for o in inv.get("objetos", [])}
    def lleva_a_su_ficha(h):  # noqa: E306
        m = re.match(r"mcp:[^/]+/([^#@]+)", str(h.get("evidencia") or ""))
        ficha = anexo.get(m.group(1).strip()) if m else None
        return bool(ficha) and (as_is / ficha).is_file()
    buenos = [h["id"] for h in hal.get("hallazgos", []) if "MNT_CS_Proveedores" in (h.get("objetos") or [])
              and h.get("certeza") == "verificado" and lleva_a_su_ficha(h)]
    print(("✓" if buenos else "✗") + " MNT_CS_Proveedores: hallazgo verificado con evidencia a su ficha del anexo"
          + (f" ({', '.join(buenos)})" if buenos else ""))
    if not buenos:
        fallos.append(1)

    # 2. los CMN, fuera de la aplicación y con su NV
    fuera = {o.get("nombre"): o for o in dep.get("fueraDeLaAplicacion", [])}
    nvs = {n.get("id"): n for n in (nv or {}).get("sinVerificar", [])}
    for nombre in CMN:
        o = fuera.get(nombre)
        n = nvs.get((o or {}).get("nv"))
        ok = bool(o) and bool(n) and normal(str(n.get("queHaceFalta") or "")).startswith(("export", "acceso"))
        print(("✓" if ok else "✗") + f" {nombre}: en fueraDeLaAplicacion con un NV de export o acceso"
              + (f" ({o.get('nv')})" if ok else "" if o else " (no está)"))
        if not ok:
            fallos.append(2)

    # 3. ningún «no existe» en los entregables
    negativos = []
    for doc in sorted(as_is.rglob("*.md")):
        rel = doc.relative_to(as_is).as_posix()
        if rel.split("/", 1)[0] in FUERA:
            continue
        for i, l in enumerate(doc.read_text(encoding="utf-8").splitlines(), 1):
            if re.search(r"(?i)\bno\s+existen?\b", l):
                negativos.append(f"{rel}:{i}")
    print(("✓" if not negativos else "✗") + " ningún entregable dice «no existe»"
          + (f": {', '.join(negativos[:10])}" if negativos else ""))
    if negativos:
        fallos.append(3)
    return 1 if fallos else 0


if __name__ == "__main__":
    for st in (sys.stdout, sys.stderr):
        st.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv[1:]))
