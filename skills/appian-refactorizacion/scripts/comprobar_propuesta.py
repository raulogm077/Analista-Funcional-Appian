#!/usr/bin/env python3
"""comprobar_propuesta.py - Comprueba refactorizacion/propuesta.md contra lo que documentó la ingeniería inversa.

Uso:
  python3 <skill>/scripts/comprobar_propuesta.py <carpeta del proyecto>

Lee <p>/refactorizacion/propuesta.md y, de <p>/as-is/datos/, inventario.json, dependencias.json, hallazgos.json y
sin-verificar.json (los dos últimos, si están).

Errores (✗, salida 1):
  - falta uno de los seis apartados (## 1. Alcance … ## 6. Pendientes) o el Diagnóstico no tiene ninguna REF;
  - una REF sin Evidencia, Regla, Efecto, Prioridad o Esfuerzo; una evidencia sin enlace a as-is/; una Regla sin
    «BP nn §x»; una Prioridad que no es Alta, Media ni Baja, o un Esfuerzo que no es S, M ni L;
  - un enlace relativo a un fichero que no existe, o a la extracción en bruto de ingeniería inversa;
  - una «BP nn §x» que no encuentra appian-best-practices/scripts/seccion.py nn x;
  - en el Diagnóstico, un nombre entre comillas invertidas que empieza por el prefijo de la aplicación y no es un
    objeto del inventario, algo que se cita con uno («tambien»), un objeto de fuera de la aplicación ni la aplicación
    (la Solución sí puede nombrar objetos nuevos);
  - una REF del Diagnóstico que no aparece en la Solución, o una REF citada que no está en el Diagnóstico;
  - un H-… que no está en hallazgos.json o un NV-… que no está en sin-verificar.json.
Avisos (·): una REF que no está en la Hoja de ruta; una REF cuya evidencia cita un hallazgo inferido o pendiente sin
«Verificar H-…» antes en la Hoja de ruta.
Salida: 0 sin errores, 1 con errores, 2 uso o faltan la propuesta o as-is/datos/inventario.json.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
sys.dont_write_bytecode = True  # sin __pycache__ en el plugin: no se escribe fuera del proyecto
import unicodedata
from pathlib import Path
from urllib.parse import unquote

SECCION = Path(__file__).resolve().parents[2] / "appian-best-practices" / "scripts" / "seccion.py"
APARTADOS = ("1. Alcance", "2. Diagnóstico", "3. Solución", "4. Migración y convivencia", "5. Hoja de ruta",
             "6. Pendientes")
CAMPOS = ("Evidencia", "Regla", "Efecto", "Prioridad", "Esfuerzo")
PRIORIDADES = ("Alta", "Media", "Baja")
CODIGO = re.compile(r"`([^`\n]+)`")
ENLACE = re.compile(r"!?\[[^\]\n]*\]\((<[^>\n]+>|[^)\s]+)(?:\s+\"[^\"\n]*\")?\)")
FICHA = re.compile(r"^(?:#{3,4}\s+)?(REF-\d{2,3})\s*[—–-]\s*\S")
CAMPO = re.compile(rf"^\s*[-*]\s*({'|'.join(CAMPOS)})\s*:\s*(.*)$")
REF = re.compile(r"\bREF-\d{2,3}\b")
HALLAZGO = re.compile(r"\bH-[A-Z]{2,4}-\d{2,3}\b")
NV = re.compile(r"\bNV-[A-Z]{2,4}-\d{2,3}\b")
BP = re.compile(r"\bBP\s+(\d{1,2})\s*§\s*(\d(?:[\w.]*\w)?)")
NO_NOMBRE = re.compile(r"[^\w ]")   # lo que no admite el nombre de una regla, una interfaz o una constante


def normal(texto: str) -> str:
    """Sin tildes ni mayúsculas, con un espacio entre palabras: así se comparan los títulos."""
    t = unicodedata.normalize("NFKD", texto)
    return " ".join("".join(c for c in t if not unicodedata.combining(c)).lower().split())


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


def apartados(numeradas: list[tuple[int, str]]) -> dict[str, list[tuple[int, str]]]:
    """Las líneas de cada apartado «## …», por su título normalizado."""
    out, actual = {}, None
    for n, l in numeradas:
        if l.startswith("## "):
            actual = normal(l[3:])
            out.setdefault(actual, [])
        elif actual is not None:
            out[actual].append((n, l))
    return out


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


