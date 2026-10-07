#!/usr/bin/env python3
"""
Construye un prototipo navegable (un único HTML autocontenido) a partir de un app spec.

Uso:
  python3 build.py app.json -o prototipo.html [--brand <id>] [--no-validate]

Sin --brand, la marca estándar de Appian (assets/brand-appian.json, sin logo); con --brand <id>, la del proyecto:
brand-<id>.json junto al app.json, con su logo si lo tiene (references/marca.md).
Genera además <salida>-trazabilidad.md (requisitos ↔ pantallas, preguntas abiertas, supuestos) y, si la marca lleva
perfil CSS, <salida>-perfil-css.txt.
El HTML empieza por <title> (sin <html>/<body>) para poder publicarse como Artifact en Claude.ai
y también abrirse directamente en un navegador.
"""
import base64, json, re, sys, argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate import validate, trace_markdown, find_brand, ux_summary  # noqa: E402
from entorno import utf8_stdio  # noqa: E402

# Open Sans (licencia SIL OFL, assets/fonts/OFL-OpenSans.txt) embebida: el prototipo y sus capturas usan la fuente
# de la marca sin internet (las capturas bloquean la red); variable de 300 a 800, subconjuntos latin y latin-ext
_FONTS = [("open-sans-latin-wght-normal.woff2", "U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD"),
          ("open-sans-latin-ext-wght-normal.woff2", "U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF")]
FONT = "<style>" + "".join(
    "@font-face{font-family:'Open Sans';font-style:normal;font-display:swap;font-weight:300 800;"
    f"src:url(data:font/woff2;base64,{base64.b64encode((ROOT / 'assets' / 'fonts' / f).read_bytes()).decode()}) format('woff2');unicode-range:{r}}}"
    for f, r in _FONTS) + "</style>"


def mix_white(hex_color, pct):
    h = hex_color.lstrip("#")[:6]
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    f = lambda c: round(c * pct + 255 * (1 - pct))
    return "#%02x%02x%02x" % (f(r), f(g), f(b))


def _lum(hex_color):
    h = hex_color.lstrip("#")[:6]
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def on_color(hex_color):
    """Texto legible sobre un color sólido (blanco o casi negro), el mismo criterio que solidFg() del runtime."""
    L = _lum(hex_color)
    return "#1a1a1a" if (L + 0.05) / (0.0103 + 0.05) > 1.05 / (L + 0.05) else "#ffffff"


# perfil CSS de Appian (brand → cssProfile) → variables CSS del runtime (lo que el prototipo sabe dibujar)
CSS_PROFILE_VARS = {
    "negative-on-light-color": "--negative", "positive-on-light-color": "--positive", "warn-on-light-color": "--warn", "info-on-light-color": "--info",
    "error-background-color": "--bg-negative", "success-background-color": "--bg-positive", "warn-background-color": "--bg-warn", "info-background-color": "--bg-info",
    "negative-on-dark-color": "--negative-dark", "positive-on-dark-color": "--positive-dark", "warn-on-dark-color": "--warn-dark", "info-on-dark-color": "--info-dark",
    "content-on-accent-color": "--accent-fg", "base-font-size": "--base-font",
    "label-on-light-color": "--label", "instructions-on-light-color": "--instr", "placeholder-text-on-light-color": "--placeholder", "required-asterisk-on-light-color": "--req",
    "input-box-on-light-border-color": "--input-border", "input-card-on-light-border-color": "--input-card-border", "input-on-light-background-color": "--input-bg",
    "card-box-shadow": "--card-shadow", "card-box-semi-rounded-border-radius": "--card-radius-semi", "card-box-rounded-border-radius": "--card-radius-round",
    "tag-standard-semi-rounded-border-radius": "--tag-radius", "tag-small-semi-rounded-border-radius": "--tag-radius-small",
    "tooltip-background-color": "--tip-bg", "tooltip-text-color": "--tip-fg", "tooltip-border-radius": "--tip-radius", "tooltip-icon-on-light-color": "--tip-icon",
    "button-hover-blur-radius": "--btn-glow", "pop-up-menu-on-light-background-color": "--popup-bg",
}
# según la forma del site (buttonShape / inputShape), qué radio del perfil se aplica
SHAPE_RADIUS = {("buttonShape", "SEMI_ROUNDED"): ("button-semi-rounded-border-radius", "--btn-radius"), ("buttonShape", "ROUNDED"): ("button-rounded-border-radius", "--btn-radius"),
                ("inputShape", "SEMI_ROUNDED"): ("input-box-semi-rounded-border-radius", "--input-radius")}


def css_profile_props(brand):
    """Propiedades del perfil CSS de la marca, en orden: [(comentario, {propiedad: valor})]."""
    cp = brand.get("cssProfile") or {}
    return [(g.get("comment"), g.get("properties") or {}) for g in cp.get("groups") or []]


