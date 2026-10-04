# Guía de objetos Appian: dónde está cada dato y cómo valorarlo

Complementa `references/lectura-mcp-raw.md` (cómo leer los ficheros). Aquí: **qué buscar en cada tipo de objeto** y criterios para valorar importancia, deuda y actores. La certeza (✅/🔵/❓) y la severidad de los hallazgos (Alta/Media/Baja) siguen `presentation-rules.md`, Regla 7.

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

## Importancia de un objeto

- **Process models**: «proceso crítico» es solo el que marca `criticality` en el inventario (una única fórmula para todos los documentos, ver `lectura-mcp-raw.md`). No la recalcules ni la sustituyas por otra.
- **Resto de objetos**: estos criterios ayudan a decidir qué describir con más detalle y qué priorizar en 12 y 13. No son una etiqueta: la severidad solo se da a hallazgos.
  - Lo referencian 5 o más objetos (hub en `graph.json`).
  - Es punto de entrada: página de site, acción de record, Web API, temporizador.
  - Tiene mucho uso real (`usage.executions` alto, en producción).
  - Lee o escribe entidades centrales del modelo de datos.
  - Llama a integraciones externas.
  - Tiene lógica de seguridad (permisos, comprobación de grupos).

## Indicadores de complejidad y deuda

| Indicador | Cómo medirlo |
|---|---|
| Expression rule grande | `sailLines` > 200; muchos `if`/`choose` anidados. |
| Interfaz grande | `sailBytes` > 80 KB o más de ~30 componentes. |
| Process model complejo | Más de 50 nodos o más de 100 variables de proceso (recomendaciones de diseño de Appian, [fuente](https://docs.appian.com/suite/help/26.6/appian-recommendations.html#process-model-design-guidance)); muchas pasarelas o subprocesos muy anidados. |
| Lógica de negocio en la interfaz | Cálculos pesados en `a!localVariables` que deberían ser regla. |
| Valores *hardcodeados* | URLs, emails, identificadores de grupo, valores tipo "PROD"/"DEV" en literales. |
| Duplicidad | Reglas con nombres parecidos y SAIL similar. |
| Sin descripción | `description` vacía en la respuesta. Si la respuesta no trae el campo, no es indicio (dato ausente no es defecto). |
| Naming inconsistente | Mezcla de estilos en el mismo módulo. |
| Avisos de validación | `validationIssues` no vacío. |
| Sin uso | `usage.executions = 0` con historial disponible y en un entorno de producción. |

Para las alternativas actuales de cada patrón, ver `references/modernization-guide.md`.

## Roles típicos en aplicaciones Appian

Para inferir actores cuando el grupo no lo aclara (es una inferencia: 🔵, con el nombre del grupo como evidencia):

| Grupo típico | Rol funcional |
|---|---|
| `*Admin*`, `*Administrators` | Administradores. |
| `*Manager*`, `*Gestor*` | Gestor / supervisor. |
| `*Approver*`, `*Revisor*` | Aprobador en flujos de aprobación. |
| `*Viewer*`, `*ReadOnly*`, `*Consulta*` | Consulta sin edición. |
| `*Initiator*`, `*Requestor*`, `*Solicitante*` | Quien arranca un proceso. |
| `*Operator*`, `*Users` | Usuario operativo. |
| `All Users`, `Everyone`, `Public` | Posible exposición amplia: lo valora `04-seguridad-grupos.md`. |

## Informes y cuadros de mando

Suelen estar como páginas de site con interfaces de gráficos (`a!barChartField`, `a!pieChartField`, `a!gridField`, KPIs) o como vistas de record. Si se usan record types sincronizados, valora Process HQ (ver `modernization-guide.md`).

## Cuándo marcar algo como pendiente

Marca ❓ (no ✅) cuando la conclusión depende de un dato que la extracción no trae: su ausencia no prueba que falte en la aplicación (`execution-principles.md`, principio 3). Por ejemplo:

- La definición del objeto no está disponible (`detail: "none"`).
- El propósito de negocio no está claro y no hay descripción.
- Hay valores que dependen del entorno y no se ven los de producción.
- Un process model no se invoca desde ningún sitio visible (puede tener un disparador externo).
- La seguridad por objeto no está disponible y la conclusión depende de ella.
- Un grupo no tiene miembros según la extracción (la herramienta puede no devolverlos todos).
- Falta configuración que el Dev MCP no siempre devuelve: excepciones y alertas de nodos, destinatarios de correo, seguridad de acciones de record.

Cada pendiente lleva **responsable sugerido** (funcional, técnico Appian, DBA o responsable del sistema externo).
