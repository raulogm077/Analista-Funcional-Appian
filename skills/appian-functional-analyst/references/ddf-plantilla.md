# Plantilla del DDF (17 secciones)

El `ddf.md` sigue esta estructura y numeración; el `.docx` se genera a partir
de él. Si la información es insuficiente para una sección, indícalo con ❓:
nunca omitas una sección (en modo fiel, ver la tabla siguiente).

**Formato que leen los scripts** (`comprobar_ddf.py`, `ddf_indice.py`, `ddf_docx.js`, el prototipo):
- Títulos de sección: `## N. Título` (`## 8. Requisitos funcionales`). En esta plantilla, «Sección N — …» es
  solo el título de la explicación, no el que se escribe en el `ddf.md`.
- Fichas (RF, ACT, PAN, CU, INT, NOT): una línea en negrita `**RF-001 — Nombre**` seguida de su tabla
  `| Campo | Contenido |`.
- Filas (RB, S, P, D y los resúmenes de ACT, INT, NOT): el ID en la primera celda, `| RB-001 | … |`.
- Criterios: `` `CA-PAN-03.1` **Dado** …, **cuando** …, **entonces** … ``.

**Documentos grandes** (más de 5 procesos principales, o un DDF previsible de
60+ páginas): propón dividirlo por módulo funcional antes de escribir.

## Modo fiel: qué se rellena

Cuando la fuente principal es un diseño funcional o ERS existente, el `ddf.md`
es un extracto estructurado, no un documento nuevo. No se genera `.docx`.

| Sección | Modo fiel |
|---|---|
| 1 | Fuentes y control de versiones |
| 2, 3, 4 | Solo lo que el documento base dice (alcance y exclusiones sí) |
| 5 Actores | Sí |
| 6 Procesos | Actividades con su ID literal, estados de entrada y salida y si ocurren en la aplicación; fichas de las tareas de usuario; sin diagrama |
| 7 Casos de uso | «Ver documento base» salvo que los defina |
| 8 Requisitos | Los del documento, con su ID literal; en ficha o en una tabla `ID · Requisito · Se verifica en · Fuente` |
| 9 Reglas | Sí, con cita |
| 10 Datos | Sí (entidades, campos, tipos, obligatoriedad, listas de valores) |
| 11 Estados | Sí |
| **12 Pantallas** | **Sí, completa y literal: es lo que más usa el prototipo** |
| 13, 14 | Resumen (qué integraciones y avisos hay) |
| 15 | KPIs e informes que describa |
| 16 | Matriz de cobertura con los criterios que existan |
| 17 | Preguntas, incoherencias internas del documento y dudas |

**Criterios de aceptación en modo fiel**: se copian los que traiga el documento base. Si una pantalla o tarea no
tiene, su ficha lo dice («❓ El documento base no define criterios de aceptación»). Solo se proponen
criterios nuevos si el usuario lo pide (por ejemplo, para preparar pruebas), y van marcados ⚠️.

## IDs estables

- Prefijos: `RF-001`, `RB-001`, `CU-001`, `ACT-01` (actividades del proceso),
  `S-001` (supuestos), `INT-001`, `NOT-001`, `PAN-01` (pantallas), `P-001`
  (preguntas), `D-001` (decisiones, Sec 17), `R-001` (riesgos, Sec 17). Criterios de aceptación: `CA-PAN-03.1` (pantalla), `CA-ACT-02.1`
  (tarea), `CA-RF-012.1` (requisito sin pantalla ni tarea), `CA-E2E-01`
  (escenario de extremo a extremo). Las fuentes son `FU-01`… y las asigna `leer_fuentes.py`. En modo fiel se usan
  los IDs del documento base tal cual.
- Un ID **nunca se renumera ni se reutiliza**. Si algo deja de valer, se
  tacha el ID y se queda con la decisión que lo anuló: en una ficha,
  `**~~RF-007~~ — Título** Anulado por D-012 [FU-26 00:12:30]`; en una tabla,
  `| ~~RB-031~~ | … | Anulado por D-012 |`; un criterio,
  `` - ~~`CA-PAN-07.3`~~ Anulado por D-012: ~~**Dado** …~~ ``; una pregunta contestada,
  `| ~~P-003~~ | … | Respondida por D-015 |`. Lo nuevo toma el siguiente número
  libre (`ddf_indice.py siguientes`).
- **Estado de cada pieza**: el campo o la columna «Certeza» (o la marca tras el
  título de la ficha) con 🔒 Validado, ✅ Decidido, 🔶 Inferido, ⚠️ Pendiente o
  ❓ No definido (escala del SKILL.md). «Lo confirmado» es un filtro sobre esta
  marca, no otro documento.
- Cada fila de requisitos, reglas, datos y pantallas cita su fuente (ver
  `ingesta-fuentes.md` §2).

## Pantallas y flujo, cada uno con sus criterios

El DDF sirve para prototipar y para derivar pruebas. Para que las pruebas de
una pantalla no se mezclen con las del flujo:

