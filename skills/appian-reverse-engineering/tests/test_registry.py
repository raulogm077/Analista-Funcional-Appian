"""Pruebas del registro único de hallazgos (build_registry.py) y su uso en build_summary.py."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from conftest import ROOT

REG = ROOT / "scripts" / "build_registry.py"
SUM = ROOT / "scripts" / "build_summary.py"


def setup(tmp_path: Path):
    out = tmp_path / "appian-docs" / "DEM"
    work = tmp_path / "appian-docs" / "_trabajo" / "DEM"
    (out / "08-procesos-bpmn").mkdir(parents=True)
    (work / "hallazgos").mkdir(parents=True)
    (out / "08-procesos-bpmn" / "DEM_Alta_Solicitud.md").write_text("# Alta\n## Hallazgos\n")
    (out / "04-seguridad-grupos.md").write_text("# Seguridad\n")
    (out / "09-valor-adicional.md").write_text("# 09\n\n## Registro de hallazgos\n\n<!-- registro:inicio -->\n"
                                               "(lo rellena build_registry.py)\n<!-- registro:fin -->\n\n## Glosario\n")
    return out, work


def h(id_, **kw):
    base = {"id": id_, "titulo": "Cancelar no anula el alta", "area": "procesos", "severidad": "Alta",
            "certeza": "verificado", "documento": "08-procesos-bpmn/DEM_Alta_Solicitud.md#hallazgos",
            "evidencia": "mcp:processModel/DEM Alta Solicitud#nodes[id=1]"}
    base.update(kw)
    return base


def run(script, out):
    return subprocess.run([sys.executable, str(script), str(out)], capture_output=True, text=True)


def test_registry_fills_09_and_links_treatment(tmp_path):
    out, work = setup(tmp_path)
    (work / "hallazgos" / "process-modeler.json").write_text(json.dumps([h("H-PRO-01")]))
    (work / "hallazgos" / "integration-security-analyzer.json").write_text(json.dumps([
        h("H-SEG-01", titulo="Alta abierta a todos los usuarios", area="seguridad", severidad="Media",
          certeza="inferido", documento="04-seguridad-grupos.md#hallazgos", evidencia="mcp:processModel/X@other:roleMap"),
        h("H-SEG-02", titulo="Cancelar | no anula", duplicadoDe="H-PRO-01", documento="04-seguridad-grupos.md")]))
    (work / "modernizacion.json").write_text(json.dumps({"veredicto": "Refactorizar por fases",
        "mod": [{"id": "MOD-001", "hallazgos": ["H-PRO-01"]}], "pq": [{"id": "PQ-002", "hallazgos": ["H-SEG-01"]}]}))
    p = run(REG, out)
    assert p.returncode == 0, p.stderr
    t = (out / "09-valor-adicional.md").read_text()
    assert "| H-PRO-01 | Cancelar no anula el alta | procesos | Alta | ✅ |" in t and "MOD-001" in t
    assert "| H-SEG-01 |" in t and "🔵" in t and "PQ-002" in t
    assert "| H-SEG-02 |" not in t and "H-SEG-02 → H-PRO-01" in t        # fusionado, no se repite
    assert t.index("H-PRO-01 |") < t.index("H-SEG-01 |")                 # Alta antes que Media
    assert "## Glosario" in t and "(lo rellena" not in t
    assert run(REG, out).returncode == 0 and (out / "09-valor-adicional.md").read_text() == t   # idempotente
    reg = json.loads((work / "registro.json").read_text())
    assert reg["porSeveridad"] == {"Alta": 1, "Media": 1, "Baja": 0} and reg["veredicto"] == "Refactorizar por fases"
    # build_summary toma el registro (sin inventario: solo se comprueba la parte de hallazgos)
    (work / "inventory.json").write_text(json.dumps({"counts": {}, "objects": {}}))
    p = run(SUM, out)
    assert p.returncode == 0, p.stderr
    s = json.loads((work / "summary.json").read_text())
    assert [f["id"] for f in s["findings"]] == ["H-PRO-01", "H-SEG-01"]
    assert s["modernization"]["verdict"] == "Refactorizar por fases"


def test_registry_rejects_bad_entries(tmp_path):
    out, work = setup(tmp_path)
    (work / "hallazgos" / "a.json").write_text(json.dumps([
        h("H-PRO-01"), h("H-PRO-01"), h("PRO-2"), h("H-PRO-03", severidad="🔴"), h("H-PRO-04", certeza="seguro"),
        h("H-PRO-05", documento="no-existe.md"), h("H-PRO-06", evidencia=""), h("H-PRO-07", duplicadoDe="H-XXX-99")]))
    p = run(REG, out)
    assert p.returncode == 1
    for frag in ("repetido", "no sigue H-", "severidad", "certeza", "no existe en la salida", "sin evidencia",
                 "duplicadoDe 'H-XXX-99'"):
        assert frag in p.stderr, frag
    assert "(lo rellena" in (out / "09-valor-adicional.md").read_text()      # con errores no toca 09
