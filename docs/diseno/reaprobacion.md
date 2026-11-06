# Cuándo vuelve a aprobación una unidad ya aprobada

Análisis para que decida Raúl (pedido el 5-nov: «analiza pros y contras de cada opción… imagínate diferentes
posibilidades… sin burocracia de más, solo la que aporte valor»). Su criterio provisional, dicho a Codex el mismo día:
«si lo que llega cambia lo que hay que construir se debe aprobar, pero si no, lo valida la IA». No se ha cambiado
nada: el punto está en `siguiente-version.md` §2. Lo hizo un workflow de seis
agentes (mecanismo, 16 escenarios, tres revisores con criterios distintos y una síntesis) y lo revisó la sesión que dirige
la campaña. El detalle completo está en `Pruebas-plugin/metodo-20261104/revisiones/reaprobacion.json`, fuera del
repositorio.

## El problema

El jefe de proyecto (JP) aprueba una unidad (EV-nn) con su alcance y su coste, y entonces se escriben sus issues. Hoy, si
después llega un informe de impacto con `Cambio: EV-nn` (o un punto «Pendiente»), la unidad «ha crecido»: no se pueden
regenerar las issues ni marcarla Construida hasta que el JP vuelva a aprobar con una fuente (`cambios.md` §1;
`unidades.py`, `Contexto.crecida()`). El disparador es la etiqueta del informe, no lo que cambia. Una versión nueva, un
retoque del técnico sin informe o un informe sin `Cambio:` no lo disparan.

En la campaña ha pasado tres veces:

| Caso | Qué cambió | ¿Cambia alcance o coste? | Qué hizo el plugin |
|---|---|---|---|
| FU-08 | HU-02 aparecía validada y dependía de una pregunta abierta: se reescribió como pendiente, con su supuesto en el técnico | Cambia lo validado y su texto; no está demostrado que cambie lo construido: ISS-05 ya pedía que el empleado viera «Cerrada» | Pidió reaprobar, porque el mecanismo lo exige con la etiqueta |
| FU-10 | Las cuentas de prueba, al técnico §0 | No | La sesión lo registró sin `Cambio:` a propósito, y no pidió reaprobación (no consta qué leyó el JP) |
| FU-11 | El origen de datos de desarrollo pasa a `jdbc/Appian`: sale un objeto de §13 y cambia cómo se crean las tablas | El funcional no; el trabajo técnico, sí (cuánto, sin medir) | Pidió reaprobar. Un «de acuerdo» más del JP |

FU-10 y FU-11 no son iguales (FU-11 cambia el trabajo técnico), pero la diferencia de trato la puso la etiqueta, no lo
que cambiaban.

## Las opciones

| Opción | Pros | Contras |
|---|---|---|
| **1. Como está** | Sin código. Todo informe de la unidad pasa por el JP y deja una fuente. En FU-08 hizo que el JP viera una corrección de lo validado | Trata igual una errata que un campo nuevo. Depende de la etiqueta: FU-10 pasó sin pedir reaprobación. Una sesión desatendida se para toda la noche por una errata. No ve los cambios de coste |
| **2. «Sin efecto», con topes y aviso (recomendada)** | Quita la reaprobación de lo que no cambia el encargo y no toca nada validado (un literal en una pieza sin 🔒, un supuesto confirmado, las cuentas de prueba). Bloquea donde lo marcan los topes. Deja una línea que el JP puede ver, sin lista que cerrar. Pequeña y sin IA en el script | La primera clasificación es del analista. Los topes dependen de que las demás marcas (pendiente, alcance, 🔒) estén bien puestas: no son una comprobación independiente de su juicio. Una aclaración de regla o un cambio de coste mal declarados pasarían. La línea dice qué informes llegaron después de aprobar, no que el JP los haya visto. Una errata en una pieza 🔒 seguiría bloqueando |
| 3. Por lo que cambia en las issues, por script | Determinista, igual de noche. Detecta piezas u objetos nuevos aunque falte la etiqueta | Lo más caro (dos scripts y sus pruebas). Comparar huellas no separa una errata de un cambio de comportamiento, y contar piezas deja pasar justo FU-08. No ve el coste |
| 4. Aviso sin bloqueo para lo menor | No para a nadie y deja constancia | Alguien tiene que decidir qué es menor. Si el aviso es una lista que cerrar, es otro trámite que se acumula |

Los tres revisores preferían la 3 combinada con la 4. La síntesis discrepa en el método, no en el fin: la 3 no
distingue lo que importa sin entender el texto, y eso ya no es un script. Por eso recomienda la 2.

