"""Prototipo de prueba de dos pantallas, generado del análisis ficticio de autorizaciones.

Uso: python3 generar_app.py <app.json>        (lo ejecuta pruebas/appian-prototipos/selftest.py)

Como en un proyecto (SKILL.md del kit, paso 2), el spec sale del análisis: el funcional y el técnico de
pruebas/appian-functional-analyst/datos/autorizaciones/, leídos con modelo.py del analista. De ahí salen el `ref`
y el `req` de cada pantalla, los requisitos (historias y pasos), las preguntas abiertas (PC), los estados y los tipos
de solicitud y la versión de Appian, así que el spec no se desincroniza del análisis. Las pantallas son PAN-01
(listado, P01) y PAN-02 (ficha, P02), hechas con los helpers del kit (scripts/sail_helpers.py).

El kit y el analista se toman de $PLUGIN_A_PROBAR/skills/ (por defecto, los de este repositorio).
"""
import json
import os
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent                       # pruebas/appian-prototipos/datos/autorizaciones
PRUEBAS = AQUI.parents[2]                                    # pruebas/
PLUGIN = Path(os.environ.get("PLUGIN_A_PROBAR") or PRUEBAS.parent).resolve()
sys.dont_write_bytecode = True  # sin __pycache__ en el plugin
sys.path.insert(0, str(PLUGIN / "skills" / "appian-prototipos" / "scripts"))
sys.path.insert(0, str(PLUGIN / "skills" / "appian-functional-analyst" / "scripts"))
from sail_helpers import *  # noqa: E402,F401,F403
import modelo  # noqa: E402

FUN = modelo.Proyecto(PRUEBAS / "appian-functional-analyst" / "datos" / "autorizaciones")
if "F" not in FUN.docs or "T" not in FUN.docs:
    sys.exit(f"No encuentro funcional.md y tecnico.md en {FUN.analisis}")


# ------------------------------------------------------------------ del análisis
def ref(pan):
    """«PAN-02 · Ficha de la solicitud»: el ID y el título de la ficha, literales."""
    return f"{pan} · {FUN.piezas[pan].titulo}"


def req(pan):
    """Las historias de la línea «Historias:» de la ficha y los pasos cuya pantalla es esa."""
    linea = re.search(r"^Historias:(.*)$", FUN.texto(pan), re.M)
    historias = sorted(modelo.ids_en(linea.group(1)) if linea else (), key=modelo.numero)
    pasos = [p.id for p in sorted(FUN.vigentes("ACT"), key=lambda p: modelo.numero(p.id))
             if pan in modelo.ids_en(FUN.campos(p.id).get("pantalla", ""))]
    return historias + pasos


def requisitos(screens):
    """Las historias y los pasos de las pantallas del prototipo, con su ID y su título literales."""
    ids = {i for s in screens for i in s["req"]}
    orden = sorted(ids, key=lambda i: (modelo.tipo_de(i) != "HU", modelo.numero(i)))
    return [{"id": i, "title": FUN.piezas[i].titulo} for i in orden]


def preguntas(screens):
    """PC abiertos: la pregunta con sus opciones y, si «Afecta a» cita algo de una pantalla del prototipo, esa pantalla."""
    pantalla = {}
    for s in screens:
        for i in [s["ref"].split(" · ")[0], *s["req"]]:
            pantalla.setdefault(i, s["id"])
    out = []
    for p in sorted(FUN.vigentes("PC"), key=lambda p: modelo.numero(p.id)):
        cab = [modelo.normaliza(c) for c in modelo.celdas(p.cabecera)]
        fila = dict(zip(cab, (modelo.sin_comentarios(c).strip() for c in modelo.celdas(FUN.lineas("F")[p.ini]))))
        opciones = fila.get("opciones", "").strip(" —-")
        q = {"id": p.id, "text": fila.get("pregunta", p.titulo) + (f" ({opciones})" if opciones else "")}
        destino = [pantalla[i] for i in sorted(modelo.ids_en(fila.get("afecta a", ""))) if i in pantalla]
        if destino:
            q["screen"] = destino[0]
        out.append(q)
    return out


def tabla(doc, seccion, primera):
    """Filas, sin comentarios, de la tabla del apartado cuya primera columna se llama `primera`."""
    for _, cab, filas in FUN.tablas(doc, seccion):
        if cab and modelo.normaliza(cab[0]) == modelo.normaliza(primera):
            return [[modelo.sin_comentarios(c).strip() for c in f] for f in filas]
    sys.exit(f"No encuentro la tabla «{primera} · …» en {modelo.NOMBRE_DOC[doc]} §{seccion}")


