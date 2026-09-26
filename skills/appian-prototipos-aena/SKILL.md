---
name: appian-prototipos-aena
description: "Crea prototipos navegables (maquetas, mockups) de aplicaciones Appian con la marca AENA, con componentes SAIL reales, patrones de pantalla repetibles y capturas PNG para el documento funcional. Úsala siempre que se pida un prototipo, maqueta, mockup o propuesta de pantallas navegable, sea cual sea el material de partida (primero obtiene el análisis ddf.md con appian-functional-analyst), o capturas de pantallas del prototipo para el documento funcional. No genera código SAIL (para eso, appian-sail-generator)."
---

# Prototipos Appian · AENA

Convierte un documento de requisitos o de diseño funcional en un **prototipo navegable de la aplicación Appian tal y como quedará construida**:

- **Replicable en Appian**: cada pantalla es un árbol de funciones SAIL reales (`a!cardLayout`, `a!gridField`, `a!wizardLayout`...) con sus parámetros y valores válidos. El validador rechaza cualquier cosa que no exista en SAIL.
- **Marca AENA**: configuración real del objeto Site (colores, logo, formas) y perfil CSS de Appian 26.9 (colores de estado accesibles, campos, tarjetas, tooltips) en `assets/brand-aena.json`.
- **Catálogo completo de Appian 26.9**: los 147 componentes de interfaz (navegadores, organigrama, vídeo, contenido web, firma, chats de IA…) se validan y se pintan con su aspecto real; `examples/componentes/` los enseña todos, agrupados como en la documentación de Appian.
- **Genérica para cualquier proceso**: acuerdos con terceros, medioambiente, servidumbres, informes, expedientes… El kit no sabe de ningún dominio: entidades, roles, estados, códigos, textos, reglas y datos salen siempre del `ddf.md` del proyecto. Las plantillas y los ejemplos enseñan técnica (cómo se resuelve una pantalla), nunca un dominio que copiar (`examples/README.md`).
- **Patrón repetible y UX cuidada**: toda pantalla declara uno de los 12 patrones de `templates/patterns.json` y sigue `references/design-rules.md`, que es la guía de diseño: el SAIL Design System oficial de Appian adaptado a AENA. El validador avisa de lo que la incumple (`UX ·`).
- **Tres usos**: demo en reunión con cliente (navegación, validaciones, diálogos), capturas PNG para el documento funcional y referencia para desarrollo (inspector SAIL + `app.json` + trazabilidad).

## Flujo

### 0. Kit y requisitos
`KIT` = la carpeta de este SKILL.md (la «base directory» que indica la herramienta al cargar la skill): scripts, runtime, schemas, plantillas, marca y ejemplos vienen dentro del plugin. Todos los comandos usan `python3 $KIT/scripts/...` (en Windows, `python`) y las rutas `references/`, `templates/`, `examples/` son relativas a `$KIT`.

**Antes de nada, comprueba que el kit está**: `ls "$KIT/scripts/build.py"`.
- Si no está junto al SKILL.md, búscalo una sola vez fuera de la papelera de plugins: `find / -path "*/appian-prototipos-aena/scripts/build.py" -not -path "*/.trash/*" -not -path "/proc/*" 2>/dev/null` (en Windows, `where /r %USERPROFILE% build.py` y quédate con la ruta que acabe en `appian-prototipos-aena\scripts\build.py`). Si hay varias, usa la que esté junto al SKILL.md que has cargado o, si no, la más reciente.
- Si no aparece, la skill está instalada **sin su kit**: solo el SKILL.md (una skill suelta creada o copiada a mano, o una versión anterior al plugin). **Para** y díselo al usuario en una frase: hay que instalar el plugin completo `appian-analisis-funcional.plugin` y retirar las skills sueltas `appian-prototipos-aena` y `appian-functional-analyst`. No busques el kit en artefactos, enlaces ni internet, ni lo reconstruyas: sin él no se puede validar ni construir un prototipo fiel.

| Para | Necesita | Si falta |
|---|---|---|
| Validar y construir | Python 3.9+ (solo biblioteca estándar) | Imprescindible |
| Prueba de humo y capturas | `pip install playwright` (versión actual) + un navegador: `python -m playwright install chromium`, o Chrome / Edge ya instalados | Valida, construye y revisa el HTML generado |
| Fuente Open Sans | Internet al abrir el prototipo | Se ve con Segoe UI / Arial |