## La opción 2, en concreto

Concreta el criterio provisional de Raúl, pero añade cosas que él no dijo y que son propuestas por contrastar: una
pregunta fija en el informe, una línea marcada, los topes del script, la línea del estado y que de noche una sesión no
pueda declarar «sin efecto» por su cuenta. Su criterio («si no cambia, lo valida la IA») no pone esa última restricción.

- El informe de impacto lleva una pregunta fija: «¿Cambia lo que se construye o su esfuerzo?». Si la respuesta es que no,
  lleva la línea `Efecto: sin cambio de alcance ni coste`.
- El script acepta esa línea sin reaprobar **solo si** el informe no tiene puntos «Pendiente», ni puntos de alcance
  (ALCANCE±) o que requieran aprobación, ni toca una pieza validada (🔒). Si no, como hoy.
- Si la acepta, regenera las issues y deja una línea en `estado` y en el paquete de F9: «Cambios que el JP no ha visto:
  FU-nn». Desaparece sola en la siguiente aprobación: no hay nada que cerrar.
- Una sesión desatendida no puede declarar «sin efecto» por su cuenta: de noche solo avanza con informes que ya declaró
  una persona.
- Sobre una unidad en curso, todo informe lleva `Cambio:`, para que no vuelva a pasar lo de FU-10.

Cómo se comporta:

| Escenario | Con la opción 2 |
|---|---|
| FU-08 (corregir una historia validada) | Igual que hoy: toca una pieza 🔒 y deja una pregunta abierta, así que se reaprueba |
| FU-10 (cuentas de prueba) | Pasa sin parar, con la línea |
| FU-11 (origen de datos) | Pasa si el analista lo declara sin efecto, y eso es discutible: cambia el trabajo técnico. Es justo el tipo de caso que depende de su juicio |
| Una errata o un literal del cliente | Pasa con la línea si la pieza no está validada; en una pieza 🔒, bloquea como hoy |
| El cliente confirma un supuesto con el que ya se construye | Pasa: el supuesto queda como hecho |
| El cliente contradice un supuesto, o pide un campo nuevo | No se puede declarar «sin efecto» con honestidad. Si se hiciera por error, lo para el punto de alcance o aprobación solo si está bien marcado |
| Sesión desatendida de noche | Sigue si una persona ya declaró «sin efecto»; si no, se para como hoy |
| Cambia el coste sin cambiar funciones, o se aclara una regla | Ningún automatismo lo ve: depende de la respuesta honesta a la pregunta y de que el JP mire la línea |

Lo que habría que tocar, estimado sin implementarlo: `unidades.py` (`crecida()` lee la línea y los topes, unas 30 a 50
líneas), `proyecto.py` (la línea del estado y de F9), `cambios.md` §1, la plantilla del informe en `actualizacion.md` y
una frase en F8, con sus pruebas: sin efecto que no bloquea, sin efecto con un punto pendiente que sí, con una pieza 🔒
que sí, la línea que se borra al reaprobar y la sesión desatendida que no puede declararlo. No toca `issues.py` ni las
huellas. Antes, comprobar en el código que se puede saber qué piezas estaban 🔒 al aprobar: si no, ese tope se queda en
los puntos pendientes, de alcance o de aprobación.

Límites: hay tres casos reales; los demás escenarios son supuestos. No se ha medido cuánto cuesta de verdad cada
reaprobación ni cuánto trabajo cambió FU-11. Revisión de Codex (5-nov), aceptada: corrigió las premisas de FU-08, FU-11
y de lo que pasa con los topes.

## Con ejemplos concretos (Raúl, 5-nov)

Raúl pidió ver cómo se comporta cada opción con cambios reales antes de decidir: un label, un usuario en un grupo, la
visibilidad de un record, el color de un botón, mover un componente, campos nuevos, una función, una integración, un
parámetro, una notificación y una validación. Están abajo, con otros que han salido en las pruebas.

### Tres preguntas distintas

Al repasar los ejemplos sale que «reaprobar» mezcla tres cosas que no son lo mismo:

1. **¿Lo tiene que ver el cliente?** Cambia algo que el cliente validó: lo que hace la aplicación, un texto o una regla
   que vio (una pieza 🔒). Quien responde es el cliente, revalidando, y para eso ya está F2 (la pieza deja de estar 🔒 y
   entra en la próxima validación). No es cosa del JP.
