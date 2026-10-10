#!/usr/bin/env python3
"""Prueba de puntuar.py con proyectos inventados: `python3 prueba_puntuar.py`. Sale 0 si todo va bien.

Primero monta el proyecto de partida con montar.py (con el plugin de PLUGIN_A_PROBAR) y comprueba el propio caso: EV-01
en producción y EV-02 aprobada con DEM_SolicitudForm entre sus objetos, el encargo de EV-02 sin nada que reaplicar, la
incidencia que nombra ese objeto, un entorno de corrección del que hablan las fuentes, lo esperado coherente consigo
mismo. Después hace, sobre copias del proyecto, lo que haría el agente con los scripts del plugin (catalogar la fuente,
abrir la URG, su ficha, la prueba en §14, rehacer el encargo) y variantes que no deben pasar, y mira la salida de
puntuar.py."""
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
sys.path.insert(0, str(AQUI))
import montar as mt  # noqa: E402

sys.path.insert(0, str(mt.ANALISTA))
import modelo as mo  # noqa: E402
import unidades as un  # noqa: E402

PUNTUAR = AQUI / "puntuar.py"
VISIBLE = json.loads((AQUI / "esperado.json").read_text(encoding="utf-8"))
OCULTO = json.loads((AQUI / "ocultas" / "esperado.json").read_text(encoding="utf-8"))
AVISO = AQUI / "ocultas" / OCULTO["fuente"]
PY = sys.executable

FICHA = """# URG-01 · No se pueden enviar solicitudes de 1.000 € o más · 2026-10-08
Análisis base: versión 1.1 · Cambio: URG-01 · Estado: sin cambios

## Urgencia

| Campo | Valor |
|---|---|
| Tipo | {tipo} |
| Síntoma | Al enviar una solicitud de 1.000 € o más sale un error y se queda en borrador [{fu}] |
| Quién la declara crítica | {quien} |
| Causa | La validación del importe de `DEM_SolicitudForm` no admite el punto de los miles: incumple HU-01.2 |
| Objetos | `DEM_SolicitudForm` |
| Colisión | {colision} |
| Dónde se corrige | {donde} |
| Despliegue y vuelta atrás | Un paquete con `DEM_SolicitudForm`; vuelta atrás con el del PASE-2026-031 |
| Cierre | — |

## Puntos

| # | Tipo | Qué se dice | Encaja en | Cambio propuesto | Revisar también | Requiere | Decisión |
|---|---|---|---|---|---|---|---|
| 1 | SIN IMPACTO | Defecto en producción: el funcional no cambia [{fu}] | HU-01 | Prueba que lo reproduce en técnico §14 | — | — | ✔ |

## Aplicado
"""
BIEN = {"tipo": "Defecto", "fu": "FU-05",
        "quien": "La jefa de Servicios generales: 35 solicitudes paradas y el pedido se cierra el viernes; el jefe de "
                 "proyecto está de acuerdo [FU-05]",
        "colision": "Sí: EV-02 (Aprobada) cambia `DEM_SolicitudForm`", "donde": "Entorno de corrección"}


def corre(*orden) -> tuple[int, str]:
    r = subprocess.run([str(x) for x in orden], capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env=mt.ENTORNO)
    return r.returncode, r.stdout + r.stderr


def editar(ruta: Path, viejo: str, nuevo: str):
    t = ruta.read_text(encoding="utf-8")
    if viejo not in t:
        sys.exit(f"{ruta.name} no tiene «{viejo[:60]}»: la prueba no está al día con los datos")
    ruta.write_text(t.replace(viejo, nuevo, 1), encoding="utf-8")


def copia(base: Path, raiz: Path) -> Path:
    p = raiz / f"Carpeta con espacios {len(list(raiz.iterdir())) + 1}" / "Gestión app"
    shutil.copytree(base, p)
    return p


def agente(p: Path, catalogar=True, encargo=True, prueba=True, **ficha):
    """Lo que haría el agente con los scripts del plugin: catalogar la incidencia, abrir URG-01, su ficha, la prueba que
    reproduce el fallo en técnico §14 y rehacer el encargo de EV-02."""
    if catalogar:
        corre(PY, mt.ANALISTA / "leer_fuentes.py", p / VISIBLE["fuente"], "-o", p / "fuentes")
    c, s = corre(PY, mt.ANALISTA / "proyecto.py", "cambio", p, "URG-01", "abrir", "--titulo",
                 "No se pueden enviar solicitudes de 1.000 € o más")
    if c:
        sys.exit(f"proyecto.py cambio abrir falla:\n{s}")
    (p / "impacto" / "URG-01.md").write_text(FICHA.format(**{**BIEN, **ficha}), encoding="utf-8")
    if prueba:
        editar(p / "analisis" / "tecnico.md", "| HU-05.1 | Aprobar, rechazar y devolver sin firma |",
               "| HU-05.1 | Aprobar, rechazar y devolver sin firma |\n| URG-01 | Enviar una solicitud de 1.250,00 € |")
    if encargo:
        c, s = corre(PY, mt.ANALISTA / "indice.py", "encargo", p, "EV-02")
        if c:
            sys.exit(f"indice.py encargo falla:\n{s}")
    return p


