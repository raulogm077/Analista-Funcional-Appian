"""Genera examples/atp/app.json. Uso: python3 generar_app.py app.json
Ejemplo de cómo escribir specs grandes con los helpers del kit (scripts/sail_helpers.py) y la guía de diseño
(references/design-rules.md): páginas con cards blancas sobre fondo gris, franja de KPI, franja de datos clave,
grids consolidados, paleta semántica de estados, asistente con barra lateral y decisión con cards."""
import json, datetime, random, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from sail_helpers import *  # noqa: E402,F401
ATP_ESTADOS = {"Borrador": "neutral", "En revisión jurídica": "enCurso", "Pendiente de firma": "atencion", "Vigente": "positivo", "Vencido": "negativo", "Rechazado": "negativo"}
ATP_FASES = ["Borrador", "En revisión jurídica", "Pendiente de firma", "Vigente", "Vencido", "Rechazado"]
random.seed(7)
TODAY = datetime.date(2026, 9, 24)

# ------------------------------------------------------------------ data
users = [{"id": u, "name": n} for u, n in [
    ("mlopez", "María López Arranz"), ("jgarcia", "Javier García Ruiz"), ("rsanchez", "Rocío Sánchez Vidal"),
    ("pmartin", "Pablo Martín Ortega"), ("lfernandez", "Lucía Fernández Gil"), ("amoreno", "Andrés Moreno Pastor")]]
rows_src = [
    ("Convenio de colaboración para formación en seguridad aeroportuaria", "Convenio", "Universidad Politécnica de Madrid", "Q2818015F", "Universidad o centro de investigación", "MAD", "mlopez", "2025-03-01", "2027-02-28", True, False, 0, "Vigente", "2025-01-20"),
    ("Acuerdo de confidencialidad proyecto biometría en filtros", "Acuerdo de confidencialidad", "Veridas Digital Authentication", "B71330001", "Empresa privada", "BCN", "jgarcia", "2026-02-15", "2026-11-30", False, False, 0, "Vigente", "2026-02-02"),
    ("Protocolo general de actuación con el Ayuntamiento de El Prat", "Protocolo general de actuación", "Ajuntament del Prat de Llobregat", "P0816800A", "Administración pública", "BCN", "rsanchez", "2024-06-01", "2026-12-15", False, False, 0, "Vigente", "2024-05-10"),
    ("Contrato de colaboración para la promoción turística de Canarias", "Contrato de colaboración", "Turismo de Canarias S.A.", "A35077817", "Administración pública", "LPA", "pmartin", "2026-01-01", "2026-12-31", True, True, 180000, "Vigente", "2025-11-18"),
    ("Convenio de prácticas para grado en ingeniería aeroespacial", "Convenio", "Universidad de Sevilla", "Q4118001I", "Universidad o centro de investigación", "SVQ", "lfernandez", "2026-10-01", "2028-09-30", True, False, 0, "Pendiente de firma", "2026-07-28"),
    ("Acuerdo de colaboración en eficiencia energética de terminales", "Contrato de colaboración", "Iberdrola Clientes S.A.U.", "A95758389", "Empresa privada", "SSCC", "amoreno", "2026-11-01", "2029-10-31", False, True, 420000, "En revisión jurídica", "2026-09-02"),
    ("Protocolo de coordinación de emergencias con la Comunidad de Madrid", "Protocolo general de actuación", "Comunidad de Madrid · ASEM112", "S7800001E", "Administración pública", "MAD", "mlopez", "2023-04-01", "2026-03-31", False, False, 0, "Vencido", "2023-03-02"),
    ("Acuerdo de confidencialidad licitación de handling", "Acuerdo de confidencialidad", "Groundforce Cargo S.L.", "B84527977", "Empresa privada", "SSCC", "jgarcia", "2026-09-10", "2027-09-09", False, False, 0, "En revisión jurídica", "2026-09-12"),
    ("Convenio de patrocinio del festival de cine de Málaga", "Convenio", "Festival de Málaga", "P2906700F", "Administración pública", "AGP", "pmartin", "2026-02-01", "2026-10-31", False, True, 35000, "Vigente", "2026-01-12"),
    ("Contrato de colaboración para movilidad eléctrica en aparcamientos", "Contrato de colaboración", "Zunder Charging S.L.", "B42812727", "Empresa privada", "VLC", "rsanchez", "2026-12-01", "2030-11-30", True, True, 96000, "Borrador", "2026-09-18"),
    ("Convenio con la Guardia Civil para el control de fronteras", "Convenio", "Dirección General de la Guardia Civil", "S2816003D", "Administración pública", "PMI", "amoreno", "2025-07-01", "2027-06-30", True, False, 0, "Vigente", "2025-06-05"),
    ("Acuerdo de confidencialidad sobre datos de tráfico", "Acuerdo de confidencialidad", "Cirium Data Services Ltd.", "N0073581E", "Empresa privada", "SSCC", "lfernandez", "2026-06-01", "2027-05-31", False, False, 0, "Rechazado", "2026-05-20"),
    ("Convenio de investigación sobre ruido en entornos aeroportuarios", "Convenio", "CSIC · Instituto de Acústica", "Q2818002D", "Universidad o centro de investigación", "MAD", "mlopez", "2026-04-01", "2028-03-31", False, True, 64000, "Vigente", "2026-03-03"),
    ("Contrato de colaboración de accesibilidad PMR", "Contrato de colaboración", "Fundación ONCE", "G78661923", "Otro", "BIO", "jgarcia", "2026-10-15", "2027-10-14", True, True, 22000, "En revisión jurídica", "2026-09-20"),
    ("Protocolo con Renfe para intermodalidad tren-avión", "Protocolo general de actuación", "Renfe Viajeros S.M.E. S.A.", "A86868189", "Administración pública", "MAD", "pmartin", "2025-10-01", "2027-09-30", True, False, 0, "Vigente", "2025-09-08"),
    ("Acuerdo de confidencialidad piloto de drones de inspección", "Acuerdo de confidencialidad", "Arbórea Intellbird S.L.", "B37534129", "Empresa privada", "SVQ", "rsanchez", "2026-08-01", "2027-01-31", False, False, 0, "Pendiente de firma", "2026-07-15"),
]
uname = {u["id"]: u["name"] for u in users}
acuerdos = []
for i, r in enumerate(rows_src, start=1):
    (tit, tipo, ter, cif, tter, apt, resp, ini, fin, pro, conimp, imp, est, alta) = r
    dfin = datetime.date.fromisoformat(fin)
    acuerdos.append({
        "id": i, "codigo": f"ATP-{alta[:4]}-{i:04d}", "titulo": tit, "tipo": tipo, "tercero": ter, "cif": cif,
        "tipoTercero": tter, "aeropuerto": apt, "responsable": uname[resp], "responsableId": resp,
        "fechaInicio": ini, "fechaFin": fin, "prorroga": pro, "conImporte": conimp, "importe": imp if conimp else None,
        "contraprestacion": "Cesión de espacios y difusión institucional" if conimp else None,
        "estado": est, "fechaAlta": alta, "mesAlta": alta[:7], "diasParaVencer": (dfin - TODAY).days,
    })
