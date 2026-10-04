<!--
  Plantilla 13 — Modernización y refactorización (rebuild-architect).
  Estructura: TL;DR → Vista → Detalle → Cobertura y límites. Sin sección Hallazgos: los hallazgos están en sus documentos
  propietarios y en el registro de 09; aquí se citan por su ID, sin severidad.
  Alcance: diagnóstico, estrategia, arquitectura objetivo de alto nivel, plan por fases y decisiones. El diseño detallado
  (modelo de datos, procesos, pantallas, catálogo de objetos y correspondencia actual → objetivo) está en 14-diseno-objetivo.md.
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

Prioridad: Alta · Media · Baja. Esfuerzo por persona: S (de horas a 2 días) · M (3-10 días) · L (más de 2 semanas).

<!-- Más de 15 MOD: una tabla por área (### Datos, ### Procesos, ### Interfaces, ### Integraciones, ### Seguridad, ### Operación). -->

## Detalle: diagnóstico

<!-- Más de 5 fichas: empieza con un índice de enlaces a ellas. Si un MOD no resuelve ningún hallazgo registrado: «Resuelve: —». -->

### MOD-001 — {{actuación}}

{{1 línea: qué cambia y para qué.}}

| Campo | Valor |
|---|---|
| Área | {{Datos · Procesos · Interfaces · Integraciones · Seguridad · Operación}} |
| Qué hay | {{hecho observable y nº de objetos afectados}} |
| Resuelve | [H-UI-01](./10-pantallas.md#hallazgos), [H-PRO-02](./08-procesos-bpmn/{{slug}}.md#hallazgos) |
| Problema | {{Obsoleto · Antipatrón · Diseño mejorable · Deuda}}: {{impacto}} |
| Recomendación | {{práctica o funcionalidad actual de Appian}} |
| Fuente | {{URL de docs.appian.com · «criterio de diseño, sin fuente oficial de Appian»}} |
| Esfuerzo | {{S · M · L}} — {{justificación en una línea}} |
| Prioridad | {{Alta · Media · Baja}} |

Evidencia: `mcp:{{tipo}}/{{nombre}}#{{ubicación}}` · Certeza: ✅

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

{{1-5 líneas: versión de Appian (o «no determinada: se usó la documentación más reciente»); si las recomendaciones se verificaron en el Docs MCP; patrones revisados sin aparición; señales que no se pudieron comprobar porque la extracción no trae su configuración.}}
