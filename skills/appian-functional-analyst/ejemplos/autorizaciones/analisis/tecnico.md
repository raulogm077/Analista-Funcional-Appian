# Solicitudes de autorización — Especificación técnica

Versión: 1.1

## 0. Entorno

| Dato | Valor | Fuente |
|---|---|---|
| Versión de Appian | Desarrollo, pruebas y producción en 26.6 | FU-02 00:30:10 |
| Tier y complementos | Estándar; sin complementos de IA | FU-02 00:30:10 |
| Base de datos | Base de datos de Appian Cloud | FU-02 00:30:40 |
| Inicio de sesión | SAML con el directorio corporativo | FU-02 00:14:30 |
| Idioma y zona horaria | Español; Europe/Madrid | FU-01 00:02:00 |
| Calendario laboral | Calendario de procesos de Appian con las fiestas de la organización | D-01 |
| Volumen | 600 solicitudes al año y unos 4 documentos por solicitud | funcional §10 |
| Usuarios | 150 personas de 40 unidades; 20 a la vez como máximo | funcional §10 |
| Tiempo de recuperación | Hasta 4 horas sin servicio | funcional §10 |
| Accesibilidad | Norma de la organización (WCAG 2.1 AA) | funcional §10 |
| Móvil y usuarios externos | No | funcional §10 |
| Licencias | PT-01 | — |

## 1. Convenciones

| Qué | Convención | Por qué |
|---|---|---|
| Prefijo | `AUT` | BP 08 §1 |
| Idioma de los nombres | Español | Decisión del equipo; manda sobre la de la skill oficial (BP, *Which Source Wins*) |
| Record types | Singular, con prefijo y espacio: `AUT Solicitud` | BP 08 §1 |
| Reglas, interfaces, integraciones | PascalCase con prefijo: `AUT_CalcularFechaLimite` | BP 08 §1 |
| Process models y grupos | Con espacios: `AUT Tramitar Solicitud`, `AUT Técnicos` | BP 08 §1 |
| Constantes | Mayúsculas: `AUT_GRUPO_TECNICOS` | BP 08 §1 |
| Campos | camelCase en español; clave `id` | BP 01 §8 |
| Auditoría | `createdBy`, `createdOn`, `modifiedBy`, `modifiedOn` en cada tabla, como los genera Appian | BP 01 §3.4 |
| Borrado | No se borra nada: las solicitudes terminan en «Autorizada» o «Denegada» | DT-03 |

## 2. Decisiones técnicas

**DT-01 — Estados y listas de valores como record types de referencia**

