"""Genera el spec del prototipo del caso ATP. Uso, desde esta carpeta: python3 generar_app.py app.json

El caso es un proceso más, no un modelo de dominio. Parte de ../analisis/funcional.md (references/ingesta-requisitos.md):
- los requisitos (historias y pasos), las preguntas abiertas (PC) y el `ref` y el `req` de cada pantalla se leen del
  funcional con modelo.py de appian-functional-analyst: así el spec no se desincroniza del análisis;
- las pantallas usan los helpers del kit (scripts/sail_helpers.py) y la guía de diseño (references/design-rules.md):
  cards blancas sobre fondo gris, franja de KPI, franja de datos clave, grids consolidados, paleta de estados,
  asistente con barra lateral, decisión con cards y gráficos con su tabla alternativa."""
import json, datetime, random, re, sys
from pathlib import Path
AQUI = Path(__file__).resolve().parent                # <caso>/prototipo
KIT = Path(__file__).resolve().parents[4]             # skills/appian-prototipos-aena
sys.path.insert(0, str(KIT / "scripts"))
sys.path.insert(0, str(KIT.parent / "appian-functional-analyst" / "scripts"))
from sail_helpers import *  # noqa: E402,F401
import modelo  # noqa: E402

# ------------------------------------------------------------------ el funcional
FUN = modelo.Proyecto(AQUI.parent)
if "F" not in FUN.docs:
    sys.exit(f"No encuentro {FUN.analisis / 'funcional.md'}")


def ref(pan):
    """«PAN-03 · Ficha del acuerdo»: ID y título de la ficha, literales."""
    return f"{pan} · {FUN.piezas[pan].titulo}"


def req(pan):
    """Historias de la ficha («Historias: …») y pasos que se hacen en esa pantalla."""
    m = re.search(r"^Historias:(.*)$", FUN.texto(pan), re.M)
    hu = sorted(modelo.ids_en(m.group(1))) if m else []
    return hu + sorted(p.id for p in FUN.vigentes("ACT") if pan in modelo.ids_en(FUN.campos(p.id).get("pantalla", "")))


def requisitos():
    """Historias y pasos con su ID y título literales; los pasos sin pantalla dicen por qué."""
    out = [{"id": p.id, "title": p.titulo} for p in sorted(FUN.vigentes("HU"), key=lambda p: modelo.numero(p.id))]
    for p in sorted(FUN.vigentes("ACT"), key=lambda p: modelo.numero(p.id)):
        c, r = FUN.campos(p.id), {"id": p.id, "title": p.titulo}
        pantalla = modelo.sin_comentarios(c.get("pantalla", "")).strip()
        if any(i.startswith("PAN-") for i in modelo.ids_en(pantalla)):
            pass
        elif modelo.normaliza(pantalla).startswith("fuera"):
            r["outOfScope"] = f"Fuera de la aplicación ({c.get('quien', '—')})"
        elif pantalla in ("—", "-"):
            r["noScreen"] = "Lo hace la aplicación"
        else:
            pcs = sorted(i for i in modelo.ids_en(modelo.sin_comentarios(FUN.texto(p.id))) if i.startswith("PC-"))
            r["noScreen"] = "Pantalla por decidir" + (f" ({', '.join(pcs)})" if pcs else "")
        out.append(r)
    return out


def preguntas(screens):
    """PC abiertos → openQuestions, con la pantalla del spec que corresponde a «Afecta a»."""
    pantalla = {s["ref"].split(" · ")[0]: s["id"] for s in screens if s.get("ref")}

    def de(i, nivel=0):  # la pantalla de un PAN, o la de la historia, el paso o la regla citados
        if i in pantalla:
            return pantalla[i]
        p = FUN.piezas.get(i)
        if not p or nivel > 1:
            return None
        cand = modelo.RX_ID.findall(FUN.campos(i).get("pantalla", "")) if p.tipo in ("HU", "ACT") else sorted(p.refs)
        return next(filter(None, (de(x, nivel + 1) for x in cand)), None)

    out = []
    for p in sorted(FUN.vigentes("PC"), key=lambda p: modelo.numero(p.id)):
        cab = [modelo.normaliza(c) for c in modelo.celdas(p.cabecera)]
        fila = dict(zip(cab, (modelo.sin_comentarios(c).strip() for c in modelo.celdas(FUN.docs["F"].lineas[p.ini]))))
        opciones = fila.get("opciones", "").strip("—- ")
        q = {"id": p.id, "text": fila.get("pregunta", "") + (f" ({opciones})" if opciones else "")}
        s = next(filter(None, (de(i) for i in modelo.RX_ID.findall(fila.get("afecta a", "")))), None)
        if s:
            q["screen"] = s
        out.append(q)
    return out


# ------------------------------------------------------------------ datos de ejemplo (ficticios)
ATP_ESTADOS = {"Borrador": "neutral", "En revisión jurídica": "enCurso", "Pendiente de firma": "atencion", "Vigente": "positivo", "Vencido": "negativo", "Rechazado": "negativo"}
ATP_FASES = list(ATP_ESTADOS)
GESTOR, REVISOR = "Gestor de acuerdos", "Revisor jurídico"
random.seed(7)
TODAY = datetime.date(2026, 9, 24)

groups = [
    {"id": "g-atp", "name": "Acuerdos con terceras partes", "description": "Todas las personas de la aplicación"},
    {"id": "g-gestores", "name": "Gestores de acuerdos", "parent": "g-atp", "description": "Perfil Gestor de acuerdos (unidades promotoras)"},
    {"id": "g-juridica", "name": "Asesoría Jurídica", "parent": "g-atp", "description": "Perfil Revisor jurídico"},
    {"id": "g-consulta", "name": "Consulta", "parent": "g-atp", "description": "Perfil Consulta"}]
users = [{"id": u, "name": n, "title": t, "groups": [g]} for u, n, t, g in [
    ("mlopez", "María López Arranz", "Gestora de acuerdos · Madrid-Barajas", "g-gestores"),
    ("jgarcia", "Javier García Ruiz", "Gestor de acuerdos · Servicios Centrales", "g-gestores"),
    ("rsanchez", "Rocío Sánchez Vidal", "Gestora de acuerdos · Barcelona-El Prat", "g-gestores"),
    ("pmartin", "Pablo Martín Ortega", "Gestor de acuerdos · Canarias y Málaga", "g-gestores"),
    ("amoreno", "Andrés Moreno Pastor", "Gestor de acuerdos · Sevilla, Palma y Bilbao", "g-gestores"),
    ("lfernandez", "Lucía Fernández Gil", "Letrada · Asesoría Jurídica", "g-juridica"),
    ("cnavarro", "Carmen Navarro Sanz", "Auditoría interna", "g-consulta")]]
