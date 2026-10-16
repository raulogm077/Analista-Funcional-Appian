#!/usr/bin/env python3
"""El DF del cliente en Word, sobre la plantilla: lee analisis/df-cliente.md y rellena la plantilla del documento de
diseño funcional (portada, control de cambios, introducción, flujo y reglas comunes, actividades, pantallas por área,
roles y permisos, notificaciones, KPIs y periodo de estabilización). El formato de df-cliente.md, en
references/df-cliente-plantilla.md.

Uso:
  python3 df_cliente_docx.py <proyecto> [-o salida.docx] [--plantilla fichero.docx] [--pdf]

Plantilla, la primera que exista:
  1. --plantilla <fichero.docx>
  2. <proyecto>/plantillas/df-cliente.docx      la del cliente (logos, colores y pie del cliente)
  3. assets/plantillas/df-cliente.docx de esta skill, neutra; si el proyecto tiene prototipo/brand-<id>.json, su color
     (site.backgroundColor) sustituye al azul de la neutra.
Una plantilla del cliente tiene que ser una copia de la neutra a la que solo se le cambian logos, colores, tipos de letra
y pie: el script reconoce sus piezas por el texto de ejemplo («[CÓDIGO DEL DOCUMENTO]», «IDENTIFICADOR_NOMBRE TAREA»…).

El DF del cliente solo lleva lo que lee el cliente: sus fuentes (df-cliente-fuentes.md) y sus preguntas
(df-cliente-pendientes.md) están aparte y no salen. Si quedara un comentario <!-- … --> o algo tachado (~~…~~), tampoco
sale. «pendiente de confirmar» sale resaltado en amarillo. Avisa de lo que queda pendiente, de las actividades y
pantallas incompletas y de los textos de ejemplo de la plantilla («[…]») que quedan sin rellenar.

Salida: <proyecto>/entregables/DF-cliente-<proceso>-v<versión>.docx (el nombre que espera proyecto.py entregar
--df-cliente); no sobrescribe un Word entregado (los que nombra proyecto.md). --pdf lo convierte con LibreOffice a
<proyecto>/entregables/revision/, si está instalado.

Requiere python-docx (python3 -m pip install python-docx).
"""
from __future__ import annotations

import copy
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import zipfile
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
NEUTRA = SKILL / "assets" / "plantillas" / "df-cliente.docx"
COLORES_NEUTRA = ("1F3864", "2F5597")

try:
    import docx
    from docx.oxml.ns import qn
    from docx.shared import Emu
    from docx.text.paragraph import Paragraph
except ImportError:  # pragma: no cover
    docx = None

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
avisos: list[str] = []


# ---------------------------------------------------------------- utilidades de texto

def norm(s: str) -> str:
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s).strip().lower()


def limpiar(md: str) -> list[str]:
    """Quita lo que no ve el cliente: comentarios, filas y viñetas tachadas, fichas anuladas."""
    md = re.sub(r"<!--.*?-->", "", md, flags=re.S)
    res, saltar = [], False
    for linea in md.splitlines():
        if re.match(r"^#{2,5}\s+~~", linea):           # ficha anulada: hasta el siguiente título
            saltar = True
            continue
        if saltar and re.match(r"^#{1,5}\s", linea):
            saltar = False
        if saltar:
            continue
        if re.match(r"^\s*\|\s*~~", linea) or re.match(r"^\s*([-*]|\d+[.)])\s+~~", linea):
            continue
        res.append(linea.rstrip())
    return res


def celdas(linea: str) -> list[str]:
    return [c.strip() for c in linea.strip().strip("|").split("|")]


def es_separador(linea: str) -> bool:
    return bool(re.match(r"^\s*\|?[\s:|-]+\|?\s*$", linea)) and "-" in linea


# ---------------------------------------------------------------- Markdown → bloques

LISTA = re.compile(r"^(\s*)([-*]|\d+[.)])\s+(.*)$")
IMAGEN = re.compile(r"^!\[([^\]]*)\]\(([^)]+)\)\s*$")


def bloques(lineas: list[str]) -> list[tuple]:
    """('p', texto) · ('lista', ordenada, [(nivel, texto)]) · ('tabla', filas) · ('img', pie, ruta) · ('nota', texto)."""
    res, i = [], 0
    while i < len(lineas):
        l = lineas[i]
        if not l.strip():
            i += 1
            continue
        m = IMAGEN.match(l.strip())
        if m:
            res.append(("img", m.group(1), m.group(2)))
            i += 1
            continue
        if l.lstrip().startswith("|"):
            filas = []
            while i < len(lineas) and lineas[i].lstrip().startswith("|"):
                if not es_separador(lineas[i]):
                    filas.append(celdas(lineas[i]))
                i += 1
            res.append(("tabla", filas))
            continue
        if LISTA.match(l):
            items, ordenada = [], bool(re.match(r"\d", LISTA.match(l).group(2)))
            while i < len(lineas) and lineas[i].strip():
                m = LISTA.match(lineas[i])
                if m:
                    sang = len(m.group(1).replace("\t", "    "))
                    nivel = 0 if sang < 2 else (1 if sang < 5 else 2)
                    items.append([nivel, m.group(3).strip()])
                elif items and lineas[i].startswith((" ", "\t")):
                    items[-1][1] += " " + lineas[i].strip()
                else:
                    break
                i += 1
            res.append(("lista", ordenada, items))
            continue
        if l.startswith(">") or l.startswith("\\*") or re.match(r"^\*[^*]", l) and not l.rstrip().endswith("*"):
            res.append(("nota", l.lstrip(">").strip().replace("\\*", "*")))
            i += 1
            continue
        texto = [l.strip()]
        i += 1
        while i < len(lineas) and lineas[i].strip() and not (
                lineas[i].lstrip().startswith(("|", "#", ">")) or LISTA.match(lineas[i]) or IMAGEN.match(lineas[i].strip())):
            texto.append(lineas[i].strip())
            i += 1
        res.append(("p", " ".join(texto)))
    return res


