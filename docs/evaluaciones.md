# Evaluaciones y cierre de fases

Resultados de las evaluaciones de los planes de `docs/plan/` y, al cerrar cada
fase, el resumen de cambios, lo aprendido y lo que queda aplazado, con la tarea que lo recoge. Los proyectos de prueba
están en `$PROYECTOS_PRUEBA`, fuera del repositorio; aquí solo los resultados.

## Método L.U.C.I.A. (14 de octubre de 2026)

Rama `metodo-lucia`, de `main` d6126a8 (0.7.0-beta.4). Plan: `docs/plan/2026-10-14-metodo-lucia.md`. Las pruebas con
reuniones reales y con el entorno de desarrollo se hacen fuera del repositorio; aquí, solo las cifras y las lecciones.

### Fase 7 · T17, T18 y las medidas con el plugin terminado

**T18.** `cambios.md` §6 y `urgentes.md`: quien prepara el paquete revisa en Compare and Deploy la comparación de sus
objetos, como en un Merge Request, con los fallos de la regresión, los de los guiones de QA y las pruebas marcadas como no
necesarias (la línea nombra los tres ficheros); se promueve el mismo paquete con un ICF por entorno y, si el despliegue es
directo o por API, con «Require review» activado en el destino; `produccion --ref` lleva la referencia del pase. Sin script
nuevo. De paso, `urgentes.md` pide ya «Dónde se corrige» también en una urgencia de datos u operación, como exigía
`proyecto.py`.

**T17, primera medida** (copia fija del commit `85d801e`; el retoque de T6 con el proyecto puesto al día: repositorio git,
«Para» en §13, la acción en la tabla de §7 y la unidad aprobada de nuevo para que salgan sus issues):

| | T6 | T17 (media de 3) |
|---|---|---|
| Minutos | 2,9 | 4,7 |
| Llamadas | 54 | 38 |
| Contexto máximo | 217.215 | 140.785 |
| Coste (USD) | 2,51 | 1,92 |

Leen la issue y el flujo, y del técnico solo el entorno (antes, entero); no ejecutan casos de prueba ni SAIL CLI;
`verificar` comprueba el nombre de la acción (sin renombrarla, `construida` se niega). Una cuarta pasada no vale: leyó un
fichero de la prueba que decía dónde estaba el texto. **El criterio se cumple en llamadas y coste, no en minutos**: las tres
sesiones buscaron el plugin en el disco, porque `AGENTS.md`, el flujo y la issue nombraban los scripts sin ruta (son del
proyecto y se comparten entre equipos), y una se quedó colgada tres minutos en una búsqueda por todo el disco.

**El caso de T1 con el plugin terminado** (misma base, encargo y memoria que T1, T3 y T3b):

| | T1 | T3 | T3b | Final |
|---|---|---|---|---|
| Minutos | 18,6 | 16,0 | 19,4 | 16,8 |
| Llamadas | 124 | 155 | 135 | 87 |
| Coste (USD) | 6,73 | 6,64 | 5,61 | 6,84 |

Las fases 3 a 6 no lo encarecen en tiempo. Los siete criterios nuevos o cambiados salieron en Gherkin y `comprobar.py` no
tuvo que avisar; el orden análisis, comprobación, prototipo y Word se mantiene; recoge los 15 puntos de la reunión. El
coste sube porque hizo más mensajes con una orden cada uno, con otra versión de Claude Code (2.1.299 frente a 2.1.296): no
se puede atribuir al plugin. Salieron dos fallos: los avisos de «texto que queda viejo» pasaron de 4 a 7 por sesión a 21,
porque los criterios en Gherkin empiezan igual y se señalaban entre sí, y nadie los atendía; y el aviso de `estado` de que
el proyecto no está en git se trató como información, así que un proyecto que ya existe nunca pasaría a git.

**El retoque de análisis a ciegas** con el plugin terminado (`pruebas/evaluaciones/coste-retoque`): 22, 20 y 22 llamadas,
ninguna pasada de `comprobar.py` con errores y 6/6 las tres (la ronda anterior, 22, 20 y 18). **El criterio de las 25
llamadas se cumple** y lo nuevo (git, `AGENTS.md`, Gherkin, «Para», issues) no añade llamadas. Lo que sobra son cosas del
equipo donde se mide y dos llamadas recurrentes para saber en qué línea va la fila de §13.

**Revisión final de toda la rama**, independiente: recorrió como un equipo nuevo un proyecto nuevo, una reunión corta, un
evolutivo hasta producción, una urgencia y un retoque; todas las órdenes coinciden con su ayuda real, todo lo que bloquea
es uno de los dos bloqueos de B3 o su consecuencia directa y ninguno se queda sin salida, y el paquete (192 ficheros) no
lleva nada de desarrollo ni datos de nadie. Encontró tres fallos: la barrera de `qa.py` contra pruebas y producción tenía
fugas; la urgencia no tenía regresión; y el fichero de la regresión no tenía dueño. Y repeticiones: la regla «un fallo deja
la issue pendiente salvo que una persona lo marque» estaba escrita en ocho sitios, y el `AGENTS.md` generado había vuelto a
38 líneas.

**Ajustes finales**, de esas medidas y de la revisión: el aviso de texto viejo compara paso a paso en un criterio en
Gherkin (el arranque común ya no avisa; el criterio viejo escrito en otro sitio sí); `estado` dice «lanza `proyecto.py
iniciar`» y el método lo manda; `AGENTS.md`, las copias de los flujos y cada issue dicen que las órdenes salen de la skill
nombrada y que no se busca el plugin en el disco; `qa.py` solo repite contra desarrollo o el entorno de corrección (lista
blanca); la regresión de una urgencia va contra el entorno de corrección; cada regla en un solo sitio; `AGENTS.md` en 30
líneas. Pruebas con todo unido: `comprobar_plugin.py`, 0 errores; los cinco selftest; las ocho evaluaciones de
`pruebas/evaluaciones/`; ingeniería inversa, 193 pasan y 2 se saltan.

### Fase 5 · T10 a T14: issues por requisito y pruebas de la issue

Qué cambia:
- **T10.** Técnico §13 gana la columna «Para» (el requisito de cada objeto, o «Base»); `comprobar.py` avisa del objeto sin
  ella, una sola vez en un técnico antiguo. La plantilla dice además, en un solo sitio cada cosa: cada acción que lanza un
  proceso es una acción de registro (de lista o relacionada) de un record type, nunca un enlace de proceso; la URL de cada
  entorno en §0; y cómo se comprueba cada criterio en §14.
- **T11.** `indice.py issues` sustituye al encargo, que desaparece. Las issues se generan al aprobar la unidad, una por
  requisito (juntas las que comparten pantalla o proceso, lo común en la Base), con el extracto del técnico y del
  prototipo, sus escenarios y su `.feature`. `--siguiente` da la próxima, la reserva con una línea en el índice de la
  unidad (commit y push) e imprime la orden de terminar con las rutas y el servidor del equipo. `construida` pide todas
  las issues hechas.
- **T12** (decisión de Raúl): `LCP_TOOL_MODE` no hace nada en el Dev MCP 26.6.110 y se dejó de afirmar lo contrario en
  ingeniería inversa. Fuera de desarrollo, una cuenta que solo ve la aplicación, la misma por entorno: el Dev MCP rechaza
  con 403 a una cuenta que no es diseñadora, y una diseñadora que solo ve la aplicación no cambia lo que existe, pero puede
  crear objetos nuevos (según la documentación; sin probar). SAIL CLI, solo en desarrollo.
- **T13.** `verificar` ejecuta los casos de prueba de las reglas e interfaces de la issue y de lo que las usa, reconociendo
  las herramientas por su firma, y deja el detalle en su fichero. Bloquea un fallo propio, salvo que una persona lo marque
  con `--sin-prueba` y motivo (se niega en una sesión desatendida y caduca si cambian la issue o el fallo); un fallo en lo
  que la usa es un aviso; la rejilla que el ejecutor no evalúa es «no evaluable». Comprueba nombre y tipo de las acciones
  de registro. La regresión de toda la aplicación la pasa un script antes del paquete.
- **T14.** Al aprobar una unidad que cambia datos, seguridad, integraciones o procesos en curso, o que usa IA, y en su
  issue: «que una persona revise DT-nn antes de construir». Aviso, no puerta.
- Un retoque solo se libra de la DT si renombra una acción, vista o filtro de un record type y su fila del técnico no
  cambia nada más; si cambia quién la ve, pide «Permisos».

Prueba real, en solo lectura, contra la aplicación ficticia del entorno de desarrollo:

| Orden | Tiempo | Por pantalla | Casos |
|---|---|---|---|
| `verificar` de la unidad del retoque (regla con dependientes, panel y acción) | 11 s | 425 bytes | 40: 39 pasan, 1 no evaluable |
| `regresion` de la aplicación | 12 s | 250 bytes | 75: 74 pasan, 1 no evaluable |

El registro del Dev MCP, que en T6 llegaba a 331 KB, ya no sale. Una acción renombrada a mano sale como diferencia. En el
retoque de T6, la issue ocupa 2,2 KB (el técnico, 16 KB) y dice que no hay pruebas que ejecutar.

Tres revisiones independientes (una de cada mitad y otra de la fase entera) encontraron, y quedó corregido:
- Parte del técnico no llegaba a ninguna issue mientras la issue decía que no hacía falta leerlo: primero 21 de 67 líneas
  del proyecto de prueba, y después la matriz de seguridad, que no nombra objetos. Lo que no cae en ninguna issue va a la
  Base y el analista recibe el aviso.
- La reserva deshacía una fusión de git a medias, subía commits ajenos si el proyecto estaba dentro de otro repositorio y
  daba a una sesión reiniciada, o a dos sesiones del mismo usuario, una issue que no era suya.
- La regla de «retoque en una parte» dejaba pasar cambios de datos y de permisos, y saltaba la decisión de orden entre dos
  unidades sobre el mismo record type.
- `construida --manual --desatendida` se saltaba el bloqueo de las pruebas; y unos casos que no se pudieron ejecutar
  bloqueaban sin salida (ahora esperan a la regresión, con aviso).

Comprobado: mismas issues byte a byte con los mismos datos, en carpetas distintas; cada issue conserva su número al
cambiar el análisis; en 15 rondas con dos o tres agentes a la vez, ninguno se llevó la misma issue.

Lo que no se cumple tal cual: «fuera de desarrollo, el Dev MCP no ofrece herramientas que escriban» (decisión de Raúl:
sin maquinaria; queda la cuenta que solo ve la aplicación). «Una regla que rompe otra que la usa se detecta» está probado
con el simulador: en solo lectura no se puede provocar; lo prueba T16 con un defecto sembrado.

### Fase 6 · T15: la skill appian-qa

`skills/appian-qa/`: QA de una unidad completa, en otra sesión, solo con sus `.feature`. Por escenario, el «dado» como un
usuario, el «cuando» con la cuenta de su rol y su `--data-dir`, y el «entonces» en el `--json` de SAIL CLI. Cada recorrido
queda como guion en `qa/<U>/` y `qa.py` los repite sin IA antes del paquete; un fallo devuelve su issue a pendiente y se
puede marcar como no necesario con `--sin-prueba` y motivo, como un caso de prueba. La sesión de cada rol se busca en el
equipo de quien repite, sin fichero por proyecto y sin que el script vea contraseñas. No repite contra pruebas ni
producción. En un retoque cosmético, nada.

