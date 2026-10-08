<!--
  Plantilla 00 — Resumen ejecutivo (orquestador, fase 6, después de la pasada de coherencia).
  Fuente única de cifras: <trabajo>/summary.json (build_summary.py, ejecutado después de build_registry.py).
  No recalcules ni copies cifras de otros documentos: si summary.json contradice un documento, corrige el
  documento en la pasada de coherencia y vuelve a generar summary.json.
  Objetivo 1-2 pantallas, máximo 3. Las secciones sin datos se omiten.

  De dónde sale cada dato:
    Confianza ........... meta.confidence + meta.confidenceBasis (unidos por «; »)
    Entorno ............. meta.environment {url, isProduction, appianVersion}; fecha: meta.source.extractedAt
    Cifras .............. counts, totals, layerBreakdown (sus 6 claves, en el orden y con los nombres de 02)
    Procesos críticos ... criticalProcesses (ya ordenados; máx. 5). Enlace: slug de objects.processModel
    Hallazgos ........... findingsBySeverity, findingsByCertainty y findings de severidad Alta (si no hay Alta: los
                          Media, máx. 5, y dilo en el TL;DR). Evidencia: la de cada uno en <trabajo>/registro.json,
                          enlazada a la ficha de su objeto en el anexo (anexo/<tipo>/<slug>.md, slug de inventory.json)
    Uso real ............ usage (los 3-5 más ejecutados; failedInSampleOf = fallos en una muestra) y
                          signals[type=processModelsWithoutExecutions]. Los fallos citan su H-PRO (08); los
                          procesos sin ejecuciones, su H-GEN (09). Sin historial, la sección es una línea:
                          «La extracción no trae historial de ejecuciones.»
  Los secretos son hallazgos H-SEG de severidad Alta: salen en «Hallazgos principales».
  Certeza: verificado ✅ · inferido 🔶 · pendiente ❓. En 00 los hallazgos se citan por ID, sin columna de severidad.
  Limitaciones globales (entorno no productivo, muestra de ejecuciones…): no se explican aquí; las cifras afectadas
  llevan la marca «orientativo (ver LEEME)».
-->

# {{meta.appName}}: resumen ejecutivo

> **Responde a:** ¿Qué es la aplicación y qué tamaño tiene? ¿Qué procesos son críticos y cuánto se usan? ¿Qué es lo más grave que se ha encontrado? ¿Cuánto se puede confiar en esta documentación?

> **TL;DR**: {{Qué hace la aplicación y para quién, en lenguaje de negocio, 1-2 frases}}. {{Lo más grave: el hallazgo Alta principal en una frase}}.
> **Volumen**: {{totals.objects}} objetos ({{n}} process models, {{n}} interfaces, {{n}} record types). **Hallazgos**: {{N}} (Alta: {{findingsBySeverity.Alta}}) — principales: [{{H-SEG-01}}](./04-seguridad-grupos.md#hallazgos), [{{H-PRO-02}}](./08-procesos-bpmn/{{slug}}.md#hallazgos).

| Dato | Valor |
|---|---|
| Aplicación | `{{meta.appName}}` · prefijo `{{meta.appPrefix}}` |
| Entorno | `{{meta.environment.url}}` ({{producción / no productivo / no consta si es producción}}) |
| Versión de Appian | {{meta.environment.appianVersion o «no determinada»}} |
| Extracción | {{AAAA-MM-DD de meta.source.extractedAt}}, en solo lectura |
| Confianza de la documentación | **{{meta.confidence}}**: {{meta.confidenceBasis}} |

## La aplicación en cifras

<!-- Las 6 claves de layerBreakdown, con estos nombres y en este orden (los de 02). Una capa con 0 objetos se omite. -->

| Capa | Objetos | Qué incluye | Dónde |
|---|---|---|---|
| Entrada y presentación | {{layerBreakdown["Entrada y presentación"]}} | {{n}} sites, {{n}} interfaces, {{n}} Web APIs | [10](./10-pantallas.md), [06](./06-apis-expuestas.md) |
| Lógica | {{layerBreakdown["Lógica"]}} | {{n}} process models ({{n}} programados), {{n}} reglas, {{n}} decisiones, {{n}} agentes de IA | [08](./08-procesos-bpmn/indice.md), [11](./11-reglas-negocio.md) |
| Datos | {{layerBreakdown["Datos"]}} | {{n}} record types, {{n}} CDTs, {{n}} data stores | [03](./03-modelo-datos.md) |
| Integración | {{layerBreakdown["Integración"]}} | {{n}} integraciones, {{n}} connected systems | [05](./05-integraciones-consumidas.md) |
| Transversal | {{layerBreakdown["Transversal"]}} | {{n}} constantes | [02](./02-arquitectura.md), [09](./09-valor-adicional.md#configuración-por-entorno) |
| Seguridad | {{layerBreakdown["Seguridad"]}} | {{n}} grupos | [04](./04-seguridad-grupos.md) |

{{totals.withDefinition}} de {{totals.objects}} objetos con definición ([INVENTARIO](./INVENTARIO.md)){{; fuera de las capas: n carpetas, n …}} · {{totals.hubs}} muy referenciados ([02](./02-arquitectura.md)) · {{totals.orphans}} sin referencias ([09](./09-valor-adicional.md#objetos-huérfanos)).

## Procesos críticos

| Proceso | Por qué es crítico | Programado | Ejecuciones{{, orientativo (ver [LEEME](./LEEME.md))}} |
|---|---|---|---|
| [`{{name}}`](./08-procesos-bpmn/{{slug}}.md) | {{reasons, unidas por «, »}} | Sí/No | {{executions o «—»}} |

{{Si hay más de 5: «Hay N procesos críticos; el resto, en el [índice de procesos](./08-procesos-bpmn/indice.md).»}}

## Hallazgos principales

{{N}} hallazgos: Alta {{n}} · Media {{n}} · Baja {{n}}; verificados {{n}}, inferidos {{n}}, pendientes de validar {{n}}. Registro completo en [09](./09-valor-adicional.md#registro-de-hallazgos).

| ID | Hallazgo | Área | Certeza | Evidencia |
|---|---|---|---|---|
| [{{H-SEG-01}}](./{{documento}}) | {{titulo}} | {{area}} | ✅ | [`mcp:{{tipo}}/{{nombre}}#{{ubicación}}`](./anexo/{{tipo}}/{{slug}}.md) |

## Uso real

| Proceso | Ejecuciones{{, orientativo (ver [LEEME](./LEEME.md))}} | Última | Fallos en la muestra |
|---|---|---|---|
| [`{{name}}`](./08-procesos-bpmn/{{slug}}.md) | {{executions}} | {{AAAA-MM-DD}} | {{«3 de las últimas 50» ([H-PRO-NN](./08-procesos-bpmn/{{slug}}.md#hallazgos)) o «—»}} |

{{N}} process models sin ejecuciones: `{{a}}`, `{{b}}` ([{{H-GEN-NN}}](./09-valor-adicional.md#hallazgos)).

## Cobertura y límites

{{1-3 líneas: lo que falta y cambia las conclusiones (p. ej. «sin volúmenes de datos», «sin role maps»)}}. La lista completa y la guía de lectura, en [LEEME](./LEEME.md).
