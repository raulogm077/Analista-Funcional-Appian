#!/usr/bin/env python3
"""Prueba de puntuar.py con proyectos inventados: `python3 prueba_puntuar.py`. Sale 0 si todo va bien.

Primero monta el proyecto con ../evolutivo-urgencia/montar.py y el correo de esta prueba (con el plugin de
PLUGIN_A_PROBAR) y comprueba el propio caso: PAN-01 construida en EV-01, validada por el equipo y no por el cliente
(✅, no 🔒), sin unidad en curso que la toque (`indice.py ficha` lo dice), `DEM_Dashboard` fuera de EV-02, una interfaz que
no pide DT, y un correo que pide justo ese texto. Después recorre sobre una copia el camino corto de un retoque
(actualizacion.md, «Camino corto») con las órdenes de ahora (estado, catalogar, abrir EV-03, ficha e impacto --cambio
EV-03, version con la fila D, funcional, técnico §7 y §13, el informe ya aplicado y comprobar.py --anterior --impacto),
contando las llamadas como el README (también leer antes lo que se edita): tienen que ser las 16 que cuenta, dentro del tope, y sin ninguna pasada de
comprobar.py con errores. Después, variantes que no deben pasar, y mira la salida de puntuar.py."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "evolutivo-urgencia"))
import montar as mt  # noqa: E402

sys.path.insert(0, str(mt.ANALISTA))
import modelo as mo  # noqa: E402
import unidades as un  # noqa: E402

PUNTUAR = AQUI / "puntuar.py"
E = json.loads((AQUI / "esperado.json").read_text(encoding="utf-8"))
CORREO = AQUI / E["fuente"]
PY = sys.executable

INFORME = """# Impacto de FU-05 · Texto del botón del panel · 2026-10-08
Análisis base: versión 1.1 · Cambio: {unidad} · Estado: {estado}

## Resumen
- 1 punto: 1 CAMBIA
- Requieren aprobación: {aprobacion}
- Posible petición de cambio: punto 1 (PAN-01 está construida en EV-01)
- Pantallas afectadas: PAN-01 · Técnico: §7, §13

## Puntos

| # | Tipo | Qué se dice | Encaja en | Cambio propuesto | Revisar también | Requiere | Decisión |
|---|---|---|---|---|---|---|---|
| 1 | CAMBIA | El botón «Nueva solicitud» confunde: que diga «Pedir material» [FU-05] | PAN-01 | PAN-01 con el botón «Pedir material» | — | {requiere} | {decision} |

## Aplicado
{aplicado}
"""
DT = """**DT-04 — Cambio sobre lo construido: EV-03**

| Campo | Contenido |
|---|---|
| **Capa** | Operación |
| **Necesidad** | PAN-01 (FU-05) |
| **Despliegue y vuelta atrás** | Un paquete con `DEM_Dashboard`; vuelta atrás con el del PASE-2026-031 |
| **Por qué** | Lo que ya está en producción no se rompe al desplegar (BP 08 §3) |
| **Verificado** | No hace falta |

## 3. Modelo de datos"""


def corre(*orden) -> tuple[int, str]:
    r = subprocess.run([str(x) for x in orden], capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env=mt.ENTORNO)
    return r.returncode, r.stdout + r.stderr


def editar(ruta: Path, viejo: str, nuevo: str):
    t = ruta.read_text(encoding="utf-8")
    if viejo not in t:
        sys.exit(f"{ruta.name} no tiene «{viejo[:60]}»: la prueba no está al día con los datos")
    ruta.write_text(t.replace(viejo, nuevo, 1), encoding="utf-8")


LEIDOS = 5    # lo que el agente lee sin script: la skill, actualizacion.md, el correo catalogado y, antes de editarlos,
              # el tramo del funcional y el del técnico (la herramienta de edición pide leer antes)
MINIMO = 16   # el camino corto que cuenta el README («El tope: 25 llamadas»)
CAMINO = {}   # carpeta → {"llamadas": n, "salidas": {orden: salida}, "comprobar_con_errores": k} del camino simulado


