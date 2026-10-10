"""Genera las plantillas de patrón (P01–P12) y templates/catalogo-patrones.json con los helpers del kit
(scripts/sail_helpers.py) y la guía (references/design-rules.md). Entidad genérica: «Expediente» (EXP Expediente).
Los datos de ejemplo del catálogo (expedientes, documentos, tareas) se generan aquí y son coherentes entre pantallas:
las cifras de la portada, las tareas del inicio y la bandeja salen del mismo dataset.
Uso: python3 generar_plantillas.py        (escribe en esta carpeta)"""
import datetime, json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True  # sin __pycache__ en el plugin: no se escribe fuera del proyecto
sys.path.insert(0, str(HERE.parent / "scripts"))
from sail_helpers import *  # noqa: E402,F401

RT = "EXP Expediente"
F = lambda f: f"recordType!{RT}.fields.{f}"
TIPOS = ["Obra", "Servicio", "Suministro"]
TIPOS_DET = ["Construcción, reforma o reparación", "Mantenimiento, limpieza o asistencia", "Compra de equipos o materiales"]
TIPOS_ICON = ["building", "wrench", "truck"]
UNIDADES = ["NOR", "SUR", "EST", "OES", "SSCC"]  # sedes Norte, Sur, Este y Oeste y Servicios Centrales de una empresa ficticia
TODAY = datetime.date(2026, 9, 24)
FASES = ["Borrador", "En tramitación", "Pendiente de aprobación", "Aprobado", "Cerrado", "Rechazado"]

# ------------------------------------------------------------------ datos de ejemplo (ficticios, coherentes entre pantallas)
_src = [
    ("Renovación de la cubierta del edificio A", "Obra", "NOR", "Javier García Ruiz", "2026-02-11", 185000, "En tramitación", None, "Sustitución de la lámina impermeable y de los lucernarios del edificio A."),
    ("Suministro de asientos para las salas de espera", "Suministro", "SUR", "Rocío Sánchez Vidal", "2026-09-02", 48600, "Pendiente de aprobación", "2026-09-12", "Bancadas de cuatro plazas con toma de carga para las salas de espera de las plantas 1 a 3."),
    ("Mantenimiento de ascensores 2026-2027", "Servicio", "EST", "María López Arranz", "2026-04-13", 320000, "Aprobado", None, "Mantenimiento preventivo y correctivo de los 14 ascensores y montacargas de la sede."),
    ("Señalética accesible en el edificio principal", "Obra", "OES", "Javier García Ruiz", "2026-05-14", 36500, "Cerrado", None, "Señales táctiles y en braille en los recorridos de acceso."),
    ("Limpieza de fachadas acristaladas", "Servicio", "NOR", "Rocío Sánchez Vidal", "2026-06-15", 92000, "Rechazado", None, "Limpieza semestral de las fachadas de los edificios A y B."),
    ("Ampliación del aparcamiento de empleados", "Obra", "SUR", "María López Arranz", "2026-07-16", 610000, "En tramitación", None, "Nueva planta de 220 plazas en el aparcamiento de empleados del edificio 1."),
    ("Sustitución de luminarias por LED en el aparcamiento P2", "Obra", "NOR", "Javier García Ruiz", "2026-08-17", 74000, "Pendiente de aprobación", "2026-09-21", "Cambio de 1.200 luminarias por LED con sensor de presencia."),
    ("Refuerzo de la atención a visitantes en temporada alta", "Servicio", "EST", "Rocío Sánchez Vidal", "2026-09-10", 128000, "Pendiente de aprobación", "2026-09-18", "Refuerzo del servicio de recepción y atención a visitantes de junio a septiembre."),
    ("Adquisición de escáneres de paquetería", "Suministro", "OES", "María López Arranz", "2026-01-10", 540000, "Aprobado", None, "Seis escáneres de rayos X para el control de accesos y la recepción de paquetes."),
    ("Reparación del pavimento de los muelles de carga", "Obra", "NOR", "Javier García Ruiz", "2026-02-11", 212000, "Cerrado", None, "Reparación de juntas y losas en los muelles 4 a 8 del almacén."),
    ("Consultoría de eficiencia energética", "Servicio", "SSCC", "Rocío Sánchez Vidal", "2026-03-12", 58000, "Aprobado", None, "Auditoría energética de los edificios de Servicios Centrales."),
    ("Mobiliario para la zona de trabajo compartida", "Suministro", "SUR", "María López Arranz", "2026-09-22", 6000, "Borrador", None, "Mesas y sillas para la sala de trabajo compartida del edificio 1."),
]
ROWS = []
plazo_txt = lambda d: f"Vence en {d} días" if d > 1 else "Vence mañana" if d == 1 else "Vence hoy"
for i, (tit, tipo, uni, resp, alta, imp, est, envio, desc) in enumerate(_src, start=1):
    r = {"id": i, "codigo": f"EXP-2026-{i:04d}", "titulo": tit, "tipo": tipo, "unidad": uni, "responsable": resp, "fechaAlta": alta, "mesAlta": alta[:7],
         "importe": imp, "estado": est, "descripcion": desc, "fechaEnvio": envio, "fechaLimite": None, "plazo": None}
    if envio and est == "Pendiente de aprobación":  # plazo de aprobación: 14 días desde el envío
        lim = datetime.date.fromisoformat(envio) + datetime.timedelta(days=14)
        r["fechaLimite"], r["plazo"] = lim.isoformat(), plazo_txt((lim - TODAY).days)
    ROWS.append(r)
PEND = [r for r in ROWS if r["estado"] == "Pendiente de aprobación"]
TAREAS = []
for r in PEND:
    d = (datetime.date.fromisoformat(r["fechaLimite"]) - TODAY).days
    TAREAS.append({"id": r["id"], "expedienteId": r["id"], "codigo": r["codigo"], "titulo": r["titulo"], "recibida": r["fechaEnvio"], "vence": r["fechaLimite"],
                   "plazo": r["plazo"], "urgente": d <= 3, "dias": d})
TAREAS.sort(key=lambda t: t["vence"])  # la que vence antes, primero
DOCS = []
for r in ROWS:
    for k, (nom, ico, kb) in enumerate([("Memoria_justificativa.pdf", "file-pdf-o", 420), ("Presupuesto.xlsx", "file-excel-o", 38), ("Pliego_tecnico.docx", "file-word-o", 160)][: 2 + r["id"] % 2]):
        DOCS.append({"id": r["id"] * 10 + k, "expedienteId": r["id"], "nombre": f"{r['codigo']}_{nom}", "icono": ico, "meta": f"{nom.rsplit('.', 1)[1].upper()} · {kb} KB · {r['responsable']} · {r['fechaAlta'][8:]}/{r['fechaAlta'][5:7]}/2026"})
