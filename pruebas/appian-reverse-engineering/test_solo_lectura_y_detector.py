"""La política de solo lectura (lo que la extracción nunca usa, escriba como se escriba) y el detector de secretos."""
from __future__ import annotations

import json
import subprocess
import sys

import pytest

from conftest import SKILL

SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))
import build_model  # noqa: E402
import detect_secrets  # noqa: E402
from devmcp_extract import DEFAULT_POLICY, Policy  # noqa: E402

POL = Policy(DEFAULT_POLICY)


def respuesta(carpeta, response, meta=None):
    """Una respuesta como las escribe devmcp_extract.py: json.dumps con indent=1, una propiedad por línea."""
    f = carpeta / "getX.json"
    f.write_text(json.dumps({"_meta": meta or {"tool": "getX", "ok": True}, "response": response},
                            ensure_ascii=False, indent=1), encoding="utf-8")
    return f


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


# en el fichero, el nombre y el valor de una cabecera van en líneas distintas y las comillas de una expresión, escapadas;
# la propiedad es la ubicación dentro de la respuesta, la misma que lleva su evidencia (mcp:<tipo>/<nombre>#<propiedad>)
@pytest.mark.parametrize("response, propiedad", [
    ({"headers": [{"name": "X-Api-Key", "value": "a8f3k29dk3l"}]}, "headers[0].value"),
    ({"headers": {"Authorization": "Basic dXNlcjpwYXNzd29yZA=="}}, "headers.Authorization"),
    ({"expression": '=a!httpAuthenticationBasic(username: "svc_dem", password: "Sup3rS3cret!")'}, "expression"),
    ({"expression": '=a!integrationRule(apiKey: "k3y-9f8e7d6c5b")'}, "expression"),
    ({"expression": '=a!map(headers: {Authorization: "Bearer k3y-9f8e7d6c5b"})'}, "expression"),
])
def test_detector_en_la_extraccion(tmp_path, response, propiedad):
    f = respuesta(tmp_path, response)
    assert [donde for _, donde in detect_secrets.buscar(f)] == [propiedad]
    p = subprocess.run([sys.executable, str(SCRIPTS / "detect_secrets.py"), str(tmp_path)], capture_output=True,
                       text=True, encoding="utf-8")
    assert p.returncode == 1 and f"{f}#{propiedad} |" in p.stdout         # el fichero y la propiedad


def test_detector_cabecera_que_sale_de_una_constante(tmp_path):
    """«Bearer » & cons!X en un mapa SAIL no es un secreto escrito: el valor sale de la constante. El secreto, si lo
    hay, está en la constante, y ese sí se detecta."""
    (tmp_path / "integracion").mkdir()
    (tmp_path / "constante").mkdir()
    sail = respuesta(tmp_path / "integracion", {"expression": (
        '=a!localVariables(\n  local!cabeceras: {Authorization: "Bearer " & cons!DEM_ERP_API_TOKEN, Accept: "*/*"},\n'
        '  local!otras: a!map(headers: {authorization: "Bearer " & cons!DEM_ERP_API_TOKEN}),\n'
        '  rule!DEM_INT_NotificarERP(cabeceras: local!cabeceras)\n)')})
    constante = respuesta(tmp_path / "constante", {"name": "DEM_ERP_API_TOKEN", "value": "tk-41b7c9e2d05a"})
    assert list(detect_secrets.buscar(sail)) == []
    assert [donde for _, donde in detect_secrets.buscar(constante)] == ["value"]
    p = subprocess.run([sys.executable, str(SCRIPTS / "detect_secrets.py"), str(tmp_path)], capture_output=True,
                       text=True, encoding="utf-8")
    assert p.returncode == 1 and f"{constante}#value |" in p.stdout and str(sail) not in p.stdout


def test_detector_no_cuenta_referencias(tmp_path):
    f = respuesta(tmp_path, {"headers": [{"name": "X-Api-Key", "value": "=cons!DEM_ERP_API_TOKEN"}],
                             "auth": {"password": "=cons!DEM_PASSWORD"},
                             "expression": '=a!httpAuthenticationBasic(username: "svc_dem", password: cons!DEM_PWD)'},
                  meta={"tool": "getX", "ok": False, "error": "password: abc12345"})   # el _meta no es la aplicación
    assert list(detect_secrets.buscar(f)) == []


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
