# Catálogo de bloques de interfaz

Bloques reutilizables para componer pantallas. Cada uno es una función de `scripts/sail_helpers.py` que devuelve
**SAIL real** (solo las claves que empiezan por `$` son del prototipo) y aplica la guía de `design-rules.md`.
Salen de los patrones del *SAIL Design System* y del catálogo *Drag & Drop Patterns* de Appian, adaptados a AENA.

- Galería navegable con un ejemplo de cada bloque: `examples/bloques/` (`generar_app.py` → `app.json` → HTML).
- Los componentes de IA en acción (agente, chat de datos en panel, documento con citas, revisión): `examples/ia/`.
- Los 147 componentes de Appian 26.9, uno a uno: `examples/componentes/`.
- Todos funcionan desde **Appian 26.6** salvo que se indique otra versión (§6 y §7).

Uso en un `generar_app.py`:

```python
import sys; sys.path.insert(0, r"<KIT>/scripts")
from sail_helpers import *
```

Regla general: **elige el bloque por la tarea del usuario**, no por el componente. Si dos bloques valen, el más
sencillo. No mezcles en una pantalla dos bloques que resuelven lo mismo (p. ej. `grid_with_detail` y `drilldown`).

---

## 1. Cabeceras y navegación

| Bloque | Úsalo cuando | No lo uses cuando | Origen |
|---|---|---|---|
| `page_header(title, subtitle, buttons, crumbs, level)` | Toda página: H1 + una línea de descripción + la acción principal a la derecha. `crumbs` añade migas encima. | Formularios y asistentes (el título va en `titleBar`). | Page titles |
| `breadcrumbs(items)` | La página está dentro de una jerarquía (Área › Lista › Registro). `items`: `[("Texto", $action), …, "Actual"]`. | Para «volver atrás» o historial de navegación. | Breadcrumbs |
| `hero_header(title, subtitle, stats, buttons, level)` | Inicio o portada de módulo que necesita presencia: card azul marino con cifras en línea. Sustituye a `page_header`. | Páginas de trabajo diario (listados, fichas): allí, `page_header`. | Hero card header |
| `filter_bar(filters, clear)` | 2–4 filtros que afectan a **toda** la página (informe, listado con varios bloques). | Filtros de un solo grid: usa `userFilters` y la búsqueda del propio grid. | Filter bar header |
| `side_nav(items, var, content)` | Más de 6 secciones o etiquetas largas en proyectos anteriores a 26.7. | 2–6 secciones: `a!tabLayout`. Desde 26.7: `a!tabLayout(orientation: "VERTICAL")`. | Navigation (lightweight) |
| `inline_stats(items)` | Resumen de 2–4 cifras en una línea bajo un título. | Cifras que son el objetivo de la página: `kpi_strip`. | Inline Stats |
| `action_banner(title, text, button, kind)` | Aviso que pide una acción concreta, con el botón dentro. | Avisos solo informativos: `a!messageBanner`. | Action Banner |
| `empty_state(icon, title, text, button)` | Lista, grid o sección sin elementos: qué pasa y siguiente paso. | Grids: basta `emptyGridMessage` concreto. | Full page empty state |

## 2. Datos e indicadores

| Bloque | Úsalo cuando | Detalles |
|---|---|---|
| `kpi_strip([kpi(…)])` | 2–4 indicadores de una página de inicio o informe. | Una card, divisores, barra verde arriba; cada KPI con su icono en un sello de color suave (iconStyle STAMP). `kpi(..., secondary=)` calcula la tendencia; `reverse=True` si bajar es bueno. En columnas estrechas: `template="COMPACT", iconStyle="ICON"`. |
| `kpi_sparkline(text, value, cats, values)` | Importa la evolución reciente, no el detalle. | Línea `MICRO` sin ejes con `accessibilityText` que enumera los valores. |
| `kpi_progress(text, value, pct, icon)` | Avance hacia un objetivo (plan, presupuesto). | KPI `ADJACENT` con icono en sello + barra `THIN`. Devuelve una lista (KPI + barra). |
| `key_facts(items, extra)` | 3–6 datos clave de un registro bajo la cabecera. | Valores vacíos muestran «–». Un tag o avatar puede ser un valor. |
| `field_summary(pairs, columns)` | Resumen de solo lectura fácil de leer (revisión, ficha). | Etiqueta pequeña encima y valor grande; `(etiqueta, valor, True)` ocupa el ancho. |
| `duration(start, end, days, late_when)` | Tiempo entre dos hitos y si supera el objetivo (SLA). | Aviso con icono y texto, nunca solo color. |
| `milestone(steps, active)` | Fase del ciclo de vida (4–7 fases). | `a!milestoneField` LINE; vertical con `orientation="VERTICAL"` si hay muchas fases. |
| `stamp_steps(steps)` | Explicar un proceso en 3–4 pasos («Cómo funciona»). | Cards numeradas con título y explicación. |
| `checklist(items)` | Comprobaciones hechas y pendientes (cierre, requisitos). | Icono + texto; `altText` «Hecho» / «Pendiente». |
| `leaderboard(items)` | Clasificación con variación (quién o qué destaca). | Posición, avatar, valor y cambio con color **e** icono. |
| `user_list(users)` | Equipo o contactos (≤10). | Mejor que un grid para personas. |