cnt = lambda e: sum(1 for r in ROWS if r["estado"] == e)
fmt_date = lambda iso: f"{iso[8:10]}/{iso[5:7]}/{iso[:4]}"
ESTADOS = {"Borrador": "neutral", "En tramitación": "enCurso", "Pendiente de aprobación": "atencion", "Aprobado": "positivo", "Cerrado": "neutral", "Rechazado": "negativo"}
NUEVO = {"goto": "asistente"}


def screen(sid, title, stype, pattern, req, interface, note, **kw):
    s = {"id": sid, "title": title, "type": stype, "pattern": pattern, "req": req, "$note": note}
    s.update(kw)
    s["interface"] = interface
    return s


# ------------------------------------------------------------------ P01 Listado
p01 = screen("listado", "Expedientes", "page", "P01", ["RF-LIST"], {"type": "a!headerContentLayout", "backgroundColor": BG, "contents": [
    page_header("Expedientes", "Todos los expedientes de su unidad", [primary("Nuevo expediente", NUEVO, "plus")]),
    content_card([grid(f"recordType!{RT}", None, [
        gcol("Expediente", two_line("{fv!row.codigo}", "{fv!row.titulo}", {"type": "a!recordLink", "recordType": f"recordType!{RT}", "identifier": "{fv!row.id}"}), sortField=F("codigo"), width="4X"),
        gcol("Tipo", "{fv!row.tipo}", sortField=F("tipo"), width="2X"),
        gcol("Unidad", "{fv!row.unidad}", sortField=F("unidad"), width="NARROW"),
        gcol("Responsable", "{fv!row.responsable}", sortField=F("responsable"), width="3X"),
        gcol_num("Importe", "{fv!row.importe|eur|dash}", sortField=F("importe"), width="2X"),
        gcol("Alta", "{fv!row.fechaAlta|date}", sortField=F("fechaAlta"), width="NARROW"),
        gcol("Estado", tag("fv!row.estado", "estadoColorGrid"), sortField=F("estado"), width="NARROW_PLUS"),
    ], "No hay expedientes que cumplan los filtros", page_size=25, showSearchBox=True, showExportButton=True,
        userFilters=[f"recordType!{RT}.filters.estado", f"recordType!{RT}.filters.tipo", f"recordType!{RT}.filters.unidad"],
        initialSorts=[{"type": "a!sortInfo", "field": F("fechaAlta"), "ascending": False}])]),
]}, "P01: cabecera con la acción principal + grid en una card: ≤7 columnas consolidadas (código + título en la 1.ª, enlace a la ficha), cifras a la derecha, "
    "estado como tag (en grids solo atención y negativo llevan color), filtros de usuario y búsqueda. Con asistente de datos: ai_side_pane (references/bloques.md). "
    "Página del site: si basta con buscar, filtrar y abrir la ficha, en Appian es una página de tipo Record List (la lista configurada en el record type, "
    "con sus filtros, búsqueda, exportación y acciones de lista), no una interfaz (BP 09 §1.3); el prototipo la pinta igual y app.json no declara el tipo de página.")

# ------------------------------------------------------------------ P03 Formulario de una página
p03 = screen("formulario", "Nuevo expediente (una página)", "form", "P03", ["RF-ALTA"], {
    "type": "a!formLayout", "titleBar": "Nuevo expediente", "contentsWidth": "NARROW", "backgroundColor": "WHITE", "showButtonDivider": True,
    "contents": [
        {"type": "a!sectionLayout", "label": "Datos generales", "labelSize": "MEDIUM", "labelHeadingTag": "H2", "labelColor": "STANDARD", "contents": [
            txt("Título", "local!exp.titulo", required=True, requiredMessage="Indique un título", characterLimit=200),
            choice_cards("Tipo", [{"id": t, "texto": t, "detalle": d, "icono": i} for t, d, i in zip(TIPOS, TIPOS_DET, TIPOS_ICON)], "local!exp.tipo", required=True),
            cols(dd("Unidad", UNIDADES, "local!exp.unidad", required=True), date("Fecha de inicio", "local!exp.fecha", required=True)),
        ]},
        {"type": "a!sectionLayout", "label": "Detalle", "labelSize": "MEDIUM", "labelHeadingTag": "H2", "labelColor": "STANDARD", "marginBelow": "NONE", "contents": [
            par("Descripción", "local!exp.descripcion", instructions="Qué se solicita y por qué", characterLimit=2000, showCharacterCount=True),
            upload("Documentación", "local!exp.docs", maxSelections=5, instructions="PDF o DOCX, máximo 10 MB por fichero"),
        ]},
    ],
    "buttons": bl(primary("Crear expediente", {"goto": "listado"}, submit=True), [secondary("Cancelar", {"goto": "listado"})])},
    "P03: una columna estrecha (NARROW) con secciones H2; el botón repite el verbo del título; campos cortos en pareja; selección con explicación en cards; una acción SOLID.",
    local={"local!exp": {"titulo": None, "tipo": None, "unidad": None, "fecha": None, "descripcion": None, "docs": []}})

# ------------------------------------------------------------------ P04 Asistente por pasos
def revisa(label, step, pairs):
    return subsection_with_link(label, "Editar", {"step": step}, field_summary(pairs, columns=2))