def valor(filas, dato):
    return next((f[1] for f in filas if modelo.normaliza(f[0]) == modelo.normaliza(dato)), "")


ESTADOS = [f[0] for f in tabla("F", "3", "Estado")]
TIPOS = [x.strip() for x in valor(tabla("F", "6", "Lista"), "Tipo de autorización").split(",") if x.strip()]
VERSION = re.search(r"\d+\.\d+", valor(tabla("T", "0", "Dato"), "Versión de Appian"))
NOMBRE = FUN.lineas("F")[0].lstrip("# ").split(" — ")[0]
V = FUN.version("F")

# ------------------------------------------------------------------ datos de ejemplo (ficticios)
RT = "AUT Solicitud"                                         # técnico §3.1; los campos, con su nombre de técnico §3
F = lambda f: f"recordType!{RT}.fields.{f}"
COLOR = {"Borrador": "neutral", "En revisión": "enCurso", "Pendiente de subsanar": "atencion", "En informe": "enCurso",
         "Pendiente de resolver": "atencion", "Autorizada": "positivo", "Denegada": "negativo"}
TECNICA = "Elena Martín Soto"                                # perfil Técnico de la unidad gestora, el de PAN-02
_src = [  # (título, tipo, unidad, estado, inicio, fin, fecha límite, creada por, creada el, informe técnico, resolución, motivo)
    ("Corte del vial de acceso norte durante una semana", "Obra menor", "Unidad de Obras", "Autorizada", "2026-09-28", "2026-10-04", "2026-09-18", "Andrés Gil Prieto", "2026-08-06", "La obra no coincide con otras de la zona y el desvío está señalizado.", "Favorable", None),
    ("Sustitución de luminarias en el aparcamiento P2", "Obra menor", "Unidad de Mantenimiento", "Pendiente de subsanar", "2026-10-19", "2026-10-23", "2026-10-21", "Pablo Ortiz Lara", "2026-09-08", None, None, None),
    ("Ocupación temporal de la explanada para la feria de otoño", "Ocupación temporal", "Unidad de Eventos", "En informe", "2026-11-06", "2026-11-08", "2026-10-09", "Sara Núñez Ferrer", "2026-08-27", None, None, None),
    ("Zanja para la nueva acometida de agua", "Obra menor", "Unidad de Obras", "Denegada", "2026-10-05", "2026-10-16", "2026-09-22", "Andrés Gil Prieto", "2026-08-11", "La zanja cruza el vial que ocupa otra obra autorizada.", "Desfavorable", "La obra coincide con otra en la misma zona."),
    ("Uso del salón de actos para unas jornadas técnicas", "Uso de instalaciones", "Unidad de Seguridad", "Pendiente de resolver", "2026-10-14", "2026-10-15", "2026-09-30", "Diego Campos Ruiz", "2026-08-19", "El salón está libre esas fechas y el aforo es suficiente.", None, None),
    ("Montaje de andamios en la fachada sur", "Obra menor", "Unidad de Mantenimiento", "En revisión", "2026-11-02", "2026-11-27", "2026-10-30", "Pablo Ortiz Lara", "2026-09-17", None, None, None),
    ("Ocupación de dos plazas de aparcamiento para un contenedor", "Ocupación temporal", "Unidad de Obras", "Autorizada", "2026-09-21", "2026-10-02", "2026-09-10", "Andrés Gil Prieto", "2026-07-29", "Las plazas no son de uso público y el contenedor no corta el paso.", "Favorable", None),
    ("Uso de la sala de formación para un simulacro", "Uso de instalaciones", "Unidad de Seguridad", "En revisión", "2026-11-10", "2026-11-10", "2026-11-04", "Diego Campos Ruiz", "2026-09-22", None, None, None),
    ("Reparación del muro del jardín", "Obra menor", "Unidad de Mantenimiento", "Borrador", "2026-11-16", "2026-11-20", None, "Pablo Ortiz Lara", "2026-09-23", None, None, None),
    ("Ocupación temporal del vestíbulo para una exposición", "Ocupación temporal", "Unidad de Eventos", "En informe", "2026-12-01", "2026-12-12", "2026-10-15", "Sara Núñez Ferrer", "2026-09-03", None, None, None),
]
rows, numero = [], 0
for i, (tit, tipo, uni, est, ini, fin, lim, por, el, inf, res, mot) in enumerate(_src, start=1):
    if est != "Borrador":                                    # HU-01.2: el número se pone al enviarla
        numero += 1
    rows.append({"id": i, "numero": None if est == "Borrador" else f"AUT-2026-{numero:04d}", "titulo": tit, "tipo": tipo,
                 "grupoUnidad": uni, "estado": est, "fechaInicio": ini, "fechaFin": fin, "fechaLimite": lim,
                 "descripcion": f"{tit} entre el {ini[8:]}/{ini[5:7]} y el {fin[8:]}/{fin[5:7]}.", "informeTecnico": inf,
                 "resolucion": res, "motivo": mot, "comentarioSubsanacion": "Falta el plano de la zona." if est == "Pendiente de subsanar" else None,
                 "createdBy": por, "createdOn": el})
