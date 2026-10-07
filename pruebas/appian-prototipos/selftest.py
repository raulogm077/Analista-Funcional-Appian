#!/usr/bin/env python3
"""Comprueba que el kit funciona en este equipo.

Uso:  python3 pruebas/appian-prototipos/selftest.py

Prueba el kit de $PLUGIN_A_PROBAR/skills/appian-prototipos (por defecto, el de este repositorio).
1. Valida y construye, en una carpeta temporal, el catálogo de patrones, el prototipo de prueba de dos pantallas
   que genera datos/autorizaciones/generar_app.py a partir del análisis ficticio del analista y cada galería
   (galerias/<galería>/app.json: las que haya).
2. La marca: sin --brand, la estándar de Appian y sin logo; con --brand x, la de brand-x.json junto al app.json (con su
   logo); con una marca que no está junto al app.json, error que dice dónde ponerla; y los helpers, con la neutra por
   defecto y la del proyecto con usar_marca().
3. Si hay Playwright y un navegador, pasa la prueba de humo y la auditoría de contraste a todo lo construido.
Sale con 0 si validar y construir funcionan (lo imprescindible); la prueba de humo y
las capturas son opcionales y se informa de lo que falta para tenerlas.
"""
import json, os, pathlib, re, subprocess, sys, tempfile

AQUI = pathlib.Path(__file__).resolve().parent
PLUGIN = pathlib.Path(os.environ.get("PLUGIN_A_PROBAR") or AQUI.parents[1]).resolve()
ROOT = PLUGIN / "skills" / "appian-prototipos"
HERE = ROOT / "scripts"
sys.path.insert(0, str(HERE))
from entorno import utf8_stdio  # noqa: E402


def run(args):
    r = subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, (r.stdout + r.stderr).strip()


def coverage():
    """Cada función del catálogo oficial de Appian (schemas/catalogo-appian.json) la conocen los schemas, la pinta el runtime
    (o la consume su componente padre) y aparece en la galería galerias/componentes."""
    from validate import load_catalog, SUBOBJECTS
    cat = json.loads((ROOT / "schemas" / "catalogo-appian.json").read_text(encoding="utf-8"))
    funcs = [f for fs in cat["categories"].values() for f in fs]
    known = load_catalog()
    rend = set(re.findall(r'R\["(a![A-Za-z]+)"\]\s*=', (ROOT / "runtime" / "appian-kit.js").read_text(encoding="utf-8")))
    used = set()

    def walk(o):
        if isinstance(o, dict):
            if isinstance(o.get("type"), str):
                used.add(o["type"])
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(json.loads((ROOT / "galerias" / "componentes" / "app.json").read_text(encoding="utf-8")))
    probs = [f"{f}: no está en los schemas" for f in funcs if f not in known]
    probs += [f"{f}: el runtime no lo pinta" for f in funcs if f not in rend and f not in SUBOBJECTS]
    probs += [f"{f}: falta en la galería de componentes" for f in funcs if f not in used]
    return cat, funcs, probs


# marca de prueba que va junto al app.json, como la de un cliente en <p>/prototipo/ (colores que no son de ninguna otra)
MARCA_PRUEBA = {"id": "prueba", "name": "Marca de prueba",
                "site": {"navigationLayout": "HEADER_BAR", "headerBarStyle": "MERCURY", "backgroundColor": "#22313F",
                         "selectedPageHighlightColor": "#F2C14E", "accentColor": "#7B2D8E", "logo": "logo-prueba.svg", "logoAltText": "Prueba"},
                "palette": {"navy": "#22313F"}}
LOGO_PRUEBA = "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 10 10'><title>logo de prueba</title></svg>"


def built_with(html):
    """La marca con la que se construyó un HTML (el JSON de px-brand) y su logo (la plantilla px-logo)."""
    t = pathlib.Path(html).read_text(encoding="utf-8")
    m = re.search(r'<script type="application/json" id="px-brand">(.*?)</script>', t, re.S)
    logo = re.search(r'<template id="px-logo">(.*?)</template>', t, re.S)
    return (json.loads(m.group(1)) if m else {}), (logo.group(1) if logo else None), t


