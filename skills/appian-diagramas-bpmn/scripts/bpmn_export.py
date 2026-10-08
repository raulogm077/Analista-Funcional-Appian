"""Exporta el proceso de un .drawio a BPMN 2.0 (XML con la parte de dibujo), para abrirlo en
Camunda Modeler, bpmn.io, Signavio u otra herramienta BPM. Usa las posiciones del .drawio.

Conserva: inicio con temporizador o con mensaje, tareas de usuario, de sistema, de script y manuales,
subproceso y llamada a otro proceso, flujo por defecto, plazos y errores como eventos de borde, participantes
externos con sus flujos de mensaje, notas unidas a su paso y los datos de Appian: el nodo (documentation), la
expresión del temporizador, el proceso llamado (calledElement) y la condición de cada flujo (conditionExpression)."""
import re
import sys
from xml.sax.saxutils import escape, quoteattr

sys.dont_write_bytecode = True  # sin __pycache__ en el plugin: no se escribe fuera del proyecto
import colocacion

ELEMENTO = {
    "inicio": "startEvent", "inicio_temporizador": "startEvent", "inicio_mensaje": "startEvent", "fin": "endEvent",
    "temporizador": "intermediateCatchEvent", "mensaje": "intermediateThrowEvent", "intermedio": "intermediateCatchEvent",
    "error": "intermediateCatchEvent",   # solo si no está en el borde de una tarea (validar lo avisa)
    "exclusiva": "exclusiveGateway", "paralela": "parallelGateway", "inclusiva": "inclusiveGateway",
    "tarea": "userTask", "sistema": "serviceTask", "script": "scriptTask", "manual": "manualTask",
    "subproceso": "subProcess", "llamada": "callActivity",
}
DEFINICION = {"temporizador": "<bpmn:timerEventDefinition/>", "inicio_temporizador": "<bpmn:timerEventDefinition/>",
              "mensaje": "<bpmn:messageEventDefinition/>", "inicio_mensaje": "<bpmn:messageEventDefinition/>",
              "error": "<bpmn:errorEventDefinition/>"}
TAREAS = {"tarea", "sistema", "script", "manual", "subproceso", "llamada"}
BORDE = ("temporizador", "mensaje", "intermedio", "error")   # eventos que, unidos a una tarea, van en su borde
MARGEN = 30  # cabecera del participante
# ISO 8601 (BPMN 2.0, 10.4.5): una duración va en timeDuration y una fecha y hora en timeDate; una repetición (R/…)
# o una expresión de Appian, en timeCycle
DURACION = re.compile(r"P(?=\d|T\d)(\d+Y)?(\d+M)?(\d+W)?(\d+D)?(T(?=\d)(\d+H)?(\d+M)?(\d+([.,]\d+)?S)?)?")
FECHA = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2}([.,]\d+)?)?(Z|[+-]\d{2}:?\d{2})?")


def _id(s):
    s = re.sub(r"[^A-Za-z0-9_.-]", "_", s)
    return s if re.match(r"[A-Za-z_]", s) else "_" + s


def _qname(s):
    """Nombre válido para calledElement (xsd:QName): sin espacios ni signos; las letras con tilde se conservan."""
    s = re.sub(r"[^\w.-]", "_", s.strip())
    return s if re.match(r"[^\W\d]", s) else "_" + s


def _temporizador(expresion):
    tipo = "timeDuration" if DURACION.fullmatch(expresion) else "timeDate" if FECHA.fullmatch(expresion) else "timeCycle"
    return (f'<bpmn:timerEventDefinition><bpmn:{tipo} xsi:type="bpmn:tFormalExpression">{escape(expresion)}'
            f'</bpmn:{tipo}></bpmn:timerEventDefinition>')


def _recorte(caja, p, q):
    """Punto donde el segmento p→q (p en el centro de la caja) sale de la caja."""
    x, y, w, h = caja
    cx, cy = x + w / 2, y + h / 2
    dx, dy = q[0] - cx, q[1] - cy
    if dx == 0 and dy == 0:
        return cx, cy
    t = min((w / 2) / abs(dx) if dx else float("inf"), (h / 2) / abs(dy) if dy else float("inf"))
    return cx + dx * t, cy + dy * t


def _ortogonal(ruta):
    """Añade un codo donde dos puntos seguidos no están en la misma horizontal ni vertical."""
    out = [ruta[0]]
    for q in ruta[1:]:
        p = out[-1]
        if abs(p[0] - q[0]) > 1 and abs(p[1] - q[1]) > 1:
            out.append((q[0], p[1]))
        out.append(q)
    return out