# terceros, CIF y acuerdos inventados; ESC-01 = 5, ESC-02 = 6, ESC-03 = 12
rows_src = [
    ("Convenio de colaboración para formación en seguridad aeroportuaria", "Convenio", "Universidad Politécnica del Tajo", "Q2899101C", "Universidad o centro de investigación", "MAD", "mlopez", "2025-03-01", "2027-02-28", True, False, 0, "Vigente", "2025-01-20"),
    ("Acuerdo de confidencialidad del proyecto de biometría en filtros", "Acuerdo de confidencialidad", "Biometrix Identidad Digital S.L.", "B71990102", "Empresa privada", "BCN", "jgarcia", "2026-02-15", "2026-11-30", False, False, 0, "Vigente", "2026-02-02"),
    ("Protocolo general de actuación con el Ayuntamiento de Vilamar", "Protocolo general de actuación", "Ayuntamiento de Vilamar de Llobregat", "P0899103D", "Administración pública", "BCN", "rsanchez", "2024-06-01", "2026-12-15", False, False, 0, "Vigente", "2024-05-10"),
    ("Contrato de colaboración para la promoción turística de Canarias", "Contrato de colaboración", "Consorcio Turístico Atlántico", "S3599104E", "Administración pública", "LPA", "pmartin", "2026-01-01", "2026-12-31", True, True, 180000, "Vigente", "2025-11-18"),
    ("Convenio de prácticas para el grado en ingeniería aeroespacial", "Convenio", "Universidad de la Vega del Guadalquivir", "Q4199105F", "Universidad o centro de investigación", "SVQ", "amoreno", "2026-10-01", "2028-09-30", True, False, 0, "Pendiente de firma", "2026-07-28"),
    ("Contrato de colaboración en eficiencia energética de las terminales", "Contrato de colaboración", "Energía Verde Terminales S.A.", "A95990106", "Empresa privada", "SSCC", "amoreno", "2026-11-01", "2029-10-31", False, True, 420000, "En revisión jurídica", "2026-09-02"),
    ("Protocolo de coordinación de emergencias con la agencia regional", "Protocolo general de actuación", "Agencia Regional de Emergencias del Centro", "S7899107G", "Administración pública", "MAD", "mlopez", "2023-04-01", "2026-03-31", False, False, 0, "Vencido", "2023-03-02"),
    ("Acuerdo de confidencialidad de la licitación de handling", "Acuerdo de confidencialidad", "Handling Peninsular Cargo S.L.", "B84990108", "Empresa privada", "SSCC", "jgarcia", "2026-09-10", "2027-09-09", False, False, 0, "En revisión jurídica", "2026-09-12"),
    ("Convenio de patrocinio de un festival de cine", "Convenio", "Fundación Festival de Cine del Sur", "G2999109I", "Otro", "AGP", "pmartin", "2026-02-01", "2026-10-31", False, True, 35000, "Vigente", "2026-01-12"),
    ("Contrato de colaboración para movilidad eléctrica en aparcamientos", "Contrato de colaboración", "Recarga Urbana Movilidad S.L.", "B42990110", "Empresa privada", "VLC", "rsanchez", "2026-12-01", "2030-11-30", True, True, 96000, "Borrador", "2026-09-18"),
    ("Convenio de colaboración en el control de accesos", "Convenio", "Jefatura Insular de Seguridad de Baleares", "S0799111K", "Administración pública", "PMI", "amoreno", "2025-07-01", "2027-06-30", True, False, 0, "Vigente", "2025-06-05"),
    ("Acuerdo de confidencialidad sobre datos de tráfico", "Acuerdo de confidencialidad", "Tráfico Aéreo Analytics Ltd.", "N0099112L", "Empresa privada", "SSCC", "jgarcia", "2026-06-01", "2027-05-31", False, False, 0, "Rechazado", "2026-05-20"),
    ("Convenio de investigación sobre ruido en entornos aeroportuarios", "Convenio", "Centro de Investigación en Acústica Ambiental", "Q2899113M", "Universidad o centro de investigación", "MAD", "mlopez", "2026-04-01", "2028-03-31", False, True, 64000, "Vigente", "2026-03-03"),
    ("Contrato de colaboración de accesibilidad para personas con movilidad reducida", "Contrato de colaboración", "Fundación Accesibilidad Universal", "G78990114", "Otro", "BIO", "jgarcia", "2026-10-15", "2027-10-14", True, True, 22000, "En revisión jurídica", "2026-09-20"),
    ("Protocolo para la intermodalidad tren-avión", "Protocolo general de actuación", "Ferrocarriles Interurbanos S.A.", "A86990115", "Empresa privada", "MAD", "pmartin", "2025-10-01", "2027-09-30", True, False, 0, "Vigente", "2025-09-08"),
    ("Acuerdo de confidencialidad del piloto de drones de inspección", "Acuerdo de confidencialidad", "Drones de Inspección Técnica S.L.", "B37990116", "Empresa privada", "SVQ", "rsanchez", "2026-08-01", "2027-01-31", False, False, 0, "Pendiente de firma", "2026-07-15"),
]
uname = {u["id"]: u["name"] for u in users}
# Sin especificación técnica: cada campo lleva el nombre del dato de funcional §6 en camelCase (ingesta-requisitos.md §0.3).
# mesAlta y diasParaVencer los precalcula el prototipo (spec-format.md, «Los datos de ejemplo no cambian»).
acuerdos = []
for i, r in enumerate(rows_src, start=1):
    (tit, tipo, ter, cif, tter, apt, resp, ini, fin, pro, conimp, imp, est, alta) = r
    acuerdos.append({
        "id": i, "codigo": f"ATP-{alta[:4]}-{i:04d}", "titulo": tit, "tipoAcuerdo": tipo, "tercero": ter, "cifNifTercero": cif,
        "tipoTercero": tter, "aeropuertoUnidad": apt, "responsableAena": resp, "fechaInicio": ini, "fechaFin": fin,
        "prorrogaAutomatica": pro, "contenidoEconomico": conimp, "importe": imp if conimp else None,
        "contraprestacion": "Cesión de espacios y difusión institucional" if conimp else None,
        "estado": est, "fechaAlta": alta, "mesAlta": alta[:7], "diasParaVencer": (datetime.date.fromisoformat(fin) - TODAY).days,
    })
tareas = [{"id": k, "tarea": "Revisar acuerdo", "acuerdoId": a, "codigo": acuerdos[a - 1]["codigo"], "titulo": acuerdos[a - 1]["titulo"], "recibida": rec, "vence": ven}
          for k, (a, rec, ven) in enumerate([(6, "2026-09-02", "2026-09-26"), (8, "2026-09-12", "2026-09-30"), (14, "2026-09-20", "2026-10-06")], start=1)]
for t in tareas:
    d = (datetime.date.fromisoformat(t["vence"]) - TODAY).days
    t["plazo"] = f"Vence en {d} días" if d > 1 else "Vence mañana" if d == 1 else "Vence hoy"
    t["urgente"] = d <= 3
