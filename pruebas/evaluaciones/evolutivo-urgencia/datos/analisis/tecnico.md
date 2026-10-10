# Solicitudes de material — Especificación técnica

Versión: 1.1 · Estado: completo

## 0. Entorno

| Dato | Valor | Fuente |
|---|---|---|
| Versión de Appian | 26.6 en todos los entornos | Equipo del proyecto |
| Aplicación | `DEM Gestión de Solicitudes`, prefijo `DEM` | Equipo del proyecto |
| Entornos | Desarrollo, preproducción, producción y un entorno de corrección con la misma versión que producción, para las urgencias | FU-02 |
| Despliegue | Por el proceso de cambios de Sistemas | FU-02 |
| Volumen | Unas 1.200 solicitudes al año | funcional §10 |
| Usuarios | Unas 60 personas de 12 centros; no más de 15 a la vez | funcional §10 |
| Calendario laboral | Calendario de procesos de Appian con las fiestas de la organización | funcional §10 |

## 1. Convenciones

| Qué | Convención | Por qué |
|---|---|---|
| Prefijo y nombres | `DEM`; record types y process models con espacios (`DEM Solicitud`), reglas e interfaces en PascalCase (`DEM_ER_SiguienteNumero`) | BP 08 §1 |
| Idioma de los nombres | Español | Decisión del equipo |

## 2. Decisiones técnicas

**DT-01 — Los estados son un record type de referencia**