def nombre_citado(s: str, prefijo: str, conocidos: set) -> str | None:
    """El objeto que cita `s` si empieza por el prefijo de la aplicación; None si no cita ninguno. Como en
    comprobar_asis.py de ingeniería inversa: se prueban la cita entera, lo que hay antes de «.», «#», «(» o «[» y lo que
    hay antes de lo primero que no admite el nombre de una regla; vale el primero que se conoce y, si no, el último."""
    s = re.sub(r"^[A-Za-z]+!(\{[^}]*\})?", "", s.strip().strip("'\""))   # rule!X, recordType!{uuid}X
    patron = rf"{re.escape(prefijo)}[_ ]\S"
    if not re.match(patron, s):
        return None
    cortes = [s.rstrip(), re.split(r"[.#(\[]", s, 1)[0].rstrip(), NO_NOMBRE.split(s, 1)[0].rstrip()]
    nombre = next((c for c in cortes if c in conocidos), cortes[-1])
    return nombre if re.match(patron, nombre) else None


def _json(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def en_buenas_practicas(nn: str, x: str, cache: dict) -> bool | None:
    """Si seccion.py de appian-best-practices encuentra §x en el doc nn; None si esa skill no está al lado."""
    if not SECCION.exists():
        return None
    if (nn, x) not in cache:
        r = subprocess.run([sys.executable, str(SECCION), nn, x], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        cache[(nn, x)] = r.returncode == 0
    return cache[(nn, x)]


def fichas(diagnostico: list[tuple[int, str]]) -> dict[str, dict]:
    """Las fichas REF-nn del Diagnóstico: {ref: {"linea": n, campo: (n, valor)}}."""
    out, actual = {}, None
    for n, l in diagnostico:
        plana = l.replace("**", "").strip()
        m = FICHA.match(plana)
        if m:
            actual = out.setdefault(m.group(1), {"linea": n})
            continue
        c = CAMPO.match(plana)
        if c and actual is not None:
            actual.setdefault(c.group(1), (n, c.group(2).strip()))
    return out


def comprobar(p: Path) -> tuple[list[str], list[str]]:
    """(errores, avisos) de <p>/refactorizacion/propuesta.md."""
    p = Path(p).resolve()
    propuesta = p / "refactorizacion" / "propuesta.md"
    asis = p / "as-is"
    datos = asis / "datos"
    inv = json.loads((datos / "inventario.json").read_text(encoding="utf-8"))
    app = inv.get("aplicacion") or {}
    prefijo = app.get("prefijo")
    objetos = inv.get("objetos") or []
    fuera = _json(datos / "dependencias.json").get("fueraDeLaAplicacion") or []
    conocidos = {app.get("nombre")} | {o.get("nombre") for o in objetos} | \
                {t for o in objetos for t in o.get("tambien") or []} | {f.get("nombre") for f in fuera}
    hallazgos = ({h.get("id"): h for h in _json(datos / "hallazgos.json").get("hallazgos", [])}
                 if (datos / "hallazgos.json").exists() else None)
    nvs = ({n.get("id") for n in _json(datos / "sin-verificar.json").get("sinVerificar", [])}
           if (datos / "sin-verificar.json").exists() else None)

    numeradas = lineas(propuesta.read_text(encoding="utf-8"))
    errores: list[tuple[int, str]] = []
    avisos: list[str] = []
    e = lambda n, msg: errores.append((n or 0, msg))  # noqa: E731

    secciones = apartados(numeradas)
    for titulo in APARTADOS:
        if normal(titulo) not in secciones:
            e(None, f"falta el apartado «## {titulo}»")
    diagnostico = secciones.get(normal(APARTADOS[1]), [])
    solucion = "\n".join(l for _, l in secciones.get(normal(APARTADOS[2]), []))
    hoja = "\n".join(l for _, l in secciones.get(normal(APARTADOS[4]), []))
    refs = fichas(diagnostico)
    if normal(APARTADOS[1]) in secciones and not refs:
        e(None, "el Diagnóstico no tiene ninguna ficha «**REF-nn — Problema**»")

    # Cada ficha: sus cinco campos, con evidencia en as-is/ y los valores de las escalas
    for ref, ficha in refs.items():
        for campo in CAMPOS:
            if campo not in ficha or not ficha[campo][1]:
                e(ficha["linea"], f"{ref}: falta «{campo}»")
        if "Evidencia" in ficha:
            n, valor = ficha["Evidencia"]
            en_asis = [d for d in destinos(valor) if (propuesta.parent / d).resolve().is_relative_to(asis)]
            if not en_asis:
                e(n, f"{ref}: la evidencia no enlaza nada de as-is/ (la ficha del anexo o el documento que lo muestra)")
        if "Regla" in ficha and ficha["Regla"][1] and not BP.search(ficha["Regla"][1]):
            e(ficha["Regla"][0], f"{ref}: la Regla no cita la sección de buenas prácticas que lo trata («BP nn §x»)")
        if "Prioridad" in ficha and ficha["Prioridad"][1]:
            valor = re.split(r"[\s,.;:—–-]", ficha["Prioridad"][1], 1)[0]
            if valor not in PRIORIDADES:
                e(ficha["Prioridad"][0], f"{ref}: prioridad «{valor}»; es Alta, Media o Baja")
        if "Esfuerzo" in ficha and ficha["Esfuerzo"][1] and not re.match(r"^[SML]\b", ficha["Esfuerzo"][1]):
            e(ficha["Esfuerzo"][0], f"{ref}: esfuerzo «{ficha['Esfuerzo'][1][:20]}»; es S, M o L")

    # Enlaces, reglas de buenas prácticas e IDs citados, en todo el documento
    cache: dict = {}
    for n, l in numeradas:
        for d in destinos(l):
            destino = (propuesta.parent / d).resolve()
            if destino.is_relative_to(asis) and destino.relative_to(asis).parts[:1] == ("extraccion",):
                e(n, f"enlaza la extracción en bruto de ingeniería inversa ({d}): enlaza su ficha del anexo o el "
                     "documento de as-is/ que lo muestra")
            elif not destino.exists():
                e(n, f"enlace a {d}, que no existe")
        for m in BP.finditer(l):
            nn, x = m.group(1).zfill(2), m.group(2)
            encontrada = en_buenas_practicas(nn, x, cache)
            if encontrada is False:
                e(n, f"«BP {nn} §{x}» no está en appian-best-practices (seccion.py {nn} {x} no la encuentra)")
            elif encontrada is None and ("sin-seccion", nn) not in cache:
                cache[("sin-seccion", nn)] = True
                avisos.append(f"«BP {nn} §…» sin comprobar: no está appian-best-practices junto a esta skill")
        for ref in REF.findall(l):
            if ref not in refs:
                e(n, f"cita {ref}, que no está en el Diagnóstico")
        for h in HALLAZGO.findall(l) if hallazgos is not None else []:
            if h not in hallazgos:
                e(n, f"cita {h}, que no está en as-is/datos/hallazgos.json")
        for nv in NV.findall(l) if nvs is not None else []:
            if nv not in nvs:
                e(n, f"cita {nv}, que no está en as-is/datos/sin-verificar.json")

    # En el Diagnóstico, solo objetos que existen (la Solución puede proponer nuevos)
    for n, l in diagnostico if prefijo else []:
        for m in CODIGO.finditer(l):
            nombre = nombre_citado(m.group(1), prefijo, conocidos)
            if nombre and nombre not in conocidos:
                e(n, f"Diagnóstico: `{nombre}` no es un objeto del inventario (as-is/datos/inventario.json) ni se cita "
                     "con uno; el Diagnóstico solo afirma lo que está en as-is/")

    # Cada REF tiene su alternativa en la Solución y su fase en la Hoja de ruta
    for ref, ficha in refs.items():
        patron = rf"\b{re.escape(ref)}\b"
        if not re.search(patron, solucion):
            e(ficha["linea"], f"{ref} no aparece en la Solución: cada problema del Diagnóstico tiene su alternativa")
        en_hoja = re.search(patron, hoja)
        if not en_hoja:
            avisos.append(f"{ref} no está en la Hoja de ruta")
        evidencia = ficha.get("Evidencia", (0, ""))[1]
        for h in HALLAZGO.findall(evidencia):
            certeza = ((hallazgos or {}).get(h) or {}).get("certeza")
            if certeza in ("inferido", "pendiente"):
                verificar = re.search(rf"Verificar\s+\[?{re.escape(h)}\b", hoja)
                if not verificar or (en_hoja and verificar.start() > en_hoja.start()):
                    avisos.append(f"{ref} se apoya en {h} ({certeza}) y la Hoja de ruta no pone antes «Verificar {h}»")
    return [f"propuesta.md:{n}: {msg}" if n else f"propuesta.md: {msg}"
            for n, msg in sorted(errores, key=lambda x: x[0])], avisos


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__, file=sys.stderr)
        return 2
    p = Path(argv[0]).resolve()
    for falta, quien in ((p / "refactorizacion" / "propuesta.md", "esta skill"),
                         (p / "as-is" / "datos" / "inventario.json", "appian-reverse-engineering, build_datos.py")):
        if not falta.exists():
            print(f"ERROR: falta {falta} (lo escribe {quien})", file=sys.stderr)
            return 2
    errores, avisos = comprobar(p)
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
