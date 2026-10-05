# Formato del app spec (`app.json`)

El prototipo se describe en un único JSON. Los ejemplos de esta página usan un dominio genérico y ficticio (expedientes de una unidad, el mismo que las plantillas); en un proyecto, nombres, campos, estados y datos salen de su `ddf.md`. Regla de oro: **los nodos de interfaz son funciones SAIL reales con sus parámetros reales** (`"type": "a!cardLayout"`, `"padding": "MORE"`...). Todo lo que existe solo para el prototipo empieza por `$` y el equipo de desarrollo sabe que no se traslada a SAIL.

## Estructura raíz

```json
{
  "app":   { "name": "Gestión de expedientes", "language": "es", "source": "ddf.md v1.2 (15/09/2026)", "today": "2026-09-24", "appianVersion": "26.9" },
  "site":  { "displayName": "...", "home": "inicio", "user": { "name": "Lucía Fernández Gil" },
             "pages": [ { "title": "Inicio", "icon": "home", "screen": "inicio", "includes": ["revision"] } ] },
  "requirements":  [ { "id": "RF-01", "title": "Indicadores en la página de inicio" } ],
  "openQuestions": [ { "id": "Q-01", "text": "¿Quién puede editar un expediente aprobado?", "screen": "editar", "priority": "CRITICA" } ],
  "maps":  { "estadoColor": { "Aprobado": "POSITIVE", "Rechazado": "NEGATIVE", "*": "SECONDARY" } },
  "users": [ { "id": "mlopez", "name": "María López Arranz", "title": "Jefa de Operaciones MAD", "supervisor": "cruiz", "groups": ["g-mad"] } ],
  "groups": [ { "id": "g-mad", "name": "Operaciones MAD", "parent": "g-dir", "description": "Adolfo Suárez Madrid-Barajas" } ],
  "documents": [ { "id": "f-norm", "name": "Normativa", "type": "folder" }, { "id": "d-sms", "name": "Manual_SMS_v4.pdf", "folder": "f-norm", "type": "document", "size": "2,4 MB", "modified": "2026-07-14" } ],
  "data":  { "expedientes": { "recordType": "EXP Expediente", "rows": [ { "id": 1, "codigo": "EXP-2026-0001" } ] } },
  "state": { },
  "screens":  [ ... ],
  "captures": [ ... ]
}
```

| Clave | Para qué |
|---|---|
| `site.pages` | Páginas del Site (máx. 10). `includes` = pantallas que marcan esa pestaña como activa (ficha, alta...). |
| `app.today` | Fecha «de hoy» fija para `today()`/`now()`, para que demo y capturas no cambien con el día. |
| `app.appianVersion` | Versión de Appian del entorno: la del apartado «0. Entorno» de `analisis/tecnico.md` del proyecto; si no existe, `26.9` con `"$assumption"` en `app` y una pregunta abierta. El validador da error si se usa un componente, un parámetro o un valor posterior (`schemas/appian-versions.json`). También se usa al consultar la documentación oficial. |
| `requirements` | IDs del documento de entrada. Alimentan la matriz de cobertura. Las actividades que el documento sitúa fuera de la aplicación (otro sistema, un actor externo que no usa Appian) llevan `"outOfScope": "motivo"`; los requisitos de la aplicación que no tienen pantalla propia (los hace el sistema o un robot, o son de otra iteración), `"noScreen": "motivo"`. Ninguno de los dos cuenta como hueco y la trazabilidad muestra el motivo. |
| `openQuestions` | Ambigüedades del documento, para la reunión con el cliente. `priority` opcional: `CRITICA` 🔴, `IMPORTANTE` 🟡, `MEJORA` 🟢 (misma escala que el DDF). |
| `maps` | Tablas de traducción para `{expr\|map:nombre}` (estado → color, estado → paso del hito, booleano → Sí/No). `"*"` = valor por defecto. |
| `data` | Datos de ejemplo por record type. **Los nombres de campo son los del record type**: documentan el modelo de datos para desarrollo. |
| `users` | Usuarios para selectores, navegadores y organigrama: `title` (cargo), `supervisor` (id de su responsable: a!orgChartField), `groups` (ids de sus grupos: navegadores de usuarios y grupos). |
| `groups` | Grupos del entorno: `parent` (id del grupo padre) forma la jerarquía de a!groupBrowserFieldColumns y a!userBrowserFieldColumns (`rootGroup`: id o nombre del grupo). |
| `documents` | Carpetas (`type: "folder"`) y documentos del entorno, con `folder` (carpeta que los contiene), `size` y `modified`: navegadores y selectores de documentos y carpetas (`rootFolder`, `folderFilter`). |

