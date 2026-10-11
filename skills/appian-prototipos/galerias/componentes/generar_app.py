"""Genera galerias/componentes/app.json: catálogo navegable de TODOS los componentes de interfaz de Appian 26.9
(las 147 funciones de https://docs.appian.com/suite/help/26.9/SAIL_Components.html), agrupados por las categorías de Appian.

Cada demostración lleva el nombre de la función, cuándo usarla según el SAIL Design System y un ejemplo con datos
ficticios. La prueba del plugin comprueba que el catálogo cubre todas las funciones de schemas/catalogo-appian.json.
Uso: python3 generar_app.py app.json"""
import json, sys
from pathlib import Path
sys.dont_write_bytecode = True  # sin __pycache__ en el plugin: no se escribe fuera del proyecto
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from sail_helpers import *  # noqa: E402,F401

# ------------------------------------------------------------------ datos de ejemplo (ficticios)
USERS = [
    ("cruiz", "Carmen Ruiz Herrera", "Directora de Operaciones", None, ["g-dir"]),
    ("mlopez", "María López Arranz", "Jefa de la sede Norte", "cruiz", ["g-norte"]),
    ("jgarcia", "Javier García Ruiz", "Jefe de la sede Sur", "cruiz", ["g-sur"]),
    ("amoreno", "Andrés Moreno Pastor", "Jefe de Mantenimiento", "cruiz", ["g-mant"]),
    ("rsanchez", "Rocío Sánchez Vidal", "Supervisora del edificio A", "mlopez", ["g-edifa"]),
    ("pmartin", "Pablo Martín Ortega", "Coordinador de servicios generales", "mlopez", ["g-servicios"]),
    ("lfernandez", "Lucía Fernández Gil", "Técnica de operaciones", "rsanchez", ["g-edifa"]),
    ("dnavarro", "Diego Navarro Sáez", "Técnico de operaciones", "rsanchez", ["g-edifa"]),
    ("ivega", "Irene Vega Molina", "Técnica de climatización", "amoreno", ["g-clima"]),
    ("sortiz", "Sergio Ortiz Lara", "Técnico de elevación", "amoreno", ["g-elev"]),
    ("ecastro", "Elena Castro Ibáñez", "Supervisora de turno de la sede Sur", "jgarcia", ["g-sur"]),
    ("hromero", "Hugo Romero Díaz", "Técnico de sistemas", "jgarcia", ["g-sis"]),
]
GROUPS = [
    ("g-dir", "Dirección de Operaciones", None, "Dirección y jefaturas de las sedes"),
    ("g-norte", "Sede Norte", "g-dir", "Oficinas centrales y almacén"),
    ("g-edifa", "Edificio A", "g-norte", "Supervisión y técnicos del edificio A"),
    ("g-servicios", "Servicios generales", "g-norte", "Recepción, correo interno y aparcamientos"),
    ("g-sur", "Sede Sur", "g-dir", "Oficinas y centro de formación"),
    ("g-mant", "Mantenimiento", None, "Mantenimiento de edificios e instalaciones"),
    ("g-clima", "Climatización", "g-mant", "Enfriadoras, climatizadoras y ventilación"),
    ("g-elev", "Elevación", "g-mant", "Ascensores, montacargas y puertas automáticas"),
    ("g-sis", "Sistemas", None, "Sistemas de información y comunicaciones"),
]
DOCS = [
    ("f-norm", "Normativa", None, "folder", None, None),
    ("f-seg", "Seguridad y salud", "f-norm", "folder", None, None),
    ("d-prev", "Manual_de_prevencion_v4.pdf", "f-seg", "document", "2,4 MB", "2026-07-14"),
    ("d-evac", "Procedimiento_de_evacuacion.docx", "f-seg", "document", "310 KB", "2026-05-02"),
    ("f-alm", "Almacén", "f-norm", "folder", None, None),
    ("d-alm", "Normas_del_almacen_2026.pdf", "f-alm", "document", "1,1 MB", "2026-01-20"),
    ("f-contr", "Contratos", None, "folder", None, None),
    ("f-cmant", "Mantenimiento", "f-contr", "folder", None, None),
    ("d-clima", "Contrato_climatizacion_sede_Norte.pdf", "f-cmant", "document", "860 KB", "2026-03-09"),
    ("d-precios", "Anexo_precios_2026.xlsx", "f-cmant", "document", "48 KB", "2026-03-09"),
    ("f-planos", "Planos", None, "folder", None, None),
    ("d-ea1", "Plano_edificio_A_planta_1.pdf", "f-planos", "document", "5,2 MB", "2025-11-30"),
    ("d-ea2", "Plano_edificio_A_planta_2.pdf", "f-planos", "document", "4,8 MB", "2025-11-30"),
    ("d-org", "Organigrama_operaciones.pdf", None, "document", "190 KB", "2026-09-01"),
]
# sedes de Vadelia (una empresa ficticia) → edificios → zonas (jerarquía propia para a!hierarchyBrowserField*)
RED = [
    {"id": "NOR", "label": "Sede Norte", "description": "Oficinas centrales", "details": "3 edificios", "icon": "map-marker", "children": [
        {"id": "NOR-A", "label": "Edificio A", "description": "Oficinas y atención al público", "icon": "building", "children": [
            {"id": "NOR-A-R", "label": "Recepción", "description": "Puestos 1 a 12", "icon": "users"},
            {"id": "NOR-A-C", "label": "Control de accesos", "description": "12 tornos", "icon": "shield"},
            {"id": "NOR-A-S", "label": "Salas de reuniones", "description": "38 salas", "icon": "sign-in"}]},
        {"id": "NOR-B", "label": "Edificio B", "description": "Oficinas y formación", "icon": "building", "children": [
            {"id": "NOR-B-F", "label": "Salas de formación", "description": "6 salas", "icon": "graduation-cap"}]},
        {"id": "NOR-ALM", "label": "Almacén", "description": "Edificio de servicios", "icon": "building", "children": [
            {"id": "NOR-ALM-M", "label": "Muelles de carga", "icon": "truck"}]}]},
    {"id": "SUR", "label": "Sede Sur", "description": "Oficinas y centro de formación", "details": "2 edificios", "icon": "map-marker", "children": [
        {"id": "SUR-1", "label": "Edificio 1", "description": "Plantas 0 a 4", "icon": "building", "children": [
            {"id": "SUR-1-F", "label": "Centro de formación", "icon": "graduation-cap"}]},
        {"id": "SUR-2", "label": "Edificio 2", "description": "Plantas 0 a 2", "icon": "building"}]},
    {"id": "EST", "label": "Sede Este", "details": "1 edificio", "icon": "map-marker", "children": [
        {"id": "EST-P", "label": "Edificio principal", "description": "Plantas 0 a 3", "icon": "building"}]},
    {"id": "OES", "label": "Sede Oeste", "details": "1 edificio", "icon": "map-marker", "children": [
        {"id": "OES-P", "label": "Edificio principal", "icon": "building"}]},
]
RED_TREE = [{"id": "RED", "label": "Sedes de Vadelia", "description": "4 sedes", "details": "Vadelia, S.A.", "icon": "globe", "children": RED}]


def demo(names, when, contents, card=True, note=None):
    """Una demostración: funciones SAIL (H2), cuándo usarlas según Appian y el ejemplo."""
    head = [{"type": "a!headingField", "text": names, "size": "MEDIUM", "headingTag": "H2", "marginBelow": "EVEN_LESS"},
            {"type": "a!richTextDisplayField", "labelPosition": "COLLAPSED", "marginBelow": "STANDARD", "value": [{"type": "a!richTextItem", "text": when, "color": "SECONDARY"}]}]
    body = contents if isinstance(contents, list) else [contents]
    s = {"type": "a!sectionLayout", "marginBelow": "EVEN_MORE", "contents": head + ([content_card(body)] if card else body)}
    if note:
        s["$note"] = note
    return s


def page(sid, title, subtitle, blocks, local=None):
    return {"id": sid, "title": title, "type": "page", "pattern": "P06", "req": ["C1"], "local": local or {},
            "interface": {"type": "a!headerContentLayout", "backgroundColor": BG, "contents": [page_header(title, subtitle)] + blocks}}


def two(a, b, widths=None):
    return cols(a, b, widths=widths or ["1X", "1X"])


