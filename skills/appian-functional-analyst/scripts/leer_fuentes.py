#!/usr/bin/env python3
"""Cataloga y convierte a texto las fuentes de un análisis funcional.

Cada fichero recibe un ID estable (FU-01, FU-02…) y se guarda como Markdown con
marcas de posición para poder citarlo: «Diapositiva 34», «Página 12»,
«[00:14:32] Rol», cabeceras del correo, actividades de un BPMN…

Uso:
  python3 leer_fuentes.py <ficheros o carpetas...> -o fuentes/
  python3 leer_fuentes.py --una-fuente <p>/as-is [<ficheros…>] -o fuentes/

Con --una-fuente, la carpeta entera es una sola fuente (p. ej. as-is/, la aplicación existente): su .md es el índice
de sus documentos, sin su extracción en bruto (extraccion/), que el análisis no cita.

Genera en la carpeta de salida:
  FU-01-<nombre>.md …   el contenido de cada fuente
  indice.md            tabla de fuentes (ID, fichero, tipo, detalle, fecha)
  indice.json          estado para mantener los IDs entre ejecuciones
  adjuntos/FU-xx/       adjuntos de los correos .eml

Volver a ejecutarlo con fuentes nuevas conserva los IDs de las ya catalogadas
(se reconocen por contenido) y numera las nuevas a continuación.

Solo usa la biblioteca estándar de Python, salvo:
  .pdf  pdftotext (poppler) o el paquete pypdf; si no hay, léelo con la herramienta Read
  .msg  el paquete extract-msg; si no hay, guarda el correo como .eml o PDF desde Outlook
Formatos: .vtt .srt .txt .md .docx .pptx .xlsx .pdf .eml .msg .bpmn .drawio .vsdx.
Se catalogan sin leer: imágenes (.png .jpg…, se revisan con Read) y formatos antiguos
(.doc .ppt .xls .vsd .odt .rtf…, con la indicación de a qué formato convertirlos).
Acepta comodines entre comillas ("reuniones/*.vtt") también en PowerShell o cmd.
"""
import argparse, base64, datetime, email, email.policy, email.utils, glob, hashlib, html, json, pathlib, re
import shutil, subprocess, sys, urllib.parse, zipfile, zlib
import xml.etree.ElementTree as ET

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
    "x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL",
    "v": "http://schemas.microsoft.com/office/visio/2012/main",
}
IMAGES = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}
SUPPORTED = {".vtt", ".srt", ".txt", ".md", ".docx", ".pptx", ".xlsx", ".pdf", ".eml", ".msg",
             ".bpmn", ".drawio", ".vsdx"} | IMAGES
# formatos que se catalogan (para que no se pierdan) pero hay que convertir antes de leer
LEGACY = {".doc": ".docx o PDF", ".ppt": ".pptx o PDF", ".xls": ".xlsx", ".vsd": ".vsdx o PDF", ".odt": ".docx o PDF",
          ".odp": ".pptx o PDF", ".ods": ".xlsx", ".rtf": ".docx o PDF", ".oft": ".eml o PDF"}
MAX_ROWS = 300


def md_table(rows):
    rows = [[c.replace("|", "\\|").replace("\n", " ").strip() for c in r] for r in rows if any(c.strip() for c in r)]
    if not rows:
        return ""
    n = max(len(r) for r in rows)
    rows = [r + [""] * (n - len(r)) for r in rows]
    out = ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * n]
    out += ["| " + " | ".join(r) + " |" for r in rows[1:]]
    return "\n".join(out)


def rels(z, path):
    """Relaciones de una parte OOXML: {rId: ruta dentro del zip}."""
    p = pathlib.PurePosixPath(path)
    rp = p.parent / "_rels" / (p.name + ".rels")
    if str(rp) not in z.namelist():
        return {}
    out = {}
    for r in ET.fromstring(z.read(str(rp))).findall("rel:Relationship", NS):
        t = r.get("Target")
        if r.get("TargetMode") == "External":
            continue
        full = pathlib.PurePosixPath(t[1:]) if t.startswith("/") else p.parent / t
        parts = []
        for seg in full.parts:
            if seg == "..":
                parts.pop()
            elif seg != ".":
                parts.append(seg)
        out[r.get("Id")] = ("/".join(parts), r.get("Type", ""))
    return out


# ---------------------------------------------------------------- lectores

