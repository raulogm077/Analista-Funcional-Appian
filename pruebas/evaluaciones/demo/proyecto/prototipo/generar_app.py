"""Prototipo del préstamo de equipos audiovisuales: las seis pantallas del funcional, hechas con los helpers del kit.

Uso:
  python3 generar_app.py <app.json> [--kit <carpeta de appian-prototipos>] [--proyecto <p>]

El spec sale del análisis del proyecto (<p>/analisis/funcional.md y tecnico.md, leídos con modelo.py del analista): el
`ref` y el `req` de cada pantalla, los requisitos, las preguntas abiertas, los estados, las categorías y la versión de
Appian. <p> es la carpeta de encima de esta (el script vive en <p>/prototipo/). El kit se busca en --kit, en
$KIT_PROTOTIPOS, en $PLUGIN_A_PROBAR/skills/appian-prototipos y en el repositorio del plugin, si el script está en él.
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
AQUI = Path(__file__).resolve().parent
ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("salida", nargs="?", default="app.json")
ap.add_argument("--kit")
ap.add_argument("--proyecto", default=str(AQUI.parent))
a = ap.parse_args()
candidatos = [a.kit, os.environ.get("KIT_PROTOTIPOS"),
              os.environ.get("PLUGIN_A_PROBAR") and str(Path(os.environ["PLUGIN_A_PROBAR"]) / "skills" / "appian-prototipos"),
              str(AQUI.parents[4] / "skills" / "appian-prototipos") if len(AQUI.parents) > 4 else None]
KIT = next((Path(c) for c in candidatos if c and (Path(c) / "scripts" / "sail_helpers.py").is_file()), None)
if KIT is None:
    sys.exit("No encuentro el kit de prototipos: pásalo con --kit <carpeta de appian-prototipos>")
sys.path.insert(0, str(KIT / "scripts"))
sys.path.insert(0, str(KIT.parent / "appian-functional-analyst" / "scripts"))
from sail_helpers import *  # noqa: E402,F401,F403
import modelo  # noqa: E402

FUN = modelo.Proyecto(Path(a.proyecto))
if "F" not in FUN.docs:
    sys.exit(f"No encuentro funcional.md en {FUN.analisis}")


# ------------------------------------------------------------------ del análisis
def ref(pan):
    """«PAN-02 · Solicitar préstamo»: el ID y el título de la ficha, literales."""
    return f"{pan} · {FUN.piezas[pan].titulo}"


def req(pan):
    """Las historias de la línea «Historias:» de la ficha y los pasos cuya pantalla es esa."""
    linea = re.search(r"^Historias:(.*)$", FUN.texto(pan), re.M)
    historias = sorted(modelo.ids_en(linea.group(1)) if linea else (), key=modelo.numero)
    pasos = [p.id for p in sorted(FUN.vigentes("ACT"), key=lambda p: modelo.numero(p.id))
             if pan in modelo.ids_en(FUN.campos(p.id).get("pantalla", ""))]
    return historias + pasos


def requisitos(screens):
    ids = {i for s in screens for i in s["req"]}
    orden = sorted(ids, key=lambda i: (modelo.tipo_de(i) != "HU", modelo.numero(i)))
    return [{"id": i, "title": FUN.piezas[i].titulo} for i in orden]


def preguntas():
    out = []
    for p in sorted(FUN.vigentes("PC"), key=lambda p: modelo.numero(p.id)):
        cab = [modelo.normaliza(c) for c in modelo.celdas(p.cabecera)]
        fila = dict(zip(cab, (modelo.sin_comentarios(c).strip() for c in modelo.celdas(FUN.lineas("F")[p.ini]))))
        opciones = fila.get("opciones", "").strip(" —-")
        out.append({"id": p.id, "text": fila.get("pregunta", p.titulo) + (f" ({opciones})" if opciones else "")})
    return out


def tabla(doc, seccion, primera):
    for _, cab, filas in FUN.tablas(doc, seccion):
        if cab and modelo.normaliza(cab[0]) == modelo.normaliza(primera):
            return [[modelo.sin_comentarios(c).strip() for c in f] for f in filas]
    return []


def valor(filas, dato):
    return next((f[1] for f in filas if modelo.normaliza(f[0]) == modelo.normaliza(dato)), "")


ESTADOS = [f[0] for f in tabla("F", "3", "Estado")]
CATEGORIAS = [x.strip() for x in valor(tabla("F", "6", "Lista"), "Categoría").split(",") if x.strip()]
VERSION = re.search(r"\d+\.\d+", valor(tabla("T", "0", "Dato"), "Versión de Appian"))
NOMBRE = FUN.lineas("F")[0].lstrip("# ").split(" — ")[0]
V = FUN.version("F")

# ------------------------------------------------------------------ datos de ejemplo (ficticios)
EQ, PR = "PRE Equipo", "PRE Prestamo"
FE = lambda f: f"recordType!{EQ}.fields.{f}"
FP = lambda f: f"recordType!{PR}.fields.{f}"
YO = "Marta Ibáñez Gil"                                       # perfil Solicitante, del área de Formación
_equipos = [  # (código, nombre, categoría, estado, ubicación, última revisión)
    ("PRY-01", "Proyector Lumia X200", "Proyector", "Prestado", "Almacén, estante A1", "2026-03-10"),
    ("PRY-02", "Proyector Lumia X200", "Proyector", "Disponible", "Almacén, estante A1", "2026-03-10"),
    ("PRY-03", "Proyector portátil Mini P5", "Proyector", "En reparación", "Taller", "2025-11-04"),
    ("CAM-01", "Cámara de vídeo Vista HD4", "Cámara", "Disponible", "Almacén, armario B", "2026-05-22"),
    ("CAM-02", "Cámara de vídeo Vista HD4", "Cámara", "Prestado", "Almacén, armario B", "2026-05-22"),
    ("MIC-01", "Micrófono inalámbrico Eco 10", "Micrófono", "Disponible", "Almacén, cajón C2", "2026-01-15"),
    ("MIC-02", "Micrófono inalámbrico Eco 10", "Micrófono", "Disponible", "Almacén, cajón C2", "2026-01-15"),
    ("MIC-03", "Micrófono de solapa Eco S", "Micrófono", "En reparación", "Taller", "2025-09-30"),
    ("POR-01", "Portátil Nova 14", "Portátil", "Prestado", "Almacén, armario D", "2026-06-02"),
    ("POR-02", "Portátil Nova 14", "Portátil", "Disponible", "Almacén, armario D", "2026-06-02"),
    ("PNT-01", "Pantalla enrollable de 2 m", "Pantalla", "Disponible", "Almacén, pared norte", "2025-12-12"),
    ("PNT-02", "Pantalla de trípode de 1,8 m", "Pantalla", "Disponible", "Almacén, pared norte", "2025-12-12"),
]
equipos = [{"id": i, "codigo": c, "nombre": n, "categoria": cat, "estado": est, "ubicacion": u, "ultimaRevision": rev}
           for i, (c, n, cat, est, u, rev) in enumerate(_equipos, start=1)]
_prestamos = [  # (equipo, solicitante, área, responsable, inicio, devolución, motivo, lugar, estado, comentario, al devolver, observaciones)
    (1, YO, "Formación", "Ricardo Peña Luna", "2026-10-05", "2026-10-07", "Curso de bienvenida", "Aula 3", "En préstamo", None, None, None),
    (4, YO, "Formación", "Ricardo Peña Luna", "2026-10-14", "2026-10-15", "Grabación de una sesión del curso", "Aula magna", "Solicitado", None, None, None),
    (6, YO, "Formación", "Ricardo Peña Luna", "2026-09-21", "2026-09-22", "Jornada de acogida", "Salón de actos", "Devuelto", "De acuerdo", "Correcto", None),
    (5, YO, "Formación", "Ricardo Peña Luna", "2026-09-28", "2026-09-30", "Grabación externa", "Sede de otra organización", "Rechazado", "Pídela a través del área de Comunicación", None, None),
    (10, YO, "Formación", "Ricardo Peña Luna", "2026-10-09", "2026-10-13", "Taller de herramientas", "Aula 2", "Aprobado", "De acuerdo", None, None),
    (2, "Pablo Ruiz Navas", "Comunicación", "Inés Mora Cano", "2026-10-08", "2026-10-09", "Rueda de prensa", "Sala de prensa", "Aprobado", None, None, None),
    (5, "Pablo Ruiz Navas", "Comunicación", "Inés Mora Cano", "2026-10-01", "2026-10-10", "Vídeo institucional", "Edificio principal", "En préstamo", "Adelante", None, None),
    (8, "Pablo Ruiz Navas", "Comunicación", "Inés Mora Cano", "2026-09-14", "2026-09-16", "Entrevista", "Plató", "Devuelto", None, "Con daños", "El cable del receptor está roto."),
    (9, "Lorena Vidal Sanz", "Informática", "Óscar Gil Ferrer", "2026-10-02", "2026-10-09", "Pruebas de una aplicación", "Planta 2", "En préstamo", None, None, None),
    (11, "Lorena Vidal Sanz", "Informática", "Óscar Gil Ferrer", "2026-10-15", "2026-10-15", "Presentación del proyecto", "Sala de juntas", "Solicitado", None, None, None),
    (3, "Hugo Serrano Ortiz", "Recursos Humanos", "Elena Ramos Díaz", "2026-09-07", "2026-09-11", "Proceso de selección", "Sala 1", "Devuelto", None, "Con daños", "La lente tiene un golpe."),
    (12, "Hugo Serrano Ortiz", "Recursos Humanos", "Elena Ramos Díaz", "2026-10-20", "2026-10-21", "Charla de prevención", "Salón de actos", "Solicitado", None, None, None),
    (7, "Hugo Serrano Ortiz", "Recursos Humanos", "Elena Ramos Díaz", "2026-10-06", "2026-10-06", "Reunión de equipo", "Sala 4", "Rechazado", "El micrófono de la sala es suficiente", None, None),
]
prestamos = []
for i, (eq, sol, area, resp, ini, dev, mot, lug, est, com, al, obs) in enumerate(_prestamos, start=1):
    prestamos.append({"id": i, "numero": f"PRE-2026-{i:04d}", "equipoId": eq, "equipo": equipos[eq - 1]["nombre"],
                      "codigoEquipo": equipos[eq - 1]["codigo"], "solicitante": sol, "area": area, "responsable": resp,
                      "fechaInicio": ini, "fechaDevolucion": dev, "motivo": mot, "lugarUso": lug, "estado": est,
                      "comentario": com, "estadoDevolucion": al, "observaciones": obs})
mal = sorted({p["estado"] for p in prestamos} - set(ESTADOS)) + sorted({e["categoria"] for e in equipos} - set(CATEGORIAS))
if mal:
    sys.exit(f"Los datos de ejemplo usan valores que no están en el funcional: {', '.join(mal)}")
COLOR_PRESTAMO = {"Solicitado": "atencion", "Aprobado": "enCurso", "Rechazado": "negativo", "En préstamo": "enCurso",
                  "Devuelto": "neutral"}
COLOR_EQUIPO = {"Disponible": "positivo", "Prestado": "enCurso", "En reparación": "atencion"}
DISPONIBLES = [e["nombre"] + " (" + e["codigo"] + ")" for e in equipos if e["estado"] == "Disponible"]

# ------------------------------------------------------------------ PAN-01 Catálogo de equipos (P01)
catalogo = {"id": "catalogo", "title": "Catálogo de equipos", "type": "page", "pattern": "P01", "ref": ref("PAN-01"), "req": req("PAN-01"),
            "interface": {"type": "a!headerContentLayout", "backgroundColor": BG, "contents": [
                page_header("Catálogo de equipos", "Los equipos del almacén de medios y si se pueden pedir",
                            [primary("Solicitar préstamo", {"goto": "solicitar"}, "plus")]),
                content_card([grid(f"recordType!{EQ}", None, [
                    gcol("Equipo", two_line("{fv!row.nombre}", "{fv!row.codigo}", {"type": "a!recordLink", "recordType": f"recordType!{EQ}", "identifier": "{fv!row.id}"}), sortField=FE("nombre"), width="4X"),
                    gcol("Categoría", "{fv!row.categoria}", sortField=FE("categoria"), width="2X"),
                    gcol("Estado", tag("fv!row.estado", "equipoColorGrid"), sortField=FE("estado"), width="NARROW_PLUS"),
                ], "No hay equipos que cumplan los filtros", page_size=25, showSearchBox=True,
                    userFilters=[FE("categoria").replace(".fields.", ".filters."), FE("estado").replace(".fields.", ".filters.")],
                    initialSorts=[{"type": "a!sortInfo", "field": FE("nombre"), "ascending": True}])]),
            ]}}

# ------------------------------------------------------------------ PAN-02 Solicitar préstamo (P03)
solicitar = {"id": "solicitar", "title": "Solicitar préstamo", "type": "form", "pattern": "P03", "ref": ref("PAN-02"), "req": req("PAN-02"),
             "local": {"local!p": {"equipo": None, "inicio": None, "devolucion": None, "motivo": None, "lugar": None}},
             "interface": {"type": "a!formLayout", "titleBar": "Solicitar préstamo", "contentsWidth": "NARROW", "backgroundColor": "WHITE", "showButtonDivider": True,
                           "contents": [
                               {"type": "a!sectionLayout", "label": "Equipo y fechas", "labelSize": "MEDIUM", "labelHeadingTag": "H2", "labelColor": "STANDARD", "contents": [
                                   dd("Equipo", DISPONIBLES, "local!p.equipo", required=True, requiredMessage="Indique el equipo y las fechas",
                                      instructions="Solo los equipos disponibles"),
                                   cols(date("Fecha de inicio", "local!p.inicio", required=True, requiredMessage="Indique el equipo y las fechas"),
                                        date("Fecha de devolución", "local!p.devolucion", required=True, requiredMessage="Indique el equipo y las fechas",
                                             instructions="Como mucho 15 días después del inicio")),
                               ]},
                               {"type": "a!sectionLayout", "label": "Uso", "labelSize": "MEDIUM", "labelHeadingTag": "H2", "labelColor": "STANDARD", "marginBelow": "NONE", "contents": [
                                   par("Motivo", "local!p.motivo", required=True, characterLimit=500, instructions="Para qué necesita el equipo"),
                                   txt("Lugar de uso", "local!p.lugar", required=True, characterLimit=200),
                               ]},
                           ],
                           "buttons": bl(primary("Enviar solicitud", {"goto": "mis-prestamos"}, submit=True), [secondary("Cancelar", {"goto": "catalogo"})])}}

# ------------------------------------------------------------------ PAN-03 Mis préstamos (P01)
mis_prestamos = {"id": "mis-prestamos", "title": "Mis préstamos", "type": "page", "pattern": "P01", "ref": ref("PAN-03"), "req": req("PAN-03"),
                 "interface": {"type": "a!headerContentLayout", "backgroundColor": BG, "contents": [
                     page_header("Mis préstamos", "Los equipos que ha pedido y en qué punto está cada préstamo"),
                     content_card([grid(f"recordType!{PR}", f'fv!row.solicitante = "{YO}"', [
                         gcol("Préstamo", two_line("{fv!row.numero}", "{fv!row.equipo}"), sortField=FP("numero"), width="4X"),
                         gcol("Desde", "{fv!row.fechaInicio|date}", sortField=FP("fechaInicio"), width="NARROW_PLUS"),
                         gcol("Hasta", "{fv!row.fechaDevolucion|date}", sortField=FP("fechaDevolucion"), width="NARROW_PLUS"),
                         gcol("Estado", tag("fv!row.estado", "prestamoColorGrid"), sortField=FP("estado"), width="NARROW_PLUS"),
                     ], "Todavía no ha pedido ningún préstamo", page_size=25,
                         initialSorts=[{"type": "a!sortInfo", "field": FP("fechaInicio"), "ascending": False}],
                         **{"$note": "RB-01: cada solicitante ve solo los suyos; en Appian, seguridad de registro, no el filtro."})]),
                 ]}}

# ------------------------------------------------------------------ PAN-04 Aprobar préstamo (P05)
aprobar = {"id": "aprobar", "title": "Aprobar préstamo", "type": "form", "pattern": "P05", "recordType": PR, "ref": ref("PAN-04"), "req": req("PAN-04"),
           "local": {"local!decision": None, "local!comentario": None},
           "interface": {"type": "a!formLayout", "contentsWidth": "WIDE", "backgroundColor": "WHITE", "showButtonDivider": True, "isButtonFooterFixed": True,
                         "titleBar": {"type": "a!headerTemplateSimple", "title": "Aprobar préstamo {rv!record.numero}", "secondaryText": "Tarea del responsable de área",
                                      "stampIcon": "check-square-o", "stampColor": "ACCENT"},
                         "contents": [
                             {"type": "a!columnsLayout", "spacing": "SPARSE", "columns": [
                                 {"type": "a!columnLayout", "width": "3X", "contents": [
                                     {"type": "a!sectionLayout", "label": "Datos del préstamo", "labelSize": "MEDIUM", "labelHeadingTag": "H2", "labelColor": "STANDARD", "contents": field_summary(
                                         [("Equipo", "{rv!record.equipo}", True), ("Solicitante", "{rv!record.solicitante}"), ("Área", "{rv!record.area}"),
                                          ("Fecha de inicio", "{rv!record.fechaInicio|date}"), ("Fecha de devolución", "{rv!record.fechaDevolucion|date}"),
                                          ("Lugar de uso", "{rv!record.lugarUso}"), ("Motivo", "{rv!record.motivo}", True)], columns=3)}]},
                                 {"type": "a!columnLayout", "width": "2X", "contents": [{"type": "a!cardLayout", "showBorder": True, "shape": "SEMI_ROUNDED", "padding": "MORE", "borderColor": "STANDARD", "contents": [
                                     {"type": "a!sectionLayout", "label": "Decisión", "labelSize": "MEDIUM", "labelHeadingTag": "H2", "labelColor": "STANDARD", "contents": [
                                         choice_cards("Resultado", [
                                             {"id": "APROBAR", "texto": "Aprobar", "detalle": "El almacén entregará el equipo", "icono": "check-circle", "color": "POSITIVE"},
                                             {"id": "RECHAZAR", "texto": "Rechazar", "detalle": "El solicitante recibe el comentario", "icono": "times-circle", "color": "NEGATIVE"}],
                                             "local!decision", labelPosition="COLLAPSED", required=True, requiredMessage="Indique el resultado"),
                                         par("Comentario", "local!comentario", characterLimit=500, instructions="Le llega al solicitante")]}]}]},
                             ]},
                         ],
                         "buttons": bl(primary("Enviar decisión", {"goto": "catalogo"}, submit=True), [secondary("Cancelar", {"back": True})])}}

# ------------------------------------------------------------------ PAN-05 Entregar y recoger equipo (P03, formulario de tarea)
entregar = {"id": "entregar", "title": "Entregar y recoger equipo", "type": "form", "pattern": "P03", "recordType": PR, "ref": ref("PAN-05"), "req": req("PAN-05"),
            "$uxIgnore": "Tarea del almacén: llega por su bandeja de tareas, como las de aprobación",
            "local": {"local!entregado": None, "local!vuelve": "Correcto", "local!observaciones": None},
            "interface": {"type": "a!formLayout", "titleBar": "Préstamo {rv!record.numero}", "contentsWidth": "NARROW", "backgroundColor": "WHITE", "showButtonDivider": True,
                          "contents": [
                              {"type": "a!sectionLayout", "label": "Datos del préstamo", "labelSize": "MEDIUM", "labelHeadingTag": "H2", "labelColor": "STANDARD", "contents": field_summary(
                                  [("Equipo", "{rv!record.equipo}", True), ("Solicitante", "{rv!record.solicitante}"),
                                   ("Fecha de inicio", "{rv!record.fechaInicio|date}"), ("Fecha de devolución", "{rv!record.fechaDevolucion|date}")], columns=2)},
                              {"type": "a!sectionLayout", "label": "Entrega", "labelSize": "MEDIUM", "labelHeadingTag": "H2", "labelColor": "STANDARD",
                               "showWhen": 'rv!record.estado = "Aprobado"', "contents": [
                                   {"type": "a!checkboxField", "label": "Entrega", "labelPosition": "COLLAPSED", "choiceLabels": ["Entrego el equipo al solicitante"],
                                    "choiceValues": [True], "value": "local!entregado", "saveInto": "local!entregado", "required": True}]},
                              {"type": "a!sectionLayout", "label": "Recogida", "labelSize": "MEDIUM", "labelHeadingTag": "H2", "labelColor": "STANDARD", "marginBelow": "NONE",
                               "showWhen": 'rv!record.estado = "En préstamo"', "contents": [
                                   {"type": "a!radioButtonField", "label": "Cómo vuelve el equipo", "choiceLabels": ["Correcto", "Con daños"], "choiceValues": ["Correcto", "Con daños"],
                                    "value": "local!vuelve", "saveInto": "local!vuelve", "required": True, "choiceLayout": "COMPACT"},
                                   par("Observaciones", "local!observaciones", characterLimit=1000, required='local!vuelve = "Con daños"',
                                       instructions="Obligatorias si vuelve con daños")]},
                          ],
                          "buttons": bl(primary("Guardar", {"goto": "catalogo"}, submit=True), [secondary("Cancelar", {"back": True})])}}

# ------------------------------------------------------------------ PAN-06 Ficha del equipo (P02)
equipo = {"id": "equipo", "title": "{rv!record.nombre}", "type": "record", "pattern": "P02", "recordType": EQ, "ref": ref("PAN-06"), "req": req("PAN-06"),
          "breadcrumb": {"label": "Catálogo de equipos", "goto": "catalogo"}, "headerBackgroundColor": NAVY,
          "views": [
              {"id": "resumen", "label": "Resumen", "interface": {"type": "a!headerContentLayout", "backgroundColor": BG, "contents": [
                  key_facts([("Estado", tag("rv!record.estado", "equipoColor")), ("Categoría", "{rv!record.categoria}"), ("Código", "{rv!record.codigo}")]),
                  section_card("Datos del equipo", field_summary([("Nombre", "{rv!record.nombre}", True), ("Ubicación", "{rv!record.ubicacion}")], columns=2))]}},
              {"id": "prestamos", "label": "Préstamos", "interface": {"type": "a!headerContentLayout", "backgroundColor": BG, "contents": [
                  content_card([grid(f"recordType!{PR}", "fv!row.equipoId = rv!record.id", [
                      gcol("Préstamo", two_line("{fv!row.numero}", "{fv!row.solicitante}"), width="3X"),
                      gcol("Fecha de inicio", "{fv!row.fechaInicio|date}", width="NARROW_PLUS"),
                      gcol("Fecha de devolución", "{fv!row.fechaDevolucion|date}", width="NARROW_PLUS"),
                      gcol("Estado", tag("fv!row.estado", "prestamoColorGrid"), width="NARROW_PLUS"),
                  ], "Este equipo no se ha prestado nunca", initialSorts=[{"type": "a!sortInfo", "field": FP("fechaInicio"), "ascending": False}])])]}},
          ]}

screens = [catalogo, solicitar, mis_prestamos, aprobar, entregar, equipo]
app = {"name": NOMBRE, "shortName": "PRE", "version": "0.1", "language": "es", "source": f"analisis/funcional.md v{V[0]}.{V[1]}",
       "today": "2026-10-06", "appianVersion": VERSION.group(0) if VERSION else "26.9"}
if not VERSION:
    app["$assumption"] = "Versión de Appian sin confirmar: el técnico no la dice (§0). Se prototipa con 26.9."
spec = {"app": app,
        "site": {"displayName": NOMBRE, "home": "catalogo", "user": {"name": YO},
                 "pages": [{"title": "Catálogo", "icon": "th-large", "screen": "catalogo", "includes": ["equipo", "solicitar"]},
                           {"title": "Mis préstamos", "icon": "list", "screen": "mis-prestamos"}]},
        "requirements": requisitos(screens),
        "openQuestions": preguntas(),
        "maps": {"prestamoColor": state_map(COLOR_PRESTAMO), "prestamoColorGrid": state_map(COLOR_PRESTAMO, grid=True),
                 "equipoColor": state_map(COLOR_EQUIPO), "equipoColorGrid": state_map(COLOR_EQUIPO, grid=True)},
        "data": {"equipos": {"recordType": EQ, "rows": equipos}, "prestamos": {"recordType": PR, "rows": prestamos}},
        "screens": screens,
        "captures": [{"name": "01-catalogo", "screen": "catalogo"},
                     {"name": "02-solicitar", "screen": "solicitar"},
                     {"name": "03-mis-prestamos", "screen": "mis-prestamos"},
                     {"name": "04-aprobar", "screen": "aprobar", "params": {"id": 2}},
                     {"name": "05-entregar", "screen": "entregar", "params": {"id": 1}},
                     {"name": "06-equipo", "screen": "equipo", "params": {"id": 1}}]}
salida = Path(a.salida)
salida.parent.mkdir(parents=True, exist_ok=True)
salida.write_text(json.dumps(clean(spec), ensure_ascii=False, indent=1), encoding="utf-8")
print("ok:", len(equipos), "equipos ·", len(prestamos), "préstamos ·", len(spec["requirements"]), "requisitos ·",
      len(spec["openQuestions"]), "preguntas abiertas")