tareas = [
    {"id": 1, "tarea": "Revisar acuerdo", "acuerdoId": 6, "codigo": "ATP-2026-0006", "titulo": acuerdos[5]["titulo"], "recibida": "2026-09-02", "vence": "2026-09-26", "prioridad": "Alta"},
    {"id": 2, "tarea": "Revisar acuerdo", "acuerdoId": 8, "codigo": "ATP-2026-0008", "titulo": acuerdos[7]["titulo"], "recibida": "2026-09-12", "vence": "2026-09-30", "prioridad": "Media"},
    {"id": 3, "tarea": "Revisar acuerdo", "acuerdoId": 14, "codigo": "ATP-2026-0014", "titulo": acuerdos[13]["titulo"], "recibida": "2026-09-20", "vence": "2026-10-06", "prioridad": "Baja"},
]
for t in tareas:
    d = (datetime.date.fromisoformat(t["vence"]) - TODAY).days
    t["plazo"] = f"Vence en {d} días" if d > 1 else "Vence mañana" if d == 1 else "Vence hoy"
    t["urgente"] = d <= 3
documentos = []
did = 1
for a in acuerdos:
    for nombre, tipo in [(f"{a['codigo']}_texto_acuerdo.pdf", "Texto del acuerdo"), (f"{a['codigo']}_memoria_justificativa.docx", "Memoria justificativa")] + ([(f"{a['codigo']}_acuerdo_firmado.pdf", "Acuerdo firmado")] if a["estado"] in ("Vigente", "Vencido") else []):
        kb = random.randint(180, 2400)
        documentos.append({"id": did, "acuerdoId": a["id"], "nombre": nombre, "tipo": tipo, "subidoPor": a["responsable"], "fecha": a["fechaAlta"],
                           "tamano": f"{kb} KB" if kb < 1000 else f"{kb / 1024:.1f} MB".replace(".", ","), "icono": "file-pdf-o" if nombre.endswith(".pdf") else "file-word-o"})
        did += 1
eventos = []
for a in acuerdos:
    ev = [("Acuerdo creado", a["responsable"], a["fechaAlta"] + "T09:14:00", "Alta en estado Borrador", None)]
    if a["estado"] != "Borrador":
        ev.append(("Enviado a revisión jurídica", a["responsable"], a["fechaAlta"] + "T12:40:00", None, None))
    if a["estado"] in ("Pendiente de firma", "Vigente", "Vencido"):
        ev.append(("Aprobado por Asesoría Jurídica", "Lucía Fernández Gil", a["fechaAlta"] + "T17:05:00", None, "Conforme. Revisada la cláusula de protección de datos."))
    if a["estado"] == "Rechazado":
        ev.append(("Rechazado por Asesoría Jurídica", "Lucía Fernández Gil", a["fechaAlta"] + "T17:05:00", None, "El objeto del acuerdo requiere licitación pública."))
    if a["estado"] in ("Vigente", "Vencido"):
        ev.append(("Acuerdo firmado", a["responsable"], a["fechaInicio"] + "T10:00:00", "Estado: Vigente", None))
    for e in reversed(ev):
        eventos.append({"acuerdoId": a["id"], "event": e[0], "user": e[1], "timestamp": e[2], "details": e[3], "comment": e[4]})

RT = "ATP Acuerdo"
F = lambda f: f"recordType!{RT}.fields.{f}"
TIPOS = ["Convenio", "Contrato de colaboración", "Acuerdo de confidencialidad", "Protocolo general de actuación"]
TIPOS_ICON = ["handshake-o", "file-text-o", "lock", "sitemap"]
TIPOS_TERCERO = ["Empresa privada", "Administración pública", "Universidad o centro de investigación", "Otro"]
AEROPUERTOS = ["SSCC", "MAD", "BCN", "PMI", "AGP", "LPA", "SVQ", "VLC", "BIO"]
AEROPUERTOS_L = ["Servicios Centrales", "Adolfo Suárez Madrid-Barajas (MAD)", "Josep Tarradellas Barcelona-El Prat (BCN)", "Palma de Mallorca (PMI)", "Málaga-Costa del Sol (AGP)", "Gran Canaria (LPA)", "Sevilla (SVQ)", "Valencia (VLC)", "Bilbao (BIO)"]
VENCE = "and(fv!row.estado = \"Vigente\", fv!row.diasParaVencer <= 90, fv!row.diasParaVencer >= 0)"
n_vencen = sum(1 for a in acuerdos if a["estado"] == "Vigente" and 0 <= a["diasParaVencer"] <= 90)

def kpi_rt(text, icon, flt, secondary, sec_text, reverse=False, fmt=None, measure=None):
    k = kpi(text, icon, secondary=secondary, sec_text=sec_text, reverse=reverse, data=f"recordType!{RT}",
            primaryMeasure=measure or {"type": "a!measure", "function": "COUNT", "field": F("id")})
    k["$filter"] = flt
    if fmt: k["$format"] = fmt
    return k

