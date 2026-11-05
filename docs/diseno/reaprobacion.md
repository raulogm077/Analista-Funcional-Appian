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

## Lo que decide Raúl

1. **No cambiar nada por ahora.** Sin cambio de código; el coste de operación (los «de acuerdo» del JP) no está medido.
   Las erratas, los supuestos confirmados y los ajustes de entorno seguirán pidiendo un «de acuerdo».
2. **La opción 2** (recomendada). Si se elige, ¿puede una sesión desatendida declarar «sin efecto» por sí sola? La
   propuesta es que no.
3. **La opción 3 completa.** Lo más fiable sobre el papel y lo más caro, y no resuelve FU-08 ni las aclaraciones de regla.
