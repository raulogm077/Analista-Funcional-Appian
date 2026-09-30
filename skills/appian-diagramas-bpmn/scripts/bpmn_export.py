"""Exporta el proceso de un .drawio a BPMN 2.0 (XML con la parte de dibujo), para abrirlo en
Camunda Modeler, bpmn.io, Signavio u otra herramienta BPM. Usa las posiciones del .drawio."""
import re
from xml.sax.saxutils import quoteattr

ELEMENTO = {
    "inicio": "startEvent", "fin": "endEvent", "temporizador": "intermediateCatchEvent",
    "mensaje": "intermediateThrowEvent", "intermedio": "intermediateCatchEvent",
    "exclusiva": "exclusiveGateway", "paralela": "parallelGateway", "inclusiva": "inclusiveGateway",
    "tarea": "userTask", "sistema": "serviceTask", "manual": "manualTask", "subproceso": "subProcess",
}
DEFINICION = {"temporizador": "<bpmn:timerEventDefinition/>", "mensaje": "<bpmn:messageEventDefinition/>"}
MARGEN = 30  # cabecera del participante


def _id(s):
    s = re.sub(r"[^A-Za-z0-9_.-]", "_", s)
    return s if re.match(r"[A-Za-z_]", s) else "_" + s


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


def exportar(proc, geo, destino):
    pasos = {p["id"]: p for p in proc["pasos"]}
    caja = {}
    for pid, (cx, cy, w, h) in geo["pasos"].items():
        caja[pid] = (cx - w / 2 + MARGEN, cy - h / 2, w, h)
    # un temporizador o evento unido a una tarea con flujo discontinuo es un evento de borde (plazo que no la interrumpe)
    borde = {}
    for f in proc["flujos"]:
        if f.get("discontinuo") and pasos[f["a"]]["tipo"] in ("temporizador", "mensaje", "intermedio") \
                and pasos[f["de"]]["tipo"] in ("tarea", "sistema", "manual", "subproceso") and f["a"] not in borde:
            borde[f["a"]] = f["de"]
    for ev, tarea in borde.items():  # el evento se dibuja sobre el borde inferior de su tarea
        tx, ty, tw, th = caja[tarea]
        _, _, w, h = caja[ev]
        caja[ev] = (tx + tw - w - 8, ty + th - h / 2, w, h)
    puntos_de = geo["flujos"] + [[]] * max(0, len(proc["flujos"]) - len(geo["flujos"]))
    sal, ent = {}, {}
    flujos = []
    for f, pts in zip(proc["flujos"], puntos_de):
        if f.get("discontinuo") and borde.get(f["a"]) == f["de"]:
            continue  # el evento de borde no lleva flujo de entrada
        fid = f"Flujo_{len(flujos) + 1}"
        flujos.append((fid, f, pts if f["de"] not in borde else []))
        sal.setdefault(f["de"], []).append(fid); ent.setdefault(f["a"], []).append(fid)

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
            tag, extra = "boundaryEvent", f' attachedToRef="{_id(borde[p["id"]])}" cancelActivity="false"'
        dentro = "".join(f"<bpmn:incoming>{x}</bpmn:incoming>" for x in ent.get(p["id"], [])) + \
            "".join(f"<bpmn:outgoing>{x}</bpmn:outgoing>" for x in sal.get(p["id"], [])) + DEFINICION.get(p["tipo"], "")
        proc_xml.append(f'<bpmn:{tag} id="{_id(p["id"])}" name={quoteattr(p.get("nombre", ""))}{extra}>{dentro}</bpmn:{tag}>')
    for fid, f, _ in flujos:
        nombre = f' name={quoteattr(f["etiqueta"])}' if f.get("etiqueta") else ""
        proc_xml.append(f'<bpmn:sequenceFlow id="{fid}"{nombre} sourceRef="{_id(f["de"])}" targetRef="{_id(f["a"])}"/>')

    di = []
    if carriles:
        ys = [geo["carriles"][c][0] for c in carriles]
        fin = max(geo["carriles"][c][0] + geo["carriles"][c][1] for c in carriles)
        ancho = max(geo["carriles"][c][3] for c in carriles)
        x0 = min(geo["carriles"][c][2] for c in carriles)
        di.append(f'<bpmndi:BPMNShape id="Participante_di" bpmnElement="Participante" isHorizontal="true">'
                  f'<dc:Bounds x="{x0:.0f}" y="{min(ys):.0f}" width="{ancho + MARGEN:.0f}" height="{fin - min(ys):.0f}"/></bpmndi:BPMNShape>')
        for i, c in enumerate(carriles, 1):
            y, h, x, w, _ = geo["carriles"][c]
            di.append(f'<bpmndi:BPMNShape id="Carril_{i}_di" bpmnElement="Carril_{i}" isHorizontal="true">'
                      f'<dc:Bounds x="{x + MARGEN:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}"/></bpmndi:BPMNShape>')
    for p in proc["pasos"]:
        x, y, w, h = caja[p["id"]]
        extra = ' isMarkerVisible="true"' if p["tipo"] == "exclusiva" else ""
        extra += ' isExpanded="false"' if p["tipo"] == "subproceso" else ""
        di.append(f'<bpmndi:BPMNShape id="{_id(p["id"])}_di" bpmnElement="{_id(p["id"])}"{extra}>'
                  f'<dc:Bounds x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}"/></bpmndi:BPMNShape>')
    for fid, f, puntos in flujos:
        a, b = caja[f["de"]], caja[f["a"]]
        centro = lambda c: (c[0] + c[2] / 2, c[1] + c[3] / 2)
        medios = [(x + MARGEN, y) for x, y in puntos]
        (ax, ay), (bx, by) = centro(a), centro(b)
        if not medios and abs(ay - by) > 1 and abs(ax - bx) > 1:
            medios = [(bx, ay)]  # sin puntos en el .drawio: en ángulo recto, primero en horizontal
        ruta = _ortogonal([centro(a)] + medios + [centro(b)])
        ruta[0] = _recorte(a, ruta[0], ruta[1])
        ruta[-1] = _recorte(b, ruta[-1], ruta[-2])
        wps = "".join(f'<di:waypoint x="{x:.0f}" y="{y:.0f}"/>' for x, y in ruta)
        di.append(f'<bpmndi:BPMNEdge id="{fid}_di" bpmnElement="{fid}">{wps}</bpmndi:BPMNEdge>')

    nombre = proc.get("proceso") or "Proceso"
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
           'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" '
           'xmlns:di="http://www.omg.org/spec/DD/20100524/DI" id="Definiciones" targetNamespace="http://bpmn.io/schema/bpmn" '
           'exporter="appian-analisis-funcional" exporterVersion="1">\n'
           f'<bpmn:collaboration id="Colaboracion"><bpmn:participant id="Participante" name={quoteattr(nombre)} processRef="Proceso"/>'
           '</bpmn:collaboration>\n'
           f'<bpmn:process id="Proceso" name={quoteattr(nombre)} isExecutable="false">\n' + "\n".join(proc_xml) + "\n</bpmn:process>\n"
           '<bpmndi:BPMNDiagram id="Diagrama"><bpmndi:BPMNPlane id="Plano" bpmnElement="Colaboracion">\n' + "\n".join(di) +
           "\n</bpmndi:BPMNPlane></bpmndi:BPMNDiagram>\n</bpmn:definitions>\n")
    with open(destino, "w", encoding="utf-8") as fh:
        fh.write(xml)
    return destino
