"""Genera galerias/ia/app.json: componentes de IA de Appian en pantallas de ejemplo (agente con propuesta revisable,
listado con búsqueda inteligente y chat de datos en panel, ficha con chat del registro, documento con citas,
revisión de datos sugeridos) y las novedades visuales de 26.7–26.9. Declara appianVersion 26.9 por la última pantalla.
Uso: python3 generar_app.py app.json"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from sail_helpers import *  # noqa: E402,F401

inc = [
    (1, "INC-2026-0412", "Fuga de agua en el falso techo de la zona de facturación", "Mantenimiento", "MAD", "En curso", "Alta", "Goteo continuo sobre los mostradores 812-818; se han colocado cubos y se ha acotado la zona."),
    (2, "INC-2026-0415", "Escalera mecánica detenida en el acceso a la T4S", "Mantenimiento", "MAD", "Pendiente", "Alta", "La escalera 4S-03 se detiene al arrancar; posible fallo del freno de servicio."),
    (3, "INC-2026-0418", "Cola excesiva en el filtro de seguridad norte", "Operaciones", "BCN", "Cerrada", "Media", "Tiempo de espera de 38 minutos entre las 6:00 y las 7:30 por falta de personal."),
    (4, "INC-2026-0421", "Pantallas de información de vuelos sin datos en la puerta B22", "Sistemas", "BCN", "En curso", "Media", "Los monitores FIDS de la puerta B22 muestran la pantalla en negro desde el cambio de turno."),
    (5, "INC-2026-0423", "Humedad y moho en los aseos de llegadas", "Limpieza", "PMI", "Pendiente", "Baja", "Olor persistente y manchas de humedad en la pared del aseo de caballeros."),
    (6, "INC-2026-0426", "Avería del sistema de climatización en la sala de embarque C", "Mantenimiento", "AGP", "En curso", "Alta", "Temperatura de 29 °C en la sala; la enfriadora 2 da alarma de alta presión."),
    (7, "INC-2026-0430", "Pérdida de equipajes en la cinta de recogida 7", "Operaciones", "MAD", "Cerrada", "Media", "Maletas atascadas en la curva de la cinta 7; revisada la guía lateral."),
    (8, "INC-2026-0433", "Fallo de la red wifi de pasajeros en la terminal 2", "Sistemas", "BCN", "Pendiente", "Media", "Los pasajeros no reciben la página de acceso; el controlador inalámbrico se reinicia cada hora."),
    (9, "INC-2026-0436", "Filtración de agua en la cubierta del aparcamiento P1", "Mantenimiento", "PMI", "Pendiente", "Media", "Tras la lluvia aparecen charcos en la planta -1 junto a los pilares 14 y 15."),
    (10, "INC-2026-0439", "Puerta automática bloqueada en la salida de llegadas", "Mantenimiento", "AGP", "Cerrada", "Alta", "La puerta de doble hoja no abre por un sensor sucio; se limpió y se probó."),
]
RESP = ["Rocío Sánchez Vidal", "Pablo Martín Ortega", "Javier García Ruiz", "Andrés Moreno Pastor"]
rows = [{"id": i, "codigo": c, "titulo": t, "area": a, "aeropuerto": ap, "estado": e, "prioridad": p, "descripcion": d,
         "fecha": f"2026-09-{10 + i:02d}", "responsable": RESP[i % len(RESP)]} for i, c, t, a, ap, e, p, d in inc]
ESTADO = state_map({"Pendiente": "atencion", "En curso": "enCurso", "Cerrada": "positivo"})

# ------------------------------------------------------------------ 1. Asistente de agente (a!agentChatField + outputsSaveInto con revisión humana)
asistente = {"id": "asistente", "title": "Asistente de incidencias", "type": "page", "pattern": "P11", "req": ["R1"],
  "local": {"local!propuesta": None, "local!valoracion": None},
  "interface": {"type": "a!headerContentLayout", "backgroundColor": BG, "contents": [
    page_header("Partes de trabajo", "Pida al asistente que prepare el parte de una incidencia y revíselo antes de guardarlo"),
    cols(
      [content_card([ai_agent_chat("Asistente de incidencias", "agent!AENA_INCIDENCIAS", "Puedo buscar incidencias, resumir su historial y preparar el parte de trabajo para que usted lo revise.\n\nPor ejemplo: «¿Qué incidencias de climatización hay abiertas en AGP?»",
          placeholder="Pregunte por una incidencia o pida un parte de trabajo", inputs={"usuario": "loggedInUser()"},
          outputs=[{"type": "a!save", "target": "local!propuesta", "value": "save!value.parte"}], height="TALL",
          **{"$sessions": [{"name": "Incidencias abiertas de climatización en AGP", "messages": [{"role": "USER", "text": "Incidencias abiertas de climatización en AGP"}, {"role": "TOOL", "tool": "Buscar incidencias", "text": "1 resultado"}, {"role": "ASSISTANT", "text": "Hay **1 incidencia abierta**: INC-2026-0426, avería de la enfriadora 2 en la sala de embarque C (prioridad alta)."}]}, "Resumen semanal de Mantenimiento en MAD"],
             "$replies": [{"text": "He preparado el **parte de trabajo** para la INC-2026-0426:\n\n- Revisar la presión de condensación de la enfriadora 2\n- Limpiar el condensador y comprobar el ventilador\n- Medir la temperatura de la sala tras la intervención\n\nLo tiene a la derecha para revisarlo antes de guardarlo.",
                           "tools": [{"tool": "Consultar incidencia", "text": "INC-2026-0426", "input": {"codigo": "INC-2026-0426"}, "output": {"estado": "En curso", "equipo": "Enfriadora 2"}}, {"tool": "Generar parte de trabajo", "input": {"plantilla": "Climatización"}, "output": {"tareas": 3}}],
                           "outputs": {"parte": {"incidencia": "INC-2026-0426", "equipo": "Enfriadora 2 · Sala de embarque C", "tareas": "Revisar la presión de condensación; limpiar el condensador y comprobar el ventilador; medir la temperatura de la sala", "horas": 3}}}]})], padding="NONE")],
      [{"type": "a!sectionLayout", "label": "Parte propuesto", "labelSize": "MEDIUM", "labelHeadingTag": "H2", "labelColor": "STANDARD", "contents": [
          empty_state("magic", "Aún no hay parte propuesto", "Pida al asistente que prepare el parte de una incidencia", showWhen="a!isNullOrEmpty(local!propuesta)"),
          content_card([
              ai_notice("Borrador generado con IA: revíselo antes de guardarlo"),
              ro("Incidencia", "{local!propuesta.incidencia}"), ro("Equipo", "{local!propuesta.equipo}"),
              par("Tareas", "local!propuesta.tareas", height="SHORT"), cols({"type": "a!integerField", "label": "Horas estimadas", "value": "local!propuesta.horas", "saveInto": "local!propuesta.horas"}, []),
              ai_feedback("local!valoracion", marginBelow="STANDARD"),
              {"type": "a!buttonArrayLayout", "align": "END", "marginBelow": "NONE", "buttons": [secondary("Descartar", {"set": {"local!propuesta": None}}), primary("Guardar parte")]}], showWhen="a!isNotNullOrEmpty(local!propuesta)")]}],
      widths=["AUTO", "MEDIUM_PLUS"])]}}

# ------------------------------------------------------------------ 2. Listado con búsqueda inteligente + Data Fabric Chatbot en pane
listado = {"id": "incidencias", "title": "Incidencias", "type": "page", "pattern": "P01", "req": ["R1"], "chrome": True,
  "local": {"local!asistente": True},
  "interface": ai_side_pane(
      [page_header("Incidencias", "Busque por significado: «goteras», «no funciona el aire»…", ai_toggle("local!asistente")),
       content_card([grid("data!incidencias", None, [
           gcol_link("Incidencia", "{fv!row.codigo}", {"goto": "incidencia", "params": {"id": "{fv!row.id}"}}, "{fv!row.aeropuerto} · {fv!row.area}", width="MEDIUM"),
           gcol("Descripción", two_line("{fv!row.titulo}", "{fv!row.descripcion}", strong=False)),
           gcol("Estado", tag("fv!row.estado", "estadoGrid"), width="NARROW"),
           match_quality("AENA Incidencia")], "No hay incidencias que coincidan con la búsqueda",
           showSearchBox=True, smartSearchType="SEMANTIC", similarityScoreThreshold=0.5)])],
      ai_data_chat("Pregunte a sus datos", ["recordType!AENA Incidencia"], [
          ("¿Cuántas incidencias hay pendientes por aeropuerto?", "list", "ACCENT"),
          ("¿Qué área acumula más incidencias de prioridad alta?", "bar-chart", "ACCENT"),
          ("Resume las incidencias abiertas de Mantenimiento", "file-text-o", "ACCENT")],
          **{"$replies": ["Hay **5 incidencias pendientes**:\n\n- MAD: 1\n- BCN: 1\n- PMI: 2\n- AGP: 1", "**Mantenimiento** acumula 4 de las 5 incidencias de prioridad alta."]}),
      "local!asistente")}

# ------------------------------------------------------------------ 3. Ficha con Records Chatbot
ficha = {"id": "incidencia", "title": "{rv!record.codigo} · {rv!record.titulo}", "type": "record", "pattern": "P02", "recordType": "AENA Incidencia", "req": ["R1"],
  "breadcrumb": {"label": "Incidencias", "goto": "incidencias"}, "headerBackgroundColor": NAVY,
  "views": [{"id": "resumen", "label": "Resumen", "interface": {"type": "a!headerContentLayout", "backgroundColor": BG, "contents": [
      key_facts([("Estado", tag("rv!record.estado", "estado")), ("Prioridad", "{rv!record.prioridad}"), ("Aeropuerto", "{rv!record.aeropuerto}"), ("Área", "{rv!record.area}")],
                extra=milestone(["Pendiente", "En curso", "Cerrada"], "{rv!record.estado|map:estadoPaso}")),
      cols([section_card("Datos de la incidencia", field_summary([("Descripción", "{rv!record.descripcion}", True), ("Comunicada", "{rv!record.fecha|date}"), ("Responsable", "{rv!record.responsable}")], columns=2))],
           [{"type": "a!sectionLayout", "label": "Pregunte por esta incidencia", "labelSize": "MEDIUM", "labelHeadingTag": "H2", "labelColor": "STANDARD", "contents": [
               ai_records_chat("Asistente", "recordType!AENA Incidencia", "rv!record.id", "Hola. Puedo responder preguntas sobre esta incidencia: su historial, el equipo afectado o incidencias parecidas.",
                               ["¿Qué se ha hecho hasta ahora?", "¿Hay incidencias parecidas en otros aeropuertos?"], labelPosition="COLLAPSED",
                               **{"$replies": ["Se acotó la zona y se colocaron cubos. Está **pendiente la visita del equipo de cubiertas**, prevista para mañana a las 8:00."]}),
               ai_notice(marginAbove="LESS")]}], widths=["AUTO", "MEDIUM_PLUS"])]}},
            {"id": "historial", "label": "Historial", "interface": {"type": "a!headerContentLayout", "backgroundColor": BG, "contents": [content_card([
                {"type": "a!eventHistoryListField", "labelPosition": "COLLAPSED", "eventStyle": "TIMELINE", "$events": [
                    {"event": "Asignada al equipo de cubiertas", "user": "{rv!record.responsable}", "timestamp": "{rv!record.fecha}T11:20"},
                    {"event": "Incidencia comunicada", "user": "Centro de control", "timestamp": "{rv!record.fecha}T08:40"}]}], padding="MORE")]}}]}

# ------------------------------------------------------------------ 4. Documento + chat con cita (initialPageDisplay + highlightedText)
pag = [["1. Objeto", "El presente pliego regula el servicio de mantenimiento preventivo y correctivo de las instalaciones de climatización de las terminales."],
       ["2. Alcance", "Incluye enfriadoras, unidades de tratamiento de aire, fancoils y el sistema de control centralizado.", "Quedan excluidas las instalaciones de los locales comerciales."],
       ["3. Niveles de servicio", "Las averías críticas deberán atenderse en un plazo máximo de 2 horas desde el aviso.", "Las averías no críticas se atenderán en un plazo de 24 horas.", "El incumplimiento reiterado de los plazos dará lugar a penalizaciones."],
       ["4. Penalizaciones", "Cada hora de retraso en una avería crítica supone una penalización del 0,5 % de la facturación mensual.", "El importe máximo de las penalizaciones será del 10 % anual."],
       ["5. Personal", "El adjudicatario dispondrá de un técnico de guardia 24 horas los 365 días del año."],
       ["6. Duración", "El contrato tendrá una duración de dos años prorrogables por un año más."]]
docchat = {"id": "documento", "title": "Consultar pliego", "type": "page", "pattern": "P11", "req": ["R1"],
  "local": {"local!doc": 101, "local!pagina": 3, "local!cita": "plazo máximo de 2 horas", "local!v1": None},
  "interface": {"type": "a!headerContentLayout", "backgroundColor": BG, "contents": [
      page_header("Consultar pliego de climatización", "Las respuestas indican la página de la que salen; pulse la cita para verla en el documento"),
      ai_doc_chat("Pregunte al pliego", "local!doc", "local!pagina", "local!cita", [
          ("USER", "¿En cuánto tiempo hay que atender una avería crítica?"),
          ("ASSISTANT", ai_answer("En un **plazo máximo de 2 horas** desde el aviso. Las no críticas, en 24 horas.",
                                  [ai_citation(3, "plazo máximo de 2 horas", "local!pagina", "local!cita")], "local!v1"))],
          "Pliego_climatizacion_2026.pdf", pages=6, content=pag,
          replies=[{"content": ai_answer("Cada hora de retraso en una avería crítica supone un **0,5 % de la facturación mensual**, con un máximo del 10 % anual.",
                                         [ai_citation(4, "0,5 % de la facturación mensual", "local!pagina", "local!cita")]),
                    "$action": {"set": {"local!pagina": 4, "local!cita": "0,5 % de la facturación mensual"}}}])]}}

# ------------------------------------------------------------------ 5. Revisión de sugerencias de IA (confianza + revisión humana antes de guardar)
campos = [
    {"campo": "Aeropuerto", "valor": "AGP", "confianza": "ALTA", "origen": "IA", "revisado": True, "pagina": 1},
    {"campo": "Equipo afectado", "valor": "Enfriadora 2", "confianza": "ALTA", "origen": "IA", "revisado": True, "pagina": 1},
    {"campo": "Fecha del aviso", "valor": "22/09/2026", "confianza": "MEDIA", "origen": "IA", "revisado": True, "pagina": 2},
    {"campo": "Importe estimado", "valor": "1.850,00 €", "confianza": "BAJA", "origen": "IA", "revisado": False, "pagina": 2},
    {"campo": "Proveedor", "valor": "Clima Sur S.L.", "confianza": "BAJA", "origen": "IA", "revisado": False, "pagina": 3}]
revision = {"id": "revision", "title": "Revisar datos extraídos", "type": "form", "pattern": "P12", "req": ["R1"], "local": {"local!campos": campos, "local!doc": 7, "local!pagina": 1, "local!cita": None},
  "interface": {"type": "a!formLayout", "titleBar": "Revisar datos extraídos del parte", "contentsWidth": "FULL", "backgroundColor": "WHITE", "showButtonDivider": True, "isButtonFooterFixed": True,
    "contents": [
      action_banner("Revise los datos con confianza baja", "La IA ha rellenado 5 campos a partir del parte escaneado. Pulse «Página N» para ver de dónde sale cada dato.", kind="INFO", icon="magic", marginBelow="MORE"),
      cols([ai_review_grid("local!campos", page_var="local!pagina", quote_var="local!cita"),
            ai_notice("El botón Guardar se activa cuando estén revisados los datos de confianza baja", marginAbove="STANDARD")],
           {"type": "a!documentViewerField", "label": "Parte escaneado", "labelPosition": "COLLAPSED", "document": "local!doc", "height": "TALL", "initialPageDisplay": "local!pagina", "highlightedText": "local!cita",
            "altText": "Parte de trabajo escaneado", "$fileName": "Parte_PT-2026-118.pdf", "$pages": 3,
            "$content": [["Parte de trabajo PT-2026-118", "Aeropuerto: AGP", "Equipo afectado: Enfriadora 2"], ["Fecha del aviso: 22/09/2026", "Importe estimado: 1.850,00 €"], ["Proveedor: Clima Sur S.L.", "Firma del técnico"]]},
           widths=["3X", "2X"])],
    "buttons": bl(primary("Guardar datos", disabled="contains(local!campos.revisado, false)"), [secondary("Cancelar")])}}
# ------------------------------------------------------------------ 6. Novedades 26.7–26.9
ventas = [{"id": i, "mes": m, "area": a, "n": n} for i, (m, a, n) in enumerate([(m, a, n) for m in ["2026-06", "2026-07", "2026-08"] for a, n in [("Mantenimiento", 12), ("Sistemas", 7), ("Operaciones", 5)]])]
novedades = {"id": "novedades", "title": "Novedades 26.7–26.9", "type": "page", "pattern": "P06", "req": ["R1"], "local": {"local!doc": None, "local!tab": 1, "local!tablaGrafico": False},
  "interface": {"type": "a!headerContentLayout", "backgroundColor": BG, "contents": [
    page_header("Novedades de Appian 26.7–26.9", "Parámetros visuales nuevos que el prototipo ya dibuja"),
    {"type": "a!tabLayout", "orientation": "VERTICAL", "selectedTab": "local!tab", "tabs": [
      {"type": "a!tabItem", "label": "Contenedores", "icon": "square-o", "contents": [
         cols([{"type": "a!boxLayout", "label": "Caja con borde de acento", "style": "STANDARD", "borderColor": "ACCENT", "borderWeight": "MEDIUM", "labelFontWeight": "BOLD", "contents": [{"type": "a!richTextDisplayField", "value": [{"type": "a!richTextItem", "text": "Texto ligero (LIGHT) ", "style": "LIGHT"}, {"type": "a!richTextItem", "text": "y seminegrita (SEMI_BOLD)", "style": "SEMI_BOLD"}]}]}],
              [section_card("Sección con etiqueta LIGHT", [{"type": "a!richTextDisplayField", "value": ["Card con borde grueso de 26.7 (borderWeight THICK)."]}], card={"showShadow": False, "showBorder": True, "borderWeight": "THICK", "borderColor": "#527500"}, labelFontWeight="LIGHT")])]},
      {"type": "a!tabItem", "label": "Indicadores y subida", "icon": "tachometer", "contents": [
         cols({"type": "a!gaugeField", "label": "Fracción", "percentage": 72, "primaryText": {"type": "a!gaugeFraction", "denominator": 25}, "secondaryText": "partes cerrados"},
              {"type": "a!gaugeField", "label": "Icono", "percentage": 100, "color": "POSITIVE", "primaryText": {"type": "a!gaugeIcon", "icon": "check", "altText": "Completado"}, "secondaryText": "Completado"},
              {"type": "a!gaugeField", "label": "Porcentaje", "percentage": 38, "primaryText": {"type": "a!gaugePercentage"}, "secondaryText": "del plan anual"}),
         {"type": "a!fileUploadField", "label": "Adjuntar parte (zona amplia, botón GHOST)", "value": "local!doc", "saveInto": "local!doc", "dropZoneStyle": "EXPANDED", "buttonStyle": "GHOST", "buttonColor": "ACCENT", "marginAbove": "STANDARD"},
         {"type": "a!linkField", "label": "Enlace a una página del site (a!pageLink)", "links": [{"type": "a!pageLink", "label": "Ir a Incidencias", "page": "sitePage!AENA_INCIDENCIAS.pages.incidencias"}]}]},
      {"type": "a!tabItem", "label": "Gráfico y grafo", "icon": "sitemap", "contents": [
         chart_table("local!tablaGrafico", {"type": "a!columnChartField", "label": "Incidencias por mes y área (pulse la leyenda para filtrar)", "data": "data!ventas", "allowLegendFiltering": True, "height": "SHORT",
          "config": {"type": "a!columnChartConfig", "primaryGrouping": {"type": "a!grouping", "field": "mes", "interval": "MONTH_SHORT_TEXT"}, "secondaryGrouping": {"type": "a!grouping", "field": "area"}, "measures": [{"type": "a!measure", "function": "SUM", "field": "n"}]}}, "Mes", value_labels=["Mantenimiento", "Sistemas", "Operaciones"]),
         {"type": "a!recordKnowledgeGraph", "label": "Relaciones de la incidencia", "recordType": "recordType!AENA Incidencia", "recordIdentifier": 6, "relationshipLevel": 2, "height": "MEDIUM",
          "$root": {"recordType": "Incidencia", "name": "INC-2026-0426", "icon": "wrench"},
          "$nodes": [{"recordType": "Aeropuerto", "name": "AGP", "icon": "plane"}, {"recordType": "Equipo", "name": "Enfriadora 2", "icon": "cog"}, {"recordType": "Parte de trabajo", "name": "PT-2026-118", "icon": "file-text-o"},
                     {"recordType": "Proveedor", "name": "Clima Sur S.L.", "icon": "building", "parent": "PT-2026-118"}, {"recordType": "Técnico", "name": "Rocío Sánchez", "icon": "user", "parent": "PT-2026-118"},
                     {"recordType": "Incidencia", "name": "INC-2026-0301", "icon": "wrench", "parent": "Enfriadora 2"}, {"recordType": "Responsable", "name": "Pablo Martín", "icon": "user"}]}]},
      {"type": "a!tabItem", "label": "Celdas compuestas", "icon": "table", "contents": [
         grid("data!incidencias", None, [
             gcol("Incidencia", {"type": "a!sideBySideLayout", "alignVertical": "MIDDLE", "items": [
                 {"type": "a!sideBySideItem", "width": "MINIMIZE", "item": {"type": "a!richTextDisplayField", "value": [{"type": "a!richTextIcon", "icon": "wrench", "color": "SECONDARY"}]}},
                 {"type": "a!sideBySideItem", "item": {"type": "a!richTextDisplayField", "value": [{"type": "a!richTextItem", "text": "{fv!row.codigo}", "style": "STRONG", "link": {"type": "a!recordLink", "recordType": "recordType!AENA Incidencia", "identifier": "{fv!row.id}"}, "$action": {"goto": "incidencia", "params": {"id": "{fv!row.id}"}}}]}}]}),
             gcol("Título", "{fv!row.titulo}"), gcol("Estado", tag("fv!row.estado", "estadoGrid"), width="NARROW")], "Sin incidencias", page_size=5)]},
      {"type": "a!tabItem", "label": "Estados del chat", "icon": "comments-o", "contents": [
         cols(ai_agent_chat("Respondiendo (botón Detener)", "agent!AENA_INCIDENCIAS", "Pregunte por una incidencia.", height="MEDIUM", shape="FULLY_ROUNDED", showBorder=True, showSessionPicker=False,
                            **{"$messages": [{"role": "USER", "text": "Resume la INC-2026-0426"}, {"role": "TOOL", "tool": "Consultar incidencia", "text": "INC-2026-0426"}], "$state": "RUNNING"}),
              ai_agent_chat("Función no habilitada", "agent!AENA_INCIDENCIAS", "Pregunte por una incidencia.", height="MEDIUM", shape="SEMI_ROUNDED", showBorder=True, **{"$state": "UNAVAILABLE"}),
              ai_agent_chat("Modo depuración (solo en desarrollo)", "agent!AENA_INCIDENCIAS", "Pregunte por una incidencia.", height="MEDIUM", showBorder=True, debugMode=True, showSessionPicker=False,
                            **{"$uxIgnore": "Muestra cómo se ve el modo de depuración; en pantallas de usuario va desactivado.", "$messages": [{"role": "USER", "text": "¿Quién es el técnico?"}, {"role": "TOOL", "tool": "Consultar parte", "input": {"parte": "PT-2026-118"}, "output": {"tecnico": "Rocío Sánchez"}}, {"role": "ASSISTANT", "text": "Rocío Sánchez."}]}))]}]}]}}

spec = {"app": {"name": "Galería IA", "language": "es", "today": "2026-09-24", "appianVersion": "26.9"},
        "site": {"displayName": "Galería IA", "home": "asistente", "user": {"name": "Lucía Fernández Gil"}, "pages": [
            {"title": "Asistente", "icon": "magic", "screen": "asistente"}, {"title": "Incidencias", "icon": "wrench", "screen": "incidencias", "includes": ["incidencia"]},
            {"title": "Pliego", "icon": "file-text-o", "screen": "documento"}, {"title": "Revisión", "icon": "check-square-o", "screen": "revision"}, {"title": "26.7–26.9", "icon": "star", "screen": "novedades"}]},
        "requirements": [{"id": "R1", "title": "Galería de componentes de IA"}],
        "maps": {"estado": ESTADO, "estadoPaso": {"Pendiente": 1, "En curso": 2, "Cerrada": -1}, "estadoGrid": state_map({"Pendiente": "atencion", "En curso": "enCurso", "Cerrada": "positivo"}, grid=True), **AI_MAPS},
        "data": {"incidencias": {"recordType": "AENA Incidencia", "rows": rows}, "ventas": ventas},
        "screens": [asistente, listado, ficha, docchat, revision, novedades],
        "captures": [{"name": "01-asistente", "screen": "asistente"}, {"name": "02-incidencias", "screen": "incidencias"}, {"name": "03-ficha", "screen": "incidencia", "params": {"id": 1}},
                     {"name": "04-documento", "screen": "documento"}, {"name": "05-revision", "screen": "revision"}, {"name": "06-novedades", "screen": "novedades"}] + [{"name": f"06-novedades-{k}", "screen": "novedades", "state": {"local!tab": k}} for k in (2, 3, 4, 5)]}
Path(sys.argv[1] if len(sys.argv) > 1 else "app.json").write_text(json.dumps(clean(spec), ensure_ascii=False, indent=1), encoding="utf-8")
print("ok")