# ------------------------------------------------------------------ P06 Inicio
inicio = {
    "id": "inicio", "title": "Inicio", "type": "page", "pattern": "P06", "ref": "PAN-01 · Inicio", "req": ["RF-01", "RF-02", "RF-11"],
    "interface": {"type": "a!headerContentLayout", "backgroundColor": BG, "contents": [
        page_header("Hola, Lucía", "Acuerdos con terceras partes · 24 de septiembre de 2026", [primary("Nuevo acuerdo", {"goto": "alta"}, "plus")]),
        kpi_strip([
            kpi_rt("Acuerdos vigentes", "handshake-o", "fv!row.estado = \"Vigente\"", 7, "vs. agosto"),
            kpi_rt("En revisión jurídica", "gavel", "fv!row.estado = \"En revisión jurídica\"", 1, "vs. agosto", reverse=True),
            kpi_rt("Vencen en 90 días", "calendar-times-o", VENCE, 1, "vs. agosto", reverse=True),
            kpi_rt("Importe comprometido", "eur", "fv!row.estado = \"Vigente\"", 215000, "vs. agosto", fmt="eur", measure={"type": "a!measure", "function": "SUM", "field": F("importe")}),
        ]),
        {"type": "a!columnsLayout", "columns": [
            {"type": "a!columnLayout", "width": "2X", "contents": [section_card("Mis tareas", [
                grid("data!tareas", None, [
                    gcol_link("Tarea", "{fv!row.tarea} {fv!row.codigo}", {"goto": "revision", "params": {"id": "{fv!row.acuerdoId}"}}, "{fv!row.titulo}"),
                    gcol("Recibida", "{fv!row.recibida|date}", width="NARROW"),
                    gcol("Plazo", {"type": "a!tagField", "labelPosition": "COLLAPSED", "size": "SMALL", "tags": [{"type": "a!tagItem", "text": "{fv!row.plazo}", "backgroundColor": "{fv!row.urgente|map:plazoColor}"}]}, width="NARROW_PLUS"),
                ], "No tiene tareas pendientes", page_size=10, **{"$note": "En Appian: a!gridField sobre el record type de tareas o a!queryProcessAnalytics. Lista de 5–10 tareas sin paginación."}),
            ], card={"padding": "NONE"})]},
            {"type": "a!columnLayout", "contents": [
                action_banner(f"{n_vencen} acuerdos vencen en los próximos 90 días", "Revise si deben renovarse antes de su vencimiento",
                              secondary("Revisar", {"goto": "acuerdos"}, size="SMALL"), kind="WARN", icon="clock-o", marginBelow="MORE"),
                section_card("Acuerdos por estado", [{"type": "a!barChartField", "labelPosition": "COLLAPSED", "data": f"recordType!{RT}", "height": "AUTO", "showDataLabels": True,
                    "$categories": ["Borrador", "En revisión jurídica", "Pendiente de firma", "Vigente", "Vencido", "Rechazado"],
                    "config": {"type": "a!barChartConfig", "primaryGrouping": {"type": "a!grouping", "field": F("estado")}, "secondaryGrouping": {"type": "a!grouping", "field": F("estado")},
                               "measures": [{"type": "a!measure", "function": "COUNT", "field": F("id"), "label": "Acuerdos"}]},
                    "stacking": "NORMAL", "showLegend": False, "colorScheme": state_chart_colors(ATP_ESTADOS, ATP_FASES)}]),
            ]},
        ]},
    ]},
}

# ------------------------------------------------------------------ P01 Listado
listado = {
    "id": "acuerdos", "title": "Acuerdos", "type": "page", "pattern": "P01", "ref": "PAN-02 · Listado de acuerdos", "req": ["RF-03", "RF-04", "RF-11"],
    "interface": {"type": "a!headerContentLayout", "backgroundColor": BG, "contents": [
        page_header("Acuerdos", "Acuerdos con terceras partes de todos los aeropuertos y Servicios Centrales", [primary("Nuevo acuerdo", {"goto": "alta"}, "plus")]),
        {"type": "a!messageBanner", "backgroundColor": "SUCCESS", "highlightColor": "POSITIVE", "shape": "SEMI_ROUNDED", "showWhen": "a!isNotNullOrEmpty(ri!mensaje)", "primaryText": "{ri!mensaje}", "secondaryText": "Asesoría Jurídica ha recibido la tarea de revisión.", "marginBelow": "STANDARD"},
        content_card([grid(f"recordType!{RT}", None, [
            gcol("Acuerdo", two_line("{fv!row.codigo}", "{fv!row.titulo}", {"type": "a!recordLink", "recordType": f"recordType!{RT}", "identifier": "{fv!row.id}"}), sortField=F("codigo"), width="4X"),
            gcol("Tercero", two_line("{fv!row.tercero}", "{fv!row.tipoTercero}", strong=False), sortField=F("tercero"), width="3X"),
            gcol("Tipo", "{fv!row.tipo}", sortField=F("tipo"), width="2X"),
            gcol("Aeropuerto", "{fv!row.aeropuerto}", sortField=F("aeropuerto"), width="NARROW"),
            gcol("Fin", "{fv!row.fechaFin|date}", sortField=F("fechaFin"), width="NARROW"),
            gcol("Estado", tag("fv!row.estado", "estadoColorGrid"), sortField=F("estado"), width="NARROW_PLUS"),
            gcol("Aviso", alert_icons([(VENCE, "clock-o", "Vence en {fv!row.diasParaVencer} días", "WARN")]), width="ICON", align="CENTER"),
        ], "No hay acuerdos que cumplan los filtros", page_size=25, showSearchBox=True, showExportButton=True,
            userFilters=[f"recordType!{RT}.filters.estado", f"recordType!{RT}.filters.tipo", f"recordType!{RT}.filters.aeropuerto"],
            initialSorts=[{"type": "a!sortInfo", "field": F("fechaAlta"), "ascending": False}])]),
    ]},
}

