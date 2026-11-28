# Componentes: qué se pinta y cómo se traslada a Appian

La fuente de verdad de nombres, parámetros y valores válidos son los schemas de `schemas/` (los mismos que usa la skill appian-sail-generator) más `schemas/prototype-extensions.json`. `validate.py` rechaza cualquier componente, parámetro o valor que no exista en SAIL, cualquier icono que no esté en `schemas/icon-aliases.md` y las anidaciones que Appian no admite (layouts raíz anidados, botones fuera de su layout, layouts o grids en `a!sideBySideItem`, campos editables en columnas de `a!gridField` — y, antes de 26.9, `a!sideBySideLayout` en celdas de grid —, `a!tabLayout` en side-by-side o grids, cabeceras de `a!headerContentLayout` que no sean card o billboard, hijos no válidos de `a!richTextDisplayField`).

## Se renderizan con aspecto Appian: los 147 componentes de Appian 26.10

`schemas/catalogo-appian.json` lista las 147 funciones de interfaz de Appian 26.10 por categoría, como la documentación (docs.appian.com/suite/help/26.10/SAIL_Components.html). Lo que trae una versión posterior a `app.appianVersion` (26.9 si no se declara) es un error del validador: lo de 26.10 solo se usa si el entorno del proyecto ya está en 26.10. La prueba del plugin comprueba que todas están en los schemas, que el runtime las pinta (o las consume su componente padre) y que aparecen en la galería `galerias/componentes/`, donde se ve cómo se configura cada una.

**Plantillas de nivel superior y barras de título**: a!headerContentLayout (26.10: `contentsWidth`, que limita y centra solo el contenido, y `footer`, tarjetas o billboards de borde a borde al final), a!formLayout (barra de título y botonera fijas, divisores, fondo, validaciones con a!validationMessage, también `validateAfter: "REFRESH"`), a!wizardLayout + a!wizardStep (DOT, LINE, CHEVRON horizontales y verticales, MINIMAL), a!paneLayout + a!pane (también dentro de a!formLayout; cada panel se desplaza por separado), a!headerTemplateSimple, a!headerTemplateFull, a!headerTemplateImage (también como cabecera de diálogo a todo el ancho) y a!sidebarTemplate.

**Layouts**: a!columnsLayout/a!columnLayout (anchos fijos y 1X–10X), a!sideBySideLayout/a!sideBySideItem, a!cardLayout (estilos, barra decorativa, borde y grosor, sombra, alto, enlace; en fondos oscuros los enlaces cambian de color, 26.9), a!cardGroupLayout, a!sectionLayout (color y grosor del divisor, plegable, validaciones), a!boxLayout (26.7: `borderColor`, `borderWeight`, `labelFontWeight`), a!tabLayout/a!tabItem (26.7: `orientation` VERTICAL, `tabWidth` FILL, `loadBehavior` ASYNC), a!billboardLayout + a!barOverlay/a!columnOverlay/a!fullOverlay, a!buttonLayout, a!buttonArrayLayout, a!forEach.

**Entrada**: a!textField, a!paragraphField, a!integerField, a!decimalField (26.10; `decimalType` PRECISE, por defecto, para importes y cálculos exactos, o FLOATING para medidas) y a!floatingPointField (hasta 26.9; obsoleto desde 26.10, sale del catálogo), todos con `align`, a!encryptedTextField, a!barcodeField (en web, campo de texto; `masked`), a!dateField, a!dateTimeField, a!fileUploadField (COMPACT/EXPANDED, `buttonStyle` y, desde 26.8, `buttonColor`), **a!signatureField** (26.8: botón «Dibujar firma», cuadro de firma con línea discontinua y firma guardada como imagen), a!styledTextEditorField.

**Selección**: a!dropdownField, a!multipleDropdownField, a!radioButtonField, a!checkboxField (y sus variantes ByIndex; `choiceStyle` CARDS), a!booleanCheckboxField, a!toggleField, a!cardChoiceField con a!cardTemplateTile / a!cardTemplateBarTextJustified / a!cardTemplateBarTextStacked.