- **Sec 12 (pantallas)**: cada ficha es autocontenida: campos, filtros,
  ordenación, acciones, reglas de la pantalla, textos literales y sus
  **criterios de aceptación** (funcionales y de presentación).
- **Sec 6 (flujo)**: cada tarea de usuario tiene su ficha: actor, pantalla,
  estado de entrada, opciones con su estado de salida y siguiente tarea, y su
  **criterio mínimo de aceptación**.
- **Un criterio vive en un solo sitio.** La Sec 8 no repite criterios: cada RF
  dice dónde se verifica (`CA-PAN-…`, `CA-ACT-…`). Solo los RF que no dependen
  de una pantalla ni de una tarea (avisos, informes, integraciones, procesos
  automáticos) llevan su propio criterio (`CA-RF-…`). La Sec 16 es la matriz
  que comprueba que todo RF MUST está cubierto.
- Las reglas de negocio generales viven en la Sec 9 (RB-xxx); las fichas las
  citan por ID en vez de repetirlas.

## Cómo se redacta un requisito, una regla o un criterio

- Frase completa y verificable: si no se puede probar, no está bien escrita.
- «debe» / «será» para lo obligatorio; «podrá» para lo opcional.
- Sin términos vagos («amigable», «flexible», «adecuadamente», «rápido» sin cifra).
- Sin escapes en lo obligatorio («salvo que», «a no ser que»): cada excepción
  es un caso explícito.
- Cada acción del usuario dice **qué pasa después** (qué se muestra, qué estado
  cambia, a dónde navega).
- Lógica con varios escenarios, enumerada: «Caso A: condición → efecto».
- Textos literales entre comillas («Aprobar», «¿Desea eliminar el documento?»).
- Qué se quiere, no cómo se implementa (nada de nombres de tablas, reglas SAIL
  ni objetos Appian en los requisitos; eso va en notas para desarrollo).

---

### Sección 1 — Portada y control documental

- Nombre del proyecto y subtítulo del módulo
- Cliente / organización
- Versión: v1.0 — Borrador para validación
- Fecha de generación
- Modo: síntesis, fiel o mixto
- Tabla de **fuentes** (la de `fuentes/indice.md`: ID, fichero, tipo, fecha) y,
  si el usuario lo quiere, asistentes de cada reunión por rol
- Tabla de control de versiones: `Versión | Fecha | Cambio | Fuentes | IDs afectados`
  (iniciar con v1.0)

---

### Sección 2 — Resumen ejecutivo y contexto de negocio

**Resumen ejecutivo** (5-8 líneas, lenguaje de negocio, sin jerga técnica):
Qué problema existe hoy, qué se propone construir, cuál es el valor esperado,
qué puntos críticos requieren validación.

**Objetivo del documento**: Para qué sirve y a quién va dirigido.

**Contexto de negocio**: Entorno del cliente, área afectada y por qué surge
esta iniciativa.

**AS-IS / TO-BE**:
- *AS-IS*: Cómo se hace actualmente. Qué falla, qué genera ineficiencia.
  Solo lo que las transcripciones mencionen.
- *TO-BE*: Qué mejora. Qué capacidades nuevas tendrá la organización.

---

### Sección 3 — Alcance y exclusiones

**Dentro del alcance**: Lista específica de qué incluye esta fase.
Ser concreto: no "gestión de documentos" sino "carga de documentos en SharePoint
al crear un informe y control de versiones de entregas de la aTRP".

**Fuera del alcance**: Qué NO incluye esta fase, con justificación breve.
Incluir funcionalidades mencionadas por el cliente pero descartadas.

---

### Sección 4 — Supuestos y restricciones

**Supuestos**: Premisas que el analista asume como ciertas para elaborar el diseño.
Siempre hay supuestos — si el cliente no los verbalizó, los genera el analista marcándolos ⚠️.
Ejemplos habituales: "El sistema de RRHH tiene API disponible", "Los usuarios tienen conexión estable en campo", "El cliente dispone de licencias Appian suficientes".

| ID | Descripción | Base (transcripción / inferencia / estándar) | Impacto si es incorrecto | Estado |
|----|-------------|----------------------------------------------|--------------------------|--------|
| S-001 | [descripción del supuesto] | [FU-02 00:31:10, Jefe de servicio / inferido de FU-02, FU-05] | [qué cambia si es falso] | ⚠️ Pendiente |

*Estado*: ⚠️ Pendiente de validación / ✅ Decidido / 🔒 Validado por el cliente

**Restricciones**: Condiciones técnicas, organizativas o contractuales que
limitan el diseño. Incluir restricciones de plataforma Appian si son relevantes.
Si no hay restricciones conocidas, indicarlo explícitamente — no dejar vacío.

---

### Sección 5 — Actores, roles y permisos

Para cada actor, una tabla que combina descripción funcional y permisos:

| Rol | Descripción | Participa en | Crea | Consulta | Edita | Aprueba / Ejecuta | Nivel de acceso |
|-----|-------------|--------------|------|----------|-------|-------------------|-----------------|
| Aprobador | Responsable de la unidad | ACT-02; PAN-01, PAN-05 | — | Expedientes | — | Resuelve la aprobación | Grupo «Responsables de unidad» |

