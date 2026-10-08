#!/usr/bin/env python3
"""comprobar_asis.py - Comprueba la documentación de ingeniería inversa antes de entregarla.

Uso:
  python3 <skill>/scripts/comprobar_asis.py <carpeta_salida>

Lee los .md de <salida>, <salida>/datos/inventario.json (build_datos.py) y <trabajo>/summary.json (build_summary.py).

Errores (✗, salida 1):
  - un nombre entre comillas invertidas que empieza por el prefijo de la aplicación (seguido de «_» o espacio; se
    corta en «.», «#», «(» o «[») y no es un objeto del inventario, algo que se cita con uno ni la aplicación;
  - una tabla con columna «Certeza» sin columna «Evidencia» (salvo el registro de 09, cuyas filas enlazan en «Dónde»
    al documento que tiene la evidencia), una fila cuya evidencia no enlaza a un fichero del anexo o una certeza que
    no es ✅, 🔵 ni ❓;
  - cifras de 00 («N objetos», «N process models», «N interfaces», «N record types») distintas de las de summary.json;
  - un «{{» sin sustituir o un enlace relativo a un fichero que no existe.
  Las tablas y los «{{» no se miran en anexo/ ni en extraccion/ (una lista anidada de SAIL lleva «{{»).
Avisos (·), con redaccion.py del analista: muletillas, frases de más de 35 palabras, párrafos de 20 palabras o más
repetidos en dos documentos y documentos por encima de su presupuesto (assets/presupuesto-palabras.json).
Salida: 0 sin errores, 1 con errores, 2 uso o faltan datos/inventario.json o summary.json.
"""
from __future__ import annotations

import fnmatch
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from rutas import work_dir  # noqa: E402

SKILL = AQUI.parent
sys.path.append(str(SKILL.parent / "appian-functional-analyst" / "scripts"))
try:
    import redaccion as rd  # noqa: E402
except ImportError:  # la skill suelta, sin el analista al lado
    rd = None

PRESUPUESTO = SKILL / "assets" / "presupuesto-palabras.json"
SIN_TABLAS = ("anexo", "extraccion")
REGISTRO = ("<!-- registro:inicio -->", "<!-- registro:fin -->")
CERTEZAS = ("✅", "🔵", "❓")
CODIGO = re.compile(r"`([^`\n]+)`")
ENLACE = re.compile(r"!?\[[^\]\n]*\]\((<[^>\n]+>|[^)\s]+)(?:\s+\"[^\"\n]*\")?\)")
CIFRA = re.compile(r"(\d[\d.]*)\s+(objetos|process models?|interfa(?:ces|z)|record types?)\b", re.I)


def lineas(texto: str) -> list[tuple[int, str]]:
    """(número, línea) fuera de bloques de código y comentarios HTML."""
    texto = re.sub(r"<!--.*?-->", lambda m: "\n" * m.group(0).count("\n"), texto, flags=re.S)
    out, codigo = [], False
    for n, l in enumerate(texto.splitlines(), 1):
        if l.strip().startswith(("```", "~~~")):
            codigo = not codigo
            continue
        if not codigo:
            out.append((n, l))
    return out


def celdas(linea: str) -> list[str]:
    return [c.strip() for c in re.split(r"(?<!\\)\|", linea.strip().strip("|"))]


def destinos(linea: str) -> list[str]:
    """Los destinos relativos de los enlaces de una línea (sin los de fuera ni los que solo son un ancla)."""
    out = []
    for m in ENLACE.finditer(CODIGO.sub("x", linea)):
        d = m.group(1).strip("<>")
        if re.match(r"^[a-z][a-z0-9+.-]*:", d, re.I) or d.startswith("#"):
            continue
        d = unquote(d.split("#", 1)[0].split("?", 1)[0])
        if d:
            out.append(d)
    return out


def nombre_citado(s: str, prefijo: str) -> str | None:
    s = re.sub(r"^[A-Za-z]+!(\{[^}]*\})?", "", s.strip().strip("'\""))   # rule!X, recordType!{uuid}X
    if not re.match(rf"{re.escape(prefijo)}[_ ]\S", s):
        return None
    return re.split(r"[.#(\[]", s, 1)[0].rstrip()