**Selectores y navegadores**:
- a!pickerFieldUsers/Groups/UsersAndGroups/Records/Custom/Documents/Folders y **a!pickerFieldDocumentsAndFolders** (sugerencias de `users`, `groups`, `documents` del `app.json` o de `$options`; `folderFilter`).
- **Navegadores en columnas**: a!userBrowserFieldColumns, a!groupBrowserFieldColumns (`hideUsers`; recuento de miembros al pasar el ratón), a!userAndGroupBrowserFieldColumns, a!documentBrowserFieldColumns, a!folderBrowserFieldColumns, a!documentAndFolderBrowserFieldColumns (`navigationValue` = carpeta abierta) y a!hierarchyBrowserFieldColumns + a!hierarchyBrowserFieldColumnsNode (`firstColumnValues`, `nodeConfigs` con `fv!nodeValue`, `nextColumnValues`). Ruta resaltada, selección en el color de acento con marca, alto SHORT/MEDIUM/TALL.
- **a!hierarchyBrowserFieldTree** + a!hierarchyBrowserFieldTreeNode: un nivel por fila con conectores, nodo actual con borde de acento y recuento de hijos.
- **a!orgChartField**: responsable (o todos los superiores con `showAllAncestors`), compañeros, persona centrada y sus colaboradores; recuento directo o total (`showTotalCounts`); al pulsar, se centra en esa persona.

**Visualización**:
- Texto: a!richTextDisplayField (a!richTextItem con `style` LIGHT y SEMI_BOLD de 26.7, a!richTextIcon, listas con subniveles, **a!richTextImage** a la altura de la línea), a!headingField.
- Estados y marcadores: a!stampField, a!tagField + a!tagItem (26.10: tamaño LARGE, fondo TRANSPARENT, `showBorder` con `borderColor` e `icon` al principio o al final; el icono es decorativo y, si significa algo más que el texto, se explica en `tooltip`), a!milestoneField.
- Indicadores: a!progressBarField, a!gaugeField (a!gaugePercentage, a!gaugeFraction, a!gaugeIcon), a!kpiField (COMPACT, STACKED, ADJACENT; icono en sello; tendencia), a!messageBanner.
- Imágenes: a!imageField con a!webImage (data: URI), a!documentImage y a!userImage (iniciales con el nombre del usuario).
- **a!videoField + a!webVideo**: reproductor 16:9 con controles, título y origen; varios vídeos en rejilla.
- **a!webContentField**: marco con la página externa (dominio, título y esqueleto; el prototipo no la carga), borde y alto.
- Otros: a!horizontalLine, a!timeDisplayField, a!documentViewerField (páginas, zoom, resaltado), a!recordKnowledgeGraph (26.8; 26.10: `enableLevelSlider`, que empieza en el nivel 1 con un control para abrir hasta `relationshipLevel`, y `selectionSaveInto`, que guarda el registro pulsado como `recordTypeReference`, `recordTypePluralName`, `recordTitle` y `recordIdentifier`; en el prototipo, el identificador es el `id` del nodo de `$nodes` o, si no lo lleva, su `name`; el de la raíz, `recordIdentifier`).

**Acciones y enlaces**: a!buttonWidget (SOLID, OUTLINE, GHOST, LINK; tamaños; solo icono con `accessibilityText`), a!recordActionField + a!recordActionItem (CARDS, TOOLBAR), a!linkField y los 12 enlaces: a!dynamicLink, a!recordLink, a!pageLink (26.8), a!safeLink, a!startProcessLink (`bannerMessage`, 26.9), a!processTaskLink, a!submitLink, a!documentDownloadLink, a!userRecordLink, a!reportLink, a!newsEntryLink y a!authorizationLink.

**Grids y listas**: a!gridField + a!gridColumn (bordes, selección, alto, anchos, colores de celda, búsqueda inteligente, celdas con a!sideBySideLayout desde 26.9), a!gridLayout + a!gridRowLayout + a!gridLayoutHeaderCell + a!gridLayoutColumnConfig, a!eventHistoryListField + a!eventData (FULL_LIST, PREVIEW_LIST, TIMELINE, LIST_WITH_COMMENTS).

**Gráficos**: a!columnChartField, a!barChartField, a!lineChartField, a!areaChartField (también apilado), a!pieChartField, a!scatterChartField, con `categories` + a!chartSeries o `data` + a!xxxChartConfig, a!grouping, a!measure, a!chartReferenceLine (etiqueta legible sobre blanco) y a!colorSchemeCustom. Etiquetas de datos (26.8: dentro de un segmento apilado, blanco o negro según su color), leyenda que filtra (`allowLegendFiltering`) y drilldown (`fv!selection`).

**IA** (conversación simulada con `$messages`, `$replies`, `$sessions`, `$state`): a!agentChatField (26.6; forma, borde y botón Detener de 26.7; 26.10: `showReasoning`, por defecto true, deja a la vista cada acción del agente; con false se ve solo la que está en curso), a!chatField + a!chatMessage, a!dataFabricChatField + a!suggestedQuestion, a!recordsChatField, a!documentsChatField.

## Cómo leen el prototipo los desarrolladores

