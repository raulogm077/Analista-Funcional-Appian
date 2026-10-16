# Solicitudes de autorización — Documento de diseño funcional

Código: DF-AUT-001 · Proyecto: Gestión de autorizaciones · Ciudad: Madrid · Fecha: Octubre 2026
Versión: 1.0 · Estado: en revisión

## Control de cambios

| Fecha entrega | Versión | Descripción / Motivo del cambio | Autor | Responsable de validación | Fecha de validación |
|---|---|---|---|---|---|
| 14/10/2026 | 1.0 | Primera versión del diseño funcional | Equipo de análisis | | |

## 1. Introducción al proceso

### 1.1 Descripción del proceso

#### Descripción del proceso

Las unidades de la organización piden autorización para ocupar espacios comunes con actividades temporales. Hoy la
solicitud llega por correo con un formulario en hoja de cálculo; el área de autorizaciones la revisa, pide lo que
falta por correo y resuelve con un escrito firmado.

El objetivo funcional es disponer de un entorno para:

- Registrar las solicitudes y su documentación.
- Dar seguimiento a los plazos de revisión.

#### Integraciones

- **Registro de organismos** – Al enviar la solicitud se comprueba que la unidad está de alta.

### 1.2 Alcance

#### Dentro del alcance

Digitalizar la solicitud, la revisión y la resolución de las autorizaciones de ocupación temporal.

Aplica a las solicitudes nuevas desde la puesta en marcha; las que estén en curso terminan por correo.

#### Fuera del alcance

- Queda fuera del alcance aquellos aspectos no contemplados en este documento.
- El cobro de las tasas, que irá en una fase posterior.

## 2. Diseño de la solución

### 2.1 Flujo del proceso

El proceso empieza cuando una unidad registra una solicitud y termina con la solicitud autorizada, denegada o
cancelada.

![Flujo del proceso Solicitudes de autorización – Situación futura (To Be)](diagramas/solicitud.png)

#### Lógica general del flujo

##### Regla común 1 · Plazos

- Los plazos de este documento se cuentan en días hábiles.
- Si un plazo vence en un día no hábil, pasa al siguiente día hábil.

##### Regla común 2 · Cancelar la solicitud

- La unidad solicitante puede cancelar su solicitud en cualquier estado anterior a "Resuelta".
- Al cancelarla, la solicitud pasa al estado "Cancelada" y se envía la notificación de cancelación (NOT-03).

### 2.2 Descripción de actividades

#### ACT-03 Revisar la solicitud

| Campo | Valor |
|---|---|
| Descripción | En este paso, el Área de autorizaciones comprueba que la solicitud está completa y que la documentación es válida.<br>Se llega desde el registro de la solicitud y, si se devolvió, desde su subsanación.<br>Si falta algo, la devuelve a la Unidad solicitante con el motivo; si está completa, la pasa a resolución. |
| Actores | Área de autorizaciones |
| Entrada / Salida | **Entrada:**<br>- Solicitud enviada desde Registrar la solicitud (ACT-02).<br>- Solicitud subsanada desde Subsanar la solicitud (ACT-04).<br>**Salida:**<br>- Solicitud devuelta: Subsanar la solicitud (ACT-04).<br>- Solicitud completa: Resolver la solicitud (ACT-05). |
| Estados de la entrada / Estados de salida | **Entrada:** En revisión / Pendiente de revisar.<br>**Salida** (según la acción seleccionada):<br>- Acción "Devolver" → Pendiente de subsanar / Devuelta.<br>- Acción "Pasar a resolución" → En resolución / Pendiente de resolver. |
| Formas de arranque / Formas de finalización | **Arranque:**<br>- Acción "Enviar" de la Unidad solicitante en Registrar la solicitud (ACT-02).<br>- Acción "Reenviar" de la Unidad solicitante en Subsanar la solicitud (ACT-04), una vez corregido lo que faltaba.<br>**Finalización:**<br>- Acción "Devolver", con el motivo obligatorio: la solicitud pasa a Subsanar la solicitud (ACT-04).<br>- Acción "Pasar a resolución": la solicitud pasa a Resolver la solicitud (ACT-05).<br>- Cancelación de la solicitud por la Unidad solicitante, en cualquier momento (ver regla común "Cancelar la solicitud"). |
| Lógica de asignación | La tarea llega a la bandeja común del Área de autorizaciones y es de quien la abre primero; mientras la tiene abierta, nadie más puede tomarla. |
| Documentos | Memoria de la actividad, plano del espacio. |
| Reglas de negocio | - Para devolver es obligatorio escribir el motivo.<br>- Una solicitud solo puede devolverse dos veces; a la tercera, se resuelve. |
| Notificaciones | NOT-02 Solicitud devuelta. |
| Ejecución esperada | 5 días hábiles desde que llega (ver regla común "Plazos"). |

