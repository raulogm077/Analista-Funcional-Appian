"""Aplicación Appian ficticia y mal hecha a propósito: «MNT Mantenimiento de Instalaciones».

La sirve el simulador con MOCK_APP=fixture_mal_hecha, en un entorno de preproducción
(LCP_URL=https://pre.mnt.example.org). Expone lo mismo que fixture.py (la aplicación DEM) y sigue sus formas de
respuesta. Todo es ficticio: objetos, usuarios, correos y dominios (example.org).

Es la aplicación de las evaluaciones del recién llegado y de malas prácticas (pruebas/evaluaciones/aplicacion-ficticia/).
Llama a tres objetos de otra aplicación, un marco común con prefijo CMN que no está en la extracción:
rule!CMN_FormatearFecha, rule!CMN_UsuarioActual y rule!CMN_IF_Cabecera.
"""
from __future__ import annotations

import re

APP_KEY = "APP"


def _uuid(n: int) -> str:
    return f"_a-0000e{n:03d}-mnt0-8000-9bb2-011c48011c48_{n:05d}"


ORDEN = "'recordType!{@RT_ORD}MNT Orden'"
TECNICO = "'recordType!{@RT_TEC}MNT Técnico'"


def f_orden(campo: str) -> str:
    return f"'recordType!{{@RT_ORD}}MNT Orden.fields.{campo}'"


def f_tecnico(campo: str) -> str:
    return f"'recordType!{{@RT_TEC}}MNT Técnico.fields.{campo}'"


def _sail(*lineas: str) -> str:
    return "\n".join(lineas)


# ---------------------------------------------------------------- el formulario de la orden
# Los tres modos (alta, edición y revisión) copian el mismo formulario y cada campo copia la misma lógica.

CATEGORIAS = '{"Electricidad", "Climatización", "Fontanería", "Obra civil", "Ascensores"}'
TODOS_LOS_TECNICOS = f"a!queryRecordType(recordType: {TECNICO}, pagingInfo: a!pagingInfo(1, 100)).data"
CAMPOS_FORMULARIO = [
    # (campo, etiqueta, componente, obligatorio, parámetros propios)
    ("titulo", "Título", "a!textField", True, []),
    ("descripcion", "Descripción", "a!paragraphField", True, []),
    ("instalacion", "Instalación", "a!textField", True, []),
    ("ubicacion", "Ubicación", "a!textField", False, []),
    ("prioridad", "Prioridad", "a!dropdownField", True,
     ['placeholder: "Selecciona un valor",', "choiceLabels: cons!MNT_PRIORIDADES,",
      "choiceValues: cons!MNT_PRIORIDADES,"]),
    ("categoria", "Categoría", "a!dropdownField", True,
     ['placeholder: "Selecciona un valor",', f"choiceLabels: {CATEGORIAS},", f"choiceValues: {CATEGORIAS},"]),
    ("estadoId", "Estado", "a!dropdownField", False,
     ['placeholder: "Selecciona un valor",',
      'choiceLabels: {"Nueva", "Asignada", "En curso", "Pendiente de material", "Cerrada", "Cancelada"},',
      "choiceValues: {1, 2, 3, 4, 5, 6},"]),
    ("solicitante", "Solicitante", "a!pickerFieldUsers", True, ["maxSelections: 1,"]),
    ("telefonoContacto", "Teléfono de contacto", "a!textField", False, []),
    ("correoContacto", "Correo de contacto", "a!textField", False, []),
    ("fechaAlta", "Fecha de alta", "a!dateTimeField", False, []),
    ("fechaLimite", "Fecha límite", "a!dateField", True, []),
    ("fechaCierre", "Fecha de cierre", "a!dateTimeField", False, []),
    ("tecnicoId", "Técnico", "a!dropdownField", False,
     ['placeholder: "Selecciona un valor",', f"choiceLabels: {TODOS_LOS_TECNICOS}[{f_tecnico('nombre')}],",
      f"choiceValues: {TODOS_LOS_TECNICOS}[{f_tecnico('id')}],"]),
    ("proveedorId", "Proveedor", "a!dropdownField", False,
     ['placeholder: "Selecciona un valor",', "choiceLabels: rule!MNT_INT_ConsultarProveedores().result.body.nombre,",
      "choiceValues: rule!MNT_INT_ConsultarProveedores().result.body.id,"]),
    ("presupuesto", "Presupuesto (€)", "a!floatingPointField", False, []),
    ("horasEstimadas", "Horas estimadas", "a!integerField", False, []),
    ("horasReales", "Horas reales", "a!integerField", False, []),
    ("observaciones", "Observaciones", "a!paragraphField", False, []),
]
MODOS = [("ALTA", "Nueva orden de mantenimiento"), ("EDICION", "Editar orden"), ("REVISION", "Revisar orden")]


def _componente(funcion: str) -> str:
    """El nombre del componente en el árbol renderizado: a!textField -> TextField."""
    nombre = funcion.removeprefix("a!")
    return nombre[:1].upper() + nombre[1:]


def _campo(modo: str, campo: str, etiqueta: str, componente: str, obligatorio: bool, propios: list[str]) -> list[str]:
    valor, estado, alta = (f"ri!orden[{f_orden(c)}]" for c in (campo, "estadoId", "fechaAlta"))
    ob = "true" if obligatorio else "false"
    return [
        f"/* {etiqueta} */",
        f"{componente}(",
        f'  label: "{etiqueta}",',
        '  labelPosition: "ABOVE",',
        f'  helpTooltip: "{etiqueta} de la orden",',
        f'  accessibilityText: "{etiqueta}",',
        *[f"  {p}" for p in propios],
        f"  value: {valor},",
        "  saveInto: {",
        f"    {valor},",
        f'    a!save(local!cambios, append(local!cambios, "{campo}")),',
        "    a!save(local!hayCambios, true)",
        "  },",
        f"  required: {ob},",
        "  readOnly: or(",
        f"    {estado} = 5,",
        f"    {estado} = 6,",
        "    and(",
        '      ri!modo = "REVISION",',
        "      not(a!isUserMemberOfGroup(loggedInUser(), cons!MNT_GRUPO_SUPERVISORES))",
        "    )",
        "  ),",
        "  instructions: if(",
        f"    a!isNullOrEmpty({alta}),",
        '    "",',
        f'    "Orden creada el " & rule!CMN_FormatearFecha({alta})',
        "  ),",
        "  validations: {",
        "    if(",
        f"      and({ob}, a!isNullOrEmpty({valor})),",
        f'      "{etiqueta}: el campo es obligatorio",',
        "      null",
        "    ),",
        "    if(",
        f"      a!isNullOrEmpty({valor}),",
        "      null,",
        "      if(",
        f"        len(tostring({valor})) > 255,",
        f'        "{etiqueta}: no puede superar 255 caracteres",',
        "        null",
        "      )",
        "    ),",
        "    if(",
        "      and(",
        f'        ri!modo = "{modo}",',
        f"        {estado} = 5,",
        f"        not(a!isNullOrEmpty({valor}))",
        "      ),",
        f'      "{etiqueta}: una orden cerrada no se puede cambiar",',
        "      null",
        "    )",
        "  },",
        "  showWhen: true",
        "),",
    ]