# ------------------------------------------------------------------ P02 Vista de registro
def summary_view():
    return {"type": "a!headerContentLayout", "backgroundColor": BG, "contents": [
        key_facts([
            ("Estado", tag("rv!record.estado", size="STANDARD")),
            ("Vigencia", "{rv!record.fechaInicio|date} – {rv!record.fechaFin|date}"),
            ("Tercero", "{rv!record.tercero}"),
            ("Importe", "{rv!record.importe|eur}"),
            ("Responsable", "{rv!record.responsable}"),
        ], extra=[milestone(["Borrador", "En revisión jurídica", "Pendiente de firma", "Vigente", "Vencido"], "{rv!record.estado|map:estadoPaso}")]),
        action_banner("Este acuerdo vence en {rv!record.diasParaVencer} días", "Valore la renovación antes del {rv!record.fechaFin|date}", kind="WARN", icon="clock-o",
                      showWhen="and(rv!record.estado = \"Vigente\", rv!record.diasParaVencer <= 90)", marginBelow="MORE"),
        {"type": "a!columnsLayout", "columns": [
            {"type": "a!columnLayout", "width": "2X", "contents": [section_card("Datos del acuerdo", [
                subsection("Datos generales", field_summary([
                    ("Código", "{rv!record.codigo}"), ("Tipo de acuerdo", "{rv!record.tipo}"), ("Aeropuerto / unidad", "{rv!record.aeropuerto}"),
                    ("Título", "{rv!record.titulo}", True),
                    ("Fecha de inicio", "{rv!record.fechaInicio|date}"), ("Fecha de fin", "{rv!record.fechaFin|date}"), ("Prórroga automática", "{rv!record.prorroga|map:siNo}")])),
                subsection("Tercero", field_summary([("Razón social", "{rv!record.tercero}"), ("CIF/NIF", "{rv!record.cif}"), ("Tipo de tercero", "{rv!record.tipoTercero}")])),
                subsection("Condiciones económicas", field_summary([("Contenido económico", "{rv!record.conImporte|map:siNo}"), ("Importe", "{rv!record.importe|eur}"), ("Contraprestación", "{rv!record.contraprestacion}")]), marginBelow="NONE"),
            ])]},
            {"type": "a!columnLayout", "contents": [
                section_card("Responsable", [{"type": "a!sideBySideLayout", "alignVertical": "MIDDLE", "items": [
                    {"type": "a!sideBySideItem", "width": "MINIMIZE", "item": {"type": "a!imageField", "labelPosition": "COLLAPSED", "size": "TINY", "style": "AVATAR", "images": [{"type": "a!userImage", "user": "{rv!record.responsable}"}]}},
                    {"type": "a!sideBySideItem", "item": two_line("{rv!record.responsable}", "Unidad promotora · {rv!record.aeropuerto}")}]}]),
                section_card("Documentos recientes", [
                    {"type": "a!forEach", "items": "data!documentos", "$filter": "fv!item.acuerdoId = rv!record.id", "$limit": 3,
                     "expression": doc_line("{fv!item.nombre}", "{fv!item.tipo} · {fv!item.fecha|date}", {"goto": "acuerdo", "params": {"id": "{rv!record.id}"}, "view": "documentos"}, icon="{fv!item.icono}")},
                    link_all("Ver todos los documentos", {"goto": "acuerdo", "params": {"id": "{rv!record.id}"}, "view": "documentos"})]),
            ]},
        ]},
    ]}

registro = {
    "id": "acuerdo", "title": "{rv!record.codigo} · {rv!record.titulo}", "type": "record", "pattern": "P02", "ref": "PAN-03 · Ficha del acuerdo", "recordType": RT,
    "req": ["RF-04", "RF-08", "RF-09", "RF-11"],
    "breadcrumb": {"label": "Acuerdos", "goto": "acuerdos"},
    "headerBackgroundColor": NAVY,
    "recordActions": [
        {"type": "a!recordActionItem", "action": f"recordType!{RT}.actions.editarDatosGenerales", "identifier": "{rv!record.id}", "$label": "Editar datos", "$icon": "pencil", "$action": {"dialog": "editar", "params": {"id": "{rv!record.id}"}}},
        {"type": "a!recordActionItem", "action": f"recordType!{RT}.actions.anadirDocumento", "identifier": "{rv!record.id}", "$label": "Añadir documento", "$icon": "paperclip", "$action": {"dialog": "documento", "params": {"id": "{rv!record.id}"}}},
    ],
    "views": [
        {"id": "resumen", "label": "Resumen", "interface": summary_view()},
        {"id": "documentos", "label": "Documentos", "interface": {"type": "a!headerContentLayout", "backgroundColor": BG, "contents": [content_card([
            grid("data!documentos", "fv!row.acuerdoId = rv!record.id", [
                gcol("Documento", {"type": "a!richTextDisplayField", "labelPosition": "COLLAPSED", "value": [{"type": "a!richTextIcon", "icon": "{fv!row.icono}", "color": "SECONDARY", "size": "MEDIUM"}, "  ", {"type": "a!richTextItem", "text": "{fv!row.nombre}", "link": {"type": "a!dynamicLink"}, "linkStyle": "STANDALONE", "style": "STRONG"}, "\n", {"type": "a!richTextItem", "text": "{fv!row.tipo}", "color": "SECONDARY", "size": "SMALL"}]}, width="5X"),
                gcol("Subido por", "{fv!row.subidoPor}", width="3X"),
                gcol("Fecha", "{fv!row.fecha|date}", width="NARROW"),
                gcol_num("Tamaño", "{fv!row.tamano}", width="NARROW"),
            ], "El acuerdo no tiene documentos", **{"$note": "En Appian: record type de documentos relacionado con ATP Acuerdo (relación uno a muchos)."})], padding="NONE")]}},
        {"id": "historial", "label": "Historial", "interface": {"type": "a!headerContentLayout", "backgroundColor": BG, "contents": [content_card([
            {"type": "a!eventHistoryListField", "labelPosition": "COLLAPSED", "eventStyle": "TIMELINE", "commentLayout": "CARD", "$events": "data!eventos", "$filter": "fv!row.acuerdoId = rv!record.id",
             "$note": "En Appian: a!eventHistoryListField con a!eventData sobre el record type de eventos de ATP Acuerdo (record events)."}], padding="MORE")]}},
    ],
}