## 3. Listas y grids

| Bloque | Úsalo cuando | No lo uses cuando |
|---|---|---|
| `grid(…)` + `gcol*`, `tag`, `two_line` | Consultar muchos registros: ≤7 columnas consolidadas, `LIGHT`, primera columna enlace a la ficha. | – |
| `grid_with_detail(data, sel_var, columns, detail, empty, flt=…)` | Revisar elementos uno tras otro sin cambiar de página (bandejas, colas). Empieza con una fila seleccionada. | El detalle es largo o tiene acciones propias: ficha de registro. |
| `grid_with_selection(data, sel_var, columns, empty, label_expr, …, action)` | Elegir varias filas para una acción en bloque; el panel lista lo elegido y el botón se activa al elegir. | Una sola fila: acción en la ficha. |
| `drilldown(var, grid, detail)` + `drill_link` | El detalle no cabe al lado: sustituye al grid y «Volver» arriba a la izquierda. | Nunca pongas el detalle **debajo** del grid. |
| `chart_link(var, recordType, field)` en `config.link` | Informe en el que se pulsa una barra para ver sus registros (el grid filtra por `var`). | Gráficos decorativos o de un solo valor. |
| `chart_table(var, chart, cat_label)` | Siempre que hay un gráfico: «Ver como tabla» alterna el gráfico y una tabla con sus mismas categorías, medidas y filtros (alternativa accesible, también del drilldown). | Minigráfico de un KPI (`kpi_sparkline`): ya lleva su texto en `accessibilityText`. |
| `more_less(text_expr, var)` | Descripciones de longitud desigual en un grid. | Textos cortos: se muestran enteros. |
| `document_list(items, search_var)` | Biblioteca de documentos con buscador. | Pocos documentos en una ficha: `doc_line`. |
| `comments(items)` | Notas o conversación sobre un caso (más reciente primero). | Historial automático: `a!eventHistoryListField`. |
| `dual_picklist(all, sel, mark_l, mark_r)` | Mover elementos entre dos listas medianas (10–50). | Listas cortas: casillas. Muy largas: un selector (`picker`). |
| `dynamic_inputs(var, label)` | Lista de valores de longitud variable (correos, matrículas). | Registros con varios campos por fila: `a!gridLayout` editable. |

## 4. Cards

| Bloque | Úsalo cuando | Detalles |
|---|---|---|
| `cards_as_buttons(items)` | 2–6 destinos u opciones con explicación (portada de módulo). | Toda la card es el enlace; iconos del mismo estilo. |
| `cards_as_info(items)` | Catálogo de servicios u opciones. | `a!cardGroupLayout` (se reparte solo), sello de color suave, etiqueta opcional. |
| `choice_cards(label, options, var)` | Elegir una opción con explicación en un formulario (≤6). | `a!cardChoiceField` con plantilla de barra; icono de color solo con significado. |
| `call_to_action(icon, title, text, button)` | Página con una sola cosa que hacer (primer uso). | Centrada; un único botón SOLID grande. |

## 5. Inteligencia artificial

Solo si el análisis lo pide. Si la propones tú, márcala con `$assumption` («Propuesta: …») y explica el beneficio.
Reglas completas en `design-rules.md` §14.

| Bloque | Componente | Úsalo cuando |
|---|---|---|
| `ai_agent_chat(title, agent, welcome, …, outputs)` | `a!agentChatField` (26.6) | Un agente busca, resume o prepara borradores. `outputs` rellena campos que el usuario revisa y guarda (nunca guarda la IA). A página completa (`height="FILL"`) o en una card sin relleno junto a la propuesta. |
| `ai_side_pane(main, chat, open_var)` + `ai_toggle(open_var)` + `ai_data_chat(…)` | `a!paneLayout` + `a!dataFabricChatField` | Preguntas sobre los datos de varios record types. El chat va solo en un panel lateral que se muestra u oculta; nada encima ni debajo. |
| `ai_records_chat(label, recordType, id, initial, questions)` | `a!recordsChatField` | Preguntas sobre un registro, en su vista resumen (mejor en un panel lateral o columna derecha). |
| `ai_doc_chat(…)` + `ai_answer` + `ai_citation` | `a!chatField` + `a!documentViewerField` | Preguntar a un documento: chat a la izquierda, visor a la derecha; la cita salta a la página (`initialPageDisplay`) y resalta el texto (`highlightedText`). |
| `ai_review_grid(var, page_var, quote_var)` + `ai_confidence_tag` | `a!gridLayout` | El usuario confirma datos que ha rellenado la IA: origen, confianza, casilla «Revisado» en los de confianza baja y Guardar bloqueado hasta revisarlos (patrón P12). Con `page_var`/`quote_var`, «Página N» lleva el visor de la fuente a esa página y resalta el valor. |
| `match_quality(recordType)` | columna de `a!gridField` con `smartSearchType` | Búsqueda por significado: calidad de la coincidencia en palabras (Exacta, Alta, Media, Baja), nunca la puntuación numérica. |
| `ai_notice()`, `ai_feedback(var)` | texto enriquecido | Junto a toda salida de IA: aviso de que hay que comprobarla y valoración útil / no útil. |

