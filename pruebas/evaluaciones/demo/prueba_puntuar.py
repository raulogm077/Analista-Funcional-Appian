#!/usr/bin/env python3
"""Prueba de puntuar.py con proyectos inventados: `python3 prueba_puntuar.py`. Sale 0 si todo va bien.

Primero comprueba el propio caso: el análisis de partida pasa comprobar.py, sus pantallas validadas (🔒) son las de
`con_aprobacion`, generar_app.py escribe siempre el mismo app.json y validate.py lo da por bueno, y cada comentario
de lo esperado es una intervención de la demo. Después monta proyectos con el app.json de partida cambiado en unas
pantallas y un informe de impacto, y mira la salida de puntuar.py."""
from __future__ import annotations

import copy
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
ANALISTA = PLUGIN / "skills" / "appian-functional-analyst" / "scripts"
sys.path.insert(0, str(ANALISTA))
import modelo as mo  # noqa: E402

PUNTUAR = AQUI / "puntuar.py"
VISIBLE = json.loads((AQUI / "esperado.json").read_text(encoding="utf-8"))
OCULTO = json.loads((AQUI / "ocultas" / "esperado.json").read_text(encoding="utf-8"))
FUENTES = ["01-reunion-2026-09-15.txt", "02-correo-2026-09-29-validacion.eml", VISIBLE["fuente"], OCULTO["fuente"]]


