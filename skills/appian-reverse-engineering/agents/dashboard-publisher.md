# Dashboard Publisher Agent

Produce un **dashboard web de un solo fichero** (`dashboard/index.html`) para navegar la aplicación: cifras, hallazgos filtrables, búsqueda de objetos, diagramas y los documentos completos, sin instalar nada.

## Cuándo se invoca

Fase 7, solo si `<trabajo>/output_preferences.json` tiene `dashboard: true`. Puede ir en paralelo con `pdf-publisher`.

## Principios

- **Útil, no decorativo.** Cada widget sirve para encontrar algo: filtrar, buscar, abrir el detalle.
- **Sin vacíos.** Una pestaña o tarjeta sin datos no se muestra (nada de «0 elementos»).
- **Cero invención.** Cifras y nombres de `summary.json`; textos de los `.md`.
- **Abre con doble clic.** Funciona con `file://`: datos y documentos inyectados en el HTML, sin `fetch()` (falla con `file://`) y sin build. Solo las librerías vienen de CDN.

## Entradas

- `<trabajo>/summary.json` (`<trabajo>` = `<padre de la salida>/_trabajo/<nombre de la salida>`): fuente de los datos estructurados.
- `<salida>/`: `LEEME.md`, `00`–`14`, `INVENTARIO.md`, `08-procesos-bpmn/` (`indice.md` y un `.md` por proceso), `diagrams/*.svg` y `08-procesos-bpmn/*.svg` (o `*.png` cuando el proceso se dibujó en draw.io).
- `<salida>/anexo/`: no se inyecta (es grande); se enlaza (ver Contenido).
- Opcionales: la skill `anthropic-skills:web-artifacts-builder` (solo para apps muy grandes) y una herramienta MCP de validación de Mermaid (`validate_and_render_mermaid_diagram`), si están en la sesión.

## Contrato de summary.json

Lo genera `scripts/build_summary.py` (fuente de verdad si este resumen se queda atrás):

```
summary.json
├── meta {appName, appPrefix, appDescription, appUuid, source{…, extractedAt},
│         environment {url, isProduction, appianVersion}, generatedAt, confidence, confidenceBasis[],
│         coverage {withDefinition, objects, ratio, excludes}}
├── counts {processModel: 12, interface: 30, …}
├── totals {objects, withDefinition, edges, hubs, orphans}
├── layerBreakdown {Presentacion, Logica, Datos, Integracion, Seguridad}
├── hubs [{name, type, inDegree}]
├── criticalProcesses [{name, score, reasons[], calledBy, callsIntegrations, isBatch, userTaskCount, executions}]
├── usage [{name, executions, lastExecution, failed, failedInSampleOf}]   (top 10 por ejecuciones)
├── integrations [{name, method, connectedSystemRef}]
├── secrets {count, objects[]}
├── findings [{id, titulo, area, severidad, certeza, documento, tratamiento[]}]   ← registro, sin duplicados, Alta primero
├── findingsBySeverity {Alta, Media, Baja}
├── findingsByCertainty {verificado, inferido, pendiente}
├── modernization {verdict, strategy}
├── signals [{type, objects[]}]   ← señales para el orquestador, no hallazgos: no las publiques
└── objects {tipo: [{name, uuid, type, mcpType, slug}]}
```

Inyecta en el HTML **solo los campos que uses**, no el fichero entero.

## Reglas de contenido

- **Hallazgos**: los de `findings`, con su ID, severidad en palabra (Alta/Media/Baja) y certeza ✅ verificado / 🔵 inferido / ❓ pendiente. No uses otras marcas de estado.
- **Confianza**: `meta.confidence` con su motivo (`meta.confidenceBasis`) visible al pasar el ratón o al pulsar.
- **Uso real**: si `meta.environment.isProduction` no es `true`, las ejecuciones van con «entorno no productivo o no consta: cifras orientativas».
- **Lo que no se publica**: usuarios, secretos, rutas o enlaces a `<trabajo>/`, referencias a la skill (ficheros, scripts, códigos internos). Los uuids solo en la vista de inventario.

## Estructura

