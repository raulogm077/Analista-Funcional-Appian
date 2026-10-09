#!/usr/bin/env python3
"""Puntúa una propuesta de refactorización contra las malas prácticas sembradas en la aplicación ficticia MNT.

Uso:
  python3 puntuar.py <propuesta.md> <as-is> [--ocultas]

Las malas prácticas están en ../aplicacion-ficticia/malas-practicas.json (con --ocultas, en
../aplicacion-ficticia/ocultas/malas-practicas.json), cada una con sus objetos, su «BP nn §x» y `bp_aceptadas`: las
secciones de buenas prácticas que tratan ese problema, empezando por la de `bp`.

Una mala práctica cuenta si hay una REF del Diagnóstico que:
  - cita en su Evidencia alguno de sus objetos, por su nombre exacto (vale también con «_» en lugar de los espacios,
    como en las rutas del anexo);
  - tiene en su Regla una de sus `bp_aceptadas`, la sección exacta («§1» no vale por «§1.3» si la lista no lo dice);
  - sale en el apartado Solución.
Además, Pendientes tiene que citar los NV de <as-is>/datos/sin-verificar.json que tratan objetos de fuera de la
aplicación (`fueraDeLaAplicacion` de dependencias.json, con su campo `nv`): en MNT, el de las reglas CMN.

Imprime cada mala práctica, el total y los NV. Sale 0 con el 90 % o más y los NV citados; 1 si no; 2 si falta un
fichero.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
FICTICIA = Path(__file__).resolve().parents[1] / "aplicacion-ficticia"
MINIMO = 0.9


def apartados(texto: str) -> dict[str, str]:
    """{título sin número: cuerpo} de cada `## n. Título`."""
    partes = re.split(r"(?m)^##\s+(?:\d+\.\s*)?(.+?)\s*$", texto)
    return {partes[k].strip().lower(): partes[k + 1] for k in range(1, len(partes) - 1, 2)}


def apartado(secciones: dict[str, str], nombre: str) -> str:
    return next((cuerpo for titulo, cuerpo in secciones.items() if titulo.startswith(nombre)), "")


def campo(ficha: str, nombre: str) -> str:
    """El texto de «- Nombre: …», con las líneas sangradas que lo continúan."""
    m = re.search(rf"(?m)^[-*]\s*\**{nombre}\**\s*:(.*(?:\n[ \t]+\S.*)*)", ficha)
    return m.group(1) if m else ""


def fichas(diagnostico: str) -> dict[str, str]:
    """{REF-nn: texto de la ficha} de las fichas `**REF-nn — …**`."""
    trozos = re.split(r"(?m)^\*\*(REF-\d+)\b", diagnostico)
    return {trozos[k]: trozos[k + 1] for k in range(1, len(trozos) - 1, 2)}


def nombra(texto: str, objeto: str) -> bool:
    formas = {objeto, objeto.replace(" ", "_")}
    return any(re.search(rf"(?<![\w]){re.escape(f)}(?![\w])", texto) for f in formas)


def secciones_bp(texto: str) -> set[str]:
    """Las «BP nn §x» de un texto, normalizadas («BP 5 §2» → «BP 05 §2»)."""
    return {f"BP {m.group(1).zfill(2)} §{m.group(2)}"
            for m in re.finditer(r"\bBP\s*(\d{1,2})\s*§\s*(\d(?:[\w.]*\w)?)", texto)}


def cuenta(mp: dict, refs: dict[str, str], solucion: str) -> tuple[bool, str]:
    aceptadas = secciones_bp(" ".join(mp["bp_aceptadas"]))
    candidatas = [r for r, f in refs.items() if any(nombra(campo(f, "Evidencia"), o) for o in mp["objetos"])]
    if not candidatas:
        return False, "ninguna REF cita sus objetos en la evidencia"
    con_regla = [r for r in candidatas if aceptadas & secciones_bp(campo(refs[r], "Regla"))]
    if not con_regla:
        citadas = sorted(set().union(*(secciones_bp(campo(refs[r], "Regla")) for r in candidatas)))
        return False, (f"{', '.join(candidatas)} cita sus objetos, pero con {', '.join(citadas) or 'otra regla'}; "
                       f"valen {', '.join(mp['bp_aceptadas'])}")
    en_solucion = [r for r in con_regla if re.search(rf"(?<![\w-]){re.escape(r)}(?!\d)", solucion)]
    if not en_solucion:
        return False, f"{', '.join(con_regla)} no sale en Solución"
    return True, ", ".join(en_solucion)


def nv_de_fuera(as_is: Path) -> list[str]:
    datos = as_is / "datos"
    deps = json.loads((datos / "dependencias.json").read_text(encoding="utf-8"))
    fuera = deps.get("fueraDeLaAplicacion") or []
    nombres = {f.get("nombre") for f in fuera}
    ids = {f["nv"] for f in fuera if f.get("nv")}
    sv = datos / "sin-verificar.json"
    if sv.exists():
        for nv in json.loads(sv.read_text(encoding="utf-8")).get("sinVerificar", []):
            if nombres & set(nv.get("objetos") or []):
                ids.add(nv["id"])
    return sorted(ids)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("propuesta")
    ap.add_argument("as_is")
    ap.add_argument("--ocultas", action="store_true")
    a = ap.parse_args()
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")
    propuesta, as_is = Path(a.propuesta), Path(a.as_is)
    esperadas = FICTICIA / ("ocultas" if a.ocultas else "") / "malas-practicas.json"
    faltan = [str(p) for p in (propuesta, as_is / "datos" / "dependencias.json", esperadas) if not p.is_file()]
    if faltan:
        print("No encuentro: " + ", ".join(faltan), file=sys.stderr)
        return 2
    texto = propuesta.read_text(encoding="utf-8")
    secciones = apartados(texto)
    refs = fichas(apartado(secciones, "diagnóstico"))
    solucion = apartado(secciones, "solución")
    pendientes = apartado(secciones, "pendientes")
    malas = json.loads(esperadas.read_text(encoding="utf-8"))
    bien = 0
    for mp in malas:
        ok, por_que = cuenta(mp, refs, solucion)
        bien += ok
        print(f"{'OK   ' if ok else 'FALLO'} {mp['id']} ({mp['bp']}): {por_que}")
    nvs = nv_de_fuera(as_is)
    sin_citar = [nv for nv in nvs if not re.search(rf"(?<![\w-]){re.escape(nv)}(?!\d)", pendientes)]
    print(f"Total: {bien}/{len(malas)} ({len(refs)} REF en el Diagnóstico)")
    if nvs:
        print(f"NV de fuera de la aplicación en Pendientes: {', '.join(nvs)}"
              + (f"; faltan {', '.join(sin_citar)}" if sin_citar else " (todos)"))
    return 0 if bien >= MINIMO * len(malas) and not sin_citar else 1


if __name__ == "__main__":
    sys.exit(main())
