#!/usr/bin/env python3
"""comprobar_asis.py - Comprueba la documentación de ingeniería inversa antes de entregarla.

Uso:
  python3 <skill>/scripts/comprobar_asis.py <carpeta_salida>

Lee los .md de <salida>, <salida>/datos/ (build_datos.py) y, de <trabajo>, summary.json (build_summary.py),
inventory.json (build_model.py) y las preguntas de la revisión (output_preferences.json).

Errores (✗, salida 1):
  - un nombre entre comillas invertidas que empieza por el prefijo de la aplicación (seguido de «_» o espacio; se
    corta en «.», «#», «(» o «[» y, si así no es un objeto, en lo que no admite el nombre de una regla, una interfaz
    o una constante, como en una expresión SAIL) y no es un objeto del inventario, algo que se cita con uno ni la
    aplicación; fuera del código, en texto plano, en negrita o como texto de un enlace, igual con <prefijo>_<palabra>
    (sin contar rutas ni el slug de la ficha de un objeto);
  - una tabla con columna «Certeza» sin columna «Evidencia» (salvo el registro de 09, cuyas filas enlazan en «Dónde»
    al documento que tiene la evidencia), una fila cuya evidencia no enlaza a un fichero del anexo o una certeza que
    no es ✅, 🔶 ni ❓;
  - una evidencia «mcp:<tipo>/<nombre>» que enlaza una ficha del anexo que no es la de ese objeto (inventario.json →
    anexo), también anexo/indice.md;
  - cifras del volumen de LEEME («N objetos», «N process models», «N interfaces», «N record types») distintas de las
    de summary.json; se comparan solo en la línea «Volumen» (sin ella, en todo LEEME): una cifra en otra línea o en
    otro documento no se mira;
  - un «{{» sin sustituir o un enlace relativo a un fichero que no existe;
  - un NV-<ÁREA>-NN citado que no está en datos/sin-verificar.json, o un H-<ÁREA>-NN que no está en
    datos/hallazgos.json (el registro de 09, que escribe build_registry.py, no se mira);
  - una pregunta de la revisión que no está en la tabla «Preguntas de esta revisión» de LEEME, o está sin estado
    (Respondida, Parcial o Sin resolver), Respondida sin enlace ni NV, o Parcial o Sin resolver sin NV ni enlace a
    «Qué no incluye».
  Las tablas, las evidencias, los «{{», los H y los NV no se miran en anexo/ ni en extraccion/ (una lista anidada de
  SAIL lleva «{{»).
Avisos (·): la aplicación sin prefijo (no se comprueban los nombres); «no existe», «no existen» o «no hay ningún» en
un documento (lo que no se encontró dice dónde se buscó); una línea que enlaza los hallazgos de otro documento
(«04-seguridad-grupos.md#hallazgos») sin citar un H-… o un NV-… (heurístico: la pasada de coherencia cita el ID
canónico); «según su nombre» en una fila de INVENTARIO cuyo objeto tiene definición; un hallazgo inferido de severidad
Alta con menos de dos evidencias en «base»; un objeto de fuera de la aplicación que esta usa y que ningún NV tiene en
«objetos»; y, con redaccion.py del analista, muletillas, frases de más de 35 palabras, párrafos de 20 palabras o más
repetidos en dos documentos y documentos por encima de su presupuesto (assets/presupuesto-palabras.json), que cuenta
palabras(): sin títulos ni lo que escriben los scripts entre sus marcadores (el registro de 09 y la tabla «Sin
verificar» de LEEME).
Salida: 0 sin errores, 1 con errores, 2 uso o faltan datos/inventario.json o summary.json.
"""
from __future__ import annotations

