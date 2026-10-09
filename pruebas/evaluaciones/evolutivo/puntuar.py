#!/usr/bin/env python3
"""Puntúa el caso evolutivo: el plan de construcción (técnico §13) de tres historias nuevas sobre la aplicación MNT.

Uso:
  python3 puntuar.py <p> [--ocultas]

<p> es la carpeta del proyecto, con as-is/ (la aplicación MNT) y analisis/. Lee las tablas de técnico §13
(`Paso · Objeto · Tipo · Situación · Sustituye a`) y las compara con esperado.json (con --ocultas, con
ocultas/esperado.json): {objeto: [situaciones que valen]}.
  - Un objeto de la aplicación cuenta si alguna de sus filas tiene una situación que vale. Una fila de una parte suya
    («MNT Orden — acción Corregir orden») cuenta como el objeto, y si es «Nuevo», como «Modifica». Una fila «Sustituye»
    cuenta para el objeto que dice en «Sustituye a».
  - «(nuevo) <tipo>: <qué es>» cuenta con una fila «Nuevo» de ese tipo (proceso, interfaz, record type, regla…), de un
    objeto que no está en la aplicación y que no haya contado ya para otro.
Además, ningún objeto que ya existe (as-is/datos/inventario.json) va como «Nuevo», y comprobar.py del analista sale
sin errores (con --fuentes si existe <p>/fuentes).

Imprime cada objeto y el total. Sale 0 con el 80 % o más de lo esperado, ningún objeto existente como nuevo y
comprobar.py sin errores; 1 si no; 2 si falta un fichero.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
AQUI = Path(__file__).resolve().parent
PLUGIN = Path(os.environ.get("PLUGIN_A_PROBAR") or AQUI.parents[2]).resolve()
ANALISTA = PLUGIN / "skills" / "appian-functional-analyst" / "scripts"
sys.path.insert(0, str(ANALISTA))
import modelo as mo  # noqa: E402

MINIMO = 0.8
TIPOS = {  # tipo de «(nuevo) <tipo>: …» → cómo puede venir en la columna Tipo
    "proceso": ("process model", "modelo de proceso", "proceso"),
    "interfaz": ("interface", "interfaz"),
    "record type": ("record type", "tipo de registro"),
    "regla": ("expression rule", "regla"),
    "constante": ("constant", "constante"),
    "grupo": ("group", "grupo"),
    "web api": ("web api",),
    "integracion": ("integration", "integracion"),
}


def limpio(celda: str) -> str:
    """El nombre de un objeto sin formato: sin `código`, negrita, comillas ni enlaces."""
    t = mo.sin_comentarios(celda)
    t = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", t)
    return re.sub(r"[`*«»\"]", "", t).strip()


def situacion(celda: str) -> str:
    n = mo.normaliza(limpio(celda))
    return next((s for s in ("nuevo", "modifica", "existe", "sustituye") if n.startswith(s)), n)


def filas_13(m: mo.Proyecto) -> list[dict]:
    out = []
    for _, cab, filas in m.tablas("T", "13"):
        ncab = [mo.normaliza(c).strip() for c in cab]
        if "objeto" not in ncab or not any(c.startswith("situacion") for c in ncab):
            continue
        for f in filas:
            fila = {k: (f[i] if i < len(f) else "") for i, k in enumerate(ncab)}
            out.append({"objeto": limpio(fila.get("objeto", "")), "tipo": mo.normaliza(limpio(fila.get("tipo", ""))),
                        "situacion": situacion(next((v for k, v in fila.items() if k.startswith("situacion")), "")),
                        "sustituye": limpio(next((v for k, v in fila.items() if k.startswith("sustituye")), ""))})
    return out


def igual(a: str, b: str) -> bool:
    return mo.normaliza(a) == mo.normaliza(b)


def parte_de(objeto: str, nombre: str) -> bool:
    """«MNT Orden — acción Corregir orden» o «MNT Orden (acción …)» es una parte de MNT Orden; «MNT_OrdenDTO» no."""
    o, n = mo.normaliza(objeto), mo.normaliza(nombre)
    return o.startswith(n) and len(o) > len(n) and not re.match(r"[\w]", o[len(n)])


def situaciones(nombre: str, filas: list[dict]) -> list[str]:
    out = [f["situacion"] for f in filas if igual(f["objeto"], nombre)]
    out += ["modifica" if f["situacion"] == "nuevo" else f["situacion"] for f in filas if parte_de(f["objeto"], nombre)]
    out += ["sustituye" for f in filas if f["situacion"] == "sustituye"
            and any(igual(x, nombre) or parte_de(x, nombre) for x in re.split(r",|;| y ", f["sustituye"]))]
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("proyecto")
    ap.add_argument("--ocultas", action="store_true")
    a = ap.parse_args()
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")
    p = Path(a.proyecto)
    m = mo.Proyecto(p)
    if "T" not in m.docs:
        print(f"No encuentro: {p / 'analisis' / 'tecnico.md'}", file=sys.stderr)
        return 2
    esperado = json.loads((AQUI / ("ocultas" if a.ocultas else "") / "esperado.json").read_text(encoding="utf-8"))
    filas = filas_13(m)
    print(f"  técnico §13: {len(filas)} filas con objeto y situación")
    inventario = p / "as-is" / "datos" / "inventario.json"
    existentes = set()
    if inventario.is_file():
        existentes = {mo.normaliza(o["nombre"]) for o in json.loads(inventario.read_text(encoding="utf-8")).get("objetos", [])}
    usadas, bien = set(), 0
    for clave, valen in esperado.items():
        valen_n = [mo.normaliza(v) for v in valen]
        nuevo = re.match(r"\(nuevo\)\s*([^:]+):", clave)
        if nuevo:
            tipo = mo.normaliza(nuevo.group(1).strip())
            sinonimos = TIPOS.get(tipo, (tipo,))
            k = next((k for k, f in enumerate(filas) if k not in usadas and f["situacion"] == "nuevo"
                      and mo.normaliza(f["objeto"]) not in existentes and any(s in f["tipo"] for s in sinonimos)), None)
            if k is None:
                print(f"FALLO {clave}: ninguna fila «Nuevo» de tipo {tipo} sin contar")
                continue
            usadas.add(k)
            bien += 1
            print(f"OK    {clave}: {filas[k]['objeto']} ({filas[k]['tipo']}, nuevo)")
            continue
        vistas = situaciones(clave, filas)
        if any(s in valen_n for s in vistas):
            bien += 1
            print(f"OK    {clave}: {', '.join(sorted(set(vistas)))}")
        elif vistas:
            print(f"FALLO {clave}: {', '.join(sorted(set(vistas)))}; vale {' o '.join(valen)}")
        else:
            print(f"FALLO {clave}: no está en §13; vale {' o '.join(valen)}")
    malos = sorted({f["objeto"] for f in filas if f["situacion"] == "nuevo" and mo.normaliza(f["objeto"]) in existentes})
    if malos:
        print(f"FALLO como «Nuevo» y ya existen en la aplicación: {', '.join(malos)}")
    orden = [sys.executable, str(ANALISTA / "comprobar.py"), str(p)]
    if (p / "fuentes").is_dir():
        orden += ["--fuentes", str(p / "fuentes")]
    r = subprocess.run(orden, capture_output=True, text=True, encoding="utf-8", errors="replace")
    errores = [l for l in r.stdout.splitlines() if l.startswith("✗")]
    print(("OK    " if r.returncode == 0 else "FALLO ") + "comprobar.py: "
          + ("sin errores" if r.returncode == 0 else f"{len(errores)} con errores" + "".join(f"\n  {e}" for e in errores[:10])))
    total = len(esperado)
    print(f"Total: {bien}/{total} ({bien / total:.0%}; hace falta el {MINIMO:.0%})")
    return 0 if bien >= MINIMO * total and not malos and r.returncode == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