# ------------------------------------------------------------------ Selectores y navegadores
p_nav = page("navegadores", "Selectores y navegadores", "Buscar y elegir usuarios, grupos, documentos, carpetas y registros; recorrer jerarquías", [
    demo("a!pickerFieldUsers · a!pickerFieldGroups · a!pickerFieldUsersAndGroups", "Elegir personas o grupos escribiendo parte del nombre. Mejor que un desplegable cuando hay más de 10 opciones.",
         two({"type": "a!pickerFieldUsers", "label": "Responsable", "value": "local!resp", "saveInto": "local!resp", "maxSelections": 1, "placeholder": "Escriba un nombre"},
             {"type": "a!pickerFieldUsersAndGroups", "label": "Notificar a", "value": "local!notif", "saveInto": "local!notif", "instructions": "Personas o grupos"})),
    demo("a!pickerFieldGroups · a!pickerFieldRecords · a!pickerFieldCustom", "Grupos del entorno, registros de un record type o cualquier lista propia (sugerencias con una regla).",
         cols({"type": "a!pickerFieldGroups", "label": "Equipo asignado", "value": "local!grupo", "saveInto": "local!grupo", "maxSelections": 1},
              {"type": "a!pickerFieldRecords", "label": "Incidencia relacionada", "recordType": "recordType!INC Incidencia", "value": "local!inc", "saveInto": "local!inc", "maxSelections": 1},
              {"type": "a!pickerFieldCustom", "label": "Sede", "value": "local!sede", "saveInto": "local!sede", "suggestFunction": "rule!INC_sugerirSedes", "$options": [{"id": "NOR", "label": "NOR · Sede Norte"}, {"id": "SUR", "label": "SUR · Sede Sur"}, {"id": "EST", "label": "EST · Sede Este"}, {"id": "OES", "label": "OES · Sede Oeste"}]})),
    demo("a!pickerFieldDocuments · a!pickerFieldFolders · a!pickerFieldDocumentsAndFolders", "Adjuntar un documento que ya está en Appian (no subir uno nuevo). folderFilter limita la búsqueda a una carpeta.",
         cols({"type": "a!pickerFieldDocuments", "label": "Procedimiento aplicable", "value": "local!docProc", "saveInto": "local!docProc", "folderFilter": "f-norm", "placeholder": "Buscar en Normativa"},
              {"type": "a!pickerFieldFolders", "label": "Carpeta de destino", "value": "local!carpeta", "saveInto": "local!carpeta", "maxSelections": 1},
              {"type": "a!pickerFieldDocumentsAndFolders", "label": "Documentación del expediente", "value": "local!docCarp", "saveInto": "local!docCarp"})),
    demo("a!userBrowserFieldColumns", "Encontrar a una persona recorriendo la estructura de grupos (cuando no se sabe su nombre). Los grupos se despliegan; las personas se seleccionan.",
         [{"type": "a!userBrowserFieldColumns", "label": "Técnico de guardia", "labelPosition": "COLLAPSED", "rootGroup": "g-dir", "pathValue": "local!rutaU", "pathSaveInto": "local!rutaU", "selectionValue": "local!tecnico", "selectionSaveInto": "local!tecnico", "height": "SHORT"},
          ro("Seleccionado", "{local!tecnico|map:usuarios|dash}", marginAbove="STANDARD")]),
    demo("a!groupBrowserFieldColumns · a!userAndGroupBrowserFieldColumns", "Elegir un grupo (o una persona o un grupo) viendo sus miembros. El recuento de miembros aparece al pasar el ratón.",
         two({"type": "a!groupBrowserFieldColumns", "label": "Grupo responsable", "rootGroup": "g-dir", "pathValue": "local!rutaG", "pathSaveInto": "local!rutaG", "selectionValue": "local!grupoSel", "selectionSaveInto": "local!grupoSel", "height": "SHORT", "hideUsers": True},
             {"type": "a!userAndGroupBrowserFieldColumns", "label": "Destinatario", "rootGroup": "g-mant", "pathValue": "local!rutaUG", "pathSaveInto": "local!rutaUG", "selectionValue": "local!ug", "selectionSaveInto": "local!ug", "height": "SHORT"})),
    demo("a!documentBrowserFieldColumns · a!folderBrowserFieldColumns · a!documentAndFolderBrowserFieldColumns", "Explorar una carpeta o una base de conocimiento. navigationValue es la carpeta abierta; selectionValue, lo elegido.",
         [{"type": "a!documentAndFolderBrowserFieldColumns", "label": "Documentación de operaciones", "labelPosition": "COLLAPSED", "rootFolder": None, "navigationValue": "local!navDoc", "navigationSaveInto": "local!navDoc", "selectionValue": "local!docSel", "selectionSaveInto": "local!docSel", "height": "SHORT"},
          two({"type": "a!documentBrowserFieldColumns", "label": "Solo documentos", "rootFolder": "f-norm", "navigationValue": "local!navDoc2", "navigationSaveInto": "local!navDoc2", "selectionValue": "local!docSel2", "selectionSaveInto": "local!docSel2", "height": "SHORT"},
              {"type": "a!folderBrowserFieldColumns", "label": "Solo carpetas", "rootFolder": None, "navigationValue": "local!navCarp", "navigationSaveInto": "local!navCarp", "selectionValue": "local!carpSel", "selectionSaveInto": "local!carpSel", "height": "SHORT"}) | {"marginAbove": "MORE"}]),
    demo("a!hierarchyBrowserFieldColumns · a!hierarchyBrowserFieldColumnsNode", "Recorrer datos propios con jerarquía (sede → edificio → zona) en columnas. Cada nodo se describe con nodeConfigs y fv!nodeValue.",
         {"type": "a!hierarchyBrowserFieldColumns", "label": "Ubicación", "labelPosition": "COLLAPSED", "firstColumnValues": RED, "pathValue": "local!rutaH", "pathSaveInto": "local!rutaH", "selectionValue": "local!zona", "selectionSaveInto": "local!zona", "height": "MEDIUM",
          "nodeConfigs": {"type": "a!hierarchyBrowserFieldColumnsNode", "id": "{fv!nodeValue.id}", "label": "{fv!nodeValue.label}", "image": {"type": "a!documentImage", "document": "cons!INC_ICONO_UBICACION"}, "$icon": "{fv!nodeValue.icon}",
                          "isDrillable": "{a!isNotNullOrEmpty(fv!nodeValue.children)}", "isSelectable": True},
          "nextColumnValues": "{fv!nodeValue.children}"}),
    demo("a!hierarchyBrowserFieldTree · a!hierarchyBrowserFieldTreeNode", "La misma jerarquía como árbol vertical: el primer valor de pathValue es la raíz; cada nivel muestra los hijos del nodo pulsado.",
         {"type": "a!hierarchyBrowserFieldTree", "label": "Sedes", "labelPosition": "COLLAPSED", "pathValue": "local!rutaT", "pathSaveInto": "local!rutaT",
          "nodeConfigs": {"type": "a!hierarchyBrowserFieldTreeNode", "id": "{fv!nodeValue.id}", "label": "{fv!nodeValue.label}", "description": "{fv!nodeValue.description}", "details": "{fv!nodeValue.details}",
                          "image": {"type": "a!documentImage", "document": "cons!INC_ICONO_UBICACION"}, "$icon": "{fv!nodeValue.icon}", "isDrillable": "{a!isNotNullOrEmpty(fv!nodeValue.children)}", "nextLevelCount": "{count(fv!nodeValue.children)}"},
          "nextLevelValues": "{fv!nodeValue.children}"}),
    demo("a!orgChartField", "Mostrar la línea jerárquica de una persona: su responsable, sus compañeros y quién depende de ella. Pulse una tarjeta para centrar el organigrama.",
         {"type": "a!orgChartField", "label": "Organigrama", "labelPosition": "COLLAPSED", "value": "local!persona", "saveInto": "local!persona", "showAllAncestors": True}),
], local={"local!resp": None, "local!notif": ["mlopez"], "local!grupo": None, "local!inc": None, "local!sede": ["NOR"], "local!docProc": ["d-prev"], "local!carpeta": None, "local!docCarp": None,
          "local!rutaU": ["g-norte", "g-edifa"], "local!tecnico": None, "local!rutaG": ["g-norte"], "local!grupoSel": "g-norte", "local!rutaUG": [], "local!ug": None,
          "local!navDoc": "f-seg", "local!docSel": "d-prev", "local!navDoc2": None, "local!docSel2": None, "local!navCarp": None, "local!carpSel": None,
          "local!rutaH": [RED[0], RED[0]["children"][0]], "local!zona": RED[0]["children"][0], "local!rutaT": [RED_TREE[0], RED[0]], "local!persona": "mlopez"})

# ------------------------------------------------------------------ datos de incidencias (grids, gráficos, registros)
INC = [
    (1, "INC-2026-0412", "Fuga de agua en el falso techo del vestíbulo", "Mantenimiento", "NOR", "En curso", "Alta", "2026-09-12", "rsanchez", 6, 1850),
    (2, "INC-2026-0415", "Ascensor detenido en el edificio B", "Mantenimiento", "NOR", "Pendiente", "Alta", "2026-09-14", "sortiz", 4, 920),
    (3, "INC-2026-0418", "Cola excesiva en el control de accesos principal", "Operaciones", "SUR", "Cerrada", "Media", "2026-09-15", "ecastro", 2, 0),
    (4, "INC-2026-0421", "Pantallas de cartelería sin datos en la planta 2", "Sistemas", "SUR", "En curso", "Media", "2026-09-17", "hromero", 3, 310),
    (5, "INC-2026-0423", "Humedad en los aseos de la planta baja", "Limpieza", "EST", "Pendiente", "Baja", "2026-09-18", "lfernandez", 1, 120),
    (6, "INC-2026-0426", "Avería de climatización en la sala de formación C", "Mantenimiento", "OES", "En curso", "Alta", "2026-09-20", "ivega", 8, 2400),
    (7, "INC-2026-0430", "Cajas atascadas en la cinta 7 del almacén", "Operaciones", "NOR", "Cerrada", "Media", "2026-09-21", "pmartin", 2, 150),
    (8, "INC-2026-0433", "Wifi de visitantes intermitente en el edificio 2", "Sistemas", "SUR", "Pendiente", "Media", "2026-09-23", "hromero", 5, 640),
]
INC_ROWS = [{"id": i, "codigo": c, "titulo": t, "area": a, "sede": se, "estado": e, "prioridad": p, "fecha": f, "responsable": r, "horas": hh, "coste": co}
            for i, c, t, a, se, e, p, f, r, hh, co in INC]
ESTADOS_INC = {"Pendiente": "atencion", "En curso": "enCurso", "Cerrada": "neutral"}
ORDEN_INC = ["Pendiente", "En curso", "Cerrada"]
ESTADO = state_map(ESTADOS_INC)
ESTADO_G = state_map(ESTADOS_INC, grid=True)
# imágenes de ejemplo embebidas (SVG): un prototipo no descarga imágenes de internet. Con los colores de la marca: el
# oscuro (NAVY), el de resaltado (GREEN) y el gris secundario, más el acento de Appian, su tinte claro y el marino oscurecido
_c = lambda h: h.replace("#", "%23")  # un color hex dentro de un data URI
CIELO, CIELO_CLARO, SUELO = "#1D659C", "#A5C1D7", "#081220"
SVG_EDIFICIO = "data:image/svg+xml;utf8," + (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 320 180'><defs><linearGradient id='g' x1='0' y1='0' x2='0' y2='1'><stop offset='0' stop-color='{_c(CIELO)}'/><stop offset='1' stop-color='{_c(CIELO_CLARO)}'/></linearGradient></defs>"
          "<rect width='320' height='180' fill='url(%23g)'/><g fill='%23ffffff' opacity='.85'><rect x='128' y='36' width='34' height='104'/><rect x='168' y='58' width='26' height='82'/></g>"
          f"<path d='M0 150 Q160 70 320 150 L320 180 L0 180Z' fill='{_c(NAVY)}'/><g fill='{_c(GREEN)}'><rect x='40' y='140' width='240' height='6' rx='3'/></g></svg>")
SVG_VIAL = "data:image/svg+xml;utf8," + (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 320 180'><rect width='320' height='180' fill='{_c(GREY_TXT)}'/><rect y='70' width='320' height='40' fill='%23333333'/>"
             "<g fill='%23ffffff'>" + "".join(f"<rect x='{x}' y='88' width='20' height='4'/>" for x in range(10, 320, 36)) + f"</g><circle cx='270' cy='40' r='18' fill='{_c(GREEN)}' opacity='.9'/></svg>")
BILL = "data:image/svg+xml;utf8," + (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1200 300'><defs><linearGradient id='s' x1='0' y1='0' x2='1' y2='1'><stop offset='0' stop-color='{_c(NAVY)}'/><stop offset='1' stop-color='{_c(CIELO)}'/></linearGradient></defs>"
        "<rect width='1200' height='300' fill='url(%23s)'/><g fill='%23ffffff' opacity='.9'><rect x='760' y='125' width='70' height='125'/><rect x='840' y='95' width='60' height='155'/><rect x='910' y='145' width='50' height='105'/></g>"
        f"<path d='M0 260 Q600 150 1200 260 L1200 300 L0 300Z' fill='{_c(SUELO)}'/><rect x='0' y='285' width='1200' height='6' fill='{_c(GREEN)}'/></svg>")
SEDES = [("NOR", "Sede Norte", "Oficinas centrales", "building", 1250, "En servicio"), ("SUR", "Sede Sur", "Centro de formación", "building", 860, "En servicio"),
         ("EST", "Sede Este", "Oficinas", "building", 420, "Obras en el edificio"), ("OES", "Sede Oeste", "Oficinas y almacén", "building", 310, "En servicio")]


