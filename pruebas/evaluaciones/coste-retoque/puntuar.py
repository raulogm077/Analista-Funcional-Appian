#!/usr/bin/env python3
"""Puntúa la prueba de coste «texto de un botón construido» (tarea 5.12): el cliente pide cambiar el texto del botón
«Nueva solicitud» del panel (PAN-01, `DEM_Dashboard`, construido en EV-01 y en producción).

Uso:
  python3 puntuar.py <p> --llamadas N --comprobar-con-errores K [--montaje <fichero>]

<p> es la carpeta del proyecto, montada con ../evolutivo-urgencia/montar.py y el correo de esta prueba; --montaje, la
huella que escribió (por defecto, <p>.montaje.json, junto a la carpeta). Los cuenta quien pasa la evaluación, en la
sesión del agente, de su encargo al final: N, todas sus llamadas a herramientas (también las de sus subagentes); K, las
veces que pasó comprobar.py y salió con errores. Lo esperado está en esperado.json.

Puntos (umbral: todos):
  hecho                 el correo está catalogado, su informe de impacto (impacto/<FU>*.md) aplicado, la ficha de PAN-01
                        dice el texto nuevo y técnico §13 tiene `DEM_Dashboard` «Modifica» en una unidad Abierta: la
                        aprueba después el jefe de proyecto, una vez (no hacer nada no pasa; meterlo en EV-02, ya
                        aprobada con su alcance, sería construir algo sin aprobar)
  sin_aprobacion        ningún punto de ese informe pide aprobación («Requiere: Sí…») ni queda «Pendiente»: lo construido
                        no la pide (como mucho, «Posible petición de cambio» en el Resumen)
  sin_dt                ninguna DT «Cambio sobre lo construido» nueva: una interfaz no la pide
  comprobar_una_pasada  comprobar.py sin errores ahora, y K = 0
  sin_word_ni_capturas  ningún .docx, .pdf ni .png nuevo o cambiado desde el montaje (salvo fuentes/)
  llamadas              N ≤ tope_llamadas

Imprime cada punto y el total. Sale 0 si se cumplen todos; 1 si no; 2 si falta el proyecto o la huella del montaje.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "evolutivo-urgencia"))   # el montaje es el de «evolutivo con urgencia»
import montar as mt  # noqa: E402

sys.path.insert(0, str(mt.ANALISTA))
import modelo as mo  # noqa: E402
import unidades as un  # noqa: E402


def campo(fila: dict, prefijo: str) -> str:
    return next((v for k, v in fila.items() if k.startswith(prefijo)), "")


def requiere(fila: dict) -> bool:
    """«Sí (…)», como comprobar.py; «—» no."""
    return re.match(r"si(?!\w)", mo.normaliza(mo.sin_comentarios(campo(fila, "requiere"))).strip(" *")) is not None


def dts_construido(m) -> set:
    return {p.id for p in m.vigentes("DT") if "cambio sobre lo construido" in mo.normaliza(p.titulo)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("proyecto")
    ap.add_argument("--llamadas", type=int, required=True, help="llamadas a herramientas del agente")
    ap.add_argument("--comprobar-con-errores", type=int, required=True,
                    help="pasadas de comprobar.py del agente que salieron con errores")
    ap.add_argument("--montaje", help="la huella de montar.py (por defecto, <proyecto>.montaje.json)")
    a = ap.parse_args()
    for s in (sys.stdout, sys.stderr):
        s.reconfigure(encoding="utf-8", errors="replace")
    p = Path(a.proyecto).resolve()
    if not (p / "analisis" / "funcional.md").is_file():
        print(f"No encuentro: {p / 'analisis' / 'funcional.md'}", file=sys.stderr)
        return 2
    huella = mt.lee_huella(p, a.montaje)
    if huella is None:
        print(f"No encuentro la huella del montaje ({a.montaje or mt.montaje_de(p)}): monta el proyecto con "
              "../evolutivo-urgencia/montar.py", file=sys.stderr)
        return 2
    e = json.loads((AQUI / "esperado.json").read_text(encoding="utf-8"))
    m = mo.Proyecto(p)
    ctx = un.Contexto(m)
    hechos = {}

    def punto(clave, ok, detalle):
        hechos[clave] = ok
        print(f"{'OK   ' if ok else 'FALLO'} {clave}: {detalle}")

    fus = mt.fuentes_nuevas(p, huella)
    fu = next((f["id"] for f in fus if f.get("fichero") == e["fuente"]), fus[0]["id"] if fus else None)
    informes = sorted((p / "impacto").glob(f"{fu}*.md")) if fu else []
    leidos = [(f.name, *mo.lee_informe(f)) for f in informes]
    # hecho
    mal = []
    if not fu:
        mal.append(f"{e['fuente']} no está catalogada en fuentes/")
    elif not informes:
        mal.append(f"sin informe de impacto de {fu} (impacto/{fu}.md)")
    elif not any(mo.normaliza(mo.estado_informe(t)).startswith("aplicado") for _, t, _, _ in leidos):
        mal.append(f"el informe de {fu} no está aplicado («{mo.estado_informe(leidos[0][1])}»)")
    pan = e["pantalla"]
    if pan not in m.piezas or mo.normaliza(e["texto_nuevo"]) not in mo.normaliza(mo.sin_comentarios(m.texto(pan))):
        mal.append(f"{pan} no dice «{e['texto_nuevo']}»")
    filas = [f for f in ctx.filas if f["situacion"] == "modifica" and e["objeto"] in map(un.objeto, f["objetos"])]
    abiertas = [f for f in filas if f["unidad"] in ctx.por_id and ctx.por_id[f["unidad"]].estado == un.ABIERTA]
    if not abiertas:
        donde = ", ".join(f"{u} ({ctx.por_id[u].estado})" if u in ctx.por_id else
                          f"{u}, que no está en analisis/cambios.md" if u else "sin unidad"
                          for u in (f["unidad"] for f in filas))
        mal.append(f"técnico §13 sin `{e['objeto']}` «Modifica» en una unidad Abierta" + (f" (está en {donde})" if filas else ""))
    punto("hecho", not mal, "; ".join(mal) or f"{fu} en {', '.join(n for n, *_ in leidos)}, aplicado; {pan} dice "
          f"«{e['texto_nuevo']}»; §13 `{e['objeto']}` Modifica en {abiertas[0]['unidad']} (Abierta)")
    # sin aprobación
    piden = [f"{n} punto {f.get('#', '?')} («{campo(f, 'requiere')}», {campo(f, 'decision') or '—'})"
             for n, _, puntos, _ in leidos for f in puntos
             if requiere(f) or mo.normaliza(campo(f, "decision")).strip(" *").startswith("pendiente")]
    punto("sin_aprobacion", bool(leidos) and not piden,
          "; ".join(piden) if piden else ("ningún punto pide aprobación" if leidos else "sin informe"))
    # sin DT «Cambio sobre lo construido» nueva
    nuevas = sorted(dts_construido(m) - dts_construido(mo.Proyecto(mt.DATOS)))
    punto("sin_dt", not nuevas, ", ".join(nuevas) or "ninguna DT «Cambio sobre lo construido» nueva")
    ok, errores = mt.comprobar(p)
    punto("comprobar_una_pasada", ok and a.comprobar_con_errores == 0,
          ("sin errores" if ok else f"{len(errores)} con errores" + "".join(f"\n  {x}" for x in errores[:10]))
          + f"; pasadas del agente con errores: {a.comprobar_con_errores}")
    regen = mt.regenerados(p, huella)
    punto("sin_word_ni_capturas", not regen, ", ".join(regen) or "ningún Word ni captura nuevos o cambiados")
    punto("llamadas", a.llamadas <= e["tope_llamadas"], f"{a.llamadas} (tope {e['tope_llamadas']})")
    bien = sum(hechos.values())
    pasa = bien == len(e["puntos"])
    print(f"Total: {bien}/{len(e['puntos'])} → {'pasa' if pasa else 'no pasa'}")
    return 0 if pasa else 1


if __name__ == "__main__":
    sys.exit(main())