# ------------------------------------------------------------------ P04 Asistente
paso1 = [
    txt("Título", "local!acuerdo.titulo", required=True, characterLimit=200, showCharacterCount=True),
    choice_cards("Tipo de acuerdo", [{"id": t, "texto": t, "icono": i} for t, i in zip(TIPOS, TIPOS_ICON)], "local!acuerdo.tipo", required=True),
    cols(dd("Aeropuerto / unidad", AEROPUERTOS_L, "local!acuerdo.aeropuerto", AEROPUERTOS, required=True),
         {"type": "a!pickerFieldUsers", "label": "Responsable AENA", "maxSelections": 1, "value": "local!acuerdo.responsable", "saveInto": "local!acuerdo.responsable", "required": True}),
    cols(date("Fecha de inicio", "local!acuerdo.fechaInicio", required=True),
         date("Fecha de fin", "local!acuerdo.fechaFin", required=True, **{"$validations": [{"when": "and(a!isNotNullOrEmpty(local!acuerdo.fechaFin), a!isNotNullOrEmpty(local!acuerdo.fechaInicio), local!acuerdo.fechaFin <= local!acuerdo.fechaInicio)", "message": "La fecha de fin debe ser posterior a la fecha de inicio (RN-01)"}]})),
    {"type": "a!booleanCheckboxField", "choiceLabel": "Prórroga automática al vencimiento", "value": "local!acuerdo.prorroga", "saveInto": "local!acuerdo.prorroga"},
]
paso2 = [
    txt("Razón social del tercero", "local!acuerdo.tercero", required=True),
    cols(txt("CIF/NIF", "local!acuerdo.cif", required=True, **{"$assumption": "La ERS no indica si el CIF se valida contra un servicio externo (AEAT). Se asume validación solo de formato."}), []),
    {"type": "a!radioButtonField", "label": "Tipo de tercero", "choiceLabels": TIPOS_TERCERO, "choiceValues": TIPOS_TERCERO, "value": "local!acuerdo.tipoTercero", "saveInto": "local!acuerdo.tipoTercero", "required": True, "choiceLayout": "STACKED"},
]
paso3 = [
    {"type": "a!radioButtonField", "label": "¿El acuerdo tiene contenido económico?", "choiceLabels": ["Sí", "No"], "choiceValues": [True, False], "value": "local!acuerdo.conImporte", "saveInto": "local!acuerdo.conImporte", "required": True, "choiceLayout": "COMPACT"},
    cols({"type": "a!floatingPointField", "label": "Importe (€)", "value": "local!acuerdo.importe", "saveInto": "local!acuerdo.importe", "required": True, "instructions": "Importe total sin IVA para toda la vigencia"}, [], showWhen="local!acuerdo.conImporte"),
    par("Contraprestación", "local!acuerdo.contraprestacion", showWhen="local!acuerdo.conImporte", height="SHORT"),
]
paso4 = [
    upload("Texto del acuerdo", "local!acuerdo.docs", required=True, maxSelections=5, instructions="PDF o DOCX, máximo 10 MB por fichero",
           **{"$note": "En Appian: target = constante de carpeta de documentos ATP; validar extensión con fv!files."}),
    par("Observaciones para Asesoría Jurídica", "local!acuerdo.observaciones", height="SHORT"),
]
def revisa(label, step, pairs):
    return subsection_with_link(label, "Editar", {"step": step}, field_summary(pairs, columns=2))
paso5 = [
    {"type": "a!messageBanner", "backgroundColor": "INFO", "highlightColor": "INFO", "shape": "SEMI_ROUNDED", "primaryText": "Revise los datos antes de enviar", "secondaryText": "Al enviar, el acuerdo pasará a «En revisión jurídica» y no podrá editarse hasta que Asesoría Jurídica lo resuelva.", "marginBelow": "MORE"},
    revisa("Datos generales", 1, [("Título", "{local!acuerdo.titulo}", True), ("Tipo de acuerdo", "{local!acuerdo.tipo}"), ("Aeropuerto / unidad", "{local!acuerdo.aeropuerto}"), ("Responsable AENA", "{local!acuerdo.responsable|map:usuarios}"), ("Vigencia", "{local!acuerdo.fechaInicio|date} – {local!acuerdo.fechaFin|date}"), ("Prórroga automática", "{local!acuerdo.prorroga|map:siNo}")]),
    revisa("Tercero", 2, [("Razón social", "{local!acuerdo.tercero}"), ("CIF/NIF", "{local!acuerdo.cif}"), ("Tipo de tercero", "{local!acuerdo.tipoTercero}")]),
    revisa("Condiciones económicas", 3, [("Contenido económico", "{local!acuerdo.conImporte|map:siNo}"), ("Importe", "{local!acuerdo.importe|eur}"), ("Contraprestación", "{local!acuerdo.contraprestacion}", True)]),
    revisa("Documentación", 4, [("Texto del acuerdo", "{local!acuerdo.docs.name}", True), ("Observaciones para Asesoría Jurídica", "{local!acuerdo.observaciones}", True)]),
]
alta = {
    "id": "alta", "title": "Nuevo acuerdo", "type": "form", "pattern": "P04", "ref": "PAN-04 · Alta de acuerdo", "req": ["RF-05", "RF-06", "RF-07"],
    "local": {"local!acuerdo": {"titulo": None, "tipo": None, "aeropuerto": None, "responsable": None, "fechaInicio": None, "fechaFin": None, "prorroga": False, "tercero": None, "cif": None, "tipoTercero": None, "conImporte": None, "importe": None, "contraprestacion": None, "docs": [], "observaciones": None}},
    "assumptions": ["El código ATP-AAAA-NNNN lo genera el proceso al enviar; no se muestra en el alta."],
    "interface": {"type": "a!wizardLayout", "style": "DOT_VERTICAL", "contentsWidth": "MEDIUM", "showButtonDivider": True, "backgroundColor": "WHITE",
        "titleBar": {"type": "a!sidebarTemplate", "title": "Nuevo acuerdo", "secondaryText": "Alta de un acuerdo con una tercera parte", "backgroundColor": NAVY, "width": "NARROW_PLUS",
                     "additionalContents": [{"type": "a!richTextDisplayField", "labelPosition": "COLLAPSED", "value": [{"type": "a!richTextIcon", "icon": "info-circle", "color": GREEN}, " ", {"type": "a!richTextItem", "text": "Al enviar, Asesoría Jurídica recibe una tarea de revisión.", "size": "SMALL", "color": "#FFFFFF"}]}]},
        "steps": [
            {"type": "a!wizardStep", "label": "Datos generales", "contents": paso1},
            {"type": "a!wizardStep", "label": "Tercero", "contents": paso2},
            {"type": "a!wizardStep", "label": "Condiciones económicas", "contents": paso3},
            {"type": "a!wizardStep", "label": "Documentación", "contents": paso4},
            {"type": "a!wizardStep", "label": "Revisión", "contents": paso5},
        ],
        "secondaryButtons": [secondary("Cancelar", {"goto": "acuerdos"}, confirmHeader="¿Descartar el alta?", confirmMessage="Se perderán los datos introducidos.", confirmButtonLabel="Descartar", cancelButtonLabel="Seguir editando")],
        "primaryButtons": [primary("Enviar a revisión", {"goto": "acuerdos", "params": {"mensaje": "Acuerdo ATP-2026-0017 enviado a revisión jurídica"}}, submit=True)],
    },
}