def rtd(value, **kw):
    n = {"type": "a!richTextDisplayField", "labelPosition": "COLLAPSED", "value": value if isinstance(value, list) else [value]}
    n.update(kw); return n


def strong(t, **kw):
    it = {"type": "a!richTextItem", "text": t, "style": "STRONG"}; it.update(kw); return it


def muted(t, **kw):
    it = {"type": "a!richTextItem", "text": t, "color": "SECONDARY"}; it.update(kw); return it


def opener(icon, title, text, action):
    return (icon, title, text, action)


# ------------------------------------------------------------------ 1. Diseño de página: layouts, subcomponentes, billboards y plantillas de nivel superior
p_dis = page("diseno", "Diseño de página", "Layouts para ordenar el contenido y plantillas de página de nivel superior", [
    demo("Plantillas de nivel superior · a!formLayout · a!wizardLayout · a!paneLayout · a!headerContentLayout", "Cada pantalla empieza con una de estas cuatro. Esta página es un a!headerContentLayout; pulse una tarjeta para ver las otras con sus barras de título.",
         cards_as_buttons([("file-text-o", "Formulario", "a!formLayout con a!headerTemplateSimple, a!validationMessage y a!buttonLayout", {"goto": "formulario"}),
                           ("list-ol", "Asistente", "a!wizardLayout con a!wizardStep y a!sidebarTemplate", {"goto": "asistente"}),
                           ("columns", "Paneles", "a!paneLayout con a!pane que se desplazan por separado", {"goto": "paneles"}),
                           ("window-maximize", "Diálogos", "a!headerTemplateFull y a!headerTemplateImage como barra de título", {"dialog": "dlg-full"})], marginBelow="NONE"), card=False),
    demo("a!columnsLayout · a!columnLayout", "Dividir una zona en columnas. Anchos fijos (NARROW, MEDIUM…) para lo auxiliar y AUTO para el contenido principal; stackWhen apila en móvil.",
         {"type": "a!columnsLayout", "showDividers": True, "stackWhen": ["PHONE", "TABLET_PORTRAIT"], "columns": [
             {"type": "a!columnLayout", "width": "NARROW", "contents": [ro("Sede", "NOR"), ro("Planta", "2")]},
             {"type": "a!columnLayout", "contents": [ro("Incidencia", "Ascensor B-03 parado por inspección del freno de servicio"), ro("Origen", "Centro de control de mantenimiento")]},
             {"type": "a!columnLayout", "width": "NARROW_PLUS", "contents": [ro("Estado", "En curso"), ro("Actualizado", "26/09/2026 08:40")]}]}),
    demo("a!sideBySideLayout · a!sideBySideItem", "Poner juntos elementos pequeños que se leen como una línea: avatar, nombre y estado. Se ajusta al contenido (MINIMIZE) sin partir el texto.",
         {"type": "a!sideBySideLayout", "alignVertical": "MIDDLE", "spacing": "STANDARD", "items": [
             {"type": "a!sideBySideItem", "width": "MINIMIZE", "item": {"type": "a!imageField", "labelPosition": "COLLAPSED", "size": "SMALL", "style": "AVATAR", "images": [{"type": "a!userImage", "user": "Rocío Sánchez Vidal"}]}},
             {"type": "a!sideBySideItem", "item": rtd([strong("Rocío Sánchez Vidal"), "\n", muted("Supervisora del edificio A · turno de mañana")])},
             {"type": "a!sideBySideItem", "width": "MINIMIZE", "item": {"type": "a!tagField", "labelPosition": "COLLAPSED", "size": "SMALL", "tags": [{"type": "a!tagItem", "text": "De guardia", "backgroundColor": STATES["positivo"]["tag"]}]}}]}),
    demo("a!cardLayout", "Agrupar y destacar. Blanca con sombra sobre fondo gris; con color suave o barra decorativa para estados; con link, toda la card es clicable.",
         {"type": "a!columnsLayout", "columns": [
             {"type": "a!columnLayout", "contents": [{"type": "a!cardLayout", "style": "NONE", "showShadow": True, "showBorder": False, "shape": "SEMI_ROUNDED", "padding": "STANDARD", "decorativeBarPosition": "TOP", "decorativeBarColor": GREEN,
                                                     "contents": [rtd([strong("Barra decorativa"), "\n", muted("Resalta sin llenar de color")])]}]},
             {"type": "a!columnLayout", "contents": [{"type": "a!cardLayout", "style": STATES["enCurso"]["tag"], "showBorder": False, "shape": "SEMI_ROUNDED", "padding": "STANDARD", "contents": [rtd([strong("Color suave (hex)"), "\n", muted("Estado «En curso»")])]}]},
             {"type": "a!columnLayout", "contents": [{"type": "a!cardLayout", "style": NAVY, "showBorder": False, "shape": "SEMI_ROUNDED", "padding": "STANDARD", "contents": [
                 rtd([strong("Fondo oscuro"), "\n", "El enlace ajusta su color (26.9): ", {"type": "a!richTextItem", "text": "ver detalle", "link": {"type": "a!dynamicLink", "$action": {"goto": "diseno"}}}])]}]},
             {"type": "a!columnLayout", "contents": [{"type": "a!cardLayout", "style": "NONE", "showBorder": True, "borderWeight": "THICK", "borderColor": "ACCENT", "shape": "SEMI_ROUNDED", "padding": "STANDARD", "link": {"type": "a!dynamicLink", "$action": {"goto": "graficos"}}, "accessibilityText": "Ir a gráficos",
                                                     "contents": [rtd([strong("Card con enlace"), "\n", muted("Borde grueso (26.7)")])]}]}]}, card=False),
    demo("a!cardGroupLayout", "Repetir cards del mismo tamaño que se recolocan solas según el ancho (catálogos, sedes, servicios).",
         {"type": "a!cardGroupLayout", "labelPosition": "COLLAPSED", "cardWidth": "MEDIUM", "cardHeight": "SHORT", "spacing": "STANDARD", "cards": [
             {"type": "a!cardLayout", "style": "NONE", "showBorder": False, "showShadow": True, "shape": "SEMI_ROUNDED", "padding": "STANDARD", "contents": [
                 rtd([{"type": "a!richTextIcon", "icon": ic, "color": "ACCENT", "size": "MEDIUM"}, "  ", strong(f"{c} · {n}"), "\n", muted(f"{m} · {v:,} personas".replace(",", "."))]),
                 {"type": "a!tagField", "labelPosition": "COLLAPSED", "size": "SMALL", "marginAbove": "LESS", "tags": [{"type": "a!tagItem", "text": st, "backgroundColor": STATES["positivo" if st == "En servicio" else "atencion"]["tag"]}]}]}
             for c, n, m, ic, v, st in SEDES]}, card=False),
    demo("a!sectionLayout · a!validationMessage", "Dar título a un bloque (H2/H3) y, si hace falta, plegarlo. Las validaciones de sección avisan de reglas entre varios campos; con validateAfter REFRESH, al momento.",
         {"type": "a!sectionLayout", "label": "Ventana de mantenimiento", "labelSize": "SMALL", "labelHeadingTag": "H3", "labelColor": "STANDARD", "isCollapsible": True, "dividerColor": "SECONDARY", "divider": "BELOW",
          "validations": [{"type": "a!validationMessage", "message": "La hora de fin debe ser posterior a la de inicio", "validateAfter": "REFRESH", "showWhen": "local!finVentana <= local!inicioVentana"}],
          "contents": [cols({"type": "a!dateTimeField", "label": "Inicio", "value": "local!inicioVentana", "saveInto": "local!inicioVentana"},
                            {"type": "a!dateTimeField", "label": "Fin", "value": "local!finVentana", "saveInto": "local!finVentana"})]}),
    demo("a!boxLayout", "Recuadro con cabecera de color para datos que deben destacar o separarse. 26.7: color y grosor del borde, peso de la etiqueta.",
         cols({"type": "a!boxLayout", "label": "Aviso de mantenimiento", "style": "WARN", "shape": "SEMI_ROUNDED", "marginBelow": "NONE", "contents": [rtd("Edificio A sin electricidad de 23:00 a 05:00 por mantenimiento del cuadro general.")]},
              {"type": "a!boxLayout", "label": "Datos del turno", "style": "STANDARD", "borderColor": "ACCENT", "borderWeight": "MEDIUM", "labelFontWeight": "BOLD", "shape": "SEMI_ROUNDED", "marginBelow": "NONE", "contents": [rtd("Turno de mañana · 6:00 a 14:00 · 14 personas")]},
              {"type": "a!boxLayout", "label": "Caja con color de marca", "style": NAVY, "shape": "SEMI_ROUNDED", "marginBelow": "NONE", "contents": [rtd("Cabecera con el color oscuro de la marca; el texto se vuelve blanco solo.")]}), card=False),
    demo("a!tabLayout · a!tabItem", "Secciones del mismo nivel que no hace falta ver a la vez. Horizontal con 2–6 pestañas; 26.7: vertical (más secciones), anchos iguales (FILL) y carga en segundo plano (ASYNC).",
         cols({"type": "a!tabLayout", "tabWidth": "FILL", "selectedTab": "local!tabH", "tabs": [
                  {"type": "a!tabItem", "label": "Resumen", "icon": "info-circle", "contents": [rtd("Datos generales del edificio.")]},
                  {"type": "a!tabItem", "label": "Equipos", "icon": "cogs", "contents": [rtd("Ascensores, montacargas y puertas automáticas.")]},
                  {"type": "a!tabItem", "label": "Histórico", "icon": "history", "loadBehavior": "ASYNC", "contents": [rtd("Se carga en segundo plano.")]}]},
              {"type": "a!tabLayout", "orientation": "VERTICAL", "selectedTab": "local!tabV", "tabs": [
                  {"type": "a!tabItem", "label": "Recepción", "contents": [rtd("Puestos 1 a 12.")]},
                  {"type": "a!tabItem", "label": "Accesos", "contents": [rtd("12 tornos de control.")]},
                  {"type": "a!tabItem", "label": "Salas", "contents": [rtd("Salas de reuniones de las plantas 1 a 3.")]}]})),
    demo("a!billboardLayout · a!barOverlay · a!columnOverlay · a!fullOverlay", "Imagen de fondo con texto encima para portadas y cabeceras visuales. El overlay oscuro garantiza el contraste del texto.",
         [{"type": "a!billboardLayout", "backgroundMedia": {"type": "a!webImage", "source": BILL, "altText": "Edificios de oficinas al atardecer"}, "backgroundColor": NAVY, "height": "SHORT_PLUS", "marginBelow": "STANDARD",
           "overlay": {"type": "a!columnOverlay", "position": "START", "width": "MEDIUM", "style": "DARK", "alignVertical": "MIDDLE", "contents": [
               {"type": "a!headingField", "text": "Operaciones de invierno", "size": "LARGE", "headingTag": "H2"}, rtd("Plan de temporada 2026-2027 para todas las sedes")]}},
          cols({"type": "a!billboardLayout", "backgroundMedia": {"type": "a!webImage", "source": SVG_VIAL, "altText": "Vial de acceso"}, "backgroundColor": NAVY, "height": "SHORT", "marginBelow": "NONE",
                "overlay": {"type": "a!barOverlay", "position": "BOTTOM", "style": "SEMI_DARK", "padding": "STANDARD", "contents": [rtd([strong("Aparcamiento P1"), " · reapertura el 3 de octubre"])]}},
               {"type": "a!billboardLayout", "backgroundColor": NAVY, "height": "SHORT", "marginBelow": "NONE",
                "overlay": {"type": "a!fullOverlay", "alignVertical": "MIDDLE", "style": "NONE", "padding": "MORE", "contents": [
                    rtd([{"type": "a!richTextItem", "text": "98,7 %", "size": "LARGE_PLUS", "style": "STRONG", "color": GREEN}, "\n", {"type": "a!richTextItem", "text": "incidencias resueltas en plazo en septiembre", "color": "#FFFFFF"}], align="CENTER")]}})]),
], local={"local!inicioVentana": "2026-09-30T23:00", "local!finVentana": "2026-09-30T22:00", "local!tabH": 1, "local!tabV": 1})