documentos = []
for a in acuerdos:
    for nombre, tipo in [(f"{a['codigo']}_texto_acuerdo.pdf", "Texto del acuerdo"), (f"{a['codigo']}_memoria_justificativa.docx", "Memoria justificativa")] + ([(f"{a['codigo']}_acuerdo_firmado.pdf", "Acuerdo firmado")] if a["estado"] in ("Vigente", "Vencido") else []):
        kb = random.randint(180, 2400)
        documentos.append({"id": len(documentos) + 1, "acuerdoId": a["id"], "nombre": nombre, "tipo": tipo, "subidoPor": uname[a["responsableAena"]], "fecha": a["fechaAlta"],
                           "tamano": f"{kb} KB" if kb < 1000 else f"{kb / 1024:.1f} MB".replace(".", ","), "icono": "file-pdf-o" if nombre.endswith(".pdf") else "file-word-o"})
eventos = []
for a in acuerdos:
    quien = uname[a["responsableAena"]]
    ev = [("Acuerdo creado", quien, a["fechaAlta"] + "T09:14:00", "Alta en estado Borrador", None)]
    if a["estado"] != "Borrador":
        ev.append(("Enviado a revisión jurídica", quien, a["fechaAlta"] + "T12:40:00", None, None))
    if a["estado"] in ("Pendiente de firma", "Vigente", "Vencido"):
        ev.append(("Aprobado por Asesoría Jurídica", uname["lfernandez"], a["fechaAlta"] + "T17:05:00", None, "Conforme. Revisada la cláusula de protección de datos."))
    if a["estado"] == "Rechazado":
        ev.append(("Rechazado por Asesoría Jurídica", uname["lfernandez"], a["fechaAlta"] + "T17:05:00", None, "El objeto del acuerdo requiere licitación pública."))
    if a["estado"] in ("Vigente", "Vencido"):
        ev.append(("Acuerdo firmado", quien, a["fechaInicio"] + "T10:00:00", "Estado: Vigente", None))
    for e in reversed(ev):
        eventos.append({"acuerdoId": a["id"], "event": e[0], "user": e[1], "timestamp": e[2], "details": e[3], "comment": e[4]})

RT = "ATP Acuerdo"
F = lambda f: f"recordType!{RT}.fields.{f}"
TIPOS = ["Convenio", "Contrato de colaboración", "Acuerdo de confidencialidad", "Protocolo general de actuación"]
TIPOS_ICON = ["handshake-o", "file-text-o", "lock", "sitemap"]
TIPOS_TERCERO = ["Empresa privada", "Administración pública", "Universidad o centro de investigación", "Otro"]
AEROPUERTOS = ["SSCC", "MAD", "BCN", "PMI", "AGP", "LPA", "SVQ", "VLC", "BIO"]
AEROPUERTOS_L = ["Servicios Centrales", "Adolfo Suárez Madrid-Barajas (MAD)", "Josep Tarradellas Barcelona-El Prat (BCN)", "Palma de Mallorca (PMI)", "Málaga-Costa del Sol (AGP)", "Gran Canaria (LPA)", "Sevilla (SVQ)", "Valencia (VLC)", "Bilbao (BIO)"]
VENCEN_90 = "and(fv!row.estado = \"Vigente\", fv!row.diasParaVencer <= 90, fv!row.diasParaVencer >= 0)"  # HU-01.1: «en los próximos 90 días»
VENCE = "and(fv!row.estado = \"Vigente\", fv!row.diasParaVencer < 90, fv!row.diasParaVencer >= 0)"  # HU-11.1: «en menos de 90 días»
n_vencen = sum(1 for a in acuerdos if a["estado"] == "Vigente" and 0 <= a["diasParaVencer"] <= 90)
RB01 = {"when": "and(a!isNotNullOrEmpty({f}), a!isNotNullOrEmpty({i}), {f} <= {i})", "message": "La fecha de fin debe ser posterior a la fecha de inicio"}
NOTA_RB01 = "RB-01. Texto del mensaje pendiente: PC-09."
NOTA_RB02 = "RB-02: PDF o DOCX, 10 MB como máximo. En Appian: validar extensión y tamaño con fv!files."


def rb01(fin, ini):
    return [{"when": RB01["when"].format(f=fin, i=ini), "message": RB01["message"]}]


def kpi_rt(text, icon, flt, secondary, sec_text, reverse=False, fmt=None, measure=None):
    k = kpi(text, icon, secondary=secondary, sec_text=sec_text, reverse=reverse, data=f"recordType!{RT}",
            primaryMeasure=measure or {"type": "a!measure", "function": "COUNT", "field": F("id")})
    k["$filter"] = flt
    if fmt: k["$format"] = fmt
    return k


def nuevo_acuerdo():
    return por_perfil(primary("Nuevo acuerdo", {"goto": "alta"}, "plus"), GESTOR, "accion")


def estados_chart(kind):
    cfg = "a!barChartConfig" if kind == "a!barChartField" else "a!columnChartConfig"
    return {"type": kind, "labelPosition": "COLLAPSED", "data": f"recordType!{RT}", "height": "AUTO" if kind == "a!barChartField" else "SHORT", "showDataLabels": True,
            "$categories": ATP_FASES, "config": {"type": cfg, "primaryGrouping": {"type": "a!grouping", "field": F("estado")}, "secondaryGrouping": {"type": "a!grouping", "field": F("estado")},
                                                "measures": [{"type": "a!measure", "function": "COUNT", "field": F("id"), "label": "Acuerdos"}]},
            "stacking": "NORMAL", "showLegend": False, "colorScheme": state_chart_colors(ATP_ESTADOS, ATP_FASES)}


# ------------------------------------------------------------------ P06 Inicio (PAN-01)
importe = kpi_rt("Importe comprometido", "eur", "fv!row.estado = \"Vigente\"", 215000, "vs. agosto", fmt="eur", measure={"type": "a!measure", "function": "SUM", "field": F("importe")})
importe["$assumption"] = "Pendiente: PC-16. Suma los acuerdos vigentes."
inicio = {
    "id": "inicio", "title": "Inicio", "type": "page", "pattern": "P06", "ref": ref("PAN-01"), "req": req("PAN-01"),
    "local": {"local!tablaEstado": False},
    "interface": {"type": "a!headerContentLayout", "backgroundColor": BG, "contents": [
        page_header("Hola, Lucía", "Acuerdos con terceras partes · 24 de septiembre de 2026", [nuevo_acuerdo()]),
        por_perfil(kpi_strip([
            kpi_rt("Acuerdos vigentes", "handshake-o", "fv!row.estado = \"Vigente\"", 7, "vs. agosto"),
            kpi_rt("En revisión jurídica", "gavel", "fv!row.estado = \"En revisión jurídica\"", 1, "vs. agosto", reverse=True),
            kpi_rt("Vencen en 90 días", "calendar-times-o", VENCEN_90, 1, "vs. agosto", reverse=True),
            importe,
        ], **{"$assumption": "Pendiente: PC-05. Si Consulta también ve los indicadores."}), f"{GESTOR} y {REVISOR}", "interfaz"),
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
                              secondary("Revisar", {"goto": "acuerdos"}, size="SMALL"), kind="WARN", icon="clock-o", marginBelow="MORE",
                              **{"$assumption": "Propuesta: aviso con acceso a la lista. PAN-01 solo pide el indicador."}),
                section_card("Acuerdos por estado", [chart_table("local!tablaEstado", estados_chart("a!barChartField"), "Estado")],
                             **{"$assumption": "Propuesta: resumen por estado. PAN-01 no lo pide."}),
            ]},
        ]},
    ]},
}

