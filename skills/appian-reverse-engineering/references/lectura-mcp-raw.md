# Cómo leer los datos extraídos del Dev MCP

Guía común para todos los subagentes. **Léela antes de abrir ningún fichero de `<trabajo>/`.**

La skill no lee un export: la aplicación se ha extraído en vivo del entorno Appian con `scripts/devmcp_extract.py`, en modo solo lectura. Las herramientas del Dev MCP cambian entre versiones, así que **no busques herramientas concretas por nombre**. Trabaja con los roles y con el contenido.

## Ficheros de partida

`<trabajo>` es la carpeta de datos de trabajo: `<padre de la salida>/_trabajo/<nombre de la salida>` (p. ej. `appian-docs/_trabajo/DEM/` para la salida `appian-docs/DEM/`). No se comparte y los entregables no deben enlazarla.

| Fichero | Qué contiene | Úsalo para |
|---|---|---|
| `<trabajo>/inventory.json` | Todos los objetos de la app, agrupados por tipo. Cada objeto trae `name`, `uuid`, `type`, `mcpType`, `description`, `detail`, `path` (su definición), `files` (todas sus respuestas, con rol) y campos derivados (ver abajo). | Punto de partida y control de cobertura (100%). |
| `<trabajo>/graph.json` | Nodos y aristas `{source, target, refType, origin, evidence}`. `origin` = `dependents`/`dependencies` (análisis de dependencias de Appian, fiable), `uuid`/`name`/`literal` (referencia encontrada en la definición), `derived` (deducida, p. ej. `a!startProcess` vía constante). | Quién llama a quién, callers, hubs, huérfanos. |
| `<trabajo>/mcp_raw/<tipo>/<uuid>/<herramienta>.json` | Respuesta tal cual de cada herramienta para ese objeto: `{"_meta": {tool, role, ok, error, ...}, "response": ...}`. | El detalle: SAIL, nodos, campos, páginas, pantallas… |
| `<trabajo>/mcp_raw/_app/*.json`, `_env/*.json` | Llamadas de aplicación (definición de la app, listados) y de entorno (catálogos de tipos de nodo, etc.). | Contexto general. |
| `<trabajo>/extraction_report.json` | Herramientas usadas y excluidas, errores, herramientas desactivadas por tipo, servidor y entorno (`server.url`). | Sección de cobertura y limitaciones. |
| `<trabajo>/datafabric.json` (opcional) | Metadatos del data fabric y `count` por record type (Appian MCP Server). | Volúmenes en 03 y en 12. |
| `<trabajo>/preflight.json` | Estado de los 3 MCP al empezar y el entorno (`environment.url`, `isProduction`, `appianVersion` si se conocen). | Cobertura; interpretar el uso real. |
| `<salida>/anexo/<tipo>/<slug>.md` | La definición de cada objeto legible: expresiones con número de línea, nodos de los procesos y JSON completo, sin usuarios. | Citar líneas y enlazar el detalle desde los documentos. |

## Roles de los ficheros (`_meta.role`)

| Rol | Qué es | Dónde se usa |
|---|---|---|
| `definition` | La definición del objeto (SAIL, nodos, campos, páginas…). Es la fuente principal. | Todos los documentos |
| `dependents` | Quién referencia a este objeto, con *breadcrumb* (p. ej. «Interface Definition: Line 19»). | Callers, impacto |
| `dependencies` | Qué referencia este objeto. | Llamadas salientes |
| `history` | Ejecuciones reales del process model (total, última, fallos). En los documentos llámalo «ejecuciones». | 07, 08, 12 (prioridad), 13 (código muerto) |
| `versions` | Historial de versiones (cuándo y por quién; los usuarios no se citan). En los documentos llámalo «versiones». | 09 (versionado), 13 |
| `validation` | Avisos de validación de la plataforma (funciones obsoletas, errores). | 09, 13 |
| `screen` | Árbol de componentes de la interfaz renderizada con entradas vacías. Puede traer datos reales evaluados: no copies sus valores. No se publica en el anexo. | 10 (pantallas), 01 |
| `members` | Miembros de un grupo (grupos y usuarios). | 04 |
| `other` | Cualquier otra herramienta (p. ej. una nueva que haya añadido Appian). **Ábrela y aprovecha lo que aporte**: seguridad, métricas, configuración… | Donde encaje |

Si un objeto tiene `detail: "none"`, no hubo herramienta que devolviera su definición (por ejemplo, CDTs o decisiones en algunas versiones del Dev MCP). Documenta el objeto con lo que haya (nombre, tipo, dependencias) y márcalo ❓ indicando que la definición no está disponible por Dev MCP.

## Campos derivados en `inventory.json`

`build_model.py` ya ha calculado, cuando la respuesta lo permitía:

- **Process model:** `nodeCount`, `userTaskCount`, `subProcessCount`, `startType` (`none`/`timer`/`message`), `hasRecurrence`, `schedule` (configuración del temporizador tal cual), `startFormInterface`, `initiatorGroup` (ver «Quién puede iniciar un process model»), `usage` (`executions`, `lastExecution`, `failed`). Si `usage.failedInSampleOf` existe, `failed` se contó solo sobre esa muestra de instancias, no sobre el total: escríbelo así («3 fallos en las últimas 50 ejecuciones»), nunca como tasa global.
- **Interfaz, regla, Web API, integración:** `sailBytes`, `sailLines`.
- **Constante:** `value` (enmascarado si parece secreto, con `maskedSecret: true`), `typeRef`, `valueRef`.
- **Integración:** `method`, `endpoint`, `connectedSystemRef`, `modifiesData`.
- **Connected system:** `csType`, `baseUrl` (credenciales enmascaradas), `authType`.
- **Web API:** `method`, `endpointPath`.
- **Record type:** `fieldCount`, `sourceType`, `tableName`, `urlStub`, `relationshipCount`.
- **Site:** `pageCount`, `urlStub`. **Grupo:** `parentGroup`, `memberGroups`, `userCount` (solo usuarios directos; los de subgrupos no se suman).
- **Process model, criticidad:** `criticality` (`score`, `critical`, `reasons`, `calledBy`, `callsIntegrations`). Es la única fórmula de «proceso crítico»: úsala en todos los documentos.
- **Cualquiera:** `slug` (nombre sin espacios ni tildes; úsalo para nombrar ficheros por objeto, p. ej. `08-procesos-bpmn/<slug>.md` y `anexo/<tipo>/<slug>.md`), `maskedSecrets` (valores enmascarados en su extracción), `versions` (`count`, `lastModifiedOn`, `lastModifiedBy`), `validationIssues`, `screen`, `extraTools`.

Son una ayuda: ante la duda, **la fuente es el fichero `definition`**.

## Cómo interpretar las respuestas

- La forma exacta de las respuestas puede variar entre versiones del Dev MCP. Pueden venir envueltas (`{"result": {...}}`), y el uuid o el nombre pueden llamarse `uuid`/`objectUuid` y `name`/`objectName`. Interprétalas con sentido común; no asumas un esquema fijo.
- Process models: cada nodo suele tener `id`, `type` (id de esquema, p. ej. `core.0` inicio, `core.1` fin, `core.4` XOR, `internal.16` script task, `internal.17` user input task, `internal3.write_records_to_source_23r3` write records, `internal3.sendemail3` email, `internal3.integration` call integration), `name`, `connections` (ids destino), `assignment`, `data`, `forms` y `decision` (condiciones de las pasarelas). Si aparece un tipo de nodo que no reconoces, búscalo en `mcp_raw/_env/` (catálogo de tipos de nodo, si existe) o consúltalo en el Docs MCP.
- Las referencias a record types en SAIL tienen la forma `recordType!{uuid}Nombre.fields.{uuid}campo`. Traduce siempre a nombres legibles con `inventory.json`.
- Los uuids no se muestran al lector salvo en `INVENTARIO.md` y en el `anexo/`.
- **Definición frente a pantalla (`screen`).** La definición de una interfaz solo contiene su propio SAIL; el árbol renderizado incluye también lo que aportan las interfaces hijas. Si un componente o texto solo aparece en el render, cítalo con `@screen` y atribúyelo a la interfaz hija cuando puedas identificarla. Si definición y render no coinciden (p. ej. un campo que el render no muestra porque depende de una condición), manda la definición y explica la condición.

## Quién puede iniciar un process model

Según la documentación oficial, para iniciar un process model hace falta **al menos el permiso Initiator**; Administrator, Editor, Manager y Viewer también pueden iniciarlo, y **Deny** no puede hacer nada. Fuente: https://docs.appian.com/suite/help/26.6/process-model-object.html#process-model-security

Los procesos que arranca un temporizador o que se lanzan como subproceso se ejecutan como el usuario que desplegó el process model. Fuente: https://docs.appian.com/suite/help/26.6/Testing_and_Debugging_Problems_with_Process_Models.html#insufficient-object-permissions

Cada nodo desatendido se ejecuta como quien inició el proceso o como su diseñador, según su pestaña Asignación, que la extracción no trae: es ❓ salvo que la definición lo muestre. Fuente: https://docs.appian.com/suite/help/26.6/Process_Node_and_Smart_Service_Properties.html#assignment-tab

El iniciador que registran las ejecuciones es un dato: dalo por su grupo («una cuenta de DEM Users»), nunca por su nombre, y no lo confundas con la cuenta de despliegue si no coinciden; si no cuadran, dilo como ❓.

