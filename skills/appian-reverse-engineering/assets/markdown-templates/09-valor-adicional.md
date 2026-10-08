<!--
  Plantilla 09 — Información de valor adicional (orquestador, paso 4.3).
  Qué analizar y criterios de los hallazgos: references/analysis-workflow.md, «Guía de 09».
  Datos: inventory.json, graph.json y summary.json (`signals`) de <trabajo>.
  Propiedad: aquí solo se registran hallazgos H-GEN (mantenimiento, validación de la plataforma, versionado,
  métricas, uso). Secretos (H-SEG, 04), hubs y huérfanos (H-ARQ, 02), integraciones (H-INT, 05) y el resto de áreas
  se enlazan por su ID, sin severidad.
  El registro de hallazgos lo escribe build_registry.py entre los dos marcadores: no los cambies ni escribas
  dentro. Omite las subsecciones del Detalle sin contenido (y su entrada del índice).
  Un solo dueño por señal: process models sin ejecuciones → H-GEN (aquí); la lista de objetos huérfanos es solo
  la de este documento (02 tiene el H-ARQ y los demás la enlazan); lo que cambia por entorno está solo aquí (05 lo enlaza).
  Si el entorno no consta como producción, las cifras de uso llevan «orientativo (ver LEEME)», sin más explicación.
  Evidencia: siempre enlazada a la ficha del objeto en el anexo.
  «Cobertura y límites»: solo lo de este documento; lo global está en LEEME.
-->

# Información de valor adicional

> **Responde a:** ¿Qué cambia por entorno? ¿Qué objetos son muy grandes, tienen avisos de la plataforma o no los usa nadie? ¿Quién cambió la aplicación y cuándo? ¿Qué significan los términos del negocio? ¿Qué hallazgos hay en total?

> **TL;DR**: {{Lo más útil para quien mantiene la aplicación, p. ej. «12 constantes dependen del entorno, 3 objetos tienen avisos de la plataforma y 5 no tienen referencias»}}.
> **Volumen**: {{N}} líneas de expresiones · {{N}} hallazgos en el registro (Alta: {{n}}). **Hallazgos propios**: {{N (Alta: n)}} — principales: [H-GEN-01](#hallazgos), … (o «sin hallazgos»).

## Vista: métricas de la aplicación

| Métrica | Valor |
|---|---|
| Líneas de expresiones (interfaces, reglas, integraciones, Web APIs) | {{N}} |
| Process models con más de 50 nodos ([fuente](https://docs.appian.com/suite/help/26.6/appian-recommendations.html#process-model-design-guidance)) | {{N}} (el mayor, `{{nombre}}`, con {{N}}) |
| Expression rules de más de 200 líneas | {{N}} |
| Interfaces de más de 80 KB de expresión | {{N}} |
| Objetos con avisos de validación de la plataforma | {{N}} |
| Process models sin ejecuciones | {{N}}{{, orientativo (ver [LEEME](./LEEME.md))}} |

## Detalle

- [Configuración por entorno](#configuración-por-entorno)
- [Objetos huérfanos](#objetos-huérfanos)
- [Avisos de validación de la plataforma](#avisos-de-validación-de-la-plataforma)
- [Versionado](#versionado)
- [Glosario de negocio](#glosario-de-negocio)

### Configuración por entorno

<!--
  Lo que cambia entre entornos: la URL base y las credenciales de cada connected system, y las constantes con URLs,
  hosts, identificadores o interruptores de entorno (DEV/PRE/PRO). Solo se ve el valor del entorno extraído.
  «Por entorno»: Sí (connected system, o constante marcada «Environment Specific»), No (literal en una expresión o
  constante sin la marca) o ❓ (la definición no lo dice). Certeza: la de que el valor dependa del entorno (🔶 si solo
  lo dice el valor). «Hallazgo»: el H-SEG de 04 si el valor es un secreto; el H-INT de 05 si apunta a otro entorno.
-->

| Objeto | Propiedad | Valor en este entorno | Por entorno | Usado por | Hallazgo | Certeza | Evidencia |
|---|---|---|---|---|---|---|---|
| `{{CS_SAP}}` | URL base | `{{https://sap.example.org/sap/api/v1}}` | Sí | {{2}} integraciones | — | ✅ | [`mcp:connectedSystem/{{CS_SAP}}#baseUrl`](./anexo/connectedSystem/{{slug}}.md) |
| `{{constante}}` | Valor | `{{valor}}` | ❓ | {{N}} objetos | {{[H-INT-01](./05-integraciones-consumidas.md#hallazgos) o «—»}} | 🔶 | [`mcp:constant/{{constante}}#value`](./anexo/constant/{{slug}}.md) |

### Objetos huérfanos

Sin referencias entrantes en la aplicación{{, y process models sin ejecuciones en producción}}; pueden usarse desde fuera de ella. Hallazgo: [{{H-ARQ-02}}](./02-arquitectura.md#hallazgos){{; procesos sin ejecuciones: [H-GEN-NN](#hallazgos)}}.

| Objeto | Tipo | Última modificación | Ejecuciones | Ficha |
|---|---|---|---|---|
| `{{objeto}}` | {{tipo}} | {{AAAA-MM-DD o «—»}} | {{N; «—» si no es process model}} | [anexo](./anexo/{{tipo}}/{{slug}}.md) |

### Avisos de validación de la plataforma

| Objeto | Tipo | Aviso | Hallazgo |
|---|---|---|---|
| `{{objeto}}` | {{tipo}} | {{texto del aviso, ≤ 100 caracteres}} | {{H-GEN-01}} |

### Versionado

| Último autor | Tipo de cuenta | Grupo | Objetos | Último cambio |
|---|---|---|---|---|
| `{{marta.ruiz}}` | {{Cuenta personal / Cuenta de servicio / Tipo no determinado}} | {{grupo o «—»}} | {{N}} | {{AAAA-MM-DD}} |

Objetos con más versiones:

| Objeto | Tipo | Versiones | Último cambio |
|---|---|---|---|
| `{{objeto}}` | {{tipo}} | {{N}} | {{AAAA-MM-DD}} |

{{N}} objetos cambiados en los últimos 30 días; {{N}} sin cambios desde hace más de un año.

### Glosario de negocio

| Término | Significado | Dónde aparece | Certeza | Evidencia |
|---|---|---|---|---|
| {{Expediente}} | {{definición en una frase}} | `{{record type}}`, `{{campo}}` | {{✅ (de la descripción) o 🔶 (del nombre)}} | [`mcp:recordType/{{record type}}#description`](./anexo/recordType/{{slug}}.md) |

## Hallazgos

| ID | Hallazgo | Severidad | Certeza | Evidencia |
|---|---|---|---|---|
| H-GEN-01 | {{Función obsoleta en 3 interfaces}} | {{Alta/Media/Baja}} | ✅ | [`mcp:interface/{{nombre}}@validation#{{ubicación}}`](./anexo/interface/{{slug}}.md) |

## Registro de hallazgos

<!-- registro:inicio -->
(lo rellena build_registry.py)
<!-- registro:fin -->

## Cobertura y límites

{{1-5 líneas: p. ej. «sin historial de versiones para los CDTs».}}
