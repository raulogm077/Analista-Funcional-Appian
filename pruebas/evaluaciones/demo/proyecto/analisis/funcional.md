# Préstamo de equipos audiovisuales — Diseño funcional

Versión: 1.1 · Estado: en validación

## 1. Objetivo y alcance

Hoy los equipos audiovisuales se piden por correo al almacén de medios y los préstamos se apuntan en una hoja de cálculo. Se pierden peticiones y nadie sabe qué equipo está prestado. <!-- ✅ FU-01 00:00:40 -->

La aplicación sirve para consultar el catálogo de equipos, pedir un préstamo, aprobarlo y llevar la entrega y la recogida de cada equipo. Cada persona ve en todo momento en qué estado están sus préstamos.

Queda fuera de esta fase la ampliación de un préstamo en curso, hasta que se decida cómo se hace (pendiente: PC-01).

Términos que se usan con un significado preciso:

| Término | Significa |
|---|---|
| Equipo | Un aparato del almacén que se presta: proyector, cámara, micrófono, portátil o pantalla |
| Préstamo | La petición de un equipo para unas fechas, desde que se pide hasta que se devuelve |
| Almacén de medios | El servicio que guarda, entrega y recoge los equipos |

## 2. Perfiles

| Perfil | Quién es | Qué hace en la aplicación |
|---|---|---|
| Solicitante | Cualquier persona de la organización que necesita un equipo | Consulta el catálogo, pide préstamos y sigue los suyos |
| Responsable de área | Responsable del área de quien pide el equipo | Aprueba o rechaza los préstamos de su área |
| Almacén de medios | Personal del almacén de medios audiovisuales | Entrega y recoge los equipos y consulta su ficha |

## 3. Proceso

### 3.1 Préstamo de un equipo

**ACT-01 — Solicitar préstamo** <!-- ✅ FU-01 00:04:40 -->

| Quién | Empieza cuando | Pantalla | Plazo |
|---|---|---|---|
| Solicitante | Necesita un equipo | PAN-02 | — |

Elige el equipo y las fechas y envía la solicitud. Pasa a «Solicitado» y el responsable de su área recibe la tarea de aprobarla (AV-01).

**ACT-02 — Aprobar préstamo** <!-- ✅ FU-01 00:07:00 -->

| Quién | Empieza cuando | Pantalla | Plazo |
|---|---|---|---|
| Responsable de área | Llega una solicitud de su área | PAN-04 | 2 días hábiles |

Decide si presta el equipo.
- Si lo aprueba, pasa a «Aprobado» y el almacén recibe la tarea de entregarlo (AV-02).
- Si lo rechaza, pasa a «Rechazado» y el solicitante recibe AV-03 con el comentario.

**ACT-03 — Entregar equipo** <!-- ✅ FU-01 00:09:20 -->

| Quién | Empieza cuando | Pantalla | Plazo |
|---|---|---|---|
| Almacén de medios | Llega la fecha de inicio de un préstamo aprobado | PAN-05 | El día de inicio |

Entrega el equipo y lo anota. El préstamo pasa a «En préstamo» y el equipo, a «Prestado».

**ACT-04 — Recordar la devolución** <!-- ✅ FU-01 00:10:55 -->

| Quién | Empieza cuando | Pantalla | Plazo |
|---|---|---|---|
| Aplicación | Falta un día para la fecha de devolución | — | El día antes |

Envía al solicitante el recordatorio AV-04.

**ACT-05 — Recoger equipo** <!-- ✅ FU-01 00:12:10 -->

| Quién | Empieza cuando | Pantalla | Plazo |
|---|---|---|---|
| Almacén de medios | El solicitante devuelve el equipo | PAN-05 | — |

Recoge el equipo y anota si vuelve correcto o con daños. El préstamo pasa a «Devuelto».
- Si vuelve correcto, el equipo queda «Disponible».
- Si vuelve con daños, escribe qué le pasa y el equipo pasa a «En reparación».

### 3.2 Estados del préstamo

| Estado | Qué significa |
|---|---|
| Solicitado | Espera la decisión del responsable de área |
| Aprobado | El almacén lo entregará el día de inicio |
| Rechazado | El responsable no lo aprobó |
| En préstamo | El solicitante tiene el equipo |
| Devuelto | El almacén ha recogido el equipo |