Prueba real con la aplicación ficticia y tres cuentas locales por rol: tres escenarios recorridos y escritos como guion en
1, 1 y 0,5 minutos; repetirlos sin IA, 15 segundos la unidad entera, dos veces con el mismo resultado; un fallo provocado
falla donde debe. Para que el guion sea estable hizo falta no fijar los números que da Appian (se comparan por el
principio), marcar las filas por su contenido y tener en cuenta que una rejilla vacía no trae filas y que lo buscado se
queda en la caja de búsqueda.

La revisión independiente encontró, y quedó corregido: la unidad podía quedar Construida sin QA (ahora la última issue lo
dice y `construida` avisa); un guion podía dar «pasa» sin afirmar nada; nada impedía repetirlo contra producción; y un
código de salida tapaba un fallo. Las sesiones de cuentas locales se cierran al terminar la campaña de QA y la importada
del Dev MCP no se cierra: cerrarla podría dejar sin acceso al Dev MCP.

Pruebas, con la Fase 5 y T15 unidas: `comprobar_plugin.py`, 7 skills y 0 errores; selftest del analista (382), de
`appian-qa` (48), de prototipos y de diagramas, correctos; los siete `prueba_puntuar.py`; ingeniería inversa, 193 pasan y
2 se saltan.

### Fase 1 · T1: el caso de «Agilidad» con la 0.7.0-beta.4

Una sesión nueva, con el plugin cargado desde una carpeta (`claude --plugin-dir`), incorpora una reunión de 2.467 palabras
a un análisis con prototipo y DF enviado, retoca el prototipo y saca el DF nuevo. El análisis de partida lo montó otra
sesión con tres reuniones del mismo proyecto (56 minutos, 142 llamadas). **18,6 minutos activos frente a los 70 de la
0.6.0-beta.1**: 124 llamadas (100 de la IA y 24 de script), un turno sin aprobaciones y 6,73 USD. No es el mismo caso
(otro proyecto, sin persona delante, una sola ejecución): la referencia para T3 son estos 18,6 minutos.

| Paso | Min | Llamadas | Qué leyó | Quién lo hizo → quién debería |
|---|---|---|---|---|
| Método | 1,5 | 9 | 5 referencias enteras, 778 líneas | IA lee el fichero → por partes |
| Fuente | 0,2 | 6 | entera, 49 líneas | script e IA |
| Encajar | 3,9 | 18 | 216 de 1.995 líneas; 13 consultas de `indice.py` | script e IA |
| Nota | 0,5 | 1 | — | IA |
| Informe de impacto | 1,0 | 5 | — | IA, dos veces → una |
| Versión, aplicar, diagrama, comprobar | 4,3 | 23 | 17 líneas | IA y script |
| Prototipo: leer | 1,1 | 6 | el script del proyecto entero, 665 líneas | IA → por partes |
| Prototipo: editar | 3,1 | 25 | — | IA |
| Generar, capturar, revisar | 1,1 | 10 | 6 capturas | script e IA |
| Enlazar capturas | 0,2 | 3 | — | IA → script |
| Word y PDF | 0,7 | 2 | — | script; el PDF, IA → script |
| Revisar páginas | 0,5 | 10 | 6 páginas | IA |
| Cierre | 0,3 | 6 | — | IA y script |

Los cuatro puntos de «Agilidad» (`docs/siguiente-version.md`), con la versión actual:
1. Guía de diseño y código en un retoque de prototipo: ya no pasa (0 líneas de `design-rules.md` y del kit). Queda que lee
   entero el script del proyecto y rehace 11 capturas para 3 pantallas afectadas: el método no dice cómo localizar una
   pantalla ni qué se lee en un retoque.
2. Funcional y técnico enteros: ya no pasa (233 de 1.995 líneas). Lo que se lee entero son las referencias del método,
   porque la tabla de referencias las manda sin distinguir una actualización.
3. Nota de la fuente: 747 palabras, 0,30 veces el original. El método sigue sin decir que es proporcional: 5 de sus 13
   apartados salieron casi vacíos.
4. El DF espera al prototipo: sigue pasando, 5,8 minutos (31 %). Lo manda `actualizacion.md` §7.

Fallos que salieron: el script del prototipo que escribe el agente lleva la ruta absoluta del plugin (no vale en un
proyecto compartido); `validate.py --anterior` exige `--confirmadas`; `df_docx.js --pdf` solo convierte con LibreOffice y,
sin él, la sesión sacó el PDF por su cuenta; y el hook de arranque prueba `python3` antes y deja un error en Windows.

`--plugin-dir`: la copia de la carpeta sustituye a la instalada o sincronizada con el mismo nombre (aparece como
`<nombre>@inline`; está documentado). La app de escritorio no tiene un equivalente documentado: para probar un cambio sin
instalarlo, la CLI.

### Fase 1 · T2 y T3: lo que se corrigió y lo que mide

T2 (sobre la 0.7.0-beta.4): el Word no espera al prototipo y se repite con las capturas; en un retoque de prototipo se lee
solo el tramo de cada pantalla del script del proyecto y el apartado de la guía que cambie; la tabla de referencias del
analista dice qué se lee por partes al incorporar una fuente; el informe de impacto se escribe una vez si nada requiere
aprobación; la nota es proporcional y sin apartados vacíos; `capture.py` enlaza cada captura en su ficha; sin LibreOffice
no se saca el PDF por otra vía y se dice a quien envía que el Word va sin revisar; el script del prototipo ya no lleva la
ruta del plugin; `validate.py --anterior` vale sin `--confirmadas`; el hook no deja el error de `python3` en Windows. Los
ficheros de instrucciones no crecen (analista `SKILL.md` 216 → 218 líneas; prototipos, 180 → 180).

T3 repite el caso de T1 con una copia del plugin que lleva solo T2; T3b, con T2 tras su revisión y dos ajustes que salieron
de T3. Mismo punto de partida, encargo, modelo y memoria; una ejecución de cada una.

| | T1 | T3 | T3b |
|---|---|---|---|
| Minutos activos | 18,6 | 16,0 | 19,4 |
| Llamadas | 124 | 155 | 135 |
| Líneas del método | 838 | 331 | 287 |
| Líneas del análisis | 427 | 1.105 | 413 |
| Líneas de código del plugin | 0 | 215 | 0 |
| Líneas del script del prototipo | 665 | 494 | 524 |
| Coste (USD) | 6,73 | 6,64 | 5,61 |

- **El criterio «T3 baja en minutos y llamadas frente a T1» no queda demostrado**: el total se mueve entre 16 y 19 minutos
  y entre 124 y 155 llamadas de una ejecución a otra, y eso es más que lo que T2 quita. Lo que queda del caso es tiempo
  del modelo pensando y editando.
- Se repite en las dos y es de T2: el método se lee en un tercio; el informe, de 5 llamadas a 2; el enlace de capturas, de
  3 a 1; el script del prototipo ya no se lee entero.
- **El Word no se adelantó en ninguna de las tres**: con todo pedido en un turno, nadie lee uno intermedio y la sesión se lo
  salta. Sin efecto medido; pendiente de que Raúl decida si se queda.
- Lo que T3 enseñó y se corrigió antes de T3b: al escribirse el informe «una vez, ya aplicado», la sesión lo dejó (con
  `comprobar.py`) para después del prototipo, que se retocó sobre un análisis sin comprobar. `actualizacion.md` §7 fija el
  orden en un solo sitio y en T3b se cumple (informe en el minuto 8,4, comprobación en el 9,1, prototipo después). Y sin la
  plantilla del funcional, la sesión buscó en el código de `comprobar.py` cómo se tacha una pregunta: la tabla de
  referencias cita ahora ese tramo.
- Calidad: las tres pasan `comprobar.py` y `validate.py` sin errores. Contrastadas con la reunión, las tres recogen sus 15
  puntos en la nota, en el informe y aplicados; T3b toca menos piezas (16 frente a 22 y 21) porque no repite un supuesto
  que ya estaba en una pregunta abierta. Un punto depende de una palabra mal transcrita y cada sesión lo trató distinto.
- Revisión independiente de T2: dos correcciones de texto antes de unir (el Word que sale antes podía entregarse con las
  capturas viejas y ya no se dejaba repetir; sin LibreOffice nadie sabía que iba sin revisar) y cuatro restos de lo
  anterior. El código nuevo, sin fallos.
- T4: `CLAUDE.md` lleva las preguntas del color y de la IA, dónde van las lecciones de cada prueba y cómo se prueba un
  cambio de una skill con `claude --plugin-dir`.

Pruebas, con T2 unida: `comprobar_plugin.py`, 0 errores; selftest del analista y de prototipos, correctos;
`coste-retoque/prueba_puntuar.py`, bien (el camino corto sigue en 16 llamadas). El retoque de análisis a ciegas (tope de
25 llamadas) se repite al final, con el plugin completo.

### Fase 3 · T7 y T8: flujos y un repositorio git por proyecto

Qué cambia:
- **Flujos F1 a F9** (`skills/appian-functional-analyst/assets/flujos/`): un fichero de 12 a 22 líneas por flujo, con
  cuándo se usa, los pasos, quién hace cada uno y con qué skill; citan la referencia de cada paso sin repetirla.
- **`proyecto.py iniciar`** deja el proyecto como repositorio git (rama `main`, sin primer commit ni repositorio dentro
  de otro), con `.gitignore`, `.gitattributes`, `AGENTS.md` (28 líneas, generado entero), `CLAUDE.md` con «@AGENTS.md» y
  `.agents/workflows/`. Si se vuelve a lanzar, pone al día `AGENTS.md` y los flujos y no toca lo demás; no pisa un
  `AGENTS.md` ajeno ni lo que generó una versión posterior del plugin.
- **`proyecto.py estado`** avisa de lo no confirmado, lo no subido, lo que falta traer, de `AGENTS.md` o flujos de otra
  versión y de un `CLAUDE.md` que no importa `AGENTS.md`. Nunca bloquea.
- **Los scripts escriben siempre con `
`** (50 escrituras en cuatro skills y `requisitos.py`), y `comprobar_plugin.py`
  comprueba que no vuelva a colarse: con proyectos compartidos entre Windows, macOS y Linux, cada reescritura en otro
  sistema cambiaba el fichero entero.

Revisión independiente, con proyectos creados fuera del repositorio: los tres criterios de la fase se cumplen y los siete
bordes probados (carpeta que ya es repositorio, dentro de otro, sin git, sin remoto, remoto que no contesta, ruta con
espacios y tildes, `iniciar` dos veces) no fallan. Encontró y quedó corregido:
- Con el `core.autocrlf` de Git para Windows, un clon cambiaba los finales de línea y las fuentes ya catalogadas se
  volvían a catalogar: de ahí el `.gitattributes`.
- «Se sube todo menos los secretos» no era cierto con ingeniería inversa: un valor encontrado queda en claro en varios
  documentos de `as-is/`. La regla y F6 dicen que, con hallazgos de seguridad con valores, el equipo decide antes de subir.
- Tres pasos de F4, F5 y F6 no decían lo que su referencia, y dos avisos de `estado` eran falsos (rama subida sin
  seguimiento; plugin anterior con un flujo retirado).
