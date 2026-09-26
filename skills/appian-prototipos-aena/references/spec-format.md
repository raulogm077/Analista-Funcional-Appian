# Formato del app spec (`app.json`)

El prototipo se describe en un único JSON. Regla de oro: **los nodos de interfaz son funciones SAIL reales con sus parámetros reales** (`"type": "a!cardLayout"`, `"padding": "MORE"`...). Todo lo que existe solo para el prototipo empieza por `$` y el equipo de desarrollo sabe que no se traslada a SAIL.

## Estructura raíz

```json
{
  "app":   { "name": "Acuerdos con Terceras Partes", "language": "es", "source": "DDF OP_ATP v1.2 (15/09/2026)", "today": "2026-09-24", "appianVersion": "25.4" },
  "site":  { "displayName": "...", "home": "inicio", "user": { "name": "Lucía Fernández Gil" },
             "pages": [ { "title": "Inicio", "icon": "home", "screen": "inicio", "includes": ["revision"] } ] },
  "requirements":  [ { "id": "RF-01", "title": "Indicadores en la página de inicio" } ],
  "openQuestions": [ { "id": "Q-01", "text": "¿Quién puede editar un acuerdo vigente?", "screen": "editar", "priority": "CRITICA" } ],
  "maps":  { "estadoColor": { "Vigente": "POSITIVE", "Vencido": "NEGATIVE", "*": "SECONDARY" } },
  "users": [ { "id": "mlopez", "name": "María López Arranz" } ],
  "data":  { "acuerdos": { "recordType": "ATP Acuerdo", "rows": [ { "id": 1, "codigo": "ATP-2026-0001" } ] } },
  "state": { },
  "screens":  [ ... ],
  "captures": [ ... ]
}
```

| Clave | Para qué |
|---|---|
| `site.pages` | Páginas del Site (máx. 10). `includes` = pantallas que marcan esa pestaña como activa (ficha, alta...). |
| `app.today` | Fecha «de hoy» fija para `today()`/`now()`, para que demo y capturas no cambien con el día. |
| `app.appianVersion` | Versión de Appian del entorno del cliente (por defecto `26.6`). El validador da error si se usa un componente, un parámetro o un valor posterior (`schemas/appian-versions.json`). También se usa al consultar la documentación oficial. |
| `requirements` | IDs del documento de entrada. Alimentan la matriz de cobertura. Las actividades que el documento sitúa fuera de la aplicación (otro sistema, un actor externo que no usa Appian) llevan `"outOfScope": "motivo"`: no cuentan como huecos y la trazabilidad muestra el motivo. |
| `openQuestions` | Ambigüedades del documento, para la reunión con el cliente. `priority` opcional: `CRITICA` 🔴, `IMPORTANTE` 🟡, `MEJORA` 🟢 (misma escala que el DDF). |
| `maps` | Tablas de traducción para `{expr\|map:nombre}` (estado → color, estado → paso del hito, booleano → Sí/No). `"*"` = valor por defecto. |
| `data` | Datos de ejemplo por record type. **Los nombres de campo son los del record type**: documentan el modelo de datos para desarrollo. |
| `users` | Usuarios para los pickers de usuario. |

## Pantallas

```json
{ "id": "acuerdos", "title": "Acuerdos", "type": "page", "pattern": "P01",
  "req": ["RF-03", "RF-04"], "assumptions": ["..."], "local": { "local!filtro": null },
  "interface": { "type": "a!headerContentLayout", "contents": [ ... ] } }
```

- `type`: `page` (página del site) · `record` (vista de registro) · `form` (formulario o tarea a página completa) · `dialog` (acción en diálogo).
- `pattern`: obligatorio, uno de `templates/patterns.json`. El validador comprueba el tipo y el componente raíz.
- `req`: requisitos que cubre. `assumptions`: supuestos a nivel de pantalla.
- `ref`: dónde está definida en el documento de entrada (p. ej. `"PAN-02 · Listado de acuerdos"`, el ID de la ficha en la Sec 12 del `ddf.md`). Sale en la trazabilidad y en el índice de capturas para saber bajo qué ficha va cada imagen.
- `local`: variables locales iniciales (se reinician al entrar). Admiten `{rv!record.campo}` para precargar desde el registro.
- `recordType` (en `record`, y opcional en `form`/`dialog`): la pantalla recibe `rv!record` = fila de `data` con `id = params.id`.
- `openFrom` (en `dialog`): pantalla sobre la que se abre en el índice y en las capturas.

Pantalla de registro:

