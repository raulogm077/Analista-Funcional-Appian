#!/usr/bin/env python3
"""Prueba de enrutado: el enunciado para el agente que enruta y la puntuación de sus respuestas.

Uso:
  python3 puntuar.py --enunciado [--ocultas | --fronteras]   # las seis descripciones y las peticiones, sin la skill
  python3 puntuar.py <respuestas.json> [--ocultas | --fronteras]

Las peticiones visibles están en pruebas/enrutado.json, las ocultas en ocultas/enrutado.json y las de las fronteras
(los solapes más probables, sin las palabras que delatan la skill) en fronteras/enrutado.json, las tres con el formato
[{"peticion": "…", "skill": "appian-…"}]. Las respuestas tienen el mismo formato y el mismo orden, una por petición y
con la petición copiada tal cual. Vale la skill con el prefijo del plugin («appian-analisis-funcional:appian-…»).

Imprime cada petición con la skill esperada y la elegida, y el total. Sale 0 si coinciden todas; 1 si falla alguna;
2 si falta un fichero o las respuestas no se pueden comparar (otro número, otro orden u otro formato).
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
REPO = AQUI.parents[2]
PLUGIN = Path(os.environ.get("PLUGIN_A_PROBAR") or REPO).resolve()
VISIBLES = REPO / "pruebas" / "enrutado.json"
OCULTAS = AQUI / "ocultas" / "enrutado.json"
FRONTERAS = AQUI / "fronteras" / "enrutado.json"
SKILLS = PLUGIN / "skills"


class Formato(Exception):
    """Respuestas que no se pueden comparar con lo esperado."""


def normal(texto: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", texto)).strip()


def skill_de(valor: str) -> str:
    """«appian-analisis-funcional:appian-prototipos» o «`appian-prototipos`» → «appian-prototipos»."""
    return valor.strip().strip("`").rsplit(":", 1)[-1].strip().lower()


def lee_lista(ruta: Path) -> list[dict]:
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    if not isinstance(datos, list) or not all(isinstance(d, dict) and isinstance(d.get("peticion"), str)
                                              and isinstance(d.get("skill"), str) for d in datos):
        raise Formato(f"{ruta.name}: tiene que ser una lista de {{\"peticion\": \"…\", \"skill\": \"…\"}}")
    return datos


def descripcion(skill_md: Path) -> str:
    """El `description` del frontmatter, en una línea y sin comillas."""
    m = re.match(r"^---\n(.*?)\n---\n", skill_md.read_text(encoding="utf-8"), re.S)
    campos, actual = {}, None
    for linea in (m.group(1).splitlines() if m else []):
        if re.match(r"^[a-z-]+:", linea):
            actual, _, valor = linea.partition(":")
            campos[actual] = valor.strip()
        elif actual:
            campos[actual] += " " + linea.strip()
    valor = campos.get("description", "").lstrip(">|").strip()
    if len(valor) > 1 and valor[0] == valor[-1] and valor[0] in "\"'":
        valor = valor[1:-1].replace('\\"', '"') if valor[0] == '"' else valor[1:-1].replace("''", "'")
    return valor


def enunciado(peticiones: list[dict]) -> str:
    skills = []
    for md in sorted(SKILLS.glob("*/SKILL.md")):
        texto = descripcion(md)
        if not texto:
            raise Formato(f"{md.relative_to(PLUGIN).as_posix()} no tiene description")
        skills.append(f"- `{md.parent.name}`: {texto}")
    return ("# Enrutado de peticiones\n\n"
            "Decide qué skill atiende cada petición. Solo conoces estas skills, por su descripción. Cada petición entra "
            "por una sola skill: la que se ocupa de lo que se pide; las demás se usan desde ella. No expliques nada.\n\n"
            "Devuelve solo un JSON con una entrada por petición, en el mismo orden y con la petición copiada tal cual:\n"
            '[{"peticion": "…", "skill": "appian-…"}]\n\n'
            "## Skills\n\n" + "\n".join(skills) + "\n\n## Peticiones\n\n"
            + json.dumps([p["peticion"] for p in peticiones], ensure_ascii=False, indent=2) + "\n")


def compara(esperadas: list[dict], respuestas: list[dict]) -> list[tuple[int, str, str, str]]:
    """(número, petición, esperada, elegida) de cada petición; Formato si no se pueden comparar."""
    if len(respuestas) != len(esperadas):
        raise Formato(f"hay {len(respuestas)} respuestas para {len(esperadas)} peticiones")
    otras = [str(k) for k, (e, r) in enumerate(zip(esperadas, respuestas), 1)
             if normal(e["peticion"]) != normal(r["peticion"])]
    if otras:
        raise Formato("la petición de la respuesta no es la de su número, o no está copiada tal cual, en "
                      + ", ".join(otras))
    return [(k, e["peticion"], e["skill"], skill_de(r["skill"]))
            for k, (e, r) in enumerate(zip(esperadas, respuestas), 1)]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("respuestas", nargs="?")
    lote = ap.add_mutually_exclusive_group()
    lote.add_argument("--ocultas", action="store_true", help="las peticiones ocultas en vez de las visibles")
    lote.add_argument("--fronteras", action="store_true", help="las peticiones de las fronteras en vez de las visibles")
    ap.add_argument("--enunciado", action="store_true", help="imprime lo que recibe el agente que enruta")
    a = ap.parse_args()
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")
    if bool(a.enunciado) == bool(a.respuestas):
        ap.error("o --enunciado o un fichero de respuestas")
    esperado = OCULTAS if a.ocultas else FRONTERAS if a.fronteras else VISIBLES
    faltan = [str(p) for p in (esperado, Path(a.respuestas or esperado)) if not p.is_file()]
    if faltan:
        print("No encuentro: " + ", ".join(faltan), file=sys.stderr)
        return 2
    try:
        esperadas = lee_lista(esperado)
        if a.enunciado:
            print(enunciado(esperadas), end="")
            return 0
        filas = compara(esperadas, lee_lista(Path(a.respuestas)))
    except (Formato, json.JSONDecodeError) as e:
        print(f"No se puede puntuar: {e}", file=sys.stderr)
        return 2
    validas = {md.parent.name for md in SKILLS.glob("*/SKILL.md")}
    bien = 0
    for k, peticion, esperada, elegida in filas:
        ok = elegida == esperada
        bien += ok
        if ok:
            print(f"OK    {k:2d} {esperada}")
        else:
            otra = elegida if elegida in validas else f"«{elegida}» (no es una de las skills)"
            print(f"FALLO {k:2d} esperada {esperada}, elegida {otra}: {peticion}")
    print(f"Total: {bien}/{len(filas)}" + (" (ocultas)" if a.ocultas else " (fronteras)" if a.fronteras else ""))
    return 0 if bien == len(filas) else 1


if __name__ == "__main__":
    sys.exit(main())