def retoque(p: Path, aplicar=True, requiere="—", decision="✔", unidad="EV-03", dt=False) -> Path:
    """El camino corto de un retoque, con las órdenes de ahora y en su orden, contando las llamadas como el README:
    estado, catalogar el correo, abrir EV-03, ficha e impacto --cambio EV-03 de PAN-01, version (la copia, la 1.2 en los
    dos, la fila de la versión, la D-01 del CAMBIA y la fuente en proyecto.md), PAN-01 en el funcional, §7 y la fila
    «Modifica» de §13 en el técnico, el informe ya aplicado y comprobar.py --anterior --impacto. Con aplicar=False,
    solo el informe pendiente (el camino entero, parado en la aprobación). Lo que cuenta queda en CAMINO[p]."""
    camino = CAMINO.setdefault(p, {"llamadas": LEIDOS, "salidas": {}, "comprobar_con_errores": 0})

    def script(nombre, *args, puede_fallar=False):
        c, s = corre(PY, mt.ANALISTA / nombre, *args)
        camino["llamadas"] += 1
        if nombre == "comprobar.py" and c:
            camino["comprobar_con_errores"] += 1
        if c and not puede_fallar:
            sys.exit(f"{nombre} {' '.join(map(str, args[:3]))} falla:\n{s}")
        return s

    def edita(ruta, *cambios):
        for viejo, nuevo in cambios:
            editar(ruta, viejo, nuevo)
        camino["llamadas"] += 1

    def informe(**k):
        (p / "impacto" / "FU-05.md").write_text(INFORME.format(unidad=unidad if unidad != "EV-01" else "—", **k),
                                               encoding="utf-8")
        camino["llamadas"] += 1

    camino["salidas"]["estado"] = script("proyecto.py", "estado", p)
    script("leer_fuentes.py", p / CORREO.name, "-o", p / "fuentes")
    if unidad == "EV-03":
        script("proyecto.py", "cambio", p, "EV-03", "abrir", "--titulo", "Texto del botón del panel")
    camino["salidas"]["ficha"] = script("indice.py", "ficha", p, "PAN-01", "--lineas")
    camino["salidas"]["impacto"] = script("indice.py", "impacto", p, "PAN-01", "--cambio", unidad)
    pedida = "ninguno" if requiere == "—" else "punto 1"
    if not aplicar:
        informe(estado="pendiente", aprobacion=pedida, requiere=requiere, decision=decision, aplicado="")
        return p
    camino["salidas"]["version"] = script(
        "proyecto.py", "version", p, "--fuente", "FU-05", "--que", "El botón del panel se llama «Pedir material»",
        "--decision", "CAMBIA", "PAN-01", "El botón del panel para empezar una solicitud se llama «Pedir material»",
        "«Nueva solicitud» [FU-01 00:06:40]")
    a = p / "analisis"
    edita(a / "funcional.md", ("| Botón «Nueva solicitud» | Empezar una solicitud en PAN-02 | Gestor |",
                               "| Botón «Pedir material» | Empezar una solicitud en PAN-02 | Gestor <!-- ✅ FU-05 --> |"))
    edita(a / "tecnico.md", ("botón «Nueva solicitud» que abre", "botón «Pedir material» que abre"))
    edita(a / "tecnico.md", ("| 8 | `DEM_SolicitudForm` | Interfaz | Modifica | — | EV-02 |",
                             "| 8 | `DEM_SolicitudForm` | Interfaz | Modifica | — | EV-02 |\n"
                             f"| 9 | `DEM_Dashboard` | Interfaz | Modifica | — | {unidad if unidad != 'EV-01' else ''} |"))
    if dt:
        edita(a / "tecnico.md", ("## 3. Modelo de datos", DT))
    informe(estado="aplicado en 1.2", aprobacion=pedida, requiere=requiere, decision=decision,
            aplicado="Versión 1.2: PAN-01 modificada · nueva: D-01")
    script("comprobar.py", p, "--fuentes", p / "fuentes", "--anterior", p / "versiones" / "v1.1", "--impacto",
           p / "impacto" / "FU-05.md", puede_fallar=True)
    return p