def _formulario() -> str:
    lineas = ["=a!localVariables(",
              "  local!cambios: {},",
              "  local!hayCambios: false,",
              '  local!indiceModo: if(a!isNullOrEmpty(ri!modo), 1, index(wherecontains(ri!modo, {"ALTA", "EDICION", '
              '"REVISION"}), 1, 1)),',
              "  choose(",
              "    local!indiceModo,"]
    for i, (modo, titulo) in enumerate(MODOS):
        campos = [linea for c in CAMPOS_FORMULARIO for linea in _campo(modo, *c)]
        campos[-1] = campos[-1].rstrip(",")
        lineas += [f"    /* Modo {modo} */",
                   "    a!formLayout(",
                   f'      titleBar: "{titulo}",',
                   "      contents: {",
                   "        a!sectionLayout(",
                   '          label: "Datos de la orden",',
                   "          contents: {",
                   *[f"            {linea}" for linea in campos],
                   "          }",
                   "        )",
                   "      },",
                   "      buttons: a!buttonLayout(",
                   '        primaryButtons: a!buttonWidget(label: "Guardar", submit: true, style: "SOLID", validate: true),',
                   '        secondaryButtons: a!buttonWidget(label: "Cancelar", value: true, saveInto: ri!cancelar, '
                   'submit: true, style: "LINK", validate: false)',
                   "      )",
                   "    )" + ("," if i < len(MODOS) - 1 else "")]
    return "\n".join(lineas + ["  )", ")"])


# ---------------------------------------------------------------- el proceso de la orden
# Cada hito copia los mismos nueve nodos; ningún subproceso.

HITOS = ["Nueva", "Urgencia atendida", "Asignada", "En curso", "Pendiente de material", "Material recibido",
         "Trabajo terminado", "Cierre solicitado", "Cierre validado", "Cerrada", "Cierre rechazado", "Reabierta",
         "Cancelada"]


def _gestion() -> list[dict]:
    nodos: list[dict] = []

    def nodo(tipo: str, nombre: str, **kw) -> dict:
        n = {"id": len(nodos) + 1, "type": tipo, "name": nombre, "connections": [], **kw}
        nodos.append(n)
        return n

    def script(nombre: str, expresion: str, destino: str) -> dict:
        return nodo("internal.16", nombre, assignment={"attended": False},
                    data={"outputs": [{"expression": expresion, "saveInto": destino}]})

    def guardar(nombre: str) -> dict:
        return nodo("internal3.write_records_to_source_23r3", nombre, assignment={"attended": False},
                    data={"inputs": [{"name": "Records", "expression": "{pv!orden}"}]})

    def tarea(nombre: str, asignados: list[dict], formulario: str, entradas: dict) -> dict:
        return nodo("internal.17", nombre, displayName=nombre,
                    assignment={"attended": True, "assignees": asignados},
                    forms={"interfaceUuid": formulario, "inputMap": entradas})

    def une(*ns: dict) -> None:
        for a, b in zip(ns, ns[1:]):
            a["connections"].append(b["id"])

    def hito(nombre: str) -> tuple[dict, dict]:
        preparar = script(f"Preparar {nombre}", f'"{nombre}"', "pv!hito")
        guarda = guardar(f"Guardar {nombre}")
        fecha = script(f"Fecha de {nombre}", "now()", "pv!fechaHito")
        historial = script(f"Historial de {nombre}",
                           'append(pv!historial, pv!hito & " · " & text(pv!fechaHito, "dd/mm/yyyy hh:mm"))',
                           "pv!historial")
        destinatarios = script(f"Destinatarios de {nombre}", "a!groupMembers(cons!MNT_GRUPO_SUPERVISORES)",
                               "pv!destinatarios")
        avisar = nodo("core.4", f"¿Avisar de {nombre}?")
        aviso = nodo("internal3.sendemail3", f"Aviso de {nombre}", assignment={"attended": False}, data={"inputs": [
            {"name": "To", "expression": "pv!destinatarios"},
            {"name": "Cc", "expression": "cons!MNT_CORREO_SOPORTE"},
            {"name": "Subject", "expression": f'"Orden " & pv!orden[{f_orden("id")}] & ": {nombre}"'}]})
        registrado = script(f"Registrar aviso de {nombre}", "true", "pv!avisado")
        cierre = script(f"Fin de {nombre}", "false", "pv!avisado")
        avisar["decision"] = {"conditions": [{"expression": "pv!avisar", "targetNodeId": aviso["id"]}],
                              "defaultPath": cierre["id"]}
        une(preparar, guarda, fecha, historial, destinatarios, avisar, aviso, registrado, cierre)
        avisar["connections"].append(cierre["id"])
        return preparar, cierre

    inicio = nodo("core.0", "Inicio")
    usuario = script("Obtener usuario actual", "rule!CMN_UsuarioActual()", "pv!creador")
    plazo = script("Calcular fecha límite", "rule!ReglaCalculoPlazo(prioridad: pv!prioridad, fechaAlta: now())",
                   "pv!fechaLimite")
    orden = guardar("Guardar orden")
    erp = nodo("internal3.integration", "Consultar orden en el ERP", assignment={"attended": False}, data={
        "integrationUuid": "@INT_ERP",
        "inputs": [{"name": "ordenId", "expression": f"pv!orden[{f_orden('id')}]"}],
        "outputs": [{"expression": "ac!result.body", "saveInto": "pv!datosErp"}]})
    h = {n: hito(n) for n in HITOS[:1]}
    urgente = nodo("core.4", "¿Urgente?")
    atender = tarea("Atender urgencia", [{"type": "EXPRESSION", "expression": "cons!MNT_USUARIO_GUARDIA"}], "@I_ASIG",
                    {"orden": "orden", "tecnico": "tecnico"})
    h.update({n: hito(n) for n in HITOS[1:2]})
    asignar = tarea("Asignar técnico", [{"type": "GROUP", "name": "MNT Supervisores"}], "@I_ASIG",
                    {"orden": "orden", "tecnico": "tecnico"})
    h.update({n: hito(n) for n in HITOS[2:3]})
    ejecutar = tarea("Ejecutar trabajo", [{"type": "EXPRESSION", "expression": "pv!tecnico"}], "@I_CIERRE",
                     {"orden": "orden", "decision": "decision"})
    h.update({n: hito(n) for n in HITOS[3:8]})
    validar = tarea("Validar cierre", [{"type": "USER", "name": "david.molina"}], "@I_CIERRE",
                    {"orden": "orden", "decision": "decision"})
    validado = nodo("core.4", "¿Cierre validado?")
    h.update({n: hito(n) for n in HITOS[8:9]})
    cerrar = guardar("Cerrar orden")
    h.update({n: hito(n) for n in HITOS[9:]})
    fin = nodo("core.1", "Fin")

    une(inicio, usuario, plazo, orden, erp, h["Nueva"][0])
    une(h["Nueva"][1], urgente)
    urgente["decision"] = {"conditions": [{"expression": 'pv!prioridad = "Urgente"', "targetNodeId": atender["id"]}],
                           "defaultPath": asignar["id"]}
    une(urgente, atender)
    une(atender, h["Urgencia atendida"][0])
    une(h["Urgencia atendida"][1], ejecutar)
    urgente["connections"].append(asignar["id"])
    une(asignar, h["Asignada"][0])
    une(h["Asignada"][1], ejecutar)
    une(ejecutar, h["En curso"][0])
    for a, b in zip(HITOS[3:7], HITOS[4:8]):
        une(h[a][1], h[b][0])
    une(h["Cierre solicitado"][1], validar, validado)
    validado["decision"] = {"conditions": [
        {"expression": 'pv!decision = "VALIDAR"', "targetNodeId": h["Cierre validado"][0]["id"]},
        {"expression": 'pv!decision = "CANCELAR"', "targetNodeId": h["Cancelada"][0]["id"]}],
        "defaultPath": h["Cierre rechazado"][0]["id"]}
    validado["connections"] = [h[n][0]["id"] for n in ("Cierre validado", "Cancelada", "Cierre rechazado")]
    une(h["Cierre validado"][1], cerrar, h["Cerrada"][0])
    une(h["Cerrada"][1], fin)
    une(h["Cierre rechazado"][1], h["Reabierta"][0])
    une(h["Reabierta"][1], ejecutar)
    une(h["Cancelada"][1], fin)
    return nodos


