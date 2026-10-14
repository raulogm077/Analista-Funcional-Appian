"""Utilidades comunes de los scripts: salida UTF-8, ficheros con el mismo final de línea y navegador para Playwright."""
import sys


def utf8_stdio():
    """Evita errores de codificación al imprimir en consolas Windows o a través de tuberías."""
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")


def escribe(ruta, texto):
    """Escribe un fichero de texto en UTF-8 con finales de línea \\n en cualquier sistema (write_text() los pone \\r\\n
    en Windows): en un proyecto que comparten varios equipos, reescribirlo no cambia todas sus líneas."""
    with open(ruta, "w", encoding="utf-8", newline="\n") as f:
        f.write(texto)


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
