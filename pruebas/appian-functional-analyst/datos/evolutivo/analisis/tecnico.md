# Devoluciones de solicitudes — Especificación técnica

Versión: 1.0 · Estado: completo

## 0. Entorno

| Dato | Valor | Fuente |
|---|---|---|
| Versión de Appian | 26.6 en preproducción | FU-01 |
| Aplicación | `DEM Gestión de Solicitudes`, prefijo `DEM` | FU-01 |
| Volumen | 152 solicitudes en `DEM_SOLICITUD`; unas 150 al año | FU-01, funcional §10 |
| Usuarios | Unas 30 personas en `DEM Gestores` y `DEM Revisores` | FU-01, funcional §10 |

## 1. Convenciones

| Qué | Convención | Por qué |
|---|---|---|
| Prefijo y nombres | Los de la aplicación: `DEM`, record types y process models con espacios (`DEM Solicitud`), reglas e interfaces en PascalCase (`DEM_ER_IdEstado`) | FU-01 · BP 08 §1 |

## 2. Decisiones técnicas

**DT-01 — Los estados salen de DEM Estado**

| Campo | Contenido |
|---|---|
| **Capa** | Datos |
| **Necesidad** | [FU-02 REF-01], HU-02 |
| **Decisión** | `DEM_ER_IdEstado` da el id de un estado de `DEM Estado`; `DEM_SolicitudForm` deja de enseñar el estado y `DEM_ESTADOS_VALIDOS` se retira |
| **Por qué** | Los valores de una lista viven en un record type de referencia (BP 01 §1.1 · https://docs.appian.com/suite/help/latest/build-best-data-fabric.html#store-lookup-data-in-a-separate-record-type) |
| **Descartada** | Añadir «Devuelta» a la constante: repite el hallazgo |
| **Riesgo** | Ninguno relevante |
| **Depende de** | — |
| **Verificar** | — |
| **Verificado** | No hace falta |

**DT-02 — Devolver es una salida más de la revisión**

| Campo | Contenido |
|---|---|
| **Capa** | Proceso |
| **Necesidad** | HU-01, HU-02, ACT-01, ACT-02 |
| **Decisión** | `DEM Revisar Solicitud` añade la salida «Devolver»: guarda el comentario, pasa a «Devuelta» y asigna PAN-02 al `solicitante` de la solicitud; al reenviar vuelve al nodo «Revisión» |
| **Por qué** | Una tarea se asigna a un grupo o a un usuario guardado en el caso (BP 03 §7 · https://docs.appian.com/suite/help/latest/Process_Node_and_Smart_Service_Properties.html#assignment-tab) |
| **Descartada** | Rechazar y que el gestor dé de alta otra solicitud: es lo que pasa hoy |
| **Riesgo** | Si el `solicitante` ya no está en la organización, la tarea no llega a nadie |
| **Depende de** | — |
| **Verificar** | — |
| **Verificado** | No hace falta |

**DT-03 — Días pendiente con la regla de la aplicación de utilidades**

| Campo | Contenido |
|---|---|
| **Capa** | Lógica |
| **Necesidad** | HU-03 |
| **Decisión** | `DEM_ER_DiasPendiente` llama a `UTL_DiasLaborables` con `fechaEnvio` y hoy; `DEM_Dashboard` añade la columna «Días pendiente» |
| **Por qué** | La lógica que ya existe en otra aplicación se reutiliza en vez de copiarla (BP 04 §1 · https://docs.appian.com/suite/help/latest/expressions-best-practices.html) |
| **Descartada** | Contar los días en `DEM` con las fiestas en una constante: otra lista que mantener |
| **Riesgo** | Si `UTL_DiasLaborables` no cuenta como espera el cliente, los días salen mal |
| **Depende de** | PT-01 |
| **Verificar** | Que `UTL_DiasLaborables` recibe dos fechas y devuelve un número |
| **Verificado** | pendiente (PT-01) |

## 3. Modelo de datos

### 3.1 DEM Solicitud

| Origen | Acceso | Volumen | Eventos | Seguridad |
|---|---|---|---|---|
| Tabla `DEM_SOLICITUD`, que ya existe | El de hoy | 152 filas; unas 150 al año | No | La de hoy |

| Campo | Tipo | Long. | Clave | Único | Oblig. | Por defecto | Uso |
|---|---|---|---|---|---|---|---|
| comentarioDevolucion | Texto | 1000 | — | No | Al devolver | — | Funcional: Comentario de devolución |
| fechaEnvio | Fecha y hora | — | — | No | Al enviar | Ahora | Funcional: Fecha de envío |

Los demás campos siguen como están (FU-01).

### 3.2 Carga inicial y migración

| Origen en la app actual | Destino | Transformación | Volumen | Cómo se verifica |
|---|---|---|---|---|
| — | `DEM_ESTADO` | Fila nueva «Devuelta» | 1 fila | `DEM Estado` tiene 5 filas |
| `DEM_SOLICITUD.fechaAlta` | `DEM_SOLICITUD.fechaEnvio` | Se copia en las que no están en «Borrador» | 152 filas como mucho | Ninguna solicitud enviada queda sin `fechaEnvio` |

## 4. Grupos y seguridad

| Perfil | Grupo | Constante |
|---|---|---|
| Gestor | `DEM Gestores`, que ya existe | — |
| Revisor | `DEM Revisores`, que ya existe | — |

Sin cambios de seguridad: la tarea de corregir va al gestor que creó la solicitud (DT-02).

## 5. Estados y transiciones

«Devuelta» y sus dos transiciones (funcional 3.2) las hace `DEM Revisar Solicitud` (DT-02) con `DEM_ER_IdEstado`.

## 6. Lógica

| Regla | Entradas | Devuelve | Lógica | Pruebas |
|---|---|---|---|---|
| `DEM_ER_IdEstado` | nombre | Número | El id de la fila de `DEM Estado` con ese `label` (DT-01) | «Devuelta» da el id nuevo |
| `DEM_ER_DiasPendiente` | fechaEnvio | Número | `UTL_DiasLaborables` desde `fechaEnvio` hasta hoy (DT-03) | Envío el viernes y consulta el lunes: 1 |

## 7. Interfaces y acciones

| Pantalla | Qué es en Appian | Guarda con | Notas |
|---|---|---|---|
| PAN-01 | `DEM_RevisionForm`, formulario de tarea | `DEM Revisar Solicitud` | Añade «Devolver» y el comentario obligatorio al devolver |
| PAN-02 | `DEM_SolicitudForm`, formulario de tarea | `DEM Revisar Solicitud` | Enseña el comentario y quita la lista «Estado» (DT-01) |
| PAN-03 | `DEM_Dashboard`, página «Panel» del site | — | Columna «Días pendiente» con `DEM_ER_DiasPendiente` |

## 8. Procesos

**DEM Revisar Solicitud** (DT-02).

| Nodo | Qué hace | Asignado a | Plazo y escalado | Escribe | Evento |
|---|---|---|---|---|---|
| Revisión (ACT-01) | Tarea PAN-01 con la salida «Devolver» | `DEM Revisores` | — | decision, comentarioDevolucion | — |
| Marcar devuelta | Escribe «Devuelta» con `DEM_ER_IdEstado` | — | — | estadoId | — |
| Corregir (ACT-02) | Tarea PAN-02 | `solicitante` de la solicitud | — | Datos de la solicitud, fechaEnvio, estadoId | — |

`DEM Alta Solicitud` no cambia: llama a `DEM_INT_NotificarERP` con el estado final, como hoy.

## 9. Avisos

| Aviso | Cómo se hace | Remitente y respuesta | Plantilla |
|---|---|---|---|
| AV-01 | Tarea asignada y correo de la tarea | El de «Avisar solicitante» (PC-01) | Texto plano |

## 10. Integraciones, documentos e IA

No aplica: el cambio no toca integraciones ni documentos. `DEM_INT_NotificarERP` sigue igual.

## 11. Site e informes

`DEM Portal Solicitudes` no cambia: la página «Panel» es PAN-03.

## 12. Volumen y operación

152 solicitudes: sin riesgo de volumen. Los días pendiente dependen del calendario de otra aplicación (PT-01).

## 13. Plan de construcción

| Paso | Objeto | Tipo | Situación | Sustituye a |
|---|---|---|---|---|
| 1 | `DEM Estado` | Record type | Existe | — |
| 1 | `DEM Solicitud` | Record type | Modifica | — |
| 2 | `DEM_ER_IdEstado` | Regla de expresión | Sustituye | `DEM_ESTADOS_VALIDOS` |
| 2 | `UTL_DiasLaborables` | Regla de otra aplicación | Existe | — |
| 2 | `DEM_ER_DiasPendiente` | Regla de expresión | Nuevo | — |
| 3 | `DEM_RevisionForm` | Interfaz | Modifica | — |
| 3 | `DEM_SolicitudForm` | Interfaz | Modifica | — |
| 3 | `DEM_Dashboard` | Interfaz | Modifica | — |
| 4 | `DEM Revisar Solicitud` | Process model | Modifica | — |
| 4 | `DEM_INT_NotificarERP` | Integración | Existe | — |

Manual, en cada entorno: la fila «Devuelta» y la `fechaEnvio` de las solicitudes enviadas (§3.2).

## 14. Pruebas y trazabilidad

| Criterio | Cómo se prueba |
|---|---|
| HU-01.1, HU-01.2 | Devolver sin comentario y con comentario |
| HU-02.1, HU-02.2 | Corregir una devuelta y reenviarla |
| HU-03.1, HU-03.2 | Una enviada el viernes se consulta el lunes; una devuelta no enseña días |
| ESC-01 | De extremo a extremo en preproducción; `DEM_INT_NotificarERP` recibe el estado final |

## 15. Pendientes técnicos

| ID | Duda | Bloquea | Quién la resuelve |
|---|---|---|---|
| PT-01 | ¿Qué recibe y qué devuelve `UTL_DiasLaborables`? [FU-01 NV-ARQ-01] | DT-03 | Equipo de la aplicación de utilidades |
| PT-02 | ¿Quién recibe el correo de la revisión? [FU-01 NV-PRO-01] | §9 | Analista con el responsable de las solicitudes (PC-01) |