def tablas(numeradas: list[tuple[int, str]]):
    """(número de la cabecera, cabecera, [(número, celdas)]) de cada tabla."""
    i = 0
    while i < len(numeradas):
        n, l = numeradas[i]
        sig = numeradas[i + 1][1] if i + 1 < len(numeradas) else ""
        if l.lstrip().startswith("|") and re.match(r"^\s*\|?\s*:?-{3,}", sig):
            filas, j = [], i + 2
            while j < len(numeradas) and numeradas[j][1].lstrip().startswith("|"):
                filas.append((numeradas[j][0], celdas(numeradas[j][1])))
                j += 1
            yield n, celdas(l), filas
            i = j
        else:
            i += 1


def comprobar(salida: Path) -> tuple[list[str], list[str]]:
    """(errores, avisos) de la documentación de <salida>."""
    salida = Path(salida).resolve()
    inv = json.loads((salida / "datos" / "inventario.json").read_text(encoding="utf-8"))
    resumen = json.loads((work_dir(salida) / "summary.json").read_text(encoding="utf-8"))
    app = inv.get("aplicacion") or {}
    prefijo = app.get("prefijo")
    conocidos = {app.get("nombre")} | {o.get("nombre") for o in inv.get("objetos", [])} | \
                {t for o in inv.get("objetos", []) for t in o.get("tambien", [])}
    anexo = salida / "anexo"
    errores: list[tuple] = []
    avisos: list[tuple] = []
    textos: dict[str, str] = {}
    for doc in sorted(salida.rglob("*.md")):
        rel = doc.relative_to(salida).as_posix()
        texto = doc.read_text(encoding="utf-8")
        numeradas = lineas(texto)
        con_tablas = rel.split("/", 1)[0] not in SIN_TABLAS
        e = lambda n, msg: errores.append((rel, n, msg))  # noqa: E731
        # nombres que empiezan por el prefijo
        for n, l in numeradas if prefijo else []:
            for m in CODIGO.finditer(l):
                nombre = nombre_citado(m.group(1), prefijo)
                if nombre and nombre not in conocidos:
                    e(n, f"`{nombre}` no es un objeto del inventario ni se cita con uno")
        if con_tablas:
            # certeza y evidencia
            registro, dentro = set(), False
            for n, l in enumerate(texto.splitlines(), 1):
                dentro = (dentro or REGISTRO[0] in l) and REGISTRO[1] not in l
                if dentro:
                    registro.add(n)
            for n, cab, filas in tablas(numeradas):
                cols = [c.replace("*", "").lower() for c in cab]
                cert = next((k for k, c in enumerate(cols) if c.startswith("certeza")), None)
                evid = next((k for k, c in enumerate(cols) if c.startswith("evidencia")), None)
                if cert is not None and evid is None and n not in registro:
                    e(n, "tabla con «Certeza» sin «Evidencia»")
                for fn, fila in filas:
                    if cert is not None and cert < len(fila) and not fila[cert].startswith(CERTEZAS):
                        e(fn, f"certeza «{fila[cert]}»: es ✅, 🔵 o ❓")
                    if evid is not None and not any(
                            anexo in (doc.parent / d).resolve().parents and (doc.parent / d).resolve().is_file()
                            for d in destinos(fila[evid] if evid < len(fila) else "")):
                        e(fn, "la evidencia no enlaza a una ficha del anexo")
            # marcadores sin sustituir
            for n, l in numeradas:
                if "{{" in CODIGO.sub("", l) or any(re.search(r"\{\{[^{}]*\}\}", c) for c in CODIGO.findall(l)):
                    e(n, "«{{» sin sustituir")
        # enlaces rotos
        for n, l in numeradas:
            for d in destinos(l):
                if not (doc.parent / d).exists():
                    e(n, f"enlace a {d}, que no existe")
        if con_tablas:
            textos[rel] = re.sub(r"<!--.*?-->", "", texto, flags=re.S)
    # cifras de 00
    cero = salida / "00-resumen-ejecutivo.md"
    if cero.exists():
        numeradas = lineas(cero.read_text(encoding="utf-8"))
        volumen = [(n, l) for n, l in numeradas if "volumen" in l.lower()] or numeradas
        esperado = {"objetos": (resumen.get("totals") or {}).get("objects"),
                    "process model": (resumen.get("counts") or {}).get("processModel", 0),
                    "interfa": (resumen.get("counts") or {}).get("interface", 0),
                    "record type": (resumen.get("counts") or {}).get("recordType", 0)}
        vistas = set()
        for n, l in volumen:
            for m in CIFRA.finditer(l.replace("*", "")):
                clave = next(k for k in esperado if m.group(2).lower().startswith(k))
                if clave in vistas:
                    continue
                vistas.add(clave)
                if esperado[clave] is not None and int(m.group(1).replace(".", "")) != esperado[clave]:
                    errores.append(("00-resumen-ejecutivo.md", n, f"«{m.group(0)}»: summary.json dice {esperado[clave]}"))
    redaccion(salida, textos, resumen.get("counts") or {}, avisos)
    orden = lambda x: (x[0], x[1] or 0)  # noqa: E731
    return ([f"{r}:{n} {m}" if n else f"{r}: {m}" for r, n, m in sorted(errores, key=orden)],
            [f"{r}:{n} {m}" if n else f"{r}: {m}" for r, n, m in sorted(avisos, key=orden)])


