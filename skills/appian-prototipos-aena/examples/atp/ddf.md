# Análisis funcional · Gestión de Acuerdos con Terceras Partes (ATP)

## 1. Portada y control documental

- Proyecto: Gestión de Acuerdos con Terceras Partes (ATP)
- Cliente: AENA
- Modo: **fiel** — extracto estructurado de la ERS; no sustituye al documento base
- Versión: v1.1 — 25/09/2026
- Criterios de aceptación: la ERS no los define. Los marcados ⚠️ se han propuesto a petición del usuario para preparar pruebas y están pendientes de validar con el cliente.

**Fuentes**

| ID | Fichero | Tipo | Fecha |
|---|---|---|---|
| FU-01 | ../ers-atp-ejemplo.md | ERS (texto) | 2026-09-25 |

**Control de versiones**

| Versión | Fecha | Cambio | Fuentes | IDs afectados |
|---|---|---|---|---|
| v1.0 | 25/09/2026 | Extracto inicial de la ERS | FU-01 | Todos |
| v1.1 | 25/09/2026 | Fichas de tarea (6.3), fichas de pantalla con criterios propuestos, matriz de cobertura | FU-01 | ACT-01, ACT-02, PAN-01…PAN-08, Sec 16 |

## 2. Resumen y contexto

Aplicación para registrar, revisar y hacer seguimiento de los acuerdos que AENA suscribe con terceras partes: convenios, contratos de colaboración, acuerdos de confidencialidad y protocolos generales de actuación. [FU-01 §1]

## 3. Alcance y exclusiones

- Dentro: alta del acuerdo en varios pasos, revisión jurídica, consulta y ficha, edición y documentos, avisos de vencimiento, indicadores e informe. [FU-01 §4]
- Fuera: ❓ La ERS no declara exclusiones.

## 4. Supuestos y restricciones

Ver documento base. La ERS no declara supuestos ni restricciones.

## 5. Actores, roles y permisos

| Rol | Descripción | Participa en | Crea | Consulta | Edita | Aprueba / Ejecuta | Fuente |
|---|---|---|---|---|---|---|---|
| Gestor de acuerdos | Unidad promotora | ACT-01; PAN-01, PAN-02, PAN-03, PAN-04, PAN-06, PAN-07 | Acuerdos | Sí | Datos generales y documentos | Solicita la revisión | [FU-01 §2] |
| Revisor jurídico | Asesoría Jurídica | ACT-02; PAN-01, PAN-02, PAN-03, PAN-05 | — | Sí | — | Aprueba, rechaza o devuelve con comentarios | [FU-01 §2] |
| Consulta | Cualquier usuario de AENA con acceso | PAN-02, PAN-03 (solo vigentes) | — | Acuerdos vigentes | — | — | [FU-01 §2] |

¿Quién ve el informe (PAN-08) y los indicadores de inicio? ❓ (P-005)

## 6. Procesos y actividades

**Actividades**

| ID | Actividad | Actor | Tipo | Estado de entrada → salida | En la aplicación | Fuente |
|---|---|---|---|---|---|---|
| ACT-01 | Dar de alta el acuerdo y solicitar la revisión | Gestor de acuerdos | Usuario | — → «En revisión jurídica» | Sí | [FU-01 RF-05, RF-07] |
| ACT-02 | Resolver la revisión jurídica | Revisor jurídico | Usuario | «En revisión jurídica» → «Pendiente de firma» / «Borrador» / «Rechazado» (❓ P-001, P-007) | Sí | [FU-01 RF-10] |
| ACT-03 | Firma del acuerdo | ❓ | ❓ | «Pendiente de firma» → «Vigente» (❓) | ❓ La ERS no dice quién firma ni si se registra en la aplicación | [FU-01 §3 Estado] |

Sin diagrama en modo fiel.

### 6.3 Fichas de tarea

**ACT-01 — Dar de alta el acuerdo y solicitar la revisión**