«Participa en» lista las actividades (Sec 6) y pantallas (Sec 12) de cada rol:
con ella queda claro qué hace cada actor dentro del proceso antes de leer el
detalle.

Tras la tabla, un párrafo por actor con particularidades relevantes de las
transcripciones.

**Matriz de permisos por entidad** (incluir si hay múltiples entidades con
seguridad diferenciada):
| Entidad | Rol A | Rol B | Rol C |
|---------|-------|-------|-------|

Si el cliente no detalló la seguridad, marcarlo como ❓ y listar las preguntas
de validación necesarias.

---

### Sección 6 — Flujo BPM end-to-end

Esta es la sección central del documento.

#### 6.1 Diagrama del proceso (BPMN en draw.io)

**Genera el diagrama primero, antes de escribir la descripción textual.** Lo dibuja la skill
`appian-diagramas-bpmn` (lee su `SKILL.md`): describe el proceso en su formato JSON, con un carril por
rol y los mismos `ACT-nn` que la tabla de actividades, y ejecuta `diagrama.py crear … -o diagramas/`.
Quedan `diagramas/<proceso>.drawio` (editable en draw.io, también durante una reunión con el cliente),
`.png` y `.json`.

En el `ddf.md`, bajo 6.1, solo la imagen con su pie y la nota:

```
![Flujo — <proceso>](diagramas/<proceso>.png)

Diagrama vX.Y — Pendiente de validación con el cliente
```

Con más de 20 tareas, divide en subprocesos: un diagrama por subproceso.

Si alguien ha editado el `.drawio` a mano (por ejemplo, en una reunión), antes de tocar la Sec 6 ejecuta
`diagrama.py comparar diagramas/<proceso>.drawio`: lleva cada cambio a la tabla de actividades y a las fichas
y después acéptalos con `--aceptar`.

Sin navegador para generar el PNG, el `.drawio` se entrega igual (se abre en draw.io) y queda un punto 🟡 en la
Sec 17. Nunca uses webs públicas para verlo.

#### 6.2 Descripción del flujo por proceso / subproceso

Para cada proceso o subproceso, una ficha estructurada:

| Campo | Contenido |
|-------|-----------|
| **Nombre** | Nombre del proceso |
| **Objetivo** | Qué logra cuando se completa correctamente |
| **Trigger** | Evento o acción que lo desencadena |
| **Actores** | Roles que participan |
| **Happy Path** | Resultado cuando todo va bien |
| **RBs asociadas** | IDs de reglas de negocio: RB-001, RB-002... |
| **RFs asociados** | IDs de requisitos funcionales del proceso: RF-001, RF-002... |
| **Estados impactados** | Qué estados de qué entidades cambia este proceso |

**Actividades** (una fila por actividad del flujo; en modo fiel, con el ID del documento):

| ID | Actividad | Actor | Tipo (usuario / sistema / externo) | Estado de entrada → salida | En la aplicación | Fuente |
|----|-----------|-------|------------------------------------|----------------------------|------------------|--------|
| ACT-01 | Registrar expediente | Técnico | Usuario | — → «Borrador» | Sí | [FU-10 «Registrar expediente»] |
| ACT-05 | Emitir informe de ENAIRE | ENAIRE | Externo | «Consulta enviada» → «Informe recibido» | No: la realiza un organismo externo | [FU-01 diap. 12] |

La columna «En la aplicación» decide qué se prototipa: lo marcado «No» llega
al prototipo como fuera de alcance, con su motivo.

**Descripción paso a paso (Happy Path):**
Pasos numerados. Cada paso: acción + quién la hace + qué genera como resultado.

**Excepciones y caminos alternativos:**
Para cada excepción: qué la desencadena → quién actúa → qué ocurre → cómo se
resuelve (retorno al flujo / flujo alternativo / cierre). Incluir rechazos,
subsanaciones, cancelaciones, errores de integración, timeouts, duplicidades.

#### 6.3 Fichas de tarea

Una ficha por cada **tarea de usuario** (y por cada tarea de sistema con más de
una salida). Todo lo que haya que explicar de un punto del flujo va aquí, no
dentro del diagrama.

**ACT-02 — Resolver la aprobación**

| Campo | Detalle |
|-------|---------|
| **Actor** | Aprobador (grupo o rol) |
| **Pantalla** | PAN-05 |
| **Disparador** | Qué crea la tarea (ACT anterior, fecha, evento) |
| **Estado de entrada** | «Pendiente de aprobación» |
| **Plazo / escalado** | Si lo hay (NOT-xxx), o «—» |
| **Fuente** | [FU-01 diap. 30] |

**Opciones** (una fila por decisión o botón; todas las salidas posibles):

