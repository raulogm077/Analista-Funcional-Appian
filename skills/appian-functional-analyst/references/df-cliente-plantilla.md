# DF del cliente (`analisis/df-cliente.md`)

Es el documento que el cliente revisa, corrige y valida: qué proceso se automatiza, cómo funciona cada actividad, qué
hace cada pantalla, quién puede hacer qué, qué correos salen, qué se gana y cuánto dura la estabilización. Sale en
Word sobre la plantilla del DF (`assets/plantillas/df-cliente.docx`, o la del cliente en `<p>/plantillas/`) con
`df_cliente_docx.py`.

Se escribe **desde las fuentes del proyecto**: reuniones, correos, documentos, capturas, diagramas y lo que se pase
como contexto. No se deriva del análisis funcional (`funcional.md`): si el proyecto lo tiene, es una fuente más. Cómo
se construye desde cero y cómo entra cada fuente nueva: `df-cliente-construir.md`. Cómo se describe una pantalla:
`requerimientos-pantallas.md`.

Los ejemplos son de un caso ficticio (solicitudes de autorización) y tienen el formato exacto que lee el script.

## Lo que leen el script y las personas

- **Cabecera**: `# <Proceso> — Documento de diseño funcional`, la línea `Código: … · Proyecto: … · Ciudad: … · Fecha:
  …` y la línea `Versión: 0.1 · Estado: borrador` (estados: borrador, en revisión, validado).
- **Apartados** con los números de la plantilla: `## 1.`, `### 1.1`, `#### …`. Los títulos de la plantilla no se
  cambian.
- **Solo lo que lee el cliente.** El DF no lleva fuentes, estados, preguntas abiertas ni notas del equipo, tampoco
  escondidos en comentarios: todo eso vive en dos ficheros aparte, junto a él, que no salen en el Word:
  - `analisis/df-cliente-fuentes.md`: de dónde sale cada bloque (§«Fuentes de cada bloque», abajo);
  - `analisis/df-cliente-pendientes.md`: lo que falta por confirmar (§«Pendientes», abajo).
- **Lo que deja de valer** se borra del texto: el DF dice siempre lo vigente. Lo de antes queda en `decisiones.md`
  (`df-cliente-construir.md` §3).
- **Lo pendiente**, mientras se trabaja, se escribe «pendiente de confirmar» en la frase que afecta (sale resaltado
  en el Word, para que se vea en una revisión) y su pregunta va a `df-cliente-pendientes.md`. Al resolverse, la frase
  se completa y la pregunta sale de ese fichero. En la entrega no queda ninguno.
- **Referencias por nombre, nunca por número**: «(se describe en la pantalla "Nueva solicitud")», «(ver regla común
  "Plazos")». Los números cambian al reordenar.
- **Una sola vez**: cada cosa se dice en su sitio y los demás la citan. Lo común a todo el flujo, en 2.1; quién ve
  qué, solo en 2.4.1; el texto de un correo, solo en 2.4.2.

## Cómo se escribe

Además de `redaccion.md`:
- **Para el cliente.** Lo lee alguien de negocio que tiene que reconocer su proceso. Sus palabras («expediente», no
  «registro»), sin nombres de objetos ni de componentes de Appian. Los términos de pantalla corrientes (modal,
  desplegable, tooltip, pestaña) sí se usan: son los que el cliente ve.
- **Afirmativo y verificable.** «Al pulsar "Enviar", la solicitud pasa a "En revisión"», no «se podría enviar». Lo que
  es opcional para el usuario, con «puede».
- **El después de cada acción.** Toda acción (pulsar, enviar, cancelar, que venza un plazo) dice qué pasa a
  continuación: cambio de estado, correo, a quién le llega.
- **Textos literales entre comillas**: estados, botones, mensajes, asuntos de correo.
- **Nada inventado.** Lo que las fuentes no dicen se pregunta. «N/A» solo cuando de verdad no aplica.

## Portada y control de cambios

