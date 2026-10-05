<!--
  Plantilla 14 — Diseño objetivo (target-designer).
  Estructura: TL;DR → Vista → Detalle (por partes) → Cobertura y límites. Sin sección Hallazgos: se citan IDs de 12, 13 y del registro.
  Cada elemento cita su origen (RF, RN, PAN, MOD, DEC, H-). Lo que depende de una PQ o DEC abierta lleva ❓.
  Diagramas: objetivo-datos (erDiagram); objetivo-<slug> y objetivo-navegacion solo si cambian. Los {{marcadores}} se sustituyen y los comentarios se borran.
-->

# Diseño objetivo

> **TL;DR**: {{1-2 frases: cómo es la aplicación objetivo y la decisión de diseño que más cambia; la estrategia de 13 (reconstrucción limpia · refactor in situ · mixta) solo afecta a la migración}}.
> **Volumen**: {{N}} entidades, {{N}} procesos, {{N}} pantallas, {{N}} integraciones; {{N}} objetos nuevos, {{N}} que cambian, {{N}} que se eliminan; {{N}} elementos condicionados a PQ o DEC.

## Vista

| Parte | Qué se construye | Sale de | Detalle |
|---|---|---|---|
| Datos | {{N entidades sincronizadas y sus relaciones}} | {{RF-001…RF-00N, MOD-00N}} | [Datos](#detalle-datos) |
| Procesos | {{N procesos; N cambian de forma}} | {{RF-…, MOD-…}} | [Procesos](#detalle-procesos) |
| Pantallas | {{N pantallas}} | {{PAN-001…PAN-00N}} | [Pantallas](#detalle-pantallas) |
| Integraciones | {{N contratos}} | {{RF-…, MOD-…}} | [Integraciones y seguridad](#detalle-integraciones-y-seguridad) |
| Seguridad | {{N grupos por rol}} | {{RF-…, MOD-…}} | [Integraciones y seguridad](#detalle-integraciones-y-seguridad) |

**Orden de construcción** (fases de [13](./13-modernizacion-refactor.md#detalle-plan-por-fases)): {{1. datos y seguridad base → 2. reglas → 3. integraciones → 4. interfaces → 5. procesos → 6. pruebas con los criterios de 12}}.

## Detalle: datos

{{Frase: qué muestra el diagrama.}}

![Modelo de datos objetivo](diagrams/objetivo-datos.svg)

Fuente: [objetivo-datos.mmd](diagrams/objetivo-datos.mmd)

### {{Entidad}}

{{1 línea: qué representa y para qué RF.}} Volumen actual: {{N filas · ❓}}.

| Campo | Tipo | Obligatorio | Regla o validación | Origen | Para |
|---|---|---|---|---|---|
| {{importe}} | {{Decimal}} | {{Sí}} | {{> 0 (RN-003)}} | {{campo actual `importe` · nuevo}} | {{RF-001}} |

Relaciones: {{N:1 con Estado (estadoId)}}. {{Eventos de record, filtros o seguridad por fila, solo si los pide un RF, RN o MOD, con su ID.}}

## Detalle: procesos

### {{Proceso objetivo}}

{{1 línea: propósito (RF-00N) y disparador.}}

| Paso | Actor | Qué hace | Errores | Cambia respecto al actual |
|---|---|---|---|---|
| 1 | {{Gestor}} | {{Rellena el formulario de alta (PAN-002)}} | — | {{Ahora guarda todos los campos (MOD-001, H-UI-01)}} |

<!-- Si el proceso cambia de forma: imagen objetivo-<slug>.png con «Editable: [objetivo-<slug>.drawio](…) · BPMN: [objetivo-<slug>.bpmn](…)» (vía draw.io), o imagen objetivo-<slug>.svg + «Fuente» (Mermaid). Si se mantiene igual: «Sin cambios de forma: ver [ficha actual](./08-procesos-bpmn/<slug>.md)». -->

## Detalle: ciclo de vida

{{Solo si la entidad principal tiene estados. Frase: qué estados tiene hoy y cuáles tendrá.}}

| Estado | Entra por (evento) | Lo escribe | Sale hacia | Hoy |
|---|---|---|---|---|
| {{Enviada}} | {{Alta (RF-001)}} | {{DEM Alta Solicitud}} | {{Aprobada · Rechazada}} | {{Existe · No existe · ❓ (PQ-001)}} |

## Detalle: pantallas

### PAN-00N — {{pantalla}}

{{1 línea: quién la usa y para qué (RF-00N).}}

| Componente | Tipo | Campo vinculado | Validación | Obligatorio |
|---|---|---|---|---|
| {{Título}} | {{Texto}} | {{Solicitud.titulo}} | {{RN-001}} | {{Sí}} |

Acciones: {{Enviar → crea la solicitud y lanza la revisión (RF-001) · Cancelar → no crea nada (corrección: H-PRO-01)}}.

## Detalle: integraciones y seguridad

| Integración | Operación | Entradas → salidas | Autenticación | Errores |
|---|---|---|---|---|
| {{ERP: notificar alta}} | {{POST /notificaciones}} | {{id, estado → acuse}} | {{API key en el connected system}} | {{Reintento y aviso al administrador (MOD-00N)}} |

| Grupo (rol) | Puede | Sale de |
|---|---|---|
| {{Gestores}} | {{Iniciar el alta, ver sus solicitudes}} | {{RF-001, matriz de 12}} |

## Detalle: catálogo de objetos

Nomenclatura: {{regla aplicada}} (fuente: {{URL de la guía oficial de nombres de Appian}}).

| Objeto objetivo | Tipo | Propósito | Sale de |
|---|---|---|---|
| {{DEM_SolicitudForm}} | {{Interfaz}} | {{Alta de solicitud}} | {{PAN-002, MOD-001}} |

## Detalle: correspondencia y migración

{{1 línea: estrategia de 13 y qué significa aquí.}}

| Objeto actual | Objeto objetivo | Qué pasa | Motivo |
|---|---|---|---|
| {{DEM_SolicitudForm}} | {{DEM_SolicitudForm}} | {{Se mantiene y cambia · Se sustituye · Se elimina · Nuevo}} | {{MOD-001}} |

{{Migración de datos: qué se conserva, qué se transforma y en qué fase de 13.}}

### Si se reconstruye en una aplicación nueva

{{Siempre, sea cual sea la estrategia: lo que haría falta para construir este diseño en una aplicación nueva y retirar la actual.}}

| Tema | Qué hacer |
|---|---|
| Datos | {{Migrar las N solicitudes y el catálogo; transformaciones; verificación por recuento}} |
| Corte | {{Cuándo se cambia y qué pasa con las tareas y procesos en curso}} |
| Contratos externos | {{Mantener el alias de la Web API y el contrato con el ERP, o versionarlos}} |
| Seguridad | {{Grupos y cuentas de servicio nuevos; quién los crea}} |
| Retirada | {{Cómo se apaga la aplicación actual (permisos, temporizadores, objetos)}} |

## Cobertura y límites

{{1-5 líneas: elementos condicionados a PQ o DEC (con sus IDs), detalles del modelo actual que la extracción no trajo y que este diseño decide, funcionalidades confirmadas o no en la documentación de la versión del entorno. Lo global (entorno, versión, muestra de ejecuciones, configuración que el Dev MCP no devuelve) está en LEEME: no lo repitas.}}
