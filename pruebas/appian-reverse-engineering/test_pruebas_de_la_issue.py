"""Las pruebas de una issue y la regresión (T13 del plan del método L.U.C.I.A.), con el Dev MCP simulado como el real.

El simulador, con MOCK_PRUEBAS=1 y MOCK_IGNORE_READONLY=1, se porta como el Dev MCP 26.6.110 de T5: ofrece ejecutar
los casos de prueba guardados de reglas e interfaces (con readOnlyHint), da los dependientes con el parámetro «object»,
lista las acciones de un record type sin envolverlas y no quita herramientas con LCP_TOOL_MODE=readonly.

- verificar ejecuta solo los casos de las reglas e interfaces de la issue y de lo que las usa (sus dependientes
  directos), y no los de las demás; un retoque que no cambia criterios ni reglas («pruebas»: false) no ejecuta nada y
  solo lee lo que compara.
- Un caso que el ejecutor de Appian no sabe evaluar (la rejilla de registros con filtros de usuario) es «no evaluable»,
  no un fallo; un error de verdad en la misma interfaz, sí.
- Por la salida, solo el resumen; ni las respuestas ni el registro del servidor.
- Las acciones de registro: su nombre y su tipo, sin dar por diferencias los campos del record type.
- regresion: todos los casos de la aplicación, con el resumen en un fichero y por la salida solo lo que falla.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from conftest import SKILL

sys.path.insert(0, str(Path(__file__).parent / "mock_devmcp"))
import fixture  # noqa: E402

sys.path.insert(0, str(SKILL / "scripts"))
from devmcp_extract import DEFAULT_POLICY, Policy, caso  # noqa: E402

OBJS, KEY_BY_UUID, _ = fixture.build()
POL = Policy(DEFAULT_POLICY)
COMO_EL_REAL = {"MOCK_PRUEBAS": "1", "MOCK_IGNORE_READONLY": "1"}


def esperado(tmp_path, objetos: dict, pruebas=None) -> Path:
    issue = {"id": "ISS-02", "unidad": "EV-02", "version": "3f9a0c1d2b7e", **({} if pruebas is None else
                                                                              {"pruebas": pruebas})}
    f = tmp_path / "ISS-02-esperado.json"
    f.write_text(json.dumps({"_issue": issue, **objetos}, ensure_ascii=False), encoding="utf-8")
    return f


def verifica(project, tmp_path, objetos, pruebas=None, *extra):
    destino = tmp_path / "construccion" / "EV-02" / "verificacion" / "ISS-02.json"
    p = project.run("verificar", "--app", "DEM", "--esperado", str(esperado(tmp_path, objetos, pruebas)),
                    "--out", str(destino), *extra, check=0)
    return p, json.loads(destino.read_text(encoding="utf-8"))


def ejecutados(project, desde=0) -> set[str]:
    """Los objetos cuyos casos de prueba se han ejecutado (con la herramienta que los ejecuta todos)."""
    return {OBJS[KEY_BY_UUID[c["args"]["uuid"]]]["name"] for c in project.calls_list()[desde:]
            if c["tool"].startswith("runAll")}


def por_objeto(v):
    return {o["objeto"]: o for o in v["pruebas"]["objetos"]}


def test_ejecuta_los_de_la_issue_y_lo_que_los_usa(project, tmp_path):
    """Las reglas e interfaces de la issue y sus dependientes directos que son reglas o interfaces: el panel usa la regla
    de la issue. No los de las demás de la aplicación, ni de un record type o un process model."""
    project.add_devmcp(**COMO_EL_REAL)
    p, v = verifica(project, tmp_path, {"DEM_ER_ContarPorEstado": {"tipo": "expressionRule"},
                                        "DEM_RevisionForm": {"tipo": "interface"},
                                        "DEM Solicitud": {"tipo": "recordType"}})
    assert ejecutados(project) == {"DEM_ER_ContarPorEstado", "DEM_RevisionForm", "DEM_Dashboard"}
    pr = v["pruebas"]
    assert pr["ejecutadas"] is True and (pr["casos"], pr["pasan"], pr["fallan"], pr["noEvaluables"]) == (3, 2, 0, 1)
    o = por_objeto(v)
    assert (o["DEM_ER_ContarPorEstado"]["de"], o["DEM_ER_ContarPorEstado"]["casos"]) == ("issue", 2)
    assert (o["DEM_RevisionForm"]["de"], o["DEM_RevisionForm"]["casos"]) == ("issue", 0)
    assert o["DEM_Dashboard"]["de"] == "usa" and o["DEM_Dashboard"]["usaA"] == ["DEM_ER_ContarPorEstado"]
    assert o["DEM_Dashboard"]["noEvaluables"] == [{"caso": "Panel con los datos de prueba", "motivo": (
        "el ejecutor de casos de prueba de Appian no evalúa una rejilla de registros con filtros de usuario")}]
    # el fichero no lleva las salidas de los casos que pasan (de una interfaz, el árbol de componentes)
    assert "output" not in json.dumps(v) and "salida" not in json.dumps(v)
    # por la salida, solo el resumen; el registro del servidor, nada
    assert "Pruebas: 2 de la issue y 1 que los usan, 3 casos: 2 pasan, 0 fallan, 1 no evaluables" in p.stdout
    assert "DEM_RevisionForm: sin casos de prueba" in p.stdout and "no evaluable" in p.stdout
    assert len(p.stdout.splitlines()) <= 6 and "Processing request" not in p.stderr, p.stdout + p.stderr[-500:]
    con_registro = project.run("verificar", "--app", "DEM", "--esperado", str(tmp_path / "ISS-02-esperado.json"),
                               "--out", str(tmp_path / "otra.json"), "--registro", check=0)
    assert len(con_registro.stderr) > len(p.stderr)                # con --registro sale el del servidor


def test_un_cambio_que_rompe_lo_que_lo_usa_se_ve(project, tmp_path):
    """La regla de la issue rompe la interfaz que la usa: se detecta antes de dar la issue por hecha, como aviso (es de
    otra issue). Un fallo en un caso de la propia issue también sale, y es el que la deja pendiente (issues.py)."""
    project.add_devmcp(**COMO_EL_REAL, MOCK_FALLAN="I_RES:Resumen de una solicitud,R_ADMIN:Otro usuario")
    p, v = verifica(project, tmp_path, {"DEM_ER_EsAdmin": {"tipo": "expressionRule"}})
    o = por_objeto(v)
    assert [c["caso"] for c in o["DEM_ER_EsAdmin"]["fallan"]] == ["Otro usuario"] and o["DEM_ER_EsAdmin"]["de"] == "issue"
    resumen = o["DEM_SolicitudResumen"]
    assert (resumen["de"], resumen["usaA"], [c["caso"] for c in resumen["fallan"]]) == (
        "usa", ["DEM_ER_EsAdmin"], ["Resumen de una solicitud"])
    assert "Invalid field 'estadoId'" in resumen["fallan"][0]["error"]
    assert "✗ DEM_ER_EsAdmin «Otro usuario» (de la issue)" in p.stdout
    assert "✗ DEM_SolicitudResumen «Resumen de una solicitud» (usa DEM_ER_EsAdmin: aviso)" in p.stdout


def test_sin_dependientes_lo_dice(project, tmp_path):
    """Si falla la llamada que da los dependientes, lo que usa la issue no desaparece sin más: se dice, en el fichero y
    por la salida, y los casos de la issue se ejecutan igual."""
    project.add_devmcp(**COMO_EL_REAL, MOCK_FALLAN_DEPENDIENTES="1")
    p, v = verifica(project, tmp_path, {"DEM_ER_ContarPorEstado": {"tipo": "expressionRule"}})
    assert v["pruebas"]["sinDependientes"] == ["DEM_ER_ContarPorEstado"] and ejecutados(project) == {"DEM_ER_ContarPorEstado"}
    assert "no se pudieron leer los dependientes de DEM_ER_ContarPorEstado: lo que los usa no se ha probado" in p.stdout


def test_un_retoque_no_ejecuta_nada(project, tmp_path):
    """Una issue que no cambia criterios ni reglas lo dice en lo esperado («pruebas»: false): no se ejecuta ningún caso."""
    project.add_devmcp(**COMO_EL_REAL)
    p, v = verifica(project, tmp_path, {"DEM_Dashboard": {"tipo": "interface"}}, False)
    assert ejecutados(project) == set() and not any(c["tool"] == "getObjectDependents" for c in project.calls_list())
    assert v["pruebas"] == {"ejecutadas": False, "motivo": "la issue no cambia criterios ni reglas"}
    assert "Pruebas: ninguna; la issue no cambia criterios ni reglas." in p.stdout


CUENTA = ("pedido", "existe", "nombre", "tipo", "uuid", "acciones", "diferencias")


def test_un_retoque_lee_solo_lo_que_compara(project, tmp_path):
    """Sin pruebas, verificar lee solo lo que compara: las aplicaciones en una página, la lista de record types de la
    aplicación y las acciones; ni las demás listas, ni la definición, ni el historial (en el Dev MCP real, de 36 llamadas
    a 3). Dice lo mismo que la verificación entera: que existe, su tipo, y el nombre y el tipo de la acción."""
    project.add_devmcp(**COMO_EL_REAL, MOCK_APPS_PAGINA="1")
    objetos = {"DEM Solicitud": {"tipo": "recordType", "acciones": [{"nombre": "Pedir material", "tipo": "De lista"}]}}
    _, v = verifica(project, tmp_path, objetos, False)
    llamadas = project.calls_list()
    assert [c["tool"] for c in llamadas] == ["listApplications", "listRecordTypes", "listRecordTypeActions"], llamadas
    assert llamadas[0]["args"]["limit"] > 2
    ligera = v["objetos"][0]
    assert ligera["diferencias"] == {"faltanAcciones": ["Pedir material"]} and v["aplicacion"]["prefijo"] == "DEM"
    assert "campos" not in ligera and "ultimaModificacion" not in ligera
    _, v = verifica(project, tmp_path, objetos)                          # con pruebas: lo lee todo
    assert {"listApplicationObjects", "getObjectVersionHistory", "getRecordType"} <= {
        c["tool"] for c in project.calls_list()[len(llamadas):]}
    assert {k: v["objetos"][0].get(k) for k in CUENTA} == {k: ligera.get(k) for k in CUENTA}
    # de una acción sin tipo de objeto en lo esperado, el record type; y del objeto que no está en su lista, la entera
    n = len(project.calls_list())
    objetos = {"DEM Solicitud": {"acciones": [{"nombre": "Nueva solicitud"}]}, "DEM_Dashboard": {"tipo": "recordType"},
               "DEM_Nada": {"tipo": "interface"}}
    _, v = verifica(project, tmp_path, objetos, False)
    assert "listApplicationObjects" in {c["tool"] for c in project.calls_list()[n:]}
    por = {o["pedido"]: o for o in v["objetos"]}
    assert por["DEM Solicitud"]["diferencias"] == {} and por["DEM_Nada"]["diferencias"] == {"falta": True}
    assert por["DEM_Dashboard"]["diferencias"] == {"tipo": {"esperado": "recordType", "real": "interface"}}


@pytest.mark.parametrize("pagina, llamadas", [("1", 1), ("1:1", 3)])
def test_las_aplicaciones_de_una_vez(project, tmp_path, pagina, llamadas):
    """Sin pruebas, las aplicaciones del entorno se piden en una página (482 en el entorno de desarrollo: una llamada y no
    diez); si el servidor no admite una tan grande, en las suyas."""
    project.add_devmcp(**COMO_EL_REAL, MOCK_APPS_PAGINA=pagina)
    _, v = verifica(project, tmp_path, {"DEM Estado": {"tipo": "recordType"}}, False)
    assert v["aplicacion"]["prefijo"] == "DEM" and v["objetos"][0]["existe"] is True
    assert sum(c["tool"] == "listApplications" for c in project.calls_list()) == llamadas


def test_sin_herramienta_de_ejecutar_lo_dice(project, tmp_path):
    """Si el Dev MCP no ofrece ejecutar casos, lo dice: los de la issue esperan a la regresión, que se pasa en Appian."""
    project.add_devmcp(MOCK_IGNORE_READONLY="1")
    p, v = verifica(project, tmp_path, {"DEM_ER_ContarPorEstado": {"tipo": "expressionRule"}})
    assert v["pruebas"]["ejecutadas"] is False and "esperan a la regresión" in v["pruebas"]["motivo"]
    assert "Pruebas: ninguna; el Dev MCP no ofrece ejecutar casos de prueba" in p.stdout


@pytest.mark.parametrize("accion, tipo, diferencias", [
    (None, "De lista", {"faltanAcciones": ["Pedir material"]}),          # antes del cambio: no está
    ("Pedir material", "De lista", {}),                                     # ya cambiado
    ("Pedir material", "Relacionada", {"accionesDeOtroTipo": [
        {"nombre": "Pedir material", "esperado": "Relacionada", "real": "LIST_ACTION"}]}),
])
def test_acciones_de_registro(project, tmp_path, accion, tipo, diferencias):
    """De una acción de registro se comprueba su nombre y su tipo; los campos del record type que solo toca una acción
    no se comparan (en T6 salían «sobrantes» y el cambio de nombre no se veía)."""
    project.add_devmcp(**COMO_EL_REAL, **({"MOCK_ACCION": accion} if accion else {}))
    _, v = verifica(project, tmp_path, {"DEM Solicitud": {"tipo": "recordType", "acciones": [
        {"nombre": "Pedir material", "tipo": tipo}]}}, False)
    assert v["objetos"][0]["diferencias"] == diferencias
    assert any(c["tool"] == "listRecordTypeActions" for c in project.calls_list())
    if accion:      # el nombre, como lo escribe el técnico: entre comillas latinas y sin mirar mayúsculas
        _, v = verifica(project, tmp_path, {"DEM Solicitud": {"acciones": [{"nombre": "«pedir  Material»"}]}}, False)
        assert v["objetos"][0]["diferencias"] == {}


def test_acciones_sin_herramienta_que_las_liste(project, tmp_path):
    """Sin una herramienta que liste las acciones, las de la definición del record type, si las trae."""
    project.add_devmcp(MOCK_ACCION="Pedir material")
    _, v = verifica(project, tmp_path, {"DEM Solicitud": {"acciones": [{"nombre": "Pedir material", "tipo": "De lista"}]}},
                    False)
    assert v["objetos"][0]["diferencias"] == {} and v["objetos"][0]["acciones"][0]["tipo"] == "LIST_ACTION"


def test_regresion(project, tmp_path):
    """Todos los casos de la aplicación, objeto a objeto: el resumen, en el fichero; por la salida, solo lo que falla.
    El caso que el ejecutor no evalúa no es un fallo. Sale 1 si algo falla y 17 si no se pueden ejecutar."""
    project.add_devmcp(**COMO_EL_REAL)
    destino = tmp_path / "construccion" / "EV-02" / "regresion.json"
    p = project.run("regresion", "--app", "DEM", "--out", str(destino), check=0)
    r = json.loads(destino.read_text(encoding="utf-8"))
    assert r["ejecutada"] is True and (r["objetos"], r["casos"], r["pasan"], r["fallan"], r["noEvaluables"]) == (
        7, 8, 7, 0, 1)
    assert sorted(r["sinCasos"]) == ["DEM_AdminPanel", "DEM_RevisionForm"]
    assert ejecutados(project) == {o["name"] for o in OBJS.values() if o["objType"] in ("FREEFORM_RULE", "INTERFACE")}
    assert len(p.stdout.splitlines()) == 1 and "8 casos: 7 pasan, 0 fallan, 1 no evaluables" in p.stdout, p.stdout
    project.add_devmcp(**COMO_EL_REAL, MOCK_FALLAN="R_CONT:Dos estados")
    p = project.run("regresion", "--app", "DEM", "--out", str(destino), check=1)
    assert p.stdout.splitlines()[1:] == ["  ✗ DEM_ER_ContarPorEstado «Dos estados»: Expression evaluation error in rule "
                                         "'dem_er_contarporestado' at function a!queryRecordType [line 2]: Invalid field "
                                         "'estadoId'"], p.stdout
    project.add_devmcp(MOCK_IGNORE_READONLY="1")
    p = project.run("regresion", "--app", "DEM", "--out", str(destino), check=17)
    assert json.loads(destino.read_text(encoding="utf-8"))["ejecutada"] is False and "en Appian" in p.stdout
    assert "los de las interfaces, desde cada interfaz en Designer, que Manage Test Cases no los ejecuta" in p.stdout


def test_la_extraccion_no_ejecuta_casos(project):
    """La extracción (que puede ser de producción) no evalúa lógica: las herramientas de ejecutar casos salen excluidas,
    con su motivo, y ninguna se llama."""
    project.add_devmcp(**COMO_EL_REAL)
    project.run("extract", "--app", "DEM", "--out", str(project.out), "--retry-delay", "0.1", check=0)
    assert not any(c["tool"].startswith("run") for c in project.calls_list())
    plan = json.loads((project.interm() / "extraction_plan.json").read_text(encoding="utf-8"))
    run = [t for t in plan["tools"] if t["name"].startswith("run")]
    assert len(run) == 4 and all(not t["use"] and t["role"] == "testRun" and "verificar" in t["reason"] for t in run)


@pytest.mark.parametrize("nombre", ["runAllExpressionRuleTestCases", "run_all_interface_test_cases",
                                    "executeTestCasesForRule", "runInterfaceTestCase"])
def test_ejecutar_casos_por_su_firma(nombre):
    """Se reconocen por su firma (el verbo y las palabras de testCases de la política), escriba como se escriba; la
    extracción no las usa. Una que el servidor declara destructiva no es de ejecutar casos."""
    ok, motivo, rol = POL.safety(nombre, None, False)
    assert not ok and rol == "testRun", (nombre, motivo)
    destructiva = type("A", (), {"destructiveHint": True, "readOnlyHint": False})()
    assert POL.safety(nombre, destructiva, False)[2] is None
    assert not POL.runs_test_cases("testProcessModel", None) and not POL.runs_test_cases("runProcessModel", None)


REJILLA = {"type": "OUTPUT_EVAL", "details": fixture.GRID_NO_EVALUABLE}
TEXTO = {"type": "OUTPUT_EVAL", "details": "Expression evaluation error in rule 'x_tablero' at function "
                                           "a!richTextDisplayField [line 184]: … Received List of Variant."}


@pytest.mark.parametrize("errores, resultado", [
    ([REJILLA], "noEvaluable"),             # la rejilla de registros con filtros de usuario, en T5 y T6
    ([TEXTO], "falla"),                     # un error de verdad de la interfaz (también en T5)
    ([REJILLA, TEXTO], "falla"),            # con los dos, no se tapa
    ([{"type": "ASSERTION", "details": "flow!userFilterSetData"}], "falla"),   # otro tipo de error
])
def test_no_evaluable_con_precision(errores, resultado):
    r = caso({"name": "Caso", "success": False, "output": None, "testErrors": errores,
              "error": errores[0]["details"]}, POL)
    assert r["resultado"] == resultado, r
    assert caso({"name": "Caso", "success": True, "output": "x" * 50_000}, POL) == {"caso": "Caso", "resultado": "pasa"}
    regla = caso({"name": "Aserción", "success": False, "output": "COYOACAN", "testErrors": [], "error": None}, POL)
    assert regla == {"caso": "Aserción", "resultado": "falla", "error": "no da lo esperado", "salida": "COYOACAN"}
