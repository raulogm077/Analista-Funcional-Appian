# Plan: el DF del cliente sobre una plantilla universal

Fecha: 16 de octubre de 2026. Parte de `main` (`2f9151d`, 0.8.0-beta.1). Rama `yaroslav/plantilla-DF-cliente`. Registro
de cada cambio, para adjuntar al PR: `docs/plan/2026-10-16-plantilla-df-cliente-registro.md`.

**Objetivo.** Que `appian-functional-analyst` entregue, además del análisis funcional, el **DF del cliente**: el
documento que el cliente revisa y valida, con la estructura de la plantilla de Word que ya usa el equipo (sale del
PowerPoint de revisión de requisitos), sin la marca de ningún cliente. Cada sección lleva su descripción y su tono, y
las pantallas se describen con una guía de requerimientos universal que pasa a formar parte del plugin.

**Cómo se trabaja.** Como piden `CLAUDE.md` y `.github/CONTRIBUTING.md`: solo en esta rama, sin tocar la versión, la
rama se sube como copia de seguridad cuando convenga y el PR se abre al terminar, con auto-merge, y entra con la
aprobación de Raúl. Antes de cada commit, `comprobar_plugin.py`; si cambia un script o una plantilla, el selftest de la
skill. Las pruebas se hacen con el plugin cargado desde esta carpeta (`claude --plugin-dir`) en un proyecto fuera del
repositorio.

**Material de partida (fuera del repositorio).**
- La plantilla de Word del equipo, con la marca de un cliente: portada, control de cambios, 1. Introducción (descripción,
  integraciones, alcance), 2. Diseño de la solución (flujo y reglas comunes, ficha de 10 campos por actividad, pantallas,
  roles y matriz de permisos, notificaciones, métricas y KPIs).
- El PowerPoint con ejemplos reales del tono de varias secciones (reglas comunes, actividades, roles, matriz,
  notificaciones). Tiene datos del cliente: **no entra en el repositorio**; de él solo salen ejemplos reescritos con un
  caso ficticio.
- La skill suelta `requerimientos-pantallas` (Lógica General, Filtros, Ordenación, Reglas de Validación), hoy fuera del
  plugin y con un ejemplo de un proyecto concreto.
- Un primer intento ya hecho sobre la 0.7.0-beta.4 en el plugin «appian-analyst-plantilla-actualizada» (instalado en la
  cuenta, no en el repositorio): `assets/plantillas/df-cliente.docx` (la misma plantilla sin logos),
  `assets/plantillas/df-cliente.md`, `references/df-cliente-plantilla.md`, `references/requerimientos-pantallas.md` y
  `scripts/df_cliente_docx.py` (906 líneas, python-docx). Se parte de él en vez de empezar de cero.

## 1. Decisiones

Confirmadas por Yaroslav el 16 de octubre de 2026, salvo las marcadas «propuesta».

- **D0. Se parte de la variante, pero como borrador.** Se aprovecha lo que sirva de la 0.7.0-beta.4, revisado con lo
  de este plan; la base es siempre la última versión del plugin (`main`), no la variante.
- **D1. El DF del cliente es un documento propio, escrito desde las fuentes.** No se deriva del análisis funcional
  (`analisis/funcional.md`) ni hay una tabla que ate sus secciones a las del funcional. Se escribe analizando una a una
  las fuentes del proyecto (transcripciones, correos, documentos, capturas, diagramas y lo que se pase como contexto).
  Si el proyecto ya tiene funcional, es una fuente más, no el origen. Vive en `analisis/df-cliente.md`.
- **D1b. El DF solo lleva lo que lee el cliente** (Yaroslav, 16/10). Ni fuentes ni preguntas abiertas, tampoco en
  comentarios escondidos: de dónde sale cada bloque va en `analisis/df-cliente-fuentes.md` y lo pendiente, en
  `analisis/df-cliente-pendientes.md`, del que cada respuesta quita su fila. En la entrega final no queda ninguno.