def read_docx(path):
    z = zipfile.ZipFile(path)
    styles = {}
    if "word/styles.xml" in z.namelist():
        for s in ET.fromstring(z.read("word/styles.xml")).findall("w:style", NS):
            name = s.find("w:name", NS)
            styles[s.get(f"{{{NS['w']}}}styleId")] = (name.get(f"{{{NS['w']}}}val") if name is not None else "").lower()

    def ptext(p):
        parts = []
        for el in p.iter():
            tag = el.tag.split("}")[1]
            if tag == "t":
                parts.append(el.text or "")
            elif tag == "tab":
                parts.append("\t")
            elif tag in ("br", "cr"):
                parts.append("\n")
        return "".join(parts).strip()

    body = ET.fromstring(z.read("word/document.xml")).find("w:body", NS)
    out, paras = [], 0
    for el in body:
        tag = el.tag.split("}")[1]
        if tag == "p":
            t = ptext(el)
            if not t:
                continue
            paras += 1
            ps = el.find("w:pPr/w:pStyle", NS)
            name = styles.get(ps.get(f"{{{NS['w']}}}val"), "") if ps is not None else ""
            m = re.match(r"(heading|título|titulo|encabezado)\s*(\d)", name)
            out.append(("#" * (int(m.group(2)) + 1) + " " + t) if m else t)
        elif tag == "tbl":
            rows = [[ptext(tc) for tc in tr.findall("w:tc", NS)] for tr in el.findall("w:tr", NS)]
            out.append(md_table(rows))
    notas, n_com, n_cambios = docx_revision(z, body, styles)
    detalle = f"{paras} párrafos" + (f", {n_com} comentarios" if n_com else "") + (f", {n_cambios} cambios marcados" if n_cambios else "")
    return "\n\n".join(out + notas), detalle


RX_PIEZA = re.compile(r"^~*((?:ACT|ESC|HU|RB|PAN|AV|DOC|INT|PC|DT|PT)-\d+)")


def docx_revision(z, body, styles):
    """Comentarios y cambios marcados de un Word (por ejemplo, el DF que devuelve el cliente revisado), cada uno
    con el texto al que se refiere y la pieza (HU-07, PAN-03…) o el apartado donde está."""
    w = f"{{{NS['w']}}}"
    textos = {}
    if "word/comments.xml" in z.namelist():
        for c in ET.fromstring(z.read("word/comments.xml")).findall("w:comment", NS):
            t = "\n".join("".join(x.text or "" for x in p.iter(f"{w}t")) for p in c.findall("w:p", NS)).strip()
            textos[c.get(f"{w}id")] = (c.get(f"{w}author", ""), (c.get(f"{w}date") or "")[:10], t)
    ancla, donde, abiertos = {}, {}, set()
    cambios, titulo, pieza = [], "", ""
    for p in body.iter(f"{w}p"):
        texto_p = "".join(x.text or "" for x in p.iter(f"{w}t")).strip()
        ps = p.find("w:pPr/w:pStyle", NS)
        if texto_p and ps is not None and re.match(r"(heading|título|titulo|encabezado)", styles.get(ps.get(f"{w}val"), "")):
            titulo, pieza = texto_p, ""
        mp = RX_PIEZA.match(texto_p)
        if mp:
            pieza = mp.group(1)
        lugar = titulo[:70] if pieza and titulo.startswith(pieza) else " · ".join(x for x in (pieza, titulo[:60]) if x)
        for el in p.iter():
            tag = el.tag.split("}")[1]
            if tag == "commentRangeStart":
                abiertos.add(el.get(f"{w}id"))
                donde.setdefault(el.get(f"{w}id"), lugar)
            elif tag == "commentRangeEnd":
                abiertos.discard(el.get(f"{w}id"))
            elif tag == "commentReference":
                donde.setdefault(el.get(f"{w}id"), lugar)
            elif tag == "t":
                for i in abiertos:
                    ancla[i] = ancla.get(i, "") + (el.text or "")
            elif tag in ("ins", "del"):
                t = "".join(x.text or "" for x in el.iter() if x.tag.split("}")[1] in ("t", "delText")).strip()
                if t:
                    cambios.append(f"- {'Añade' if tag == 'ins' else 'Quita'} «{t}» · {el.get(f'{w}author', '')} · "
                                   f"{(el.get(f'{w}date') or '')[:10]} · en {lugar or 'el principio'}: «{texto_p[:120]}»")
    notas = []
    if textos:
        notas.append("## Comentarios del documento")
        for i, (autor, fecha, t) in textos.items():
            a = re.sub(r"\s+", " ", ancla.get(i, "")).strip()
            notas.append(f"- **C{int(i) + 1 if i.isdigit() else i}** · {autor} · {fecha} · en {donde.get(i) or 'el documento'}"
                         + (f" · sobre «{a[:200]}»" if a else "") + f": {t}")
    if cambios:
        notas.append("\n## Cambios marcados\n")
        notas += cambios
    return ["\n".join(notas[:1] + [""] + notas[1:])] if notas else [], len(textos), len(cambios)


