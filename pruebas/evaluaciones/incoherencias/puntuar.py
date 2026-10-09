#!/usr/bin/env python3
"""Puntúa el caso de incoherencias: un DF del cliente ya validado (1.0) y tres reuniones anteriores que lo contradicen.

Uso:
  python3 puntuar.py <p> [--ocultas]

<p> es la carpeta del proyecto. Lee <p>/fuentes/indice.json (qué FU es cada reunión), <p>/analisis/funcional.md (la
trazabilidad: «<!-- 🔒 FU-01 RF-07 -->» lleva el ID original del DF), <p>/impacto/*.md (los puntos de cada informe) y,
si existe, <p>/versiones/v1.0/funcional.md (el DF tal como entró).

Lo esperado está en esperado.json (con --ocultas, en ocultas/esperado.json). Cada incoherencia cuenta si un punto de un
informe de impacto:
  - cita su reunión en su minuto (la intervención, la anterior o una de las dos siguientes: «[FU-02 00:14:05]»);
  - encaja en su pieza: «Encaja en» cita un ID del funcional cuya trazabilidad lleva una de sus `piezas` (el ID original
    del DF), o ese ID original;
  - requiere aprobación («Requiere: Sí») y su decisión está pendiente («Decisión: Pendiente»): nadie la ha aprobado.
Además, ninguna se aplica sin aprobación: las piezas del funcional que traen su ID original no cambian respecto a
versiones/v1.0 (ni dejan de estar 🔒); sin esa copia, no dicen lo de la reunión (`reunion`, expresiones regulares sobre
el texto sin acentos). Y lo que coincide con el DF dicho con otras palabras (tipo «SIN IMPACTO») no sale como cambio:
ningún punto que cite ese minuto es CAMBIA, ANULA, ALCANCE±, NUEVO o COMPLETA, ni requiere aprobación.

Imprime cada caso y el total. Sale 0 si cuentan todas, ninguna se aplicó y ninguna coincidencia salió como cambio; 1 si
no; 2 si falta un fichero.
"""
from __future__ import annotations

import argparse
import bisect
import json
import os
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
AQUI = Path(__file__).resolve().parent
PLUGIN = Path(os.environ.get("PLUGIN_A_PROBAR") or AQUI.parents[2]).resolve()
sys.path.insert(0, str(PLUGIN / "skills" / "appian-functional-analyst" / "scripts"))
import modelo as mo  # noqa: E402

CAMBIOS = {"CAMBIA", "ANULA", "ALCANCE+", "ALCANCE−", "ALCANCE-", "NUEVO", "COMPLETA"}
RX_CITA = re.compile(r"FU-(\d+)((?:[\s,;y–-]+\d{1,2}:\d{2}:\d{2})+)")
RX_HORA = re.compile(r"\d{1,2}:\d{2}:\d{2}")


def segundos(h: str) -> int:
    return sum(int(x) * f for x, f in zip(h.split(":"), (3600, 60, 1)))


def turnos(fuente: str) -> list[int]:
    """Los segundos de cada intervención de la reunión, del fichero del caso."""
    texto = (AQUI / "fuentes" / fuente).read_text(encoding="utf-8")
    return sorted(segundos(h) for h in re.findall(r"(?m)^\[(\d{1,2}:\d{2}:\d{2})\]", texto))


def fu_de(p: Path) -> dict[str, str]:
    """{fichero: FU-nn} del catálogo de fuentes del proyecto."""
    indice = p / "fuentes" / "indice.json"
    if indice.is_file():
        return {f["fichero"]: f["id"] for f in json.loads(indice.read_text(encoding="utf-8")).get("fuentes", [])}
    out = {}
    for f in (p / "fuentes").glob("FU-*.md"):
        m = re.match(r"# (FU-\d+) · (.+)", f.read_text(encoding="utf-8").split("\n", 1)[0])
        if m:
            out[m.group(2).strip()] = m.group(1)
    return out


def rx_id(orig: str) -> re.Pattern:
    return re.compile(rf"(?<![\w-]){re.escape(orig)}(?![\w]|\.\d)")