mal = sorted({r["estado"] for r in rows} - set(ESTADOS)) + sorted({r["tipo"] for r in rows} - set(TIPOS))
if mal:
    sys.exit(f"Los datos de ejemplo usan valores que no están en el funcional: {', '.join(mal)}")
documentos = []
for r in rows:
    clases = ["Memoria"] + ([] if r["comentarioSubsanacion"] else ["Plano"])          # ESC-02: falta el plano
    clases += ["Informe del organismo"] if r["estado"] in ("Pendiente de resolver", "Autorizada", "Denegada") else []
    clases += ["Autorización"] if r["estado"] == "Autorizada" else []
    for k, clase in enumerate(clases):
        subido = TECNICA if clase == "Informe del organismo" else "Aplicación" if clase == "Autorización" else r["createdBy"]
        documentos.append({"id": r["id"] * 10 + k, "solicitudId": r["id"], "clase": clase, "icono": "file-pdf-o",
                           "fichero": f"{r['numero'] or 'borrador'}_{clase.lower().replace(' ', '_')}.pdf",
                           "createdBy": subido, "meta": f"{clase} · PDF · {subido} · {r['createdOn'][8:]}/{r['createdOn'][5:7]}/2026"})

# ------------------------------------------------------------------ PAN-01 Solicitudes (P01)
solicitudes = {"id": "solicitudes", "title": "Solicitudes", "type": "page", "pattern": "P01", "ref": ref("PAN-01"), "req": req("PAN-01"),
               "assumptions": ["Prueba de dos pantallas: «Nueva solicitud» abre PAN-03, que no se prototipa aquí"],
               "interface": {"type": "a!headerContentLayout", "backgroundColor": BG, "contents": [
                   page_header("Solicitudes", "Las solicitudes de todas las unidades, salvo los borradores"),
                   content_card([grid(f"recordType!{RT}", 'fv!row.estado <> "Borrador"', [
                       gcol("Solicitud", two_line("{fv!row.numero}", "{fv!row.titulo}", {"type": "a!recordLink", "recordType": f"recordType!{RT}", "identifier": "{fv!row.id}"}), sortField=F("numero"), width="5X"),
                       gcol("Unidad", "{fv!row.grupoUnidad}", sortField=F("grupoUnidad"), width="2X"),
                       gcol("Estado", tag("fv!row.estado", "estadoColorGrid"), sortField=F("estado"), width="NARROW_PLUS"),
                       gcol("Fecha límite", "{fv!row.fechaLimite|date|dash}", sortField=F("fechaLimite"), width="NARROW_PLUS"),
                   ], "No hay solicitudes que cumplan los filtros", page_size=25, showSearchBox=True, showExportButton=True,
                       userFilters=[f"recordType!{RT}.filters.estado", f"recordType!{RT}.filters.tipo"],
                       initialSorts=[{"type": "a!sortInfo", "field": F("fechaLimite"), "ascending": True}],
                       **{"$note": "RB-01: la técnica ve todas menos los borradores; en Appian, seguridad de registro (DT-02), no el filtro. "
                                   "Descargar (DOC-02) solo para Consulta: showExportButton con a!isUserMemberOfGroup(cons!AUT_GRUPO_CONSULTA). "
                                   "Estado y tipo son record types de referencia (DT-01): la columna lee su nombre por la relación."})]),
               ]}}

# ------------------------------------------------------------------ PAN-02 Ficha de la solicitud (P02)
FACTS = [("Estado", tag("rv!record.estado", "estadoColor")), ("Tipo", "{rv!record.tipo}"), ("Unidad", "{rv!record.grupoUnidad}"),
         ("Fecha límite", "{rv!record.fechaLimite|date|dash}")]
