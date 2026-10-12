#!/usr/bin/env python3
"""Dice qué filas del doc 14 de buenas prácticas hay que revisar porque la skill oficial de Appian ha cambiado.

  python3 pruebas/comprobar_divergencias.py [--oficial <carpeta de la skill appian>]

skills/appian-best-practices/references/14-official-skill-divergences.md lista lo que la skill oficial `appian`
(appian/dev-mcp-skills) dice en contra de la documentación. Appian actualiza esa skill a menudo, y una fila corregida
sobra. pruebas/divergencias-oficial.json lleva, por fila, el fichero de la oficial y una expresión regular (`marcador`)
que está mientras la divergencia siga viva; con `sin`, otra que no debe estar.

Un marcador que falta no prueba que Appian lo haya corregido: puede haber cambiado solo la redacción. Por eso el script
avisa y manda leerlo, no dice que la fila sobre. Si el marcador está en otro fichero, lo dice. Avisa también si algún
fichero de la skill oficial al que remite buenas prácticas ha dejado de existir. Se pasa al actualizar la skill oficial.

Por defecto mira ~/.claude/skills/appian. Es un aviso: código 0 salvo que falte la carpeta o no cuadren el JSON y el
doc 14 (2).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True

RAIZ = Path(__file__).resolve().parent.parent
DOC = RAIZ / "skills" / "appian-best-practices" / "references" / "14-official-skill-divergences.md"
MARCADORES = Path(__file__).resolve().parent / "divergencias-oficial.json"
SECCION = "## 1."  # la tabla de divergencias; las convenciones de la sección 2 no llevan marcador
PUNTERO = re.compile(r"`(?:references/)?([A-Za-z0-9-]+\.md)`")
VIVA = "viva"


def ruta_larga(p):
    """En Windows, la ruta con el prefijo que admite más de 260 caracteres: sin él, un fichero que existe en una carpeta
    profunda da «no existe», y aquí eso se leería como un marcador ausente."""
    s = str(p)
    return Path("\\\\?\\" + s) if sys.platform == "win32" and not s.startswith("\\\\") else p


def temas_del_doc():
    """La primera columna de la tabla de la sección 1 del doc 14."""
    texto = DOC.read_text(encoding="utf-8")
    tabla = texto[texto.index(SECCION):].split("\n## ", 1)[0]
    filas = [l for l in tabla.splitlines() if l.startswith("|") and not l.startswith("|---")]
    return [f.split("|")[1].strip() for f in filas[1:]]  # sin la cabecera


def punteros():
    """{fichero de la skill oficial: dónde lo cita buenas prácticas}. Es de la oficial un `nombre.md` entre comillas
    invertidas, solo o con `references/` delante, que no es de buenas prácticas (NN-nombre.md), ni SKILL.md, CLAUDE.md o
    AGENTS.md, ni un documento del proyecto (analisis/…, construccion/…)."""
    citados = {}
    for f in sorted(DOC.parent.parent.rglob("*.md")):
        for m in PUNTERO.finditer(f.read_text(encoding="utf-8")):
            nombre = m.group(1)
            if not re.match(r"\d\d-", nombre) and not nombre[:-3].isupper():
                citados.setdefault(nombre, f.relative_to(RAIZ).as_posix())
    return citados


def estado(regla, textos):
    """VIVA, o el aviso que toca. `textos` es {ruta relativa: contenido} de los .md de la skill oficial."""
    fichero = regla["fichero"]
    esta_en = [ruta for ruta, t in textos.items() if re.search(regla["marcador"], t)]
    if fichero in esta_en:
        if regla.get("sin") and re.search(regla["sin"], textos[fichero]):
            return f"{fichero} dice ahora algo que antes no decía; léelo: puede estar corregida"
        return VIVA
    if esta_en:
        return f"sigue viva, pero el texto está ahora en {', '.join(sorted(esta_en))}: cambia `fichero` en {MARCADORES.name}"
    falta = "ya no existe" if fichero not in textos else "ya no lo dice con esas palabras"
    return (f"{fichero} {falta}. Puede estar corregida o solo reescrita: léelo en la skill oficial antes de quitar "
            f"la fila del doc 14 y de {MARCADORES.name}")


def main() -> int:
    for s in (sys.stdout, sys.stderr):  # consolas de Windows sin UTF-8
        s.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--oficial", help="carpeta de la skill oficial, la que tiene SKILL.md (por defecto, ~/.claude/skills/appian)")
    a = ap.parse_args()
    oficial = Path(a.oficial).expanduser().resolve() if a.oficial else Path.home() / ".claude" / "skills" / "appian"
    larga = ruta_larga(oficial)
    if not (larga / "SKILL.md").is_file():
        print(f"No hay una skill en {oficial}: pásale su carpeta con --oficial.", file=sys.stderr)
        return 2

    reglas = json.loads(MARCADORES.read_text(encoding="utf-8"))
    temas, con_marcador = temas_del_doc(), [r["tema"] for r in reglas]
    descuadre = [f"fila del doc 14 sin marcador: {t}" for t in temas if t not in con_marcador]
    descuadre += [f"marcador sin fila en el doc 14: {t}" for t in con_marcador if t not in temas]
    if descuadre:
        print("\n".join(descuadre), file=sys.stderr)
        return 2

    textos = {f.relative_to(larga).as_posix(): f.read_text(encoding="utf-8", errors="replace")
              for f in sorted(larga.rglob("*.md"))}
    avisos = [(r["tema"], e) for r in reglas for e in [estado(r, textos)] if e != VIVA]
    for tema, aviso in avisos:
        print(f"Revisar «{tema}»: {aviso}.")
    print(f"{len(reglas) - len(avisos)} de {len(reglas)} divergencias siguen como estaban en {oficial}")

    estan = {Path(ruta).name for ruta in textos if ruta.startswith("references/")}
    citados = punteros()
    for nombre, donde in sorted(citados.items()):
        if nombre not in estan:
            print(f"Puntero roto: {donde} remite a `{nombre}`, que ya no está en la skill oficial.")
    print(f"{sum(1 for n in citados if n in estan)} de {len(citados)} ficheros de la skill oficial citados siguen en ella")
    return 0


if __name__ == "__main__":
    sys.exit(main())
