# Guía de objetos Appian: dónde está cada dato y cómo valorarlo

Complementa `references/lectura-mcp-raw.md` (cómo leer los ficheros). Aquí: **qué buscar en cada tipo de objeto** y heurísticas para valorar criticidad, deuda y actores.

## Dónde está cada dato

Los campos citados son los habituales en las definiciones del Dev MCP (según la skill oficial de Appian). Si en tu versión se llaman de otra forma, búscalos por sentido.

| Tipo | Dato | Dónde |
|---|---|---|
| Aplicación | Prefijo, descripción, objetos por defecto | Fichero de aplicación en `mcp_raw/_app/` |
| Record type | Origen, tabla | `sourceType`, `tableName` (también en el inventario) |
| | Campos | `fields[]`: `fieldName`, `fieldType`, `isPrimaryKey`, `length` |
| | Relaciones | `relationships[]`: `relationshipName`, `relationshipType`, record destino, campos origen/destino |
| | Vistas y acciones | `views[]` (interfaz de cada vista), `actions[]` (`actionType`, `processModelUuid`, `visibilityExpr`, `contextExpr`) |
| | Filtros de usuario | `userFilters[]` o similar |
| Interfaz | Entradas | `inputs[]` |
| | Lógica y componentes | `expression` (SAIL). Pantalla renderizada en el fichero con rol `screen` |
| Expression rule | Entradas y lógica | `inputs[]`, `expression` |
| Constante | Tipo y valor | `type`, `value` (enmascarado en el inventario si parece secreto) |
| Process model | Nodos y flujo | `nodes[]` (`id`, `type`, `name`, `connections`, `assignment`, `data`, `forms`, `decision`) |
| | Variables | `processVariables[]` (`isParameter`) |
| | Formulario de inicio | `startForm.interfaceUuid`, `inputMap` |
| | Temporizador | Configuración del nodo de inicio (`schedule` en el inventario) |
| | Grupo iniciador | `securityGroupName` (`initiatorGroup` en el inventario) |
| | Uso real | Fichero con rol `history` (`usage` en el inventario) |
| Site | Páginas | `pages[]`: `name`, `targetUuid`, `visibilityExpr`; URL en `webAddressIdentifier` |
| Integración | Llamada | Método, ruta relativa, cabeceras, cuerpo (SAIL), connected system, si modifica datos |
| Connected system | Destino y autenticación | Tipo, URL base, tipo de autenticación (nunca credenciales) |
| Web API | Endpoint | Método, alias de URL, `expression` (qué hace) |
| Grupo | Jerarquía y miembros | Padre en la definición; miembros en el fichero con rol `members` |
| Cualquiera | Quién lo usa | Ficheros con rol `dependents` (con *breadcrumb*) y aristas del grafo |
| | Historial de cambios | Fichero con rol `versions` |
| | Avisos de la plataforma | Fichero con rol `validation` |

### Tipos de nodo más comunes

| Id de esquema | Nodo |
|---|---|
| `core.0` | Inicio |
| `core.1` | Fin |
| `core.4` | Pasarela exclusiva (XOR) |
| `internal.16` | Script task |
| `internal.17` | User input task |
| `internal3.write_records_to_source_23r3` | Write Records |
| `internal3.sendemail3` | Send E-Mail |
| `internal3.integration` | Call Integration |

Fuente: [appian/dev-mcp-skills – process-models.md](https://github.com/appian/dev-mcp-skills). Para cualquier otro id, usa el catálogo de tipos de nodo de `mcp_raw/_env/` (si existe) o el Docs MCP.

### Referencias en SAIL

| Forma | Qué referencia |
|---|---|
| `rule!NOMBRE(...)` | Expression rule, interfaz, integración o decisión |
| `cons!NOMBRE` | Constante |
| `recordType!{uuid}Nombre.fields.{uuid}campo` | Record type y campo |
| `a!startProcess(processModel: ...)` | Process model (a menudo a través de una constante) |
| `a!queryRecordType`, `a!writeRecords` | Lectura y escritura de records |
| `a!queryEntity`, `a!writeToDataStoreEntity` | Lectura y escritura de data stores (modelo antiguo) |

## Heurísticas de criticidad

Un objeto es **crítico** cuando cumple varios de estos criterios:

- Referenciado por más de 5 objetos distintos (hub en `graph.json`).
- Es punto de entrada: página de site, acción de record, Web API, temporizador.
- Tiene **mucho uso real** (`usage.executions` alto).
- Maneja decisiones de negocio importantes (process model con muchas pasarelas).
- Lee o escribe entidades centrales del modelo de datos.
- Está conectado a integraciones externas.
- Tiene lógica de seguridad (permisos, validación de roles).

Márcalos con criticidad **Alta** o **Crítica**.

## Heurísticas de complejidad y deuda

| Indicador | Cómo medirlo |
|---|---|
| Expression rule grande | `sailLines` > 200; muchos `if`/`choose` anidados. |
| Interfaz grande | `sailBytes` > 80 KB o más de ~30 componentes. |
| Process model complejo | Más de 30 nodos (Appian recomienda no pasar de 50), más de 5 pasarelas, subprocesos muy anidados. |
| Lógica de negocio en la interfaz | Cálculos pesados en `a!localVariables` que deberían ser regla. |
| Valores *hardcodeados* | URLs, emails, identificadores de grupo, valores tipo "PROD"/"DEV" en literales. |
| Duplicidad | Reglas con nombres parecidos y SAIL similar. |
| Sin descripción | `description` vacía. |
| Naming inconsistente | Mezcla de estilos en el mismo módulo. |
| Avisos de validación | `validationIssues` no vacío. |
| Sin uso | `usage.executions = 0` con historial disponible. |

Para las alternativas actuales de cada patrón, ver `references/modernization-guide.md`.

## Roles típicos en aplicaciones Appian

Para inferir actores cuando el grupo no lo aclara:

| Grupo típico | Rol funcional |
|---|---|
| `*Admin*`, `*Administrators` | Administradores. |
| `*Manager*`, `*Gestor*` | Gestor / supervisor. |
| `*Approver*`, `*Revisor*` | Aprobador en flujos de aprobación. |
| `*Viewer*`, `*ReadOnly*`, `*Consulta*` | Consulta sin edición. |
| `*Initiator*`, `*Requestor*`, `*Solicitante*` | Quien arranca un proceso. |
| `*Operator*`, `*Users` | Usuario operativo. |
| `All Users`, `Everyone`, `Public` | 🔴 Atención: posible exposición amplia. |

## Informes y cuadros de mando

Suelen estar como páginas de site con interfaces de gráficos (`a!barChartField`, `a!pieChartField`, `a!gridField`, KPIs) o como vistas de record. Si se usan record types sincronizados, valora Process HQ (ver `modernization-guide.md`).

## Cuándo marcar algo como pendiente

Marca 🟡 (no ✅) cuando:

- La definición del objeto no está disponible (`detail: "none"`).
- El propósito de negocio no está claro y no hay descripción.
- Hay valores que dependen del entorno y no se ven los de producción.
- Un process model no se invoca desde ningún sitio visible (puede tener un disparador externo).
- La seguridad por objeto no está disponible y la conclusión depende de ella.
- Un grupo no tiene miembros según la extracción.

Cada pendiente lleva **responsable sugerido** (funcional, técnico Appian, DBA o responsable del sistema externo).