## Pantallas

```json
{ "id": "listado", "title": "Expedientes", "type": "page", "pattern": "P01",
  "req": ["RF-03", "RF-04"], "assumptions": ["..."], "local": { "local!filtro": null },
  "interface": { "type": "a!headerContentLayout", "contents": [ ... ] } }
```

- `type`: `page` (página del site) · `record` (vista de registro) · `form` (formulario o tarea a página completa) · `dialog` (acción en diálogo).
- `pattern`: obligatorio, uno de `templates/patterns.json`. El validador comprueba el tipo y el componente raíz.
- `req`: requisitos que cubre. `assumptions`: supuestos a nivel de pantalla.
- `ref`: dónde está definida en el documento de entrada (p. ej. `"PAN-02 · Listado de expedientes"`, el ID de la ficha en la Sec 12 del `ddf.md`). Sale en la trazabilidad y en el índice de capturas para saber bajo qué ficha va cada imagen. Una vista de registro que es otra ficha del análisis lleva su propio `ref` (y `req`).
- `local`: variables locales iniciales (se reinician al entrar). Admiten `{rv!record.campo}` para precargar desde el registro.
- `recordType` (en `record`, y opcional en `form`/`dialog`): la pantalla recibe `rv!record` = fila de `data` con `id = params.id`. Sin `id`, un `form` o `dialog` recibe un registro vacío (un alta no sale rellena con otro registro) y una `record`, el primero (para abrirla desde el índice).
- `openFrom` (en `dialog`): pantalla sobre la que se abre en el índice y en las capturas.
- `$dialogWidth` (en `dialog`): ancho del cuadro en el prototipo (`EXTRA_NARROW`, `NARROW`, `MEDIUM`, `MEDIUM_PLUS`, `WIDE`, `FULL`). En Appian es la Dialog Width de la acción de registro; el formulario o asistente del diálogo va a `contentsWidth: "FULL"`.

Pantalla de registro:

```json
{ "id": "registro", "type": "record", "pattern": "P02", "recordType": "EXP Expediente",
  "title": "{rv!record.codigo} · {rv!record.titulo}",
  "breadcrumb": { "label": "Expedientes", "goto": "listado" },
  "recordActions": [ { "type": "a!recordActionItem", "action": "recordType!EXP Expediente.actions.editar",
                       "identifier": "{rv!record.id}", "$label": "Editar datos", "$icon": "pencil",
                       "$action": { "dialog": "editar", "params": { "id": "{rv!record.id}" } } } ],
  "views": [ { "id": "resumen", "label": "Resumen", "interface": { ... } } ] }
```

Configuración de la cabecera del registro (record type, no SAIL):
- `headerBackgroundColor`: fondo de la cabecera (Record header background: Color). Con `"#1A2732"` continúa la barra del site.
- `recordActionsStyle`: estilo de los atajos de acción (`TOOLBAR_PRIMARY` por defecto, `TOOLBAR`, `MENU`…).
- Como máximo 3 atajos en `recordActions`: el resto va en «Acciones relacionadas».

## Expresiones y enlace de datos

Se usa la sintaxis de dominios de SAIL para que el código sea legible por desarrollo:

