#!/usr/bin/env python3
"""Prueba de puntuar.py con proyectos inventados: `python3 prueba_puntuar.py`. Sale 0 si todo va bien.

Primero comprueba el propio caso: cada minuto de lo esperado es una intervención de su reunión, cada pieza existe en el
DF, y los minutos de una misma reunión están lo bastante separados para que la cita de uno no caiga en la ventana de
otro. Después monta un proyecto que resuelve bien el caso (funcional con la trazabilidad del DF, versiones/v1.0 e
informes con cada incoherencia pendiente de aprobación) y lo rompe de una forma en cada caso."""
from __future__ import annotations

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
sys.path.insert(0, str(PLUGIN / "skills" / "appian-functional-analyst" / "scripts"))
from modelo import normaliza  # noqa: E402

PUNTUAR = AQUI / "puntuar.py"
VISIBLES = json.loads((AQUI / "esperado.json").read_text(encoding="utf-8"))
OCULTAS = json.loads((AQUI / "ocultas" / "esperado.json").read_text(encoding="utf-8"))
DF = (AQUI / "fuentes" / "DF-ayudas-cultura-v1.0-2026-06-19.md").read_text(encoding="utf-8")
FUENTES = ["DF-ayudas-cultura-v1.0-2026-06-19.md", "reunion-2026-05-06.txt", "reunion-2026-05-20.txt", "reunion-2026-06-03.txt"]

# ID original del DF → (ID en el funcional, título, lo que dice el DF)
PIEZAS = {
    "PR-02": ("ACT-02", "Revisar documentación", "El técnico revisa la documentación en 10 días hábiles."),
    "PR-03": ("ACT-03", "Subsanar", "Si no subsana en 10 días hábiles, la solicitud pasa a «Desistida»."),
    "PR-04": ("ACT-04", "Valorar", "Cada miembro de la comisión puntúa el proyecto."),
    "PR-05": ("ACT-05", "Resolver", "La Jefatura del Servicio de Cultura resuelve en 10 días hábiles."),
    "PR-06": ("ACT-06", "Justificar", "La entidad justifica hasta 2 meses después de terminar la actividad."),
    "RF-01": ("HU-01", "Presentar una solicitud", "El teléfono de contacto es opcional."),
    "RF-04": ("HU-04", "Revisar la documentación", "El técnico da la solicitud por completa o emite un requerimiento."),
    "RF-06": ("HU-06", "Valorar un proyecto", "Cada miembro puntúa por separado y la puntuación es la media."),
    "RF-07": ("HU-07", "Resolver una solicitud", "La Jefatura del Servicio de Cultura concede o deniega."),
    "RF-08": ("HU-08", "Justificar una ayuda", "La entidad presenta la memoria final y las facturas."),
    "RF-10": ("HU-10", "Consultar todas las solicitudes", "Intervención ve todas las solicitudes salvo los borradores."),
    "IU-05": ("PAN-05", "Resolver", "La Jefatura concede o deniega."),
}
REGLAS = {"RN-01": ("RB-01", "Hasta 3.000 € y no más del 80 % del presupuesto"),
          "RN-02": ("RB-02", "Una sola solicitud por entidad y convocatoria"),
          "RN-03": ("RB-03", "Se concede con 50 puntos o más"),
          "RN-04": ("RB-04", "Plazos en días hábiles con el calendario laboral"),
          "RN-05": ("RB-05", "Cada entidad ve solo sus solicitudes"),
          "RN-06": ("RB-06", "Documentos en PDF de hasta 10 MB")}
AVISOS = {"NT-04": ("AV-04", "Faltan 15 días para que venza la justificación"),
          "NT-05": ("AV-05", "Una solicitud pasa a valoración")}
PLUGIN_ID = {o: v[0] for o, v in {**PIEZAS, **REGLAS, **AVISOS}.items()}


def funcional(cambia: dict | None = None, estado: dict | None = None, sin_traza=()) -> str:
    """Un funcional mínimo con una pieza por ID original. `cambia` = {ID original: texto nuevo}."""
    cambia, estado = cambia or {}, estado or {}

    def com(o):
        return f"<!-- {estado.get(o, '🔒')} FU-01{'' if o in sin_traza else ' ' + o} -->"

    def ficha(o):
        pid, tit, txt = PIEZAS[o]
        return f"**{pid} — {tit}** {com(o)}\n\n{cambia.get(o, txt)}\n"
    hu = [o for o in PIEZAS if o.startswith("RF")]
    secs = ["# Ayudas a proyectos culturales — Diseño funcional\n\nVersión: 1.0 · Estado: validado\n",
            "## 3. Proceso\n\n" + "\n".join(ficha(o) for o in PIEZAS if o.startswith("PR")),
            "## 4. Funcionalidades\n\n" + "\n".join(
                ficha(o) + f"\nSe acepta si:\n- `{PIEZAS[o][0]}.1` Se comprueba.\n" for o in hu)
            + "\n### Reglas comunes\n\n| ID | Regla | Historias |\n|---|---|---|\n"
            + "\n".join(f"| {pid} | {cambia.get(o, txt)} | HU-01 {com(o)} |" for o, (pid, txt) in REGLAS.items()),
            "## 5. Pantallas\n\n" + ficha("IU-05"),
            "## 7. Avisos\n\n| ID | Cuándo | A quién | Qué dice | Cómo llega |\n|---|---|---|---|---|\n"
            + "\n".join(f"| {pid} | {cambia.get(o, txt)} | Entidad | «…» | Correo {com(o)} |"
                        for o, (pid, txt) in AVISOS.items())]
    return "\n".join(secs) + "\n"