- `AGENTS.md` pasó de 50 líneas a 28: se carga en cada sesión del proyecto.

Coste de `estado`, que se ejecuta al empezar cada tarea: de 0,15 a 0,27 s sin repositorio, 0,52 s sin remoto y 1,41 s con
un remoto en GitHub (antes, 0,22 s); 5,5 s si el remoto no contesta. El intento de traer lo nuevo se queda: sin él, «va
por detrás» sería un dato viejo.

Pruebas, sobre la rama ya unida: `comprobar_plugin.py`, 0 errores; selftest del analista (290 comprobaciones), de
diagramas y de prototipos, correctos; ingeniería inversa, 173 pasan y 2 se saltan. Sin ejecutar en macOS ni Linux: lo
pasa GitHub en la PR.

### Fase 2 · T5: el Dev MCP y SAIL CLI reales

Mirados el 14 de octubre en el entorno de desarrollo, en solo lectura: Dev MCP 26.6.110 (build 20261008, el último
publicado) y SAIL CLI 26.6.110. Lo que cambia el plan lo confirmó un segundo agente por separado.

| Pregunta | Lo que hay |
|---|---|
| Casos de prueba | Se crean y se ejecutan en reglas e interfaces. La ejecución da, por caso, si pasa, la salida obtenida y el error con regla, función y línea; la salida esperada no viene (está en la definición del caso). Solo las reglas llevan aserción: una interfaz solo comprueba que no da error |
| En bloque | No. Se ejecutan los casos de un objeto por llamada. Una aplicación de 106 reglas y 32 interfaces (609 casos): 138 llamadas, 73 s y 1,5 MB de respuestas (unos 380.000 tokens si pasan por el contexto). Una regla de 6 casos, 1 KB; una interfaz de 7, 270 KB |
| Dependientes | Sí, solo los directos, con tipo y nombre; incluye siempre la propia aplicación |
| `LCP_TOOL_MODE=readonly` | **No hace nada en este bundle.** La documentación de Appian (26.6 y la vigente) la describe, pero la variable no está en su código: el servidor ofrece las mismas 200 herramientas con ella y sin ella, y 121 no son de lectura |
| Reconocer por la firma | `devmcp_extract.py` clasifica cada herramienta por su verbo, sus anotaciones y sus parámetros. Su `devmcp_policy.json` cuenta `run` como escritura: tal cual, deja fuera las de ejecutar casos, que el servidor anota como de solo lectura |
| SAIL CLI | La cuenta local entra con `SAIL_USERNAME` y `SAIL_PASSWORD`, sin teclado; cada sesión, en su `--data-dir`. `load --json` da cada componente con su `ref`: en dos cargas de la misma página coinciden 32 de 35 (cambian las que el propio JSON marca como propias de cada carga). Una `ref` que lleva un dato dentro («Pendientes (22)») no sirve para un guion. Los errores salen como texto aunque se pida JSON |

Lo que el plan daba por hecho y no es así:
- **T12.** `LCP_TOOL_MODE` no protege. Lo único que aplica el servidor son los permisos del usuario con el que se conecta, y
  solo sobre lo que ya existe: un diseñador puede crear objetos nuevos aunque solo vea la aplicación. Las anotaciones
  de las herramientas y las reglas de cada cliente (`permissions.deny` en Claude Code y sus equivalentes) son barreras
  contra el descuido. `SKILL.md`, `devmcp-setup.md` y `devmcp_extract.py` de ingeniería inversa recomiendan hoy la
  variable; la extracción es de solo lectura por su propia política, no por ella.
- **T13.** La regresión de toda la aplicación no se puede lanzar en bloque por el Dev MCP; lo nativo de Appian que lo hace
  es solo para reglas. Los casos de una issue los tiene que ejecutar un script, para que las respuestas no pasen por el
  contexto.

### Fase 2 · T6: línea base del retoque construido

El caso ficticio de `pruebas/evaluaciones/coste-retoque` («Nueva solicitud» pasa a «Pedir material»), construido de
verdad: la aplicación «Solicitudes de material» en una aplicación nueva del entorno de desarrollo (11 objetos del
técnico, tres cuentas locales por rol; 36 minutos y 105 llamadas al Dev MCP montarla). Tres sesiones a ciegas con una
copia fija de la 0.7.0-beta.4, el retoque ya aplicado en el análisis y la unidad aprobada, y un solo encargo: «La unidad
EV-03 está aprobada. Constrúyela en desarrollo y déjala como construida.» Las cifras salen de la transcripción de cada
sesión y coinciden con su evento de resultado.

| | Pasada 1 | Pasada 2 | Pasada 3 | Media |
|---|---|---|---|---|
| Minutos | 2,4 | 2,9 | 3,3 | **2,9** |
| Llamadas | 50 | 58 | 55 | **54** |
| Dev MCP: lectura / escritura / prueba | 9 / 1 / 1 | 9 / 1 / 1 | 13 / 1 / 1 | — |
| Tokens de salida | 11.662 | 14.130 | 16.450 | 14.081 |
| Contexto máximo | 233.110 | 209.472 | 209.062 | 217.215 |
| Coste (USD) | 2,63 | 2,27 | 2,63 | **2,51** |

Las tres dejan la acción renombrada, nada más tocado y la unidad Construida, sin preguntar. El cambio en sí (leer el
objeto y escribirlo) son 0,6 minutos y 0,31 USD; lo demás es carga fija:

| Paso | Min | Llamadas | USD | Quién lo hizo → quién debería |
|---|---|---|---|---|
| Arranque y estado | 0,3 | 5 | 0,11 | IA y script → script |
| Encargo | 0,1 | 3,3 | 0,06 | script lanzado por la IA → fichero ya generado |
| Skills y referencias | 0,5 | 14,7 | 1,01 | IA leyendo ficheros enteros → por partes |
| Leer el análisis | 0,0 | 4,7 | 0,14 | IA → fichero (el extracto, en el encargo) |
| Leer el objeto | 0,2 | 7 | 0,24 | IA |
| Escribirlo | 0,4 | 4,7 | 0,07 | IA, o una persona (B4) |
| Casos de prueba | 0,4 | 5,3 | 0,19 | IA → script; en un retoque, nada |
| `verificar` | 0,3 | 2,3 | 0,25 | script compuesto por la IA → script |
| Marcar construida | 0,1 | 1 | 0,02 | script |
| Contexto de arranque | — | — | 0,35 | fichero |

- La «hora por un cambio menor» de appian-harness no ha vuelto: son 3 minutos. La skill oficial es el 25 % del coste
  (0,63 USD; carga 2.480 líneas de media, no las 5.600 que se temían) y sube el contexto por encima de 200.000 tokens
  antes de tocar el entorno; las respuestas del Dev MCP, el 16 %.
- **B4 lo decide Raúl con estas cifras.** Lo mismo a mano en Designer no se ha medido.
- Dato aparte: con el texto del botón en la interfaz (un enlace de inicio de proceso, que es peor diseño y se rehízo como
  acción de registro), dos pasadas costaron 3,6 y 3,9 minutos y 2,72 y 2,40 USD.

Lo que falla hoy y tienen que quitar las issues de la Fase 5 (T17 lo vuelve a medir):
- El encargo no dice qué cambia («ver técnico §7»), así que la sesión lee el técnico; y no existe hasta que la sesión lo
  genera.
- La orden de `verificar` del encargo no se puede copiar: lleva `python3` y marcadores, y le falta el servidor (una pasada
  falló por eso). `verificar` vuelca de 78 a 331 KB de registro.
- **`verificar` no mira las acciones de registro:** sale igual con el cambio que sin él, y da por sobrantes los campos del
  record type. Ninguna sesión lo dice; las tres lo suplen releyendo la acción y mirando el botón con SAIL CLI.
- Las sesiones ejecutan casos de prueba y SAIL CLI sin que nadie lo pida, en un retoque que no cambia criterios ni reglas.
- Con el texto en un record type, el análisis pide una DT «Cambio sobre lo construido» y decidir el orden con la otra
  unidad, para un cambio de nombre; `comprobar.py` da un aviso que no procede.
- El técnico ficticio dice que el botón «abre el formulario de inicio» sin decir cómo: quien construyó eligió un enlace
  de proceso en vez de la acción de registro que pide buenas prácticas (00, 01 §9.2, 02 §5.4, 03 §8, 06 §5.3).
- Los casos de prueba de una interfaz con una rejilla de registros fallan siempre: el ejecutor no la evalúa.

### Fase 4 · T9: criterios en Gherkin de una línea

Qué cambia: `funcional-plantilla.md` §4 es el único sitio que dice cómo se escribe un criterio (dado, cuando y entonces,
con su ID; `redaccion.md` y `actualizacion.md` remiten a él); `comprobar.py --anterior` avisa del criterio nuevo o
cambiado en su texto que no tiene las tres partes; y `modelo.py` convierte los criterios de una historia en Gherkin
formal en español (`pasos_gherkin`, `Proyecto.feature`, `Proyecto.escenarios`), que T11 escribirá en cada issue. Sin
órdenes ni ficheros nuevos; los datos de prueba no se han reescrito.

Revisión independiente, con un proyecto ficticio fuera del repositorio:
- El criterio de la fase se cumple: un analizador oficial de Gherkin (`gherkin-official` 42) acepta todos los `.feature`
  que salen, también con finales de línea de Windows y caracteres no ASCII.
- El aviso no hace ruido: calla con los criterios viejos y cuando solo cambia la cita; un retoque que no toca criterios
  ve una línea «✓» más y `comprobar.py` tarda lo mismo (0,339 → 0,347 s de mediana en 20 pasadas).
- Encontró un fallo que las pruebas no veían: un criterio escrito en dos líneas perdía la segunda al pasar a Gherkin, sin
  avisar (el Word sí las unía). Corregido, con su caso.
- «Sin botones ni campos», la frase del diseño, se entendía mal en una validación («sin comentario»): la plantilla dice
  «sin pasos de pantalla (pulsar, rellenar); los datos, con el nombre que les da el cliente».

Pruebas: `comprobar_plugin.py`, 0 errores; `selftest.py` del analista, 261 comprobaciones (19 nuevas), también con
Python 3.9. En el Word, cada criterio pasa de unas 10 palabras a 19.

Aplazado: el aviso de «texto que queda viejo» señala criterios que empiezan igual (`docs/siguiente-version.md`).

## 0.7.0-beta.3 · Retoques ligeros y menores (11 de octubre de 2026)

Rama `v0.7.0-beta.3`, de `main` 222a8e6. Plan: `docs/plan/2026-10-11-0.7.0-beta.3.md`. Todas las evaluaciones, a ciegas
con una copia del paquete (`/home/claude/eval-plugin`), sin `pruebas/` ni `docs/`.

### Prueba de coste: texto de un botón construido (camino corto)

| Ronda | Método | Llamadas | Puntos |
|---|---|---|---|
| 0.7.0-beta.2 | Camino entero | 34, 34, 47 | 5/6 las tres (llamadas) |
| 1 | Camino corto con `proyecto.py version` | 27, 29, 30 | 5/6 las tres (llamadas) |
| 2 | Y `version --decision`, el informe de ejemplo, «Siguiente paso» sin tocar | 16, 19, 21 | **6/6 las tres** |
| 3 | Tras la revisión independiente (anexo, fila de §13) | 20, 27, 23 | 6/6, 5/6, 6/6 |
| 4 | El anexo solo si `comprobar.py` avisa; las dos órdenes de `ficha` e `impacto`, separadas | 22, 20, 18 | **6/6 las tres** |

