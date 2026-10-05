<!--
  Plantilla de 08-procesos-bpmn/indice.md. Este comentario no se copia.
  Sustituye los {{marcadores}} y omite las secciones que queden vacías.
  «Crítico» es criticality.critical del inventario (no se recalcula).
-->

# Procesos — índice

> **TL;DR**: {{qué procesos sostienen el negocio, cuáles son críticos y lo más importante que hay que saber de ellos}}.
> **Volumen**: {{N}} process models ({{n}} los inicia una persona, {{n}} un temporizador, {{n}} solo como subproceso, {{n}} sin invocador detectado). **Hallazgos**: {{5 (Alta: 1) — principales: [H-PRO-01](./slug.md#hallazgos)}} o «sin hallazgos».

## Vista: mapa de procesos

{{Una frase: qué proceso lanza a cuál (subprocesos y `a!startProcess`) y desde dónde se inicia cada uno.}}

![Mapa de procesos](../diagrams/mapa-procesos.svg)

Fuente: [mapa-procesos.mmd](../diagrams/mapa-procesos.mmd)

## Detalle: catálogo

Cada proceso tiene su documento (paso a paso, tareas, datos y hallazgos) y su diagrama BPMN 2.0 (`.bpmn`), que se abre en Camunda Modeler o en bpmn.io.

| Proceso | Inicio | Crítico | Ejecuciones | Invocado por | Subprocesos e integraciones | Hallazgos | BPMN |
|---|---|---|---|---|---|---|---|
| [{{nombre}}](./{{slug}}.md) | Formulario de inicio | Sí | 120 | [`{{interfaz}}`](../10-pantallas.md#ancla) | [{{hijo}}](./slug-hijo.md), `{{integración}}` | H-PRO-01, H-PRO-02 | [.bpmn](./{{slug}}.bpmn) |
| [{{nombre}}](./{{slug}}.md) | Temporizador diario | No | 0 | — | — | — | [.bpmn](./{{slug}}.bpmn) |

### Cómo leer los diagramas

{{Solo si los diagramas son los .svg de la vía propia; los .png de draw.io usan la notación BPMN estándar.}}

{{Vía draw.io: «Cada proceso tiene su `.drawio` (se abre y se edita en draw.io), su `.png` (la imagen del documento), su `.json` (la descripción del dibujo que mantiene la herramienta; no se edita a mano) y su `.bpmn` (para Camunda Modeler o bpmn.io).»}}

| Forma | Significa |
|---|---|
| Círculo verde (⏰ temporizador, ✉ mensaje) | Inicio |
| 👤 caja amarilla | Tarea de una persona |
| 📜 gris · 📋 o 💾 azul · 🔌 azul | Script · escritura de datos · llamada a una integración |
| 📧 caja violeta | Correo |
| ➡️ caja verde | Subproceso (tiene su propio documento) |
| Rombo amarillo | Decisión |
| Círculo doble (⊗ si termina el proceso entero) | Fin |
| Caja discontinua gris | Sistema externo |

## Hallazgos

{{Los de cada proceso están en su documento y el catálogo los cita. Aquí solo los que afectan a varios procesos.}}

| ID | Hallazgo | Severidad | Certeza | Evidencia |
|---|---|---|---|---|
| H-PRO-01 | {{qué hay que corregir, decidir o vigilar}} | {{Alta/Media/Baja}} | {{✅/🔵/❓}} | `mcp:processModel/{{nombre}}#nodes[id={{N}}]` |

## Cobertura y límites

- Excepciones, alertas y escalados de los nodos: la extracción no los devuelve ([LEEME](../LEEME.md)); cada proceso dice dónde importa ❓.
- {{Uso real: una línea con lo que la muestra no permite concluir en estos procesos; el entorno y la muestra, en [LEEME](../LEEME.md).}}
- {{Diagramas sin imagen (se muestra el bloque mermaid): lista de procesos}}.