# ---------------------------------------------------------------- objetos
# key, mcpType, name, extra

_RAW = [
    ("APP", "APPLICATION", "MNT Mantenimiento de Instalaciones", {
        "prefix": "MNT",
        "description": "Órdenes de mantenimiento de las instalaciones: alta, asignación a técnicos, seguimiento y cierre.",
    }),
    ("G_ADM", "GROUP", "MNT Administradores", {"groupType": "Custom",
                                               "description": "Administran la aplicación y su configuración."}),
    ("G_USR", "GROUP", "MNT Técnicos", {"groupType": "Custom",
                                        "description": "Técnicos de mantenimiento: dan de alta, ejecutan y cierran órdenes."}),
    ("G_SUP", "GROUP", "MNT Supervisores", {"groupType": "Custom",
                                            "description": "Asignan las órdenes a los técnicos y validan los cierres."}),
    # constantes
    ("C_URL_ERP", "CONSTANT", "MNT_URL_ERP_PRE", {"type": "TEXT", "value": "https://erp-pre.example.org/api/v2",
                                                  "environmentSpecific": False}),
    ("C_TOKEN", "CONSTANT", "MNT_ERP_API_TOKEN", {"type": "TEXT", "value": "sk_live_51MntErpFake0000",
                                                  "environmentSpecific": False}),
    ("C_GRP_ADM", "CONSTANT", "MNT_GRUPO_ADMINISTRADORES", {"type": "GROUP", "value": "MNT Administradores",
                                                            "environmentSpecific": False}),
    ("C_GRP_SUP", "CONSTANT", "MNT_GRUPO_SUPERVISORES", {"type": "GROUP", "value": "MNT Supervisores",
                                                         "environmentSpecific": False}),
    ("C_GUARDIA", "CONSTANT", "MNT_USUARIO_GUARDIA", {"type": "USER", "value": "carmen.ortega",
                                                      "environmentSpecific": False,
                                                      "description": "Supervisor de guardia: atiende las órdenes urgentes."}),
    ("C_DSE", "CONSTANT", "MNT_DSE_ORDENES", {"type": "DATA_STORE_ENTITY", "value": {"dataStoreUuid": "@DS",
                                                                                     "entity": "ordenes"},
                                              "environmentSpecific": False}),
    ("C_PRIO", "CONSTANT", "MNT_PRIORIDADES", {"type": "TEXT", "isArray": True,
                                               "value": ["Baja", "Media", "Alta", "Urgente"],
                                               "environmentSpecific": False}),
    ("C_ABIERTOS", "CONSTANT", "MNT_ESTADOS_ABIERTOS", {"type": "INTEGER", "isArray": True, "value": [1, 2, 3, 4],
                                                        "environmentSpecific": False}),
    ("C_PLAZO", "CONSTANT", "MNT_DIAS_PLAZO_DEFECTO", {"type": "INTEGER", "value": 7, "environmentSpecific": False}),
    ("C_PM_GEST", "CONSTANT", "MNT_PM_GESTION_ORDEN", {"type": "PROCESS_MODEL", "value": "@PM_GEST",
                                                       "environmentSpecific": False}),
    ("C_CORREO", "CONSTANT", "MNT_CORREO_SOPORTE", {"type": "TEXT", "value": "soporte.mnt@example.org",
                                                    "environmentSpecific": False}),
    # datos
    ("RT_EST", "RECORD_TYPE", "MNT Estado", {
        "pluralName": "Estados", "sourceType": "DATABASE", "tableName": "MNT_ESTADO",
        "fields": [
            {"fieldName": "id", "fieldType": "INTEGER", "isPrimaryKey": True},
            {"fieldName": "nombre", "fieldType": "TEXT", "length": 50},
            {"fieldName": "esFinal", "fieldType": "BOOLEAN"},
        ],
        "relationships": [{"relationshipName": "ordenes", "relationshipType": "ONE_TO_MANY",
                           "targetRecordTypeUuid": "@RT_ORD"}],
        "recordLevelSecurity": {"securityRules": [], "securityExpression": None},
    }),
    ("RT_TEC", "RECORD_TYPE", "MNT Técnico", {
        "pluralName": "Técnicos", "sourceType": "DATABASE", "tableName": "MNT_TECNICO", "urlStub": "tecnicos",
        "fields": [
            {"fieldName": "id", "fieldType": "INTEGER", "isPrimaryKey": True},
            {"fieldName": "usuario", "fieldType": "USER"},
            {"fieldName": "nombre", "fieldType": "TEXT", "length": 100},
            {"fieldName": "especialidad", "fieldType": "TEXT", "length": 50},
            {"fieldName": "zona", "fieldType": "TEXT", "length": 50},
            {"fieldName": "activo", "fieldType": "BOOLEAN"},
        ],
        "relationships": [{"relationshipName": "ordenes", "relationshipType": "ONE_TO_MANY",
                           "targetRecordTypeUuid": "@RT_ORD"}],
        "views": [{"name": "Ficha", "interfaceUuid": "@I_FICHA_TEC"}],
        "actions": [{"displayName": "Alta de técnico", "actionType": "LIST_ACTION", "key": "altaTecnico",
                     "processModelUuid": "@PM_ALTA_TEC"}],
        "recordLevelSecurity": {"securityRules": [
            {"name": "Cada técnico ve su ficha", "appliesTo": ["MNT Técnicos"], "condition": "usuario = loggedInUser()"},
            {"name": "Supervisores y administradores ven todas", "appliesTo": ["MNT Supervisores",
                                                                            "MNT Administradores"]},
        ], "securityExpression": None},
    }),
    ("RT_ORD", "RECORD_TYPE", "MNT Orden", {
        "pluralName": "Órdenes", "sourceType": "DATABASE", "tableName": "MNT_ORDEN", "urlStub": "ordenes",
        "fields": [
            {"fieldName": "id", "fieldType": "INTEGER", "isPrimaryKey": True},
            {"fieldName": "titulo", "fieldType": "TEXT", "length": 255},
            {"fieldName": "descripcion", "fieldType": "TEXT", "length": 4000},
            {"fieldName": "instalacion", "fieldType": "TEXT", "length": 100},
            {"fieldName": "ubicacion", "fieldType": "TEXT", "length": 255},
            {"fieldName": "prioridad", "fieldType": "TEXT", "length": 20},
            {"fieldName": "categoria", "fieldType": "TEXT", "length": 50},
            {"fieldName": "estadoId", "fieldType": "INTEGER"},
            {"fieldName": "solicitante", "fieldType": "USER"},
            {"fieldName": "telefonoContacto", "fieldType": "TEXT", "length": 20},
            {"fieldName": "correoContacto", "fieldType": "TEXT", "length": 255},
            {"fieldName": "fechaAlta", "fieldType": "DATETIME"},
            {"fieldName": "fechaLimite", "fieldType": "DATE"},
            {"fieldName": "fechaCierre", "fieldType": "DATETIME"},
            {"fieldName": "tecnicoId", "fieldType": "INTEGER"},
            {"fieldName": "proveedorId", "fieldType": "INTEGER"},
            {"fieldName": "presupuesto", "fieldType": "DECIMAL"},
            {"fieldName": "horasEstimadas", "fieldType": "INTEGER"},
            {"fieldName": "horasReales", "fieldType": "INTEGER"},
            {"fieldName": "observaciones", "fieldType": "TEXT", "length": 4000},
        ],
        "relationships": [
            {"relationshipName": "estado", "relationshipType": "MANY_TO_ONE", "targetRecordTypeUuid": "@RT_EST"},
            {"relationshipName": "tecnico", "relationshipType": "MANY_TO_ONE", "targetRecordTypeUuid": "@RT_TEC"},
        ],
        "views": [{"name": "Resumen", "interfaceUuid": "@I_RES"}],
        "actions": [{"displayName": "Nueva orden", "actionType": "LIST_ACTION", "key": "nuevaOrden",
                     "processModelUuid": "@PM_GEST"}],
        "recordLevelSecurity": {"securityRules": [], "securityExpression": None},
    }),
    ("T_DTO", "DATA_TYPE", "MNT_OrdenDTO", {
        "namespace": "urn:com:appian:types:MNT",
        "description": "Orden de mantenimiento del modelo de datos de la versión 1.",
        "tableName": "MNT_ORDEN",
        "fields": [
            {"name": "id", "type": "Number (Integer)", "primaryKey": True},
            {"name": "titulo", "type": "Text"},
            {"name": "descripcion", "type": "Text"},
            {"name": "instalacion", "type": "Text"},
            {"name": "prioridad", "type": "Text"},
            {"name": "estado", "type": "Text"},
            {"name": "tecnico", "type": "User"},
            {"name": "fechaAlta", "type": "Date and Time"},
            {"name": "fechaLimite", "type": "Date"},
        ],
    }),
    ("DS", "DATA_STORE", "MNT Datos Mantenimiento", {
        "dataSource": "jdbc/AppianBusinessDS",
        "autoUpdateSchema": False,
        "entities": [{"name": "ordenes", "dataTypeUuid": "@T_DTO",
                      "dataType": "{urn:com:appian:types:MNT}MNT_OrdenDTO"}],
    }),
    # interfaces
    ("I_PANEL", "INTERFACE", "MNT_IF_Panel", {
        "inputs": [],
        "expression": _sail(
            "=a!localVariables(",
            "  local!esAdmin: a!isUserMemberOfGroup(loggedInUser(), cons!MNT_GRUPO_ADMINISTRADORES),",
            "  local!esSupervisor: a!isUserMemberOfGroup(loggedInUser(), cons!MNT_GRUPO_SUPERVISORES),",
            "  local!abiertas: a!queryRecordType(",
            f"    recordType: {ORDEN},",
            "    filters: a!queryFilter(",
            f"      field: {f_orden('estadoId')},",
            '      operator: "in",',
            "      value: cons!MNT_ESTADOS_ABIERTOS",
            "    ),",
            "    pagingInfo: a!pagingInfo(1, 1),",
            "    fetchTotalCount: true",
            "  ).totalCount,",
            "  {",
            '    rule!CMN_IF_Cabecera(titulo: "Mantenimiento de instalaciones"),',
            "    a!cardLayout(",
            "      contents: {",
            '        a!richTextDisplayField(value: a!richTextItem(text: local!abiertas, size: "LARGE", style: "STRONG")),',
            '        a!richTextDisplayField(value: "Órdenes abiertas")',
            "      }",
            "    ),",
            "    rule!MNT_IF_ListadoOrdenes(),",
            "    a!sectionLayout(",
            '      label: "Supervisión",',
            "      showWhen: local!esSupervisor,",
            "      contents: rule!MNT_IF_Tecnicos()",
            "    ),",
            "    a!sectionLayout(",
            '      label: "Administración",',
            "      showWhen: local!esAdmin,",
            "      contents: a!buttonArrayLayout(",
            "        buttons: a!buttonWidget(",
            '          label: "Crear orden urgente",',
            '          style: "SOLID",',
            "          saveInto: a!startProcess(",
            "            processModel: cons!MNT_PM_GESTION_ORDEN,",
            '            processParameters: {prioridad: "Urgente"}',
            "          )",
            "        )",
            "      )",
            "    )",
            "  }",
            ")"),
        "screen": {"type": "Contents", "contents": [
            {"type": "CardLayout", "contents": [
                {"type": "ImageField", "label": "Logotipo"},
                {"type": "RichTextDisplayField", "value": "Mantenimiento de instalaciones"}]},
            {"type": "CardLayout", "contents": [
                {"type": "RichTextDisplayField", "value": "184"},
                {"type": "RichTextDisplayField", "value": "Órdenes abiertas"}]},
            {"type": "GridField", "label": "Órdenes", "totalCount": 2315,
             "columns": ["Título", "Instalación", "Prioridad", "Estado", "Técnico", "Fecha límite"]}]},
    }),
    ("I_LIST", "INTERFACE", "MNT_IF_ListadoOrdenes", {
        "inputs": [],
        "expression": _sail(
            "=a!localVariables(",
            "  local!ordenes: a!queryEntity(",
            "    entity: cons!MNT_DSE_ORDENES,",
            "    query: a!query(",
            "      pagingInfo: a!pagingInfo(startIndex: 1, batchSize: -1)",
            "    ),",
            "    fetchTotalCount: true",
            "  ).data,",
            "  a!gridField(",
            '    label: "Órdenes",',
            "    data: local!ordenes,",
            "    columns: {",
            '      a!gridColumn(label: "Título", value: fv!row.titulo),',
            '      a!gridColumn(label: "Instalación", value: fv!row.instalacion),',
            '      a!gridColumn(label: "Prioridad", value: fv!row.prioridad),',
            '      a!gridColumn(label: "Estado", value: fv!row.estado),',
            '      a!gridColumn(label: "Técnico", value: fv!row.tecnico),',
            '      a!gridColumn(label: "Fecha límite", value: fv!row.fechaLimite)',
            "    },",
            "    pageSize: 50",
            "  )",
            ")"),
        "screen": {"type": "GridField", "label": "Órdenes", "totalCount": 2315,
                   "columns": ["Título", "Instalación", "Prioridad", "Estado", "Técnico", "Fecha límite"]},
    }),
    ("I_FORM", "INTERFACE", "MNT_IF_FormularioOrden", {
        "inputs": [{"name": "orden", "type": "recordType!{@RT_ORD}MNT Orden"}, {"name": "modo", "type": "Text"},
                   {"name": "cancelar", "type": "Boolean"}],
        "expression": _formulario(),
        "screen": {"type": "FormLayout", "titleBar": "Nueva orden de mantenimiento", "contents": [
            {"type": "SectionLayout", "label": "Datos de la orden", "contents": [
                {"type": _componente(funcion), "label": etiqueta, "required": obligatorio}
                for _c, etiqueta, funcion, obligatorio, _p in CAMPOS_FORMULARIO]}],
            "buttons": ["Guardar", "Cancelar"]},
    }),
    ("I_TEC", "INTERFACE", "MNT_IF_Tecnicos", {
        "inputs": [],
        "expression": _sail(
            "=a!localVariables(",
            "  local!tecnicos: a!queryRecordType(",
            f"    recordType: {TECNICO},",
            "    filters: a!queryFilter(",
            f"      field: {f_tecnico('activo')},",
            '      operator: "=",',
            "      value: true",
            "    ),",
            "    pagingInfo: a!pagingInfo(1, 100)",
            "  ).data,",
            "  a!gridLayout(",
            '    label: "Carga de trabajo por técnico",',
            "    headerCells: {",
            '      a!gridLayoutHeaderCell(label: "Técnico"),',
            '      a!gridLayoutHeaderCell(label: "Zona"),',
            '      a!gridLayoutHeaderCell(label: "Órdenes abiertas")',
            "    },",
            "    rows: a!forEach(",
            "      items: local!tecnicos,",
            "      expression: a!gridRowLayout(",
            "        contents: {",
            f"          a!textField(value: fv!item[{f_tecnico('nombre')}], readOnly: true),",
            f"          a!textField(value: fv!item[{f_tecnico('zona')}], readOnly: true),",
            "          a!integerField(",
            "            value: a!queryRecordType(",
            f"              recordType: {ORDEN},",
            "              filters: {",
            "                a!queryFilter(",
            f"                  field: {f_orden('tecnicoId')},",
            '                  operator: "=",',
            f"                  value: fv!item[{f_tecnico('id')}]",
            "                ),",
            "                a!queryFilter(",
            f"                  field: {f_orden('estadoId')},",
            '                  operator: "in",',
            "                  value: cons!MNT_ESTADOS_ABIERTOS",
            "                )",
            "              },",
            "              pagingInfo: a!pagingInfo(1, 1),",
            "              fetchTotalCount: true",
            "            ).totalCount,",
            "            readOnly: true",
            "          )",
            "        }",
            "      )",
            "    )",
            "  )",
            ")"),
        "screen": {"type": "GridLayout", "label": "Carga de trabajo por técnico",
                   "headerCells": ["Técnico", "Zona", "Órdenes abiertas"], "rowCount": 12},
    }),
    ("I_RES", "INTERFACE", "MNT_IF_ResumenOrden", {
        "inputs": [{"name": "orden", "type": "recordType!{@RT_ORD}MNT Orden"}],
        "expression": _sail(
            "=a!sectionLayout(",
            '  label: "Resumen",',
            "  contents: {",
            f'    a!textField(label: "Título", value: ri!orden[{f_orden("titulo")}], readOnly: true),',
            f'    a!textField(label: "Instalación", value: ri!orden[{f_orden("instalacion")}], readOnly: true),',
            f'    a!textField(label: "Prioridad", value: ri!orden[{f_orden("prioridad")}], readOnly: true),',
            "    a!textField(label: \"Estado\", value: ri!orden['recordType!{@RT_ORD}MNT Orden.estado.fields.nombre'], "
            "readOnly: true),",
            "    a!textField(label: \"Técnico\", value: ri!orden['recordType!{@RT_ORD}MNT Orden.tecnico.fields.nombre'], "
            "readOnly: true),",
            f'    a!dateField(label: "Fecha límite", value: ri!orden[{f_orden("fechaLimite")}], readOnly: true),',
            "    a!textField(",
            '      label: "Plazo calculado",',
            "      value: rule!ReglaCalculoPlazo(",
            f"        prioridad: ri!orden[{f_orden('prioridad')}],",
            f"        fechaAlta: ri!orden[{f_orden('fechaAlta')}]",
            "      ),",
            "      readOnly: true",
            "    )",
            "  }",
            ")"),
        "screen": {"type": "SectionLayout", "label": "Resumen", "contents": [
            {"type": "TextField", "label": x, "readOnly": True}
            for x in ("Título", "Instalación", "Prioridad", "Estado", "Técnico", "Fecha límite", "Plazo calculado")]},
    }),
    ("I_ADMIN", "INTERFACE", "MNT_IF_Administracion", {
        "inputs": [],
        "expression": _sail(
            "={",
            "  a!sectionLayout(",
            '    label: "Técnicos",',
            "    contents: rule!MNT_IF_Tecnicos()",
            "  ),",
            "  a!sectionLayout(",
            '    label: "Configuración",',
            "    contents: {",
            '      a!textField(label: "URL del ERP", value: cons!MNT_URL_ERP_PRE, readOnly: true),',
            '      a!textField(label: "Supervisor de guardia", value: cons!MNT_USUARIO_GUARDIA, readOnly: true),',
            '      a!textField(label: "Correo de soporte", value: cons!MNT_CORREO_SOPORTE, readOnly: true)',
            "    }",
            "  )",
            "}"),
        "screen": {"type": "Contents", "contents": [
            {"type": "SectionLayout", "label": "Técnicos", "contents": [
                {"type": "GridLayout", "label": "Carga de trabajo por técnico", "rowCount": 12}]},
            {"type": "SectionLayout", "label": "Configuración", "contents": [
                {"type": "TextField", "label": "URL del ERP", "value": "https://erp-pre.example.org/api/v2"},
                {"type": "TextField", "label": "Supervisor de guardia", "value": "carmen.ortega"},
                {"type": "TextField", "label": "Correo de soporte", "value": "soporte.mnt@example.org"}]}]},
    }),
    ("I_ASIG", "INTERFACE", "MNT_IF_AsignarTecnico", {
        "inputs": [{"name": "orden", "type": "recordType!{@RT_ORD}MNT Orden"}, {"name": "tecnico", "type": "User"}],
        "expression": _sail(
            "=a!localVariables(",
            "  local!tecnicos: a!queryRecordType(",
            f"    recordType: {TECNICO},",
            f"    fields: {{{f_tecnico('id')}, {f_tecnico('usuario')}, {f_tecnico('nombre')}}},",
            "    pagingInfo: a!pagingInfo(1, 100)",
            "  ).data,",
            "  a!formLayout(",
            '    titleBar: "Asignar técnico",',
            "    contents: {",
            f'      a!textField(label: "Orden", value: ri!orden[{f_orden("titulo")}], readOnly: true),',
            "      a!dropdownField(",
            '        label: "Técnico",',
            '        placeholder: "Selecciona un técnico",',
            f"        choiceLabels: local!tecnicos[{f_tecnico('nombre')}],",
            f"        choiceValues: local!tecnicos[{f_tecnico('usuario')}],",
            "        value: ri!tecnico,",
            "        saveInto: {",
            "          ri!tecnico,",
            "          a!save(",
            f"            ri!orden[{f_orden('tecnicoId')}],",
            f"            index(local!tecnicos[{f_tecnico('id')}], wherecontains(save!value, "
            f"local!tecnicos[{f_tecnico('usuario')}]), null)",
            "          )",
            "        },",
            "        required: true",
            "      )",
            "    },",
            '    buttons: a!buttonLayout(primaryButtons: a!buttonWidget(label: "Asignar", submit: true, style: "SOLID"))',
            "  )",
            ")"),
        "screen": {"type": "FormLayout", "titleBar": "Asignar técnico", "contents": [
            {"type": "TextField", "label": "Orden", "readOnly": True},
            {"type": "DropdownField", "label": "Técnico", "required": True}], "buttons": ["Asignar"]},
    }),
    ("I_CIERRE", "INTERFACE", "MNT_IF_CierreOrden", {
        "inputs": [{"name": "orden", "type": "recordType!{@RT_ORD}MNT Orden"}, {"name": "decision", "type": "Text"}],
        "expression": _sail(
            "=a!formLayout(",
            '  titleBar: "Cierre de la orden",',
            "  contents: {",
            f'    a!textField(label: "Orden", value: ri!orden[{f_orden("titulo")}], readOnly: true),',
            "    a!integerField(",
            '      label: "Horas reales",',
            f"      value: ri!orden[{f_orden('horasReales')}],",
            f"      saveInto: ri!orden[{f_orden('horasReales')}],",
            "      required: true",
            "    ),",
            "    a!paragraphField(",
            '      label: "Observaciones",',
            f"      value: ri!orden[{f_orden('observaciones')}],",
            f"      saveInto: ri!orden[{f_orden('observaciones')}]",
            "    ),",
            "    a!radioButtonField(",
            '      label: "Decisión",',
            '      choiceLabels: {"Validar cierre", "Rechazar cierre", "Cancelar orden"},',
            '      choiceValues: {"VALIDAR", "RECHAZAR", "CANCELAR"},',
            "      value: ri!decision,",
            "      saveInto: ri!decision,",
            "      showWhen: rule!MNT_ER_EsSupervisor()",
            "    )",
            "  },",
            '  buttons: a!buttonLayout(primaryButtons: a!buttonWidget(label: "Enviar", submit: true, style: "SOLID"))',
            ")"),
        "screen": {"type": "FormLayout", "titleBar": "Cierre de la orden", "contents": [
            {"type": "TextField", "label": "Orden", "readOnly": True},
            {"type": "IntegerField", "label": "Horas reales", "required": True},
            {"type": "ParagraphField", "label": "Observaciones"}], "buttons": ["Enviar"]},
    }),
    ("I_ALTA_TEC", "INTERFACE", "MNT_IF_AltaTecnico", {
        "inputs": [{"name": "tecnico", "type": "recordType!{@RT_TEC}MNT Técnico"}, {"name": "cancelar", "type": "Boolean"}],
        "expression": _sail(
            "=a!formLayout(",
            '  titleBar: "Alta de técnico",',
            "  contents: {",
            f'    a!pickerFieldUsers(label: "Usuario", maxSelections: 1, value: ri!tecnico[{f_tecnico("usuario")}], '
            f'saveInto: ri!tecnico[{f_tecnico("usuario")}], required: true),',
            f'    a!textField(label: "Nombre", value: ri!tecnico[{f_tecnico("nombre")}], '
            f'saveInto: ri!tecnico[{f_tecnico("nombre")}], required: true),',
            "    a!dropdownField(",
            '      label: "Especialidad",',
            '      placeholder: "Selecciona un valor",',
            f"      choiceLabels: {CATEGORIAS},",
            f"      choiceValues: {CATEGORIAS},",
            f"      value: ri!tecnico[{f_tecnico('especialidad')}],",
            f"      saveInto: ri!tecnico[{f_tecnico('especialidad')}]",
            "    ),",
            f'    a!textField(label: "Zona", value: ri!tecnico[{f_tecnico("zona")}], '
            f'saveInto: ri!tecnico[{f_tecnico("zona")}])',
            "  },",
            "  buttons: a!buttonLayout(",
            '    primaryButtons: a!buttonWidget(label: "Dar de alta", submit: true, style: "SOLID"),',
            '    secondaryButtons: a!buttonWidget(label: "Cancelar", value: true, saveInto: ri!cancelar, submit: true, '
            "validate: false)",
            "  )",
            ")"),
        "screen": {"type": "FormLayout", "titleBar": "Alta de técnico", "contents": [
            {"type": "PickerFieldUsers", "label": "Usuario", "required": True},
            {"type": "TextField", "label": "Nombre", "required": True},
            {"type": "DropdownField", "label": "Especialidad"},
            {"type": "TextField", "label": "Zona"}], "buttons": ["Dar de alta", "Cancelar"]},
    }),
    ("I_FICHA_TEC", "INTERFACE", "MNT_IF_FichaTecnico", {
        "inputs": [{"name": "tecnico", "type": "recordType!{@RT_TEC}MNT Técnico"}],
        "expression": _sail(
            "=a!sectionLayout(",
            '  label: "Ficha del técnico",',
            "  contents: {",
            f'    a!textField(label: "Nombre", value: ri!tecnico[{f_tecnico("nombre")}], readOnly: true),',
            f'    a!textField(label: "Especialidad", value: ri!tecnico[{f_tecnico("especialidad")}], readOnly: true),',
            f'    a!textField(label: "Zona", value: ri!tecnico[{f_tecnico("zona")}], readOnly: true),',
            f'    a!checkboxField(label: "Activo", choiceLabels: {{"Sí"}}, choiceValues: {{true}}, '
            f'value: if(ri!tecnico[{f_tecnico("activo")}], true, null), readOnly: true)',
            "  }",
            ")"),
        "screen": {"type": "SectionLayout", "label": "Ficha del técnico", "contents": [
            {"type": "TextField", "label": x, "readOnly": True} for x in ("Nombre", "Especialidad", "Zona")]
            + [{"type": "CheckboxField", "label": "Activo", "readOnly": True}]},
    }),
    # reglas
    ("R_PLAZO", "FREEFORM_RULE", "ReglaCalculoPlazo", {
        "inputs": [{"name": "prioridad", "type": "Text"}, {"name": "fechaAlta", "type": "Date and Time"}],
        "expression": _sail(
            "=rule!calcFecha(",
            "  fecha: ri!fechaAlta,",
            "  dias: if(",
            '    ri!prioridad = "Urgente",',
            "    1,",
            "    if(",
            '      ri!prioridad = "Alta",',
            "      3,",
            "      cons!MNT_DIAS_PLAZO_DEFECTO",
            "    )",
            "  )",
            ")"),
    }),
    ("R_FECHA", "FREEFORM_RULE", "calcFecha", {
        "inputs": [{"name": "fecha", "type": "Date and Time"}, {"name": "dias", "type": "Number (Integer)"}],
        "expression": "=todate(ri!fecha) + ri!dias",
    }),
    ("R_PEND", "FREEFORM_RULE", "MNT_ER_OrdenesPendientes", {
        "inputs": [],
        "expression": _sail(
            "=a!queryRecordType(",
            f"  recordType: {ORDEN},",
            "  fields: {",
            f"    {f_orden('id')},",
            f"    {f_orden('titulo')},",
            f"    {f_orden('tecnicoId')},",
            f"    {f_orden('fechaLimite')}",
            "  },",
            "  filters: a!queryFilter(",
            f"    field: {f_orden('estadoId')},",
            '    operator: "in",',
            "    value: cons!MNT_ESTADOS_ABIERTOS",
            "  ),",
            "  pagingInfo: a!pagingInfo(1, 500)",
            ").data"),
    }),
    ("R_ESSUP", "FREEFORM_RULE", "MNT_ER_EsSupervisor", {
        "inputs": [],
        "expression": "=a!isUserMemberOfGroup(loggedInUser(), cons!MNT_GRUPO_SUPERVISORES)",
    }),
    # integraciones
    ("INT_ERP", "OUTBOUND_INTEGRATION", "MNT_INT_ConsultarERP", {
        "description": "Consulta una orden en el ERP.",
        "connectedSystemUuid": None,
        "method": "GET",
        "url": '=cons!MNT_URL_ERP_PRE & "/ordenes/" & ri!ordenId',
        "headers": [{"name": "X-Api-Key", "value": "=cons!MNT_ERP_API_TOKEN"}],
        "inputs": [{"name": "ordenId", "type": "Number (Integer)"}],
        "isWrite": False,
        "timeout": None,
        "errorHandling": None,
    }),
    ("INT_PROV", "OUTBOUND_INTEGRATION", "MNT_INT_ConsultarProveedores", {
        "description": "Lista los proveedores homologados.",
        "connectedSystemUuid": "@CS_PROV",
        "method": "GET",
        "relativePath": "/proveedores",
        "queryParameters": [{"name": "activos", "value": "true"}],
        "isWrite": False,
        "timeout": 30,
        "errorHandling": {"type": "CUSTOM", "expression": '=a!integrationError(title: "Proveedores", '
                                                         'message: "No se pudo consultar la lista de proveedores")'},
    }),
    ("CS_PROV", "CONNECTED_SYSTEM", "MNT_CS_Proveedores", {
        "description": "API de proveedores homologados.",
        "systemType": "HTTP", "baseUrl": "https://proveedores-dev.example.org", "authType": "NONE"}),
    ("WS_EST", "WEB_API", "MNT_WS_EstadoOrden", {
        "description": "El ERP consulta el estado y la fecha límite de una orden.",
        "httpMethod": "GET", "urlAlias": "mnt-estado-orden",
        "expression": _sail(
            "=a!localVariables(",
            "  local!orden: a!queryRecordByIdentifier(",
            f"    recordType: {ORDEN},",
            "    identifier: http!request.queryParameters.id,",
            f"    fields: {{{f_orden('estadoId')}, {f_orden('fechaLimite')}}}",
            "  ),",
            "  a!httpResponse(",
            "    statusCode: 200,",
            '    headers: a!httpHeader(name: "Content-Type", value: "application/json"),',
            "    body: a!toJson(",
            "      {",
            "        id: http!request.queryParameters.id,",
            f"        estado: local!orden[{f_orden('estadoId')}],",
            f"        fechaLimite: local!orden[{f_orden('fechaLimite')}]",
            "      }",
            "    )",
            "  )",
            ")"),
    }),
    # procesos
    ("PM_GEST", "PROCESS_MODEL", "MNT_PM_GestionOrden", {
        "description": "Alta, asignación, ejecución y cierre de una orden de mantenimiento.",
        "displayName": "Gestión de orden",
        "securityGroupName": "MNT Técnicos",
        "processVariables": [
            {"name": "orden", "type": "recordType!{@RT_ORD}MNT Orden", "isParameter": True},
            {"name": "prioridad", "type": "TEXT", "isParameter": True},
            {"name": "cancelar", "type": "BOOLEAN", "isParameter": True},
            {"name": "creador", "type": "USER"},
            {"name": "fechaLimite", "type": "DATE"},
            {"name": "datosErp", "type": "ANY"},
            {"name": "tecnico", "type": "USER"},
            {"name": "decision", "type": "TEXT"},
            {"name": "hito", "type": "TEXT"},
            {"name": "fechaHito", "type": "DATETIME"},
            {"name": "historial", "type": "TEXT", "isArray": True},
            {"name": "destinatarios", "type": "USER", "isArray": True},
            {"name": "avisar", "type": "BOOLEAN"},
            {"name": "avisado", "type": "BOOLEAN"},
        ],
        "startForm": {"interfaceUuid": "@I_FORM", "inputMap": {"orden": "orden", "cancelar": "cancelar"}},
        "nodes": _gestion(),
    }),
    ("PM_REC", "PROCESS_MODEL", "MNT_PM_Recordatorio", {
        "description": "Recuerda a los técnicos sus órdenes abiertas.",
        "securityGroupName": "MNT Administradores",
        "processVariables": [{"name": "pendientes", "type": "recordType!{@RT_ORD}MNT Orden", "isArray": True}],
        "nodes": [
            {"id": 1, "type": "core.0", "name": "Cada 5 minutos", "connections": [2],
             "timer": {"type": "RECURRING", "recurrence": {"frequency": "MINUTES", "interval": 5}}},
            {"id": 2, "type": "internal.16", "name": "Buscar órdenes pendientes", "connections": [3],
             "assignment": {"attended": False},
             "data": {"outputs": [{"expression": "rule!MNT_ER_OrdenesPendientes()", "saveInto": "pv!pendientes"}]}},
            {"id": 3, "type": "core.4", "name": "¿Hay pendientes?", "connections": [4, 5],
             "decision": {"conditions": [{"expression": "length(pv!pendientes) > 0", "targetNodeId": 4}],
                          "defaultPath": 5}},
            {"id": 4, "type": "internal3.sendemail3", "name": "Recordar a los técnicos", "connections": [5],
             "assignment": {"attended": False},
             "data": {"inputs": [{"name": "To", "expression": '"tecnicos.mnt@example.org"'},
                                 {"name": "Cc", "expression": "cons!MNT_CORREO_SOPORTE"},
                                 {"name": "Subject", "expression": '"Órdenes pendientes"'}]}},
            {"id": 5, "type": "core.1", "name": "Fin", "connections": []},
        ],
    }),
    ("PM_ALTA_TEC", "PROCESS_MODEL", "MNT_PM_AltaTecnico", {
        "description": "Da de alta a un técnico.",
        "securityGroupName": "MNT Administradores",
        "processVariables": [{"name": "tecnico", "type": "recordType!{@RT_TEC}MNT Técnico", "isParameter": True},
                             {"name": "cancelar", "type": "BOOLEAN", "isParameter": True}],
        "startForm": {"interfaceUuid": "@I_ALTA_TEC", "inputMap": {"tecnico": "tecnico", "cancelar": "cancelar"}},
        "nodes": [
            {"id": 1, "type": "core.0", "name": "Inicio", "connections": [2]},
            {"id": 2, "type": "internal3.write_records_to_source_23r3", "name": "Guardar técnico", "connections": [3],
             "assignment": {"attended": False}, "data": {"inputs": [{"name": "Records", "expression": "{pv!tecnico}"}]}},
            {"id": 3, "type": "internal3.sendemail3", "name": "Dar la bienvenida", "connections": [4],
             "assignment": {"attended": False},
             "data": {"inputs": [{"name": "To", "expression": f"pv!tecnico[{f_tecnico('usuario')}]"},
                                 {"name": "Cc", "expression": "cons!MNT_CORREO_SOPORTE"}]}},
            {"id": 4, "type": "core.1", "name": "Fin", "connections": []},
        ],
    }),
    ("PM_ANT", "PROCESS_MODEL", "MNT_PM_Antiguo", {
        "description": "Alta de órdenes de la versión 1, anterior al record type MNT Orden.",
        "securityGroupName": "MNT Administradores",
        "processVariables": [{"name": "orden", "type": "MNT_OrdenDTO", "isParameter": True}],
        "nodes": [
            {"id": 1, "type": "core.0", "name": "Inicio", "connections": [2]},
            {"id": 2, "type": "internal.16", "name": "Validar orden", "connections": [3],
             "assignment": {"attended": False},
             "data": {"outputs": [{"expression": 'if(isnull(pv!orden.titulo), "Sin título", pv!orden.titulo)',
                                   "saveInto": "pv!orden.titulo"}]}},
            {"id": 3, "type": "internal3.sendemail3", "name": "Avisar al supervisor", "connections": [4],
             "assignment": {"attended": False},
             "data": {"inputs": [{"name": "To", "expression": "cons!MNT_GRUPO_SUPERVISORES"},
                                 {"name": "Subject", "expression": '"Nueva orden"'}]}},
            {"id": 4, "type": "core.1", "name": "Fin", "connections": []},
        ],
    }),
    ("SITE", "SITE", "MNT Portal Mantenimiento", {
        "displayName": "Mantenimiento", "webAddressIdentifier": "mantenimiento",
        "pages": [
            {"name": "Panel", "targetUuid": "@I_PANEL"},
            {"name": "Órdenes", "targetUuid": "@RT_ORD"},
            {"name": "Administración", "targetUuid": "@I_ADMIN",
             "visibilityExpr": "a!isUserMemberOfGroup(loggedInUser(), cons!MNT_GRUPO_ADMINISTRADORES)"},
        ],
    }),
    ("F_RULES", "RULE_FOLDER", "MNT Reglas y Constantes", {}),
    ("F_PM", "PROCESS_MODEL_FOLDER", "MNT Modelos de Proceso", {}),
]