def prosa(l: str) -> str:
    """La línea como se lee: sin código en línea ni destinos de enlaces."""
    return re.sub(r"\]\([^)]*\)", "]", CODIGO.sub(" ", l))


def redaccion(salida: Path, textos: dict[str, str], cuentas: dict, avisos: list) -> None:
    if rd is None:
        avisos.append(("redaccion", None, "sin avisos de redacción: no está appian-functional-analyst/scripts/redaccion.py"))
        return
    muletillas = rd.muletillas()
    presupuesto = json.loads(PRESUPUESTO.read_text(encoding="utf-8")).get("documentos", {})
    for rel, texto in textos.items():
        palabras = 0
        for n, l in lineas(texto):
            if l.lstrip().startswith("#"):
                continue
            leida = prosa(l)
            palabras += len(re.findall(r"\w+", leida))
            normal = rd.normaliza(leida)
            for x in muletillas:
                if re.search(rf"(?<!\w){re.escape(x)}(?!\w)", normal):
                    avisos.append((rel, n, f"muletilla «{x}»"))
            trozos = celdas(leida) if l.lstrip().startswith("|") else [leida]
            for t in trozos:
                for f in rd.frases(t):
                    k = len(re.findall(r"\w+", f))
                    if k > rd.MAX_PALABRAS:
                        avisos.append((rel, n, f"frase de {k} palabras (más de {rd.MAX_PALABRAS})"))
        regla = presupuesto.get(rel) or next((v for k, v in presupuesto.items() if fnmatch.fnmatch(rel, k)), None)
        if regla:
            limite = regla.get("base", 0) + sum(p * cuentas.get(t, 0) for t, p in (regla.get("porObjeto") or {}).items())
            if palabras > limite:
                avisos.append((rel, None, f"{palabras} palabras, más que su presupuesto ({limite})"))
    for p, nombres in rd.parrafos_repetidos(textos):
        avisos.append((nombres[0], None, f"párrafo repetido en {' y '.join(nombres)}: «{p[:60]}…»"))


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__, file=sys.stderr)
        return 2
    salida = Path(argv[0]).resolve()
    for falta, script in ((salida / "datos" / "inventario.json", "build_datos.py"),
                          (work_dir(salida) / "summary.json", "build_summary.py")):
        if not falta.exists():
            print(f"ERROR: falta {falta} (ejecuta antes {script})", file=sys.stderr)
            return 2
    errores, avisos = comprobar(salida)
    for x in errores:
        print(f"✗ {x}")
    for x in avisos:
        print(f"· {x}")
    print(f"{len(errores)} errores · {len(avisos)} avisos")
    return 1 if errores else 0


if __name__ == "__main__":
    for st in (sys.stdout, sys.stderr):
        st.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv[1:]))