1. Activar **Inspector** (botón de la barra o tecla `I`): cada componente se recuadra; al pasar el ratón se ve `a!componente(parámetros clave)` y al hacer clic, todos sus parámetros SAIL y, aparte, los `$` del prototipo, las notas (`$note`) y los supuestos (`$assumption`).
2. El `app.json` es la especificación: la interfaz de cada pantalla es un árbol de funciones SAIL con sus parámetros. Traducirlo a SAIL es mecánico (`{"type": "a!cardLayout", "padding": "MORE"}` → `a!cardLayout(padding: "MORE")`).
3. `data` describe los record types de ejemplo: nombres de campo, tipos de valor y relaciones (`expedienteId` en la entidad hija).
4. `brand-<id>.json → site`, el de la marca con la que se construyó (la del proyecto o `assets/brand-appian.json`), es la configuración del objeto Site.

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
| Tareas de ejemplo (`data!tareas`) | `a!queryTaskList()` (26.9: tareas de procesos normales y con autoescalado, sin informe de procesos), record type de tareas o `a!queryProcessAnalytics` |
| `users` / `groups` / `documents` del `app.json` | Usuarios, grupos, carpetas y documentos del entorno (`rootGroup`, `rootFolder`, constantes de carpeta) |
| `$tree` en un navegador | `firstColumnValues` / `nextColumnValues` (o `nextLevelValues`) con una regla que consulta la jerarquía, y `nodeConfigs` |
| `$duration` en a!webVideo, `$title` en a!webContentField | Metadatos del vídeo o de la página embebida (no son parámetros de SAIL) |
| `$local` en a!forEach | `a!localVariables(local!x: fv!item, …)` dentro de la expresión del bucle |
| `$action.prepend` / `append` en comentarios o tareas | `a!save(local!lista, append(...))` o el process model que crea el registro |
| `<prototipo>-perfil-css.txt` | Admin Console › Branding › CSS Profiles: se pega tal cual y se asigna al site |

## Diferencias visuales conocidas

- POSITIVE/NEGATIVE/WARN/INFO se pintan con los colores estándar que Appian publica para los perfiles CSS (css-property-usage.html) o con los del perfil CSS de la marca, que los sustituye; los colores con nombre de gráficos (BLUEGRAY, GREEN, AMBER…) son aproximaciones. En SAIL se usan siempre los enumerados.
- Los valores por defecto del prototipo son los documentados en Appian 26.6–26.10: card NONE (blanca) con padding LESS, sección con etiqueta ACCENT, grid LIGHT sin sombreado, asistente DOT_VERTICAL a ancho FULL, tag ACCENT, KPI con icono STANDARD.
- Tipografía Open Sans (la de Appian); si el cliente configura su tipografía en Admin Console, el sistema real la mostrará.
- Sin perfil CSS (la marca estándar), el borde de los campos se pinta con 3:1 sobre blanco y sobre el gris de página (`#828588`, WCAG 1.4.11); Appian sin perfil puede pintarlo más claro.
- Los gráficos son SVG simplificados (sin animaciones ni tooltips enriquecidos).
- Si la pantalla no declara `contentsWidth`, el contenido se limita a 1440 px y se centra (convención del kit). Con `contentsWidth: FULL`, o con un panel dentro, ocupa todo el ancho, como en Appian, donde lo limita el ajuste de ancho de página del Site. A 1440 px o menos no se nota.
- **Se validan pero no se simulan** (el inspector los enseña): los de servidor y refresco (`refreshAlways`, `refreshInterval`, `refreshOnVarChange`, `loadDataAsync`), los de accesibilidad sin efecto visible (`iconAltText`, `announceBehavior`, `inputPurpose`, `rowHeader`), los que dependen del entorno (`groupFilter`: el selector propone todos los usuarios del prototipo; los destinos de `a!startProcessLink`, `a!processTaskLink` y `a!reportLink`, que se simulan con `$action`) y algunos que en Appian sí se ven: la cabecera fija (`isHeaderFixed`), reordenar las filas de un grid editable (`allowRowReordering`), el mensaje al terminar de `a!startProcessLink` (`bannerMessage`), el formato de la tendencia de un KPI (`trendFormat`), la descarga de imagen de los gráficos (`allowImageDownload`), el recuento de seleccionados y el menú de filtros de un grid (`showSelectionCount`, `showManageFiltersMenu`) y los métodos de subida de ficheros (`uploadMethods`). Si una pantalla depende de uno de ellos para entenderse, dilo en su `$note`.
- El menú del site en móvil se desplaza horizontalmente; Appian lo pliega en un menú.
