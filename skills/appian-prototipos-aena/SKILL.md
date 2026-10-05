---
name: appian-prototipos-aena
description: "Crea prototipos navegables (maquetas, mockups) de aplicaciones Appian con la marca AENA, con componentes SAIL reales, patrones de pantalla repetibles y capturas PNG que se enlazan en el diseño funcional. Úsala siempre que se pida un prototipo, maqueta, mockup o propuesta de pantallas navegable, sea cual sea el material de partida (primero obtiene el análisis funcional del proyecto, analisis/funcional.md, con appian-functional-analyst), o capturas de las pantallas para el DF. No redacta requisitos, no decide el modelo de datos ni la seguridad y no construye en Appian: parte del funcional y, si existe, de la especificación técnica. Para código SAIL suelto, appian-sail-generator."
---

# Prototipos Appian · AENA

Convierte el análisis funcional de un proyecto en un **prototipo navegable de la aplicación Appian tal y como quedará construida**:

- **Replicable en Appian**: cada pantalla es un árbol de funciones SAIL reales (`a!cardLayout`, `a!gridField`, `a!wizardLayout`...) con sus parámetros y valores válidos. El validador rechaza cualquier cosa que no exista en SAIL.
- **Marca AENA**: configuración real del objeto Site (colores, logo, formas) y perfil CSS de Appian 26.9 (colores de estado accesibles, campos, tarjetas, tooltips) en `assets/brand-aena.json`.
- **Catálogo completo de Appian 26.9**: los 147 componentes de interfaz (navegadores, organigrama, vídeo, contenido web, firma, chats de IA…) se validan y se pintan con su aspecto real; `examples/componentes/` los enseña todos, agrupados como en la documentación de Appian.
- **Genérica para cualquier proceso**: acuerdos con terceros, medioambiente, servidumbres, informes, expedientes… El kit no sabe de ningún dominio: entidades, perfiles, estados, códigos, textos, reglas y datos salen siempre del análisis funcional del proyecto. Las plantillas y los ejemplos enseñan técnica (cómo se resuelve una pantalla), nunca un dominio que copiar (`examples/README.md`).
- **Patrón repetible y UX cuidada**: toda pantalla declara uno de los 12 patrones de `templates/patterns.json` y sigue `references/design-rules.md`, que es la guía de diseño: el SAIL Design System oficial de Appian adaptado a AENA. El validador avisa de lo que la incumple (`UX ·`).
- **Tres usos**: demo en reunión con cliente (navegación, validaciones, diálogos), capturas PNG para el documento funcional y referencia para desarrollo (inspector SAIL + `app.json` + trazabilidad).

**Qué no hace:**
- No redacta requisitos. Lo que el análisis no dice va a `openQuestions` o a un `$assumption`, y el analista lo pregunta.
- No decide el modelo de datos ni la seguridad. Marca qué ve cada perfil y la especificación técnica dice cómo lo aplica Appian.
- No construye en Appian. El `app.json` es la referencia de pantalla para quien construye.

## Flujo

### 0. Kit y requisitos
`KIT` = la carpeta de este SKILL.md: scripts, runtime, schemas, plantillas, marca y ejemplos vienen dentro del plugin. Todos los comandos usan `python3 $KIT/scripts/...` (en Windows, `python`) y las rutas `references/`, `templates/`, `examples/` son relativas a `$KIT`.

| Para | Necesita | Si falta |
|---|---|---|
| Validar y construir | Python 3.9+ (solo biblioteca estándar) | Imprescindible |
| Prueba de humo y capturas | `pip install playwright` (versión actual) + un navegador: `python -m playwright install chromium`, o Chrome / Edge ya instalados | Valida, construye y revisa el HTML generado |

En Claude (web / escritorio) todo está en el entorno. En un equipo nuevo, `python3 $KIT/scripts/selftest.py` dice qué funciona y qué falta (valida y construye en segundos; la prueba de humo y el contraste de los ejemplos tardan un par de minutos).

