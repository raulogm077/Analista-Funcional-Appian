<!--
  Plantilla de 08-procesos-bpmn/indice.md. Este comentario no se copia.
  Sustituye los {{marcadores}} y omite las secciones que queden vacías.
  «Crítico» es criticality.critical del inventario (no se recalcula).
  «Ejecuciones»: si el entorno no consta como producción, «orientativo (ver LEEME)» en la cabecera, sin más explicación.
  Hallazgos: los de cada proceso están en su documento y el catálogo los cita; aquí solo los que afectan a varios.
  Evidencia: siempre enlazada a la ficha del proceso en el anexo (../anexo/processModel/<slug>.md).
  «Cobertura y límites»: solo lo de este documento; lo global está en LEEME.
  «Vista»: solo si algún proceso lanza a otro (subproceso o a!startProcess). Si ninguno lo hace, no hay mapa: se omite la
  sección y el TL;DR lo dice («ningún proceso lanza a otro»).
-->

# Procesos — índice

> **Responde a:** ¿Qué procesos hay y cómo empieza cada uno? ¿Qué proceso lanza a cuál? ¿Cuáles son críticos? ¿Cuántas veces se ejecuta cada uno?

> **TL;DR**: {{qué procesos sostienen el negocio, cuáles son críticos y lo más importante que hay que saber de ellos}}{{. Sin mapa: «Ningún proceso lanza a otro»}}.
> **Volumen**: {{N}} process models ({{n}} los inicia una persona, {{n}} un temporizador, {{n}} solo como subproceso, {{n}} sin invocador detectado). **Hallazgos**: {{5 (Alta: 1) — principales: [H-PRO-01](./slug.md#hallazgos)}} o «sin hallazgos».

## Vista: mapa de procesos

{{Una frase: qué proceso lanza a cuál (subprocesos y `a!startProcess`) y desde dónde se inicia cada uno.}}

![Mapa de procesos](../diagrams/mapa-procesos.svg)

Fuente: [mapa-procesos.mmd](../diagrams/mapa-procesos.mmd)

## Detalle: catálogo

| Proceso | Inicio | Crítico | Ejecuciones{{, orientativo (ver [LEEME](../LEEME.md))}} | Invocado por | Subprocesos e integraciones | Hallazgos | BPMN |
|---|---|---|---|---|---|---|---|
| [{{nombre}}](./{{slug}}.md) | Formulario de inicio | Sí | 120 | [`{{interfaz}}`](../10-pantallas.md#{{ancla}}) | [{{hijo}}](./{{slug-hijo}}.md), `{{integración}}` | H-PRO-01, H-PRO-02 | [.bpmn](./{{slug}}.bpmn) |
| [{{nombre}}](./{{slug}}.md) | Temporizador diario | No | 0 | — | — | — | [.bpmn](./{{slug}}.bpmn) |

### Cómo leer los diagramas

Cada proceso tiene su imagen (`.png`), su `.drawio` (se abre y se edita en draw.io) y su `.bpmn` (para Camunda Modeler o bpmn.io). Su `.json` es la descripción del dibujo que mantiene la herramienta: no se edita a mano. Los dibujos usan la notación BPMN:

| Forma | Significa |
|---|---|
| Círculo fino verde (con reloj: temporizador; con sobre: mensaje) | Inicio |
| Círculo grueso rojo | Fin |
| Caja con una persona | Tarea de una persona |
| Caja con engranajes · con un pergamino | Tarea automática (datos, integración) · script |
| Caja de borde grueso | Llamada a otro proceso (tiene su propio documento) |
| Círculo doble con un sobre | Correo o aviso que se envía |
| Círculo doble con un reloj · con un rayo, unido a una tarea | Plazo de la tarea · error que la interrumpe |
| Rombo con una X | Decisión |
| Franja gris debajo de los carriles | Sistema externo |
| Círculo doble con una flecha (blanca: entra; azul: sale) | El proceso sigue en otro tramo (proceso en varias imágenes) |

## Hallazgos

| ID | Hallazgo | Severidad | Certeza | Evidencia |
|---|---|---|---|---|
| H-PRO-01 | {{qué pasa y qué riesgo tiene}} | {{Alta/Media/Baja}} | {{✅/🔶/❓}} | [`mcp:processModel/{{nombre}}#nodes[id={{N}}]`](../anexo/processModel/{{slug}}.md) |

## Cobertura y límites

- Excepciones, alertas y escalados de los nodos: la extracción no los devuelve ([LEEME](../LEEME.md)); cada proceso dice dónde importa ❓.
- {{Uso real: una línea con lo que la muestra no permite concluir en estos procesos; el entorno y la muestra, en [LEEME](../LEEME.md).}}
- {{Diagramas sin imagen (no había navegador al dibujarlos; se ven abriendo el .drawio en draw.io): lista de procesos}}.
- {{Diagramas en tramos por no caber en una página: lista de procesos (su `.bpmn` está completo)}}.