p04 = screen("asistente", "Nuevo expediente (asistente)", "form", "P04", ["RF-ALTA"], {
    "type": "a!wizardLayout", "style": "DOT_VERTICAL", "contentsWidth": "MEDIUM", "showButtonDivider": True, "backgroundColor": "WHITE",
    "titleBar": {"type": "a!sidebarTemplate", "title": "Nuevo expediente", "secondaryText": "Complete los datos en 4 pasos", "backgroundColor": NAVY, "width": "NARROW_PLUS",
                 "additionalContents": [{"type": "a!richTextDisplayField", "labelPosition": "COLLAPSED", "value": [{"type": "a!richTextIcon", "icon": "info-circle", "color": GREEN}, " ",
                                         {"type": "a!richTextItem", "text": "Al enviar, el responsable recibe una tarea de aprobación.", "size": "SMALL", "color": "#FFFFFF"}]}]},
    "steps": [
        {"type": "a!wizardStep", "label": "Datos generales", "contents": [
            txt("Título", "local!exp.titulo", required=True, characterLimit=200),
            choice_cards("Tipo", [{"id": t, "texto": t, "detalle": d, "icono": i} for t, d, i in zip(TIPOS, TIPOS_DET, TIPOS_ICON)], "local!exp.tipo", required=True),
            {"type": "a!pickerFieldUsers", "label": "Responsable", "maxSelections": 1, "value": "local!exp.responsable", "saveInto": "local!exp.responsable", "required": True}]},
        {"type": "a!wizardStep", "label": "Importe", "contents": [
            {"type": "a!radioButtonField", "label": "¿Tiene importe?", "choiceLabels": ["Sí", "No"], "choiceValues": [True, False], "choiceLayout": "COMPACT", "value": "local!exp.conImporte", "saveInto": "local!exp.conImporte", "required": True},
            cols({"type": "a!floatingPointField", "label": "Importe (€)", "value": "local!exp.importe", "saveInto": "local!exp.importe", "required": True, "instructions": "Sin IVA"}, [], showWhen="local!exp.conImporte")]},
        {"type": "a!wizardStep", "label": "Documentación", "contents": [upload("Documentos", "local!exp.docs", required=True, maxSelections=5, instructions="PDF o DOCX, máximo 10 MB por fichero")]},
        {"type": "a!wizardStep", "label": "Revisión", "contents": [
            {"type": "a!messageBanner", "backgroundColor": "INFO", "highlightColor": "INFO", "shape": "SEMI_ROUNDED", "primaryText": "Revise los datos antes de enviar", "secondaryText": "Al enviar, el expediente pasa a «Pendiente de aprobación».", "marginBelow": "MORE"},
            revisa("Datos generales", 1, [("Título", "{local!exp.titulo}", True), ("Tipo", "{local!exp.tipo}"), ("Responsable", "{local!exp.responsable|map:usuarios}")]),
            revisa("Importe", 2, [("Tiene importe", "{local!exp.conImporte|map:siNo}"), ("Importe", "{local!exp.importe|eur}")]),
            revisa("Documentación", 3, [("Documentos", "{local!exp.docs.name}", True)])]},
    ],
    "secondaryButtons": [secondary("Cancelar", {"goto": "listado"}, confirmHeader="¿Descartar el alta?", confirmMessage="Se perderán los datos introducidos.", confirmButtonLabel="Descartar", cancelButtonLabel="Seguir editando")],
    "primaryButtons": [primary("Crear expediente", {"goto": "listado"}, submit=True)]},
    "P04: barra lateral con el hito vertical (DOT_VERTICAL si hay más de 5 pasos o con sidebar; MINIMAL si 1–2), un tema por paso, "
    "revisión final con «Editar» por bloque ($action.step) y confirmación al cancelar.",
    local={"local!exp": {"titulo": None, "tipo": None, "responsable": None, "conImporte": True, "importe": None, "docs": []}})

# ------------------------------------------------------------------ P05 Tarea de aprobación
p05 = screen("tarea", "Aprobar expediente", "form", "P05", ["RF-APROB"], {
    "type": "a!formLayout", "contentsWidth": "WIDE", "backgroundColor": "WHITE", "showButtonDivider": True, "isButtonFooterFixed": True,
    "titleBar": {"type": "a!headerTemplateSimple", "title": "Aprobar expediente {rv!record.codigo}", "secondaryText": "Tarea de aprobación · recibida el {rv!record.fechaEnvio|date}", "stampIcon": "check-square-o", "stampColor": "ACCENT"},
    "contents": [
        action_banner("{rv!record.plazo}", "Plazo: {rv!record.fechaLimite|date}. Si no se resuelve a tiempo, la tarea se escala a su responsable.", kind="WARN", icon="clock-o", marginBelow="MORE"),
        {"type": "a!columnsLayout", "spacing": "SPARSE", "columns": [
            {"type": "a!columnLayout", "width": "3X", "contents": [
                {"type": "a!sectionLayout", "label": "Datos del expediente", "labelSize": "MEDIUM", "labelHeadingTag": "H2", "labelColor": "STANDARD", "contents": field_summary(
                    [("Título", "{rv!record.titulo}", True), ("Tipo", "{rv!record.tipo}"), ("Unidad", "{rv!record.unidad}"), ("Importe", "{rv!record.importe|eur}"), ("Responsable", "{rv!record.responsable}"), ("Alta", "{rv!record.fechaAlta|date}")], columns=3)},
                {"type": "a!sectionLayout", "label": "Documentación", "labelSize": "MEDIUM", "labelHeadingTag": "H2", "labelColor": "STANDARD", "marginBelow": "NONE",
                 "contents": [{"type": "a!documentViewerField", "labelPosition": "COLLAPSED", "$fileName": "{rv!record.codigo}_memoria.pdf", "height": "SHORT"}]}]},
            {"type": "a!columnLayout", "width": "2X", "contents": [{"type": "a!cardLayout", "showBorder": True, "shape": "SEMI_ROUNDED", "padding": "MORE", "borderColor": "STANDARD", "contents": [
                {"type": "a!sectionLayout", "label": "Decisión", "labelSize": "MEDIUM", "labelHeadingTag": "H2", "labelColor": "STANDARD", "contents": [
                    choice_cards("Resultado", [
                        {"id": "APROBAR", "texto": "Aprobar", "detalle": "El expediente pasa a «Aprobado»", "icono": "check-circle", "color": "POSITIVE"},
                        {"id": "DEVOLVER", "texto": "Devolver para cambios", "detalle": "El gestor recibe los comentarios", "icono": "undo", "color": "#B35C00"},
                        {"id": "RECHAZAR", "texto": "Rechazar", "detalle": "El expediente queda «Rechazado»", "icono": "times-circle", "color": "NEGATIVE"}],
                        "local!decision", labelPosition="COLLAPSED", required=True, requiredMessage="Indique el resultado"),
                    par("Comentarios", "local!comentarios", required="and(a!isNotNullOrEmpty(local!decision), local!decision <> \"APROBAR\")", instructions="Obligatorios si no se aprueba")]}]}]},
        ]},
    ],
    "buttons": bl(primary("Enviar decisión", {"goto": "inicio"}, submit=True), [secondary("Cancelar", {"back": True})])},
    "P05: resumen de solo lectura (etiqueta encima, valor grande) + documento + decisión en card con choice cards; comentario obligatorio si no se aprueba; pie fijo.",
    recordType=RT, local={"local!decision": None, "local!comentarios": None})