| Opción | Condición para poder elegirla | Estado de salida | Siguiente | Aviso |
|--------|-------------------------------|------------------|-----------|-------|
| «Aprobar» | — | «Aprobado» | ACT-03 | NOT-002 al gestor |
| «Devolver» | Comentario obligatorio | «Borrador» | ACT-01 | NOT-003 al gestor |
| «Rechazar» | Comentario obligatorio | «Rechazado» | Fin | NOT-004 al gestor |

**Criterio mínimo de aceptación** (qué debe cumplirse para dar la tarea por
validada; uno por opción como mínimo):
- `CA-ACT-02.1` **Dado** un expediente en «Pendiente de aprobación», **cuando** el
  aprobador pulsa «Aprobar», **entonces** el expediente pasa a «Aprobado», la tarea
  desaparece de su bandeja y se crea ACT-03.
- `CA-ACT-02.2` **Dado** …, **cuando** pulsa «Devolver» sin comentario, **entonces**
  no se envía la decisión y se muestra «…».

Los estados de entrada y salida deben coincidir con las transiciones de la
Sec 11: una transición que aparezca aquí y no allí (o al revés) es un error.

---

### Sección 7 — Casos de uso funcionales

#### 7.1 Diagrama de casos de uso (Mermaid, opcional)

Si hay **3 o más actores** y/o **6 o más casos de uso**, genera un diagrama
visual actor↔CU usando `flowchart LR` adaptado (Mermaid no tiene tipo nativo
de Use Case Diagram). Si solo hay 1-2 actores y 2-3 CUs, la tabla siguiente
basta — no fuerces el diagrama.

Sigue el workflow validar → renderizar → incrustar de `mermaid-diagrams.md`.
Las convenciones de actores (círculo), CUs (elipse) y conexiones están en
`mermaid-diagrams.md` (sección "Diagrama de casos de uso"). Guarda
el diagrama como `diagramas/cu.mmd` y, después de la imagen, añade pie de figura.

El diagrama no reemplaza las fichas detalladas de CU — las complementa.

#### 7.2 Tabla resumen y fichas detalladas

Tabla resumen de todos los casos de uso identificados:

| ID | Nombre | Actor principal | Proceso asociado | Prioridad |
|----|--------|-----------------|------------------|-----------|

Para los casos de uso críticos o complejos, ficha detallada:

| Campo | Contenido |
|-------|-----------|
| **ID** | CU-XXX |
| **Actor principal** | (y actores secundarios) |
| **Precondición** | Qué debe ser cierto antes de que empiece |
| **Flujo principal** | Pasos numerados |
| **Flujos alternativos** | Variantes del flujo principal |
| **Postcondición** | Qué es cierto cuando termina correctamente |
| **Excepciones** | Qué puede ir mal y cómo se gestiona |

---

### Sección 8 — Requisitos funcionales

Cada requisito debe ser **trazable y verificable por QA sin ambigüedad**.
Agrupa por proceso o módulo funcional. Incluye al menos un RF por cada paso
relevante del Happy Path del BPM.

**Formato obligatorio: ficha vertical por cada RF** (no tabla horizontal resumida).
«Se verifica en» es el campo más importante: sin criterio de aceptación, QA no
puede verificar el requisito ni desarrollo puede considerarlo cerrado. El
criterio se escribe donde se prueba (ficha de pantalla o de tarea) y aquí solo
se referencia; solo lleva criterio propio el RF que no depende de ninguna
pantalla ni tarea. No abreviar, no poner "(extracto)" ni omitir RFs: si el
proceso tiene 10 pasos en el Happy Path, el documento tiene al menos 10 RFs.

---

**RF-XXX — [Nombre del requisito]**

| Campo | Contenido |
|-------|-----------|
| **Actor** | Quién ejecuta o desencadena |
| **Precondición** | Estado previo necesario para que el requisito aplique |
| **Descripción** | Comportamiento exacto del sistema. Sin ambigüedades. |
| **Se verifica en** | `CA-PAN-03.2`, `CA-ACT-02.1`… o, si no depende de pantalla ni tarea, `CA-RF-012.1` **Dado** [estado previo], **cuando** [acción], **entonces** [resultado verificable] |
| **Fuente** | [FU-03 00:42:15] |
| **Prioridad** | MUST / SHOULD / COULD (MoSCoW) |
| **Certeza** | 🔒 Validado / ✅ Decidido / 🔶 Inferencia / ⚠️ Pendiente / ❓ No definido |

---

**Ejemplo RF-012 — Registrar resultado de revisión:** el responsable de revisión
debe poder aprobar o rechazar la entrega; al rechazar, las observaciones son
obligatorias (mín. 20 caracteres) y la aTRP recibe aviso. Se verifica en
`CA-ACT-04.1`, `CA-ACT-04.2` y `CA-PAN-06.3`. [✅ Confirmado — FU-03 00:42:15,
Responsable de revisión]

---

### Sección 9 — Reglas de negocio

Las reglas de negocio describen BAJO QUÉ CONDICIONES o CON QUÉ LÓGICA actúa
el sistema. Son distintas de los requisitos funcionales (que describen QUÉ hace).

