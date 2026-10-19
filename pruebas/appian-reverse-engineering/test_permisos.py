"""Configuración declarada de permisos; datos ficticios con la forma del Dev MCP leído el 19-10-2026."""
import asyncio
import copy
from types import SimpleNamespace

import pytest
import devmcp_extract as de


def miembro(nombre):
    return f"a!isUserMemberOfGroup(loggedInUser(), cons!{nombre})"


def accion(expr, **extra):
    return {"nombre": "Abrir", "tipo": "LIST_ACTION", "securityMode": "EXPRESSION", "visibilityExpr": expr, **extra}


def esperado_accion(expr):
    return {"acciones": [{"nombre": "Abrir", "visibilidad": {"declaracion": "Gestores",
                                                              "configuracion": "EXPRESSION: " + expr}}]}


def observado_accion(expr, **extra):
    return {"existe": True, "acciones": [accion(expr, **extra)], "constantesDeVisibilidad": {
        "DEM_GESTORES": {"grupo": "DEM Gestores", "uuid": "grupo-1"},
        "DEM_ALIAS": {"grupo": "DEM Gestores", "uuid": "grupo-1"},
        "DEM_REVISORES": {"grupo": "DEM Revisores", "uuid": "grupo-2"}}}


def test_alias_orden_duplicados_y_fn_or_no_son_diferencias():
    exp = esperado_accion(f"or({miembro('DEM_GESTORES')},{miembro('DEM_REVISORES')})")
    real = observado_accion(f"= fn!or({miembro('DEM_REVISORES')},{miembro('DEM_ALIAS')},{miembro('DEM_ALIAS')})")
    assert de.diferencias(real, exp) == {}
    exp = esperado_accion(miembro("DEM_GESTORES"))
    assert de.diferencias(observado_accion(miembro("DEM_ALIAS")), exp) == {}


def test_conjunto_distinto_es_configuracion_distinta_no_acceso_efectivo():
    dif = de.diferencias(observado_accion(miembro("DEM_REVISORES")), esperado_accion(miembro("DEM_GESTORES")))
    h = dif["permisosDiferentes"][0]
    assert h["comprobacion"] == "configuración de visibilidad de Abrir"
    assert h["esperado"]["configuracion"] == {"gruposReferenciados": ["grupo-1"]}
    assert h["real"]["configuracion"] == {"gruposReferenciados": ["grupo-2"]}
    assert de.diferencias(observado_accion("false()"), esperado_accion("true()"))["permisosDiferentes"]


@pytest.mark.parametrize("expr,extra", [
    ("false()", {"securityMode": "RULES"}),
    ("false()", {"securityRule": {"unsupportedFilter": True}}),
    ("false()", {"securityRule": {"unsupportedMembership": True}}),
    ("and(true(), rule!DEM_Visible(rv!record))", {}),
    (None, {}),
])
def test_reglas_y_expresiones_no_decidibles_no_bloquean_como_diferencia(expr, extra):
    dif = de.diferencias(observado_accion(expr, **extra), esperado_accion("true()"))
    assert "permisosDiferentes" not in dif and dif["permisosNoComprobados"]


def proceso():
    return {"existe": True, "uuid": "pm", "tipo": "processModel", "gruposParaPermisos": {"DEM Gestores": "grupo-1"},
            "seguridadInicio": {"uuid": "pm", "objectType": "process_model", "roles": [
                {"roleName": r, "groupUuids": ["grupo-1"] if r == "viewer" else [], "inheritedGroupUuids": []}
                for r in sorted(de.ROLES_PROCESO)]}}


def contrato_pm():
    return {"permisosInicio": [{"rol": r, "grupos": ["DEM Gestores"] if r == "viewer" else []}
                               for r in sorted(de.ROLES_PROCESO)]}


def test_pm_compara_todos_los_roles_declarados_no_solo_initiator():
    real, exp = proceso(), contrato_pm()
    assert de.diferencias(real, exp) == {}
    exp["permisosInicio"] = [{"rol": "initiator", "grupos": []}]
    dif = de.diferencias(real, exp)
    assert "permisosDiferentes" not in dif and "parcial" in dif["permisosNoComprobados"][0]
    exp["permisosInicio"].append({"rol": "viewer", "grupos": []})
    assert de.diferencias(real, exp)["permisosDiferentes"][0]["comprobacion"] == "inicio: rol viewer"