# ------------------------------------------------------------------ P07 Diálogo
p07 = dialog("dialogo", "Editar expediente {rv!record.codigo}", [
    txt("Título", "local!titulo", required=True, characterLimit=200),
    cols(dd("Tipo", TIPOS, "local!tipo", required=True), dd("Unidad", UNIDADES, "local!unidad", required=True)),
    par("Descripción", "local!descripcion", height="SHORT"),
], bl(primary("Guardar", {"close": True}, submit=True)), ["RF-EDIT"], None, openFrom="registro", recordType=RT,
    local={"local!titulo": "{rv!record.titulo}", "local!tipo": "{rv!record.tipo}", "local!unidad": "{rv!record.unidad}", "local!descripcion": "{rv!record.descripcion}"})
p07.pop("ref")
p07["$note"] = ("P07: acción corta de registro en diálogo: solo los campos de la acción, en una columna; formulario a contentsWidth FULL y el ancho del cuadro "
                "($dialogWidth NARROW) es la Dialog Width de la acción de registro. Cancelar a la izquierda y la acción a la derecha.")

# ------------------------------------------------------------------ P08 Informe
FT = "and(or(isnull(local!tipo), fv!row.tipo = local!tipo), or(isnull(local!unidad), fv!row.unidad = local!unidad))"
G_MES = {"type": "a!columnChartField", "labelPosition": "COLLAPSED", "data": f"recordType!{RT}", "$filter": FT, "height": "SHORT", "showDataLabels": True,
         "config": {"type": "a!columnChartConfig", "primaryGrouping": {"type": "a!grouping", "field": F("mesAlta"), "interval": "MONTH_SHORT_TEXT"}, "measures": [{"type": "a!measure", "function": "COUNT", "field": F("id"), "label": "Altas"}]},
         "colorScheme": {"type": "a!colorSchemeCustom", "colors": [NAVY]}}
G_TIPO = {"type": "a!pieChartField", "labelPosition": "COLLAPSED", "data": f"recordType!{RT}", "$filter": FT, "style": "DONUT", "height": "SHORT", "showDataLabels": True, "$categories": TIPOS,
          "config": {"type": "a!pieChartConfig", "primaryGrouping": {"type": "a!grouping", "field": F("tipo")}, "measures": [{"type": "a!measure", "function": "COUNT", "field": F("id"), "label": "Expedientes"}]},
          "colorScheme": {"type": "a!colorSchemeCustom", "colors": CHART[:3]}}
G_ESTADO = {"type": "a!barChartField", "labelPosition": "COLLAPSED", "data": f"recordType!{RT}", "$filter": FT, "height": "AUTO", "showDataLabels": True, "$categories": FASES,
            "config": {"type": "a!barChartConfig", "primaryGrouping": {"type": "a!grouping", "field": F("estado")}, "secondaryGrouping": {"type": "a!grouping", "field": F("estado")},
                       "measures": [{"type": "a!measure", "function": "COUNT", "field": F("id"), "label": "Expedientes"}], "link": chart_link("local!estadoSel", RT, "estado")},
            "stacking": "NORMAL", "showLegend": False, "colorScheme": state_chart_colors(ESTADOS, FASES),
            "$note": "Cada barra con el color de su estado (el mismo significado que las etiquetas): agrupación secundaria por el mismo campo."}
p08 = screen("informe", "Informes", "page", "P08", ["RF-INFORME"], {"type": "a!headerContentLayout", "backgroundColor": BG, "contents": [
    page_header("Informes", "Distribución y evolución de los expedientes"),
    content_card([filter_bar([dd("Tipo", TIPOS, "local!tipo", placeholder="Todos los tipos", marginBelow="NONE"), dd("Unidad", UNIDADES, "local!unidad", placeholder="Todas las unidades", marginBelow="NONE"), []],
                             clear=["local!tipo", "local!unidad"], marginBelow="NONE")], marginBelow="MORE"),
    kpi_strip([
        kpi("Expedientes", "folder-open-o", sec_text="en el filtro", data=f"recordType!{RT}", primaryMeasure={"type": "a!measure", "function": "COUNT", "field": F("id")}, **{"$filter": FT}),
        kpi("Aprobados", "check-circle", sec_text="en el filtro", data=f"recordType!{RT}", primaryMeasure={"type": "a!measure", "function": "COUNT", "field": F("id")}, **{"$filter": "and(" + FT + ", fv!row.estado = \"Aprobado\")"}),
        kpi("Importe total", "eur", sec_text="expedientes con importe", data=f"recordType!{RT}", primaryMeasure={"type": "a!measure", "function": "SUM", "field": F("importe")}, **{"$filter": FT, "$format": "eur"})]),
    section_card("Altas por mes", [chart_table("local!tablaMes", G_MES, "Mes")]),
    {"type": "a!columnsLayout", "columns": [
        {"type": "a!columnLayout", "contents": [section_card("Por tipo", [chart_table("local!tablaTipo", G_TIPO, "Tipo")])]},
        {"type": "a!columnLayout", "contents": [section_card("Expedientes por estado", [
            {"type": "a!richTextDisplayField", "labelPosition": "COLLAPSED", "marginBelow": "LESS", "showWhen": "not(local!tablaEstado)",
             "value": [{"type": "a!richTextItem", "text": "Pulse una barra para ver sus expedientes", "color": "SECONDARY", "size": "SMALL"}]},
            chart_table("local!tablaEstado", G_ESTADO, "Estado"),
            {"type": "a!sectionLayout", "showWhen": "a!isNotNullOrEmpty(local!estadoSel)", "label": "Expedientes en «{local!estadoSel}»", "labelSize": "SMALL", "labelHeadingTag": "H3", "labelColor": "SECONDARY", "marginAbove": "STANDARD", "contents": [
                grid(f"recordType!{RT}", "and(" + FT + ", fv!row.estado = local!estadoSel)", [gcol("Expediente", two_line("{fv!row.codigo}", "{fv!row.titulo}", {"type": "a!recordLink", "recordType": f"recordType!{RT}", "identifier": "{fv!row.id}"})), gcol("Unidad", "{fv!row.unidad}", width="NARROW"), gcol_num("Importe", "{fv!row.importe|eur|dash}", width="NARROW_PLUS")],
                     "No hay expedientes", page_size=5)]}])]}]},
]}, "P08: filtros de página en una barra y franja de KPI calculados con los filtros. Un gráfico con más de 7 puntos va solo, a todo el ancho y arriba; "
    "los pequeños, en parejas. Cada gráfico con su tabla alternativa (chart_table: enlace «Ver como tabla») y uno que profundiza a sus registros (chart_link).",
    local={"local!tipo": None, "local!unidad": None, "local!estadoSel": None, "local!tablaMes": False, "local!tablaTipo": False, "local!tablaEstado": False})

