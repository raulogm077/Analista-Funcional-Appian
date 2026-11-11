"""El plan usa tipos de objeto, nunca el tipo del valor de una constante."""
from types import SimpleNamespace

import pytest

import devmcp_extract as dx


def tool(name, param):
    return SimpleNamespace(name=name, description="", annotations=None,
                           inputSchema={"properties": {param: {"type": "string"}}, "required": [param]})


def result(items):
    return SimpleNamespace(ok=True, data={"items": items})


@pytest.mark.parametrize("nombre, parametro, tipo", [
    ("getTaskReport", "uuid", "taskReport"), ("getTempoReport", "uuid", "tempoReport"),
    ("getTranslationSet", "uuid", "translationSet"), ("listTranslationStrings", "translationSetUuid", "translationSet"),
    ("getDecision", "uuid", "decision")])
def test_las_herramientas_de_un_tipo_que_la_app_no_tiene_no_se_prueban_en_los_demas(nombre, parametro, tipo):
    """Visto con el Dev MCP 26.9.15 en una aplicación sin informes ni traducciones: las de informes de tareas y de Tempo y
    las de traducciones se tomaban por genéricas y se llamaban con cada constante, carpeta, grupo e interfaz (72 errores
    404 en 29 objetos)."""
    ex = dx.Extractor(None, dx.Policy(dx.DEFAULT_POLICY), None)
    ex.catalog = [tool(nombre, parametro), tool("getConstant", "uuid")]
    ex.classify(ex.base_type_phrases())
    suya = next(t for t in ex.tools if t.name == nombre)
    assert (suya.generic, suya.types) == (False, [tipo])
    objetos = [{"uuid": "demo-constante", "name": "DEM_UNA", "type": "constant"}]
    ex.classify(ex.type_phrases_for(objetos))
    assert [(t.name, t_tipo) for t, t_tipo, _ in ex.plan_object_calls(objetos)] == [("getConstant", "constant")]


def test_plan_constantes_no_adquieren_herramientas_de_sus_valores():
    ex = dx.Extractor(None, dx.Policy(dx.DEFAULT_POLICY), None)
    ex.catalog = [tool("listConstants", "appUuid")] + [tool("get" + t, "uuid") for t in
                  ("Constant", "Group", "Document", "Folder", "ProcessModel")]
    ex.classify(ex.base_type_phrases())
    _, objetos = ex.harvest_objects("demo-app-uuid", {"listConstants": result([
        {"uuid": "demo-constant-" + t, "name": "DEM_" + t, "type": t}
        for t in ("TEXT", "GROUP", "DOCUMENT", "FOLDER", "PROCESS_MODEL")])})
    ex.classify(ex.type_phrases_for(objetos))
    plan = ex.plan_object_calls(objetos)
    assert [(t.name, tipo, len(objs)) for t, tipo, objs in plan] == [("getConstant", "constant", 5)]


@pytest.mark.parametrize("skip, permitida", [(None, True), ("^testInterface$", False)])
def test_skip_deja_fuera_testinterface(skip, permitida):
    """Con datos reales se extrae con --skip: la política permite evaluar pantallas y guardaría lo que consulten."""
    ex = dx.Extractor(None, dx.Policy(dx.DEFAULT_POLICY), None, skip=skip)
    ex.catalog = [tool("testInterface", "uuid")]
    ex.classify(ex.base_type_phrases())
    assert ex.tools[0].allowed is permitida


@pytest.mark.parametrize("orden", [("listApplicationObjects", "listAgents"), ("listAgents", "listApplicationObjects")])
def test_lista_generica_no_impide_identificar_agente(orden):
    ex = dx.Extractor(None, dx.Policy(dx.DEFAULT_POLICY), None)
    ex.catalog = [tool(n, "appUuid") for n in orden] + [tool("getAgent", "uuid")]
    ex.classify(ex.base_type_phrases())
    agente = {"uuid": "demo-agent-uuid", "name": "DEM_AGT_Asistente"}
    desconocido = {"uuid": "demo-unknown-uuid", "name": "DEM_Desconocido"}
    respuestas = {"listApplicationObjects": result([agente, desconocido]), "listAgents": result([agente])}
    _, objetos = ex.harvest_objects("demo-app-uuid", {n: respuestas[n] for n in orden})
    assert {o["name"]: o["type"] for o in objetos} == {"DEM_AGT_Asistente": "aiAgent", "DEM_Desconocido": "unknown"}
    ex.classify(ex.type_phrases_for(objetos))
    assert [(t.name, tipo, [o["name"] for o in objs]) for t, tipo, objs in ex.plan_object_calls(objetos)] == [
        ("getAgent", "aiAgent", ["DEM_AGT_Asistente"])]


def test_eventos_solo_se_planifican_para_record_types():
    ex = dx.Extractor(None, dx.Policy(dx.DEFAULT_POLICY), None)
    eventos = tool("getRecordEventsConfig", "uuid")
    # Contrato del catalogo: UUID sin tipo en su nombre; la descripcion identifica el objeto.
    eventos.description = "Get the record event configuration for an Appian record type."
    ex.catalog = [eventos, tool("getObjectSecurity", "uuid")]
    tipos = ("constant", "document", "expressionRule", "folder", "group", "interface", "processModel",
             "recordType", "site", "aiAgent", "unknown")
    objetos = [{"uuid": "demo-" + t, "name": "DEM_" + t, "type": t} for t in tipos]
    ex.classify(ex.type_phrases_for(objetos))
    llamadas = ex.plan_object_calls(objetos)
    assert [(tipo, [o["type"] for o in objs]) for t, tipo, objs in llamadas
            if t.name == "getRecordEventsConfig"] == [("recordType", ["recordType"])]
    # No convierte otras herramientas genericas ni crea llamadas si no hay record types.
    assert next(t for t in ex.tools if t.name == "getObjectSecurity").generic
    assert not any(t.name == "getRecordEventsConfig" for t, _, _ in
                   ex.plan_object_calls([o for o in objetos if o["type"] != "recordType"]))
