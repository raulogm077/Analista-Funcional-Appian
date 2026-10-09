"""Pruebas de los scripts auxiliares: detect_secrets.sh."""
from __future__ import annotations

import shutil
import subprocess

import pytest

from conftest import SKILL

DS = SKILL / "scripts" / "detect_secrets.sh"


@pytest.mark.skipif(shutil.which("bash") is None, reason="detect_secrets.sh necesita bash")
def test_detect_secrets_files_and_dirs(tmp_path):
    d = tmp_path / "raw"
    d.mkdir()
    (d / "cs.json").write_text('{"baseUrl": "https://svc:P4ss@erp.example.org",\n "value": "sk_live_51Hc9fakeTOKEN",\n'
                               ' "password": "hunter2hunter2",\n "h": "Bearer abcdefghijklmnopqrstuvwxyz"}')
    clean = tmp_path / "05.md"
    clean.write_text("Constante: sk***\nURL base: https://***:***@erp.example.org/api\n")   # asteriscos: no es un secreto
    user_only = tmp_path / "06.md"
    user_only.write_text("URL base: https://svc_erp:***@erp.example.org/api\n")     # usuario visible: cuenta
    p = subprocess.run(["bash", str(DS), str(d), str(clean)], capture_output=True, text=True, encoding="utf-8")
    assert p.returncode == 1
    assert [f"cs.json#{k} |" in p.stdout for k in ("baseUrl", "value", "password", "h")] == [True] * 4   # dónde
    assert "05.md:" not in p.stdout
    assert subprocess.run(["bash", str(DS), str(clean)], capture_output=True).returncode == 0
    assert subprocess.run(["bash", str(DS), str(user_only)], capture_output=True).returncode == 1
    assert subprocess.run(["bash", str(DS), str(tmp_path / "nope")], capture_output=True).returncode == 2


@pytest.mark.skipif(shutil.which("bash") is None or shutil.which("dirname") is None or __import__("os").name == "nt",
                    reason="simula en macOS y Linux el Windows sin python3 (en Windows lo prueba la de arriba)")
def test_detect_secrets_sh_sin_python3(tmp_path):
    """En Windows solo hay «python», y «python3» puede ser el alias de la Microsoft Store, que no ejecuta nada: el
    envoltorio usa el primero que funcione."""
    import os
    import sys
    bin_ = tmp_path / "bin"
    bin_.mkdir()
    (bin_ / "python").symlink_to(sys.executable)
    (bin_ / "dirname").symlink_to(shutil.which("dirname"))
    stub = bin_ / "python3"   # como el alias de la tienda: existe, pero no es Python
    stub.write_text("#!/bin/sh\necho 'Python was not found' >&2\nexit 9\n")
    stub.chmod(0o755)
    d = tmp_path / "raw"
    d.mkdir()
    (d / "cs.json").write_text('{"value": "sk_live_51Hc9fakeTOKEN"}')
    p = subprocess.run([shutil.which("bash"), str(DS), str(d)], capture_output=True, text=True, encoding="utf-8",
                       env=dict(os.environ, PATH=str(bin_)))
    assert p.returncode == 1, p.stderr
    assert "cs.json#value |" in p.stdout