| Campo | Detalle |
|---|---|
| **Actor** | Gestor de acuerdos |
| **Pantalla** | PAN-04 |
| **Disparador** | El gestor pulsa «Nuevo acuerdo» (PAN-01 o PAN-02) |
| **Estado de entrada** | — (acuerdo nuevo) |
| **Plazo / escalado** | — |
| **Fuente** | [FU-01 RF-05, RF-07] |

| Opción | Condición para poder elegirla | Estado de salida | Siguiente | Aviso |
|---|---|---|---|---|
| «Enviar a revisión» | Campos obligatorios completos; RN-01, RN-02 | «En revisión jurídica» | ACT-02 | Tarea para Asesoría Jurídica (RF-07) |
| «Cancelar» | — | No se crea el acuerdo | — | — |

**Criterio mínimo de aceptación**
- `CA-ACT-01.1` ⚠️ **Dado** un gestor con el alta completa, **cuando** pulsa «Enviar a revisión», **entonces** el acuerdo queda en «En revisión jurídica» y aparece una tarea de revisión en la bandeja de Asesoría Jurídica.

**ACT-02 — Resolver la revisión jurídica**

| Campo | Detalle |
|---|---|
| **Actor** | Revisor jurídico |
| **Pantalla** | PAN-05 |
| **Disparador** | ACT-01 |
| **Estado de entrada** | «En revisión jurídica» |
| **Plazo / escalado** | ❓ |
| **Fuente** | [FU-01 RF-10] |

| Opción | Condición para poder elegirla | Estado de salida | Siguiente | Aviso |
|---|---|---|---|---|
| «Aprobar» | — | «Pendiente de firma» (❓ P-001) | ACT-03 | ❓ |
| «Devolver para cambios» | Comentarios obligatorios | ❓ «Borrador» (P-007) | ❓ ACT-01 (P-007) | ❓ |
| «Rechazar» | Comentarios obligatorios | «Rechazado» | Fin | ❓ |

**Criterio mínimo de aceptación**
- `CA-ACT-02.1` ⚠️ **Dado** un acuerdo en «En revisión jurídica», **cuando** el revisor elige «Aprobar» y envía, **entonces** el acuerdo pasa a «Pendiente de firma» y la tarea sale de su bandeja.
- `CA-ACT-02.2` ⚠️ **Dado** un acuerdo en «En revisión jurídica», **cuando** el revisor elige «Rechazar» o «Devolver para cambios» sin comentarios, **entonces** no puede enviar la decisión.
- `CA-ACT-02.3` ⚠️ **Dado** un acuerdo en «En revisión jurídica», **cuando** el revisor elige «Rechazar» con comentarios y envía, **entonces** el acuerdo pasa a «Rechazado».

## 7. Casos de uso

Ver documento base.

## 8. Requisitos funcionales

| ID | Requisito | Se verifica en | Fuente |
|---|---|---|---|
| RF-01 | Página de inicio con indicadores: acuerdos vigentes, pendientes de revisión, que vencen en los próximos 90 días e importe comprometido | CA-PAN-01.1 | [FU-01 §4] |
| RF-02 | La página de inicio muestra las tareas pendientes del usuario conectado | CA-PAN-01.2 | [FU-01 §4] |
| RF-03 | Listado de acuerdos con búsqueda por texto, filtros por estado, tipo y aeropuerto, y exportación a Excel | CA-PAN-02.1, CA-PAN-02.2 | [FU-01 §4] |
| RF-04 | Desde el listado se accede a la ficha del acuerdo | CA-PAN-02.3 | [FU-01 §4] |
| RF-05 | Alta del acuerdo en varios pasos: datos generales, tercero, condiciones económicas y documentación, con resumen final antes de enviarlo | CA-PAN-04.1 | [FU-01 §4] |
| RF-06 | El importe solo se pide si el acuerdo tiene contenido económico | CA-PAN-04.2 | [FU-01 §4] |
| RF-07 | Al enviar el alta, el acuerdo pasa a *En revisión jurídica* y se genera una tarea para Asesoría Jurídica | CA-ACT-01.1 | [FU-01 §4] |
| RF-08 | La ficha del acuerdo muestra ciclo de vida, datos generales, tercero, condiciones económicas, documentos e historial de cambios | CA-PAN-03.1 | [FU-01 §4] |
| RF-09 | Desde la ficha, el gestor puede editar los datos generales y añadir documentos | CA-PAN-06.1, CA-PAN-07.1 | [FU-01 §4] |
| RF-10 | El revisor jurídico resuelve la tarea: aprobar, devolver para cambios o rechazar; comentarios obligatorios si no se aprueba | CA-ACT-02.1, CA-ACT-02.2, CA-ACT-02.3 | [FU-01 §4] |
| RF-11 | Aviso en la ficha cuando un acuerdo vigente vence en menos de 90 días | CA-PAN-03.2 | [FU-01 §4] |
| RF-12 | Informe con acuerdos por tipo, por estado, altas por mes e importe por aeropuerto | CA-PAN-08.1 | [FU-01 §4] |

