# Un fallo de QA visto a mano

Análisis para que decida Raúl (5-nov: «esto tenemos que analizarlo bien, porque no me termina de encajar; explícame por
qué haces esa recomendación y plantéate si es lo correcto para este flujo, con pros y contras»). El punto está en
`siguiente-version.md` §2. No se ha cambiado nada.

## El problema, acotado

El QA de una unidad repite sus escenarios con guiones (`qa.py repetir`) y deja el resultado en `qa/<U>/resultado.json`.
Ese fichero es lo que miran `indice.py issues` (un escenario que falla devuelve su issue a pendiente),
`proyecto.py … construida` y el paso 2 de F9. Lo que no está ahí, no existe para el método.

Hay escenarios que no pueden llevar guion: lo que SAIL CLI no hace o no ve. En esta campaña:
- descargar un documento (el certificado de HU-09.2);
- un correo que llega a un buzón (AV-01 a AV-03);
- un proceso que arranca a una hora (HU-08);
- un contador que depende de todo el entorno (HU-04.4);
- la maquetación y el aspecto.

Esos escenarios los mira una persona. Si lo que ve **pasa**, no hay problema: quedan como «sin guion» y
`construida` lo avisa. El problema es cuando ve que **falla**. Hoy ese fallo solo está en el informe del QA. La issue
sigue «hecha» y la unidad se puede marcar Construida con un fallo conocido. Con HU-09.2 pasó en la primera pasada:
solo lo paró quien dirigía la campaña, porque leyó el informe.

El hueco es estrecho. Existe solo entre que la issue está hecha y la unidad Construida. Después, un fallo visto en la
aplicación es un defecto y va por F4 (lo que se probó en E7).

## Las opciones

| Opción | Cómo funciona | Pros | Contras |
|---|---|---|---|
| A. Entrada manual que cuenta | `qa.py` anota el escenario en `resultado.json`: resultado, motivo, quién lo vio y cuándo, marcado «a mano». Un «falla» a mano devuelve la issue a pendiente, igual que un guion | Un fallo conocido bloquea como cualquier otro. Una sola fuente para `issues`, `construida` y F9. Pequeña: una orden de `qa.py` y que `issues` lea el campo. Sin fichero nuevo | Un «pasa» a mano no se puede repetir solo: vale lo que diga la persona, con fecha. F9 lo repite todo «sin IA» y estos no: tiene que enseñarlos aparte. Se puede usar mal, para no escribir un guion que sí se podía |
| B. Guion «por terminar» | QA escribe el guion hasta el paso que falla y lo deja «por terminar» | Lo que se puede automatizar queda automatizado | «Por terminar» significa que el guion está incompleto, no que la aplicación falla: por diseño no reabre la issue. La unidad se cierra igual. Mezcla «falta trabajo de QA» con «la aplicación falla» |
| C. Solo el informe | QA lo escribe en su informe; lo lee quien marca la unidad | Nada nuevo | Depende de que alguien lea el informe. Es lo que falló, y de noche o con IA no lo lee nadie |
| D. Siempre un defecto por F4 | Un fallo a mano se cataloga como aviso y sigue F4 | Lo prueba F4 y deja traza | Para un fallo dentro de una unidad que aún se construye, F4 es demasiado: abrir otra unidad y otra aprobación por algo que F8 arregla en la misma issue. Es la burocracia que no queremos |
| E. Que `construida` lea el informe | Un script busca «falla» en el informe del QA | Sin estado nuevo | Leer texto libre es frágil: un «no falla» o un fallo descrito con otras palabras la engaña |

## Por qué recomendaba la A, y si encaja

Lo que tiene que cumplir el flujo es esto: **un fallo conocido no se pierde entre el QA y el cierre de la unidad**. Solo la
A lo garantiza sin depender de que alguien lea, y es la que menos añade. Las otras fallan en lo esencial: la B no
bloquea, la C depende de leer, la D es desproporcionada y la E es frágil.

Lo que no encajaba, y hay que resolver antes de hacerla:

1. **Cómo se quita un «falla» a mano.** Con un guion, se arregla y el guion pasa. A mano, alguien lo vuelve a mirar
   y anota «pasa», con su nombre y la fecha. Es una declaración, no una prueba repetible. Es igual de válida que la
   primera vez que lo miró, pero F9 tiene que distinguirla.
2. **Que no se use para no escribir guiones.** La entrada a mano pide un motivo de por qué no hay guion. El QA lo dice ya en su
   informe; aquí quedaría junto al resultado. No hace falta otro control.
3. **Quién la escribe.** La sesión de QA, cuando una persona le dice lo que vio, o la propia persona con la orden. Es
   lo mismo que hoy con «sin guion»: la persona mira, el registro lo deja la orden.
4. **Que no sea otra lista que cerrar.** Solo se anota lo que alguien miró. No pide anotar todos los «sin guion»: los que
   nadie ha mirado siguen como hoy, con su aviso en `construida`.

## Lo que decide Raúl

1. **La A con esos cuatro límites** (recomendada). Un «falla» a mano bloquea la issue como un guion. Un «pasa» a mano
   queda con quién y cuándo. F9 los enseña aparte, como mirados a mano y no repetidos.
2. **La C**, dejarlo como está. Se asume que un fallo visto a mano depende de que alguien lea el informe.
3. **Otra**: por ejemplo, la A solo para «falla», sin registrar los «pasa» a mano.