def pase(p: Path, ref="HF-2026-007", produccion=True):
    """Lo que haría el agente con el aviso del pase: catalogarlo, «Cierre» en la ficha y la URG En producción."""
    corre(PY, mt.ANALISTA / "leer_fuentes.py", AVISO, "-o", p / "fuentes")
    editar(p / "impacto" / "URG-01.md", "| Cierre | — |",
           f"| Cierre | 2026-10-08 · {ref} · una solicitud de 1.250,00 € se envía sin error [FU-06] |")
    if produccion:
        c, s = corre(PY, mt.ANALISTA / "proyecto.py", "cambio", p, "URG-01", "produccion", "--ref", ref)
        if c:
            sys.exit(f"proyecto.py cambio produccion falla:\n{s}")
    return p


def version(p: Path, v="1.2"):
    """Una versión nueva del análisis, coherente en los tres ficheros."""
    for f in ("funcional.md", "tecnico.md"):
        editar(p / "analisis" / f, "Versión: 1.1", f"Versión: {v}")
    editar(p / "analisis" / "decisiones.md", "DF del cambio EV-02 entregado 2026-10-02 |",
           f"DF del cambio EV-02 entregado 2026-10-02 |\n| {v} | 2026-10-08 | Los importes de 1.000 € o más se pueden "
           "enviar | FU-05 | — |")
    return p


def comprobar_caso(base: Path) -> list[str]:
    mal = []
    ctx = un.Contexto(mo.Proyecto(base))
    estados = {u.id: u.estado for u in ctx.unidades}
    if estados != {"EV-01": "En producción", "EV-02": "Aprobada"}:
        mal.append(f"las unidades al montar son {estados}")
    if VISIBLE["objeto"] not in ctx.cambian("EV-02"):
        mal.append(f"EV-02 no cambia {VISIBLE['objeto']}: no hay colisión")
    c, s = corre(PY, mt.ANALISTA / "proyecto.py", "estado", base)
    if c or not re.search(rf"EV-02 · .* · Aprobada · .*objetos: .*{VISIBLE['objeto']}", s):
        mal.append(f"proyecto.py estado no lista EV-02 con {VISIBLE['objeto']}:\n{s}")
    enc = base / "construccion" / "EV-02.md"
    if not enc.is_file() or "Reaplicar" in enc.read_text(encoding="utf-8"):
        mal.append("el encargo de EV-02 no está al montar, o ya tiene algo que reaplicar")
    incidencia = (base / VISIBLE["fuente"]).read_text(encoding="utf-8")
    if VISIBLE["objeto"] not in incidencia or not any(mo.normaliza(r) in mo.normaliza(incidencia)
                                                      for r in VISIBLE["declara"]):
        mal.append("la incidencia no nombra el objeto o a quien la declara crítica")
    if OCULTO["ref"] not in AVISO.read_text(encoding="utf-8"):
        mal.append("el aviso del pase no trae la referencia esperada")
    if not any("entorno de correccion" in mo.normaliza(f.read_text(encoding="utf-8")) for f in mt.FUENTES):
        mal.append("ninguna fuente dice que hay un entorno de corrección")
    v = mo.Proyecto(mt.DATOS).version("F")
    if f"{v[0]}.{v[1]}" != VISIBLE["version_funcional"] or OCULTO["version_funcional"] != VISIBLE["version_funcional"]:
        mal.append("version_funcional no es la del funcional de datos/")
    for e in (VISIBLE, OCULTO):
        um = e["umbral"]
        if sorted(um["obligatorios"] + um["ligereza"]) != sorted(e["puntos"]):
            mal.append("obligatorios y ligereza no reparten los puntos")
    huella = json.loads(mt.montaje_de(base).read_text(encoding="utf-8"))
    docx = [r for r in huella["ficheros"] if r.endswith(".docx")]
    pngs = [r for r in huella["ficheros"] if r.startswith("prototipo/capturas/") and r.endswith(".png")]
    if len(pngs) != 3 or (huella["word"] and len(docx) != 2):
        mal.append(f"al montar: capturas {pngs}, Word {docx}")
    if not huella["word"]:
        print("· sin Node o sin el paquete docx: el proyecto de partida no tiene los Word entregados")
    return mal