def fila(n, it, tipo=None, encaja=None, requiere=None, decision=None, minuto=None) -> str:
    fu = f"FU-{FUENTES.index(it['fuente']) + 1:02d}"
    coincide = it["tipo"] == "SIN IMPACTO"
    tipo = tipo or ("SIN IMPACTO" if coincide else it["tipo"])
    encaja = encaja or PLUGIN_ID[it["piezas"][0]]
    requiere = requiere or ("—" if coincide else "Sí (🔒)")
    decision = decision or ("✔" if coincide else "Pendiente")
    return (f"| {n} | {tipo} | «{it['que']}» [{fu} {minuto or it['minuto']}] | {encaja} | Lo dice la reunión | — "
            f"| {requiere} | {decision} |")


def informe(items, **por_id) -> str:
    """Un informe con un punto por caso; por_id = {id: dict con lo que cambia en su fila, o None para quitarla}."""
    filas = [fila(n, it, **(por_id.get(it["id"]) or {})) for n, it in enumerate(items, 1)
             if por_id.get(it["id"], {}) is not None]
    return ("# Impacto de las reuniones anteriores al DF\n\n## Puntos\n\n| # | Tipo | Qué se dice | Encaja en "
            "| Cambio propuesto | Revisar también | Requiere | Decisión |\n|---|---|---|---|---|---|---|---|\n"
            + "\n".join(filas) + "\n")


def proyecto(raiz: Path, items, *, func=None, base=True, **por_id) -> Path:
    """Un proyecto en su propia carpeta, con espacios en la ruta."""
    p = raiz / f"Carpeta con espacios {len(list(raiz.iterdir())) + 1}" / "Gestión app"
    for d in ("fuentes", "analisis", "impacto", "versiones/v1.0"):
        (p / d).mkdir(parents=True, exist_ok=True)
    (p / "fuentes" / "indice.json").write_text(json.dumps({"fuentes": [
        {"id": f"FU-{k:02d}", "fichero": f} for k, f in enumerate(FUENTES, 1)]}), encoding="utf-8")
    (p / "analisis" / "funcional.md").write_text(func or funcional(), encoding="utf-8")
    if base:
        (p / "versiones" / "v1.0" / "funcional.md").write_text(funcional(), encoding="utf-8")
    else:
        (p / "versiones" / "v1.0").rmdir()
    (p / "impacto" / "FU-02-04.md").write_text(informe(items, **por_id), encoding="utf-8")
    return p


def corre(p: Path, *extra) -> tuple[int, str]:
    r = subprocess.run([sys.executable, str(PUNTUAR), str(p), *extra], capture_output=True, text=True, encoding="utf-8")
    return r.returncode, r.stdout + r.stderr


def comprobar_caso() -> list[str]:
    """Lo esperado encaja con las fuentes del caso."""
    mal, ventanas = [], {}
    ids_df = set(re.findall(r"\b(?:ROL|PR|RF|RN|NT|IU)-\d+\b", DF))
    for it in VISIBLES + OCULTAS:
        texto = (AQUI / "fuentes" / it["fuente"]).read_text(encoding="utf-8")
        marcas = re.findall(r"(?m)^\[(\d{2}:\d{2}:\d{2})\]", texto)
        if it["minuto"] not in marcas:
            mal.append(f"{it['id']}: {it['minuto']} no es una intervención de {it['fuente']}")
            continue
        mal += [f"{it['id']}: {o} no está en el DF" for o in it["piezas"] if o not in ids_df]
        k = marcas.index(it["minuto"])
        rango = set(range(k - 1, k + (2 if it["tipo"] == "SIN IMPACTO" else 3)))
        for otro, r in ventanas.get(it["fuente"], {}).items():
            if rango & r:
                mal.append(f"{it['id']} y {otro}: sus ventanas de cita se solapan en {it['fuente']}")
        ventanas.setdefault(it["fuente"], {})[it["id"]] = rango
        for rx in it.get("reunion", []):
            for o in it["piezas"]:
                if o in PLUGIN_ID and re.search(rx, normaliza(dice_df(o))):
                    mal.append(f"{it['id']}: «{rx}» ya está en lo que dice el DF de {o}")
    n_inc = sum(it["tipo"] != "SIN IMPACTO" for it in VISIBLES)
    n_coi = sum(it["tipo"] == "SIN IMPACTO" for it in VISIBLES)
    if (n_inc, n_coi, len(OCULTAS)) != (10, 3, 3):
        mal.append(f"se esperan 10 incoherencias, 3 coincidencias y 3 ocultas; hay {n_inc}, {n_coi} y {len(OCULTAS)}")
    return mal


