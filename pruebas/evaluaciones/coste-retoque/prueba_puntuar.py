#!/usr/bin/env python3
"""Prueba de puntuar.py con proyectos inventados: `python3 prueba_puntuar.py`. Sale 0 si todo va bien.

Primero monta el proyecto con ../evolutivo-urgencia/montar.py y el correo de esta prueba (con el plugin de
PLUGIN_A_PROBAR) y comprueba el propio caso: PAN-01 construida en EV-01, validada por el equipo y no por el cliente
(✅, no 🔒), sin unidad en curso que la toque (`indice.py ficha` lo dice), `DEM_Dashboard` fuera de EV-02, una interfaz que
no pide DT, y un correo que pide justo ese texto. Después hace sobre copias lo que haría el agente con los scripts del
plugin (catalogar, abrir EV-03, copia, informe aplicado, PAN-01, técnico §7 y §13, versión 1.2), comprueba que pasa
comprobar.py --anterior --impacto, y variantes que no deben pasar, y mira la salida de puntuar.py."""
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


def script(nombre, *args):
    c, s = corre(PY, mt.ANALISTA / nombre, *args)
    if c:
        sys.exit(f"{nombre} {' '.join(map(str, args[:2]))} falla:\n{s}")
    return s


def retoque(p: Path, aplicar=True, requiere="—", decision="✔", unidad="EV-03", dt=False) -> Path:
    """Lo que haría el agente: catalogar el correo, abrir EV-03, y con el informe aplicado, PAN-01 con el texto nuevo, el
    técnico (§7 y una fila «Modifica» de §13), la versión 1.2 y proyecto.md. Con aplicar=False, solo el informe pendiente."""
    script("leer_fuentes.py", p / CORREO.name, "-o", p / "fuentes")
    if unidad == "EV-03":
        script("proyecto.py", "cambio", p, "EV-03", "abrir", "--titulo", "Texto del botón del panel")
    if not aplicar:
        (p / "impacto" / "FU-05.md").write_text(INFORME.format(
            unidad=unidad, estado="pendiente", aprobacion="punto 1 (construido)", requiere=requiere, decision=decision,
            aplicado=""), encoding="utf-8")
        return p
    script("proyecto.py", "copia", p)
    a = p / "analisis"
    editar(a / "funcional.md", "| Botón «Nueva solicitud» | Empezar una solicitud en PAN-02 | Gestor |",
           "| Botón «Pedir material» | Empezar una solicitud en PAN-02 | Gestor <!-- ✅ FU-05 --> |")
    for f in ("funcional.md", "tecnico.md"):
        editar(a / f, "Versión: 1.1", "Versión: 1.2")
    editar(a / "tecnico.md", "botón «Nueva solicitud» que abre", "botón «Pedir material» que abre")
    editar(a / "tecnico.md", "| 8 | `DEM_SolicitudForm` | Interfaz | Modifica | — | EV-02 |",
           "| 8 | `DEM_SolicitudForm` | Interfaz | Modifica | — | EV-02 |\n"
           f"| 9 | `DEM_Dashboard` | Interfaz | Modifica | — | {unidad if unidad != 'EV-01' else ''} |")
    if dt:
        editar(a / "tecnico.md", "## 3. Modelo de datos", DT)
    editar(a / "decisiones.md", "DF del cambio EV-02 entregado 2026-10-02 |",
           "DF del cambio EV-02 entregado 2026-10-02 |\n| 1.2 | 2026-10-08 | El botón del panel para empezar una "
           "solicitud se llama «Pedir material» | FU-05 | — |")
    editar(a / "decisiones.md", "|---|---|---|---|---|---|---|---|",
           "|---|---|---|---|---|---|---|---|\n| D-01 | 2026-10-08 | FU-05 | CAMBIA | El botón del panel para empezar "
           "una solicitud se llama «Pedir material» | «Nueva solicitud» [FU-01 00:06:40] | PAN-01 | Sí |")
    editar(p / "proyecto.md", "| FU-04 | 2026-10-05 |",
           "| FU-05 | 2026-10-08 | Correo de Servicios generales: texto del botón del panel | impacto/FU-05.md | 1.2 |\n"
           "| FU-04 | 2026-10-05 |")
    (p / "impacto" / "FU-05.md").write_text(INFORME.format(
        unidad=unidad if unidad != "EV-01" else "—", estado="aplicado en 1.2",
        aprobacion="ninguno" if requiere == "—" else "punto 1", requiere=requiere, decision=decision,
        aplicado="Versión 1.2: PAN-01 modificada · nueva: D-01"), encoding="utf-8")
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
    # lo que haría el agente pasa la comprobación de después de aplicar y no pide DT: una interfaz no la pide
    c, s = corre(PY, mt.ANALISTA / "comprobar.py", p_bien, "--fuentes", p_bien / "fuentes", "--anterior",
                 p_bien / "versiones" / "v1.1", "--impacto", p_bien / "impacto" / "FU-05.md")
    if c:
        mal.append(f"el retoque simulado no pasa comprobar.py --anterior --impacto:\n{s}")
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
        script("leer_fuentes.py", solo_catalogada / CORREO.name, "-o", solo_catalogada / "fuentes")
        casos = [
            ("lo que se espera", bien, cuenta(21), 0, "Total: 6/6"),
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