Cada RB debe referenciar los RFs que la activan — y cada RF mencionado en una
RB debe a su vez incluir en su descripción la regla que aplica. Esta referencia
cruzada RF↔RB permite a desarrollo tener todo el contexto en un único punto.

Una fila por regla:

| ID | Descripción | Cuándo aplica | Efecto | Fuente | Certeza |
|----|-------------|---------------|--------|--------|---------|
| RB-001 | Enunciado preciso con valores concretos si se mencionaron | RF o evento que la activa («Al ejecutar RF-003») | Qué ocurre cuando se cumple / no se cumple | `[FU-03 00:14:32]` y rol de quien la mencionó | 🔒 / ✅ / 🔶 / ⚠️ / ❓ |

**Ejemplo RB-007:** Si una aTRP supera 3 entregas rechazadas en el mismo
expediente, el sistema bloquea nuevas entregas y notifica al Coordinador.
[✅ Confirmado — FU-05 00:12:40, Coordinador]

---

### Sección 10 — Modelo de datos funcional

**Principio estricto**: Solo incluir atributos que las transcripciones mencionan
explícitamente o que se derivan de forma directa e inequívoca del flujo.

Para cada entidad:
- *Nombre* y correspondencia con Record Type en Appian
- *Descripción*: qué representa en el negocio

**Tabla de atributos:**
| Clave (PK/FK) | Nombre | Tipo | Fuente / Base | Descripción y reglas |
|---------------|--------|------|---------------|---------------------|

**Tabla de relaciones entre entidades:**
| Entidad origen | Relación | Entidad destino | Cardinalidad | Notas |
|----------------|----------|-----------------|--------------|-------|
| Expediente | contiene | Entrega | 1..N | Una aTRP puede hacer N entregas por expediente |

Si una entidad no fue suficientemente detallada: "Atributos no detallados en
sesiones. Pendiente de sesión de modelo de datos."

**Prohibido**: campos de auditoría técnica sin evidencia, enumeraciones que el
cliente no listó, estructura asumida de sistemas externos no descritos.

#### 10.1 Diagrama entidad-relación (Mermaid `erDiagram`)

Si hay **2 o más entidades con atributos definidos**, genera un `erDiagram` de
Mermaid que muestre entidades, atributos y cardinalidades. Si todas las
entidades están en ❓ (sin atributos), omite el diagrama y declara en su lugar:
"Modelo de datos pendiente de sesión específica — el erDiagram se generará
cuando los atributos estén definidos."

Sigue el workflow validar → renderizar → incrustar de `mermaid-diagrams.md`. Las
convenciones de cardinalidad, atributos PK/FK y un ejemplo completo están en
`mermaid-diagrams.md` (sección "erDiagram"). Guarda el diagrama como
`diagramas/er.mmd` y añade pie de figura debajo.

**Coherencia**: cada entidad y relación del diagrama debe aparecer también
en las tablas anteriores. El diagrama es una representación visual de lo
mismo, no una fuente alternativa.

---

### Sección 11 — Estados y ciclo de vida

Para cada entidad principal con ciclo de vida:

**Tabla de estados:**
| Estado | Nombre de negocio | Descripción | Quién lo establece |
|--------|-------------------|-------------|-------------------|

**Tabla de transiciones:**
| Estado origen | Evento / Acción | Estado destino | Actor | Condición |
|---------------|-----------------|----------------|-------|-----------|

**Acciones permitidas por estado:**
| Estado | Actor | Puede ver | Puede editar | Puede ejecutar |
|--------|-------|-----------|--------------|----------------|

Usar siempre nombres de negocio: ✅ "En elaboración" / ❌ "STATUS_ELAB"

#### 11.1 Diagrama de estados (Mermaid `stateDiagram-v2`)

Para cada entidad con **3 o más estados**, genera un `stateDiagram-v2` que
muestre el ciclo de vida completo. Una entidad con solo 1-2 estados no
necesita diagrama — la tabla basta.

Sigue el workflow validar → renderizar → incrustar de `mermaid-diagrams.md`. Las
convenciones (estados de negocio, transiciones con actor, estados finales por
cada cierre distinto) y un ejemplo completo están en
`mermaid-diagrams.md` (sección "stateDiagram-v2"). Guarda cada
diagrama como `diagramas/estados-<entidad>.mmd` y añade pie de figura.

**Regla de coherencia**: toda transición del diagrama debe aparecer también
en la tabla de transiciones. Sin flechas huérfanas, sin transiciones
"implícitas" — el diagrama y la tabla cuentan la misma historia.

---

### Sección 12 — Diseño funcional de pantallas

Una ficha por pantalla, vista o diálogo (un diálogo que se abre desde otra
pantalla es su propia ficha; la pantalla de origen solo dice «abre PAN-07»).
Es la sección que usa el prototipo y de la que salen las pruebas de pantalla:
cuanto más concreta, menos supuestos. Lo que no se sepa se marca ❓ en la
celda, no se inventa. Los apartados que no apliquen (una pantalla sin filtros)
se omiten.