# plantillas de nivel superior: formulario, asistente, paneles y diálogos con barras de título
scr_form = {"id": "formulario", "title": "Parte de incidencia", "type": "form", "pattern": "P03", "req": ["C1"],
    "local": {"local!titulo": None, "local!sede": None, "local!desc": None},
    "interface": {"type": "a!formLayout", "contentsWidth": "MEDIUM",
        "titleBar": {"type": "a!headerTemplateSimple", "title": "Nuevo parte de incidencia", "secondaryText": "a!formLayout con a!headerTemplateSimple", "stampIcon": "wrench", "stampColor": "ACCENT"},
        "contents": [txt("Título", "local!titulo", required=True, characterLimit=120),
                     dd("Sede", ["NOR", "SUR", "EST", "OES"], "local!sede", required=True),
                     par("Descripción", "local!desc", instructions="Qué ocurre, dónde y desde cuándo")],
        "validations": [{"type": "a!validationMessage", "message": "Indique la sede antes de enviar el parte", "validateAfter": "SUBMIT", "showWhen": "a!isNullOrEmpty(local!sede)"}],
        "buttons": bl(primary("Enviar parte", {"goto": "diseno"}), [secondary("Cancelar", {"goto": "diseno"})])}}
scr_wiz = {"id": "asistente", "title": "Alta de proveedor", "type": "form", "pattern": "P04", "req": ["C1"],
    "local": {"local!razon": "Clima Sur S.L.", "local!cif": None, "local!servicio": None},
    "interface": {"type": "a!wizardLayout", "style": "DOT_VERTICAL", "contentsWidth": "MEDIUM", "showButtonDivider": True,
        "titleBar": {"type": "a!sidebarTemplate", "title": "Alta de proveedor", "secondaryText": "a!wizardLayout con a!sidebarTemplate", "backgroundColor": NAVY, "width": "NARROW_PLUS"},
        "steps": [{"type": "a!wizardStep", "label": "Datos de la empresa", "contents": [txt("Razón social", "local!razon", required=True), txt("CIF", "local!cif", required=True)]},
                  {"type": "a!wizardStep", "label": "Servicio", "contents": [dd("Tipo de servicio", ["Mantenimiento", "Limpieza", "Seguridad", "Sistemas"], "local!servicio", required=True)]},
                  {"type": "a!wizardStep", "label": "Revisión", "contents": [ro("Razón social", "{local!razon}"), ro("CIF", "{local!cif|dash}"), ro("Servicio", "{local!servicio|dash}")]}],
        "primaryButtons": [primary("Dar de alta", {"goto": "diseno"})], "secondaryButtons": [secondary("Cancelar", {"goto": "diseno"})]}}
scr_pane = {"id": "paneles", "title": "Consola de guardia", "type": "page", "pattern": "P09", "req": ["C1"], "local": {"local!sel": 1},
    "interface": {"type": "a!paneLayout", "panes": [
        {"type": "a!pane", "width": "NARROW_PLUS", "backgroundColor": "#F4F5F7", "contents": [
            {"type": "a!headingField", "text": "Avisos", "size": "LARGE", "headingTag": "H1"},
            {"type": "a!forEach", "items": "data!incidencias", "expression": {"type": "a!cardLayout", "style": "{if(local!sel = fv!item.id, \"%s\", \"NONE\")}" % STATES["enCurso"]["tag"], "showBorder": False, "showShadow": True,
                "decorativeBarPosition": "{if(local!sel = fv!item.id, \"START\", \"NONE\")}", "decorativeBarColor": NAVY, "shape": "SEMI_ROUNDED", "padding": "LESS", "marginBelow": "LESS",
                "link": {"type": "a!dynamicLink", "value": "{fv!item.id}", "saveInto": "local!sel"}, "accessibilityText": "{fv!item.codigo}",
                "contents": [rtd([strong("{fv!item.codigo}"), "\n", muted("{fv!item.titulo}")])]}}]},
        {"type": "a!pane", "contents": [{"type": "a!forEach", "items": "data!incidencias", "$filter": "fv!item.id = local!sel", "expression": {"type": "a!sectionLayout", "contents": [
            page_header("{fv!item.codigo}", "{fv!item.titulo}", secondary("Volver al catálogo", {"goto": "diseno"}), level="H2"),
            content_card(field_summary([("Sede", "{fv!item.sede}"), ("Área", "{fv!item.area}"), ("Estado", "{fv!item.estado}"), ("Prioridad", "{fv!item.prioridad}")], columns=2))]}}]}]}}
dlg_full = {"id": "dlg-full", "title": "Detalle de la visita", "type": "dialog", "pattern": "P07", "req": ["C1"], "openFrom": "diseno", "$dialogWidth": "NARROW",
    "interface": {"type": "a!formLayout", "contentsWidth": "FULL",
        "titleBar": {"type": "a!headerTemplateFull", "title": "VIS-2026-0186 · Visita de proveedores", "secondaryText": "a!headerTemplateFull · llegada 08:40 · sala 2.2", "backgroundColor": NAVY, "stampIcon": "users", "stampColor": GREEN},
        "contents": [field_summary([("Estado", "En curso"), ("Recepción", "Puesto 3"), ("Asistentes", "18")], columns=3)],
        "buttons": bl(secondary("Ver con imagen", {"dialog": "dlg-imagen", "close": True}), [secondary("Cerrar", {"close": True})])}}
dlg_img = {"id": "dlg-imagen", "title": "Edificio A", "type": "dialog", "pattern": "P07", "req": ["C1"], "openFrom": "diseno", "$dialogWidth": "NARROW",
    "interface": {"type": "a!formLayout", "contentsWidth": "FULL",
        "titleBar": {"type": "a!headerTemplateImage", "title": "Edificio A", "secondaryText": "a!headerTemplateImage · Sede Norte", "backgroundColor": "WHITE", "image": {"type": "a!webImage", "source": SVG_EDIFICIO, "altText": "Edificio A"}, "imageSize": "MEDIUM"},
        "contents": [rtd("Edificio inaugurado en 2006: 38 salas de reuniones y 12 tornos de control de accesos.")],
        "buttons": bl([], [secondary("Cerrar", {"close": True})])}}

# ------------------------------------------------------------------ 2. Entradas y selección
CARD_OPC = [{"id": "MAN", "label": "Mantenimiento", "detail": "Averías de edificios e instalaciones", "icon": "wrench"},
            {"id": "SIS", "label": "Sistemas", "detail": "Cartelería, wifi, megafonía, control de accesos", "icon": "desktop"},
            {"id": "LIM", "label": "Limpieza", "detail": "Aseos, zonas comunes y aparcamientos", "icon": "tint"}]