| Escribes | Significa |
|---|---|
| `"value": "local!exp.titulo"`, `"saveInto": "local!exp.titulo"` | Enlace de lectura y escritura (admite rutas con puntos). |
| `"{fv!row.codigo}"` | Interpolación en columnas de grid y `a!forEach` (`fv!item`, `fv!index`). En las plantillas de `a!cardChoiceField` (`cardTemplate: a!cardTemplateTile(...)`), cada opción es `fv!data`: `"id": "fv!data.id"`, `"primaryText": "{fv!data.texto}"`. |
| `"{rv!record.fechaFin\|date}"` | Campo del registro con filtro. Filtros: `date`, `datetime`, `eur`, `num`, `pct`, `upper`, `initials`, `dash` («–» si está vacío; en SAIL `a!defaultValue(valor, "–")`), fechas en texto `longdate` («Lunes, 5 de octubre»; en SAIL `text(fecha, "dddd, d \"de\" mmmm")`), `monthyear` («Octubre de 2026»), `dayname` («Lunes»), `daymonth` («5 oct»), `time` («09:30» de una fecha y hora), `map:<nombre>`. Se encadenan: `{rv!record.importe\|eur\|dash}`. |
| `"showWhen": "and(local!x = \"A\", not(isnull(local!y)))"` | Expresión booleana. Funciones: `and or not if isnull a!isNullOrEmpty a!isNotNullOrEmpty a!defaultValue contains len count sum index where wherecontains displayvalue today todate left search` y de listas `append difference union remove joinarray`. Operadores `= <> < > <= >= + - * / &`. `contains(lista, valor)` es pertenencia a una lista; para buscar texto dentro de un texto, `search(buscado, texto) > 0`. |
| `"required": "local!decision <> \"APROBAR\""` | Obligatoriedad condicional. |
| `todate(local!hasta) - todate(local!desde) > 90` | Aritmética de fechas: `todate()` convierte una fecha ISO en número de días. Las fechas sin `todate()` son texto ISO: se pueden comparar (`<`, `>=`) pero no restar. |
| `local!lineas.importe` | Campo de una lista de registros → lista (como en SAIL), p. ej. `sum(local!lineas.importe)`. |
| `"saveInto": [{ "type": "a!save", "target": "local!tipo", "value": null }]` | `a!save` real. `"value": "save!value"` = valor introducido. |
| `"items": "data!documentos"` en `a!forEach` | Recorre un dataset de ejemplo (`$filter`, `$limit`). Sobre una variable (`"items": "local!correos"`), `"value": "fv!item"` y `"saveInto": "fv!item"` editan cada elemento. |
| `fv!row[recordType!X.fields.campo]` | Referencia de campo de registro (SAIL real): equivale a `fv!row.campo`. `fv!row[recordType!X.searchResults.allSearchFields.similarityScore]` es la puntuación de la búsqueda inteligente (solo para ordenar o para `match_quality`). |
| `fv!selection[recordType!X.fields.campo]` | En el `link` de la configuración de un gráfico de registros: valor de la agrupación pulsada (drilldown, helper `chart_link`). |
| `fv!percentage` | En `a!gaugeField`: porcentaje actual (colores por tramo). |
| `"data": "recordType!EXP Expediente"` en grids, KPIs y gráficos | Se resuelve al dataset con ese `recordType`. |

## Parámetros solo de prototipo (`$`)

