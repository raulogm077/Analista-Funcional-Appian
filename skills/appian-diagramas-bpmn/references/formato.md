# Formato del proceso: el detalle

Lo que no hace falta en cada proceso: tramos, posiciones, datos de Appian, pestañas y el aspecto del dibujo. Lo básico está en `SKILL.md`, «Formato del proceso».

## Tramos, posiciones y datos de Appian

**Tramos, sólo si se piden.** El proceso se dibuja completo por defecto, aunque quede pequeño en el documento; el detalle se consulta ampliando la imagen o abriendo el `.drawio`. `"tramos": true` permite pedir una división explícita: si no cabe en una página (1.600 px de ancho), se dibuja una página del `.drawio` por tramo, con capas seguidas del flujo, y un PNG por tramo. Cada flujo que pasa de un tramo a otro se corta con un par de eventos de enlace: «Sigue en el tramo N: <paso>» en el tramo de origen y «Viene del tramo M: <código y paso de origen>» en el de destino. Los enlaces son del dibujo, no del proceso: `leer`, `comparar` y `bpmn` los deshacen y el `.bpmn` es uno, con todos los pasos. Un plazo o un error va en el tramo de su tarea. Si cabe en una página, no se parte. `crear` y `actualizar` dicen qué pasos lleva cada tramo, una línea por tramo («tramo N: <primer paso> – <último paso> (K pasos)»), y el nombre de cada página dice lo mismo (también tras aceptar un paso renombrado a mano).

**Posición.** `"posicion": [x, y]` en un paso es opcional. Solo la usa ingeniería inversa, cuando lee de Appian dónde está cada nodo, y tiene que venir en todos los pasos para que se use.

**Datos de Appian.** Los pone ingeniería inversa al leer un process model:
- en un paso, `nodo` (el id del nodo en Appian), `temporizador` (la expresión, en `inicio_temporizador` y `temporizador`) y `proceso_llamado` (en `llamada`);
- en un flujo, `condicion` (la expresión que decide esa salida de la puerta).

```json
{"id": "ACT-04", "tipo": "llamada", "carril": "Aplicación", "nombre": "Notificar resolución", "nodo": "7", "proceso_llamado": "Notificación de resolución"}
{"de": "GW-01", "a": "ACT-02", "etiqueta": "Sí", "condicion": "pv!completa"}
```

No se ven en el dibujo: en draw.io están en «Editar datos» del paso o del flujo, y `comparar` lista los que se cambien ahí. En el BPMN, `nodo` va en `documentation` («nodo 7»), `proceso_llamado` en `calledElement` (es el nombre del proceso llamado, con `_` en lugar de espacios y signos, no la referencia a un proceso: la otra herramienta no lo resuelve), `condicion` en `conditionExpression` y `temporizador` en `timeCycle` (en `timeDuration` si es una duración ISO 8601, como `P10D`, y en `timeDate` si es una fecha y hora).

## Un proceso con varias fases en pestañas

Cuando el proceso tiene fases o subprocesos que el cliente ve por separado (o el usuario lo pide), se entrega **un único `.drawio` con una pestaña por fase**, no un fichero por fase. El JSON lleva `paginas`, un proceso por pestaña, con el nombre de la pestaña en su `proceso`:

```json
{"proceso": "Contratación", "paginas": [
  {"proceso": "Alta", "carriles": [...], "pasos": [...], "flujos": [...]},
  {"proceso": "Evaluación", "carriles": [...], "pasos": [...], "flujos": [...]}
]}
```

- `crear` da `X.drawio` con una pestaña por fase, `X.json` con todas y un PNG por pestaña (`X-1.png`, `X-2.png`…), para poner cada fase en su apartado del DF.
- `leer`, `comparar` (también `--aceptar` y `--con`), `png` y `bpmn` trabajan sobre todas las pestañas y dicen de cuál es cada línea; `bpmn` da un `X-N.bpmn` por pestaña.
- `actualizar` dice a qué pestaña va cada cambio: `{"pagina": "Evaluación", "cambios": [...]}` (por nombre o por número), o se le pasa el libro entero, con el mismo número de pestañas. Para añadir o quitar una pestaña, se vuelve a `crear` con `--forzar` (pregunta antes).
- Un `subproceso` o una `llamada` que se llama como otra pestaña enlaza con ella: en draw.io, un clic la abre.
- Cada pestaña empieza con un inicio por cada sitio del que se llega («Viene de Trabajos previos», «Viene de Documento de alcance (salto de fase)») y termina con un fin por cada sitio al que se sigue («Sigue en Proyecto básico»).
- Una pestaña no va en tramos: si una fase no cabe, es otra pestaña.

Un `.drawio` con varias páginas que no hizo la skill (sin pestañas `pagina-N`) se lee solo por la primera; para pasarlo a pestañas, `leer` cada página por separado y `crear` el libro.

## Aspecto del dibujo

- **Tareas:** una tarjeta de 120 × 96 con el pictograma de su tipo en una placa arriba a la izquierda (persona, mano, engranaje, guion, subproceso o llamada; añil si es de usuario, verde azulado si es de sistema o script) y el nombre debajo, alineado a la izquierda. Si el nombre acaba en un código entre corchetes (`[EJ-01.001]`), el código va en una línea aparte, en monoespaciada, y si dice «nuevo» (`[nuevo paso 8]`) va en una píldora verde; `leer` devuelve el nombre entero, como siempre.
- **El tipo de una tarea** va en el estilo (`tipo=manual`), no en un marcador BPMN. Los `.drawio` de antes (con el marcador o con un aspecto anterior, sin `aspecto=lamina` en el pictograma) se leen igual y pasan al aspecto actual cuando se recolocan.
- **Adornos:** el pictograma de cada tarea (hijo de la tarea: se mueve con ella) y la cabecera de la página (título del proceso y leyenda) son imágenes sin texto. `leer` y `comparar` no los cuentan como pasos; no hace falta tocarlos.
- **El color dice qué es cada cosa:** la secuencia va en gris oscuro y un flujo que vuelve a un paso anterior (su destino queda a la izquierda), en naranja, para que los reprocesos se vean; puertas en ámbar, inicio en verde, fin en rojo, eventos intermedios en pizarra; mensajes en gris discontinuo y participantes externos en gris con borde discontinuo. Las etiquetas de los flujos van en negrita, con fondo blanco, y las notas son un papel amarillo claro con la letra normal.
- **Carriles** con el nombre en horizontal, arriba a la izquierda, alternando blanco y gris muy claro; el de la aplicación (`Aplicación`, `Sistema` o `Appian`) va en verde azulado.
- **Salidas de una puerta hacia su misma fila:** si hay otro paso en medio, van en abanico, cada una por su pasillo y más lejos cuanto más lejos está su destino, sin cruzarse ni pasar por encima de otra forma o de su texto. Si no caben en el carril sin pisar nada, se quedan como las coloca el motor.
- Los PNG los pinta el visor de draw.io: la imagen es igual a lo que se ve al abrir el `.drawio`.
- **Supuestos:** un paso con `supuesto` lleva el borde ámbar y, si es una tarea, discontinuo.