p_ent = page("entradas", "Entradas y selección", "Campos para escribir, subir, firmar y elegir", [
    demo("a!textField · a!paragraphField · a!encryptedTextField · a!barcodeField", "Texto corto, texto largo (con contador), texto cifrado en la base de datos y lectura de códigos (con cámara en Appian Mobile; en web, un campo de texto).",
         [cols(txt("Matrícula del vehículo", "local!matricula", placeholder="1234 BCD", characterLimit=10, required=True),
               {"type": "a!encryptedTextField", "label": "Código de acceso al almacén", "value": "local!codigo", "saveInto": "local!codigo", "instructions": "Se guarda cifrado"},
               {"type": "a!barcodeField", "label": "Etiqueta del paquete", "value": "local!barcode", "saveInto": "local!barcode", "acceptedTypes": ["CODE128", "QRCODE"], "placeholder": "Escanee o escriba el código"}),
          par("Observaciones", "local!obs", characterLimit=500, showCharacterCount=True, height="SHORT", marginAbove="STANDARD")]),
    demo("a!integerField · a!floatingPointField · a!dateField · a!dateTimeField", "Números enteros o con decimales (con alineación a la derecha en lectura) y fechas con o sin hora.",
         cols({"type": "a!integerField", "label": "Personas afectadas", "value": "local!personas", "saveInto": "local!personas", "align": "RIGHT"},
              {"type": "a!floatingPointField", "label": "Importe estimado (€)", "value": "local!importe", "saveInto": "local!importe", "align": "RIGHT"},
              date("Fecha del aviso", "local!fecha"),
              {"type": "a!dateTimeField", "label": "Hora de cierre prevista", "value": "local!cierre", "saveInto": "local!cierre"})),
    demo("a!fileUploadField · a!signatureField", "Subir documentos nuevos (zona amplia para arrastrar) y firmar en pantalla. 26.8: color del botón independiente del estilo y firma con línea discontinua.",
         cols({"type": "a!fileUploadField", "label": "Fotografías de la avería", "value": "local!fotos", "saveInto": "local!fotos", "dropZoneStyle": "EXPANDED", "buttonStyle": "OUTLINE", "buttonColor": "ACCENT", "maxSelections": 5},
              [{"type": "a!signatureField", "label": "Firma del técnico", "value": "local!firma", "saveInto": "local!firma", "fileName": "firma_tecnico", "buttonStyle": "OUTLINE", "buttonColor": "ACCENT", "target": "cons!INC_CARPETA_FIRMAS"},
               {"type": "a!signatureField", "label": "Firma del responsable (ya firmado)", "value": "local!firma2", "saveInto": "local!firma2", "buttonStyle": "SOLID", "target": "cons!INC_CARPETA_FIRMAS", "marginAbove": "STANDARD"}])),
    demo("a!styledTextEditorField", "Texto con formato (negrita, listas, enlaces) para comunicados o notas largas. Guarda HTML.",
         {"type": "a!styledTextEditorField", "label": "Comunicado a la plantilla", "value": "local!comunicado", "saveInto": "local!comunicado", "height": "SHORT"}),
    demo("a!dropdownField · a!dropdownFieldByIndex · a!multipleDropdownField · a!multipleDropdownFieldByIndex", "Elegir de una lista de 6 a 20 opciones (una o varias). ByIndex guarda la posición en vez del valor.",
         cols(dd("Área", ["Mantenimiento", "Sistemas", "Operaciones", "Limpieza"], "local!area", placeholder="Seleccione un área"),
              {"type": "a!dropdownFieldByIndex", "label": "Prioridad (índice)", "choiceLabels": ["Alta", "Media", "Baja"], "value": "local!prioIdx", "saveInto": "local!prioIdx", "placeholder": "Seleccione"},
              {"type": "a!multipleDropdownField", "label": "Sedes", "choiceLabels": ["NOR", "SUR", "EST", "OES"], "choiceValues": ["NOR", "SUR", "EST", "OES"], "value": "local!sedes", "saveInto": "local!sedes", "placeholder": "Todos"},
              {"type": "a!multipleDropdownFieldByIndex", "label": "Turnos (índice)", "choiceLabels": ["Mañana", "Tarde", "Noche"], "value": "local!turnos", "saveInto": "local!turnos", "placeholder": "Todos"})),
    demo("a!radioButtonField · a!radioButtonFieldByIndex · a!checkboxField · a!checkboxFieldByIndex", "Hasta 5 opciones a la vista: una (radio) o varias (checkbox). choiceStyle CARDS las muestra como tarjetas.",
         cols({"type": "a!radioButtonField", "label": "Afecta a la actividad", "choiceLabels": ["Sí", "No", "No se sabe"], "choiceValues": ["S", "N", "NS"], "value": "local!afecta", "saveInto": "local!afecta", "choiceLayout": "COMPACT"},
              {"type": "a!radioButtonFieldByIndex", "label": "Turno", "choiceLabels": ["Mañana", "Tarde", "Noche"], "value": "local!turnoIdx", "saveInto": "local!turnoIdx", "choiceStyle": "CARDS"},
              {"type": "a!checkboxField", "label": "Avisar a", "choiceLabels": ["Centro de control", "Seguridad", "Recursos humanos"], "choiceValues": ["CCO", "SEG", "RRHH"], "value": "local!avisar", "saveInto": "local!avisar"},
              {"type": "a!checkboxFieldByIndex", "label": "Medidas adoptadas", "choiceLabels": ["Zona acotada", "Señalización", "Desvío de visitantes"], "value": "local!medidas", "saveInto": "local!medidas", "choiceStyle": "CARDS"})),
    demo("a!booleanCheckboxField · a!toggleField", "Una sola casilla para aceptar algo y un interruptor para activar o desactivar al momento.",
         cols({"type": "a!booleanCheckboxField", "choiceLabel": "He revisado la zona y no hay riesgo para las personas", "value": "local!revisado", "saveInto": "local!revisado"},
              {"type": "a!toggleField", "choiceLabel": "Notificar por correo cuando cambie el estado", "value": "local!notificar", "saveInto": "local!notificar"})),
    demo("a!cardChoiceField · a!cardTemplateBarTextStacked · a!cardTemplateBarTextJustified · a!cardTemplateTile", "Elegir entre pocas opciones que necesitan explicación o icono. Tres plantillas de tarjeta.",
         [{"type": "a!cardChoiceField", "label": "Tipo de incidencia (apilada)", "data": CARD_OPC, "value": "local!tipo1", "saveInto": "local!tipo1", "maxSelections": 1,
           "cardTemplate": {"type": "a!cardTemplateBarTextStacked", "id": "{fv!data.id}", "primaryText": "{fv!data.label}", "secondaryText": "{fv!data.detail}", "icon": "{fv!data.icon}"}},
          {"type": "a!cardChoiceField", "label": "Tipo de incidencia (justificada)", "data": CARD_OPC, "value": "local!tipo2", "saveInto": "local!tipo2", "maxSelections": 1, "marginAbove": "STANDARD",
           "cardTemplate": {"type": "a!cardTemplateBarTextJustified", "id": "{fv!data.id}", "primaryText": "{fv!data.label}", "secondaryText": "{fv!data.detail}", "icon": "{fv!data.icon}"}},
          {"type": "a!cardChoiceField", "label": "Tipo de incidencia (mosaico)", "data": CARD_OPC, "value": "local!tipo3", "saveInto": "local!tipo3", "maxSelections": 1, "marginAbove": "STANDARD",
           "cardTemplate": {"type": "a!cardTemplateTile", "id": "{fv!data.id}", "primaryText": "{fv!data.label}", "secondaryText": "{fv!data.detail}", "icon": "{fv!data.icon}"}}]),
], local={"local!matricula": "4821 BCD", "local!codigo": None, "local!barcode": None, "local!obs": None, "local!personas": 46, "local!importe": 1850.5, "local!fecha": "2026-09-26", "local!cierre": None,
          "local!fotos": [{"name": "falso_techo_1.jpg", "size": "1,2 MB"}], "local!firma": None, "local!firma2": "firma_responsable.png",
          "local!comunicado": "<p>Se informa a la plantilla de que el <b>edificio A</b> permanecerá cerrado esta noche.</p>",
          "local!area": None, "local!prioIdx": 1, "local!sedes": ["NOR", "SUR"], "local!turnos": [], "local!afecta": "S", "local!turnoIdx": 1, "local!avisar": ["CCO"], "local!medidas": [1, 2],
          "local!revisado": True, "local!notificar": False, "local!tipo1": "MAN", "local!tipo2": None, "local!tipo3": "SIS"})

# ------------------------------------------------------------------ 3. Visualización
p_vis = page("visualizacion", "Visualización", "Texto, cifras, estados, imágenes, documentos, vídeo y contenido web", [
    demo("a!headingField · a!richTextDisplayField · a!richTextItem · a!richTextIcon", "Títulos con jerarquía real (H1–H6) y texto con estilos, iconos y enlaces. 26.7: pesos LIGHT y SEMI_BOLD.",
         [{"type": "a!headingField", "text": "Plan de invierno 2026-2027", "size": "LARGE", "headingTag": "H2", "fontWeight": "BOLD", "marginBelow": "LESS"},
          rtd([{"type": "a!richTextIcon", "icon": "info-circle", "color": "ACCENT"}, " ", {"type": "a!richTextItem", "text": "Texto ligero, ", "style": "LIGHT"}, {"type": "a!richTextItem", "text": "semi negrita ", "style": "SEMI_BOLD"},
               "y ", {"type": "a!richTextItem", "text": "negrita", "style": "STRONG"}, ". Los enlaces van en el color de acento: ",
               {"type": "a!richTextItem", "text": "ver el plan completo", "link": {"type": "a!dynamicLink", "$action": {"goto": "visualizacion"}}, "linkStyle": "STANDALONE"}])]),
    demo("a!richTextBulletedList · a!richTextNumberedList · a!richTextListItem · a!richTextImage", "Listas con viñetas o numeradas (con subniveles) e imágenes pequeñas dentro del texto, como un avatar junto a un nombre.",
         cols(rtd([{"type": "a!richTextNumberedList", "items": [{"type": "a!richTextListItem", "text": "Acotar la zona afectada"},
                                                              {"type": "a!richTextListItem", "text": "Avisar al centro de control", "nestedList": {"type": "a!richTextBulletedList", "items": ["Por radio, canal 3", "Parte en la aplicación"]}},
                                                              {"type": "a!richTextListItem", "text": "Registrar la incidencia"}]}]),
              rtd([{"type": "a!richTextImage", "image": {"type": "a!userImage", "user": "rsanchez"}}, " ", strong("Rocío Sánchez Vidal"), " ha cerrado el parte PT-2026-118", "\n",
                   {"type": "a!richTextImage", "image": {"type": "a!userImage", "user": "ivega"}}, " ", strong("Irene Vega Molina"), " ha añadido 3 fotografías"]))),
    demo("a!kpiField · a!gaugeField · a!gaugePercentage · a!gaugeFraction · a!gaugeIcon · a!progressBarField", "Cifras clave con tendencia, avance hacia un objetivo en anillo y barras de progreso.",
         [{"type": "a!columnsLayout", "showDividers": True, "marginBelow": "MORE", "columns": [{"type": "a!columnLayout", "contents": [k]} for k in [kpi("Incidencias abiertas", "wrench", 12, 15, "frente a la semana pasada", reverse=True), kpi("Tiempo medio de cierre", "clock-o", "5,2 h", None, "objetivo: 6 h"), kpi("Satisfacción", "smile-o", "4,6", 4.4, "sobre 5")]]},
          cols({"type": "a!gaugeField", "label": "Plan preventivo", "percentage": 72, "primaryText": {"type": "a!gaugePercentage"}, "secondaryText": "completado", "color": "ACCENT"},
               {"type": "a!gaugeField", "label": "Partes cerrados", "percentage": 60, "primaryText": {"type": "a!gaugeFraction", "denominator": 25}, "secondaryText": "este mes"},
               {"type": "a!gaugeField", "label": "Revisión anual", "percentage": 100, "color": "POSITIVE", "primaryText": {"type": "a!gaugeIcon", "icon": "check", "altText": "Completada"}, "secondaryText": "Completada"},
               [{"type": "a!progressBarField", "label": "Ocupación del edificio A", "percentage": 82, "color": "WARN", "style": "THICK"},
                {"type": "a!progressBarField", "label": "Tornos abiertos", "percentage": 58, "color": "ACCENT"}])]),
    demo("a!milestoneField · a!stampField · a!tagField · a!tagItem", "Dónde está un proceso, un icono o cifra destacada en un sello y estados en etiquetas de color suave (siempre con texto).",
         [milestone(["Comunicada", "Asignada", "En curso", "Resuelta", "Cerrada"], 3),
          cols({"type": "a!stampField", "icon": "building", "backgroundColor": NAVY, "contentColor": GREEN, "size": "MEDIUM", "align": "START", "tooltip": "Sede"},
               {"type": "a!stampField", "text": "B2", "backgroundColor": STATES["enCurso"]["tag"], "contentColor": NAVY, "size": "MEDIUM", "align": "START"},
               {"type": "a!tagField", "labelPosition": "COLLAPSED", "tags": [{"type": "a!tagItem", "text": "Pendiente", "backgroundColor": STATES["atencion"]["tag"]}, {"type": "a!tagItem", "text": "En curso", "backgroundColor": STATES["enCurso"]["tag"]},
                                                                           {"type": "a!tagItem", "text": "Resuelta", "backgroundColor": STATES["positivo"]["tag"]}, {"type": "a!tagItem", "text": "Rechazada", "backgroundColor": STATES["negativo"]["tag"]}]},
               marginAbove="STANDARD")]),
    demo("a!messageBanner · a!horizontalLine · a!timeDisplayField", "Avisos que el usuario debe leer antes de seguir, separadores entre bloques y horas sin fecha.",
         [{"type": "a!messageBanner", "primaryText": "Edificio A sin electricidad esta noche", "secondaryText": "De 23:00 a 05:00 por mantenimiento del cuadro general", "backgroundColor": "WARN", "highlightColor": "WARN", "icon": "exclamation-triangle", "shape": "SEMI_ROUNDED", "marginBelow": "STANDARD"},
          {"type": "a!horizontalLine", "weight": "THIN", "color": "SECONDARY"},
          cols({"type": "a!timeDisplayField", "label": "Apertura del edificio", "value": "07:00"}, {"type": "a!timeDisplayField", "label": "Cierre del edificio", "value": "22:00"}, [], marginAbove="STANDARD")]),
    demo("a!imageField · a!webImage · a!documentImage · a!userImage", "Fotografías, avatares e imágenes de documentos. Tamaños fijos o FIT; AVATAR para personas.",
         cols({"type": "a!imageField", "label": "Edificio A", "size": "MEDIUM_PLUS", "images": [{"type": "a!webImage", "source": SVG_EDIFICIO, "altText": "Vista del edificio A"}]},
              {"type": "a!imageField", "label": "Plano del aparcamiento", "size": "MEDIUM_PLUS", "images": [{"type": "a!documentImage", "document": "cons!INC_PLANO_APARCAMIENTO", "altText": "Plano del aparcamiento"}]},
              {"type": "a!imageField", "label": "Equipo de guardia", "size": "SMALL", "style": "AVATAR", "images": [{"type": "a!userImage", "user": "rsanchez"}, {"type": "a!userImage", "user": "ivega", "backgroundColor": "SECONDARY"}, {"type": "a!userImage", "user": "hromero"}]})),
    demo("a!documentViewerField", "Ver un documento sin descargarlo, con páginas y zoom. highlightedText resalta una cita (útil con respuestas de IA).",
         {"type": "a!documentViewerField", "label": "Normas del almacén", "labelPosition": "COLLAPSED", "document": "d-alm", "height": "MEDIUM", "altText": "Normas del almacén 2026", "highlightedText": "chaleco reflectante",
          "$fileName": "Normas_del_almacen_2026.pdf", "$pages": 3, "$content": [["1. Ámbito", "Estas normas se aplican a todas las personas que acceden al almacén."], ["2. Circulación", "Es obligatorio el uso de chaleco reflectante en toda la zona de carga.", "La velocidad máxima de las carretillas es de 10 km/h."], ["3. Sanciones"]]}),
    demo("a!videoField · a!webVideo", "Vídeos de formación o procedimientos, alojados fuera de Appian (YouTube, Vimeo, servidor propio).",
         {"type": "a!videoField", "label": "Formación", "labelPosition": "COLLAPSED", "videos": [
             {"type": "a!webVideo", "source": "https://www.youtube.com/embed/seguridad-almacen", "tooltip": "Seguridad en el almacén: circulación de carretillas", "$duration": "4:12"},
             {"type": "a!webVideo", "source": "https://vimeo.com/ejemplo/procedimiento-evacuacion", "tooltip": "Procedimiento de evacuación: puntos de encuentro", "$duration": "2:45"}]}),
    demo("a!webContentField", "Incrustar una página externa (un mapa, un panel de otra herramienta). 26.9: puede pedir cámara y micrófono para videollamadas o verificación de identidad.",
         {"type": "a!webContentField", "label": "Mapa de ocupación de salas", "labelPosition": "COLLAPSED", "source": "https://mapas.example.org/salas/NOR", "height": "SHORT", "showBorder": True, "altText": "Mapa de ocupación de salas de la sede Norte", "$title": "Ocupación de salas · NOR"}),
    demo("a!recordKnowledgeGraph", "26.8: cómo se relaciona un registro con otros (sede, equipo, parte, proveedor) hasta varios niveles.",
         {"type": "a!recordKnowledgeGraph", "label": "Relaciones de la incidencia", "labelPosition": "COLLAPSED", "recordType": "recordType!INC Incidencia", "recordIdentifier": 6, "relationshipLevel": 2, "height": "MEDIUM", "showMiniMap": True,
          "$root": {"recordType": "Incidencia", "name": "INC-2026-0426", "icon": "wrench"},
          "$nodes": [{"recordType": "Sede", "name": "OES", "icon": "building"}, {"recordType": "Equipo", "name": "Enfriadora 2", "icon": "cog"}, {"recordType": "Parte de trabajo", "name": "PT-2026-118", "icon": "file-text-o"},
                     {"recordType": "Proveedor", "name": "Clima Sur S.L.", "icon": "building", "parent": "PT-2026-118"}, {"recordType": "Técnico", "name": "Irene Vega", "icon": "user", "parent": "PT-2026-118"}]}),
])