## 9. Reglas de negocio

| ID | Regla | Aplica en | Fuente |
|---|---|---|---|
| RN-01 | La fecha de fin debe ser posterior a la fecha de inicio | PAN-04, PAN-06 | [FU-01 §5] |
| RN-02 | Documentos admitidos: PDF y DOCX, máximo 10 MB por fichero | PAN-04, PAN-07 | [FU-01 §5] |

## 10. Modelo de datos

**Acuerdo** (Record Type)

| Campo | Tipo | Obligatorio | Valores / regla | Fuente |
|---|---|---|---|---|
| Código | Texto | Sí (automático) | Formato ATP-AAAA-NNNN | [FU-01 §3] |
| Título | Texto (200) | Sí | | [FU-01 §3] |
| Tipo de acuerdo | Lista | Sí | Convenio, Contrato de colaboración, Acuerdo de confidencialidad, Protocolo general de actuación | [FU-01 §3] |
| Tercero | Texto | Sí | Razón social | [FU-01 §3] |
| CIF/NIF del tercero | Texto | Sí | | [FU-01 §3] |
| Tipo de tercero | Lista | Sí | Empresa privada, Administración pública, Universidad o centro de investigación, Otro | [FU-01 §3] |
| Aeropuerto / unidad | Lista | Sí | Código IATA o Servicios Centrales | [FU-01 §3] |
| Responsable AENA | Usuario | Sí | | [FU-01 §3] |
| Fecha de inicio | Fecha | Sí | | [FU-01 §3] |
| Fecha de fin | Fecha | Sí | Posterior a la fecha de inicio (RN-01) | [FU-01 §3] |
| Prórroga automática | Sí/No | No | | [FU-01 §3] |
| Importe (€) | Decimal | Condicional | Solo si el acuerdo tiene contenido económico (RF-06) | [FU-01 §3] |
| Contraprestación | Texto largo | No | | [FU-01 §3] |
| Estado | Lista | Automático | Ver Sec 11 | [FU-01 §3] |

Documentos del acuerdo e historial de cambios: la ERS los menciona (RF-08, RF-09) pero no detalla atributos. ❓

## 11. Estados

| Estado | Establecido por | Fuente |
|---|---|---|
| Borrador | ❓ (¿al devolver para cambios? P-007) | [FU-01 §3] |
| En revisión jurídica | ACT-01 «Enviar a revisión» (RF-07) | [FU-01 §4] |
| Pendiente de firma | ❓ presumiblemente ACT-02 «Aprobar» (P-001) | [FU-01 §3] |
| Vigente | ❓ (P-001) | [FU-01 §3] |
| Vencido | ❓ (P-001) | [FU-01 §3] |
| Rechazado | ACT-02 «Rechazar» (RF-10) | [FU-01 §4] |

## 12. Diseño funcional de pantallas

La ERS no describe pantallas: las fichas se derivan de los requisitos y lo no definido se marca ❓.

**PAN-01 — Inicio**

| Campo | Detalle |
|---|---|
| **Tipo** | Página del site |
| **Actores** | Todos (❓ P-005 para indicadores) |
| **Propósito** | Ver indicadores y tareas pendientes |
| **Se abre desde** | Página principal del site |
| **Organización** | Indicadores arriba; lista de tareas pendientes debajo |
| **Requisitos** | RF-01, RF-02 |
| **Fuente** | [FU-01 §4 RF-01, RF-02] |

