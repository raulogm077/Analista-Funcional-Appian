<!--
  Plantilla de 08-procesos-bpmn/<slug>.md, uno por process model. Este comentario no se copia.
  Sustituye los {{marcadores}} y omite las filas y secciones que queden vacías.
  Diagrama: la variante de la vía con la que se dibujó (vía propia: .svg + .mmd; vía draw.io: .png + .drawio).
  Sin imagen renderizada: el bloque mermaid del .mmd en lugar de la imagen.
-->

# {{nombre del process model}}

> **TL;DR**: {{qué resultado de negocio produce, quién lo inicia y cómo (formulario, acción de record, temporizador, subproceso) y qué deja escrito o a quién avisa}}.
> **Volumen**: {{N}} nodos ({{n}} tareas de personas, {{n}} automáticas, {{n}} pasarelas) · {{«120 ejecuciones, última el 2026-09-30» o «sin ejecuciones registradas»}}. **Hallazgos**: {{2 (Alta: 1) — principales: [H-PRO-01](#hallazgos)}} o «sin hallazgos».

## Vista

{{Una frase: qué muestra el diagrama (carriles, decisiones principales).}}

![Diagrama del proceso {{nombre}}](./{{slug}}.svg)

Fuente: [{{slug}}.mmd](./{{slug}}.mmd) · BPMN 2.0: [{{slug}}.bpmn](./{{slug}}.bpmn) (se abre en Camunda Modeler o en bpmn.io)

<!-- Vía draw.io, en lugar de las dos líneas anteriores:
![Diagrama del proceso {{nombre}}](./{{slug}}.png)

Fuente editable: [{{slug}}.drawio](./{{slug}}.drawio) (draw.io) · BPMN 2.0: [{{slug}}.bpmn](./{{slug}}.bpmn) (se abre en Camunda Modeler o en bpmn.io)
-->

| Atributo | Valor |
|---|---|
| Inicio | {{formulario [`interfaz`](../10-pantallas.md#ancla) · acción de record · temporizador · subproceso}} |
| Frecuencia | {{solo con temporizador: «cada día a las 08:00 (Europe/Madrid)»}} |
| Quién puede iniciarlo | {{grupos según el role map, o «grupo de seguridad declarado: X; role map no disponible» ❓}} |
| Carriles | {{grupos asignados}} · Sistema |
| Lo invocan | {{[proceso padre](./slug-padre.md), interfaz, acción de record}} o «sin invocador detectado» |
| Subprocesos | {{[proceso hijo](./slug-hijo.md)}} |
| Sistemas externos | {{sistema}} vía [`{{integración}}`](../05-integraciones-consumidas.md#ancla) |
| Datos que escribe | [`{{record type}}`](../03-modelo-datos.md#ancla) |
| Crítico | {{Sí/No}} ({{motivos de la criticidad}}) |
| Definición | [anexo](../anexo/processModel/{{slug}}.md) · Evidencia: `mcp:processModel/{{nombre}}` · Certeza: ✅ |

## Detalle

### Paso a paso

{{Lenguaje de negocio. Cada paso cita su nodo; en la vía draw.io, también su código (ACT-01, GW-01, EV-01).}}

1. **{{Qué pasa}}** — {{inicio · tarea de `grupo` · tarea automática · fin}}, `nodes[id={{N}}]`.
2. **{{¿Pregunta de la decisión?}}** — pasarela, `nodes[id={{N}}]`:
   - {{condición}} → paso {{n}}.
   - En otro caso → paso {{n}}.
3. **{{Qué pasa}}** — {{…}}, `nodes[id={{N}}]`.

### Tareas de personas

| Tarea | Asignada a | Formulario | Evidencia |
|---|---|---|---|
| {{nombre}} | grupo `{{grupo}}` · {{rol de la expresión}} 🔵 | [`{{interfaz}}`](../10-pantallas.md#ancla) | `mcp:processModel/{{nombre}}#nodes[id={{N}}].assignment` |

### Datos, integraciones y avisos

| Nodo | Acción | Objeto | Evidencia |
|---|---|---|---|
| {{nombre}} | Escribe | [`{{record type}}`](../03-modelo-datos.md#ancla) | `mcp:processModel/{{nombre}}#nodes[id={{N}}].data` |
| {{nombre}} | Llama | [`{{integración}}`](../05-integraciones-consumidas.md#ancla) | `mcp:processModel/{{nombre}}#nodes[id={{N}}].data` |
| {{nombre}} | Envía correo | destinatarios ❓ (no los devuelve la extracción) | `mcp:processModel/{{nombre}}#nodes[id={{N}}]` |
| {{nombre}} | Lanza subproceso | [{{proceso hijo}}](./slug-hijo.md) | `mcp:processModel/{{nombre}}#nodes[id={{N}}].data` |

### Parámetros

{{Solo si el proceso recibe datos de quien lo lanza.}}

| Variable | Tipo | Para qué |
|---|---|---|
| `{{variable}}` | {{tipo}} | {{qué lleva}} |

## Hallazgos

| ID | Hallazgo | Severidad | Certeza | Evidencia |
|---|---|---|---|---|
| H-PRO-01 | {{qué hay que corregir, decidir o vigilar}} | {{Alta/Media/Baja}} | {{✅/🔵/❓}} | `mcp:processModel/{{nombre}}#nodes[id={{N}}]` |

{{Para un hallazgo Alta: una línea con su impacto y la recomendación.}}

{{Lo que corresponde a otra área: una frase sin severidad con el enlace a su documento.}}

## Cobertura y límites

- {{Datos no devueltos que cambian lo que dice este proceso: p. ej. «sin la pestaña de excepciones de Notificar ERP, no se sabe si un fallo detiene el proceso», destinatarios de correo, entradas de un nodo}} ❓.
- {{Ejecuciones: solo lo propio de este proceso (fallos en la muestra, ninguna ejecución). Si es de temporizador o subproceso, se ejecuta como el usuario que desplegó el modelo.}}
{{Lo global (entorno, versión, muestra de ejecuciones, configuración que el Dev MCP no devuelve) está en LEEME: no lo repitas.}}