| Clave | Dónde | Uso |
|---|---|---|
| `$action` | botones, enlaces, `a!recordActionItem`, `a!cardLayout.link` | Navegación. Objeto o lista: `{"goto": id, "params": {...}, "view": id}`, `{"dialog": id, "params": {...}}`, `{"close": true}`, `{"back": true}`, `{"step": N}` (paso N del asistente, 1 = primero: enlaces «Editar» del paso de revisión), `{"set": {"local!x": v}}`, `{"append": {"local!l": {...}}}` y `{"prepend": …}` (añaden al final o al principio evaluando las `{expresiones}` del elemento), `{"remove": {"local!l": "{fv!index}"}}`. Los cambios de variables se aplican en el orden en que se escriben (como la lista de `a!save`): `{"append": …, "set": {"local!texto": null}}` añade y después vacía el campo. `goto`/`dialog` admiten destino dinámico `"{fv!row.pantalla}"` (bandeja de tareas que abre el formulario de cada tarea): el validador comprueba que todos los valores de ese campo en `data` son pantallas. |
| `$filter` | `a!gridField`, `a!kpiField`, gráficos, `a!forEach`, `a!eventHistoryListField` | Filtro sobre filas (`fv!row`): equivale a los `filters` de `a!recordData` / `a!queryFilter`. |
| `$value`, `$format` | `a!kpiField` | Valor fijo si no se calcula con `data` + `primaryMeasure`. |
| `$secondaryValue` | `a!kpiField` | Valor de comparación (mes anterior, objetivo). Con él, el KPI calcula la tendencia como Appian con `secondaryMeasure` + `trend` (`AUTO`: diferencia y %). Usa `trendColor: "REVERSE"` cuando bajar es bueno. También sirve `secondaryMeasure` con un `a!measure` que lleve `$filter`. `$trend` fija el texto de la tendencia (compatibilidad). |
| `$filter` en `a!measure` | `primaryMeasure`, `secondaryMeasure`, medidas de gráficos | Filtro de filas de esa medida (equivale a `filters` de `a!measure`). |
| `$messages` | chats de IA | Conversación ya empezada: `[{"role": "USER"\|"ASSISTANT"\|"TOOL"\|"THOUGHT"\|"BLOCKED", "text": ..., "tool": ..., "input": ..., "output": ...}]`. `TOOL` es una llamada a herramienta del agente (entradas y salidas solo con `debugMode`); `BLOCKED`, un bloqueo de guardrail. En `a!chatField`, la conversación de SAIL (`messages` con `a!chatMessage`) se pinta antes. |
| `$replies` | chats de IA | Respuestas simuladas, por turnos: texto (admite `**negrita**` y listas con `- `) u objeto `{"text", "content" (componente, p. ej. `ai_answer()`), "tools": [{"tool", "text", "input", "output"}], "thoughts": [...], "outputs": {...} (lo que recibe `outputsSaveInto` como `save!value`), "blocked": true, "$action"}`. Mientras «responde» se ve la animación y, en el agente, el botón Detener. |
| `$sessions` | `a!agentChatField` | Conversaciones anteriores del selector: texto o `{"name", "messages"}`. |
| `$state` | chats de IA | Estado fijo para capturas: `RUNNING` (respondiendo, con Detener) o `UNAVAILABLE` (función de IA no habilitada). |
| `$root`, `$nodes` | `a!recordKnowledgeGraph` | Registro base `{"recordType", "name", "icon"}` y relacionados `[{"recordType", "name", "icon", "parent"}]` (`parent` = `name` de otro nodo). |
| `$tree` | navegadores (`a!*BrowserFieldColumns`, `a!hierarchyBrowserFieldTree`) | Jerarquía propia del componente en vez de `users`/`groups`/`documents` o de `firstColumnValues`: `[{"id", "label", "description", "details", "icon", "type": "user"\|"group"\|"folder"\|"document", "count", "children": [...]}]`. Con datos SAIL (`firstColumnValues` + `nodeConfigs` + `nextColumnValues`), el prototipo evalúa `fv!nodeValue` como Appian. |
| `$icon` | `a!hierarchyBrowserField*Node` (`nodeConfigs`) | Icono del nodo en el prototipo cuando la imagen es un `a!documentImage` (en Appian, la imagen real). |
| `$duration` | `a!webVideo` | Duración que muestra el reproductor («4:12»). |
| `$title` | `a!webContentField` | Qué muestra la página embebida (el prototipo no la carga: enseña su dominio y un esqueleto). |
| `$local` | `a!forEach` | Variables de cada vuelta, como `a!localVariables` dentro de la expresión: `{"local!comentario": "fv!item"}`. Con `$filter`, lo que se guarda en `fv!item` va a la fila original de la lista. |
| `$categories` | gráficos con `config` | Orden fijo de categorías. |
| `$chart` | `a!gridField` | Tabla alternativa de un gráfico (la genera `chart_table()`): una fila por categoría con `categoria` y una columna por serie (`s1`, `s2`…), con los mismos datos y filtros que el gráfico. En Appian, el grid consulta el record type con la misma agregación. |
| `$series` | gráficos con `config` y `secondaryGrouping` | Orden fijo de los valores de la agrupación secundaria (una serie por valor), para que cada serie tome su color de `colorScheme` en ese orden: `state_chart_colors(mapa, orden)` + `"$series": orden`. |
| `$label`, `$icon` | `a!recordActionItem` | En Appian vienen de la acción del record type. |
| `$options` | pickers y listas | Opciones de ejemplo. |
| `$events` | `a!eventHistoryListField` | Eventos de ejemplo (dataset o lista). |
| `$template` | `a!cardChoiceField` | Obsoleto: usa `cardTemplate` con `a!cardTemplateTile`, `a!cardTemplateBarTextJustified` o `a!cardTemplateBarTextStacked` (SAIL real; helper `choice_cards`). |
| `$fileName`, `$pages`, `$content` | `a!documentViewerField` | Nombre, nº de páginas y texto de cada página (lista de textos o de párrafos) del documento de ejemplo. El visor abre en `initialPageDisplay` y resalta la primera coincidencia de `highlightedText`; si esas variables cambian (una cita), salta a la página. Sin documento (`document` vacío) muestra «Documento no disponible». |
| `$validations` | campos | `[{ "when": expr, "message": "..." }]` validación en vivo (reglas de negocio). |
| `$note` | cualquiera | Nota para desarrollo, visible en el inspector. |
| `$assumption` | cualquiera | Supuesto no respaldado por el documento: borde naranja en el inspector y listado en la trazabilidad. |
| `$uxIgnore` | cualquiera | Desviación deliberada de la guía, con su motivo: silencia los avisos `UX ·` de ese nodo (p. ej. una galería que enseña `debugMode`); en una pantalla, el de pantalla a la que no se llega. Úsalo poco: el motivo lo lee quien revisa. |

