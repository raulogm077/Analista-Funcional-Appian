#!/usr/bin/env python3
"""Crea la carpeta de un proyecto y dice en qué punto está.

  proyecto.py iniciar <carpeta> --nombre "Solicitudes de autorización" [--cliente …] [--direccion …] [--tipo "evolutivo de X"]
  proyecto.py estado  <carpeta>      versión, fuentes sin procesar, pendientes, pantallas, DF entregado
  proyecto.py copia   <carpeta>      guarda analisis/*.md en versiones/v<versión>/ antes de cambiarlo

`iniciar` no toca nada que ya exista.
"""
import argparse
import datetime
import pathlib
import re
import shutil
import sys
sys.dont_write_bytecode = True  # sin __pycache__ en el plugin: no se escribe fuera del proyecto

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import modelo as mo

PLANTILLAS = pathlib.Path(__file__).resolve().parents[1] / "assets" / "plantillas"
CARPETAS = ["fuentes", "notas", "impacto", "analisis/diagramas", "prototipo", "entregables", "versiones"]


def iniciar(a):
    raiz = pathlib.Path(a.carpeta)
    for c in CARPETAS:
        (raiz / c).mkdir(parents=True, exist_ok=True)
    datos = {"proyecto": a.nombre, "cliente": a.cliente or "—", "direccion": a.direccion or "—",
             "tipo": a.tipo or "nuevo", "fecha": datetime.date.today().isoformat()}
    destinos = {"proyecto.md": raiz / "proyecto.md", "funcional.md": raiz / "analisis" / "funcional.md",
                "tecnico.md": raiz / "analisis" / "tecnico.md", "decisiones.md": raiz / "analisis" / "decisiones.md"}
    for nombre, destino in destinos.items():
        if destino.exists():
            print(f"= {destino} (ya existe, no se toca)")
            continue
        texto = (PLANTILLAS / nombre).read_text(encoding="utf-8")
        for k, v in datos.items():
            texto = texto.replace("{" + k + "}", v)
        destino.write_text(texto, encoding="utf-8")
        print(f"+ {destino}")
    print(f"Carpetas: {', '.join(CARPETAS)}")


def tabla(texto, titulo):
    m = re.search(rf"^## {re.escape(titulo)}\s*$(.*?)(?=^## |\Z)", texto, re.M | re.S)
    if not m:
        return []
    filas = [mo.celdas(l) for l in m.group(1).split("\n") if l.startswith("|")]
    return [f for f in filas[2:] if any(f)]


def estado(a):
    raiz = pathlib.Path(a.carpeta)
    pm = raiz / "proyecto.md"
    texto = pm.read_text(encoding="utf-8") if pm.exists() else ""
    m = mo.Proyecto(raiz)
    print(f"# {texto.splitlines()[0][2:] if texto else raiz.name}")
    v = m.version("F")
    vs = f"{v[0]}.{v[1]}" if v else "—"
    print(f"Análisis: versión {vs}")
    entregado = re.search(r"DF entregado:\s*([\d.]+)", texto)
    if entregado and entregado.group(1) != vs:
        print(f"· El último DF entregado es el {entregado.group(1)}: el Word está desactualizado")

    # fuentes
    catalogadas = sorted({re.match(r"(FU-\d+)", f.name).group(1) for f in (raiz / "fuentes").glob("FU-*.md")})
    procesadas = {f[0] for f in tabla(texto, "Fuentes procesadas")}
    sin = [x for x in catalogadas if x not in procesadas]
    print(f"Fuentes: {len(catalogadas)} catalogadas, {len(procesadas)} procesadas" +
          (f"; sin procesar: {', '.join(sin)}" if sin else ""))
    for inf in sorted((raiz / "impacto").glob("FU-*.md")):
        t = inf.read_text(encoding="utf-8")
        if re.search(r"Estado:\s*pendiente", t, re.I):
            print(f"· {inf.name}: informe pendiente de aprobar o de aplicar")

    if not m.docs:
        print("Sin análisis todavía.")
        return
    pc = sorted(p.id for p in m.vigentes("PC"))
    pt = sorted(p.id for p in m.vigentes("PT"))
    print(f"Pendiente de confirmar: {len(pc)}" + (f" ({', '.join(pc)})" if pc else ""))
    print(f"Pendientes técnicos: {len(pt)}" + (f" ({', '.join(pt)})" if pt else ""))
    pan = sorted(p.id for p in m.vigentes("PAN"))
    sin_cap = [p for p in pan if not re.search(r"!\[[^\]]*\]\([^)]+\)", m.texto(p))]
    print(f"Pantallas: {len(pan)}" + (f"; sin captura: {', '.join(sin_cap)}" if sin_cap else ""))
    conf = [p for p in pan if m.piezas[p].estado == "🔒"]
    if conf:
        print(f"Pantallas validadas por el cliente (🔒; no se cambian sin el visto bueno del analista): {', '.join(conf)}")
        print(f"  para el prototipo: --confirmadas {','.join(conf)}")
    if "T" in m.docs:
        tv = m.version("T")
        empezado = bool(m.vigentes("DT")) or any("campo" in [mo.normaliza(c) for c in cab] for _, cab, _ in m.tablas("T", "3"))
        print("Técnico: " + (f"versión {tv[0]}.{tv[1]}" if tv else "sin versión") + ("" if empezado else ", sin empezar"))
    sig = re.search(r"^## Siguiente paso\s*\n+(.+)", texto, re.M)
    if sig:
        print(f"Siguiente paso: {sig.group(1).strip()}")


def copia(a):
    raiz = pathlib.Path(a.carpeta)
    m = mo.Proyecto(raiz)
    v = m.version("F")
    if not v:
        sys.exit("funcional.md no tiene «Versión: x.y»")
    destino = raiz / "versiones" / f"v{v[0]}.{v[1]}"
    destino.mkdir(parents=True, exist_ok=True)
    for nombre in mo.DOCS.values():
        f = m.analisis / nombre
        if f.exists():
            shutil.copy2(f, destino / nombre)
    print(f"Copia de la versión {v[0]}.{v[1]} en {destino}. Al terminar: comprobar.py {raiz} --anterior {destino}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("iniciar"); s.add_argument("carpeta"); s.add_argument("--nombre", required=True)
    s.add_argument("--cliente"); s.add_argument("--direccion"); s.add_argument("--tipo")
    s.set_defaults(f=iniciar)
    s = sub.add_parser("estado"); s.add_argument("carpeta"); s.set_defaults(f=estado)
    s = sub.add_parser("copia"); s.add_argument("carpeta"); s.set_defaults(f=copia)
    a = ap.parse_args()
    for st in (sys.stdout, sys.stderr):
        st.reconfigure(encoding="utf-8", errors="replace")
    a.f(a)


if __name__ == "__main__":
    main()