### 2.3 Diseño de la pantalla / layout

La solución centraliza la gestión de las autorizaciones y se compone de dos apartados:

- **Solicitudes**: registro, revisión y resolución de cada solicitud.
- **Datos maestros**: configuración de los espacios.

#### 2.3.1 Pantallas Solicitudes

##### Bandeja de solicitudes

###### Ejemplo ilustrativo

Caso 1: bandeja con solicitudes en distintos estados.

![Bandeja de solicitudes](../prototipo/capturas/01-bandeja.png)

###### Lógica General

1. Esta pantalla corresponde a la página principal del apartado "Solicitudes".
2. La tabla incluye las siguientes columnas:
   - NÚMERO: identificador de la solicitud, en formato de vínculo; al pulsarlo, se abre la solicitud.
   - ESTADO: estado actual de la solicitud.
3. La tabla incluye paginación, mostrando un máximo de 10 solicitudes por página.

###### Filtros

1. Estado: desplegable de selección múltiple. Valor por defecto: "Todos".

###### Reglas de Validación

1. Cancelar una solicitud: antes de ejecutarse, se muestra el mensaje de confirmación "¿Seguro que quieres cancelar
   esta solicitud?".

##### Nueva solicitud

###### Lógica General

1. El modal "Nueva solicitud" se abre al pulsar el botón "Nueva solicitud".
2. El modal incluye el campo Motivo: área de texto libre.

###### Reglas de Validación

1. Motivo: campo obligatorio, de 500 caracteres como máximo.
   - Si está vacío: "Debes indicar el motivo.".

#### 2.3.2 Pantallas Datos maestros

##### Espacios

###### Lógica General

1. Esta pantalla corresponde a la lista de espacios que se pueden pedir.

### 2.4 Otras consideraciones

#### 2.4.1 Roles y permisos

##### Descripción general

Los roles deciden qué información ve cada persona y qué acciones puede hacer en las solicitudes.

##### Roles

| Rol | Descripción | Dónde se define |
|---|---|---|
| Unidad solicitante | Registra la solicitud y la subsana. | Sistema (quien crea la solicitud) |
| Área de autorizaciones | Revisa las solicitudes. | Datos maestros → Grupos |

##### Matriz de permisos

| Acción | Unidad solicitante | Área de autorizaciones |
|---|---|---|
| Solicitudes | | |
| Ver solicitudes | ✓* | ✓ |
| Crear solicitud | ✓ | |
| Datos maestros | | |
| Gestionar espacios | | ✓ |

\*Ver solicitudes: la unidad solicitante solo ve las de su unidad.

#### 2.4.2 Notificaciones por correo

| ID | Comunicación | Disparador | Destinatarios | Asunto | Cuerpo |
|---|---|---|---|---|---|
| NOT-02 | Solicitud devuelta | El área devuelve la solicitud (ACT-03) | Unidad solicitante | Autorizaciones – [Número] – Solicitud devuelta | Buenos días.<br>La solicitud [Número] se ha devuelto por este motivo: "[Motivo]".<br>Puede corregirla a través del siguiente enlace: [Enlace a la solicitud]. |

### 2.5 Métricas y KPIs

| Indicador | As Is horas | As Is FTE | To Be horas | To Be FTE | Reducción % |
|---|---|---|---|---|---|
| Tiempo de esfuerzo manual dedicado al proceso al año | 3.200 | 2 | 1.100 | 0,7 | 65 % |

| Indicador | As Is | To Be | Reducción % |
|---|---|---|---|
| Tiempo de ciclo del proceso (Lead Time) | 15 días | 5 días | pendiente de confirmar |

### 2.6 Periodo de estabilización

Teniendo en cuenta que se trata de un proceso **mensual** se establece un **período de estabilización de 3 meses**.