def _wps(ruta):
    return "".join(f'<di:waypoint x="{x:.0f}" y="{y:.0f}"/>' for x, y in ruta)


def exportar(proc, geo, destino):
    pasos = {p["id"]: p for p in proc["pasos"]}
    externos = list(proc.get("externos") or [])
    caja = {}
    for pid, (cx, cy, w, h) in geo["pasos"].items():
        caja[pid] = (cx - w / 2 + MARGEN, cy - h / 2, w, h)
    # un evento unido a una tarea con flujo discontinuo es un evento de borde: el error la interrumpe; un plazo o un
    # mensaje, no
    borde = {}
    for f in proc["flujos"]:
        if f["de"] in pasos and f["a"] in pasos and f.get("discontinuo") \
                and pasos[f["a"]]["tipo"] in BORDE \
                and pasos[f["de"]]["tipo"] in TAREAS and f["a"] not in borde:
            borde[f["a"]] = f["de"]
    en_tarea = {}
    for ev, tarea in borde.items():  # sobre el borde inferior de su tarea; si hay varios, de derecha a izquierda
        tx, ty, tw, th = caja[tarea]
        _, _, w, h = caja[ev]
        k = en_tarea[tarea] = en_tarea.get(tarea, -1) + 1
        caja[ev] = (tx + tw - w - 8 - k * (w + 6), ty + th - h / 2, w, h)
    puntos_de = geo["flujos"] + [[]] * max(0, len(proc["flujos"]) - len(geo["flujos"]))
    sal, ent, defecto = {}, {}, {}
    flujos, mensajes = [], []
    for f, pts in zip(proc["flujos"], puntos_de):
        if f["de"] in externos or f["a"] in externos:
            mensajes.append((f"Mensaje_{len(mensajes) + 1}", f))
            continue
        if f.get("discontinuo") and borde.get(f["a"]) == f["de"]:
            continue  # el evento de borde no lleva flujo de entrada
        fid = f"Flujo_{len(flujos) + 1}"
        flujos.append((fid, f, pts if f["de"] not in borde else []))
        sal.setdefault(f["de"], []).append(fid); ent.setdefault(f["a"], []).append(fid)
        if f.get("defecto"):
            defecto[f["de"]] = fid
    ext_id = {e: f"Externo_{i}" for i, e in enumerate(externos, 1)}

    proc_xml = []
    carriles = [c for c in proc["carriles"] if c in geo["carriles"]]
    if carriles:
        proc_xml.append('<bpmn:laneSet id="LaneSet_1">')
        for i, c in enumerate(carriles, 1):
            refs = "".join(f"<bpmn:flowNodeRef>{_id(p['id'])}</bpmn:flowNodeRef>" for p in proc["pasos"] if p["carril"] == c)
            proc_xml.append(f'<bpmn:lane id="Carril_{i}" name={quoteattr(c)}>{refs}</bpmn:lane>')
        proc_xml.append("</bpmn:laneSet>")
    for p in proc["pasos"]:
        tag, extra = ELEMENTO[p["tipo"]], ""
        if p["id"] in borde:
            tag = "boundaryEvent"
            extra = f' attachedToRef="{_id(borde[p["id"]])}" cancelActivity="{"true" if p["tipo"] == "error" else "false"}"'
        if p["id"] in defecto:
            extra += f' default="{defecto[p["id"]]}"'
        if p["tipo"] == "llamada" and p.get("proceso_llamado"):
            extra += f' calledElement={quoteattr(_qname(str(p["proceso_llamado"])))}'
        definicion = DEFINICION.get(p["tipo"], "")
        if p.get("temporizador") and p["tipo"] in ("temporizador", "inicio_temporizador"):
            definicion = _temporizador(str(p["temporizador"]))
        # en el orden del esquema: documentation, incoming, outgoing y la definición del evento
        dentro = (f"<bpmn:documentation>nodo {escape(str(p['nodo']))}</bpmn:documentation>" if p.get("nodo") else "") + \
            "".join(f"<bpmn:incoming>{x}</bpmn:incoming>" for x in ent.get(p["id"], [])) + \
            "".join(f"<bpmn:outgoing>{x}</bpmn:outgoing>" for x in sal.get(p["id"], [])) + definicion
        proc_xml.append(f'<bpmn:{tag} id="{_id(p["id"])}" name={quoteattr(p.get("nombre", ""))}{extra}>{dentro}</bpmn:{tag}>')
    for fid, f, _ in flujos:
        nombre = f' name={quoteattr(f["etiqueta"])}' if f.get("etiqueta") else ""
        flujo = f'<bpmn:sequenceFlow id="{fid}"{nombre} sourceRef="{_id(f["de"])}" targetRef="{_id(f["a"])}"'
        if f.get("condicion"):
            proc_xml.append(f'{flujo}><bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">{escape(str(f["condicion"]))}'
                            "</bpmn:conditionExpression></bpmn:sequenceFlow>")
        else:
            proc_xml.append(flujo + "/>")
    notas = list(zip(proc.get("notas") or [], geo.get("anotaciones") or []))
    for i, (n, _) in enumerate(notas, 1):
        proc_xml.append(f'<bpmn:textAnnotation id="Nota_{i}"><bpmn:text>{escape(n.get("texto", ""))}</bpmn:text></bpmn:textAnnotation>')
        proc_xml.append(f'<bpmn:association id="Asociacion_{i}" sourceRef="Nota_{i}" targetRef="{_id(n["paso"])}"/>')

    di = []
    x0 = min((geo["carriles"][c][2] for c in carriles), default=0)
    ancho = max((geo["carriles"][c][3] for c in carriles), default=0)
    if carriles:
        ys = [geo["carriles"][c][0] for c in carriles]
        fin = max(geo["carriles"][c][0] + geo["carriles"][c][1] for c in carriles)
        di.append(f'<bpmndi:BPMNShape id="Participante_di" bpmnElement="Participante" isHorizontal="true">'
                  f'<dc:Bounds x="{x0:.0f}" y="{min(ys):.0f}" width="{ancho + MARGEN:.0f}" height="{fin - min(ys):.0f}"/></bpmndi:BPMNShape>')
        for i, c in enumerate(carriles, 1):
            y, h, x, w, _ = geo["carriles"][c]
            di.append(f'<bpmndi:BPMNShape id="Carril_{i}_di" bpmnElement="Carril_{i}" isHorizontal="true">'
                      f'<dc:Bounds x="{x + MARGEN:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}"/></bpmndi:BPMNShape>')
    caja_ext = {}
    for e in externos:
        y, h, x, w, _ = geo["externos"][e]
        caja_ext[e] = (x, y, w + MARGEN, h)
        di.append(f'<bpmndi:BPMNShape id="{ext_id[e]}_di" bpmnElement="{ext_id[e]}" isHorizontal="true">'
                  f'<dc:Bounds x="{x:.0f}" y="{y:.0f}" width="{w + MARGEN:.0f}" height="{h:.0f}"/></bpmndi:BPMNShape>')
    for p in proc["pasos"]:
        x, y, w, h = caja[p["id"]]
        extra = ' isMarkerVisible="true"' if p["tipo"] == "exclusiva" else ""
        extra += ' isExpanded="false"' if p["tipo"] == "subproceso" else ""
        etiqueta = ""
        lado = geo.get("etiquetas", {}).get(p["id"])
        if lado and p.get("nombre") and p["id"] not in borde:   # la etiqueta, en el mismo lado que en el dibujo
            lw, lh = colocacion.ANCHO_ETIQUETA, colocacion.alto_texto(p["nombre"])
            ly = y - lh - 4 if lado == "arriba" else y + h + 4
            etiqueta = (f'<bpmndi:BPMNLabel><dc:Bounds x="{x + w / 2 - lw / 2:.0f}" y="{ly:.0f}" width="{lw}" '
                        f'height="{lh:.0f}"/></bpmndi:BPMNLabel>')
        di.append(f'<bpmndi:BPMNShape id="{_id(p["id"])}_di" bpmnElement="{_id(p["id"])}"{extra}>'
                  f'<dc:Bounds x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}"/>{etiqueta}</bpmndi:BPMNShape>')
    centro = lambda c: (c[0] + c[2] / 2, c[1] + c[3] / 2)
    for fid, f, puntos in flujos:
        a, b = caja[f["de"]], caja[f["a"]]
        medios = [(x + MARGEN, y) for x, y in puntos]
        (ax, ay), (bx, by) = centro(a), centro(b)
        if not medios and abs(ay - by) > 1 and abs(ax - bx) > 1:
            medios = [(bx, ay)]  # sin puntos en el .drawio: en ángulo recto, primero en horizontal
        ruta = _ortogonal([centro(a)] + medios + [centro(b)])
        ruta[0] = _recorte(a, ruta[0], ruta[1])
        ruta[-1] = _recorte(b, ruta[-1], ruta[-2])
        di.append(f'<bpmndi:BPMNEdge id="{fid}_di" bpmnElement="{fid}">{_wps(ruta)}</bpmndi:BPMNEdge>')
    fondo = max((geo["carriles"][c][0] + geo["carriles"][c][1] for c in carriles), default=0)
    for mid, f in mensajes:   # en vertical entre el paso y la franja del participante; etiqueta en el hueco
        paso = f["de"] if f["a"] in externos else f["a"]
        px, py, pw, ph = caja[paso]
        ex, ey, ew, eh = caja_ext[f["a"] if f["a"] in externos else f["de"]]
        x = px + pw / 2
        ruta = [(x, py + ph), (x, ey)] if f["a"] in externos else [(x, ey), (x, py + ph)]
        etiqueta = ""
        if f.get("etiqueta"):
            lh = colocacion.LINEA + 4
            hueco = (fondo + min(c[1] for c in caja_ext.values())) / 2
            etiqueta = (f'<bpmndi:BPMNLabel><dc:Bounds x="{x + 6:.0f}" y="{hueco - lh / 2:.0f}" width="120" '
                        f'height="{lh}"/></bpmndi:BPMNLabel>')
        di.append(f'<bpmndi:BPMNEdge id="{mid}_di" bpmnElement="{mid}">{_wps(ruta)}{etiqueta}</bpmndi:BPMNEdge>')
    for i, (n, (cx, cy, w, h)) in enumerate(notas, 1):
        x, y = cx - w / 2 + MARGEN, cy - h / 2
        di.append(f'<bpmndi:BPMNShape id="Nota_{i}_di" bpmnElement="Nota_{i}"><dc:Bounds x="{x:.0f}" y="{y:.0f}" '
                  f'width="{w:.0f}" height="{h:.0f}"/></bpmndi:BPMNShape>')
        px, py, pw, ph = caja[n["paso"]]
        a, b = max(x, px), min(x + w, px + pw)          # en vertical por donde se solapan, como en el dibujo
        lx = (a + b) / 2 if a < b else (px + 4 if x < px else px + pw - 4)
        ruta = [(lx, y + h), (lx, py)] if cy < py else [(lx, y), (lx, py + ph)]
        di.append(f'<bpmndi:BPMNEdge id="Asociacion_{i}_di" bpmnElement="Asociacion_{i}">{_wps(ruta)}</bpmndi:BPMNEdge>')

    nombre = proc.get("proceso") or "Proceso"
    participantes = f'<bpmn:participant id="Participante" name={quoteattr(nombre)} processRef="Proceso"/>' + \
        "".join(f'<bpmn:participant id="{ext_id[e]}" name={quoteattr(e)}/>' for e in externos)
    for mid, f in mensajes:
        de, a = ext_id.get(f["de"], _id(f["de"])), ext_id.get(f["a"], _id(f["a"]))
        nombre_m = f' name={quoteattr(f["etiqueta"])}' if f.get("etiqueta") else ""
        participantes += f'<bpmn:messageFlow id="{mid}"{nombre_m} sourceRef="{de}" targetRef="{a}"/>'
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
           'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" '
           'xmlns:di="http://www.omg.org/spec/DD/20100524/DI" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
           'id="Definiciones" targetNamespace="http://bpmn.io/schema/bpmn" '
           'exporter="appian-analisis-funcional" exporterVersion="3">\n'
           f'<bpmn:collaboration id="Colaboracion">{participantes}</bpmn:collaboration>\n'
           f'<bpmn:process id="Proceso" name={quoteattr(nombre)} isExecutable="false">\n' + "\n".join(proc_xml) + "\n</bpmn:process>\n"
           '<bpmndi:BPMNDiagram id="Diagrama"><bpmndi:BPMNPlane id="Plano" bpmnElement="Colaboracion">\n' + "\n".join(di) +
           "\n</bpmndi:BPMNPlane></bpmndi:BPMNDiagram>\n</bpmn:definitions>\n")
    with open(destino, "w", encoding="utf-8") as fh:
        fh.write(xml)
    return destino
