# Cómo leer los datos extraídos del Dev MCP

Guía común para todos los subagentes. **Léela antes de abrir ningún fichero de `_intermedio/`.**

La skill no lee un export: la aplicación se ha extraído en vivo del entorno Appian con `scripts/devmcp_extract.py`, en modo solo lectura. Las herramientas del Dev MCP cambian entre versiones, así que **no busques herramientas concretas por nombre**. Trabaja con los roles y con el contenido.

## Ficheros de partida

| Fichero | Qué contiene | Úsalo para |
|---|---|---|
| `_intermedio/inventory.json` | Todos los objetos de la app, agrupados por tipo. Cada objeto trae `name`, `uuid`, `type`, `mcpType`, `description`, `detail`, `path` (su definición), `files` (todas sus respuestas, con rol) y campos derivados (ver abajo). | Punto de partida y control de cobertura (100%). |
| `_intermedio/graph.json` | Nodos y aristas `{source, target, refType, origin, evidence}`. `origin` = `dependents`/`dependencies` (análisis de dependencias de Appian, fiable), `uuid`/`name`/`literal` (referencia encontrada en la definición), `derived` (deducida, p. ej. `a!startProcess` vía constante). | Quién llama a quién, callers, hubs, huérfanos. |
| `_intermedio/mcp_raw/<tipo>/<uuid>/<herramienta>.json` | Respuesta tal cual de cada herramienta para ese objeto: `{"_meta": {tool, role, ok, error, ...}, "response": ...}`. | El detalle: SAIL, nodos, campos, páginas, pantallas… |
| `_intermedio/mcp_raw/_app/*.json`, `_env/*.json` | Llamadas de aplicación (definición de la app, listados) y de entorno (catálogos de tipos de nodo, etc.). | Contexto general. |
| `_intermedio/extraction_report.json` | Herramientas usadas y excluidas, errores, herramientas desactivadas por tipo, servidor y entorno (`server.url`). | Sección de cobertura y limitaciones. |
| `_intermedio/datafabric.json` (opcional) | Metadatos del data fabric y `count` por record type (Appian MCP Server). | Volúmenes en 03 y en 12. |
| `_intermedio/preflight.json` | Estado de los 3 MCP al empezar. | Sección de cobertura. |

## Roles de los ficheros (`_meta.role`)

| Rol | Qué es | Dónde se usa |
|---|---|---|
| `definition` | La definición del objeto (SAIL, nodos, campos, páginas…). Es la fuente principal. | Todos los documentos |
| `dependents` | Quién referencia a este objeto, con *breadcrumb* (p. ej. «Interface Definition: Line 19»). | Callers, impacto |
| `dependencies` | Qué referencia este objeto. | Llamadas salientes |
| `history` | Ejecuciones reales del process model (total, última, fallos). | 07, 08, 12 (prioridad), 13 (código muerto) |
| `versions` | Historial de versiones (quién y cuándo). | 09 (versionado), 13 |
| `validation` | Avisos de validación de la plataforma (funciones obsoletas, errores). | 09, 13 |
| `screen` | Árbol de componentes de la interfaz renderizada con entradas vacías. | 10 (pantallas), 01 |
| `members` | Miembros de un grupo (grupos y usuarios). | 04 |
| `other` | Cualquier otra herramienta (p. ej. una nueva que haya añadido Appian). **Ábrela y aprovecha lo que aporte**: seguridad, métricas, configuración… | Donde encaje |

Si un objeto tiene `detail: "none"`, no hubo herramienta que devolviera su definición (por ejemplo, CDTs o decisiones en algunas versiones del Dev MCP). Documenta el objeto con lo que haya (nombre, tipo, dependencias) y márcalo 🟡 indicando que la definición no está disponible por Dev MCP.

## Campos derivados en `inventory.json`

`build_model.py` ya ha calculado, cuando la respuesta lo permitía:

- **Process model:** `nodeCount`, `userTaskCount`, `subProcessCount`, `startType` (`none`/`timer`/`message`), `hasRecurrence`, `schedule` (configuración del temporizador tal cual), `startFormInterface`, `initiatorGroup`, `usage` (`executions`, `lastExecution`, `failed`).
- **Interfaz, regla, Web API, integración:** `sailBytes`, `sailLines`.
- **Constante:** `value` (enmascarado si parece secreto, con `maskedSecret: true`), `typeRef`, `valueRef`.
- **Integración:** `method`, `endpoint`, `connectedSystemRef`, `modifiesData`.
- **Connected system:** `csType`, `baseUrl` (credenciales enmascaradas), `authType`.
- **Web API:** `method`, `endpointPath`.
- **Record type:** `fieldCount`, `sourceType`, `tableName`, `urlStub`, `relationshipCount`.
- **Site:** `pageCount`, `urlStub`. **Grupo:** `parentGroup`, `memberGroups`, `userCount`.
- **Cualquiera:** `versions` (`count`, `lastModifiedOn`, `lastModifiedBy`), `validationIssues`, `screen`, `extraTools`.

Son una ayuda: ante la duda, **la fuente es el fichero `definition`**.

## Cómo interpretar las respuestas

- La forma exacta de las respuestas puede variar entre versiones del Dev MCP. Pueden venir envueltas (`{"result": {...}}`), y el uuid o el nombre pueden llamarse `uuid`/`objectUuid` y `name`/`objectName`. Interprétalas con sentido común; no asumas un esquema fijo.
- Process models: cada nodo suele tener `id`, `type` (id de esquema, p. ej. `core.0` inicio, `core.1` fin, `core.4` XOR, `internal.16` script task, `internal.17` user input task, `internal3.write_records_to_source_23r3` write records, `internal3.sendemail3` email, `internal3.integration` call integration), `name`, `connections` (ids destino), `assignment`, `data`, `forms` y `decision` (condiciones de las pasarelas). Si aparece un tipo de nodo que no reconoces, búscalo en `mcp_raw/_env/` (catálogo de tipos de nodo, si existe) o consúltalo en el Docs MCP.
- Las referencias a record types en SAIL tienen la forma `recordType!{uuid}Nombre.fields.{uuid}campo`. Traduce siempre a nombres legibles con `inventory.json`.
- Los uuids no se muestran al lector salvo en `INVENTARIO.md`.

## Formato de evidencia

Toda afirmación importante lleva evidencia verificable:

```
Evidencia: mcp:<tipo>/<nombre>#<ubicación>
```

- `<ubicación>` es una ruta dentro de la definición (`nodes[3].decision`, `pages[2].visibilityExpr`, `fields.importe`) o el *breadcrumb* de dependencias (`Interface Definition: Line 19`).
- Ejemplos: `mcp:processModel/DEM Alta Solicitud#nodes[2]`, `mcp:interface/DEM_SolicitudForm#expression (línea 4)`.
- Si la conclusión viene de un documento oficial: `Fuente: <URL de docs.appian.com>`.
- Si es inferida, márcala 🔵 y explica en una línea de qué se infiere.

## Qué no está disponible por Dev MCP

Dilo explícitamente en el documento afectado, en lugar de rellenar huecos:

- **Valores por entorno** (import customization files): no existen en la plataforma, solo en el paquete de despliegue.
- **Definiciones de tipos sin herramienta** en la versión instalada (mira `detail: "none"` y `extraction_report.json`).
- **Seguridad por objeto (role maps)**: solo si alguna herramienta la devuelve (revisa ficheros `other`). Si no, limita la matriz a lo verificable: grupo iniciador de cada process model, visibilidad de páginas, asignaciones de tareas y expresiones de seguridad en SAIL.
- **Datos de negocio**: nunca se leen filas. Solo hay metadatos y recuentos (`datafabric.json`).

## Privacidad

- `mcp_raw` puede contener nombres de usuario (historial, versiones, miembros de grupos). En los entregables, **no listes usuarios**: da recuentos o roles. Solo `09-valor-adicional.md` puede citar el último autor de cambios cuando sea relevante para el mantenimiento.
- Nunca copies valores de secretos. Sigue `references/security-rules.md`.
