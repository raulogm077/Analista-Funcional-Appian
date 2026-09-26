#!/usr/bin/env python3
"""Comprueba que el kit funciona en este equipo antes del primer prototipo.

Uso:  python3 selftest.py

1. Valida y construye el catálogo de patrones y el ejemplo ATP en una carpeta temporal.
2. Si hay Playwright y un navegador, pasa la prueba de humo sobre el catálogo.
Sale con 0 si validar y construir funcionan (lo imprescindible); la prueba de humo y
las capturas son opcionales y se informa de lo que falta para tenerlas.
"""
import pathlib, subprocess, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from entorno import utf8_stdio  # noqa: E402


def run(args):
    r = subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, (r.stdout + r.stderr).strip()


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
                 ("galería de IA (26.9)", ROOT / "examples" / "ia" / "app.json")]
        built = None
        for name, spec in cases:
            html = tmp / (spec.parent.name + ".html")
            code, out = run([HERE / "build.py", spec, "-o", html])
            if code == 0 and html.exists():
                print(f"✓ Validar y construir: {name}")
                built = built or (html, spec)
            else:
                ok = False
                print(f"✗ Validar y construir: {name}\n{out}")
        if built:
            code, out = run([HERE / "smoke_test.py", *built])
            if code == 0:
                print("✓ Prueba de humo (Playwright + navegador): capturas y pruebas disponibles")
            elif code == 2:
                print("· Prueba de humo no disponible (opcional):\n  " + out.replace("\n", "\n  "))
            else:
                ok = False
                print(f"✗ Prueba de humo con errores:\n{out}")
    print("\nKit listo." if ok else "\nEl kit tiene errores: revisa los mensajes anteriores.")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
