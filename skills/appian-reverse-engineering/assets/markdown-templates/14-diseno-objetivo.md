<!--
  Plantilla 14 — Diseño objetivo (target-designer).
  Estructura: TL;DR → Vista → Detalle (por partes) → Cobertura y límites. Sin sección Hallazgos: se citan IDs de 12, 13 y del registro.
  Cada elemento cita su origen (RF, RN, PAN, MOD, DEC, H-). Lo que depende de una PQ o DEC abierta lleva ❓.
  Diagramas: objetivo-datos (erDiagram); objetivo-<slug> y objetivo-navegacion solo si cambian. Los {{marcadores}} se sustituyen y los comentarios se borran.
-->

# Diseño objetivo

> **TL;DR**: {{1-2 frases: cómo queda la aplicación con la estrategia de 13 (reconstrucción limpia · refactor in situ · mixta) y la decisión de diseño que más cambia}}.
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

<!-- Si el proceso cambia de forma: imagen objetivo-<slug>.svg + «Fuente». Si se mantiene igual: «Sin cambios de forma: ver [ficha actual](./08-procesos-bpmn/<slug>.md)». -->

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

| Objeto objetivo | Tipo | Propósito | Sale de | Origen |
|---|---|---|---|---|
| {{DEM_SolicitudForm}} | {{Interfaz}} | {{Alta de solicitud}} | {{PAN-002, MOD-001}} | {{actual, cambia · nuevo}} |

<!-- Objetos actuales que se eliminan o se sustituyen: -->

| Objeto actual | Destino | Motivo |
|---|---|---|
| {{DEM Utilidad Huérfana}} | {{Se elimina}} | {{Sin ejecuciones ni referencias (MOD-00N) ❓ validar}} |

## Cobertura y límites

{{1-5 líneas: elementos condicionados a PQ o DEC (con sus IDs), detalles del modelo actual que la extracción no trajo y que este diseño decide, funcionalidades confirmadas o no en la documentación de la versión del entorno.}}