**PAN-02 — Listado de expedientes** (en modo fiel, el nombre y el ID del documento)

| Campo | Detalle |
|-------|---------|
| **Tipo** | Página del site / vista de registro / formulario / asistente / diálogo / tarea |
| **Actores** | Roles que la usan |
| **Propósito** | Qué logra el usuario aquí, en una frase |
| **Se abre desde** | Pestaña del site, botón de PAN-xx, tarea ACT-xx, acción sobre un registro |
| **Organización** | Cómo se distribuye: secciones, pestañas, pasos, tabla agrupada… |
| **Requisitos** | RF y RB que cubre |
| **Fuente** | [FU-01 diap. 40] |

**Campos** (del formulario, o columnas del listado, en el orden en que aparecen):

| Campo | Tipo | Origen del valor | Editable | Obligatorio | Valores, por defecto y si está vacío | Fuente |
|-------|------|------------------|----------|-------------|--------------------------------------|--------|
| Aeropuerto | Lista (aeropuertos) | Datos maestros | Sí | Sí | Por defecto, el del usuario (RB-004) | [FU-03 00:14:32] |
| Fecha de aprobación | Fecha | Calculado: al pasar a «Aprobado» | No | — | Si no está aprobado, «-» | [FU-01 diap. 41] |

*Origen*: usuario / calculado (cómo) / datos maestros / sistema (fecha, usuario conectado) / otra entidad.

**Filtros**:

| Filtro | Control | Selección | Por defecto | Opciones (de dónde salen) |
|--------|---------|-----------|-------------|---------------------------|
| Estado | Desplegable | Múltiple | Todos | Estados de la Sec 11 |

Cómo se combinan (normalmente todos a la vez, Y), cuáles son básicos y cuáles
avanzados, y **qué pasa tras filtrar**: qué se actualiza (contadores,
totales) y qué se muestra si no hay resultados.

**Ordenación**: orden por defecto (columna y sentido) y columnas que el
usuario puede ordenar.

**Acciones**:

| Acción (texto literal) | Quién la ve / cuándo está activa | Qué pasa después | Confirmación (texto literal) |
|------------------------|----------------------------------|------------------|------------------------------|
| «Nuevo expediente» | Gestor de expedientes | Abre PAN-04 | — |
| «Eliminar» | Gestor, solo en «Borrador» | Elimina el expediente y vuelve al listado con el aviso «…» | «¿Desea eliminar el expediente? Esta acción no se puede deshacer.» |

**Toda acción que borre o anule algo lleva confirmación con su texto literal**;
si la fuente no lo da, se marca ❓ y va a Sec 17, no se inventa.

**Reglas de la pantalla** (numeradas; las de negocio generales se citan por su
RB-xxx):
1. Validaciones de formato y longitud, con el mensaje literal.
2. Cálculos automáticos (qué se calcula, cuándo y a partir de qué).
3. Visibilidad por rol, enumerada:
   - Gestor de expedientes: ve todo; «Editar» activo en «Borrador».
   - Consulta: solo expedientes «Aprobado»; sin acciones.
4. Lógica con varios escenarios: «Caso A: condición → efecto», «Caso B: …».

**Textos literales**: tooltips (y qué los muestra), avisos, mensajes de
error y de confirmación que no estén ya en las tablas anteriores.

**Criterios de aceptación** (funcionales y de presentación; cada uno se puede
probar solo sobre esta pantalla):
- `CA-PAN-02.1` **Dado** un gestor en el listado, **cuando** filtra por «Aprobado» y
  «Rechazado», **entonces** solo ve expedientes en esos estados y el contador
  muestra su número.
- `CA-PAN-02.2` **Dado** un usuario de Consulta, **cuando** abre el listado,
  **entonces** no ve el botón «Nuevo expediente».

**Capturas**: las añade el prototipo, una por línea y con la ruta relativa al `ddf.md`:
`![pie de figura](prototipos/<app>/capturas/02-listado.png)`. No cuentan como cambio de la ficha.

---

### Sección 13 — Integraciones y gestión documental

#### Integraciones con sistemas externos

Una fila por integración. Si no hay integraciones conocidas, indicar ❓.

| ID | Sistema | Dirección | Propósito | Trigger | Certeza |
|----|---------|-----------|-----------|---------|---------|
| INT-001 | [nombre] | Appian → Sistema | [para qué] | [cuándo] | ✅/🔶/⚠️/❓ |

*Dirección*: Appian → Sistema / Sistema → Appian / Bidireccional

**Detalle por integración** (para las que tienen certeza ✅ o 🔶):
| Campo | Detalle |
|-------|---------|
| **Sistema** | Nombre y versión si se conoce |
| **Datos enviados** | Campos que Appian envía |
| **Datos recibidos** | Campos que Appian recibe |
| **Protocolo** | REST / SOAP / Event / Webhook / Batch |
| **Puntos abiertos** | Qué queda por definir |

#### Gestión documental

Incluir solo si el proceso maneja documentos. Si no aplica, indicarlo.