```markdown
# Solicitudes de autorización — Documento de diseño funcional

Código: DF-AUT-001 · Proyecto: Gestión de autorizaciones · Ciudad: Madrid · Fecha: Octubre 2026
Versión: 0.1 · Estado: borrador

## Control de cambios

| Fecha entrega | Versión | Descripción / Motivo del cambio | Autor | Responsable de validación | Fecha de validación |
|---|---|---|---|---|---|
| 14/10/2026 | 1.0 | Primera versión del diseño funcional | Equipo de análisis | | |
```

- **Título**: el nombre del proceso. Sale en la portada y en el encabezado de cada página.
- **Código**: lo da el equipo; se pregunta la primera vez y no se inventa.
- **Proyecto, Ciudad y Fecha** (mes y año de la entrega): para la portada.
- **Versión**: la del DF del cliente. 0.x mientras se trabaja; 1.0 en la primera entrega; cada entrega posterior sube
  la versión y añade su fila.
- **Control de cambios**: una fila por entrega. «Descripción / Motivo del cambio» dice en una frase qué cambió y por qué
  («Se añaden las prórrogas, acordadas en la reunión del 20/10»). «Responsable de validación» y «Fecha de validación»
  se rellenan cuando el cliente valida.

## 1. Introducción al proceso

### 1.1 Descripción del proceso

Para qué lo lee el cliente: comprobar que el equipo ha entendido su proceso tal como es hoy.

```markdown
#### Descripción del proceso

Las unidades de la organización piden autorización para ocupar espacios comunes con actividades temporales. Hoy la
solicitud llega por correo con un formulario en hoja de cálculo; el área de autorizaciones la revisa, pide lo que
falta por correo y resuelve con un escrito firmado. El seguimiento se lleva en una hoja compartida.

#### Integraciones

- **Registro de organismos** – Al enviar la solicitud se comprueba que la unidad está de alta.
- **Gestor documental** – El escrito de resolución firmado se archiva en el expediente de la unidad.
```

- **Descripción del proceso**: qué es, quién lo inicia, para qué sirve y cómo se hace hoy (lo que salió del
  descubrimiento), en dos o tres párrafos. Sin la solución: eso es el 1.2 y el 2. Después, si las fuentes lo dan:
  - el objetivo funcional, como lista de lo que el cliente quiere poder hacer («Gestionar las solicitudes y su
    documentación», «Dar seguimiento a los plazos»);
  - quién interviene: las áreas o roles de la organización y los actores de fuera (organismos, empresas externas), una
    viñeta cada uno;
  - las tecnologías con las que se hace hoy o con las que se hará, si el cliente las nombra.
- **Integraciones**: una viñeta por sistema, `**Sistema** – qué se intercambia y cuándo`. Si no hay, «No hay
  integraciones con otros sistemas.».

### 1.2 Alcance

Para qué lo lee el cliente: saber qué entra, qué no y desde cuándo aplica.

```markdown
#### Dentro del alcance

Digitalizar la solicitud, la revisión y la resolución de las autorizaciones de ocupación temporal.

Las unidades registran la solicitud con el espacio, las fechas y la documentación; el área de autorizaciones la
revisa, la devuelve si falta algo y la resuelve. Se registran la unidad, el espacio, las fechas, los documentos y la
resolución.

Aplica a las solicitudes nuevas desde la puesta en marcha; las que estén en curso terminan por correo.

#### Fuera del alcance

- Queda fuera del alcance aquellos aspectos no contemplados en este documento.
- El cobro de las tasas, que irá en una fase posterior.
```

- **Dentro del alcance**, tres párrafos: el objetivo respecto al proceso; la solución y los datos principales que se
  registran; a qué registros aplica (nuevos, históricos, en curso).
- **Fuera del alcance**: la primera viñeta es siempre la frase fija. Después, lo excluido de forma explícita, con su
  motivo o la fase en que irá.

## 2. Diseño de la solución

### 2.1 Flujo del proceso

Para qué lo lee el cliente: ver el proceso nuevo de un vistazo y las reglas que valen en todo él.