def secciones(lineas: list[str]):
    """Árbol de títulos: [(nivel, título, líneas propias, hijos)]."""
    raiz = (0, "", [], [])
    pila = [raiz]
    for l in lineas:
        m = re.match(r"^(#{1,6})\s+(.*)$", l)
        if m:
            nodo = (len(m.group(1)), m.group(2).strip(), [], [])
            while pila[-1][0] >= nodo[0]:
                pila.pop()
            pila[-1][3].append(nodo)
            pila.append(nodo)
        else:
            pila[-1][2].append(l)
    return raiz


def buscar(nodo, patron: str):
    """El primer descendiente cuyo título empieza por el patrón (sin acentos ni mayúsculas)."""
    for h in nodo[3]:
        if norm(h[1]).startswith(norm(patron)):
            return h
        r = buscar(h, patron)
        if r:
            return r
    return None


def todo(nodo) -> list[str]:
    """Las líneas del nodo y de sus hijos, con sus títulos."""
    res = list(nodo[2])
    for h in nodo[3]:
        res.append("#" * h[0] + " " + h[1])
        res += todo(h)
    return res


# ---------------------------------------------------------------- piezas de la plantilla

def texto_de(el) -> str:
    return "".join(t.text or "" for t in el.iter(qn("w:t")))


def rpr_base(el, conservar=False):
    """El formato del primer run, sin el de los textos de ejemplo (cursiva gris) salvo que se conserve."""
    r = el.find(".//" + qn("w:r"))
    rpr = r.find(qn("w:rPr")) if r is not None else None
    rpr = copy.deepcopy(rpr) if rpr is not None else None
    if rpr is not None and not conservar:
        for tag in ("w:i", "w:iCs", "w:lang"):
            for x in rpr.findall(qn(tag)):
                rpr.remove(x)
        for c in rpr.findall(qn("w:color")):
            if c.get(qn("w:val"), "").upper() in ("8A9096",):
                rpr.remove(c)
    return rpr


INLINE = re.compile(r"(\*\*.+?\*\*|(?<![\w*])\*[^*\s][^*]*?\*(?![\w*])|pendiente de confirmar[^.;)]*)", re.I)


def poner_texto(p, texto: str, rpr=None, conservar=False, negrita=False):
    """Sustituye los runs del párrafo por el texto, con **negrita**, *cursiva* y «pendiente de confirmar» resaltado."""
    if rpr is None:
        rpr = rpr_base(p, conservar)
    for hijo in list(p):
        if hijo.tag != qn("w:pPr"):
            p.remove(hijo)
    for trozo in INLINE.split(texto or ""):
        if not trozo:
            continue
        r = p.makeelement(qn("w:r"), {})
        pr = copy.deepcopy(rpr) if rpr is not None else r.makeelement(qn("w:rPr"), {})
        if trozo.startswith("**") and trozo.endswith("**") and len(trozo) > 4:
            trozo = trozo[2:-2]
            pr.append(pr.makeelement(qn("w:b"), {}))
        elif trozo.startswith("*") and trozo.endswith("*") and len(trozo) > 2:
            trozo = trozo[1:-1]
            pr.append(pr.makeelement(qn("w:i"), {}))
        elif trozo.lower().startswith("pendiente de confirmar"):
            pr.append(pr.makeelement(qn("w:highlight"), {qn("w:val"): "yellow"}))
        if negrita and pr.find(qn("w:b")) is None:
            pr.append(pr.makeelement(qn("w:b"), {}))
        if len(pr):
            r.append(pr)
        t = r.makeelement(qn("w:t"), {})
        t.text = trozo
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        r.append(t)
        p.append(r)
    return p


def poner_celda(tc, texto: str, conservar=False, negrita=False):
    """Rellena una celda. «<br>» separa párrafos; un trozo que empieza por «- » sale con viñeta «•»."""
    ps = tc.findall(qn("w:p"))
    base = ps[0]
    rpr = rpr_base(base, conservar)
    for p in ps[1:]:
        tc.remove(p)
    trozos = [t.strip() for t in re.split(r"<br\s*/?>", texto or "")] or [""]
    for k, trozo in enumerate(trozos):
        p = base if k == 0 else copy.deepcopy(base)
        if trozo.startswith("- "):
            trozo = "• " + trozo[2:]
        poner_texto(p, trozo, rpr, negrita=negrita)
        if k:
            tc.append(p)