2. **¿Lo tiene que aprobar el JP?** Cambia lo que se compromete: el alcance (piezas que entran o salen), el esfuerzo de
   forma apreciable o el riesgo (datos y su estructura, quién ve o hace qué, otros sistemas, el despliegue).
3. **Si no es ninguna de las dos**, lo valida la IA (el analista): es coherencia técnica, sin efecto en lo que se
   compromete ni en lo validado. Es el criterio provisional de Raúl.

La opción 2, tal como estaba arriba, mezcla la 1 y la 2: una errata en una pieza 🔒 bloquea a la espera del JP, cuando
lo que hace falta es que la vea el cliente. Y el momento importa: con la unidad Abierta todo entra antes de aprobar;
con la unidad Construida, cualquier cambio en Appian es otra unidad (F3 o F4) con su aprobación. Aun así, hoy la
reaprobación salta también con la unidad Construida (E7: `issues.calcula` admite Construida y llama a `crecida`).

### Los ejemplos

«Hoy» es lo que hace el plugin, que pide al JP volver a aprobar siempre que el informe lleve `Cambio:`. «Propuesta» es
lo que haría la propuesta revisada de abajo.

| # | Cambio, con la unidad aprobada y en construcción | ¿Cliente? | ¿JP? | Hoy | Propuesta |
|---|---|---|---|---|---|
| 1 | Cambiar el texto de un label | Solo si la pantalla estaba validada | No | Reaprueba | La IA lo valida; si la pantalla estaba 🔒, la pieza vuelve a la próxima validación del cliente, sin parar |
| 2 | Meter un usuario en un grupo | No | No | Si llega como informe, reaprueba | No es un cambio de la unidad: es operación del entorno (una persona, por el proceso del cliente). Solo si cambia quién pertenece a un perfil es la fila 3 |
| 3 | Cambiar la visibilidad de un record (quién ve qué filas) | Sí | Sí: seguridad | Reaprueba | Reaprueba y el cliente lo revalida |
| 4 | Cambiar el color de un botón | No (salvo marca validada) | No | Reaprueba | La IA lo valida |
| 5 | Mover un componente en una interfaz | Solo si el prototipo estaba validado | No | Reaprueba | Como la fila 1 |
| 6a | Un campo nuevo que el negocio ve o rellena | Sí | Sí: alcance | Reaprueba | Reaprueba y el cliente lo revalida |
| 6b | Un campo técnico (auditoría, una clave) antes del primer pase | No | Sí, por el tope de técnico §3 | Reaprueba | Va al JP por el tope de técnico §3, aunque sea pequeño (los topes son gruesos a propósito) |
| 6c | Un campo en una tabla que ya tiene datos en producción | No | Sí: datos y despliegue | Es otra unidad (lo construido ya pasó) | Otra unidad, con su aprobación |
| 7a | Una función nueva que saca lógica que ya existe (refactor) | No | No | Reaprueba | La IA lo valida, con la regresión de lo que la usa |
| 7b | Una función nueva que añade una regla de negocio | Sí | Sí: alcance | Reaprueba | Reaprueba y el cliente lo revalida |
| 8 | Una integración nueva | Si cambia lo que hace | Sí: alcance, coste y riesgo | Reaprueba | Reaprueba siempre |
| 9 | Un parámetro nuevo en una función, mismo comportamiento | No | No | Reaprueba | La IA lo valida, con la regresión de lo que la usa |
| 10 | Una notificación nueva en un punto del proceso | Sí | Sí: alcance (y destinatarios con datos personales) | Reaprueba | Reaprueba y el cliente lo revalida |
| 11a | Una validación que el funcional ya pedía y faltaba en el técnico | No | No | Reaprueba | La IA lo valida: es construir lo acordado |
| 11b | Una validación nueva que no estaba acordada | Sí | Sí: cambia lo acordado | Reaprueba | No es «sin efecto»: JP y cliente |
| 12 | Cambiar el valor de una regla (el límite de 3.000 € a 2.500 €) | Sí | Sí: cambia lo acordado, aunque no cueste más | Reaprueba | No es «sin efecto»: JP y cliente |
| 13 | Cambiar quién puede hacer una acción | Sí | Sí: seguridad | Reaprueba | Reaprueba y el cliente lo revalida |
| 14 | El cliente confirma un supuesto con el que ya se construye | Ya lo hizo | No | Reaprueba | Pasa: el supuesto queda como hecho |
| 15 | El cliente contradice un supuesto | Sí | Sí: cambia lo acordado | Reaprueba | No es «sin efecto»: JP y cliente |
| 16 | Errata en el documento, sin cambio en la aplicación | No | No | Reaprueba | La IA lo valida |
| 17 | Ajuste técnico que el funcional ya pedía (la vista de consulta, DT-11) | No | No | Hoy se esquiva sin `Cambio:` y luego cuenta para otra unidad (E7) | La IA lo valida y queda en su unidad, si no toca técnico §3, §4 o §10; FU-18 tocaba §4 y va al JP por el tope |
| 18a | Cuentas de prueba (FU-10) | No | No | Pasó sin `Cambio:` | La IA lo valida |
| 18b | Origen de datos de desarrollo (FU-11) | No | Solo si cambia el esfuerzo de forma apreciable | Reaprueba | Lo decide el umbral de esfuerzo |
| 19 | Algo que el Dev MCP no puede hacer y lo hace una persona: más esfuerzo, mismo funcional | No | Sí, si pasa del umbral | No lo ve nadie | Lo decide el umbral de esfuerzo |
| 20 | Quitar una funcionalidad | Sí | Sí: alcance | Reaprueba | Reaprueba y el cliente lo revalida |
| 21 | Rendimiento: un índice equivalente | No | No, salvo esfuerzo | Reaprueba | La IA lo valida si no toca técnico §3; una sincronización que cambia qué datos se ven y cuándo es de riesgo: JP |
| 22 | Un defecto que encuentra el QA antes de cerrar la unidad | No: no cambia lo acordado | No | No pide nada (F8: se arregla en la aplicación) | Igual |
| 23 | Corregir el técnico tras construir, sin tocar Appian (E7) | No | No | Caduca las verificaciones de issues hechas | No debería caducarlas: ver «Después de construir» |