En Claude (web / escritorio) todo está en el entorno. En un equipo nuevo, `python3 $KIT/scripts/selftest.py` dice en unos segundos qué funciona y qué falta.

### 1. Entrada: el análisis funcional (`ddf.md`)
El prototipo parte del `ddf.md` que genera **`appian-functional-analyst`** (en este mismo plugin):

| El usuario da… | Antes del prototipo |
|---|---|
| Un `ddf.md` o un DDF de esa skill | Nada: úsalo |
| Un diseño funcional o una ERS (.pptx, .docx, .pdf) | Analista en **modo fiel**: extracto literal, sin `.docx` |
| Transcripciones, correos, notas, diagramas de flujo | Analista en **modo síntesis**; pide solo el `ddf.md` salvo que el usuario quiera también el DDF en Word |
| Un DF y reuniones o correos posteriores | Analista en modo fiel + actualización |

Carga la skill del analista para ese paso y vuelve aquí con el `ddf.md`. Así el prototipo recibe siempre el mismo formato, con IDs estables y la fuente de cada dato.

Después sigue `references/ingesta-requisitos.md`: correspondencia sección del DDF → spec (§0), patrón de cada pantalla, tipo de dato → componente, y qué hacer con lo que el análisis no define. Los IDs (RF, RB, actividades, pantallas) se conservan literales, las actividades que el análisis marca fuera de la aplicación van a `requirements` con `outOfScope`, y los niveles ⚠️/❓ se convierten en `$assumption`/`openQuestions`.

**Brief de diseño** (antes de escribir el spec, guía §0). Para cada pantalla anota:
- la **tarea principal** del usuario y quién la usa (ocasional o experto);
- el **patrón**;
- los **bloques** que usa, del catálogo `references/bloques.md`: franja de KPI, franja de datos clave, aviso de acción, grid consolidado, grid con detalle, drilldown, selección con cards, cards-botón, comentarios, timeline…;
- qué va **en vistas o diálogos** para no cargar la pantalla.

En las fichas, decide qué áreas 1:N son vistas (máximo 7) y qué datos van en la franja de datos clave. En los listados, decide las ≤7 columnas y qué se consolida.

**Checkpoint**: presenta al usuario en un único mensaje el inventario (`Id · Pantalla · Patrón · Tarea principal · Requisitos`), la navegación y las preguntas abiertas, y espera confirmación. Si pidió ir directo o no está presente, sigue con la lectura más razonable y déjalo en `openQuestions` y `$assumption`.