| Campo | Contenido |
|---|---|
| **Capa** | Datos |
| **Necesidad** | funcional 3.2, HU-04 |
| **Decisión** | `DEM Estado`, record type de referencia relacionado con `DEM Solicitud` |
| **Por qué** | Un estado escrito como texto en cada fila no se puede renombrar ni filtrar bien (BP 01 §1.1 · https://docs.appian.com/suite/help/latest/build-best-data-fabric.html#store-lookup-data-in-a-separate-record-type) |
| **Descartada** | Texto con los valores en una constante: cambiar un estado obliga a desplegar |
| **Riesgo** | Ninguno relevante |
| **Depende de** | — |
| **Verificar** | — |
| **Verificado** | No hace falta |

**DT-02 — Devolver es una salida más de la revisión**

| Campo | Contenido |
|---|---|
| **Capa** | Proceso |
| **Necesidad** | HU-02, HU-03, ACT-02, ACT-03 |
| **Decisión** | `DEM Revisar Solicitud` tiene tres salidas: aprobar, rechazar y devolver. Al devolver asigna la tarea de corregir (PAN-02) al `solicitante` y, al reenviar, vuelve a la revisión. Guarda siempre la solicitud entera |
| **Por qué** | Una tarea se asigna a un grupo o a un usuario guardado en el caso (BP 03 §7 · https://docs.appian.com/suite/help/latest/Process_Node_and_Smart_Service_Properties.html#assignment-tab) |
| **Descartada** | Rechazar y que el gestor dé de alta otra solicitud: se pierde el número |
| **Riesgo** | Si el `solicitante` ya no está en la organización, la tarea no llega a nadie |
| **Depende de** | — |
| **Verificar** | — |
| **Verificado** | No hace falta |

**DT-03 — Cambio sobre lo construido: EV-02**

| Campo | Contenido |
|---|---|
| **Capa** | Operación |
| **Necesidad** | HU-02, HU-05 (FU-03) |
| **Datos existentes** | `firmaRevisor` queda vacío en las solicitudes que ya hay; no se migra nada |
| **Despliegue y vuelta atrás** | Un paquete con los cuatro objetos de EV-02; la vuelta atrás, con el paquete del PASE-2026-031 |
| **Por qué** | Lo que ya está en producción no se rompe al desplegar (BP 08 §3) |
| **Verificado** | No hace falta |

## 3. Modelo de datos

### 3.1 DEM Solicitud

| Origen | Acceso | Volumen | Eventos | Seguridad |
|---|---|---|---|---|
| Tabla `DEM_SOLICITUD` | Sincronizado | Unas 1.200 filas al año | No | El gestor, las suyas; los revisores, todas menos los borradores (§4) |

| Campo | Tipo | Long. | Clave | Único | Oblig. | Por defecto | Uso |
|---|---|---|---|---|---|---|---|
| id | Entero | — | PK | Sí | Sí | Autonumérico | Técnico: clave |
| numero | Texto | 13 | — | Sí | Al enviar | — | Funcional: Número |
| titulo | Texto | 120 | — | No | Sí | — | Funcional: Título |
| importe | Decimal | — | — | No | Sí | — | Funcional: Importe |
| descripcion | Texto | 2000 | — | No | No | — | Funcional: Descripción |
| solicitante | Usuario | — | — | No | Sí | Quien la crea | Funcional: Solicitante |
| estadoId | Entero | — | FK a `DEM Estado` | No | Sí | Borrador | Funcional: Estado |
| fechaEnvio | Fecha y hora | — | — | No | Al enviar | — | Funcional: Fecha de envío |
| comentarioDevolucion | Texto | 1000 | — | No | Al devolver | — | Funcional: Comentario de devolución |
| firmaRevisor | Usuario | — | — | No | Al decidir | — | Funcional: Firma del revisor |

### 3.2 DEM Estado

| Origen | Acceso | Volumen | Eventos | Seguridad |
|---|---|---|---|---|
| Tabla `DEM_ESTADO` | Sincronizado | 5 filas | No | Lo leen todos los usuarios de la aplicación |

| Campo | Tipo | Long. | Clave | Único | Oblig. | Por defecto | Uso |
|---|---|---|---|---|---|---|---|
| id | Entero | — | PK | Sí | Sí | — | Técnico: clave |
| nombre | Texto | 30 | — | Sí | Sí | — | Técnico: nombre del estado (funcional 3.2) |

| Record type | Valores iniciales | Quién lo mantiene |
|---|---|---|
| `DEM Estado` | Los cinco estados de funcional 3.2 | Nadie: cambian con la solicitud |

## 4. Grupos y seguridad

| Perfil | Grupo | Constante |
|---|---|---|
| Gestor | `DEM Gestores` | — |
| Revisor | `DEM Revisores` | — |

| Qué | Gestor | Revisor |
|---|---|---|
| Ver solicitudes | Las suyas | Todas menos los borradores |
| Crear, corregir y reenviar | Sí | No |
| Revisar y firmar | No | Sí |

«El gestor ve solo sus solicitudes» (HU-04.1) lo aplica la seguridad de registro de `DEM Solicitud`.

## 5. Estados y transiciones

La transición de «Borrador» a «Enviada» la hace `DEM Alta Solicitud`; las demás de funcional 3.2, `DEM Revisar Solicitud` (DT-02). Ninguna interfaz cambia el estado por su cuenta.

## 6. Lógica

| Regla | Entradas | Devuelve | Lógica | Pruebas |
|---|---|---|---|---|
| `DEM_ER_SiguienteNumero` | año | Texto | DEM-<año>-<siguiente de cuatro cifras>, con el último número del año en `DEM Solicitud` | La primera de 2027 es DEM-2027-0001 |
| `DEM_ER_Firma` | solicitud | Booleano | Si `firmaRevisor` tiene valor (HU-05) | Sin firma: false |

## 7. Interfaces y acciones

| Pantalla | Qué es en Appian | Guarda con | Notas |
|---|---|---|---|
| PAN-01 | `DEM_Dashboard`, página «Panel» del site `DEM Solicitudes` | — | Lista de `DEM Solicitud` con filtro por estado y búsqueda; botón «Nueva solicitud» que abre el formulario de inicio de `DEM Alta Solicitud` |
| PAN-02 | `DEM_SolicitudForm`, formulario de inicio de `DEM Alta Solicitud` y de la tarea de corregir | `DEM Alta Solicitud`, `DEM Revisar Solicitud` | Valida el título y el importe (HU-01.1, HU-01.2); al reenviar deja `firmaRevisor` vacío (HU-02.2) |
| PAN-03 | `DEM_RevisionForm`, formulario de tarea | `DEM Revisar Solicitud` | No deja decidir sin firma (`DEM_ER_Firma`, HU-05.1); comentario obligatorio al devolver (HU-03.2) |

## 8. Procesos

**DEM Alta Solicitud** (ACT-01): formulario de inicio PAN-02. Al enviar pone el número con `DEM_ER_SiguienteNumero`, la fecha de envío y «Enviada», guarda la solicitud y llama a `DEM Revisar Solicitud`.

**DEM Revisar Solicitud** (DT-02).

| Nodo | Qué hace | Asignado a | Plazo y escalado | Escribe | Evento |
|---|---|---|---|---|---|
| Revisión (ACT-02) | Tarea PAN-03 | `DEM Revisores` | 3 días laborables; después, recordatorio al grupo | La solicitud entera (DT-02) | — |
| Corregir (ACT-03) | Tarea PAN-02 | `solicitante` de la solicitud | — | La solicitud entera, con la fecha de envío | — |
| Avisar | Correo AV-02 al aprobar o rechazar | — | — | — | — |

## 9. Avisos

| Aviso | Cómo se hace | Remitente y respuesta | Plantilla |
|---|---|---|---|
| AV-01 | Tarea asignada a `DEM Revisores` | — | La de la tarea |
| AV-02 | Nodo «Avisar» de `DEM Revisar Solicitud` | Buzón de Servicios generales, sin respuesta | Texto plano |
| AV-03 | Tarea asignada al `solicitante` y correo de la tarea | El de la tarea | Texto plano |

## 10. Integraciones, documentos e IA

No aplica: la aplicación no tiene integraciones ni documentos.

## 11. Site e informes

`DEM Solicitudes`, con una página: «Panel» (PAN-01), para `DEM Gestores` y `DEM Revisores`.

## 12. Volumen y operación

Unas 1.200 solicitudes al año: sin riesgo de volumen. `DEM Solicitud` y `DEM Estado` están sincronizados.

## 13. Plan de construcción

| Paso | Objeto | Tipo | Situación | Sustituye a | Cambio |
|---|---|---|---|---|---|
| 1 | `DEM Gestores` | Grupo | Nuevo | — | |
| 1 | `DEM Revisores` | Grupo | Nuevo | — | |
| 2 | `DEM Estado` | Record type | Nuevo | — | |
| 2 | `DEM Solicitud` | Record type | Nuevo | — | |
| 3 | `DEM_ER_SiguienteNumero` | Regla de expresión | Nuevo | — | |
| 4 | `DEM_SolicitudForm` | Interfaz | Nuevo | — | |
| 4 | `DEM_RevisionForm` | Interfaz | Nuevo | — | |
| 4 | `DEM_Dashboard` | Interfaz | Nuevo | — | |
| 5 | `DEM Revisar Solicitud` | Process model | Nuevo | — | |
| 5 | `DEM Alta Solicitud` | Process model | Nuevo | — | |
| 6 | `DEM Solicitudes` | Site | Nuevo | — | |
| 7 | `DEM Solicitud` | Record type | Modifica | — | EV-02 |
| 7 | `DEM_ER_Firma` | Regla de expresión | Nuevo | — | EV-02 |
| 8 | `DEM_RevisionForm` | Interfaz | Modifica | — | EV-02 |
| 8 | `DEM_SolicitudForm` | Interfaz | Modifica | — | EV-02 |

Manual, en cada entorno: los cinco estados de `DEM Estado` (§3.2).

## 14. Pruebas y trazabilidad

| Criterio | Cómo se prueba |
|---|---|
| HU-01.1, HU-01.2, HU-01.3 | Enviar sin título, sin importe, con 6.000,01 € y con 250,50 €; la primera del año sale con 0001 |
| HU-02.1, HU-02.2 | Corregir una solicitud devuelta y firmada, y reenviarla: vuelve sin firma |
| HU-03.1, HU-03.2, HU-03.3 | Dos revisores: uno acepta la tarea; devolver sin comentario y con comentario |
| HU-04.1, HU-04.2 | Un gestor solo ve las suyas; un revisor no ve borradores; filtro y búsqueda |
| HU-05.1 | Aprobar, rechazar y devolver sin firma |
| ESC-01 | De extremo a extremo en preproducción |

## 15. Pendientes técnicos

No hay.