def main() -> int:
    fallos = 0
    with tempfile.TemporaryDirectory(prefix="puntuar con espacios ") as t:
        t = Path(t)
        base = t / "base" / "DEM urgencia"
        try:
            mt.montar(base)
        except SystemExit as e:
            print(f"FALLO montar.py: {e}")
            return 1
        mal = comprobar_caso(base)
        fallos += bool(mal)
        print(("OK   " if not mal else "FALLO ") + "el caso: proyecto de partida, fuentes y lo esperado"
              + "".join(f"\n  {x}" for x in mal))
        huella = mt.montaje_de(base)
        raiz = t / "proyectos"
        raiz.mkdir()
        nuevo = lambda: copia(base, raiz)

        def word(p):
            (p / "entregables").mkdir(exist_ok=True)
            (p / "entregables" / "DF-Solicitudes-de-material-v1.2.docx").write_bytes(b"PK otro Word")
            return p

        def captura(p):
            f = p / "prototipo" / "capturas" / "PAN-02.png"
            f.write_bytes(f.read_bytes() + b"otra")
            return p

        def roto(p):
            editar(p / "analisis" / "funcional.md", "## 2. Perfiles", "Perfiles")
            return p

        def construida(p):
            corre(PY, mt.ANALISTA / "proyecto.py", "cambio", p, "EV-02", "construida", "--manual", "--reaplicada", "URG-01")
            return p

        casos = [
            ("lo que se espera", agente(nuevo()), (), 0, "Total: 9/9"),
            ("sin hacer nada", nuevo(), (), 1, "FALLO ficha: ninguna URG nueva"),
            ("corregida en desarrollo: sin reaplicar en el encargo ni bloqueo",
             agente(nuevo(), donde="Desarrollo; los objetos quedan congelados"), (), 1, "FALLO bloqueo"),
            ("sin rehacer el encargo de EV-02", agente(nuevo(), encargo=False), (), 1,
             "FALLO encargo: construccion/EV-02.md no lleva «Reaplicar URG-01"),
            ("la colisión no nombra EV-02", agente(nuevo(), colision="No hay"), (), 1, "FALLO colision"),
            ("un defecto como cambio de comportamiento", agente(nuevo(), tipo="Cambio de comportamiento"), (), 1,
             "FALLO ficha: Tipo «Cambio de comportamiento»"),
            ("sin quién la declara crítica", agente(nuevo(), quien="—"), (), 1, "«Quién la declara crítica»: «—»"),
            ("la fuente sin catalogar", agente(nuevo(), catalogar=False), (), 1, "no está catalogada en fuentes/"),
            ("la URG en producción en una sesión desatendida",
             pase(agente(nuevo()), ref="PASE-SUPUESTO"), (), 1, "FALLO estados: URG En producción"),
            ("EV-02 marcada Construida", construida(agente(nuevo())), (), 1, "FALLO estados: EV-02 Construida"),
            ("un Word regenerado: de ligereza se tolera uno", word(agente(nuevo())), (), 0,
             "de ligereza fallan 1 (se tolera 1) → pasa"),
            ("una captura cambiada y versión nueva del funcional: dos de ligereza no",
             version(captura(agente(nuevo()))), (), 1, "de ligereza fallan 2"),
            ("comprobar.py con errores", roto(agente(nuevo())), (), 1, "FALLO comprobar"),
        ]
        cerrada = pase(agente(nuevo()))
        casos += [
            ("--ocultas: cerrada con su referencia", cerrada, ("--ocultas",), 0, "Total: 6/6"),
            ("--ocultas: sin pasar a producción", pase(agente(nuevo()), produccion=False), ("--ocultas",), 1,
             "FALLO produccion"),
            ("--ocultas: con otra referencia", pase(agente(nuevo()), ref="HF-2026-999"), ("--ocultas",), 1,
             "FALLO produccion"),
            ("--ocultas: EV-02 marcada Construida al cerrar", construida(pase(agente(nuevo()))), ("--ocultas",), 1,
             "FALLO ev02_sin_construir"),
            ("--ocultas: un Word regenerado al cerrar se tolera", word(pase(agente(nuevo()))), ("--ocultas",), 0,
             "de ligereza fallan 1 (se tolera 1) → pasa"),
            ("--ocultas sin la URG", nuevo(), ("--ocultas",), 1, "FALLO produccion: ninguna URG nueva"),
        ]
        for nombre, p, extra, codigo, debe in casos:
            c, salida = corre(PY, PUNTUAR, p, "--montaje", huella, *extra)
            ok = c == codigo and debe in salida
            fallos += not ok
            print(("OK   " if ok else "FALLO ") + nombre + ("" if ok else f" (sale {c}):\n{salida}"))
        # la huella por defecto es <p>.montaje.json; sin ella, o sin proyecto, sale con 2
        c, salida = corre(PY, PUNTUAR, base)
        ok = c == 1 and "Total: 3/9" in salida
        fallos += not ok
        print(("OK   " if ok else "FALLO ") + "la huella por defecto, junto a la carpeta" + ("" if ok else f" (sale {c}):\n{salida}"))
        for nombre, p in (("sin la huella del montaje sale con 2", nuevo()), ("sin proyecto sale con 2", raiz / "no existe")):
            c, salida = corre(PY, PUNTUAR, p)
            ok = c == 2 and "No encuentro" in salida
            fallos += not ok
            print(("OK   " if ok else "FALLO ") + nombre + ("" if ok else f" (sale {c}):\n{salida}"))
    print("Todo bien" if not fallos else f"{fallos} fallos")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