Simulación en el prototipo (claves `$`): `$messages` (conversación ya empezada, con filas `TOOL` para las llamadas a
herramientas), `$replies` (respuestas por turnos: texto con **negrita** y listas, `tools`, `outputs`, `content` con
componentes, `$action`), `$sessions` (conversaciones anteriores del agente) y `$state` (`RUNNING`, `UNAVAILABLE`)
para capturar estados. En el visor: `$fileName`, `$pages`, `$content` (texto de cada página).

## 6. Novedades de 26.7–26.9 (solo con `app.appianVersion` igual o posterior)

| Versión | Qué | Cómo |
|---|---|---|
| 26.7 | Pestañas verticales | `a!tabLayout(orientation: "VERTICAL", showDivider, dividerColor, tabWidth)` en vez de `side_nav`. |
| 26.7 | Bordes y pesos de etiqueta | `a!boxLayout(borderColor, borderWeight, labelFontWeight)`, `a!cardLayout(borderWeight)`, `a!sectionLayout(labelFontWeight)`, `a!richTextItem(style: "LIGHT"/"SEMI_BOLD")`. |
| 26.7 | Chat del agente con forma y borde | `a!agentChatField(shape: "SEMI_ROUNDED", showBorder: true)`; botón Detener mientras responde. |
| 26.8 | Enlace a una página del site | `a!pageLink(label, page, urlParameters)`. |
| 26.8 | Grafo de relaciones de un registro | `a!recordKnowledgeGraph(recordType, recordIdentifier, relationshipLevel, showMiniMap)`; en el prototipo, `$root` y `$nodes`. |
| 26.8 | Filtrar series desde la leyenda | `allowLegendFiltering: true` en gráficos. |
| 26.8 | Botón de subida y de firma | `buttonStyle` `SOLID`/`OUTLINE`/`GHOST`/`LINK` + `buttonColor`. |
| 26.9 | Celdas compuestas en grids | `a!sideBySideLayout` e imágenes múltiples dentro de `a!gridColumn`. |

## 7. Patrones del SAIL Design System 26.9

Fuentes: `sail/calendar.html`, `sail/comment-thread.html` y `sail/kanban.html` de la documentación de Appian 26.9. Solo SAIL de 26.6 o anterior: sirven para cualquier versión de 26.x.

| Bloque | Úsalo cuando | Detalles |
|---|---|---|
| `calendar_month(events, sel_var, today, months, month_var)` | Importa cómo se reparten eventos y plazos a lo largo del mes (turnos, cierres, auditorías, vencimientos). | Rejilla de lunes a domingo con hasta 2 eventos por día y «+N más»; al pulsar un día, su agenda a la derecha. Hoy con tinte verde, días de otro mes en gris, eventos pasados atenuados, estado vacío. `months` + `month_var` añaden flechas de mes. Eventos: `[{fecha, hora, titulo, tipo, detalle}]`; `event_maps()` en `maps` (icono y color por tipo). |
| `calendar_week(events, start, today)` | Comparar pocos días con más detalle (planificación de la semana). | Un día por columna con sus eventos en tarjetas del color del tipo (tinte suave); los días pasados en gris y hoy subrayado. |
| `comment_thread(var, user, new_var, reply_to_var, reply_var)` | Conversación sobre un registro (dudas, decisiones, adjuntos) en su vista o columna de la ficha. | Comentario nuevo arriba («Publicar» se activa al escribir), comentarios con avatar, fecha, adjuntos y «Responder»; respuestas plegables. Datos: `[{id, autor, fecha, texto, adjuntos, padre}]`; `ATTACH_MAPS` en `maps`. En Appian: record type de comentarios (1:N) con `padre`. |
| `kanban(var, title, statuses, add_button)` | El usuario mueve trabajo entre etapas (tareas de mantenimiento, acciones de un plan). | Columnas con cabecera de color (tinte + barra + recuento) y tarjetas con tipo, responsable, fecha, avance y flechas para cambiar de columna. Tareas: `[{id, titulo, descripcion, tipo, tipoColor, responsable, fecha, avance, estado}]`. Máximo 4–5 columnas. |
| `state_chart_colors(mapa, orden)` | Gráfico de barras o columnas por estado. | Un color por estado con el mismo significado que las etiquetas; va con `secondaryGrouping` por el mismo campo, `stacking: "NORMAL"` y `showLegend: false`; con una agrupación secundaria distinta (p. ej. estado dentro de mes), `"$series": orden` fija el color de cada serie. |

Técnicas del prototipo que usan: `$local` en `a!forEach` (variables de cada vuelta, como `a!localVariables`: `{"local!comentario": "fv!item"}`), `$filter` + escritura en `fv!item` (se guarda en la fila original de la lista) y `$action.prepend` / `append` (añadir un elemento evaluando sus `{expresiones}`).

