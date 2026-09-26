#!/usr/bin/env python3
"""Valida y renderiza diagramas Mermaid sin internet.

Usa el mermaid.min.js incluido en la skill (assets/) y un navegador headless:
el Chromium de Playwright si está instalado, o Chrome / Edge del sistema.
El contenido del diagrama no sale del equipo.

Uso:
  python3 render_mermaid.py diagrama.mmd [otro.mmd ...] [-o carpeta] [--check] [--svg] [--width 1600]

  --check   solo valida la sintaxis (no genera ficheros)
  --svg     además del PNG guarda el SVG
Salida: <nombre>.png (y .svg) junto a cada .mmd o en -o.
Código de salida: 0 todo OK, 1 algún diagrama con error de sintaxis, 2 falta un requisito.
"""
import argparse, glob, json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
MERMAID_JS = HERE.parent / "assets" / "mermaid.min.js"

PAGE = """<!doctype html><html><head><meta charset="utf-8">
<style>body{margin:0;background:#fff}#out{display:inline-block;padding:16px}</style></head>
<body><div id="out"></div></body></html>"""

JS_RENDER = """async ([code, width]) => {
  mermaid.initialize({startOnLoad: false, theme: 'default', securityLevel: 'strict',
                      flowchart: {useMaxWidth: false}, er: {useMaxWidth: false},
                      state: {useMaxWidth: false}});
  try { await mermaid.parse(code); }
  catch (e) { return {ok: false, error: String(e && e.message || e)}; }
  const {svg} = await mermaid.render('d' + Date.now(), code);
  const out = document.getElementById('out');
  out.innerHTML = svg;
  const el = out.querySelector('svg');
  const w = el.getBoundingClientRect().width;
  if (w > width) { el.style.width = width + 'px'; el.style.height = 'auto'; }
  return {ok: true, svg: out.innerHTML};
}"""


def launch(p):
    """Chromium de Playwright; si no está descargado, Chrome o Edge del sistema."""
    errors = []
    for opts in ({}, {"channel": "chrome"}, {"channel": "msedge"}):
        try:
            return p.chromium.launch(**opts)
        except Exception as e:  # noqa: BLE001 - probamos el siguiente navegador
            errors.append(f"{opts.get('channel', 'chromium de Playwright')}: {str(e).splitlines()[0]}")
    print("No hay navegador disponible. Instala uno de estos:\n  - playwright install chromium\n"
          "  - o Google Chrome / Microsoft Edge (se usan sin descargar nada más)\nDetalle:\n  " + "\n  ".join(errors),
          file=sys.stderr)
    sys.exit(2)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+")
    ap.add_argument("-o", "--out")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--svg", action="store_true")
    ap.add_argument("--width", type=int, default=1600)
    a = ap.parse_args()
    for stream in (sys.stdout, sys.stderr):  # consolas Windows sin UTF-8
        stream.reconfigure(encoding="utf-8", errors="replace")

    if not MERMAID_JS.exists():
        print(f"Falta {MERMAID_JS} (viene con la skill).", file=sys.stderr)
        sys.exit(2)
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Falta Playwright para Python: pip install playwright\n"
              "(con Chrome o Edge instalados no hace falta 'playwright install').", file=sys.stderr)
        sys.exit(2)

    files = [x for f in a.files for x in (sorted(glob.glob(f)) if glob.has_magic(f) and not pathlib.Path(f).exists() else [f])]  # PowerShell / cmd no expanden *
    missing = [f for f in files if not pathlib.Path(f).is_file()]
    if not files or missing:
        print("No encuentro los diagramas: " + (", ".join(missing) or " ".join(a.files)), file=sys.stderr)
        sys.exit(1)  # 2 queda para «falta un requisito» (Playwright o navegador)
    failed = 0
    with sync_playwright() as p:
        browser = launch(p)
        page = browser.new_page(device_scale_factor=2, viewport={"width": a.width + 64, "height": 800})
        page.route("**/*", lambda r: r.abort() if not r.request.url.startswith(("about:", "data:")) else r.continue_())
        page.set_content(PAGE)
        page.add_script_tag(content=MERMAID_JS.read_text(encoding="utf-8"))
        for f in files:
            src = pathlib.Path(f)
            res = page.evaluate(JS_RENDER, [src.read_text(encoding="utf-8"), a.width])
            if not res["ok"]:
                failed += 1
                print(f"ERROR {src.name}:\n{res['error']}\n", file=sys.stderr)
                continue
            if a.check:
                print(f"OK {src.name}")
                continue
            dest = pathlib.Path(a.out) if a.out else src.parent
            dest.mkdir(parents=True, exist_ok=True)
            png = dest / (src.stem + ".png")
            page.locator("#out").screenshot(path=str(png))
            if a.svg:
                (dest / (src.stem + ".svg")).write_text(res["svg"], encoding="utf-8")
            print(f"OK {src.name} -> {png}")
        browser.close()
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