### 2. Escribir el `app.json`
- **Lee `references/design-rules.md` antes de escribir la primera pantalla**: fondo y cards, jerarquía de títulos, paleta de estados, botones, estructura por patrón, grids y ficha. Formato: `references/spec-format.md`. Componentes y equivalencias: `references/componentes.md`.
- Usuarios, grupos y documentos de ejemplo (`users` con cargo y responsable, `groups`, `documents`) alimentan selectores, navegadores y organigrama (`references/spec-format.md`).
- `app.appianVersion`: la versión de Appian del cliente (por defecto `26.9`, la versión vigente). El validador da error si una pantalla usa un componente, un parámetro o un valor más nuevos (`schemas/appian-versions.json`).
- Parte siempre de la plantilla del patrón (`templates/PNN-*.json`) y sustituye sus textos, campos, estados y datos (un dominio genérico de expedientes) por los del proyecto. Hay 12: P01 listado, P02 vista de registro, P03 formulario, P04 asistente, P05 tarea de aprobación, P06 inicio, P07 diálogo, P08 informe, P09 maestro-detalle, P10 portada de módulo, P11 asistente de IA y P12 revisión de datos sugeridos por IA (`templates/patterns.json` dice cuándo usar cada uno). `templates/catalogo-patrones.json` los reúne en una app construible (galería para enseñar al equipo o al cliente); se regenera con `templates/generar_plantillas.py`. `examples/bloques/` es la galería de bloques (con los patrones de 26.9: calendario, hilo de comentarios y kanban), `examples/ia/` la de componentes de IA y `examples/componentes/` la de los 147 componentes de Appian 26.9 (dónde ver cómo se configura cada uno). `examples/casos/<proceso>/` son recorridos completos, uno por proceso y todos al mismo nivel (documento de entrada → `ddf.md` → `generar_app.py` → `app.json` y prototipo); `examples/README.md` los lista y explica cómo añadir otro.
- Datos de ejemplo realistas del dominio del proyecto (el del `ddf.md`, nunca el de una plantilla o un ejemplo), 10–20 filas en la entidad principal, todos los estados representados, mismos datos en todas las pantallas. Fija `app.today` para que las fechas relativas no cambien entre demos.
- Cada pantalla lleva `req` con los IDs que cubre. Lo que el documento no define va con `$assumption`; las dudas, a `openQuestions`. Las actividades que el documento sitúa fuera de la aplicación (otro sistema, actores externos) van en `requirements` con `outOfScope` y el motivo.
- Define `captures` con los estados que el documento funcional necesita (errores de validación, pasos del asistente, diálogos, vistas de registro).
- Escribe el JSON con un script Python en vez de a mano, importando `scripts/sail_helpers.py` (`sys.path.insert(0, r"<KIT>/scripts")` con la ruta real, en cadena `r"..."` para que funcione con rutas de Windows; `from sail_helpers import *`). Los helpers ya aplican la guía:
  - página: `page_header` (con `crumbs`), `hero_header`, `filter_bar`, `side_nav`, `content_card`, `section_card` (título H2 encima de la card), `subsection`, `action_banner`, `empty_state`, `link_all`, `inline_stats`;
  - datos: `key_facts`, `field_summary`, `kpi` / `kpi_strip`, `kpi_sparkline`, `kpi_progress`, `two_line`, `doc_line`, `milestone`, `duration`, `stamp_steps`, `checklist`, `leaderboard`, `user_list`;
  - listas y grids: `grid`, `gcol`, `gcol_num`, `gcol_link`, `tag` + `state_map` (paleta de estados), `state_chart_colors` (barras con el color de su estado) y `CHART` (colores de series en orden, todos con 3:1 sobre blanco), `alert_icons`, `grid_with_detail`, `grid_with_selection`, `drilldown` + `drill_link`, `chart_link`, `more_less`, `document_list`, `comments`, `dual_picklist`, `dynamic_inputs`;
  - patrones de 26.9: `calendar_month` / `calendar_week` (con `event_maps()` en `maps`), `comment_thread` (con `ATTACH_MAPS`), `kanban`;
  - cards: `cards_as_buttons`, `cards_as_info`, `call_to_action`, `choice_cards`;
  - botones: `primary` (uno por pantalla), `secondary`, `danger` (GHOST rojo con confirmación), `tool_button`, `bl`;
  - formularios: `txt`, `par`, `date`, `dd`, `upload`, `choice_cards`, `cols`, `subsection_with_link` (revisión con «Editar»);
  - IA: `ai_agent_chat`, `ai_side_pane` + `ai_toggle` + `ai_data_chat`, `ai_records_chat`, `ai_doc_chat` + `ai_answer` + `ai_citation`, `ai_review_grid`, `match_quality`, `ai_notice`, `ai_feedback` (con `AI_MAPS` en `maps`);
  - diálogos P07: `dialog`.

  Los `generar_app.py` de `examples/casos/` los usan en casos completos; `references/bloques.md` dice cuándo usar cada bloque.
- **IA solo si el análisis la pide.** Si crees que aporta (resumir, extraer datos de documentos, buscar por significado, preguntar a los datos), propónla con `$assumption` («Propuesta: …») y el beneficio, sin quitar el flujo manual. Reglas en `design-rules.md` §14.

### 3. Validar y construir
```bash
python3 $KIT/scripts/validate.py app.json          # 0 errores obligatorio; revisa los avisos
python3 $KIT/scripts/build.py app.json -o prototipo-<app>.html
```
El validador termina con la línea «Calidad UX: N avisos». Resuelve los avisos `UX ·` (también los de contraste, que traen un color alternativo) y, si alguno está justificado, explica el motivo en un `$uxIgnore`. `build.py` valida de nuevo, genera un único HTML autocontenido (runtime, marca, iconos y logo embebidos; solo carga Open Sans de Google Fonts), `prototipo-<app>-trazabilidad.md` (requisitos ↔ pantallas, preguntas abiertas, supuestos) y `prototipo-<app>-perfil-css.txt` (perfil CSS de AENA para Admin Console › Branding › CSS Profiles; `design-rules.md` §1). Nunca edites el HTML generado: cambia el `app.json` y reconstruye.