import fnmatch
import json
import re
import sys
sys.dont_write_bytecode = True  # sin __pycache__ en el plugin: no se escribe fuera del proyecto
import unicodedata
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
GENERADOS = (REGISTRO, ("<!-- sin-verificar:inicio -->", "<!-- sin-verificar:fin -->"))   # lo escriben los scripts
CERTEZAS = ("✅", "🔶", "❓")
NO_NOMBRE = re.compile(r"[^\w ]")   # lo que no admite el nombre de una regla, una interfaz o una constante
CODIGO = re.compile(r"`([^`\n]+)`")
ENLACE = re.compile(r"!?\[[^\]\n]*\]\((<[^>\n]+>|[^)\s]+)(?:\s+\"[^\"\n]*\")?\)")
CIFRA = re.compile(r"(\d[\d.]*)\s+(objetos|process models?|interfa(?:ces|z)|record types?)\b", re.I)
NV = re.compile(r"\bNV-[A-Z]{2,4}-\d{2,3}\b")
HALLAZGO = re.compile(r"\bH-[A-Z]{2,4}-\d{2,3}\b")
# [`mcp:<tipo>/<nombre>#…`](destino): el nombre, como lo lee evidencia.py de la evaluación del recién llegado
EVIDENCIA = re.compile(r"\[\s*`?mcp:[^/`\]]+/([^#@`\]]+)[^\]]*\]\((<[^>\n]+>|[^)\s]+)")
NEGATIVO = re.compile(r"(?i)(?<!\w)no (?:existen?|hay ning[uú]n[oa]?)(?!\w)")   # sin decir dónde se buscó
ESTADOS = {"respondida": "Respondida", "parcial": "Parcial", "sin resolver": "Sin resolver"}


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


def nombre_citado(s: str, prefijo: str, conocidos: set) -> str | None:
    """El objeto que cita `s` si empieza por el prefijo de la aplicación; None si no cita ninguno. Se prueban la cita
    entera, lo que hay antes de «.», «#», «(» o «[» (un campo, un ancla, una llamada o un índice) y lo que hay antes de
    lo primero que no admite el nombre de una regla, una interfaz o una constante, que es como se lee una expresión
    SAIL (`cons!X & "/ruta"`). Vale el primero de `conocidos`, porque otros objetos sí admiten esos caracteres (una Web
    API, un grupo con «&»); si no hay ninguno, el último. Un patrón que solo es el prefijo («DEM_*») no cita nada."""
    s = re.sub(r"^[A-Za-z]+!(\{[^}]*\})?", "", s.strip().strip("'\""))   # rule!X, recordType!{uuid}X
    patron = rf"{re.escape(prefijo)}[_ ]\S"
    if not re.match(patron, s):
        return None
    cortes = [s.rstrip(), re.split(r"[.#(\[]", s, maxsplit=1)[0].rstrip(), NO_NOMBRE.split(s, 1)[0].rstrip()]
    nombre = next((c for c in cortes if c in conocidos), cortes[-1])
    return nombre if re.match(patron, nombre) else None


def generadas(texto: str) -> set[int]:
    """Los números de las líneas que escriben los scripts entre sus marcadores: el registro de 09 (build_registry.py)
    y la tabla «Sin verificar» de LEEME (build_datos.py)."""
    out, fin = set(), None
    for n, l in enumerate(texto.splitlines(), 1):
        if fin is None:
            fin = next((f for i, f in GENERADOS if i in l), None)
        elif fin in l:
            fin = None
        else:
            out.add(n)
    return out


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


