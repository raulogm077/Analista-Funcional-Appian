"""Solo lectura y secretos: lo que la extracción nunca usa, escriba como se escriba, y lo que el detector no cuenta."""
from __future__ import annotations

import subprocess
import sys

import pytest

from conftest import SKILL

SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))
import build_model  # noqa: E402
from devmcp_extract import DEFAULT_POLICY, Policy  # noqa: E402

POL = Policy(DEFAULT_POLICY)


@pytest.mark.parametrize("nombre", [
    "list_users", "get_user_details", "listUsers", "list_record_data", "get_record_data", "queryRecordType",
    "queryRecords", "getRecords", "getRecord", "searchRecords", "getRecordTypeData", "getProcessVariables",
    "get_process_variables", "getTaskData", "queryEntity", "run_sql_query", "getCredentials", "get_api_token"])
def test_herramientas_de_datos_excluidas(nombre):
    ok, motivo, _ = POL.safety(nombre, None, True)   # también en modo de confianza
    assert not ok, (nombre, motivo)


@pytest.mark.parametrize("nombre", [
    "getRecordType", "listRecordTypes", "searchRecordTypes", "getRecordTypeFields", "getRecordActions",
    "getGroupMembers", "getProcessModel", "getProcessHistory", "getInterface", "getObjectDependents"])
def test_herramientas_de_metadatos_permitidas(nombre):
    assert POL.safety(nombre, None, True)[0], nombre


@pytest.mark.parametrize("nombre", ["testInterface", "test_interface", "render_interface", "previewInterface"])
def test_render_reconocido_escriba_como_se_escriba(nombre):
    ok, _, rol = POL.safety(nombre, None, True)
    assert ok and rol == "screen"


def test_detector_sin_falsos_positivos(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text('password: cons!DEM_PASSWORD\n"token": "=ri!token"\n"tokenUrl": "https://x/oauth"\n'
                 'https://***:***@host\n', encoding="utf-8")
    assert subprocess.run([sys.executable, str(SCRIPTS / "detect_secrets.py"), str(f)],
                          capture_output=True).returncode == 0
    f.write_text('{"clientSecret": "xyzw9876"}\n', encoding="utf-8")
    p = subprocess.run([sys.executable, str(SCRIPTS / "detect_secrets.py"), str(f)], capture_output=True, text=True)
    assert p.returncode == 1 and f"{f}:1" in p.stdout                     # dice dónde está


def test_slugs_que_chocan():
    objs = [{"type": "processModel", "slug": "DEM_Alta", "uuid": "aaaa1111-x"},
            {"type": "processModel", "slug": "dem_alta", "uuid": "bbbb2222-y"},
            {"type": "interface", "slug": "DEM_Alta", "uuid": "cccc3333-z"}]
    build_model.desambiguar_slugs(objs)
    assert objs[0]["slug"].lower() != objs[1]["slug"].lower()
    assert objs[2]["slug"] == "DEM_Alta"


def test_detector_ignora_prosa(tmp_path):
    f = tmp_path / "04.md"
    f.write_text("Secretos: ninguno detectado\nPara secretos: área de seguridad\n", encoding="utf-8")
    assert subprocess.run([sys.executable, str(SCRIPTS / "detect_secrets.py"), str(f)], capture_output=True).returncode == 0