| Documento | Quién genera / carga | Momento en el flujo | Almacenamiento | Obligatorio para avanzar |
|-----------|---------------------|--------------------|-----------------|--------------------------| 

---

### Sección 14 — Notificaciones, alertas y escalados

| ID | Evento desencadenante | Canal | Destinatario(s) | Contenido principal | Momento | Tipo |
|----|----------------------|-------|-----------------|---------------------|---------|------|

*Tipo*: **Crítica** (bloquea el proceso si no llega) / **Informativa** (aviso sin efecto en el flujo)

**Escalados**: Para cada escalado: condición que lo activa → a quién escala →
acción esperada del receptor.

---

### Sección 15 — Reporting y trazabilidad

**KPIs e indicadores:**
| KPI | Descripción | Cómo se calcula | Frecuencia | Audiencia |
|-----|-------------|-----------------|------------|-----------|

**Datos de auditoría y trazabilidad:**
| Evento trazado | Datos registrados | Para qué se necesita | Obligatorio |
|----------------|-------------------|---------------------|-------------|

**Informes y dashboards identificados:**
| Nombre | Contenido | Filtros disponibles | Formato exportación | Audiencia |
|--------|-----------|--------------------|--------------------|-----------|

Si el cliente no mencionó reporting, inferir al menos los indicadores básicos
del proceso (ej: volumen de expedientes, tiempo medio de resolución, tasa de
aprobación) y marcarlos como 🔶 Inferencia razonable.

---

### Sección 16 — Criterios de aceptación y cobertura

Los criterios ya están escritos en las fichas (Sec 6.3 y 12) y en los RF sin
pantalla ni tarea (Sec 8). Esta sección no los repite: comprueba que no falta
ninguno y define los recorridos completos.

**Matriz de cobertura** (una fila por RF):

| RF | Prioridad | Se verifica en | ¿Cubierto? |
|----|-----------|----------------|------------|
| RF-012 | MUST | CA-ACT-04.1, CA-ACT-04.2, CA-PAN-06.3 | Sí |
| RF-015 | MUST | — | ❌ Falta criterio → Sec 17 |

**Regla**: todo RF MUST tiene al menos un criterio. Los que no, van a Sec 17
como pregunta 🟡 (o 🔴 si bloquea el diseño).

**Escenarios de extremo a extremo** (modo síntesis): uno por cada camino
principal del proceso (camino feliz y cada rechazo o excepción relevante),
como secuencia de tareas y estados:

- `CA-E2E-01` Alta aprobada: ACT-01 («Borrador») → ACT-02 «Aprobar» («Aprobado»)
  → ACT-03 («Cerrado»). Se valida con CA-ACT-01.1, CA-ACT-02.1 y CA-ACT-03.1.

---

### Sección 17 — Riesgos, dependencias y validaciones pendientes

**Riesgos funcionales:**
| ID | Descripción | Impacto | Probabilidad | Mitigación propuesta |
|----|-------------|---------|--------------|---------------------|
| R-001 | … | … | … | … |

**Dependencias**: Sistemas, procesos o decisiones que condicionan la
construcción o la puesta en marcha.

**Puntos abiertos**: Todo lo pendiente de decisión. Indicar quién decide y
cuándo se necesita para no bloquear.

**Preguntas de validación pendientes:**
- 🔴 **CRÍTICA** — Bloquea el diseño. Sin respuesta no se puede avanzar.
- 🟡 **IMPORTANTE** — Afecta funcionalidad relevante. Necesaria antes del sprint.
- 🟢 **MEJORA** — Perfecciona el diseño pero no bloquea.

Para cada pregunta: ID, enunciado, por qué importa, a quién va dirigida.
Una pregunta contestada no se borra: `| ~~P-003~~ | … | Respondida por D-015 |`.

**Registro de decisiones** (una sola tabla para todo el documento): los cambios
de rumbo y lo que el cliente valida o anula, en orden de fecha. Es el historial
del análisis: el resto del `ddf.md` es el estado actual.

| ID | Fecha | Fuente | Tipo | Decisión | Antes | Piezas | Vigente |
|----|-------|--------|------|----------|-------|--------|---------|
| D-001 | 2026-07-10 | [FU-17 00:21:54] | CAMBIA | El flujo del requerimiento lo configura cada tipología en el orquestador | Fijo: elaboración y revisión con cinco acciones [FU-06 00:07:08] | ACT-02, ACT-05, RF-006 | No: sustituida por D-004 |
| D-004 | 2026-08-14 | [FU-22 00:05:10] | ANULA | Se elimina el paso de elaboración del requerimiento | D-001 | ~~ACT-02~~, RF-006 | Sí |

- **Tipo**: `CAMBIA` (sustituye una decisión anterior), `ANULA`, `VALIDA` (el
  cliente confirma por escrito o en revisión; las piezas pasan a 🔒), `RESPONDE`
  (contesta una P-xxx), `ALCANCE+` / `ALCANCE−` (entra o sale del alcance, Sec 3).