def read_pptx(path):
    z = zipfile.ZipFile(path)
    pres = ET.fromstring(z.read("ppt/presentation.xml"))
    prels = rels(z, "ppt/presentation.xml")
    order = [prels[s.get(f"{{{NS['r']}}}id")][0] for s in pres.findall("p:sldIdLst/p:sldId", NS)]

    out = []
    for n, slide in enumerate(order, 1):
        root = ET.fromstring(z.read(slide))
        tables = [md_table([[" ".join((t.text or "") for t in tc.iter(f"{{{NS['a']}}}t")) for tc in tr.findall("a:tc", NS)]
                            for tr in tbl.findall("a:tr", NS)]) for tbl in root.iter(f"{{{NS['a']}}}tbl")]
        texts = []  # cuadros de texto y formas (las celdas de tabla usan a:txBody y van aparte)
        for tb in root.iter(f"{{{NS['p']}}}txBody"):
            for p in tb.findall("a:p", NS):
                t = "".join((r.text or "") for r in p.iter(f"{{{NS['a']}}}t")).strip()
                if t:
                    texts.append(t)
        pics = sum(1 for _ in root.iter(f"{{{NS['p']}}}pic"))
        notes = []
        for target, typ in rels(z, slide).values():
            if typ.endswith("/notesSlide") and target in z.namelist():
                nroot = ET.fromstring(z.read(target))
                for sp in nroot.iter(f"{{{NS['p']}}}sp"):
                    ph = sp.find(".//p:nvPr/p:ph", NS)
                    if ph is not None and ph.get("type") == "body":
                        notes += ["".join((r.text or "") for r in p.iter(f"{{{NS['a']}}}t")).strip()
                                  for p in sp.iter(f"{{{NS['a']}}}p")]
        block = [f"## Diapositiva {n}"] + texts + tables
        if pics:
            block.append(f"_[{pics} imagen(es) en la diapositiva: si describe una pantalla o un flujo, revísala visualmente]_")
        notes = [x for x in notes if x]
        if notes:
            block.append("**Notas del orador:** " + " ".join(notes))
        out.append("\n\n".join(block))
    return "\n\n".join(out), f"{len(order)} diapositivas"


def col_index(ref):
    n = 0
    for ch in re.match(r"[A-Z]+", ref).group(0):
        n = n * 26 + ord(ch) - 64
    return n - 1


def read_xlsx(path):
    z = zipfile.ZipFile(path)
    shared = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("x:si", NS):
            shared.append("".join(t.text or "" for t in si.iter(f"{{{NS['x']}}}t")))
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    wrels = rels(z, "xl/workbook.xml")
    out, nsheets = [], 0
    for sh in wb.findall("x:sheets/x:sheet", NS):
        nsheets += 1
        target = wrels[sh.get(f"{{{NS['r']}}}id")][0]
        rows = []
        for row in ET.fromstring(z.read(target)).iter(f"{{{NS['x']}}}row"):
            cells = {}
            for c in row.findall("x:c", NS):
                t, v = c.get("t"), c.find("x:v", NS)
                if t == "s" and v is not None:
                    val = shared[int(v.text)]
                elif t == "b" and v is not None:
                    val = "Sí" if v.text == "1" else "No"
                elif t == "inlineStr":
                    val = "".join(x.text or "" for x in c.iter(f"{{{NS['x']}}}t"))
                else:
                    val = v.text if v is not None and v.text else ""
                if c.get("r"):
                    cells[col_index(c.get("r"))] = val
            if cells:
                rows.append([cells.get(i, "") for i in range(max(cells) + 1)])
        extra = f"\n\n_[{len(rows) - MAX_ROWS} filas más no incluidas]_" if len(rows) > MAX_ROWS else ""
        out.append(f"## Hoja «{sh.get('name')}»\n\n" + md_table(rows[:MAX_ROWS]) + extra)
    return "\n\n".join(out), f"{nsheets} hojas"