# ------------------------------------------------------------------ P01 Listado (PAN-02)
listado = {
    "id": "acuerdos", "title": "Acuerdos", "type": "page", "pattern": "P01", "ref": ref("PAN-02"), "req": req("PAN-02"),
    "interface": {"type": "a!headerContentLayout", "backgroundColor": BG, "contents": [
        page_header("Acuerdos", "Acuerdos con terceras partes de todos los aeropuertos y Servicios Centrales", [nuevo_acuerdo()]),
        {"type": "a!messageBanner", "backgroundColor": "SUCCESS", "highlightColor": "POSITIVE", "shape": "SEMI_ROUNDED", "showWhen": "a!isNotNullOrEmpty(ri!mensaje)", "primaryText": "{ri!mensaje}", "secondaryText": "Asesoría Jurídica ha recibido la tarea de revisión.", "marginBelow": "STANDARD"},
        content_card([grid(f"recordType!{RT}", None, [
            gcol("Acuerdo", two_line("{fv!row.codigo}", "{fv!row.titulo}", {"type": "a!recordLink", "recordType": f"recordType!{RT}", "identifier": "{fv!row.id}"}), sortField=F("codigo"), width="4X"),
            gcol("Tercero", two_line("{fv!row.tercero}", "{fv!row.tipoTercero}", strong=False), sortField=F("tercero"), width="3X"),
            gcol("Tipo", "{fv!row.tipoAcuerdo}", sortField=F("tipoAcuerdo"), width="2X"),
            gcol("Aeropuerto", "{fv!row.aeropuertoUnidad}", sortField=F("aeropuertoUnidad"), width="NARROW"),
            gcol("Fin", "{fv!row.fechaFin|date}", sortField=F("fechaFin"), width="NARROW"),
            gcol("Estado", tag("fv!row.estado", "estadoColorGrid"), sortField=F("estado"), width="NARROW_PLUS"),
            gcol("Aviso", alert_icons([(VENCE, "clock-o", "Vence en {fv!row.diasParaVencer} días", "WARN")]), width="ICON", align="CENTER",
                 **{"$assumption": "Propuesta: aviso de vencimiento también en la lista. HU-11 lo pide en la ficha."}),
        ], "No hay acuerdos que cumplan los filtros", page_size=25, showSearchBox=True, showExportButton=True,
            userFilters=[f"recordType!{RT}.filters.estado", {"field": "tipoAcuerdo", "label": "Tipo de acuerdo"}, {"field": "aeropuertoUnidad", "label": "Aeropuerto o unidad"}],
            initialSorts=[{"type": "a!sortInfo", "field": F("fechaAlta"), "ascending": False}],
            **{"$assumption": "Pendiente: PC-02 (columnas) y PC-08 (un valor por filtro; orden por fecha de alta).",
               "$note": "RB-03: Consulta solo ve los vigentes. En Appian: seguridad de registro del record type (qué filas ve)."})]),
    ]},
}

# ------------------------------------------------------------------ P02 Vista de registro (PAN-03)
def summary_view():
    return {"type": "a!headerContentLayout", "backgroundColor": BG, "contents": [
        key_facts([
            ("Estado", tag("rv!record.estado", size="STANDARD")),
            ("Vigencia", "{rv!record.fechaInicio|date} – {rv!record.fechaFin|date}"),
            ("Tercero", "{rv!record.tercero}"),
            ("Importe", "{rv!record.importe|eur|dash}"),
            ("Responsable AENA", "{rv!record.responsableAena|map:usuarios}"),
        ], extra=[milestone(["Borrador", "En revisión jurídica", "Pendiente de firma", "Vigente", "Vencido"], "{rv!record.estado|map:estadoPaso}")]),
        action_banner("Este acuerdo vence en {rv!record.diasParaVencer} días", "Valore la renovación antes del {rv!record.fechaFin|date}", kind="WARN", icon="clock-o",
                      showWhen="and(rv!record.estado = \"Vigente\", rv!record.diasParaVencer < 90)", marginBelow="MORE",
                      **{"$assumption": "Pendiente: PC-09. Texto del aviso."}),
        {"type": "a!columnsLayout", "columns": [
            {"type": "a!columnLayout", "width": "2X", "contents": [section_card("Datos del acuerdo", [
                subsection("Datos generales", field_summary([
                    ("Código", "{rv!record.codigo}"), ("Tipo de acuerdo", "{rv!record.tipoAcuerdo}"), ("Aeropuerto o unidad", "{rv!record.aeropuertoUnidad}"),
                    ("Título", "{rv!record.titulo}", True),
                    ("Fecha de inicio", "{rv!record.fechaInicio|date}"), ("Fecha de fin", "{rv!record.fechaFin|date}"), ("Prórroga automática", "{rv!record.prorrogaAutomatica|map:siNo}")])),
                subsection("Tercero", field_summary([("Razón social", "{rv!record.tercero}"), ("CIF/NIF", "{rv!record.cifNifTercero}"), ("Tipo de tercero", "{rv!record.tipoTercero}")])),
                subsection("Condiciones económicas", field_summary([("Contenido económico", "{rv!record.contenidoEconomico|map:siNo}"), ("Importe", "{rv!record.importe|eur}"), ("Contraprestación", "{rv!record.contraprestacion}")]), marginBelow="NONE"),
            ])]},
            {"type": "a!columnLayout", "contents": [
                section_card("Responsable AENA", [{"type": "a!sideBySideLayout", "alignVertical": "MIDDLE", "items": [
                    {"type": "a!sideBySideItem", "width": "MINIMIZE", "item": {"type": "a!imageField", "labelPosition": "COLLAPSED", "size": "TINY", "style": "AVATAR", "images": [{"type": "a!userImage", "user": "{rv!record.responsableAena}"}]}},
                    {"type": "a!sideBySideItem", "item": two_line("{rv!record.responsableAena|map:usuarios}", "Unidad promotora · {rv!record.aeropuertoUnidad}")}]}]),
                section_card("Documentos recientes", [
                    {"type": "a!forEach", "items": "data!documentos", "$filter": "fv!item.acuerdoId = rv!record.id", "$limit": 3,
                     "expression": doc_line("{fv!item.nombre}", "{fv!item.tipo} · {fv!item.fecha|date}", {"goto": "acuerdo", "params": {"id": "{rv!record.id}"}, "view": "documentos"}, icon="{fv!item.icono}")},
                    link_all("Ver todos los documentos", {"goto": "acuerdo", "params": {"id": "{rv!record.id}"}, "view": "documentos"})]),
            ]},
        ]},
    ]}


