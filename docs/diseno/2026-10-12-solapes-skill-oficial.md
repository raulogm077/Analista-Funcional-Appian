# Solapes entre la skill oficial `appian` y `appian-best-practices`

Versiones comparadas: `appian/dev-mcp-skills` @ `6e87fb6` (2026-09-23) y `Analista-Funcional-Appian` @ `dc51944`
(2026-10-11, 0.7.0-beta.3).

- **OF** = skill oficial (`skills/appian/`). No se edita.
- **BP** = `skills/appian-best-practices/`. Todo lo que se propone es sobre BP.
- L = líneas. Las contradicciones (§2) y los comportamientos (§1) están contrastados en los ficheros. Los números de
  línea de los duplicados (§3) salen de la pasada de comparación y están muestreados, no revisados uno a uno.

## Cómo quedó (12 de octubre de 2026)

Este análisis es el punto de partida; lo que se hizo con él está en `docs/plan/2026-10-12-correccion-buenas-practicas.md`.

- **§1, comportamientos repetidos o enfrentados:** resueltos. Las puertas 1 y 4 de `10` no repiten lo que la skill
  oficial ya comprobó al escribir; calibración, descubrimiento y dependientes se dicen una vez en `SKILL.md`; reintentos,
  alcance y carga de referencias están en `14-official-skill-divergences.md` §2.
- **§2, contradicciones:** verificadas contra docs.appian.com (26.9). Los veredictos, que cambian varias de las
  propuestas de esta sección, están en el plan §1.
- **§3 y §4, duplicados y notas de delegación:** no se recortan. Buenas prácticas tiene que valer sin la skill oficial y
  es la que lleva la fuente de cada regla; la oficial falla en 18 puntos comprobados y cambia a menudo. La doctrina
  repetida se queda con su fuente y solo se quitó la mecánica copiada (las cinco comprobaciones de `change-review` en la
  puerta 4 y la lista de tipos «manuales» de `01` §1). Las notas de delegación remiten ahora al doc 14.
- **§6, «Cómo cerrarlo»:** hechos los puntos 1, 2 y 4; el 3 se descartó por lo anterior; el 5 (avisar a Appian) queda a
  criterio de Raúl.

## Resumen

1. El reparto de planos funciona: OF es mecánica del MCP y BP es doctrina, decisiones y puertas. La duplicación literal es
   pequeña (≈5 % de `03`, ≈10 % de `06`, ≈5 % de `09`, ≈0 % de `07`, `11`, `12`, `13`; más alta en `04` y en partes de
   `01` y `02`).
2. El problema mayor no es lo repetido, sino lo **contradictorio**: unas 45 reglas en las que el agente recibe dos órdenes
   distintas con las dos skills cargadas. En varias gana OF según la tabla *Which Source Wins* de BP (`SKILL.md` L222:
   recetas de consulta, null-safety, naming), justo en temas donde BP dice otra cosa y cita la documentación.
3. Hay 12 **comportamientos de procedimiento** que se hacen dos veces o chocan (validar, verificar, renderizar,
   descubrir, documentación, reintentos, alcance).
4. Cinco notas de delegación de BP («Where the depth lives…») remiten a OF y a continuación repiten lo delegado.

## 1. Comportamientos repetidos o enfrentados (procedimiento)