# Tipos que admite el análisis de dependencias (según la skill oficial de Appian).
DEPENDENTS_SUPPORTED = {"APPLICATION", "CONSTANT", "FREEFORM_RULE", "INTERFACE", "PROCESS_MODEL",
                        "WEB_API", "CONNECTED_SYSTEM", "RECORD_TYPE", "SITE"}

# Dónde aparece la referencia, como lo cuenta el análisis de dependencias; la expresión, antes que el resto.
_EXPRESION = {"INTERFACE": "Interface Definition", "FREEFORM_RULE": "Rule Definition", "WEB_API": "Web API Expression"}
_PRIMERO = ("expression", "nodes", "startForm")


def _donde(tipo: str, extra: dict, ruta: list, linea: int) -> str:
    clave = ruta[0]
    elemento = extra[clave][ruta[1]] if len(ruta) > 1 and isinstance(extra[clave], list) else {}
    if clave == "expression":
        return f"{_EXPRESION[tipo]}: Line {linea}"
    if clave == "nodes":
        return f"Node: {elemento['name']}"
    if clave == "pages":
        return f"Page{' visibility' if ruta[2] == 'visibilityExpr' else ''}: {elemento['name']}"
    nombre = {"views": "Record View", "actions": "Record Action", "relationships": "Relationship",
              "headers": "Header", "inputs": "Rule Input", "processVariables": "Process Variable",
              "entities": "Entity"}.get(clave)
    if nombre:
        return f"{nombre}: " + str(elemento.get("name") or elemento.get("displayName") or elemento.get("relationshipName"))
    return {"startForm": "Start Form", "value": "Constant Value", "connectedSystemUuid": "Connected System",
            "url": "URL"}.get(clave, clave)


