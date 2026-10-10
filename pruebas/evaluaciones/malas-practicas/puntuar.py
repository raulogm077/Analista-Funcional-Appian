#!/usr/bin/env python3
"""Puntúa una propuesta de refactorización contra las malas prácticas sembradas en la aplicación ficticia MNT.

Uso:
  python3 puntuar.py <propuesta.md> <as-is> [--ocultas]

Las malas prácticas están en ../aplicacion-ficticia/malas-practicas.json (con --ocultas, en
../aplicacion-ficticia/ocultas/malas-practicas.json), cada una con sus objetos, su «BP nn §x» y `bp_aceptadas`: las
secciones de buenas prácticas que tratan ese problema, empezando por la de `bp`.

Una mala práctica cuenta si hay una REF del Diagnóstico (las fichas que reconoce comprobar_propuesta.py: «**REF-01 —
…**», «### REF-01 · …») que:
  - cita en su Evidencia alguno de sus objetos, por su nombre exacto (vale también con «_» en lugar de los espacios,
    como en las rutas del anexo);
  - tiene en su Regla una de sus `bp_aceptadas`, la sección exacta («§1» no vale por «§1.3» si la lista no lo dice);
  - nombra el problema: su título, su Efecto o su Evidencia dicen alguna de sus claves (claves.json, junto a este
    fichero), sin tildes ni mayúsculas y al principio de una palabra («pagin» vale por «paginar» y «sin paginación»);
  - sale en el apartado Solución.
Una REF cuenta como mucho para una mala práctica: la que más claves dice en esos tres sitios y, a igualdad, la primera
de la lista.
Además, Pendientes tiene que citar los NV de <as-is>/datos/sin-verificar.json que tratan objetos de fuera de la
aplicación (`fueraDeLaAplicacion` de dependencias.json, con su campo `nv`): en MNT, el de las reglas CMN. Un as-is sin
esos NV no sirve para esta evaluación: no se puntúa.

Imprime cada mala práctica, el total y los NV. Sale 0 con el 90 % o más y los NV citados; 1 si no; 2 si falta un
fichero, las claves de una mala práctica o los NV de objetos de fuera en el as-is.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

sys.dont_write_bytecode = True
AQUI = Path(__file__).resolve().parent
FICTICIA = AQUI.parent / "aplicacion-ficticia"
CLAVES = AQUI / "claves.json"
PLUGIN = Path(os.environ.get("PLUGIN_A_PROBAR") or AQUI.parents[2]).resolve()
sys.path.insert(0, str(PLUGIN / "skills" / "appian-refactorizacion" / "scripts"))
from comprobar_propuesta import FICHA  # noqa: E402  (la ficha que reconoce la comprobación de la skill)

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
    """{REF-nn: texto de la ficha, desde la línea de su título} de las fichas que reconoce FICHA."""
    out, actual = {}, None
    for linea in diagnostico.splitlines():
        m = FICHA.match(linea.replace("**", "").strip())
        if m:
            actual = m.group(1)
            out.setdefault(actual, "")
        if actual:
            out[actual] += linea + "\n"
    return out


def normal(texto: str) -> str:
    """Sin tildes ni mayúsculas, con un espacio entre palabras."""
    t = unicodedata.normalize("NFKD", texto)
    return " ".join("".join(c for c in t if not unicodedata.combining(c)).lower().split())


def claves_que_dice(ficha: str, claves: list[str]) -> int:
    """Cuántas claves dicen el título, el Efecto y la Evidencia de la ficha, cada una al principio de una palabra."""
    texto = normal(" ".join((ficha.split("\n", 1)[0], campo(ficha, "Efecto"), campo(ficha, "Evidencia"))))
    return sum(bool(re.search(rf"(?<!\w){re.escape(normal(c))}", texto)) for c in claves)


def nombra(texto: str, objeto: str) -> bool:
    formas = {objeto, objeto.replace(" ", "_")}
    return any(re.search(rf"(?<![\w]){re.escape(f)}(?![\w])", texto) for f in formas)


def secciones_bp(texto: str) -> set[str]:
    """Las «BP nn §x» de un texto, normalizadas («BP 5 §2» → «BP 05 §2»)."""
    return {f"BP {m.group(1).zfill(2)} §{m.group(2)}"
            for m in re.finditer(r"\bBP\s*(\d{1,2})\s*§\s*(\d(?:[\w.]*\w)?)", texto)}


def cuenta(mp: dict, claves: list[str], refs: dict[str, str], solucion: str) -> tuple[list[str], str]:
    """(las REF que valen para la mala práctica, por qué no vale ninguna)."""
    aceptadas = secciones_bp(" ".join(mp["bp_aceptadas"]))
    candidatas = [r for r, f in refs.items() if any(nombra(campo(f, "Evidencia"), o) for o in mp["objetos"])]
    if not candidatas:
        return [], "ninguna REF cita sus objetos en la evidencia"
    con_regla = [r for r in candidatas if aceptadas & secciones_bp(campo(refs[r], "Regla"))]
    if not con_regla:
        citadas = sorted(set().union(*(secciones_bp(campo(refs[r], "Regla")) for r in candidatas)))
        return [], (f"{', '.join(candidatas)} cita sus objetos, pero con {', '.join(citadas) or 'otra regla'}; "
                       f"valen {', '.join(mp['bp_aceptadas'])}")
    nombran = [r for r in con_regla if claves_que_dice(refs[r], claves)]
    if not nombran:
        return [], (f"{', '.join(con_regla)} cita sus objetos y su regla, pero ni su título, ni su Efecto ni su "
                       f"Evidencia nombran el problema (claves: {', '.join(claves)})")
    en_solucion = [r for r in nombran if re.search(rf"(?<![\w-]){re.escape(r)}(?!\d)", solucion)]
    if not en_solucion:
        return [], f"{', '.join(nombran)} no sale en Solución"
    return en_solucion, ""


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
    faltan = [str(p) for p in (propuesta, as_is / "datos" / "dependencias.json", esperadas, CLAVES)
              if not p.is_file()]
    if faltan:
        print("No encuentro: " + ", ".join(faltan), file=sys.stderr)
        return 2
    malas = json.loads(esperadas.read_text(encoding="utf-8"))
    claves = json.loads(CLAVES.read_text(encoding="utf-8"))
    sin_claves = [mp["id"] for mp in malas if not claves.get(mp["id"])]
    if sin_claves:
        print(f"{CLAVES.name} no tiene claves para {', '.join(sin_claves)}", file=sys.stderr)
        return 2
    nvs = nv_de_fuera(as_is)
    if not nvs:
        print("El as-is no trae NV de objetos de fuera (fueraDeLaAplicacion de dependencias.json, con su NV): no sirve "
              "para esta evaluación", file=sys.stderr)
        return 2
    texto = propuesta.read_text(encoding="utf-8")
    secciones = apartados(texto)
    refs = fichas(apartado(secciones, "diagnóstico"))
    solucion = apartado(secciones, "solución")
    pendientes = apartado(secciones, "pendientes")
    validas = {mp["id"]: cuenta(mp, claves[mp["id"]], refs, solucion) for mp in malas}
    duena = {}   # cada REF, para una sola mala práctica: la que más claves dice; a igualdad, la primera de la lista
    for ref in refs:
        aspirantes = [mp["id"] for mp in malas if ref in validas[mp["id"]][0]]
        if aspirantes:
            duena[ref] = max(aspirantes, key=lambda i: claves_que_dice(refs[ref], claves[i]))
    bien = 0
    for mp in malas:
        suyas, por_que = validas[mp["id"]]
        cuentan = [r for r in suyas if duena[r] == mp["id"]]
        if suyas and not cuentan:
            por_que = (f"{', '.join(suyas)} cuenta ya para {', '.join(sorted({duena[r] for r in suyas}))}, que dice "
                       "más claves: una REF cuenta para una sola mala práctica")
        bien += bool(cuentan)
        print(f"{'OK   ' if cuentan else 'FALLO'} {mp['id']} ({mp['bp']}): {', '.join(cuentan) or por_que}")
    sin_citar = [nv for nv in nvs if not re.search(rf"(?<![\w-]){re.escape(nv)}(?!\d)", pendientes)]
    print(f"Total: {bien}/{len(malas)} ({len(refs)} REF en el Diagnóstico)")
    print(f"NV de fuera de la aplicación en Pendientes: {', '.join(nvs)}"
          + (f"; faltan {', '.join(sin_citar)}" if sin_citar else " (todos)"))
    return 0 if bien >= MINIMO * len(malas) and not sin_citar else 1


if __name__ == "__main__":
    sys.exit(main())