### 4. Demostrar que funciona
Si hay Playwright y un navegador (ver paso 0):
```bash
python3 $KIT/scripts/smoke_test.py prototipo-<app>.html app.json      # pulsa todo; falla con errores JS o componentes sin pintar
python3 $KIT/scripts/contrast_audit.py prototipo-<app>.html app.json  # contraste WCAG 2.2 AA de cada texto, campo y gráfico: debe dar 0
python3 $KIT/scripts/capture.py prototipo-<app>.html app.json -o capturas/
```
Revisa **visualmente** las capturas (Read sobre los PNG): textos cortados, columnas desalineadas, pantallas vacías, datos incoherentes. Después pasa la **rúbrica UX** (`references/design-rules.md` §17): 25 criterios, marcados ✅, ⚠️ o ❌ por pantalla. Si puedes lanzar agentes, que la aplique uno que no haya diseñado las pantallas, con las capturas y la guía como única entrada. Corrige lo marcado con ❌. Después recorre los **criterios de aceptación** de cada ficha de pantalla y de tarea del `ddf.md` (`CA-PAN-…`, `CA-ACT-…`) y comprueba en el prototipo los que se pueden ver (validaciones, visibilidad, botones, textos, estados). Corrige el `app.json` y repite. Para flujos críticos (alta con validaciones, decisión de una tarea) haz además una prueba dirigida con Playwright rellenando campos y pulsando botones, usando esos criterios como casos.

Sin Playwright o sin navegador (los scripts salen con código 2 y dicen qué falta): valida, construye y revisa al menos el HTML generado.

### 5. Entregar
- **Claude (web / escritorio)**: envía con SendUserFile el HTML (se abre en cualquier navegador), `app.json`, la trazabilidad y las capturas si se generaron. **Publícalo como artefacto solo si el usuario lo pide**: lleva la marca de AENA y un enlace publicado se puede compartir. Si lo pide, usa la herramienta Artifact (el fichero ya cumple el contrato de página: empieza por `<title>`, recursos embebidos, tema claro deliberado como un Site de Appian; `icon: "layout"`) y, en iteraciones, reconstruye y republica **en la misma ruta** para mantener el enlace.
- **Claude Code**: deja todo en `prototipos/<app>/` (`app.json`, HTML, trazabilidad, `capturas/` con `indice.md`) y di cómo abrirlo.
- **Vuelta al documento funcional**: `capturas/indice.md` da, para cada PNG, su pie de figura y su ficha («Referencia», que sale del `ref` de la pantalla).
  - Análisis propio (modo síntesis): añade cada captura a la fila «Capturas» de su ficha en la Sec 12 del `ddf.md` (`![pie](capturas/NN-x.png)`) y las preguntas abiertas nuevas a su Sec 17 con prioridad 🔴🟡🟢. Si el usuario quiere el Word actualizado, se regenera desde el `ddf.md` con `appian-functional-analyst`: así las capturas no se pierden en la siguiente versión.
  - Extracto de un DF del cliente (modo fiel): entrega las capturas con su índice para pegarlas en el documento del cliente.
- Resume en pocas líneas: pantallas, cobertura de requisitos, preguntas abiertas pendientes.

## Uso del prototipo (explícalo al entregar la primera vez)
- **Reunión**: navegación por las páginas del site, filtros, búsqueda, fichas, asistentes con validación, diálogos. Barra inferior: **Pantallas** (índice para saltar a cualquier pantalla o diálogo) y **Requisitos** (cobertura, preguntas abiertas, supuestos).
- **Documento funcional**: `capturas/*.png` + `capturas/indice.md` (pie de figura listo para pegar, referencia a la ficha del documento, patrón y requisitos). En capturas la barra del prototipo no aparece.
- **Desarrollo**: **Inspector** (tecla `I`) muestra el componente SAIL y sus parámetros al pasar el ratón y al hacer clic; los supuestos aparecen con borde naranja.

## Documentación oficial de Appian (opcional)
El plugin incluye el **MCP público de documentación de Appian** (`appian-docs`, herramienta `search_appian_docs_public_knowledge_sources`). La primera vez pide iniciar sesión con Google o GitHub y tiene un límite de 300 consultas al día por persona. Úsalo cuando haya dudas de Appian:
- si un componente, parámetro o valor existe en la versión del cliente (`app.appianVersion`);
- qué admite de verdad un Site, un record type o una acción de registro antes de prometerlo en una pantalla;
- el contenido de los `$note` para desarrollo.