def _referencias() -> list[tuple[str, str, str]]:
    """Lo que devolvería el análisis de dependencias de Appian (origen -> destino, dónde): la primera referencia de
    cada objeto a otro de la aplicación, por uuid, por rule! o por cons!."""
    tipo = {k: t for k, t, _n, _e in _RAW}
    clave_de = {n: k for k, _t, n, _e in _RAW}
    vistas: dict[tuple[str, str], str] = {}

    def recorre(origen: str, extra: dict, valor, ruta: list) -> None:
        if isinstance(valor, dict):
            for k, v in valor.items():
                recorre(origen, extra, v, ruta + [k])
        elif isinstance(valor, list):
            for i, v in enumerate(valor):
                recorre(origen, extra, v, ruta + [i])
        elif isinstance(valor, str):
            for n, linea in enumerate(valor.split("\n"), 1):
                destinos = [m.group(1) for m in re.finditer(r"@([A-Z][A-Z0-9_]*)", linea)]
                destinos += [clave_de.get(m.group(1)) for m in re.finditer(r"(?:rule|cons)!(\w+)", linea)]
                for d in destinos:
                    if d in tipo and d != origen and tipo[d] in DEPENDENTS_SUPPORTED:
                        vistas.setdefault((origen, d), _donde(tipo[origen], extra, ruta, n))

    for k, _t, _n, extra in _RAW:
        for clave in sorted(extra, key=lambda c: _PRIMERO.index(c) if c in _PRIMERO else len(_PRIMERO)):
            recorre(k, extra, extra[clave], [clave])
    return [(o, d, donde) for (o, d), donde in vistas.items()]


