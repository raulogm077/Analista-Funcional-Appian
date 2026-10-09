# Ayudas a proyectos culturales de asociaciones — Documento de diseño funcional

| Versión | Fecha | Estado |
|---|---|---|
| 1.0 | 2026-06-19 | Validado por la Dirección de Cultura del Consorcio Cultural de Montelar |

Documento ficticio para las evaluaciones del plugin.

## 1. Objeto

El Consorcio Cultural de Montelar convoca cada año ayudas para proyectos culturales de las asociaciones inscritas en su
registro. Hoy las solicitudes llegan en papel o por correo y el Servicio de Cultura las sigue en hojas de cálculo.

El sistema cubre la convocatoria completa: la solicitud, la revisión de la documentación, la valoración, la resolución,
la justificación y el pago.

Volumen: unas 150 solicitudes por convocatoria, de unas 120 asociaciones inscritas. Las solicitudes se conservan seis
años desde la resolución.

## 2. Roles

| ID | Rol | Descripción |
|---|---|---|
| ROL-01 | Entidad solicitante | Asociación cultural inscrita en el registro del Consorcio. Presenta, subsana y justifica sus solicitudes |
| ROL-02 | Técnico de cultura | Personal del Servicio de Cultura. Revisa la documentación y la justificación |
| ROL-03 | Comisión de valoración | Tres personas del Consorcio que puntúan los proyectos |
| ROL-04 | Jefatura del Servicio de Cultura | Resuelve la concesión o la denegación de cada solicitud |
| ROL-05 | Intervención | Fiscaliza los pagos. Consulta las solicitudes sin modificarlas |

## 3. Procedimiento

| ID | Paso | Responsable | Plazo | Descripción |
|---|---|---|---|---|
| PR-01 | Presentar solicitud | Entidad solicitante | El que fije la convocatoria | La entidad rellena la solicitud, adjunta la documentación y la envía. Pasa a «Presentada» (NT-01) |
| PR-02 | Revisar documentación | Técnico de cultura | 10 días hábiles | El técnico comprueba que están la memoria del proyecto y el presupuesto detallado y que los datos coinciden con ellos. Si está completa, pasa a «En valoración» (NT-05). Si falta algo, emite un requerimiento (PR-03) |
| PR-03 | Subsanar | Entidad solicitante | 10 días hábiles desde el requerimiento | La entidad completa lo que se le pide y la reenvía; vuelve a PR-02. Si no subsana en plazo, la solicitud pasa a «Desistida» y termina |
| PR-04 | Valorar | Comisión de valoración | 15 días hábiles | Cada miembro de la comisión puntúa el proyecto según RN-03 |
| PR-05 | Resolver | Jefatura del Servicio de Cultura | 10 días hábiles | La Jefatura concede la ayuda, con su importe, o la deniega, con su motivo (NT-03) |
| PR-06 | Justificar | Entidad solicitante | Hasta 2 meses después de terminar la actividad | La entidad presenta la memoria final de la actividad y las facturas (NT-04, NT-06) |
| PR-07 | Revisar justificación | Técnico de cultura | 20 días hábiles | Si la justificación es conforme, la solicitud pasa a «Justificada» y se ordena el pago. Si no lo es, pasa a «Reintegro» |
| PR-08 | Pagar | Tesorería, fuera del sistema | — | Tesorería paga en el sistema económico. El técnico marca la solicitud como «Pagada» |

### 3.1 Estados de la solicitud

| Estado | Descripción |
|---|---|
| Borrador | La entidad la está preparando; solo la ve ella |
| Presentada | Enviada; pendiente de revisar |
| En subsanación | Con un requerimiento abierto |
| En valoración | Completa; la puntúa la comisión |
| Concedida | Resuelta a favor, con importe |
| Denegada | Resuelta en contra, con motivo |
| Desistida | La entidad no subsanó en plazo |
| Justificada | Justificación conforme; pendiente de pago |
| Reintegro | Justificación no conforme |
| Pagada | Pagada por Tesorería |

## 4. Requisitos funcionales

**RF-01 — Presentar una solicitud** (Entidad solicitante · IU-02)

El sistema permitirá a la entidad presentar su solicitud con estos datos: CIF de la entidad, nombre del proyecto,
descripción, fecha de inicio y fecha de fin de la actividad, presupuesto total, importe solicitado, persona de contacto
y correo de contacto, que son obligatorios, y teléfono de contacto, que es opcional. Adjuntará la memoria del proyecto y
el presupuesto detallado (RN-06).

Criterios de aceptación:
- Sin un dato obligatorio o sin un documento, la solicitud no se envía.
- Al enviarla recibe un número con la forma AYC-2026-0001, correlativo por año, y la entidad recibe NT-01.
- Se aplican RN-01 y RN-02.

**RF-02 — Guardar la solicitud como borrador** (Entidad solicitante · IU-02)

La entidad puede guardar la solicitud sin terminar y enviarla después. Un borrador solo lo ve la entidad que lo creó.

**RF-03 — Consultar mis solicitudes** (Entidad solicitante · IU-01)

La entidad ve la lista de sus solicitudes con el número, el proyecto, el estado, el importe solicitado y el importe
concedido. Se aplica RN-05.

**RF-04 — Revisar la documentación** (Técnico de cultura · IU-03)

El técnico ve juntos los datos y los documentos de la solicitud. La da por completa o emite un requerimiento con el
texto de lo que falta, que es obligatorio. El requerimiento llega a la entidad con NT-02.

