<!--
  Plantilla de 08-procesos-bpmn/<slug>.md, uno por process model. Este comentario no se copia.
  Sustituye los {{marcadores}} y omite las filas y secciones que queden vacías.
  Diagrama: la variante de la vía con la que se dibujó (vía propia: .svg + .mmd; vía draw.io: .png + .drawio).
  Sin imagen renderizada: el bloque mermaid del .mmd en lugar de la imagen.
  Más de 25 nodos (vía propia): una imagen por tramo (<slug>-1.svg, <slug>-2.svg…), en orden, cada una con una frase
  que dice qué pasos cubre y su «Fuente: [<slug>-N.mmd]»; el enlace al .bpmn (uno, completo) va una sola vez.
  Ejecuciones: si el entorno no consta como producción, la marca «orientativo (ver LEEME)» (../LEEME.md), sin más
  explicación. Instancias fallidas o detenidas de la muestra: hallazgo H-PRO de este proceso. Sin ejecuciones: el
  hallazgo es el H-GEN de 09; aquí se cita.
  Usuarios: una asignación o un destinatario que es un usuario o una constante de tipo Usuario: «una cuenta de
  ‹grupo›» o «una cuenta personal»; un correo personal: ‹correo›.
  Evidencia: siempre enlazada a la ficha del proceso en el anexo (../anexo/processModel/<slug>.md).
-->

# {{nombre del process model}}

> **TL;DR**: {{qué resultado de negocio produce, quién lo inicia y cómo (formulario, acción de record, temporizador, subproceso) y qué deja escrito o a quién avisa}}.
> **Volumen**: {{N}} nodos ({{n}} tareas de personas, {{n}} automáticas, {{n}} pasarelas) · {{«120 ejecuciones, última el 2026-09-30» o «sin ejecuciones registradas» ([H-GEN-NN](../09-valor-adicional.md#hallazgos))}}{{, orientativo (ver [LEEME](../LEEME.md))}}. **Hallazgos**: {{2 (Alta: 1) — principales: [H-PRO-01](#hallazgos)}} o «sin hallazgos».

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
| Inicio | {{formulario [`interfaz`](../10-pantallas.md#{{ancla}}) · acción de record · temporizador · subproceso}} |
| Frecuencia | {{solo con temporizador: «cada día a las 08:00 (Europe/Madrid)»}} |
| Quién puede iniciarlo | {{grupos según el role map, o «grupo de seguridad declarado: X; role map no disponible» ❓}} |
| Carriles | {{grupos asignados}} · Sistema |
| Lo invocan | {{[proceso padre](./slug-padre.md), interfaz, acción de record}} o «sin invocador detectado» |
| Subprocesos | {{[proceso hijo](./{{slug-hijo}}.md)}} |
| Sistemas externos | {{sistema}} vía [`{{integración}}`](../05-integraciones-consumidas.md#{{ancla}}) |
| Datos que escribe | [`{{record type}}`](../03-modelo-datos.md#{{ancla}}) |
| Crítico | {{Sí/No}} ({{motivos de la criticidad}}) |
| Definición | [`mcp:processModel/{{nombre}}`](../anexo/processModel/{{slug}}.md) · Certeza: ✅ |

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
| {{nombre}} | grupo `{{grupo}}` · {{rol de la expresión}} 🔵 | [`{{interfaz}}`](../10-pantallas.md#{{ancla}}) | [`mcp:processModel/{{nombre}}#nodes[id={{N}}].assignment`](../anexo/processModel/{{slug}}.md) |

### Datos, integraciones y avisos

| Nodo | Acción | Objeto | Evidencia |
|---|---|---|---|
| {{nombre}} | Escribe | [`{{record type}}`](../03-modelo-datos.md#{{ancla}}) | [`mcp:processModel/{{nombre}}#nodes[id={{N}}].data`](../anexo/processModel/{{slug}}.md) |
| {{nombre}} | Llama | [`{{integración}}`](../05-integraciones-consumidas.md#{{ancla}}) | [`mcp:processModel/{{nombre}}#nodes[id={{N}}].data`](../anexo/processModel/{{slug}}.md) |
| {{nombre}} | Envía correo | destinatarios ❓ (no los devuelve la extracción) | [`mcp:processModel/{{nombre}}#nodes[id={{N}}]`](../anexo/processModel/{{slug}}.md) |
| {{nombre}} | Lanza subproceso | [{{proceso hijo}}](./{{slug-hijo}}.md) | [`mcp:processModel/{{nombre}}#nodes[id={{N}}].data`](../anexo/processModel/{{slug}}.md) |

### Parámetros

{{Solo si el proceso recibe datos de quien lo lanza.}}

| Variable | Tipo | Para qué |
|---|---|---|
| `{{variable}}` | {{tipo}} | {{qué lleva}} |

## Hallazgos

| ID | Hallazgo | Severidad | Certeza | Evidencia |
|---|---|---|---|---|
| H-PRO-01 | {{qué hay que corregir, decidir o vigilar}} | {{Alta/Media/Baja}} | {{✅/🔵/❓}} | [`mcp:processModel/{{nombre}}#nodes[id={{N}}]`](../anexo/processModel/{{slug}}.md) |

{{Para un hallazgo Alta: una línea con su impacto y la recomendación.}}

{{Lo que corresponde a otra área: una frase sin severidad con el enlace a su documento.}}

## Cobertura y límites

- {{Datos no devueltos que cambian lo que dice este proceso: p. ej. «sin la pestaña de excepciones de Notificar ERP, no se sabe si un fallo detiene el proceso», destinatarios de correo, entradas de un nodo}} ❓.
- {{Ejecuciones: solo lo propio de este proceso (fallos en la muestra con su H-PRO, ninguna ejecución con el H-GEN de 09). Si es de temporizador o subproceso, se ejecuta como el usuario que desplegó el modelo.}}
{{Lo global (entorno, versión, muestra de ejecuciones, configuración que el Dev MCP no devuelve) está en LEEME: no lo repitas.}}