- Ronda 1: las llamadas de más eran dudas que el camino corto no resolvía: leer otro informe como modelo, el formato del
  comentario con dos fuentes, buscar en la fuente la cita del «Antes», si se cambia el «Siguiente paso» (2-3 llamadas),
  y editar sin leer antes (la herramienta de edición lo pide: 4 llamadas fallidas en una pasada).
- Ronda 2: ninguna duda en las tres. El mínimo del README sube de 15 a 16 porque cuenta leer lo que se edita.
- Ronda 3: «si cambia una parte de una pantalla, el anexo» hizo que las tres crearan un anexo que el proyecto no tenía
  (`derivadas --escribir` lo añade), y una pasó `--cambio` a `ficha`, que no lo admite. Ronda 4: el anexo, solo si
  `comprobar.py` avisa de que se quedó viejo; las dos órdenes, en un bloque cada una.
- La calidad no baja: las doce pasadas dejan D-01 con su «Antes» citado, la fila de §13 de EV-03 y el informe completo.

### Revisión independiente

Un agente que no había visto el trabajo revisó la rama: nada grave. Corregido:
- el anexo «Quién puede hacer qué» se quedaba viejo al renombrar una parte de una pantalla, y el DF lo enseña:
  `comprobar.py` avisa (se apaga con `derivadas --escribir`);
- la fila de §13 que sugiere `impacto`: fallaba sin técnico, proponía objetos sin construir, usaba una URG Abierta o la
  unidad equivocada cuando sugería abrir otra, y para historias o pasos sacaba objetos de cualquier línea: ahora, solo
  lo construido de la fila de la pantalla de la pieza (sin pantalla, solo el formato);
- `proyecto.py version` dice lo que no pudo escribir (sin la tabla), nombra solo los documentos que sube, entrecomilla
  las rutas con espacios, acepta la carpeta `analisis/`, describe bien un chat en «Fuentes procesadas» y recuerda que
  «Qué cambia» sale en el Word; los tipos de las filas D, en un solo sitio (`modelo.py`).

### Enrutado con las vecinas

`vecinas.json` con la descripción de `appian-sail-generator` 2.3.2 (su frontera con prototipos y buenas prácticas):
visibles **13/13** y las 10 ocultas nuevas (`vecinas/ocultas.json`, `--vecinas-ocultas`) **10/10**. Las seis
descripciones del plugin no cambian en esta versión: el resto de lotes no se repite.
Raúl no publica la 2.3.2 (desactiva `appian-sail-generator` en su cuenta): `vecinas.json` vuelve a la descripción
publicada, la 2.3.1, y con ella también salen **13/13** y **10/10**. El plugin marca la frontera por sí solo.

### El recién llegado (Tarea 9), con la versión actual

MNT documentada a ciegas contra el simulador (32 minutos) y respondida por otro agente con `as-is/` sin `extraccion/`.

| | Tarea 9 (después) | 0.7.0-beta.3 |
|---|---|---|
| Preguntas visibles | 21/22 | 22/22 |
| Preguntas ocultas | 7/7 | 7/7 |
| `evidencia.py` | bien | bien |
| `comprobar_asis.py` | 0 errores, 0 avisos | 0 errores, 0 avisos (8 avisos en la primera pasada, corregidos) |
| NV registrados | 8 | 12 |
| Palabras (total) | 17.293 | 14.744 (−15 %) |

- `puntuar.py` daba por mala una respuesta «No. …» a una pregunta sí/no: comparaba la primera palabra con el punto
  pegado. Corregido; sin el arreglo, 21/22.
- Lo que el agente encontró confuso en las instrucciones, y qué se hizo:
  - un documento entero que no aplica frente a «las secciones sin contenido se omiten»: Regla 1 de
    `presentation-rules.md` lo distingue;
  - la cifra del registro en el TL;DR de 09, que se sabe después de `build_registry.py`: la plantilla lo dice;
  - un temporizador por intervalo sin hora de inicio: `bpmn-mapping.md`, `R/PT5M`;
  - un proceso de 130 nodos no cabe en el presupuesto de su `.md` con un paso por nodo, y «5 cajas por capa» no basta
    para el ancho de la arquitectura: a `siguiente-version.md`.

### Menores

- `toolsOmitted` en `extraction_report.json`: usadas más omitidas son el catálogo también con `--solo` y con llamadas
  `notApplicable` (pruebas en `test_fixture_mal_hecha.py` y `test_verificar_y_deriva.py`).
- Diagramas: con 170 procesos al azar (semilla 7), etiquetas de salida de puerta sobre un tramo ajeno de 7 diagramas a 0,
  cruces de 359 a 347, sin que empeore ninguno; uno de la muestra pasa de 1.534 a 1.618 px de ancho (aviso de los 1.600).
- `requisitos.py`: GitHub o Notion configurados ya no dejan el Appian MCP Server «sin comprobar».

## 0.7.0-beta.2 · G7 · Evaluaciones finales (11 de octubre de 2026)

Rama `g7-evaluaciones`, de `v0.7.0-beta.2` 4fe7338. Se pasan a ciegas, con las skills y los puntuadores tal como están,
las ocultas del enrutado y las tres evaluaciones del analista que más ha cambiado la versión. «Evolutivo con urgencia» y
la prueba de coste se midieron en G5 con este método y no se repiten.

**Cómo se pasaron.** Cada agente es un `claude -p` nuevo con una copia del paquete (`pruebas/empaquetar.py`, 177
ficheros), sin la herramienta Skill (lee los `SKILL.md`), sin CLAUDE.md ni ajustes (`--restricted
--setting-sources ""`), con la lectura de `pruebas/`, `docs/` y `skills/` del repositorio denegada y Bash limitado a
`python3` y `node` sobre la copia (y `uv run` en ingeniería inversa). El entorno solo deja lanzar agentes con herramientas desde la carpeta del
repositorio: la copia y los proyectos estuvieron en una carpeta ignorada dentro de ella y al terminar pasaron a
`$PROYECTOS_PRUEBA`. Los registros de cada sesión confirman que ninguno abrió `pruebas/` ni `docs/`. Analista e
ingeniería inversa, con Opus; el enrutado, con el modelo por defecto de `claude -p`.

| Evaluación | Resultado | Umbral | Pasa |
|---|---|---|---|
| Enrutado, ocultas (tres pasadas) | 10/10 ×3 | todas | sí |
| Incoherencias | 10/10 y 3/3; ninguna aplicada, ninguna coincidencia como cambio | todas (las dos salen 0) | sí |
| Demo | 6/6 y 6/6 | las dos salen 0 | sí |
| Evolutivo | 10/10 y 3/3; `comprobar.py` sin errores | 8 de 10 y 3 de 3 | sí |

- **Enrutado.** Las descripciones finales de G6 con las 10 ocultas, que no se habían pasado: un agente sin herramientas
  por pasada, desde una carpeta vacía.
- **Incoherencias** (`AYC-incoherencias/`, 75 turnos). El DF entra como 1.0 con sus IDs y cada reunión tiene su
  informe, con las 13 diferencias «Sí (🔒)» y «Pendiente». La versión sube a 1.1 solo por un COMPLETA que no pedía
  aprobación (R2).
- **Demo** (`PRE-demo/`). Aplica los cuatro retoques, deja PAN-02 y PAN-05 pendientes y pide aprobación. Con «Aplica el
  de la solicitud; el de entregar y recoger, de momento no» cataloga la respuesta como aprobación (FU-04, R1), cambia
  PAN-02 y no toca PAN-05. En la ronda oculta cambia solo PAN-03.
- **Evolutivo** (`MNT-evolutivo/`). Primero la 1.0 de toda la aplicación desde `as-is/` (12 historias, 11 pantallas y 3
  procesos, E1); después la reunión como 1.1 en la unidad EV-01, con §13 objeto a objeto, y el aviso del hallazgo Alta
  de lo que se modifica. En la oculta, la consulta del ERP pasa a una ficha INT con criterios en vez de una historia (R6).
- **El `as-is/` de MNT** no estaba en este equipo: lo generó un agente a ciegas con ingeniería inversa contra el
  simulador (`mock_devmcp/`, `MOCK_APP=fixture_mal_hecha`, con el Dev MCP y el Appian MCP Server) en 40 minutos: 44
  objetos, 39 hallazgos, `comprobar_asis.py` con 0 errores y un aviso (11 pasa de su presupuesto de palabras) y
  `evidencia.py` bien. Está en `MNT/`. No se pasó la evaluación del recién llegado (sus preguntas).
- **Puntuadores.** Ninguno choca con el método nuevo: el de evolutivo lee la Situación de §13, no un «Origen» en las
  historias, y los de incoherencias y demo leen los informes y no dependen de que la versión suba (sin `versiones/v1.0`,
  buscan lo aplicado en el texto).

### Lo que salió

- **R4 en la demo.** El cambio de PAN-02 lo aprobó el equipo (FU-04, «De: analista del proyecto») y la pantalla sigue 🔒
  porque «lo pidió el almacén en la demo»; `proyecto.py estado` la sigue dando por validada por el cliente. Según R4 (y
  el plan: un CAMBIA aprobado por el jefe de proyecto pasa a ✅ y el cliente valida después) tendría que pasar a ✅. La
  fila CAMBIA de `skills/appian-functional-analyst/references/actualizacion.md` dice «si lo aprueba el cliente» sin
  decir qué es aprobarlo. Corrección propuesta, sin aplicar: «Si era 🔒 y lo aprueba el cliente (una fuente suya que lo
  apruebe: pedirlo en una reunión o en una demo no basta), sigue 🔒 con la cita; si lo aprueba el equipo, ✅». No cambia
  la puntuación.
- Con Bash limitado, los agentes probaron `echo`, `python3 -c` y órdenes encadenadas, y las rehicieron: es fricción del
  montaje, no del plugin.

## 0.7.0-beta.2 · G6 (11 de octubre de 2026)

### Enrutado con vecinas (tarea 6.6)

Lote nuevo `pruebas/evaluaciones/enrutado/vecinas/`: 13 peticiones de frontera con dos skills de fuera del plugin
(`appian-sail-generator` y `docx`, con su descripción literal en `vecinas.json`). Cada pasada, un agente nuevo sin
herramientas ni skills (`claude -p` desde una carpeta vacía) que solo recibe `puntuar.py --enunciado --vecinas`.

| Descripciones | Vecinas | Fronteras | Visibles |
|---|---|---|---|
| Las de 6.5 (≤ 1.000 bytes, fronteras con SAIL y Word) | 12/13 ×3 | — | — |
| Buenas prácticas reclama el SAIL pegado que se revisa | 13/13 ×3 | 7/8, 8/8, 7/8 | 20/20 |
| Diagramas remite al analista los de estados y de datos | 13/13 ×2 | 8/8 ×3 | 20/20 |
| Tras la revisión: buenas prácticas, en un entorno o pegado; el SAIL a partir de requisitos, de `appian-sail-generator`; analista con margen (974 bytes) | 13/13 ×3 | 8/8 ×3 | 20/20 ×2 |