```markdown
### 2.1 Flujo del proceso

El proceso empieza cuando una unidad registra una solicitud. Pasa por la revisión del área de autorizaciones y por la
resolución, y termina con la solicitud autorizada, denegada o archivada.

![Flujo del proceso Solicitudes de autorización – Situación futura (To Be)](diagramas/solicitud.png)

#### Lógica general del flujo

##### Regla común 1 · Plazos

- Los plazos de este documento se cuentan en días hábiles, según el calendario laboral de la organización.
- Si un plazo vence en un día no hábil, pasa al siguiente día hábil.

##### Regla común 2 · Cancelar la solicitud

- La unidad solicitante puede cancelar su solicitud en cualquier estado anterior a "Resuelta".
- Al cancelarla, la solicitud pasa al estado "Cancelada", deja de recibir tareas y se envía la notificación de
  cancelación. La cancelación es definitiva: la solicitud no puede reabrirse.
- Si la solicitud tenía una consulta abierta con otra unidad, la consulta se cierra con la fecha de cancelación.
```

- Un párrafo con el flujo futuro: el evento que lo inicia, las fases y el resultado final.
- El diagrama: el PNG que dibuja `appian-diagramas-bpmn`. El texto entre corchetes es el pie de figura. Sin diagrama,
  la línea queda y el Word deja el hueco.
- **Un flujo grande** se parte: primero una visión general con todas las fases y después un diagrama por fase, cada
  uno con su pie y las actividades que abarca («Actividades ACT-03 a ACT-08»). Si el diagrama distingue tipos de
  estado o subestado (obligatorio, opcional, automático), la leyenda va con él.
- **Lógica general del flujo**: lo que vale en todo el flujo o en varias actividades (estados y etiquetas, plazos,
  asignación, cancelar, pausar y reanudar, volver atrás, cómo se muestra algo en todas las tareas). Una regla por
  `##### Regla común n · Título`. En el Word, la primera columna lleva «REGLA COMÚN n» y, debajo, su título en
  mayúsculas; la segunda, solo su texto. Cada regla:
  - cuándo aplica (en qué estados, mientras qué no haya pasado);
  - qué pasa, en orden, con los estados y etiquetas exactos;
  - qué no cambia o qué no se puede hacer después;
  - los casos límite (qué pasa si coincide con otra regla, si es la última, si ya terminó).
  Lo que dice una regla común no se repite en las actividades: se cita («ver regla común "Plazos"»).

### 2.2 Descripción de actividades

Para qué lo lee el cliente: validar, paso a paso, quién hace qué, cuándo empieza, cómo termina y adónde lleva.

Una ficha por actividad del diagrama, en el orden del flujo, con el identificador del cliente si tiene uno (si no,
`ACT-nn`) y el mismo nombre que el diagrama. Diez filas, en este orden:

```markdown
#### ACT-03 Revisar la solicitud

| Campo | Valor |
|---|---|
| Descripción | En este paso, el Área de autorizaciones comprueba que la solicitud está completa y que la documentación es válida.<br>Se llega desde el registro de la solicitud y, si se devolvió, desde su subsanación.<br>Si falta algo, la devuelve a la Unidad solicitante con el motivo; si está completa, la pasa a resolución. |
| Actores | Área de autorizaciones |
| Entrada / Salida | **Entrada:**<br>- Solicitud enviada desde Registrar la solicitud (ACT-02).<br>- Solicitud subsanada desde Subsanar la solicitud (ACT-04).<br>**Salida:**<br>- Solicitud devuelta: Subsanar la solicitud (ACT-04).<br>- Solicitud completa: Resolver la solicitud (ACT-05). |
| Estados de la entrada / Estados de salida | **Entrada:** En revisión / Pendiente de revisar.<br>**Salida** (según la acción seleccionada):<br>- Acción "Devolver" → Pendiente de subsanar / Devuelta.<br>- Acción "Pasar a resolución" → En resolución / Pendiente de resolver. |
| Formas de arranque / Formas de finalización | **Arranque:**<br>- Acción "Enviar" de la Unidad solicitante en Registrar la solicitud (ACT-02).<br>- Acción "Reenviar" de la Unidad solicitante en Subsanar la solicitud (ACT-04), una vez corregido lo que faltaba.<br>**Finalización:**<br>- Acción "Devolver", con el motivo obligatorio: la solicitud pasa a Subsanar la solicitud (ACT-04).<br>- Acción "Pasar a resolución": la solicitud pasa a Resolver la solicitud (ACT-05).<br>- Cancelación de la solicitud por la Unidad solicitante, en cualquier momento (ver regla común "Cancelar la solicitud"). |
| Lógica de asignación | La tarea llega a la bandeja común del Área de autorizaciones y es de quien la abre primero; mientras la tiene abierta, nadie más puede tomarla. |
| Documentos | Memoria de la actividad, plano del espacio. |
| Reglas de negocio | - Para devolver es obligatorio escribir el motivo.<br>- Una solicitud solo puede devolverse dos veces; a la tercera, se resuelve. |
| Notificaciones | NOT-02 Solicitud devuelta. |
| Ejecución esperada | 5 días hábiles desde que llega (ver regla común "Plazos"). |
```

| Fila | Qué se escribe |
|---|---|
| Descripción | Qué se hace y para qué, desde dónde se llega y qué se decide, en dos o cuatro frases. Si una acción vuelve a este paso desde otros, se dice aquí. |
| Actores | El rol que la hace (los nombres de 2.4.1), «Aplicación» si es automática o el organismo de fuera. |
| Entrada / Salida | **Entrada:** cada actividad de la que se llega, una por línea, con lo que llega y su identificador. **Salida:** cada actividad a la que se puede ir, una por línea, con el caso que lleva a ella. |
| Estados de la entrada / Estados de salida | **Entrada:** el estado (y subestado) con el que llega. **Salida:** una línea por acción, `Acción "X" → Estado / Subestado`; si es automática, el evento en vez de la acción. |
| Formas de arranque / Formas de finalización | **Arranque:** cada forma en que empieza, una por línea: la acción exacta y en qué actividad se pulsa, el evento automático (un documento que llega, una fecha que se alcanza, la respuesta de otro sistema) o la regla común que la abre, con su condición. **Finalización:** cada acción o evento que la termina, una por línea, con su nombre exacto y adónde lleva; también las de las reglas comunes que la cortan (cancelar, pausar). |
| Lógica de asignación | A quién le llega: un grupo, una persona, por reparto; qué pasa si nadie la coge. «N/A» si no hay tarea. |
| Documentos | Los que se consultan, se adjuntan o se generan aquí. |
| Reglas de negocio | Solo las de esta actividad; las comunes están en 2.1. |
| Notificaciones | Los NOT-nn que salen aquí (2.4.2), con su nombre. |
| Ejecución esperada | El plazo y qué pasa si se supera. «N/A» si no tiene. |

Cómo se escribe cada campo:
- **Estructurado, no en párrafo corrido.** En los campos con dos partes, cada una con su etiqueta en negrita y dos
  puntos (`**Entrada:**`, `**Salida:**`, `**Arranque:**`, `**Finalización:**`) y debajo una línea por elemento.
- **Mayúsculas donde aplican**: los estados y subestados, los roles y los nombres de las actividades se escriben como
  en el flujo y en 2.4.1, con su mayúscula inicial («En revisión / Pendiente de revisar», «Área de autorizaciones»); la
  frase, con la normal de cualquier frase.
- **Las acciones con su nombre exacto**, entre comillas y como dice el botón: «Acción "Pasar a resolución"». Es el
  mismo nombre en Estados de salida, en Formas de finalización, en la pantalla donde está el botón y en la matriz de
  permisos. Nunca «se aprueba» o «se valida» sin decir qué acción lo hace.
- **Todo el detalle**: cada forma de arrancar y de terminar, también las automáticas y las de las reglas comunes; cada
  una con su origen o su destino (la actividad y su identificador) y la condición si la tiene. Si una actividad tiene
  tres salidas, hay tres líneas.
