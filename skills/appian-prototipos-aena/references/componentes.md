# Componentes: qué se pinta y cómo se traslada a Appian

La fuente de verdad de nombres, parámetros y valores válidos son los schemas de `schemas/` (los mismos que usa la skill appian-sail-generator) más `schemas/prototype-extensions.json`. `validate.py` rechaza cualquier componente, parámetro o valor que no exista en SAIL, cualquier icono que no esté en `schemas/icon-aliases.md` y las anidaciones que Appian no admite (layouts raíz anidados, botones fuera de su layout, layouts o grids en `a!sideBySideItem`, campos editables en columnas de `a!gridField` — y, antes de 26.9, `a!sideBySideLayout` en celdas de grid —, `a!tabLayout` en side-by-side o grids, cabeceras de `a!headerContentLayout` que no sean card o billboard, hijos no válidos de `a!richTextDisplayField`).

## Se renderizan con aspecto Appian

**Layouts**: a!headerContentLayout, a!formLayout (barra de título y botonera fijas, divisores, fondo), a!wizardLayout (estilos DOT, LINE y CHEVRON, horizontales y verticales, y MINIMAL), a!columnsLayout/a!columnLayout (anchos fijos y 1X–10X), a!sideBySideLayout/a!sideBySideItem, a!cardLayout (estilos, barra decorativa, borde, sombra, alto, enlace), a!cardGroupLayout, a!sectionLayout (color y grosor del divisor, plegable), a!boxLayout (26.7: `borderColor`, `borderWeight`, `labelFontWeight`), a!tabLayout/a!tabItem (26.1: color de resaltado, pestaña inicial `selectedTab`; 26.7: `orientation` VERTICAL, `tabWidth`, `showDivider`, `dividerColor`), a!paneLayout/a!pane (también dentro de a!formLayout, 25.3; cada panel se desplaza por separado), a!billboardLayout (+ overlays; `backgroundMedia` web o marcador), a!buttonLayout, a!buttonArrayLayout, a!forEach.

**Barras de título**: texto, a!headerTemplateSimple, a!headerTemplateFull, a!headerTemplateImage, **a!sidebarTemplate** (25.3: barra lateral del formulario o del asistente; en asistentes verticales lleva el hito).

**Entrada**: a!textField, a!paragraphField, a!integerField, a!floatingPointField, a!dateField, a!dateTimeField, a!dropdownField, a!multipleDropdownField, a!radioButtonField, a!checkboxField (y variantes ByIndex), a!booleanCheckboxField, a!toggleField, a!pickerFieldUsers/Groups/UsersAndGroups/Records/Custom/Documents/Folders, a!fileUploadField (zona COMPACT/EXPANDED, `buttonStyle` y, desde 26.8, `buttonColor`), a!signatureField, a!styledTextEditorField, **a!cardChoiceField con a!cardTemplateTile / a!cardTemplateBarTextJustified / a!cardTemplateBarTextStacked**, a!encryptedTextField, a!barcodeField.

**Visualización**:
- Texto: a!richTextDisplayField (a!richTextItem con `style` LIGHT y SEMI_BOLD de 26.7, a!richTextIcon, listas), a!headingField.
- Estados y marcadores: a!stampField (WARN, EXTRA_TINY), a!tagField (fondos apagados en hex para estados), a!milestoneField (LINE, DOT, CHEVRON y enlaces).
- Enlaces: a!linkField (a!dynamicLink, a!recordLink, a!safeLink, a!startProcessLink, a!submitLink, a!processTaskLink, a!userRecordLink, **a!pageLink** de 26.8 a una página del site).
- Indicadores: a!progressBarField, a!gaugeField (texto dentro, `a!gaugePercentage`, `a!gaugeFraction`, `a!gaugeIcon`, `fv!percentage`), a!kpiField (COMPACT, STACKED y ADJACENT; tendencia con medida secundaria), a!messageBanner.
- Otros: a!horizontalLine, a!imageField (los 13 tamaños, a!userImage con color), a!recordActionField, a!timeDisplayField.
- Listas: **a!eventHistoryListField** (FULL_LIST, PREVIEW_LIST, **TIMELINE**, LIST_WITH_COMMENTS; comentarios en card).
- Grids: a!gridField (estilos de borde, `selectionStyle` ROW_HIGHLIGHT/SUBTLE, alto fijo, anchos 1X–10X, colores de celda para mapas de calor, **búsqueda inteligente** `smartSearchType` + `similarityScoreThreshold` con `similarityScore` por fila y orden por relevancia, celdas con `a!sideBySideLayout` desde 26.9), a!gridLayout.
- Documentos: **a!documentViewerField** con barra (páginas, zoom, descarga), `initialPageDisplay`, resaltado de `highlightedText` y «Documento no disponible».
- Registros: **a!recordKnowledgeGraph** (26.8): grafo radial del registro y sus relacionados, controles y minimapa.