- El fallo de las tres primeras pasadas: «Revisa este SAIL: hace un a!queryRecordType dentro de un a!forEach» iba a
  `appian-sail-generator`, que se ofrece para «paste SAIL expressions and ask for fixes/improvements». Buenas prácticas
  dice ahora que construye, cambia, revisa o depura «in an environment or as pasted code» y, en su «Not for»,
  «generating SAIL from requirements (appian-sail-generator)». La otra mitad, que `appian-sail-generator` diga que no es
  para revisiones de buenas prácticas, es de Raúl (plan, apartado 6).
- El recorte del analista para caber en 1.000 bytes hizo fallar la frontera de los diagramas de estados y de datos (con
  las descripciones de antes, 8/8 ×2): diagramas dice ahora que esos los hace el analista.
- Las ocultas no se han pasado: quedan para G7, con el resto de las evaluaciones.

## 0.7.0-beta.2 · G0-G5 (10-11 de octubre de 2026)

Plan único `docs/plan/2026-10-10-0.7.0-beta.2.md`. Cada fase, en su rama, con su revisión independiente; los hallazgos
de las revisiones se corrigieron en la misma rama antes de unirla (el más grave: los IDs de hallazgos que debían quedar
estables se podían intercambiar al reextraer, G1).

### Evolutivo con urgencia (tarea 5.11)

Proyecto ficticio del caso C (`EV-01` en producción, `EV-02` aprobada) y una incidencia crítica sobre un objeto de
`EV-02`. Dos pasadas a ciegas con las skills copiadas, sin `pruebas/` ni `docs/`.

| Pasada | Visible | Ocultas | Nota |
|---|---|---|---|
| 1 | 9/9, pasa | 5/6, no pasa | No pasó la URG a producción: el método decía «desatendida: nunca» aunque el encargo traía el visto bueno del jefe de proyecto, y quiso la prueba en producción antes de cerrar |
| 2 | 9/9, pasa | 6/6, pasa | Tras corregir: con el visto bueno catalogado como Aprobación se pasa (`--desatendida --fuente`), y «En producción» registra un pase que ya ocurrió: lo que falte por comprobar va en «Cierre» |

La pasada 2 encontró además que `produccion` guardaba la fecha del registro y no la del pase, que es con la que compara
la deriva: `--fecha`.

### Prueba de coste: texto de un botón construido (tarea 5.12)

Calidad, las tres veces: informe aplicado en una unidad nueva Abierta, 0 aprobaciones, 0 DT, 0 pasadas de `comprobar.py`
con errores, ningún Word ni captura regenerados. **Coste: 34, 34 y 47 llamadas frente al tope de 25: no pasa.**

- Unas 22 llamadas son del método (leer SKILL.md y tres referencias, catalogar, buscar, informe, copia, editar
  funcional, técnico y decisiones, anexo, comprobar). El resto, dudas que el método no resolvía: si meterlo en la unidad
  Aprobada o abrir otra, el formato de la fila D, si hay que rehacer la captura.
- Tras la pasada 1 se corrigió: una fuente corta no lleva nota; si nada requiere aprobación, una sola pasada de
  `comprobar.py`; el formato de la fila D en `actualizacion.md`; e `indice.py impacto` dice qué unidad abrir cuando no
  hay ninguna Abierta. La pasada 3 ya no dudó en eso, pero editó con 20 llamadas sueltas: la cifra depende mucho de cómo
  edite el modelo.
- El tope se fijó antes de medir y no se cambia. Queda para la siguiente versión un camino corto de retoque (apartado
  «Aplazado»).

### Aplazado

- Retoque: un cambio de texto sobre algo construido sigue costando ~30 llamadas. Medir de nuevo con el plugin instalado
  y, si sigue por encima, un camino corto para un punto sin aprobación (informe y aplicación en un paso).

### Cierre de la 0.7.0-beta.2

`comprobar_plugin.py --completo` en verde en el repositorio y sobre el paquete descomprimido en una carpeta con espacios (177 ficheros, sin pruebas, docs ni cachés). CI en verde en Windows, macOS y Linux con Python 3.9 y 3.12, también con la consola en cp1252.

Lo aprendido:
- Mirar el CI tras cada subida: el Windows con consola cp1252 falló desde G0 (las pruebas de las evaluaciones escribían ✔ y 🔒 sin pasar la consola a UTF-8) y no se vio hasta G6.
- Las evaluaciones a ciegas encuentran lo que las pruebas no: «desatendida: nunca» bloqueaba un cierre con el visto bueno del jefe de proyecto en el propio encargo, y la fecha del pase no era la del pase.
- El coste de un retoque depende tanto del método como de cómo edita el modelo (34 frente a 47 llamadas con el mismo método): medirlo con varias pasadas.

## F9 · Cierre (9 de octubre de 2026)

Rama `f9-cierre`, de `main` d9503a6 al merge. Versión 0.7.0-beta.1.

### Punta a punta (Tarea 30, paso 1)

Con la aplicación ficticia MNT en el simulador, en `$PROYECTOS_PRUEBA/MNT-e2e/`, cada paso lo hace un agente distinto
que sigue los SKILL.md con una copia del plugin, sin ver el repositorio:

| Paso | Tiempo | Resultado |
|---|---|---|
| Ingeniería inversa | 31 min | 35 hallazgos (5 Alta), 9 NV, 4 procesos (el de 130 nodos en 15 tramos); `comprobar_asis.py` 0/0 |
| Refactorización del módulo de órdenes | 18 min | 20 REF, 12 decisiones y los 9 NV en Pendientes; `comprobar_propuesta.py` 0/0 |
| Funcional y técnico, una reunión que cambia dos cosas, diagramas y Word | 54 min | 19 historias, 11 pantallas, 2 procesos; informe de impacto con aprobación de la ampliación; `comprobar.py` sin errores, también con `--anterior --impacto` |
| Prototipo y Word con las capturas | 26 min | 13 pantallas, 20 capturas enlazadas en el funcional; `validate.py` sin avisos de UX |

Los nueve NV llegan a las Pendientes de la propuesta y a una PT o una PC del análisis (los de negocio, como PC, y así
al guion de la próxima reunión); cada REF de la Solución tiene su DT; el Word no lleva IDs internos ni marcas.

### Revisión de conformidad con el diseño (Tarea 30, paso 2)

Un agente que no había visto el trabajo revisó el plugin entero contra el diseño, con el punta a punta como prueba.
Lo que se corrigió:

- **Ingeniería inversa no arrancaba con un Python 3.9 de uv:** las órdenes `uv run` no fijaban la versión y `mcp` pide
  3.10. Ahora llevan `--python ">=3.10"` y `comprobar_plugin.py` da error con una que no lo lleve.
- **Repetir la ingeniería inversa en un proyecto que ya tiene análisis** cambiaba en silencio a qué apuntan las citas
  `[FU-nn H-…]` (los hallazgos se numeran de nuevo). Ahora `comprobar.py` avisa si las citas son de un `as-is/` anterior.
- **El aviso de texto viejo** daba 10 avisos falsos en el punta a punta (siete por las palabras de una URL): sin URL ni
  código y con seis palabras seguidas, queda uno, que es cierto.
- **`comprobar.py`** decía que comprobaba las REF citadas y no lo hacía; ahora también las DEC.
- **La descripción del plugin** era la de antes del plan.

### Paquete e instalación limpia (Tarea 31)

`pruebas/empaquetar.py` hace el `.plugin` con la misma lista que comprueba `comprobar_plugin.py` (171 ficheros, sin
pruebas, docs, cachés ni `.git`). Desde el paquete descomprimido en una carpeta con espacios, `requisitos.py --json` con
todo lo opcional ausente es igual a `pruebas/requisitos-esperado.json`, y `comprobar_plugin.py --completo --plugin
<copia>` pasa las pruebas del repositorio contra lo que se instala.

### Pendiente de Raúl

- Paso 4 de la Tarea 24: instalar el paquete en Claude Code y en la app de escritorio, con algo de la tabla sin instalar,
  y ver que el primer mensaje lo dice (mejor también en un Windows).
- Paso 3 de la Tarea 30: ingeniería inversa y refactorización con una aplicación real, en su equipo. Aquí va si pasó o
  no y qué se corrigió, sin nada del cliente.
- Paso 3 de la Tarea 31: desinstalar la skill suelta de ingeniería inversa y archivar su carpeta.
- El criterio de palabras de F3.

### Lo aprendido

- El punta a punta encontró lo que ninguna fase veía porque está entre fases o en el primer paso: la versión de Python
  de uv y lo que pasa al repetir la ingeniería inversa en un proyecto que ya sigue adelante.
- Un aviso nuevo se mide con un proyecto real antes de darlo por bueno: el de texto viejo pasó sus pruebas y en el
  primer caso real solo daba ruido.

## F8 · Sin solapes (9 de octubre de 2026)

Rama `f8-sin-solapes`, de `main` ab088d0 al merge. Versión 0.7.0-alpha.7.

### Qué cambia

- **Un dueño por salida (Tarea 27).** Cada SKILL.md dice en «Qué escribe» («What it writes» en buenas prácticas) qué
  rutas del proyecto escribe, y `pruebas/propietarios.json` dice de quién es cada una (gana el patrón más específico;
  `tambien` deja escribir a otra skill, como diagramas en el `.json` de un proceso). `comprobar_plugin.py` da error si
  una skill declara lo de otra, si un dueño no declara su regla, si un script fuera de diagramas pinta Mermaid o exporta
  BPMN, o si hay una lista de muletillas fuera de `redaccion.md`. Cuatro escrituras que no encajaban tienen su regla:
  el enlace de cada captura en el funcional (prototipos), las imágenes de los Mermaid de ingeniería inversa
  (diagramas), la carpeta `prototipo/` vacía y `modulos/` (analista).
- **Las seis descripciones (Tarea 28).** Qué hace cada una, cuándo usarla y qué no hace, con la skill que lo hace. El
  analista remite a refactorización; buenas prácticas, la evaluación de una aplicación entera; diagramas dibuja también
  el proceso de una aplicación existente.
- **`indice.py grafo`** escribía en la carpeta desde la que se ejecutaba; ahora, en `analisis/grafo.json`.

### La prueba de enrutado (Tarea 29)

Un agente que solo ve las seis descripciones elige la skill de cada petición; cada lote, un agente nuevo.

| Lote | Peticiones | Primera medida | Con las descripciones corregidas |
|---|---|---|---|
| Visibles (`pruebas/enrutado.json`) | 20, cuatro o tres por skill y una por frontera | 20/20 | 20/20 |
| Ocultas | 10, una variante de cada frontera | 10/10 | 10/10 |
| Fronteras difíciles (tras la revisión) | 8, sin las palabras que delatan la skill | — | 8/8 |

- La revisión vio que las peticiones de frontera llevaban la pista que las resuelve: un clasificador que solo cuenta
  palabras acertaba 16 de 20 visibles y 5 de 10 ocultas. Por eso el tercer lote: revisar una aplicación entera frente a
  un objeto, las tablas de una aplicación sin papeles, los diagramas de estados y de datos (del analista), un proceso
  contado en una reunión (primero el analista), algo navegable antes de validar, un timeout en producción y los cambios
  de una reunión sobre lo validado. `prueba_puntuar.py` comprueba que no lleven esas palabras.
