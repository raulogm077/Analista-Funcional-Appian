# Del análisis funcional (`ddf.md`) al inventario de pantallas

La entrada es el `ddf.md` de `appian-functional-analyst` (modo síntesis, fiel o
actualización; ver SKILL.md, paso 1). Esta fase produce el **inventario de
pantallas**, que se confirma antes de escribir el `app.json`. La lectura de las
fuentes originales ya la ha hecho el analista: aquí no se vuelve a interpretar
el documento del cliente, se traduce el análisis a pantallas.

## 0. Sección del `ddf.md` → spec

| Sección | Va a |
|---|---|
| Sec 1 Fuentes y versión | `app.source` («DF BPM-GI-011-2 v1.04 (FU-01); reunión 03/09 (FU-02)»; versión del análisis) |
| Sec 3 Alcance | Qué módulos entran en el prototipo; lo excluido no se prototipa |
| Sec 5 Actores | Usuario de ejemplo del site (el rol protagonista de la demo), quién ve cada pantalla (`$note`), roles de las tareas P05 |
| Sec 6 Actividades y fichas de tarea (6.3) | Una pantalla P05 por cada tarea de usuario que decide algo (ver abajo); las actividades marcadas «En la aplicación: No» van a `requirements` con `outOfScope: "<motivo>"` |
| Sec 8 Requisitos | `requirements` con el ID y el nombre **literales**, y `req` de cada pantalla |
| Sec 9 Reglas | `$validations`, `required` / `showWhen` condicionales; el mensaje cita la regla («(RB-004)») |
| Sec 10 Modelo de datos | `data`: un dataset por entidad con el nombre de su Record Type y **sus atributos como nombres de campo**; relaciones 1..N como campo `<entidad>Id`; listas de valores → desplegables y datos de ejemplo |
| Sec 11 Estados | `maps.estadoColor`, `maps.estadoPaso`, `a!milestoneField` |
| **Sec 12 Pantallas** | **Una pantalla (o diálogo) por ficha**, ver abajo |
| Sec 15 KPIs e informes | P06 (KPIs) y P08 (informes) |
| Sec 17 Preguntas 🔴🟡🟢 | `openQuestions` con `priority` (`CRITICA`, `IMPORTANTE`, `MEJORA`) |

Ficha de pantalla (Sec 12) → pantalla:

| En la ficha | En la spec |
|---|---|
| ID y nombre (PAN-xx, o el del DF) | `title` y `ref` (`"PAN-03 · Búsqueda de estudios"`); el `ref` enlaza cada captura con su ficha |
| Tipo y propósito | `type` de la pantalla y patrón (§1) |
| Se abre desde | Página del site, botón con `$action.goto`, `recordActions`, tarea |
| Organización | Secciones (`a!sectionLayout`), pestañas, pasos del asistente, tabla agrupada. En una ficha, **cada área 1:N con volumen propio** (documentación, comunicaciones, planificación, historial…) es una **vista del registro** (máximo 7; las áreas pequeñas se agrupan). Nunca una pila de secciones plegables en el resumen (guía §8) |
| Campos | Campos o columnas en ese orden; tipo → componente (§2); obligatorio → `required`; no editable o calculado → `readOnly`; valor por defecto → valor inicial en `local`; «si está vacío» → lo que muestra la celda o el campo (por defecto «–», filtro `dash`). **Listados con más de 7 columnas**: consolida en celdas de dos líneas (`two_line`: código + título, tipología + aeropuerto, paso + fase) sin perder ningún dato. Si aun así sobran, propón llevarlas a la ficha con un `$assumption` y una pregunta abierta para validarlo con el cliente; no las elimines sin decirlo |
| Filtros | Filtros del listado → hasta 4 `userFilters` en la barra del grid, más el buscador. Los filtros predefinidos que se usan a diario («mis informes», «con alertas») → **vistas guardadas** con `a!tabLayout` y el recuento en la etiqueta. Filtros de página que afectan a varios bloques (informes) → barra de filtros en una card (desplegables en fila). Valor por defecto → `local` inicial. No hagas una card-formulario de 8 desplegables encima del grid |
| Ordenación | `initialSorts` del `a!gridField` y `sortField` en las columnas ordenables |
| Acciones | Botones o acciones de registro con el **texto literal**; «quién la ve» → `showWhen`; «cuándo está activa» → `disabled`; «qué pasa después» → `$action` (`goto`, `dialog`, banner con `params`); confirmación → `confirmHeader` / `confirmMessage` literal |
| Reglas de la pantalla | `$validations` con el mensaje literal, `required` / `showWhen` condicionales; visibilidad por perfil → `por_perfil()`: `$note` con el perfil y la capa de seguridad de Appian que lo aplica (registro, vista, acción de registro, campo o visibilidad de interfaz; guía §18) y `showWhen` si la demo debe enseñarlo oculto; cada «Caso A/B» visible en el prototipo → su condición y efecto (banner, campo, botón) |
| Textos literales | `instructions`, `helpTooltip`, mensajes de `$validations` y de confirmación, sin reescribirlos |
| Criterios de aceptación | No van a la spec: son la **lista de comprobación** del paso 4. Los de presentación y validación se comprueban en el prototipo; los que dependen de algo que el prototipo no hace (integraciones, avisos, plazos) se anotan en un `$note` |

