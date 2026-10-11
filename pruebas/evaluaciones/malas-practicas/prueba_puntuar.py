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
FICTICIA = AQUI.parent / "aplicacion-ficticia"
MALAS = json.loads((FICTICIA / "malas-practicas.json").read_text(encoding="utf-8"))
OCULTAS = json.loads((FICTICIA / "ocultas" / "malas-practicas.json").read_text(encoding="utf-8"))
CLAVES = json.loads((AQUI / "claves.json").read_text(encoding="utf-8"))


def seccion_equivocada(mp: dict) -> str:
    """Una «§n» del documento de `bp` que no está en sus bp_aceptadas."""
    doc = mp["bp"].split(" ")[1]
    return next(str(n) for n in range(1, 99) if f"BP {doc} §{n}" not in mp["bp_aceptadas"])


def propuesta(quitar_solucion=(), regla_otra=(), sin_nv=False, solo_titulo=(), seccion_otra=(),
              otra_aceptada=(), titulos=None, efectos=None, juntas=(), cabecera="**{ref} — {titulo}**") -> str:
    """Una REF por mala práctica, con la primera de sus claves en el título, salvo lo que diga cada argumento.
    `titulos` y `efectos`: {MP: texto}; `juntas`: una sola REF, la de la primera, cita también los objetos de las
    demás, que no tienen REF propia; `cabecera`: la forma de la línea de la ficha."""
    fichas, filas = [], []
    for k, mp in enumerate(MALAS, 1):
        if mp["id"] in juntas[1:]:
            continue
        ref = f"REF-{k:02d}"
        titulo = (titulos or {}).get(mp["id"], f"Problema: {CLAVES[mp['id']][0]}")
        efecto = (efectos or {}).get(mp["id"], "x")
        doc, sec = mp["bp"].split(" ")[1], mp["bp"].split("§")[1]
        if mp["id"] in regla_otra:
            doc = "99" if doc != "99" else "98"
        if mp["id"] in seccion_otra:
            sec = seccion_equivocada(mp)
        if mp["id"] in otra_aceptada:   # la última de sus bp_aceptadas, no la de `bp`
            doc, sec = mp["bp_aceptadas"][-1].split(" ")[1], mp["bp_aceptadas"][-1].split("§")[1]
        suyas = juntas if mp["id"] in juntas else (mp["id"],)
        objetos = " y ".join(f"`{o}`" for m in MALAS if m["id"] in suyas for o in m["objetos"])
        if mp["id"] in solo_titulo:   # el objeto en el título, no en la evidencia
            fichas.append(cabecera.format(ref=ref, titulo=f"{titulo} en {objetos}")
                          + "\n\n- Evidencia: H-XXX-01 ✅ lo muestra el anexo\n"
                          f"- Regla: BP {doc} §{sec}\n- Efecto: x\n- Prioridad: Media\n- Esfuerzo: S, poco\n")
        else:
            fichas.append(cabecera.format(ref=ref, titulo=titulo) + f"\n\n- Evidencia: H-XXX-01 ✅ {objetos} · "
                          f"[`mcp:x/{mp['objetos'][0]}#nodes[id=130]`](../as-is/anexo/x/{mp['objetos'][0].replace(' ', '_')}.md)\n"
                          f"- Regla: BP {doc} §{sec}\n- Efecto: {efecto}\n- Prioridad: Media\n- Esfuerzo: S, poco\n")
        if mp["id"] not in quitar_solucion:
            filas.append(f"| Datos | algo | {ref}: porque sí (BP {doc} §{sec}) | nada |")
    pendientes = "| ID | Qué falta | Quién | Condiciona |\n|---|---|---|---|\n"
    if not sin_nv:
        pendientes += "| NV-ARQ-01 | ¿Qué hacen las reglas CMN? | Equipo | REF-02 |\n"
    return ("# Propuesta\n\n## 1. Alcance\n\nTodo.\n\n## 2. Diagnóstico\n\n" + "\n".join(fichas)
            + "\n## 3. Solución\n\n| Capa | Qué se hace | Por qué | Se descarta |\n|---|---|---|---|\n"
            + "\n".join(filas) + "\n\n## 4. Migración y convivencia\n\nNueva.\n\n## 5. Hoja de ruta\n\n"
            + "| Fase | Qué | Depende de |\n|---|---|---|\n| 1 | REF-01 | — |\n\n## 6. Pendientes\n\n" + pendientes)


