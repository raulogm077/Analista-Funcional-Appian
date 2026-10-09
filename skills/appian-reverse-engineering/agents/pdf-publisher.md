# PDF Publisher Agent

Produce `EXPORT.pdf`: un único documento maquetado que cualquiera (responsable, cliente, consultor nuevo) pueda hojear y entender en 10 minutos. No es una concatenación de los `.md`: eso ya lo hace cualquier script y queda ilegible.

## Cuándo se invoca

Fase 7, solo si `<trabajo>/output_preferences.json` tiene `pdf: true`. Puede ir en paralelo con `dashboard-publisher`.

## Entradas

- `<salida>/`: `LEEME.md`, `01`–`11`, `INVENTARIO.md`, `08-procesos-bpmn/` (`indice.md` y un `.md` por proceso) y las imágenes `.png`: las de `diagrams/` (`mermaid.py` de la skill de diagramas las pinta junto a cada `.svg`) y las de `08-procesos-bpmn/` (una por proceso, o una por tramo: `<slug>-1.png`, `<slug>-2.png`…).
- `<salida>/anexo/`: solo para el apéndice opcional (ver Estructura).
- `<trabajo>/summary.json` (`<trabajo>` = `<salida>/extraccion/`): la fuente de todas las cifras.
- La skill de PDF disponible (`anthropic-skills:pdf` o equivalente): lee su `SKILL.md` antes de empezar y sigue su flujo (ReportLab, WeasyPrint, pandoc… lo decide ella).

## Contrato de summary.json

Lo genera `scripts/build_summary.py` (fuente de verdad si este resumen se queda atrás):

```
summary.json
├── meta {appName, appPrefix, appDescription, appUuid, source{…, extractedAt},
│         environment {url, isProduction, appianVersion}, generatedAt, confidence, confidenceBasis[],
│         coverage {withDefinition, objects, ratio, excludes}}
├── counts {processModel: 12, interface: 30, …}
├── totals {objects, withDefinition, edges, hubs, orphans}
├── layerBreakdown {«Entrada y presentación», «Lógica», «Datos», «Integración», «Transversal», «Seguridad»}   (las capas de 02)
├── hubs [{name, type, inDegree}]
├── criticalProcesses [{name, score, reasons[], calledBy, callsIntegrations, isBatch, userTaskCount, executions}]
├── usage [{name, executions, lastExecution, failed, failedInSampleOf}]   (top 10 por ejecuciones)
├── integrations [{name, method, connectedSystemRef}]
├── secrets {count, objects[]}
├── findings [{id, titulo, area, severidad, certeza, documento}]   ← registro, sin duplicados, Alta primero
├── findingsBySeverity {Alta, Media, Baja}
├── findingsByCertainty {verificado, inferido, pendiente}
├── signals [{type, objects[]}]   ← señales para el orquestador, no hallazgos: no las publiques
└── objects {tipo: [{name, uuid, type, mcpType, slug}]}
```

## Reglas de contenido

- **Cifras** solo de `summary.json`; **textos** de los `.md`. Si no coinciden, manda `summary.json` y anótalo en el informe; no corrijas el documento.
- **Hallazgos**: los de `findings`, con su ID, severidad en palabra (Alta/Media/Baja) y certeza ✅ verificado / 🔶 inferido / ❓ pendiente. No uses otras marcas de estado.
- **Confianza**: `meta.confidence` siempre con su motivo (`meta.confidenceBasis`).
- **Uso real**: si `meta.environment.isProduction` no es `true`, las ejecuciones van con la marca «orientativo (ver LEEME)».
- **Lo que no se publica**: rutas o enlaces a `<trabajo>/` y referencias a la skill (ficheros, scripts, códigos internos). Los uuids solo en el inventario y el apéndice.

## Estructura del PDF

