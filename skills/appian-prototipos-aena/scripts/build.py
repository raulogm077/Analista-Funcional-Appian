#!/usr/bin/env python3
"""
Construye un prototipo navegable (un único HTML autocontenido) a partir de un app spec.

Uso:
  python3 build.py app.json -o prototipo.html [--brand aena] [--no-validate]

Genera además <salida>-trazabilidad.md (requisitos ↔ pantallas, preguntas abiertas, supuestos).
El HTML empieza por <title> (sin <html>/<body>) para poder publicarse como Artifact en Claude.ai
y también abrirse directamente en un navegador.
"""
import json, re, sys, argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate import validate, trace_markdown, find_brand, ux_summary  # noqa: E402
from entorno import utf8_stdio  # noqa: E402

FONT = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Open+Sans:ital,wght@0,300;0,400;0,600;0,700;1,400&display=swap">'


def mix_white(hex_color, pct):
    h = hex_color.lstrip("#")[:6]
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    f = lambda c: round(c * pct + 255 * (1 - pct))
    return "#%02x%02x%02x" % (f(r), f(g), f(b))


def used_icons(spec, js):
    # cualquier literal del runtime que sea un nombre de icono (icon("x"), mapas de iconos por estado...)
    names = set(re.findall(r'"([a-z0-9]+(?:-[a-z0-9]+)*)"', js))

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k in ("icon", "stampIcon", "labelIcon", "$icon") and isinstance(v, str):
                    names.add(v)
                    names.update(re.findall(r'"([a-z0-9-]+)"', v))
                elif k == "$template" and isinstance(v, dict) and v.get("icon"):
                    names.add(v["icon"])
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(spec)
    for m in (spec.get("maps") or {}).values():
        for v in m.values():
            if isinstance(v, str):
                names.add(v)
    for p in (spec.get("site") or {}).get("pages", []):
        if p.get("icon"):
            names.add(p["icon"])
    return names


def _strings(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for v in o.values():
            yield from _strings(v)
    elif isinstance(o, list):
        for v in o:
            yield from _strings(v)


def build(spec_path, out_path, brand_id="aena", do_validate=True):
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    spec_dir = Path(spec_path).resolve().parent
    brand, brand_dir = find_brand(brand_id, spec_dir)
    if do_validate:
        rep = validate(spec, brand, spec_dir)
        for line in rep.errors + rep.warnings:
            print(line)
        print(f"Validación: {len(rep.errors)} error(es), {len(rep.warnings)} aviso(s)")
        print(ux_summary(rep))
        if rep.errors:
            print("Build detenido: corrige los errores (o usa --no-validate para depurar).")
            sys.exit(1)
    css = (ROOT / "runtime" / "appian-kit.css").read_text(encoding="utf-8")
    js = (ROOT / "runtime" / "appian-kit.js").read_text(encoding="utf-8")
    all_icons = json.loads((ROOT / "assets" / "icons.json").read_text(encoding="utf-8"))
    # iconos citados por nombre en cualquier parte del spec (p. ej. el icono de cada opción en los datos de un a!cardChoiceField)
    names = used_icons(spec, js) | {v for v in _strings(spec) if v in all_icons}
    icons = {k: all_icons[k] for k in sorted(names) if k in all_icons}
    site = brand["site"]
    logo = (brand_dir / site["logo"]).read_text(encoding="utf-8")
    shape = {"SQUARED": "0px", "SEMI_ROUNDED": "4px", "ROUNDED": "999px"}
    dshape = {"SQUARED": "0px", "SEMI_ROUNDED": "8px", "ROUNDED": "16px"}
    tokens = f""":root {{
  --accent: {site['accentColor']};
  --accent-tint: {mix_white(site['accentColor'], 0.10)};
  --hdr-bg: {site['backgroundColor']};
  --hdr-hl: {site['selectedPageHighlightColor']};
  --loading: {site.get('loadingBarColor', site['accentColor'])};
  --btn-radius: {shape[site.get('buttonShape', 'SEMI_ROUNDED')]};
  --input-radius: {shape[site.get('inputShape', 'SEMI_ROUNDED')].replace('999px', '4px')};
  --dialog-radius: {dshape[site.get('dialogShape', 'SEMI_ROUNDED')]};
}}"""
    safe = lambda o: json.dumps(o, ensure_ascii=False).replace("</", "<\\/")
    title = spec.get("app", {}).get("name", "Prototipo Appian")
    html = f"""<title>{title}</title>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="generator" content="appian-prototipos-aena">
{FONT}
<style>
{css}
{tokens}
</style>
<script type="application/json" id="px-spec">{safe(spec)}</script>
<script type="application/json" id="px-brand">{safe(brand)}</script>
<script type="application/json" id="px-icons">{safe(icons)}</script>
<template id="px-logo">{logo}</template>
<script>
{js}
</script>
"""
    Path(out_path).write_text(html, encoding="utf-8")
    trace = Path(out_path).with_name(Path(out_path).stem + "-trazabilidad.md")
    trace.write_text(trace_markdown(spec), encoding="utf-8")
    kb = len(html.encode()) / 1024
    print(f"OK → {out_path} ({kb:.0f} KB, {len(spec.get('screens', []))} pantallas, {len(icons)} iconos)")
    print(f"OK → {trace}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("-o", "--out", default=None)
    ap.add_argument("--brand", default="aena")
    ap.add_argument("--no-validate", action="store_true")
    a = ap.parse_args()
    utf8_stdio()
    out = a.out or str(Path(a.spec).with_suffix(".html"))
    build(a.spec, out, a.brand, not a.no_validate)