# ------------------------------------------------------------------ P09 Maestro-detalle
p09 = screen("maestro", "Bandeja de revisión", "page", "P09", ["RF-APROB"], {"type": "a!headerContentLayout", "backgroundColor": BG, "contents": [
    page_header("Bandeja de revisión", "Expedientes pendientes de su aprobación, uno tras otro"),
    grid_with_detail(f"recordType!{RT}", "local!sel", [gcol("Expediente", two_line("{fv!row.codigo}", "{fv!row.titulo}")), gcol("Recibido", "{fv!row.fechaEnvio|date}", width="NARROW"),
                                                   gcol_num("Importe", "{fv!row.importe|eur|dash}", width="NARROW_PLUS")], [
        subsection("{fv!item.codigo}", [two_line("{fv!item.titulo}", "{fv!item.tipo} · {fv!item.unidad} · recibido el {fv!item.fechaEnvio|date}"), tag("fv!item.estado", "estadoColor")]),
        *field_summary([("Responsable", "{fv!item.responsable}"), ("Importe", "{fv!item.importe|eur|dash}"), ("Descripción", "{fv!item.descripcion}", True)], columns=2),
        {"type": "a!buttonArrayLayout", "align": "END", "marginBelow": "NONE", "buttons": [secondary("Abrir ficha", {"goto": "registro", "params": {"id": "{fv!item.id}"}}), primary("Revisar", {"goto": "tarea", "params": {"id": "{fv!item.id}"}})]}],
        "No tiene expedientes pendientes", flt="fv!row.estado = \"Pendiente de aprobación\""),
]}, "P09: lista a la izquierda con fila resaltada (una selección, la primera seleccionada al entrar) y detalle al lado; la acción principal en el detalle. "
    "Si el detalle no cabe al lado, drilldown (bloques.md).", local={"local!sel": [2]})

# ------------------------------------------------------------------ P10 Portada de módulo
_ev = []
for r in ROWS:
    if r["fechaEnvio"]: _ev.append({"event": f"Expediente {r['codigo']} enviado a aprobación", "user": r["responsable"], "timestamp": r["fechaEnvio"] + "T10:15"})
    _ev.append({"event": f"Nuevo expediente {r['codigo']}", "user": r["responsable"], "timestamp": r["fechaAlta"] + "T09:05"})
ACTIVIDAD = sorted(_ev, key=lambda e: e["timestamp"], reverse=True)[:3]
p10 = screen("portada", "Gestión de expedientes", "page", "P10", ["RF-INICIO"], {"type": "a!headerContentLayout", "backgroundColor": BG, "contents": [
    hero_header("Gestión de expedientes", "Alta, tramitación y aprobación de los expedientes de su unidad", [("folder-open-o", str(cnt("En tramitación")), "en tramitación"), ("hourglass-half", str(len(PEND)), "pendientes de aprobación"), ("check-circle", str(cnt("Aprobado")), "aprobados este año")],
                [primary("Nuevo expediente", NUEVO, "plus")]),
    {"type": "a!headingField", "text": "¿Qué quiere hacer?", "size": "MEDIUM", "headingTag": "H2", "marginBelow": "STANDARD"},
    cards_as_buttons([("search", "Consultar expedientes", "Busque y siga el estado de cualquier expediente.", {"goto": "listado"}),
                      ("inbox", "Revisar pendientes", "Apruebe o devuelva los expedientes que le han asignado.", {"goto": "maestro"}),
                      ("bar-chart", "Informes", "Evolución, importes y expedientes por estado.", {"goto": "informe"})]),
    {"type": "a!columnsLayout", "columns": [
        {"type": "a!columnLayout", "width": "2X", "contents": [section_card("Actividad reciente", [
            {"type": "a!eventHistoryListField", "labelPosition": "COLLAPSED", "eventStyle": "PREVIEW_LIST", "previewListPageSize": 3, "$events": ACTIVIDAD},
            link_all("Ver toda la actividad", {"goto": "listado"})])]},
        {"type": "a!columnLayout", "contents": [
            action_banner(f"{len(PEND)} expedientes esperan su aprobación", f"El más antiguo, {PEND[0]['codigo']}, se recibió el {fmt_date(PEND[0]['fechaEnvio'])}", secondary("Revisar", {"goto": "maestro"}, size="SMALL"), kind="WARN", icon="clock-o", marginBelow="MORE"),
            section_card("Ayuda", [{"type": "a!richTextDisplayField", "labelPosition": "COLLAPSED", "value": [
                {"type": "a!richTextIcon", "icon": "book", "color": "ACCENT"}, " ", {"type": "a!richTextItem", "text": "Guía de tramitación", "link": {"type": "a!safeLink", "uri": "https://intranet.example.com/guia-de-tramitacion"}, "linkStyle": "STANDALONE"}, "\n",
                {"type": "a!richTextIcon", "icon": "question-circle", "color": "ACCENT"}, " ", {"type": "a!richTextItem", "text": "Preguntas frecuentes", "link": {"type": "a!safeLink", "uri": "https://intranet.example.com/preguntas-frecuentes"}, "linkStyle": "STANDALONE"}]}])]},
    ]},
]}, "P10: entrada a un área con varias opciones: cabecera hero con cifras y la acción principal, accesos como cards-botón (2–6), actividad reciente y avisos con acción.")