### 1. Entrada: el análisis funcional (`analisis/funcional.md`)
El prototipo parte de `<p>/analisis/funcional.md`, el diseño funcional que escribe **`appian-functional-analyst`** (en este mismo plugin); `<p>` es la carpeta del proyecto. Si hay `analisis/tecnico.md`, se usa también: versión de Appian, record types y campos, y capa de seguridad de cada perfil. Si el proyecto ya existe, empieza por `python3 $KIT/../appian-functional-analyst/scripts/proyecto.py estado <p>`: versión, pantallas sin captura y pantallas confirmadas.

| El usuario da… | Antes del prototipo |
|---|---|
| Un proyecto con `analisis/funcional.md` | Nada: úsalo |
| Un DF o una ERS del cliente (.pptx, .docx, .pdf) | Analista en **modo fiel** |
| Transcripciones, correos, notas, diagramas de flujo | Analista en **modo síntesis**, sin el Word salvo que el usuario lo pida |
| Una aplicación existente que hay que cambiar | Analista en **modo evolutivo** |
| Un funcional y reuniones, correos o comentarios posteriores | Analista en **modo actualización** |
| Una pantalla que alguien explica, con o sin captura | Analista en **modo pantalla suelta**: su ficha PAN y sus historias |

Carga la skill del analista para ese paso y vuelve aquí con el funcional. Así el prototipo recibe siempre el mismo formato, con IDs estables y la fuente de cada dato.

Tras una actualización, el analista dice qué pantallas cambian: la línea «Pantallas afectadas (prototipo)» de `indice.py impacto`. Se rehacen y se vuelven a capturar solo esas.

Después sigue `references/ingesta-requisitos.md`: qué apartado del funcional va a qué parte del spec, el patrón de cada pantalla, el componente de cada tipo de dato y qué hacer con lo que el funcional no define.

**Brief de diseño** (antes de escribir el spec, guía §0). Para cada pantalla anota:
- la **tarea principal** del usuario y quién la usa (ocasional o experto);
- el **patrón**;
- los **bloques** que usa, del catálogo `references/bloques.md`: franja de KPI, franja de datos clave, aviso de acción, grid consolidado, grid con detalle, drilldown, selección con cards, cards-botón, comentarios, timeline…;
- qué va **en vistas o diálogos** para no cargar la pantalla.

En las fichas, decide qué áreas 1:N son vistas (máximo 7) y qué datos van en la franja de datos clave. En los listados, decide las ≤7 columnas y qué se consolida.

**Checkpoint**: presenta al usuario en un único mensaje el inventario (`Id · Pantalla · Patrón · Tarea principal · Historias`), la navegación y las preguntas abiertas, y espera confirmación. Si pidió ir directo o no está presente, sigue con la lectura más razonable y déjalo en `openQuestions` y `$assumption`.

