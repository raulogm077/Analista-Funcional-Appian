# Solicitudes de material — Diseño funcional

Versión: 1.0 · Estado: entregado

## 1. Objetivo y alcance

Hoy cada centro pide el material de oficina por correo a Servicios generales, que lo apunta en una hoja de cálculo. Se pierden peticiones y nadie sabe cuáles están aprobadas. <!-- ✅ FU-01 00:00:40 -->

La aplicación sirve para pedir el material, revisar cada solicitud y aprobarla, rechazarla o devolverla para que se corrija. Cada gestor ve en todo momento en qué estado están las suyas.

Queda fuera la compra al proveedor: Servicios generales la sigue haciendo en el sistema económico. <!-- ✅ FU-01 00:08:10 -->

Términos que se usan con un significado preciso:

| Término | Significa |
|---|---|
| Solicitud | La petición de material de oficina de un centro |
| Devolver | Pedir al gestor que corrija la solicitud antes de revisarla otra vez |

## 2. Perfiles

| Perfil | Quién es | Qué hace en la aplicación |
|---|---|---|
| Gestor | Personal de cada centro que pide el material | Crea, corrige y reenvía solicitudes |
| Revisor | Personal de Servicios generales que revisa las solicitudes | Aprueba, rechaza o devuelve solicitudes |

## 3. Proceso

### 3.1 Solicitud de material

**ACT-01 — Registrar solicitud** <!-- ✅ FU-01 00:01:30 -->

| Quién | Empieza cuando | Pantalla | Plazo |
|---|---|---|---|
| Gestor | El centro necesita material | PAN-02 | — |

Escribe el título, el importe y la descripción y envía la solicitud. Pasa a «Enviada» y los revisores reciben la tarea de revisarla (AV-01).

**ACT-02 — Revisar solicitud** <!-- ✅ FU-01 00:03:10 -->

| Quién | Empieza cuando | Pantalla | Plazo |
|---|---|---|---|
| Revisor | El gestor envía o reenvía la solicitud | PAN-03 | 3 días laborables |

Lee la solicitud y decide.
- Aprobar o rechazar: la solicitud termina y el gestor recibe el aviso AV-02.
- Devolver: escribe qué falta y la solicitud pasa al gestor (ACT-03), que recibe el aviso AV-03.

**ACT-03 — Corregir solicitud** <!-- ✅ FU-01 00:05:20 -->

| Quién | Empieza cuando | Pantalla | Plazo |
|---|---|---|---|
| Gestor | El revisor devuelve la solicitud | PAN-02 | — |

Corrige lo que pide el revisor y la reenvía con el mismo número. Vuelve a ACT-02.

### 3.2 Estados de la solicitud

| Estado | Qué significa |
|---|---|
| Borrador | El gestor la está preparando y nadie más la ve |
| Enviada | Espera la revisión |
| Devuelta | El gestor tiene que corregirla |
| Aprobada | Revisada y aprobada |
| Rechazada | Revisada y rechazada |

| De | A | Quién | Paso |
|---|---|---|---|
| Borrador | Enviada | Gestor | ACT-01 |
| Enviada | Devuelta | Revisor | ACT-02 |
| Devuelta | Enviada | Gestor | ACT-03 |
| Enviada | Aprobada | Revisor | ACT-02 |
| Enviada | Rechazada | Revisor | ACT-02 |

### 3.3 Escenarios

**ESC-01 — Falta el tamaño de los folios** <!-- 🔶 FU-01 -->

Un gestor envía una solicitud de 40 paquetes de folios sin decir de qué tamaño. El revisor la devuelve con el comentario «Indica el tamaño de los folios». El gestor lo añade al día siguiente y la reenvía, y el revisor la aprueba.

Pasos: ACT-01, ACT-02, ACT-03, ACT-02.

## 4. Funcionalidades

### Solicitud

**HU-01 — Registrar una solicitud** <!-- ✅ FU-01 00:01:30 -->

| Perfil | Pantalla | Paso | Prioridad |
|---|---|---|---|
| Gestor | PAN-02 | ACT-01 | Imprescindible |

Como gestor, quiero pedir el material en la aplicación para no tener que mandarlo por correo.

La solicitud se puede guardar como borrador y enviar después.

Se acepta si:
- `HU-01.1` Sin título o sin importe no se envía y aparece «Indica el título y el importe».
- `HU-01.2` El importe admite céntimos y llega hasta 6.000 €; si se pasa, aparece «El importe máximo es 6.000 €». <!-- ✅ FU-01 00:02:20 -->
- `HU-01.3` Al enviarla recibe un número con la forma DEM-2026-0001, correlativo por año. <!-- ✅ FU-01 00:04:30 -->

**HU-02 — Corregir y reenviar una solicitud devuelta** <!-- ✅ FU-01 00:05:20 -->

| Perfil | Pantalla | Paso | Prioridad |
|---|---|---|---|
| Gestor | PAN-02 | ACT-03 | Imprescindible |

Como gestor, quiero corregir la solicitud devuelta para que siga su revisión con el mismo número.

Se acepta si:
- `HU-02.1` El comentario del revisor aparece encima del formulario.
- `HU-02.2` Al reenviarla vuelve a «Enviada» con el mismo número.

### Revisión

**HU-03 — Revisar una solicitud** <!-- ✅ FU-01 00:03:10 -->

| Perfil | Pantalla | Paso | Prioridad |
|---|---|---|---|
| Revisor | PAN-03 | ACT-02 | Imprescindible |

