<!--
  Plantilla 07 — Procesos programados (orquestador, paso 4.3).
  Qué analizar y criterios de los hallazgos: references/analysis-workflow.md, «Guía de 07».
  Proceso programado = process model con inicio por temporizador (`startType: timer` en el inventario).
  Sin procesos programados, el documento es solo el título y esta línea:
    > **TL;DR**: La aplicación no tiene procesos programados: ningún process model se inicia por temporizador.
  Hallazgos: solo H-BAT, en la tabla de Hallazgos y en <trabajo>/hallazgos/orquestador.json. La severidad
  solo aparece en esa tabla; en las fichas se cita el ID. Un proceso sin ejecuciones es H-GEN (09) y los fallos
  de la muestra de ejecuciones son H-PRO (08): aquí se citan por su ID.
  Si el entorno no consta como producción, las ejecuciones llevan la marca «orientativo (ver LEEME)», sin más explicación.
-->

# Procesos programados

> **TL;DR**: {{N}} process models se lanzan solos por temporizador: {{resumen de frecuencias, p. ej. «uno diario y uno cada hora»}}. {{Lo más importante: qué mantienen al día o el hallazgo principal}}.
> **Volumen**: {{N}} procesos programados · {{N}} ejecuciones registradas{{, orientativo (ver [LEEME](./LEEME.md))}}. **Hallazgos**: {{N (Alta: n)}} — principales: [H-BAT-01](#hallazgos), … (o «sin hallazgos»).

## Vista

| Proceso | Frecuencia | Zona horaria | Próxima ejecución | Ejecuciones{{, orientativo (ver [LEEME](./LEEME.md))}} | Última | Certeza |
|---|---|---|---|---|---|---|
| [`{{nombre}}`](#{{ancla-de-la-ficha}}) | {{Cada lunes a las 08:00}} | {{Europe/Madrid}} | {{2026-10-06 08:00}} | {{N o «—»}} | {{AAAA-MM-DD o «—»}} | ✅ |

## Detalle

La zona horaria de una recurrencia es la que fija el temporizador; por defecto, la del process model (`pp!timezone`). Fuente: https://docs.appian.com/suite/help/26.6/Intermediate_Event_-_Timer.html#configuring-the-time-zone-used

Un proceso que arranca un temporizador se ejecuta con la cuenta del usuario que desplegó el process model. Fuente: https://docs.appian.com/suite/help/26.6/Testing_and_Debugging_Problems_with_Process_Models.html#issues-that-return-process-errors

### {{nombre técnico}} — {{nombre visible}}

{{1 línea: qué hace y para qué}}. Proceso completo: [08-procesos-bpmn/{{slug}}.md](./08-procesos-bpmn/{{slug}}.md).

| Campo | Valor |
|---|---|
| Frecuencia | {{configuración del temporizador en lenguaje natural}} |
| Zona horaria | {{la del temporizador, la del process model si usa `pp!timezone`, o ❓ si no consta}} |
| Cron equivalente | `{{0 8 * * 1}}` o «no traducible: {{motivo}}» |
| Próximas 3 ejecuciones | {{fecha hora; fecha hora; fecha hora}} (desde la extracción, {{AAAA-MM-DD}}, en {{zona}}) |
| Cuenta de ejecución | {{la de quien desplegó el modelo: «cuenta de servicio del grupo X», o ❓ si no consta}} |
| Uso real | {{N ejecuciones, última AAAA-MM-DD; «3 fallos en las últimas 50 ejecuciones» ([H-PRO-NN](./08-procesos-bpmn/{{slug}}.md#hallazgos)); sin ejecuciones: [H-GEN-NN](./09-valor-adicional.md#hallazgos)}} |
| Qué toca | {{records que lee o escribe, integraciones y subprocesos, con enlace a su ficha}} |
| Volumen por ejecución | {{consulta de origen y tamaño de lote (`batchSize`), o ❓ si la definición no lo muestra}} |
| Manejo de errores | {{lo que muestre la definición, o ❓ «no lo devuelve la extracción»}} |
| Hallazgos | {{H-BAT-01, … (omite la fila si no tiene)}} |

Evidencia: [`mcp:processModel/{{nombre}}#nodes[id={{N}}]`](./anexo/processModel/{{slug}}.md) · Certeza: ✅/🔵/❓

## Hallazgos

| ID | Hallazgo | Severidad | Certeza | Evidencia |
|---|---|---|---|---|
| H-BAT-01 | {{Lee todos los registros en cada ejecución, sin tamaño de lote}} | {{Alta/Media/Baja}} | ✅ | [`mcp:processModel/{{nombre}}#nodes[id={{N}}].data`](./anexo/processModel/{{slug}}.md) |

## Cobertura y límites

{{1-5 líneas: p. ej. «sin historial de ejecuciones de DEM_Batch_X», «la consulta no fija lote: el volumen real por ejecución es ❓». Lo global (entorno, versión, muestra de ejecuciones, configuración que el Dev MCP no devuelve) está en LEEME: no lo repitas.}}
