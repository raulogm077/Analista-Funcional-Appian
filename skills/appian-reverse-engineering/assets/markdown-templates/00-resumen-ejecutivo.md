<!--
  Plantilla 00 — Resumen ejecutivo (orquestador, fase 6, después de la pasada de coherencia).
  Fuente única de cifras: <trabajo>/summary.json (build_summary.py, ejecutado después de build_registry.py).
  No recalcules ni copies cifras de otros documentos: si summary.json contradice un documento, corrige el
  documento en la pasada de coherencia y vuelve a generar summary.json.
  Objetivo 1-2 pantallas, máximo 3. Sin usuarios. Las secciones sin datos se omiten.

  De dónde sale cada dato:
    Confianza ........... meta.confidence + meta.confidenceBasis (unidos por «; »)
    Entorno ............. meta.environment {url, isProduction, appianVersion}; fecha: meta.source.extractedAt
    Cifras .............. counts, totals, layerBreakdown
    Procesos críticos ... criticalProcesses (ya ordenados; máx. 5). Enlace: slug de objects.processModel
    Hallazgos ........... findingsBySeverity, findingsByCertainty y findings de severidad Alta
                          (si no hay Alta: los Media, máx. 5, y dilo en el TL;DR)
    Secretos ............ secrets {count, objects}; tratamiento: los H-SEG de findings
    Modernización ....... modernization {verdict, strategy} (vienen de 13; si son null, falta
                          <trabajo>/modernizacion.json: corrígelo antes de escribir 00)
    Uso real ............ usage (top por ejecuciones; failedInSampleOf = fallos en una muestra) y signals[type=processModelsWithoutExecutions]
  Certeza: verificado ✅ · inferido 🔵 · pendiente ❓. En 00 los hallazgos se citan por ID, sin columna de severidad.
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

| Capa | Objetos | Qué incluye | Dónde |
|---|---|---|---|
| Presentación | {{layerBreakdown.Presentacion}} | {{n}} sites, {{n}} interfaces | [10](./10-pantallas.md) |
| Lógica | {{layerBreakdown.Logica}} | {{n}} process models ({{n}} programados), {{n}} reglas, {{n}} decisiones | [08](./08-procesos-bpmn/indice.md), [11](./11-reglas-negocio.md) |
| Datos | {{layerBreakdown.Datos}} | {{n}} record types, {{n}} CDTs | [03](./03-modelo-datos.md) |
| Integración | {{layerBreakdown.Integracion}} | {{n}} integraciones, {{n}} connected systems, {{n}} Web APIs | [05](./05-integraciones-consumidas.md), [06](./06-apis-expuestas.md) |
| Seguridad | {{layerBreakdown.Seguridad}} | {{n}} grupos | [04](./04-seguridad-grupos.md) |

{{totals.withDefinition}} de {{totals.objects}} objetos con definición ([INVENTARIO](./INVENTARIO.md)) · {{totals.hubs}} objetos muy reutilizados y {{totals.orphans}} sin referencias ([02](./02-arquitectura.md)).

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

{{Si meta.environment.isProduction no es true: «El entorno {{no es de producción / no consta como producción}}: las ejecuciones son orientativas y no sirven para decidir qué se usa.»}}
{{Los 3-5 procesos más ejecutados (usage: nombre, ejecuciones, última ejecución; fallos «en las últimas N» si hay failedInSampleOf) y N process models sin ejecuciones: `a`, `b`. O «La extracción no trae historial de ejecuciones.»}}

## Cobertura y límites

{{1-3 líneas: lo que falta y cambia las conclusiones (p. ej. «sin volúmenes de datos», «sin role maps»). La lista completa está en [LEEME](./LEEME.md).}}

Guía de lectura por perfil: [LEEME.md](./LEEME.md).
