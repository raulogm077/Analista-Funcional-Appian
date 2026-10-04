"""Pruebas de los scripts auxiliares: validate_mermaid.py y detect_secrets.sh."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VM = ROOT / "scripts" / "validate_mermaid.py"
DS = ROOT / "scripts" / "detect_secrets.sh"


def vm(text: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(VM), "-"], input=text, capture_output=True, text=True)


def test_rules_examples_are_valid():
    p = subprocess.run([sys.executable, str(VM), "--check", str(ROOT / "references" / "mermaid-rules.md")],
                       capture_output=True, text=True)
    assert p.returncode == 0, p.stderr


def test_type_b_er():
    ok = "erDiagram\n  SOLICITUD }o--|| ESTADO : \"tiene\"\n  SOLICITUD {\n    int id PK\n    int estadoId FK\n  }\n  ESTADO {\n    int id PK\n    string label\n  }\n"
    p = vm(ok)
    assert p.returncode == 0 and p.stdout.strip() == ok.strip()
    assert vm("erDiagram\n  mi-entidad ||--o{ OTRA : \"x\"\n").returncode == 1
    assert vm("erDiagram\n  A {\n    int id PK\n").returncode == 1


def test_type_c_lanes():
    ok = ('flowchart LR\n  subgraph LG["Gestor"]\n    Start((Inicio)):::startNode\n    Form[Rellenar]:::userTask\n  end\n'
          '  subgraph LS["Sistema"]\n    EndOk(((Fin))):::endNode\n  end\n  Start --> Form --> EndOk\n'
          '  classDef startNode fill:#a8e6cf\n  classDef userTask fill:#fff4d2\n  classDef endNode fill:#ffd3b6\n')
    p = vm(ok)
    assert p.returncode == 0 and "Start((Inicio))" in p.stdout      # no renombra IDs
    assert vm(ok.replace("  end\n  subgraph LS", "  subgraph LS")).returncode == 1   # subgraph sin cerrar
    assert vm(ok.replace("EndOk", "end")).returncode == 1


def test_type_a_layers_limit_30():
    nodes = "\n".join(f'    N{i}["Objeto {i}"]' for i in range(1, 29))
    ok = f'flowchart LR\n  subgraph CP["Presentación"]\n{nodes}\n  end\n  N1 --> N2\n'
    p = vm(ok)
    assert p.returncode == 0 and "BPMN" not in p.stderr                 # 28 nodos por capas: válido, sin aviso BPMN
    assert vm(ok + "  N29 --> N30\n  N31 --> N1\n").returncode == 1     # 31 nodos: supera el límite de tipo A


def test_type_a_still_sanitized():
    p = vm('flowchart TD\n  A["Uno"] --> B["Dos"]\n')
    assert p.returncode == 0 and "N1" in p.stdout


def test_detect_secrets_files_and_dirs(tmp_path):
    d = tmp_path / "raw"
    d.mkdir()
    (d / "cs.json").write_text('{"baseUrl": "https://svc:P4ss@erp.example.org",\n "value": "sk_live_51Hc9fakeTOKEN",\n'
                               ' "password": "hunter2hunter2",\n "h": "Bearer abcdefghijklmnopqrstuvwxyz"}')
    clean = tmp_path / "05.md"
    clean.write_text("Constante enmascarada: sk***\nURL base: https://***:***@erp.example.org/api\n")
    user_only = tmp_path / "06.md"
    user_only.write_text("URL base: https://svc_erp:***@erp.example.org/api\n")     # usuario visible: cuenta
    p = subprocess.run(["bash", str(DS), str(d), str(clean)], capture_output=True, text=True)
    assert p.returncode == 1
    for secret in ("P4ss", "sk_live", "hunter2", "abcdefghijklmnop"):
        assert secret not in p.stdout, secret
    assert p.stdout.count("[VALOR ENMASCARADO]") >= 4
    assert subprocess.run(["bash", str(DS), str(clean)], capture_output=True).returncode == 0
    assert subprocess.run(["bash", str(DS), str(user_only)], capture_output=True).returncode == 1
    assert subprocess.run(["bash", str(DS), str(tmp_path / "nope")], capture_output=True).returncode == 2
