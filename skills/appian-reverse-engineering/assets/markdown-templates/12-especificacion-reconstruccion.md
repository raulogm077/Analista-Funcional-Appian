<!--
  Plantilla 12 — Especificación para reconstruir la aplicación (rebuild-architect).
  Estructura: TL;DR → Vista → Detalle → Cobertura y límites. Sin sección Hallazgos: los del registro se citan por su ID, sin severidad.
  Independiente de la implementación: los nombres de objetos Appian solo aparecen en la evidencia y en la matriz de trazabilidad.
  Evidencia con el enlace a su ficha del anexo: [`mcp:<tipo>/<nombre>#<ubicación>`](./anexo/<tipo>/<slug>.md).
  Cifras de uso de un entorno que no consta como producción: marca corta «orientativo (ver LEEME)», sin explicar la limitación.
  Longitud: crece con los RF (Regla 9 de presentation-rules); nunca se recorta un RF para cumplirla.
  Sin diagrama obligatorio. Los {{marcadores}} se sustituyen y los comentarios se borran.
-->

# Especificación para reconstruir la aplicación

> **TL;DR**: {{2-3 frases: qué hace la aplicación para el negocio y qué cambia respecto a la actual (correcciones y objetivos principales)}}.
> **Volumen**: {{N}} requisitos funcionales, {{N}} reglas de negocio, {{N}} pantallas, {{N}} integraciones y {{N}} requisitos no funcionales; {{N}} criterios corrigen hallazgos registrados, {{N}} funcionalidades son candidatas a no migrar y quedan {{N}} preguntas abiertas.

## Vista

{{Contexto y objetivos de negocio en 2-4 líneas, a partir de 01-funcional.md.}}

Cada paso y cada criterio de aceptación lleva una etiqueta: **(equivalente)** reproduce lo que hoy hace la aplicación, verificado o inferido; **(corrección: H-…)** corrige un hallazgo registrado; **(objetivo)** es un comportamiento nuevo, o uno actual sin confirmar, que valida una PQ o una DEC.

| Actor | Responsabilidad | Requisitos |
|---|---|---|
| {{Gestor}} | {{Da de alta las solicitudes}} | RF-001, RF-004 |