def brands(tmp, built):
    """[(qué se comprueba, problemas)] de la marca en build.py y en los helpers."""
    out = []
    cat = next((html for _, html, spec in built if spec.name == "catalogo-patrones.json"), None)
    probs = []
    if cat is None:
        probs.append("no se construyó el catálogo de patrones")
    else:
        b, logo, _ = built_with(cat)
        if b.get("id") != "appian":
            probs.append(f"sin --brand, build.py construye con «{b.get('id')}» y no con «appian»")
        if logo:
            probs.append("la marca estándar de Appian no lleva logo y el HTML trae uno")
    out.append(("marca por defecto (sin --brand): appian, sin logo", probs))
    # la marca del proyecto: brand-prueba.json y su logo junto al app.json
    carpeta = tmp / "Carpeta con espacios" / "prototipo"
    carpeta.mkdir(parents=True)
    spec = carpeta / "app.json"
    spec.write_text((ROOT / "templates" / "catalogo-patrones.json").read_text(encoding="utf-8"), encoding="utf-8")
    (carpeta / "brand-prueba.json").write_text(json.dumps(MARCA_PRUEBA, ensure_ascii=False), encoding="utf-8")
    (carpeta / "logo-prueba.svg").write_text(LOGO_PRUEBA, encoding="utf-8")
    html = carpeta / "prototipo.html"
    code, salida = run([HERE / "build.py", spec, "-o", html, "--brand", "prueba"])
    probs = []
    if code or not html.exists():
        probs.append(f"build.py --brand prueba falla:\n{salida[-800:]}")
    else:
        b, logo, t = built_with(html)
        if b.get("id") != "prueba":
            probs.append(f"con --brand prueba construye con «{b.get('id')}»")
        if f"--accent: {MARCA_PRUEBA['site']['accentColor']};" not in t:
            probs.append("el HTML no lleva el acento de la marca del proyecto")
        if "logo de prueba" not in (logo or ""):
            probs.append("el HTML no lleva el logo de la marca del proyecto")
    out.append(("marca del proyecto (--brand prueba, junto al app.json): sus colores y su logo", probs))
    # una marca que no está junto al app.json: error que dice dónde ponerla
    sin = tmp / "sin marca"
    sin.mkdir()
    (sin / "app.json").write_text(spec.read_text(encoding="utf-8"), encoding="utf-8")
    code, salida = run([HERE / "build.py", sin / "app.json", "-o", sin / "prototipo.html", "--brand", "aena"])
    falta = str(sin.resolve() / "brand-aena.json")
    probs = [] if code and falta in salida else [f"build.py --brand aena sin brand-aena.json sale con {code} y no dice «{falta}»:\n{salida[-600:]}"]
    out.append(("marca que falta (--brand aena sin su fichero): error con la ruta donde ponerla", probs))
    # los helpers: la marca neutra por defecto y la del proyecto con usar_marca(), antes de from sail_helpers import *
    prog = ("import sys; sys.path.insert(0, sys.argv[1]); import sail_helpers as s; print(s._BRAND.get('id'), s.PRIMARY); "
            "s.usar_marca('prueba', sys.argv[2]); from sail_helpers import NAVY, GREEN; print(NAVY, GREEN)")
    code, salida = run(["-c", prog, HERE, carpeta])
    lineas = salida.splitlines()
    esperado = ["appian ACCENT", f"{MARCA_PRUEBA['palette']['navy']} {MARCA_PRUEBA['site']['selectedPageHighlightColor']}"]
    probs = [] if code == 0 and lineas[-2:] == esperado else [f"esperaba {esperado} y sale ({code}):\n{salida[-600:]}"]
    out.append(("helpers: marca neutra por defecto y la del proyecto con usar_marca()", probs))
    return out


def main():
    utf8_stdio()
    ok = True
    print(f"Python {sys.version.split()[0]} ({sys.executable})")
    if sys.version_info < (3, 9):
        print("✗ Hace falta Python 3.9 o superior")
        sys.exit(1)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        # el prototipo de prueba sale del análisis ficticio del analista (modelo.py), como en un proyecto
        prueba = tmp / "autorizaciones" / "app.json"
        code, out = run([AQUI / "datos" / "autorizaciones" / "generar_app.py", prueba])
        if code:
            ok = False
            print(f"✗ Generar el prototipo de prueba «autorizaciones» desde el análisis\n{out}")
        # las galerías (el catálogo del kit) se descubren solas
        galerias = [(f"galería «{p.parent.name}»", p) for p in sorted((ROOT / "galerias").glob("*/app.json"))]
        cases = [("catálogo de patrones", ROOT / "templates" / "catalogo-patrones.json"),
                 *([("prototipo de prueba «autorizaciones»", prueba)] if not code else []), *galerias]
        cat, funcs, probs = coverage()
        if probs:
            ok = False
            print(f"✗ Catálogo de Appian {cat['version']}: " + "; ".join(probs))
        else:
            print(f"✓ Catálogo de Appian {cat['version']}: {len(funcs)} componentes en schemas, runtime y galería")
        built = []  # (nombre, html, spec) de lo que se ha construido
        for name, spec in cases:
            html = tmp / (spec.parent.name + ".html")  # nombres únicos: templates, autorizaciones y una por galería
            code, out = run([HERE / "build.py", spec, "-o", html])
            if code == 0 and html.exists():
                print(f"✓ Validar y construir: {name}")
                built.append((name, html, spec))
            else:
                ok = False
                print(f"✗ Validar y construir: {name}\n{out}")
        for que, probs in brands(tmp, built):
            if probs:
                ok = False
                print(f"✗ Marca: {que}\n  " + "\n  ".join(probs))
            else:
                print(f"✓ Marca: {que}")
        # prueba de humo (clics y expresiones) y contraste en todo lo construido
        browser = True
        for name, html, spec in built:
            code, out = run([HERE / "smoke_test.py", html, spec])
            if code == 0:
                print(f"✓ Prueba de humo ({name}, Playwright + navegador): {out.splitlines()[0] if out else 'sin errores'}")
            elif code == 2:
                print("· Prueba de humo y contraste no disponibles (opcional):\n  " + out.replace("\n", "\n  "))
                browser = False
                break
            else:
                ok = False
                print(f"✗ Prueba de humo con errores ({name}):\n{out}")
        for name, html, spec in built if browser else []:
            # contraste WCAG 2.2 AA de lo que se ve (texto, marcadores de posición, bordes de campo, textos de gráficos)
            code, out = run([HERE / "contrast_audit.py", html, spec])
            last = out.splitlines()[-1] if out else ""
            if code == 0:
                print(f"✓ Contraste ({name}): {last.replace('Contraste: ', '')}")
            else:
                ok = False
                print(f"✗ Contraste ({name}):\n{out}")
    print("\nKit listo." if ok else "\nEl kit tiene errores: revisa los mensajes anteriores.")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