solicitud = {"id": "solicitud", "title": "{rv!record.numero} · {rv!record.titulo}", "type": "record", "pattern": "P02", "recordType": RT,
             "ref": ref("PAN-02"), "req": req("PAN-02"), "breadcrumb": {"label": "Solicitudes", "goto": "solicitudes"}, "headerBackgroundColor": NAVY,
             "assumptions": ["Prueba de dos pantallas: adjuntar el informe del organismo y redactar el informe técnico son acciones con su propia pantalla, que no se prototipan aquí"],
             "views": [
                 {"id": "resumen", "label": "Resumen", "interface": {"type": "a!headerContentLayout", "backgroundColor": BG, "contents": [
                     key_facts(FACTS),
                     section_card("Datos de la solicitud", field_summary([("Título", "{rv!record.titulo}", True), ("Fecha de inicio", "{rv!record.fechaInicio|date}"),
                                                                          ("Fecha de fin", "{rv!record.fechaFin|date}"), ("Resolución", "{rv!record.resolucion|dash}"),
                                                                          ("Descripción", "{rv!record.descripcion}", True), ("Motivo", "{rv!record.motivo|dash}", True)]))]}},
                 {"id": "documentos", "label": "Documentos", "interface": {"type": "a!headerContentLayout", "backgroundColor": BG, "contents": [
                     section_card("Documentos", [document_list("data!documentos", name="fv!item.fichero", flt="fv!item.solicitudId = rv!record.id",
                                                               **{"$note": "AUT Documento, relacionado con AUT Solicitud (1:N)."})])]}},
                 {"id": "informe", "label": "Informe técnico", "interface": {"type": "a!headerContentLayout", "backgroundColor": BG, "contents": [
                     por_perfil(section_card("Informe técnico", [{"type": "a!richTextDisplayField", "labelPosition": "COLLAPSED", "value": ["{rv!record.informeTecnico|dash}"]}]),
                                "Técnico de la unidad gestora hasta que lo marca como terminado (HU-06.1)", "vista")]}},
                 {"id": "historial", "label": "Historial", "interface": {"type": "a!headerContentLayout", "backgroundColor": BG, "contents": [content_card([
                     {"type": "a!eventHistoryListField", "labelPosition": "COLLAPSED", "$events": [
                         {"event": "Solicitud enviada", "user": "{rv!record.createdBy}", "timestamp": "{rv!record.createdOn}T10:30:00"},
                         {"event": "Borrador creado", "user": "{rv!record.createdBy}", "timestamp": "{rv!record.createdOn}T09:00:00"}]}], padding="MORE")]}},
             ]}

screens = [solicitudes, solicitud]
app = {"name": NOMBRE, "shortName": "AUT", "version": "0.1", "language": "es", "source": f"analisis/funcional.md v{V[0]}.{V[1]}",
       "today": "2026-09-24", "appianVersion": VERSION.group(0) if VERSION else "26.9"}
if not VERSION:
    app["$assumption"] = "Versión de Appian sin confirmar: el técnico no la dice (§0). Se prototipa con 26.9."
spec = {"app": app,
        "site": {"displayName": NOMBRE, "home": "solicitudes", "user": {"name": TECNICA},
                 "pages": [{"title": "Solicitudes", "icon": "list", "screen": "solicitudes", "includes": ["solicitud"]}]},
        "requirements": requisitos(screens),
        "openQuestions": preguntas(screens),
        "maps": {"estadoColor": state_map(COLOR), "estadoColorGrid": state_map(COLOR, grid=True)},
        "data": {"solicitudes": {"recordType": RT, "rows": rows}, "documentos": documentos},
        "screens": screens,
        "captures": [{"name": "01-solicitudes", "screen": "solicitudes"},
                     {"name": "02-ficha-resumen", "screen": "solicitud", "params": {"id": 5}},
                     {"name": "03-ficha-documentos", "screen": "solicitud", "params": {"id": 5}, "view": "documentos"}]}
salida = Path(sys.argv[1] if len(sys.argv) > 1 else "app.json")
salida.parent.mkdir(parents=True, exist_ok=True)
salida.write_text(json.dumps(clean(spec), ensure_ascii=False, indent=1), encoding="utf-8")
print("ok:", len(rows), "solicitudes ·", len(spec["requirements"]), "requisitos ·", len(spec["openQuestions"]), "preguntas abiertas")
