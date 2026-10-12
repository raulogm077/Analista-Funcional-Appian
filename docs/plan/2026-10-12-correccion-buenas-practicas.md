# Plan: corregir `appian-best-practices` según la documentación de Appian

Fecha: 12 de octubre de 2026. Parte de `main` (`547a332`, 0.7.0-beta.3; buenas prácticas, igual que en `dc51944`).
Rama `correccion-buenas-practicas`. Lo que cambió al ejecutarlo está en §7.

**Objetivo.** Dejar `skills/appian-best-practices/` de acuerdo con docs.appian.com en las 37 reglas donde contradecía
a la skill oficial `appian`, y escribir en un solo sitio las divergencias en las que la oficial no sigue la
documentación.

**Enfoque.** La skill oficial no se toca (Appian la actualiza a menudo). Todo cambio es en este repositorio: correcciones
dentro de cada sección de `references/`, un documento nuevo de divergencias y dos comprobaciones a demanda.

**Base.** Verificación del 12-10-2026 contra `https://docs.appian.com/suite/help/latest/` (resuelve a **26.9**; cotejado
con 26.6) y `appian/dev-mcp-skills` @ `6e87fb6`. Abreviaturas: **BP** = buenas prácticas, **OF** = skill oficial,
`D/` = la URL base anterior. Análisis previo: `docs/diseno/2026-10-12-solapes-skill-oficial.md`.

## 1. Veredictos

Resultado: BP correcta en 19, OF correcta en 3, ambas con parte de razón en 11, convención sin respaldo documental en 3,
sin resolver 1. Aun donde BP acierta, 14 reglas necesitan precisar fuente, ancla o alcance.

### Expresiones, consultas y rendimiento

| Tema | Quién tiene razón | Fuente | Cambio en BP |
|---|---|---|---|
| `and()`/`or()` cortocircuitan | **BP** | `D/fnc_logical_and.html#evaluation-order-and-performance` | `05` L92: `match()` → `a!match()` |
| `fetchTotalCount` | **BP** (por defecto `false`; consulta adicional de recuento) | `D/fnc_system_queryrecordtype.html#using-the-fetchtotalcount-parameter` | `05` L68-69: citar esta página |
| Tamaño de lote | **Ambas**: OF en el límite (0-5000, −1 no válido en `a!queryRecordType`); BP en el criterio | `…#using-the-paginginfo-parameter`, `D/query-best-practices.html` | `05` L50, `04` L173: añadir el rango. `05` L63: enlace equivocado |
| `choose()` | **Ambas**: vigente y evalúa solo la opción elegida; Appian apunta a `a!match()` como alternativa | `D/fnc_logical_choose.html#evaluation-order` | `04` L99: añadir la alternativa |
| `a!forEach(null)` | **BP** (lista vacía, sin evaluar) | `D/fnc_looping_a_foreach.html#null-or-empty-items-list` | `04` L130, L202: ancla rota |
| `length()` en listas | **BP** | `D/fnc_array_length.html#length-of-list` | Ninguno |
| Cuándo crear test cases | **Ambas**: la doc exceptúa reglas que consultan datos transaccionales | `D/Expression_Rule_Testing.html#general-testing-guidance` | `04` L192, L207 |
| «Hoy» y zona horaria | **BP** | `D/fnc_date_and_time_local.html#use-local-to-get-the-current-context-for-date-time-functions` | `04` L248: citar docs además del KB |
| Recursión | **BP** (profundidad 20) | `D/understanding-the-health-check-report.html#recursive-rule-depth-limit` | Ninguno |
| Constantes de usuario | **Ambas**: la doc no prefiere; el riesgo es de KB-1854 | `D/Constants.html#when-to-use-a-constant` | `04` L227: redactar como riesgo |
| Historial del objeto | **Sin resolver** (la doc no lo trata) | `D/Managing_Object_Versions.html` | `04` L69-71, `10` L229-230: criterio propio |

### Modelo de datos