| De | A | Quién | Paso |
|---|---|---|---|
| Solicitado | Aprobado | Responsable de área | ACT-02 |
| Solicitado | Rechazado | Responsable de área | ACT-02 |
| Aprobado | En préstamo | Almacén de medios | ACT-03 |
| En préstamo | Devuelto | Almacén de medios | ACT-05 |

### 3.3 Escenarios

**ESC-01 — Préstamo de un proyector** <!-- 🔶 FU-01 -->

Una persona del área de Formación pide un proyector para un curso de tres días. Su responsable lo aprueba esa misma mañana. El almacén se lo entrega el primer día, ella recibe el recordatorio la víspera de la devolución y lo devuelve sin daños.

Pasos: ACT-01, ACT-02, ACT-03, ACT-04, ACT-05.

**ESC-02 — Préstamo rechazado** <!-- 🔶 FU-01 -->

Una persona pide una cámara para una grabación que no es de su área. El responsable lo rechaza con el comentario «Pídela a través del área de Comunicación» y ella recibe el aviso.

Pasos: ACT-01, ACT-02.

**ESC-03 — El equipo vuelve con daños** <!-- 🔶 FU-01 -->

Un micrófono vuelve con el cable roto. El almacén lo recoge, anota el daño y el micrófono pasa a «En reparación», así que no aparece disponible en el catálogo.

Pasos: ACT-03, ACT-05.

## 4. Funcionalidades

### Catálogo

**HU-01 — Consultar el catálogo de equipos** <!-- ✅ FU-01 00:03:00 -->

| Perfil | Pantalla | Paso | Prioridad |
|---|---|---|---|
| Solicitante | PAN-01 | — | Imprescindible |

Como solicitante, quiero ver qué equipos hay y si están libres para pedir el que me sirve.

Se acepta si:
- `HU-01.1` La lista enseña el nombre, la categoría y el estado de cada equipo.
- `HU-01.2` Se puede buscar por nombre y filtrar por categoría y por estado.

**HU-02 — Consultar la ficha de un equipo** <!-- ✅ FU-01 00:16:25 -->

| Perfil | Pantalla | Paso | Prioridad |
|---|---|---|---|
| Almacén de medios | PAN-06 | — | Deseable |

Como almacén de medios, quiero ver los datos de un equipo y sus préstamos para saber dónde está y cuánto se usa.

Se acepta si:
- `HU-02.1` La ficha enseña el código, la categoría, el estado y la ubicación del equipo.
- `HU-02.2` La ficha enseña los préstamos del equipo, del más reciente al más antiguo.

### Préstamos

**HU-03 — Solicitar un préstamo** <!-- ✅ FU-01 00:04:40 -->

| Perfil | Pantalla | Paso | Prioridad |
|---|---|---|---|
| Solicitante | PAN-02 | ACT-01 | Imprescindible |

Como solicitante, quiero pedir un equipo para unas fechas para no tener que escribir al almacén.

Se aplica RB-01.

Se acepta si:
- `HU-03.1` Sin equipo o sin fechas no se envía y aparece «Indique el equipo y las fechas».
- `HU-03.2` La fecha de devolución no puede ser anterior a la de inicio ni estar a más de 15 días naturales de ella. <!-- ✅ FU-01 00:05:30 -->
- `HU-03.3` Solo se pueden elegir equipos «Disponibles» en esas fechas.
- `HU-03.4` Al enviarla recibe un número con la forma PRE-2026-0001 y queda «Solicitado».

**HU-04 — Consultar mis préstamos** <!-- ✅ FU-01 00:13:50 -->

| Perfil | Pantalla | Paso | Prioridad |
|---|---|---|---|
| Solicitante | PAN-03 | — | Imprescindible |

Como solicitante, quiero ver mis préstamos y su estado para no tener que preguntar al almacén.

Se aplica RB-01.

Se acepta si:
- `HU-04.1` La lista solo enseña los préstamos de quien entra.
- `HU-04.2` Cada fila enseña el número, el equipo, desde cuándo, hasta cuándo y el estado.

**HU-05 — Aprobar o rechazar un préstamo** <!-- ✅ FU-01 00:07:00 -->

