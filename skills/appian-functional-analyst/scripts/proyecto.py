#!/usr/bin/env python3
"""Crea la carpeta de un proyecto y dice en qué punto está.

  proyecto.py iniciar  <carpeta> --nombre "Solicitudes de autorización" [--cliente …] [--direccion …] [--tipo "evolutivo de X"]
  proyecto.py estado   <carpeta>     versión, cliente y marca, DF enviado, fuentes sin procesar, pendientes, pantallas
  proyecto.py copia    <carpeta>     guarda analisis/*.md en versiones/v<versión>/ antes de cambiarlo
  proyecto.py entregar <carpeta>     el Word sale hacia el cliente: «DF entregado» y el fichero en «Entregados»

`iniciar` no toca nada que ya exista. `entregar` solo cuando el Word se envía, nunca en una sesión desatendida.
"""
import argparse
import datetime
import pathlib
import re
import shutil
import sys
import unicodedata
sys.dont_write_bytecode = True  # sin __pycache__ en el plugin: no se escribe fuera del proyecto

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import modelo as mo

PLANTILLAS = pathlib.Path(__file__).resolve().parents[1] / "assets" / "plantillas"
CARPETAS = ["fuentes", "notas", "impacto", "analisis/diagramas", "prototipo", "entregables", "versiones"]
# «DF entregado: 1.1 · 2026-10-10» (entregar) o, en proyectos anteriores, «DF entregado: 1.0 (2026-09-12)»
RX_ENTREGADO = re.compile(r"DF entregado:\s*v?(\d+\.\d+)(?:\s*(?:·\s*|\()(\d{4}-\d{2}-\d{2}))?")


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
    cliente = re.search(r"Cliente:\s*([^·\n]+)", texto)
    marcas = sorted(f"prototipo/{b.name}" for b in (raiz / "prototipo").glob("brand-*.json"))
    print(f"Cliente: {cliente.group(1).strip() if cliente else '—'} · Marca: {', '.join(marcas) or 'sin marca'}")
    entregado = RX_ENTREGADO.search(texto)
    if entregado:   # el Word se genera al enviarlo o si se pide: aquí solo se informa
        fecha = f" ({entregado.group(2)})" if entregado.group(2) else ""
        print(f"DF en Word: último enviado {entregado.group(1)}{fecha}, versión actual {vs}")

    # informes de impacto: los pendientes; las PAN de un cambio aprobado (✔) en una versión posterior al prototipo que se
    # enseñó (el último prototipo/app-vX.Y.json; sin ninguno, todas), que el prototipo rehace; y las fuentes que cuentan
    # como procesadas aunque no estén en la tabla: la de un informe «sin cambios» y la que cita una Decisión («✔ FU-09»)
    ensenadas = [tuple(map(int, x.groups())) for b in (raiz / "prototipo").glob("app-v*.json")
                 for x in [re.match(r"app-v(\d+)\.(\d+)\.json$", b.name)] if x]
    ultima = max(ensenadas) if ensenadas else None
    aprobadas, procesadas, pendientes = set(), {f[0] for f in tabla(texto, "Fuentes procesadas")}, []
    for nombre, t, puntos, _ in mo.informes(raiz):
        # «Estado: pendiente» o «Estado: aplicado en 1.2; pendientes de aprobación: puntos 4 y 7» (actualizacion.md)
        e = mo.estado_informe(t)
        if re.search(r"pendientes? de aprobaci[oó]n:\s*puntos?\s+\d", e, re.I):
            pendientes.append(f"· {nombre}.md: {e}")
        elif re.match(r"pendiente", e, re.I):
            pendientes.append(f"· {nombre}.md: informe pendiente de aprobar o de aplicar")
        if re.match(r"sin cambios", e, re.I):
            procesadas |= set(re.findall(r"FU-\d+", nombre))
        procesadas |= {x for f in puntos for x in re.findall(r"FU-\d+", f.get("decision", ""))}
        aplicado = re.match(r"aplicado en v?(\d+)\.(\d+)", e, re.I)
        if aplicado and (ultima is None or tuple(map(int, aplicado.groups())) > ultima):
            aprobadas |= {x for f in puntos if "✔" in f.get("decision", "")
                          for col in ("encaja en", "cambio propuesto") for x in mo.ids_en(f.get(col, ""))
                          if x.startswith("PAN-")}
    catalogadas = sorted({re.match(r"(FU-\d+)", f.name).group(1) for f in (raiz / "fuentes").glob("FU-*.md")})
    sin = [x for x in catalogadas if x not in procesadas]
    print(f"Fuentes: {len(catalogadas)} catalogadas, {len(procesadas)} procesadas" +
          (f"; sin procesar: {', '.join(sin)}" if sin else ""))
    for x in pendientes:
        print(x)

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
        cambian = [p for p in conf if p in aprobadas]
        if cambian:
            desde = f"después de app-v{ultima[0]}.{ultima[1]}.json" if ultima else "(sin app-vX.Y.json)"
            print(f"  con un cambio aprobado {desde}, el prototipo las rehace: {', '.join(cambian)}")
        quedan = [p for p in conf if p not in aprobadas]
        print(f"  para el prototipo: --confirmadas {','.join(quedan)}" if quedan else
              "  para el prototipo: ninguna va en --confirmadas")
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