| Tema | Quién tiene razón | Fuente | Cambio en BP |
|---|---|---|---|
| Clave primaria | **Ambas**: compuesta válida con sync **desde 26.3**; la tabla generada lleva `id` entero único | `D/about-data-sync.html#field-requirements-for-optimized-data-access` | `01` L78, L126, L312 |
| PK autogenerada | **Ambas** (BP habla de CDT) | `D/Generating_Database_Tables_from_CDTs.html#primary-keys` | `01` L310: acotar |
| Campos de auditoría | **BP** (`createdOn`/`modifiedOn` son los que genera Appian) | `D/create-record-data-source.html#review-the-default-fields`, `D/records-data-sync.html#multiple-syncs-at-the-same-time` | `01` L143: precisar cuándo es obligatorio |
| Vigencia en datos de referencia | **Convención** (la doc ofrece `startDate`, `endDate` e `isActive` por igual); BP sale de Appian Max | `…#add-commonly-used-fields` | `01` L200: acotar |
| Nombre de las relaciones | **BP** | `D/build-best-data-fabric.html#relationship-names` | `01` L188: caso de varias relaciones al mismo tipo |
| 3FN frente a tablas de informe | **Ambas**: esquema normalizado; materializar es el último recurso | `D/appian-cloud-database-administration.html#follow-industry-and-appian-best-practices` | `01` L442, L461; `00` L35 |
| Record list | **BP** en que sigue vigente; preferirla a una rejilla es convención | `D/record-list.html#what-is-a-record-list`, `D/sites_object.html#page-types` | `09` L39, `00` L97: rebajar a preferencia |
| Adjuntos | **BP** | `D/about-doc-management.html#how-to-manage-documents` | `01` L329: remitir a L341 (tier) |
| Lookup compartido | **Convención**, sin contradicción real | `D/data-modeling-with-appian-records.html#store-lookup-data-in-a-separate-record-type` | `01` L49-52: fuente y ejemplo |

### Procesos, seguridad y sitios

| Tema | Quién tiene razón | Fuente | Cambio en BP |
|---|---|---|---|
| Escribir en línea o con proceso | **Ambas**: los dos son válidos; eventos solo con el nodo | `D/Write_Records_Smart_Service.html#awriterecords`, `D/manage-record-data.html` | `03` L418-421; fila nueva en `00` |
| Botón que arranca un proceso | **Ambas**: record action para crear o editar; `a!startProcess` para trabajo desatendido | `D/Ways_to_Start_a_Process_From_a_Process.html#starting-a-process-from-an-interface` | `00` L70 |
| Visibilidad de página | **OF**: la doc la presenta como capa de seguridad. El acceso por URL no consta | `D/object-security.html#visibility`, `D/sites_object.html#site-security` | `09` L270-276 |
| Role map del sitio | **Ambas**: no hereda, pero nace con los grupos por defecto de la aplicación | `D/object-security.html#setting-security-during-object-creation` | `09` L242-247; ancla de §7.2 |
| Seguridad de reglas e interfaces | **BP** (heredan de la carpeta) | `D/object-security.html#security-inheritance` | Ninguno |
| Un grupo por rol | **BP** | `D/User_Management.html#manage-user-rights-and-security` | `06` L24-25: la «cita literal» no lo es |
| Nombre de los grupos | **OF**: con prefijo, salvo los que ve el usuario final | `D/Standard_Object_Names.html#group-objects` | `08` L50-52 |
| Seguridad de record actions | **BP** | `D/record-action-security.html#security-expression` | `06` L163-165: fuente y equivalencia |
| Grupo de seguridad del proceso | **BP** | `D/process-model-object.html#process-model-security` | `03` L368-372: nace relleno |

### Interfaces