### Qué errores comete cada opción

| Opción | Aprueba sin necesidad (burocracia) | Deja pasar lo que debía verse (riesgo) |
|---|---|---|
| 1. Como está | Las filas 1, 4, 5, 7a, 9, 11a, 14, 16 y 21: casi la mitad de los ejemplos | Lo que llega sin `Cambio:` (18a, 17) y el esfuerzo que nadie declara (19) |
| 2. Como estaba arriba | Las filas 1 y 5 con la pieza 🔒, la 12, y lo que una sesión desatendida no puede declarar | Un esfuerzo o una regla mal declarados (es juicio del analista) |
| 3. Por script | Toda diferencia de objetos: 1, 4, 5, 9 y 21 bloquean igual que una integración | La 12 pesa lo mismo que una errata (es una constante que cambia); el esfuerzo (19) no se ve en los objetos |
| Propuesta revisada | Ninguna de la lista, si el analista clasifica bien | Lo mismo que la 2: depende del juicio, con topes que lo acotan y la línea que ve el JP |

### La propuesta revisada

- **El informe de impacto responde las tres preguntas.** Con la 1, sus piezas dejan de estar 🔒 y van a la próxima
  validación del cliente (como en F2), sin parar la construcción. Con la 2, el JP aprueba (como hoy). Si ninguna, lleva
  `Efecto: sin cambio de alcance, esfuerzo ni riesgo` y lo valida la IA.
- **Topes que el script comprueba** (no son juicio): no se acepta «sin efecto» si el informe tiene puntos de alcance
  (ALCANCE±), «Pendiente» o que piden aprobación, ni si cita una DT o pieza de seguridad, datos o integraciones. Hay que
  comprobar en el código qué de eso se puede saber por las piezas citadas; lo que no, lo declara el analista y se ve en
  la línea del JP.
- **Umbral de esfuerzo**: el JP aprueba si el cambio añade una issue o, según la estimación del analista, más de media
  jornada. Es un número para que la pregunta tenga respuesta, no una medida exacta.
- **Una línea para el JP**, sin lista que cerrar: «Cambios validados por la IA desde tu aprobación: FU-nn». Se borra sola
  en la siguiente aprobación.
- **El ajuste se queda en su unidad**: un informe «sin efecto» lleva `Cambio: EV-nn` y no la hace crecer, así que lo de
  E7 (FU-17 y FU-18 contados para EV-02) no vuelve a pasar.
- **Sesión desatendida**: con el criterio de Raúl («si no cambia, lo valida la IA»), puede declarar «sin efecto» sola.
  Para acotarlo, solo en los tipos de cambio de la tabla que la propuesta da a la IA. Ante la duda, se para como hoy.

