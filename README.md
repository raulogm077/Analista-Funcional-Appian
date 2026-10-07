# appian-analisis-funcional

Análisis funcional y propuesta de pantallas para aplicaciones Appian, del
material del cliente al prototipo navegable:

```
transcripciones · correos · actas · diagramas de flujo · DF / ERS del cliente
        │
        ▼  appian-functional-analyst
fuentes/ (FU-01, FU-02…)  →  ddf.md  (+ DDF .docx con diagramas, en modo síntesis)
        │        └──► appian-diagramas-bpmn: proceso en draw.io (.drawio editable) + PNG
        │
        ▼  appian-prototipos-aena
prototipo HTML navegable (marca AENA) · capturas PNG con pie de figura · trazabilidad
        │
        └──► las capturas vuelven al DDF (o al DF del cliente) bajo su ficha de pantalla
```

Sirve para cualquier proceso (acuerdos con terceros, medioambiente, servidumbres,
informes, expedientes…): el dominio sale siempre de las fuentes del proyecto. Los
casos y las plantillas del plugin son ejemplos de técnica, todos al mismo nivel
(`skills/appian-prototipos-aena/examples/README.md`).

## Qué incluye

| Componente | Para qué |
|---|---|
| Skill `appian-functional-analyst` | Lee y cataloga las fuentes, detecta decisiones y contradicciones, y escribe el análisis (`ddf.md`) y el DDF en Word. Tres modos: **síntesis** (reuniones, correos), **fiel** (ya hay un DF o ERS: extracto literal, sin Word) y **actualización** (cada reunión o correo nuevo se encaja en el análisis con un informe de impacto que aprueba el analista, registro de decisiones e IDs estables) |
| Skill `appian-diagramas-bpmn` | Dibuja y mantiene los diagramas de proceso en draw.io con notación BPMN y carriles por perfil: se crean desde una descripción del proceso, se actualizan por cambios respetando lo que se haya colocado a mano, se pueden editar en draw.io durante una reunión (después dice qué cambió y da código a lo nuevo), generan el PNG del documento sin internet y se exportan a BPMN 2.0. La usan el analista y la ingeniería inversa |
| Skill `appian-prototipos-aena` | Convierte el `ddf.md` en un prototipo navegable con los 147 componentes de interfaz de Appian 26.9, 12 patrones de pantalla, un catálogo de bloques con su guía de uso, componentes de IA de Appian, validaciones, diálogos, auditoría de contraste, perfil CSS de la marca y capturas para el documento |
| MCP `appian-docs` | Búsqueda en la documentación oficial de Appian (servidor público de Appian alojado en Kapa) |

## Requisitos

| Entorno | Qué hace falta |
|---|---|
| **Claude (web o escritorio, sesiones en la nube)** | Nada: Python, Playwright, navegador, LibreOffice y la skill `docx` ya están |
| **Claude Code** en el equipo | **Python 3.9+** (en Windows, el comando es `python`). Para diagramas, prueba de humo y capturas: `pip install playwright` (versión actual) y un navegador (`python -m playwright install chromium`, o Chrome / Edge ya instalados: no hace falta descargar nada más). Para el DDF en Word: Node.js con el paquete `docx` y el plugin `document-skills` del repositorio `anthropics/skills`; pandoc o LibreOffice para revisarlo. Opcional: `pdftotext` o `pip install pypdf` para PDF; LibreOffice y poppler para ver diapositivas de un DF |

Comprobación rápida en un equipo nuevo: pide a Claude «comprueba que el plugin
funciona en este equipo», o ejecuta desde la carpeta del plugin:

```bash
python skills/appian-prototipos-aena/scripts/selftest.py
python skills/appian-diagramas-bpmn/scripts/selftest.py
python skills/appian-functional-analyst/scripts/render_mermaid.py --check skills/appian-functional-analyst/assets/prueba.mmd
```

Nada de lo anterior envía información del cliente fuera del equipo: Mermaid
(licencia MIT) y el visor de draw.io (licencia Apache 2.0) van incluidos en el plugin
y los diagramas se dibujan con el navegador local. Para editar un `.drawio` a mano
sirve draw.io Desktop, app.diagrams.net (no sube el fichero) o la integración de
draw.io con SharePoint y OneDrive.

**Correos de Outlook (.msg)**: el paquete `extract-msg` no instala en muchos
equipos. Lo fiable es guardar el correo como `.eml` (Archivo → Guardar como) o
PDF.