| Tema | Quién tiene razón | Fuente | Cambio en BP |
|---|---|---|---|
| Botón destructivo | **BP** (Ghost + Negative; un solo Solid) | `D/sail/ux-buttons.html#position` | Ninguno |
| Guardar dentro de `a!forEach` | **BP** | `D/fnc_looping_a_foreach.html#using-aforeach-with-interface-components` | `02` L144-146: fuente canónica |
| Consulta en `data` | **OF**: la doc exime a `data` en componentes de registros | `D/interface-performance.html#put-expensive-computations-in-local-variables-not-component-parameters` | `02` L19 |
| Filas por página | **BP** | `D/sail/ux-grids.html#batch-size` | Ninguno |
| Estilo del asistente | **BP** | `D/sail/ux-wizard-layout.html#selecting-a-wizard-style` | `02` L162: una condición más |
| Etiqueta oculta | **Ambas**: el lector la lee; el checklist de Appian Max pide etiqueta visible en campos de entrada | `D/sail/ux-accessibility.html#explicitly-describe-form-inputs` | `02` L435 |
| Foco inicial | **Convención**; BP además yerra: ya viene activo | `D/Form_Layout.html#parameters` | `02` L155 |
| Enumeraciones de rich text | **BP** (`WARN` desde 26.6) | `D/Styled_Icon_Component.html#parameters` | `02` L309: `ⓥ 26.6` |

## 2. Decisiones

- **D1. Solo se corrige BP.** Lo que la oficial tenga mal se anota como divergencia; no se edita ni se copia.
- **D2. No se renumera ni se mueve ninguna sección.** `skills/appian-refactorizacion/references/senales.md` y
  `pruebas/evaluaciones/` citan «BP nn §x.y». Cada cambio va dentro de su sección.
- **D3. Las líneas son de `dc51944`.** Se localiza por la frase, no por el número; dentro de cada fichero se edita de
  abajo arriba.
- **D4. Divergencias en un documento propio**, `references/14-official-skill-divergences.md`, enrutado desde `SKILL.md`
  en el párrafo que exige la skill oficial antes de escribir. No van a `SKILL.md` (se carga siempre) ni llevan números de
  línea de la oficial (caducan).
- **D5. Toda regla corregida lleva su URL `/latest/` con ancla.** Lo que salga de Appian Max o de un KB se dice («Appian
  Max», «KB-nnnn»), y lo que sea criterio propio se marca como tal, sin presentarlo como doctrina de plataforma.
- **D6. Lo que depende de versión lleva `ⓥ` y la versión** (clave compuesta 26.3, `WARN` 26.6).
- **D7. Queda fuera:** recortar duplicados y notas de delegación (§3 y §4 del análisis). Es otro plan.
- **D8. Versión 0.7.0-beta.4** (la 0.7.0 sigue pendiente de los pasos de Raúl).

## 3. Tareas

Cada tarea es un commit en español. Antes de cada uno: `python3 pruebas/comprobar_plugin.py --completo`, sin errores ni
avisos. El texto nuevo va en inglés, con los marcadores del doc (✅ ❌ ⚠️ ⓥ).