registro = {
    "id": "acuerdo", "title": "{rv!record.codigo} · {rv!record.titulo}", "type": "record", "pattern": "P02", "ref": ref("PAN-03"), "recordType": RT,
    "req": req("PAN-03"),
    "breadcrumb": {"label": "Acuerdos", "goto": "acuerdos"},
    "headerBackgroundColor": NAVY,
    "recordActions": [
        por_perfil({"type": "a!recordActionItem", "action": f"recordType!{RT}.actions.editarDatosGenerales", "identifier": "{rv!record.id}", "$label": "Editar datos generales", "$icon": "pencil",
                    "$action": {"dialog": "editar", "params": {"id": "{rv!record.id}"}}}, GESTOR, "accion"),
        por_perfil({"type": "a!recordActionItem", "action": f"recordType!{RT}.actions.anadirDocumento", "identifier": "{rv!record.id}", "$label": "Añadir documento", "$icon": "paperclip",
                    "$action": {"dialog": "documento", "params": {"id": "{rv!record.id}"}}}, GESTOR, "accion"),
    ],
    "views": [
        {"id": "resumen", "label": "Resumen", "interface": summary_view()},
        {"id": "documentos", "label": "Documentos", "interface": {"type": "a!headerContentLayout", "backgroundColor": BG, "contents": [content_card([
            grid("data!documentos", "fv!row.acuerdoId = rv!record.id", [
                gcol("Documento", {"type": "a!richTextDisplayField", "labelPosition": "COLLAPSED", "value": [{"type": "a!richTextIcon", "icon": "{fv!row.icono}", "color": "SECONDARY", "size": "MEDIUM"}, "  ", {"type": "a!richTextItem", "text": "{fv!row.nombre}", "link": {"type": "a!dynamicLink"}, "linkStyle": "STANDALONE", "style": "STRONG"}, "\n", {"type": "a!richTextItem", "text": "{fv!row.tipo}", "color": "SECONDARY", "size": "SMALL"}]}, width="5X"),
                gcol("Subido por", "{fv!row.subidoPor}", width="3X"),
                gcol("Fecha", "{fv!row.fecha|date}", width="NARROW"),
                gcol_num("Tamaño", "{fv!row.tamano}", width="NARROW"),
            ], "El acuerdo no tiene documentos", **{"$note": "En Appian: record type de documentos relacionado con ATP Acuerdo (relación uno a muchos).",
                                                     "$assumption": "Pendiente: PC-15. Tipo, quién lo sube y fecha de cada documento."})], padding="NONE")]}},
        {"id": "historial", "label": "Historial", "interface": {"type": "a!headerContentLayout", "backgroundColor": BG, "contents": [content_card([
            {"type": "a!eventHistoryListField", "labelPosition": "COLLAPSED", "eventStyle": "TIMELINE", "commentLayout": "CARD", "$events": "data!eventos", "$filter": "fv!row.acuerdoId = rv!record.id",
             "$note": "En Appian: a!eventHistoryListField con a!eventData sobre el record type de eventos de ATP Acuerdo (record events).",
             "$assumption": "Pendiente: PC-04. Se muestran los cambios de estado."}], padding="MORE")]}},
    ],
}

# ------------------------------------------------------------------ P04 Asistente (PAN-04)
paso1 = [
    txt("Título", "local!acuerdo.titulo", required=True, characterLimit=200, showCharacterCount=True),
    choice_cards("Tipo de acuerdo", [{"id": t, "texto": t, "icono": i} for t, i in zip(TIPOS, TIPOS_ICON)], "local!acuerdo.tipoAcuerdo", required=True),
    cols(dd("Aeropuerto o unidad", AEROPUERTOS_L, "local!acuerdo.aeropuertoUnidad", AEROPUERTOS, required=True),
         {"type": "a!pickerFieldUsers", "label": "Responsable AENA", "maxSelections": 1, "value": "local!acuerdo.responsableAena", "saveInto": "local!acuerdo.responsableAena", "required": True}),
    cols(date("Fecha de inicio", "local!acuerdo.fechaInicio", required=True),
         date("Fecha de fin", "local!acuerdo.fechaFin", required=True, **{"$validations": rb01("local!acuerdo.fechaFin", "local!acuerdo.fechaInicio"), "$note": NOTA_RB01})),
    {"type": "a!booleanCheckboxField", "choiceLabel": "Prórroga automática al vencimiento", "value": "local!acuerdo.prorrogaAutomatica", "saveInto": "local!acuerdo.prorrogaAutomatica"},
]
paso2 = [
    txt("Razón social del tercero", "local!acuerdo.tercero", required=True),
    cols(txt("CIF/NIF del tercero", "local!acuerdo.cifNifTercero", required=True), []),
    {"type": "a!radioButtonField", "label": "Tipo de tercero", "choiceLabels": TIPOS_TERCERO, "choiceValues": TIPOS_TERCERO, "value": "local!acuerdo.tipoTercero", "saveInto": "local!acuerdo.tipoTercero", "required": True, "choiceLayout": "STACKED"},
]
paso3 = [
    {"type": "a!radioButtonField", "label": "¿El acuerdo tiene contenido económico?", "choiceLabels": ["Sí", "No"], "choiceValues": [True, False], "value": "local!acuerdo.contenidoEconomico", "saveInto": "local!acuerdo.contenidoEconomico", "required": True, "choiceLayout": "COMPACT"},
    cols({"type": "a!floatingPointField", "label": "Importe (€)", "value": "local!acuerdo.importe", "saveInto": "local!acuerdo.importe", "required": True}, [], showWhen="local!acuerdo.contenidoEconomico"),
    par("Contraprestación", "local!acuerdo.contraprestacion", height="SHORT"),
]
paso4 = [
    upload("Documentos del acuerdo", "local!acuerdo.docs", maxSelections=5, instructions="PDF o DOCX, máximo 10 MB por fichero", **{"$note": NOTA_RB02}),
]


def revisa(label, step, pairs):
    return subsection_with_link(label, "Editar", {"step": step}, field_summary(pairs, columns=2))