## Instalación

- **Claude (organización)**: un administrador publica el fichero
  `appian-analisis-funcional.plugin` para la organización; cada persona lo
  instala desde el catálogo de plugins. También se puede instalar a título
  personal abriendo el `.plugin` en una conversación. El `.plugin` es la carpeta
  del plugin comprimida en zip (sin `.git` ni `__pycache__`):
  `zip -r appian-analisis-funcional.plugin . -x ".git/*" "*__pycache__*"`.
- **Claude Code**: el repositorio es también un marketplace.
  ```bash
  claude plugin marketplace add <ruta o URL git del repositorio>
  claude plugin install appian-analisis-funcional@appian-analisis-funcional
  ```

**Retirar las skills sueltas**: si la organización tenía `appian-functional-analyst`
o `appian-prototipos-aena` como skills independientes, hay que eliminarlas al
publicar el plugin. Si no, existen dos veces con versiones distintas y no se sabe
cuál se activa.

**Si Claude dice que «el kit de la skill no está disponible»**: esa persona tiene
una skill suelta de antes del plugin (solo el SKILL.md, que descargaba el kit de un
artefacto privado). Hay que retirarla e instalar el `.plugin`, que lleva todo dentro.

### MCP de documentación de Appian

Se conecta solo al instalar el plugin. La primera consulta pide iniciar sesión
con Google o GitHub (lo exige el proveedor, Kapa; no guarda datos personales).
Límite: 300 consultas al día y 60 por minuto por persona. Es opcional: sin él,
las skills consultan docs.appian.com por la web.

**No se incluye el Appian Dev MCP** (lectura y escritura de objetos de diseño):
se instala en local por persona (Python 3.13, `uv`, ruta propia y el plug-in
instalado en el entorno Appian por un administrador) y sirve para construir, no
para analizar ni proponer pantallas.

**No se incluye `appian-sail-generator`**: este plugin es de análisis y propuesta;
el paso a construcción (SAIL real) va en un plugin aparte. El `app.json` del
prototipo es un árbol SAIL real y sirve de punto de partida para ese paso.

## Confidencialidad

- `fuentes/`, `ddf.md` y los prototipos contienen información del cliente: no se
  publican fuera del proyecto.
- Un prototipo publicado como artefacto es privado hasta que su autor lo
  comparte.
- Los prototipos usan siempre personas y datos ficticios.

## Versiones