def read_pdf(path):
    if shutil.which("pdftotext"):
        txt = subprocess.run(["pdftotext", "-layout", "-enc", "UTF-8", str(path), "-"], capture_output=True,
                             text=True, encoding="utf-8", errors="replace").stdout
        pages = txt.split("\f")
    else:
        try:
            from pypdf import PdfReader
        except ImportError:
            return None, "no leído: falta pdftotext (poppler) o pypdf; léelo con la herramienta Read"
        pages = [p.extract_text() or "" for p in PdfReader(str(path)).pages]
    pages = [p for p in pages]
    while pages and not pages[-1].strip():
        pages.pop()
    body = "\n\n".join(f"## Página {i}\n\n{p.strip()}" for i, p in enumerate(pages, 1))
    note = "" if any(p.strip() for p in pages) else " (sin texto: probablemente escaneado; revísalo con Read)"
    return body, f"{len(pages)} páginas{note}"


def ts(t):
    t = t.strip().replace(",", ".")
    parts = t.split(":")
    if len(parts) == 2:
        parts = ["0"] + parts
    h, m, s = parts
    return f"{int(h):02d}:{int(m):02d}:{int(float(s)):02d}"


def read_subtitles(path):
    """VTT (Teams, Zoom, Meet) y SRT → [hh:mm:ss] Hablante: texto, uniendo intervenciones seguidas."""
    raw = path.read_text(encoding="utf-8-sig", errors="replace")
    turns = []
    for block in re.split(r"\n\s*\n", raw.replace("\r\n", "\n")):
        lines = [l for l in block.strip().split("\n") if l.strip()]
        idx = next((i for i, l in enumerate(lines) if "-->" in l), None)
        if idx is None:
            continue
        start = ts(lines[idx].split("-->")[0])
        text = " ".join(lines[idx + 1:])
        speaker = ""
        m = re.match(r"<v\s+([^>]+)>(.*)", text)
        if m:
            speaker, text = m.group(1).strip(), m.group(2)
        text = re.sub(r"</?[^>]+>", "", text).strip()
        if not speaker:
            m = re.match(r"([^:]{2,40}):\s+(.*)", text)
            if m:
                speaker, text = m.group(1).strip(), m.group(2)
        if not text:
            continue
        if turns and turns[-1][1] == speaker:
            turns[-1][2] += " " + text
        else:
            turns.append([start, speaker, text])
    body = "\n\n".join(f"[{t}] {s + ': ' if s else ''}{x}" for t, s, x in turns)
    speakers = sorted({s for _, s, _ in turns if s})
    return body, f"{len(turns)} intervenciones, {len(speakers)} participantes"


def html_text(s):
    s = re.sub(r"(?is)<(script|style).*?</\1>", "", s)
    s = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</tr>|</li>", "\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"\n\s*\n+", "\n\n", html.unescape(s)).strip()


def read_eml(path, attach_dir):
    msg = email.message_from_bytes(path.read_bytes(), policy=email.policy.default)
    head = [f"**{k}:** {msg.get(h, '')}" for k, h in
            (("De", "From"), ("Para", "To"), ("CC", "Cc"), ("Fecha", "Date"), ("Asunto", "Subject")) if msg.get(h)]
    body = msg.get_body(preferencelist=("plain", "html"))
    text = ""
    if body is not None:
        text = body.get_content()
        if body.get_content_type() == "text/html":
            text = html_text(text)
    names = []
    for part in msg.iter_attachments():
        name = part.get_filename()
        if not name:
            continue
        attach_dir.mkdir(parents=True, exist_ok=True)
        safe = re.sub(r'[\\/:*?"<>|\x00-\x1f]', "_", name).strip(" .") or "adjunto"
        (attach_dir / safe).write_bytes(part.get_payload(decode=True) or b"")
        names.append(safe)
    if names:
        head.append("**Adjuntos** (guardados en " + attach_dir.as_posix() + "; catalógalos si son relevantes): " + ", ".join(names))
    date = ""
    try:
        date = email.utils.parsedate_to_datetime(msg["Date"]).strftime("%Y-%m-%d %H:%M") if msg["Date"] else ""
    except (TypeError, ValueError):
        pass
    return "\n".join(head) + "\n\n" + text.strip(), f"correo «{msg.get('Subject', '')}»", date