- **Vigente**: «Sí», «No: sustituida por D-xxx» o «En parte: D-xxx cambia …».
- Lo nuevo, lo que completa una pieza y lo que confirma algo ⚠️ **no** lleva
  fila: basta con la cita en la pieza y la fila de la versión en la Sec 1.
- En la primera versión (síntesis), las filas son los cambios de criterio entre
  reuniones, numeradas `D-001`… por fecha. Solo con módulos (`volumen-grande.md`)
  se escriben `D-?` y `unir_modulos.py` las numera al unir.

---

## Formato del documento `.docx`

Se genera con `scripts/ddf_docx.js` a partir del `ddf.md` (mismo contenido, misma
numeración) y se revisa con la skill `docx`. Para una versión nueva se actualiza el `ddf.md` y se regenera el
`.docx` completo: no se edita el Word a mano.

- **Portada** con nombre del proyecto, cliente, versión y fecha
- **Tabla de contenidos** automática con hipervínculos
- **Encabezado** con nombre del documento en todas las páginas
- **Pie de página** con confidencialidad, versión y número de página
- **Heading styles** para separación clara de secciones
- **Tablas** para actores, RF, RB, datos, estados, notificaciones y gaps
- **Callout boxes** para CRÍTICO / VALIDAR / SUPUESTO / CONTRADICCIÓN
- **Numeración** de RFs (RF-XXX) y RBs (RB-XXX) para referencia cruzada
- **Figuras numeradas** para cada diagrama (BPM, casos de uso, ER, estados) y
  cada captura del prototipo de la Sec 12, con pie `Figura N — [pie]`. La
  numeración se hace al generar el `.docx`, en el orden en que aparecen

---

## Verificación de completitud antes de cerrar el documento

Antes de considerar el análisis terminado, recorre este checklist. En modo
fiel no aplican las casillas marcadas «(síntesis)».
Si alguna sección está vacía o tiene solo el encabezado, complétala —
aunque la información sea mínima, escribe lo que hay y marca los gaps:

- [ ] Sec 1 — Portada con versión, fecha, tabla de fuentes y control de versiones
- [ ] Sec 2 — Resumen ejecutivo + AS-IS/TO-BE con contenido real (síntesis)
- [ ] Sec 3 — Lista concreta de qué incluye y qué excluye (no genérica)
- [ ] Sec 4 — Tabla de supuestos con al menos 2-3 filas + restricciones (síntesis)
- [ ] Sec 5 — Tabla de actores con «Participa en», roles y permisos + párrafo por actor
- [ ] Sec 6 — Tabla de actividades con estados de entrada/salida y «En la aplicación»; ficha por tarea de usuario con todas sus opciones y su criterio mínimo; diagrama BPM renderizado e incrustado y fichas de proceso (síntesis)
- [ ] Sec 7 — Tabla resumen de CUs + fichas detalladas para los críticos; diagrama actor↔CU si aplica (≥3 actores o ≥6 CUs) (síntesis)
- [ ] Sec 8 — RFs con ID, fuente y «Se verifica en»; en síntesis, ≥1 RF por paso del Happy Path
- [ ] Sec 9 — RBs con ID, efecto, fuente y certeza; referencias cruzadas RF↔RB
- [ ] Sec 10 — Modelo de datos con tabla de atributos y relaciones; `erDiagram` si ≥2 entidades tienen atributos definidos (síntesis)
- [ ] Sec 11 — Estados y ciclo de vida con transiciones; `stateDiagram-v2` por cada entidad con ≥3 estados (síntesis)
- [ ] Sec 12 — Fichas de pantalla con «se abre desde», campos (tipo, origen, editable, obligatorio, vacío), filtros (única/múltiple, por defecto), ordenación, acciones con «qué pasa después», confirmación literal en todo borrado, visibilidad por rol y criterios de aceptación
- [ ] Sec 13 — Tabla de integraciones + gestión documental (o indicar ❓ si no aplica)
- [ ] Sec 14 — Tabla de notificaciones y escalados (o indicar ❓ si no aplica)
- [ ] Sec 15 — KPIs y reporting (en síntesis, inferir mínimos si el cliente no lo mencionó)
- [ ] Sec 16 — Matriz de cobertura sin RF MUST sin criterio; escenarios de extremo a extremo (síntesis)
- [ ] Ningún criterio de aceptación aparece escrito en dos sitios; estados de las fichas de tarea = transiciones de la Sec 11
- [ ] Sec 17 — Riesgos, dependencias y preguntas pendientes clasificadas 🔴🟡🟢
- [ ] El proceso pasó `diagrama.py` y los diagramas Mermaid pasaron `render_mermaid.py` sin error y se revisó cada PNG; ninguno quedó como código sin renderizar (salvo fallback documentado en Sec 17) (síntesis)
- [ ] Todo RF, RB, campo y pantalla cita su fuente; ningún ID se ha renumerado respecto a la versión anterior
- [ ] Sec 17 — Registro de decisiones con los cambios de criterio; ninguna pieza vigente remite a una pieza anulada (`comprobar_ddf.py`)
