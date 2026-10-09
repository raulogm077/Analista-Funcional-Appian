# Devoluciones de solicitudes — Diseño funcional

Versión: 1.0 · Estado: en validación

## 1. Objetivo y alcance

Hoy el revisor solo puede aprobar o rechazar una solicitud. Si le falta un dato, la rechaza y el gestor tiene que darla de alta otra vez.

Con este cambio, el revisor devuelve la solicitud con un comentario y el gestor la corrige y la reenvía sin perder nada. Los revisores ven además cuántos días laborables lleva esperando cada solicitud.

Queda fuera de este cambio la conexión con el sistema económico, que se revisará aparte. <!-- ✅ FU-03 00:21:40 -->

Términos que se usan con un significado preciso:

| Término | Significa |
|---|---|
| Devolver | Pedir al gestor que corrija la solicitud antes de revisarla otra vez |
| Días pendiente | Días laborables desde el último envío de la solicitud |

## 2. Perfiles

| Perfil | Quién es | Qué hace en la aplicación |
|---|---|---|
| Gestor | Personal que da de alta las solicitudes | Crea, corrige y reenvía solicitudes |
| Revisor | Personal que revisa las solicitudes | Aprueba, rechaza o devuelve solicitudes |

## 3. Proceso

### 3.1 Revisión de una solicitud

**ACT-01 — Revisar solicitud** <!-- ✅ FU-03 00:04:30 -->

| Quién | Empieza cuando | Pantalla | Plazo |
|---|---|---|---|
| Revisor | El gestor envía o reenvía la solicitud | PAN-01 | — |

Lee la solicitud y decide.
- Aprobar o rechazar: termina como hasta ahora.
- Devolver: escribe qué falta y la solicitud pasa al gestor (ACT-02), que recibe el aviso AV-01.

**ACT-02 — Corregir solicitud** <!-- ✅ FU-03 00:09:20 -->

| Quién | Empieza cuando | Pantalla | Plazo |
|---|---|---|---|
| Gestor | El revisor devuelve la solicitud | PAN-02 | — |

Corrige lo que pide el revisor y la reenvía. Vuelve a ACT-01.

### 3.2 Estados de la solicitud

| Estado | Qué significa |
|---|---|
| Borrador | El gestor la está preparando |
| Enviada | Espera la revisión |
| Devuelta | El gestor tiene que corregirla |
| Aprobada | Revisada y aprobada |
| Rechazada | Revisada y rechazada |

| De | A | Quién | Paso |
|---|---|---|---|
| Enviada | Devuelta | Revisor | ACT-01 |
| Devuelta | Enviada | Gestor | ACT-02 |
| Enviada | Aprobada | Revisor | ACT-01 |
| Enviada | Rechazada | Revisor | ACT-01 |

### 3.3 Escenarios

**ESC-01 — Falta el importe** <!-- 🔶 FU-03 -->

Un gestor envía una solicitud de material sin importe. El revisor la devuelve con el comentario «Indica el importe del presupuesto». El gestor lo añade al día siguiente y la reenvía, y el revisor la aprueba.

Pasos: ACT-01, ACT-02, ACT-01.

## 4. Funcionalidades

### Revisión

**HU-01 — Devolver una solicitud para que se corrija** <!-- ✅ FU-03 00:04:30 -->

| Perfil | Pantalla | Paso | Prioridad | Origen |
|---|---|---|---|---|
| Revisor | PAN-01 | ACT-01 | Imprescindible | Nueva |

Como revisor, quiero devolver una solicitud con lo que falta para que el gestor la corrija sin darla de alta otra vez.

Se acepta si:
- `HU-01.1` Sin comentario no se devuelve y aparece «Indica qué falta».
- `HU-01.2` La solicitud pasa a «Devuelta» y el gestor recibe el aviso AV-01 con el comentario.

**HU-02 — Corregir y reenviar una solicitud devuelta** <!-- ✅ FU-03 00:09:20; [FU-01 H-DAT-01] -->

| Perfil | Pantalla | Paso | Prioridad | Origen |
|---|---|---|---|---|
| Gestor | PAN-02 | ACT-02 | Imprescindible | Nueva |