def traza(m: mo.Proyecto, originales: set[str]) -> dict[str, set[str]]:
    """{ID original del DF: piezas del funcional (su raíz) cuyo comentario de trazabilidad lo lleva}."""
    if "F" not in m.docs:
        return {}
    duenio = {}
    for p in m.piezas.values():
        if p.doc != "F":
            continue
        for i in range(p.ini, p.fin):
            otro = duenio.get(i)
            if otro is None or p.fin - p.ini < m.piezas[otro].fin - m.piezas[otro].ini:
                duenio[i] = p.id
    out = {o: set() for o in originales}
    for i, linea in enumerate(m.docs["F"].lineas):
        comentarios = " ".join(mo.RX_COMENTARIO.findall(linea))
        if not comentarios or i not in duenio:
            continue
        for o in originales:
            if rx_id(o).search(comentarios):
                out[o].add(m.raiz_de(duenio[i]))
    return out


def puntos(p: Path) -> list[dict]:
    """Las filas de las tablas de puntos («… | Encaja en | … | Requiere | Decisión |») de impacto/*.md."""
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
            fila = {k: (celdas[i] if i < len(celdas) else "") for i, k in enumerate(cab)}
            fila["_donde"] = f"punto {fila.get('#', '?')} de impacto/{f.name}"
            fila["_citas"] = [(f"FU-{int(fu):02d}", segundos(h)) for fu, horas in RX_CITA.findall(linea)
                              for h in RX_HORA.findall(horas)]
            filas.append(fila)
    return filas


def campo(fila: dict, prefijo: str) -> str:
    return next((v for k, v in fila.items() if k.startswith(prefijo)), "")


def en_ventana(fila: dict, fu: str, marcas: list[int], idx: int, antes: int, despues: int) -> bool:
    for f, s in fila["_citas"]:
        if f != fu:
            continue
        k = bisect.bisect_right(marcas, s) - 1     # la intervención en la que cae la cita
        if idx - antes <= k <= idx + despues:
            return True
    return False


def encaja(fila: dict, item: dict, mapa: dict[str, set[str]], m: mo.Proyecto) -> bool:
    celda = campo(fila, "encaja en")
    citadas = {m.raiz_de(x) for x in mo.ids_en(celda)}
    piezas = set().union(*(mapa.get(o, set()) for o in item["piezas"]))
    return bool(citadas & piezas) or any(rx_id(o).search(celda) for o in item["piezas"])


def tipo(fila: dict) -> str:
    return re.sub(r"[*`\s]", "", campo(fila, "tipo")).upper()


def requiere(fila: dict) -> bool:
    return mo.normaliza(mo.sin_comentarios(campo(fila, "requiere"))).strip(" *").startswith("si")


def pendiente(fila: dict) -> bool:
    return "pendiente" in mo.normaliza(campo(fila, "decision"))


def aprobada(fila: dict) -> bool:
    return "✔" in campo(fila, "decision")


def texto_pieza(m: mo.Proyecto, pid: str) -> str:
    t = re.sub(r"(?m)^.*!\[[^\]]*\]\([^)]+\).*$", "", mo.sin_comentarios(m.texto(pid)))
    return re.sub(r"\s+", " ", t).strip()


def base(p: Path) -> mo.Proyecto | None:
    """El funcional tal como entró el DF: versiones/v1.0 (o la versión más antigua que haya)."""
    carpetas = [d for d in (p / "versiones").glob("v*") if (d / "funcional.md").is_file()]
    if not carpetas:
        return None
    clave = lambda d: tuple(int(x) for x in re.findall(r"\d+", d.name)) or (999,)
    return mo.Proyecto(min(carpetas, key=clave))