- `<br>` separa líneas dentro de una celda; una línea que empieza por «- » sale con viñeta.
- Una fila sin contenido real: «N/A». Si falta el dato: «pendiente de confirmar».
- Cada ficha sale en su propia página.

### 2.3 Diseño de la pantalla / layout

Para qué lo lee el cliente: validar, pantalla a pantalla, todo lo que se ve y lo que pasa con cada acción. Es la parte
más larga y la que más se corrige.

Las pantallas se agrupan **por área** (lo que en el proyecto serían épicas: la gestión de solicitudes, los datos
maestros, el cuadro de mando). Las áreas salen de cada proyecto: no hay una lista fija.

```markdown
### 2.3 Diseño de la pantalla / layout

#### 2.3.1 Pantallas Solicitudes

##### Bandeja de solicitudes

###### Ejemplo ilustrativo
Caso 1: bandeja del área de autorizaciones con solicitudes pendientes.

![Bandeja de solicitudes](../prototipo/capturas/01-bandeja.png)

###### Lógica General
1. Esta pantalla corresponde a la página principal del apartado "Solicitudes". Muestra las solicitudes …

###### Búsqueda y Filtros
…

##### Nueva solicitud
…
```

- **Antes de las áreas**, un párrafo con lo que es la solución y de cuántas partes se compone, y una línea por área
  con para qué sirve:

  ```markdown
  La solución centraliza la gestión de las autorizaciones y se compone de tres apartados:

  - **Solicitudes**: registro, revisión y resolución de cada solicitud, con su documentación y sus plazos.
  - **Cuadro de mando**: visión agregada de las solicitudes por estado, espacio y unidad.
  - **Datos maestros**: configuración de los espacios, los tipos de documento y los grupos.
  ```
- Las áreas son las de cada proyecto. Si varias áreas comparten secciones iguales (la documentación o los comentarios
  de varios tipos de registro), van una sola vez en un área «Pantallas comunes» y las demás la citan. Una herramienta
  de configuración de la propia solución (de flujos, de plantillas, de permisos) es un área más.
- `#### 2.3.n Pantallas <Área>` abre cada área; `##### <Nombre de la pantalla>`, cada pantalla, modal o sección de un
  registro que se describe por separado; `###### …`, sus apartados.
- Los apartados, su orden, qué va en cada uno y cómo se describe cada elemento: `requerimientos-pantallas.md`.
- La captura la pone `appian-prototipos` en `../prototipo/capturas/`, o es la que pasa el cliente. El prototipo solo
  enlaza sus capturas en las fichas PAN del funcional: en el DF del cliente, la línea de la imagen la pone el analista,
  con la ruta que `appian-prototipos` deja en `prototipo/capturas/indice.md`. Sin captura, el caso y la línea de la imagen quedan y el Word deja el
  hueco.
- Al final de cada pantalla el Word añade la nota fija: la visibilidad por rol no va aquí, va en 2.4.1.

### 2.4 Otras consideraciones

#### 2.4.1 Roles y permisos

Para qué lo lee el cliente: decidir quién puede ver y hacer cada cosa. Es la **única fuente** de la visibilidad por rol:
las pantallas describen todo lo que existe y no dicen quién lo ve. Un cambio de permisos se hace aquí y solo aquí.