Como gestor, quiero corregir la solicitud devuelta para que siga su revisión con el mismo número.

El gestor no elige el estado: lo cambia la aplicación al reenviarla.

Se acepta si:
- `HU-02.1` El comentario del revisor aparece encima del formulario.
- `HU-02.2` Al reenviarla vuelve a «Enviada» con el mismo número.

### Seguimiento

**HU-03 — Ver los días que lleva pendiente cada solicitud** <!-- ✅ FU-03 00:15:10 -->

| Perfil | Pantalla | Paso | Prioridad | Origen |
|---|---|---|---|---|
| Revisor | PAN-03 | — | Deseable | Nueva |

Como revisor, quiero ver cuántos días laborables lleva esperando cada solicitud para revisar antes las más antiguas.

Se acepta si:
- `HU-03.1` La lista enseña los días laborables desde el último envío de cada solicitud «Enviada».
- `HU-03.2` Las solicitudes «Devuelta» no enseñan días mientras el gestor las corrige.

## 5. Pantallas

**PAN-01 — Revisar solicitud** <!-- ✅ FU-03 00:04:30 -->

Tarea del revisor. Se abre desde su bandeja de tareas.

| Parte | Qué permite | Quién |
|---|---|---|
| Datos | Ver la solicitud | Revisor |
| Decisión | Aprobar, rechazar o devolver con un comentario | Revisor |

Historias: HU-01.

**PAN-02 — Corregir solicitud** <!-- ✅ FU-03 00:09:20 -->

Tarea del gestor. Le llega cuando el revisor le devuelve una solicitud.

| Parte | Qué permite | Quién |
|---|---|---|
| Comentario del revisor | Leer lo que falta | Gestor |
| Datos | Corregir el título y el importe | Gestor |
| Reenviar | Enviar la solicitud otra vez | Gestor |

Historias: HU-02.

**PAN-03 — Panel de solicitudes** <!-- ✅ FU-03 00:15:10 -->

Página de inicio de los revisores.

| Parte | Qué permite | Quién |
|---|---|---|
| Lista | Ver título, estado, gestor y días pendiente | Revisor |

Historias: HU-03.

## 6. Información que gestiona

### 6.1 Solicitud

Unas 150 al año. Los datos que ya tiene no cambian; se añaden dos.

| Dato | Qué significa | Formato | Obligatorio | Dónde se ve |
|---|---|---|---|---|
| Comentario de devolución | Lo que el revisor pide corregir | Texto, hasta 1.000 caracteres | Al devolver | PAN-01, PAN-02 |
| Fecha de envío | Último envío o reenvío | Fecha y hora | Automático | No se muestra: sirve para contar los días pendiente |

### 6.2 Listas de valores

| Lista | Valores | Quién la mantiene |
|---|---|---|
| Estado | Borrador, Enviada, Devuelta, Aprobada, Rechazada | Nadie: cambian con el proceso |

## 7. Avisos

| ID | Cuándo | A quién | Qué dice | Cómo llega |
|---|---|---|---|---|
| AV-01 | El revisor devuelve una solicitud | Gestor que la creó | «Tu solicitud necesita cambios» con el comentario | Tarea y correo <!-- ✅ FU-03 00:09:20 --> |

## 8. Documentos e informes

No hay.

## 9. Relación con otros sistemas

No hay.

## 10. Condiciones de uso

- Los mismos gestores y revisores que hoy, unas 30 personas.
- Unas 150 solicitudes al año.
- Los días pendiente solo cuentan los días laborables de la organización.
- Sin carga de datos: las solicitudes enviadas antes del cambio cuentan desde su fecha de alta.

## 11. Pendiente de confirmar

| ID | Pregunta | Opciones | A quién | Afecta a |
|---|---|---|---|---|
| PC-01 | ¿Quién recibe el correo cuando el revisor aprueba o rechaza una solicitud? | Solo el gestor / El gestor y el buzón de soporte | Responsable de las solicitudes | ACT-01 <!-- ❓ [FU-01 NV-PRO-01] --> |
