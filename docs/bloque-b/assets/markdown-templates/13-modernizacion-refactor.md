<!--
  Plantilla 13 — Modernización y refactorización (rebuild-architect).
  Estructura: TL;DR → Vista → Detalle → Cobertura y límites. Sin sección Hallazgos: los hallazgos están en sus documentos
  propietarios y en el registro de 09; aquí se citan por su ID, sin severidad, y se enlazan en lugar de volver a explicarlos.
  Alcance: diagnóstico, estrategia, arquitectura objetivo de alto nivel, plan por fases y decisiones. El diseño detallado
  (modelo de datos, procesos, pantallas, catálogo de objetos y correspondencia actual → objetivo) está en 14-diseno-objetivo.md.
  Evidencia con el enlace a su ficha del anexo: [`mcp:<tipo>/<nombre>#<ubicación>`](./anexo/<tipo>/<slug>.md).
  Cifras de uso de un entorno que no consta como producción: marca corta «orientativo (ver LEEME)», sin explicar la limitación.
  Longitud: crece con los MOD (Regla 9 de presentation-rules); nunca se recorta un MOD para cumplirla.
  Diagrama obligatorio: arquitectura-objetivo (flowchart TD por capas). Los {{marcadores}} se sustituyen y los comentarios se borran.
-->

# Modernización y refactorización

> **TL;DR**: Veredicto: **{{Mantener y mejorar · Refactorizar por fases · Reconstruir}}**, con estrategia de **{{reconstrucción limpia · refactor in situ · mixta}}**. {{1-2 frases: por qué (hallazgos, tamaño, uso real) y qué se hace primero}}.
> **Volumen**: {{N}} actuaciones (prioridad Alta: {{n}}) que tratan {{N}} de los {{N}} hallazgos del registro, en {{N}} fases; {{N}} decisiones pendientes.

## Vista

| Decisión | Elección | Por qué |
|---|---|---|
| Veredicto | {{Refactorizar por fases}} | {{Hallazgos Alta en el alta y la revisión; modelo de datos ya actual}} |
| Estrategia | {{Refactor in situ}} | {{Los objetos actuales siguen el diseño recomendado; cambiar en la app es más barato}} |

{{1-2 líneas: por qué no las otras dos estrategias.}}