# ------------------------------------------------------------------ P11 Asistente de IA
p11 = screen("ia", "Asistente del expediente", "page", "P11", ["RF-FICHA"], {"type": "a!headerContentLayout", "backgroundColor": BG, "contents": [
    page_header("Informes de tramitación", "Pida al asistente un borrador del informe de un expediente y revíselo antes de guardarlo"),
    cols([content_card([ai_agent_chat("Asistente de expedientes", "agent!EXP_ASISTENTE", "Puedo buscar expedientes, resumir su historial y redactar un borrador del informe de tramitación para que usted lo revise.",
                                      placeholder="Pregunte por un expediente o pida un informe", height="TALL", outputs=[{"type": "a!save", "target": "local!borrador", "value": "save!value.informe"}],
                                      **{"$replies": [{"text": "He redactado el **borrador del informe** del EXP-2026-0003 con los datos del expediente y su historial. Lo tiene a la derecha para revisarlo.",
                                                       "tools": [{"tool": "Consultar expediente", "text": "EXP-2026-0003"}, {"tool": "Redactar informe"}],
                                                       "outputs": {"informe": {"expediente": "EXP-2026-0003", "texto": "El expediente se tramitó en plazo. Consta la documentación requerida y el importe se ajusta al presupuesto aprobado."}}}]})], padding="NONE")],
         [{"type": "a!sectionLayout", "label": "Borrador propuesto", "labelSize": "MEDIUM", "labelHeadingTag": "H2", "labelColor": "STANDARD", "contents": [
             empty_state("magic", "Aún no hay borrador", "Pida al asistente que redacte el informe de un expediente", showWhen="a!isNullOrEmpty(local!borrador)"),
             content_card([ai_notice("Borrador generado con IA: revíselo antes de guardarlo"), ro("Expediente", "{local!borrador.expediente}"), par("Informe", "local!borrador.texto", height="MEDIUM"),
                           ai_feedback("local!valoracion", marginBelow="STANDARD"),
                           {"type": "a!buttonArrayLayout", "align": "END", "marginBelow": "NONE", "buttons": [secondary("Descartar", {"set": {"local!borrador": None}}), primary("Guardar informe")]}],
                          showWhen="a!isNotNullOrEmpty(local!borrador)")]}],
         widths=["AUTO", "MEDIUM_PLUS"]),
]}, "P11: solo si el análisis pide IA (si no, propuesta con $assumption). Chat del agente en una card sin relleno y, al lado, lo que propone en campos editables "
    "que el usuario revisa y guarda (outputsSaveInto); aviso de fiabilidad y valoración. Variantes: a página completa (height FILL), documento + chat (ai_doc_chat) "
    "y chat de datos en panel (ai_side_pane). Reglas en design-rules.md §14.", local={"local!borrador": None, "local!valoracion": None},
    **{"$assumption": "Propuesta: asistente de IA para redactar el informe de tramitación (no está en los requisitos)."})

# ------------------------------------------------------------------ P12 Revisión de datos sugeridos por IA
campos = [{"campo": "Unidad", "valor": "OES", "confianza": "ALTA", "origen": "IA", "revisado": True, "pagina": 1},
          {"campo": "Tipo", "valor": "Servicio", "confianza": "ALTA", "origen": "IA", "revisado": True, "pagina": 1},
          {"campo": "Fecha de inicio", "valor": "01/10/2026", "confianza": "MEDIA", "origen": "IA", "revisado": True, "pagina": 2},
          {"campo": "Importe", "valor": "12.400,00 €", "confianza": "BAJA", "origen": "IA", "revisado": False, "pagina": 3},
          {"campo": "Responsable", "valor": "Javier García", "confianza": "BAJA", "origen": "IA", "revisado": False, "pagina": 3}]
p12 = screen("revision-ia", "Revisar datos extraídos", "form", "P12", ["RF-ALTA"], {
    "type": "a!formLayout", "titleBar": "Revisar datos extraídos de la solicitud", "contentsWidth": "FULL", "backgroundColor": "WHITE", "showButtonDivider": True, "isButtonFooterFixed": True,
    "contents": [
        action_banner("Revise los datos con confianza baja", "La IA ha rellenado 5 campos a partir de la solicitud escaneada. Pulse «Página N» para ver de dónde sale cada dato.", kind="INFO", icon="magic", marginBelow="MORE"),
        {"type": "a!columnsLayout", "columns": [
            {"type": "a!columnLayout", "width": "3X", "contents": [ai_review_grid("local!campos", page_var="local!pagina", quote_var="local!cita"),
                                                                   ai_notice("Al guardar se comprueba que estén revisados los datos de confianza baja.", marginAbove="STANDARD")]},
            {"type": "a!columnLayout", "width": "2X", "contents": [{"type": "a!documentViewerField", "label": "Solicitud escaneada", "labelPosition": "COLLAPSED", "document": "local!doc", "height": "TALL",
                                                                    "initialPageDisplay": "local!pagina", "highlightedText": "local!cita", "altText": "Solicitud escaneada", "$fileName": "Solicitud_EXP-2026-0013.pdf", "$pages": 3,
                                                                    "$content": [["Solicitud de expediente", "Unidad solicitante: OES", "Tipo de expediente: Servicio"], ["Fecha prevista de inicio: 01/10/2026"], ["Importe estimado: 12.400,00 €", "Responsable: Javier García"]]}]}]},
    ],
    "validations": [ai_review_validation("local!campos")],
    "buttons": bl(primary("Guardar datos", {"goto": "listado"}, submit=True), [secondary("Cancelar", {"goto": "listado"})])},
    "P12: datos que ha rellenado la IA con origen y confianza; la fuente al lado (visor que salta a la página y resalta el valor); editar un dato lo marca como editado "
    "y revisado; Guardar valida y, si queda algún dato de confianza baja sin revisar, el mensaje del formulario dice qué falta (nunca un botón desactivado sin explicación). "
    "La IA nunca guarda: guarda el usuario.",
    local={"local!campos": campos, "local!doc": 13, "local!pagina": 1, "local!cita": None})