**Campos**: indicadores «acuerdos vigentes», «pendientes de revisión», «vencen en los próximos 90 días», «importe comprometido» (calculados); lista de tareas pendientes (columnas ❓).

**Acciones**: abrir una tarea → su pantalla (PAN-05); «Nuevo acuerdo» ❓ (no lo pide la ERS en inicio).

**Criterios de aceptación**
- `CA-PAN-01.1` ⚠️ **Dado** un usuario en Inicio, **cuando** se carga la página, **entonces** ve los cuatro indicadores de RF-01 con valores coherentes con los acuerdos existentes.
- `CA-PAN-01.2` ⚠️ **Dado** un revisor con tareas de revisión, **cuando** abre Inicio, **entonces** ve esas tareas y ninguna de otros usuarios.

**PAN-02 — Listado de acuerdos**

| Campo | Detalle |
|---|---|
| **Tipo** | Página del site |
| **Actores** | Todos (Consulta: solo vigentes, ❓ P-003) |
| **Propósito** | Buscar y consultar acuerdos |
| **Se abre desde** | Pestaña del site |
| **Organización** | Buscador y filtros sobre una tabla de acuerdos |
| **Requisitos** | RF-03, RF-04 |
| **Fuente** | [FU-01 §4 RF-03, RF-04] |

**Campos**: columnas ❓ (la ERS no las enumera; P-002).

**Filtros**:

| Filtro | Control | Selección | Por defecto | Opciones (de dónde salen) |
|---|---|---|---|---|
| Búsqueda | Texto | — | Vacío | ❓ campos en los que busca |
| Estado | Desplegable | ❓ | ❓ | Estados de la Sec 11 |
| Tipo de acuerdo | Desplegable | ❓ | ❓ | Lista de la Sec 10 |
| Aeropuerto / unidad | Desplegable | ❓ | ❓ | Aeropuertos y Servicios Centrales |

**Ordenación**: ❓

**Acciones**:

| Acción (texto literal) | Quién la ve / cuándo está activa | Qué pasa después | Confirmación (texto literal) |
|---|---|---|---|
| Exportar a Excel | Todos ❓ | Descarga la lista filtrada | — |
| Abrir un acuerdo | Todos | Abre PAN-03 | — |

**Criterios de aceptación**
- `CA-PAN-02.1` ⚠️ **Dado** el listado, **cuando** el usuario filtra por un estado, un tipo y un aeropuerto, **entonces** solo ve los acuerdos que cumplen los tres.
- `CA-PAN-02.2` ⚠️ **Dado** el listado filtrado, **cuando** pulsa exportar, **entonces** obtiene un Excel con esos mismos acuerdos.
- `CA-PAN-02.3` ⚠️ **Dado** el listado, **cuando** pulsa un acuerdo, **entonces** se abre su ficha (PAN-03).

**PAN-03 — Ficha del acuerdo**

| Campo | Detalle |
|---|---|
| **Tipo** | Vista de registro |
| **Actores** | Todos; edición solo Gestor de acuerdos |
| **Propósito** | Consultar el acuerdo completo |
| **Se abre desde** | PAN-02 |
| **Organización** | Ciclo de vida, datos generales, tercero, condiciones económicas, documentos, historial de cambios |
| **Requisitos** | RF-04, RF-08, RF-09, RF-11 |
| **Fuente** | [FU-01 §4 RF-08, RF-09, RF-11] |

**Campos**: los de la Sec 10, en solo lectura.

**Acciones**:

| Acción (texto literal) | Quién la ve / cuándo está activa | Qué pasa después | Confirmación (texto literal) |
|---|---|---|---|
| Editar datos generales | Gestor de acuerdos (❓ en qué estados, P-006) | Abre PAN-06 | — |
| Añadir documento | Gestor de acuerdos | Abre PAN-07 | — |

