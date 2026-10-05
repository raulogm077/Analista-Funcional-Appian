<!--
  Plantilla 14 — Diseño objetivo (target-designer).
  Estructura: TL;DR → Vista → Detalle (por partes) → Cobertura y límites. Sin sección Hallazgos: se citan IDs de 12, 13 y del registro.
  Cada elemento cita su origen (RF, RN, PAN, MOD, DEC, H-). Lo que depende de una PQ o DEC abierta lleva ❓.
  Lo que decide el diseño sin PQ ni DEC: «decisión de diseño — Valida: Arquitectura» (o el rol que corresponda).
  Lo que no cambia: en el catálogo, con el enlace a su ficha del anexo. Los objetos huérfanos no se listan: se cita su H-ARQ o se enlaza 09.
  Cifras de uso o volumen de un entorno que no consta como producción: marca corta «orientativo (ver LEEME)».
  Longitud: crece con los elementos que cambian (Regla 9 de presentation-rules); nunca se recorta uno para cumplirla.
  Más de unas 15 fichas: las fichas de datos, procesos y pantallas se agrupan por área («### <área>» dentro de cada
  «## Detalle: …») y tras la Vista va un índice de áreas con enlaces (presentation-rules.md, Regla 9).
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

**Orden de construcción en una aplicación nueva** (siempre, sea cual sea la estrategia; cuándo se aplica cada cambio a la aplicación actual lo dicen las [fases de 13](./13-modernizacion-refactor.md#detalle-plan-por-fases)):

| Paso | Se construye | Objetos | Se prueba con |
|---|---|---|---|
| 1 | {{Dependencias externas, datos y seguridad base}} | {{Plug-ins de 02, record types, grupos}} | — |
| 2 | {{Reglas y constantes}} | {{…}} | {{Criterios de RN-00N}} |
| 3 | {{Integraciones}} | {{…}} | {{Criterios de RF-00N}} |
| 4 | {{Interfaces}} | {{…}} | {{Criterios de RF-00N}} |
| 5 | {{Procesos}} | {{…}} | {{Criterios de RF-00N}} |

## Detalle: datos

{{Frase: qué muestra el diagrama.}}

![Modelo de datos objetivo](diagrams/objetivo-datos.svg)

Fuente: [objetivo-datos.mmd](diagrams/objetivo-datos.mmd)

<!-- Una ficha por entidad nueva o que cambia; las que no cambian, en «Entidades sin cambios». Entre las dos, todas las entidades. -->

### {{Entidad}}

{{1 línea: qué representa y para qué RF.}} Volumen actual: {{N filas · ❓}}.

| Campo | Tipo | Obligatorio | Regla o validación | Origen | Para |
|---|---|---|---|---|---|
| {{importe}} | {{Decimal}} | {{Sí}} | {{> 0 (RN-003)}} | {{campo actual `importe` · nuevo}} | {{RF-001}} |
| {{comentario}} | {{Texto (2000)}} | {{No}} | {{Longitud: decisión de diseño — Valida: Arquitectura}} | {{nuevo}} | {{RF-003}} |

Relaciones: {{N:1 con Estado (estadoId)}}. {{Eventos de record, filtros o seguridad por fila, solo si los pide un RF, RN o MOD, con su ID.}}

### Entidades sin cambios

| Entidad | Campos clave (tipo) | Relaciones | Volumen | Definición |
|---|---|---|---|---|
| {{Estado}} | {{id (entero), nombre (texto)}} | {{1:N Solicitud}} | {{N filas · ❓}} | [anexo](./anexo/recordType/{{slug}}.md) |

## Detalle: procesos

### {{Proceso objetivo}}

{{1 línea: propósito (RF-00N) y disparador.}}

<!-- Si el proceso cambia de forma: imagen diagrams/objetivo-<slug>.png con «Editable: [objetivo-<slug>.drawio](diagrams/objetivo-<slug>.drawio)» (vía draw.io), o imagen diagrams/objetivo-<slug>.svg + «Fuente» (Mermaid). Si se mantiene igual: «Sin cambios de forma: ver [ficha actual](./08-procesos-bpmn/<slug>.md)». -->

| Paso | Actor | Qué hace | Errores | Cambia respecto al actual |
|---|---|---|---|---|
| 1 | {{Gestor}} | {{Rellena el formulario de alta (PAN-002)}} | — | {{Ahora guarda todos los campos (MOD-001, H-UI-01)}} |

## Detalle: ciclo de vida

{{Solo si la entidad principal tiene estados. Frase: qué estados tiene hoy y cuáles tendrá. El ciclo actual está en [11](./11-reglas-negocio.md).}}

| Estado | Entra por (evento) | Lo escribe | Sale hacia | Hoy |
|---|---|---|---|---|
| {{Enviada}} | {{Alta (RF-001)}} | {{DEM Alta Solicitud}} | {{Aprobada · Rechazada}} | {{Existe ([RN-009](./11-reglas-negocio.md#rn-009--{{ancla}})) · No existe · ❓ (PQ-001)}} |

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
| {{DEM_ER_EsAdmin}} | {{Regla de expresión}} | {{Comprobación de administrador}} | Sin cambios: [definición](./anexo/{{tipo}}/{{slug}}.md) |

## Detalle: correspondencia y migración

{{1 línea: estrategia de 13 y qué significa aquí.}}

| Objeto actual | Objeto objetivo | Qué pasa | Motivo |
|---|---|---|---|
| {{DEM_SolicitudForm}} | {{DEM_SolicitudForm}} | {{Se mantiene y cambia · Se sustituye · Se elimina · Nuevo}} | {{MOD-001}} |
| Objetos sin referencias ([lista de 09](./09-valor-adicional.md#objetos-huérfanos)) | — | {{Se eliminan}} | {{MOD-00N, H-ARQ-0N}} |

{{Migración de datos: qué se conserva, qué se transforma y en qué fase de 13.}}

### Si se reconstruye en una aplicación nueva

{{Siempre, sea cual sea la estrategia: lo que haría falta para construir este diseño en una aplicación nueva y retirar la actual. El orden de construcción está en la Vista.}}

| Tema | Qué hacer |
|---|---|
| Plug-ins y dependencias | {{Las de [02](./02-arquitectura.md#dependencias-externas): qué se instala o se crea antes en el entorno nuevo y qué se sustituye}} |
| Datos | {{Migrar las N solicitudes y el catálogo; transformaciones; verificación por recuento}} |
| Corte | {{Cuándo se cambia y qué pasa con las tareas y procesos en curso}} |
| Contratos externos | {{Mantener el alias de la Web API y el contrato con el ERP, o versionarlos}} |
| Seguridad | {{Grupos y cuentas de servicio nuevos; quién los crea}} |
| Retirada | {{Cómo se apaga la aplicación actual (permisos, temporizadores, objetos)}} |

## Cobertura y límites

{{1-5 líneas: elementos condicionados a PQ o DEC (con sus IDs), decisiones de diseño y quién las valida, detalles del modelo actual que la extracción no trajo y que este diseño decide, funcionalidades confirmadas o no en la documentación de la versión del entorno. Lo global (entorno, versión, muestra de ejecuciones, configuración que el Dev MCP no devuelve) está en LEEME: no lo repitas.}}
