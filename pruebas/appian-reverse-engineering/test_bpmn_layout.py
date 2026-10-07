"""Pruebas de bpmn_layout.py: el .bpmn queda dibujable (DI completo) y el script es repetible."""
from __future__ import annotations

import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from conftest import DATOS, SKILL

LAYOUT = SKILL / "scripts" / "bpmn_layout.py"
FIXTURE = DATOS / "proceso_semantico.bpmn"
NS = {"bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL", "bpmndi": "http://www.omg.org/spec/BPMN/20100524/DI",
      "dc": "http://www.omg.org/spec/DD/20100524/DC", "di": "http://www.omg.org/spec/DD/20100524/DI"}


def run(path):
    p = subprocess.run([sys.executable, str(LAYOUT), str(path)], capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    return ET.parse(path).getroot()


def test_layout_adds_full_di(tmp_path):
    f = tmp_path / "p.bpmn"
    shutil.copy(FIXTURE, f)
    root = run(f)
    proc = root.find("bpmn:process", NS)
    collab = root.find("bpmn:collaboration", NS)
    assert collab is not None and collab.find("bpmn:participant", NS).get("processRef") == "P"   # pool creado por los carriles
    plane = root.find("bpmndi:BPMNDiagram/bpmndi:BPMNPlane", NS)
    assert plane.get("bpmnElement") == collab.get("id")
    shaped = {s.get("bpmnElement") for s in plane.findall("bpmndi:BPMNShape", NS)}
    nodes = {n.get("id") for n in proc if n.tag.split("}")[1] in ("startEvent", "userTask", "exclusiveGateway",
                                                                    "serviceTask", "boundaryEvent", "endEvent")}
    assert nodes | {"L_Rev", "L_Sis"} <= shaped
    edges = {e.get("bpmnElement"): e for e in plane.findall("bpmndi:BPMNEdge", NS)}
    assert set(edges) == {f.get("id") for f in proc.findall("bpmn:sequenceFlow", NS)}
    assert all(len(e.findall("di:waypoint", NS)) >= 2 for e in edges.values())
    g = proc.find("bpmn:exclusiveGateway[@id='G']", NS)
    assert [x.text for x in g.findall("bpmn:incoming", NS)] == ["F2"]
    assert sorted(x.text for x in g.findall("bpmn:outgoing", NS)) == ["F_no", "F_si"]
    start = proc.find("bpmn:startEvent", NS)
    assert [c.tag.split("}")[1] for c in start] == ["documentation", "outgoing"]   # orden del esquema
    # el retroceso (No -> Revisar) se dibuja por fuera, no atraviesa nodos
    assert len(edges["F_no"].findall("di:waypoint", NS)) == 4
    # Revisar va en el carril de Revisores (arriba) y Guardar en Sistema
    y = {s.get("bpmnElement"): float(s.find("dc:Bounds", NS).get("y")) for s in plane.findall("bpmndi:BPMNShape", NS)}
    assert y["T_Rev"] < y["L_Sis"] <= y["T_Ok"]
    assert "xsi:type=\"bpmn:tFormalExpression\"" in f.read_text(encoding="utf-8")


def test_layout_is_repeatable(tmp_path):
    f = tmp_path / "p.bpmn"
    shutil.copy(FIXTURE, f)
    run(f)
    first = f.read_text(encoding="utf-8")
    run(f)
    assert f.read_text(encoding="utf-8") == first
    assert first.count("<bpmndi:BPMNDiagram") == 1