```markdown
#### 2.4.1 Roles y permisos

##### Descripción general

Los roles deciden qué información ve cada persona y qué acciones puede hacer en las solicitudes. Su propósito es que
cada persona acceda solo a lo que le corresponde según su papel en el proceso, sin configurarlo caso por caso.

Todas las personas de la organización pueden registrar solicitudes y ver las suyas. La bandeja del área, la resolución
y los datos maestros quedan reservados a los roles de la tabla.

##### Roles

| Rol | Descripción | Dónde se define |
|---|---|---|
| Unidad solicitante | Persona de una unidad que registra la solicitud y la subsana. | Sistema (quien crea la solicitud) |
| Área de autorizaciones | Revisa las solicitudes y las pasa a resolución. | Datos maestros → Grupos |
| Responsable del área | Resuelve las solicitudes y mantiene los datos maestros. | Datos maestros → Grupos |

##### Matriz de permisos

| Acción | Unidad solicitante | Área de autorizaciones | Responsable del área |
|---|---|---|---|
| Solicitudes | | | |
| Ver solicitudes | ✓* | ✓ | ✓ |
| Crear solicitud | ✓ | | |
| Devolver solicitud | | ✓ | ✓ |
| Resolver solicitud | | | ✓ |
| Datos maestros | | | |
| Gestionar espacios | | | ✓ |

\*Ver solicitudes: la unidad solicitante solo ve las de su unidad.
```

- **Descripción general**: qué regulan los roles y para qué; el acceso por defecto; lo que queda restringido.
- **Roles**: uno por fila, con el nombre que usan las actividades y las pantallas. Si un rol se da solo al pasar algo
  (al asignar una tarea, al consultar a alguien), se dice en su descripción y qué otro rol recibe con ello («Tras su
  asignación, también pasa a ser visualizador de la solicitud»). «Dónde se define»: datos maestros
  (con la ruta), un campo del registro (quien crea, el asignado) o el sistema de usuarios del cliente. Un rol que no
  entra en la aplicación pero aparece en el proceso, también, con «Solamente informativo».
- **Matriz**: una columna por rol, en el orden de la tabla. Las filas se agrupan por área o por pantalla: una fila con
  solo el nombre abre el grupo y debajo van sus acciones, con «✓» donde está permitida (vacía, no permitida). Toda
  acción descrita en 2.3 está en la matriz, también «Ver sección …». Los matices, con asterisco en la acción o el rol y
  la aclaración debajo, en una línea que empieza por `\*`. Si una columna agrupa varios roles, se dice con asterisco.

#### 2.4.2 Notificaciones por correo

Para qué lo lee el cliente: validar cuándo sale cada correo, a quién y con qué texto exacto.

```markdown
#### 2.4.2 Notificaciones por correo

| ID | Comunicación | Disparador | Destinatarios | Asunto | Cuerpo |
|---|---|---|---|---|---|
| NOT-01 | Solicitud registrada | La unidad envía la solicitud (ACT-02) | Área de autorizaciones | Autorizaciones – [Número] – Nueva solicitud | Buenos días.<br>Se ha registrado la solicitud [Número] de la unidad [Unidad], para el espacio [Espacio] del [Fecha inicio] al [Fecha fin].<br>Puede acceder a la solicitud a través del siguiente enlace: [Enlace a la solicitud]. |
| NOT-02 | Solicitud devuelta | El área devuelve la solicitud (ACT-03) | Unidad solicitante | Autorizaciones – [Número] – Solicitud devuelta | Buenos días.<br>La solicitud [Número] se ha devuelto por este motivo: "[Motivo]".<br>Puede corregirla a través del siguiente enlace: [Enlace a la solicitud]. |
```

- Una fila por correo. Las tareas que solo llegan a la bandeja no van aquí.
- **Disparador**: el evento y la actividad o la regla común que lo produce.
- **Destinatarios**: los roles; si cambian según el caso, uno por línea («Solicitud → …; Consulta → …»).
- **Asunto**: `<Aplicación> – [ID del registro] – <Texto>`.
- **Cuerpo**: el texto literal, con las variables entre corchetes y el enlace al registro; `<br>` separa párrafos.
  Varios correos con la misma lógica que otro: «Misma lógica que NOT-01» en las columnas que se repiten.
- El Word añade, en «Ejemplos visuales de las notificaciones», una maqueta de cada correo hecha con esta tabla. Si no
  hay correos, «No hay.».

### 2.5 Métricas y KPIs

Para qué lo lee el cliente: ver qué gana con la automatización.