def as_is(carpeta: Path, con_fuera: bool = True) -> Path:
    datos = carpeta / "as-is" / "datos"
    datos.mkdir(parents=True)
    (datos / "dependencias.json").write_text(json.dumps({"aristas": [], "fueraDeLaAplicacion": [
        {"nombre": "CMN_UsuarioActual", "tipo": "llamado con rule!", "usadoPor": ["MNT_PM_GestionOrden"], "usa": [],
         "nv": "NV-ARQ-01"}] if con_fuera else []}), encoding="utf-8")
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
    sin_lista = [mp["id"] for mp in MALAS + OCULTAS if (mp.get("bp_aceptadas") or [None])[0] != mp["bp"]]
    fallos += bool(sin_lista)
    print(("OK   " if not sin_lista else "FALLO ") + "cada mala práctica lleva bp_aceptadas, empezando por su bp"
          + (f": {', '.join(sin_lista)}" if sin_lista else ""))
    ids = [mp["id"] for mp in MALAS + OCULTAS]
    mal = sorted({i for i in ids if not CLAVES.get(i)} | (set(CLAVES) - set(ids)))
    fallos += bool(mal)
    print(("OK   " if not mal else "FALLO ") + "claves.json da claves a cada mala práctica, y solo a ellas"
          + (f": {', '.join(mal)}" if mal else ""))
    with tempfile.TemporaryDirectory(prefix="puntuar con espacios ") as t:
        carpeta = Path(t)
        as_is(carpeta)
        casos = [
            ("las 11 y el NV", propuesta(), 0, "11/11"),
            ("una sin Solución: 10/11 basta", propuesta(quitar_solucion=["MP-05"]), 0, "10/11"),
            ("dos sin Solución: 9/11 no basta", propuesta(quitar_solucion=["MP-05", "MP-06"]), 1, "9/11"),
            ("regla de otro documento no cuenta", propuesta(regla_otra=["MP-01", "MP-02"]), 1, "9/11"),
            ("sección equivocada del documento correcto no cuenta",
             propuesta(seccion_otra=["MP-01", "MP-04"]), 1, "9/11"),
            ("otra sección de bp_aceptadas cuenta", propuesta(otra_aceptada=["MP-01", "MP-03", "MP-04"]), 0, "11/11"),
            ("objeto solo en el título no cuenta", propuesta(solo_titulo=["MP-03", "MP-04"]), 1, "9/11"),
            ("sin el NV de CMN no pasa", propuesta(sin_nv=True), 1, "NV-ARQ-01"),
            ("fichas «### REF-nn · …» cuentan", propuesta(cabecera="### {ref} · {titulo}"), 0, "11/11"),
            ("fichas «**REF-nn: …**» cuentan", propuesta(cabecera="**{ref}: {titulo}**"), 0, "11/11"),
            ("ninguna clave casa con los objetos ni con el resto de la ficha",
             propuesta(titulos={mp["id"]: "Otro asunto" for mp in MALAS}), 1, "0/11"),
            ("REF de MP-04 retitulada sin nombrar el problema no cuenta",
             propuesta(titulos={"MP-04": "Escribe el historial a mano"}), 0, "FALLO MP-04"),
            ("una REF con los objetos de MP-06 y MP-11 cuenta solo para la que nombra",
             propuesta(juntas=("MP-06", "MP-11")), 0, "FALLO MP-11"),
            # Fichas escritas como las escribiría un arquitecto (sin mirar ninguna propuesta real)
            ("fichas naturales de MP-02, MP-03, MP-04 y MP-05 cuentan",
             propuesta(titulos={"MP-02": "El formulario tiene más de 3.000 líneas",
                                "MP-03": "La seguridad de las órdenes está solo en la interfaz",
                                "MP-04": "Proceso monolítico de 130 actividades",
                                "MP-05": "Arranca por timer aunque no haya órdenes pendientes"}), 0, "11/11"),
            ("el Efecto también nombra el problema («cada cambio se hace tres veces»)",
             propuesta(titulos={"MP-02": "Formulario de alta y edición"},
                       efectos={"MP-02": "mantenimiento: cada cambio se hace tres veces"}), 0, "11/11"),
            ("«por cada», «error» y «falla» no nombran el problema de MP-10 ni el de MP-08",
             propuesta(titulos={"MP-10": "Por cada técnico se muestra la etiqueta sin traducir",
                                "MP-08": "La pantalla falla porque el mensaje de error no está traducido"}),
             1, ("9/11", "FALLO MP-10", "FALLO MP-08")),
            # Una REF cuenta como mucho para una mala práctica
            ("una REF con «URL» y «desarrollo» cuenta solo para una (a igualdad, la primera)",
             propuesta(juntas=("MP-06", "MP-11"), titulos={"MP-06": "La URL del ERP apunta al entorno de desarrollo"}),
             0, ("10/11", "OK    MP-06", "FALLO MP-11")),
            ("una REF que nombra más el problema de MP-11 cuenta para MP-11",
             propuesta(juntas=("MP-06", "MP-11"),
                       titulos={"MP-06": "Autenticación None hacia el entorno de desarrollo, con su URL"}),
             0, ("10/11", "FALLO MP-06", "OK    MP-11")),
        ]
        for nombre, texto, codigo, debe in casos:
            c, salida = corre(texto, carpeta)
            bien = c == codigo and all(d in salida for d in ((debe,) if isinstance(debe, str) else debe))
            fallos += not bien
            print(("OK   " if bien else "FALLO ") + nombre + ("" if bien else f" (sale {c}):\n{salida}"))
        c, salida = corre(propuesta(), carpeta, "--ocultas")
        bien = c == 1 and "MPO-03" in salida and "/3 (" in salida   # las ocultas, no las visibles
        fallos += not bien
        print(("OK   " if bien else "FALLO ") + "--ocultas lee las ocultas" + ("" if bien else f" (sale {c}):\n{salida}"))
        sin_fuera = Path(t) / "sin objetos de fuera"
        as_is(sin_fuera, con_fuera=False)
        c, salida = corre(propuesta(), sin_fuera)
        bien = c == 2 and "no trae NV de objetos de fuera" in salida and "Total" not in salida
        fallos += not bien
        print(("OK   " if bien else "FALLO ") + "as-is sin NV de objetos de fuera sale con 2, sin puntuar, y lo dice"
              + ("" if bien else f" (sale {c}):\n{salida}"))
        c, salida = corre(propuesta(), Path(t) / "no-existe")
        bien = c == 2
        fallos += not bien
        print(("OK   " if bien else "FALLO ") + "sin as-is sale con 2" + ("" if bien else f" (sale {c}):\n{salida}"))
    print("Todo bien" if not fallos else f"{fallos} fallos")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
