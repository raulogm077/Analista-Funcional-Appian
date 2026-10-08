"""Aplicación Appian sintética para probar la skill sin un entorno real.

Todo es ficticio. Los esquemas de process model, site, record type, interfaz y
constante siguen los ejemplos publicados en github.com/appian/dev-mcp-skills;
el resto de formas de respuesta son supuestos del mock.
"""
from __future__ import annotations

APP_KEY = "APP"


def _uuid(n: int) -> str:
    return f"_a-0000e{n:03d}-dem0-8000-9bb2-011c48011c48_{n:05d}"


# key, mcpType, name, extra
_RAW = [
    ("APP", "APPLICATION", "DEM Gestión de Solicitudes", {
        "prefix": "DEM",
        "description": "Gestión de solicitudes internas: alta, revisión y seguimiento.",
    }),
    ("G_ADM", "GROUP", "DEM Administrators", {"groupType": "Custom"}),
    ("G_USR", "GROUP", "DEM Users", {"groupType": "Custom"}),
    ("G_GES", "GROUP", "DEM Gestores", {"groupType": "Custom", "parent": "G_USR"}),
    ("G_REV", "GROUP", "DEM Revisores", {"groupType": "Custom", "parent": "G_USR"}),
    ("C_ADMIN", "CONSTANT", "DEM_ADMIN_GROUP", {"type": "GROUP", "value": "DEM Administrators"}),
    ("C_PM_ALTA", "CONSTANT", "DEM_PM_ALTA_SOLICITUD", {"type": "PROCESS_MODEL", "value": "@PM_ALTA"}),
    ("C_ESTADOS", "CONSTANT", "DEM_ESTADOS_VALIDOS", {
        "type": "TEXT", "isArray": True, "value": ["Borrador", "Enviada", "Aprobada", "Rechazada"]}),
    ("C_TOKEN", "CONSTANT", "DEM_ERP_API_TOKEN", {"type": "TEXT", "value": "sk_live_51Hc9fakeTOKENvalue0000"}),
    ("C_URL", "CONSTANT", "DEM_URL_PORTAL", {"type": "TEXT", "value": "https://portal.example.org/solicitudes"}),
    ("RT_EST", "RECORD_TYPE", "DEM Estado", {
        "pluralName": "Estados", "sourceType": "DATABASE", "tableName": "DEM_ESTADO",
        "fields": [
            {"fieldName": "id", "fieldType": "INTEGER", "isPrimaryKey": True},
            {"fieldName": "label", "fieldType": "TEXT", "length": 50},
        ],
        "relationships": [{"relationshipName": "solicitudes", "relationshipType": "ONE_TO_MANY",
                           "targetRecordTypeUuid": "@RT_SOL"}],
    }),
    ("RT_SOL", "RECORD_TYPE", "DEM Solicitud", {
        "pluralName": "Solicitudes", "sourceType": "DATABASE", "tableName": "DEM_SOLICITUD",
        "urlStub": "solicitudes",
        "fields": [
            {"fieldName": "id", "fieldType": "INTEGER", "isPrimaryKey": True},
            {"fieldName": "titulo", "fieldType": "TEXT", "length": 255},
            {"fieldName": "estadoId", "fieldType": "INTEGER"},
            {"fieldName": "solicitante", "fieldType": "USER"},
            {"fieldName": "fechaAlta", "fieldType": "DATETIME"},
            {"fieldName": "importe", "fieldType": "DECIMAL"},
        ],
        "relationships": [{"relationshipName": "estado", "relationshipType": "MANY_TO_ONE",
                           "targetRecordTypeUuid": "@RT_EST"}],
        "views": [{"name": "Resumen", "interfaceUuid": "@I_RES"}],
        "actions": [{"displayName": "Nueva solicitud", "actionType": "LIST_ACTION",
                     "key": "nuevaSolicitud", "processModelUuid": "@PM_ALTA"}],
    }),
    ("T_DTO", "DATA_TYPE", "DEM_SolicitudDTO", {}),
    ("D_PRIO", "DECISION", "DEM_DEC_Prioridad", {}),
    ("AG_CLAS", "AI_AGENT", "DEM Clasificador de Solicitudes", {
        "instructions": "Clasifica cada solicitud por categoría usando rule!DEM_ER_ContarPorEstado.",
        "tools": [{"type": "RULE", "uuid": "@R_CONT"}],
    }),
    ("I_DASH", "INTERFACE", "DEM_Dashboard", {
        "inputs": [],
        "expression": "=a!localVariables(\n  local!total: a!queryRecordType(recordType: 'recordType!{@RT_SOL}DEM Solicitud', "
                      "pagingInfo: a!pagingInfo(1, 1)).totalCount,\n  local!porEstado: rule!DEM_ER_ContarPorEstado(),\n"
                      "  a!headerContentLayout(header: a!cardLayout(contents: a!richTextDisplayField(value: \"Panel de solicitudes\")),\n"
                      "    contents: {a!gridField(label: \"Últimas solicitudes\", data: 'recordType!{@RT_SOL}DEM Solicitud')})\n)",
        "screen": {"type": "HeaderContentLayout", "contents": [
            {"type": "RichTextDisplayField", "value": "Panel de solicitudes"},
            {"type": "CardLayout", "label": "Pendientes", "value": "12"},
            {"type": "CardLayout", "label": "Aprobadas", "value": "40"},
            {"type": "GridField", "label": "Últimas solicitudes",
             "columns": ["Título", "Estado", "Solicitante", "Fecha de alta"]}]},
    }),
    ("I_FORM", "INTERFACE", "DEM_SolicitudForm", {
        "inputs": [{"name": "record", "type": "recordType!{@RT_SOL}DEM Solicitud"}, {"name": "cancel", "type": "Boolean"}],
        "expression": "=a!formLayout(titleBar: \"Nueva solicitud\", contents: {\n"
                      "  a!textField(label: \"Título\", required: true, value: ri!record['recordType!{@RT_SOL}DEM Solicitud.fields.titulo']),\n"
                      "  a!floatingPointField(label: \"Importe\"),\n"
                      "  a!dropdownField(label: \"Estado\", choiceLabels: cons!DEM_ESTADOS_VALIDOS, choiceValues: cons!DEM_ESTADOS_VALIDOS),\n"
                      "  a!dropdownField(label: \"Categoría\", choiceLabels: rule!DEM_INT_ConsultarCatalogo().result.body)\n},\n"
                      "buttons: a!buttonLayout(primaryButtons: a!buttonWidget(label: \"Enviar\", submit: true),\n"
                      "  secondaryButtons: a!buttonWidget(label: \"Cancelar\", value: true, saveInto: ri!cancel, submit: true)))",
        "screen": {"type": "FormLayout", "titleBar": "Nueva solicitud", "contents": [
            {"type": "TextField", "label": "Título", "required": True},
            {"type": "FloatingPointField", "label": "Importe"},
            {"type": "DropdownField", "label": "Estado"},
            {"type": "DropdownField", "label": "Categoría"}],
            "buttons": ["Enviar", "Cancelar"]},
    }),
    ("I_RES", "INTERFACE", "DEM_SolicitudResumen", {
        "inputs": [{"name": "record", "type": "recordType!{@RT_SOL}DEM Solicitud"}],
        "expression": "=a!sectionLayout(label: \"Resumen\", contents: {a!textField(label: \"Título\", readOnly: true),\n"
                      "  a!textField(label: \"Estado\", readOnly: true),\n"
                      "  a!linkField(showWhen: rule!DEM_ER_EsAdmin(), links: a!dynamicLink(label: \"Editar\"))})",
        "screen": {"type": "SectionLayout", "label": "Resumen", "contents": [
            {"type": "TextField", "label": "Título", "readOnly": True},
            {"type": "TextField", "label": "Estado", "readOnly": True},
            {"type": "LinkField", "label": "Editar"}]},
    }),
    ("I_ADMIN", "INTERFACE", "DEM_AdminPanel", {
        "inputs": [],
        "expression": "=a!localVariables(local!legacy: a!queryEntity(entity: null, query: a!query()),\n"
                      "  a!buttonArrayLayout(buttons: a!buttonWidget(label: \"Crear solicitud de prueba\",\n"
                      "    saveInto: a!startProcess(processModel: cons!DEM_PM_ALTA_SOLICITUD, processParameters: {}))))",
        "screen": {"type": "ButtonArrayLayout", "buttons": ["Crear solicitud de prueba"]},
    }),
    ("I_REV", "INTERFACE", "DEM_RevisionForm", {
        "inputs": [{"name": "decision", "type": "Text"}, {"name": "comentarios", "type": "Text"}],
        "expression": "=a!formLayout(titleBar: \"Revisar solicitud\", contents: {\n"
                      "  a!radioButtonField(label: \"Decisión\", choiceLabels: {\"Aprobar\", \"Rechazar\"}, saveInto: ri!decision),\n"
                      "  a!paragraphField(label: \"Comentarios\", saveInto: ri!comentarios)},\n"
                      "  buttons: a!buttonLayout(primaryButtons: a!buttonWidget(label: \"Enviar\", submit: true)))",
        "screen": {"type": "FormLayout", "titleBar": "Revisar solicitud", "contents": [
            {"type": "RadioButtonField", "label": "Decisión", "choices": ["Aprobar", "Rechazar"]},
            {"type": "ParagraphField", "label": "Comentarios"}], "buttons": ["Enviar"]},
    }),
    ("R_CONT", "FREEFORM_RULE", "DEM_ER_ContarPorEstado", {
        "inputs": [],
        "expression": "=a!queryRecordType(recordType: 'recordType!{@RT_SOL}DEM Solicitud',\n"
                      "  fields: a!aggregationFields(groupings: a!grouping(field: 'recordType!{@RT_SOL}DEM Solicitud.fields.estadoId', alias: \"estado\"),\n"
                      "  measures: a!measure(function: \"COUNT\", alias: \"total\")), pagingInfo: a!pagingInfo(1, 100)).data",
    }),
    ("R_ADMIN", "FREEFORM_RULE", "DEM_ER_EsAdmin", {
        "inputs": [],
        # un usuario de DEM Users escrito en el código
        "expression": "=or(loggedInUser() = \"ana.garcia\", a!isUserMemberOfGroup(loggedInUser(), cons!DEM_ADMIN_GROUP))",
    }),
    ("INT_CAT", "OUTBOUND_INTEGRATION", "DEM_INT_ConsultarCatalogo", {
        "connectedSystemUuid": "@CS_CAT", "method": "GET", "relativePath": "/catalogo/categorias",
        "isWrite": False,
    }),
    ("INT_ERP", "OUTBOUND_INTEGRATION", "DEM_INT_NotificarERP", {
        "connectedSystemUuid": "@CS_ERP", "method": "POST", "relativePath": "/erp/notificaciones",
        "headers": [{"name": "X-Api-Key", "value": "=cons!DEM_ERP_API_TOKEN"}],
        "body": "=a!toJson({solicitudId: ri!solicitudId, estado: ri!estado})", "isWrite": True,
    }),
    ("CS_CAT", "CONNECTED_SYSTEM", "DEM_CS_Catalogo", {
        "systemType": "HTTP", "baseUrl": "https://api.catalogo.example.org", "authType": "API_KEY"}),
    ("CS_ERP", "CONNECTED_SYSTEM", "DEM_CS_ERP", {
        "systemType": "HTTP", "baseUrl": "https://svc_erp:P4ssw0rd!@erp.example.org/api", "authType": "BASIC"}),
    ("WS_SOL", "WEB_API", "DEM_WS_Solicitudes", {
        "httpMethod": "GET", "urlAlias": "dem-solicitudes",
        "expression": "=a!httpResponse(statusCode: 200, body: a!toJson(rule!DEM_ER_ContarPorEstado()))",
    }),
    ("PM_ALTA", "PROCESS_MODEL", "DEM Alta Solicitud", {
        "securityGroupName": "DEM Gestores",
        "processVariables": [{"name": "record", "type": "recordType!{@RT_SOL}DEM Solicitud", "isParameter": True},
                             {"name": "cancel", "type": "BOOLEAN", "isParameter": True}],
        "startForm": {"interfaceUuid": "@I_FORM", "inputMap": {"record": "record", "cancel": "cancel"}},
        "nodes": [
            {"id": 1, "type": "core.0", "name": "Inicio", "connections": [2]},
            {"id": 2, "type": "internal3.write_records_to_source_23r3", "name": "Guardar solicitud",
             "connections": [3], "assignment": {"attended": False},
             "data": {"inputs": [{"name": "Records", "expression": "{pv!record}"}]}},
            {"id": 3, "type": "internal3.subprocess", "name": "Revisar", "connections": [4],
             "assignment": {"attended": False}, "data": {"processModelUuid": "@PM_REV"}},
            {"id": 4, "type": "internal3.integration", "name": "Notificar ERP", "connections": [5],
             "assignment": {"attended": False}, "data": {"integrationUuid": "@INT_ERP"}},
            {"id": 5, "type": "core.1", "name": "Fin", "connections": []},
        ],
    }),
    ("PM_REV", "PROCESS_MODEL", "DEM Revisar Solicitud", {
        "securityGroupName": "DEM Revisores",
        "processVariables": [{"name": "decision", "type": "TEXT", "isParameter": True}],
        "nodes": [
            {"id": 1, "type": "core.0", "name": "Inicio", "connections": [2]},
            {"id": 2, "type": "internal.17", "name": "Revisión", "connections": [3],
             "assignment": {"attended": True, "assignees": [{"type": "GROUP", "name": "DEM Revisores"}]},
             "forms": {"interfaceUuid": "@I_REV", "inputMap": {"decision": "decision"}}},
            {"id": 3, "type": "core.4", "name": "¿Aprobada?", "connections": [4, 6],
             "decision": {"conditions": [{"expression": "pv!decision = \"Aprobar\"", "targetNodeId": 4}], "defaultPath": 6}},
            {"id": 4, "type": "internal.16", "name": "Marcar aprobada", "connections": [5],
             "assignment": {"attended": False}},
            {"id": 5, "type": "internal3.sendemail3", "name": "Avisar solicitante", "connections": [6],
             "assignment": {"attended": False},
             "data": {"inputs": [{"name": "Cc", "expression": "\"soporte.dem@example.org\""}]}},
            {"id": 6, "type": "core.1", "name": "Fin", "connections": []},
        ],
    }),
    ("PM_BATCH", "PROCESS_MODEL", "DEM Batch Recordatorios", {
        "securityGroupName": "DEM Administrators",
        "nodes": [
            {"id": 1, "type": "core.0", "name": "Cada día 08:00", "connections": [2],
             "timer": {"type": "RECURRING", "recurrence": {"frequency": "DAILY", "time": "08:00", "timezone": "Europe/Madrid"}}},
            {"id": 2, "type": "internal.16", "name": "Buscar pendientes", "connections": [3],
             "assignment": {"attended": False},
             "data": {"outputs": [{"expression": "a!queryRecordType(recordType: 'recordType!{@RT_SOL}DEM Solicitud')", "saveInto": "pv!pendientes"}]}},
            {"id": 3, "type": "internal3.sendemail3", "name": "Enviar recordatorio", "connections": [4],
             "assignment": {"attended": False}},
            {"id": 4, "type": "core.1", "name": "Fin", "connections": []},
        ],
    }),
    ("PM_HUERF", "PROCESS_MODEL", "DEM Utilidad Huérfana", {
        "securityGroupName": "DEM Administrators",
        "nodes": [
            {"id": 1, "type": "core.0", "name": "Inicio", "connections": [2]},
            {"id": 2, "type": "internal.16", "name": "Nada", "connections": [3], "assignment": {"attended": False}},
            {"id": 3, "type": "core.1", "name": "Fin", "connections": []},
        ],
    }),
    ("SITE", "SITE", "DEM Portal Solicitudes", {
        "displayName": "Solicitudes", "webAddressIdentifier": "dem-solicitudes",
        "pages": [
            {"name": "Panel", "targetUuid": "@I_DASH"},
            {"name": "Solicitudes", "targetUuid": "@RT_SOL"},
            {"name": "Administración", "targetUuid": "@I_ADMIN",
             "visibilityExpr": "a!isUserMemberOfGroup(loggedInUser(), cons!DEM_ADMIN_GROUP)"},
        ],
    }),
    ("F_RULES", "RULE_FOLDER", "DEM Rules and Constants", {}),
    ("F_PM", "PROCESS_MODEL_FOLDER", "DEM Process Models", {}),
]