# ------------------------------------------------------------------ P06 Inicio
aprobado = sum(r["importe"] for r in ROWS if r["estado"] == "Aprobado")
p06 = screen("inicio", "Inicio", "page", "P06", ["RF-INICIO"], {"type": "a!headerContentLayout", "backgroundColor": BG, "contents": [
    hero_header("Hola, María", "Expedientes de su unidad · jueves, 24 de septiembre de 2026", [("inbox", str(len(TAREAS)), "tareas pendientes"), ("clock-o", str(sum(1 for t in TAREAS if t["dias"] <= 7)), "vence esta semana")],
                [primary("Nuevo expediente", NUEVO, "plus")]),
    kpi_strip([
        kpi("En tramitación", "hourglass-half", secondary=cnt("En tramitación") + 1, sec_text="frente al mes anterior", data=f"recordType!{RT}", primaryMeasure={"type": "a!measure", "function": "COUNT", "field": F("id")}, **{"$filter": "fv!row.estado = \"En tramitación\""}),
        kpi("Pendientes de aprobación", "gavel", secondary=len(PEND) + 2, sec_text="frente al mes anterior", reverse=True, data=f"recordType!{RT}", primaryMeasure={"type": "a!measure", "function": "COUNT", "field": F("id")}, **{"$filter": "fv!row.estado = \"Pendiente de aprobación\""}),
        kpi("Importe aprobado", "eur", secondary=aprobado - 90000, sec_text="frente al mes anterior", data=f"recordType!{RT}", primaryMeasure={"type": "a!measure", "function": "SUM", "field": F("importe")}, **{"$filter": "fv!row.estado = \"Aprobado\"", "$format": "eur"})]),
    {"type": "a!columnsLayout", "columns": [
        {"type": "a!columnLayout", "width": "2X", "contents": [section_card("Mis tareas", [
            grid("data!tareas", None, [
                gcol_link("Tarea", "Aprobar {fv!row.codigo}", {"goto": "tarea", "params": {"id": "{fv!row.expedienteId}"}}, "{fv!row.titulo}"),
                gcol("Recibida", "{fv!row.recibida|date}", width="NARROW"),
                gcol("Plazo", {"type": "a!tagField", "labelPosition": "COLLAPSED", "size": "SMALL", "tags": [{"type": "a!tagItem", "text": "{fv!row.plazo}", "backgroundColor": "{fv!row.urgente|map:plazoColor}"}]}, width="NARROW_PLUS"),
            ], "No tiene tareas pendientes", page_size=10, **{"$note": "En Appian: record type de tareas o a!queryProcessAnalytics. 5–10 tareas sin paginación."}),
            link_all("Ver todas", {"goto": "maestro"})])]},
        {"type": "a!columnLayout", "contents": [
            action_banner(f"{TAREAS[0]['codigo']}: {TAREAS[0]['plazo'].lower()}", "Si no se resuelve a tiempo, la tarea se escala a su responsable", secondary("Revisar", {"goto": "tarea", "params": {"id": TAREAS[0]["expedienteId"]}}, size="SMALL"),
                          kind="WARN", icon="clock-o", marginBelow="MORE"),
            section_card("Accesos rápidos", [{"type": "a!recordActionField", "style": "CARDS", "display": "LABEL_AND_ICON", "actions": [
                {"type": "a!recordActionItem", "action": f"recordType!{RT}.actions.altaDesdeSolicitud", "$label": "Alta desde solicitud escaneada", "$icon": "magic", "$action": {"goto": "revision-ia"}},
                {"type": "a!recordActionItem", "action": f"recordType!{RT}.actions.altaRapida", "$label": "Alta rápida (una página)", "$icon": "bolt", "$action": {"goto": "formulario"}}]}],
                **{"$note": "Otras acciones del registro; la principal («Nuevo expediente») ya está en la cabecera y no se repite."}),
            section_card("Por estado", [chart_table("local!tablaEstado", {"type": "a!barChartField", "labelPosition": "COLLAPSED", "data": f"recordType!{RT}", "height": "AUTO", "showDataLabels": True, "$categories": FASES,
                "config": {"type": "a!barChartConfig", "primaryGrouping": {"type": "a!grouping", "field": F("estado")}, "secondaryGrouping": {"type": "a!grouping", "field": F("estado")},
                           "measures": [{"type": "a!measure", "function": "COUNT", "field": F("id"), "label": "Expedientes"}]},
                "stacking": "NORMAL", "showLegend": False, "colorScheme": state_chart_colors(ESTADOS, FASES)}, "Estado")]),
        ]},
    ]},
]}, "P06: cabecera de color (saludo, fecha y lo pendiente) + franja de KPI (una card, divisores, sellos de icono, tendencia) + 2X/1X: tareas sin paginación con plazo y «Ver todas»; "
    "a la derecha, aviso con acción, accesos rápidos y un gráfico resumen con su tabla alternativa.", local={"local!tablaEstado": False})

