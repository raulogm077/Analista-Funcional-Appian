#!/usr/bin/env python3
"""Reglas de prosa comunes. Las usan comprobar.py del analista y comprobar_asis.py de ingeniería inversa.

  muletillas(ruta=None)              expresiones de references/redaccion.md («- «x» → …»), normalizadas
  frases(texto)                      las frases de un texto
  MAX_PALABRAS                       palabras por frase, como mucho
  parrafos_repetidos(textos, minimo) párrafos de `minimo` palabras o más que están en dos textos o más
"""
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import modelo as mo  # noqa: E402

GUIA = pathlib.Path(__file__).resolve().parents[1] / "references" / "redaccion.md"
MAX_PALABRAS = 35


def muletillas(ruta=None):
    """Las expresiones de la guía (`- «x» → qué hacer`), sin mayúsculas ni tildes. [] si no está la guía."""
    f = pathlib.Path(ruta) if ruta else GUIA
    if not f.exists():
        return []
    return [mo.normaliza(x) for x in re.findall(r"^- «([^»]+)» →", f.read_text(encoding="utf-8"), re.M)]


def frases(texto):
    texto = re.sub(r"\*\*|~~|\||https?://\S+", " ", texto)
    return [f.strip() for f in re.split(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÑ«¿])", texto) if f.strip()]


def parrafos(texto):
    """Los párrafos de un markdown: bloques entre líneas en blanco, sin código, tablas ni títulos."""
    out, bloque, codigo = [], [], False
    for linea in texto.splitlines() + [""]:
        l = linea.strip()
        if l.startswith(("```", "~~~")):
            codigo, l = not codigo, ""
        elif codigo:
            continue
        if not l or l.startswith(("#", "|")):
            if bloque:
                out.append(" ".join(bloque))
            bloque = []
        else:
            bloque.append(l)
    return out


def parrafos_repetidos(textos, minimo=20):
    """[(párrafo, [nombres])] de los párrafos de `minimo` palabras o más que están en dos o más de los `textos`
    ({nombre: texto}); se comparan sin mayúsculas, tildes ni signos."""
    vistos = {}
    for nombre, texto in textos.items():
        for p in parrafos(texto):
            palabras = re.findall(r"\w+", mo.normaliza(p))
            if len(palabras) < minimo:
                continue
            nombres = vistos.setdefault(" ".join(palabras), (p, []))[1]
            if nombre not in nombres:
                nombres.append(nombre)
    return [(p, nombres) for p, nombres in vistos.values() if len(nombres) > 1]
