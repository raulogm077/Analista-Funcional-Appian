"""Una pieza por capacidad: ingeniería inversa dibuja y exporta con la skill de diagramas.

Los procesos los dibuja y los exporta a BPMN appian-diagramas-bpmn (diagrama.py) y los diagramas Mermaid los valida y
los pinta su mermaid.py. Ingeniería inversa ya no lleva su exportador BPMN ni su pintor, ni los cita.
"""
from __future__ import annotations

import re
import subprocess
import sys

import pytest

from conftest import PLUGIN, SKILL

RETIRADOS = ("bpmn_layout", "validate_mermaid", "render_diagrams", "mmdc")
VIA_RETIRADA = re.compile(r"v[ií]a propia|\.bpmn \+ Mermaid", re.I)
TEXTOS = (".md", ".py", ".json", ".sh", ".txt", ".html")
DIAGRAMAS = "appian-diagramas-bpmn/scripts/"


def ficheros():
    return [f for f in sorted(SKILL.rglob("*")) if f.is_file() and f.suffix in TEXTOS and "__pycache__" not in f.parts]


def test_sin_exportador_ni_pintor_propios():
    for nombre in ("bpmn_layout.py", "validate_mermaid.py", "render_diagrams.sh"):
        assert not (SKILL / "scripts" / nombre).exists(), nombre


def test_ningun_fichero_cita_la_via_retirada():
    citas = []
    for f in ficheros():
        for n, linea in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if any(r in linea for r in RETIRADOS) or VIA_RETIRADA.search(linea):
                citas.append(f"{f.relative_to(SKILL).as_posix()}:{n}: {linea.strip()[:100]}")
    assert not citas, "\n".join(citas)


def test_dibuja_con_la_skill_de_diagramas():
    """process-modeler dibuja con diagrama.py crear y exporta con diagrama.py bpmn; la fase 5 valida con mermaid.py --md.
    Las órdenes apuntan a scripts que existen."""
    modeler = (SKILL / "agents" / "process-modeler.md").read_text(encoding="utf-8")
    skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    assert re.search(r"diagrama\.py\b[^`\n]*\bcrear\b", modeler) and re.search(r"diagrama\.py\b[^`\n]*\bbpmn\b", modeler)
    assert "mermaid.py" in skill and "--md" in skill
    for f in ficheros():
        for m in re.finditer(re.escape(DIAGRAMAS) + r"([\w.-]+)", f.read_text(encoding="utf-8")):
            assert (PLUGIN / "skills" / "appian-diagramas-bpmn" / "scripts" / m.group(1)).is_file(), (f.name, m.group(0))


def test_ejemplos_de_mermaid_rules():
    """Los bloques mermaid de mermaid-rules.md son Mermaid válido y caben en una página (los «Mal» van como texto).
    Lo comprueba el pintor de la skill de diagramas, que necesita un navegador: sin él, la prueba se salta."""
    pintor = PLUGIN / "skills" / "appian-diagramas-bpmn" / "scripts" / "mermaid.py"
    p = subprocess.run([sys.executable, str(pintor), "--md", str(SKILL / "references" / "mermaid-rules.md")],
                       capture_output=True, text=True, encoding="utf-8")
    if p.returncode == 2:
        pytest.skip("sin navegador para mermaid.py: " + (p.stdout + p.stderr).strip().splitlines()[0])
    assert p.returncode == 0 and "px de ancho" not in p.stdout, p.stdout + p.stderr
