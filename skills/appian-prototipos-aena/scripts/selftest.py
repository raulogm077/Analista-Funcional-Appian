#!/usr/bin/env python3
"""Comprueba que el kit funciona en este equipo antes del primer prototipo.

Uso:  python3 selftest.py

1. Valida y construye el catálogo de patrones y el ejemplo ATP en una carpeta temporal.
2. Si hay Playwright y un navegador, pasa la prueba de humo sobre el catálogo.
Sale con 0 si validar y construir funcionan (lo imprescindible); la prueba de humo y
las capturas son opcionales y se informa de lo que falta para tenerlas.
"""
import json, pathlib, re, subprocess, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from entorno import utf8_stdio  # noqa: E402


def run(args):
    r = subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, (r.stdout + r.stderr).strip()


def coverage():
    """Cada función del catálogo oficial de Appian (schemas/catalogo-appian.json) la conocen los schemas, la pinta el runtime
    (o la consume su componente padre) y aparece en la galería examples/componentes."""
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
    walk(json.loads((ROOT / "examples" / "componentes" / "app.json").read_text(encoding="utf-8")))
    probs = [f"{f}: no está en los schemas" for f in funcs if f not in known]
    probs += [f"{f}: el runtime no lo pinta" for f in funcs if f not in rend and f not in SUBOBJECTS]
    probs += [f"{f}: falta en la galería de componentes" for f in funcs if f not in used]
    return cat, funcs, probs


def main():
    utf8_stdio()
    ok = True
    print(f"Python {sys.version.split()[0]} ({sys.executable})")
    if sys.version_info < (3, 9):
        print("✗ Hace falta Python 3.9 o superior")
        sys.exit(1)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        cases = [("catálogo de patrones", ROOT / "templates" / "catalogo-patrones.json"),
                 ("ejemplo ATP", ROOT / "examples" / "atp" / "app.json"),
                 ("galería de bloques", ROOT / "examples" / "bloques" / "app.json"),
                 ("galería de IA (26.9)", ROOT / "examples" / "ia" / "app.json"),
                 ("galería de componentes (26.9)", ROOT / "examples" / "componentes" / "app.json")]
        cat, funcs, probs = coverage()
        if probs:
            ok = False
            print(f"✗ Catálogo de Appian {cat['version']}: " + "; ".join(probs))
        else:
            print(f"✓ Catálogo de Appian {cat['version']}: {len(funcs)} componentes en schemas, runtime y galería")
        built = []  # (nombre, html, spec) de lo que se ha construido
        for name, spec in cases:
            html = tmp / (spec.parent.name + ".html")
            code, out = run([HERE / "build.py", spec, "-o", html])
            if code == 0 and html.exists():
                print(f"✓ Validar y construir: {name}")
                built.append((name, html, spec))
            else:
                ok = False
                print(f"✗ Validar y construir: {name}\n{out}")
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
            code, out = run([HERE / "contrast_audit.py", html, spec, "--strict"])
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