Ficha de tarea (Sec 6.3) → pantalla P05 si la tarea decide algo (si solo recoge datos, P03). La ficha de tarea y su ficha de pantalla de la Sec 12 describen la misma pantalla: una sola en el spec, con los dos IDs en `ref` y `req`.

| En la ficha | En la spec |
|---|---|
| Actor, estado de entrada | Tarea en la bandeja del rol; la vista de la tarea muestra el registro en ese estado |
| Opciones | `a!cardChoiceField` con `a!cardTemplateBarTextStacked` en la card «Decisión» (patrón P05, helper `choice_cards`): texto literal de cada opción, su estado de salida como texto secundario e icono de color (aprobar POSITIVE, devolver naranja, rechazar NEGATIVE). «Enviar decisión» las envía |
| Condición de cada opción | `required` condicional o `$validations` (p. ej. comentario obligatorio al devolver) |
| Estado de salida y siguiente | `$action`: vuelta a la bandeja o al registro con un banner («El expediente ha pasado a «Aprobado»») |
| Criterio mínimo de aceptación | Lista de comprobación del paso 4, como los de pantalla |

Nivel de certeza del análisis:
- ✅ Confirmado / 🔶 Inferencia → se prototipa sin marca.
- ⚠️ Pendiente de validación → se prototipa y se marca con `$assumption` («⚠️ RB-007 pendiente de validación»), para que el cliente lo vea en la reunión.
- ❓ No definido → no se inventa: se deja el hueco mínimo con `$assumption` y se añade a `openQuestions`.
- 🔒 Validado → como ✅. Lo tachado (`~~RF-007~~ … Anulado por D-xxx`) no se construye; una pregunta tachada («Respondida») no va a `openQuestions`.
- Tras una actualización del análisis, el informe de impacto (`impacto/FU-xx.md`) lista las «Pantallas afectadas»: se regeneran solo esas y se vuelven a capturar.

Si el análisis no numera algo que el prototipo necesita referenciar, no inventes
IDs en la spec: pide al analista que los asigne en el `ddf.md` (IDs estables) y
úsalos.

## 1. Asignar patrón a cada pantalla

| El documento dice… | Patrón |
|---|---|
| consultar, listar, buscar, filtrar, exportar X | P01 Listado |
| ficha, detalle, consultar un X, ver el expediente | P02 Vista de registro |
| alta / solicitud / registro con ≤ 8 campos o un solo bloque | P03 Formulario |
| alta con varios bloques, > 8 campos, documentación o pasos | P04 Asistente |
| aprobar, validar, revisar, dar el visto bueno, resolver (por un rol) | P05 Tarea |
| tarea que solo recoge datos (cargar un documento, completar datos del registro) | P03 Formulario, con el contexto del registro arriba o en `a!sidebarTemplate` |
| inicio: tareas pendientes, avisos, indicadores y accesos del usuario | P06 Inicio |
| editar, modificar, cambiar estado, adjuntar sobre un X existente | P07 Diálogo (acción de registro) |
| informe, estadísticas, gráficos, evolución; cuadro de mando con filtros que actualizan indicadores y gráficos | P08 Informe |
| bandeja, cola de revisión, revisar uno tras otro, triaje, clasificar pendientes | P09 Maestro-detalle |
| portada o entrada de un módulo con varias opciones («desde aquí el usuario puede…») | P10 Portada de módulo |
| asistente virtual, chatbot, preguntar a los datos o a un documento, resumen o borrador generado con IA | P11 Asistente de IA |
| extracción automática de documentos (OCR, IDP), clasificación o datos propuestos por IA que alguien confirma | P12 Revisión de datos sugeridos por IA |

Si el documento dice expresamente cómo es la pantalla («en un único formulario», «en varios pasos»), eso manda sobre los umbrales de la tabla. El patrón se elige por el contenido, no por el nombre que le dé el documento (un «cuadro de mando» sin tareas ni accesos es un P08).

**IA**: P11 y P12 solo cuando el análisis la pide. Si no la pide pero hay un caso claro (documentos que alguien teclea a mano, búsquedas por texto libre en muchos registros, informes que se redactan copiando datos), propónla como pantalla o bloque marcado con `$assumption` («Propuesta: …» y el beneficio) y como pregunta abierta; el flujo manual sigue existiendo. El chat de datos va en un panel lateral del listado (P01 con `ai_side_pane`); el chat de un registro, en su vista resumen (P02 con `ai_records_chat`); la búsqueda por significado, en el propio grid (`smartSearchType` + `match_quality`).