### 2. Escribir el `app.json`
- **Lee `references/design-rules.md` antes de escribir la primera pantalla**: fondo y cards, jerarquía de títulos, paleta de estados, botones, estructura por patrón, grids y ficha. Formato: `references/spec-format.md`. Componentes y equivalencias: `references/componentes.md`.
- Usuarios, grupos y documentos de ejemplo (`users` con cargo y responsable, `groups`, `documents`) alimentan selectores, navegadores y organigrama (`references/spec-format.md`).
- `app.appianVersion`: la versión de Appian del entorno, del apartado «0. Entorno» de `analisis/tecnico.md` del proyecto. Si no existe, `26.9` con un `"$assumption"` en `app` y una pregunta abierta para confirmarla. El validador da error si una pantalla usa un componente, un parámetro o un valor más nuevos (`schemas/appian-versions.json`).
- Parte siempre del patrón de la pantalla: `templates/PNN-*.json` enseña el resultado y `templates/generar_plantillas.py`, el código con los helpers que lo produce. Copia de ahí la pantalla de ese patrón y sustituye sus textos, campos, estados y datos (un dominio genérico de expedientes) por los del proyecto. Hay 12: P01 listado, P02 vista de registro, P03 formulario, P04 asistente, P05 tarea de aprobación, P06 inicio, P07 diálogo, P08 informe, P09 maestro-detalle, P10 portada de módulo, P11 asistente de IA y P12 revisión de datos sugeridos por IA (`templates/patterns.json` dice cuándo usar cada uno). `templates/catalogo-patrones.json` los reúne en una app construible (galería para enseñar al equipo o al cliente); se regenera con `templates/generar_plantillas.py`. `examples/bloques/` es la galería de bloques (con los patrones de 26.9: calendario, hilo de comentarios y kanban), `examples/ia/` la de componentes de IA y `examples/componentes/` la de los 147 componentes de Appian 26.9 (dónde ver cómo se configura cada uno). `examples/casos/<proceso>/` son proyectos completos, uno por proceso y todos al mismo nivel (fuente → `analisis/funcional.md` → `prototipo/` con su `generar_app.py`, el prototipo y las capturas enlazadas en el funcional); `examples/README.md` los lista y explica cómo añadir otro.
- Datos de ejemplo realistas del dominio del proyecto (el del funcional, nunca el de una plantilla o un ejemplo), 10–20 filas en la entidad principal, todos los estados representados, los casos de los escenarios y los mismos datos en todas las pantallas. Fija `app.today` para que las fechas relativas no cambien entre demos.
- Cada pantalla lleva en `ref` su ficha PAN y en `req` las historias y el paso que cubre. Lo que el funcional no define va con `$assumption`; las dudas, a `openQuestions`.
- Define `captures` con los estados que el documento funcional necesita (errores de validación, pasos del asistente, diálogos, vistas de registro).
- Escribe el JSON con un script Python en `<p>/prototipo/`, no a mano, importando `scripts/sail_helpers.py` (`sys.path.insert(0, r"<KIT>/scripts")` con la ruta real, en cadena `r"..."` para que funcione con rutas de Windows; `from sail_helpers import *`). Los helpers ya aplican la guía:
  - página: `page_header` (con `crumbs`), `hero_header`, `filter_bar`, `side_nav`, `content_card`, `section_card` (título H2 encima de la card), `subsection`, `action_banner`, `empty_state`, `link_all`, `inline_stats`;
  - datos: `key_facts`, `field_summary`, `kpi` / `kpi_strip`, `kpi_sparkline`, `kpi_progress`, `two_line`, `doc_line`, `milestone`, `duration`, `stamp_steps`, `checklist`, `leaderboard`, `user_list`;
  - listas y grids: `grid`, `gcol`, `gcol_num`, `gcol_link`, `tag` + `state_map` (paleta de estados), `state_chart_colors` (barras con el color de su estado) y `CHART` (colores de series en orden, todos con 3:1 sobre blanco), `alert_icons`, `grid_with_detail`, `grid_with_selection`, `drilldown` + `drill_link`, `chart_link`, `chart_table` (gráfico ↔ tabla, obligatorio en todo gráfico), `more_less`, `document_list`, `comments`, `dual_picklist`, `dynamic_inputs`;
  - patrones de 26.9: `calendar_month` / `calendar_week` (con `event_maps()` en `maps`), `comment_thread` (con `ATTACH_MAPS`), `kanban`;
  - cards: `cards_as_buttons`, `cards_as_info`, `call_to_action`, `choice_cards`;
  - botones: `primary` (uno por pantalla), `secondary`, `danger` (GHOST rojo con confirmación obligatoria, solo para pérdida real de datos), `tool_button`, `bl`;
  - formularios: `txt`, `par`, `date`, `dd`, `upload`, `choice_cards`, `cols`, `subsection_with_link` (revisión con «Editar»);
  - IA: `ai_agent_chat`, `ai_side_pane` + `ai_toggle` + `ai_data_chat`, `ai_records_chat`, `ai_doc_chat` + `ai_answer` + `ai_citation`, `ai_review_grid` + `ai_review_validation`, `match_quality`, `ai_notice`, `ai_feedback` (con `AI_MAPS` en `maps`);
  - diálogos P07: `dialog` (formulario a FULL; el ancho del cuadro, en `$dialogWidth`);
  - visibilidad por perfil: `por_perfil` (`$note` con la capa de seguridad de Appian que lo aplica).

  Los `generar_app.py` de `examples/casos/` los usan en casos completos; `references/bloques.md` dice cuándo usar cada bloque.