| # | Comportamiento | BP | OF | Tipo | Propuesta |
|---|---|---|---|---|---|
| 1 | Validar la sintaxis de una interfaz | `10` puerta 1 L97-99 y puerta 4 paso 1 L159: `validateExpression` con `isInterface: true` siempre | `SKILL.md` paso 7B-7C; `validation-checkpoint.md` L91 («Interfaces with ri! inputs: Skip Step 7B») y L100-104 (`createInterface`/`updateInterface` ya hacen parse + design guidance + evaluación) | Repetido y enfrentado | La puerta acepta como evidencia el resultado de crear/actualizar por MCP; `validateExpression` solo sin MCP de escritura o para código pegado. `isInterface` ya lo explica el esquema de la herramienta |
| 2 | Comprobar que funciones, parámetros, iconos y enumeraciones existen | `10` puerta 4 paso 2 L160-163 («review by hand…») | `SKILL.md` paso 4 (4A/4B con artefacto obligatorio), `sail-verification-checkpoint.md`, `interface-generation-checklist.md` §5 | Repetido | Evidencia de la puerta = artefacto del paso 4 de OF. Revisión a mano solo si OF no está instalada |
| 3 | Comprobaciones tras renderizar | `10` puerta 4 paso 5 L168-174 copia las cinco de OF («these five when this was written») | `change-review.md` L217-223 | Delegado que repite | Borrar las cinco; dejar el puntero y las tres propias (L176-180) |
| 4 | Cuántas veces renderizar | `10` puerta 4 paso 4 L165: dos (poblado y vacío) | `SKILL.md` paso 7D y `validation-checkpoint.md` L114-125: una por rama condicional | Enfrentado | Una sola regla: poblado + vacío, más las ramas que pide OF (las de 7D cuentan como render poblado si llevan datos) |
| 5 | Releer lo escrito | `SKILL.md` L252 («The API returned 200… Read back») | `change-review.md` L4 y L6-43 | Repetido | Dejar la frase como racionalización y remitir a `change-review` para qué releer |
| 6 | Dependientes antes de tocar un objeto | `SKILL.md` L121-122, `10` L107-108, `08` §2 L96-100 (tres veces) | `confirmation-patterns.md` flujo 1 (solo borrado y renombrado) | Complementario; repetido dentro de BP | Una sola mención en BP (puerta 1). Para borrar, puntero al flujo de OF |
| 7 | Descubrir el entorno | `SKILL.md` L96-97 y L119-121 («don't list the whole application») | `change-planning.md` L2-21 (mismo principio, con reglas por tamaño) y `tools-mcp.md` L58-76 (listar el tipo antes de cada `create`) | Repetido, con roce | BP se queda con el plano de proyecto (`CLAUDE.md`, `analisis/tecnico.md`, convenciones) y remite a `change-planning` para el entorno. Aclarar que «no listar toda la aplicación» no anula el listado previo a crear |
| 8 | No inventar funciones ni UUID | `SKILL.md` L158-160, `10` L105-106 | `tools-mcp.md` L85-215, `sail-verification-checkpoint.md` | Repetido | Una línea de principio + puntero |
| 9 | Documentación como requisito para escribir | `SKILL.md` L129-131 y L152-154: sin MCP de documentación, parar, porque «the official skill's function checks come back empty» | `documentation-lookup-strategy.md`: la existencia de funciones se comprueba con `functions.json` + `curl` (nivel 2A); la búsqueda semántica es el nivel 3, opcional (L339: «Tool not in tool list → Proceed without Tier 3») | **Contradicción** | Corregir BP: la parada no se apoya en cómo trabaja hoy OF. Si se quiere mantener como exigencia propia, decirlo así |
| 10 | Orden de creación y tipos «manuales» | `01` §1 L29-35: la nota de delegación enumera Connected Systems, Record Actions y Portals como no automatizables | `change-planning.md` L127-154 (esa lista); pero `record-types.md` L134-262 documenta acciones, y el MCP actual tiene `addRecordTypeAction`, `createConnectedSystem`, `createPortal` | Delegado que repite un dato caducado | Dejar solo el puntero, sin enumerar |
| 11 | Reintentar una escritura | `SKILL.md` L270 (bandera roja: reintentar sin comprobar si la primera persistió), `11` §2 | `change-review.md` L157-165: ante timeout o 500, reintentar una vez | Enfrentado | Gana BP; escribirlo: tras timeout de un `create`, listar antes de reintentar |
| 12 | Alcance del cambio | `SKILL.md` L288 («Nothing changed outside the agreed scope»), L99-103 (`construccion/<U>.md`, objetos congelados) | `confirmation-patterns.md` L56-65 y flujo 5: completar sin preguntar lo obligatorio (relación inversa, relación a usuario) | Enfrentado | Decir en BP que la compleción obligatoria de OF no cuenta como salirse del alcance, salvo que toque un objeto congelado: entonces se para y se pregunta |
| 13 | Calibración del esfuerzo | `SKILL.md` L36 («Don't open the reference docs» en cambio cosmético) | `SKILL.md` L199-219: cargar siempre siete ficheros antes de cualquier herramienta | Enfrentado | Aclarar que la calibración de BP gobierna sus propias referencias, no la carga de OF |

## 2. Contradicciones de contenido

> **Actualización del 12-10-2026.** Estas contradicciones se verificaron contra docs.appian.com (26.9). La columna
> «Propuesta» de esta sección queda sustituida por los veredictos de `docs/plan/2026-10-12-correccion-buenas-practicas.md` §1; varias
> cambian de sentido (nombres de auditoría, nombre de las relaciones, visibilidad de página, `data`).

«Propuesta» dice a favor de quién resolver; donde BP cita la documentación y OF no, conviene confirmarlo con el MCP de
documentación antes de fijarlo.

### Expresiones, consultas y rendimiento

| Tema | BP | OF | Propuesta |
|---|---|---|---|
| `and()`/`or()` cortocircuitan | `04` §7 L170-171, `05` §3 L92-93: sí (cita *Interface Performance*) | `short-circuit-patterns.md` L14: «DO NOT short-circuit»; se carga siempre | Confirmar en la doc. Si gana BP: mantener como regla de rendimiento y añadir que para guardas de null vale el `if()` anidado de OF |
| `fetchTotalCount` | `05` §2 L68: ejecuta la consulta dos veces; solo donde se muestra un total | `query-record-type-patterns.md` L292-308: «REQUIRED» en toda consulta | BP. Escribir la excepción junto a la nota que manda cargar ese fichero |
| Tamaño de lote | `05` §2 L39-50, L62; `04` §6 L150: `batchSize: 5000` es antipatrón; filtrar en origen | `function-reference.md` L54: «Use `batchSize: 5000`»; `expressions.md` L1539-1555: una consulta y filtrar en memoria | BP, con nota expresa |
| `choose()` | `04` §4 L99-100, `05` §3 L104: para elegir por índice | `function-reference.md` L41, L65: no usar; `a!match()` | Ceder: quitar la recomendación activa |
| `a!forEach(null)` | `04` §5 L129-130: devuelve lista vacía (cita la doc) | `expressions.md` L1353: devuelve null | BP |
| `length()` en listas | `04` §5 L135: comprobar listas con `length()` | `expressions.md` L1375: error, usar `count()` (OF se contradice en `function-reference.md` L155) | BP |
| Cuándo crear test cases | `04` §8 L192, L207: con toda regla, caso NULL siempre, antes de la regla | `expression-rules.md` L90, L102: omitir en reglas triviales; después de guardar | BP; decir que prevalece |
| «Hoy» y zona horaria | `04` §11 L248: `todate(local(now()))` | `date-time-patterns.md` L128, L139: `todate(now())` | BP |
| Recursión | `04` §7 L182: admitida hasta profundidad 20 | `expression-rules.md` L85: error en ejecución | BP, con frase aclaratoria |
| Constantes de tipo usuario | `04` §9 L227: grupo antes que usuario | `supporting-objects.md` L29: las propone para cuentas de sistema | BP |
| Historial del objeto | `04` §3 L69-71, `10` L229-230: fuera del objeto | `expressions.md` L1503-1506, L1675-1678: en la descripción y sufijos `_v2` | BP; decir si alcanza a la descripción |

### Modelo de datos

| Tema | BP | OF | Propuesta |
|---|---|---|---|
| Clave primaria | `01` §2.1 L78: clave compuesta válida con sync; PK entera o de texto | `data-modeling.md` L5-12: una sola, `id`, INTEGER; «Appian does not support» compuestas | BP, con alcance: tabla nueva por MCP → `id` de OF; compuesta o texto solo en fuentes existentes |
| PK autogenerada | `01` §8.1 L310: «Don't let Appian auto-generate the PK» (habla de CDT) | `data-modeling.md` L9: «Auto-generated by Appian» | Acotar la frase de BP a CDT o moverla a §7 |
| Campos de auditoría | `01` §3.4 L143: `createdOn`/`modifiedOn`, rellenar siempre | `data-modeling.md` L158-172: `createdAt`/`updatedAt` opcional; nunca en tablas de referencia ni de unión | Nombres de OF; la regla de BP formulada por función (campo *Last Modified* obligatorio con sync incremental) |
| Vigencia en datos de referencia | `01` §4.3 L200: `startDate`/`endDate` antes que `isActive` | `data-modeling.md` L95-109: cuatro campos fijos con `isActive`, sin atributos temporales | OF para lookups; limitar BP a datos con periodo de validez |
| Nombre de las relaciones | `01` §4.2 L188: como el record type relacionado | `relationship-patterns.md` L313-370: derivado del campo FK; usuario `{campo}User` | Puntero a OF; conservar el porqué |
| 3FN frente a tablas de informe | `01` §12.1 L442, §12.3 L461; `00` L35 | `data-modeling.md` L69, L302: 3FN mínimo, derivados no almacenados | BP, declarado como excepción |
| Record list | `01` §9.1 L370; `09` §1.3 L37-39; `00` L97: configurarla y reutilizarla | `record-summary-views.md` L62-63: «DEPRECATED»; `appian-workflow-patterns.md` L146 | BP, con la excepción (rejilla propia) y puntero a cómo cablear acciones |
| Adjuntos | `01` §8.bis.1 L329: no en carpetas | `supporting-objects.md` L105: subcarpeta «Attachments» | BP |
| Lookup compartido | `01` §1.1 L49, §10 L399: con dos entidades | `data-modeling.md` L33: «3+ entities» | Aclarar en BP |

### Procesos, seguridad y sitios

| Tema | BP | OF | Propuesta |
|---|---|---|---|
| Escribir en línea o con proceso | `03` §8 L418-421: «to modify it, use a process model»; `a!writeRecords` no aparece en ningún doc de BP | `write-records-patterns.md` L9-31: sin proceso existente → `a!writeRecords()` en línea | Fila nueva en `00` con criterio propio (eventos, notificación, integración o varios registros → proceso; CRUD simple → en línea) y puntero a OF para la mecánica |
| Botón que arranca un proceso | `00` L70: evitarlo; usar record action | `write-records-patterns.md` L421-447: `a!startProcess` en `saveInto` | BP; lo de OF, mecánica de excepción |
| Visibilidad de página | `09` §7.3 L270-272: «This is not security» | `security.md` L82, `security-patterns.md` L93: «Page-level security uses visibilityExpr» | BP; nombrar la discrepancia |
| Role map del sitio | `09` §7.1 L242-247: configurarlo a mano, no hereda | `security.md` L13, L46; `security-patterns.md` L63: nace con el role map de la aplicación (`appUuid`) | Reescribir BP como «revisar»: su «why» no vale para objetos creados con `appUuid` |
| Seguridad de reglas, interfaces y constantes | `06` §3 L64-66: heredan de la carpeta | `security.md` L114: del role map de la aplicación | BP; decirlo |
| Un grupo por rol | `06` §1 L24-25: uno por rol de negocio | `security.md` L37: no crear grupos por si acaso | Matizar BP: grupo cuando el rol difiere en acceso |
| Nombre de los grupos | `08` §1 L50-52: grupos de negocio sin prefijo | `supporting-objects.md` L82-84: `PREFIX RoleName` | Según `SKILL.md` L222 gana OF: corregir `08` o declarar la excepción |
| A quién se cede el naming | `SKILL.md` L222: a OF | `10` puerta 6 L225-226: a `08` (*Standard Object Names*) | Incoherencia interna de BP: elegir una |
| Seguridad de record actions | `06` §5.3 L163: reglas de seguridad | `record-types.md` L172-194: solo `visibilityExpr` | BP; anotar que por MCP la mecánica es la expresión |
| Grupo de seguridad del proceso | `03` §7 L368-372 | OF se contradice: `process-models.md` L300 (administradores) y `security.md` L66 (usuarios o rol) | Decir en BP cuál aplica |

### Interfaces

| Tema | BP | OF | Propuesta |
|---|---|---|---|
| Botón destructivo | `02` §4.9 L185-187: Ghost + Negative; un solo Solid | `sail.md` L233: Solid + Negative | BP |
| Guardar dentro de `a!forEach` | `02` §4.3 L144: en `fv!item` (KB-1398) | `sail.md` L391-395: `local!lista[fv!index]` | BP; marcar que corrige el ejemplo |
| Consulta en `data` | `02` §1.1 L19: no en `value`/`data` (y lo contrario en §2.1 L63) | `dropdown-patterns.md` L53: `data` preferido | Corregir la redacción de BP |
| Filas por página | `02` §5.6 L245: 5-10, 25 o 50 | `grid-field-instructions.md` L986: 10-25 | BP |
| Estilo del asistente | `02` §4.6 L162: vertical con más de 5 pasos | `wizard-layout-instructions.md` L199-200: con 4 o más | BP, revisando el caso de un paso |
| Etiqueta oculta | `02` §9.3 L435: `COLLAPSED` como opción libre | `accessibility-reference.md` L23: visible salvo equivalente | OF: acotar BP (la auditoría lo marcará) |
| Foco inicial | `02` §4.5 L155: considerar el foco automático | `component-checks.md` L151: no si hay información antes del primer campo | Añadir la condición |
| Enumeraciones de rich text | `02` §6.2 L309 (incluye `WARN`) | `component-reference.md` L296-297 (sin `WARN`) | Borrar enumeraciones; puntero |

## 3. Duplicados: sustituir por puntero

Se conserva lo que figura entre paréntesis.

- **`01`**: record events §11 L415-424, L427-428 ↔ `record-events.md` (conservar L410-413, L425-426, L429) · ambos
  lados de la relación §4.2 L186-187 · N:M §4.1 L178-179 · lookup y normalización §1 L40, §1.1 L48-50 · borrado lógico
  §4.3 L199 (alinear `deletedOn`/`deletedAt`) · acciones §9.2 L379-381 · tipos de campo §8 L292-301 (conservar tramos
  255/4.000/64.000, GMT, doble precisión).
- **`02`**: `showWhen` §4.4 L148-150 · cancelar en start form §4.9 L188 · `required` §4.1 L128-129 · rejilla de lectura
  o editable §5.1 L211-212 · record type como fuente §5.3 L226-227 · `rowHeader` §5.5 · elección de gráfico §5A.1-5A.2
  (conservar umbrales) · anchos de columna §3.2 L105-106 · tarjeta dentro de rejilla §7.5 L367.
- **`03`**: un solo Start Event §1 L29-32 · cancelar en start form §7 L389-397 (conservar el antipatrón) · lista de los
  seis roles §7 L372-377.
- **`04`**: regla o expresión en línea §1 L16-20 · una responsabilidad §1 L22-24 · naming de reglas y constantes §3
  L58-61 y §9 L219 · naming de inputs §2 L51-52 · `a!match` frente a `if` anidado §4 L94-97 · guardar la consulta en un
  local §7 L160-161 · tipos de aserción §8 L195-199 · qué casos crear §8 L201 · comentarios y constantes §3 L67-68, §9
  L214-217.
- **`06`**: reglas o expresión de seguridad §5.1 L118-128 · grupos por defecto §4 L84-86 (también `08` §2 L102-104).
- **`08`**: naming de proceso y sitio §1 L42-44, L54.
- **`09`**: el nombre visible no cambia la URL §6.2 L221-229.

## 4. Notas de delegación que siguen repitiendo

| Nota | Qué repite después |
|---|---|
| `04` §5 L113-117 (null-safety) | `a!defaultValue` L119, `a!isNullOrEmpty` L123, `applyWhen` L126 |
| `05` §2 L31-37 (consultas) | `fields` vacío L44, consulta en bucle L53, techos 100/250 L56 y tabla §8 L296, `fields`/`pagingInfo` L41, L50 |
| `02` §2 L55-58 (consultas) | §2.1 L61-62 |
| `02` §9 L411-418 (accesibilidad) | §9.1 iconos, §9.3, §9.4 L443, primera viñeta de §9.6; además la puerta 4 de `10` no cita la auditoría de OF |
| `10` puerta 4 paso 5 L168 | Las cinco comprobaciones de `change-review.md` |
| `01` §1 L29-35 (orden de creación) | La lista de tipos «manuales», ya caducada |

`03`, `06`, `07` y `09` no mencionan la skill oficial ni una vez: la remisión solo está en `SKILL.md`.

## 5. Sin solape (valor propio de BP)

`00`, `07`, `11`, `12`, `13` enteros · `10` salvo los pasos 1, 2 y 5 de la puerta 4 · `03` §2, §3, §5, §6, §9-§13 ·
`06` §5.2, §6-§11 · `09` §1-§5 · `05` §1, §4-§7 · `04` §10, §11 · `01` §0, §2, §3, §5-§7, §8.1, §8.bis.2-4, §10, §12 ·
`02` §1.2-1.5, §2.2-2.3, §3.1, §3.4, §4.2, §4.7, §4.8, §4.10, §4.11, §5.2, §5.4, §5A.3-5A.5, §6.4, §6.5, §7.1-7.4, §8,
§10, §11.

## 6. Cómo cerrarlo

1. **Una tabla de «divergencias conocidas con la skill oficial» en BP** (un solo sitio, citada desde `SKILL.md`): cada
   fila de §2 con quién gana y por qué. Hoy *Which Source Wins* cede a OF las recetas de consulta, el null-safety y el
   naming, y luego los docs de BP dicen otra cosa.
2. **Las puertas 1 y 4 aceptan como evidencia los artefactos de OF** (paso 4, 7B-7D, `change-review`) en vez de mandar
   repetir la comprobación. Con eso desaparecen las filas 1-5 de §1.
3. **Recortar lo de §3 y §4** a criterio + puntero con fichero y sección (OF se contradice entre ficheros; para datos,
   `data-modeling.md` es el más coherente).
4. **Corregir en BP** lo que no depende de OF: fila 9 de §1, `01` L310, `02` L19, `09` §7.1, naming en `SKILL.md` L222
   frente a `10` L225.
5. **Avisar a Appian** (issues en `dev-mcp-skills`) de lo que es error suyo: `and()`/`or()`, `fetchTotalCount`
   «REQUIRED», `a!forEach(null)`, `length()`, clave compuesta, record list «DEPRECATED», grupo de seguridad del proceso,
   lista de tipos «manuales», y dos referencias rotas (`references/node-types.md` en `SKILL.md` L239 y
   `rich-text-icon-aliases.md` en `sail.md` L530).
