# Guía de modernización y refactorización

Catálogo que usa `rebuild-architect` para el diagnóstico de `13-modernizacion-refactor.md`. Cada patrón indica **cómo detectarlo** con los datos extraídos, **qué problema** supone y **qué alternativa actual** recomienda Appian, con la **fuente oficial**.

**Reglas de uso**

1. Las URLs apuntan a la documentación de Appian 26.6, revisada el 2026-09-30. Antes de recomendar, **confirma en el Docs MCP** la versión del entorno (`references/docs-mcp-usage.md`). Si no puedes, indica «sin verificar para la versión X».
2. Un patrón solo se reporta si hay **evidencia en objetos concretos**. Nada de recomendaciones genéricas.
3. Las entradas marcadas **[heurística]** son criterios de esta skill, no de Appian: preséntalas como tales.
4. La lista no es cerrada. Si encuentras otro patrón, añádelo como hallazgo con su propia evidencia y fuente.

---

## A. Datos

| ID | Señal de detección | Problema | Alternativa actual | Fuente |
|---|---|---|---|---|
| DAT-01 | Objetos de tipo CDT y data store en la app; `a!queryEntity`, `Write to Data Store Entity`, query rules en el SAIL. | Modelo de datos antiguo: sin relaciones de record, sin capacidades del data fabric (Process HQ, IA, búsqueda). | Record types sincronizados (*Optimized Data Access*). Appian permite **modernizar sin refactorizar**: crear record types sobre las mismas tablas y usarlos en lo nuevo, manteniendo los objetos existentes. | [Build your best data fabric](https://docs.appian.com/suite/help/26.6/build-best-data-fabric.html) · [Use data fabric in existing apps](https://docs.appian.com/suite/help/26.6/use-synced-record-types-in-existing-apps.html) |
| DAT-02 | Record types con `sourceType` distinto de base de datos sincronizada, o sin relaciones cuando la tabla tiene claves ajenas evidentes (campos `…Id`). | Record types *legacy* (acceso directo sin funcionalidades): sin relaciones ni funcionalidades relacionadas. | Record types sincronizados o, si no se puede sincronizar, no sincronizados con funcionalidades habilitadas. | [About record types – tipos](https://docs.appian.com/suite/help/26.6/Record_Type_Object.html#types-of-record-types) · [Optimized data access](https://docs.appian.com/suite/help/26.6/about-data-sync.html#optimized-data-access) |
| DAT-03 | Campos que actúan como clave ajena sin `relationships[]` declaradas. | Navegación y consultas manuales entre entidades; más código y más errores. | Relaciones de record type. | [Record type relationships](https://docs.appian.com/suite/help/26.6/record-type-relationships.html) |
| DAT-04 | Seguridad a nivel de registro definida con una **expresión** en el record type. | No compatible con el acceso al data fabric desde el Appian MCP Server y otras capacidades. | Sustituir la expresión por reglas de seguridad (*security rules*). | [Record-level security – reemplazar la expresión](https://docs.appian.com/suite/help/26.6/record-level-security.html#replace-a-security-expression-with-security-rules) |
| DAT-05 | Tablas grandes (`datafabric.json` → `count`) sincronizadas sin filtros. | Consumo y rendimiento; límites de filas por tier. | Filtros de sincronización (*sync filters*). | [Optimized data access – límites de filas](https://docs.appian.com/suite/help/26.6/about-data-sync.html#optimized-data-access) |
| DAT-06 | Historial o auditoría implementados a mano (tablas `*_HIST`, `*_LOG`, escrituras extra en cada proceso). | Lógica repetida y difícil de analizar. | Eventos de record (*record events*), base también de Process HQ. | [Record events](https://docs.appian.com/suite/help/26.6/record-events.html) · [Process HQ](https://docs.appian.com/suite/help/26.6/processhq.html) |

## B. Procesos

| ID | Señal de detección | Problema | Alternativa actual | Fuente |
|---|---|---|---|---|
| PRO-01 | `nodeCount` > 50. | Difícil de mantener y más consumo de memoria («Too many nodes»). | Dividir en subprocesos. | [Design guidance – process models](https://docs.appian.com/suite/help/26.6/appian-recommendations.html#process-model-design-guidance) |
| PRO-02 | Más de 100 `processVariables`. | Mantenimiento y memoria («Too many process variables»). | Parámetros de actividad o subprocesos. | Misma fuente |
| PRO-03 | Nombre del proceso o de las tareas sin expresión (texto fijo). | Tareas y procesos indistinguibles en listas y monitorización. | Nombres dinámicos. | Misma fuente |
| PRO-04 | Subprocesos que reciben CDTs **por referencia**. | Riesgo de que las instancias activas se detengan por excepción al publicar una nueva versión del CDT. | Pasar por valor. | [Health Check – CDTs by reference](https://docs.appian.com/suite/help/26.6/understanding-the-health-check-report.html#design) |
| PRO-05 | Nodos desatendidos con instancias múltiples (MNI) y encadenamiento de actividades. | Rendimiento y límite de encadenamiento. | Operación masiva (escritura de una lista) o funciones de bucle en un script task. | Misma fuente · [Design guidance](https://docs.appian.com/suite/help/26.6/appian-recommendations.html#process-model-design-guidance) |
| PRO-06 | Eventos de envío de mensaje sin proceso destino. | Mensaje a todas las instancias: coste creciente. | Indicar el id del proceso destino. | [Design guidance](https://docs.appian.com/suite/help/26.6/appian-recommendations.html#process-model-design-guidance) |
| PRO-07 | `usage.executions = 0` en PRO, o process model huérfano en el grafo. | Código muerto o funcionalidad abandonada. | Validar con negocio y retirar. | [heurística] |
| PRO-08 | Varios process models con la misma secuencia de nodos o que escriben la misma entidad con lógica parecida. | Duplicidad; cambios que hay que repetir. | Subproceso común o acción de record única. | [heurística] |
| PRO-09 | Botones con `a!startProcess` en interfaces para acciones sobre un registro. | Acciones repartidas en interfaces en vez de declaradas en el record. | Acciones de record (*record actions*) con su seguridad. | [Record actions](https://docs.appian.com/suite/help/26.6/record-actions.html) |

## C. Interfaces y expresiones

| ID | Señal de detección | Problema | Alternativa actual | Fuente |
|---|---|---|---|---|
| UI-01 | `validationIssues` con funciones o componentes obsoletos; nombres con sufijo de versión antigua (`_17r1`, `_18r3`, `_22r2`…). | Funcionalidad deprecada que se retirará o versiones antiguas de funciones. | Versión actual del componente o función (consúltala en el Docs MCP). | [Deprecated features](https://docs.appian.com/suite/help/26.6/Deprecated_Features.html) · [All functions](https://docs.appian.com/suite/help/26.6/Appian_Functions.html) |
| UI-02 | Componentes deprecados: *Paging Grid* (`a!gridTextColumn`…), *Dashboard Layout*, *Column-based layouts*, *Submit Button*. | Retirada futura. | Componentes actuales (p. ej. `a!gridField`, layouts actuales). | [Deprecated features](https://docs.appian.com/suite/help/26.6/Deprecated_Features.html) |
| UI-03 | Consultas sin paginar (batch `-1`) o bucles sobre grandes listas, bucles anidados de más de 2 niveles. | Consumo de memoria y lentitud. | Paginar y filtrar; evitar bucles de más de ~500 elementos y anidados. | [Expressions best practices – memoria](https://docs.appian.com/suite/help/26.6/expressions-best-practices.html#designing-memory-efficient-expressions) |
| UI-04 | Variables locales o entradas de regla no usadas; llamadas a reglas con varias entradas sin sintaxis de palabra clave; funciones no documentadas. | Recomendaciones de diseño de Appian (mantenimiento, compatibilidad). | Corregir según la guía. | [Design guidance – expressions](https://docs.appian.com/suite/help/26.6/appian-recommendations.html#expression-design-guidance) |
| UI-05 | `sailBytes` muy alto (> 80 KB) o interfaces con muchas responsabilidades. | Mantenimiento difícil. | Descomponer en interfaces hijas y reglas. | [heurística] |
| UI-06 | Listas y cuadros de mando construidos a mano con consultas a data stores. | Más código; sin capacidades de records. | Componentes basados en records (*records-powered components*) y listas de record. | [Records-powered components](https://docs.appian.com/suite/help/26.6/records-powered-components.html) |
| UI-07 | Literales de negocio repetidos en SAIL (estados, umbrales, grupos). | Reglas ocultas y difíciles de cambiar. | Constantes, tablas de referencia o decisiones. | [heurística] |

## D. Integraciones

| ID | Señal de detección | Problema | Alternativa actual | Fuente |
|---|---|---|---|---|
| INT-01 | Uso de `a!httpQuery`, `a!httpWrite`, smart services *HTTP Query/File Upload/File Download*, conectores deprecados (`a!sfc*`, `a!shp*`, `a!dyn*`, `a!sbl*`). | Deprecados. | Objetos de integración con connected systems. | [Deprecated features](https://docs.appian.com/suite/help/26.6/Deprecated_Features.html) |
| INT-02 | Integraciones sin connected system, URLs completas en la integración o en constantes de texto, credenciales en cabeceras literales o en la URL. | Configuración por entorno frágil y secretos expuestos. | Connected system con autenticación gestionada y valores por entorno. | [Connected systems](https://docs.appian.com/suite/help/26.6/Connected_System_Object.html) |
| INT-03 | Connected system sin autenticación o apuntando a un entorno distinto del extraído (p. ej. un host de desarrollo en PRO). | Riesgo de seguridad y de datos cruzados. | Autenticación y parametrización por entorno. | [heurística] + fuente INT-02 |
| INT-04 | Integraciones que modifican datos sin tratamiento de errores en el proceso que las llama (sin camino de excepción). | Fallos silenciosos. | Manejo de errores explícito en el proceso. | [heurística] |

## E. Seguridad

| ID | Señal de detección | Problema | Alternativa actual | Fuente |
|---|---|---|---|---|
| SEG-01 | Role maps con usuarios individuales (si alguna herramienta devuelve la seguridad). | Mantenimiento de permisos por persona. | Siempre grupos en los role maps. | [Object security](https://docs.appian.com/suite/help/26.6/object-security.html) |
| SEG-02 | Objetos sin grupo con permiso de lectura o con administradores como único grupo. | Antipatrón señalado por Health Check. | Grupos de lectura y administración separados. | [Health Check – design](https://docs.appian.com/suite/help/26.6/understanding-the-health-check-report.html#design) |
| SEG-03 | Constantes con aspecto de secreto (`maskedSecret`). | Secretos en objetos de diseño. | Credenciales en connected systems (valores por entorno). | [heurística] + [Connected systems](https://docs.appian.com/suite/help/26.6/Connected_System_Object.html) |

## F. Oportunidades (no son deuda)

Proponlas **solo si resuelven una necesidad observada** en la app, y siempre con fuente:

| Capacidad | Cuándo proponerla | Fuente |
|---|---|---|
| Process HQ (análisis y cuadros de mando de negocio) | Hay informes a mano o necesidad de medir procesos. Requiere record types sincronizados. | [Process HQ](https://docs.appian.com/suite/help/26.6/processhq.html) |
| AI skills | Clasificación o extracción de documentos a mano, o uso de *Intelligent Document Processing* / *Start Doc Extraction* (deprecados). | [AI skills](https://docs.appian.com/suite/help/26.6/ai-skills-intro.html) · [Deprecated features](https://docs.appian.com/suite/help/26.6/Deprecated_Features.html) |
| Agentes de IA de Appian | Tareas de análisis o redacción que hoy hace una persona sobre datos de la app. | [AI agents](https://docs.appian.com/suite/help/26.6/about-ai-agents.html) |
| Portals | Web APIs expuestas para que un frontal externo muestre formularios a usuarios no Appian. | [Portals](https://docs.appian.com/suite/help/26.6/portals-design.html) |
| Appian MCP Server | Necesidad de consultar datos o lanzar procesos desde asistentes de IA externos. | [Appian MCP Server](https://docs.appian.com/suite/help/26.6/appian-mcp-server.html) |
| Composer | Reconstrucción asistida por IA a partir de requisitos (`12`). | [How Composer works](https://docs.appian.com/suite/help/26.6/how-dev-agent-works.html) |

## G. Correspondencia orientativa actual → propuesto

| Actual | Propuesto (a confirmar caso a caso) |
|---|---|
| CDT + data store + `a!queryEntity` / query rule | Record type sincronizado + `a!queryRecordType` |
| `Write to Data Store Entity` | `Write Records` |
| Listas y detalles a mano en interfaces | Lista de record, vistas de record, componentes basados en records |
| Botón con `a!startProcess` sobre un registro | Acción de record |
| Tablas de historial a mano | Eventos de record |
| Umbrales y estados en literales | Constantes, tablas de referencia o decisiones |
| `a!httpQuery` / smart services HTTP | Integración + connected system |
| Process model monolítico (> 50 nodos) | Proceso principal + subprocesos por responsabilidad |
