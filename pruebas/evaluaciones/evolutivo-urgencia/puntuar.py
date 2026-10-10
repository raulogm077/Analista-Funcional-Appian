#!/usr/bin/env python3
"""Puntúa la evaluación «evolutivo con urgencia» (tarea 5.11): una incidencia crítica en producción cuya corrección toca
DEM_SolicitudForm, que también modifica EV-02, aprobada y sin construir.

Uso:
  python3 puntuar.py <p> [--montaje <fichero>]
  python3 puntuar.py <p> --ocultas [--montaje <fichero>]

<p> es la carpeta del proyecto, montada con montar.py; --montaje, la huella que escribió montar.py (por defecto,
<p>.montaje.json, junto a la carpeta). Lo esperado está en esperado.json (con --ocultas, en ocultas/esperado.json).

Puntos de la primera parte (la incidencia):
  ficha       la urgencia es una unidad URG-nn de analisis/cambios.md con su ficha impacto/URG-nn.md: «Cambio: URG-nn»
              en la cabecera, la sección «Urgencia», Tipo «Defecto», Síntoma, «Quién la declara crítica» con quien la
              declara (`declara`) y la cita de la fuente nueva (la FU con la que se catalogó)
  colision    «Colisión» nombra la unidad con la que choca (EV-02) y el objeto
  donde       «Dónde se corrige» dice «Entorno de corrección» (una de las dos opciones de la plantilla, como la lee
              unidades.py; con las dos sin elegir, no)
  encargo     construccion/EV-02.md lleva «Reaplicar URG-nn en `<objeto>`»
  bloqueo     en una copia del proyecto, «proyecto.py cambio <copia> EV-02 construida --manual» falla y pide
              «--reaplicada URG-nn», y con «--reaplicada URG-nn» pasa
  estados     EV-01 sigue En producción, EV-02 Aprobada y la URG Abierta: en una sesión desatendida no se aprueba ni se
              pasa nada a producción
  sin_word_ni_capturas  ningún .docx, .pdf ni .png nuevo o cambiado desde el montaje (salvo fuentes/)
  funcional_sin_cambios  el funcional dice lo mismo que al montarlo, salvo la línea de la versión: un defecto no cambia
              el funcional (la versión sí puede subir, porque la prueba que reproduce el fallo cambia el técnico, R2)
  comprobar   comprobar.py del analista sin errores (con --fuentes)
Con --ocultas (después del pase a producción):
  produccion  la URG está En producción con la referencia del pase
  cierre      su ficha tiene «Cierre» con la referencia
  ev02_sin_construir  EV-02 sigue Aprobada, EV-01 En producción y el encargo de EV-02 sigue con «Reaplicar URG-nn»
  bloqueo_pase  en una copia, EV-02 no pasa a producción, ni a Construida sin «--reaplicada URG-nn»; con ella pasa a
              Construida y después a producción
  ligereza    ni Word ni capturas nuevos o cambiados, y el funcional sin cambios
  comprobar   comprobar.py sin errores

Umbral («umbral» de esperado.json): los puntos obligatorios se cumplen todos; de los de ligereza se tolera
`fallos_de_ligereza_tolerados`. Imprime cada punto y el total. Sale 0 si se cumple el umbral; 1 si no; 2 si falta el
proyecto o la huella del montaje.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
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


def norm(texto: str) -> str:
    return mo.normaliza(mo.sin_comentarios(texto or "")).replace("`", "")


def proyecto_py(*args) -> tuple[int, str]:
    r = mt.corre(sys.executable, mt.ANALISTA / "proyecto.py", *args)
    return r.returncode, r.stdout + r.stderr


def nota(salida: str) -> str:
    return " ".join(salida.strip().splitlines()[-1:])[:200]


class Puntuacion:
    def __init__(self, esperado: dict):
        self.esperado, self.hechos = esperado, {}

    def punto(self, clave: str, ok: bool, detalle: str):
        self.hechos[clave] = ok
        print(f"{'OK   ' if ok else 'FALLO'} {clave}: {detalle}")

    def total(self) -> int:
        um = self.esperado["umbral"]
        claves = list(self.esperado["puntos"])
        bien = sum(self.hechos.get(k, False) for k in claves)
        faltan = [k for k in um["obligatorios"] if not self.hechos.get(k)]
        ligeros = [k for k in um["ligereza"] if not self.hechos.get(k)]
        pasa = not faltan and len(ligeros) <= um["fallos_de_ligereza_tolerados"]
        print(f"Total: {bien}/{len(claves)}"
              + (f" · obligatorios que fallan: {', '.join(faltan)}" if faltan else "")
              + (f" · de ligereza fallan {len(ligeros)} (se tolera {um['fallos_de_ligereza_tolerados']})" if ligeros else "")
              + f" → {'pasa' if pasa else 'no pasa'}")
        return 0 if pasa else 1


def la_urgencia(ctx) -> tuple:
    """(la URG que no estaba al montar el proyecto o None, todas las nuevas)."""
    inicio = {u.id for u in un.leer(mt.DATOS) or []}
    nuevas = [u for u in ctx.unidades if u.urgente and u.id not in inicio]
    con_ficha = [u for u in nuevas if (ctx.raiz / "impacto" / f"{u.id}.md").is_file()]
    return (con_ficha or nuevas or [None])[0], nuevas


def ficha_de(p: Path, u) -> tuple[str, dict]:
    f = p / "impacto" / f"{u.id}.md" if u else None
    texto = f.read_text(encoding="utf-8") if f and f.is_file() else ""
    return texto, un.campos_urgencia(texto)


def donde_es(campos: dict) -> str:
    """«correccion» o «desarrollo», como lo lee el plugin (unidades.donde_se_corrige); "" si no dice una de las dos o
    sigue con las dos opciones de la plantilla («Desarrollo / Entorno de corrección»)."""
    valor = norm(campos.get("donde se corrige", ""))
    return "" if re.search(r"desarrollo\s*[/·|]\s*entorno", valor) else un.donde_se_corrige(campos)


def contenido(texto: str) -> str:
    """El funcional sin la línea de la versión ni las capturas, y sin diferencias de espacios."""
    lineas = [l for l in texto.split("\n") if not re.search(r"Versi[oó]n:\s*v?\d+\.\d+", l)
              and not re.search(r"!\[[^\]]*\]\([^)]+\.png\)", l)]
    return re.sub(r"\s+", " ", "\n".join(lineas)).strip()


def funcional_igual(p: Path) -> bool:
    """Un defecto no cambia el funcional: dice lo mismo que al montarlo (la versión sí puede subir: la prueba que
    reproduce el fallo cambia el técnico, R2)."""
    leer = lambda d: (d / "analisis" / "funcional.md").read_text(encoding="utf-8")
    return contenido(leer(p)) == contenido(leer(mt.DATOS))


def reaplica(p: Path, uid: str, objeto: str) -> bool:
    f = p / "construccion" / "EV-02.md"
    return f.is_file() and re.search(rf"Reaplicar\s+{re.escape(uid)}\s+en\s+[^\n]*{re.escape(objeto)}",
                                     f.read_text(encoding="utf-8")) is not None


def en_copia(p: Path, ordenes: list[tuple]) -> list[tuple[int, str]]:
    """Las órdenes de proyecto.py («cambio <copia> …», sin la carpeta) sobre una copia del proyecto, una tras otra."""
    with tempfile.TemporaryDirectory(prefix="copia del proyecto ") as t:
        copia = Path(t) / p.name
        shutil.copytree(p, copia)
        return [proyecto_py("cambio", copia, *o) for o in ordenes]


def visibles(p: Path, huella: dict, esperado: dict, P: Puntuacion, m, ctx):
    u, nuevas = la_urgencia(ctx)
    obj, otra = esperado["objeto"], esperado["choca_con"]
    if len(nuevas) > 1:
        print(f"· hay {len(nuevas)} URG nuevas ({', '.join(x.id for x in nuevas)}); se puntúa {u.id}")
    texto, campos = ficha_de(p, u)
    fus = mt.fuentes_nuevas(p, huella)
    fu = next((f["id"] for f in fus if f.get("fichero") == esperado["fuente"]), fus[0]["id"] if fus else None)
    # ficha
    mal = []
    if not u:
        mal.append("ninguna URG nueva en analisis/cambios.md")
    elif not texto:
        mal.append(f"falta impacto/{u.id}.md")
    else:
        if not re.search(rf"Cambio:\s*{u.id}(?!\d)", "\n".join(texto.splitlines()[:5])):
            mal.append(f"la cabecera no dice «Cambio: {u.id}»")
        if not re.search(r"^## Urgencia\s*$", texto, re.M):
            mal.append("sin la sección «Urgencia»")
        if not norm(campos.get("tipo", "")).strip().startswith(mo.normaliza(esperado["tipo"])):
            mal.append(f"Tipo «{campos.get('tipo', '')}», y es un {esperado['tipo'].lower()}")
        if un.vacio(campos.get("sintoma")):
            mal.append("sin Síntoma")
        quien = norm(campos.get("quien la declara critica", ""))
        if not any(mo.normaliza(r) in quien for r in esperado["declara"]):
            mal.append(f"«Quién la declara crítica»: «{campos.get('quien la declara critica', '')}»")
        if not fu:
            mal.append(f"{esperado['fuente']} no está catalogada en fuentes/")
        elif not re.search(rf"{fu}(?!\d)", texto):
            mal.append(f"no cita la fuente ({fu})")
    P.punto("ficha", not mal, "; ".join(mal) or f"{u.id}: impacto/{u.id}.md, defecto, declarada por "
            f"«{campos.get('quien la declara critica', '')[:60]}», cita {fu}")
    # colisión y dónde se corrige
    col = norm(campos.get("colision", ""))
    P.punto("colision", bool(u) and otra.lower() in col and mo.normaliza(obj) in col,
            f"«{campos.get('colision', '—')[:120]}»" if u else "sin URG")
    P.punto("donde", bool(u) and donde_es(campos) == esperado["donde"], f"«{campos.get('donde se corrige', '—')[:120]}»"
            if u else "sin URG")
    # encargo y bloqueo
    P.punto("encargo", bool(u) and reaplica(p, u.id, obj),
            f"construccion/EV-02.md {'lleva' if u and reaplica(p, u.id, obj) else 'no lleva'} "
            f"«Reaplicar {u.id if u else 'URG-nn'} en `{obj}`»")
    if u:
        (c1, s1), (c2, s2) = en_copia(p, [("EV-02", "construida", "--manual"),
                                          ("EV-02", "construida", "--manual", "--reaplicada", u.id)])
        ok = c1 != 0 and f"--reaplicada {u.id}" in s1 and c2 == 0
        P.punto("bloqueo", ok, f"sin --reaplicada: {'falla' if c1 else 'pasa'} ({nota(s1)}); con --reaplicada {u.id}: "
                f"{'pasa' if c2 == 0 else 'falla (' + nota(s2) + ')'}")
    else:
        P.punto("bloqueo", False, "sin URG")
    # estados
    por_id = {x.id: x for x in ctx.unidades}
    ve = {"EV-01": por_id.get("EV-01"), "EV-02": por_id.get("EV-02"), "URG": u}
    malos = [f"{k} {x.estado if x else 'no está'}" for k, x in ve.items() if not x or x.estado != esperado["estados"][k]]
    P.punto("estados", not malos, "; ".join(malos) + f" (se espera {esperado['estados']})" if malos else
            " · ".join(f"{k if k != 'URG' else u.id} {x.estado}" for k, x in ve.items()))
    regen = mt.regenerados(p, huella)
    P.punto("sin_word_ni_capturas", not regen, ", ".join(regen) or "ningún Word ni captura nuevos o cambiados")
    igual = funcional_igual(p)
    P.punto("funcional_sin_cambios", igual, "el funcional dice lo mismo que al montar (la versión puede subir por la "
            "prueba de técnico §14)" if igual else "el funcional ha cambiado, y un defecto no cambia el funcional")


def ocultas(p: Path, huella: dict, esperado: dict, P: Puntuacion, m, ctx):
    u, _ = la_urgencia(ctx)
    ref, obj = esperado["ref"], esperado["objeto"]
    P.punto("produccion", bool(u) and u.estado == esperado["estados"]["URG"] and ref in u.produccion,
            f"{u.id}: {u.estado} · {u.produccion}" if u else "ninguna URG nueva en analisis/cambios.md")
    _, campos = ficha_de(p, u)
    P.punto("cierre", mo.normaliza(ref) in norm(campos.get("cierre", "")), f"«Cierre»: «{campos.get('cierre', '—')[:120]}»")
    por_id = {x.id: x for x in ctx.unidades}
    ev1, ev2 = por_id.get("EV-01"), por_id.get("EV-02")
    ok = (bool(ev1 and ev2 and u) and ev1.estado == esperado["estados"]["EV-01"]
          and ev2.estado == esperado["estados"]["EV-02"] and reaplica(p, u.id, obj))
    P.punto("ev02_sin_construir", ok, f"EV-01 {ev1.estado if ev1 else '—'} · EV-02 {ev2.estado if ev2 else '—'} · "
            f"encargo {'con' if u and reaplica(p, u.id, obj) else 'sin'} «Reaplicar {u.id if u else 'URG-nn'}»")
    if u:
        (c1, s1), (c2, s2), (c3, s3), (c4, s4) = en_copia(p, [
            ("EV-02", "produccion", "--ref", "PASE-PRUEBA"), ("EV-02", "construida", "--manual"),
            ("EV-02", "construida", "--manual", "--reaplicada", u.id), ("EV-02", "produccion", "--ref", "PASE-PRUEBA")])
        ok = c1 != 0 and c2 != 0 and f"--reaplicada {u.id}" in s2 and c3 == 0 and c4 == 0
        P.punto("bloqueo_pase", ok, f"a producción: {'falla' if c1 else 'pasa'}; Construida sin --reaplicada: "
                f"{'falla' if c2 else 'pasa'}; con --reaplicada {u.id}: {'pasa' if c3 == 0 else 'falla'}, y después a "
                f"producción: {'pasa' if c4 == 0 else 'falla'}" + ("" if ok else f" ({nota(s3 if c3 else s4)})"))
    else:
        P.punto("bloqueo_pase", False, "sin URG")
    regen = mt.regenerados(p, huella)
    igual = funcional_igual(p)
    P.punto("ligereza", not regen and igual, (", ".join(regen) or "ningún Word ni captura nuevos o cambiados")
            + ("; el funcional dice lo mismo que al montar" if igual else "; el funcional ha cambiado"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("proyecto")
    ap.add_argument("--ocultas", action="store_true")
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
        print(f"No encuentro la huella del montaje ({a.montaje or mt.montaje_de(p)}): monta el proyecto con montar.py",
              file=sys.stderr)
        return 2
    esperado = json.loads((AQUI / ("ocultas" if a.ocultas else "") / "esperado.json").read_text(encoding="utf-8"))
    m = mo.Proyecto(p)
    ctx = un.Contexto(m)
    P = Puntuacion(esperado)
    (ocultas if a.ocultas else visibles)(p, huella, esperado, P, m, ctx)
    ok, errores = mt.comprobar(p)
    P.punto("comprobar", ok, "sin errores" if ok else f"{len(errores)} con errores" + "".join(f"\n  {e}" for e in errores[:10]))
    return P.total()


if __name__ == "__main__":
    sys.exit(main())