| Perfil | Pantalla | Paso | Prioridad |
|---|---|---|---|
| Responsable de área | PAN-04 | ACT-02 | Imprescindible |

Como responsable de área, quiero decidir sobre los préstamos de mi área para que el almacén sepa qué entregar.

Se acepta si:
- `HU-05.1` La tarea solo llega al responsable del área de quien pide.
- `HU-05.2` Al aprobarlo pasa a «Aprobado» y el almacén recibe AV-02.
- `HU-05.3` Al rechazarlo pasa a «Rechazado» y el solicitante recibe AV-03 con el comentario. <!-- ✅ FU-01 00:08:10 -->

### Entrega y recogida

**HU-06 — Entregar un equipo** <!-- ✅ FU-01 00:09:20 -->

| Perfil | Pantalla | Paso | Prioridad |
|---|---|---|---|
| Almacén de medios | PAN-05 | ACT-03 | Imprescindible |

Como almacén de medios, quiero anotar la entrega para saber qué equipos están fuera.

Se acepta si:
- `HU-06.1` Solo se entrega un préstamo «Aprobado».
- `HU-06.2` Al entregarlo, el préstamo pasa a «En préstamo» y el equipo, a «Prestado».

**HU-07 — Recoger un equipo** <!-- ✅ FU-01 00:12:10 -->

| Perfil | Pantalla | Paso | Prioridad |
|---|---|---|---|
| Almacén de medios | PAN-05 | ACT-05 | Imprescindible |

Como almacén de medios, quiero anotar cómo vuelve cada equipo para mandar a reparar los que tienen daños.

Se acepta si:
- `HU-07.1` Hay que indicar si el equipo vuelve «Correcto» o «Con daños»; con daños, las observaciones son obligatorias.
- `HU-07.2` Al recogerlo, el préstamo pasa a «Devuelto» y el equipo, a «Disponible» o, con daños, a «En reparación».

### Reglas comunes

| ID | Regla | Historias |
|---|---|---|
| RB-01 | Cada solicitante ve solo sus préstamos; el responsable de área, los de su área; el almacén de medios, todos. | HU-03, HU-04 <!-- ✅ FU-01 00:15:05 --> |

## 5. Pantallas

**PAN-01 — Catálogo de equipos** <!-- ✅ FU-01 00:03:00 -->

![PAN-01 Catálogo de equipos](../prototipo/capturas/01-catalogo.png)

Lista de los equipos del almacén. Es la página de inicio de todos los perfiles.

| Parte | Qué permite | Quién |
|---|---|---|
| Lista | Ver el nombre, la categoría y el estado de cada equipo, y abrir su ficha | Todos |
| Filtros | Buscar por nombre y filtrar por categoría y por estado | Todos |
| Solicitar préstamo | Empezar una solicitud | Solicitante |

Historias: HU-01.

**PAN-02 — Solicitar préstamo** <!-- 🔒 FU-01 00:04:40; FU-02 -->

![PAN-02 Solicitar préstamo](../prototipo/capturas/02-solicitar.png)

Formulario de la solicitud. Se abre con «Solicitar préstamo» desde el catálogo.

| Parte | Qué permite | Quién |
|---|---|---|
| Equipo | Elegir uno de los equipos disponibles | Solicitante |
| Fechas | Escribir la fecha de inicio y la de devolución | Solicitante |
| Motivo y lugar de uso | Explicar para qué se pide y dónde se va a usar | Solicitante |
| Botones | Enviar la solicitud o cancelar | Solicitante |

Historias: HU-03.

**PAN-03 — Mis préstamos** <!-- ✅ FU-01 00:13:50 -->

![PAN-03 Mis préstamos](../prototipo/capturas/03-mis-prestamos.png)

Lista de los préstamos de quien entra.

| Parte | Qué permite | Quién |
|---|---|---|
| Lista | Ver el número, el equipo, desde, hasta y el estado de cada préstamo | Solicitante |

Historias: HU-04.

**PAN-04 — Aprobar préstamo** <!-- ✅ FU-01 00:07:00 -->

![PAN-04 Aprobar préstamo](../prototipo/capturas/04-aprobar.png)

Tarea del responsable de área. Se abre desde su bandeja de tareas.