class Plantilla:
    def __init__(self, ruta: Path):
        self.d = docx.Document(str(ruta))
        self.body = self.d.element.body
        els = list(self.body.iterchildren())
        self.final = els[-1] if els[-1].tag == qn("w:sectPr") else None
        p = lambda cond: next((e for e in els if e.tag == qn("w:p") and cond(texto_de(e).strip(), e)), None)
        t = lambda cond: next((e for e in els if e.tag == qn("w:tbl") and cond(texto_de(e).strip(), e)), None)
        lista = lambda e: e.find(".//" + qn("w:numPr")) is not None
        self.P = {
            "h1": p(lambda x, e: re.match(r"^1\.\s+INTRODUC", x, re.I)),
            "h2": p(lambda x, e: re.match(r"^1\.1\s", x)),
            "h3": p(lambda x, e: re.match(r"^2\.3\.1\s", x)),
            "h3pb": p(lambda x, e: re.match(r"^2\.3\.[2-9]\s", x)),
            "h4": p(lambda x, e: re.match(r"^2\.3\.1\.1\s", x)),
            "h4pb": p(lambda x, e: re.match(r"^2\.3\.1\.2\s", x)),
            "h26": p(lambda x, e: re.match(r"^2\.6\s", x)),
            "h3b": p(lambda x, e: re.match(r"^2\.4\.1\s", x)),
            "h3bpb": p(lambda x, e: re.match(r"^2\.4\.2\s", x)),
            "h2pb": p(lambda x, e: re.match(r"^2\.5\s", x)),
            "barra": p(lambda x, e: norm(x) == "descripcion del proceso"),
            "sub": p(lambda x, e: norm(x) == "logica general del flujo"),
            "txt": p(lambda x, e: x.startswith("[Descripción del proceso")),
            "vineta": p(lambda x, e: lista(e) and x.startswith("[Integración 1]")),
            "n0": p(lambda x, e: lista(e) and x.startswith("La pantalla [")),
            "n1": p(lambda x, e: lista(e) and x.startswith("La tabla incluye paginación")),
            "n2": p(lambda x, e: lista(e) and x.startswith("Tipo de control: [campo")),
            "pie": p(lambda x, e: x.startswith("Flujo del proceso [")),
            "nota": p(lambda x, e: x.startswith("La visibilidad de campos")),
            "aclaracion": p(lambda x, e: x.startswith("*[Aclaraciones")),
            "leyenda": p(lambda x, e: x.startswith("Leyenda:")),
            "desc_general": p(lambda x, e: norm(x) == "descripcion general"),
            "ejemplos": p(lambda x, e: norm(x).startswith("ejemplos visuales")),
            "salto": p(lambda x, e: not x and e.find(".//" + qn("w:pageBreakBefore")) is not None),
            "vacio": p(lambda x, e: not x and e.find(".//" + qn("w:sectPr")) is None
                       and e.find(".//" + qn("w:pageBreakBefore")) is None and els.index(e) > 9),
        }
        if self.P["h3pb"] is None:
            self.P["h3pb"] = self.P["h3"]
        # los textos de ejemplo de la plantilla («[…]»), para avisar de los que queden sin rellenar
        self.ejemplos = set(re.findall(r"\[[^\]\n]{3,80}\]", "".join(texto_de(e) for e in els)))
        self.cortes = [e for e in els if e.tag == qn("w:p") and e.find(".//" + qn("w:sectPr")) is not None]
        self.T = {
            "portada": t(lambda x, e: "[CÓDIGO DEL DOCUMENTO]" in x),
            "control": t(lambda x, e: x.startswith("Fecha Entrega")),
            "diagrama": t(lambda x, e: x.startswith("[Insertar diagrama")),
            "reglas": t(lambda x, e: x.startswith("REGLA COMÚN")),
            "actividad": t(lambda x, e: x.startswith("IDENTIFICADOR_NOMBRE")),
            "captura": t(lambda x, e: x.startswith("[Insertar captura del prototipo")),
            "roles": t(lambda x, e: x.startswith("ROLDESCRIP")),
            "matriz": t(lambda x, e: x.startswith("ACCIÓN")),
            "avisos": t(lambda x, e: x.startswith("IDComunicaci")),
            "correos": t(lambda x, e: x.startswith("NOT-01") and "Insertar captura del correo" in x),
            "kpi1": t(lambda x, e: "Horas" in x and "FTE" in x),
            "kpi2": t(lambda x, e: "Lead Time" in x),
        }
        faltan = [k for k, v in {**self.P, **self.T}.items() if v is None and k not in ("vacio",)]
        if faltan or len(self.cortes) < 3:
            raise SystemExit("La plantilla no tiene las piezas de la neutra (" + ", ".join(faltan or ["saltos de sección"])
                             + "): parte de assets/plantillas/df-cliente.docx y cambia solo logos, colores y pie.")
        self.P = {k: copy.deepcopy(v) if v is not None else None for k, v in self.P.items()}
        self.T = {k: v if k in ("portada", "control") else copy.deepcopy(v) for k, v in self.T.items()}
        self.cortes = [copy.deepcopy(c) for c in self.cortes[:3]]
        # se vacía el cuerpo desde «1. INTRODUCCIÓN»; lo de antes (portada, control, índice) se queda
        inicio = next(i for i, e in enumerate(els) if texto_de(e).strip().upper().startswith("1. INTRODUC"))
        for e in els[inicio:]:
            if e is not self.final:
                self.body.remove(e)
        # numeración: el abstracto de las listas numeradas de las pantallas
        self.numeracion = self.d.part.numbering_part.element
        nid = self.P["n0"].find(".//" + qn("w:numId")).get(qn("w:val"))
        num = next(n for n in self.numeracion.findall(qn("w:num")) if n.get(qn("w:numId")) == nid)
        self.abstracto = num.find(qn("w:abstractNumId")).get(qn("w:val"))

    # -- añadir
    def add(self, el):
        if self.final is not None:
            self.final.addprevious(el)
        else:
            self.body.append(el)
        return el

    def par(self, clave, texto=None, **kw):
        p = copy.deepcopy(self.P[clave])
        if texto is not None:
            poner_texto(p, texto, **kw)
        return self.add(p)

    def nueva_lista(self) -> str:
        ids = [int(n.get(qn("w:numId"))) for n in self.numeracion.findall(qn("w:num"))]
        nid = str(max(ids + [0]) + 1)
        num = self.numeracion.makeelement(qn("w:num"), {qn("w:numId"): nid})
        a = num.makeelement(qn("w:abstractNumId"), {qn("w:val"): self.abstracto})
        o = num.makeelement(qn("w:lvlOverride"), {qn("w:ilvl"): "0"})
        o.append(o.makeelement(qn("w:startOverride"), {qn("w:val"): "1"}))
        num.append(a)
        num.append(o)
        self.numeracion.append(num)
        return nid

    def lista(self, ordenada, items, numerar=True):
        nid = self.nueva_lista() if (ordenada or numerar) else None
        for nivel, texto in items:
            if nid:
                p = copy.deepcopy(self.P[("n0", "n1", "n2")[nivel]])
                p.find(".//" + qn("w:numId")).set(qn("w:val"), nid)
            else:
                p = copy.deepcopy(self.P["vineta"])
                p.find(".//" + qn("w:ilvl")).set(qn("w:val"), str(min(nivel, 2)))
            poner_texto(p, texto)
            self.add(p)

    def imagen(self, marco_clave, ruta: Path, pie: str, alto_max_cm: float):
        tbl = copy.deepcopy(self.T[marco_clave])
        tc = tbl.find(".//" + qn("w:tc"))
        p = tc.find(qn("w:p"))
        if ruta.is_file():
            for hijo in list(p):
                if hijo.tag != qn("w:pPr"):
                    p.remove(hijo)
            ancho_tw = int(tbl.find(".//" + qn("w:tblW")).get(qn("w:w"), "9000")) - 400
            par = Paragraph(p, self.d._body)
            run = par.add_run()
            pic = run.add_picture(str(ruta))
            ancho, alto = pic.width, pic.height
            f = min(1.0, Emu(ancho_tw * 635) / ancho, Emu(int(alto_max_cm * 360000)) / alto)
            pic.width, pic.height = int(ancho * f), int(alto * f)
        else:
            avisos.append(f"no está la imagen {ruta}: queda el hueco para pegarla")
        self.add(tbl)
        if pie:
            self.par("pie", pie, conservar=True)

    def bloques(self, bs, base: Path, numerar=False, marco="captura", alto=12.0):
        for b in bs:
            if b[0] == "p":
                self.par("txt", b[1])
            elif b[0] == "nota":
                self.par("aclaracion", b[1], conservar=True)
            elif b[0] == "lista":
                self.lista(b[1], b[2], numerar=numerar)
            elif b[0] == "img":
                self.imagen(marco, (base / b[2]).resolve(), b[1], alto)
            elif b[0] == "tabla":
                self.tabla_generica(b[1])

    def tabla_generica(self, filas):
        """Una tabla libre: con el aspecto de la de roles (cabecera de color)."""
        if not filas:
            return
        tbl = copy.deepcopy(self.T["roles"])
        ajustar_columnas(tbl, len(filas[0]), primera=None)
        rellenar_filas(tbl, filas[1:], proto=1, cabecera=filas[0])
        self.add(tbl)