def read_msg(path):
    try:
        import extract_msg
    except ImportError:
        return None, "no leído: falta el paquete extract-msg; guarda el correo como .eml o PDF desde Outlook", ""
    m = extract_msg.Message(str(path))
    head = [f"**{k}:** {v}" for k, v in (("De", m.sender), ("Para", m.to), ("CC", m.cc), ("Fecha", m.date), ("Asunto", m.subject)) if v]
    names = [getattr(a, "longFilename", None) or getattr(a, "shortFilename", "") for a in m.attachments]
    if any(names):
        head.append("**Adjuntos** (guárdalos desde Outlook para leerlos): " + ", ".join(n for n in names if n))
    return "\n".join(head) + "\n\n" + (m.body or "").strip(), f"correo «{m.subject or ''}»", str(m.date or "")


def read_bpmn(path):
    root = ET.parse(path).getroot()
    q = lambda t: f"{{{NS['bpmn']}}}{t}"
    lane_of = {}
    for lane in root.iter(q("lane")):
        for ref in lane.findall("bpmn:flowNodeRef", NS):
            lane_of[ref.text.strip()] = lane.get("name", "")
    pool_of = {p.get("processRef"): p.get("name", "") for p in root.iter(q("participant"))}
    kinds = {"task": "Tarea", "userTask": "Tarea de usuario", "serviceTask": "Tarea de servicio",
             "manualTask": "Tarea manual", "sendTask": "Envío", "receiveTask": "Recepción",
             "scriptTask": "Script", "businessRuleTask": "Regla de negocio", "callActivity": "Subproceso (llamada)",
             "subProcess": "Subproceso", "startEvent": "Inicio", "endEvent": "Fin",
             "intermediateCatchEvent": "Evento intermedio", "intermediateThrowEvent": "Evento intermedio",
             "boundaryEvent": "Evento de borde", "exclusiveGateway": "Decisión (XOR)",
             "parallelGateway": "Paralelo (AND)", "inclusiveGateway": "Decisión (OR)", "eventBasedGateway": "Decisión por evento"}
    out, names, nodes = [], {}, 0
    for proc in root.iter(q("process")):
        rows = [["ID", "Tipo", "Nombre", "Carril", "Documentación"]]
        for el in proc.iter():
            kind = el.tag.split("}")[-1]
            if kind in kinds and el.get("id"):
                names[el.get("id")] = el.get("name", "") or el.get("id")
                doc = el.find("bpmn:documentation", NS)
                rows.append([el.get("id"), kinds[kind], el.get("name", ""), lane_of.get(el.get("id"), ""),
                             (doc.text or "").strip() if doc is not None else ""])
        nodes += len(rows) - 1
        flows = [["Desde", "Hacia", "Etiqueta / condición"]]
        for f in proc.iter(q("sequenceFlow")):
            cond = f.find("bpmn:conditionExpression", NS)
            label = f.get("name", "") or ((cond.text or "").strip() if cond is not None else "")
            flows.append([names.get(f.get("sourceRef"), f.get("sourceRef")), names.get(f.get("targetRef"), f.get("targetRef")), label])
        title = proc.get("name") or pool_of.get(proc.get("id")) or proc.get("id")
        out.append(f"## Proceso «{title}»\n\n### Elementos\n\n{md_table(rows)}\n\n### Flujos\n\n{md_table(flows)}")
    msgs = [["Desde", "Hacia", "Mensaje"]] + [[f.get("sourceRef"), f.get("targetRef"), f.get("name", "")]
                                            for f in root.iter(q("messageFlow"))]
    if len(msgs) > 1:
        out.append("## Mensajes entre participantes\n\n" + md_table(msgs))
    return "\n\n".join(out), f"{nodes} elementos BPMN"


def drawio_pages(path):
    root = ET.parse(path).getroot()
    for d in root.iter("diagram"):
        model = d.find("mxGraphModel")
        if model is None and (d.text or "").strip():
            data = zlib.decompress(base64.b64decode(d.text.strip()), -15)
            model = ET.fromstring(urllib.parse.unquote(data.decode("utf-8")))
        if model is not None:
            yield d.get("name", ""), model
    if root.tag == "mxGraphModel":
        yield "", root


