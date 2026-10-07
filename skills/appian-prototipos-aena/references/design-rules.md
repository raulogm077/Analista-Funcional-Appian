# Guía de diseño UX (AENA · Appian 26.9)

Esta guía adapta el **SAIL Design System** oficial de Appian (docs.appian.com/suite/help/26.9/sail/) a la marca AENA. Sirve para que todas las pantallas se parezcan entre sí y para que el equipo pueda construirlas en Appian sin decidir nada de diseño.

El validador comprueba las reglas marcadas con ✔ y las muestra como avisos `UX ·`. Al final de la validación imprime la línea «Calidad UX: N avisos». El resto se revisa con la rúbrica (§17).

Los bloques con los que se componen las pantallas (cabeceras, KPI, listas, grids con detalle, cards, IA, calendario, comentarios, kanban…) están en `references/bloques.md`, con cuándo usar cada uno; la galería navegable está en `galerias/bloques/`. Los 147 componentes de interfaz de Appian 26.9, uno a uno y agrupados como en la documentación, están en `galerias/componentes/`.

## 0. Antes de diseñar una pantalla

Contesta estas tres preguntas en el brief de diseño (SKILL.md, paso 1):

1. **¿Cuál es la tarea principal del usuario en esta pantalla?**
   - Esa tarea ocupa el primer sitio visual: arriba y a la izquierda, con el mayor tamaño.
   - Lo demás queda a un clic: en otra vista, en un diálogo o en «Ver todos».
2. **¿Quién la usa y con qué frecuencia?**
   - Un usuario ocasional necesita un flujo guiado y poca densidad.
   - Un experto (quien revisa, gestiona o aprueba) agradece pantallas densas y atajos.
3. **¿Qué necesita ver de un vistazo?**
   - Estado, plazo, responsable, importe… van en la cabecera o en una franja de datos clave, nunca en la posición 14 de una lista de campos.

Pregunta de control, del SAIL Design System: «¿qué falta aquí que el usuario necesite? ¿qué sobra?».

## 1. Site y marca (objeto Site de Appian)

La configuración está en `assets/brand-aena.json → site` y se copia tal cual en el objeto Site.

| Propiedad del Site | Valor |
|---|---|
| Navigation layout | HEADER_BAR, estilo MERCURY (subrayado en la página seleccionada) |
| Background Color | `#1A2732` (azul marino AENA) |
| Selected Page Highlight Color | `#90CE00` (verde AENA) |
| Accent Color | `#527500` (verde oscuro: enlaces, pestañas, bordes OUTLINE; contraste AA sobre blanco) |
| Loading Bar Color | `#90CE00` |
| Button / Input / Dialog Shape | SEMI_ROUNDED |
| Logo | `assets/logo-aena-on-dark.svg` (símbolo + «aena», sin el lema) |
| Tipografía | Open Sans (por defecto en Appian). AenaSansNew solo si se configura como Custom Typeface en Admin Console |

### Perfil CSS de AENA (Appian 26.9, `brand-aena.json → cssProfile`)

Lo que el objeto Site no alcanza (colores de estado, textos de los campos, bordes, radios, sombras, tooltips) se fija con un **perfil CSS** de Appian (Admin Console › Branding › CSS Profiles; capacidades avanzadas y premium). `build.py` lo aplica al prototipo y deja junto al HTML el fichero `<prototipo>-perfil-css.txt`, listo para pegar.

- Solo lleva lo que cambia respecto a Appian: lo que no está en el perfil conserva el valor estándar.
- Colores de estado accesibles: `warn-on-light-color: #9A5200` (el ámbar estándar de Appian, `#D97706`, se queda en 3,2:1 sobre blanco), `positive-on-light-color: #0E6B00`, `negative-on-light-color: #B2002C`, `info-on-light-color: #115EBB`, y los fondos de estado de AENA (`#FCDCDC`, `#E3EFD3`, `#FCEFCA`, `#DDE7F0`). Todos cumplen 4,5:1 sobre blanco y sobre su fondo.
- Campos: etiqueta en azul AENA, instrucciones en `#525C65`, marcador de posición en `#6B747C` y borde `#848D96` (3:1 sobre blanco y sobre el gris de página, WCAG 1.4.11).
- Tarjetas con sombra suave teñida de azul AENA y radio de 8 px; tooltips en azul AENA.
- Si el cliente no tiene el nivel avanzado, el prototipo sigue siendo válido: sin perfil, Appian usa sus colores estándar y los parámetros de SAIL no cambian. Indícalo en el documento funcional.
- No toques las propiedades de color de los botones salvo que se definan todas las de un estilo (Appian completa las que falten y el resultado cambia).