| Parte | Qué permite | Quién |
|---|---|---|
| Datos del préstamo | Ver el equipo, quién lo pide, las fechas y el motivo | Responsable de área |
| Decisión | Aprobar o rechazar, con un comentario | Responsable de área |

Historias: HU-05.

**PAN-05 — Entregar y recoger equipo** <!-- 🔒 FU-01 00:09:20; FU-02 -->

![PAN-05 Entregar y recoger equipo](../prototipo/capturas/05-entregar.png)

Tarea del almacén de medios. Se abre desde su bandeja de tareas el día de inicio y cuando se devuelve el equipo.

| Parte | Qué permite | Quién |
|---|---|---|
| Datos del préstamo | Ver el equipo, quién lo tiene y las fechas | Almacén de medios |
| Entrega | Confirmar que se entrega el equipo | Almacén de medios |
| Recogida | Indicar si vuelve correcto o con daños, con observaciones | Almacén de medios |

Historias: HU-06, HU-07.

**PAN-06 — Ficha del equipo** <!-- ✅ FU-01 00:16:25 -->

![PAN-06 Ficha del equipo](../prototipo/capturas/06-equipo.png)

Todo lo de un equipo. Se abre desde el catálogo.

| Parte | Qué permite | Quién |
|---|---|---|
| Resumen | Ver el código, la categoría, el estado y la ubicación | Almacén de medios |
| Préstamos | Ver los préstamos del equipo | Almacén de medios |

Historias: HU-02.

## 6. Información que gestiona

### 6.1 Préstamo

Unos 2.000 al año. Se conservan tres años. <!-- ✅ FU-01 00:17:55 -->

| Dato | Qué significa | Formato | Obligatorio | Dónde se ve |
|---|---|---|---|---|
| Número | Identifica el préstamo; lo pone la aplicación al enviarlo | PRE-AAAA-nnnn | Automático | PAN-03, PAN-04 |
| Equipo | El equipo que se pide | Equipo del catálogo | Sí | PAN-02, PAN-03, PAN-04, PAN-05 |
| Solicitante | Quién lo pide | Persona | Automático | PAN-04, PAN-05 |
| Área | Área de quien lo pide | Lista de áreas | Automático | PAN-04 |
| Fecha de inicio | Día en que se entrega el equipo | Fecha | Sí | PAN-02, PAN-03, PAN-04, PAN-05 |
| Fecha de devolución | Día en que se devuelve | Fecha, hasta 15 días después del inicio | Sí | PAN-02, PAN-03, PAN-04, PAN-05 |
| Motivo | Para qué se pide | Texto, hasta 500 caracteres | Sí | PAN-02, PAN-04 |
| Lugar de uso | Dónde se va a usar | Texto, hasta 200 caracteres | Sí | PAN-02, PAN-04 |
| Estado | Punto del proceso en que está (3.2) | Lista de estados | Automático | PAN-03, PAN-04 |
| Comentario del responsable | Por qué se aprueba o se rechaza | Texto, hasta 500 caracteres | No | PAN-04 |
| Estado al devolver | Si el equipo vuelve correcto o con daños | Correcto o Con daños | Al recoger | PAN-05 |
| Observaciones de la recogida | Qué daños tiene el equipo | Texto, hasta 1.000 caracteres | Si vuelve con daños | PAN-05 |

### 6.2 Equipo

Unos 120. Se dan de baja cuando se retiran, pero se conservan con sus préstamos. <!-- ✅ FU-01 00:02:05 -->

| Dato | Qué significa | Formato | Obligatorio | Dónde se ve |
|---|---|---|---|---|
| Código | Identifica el equipo; es la etiqueta que lleva pegada | Texto, hasta 20 caracteres | Sí | PAN-01, PAN-06 |
| Nombre | Marca y modelo | Texto, hasta 120 caracteres | Sí | PAN-01, PAN-02, PAN-06 |
| Categoría | Clase de equipo | Lista de categorías | Sí | PAN-01, PAN-06 |
| Estado del equipo | Si se puede prestar | Disponible, Prestado o En reparación | Automático | PAN-01, PAN-06 |
| Ubicación | Dónde lo guarda el almacén | Texto, hasta 100 caracteres | Sí | PAN-06 |
| Última revisión | Fecha de la última revisión técnica | Fecha | No | No se muestra: la usa el almacén para planificar las revisiones |