def read_drawio(path):
    out, total = [], 0
    for name, model in drawio_pages(path):
        cells = {c.get("id"): c for c in model.iter("mxCell")}
        label = lambda c: html_text(c.get("value") or "").replace("\n", " ") if c is not None else ""
        edge_ids = {i for i, c in cells.items() if c.get("edge") == "1"}
        nodes = [["Elemento"]] + [[label(c)] for c in cells.values()
                                  if c.get("vertex") == "1" and label(c) and c.get("parent") not in edge_ids]
        edges = [["Desde", "Hacia", "Etiqueta"]]
        for c in cells.values():
            if c.get("edge") == "1":
                txt = label(c) or " ".join(label(x) for x in cells.values() if x.get("parent") == c.get("id"))
                edges.append([label(cells.get(c.get("source"))) or "?", label(cells.get(c.get("target"))) or "?", txt])
        total += len(nodes) - 1
        out.append(f"## Página «{name}»\n\n### Elementos\n\n{md_table(nodes)}\n\n### Conexiones\n\n{md_table(edges)}")
    return "\n\n".join(out), f"{total} elementos"


def read_vsdx(path):
    z = zipfile.ZipFile(path)
    pages = sorted((n for n in z.namelist() if re.match(r"visio/pages/page\d+\.xml$", n)),
                   key=lambda n: int(re.search(r"(\d+)\.xml$", n).group(1)))
    out, total = [], 0
    for i, pg in enumerate(pages, 1):
        texts = []
        for t in ET.fromstring(z.read(pg)).iter(f"{{{NS['v']}}}Text"):
            s = re.sub(r"\s+", " ", "".join(t.itertext())).strip()
            if s:
                texts.append(s)
        total += len(texts)
        out.append(f"## Página {i}\n\n" + "\n".join(f"- {s}" for s in texts))
    return "\n\n".join(out), f"{total} textos (sin conexiones: para el flujo, exporta a PDF o PNG y revísalo visualmente)"


# ---------------------------------------------------------------- catálogo

def slug(s):
    s = re.sub(r"[^\w\-]+", "-", pathlib.Path(s).stem, flags=re.UNICODE).strip("-").lower()
    return s[:50] or "fuente"


def convert(path, out_dir, fid):
    ext = path.suffix.lower()
    date = datetime.datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d")
    try:
        if ext in (".vtt", ".srt"):
            body, detail = read_subtitles(path); kind = "Transcripción"
        elif ext in (".txt", ".md"):
            body = path.read_text(encoding="utf-8-sig", errors="replace"); kind = "Texto"
            detail = f"{body.count(chr(10)) + 1} líneas"
            turns = re.findall(r"^\[(\d{1,2}:\d{2}:\d{2})\] ([^:\n]{2,60}):\s*$", body, re.M)
            stamps = re.findall(r"^\[(\d{1,2}:\d{2}:\d{2})\]", body, re.M)
            if len(turns) >= 5:  # transcripción exportada (Teams, Stream, Otter…) con «[hh:mm:ss] Hablante:»
                kind = "Transcripción"
                detail = f"{len(turns)} intervenciones, {len({s for _, s in turns})} participantes"
            elif len(stamps) >= 5 or re.search(r"^Tipo de fuente:.*transcripci", body[:2000], re.I | re.M):
                # transcripción automática sin hablantes («[hh:mm:ss]» en su línea): duración de la cabecera o de la última marca
                kind = "Transcripción"
                dur = re.search(r"^Duración[^:\n]*:\s*(\d{1,2}:\d{2}(?::\d{2})?)", body[:2000], re.I | re.M)
                detail = f"duración {dur.group(1) if dur else (stamps[-1] if stamps else '¿?')}, sin hablantes identificados"
        elif ext == ".docx":
            body, detail = read_docx(path); kind = "Documento Word"
        elif ext == ".pptx":
            body, detail = read_pptx(path); kind = "Presentación"
        elif ext == ".xlsx":
            body, detail = read_xlsx(path); kind = "Hoja de cálculo"
        elif ext == ".pdf":
            body, detail = read_pdf(path); kind = "PDF"
        elif ext == ".eml":
            body, detail, d = read_eml(path, out_dir / "adjuntos" / fid); kind = "Correo"; date = d or date
        elif ext == ".msg":
            body, detail, d = read_msg(path); kind = "Correo"; date = d or date
        elif ext == ".bpmn":
            body, detail = read_bpmn(path); kind = "Diagrama BPMN"
        elif ext == ".drawio":
            body, detail = read_drawio(path); kind = "Diagrama draw.io"
        elif ext == ".vsdx":
            body, detail = read_vsdx(path); kind = "Diagrama Visio"
        elif ext in LEGACY:
            body, detail, kind = None, f"no leído: formato antiguo; guárdalo como {LEGACY[ext]}", ext[1:].upper()
        else:
            body, detail, kind = None, "imagen: revísala visualmente con Read", "Imagen"
    except Exception as e:  # noqa: BLE001 - un fichero dañado no debe parar el resto
        body, detail, kind = None, f"no leído: {type(e).__name__}: {e}", ext[1:].upper()
    m = re.search(r"(20\d{2})[-_]?(0[1-9]|1[0-2])[-_]?(0[1-9]|[12]\d|3[01])(?!\d)", path.name)
    if m and ext not in (".eml", ".msg"):  # fecha en el nombre (p. ej. grabaciones de Teams): mejor que la del fichero
        date = "-".join(m.groups())
    return body, kind, detail, date