paso5 = [
    {"type": "a!messageBanner", "backgroundColor": "INFO", "highlightColor": "INFO", "shape": "SEMI_ROUNDED", "primaryText": "Revise los datos antes de enviar", "secondaryText": "Al enviar, el acuerdo pasará a «En revisión jurídica» y Asesoría Jurídica recibirá la tarea de revisarlo.", "marginBelow": "MORE"},
    revisa("Datos generales", 1, [("Título", "{local!acuerdo.titulo}", True), ("Tipo de acuerdo", "{local!acuerdo.tipoAcuerdo}"), ("Aeropuerto o unidad", "{local!acuerdo.aeropuertoUnidad}"), ("Responsable AENA", "{local!acuerdo.responsableAena|map:usuarios}"), ("Vigencia", "{local!acuerdo.fechaInicio|date} – {local!acuerdo.fechaFin|date}"), ("Prórroga automática", "{local!acuerdo.prorrogaAutomatica|map:siNo}")]),
    revisa("Tercero", 2, [("Razón social", "{local!acuerdo.tercero}"), ("CIF/NIF", "{local!acuerdo.cifNifTercero}"), ("Tipo de tercero", "{local!acuerdo.tipoTercero}")]),
    revisa("Condiciones económicas", 3, [("Contenido económico", "{local!acuerdo.contenidoEconomico|map:siNo}"), ("Importe", "{local!acuerdo.importe|eur}"), ("Contraprestación", "{local!acuerdo.contraprestacion}", True)]),
    revisa("Documentación", 4, [("Documentos del acuerdo", "{local!acuerdo.docs.name}", True)]),
]
alta = {
    "id": "alta", "title": "Nuevo acuerdo", "type": "form", "pattern": "P04", "ref": ref("PAN-04"), "req": req("PAN-04"),
    "local": {"local!acuerdo": {"titulo": None, "tipoAcuerdo": None, "aeropuertoUnidad": None, "responsableAena": None, "fechaInicio": None, "fechaFin": None, "prorrogaAutomatica": False,
                                "tercero": None, "cifNifTercero": None, "tipoTercero": "Empresa privada", "contenidoEconomico": False, "importe": None, "contraprestacion": None, "docs": []}},
    "assumptions": ["El código ATP-AAAA-NNNN lo pone la aplicación al enviar (HU-07.2); no se muestra en el alta."],
    "interface": {"type": "a!wizardLayout", "style": "DOT_VERTICAL", "contentsWidth": "MEDIUM", "showButtonDivider": True, "backgroundColor": "WHITE",
        "titleBar": {"type": "a!sidebarTemplate", "title": "Nuevo acuerdo", "secondaryText": "Alta de un acuerdo con una tercera parte", "backgroundColor": NAVY, "width": "NARROW_PLUS",
                     "additionalContents": [{"type": "a!richTextDisplayField", "labelPosition": "COLLAPSED", "value": [{"type": "a!richTextIcon", "icon": "info-circle", "color": GREEN}, " ", {"type": "a!richTextItem", "text": "Al enviar, Asesoría Jurídica recibe una tarea de revisión.", "size": "SMALL", "color": "#FFFFFF"}]}]},
        "steps": [
            {"type": "a!wizardStep", "label": "Datos generales", "contents": paso1},
            {"type": "a!wizardStep", "label": "Tercero", "contents": paso2},
            {"type": "a!wizardStep", "label": "Condiciones económicas", "contents": paso3},
            {"type": "a!wizardStep", "label": "Documentación", "contents": paso4},
            {"type": "a!wizardStep", "label": "Resumen", "contents": paso5},
        ],
        "secondaryButtons": [secondary("Cancelar", {"goto": "acuerdos"}, confirmHeader="¿Descartar el alta?", confirmMessage="Se perderán los datos introducidos.", confirmButtonLabel="Descartar", cancelButtonLabel="Seguir editando")],
        "primaryButtons": [primary("Enviar a revisión", {"goto": "acuerdos", "params": {"mensaje": "Acuerdo ATP-2026-0017 enviado a revisión jurídica"}}, submit=True,
                                   **{"$note": "HU-07.1: el acuerdo pasa a «En revisión jurídica» y Asesoría Jurídica recibe la tarea (AV-01; correo pendiente: PC-11)."})],
    },
}

# ------------------------------------------------------------------ P05 Tarea de aprobación (PAN-05, ACT-02)
revision = {
    "id": "revision", "title": "Revisar acuerdo", "type": "form", "pattern": "P05", "ref": ref("PAN-05"), "req": req("PAN-05"), "recordType": RT,
    "local": {"local!decision": None, "local!comentarios": None},
    "interface": {"type": "a!formLayout", "contentsWidth": "WIDE", "backgroundColor": "WHITE", "showButtonDivider": True, "isButtonFooterFixed": True,
        "titleBar": {"type": "a!headerTemplateSimple", "title": "Revisar acuerdo {rv!record.codigo}", "secondaryText": "Tarea de Asesoría Jurídica · recibida el 02/09/2026", "stampIcon": "gavel", "stampColor": "ACCENT"},
        "contents": [
            action_banner("Vence el 26/09/2026, en 2 días", "Resuelva la revisión antes de esa fecha", kind="WARN", icon="clock-o", marginBelow="MORE",
                          **{"$assumption": "Pendiente: PC-10. Plazo de la revisión y qué pasa si vence."}),
            {"type": "a!columnsLayout", "spacing": "SPARSE", "columns": [
                {"type": "a!columnLayout", "width": "3X", "contents": [
                    {"type": "a!sectionLayout", "label": "Datos del acuerdo", "labelSize": "MEDIUM", "labelHeadingTag": "H2", "labelColor": "STANDARD", "contents": field_summary([("Título", "{rv!record.titulo}", True), ("Tipo de acuerdo", "{rv!record.tipoAcuerdo}"), ("Tercero", "{rv!record.tercero} ({rv!record.cifNifTercero})"),
                                                                   ("Vigencia", "{rv!record.fechaInicio|date} – {rv!record.fechaFin|date}"), ("Importe", "{rv!record.importe|eur|dash}"), ("Responsable AENA", "{rv!record.responsableAena|map:usuarios}")], columns=3)},
                    {"type": "a!sectionLayout", "label": "Texto del acuerdo", "labelSize": "MEDIUM", "labelHeadingTag": "H2", "labelColor": "STANDARD", "marginBelow": "NONE", "contents": [{"type": "a!documentViewerField", "labelPosition": "COLLAPSED", "$fileName": "{rv!record.codigo}_texto_acuerdo.pdf", "height": "SHORT"}]},
                ]},
                {"type": "a!columnLayout", "width": "2X", "contents": [{"type": "a!cardLayout", "showBorder": True, "shape": "SEMI_ROUNDED", "padding": "MORE", "borderColor": "STANDARD", "contents": [
                    {"type": "a!sectionLayout", "label": "Decisión", "labelSize": "MEDIUM", "labelHeadingTag": "H2", "labelColor": "STANDARD", "contents": [
                        choice_cards("Resultado de la revisión", [
                            {"id": "APROBAR", "texto": "Aprobar", "detalle": "El acuerdo pasa a «Pendiente de firma»", "icono": "check-circle", "color": "POSITIVE"},
                            {"id": "DEVOLVER", "texto": "Devolver para cambios", "detalle": "El gestor recibe los comentarios", "icono": "undo", "color": "#FF9F2F"},
                            {"id": "RECHAZAR", "texto": "Rechazar", "detalle": "El acuerdo queda «Rechazado»", "icono": "times-circle", "color": "NEGATIVE"}],
                            "local!decision", labelPosition="COLLAPSED", required=True, requiredMessage="Indique el resultado de la revisión",
                            **{"$assumption": "Pendiente: PC-01 (qué pasa tras aprobar) y PC-07 (cómo vuelve al gestor al devolver)."}),
                        par("Comentarios", "local!comentarios", required="and(a!isNotNullOrEmpty(local!decision), local!decision <> \"APROBAR\")", instructions="Obligatorios si no se aprueba", **{"$note": "HU-10.2: comentario obligatorio al devolver o rechazar."}),
                    ]}]}]},
            ]},
        ],
        "buttons": bl(primary("Enviar decisión", {"goto": "inicio"}, submit=True), [secondary("Cancelar", {"back": True})]),
    },
}