def test_pm_legacy_sin_contrato_se_declara_no_comprobado():
    dif = de.diferencias(proceso(), {"tipo": "processModel"})
    assert "permisosDiferentes" not in dif and "falta contrato" in dif["permisosNoComprobados"][0]


@pytest.mark.parametrize("cambio", ["grupo", "rol", "herencia", "propietario", "ilegible", "vacio"])
def test_pm_ambiguo_heredado_o_ilegible_no_se_toma_por_vacio(cambio):
    real, exp = proceso(), contrato_pm()
    if cambio == "grupo": real["gruposParaPermisos"]["DEM Gestores"] = None
    if cambio == "rol": real["seguridadInicio"]["roles"] = []
    if cambio == "herencia": real["seguridadInicio"]["inheritSecurity"] = True
    if cambio == "propietario": real["seguridadInicio"]["uuid"] = "otro"
    if cambio == "ilegible": real["seguridadInicio"] = None
    if cambio == "vacio": exp["permisosInicio"][0]["grupos"] = None
    dif = de.diferencias(real, exp)
    assert "permisosDiferentes" not in dif and dif["permisosNoComprobados"]


class ExtractorFicticio:
    def __init__(self, valor="DEM Gestores", multiple=False):
        self.policy = SimpleNamespace(generic_skip=set())
        self.calls = []
        self.tools = [SimpleNamespace(name=n, toks=de.tokens(n), role=rol, types=tipos, generic=not tipos)
                      for n, rol, tipos in [("getConstant", "definition", ["constant"]),
                                            ("listRecordTypeActions", "other", ["recordType"]),
                                            ("getObjectSecurity", "other", [])]]
        self.datos = {"getConstant": {"uuid": "constante", "type": "GROUP", "multiple": multiple, "value": valor},
                      "listRecordTypeActions": [{"displayName": "Abrir", "actionType": "LIST_ACTION",
                                                 "securityMode": "EXPRESSION", "visibilityExpr": miembro("DEM_GESTORES")}],
                      "getObjectSecurity": proceso()["seguridadInicio"]}

    def usable(self, scope): return self.tools

    async def run_call(self, t, scope, obj):
        self.calls.append((t.name, obj["uuid"]))
        return SimpleNamespace(ok=True, data=self.datos[t.name], error=None)


@pytest.mark.parametrize("valor,multiple,duplicado,resuelto", [
    ("DEM Gestores", False, False, True), ("", False, False, False),
    ("DEM Gestores", True, False, False), ("DEM Gestores", False, True, False),
    ("999", False, False, False), (None, False, False, False)])
def test_verifica_resuelve_solo_group_escalar_de_nombre_unico(valor, multiple, duplicado, resuelto):
    ex = ExtractorFicticio(valor, multiple)
    objects = [{"name": "DEM Registro", "uuid": "record", "type": "recordType"},
               {"name": "DEM_GESTORES", "uuid": "constante", "type": "constant"},
               {"name": "DEM Gestores", "uuid": "grupo-1", "type": "group"}]
    if duplicado: objects.append({"name": "DEM Gestores", "uuid": "grupo-2", "type": "group"})
    esperado = esperado_accion(miembro("DEM_GESTORES"))
    resultado = asyncio.run(de.verifica(ex, {}, objects, ["DEM Registro"], {"DEM Registro": esperado}, ligero=True))
    obj = resultado["objetos"][0]
    assert bool(obj["constantesDeVisibilidad"]["DEM_GESTORES"]) is resuelto
    assert bool(de.diferencias(obj, esperado).get("permisosNoComprobados")) is not resuelto
    assert ex.calls == [("listRecordTypeActions", "record"), ("getConstant", "constante")]


def test_verifica_lee_seguridad_sin_ejecutar_proceso():
    ex = ExtractorFicticio()
    objects = [{"name": "DEM Proceso", "uuid": "pm", "type": "processModel"},
               {"name": "DEM Gestores", "uuid": "grupo-1", "type": "group"}]
    exp = contrato_pm()
    resultado = asyncio.run(de.verifica(ex, {}, objects, ["DEM Proceso"], {"DEM Proceso": exp}, ligero=True))
    assert de.diferencias(resultado["objetos"][0], exp) == {}
    assert ex.calls == [("getObjectSecurity", "pm")]