Como revisor, quiero aprobar, rechazar o devolver cada solicitud desde una tarea para contestar a los centros sin correos.

Se acepta si:
- `HU-03.1` La tarea aparece a todos los revisores y desaparece para los demás cuando uno la acepta.
- `HU-03.2` Sin comentario no se devuelve y aparece «Indica qué falta».
- `HU-03.3` Al aprobar o rechazar, el gestor recibe el aviso AV-02; al devolver, el aviso AV-03.

### Seguimiento

**HU-04 — Consultar las solicitudes** <!-- ✅ FU-01 00:06:40 -->

| Perfil | Pantalla | Paso | Prioridad |
|---|---|---|---|
| Gestor, Revisor | PAN-01 | — | Imprescindible |

Como gestor o revisor, quiero ver las solicitudes y su estado para no tener que preguntar por ellas.

Se acepta si:
- `HU-04.1` El gestor ve solo sus solicitudes; el revisor, todas menos los borradores.
- `HU-04.2` Se puede filtrar por estado y buscar por número o título.

## 5. Pantallas

**PAN-01 — Panel de solicitudes** <!-- ✅ FU-01 00:06:40 -->

![PAN-01 Panel de solicitudes](../prototipo/capturas/PAN-01.png)

Página de inicio de gestores y revisores. Cada uno ve las solicitudes que le corresponden.

| Parte | Qué permite | Quién |
|---|---|---|
| Filtros | Filtrar por estado y buscar por número o título | Gestor, Revisor |
| Lista | Ver número, título, importe, estado y fecha de envío, y abrir la solicitud | Gestor, Revisor |
| Botón «Nueva solicitud» | Empezar una solicitud en PAN-02 | Gestor |

Historias: HU-04.

**PAN-02 — Solicitud** <!-- ✅ FU-01 00:01:30 -->

![PAN-02 Solicitud](../prototipo/capturas/PAN-02.png)

Formulario de la solicitud. Se abre desde el panel o desde la tarea de corregir.

| Parte | Qué permite | Quién |
|---|---|---|
| Comentario del revisor | Leer lo que falta, solo al corregir | Gestor |
| Datos | Escribir título, importe y descripción | Gestor |
| Botones | «Guardar borrador» y «Enviar» | Gestor |

Historias: HU-01, HU-02.

**PAN-03 — Revisar solicitud** <!-- ✅ FU-01 00:03:10 -->

![PAN-03 Revisar solicitud](../prototipo/capturas/PAN-03.png)

Tarea del revisor. Se abre desde su bandeja de tareas.

| Parte | Qué permite | Quién |
|---|---|---|
| Datos | Ver la solicitud | Revisor |
| Decisión | Aprobar, rechazar o devolver con un comentario | Revisor |

Historias: HU-03.

## 6. Información que gestiona

### 6.1 Solicitud

Unas 1.200 al año.

| Dato | Qué significa | Formato | Obligatorio | Dónde se ve |
|---|---|---|---|---|
| Número | Identifica la solicitud; lo pone la aplicación al enviarla | DEM-AAAA-nnnn | Automático | PAN-01, PAN-03 |
| Título | Qué se pide, en una línea | Texto, hasta 120 caracteres | Sí | PAN-01, PAN-02, PAN-03 |
| Importe | Coste estimado del material | Euros con céntimos, hasta 6.000 € | Sí | PAN-01, PAN-02, PAN-03 |
| Descripción | Detalle del material | Texto, hasta 2.000 caracteres | No | PAN-02, PAN-03 |
| Solicitante | Gestor que la creó | Persona | Automático | PAN-01, PAN-03 |
| Estado | Punto del proceso en que está (3.2) | Lista de estados | Automático | PAN-01 |
| Fecha de envío | Último envío o reenvío | Fecha y hora | Automático | PAN-01 |
| Comentario de devolución | Lo que el revisor pide corregir | Texto, hasta 1.000 caracteres | Al devolver | PAN-02, PAN-03 |

### 6.2 Listas de valores

| Lista | Valores | Quién la mantiene |
|---|---|---|
| Estado | Borrador, Enviada, Devuelta, Aprobada, Rechazada | Nadie: cambian con la solicitud |

## 7. Avisos

| ID | Cuándo | A quién | Qué dice | Cómo llega |
|---|---|---|---|---|
| AV-01 | Se envía o se reenvía una solicitud | Revisores | «Solicitud DEM-… pendiente de revisar» | Tarea <!-- ✅ FU-01 00:03:10 --> |
| AV-02 | Se aprueba o se rechaza | Gestor que la creó | «Tu solicitud DEM-… está aprobada» o «… rechazada» | Correo <!-- ✅ FU-01 00:07:30 --> |
| AV-03 | Se devuelve | Gestor que la creó | «Tu solicitud DEM-… necesita cambios», con el comentario | Tarea y correo <!-- ✅ FU-01 00:07:30 --> |

## 8. Documentos e informes

No hay.

## 9. Relación con otros sistemas

No hay.

## 10. Condiciones de uso

- Unas 60 personas de 12 centros; no más de 15 a la vez. <!-- ✅ FU-01 00:09:20 -->
- Unas 1.200 solicitudes al año.
- Los plazos se cuentan en días laborables de la organización.
- Sin carga inicial: las peticiones abiertas en la hoja de cálculo terminan allí.

## 11. Pendiente de confirmar

No hay.