| RF | Capacidad | Actor | Disparador | Prioridad | Certeza |
|---|---|---|---|---|---|
| [RF-001](#rf-001--{{ancla}}) | {{Alta de una solicitud}} | {{Gestor}} | {{Acción del usuario}} | {{Alta}} | ✅ |

<!-- Más de 15 RF: una tabla por actor o por área de negocio. -->

## Detalle: requisitos funcionales

<!-- Más de 5 fichas: empieza con un índice de enlaces a ellas.
     Más de unas 15 fichas: un «## Detalle: <área de negocio>» por área con sus fichas RF, y tras la Vista un índice de
     áreas con enlaces (presentation-rules.md, Regla 9). -->

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
| Prioridad sugerida | {{Alta}} — {{N ejecuciones, última dd/mm/aaaa · 0 ejecuciones registradas (PQ-00N) · uso no medible (PQ-00N)}} |

**Flujo principal**

1. {{El gestor abre la lista y elige «Nueva solicitud».}} (equivalente)
2. {{El sistema registra la solicitud con los datos introducidos.}} (corrección: H-UI-01)
3. {{El sistema pasa la solicitud a revisión y espera su resultado.}} (objetivo, PQ-003)

**Flujos alternativos**

- {{Cancelar: no se registra nada ni se crea la revisión.}} (corrección: H-PRO-01)

**Criterios de aceptación**

- **Dado** {{el formulario de alta}}, **cuando** {{se envía sin título}}, **entonces** {{no se registra y se señala el título}}. (equivalente, RN-001)
- **Dado** {{un formulario completo}}, **cuando** {{se envía}}, **entonces** {{se guardan todos los datos}}. (corrección: H-UI-01)
- **Dado** {{un usuario sin rol de gestor}}, **cuando** {{abre la lista}}, **entonces** {{no ve «Nueva solicitud»}}. (objetivo, PQ-002)

Evidencia: [`mcp:processModel/{{nombre}}#nodes[id={{N}}]`](./anexo/processModel/{{slug}}.md), [`mcp:interface/{{nombre}}#expression (línea {{N}})`](./anexo/interface/{{slug}}.md) · Certeza: ✅

## Detalle: información, integraciones y seguridad

### Modelo de información

Entidades de negocio con tipo lógico. El diseño de datos (tablas, tipos, nulos) está en [14-diseno-objetivo.md](./14-diseno-objetivo.md).

| Entidad | Descripción | Atributos clave (tipo lógico) | Relaciones | Volumen |
|---|---|---|---|---|
| {{Solicitud}} | {{Petición interna que se revisa}} | {{título (texto), importe (decimal)}} | {{N:1 Estado}} | {{N registros · no disponible}} |

### Datos de referencia

Valores de los catálogos que la migración necesita. Solo se conocen los que fija la aplicación en constantes o expresiones; los que están únicamente en la base de datos hay que exportarlos (la extracción no lee filas de datos).

| Catálogo | Valores conocidos | Dónde constan | Pendiente |
|---|---|---|---|
| {{Estado}} | {{Borrador, Enviada, Aprobada, Rechazada}} | [`mcp:constant/{{nombre}}#value`](./anexo/constant/{{slug}}.md) | {{Identificadores de cada valor (PQ-00N)}} |
| {{Tipo de gasto}} | {{Solo en base de datos}} | — | {{Exportar la tabla completa (PQ-00N, DBA)}} |

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

<!-- Al menos un RNF por categoría, sin juntar categorías: entornos y despliegue, rendimiento y volumen, disponibilidad,
     auditoría y trazabilidad, retención de datos, accesibilidad e idioma, dependencias externas.
     Criterio medible: Dado/Cuando/Entonces o un umbral. Sin evidencia: «valor a fijar» y su PQ. -->

| ID | Categoría | Requisito | Criterio medible | Certeza | Evidencia |
|---|---|---|---|---|---|
| RNF-001 | {{Rendimiento y volumen}} | {{Tratar todas las solicitudes, aunque superen un lote}} | {{Dado N+1 pendientes con lote N, cuando corre el recordatorio, entonces las trata todas}} | ✅ | {{Recuento del data fabric del registro Solicitud}} |
| RNF-002 | Dependencias externas | {{Funciona con las dependencias de [02](./02-arquitectura.md#dependencias-externas)}} | {{Dado un entorno nuevo con esas dependencias, cuando se despliega, entonces todo resuelve}} | {{✅ · ❓ (no reconocidas)}} | [`mcp:{{tipo}}/{{nombre}}@dependencies`](./anexo/{{tipo}}/{{slug}}.md) |
| RNF-003 | {{Retención de datos}} | {{Plazo de conservación de las solicitudes}} | {{Valor a fijar (PQ-00N)}} | ❓ | {{Sin evidencia en la aplicación}} |

## Detalle: alcance y trazabilidad

### Funcionalidad candidata a no migrar

| Elemento | Motivo | Decisión |
|---|---|---|
| {{Proceso de utilidad}} | {{0 ejecuciones registradas y sin invocador}} | {{Pendiente de negocio (PQ-003)}} |
| Objetos sin referencias | [Lista de 09](./09-valor-adicional.md#objetos-huérfanos) ({{H-ARQ-0N}}) | {{Pendiente de IT (PQ-00N)}} |

### Preguntas abiertas

<!-- Solo las que afectan a la reconstrucción. Las de operación de la aplicación actual (una ejecución concreta,
     instancias detenidas, qué cuentas despliegan) se quedan como ❓ en su documento propietario. -->

| ID | Pregunta | Para | Hallazgos | Motivo |
|---|---|---|---|---|
| PQ-001 | {{¿Debe poder elegirse el estado en el alta?}} | {{Negocio}} | {{H-UI-03}} | {{Diseño previsto sin confirmar}} |

### Matriz de trazabilidad

| RF | RN | PAN | Proceso | Objetos actuales |
|---|---|---|---|---|
| RF-001 | RN-001, RN-002 | PAN-002 | {{Alta de solicitud}} | `{{objeto}}`, `{{objeto}}` |

## Cobertura y límites

{{1-5 líneas: qué no se pudo especificar y por qué (p. ej. configuración de la lista de registros no disponible). Lo global (entorno, versión, muestra de ejecuciones, configuración que el Dev MCP no devuelve) está en LEEME: no lo repitas.}}
