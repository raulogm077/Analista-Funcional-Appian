<!--
  Plantilla LEEME — Guía de lectura (orquestador, fase 6, lo último que se escribe). Objetivo 1-2 pantallas, máximo 3.
  - Columna IDs: el rango real de esta ejecución (p. ej. PAN-001…PAN-006, H-SEG-01…H-SEG-04); «—» si no tiene.
  - «Qué no incluye»: las tres primeras líneas van siempre; añade las de esta ejecución que de verdad falten (omite las que no apliquen: si hubo role maps o MCP opcionales, no van aquí).
  - Las limitaciones globales (entorno, versión, muestra de ejecuciones, configuración que el Dev MCP no devuelve) se explican aquí una vez; los demás documentos no las repiten.
  - «Orientativo (ver LEEME)»: los demás documentos marcan así las cifras que dependen de una limitación global; aquí,
    en «Qué no incluye», se explica una vez por qué. Si ningún documento usa la marca, quita su fila de las marcas.
  - Glosario de Appian: las filas fijas (hasta «Data fabric») van siempre. Debajo, una fila por cada término de Appian
    que usen los entregables: las de la plantilla son las habituales (quita las que no aparezcan) y las que falten se
    añaden con la documentación oficial (p. ej. https://docs.appian.com/suite/help/26.6/Sub-Process_Activity.html,
    https://docs.appian.com/suite/help/26.6/record-events.html,
    https://docs.appian.com/suite/help/26.6/prepare-deployment-packages.html#add-plugins).
  - Celdas ≤ 100 caracteres. Un solo TL;DR. Sin usuarios.
-->

# {{Nombre visible de la aplicación}}: documentación de reingeniería

> **TL;DR**: Documentación de `{{nombre técnico}}` obtenida leyendo el entorno `{{url}}` el {{AAAA-MM-DD}}, en solo lectura: la aplicación no se modificó. Empieza por [00-resumen-ejecutivo.md](./00-resumen-ejecutivo.md) y sigue la ruta de tu perfil.
> **Volumen**: {{N}} objetos · {{N}} procesos · {{N}} pantallas · {{N}} hallazgos (Alta: {{n}}).

## Por dónde empezar

| Perfil | Ruta de lectura |
|---|---|
| Nuevo en el proyecto | 00 → 01 → 10 → 02 → 08 (índice) → 03 |
| Desarrollador que la mantiene | 02 → 03 → 08 → 05 y 06 → 04 → 07 → 09 → INVENTARIO → anexo/ |
| Arquitecto que la reconstruye o moderniza | 00 → 13 → 12 → 14 → 11 → 10 → anexo/ |
| Negocio, para validar | 01 → 11 → 12 (preguntas abiertas y funcionalidad candidata a no migrar) |
| Auditoría o seguridad | 04 → 06 → 05 → 09 (registro de hallazgos) |

## Contenido

| Documento | Qué contiene | IDs |
|---|---|---|
| [00-resumen-ejecutivo.md](./00-resumen-ejecutivo.md) | Cifras, procesos críticos, hallazgos principales y veredicto | — |
| [01-funcional.md](./01-funcional.md) | Qué hace, para quién y casos de uso | {{H-FUN-01…H-FUN-02}} |
| [02-arquitectura.md](./02-arquitectura.md) | Capas, objetos principales, acoplamientos y huérfanos | {{H-ARQ-01…H-ARQ-03}} |
| [03-modelo-datos.md](./03-modelo-datos.md) | Entidades, relaciones y volúmenes | {{H-DAT-01…H-DAT-04}} |
| [04-seguridad-grupos.md](./04-seguridad-grupos.md) | Grupos, permisos y secretos | {{H-SEG-01…H-SEG-03}} |
| [05-integraciones-consumidas.md](./05-integraciones-consumidas.md) | Sistemas externos a los que llama | {{H-INT-01…H-INT-02}} |
| [06-apis-expuestas.md](./06-apis-expuestas.md) | APIs que ofrece a otros sistemas | {{H-API-01}} |
| [07-batches.md](./07-batches.md) | Procesos programados | {{H-BAT-01}} |
| [08-procesos-bpmn/indice.md](./08-procesos-bpmn/indice.md) | Cada proceso en BPMN 2.0 (abre en bpmn.io o Camunda) y su explicación | {{H-PRO-01…H-PRO-05}} |
| [09-valor-adicional.md](./09-valor-adicional.md) | Métricas, constantes, huérfanos, versionado, glosario y registro de hallazgos | {{H-GEN-01…H-GEN-02}} |
| [10-pantallas.md](./10-pantallas.md) | Catálogo de pantallas | {{PAN-001…PAN-006}} |
| [11-reglas-negocio.md](./11-reglas-negocio.md) | Catálogo de reglas de negocio | {{RN-001…RN-012}} |
| [12-especificacion-reconstruccion.md](./12-especificacion-reconstruccion.md) | Requisitos para reconstruirla, criterios de aceptación y trazabilidad | {{RF-001…RF-010, PQ-001…PQ-004}} |
| [13-modernizacion-refactor.md](./13-modernizacion-refactor.md) | Diagnóstico, estrategia y plan de migración | {{MOD-001…MOD-008}} |
| [14-diseno-objetivo.md](./14-diseno-objetivo.md) | Cómo construirla: datos, procesos, pantallas e integraciones | — |
| [INVENTARIO.md](./INVENTARIO.md) | Todos los objetos, con uuid, y cobertura de la extracción | — |
| [anexo/indice.md](./anexo/indice.md) | Definición original de cada objeto: código numerado por líneas, sin usuarios | — |

## Cómo leer las marcas

| Marca | Significado |
|---|---|
| ✅ | Verificado: la definición o la respuesta de Appian lo muestra. |
| 🔵 | Inferido de evidencia indirecta; el documento dice de qué («según su nombre»: solo lo dice el nombre). |
| ❓ | Pendiente: dato que la extracción no trae o que debe validar negocio. |
| Alta · Media · Baja | Severidad de un hallazgo: actuar ya · planificar · mejora o higiene. |
| orientativo (ver LEEME) | Cifra que depende de una limitación de esta extracción (ver «Qué no incluye»). |

Que la extracción no traiga un dato no significa que falte en la aplicación: por eso se marca ❓ y no se trata como defecto.

**Identificadores**

| Prefijo | Qué es | Dónde |
|---|---|---|
| `H-<ÁREA>-NN` | Hallazgo: algo que corregir, decidir o vigilar; el área dice su documento (ver «Contenido») | Su documento y el [registro de 09](./09-valor-adicional.md#registro-de-hallazgos) |
| `PAN-NNN` | Pantalla | 10 |
| `RN-NNN` | Regla de negocio | 11 |
| `RF-NNN` · `RNF-NNN` | Requisito funcional · requisito no funcional (volúmenes, rendimiento…) | 12 |
| `PQ-NNN` | Pregunta abierta para negocio o para el equipo técnico | 12 |
| `MOD-NNN` | Actuación de modernización | 13 |
| `DEC-NNN` | Decisión pendiente | 13 |

**Evidencia**

| Forma | Qué indica |
|---|---|
| `mcp:tipo/nombre#ubicación` | Objeto y punto de su definición; el enlace abre su ficha en el [anexo](./anexo/indice.md). |
| `@dependents` · `@history` · `@versions` | Tras el nombre, la respuesta de la que sale: quién lo usa · ejecuciones · versiones. |
| `@validation` · `@screen` · `@members` | Avisos de la plataforma · pantalla renderizada (sin valores) · miembros del grupo. |
| `@other:<herramienta>` | Otra respuesta de la plataforma (p. ej. el role map). |
| `graph:hubs` · `graph:orphans` · `graph:edge/A→B` | Conclusión del grafo de referencias entre objetos ([anexo/grafo.md](./anexo/grafo.md)). |
| `Fuente: <URL>` | Documentación oficial de Appian. |

## Qué no incluye

- Datos de negocio: no se leyó ninguna fila, solo metadatos y recuentos.
- Valores de otros entornos: solo los de `{{url}}`; los demás están en el paquete de despliegue.
- Configuración que el Dev MCP no devuelve (excepciones y alertas de nodos, destinatarios de correo, seguridad de acciones de record): marcada ❓.
- {{Definición de N CDTs y N decisiones: el Dev MCP no la devuelve (ver INVENTARIO).}}
- {{Seguridad por objeto (role maps): no disponible.}}
- {{Volúmenes de datos: Appian MCP Server no disponible.}}
- {{Verificación con la documentación oficial: Docs MCP no disponible; las fuentes de 13 no están verificadas para la versión.}}
- {{Versión de Appian: no determinada; las recomendaciones usan la documentación más reciente.}}
- {{Uso real: el entorno no consta como producción y la muestra son las últimas N ejecuciones de cada proceso; las cifras son orientativas (los documentos las marcan «orientativo (ver LEEME)») y no sirven para decidir qué se usa{{; la muestra es uniforme (mismo iniciador y hora), así que no dice quién usa cada proceso ni cuándo}}.}}

## Glosario de Appian

| Término | Significado |
|---|---|
| Record type | Entidad de datos: campos, relaciones, vistas y acciones sobre una tabla u otra fuente. |
| CDT | Tipo de datos personalizado: estructura de datos para procesos, reglas e interfaces. |
| Process model | Flujo de trabajo: tareas de usuario, pasos automáticos y decisiones. |
| Interfaz | Pantalla o componente de pantalla. |
| SAIL | Lenguaje de expresiones de Appian con el que se escriben interfaces y reglas. |
| Expression rule | Función reutilizable escrita en SAIL. |
| Decisión | Reglas de negocio expresadas como tabla de decisión. |
| Constante | Valor con nombre (texto, número, grupo, documento…) que usan otros objetos. |
| Integración | Llamada a un sistema externo, normalmente a través de un connected system. |
| Connected system | Conexión y autenticación con un sistema externo. |
| Web API | Endpoint HTTP que la aplicación ofrece a otros sistemas. |
| Site | Aplicación web para el usuario final, organizada en páginas. |
| Grupo | Conjunto de usuarios; base de la seguridad y de la asignación de tareas. |
| Data fabric | Capa de datos de Appian construida con record types y sus relaciones. |
| Role map | Grupos de un objeto con su nivel de permiso (Administrator, Editor, Viewer, Deny…). |
| Initiator · Viewer | Permisos de un process model: Initiator, el mínimo para iniciarlo; Viewer, verlo e iniciarlo. |
| Acción de lista · acción relacionada | Botón de un record type que lanza un proceso: desde la lista · sobre un registro concreto. |
| Vista de record | Página de un registro concreto (p. ej. «Resumen»), hecha con una interfaz. |
| Smart service · Write Records | Nodo que hace una acción de la plataforma · el que guarda registros de un record type. |
| Subproceso síncrono · asíncrono | El proceso padre espera a que termine el hijo y recibe sus datos · sigue sin esperarlo. |
| Record type sincronizado | Record type cuyos datos Appian copia en su caché para consultarlos y relacionarlos. |
| Evento de record | Anotación de quién hizo qué y cuándo en un registro, guardada en un record type de historial. |
| Plug-in | Extensión instalada en el entorno, no en la aplicación: añade nodos, funciones o componentes. |
| Grupo de sistema | Grupo que trae la plataforma, no la aplicación. |
| Knowledge center · translation set | Carpeta de documentos con su seguridad · textos de la aplicación con sus traducciones. |

El vocabulario del negocio está en el [glosario de 09](./09-valor-adicional.md#glosario-de-negocio).

> Los datos de trabajo de la extracción se guardan aparte, en la carpeta de trabajo que está junto a esta, y no viajan con esta documentación: contienen las respuestas sin filtrar, con usuarios y hosts internos.
