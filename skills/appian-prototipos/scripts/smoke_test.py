#!/usr/bin/env python3
"""
Prueba de humo del prototipo: abre cada pantalla, pulsa cada botón, enlace, pestaña y acción
(restaurando la pantalla tras cada clic) y falla si aparece algún error de JavaScript o si una
navegación deja la página en blanco.

Uso:  python3 smoke_test.py prototipo.html app.json [--width 1440]
Requiere Playwright para Python y un navegador (Chromium de Playwright, Chrome o Edge).
"""
import json, sys, argparse
sys.dont_write_bytecode = True  # sin __pycache__ en el plugin: no se escribe fuera del proyecto
from pathlib import Path
from entorno import utf8_stdio, sync_playwright, launch_browser

PAGE = "#px-root .site-body button:not([disabled]):visible, #px-root .site-body a[href]:visible, .site-nav button:visible"


def clickables(pg):
    """Elementos pulsables visibles; con un diálogo abierto, solo los del diálogo superior (lo de detrás no se puede pulsar)."""
    dlg = pg.locator(".dlg-bg")
    # :visible en el selector (y no Locator.filter(visible=...)) para funcionar con cualquier versión de Playwright
    return dlg.last.locator("button:not([disabled]):visible, a[href]:visible") if dlg.count() else pg.locator(PAGE)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("html")
    ap.add_argument("spec")
    ap.add_argument("--width", type=int, default=1440)
    a = ap.parse_args()
    utf8_stdio()

    spec = json.loads(Path(a.spec).read_text(encoding="utf-8"))
    errors, clicks, blank = [], 0, []
    with sync_playwright() as p:
        b = launch_browser(p)
        pg = b.new_page(viewport={"width": a.width, "height": 900})
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.on("dialog", lambda d: d.dismiss())
        # enlaces externos (a!safeLink) y window.open: no salir del prototipo durante la prueba
        pg.add_init_script("window.open = () => null;")
        pg.route("**/*", lambda r: r.continue_() if r.request.url.startswith(("file:", "data:", "blob:")) else r.abort())
        pg.on("console", lambda m: errors.append(m.text) if m.type == "warning" and ("no válida" in m.text or "no encontrad" in m.text) else None)
        pg.goto(Path(a.html).resolve().as_uri())
        pg.wait_for_function("window.PROTO && window.PROTO.ready")
        for s in spec["screens"]:
            pg.evaluate("([id]) => PROTO.show(id, {})", [s["id"]])
            # componentes que el runtime no sabe pintar
            for t in pg.evaluate("[...document.querySelectorAll('.banner .pt')].map((e) => e.textContent).filter((x) => /no soportado/.test(x))"):
                errors.append(f"{s['id']}: {t}")
            n = clickables(pg).count()
            for i in range(n):
                pg.evaluate("([id]) => PROTO.show(id, {})", [s["id"]])
                loc = clickables(pg)
                if i >= loc.count():
                    break
                el = loc.nth(i)
                try:
                    label = (el.inner_text(timeout=500) or el.get_attribute("aria-label") or "").strip()[:40]
                    if el.get_attribute("type") == "file":
                        continue
                    el.click(timeout=1500)
                    clicks += 1
                    pg.wait_for_timeout(40)
                    if pg.evaluate("document.querySelector('#px-root .site-body')?.innerText.trim().length || 0") == 0:
                        blank.append(f"{s['id']} → «{label}»")
                except Exception as e:  # elemento oculto o fuera de vista: no es un fallo del prototipo
                    if "Timeout" not in str(e) and "not visible" not in str(e):
                        errors.append(f"{s['id']} «{label}»: {e}")
        b.close()
    print(f"{len(spec['screens'])} pantallas, {clicks} clics")
    for e in errors:
        print("  ✗ JS:", e)
    for x in blank:
        print("  ✗ Página en blanco tras:", x)
    if errors or blank:
        sys.exit(1)
    print("OK: sin errores")


if __name__ == "__main__":
    main()