Una necesidad = una pantalla. Si dos requisitos caben en la misma pantalla (listado + exportar), comparten pantalla y ambos IDs van en `req`.

## 2. Tipo de dato → componente SAIL

| En el documento | Editable | Solo lectura |
|---|---|---|
| Texto corto (longitud N) | `a!textField` + `characterLimit: N` | `a!textField readOnly` |
| Texto largo / observaciones | `a!paragraphField` | `a!textField readOnly` o `a!richTextDisplayField` |
| Texto con formato | `a!styledTextEditorField` | `a!richTextDisplayField` |
| Lista cerrada ≤ 5 valores | `a!radioButtonField` (COMPACT si 2–3) | dato del resumen (`field_summary`) / `a!tagField` si es un estado |
| Lista cerrada ≤ 6 valores que necesitan icono o explicación (tipo de expediente, decisión) | `a!cardChoiceField` + plantilla Tile o BarTextStacked (`choice_cards`) | dato del resumen |
| Lista cerrada > 5 valores | `a!dropdownField` | `a!textField readOnly` |
| Selección múltiple | `a!checkboxField` (≤ 5) / `a!multipleDropdownField` | `a!tagField` |
| Sí/No opcional | `a!booleanCheckboxField` (dentro de un formulario) / `a!toggleField` (se aplica en el momento) | mapa `siNo` |
| Sí/No que debe contestarse | `a!radioButtonField` Sí/No | `readOnly` con mapa `siNo` |
| Fecha / fecha y hora | `a!dateField` / `a!dateTimeField` | filtro `date` / `datetime` |
| Entero / decimal / importe | `a!integerField` / `a!floatingPointField` | filtro `num` / `eur` |
| Usuario / grupo | `a!pickerFieldUsers` / `a!pickerFieldGroups`; si hay que recorrer la estructura para encontrarlo, `a!userBrowserFieldColumns` / `a!groupBrowserFieldColumns` | nombre + `a!imageField` AVATAR; línea jerárquica → `a!orgChartField` |
| Documento o carpeta ya existente en Appian | `a!pickerFieldDocuments` / `a!pickerFieldFolders` / `a!pickerFieldDocumentsAndFolders`; explorar una biblioteca → `a!documentAndFolderBrowserFieldColumns` | `a!documentDownloadLink` / `a!documentViewerField` |
| Jerarquía propia (aeropuerto → terminal → zona, organigrama de unidades) | `a!hierarchyBrowserFieldColumns` (selección) | `a!hierarchyBrowserFieldTree` |
| Firma | `a!signatureField` | la firma guardada como imagen |
| Vídeo de formación o procedimiento / página de otra herramienta | — | `a!videoField` + `a!webVideo` / `a!webContentField` |
| Relación con otra entidad | `a!pickerFieldRecords` o `a!dropdownField` | `a!recordLink` |
| Documento adjunto | `a!fileUploadField` | grid de documentos / `a!documentViewerField` |
| Líneas repetibles (tabla dentro del formulario) | `a!gridLayout` + `a!forEach` sobre `local!lineas` | `a!gridField` |
| Estado | (lo cambia el proceso) | `a!tagField` con la paleta de estados (`state_map`) + `a!milestoneField` en la franja de datos clave |
| Alertas o avisos por registro | (los genera el proceso) | Columna `ICON` con `alert_icons` (icono con tooltip) en el listado; en la ficha, `action_banner` con la acción que las resuelve |
| Agenda, turnos, vencimientos por fecha | — | `calendar_month` (mes con panel del día) / `calendar_week` |
| Comentarios o conversación sobre un registro | `comment_thread` (con respuestas y adjuntos) | ídem, en su vista de la ficha |
| Tareas o acciones que avanzan por etapas | `kanban` (flechas para cambiar de etapa) | `kanban` / grid con estado |

## 3. No inventar

- No añadir campos, estados, roles ni pantallas que el documento no pida.
- Cuando una pantalla necesita algo que el documento no define (qué columnas lleva el listado, qué ve el usuario tras enviar), elegir lo mínimo razonable y marcarlo con `$assumption` en el componente o en `assumptions` de la pantalla.
- Contradicciones y huecos → `openQuestions` con la pantalla afectada. Son el orden del día de la reunión con AENA.

## 4. Checkpoint con el usuario

Antes de escribir el `app.json`, presentar en un solo mensaje:

1. Inventario: tabla `Id · Pantalla · Patrón · Tarea principal · Requisitos` (el brief de diseño de SKILL.md, paso 1).
2. Navegación: páginas del site y desde dónde se abre cada pantalla.
3. Preguntas abiertas y supuestos.

Si el usuario pidió explícitamente ir directo, o no está presente, seguir con la lectura más razonable y dejarlo reflejado en `openQuestions`/`$assumption`.
