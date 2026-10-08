<!--
  Plantilla 01 — Explicación funcional (agente interface-analyzer). Borra estos comentarios en el documento final.
  Lenguaje de negocio: sin jerga Appian salvo en las filas «Implementado en» y en la evidencia.
  Comportamiento que es defecto de otra área (procesos, pantallas, datos, seguridad): se describe en lenguaje de
  negocio, sin severidad, con enlace al documento propietario. Aquí solo hay hallazgos H-FUN.
  Diagrama: si existe el .svg, imagen + «Fuente»; si no, en su lugar, el bloque mermaid idéntico al .mmd
  (flowchart TD, ≤ 10 nodos).
  Secciones sin contenido: se omiten. Fichas: todas con los mismos campos; un campo que no aplica a ningún caso
  de uso se quita de todas (y, si es un dato que falta, se dice en «Cobertura y límites»).
  Longitud: 1 pantalla + ½ por caso de uso. Ningún caso de uso se recorta ni se omite; con más de ~15, el Detalle se
  parte por área (`## Detalle: <área>`) con un índice de áreas tras la Vista.
  Uso real: si el entorno no consta como producción, la marca «orientativo (ver LEEME)» en la cabecera de la columna.
  Evidencia: siempre enlazada a la ficha del objeto en el anexo. La de un caso de uso, su punto de entrada; la de un
  actor, de donde sale (role map, asignación de tareas, visibilidad de páginas o expresión de seguridad).
  «Cobertura y límites»: solo lo de este documento; lo global está en LEEME.
-->

# Explicación funcional

> **Responde a:** ¿Qué hace la aplicación y para quién? ¿Cómo empieza cada caso de uso y qué consigue? ¿Qué pasos sigue cada caso de uso? ¿Quién hace qué en la aplicación?

> **TL;DR**: {{2-3 frases: qué problema de negocio resuelve la aplicación, para quién y cuál es su caso de uso central}}.
> **Volumen**: {{N}} casos de uso, {{N}} actores, {{N}} puntos de entrada ({{n}} páginas, {{n}} acciones, {{n}} automáticos). **Hallazgos**: {{N (Alta: n)}} — principales: [H-FUN-01](#hallazgos) (o «sin hallazgos»).

## Vista

{{Una frase: qué muestra el diagrama, p. ej. «Quién inicia cada caso de uso y qué obtiene».}}

![{{qué muestra}}](diagrams/flujo-general.svg)

Fuente: [flujo-general.mmd](diagrams/flujo-general.mmd)

### Casos de uso

| Caso de uso | Quién lo inicia | Cómo empieza | Uso real | Certeza | Evidencia |
|---|---|---|---|---|---|
| [{{Registrar solicitud}}](#{{ancla}}) | {{Gestor}} | {{Botón «Nueva solicitud» del listado}} | {{N ejecuciones, última dd/mm/aaaa}} | ✅ | [`mcp:recordType/{{DEM Solicitud}}#actions[{{0}}]`](./anexo/recordType/{{slug}}.md) |
| [{{Revisión diaria}}](#{{ancla}}) | Sistema | {{Automático, cada día a las 06:00}} | {{N ejecuciones}} | 🔶 | [`mcp:processModel/{{DEM Revisión}}#nodes[id={{1}}]`](./anexo/processModel/{{slug}}.md) |

### Actores

| Actor | Grupos | Qué hace en la aplicación | Certeza | Evidencia |
|---|---|---|---|---|
| {{Gestor}} | `{{grupo}}` ([04](./04-seguridad-grupos.md)) | {{Registra solicitudes y consulta su estado}} | ✅ | [`mcp:processModel/{{DEM Alta Solicitud}}#nodes[id={{3}}].assignment`](./anexo/processModel/{{slug}}.md) |
| Sistema | — | {{Revisa a diario las solicitudes pendientes}} | ✅ | [`mcp:processModel/{{DEM Revisión}}#nodes[id={{1}}]`](./anexo/processModel/{{slug}}.md) |

## Detalle

<!-- Índice si hay más de 5 casos de uso: - [Registrar solicitud](#registrar-solicitud) · … -->

### {{Registrar solicitud}}

{{1 línea: qué consigue el negocio con este caso de uso.}}

| Campo | Valor |
|---|---|
| Quién lo inicia | {{Gestor}} |
| Cómo lo inicia | {{Página «Solicitudes» del portal de gestión → botón «Nueva solicitud»}} |
| Resultados y avisos | {{Correo al solicitante · tarea de revisión para el revisor}} |
| Uso real | {{N ejecuciones, última dd/mm/aaaa}} |
| Implementado en | {{Site `X` → página `Y` · acción `Z` de `Record` · proceso `PM` · interfaz `IF`}} |

**Paso a paso**

1. {{El gestor rellena el formulario con el título y el importe.}}
2. {{Si el importe supera 1.000 €, la solicitud va a aprobación del director; si no, se registra directamente.}}
3. {{El sistema guarda la solicitud y avisa al solicitante.}}

**A tener en cuenta**

- {{Comportamiento actual relevante, en lenguaje de negocio, p. ej. «Cancelar en el formulario no anula el alta: la solicitud se registra igualmente» ([proceso](./08-procesos-bpmn/{{slug}}.md)).}}

Evidencia: [`mcp:{{tipo}}/{{nombre}}#{{ubicación}}`](./anexo/{{tipo}}/{{slug}}.md) · Certeza: ✅/🔶/❓

### {{Siguiente caso de uso}}

{{Misma ficha, con los mismos campos y en el mismo orden.}}

## Hallazgos

| ID | Hallazgo | Severidad | Certeza | Evidencia |
|---|---|---|---|---|
| H-FUN-01 | {{Las solicitudes no se pueden anular aunque existe el estado «Anulada»}} | Media | 🔶 | [`mcp:{{tipo}}/{{nombre}}#{{ubicación}}`](./anexo/{{tipo}}/{{slug}}.md) |

{{Para cada hallazgo ❓: la pregunta que lo resuelve y a quién hacerla.}}

## Cobertura y límites

- {{Qué no se pudo obtener o verificar en este documento y por qué, p. ej. «Sin historial de ejecuciones: el uso real no se puede medir» o «Role map no disponible: actores deducidos de tareas y visibilidad de páginas».}}
