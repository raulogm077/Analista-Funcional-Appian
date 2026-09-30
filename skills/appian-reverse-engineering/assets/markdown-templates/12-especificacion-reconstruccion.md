<!--
  Plantilla 12 — Especificación de reconstrucción (agente rebuild-architect)
  Independiente de la implementación actual: describe QUÉ necesita el negocio, no cómo está hecho.
  Los nombres de objetos Appian solo aparecen en "Evidencia" y en la matriz de trazabilidad.
-->

# Especificación para reconstruir la aplicación

> Requisitos funcionales y no funcionales extraídos de la aplicación actual, con criterios de aceptación verificables. Sirve para construirla de nuevo (en Appian actual o en otra tecnología) y como prueba de equivalencia funcional.

## TL;DR

{{Qué hace la aplicación en 2-3 frases}}. {{N}} requisitos funcionales, {{N}} reglas de negocio, {{N}} pantallas, {{N}} integraciones. {{N}} funcionalidades candidatas a no migrar.

## 1. Contexto y objetivos de negocio

{{Del resumen funcional de 01.}}

## 2. Actores y roles

| Actor | Responsabilidad | Capacidades |
|---|---|---|
| {{Gestor}} | {{…}} | {{RF-001, RF-003}} |

## 3. Requisitos funcionales

### RF-001 — {{nombre de la capacidad}}

| Campo | Valor |
|---|---|
| Actor | {{…}} |
| Disparador | {{acción del usuario / temporizador / llamada externa}} |
| Precondiciones | {{…}} |
| Reglas | RN-xxx, RN-yyy |
| Pantallas | PAN-xxx |
| Información | {{entidades que lee / modifica}} |
| Prioridad sugerida | {{Alta/Media/Baja}} — {{uso real: N ejecuciones, última …}} |
| Estado | ✅/🔵/🟡 — Evidencia: `mcp:{{tipo}}/{{nombre}}` |

**Flujo principal**

1. {{…}}

**Flujos alternativos**

- {{…}}

**Criterios de aceptación**

- **Dado** {{contexto}}, **cuando** {{acción}}, **entonces** {{resultado}}.

## 4. Modelo de información

| Entidad | Descripción | Atributos clave (tipo lógico) | Relaciones | Volumen |
|---|---|---|---|---|
| {{Solicitud}} | {{…}} | {{título (texto), importe (decimal)…}} | {{N:1 Estado}} | {{N filas o «no disponible»}} |

## 5. Integraciones (contratos)

| Sistema | Operación | Sentido | Datos | Disparador | Errores |
|---|---|---|---|---|---|
| {{ERP}} | {{notificar alta}} | Salida | {{…}} | {{al aprobar}} | {{tratamiento observado}} |

## 6. Automatismos y notificaciones

| Automatismo | Frecuencia / disparador | Qué hace | Uso real |
|---|---|---|---|
| {{Recordatorio diario}} | {{cada día 08:00}} | {{…}} | {{N ejecuciones}} |

## 7. Seguridad

| Rol | {{RF-001}} | {{RF-002}} |
|---|---|---|
| {{Gestor}} | ✔ | — |

## 8. Requisitos no funcionales

| ID | Requisito | Evidencia |
|---|---|---|
| RNF-001 | {{Volumen: la entidad Solicitud tiene N registros}} | `datafabric.json` |

## 9. Funcionalidad candidata a no migrar

| Elemento | Motivo | Decisión |
|---|---|---|
| {{proceso X}} | {{0 ejecuciones}} | Pendiente de negocio |

## 10. Preguntas abiertas

| ID | Pregunta | Para | Motivo |
|---|---|---|---|
| PQ-001 | {{…}} | Negocio / IT | {{dato no disponible o ambiguo}} |

## 11. Matriz de trazabilidad

| RF | RN | PAN | Proceso | Objetos actuales |
|---|---|---|---|---|
| RF-001 | RN-001, RN-002 | PAN-002 | {{…}} | `{{objetos}}` |