# ------------------------------------------------------------------ P07 Diálogos (PAN-06, PAN-07)
editar = dialog("editar", "Editar datos generales", [
        txt("Título", "local!titulo", required=True, characterLimit=200, showCharacterCount=True),
        cols(dd("Tipo de acuerdo", TIPOS, "local!tipo", required=True), dd("Aeropuerto o unidad", AEROPUERTOS_L, "local!apt", AEROPUERTOS, required=True)),
        {"type": "a!pickerFieldUsers", "label": "Responsable AENA", "maxSelections": 1, "value": "local!resp", "saveInto": "local!resp", "required": True},
        cols(date("Fecha de inicio", "local!ini", required=True), date("Fecha de fin", "local!fin", required=True, **{"$validations": rb01("local!fin", "local!ini"), "$note": NOTA_RB01})),
        {"type": "a!booleanCheckboxField", "choiceLabel": "Prórroga automática al vencimiento", "value": "local!prorroga", "saveInto": "local!prorroga"},
    ], bl(primary("Guardar", {"close": True}, submit=True)), req("PAN-06"), ref("PAN-06"), width="MEDIUM", openFrom="acuerdo", recordType=RT,
    local={"local!titulo": "{rv!record.titulo}", "local!tipo": "{rv!record.tipoAcuerdo}", "local!apt": "{rv!record.aeropuertoUnidad}", "local!resp": "{rv!record.responsableAena}",
           "local!ini": "{rv!record.fechaInicio}", "local!fin": "{rv!record.fechaFin}", "local!prorroga": "{rv!record.prorrogaAutomatica}"},
    assumptions=["Pendiente: PC-06. En qué estados se pueden editar los datos generales."])
DOC_TIPOS = ["Texto del acuerdo", "Memoria justificativa", "Informe jurídico", "Acuerdo firmado", "Otro"]
documento = dialog("documento", "Añadir documento", [
        dd("Tipo de documento", DOC_TIPOS, "local!tipoDoc", required=True, **{"$assumption": "Pendiente: PC-15. Si se guarda el tipo de cada documento y qué tipos hay."}),
        upload("Fichero", "local!ficheros", required=True, maxSelections=1, instructions="PDF o DOCX, máximo 10 MB", **{"$note": NOTA_RB02}),
    ], bl(primary("Añadir", {"close": True}, submit=True)), req("PAN-07"), ref("PAN-07"), openFrom="acuerdo", recordType=RT,
    local={"local!tipoDoc": None, "local!ficheros": []})

# ------------------------------------------------------------------ P08 Informe (PAN-08)
FT = "or(isnull(local!tipo), fv!row.tipoAcuerdo = local!tipo)"
altas_mes = {}
for a in acuerdos:
    if a["fechaAlta"] >= "2025-10": altas_mes[a["mesAlta"]] = altas_mes.get(a["mesAlta"], 0) + 1
media = round(sum(altas_mes.values()) / len(altas_mes), 1)  # media de los meses del gráfico
G_MES = {"type": "a!lineChartField", "labelPosition": "COLLAPSED", "data": f"recordType!{RT}", "$filter": "and(" + FT + ", fv!row.fechaAlta >= \"2025-10\")", "height": "SHORT",
         "config": {"type": "a!lineChartConfig", "primaryGrouping": {"type": "a!grouping", "field": F("mesAlta"), "interval": "MONTH_SHORT_TEXT"}, "measures": [{"type": "a!measure", "function": "COUNT", "field": F("id"), "label": "Altas"}]},
         "referenceLines": [{"type": "a!chartReferenceLine", "label": f"Media: {str(media).replace('.', ',')}", "value": media, "color": "BLUEGRAY", "style": "DASH"}],
         "colorScheme": {"type": "a!colorSchemeCustom", "colors": ["#527500"]}}
G_TIPO = {"type": "a!pieChartField", "labelPosition": "COLLAPSED", "data": f"recordType!{RT}", "$filter": FT, "style": "DONUT", "height": "SHORT", "showTooltips": True, "showDataLabels": True, "$categories": TIPOS,
          "config": {"type": "a!pieChartConfig", "primaryGrouping": {"type": "a!grouping", "field": F("tipoAcuerdo")}, "measures": [{"type": "a!measure", "function": "COUNT", "field": F("id"), "label": "Acuerdos"}]},
          "colorScheme": {"type": "a!colorSchemeCustom", "colors": CHART[:4]}}
G_ESTADO = dict(estados_chart("a!columnChartField"), **{"$filter": FT})
G_IMPORTE = {"type": "a!barChartField", "labelPosition": "COLLAPSED", "data": f"recordType!{RT}", "$filter": "and(" + FT + ", fv!row.contenidoEconomico)", "height": "AUTO", "showDataLabels": True, "xAxisTitle": "Importe (€)",
             "config": {"type": "a!barChartConfig", "primaryGrouping": {"type": "a!grouping", "field": F("aeropuertoUnidad")}, "measures": [{"type": "a!measure", "function": "SUM", "field": F("importe"), "label": "Importe"}]},
             "colorScheme": {"type": "a!colorSchemeCustom", "colors": ["#527500"]}}