| MOD | Actuación | Área | Prioridad | Esfuerzo | Resuelve |
|---|---|---|---|---|---|
| [MOD-001](#mod-001--{{ancla}}) | {{Guardar los datos del formulario de alta}} | {{Interfaces}} | {{Alta}} | {{S}} | {{H-UI-01, H-PRO-02}} |
| [MOD-007](#actuaciones-menores) | {{Una sola comprobación de administrador}} | {{Seguridad}} | Baja | S | {{H-RN-05}} |

Prioridad: Alta · Media · Baja. Esfuerzo por persona: S (de horas a 2 días) · M (3-10 días) · L (más de 2 semanas).

<!-- Más de 15 MOD: una tabla por área (### Datos, ### Procesos, ### Interfaces, ### Integraciones, ### Seguridad, ### Operación). -->

## Detalle: diagnóstico

<!-- Ficha completa solo para los MOD de prioridad Alta o Media, o de esfuerzo M o L. Los de prioridad Baja y esfuerzo S
     van como fila de «Actuaciones menores», al final de esta sección.
     Más de 5 fichas: empieza con un índice de enlaces a ellas.
     Más de unas 15 fichas: un «## Detalle: <área>» por área (datos, procesos, interfaces, integraciones, seguridad,
     operación) con sus fichas, y tras la Vista un índice de áreas con enlaces (presentation-rules.md, Regla 9).
     Objetos huérfanos: el MOD cita su H-ARQ y enlaza la lista de 09 (./09-valor-adicional.md#objetos-huérfanos); no la copia. -->

### MOD-001 — {{actuación}}

{{1 línea: qué cambia y para qué.}}

| Campo | Valor |
|---|---|
| Área | {{Datos · Procesos · Interfaces · Integraciones · Seguridad · Operación}} |
| Resuelve | [H-UI-01](./10-pantallas.md#hallazgos), [H-PRO-02](./08-procesos-bpmn/{{slug}}.md#hallazgos) |
| Qué hay | {{nº de objetos afectados (el problema, en el hallazgo); con «Resuelve: —», el hecho observable}} |
| Problema | {{Obsoleto · Antipatrón · Diseño mejorable · Deuda}}{{; impacto en una línea solo con «Resuelve: —»}} |
| Recomendación | {{práctica o funcionalidad actual de Appian}} |
| Fuente | {{URL de docs.appian.com · «criterio de diseño, sin fuente oficial de Appian»}} |
| Esfuerzo | {{S · M · L}} — {{justificación en una línea}} |
| Prioridad | {{Alta · Media · Baja}} |

{{Notas (si aplica, ≤ 3 líneas): cómo se aplica la recomendación y sus riesgos; no repitas el hallazgo.}}

Evidencia: [`mcp:{{tipo}}/{{nombre}}#{{ubicación}}`](./anexo/{{tipo}}/{{slug}}.md) · Certeza: ✅

### Actuaciones menores

Prioridad Baja y esfuerzo S.

| MOD | Actuación | Resuelve | Recomendación | Fuente | Evidencia |
|---|---|---|---|---|---|
| MOD-007 | {{Una sola comprobación de administrador}} | [H-RN-05](./11-reglas-negocio.md#hallazgos) | {{Llamar a la regla común}} | {{Criterio de diseño, sin fuente oficial de Appian}} | [`mcp:{{tipo}}/{{nombre}}#{{ubicación}}`](./anexo/{{tipo}}/{{slug}}.md) |

## Detalle: oportunidades

<!-- Solo si alguna capacidad resuelve una necesidad observada en esta app. -->

| Capacidad | Necesidad observada en esta app | Fuente |
|---|---|---|
| {{Process HQ}} | {{Los recuentos por estado se calculan a mano en el panel}} | {{URL de docs.appian.com}} |

## Detalle: arquitectura objetivo

{{Frase: qué muestra el diagrama.}}

![Arquitectura objetivo por capas](diagrams/arquitectura-objetivo.svg)

Fuente: [arquitectura-objetivo.mmd](diagrams/arquitectura-objetivo.mmd)

<!-- Sin SVG: sustituye las dos líneas anteriores por el bloque mermaid idéntico a arquitectura-objetivo.mmd (flowchart TD, subgraph por capa, ≤ 30 nodos). -->

**Principios de diseño**

- {{Principio}} ({{MOD-00N · RF-00N}})

El diseño detallado (modelo de datos objetivo, procesos y pantallas objetivo, catálogo de objetos con su nomenclatura y correspondencia objeto actual → objetivo) está en [14-diseno-objetivo.md](./14-diseno-objetivo.md).

## Detalle: plan por fases

| Fase | Objetivo | Incluye | Depende de | Riesgos y mitigación |
|---|---|---|---|---|
| 0 | {{Contención y mejoras sin refactorizar}} | {{MOD-002, MOD-005}} | — | {{…}} |
| 1 | {{…}} | {{MOD-001}} | {{Fase 0}} | {{…}} |

**Estrategia de datos**: {{coexistencia · migración}} — {{por qué}}.

**Estrategia de pruebas**: los criterios de aceptación de [12-especificacion-reconstruccion.md](./12-especificacion-reconstruccion.md) son la prueba: los (equivalente) demuestran que no se pierde nada; los (corrección) y (objetivo), el cambio.

## Detalle: decisiones pendientes

| ID | Decisión | Opciones | Recomendación | Quién |
|---|---|---|---|---|
| DEC-001 | {{…}} | {{A · B}} | {{A, porque …}} | {{Arquitectura · Negocio}} |

## Cobertura y límites

{{1-5 líneas: recomendaciones no verificadas en el Docs MCP (con sus IDs); patrones revisados sin aparición; señales que no se pudieron comprobar porque la extracción no trae su configuración. Lo global (entorno, versión, muestra de ejecuciones, configuración que el Dev MCP no devuelve) está en LEEME: no lo repitas.}}
