<!--
  Plantilla 09 — Información de valor adicional (orquestador, paso 4.3).
  Qué analizar y criterios de los hallazgos: references/analysis-workflow.md, «Guía de 09».
  Datos: inventory.json, graph.json y summary.json (`signals`) de <trabajo>.
  Propiedad: aquí solo se registran hallazgos H-GEN (mantenimiento, validación de la plataforma, versionado,
  métricas, uso). Secretos (H-SEG, 04), hubs y huérfanos (H-ARQ, 02) y el resto de áreas se enlazan por su ID,
  sin severidad.
  El registro de hallazgos lo escribe build_registry.py entre los dos marcadores: no los cambies ni escribas
  dentro. Omite las subsecciones del Detalle sin contenido (y su entrada del índice).
  Sin usuarios: el versionado da fechas, recuentos y tipo de cuenta.
-->

# Información de valor adicional

> **TL;DR**: {{Lo más útil para quien mantiene la aplicación, p. ej. «12 constantes dependen del entorno, 3 objetos tienen avisos de la plataforma y 5 son candidatos a retirar»}}.
> **Volumen**: {{N}} objetos · {{N}} líneas de expresiones · {{N}} hallazgos en el registro (Alta: {{n}}). **Hallazgos propios**: {{N (Alta: n)}} — principales: [H-GEN-01](#hallazgos), … (o «sin hallazgos»).

## Vista: métricas de la aplicación

| Métrica | Valor |
|---|---|
| Objetos (con definición) | {{N}} ({{N}}) |
| Líneas de expresiones (interfaces, reglas, integraciones, Web APIs) | {{N}} |
| Process models con más de 50 nodos (el mayor tiene {{N}}) | {{N}} |
| Expression rules de más de 200 líneas | {{N}} |
| Interfaces de más de 80 KB de expresión | {{N}} |
| Objetos con avisos de validación de la plataforma | {{N}} |
| Process models sin ejecuciones | {{N}}{{ (orientativo: el entorno no consta como producción)}} |

Appian recomienda dividir en subprocesos los process models de más de 50 nodos. Fuente: https://docs.appian.com/suite/help/26.6/appian-recommendations.html#process-model-design-guidance

## Detalle

- [Constantes por entorno y secretos](#constantes-por-entorno-y-secretos)
- [Reglas reutilizables](#reglas-reutilizables)
- [Objetos huérfanos](#objetos-huérfanos)
- [Avisos de validación de la plataforma](#avisos-de-validación-de-la-plataforma)
- [Versionado](#versionado)
- [Glosario de negocio](#glosario-de-negocio)

### Constantes por entorno y secretos

Constantes cuyo valor depende del entorno (URLs, hosts, identificadores, interruptores). Solo se ve el valor de este entorno: los de los demás van en el fichero de personalización del paquete de despliegue, que la extracción no trae.

| Constante | Tipo | Valor en este entorno | Usada por | Certeza |
|---|---|---|---|---|
| `{{constante}}` | {{Texto}} | `{{valor sin credenciales}}` | {{N}} objetos | 🔵 |

La extracción enmascaró valores con aspecto de secreto en {{N}} objetos; su tratamiento está en [{{H-SEG-02}}](./04-seguridad-grupos.md#hallazgos).

### Reglas reutilizables

Expression rules y decisiones que usan 5 o más objetos: un cambio en ellas afecta a todos sus llamadores. Lo que suponen para la arquitectura está en [02](./02-arquitectura.md).

| Regla | Qué hace | Entradas | Devuelve | Llamada por | Ficha |
|---|---|---|---|---|---|
| `{{regla}}` | {{qué calcula}} | `{{ri!a (Texto), ri!b (Número)}}` | {{tipo}} | {{N}} | [anexo](./anexo/expressionRule/{{slug}}.md) |

«Llamada por» cuenta las referencias del grafo de la aplicación: puede ser mayor que lo que muestra la herramienta de dependientes de Appian, porque añade las encontradas en las definiciones.

### Objetos huérfanos

Objetos sin ninguna referencia entrante en la aplicación{{, y process models sin ejecuciones en producción}}. Son candidatos a retirar, no código muerto seguro: pueden usarse desde fuera de la aplicación. El hallazgo de arquitectura es [{{H-ARQ-03}}](./02-arquitectura.md#hallazgos).

| Objeto | Tipo | Última modificación | Ejecuciones | Ficha |
|---|---|---|---|---|
| `{{objeto}}` | {{tipo}} | {{AAAA-MM-DD o «—»}} | {{N; «—» si no es process model}} | [anexo](./anexo/{{tipo}}/{{slug}}.md) |

### Avisos de validación de la plataforma

Avisos que da la propia plataforma al validar el objeto (funciones obsoletas, referencias rotas…).

| Objeto | Tipo | Aviso | Hallazgo |
|---|---|---|---|
| `{{objeto}}` | {{tipo}} | {{texto del aviso, ≤ 100 caracteres}} | {{H-GEN-01}} |

### Versionado

Historial de versiones de los objetos: fechas y recuentos; los autores no se nombran.

| Último autor | Grupo | Objetos | Último cambio |
|---|---|---|---|
| {{Cuenta personal / Cuenta de servicio / Tipo no determinado}} | {{grupo o «—»}} | {{N}} | {{AAAA-MM-DD}} |

Objetos con más versiones:

| Objeto | Tipo | Versiones | Último cambio |
|---|---|---|---|
| `{{objeto}}` | {{tipo}} | {{N}} | {{AAAA-MM-DD}} |

{{N}} objetos cambiados en los últimos 30 días; {{N}} sin cambios desde hace más de un año.

### Glosario de negocio

Vocabulario del negocio que aparece en record types, campos, procesos y pantallas. Los términos de Appian están en [LEEME](./LEEME.md).

| Término | Significado | Dónde aparece | Certeza |
|---|---|---|---|
| {{Expediente}} | {{definición en una frase}} | `{{record type}}`, `{{campo}}` | {{✅ (de la descripción) o 🔵 (del nombre)}} |

## Hallazgos

Mantenimiento, validación de la plataforma, versionado, métricas y uso. Los de las demás áreas están en su documento y en el registro de abajo.

| ID | Hallazgo | Severidad | Certeza | Evidencia |
|---|---|---|---|---|
| H-GEN-01 | {{Función obsoleta en 3 interfaces}} | {{Alta/Media/Baja}} | ✅ | `mcp:interface/{{nombre}}@validation#{{ubicación}}` |

## Registro de hallazgos

Todos los hallazgos de la documentación, de mayor a menor severidad, con el documento que los explica y su tratamiento: la mejora de 13 (`MOD-`) o la pregunta abierta de 12 (`PQ-`).

<!-- registro:inicio -->
(lo rellena build_registry.py)
<!-- registro:fin -->

## Cobertura y límites

{{1-5 líneas: p. ej. «sin historial de versiones para los CDTs», «solo se ven los valores de las constantes de este entorno». Lo global (entorno, versión, muestra de ejecuciones, configuración que el Dev MCP no devuelve) está en LEEME: no lo repitas.}}
