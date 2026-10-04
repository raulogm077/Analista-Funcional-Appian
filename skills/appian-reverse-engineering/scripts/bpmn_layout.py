#!/usr/bin/env python3
"""bpmn_layout.py - Añade a un .bpmn semántico lo que necesitan los modeladores para dibujarlo.

Camunda Modeler y bpmn.io (bpmn-js) solo dibujan lo que tiene coordenadas (BPMN DI). Este script:
  1. completa <bpmn:incoming>/<bpmn:outgoing> en cada nodo a partir de los sequenceFlow;
  2. crea la colaboración y el pool si el proceso tiene carriles y no los tenía;
  3. calcula un layout de izquierda a derecha por capas, con un carril por lane, y escribe el
     <bpmndi:BPMNDiagram> (sustituye el que hubiera, así que se puede repetir).

Uso:
  python3 scripts/bpmn_layout.py <fichero.bpmn | carpeta> [...]

Solo librería estándar. Salida: 0 bien, 1 algún fichero no se pudo procesar, 2 uso.
"""
from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

NS = {
    "bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL",
    "bpmndi": "http://www.omg.org/spec/BPMN/20100524/DI",
    "dc": "http://www.omg.org/spec/DD/20100524/DC",
    "di": "http://www.omg.org/spec/DD/20100524/DI",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}
for _p, _u in NS.items():
    ET.register_namespace(_p, _u)
B = "{%s}" % NS["bpmn"]
BDI = "{%s}" % NS["bpmndi"]
DC = "{%s}" % NS["dc"]
DI = "{%s}" % NS["di"]

EVENTS = {"startEvent", "endEvent", "intermediateCatchEvent", "intermediateThrowEvent", "boundaryEvent"}
GATEWAYS = {"exclusiveGateway", "inclusiveGateway", "parallelGateway", "eventBasedGateway", "complexGateway"}
ACTIVITIES = {"task", "userTask", "serviceTask", "scriptTask", "sendTask", "receiveTask", "manualTask",
              "businessRuleTask", "callActivity", "subProcess", "transaction", "adHocSubProcess"}
FLOW_NODES = EVENTS | GATEWAYS | ACTIVITIES
SIZE = {**{t: (36, 36) for t in EVENTS}, **{t: (50, 50) for t in GATEWAYS}, **{t: (100, 80) for t in ACTIVITIES}}
HEAD_CHILDREN = {"documentation", "extensionElements", "auditing", "monitoring", "categoryValueRef"}

COL_W, ROW_H, POOL_LABEL, LANE_LABEL, MARGIN_X, PAD_Y = 160, 110, 30, 30, 50, 15
BLACKBOX_H, GAP = 80, 40


def local(el: ET.Element) -> str:
    return el.tag.split("}", 1)[-1]


def add_refs(process: ET.Element) -> None:
    """Completa incoming/outgoing de cada nodo (el esquema BPMN los coloca tras documentation)."""
    nodes = {n.get("id"): n for n in process if local(n) in FLOW_NODES}
    inc, out = defaultdict(list), defaultdict(list)
    for f in process.findall(B + "sequenceFlow"):
        out[f.get("sourceRef")].append(f.get("id"))
        inc[f.get("targetRef")].append(f.get("id"))
    for nid, n in nodes.items():
        for old in n.findall(B + "incoming") + n.findall(B + "outgoing"):
            n.remove(old)
        pos = 0
        for i, ch in enumerate(list(n)):
            if local(ch) in HEAD_CHILDREN:
                pos = i + 1
        new = []
        for fid in inc.get(nid, []):
            e = ET.Element(B + "incoming"); e.text = fid; new.append(e)
        for fid in out.get(nid, []):
            e = ET.Element(B + "outgoing"); e.text = fid; new.append(e)
        for k, e in enumerate(new):
            n.insert(pos + k, e)