# ------------------------------------------------------------------ 4. Acciones y enlaces
LINKS = [
    ("a!dynamicLink", "Cambiar algo en la misma pantalla", {"type": "a!dynamicLink", "label": "Marcar como leída", "value": True, "saveInto": "local!leida"}),
    ("a!recordLink", "Abrir un registro", {"type": "a!recordLink", "label": "INC-2026-0426", "recordType": "recordType!INC Incidencia", "identifier": 6}),
    ("a!pageLink", "Ir a otra página del site sin recargar (26.8)", {"type": "a!pageLink", "label": "Ir a Gráficos", "page": "sitePage!INC_COMPONENTES.pages.graficos"}),
    ("a!safeLink", "Abrir una web externa", {"type": "a!safeLink", "label": "example.com", "uri": "https://www.example.com", "openLinkIn": "NEW_TAB"}),
    ("a!startProcessLink", "Iniciar un proceso (26.9: mensaje al terminar)", {"type": "a!startProcessLink", "label": "Solicitar revisión", "processModel": "cons!INC_PM_REVISION", "bannerMessage": "Solicitud enviada", "$action": {"goto": "formulario"}}),
    ("a!processTaskLink", "Abrir una tarea asignada", {"type": "a!processTaskLink", "label": "Aprobar presupuesto", "task": 4521, "$action": {"goto": "formulario"}}),
    ("a!submitLink", "Enviar el formulario desde un enlace", {"type": "a!submitLink", "label": "Enviar sin adjuntos", "confirmHeader": "¿Enviar sin adjuntos?", "confirmMessage": "Podrá añadirlos después"}),
    ("a!documentDownloadLink", "Descargar un documento", {"type": "a!documentDownloadLink", "label": "Manual_de_prevencion_v4.pdf", "document": "d-prev"}),
    ("a!userRecordLink", "Ver el perfil de una persona", {"type": "a!userRecordLink", "label": "Rocío Sánchez Vidal", "user": "rsanchez"}),
    ("a!reportLink", "Abrir un informe de Tempo", {"type": "a!reportLink", "label": "Informe de nivel de servicio", "report": "cons!INC_INFORME_SERVICIO", "openLinkIn": "NEW_TAB"}),
    ("a!newsEntryLink", "Abrir una noticia del feed", {"type": "a!newsEntryLink", "label": "Nueva normativa del almacén", "entry": "e-4f2a"}),
    ("a!authorizationLink", "Autorizar el acceso a un sistema externo (OAuth)", {"type": "a!authorizationLink", "label": "Conectar con SharePoint", "connectedSystem": "cons!INC_CS_SHAREPOINT"}),
]
p_acc = page("acciones", "Acciones y enlaces", "Botones para actuar y enlaces para navegar", [
    demo("a!buttonArrayLayout · a!buttonWidget", "Botones sueltos en el contenido. Una sola acción SOLID por pantalla (con el color principal de la marca); el resto OUTLINE o GHOST; destructivas en NEGATIVE con confirmación.",
         [{"type": "a!buttonArrayLayout", "align": "START", "buttons": [
             primary("Crear incidencia", icon="plus"), secondary("Exportar", icon="download"), tool_button("Filtrar", icon="filter"),
             {"type": "a!buttonWidget", "label": "Asignar", "style": "GHOST", "color": "ACCENT", "icon": "user-plus"},
             danger("Anular", confirm=("¿Anular la incidencia?", "La incidencia pasará a «Anulada» y no se podrá editar"), icon="ban"),
             {"type": "a!buttonWidget", "label": "Ayuda", "style": "LINK", "color": "SECONDARY", "icon": "question-circle"}], "marginBelow": "MORE"},
          {"type": "a!buttonArrayLayout", "align": "START", "buttons": [
             {"type": "a!buttonWidget", "label": "Pequeño", "style": "OUTLINE", "color": "SECONDARY", "size": "SMALL"},
             {"type": "a!buttonWidget", "label": "Estándar", "style": "OUTLINE", "color": "SECONDARY"},
             {"type": "a!buttonWidget", "label": "Grande", "style": "OUTLINE", "color": "SECONDARY", "size": "LARGE"},
             {"type": "a!buttonWidget", "icon": "print", "accessibilityText": "Imprimir", "tooltip": "Imprimir", "style": "OUTLINE", "color": "SECONDARY"}]}]),
    demo("a!buttonLayout", "Botonera de formulario: principales a la derecha y secundarios a la izquierda. Vea el formulario de ejemplo.",
         {"type": "a!buttonLayout", "primaryButtons": [secondary("Abrir el formulario de ejemplo", {"goto": "formulario"})], "secondaryButtons": [{"type": "a!buttonWidget", "label": "Volver", "style": "LINK", "color": "SECONDARY", "$action": {"goto": "diseno"}}]}),
    demo("a!recordActionField · a!recordActionItem", "Acciones de un record type (crear, editar…) con su seguridad. Como tarjetas en portadas o como barra en una ficha.",
         [{"type": "a!recordActionField", "style": "CARDS", "display": "LABEL_AND_ICON", "actions": [
             {"type": "a!recordActionItem", "action": "recordType!INC Incidencia.actions.nueva", "$label": "Nueva incidencia", "$icon": "plus", "$action": {"goto": "formulario"}},
             {"type": "a!recordActionItem", "action": "recordType!INC Incidencia.actions.parte", "$label": "Nuevo parte", "$icon": "file-text-o", "$action": {"goto": "formulario"}},
             {"type": "a!recordActionItem", "action": "recordType!INC Proveedor.actions.alta", "$label": "Alta de proveedor", "$icon": "building", "$action": {"goto": "asistente"}}]},
          {"type": "a!horizontalLine", "color": "SECONDARY", "marginAbove": "STANDARD"},
          {"type": "a!recordActionField", "style": "TOOLBAR", "display": "LABEL_AND_ICON", "align": "START", "actions": [
             {"type": "a!recordActionItem", "action": "recordType!INC Incidencia.actions.editar", "identifier": 6, "$label": "Editar", "$icon": "pencil", "$action": {"goto": "formulario"}},
             {"type": "a!recordActionItem", "action": "recordType!INC Incidencia.actions.cerrar", "identifier": 6, "$label": "Cerrar incidencia", "$icon": "check", "$action": {"goto": "formulario"}}]}]),
    demo("a!linkField · los 12 tipos de enlace", "Enlaces sueltos o dentro de texto, tarjetas e imágenes. El tipo de enlace decide qué hace al pulsarlo.",
         {"type": "a!gridLayout", "label": "Tipos de enlace", "labelPosition": "COLLAPSED", "borderStyle": "LIGHT", "shadeAlternateRows": False,
          "headerCells": [{"type": "a!gridLayoutHeaderCell", "label": "Función"}, {"type": "a!gridLayoutHeaderCell", "label": "Para qué"}, {"type": "a!gridLayoutHeaderCell", "label": "Ejemplo"}],
          "columnConfigs": [{"type": "a!gridLayoutColumnConfig", "width": "MEDIUM"}, {"type": "a!gridLayoutColumnConfig", "width": "DISTRIBUTE"}, {"type": "a!gridLayoutColumnConfig", "width": "WIDE"}],
          "rows": [{"type": "a!gridRowLayout", "contents": [rtd({"type": "a!richTextItem", "text": f, "style": "SEMI_BOLD"}), rtd(muted(w)), {"type": "a!linkField", "labelPosition": "COLLAPSED", "links": [l]}]} for f, w, l in LINKS]}),
], local={"local!leida": False})