- **D2. Trabajo iterativo: la última fuente manda.** Cada fuente nueva se lee contra el DF tal como está y, si
  contradice lo que se acordó antes (también lo aceptado en la reunión anterior), se reescribe con la decisión nueva.
  Nada se cambia en silencio: cada cambio dice qué fuente lo trae y qué decisión anterior sustituye, y la entrega
  siguiente lo recoge en el control de cambios. Se apoya en lo que el plugin ya hace con las fuentes (`leer_fuentes.py`,
  notas, informe de impacto, `decisiones.md`).
- **D3. La plantilla neutra es la del equipo sin marca**: sin logos, con colores neutros y textos de ejemplo
  genéricos, y con el apartado **2.6 Periodo de estabilización**, que la plantilla de Word aún no tiene. La de un
  cliente vive en su proyecto (`<p>/plantillas/df-cliente.docx`), nunca en el plugin.
- **D4. La guía de pantallas va dentro de la skill del analista** (`references/requerimientos-pantallas.md`), que es la
  que escribe el DF. La usan el apartado 2.3 y el modo «Pantalla suelta». La skill suelta se retira cuando esto esté en
  `main`.
- **D5. El Word se genera con Python** (`df_cliente_docx.py`, python-docx), porque rellena la plantilla en vez de
  dibujarla desde cero. python-docx entra en `requisitos.json`. (Propuesta.)
- **D6. Antes del PR, pruebas con casos reales** que pasa Yaroslav (transcripciones de un proyecto), fuera del
  repositorio: se prueba, se revisa el resultado, se corrige el plugin y se repite hasta que el DF salga bien. Al
  repositorio solo llegan los cambios del plugin y las lecciones, sin datos del cliente.

## 2. Tareas

### Fase 0 · Preparación

- [x] **T0. Equipo y punto de partida.** Python (aquí solo existe `py`: ver «Aprendizajes»), python-docx, Node y
  LibreOffice; `comprobar_plugin.py` y el selftest del analista en verde antes de tocar nada. Comparar la variante con
  la 0.8.0-beta.1 fichero a fichero y decidir qué se trae y qué se rehace.

### Fase 1 · Plantilla universal

- [ ] **T1. `assets/plantillas/df-cliente.docx` neutro** (hecho; Yaroslav lo revisa abriéndolo en Word: sin PDF, decidido el 16/10), a partir de la plantilla del equipo: sin las tres imágenes de
  marca, colores y tipos de letra neutros, encabezado y pie genéricos, textos de ejemplo entre corchetes que el script
  reconoce. Comprobar que no queda nada de ningún cliente (`pruebas/clientes.txt`, también dentro del `.docx`).
- [ ] **T2. Plantilla de un cliente.** Cómo se crea en un proyecto (copia de la neutra cambiando solo logos, colores,
  letra y pie) y que el script la usa si existe; si no, la neutra con el color de `prototipo/brand-<id>.json`.
- [x] **T3. Añadir «2.6 Periodo de estabilización»** a la plantilla neutra, con el texto que usa el equipo: «Teniendo en
  cuenta que se trata de un proceso **[anual / mensual / diario…]** se establece un **período de estabilización de [X]
  meses**.» La periodicidad y los meses salen de las fuentes; si no lo dicen, «pendiente de confirmar».

### Fase 2 · El DF del cliente como entregable

- [x] **T4. `references/df-cliente-plantilla.md`**: para cada sección, qué es, para qué la lee el cliente, qué se
  escribe, de qué tipo de fuente suele salir y el formato exacto que lee el script, con un caso ficticio.
- [x] **T5. `assets/plantillas/df-cliente.md`**: el esqueleto que copia `proyecto.py iniciar`.
- [x] **T6. Del material al DF.** Cómo se construye el DF desde cero con todas las fuentes: leerlas todas antes de
  escribir, en orden de fecha; qué sale de cada tipo (una transcripción, un correo, un documento del cliente, una
  captura, un diagrama, un funcional que ya exista) y qué se pregunta en vez de inventarse.
- [x] **T7. Iteración: una fuente nueva sobre un DF que ya existe.** La fuente se lee contra el DF; lo que cambia se
  reescribe con la decisión nueva, aunque se hubiera aceptado antes; el informe de impacto dice qué cambia, de qué
  fuente sale y qué sustituye; la entrega siguiente sube la versión y añade su fila al control de cambios. Reutiliza
  `actualizacion.md` donde encaje, sin atar el DF al funcional.