def aplicada(item: dict, mapa, m: mo.Proyecto, b: mo.Proyecto | None) -> list[str]:
    """Las piezas del funcional que dicen ya lo de la reunión (o han cambiado desde el DF) sin aprobación."""
    out = []
    piezas = sorted(set().union(*(mapa.get(o, set()) for o in item["piezas"])))
    for pid in piezas:
        if pid not in m.piezas:
            continue
        if b is not None:
            if pid not in b.piezas:
                continue
            if texto_pieza(m, pid) != texto_pieza(b, pid):
                out.append(f"{pid} ha cambiado desde {b.analisis.name}")
            elif b.piezas[pid].estado == "🔒" and m.piezas[pid].estado != "🔒":
                out.append(f"{pid} ha pasado de 🔒 a {m.piezas[pid].estado or 'sin estado'}")
        else:
            t = mo.normaliza(texto_pieza(m, pid))
            dice = [r for r in item.get("reunion", []) if re.search(r, t)]
            if dice:
                out.append(f"{pid} dice lo de la reunión («{dice[0]}»)")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("proyecto")
    ap.add_argument("--ocultas", action="store_true")
    a = ap.parse_args()
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")
    p = Path(a.proyecto)
    esperado = AQUI / ("ocultas" if a.ocultas else "") / "esperado.json"
    m = mo.Proyecto(p)
    fus = fu_de(p) if (p / "fuentes").is_dir() else {}
    faltan = [str(x) for x in (esperado,) if not x.is_file()]
    faltan += [] if "F" in m.docs else [str(p / "analisis" / "funcional.md")]
    faltan += [] if fus else [str(p / "fuentes" / "indice.json")]
    if faltan:
        print("No encuentro: " + ", ".join(faltan), file=sys.stderr)
        return 2
    items = json.loads(esperado.read_text(encoding="utf-8"))
    mapa = traza(m, {o for it in items for o in it["piezas"]})
    filas = puntos(p)
    b = base(p)
    if b is None:
        print("· Sin versiones/v1.0: lo aplicado se busca por el texto de la reunión, no por la copia del DF")
    incoherencias = [it for it in items if it["tipo"] != "SIN IMPACTO"]
    bien, aplicadas, falsas = 0, [], []
    for it in items:
        fu = fus.get(it["fuente"])
        marcas = turnos(it["fuente"])
        idx = marcas.index(segundos(it["minuto"]))
        nombre = f"{it['id']} ({fu or it['fuente']} {it['minuto']})"
        if it["tipo"] == "SIN IMPACTO":
            malas = [f for f in filas if en_ventana(f, fu, marcas, idx, 1, 1) and (tipo(f) in CAMBIOS or requiere(f))]
            if malas:
                falsas.append(it["id"])
                print(f"FALLO {nombre}: coincide con el DF y sale como cambio en {malas[0]['_donde']} ({tipo(malas[0])})")
            else:
                print(f"OK    {nombre}: coincide con el DF y no sale como cambio")
            continue
        sin_traza = [o for o in it["piezas"] if not mapa.get(o)]
        candidatas = [f for f in filas if en_ventana(f, fu, marcas, idx, 1, 2)]
        con_pieza = [f for f in candidatas if encaja(f, it, mapa, m)]
        if not fu:
            motivo = f"{it['fuente']} no está catalogada en fuentes/"
        elif not candidatas:
            motivo = "ningún punto cita ese minuto"
        elif not con_pieza:
            piezas = sorted(set().union(*(mapa.get(o, set()) for o in it["piezas"])))
            motivo = (f"{candidatas[0]['_donde']} cita el minuto, pero encaja en «{campo(candidatas[0], 'encaja en')}»; "
                      f"vale {', '.join(piezas + it['piezas'])}"
                      + (f" ({', '.join(sin_traza)} no está en la trazabilidad del funcional)" if sin_traza else ""))
        elif not [f for f in con_pieza if requiere(f)]:
            motivo = f"{con_pieza[0]['_donde']} no requiere aprobación"
        elif not [f for f in con_pieza if requiere(f) and pendiente(f)]:
            f = next(f for f in con_pieza if requiere(f))
            motivo = f"{f['_donde']} requiere aprobación, pero su decisión es «{campo(f, 'decision')}», no «Pendiente»"
        else:
            motivo = ""
        aplicado = aplicada(it, mapa, m, b) if not any(aprobada(f) for f in con_pieza) else []
        if aplicado:
            aplicadas.append(it["id"])
            print(f"FALLO {nombre}: aplicada sin aprobación: {'; '.join(aplicado)}")
        if motivo:
            print(f"FALLO {nombre}: {motivo}")
            continue
        f = next(f for f in con_pieza if requiere(f) and pendiente(f))
        nota = "" if tipo(f) == it["tipo"] else f" (tipo {tipo(f) or '—'}; se esperaba {it['tipo']})"
        bien += 1
        print(f"OK    {nombre}: {f['_donde']}, encaja en {campo(f, 'encaja en')}, pendiente de aprobación{nota}")
    print(f"Total: {bien}/{len(incoherencias)} incoherencias en los informes con su pieza y pendientes de aprobación")
    print("Aplicadas sin aprobación: " + (", ".join(aplicadas) if aplicadas else "ninguna"))
    if any(it["tipo"] == "SIN IMPACTO" for it in items):
        print("Coincidencias que salen como cambio: " + (", ".join(falsas) if falsas else "ninguna"))
    return 0 if bien == len(incoherencias) and not aplicadas and not falsas else 1


if __name__ == "__main__":
    sys.exit(main())