# ------------------------------------------------------------------ P05 Tarea de aprobación
revision = {
    "id": "revision", "title": "Revisar acuerdo", "type": "form", "pattern": "P05", "ref": "PAN-05 · Revisión jurídica", "req": ["RF-10"], "recordType": RT,
    "local": {"local!decision": None, "local!comentarios": None},
    "interface": {"type": "a!formLayout", "contentsWidth": "WIDE", "backgroundColor": "WHITE", "showButtonDivider": True, "isButtonFooterFixed": True,
        "titleBar": {"type": "a!headerTemplateSimple", "title": "Revisar acuerdo {rv!record.codigo}", "secondaryText": "Tarea de Asesoría Jurídica · recibida el 02/09/2026", "stampIcon": "gavel", "stampColor": "ACCENT"},
        "contents": [
            action_banner("Vence el 26/09/2026, en 2 días", "Si no se resuelve a tiempo, la tarea se escala a la jefatura de Asesoría Jurídica", kind="WARN", icon="clock-o", marginBelow="MORE",
                          **{"$assumption": "El escalado por plazo no está en la ERS; se muestra solo el vencimiento de la tarea."}),
            {"type": "a!columnsLayout", "spacing": "SPARSE", "columns": [
                {"type": "a!columnLayout", "width": "3X", "contents": [
                    {"type": "a!sectionLayout", "label": "Datos del acuerdo", "labelSize": "MEDIUM", "labelHeadingTag": "H2", "labelColor": "STANDARD", "contents": field_summary([("Título", "{rv!record.titulo}", True), ("Tipo de acuerdo", "{rv!record.tipo}"), ("Tercero", "{rv!record.tercero} ({rv!record.cif})"),
                                                                   ("Vigencia", "{rv!record.fechaInicio|date} – {rv!record.fechaFin|date}"), ("Importe", "{rv!record.importe|eur}"), ("Responsable AENA", "{rv!record.responsable}")], columns=3)},
                    {"type": "a!sectionLayout", "label": "Texto del acuerdo", "labelSize": "MEDIUM", "labelHeadingTag": "H2", "labelColor": "STANDARD", "marginBelow": "NONE", "contents": [{"type": "a!documentViewerField", "labelPosition": "COLLAPSED", "$fileName": "{rv!record.codigo}_texto_acuerdo.pdf", "height": "SHORT"}]},
                ]},
                {"type": "a!columnLayout", "width": "2X", "contents": [{"type": "a!cardLayout", "showBorder": True, "shape": "SEMI_ROUNDED", "padding": "MORE", "borderColor": "STANDARD", "contents": [
                    {"type": "a!sectionLayout", "label": "Decisión", "labelSize": "MEDIUM", "labelHeadingTag": "H2", "labelColor": "STANDARD", "contents": [
                        choice_cards("Resultado de la revisión", [
                            {"id": "APROBAR", "texto": "Aprobar", "detalle": "El acuerdo pasa a «Pendiente de firma»", "icono": "check-circle", "color": "POSITIVE"},
                            {"id": "DEVOLVER", "texto": "Devolver para cambios", "detalle": "El gestor recibe los comentarios", "icono": "undo", "color": "#FF9F2F"},
                            {"id": "RECHAZAR", "texto": "Rechazar", "detalle": "El acuerdo queda «Rechazado»", "icono": "times-circle", "color": "NEGATIVE"}],
                            "local!decision", labelPosition="COLLAPSED", required=True, requiredMessage="Indique el resultado de la revisión"),
                        par("Comentarios", "local!comentarios", required="and(a!isNotNullOrEmpty(local!decision), local!decision <> \"APROBAR\")", instructions="Obligatorios si no se aprueba", **{"$note": "RF-10: comentario obligatorio al devolver o rechazar."}),
                    ]}]}]},
            ]},
        ],
        "buttons": bl(primary("Enviar decisión", {"goto": "inicio"}, submit=True), [secondary("Cancelar", {"back": True})]),
    },
}

# ------------------------------------------------------------------ P07 Diálogos
editar = dialog("editar", "Editar datos generales", [
        txt("Título", "local!titulo", required=True, characterLimit=200, showCharacterCount=True),
        cols(date("Fecha de inicio", "local!ini", required=True), date("Fecha de fin", "local!fin", required=True)),
        {"type": "a!pickerFieldUsers", "label": "Responsable AENA", "maxSelections": 1, "value": "local!resp", "saveInto": "local!resp", "required": True},
        {"type": "a!booleanCheckboxField", "choiceLabel": "Prórroga automática al vencimiento", "value": "local!prorroga", "saveInto": "local!prorroga"},
    ], bl(primary("Guardar", {"close": True}, submit=True)), ["RF-09"], "PAN-06 · Editar datos generales", openFrom="acuerdo", recordType=RT,
    local={"local!titulo": "{rv!record.titulo}", "local!ini": "{rv!record.fechaInicio}", "local!fin": "{rv!record.fechaFin}", "local!resp": "{rv!record.responsableId}", "local!prorroga": "{rv!record.prorroga}"})
