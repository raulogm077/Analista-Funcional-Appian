#!/usr/bin/env python3
"""Valida y pinta diagramas Mermaid sin conexión: el diagrama no sale del equipo.

Usa el mermaid.min.js de esta skill (assets/) y un navegador sin ventana: el Chromium de Playwright o, si no
está, Chrome o Edge del sistema.

  python3 mermaid.py diagrama.mmd [otro.mmd ...] [-o carpeta] [--check] [--svg] [--width 1600] [--md documento.md ...]

  -o        carpeta de las imágenes (por defecto, la de cada .mmd). No se escribe nada fuera de ella
  --check   solo valida (no escribe nada)
  --svg     además del PNG, el SVG
  --width   ancho máximo de la imagen en px; un diagrama más ancho se reduce
  --md      valida cada bloque ```mermaid de esos Markdown, sin pintarlo; si uno falla, dice en qué línea
            empieza (la del ```mermaid; las líneas del mensaje de Mermaid cuentan desde ahí). Con --md, los .mmd
            son opcionales

Avisa de los diagramas de más de 1.600 px de ancho: en una página vertical, el texto queda pequeño.
Salida: <nombre>.png (y .svg) por cada .mmd.
Código de salida: 0 todo bien, 1 algún diagrama con error de sintaxis o un fichero que no está, 2 falta un
requisito (Playwright, un navegador o assets/mermaid.min.js).
"""
import argparse, glob, pathlib, re, sys, textwrap
sys.dont_write_bytecode = True  # sin __pycache__ en el plugin: no se escribe fuera de la carpeta de salida

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import colocacion  # noqa: E402
import navegador  # noqa: E402

MERMAID_JS = navegador.MERMAID_JS  # assets/mermaid.min.js de esta skill

JS_INICIO = """() => mermaid.initialize({startOnLoad: false, theme: 'default', securityLevel: 'strict',
    flowchart: {useMaxWidth: false}, er: {useMaxWidth: false}, state: {useMaxWidth: false}})"""

JS_PINTAR = """async ([code, width]) => {
  const out = document.getElementById('out');
  out.innerHTML = '';
  try {
    await mermaid.parse(code);
    window.n = (window.n || 0) + 1;
    out.innerHTML = (await mermaid.render('d' + window.n, code)).svg;
  } catch (e) { return {ok: false, error: String(e && e.message || e)}; }
  const el = out.querySelector('svg');
  const ancho = el.getBoundingClientRect().width;
  if (ancho > width) { el.style.width = width + 'px'; el.style.height = 'auto'; }
  return {ok: true, ancho: ancho, svg: out.innerHTML};
}"""


def bloques(texto):
    """(línea del ```mermaid, código) de cada bloque mermaid de un Markdown. Las demás vallas se saltan enteras."""
    out, valla = [], None
    for n, linea in enumerate(texto.splitlines(), 1):
        s = linea.strip()
        if valla is None:
            m = re.match(r"(`{3,}|~{3,})\s*([\w-]*)", s)
            if m:
                valla, inicio = m.group(1), n
                cuerpo = [] if m.group(2).lower() == "mermaid" else None
        elif re.fullmatch(re.escape(valla[0]) + "{%d,}" % len(valla), s):
            if cuerpo is not None:
                out.append((inicio, textwrap.dedent("\n".join(cuerpo))))
            valla = None
        elif cuerpo is not None:
            cuerpo.append(linea)
    if valla is not None and cuerpo is not None:  # sin cerrar: llega hasta el final, como en Markdown
        out.append((inicio, textwrap.dedent("\n".join(cuerpo))))
    return out


def ficheros(rutas):
    """Las rutas, con los comodines expandidos (PowerShell y cmd no los expanden)."""
    return [x for f in rutas
            for x in (sorted(glob.glob(f, recursive=True)) if glob.has_magic(f) and not pathlib.Path(f).exists() else [f])]


def aviso_ancho(que, ancho):
    if ancho > colocacion.ANCHO_LEGIBLE:
        print(f"aviso: {que} mide {ancho:.0f} px de ancho: en una página vertical el texto quedará pequeño. "
              "Ponlo de arriba abajo (TD), quita detalle o pártelo en dos")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*", metavar="diagrama.mmd")
    ap.add_argument("-o", "--out")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--svg", action="store_true")
    ap.add_argument("--width", type=int, default=1600)
    ap.add_argument("--md", nargs="+", action="extend", default=[], metavar="documento.md")
    a = ap.parse_intermixed_args()
    for stream in (sys.stdout, sys.stderr):  # consolas Windows sin UTF-8
        stream.reconfigure(encoding="utf-8", errors="replace")

    # un .mmd que va detrás de --md es un diagrama, no un Markdown
    mmd = ficheros(a.files + [f for f in a.md if f.lower().endswith(".mmd")])
    mds = ficheros([f for f in a.md if not f.lower().endswith(".mmd")])
    if not mmd and not mds:
        ap.error("indica algún .mmd o --md con un Markdown")
    faltan = [f for f in mmd + mds if not pathlib.Path(f).is_file()]
    if faltan:
        print("No encuentro: " + ", ".join(faltan), file=sys.stderr)
        sys.exit(1)  # 2 queda para «falta un requisito»
    if not MERMAID_JS.exists():
        print(f"Falta {MERMAID_JS} (viene con la skill appian-diagramas-bpmn del plugin).", file=sys.stderr)
        sys.exit(2)

    fallos = 0
    try:
        sync_playwright = navegador._playwright()
        with sync_playwright() as p:
            b, pg = navegador._pagina(p, ancho=a.width + 64, alto=800, escala=2)
            try:
                pg.add_style_tag(content="#out{display:inline-block;padding:16px}")
                pg.add_script_tag(content=MERMAID_JS.read_text(encoding="utf-8"))
                pg.evaluate(JS_INICIO)
                for f in mmd:
                    src = pathlib.Path(f)
                    res = pg.evaluate(JS_PINTAR, [src.read_text(encoding="utf-8-sig"), a.width])
                    if not res["ok"]:
                        fallos += 1
                        print(f"ERROR {f}:\n{res['error']}\n", file=sys.stderr)
                        continue
                    if a.check:
                        print(f"OK {f}")
                    else:
                        dest = pathlib.Path(a.out) if a.out else src.parent
                        dest.mkdir(parents=True, exist_ok=True)
                        png = dest / (src.stem + ".png")
                        pg.locator("#out").screenshot(path=str(png))
                        if a.svg:
                            (dest / (src.stem + ".svg")).write_text(res["svg"], encoding="utf-8")
                        print(f"OK {f} -> {png}")
                    aviso_ancho(f, res["ancho"])
                for f in mds:
                    encontrados, malos = bloques(pathlib.Path(f).read_text(encoding="utf-8-sig")), 0
                    for linea, codigo in encontrados:
                        res = pg.evaluate(JS_PINTAR, [codigo, a.width])
                        if res["ok"]:
                            aviso_ancho(f"{f}, línea {linea},", res["ancho"])
                        else:
                            malos += 1
                            print(f"ERROR {f}, línea {linea}: el bloque mermaid no es válido\n{res['error']}\n",
                                  file=sys.stderr)
                    fallos += malos
                    if not malos:
                        n = len(encontrados)
                        print(f"OK {f}: " + (f"{n} bloque{'s' * (n > 1)} mermaid" if n else "sin bloques mermaid"))
            finally:
                navegador.cerrar(b)  # y sus temporales: no queda nada fuera de la carpeta de salida
    except navegador.SinNavegador as e:
        print(e, file=sys.stderr)
        sys.exit(2)
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