Un equipo tiene cero o más préstamos; cada préstamo es de un solo equipo.

### 6.3 Listas de valores

| Lista | Valores | Quién la mantiene |
|---|---|---|
| Categoría | Proyector, Cámara, Micrófono, Portátil, Pantalla | Almacén de medios |
| Áreas | Las del directorio corporativo (INT-01) | Directorio corporativo |

## 7. Avisos

| ID | Cuándo | A quién | Qué dice | Cómo llega |
|---|---|---|---|---|
| AV-01 | Se envía una solicitud | Responsable de área | «Nueva solicitud de préstamo PRE-… pendiente de aprobar» | Tarea y correo <!-- ✅ FU-01 00:07:00 --> |
| AV-02 | Se aprueba un préstamo | Almacén de medios | «Préstamo PRE-… aprobado: entrega el …» | Tarea y correo <!-- ✅ FU-01 00:09:20 --> |
| AV-03 | Se rechaza un préstamo | Solicitante | «Su préstamo PRE-… no se ha aprobado», con el comentario | Correo <!-- ✅ FU-01 00:08:10 --> |
| AV-04 | Falta un día para la fecha de devolución | Solicitante | «Recuerde devolver mañana el equipo del préstamo PRE-…» | Correo <!-- ✅ FU-01 00:10:55 --> |

## 8. Documentos e informes

No hay.

## 9. Relación con otros sistemas

| ID | Sistema | Qué se intercambia | Cuándo | Si falla |
|---|---|---|---|---|
| INT-01 | Directorio corporativo | Personas y áreas | Cada noche | Se usa la copia del día anterior <!-- ✅ FU-01 00:19:05 --> |

## 10. Condiciones de uso

- Unas 400 personas; unos 2.000 préstamos al año y 120 equipos. <!-- ✅ FU-01 00:17:55 -->
- Los préstamos se conservan tres años.
- Se cargan al empezar los 120 equipos de la hoja de cálculo del almacén.
- Solo en español. No se usa desde el móvil ni la usan personas de fuera de la organización.
- Los plazos de aprobación se cuentan en días hábiles y los de préstamo, en días naturales.

## 11. Pendiente de confirmar

| ID | Pregunta | Opciones | A quién | Afecta a |
|---|---|---|---|---|
| PC-01 | ¿Se puede ampliar un préstamo que está en curso? | Sí, pidiendo una nueva fecha de devolución / No, se pide otro préstamo | Almacén de medios | 1, ACT-05, HU-04 <!-- ❓ FU-01 00:20:15 --> |

## Anexo. Quién puede hacer qué

<!-- Lo genera indice.py derivadas a partir de las pantallas (apartado 5); no se edita a mano. -->

| Pantalla y parte | Solicitante | Responsable de área | Almacén de medios |
|---|---|---|---|
| PAN-01 Catálogo de equipos · Lista | ✔ | ✔ | ✔ |
| PAN-01 Catálogo de equipos · Filtros | ✔ | ✔ | ✔ |
| PAN-01 Catálogo de equipos · Solicitar préstamo | ✔ |  |  |
| PAN-02 Solicitar préstamo · Equipo | ✔ |  |  |
| PAN-02 Solicitar préstamo · Fechas | ✔ |  |  |
| PAN-02 Solicitar préstamo · Motivo y lugar de uso | ✔ |  |  |
| PAN-02 Solicitar préstamo · Botones | ✔ |  |  |
| PAN-03 Mis préstamos · Lista | ✔ |  |  |
| PAN-04 Aprobar préstamo · Datos del préstamo |  | ✔ |  |
| PAN-04 Aprobar préstamo · Decisión |  | ✔ |  |
| PAN-05 Entregar y recoger equipo · Datos del préstamo |  |  | ✔ |
| PAN-05 Entregar y recoger equipo · Entrega |  |  | ✔ |
| PAN-05 Entregar y recoger equipo · Recogida |  |  | ✔ |
| PAN-06 Ficha del equipo · Resumen |  |  | ✔ |
| PAN-06 Ficha del equipo · Préstamos |  |  | ✔ |
