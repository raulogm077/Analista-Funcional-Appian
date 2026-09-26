#!/usr/bin/env python3
"""Une las secciones comunes y los módulos de un análisis grande en un único ddf.md.

Uso:
  unir_modulos.py ddf-base.md modulos/M1.md modulos/M2.md ... -o ddf.md [--diagramas diagramas/]

- ddf-base.md: secciones comunes (1–5 y, si las hay, 15, 16 con los escenarios de extremo a extremo y 17
  con riesgos generales). Si incluye una línea «Módulos: M1 Nombre · M2 Nombre…», de ahí salen los nombres.
- Cada módulo: secciones «## n. Título — Mx» (6, 8–14, 17). Sus títulos internos bajan un nivel.
- Las filas «| D-? |» de los registros de decisiones de los módulos se juntan en una sola tabla al final
  de la Sec 17, ordenadas por fecha y numeradas D-001…; «sustituida por la decisión del <fecha> [FU-xx …]»
  se resuelve al ID correspondiente.
- La Sec 7 (casos de uso) y la matriz de la Sec 16 se generan (ddf_indice.py derivadas).
- Con --diagramas, cada bloque Mermaid se guarda como .mmd y se enlaza su imagen (falta renderizar).
"""
import argparse, pathlib, re, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import ddf_indice

TITULOS = {6: "Flujo BPM end-to-end", 7: "Casos de uso funcionales", 8: "Requisitos funcionales",
           9: "Reglas de negocio", 10: "Modelo de datos funcional", 11: "Estados y ciclo de vida",
           12: "Diseño funcional de pantallas", 13: "Integraciones y gestión documental",
           14: "Notificaciones, alertas y escalados", 15: "Reporting y trazabilidad",
           16: "Criterios de aceptación y cobertura", 17: "Riesgos, dependencias y validaciones pendientes"}
CAB_D = "| ID | Fecha | Fuente | Tipo | Decisión | Antes | Piezas | Vigente |"


def partes(texto):
    """{n: [líneas]} con el contenido de cada «## n.» (sin el título)."""
    out, n = {}, None
    for l in texto.split("\n"):
        m = re.match(r"^## (\d+)\.", l)
        if m:
            n = int(m.group(1))
            out.setdefault(n, [])
            continue
        if n is not None:
            out[n].append(l)
    return out


def baja_titulos(lineas):
    res, codigo = [], False
    for l in lineas:
        if l.startswith("```"):
            codigo = not codigo
        if not codigo and re.match(r"^#{2,5} ", l):
            l = "#" + l
        res.append(l)
    return res


def saca_decisiones(lineas, modulo, orden):
    """Saca las filas D-? del módulo y quita su apartado «Registro de decisiones» (va a la tabla común)."""
    filas, res, dentro = [], [], False
    for l in lineas:
        if re.match(r"^#+ ", l):
            dentro = bool(re.search(r"Registro de decisiones", l))
            if dentro:
                continue
        if re.match(r"^\|\s*D-\?\s*\|", l):
            c = [x.strip() for x in l.strip().strip("|").split("|")]
            filas.append({"orden": orden + len(filas), "modulo": modulo, "celdas": c})
            continue
        if not dentro:
            res.append(l)
    return res, filas


def numera_decisiones(filas):
    filas.sort(key=lambda f: (f["celdas"][1], f["orden"]))
    for k, f in enumerate(filas, 1):
        f["id"] = f"D-{k:03d}"
        f["celdas"][0] = f["id"]
    for f in filas:
        v = f["celdas"][7] if len(f["celdas"]) > 7 else ""
        m = re.search(r"sustituida por la decisi[oó]n del (\d{4}-\d\d-\d\d)\s*(\[FU-\d\d[^\]]*\])?", v)
        if not m:
            continue
        fecha, cita = m.group(1), (m.group(2) or "").strip("[]")
        cand = [g for g in filas if g["celdas"][1] == fecha and g is not f]
        if cita:
            cand = [g for g in cand if cita in g["celdas"][2]] or cand
        mismas = [g for g in cand if g["modulo"] == f["modulo"]]
        cand = mismas or cand
        if len(cand) == 1:
            f["celdas"][7] = v[:m.start()] + f"sustituida por {cand[0]['id']}" + v[m.end():]
    return ["| " + " | ".join(f["celdas"]) + " |" for f in filas]


def main():
    for s in (sys.stdout, sys.stderr):
        s.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("base")
    ap.add_argument("modulos", nargs="+")
    ap.add_argument("-o", required=True)
    ap.add_argument("--diagramas")
    a = ap.parse_args()

    base = pathlib.Path(a.base).read_text(encoding="utf-8")
    nombres = {}
    mm = re.search(r"M[oó]dulos:\s*(.+)", base)
    if mm:
        for x in re.finditer(r"(M\d+)\s+([^·\n]+)", mm.group(1)):
            nombres[x.group(1)] = x.group(2).strip()
    pb = partes(base)
    cab = base.split("\n## 6.")[0].split("\n## 15.")[0].rstrip()
    cab = re.split(r"\n## (?:1[5-7])\.", cab)[0].rstrip()

    mods = []
    for f in a.modulos:
        t = pathlib.Path(f).read_text(encoding="utf-8")
        m = re.search(r"—\s*(M\d+)\s*$", t, re.M)
        mid = m.group(1) if m else pathlib.Path(f).stem
        mods.append((mid, partes(t)))

    out, decisiones = [cab, ""], []
    for n in range(6, 18):
        out += [f"## {n}. {TITULOS[n]}", ""]
        if n == 7:
            continue  # la genera derivadas
        if n in pb and n in (15, 16, 17):
            out += [l for l in pb[n]] + [""]
        for mid, p in mods:
            if n not in p:
                continue
            lineas = p[n]
            if n == 17:
                lineas, fil = saca_decisiones(lineas, mid, len(decisiones) * 1000)
                decisiones += fil
            titulo = f"### {mid} · {nombres[mid]}" if mid in nombres else f"### {mid}"
            out += [titulo, ""] + baja_titulos(lineas) + [""]
        if n == 17 and decisiones:
            out += ["### Registro de decisiones", "",
                    "Historial de los cambios de criterio: cada fila dice qué se decidió, cuándo, qué había antes "
                    "y qué piezas afecta. El resto del documento es el estado vigente.", "",
                    CAB_D, "|---|---|---|---|---|---|---|---|"] + numera_decisiones(decisiones) + [""]
    texto = re.sub(r"\n{3,}", "\n\n", "\n".join(out)).rstrip() + "\n"
    if a.diagramas:
        texto, nd = ddf_indice.extrae_diagramas(texto, a.diagramas)
        print(f"{len(nd)} diagramas guardados en {a.diagramas}/ (renderiza con render_mermaid.py)")
    texto = ddf_indice.aplica_derivadas(texto)
    pathlib.Path(a.o).write_text(texto, encoding="utf-8")
    print(f"{a.o}: {len(texto.splitlines())} líneas, {len(mods)} módulos, {len(decisiones)} decisiones")


if __name__ == "__main__":
    main()