- Como máximo **8 páginas de primer nivel** ✔ (Appian admite 10 ✔; con más de 8 la barra se satura).
- **Iconos y nombres de página** (ux-site-branding#style-header-bar-only): con MERCURY, la barra de AENA, y con OXYGEN no se ven iconos de página en web, y el nombre de la página solo aparece si hay más de una. HELIUM pinta el icono encima del nombre y la barra lateral (SIDEBAR) lo pinta siempre. Ninguna página depende de su icono para entenderse; el prototipo pinta la barra como Appian.
- Ordena las páginas por frecuencia de uso: primero lo que se usa a diario, al final los datos maestros.

## 2. Fondo de página, cards y secciones

**Páginas de contenido** (inicio, listados, vistas de registro, informes):
- La raíz es `a!headerContentLayout(backgroundColor: "TRANSPARENT")`, que en Appian es gris claro.
- Encima van **cards blancas con sombra y sin borde**: `a!cardLayout(style: "NONE", showBorder: false, showShadow: true, shape: "SEMI_ROUNDED", padding: "STANDARD")`. Es el helper `content_card()`.
- **Borde o sombra, nunca las dos cosas ✔**: sobre fondo gris, sombra; sobre fondo blanco, borde.

**Formularios, asistentes y diálogos:** fondo `WHITE`, sin cards de contenido. Las secciones separan los bloques.

**El color de una card:**
- `style: "NONE"` es blanco y es el valor por defecto. `STANDARD` es **gris** y solo sirve para mensajes de ayuda que se pueden cerrar o para estados vacíos.
- **No colorees una card entera para indicar un estado**: colorea el icono o el texto.

**Títulos de sección en páginas con cards:**
- El título H2 va **encima de la card**, no dentro ✔: `a!sectionLayout(label, labelSize: "MEDIUM", labelHeadingTag: "H2", labelColor: "STANDARD")` y dentro, la card. Es el helper `section_card()`.
- Dentro de una card, los subtítulos son `labelSize: "SMALL"`, H3, `labelColor: "SECONDARY"` y en mayúsculas (helper `subsection()`).

**Anidar:**
- No anides cards ni boxes con borde ✔. Los controles con marco propio (opciones de `a!cardChoiceField`, casillas con `choiceStyle: "CARDS"`) son campos, no cards: pueden ir dentro de una card con borde.
- Una lista de cards seleccionables no va dentro de otra card.

**La barra decorativa** (`decorativeBarPosition`):
- Úsala solo en las cards que destacan algo: la franja de KPI o el aviso de acción.
- Va en la **misma posición** en toda la pantalla y nunca comunica un significado por sí sola.

**Una idea por layout:** no uses cards a la vez como secciones, como botones y como cabeceras en la misma pantalla.

**Secciones plegables:**
- Úsalas solo con un motivo claro: el usuario salta directamente a una de ellas.
- **No mezcles plegables y fijas ✔.**
- **Nunca uses secciones plegables como navegación entre áreas de un registro**: para eso están las vistas (§8).

## 3. Jerarquía de títulos

| Elemento | Tamaño | Etiqueta | Color |
|---|---|---|---|
| Título de página (uno y solo uno por pantalla ✔) | `a!headingField` LARGE o sección LARGE | H1 | STANDARD |
| Sección principal | MEDIUM | H2 | STANDARD (las secciones son ACCENT por defecto en Appian: pon `labelColor: "STANDARD"`) |
| Subsección o grupo de datos | SMALL, EN MAYÚSCULAS | H3 | SECONDARY |
| Etiqueta de dato en un resumen | texto SMALL | — | SECONDARY |

- La etiqueta H corresponde al tamaño ✔ (LARGE → H1, MEDIUM → H2, SMALL → H3).
- No des estilo de título a un dato: el nombre de una persona o de una empresa no es un H2.
- El título de la página no cambia cuando el usuario selecciona algo en ella.

## 4. Color y contraste

Guía de color del SAIL Design System (ux-color-overview) aplicada a AENA: **paleta corta, bloques de color en el perímetro de la página y color para resaltar lo que importa**, siempre con el mismo significado.

- **Bloques de color en el perímetro**: la cabecera del site, la cabecera de la ficha (`headerBackgroundColor` azul marino) y la cabecera «hero» del inicio o de una portada (`hero_header()`). No pintes bloques de color en mitad de la página para «alegrarla».
- **Color para resaltar**: los sellos de icono de los KPI (`kpi()`: iconStyle STAMP con el acento), la barra decorativa verde de la franja de KPI, las etiquetas de estado y las barras de un gráfico por estado. Cada color nuevo compite por la atención: pregunta qué debe ver el usuario primero.
- **Capas con transparencia** (`#RRGGBBAA`): tintes suaves para fondos de tarjetas de estado, eventos de calendario o el día de hoy (`#90CE0033`), sin tapar lo que hay debajo.
- **Estados**: usa la paleta semántica común de `brand-aena.json → states`, con el mismo mapa `estadoColor` en toda la app.

| Categoría | Tag (fondo apagado, texto STANDARD) | Icono, texto o barra de gráfico | Ejemplos |
|---|---|---|---|
| neutral | `#EEF0F2` | SECONDARY (`#525C65` en gráficos) | Borrador, cerrado, cancelado |
| enCurso | `#DDE7F0` | `#1A2732` | En curso, en tramitación, en revisión |
| atencion | `#FCEFCA` | WARN (`#9A5200` con el perfil CSS) | Pendiente de terceros, vence pronto |
| positivo | `#E3EFD3` | POSITIVE (`#0E6B00`) | Aprobado, vigente, completado |
| negativo | `#FCDCDC` | NEGATIVE (`#B2002C`) | Rechazado, vencido, alerta |

- **Tags en filas de un grid: siempre con fondo apagado** (patrón de Appian). Los colores vivos (`POSITIVE`, `NEGATIVE` sólidos) se reservan para los pocos valores que de verdad deben saltar a la vista.
- Como máximo **dos colores no neutros por grid**: en las filas de un listado, solo **atencion** y **negativo** llevan color y el resto de estados va en neutro (`state_map(..., grid=True)`). En la ficha, un solo registro, se usa la paleta completa (`state_map(...)`). Los iconos de alerta de una columna van todos del mismo color, con `caption`.
- **Gráficos por estado**: cada barra con el color de su estado (`state_chart_colors(mapa, orden)` + agrupación secundaria por el mismo campo, sin leyenda), el mismo significado que las etiquetas.
- **Todo estado tiene su categoría en el mapa**: un estado sin mapear sale gris y puede esconder justo lo que pide acción.
- **Nunca uses el color solo**: acompáñalo siempre de texto o de un icono con tooltip.
- **El color de acento solo se usa en enlaces ✔**: un texto verde oscuro que no es un enlace parece clicable.
- Gráficos: un único esquema en toda la interfaz (`chartColorScheme` de la marca: azul marino, verde `#72A300`, azul acero, rosa, naranja `#E07000`…; todos con 3:1 o más sobre blanco). Como máximo 5 colores; una sola serie lleva un solo color. El verde lima `#90CE00` va el último y solo con etiquetas de datos ✔.
- El verde AENA `#90CE00` se usa en el botón principal (con texto azul marino: 8:1), en el resaltado de navegación, en la barra decorativa de la franja de KPI y como enlace sobre fondos azul marino. No se usa como fondo de cards ni como texto sobre blanco (1,9:1).

### Contraste (WCAG 2.2 AA)

| Qué | Mínimo | Cómo se comprueba |
|---|---|---|
| Texto normal | 4,5:1 | `validate.py` (aviso «UX · contraste» con un color alternativo) y `contrast_audit.py` sobre el prototipo |
| Texto grande (24 px, o 18,66 px en negrita) | 3:1 | ídem |
| Iconos que informan, bordes de campos, series de gráficos | 3:1 | ídem (WCAG 1.4.11) |

Parejas que funcionan (medidas): texto `#1A2732` o `#525C65` sobre cualquier fondo claro de la paleta; acento `#527500` sobre blanco (5,4:1) y sobre el gris de página (4,9:1), **no** sobre los fondos de estado azul o rojo (4,2–4,3:1); blanco sobre azul marino (15:1), sobre el acento (5,4:1) y sobre los colores de estado del perfil. En fondos oscuros, los enlaces cambian de color solos (26.9) y el prototipo los pinta en verde lima.

`contrast_audit.py prototipo.html app.json` mide en el navegador cada texto, marcador de posición, borde de campo y texto de gráfico de todas las pantallas (vistas de registro y pasos de asistente incluidos) con los colores del perfil CSS. Debe acabar con **0 combinaciones por debajo de AA**; el texto sobre fotos no se mide: comprueba que lleva un overlay oscuro.

## 5. Botones y acciones

| Uso | Configuración |
|---|---|
| Acción principal (la más frecuente) | `style: "SOLID"`, `color: "#90CE00"`. **Una sola por pantalla ✔** |
| Resto de acciones | `style: "OUTLINE"`, `color: "ACCENT"` (es el valor por defecto) |
| Destructiva (pérdida real de datos: borrar, anular sin vuelta atrás) | `style: "GHOST"`, `color: "NEGATIVE"` y `confirmHeader`/`confirmMessage` ✔ (helper `danger()`, que la exige). Nunca SOLID |
| Barra de herramientas encima de un grid o dentro de una card | `size: "SMALL"`, `style: "OUTLINE"`, `color: "SECONDARY"` (helper `tool_button()`) |
| Botón solo con icono | `accessibilityText` obligatorio ✔ |

- Cancelar, cerrar o archivar algo que se puede retomar no es destructivo: botón normal y, si se pierde trabajo sin guardar, confirmación.
- **Pie de formulario**: los botones de envío a la derecha, con el principal SOLID; «Anterior» y «Cancelar» a la izquierda, en ese orden. Siempre hay un «Cancelar».
- **Los botones llevan un verbo**, y ese verbo coincide con el título del formulario: «Enviar a revisión» abre «Enviar a revisión»; nunca «Aceptar».
- Un botón que no está disponible en ese momento se **desactiva**, no se oculta, y la pantalla dice por qué. Si lo que falta es un dato del formulario, el botón queda activo y valida con un mensaje.
- **Acciones de registro en la cabecera**:
  - Como máximo 3 atajos ✔, con títulos cortos. El resto van en la vista o en un menú (`MENU`).
  - Estilo `TOOLBAR_PRIMARY` si hay una acción principal clara; `TOOLBAR` si no la hay.
- Dentro de una página, las acciones de registro se configuran según el contexto:
  - `TOOLBAR` encima de un grid.
  - `SIDEBAR` como lista de acciones en una columna.
  - `CARDS` en la página de inicio.
  - `CALL_TO_ACTION` para una única acción con espacio alrededor.
  - `LINKS` en sitios estrechos.

## 6. Estructura por patrón

| Patrón | Raíz | Estructura |
|---|---|---|
| P01 Listado | `a!headerContentLayout` TRANSPARENT | Ver abajo |
| P02 Vista de registro | Record view | Ver §8 |
| P03 Formulario | `a!formLayout` WHITE, `contentsWidth: "NARROW"` o `"MEDIUM"` | Ver abajo |
| P04 Asistente | `a!wizardLayout` | Ver abajo |
| P05 Tarea de aprobación | `a!formLayout` WIDE o `a!paneLayout` dentro del form | Ver abajo |
| P06 Inicio | `a!headerContentLayout` TRANSPARENT | Ver abajo |
| P07 Diálogo | `a!formLayout` (o `a!wizardLayout`) `contentsWidth: "FULL"`, título en `titleBar` | Ver abajo |
| P08 Informe | `a!headerContentLayout` TRANSPARENT | Ver abajo |
| P09 Maestro-detalle | `a!headerContentLayout` TRANSPARENT | Ver abajo |
| P10 Portada de módulo | `a!headerContentLayout` TRANSPARENT | Ver abajo |
| P11 Asistente de IA | `a!headerContentLayout` o `a!paneLayout` | Ver abajo y §14 |
| P12 Revisión de datos sugeridos por IA | `a!formLayout` WHITE, `contentsWidth: "FULL"` | Ver abajo y §14 |

**P01 Listado**
- Cabecera de página (`page_header()`): H1, descripción SECONDARY de una línea y el botón principal «Nuevo X».
- Si hay algo que requiere atención: un aviso de acción (`action_banner()`) con su botón dentro.
- Una card con un `a!gridField`:
  - buscador y como máximo 4 `userFilters` en la barra del grid, más exportar;
  - de 25 a 50 filas en un listado a página completa, y 5–10 cuando el grid comparte la página;
  - como máximo **7 columnas** (§7).
- Con asistente de datos (si el análisis lo pide): `a!paneLayout` con el listado en un pane `AUTO` y el chat de datos en un pane lateral que se muestra u oculta (`ai_side_pane()` + `ai_toggle()`).
- **Página Record List**: si el listado solo sirve para buscar, filtrar y abrir la ficha, en Appian es una página del site de tipo Record List (la lista configurada en el record type, con búsqueda, filtros de usuario, exportación y acciones de lista), no una interfaz con un grid (BP 09 §1.3, BP 01 §9). Interfaz solo si lleva algo más (aviso de acción, KPI, asistente de datos). `app.json` no declara el tipo de página: dilo en el `$note` de la pantalla.

**P03 Formulario**
- `a!headerTemplateSimple` o `a!headerTemplateFull` con el verbo de la acción.
- Una columna estrecha con `a!sectionLayout` por bloque (MEDIUM, H2). Solo los campos cortos relacionados van en pareja.
- Si hace falta contexto (datos del expediente, ayuda), usa `a!sidebarTemplate`.
- Botones con `a!buttonLayout`.

**P04 Asistente**
- De 3 a 6 pasos, con un estilo vertical si hay más de 5 ✔ y `MINIMAL` si hay 1 o 2 ✔.
- Con `a!sidebarTemplate` (NAVY o `#1A2732`), la barra lateral lleva el título y el hito vertical.
- El último paso es «Revisión»: un resumen por secciones en solo lectura, con un enlace «Editar» que lleva al paso correspondiente.

**P05 Tarea de aprobación**
- Cabecera con el código, el asunto y el **plazo destacado** (tag de atención si vence en ≤3 días).
- A la izquierda, el resumen en solo lectura y el documento (`a!documentViewerField`).
- A la derecha, la card «Decisión»: `a!cardChoiceField` con `a!cardTemplateBarTextStacked` e icono de color por opción (aprobar POSITIVE, devolver WARN, rechazar NEGATIVE), seguida de los comentarios, obligatorios según la decisión.

**P06 Inicio**
- Saludo H1 y botón principal.
- **Franja de KPI**: 2–4 `a!kpiField` en **una sola card** con `columnsLayout(showDividers: true, spacing: "SPARSE")`, sombra y barra decorativa TOP verde. Cada KPI lleva tendencia (`secondaryMeasure` o `$secondaryValue`) y usa `trendColor: "REVERSE"` cuando bajar es bueno.
- En columnas 2X / 1X:
  - a la izquierda, «Mis tareas»: 5–10 filas **sin paginación**, con el enlace «Ver todas» y el plazo como tag;
  - a la derecha, avisos o accesos rápidos (`a!recordActionField` CARDS o cards enlazadas) y un gráfico resumen SHORT con su tabla (`chart_table()`).

**P07 Diálogo**
- Título con el verbo de la acción.
- De 2 a 6 campos en una columna, con `contentsWidth: "FULL"` ✔: el formulario ocupa el cuadro. El ancho del cuadro lo fija la acción de registro (Dialog Width, en el record type) y se ajusta a lo que se escribe; en el prototipo, `$dialogWidth` (`NARROW` para pocos campos; helper `dialog()`).
- Un asistente en diálogo lleva altura fija, nunca «Auto»: saltaría de un paso a otro.
- «Guardar» SOLID + «Cancelar».
- Si el diálogo es largo, fija la barra de título y los botones (`isTitleBarFixed`, `isButtonFooterFixed`).

**P08 Informe**
- Cabecera.
- **Barra de filtros de página** (una card con 2–4 desplegables en fila) si los filtros afectan a todos los gráficos.
- Franja de KPI.
- Gráficos en cards, `height: "SHORT"` o `"MEDIUM"`, con `referenceLines` para objetivos o umbrales y `showDataLabels` cuando hay pocas barras.
- **Más de 7 puntos o categorías: solo en la fila ✔**, a todo el ancho y por encima de las filas de dos. Los pequeños, de dos en dos para compararlos (BP 02 §5A.3).
- **Cada gráfico con su tabla ✔**: «Ver como tabla» alterna el gráfico y una tabla con los mismos datos (`chart_table()`, BP 02 §9.5).
- Drilldown: un clic en una categoría muestra el grid filtrado debajo del gráfico (`config.link` con `chart_link()`; el grid filtra por la variable). El drilldown no se usa con teclado: la tabla del gráfico sigue siendo obligatoria.

**P09 Maestro-detalle**
- Para revisar muchos elementos uno tras otro sin cambiar de página (bandejas, colas de revisión).
- Grid a la izquierda con `selectionStyle: "ROW_HIGHLIGHT"`, `maxSelections: 1`, 7–10 filas y **una fila seleccionada al entrar**; detalle en una card a la derecha (`MEDIUM_PLUS`) con la acción principal (`grid_with_detail()`).
- Sin selección, una pista en cursiva («Seleccione una fila…»), nunca un hueco en blanco.
- Si el detalle no cabe al lado, `drilldown()`: el detalle sustituye al grid y «Volver» va arriba a la izquierda. **Nunca el detalle debajo del grid.**

**P10 Portada de módulo**
- `hero_header()` con el nombre del área, una línea de contexto, 2–4 cifras en línea y la acción principal.
- «¿Qué quiere hacer?»: 2–6 accesos como cards-botón (`cards_as_buttons()`), con iconos del mismo estilo.
- Debajo, en 2X / 1X: actividad reciente (`a!eventHistoryListField` PREVIEW_LIST con «Ver toda la actividad») y, a la derecha, avisos de acción y enlaces de ayuda.

**P11 Asistente de IA** (§14)
- Chat del agente en una card sin relleno (`content_card(..., padding="NONE")`) y, al lado, lo que propone en campos editables que el usuario revisa y guarda, con el aviso de fiabilidad y la valoración.
- Variantes: a página completa (`height: "FILL"`), documento + chat (`ai_doc_chat()`) y chat de datos en panel lateral (`ai_side_pane()`).

**P12 Revisión de datos sugeridos por IA** (§14)
- Aviso INFO que explica qué ha rellenado la IA y qué hay que revisar.
- `ai_review_grid()`: campo, valor editable, origen («Sugerido por IA» / «Editado»), confianza y casilla «Revisado» en los de confianza baja; al editar un valor queda marcado como editado y revisado.
- La fuente al lado: `a!documentViewerField` que salta a la página del dato y lo resalta al pulsar «Página N».
- «Guardar» valida: si queda algún dato de confianza baja sin revisar, el formulario lo dice con un mensaje (`ai_review_validation()` en `validations`). Nunca un botón desactivado sin explicación.

## 7. Grids

Aquí fallan casi todos los listados. Las reglas:

- **Columnas**: como máximo **7** en un listado ✔. Si hay más datos:
  - **Consolidar columnas**: una celda con una línea principal y otra SECONDARY SMALL debajo (código + título; persona + unidad; paso + fase). Es el helper `two_line()`. Como máximo 2–3 líneas por celda.
  - Mover lo secundario a la ficha. El listado sirve para encontrar, la ficha para leer.
- **La primera columna** va alineada a la izquierda y lleva el enlace a la ficha (`a!recordLink`). Configura `rowHeader: 1` ✔.
- **Alineación**:
  - Importes, cantidades y porcentajes a la derecha (`align: "END"`) ✔.
  - Texto y fechas a la izquierda.
  - Una columna de solo iconos va centrada, con ancho `ICON`.
- **Anchos**: `AUTO` por defecto. Para las columnas cortas (fechas, códigos, estados), `NARROW` o `NARROW_PLUS`. Si el texto se parte en más de 2 líneas, sobran columnas.
- **Acciones**: una por celda ✔. Si hay varias, en una barra de herramientas encima del grid (`TOOLBAR`) o con `a!recordActionField` de solo icono en su columna (BP 02 §5.4).
- **Estados**: un tag con el mapa de la paleta semántica. **Alertas**: iconos en una columna `ICON` con `caption` (tooltip), nunca un icono rojo suelto sin explicación.
- **Celdas vacías**: «–». Nunca «N/A» ni una celda en blanco.
- **Estilo**:
  - `borderStyle: "LIGHT"` y `spacing: "STANDARD"`; `DENSE` solo para listas largas de expertos.
  - `shadeAlternateRows` solo para muchos datos.
  - **El mismo estilo en todos los grids de la pantalla ✔.**
- **Filtros**:
  - Hasta 4 `userFilters` en la barra del grid, más el buscador.
  - Los filtros que se usan a diario se convierten en **vistas guardadas** (pestañas o accesos «Mis informes», «Con alertas»). No hagas una card de 8 desplegables encima del grid.
- **Vacío**: `emptyGridMessage` concreto ✔, por ejemplo «No hay informes con alertas».
- **Maestro-detalle**: `selectionStyle: "ROW_HIGHLIGHT"`, `maxSelections: 1`, una fila seleccionada al entrar y el detalle **al lado**, nunca debajo.
- **Mapa de calor**: `a!gridColumn.backgroundColor` con `SUCCESS`, `WARN` o `ERROR` según un umbral, y `accessibilityText` que explique el color.
- **Grids editables** (`a!gridLayout`): todo alineado a la izquierda, incluidos los números.

## 8. Vista de registro (P02)

**Cabecera** (configuración del record type):
- Migas de pan.
- El título es `código · nombre corto`. Si el nombre es largo, se recorta con criterio.
- Como máximo **3 atajos de acción**.
- Fondo opcional `headerBackgroundColor: "#1A2732"`: continúa la barra del site y da peso a la ficha.

**Vistas (pestañas)**:
- **Resumen** siempre.
- Una vista por cada área 1:N con volumen propio (Documentación, Comunicaciones, Planificación, Presupuesto, Historial…), con **un máximo de 7 ✔**. Agrupa las áreas pequeñas: «Comunicaciones» puede reunir las comunicaciones con la unidad asistente, las consultas internas y los organismos externos, con `a!tabLayout` o con subsecciones dentro.
- **Nunca apiles 10 secciones plegables en el resumen.**

**Resumen**:
1. **Franja de datos clave** (`key_facts()`): una card con 4–6 datos en columnas con divisor (etiqueta SECONDARY SMALL y valor MEDIUM_PLUS), además del estado como tag y el hito del ciclo de vida (`a!milestoneField`, `stepStyle: "LINE"`).
2. Aviso de acción, si lo hay: vence pronto, falta un documento.
3. Columnas 2X / 1X:
   - **Izquierda: datos 1:1**, agrupados en cards con subsecciones. Presenta los datos **como resumen fácil de leer** (`field_summary()`): 2–3 columnas, etiqueta encima en SECONDARY, sin etiquetas ADJACENT de 240 px que dejan el valor en una columna estrecha. Los textos largos (descripción, motivo) van a ancho completo.
   - **Derecha: listas 1:N cortas**: responsable y equipo con avatar, documentos recientes con el icono de su tipo, próximas fechas. Cada lista termina en «Ver todos» → vista correspondiente.
4. Historial en su vista: `a!eventHistoryListField(eventStyle: "TIMELINE")`.

## 9. Formularios

- **Una columna estrecha**. Los usuarios no se quejan de hacer scroll, y dos secciones lado a lado recargan la pantalla. No centres el formulario con columnas vacías: `contentsWidth` lo centra solo.
- **Qué estructura elegir**:
  - Pasos secuenciales: asistente.
  - Bloques que se rellenan en cualquier orden: `a!tabLayout` dentro del form.
  - Todo visible a la vez: secciones.
  - Dos columnas largas con scroll propio: `a!paneLayout` dentro del form.
- **Etiquetas**: todo campo lleva `label` ✔; si no debe verse, `labelPosition: "COLLAPSED"` (el lector de pantalla la lee). Siempre `ABOVE` en los campos editables ✔. En los de solo lectura, `ABOVE` en resúmenes y `ADJACENT` solo en listas cortas. No mezcles posiciones en una misma card. El placeholder no sustituye a la etiqueta.
- El ancho de cada campo se ajusta a lo que se espera escribir: fechas y códigos en pareja con `a!columnsLayout`; textos largos a ancho completo.
- **Elegir la forma de selección**:
  - 2–3 opciones: `a!radioButtonField` COMPACT, con la opción más habitual marcada ✔ (BP 02 §4.8). Sin opción marcada solo si el usuario debe decidir sin sugerencia (una decisión de aprobación), con `$uxIgnore`.
  - Hasta 6 opciones que necesitan explicación o icono: `a!cardChoiceField` (Tile o BarTextStacked).
  - Más de 5 opciones: `a!dropdownField`.
  - Muchas o con búsqueda: picker.
  - Un sí/no que se aplica en el momento: `a!toggleField`. Un sí/no dentro de un formulario: `a!booleanCheckboxField`.
- **Obligatoriedad y validación**:
  - `required` con `requiredMessage` concreto.
  - Las reglas de negocio van en `$validations` con el ID de la regla («(RB-004)»). Fuera de los mensajes de validación, **los IDs de requisito no se muestran al usuario** (ni en avisos ni en instrucciones): la trazabilidad va en `req` y en `$note`.
  - Las longitudes en `characterLimit`.
  - Las instrucciones cortas en `instructions`.
- En formularios largos o críticos, usa un paso de revisión y una confirmación: número de caso, qué pasa ahora y un botón para volver.

## 10. Estados vacíos, avisos y confirmaciones

- **Nunca una pantalla o un grid en blanco.** Estado vacío (`empty_state()`):
  - una card STANDARD con icono MEDIUM centrado;
  - el mensaje en MEDIUM_PLUS;
  - una línea SECONDARY que sugiere el siguiente paso;
  - el botón de acción.
- **Aviso de acción** (`action_banner()`): una card WARN/INFO con barra decorativa START, icono, texto y el botón o enlace dentro. No lo separes del botón. Si el documento define la acción que resuelve el aviso (renovar, responder), el botón la abre; si no, el aviso lleva a la lista filtrada o a la vista donde se resuelve.
- **`a!messageBanner`** para mensajes de sistema accesibles (confirmación tras guardar, errores de envío).
- **Confirmación de borrado**: `confirmHeader` con el objeto («¿Borrar el documento?») y `confirmMessage` con la consecuencia.

## 11. Textos y formatos

- En español, con mayúscula solo en la primera palabra («Nuevo expediente»).
- Los mensajes de una sola frase no llevan punto final.
- Mensajes de vacío concretos, con el nombre de la entidad del proyecto: «No hay expedientes que cumplan los filtros».
- Fechas dd/mm/aaaa; importes `1.234,56 €` (filtros `date` y `eur`); separador de miles en las cifras, salvo en los identificadores.
- Códigos con el formato que fija el documento del proyecto (p. ej., `XXX-AAAA-NNNN`); si no lo fija, uno así, con prefijo propio, y un `$assumption`.
- Los campos de solo lectura no llevan asterisco de obligatorio.

## 12. Accesibilidad

- Una etiqueta H por nivel y un solo H1 ✔.
- `accessibilityText` en botones solo con icono, en mapas de calor y en KPI de color.
- Contraste (§4): 4,5:1 en texto, 3:1 en texto grande, iconos que informan, bordes de campos y series de gráficos. `validate.py` avisa de los colores explícitos que no llegan y propone uno que sí; `contrast_audit.py` mide la pantalla real. El verde `#90CE00` lleva texto azul marino y nunca se usa como texto sobre blanco.
- Los botones solo con icono llevan `accessibilityText` (se lee como nombre del botón) y `tooltip`.
- Los navegadores, el organigrama, el calendario y el kanban se usan con teclado: cada nodo, día o tarjeta es un botón con nombre accesible.
- `stackWhen` por defecto en columnas (PHONE). En pantallas densas, comprueba cómo se ven en tablet.

## 13. Datos de ejemplo

- Realistas y del dominio del proyecto (el de su análisis funcional, no el de un ejemplo del kit): aeropuertos por código IATA, personas y empresas verosímiles, importes creíbles. Nunca «Lorem ipsum» ni «Test 1».
- 10–20 filas en la entidad principal, con todos los estados representados.
- Coherencia entre pantallas: el mismo registro muestra los mismos datos en el listado, la ficha, la tarea y las capturas.
- Personas ficticias. Nunca datos personales reales de empleados de AENA.

## 14. Inteligencia artificial

Solo se diseña IA si el análisis la pide. Si la propones tú, va marcada con `$assumption` («Propuesta: …»), con el beneficio concreto, y nunca sustituye al flujo manual. Los componentes y bloques están en `bloques.md` §5.

1. **Elige el componente por el origen de la respuesta**:
   - un agente que usa herramientas o hace tareas → `a!agentChatField` (26.6);
   - un registro concreto → `a!recordsChatField` en su vista resumen;
   - los datos de varios record types → `a!dataFabricChatField`;
   - un conjunto de documentos → `a!documentsChatField` (preguntas concretas, no resúmenes);
   - lógica o modelo propios, o respuestas con componentes (citas, botones) → `a!chatField` + `a!chatMessage`.
2. **Colocación**:
   - chat de datos: solo en un `a!pane` que se muestra u oculta, **sin nada encima ni debajo** ✔;
   - chat de registro y de datos: nunca en `a!sideBySideLayout` ✔;
   - chat de agente: a página completa con `height: "FILL"` o en una card junto al contenido (26.7+: `showBorder: true`);
   - documento + chat: dos columnas, chat a la izquierda y visor a la derecha.
3. **Estado inicial en español, concreto** ✔: título contextual (nunca el de por defecto ni el mismo texto que el H1), `welcomeMessage` o `initialMessage` que diga qué puede hacer y hasta 3 preguntas sugeridas que sepa responder donde el componente las admite (chat de datos y de registro). El chat del agente no tiene preguntas sugeridas: pon un ejemplo de pregunta en el `welcomeMessage`.
4. **Fiabilidad**: junto a toda salida de IA, un aviso breve para comprobarla (`ai_notice()`). No uses el chat para cifras que exigen exactitud.
5. **La fuente, siempre que se pueda**: cita con la página que abre el visor y resalta el texto (`ai_citation()`); en extracción, «Página N» por dato.
6. **La IA propone, el usuario decide**: lo que devuelve (`outputsSaveInto`, extracción, clasificación) rellena campos editables; guardar o enviar es una acción del usuario. Marca el origen («Sugerido por IA», «Editado») y valida al guardar: un mensaje dice qué datos de confianza baja faltan por revisar.
7. **Nunca muestres la puntuación de similitud** ✔: ordena por relevancia y, si hace falta, la calidad en palabras (`match_quality()`).
8. **`debugMode` desactivado** ✔ en pantallas de usuario: las entradas y salidas de las herramientas solo sirven al desarrollador.
9. **Control**: el usuario puede detener una respuesta (26.7) y seguir en la misma conversación; el selector de conversaciones solo si el caso de uso tiene varias.
10. **Estados de error previstos**: bloqueo por guardrail (mensaje del administrador, la conversación sigue), función no habilitada, documento no disponible. En el prototipo, `$state`.
11. **Valoración**: pulgar arriba/abajo alrededor de las respuestas (`ai_feedback()`) y a quién escalar si el agente no resuelve.
12. **Límites de la plataforma**: los chats de IA no funcionan en Portals, offline, Appian Mobile ni Appian for Windows; prevé una alternativa. Solo inglés garantizado en algunos componentes: indícalo como supuesto si el usuario escribe en español.

## 15. Cabeceras de página y navegación secundaria

- **Cabecera**: `page_header()` en páginas de trabajo; `hero_header()` solo en inicio o portada de módulo; migas (`crumbs`) cuando la página está dentro de una jerarquía, nunca como historial.
- **Barra de filtros de página** (`filter_bar()`) solo si los filtros afectan a varios bloques; los de un solo grid van en su barra (`userFilters`).
- **Navegación secundaria**: prefiere `a!tabLayout`.
  - Horizontal con **menos de 7** pestañas ✔ y etiquetas cortas.
  - Vertical con **más de 6**, varios niveles o etiquetas largas: `a!tabLayout(orientation: "VERTICAL")` (26.7), sin límite de pestañas (secondary-navigation, ux-tab-layout); en proyectos anteriores a 26.7, `side_nav()`.
  - Sobre fondo gris con cards, la navegación vertical va sin card ni divisor alrededor.
  - Nada de navegación solo con iconos para usuarios ocasionales.
- **Vistas de registro** para las áreas 1:N (§8); pestañas dentro de una vista solo para bloques del mismo tema.

## 16. Patrones y componentes nuevos de Appian 26.9

- **Calendario** (`calendar_month()`, `calendar_week()`): cuando importa cómo se reparten eventos y plazos en el tiempo. Mes con panel del día a la derecha para ver el detalle sin salir; semana para comparar pocos días. Tipos de evento con icono y color (`event_maps()`), hoy resaltado y lo pasado atenuado.
- **Hilo de comentarios** (`comment_thread()`): conversación sobre un registro, en su propia vista o columna de la ficha o al final de la página. Comentario nuevo arriba, respuestas plegadas bajo su comentario, adjuntos como tarjetas.
- **Tablero kanban** (`kanban()`): tareas por etapas cuando el usuario mueve el trabajo de una columna a otra. Como máximo 4–5 columnas; cada tarjeta con tipo, responsable, fecha y avance; «Añadir tarea» como acción del record type.
- **Bandejas de tareas**: en Appian 26.9, `a!queryTaskList()` consulta las tareas de procesos normales y con autoescalado sin informe de procesos; el grid del prototipo (`data!tareas`) se traduce a esa consulta.
- **Selectores y navegadores**: selector (`a!pickerField*`) cuando el usuario sabe qué busca; navegador en columnas (`a!userBrowserFieldColumns`, `a!documentAndFolderBrowserFieldColumns`…) cuando necesita recorrer una estructura; árbol (`a!hierarchyBrowserFieldTree`) para jerarquías propias de pocos niveles; `a!orgChartField` para la línea jerárquica de una persona.
- **Contenido multimedia**: `a!videoField` para formación o procedimientos; `a!webContentField` para incrustar otra herramienta (26.9: con cámara y micrófono); `a!signatureField` con la firma de 26.8 (línea discontinua).
- **Celdas compuestas** en grids (26.9): `a!sideBySideLayout` para juntar avatar y nombre o estado y fecha en una celda, sin añadir columnas.

## 17. Rúbrica de revisión UX

Aplica la rúbrica en el paso 4 de SKILL.md. Si hay agentes disponibles, que la aplique un agente distinto del que diseñó la pantalla. Puntúa cada criterio como ✅, ⚠️ o ❌ por pantalla, con el motivo.

1. La tarea principal se identifica en 3 segundos y está arriba a la izquierda.
2. Hay un solo H1 y la jerarquía de títulos es coherente (§3).
3. Hay como máximo un botón SOLID, solo la pérdida real de datos va en GHOST rojo, siempre con confirmación, y los botones llevan verbos.
4. Las cards de contenido son blancas y llevan borde o sombra según el fondo; no hay cards con borde anidadas.
5. El color tiene significado: la paleta de estados es común, hay como máximo dos colores no neutros por grid y el acento solo aparece en enlaces.
6. Los grids tienen ≤7 columnas y una acción por celda, ningún texto se parte en más de 2 líneas, las cifras van a la derecha, las celdas vacías llevan «–» y el primer campo enlaza a la ficha.
7. Los filtros están en la barra del grid (≤4) o en una barra de página; no hay una card-formulario de filtros.
8. La ficha tiene una cabecera con ≤3 acciones, una franja de datos clave y un hito; las áreas 1:N van en vistas, no en acordeones.
9. Los datos de la ficha se leen como resumen: etiqueta encima y 2–3 columnas, sin columnas estrechas de valores.
10. Los formularios van en una columna estrecha con etiqueta en cada campo y la selección adecuada (cards, radio con una opción marcada, desplegable, toggle); los diálogos, a FULL.
11. El asistente usa un estilo acorde al número de pasos y tiene un paso de revisión con «Editar».
12. La tarea muestra el plazo destacado, el documento visible y una decisión con color e icono.
13. El inicio muestra los KPI en una franja con tendencia, las tareas sin paginación con «Ver todas» y accesos rápidos.
14. Los gráficos tienen su tabla alternativa, ≤5 colores, un solo esquema, líneas de referencia si hay un objetivo y etiquetas si hay pocas barras; con más de 7 puntos van solos en la fila.
15. Hay estados vacíos diseñados y avisos de acción con el botón dentro.
16. Los textos van en frase con mayúscula inicial, los botones llevan verbos, los formatos de fecha e importe son correctos y los códigos siguen el formato del documento.
17. Hay coherencia entre pantallas: mismos datos, mismos mapas de color, mismas posiciones de acciones.
18. No hay nada que sobre: cada bloque responde a un requisito o a la tarea principal.
19. La accesibilidad está cubierta: `accessibilityText` en iconos, color acompañado de texto o icono y **0 fallos en `contrast_audit.py`** (§4).
20. La pantalla se ve bien a 1440 px y aguanta 1024 px sin columnas de 3 palabras por línea.
21. Si hay IA: el componente responde al origen de la respuesta, está bien colocado, empieza con un estado inicial en español, avisa de la fiabilidad, muestra la fuente y deja la decisión al usuario (§14).
22. La navegación secundaria y las cabeceras siguen §15: pestañas o navegación vertical según el número de secciones, migas solo en jerarquías.
23. El color da vida sin ruido (§4): bloque de color en la cabecera de las páginas de entrada, KPI con sello de icono, estados con su color en etiquetas y gráficos, y nada de color sin significado.
24. Si la pantalla usa un patrón o componente de 26.9 (calendario, comentarios, kanban, navegadores, organigrama), sigue §16 y la versión del cliente lo admite.
25. Todo es del proceso del proyecto: entidades, perfiles, estados, códigos, textos y datos salen de su análisis funcional; no queda nada de una plantilla ni de un ejemplo del kit (nombres, códigos como `EXP-`, estados o roles de otro proceso).

## 18. Doctrina Appian

Si esta guía y appian-best-practices no coinciden, manda appian-best-practices; avisa para corregir la guía.

Reglas de pantalla que se aplican siempre (✔: las comprueba el validador). Detalle y motivo en la sección citada de `appian-best-practices` (`scripts/seccion.py 02 4.9`).

- Un solo botón SOLID; la pérdida real de datos, GHOST + NEGATIVE con confirmación ✔ (BP 02 §4.9).
- En un flujo secuencial, lo que aún no se puede usar se desactiva, no se oculta (BP 02 §4.7).
- Una regla de varios campos se valida en el formulario o la sección, con mensaje (BP 02 §4.1).
- Selección por número de opciones; radio con una opción marcada ✔ (BP 02 §4.8).
- Formulario o asistente en diálogo a FULL ✔, título y botones fijos si hay scroll (BP 02 §4.5, §4.6).
- Grids: cabecera de fila ✔, una acción por celda ✔, 50 filas como máximo ✔ (BP 02 §5.4–5.6).
- Gráficos: tabla alternativa ✔, solos en la fila con más de 7 puntos ✔, ≤5 colores (BP 02 §9.5, §5A.3, §5A.2).
- Todo campo con label ✔; títulos con etiqueta H real y un H1 por pantalla ✔ (BP 02 §9.3, §9.6).
- El color nunca va solo: texto o icono con él (BP 02 §9.2).
- Sin datos, un estado vacío con mensaje (BP 02 §7.3).
- Site: ≤8 páginas de primer nivel ✔; con MERCURY no hay iconos de página (BP 09 §2.1, §3.3).
- El listado de una entidad es una página Record List si basta (BP 09 §1.3).
- Pestañas horizontales hasta 6; con más, verticales ✔ (BP 09 §4.2).
- Lo que solo ve un perfil lleva `$note` con la capa de seguridad que lo aplica: registro, vista, acción de registro, campo o visibilidad de interfaz, que solo oculta (`por_perfil()`; BP 06 §5, BP 09 §7.3).