- **IA solo si el análisis la pide.** Si crees que aporta (resumir, extraer datos de documentos, buscar por significado, preguntar a los datos), propónla con `$assumption` («Propuesta: …») y el beneficio, sin quitar el flujo manual. Reglas en `design-rules.md` §14.

### 3. Validar y construir
```bash
python3 $KIT/scripts/validate.py app.json          # 0 errores obligatorio; revisa los avisos
python3 $KIT/scripts/build.py app.json -o prototipo-<app>.html
```
El validador termina con la línea «Calidad UX: N avisos». Resuelve los avisos `UX ·` (también los de contraste, que traen un color alternativo) y, si alguno está justificado, explica el motivo en un `$uxIgnore`. Las pantallas confirmadas por el cliente se listan en `proyecto.md` del proyecto (`proyecto.py estado <p>` las imprime con el `--confirmadas` listo) y no se cambian sin el visto bueno del analista: antes de cambiar el prototipo se guarda una copia `app-vX.Y.json` y se valida con `--anterior app-vX.Y.json --confirmadas PAN-02,PAN-05` (error si cambia una de esas pantallas o un diálogo que abre). `build.py` valida de nuevo, genera un único HTML autocontenido (runtime, marca, fuente Open Sans, iconos y logo embebidos: se abre sin internet), `prototipo-<app>-trazabilidad.md` (requisitos ↔ pantallas, preguntas abiertas, supuestos) y `prototipo-<app>-perfil-css.txt` (perfil CSS de AENA para Admin Console › Branding › CSS Profiles; `design-rules.md` §1). Nunca edites el HTML generado: cambia el `app.json` y reconstruye.

### 4. Demostrar que funciona
Si hay Playwright y un navegador (ver paso 0):
```bash
python3 $KIT/scripts/smoke_test.py prototipo-<app>.html app.json      # pulsa todo; falla con errores JS o componentes sin pintar
python3 $KIT/scripts/contrast_audit.py prototipo-<app>.html app.json  # contraste WCAG 2.2 AA de cada texto, campo y gráfico: debe dar 0
python3 $KIT/scripts/capture.py prototipo-<app>.html app.json -o capturas/
```
Revisa **visualmente** las capturas (Read sobre los PNG): textos cortados, columnas desalineadas, pantallas vacías, datos incoherentes. Después pasa la **rúbrica UX** (`references/design-rules.md` §17): 25 criterios, marcados ✅, ⚠️ o ❌ por pantalla. Si puedes lanzar agentes, que la aplique uno que no haya diseñado las pantallas, con las capturas y la guía como única entrada. Corrige lo marcado con ❌. Después recorre los **criterios de aceptación** (`HU-nn.m`) de las historias de cada pantalla y comprueba en el prototipo los que se pueden ver (validaciones, visibilidad, botones, textos, estados); los que dependen de algo que el prototipo no hace (avisos, plazos, integraciones) quedan en un `$note`. Corrige el `app.json` y repite. Para flujos críticos (alta con validaciones, decisión de una tarea) haz además una prueba dirigida con Playwright rellenando campos y pulsando botones: los escenarios `ESC-nn` del funcional son los recorridos y los criterios, lo que se comprueba. El prototipo expone `window.PROTO` (espera a `PROTO.ready`): `PROTO.show("pantalla", {params: {id: 4}, view: "documentos", step: 1, state: {"local!x": …}, showValidation: true})` abre una pantalla en ese estado; después, pulsa y escribe con Playwright sobre lo visible (`page.get_by_role("button", name="Enviar")`, `page.get_by_label("Título")`). `scripts/capture.py` es un ejemplo completo.

Sin Playwright o sin navegador (los scripts salen con código 2 y dicen qué falta): valida, construye y revisa al menos el HTML generado.

