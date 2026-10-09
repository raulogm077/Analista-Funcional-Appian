# Del análisis funcional al inventario de pantallas

La entrada es `<p>/analisis/funcional.md`, que escribe `appian-functional-analyst` (SKILL.md, paso 1).
Su formato está en `references/funcional-plantilla.md` de esa skill. Si existe `analisis/tecnico.md`,
se usan además su §0, §3 y §4. Esta fase produce el **inventario de pantallas**, que se confirma antes de
escribir el `app.json`. Las fuentes ya las ha leído el analista: aquí no se reinterpreta lo que dijo el
cliente, se traduce el funcional a pantallas.

## 0. Apartado del funcional → spec

| Apartado | Va a |
|---|---|
| Cabecera (`Versión: 1.2 · Estado: …`) | `app.source` («analisis/funcional.md v1.2») |
| §1 Objetivo y alcance | Qué entra en el prototipo; lo que queda fuera no se prototipa. Los términos, tal cual, en los textos de pantalla |
| §2 Perfiles | Un grupo de ejemplo por perfil en `groups` y personas ficticias en `users`. `site.user`: una persona del perfil protagonista de la demo, el que más pasos tiene en §3 salvo que el usuario diga otro |
| §3 Pasos `ACT-nn` | Todos a `requirements` con su ID y título. Según su «Pantalla»: `PAN-nn` → esa pantalla lleva el paso en `req` (§0.2); «Fuera de la aplicación» → `outOfScope` con quién lo hace; «—» (lo hace la aplicación) → `noScreen`; sin decidir → `noScreen` con su PC |
| §3 Estados | `maps.estadoColor` con la paleta (`state_map`), `maps.estadoPaso` y el hito (`milestone`). Todos los estados, presentes en los datos de ejemplo |
| §3 Escenarios `ESC-nn` | Recorridos de la prueba dirigida (SKILL.md, paso 4) y guion de la demo. Sus casos concretos, como filas de los datos de ejemplo |
| §4 Historias `HU-nn` | `requirements` con el ID y el título **literales**; `req` de la pantalla que dice su «Pantalla». Con «—», `noScreen` y el motivo |
| §4 Criterios `HU-nn.m` | No van al spec: son la lista de comprobación del paso 4 |
| §4 Reglas `RB-nn` | `$validations` con el mensaje literal del criterio, `required` y `showWhen` condicionales. Una regla que no se ve en pantalla, en un `$note` |
| §5 Pantallas `PAN-nn` | Una pantalla o diálogo por ficha (§0.1) |
| §6 Información | `data` (§0.3) y lo que muestra cada pantalla («Dónde se ve») |
| §7 Avisos `AV-nn` | Lo que se ve: la tarea en la bandeja, un banner tras enviar. El correo, en un `$note` del botón que lo dispara |
| §8 Documentos `DOC-nn` | Lo que se sube → `a!fileUploadField` con formato y tamaño en `instructions`. Lo que genera la aplicación → enlace o visor en la ficha, con `$note`. La descarga de una lista → `showExportButton` |
| §9 Otros sistemas `INT-nn` | Los datos que llegan de fuera, en solo lectura y con `$note`. La integración no se pinta |
| §10 Condiciones de uso | Móvil (`stackWhen`), idiomas, accesibilidad |
| §11 `PC-nn` abiertos | `openQuestions`: `id` el PC, `text` la pregunta y sus opciones, `screen` la pantalla que corresponde a «Afecta a». Los tachados no van |
| Técnico §0 | `app.appianVersion` (`spec-format.md`) |
| Técnico §3 y §4 | Nombres de record types y campos (§0.3) y capa de seguridad de cada parte (§0.1) |

### 0.1 Ficha `PAN-nn` → pantalla

| En la ficha | En la spec |
|---|---|
| `**PAN-04 — Revisar documentación**` | `ref: "PAN-04 · Revisar documentación"`, literal. Enlaza cada captura con su ficha. `title`, el que verá el usuario |
| Para qué sirve, quién entra, desde dónde se abre | `type` y patrón (§1). Página del site (`site.pages`), botón con `$action`, `recordActions` o tarea |
| Cada fila de «Parte» | Una sección, bloque, paso o vista, en el orden de la tabla. En una ficha de registro, cada parte 1:N con volumen propio (documentos, comunicaciones, historial) es una **vista** (máximo 7; las pequeñas se agrupan), nunca una pila de secciones plegables (guía §8) |
| «Qué permite» | Los campos y acciones de esa parte |
| «Quién»: Todos | Sin restricción |
| «Quién»: uno o varios perfiles | `por_perfil(nodo, perfil, capa)`: `$note` con el perfil y la capa de seguridad que lo aplica. La capa, de técnico §4; sin técnico, la que corresponde según la guía §18 (registro, campo, vista, acción o interfaz). `showWhen` solo si la demo debe enseñarlo oculto |
| `Historias: HU-04, HU-05.` | `req`, más el `ACT-nn` si es la pantalla de un paso |
| La captura | La pone el prototipo (SKILL.md, paso 5) |