**Después de construir.** Corregir el técnico de una unidad Construida sin tocar Appian (fila 23) hoy cambia la versión
de sus issues y caduca su verificación y su QA: en E7, cuatro issues de EV-01 se reverificaron por un cambio de
redacción y por la fila de §14 de la unidad siguiente. Propuesta: que la versión de una issue cuente lo que se verifica
(sus objetos y lo que se espera de ellos) y sus escenarios, no el texto de las notas. Un criterio que cambia sigue
caducando el QA, porque cambia su escenario.

**Lo que cuesta**: lo de arriba (`unidades.py`, la plantilla del informe, `cambios.md` y una frase en F8), más la
separación de la pregunta 1, que reutiliza lo de F2, y, si se acepta, la versión de las issues en `issues.py`. Unas
cuantas pruebas por cada tope. Sin IA en los scripts.

## Lo que decide Raúl

1. **Separar «lo ve el cliente» de «lo aprueba el JP».** Recomendado: es lo que quita las aprobaciones de más sin perder
   lo que el cliente validó.
2. **La propuesta revisada, entera o por partes.** Recomendada entera. Lo mínimo útil serían los topes con la línea del
   JP y que el ajuste se quede en su unidad.
3. **La sesión desatendida.** ¿Puede declarar «sin efecto» sola en los tipos que la tabla da a la IA? La propuesta dice
   que sí, por su criterio; la versión anterior decía que no.
4. **El umbral de esfuerzo.** Propuesto: una issue más o media jornada. Otro número vale; lo que hace falta es uno.
5. **Después de construir**: que una corrección de redacción no caduque verificaciones ni QA.
6. **No cambiar nada por ahora**, sabiendo que la mitad de los ejemplos seguirán pidiendo un «de acuerdo» del JP.

## Lo que se aplicó (6-nov)

Raúl eligió aplicar la propuesta revisada, el umbral de «una issue nueva o más de una jornada» y que una sesión
desatendida declare «sin efecto» en los tipos de la lista. Implementado en `unidades.py` (`sin_efecto`, `crecida`,
`validados_ia`), `issues.py` (unidad Construida) y `proyecto.py estado` (la línea del JP), descrito en `cambios.md` §1
«Sin efecto», con `pruebas/appian-functional-analyst/test_sin_efecto.py`.

Ajustes tras la revisión de Codex, aceptados: cambiar una regla acordada o lo que usan otros no es «sin efecto» aunque
no cueste más (filas 11b, 12 y 15); los topes leen también «T §n» y «Encaja en», no cuentan puntos descartados y, con
columna «Cambio», solo los de la unidad; con la unidad Construida, un fallo de QA conocido sigue contando aunque cambie
la versión; y, con la unidad Construida, la verificación anterior solo sigue valiendo si lo único que cambió es §12 o
§15 del técnico (abajo): lo pedía Codex y lo exigían las pruebas que ya había (`test_secuenciacion.py`).

**Lo que dio el caso real.** Con los dos ajustes de la campaña (FU-17 y FU-18, de E5 y E8) marcados «sin efecto», los
topes los mandan al JP: FU-17 toca técnico §3 y §4 y una DT de datos; FU-18, técnico §4. Es el lado seguro, pero en esta
campaña la regla no habría quitado esas dos aprobaciones. Si resulta demasiado grueso, la alternativa es que citar esas
secciones sea un aviso en la línea del JP en vez de un tope: decide Raúl con más casos.

**Las piezas validadas (🔒).** Aplicado como se aprobó, tras corregir un primer intento que lo dejaba como estaba (lo
señaló Codex: la protección anterior era lo que había que alinear). Un retoque «sin efecto» sobre algo 🔒 no espera al
cliente: se aplica, la pieza pasa a ✅ y vuelve a la próxima validación del cliente; `comprobar.py` ya no pide
«Requiere: Sí (🔒)» en un informe «sin efecto» y comprueba que la pieza deje de estar 🔒 (`actualizacion.md` §3.4 y §5).
Si el cambio lo pidió o aprobó el propio cliente («Requiere: Sí (🔒)», ✔), sigue 🔒 y no pasa además por el JP: era
una doble aprobación. Un cambio de alcance, de seguridad o de datos sigue pidiendo decisión.

**Con la unidad Construida, acotado.** La primera versión aceptaba la verificación anterior ante cualquier cambio del
texto del técnico; Codex demostró, con el técnico real del proyecto de formación, que una instrucción de §7 («el filtro
se vincula a fechaFin») pasaba por redacción. Ahora solo quedan fuera de la huella de estructura lo que el técnico dice
en §12 (operación) y §15 (pendientes): una nota allí no caduca la verificación; cualquier otra línea, sí
(`test_sin_efecto.py`, la pareja con contenido real).