# ------------------------------------------------------------------ 5. Grids y listas
p_grid = page("grids", "Grids y listas", "Datos en tabla, tablas editables e historial de eventos", [
    demo("a!gridField · a!gridColumn", "Listas de registros con orden, búsqueda, selección y paginación. 26.9: varios componentes en una celda (a!sideBySideLayout) y varias imágenes.",
         grid("data!incidencias", None, [
             gcol("Incidencia", {"type": "a!sideBySideLayout", "alignVertical": "MIDDLE", "spacing": "DENSE", "items": [
                 {"type": "a!sideBySideItem", "width": "MINIMIZE", "item": {"type": "a!imageField", "labelPosition": "COLLAPSED", "size": "ICON_PLUS", "style": "AVATAR", "images": [{"type": "a!userImage", "user": "{fv!row.responsable}"}]}},
                 {"type": "a!sideBySideItem", "item": two_line("{fv!row.codigo}", "{fv!row.titulo}", link={"type": "a!recordLink", "recordType": "recordType!INC Incidencia", "identifier": "{fv!row.id}"})}]}, width="WIDE", sortField="codigo"),
             gcol("Sede", "{fv!row.sede}", width="NARROW", sortField="sede"),
             gcol("Estado y fecha", {"type": "a!sideBySideLayout", "alignVertical": "MIDDLE", "spacing": "DENSE", "items": [
                 {"type": "a!sideBySideItem", "width": "MINIMIZE", "item": tag("fv!row.estado", "estadoGrid")},
                 {"type": "a!sideBySideItem", "item": rtd(muted("{fv!row.fecha|date}", size="SMALL"))}]}, width="MEDIUM"),
             gcol_num("Horas", "{fv!row.horas}", width="NARROW"),
             gcol_num("Coste", "{fv!row.coste|eur}", width="NARROW_PLUS")], "No hay incidencias", page_size=5, showSearchBox=True, selectable=True, selectionStyle="ROW_HIGHLIGHT",
             selectionValue="local!selInc", selectionSaveInto="local!selInc")),
    demo("a!gridLayout · a!gridRowLayout · a!gridLayoutHeaderCell · a!gridLayoutColumnConfig", "Tabla editable para varias filas de datos del mismo tipo (líneas de un presupuesto, materiales). Añadir y quitar filas en la propia tabla.",
         [{"type": "a!gridLayout", "label": "Materiales del parte", "labelPosition": "COLLAPSED", "addRowLink": {"type": "a!dynamicLink", "label": "Añadir material", "$action": {"append": {"local!mat": {"desc": None, "cant": 1, "precio": None}}}},
           "headerCells": [{"type": "a!gridLayoutHeaderCell", "label": "Material"}, {"type": "a!gridLayoutHeaderCell", "label": "Cantidad", "align": "RIGHT"}, {"type": "a!gridLayoutHeaderCell", "label": "Precio (€)", "align": "RIGHT"}, {"type": "a!gridLayoutHeaderCell", "label": ""}],
           "columnConfigs": [{"type": "a!gridLayoutColumnConfig", "width": "DISTRIBUTE", "weight": 4}, {"type": "a!gridLayoutColumnConfig", "width": "NARROW"}, {"type": "a!gridLayoutColumnConfig", "width": "NARROW_PLUS"}, {"type": "a!gridLayoutColumnConfig", "width": "ICON"}],
           "rows": {"type": "a!forEach", "items": "local!mat", "expression": {"type": "a!gridRowLayout", "contents": [
               {"type": "a!textField", "label": "Material", "value": "fv!item.desc", "saveInto": "fv!item.desc", "placeholder": "Descripción"},
               {"type": "a!integerField", "label": "Cantidad", "value": "fv!item.cant", "saveInto": "fv!item.cant", "align": "RIGHT"},
               {"type": "a!floatingPointField", "label": "Precio", "value": "fv!item.precio", "saveInto": "fv!item.precio", "align": "RIGHT"},
               {"type": "a!richTextDisplayField", "value": [{"type": "a!richTextIcon", "icon": "times-circle", "altText": "Quitar", "caption": "Quitar", "color": "SECONDARY", "link": {"type": "a!dynamicLink", "$action": {"remove": {"local!mat": "{fv!index}"}}}, "linkStyle": "STANDALONE"}]}]}}}]),
    demo("a!eventHistoryListField · a!eventData", "Historial de lo que ha pasado en un registro (quién, qué y cuándo) a partir de su event history; con comentarios en tarjeta.",
         {"type": "a!eventHistoryListField", "labelPosition": "COLLAPSED", "eventStyle": "TIMELINE", "commentLayout": "CARD",
          "eventData": {"type": "a!eventData", "recordType": "recordType!INC Incidencia.relationships.historial", "timestamp": "recordType!INC Incidencia Evento.fields.fecha", "user": "recordType!INC Incidencia Evento.fields.usuario", "eventTypeName": "recordType!INC Incidencia Evento.fields.tipo", "comment": "recordType!INC Incidencia Evento.fields.comentario"},
          "$events": [{"event": "Parte de trabajo cerrado", "user": "Irene Vega Molina", "timestamp": "2026-09-22T13:10", "comment": "Sustituido el presostato de la enfriadora 2. Temperatura de la sala: 23 °C.", "icon": "check", "color": "POSITIVE"},
                      {"event": "Asignada a Climatización", "user": "Andrés Moreno Pastor", "timestamp": "2026-09-20T10:05", "icon": "user-plus"},
                      {"event": "Incidencia comunicada", "user": "Centro de control", "timestamp": "2026-09-20T08:40", "details": "Temperatura de 29 °C en la sala de formación C", "icon": "flag"}]}),
], local={"local!selInc": [], "local!mat": [{"desc": "Presostato de alta presión", "cant": 1, "precio": 186.4}, {"desc": "Filtro de aire F7", "cant": 4, "precio": 22.5}]})

# ------------------------------------------------------------------ 6. Gráficos
VISITAS = [{"id": k, "mes": m, "sede": s, "visitas": v} for k, (m, s, v) in enumerate(
    [(m, a, v) for m, vals in [("Abr", (5.1, 4.2, 2.1)), ("May", (5.6, 4.8, 3.0)), ("Jun", (5.9, 5.2, 3.9)), ("Jul", (6.4, 5.8, 4.6)), ("Ago", (6.6, 6.0, 4.9)), ("Sep", (6.0, 5.3, 4.0))]
     for a, v in zip(["NOR", "SUR", "EST"], vals)])]
