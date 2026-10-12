#!/usr/bin/env python3
"""Comprueba que las URL de docs.appian.com que citan las skills existen y que sus anclas están en la página.

  python3 pruebas/comprobar_anclas.py [--skill <nombre>]... [--cache <carpeta>]

Necesita red: por eso no entra en comprobar_plugin.py --completo. Descarga cada página una vez (sigue la redirección de
/latest/ a la versión vigente) y busca el ancla como id="…" o name="…". Con --cache guarda las páginas en esa carpeta y
las reutiliza. Por defecto mira appian-best-practices; --skill se puede repetir.

Salida: «fichero:línea URL — motivo» por cada enlace roto. Código 1 si hay alguno, 2 si no se pudo descargar nada.
"""
from __future__ import annotations

import argparse
import hashlib
import http.client
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.dont_write_bytecode = True

RAIZ = Path(__file__).resolve().parent.parent
URL = re.compile(r"https://docs\.appian\.com/suite/help/[^\s<>()\[\]\"'`|]+")
SOBRA_AL_FINAL = ".,;:*"  # puntuación o negrita de Markdown pegada a la URL
AGENTE = "Mozilla/5.0 (comprobar_anclas.py; appian-analisis-funcional)"
SIN_RED, NO_EXISTE = "sin red", "la página no existe"


def urls_citadas(skills):
    """[(fichero relativo, línea, URL)] de cada .md de las skills, en orden."""
    citas = []
    for nombre in skills:
        for f in sorted((RAIZ / "skills" / nombre).rglob("*.md")):
            for n, linea in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                for m in URL.finditer(linea):
                    citas.append((f.relative_to(RAIZ).as_posix(), n, m.group(0).rstrip(SOBRA_AL_FINAL)))
    return citas


def descargar(pagina, cache):
    """El HTML de `pagina`, o SIN_RED o NO_EXISTE. Con `cache`, lo guarda y lo reutiliza."""
    guardada = cache / (hashlib.sha1(pagina.encode()).hexdigest() + ".html") if cache else None
    if guardada and guardada.is_file():
        return guardada.read_text(encoding="utf-8", errors="replace")
    try:
        with urllib.request.urlopen(urllib.request.Request(pagina, headers={"User-Agent": AGENTE}), timeout=30) as r:
            html = r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return NO_EXISTE if e.code in (404, 410) else SIN_RED
    except (urllib.error.URLError, http.client.HTTPException, TimeoutError, OSError, ValueError):
        return SIN_RED  # también una URL que no se puede pedir (caracteres no ASCII) o una respuesta cortada
    if guardada:
        guardada.write_text(html, encoding="utf-8")
    return html


def tiene_ancla(html, ancla):
    return re.search(r"""\b(?:id|name)=["']%s["']""" % re.escape(ancla), html) is not None


def main() -> int:
    for s in (sys.stdout, sys.stderr):  # consolas de Windows sin UTF-8
        s.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--skill", action="append", help="skill que se mira (por defecto, appian-best-practices)")
    ap.add_argument("--cache", help="carpeta donde guardar y reutilizar las páginas descargadas")
    a = ap.parse_args()
    skills = a.skill or ["appian-best-practices"]
    for nombre in skills:
        if not (RAIZ / "skills" / nombre).is_dir():
            print(f"No existe la skill {nombre}.", file=sys.stderr)
            return 2
    cache = Path(a.cache).resolve() if a.cache else None
    if cache:
        cache.mkdir(parents=True, exist_ok=True)

    citas = urls_citadas(skills)
    paginas = sorted({u.split("#", 1)[0] for _, _, u in citas})
    with ThreadPoolExecutor(max_workers=8) as ex:
        html = dict(zip(paginas, ex.map(lambda p: descargar(p, cache), paginas)))
    if paginas and all(h == SIN_RED for h in html.values()):
        print("No se pudo descargar ninguna página: sin red o docs.appian.com no responde.", file=sys.stderr)
        return 2

    rotas = []
    for fichero, linea, url in citas:
        pagina, _, ancla = url.partition("#")
        h = html[pagina]
        if h in (SIN_RED, NO_EXISTE):
            rotas.append(f"{fichero}:{linea} {url} — {h}")
        elif ancla and not tiene_ancla(h, urllib.parse.unquote(ancla)):
            rotas.append(f"{fichero}:{linea} {url} — el ancla no está en la página")
    for r in rotas:
        print(r)
    con_ancla = sum(1 for _, _, u in citas if "#" in u)
    print(f"{len(citas)} citas ({con_ancla} con ancla) a {len(paginas)} páginas: {len(rotas)} rotas")
    return 1 if rotas else 0


if __name__ == "__main__":
    sys.exit(main())