- [x] **T1. `02-interfaces-sail.md`**
  - L19 («Don't put it directly in a component parameter»): quitar `data` del paréntesis; añadir que `data` con record
    type o `a!recordData()` no necesita variable local, salvo en interfaces offline (§11.1).
  - L144-146: añadir la página de `a!forEach()` como fuente principal; KB-1398 queda de apoyo.
  - L155: el foco automático viene activo por defecto; la decisión es cuándo desactivarlo (información antes del primer
    campo), marcada como criterio de accesibilidad sin respaldo en la doc. «Fix title bar/buttons»: ya es el
    comportamiento por defecto en diálogos de record action.
  - L162: añadir «o cuando las etiquetas no caben en horizontal».
  - L309: «in recent releases» → `ⓥ 26.6`; ancla `#parameters`.
  - L435: `COLLAPSED` lo lee el lector de pantalla, pero en campos de entrada la etiqueta visible es lo que pide el
    checklist de Appian Max (WCAG 3.3.2); usarlo solo con equivalente visible (encabezado, cabecera de columna).
- [x] **T2. `01-data-model-records.md`**
  - L49-52: fuente → `data-modeling-with-appian-records.html#store-lookup-data-in-a-separate-record-type`; el lookup se
    crea aunque lo use una sola entidad; actualizar el ejemplo.
  - L63-64: confirmar en la página y, si procede, anotar `ⓥ 26.9` (acceso directo con funciones también en Oracle).
  - L78, L126, L312: clave compuesta `ⓥ 26.3`; la tabla generada desde el record type lleva `id` entero único y con
    clave compuesta no se puede modificar la tabla desde Appian.
  - L143: `modifiedOn` es obligatorio y no nulo solo cuando es el campo *Last Modified* de un sync incremental;
    recomendación en el resto. Añadir las dos anclas.
  - L182: ancla → `#relationship-requirements`.
  - L188: añadir «varias relaciones al mismo record type → nombre por rol».
  - L200: acotar a datos cuya vigencia histórica importa; en un lookup estático vale `isActive`. Fuente: Appian Max.
  - L310: acotar a «CDT con data store»; no afecta al `id` autogenerado de las tablas creadas desde el record type.
  - L329: remitir a L341 (sin el tier, la carpeta es la única vía).
  - L442, L461: tablas de informe como último recurso (antes: sync, índices, rehacer la vista) y excepción expresa a
    la 3FN.
- [x] **T3. `04-expression-rules.md` y `10-quality-gates.md`**
  - `04` L69-71 y `10` L229-230: marcar como criterio propio, citar `Managing_Object_Versions.html` como motivo y decir
    que alcanza a la descripción del objeto.
  - `04` L99: añadir que Appian presenta `a!match()` como alternativa más flexible a `choose()`.
  - `04` L130, L202: ancla → `#null-or-empty-items-list`.
  - `04` L173: en `a!queryRecordType` el `batchSize` va de 0 a 5000 y −1 no es válido (solo en `a!queryEntity`).
  - `04` L192: «toda regla con lógica propia»; excepción documentada: reglas que consultan datos transaccionales.
  - `04` L207: el caso NULL «siempre» es de Appian Max.
  - `04` L227: riesgo conocido (KB-1854) y recomendación propia, no doctrina oficial.
  - `04` L248: añadir las páginas de `local()` y `todate()` como fuente principal.
- [x] **T4. `05-performance.md`**
  - L50: mismo rango de `batchSize` que en T3.
  - L63: enlace → `Paging_Grid_Component.html#row-limit-for-records-powered-components`.
  - L68-69: fuente → página de la función; «consulta adicional de recuento; por defecto `false`».
  - L92: `match()` → `a!match()`.
- [x] **T5. `03-processes.md` y `00-solution-decisions.md`**
  - `03` L418-421: quitar «Platform doctrine» (la fuente es una página de RPA). Regla nueva: `a!writeRecords()` es
    válido en un `saveInto` o una Web API; proceso cuando hay record events, notificación, integración, varios registros
    o aprobación. Puntero a la skill oficial para la mecánica.
  - `03` L368-372: el role map nace con los grupos por defecto de la aplicación: «set» es revisar. El grupo iniciador
    es el de quien inicia, no el de administradores.
  - `00` «Process»: fila nueva con ese criterio de escritura en línea o con proceso.
  - `00` L35: tablas de informe como último recurso.
  - `00` L70: limitar el «Avoid» a crear o editar registros con formulario; `a!startProcess` es lo documentado para
    actividades desatendidas.
  - `00` L97: de «Avoid» a preferencia (la doc da por válida la rejilla de registros en una interfaz).
- [x] **T6. `06-security.md` y `08-alm-testing-naming.md`**
  - `06` L24-25: poner el texto real de `User_Management.html` o quitar «literal».
  - `06` L163-165: fuente → `record-action-security.html#security-expression`; `visibilityExpr` del MCP es la Security
    Expression.
  - `08` L50-52: quitar «business groups»; los grupos llevan prefijo salvo los que ve directamente el usuario final
    (p. ej. audiencia de Tempo). Coherente con la tabla de L44.
- [x] **T7. `09-sites-navigation.md`**
  - L39: de ❌ a preferencia.
  - L242-247: «no hereda; nace con los grupos por defecto de la aplicación si existen, y si no, solo con el creador:
    revísalo». Reescribir el «Why» y añadir las dos fuentes.
  - §7.2: ancla `#security` → `#site-security`.
  - L270-276: quitar «This is not security» y lo del acceso por URL. Texto nuevo: la visibilidad es una capa más y no
    sustituye los permisos sobre los objetos que la página usa (`object-security.html#layered-object-security`).
- [x] **T8. `SKILL.md` y `01` §1: lo que BP dice mal de la skill oficial**
  - `SKILL.md` L129-131 y L152-154: la oficial comprueba funciones con `functions.json` y `curl`; la búsqueda de
    documentación es su nivel 3, opcional. Quitar la parada obligatoria o declararla exigencia propia.
  - `SKILL.md` L222 y `10` L225-226: una sola regla de naming: convención del proyecto → *Standard Object Names* (`08`)
    → skill oficial para lo que `08` no cubre (tablas, campos, relaciones).
  - `SKILL.md` L222: quitar «query recipes» y «null handling» de lo que gana la oficial; remitir al doc 14.
  - `01` L29-35: dejar el puntero a `change-planning.md` sin enumerar los tipos «manuales» ni «twelve steps».
- [x] **T9. `references/14-official-skill-divergences.md` (nuevo) y su enrutado**
  - Cabecera: comprobado contra `dev-mcp-skills` `6e87fb6` y docs 26.9; la documentación gana a ambas skills.
  - Una fila por divergencia: tema · qué dice la oficial · qué dice la doc (URL) · qué hacer. Filas: `and()`/`or()`,
    `fetchTotalCount`, lote de 5000 y filtrar en memoria, `a!forEach(null)`, `length()`, `todate(now())`, recursión,
    clave compuesta, nombres de auditoría, record list «deprecated», carpeta de adjuntos, origen de la seguridad de
    reglas, record actions solo con expresión, grupo de seguridad del proceso, botón destructivo Solid, guardar en
    `local!lista[fv!index]`, filas por página, umbral del asistente, enumeraciones de rich text.
  - Segunda tabla, «la oficial acierta y BP se corrigió»: `data`, prefijo de grupos, visibilidad de página.
  - `SKILL.md`: fila en *Routing by Domain* y mención en el párrafo «Before writing through a design MCP».
- [x] **T10. `skills/appian-refactorizacion/references/senales.md`**
  - L57: excluir `data` con record type o `a!recordData()` (por T1).
  - L48: comprobar que sigue siendo coherente con `00` L70 (actuar sobre un registro → record action).
- [x] **T11. `pruebas/comprobar_anclas.py` (nuevo, a demanda; no entra en `--completo` porque necesita red)**
  - `python3 pruebas/comprobar_anclas.py [--skill appian-best-practices]`: saca de `references/*.md` cada URL de
    docs.appian.com con ancla, descarga cada página una vez y comprueba que existe un elemento con ese `id`.
  - Salida: `fichero:línea URL` por ancla rota; código 1 si hay alguna.
  - Ejecutarlo, corregir lo que encuentre (la verificación solo miró 37 reglas y halló 3 anclas rotas y 1 enlace
    equivocado) y repetir hasta código 0.
- [x] **T12. `pruebas/comprobar_divergencias.py` y `pruebas/divergencias-oficial.json` (nuevos, a demanda)**
  - El JSON lleva, por fila del doc 14, el fichero de la oficial y una expresión regular que aparece mientras la
    divergencia siga viva (p. ej. `short-circuit-patterns.md` · `DO NOT short-circuit`; `data-modeling.md` ·
    `Never use composite primary keys`; `record-summary-views.md` · `DEPRECATED`).
  - `python3 pruebas/comprobar_divergencias.py --oficial <carpeta de la skill>`: lista las divergencias que Appian ya
    ha corregido (marcador ausente), para quitarlas del doc 14. Código 0 siempre; es un aviso.
  - Probarlo contra `~/.claude/skills/appian/`: todas las filas deben salir vivas.
- [x] **T13. Cierre**
  - `comprobar_plugin.py --completo` en el repositorio y en el paquete (`--plugin`).
  - Versión 0.7.0-beta.4 en `.claude-plugin/plugin.json` y en la primera fila del README.
  - `docs/siguiente-version.md`: apuntar D7 (recorte de duplicados) y los pasos de Raúl.

## 4. Pasos de Raúl

Ninguno. Los dos que se preveían quedaron resueltos sin él:

- **Acceso por URL a una página oculta de un sitio.** La documentación dice que ver una página exige Viewer en el sitio
  y visibilidad de la página, y no dice qué pasa con una URL directa; en la comunidad tampoco consta. La regla de `09`
  §7.3 no depende de esa prueba: se diseña como si la página se pudiera alcanzar y se protegen los objetos que usa.
- **Mantenimiento al actualizar la skill oficial y antes de publicar.** Es una regla del repositorio (`CLAUDE.md`):
  `comprobar_divergencias.py` cuando cambie la skill oficial y `comprobar_anclas.py` antes de publicar una versión.

## 5. Riesgos a revisar

- Que un cambio mueva una sección y rompa las citas «BP nn §x.y» de `senales.md` y de las evaluaciones (D2).
- Que una corrección contradiga otra frase del mismo doc que no estaba en la tabla: tras cada tarea, buscar el término
  en todo `references/` (p. ej. `COLLAPSED`, `batchSize`, `record list`, `prefix`).
- Que el doc 14 se quede viejo cuando Appian corrija su skill (T12).
- Anclas tomadas de la verificación sin comprobar una a una: las valida T11.
- Reglas que dependen de versión aplicadas a un entorno anterior a 26.3 o 26.6 (D6).

## 6. Criterios

- `comprobar_plugin.py --completo` sin errores ni avisos, en el repositorio y en el paquete.
- `comprobar_anclas.py` con código 0.
- `comprobar_divergencias.py` contra la oficial instalada: todas las filas del doc 14 vivas.
- Cada fila de §1 con cambio tiene su edición hecha y su fuente; ninguna sección renumerada (`git diff --stat` solo
  toca los ficheros de las tareas).
- La evaluación de malas prácticas y la de enrutado, sin empeorar respecto a la 0.7.0-beta.3.

## 7. Resoluciones durante la ejecución

Lo que se decidió sobre la marcha y se aparta del plan. Cada cambio se contrastó antes con la página descargada de la
documentación (26.9).

- **R1. La clave compuesta consta desde la 26.3, no la 26.1.** Las URL `/help/26.1/` y `/help/26.2/` redirigen a la
  versión vigente; lo comprobado es que no está en la 25.4 y sí en la 26.3.
- **R2. Oracle en el acceso directo, `ⓥ 26.8`** (notas de versión). `01` §2.
- **R3. `04` L207, sin cambio:** la regla ya decía «(Appian Max)».
- **R4. `SKILL.md`: se quita la parada por no tener MCP de documentación.** Queda «no escribir sobre una función o un
  parámetro que no se pudo confirmar». La skill oficial comprueba la existencia de funciones contra `functions.json`.
- **R5. Naming:** convención del proyecto → `08` y `01` §4.2 → skill oficial para tablas y campos.
- **R6. El doc 14 lleva 18 filas.** En la segunda fase se contrastaron y añadieron tres (umbral del asistente,
  colores de rich text, recursión); la carpeta de adjuntos se descartó (la oficial solo la pone de ejemplo). Fuera el
  grupo de seguridad del proceso, que la skill del
  bundle DevMCP del 8-10-2026 ya corrige. Sin la segunda tabla («la oficial acierta y BP se corrigió»): es historial, y
  el propio `04` §3 lo deja fuera de los objetos.
- **R7. La skill oficial instalada (bundle DevMCP, build 2026-10-08) es más nueva que GitHub `6e87fb6`.** El doc 14 está
  comprobado contra la instalada: 18 de 18 divergencias vivas.
- **R8. `comprobar_anclas.py` encontró 18 anclas rotas más**, en secciones que la verificación no miró (`01`, `02`,
  `03`, `06`, `09`, `10`, `12`): 16 pasan al nombre actual de su sección y 2 citan la página, sin ancla. Tras
  corregirlas: 1.188 citas, 0 rotas.
- **R9. `comprobar_divergencias.py` no dice «corregida»:** un marcador que falta solo prueba que cambió el texto, así
  que avisa y manda leerlo; si el texto está en otro fichero, lo dice. Usa rutas largas en Windows (sin ellas, un
  fichero que existe en una carpeta profunda daba «no existe»). Comprueba también que existen los 21 ficheros de la
  skill oficial a los que remite buenas prácticas.
- **R10. Dos commits, no trece:** la comprobación completa tarda unos 20 minutos en este equipo.
- **R11. No se repiten las evaluaciones a ciegas** (malas prácticas, enrutado): la descripción de la skill no cambia
  (el enrutado depende de ella) ni la numeración de las secciones que citan las claves; sus `prueba_puntuar.py` pasan en
  `--completo`.

## 8. Segunda fase: sin pendientes (objetivo de Raúl del 12 de octubre)

«Dejar la skill de buenas prácticas bien hecha, sin nada por hacer y con coherencia en lo que dice.» Se cierra aquí lo
que la primera fase dejaba para la siguiente versión. Estado: `[ ]` pendiente, `[x]` hecho.

**Criterio para lo duplicado (R12).** Buenas prácticas tiene que valer sin la skill oficial (revisar código pegado,
trabajar en Designer) y es la que lleva la fuente de cada regla; la oficial falla en 18 puntos comprobados y cambia a
menudo. Por eso la doctrina repetida **se queda** en buenas prácticas con su fuente, y solo se sustituye por un puntero
lo que es mecánica copiada de la oficial. Lo que se elimina son los comportamientos que se hacían dos veces.

- [x] **F2-1. Comportamientos repetidos o enfrentados** (§1 del análisis), en `SKILL.md` y `10`: las puertas 1 y 4 no
  repiten lo que la skill oficial ya comprobó al escribir; una sola regla de cuántas veces renderizar; fuera las cinco
  comprobaciones copiadas de `change-review`; calibración, descubrimiento y dependientes dichos una vez.
- [x] **F2-2. Doc 14:** convenciones nuevas en §2 (reintentos, compleción obligatoria frente al alcance, carga de
  referencias, listar antes de crear) y las cuatro filas que faltaban por contrastar (umbral del asistente,
  enumeraciones de rich text, recursión, carpeta de adjuntos): se añaden o se descartan con motivo.
- [x] **F2-3. Hallazgos de la revisión independiente:** todos, también los menores que afecten a la coherencia.
- [x] **F2-4. Una sola voz sobre «ocultar no es autorizar»** (`SKILL.md`, `06`, `09` §7.3, `10` puerta 3, `11` §6).
- [x] **F2-5. `comprobar_divergencias.py`:** que compruebe también que existen los ficheros de la skill oficial a los
  que remite buenas prácticas.
- [x] **F2-6. Cierre:** `docs/siguiente-version.md` sin pendientes de buenas prácticas que se puedan hacer aquí; nota de
  cierre en el análisis; fila del README.
- [x] **F2-7. Comprobaciones finales** (`comprobar_anclas.py`, `comprobar_divergencias.py`, `comprobar_plugin.py
  --completo`) y commits.
- [x] **F2-8. Avisar a la sesión «Evolucionar plugin analista funcional»** cuando estén los commits. Sus cambios
  aprobados (tres avisos en «Tools», quitar el registro de veredictos de las puertas) los hace ella después: lo de
  F2-1 se escribe sin añadir registro de evidencias, para que encaje.

### Revisión independiente (R13)

Un agente que no había visto el trabajo revisó el diff contra la documentación (26.9) y la skill oficial instalada. Sin
hallazgos críticos; tres importantes y siete menores, todos corregidos:

- La fila «lote de 5000» del doc 14 atribuía a la oficial algo que no dice (sustituye `-1` por 5000, que es el máximo
  válido). La divergencia real es «Query once, transform many»: una consulta sin filtrar partida en memoria.
- `comprobar_divergencias.py` daba por corregido lo que solo había cambiado de redacción (R9).
- «Editar un registro con formulario» tenía dos respuestas (`00`, `03` §8): con formulario es una record action;
  `a!writeRecords()` en línea queda para la edición en el sitio fuera de una record action.
- Menores: Oracle desde la 26.8 (R2); dos citas más del límite de 5.000 filas a la página equivocada; la excepción de
  `data` y la invalidez de `batchSize: -1` dichas también en `05` y `04`; «test cases saved» de la puerta por tipo de
  objeto remite a `04` §8; `comprobar_anclas.py` no se cae con una URL que no se puede pedir.

