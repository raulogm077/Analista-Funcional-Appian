#!/usr/bin/env python3
"""
Auditoría de contraste (WCAG 2.2 AA) del prototipo: abre cada pantalla y mide el contraste real de lo que se ve.

- Texto: 4,5:1; texto grande (24 px, o 18,66 px en negrita): 3:1. Incluye el marcador de posición de los campos.
- Componentes de interfaz (WCAG 1.4.11): borde de los campos 3:1 frente a su fondo.
- Colores tal y como los pinta el navegador (perfil CSS de la marca incluido), con transparencias y opacidad compuestas
  sobre el fondo real. No mide texto sobre imágenes (billboards con foto): lo cuenta aparte.
- No cuenta lo inactivo (botones deshabilitados, campos disabled): WCAG lo exime.

Uso:  python3 contrast_audit.py prototipo.html app.json [--screens id1,id2] [--json informe.json]
Sale con 1 si hay fallos. Requiere Playwright y un navegador, como smoke_test.py.
"""
import json, sys, argparse
sys.dont_write_bytecode = True  # sin __pycache__ en el plugin: no se escribe fuera del proyecto
from pathlib import Path
from entorno import utf8_stdio, sync_playwright, launch_browser

JS = r"""
() => {
  const parse = (c) => { const m = String(c || "").match(/rgba?\(([^)]+)\)/); if (!m) return null; const p = m[1].split(/[ ,\/]+/).filter(Boolean).map(parseFloat); return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 }; };
  const over = (fg, bg) => ({ r: fg.r * fg.a + bg.r * (1 - fg.a), g: fg.g * fg.a + bg.g * (1 - fg.a), b: fg.b * fg.a + bg.b * (1 - fg.a), a: 1 });
  const lum = (c) => { const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }; return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b); };
  const ratio = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); };
  const hex = (c) => "#" + [c.r, c.g, c.b].map((v) => Math.round(v).toString(16).padStart(2, "0")).join("");
  const visible = (el) => { const r = el.getBoundingClientRect(); if (!r.width || !r.height) return false; const cs = getComputedStyle(el); return cs.visibility !== "hidden" && cs.display !== "none"; };
  // fondo efectivo: capas de color de los antepasados compuestas de abajo arriba (blanco al fondo); imagen → no medible
  function background(el) {
    const layers = [];
    for (let e = el; e; e = e.parentElement) {
      const cs = getComputedStyle(e);
      if (cs.backgroundImage && cs.backgroundImage !== "none" && !/gradient/.test(cs.backgroundImage)) return { image: true };
      if (/gradient/.test(cs.backgroundImage)) { const g = parse((cs.backgroundImage.match(/rgba?\([^)]+\)/) || [])[0]); if (g) { layers.push(g); if (g.a >= 1) break; } }
      const c = parse(cs.backgroundColor);
      if (c && c.a > 0) { layers.push(c); if (c.a >= 1) break; }
    }
    let bg = { r: 255, g: 255, b: 255, a: 1 };
    for (const c of layers.reverse()) bg = over(c, bg);
    return bg;
  }
  const opacityOf = (el) => { let o = 1; for (let e = el; e; e = e.parentElement) o *= parseFloat(getComputedStyle(e).opacity || "1"); return o; };
  const inactive = (el) => !!el.closest("button:disabled, input:disabled, textarea:disabled, select:disabled, [aria-disabled='true'], .dis, .inert-ok");
  const where = (el) => { const s = el.closest("[data-sail]"); return s ? s.getAttribute("data-sail") : el.tagName.toLowerCase(); };
  const root = document.querySelector("#px-root") || document.body;
  const out = [], seen = new Set();
  let images = 0;
  function check(el, text, fgRaw, kind) {
    if (!visible(el) || inactive(el)) return;
    const bg = background(el);
    if (bg.image) { images++; return; }
    const fg0 = parse(fgRaw); if (!fg0) return;
    const fg = over(Object.assign({}, fg0, { a: fg0.a * opacityOf(el) }), bg);
    const cs = getComputedStyle(el);
    const size = parseFloat(cs.fontSize), weight = parseInt(cs.fontWeight, 10) || 400;
    const large = size >= 24 || (size >= 18.66 && weight >= 700);
    const need = kind === "ui" ? 3 : large ? 3 : 4.5;
    const r = ratio(fg, bg);
    const key = [kind, where(el), hex(fg), hex(bg)].join("|");
    if (r + 0.005 < need && !seen.has(key)) { seen.add(key); out.push({ kind, comp: where(el), text: String(text).trim().slice(0, 60), fg: hex(fg), bg: hex(bg), ratio: Math.round(r * 100) / 100, need, size: Math.round(size) }); }
  }
  const tw = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, { acceptNode: (n) => (n.nodeValue.trim() ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT) });
  for (let n = tw.nextNode(); n; n = tw.nextNode()) {
    const el = n.parentElement;
    if (!el || el.closest(".px-bar, .px-panel, .px-tip, [aria-hidden='true'], svg, script, style, template, title")) continue;
    check(el, n.nodeValue, getComputedStyle(el).color, "texto");
  }
  // marcador de posición y borde de los campos
  root.querySelectorAll("input.inp, textarea.inp, select.inp").forEach((el) => {
    if (el.placeholder && !el.value) check(el, "placeholder: " + el.placeholder, getComputedStyle(el, "::placeholder").color, "texto");
    const cs = getComputedStyle(el);
    if (!visible(el) || inactive(el)) return;
    const bc = parse(cs.borderTopColor), bw = parseFloat(cs.borderTopWidth);
    if (bc && bw > 0) { const bg = background(el.parentElement); if (!bg.image) { const r = ratio(over(bc, bg), bg); const key = "ui|" + where(el) + "|" + hex(bc); if (r + 0.005 < 3 && !seen.has(key)) { seen.add(key); out.push({ kind: "borde de campo", comp: where(el), text: el.getAttribute("aria-label") || el.placeholder || "", fg: hex(over(bc, bg)), bg: hex(bg), ratio: Math.round(r * 100) / 100, need: 3, size: 0 }); } } }
  });
  // texto de los gráficos (ejes, etiquetas de datos fuera de las barras)
  root.querySelectorAll(".chart svg text").forEach((t) => {
    if (t.classList.contains("in") || t.classList.contains("pl")) return; // dentro de la barra o del sector: color calculado por contraste
    const fill = getComputedStyle(t).fill;
    check(t, t.textContent, fill, "texto");
  });
  return { fails: out, images };
}
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("html")
    ap.add_argument("spec")
    ap.add_argument("--screens", default=None)
    ap.add_argument("--json", default=None)
    ap.add_argument("--strict", action="store_true", help=argparse.SUPPRESS)  # compatibilidad: ya es el comportamiento por defecto
    a = ap.parse_args()
    utf8_stdio()
    spec = json.loads(Path(a.spec).read_text(encoding="utf-8"))
    only = set(a.screens.split(",")) if a.screens else None
    # cada pantalla; las de registro, vista a vista; los asistentes, paso a paso
    targets = []
    for s in spec["screens"]:
        if only and s["id"] not in only:
            continue
        if s.get("type") == "record" and s.get("views"):
            targets += [(f"{s['id']} · {v.get('label', v.get('id'))}", s["id"], {"view": v["id"]}) for v in s["views"]]
        elif (s.get("interface") or {}).get("type") == "a!wizardLayout":
            targets += [(f"{s['id']} · paso {k + 1}", s["id"], {"step": k}) for k in range(len((s["interface"].get("steps") or [])))]
        else:
            targets.append((s["id"], s["id"], {}))
    ids = [t[0] for t in targets]
    report, total, imgs = {}, 0, 0
    with sync_playwright() as p:
        b = launch_browser(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        pg.route("**/*", lambda r: r.continue_() if r.request.url.startswith(("file:", "data:", "blob:")) else r.abort())
        pg.goto(Path(a.html).resolve().as_uri())
        pg.wait_for_function("window.PROTO && window.PROTO.ready")
        pg.evaluate("PROTO.setCapture(true)")
        for sid, scr, opts in targets:
            pg.evaluate("([id, o]) => PROTO.show(id, o)", [scr, opts])
            pg.wait_for_timeout(120)
            r = pg.evaluate(JS)
            report[sid] = r["fails"]
            total += len(r["fails"])
            imgs += r["images"]
        b.close()
    for sid, fails in report.items():
        if not fails:
            continue
        print(f"\n{sid}: {len(fails)} combinación(es) por debajo del mínimo")
        for f in sorted(fails, key=lambda x: x["ratio"]):
            print(f"  ✗ {f['ratio']:>5}:1 (mín. {f['need']}) {f['kind']:<14} {f['comp']:<28} {f['fg']} sobre {f['bg']}  «{f['text']}»")
    print(f"\nContraste: {len(ids)} pantallas, {total} combinación(es) de color por debajo de WCAG 2.2 AA" + (f"; {imgs} texto(s) sobre imagen no medidos" if imgs else ""))
    if a.json:
        Path(a.json).write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()