def corre(*orden) -> tuple[int, str]:
    r = subprocess.run([str(x) for x in orden], capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, r.stdout + r.stderr


def genera(destino: Path) -> dict:
    c, salida = corre(sys.executable, AQUI / "proyecto" / "prototipo" / "generar_app.py", destino, "--kit", KIT)
    if c:
        sys.exit(f"generar_app.py falla:\n{salida}")
    return json.loads(destino.read_text(encoding="utf-8"))


def cambia(spec: dict, pans, invalido=False, nota="Cambiada tras la demo") -> dict:
    """Una copia del spec con las pantallas de esas PAN cambiadas (una nota más); con invalido, un componente que no existe."""
    s = copy.deepcopy(spec)
    for pantalla in s["screens"]:
        if any(re.search(rf"(?<![\w-]){p}(?!\d)", pantalla.get("ref", "")) for p in pans):
            pantalla["$note"] = nota
    if invalido:
        s["screens"][0]["interface"]["contents"].append({"type": "a!campoInventadoField", "label": "No existe"})
    return s


def fila(n, pan, requiere="—", decision="✔") -> str:
    return (f"| {n} | CAMBIA | «Comentario de la demo» [FU-03 00:01:45] | {pan} | Cambia {pan} | — | {requiere} "
            f"| {decision} |")


def informe(fu, decisiones: dict, quitar=(), sin_pedir=()) -> str:
    """decisiones = {PAN validada: «Pendiente» o «✔»}; el resto, retoques sin aprobación."""
    filas = []
    for n, c in enumerate(VISIBLE["comentarios"], 1):
        pan = c["pan"]
        if pan in quitar:
            continue
        if pan in decisiones and pan not in sin_pedir:
            filas.append(fila(n, pan, "Sí (🔒)", decisiones[pan]))
        else:
            filas.append(fila(n, pan))
    return (f"# Impacto de {fu} · Demo del prototipo\n\n## Puntos\n\n| # | Tipo | Qué se dice | Encaja en | Cambio propuesto "
            "| Revisar también | Requiere | Decisión |\n|---|---|---|---|---|---|---|---|\n" + "\n".join(filas) + "\n")


def proyecto(raiz: Path, spec: dict | None, inf: str | None = None, extra: str | None = None) -> Path:
    p = raiz / f"Carpeta con espacios {len(list(raiz.iterdir())) + 1}" / "Gestión app"
    for d in ("fuentes", "impacto", "prototipo"):
        (p / d).mkdir(parents=True)
    (p / "fuentes" / "indice.json").write_text(json.dumps({"fuentes": [
        {"id": f"FU-{k:02d}", "fichero": f} for k, f in enumerate(FUENTES, 1)]}), encoding="utf-8")
    if spec is not None:
        (p / "prototipo" / "app.json").write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
    (p / "impacto" / "FU-03.md").write_text(inf or informe("FU-03", {"PAN-02": "Pendiente", "PAN-05": "Pendiente"}),
                                           encoding="utf-8")
    if extra:
        (p / "impacto" / "FU-04.md").write_text(extra, encoding="utf-8")
    return p


def comprobar_caso(t: Path, antes: dict) -> list[str]:
    mal = []
    c, salida = corre(sys.executable, ANALISTA / "comprobar.py", AQUI / "proyecto")
    if c:
        mal.append(f"el análisis de partida no pasa comprobar.py:\n{salida}")
    m = mo.Proyecto(AQUI / "proyecto")
    validadas = sorted(p.id for p in m.vigentes("PAN") if p.estado == "🔒")
    if validadas != sorted(VISIBLE["con_aprobacion"]):
        mal.append(f"pantallas 🔒 del funcional {validadas} ≠ con_aprobacion {VISIBLE['con_aprobacion']}")
    otra = genera(t / "otra vez.json")
    if otra != antes:
        mal.append("generar_app.py no escribe siempre el mismo app.json")
    c, salida = corre(sys.executable, KIT / "scripts" / "validate.py", t / "antes.json")
    if c or "0 error(es), 0 aviso(s)" not in salida:
        mal.append(f"validate.py no da por bueno el app.json de partida:\n{salida}")
    refs = " ".join(s.get("ref", "") for s in antes["screens"])
    pans = sorted(p.id for p in m.vigentes("PAN"))
    for pan in pans:
        if pan not in refs:
            mal.append(f"{pan} no tiene pantalla en el prototipo")
    todas = VISIBLE["cambian"] + VISIBLE["con_aprobacion"]
    if sorted(todas) != pans or sorted(OCULTO["cambian"] + OCULTO["sin_cambio"]) != pans:
        mal.append("lo esperado no reparte las seis pantallas")
    marcas = re.findall(r"(?m)^\[(\d{2}:\d{2}:\d{2})\]", (AQUI / VISIBLE["fuente"]).read_text(encoding="utf-8"))
    mal += [f"{c['pan']}: {c['minuto']} no es una intervención de la demo" for c in VISIBLE["comentarios"]
            if c["minuto"] not in marcas]
    if sorted(c["pan"] for c in VISIBLE["comentarios"]) != pans:
        mal.append("la demo no tiene un comentario por pantalla")
    return mal


def main() -> int:
    fallos = 0
    with tempfile.TemporaryDirectory(prefix="puntuar con espacios ") as t:
        t = Path(t)
        antes = genera(t / "antes.json")
        mal = comprobar_caso(t, antes)
        fallos += bool(mal)
        print(("OK   " if not mal else "FALLO ") + "el caso: análisis, prototipo de partida y demo" + "".join(f"\n  {x}" for x in mal))
        raiz = t / "proyectos"
        raiz.mkdir()
        cuatro = VISIBLE["cambian"]
        ronda1 = cambia(antes, cuatro)
        (t / "ronda1.json").write_text(json.dumps(ronda1, ensure_ascii=False), encoding="utf-8")
        oculto = informe("FU-04", {}).replace("FU-03", "FU-04")
        casos = [
            ("cambian las cuatro y las validadas, pendientes, no", proyecto(raiz, ronda1), (), 0, "Total: 6/6"),
            ("una validada aprobada (✔) que cambia", proyecto(raiz, cambia(antes, cuatro + ["PAN-02"]),
                                                              informe("FU-03", {"PAN-02": "✔", "PAN-05": "Pendiente"})),
             (), 0, "PAN-02: aprobado (✔) y ha cambiado"),
            ("una no validada que no cambia", proyecto(raiz, cambia(antes, cuatro[:-1])), (), 1, f"{cuatro[-1]}: no ha cambiado"),
            ("una validada que cambia sin aprobación", proyecto(raiz, cambia(antes, cuatro + ["PAN-05"])), (), 1,
             "PAN-05: ha cambiado sin aprobación (decisión: Pendiente)"),
            ("una validada aprobada que no cambia", proyecto(raiz, ronda1, informe("FU-03", {"PAN-02": "Pendiente", "PAN-05": "✔"})),
             (), 1, "PAN-05: su punto está aprobado (✔) y la pantalla no ha cambiado"),
            ("una validada sin punto en el informe", proyecto(raiz, ronda1, informe("FU-03", {"PAN-02": "Pendiente"},
                                                                                     quitar=["PAN-05"])),
             (), 1, "PAN-05: ningún punto del informe"),
            ("una validada cuyo punto no pide aprobación",
             proyecto(raiz, ronda1, informe("FU-03", {"PAN-02": "Pendiente", "PAN-05": "Pendiente"}, sin_pedir=["PAN-02"])),
             (), 1, "PAN-02: está validada y"),
            ("un app.json que validate.py no acepta", proyecto(raiz, cambia(antes, cuatro, invalido=True)), (), 1,
             "FALLO validate.py"),
            ("--ocultas: solo cambia PAN-03", proyecto(raiz, cambia(ronda1, ["PAN-03"], nota="Tras el correo"), extra=oculto),
             ("--ocultas", "--antes", t / "ronda1.json"), 0, "Total: 6/6"),
            ("--ocultas: cambia otra más", proyecto(raiz, cambia(ronda1, ["PAN-03", "PAN-06"], nota="Tras el correo"), extra=oculto),
             ("--ocultas", "--antes", t / "ronda1.json"), 1, "PAN-06: ha cambiado y no estaba"),
            ("--ocultas sin --antes sale con 2", proyecto(raiz, ronda1), ("--ocultas",), 2, "--antes"),
            ("sin app.json sale con 2", proyecto(raiz, None), (), 2, "No encuentro"),
        ]
        for nombre, p, extra, codigo, debe in casos:
            c, salida = corre(sys.executable, PUNTUAR, p, *extra)
            bien = c == codigo and debe in salida
            fallos += not bien
            print(("OK   " if bien else "FALLO ") + nombre + ("" if bien else f" (sale {c}):\n{salida}"))
    print("Todo bien" if not fallos else f"{fallos} fallos")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