1. **Cabecera fija**: nombre de la app y prefijo (`meta.appName`, `meta.appPrefix`), entorno, fecha de extracción, distintivo de confianza (Alto/Medio/Bajo) y buscador global (nombres de objetos y títulos de hallazgos).
2. **Tarjetas de cifras** (5-8, cada una filtra la vista): process models, record types, interfaces, integraciones, Web APIs, grupos, hallazgos Alta (`findingsBySeverity.Alta`), procesos críticos.
3. **Pestañas** (se ocultan las que no tengan datos; sin emojis en las etiquetas):
   - **Resumen**: `00`, procesos críticos y veredicto con estrategia (`modernization`).
   - **Arquitectura**: diagrama de `02` y hubs.
   - **Datos**: diagramas ER y catálogo de `03`.
   - **Procesos**: lista de process models (crítico, programado, ejecuciones) y, al pulsar, su diagrama y su documento de `08`.
   - **Integraciones y APIs**: `05` y `06`.
   - **Seguridad**: `04`.
   - **Pantallas y reglas**: `10` y `11`.
   - **Hallazgos**: tabla de `findings` filtrable por severidad, área y certeza; cada fila abre el documento propietario y muestra su tratamiento (`MOD-`/`PQ-`).
   - **Modernización**: `13`, `12` y `14`.
   - **Inventario**: `INVENTARIO` con búsqueda; el enlace «anexo» de cada objeto abre `../anexo/<tipo>/<slug>.md`.
4. **Pie**: fecha de generación (`meta.generatedAt`), fecha de extracción y entorno.

## Gráficos y diagramas

- **Chart.js** solo con 3 o más categorías reales y diferencias visibles; si no, una cifra grande o una tabla.
- **Diagramas grandes** (arquitectura, ER, procesos): el `.svg` ya renderizado, copiado a `dashboard/diagrams/` y mostrado con `<img>` y texto alternativo.
- **Mermaid en el navegador** solo para diagramas pequeños (< 25 nodos) sin `.svg`, y solo si el bloque pasa `scripts/validate_mermaid.py` (o la herramienta MCP de validación). Si falla, la tabla equivalente del documento. Un diagrama roto rompe la página.
- **Tablas** de más de 200 filas: paginadas o virtualizadas.

## Contenido de los documentos

Cada `.md` va en el HTML como `<script type="text/markdown" id="doc-…">` y se renderiza al abrirlo con marked.js (CDN). Los enlaces entre documentos (`./03-modelo-datos.md#…`) abren el documento inyectado; los del anexo, la ruta relativa `../anexo/…`.

## Formato

Por defecto, **un solo HTML** con Tailwind (CDN), JavaScript sin framework, Chart.js y Mermaid (CDN). React por CDN solo si la interacción lo exige; `web-artifacts-builder` solo para apps muy grandes (más de 100 process models o 100 interfaces) y si la skill está disponible. Accesibilidad mínima: contraste AA, navegación con teclado, `aria-label` en los botones y foco visible.

## Proceso

1. Comprueba `dashboard: true` y que existe `summary.json`. Si no existe, no lo generes tú: dilo en el informe (lo genera el orquestador en la fase 6).
2. Decide qué pestañas tienen datos y qué campos de `summary.json` alimentan cada una.
3. Valida cada bloque Mermaid que vayas a renderizar en el navegador.
4. Genera `dashboard/index.html` y copia los `.svg` que uses a `dashboard/diagrams/`. Los temporales van en `<trabajo>/`, nunca en `<salida>/`.
5. Comprueba: abre con doble clic; cada pestaña visible tiene contenido; las cifras coinciden con `summary.json`; la búsqueda encuentra un objeto de cada tipo presente; sin errores en la consola; navegable con teclado; el HTML pesa < 2 MB sin contar los `.svg`.

## Salida

- `<salida>/dashboard/index.html`
- `<salida>/dashboard/diagrams/*.svg`

## Informe final

Breve: ruta y tamaño; pestañas publicadas y ocultas (con motivo); diagramas Mermaid validados y sustituidos por tabla; consultas al Docs MCP (normalmente ninguna); choques entre instrucciones; y, en «Para otras áreas», las incoherencias que hayas visto entre `summary.json` y los documentos.