COLORES = {"type": "a!colorSchemeCustom", "colors": CHART[:6]}  # series de gráficos de la marca, en orden
p_graf = page("graficos", "Gráficos", "Comparar, ver tendencias y proporciones. Siempre con título que diga qué se compara", [
    demo("a!columnChartField · a!columnChartConfig · a!grouping · a!measure · a!colorSchemeCustom", "Comparar cantidades entre categorías. Con datos de un record type, Appian agrupa y cuenta. Apilado con etiquetas de datos: 26.8 ajusta su color al del segmento.",
         chart_table("local!tablaColumnas", {"type": "a!columnChartField", "label": "Incidencias por área y estado", "data": "data!incidencias", "stacking": "NORMAL", "showDataLabels": True, "height": "MEDIUM", "colorScheme": state_chart_colors(ESTADOS_INC, ORDEN_INC), "allowLegendFiltering": True, "$series": ORDEN_INC,
          "config": {"type": "a!columnChartConfig", "primaryGrouping": {"type": "a!grouping", "field": "recordType!INC Incidencia.fields.area", "alias": "area"},
                     "secondaryGrouping": {"type": "a!grouping", "field": "recordType!INC Incidencia.fields.estado", "alias": "estado"},
                     "measures": [{"type": "a!measure", "function": "COUNT", "field": "recordType!INC Incidencia.fields.id", "alias": "total", "label": "Incidencias"}]}}, "Área")),
    demo("a!barChartField · a!barChartConfig · a!chartReferenceLine", "Comparar categorías con etiquetas largas (barras horizontales). La línea de referencia marca un objetivo o un umbral.",
         chart_table("local!tablaBarras", {"type": "a!barChartField", "label": "Coste de reparación por sede (€)", "data": "data!incidencias", "showDataLabels": True, "height": "SHORT", "colorScheme": COLORES,
          "config": {"type": "a!barChartConfig", "primaryGrouping": {"type": "a!grouping", "field": "recordType!INC Incidencia.fields.sede", "alias": "sede"},
                     "measures": [{"type": "a!measure", "function": "SUM", "field": "recordType!INC Incidencia.fields.coste", "alias": "coste", "label": "Coste", "formatValue": "EURO"}]},
          "referenceLines": [{"type": "a!chartReferenceLine", "label": "Presupuesto mensual", "value": 2500, "color": "RED", "style": "DASH"}]}, "Sede", fmt="eur")),
    demo("a!lineChartField · a!chartSeries · a!lineChartConfig", "Tendencias en el tiempo. Con categorías y series fijas (a!chartSeries) o con datos y a!lineChartConfig.",
         cols(chart_table("local!tablaPlazo", {"type": "a!lineChartField", "label": "Incidencias resueltas en plazo (%)", "categories": ["Abr", "May", "Jun", "Jul", "Ago", "Sep"], "yAxisMin": 80, "yAxisMax": 100, "height": "SHORT",
               "series": [{"type": "a!chartSeries", "label": "NOR", "data": [91.2, 90.4, 88.1, 86.9, 87.5, 92.3], "color": CHART[0]}, {"type": "a!chartSeries", "label": "SUR", "data": [89.8, 89.1, 87.4, 85.2, 86.0, 90.7], "color": CHART[1]}],
               "referenceLines": [{"type": "a!chartReferenceLine", "label": "Objetivo 90 %", "value": 90, "color": "GOLD", "style": "SHORTDASH"}]}, "Mes"),
              chart_table("local!tablaVisitas", {"type": "a!lineChartField", "label": "Visitas por mes (miles)", "data": "data!visitas", "height": "SHORT", "colorScheme": COLORES,
               "config": {"type": "a!lineChartConfig", "primaryGrouping": {"type": "a!grouping", "field": "mes", "alias": "mes"}, "secondaryGrouping": {"type": "a!grouping", "field": "sede", "alias": "sede"},
                          "measures": [{"type": "a!measure", "function": "SUM", "field": "visitas", "alias": "visitas", "label": "Visitas"}]}}, "Mes", value_labels=["NOR", "SUR", "EST"]))),
    demo("a!areaChartField · a!areaChartConfig · a!pieChartField · a!pieChartConfig", "Volumen acumulado en el tiempo (área) y proporción de un total con pocas categorías (tarta o anillo, máximo 5 porciones).",
         cols(chart_table("local!tablaArea", {"type": "a!areaChartField", "label": "Visitas acumuladas por sede (miles)", "data": "data!visitas", "stacking": "NORMAL", "height": "SHORT", "colorScheme": COLORES,
               "config": {"type": "a!areaChartConfig", "primaryGrouping": {"type": "a!grouping", "field": "mes", "alias": "mes"}, "secondaryGrouping": {"type": "a!grouping", "field": "sede", "alias": "sede"},
                          "measures": [{"type": "a!measure", "function": "SUM", "field": "visitas", "alias": "visitas", "label": "Visitas"}]}}, "Mes", value_labels=["NOR", "SUR", "EST"]),
              chart_table("local!tablaAnillo", {"type": "a!pieChartField", "label": "Incidencias por estado", "data": "data!incidencias", "style": "DONUT", "seriesLabelStyle": "LEGEND", "showDataLabels": True, "height": "SHORT", "colorScheme": state_chart_colors(ESTADOS_INC, ORDEN_INC), "$categories": ORDEN_INC,
               "config": {"type": "a!pieChartConfig", "primaryGrouping": {"type": "a!grouping", "field": "recordType!INC Incidencia.fields.estado", "alias": "estado"},
                          "measures": [{"type": "a!measure", "function": "COUNT", "field": "recordType!INC Incidencia.fields.id", "alias": "total"}]}}, "Estado", value_labels=["Incidencias"]))),
    demo("a!scatterChartField", "Relación entre dos medidas de cada elemento (horas de trabajo frente a coste de cada incidencia) para detectar casos fuera de lo normal.",
         chart_table("local!tablaDispersion", {"type": "a!scatterChartField", "label": "Horas frente a coste por incidencia", "data": "data!incidencias", "height": "SHORT", "colorScheme": COLORES, "xAxisTitle": "Horas de trabajo", "yAxisTitle": "Coste (€)",
          "primaryGrouping": {"type": "a!grouping", "field": "recordType!INC Incidencia.fields.codigo", "alias": "codigo"},
          "secondaryGrouping": {"type": "a!grouping", "field": "recordType!INC Incidencia.fields.area", "alias": "area"},
          "xAxisMeasure": {"type": "a!measure", "function": "SUM", "field": "recordType!INC Incidencia.fields.horas", "alias": "horas"},
          "yAxisMeasure": {"type": "a!measure", "function": "SUM", "field": "recordType!INC Incidencia.fields.coste", "alias": "coste"}},
                     table=grid("data!incidencias", None, [gcol("Incidencia", two_line("{fv!row.codigo}", link={"type": "a!recordLink", "recordType": "recordType!INC Incidencia", "identifier": "{fv!row.id}"})), gcol("Área", "{fv!row.area}"), gcol_num("Horas", "{fv!row.horas|num}"), gcol_num("Coste", "{fv!row.coste|eur}")],
                                "No hay incidencias", page_size=10))),
], local={"local!tablaColumnas": False, "local!tablaBarras": False, "local!tablaPlazo": False, "local!tablaVisitas": False, "local!tablaArea": False,
          "local!tablaAnillo": False, "local!tablaDispersion": False})

# ------------------------------------------------------------------ 7. IA y chat
p_ia = page("ia", "IA y chat", "Conversar con agentes, con los datos, con un registro o con documentos", [
    demo("a!agentChatField", "26.6: conversación con un agente de IA que usa herramientas (buscar, consultar, preparar borradores). 26.7: forma, borde y botón Detener.",
         ai_agent_chat("Asistente de operaciones", "agent!INC_OPERACIONES", "Puedo buscar incidencias, resumir su historial y preparar partes de trabajo.", height="MEDIUM", shape="SEMI_ROUNDED", showBorder=True, showSessionPicker=False,
                       **{"$messages": [{"role": "USER", "text": "¿Qué incidencias de climatización siguen abiertas?"}, {"role": "TOOL", "tool": "Buscar incidencias", "text": "1 resultado"},
                                        {"role": "ASSISTANT", "text": "Hay **1 incidencia abierta**: la INC-2026-0426, avería de climatización en la sala de formación C de la sede Oeste, asignada a Irene Vega."}],
                          "$replies": ["He preparado el parte de trabajo de la INC-2026-0426. Revíselo antes de guardarlo."]})),
    demo("a!chatField · a!chatMessage", "Chat que construye usted mismo (mensajes guardados en variables o en un record type), con mensajes de texto o de componentes.",
         {"type": "a!chatField", "title": "Consultas al centro de control", "height": "SHORT_PLUS", "showBorder": True, "shape": "SEMI_ROUNDED", "placeholder": "Escriba su consulta",
          "messages": [{"type": "a!chatMessage", "role": "USER", "messageContent": "¿Estará abierto el edificio A esta noche?"},
                       {"type": "a!chatMessage", "role": "ASSISTANT", "messageContent": "Hasta las 23:00. Después se corta la electricidad por mantenimiento del cuadro general hasta las 05:00."}],
          "$replies": ["Consulto el estado del edificio y le respondo en unos minutos."]}),
    demo("a!dataFabricChatField · a!suggestedQuestion", "Preguntar a los datos de varios record types en lenguaje natural. Hasta 3 preguntas sugeridas para empezar.",
         ai_data_chat("Pregunte a sus datos", ["recordType!INC Incidencia"], [("¿Cuántas incidencias hay pendientes por sede?", "list", "ACCENT"), ("¿Qué área tiene más coste este mes?", "bar-chart", "ACCENT")],
                      **{"$replies": ["Hay **3 incidencias pendientes**: 1 en NOR, 1 en SUR y 1 en EST."], "$uxIgnore": "Catálogo: se muestra junto a los demás chats; en una pantalla real va en un panel lateral (ai_side_pane)"})),
    demo("a!recordsChatField · a!documentsChatField", "Preguntar por un registro concreto (su historial, sus relaciones) o por el contenido de uno o varios documentos.",
         cols(ai_records_chat("Pregunte por la incidencia", "recordType!INC Incidencia", 6, "Hola. Puedo responder preguntas sobre la INC-2026-0426.", ["¿Qué se ha hecho hasta ahora?", "¿Quién es el técnico?"],
                              **{"$replies": ["Se sustituyó el presostato de la enfriadora 2 y la sala está a 23 °C."]}),
              {"type": "a!documentsChatField", "label": "Pregunte a las normas del almacén", "documents": ["d-alm", "d-evac"], "height": "MEDIUM"})),
])

# ficha de registro (destino de los a!recordLink): vista de registro con cabecera de color
scr_rec = {"id": "incidencia", "title": "{rv!record.codigo} · {rv!record.titulo}", "type": "record", "pattern": "P02", "recordType": "INC Incidencia", "req": ["C1"],
    "breadcrumb": {"label": "Grids y listas", "goto": "grids"}, "headerBackgroundColor": NAVY,
    "views": [{"id": "resumen", "label": "Resumen", "interface": {"type": "a!headerContentLayout", "backgroundColor": BG, "contents": [
        key_facts([("Estado", tag("rv!record.estado", "estado")), ("Prioridad", "{rv!record.prioridad}"), ("Sede", "{rv!record.sede}"), ("Área", "{rv!record.area}")],
                  extra=milestone(["Pendiente", "En curso", "Cerrada"], "{rv!record.estado|map:estadoPaso}")),
        section_card("Datos de la incidencia", field_summary([("Comunicada", "{rv!record.fecha|date}"), ("Responsable", "{rv!record.responsable|map:usuarios}"), ("Horas", "{rv!record.horas}"), ("Coste", "{rv!record.coste|eur}")], columns=2))]}}]}

pages = [p_dis, p_ent, p_vis, p_acc, p_grid, p_graf, p_nav, p_ia]
extra = [scr_form, scr_wiz, scr_pane, scr_rec, dlg_full, dlg_img]
spec = {"app": {"name": "Componentes de Appian 26.9", "language": "es", "today": "2026-09-26", "appianVersion": "26.9",
                "source": "Catálogo SAIL de Appian 26.9 (docs.appian.com/suite/help/26.9/SAIL_Components.html) con datos ficticios"},
        "site": {"displayName": "Componentes Appian 26.9", "home": pages[0]["id"], "user": {"name": "Lucía Fernández Gil"},
                 "pages": [{"title": tt, "icon": ic, "screen": p["id"], **({"includes": ["formulario", "asistente", "paneles"]} if p is p_dis else {})}
                           for p, tt, ic in zip(pages, ["Diseño", "Entradas", "Visualización", "Acciones", "Grids", "Gráficos", "Selectores", "IA"],
                                                ["th-large", "keyboard-o", "eye", "hand-pointer-o", "table", "bar-chart", "sitemap", "magic"])]},
        "requirements": [{"id": "C1", "title": "Catálogo completo de componentes de interfaz de Appian 26.9"}],
        "users": [{"id": i, "name": n, "title": t, "supervisor": s, "groups": g} for i, n, t, s, g in USERS],
        "groups": [{"id": i, "name": n, "parent": p, "description": d} for i, n, p, d in GROUPS],
        "documents": [{"id": i, "name": n, "folder": f, "type": ty, "size": sz, "modified": m} for i, n, f, ty, sz, m in DOCS],
        "maps": {"usuarios": {i: n for i, n, *_ in USERS}, "estado": ESTADO, "estadoGrid": ESTADO_G, "estadoPaso": {"Pendiente": 1, "En curso": 2, "Cerrada": 3}, **AI_MAPS},
        "data": {"incidencias": {"recordType": "INC Incidencia", "rows": INC_ROWS}, "visitas": {"recordType": "INC Visita", "rows": VISITAS}},
        "screens": pages + extra,
        "captures": [{"name": f"{k + 1:02d}-{p['id']}", "screen": p["id"]} for k, p in enumerate(pages + extra)]}
Path(sys.argv[1] if len(sys.argv) > 1 else "app.json").write_text(json.dumps(clean(spec), ensure_ascii=False, indent=1), encoding="utf-8")
print("ok")
