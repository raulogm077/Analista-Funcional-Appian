<!--
  Plantilla 12 — Especificación para reconstruir la aplicación (rebuild-architect).
  Estructura: TL;DR → Vista → Detalle → Cobertura y límites. Sin sección Hallazgos: los del registro se citan por su ID, sin severidad.
  Independiente de la implementación: los nombres de objetos Appian solo aparecen en las líneas de evidencia y en la matriz de trazabilidad.
  Sin diagrama obligatorio. Los {{marcadores}} se sustituyen y los comentarios se borran.
-->

# Especificación para reconstruir la aplicación

> **TL;DR**: {{2-3 frases: qué hace la aplicación para el negocio y qué cambia respecto a la actual (correcciones y objetivos principales)}}.
> **Volumen**: {{N}} requisitos funcionales, {{N}} reglas de negocio, {{N}} pantallas, {{N}} integraciones y {{N}} requisitos no funcionales; {{N}} criterios corrigen hallazgos registrados, {{N}} funcionalidades son candidatas a no migrar y quedan {{N}} preguntas abiertas.

## Vista

{{Contexto y objetivos de negocio en 2-4 líneas, a partir de 01-funcional.md.}}

Cada paso y cada criterio de aceptación lleva una etiqueta: **(equivalente)** reproduce lo que hoy funciona; **(corrección: H-…)** corrige un hallazgo registrado; **(objetivo)** es un comportamiento nuevo que valida una PQ o una DEC.

| Actor | Responsabilidad | Requisitos |
|---|---|---|
| {{Gestor}} | {{Da de alta las solicitudes}} | RF-001, RF-004 |

| RF | Capacidad | Actor | Disparador | Prioridad | Certeza |
|---|---|---|---|---|---|
| [RF-001](#rf-001--{{ancla}}) | {{Alta de una solicitud}} | {{Gestor}} | {{Acción del usuario}} | {{Alta}} | ✅ |

<!-- Más de 15 RF: una tabla por actor o por área de negocio. -->

## Detalle: requisitos funcionales

<!-- Más de 5 fichas: empieza con un índice de enlaces a ellas. -->

### RF-001 — {{nombre de la capacidad}}

{{1 línea: qué consigue el actor.}}

| Campo | Valor |
|---|---|
| Actor | {{…}} |
| Disparador | {{acción del usuario · temporizador · llamada externa}} |
| Precondiciones | {{…}} |
| Reglas | [RN-001](./11-reglas-negocio.md#rn-001--{{ancla}}), {{…}} |
| Pantallas | [PAN-002](./10-pantallas.md#pan-002--{{ancla}}) |
| Información | {{entidades que lee, crea o modifica}} |
| Prioridad sugerida | {{Alta · Media · Baja}} — {{N ejecuciones, última dd/mm/aaaa · sin ejecuciones: validar (PQ-00N)}} |

**Flujo principal**

1. {{El gestor abre la lista y elige «Nueva solicitud».}} (equivalente)
2. {{El sistema registra la solicitud con los datos introducidos.}} (corrección: H-UI-01)

**Flujos alternativos**

- {{Cancelar: no se registra nada ni se crea la revisión.}} (corrección: H-PRO-01)

**Criterios de aceptación**

- **Dado** {{el formulario de alta}}, **cuando** {{se envía sin título}}, **entonces** {{no se registra y se señala el título}}. (equivalente, RN-001)
- **Dado** {{un formulario completo}}, **cuando** {{se envía}}, **entonces** {{se guardan todos los datos}}. (corrección: H-UI-01)
- **Dado** {{un usuario sin rol de gestor}}, **cuando** {{abre la lista}}, **entonces** {{no ve «Nueva solicitud»}}. (objetivo, PQ-002)

Evidencia: `mcp:processModel/{{nombre}}#nodes[id={{N}}]`, `mcp:interface/{{nombre}}#expression (línea {{N}})` · Certeza: ✅

## Detalle: información, integraciones y seguridad

### Modelo de información

Entidades de negocio con tipo lógico. El diseño de datos (tablas, tipos, nulos) está en [14-diseno-objetivo.md](./14-diseno-objetivo.md).

| Entidad | Descripción | Atributos clave (tipo lógico) | Relaciones | Volumen |
|---|---|---|---|---|
| {{Solicitud}} | {{Petición interna que se revisa}} | {{título (texto), importe (decimal)}} | {{N:1 Estado}} | {{N registros · no disponible}} |

### Integraciones (contratos)

| Sistema | Operación | Sentido | Datos | Disparador | Errores |
|---|---|---|---|---|---|
| {{ERP}} | {{Notificar el alta}} | Salida | {{Identificador y título}} | {{Al terminar el alta}} | {{Tratamiento observado · ❓ no lo trae la extracción}} |

### Automatismos y notificaciones

| Automatismo | Frecuencia o disparador | Qué hace | Uso real |
|---|---|---|---|
| {{Recordatorio de pendientes}} | {{Cada día a las 08:00}} | {{Avisa de las solicitudes pendientes}} | {{N ejecuciones}} |

### Seguridad

Qué rol puede ejecutar cada requisito. Si el permiso necesario difiere del actual, la celda lo indica.

| RF | {{Gestor}} | {{Revisor}} | {{Administrador}} |
|---|---|---|---|
| RF-001 | Sí | {{No (corrección: H-SEG-01)}} | Sí |

### Requisitos no funcionales

| ID | Requisito | Evidencia |
|---|---|---|
| RNF-001 | {{La entidad Solicitud tiene N registros}} | {{Recuento del data fabric del registro Solicitud}} |

## Detalle: alcance y trazabilidad

### Funcionalidad candidata a no migrar

| Elemento | Motivo | Decisión |
|---|---|---|
| {{Proceso de utilidad}} | {{Sin ejecuciones ni referencias}} | {{Pendiente de negocio (PQ-003)}} |

### Preguntas abiertas

| ID | Pregunta | Para | Hallazgos | Motivo |
|---|---|---|---|---|
| PQ-001 | {{¿Debe poder elegirse el estado en el alta?}} | {{Negocio}} | {{H-UI-03}} | {{Diseño previsto sin confirmar}} |

### Matriz de trazabilidad

| RF | RN | PAN | Proceso | Objetos actuales |
|---|---|---|---|---|
| RF-001 | RN-001, RN-002 | PAN-002 | {{Alta de solicitud}} | `{{objeto}}`, `{{objeto}}` |

## Cobertura y límites

{{1-5 líneas: qué no se pudo especificar y por qué (p. ej. configuración de la lista de registros no disponible). Lo global (entorno, versión, muestra de ejecuciones, configuración que el Dev MCP no devuelve) está en LEEME: no lo repitas.}}