def filas_de(tbl):
    return tbl.findall(qn("w:tr"))


def rellenar_filas(tbl, filas, proto: int, cabecera=None, borrar_desde=None):
    trs = filas_de(tbl)
    modelo = copy.deepcopy(trs[proto])
    for tr in trs[proto if borrar_desde is None else borrar_desde:]:
        tbl.remove(tr)
    if cabecera is not None:
        for tc, x in zip(trs[0].findall(qn("w:tc")), cabecera):
            poner_celda(tc, x, conservar=True)
    for fila in filas:
        tr = copy.deepcopy(modelo)
        for k, tc in enumerate(tr.findall(qn("w:tc"))):
            poner_celda(tc, fila[k] if k < len(fila) else "")
        tbl.append(tr)


def ajustar_columnas(tbl, n: int, primera: int | None):
    """Deja n columnas: la primera con su ancho (o el que diga «primera») y el resto a partes iguales."""
    grid = tbl.find(qn("w:tblGrid"))
    cols = grid.findall(qn("w:gridCol"))
    total = sum(int(c.get(qn("w:w"))) for c in cols)
    w0 = primera if primera is not None else (int(cols[0].get(qn("w:w"))) if n > 1 else total)
    anchos = [w0] + [int((total - w0) / max(n - 1, 1))] * (n - 1) if n > 1 else [total]
    if primera is None and n > 1:
        anchos = [int(total / n)] * n
    for c in cols:
        grid.remove(c)
    for a in anchos:
        grid.append(grid.makeelement(qn("w:gridCol"), {qn("w:w"): str(a)}))
    for tr in filas_de(tbl):
        tcs = tr.findall(qn("w:tc"))
        span = tcs[0].find(".//" + qn("w:gridSpan"))
        if len(tcs) == 1 and span is not None:          # fila de grupo: ocupa todo
            span.set(qn("w:val"), str(n))
            continue
        while len(tcs) > n:
            tr.remove(tcs.pop())
        while len(tcs) < n:
            nuevo = copy.deepcopy(tcs[-1])
            tcs[-1].addnext(nuevo)
            tcs.append(nuevo)
        for tc, a in zip(tcs, anchos):
            w = tc.find(".//" + qn("w:tcW"))
            if w is not None:
                w.set(qn("w:w"), str(a))
                w.set(qn("w:type"), "dxa")


# ---------------------------------------------------------------- el documento

CAMPOS_ACTIVIDAD = ["descripcion", "actores", "entrada / salida", "estados de la entrada / estados de salida",
                    "formas de arranque / formas de finalizacion", "logica de asignacion", "documentos",
                    "reglas de negocio", "notificaciones", "ejecucion esperada"]
ALIAS_CAMPO = {"estados de entrada / salida": "estados de la entrada / estados de salida",
               "estados": "estados de la entrada / estados de salida",
               "formas de arranque / finalizacion": "formas de arranque / formas de finalizacion",
               "arranque / finalizacion": "formas de arranque / formas de finalizacion",
               "asignacion": "logica de asignacion", "entrada/salida": "entrada / salida"}


