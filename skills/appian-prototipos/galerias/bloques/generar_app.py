"""Genera galerias/bloques/app.json: galería navegable de los bloques del kit (scripts/sail_helpers.py, references/bloques.md).
Cada bloque aparece con su nombre, cuándo usarlo y un ejemplo real. Versión de Appian 26.9.
Uso: python3 generar_app.py app.json"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from sail_helpers import *  # noqa: E402,F401

# ------------------------------------------------------------------ datos de ejemplo (ficticios)
inc = [
    (1, "INC-2026-0412", "Fuga de agua en el falso techo del vestíbulo", "Mantenimiento", "NOR", "En curso", "Alta", "Goteo continuo sobre los puestos de recepción 1 a 4; se han colocado cubos y se ha acotado la zona a la espera del equipo de cubiertas, que revisará la impermeabilización de la lucernaria."),
    (2, "INC-2026-0415", "Ascensor detenido en el edificio B", "Mantenimiento", "NOR", "Pendiente", "Alta", "El ascensor B-03 se detiene al arrancar; posible fallo del freno de servicio."),
    (3, "INC-2026-0418", "Cola excesiva en el control de accesos principal", "Operaciones", "SUR", "Cerrada", "Media", "Tiempo de espera de 38 minutos entre las 8:00 y las 9:30 por falta de personal en el turno de mañana; se reforzó el turno con dos vigilantes adicionales."),
    (4, "INC-2026-0421", "Pantallas de cartelería sin datos en la planta 2", "Sistemas", "SUR", "En curso", "Media", "Las pantallas de cartelería digital de la planta 2 están en negro desde el cambio de turno."),
    (5, "INC-2026-0423", "Humedad y moho en los aseos de la planta baja", "Limpieza", "EST", "Pendiente", "Baja", "Olor persistente y manchas de humedad en la pared del aseo de caballeros."),
    (6, "INC-2026-0426", "Avería del sistema de climatización en la sala de formación C", "Mantenimiento", "OES", "En curso", "Alta", "Temperatura de 29 °C en la sala; la enfriadora 2 da alarma de alta presión."),
    (7, "INC-2026-0430", "Cajas atascadas en la cinta transportadora del almacén", "Operaciones", "NOR", "Cerrada", "Media", "Cajas atascadas en la curva de la cinta 7; revisada la guía lateral."),
    (8, "INC-2026-0433", "Fallo de la red wifi de visitantes en el edificio 2", "Sistemas", "SUR", "Pendiente", "Media", "Los visitantes no reciben la página de acceso; el controlador inalámbrico se reinicia cada hora."),
]
rows = [{"id": i, "codigo": c, "titulo": t, "area": a, "sede": se, "estado": e, "prioridad": p, "descripcion": d} for i, c, t, a, se, e, p, d in inc]
docs = [{"id": 1, "nombre": "Parte_de_trabajo_PT-118.pdf", "meta": "PDF · 240 KB · Rocío Sánchez · 22/09/2026", "icono": "file-pdf-o"},
        {"id": 2, "nombre": "Fotografias_falso_techo.zip", "meta": "ZIP · 8,1 MB · Pablo Martín · 21/09/2026", "icono": "file-archive-o"},
        {"id": 3, "nombre": "Presupuesto_reparacion.xlsx", "meta": "Excel · 36 KB · Clima Sur S.L. · 20/09/2026", "icono": "file-excel-o"},
        {"id": 4, "nombre": "Informe_inspeccion_cubiertas.docx", "meta": "Word · 118 KB · Lucía Fernández · 19/09/2026", "icono": "file-word-o"}]
comentarios = [{"id": 2, "autor": "Pablo Martín Ortega", "fecha": "2026-09-22T12:40", "texto": "El equipo de cubiertas viene mañana a las 8:00. Dejo la zona acotada."},
               {"id": 1, "autor": "Rocío Sánchez Vidal", "fecha": "2026-09-21T09:15", "texto": "He colocado cubos y avisado a Limpieza para que revise cada hora."}]
ESTADO = state_map({"Pendiente": "atencion", "En curso": "enCurso", "Cerrada": "positivo"})
ESTADO_G = state_map({"Pendiente": "atencion", "En curso": "enCurso", "Cerrada": "positivo"}, grid=True)
SEDES = ["NOR", "SUR", "EST", "OES"]  # sedes de Vadelia, una empresa ficticia
AREAS = ["Mantenimiento", "Sistemas", "Operaciones", "Limpieza", "Seguridad", "Aparcamientos", "Comercial", "Medio ambiente"]


def demo(name, when, contents, card=True):
    """Un bloque de la galería: título H2 con el nombre del helper, cuándo usarlo y el ejemplo."""
    head = [{"type": "a!headingField", "text": name, "size": "MEDIUM", "headingTag": "H2", "marginBelow": "EVEN_LESS"},
            {"type": "a!richTextDisplayField", "labelPosition": "COLLAPSED", "marginBelow": "STANDARD", "value": [{"type": "a!richTextItem", "text": when, "color": "SECONDARY"}]}]
    body = contents if isinstance(contents, list) else [contents]
    return {"type": "a!sectionLayout", "marginBelow": "EVEN_MORE", "contents": head + ([content_card(body)] if card else body)}


def page(sid, title, subtitle, blocks, local=None, crumbs=None):
    return {"id": sid, "title": title, "type": "page", "pattern": "P06", "req": ["B1"], "local": local or {},
            "interface": {"type": "a!headerContentLayout", "backgroundColor": BG, "contents": [page_header(title, subtitle, crumbs=crumbs)] + blocks}}


# ------------------------------------------------------------------ 1. Cabeceras y navegación
p1 = page("cabeceras", "Cabeceras y navegación", "Cómo empieza una página y cómo se mueve el usuario por ella", [
    demo("page_header(…, crumbs=…) · breadcrumbs", "Migas de pan encima del título cuando la página está dentro de una jerarquía (nunca como historial).",
         page_header("INC-2026-0412", "Fuga de agua en el falso techo", [secondary("Editar", icon="pencil"), secondary("Cerrar incidencia")],
                     crumbs=[("Mantenimiento", {"goto": "cabeceras"}), ("Incidencias", {"goto": "listas"}), "INC-2026-0412"], level="H2"), card=False),
    demo("hero_header", "Portada de un módulo o inicio con más presencia: card del color de la barra del site con cifras clave y acciones.",
         hero_header("Mantenimiento de sedes", "Sede Norte de Vadelia", [("wrench", "12", "abiertas"), ("clock-o", "3", "vencen hoy"), ("check-circle", "48", "cerradas este mes")],
                     [primary("Nueva incidencia", icon="plus"), secondary("Ver informes", color="#FFFFFF")], level="H2"), card=False),
    demo("filter_bar", "Filtros que afectan a toda la página (listados, informes). «Borrar filtros» solo si hay más de un filtro.",
         filter_bar([dd("Sede", SEDES, "local!fSede"), dd("Área", AREAS[:4], "local!fArea"),
                     date("Desde", "local!fDesde"), txt("Buscar", "local!fTexto", placeholder="Código o descripción")], clear=["local!fSede", "local!fArea", "local!fDesde", "local!fTexto"])),
    demo("side_nav", "Más de 6 secciones o etiquetas largas con Appian 26.6 (desde 26.7, a!tabLayout vertical). Sin card ni divisor alrededor en fondo gris.",
         side_nav([(a.lower().replace(" ", ""), a, ic) for a, ic in zip(AREAS, ["wrench", "desktop", "cogs", "paint-brush", "shield", "car", "shopping-bag", "leaf"])], "local!seccion",
                  [section_card("Contenido de la sección", [empty_state("folder-open-o", "Sección seleccionada: {local!seccion}", "Aquí va el contenido de la sección.")])]), card=False),
    demo("inline_stats", "Resumen en una línea bajo un título (cabecera de card o de registro).",
         inline_stats([("wrench", "12", "incidencias abiertas"), ("clock-o", "3", "vencen hoy"), ("user", "5", "técnicos de guardia")])),
    demo("action_banner", "Aviso que pide una acción, con el botón dentro. Para avisos informativos sin acción: a!messageBanner.",
         action_banner("3 incidencias vencen hoy", "Revíselas antes de las 14:00 para no incumplir el nivel de servicio.", secondary("Ver incidencias"), kind="WARN"), card=False),
    demo("empty_state", "Lista o sección vacía: icono, qué pasa y el siguiente paso.",
         empty_state("inbox", "No tiene tareas pendientes", "Cuando le asignen una incidencia aparecerá aquí.", secondary("Ver todas las incidencias"))),
], local={"local!seccion": "mantenimiento", "local!fSede": None, "local!fArea": None, "local!fDesde": None, "local!fTexto": None})

# ------------------------------------------------------------------ 2. Datos e indicadores
p2 = page("datos", "Datos e indicadores", "Cifras, hechos clave y progreso", [
    demo("kpi_strip · kpi", "2–4 indicadores en una sola card con divisores; la tendencia compara con el periodo anterior.",
         kpi_strip([kpi("Abiertas", "wrench", "12", 15, "frente a 15 la semana pasada", reverse=True), kpi("Tiempo medio de cierre", "clock-o", "3,2 días", 4.1, "objetivo: 4 días", reverse=True),
                    kpi("Cumplimiento del SLA", "check-circle", "94 %", 91, "objetivo: 95 %")]), card=False),
    demo("kpi_sparkline", "Indicador con su evolución reciente (sin ejes: la tendencia, no el detalle).",
         cols(kpi_sparkline("Incidencias al día", "18", ["L", "M", "X", "J", "V", "S", "D"], [12, 15, 11, 19, 22, 14, 18], sec_text="media semanal: 16"),
              kpi_sparkline("Horas de técnico", "74", ["L", "M", "X", "J", "V", "S", "D"], [60, 64, 70, 66, 71, 58, 74], sec_text="capacidad: 80"), showDividers=True, spacing="SPARSE")),
    demo("kpi_progress", "Avance hacia un objetivo (presupuesto, plan de revisiones).",
         cols(kpi_progress("Revisiones preventivas", "46 de 60", 77, "calendar-check-o", sec_text="plan trimestral"), kpi_progress("Presupuesto ejecutado", "182.400,00 €", 61, "eur", sec_text="de 300.000,00 €"), showDividers=True, spacing="SPARSE")),
    demo("key_facts", "Franja de datos clave de un registro (3–6), debajo de la cabecera.",
         key_facts([("Estado", tag("\"En curso\"", "estado")), ("Prioridad", "Alta"), ("Sede", "NOR"), ("Responsable", "Rocío Sánchez"), ("Plazo", "25/09/2026")]), card=False),
    demo("field_summary", "Resumen de datos fácil de leer (etiqueta encima y valor grande), en 2–3 columnas.",
         field_summary([("Equipo", "Enfriadora 2"), ("Ubicación", "Sala de formación C"), ("Proveedor", "Clima Sur S.L."), ("Descripción", "Alarma de alta presión; temperatura de 29 °C en la sala.", True)])),
    demo("duration", "Tiempo entre dos hitos con aviso si supera el objetivo (SLA).",
         duration("21/09/2026", "25/09/2026", "4 días", late_when="true", late_text="Supera el objetivo de 3 días", goal="Objetivo: 3 días")),
    demo("milestone", "Fase del ciclo de vida de un registro (4–7 fases).",
         milestone(["Abierta", "Asignada", "En reparación", "Verificación", "Cerrada"], "3")),
    demo("stamp_steps", "Explicar un proceso en pocos pasos («Cómo funciona»).",
         stamp_steps([("Comunique la incidencia", "Desde el móvil o el puesto, con foto y ubicación."), ("La asignamos", "El centro de control la envía al equipo adecuado."), ("Siga su estado", "Recibirá un aviso en cada cambio hasta el cierre.")]), card=False),
    demo("checklist", "Comprobaciones pendientes y hechas (preparación de un cierre, requisitos de un alta).",
         checklist([("Parte de trabajo firmado", "true"), ("Fotografías después de la reparación", "true"), ("Conformidad del responsable de la zona", "false")])),
    cols(demo("leaderboard", "Clasificación (quién o qué destaca), con variación.", leaderboard([("Rocío Sánchez Vidal", "38", "+4"), ("Pablo Martín Ortega", "31", "+1"), ("Javier García Ruiz", "27", "-3")], value_label="partes")),
         demo("user_list", "Personas de un equipo o contactos (mejor que un grid).", user_list([("Lucía Fernández Gil", "Jefa de Mantenimiento"), ("Andrés Moreno Pastor", "Técnico de climatización"), ("María López Arranz", "Coordinadora de turnos")]))),
])

# ------------------------------------------------------------------ 3. Listas y grids
cols_inc = [gcol_link("Incidencia", "{fv!row.codigo}", None, "{fv!row.sede} · {fv!row.area}", width="MEDIUM"), gcol("Descripción", "{fv!row.titulo}"), gcol("Estado", tag("fv!row.estado", "estadoGrid"), width="NARROW")]
p3 = page("listas", "Listas y grids", "Consultar, seleccionar y profundizar", [
    demo("grid_with_detail", "Revisar elementos uno tras otro sin cambiar de página: fila resaltada y detalle al lado, con una fila seleccionada al entrar.",
         grid_with_detail("data!incidencias", "local!sel", [gcol("Incidencia", two_line("{fv!row.codigo}", "{fv!row.titulo}")), gcol("Estado", tag("fv!row.estado", "estadoGrid"), width="NARROW")],
                          [subsection("{fv!item.codigo}", [two_line("{fv!item.titulo}", "{fv!item.sede} · {fv!item.area}"), {"type": "a!richTextDisplayField", "labelPosition": "COLLAPSED", "value": ["{fv!item.descripcion}"]}]),
                           {"type": "a!buttonArrayLayout", "align": "END", "buttons": [secondary("Abrir ficha")]}], "No hay incidencias"), card=False),
    demo("grid_with_selection", "Elegir varias filas para una acción en bloque; el panel muestra lo elegido.",
         grid_with_selection("data!incidencias", "local!marcadas", [gcol("Incidencia", two_line("{fv!row.codigo}", "{fv!row.titulo}")), cols_inc[2]], "No hay incidencias", "fv!item.codigo", "Seleccionadas", secondary("Asignar a un técnico", icon="user-plus")), card=False),
    demo("drilldown · drill_link", "Detalle que no cabe al lado: sustituye al grid y «Volver» arriba a la izquierda (nunca el detalle debajo del grid).",
         drilldown("local!abierta", grid("data!incidencias", None, [gcol("Incidencia", drill_link("{fv!row.codigo}", "local!abierta", sub="{fv!row.sede}"), width="NARROW_PLUS"), gcol("Descripción", "{fv!row.titulo}")], "No hay incidencias", page_size=5),
                   [{"type": "a!forEach", "items": "data!incidencias", "$filter": "fv!item.id = local!abierta", "expression": {"type": "a!sectionLayout", "contents": [
                       {"type": "a!headingField", "text": "{fv!item.codigo} · {fv!item.titulo}", "size": "MEDIUM_PLUS", "headingTag": "H3", "marginBelow": "LESS"}, {"type": "a!richTextDisplayField", "labelPosition": "COLLAPSED", "value": ["{fv!item.descripcion}"]}]}}], "Volver a las incidencias")),
    demo("chart_link (drilldown de gráfico)", "Informe en el que se pulsa una barra para ver sus registros debajo.",
         [chart_table("local!tablaArea", {"type": "a!columnChartField", "label": "Incidencias por área (pulse una barra)", "data": "data!incidencias", "height": "SHORT",
           "config": {"type": "a!columnChartConfig", "primaryGrouping": {"type": "a!grouping", "field": "recordType!INC Incidencia.fields.area"}, "measures": [{"type": "a!measure", "function": "COUNT", "field": "recordType!INC Incidencia.fields.id", "label": "Incidencias"}],
                      "link": chart_link("local!areaSel", "INC Incidencia", "area")}}, "Área"),
          {"type": "a!sectionLayout", "showWhen": "a!isNotNullOrEmpty(local!areaSel)", "label": "Incidencias de {local!areaSel}", "labelSize": "SMALL", "labelHeadingTag": "H3", "labelColor": "SECONDARY", "contents": [
              {"type": "a!richTextDisplayField", "labelPosition": "COLLAPSED", "align": "RIGHT", "marginBelow": "LESS", "value": [{"type": "a!richTextIcon", "icon": "times", "color": "ACCENT"}, " ", {"type": "a!richTextItem", "text": "Quitar selección", "style": "STRONG", "linkStyle": "STANDALONE", "link": {"type": "a!dynamicLink", "saveInto": [{"type": "a!save", "target": "local!areaSel", "value": None}]}}]},
              grid("data!incidencias", "fv!row.area = local!areaSel", cols_inc, "No hay incidencias", page_size=5)]}]),
    demo("more_less", "Descripciones de longitud desigual dentro de un grid.",
         grid("data!incidencias", None, [gcol("Incidencia", "{fv!row.codigo}", width="NARROW_PLUS"), gcol("Descripción", more_less("fv!row.descripcion", "local!abiertos"))], "No hay incidencias", page_size=4)),
    cols(demo("document_list", "Biblioteca de documentos con buscador (en vez de un grid).", document_list("local!docs", "local!buscarDoc")),
         demo("comments", "Notas o conversación sobre un caso, del más reciente al más antiguo.", [link_right([("Nuevo comentario", None, "comment-o")]), comments("local!comentarios")])),
    demo("dual_picklist", "Mover elementos entre dos listas medianas (listas cortas: casillas; muy largas: selector).",
         dual_picklist("local!areas", "local!areasSel", "local!marcaIzq", "local!marcaDer", "Áreas disponibles", "Áreas asignadas"), card=False),
    demo("dynamic_inputs", "Lista de valores de longitud variable (correos, matrículas, referencias).",
         dynamic_inputs("local!correos", "Correos de aviso", "Añadir otro correo", placeholder="nombre@example.org")),
], local={"local!sel": [6], "local!marcadas": [2, 5], "local!abierta": None, "local!areaSel": None, "local!tablaArea": False, "local!abiertos": [], "local!docs": docs, "local!buscarDoc": None,
          "local!comentarios": comentarios, "local!areas": AREAS, "local!areasSel": ["Mantenimiento", "Sistemas"], "local!marcaIzq": None, "local!marcaDer": None, "local!correos": ["guardia.norte@example.org", ""]})

# ------------------------------------------------------------------ 4. Cards
p4 = page("cards", "Cards", "Opciones, catálogos y llamadas a la acción", [
    demo("cards_as_buttons", "Pocas opciones o destinos con explicación (portada de módulo, «¿qué quiere hacer?»).",
         cards_as_buttons([("plus-circle", "Comunicar incidencia", "Avise de una avería o un problema en su sede.", {"goto": "cards"}),
                           ("search", "Consultar incidencias", "Busque y siga el estado de cualquier incidencia.", {"goto": "listas"}),
                           ("bar-chart", "Informes", "Tiempos de resolución y cumplimiento del SLA.", {"goto": "datos"})]), card=False),
    demo("cards_as_info", "Catálogo de servicios u opciones con icono, descripción y etiqueta.",
         cards_as_info([("wrench", "Mantenimiento correctivo", "Reparación de averías en instalaciones y equipos.", "24 h"), ("calendar-check-o", "Mantenimiento preventivo", "Revisiones periódicas según el plan anual.", None),
                        ("shield", "Seguridad", "Incidencias en el control de accesos y la vigilancia.", "Crítico"), ("leaf", "Medio ambiente", "Residuos, ruido y consumo energético.", None)]), card=False),
    demo("choice_cards", "Elegir una opción con explicación en un formulario (≤6 opciones).",
         choice_cards("Tipo de incidencia", [{"id": "AV", "texto": "Avería", "detalle": "Algo ha dejado de funcionar", "icono": "wrench"}, {"id": "LI", "texto": "Limpieza", "detalle": "Suciedad o residuos", "icono": "paint-brush"},
                                              {"id": "SE", "texto": "Seguridad", "detalle": "Riesgo para personas", "icono": "shield", "color": "NEGATIVE"}], "local!tipo")),
    demo("call_to_action", "Página con una sola cosa que hacer (primer uso, permisos pendientes).",
         call_to_action("rocket", "Empiece a comunicar incidencias", "Todavía no ha comunicado ninguna. Hágalo en menos de un minuto desde aquí o desde el móvil.", primary("Comunicar incidencia", icon="plus"))),
], local={"local!tipo": None})

# ------------------------------------------------------------------ 5. IA
campos = [{"campo": "Sede", "valor": "OES", "confianza": "ALTA", "origen": "IA", "revisado": True, "pagina": 1},
          {"campo": "Equipo afectado", "valor": "Enfriadora 2", "confianza": "MEDIA", "origen": "IA", "revisado": True, "pagina": 1},
          {"campo": "Importe estimado", "valor": "1.850,00 €", "confianza": "BAJA", "origen": "IA", "revisado": False, "pagina": 2}]
p5 = page("ia", "Inteligencia artificial", "Solo si el análisis lo pide; si no, se propone marcado como supuesto ($assumption)", [
    demo("ai_agent_chat · ai_feedback · ai_notice", "Conversar con un agente que busca, resume o prepara borradores. Lo que propone rellena campos que el usuario revisa y guarda.",
         [content_card([ai_agent_chat("Asistente de incidencias", "agent!INC_INCIDENCIAS", "Puedo buscar incidencias, resumir su historial y preparar el parte de trabajo para que usted lo revise.", height="MEDIUM",
                                          **{"$messages": [{"role": "USER", "text": "¿Qué incidencias de climatización hay abiertas en la sede Oeste?"}, {"role": "TOOL", "tool": "Buscar incidencias", "text": "1 resultado"},
                                                           {"role": "ASSISTANT", "text": "Hay **1 incidencia abierta**: INC-2026-0426, avería de la enfriadora 2 en la sala de formación C (prioridad alta)."}]})], padding="NONE", marginBelow="LESS"),
          cols(ai_notice(marginBelow="NONE"), dict(ai_feedback("local!valoracion"), align="RIGHT"), alignVertical="MIDDLE")], card=False),
    demo("ai_records_chat", "Preguntas sobre un registro concreto, en su vista resumen (mejor en un panel lateral).",
         ai_records_chat("Pregunte por esta incidencia", "recordType!INC Incidencia", 1, "Hola. Puedo responder preguntas sobre esta incidencia: su historial, el equipo afectado o incidencias parecidas.",
                         ["¿Qué se ha hecho hasta ahora?", "¿Hay incidencias parecidas?"], labelPosition="COLLAPSED", height="SHORT")),
    demo("ai_doc_chat · ai_answer · ai_citation", "Preguntar a un documento: la respuesta cita la página y, al pulsarla, el visor la muestra resaltada.",
         ai_doc_chat("Pregunte al pliego", "local!doc", "local!pagina", "local!cita", [("USER", "¿En cuánto tiempo hay que atender una avería crítica?"),
                     ("ASSISTANT", ai_answer("En un **plazo máximo de 2 horas** desde el aviso.", [ai_citation(3, "plazo máximo de 2 horas", "local!pagina", "local!cita")]))],
                     "Pliego_climatizacion_2026.pdf", pages=6, content=[[], [], ["3. Niveles de servicio", "Las averías críticas deberán atenderse en un plazo máximo de 2 horas desde el aviso."]]), card=False),
    demo("ai_review_grid · ai_confidence_tag", "Revisar datos que ha rellenado la IA: origen, confianza y guardado bloqueado hasta revisar los de confianza baja.",
         [cols([ai_review_grid("local!campos", page_var="local!pag", quote_var="local!resaltar"), ai_notice("El botón Guardar se activa cuando estén revisados los datos de confianza baja", marginAbove="STANDARD")],
               {"type": "a!documentViewerField", "label": "Parte escaneado", "labelPosition": "COLLAPSED", "document": "local!parte", "height": "SHORT", "initialPageDisplay": "local!pag", "highlightedText": "local!resaltar",
                "altText": "Parte escaneado", "$fileName": "Parte_PT-2026-118.pdf", "$pages": 2, "$content": [["Parte de trabajo PT-2026-118", "Sede: OES", "Equipo afectado: Enfriadora 2"], ["Importe estimado: 1.850,00 €"]]},
               widths=["3X", "2X"]),
          {"type": "a!buttonArrayLayout", "align": "END", "buttons": [primary("Guardar datos", disabled="contains(local!campos.revisado, false)")]}]),
    demo("match_quality", "Búsqueda por significado en un grid (smartSearchType): calidad de la coincidencia en palabras, nunca la puntuación. Pruebe «goteras».",
         grid("data!incidencias", None, cols_inc + [match_quality("INC Incidencia")], "No hay incidencias que coincidan con la búsqueda", page_size=5, showSearchBox=True, smartSearchType="SEMANTIC", similarityScoreThreshold=0.5)),
], local={"local!valoracion": None, "local!doc": 101, "local!pagina": 3, "local!cita": "plazo máximo de 2 horas", "local!campos": campos, "local!parte": 7, "local!pag": 1, "local!resaltar": None})
# (el chat de datos, a!dataFabricChatField, va en un panel lateral a página completa: ver galerias/ia o el patrón P11)

# ------------------------------------------------------------------ 6. Patrones nuevos del SAIL Design System 26.9
eventos = [{"id": k + 1, "fecha": f, "hora": hh, "titulo": ti, "tipo": tp, "detalle": de} for k, (f, hh, ti, tp, de) in enumerate([
    ("2026-09-21", "09:00", "Coordinación del plan de invierno", "Evento", "Jefaturas de las sedes Norte y Sur"),
    ("2026-09-23", "23:59", "Entrega del plan de invierno", "Plazo", "Documento consolidado a la Dirección de Operaciones"),
    ("2026-09-24", "08:30", "Simulacro de evacuación del edificio A", "Evento", "Vestíbulo y plantas 1 a 3"),
    ("2026-09-24", "12:00", "Revisión del plan de prevención", "Evento", "Sala de juntas, edificio de servicios generales"),
    ("2026-09-24", "14:00", "Refuerzo en el control de accesos", "Turno", "Dos vigilantes adicionales de 14:00 a 22:00"),
    ("2026-09-25", "18:00", "Cierre de ofertas de limpieza", "Plazo", "Licitación de limpieza del edificio 2"),
    ("2026-09-29", "10:00", "Visita de la dirección a la sede Este", "Evento", "Recorrido por las obras del edificio principal"),
    ("2026-09-30", "23:00", "Corte nocturno de la electricidad del edificio A", "Evento", "Mantenimiento del cuadro general hasta las 05:00"),
    ("2026-10-02", "09:00", "Auditoría de seguridad y salud", "Evento", "Auditoría interna anual"),
    ("2026-10-05", "23:59", "Informe mensual del nivel de servicio", "Plazo", "Datos de septiembre de todas las sedes"),
    ("2026-10-14", "07:00", "Turno especial del puente de octubre", "Turno", "Refuerzo de personal en las sedes Sur y Norte")])]
tipos_trabajo = dict(zip(["Mantenimiento", "Sistemas", "Seguridad", "Operaciones"], [CHART[1], CHART[2], CHART[3], CHART[0]]))  # tintes de la paleta de gráficos, sin rojo (rojo = negativo)
tareas_k = [{"id": k + 1, "titulo": ti, "descripcion": de, "tipo": tp, "tipoColor": tipos_trabajo[tp], "responsable": rs, "fecha": fe, "avance": av, "estado": es} for k, (ti, de, tp, rs, fe, av, es) in enumerate([
    ("Revisar enfriadora 2 de la sala C", "Presión de condensación alta tras la sustitución del presostato", "Mantenimiento", "Irene Vega", "2026-09-28", 0, "Pendiente"),
    ("Actualizar el firmware de la cartelería", "Pantallas de las plantas 1 a 3", "Sistemas", "Hugo Romero", "2026-10-02", 0, "Pendiente"),
    ("Formación de nuevos vigilantes", "Procedimiento de control de accesos y registro de visitas", "Seguridad", "Elena Castro", "2026-09-30", 40, "En curso"),
    ("Sustituir la guía de la cinta 7", "Pieza recibida del proveedor; montaje en turno de noche", "Mantenimiento", "Sergio Ortiz", "2026-09-26", 70, "En curso"),
    ("Plan de invierno de la sede Sur", "Consolidado y enviado a la Dirección de Operaciones", "Operaciones", "Javier García", "2026-09-23", 100, "Hecho")])]
hilo = [   # comentarios de primer nivel del más reciente al más antiguo; las respuestas, en orden de llegada
    {"id": 4, "autor": "Lucía Fernández Gil", "fecha": "2026-09-23T16:30", "texto": "¿Podemos reabrir los puestos de recepción 1 a 4 mientras llegan las juntas? Hay mucha cola en el vestíbulo.", "adjuntos": [], "padre": None},
    {"id": 1, "autor": "Rocío Sánchez Vidal", "fecha": "2026-09-22T09:15", "texto": "He colocado cubos y avisado a Limpieza para que revise la zona cada hora. Adjunto las fotos del falso techo.", "adjuntos": [{"nombre": "falso_techo_1.jpg", "tipo": "imagen", "tamano": "1,2 MB"}, {"nombre": "Parte_PT-118.pdf", "tipo": "pdf", "tamano": "240 KB"}], "padre": None},
    {"id": 2, "autor": "Pablo Martín Ortega", "fecha": "2026-09-22T12:40", "texto": "El equipo de cubiertas viene mañana a las 8:00. Dejo la zona acotada.", "adjuntos": [], "padre": 1},
    {"id": 3, "autor": "Andrés Moreno Pastor", "fecha": "2026-09-23T10:05", "texto": "Revisada la impermeabilización de la lucernaria: hay que sustituir dos juntas. Presupuesto en el anexo.", "adjuntos": [{"nombre": "Presupuesto_juntas.xlsx", "tipo": "excel", "tamano": "36 KB"}], "padre": 1}]
p6 = page("patrones269", "Patrones 26.9", "Calendario, hilo de comentarios y tablero kanban del SAIL Design System de Appian 26.9", [
    demo("calendar_month(events, sel_var, today, months, month_var)", "Ver cómo se reparten eventos y plazos en el mes; al pulsar un día, su agenda aparece a la derecha. Hoy resaltado; lo pasado, atenuado.",
         calendar_month("local!eventos", "local!dia", "2026-09-24", months=[(2026, 9), (2026, 10)], month_var="local!mes"), card=False),
    demo("calendar_week(events, start, today)", "Una semana en columnas para comparar días con más detalle. Cada evento lleva el color de su tipo en un tinte suave.",
         calendar_week("local!eventos", "2026-09-21", "2026-09-24"), card=False),
    demo("kanban(var, title, statuses, add_button)", "Seguir tareas por etapas: tipo de trabajo, responsable, fecha y avance; las flechas pasan la tarea a la columna de al lado.",
         kanban("local!tareasK", "Tareas de la semana", add_button=secondary("Añadir tarea", icon="plus")), card=False),
    demo("comment_thread(var, user, new_var, reply_to_var, reply_var)", "Conversación sobre un registro: comentarios con adjuntos, respuestas plegables y cuadro para responder. En una ficha, en su propia columna o al final.",
         comment_thread("local!comentarios", "Lucía Fernández Gil", "local!nuevoComentario", "local!respondiendoA", "local!respuesta"), card=False),
], local={"local!eventos": eventos, "local!dia": "2026-09-24", "local!mes": 1, "local!tareasK": tareas_k, "local!comentarios": hilo,
          "local!nuevoComentario": None, "local!respondiendoA": None, "local!respuesta": None})

pages = [p1, p2, p3, p4, p5, p6]
spec = {"app": {"name": "Bloques del kit", "language": "es", "today": "2026-09-24", "appianVersion": "26.9", "source": "Galería de bloques de scripts/sail_helpers.py (datos ficticios)"},
        "site": {"displayName": "Bloques del kit", "home": "cabeceras", "user": {"name": "Lucía Fernández Gil"},
                 "pages": [{"title": t, "icon": ic, "screen": p["id"]} for p, t, ic in zip(pages, ["Cabeceras", "Datos", "Listas", "Cards", "IA", "Patrones 26.9"], ["header", "tachometer", "table", "th-large", "magic", "calendar"])]},
        "requirements": [{"id": "B1", "title": "Catálogo de bloques de interfaz"}],
        "maps": {"estado": ESTADO, "estadoGrid": ESTADO_G, **AI_MAPS, **event_maps(), **ATTACH_MAPS},
        "data": {"incidencias": {"recordType": "INC Incidencia", "rows": rows}},
        "screens": pages,
        "captures": [{"name": f"{k + 1:02d}-{p['id']}", "screen": p["id"]} for k, p in enumerate(pages)]}
Path(sys.argv[1] if len(sys.argv) > 1 else "app.json").write_text(json.dumps(clean(spec), ensure_ascii=False, indent=1), encoding="utf-8")
print("ok")