informe = {
    "id": "informes", "title": "Informes", "type": "page", "pattern": "P08", "ref": ref("PAN-08"), "req": req("PAN-08"),
    "local": {"local!tipo": None, "local!tablaMes": False, "local!tablaTipo": False, "local!tablaEstado": False, "local!tablaImporte": False},
    "interface": {"type": "a!headerContentLayout", "backgroundColor": BG, "contents": [
        page_header("Informes", "Evolución y distribución de los acuerdos con terceras partes"),
        content_card([{"type": "a!columnsLayout", "alignVertical": "BOTTOM", "columns": [
            {"type": "a!columnLayout", "width": "MEDIUM", "contents": [dd("Tipo de acuerdo", TIPOS, "local!tipo", placeholder="Todos los tipos", marginBelow="NONE")]},
            {"type": "a!columnLayout", "contents": [{"type": "a!buttonArrayLayout", "marginBelow": "NONE", "buttons": [{"type": "a!buttonWidget", "label": "Quitar filtro", "style": "LINK", "showWhen": "a!isNotNullOrEmpty(local!tipo)", "saveInto": [{"type": "a!save", "target": "local!tipo", "value": None}]}]}]},
        ]}], marginBelow="MORE", **{"$assumption": "Propuesta: filtrar el informe por tipo de acuerdo. PAN-08 no lo pide."}),
        kpi_strip([
            kpi("Acuerdos", "handshake-o", sec_text="en el filtro", data=f"recordType!{RT}", primaryMeasure={"type": "a!measure", "function": "COUNT", "field": F("id")}, **{"$filter": FT}),
            kpi("Vigentes", "check-circle", sec_text="en el filtro", data=f"recordType!{RT}", primaryMeasure={"type": "a!measure", "function": "COUNT", "field": F("id")}, **{"$filter": "and(" + FT + ", fv!row.estado = \"Vigente\")"}),
            kpi("Importe total", "eur", sec_text="acuerdos con contenido económico", data=f"recordType!{RT}", primaryMeasure={"type": "a!measure", "function": "SUM", "field": F("importe")}, **{"$filter": FT, "$format": "eur"}),
        ], **{"$assumption": "Propuesta: totales del filtro. PAN-08 no los pide."}),
        section_card("Altas por mes", [chart_table("local!tablaMes", G_MES, "Mes")]),
        {"type": "a!columnsLayout", "columns": [
            {"type": "a!columnLayout", "contents": [section_card("Acuerdos por tipo", [chart_table("local!tablaTipo", G_TIPO, "Tipo de acuerdo")])]},
            {"type": "a!columnLayout", "contents": [section_card("Acuerdos por estado", [chart_table("local!tablaEstado", G_ESTADO, "Estado")])]},
        ]},
        section_card("Importe por aeropuerto", [chart_table("local!tablaImporte", G_IMPORTE, "Aeropuerto o unidad", fmt="eur")]),
    ]},
}

screens = [inicio, listado, registro, alta, revision, editar, documento, informe]
v = FUN.version("F")
spec = {
    "app": {"name": "Acuerdos con Terceras Partes", "shortName": "ATP", "version": "0.1", "language": "es", "today": TODAY.isoformat(), "appianVersion": "26.9",
            "$assumption": "Versión de Appian sin confirmar: el análisis no tiene especificación técnica (técnico §0). Se prototipa con 26.9.",
            "source": f"analisis/funcional.md v{v[0]}.{v[1]} (modo fiel de la ERS de ejemplo, FU-01) · datos ficticios"},
    "site": {"displayName": "Acuerdos con Terceras Partes", "home": "inicio", "user": {"name": uname["lfernandez"]},
             "pages": [
                 {"title": "Inicio", "icon": "home", "screen": "inicio", "includes": ["revision"]},
                 {"title": "Acuerdos", "icon": "handshake-o", "screen": "acuerdos", "includes": ["acuerdo", "alta"]},
                 {"title": "Informes", "icon": "bar-chart", "screen": "informes"}]},
    "requirements": requisitos(),
    "openQuestions": preguntas(screens) + [
        {"id": "Q-01", "text": "¿Qué versión de Appian tiene el entorno? Va en técnico §0; el prototipo usa 26.9."}],
    "maps": {
        "estadoColor": state_map(ATP_ESTADOS),
        "estadoColorGrid": state_map(ATP_ESTADOS, grid=True),
        "plazoColor": {"true": STATES["atencion"]["tag"], "*": STATES["neutral"]["tag"]},
        "estadoPaso": {"Borrador": 1, "En revisión jurídica": 2, "Pendiente de firma": 3, "Vigente": 4, "Vencido": 5, "Rechazado": 2},
        "siNo": {"true": "Sí", "false": "No", "*": "No"},
        "usuarios": uname},
    "users": users,
    "groups": groups,
    "data": {
        "acuerdos": {"recordType": RT, "rows": acuerdos},
        "tareas": {"recordType": "ATP Tarea", "rows": tareas},
        "documentos": {"recordType": "ATP Documento", "rows": documentos},
        "eventos": {"recordType": "ATP Evento", "rows": eventos}},
    "screens": screens,
    "captures": [
        {"name": "01-inicio", "screen": "inicio"},
        {"name": "02-acuerdos", "screen": "acuerdos"},
        {"name": "03-ficha-resumen", "screen": "acuerdo", "params": {"id": 3}},
        {"name": "04-ficha-documentos", "screen": "acuerdo", "params": {"id": 3}, "view": "documentos"},
        {"name": "05-ficha-historial", "screen": "acuerdo", "params": {"id": 4}, "view": "historial"},
        {"name": "06-alta-errores", "screen": "alta", "step": 0, "showValidation": True},
        {"name": "07-alta-importe", "screen": "alta", "step": 2, "caption": "paso 3, con contenido económico", "state": {"local!acuerdo": {"contenidoEconomico": True, "importe": 96000, "contraprestacion": "Cesión de espacios para puntos de recarga"}}},
        {"name": "08-alta-resumen", "screen": "alta", "step": 4, "caption": "paso 5, resumen antes de enviar", "state": {"local!acuerdo": {
            "titulo": "Contrato de colaboración para movilidad eléctrica en aparcamientos", "tipoAcuerdo": "Contrato de colaboración", "aeropuertoUnidad": "VLC", "responsableAena": ["rsanchez"],
            "fechaInicio": "2026-12-01", "fechaFin": "2030-11-30", "prorrogaAutomatica": True, "tercero": "Recarga Urbana Movilidad S.L.", "cifNifTercero": "B42990110", "tipoTercero": "Empresa privada",
            "contenidoEconomico": True, "importe": 96000, "contraprestacion": "Cesión de espacios para puntos de recarga", "docs": [{"name": "Borrador contrato movilidad eléctrica.pdf", "size": "412 KB"}]}}},
        {"name": "09-revision-devolver", "screen": "revision", "params": {"id": 6}, "caption": "devolver para cambios", "state": {"local!decision": "DEVOLVER", "local!comentarios": "Justifique el importe en la memoria."}},
        {"name": "10-editar", "screen": "editar", "hostParams": {"id": 3}, "params": {"id": 3}},
        {"name": "11-documento", "screen": "documento", "hostParams": {"id": 3}, "params": {"id": 3}},
        {"name": "12-informe", "screen": "informes"}],
}
json.dump(spec, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("ok", len(acuerdos), "acuerdos ·", len(spec["requirements"]), "requisitos ·", len(spec["openQuestions"]), "preguntas")