- [ ] **T8. `SKILL.md` del analista**: el DF del cliente en «Qué escribe», en los modos, en los pasos y en la tabla de
  referencias; los flujos que lo nombran; `proyecto.py` (iniciar, estado, entregar) y `comprobar.py` si tienen que
  conocerlo.

### Fase 3 · Tono y descripción de cada sección

- [ ] **T9. Guía de tono por sección**, a partir de los ejemplos del PowerPoint reescritos con un caso ficticio: regla
  común (título en mayúsculas, cuándo aplica, qué pasa, excepciones), ficha de actividad (entrada y salida con sus IDs,
  estados por acción «Acción "X" → Estado / Subestado», «N/A» cuando no aplica), roles («Dónde se define»), matriz
  (agrupada por pantalla o sección, con notas con asterisco) y notificaciones (asunto con variables, cuerpo literal).
- [ ] **T10. Revisar la guía con Yaroslav** con una sección de cada tipo escrita con ella.

### Fase 4 · Descripción de pantallas universal

- [ ] **T11. Revisar las instrucciones generales** de la skill suelta y de la variante: qué sirve, qué sobra y qué está
  pensado para un proyecto concreto.
- [ ] **T12. `references/requerimientos-pantallas.md`**, dentro de la skill del analista. Tiene que decir de forma
  explícita:
  - que **cada funcionalidad de la pantalla se describe, sin saltarse ninguna**: cada campo, columna, botón de cabecera
    y de fila, enlace, icono, pestaña, filtro, orden, tooltip, mensaje, estado vacío y modal que se abre; lo que se ve en
    la captura o el prototipo y nadie explicó también se describe o se pregunta;
  - **el formato**: los apartados de la plantilla en su orden («Ejemplo ilustrativo», «Lógica General», «Búsqueda y
    Filtros», «Ordenación», «Reglas de Validación»), lista numerada con sub-viñetas, una idea por punto;
  - **cómo se describe** cada tipo de elemento (qué es, tipo de control, de dónde sale el valor, valores y por defecto,
    qué pasa al pulsarlo o cambiarlo, qué se ve si está vacío), con un ejemplo ficticio completo en vez del de un
    proyecto real;
  - una **lista de repaso** final para comprobar que no falta nada.