La ficha no dice cómo se compone la pantalla. Eso sale de las historias y de §6:

| De | En la spec |
|---|---|
| §6 «Dónde se ve» | Qué datos lleva cada pantalla. «No se muestra» → solo en `data` |
| §6 «Formato» | Componente (§2), `characterLimit`, filtro de presentación (`date`, `eur`) |
| §6 «Obligatorio» | «Sí» → `required`; condicional («Si es desfavorable») → `required` con su expresión; «Automático» → `readOnly`, o fuera del alta |
| Descripción y criterios de la historia | Columnas, filtros y orden de los listados. Acciones con su texto literal: quién la ve → `showWhen`, cuándo está activa → `disabled`, qué pasa después → `$action`, confirmación → `confirmHeader` / `confirmMessage` literales. Los textos entre comillas → `instructions`, `helpTooltip`, mensajes de `$validations` y banners, sin reescribirlos |

- **Listados con más de 7 columnas**: consolida en celdas de dos líneas (`two_line`: código + título,
  tipología + sede, paso + fase) sin perder ningún dato. Si aun así sobran, propón llevarlas a la
  ficha con un `$assumption` y una pregunta abierta; no las quites sin decirlo.
- **Filtros**: hasta 4 `userFilters` en la barra del grid, más el buscador. Los filtros predefinidos de uso
  diario («mis informes», «con alertas») → vistas guardadas con `a!tabLayout` y el recuento en la
  etiqueta. Los de página que afectan a varios bloques (informes) → barra de filtros en una card. Nunca una
  card-formulario de 8 desplegables encima del grid. Valor por defecto → `local` inicial.
- **Ordenación**: `initialSorts` del `a!gridField` y `sortField` en las columnas ordenables.

### 0.2 Paso `ACT-nn` con pantalla → tarea

El `PAN-nn` de un paso es la pantalla donde su perfil lo hace. Si el paso llega como tarea (la ficha dice
«Tarea de…» o técnico §7 dice formulario de tarea), es un P05 si decide algo y un P03 si solo recoge
datos. El paso y su ficha describen la misma pantalla: una sola en el spec.

| En el paso | En la spec |
|---|---|
| «Quién» y «Empieza cuando» | Tarea en la bandeja del perfil; enseña el registro en el estado en que llega |
| Cada opción («- Aprobar: …») | `a!cardChoiceField` con `a!cardTemplateBarTextStacked` en la card «Decisión» (P05, helper `choice_cards`): texto literal, estado de salida como texto secundario e icono de color (aprobar POSITIVE, devolver naranja, rechazar NEGATIVE). «Enviar decisión» la envía |
| Condición de una opción | `required` condicional o `$validations` (comentario obligatorio al devolver) |
| Adónde lleva | `$action`: vuelta a la bandeja o al registro con un banner («El expediente ha pasado a «Aprobado»») |
| «Plazo» | Banner de vencimiento arriba de la tarea |

### 0.3 §6 → `data`

- Un dataset por entidad (`### 6.n`, salvo «Listas de valores»). Con técnico §3, el `recordType` y los campos con sus nombres reales
  (columna «Campo»; el dato del funcional está en «Uso»). Sin técnico, `recordType` con el prefijo del
  proyecto y la entidad (`EXP Expediente`), y cada campo con el nombre del dato en camelCase español
  («Fecha de inicio» → `fechaInicio`). Son provisionales: los fija la especificación técnica.
- La relación que dice la frase final de cada entidad → campo `<entidad>Id` en la hija.
- Listas de valores → opciones de desplegables, radios o cards, y valores de los datos.
- Lo que el prototipo no sabe calcular (días hasta el vencimiento), precalculado en los datos
  (`spec-format.md`).

### 0.4 Estado de cada pieza

El comentario de trazabilidad de cada ficha o fila (`<!-- ✅ FU-03 00:14:32 -->`) dice cómo se prototipa:

- 🔒 ✅ 🔶 → sin marca.
- ⚠️ → se prototipa y lleva un `$assumption` que cita su PC («Pendiente: PC-04»), para que el cliente lo
  vea en la reunión.
- ❓ → no se inventa: hueco mínimo con `$assumption`. Su PC ya está en `openQuestions`.
- «(pendiente: PC-04)» dentro de una frase → lo mismo, solo para esa parte.
- Tachado (`**~~HU-11~~ — …** Anulada por D-02`) → no se construye. Un criterio tachado no se comprueba.