- La revisión de la fase también encontró que diagramas decía que la usa refactorización, que no dibuja, y que el «No…»
  de cuatro descripciones no nombraba a la skill que lo hace: corregido antes de la segunda medida.

### Lo aprendido

- Una prueba de enrutado con las palabras de las descripciones mide el vocabulario, no la frontera. La prueba de que
  mide algo es un clasificador tonto que falla donde el agente acierta.
- «Qué escribe» cruzado con lo que escriben los scripts encontró una escritura fuera del proyecto (`grafo.json`) que
  ninguna prueba había visto.

### Aplazado

Lo menor de la revisión, en `docs/siguiente-version.md` («Sin solapes»): el `tambien` de `prototipo/`, la comprobación
de dueños que solo lee «Qué escribe», el `cambios.json` de diagramas, «una pieza por capacidad» fuera de los `.py`, las
descripciones cerca del límite y las skills vecinas como distractoras en el enrutado.

## F7 · Equipo (9 de octubre de 2026)

Rama `f7-equipo`, de `main` ee4b19b al merge. Versión 0.7.0-alpha.6.

### Qué cambia

- **`requisitos.py` y `requisitos.json` (Tarea 23).** Qué hace falta para cada skill (Python, Playwright y un navegador,
  Node con `docx`, LibreOffice, un lector de PDF, `uv`, el Dev MCP, el Appian MCP Server), qué se pierde sin ello y
  cómo se instala en cada sistema. Solo busca ejecutables y rutas: no abre nada. Avisa si hay una copia suelta de una
  skill del plugin, también con el nombre anterior de prototipos.
- **El aviso al instalar (Tarea 24).** Un hook `SessionStart` ejecuta `requisitos.py --breve`: dice lo que falta una vez
  por versión y deja la marca en `~/.cache/appian-analisis-funcional/` (lo único que el plugin escribe fuera de un
  proyecto). El comando vale en sh y en PowerShell 5.1 y prueba `python3` y `python`. Cada skill lo comprueba antes de
  su primera tarea y sigue sin él en una copia suelta.
- **El README y el paquete (Tarea 25).** La tabla de requisitos del README sale de `requisitos.json`. `comprobar_plugin.py`
  da error si un fichero del paquete, o su nombre, lleva un dato personal (usuarios, carpetas personales de Windows,
  macOS o Linux) o un cliente de `pruebas/clientes.txt`. Las galerías, las plantillas y los ejemplos de prototipos pasan
  a una empresa ficticia (Vadelia, sus sedes, incidencias y expedientes) y se regeneran.
- **Windows (Tarea 26 y revisión).** Los scripts pasan la consola a UTF-8 al arrancar y leen la salida de otros
  programas en UTF-8; `comprobar_plugin.py` da error si uno no lo hace. `detect_secrets.sh` usa el primer Python que
  funcione.

### Pruebas: la matriz de GitHub

| Ejecución | ubuntu 3.9 / 3.12 | macOS 3.9 / 3.12 | Windows 3.9 / 3.12 | Windows 3.12 sin UTF-8 |
|---|---|---|---|---|
| acac31e, 8c19eb7 | ✓ / ✓ | ✓ / ✓ | ✗ / ✗ | — |
| c47c1f5 | ✓ / ✓ | ✓ / ✓ | ✗ / ✗ | — |
| dfe6af6, d102e72 | ✓ / ✓ | ✓ / ✓ | ✓ / ✓ | ✗ |
| ff22ff9 | ✓ / ✓ | ✓ / ✓ | ✓ / ✓ | ✓ |

- **Windows con `PYTHONUTF8=1`** fallaba en una sola prueba, la de `detect_secrets.sh`. El primer arreglo (que el
  envoltorio no encontrara `python3`) era bueno pero no era la causa: en Windows, `subprocess` con «bash» a secas encuentra
  el lanzador de WSL de System32 antes que el bash de Git. Lo vio la revisión de la fase.
- **Windows sin UTF-8**, la consola de un compañero: no estaba en el plan; lo pidió la revisión, porque `PYTHONUTF8=1`
  tapaba justo el fallo típico. Se rompían nueve scripts al imprimir «→» o «✓» y el propio comprobador. Aquí se
  reprodujo con una locale CP1252 antes de subir el arreglo.
- Los registros de un job no se pueden leer desde la API: si la comprobación falla, el workflow deja la cola de la
  salida en anotaciones.
- **Pendiente de Raúl (Paso 4 de la Tarea 24):** instalar el paquete en Claude Code y en la app de escritorio, con algo de
  la tabla sin instalar, y ver que el primer mensaje lo dice; si puede ser, también en un Windows.

### Lo aprendido

- Antes de arreglar un fallo que solo se ve en otra máquina, confirmar la causa: el primer arreglo de Windows tenía
  sentido y no era el fallo. Una aserción que pasaba (el código de salida) ya lo decía.
- Una variable que hace pasar las pruebas (`PYTHONUTF8=1`) también puede esconder lo que más le pasa a quien usa el
  plugin. Conviene una combinación de la matriz sin ella.
- Lo que no se puede ver (los registros de GitHub) se hace visible desde el propio workflow.
- Una comprobación estática barata (AST: `print` sin `reconfigure`, `subprocess` de texto sin `encoding`) evita que el
  fallo vuelva con el siguiente script.

### Aplazado

Lo menor de la revisión, en `docs/siguiente-version.md` («Equipo»): «PMI» como código de un cliente, el orden
`python3`/`python` del hook en Windows, la sustitución de `${CLAUDE_PLUGIN_ROOT}` en PowerShell (sin verificar), el Dev
MCP configurado en otro proyecto y las acciones de Node 20 de la matriz.

## F6 · Analista (9 de octubre de 2026)

Rama `f6-analista`, de `main` a3cc312 al merge. Versión 0.7.0-alpha.5.

### Qué cambia

- **Citas de IDs de otra skill (Tarea 16).** «[FU-07 PAN-03]» es la PAN-03 del prototipo: `modelo.quita_citas` la quita
  antes de buscar IDs, y no cuenta como referencia en el índice ni en las comprobaciones.
- **Guion de la próxima reunión (Tarea 17).** `indice.py pendientes`: las PC abiertas por «A quién», de las que afectan a
  más partes del análisis a las que menos.
- **Texto que queda viejo (Tarea 18).** `comprobar.py --anterior` avisa de cada línea que ya estaba y aún dice lo que una
  pieza cambiada ya no dice (cinco palabras seguidas).
- **Aplicación existente (Tareas 19 y 20).** Con `as-is/`: «Origen» de cada historia, §13 con la Situación de cada
  objeto, carga inicial y migración en §3, cada REF de la propuesta con su DT (o «No se hace»), y los NV que condicionan
  lo que se construye como PT o, si los resuelve negocio, como PC. Avisa si se toca un objeto con un hallazgo Alta o
  algo sin verificar que ninguna PT o PC cita. Sin `as-is/`, la salida es la de antes. `leer_fuentes.py --una-fuente`
  cataloga `as-is/` como una sola fuente.
- **DF ya hecho y demo (Tarea 21).** El DF del cliente entra como versión 1.0, cada pieza 🔒 con su ID original; las
  reuniones de antes pasan por el informe de impacto. Los comentarios de una demo son puntos del informe y prototipos
  rehace solo sus pantallas, sin tocar las validadas sin aprobación.
- **El informe de impacto, más estricto (pasada de correcciones).** «Requiere» es «—» o «Sí (motivo)», y `comprobar.py`
  lo exige; «de momento no» es «Pendiente»; en una sesión desatendida lo que requiere aprobación no se aplica y la
  cabecera dice qué puntos quedan, que `proyecto.py estado` lista.

### Las evaluaciones del analista (Tarea 22)

Tres casos ficticios en `pruebas/evaluaciones/`, cada uno ejecutado por un agente a ciegas (copia de las skills, sin
`pruebas/` ni `docs/`) en su proyecto de `$PROYECTOS_PRUEBA`.

| Caso | Primera medida | Segunda medida (tras la pasada de correcciones) |
|---|---|---|
| Incoherencias: DF validado y tres reuniones anteriores, 10 incoherencias + 3 ocultas | 0/10 y 0/3 | 10/10 y 3/3, ninguna aplicada, ninguna coincidencia como cambio |
| Demo: seis pantallas, dos validadas; un comentario por pantalla + un correo oculto | 4/6 | 6/6 y 6/6 |
| Evolutivo: tres historias sobre MNT + una cuarta oculta | 10/10; oculta 2/3 sin aprobar y 3/3 aprobada | — (10/10 y 3/3 con el puntuador nuevo) |

- **El fondo estaba bien desde la primera medida y el formato no.** En incoherencias y demo, los agentes encontraron todo,
  con su pieza, sin aplicar nada sin aprobación; pero escribieron «Aprobación: cambia HU-01 🔒…» en la columna
  «Requiere», que la skill no definía, y el puntuador lo da por no pedido. La revisión lo confirmó (con «Sí (🔒)» salen
  10/10, 3/3 y 6/6). Se fija el formato y `comprobar.py` lo exige; no se ablanda el puntuador.
- **La ronda oculta de evolutivo** pide una ampliación, que en una sesión desatendida no se aplica sin aprobación: el
  README da ahora la aprobación por adelantado, como la demo.
- **El puntuador de evolutivo emparejaba los objetos nuevos solo por tipo**: con tres quitados seguía en 9/10. Ahora cada
  uno lleva las raíces de nombre que valen, sacadas de la reunión.
- `comprobar.py` sin errores en los tres. Proyectos: `AYC-incoherencias/`, `PRE-demo/` y `MNT-evolutivo/` (las
  primeras medidas, en `AYC-incoherencias-1/` y `PRE-demo-1/`).

### Lo aprendido

- Un formato que solo está en un ejemplo no es un formato: dos agentes distintos escribieron lo mismo fuera de él. Si
  algo se va a leer con un script, la skill lo define y el comprobador lo exige.
- Las reglas para la sesión desatendida tienen que cuadrar con las comprobaciones: «entra como ⚠️» chocaba con «una
  pieza 🔒 no cambia sin aprobación».
- Los avisos que no se pueden apagar se ignoran: 25 en el evolutivo, todos ya atendidos por una PT o una PC, y 4 de 4
  falsos en el texto viejo. Ahora se apagan cuando lo que piden ya está hecho.
- Los puntuadores se revisan quitando lo que debería contar, como en F5: el de evolutivo no bajaba.

### Aplazado

Lo menor de la revisión y la fricción de las evaluaciones, en `docs/siguiente-version.md` («Analista»). Lo más
importante para la siguiente versión: en una sesión desatendida, los puntos pendientes de aprobación solo quedan en
los informes y no llegan al guion de la próxima reunión.

## F5 · Refactorización (9 de octubre de 2026)

Rama `f5-refactorizacion`, de `main` e475a94 al merge. Versión 0.7.0-alpha.4.

### Qué cambia

- **La skill `appian-refactorizacion` (Tarea 13).** Lee `as-is/` y nada más (no la extracción) y escribe
  `refactorizacion/propuesta.md`: alcance y límites, diagnóstico (una ficha `REF-nn` por problema, con su evidencia en
  `as-is/`, la sección de buenas prácticas que lo trata, efecto, prioridad y esfuerzo), solución por capa con lo que se
  descarta, migración y convivencia, hoja de ruta y pendientes (decisiones y los NV que condicionan la solución). Del
  bloque B entran rebuild-architect (sin el 12 ni el detalle objeto a objeto del 14), la migración de target-designer y
  las señales de `modernization-guide.md`; `docs/bloque-b/` se borra.