# ------------------------------------------------------------------ P02 Vista de registro
REC = "rv!record"
p02 = {"id": "registro", "title": "{rv!record.codigo} · {rv!record.titulo}", "type": "record", "pattern": "P02", "recordType": RT, "req": ["RF-FICHA"],
       "$note": "P02: cabecera azul marino con ≤3 acciones; Resumen = franja de datos clave + hito + aviso + 2X/1X (datos que no están en la franja / documentos recientes); las áreas 1:N en vistas.",
       "breadcrumb": {"label": "Expedientes", "goto": "listado"}, "headerBackgroundColor": NAVY,
       "local": {"local!comentarios": [
           {"id": 1, "autor": "Rocío Sánchez Vidal", "fecha": "2026-09-12T10:20", "texto": "Adjunto el presupuesto actualizado con las bancadas de cuatro plazas.", "adjuntos": [{"nombre": "Presupuesto_bancadas_v2.xlsx", "tipo": "excel", "tamano": "38 KB"}], "padre": None},
           {"id": 2, "autor": "María López Arranz", "fecha": "2026-09-12T12:05", "texto": "Gracias. ¿Incluye la toma de carga USB-C en todas las plazas?", "adjuntos": [], "padre": 1},
           {"id": 3, "autor": "Rocío Sánchez Vidal", "fecha": "2026-09-12T13:40", "texto": "Sí, en las cuatro plazas de cada bancada.", "adjuntos": [], "padre": 1}],
                 "local!nuevoComentario": None, "local!respondiendoA": None, "local!respuesta": None},
       "recordActions": [{"type": "a!recordActionItem", "action": f"recordType!{RT}.actions.editar", "identifier": "{rv!record.id}", "$label": "Editar", "$icon": "pencil", "$action": {"dialog": "dialogo", "params": {"id": "{rv!record.id}"}}},
                         por_perfil({"type": "a!recordActionItem", "action": f"recordType!{RT}.actions.cerrar", "identifier": "{rv!record.id}", "$label": "Cerrar expediente", "$icon": "lock"},
                                    "el responsable de la unidad", "accion")],
       "views": [
           {"id": "resumen", "label": "Resumen", "interface": {"type": "a!headerContentLayout", "backgroundColor": BG, "contents": [
               key_facts([("Estado", tag("rv!record.estado", "estadoColor")), ("Tipo", "{rv!record.tipo}"), ("Unidad", "{rv!record.unidad}"), ("Importe", "{rv!record.importe|eur}"), ("Responsable", "{rv!record.responsable}")],
                         extra=milestone(FASES[:5], "{rv!record.estado|map:estadoPaso}")),
               action_banner("Pendiente de aprobación", "El expediente espera la decisión del aprobador", kind="INFO", marginBelow="MORE", showWhen="rv!record.estado = \"Pendiente de aprobación\""),
               {"type": "a!columnsLayout", "columns": [
                   {"type": "a!columnLayout", "width": "2X", "contents": [section_card("Datos del expediente", field_summary([("Título", "{rv!record.titulo}", True), ("Fecha de alta", "{rv!record.fechaAlta|date}"), ("Enviado a aprobación", "{rv!record.fechaEnvio|date|dash}"), ("Descripción", "{rv!record.descripcion}", True)], columns=2))]},
                   {"type": "a!columnLayout", "contents": [section_card("Documentos recientes", [
                       {"type": "a!forEach", "items": "data!documentos", "$filter": "fv!item.expedienteId = rv!record.id", "$limit": 3, "expression": doc_line("{fv!item.nombre}", "{fv!item.meta}", None, "{fv!item.icono}")},
                       link_all("Ver todos los documentos", {"goto": "registro", "params": {"id": "{rv!record.id}"}, "view": "documentos"})])]},
               ]}]}},
           {"id": "documentos", "label": "Documentos", "interface": {"type": "a!headerContentLayout", "backgroundColor": BG, "contents": [
               section_card("Documentos", [document_list("data!documentos", flt="fv!item.expedienteId = rv!record.id", **{"$note": "En Appian: record type de documentos relacionado con EXP Expediente (1:N)."})])]}},
           {"id": "comentarios", "label": "Comentarios", "interface": {"type": "a!headerContentLayout", "backgroundColor": BG, "contents": [
               {"type": "a!columnsLayout", "columns": [{"type": "a!columnLayout", "width": "WIDE_PLUS", "contents": [
                   comment_thread("local!comentarios", "María López Arranz", "local!nuevoComentario", "local!respondiendoA", "local!respuesta",
                                  **{"$note": "En Appian: record type de comentarios relacionado con el expediente (1:N; padre = comentario al que responde) y adjuntos como documentos."})]},
                   {"type": "a!columnLayout", "contents": []}]}]}},
           {"id": "historial", "label": "Historial", "interface": {"type": "a!headerContentLayout", "backgroundColor": BG, "contents": [content_card([
               {"type": "a!eventHistoryListField", "labelPosition": "COLLAPSED", "eventStyle": "TIMELINE", "commentLayout": "CARD", "$events": [
                   {"event": "Enviado a aprobación", "user": "{rv!record.responsable}", "timestamp": "{rv!record.fechaAlta}T12:00:00", "comment": "Adjunto el presupuesto actualizado."},
                   {"event": "Expediente creado", "user": "{rv!record.responsable}", "timestamp": "{rv!record.fechaAlta}T09:00:00"}]}], padding="MORE")]}},
       ]}

TEMPLATES = {"P02-vista-registro.json": p02, "P06-inicio.json": p06, "P01-listado.json": p01, "P03-formulario.json": p03, "P04-asistente.json": p04, "P05-tarea-aprobacion.json": p05, "P07-dialogo.json": p07, "P08-informe.json": p08,
             "P09-maestro-detalle.json": p09, "P10-portada-modulo.json": p10, "P11-asistente-ia.json": p11, "P12-revision-ia.json": p12}

if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):  # consolas de Windows sin UTF-8: «→» o «✓» no caben en cp1252
        _s.reconfigure(encoding="utf-8", errors="replace")
    for name, s in TEMPLATES.items():
        (HERE / name).write_text(json.dumps(clean(s), ensure_ascii=False, indent=1), encoding="utf-8")
    cat = json.loads((HERE / "catalogo-patrones.json").read_text(encoding="utf-8"))
    order = [p06, p10, p01, p09, p02, p03, p04, p05, p07, p08, p11, p12]
    cat["app"]["name"] = "Catálogo de patrones"
    cat["app"]["today"] = TODAY.isoformat()
    cat["app"]["appianVersion"] = "26.9"  # versión vigente: las plantillas usan lo último de Appian
    cat["data"] = {"expedientes": {"recordType": RT, "rows": ROWS}, "tareas": TAREAS, "documentos": DOCS}
    cat["screens"] = [clean(s) for s in order]
    cat["maps"] = {**ATTACH_MAPS, "estadoColor": state_map(ESTADOS), "estadoColorGrid": state_map(ESTADOS, grid=True), "estadoPaso": {e: k + 1 for k, e in enumerate(FASES)},
                   "plazoColor": {"true": STATES["atencion"]["tag"], "*": STATES["neutral"]["tag"]},
                   "siNo": {"true": "Sí", "false": "No", "*": "–"}, "usuarios": {u["id"]: u["name"] for u in cat.get("users", [])}, **AI_MAPS}
    cat["site"]["pages"] = [{"title": "P06 Inicio", "icon": "home", "screen": "inicio", "includes": ["tarea"]},
                            {"title": "P10 Portada", "icon": "th-large", "screen": "portada"},
                            {"title": "P01 Listado", "icon": "list", "screen": "listado", "includes": ["registro", "asistente", "formulario"]},
                            {"title": "P09 Bandeja", "icon": "inbox", "screen": "maestro"},
                            {"title": "P03 Formulario", "icon": "file-text-o", "screen": "formulario"},
                            {"title": "P08 Informe", "icon": "bar-chart", "screen": "informe"},
                            {"title": "P11 IA", "icon": "magic", "screen": "ia", "includes": ["revision-ia"]}]
    capp = {"registro": {"params": {"id": PEND[0]["id"]}}, "tarea": {"params": {"id": PEND[0]["id"]}}, "dialogo": {"params": {"id": PEND[0]["id"]}, "hostParams": {"id": PEND[0]["id"]}}}
    cat["captures"] = [{"name": f"{k + 1:02d}-{s['pattern']}-{s['id']}", "screen": s["id"], **capp.get(s["id"], {})} for k, s in enumerate(order)]
    (HERE / "catalogo-patrones.json").write_text(json.dumps(cat, ensure_ascii=False, indent=1), encoding="utf-8")
    print("ok:", ", ".join(TEMPLATES), "+ catalogo-patrones.json")