def comprobar_caso(base: Path, p_bien: Path) -> list[str]:
    mal = []
    m = mo.Proyecto(base)
    ctx = un.Contexto(m)
    pan = E["pantalla"]
    if m.piezas[pan].estado != "✅":
        mal.append(f"{pan} está {m.piezas[pan].estado}: con 🔒 cambiarla pide aprobación por eso, no por construida")
    if "nueva solicitud" not in mo.normaliza(mo.sin_comentarios(m.texto(pan))):
        mal.append(f"{pan} no tiene el botón «Nueva solicitud»")
    c, s = corre(PY, mt.ANALISTA / "indice.py", "ficha", base, pan)
    if c or "Construido: EV-01 · En curso: —" not in s:
        mal.append(f"indice.py ficha {pan} no dice «Construido: EV-01 · En curso: —»:\n{s}")
    if E["objeto"] in ctx.cambian("EV-02") or E["objeto"] not in ctx.linea_base():
        mal.append(f"{E['objeto']} tiene que estar construido y fuera de EV-02")
    correo = CORREO.read_text(encoding="utf-8")
    if E["texto_nuevo"] not in correo or "Nueva solicitud" not in correo:
        mal.append("el correo no pide el texto nuevo del botón «Nueva solicitud»")
    if not (isinstance(E["tope_llamadas"], int) and E["tope_llamadas"] > 0):
        mal.append("tope_llamadas tiene que ser un número fijado")
    # el camino corto, con las órdenes de ahora: 16 llamadas (la cuenta del README), la pasada de comprobar.py sin
    # errores, estado con EV-02 Aprobada, impacto --cambio EV-03 con «Posible petición de cambio», sin pedir aprobación
    # y con la fila de §13 que lleva DEM_Dashboard, y version con la 1.2
    camino = CAMINO[p_bien]
    if camino["llamadas"] != MINIMO or MINIMO > E["tope_llamadas"]:
        mal.append(f"el camino más corto son {camino['llamadas']} llamadas; el README cuenta {MINIMO} y el tope es "
                   f"{E['tope_llamadas']}")
    if camino["comprobar_con_errores"]:
        mal.append(f"el camino más corto tiene {camino['comprobar_con_errores']} pasadas de comprobar.py con errores")
    if not re.search(r"EV-02 · [^\n]* · Aprobada", camino["salidas"]["estado"]):
        mal.append(f"proyecto.py estado no lista EV-02 Aprobada:\n{camino['salidas']['estado']}")
    imp = camino["salidas"]["impacto"]
    if "Posible petición de cambio" not in imp or "Requiere: Sí" in imp:
        mal.append(f"indice.py impacto PAN-01 --cambio EV-03 no da «Posible petición de cambio» sin pedir aprobación:\n{imp}")
    if f"| 9 | `{E['objeto']}` | Interfaz | Modifica | — | EV-03 |" not in imp:
        mal.append(f"indice.py impacto PAN-01 --cambio EV-03 no da la fila de §13 de {E['objeto']}:\n{imp}")
    if "Versión 1.2" not in camino["salidas"]["version"] or "D-01" not in camino["salidas"]["version"]:
        mal.append(f"proyecto.py version no abre la 1.2:\n{camino['salidas']['version']}")
    ctx = un.Contexto(mo.Proyecto(p_bien))
    if ctx.puntos_construido("EV-03"):
        mal.append(f"cambiar {E['objeto']} pide «Cambio sobre lo construido»: {ctx.puntos_construido('EV-03')}")
    return mal