# Referencias que el análisis de dependencias de Appian devolvería (origen -> destino).
REFS = _referencias()

GROUP_USERS = {
    "G_ADM": ["admin.mnt", "rosa.navarro"],
    "G_USR": ["jorge.martin", "lucia.romero", "sergio.diaz", "nuria.campos"],
    "G_SUP": ["carmen.ortega", "david.molina"],
}

# Ejecuciones de procesos (para herramientas de historial)
PM_HISTORY = {
    "PM_GEST": {"total": 1840, "last": "2026-10-07T17:32:00Z", "errors": 3, "iniciador": "jorge.martin"},
    "PM_REC": {"total": 8640, "last": "2026-10-07T23:55:00Z", "errors": 0, "iniciador": "admin.mnt"},
    "PM_ALTA_TEC": {"total": 41, "last": "2026-09-18T10:05:00Z", "errors": 0, "iniciador": "rosa.navarro"},
    "PM_ANT": {"total": 0, "last": None, "errors": 0, "iniciador": "pedro.lozano"},
}

VALIDATION_ISSUES = {
    "PM_GEST": [{"severity": "WARNING",
                 "message": "Too many nodes: the process model has 130 nodes (recommended: 50 or fewer)"}],
}

# Historial de versiones: (versión, autor, fecha), de la última a la primera; "*" vale para todos los objetos.
VERSIONES = {"*": [(3, "ines.ferrer", "2026-09-22T09:15:00Z"), (2, "marcos.gil", "2026-04-08T11:40:00Z"),
                   (1, "admin.mnt", "2023-09-04T08:30:00Z")],
             "PM_ANT": [(2, "pedro.lozano", "2024-05-20T09:00:00Z"), (1, "pedro.lozano", "2023-11-14T16:30:00Z")]}

# Filas de cada tabla (para el COUNT(*) del Appian MCP Server simulado)
COUNTS = {"MNT_ORDEN": 2315, "MNT_TECNICO": 12, "MNT_ESTADO": 6}


def build():
    """Devuelve (objects_by_key, key_by_uuid, names) con '@KEY' resuelto a uuids."""
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