def cabecera_doc(lineas):
    datos = {"proceso": "", "codigo": "", "proyecto": "", "ciudad": "", "fecha": "", "version": "0.1", "estado": ""}
    for l in lineas[:12]:
        m = re.match(r"^#\s+(.+?)(?:\s+[—–-]\s+.*)?$", l)
        if m and not datos["proceso"]:
            datos["proceso"] = m.group(1).strip()
            continue
        for trozo in l.split("·"):
            if ":" in trozo:
                k, v = trozo.split(":", 1)
                k = norm(k)
                clave = {"codigo": "codigo", "proyecto": "proyecto", "programa": "proyecto", "ciudad": "ciudad",
                         "fecha": "fecha", "version": "version", "estado": "estado"}.get(k)
                if clave:
                    datos[clave] = v.strip()
    return datos


def nombre_word(proceso: str, version: str) -> str:
    """DF-cliente-<proceso sin tildes ni signos>-v<versión>.docx: el mismo nombre que espera proyecto.py entregar."""
    slug = re.sub(r"[^A-Za-z0-9_]+", "-", re.sub(r"[̀-ͯ]", "", unicodedata.normalize("NFD", proceso)))
    return f"DF-cliente-{slug.strip('-') or 'proceso'}-v{version}.docx"


RX_ACTIVIDAD = re.compile(r"^(\S*\d\S*)\s+(?:[—–-]\s+)?(.+)$")      # «ACT-03 Revisar…», «GI-011-1-1.1 Análisis…»
RX_REGLA = re.compile(r"^regla com[uú]n\s*\d*\s*[·:.—–-]\s*(.+)$", re.I)