- [ ] **T13. Lo que se añade o cambia respecto a la skill suelta.** Sale de un DF real de Yaroslav que usó la skill y
  corrigió a mano (fuera del repositorio; aquí solo los patrones):
  - **Fuera lo que no aplica**: la skill suelta da por hecho que alguien explica la pantalla de viva voz («tu voz =
    verdad»). Aquí la explicación puede venir de una transcripción, un correo, un documento o el chat; manda la fuente
    más reciente, y la captura completa lo que nadie dijo.
  - **Cada columna o campo**: nombre (las columnas de una tabla, en mayúsculas), qué representa, de dónde sale su valor
    (elegido al crear, calculado, de datos maestros, heredado de otro registro), formato entre paréntesis
    («(DD/MM/AAAA)», «(nombre y apellidos)»), qué se ve si está vacío («-») y qué pasa al pulsarlo (vínculo al registro,
    descarga, copiar).
  - **Cada filtro**: tipo y selección única o múltiple, de dónde salen las opciones y en qué orden, valor por defecto
    («Todos»), qué muestra la tabla al seleccionar, la regla de «Todos» frente al resto, si se bloquea cuando solo hay
    una opción, cómo se combinan y qué se ve sin resultados. La búsqueda: sobre qué campos (también los que no son
    columna), coincidencia parcial o exacta, mayúsculas.
  - **Ordenación por columna**, con su criterio (A-Z, fechas, números, proporciones) y cómo se trata el «-»; el orden
    por defecto; que reordenar mantiene filtros y búsqueda; si ordena dentro de cada agrupación.
  - **Cada validación de un campo de formulario**: obligatorio, longitud máxima, caracteres permitidos y, para cada
    incumplimiento, su mensaje literal; al final, qué pasa si algo falla al guardar.
  - **Botones con efecto y después**: Cancelar, la «X» y el botón principal, con lo que pasa tras guardar (se cierra,
    se abre el registro nuevo, en qué estado queda); estados de un botón (inicial, en curso con indicador, disponible);
    confirmaciones con su texto literal y sus botones, y variantes por caso.
  - **Pantallas agrupadas por área** (lo que en el proyecto serían épicas): el 2.3 se parte en `2.3.n Pantallas
    <área>` según las áreas de cada proyecto, y dentro van sus pantallas y modales. Los patrones de abajo son un
    catálogo para cuando un tipo de pantalla aparece, no una lista de pantallas que tenga que haber.
  - **Pantallas compuestas**: un registro con cabecera (chips de estado, botones de flujo, iconos de alertas, línea de
    progreso), tarjetas, banner de estado y secciones desplegables (cuál se abre por defecto); un cuadro de mando con
    secciones, tarjetas de cifras y gráficos (tipo, ejes, colores por valor, tooltip, valores a cero); un modal con
    secciones desplegables o bloques que se repiten («Añadir…»). Cada parte se describe con su nombre, en orden.
  - **Un modal que cambia según desde dónde se abre** (precargado y bloqueado desde otro registro): cada variante como un
    caso, con lo que se precarga, lo que se puede editar y qué pasa al cancelar.
  - **Exportaciones**: qué contiene el fichero (hojas, columnas, una fila por qué), qué filtros respeta y qué no.
  - **Componentes comunes** que ya existen en otras aplicaciones del cliente (una bandeja de tareas, una tabla con
    «Limpiar» y «Guardar»): se nombran y se dice que no se redefinen.
  - **Referencias por nombre, nunca por número**: «(se describe en la pantalla "Nuevo expediente")», porque los números
    cambian al reordenar el documento. Nunca «en la siguiente diapositiva».
  - **Visibilidad por rol: solo en Roles y Permisos (2.4.1).** Es la única fuente: quién ve una pantalla, una sección o
    un botón se escribe allí y se cambia allí, sin tocar las pantallas. Las pantallas describen todo lo que existe y no
    dicen quién lo ve (la nota fija de la plantilla lo recuerda). Decidido por Yaroslav el 16/10.
  - **«Búsqueda y Filtros» si hay buscador, «Filtros» si no.** Decidido por Yaroslav el 16/10.
- [ ] **T14. Modo «Pantalla suelta»** con esta guía: la ficha en el formato del 2.3, en el chat y, si hay proyecto, en
  el DF del cliente.

### Fase 5 · El Word

- [ ] **T15. `scripts/df_cliente_docx.py`** traído de la variante y puesto al día con `main`: lee `df-cliente.md`,
  rellena la plantilla (con el 2.6), no enseña comentarios ni lo tachado, resalta «pendiente de confirmar», avisa de
  textos de ejemplo sin rellenar y de pantallas sin Lógica General; no sobrescribe un Word entregado; PDF con
  LibreOffice.
- [ ] **T16. Selftest** en `pruebas/appian-functional-analyst/` con un proyecto ficticio: genera el Word y comprueba
  secciones, fichas, matriz, notificaciones y avisos.

### Fase 6 · Probar con casos reales e iterar

Fuera del repositorio, con el plugin cargado desde esta carpeta (`claude --plugin-dir`). Cada vuelta, una fila en el
registro y las lecciones en «Aprendizajes».

- [ ] **T17. Primera pasada**: con las transcripciones y artefactos que pase Yaroslav de un proyecto, el DF del cliente
  desde cero y en Word. Revisar el PDF juntos: qué falta, qué sobra, qué está mal contado, qué pantalla no está entera.
- [ ] **T18. Iteración**: pasar las fuentes una a una, como llegarían en el proyecto, y comprobar que cada una reescribe
  lo que cambia (también lo aceptado antes) y que el control de cambios lo recoge.
- [ ] **T19. Corregir y repetir**: cada fallo se corrige en el plugin y se vuelve a probar hasta que Yaroslav dé el DF
  por bueno. Lo que no entre en este trabajo, a `siguiente-version.md`; lo aplicado, a `evaluaciones.md`, sin datos del
  cliente.

### Fase 7 · Cerrar