SISTEMA = ("desktop.ini", "thumbs.db", ".ds_store")   # lo que dejan Windows y macOS en una carpeta


def una_fuente(carpeta):
    """Una carpeta como una sola fuente: (sus documentos, el .md con su índice, detalle, fecha). No entra su extracción
    en bruto (extraccion/), que el análisis no lee, ni lo que dejan el sistema y Office (desktop.ini, Thumbs.db,
    .DS_Store, ~$…), que cambiaría la fuente sin cambiar nada."""
    docs = sorted(f for f in carpeta.rglob("*") if f.is_file() and "extraccion" not in f.relative_to(carpeta).parts
                  and f.name.lower() not in SISTEMA and not f.name.startswith("~$"))
    rows = [["Documento", "Qué es"]]
    for f in docs:
        titulo = ""
        if f.suffix.lower() == ".md":
            m = re.search(r"^#\s+(.+)$", f.read_text(encoding="utf-8", errors="replace"), re.M)
            titulo = m.group(1).strip() if m else ""
        rows.append([f"{carpeta.name}/{f.relative_to(carpeta).as_posix()}", titulo or f.suffix[1:].upper()])
    body = ("Una sola fuente: lo que se cita de ella lleva su ID dentro de la cita («[FU-nn H-SEG-01]»).\n\n"
            "## Documentos\n\n" + md_table(rows))
    fecha = max((f.stat().st_mtime for f in docs), default=carpeta.stat().st_mtime)
    return docs, body, f"{len(docs)} documentos", datetime.datetime.fromtimestamp(fecha).strftime("%Y-%m-%d")