## 1. Asignar patrón a cada pantalla

| La ficha o la historia dice… | Patrón |
|---|---|
| consultar, listar, buscar, filtrar, exportar X | P01 Listado |
| ficha, detalle, consultar un X, ver el expediente | P02 Vista de registro |
| alta / solicitud / registro con ≤ 8 campos o un solo bloque | P03 Formulario |
| alta con varios bloques, > 8 campos, documentación o pasos | P04 Asistente |
| aprobar, validar, revisar, dar el visto bueno, resolver (por un perfil) | P05 Tarea |
| tarea que solo recoge datos (cargar un documento, completar datos del registro) | P03 Formulario, con el contexto del registro arriba o en `a!sidebarTemplate` |
| inicio: tareas pendientes, avisos, indicadores y accesos del usuario | P06 Inicio |
| editar, modificar, cambiar estado, adjuntar sobre un X existente | P07 Diálogo (acción de registro) |
| informe, estadísticas, gráficos, evolución; cuadro de mando con filtros que actualizan indicadores y gráficos | P08 Informe |
| bandeja, cola de revisión, revisar uno tras otro, triaje, clasificar pendientes | P09 Maestro-detalle |
| portada o entrada de un módulo con varias opciones («desde aquí el usuario puede…») | P10 Portada de módulo |
| asistente virtual, chatbot, preguntar a los datos o a un documento, resumen o borrador generado con IA | P11 Asistente de IA |
| extracción automática de documentos (OCR, IDP), clasificación o datos propuestos por IA que alguien confirma | P12 Revisión de datos sugeridos por IA |

Si el funcional dice expresamente cómo es la pantalla («en un único formulario», «por pasos»), eso manda sobre los umbrales de la tabla. El patrón se elige por el contenido, no por el nombre (un «cuadro de mando» sin tareas ni accesos es un P08).

**IA**: P11 y P12 solo cuando el funcional la pide. Si no la pide pero hay un caso claro (documentos que alguien teclea a mano, búsquedas por texto libre en muchos registros, informes que se redactan copiando datos), propónla como pantalla o bloque marcado con `$assumption` («Propuesta: …» y el beneficio) y como pregunta abierta; el flujo manual sigue existiendo. El chat de datos va en un panel lateral del listado (P01 con `ai_side_pane`); el chat de un registro, en su vista resumen (P02 con `ai_records_chat`); la búsqueda por significado, en el propio grid (`smartSearchType` + `match_quality`).

Una necesidad, una pantalla. Si dos historias caben en la misma (listado + exportar), comparten pantalla y las dos van en `req`.

## 2. Formato del dato → componente SAIL

| Formato en §6 | Editable | Solo lectura |
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
| Persona / grupo | `a!pickerFieldUsers` / `a!pickerFieldGroups`; si hay que recorrer la estructura para encontrarlo, `a!userBrowserFieldColumns` / `a!groupBrowserFieldColumns` | nombre + `a!imageField` AVATAR; línea jerárquica → `a!orgChartField` |
| Documento o carpeta ya existente en Appian | `a!pickerFieldDocuments` / `a!pickerFieldFolders` / `a!pickerFieldDocumentsAndFolders`; explorar una biblioteca → `a!documentAndFolderBrowserFieldColumns` | `a!documentDownloadLink` / `a!documentViewerField` |
| Jerarquía propia (sede → edificio → zona, organigrama de unidades) | `a!hierarchyBrowserFieldColumns` (selección) | `a!hierarchyBrowserFieldTree` |
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

- No añadir campos, estados, perfiles ni pantallas que el funcional no tenga.
- Si una pantalla necesita algo que el funcional no define (qué ve el usuario tras enviar, el orden de la
  lista), elegir lo mínimo razonable y marcarlo con `$assumption` en el componente o en `assumptions` de la
  pantalla.
- Si el prototipo necesita referenciar algo que el funcional no numera (un diálogo sin ficha PAN), no se
  inventa el ID: el analista añade la ficha con el siguiente libre (`indice.py siguientes`).
- Contradicciones y huecos nuevos → `openQuestions` con un ID provisional `Q-nn` y la pantalla afectada.
  Vuelven al analista, que los convierte en PC (SKILL.md, paso 5).

## 4. Checkpoint con el usuario

Antes de escribir el `app.json`, presentar en un solo mensaje:

1. Inventario: tabla `Id · Pantalla · Patrón · Tarea principal · Historias` (el brief de diseño de SKILL.md, paso 1).
2. Navegación: páginas del site y desde dónde se abre cada pantalla.
3. Preguntas abiertas y supuestos.

Si el usuario pidió explícitamente ir directo, o no está presente, seguir con la lectura más razonable y dejarlo reflejado en `openQuestions`/`$assumption`.