def main() -> int:
    fallos = 0
    with tempfile.TemporaryDirectory(prefix="puntuar con espacios ") as t:
        t = Path(t)
        base = t / "base" / "DEM retoque"
        try:
            mt.montar(base, CORREO)
        except SystemExit as e:
            print(f"FALLO montar.py: {e}")
            return 1
        huella = mt.montaje_de(base)
        raiz = t / "proyectos"
        raiz.mkdir()

        def nuevo():
            p = raiz / f"Carpeta con espacios {len(list(raiz.iterdir())) + 1}" / "Gestión app"
            shutil.copytree(base, p)
            return p

        def word(p):
            (p / "entregables" / "DF-Solicitudes-de-material-v1.2.docx").write_bytes(b"PK otro Word")
            return p

        def captura(p):
            f = p / "prototipo" / "capturas" / "PAN-01.png"
            f.write_bytes(f.read_bytes() + b"otra")
            return p

        def roto(p):
            editar(p / "analisis" / "funcional.md", "## 2. Perfiles", "Perfiles")
            return p

        bien = retoque(nuevo())
        mal = comprobar_caso(base, bien)
        fallos += bool(mal)
        print(("OK   " if not mal else "FALLO ") + "el caso: PAN-01 construida y sin otra unidad, el correo, el tope y el "
              "retoque simulado" + "".join(f"\n  {x}" for x in mal))
        cuenta = lambda n, k=0: ("--llamadas", str(n), "--comprobar-con-errores", str(k))
        solo_catalogada = nuevo()
        corre(PY, mt.ANALISTA / "leer_fuentes.py", solo_catalogada / CORREO.name, "-o", solo_catalogada / "fuentes")
        casos = [
            ("lo que se espera, con las llamadas del camino más corto",
             bien, cuenta(CAMINO[bien]["llamadas"], CAMINO[bien]["comprobar_con_errores"]), 0, "Total: 6/6"),
            ("justo en el tope", bien, cuenta(E["tope_llamadas"]), 0, "Total: 6/6"),
            ("una llamada de más", bien, cuenta(E["tope_llamadas"] + 1), 1, "FALLO llamadas"),
            ("una pasada de comprobar.py con errores", bien, cuenta(21, 1), 1, "FALLO comprobar_una_pasada"),
            ("pide aprobación por construido y no lo aplica",
             retoque(nuevo(), aplicar=False, requiere="Sí (construido)", decision="Pendiente"), cuenta(18), 1,
             "FALLO sin_aprobacion: FU-05.md punto 1 («Sí (construido)», Pendiente)"),
            ("aplicado, pero el punto pide aprobación", retoque(nuevo(), requiere="Sí (EV-01)"), cuenta(21), 1,
             "FALLO sin_aprobacion"),
            ("una DT «Cambio sobre lo construido»", retoque(nuevo(), dt=True), cuenta(22), 1, "FALLO sin_dt: DT-04"),
            ("el Word regenerado", word(retoque(nuevo())), cuenta(22), 1, "FALLO sin_word_ni_capturas"),
            ("la captura de PAN-01 regenerada", captura(retoque(nuevo())), cuenta(23), 1, "FALLO sin_word_ni_capturas"),
            ("la fila de §13 sin unidad (queda en EV-01, en producción)", retoque(nuevo(), unidad="EV-01"), cuenta(20),
             1, "FALLO hecho: técnico §13 sin `DEM_Dashboard` «Modifica» en una unidad Abierta (está en EV-01"),
            ("metido en EV-02, ya aprobada", retoque(nuevo(), unidad="EV-02"), cuenta(20), 1,
             "(está en EV-02 (Aprobada))"),
            ("solo catalogada: no se hace nada", solo_catalogada, cuenta(5), 1, "FALLO hecho"),
            ("comprobar.py con errores", roto(retoque(nuevo())), cuenta(21), 1, "FALLO comprobar_una_pasada"),
        ]
        for nombre, p, extra, codigo, debe in casos:
            c, salida = corre(PY, PUNTUAR, p, "--montaje", huella, *extra)
            ok = c == codigo and debe in salida
            fallos += not ok
            print(("OK   " if ok else "FALLO ") + nombre + ("" if ok else f" (sale {c}):\n{salida}"))
        for nombre, args, debe in (("sin --llamadas sale con 2", (bien, "--montaje", huella), "--llamadas"),
                                   ("sin la huella del montaje sale con 2", (nuevo(), *cuenta(10)), "No encuentro"),
                                   ("sin proyecto sale con 2", (raiz / "no existe", *cuenta(10)), "No encuentro")):
            c, salida = corre(PY, PUNTUAR, *args)
            ok = c == 2 and debe in salida
            fallos += not ok
            print(("OK   " if ok else "FALLO ") + nombre + ("" if ok else f" (sale {c}):\n{salida}"))
    print("Todo bien" if not fallos else f"{fallos} fallos")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