def generated(f, out):
    """Lo que escribe este script en la carpeta de salida (FU-xx-*.md, indice.*, adjuntos/): no es una fuente.
    Las fuentes originales pueden estar en esa misma carpeta (leer_fuentes.py fuentes/ -o fuentes/)."""
    f, out = f.resolve(), out.resolve()
    if (out / "adjuntos") in f.parents:
        return True
    return f.parent == out and (re.match(r"FU-\d+-.*\.md$", f.name) is not None or f.name in ("indice.md", "indice.json"))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="*")
    ap.add_argument("--una-fuente", action="append", default=[], metavar="CARPETA",
                    help="la carpeta entera como una sola fuente (as-is/), con el índice de sus documentos")
    ap.add_argument("-o", "--out", default="fuentes")
    a = ap.parse_args()
    if not a.inputs and not a.una_fuente:
        ap.error("indica los ficheros o carpetas, o --una-fuente <carpeta>")
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")

    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    state_file = out / "indice.json"
    state = json.loads(state_file.read_text(encoding="utf-8")) if state_file.exists() else {"fuentes": []}
    by_hash = {f["hash"]: f for f in state["fuentes"]}

    for carpeta in map(pathlib.Path, a.una_fuente):
        if not carpeta.is_dir():
            print(f"AVISO: no es una carpeta: {carpeta}", file=sys.stderr)
            continue
        carpeta = carpeta.resolve()
        docs, body, detail, date = una_fuente(carpeta)
        h = hashlib.sha1("\n".join(f"{d.relative_to(carpeta).as_posix()} {hashlib.sha1(d.read_bytes()).hexdigest()}"
                                   for d in docs).encode("utf-8")).hexdigest()
        nombre = carpeta.name + "/"
        if h in by_hash:   # la misma carpeta con lo mismo dentro; si cambia, es otra fuente, como un fichero
            print(f"= {by_hash[h]['id']} {nombre} (ya catalogada)")
            continue
        fid = f"FU-{len(state['fuentes']) + 1:02d}"
        entry = {"id": fid, "fichero": nombre, "tipo": "Carpeta", "detalle": detail, "fecha": date, "hash": h,
                 "salida": f"{fid}-{slug(carpeta.name)}.md"}
        (out / entry["salida"]).write_text(
            f"# {fid} · {nombre}\n\n- Tipo: Carpeta\n- Detalle: {detail}\n- Fecha: {date}\n\n---\n\n{body}\n",
            encoding="utf-8")
        state["fuentes"].append(entry)
        by_hash[h] = entry
        print(f"+ {fid} {nombre}: Carpeta, {detail}")

    files = []
    inputs = [x for inp in a.inputs for x in (sorted(glob.glob(inp)) if glob.has_magic(inp) and not pathlib.Path(inp).exists() else [inp])]
    for inp in inputs:
        p = pathlib.Path(inp)
        if p.is_dir():
            files += sorted(f for f in p.rglob("*") if f.is_file() and f.suffix.lower() in SUPPORTED | set(LEGACY)
                            and not generated(f, out))
        elif p.is_file():
            files.append(p)
        else:
            print(f"AVISO: no existe {inp}", file=sys.stderr)

    for f in files:
        if f.suffix.lower() not in SUPPORTED | set(LEGACY):
            print(f"AVISO: formato no soportado, se omite: {f.name}", file=sys.stderr)
            continue
        h = hashlib.sha1(f.read_bytes()).hexdigest()
        old = by_hash.get(h)
        if old and old["fichero"] != f.name:
            print(f"= {old['id']} {f.name} (mismo contenido que {old['fichero']})")
            continue
        if old and (old["salida"] or old["tipo"] == "Imagen"):
            print(f"= {old['id']} {f.name} (ya catalogada)")
            continue
        fid = old["id"] if old else f"FU-{len(state['fuentes']) + 1:02d}"  # reintento de una fuente no leída
        body, kind, detail, date = convert(f, out, fid)
        entry = {"id": fid, "fichero": f.name, "tipo": kind, "detalle": detail, "fecha": date, "hash": h,
                 "salida": f"{fid}-{slug(f.name)}.md" if body is not None else ""}
        if body is not None:
            gente = ""
            if kind == "Transcripción":  # para que comprobar.py vigile que sus nombres no pasan al análisis
                nombres = sorted({x.strip() for x in re.findall(r"^\[\d{1,2}:\d{2}:\d{2}\] ([^:\n\[\]]{2,60}):", body, re.M)})
                gente = f"- Participantes: {'; '.join(nombres) if nombres else 'sin identificar'}\n"
            (out / entry["salida"]).write_text(
                f"# {fid} · {f.name}\n\n- Tipo: {kind}\n- Detalle: {detail}\n- Fecha: {date}\n{gente}\n---\n\n{body}\n",
                encoding="utf-8")
        if old:
            state["fuentes"][state["fuentes"].index(old)] = entry
        else:
            state["fuentes"].append(entry)
        by_hash[h] = entry
        print(f"+ {fid} {f.name}: {kind}, {detail}")

    state_file.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    rows = [["ID", "Fichero", "Tipo", "Detalle", "Fecha", "Texto"]] + [
        [e["id"], e["fichero"], e["tipo"], e["detalle"], e["fecha"], e["salida"] or "—"] for e in state["fuentes"]]
    (out / "indice.md").write_text("# Fuentes del análisis\n\n" + md_table(rows) + "\n", encoding="utf-8")
    print(f"Índice: {out / 'indice.md'} ({len(state['fuentes'])} fuentes)")
    if not state["fuentes"]:
        print("ERROR: no se ha catalogado ninguna fuente: revisa las rutas y los formatos admitidos", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