**Reglas de la pantalla**
1. Caso A: acuerdo «Vigente» con fecha de fin a menos de 90 días → aviso de vencimiento (RF-11). Caso B: resto → sin aviso. Texto del aviso ❓.

**Criterios de aceptación**
- `CA-PAN-03.1` ⚠️ **Dado** un acuerdo, **cuando** se abre su ficha, **entonces** se ven los seis bloques de RF-08.
- `CA-PAN-03.2` ⚠️ **Dado** un acuerdo «Vigente» que vence en 60 días, **cuando** se abre su ficha, **entonces** se muestra el aviso de vencimiento; con 120 días, no.

**PAN-04 — Alta de acuerdo**

| Campo | Detalle |
|---|---|
| **Tipo** | Asistente |
| **Actores** | Gestor de acuerdos |
| **Propósito** | Registrar un acuerdo y enviarlo a revisión (ACT-01) |
| **Se abre desde** | ❓ acción «Nuevo acuerdo» (ubicación no definida) |
| **Organización** | Pasos: datos generales, tercero, condiciones económicas, documentación, resumen |
| **Requisitos** | RF-05, RF-06, RF-07; RN-01, RN-02 |
| **Fuente** | [FU-01 §4 RF-05–RF-07] |

**Campos**: los de la Sec 10, editables, con su obligatoriedad; Código y Estado automáticos.

**Acciones**: las de la ficha de tarea ACT-01.

**Reglas de la pantalla**
1. Importe: Caso A, el acuerdo tiene contenido económico → se pide y es obligatorio; Caso B, no lo tiene → no se muestra (RF-06).
2. RN-01 y RN-02. Texto de los mensajes ❓.

**Criterios de aceptación**
- `CA-PAN-04.1` ⚠️ **Dado** el alta, **cuando** el gestor avanza por los pasos, **entonces** no puede pasar de un paso con obligatorios vacíos y el último paso muestra el resumen de todo lo introducido.
- `CA-PAN-04.2` ⚠️ **Dado** el paso de condiciones económicas, **cuando** indica que no hay contenido económico, **entonces** el importe no aparece; si indica que sí, es obligatorio.

**PAN-05 — Revisión jurídica (tarea)**

| Campo | Detalle |
|---|---|
| **Tipo** | Tarea |
| **Actores** | Revisor jurídico |
| **Propósito** | Resolver la revisión (ACT-02) |
| **Se abre desde** | Tarea ACT-02, lista de tareas de PAN-01 |
| **Organización** | Datos del acuerdo en solo lectura; decisión y comentarios |
| **Requisitos** | RF-10 |
| **Fuente** | [FU-01 §4 RF-10] |

**Acciones y criterios**: los de la ficha de tarea ACT-02.

**PAN-06 — Editar datos generales (diálogo)**

| Campo | Detalle |
|---|---|
| **Tipo** | Diálogo |
| **Actores** | Gestor de acuerdos |
| **Se abre desde** | PAN-03 |
| **Requisitos** | RF-09; RN-01 |
| **Fuente** | [FU-01 §4 RF-09] |

**Campos**: datos generales de la Sec 10, precargados.

**Criterios de aceptación**
- `CA-PAN-06.1` ⚠️ **Dado** un acuerdo editable, **cuando** el gestor cambia la fecha de fin a una anterior a la de inicio y guarda, **entonces** no se guarda y se indica el error (RN-01).

**PAN-07 — Añadir documento (diálogo)**

| Campo | Detalle |
|---|---|
| **Tipo** | Diálogo |
| **Actores** | Gestor de acuerdos |
| **Se abre desde** | PAN-03 |
| **Requisitos** | RF-09; RN-02 |
| **Fuente** | [FU-01 §4 RF-09, §5] |

**Criterios de aceptación**
- `CA-PAN-07.1` ⚠️ **Dado** el diálogo, **cuando** el gestor adjunta un fichero que no es PDF ni DOCX, o de más de 10 MB, **entonces** no se admite (RN-02).

**PAN-08 — Informe de acuerdos**