- **`comprobar_propuesta.py` (Tarea 14).** Apartados, fichas completas, evidencias que llevan a `as-is/`, «BP nn §x»
  que existen (una o dos por REF), objetos del inventario en el Diagnóstico (los patrones no), cada REF en Solución,
  `H-…` y NV que existen, marcadores sin sustituir y enlaces a la extracción. Avisa de lo no verificado que se pierde:
  un NV que no se cita, un hallazgo inferido marcado ✅, uno Alta o Media sin REF ni pendiente, y una REF sobre un
  hallazgo inferido sin «Verificar H-…» antes en la Hoja de ruta.
- **Un problema, un hallazgo, una REF.** Ingeniería inversa no abre dos hallazgos del mismo problema visto por dos
  señales (huérfano y sin ejecuciones; el aviso de validación de más de 50 nodos), y refactorización hace una REF por
  problema citando todos sus hallazgos.
- `comprobar_plugin.py` da error si refactorización o el analista citan la extracción en bruto.

### La evaluación de malas prácticas (Tarea 15)

Un agente sigue el `SKILL.md` sobre `$PROYECTOS_PRUEBA/MNT/` con una copia de las skills, sin ver `pruebas/` ni
`docs/`, con alcance «toda la aplicación», seis meses y sin tocar las reglas `CMN_`. `puntuar.py` cuenta una mala
práctica si una REF cita sus objetos en la evidencia, una de sus secciones aceptadas en la Regla y sale en Solución.

| | Primera propuesta | Segunda propuesta (tras la revisión) |
|---|---|---|
| REF / palabras / tiempo | 27 / 6.298 / 16 min | 26 / 6.678 / 16 min |
| Visibles, puntuador de la Tarea 15 | 11/11 | — |
| Visibles, puntuador por sección | 9/11 (MP-05 y MP-11) | 10/11 (MP-01) |
| Ocultas | 3/3 | 3/3 |
| NV de las reglas `CMN_` en Pendientes | sí | sí |
| `comprobar_propuesta.py` | 0/0 (el de entonces) | 0/0 |

- **El primer puntuador medía poco.** Aceptaba cualquier sección del documento de buenas prácticas esperado: la revisión
  quitó las cuatro REF que trataban MP-04, MP-08, MPO-01 y MPO-02 y seguía saliendo 11/11 y 3/3. Ahora cada mala
  práctica lleva `bp_aceptadas`, fijadas por un agente con la descripción y las secciones, sin ver ninguna propuesta.
- **Con el puntuador nuevo, la primera propuesta da 9/11**, y los dos fallos venían de `senales.md`: el correo
  repetido iba a BP 03 §13 y el connected system de desarrollo a BP 07 §2, que no trata los entornos. Corregidas las
  dos filas, la segunda propuesta, hecha a ciegas con la skill corregida, da 10/11: MP-01 (el listado sin paginar) sale
  con BP 01 §7 y BP 02 §5.3.
- Las dos propuestas citan en una sola REF los dos hallazgos de `MNT_PM_Antiguo` (huérfano y sin ejecuciones).
- Proyectos: `MNT/` (la segunda) y `MNT-refactorizacion-1/` (la primera), en `$PROYECTOS_PRUEBA`.

### Lo aprendido

- Un puntuador también se revisa con sondas: quitar lo que debería contar y ver si el número baja. El primero pasaba
  por bueno lo que no medía.
- Las listas de lo aceptado se fijan antes de ver un resultado y no se tocan después; cuando un resultado no cuadra, se
  arregla la skill y se vuelve a medir a ciegas.
- La tabla de señales decide la regla que cita cada REF: un error en una fila es un error en todas las propuestas.
- Lo que falta en buenas prácticas sale enseguida al usarla para justificar (el «Cancelar» de un formulario de inicio,
  un paso que se hace siempre): apuntado para la siguiente versión.

### Aplazado

Siete menores de la revisión y la fricción de la segunda propuesta, en `docs/siguiente-version.md` («Refactorización»
y «Buenas prácticas»).

## F4 · Diagramas (9 de octubre de 2026)

Rama `f4-diagramas`, de `main` c656d21 al merge. Versión 0.7.0-alpha.3.

### Qué cambia

- **Un solo exportador y un solo pintor (Tarea 12).** Ingeniería inversa dibuja y exporta con `diagrama.py` de la skill
  de diagramas; se retiran `bpmn_layout.py`, `validate_mermaid.py` y `render_diagrams.sh`. El carril de lo que hace
  Appian es «Aplicación», una integración sin connected system es un participante externo y el índice de procesos no
  pide «Vista» si ningún proceso lanza a otro.
- **Procesos grandes en tramos (Tarea 12).** Con `"tramos": true`, un proceso que existe y no cabe en 1.600 px sale en
  varias páginas del `.drawio`, unidas por eventos de enlace, y un PNG por página; `leer`, `comparar` y `bpmn` deshacen
  los enlaces y el `.bpmn` es uno. `crear` y `actualizar` dicen qué pasos lleva cada tramo, y el nombre de la página
  también.
- **Sin navegador (Tarea 12).** Con la colocación por capas, `crear`, `actualizar` y `comparar --aceptar` escriben el
  `.drawio` y el `.json` igual, avisan «sin PNG» y salen con 2; si había PNG, lo quitan. Se prueba con
  `DIAGRAMAS_SIN_NAVEGADOR=1`.
- **Los datos de Appian en el diagrama (Tarea 10).** El nodo, la expresión del temporizador, el proceso llamado y la
  condición de cada salida, en «Editar datos» de draw.io y en el `.bpmn` (válido contra el XSD de BPMN 2.0). Un paso
  para los errores; la nota es un corchete que se ensancha con su texto.
- **`mermaid.py` en la skill de diagramas (Tarea 11).** Comprueba y pinta los bloques Mermaid de un Markdown (`--md`),
  avisa si uno pasa del ancho legible y acepta comodines también en Windows. El analista lo usa en lugar del suyo.

### Pruebas

| | Antes (F3) | Después |
|---|---|---|
| `MNT_PM_GestionOrden` (130 nodos), `.drawio` | una página de 29.536 px | 14 tramos de 1.244 a 1.528 px |
| PNG | uno de 22.171 px (la skill promete 3.200) | uno por tramo |
| `.bpmn` | del exportador de ingeniería inversa | uno, de `diagrama.py`, válido contra el XSD |
| Pruebas de ingeniería inversa | 139 | 140 |

- Selftest de la skill de diagramas con y sin navegador; `--completo` en verde, también con Python 3.9.
- La revisión de la fase reprodujo con tres puertas seguidas conexiones que no existen en la colocación por capas. El
  selftest comprueba ahora sobre la geometría que sale (no sobre un caso) que ningún flujo pasa por un paso ajeno ni por
  la etiqueta de otro flujo y que dos flujos sin extremo común no van por la misma recta; con el JSON del revisor, de 9
  conexiones falsas a 0.

### Lo aprendido

- Un dibujo puede ser correcto en el `.drawio` y engañar a la vista. La prueba que lo atrapa mide la geometría (qué
  cruza qué), no el XML; conviene que toda colocación nueva pase por ella.
- Lo que se hace sin navegador tiene que dejar la carpeta coherente: un PNG que ya no es del dibujo es peor que ninguno.
- Partir en páginas resuelve el ancho pero crea otro problema, encontrar un paso; la salida de `crear` tiene que decir
  dónde está cada uno.
- El comprobador del plugin también es código del plugin: la anotación `int | None` de F3 lo rompía en Python 3.9 y
  ninguna prueba lo veía, porque todas corren con el Python del equipo.

### Aplazado

Ocho menores de la revisión y de su pasada de correcciones, en `docs/siguiente-version.md` («Diagramas»): la línea de
una nota sobre la etiqueta de su puerta, el `.tmp` que queda si falla la relectura, `calledElement` y los errores sin
tarea en el BPMN, el bucle de dos pasos en Mermaid, `__pycache__` de las pruebas, verticales largas en la colocación por
capas, el nombre de la página tras renombrar a mano y la salida de `mermaid.py` sin argumentos.

## F3 · Precisa y sin relleno (8 de octubre de 2026)

Rama `f3-precisa-sin-relleno`, de `main` 795ec61 al merge. Versión 0.7.0-alpha.2.

### Qué cambia

- **Reglas de prosa en un solo sitio (Tarea 4).** `redaccion.py` del analista (muletillas, frases, párrafos repetidos);
  la prosa de ingeniería inversa sigue `redaccion.md`, sin lo que allí es solo del DF.
- **`as-is/datos/` (Tareas 5 y 8b).** Lo único que leen las demás skills de ingeniería inversa: inventario (con lo que
  se cita con cada record type), dependencias (y lo que queda fuera de la aplicación), hallazgos, procesos y lo que no
  se pudo verificar. Formato en `references/datos.md`.
- **`comprobar_asis.py` (Tarea 6).** Objetos inventados, certezas sin evidencia, evidencias que no llevan al anexo,
  cifras distintas de `summary.json`, marcadores y enlaces rotos, NV y preguntas sin cerrar; avisos de redacción y de
  presupuesto de palabras. La fase 8 lo exige sin errores.
- **Aplicación ficticia MNT (Tarea 7).** 44 objetos con 11 malas prácticas, 22 preguntas y un conjunto oculto de 7
  preguntas y 3 malas prácticas escrito a ciegas. Tres reglas de una aplicación común (CMN) que no está en la extracción.
- **Preguntas primero, hechos y no consejos (Tarea 8).** Cada documento empieza por las preguntas que responde; toda
  tabla con certeza lleva evidencia; sin recomendaciones.
- **Disciplina de evidencia (Tarea 8b).** Lo no verificado queda como NV, con lo que hace falta para resolverlo; nada
  se da por inexistente sin decir dónde se buscó; la definición no se toma por la ejecución; la revisión cierra sus
  preguntas. La marca de inferido pasa a 🔶.
- **Una entrada (Tarea 9, paso 3).** LEEME y el resumen ejecutivo se remitían el uno al otro y ahora son un documento;
  fuera la tabla que repetía las preguntas de cada documento.
- **Lo que encontraron las medidas.** El extractor reconoce los tipos habituales aunque la aplicación no tenga ninguno
  (con MNT, `getAiAgent` daba 27 errores); ningún script deja `__pycache__` dentro del plugin, en las cinco skills, y
  `comprobar_plugin.py` lo exige; el aviso de respuestas reutilizadas solo sale si son de hace más de una hora; `doctor`
  guarda su salida en el proyecto (`--out`) y la fase 0 dice cuándo usar `--mcp-server-name`.

### La evaluación del recién llegado (Tarea 9)

La skill documenta MNT contra el simulador; otro agente, que solo lee `as-is/` sin `extraccion/`, responde las
preguntas. «Antes» es la skill en `f3-antes` (4a7a09f, tras la Tarea 7); «después», con las Tareas 8, 8b y el paso 3.