# Referencias que el análisis de dependencias de Appian devolvería (origen -> destino).
REFS = [
    ("I_DASH", "RT_SOL", "Interface Definition: Line 2"),
    ("I_DASH", "R_CONT", "Interface Definition: Line 3"),
    ("I_FORM", "RT_SOL", "Interface Definition: Line 2"),
    ("I_FORM", "C_ESTADOS", "Interface Definition: Line 4"),
    ("I_RES", "R_ADMIN", "Interface Definition: Line 3"),
    ("I_ADMIN", "C_PM_ALTA", "Interface Definition: Line 3"),
    ("R_CONT", "RT_SOL", "Rule Definition: Line 1"),
    ("R_ADMIN", "C_ADMIN", "Rule Definition: Line 1"),
    ("INT_CAT", "CS_CAT", "Connected System"),
    ("INT_ERP", "CS_ERP", "Connected System"),
    ("INT_ERP", "C_TOKEN", "Header: X-Api-Key"),
    ("WS_SOL", "R_CONT", "Web API Expression: Line 1"),
    ("PM_ALTA", "I_FORM", "Start Form"),
    ("PM_ALTA", "RT_SOL", "Node: Guardar solicitud"),
    ("PM_ALTA", "PM_REV", "Node: Revisar"),
    ("PM_REV", "I_REV", "Node: Revisión"),
    ("PM_BATCH", "RT_SOL", "Node: Buscar pendientes"),
    ("RT_SOL", "I_RES", "Record View: Resumen"),
    ("RT_SOL", "PM_ALTA", "Record Action: Nueva solicitud"),
    ("RT_SOL", "RT_EST", "Relationship: estado"),
    ("RT_EST", "RT_SOL", "Relationship: solicitudes"),
    ("SITE", "I_DASH", "Page: Panel"),
    ("SITE", "RT_SOL", "Page: Solicitudes"),
    ("SITE", "I_ADMIN", "Page: Administración"),
    ("SITE", "C_ADMIN", "Page visibility: Administración"),
    ("C_PM_ALTA", "PM_ALTA", "Constant Value"),
    ("AG_CLAS", "R_CONT", "Agent Tool"),
]