DOC_TIPOS = ["Texto del acuerdo", "Memoria justificativa", "Informe jurídico", "Acuerdo firmado", "Otro"]
documento = dialog("documento", "Añadir documento", [
        dd("Tipo de documento", DOC_TIPOS, "local!tipoDoc", required=True),
        upload("Fichero", "local!ficheros", required=True, maxSelections=1, instructions="PDF o DOCX, máximo 10 MB", **{"$note": "RN-02: formatos y tamaño máximo."}),
    ], bl(primary("Añadir", {"close": True}, submit=True)), ["RF-09"], "PAN-07 · Añadir documento", openFrom="acuerdo", recordType=RT,
    local={"local!tipoDoc": None, "local!ficheros": []})

# ------------------------------------------------------------------ P08 Informe
FT = "or(isnull(local!tipo), fv!row.tipo = local!tipo)"
altas_mes = {}
for a in acuerdos:
    if a["fechaAlta"] >= "2025-10": altas_mes[a["mesAlta"]] = altas_mes.get(a["mesAlta"], 0) + 1
media = round(sum(altas_mes.values()) / len(altas_mes), 1)  # media de los meses del gráfico
informe = {
    "id": "informes", "title": "Informes", "type": "page", "pattern": "P08", "ref": "PAN-08 · Informe de acuerdos", "req": ["RF-12"],
    "local": {"local!tipo": None},
    "interface": {"type": "a!headerContentLayout", "backgroundColor": BG, "contents": [
        page_header("Informes", "Evolución y distribución de los acuerdos con terceras partes"),
        content_card([{"type": "a!columnsLayout", "alignVertical": "BOTTOM", "columns": [
            {"type": "a!columnLayout", "width": "MEDIUM", "contents": [dd("Tipo de acuerdo", TIPOS, "local!tipo", placeholder="Todos los tipos", marginBelow="NONE")]},
            {"type": "a!columnLayout", "contents": [{"type": "a!buttonArrayLayout", "marginBelow": "NONE", "buttons": [{"type": "a!buttonWidget", "label": "Quitar filtro", "style": "LINK", "showWhen": "a!isNotNullOrEmpty(local!tipo)", "saveInto": [{"type": "a!save", "target": "local!tipo", "value": None}]}]}]},
        ]}], marginBelow="MORE"),
        kpi_strip([
            kpi("Acuerdos", "handshake-o", sec_text="en el filtro", data=f"recordType!{RT}", primaryMeasure={"type": "a!measure", "function": "COUNT", "field": F("id")}, **{"$filter": FT}),
            kpi("Vigentes", "check-circle", sec_text="en el filtro", data=f"recordType!{RT}", primaryMeasure={"type": "a!measure", "function": "COUNT", "field": F("id")}, **{"$filter": "and(" + FT + ", fv!row.estado = \"Vigente\")"}),
            kpi("Importe total", "eur", sec_text="acuerdos con contenido económico", data=f"recordType!{RT}", primaryMeasure={"type": "a!measure", "function": "SUM", "field": F("importe")}, **{"$filter": FT, "$format": "eur"}),
        ]),
        {"type": "a!columnsLayout", "columns": [
            {"type": "a!columnLayout", "contents": [section_card("Acuerdos por tipo", [{"type": "a!pieChartField", "labelPosition": "COLLAPSED", "data": f"recordType!{RT}", "$filter": FT, "style": "DONUT", "height": "SHORT", "showTooltips": True, "showDataLabels": True,
                "config": {"type": "a!pieChartConfig", "primaryGrouping": {"type": "a!grouping", "field": F("tipo")}, "measures": [{"type": "a!measure", "function": "COUNT", "field": F("id"), "label": "Acuerdos"}]},
                "colorScheme": {"type": "a!colorSchemeCustom", "colors": CHART[:4]}}])]},
            {"type": "a!columnLayout", "contents": [section_card("Acuerdos por estado", [{"type": "a!columnChartField", "labelPosition": "COLLAPSED", "data": f"recordType!{RT}", "$filter": FT, "height": "SHORT", "showDataLabels": True,
                "$categories": ["Borrador", "En revisión jurídica", "Pendiente de firma", "Vigente", "Vencido", "Rechazado"],
                "config": {"type": "a!columnChartConfig", "primaryGrouping": {"type": "a!grouping", "field": F("estado")}, "secondaryGrouping": {"type": "a!grouping", "field": F("estado")},
                           "measures": [{"type": "a!measure", "function": "COUNT", "field": F("id"), "label": "Acuerdos"}]},
                "stacking": "NORMAL", "showLegend": False, "colorScheme": state_chart_colors(ATP_ESTADOS, ATP_FASES)}])]},
        ]},
        {"type": "a!columnsLayout", "columns": [
            {"type": "a!columnLayout", "contents": [section_card("Altas por mes", [{"type": "a!lineChartField", "labelPosition": "COLLAPSED", "data": f"recordType!{RT}", "$filter": "and(" + FT + ", fv!row.fechaAlta >= \"2025-10\")", "height": "SHORT",
                "config": {"type": "a!lineChartConfig", "primaryGrouping": {"type": "a!grouping", "field": F("mesAlta"), "interval": "MONTH_SHORT_TEXT"}, "measures": [{"type": "a!measure", "function": "COUNT", "field": F("id"), "label": "Altas"}]},
                "referenceLines": [{"type": "a!chartReferenceLine", "label": f"Media: {str(media).replace('.', ',')}", "value": media, "color": "BLUEGRAY", "style": "DASH"}],
                "colorScheme": {"type": "a!colorSchemeCustom", "colors": ["#527500"]}}])]},
            {"type": "a!columnLayout", "contents": [section_card("Importe por aeropuerto", [{"type": "a!barChartField", "labelPosition": "COLLAPSED", "data": f"recordType!{RT}", "$filter": "and(" + FT + ", fv!row.conImporte)", "height": "AUTO", "showDataLabels": True, "xAxisTitle": "Importe (€)",
                "config": {"type": "a!barChartConfig", "primaryGrouping": {"type": "a!grouping", "field": F("aeropuerto")}, "measures": [{"type": "a!measure", "function": "SUM", "field": F("importe"), "label": "Importe"}]},
                "colorScheme": {"type": "a!colorSchemeCustom", "colors": ["#527500"]}}])]},
        ]},
    ]},
}

