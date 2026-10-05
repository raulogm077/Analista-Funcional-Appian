<!--
  Plantilla 00 — Resumen ejecutivo (orquestador, fase 6, después de la pasada de coherencia).
  Fuente única de cifras: <trabajo>/summary.json (build_summary.py, ejecutado después de build_registry.py).
  No recalcules ni copies cifras de otros documentos: si summary.json contradice un documento, corrige el
  documento en la pasada de coherencia y vuelve a generar summary.json.
  Objetivo 1-2 pantallas, máximo 3. Sin usuarios. Las secciones sin datos se omiten.

  De dónde sale cada dato:
    Confianza ........... meta.confidence + meta.confidenceBasis (unidos por «; »)
    Entorno ............. meta.environment {url, isProduction, appianVersion}; fecha: meta.source.extractedAt
    Cifras .............. counts, totals, layerBreakdown (sus 6 claves, en el orden y con los nombres de 02)
    Procesos críticos ... criticalProcesses (ya ordenados; máx. 5). Enlace: slug de objects.processModel
    Hallazgos ........... findingsBySeverity, findingsByCertainty y findings de severidad Alta
                          (si no hay Alta: los Media, máx. 5, y dilo en el TL;DR)
    Secretos ............ secrets {count, objects}; tratamiento: los H-SEG de findings
    Modernización ....... modernization {verdict, strategy} (vienen de 13; si son null, falta
                          <trabajo>/modernizacion.json: corrígelo antes de escribir 00)
    Uso real ............ usage (top por ejecuciones; failedInSampleOf = fallos en una muestra) y signals[type=processModelsWithoutExecutions].
                          Los fallos citan su H-PRO (08); los procesos sin ejecuciones, su H-GEN (09).
  Certeza: verificado ✅ · inferido 🔵 · pendiente ❓. En 00 los hallazgos se citan por ID, sin columna de severidad.
  Limitaciones globales (entorno no productivo, muestra de ejecuciones…): no se explican aquí; las cifras afectadas
  llevan la marca «orientativo (ver LEEME)».
-->

# {{meta.appName}}: resumen ejecutivo

> **TL;DR**: {{Qué hace la aplicación y para quién, en lenguaje de negocio, 1-2 frases}}. {{Lo más importante: el hallazgo Alta principal o el veredicto en una frase}}.
> **Volumen**: {{totals.objects}} objetos ({{n}} process models, {{n}} interfaces, {{n}} record types). **Hallazgos**: {{N}} (Alta: {{findingsBySeverity.Alta}}) — principales: [{{H-SEG-01}}](./04-seguridad-grupos.md#hallazgos), [{{H-PRO-02}}](./08-procesos-bpmn/{{slug}}.md#hallazgos). **Veredicto**: {{modernization.verdict}}.

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
| Transversal | {{layerBreakdown["Transversal"]}} | {{n}} constantes | [02](./02-arquitectura.md), [09](./09-valor-adicional.md#constantes-por-entorno-y-secretos) |
| Seguridad | {{layerBreakdown["Seguridad"]}} | {{n}} grupos | [04](./04-seguridad-grupos.md) |

{{totals.withDefinition}} de {{totals.objects}} objetos con definición ([INVENTARIO](./INVENTARIO.md)){{; fuera de las capas: n carpetas, n …}} · {{totals.hubs}} objetos muy reutilizados ([02](./02-arquitectura.md)) y {{totals.orphans}} sin referencias ([lista en 09](./09-valor-adicional.md#objetos-huérfanos)).

## Procesos críticos

Criterio único para toda la documentación: cuántos objetos lo lanzan, a cuántas integraciones llama, si es programado y si tiene tareas humanas.

| Proceso | Por qué es crítico | Programado | Ejecuciones |
|---|---|---|---|
| [`{{name}}`](./08-procesos-bpmn/{{slug}}.md) | {{reasons, unidas por «, »}} | Sí/No | {{executions o «—»}} |

{{Si hay más de 5: «Hay N procesos críticos; el resto, en el [índice de procesos](./08-procesos-bpmn/indice.md).»}}

## Hallazgos principales

{{N}} hallazgos: Alta {{n}} · Media {{n}} · Baja {{n}}; verificados {{n}}, inferidos {{n}}, pendientes de validar {{n}}. Registro completo en [09](./09-valor-adicional.md#registro-de-hallazgos).

| ID | Hallazgo | Área | Certeza | Tratamiento |
|---|---|---|---|---|
| [{{H-SEG-01}}](./{{documento}}) | {{titulo}} | {{area}} | ✅ | {{MOD-003 o «—»}} |

## Secretos

La extracción enmascaró valores con aspecto de secreto en {{secrets.count}} objetos: `{{objeto 1}}`, `{{objeto 2}}`. Ningún valor aparece en esta documentación. Tratamiento: [{{H-SEG-02}}](./04-seguridad-grupos.md#hallazgos).

## Modernización

**Veredicto:** {{modernization.verdict}}. **Estrategia:** {{modernization.strategy}}.

Diagnóstico y plan en [13](./13-modernizacion-refactor.md), requisitos para reconstruirla en [12](./12-especificacion-reconstruccion.md) y diseño objetivo en [14](./14-diseno-objetivo.md).

## Uso real

{{Los 3-5 procesos más ejecutados (usage: nombre, ejecuciones, última ejecución; fallos «en las últimas N» si hay failedInSampleOf, con su H-PRO) y N process models sin ejecuciones: `a`, `b` ([H-GEN-NN](./09-valor-adicional.md#hallazgos)). O «La extracción no trae historial de ejecuciones.»}}
{{Si meta.environment.isProduction no es true: la marca «orientativo (ver [LEEME](./LEEME.md))» en la cabecera de la columna de ejecuciones (o tras la cifra, si va en texto), sin más explicación.}}

## Cobertura y límites

{{1-3 líneas: lo que falta y cambia las conclusiones (p. ej. «sin volúmenes de datos», «sin role maps»). La lista completa está en [LEEME](./LEEME.md).}}

Guía de lectura por perfil: [LEEME.md](./LEEME.md).