| Campo | Contenido |
|---|---|
| **Capa** | Datos |
| **Necesidad** | funcional 3.2 y 6.3 |
| **Decisión** | `AUT Estado` y `AUT Tipo Autorizacion` son record types de referencia relacionados con `AUT Solicitud` |
| **Por qué** | Un estado escrito como texto en cada fila no se puede renombrar ni filtrar bien (BP 01 §1.1 · https://docs.appian.com/suite/help/latest/build-best-data-fabric.html#store-lookup-data-in-a-separate-record-type) |
| **Descartada** | Campo de texto con los valores en una constante: obliga a desplegar para cambiar un tipo |
| **Riesgo** | Ninguno relevante |
| **Depende de** | — |
| **Verificar** | — |
| **Verificado** | No hace falta |

**DT-02 — Visibilidad por unidad con seguridad de registro**

| Campo | Contenido |
|---|---|
| **Capa** | Seguridad |
| **Necesidad** | RB-01, HU-02, HU-09 |
| **Decisión** | `AUT Solicitud` lleva el campo `grupoUnidad` (Group). Regla de seguridad «Users found in fields» sobre ese campo para la unidad, y «Users found in groups» para `AUT Técnicos`, `AUT Responsables` y `AUT Consulta` con la condición «estado distinto de Borrador» |
| **Por qué** | La seguridad de registro se aplica en listas, consultas, gráficos y relaciones sin tocar cada interfaz (BP 06 §5.1 · https://docs.appian.com/suite/help/latest/record-level-security.html) |
| **Descartada** | Filtrar en cada interfaz: se olvida en la siguiente pantalla o en la descarga a Excel |
| **Riesgo** | Una persona que cambia de unidad sigue viendo lo de la anterior hasta que el directorio actualiza su grupo (INT-01) |
| **Depende de** | Record type sincronizado |
| **Verificar** | Con un usuario de cada perfil, en «Test Security Rules» |
| **Verificado** | Documentación 26.6: «Users found in fields» y condiciones por campo |

**DT-03 — Plazos en días hábiles con el calendario de procesos**

| Campo | Contenido |
|---|---|
| **Capa** | Proceso |
| **Necesidad** | RB-02, ACT-02, ACT-08 |
| **Decisión** | Temporizadores y escalados con `a!addDateTime(…, useProcessCalendar: true)`; el administrador mantiene las fiestas en el calendario de procesos |
| **Por qué** | Es el mecanismo de Appian para que un temporizador no cuente días no laborables (BP 03 §6 · https://docs.appian.com/suite/help/latest/Intermediate_Event_-_Timer.html#configuring-a-timer-event) |
| **Descartada** | `workday()` con una lista de fiestas en una constante: hay que desplegar cada año |
| **Riesgo** | Si nadie carga las fiestas del año, los plazos se calculan mal: tarea de operación en §12 |
| **Depende de** | — |
| **Verificar** | Que el calendario de procesos del entorno excluye fines de semana |
| **Verificado** | Documentación 26.6 (Process Calendar Settings, a!addDateTime) |

## 3. Modelo de datos

### 3.1 AUT Solicitud

| Origen | Acceso | Volumen | Eventos | Seguridad |
|---|---|---|---|---|
| Tabla `AUT_SOLICITUD` en la base de datos de Appian | Sincronizado | 600 al año; 6.000 en 10 años | Sí: alta, envío, devolución, resolución | DT-02 |

| Campo | Tipo | Long. | Clave | Único | Oblig. | Por defecto | Uso |
|---|---|---|---|---|---|---|---|
| id | Número | — | Sí | Sí | Sí | Autonumérico | Técnico: clave |
| numero | Texto | 13 | — | Sí | Al enviar | `AUT_GenerarNumero` | Funcional: Número |
| grupoUnidad | Grupo | — | — | No | Sí | Grupo de la unidad de quien la crea | Funcional: Unidad solicitante |
| tipoId | Número | — | FK `AUT Tipo Autorizacion` | No | Sí | — | Funcional: Tipo |
| titulo | Texto | 120 | — | No | Sí | — | Funcional: Título |
| descripcion | Texto | 4000 | — | No | Sí | — | Funcional: Descripción |
| fechaInicio | Fecha | — | — | No | Sí | — | Funcional: Fecha de inicio |
| fechaFin | Fecha | — | — | No | Sí | — | Funcional: Fecha de fin |
| estadoId | Número | — | FK `AUT Estado` | No | Sí | Borrador | Funcional: Estado |
| fechaLimite | Fecha | — | — | No | Al enviar | `AUT_CalcularFechaLimite` | Funcional: Fecha límite |
| comentarioSubsanacion | Texto | 1000 | — | No | Al devolver | — | Funcional: Comentario de subsanación |
| informeTecnico | Texto | 4000 | — | No | Para resolver | — | Funcional: Informe técnico |
| informeTerminado | Booleano | — | — | No | Sí | false | Técnico: el informe técnico deja de ser borrador (HU-06.1) |
| resolucion | Texto | 20 | — | No | Al resolver | — | Funcional: Resolución |
| motivo | Texto | 2000 | — | No | Si es desfavorable | — | Funcional: Motivo |
| fechaUltimoRecordatorio | Fecha | — | — | No | No | — | Funcional: Último recordatorio al organismo |
| idProceso | Número | — | — | No | No | — | Técnico: instancia en curso, para cancelarla si hiciera falta |
| createdBy, createdOn, modifiedBy, modifiedOn | Auditoría | — | — | No | Sí | Appian | Técnico: auditoría (convenciones) |

### 3.2 AUT Documento

| Origen | Acceso | Volumen | Eventos | Seguridad |
|---|---|---|---|---|
| Tabla `AUT_DOCUMENTO` | Sincronizado | 2.400 al año | No | Hereda de la solicitud (Users who can view related records) |

| Campo | Tipo | Long. | Clave | Único | Oblig. | Por defecto | Uso |
|---|---|---|---|---|---|---|---|
| id | Número | — | Sí | Sí | Sí | Autonumérico | Técnico: clave |
| solicitudId | Número | — | FK `AUT Solicitud` | No | Sí | — | Técnico: relación |
| clase | Texto | 30 | — | No | Sí | — | Funcional: Clase |
| fichero | Documento | — | — | No | Sí | — | Funcional: Fichero |
| createdBy, createdOn | Auditoría | — | — | No | Sí | Appian | Funcional: Subido por, Fecha |

### 3.3 Referencias y carga inicial

| Record type | Valores iniciales | Quién lo mantiene |
|---|---|---|
| AUT Estado | Los siete de funcional 3.2 | Nadie: cambian con el proceso |
| AUT Tipo Autorizacion | Obra menor, Ocupación temporal, Uso de instalaciones | Responsable de la unidad (PT-02) |

Sin carga de datos antiguos (funcional §10).

## 4. Grupos y seguridad

| Perfil | Grupo | Constante |
|---|---|---|
| Unidad solicitante | Un grupo por unidad, del directorio, dentro de `AUT Unidades` | `AUT_GRUPO_UNIDADES` |
| Técnico de la unidad gestora | `AUT Técnicos` | `AUT_GRUPO_TECNICOS` |
| Responsable de la unidad | `AUT Responsables` | `AUT_GRUPO_RESPONSABLES` |
| Consulta | `AUT Consulta` | `AUT_GRUPO_CONSULTA` |

| Qué | Unidad | Técnicos | Responsables | Consulta |
|---|---|---|---|---|
| Ver solicitudes | Las suyas (DT-02) | Todas menos borradores | Todas menos borradores | Todas menos borradores |
| Acción «Nueva solicitud» | Sí | No | No | No |
| Informe técnico | Ver al terminar | Editar | Ver | Ver |
| Descargar la lista | No | No | No | Sí |

Seguridad de acción de registro para «Nueva solicitud» y «Adjuntar informe del organismo» (BP 06 §5.3).

## 5. Estados y transiciones

Las transiciones de funcional 3.2. Cada una la hace un process model (§8); ninguna interfaz cambia el estado por su cuenta.

## 6. Lógica

| Regla | Entradas | Devuelve | Lógica | Pruebas |
|---|---|---|---|---|
| `AUT_GenerarNumero` | — | Texto | `AUT-` + año + secuencia del año con 4 cifras, desde la tabla `AUT_SECUENCIA` con bloqueo | Primera del año = 0001; dos envíos a la vez no repiten número |
| `AUT_CalcularFechaLimite` | fechaEnvio | Fecha | `a!addDateTime(fechaEnvio, days: 30, useProcessCalendar: true)` (DT-03) | Envío un viernes antes de un festivo |

| Constante | Valor | Cambia por entorno |
|---|---|---|
| `AUT_CORREO_ORGANISMO` | Buzón del organismo | Sí (en pruebas, un buzón interno) |
| `AUT_DIAS_RECORDATORIO` | 10 | No |

## 7. Interfaces y acciones

| Pantalla | Qué es en Appian | Guarda con | Notas |
|---|---|---|---|
| PAN-01 | Página de site de tipo Record List de `AUT Solicitud` | — | Filtros de usuario: estado, tipo. Búsqueda en número y título. Exportación a Excel solo para Consulta |
| PAN-02 | Vista de registro «Resumen» + vistas «Documentos» e «Historial» | Acciones de registro | Ver prototipo, pantalla `ficha` |
| PAN-03 | Acción de registro «Nueva solicitud» y formulario de la tarea de subsanar | `AUT Tramitar Solicitud` | Ver prototipo, pantalla `alta` |
| PAN-04 | Formulario de tarea | `AUT Tramitar Solicitud` | Ver prototipo, pantalla `revisar` |
| PAN-05 | Formulario de tarea | `AUT Tramitar Solicitud` | Ver prototipo, pantalla `resolver` |

## 8. Procesos

**AUT Tramitar Solicitud** (uno por solicitud, desde el envío hasta la resolución)

| Nodo | Qué hace | Asignado a | Plazo y escalado | Escribe | Evento |
|---|---|---|---|---|---|
| Revisar documentación | Tarea PAN-04 | `AUT_GRUPO_TECNICOS` | 5 días hábiles; al vencer, aviso al responsable | estadoId, comentarioSubsanacion | Devolución o paso a informe |
| Subsanar | Tarea PAN-03 | Grupo de la unidad | 10 días hábiles (PC-02) | Datos de la solicitud | Reenvío |
| Pedir informe | Correo AV-02 | — | — | — | — |
| Esperar informe | Subproceso `AUT Esperar Informe` con temporizador recurrente | — | Cada 10 días hábiles, AV-03 (DT-03) | fechaUltimoRecordatorio | — |
| Resolver | Tarea PAN-05 | `AUT_GRUPO_RESPONSABLES` | 5 días hábiles | resolucion, motivo, estadoId | Resolución |
| Generar autorización | DOC-01 desde plantilla | — | — | Documento | — |

Cancelación: no se contempla en esta fase. Archivado de procesos: 7 días después de terminar (BP 03 §9).

## 9. Avisos

| Aviso | Cómo se hace | Remitente y respuesta | Plantilla |
|---|---|---|---|
| AV-01, AV-05 | Tarea asignada + correo de la tarea | Buzón de la unidad gestora; responder a ese buzón | Texto plano (BP 03 §10) |
| AV-02, AV-03 | Send E-Mail con la memoria y el plano adjuntos | Buzón de la unidad gestora | `.txt` con claves `###numero###` (https://docs.appian.com/suite/help/latest/Send_Email_Smart_Service.html#using-a-template) |
| AV-04 | Send E-Mail con DOC-01 adjunto si es favorable | Buzón de la unidad gestora | Igual |

## 10. Integraciones, documentos e IA

| Integración | Mecanismo | Si falla |
|---|---|---|
| INT-01 Directorio | Sincronización de usuarios y grupos por SAML/LDAP del entorno, no una integración propia | Appian conserva los grupos del día anterior |

Documentos: carpeta `AUT Documentos` con una subcarpeta por año; solo PDF de hasta 20 MB (validación en la interfaz). DOC-01 se genera con una plantilla Word (BP 01 §8.bis.3). Sin IA en esta fase.

## 11. Site e informes

Site «Autorizaciones», una página: Solicitudes (PAN-01). Las tareas llegan por la bandeja de tareas del site. Sin cuadros de mando en esta fase.

## 12. Volumen y operación

- 6.000 solicitudes en 10 años: muy por debajo del límite de sincronización (BP 05 §5).
- Cada enero, el administrador carga las fiestas del año en el calendario de procesos (DT-03).
- `AUT_CORREO_ORGANISMO` se configura en cada entorno.

## 13. Plan de construcción

1. Grupos, constantes y carpetas (§1, §4).
2. Tablas y record types de referencia, después `AUT Solicitud` y `AUT Documento` con sus relaciones (§3).
3. Seguridad de registro y de acciones (DT-02).
4. Reglas `AUT_GenerarNumero` y `AUT_CalcularFechaLimite` con sus casos de prueba (§6).
5. Interfaces a partir del prototipo (§7).
6. Process models (§8) y plantillas de correo (§9).
7. Site (§11).
8. Manual: calendario de procesos y buzón del organismo en cada entorno.

## 14. Pruebas y trazabilidad

| Criterio | Cómo se prueba |
|---|---|
| HU-01.1, HU-01.2, HU-01.3 | Alta con y sin documentos; dos envíos a la vez; otro usuario de otra unidad |
| HU-02.1, HU-02.2 | Usuario de la unidad A no ve solicitudes de la B (perfil que puede y perfil que no) |
| HU-03.1, HU-03.2 | Subsanar una devuelta |
| HU-04.1, HU-04.2, HU-04.3 | Dos técnicos; aceptar la tarea |
| HU-05.1, HU-05.2 | Devolver sin comentario y con comentario |
| HU-06.1, HU-06.2 | Unidad no ve el informe en borrador |
| HU-07.1, HU-07.2 | Subir un .docx y un PDF de 25 MB |
| HU-08.1, HU-08.2, HU-08.3 | Resolver en los dos sentidos |
| HU-09.1, HU-09.2, HU-09.3 | Usuario de Consulta: sin botones, con descarga |
| ESC-01 a ESC-04 | De extremo a extremo en pruebas |

## 15. Pendientes técnicos

| ID | Duda | Bloquea | Quién la resuelve |
|---|---|---|---|
| PT-01 | ¿Hay licencias para las 150 personas? | Puesta en producción | Jefe de proyecto |
| PT-02 | ¿Una pantalla para mantener los tipos o los carga el administrador? | §3.3 | Analista con el responsable |