def generar(proyecto: Path, salida: Path | None, plantilla_arg: Path | None) -> Path:
    analisis = proyecto / "analisis"
    md_path = analisis / "df-cliente.md"
    if not md_path.is_file():
        raise SystemExit(f"No está {md_path}: créalo con proyecto.py iniciar --df-cliente y escríbelo con "
                         "references/df-cliente-plantilla.md")
    lineas = limpiar(md_path.read_text(encoding="utf-8"))
    D = cabecera_doc(lineas)
    arbol = secciones(lineas)

    # plantilla
    plantilla, neutra = None, False
    for c in [plantilla_arg, proyecto / "plantillas" / "df-cliente.docx"]:
        if c and Path(c).is_file():
            plantilla = Path(c)
            break
    if plantilla is None:
        plantilla, neutra = NEUTRA, True
    print(f"· plantilla: {plantilla if not neutra else 'la neutra de la skill'}")
    T = Plantilla(plantilla)

    # portada y encabezados
    sustituir = [(r"\[C[ÓO]DIGO DEL DOCUMENTO\s*\]", D["codigo"] or "pendiente de confirmar"),
                 (r"\[NOMBRE DEL PROCESO\]", D["proceso"]), (r"\[NOMBRE DEL PROYECTO\s*/\s*PROGRAMA\]", D["proyecto"]),
                 (r"\[CIUDAD\]", D["ciudad"]), (r"\[MES A[ÑN]O\]", D["fecha"])]
    for p in T.T["portada"].iter(qn("w:p")):
        x = texto_de(p)
        y = x
        for pat, val in sustituir:
            y = re.sub(pat, (val or "").upper() if "PROCESO" not in pat else (val or ""), y, flags=re.I)
        if y != x:
            poner_texto(p, y, conservar=True)
    # todos los encabezados y pies del documento (los de cada sección, también los que se han vuelto a poner)
    partes = [r.target_part for r in T.d.part.rels.values() if r.reltype.endswith(("/header", "/footer"))]
    for parte in partes:
        for p in parte.element.iter(qn("w:p")):
            x = texto_de(p)
            y = re.sub(r"\[C[ÓO]DIGO DEL DOCUMENTO\s*\]", D["codigo"], x, flags=re.I)
            y = re.sub(r"\[Nombre del proceso\]", D["proceso"], y, flags=re.I)
            if y != x and "PAGE" not in p.xml:
                poner_texto(p, y, conservar=True)
    T.d.core_properties.title = f"{D['proceso']} — Documento de diseño funcional"

    # control de cambios
    nodo = buscar(arbol, "Control de cambios")
    filas = []
    if nodo:
        tabla = next((b for b in bloques(nodo[2]) if b[0] == "tabla"), None)
        filas = [f for f in (tabla[1][1:] if tabla else []) if any(f)]
    if not filas:
        filas = [["", D["version"], "Primera versión del diseño funcional", "", "", ""]]
    rellenar_filas(T.T["control"], filas, proto=1)

    base = analisis

    def seccion(patron, titulo, clave="h2"):
        n = buscar(arbol, patron)
        T.par(clave, titulo)
        if n is None:
            T.par("txt", "pendiente de confirmar.")
            avisos.append(f"df-cliente.md no tiene el apartado «{patron}»")
        return n

    def sub_barra(n, numerar=False):
        T.bloques(bloques(n[2]), base, numerar=numerar)
        for h in n[3]:
            T.par("barra", h[1])
            T.bloques(bloques(todo(h)), base, numerar=numerar)

    # 1. Introducción
    T.par("h1", "1. INTRODUCCIÓN AL PROCESO")
    n = seccion("1.1", "1.1 DESCRIPCIÓN DEL PROCESO")
    if n:
        sub_barra(n)
    n = seccion("1.2", "1.2 ALCANCE")
    if n:
        sub_barra(n)
    T.add(copy.deepcopy(T.cortes[0]))

    # 2.1 Flujo y reglas comunes: cada «Regla común n · Título», una fila con «REGLA COMÚN n» y su título en la primera
    # columna y su texto en la segunda
    T.par("h1", "2. DISEÑO DE LA SOLUCIÓN")
    n = seccion("2.1", "2.1 FLUJO DEL PROCESO")
    if n:
        T.bloques(bloques(n[2]), base, marco="diagrama", alto=12.5)
        for h in n[3]:
            T.par("sub", h[1])
            if not norm(h[1]).startswith("logica general"):
                T.bloques(bloques(todo(h)), base, marco="diagrama", alto=12.5)
                continue
            T.bloques(bloques(h[2]), base)
            reglas = []
            for r in h[3]:
                m = RX_REGLA.match(r[1])
                titulo = (m.group(1) if m else r[1]).strip()
                trozos = []
                for b in bloques(todo(r)):
                    if b[0] == "lista":
                        trozos += [t for _, t in b[2]]
                    elif b[0] in ("p", "nota"):
                        trozos.append(b[1])
                    else:
                        avisos.append(f"regla común «{titulo}»: solo admite párrafos y listas; lo demás no sale")
                reglas.append((titulo.upper(), "<br>".join(trozos)))
            if reglas:
                tbl = copy.deepcopy(T.T["reglas"])
                rellenar_filas(tbl, [[f"REGLA COMÚN {k}<br>{titulo}", x] for k, (titulo, x) in enumerate(reglas, 1)],
                               proto=0)
                T.add(tbl)
            else:
                avisos.append("2.1: la lógica general del flujo no tiene ninguna «##### Regla común n · Título»")

    # 2.2 Actividades
    n = seccion("2.2", "2.2 DESCRIPCIÓN DE ACTIVIDADES")
    if n:
        T.bloques(bloques(n[2]), base)
        for k, h in enumerate(n[3]):
            m = RX_ACTIVIDAD.match(h[1])
            ident, nombre = (m.group(1), m.group(2).strip()) if m else ("", h[1])
            valores, otros = {}, []
            for b in bloques(todo(h)):
                if b[0] == "tabla":
                    for f in b[1]:
                        if len(f) >= 2 and f[0] and norm(f[0]) != "campo":
                            clave = norm(f[0].strip("*"))
                            valores[ALIAS_CAMPO.get(clave, clave)] = f[1]
                else:
                    otros.append(b)
            if k:
                T.par("salto")
            tbl = copy.deepcopy(T.T["actividad"])
            trs = filas_de(tbl)
            poner_celda(trs[0].findall(qn("w:tc"))[1], f"{ident} {nombre}".strip(), negrita=True)
            for tr in trs[1:]:
                tcs = tr.findall(qn("w:tc"))
                clave = norm(texto_de(tcs[0]))
                v = valores.pop(ALIAS_CAMPO.get(clave, clave), None)
                if v is None:
                    avisos.append(f"{ident or nombre}: falta «{texto_de(tcs[0]).strip()}» (escribe «N/A» si no aplica)")
                    v = "pendiente de confirmar"
                poner_celda(tcs[1], v)
            for resto in valores:
                avisos.append(f"{ident or nombre}: la fila «{resto}» no es un campo de la ficha de actividad")
            T.add(tbl)
            T.bloques(otros, base)
    T.add(copy.deepcopy(T.cortes[1]))

    # 2.3 Pantallas, por áreas: «#### 2.3.n Pantallas <Área>» y, dentro, «##### <Pantalla>» con sus apartados
    n = seccion("2.3", "2.3 DISEÑO DE LA PANTALLA / LAYOUT")
    if n:
        T.bloques(bloques(n[2]), base)
        areas = [h for h in n[3] if re.match(r"^(2\.3\.\S+\s+)?pantallas\b", norm(h[1]))]
        if not areas and n[3]:
            avisos.append("2.3: las pantallas van dentro de un área («#### 2.3.n Pantallas <Área>»)")
            areas = [(4, "Pantallas", [], n[3])]
        for h in n[3]:
            if areas and h not in areas and areas[0][1] != "Pantallas":
                avisos.append(f"2.3: «{h[1]}» no es un área («#### 2.3.n Pantallas <Área>»): no sale")
        for ka, area in enumerate(areas, 1):
            nombre_area = re.sub(r"^(2\.3\.\S+\s+)?pantallas\s*", "", area[1], flags=re.I).strip()
            t = T.par("h3", f"2.3.{ka} PANTALLAS {nombre_area.upper()}".rstrip())
            if ka > 1:
                con_salto(t)
            T.bloques(bloques(area[2]), base)
            for kp, h in enumerate(area[3], 1):
                T.par("h4" if kp == 1 else "h4pb", f"2.3.{ka}.{kp} {h[1]}")
                T.bloques(bloques(h[2]), base, numerar=True)
                subs = [norm(s[1]) for s in h[3]]
                if "logica general" not in subs:
                    avisos.append(f"pantalla «{h[1]}»: sin «Lógica General», que es obligatoria")
                for s in h[3]:
                    T.par("sub", s[1])
                    T.bloques(bloques(todo(s)), base, numerar=True, marco="captura", alto=13)
                T.par("nota", None)
    T.add(copy.deepcopy(T.cortes[2]))

    # 2.4 Otras consideraciones
    T.par("h2", "2.4 OTRAS CONSIDERACIONES")
    n = buscar(arbol, "2.4.1")
    T.par("h3b", "2.4.1 ROLES Y PERMISOS")
    if n is None:
        T.par("txt", "pendiente de confirmar.")
        avisos.append("df-cliente.md no tiene el apartado «2.4.1 Roles y permisos»")
    else:
        T.bloques(bloques(n[2]), base)
        for s in n[3]:
            t = norm(s[1])
            T.par("desc_general" if t.startswith("descripcion general") else "sub", s[1])
            for b in bloques(todo(s)):
                if b[0] == "tabla" and t.startswith("roles"):
                    tbl = copy.deepcopy(T.T["roles"])
                    rellenar_filas(tbl, b[1][1:], proto=1)
                    T.add(tbl)
                elif b[0] == "tabla" and t.startswith("matriz"):
                    T.par("leyenda")
                    T.add(matriz(T, b[1]))
                else:
                    T.bloques([b], base)

    n = buscar(arbol, "2.4.2")
    T.par("h3bpb", "2.4.2 NOTIFICACIONES POR CORREO")
    if n is None:
        T.par("txt", "No hay.")
    else:
        avs = []
        for b in bloques(todo(n)):
            if b[0] == "tabla" and b[1] and norm(b[1][0][0]) == "id":
                avs = [f for f in b[1][1:] if any(f)]
                tbl = copy.deepcopy(T.T["avisos"])
                rellenar_filas(tbl, avs, proto=1)
                for tr in filas_de(tbl)[1:]:
                    tc = tr.findall(qn("w:tc"))[0]
                    poner_celda(tc, texto_de(tc), negrita=True)
                T.add(tbl)
            else:
                T.bloques([b], base)
        if avs:
            T.par("ejemplos")
            tbl = copy.deepcopy(T.T["correos"])
            modelo = copy.deepcopy(filas_de(tbl)[0])
            for tr in filas_de(tbl):
                tbl.remove(tr)
            for k in range(0, len(avs), 2):
                tr = copy.deepcopy(modelo)
                for tc, av in zip(tr.findall(qn("w:tc")), avs[k:k + 2] + [None]):
                    maqueta_correo(tc, av, D)
                tbl.append(tr)
            T.add(tbl)

    # 2.5 KPIs
    n = seccion("2.5", "2.5 MÉTRICAS Y KPIs", clave="h2pb")
    if n:
        tablas = [b for b in bloques(todo(n)) if b[0] == "tabla"]
        t1 = next((b[1] for b in tablas if len(b[1][0]) >= 6), None)
        t2 = next((b[1] for b in tablas if len(b[1][0]) == 4), None)
        for clave, t, proto in (("kpi1", t1, 2), ("kpi2", t2, 1)):
            tbl = copy.deepcopy(T.T[clave])
            if t:
                rellenar_filas(tbl, [f for f in t[1:] if any(f)], proto=proto)
                for tr in filas_de(tbl)[proto:]:
                    tc = tr.findall(qn("w:tc"))[0]
                    poner_celda(tc, texto_de(tc), negrita=True)
            else:
                avisos.append(f"2.5: falta la tabla de {'esfuerzo (horas y FTE)' if clave == 'kpi1' else 'tiempo de ciclo'}")
                for tr in filas_de(tbl)[proto:]:
                    for tc in tr.findall(qn("w:tc"))[1:]:
                        poner_celda(tc, "pendiente de confirmar")
            T.add(tbl)
            if T.P.get("vacio") is not None:
                T.par("vacio")
        T.bloques([b for b in bloques(todo(n)) if b[0] != "tabla"], base)

    # 2.6 Periodo de estabilización
    n = seccion("2.6", "2.6 PERIODO DE ESTABILIZACIÓN", clave="h26")
    if n:
        T.bloques(bloques(todo(n)), base)

    # índice: Word lo actualiza al abrir
    ajustes = T.d.settings.element
    if ajustes.find(qn("w:updateFields")) is None:
        ajustes.append(ajustes.makeelement(qn("w:updateFields"), {qn("w:val"): "true"}))

    # lo que queda por confirmar: en el texto y en df-cliente-pendientes.md, que no sale en el Word
    en_texto = sum(len(re.findall(r"pendiente de confirmar", texto_de(e), re.I)) for e in T.body.iterchildren())
    if en_texto:
        avisos.append(f"el Word dice «pendiente de confirmar» {en_texto} veces (sale resaltado): antes de la entrega "
                      "final no queda ninguno")
    pend = analisis / "df-cliente-pendientes.md"
    abiertas = re.findall(r"^\|\s*(PC-\d+)\s*\|", pend.read_text(encoding="utf-8"), re.M) if pend.is_file() else []
    if abiertas:
        avisos.append(f"df-cliente-pendientes.md tiene preguntas abiertas: {', '.join(abiertas)}")

    # salida
    if salida is None:
        salida = proyecto / "entregables" / nombre_word(D["proceso"], D["version"])
    entregados = (proyecto / "proyecto.md").read_text(encoding="utf-8") if (proyecto / "proyecto.md").is_file() else ""
    k = 1
    while salida.exists() and salida.name in entregados:
        salida = salida.with_name(re.sub(r"(-\d+)?\.docx$", f"-{k}.docx", salida.name))
        k += 1
    salida.parent.mkdir(parents=True, exist_ok=True)
    try:
        T.d.save(str(salida))
    except PermissionError:
        raise SystemExit(f"No se puede escribir {salida}: está abierto en Word. Ciérralo y vuelve a generarlo.")
    if neutra:
        color = color_de_marca(proyecto)
        if color:
            recolorear(salida, color)
    resto = sorted(set(re.findall(r"\[[^\]\n]{3,80}\]", "".join(texto_de(e) for e in T.body.iterchildren())))
                   & T.ejemplos)
    for r in resto[:10]:
        avisos.append(f"queda el texto de ejemplo «{r}» de la plantilla")
    return salida