def _json(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def normal(texto: str) -> str:
    """Sin tildes, mayúsculas, negritas ni código, con un espacio entre palabras: así se comparan los textos."""
    t = unicodedata.normalize("NFKD", texto.replace("*", "").replace("`", ""))
    return " ".join("".join(c for c in t if not unicodedata.combining(c)).lower().split())


def pregunta_normal(texto: str) -> str:
    return re.sub(r"[¿?¡!.:]", "", normal(texto)).strip()


def enlaza_que_no_incluye(texto: str) -> bool:
    """Si el texto enlaza la sección «Qué no incluye» de LEEME (#qué-no-incluye, con o sin tilde)."""
    return any("#" in m.group(1) and normal(unquote(m.group(1).split("#", 1)[1])) == "que-no-incluye"
               for m in ENLACE.finditer(texto))


def comprobar(salida: Path) -> tuple[list[str], list[str]]:
    """(errores, avisos) de la documentación de <salida>."""
    salida = Path(salida).resolve()
    inv = json.loads((salida / "datos" / "inventario.json").read_text(encoding="utf-8"))
    resumen = json.loads((work_dir(salida) / "summary.json").read_text(encoding="utf-8"))
    app = inv.get("aplicacion") or {}
    prefijo = app.get("prefijo")
    conocidos = {app.get("nombre")} | {o.get("nombre") for o in inv.get("objetos", [])} | \
                {t for o in inv.get("objetos", []) for t in o.get("tambien", [])} | \
                {f.get("nombre") for f in _json(salida / "datos" / "dependencias.json").get("fueraDeLaAplicacion", [])}
    nvs = {n.get("id") for n in _json(salida / "datos" / "sin-verificar.json").get("sinVerificar", [])}
    hallazgos = {h.get("id") for h in _json(salida / "datos" / "hallazgos.json").get("hallazgos", [])}
    ficha = {o.get("nombre"): o.get("anexo") for o in inv.get("objetos", []) if o.get("anexo")}
    en_prosa = re.compile(rf"(?<![\w!/]){re.escape(prefijo)}_\w+") if prefijo else None
    con_slug = conocidos | {Path(f).stem for f in ficha.values()}   # en la prosa, también el slug de una ficha
    detalle: dict[str, set] = {}
    for lista in (_json(work_dir(salida) / "inventory.json").get("objects") or {}).values():
        for o in lista:
            detalle.setdefault(o.get("name"), set()).add(o.get("detail"))
    anexo = salida / "anexo"
    errores: list[tuple] = []
    avisos: list[tuple] = []
    if not prefijo:
        avisos.append(("datos/inventario.json", None, "la aplicación no tiene prefijo: no se comprueba que los nombres "
                                                      "citados sean objetos del inventario"))
    textos: dict[str, str] = {}
    for doc in sorted(salida.rglob("*.md")):
        rel = doc.relative_to(salida).as_posix()
        texto = doc.read_text(encoding="utf-8")
        numeradas = lineas(texto)
        con_tablas = rel.split("/", 1)[0] not in SIN_TABLAS
        e = lambda n, msg: errores.append((rel, n, msg))  # noqa: E731
        # nombres que empiezan por el prefijo: en el código y, en los entregables, también fuera de él
        for n, l in numeradas if prefijo else []:
            for m in CODIGO.finditer(l):
                nombre = nombre_citado(m.group(1), prefijo, conocidos)
                if nombre and nombre not in conocidos:
                    e(n, f"`{nombre}` no es un objeto del inventario ni se cita con uno")
        for n, l in numeradas if prefijo and con_tablas else []:
            linea_prosa = prosa(l)
            for conocido in sorted((x for x in con_slug if x), key=len, reverse=True):
                linea_prosa = re.sub(rf"(?<![\w!/]){re.escape(conocido)}(?!\w)", " ", linea_prosa)
            for m in en_prosa.finditer(linea_prosa):
                nombre = nombre_citado(m.group(0), prefijo, con_slug)
                if nombre and nombre not in con_slug:
                    e(n, f"`{nombre}` no es un objeto del inventario ni se cita con uno")
        if con_tablas:
            # certeza y evidencia (el registro de 09, que escribe un script, enlaza en «Dónde» al documento que la tiene)
            generado = generadas(texto)
            for n, cab, filas in tablas(numeradas):
                cols = [c.replace("*", "").lower() for c in cab]
                cert = next((k for k, c in enumerate(cols) if c.startswith("certeza")), None)
                evid = next((k for k, c in enumerate(cols) if c.startswith("evidencia")), None)
                if cert is not None and evid is None and n not in generado:
                    e(n, "tabla con «Certeza» sin «Evidencia»")
                for fn, fila in filas:
                    if cert is not None and cert < len(fila) and not fila[cert].startswith(CERTEZAS):
                        e(fn, f"certeza «{fila[cert]}»: es ✅, 🔶 o ❓")
                    if evid is not None and not any(
                            anexo in (doc.parent / d).resolve().parents and (doc.parent / d).resolve().is_file()
                            for d in destinos(fila[evid] if evid < len(fila) else "")):
                        e(fn, "la evidencia no enlaza a una ficha del anexo")
                    if rel == "INVENTARIO.md":
                        segun_su_nombre(fn, fila, detalle, avisos)
            for n, l in numeradas:
                # marcadores sin sustituir
                if "{{" in CODIGO.sub("", l) or any(re.search(r"\{\{[^{}]*\}\}", c) for c in CODIGO.findall(l)):
                    e(n, "«{{» sin sustituir")
                # lo que no se pudo verificar se cita por su NV, que está en datos/
                for m in NV.finditer(l):
                    if m.group(0) not in nvs:
                        e(n, f"{m.group(0)} no está en datos/sin-verificar.json")
                # una evidencia lleva a la ficha de su objeto
                for nombre, destino in evidencias_de_otro(doc, l, anexo, ficha, salida):
                    e(n, f"la evidencia de «{nombre}» enlaza {destino}, que no es su ficha ({ficha[nombre]})")
                if n not in generado:   # el registro de 09 lo escribe build_registry.py
                    # un hallazgo se cita por su ID, que está en datos/
                    for m in HALLAZGO.finditer(l):
                        if m.group(0) not in hallazgos:
                            e(n, f"{m.group(0)} no está en datos/hallazgos.json")
                    # una mención a los hallazgos de otra área lleva su ID (T21)
                    otro = hallazgos_de_otro(doc, l)
                    if otro and not (HALLAZGO.search(l) or NV.search(l)):
                        avisos.append((rel, n, f"enlaza los hallazgos de {otro} sin citar su ID (H-… o NV-…)"))
                # lo que no se encontró dice dónde se buscó
                for m in NEGATIVO.finditer(prosa(l)):
                    avisos.append((rel, n, f"«{m.group(0)}»: di dónde se buscó («no encontrado en <ámbito>»)"))
        # enlaces rotos
        for n, l in numeradas:
            for d in destinos(l):
                if not (doc.parent / d).exists():
                    e(n, f"enlace a {d}, que no existe")
        if con_tablas:
            textos[rel] = texto
    cifras(salida, resumen, errores)
    preguntas(salida, _json(work_dir(salida) / "output_preferences.json").get("preguntas") or [], errores)
    datos_sin_respaldo(salida, avisos)
    redaccion(salida, textos, resumen.get("counts") or {}, avisos)
    orden = lambda x: (x[0], x[1] or 0)  # noqa: E731
    return ([f"{r}:{n} {m}" if n else f"{r}: {m}" for r, n, m in sorted(errores, key=orden)],
            [f"{r}:{n} {m}" if n else f"{r}: {m}" for r, n, m in sorted(avisos, key=orden)])


def evidencias_de_otro(doc: Path, linea: str, anexo: Path, ficha: dict, salida: Path) -> list[tuple[str, str]]:
    """(nombre, destino) de cada evidencia «mcp:<tipo>/<nombre>» de la línea que enlaza una ficha del anexo que no es
    la de ese objeto (`ficha`: su anexo en inventario.json). Un destino que no es un fichero del anexo lo dicen las
    comprobaciones de la evidencia y de los enlaces; un nombre sin ficha (la aplicación, uno de fuera), nada."""
    out = []
    for m in EVIDENCIA.finditer(linea):
        nombre = m.group(1).strip()
        destino = (doc.parent / unquote(m.group(2).strip("<>").split("#", 1)[0])).resolve()
        if nombre in ficha and anexo in destino.parents and destino.is_file() \
                and destino != (salida / ficha[nombre]).resolve():
            out.append((nombre, destino.relative_to(salida).as_posix()))
    return out


def hallazgos_de_otro(doc: Path, linea: str) -> str | None:
    """El documento de otra área cuyos hallazgos («…md#hallazgos») enlaza la línea, o None."""
    for m in ENLACE.finditer(CODIGO.sub("x", linea)):
        d = m.group(1).strip("<>")
        if re.match(r"^[a-z][a-z0-9+.-]*:", d, re.I) or "#" not in d:
            continue
        fichero, ancla = d.split("#", 1)
        if ancla.lower() == "hallazgos" and fichero and (doc.parent / unquote(fichero)).resolve() != doc.resolve():
            return Path(unquote(fichero)).name
    return None


def palabras(texto: str) -> int:
    """Las palabras de un documento como las cuenta su presupuesto: fuera de los bloques de código y de los
    comentarios, sin los títulos ni lo que escriben los scripts entre sus marcadores (generadas), sin los destinos de
    los enlaces y con cada código en línea como una palabra. La usa también palabras.py de la evaluación del recién
    llegado."""
    generado = generadas(texto)
    return sum(len(re.findall(r"\w+", prosa(l))) for n, l in lineas(texto)
               if n not in generado and not l.lstrip().startswith("#"))


def segun_su_nombre(n: int, fila: list[str], detalle: dict, avisos: list) -> None:
    """«Según su nombre» solo vale para un objeto sin definición: si la tiene, su «Para qué» sale de ella."""
    if "segun su nombre" not in normal(" ".join(fila)):
        return
    m = CODIGO.search(fila[0] if fila else "")
    if m and detalle.get(m.group(1)) == {"full"}:
        avisos.append(("INVENTARIO.md", n, f"«según su nombre» en `{m.group(1)}`, que tiene definición: su «Para qué» "
                                           "sale de ella (🔶)"))


def cifras(salida: Path, resumen: dict, errores: list) -> None:
    """Las cifras del volumen de LEEME («N objetos», «N process models»…), iguales a las de summary.json."""
    leeme = salida / "LEEME.md"
    if not leeme.exists():
        return
    numeradas = lineas(leeme.read_text(encoding="utf-8"))
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
                errores.append(("LEEME.md", n, f"«{m.group(0)}»: summary.json dice {esperado[clave]}"))


def preguntas_de_leeme(salida: Path) -> list[tuple[int, str, str, str]]:
    """(línea, pregunta, estado, dónde) de cada fila de la tabla «Preguntas de esta revisión» de LEEME."""
    leeme = salida / "LEEME.md"
    if not leeme.exists():
        return []
    seccion, dentro = [], False
    for n, l in lineas(leeme.read_text(encoding="utf-8")):
        if l.startswith("#"):
            dentro = normal(l.lstrip("#")) == "preguntas de esta revision"
        elif dentro:
            seccion.append((n, l))
    for _, cab, filas in tablas(seccion):
        cols = [normal(c) for c in cab]
        col = {k: next((i for i, c in enumerate(cols) if c.startswith(k)), None) for k in ("pregunta", "estado", "donde")}
        if col["pregunta"] is None or col["estado"] is None:
            continue

        def celda(fila: list[str], k: str) -> str:
            return fila[col[k]] if col[k] is not None and col[k] < len(fila) else ""
        return [(n, celda(f, "pregunta"), celda(f, "estado"), celda(f, "donde") if col["donde"] is not None
                 else " | ".join(f)) for n, f in filas]
    return []


def preguntas(salida: Path, lista: list[str], errores: list) -> None:
    """Cada pregunta de la revisión (output_preferences.json) está cerrada en LEEME: con su estado y, si no se
    respondió del todo, con su NV o con el enlace a «Qué no incluye» (una limitación global)."""
    filas = {pregunta_normal(p): (n, estado, donde) for n, p, estado, donde in preguntas_de_leeme(salida)} if lista else {}
    for p in lista:
        n, estado, donde = filas.get(pregunta_normal(p), (None, "", ""))
        e = lambda msg: errores.append(("LEEME.md", n, f"«{p}» {msg}"))  # noqa: E731
        if n is None:
            e("no está en «Preguntas de esta revisión»")
        elif normal(estado) not in ESTADOS:
            e("sin estado: Respondida, Parcial o Sin resolver")
        elif normal(estado) == "respondida":
            if not ENLACE.search(donde) and not NV.search(donde):
                e("Respondida sin enlace al documento que la responde")
        elif not NV.search(donde) and not enlaza_que_no_incluye(donde):
            e(f"{ESTADOS[normal(estado)]} sin NV ni enlace a «Qué no incluye»")


def datos_sin_respaldo(salida: Path, avisos: list) -> None:
    """Hallazgos inferidos de severidad Alta con menos de dos evidencias en «base», y objetos de fuera de la
    aplicación que esta usa sin un NV que los tenga en «objetos» (los que solo la usan no tienen nada sin verificar)."""
    for h in _json(salida / "datos" / "hallazgos.json").get("hallazgos", []):
        n = len(h.get("base") or [])
        if h.get("certeza") == "inferido" and h.get("severidad") == "Alta" and n < 2:
            avisos.append(("datos/hallazgos.json", None, f"{h.get('id')}: inferido de severidad Alta con {n} "
                                                          "evidencias en «base»: hacen falta dos"))
    for f in _json(salida / "datos" / "dependencias.json").get("fueraDeLaAplicacion", []):
        if f.get("usadoPor") and not f.get("nv"):
            avisos.append(("datos/dependencias.json", None, f"`{f.get('nombre')}` no está en la aplicación y lo usa "
                                                             f"{', '.join(f['usadoPor'])}: falta el NV que lo tenga en "
                                                             "«objetos»"))


def prosa(l: str) -> str:
    """La línea como se lee: cada código en línea, una palabra (así, una frase que empieza por un nombre no se suma
    a la anterior), y sin los destinos de los enlaces."""
    return re.sub(r"\]\([^)]*\)", "]", CODIGO.sub("X", l))


def redaccion(salida: Path, textos: dict[str, str], cuentas: dict, avisos: list) -> None:
    """Avisos de redacción de cada documento (`textos`: {ruta: texto tal cual}). El presupuesto cuenta palabras(), sin lo
    que escriben los scripts entre sus marcadores: cada hallazgo o NV que se registra lo haría crecer."""
    if rd is None:
        avisos.append(("redaccion", None, "sin avisos de redacción: no está appian-functional-analyst/scripts/redaccion.py"))
        return
    muletillas = rd.muletillas()
    presupuesto = json.loads(PRESUPUESTO.read_text(encoding="utf-8")).get("documentos", {})
    for rel, texto in textos.items():
        for n, l in lineas(texto):
            if l.lstrip().startswith("#"):
                continue
            leida = prosa(l)
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
            cuenta = palabras(texto)
            if cuenta > limite:
                avisos.append((rel, None, f"{cuenta} palabras, más que su presupuesto ({limite})"))
    for p, nombres in rd.parrafos_repetidos({r: re.sub(r"<!--.*?-->", "", t, flags=re.S) for r, t in textos.items()}):
        avisos.append((nombres[0], None, f"párrafo repetido en {' y '.join(nombres)}: «{p[:60]}…»"))


def main(argv: list[str]) -> int:
    if argv in (["--help"], ["-h"]):
        print(__doc__)
        return 0
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
