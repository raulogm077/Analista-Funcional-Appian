#!/usr/bin/env python3
"""Prueba de puntuar.py con una propuesta inventada: `python3 prueba_puntuar.py`. Sale 0 si todo va bien.

La propuesta trata las 11 malas prácticas visibles de MNT y cita el NV de los objetos CMN; cada caso la rompe de una
forma y mira la salida de puntuar.py."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
AQUI = Path(__file__).resolve().parent
PUNTUAR = AQUI / "puntuar.py"
MALAS = json.loads((AQUI.parent / "aplicacion-ficticia" / "malas-practicas.json").read_text(encoding="utf-8"))


def propuesta(quitar_solucion=(), regla_otra=(), sin_nv=False, solo_titulo=()) -> str:
    fichas, filas = [], []
    for k, mp in enumerate(MALAS, 1):
        ref = f"REF-{k:02d}"
        doc, sec = mp["bp"].split(" ")[1], mp["bp"].split("§")[1]
        if mp["id"] in regla_otra:
            doc = "99" if doc != "99" else "98"
        objetos = " y ".join(f"`{o}`" for o in mp["objetos"])
        if mp["id"] in solo_titulo:   # el objeto en el título, no en la evidencia
            fichas.append(f"**{ref} — Problema de {objetos}**\n\n- Evidencia: H-XXX-01 ✅ lo muestra el anexo\n"
                          f"- Regla: BP {doc} §{sec}\n- Efecto: x\n- Prioridad: Media\n- Esfuerzo: S, poco\n")
        else:
            fichas.append(f"**{ref} — Problema**\n\n- Evidencia: H-XXX-01 ✅ {objetos} · "
                          f"[`mcp:x/{mp['objetos'][0]}#a`](../as-is/anexo/x/{mp['objetos'][0].replace(' ', '_')}.md)\n"
                          f"- Regla: BP {doc} §{sec}\n- Efecto: x\n- Prioridad: Media\n- Esfuerzo: S, poco\n")
        if mp["id"] not in quitar_solucion:
            filas.append(f"| Datos | algo | {ref}: porque sí (BP {doc} §{sec}) | nada |")
    pendientes = "| ID | Qué falta | Quién | Condiciona |\n|---|---|---|---|\n"
    if not sin_nv:
        pendientes += "| NV-ARQ-01 | ¿Qué hacen las reglas CMN? | Equipo | REF-02 |\n"
    return ("# Propuesta\n\n## 1. Alcance\n\nTodo.\n\n## 2. Diagnóstico\n\n" + "\n".join(fichas)
            + "\n## 3. Solución\n\n| Capa | Qué se hace | Por qué | Se descarta |\n|---|---|---|---|\n"
            + "\n".join(filas) + "\n\n## 4. Migración y convivencia\n\nNueva.\n\n## 5. Hoja de ruta\n\n"
            + "| Fase | Qué | Depende de |\n|---|---|---|\n| 1 | REF-01 | — |\n\n## 6. Pendientes\n\n" + pendientes)


def as_is(carpeta: Path) -> Path:
    datos = carpeta / "as-is" / "datos"
    datos.mkdir(parents=True)
    (datos / "dependencias.json").write_text(json.dumps({"aristas": [], "fueraDeLaAplicacion": [
        {"nombre": "CMN_UsuarioActual", "tipo": "llamado con rule!", "usadoPor": ["MNT_PM_GestionOrden"], "usa": [],
         "nv": "NV-ARQ-01"}]}), encoding="utf-8")
    (datos / "sin-verificar.json").write_text(json.dumps({"sinVerificar": [
        {"id": "NV-ARQ-01", "objetos": ["MNT_PM_GestionOrden", "CMN_UsuarioActual"], "pregunta": "¿?"},
        {"id": "NV-PRO-01", "objetos": ["MNT_PM_GestionOrden"], "pregunta": "¿?"}]}), encoding="utf-8")
    return carpeta / "as-is"


def corre(texto: str, carpeta: Path, *extra) -> tuple[int, str]:
    p = carpeta / "refactorizacion" / "propuesta.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(texto, encoding="utf-8")
    r = subprocess.run([sys.executable, str(PUNTUAR), str(p), str(carpeta / "as-is"), *extra],
                       capture_output=True, text=True, encoding="utf-8")
    return r.returncode, r.stdout + r.stderr


def main() -> int:
    fallos = 0
    with tempfile.TemporaryDirectory(prefix="puntuar con espacios ") as t:
        carpeta = Path(t)
        as_is(carpeta)
        casos = [
            ("las 11 y el NV", propuesta(), 0, "11/11"),
            ("una sin Solución: 10/11 basta", propuesta(quitar_solucion=["MP-05"]), 0, "10/11"),
            ("dos sin Solución: 9/11 no basta", propuesta(quitar_solucion=["MP-05", "MP-06"]), 1, "9/11"),
            ("regla de otro documento no cuenta", propuesta(regla_otra=["MP-01", "MP-02"]), 1, "9/11"),
            ("objeto solo en el título no cuenta", propuesta(solo_titulo=["MP-03", "MP-04"]), 1, "9/11"),
            ("sin el NV de CMN no pasa", propuesta(sin_nv=True), 1, "NV-ARQ-01"),
        ]
        for nombre, texto, codigo, debe in casos:
            c, salida = corre(texto, carpeta)
            bien = c == codigo and debe in salida
            fallos += not bien
            print(("OK   " if bien else "FALLO ") + nombre + ("" if bien else f" (sale {c}):\n{salida}"))
        c, salida = corre(propuesta(), carpeta, "--ocultas")
        bien = c == 1 and "MPO-03" in salida and "/3 (" in salida   # las ocultas, no las visibles
        fallos += not bien
        print(("OK   " if bien else "FALLO ") + "--ocultas lee las ocultas" + ("" if bien else f" (sale {c}):\n{salida}"))
        c, salida = corre(propuesta(), Path(t) / "no-existe")
        bien = c == 2
        fallos += not bien
        print(("OK   " if bien else "FALLO ") + "sin as-is sale con 2" + ("" if bien else f" (sale {c}):\n{salida}"))
    print("Todo bien" if not fallos else f"{fallos} fallos")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