# Tipos que admite el análisis de dependencias (según la skill oficial de Appian).
DEPENDENTS_SUPPORTED = {"APPLICATION", "CONSTANT", "FREEFORM_RULE", "INTERFACE", "PROCESS_MODEL",
                        "WEB_API", "CONNECTED_SYSTEM", "RECORD_TYPE", "SITE"}

GROUP_USERS = {
    "G_ADM": ["admin.dem"],
    "G_USR": ["ana.garcia", "luis.perez"],
    "G_GES": ["marta.ruiz", "pablo.soto"],
    "G_REV": ["elena.vidal"],
}

# Ejecuciones de procesos (para herramientas de historial)
PM_HISTORY = {
    "PM_ALTA": {"total": 120, "last": "2026-09-29T17:42:00Z", "errors": 2, "iniciador": "ana.garcia"},
    "PM_REV": {"total": 118, "last": "2026-09-30T09:10:00Z", "errors": 0, "iniciador": "ana.garcia"},
    "PM_BATCH": {"total": 30, "last": "2026-09-30T08:00:00Z", "errors": 1, "iniciador": "ana.garcia"},
    "PM_HUERF": {"total": 0, "last": None, "errors": 0, "iniciador": "ana.garcia"},
}

VALIDATION_ISSUES = {
    "I_ADMIN": [{"severity": "WARNING", "line": 1,
                 "message": "a!queryEntity is deprecated; use a!queryRecordType"}],
}