def nombre_df(m, vs):
    """El nombre del Word que escribe df_docx.js por defecto: DF-<título sin tildes ni signos>-v<versión>.docx."""
    tit = re.search(r"^# (.+)$", "\n".join(m.docs["F"].lineas), re.M) if "F" in m.docs else None
    tit = re.sub(r"\s+—\s+Diseño funcional\s*$", "", tit.group(1)) if tit else "Diseño funcional"
    slug = re.sub(r"[^A-Za-z0-9_]+", "-", re.sub(r"[\u0300-\u036f]", "", unicodedata.normalize("NFD", tit))).strip("-")
    return f"DF-{slug}-v{vs}.docx"


def entregar(a):
    """El Word sale hacia el cliente: «DF entregado: <versión> · <fecha>» en proyecto.md y el fichero en «Entregados:»,
    que df_docx.js no vuelve a escribir."""
    if a.cambio:
        sys.exit("proyecto.py entregar --cambio todavía no está disponible: se marca el DF completo (sin --cambio)")
    raiz = pathlib.Path(a.carpeta)
    pm = raiz / "proyecto.md"
    if not pm.exists():
        sys.exit(f"No existe {pm}")
    m = mo.Proyecto(raiz)
    v = m.version("F")
    if not v:
        sys.exit("funcional.md no tiene «Versión: x.y»")
    vs, fecha = f"{v[0]}.{v[1]}", datetime.date.today().isoformat()
    texto = pm.read_text(encoding="utf-8")
    valor = f"DF entregado: {vs} · {fecha}"
    if re.search(r"DF entregado:", texto):
        texto = re.sub(r"DF entregado:[^\n]*?(?=\s+·\s+Estado:|$)", valor, texto, count=1, flags=re.M)
    else:   # tras la línea del cliente o, si no está, tras el título
        lineas = texto.split("\n")
        k = next((i for i, l in enumerate(lineas) if l.startswith("Cliente:")), 0)
        lineas.insert(k + 1, valor)
        texto = "\n".join(lineas)
    word = nombre_df(m, vs)
    if not (raiz / "entregables" / word).is_file():
        print(f"· No encuentro entregables/{word}: genéralo con df_docx.js antes de enviarlo")
    else:   # «Entregados: a.docx, b.docx», tras la línea de «DF entregado»
        lineas = texto.split("\n")
        k = next((i for i, l in enumerate(lineas) if l.startswith("Entregados:")), None)
        if k is None:
            k = next(i for i, l in enumerate(lineas) if "DF entregado:" in l) + 1
            lineas.insert(k, "Entregados:")
        ya = [x.strip() for x in lineas[k].split(":", 1)[1].split(",") if x.strip()]
        lineas[k] = "Entregados: " + ", ".join(ya + ([word] if word not in ya else []))
        texto = "\n".join(lineas)
    pm.write_text(texto, encoding="utf-8")
    print(f"{valor} en {pm}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("iniciar"); s.add_argument("carpeta"); s.add_argument("--nombre", required=True)
    s.add_argument("--cliente"); s.add_argument("--direccion"); s.add_argument("--tipo")
    s.set_defaults(f=iniciar)
    s = sub.add_parser("estado"); s.add_argument("carpeta"); s.set_defaults(f=estado)
    s = sub.add_parser("copia"); s.add_argument("carpeta"); s.set_defaults(f=copia)
    s = sub.add_parser("entregar"); s.add_argument("carpeta"); s.set_defaults(f=entregar)
    s.add_argument("--cambio", help="el DF de un cambio (todavía no disponible)")
    a = ap.parse_args()
    for st in (sys.stdout, sys.stderr):
        st.reconfigure(encoding="utf-8", errors="replace")
    a.f(a)


if __name__ == "__main__":
    main()