Si el validador rechaza algo que la documentación confirma para esa versión, créalo en un `prototype-extensions.json` **junto al `app.json`** (mismo formato que `schemas/prototype-extensions.json`: los parámetros y valores se fusionan con los del componente) con la URL en `source`. validate y build lo leen automáticamente. No edites la carpeta del plugin: puede ser de solo lectura y se sobrescribe al actualizar. Díselo al usuario para que se incorpore al plugin. Sin el MCP (no conectado o sin consultas), consulta docs.appian.com con WebFetch/WebSearch; si tampoco es posible, quédate con los schemas y anota la duda en `openQuestions` o en un `$note`. La documentación complementa al validador, no lo sustituye.

## Reglas que no se negocian
- Solo funciones y parámetros SAIL reales; lo exclusivo del prototipo empieza por `$`. Nada de CSS, HTML ni componentes inventados.
- La guía de diseño manda: un solo botón SOLID por pantalla, cards blancas con sombra sobre fondo gris, títulos de sección encima de la card, ≤7 columnas por grid, áreas 1:N en vistas (no en secciones plegables) y la paleta de estados común.
- Un patrón por pantalla; si ninguno encaja, usa el más cercano y avisa al usuario en vez de crear un layout nuevo.
- No inventar requisitos, campos ni estados. Supuestos siempre visibles (`$assumption`).
- Personas y datos ficticios; nunca datos personales reales.
- Un artefacto publicado es privado hasta que el usuario lo comparte; si el prototipo muestra información sensible del cliente, avísale antes de que lo comparta fuera del proyecto.

## Errores frecuentes
- `a!cardLayout(style: "STANDARD")` es **gris** en Appian: las cards de contenido van con `style: "NONE"` (blanco, el valor por defecto), o usa `content_card()`.
- Las secciones son de color de acento por defecto: los títulos de sección llevan `labelColor: "STANDARD"` (H2) o `"SECONDARY"` (subsecciones).
- Un tag muestra como máximo 40 caracteres: si el estado es más largo, Appian lo recorta.
- Un valor vacío se muestra como «–»: añade `|dash` a la expresión (`{rv!record.importe|eur|dash}`); los helpers `field_summary` y `key_facts` ya lo hacen.
- Anidaciones que Appian no admite (el validador las detecta): botones fuera de `a!buttonArrayLayout`/`a!buttonLayout`, `a!formLayout` o `a!headerContentLayout` anidados, cards o grids dentro de `a!sideBySideItem`, campos editables o layouts en columnas de `a!gridField`, `a!tabLayout` dentro de side-by-side o grids.
- Valores de enumerado mal escritos (`"PRIMARY"`, `"END"` en celdas de `a!gridLayoutHeaderCell`, que usa LEFT/CENTER/RIGHT): el validador indica los permitidos.
- `showWhen`, `required` y `disabled` en texto son expresiones SAIL (`"local!x = \"A\""`); el texto a mostrar usa interpolación (`"Vence el {rv!record.fechaFin|date}"`).
- Enlaces a variables anidadas: `"value": "local!exp.titulo"` con el mismo `saveInto`.
- Diálogos en `captures`: indica `hostParams` para abrirlos sobre el registro correcto.
- Precarga de formularios de edición: `local` con `"{rv!record.campo}"`, no `value` apuntando al registro.
- Restar fechas: `todate(b) - todate(a)`; sin `todate()` las fechas son texto y la resta no funciona.
- Las acciones no modifican los datos de ejemplo: enseña el resultado con un banner (`params` → `ri!`) o una captura con `state`.
- `a!styledTextEditorField` guarda HTML: el valor inicial va en párrafos `<p>…</p>`, no con saltos de línea.
- Grids con muchas columnas: el ancho declarado de cada columna se respeta y, si no caben, la tabla se desplaza en horizontal (como en Appian) y la captura corta las últimas. Deja sin `width` las columnas cortas y usa `spacing: "DENSE"`.
- Secciones plegables que deben salir abiertas en una captura: `isInitiallyCollapsed: "ri!abrir <> \"id\""` y `params: {"abrir": "id"}` en la captura.

## Otra marca
La marca es un fichero: `brand-<id>.json` + su logo. `--brand <id>` en validate/build busca primero junto al `app.json` (marcas de un proyecto) y después en `assets/` del kit (AENA, el valor por defecto). Para una marca nueva, copia `assets/brand-aena.json` y los logos junto al `app.json` y adáptalos; no edites la carpeta del plugin.