```json
{ "id": "acuerdo", "type": "record", "pattern": "P02", "recordType": "ATP Acuerdo",
  "title": "{rv!record.codigo} · {rv!record.titulo}",
  "breadcrumb": { "label": "Acuerdos", "goto": "acuerdos" },
  "recordActions": [ { "type": "a!recordActionItem", "action": "recordType!ATP Acuerdo.actions.editar",
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
| `"value": "local!acuerdo.titulo"`, `"saveInto": "local!acuerdo.titulo"` | Enlace de lectura y escritura (admite rutas con puntos). |
| `"{fv!row.codigo}"` | Interpolación en columnas de grid y `a!forEach` (`fv!item`, `fv!index`). En las plantillas de `a!cardChoiceField` (`cardTemplate: a!cardTemplateTile(...)`), cada opción es `fv!data`: `"id": "fv!data.id"`, `"primaryText": "{fv!data.texto}"`. |
| `"{rv!record.fechaFin\|date}"` | Campo del registro con filtro. Filtros: `date`, `datetime`, `eur`, `num`, `pct`, `upper`, `initials`, `dash` («–» si está vacío; en SAIL `a!defaultValue(valor, "–")`), `map:<nombre>`. Se encadenan: `{rv!record.importe\|eur\|dash}`. |
| `"showWhen": "and(local!x = \"A\", not(isnull(local!y)))"` | Expresión booleana. Funciones: `and or not if isnull a!isNullOrEmpty a!isNotNullOrEmpty a!defaultValue contains len count sum index where wherecontains displayvalue today todate left search` y de listas `append difference union remove joinarray`. Operadores `= <> < > <= >= + - * / &`. `contains(lista, valor)` es pertenencia a una lista; para buscar texto dentro de un texto, `search(buscado, texto) > 0`. |
| `"required": "local!decision <> \"APROBAR\""` | Obligatoriedad condicional. |
| `todate(local!hasta) - todate(local!desde) > 90` | Aritmética de fechas: `todate()` convierte una fecha ISO en número de días. Las fechas sin `todate()` son texto ISO: se pueden comparar (`<`, `>=`) pero no restar. |
| `local!lineas.importe` | Campo de una lista de registros → lista (como en SAIL), p. ej. `sum(local!lineas.importe)`. |
| `"saveInto": [{ "type": "a!save", "target": "local!tipo", "value": null }]` | `a!save` real. `"value": "save!value"` = valor introducido. |
| `"items": "data!documentos"` en `a!forEach` | Recorre un dataset de ejemplo (`$filter`, `$limit`). Sobre una variable (`"items": "local!correos"`), `"value": "fv!item"` y `"saveInto": "fv!item"` editan cada elemento. |
| `fv!row[recordType!X.fields.campo]` | Referencia de campo de registro (SAIL real): equivale a `fv!row.campo`. `fv!row[recordType!X.searchResults.allSearchFields.similarityScore]` es la puntuación de la búsqueda inteligente (solo para ordenar o para `match_quality`). |
| `fv!selection[recordType!X.fields.campo]` | En el `link` de la configuración de un gráfico de registros: valor de la agrupación pulsada (drilldown, helper `chart_link`). |
| `fv!percentage` | En `a!gaugeField`: porcentaje actual (colores por tramo). |
| `"data": "recordType!ATP Acuerdo"` en grids, KPIs y gráficos | Se resuelve al dataset con ese `recordType`. |

## Parámetros solo de prototipo (`$`)

| Clave | Dónde | Uso |
|---|---|---|
| `$action` | botones, enlaces, `a!recordActionItem`, `a!cardLayout.link` | Navegación. Objeto o lista: `{"goto": id, "params": {...}, "view": id}`, `{"dialog": id, "params": {...}}`, `{"close": true}`, `{"back": true}`, `{"step": N}` (paso N del asistente, 1 = primero: enlaces «Editar» del paso de revisión), `{"set": {"local!x": v}}`, `{"append": {"local!l": {...}}}`, `{"remove": {"local!l": "{fv!index}"}}`. `goto`/`dialog` admiten destino dinámico `"{fv!row.pantalla}"` (bandeja de tareas que abre el formulario de cada tarea): el validador comprueba que todos los valores de ese campo en `data` son pantallas. |
| `$filter` | `a!gridField`, `a!kpiField`, gráficos, `a!forEach`, `a!eventHistoryListField` | Filtro sobre filas (`fv!row`): equivale a los `filters` de `a!recordData` / `a!queryFilter`. |
| `$value`, `$format` | `a!kpiField` | Valor fijo si no se calcula con `data` + `primaryMeasure`. |
| `$secondaryValue` | `a!kpiField` | Valor de comparación (mes anterior, objetivo). Con él, el KPI calcula la tendencia como Appian con `secondaryMeasure` + `trend` (`AUTO`: diferencia y %). Usa `trendColor: "REVERSE"` cuando bajar es bueno. También sirve `secondaryMeasure` con un `a!measure` que lleve `$filter`. `$trend` fija el texto de la tendencia (compatibilidad). |
| `$filter` en `a!measure` | `primaryMeasure`, `secondaryMeasure`, medidas de gráficos | Filtro de filas de esa medida (equivale a `filters` de `a!measure`). |
| `$messages` | chats de IA | Conversación ya empezada: `[{"role": "USER"\|"ASSISTANT"\|"TOOL"\|"THOUGHT"\|"BLOCKED", "text": ..., "tool": ..., "input": ..., "output": ...}]`. `TOOL` es una llamada a herramienta del agente (entradas y salidas solo con `debugMode`); `BLOCKED`, un bloqueo de guardrail. En `a!chatField`, la conversación de SAIL (`messages` con `a!chatMessage`) se pinta antes. |
| `$replies` | chats de IA | Respuestas simuladas, por turnos: texto (admite `**negrita**` y listas con `- `) u objeto `{"text", "content" (componente, p. ej. `ai_answer()`), "tools": [{"tool", "text", "input", "output"}], "thoughts": [...], "outputs": {...} (lo que recibe `outputsSaveInto` como `save!value`), "blocked": true, "$action"}`. Mientras «responde» se ve la animación y, en el agente, el botón Detener. |
| `$sessions` | `a!agentChatField` | Conversaciones anteriores del selector: texto o `{"name", "messages"}`. |
| `$state` | chats de IA | Estado fijo para capturas: `RUNNING` (respondiendo, con Detener) o `UNAVAILABLE` (función de IA no habilitada). |
| `$root`, `$nodes` | `a!recordKnowledgeGraph` | Registro base `{"recordType", "name", "icon"}` y relacionados `[{"recordType", "name", "icon", "parent"}]` (`parent` = `name` de otro nodo). |
| `$categories` | gráficos con `config` | Orden fijo de categorías. |
| `$label`, `$icon` | `a!recordActionItem` | En Appian vienen de la acción del record type. |
| `$options` | pickers y listas | Opciones de ejemplo. |
| `$events` | `a!eventHistoryListField` | Eventos de ejemplo (dataset o lista). |
| `$template` | `a!cardChoiceField` | Obsoleto: usa `cardTemplate` con `a!cardTemplateTile`, `a!cardTemplateBarTextJustified` o `a!cardTemplateBarTextStacked` (SAIL real; helper `choice_cards`). |
| `$fileName`, `$pages`, `$content` | `a!documentViewerField` | Nombre, nº de páginas y texto de cada página (lista de textos o de párrafos) del documento de ejemplo. El visor abre en `initialPageDisplay` y resalta la primera coincidencia de `highlightedText`; si esas variables cambian (una cita), salta a la página. Sin documento (`document` vacío) muestra «Documento no disponible». |
| `$validations` | campos | `[{ "when": expr, "message": "..." }]` validación en vivo (reglas de negocio). |
| `$note` | cualquiera | Nota para desarrollo, visible en el inspector. |
| `$assumption` | cualquiera | Supuesto no respaldado por el documento: borde naranja en el inspector y listado en la trazabilidad. |
| `$uxIgnore` | cualquiera | Desviación deliberada de la guía, con su motivo: silencia los avisos `UX ·` de ese nodo (p. ej. una galería que enseña `debugMode`). Úsalo poco: el motivo lo lee quien revisa. |

## Botones de envío y validación

Un `a!buttonWidget` con `"submit": true` valida los campos `required` visibles de la pantalla (o del paso del asistente) y las `$validations` activas antes de ejecutar su `$action`, y muestra *Se requiere un valor* igual que Appian. Lo mismo hace «Siguiente» en cada paso del asistente. `confirmHeader` / `confirmMessage` abren el diálogo de confirmación nativo.

## Los datos de ejemplo no cambian

Las acciones no modifican `data`: tras «Guardar» o «Enviar decisión» el registro sigue igual y la tarea sigue en la bandeja. Para enseñar el resultado se navega con parámetros (`"params": {"mensaje": "..."}` → banner con `ri!mensaje`) o se prepara una captura con `state`. Los valores derivados que el prototipo no sabe calcular (días hasta el vencimiento, antigüedad) se precalculan en los datos de ejemplo (p. ej. `diasParaVencer`) respecto a `app.today`.

## Capturas

```json
"captures": [
  { "name": "01-inicio", "screen": "inicio" },
  { "name": "03-ficha-documentos", "screen": "acuerdo", "params": { "id": 3 }, "view": "documentos" },
  { "name": "06-alta-errores", "screen": "alta", "step": 0, "showValidation": true },
  { "name": "07-alta-importe", "screen": "alta", "step": 2, "state": { "local!acuerdo": { "conImporte": true } } },
  { "name": "09-dialogo-editar", "screen": "editar", "hostParams": { "id": 3 }, "params": { "id": 3 } }
]
```

Opciones: `params`, `view`, `step` (0 = primer paso), `state` (variables), `showValidation`, `hostParams` (registro sobre el que se abre un diálogo), `caption` (texto del estado en `indice.md`), `full: false` (solo el área visible; por defecto, página completa).

`userFilters` de `a!gridField` acepta la referencia `recordType!X.filters.campo` (etiqueta derivada del nombre del campo) o `{"field": "campo", "label": "Etiqueta"}` cuando el nombre del campo no sirve como etiqueta. Los campos booleanos se muestran como Sí/No.

Valores iniciales de `local`: los textos con `{expresión}` se evalúan al entrar en la pantalla, también dentro de mapas y listas (`"local!correo": {"asunto": "Estudio {rv!record.registro}"}`). Entrar en una pantalla la carga de nuevo: secciones plegables, pestañas y paginación de grids vuelven a su estado inicial.

Expresiones: se admiten listas SAIL con llaves (`contains({"A", "B"}, rv!record.estado)`).