def con_salto(p):
    """El párrafo empieza en página nueva."""
    ppr = p.find(qn("w:pPr"))
    if ppr is None:
        ppr = p.makeelement(qn("w:pPr"), {})
        p.insert(0, ppr)
    if ppr.find(qn("w:pageBreakBefore")) is None:
        ppr.append(ppr.makeelement(qn("w:pageBreakBefore"), {}))
    return p


def matriz(T, filas):
    """La matriz de permisos: una columna por rol y, en las filas, los grupos (una fila con solo su nombre) y las
    acciones, con «✓» donde está permitida."""
    tbl = copy.deepcopy(T.T["matriz"])
    cab = filas[0]
    ajustar_columnas(tbl, len(cab), primera=4070)
    trs = filas_de(tbl)
    for j, (tc, x) in enumerate(zip(trs[0].findall(qn("w:tc")), cab)):
        poner_celda(tc, x.upper() if j == 0 else x, conservar=True)
    grupo, accion = copy.deepcopy(trs[1]), copy.deepcopy(trs[2])
    for tr in trs[1:]:
        tbl.remove(tr)
    for f in filas[1:]:
        es_grupo = bool(f[0].strip()) and not any(x.strip() for x in f[1:])
        tr = copy.deepcopy(grupo if es_grupo else accion)
        tcs = tr.findall(qn("w:tc"))
        if es_grupo:
            poner_celda(tcs[0], f[0].strip("*").strip(), conservar=True)
        else:
            for j, tc in enumerate(tcs):
                v = f[j] if j < len(f) else ""
                poner_celda(tc, "✓" + v.strip()[1:] if v.strip().startswith("✓") else
                            ("✓" if v.strip().lower() in ("x", "sí", "si") else v))
        tbl.append(tr)
    return tbl


