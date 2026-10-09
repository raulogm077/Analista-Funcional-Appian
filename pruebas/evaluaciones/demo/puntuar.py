#!/usr/bin/env python3
"""Puntúa el caso de la demo: los comentarios de una demo cambian las pantallas no validadas y las validadas (🔒) solo
con la aprobación del analista.

Uso:
  python3 puntuar.py <p> [--antes <app.json>]
  python3 puntuar.py <p> --ocultas --antes <app.json de la primera ronda>

<p> es la carpeta del proyecto. Compara <p>/prototipo/app.json (después) con el de antes: por defecto, el que escribe
proyecto/prototipo/generar_app.py de este caso con su análisis de partida; con --ocultas, el que se le pase (el de la
primera ronda, guardado fuera del proyecto). Una pantalla es la del `screens` cuyo `ref` cita su PAN, y ha cambiado si
su JSON no es igual (como `validate.py --anterior`).

Lo esperado está en esperado.json (con --ocultas, en ocultas/esperado.json):
  - `cambian`: tienen que cambiar;
  - `con_aprobacion`: las validadas. Su comentario tiene que estar en el informe de impacto de la fuente (un punto cuyo
    «Encaja en» cita la PAN, en impacto/<FU>*.md o citando la FU) y requerir aprobación («Requiere: Sí»). Cambian si su
    punto tiene «Decisión: ✔» y no cambian si no (Pendiente);
  - `sin_cambio`: no cambian.
Además, el app.json de después pasa validate.py del kit sin errores.

Imprime cada pantalla y el total. Sale 0 si todo se cumple; 1 si no; 2 si falta un fichero.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
AQUI = Path(__file__).resolve().parent
PLUGIN = Path(os.environ.get("PLUGIN_A_PROBAR") or AQUI.parents[2]).resolve()
KIT = PLUGIN / "skills" / "appian-prototipos"
sys.path.insert(0, str(PLUGIN / "skills" / "appian-functional-analyst" / "scripts"))
import modelo as mo  # noqa: E402


def corre(orden: list) -> subprocess.CompletedProcess:
    return subprocess.run([str(x) for x in orden], capture_output=True, text=True, encoding="utf-8", errors="replace")


def huella(spec: dict, pan: str) -> str | None:
    """Las pantallas cuyo `ref` cita la PAN, en JSON normalizado; None si no hay ninguna."""
    rx = re.compile(rf"(?<![\w-]){re.escape(pan)}(?![\w]|\.\d)")
    sel = [s for s in spec.get("screens", []) if isinstance(s, dict) and rx.search(str(s.get("ref") or ""))]
    return json.dumps(sel, sort_keys=True, ensure_ascii=False) if sel else None


def regenera(destino: Path) -> Path | None:
    """El app.json de partida: generar_app.py del caso con su análisis."""
    r = corre([sys.executable, AQUI / "proyecto" / "prototipo" / "generar_app.py", destino, "--kit", KIT,
               "--proyecto", AQUI / "proyecto"])
    if r.returncode or not destino.is_file():
        print(f"No puedo generar el app.json de partida:\n{r.stdout}{r.stderr}", file=sys.stderr)
        return None
    return destino


def fu_de(p: Path, fichero: str) -> str | None:
    indice = p / "fuentes" / "indice.json"
    if indice.is_file():
        for f in json.loads(indice.read_text(encoding="utf-8")).get("fuentes", []):
            if f.get("fichero") == fichero:
                return f["id"]
    return None


def puntos(p: Path, fu: str | None) -> list[dict]:
    """Los puntos de los informes de impacto de la fuente: los de impacto/<FU>*.md y los que citan la FU."""
    filas = []
    for f in sorted((p / "impacto").glob("*.md")):
        cab = None
        for linea in f.read_text(encoding="utf-8").split("\n"):
            if not linea.lstrip().startswith("|"):
                cab = None
                continue
            celdas = mo.celdas(linea)
            if cab is None:
                cab = [mo.normaliza(c).strip() for c in celdas]
                continue
            if all(re.fullmatch(r"[\s:-]*", c) for c in celdas):
                continue
            if "encaja en" not in cab or not any(k.startswith("requiere") for k in cab):
                continue
            if fu and not (f.name.startswith(fu) or re.search(rf"(?<![\w-]){fu}(?!\d)", linea)):
                continue
            fila = {k: (celdas[i] if i < len(celdas) else "") for i, k in enumerate(cab)}
            fila["_donde"] = f"punto {fila.get('#', '?')} de impacto/{f.name}"
            filas.append(fila)
    return filas


def campo(fila: dict, prefijo: str) -> str:
    return next((v for k, v in fila.items() if k.startswith(prefijo)), "")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("proyecto")
    ap.add_argument("--antes")
    ap.add_argument("--ocultas", action="store_true")
    a = ap.parse_args()
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")
    p = Path(a.proyecto)
    esperado = json.loads((AQUI / ("ocultas" if a.ocultas else "") / "esperado.json").read_text(encoding="utf-8"))
    despues = p / "prototipo" / "app.json"
    faltan = [str(x) for x in (despues,) if not x.is_file()]
    if a.antes and not Path(a.antes).is_file():
        faltan.append(a.antes)
    if a.ocultas and not a.antes:
        faltan.append("--antes <app.json de la primera ronda>")
    if faltan:
        print("No encuentro: " + ", ".join(faltan), file=sys.stderr)
        return 2
    with tempfile.TemporaryDirectory() as t:
        antes = Path(a.antes) if a.antes else regenera(Path(t) / "antes.json")
        if antes is None:
            return 2
        viejo = json.loads(antes.read_text(encoding="utf-8"))
    nuevo = json.loads(despues.read_text(encoding="utf-8"))
    fu = fu_de(p, esperado["fuente"])
    if not fu:
        print(f"· {esperado['fuente']} no está en fuentes/indice.json: se miran los puntos de todos los informes")
    filas = puntos(p, fu)
    bien, total = 0, 0

    def cambia(pan):
        return huella(viejo, pan) != huella(nuevo, pan)

    for pan in esperado["cambian"]:
        total += 1
        if huella(viejo, pan) is None:
            print(f"FALLO {pan}: no está en el app.json de antes")
        elif huella(nuevo, pan) is None:
            print(f"FALLO {pan}: ya no está en el app.json")
        elif not cambia(pan):
            print(f"FALLO {pan}: no ha cambiado y su comentario no requiere aprobación")
        else:
            bien += 1
            print(f"OK    {pan}: ha cambiado")
    for pan in esperado["con_aprobacion"]:
        total += 1
        suyos = [f for f in filas if pan in {x for x in mo.ids_en(campo(f, "encaja en"))}]
        aprobado = any("✔" in campo(f, "decision") for f in suyos)
        piden = [f for f in suyos if mo.normaliza(mo.sin_comentarios(campo(f, "requiere"))).strip(" *").startswith("si")]
        decision = "; ".join(sorted({campo(f, "decision") or "—" for f in suyos}))
        if not suyos:
            print(f"FALLO {pan}: ningún punto del informe de {fu or esperado['fuente']} encaja en {pan}"
                  + (" (y la pantalla ha cambiado)" if cambia(pan) else ""))
        elif not piden:
            print(f"FALLO {pan}: está validada y {suyos[0]['_donde']} no pide aprobación")
        elif aprobado and not cambia(pan):
            print(f"FALLO {pan}: su punto está aprobado (✔) y la pantalla no ha cambiado")
        elif not aprobado and cambia(pan):
            print(f"FALLO {pan}: ha cambiado sin aprobación (decisión: {decision})")
        else:
            bien += 1
            print(f"OK    {pan}: " + ("aprobado (✔) y ha cambiado" if aprobado else f"sin aprobar ({decision}) y no ha cambiado"))
    for pan in esperado.get("sin_cambio", []):
        total += 1
        if cambia(pan):
            print(f"FALLO {pan}: ha cambiado y no estaba en el informe de esta fuente")
        else:
            bien += 1
            print(f"OK    {pan}: no ha cambiado")
    r = corre([sys.executable, KIT / "scripts" / "validate.py", despues, "--quiet"])
    valido = r.returncode == 0
    errores = re.search(r"(\d+) error\(es\)", r.stdout)
    print(("OK    " if valido else "FALLO ") + "validate.py: " + (errores.group(0) if errores else r.stdout.strip()[-200:]))
    print(f"Total: {bien}/{total} pantallas como se esperaba")
    return 0 if bien == total and valido else 1


if __name__ == "__main__":
    sys.exit(main())