**Gráficos**: a!columnChartField, a!barChartField, a!lineChartField, a!areaChartField, a!pieChartField, **a!scatterChartField**.
- Se configuran con `categories` + `a!chartSeries`, o con `data` (record type) + `config` (`a!xxxChartConfig`, `a!grouping`, `a!measure` COUNT/SUM/AVG/MIN/MAX): el prototipo agrega los datos de ejemplo igual que Appian agregaría el record type.
- Se pintan: **a!chartReferenceLine** (umbrales y objetivos), `showDataLabels`, títulos de eje, `yAxisMin`/`yAxisMax`, apilado `NORMAL` y `PERCENT_TO_TOTAL`, `height` MICRO para sparklines, leyenda y etiquetas de tarta, `allowLegendFiltering` (26.8: la leyenda oculta y muestra series).
- **Drilldown**: el `link` de `a!xxxChartConfig` se ejecuta al pulsar una barra o punto con `fv!selection` (valor de la agrupación); los `links` de `a!chartSeries`, por punto.

**IA** (cada una con su anatomía documentada; conversación simulada con `$messages`, `$replies`, `$sessions`, `$state`):
- **a!agentChatField** (26.6): barra de título con selector de conversaciones, mensaje de bienvenida, respuesta con animación, filas de llamadas a herramientas (entradas y salidas solo con `debugMode`), botón Detener mientras responde (26.7), `outputsSaveInto` al terminar; `shape` (FULLY_ROUNDED) y `showBorder` de 26.7; alto FILL por defecto.
- **a!chatField** + **a!chatMessage**: título de texto o componentes, mensajes de texto o componentes (citas, valoración), `saveInto` al enviar, `backgroundColor` (también esquemas oscuros), alto AUTO por defecto.
- **a!dataFabricChatField**: barra de título y hasta 3 preguntas sugeridas (`a!suggestedQuestion` con icono y color) que se envían al pulsarlas; llena su panel.
- **a!recordsChatField**: campo con etiqueta, mensaje inicial, preguntas sugeridas en píldoras y botón Enviar con `buttonStyle` (PRIMARY, NORMAL, LINK).
- **a!documentsChatField**: campo con etiqueta y chat sin mensaje inicial ni sugerencias.

**Marcadores** (se ven como un bloque rotulado, no como el componente real): a!webContentField, a!videoField.

## Cómo leen el prototipo los desarrolladores

1. Activar **Inspector** (botón de la barra o tecla `I`): cada componente se recuadra; al pasar el ratón se ve `a!componente(parámetros clave)` y al hacer clic, todos sus parámetros SAIL y, aparte, los `$` del prototipo, las notas (`$note`) y los supuestos (`$assumption`).
2. El `app.json` es la especificación: la interfaz de cada pantalla es un árbol de funciones SAIL con sus parámetros. Traducirlo a SAIL es mecánico (`{"type": "a!cardLayout", "padding": "MORE"}` → `a!cardLayout(padding: "MORE")`).
3. `data` describe los record types de ejemplo: nombres de campo, tipos de valor y relaciones (`acuerdoId`).
4. `brand-aena.json → site` es la configuración del objeto Site.

## Equivalencias del prototipo que en Appian se resuelven de otra forma

| En el prototipo | En Appian |
|---|---|
| `data: "recordType!X"` + filas de ejemplo | Record type sincronizado; `a!recordData(filters: ...)` para `$filter` |
| `$action.goto` / `dialog` | Páginas del Site, `a!recordLink`, acciones de registro (`openActionsIn: "DIALOG"`), process model de la acción |
| `recordActions` con `$label`/`$icon` | Acciones configuradas en el record type |
| Pantalla `type: "record"` con `views` | Record views del record type (Summary + vistas), cabecera del registro configurada en el record type |
| `ri!mensaje` tras enviar | Mensaje de confirmación del process model o parámetro de la interfaz |
| `$validations` | `validations` del campo con la expresión de la regla |
| `$secondaryValue` en KPI | `secondaryMeasure` (a!measure con filtros del periodo de comparación) |
| `|dash` | `a!defaultValue(valor, "–")` |
| `$replies` / `$messages` en chats de IA | Respuestas reales del agente, del modelo (`a!callLanguageModel`) o del chatbot; en `a!chatField`, la conversación se guarda en variables o en un record type |
| `$content` del visor | El documento real (`document`), con `initialPageDisplay` y `highlightedText` calculados a partir de la cita |
| `headerBackgroundColor` de la pantalla de registro | Record type › Record header › Background: Color |
| Tareas de ejemplo (`data!tareas`) | Record type de tareas o `a!queryProcessAnalytics` |

## Diferencias visuales conocidas

- Los hex de POSITIVE/NEGATIVE/WARN/INFO y de los colores con nombre de gráficos (BLUEGRAY, GREEN, AMBER…) son aproximaciones: Appian no los publica. En SAIL se usan siempre los enumerados.
- Los valores por defecto del prototipo son los documentados en Appian 26.6: card NONE (blanca) con padding LESS, sección con etiqueta ACCENT, grid LIGHT sin sombreado, asistente DOT_VERTICAL a ancho FULL, tag ACCENT, KPI con icono STANDARD.
- Tipografía Open Sans (la de Appian); si AENA configura su tipografía en Admin Console, el sistema real la mostrará.
- Los gráficos son SVG simplificados (sin animaciones ni tooltips enriquecidos).
- El menú del site en móvil se desplaza horizontalmente; Appian lo pliega en un menú.