### 5. Entregar
- Todo queda en `<p>/prototipo/`: el script que escribe el spec, `app.json`, el HTML, la trazabilidad, el perfil CSS y `capturas/` con `indice.md`. Di cómo abrirlo.
- **Claude (web / escritorio)**: envía además con SendUserFile el HTML (se abre en cualquier navegador), `app.json`, la trazabilidad y las capturas. **Publícalo como artefacto solo si el usuario lo pide**: lleva la marca de AENA y un enlace publicado se puede compartir. Si lo pide, usa la herramienta Artifact (el fichero ya cumple el contrato de página: empieza por `<title>`, recursos embebidos, tema claro deliberado como un Site de Appian; `icon: "layout"`) y, en iteraciones, reconstruye y republica **en la misma ruta** para mantener el enlace.
- **Vuelta al documento**: cada captura se enlaza en su ficha PAN de `analisis/funcional.md`, debajo del título, con la ruta relativa desde `analisis/` (`![PAN-04 Revisar documentación](../prototipo/capturas/04-revisar.png)`). `capturas/indice.md` da la línea lista para pegar en cada ficha (sale del `ref` de la pantalla). No cuenta como cambio de la ficha: no sube la versión. Después, `comprobar.py <p>` del analista ya no avisa de pantallas sin captura.
  - Las preguntas nuevas del prototipo (`Q-nn`) se devuelven al analista, que las convierte en PC.
  - El Word lo regenera el analista (`df_docx.js`); así las capturas no se pierden en la siguiente versión. En modo fiel el documento es del cliente: entrega además las capturas con su índice para pegarlas en él.
- Resume en pocas líneas: pantallas, cobertura de historias, preguntas abiertas pendientes.

## Uso del prototipo (explícalo al entregar la primera vez)
- **Reunión**: navegación por las páginas del site, filtros, búsqueda, fichas, asistentes con validación, diálogos. Barra inferior: **Pantallas** (índice para saltar a cualquier pantalla o diálogo) y **Requisitos** (cobertura, preguntas abiertas, supuestos).
- **Documento funcional**: `capturas/*.png` + `capturas/indice.md` (pie de figura, ficha PAN, línea lista para pegar en ella, patrón e historias). En capturas la barra del prototipo no aparece.
- **Desarrollo**: **Inspector** (tecla `I`) muestra el componente SAIL y sus parámetros al pasar el ratón y al hacer clic; los supuestos aparecen con borde naranja.

## Dudas de Appian

Lo que no sepas con certeza de Appian se consulta en el MCP de documentación `appian-docs` (sus herramientas empiezan por `mcp__appian-docs__`) antes de escribirlo, nunca de memoria: si existe un componente, una función, un parámetro o un objeto, qué admite, sus límites, si depende de la licencia y desde qué versión.
- Una duda por consulta, escrita como una frase completa.
- Vale lo que diga la documentación de la versión del entorno del proyecto (va en la URL: `/help/26.6/`). Si solo lo dice una versión posterior, se avisa de que puede no estar disponible.
- Lo que se escribe a partir de la respuesta lleva su URL, en la forma `/latest/`.
- Sin el MCP, se consulta docs.appian.com con WebFetch o WebSearch. Si tampoco se puede, se escribe «sin verificar» y la duda pasa a pendientes.
- Qué conviene hacer (qué mecanismo elegir, cómo diseñarlo) no es una duda de documentación: se consulta en `appian-best-practices`, solo la sección que toca. Esa skill está junto a esta, y `python3 ../appian-best-practices/scripts/seccion.py 02 4.8` imprime solo §4.8 del doc 02.

**En el prototipo**, las dudas típicas son si un componente, parámetro o valor existe en `app.appianVersion`, qué admite de verdad un Site, un record type o una acción de registro antes de enseñarlo en una pantalla, y qué poner en los `$note` para desarrollo. Lo que quede sin verificar va a `openQuestions` o a un `$note`.

**Si el validador rechaza algo que la documentación confirma** para esa versión, créalo en un `prototype-extensions.json` junto al `app.json` (mismo formato que `schemas/prototype-extensions.json`: los parámetros y valores se fusionan con los del componente) con la URL en `source`. validate y build lo leen automáticamente. No edites la carpeta del plugin: puede ser de solo lectura y se sobrescribe al actualizar. Díselo al usuario para que se incorpore al plugin. La documentación complementa al validador, no lo sustituye.

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