| | Antes | Después |
|---|---|---|
| Preguntas visibles | 21/22 (falla Q-21, obligatoria) | 21/22 (Q-21 bien) |
| Preguntas ocultas | 7/7 | 7/7 |
| `evidencia.py` | falla: los CMN no salen fuera de la aplicación | bien |
| `comprobar_asis.py` | 19 errores con el de entonces (58 con el de ahora) | 0 errores, 0 avisos |
| NV registrados | — | 8 |
| Palabras (total) | 16.741 | 17.293 (+3,3 %) |
| Palabras sin líneas «Responde a» ni tablas | 7.932 | 7.122 (−10 %) |

- **Criterio: se cumple todo salvo «menos palabras que antes».** Lo que crece son las líneas «Responde a» (523 palabras)
  y las tablas, por la columna de evidencia y el «Para qué» de INVENTARIO, que piden las Tareas 8 y 8b; la prosa baja un
  10 %. Una primera medida «después», sin el paso 3, tenía 17.741 palabras (contadas igual que las de la tabla).
- **Protocolo.** Con la primera instrucción («cada elemento corto»), quien respondía resumió los tres CMN como «las
  reglas CMN_» y Q-21 contaba como fallo aunque LEEME los nombra. La instrucción pasa a pedir cada objeto por su nombre
  (`recien-llegado/README.md`) y las cifras de la tabla son las de las dos medidas respondidas con ella.
- **Q-10, ambigua en la documentación.** 09 marcaba «Por entorno: No» en las constantes porque ninguna tiene la marca
  de Appian, y quien responde concluía que ninguna cambia por entorno, aunque `MNT_URL_ERP_PRE` guarda la URL de
  preproducción. Lo introdujo la Tarea 8; la revisión de la fase lo corrige con dos columnas, «Depende del entorno» y
  «Marca de entorno». Se vuelve a medir en el punta a punta de F9.
- **El criterio de palabras lo decide Raúl.** Aceptado de forma provisional en el merge (8 de octubre); si prefiere
  recortar las preguntas de las plantillas, se hace en F4.
- Proyectos en `$PROYECTOS_PRUEBA`: `MNT-antes/`, `MNT-despues-1/` y `MNT/` (el que usan las Tareas 15 y 22).

### Lo aprendido

- Una medida con un agente que sigue la skill de punta a punta encuentra lo que las pruebas no ven: los dos informes
  dieron 17 y 18 puntos de fricción, la mitad de diagramas. Conviene repetirla al cerrar cada fase que toca una skill.
- La instrucción de quien responde también se mide: «corto» le hizo resumir nombres. Las instrucciones de las
  evaluaciones se fijan en su README y se usan iguales en «antes» y «después».
- Contar palabras sin separar lo que se añade a propósito (preguntas, evidencia) de la prosa da un criterio que castiga
  lo que la fase pide. La cifra útil es la prosa, que baja.
- Con una sola medida por lado, una diferencia de pocos cientos de palabras está dentro de lo que varía de una
  ejecución a otra.
- La batería tiene techo: 7/7 y 21/22 en los dos lados, y solo Q-21 distingue. Para las Tareas 15 y 22 hacen falta
  preguntas que «antes» falle.
- La revisión de la fase, con sondas sobre los proyectos reales, encontró lo que ni las pruebas ni las medidas vieron:
  una regresión de la propia fase (Q-10), `objetos` sin validar en el contrato de `datos/` y un error falso con los
  objetos de fuera de la aplicación.

### Aplazado

| Dónde | Qué | Tarea |
|---|---|---|
| Vía draw.io de `process-modeler.md` y `appian-diagramas-bpmn` | Un proceso de 130 nodos da un `.drawio` de 29.536 px y un PNG de 22.171 px (la skill promete 3.200); la vía draw.io no parte en tramos; «usa subprocesos» choca con «no inventes subprocesos» | 10 y 12 |
| `scripts/render_diagrams.sh`, `validate_mermaid.py` | Temporales en `/tmp`, `--batch` recorre `extraccion/`, aviso de caché de Chrome con `PUPPETEER_EXECUTABLE_PATH`; el validador reescribe sin avisar | 11 (se retiran) |
| `references/mermaid-rules.md` | Un subgraph de un solo carril se dibuja en horizontal; el diagrama por capas pasa del ancho | 11 |
| `references/bpmn-mapping.md`, `pm-template.md` | Carril «Sistema» frente a «Aplicación»; integración sin connected system como participante externo; caja de nota cortada en el PNG | 10 |
| Plantilla `08-procesos-bpmn/indice.md` | «Vista» obligatoria aunque ningún proceso lance a otro | 12 |

## F2 · Ingeniería inversa en el plugin (8 de octubre de 2026)

Rama `f2-ingenieria-inversa`, de `main` 4938606 al merge. Versión 0.7.0-alpha.1.

### Qué cambia

- **Skills solo con lo que usan al trabajar (Tareas 0 y 0b).** Las pruebas y sus datos ficticios pasan a
  `pruebas/<skill>/` y el caso de ejemplo de prototipos sale del plugin. `comprobar_plugin.py` da error si una skill
  lleva pruebas, ejemplos, un proyecto o la marca de un cliente, y `--completo --plugin` pasa las mismas pruebas sobre
  la copia del paquete.
- **La marca de cualquier cliente (Tareas 0b y 0c).** `appian-prototipos-<cliente>` pasa a `appian-prototipos`, con la
  marca estándar de Appian por defecto; la de un cliente va en `<p>/prototipo/`. `marca.py web` saca de su web los
  colores, el logo y la tipografía, y `marca.py crear`, la configuración completa (Site, perfil CSS, paleta, estados,
  gráficos y `marca-<id>.md` para quien construye) con el contraste AA ya ajustado.
- **Ingeniería inversa, solo el bloque A (Tarea 1).** Documenta sin juzgar ni rehacer. El bloque B espera a F5 en
  `docs/bloque-b/`.
- **La extracción, en el proyecto y tal cual (Tareas 2 y 2b).** `as-is/extraccion/` con rutas cortas; al repetir o
  retomar no se vuelve a pedir lo descargado. Nada se oculta (Raúl, 8 de octubre): la detección de secretos sigue,
  también en cabeceras y literales SAIL, porque un secreto escrito en la app es un hallazgo.
- **Alta en el plugin (Tarea 3).** Ingeniería inversa entra en la prueba completa y en la regla común de dudas de
  Appian, igual en las tres skills que la llevan y válida con el plugin instalado. El comprobador exige `appian-docs`
  en `.mcp.json`.
- **Revisión de la fase.** Una carpeta es de una aplicación y un entorno: con otro entorno, el extractor sale con 15
  salvo con `extract --refresh`, y avisa cuando reutiliza respuestas de otra ejecución. La orden zip del README deja
  fuera lo de desarrollo (lo comprueba `comprobar_plugin.py`) y el paso 5 de prototipos entrega el perfil CSS que
  escribe `build.py`, también con una marca hecha a mano.

### Pruebas

- `comprobar_plugin.py --completo`: 5 skills, 0 errores y 0 avisos, en el repositorio y en la copia del paquete.
- Ingeniería inversa: 89 pruebas en verde, entre ellas retomar en otra ruta, con espacios y en otro entorno.
- Scripts de `skills/` y `pruebas/`: se analizan e importan con Python 3.9.
- Galerías y plantillas: se regeneran idénticas, byte a byte. La galería de antes, construida con el kit nuevo y la
  marca del cliente del historial, solo cambia el gris del pie del visor de documentos.

### Lo aprendido

- La revisión por tarea, con agentes y varias rondas, alargó la fase. Desde F3: una revisión independiente por fase y
  las tareas pequeñas en línea (Raúl, 8 de octubre).
- La decisión de no ocultar nada llegó a mitad de fase y dejó sin objeto el saneado de la Tarea 2 y una ronda de
  correcciones. Las decisiones de datos y privacidad se toman antes de empezar una fase. Desde ahora, el alcance está
  congelado hasta F9 y lo nuevo va a `docs/siguiente-version.md`.
- La revisión de la fase vio lo que no ven las de tarea: el entorno al retomar (cruza las Tareas 2 y 3), la versión
  sin subir y la orden zip del README. Se revisa la rama entera y también la copia del paquete.
- Claude Code no actualiza un plugin mientras su versión no cambia. Cada fase que llega a `main` sube la versión
  (0.7.0-alpha.N) y F9 cierra con la 0.7.0-beta.1.
- Con el plugin instalado, las herramientas MCP se llaman `mcp__plugin_<plugin>_<servidor>__…`: los textos de las
  skills nombran el servidor, no el prefijo.
- Las restricciones globales (rutas cortas, nada fuera de `<p>`, nada oculto) se prueban ejecutando y mirando el
  disco, no buscando frases en los textos.

### Aplazado

| Dónde | Qué | Tarea |
|---|---|---|
| `references/presentation-rules.md` | «códigos internos de patrones (DAT-02)», resto del bloque B. En el plan, «… y usuarios» ya sobra | 4 |
| `scripts/detect_secrets.py` | Falso positivo con `headers: {Authorization: "Bearer " & cons!X}` en un mapa SAIL, con su prueba | 6 u 8b |
| `assets/markdown-templates/LEEME.md`, `agents/pdf-publisher.md`, `references/response-format.md` | «reingeniería» → «ingeniería inversa», y `reingenier` en `PROHIBIDO` de `test_sin_bloque_b.py` | 8 |
| `agents/ui-rules-analyzer.md` | «independientes de la tecnología… sin abrir el código original» (enfoque de reconstrucción) | 8 |
| `agents/data-modeler.md`, `agents/interface-analyzer.md` | Punteros viejos a `docs-mcp-usage.md` y caché de consultas web | 8 |
| `SKILL.md` de ingeniería inversa | El último punto de la regla común («qué conviene hacer») llega a los subagentes | 8 |
| `scripts/build_model.py` | `slugify` sin tope nombra `extraccion/procesos/`, `anexo/<tipo>/` y `08-procesos-bpmn/`: el recorte de `safe_name` y una prueba con un nombre de 150 caracteres | 8b o 12 |
| `scripts/detect_secrets.py`, `references/response-format.md` | La ubicación de un secreto en un `.json` lleva el prefijo `response.`; «(detalle en el registro de 09)» | 8b |
| `README.md` | Quien solo tiene el paquete no puede comprobar su equipo: la comprobación pide el repositorio | 23 |
| `SKILL.md` de ingeniería inversa | Usa `python3` sin «en Windows, `python`» | 24 |
| `README.md` | Requisitos de ingeniería inversa (`uv`, Dev MCP 26.5+ con rol Designer, solo en el equipo); retirar también la `appian-reverse-engineering` suelta; en «Confidencialidad», que `as-is/` lleva la extracción tal cual y se sincroniza | 25 |
| `skills/appian-functional-analyst/SKILL.md` | La descripción dice «no audita aplicaciones existentes»: «no documenta…» | 28 |
| `.claude-plugin/plugin.json`, `marketplace.json` | La ingeniería inversa, en la descripción y en las keywords | 28 o 31 |

Sin tarea en este plan, en `docs/siguiente-version.md`: lo pendiente de `marca.py` y las copias de conflicto de
OneDrive en la extracción.

Hechas en F3 las filas de las Tareas 4, 6 u 8b, 8, 8b y 8b o 12; quedan las de las Tareas 23, 24, 25, 28 y 31.