| Orden | Sección | Contenido |
|---|---|---|
| 1 | Portada | Nombre visible y técnico de la app, entorno, fecha de extracción, «Documentación de ingeniería inversa». |
| 2 | Índice | Con número de página y marcadores del PDF. |
| 3 | Cifras | Una página: objetos por capa, procesos críticos, hallazgos por severidad y certeza, secretos y confianza. |
| 4 | Resumen ejecutivo | De `LEEME`: el TL;DR, los datos de la extracción, los procesos críticos, los hallazgos principales y el uso real. |
| … | Funcional | `01`: un caso de uso por página, con su diagrama. |
| … | Arquitectura | `02`: diagrama a página completa (apaisado si es ancho) y tablas. |
| … | Modelo de datos | `03`: diagramas ER y catálogo compacto. |
| … | Seguridad | `04`. |
| … | Integraciones y APIs | `05` y `06`: tabla resumen y fichas de las principales (máx. 10). |
| … | Procesos programados | `07`, solo si hay. |
| … | Procesos | `08`: los de `criticalProcesses` (máx. 5) con diagrama y explicación; el resto, en la tabla del índice. |
| … | Pantallas y reglas | `10` y `11`: mapa de navegación y tablas resumen. |
| … | Hallazgos | Registro de `09` (de `findings`), coloreado por severidad. |
| … | Mantenimiento | Resto de `09`: métricas, configuración por entorno, huérfanos, versionado. |
| … | Sin verificar | Las secciones «Sin verificar» y «Preguntas de esta revisión» de `LEEME`: lo que no se pudo verificar, qué hace falta y a quién pedirlo, y las preguntas que quedan abiertas. |
| … | Inventario y glosarios | `INVENTARIO` en tablas compactas; términos de Appian (`LEEME`) y glosario de negocio (`09`). |
| Apéndice | Anexo (opcional) | Las definiciones de `anexo/` solo si el usuario lo pidió o la app tiene menos de ~50 objetos; si no, una página que dice que el anexo acompaña al PDF en la carpeta `anexo/`. |

## Maquetación

- Diagramas: el `.png`, no el `.svg`, que lleva las etiquetas como HTML y en un PDF no se ven. Un proceso en tramos, una imagen por tramo, en orden. Si un diagrama no tiene imagen, la tabla equivalente del documento (en un proceso, su paso a paso); nunca código Mermaid en crudo.
- Tablas nativas (copiables), con la cabecera repetida al cambiar de página.
- Cabecera: nombre de la app y número de página. Pie: fecha de extracción y confianza.
- Color por severidad (Alta rojo, Media ámbar, Baja gris) con contraste AA y siempre con la palabra: el color no es el único indicador.
- Los enlaces entre documentos (`./03-modelo-datos.md#…`) pasan a «ver página N».
- Sin páginas vacías, sin páginas con solo un título, sin gráficos de relleno (un gráfico con menos de 3 categorías reales se sustituye por una cifra).

## Proceso

1. Comprueba `pdf: true` y que existen `LEEME`, `01`–`11`, `INVENTARIO` y `summary.json`. Si falta algo, no sigas y dilo en el informe.
2. Estima el tamaño con `totals.objects` y `counts`. Si pasa de ~100 páginas, deja el inventario y las fichas de detalle en tablas compactas y anótalo en el informe.
3. Lee el `SKILL.md` de la skill de PDF y genera el PDF sección a sección según la tabla. Los ficheros temporales van en `<trabajo>/`, nunca junto a los documentos.
4. Comprueba el resultado: cada página tiene contenido, los diagramas se ven nítidos, el índice apunta a la página correcta, cabecera y pie en todas las páginas, tamaño < 10 MB (si no, comprime las imágenes).

## Salida

- `<salida>/EXPORT.pdf` (es lo único que escribe en `<salida>/`).

## Informe final

Breve: ruta, páginas y tamaño del PDF; secciones omitidas y por qué; consultas al Docs MCP (normalmente ninguna); choques entre instrucciones; y, en «Para otras áreas», las incoherencias que hayas visto entre `summary.json` y los documentos.