```markdown
### 2.5 Métricas y KPIs

| Indicador | As Is horas | As Is FTE | To Be horas | To Be FTE | Reducción % |
|---|---|---|---|---|---|
| Tiempo de esfuerzo manual dedicado al proceso al año | 3.200 | 2 | 1.100 | 0,7 | 65 % |

| Indicador | As Is | To Be | Reducción % |
|---|---|---|---|
| Tiempo de ciclo del proceso (Lead Time) | 15 días | 5 días | 67 % |
```

- Dos tablas con estas columnas exactas. Otras métricas, como filas de la segunda.
- Solo cifras que dé el cliente o que salgan de sus datos, con su fuente en `analisis/df-cliente-fuentes.md`. Lo que no se sabe:
  «pendiente de confirmar» y su pregunta («¿Cuántas horas al año dedica hoy el área a las autorizaciones?»).

### 2.6 Periodo de estabilización

Para qué lo lee el cliente: saber cuánto dura el acompañamiento tras la puesta en marcha.

```markdown
### 2.6 Periodo de estabilización

Teniendo en cuenta que se trata de un proceso **mensual** se establece un **período de estabilización de 3 meses**.
```

- La periodicidad del proceso (anual, mensual, diario…) y los meses salen de las fuentes; si no, «pendiente de
  confirmar».

## Fuentes de cada bloque (`analisis/df-cliente-fuentes.md`)

No sale en el Word. Una fila por bloque del DF (una regla común, una actividad, una pantalla, un rol, un correo, una
cifra), con su estado y las fuentes de las que sale; los estados y las citas, como en el resto del plugin
(`funcional-plantilla.md` «Lo que leen los scripts» e `ingesta-fuentes.md` §2). Sirve para saber de dónde sale cada
cosa cuando el cliente pregunta y para encontrar qué bloques toca una fuente nueva.

```markdown
# Solicitudes de autorización — Fuentes del DF del cliente

| Apartado | Bloque | Estado | Fuentes |
|---|---|---|---|
| 1.1 | Descripción del proceso | ✅ | FU-01 00:03:10 |
| 1.1 | Integración Registro de organismos | ✅ | FU-02 00:21:40 |
| 2.1 | Regla común "Plazos" | 🔒 | FU-01 00:12:10; FU-03 00:05:00 |
| 2.2 | ACT-03 Revisar la solicitud | ✅ | FU-01 00:12:10; FU-03 00:09:20 |
| 2.3 | Pantalla "Bandeja de solicitudes" | ✅ | FU-01 00:04:10; FU-05 captura 2 |
| 2.4.2 | NOT-02 Solicitud devuelta | ✅ | FU-03 00:31:40 |
| 2.6 | Periodo de estabilización | ✅ | FU-04 00:15:20 |
```

Los bloques se nombran como en el DF (el título de la pantalla, el identificador de la actividad): si cambia un
nombre en el DF, cambia aquí. Un bloque que se borra del DF sale de la tabla.

## Pendientes (`analisis/df-cliente-pendientes.md`)

No sale en el Word. Lo que falta por confirmar, una pregunta por fila, cerrada y con opciones cuando se puede:

```markdown
# Solicitudes de autorización — Pendiente de confirmar

| ID | Pregunta | Opciones | A quién | Afecta a | Fuente |
|---|---|---|---|---|---|
| PC-01 | ¿Qué pasa si la unidad no subsana en 10 días hábiles? | Se archiva / Se le recuerda cada 10 días | Área de autorizaciones | ACT-04, regla común "Plazos" | FU-03 00:16:20 |
```

- Cada fuente nueva que responde una pregunta la **quita** de aquí: la respuesta entra en el DF y queda en
  `decisiones.md` como RESPONDE, con la pregunta en «Antes». Lo que se responde a medias se reescribe con lo que queda.
- Los IDs no se reutilizan: el siguiente es el mayor que haya habido más uno (`decisiones.md` guarda los ya
  respondidos).
- Antes de una entrega, lo que siga aquí es lo que se lleva a la próxima reunión; en la entrega final, el fichero
  queda vacío.