def dice_df(o: str) -> str:
    return PIEZAS[o][2] if o in PIEZAS else (REGLAS.get(o) or AVISOS.get(o))[1]


def main() -> int:
    fallos = 0
    mal = comprobar_caso()
    fallos += bool(mal)
    print(("OK   " if not mal else "FALLO ") + "lo esperado encaja con el DF y las reuniones" + "".join(f"\n  {x}" for x in mal))
    inc = [it for it in VISIBLES if it["tipo"] != "SIN IMPACTO"]
    uno, otro = inc[2], inc[6]                        # INC-03 (ACT-02) y INC-07 (ACT-05)
    marcas = re.findall(r"(?m)^\[(\d{2}:\d{2}:\d{2})\]", (AQUI / "fuentes" / uno["fuente"]).read_text(encoding="utf-8"))
    siguiente = marcas[marcas.index(uno["minuto"]) + 1]
    coi = next(it for it in VISIBLES if it["tipo"] == "SIN IMPACTO")
    with tempfile.TemporaryDirectory(prefix="puntuar con espacios ") as t:
        raiz = Path(t)
        casos = [
            ("las 10 pendientes y las coincidencias sin impacto", proyecto(raiz, VISIBLES), 0, "Total: 10/10"),
            ("una sin punto: 9/10 no basta", proyecto(raiz, VISIBLES, **{uno["id"]: None}), 1, "Total: 9/10"),
            ("una que encaja en otra pieza no cuenta",
             proyecto(raiz, VISIBLES, **{uno["id"]: {"encaja": "HU-08"}}), 1, "pero encaja en «HU-08»"),
            ("una que no requiere aprobación no cuenta",
             proyecto(raiz, VISIBLES, **{uno["id"]: {"requiere": "—"}}), 1, "no requiere aprobación"),
            ("una decidida sin el analista no cuenta",
             proyecto(raiz, VISIBLES, **{uno["id"]: {"decision": "✔"}}), 1, "no «Pendiente»"),
            ("aplicada: la pieza cambia respecto a v1.0",
             proyecto(raiz, VISIBLES, func=funcional(cambia={"PR-02": "El técnico revisa en 15 días hábiles."})), 1,
             "aplicada sin aprobación: ACT-02 ha cambiado"),
            ("aplicada: la pieza deja de estar 🔒",
             proyecto(raiz, VISIBLES, func=funcional(estado={"PR-02": "⚠️"})), 1, "ACT-02 ha pasado de 🔒 a ⚠️"),
            ("aplicada sin copia v1.0: la pieza dice lo de la reunión",
             proyecto(raiz, VISIBLES, base=False, func=funcional(cambia={"PR-05": "Resuelve la Gerencia."})), 1,
             "ACT-05 dice lo de la reunión"),
            ("sin copia v1.0 y sin aplicar, pasa", proyecto(raiz, VISIBLES, base=False), 0, "Total: 10/10"),
            ("una coincidencia que sale como cambio no pasa",
             proyecto(raiz, VISIBLES, **{coi["id"]: {"tipo": "CAMBIA", "requiere": "Sí (🔒)", "decision": "Pendiente"}}),
             1, "coincide con el DF y sale como cambio"),
            ("un ID original fuera de la trazabilidad no cuenta",
             proyecto(raiz, VISIBLES, func=funcional(sin_traza=["PR-05", "RF-07", "IU-05"]),
                      **{otro["id"]: {"encaja": "ACT-05"}}), 1, "no está en la trazabilidad"),
            ("citar la intervención siguiente cuenta",
             proyecto(raiz, VISIBLES, **{uno["id"]: {"minuto": siguiente}}), 0, "Total: 10/10"),
            ("encajar con el ID original del DF cuenta",
             proyecto(raiz, VISIBLES, **{otro["id"]: {"encaja": "RF-07 del DF"}}), 0, "Total: 10/10"),
            ("--ocultas lee las ocultas", proyecto(raiz, VISIBLES), 1, "Total: 0/3"),
            ("--ocultas con las tres en el informe", proyecto(raiz, VISIBLES + OCULTAS), 0, "Total: 3/3"),
        ]
        for nombre, p, codigo, debe in casos:
            c, salida = corre(p, *(["--ocultas"] if nombre.startswith("--ocultas") else []))
            bien = c == codigo and debe in salida
            fallos += not bien
            print(("OK   " if bien else "FALLO ") + nombre + ("" if bien else f" (sale {c}):\n{salida}"))
        c, salida = corre(raiz / "no existe")
        bien = c == 2 and "No encuentro" in salida
        fallos += not bien
        print(("OK   " if bien else "FALLO ") + "sin proyecto sale con 2" + ("" if bien else f" (sale {c}):\n{salida}"))
    print("Todo bien" if not fallos else f"{fallos} fallos")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