- [ ] **T20.** `comprobar_plugin.py`, selftests, registro completo, la rama subida y el PR con auto-merge; su
  descripción sale del registro.

## Abierto

- Ninguno. (El índice se queda en tres niveles, con las áreas y sin cada pantalla: puede haber muchas. Decidido por
  Yaroslav el 16/10.)

**Resultado de T0 (16/10).** `comprobar_plugin.py` y el selftest del analista, en verde (el selftest no prueba el
Word: falta el paquete docx de Node). python-docx 1.2.0, sí; LibreOffice, no. La variante ata el DF del cliente al
funcional (mismos ACT y PAN, avisos si no casan, tabla de correspondencia), justo lo que D1 descarta. Se aprovechan su
plantilla sin marca (ya con azul en vez del verde del cliente, sin los tres logos y sin autor en los metadatos), la
mecánica de su generador y el esqueleto de su guía de pantallas; `df-cliente-plantilla.md` y los cambios de
`SKILL.md` se rehacen.

**Resultado de T1 y T3 (16/10).** Sobre la plantilla de la variante: el 2.3 por áreas (`2.3.n PANTALLAS [ÁREA]`, en
«heading 30») con cada pantalla en un estilo nuevo «heading 40» (`2.3.n.m [Nombre de la pantalla]`, nivel 4 del
índice: el campo del índice es `\o "1-3"`, así que no sale en él, ver «Abierto»); las referencias «(se describe en la
pantalla [N])» pasan a «(se describe en la pantalla "[Nombre de la pantalla]")»; y el 2.6 al final. Revisado: ningún
término de `pruebas/clientes.txt` ni de la consultora dentro del `.docx`, sin imágenes.

## 3. Aprendizajes

Lo que se aprende mientras se trabaja. Lo que pide un cambio en el plugin que no entra en este trabajo pasa a
`docs/siguiente-version.md`; lo aplicado, a `docs/evaluaciones.md`. Sin datos del cliente.

- (16/10) En este Windows no existen `python` ni `python3`, solo el lanzador `py`. El SKILL.md dice «en Windows,
  `python` en vez de `python3`» y `CLAUDE.md` usa `python3`: aquí fallan los dos. → `siguiente-version.md`.
- (16/10) Ya había un primer intento de este trabajo en un plugin aparte (0.7.0-beta.4) que no llegó al repositorio.
  Lo que se hace fuera del repositorio se pierde o se duplica: es lo que el `CLAUDE.md` quiere evitar.
- (16/10) Un DF real de muchas pantallas muestra que la skill suelta se queda corta en pantallas compuestas (registro,
  cuadro de mando, modal con secciones) y en validaciones de formulario (un mensaje por incumplimiento), y que da por
  hecha una explicación de viva voz que en un proyecto casi nunca existe. → T13.
- (16/10) Las correcciones a mano de un DF entregado son la mejor fuente para afinar la guía: dicen qué echó en falta
  quien lo revisó.
- (16/10) En un Windows corporativo, PowerShell puede estar en modo de lenguaje restringido: no deja usar Word por COM
  para sacar un PDF. Sin LibreOffice no hay forma de ver el DF como queda. El plugin ya lo trata como opcional («se
  revisa a mano»), y así se queda (ver el aprendizaje siguiente).
- (16/10) El PDF no es un entregable: solo servía para ver el Word sin abrirlo. Quien revisa el DF lo abre en Word. No
  hace falta instalar LibreOffice para trabajar el DF del cliente.
- (16/10) `proyecto.py copia` y `version` cuentan con que el proyecto tiene `funcional.md`: un proyecto que solo lleva
  el DF del cliente no puede usarlos hoy. → T8.
- (16/10) Las citas escondidas en comentarios del Markdown no salen en el Word, pero quien lee el `.md` las ve como
  ruido: si un documento es para el cliente, su trazabilidad va en un fichero aparte.
- (16/10) Al repasar la guía contra el DF real faltaban: el objetivo, los actores y las tecnologías en 1.1; partir un
  flujo grande en fases; una descripción de la solución por áreas antes de las pantallas, un área de pantallas
  comunes y las herramientas de configuración como área; los roles que se dan al asignar algo.