## Botones de envío y validación

Un `a!buttonWidget` con `"submit": true` valida los campos `required` visibles de la pantalla (o del paso del asistente), las `$validations` activas y las `validations` visibles del formulario, la sección o el paso (`a!validationMessage` con `showWhen`) antes de ejecutar su `$action`, y muestra *Se requiere un valor* igual que Appian. Lo mismo hace «Siguiente» en cada paso del asistente. `confirmHeader` / `confirmMessage` abren el diálogo de confirmación nativo.

## Los datos de ejemplo no cambian

Las acciones no modifican `data`: tras «Guardar» o «Enviar decisión» el registro sigue igual y la tarea sigue en la bandeja. Para enseñar el resultado se navega con parámetros (`"params": {"mensaje": "..."}` → banner con `ri!mensaje`) o se prepara una captura con `state`. Los valores derivados que el prototipo no sabe calcular (días hasta el vencimiento, antigüedad) se precalculan en los datos de ejemplo (p. ej. `diasParaVencer`) respecto a `app.today`.

## Capturas

```json
"captures": [
  { "name": "01-inicio", "screen": "inicio" },
  { "name": "03-ficha-documentos", "screen": "registro", "params": { "id": 3 }, "view": "documentos" },
  { "name": "06-alta-errores", "screen": "alta", "step": 0, "showValidation": true },
  { "name": "07-alta-importe", "screen": "alta", "step": 2, "state": { "local!exp": { "conImporte": true } } },
  { "name": "09-dialogo-editar", "screen": "editar", "hostParams": { "id": 3 }, "params": { "id": 3 } }
]
```

Opciones: `params`, `view`, `step` (0 = primer paso), `state` (variables), `showValidation`, `hostParams` (registro sobre el que se abre un diálogo), `caption` (texto del estado en `indice.md`), `full: false` (solo el área visible; por defecto, página completa).

`userFilters` de `a!gridField` acepta la referencia `recordType!X.filters.campo` (etiqueta derivada del nombre del campo) o `{"field": "campo", "label": "Etiqueta"}` cuando el nombre del campo no sirve como etiqueta. Los campos booleanos se muestran como Sí/No.

Valores iniciales de `local`: los textos con `{expresión}` se evalúan al entrar en la pantalla, también dentro de mapas y listas (`"local!correo": {"asunto": "Estudio {rv!record.registro}"}`). Entrar en una pantalla la carga de nuevo: secciones plegables, pestañas y paginación de grids vuelven a su estado inicial.

Expresiones: se admiten listas SAIL con llaves (`contains({"A", "B"}, rv!record.estado)`).
