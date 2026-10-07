"""Utilidades comunes de los scripts: salida UTF-8 y navegador para Playwright."""
import sys


def utf8_stdio():
    """Evita errores de codificación al imprimir en consolas Windows o a través de tuberías."""
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")


def sync_playwright():
    try:
        from playwright.sync_api import sync_playwright as sp
    except ImportError:
        print("Falta Playwright para Python: pip install playwright\n"
              "Navegador: playwright install chromium, o usa Chrome / Edge si ya están instalados.", file=sys.stderr)
        sys.exit(2)
    return sp()


def launch_browser(p):
    """Chromium de Playwright; si no está descargado, Chrome o Edge del sistema."""
    errors = []
    for opts in ({}, {"channel": "chrome"}, {"channel": "msedge"}):
        try:
            return p.chromium.launch(**opts)
        except Exception as e:  # noqa: BLE001 - se prueba el siguiente navegador
            errors.append(f"{opts.get('channel', 'chromium de Playwright')}: {str(e).splitlines()[0]}")
    print("No hay navegador disponible. Instala uno de estos:\n  - playwright install chromium\n"
          "  - o Google Chrome / Microsoft Edge (se usan sin descargar nada más)\nDetalle:\n  " + "\n  ".join(errors),
          file=sys.stderr)
    sys.exit(2)
