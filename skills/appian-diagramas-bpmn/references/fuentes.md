# Sacar el proceso de las fuentes y del diagrama aprobado

Se lee cuando el proceso sale de reuniones, transcripciones, actas, notas o un DF, y no de un proceso ya descrito por quien llama.

## Antes de dibujar

- Si el proyecto lleva análisis funcional (hay `analisis/funcional.md` o el usuario lo quiere), el proceso lo describe `appian-functional-analyst`: sigue su paso de diagramas y vuelve a la skill para dibujarlo.
- Si el usuario solo quiere el dibujo, descríbelo tú: primero el diagrama aprobado, si lo hay («Partir de lo ya aprobado»); luego las fuentes, de la más reciente a la más antigua, y cada supuesto marcado.
- Fija qué lo dispara, qué cosa trata (una solicitud, un expediente, un pedido), en qué resultados acaba y qué queda fuera. Si a mitad del proceso cambia la cosa que se trata (un lote mensual frente a cada expediente del lote), es otro proceso o un subproceso. Describe primero el camino normal de principio a fin y después, paso a paso, qué puede salir distinto.

## El lenguaje hablado

- **Esconde el proceso.** Una frase sin sujeto («se revisa y se sube») no dice quién lo hace: el carril es un supuesto. «Si», «cuando» y «salvo que» anuncian una puerta; «normalmente» o «a veces», una puerta cuya otra salida nadie ha contado, que queda como pregunta; «luego lo mira el jefe», un cambio de carril; «el sistema» sin nombre, un sistema por confirmar.
- Una transcripción que no se entiende (por ejemplo, la de Teams en inglés de una reunión en español) no es una fuente: dilo en la respuesta y no saques de ella pasos ni perfiles.
- Los nombres de sistemas de una transcripción automática no son fiables (un gestor documental puede llegar como «hashtag» o con tres grafías). Tómalos del apartado «Sistemas» del DF; sin DF, escríbelos como se oyen, sin adivinar la grafía, con «Supuesto: nombre por confirmar».
- Una demo enseña solo lo que se ejecutó ese día: lo que no se llegó a ejecutar (una subida, un justificante, un aviso) va con «Pendiente de validar».
- Si dos fuentes se contradicen (un dato editable en todos los pasos en una reunión y solo al final en otra posterior), gana la más reciente y la nota del paso cita las dos, con su fecha.
- Sin DF, el alcance sale de las propias reuniones: la que lo fija («la fase 1 llega hasta…»), con su fecha, va en la nota del inicio, como el «Fuera del alcance» de un DF. Los pasos de otras fases que se comenten no se dibujan.
- Un ajuste pedido después de la última versión del DF o de la ejecución controlada, que ningún DF recoge todavía (una acción nueva fuera del flujo, un campo que deja de ser editable), va en una nota del paso al que afecta, con «Pendiente de validar (sin DF)», no como paso ni como vuelta atrás.

## La respuesta

Dice de qué fuentes sale el proceso y lista los supuestos y lo pendiente de validar. Si no hay diagrama aprobado, lo mismo queda en `supuestos-X.md`. Lista también, por cada puerta, la salida que ninguna fuente explica, como pregunta para repasarla con el usuario («¿Y si la solicitud no está completa?»).

Lo que no salga de forma explícita de las fuentes (quién hace una tarea, el orden de dos pasos) es un supuesto: va en el campo `supuesto` del paso, con el texto de lo que se supone. El paso sale con el borde ámbar (discontinuo en una tarea) y `crear` y `actualizar` lo listan para confirmarlo con el usuario.

## Partir de lo ya aprobado

Busca en la carpeta del proyecto (y en la carpeta de la que cuelga) un diagrama ya aprobado del mismo proceso: `.vsdx`, `.vsd`, `.drawio`, `.bpmn`, un DF en Word o imágenes de un DF anterior. Si no lo encuentras, la respuesta lo pide, si existe, con la ruta cuando las fuentes lo citan («está en el DF», «las rutas que indica el DF») o su cabecera la da. Si puedes esperar la respuesta del usuario, pídelo antes de dibujar; si no (el encargo pide el diagrama sin más), dibuja y empieza la respuesta con «Borrador sin el DF», que no se da por bueno hasta contrastarlo.

**Primero, ¿es la referencia?** Lee su fecha en la portada, en el control de versiones y en el bloque de aprobación; si no coinciden, vale la más reciente, y si el bloque de aprobación está vacío, dilo en la respuesta. Compárala con la de las fuentes y di en la respuesta cuál de estos dos casos aplica, antes de dibujar:

- **Las fuentes son posteriores y rediseñan el proceso** (un evolutivo, otra fase, un paso o una revisión que el aprobado no tiene, otros sistemas o perfiles): el aprobado es la versión anterior, no la referencia. Dibuja lo que dicen las fuentes; toma del aprobado los nombres del cliente (perfiles, sistemas, estados) y lo que las fuentes no contradicen; donde se contradicen, gana la fuente posterior y la nota cita las dos; marca con «Pendiente de validar» lo del aprobado que las fuentes ya no mencionan y pide el DF de la versión nueva.
- **Si no**, el aprobado es la referencia. Pregunta una vez si lo es y parte de él:
  1. Pasa su contenido al JSON de la skill: un `.vsdx` o un `.bpmn`, con `importar`; un DF, a mano, con los pasos, perfiles, puertas, inicios y fines, y los códigos del cliente.
  2. Usa las fuentes posteriores (reuniones, demos) solo para lo que ha cambiado desde que se aprobó. Lo que no está en el diagrama aprobado lleva una nota «Pendiente de validar: no está en el diagrama aprobado».
  3. Si las fuentes contradicen el diagrama aprobado, gana el diagrama aprobado y la contradicción se dice en la respuesta.

No copies el paso a paso de un DF como tareas (uno de RPA o técnico describe cada clic o cada documento): las tareas seguidas de un mismo sistema o perfil van en una caja, con lo que incluyen en la nota, aunque el DF las dibuje separadas, salvo que el negocio las vea como pasos distintos («Tareas seguidas», en `buen-proceso.md`). El código del DF va entre corchetes.

En los dos casos, con el DF a mano:

- Cada duda que las fuentes dejan abierta («lo revisamos y te decimos») se busca en su paso a paso: la nota cita lo que dice o la contradicción, no un «por confirmar».
- Su «Fuera del alcance» (tipos de expediente, importes, casos excluidos) va en una nota del paso que filtra o, si no lo hay, del inicio: las reuniones no suelen repetirlo.

## Importar un Visio o un BPMN

```bash
python3 <skill>/scripts/diagrama.py importar aprobado.vsdx -o /tmp/aprobado.json   # o un .bpmn
```

Da el JSON de la skill: pasos con su tipo (por el patrón de cada forma: Task, Gateway, Start Event, End Event, Collapsed Sub-Process, Text Annotation… también en español), su carril (el carril que los contiene) y su nombre; flujos con su etiqueta; un pool o carril sin pasos con el que se cruzan mensajes, como participante externo; y las notas unidas a un paso. Los códigos (`ACT-`, `GW-`, `EV-`) van de izquierda a derecha; un `.bpmn` exportado por la skill conserva los suyos. Un Visio con varias páginas da un proceso por página (`paginas`). Avisa de lo que no puede pasar: una forma que no es de BPMN, un conector suelto, un paso fuera de cualquier carril (va al primero). Un `.vsd` antiguo se abre en Visio y se guarda como `.vsdx`.

El tipo de una puerta que no sea exclusiva, de una tarea que no sea de usuario o de un evento intermedio no siempre se lee del patrón de Visio: repásalos en el JSON antes de `crear`.

## Leer un DF en Word (`.docx`)

También es un ZIP. El flujograma es una imagen de `word/media/`: la que sigue al pie «Flujo de Alto Nivel To-Be» (o el que corresponda) en `word/document.xml`. La tabla del paso a paso da cada paso y su perfil, y el control de versiones, la fecha con la que comparar las fuentes.

## Comparar con el diagrama aprobado

```bash
python3 <skill>/scripts/diagrama.py comparar X.drawio --con aprobado.vsdx   # o un .json, un .drawio o un .bpmn
```

Empareja los pasos por nombre (sin mayúsculas, tildes ni códigos del cliente) o, si no, por un nombre parecido del mismo tipo de forma, y separa los errores (perfil equivocado, paso, flujo o participante que falta) de las diferencias de forma (otro tipo de tarea, otra etiqueta, un nombre parecido) y de lo que el diagrama añade. No toca nada. Una referencia con varias páginas se compara por la que se llama como el proceso. Con esa lista, la respuesta da una tabla por punto: qué dice el aprobado, qué dice el generado y cuál acierta, y cuenta lo añadido por fuentes posteriores.