| Versión | Cambios |
|---|---|
| 0.6.0-alpha.2 | **`appian-diagramas-bpmn`: dibujos sin solapes y BPMN más completo** (sugerencias de la skill `appian-reverse-engineering`). Las tareas ya no se montan unas sobre otras cuando su nombre es corto, ni las etiquetas largas de eventos y puertas sobre la tarea vecina: la colocación del motor se ajusta al tamaño real de las formas de draw.io (`scripts/colocacion.py`) y las etiquetas se ajustan a 110 px. La etiqueta de un evento o una puerta va al lado por el que no llega ningún flujo. Tipos nuevos: `inicio_temporizador`, `inicio_mensaje`, `script` y `llamada` (llamada a otro proceso); flujo por defecto (`"defecto": true`); participantes externos (`externos`) con flujos de mensaje, y notas unidas a un paso (`notas`), todo con su lectura, comparación y cambios (`externo`, `quitar_externo`, `nota`, `quitar_nota`), también con la colocación hecha a mano. La exportación a BPMN 2.0 conserva todo eso (inicio con temporizador o mensaje, `scriptTask`, `callActivity`, `default`, participantes y `messageFlow`, `textAnnotation` con su asociación y el lado de cada etiqueta). Aviso cuando el diagrama pasa de 1.600 px de ancho y PNG limitado a unos 3.200 px. Ejemplo nuevo `ejemplos/pedido.json` y autotest ampliado |
| 0.6.0-alpha.1 | **Skill nueva `appian-diagramas-bpmn`**: diagramas de proceso en draw.io con las formas BPMN de draw.io (eventos, puertas, tareas de usuario, de sistema y manuales, subprocesos) y un carril por perfil. `diagrama.py crear` coloca los pasos con el motor de carriles de Mermaid y escribe `.drawio`, PNG y `.json` (el proceso que conoce el análisis); `actualizar` aplica una lista corta de cambios, recoloca todo si nadie ha movido nada y, si se colocó a mano, lo respeta y pone lo nuevo junto a su paso anterior; `comparar` dice qué se cambió a mano en draw.io (también en ficheros comprimidos o con formas básicas), da código a lo añadido y con `--aceptar` lo incorpora; `leer` devuelve el proceso en JSON para no leer XML; `bpmn` exporta BPMN 2.0 con posiciones (se abre en Camunda Modeler o bpmn.io). PNG sin conexión con el visor de draw.io incluido. El analista dibuja con ella el flujo de la Sec 6 (los demás diagramas siguen en Mermaid, cuyo motor pasa a esta skill). Prueba automática `selftest.py` |
| 0.5.0-beta.6 | **Probado de punta a punta con transcripciones reales de dos procesos** (síntesis, actualización con una reunión nueva y prototipo de 8 pantallas cada uno; material sin incorporar al plugin). Analista: `leer_fuentes.py` ya no da «0 fuentes» sin avisar cuando las fuentes están en la propia carpeta de salida (y sale con error si no cataloga ninguna), y reconoce las transcripciones `.txt` con marcas `[hh:mm:ss]` y su duración; la plantilla dice el formato exacto que leen los scripts (títulos `## N. Título`, reglas de negocio en filas) y `comprobar_ddf.py` avisa si faltan secciones con ese título, de IDs citados que no existen en ningún sitio, de fuentes sin participantes identificados (la comprobación de nombres no las cubre) y ya no toma las capturas del prototipo como cambios de las fichas; `ddf_indice.py derivadas` no reescribe una Sec 7 hecha a mano ni reutiliza IDs de casos de uso; instrucciones para diagramas sin Word, aplicaciones ya construidas que se explican en demos, transcripciones ilegibles y aprobaciones en modo desatendido (una decisión explícita del cliente no se le vuelve a preguntar). Prototipos: la fuente Open Sans va dentro del HTML (licencia OFL): capturas con la fuente de la marca y sin depender de internet; se corrige el espaciado raro de las etiquetas en las capturas; un alta con record type abierta sin `id` ya no sale rellena con otro registro; `action_banner` informativo o de error con botón llega al contraste AA; `contrast_audit.py` sale con error si hay fallos; pies de captura y trazabilidad con el nombre de la vista y el `ref` de la ficha (también por vista); `noScreen` para requisitos sin pantalla propia; el validador avisa si la primera columna de un listado no enlaza a la ficha o si un texto visible muestra IDs del análisis; instrucciones: partir del código de cada patrón en `generar_plantillas.py`, tareas de captura de datos → P03, cuadro de mando → P08, API `PROTO.show` para la prueba dirigida y ruta de las capturas en el `ddf.md` |
| 0.5.0-beta.5 | **Coherencia y dependencias revisadas**. Auditoría de las dos skills: todo fichero, carpeta, script y parámetro que citan existe dentro del plugin; no hay rutas de un equipo concreto ni enlaces a artefactos; las dependencias externas son solo las documentadas y opcionales (Playwright y navegador para capturas, pypdf/poppler para PDF, Node con `docx` para el Word, Open Sans de Google Fonts, MCP de documentación). Correcciones: la comprobación del `ddf.md` (`comprobar_ddf.py`) pasa al paso de verificación, porque estaba dentro del paso del Word y se saltaba cuando solo se pedía el `ddf.md`; `comprobar_ddf.py` y `ddf_indice.py` leen «Se verifica en» también de los RF en tabla (modo fiel), con lo que el caso de ejemplo pasa su propia comprobación; el nombre de la herramienta del MCP de documentación ya no se fija (cambia en el servidor). README: qué hacer si alguien tiene la skill suelta de antes del plugin («el kit de la skill no está disponible») |
| 0.5.0-beta.4 | **Plugin genérico para cualquier proceso**. ATP deja de ser el modelo: su recorrido completo pasa a `examples/casos/atp/`, un caso más al mismo nivel que los que se añadan (medioambiente, servidumbres, informes…), y `examples/README.md` explica qué enseña cada ejemplo y cómo añadir un caso. `selftest.py` descubre solo los casos de `examples/casos/` y les pasa validación, construcción, prueba de humo y contraste. Los ejemplos de la documentación (formato del spec, reglas de textos, plantilla del DDF del analista) usan un dominio genérico y ficticio de expedientes, el mismo que las plantillas, y el formato del spec pasa a Appian 26.9. Las dos skills dicen explícitamente que el dominio sale del `ddf.md` del proyecto y la rúbrica UX suma el criterio 25: nada de restos de plantillas o ejemplos |
| 0.5.0-beta.3 | **Appian 26.9 completo y revisión de color y contraste**. Versión por defecto 26.9 y catálogo de los 147 componentes de interfaz de Appian por categoría (`schemas/catalogo-appian.json`); `selftest.py` comprueba que los 147 están en los schemas, el motor y la galería. Componentes nuevos en el motor: navegadores en columnas de usuarios, grupos, documentos y carpetas, jerarquías en columnas y en árbol (`$tree`, `$icon`), organigrama (a!orgChartField), a!pickerFieldDocumentsAndFolders, enlaces de autorización, noticias e informes, vídeo y contenido web, además de `targetLocation` en a!recordLink y `bannerMessage` en a!startProcessLink. Galería navegable de todos los componentes (`examples/componentes/`, 14 pantallas) y patrones del SAIL Design System 26.9 como helpers: calendario mensual y semanal con agenda del día (`calendar_month`, `calendar_week`), hilo de comentarios con adjuntos y respuestas plegables (`comment_thread`) y tablero kanban (`kanban`). Perfil CSS de Appian: la marca define su `cssProfile`, el validador lo comprueba contra las 156 propiedades de 26.9 (`schemas/css-profile-properties.json`) y `build.py` escribe `<prototipo>-perfil-css.txt` listo para Admin Console › Branding. Color y contraste según la guía de Appian (design-rules §4 reescrito): paleta corta con significado fijo, gráficos con el color de cada estado (`state_chart_colors`, `$series`) y series en un orden con 3:1 sobre blanco (`CHART`), texto calculado para el máximo contraste sobre cualquier fondo, también con transparencias. Nuevo `scripts/contrast_audit.py`, que mide en el navegador el contraste real de cada pantalla (texto 4,5:1, texto grande 3:1, bordes de campo y textos de gráficos 3:1) y que el autotest pasa, junto con la prueba de humo, en los cinco ejemplos; el validador añade reglas estáticas de contraste (texto e iconos sobre su contenedor, etiquetas, sellos, series de gráficos sin etiquetas de datos). Pasada visual de las plantillas: datos de ejemplo más variados y coherentes (fechas de la tarea tomadas del expediente), accesos rápidos sin repetir la acción principal, anillo con etiquetas, avatares con color por persona, eventos con el tinte de su tipo. Guía: patrones y componentes de 26.9 (§16) y rúbrica de 24 criterios (§17); formato del spec con `users`, `groups` y `documents`, `$local`, acciones `prepend` y filtros de fecha en texto (`longdate`, `monthyear`, `dayname`, `daymonth`, `time`) |
| 0.5.0-beta.2 | **Más repertorio de interfaz y componentes de IA**. El motor pinta con su anatomía real los chats de IA de Appian (a!agentChatField con selector de conversaciones, llamadas a herramientas, modo depuración, botón Detener y `outputsSaveInto`; a!chatField con mensajes de componentes; a!dataFabricChatField con preguntas sugeridas; a!recordsChatField; a!documentsChatField), el visor de documentos con página inicial y resaltado, la búsqueda inteligente de grids (`smartSearchType`, puntuación por fila y orden por relevancia), el drilldown de gráficos (`fv!selection`) y las novedades de 26.7–26.9 (pestañas verticales, bordes y pesos de etiqueta, `a!pageLink`, `a!recordKnowledgeGraph`, filtro por leyenda, estilos de subida, celdas compuestas en grids). Catálogo de bloques (`references/bloques.md`, ~40 helpers con SAIL real: cabeceras hero y de filtros, navegación lateral, KPI con minigráfico o progreso, duración, pasos, clasificación, grid con detalle, selección, drilldown, lista doble, entradas dinámicas, documentos, comentarios, cards-botón e informativas, bloques de IA) con galerías navegables (`examples/bloques/`, `examples/ia/`). Patrones nuevos P09 maestro-detalle, P10 portada de módulo, P11 asistente de IA y P12 revisión de datos sugeridos por IA; las 12 plantillas y el catálogo se generan con `templates/generar_plantillas.py` y datos coherentes entre pantallas. Guía: IA (§14: componente según el origen de la respuesta, colocación, estado inicial, fiabilidad, fuente, la IA propone y el usuario decide), cabeceras y navegación secundaria (§15) y rúbrica de 22 criterios. El validador añade reglas de IA (chat de datos solo en su panel, nada de chats en side-by-side, `debugMode`, textos por defecto en inglés, puntuaciones visibles) y `$uxIgnore` para desviaciones justificadas. Cifras con separador de miles también en 4 dígitos |
| 0.5.0-beta.1 | **Diseño de pantallas (fases F0–F2 y rediseño de ficha e inicio)**. Guía UX nueva (`references/design-rules.md`): SAIL Design System de Appian 26.6 adaptado a AENA, con jerarquía de títulos, cards blancas con sombra sobre fondo gris, paleta semántica de estados (`brand-aena.json → states`), un único botón SOLID por pantalla, destructivas en GHOST rojo, grids de ≤7 columnas consolidadas, fichas con franja de datos clave y áreas 1:N en vistas, y rúbrica de revisión de 20 criterios. El validador emite avisos `UX ·`, cierra con «Calidad UX», comprueba la versión mínima de Appian por componente, parámetro y valor (`schemas/appian-versions.json`, por defecto 26.6) y rechaza funciones y parámetros que no existen en Appian. El motor pinta a!sidebarTemplate, a!tabLayout, plantillas de a!cardChoiceField, a!chartReferenceLine, a!scatterChartField, historial en timeline, KPI con tendencia, selección de filas, mapas de calor, chat con IA (a!chatField, a!agentChatField), pickers de documentos, carpetas y personalizados, y usa por defecto los valores documentados de Appian. `sail_helpers.py` gana bloques (`key_facts`, `field_summary`, `kpi_strip`, `section_card`, `action_banner`, `empty_state`, `two_line`, `alert_icons`, `choice_cards`…). Ejemplo ATP rehecho, y plantillas P02 y P06 renovadas |
| 0.4.0 | Discovery incremental, probado con 4 reuniones reales sobre un análisis de 11.600 líneas: procedimiento `references/actualizacion.md` (nota de la fuente, puntos clasificados NUEVO/COMPLETA/CONFIRMA/VALIDA/CAMBIA/ANULA/RESPONDE/ALCANCE±, dependencias, informe de impacto `impacto/FU-xx.md` que aprueba el analista, aplicar y verificar); estado por pieza con 🔒 Validado y anulaciones tachadas; registro de decisiones (D-xxx) en la Sec 17; `ddf_indice.py` (consultar el análisis sin leerlo entero: buscar, ficha, sección, impacto, siguientes IDs, grafo, secciones derivadas, diagramas); `unir_modulos.py`; `comprobar_ddf.py` con `--anterior` e `--impacto` (IDs desaparecidos, cambios no declarados, lo 🔒 sin aprobación, tramos de la reunión sin leer) y `--corregir-citas`; Word con tachados y columnas que no se parten |
| 0.3.0 | Probado de punta a punta con 25 transcripciones reales (modo síntesis): lectura de transcripciones .txt de Teams (tipo, participantes y fecha desde el nombre), rutas con corchetes, procedimiento para volumen grande (notas por fuente con agentes en paralelo, módulos con rangos de IDs, fusión), `comprobar_ddf.py` (IDs duplicados, criterios, citas y nombres) y `ddf_docx.js` (Word con portada, índice, figuras numeradas y pie de confidencialidad; requiere Node.js y el paquete `docx`) |
| 0.2.0 | Fichas de pantalla (campos con origen y valor si vacío, filtros, ordenación, acciones con qué pasa después, confirmación de borrados, visibilidad por rol) y fichas de tarea (estado de entrada, opciones con estado de salida, criterio mínimo), cada una con sus criterios de aceptación; la Sec 8 remite a ellos y la Sec 16 es la matriz de cobertura; actores con «Participa en»; diagramas sin comentarios y con IDs de actividad; modo «ficha suelta»; los criterios sirven de lista de comprobación del prototipo |
| 0.1.0 | Primera versión: analista con lectura de fuentes, modos fiel y actualización, `ddf.md` como fuente de verdad y Mermaid sin conexión; prototipos con el kit completo, entrada desde el `ddf.md`, soporte de Chrome / Edge y `selftest.py`; MCP público de documentación de Appian |