spec = {
    "app": {"name": "Acuerdos con Terceras Partes", "shortName": "ATP", "version": "0.1", "language": "es", "today": "2026-09-24", "appianVersion": "26.9",
            "source": "examples/atp/ddf.md v1.1 (modo fiel de la ERS de ejemplo, FU-01) · datos ficticios"},
    "site": {"displayName": "Acuerdos con Terceras Partes", "home": "inicio", "user": {"name": "Lucía Fernández Gil"},
             "pages": [
                 {"title": "Inicio", "icon": "home", "screen": "inicio", "includes": ["revision"]},
                 {"title": "Acuerdos", "icon": "handshake-o", "screen": "acuerdos", "includes": ["acuerdo", "alta"]},
                 {"title": "Informes", "icon": "bar-chart", "screen": "informes"}]},
    "requirements": [
        {"id": "RF-01", "title": "Indicadores en la página de inicio"}, {"id": "RF-02", "title": "Tareas pendientes del usuario"},
        {"id": "RF-03", "title": "Listado con búsqueda, filtros y exportación"}, {"id": "RF-04", "title": "Acceso a la ficha desde el listado"},
        {"id": "RF-05", "title": "Alta en varios pasos con resumen"}, {"id": "RF-06", "title": "Importe solo con contenido económico"},
        {"id": "RF-07", "title": "Envío a revisión jurídica"}, {"id": "RF-08", "title": "Ficha: ciclo de vida, datos, documentos e historial"},
        {"id": "RF-09", "title": "Editar datos y añadir documentos"}, {"id": "RF-10", "title": "Resolver la revisión jurídica"},
        {"id": "RF-11", "title": "Aviso de vencimiento a 90 días"}, {"id": "RF-12", "title": "Informe de acuerdos"}],
    "openQuestions": [
        {"id": "P-006", "text": "¿Quién puede editar un acuerdo en estado «Vigente»? La ERS solo habla del gestor en el alta.", "screen": "editar", "priority": "IMPORTANTE"},
        {"id": "P-001", "text": "¿Quién pasa el acuerdo a «Pendiente de firma», «Vigente» y «Vencido»? ¿La firma se registra en la aplicación (fecha, firmantes) o solo se adjunta el PDF firmado?", "screen": "acuerdo", "priority": "CRITICA"},
        {"id": "P-007", "text": "¿«Devolver para cambios» genera una tarea al gestor o el acuerdo vuelve a Borrador sin tarea?", "screen": "revision", "priority": "CRITICA"}],
    "maps": {
        "estadoColor": state_map({"Borrador": "neutral", "En revisión jurídica": "enCurso", "Pendiente de firma": "atencion", "Vigente": "positivo", "Vencido": "negativo", "Rechazado": "negativo"}),
        "estadoColorGrid": state_map({"Borrador": "neutral", "En revisión jurídica": "enCurso", "Pendiente de firma": "atencion", "Vigente": "positivo", "Vencido": "negativo", "Rechazado": "negativo"}, grid=True),
        "plazoColor": {"true": STATES["atencion"]["tag"], "*": STATES["neutral"]["tag"]},
        "estadoPaso": {"Borrador": 1, "En revisión jurídica": 2, "Pendiente de firma": 3, "Vigente": 4, "Vencido": 5, "Rechazado": 2},
        "siNo": {"true": "Sí", "false": "No", "*": "No"},
        "usuarios": {u["id"]: u["name"] for u in users}},
    "users": users,
    "data": {
        "acuerdos": {"recordType": RT, "rows": acuerdos},
        "tareas": {"recordType": "ATP Tarea", "rows": tareas},
        "documentos": {"recordType": "ATP Documento", "rows": documentos},
        "eventos": {"recordType": "ATP Evento", "rows": eventos}},
    "screens": [inicio, listado, registro, alta, revision, editar, documento, informe],
    "captures": [
        {"name": "01-inicio", "screen": "inicio"},
        {"name": "02-listado-acuerdos", "screen": "acuerdos"},
        {"name": "03-ficha-resumen", "screen": "acuerdo", "params": {"id": 3}},
        {"name": "04-ficha-documentos", "screen": "acuerdo", "params": {"id": 3}, "view": "documentos"},
        {"name": "05-ficha-historial", "screen": "acuerdo", "params": {"id": 4}, "view": "historial"},
        {"name": "06-alta-paso1-errores", "screen": "alta", "step": 0, "showValidation": True},
        {"name": "06b-alta-revision", "screen": "alta", "step": 4, "state": {"local!acuerdo": {"titulo": "Contrato de colaboración para movilidad eléctrica en aparcamientos", "tipo": "Contrato de colaboración", "aeropuerto": "VLC", "fechaInicio": "2026-12-01", "fechaFin": "2030-11-30", "prorroga": True, "tercero": "Zunder Charging S.L.", "cif": "B42812727", "tipoTercero": "Empresa privada", "conImporte": True, "importe": 96000, "contraprestacion": "Cesión de espacios para puntos de recarga", "responsable": ["rsanchez"], "docs": [{"name": "Borrador contrato movilidad eléctrica.pdf", "size": "412 KB"}], "observaciones": "Revisar la cláusula de responsabilidad por daños en las instalaciones."}}},
        {"name": "07-alta-paso3-con-importe", "screen": "alta", "step": 2, "state": {"local!acuerdo": {"conImporte": True, "importe": 96000, "contraprestacion": "Cesión de espacios para puntos de recarga"}}},
        {"name": "08-revision-juridica", "screen": "revision", "params": {"id": 6}, "state": {"local!decision": "DEVOLVER"}},
        {"name": "09-dialogo-editar", "screen": "editar", "hostParams": {"id": 3}, "params": {"id": 3}},
        {"name": "10-dialogo-documento", "screen": "documento", "hostParams": {"id": 3}, "params": {"id": 3}},
        {"name": "11-informes", "screen": "informes"}],
}
import sys
json.dump(spec, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("ok", len(acuerdos))
