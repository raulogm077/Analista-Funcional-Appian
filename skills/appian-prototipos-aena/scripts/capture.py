#!/usr/bin/env python3
"""
Genera capturas PNG de cada pantalla/estado del prototipo para el documento funcional.

Uso:
  python3 capture.py prototipo.html app.json -o capturas/ [--width 1440] [--height 900] [--viewport]

- Usa spec.captures si existe; si no, una captura por pantalla en su estado inicial.
- Oculta la barra del prototipo (modo captura).
- Por defecto captura la página completa (formularios largos incluidos). --viewport limita a 1440x900;
  en una captura concreta, "full": false hace lo mismo.
- Escribe capturas/indice.md con la lista de figuras, pantalla, patrón y requisitos, listo para pegar.
- Informa de errores de JavaScript de la página (si hay alguno, sale con código 1).
Requiere Playwright para Python (pip install playwright) y un navegador: el Chromium de Playwright
(playwright install chromium) o Chrome / Edge ya instalados.
"""
import json, sys, argparse
from pathlib import Path
from entorno import utf8_stdio, sync_playwright, launch_browser


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("html")
    ap.add_argument("spec")
    ap.add_argument("-o", "--out", default="capturas")
    ap.add_argument("--width", type=int, default=1440)
    ap.add_argument("--height", type=int, default=900)
    ap.add_argument("--viewport", action="store_true", help="capturar solo el área visible (por defecto: página completa)")
    a = ap.parse_args()
    utf8_stdio()

    spec = json.loads(Path(a.spec).read_text(encoding="utf-8"))
    byid = {s["id"]: s for s in spec["screens"]}
    caps = spec.get("captures") or [{"name": f"{i + 1:02d}-{s['id']}", "screen": s["id"]} for i, s in enumerate(spec["screens"])]
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    errors = []
    index = [f"# Capturas · {spec.get('app', {}).get('name', '')}", "",
             "Pie de figura listo para pegar en el documento funcional; «Referencia» indica bajo qué ficha va cada imagen.", "",
             "| Fichero | Pie de figura | Referencia | Patrón | Requisitos |", "|---|---|---|---|---|"]
    with sync_playwright() as p:
        b = launch_browser(p)
        pg = b.new_page(viewport={"width": a.width, "height": a.height}, device_scale_factor=1)
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.on("console", lambda m: errors.append(m.text) if (m.type == "error" and "fonts.g" not in m.text + str((m.location or {}).get("url", ""))) or (m.type == "warning" and ("no válida" in m.text or "no encontrad" in m.text)) else None)
        pg.goto(Path(a.html).resolve().as_uri())
        pg.wait_for_function("window.PROTO && window.PROTO.ready")
        try:
            pg.wait_for_load_state("networkidle", timeout=5000)
        except Exception:
            pass
        pg.evaluate("PROTO.setCapture(true)")
        for i, c in enumerate(caps, start=1):
            opts = {k: v for k, v in c.items() if k not in ("name", "screen", "caption")}
            ok = pg.evaluate("([id, o]) => PROTO.show(id, o)", [c["screen"], opts])
            if not ok:
                errors.append(f"captura {c['name']}: pantalla '{c['screen']}' no encontrada")
                continue
            pg.wait_for_timeout(200)
            f = out / f"{c['name']}.png"
            full = c.get("full", not a.viewport)
            if full and pg.locator(".dlg-bg").count():
                # diálogo: la capa es fija al viewport, así que se agranda la ventana hasta que el diálogo quepa entero
                extra = pg.evaluate("() => { const c = [...document.querySelectorAll('.dlg-c')].pop(); return c ? c.scrollHeight - c.clientHeight : 0; }")
                if extra > 0:
                    pg.set_viewport_size({"width": a.width, "height": a.height + extra + 8})
                    pg.wait_for_timeout(150)
                pg.screenshot(path=str(f), full_page=False)
                pg.set_viewport_size({"width": a.width, "height": a.height})
            else:
                pg.screenshot(path=str(f), full_page=full)
            s = byid[c["screen"]]
            v = next((x for x in s.get("views") or [] if x.get("id") == c.get("view")), None)
            bits = []
            if "step" in c:
                bits.append(f"paso {c['step'] + 1}")
            if c.get("view"):
                bits.append(f"vista «{v.get('label', c['view']) if v else c['view']}»")
            if c.get("showValidation"):
                bits.append("validación mostrada")
            if c.get("state"):
                bits.append("datos de ejemplo cargados")
            estado = c.get("caption") or (", ".join(bits) if bits else "inicial")
            titulo = pg.title().rsplit(" · ", 1)[0] or s.get("title", s["id"])
            pie = titulo + ("" if estado == "inicial" else f" ({estado})")  # el número de figura lo pone el documento
            ref = (v or {}).get("ref") or s.get("ref", "—")  # una vista puede ser otra ficha del análisis
            index.append(f"| {f.name} | {pie} | {ref} | {s.get('pattern', '')} | {', '.join((v or {}).get('req') or s.get('req', []))} |")
            print(f"  ✓ {f}")
        b.close()
    (out / "indice.md").write_text("\n".join(index) + "\n", encoding="utf-8")
    print(f"OK → {out / 'indice.md'}")
    if errors:
        print("\nErrores en la página:")
        for e in errors:
            print("  ✗", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
