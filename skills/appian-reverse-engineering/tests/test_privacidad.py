"""Privacidad y solo lectura: lo que la extracción nunca usa ni deja pasar, escriba como se escriba."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import build_annex  # noqa: E402
import build_model  # noqa: E402
import privacidad  # noqa: E402
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


def test_secretos_enmascarados():
    c = [0]
    datos = {"authToken": "t0k3nvalor", "sapPassword": "Sup3r", "tokenUrl": "https://idp/oauth",
             "headers": [{"name": "X-API-Key", "value": "abcd1234"}, {"name": "Accept", "value": "json"}],
             "auth": {"password": "=cons!DEM_PASSWORD"},
             "expr": 'a!httpAuthenticationBasic(username: "svc_dem", password: "Sup3rS3cret!")'}
    out = privacidad.mask_secrets(datos, c)
    assert out["authToken"] == out["sapPassword"] == privacidad.MASK
    assert out["tokenUrl"] == "https://idp/oauth"                       # describe el secreto, no lo es
    assert out["headers"][0]["value"] == privacidad.MASK and out["headers"][1]["value"] == "json"
    assert out["auth"]["password"] == "=cons!DEM_PASSWORD"              # una referencia no es el secreto
    assert "svc_dem" not in out["expr"] and "Sup3rS3cret" not in out["expr"]


def test_render_sin_valores():
    r = privacidad.redact_screen({"type": "GridField", "label": "Pendientes", "value": 152,
                                  "rows": [{"label": "Nombre", "value": "Solicitud de Marta"}]})
    assert r["label"] == "Pendientes" and r["value"] == "‹valor›" and r["rows"][0]["value"] == "‹valor›"


def test_detector_sin_falsos_positivos(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text('password: cons!DEM_PASSWORD\n"token": "=ri!token"\n"tokenUrl": "https://x/oauth"\n'
                 'value: ***ENMASCARADO***\nhttps://***:***@host\n', encoding="utf-8")
    assert subprocess.run([sys.executable, str(SCRIPTS / "detect_secrets.py"), str(f)],
                          capture_output=True).returncode == 0
    f.write_text('{"clientSecret": "xyzw9876"}\n', encoding="utf-8")
    p = subprocess.run([sys.executable, str(SCRIPTS / "detect_secrets.py"), str(f)], capture_output=True, text=True)
    assert p.returncode == 1 and "xyzw9876" not in p.stdout                 # nunca muestra el valor


def test_usuarios_y_correos_fuera_del_anexo():
    users = {"mruiz": "‹usuario de DEM Users›"}
    out = build_annex.scrub({"displayName": "Marta Ruiz", "lastModifiedByUser": "mruiz", "modifierFullName": "Marta Ruiz",
                             "nota": "escribe a soporte@empresa.es",
                             "usuario": {"username": "mruiz", "displayName": "Marta Ruiz", "type": "User"}}, users, set())
    texto = str(out)
    assert "Marta" not in texto and "mruiz" not in texto and "@empresa.es" not in texto
    assert out["usuario"]["displayName"] == "‹usuario de DEM Users›"


def test_slugs_que_chocan():
    objs = [{"type": "processModel", "slug": "DEM_Alta", "uuid": "aaaa1111-x"},
            {"type": "processModel", "slug": "dem_alta", "uuid": "bbbb2222-y"},
            {"type": "interface", "slug": "DEM_Alta", "uuid": "cccc3333-z"}]
    build_model.desambiguar_slugs(objs)
    assert objs[0]["slug"].lower() != objs[1]["slug"].lower()
    assert objs[2]["slug"] == "DEM_Alta"