def layers(process: ET.Element) -> tuple[dict[str, int], set[str]]:
    """Capa de cada nodo (camino más largo sin contar retrocesos) e ids de flujos que retroceden."""
    nodes = [n.get("id") for n in process if local(n) in FLOW_NODES and local(n) != "boundaryEvent"]
    host = {n.get("id"): n.get("attachedToRef") for n in process if local(n) == "boundaryEvent"}
    adj = defaultdict(list)
    for f in process.findall(B + "sequenceFlow"):
        s, t = host.get(f.get("sourceRef"), f.get("sourceRef")), f.get("targetRef")
        adj[s].append((t, f.get("id")))
    indeg = defaultdict(int)
    for s in adj:
        for t, _ in adj[s]:
            indeg[t] += 1
    back, state = set(), {}
    order: list[str] = []

    def dfs(u: str) -> None:
        stack = [(u, iter(adj[u]))]
        state[u] = 1
        while stack:
            v, it = stack[-1]
            nxt = next(it, None)
            if nxt is None:
                state[v] = 2
                order.append(v)
                stack.pop()
                continue
            t, fid = nxt
            if state.get(t) == 1:
                back.add(fid)
            elif t not in state:
                state[t] = 1
                stack.append((t, iter(adj[t])))

    for u in [n for n in nodes if indeg[n] == 0] + nodes:
        if u not in state:
            dfs(u)
    layer = {n: 0 for n in nodes}
    for u in reversed(order):
        for t, fid in adj[u]:
            if fid not in back and t in layer:
                layer[t] = max(layer[t], layer.get(u, 0) + 1)
    return layer, back


def leaf_lanes(process: ET.Element) -> list[ET.Element]:
    out = []

    def walk(ls: ET.Element) -> None:
        for lane in ls.findall(B + "lane"):
            child = lane.find(B + "childLaneSet")
            if child is not None and child.findall(B + "lane"):
                walk(child)
            else:
                out.append(lane)
    for ls in process.findall(B + "laneSet"):
        walk(ls)
    return out


def bounds(parent: ET.Element, x: float, y: float, w: float, h: float) -> None:
    ET.SubElement(parent, DC + "Bounds", x=str(round(x)), y=str(round(y)), width=str(round(w)), height=str(round(h)))


def waypoint(parent: ET.Element, x: float, y: float) -> None:
    ET.SubElement(parent, DI + "waypoint", x=str(round(x)), y=str(round(y)))


def blocking(shapes: dict, kinds: dict, flow: ET.Element, x1: float, x2: float, y1: float, y2: float) -> list:
    """Nodos (distintos del origen y destino) que se cruzan con el tramo recto de un flujo."""
    out = []
    for nid, (x, y, w, h) in shapes.items():
        if nid not in kinds or nid in (flow.get("sourceRef"), flow.get("targetRef")):
            continue
        if x < x2 and x + w > x1 and y <= y2 + 1 and y + h >= y1 - 1:
            out.append((y, h))
    return out