# Historial de versiones: (versión, autor, fecha), de la última a la primera; "*" vale para todos los objetos.
VERSIONES = {"*": [(3, "marta.ruiz", "2026-09-01T10:00:00Z"), (2, "pablo.soto", "2026-06-15T12:30:00Z"),
                   (1, "admin.dem", "2026-03-02T08:00:00Z")]}

# Filas de cada tabla (para el COUNT(*) del Appian MCP Server simulado)
COUNTS = {"DEM_SOLICITUD": 152, "DEM_ESTADO": 4}


def build():
    """Devuelve (objects_by_key, key_by_uuid) con '@KEY' resuelto a uuids."""
    uuids = {k: _uuid(i + 1) for i, (k, *_rest) in enumerate(_RAW)}
    names = {k: n for k, _t, n, _e in _RAW}

    def resolve(v):
        if isinstance(v, str):
            out = v
            for k, u in uuids.items():
                out = out.replace("{@" + k + "}", "{" + u + "}")
                if out == "@" + k:
                    return u
            return out
        if isinstance(v, list):
            return [resolve(x) for x in v]
        if isinstance(v, dict):
            return {kk: resolve(vv) for kk, vv in v.items()}
        return v

    objs = {}
    for k, t, n, e in _RAW:
        extra = resolve(e)
        if "parent" in extra:
            extra["parentGroupUuid"] = uuids[extra.pop("parent")]
        objs[k] = {"key": k, "uuid": uuids[k], "name": n, **extra, "objType": t}
    return objs, {v["uuid"]: k for k, v in objs.items()}, names