- **Si hay role map** (algún fichero `other` lo trae), es la fuente: pueden iniciar los grupos con cualquier rol distinto de Deny (Administrator, Editor, Manager, Viewer o Initiator).
- **`initiatorGroup`** es el grupo de seguridad que trae la definición del process model; no dice el nivel de permiso ni si sigue en el role map. Con role map, menciónalo solo si no coincide («la definición declara X, que no figura en el role map»). Sin role map, escribe «grupo de seguridad declarado: X; role map no disponible» ❓, nunca «solo X puede iniciarlo».
- Si el process model lo lanza una acción de record o `a!startProcess`, la seguridad de esa acción es un segundo filtro. La respuesta de los record types no siempre trae la seguridad de sus acciones: si no aparece, es ❓ (no «sin seguridad»).

## Formato de evidencia

Toda afirmación importante lleva evidencia verificable:

```
Evidencia: mcp:<tipo>/<nombre>[@<rol>]#<ubicación>
```

- `<tipo>` es el tipo del inventario (`processModel`, `interface`, `recordType`…) y `<nombre>` el nombre legible del objeto.
- `@<rol>` indica de qué fichero sale cuando **no** es la definición: `@dependents`, `@history`, `@versions`, `@validation`, `@screen`, `@members`, `@other:<herramienta>`. Sin `@`, se entiende `definition`. Para la aplicación: `mcp:application/<nombre>@other:<herramienta>`. Para conclusiones del grafo: `graph:hubs`, `graph:orphans`, `graph:edge/<origen>→<destino>`.
- `<ubicación>` es una ruta dentro de la respuesta (`pages[2].visibilityExpr`, `fields.importe`) o el *breadcrumb* de dependencias (`Interface Definition: Line 19`). En process models identifica los nodos por su id, no por su posición en la lista: `nodes[id=3].decision`.
- Ejemplos: `mcp:processModel/DEM Alta Solicitud#nodes[id=2]`, `mcp:interface/DEM_SolicitudForm#expression (línea 4)`, `mcp:processModel/DEM Alta Solicitud@history#totalCount`, `mcp:interface/DEM_SolicitudForm@screen#contents[0]`.
- Si la conclusión viene de un documento oficial: `Fuente: <URL de docs.appian.com>`.
- Si es inferida, márcala 🔵 y explica en una línea de qué se infiere.
- El lector encuentra cada objeto en `anexo/<tipo>/<slug>.md`: la definición (con «línea N» numerada) y el resto de respuestas (`@dependents`, `@history`, `@versions`, `@validation`, `@members`, `@other`), con los usuarios sustituidos por sus grupos. Las referencias `graph:` están en `anexo/grafo.md`. `@screen` no se publica: si una conclusión solo sale del render, dilo en el texto. Cuando ayude, enlaza la ficha del anexo.

## Qué no está disponible por Dev MCP

Dilo explícitamente en el documento afectado, en lugar de rellenar huecos:

- **Valores por entorno** (import customization files): no existen en la plataforma, solo en el paquete de despliegue.
- **Definiciones de tipos sin herramienta** en la versión instalada (mira `detail: "none"` y `extraction_report.json`).
- **Seguridad por objeto (role maps)**: solo si alguna herramienta la devuelve (revisa ficheros `other`). Si no, limita la matriz a lo verificable: grupo de seguridad de cada process model, visibilidad de páginas, asignaciones de tareas y expresiones de seguridad en SAIL.
- **Configuración que el Dev MCP no siempre devuelve**: pestañas de excepciones, alertas y escalados de los nodos; destinatarios y contenido de correos; entradas y salidas de algunos nodos y subprocesos; seguridad de las acciones de record; filtros y columnas de las listas de record. Su ausencia es ❓, no un defecto (`execution-principles.md`, principio 3).
- **Versión de Appian y si el entorno es producción**: solo si constan en `preflight.json`. Si no, «no determinada» y las cifras de uso son orientativas.
- **Datos de negocio**: nunca se leen filas. Solo hay metadatos y recuentos (`datafabric.json`).

## Privacidad

- `mcp_raw` contiene nombres de usuario (ejecuciones, versiones, miembros de grupos). En los entregables **no aparece ningún usuario**: da recuentos o roles («una cuenta personal del grupo DEM Gestores»).
- Nunca copies valores de secretos. Sigue `references/security-rules.md`.
- `mcp_raw` ya llega con los secretos enmascarados (`***ENMASCARADO***`, `***:***@`); `_meta.maskedSecrets` dice cuántos se taparon en cada fichero. Aun así, no vuelques definiciones completas al terminal ni a los entregables: cita la ubicación o enlaza el anexo.