def css_profile_text(brand):
    """Texto del perfil para pegar en Admin Console > Branding > CSS Profiles (propiedad: valor por línea; comentarios /* */, 26.9)."""
    cp = brand.get("cssProfile") or {}
    lines = [f"/* Perfil CSS «{cp.get('name', brand.get('name', ''))}» · generado por appian-prototipos · Appian 26.9 */"]
    if cp.get("typeface"):
        lines.append(f"/* Tipografía del perfil: {cp['typeface']} */")
    for comment, props in css_profile_props(brand):
        lines.append("")
        if comment:
            lines.append(f"/* {comment} */")
        lines += [f"{k}: {v}" for k, v in props.items()]
    return "\n".join(lines) + "\n"


def css_profile_vars(brand):
    """Declaraciones CSS que aplican el perfil al prototipo, más el color de texto legible sobre cada color semántico sólido."""
    flat = {k: v for _, props in css_profile_props(brand) for k, v in props.items()}
    out = {var: flat[k] for k, var in CSS_PROFILE_VARS.items() if k in flat}
    site = brand.get("site", {})
    for (key, shape), (prop, var) in SHAPE_RADIUS.items():
        if site.get(key, "SEMI_ROUNDED") == shape and prop in flat:
            out[var] = flat[prop]
    std = {"--negative": "#B2002C", "--positive": "#117C00", "--warn": "#D97706", "--info": "#115EBB"}
    for var, dflt in std.items():  # texto sobre el color sólido (cabeceras de a!boxLayout, sellos…)
        c = out.get(var, dflt)
        if re.match(r"^#[0-9A-Fa-f]{6}", c):
            out[var + "-fg"] = on_color(c)
    return out


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


def build(spec_path, out_path, brand_id="appian", do_validate=True):
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
    logo = ""  # una marca sin logo (la estándar de Appian: Logo = None en el Site) deja la cabecera sin logo
    if site.get("logo"):
        f = brand_dir / site["logo"]
        if not f.is_file():
            print(f"La marca «{brand_id}» cita el logo {site['logo']}, que no está en {brand_dir}: ponlo junto a "
                  f"brand-{brand_id}.json o quita «logo» de site si la marca no lleva logo.", file=sys.stderr)
            sys.exit(2)
        logo = f.read_text(encoding="utf-8")
    shape = {"SQUARED": "0px", "SEMI_ROUNDED": "4px", "ROUNDED": "999px"}
    dshape = {"SQUARED": "0px", "SEMI_ROUNDED": "8px", "ROUNDED": "16px"}
    prof = css_profile_vars(brand)
    prof_css = "".join(f"\n  {k}: {v};" for k, v in prof.items())
    tokens = f""":root {{
  --accent: {site['accentColor']};
  --accent-tint: {mix_white(site['accentColor'], 0.10)};
  --accent-fg: {on_color(site['accentColor'])};
  --hdr-bg: {site['backgroundColor']};
  --hdr-hl: {site['selectedPageHighlightColor']};
  --loading: {site.get('loadingBarColor', site['accentColor'])};
  --btn-radius: {shape[site.get('buttonShape', 'SEMI_ROUNDED')]};
  --input-radius: {shape[site.get('inputShape', 'SEMI_ROUNDED')].replace('999px', '4px')};
  --dialog-radius: {dshape[site.get('dialogShape', 'SEMI_ROUNDED')]};{prof_css}
}}"""
    safe = lambda o: json.dumps(o, ensure_ascii=False).replace("</", "<\\/")
    title = spec.get("app", {}).get("name", "Prototipo Appian")
    html = f"""<title>{title}</title>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="generator" content="appian-prototipos">
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
    profile = None
    if brand.get("cssProfile"):
        profile = Path(out_path).with_name(Path(out_path).stem + "-perfil-css.txt")
        profile.write_text(css_profile_text(brand), encoding="utf-8")
    kb = len(html.encode()) / 1024
    print(f"OK → {out_path} ({kb:.0f} KB, {len(spec.get('screens', []))} pantallas, {len(icons)} iconos)")
    print(f"OK → {trace}")
    if profile:
        print(f"OK → {profile} (perfil CSS para Admin Console › Branding › CSS Profiles)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("-o", "--out", default=None)
    ap.add_argument("--brand", default="appian", help="id de la marca: brand-<id>.json junto al app.json (por defecto, la estándar de Appian)")
    ap.add_argument("--no-validate", action="store_true")
    a = ap.parse_args()
    utf8_stdio()
    out = a.out or str(Path(a.spec).with_suffix(".html"))
    build(a.spec, out, a.brand, not a.no_validate)