def layout_file(path: Path) -> str:
    tree = ET.parse(path)
    root = tree.getroot()
    for old in root.findall(BDI + "BPMNDiagram"):
        root.remove(old)
    processes = root.findall(B + "process")
    collab = root.find(B + "collaboration")
    if collab is None and any(p.findall(B + "laneSet") for p in processes):
        collab = ET.Element(B + "collaboration", id=f"Collaboration_{processes[0].get('id')}")
        for p in processes:
            ET.SubElement(collab, B + "participant", id=f"Participant_{p.get('id')}", name=p.get("name") or p.get("id"),
                          processRef=p.get("id"))
        root.insert(list(root).index(processes[0]), collab)
    diagram = ET.SubElement(root, BDI + "BPMNDiagram", id=f"BPMNDiagram_{path.stem}")
    plane = ET.SubElement(diagram, BDI + "BPMNPlane", id=f"BPMNPlane_{path.stem}",
                          bpmnElement=(collab.get("id") if collab is not None else processes[0].get("id")))
    shapes: dict[str, tuple[float, float, float, float]] = {}
    y0 = 0.0
    pool_of = {p.get("processRef"): p for p in (collab.findall(B + "participant") if collab is not None else [])}
    total_w = 0.0
    for proc in processes:
        add_refs(proc)
        layer, back = layers(proc)
        n_layers = (max(layer.values()) + 1) if layer else 1
        lanes = leaf_lanes(proc)
        lane_of = {}
        for lane in lanes:
            for ref in lane.findall(B + "flowNodeRef"):
                lane_of.setdefault(ref.text.strip(), lane.get("id"))
        lane_ids = [lane.get("id") for lane in lanes] or ["_unico"]
        rows = defaultdict(lambda: defaultdict(list))
        kinds = {}
        for n in proc:
            k = local(n)
            if k in FLOW_NODES and k != "boundaryEvent":
                nid = n.get("id")
                kinds[nid] = k
                rows[lane_of.get(nid, lane_ids[0])][layer.get(nid, 0)].append(nid)
        pool = pool_of.get(proc.get("id"))
        x_left = POOL_LABEL + (LANE_LABEL if lanes else 0) if pool is not None else 0
        width = x_left + MARGIN_X * 2 + n_layers * COL_W
        total_w = max(total_w, width)
        y = y0
        lane_box = {}
        for lid in lane_ids:
            n_rows = max([len(v) for v in rows[lid].values()] or [1])
            h = max(n_rows * ROW_H + 2 * PAD_Y, 2 * ROW_H if pool is not None else ROW_H)
            lane_box[lid] = (y, h)
            for lay, ids in rows[lid].items():
                for r, nid in enumerate(ids):
                    w, hh = SIZE[kinds[nid]]
                    cx = x_left + MARGIN_X + lay * COL_W + COL_W / 2
                    cy = y + PAD_Y + r * ROW_H + ROW_H / 2 + (h - 2 * PAD_Y - n_rows * ROW_H) / 2
                    shapes[nid] = (cx - w / 2, cy - hh / 2, w, hh)
            y += h
        pool_h = y - y0
        if pool is not None:
            s = ET.SubElement(plane, BDI + "BPMNShape", id=f"{pool.get('id')}_di", bpmnElement=pool.get("id"), isHorizontal="true")
            bounds(s, 0, y0, width, pool_h)
            shapes[pool.get("id")] = (0, y0, width, pool_h)
            for lane in lanes:
                ly, lh = lane_box[lane.get("id")]
                s = ET.SubElement(plane, BDI + "BPMNShape", id=f"{lane.get('id')}_di", bpmnElement=lane.get("id"), isHorizontal="true")
                bounds(s, POOL_LABEL, ly, width - POOL_LABEL, lh)
        for nid, (x, yy, w, h) in shapes.items():
            if nid in kinds:
                attrs = {"id": f"{nid}_di", "bpmnElement": nid}
                if kinds[nid] == "exclusiveGateway":
                    attrs["isMarkerVisible"] = "true"
                if kinds[nid] in ("subProcess", "transaction", "adHocSubProcess"):
                    attrs["isExpanded"] = "false"
                bounds(ET.SubElement(plane, BDI + "BPMNShape", **attrs), x, yy, w, h)
        for n in proc:
            if local(n) == "boundaryEvent" and n.get("attachedToRef") in shapes:
                hx, hy, hw, hh = shapes[n.get("attachedToRef")]
                shapes[n.get("id")] = (hx + hw - 28, hy + hh - 18, 36, 36)
                bounds(ET.SubElement(plane, BDI + "BPMNShape", id=f"{n.get('id')}_di", bpmnElement=n.get("id")),
                       *shapes[n.get("id")])
        bottom = max((yy + h for nid, (x, yy, w, h) in shapes.items() if nid in kinds), default=y0) + 25
        for f in proc.findall(B + "sequenceFlow"):
            s_, t_ = shapes.get(f.get("sourceRef")), shapes.get(f.get("targetRef"))
            if not s_ or not t_:
                continue
            e = ET.SubElement(plane, BDI + "BPMNEdge", id=f"{f.get('id')}_di", bpmnElement=f.get("id"))
            sx, sy = s_[0] + s_[2], s_[1] + s_[3] / 2
            tx, ty = t_[0], t_[1] + t_[3] / 2
            if f.get("id") in back or tx <= sx:
                scx, tcx = s_[0] + s_[2] / 2, t_[0] + t_[2] / 2
                for px, py in ((scx, s_[1] + s_[3]), (scx, bottom), (tcx, bottom), (tcx, t_[1] + t_[3])):
                    waypoint(e, px, py)
            elif blocking(shapes, kinds, f, sx, tx, min(sy, ty), max(sy, ty)):
                # el tramo recto pisaría otros nodos: se rodea por debajo de ellos
                low = max(yy + h for yy, h in blocking(shapes, kinds, f, sx, tx, min(sy, ty), max(sy, ty))) + 20
                scx, tcx = s_[0] + s_[2] / 2, t_[0] + t_[2] / 2
                for px, py in ((scx, s_[1] + s_[3]), (scx, low), (tcx, low), (tcx, t_[1] + t_[3])):
                    waypoint(e, px, py)
            elif abs(sy - ty) < 1:
                waypoint(e, sx, sy); waypoint(e, tx, ty)
            else:
                mx = sx + (tx - sx) / 2
                for px, py in ((sx, sy), (mx, sy), (mx, ty), (tx, ty)):
                    waypoint(e, px, py)
        y0 = y + GAP
    if collab is not None:
        for part in collab.findall(B + "participant"):
            if part.get("processRef"):
                continue
            s = ET.SubElement(plane, BDI + "BPMNShape", id=f"{part.get('id')}_di", bpmnElement=part.get("id"), isHorizontal="true")
            bounds(s, 0, y0, total_w, BLACKBOX_H)
            shapes[part.get("id")] = (0, y0, total_w, BLACKBOX_H)
            y0 += BLACKBOX_H + GAP
        for mf in collab.findall(B + "messageFlow"):
            s_, t_ = shapes.get(mf.get("sourceRef")), shapes.get(mf.get("targetRef"))
            if not s_ or not t_:
                continue
            e = ET.SubElement(plane, BDI + "BPMNEdge", id=f"{mf.get('id')}_di", bpmnElement=mf.get("id"))
            sx = s_[0] + s_[2] / 2 if s_[2] < 200 else t_[0] + t_[2] / 2
            tx = t_[0] + t_[2] / 2 if t_[2] < 200 else sx
            if s_[1] < t_[1]:
                waypoint(e, sx, s_[1] + s_[3]); waypoint(e, tx, t_[1])
            else:
                waypoint(e, sx, s_[1]); waypoint(e, tx, t_[1] + t_[3])
    ET.indent(tree, space="  ")
    tree.write(path, encoding="UTF-8", xml_declaration=True)
    n_shapes = len(plane.findall(BDI + "BPMNShape"))
    n_edges = len(plane.findall(BDI + "BPMNEdge"))
    return f"{path.name}: {n_shapes} formas, {n_edges} conexiones"


def main(args: list[str]) -> int:
    if not args:
        print(__doc__, file=sys.stderr)
        return 2
    files: list[Path] = []
    for a in args:
        p = Path(a)
        files += sorted(p.rglob("*.bpmn")) if p.is_dir() else [p]
    code = 0
    for f in files:
        try:
            print(layout_file(f))
        except Exception as ex:  # noqa: BLE001
            print(f"ERROR {f}: {type(ex).__name__}: {ex}", file=sys.stderr)
            code = 1
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