def maqueta_correo(tc, av, D):
    """La celda de un ejemplo de correo: «NOT-nn» y, en su marco, De/Para/Asunto y el cuerpo."""
    ps = tc.findall(qn("w:p"))
    interior = tc.find(qn("w:tbl"))
    if av is None:
        if interior is not None:
            tc.remove(interior)
        for p in ps:
            poner_texto(p, "")
        return
    poner_texto(ps[0], av[0], conservar=True)
    if interior is None:
        return
    celda = interior.find(".//" + qn("w:tc"))
    lineas = [f"**Para:** {av[3] if len(av) > 3 else ''}", f"**Asunto:** {av[4] if len(av) > 4 else ''}", ""]
    lineas += [x.strip() for x in re.split(r"<br\s*/?>", av[5] if len(av) > 5 else "")]
    poner_celda(celda, "<br>".join(lineas))
    for p in celda.findall(qn("w:p")):
        ppr = p.find(qn("w:pPr"))
        jc = ppr.find(qn("w:jc")) if ppr is not None else None
        if jc is not None:
            jc.set(qn("w:val"), "left")


def color_de_marca(proyecto: Path) -> str | None:
    d = proyecto / "prototipo"
    for f in sorted(d.glob("brand-*.json")) if d.is_dir() else []:
        try:
            b = json.loads(f.read_text(encoding="utf-8"))
            c = str((b.get("site") or {}).get("backgroundColor") or (b.get("palette") or {}).get("navy") or "")
            if re.match(r"^#?[0-9a-fA-F]{6}$", c):
                print(f"· color de {f.relative_to(proyecto).as_posix()}: #{c.lstrip('#').upper()}")
                return c.lstrip("#").upper()
        except (ValueError, OSError):
            pass
    return None


def recolorear(docx_path: Path, color: str):
    tmp = docx_path.with_suffix(".tmp")
    with zipfile.ZipFile(docx_path) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for it in zin.infolist():
            data = zin.read(it.filename)
            if it.filename.startswith("word/") and it.filename.endswith(".xml"):
                x = data.decode("utf-8")
                for c in COLORES_NEUTRA:
                    x = re.sub(c, color, x, flags=re.I)
                data = x.encode("utf-8")
            zout.writestr(it, data)
    tmp.replace(docx_path)


def a_pdf(fichero: Path, revision: Path) -> Path | None:
    exes = [os.environ.get("SOFFICE"), "soffice", "libreoffice"]
    if sys.platform == "win32":
        exes.append(r"C:\Program Files\LibreOffice\program\soffice.exe")
    if sys.platform == "darwin":
        exes.append("/Applications/LibreOffice.app/Contents/MacOS/soffice")
    tmp = Path(tempfile.mkdtemp(prefix="dfc-pdf-"))
    try:
        perfil = (tmp / "perfil").as_uri()
        env = {**os.environ, "HOME": str(tmp), "TMPDIR": str(tmp), "TMP": str(tmp), "TEMP": str(tmp)}
        for exe in [e for e in exes if e]:
            if not shutil.which(exe) and not Path(exe).is_file():
                continue
            subprocess.run([exe, f"-env:UserInstallation={perfil}", "--headless", "--convert-to", "pdf", "--outdir",
                            str(tmp / "salida"), str(fichero)], env=env, capture_output=True, encoding="utf-8",
                           errors="replace", timeout=300)
            pdf = tmp / "salida" / (fichero.stem + ".pdf")
            if pdf.is_file():
                revision.mkdir(parents=True, exist_ok=True)
                destino = revision / pdf.name
                shutil.copyfile(pdf, destino)
                return destino
        print("· sin LibreOffice (soffice): no se genera el PDF; revisa el Word a mano")
        return None
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main(argv):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    if docx is None:
        print("Falta python-docx: python3 -m pip install python-docx")
        return 2
    args = list(argv)
    def opcion(k):
        if k in args:
            i = args.index(k)
            v = args[i + 1] if i + 1 < len(args) else None
            del args[i:i + 2]
            return v
        return None
    salida, plantilla = opcion("-o"), opcion("--plantilla")
    pdf = "--pdf" in args
    args = [a for a in args if a != "--pdf"]
    if not args:
        print(__doc__)
        return 2
    proyecto = Path(args[0]).resolve()
    if proyecto.name == "analisis":
        proyecto = proyecto.parent
    hecho = generar(proyecto, Path(salida).resolve() if salida else None, Path(plantilla) if plantilla else None)
    print(f"✓ {hecho}")
    if pdf:
        r = a_pdf(hecho, proyecto / "entregables" / "revision")
        if r:
            print(f"✓ PDF para revisar: {r}")
    for a in dict.fromkeys(avisos):
        print(f"  aviso: {a}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