| Campo | Detalle |
|---|---|
| **Tipo** | Página del site |
| **Actores** | ❓ (P-005) |
| **Propósito** | Analizar la cartera de acuerdos |
| **Se abre desde** | Pestaña del site |
| **Organización** | Acuerdos por tipo; por estado; altas por mes; importe por aeropuerto |
| **Requisitos** | RF-12 |
| **Fuente** | [FU-01 §4 RF-12] |

**Criterios de aceptación**
- `CA-PAN-08.1` ⚠️ **Dado** el informe, **cuando** se carga, **entonces** muestra los cuatro análisis de RF-12 con totales coherentes con el listado.

## 13. Integraciones y gestión documental

- Integraciones: ❓ ninguna mencionada.
- Documentos: PDF y DOCX, máx. 10 MB (RN-02); almacenamiento ❓.

## 14. Notificaciones

Tarea para Asesoría Jurídica al enviar el alta (RF-07); aviso de vencimiento en la ficha (RF-11). Canal de notificación ❓.

## 15. KPIs e informes

Indicadores de RF-01 e informe de RF-12.

## 16. Criterios de aceptación y cobertura

| RF | Prioridad | Se verifica en | ¿Cubierto? |
|---|---|---|---|
| RF-01 | ❓ | CA-PAN-01.1 | Sí (⚠️) |
| RF-02 | ❓ | CA-PAN-01.2 | Sí (⚠️) |
| RF-03 | ❓ | CA-PAN-02.1, CA-PAN-02.2 | Sí (⚠️) |
| RF-04 | ❓ | CA-PAN-02.3 | Sí (⚠️) |
| RF-05 | ❓ | CA-PAN-04.1 | Sí (⚠️) |
| RF-06 | ❓ | CA-PAN-04.2 | Sí (⚠️) |
| RF-07 | ❓ | CA-ACT-01.1 | Sí (⚠️) |
| RF-08 | ❓ | CA-PAN-03.1 | Sí (⚠️) |
| RF-09 | ❓ | CA-PAN-06.1, CA-PAN-07.1 | Sí (⚠️) |
| RF-10 | ❓ | CA-ACT-02.1, CA-ACT-02.2, CA-ACT-02.3 | Sí (⚠️) |
| RF-11 | ❓ | CA-PAN-03.2 | Sí (⚠️) |
| RF-12 | ❓ | CA-PAN-08.1 | Sí (⚠️) |

La ERS no prioriza los requisitos (MoSCoW ❓). Todos los criterios son propuestas ⚠️.

## 17. Preguntas y puntos abiertos

| ID | Pregunta | Prioridad | Afecta a |
|---|---|---|---|
| P-001 | ¿Quién pasa el acuerdo a *Pendiente de firma*, *Vigente* y *Vencido*? ¿La firma se registra en la aplicación (fecha, firmantes) o solo se adjunta el PDF firmado? | 🔴 CRÍTICA | Sec 11, ACT-03, PAN-03 |
| P-002 | ¿Qué columnas tiene el listado de acuerdos? | 🟡 IMPORTANTE | PAN-02 |
| P-003 | ¿El rol Consulta ve solo acuerdos vigentes también en el listado y la ficha? | 🟡 IMPORTANTE | PAN-02, PAN-03 |
| P-004 | ¿Qué se muestra del historial de cambios? | 🟢 MEJORA | PAN-03 |
| P-005 | ¿Quién tiene acceso al informe y a los indicadores? | 🟢 MEJORA | PAN-01, PAN-08 |
| P-006 | ¿Quién puede editar un acuerdo en estado «Vigente»? La ERS solo habla del gestor en el alta | 🟡 IMPORTANTE | PAN-06 |
| P-007 | ¿«Devolver para cambios» genera una tarea al gestor o el acuerdo vuelve a Borrador sin tarea? | 🔴 CRÍTICA | ACT-02, PAN-05 |
| P-008 | Filtros del listado: ¿selección única o múltiple, valores por defecto y orden por defecto? | 🟢 MEJORA | PAN-02 |
| P-009 | Textos de los mensajes de error (RN-01, RN-02) y del aviso de vencimiento | 🟢 MEJORA | PAN-03, PAN-04, PAN-06, PAN-07 |