**RF-05 — Subsanar una solicitud** (Entidad solicitante · IU-02)

La entidad ve el texto del requerimiento encima del formulario, corrige la solicitud y la reenvía. La solicitud
conserva su número.

**RF-06 — Valorar un proyecto** (Comisión de valoración · IU-04)

Cada miembro de la comisión puntúa por separado los tres criterios de RN-03 y escribe una observación. Cuando han
puntuado los tres, el sistema calcula la puntuación del proyecto como la media de las tres.

**RF-07 — Resolver una solicitud** (Jefatura del Servicio de Cultura · IU-05)

La Jefatura del Servicio de Cultura concede la ayuda o la deniega. Al conceder indica el importe, que no puede superar
el solicitado. Al denegar, el motivo es obligatorio. La entidad recibe NT-03.

**RF-08 — Justificar una ayuda** (Entidad solicitante · IU-06)

La entidad presenta la memoria final de la actividad y las facturas (RN-06) dentro del plazo de PR-06. El técnico
recibe NT-06.

**RF-09 — Revisar la justificación** (Técnico de cultura · IU-03)

El técnico revisa la memoria final y las facturas y marca la justificación como conforme o no conforme, con su motivo.

**RF-10 — Consultar todas las solicitudes** (Intervención · IU-08)

Intervención ve todas las solicitudes de la convocatoria, salvo los borradores, y las exporta a Excel con los filtros
aplicados. No puede modificar nada.

## 5. Reglas de negocio

| ID | Regla |
|---|---|
| RN-01 | El importe solicitado no puede superar 3.000 € ni el 80 % del presupuesto total del proyecto |
| RN-02 | Cada entidad puede presentar una sola solicitud por convocatoria |
| RN-03 | Criterios de valoración: interés cultural (hasta 40 puntos), alcance y participación (hasta 30) y viabilidad del presupuesto (hasta 30). Se concede con 50 puntos o más, por orden de puntuación hasta agotar el crédito de la convocatoria |
| RN-04 | Los plazos se cuentan en días hábiles con el calendario laboral del Consorcio, salvo el de justificación, que se cuenta en meses |
| RN-05 | Cada entidad ve solo sus solicitudes. El personal del Consorcio (técnicos, comisión, Jefatura e Intervención) ve todas, salvo los borradores |
| RN-06 | Los documentos se adjuntan en PDF, de hasta 10 MB cada uno |

## 6. Notificaciones

| ID | Cuándo | A quién | Contenido | Medio |
|---|---|---|---|---|
| NT-01 | Se presenta una solicitud | Entidad solicitante | «Hemos recibido su solicitud AYC-…» | Correo |
| NT-02 | El técnico emite un requerimiento | Entidad solicitante | «Su solicitud AYC-… necesita documentación», con el texto del requerimiento | Correo |
| NT-03 | Se resuelve una solicitud | Entidad solicitante | «Resolución de su solicitud AYC-…», con el importe o el motivo | Correo |
| NT-04 | Faltan 15 días naturales para que venza el plazo de justificación | Entidad solicitante | «Le quedan 15 días para justificar la ayuda AYC-…» | Correo |
| NT-05 | Una solicitud pasa a «En valoración» | Comisión de valoración | «Nueva solicitud para valorar: AYC-…» | Tarea y correo |
| NT-06 | La entidad presenta la justificación | Técnico de cultura | «Justificación presentada: AYC-…» | Tarea y correo |

## 7. Interfaces de usuario

| ID | Interfaz | Quién la usa | Qué permite |
|---|---|---|---|
| IU-01 | Mis solicitudes | Entidad solicitante | Ver sus solicitudes y abrir cada una; empezar una nueva |
| IU-02 | Solicitud | Entidad solicitante | Rellenar, guardar como borrador, enviar y subsanar |
| IU-03 | Revisar solicitud | Técnico de cultura | Revisar la documentación y la justificación |
| IU-04 | Valorar proyecto | Comisión de valoración | Puntuar los criterios y escribir la observación |
| IU-05 | Resolver | Jefatura del Servicio de Cultura | Conceder con importe o denegar con motivo |
| IU-06 | Justificar | Entidad solicitante | Adjuntar la memoria final y las facturas |
| IU-07 | Ficha de la solicitud | Todos | Ver los datos, los documentos, la valoración y el historial |
| IU-08 | Todas las solicitudes | Personal del Consorcio e Intervención | Buscar, filtrar y exportar a Excel |

## 8. Datos de la solicitud

| Dato | Tipo | Obligatorio |
|---|---|---|
| Número | AYC-AAAA-nnnn, lo pone el sistema | Automático |
| CIF de la entidad | Texto | Sí |
| Nombre del proyecto | Texto, hasta 150 caracteres | Sí |
| Descripción | Texto, hasta 4.000 caracteres | Sí |
| Fecha de inicio y fecha de fin | Fecha | Sí |
| Presupuesto total | Importe en euros | Sí |
| Importe solicitado | Importe en euros | Sí |
| Persona de contacto | Texto | Sí |
| Correo de contacto | Correo electrónico | Sí |
| Teléfono de contacto | Texto | No |
| Puntuación | De 0 a 100, la calcula el sistema | Automático |
| Importe concedido | Importe en euros | Al conceder |
| Motivo de denegación | Texto | Al denegar |
| Estado | Uno de los de 3.1 | Automático |
