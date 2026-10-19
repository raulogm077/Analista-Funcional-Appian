# Lecciones aprendidas: el DF del cliente

Lo que se aprendió en la rama `yaroslav/plantilla-DF-cliente` (16–19 de octubre de 2026), sobre todo al llevar un caso
real de principio a fin: 16 fuentes, el DF del cliente sobre su plantilla y un prototipo. Cada lección dice qué pasó y
qué se cambió por ello. Sin datos del cliente: los ejemplos son genéricos. El detalle, en el §3 del plan.

## Las fuentes

1. **Las transcripciones de Teams llegan en Word, no en `.vtt`.** Sin reconocerlas, salían como documentos, sin duración
   ni hablantes, cada una con un formato distinto. → `leer_fuentes.py` las reconoce y pasa toda transcripción a un
   formato único (`[00:14:32] Hablante: texto`).
2. **La fecha del fichero no es la de la reunión.** Una reunión cuyo nombre no llevaba fecha tomaba la de la descarga y
   quedaba la última, cuando era de las primeras. → La fecha sale de la cabecera de la transcripción, y las fuentes se
   leen por la columna Fecha del índice, no por su ID.
3. **Las fuentes internas pesan mucho en volumen y poco en decisión.** Una reunión del equipo, una sesión técnica sin el
   cliente o el propio análisis previo son propuestas hasta que el cliente las confirma. → Pauta en `ingesta-fuentes.md`
   y la cabecera de cada nota dice si la fuente es interna.
4. **El criterio cambia entre reuniones, y el resumen tiende a quedarse con el primero.** En el caso real, el reparto
   entre dos sistemas cambió tres veces; en el primer resumen se describió el enfoque de las primeras reuniones y no el
   vigente. → Cada nota dice a qué reunión sustituye un cambio, y el checkpoint se escribe desde la última decisión de
   cada tema.
5. **Los términos del cliente son decisiones.** Cuando corrige una palabra («no digáis X, para nosotros es otra cosa»),
   se usa la suya en todo el documento. → Pauta en `ingesta-fuentes.md`.
6. **Un prototipo en código no se puede leer como un documento**, y suele estar montado sobre otro proyecto, así que
   arrastra secciones que no son de este. → `leer_fuentes.py --una-fuente` saca los textos visibles de cada componente;
   lo que no sale en ninguna reunión no entra.
7. **Las capturas de un documento previo dicen lo que el texto calla** (etiquetas, columnas, textos de ayuda). →
   `leer_fuentes.py` las guarda en `adjuntos/` y las marca donde están.
8. **Un diagrama con varias páginas suele tener una vigente y una antigua.** → El índice lo avisa; hay que decidir cuál
   vale y decirlo en la nota.
9. **Una fuente que el cliente pasa a mitad del trabajo** (una hoja con los campos y su origen) puede responder más
   preguntas que varias reuniones: se cataloga como las demás y entra con su fecha.

## El DF del cliente

10. **Solo lo que lee el cliente.** Las citas y las preguntas dentro del documento, aunque estén en comentarios, son
    ruido para quien lo lee. → Fuentes y pendientes en dos ficheros aparte, que no salen en el Word.
11. **El diagrama del flujo manda en los estados y las acciones.** El primer DF usó los estados del análisis previo del
    equipo, y no coincidían con el diagrama vigente. → Los estados y los nombres de las acciones son los del diagrama,
    iguales en reglas comunes, actividades, pantallas, matriz y prototipo; si una fuente usa otros, es una pregunta.
12. **Si el flujo ya está dibujado, la imagen sale de ese dibujo.** → Su página vigente, sola, en `analisis/diagramas/`,
    y su PNG con `appian-diagramas-bpmn`.
13. **Lo que el cliente aún no ha diseñado no se rellena con propuestas.** Un tramo que depende de otro sistema se nombra
    y queda «pendiente de definición», distinto de «pendiente de confirmar», y el Word lo resalta igual.
14. **Las fichas de actividad, estructuradas.** Etiquetas «Entrada:», «Salida:», «Arranque:», «Finalización:», una línea
    por elemento, las acciones con su nombre exacto y todas las formas de empezar y terminar, también las automáticas.
15. **El título de una regla común va en la primera columna**, debajo de «REGLA COMÚN n»; la segunda, solo su texto.

## Las pantallas

16. **Nada sin describir.** Cada columna, campo, botón, filtro, mensaje y modal; lo que no se sabe, «pendiente de
    confirmar».
17. **Ninguna restricción en Lógica General.** Obligatorio u opcional, longitudes, caracteres, valores por defecto y
    mensajes de error van en Reglas de Validación.
18. **Selección única o múltiple, siempre.** En cada desplegable, selector y grupo de casillas.
19. **Columnas y campos, uno por línea.** «La tabla incluye las siguientes columnas:» y debajo una sub-viñeta por
    columna con su descripción; nunca seguidas en una frase.
20. **Los modales que siempre hay**, aunque nadie los nombre en una reunión: alta y edición de cada tabla, confirmación
    de cada borrado (con su pantalla propia), detalle de cada vínculo y edición de las filas con datos propios. El
    concepto o el prototipo del cliente suelen tenerlos todos: hay que mirarlos.
21. **La ficha y la tarea son pantallas distintas.** La ficha se abre desde el listado y es para consultar; la tarea, desde
    la bandeja, con los datos del paso editables y la sección de acciones, que solo existe en ella.
22. **Una sección con muchos datos se agrupa** en bloques con título (identificación, datos de otro sistema, importes,
    fechas, datos propios, filas hijas, firmantes, cierre) y dice de dónde sale cada bloque.
23. **Las filas hijas con datos propios** (lotes, líneas) llevan un resumen encima de la tabla (cuántas, cuántas afectan,
    el total, qué es común y qué propio) y su edición en un modal propio.
24. **La cabecera de un registro, estructurada**: tipo y paso, título con su estado, una línea de descripción, una fila de
    datos clave y, debajo y centrada, la línea de progreso.
25. **Referencias por nombre y visibilidad solo en Roles y permisos.** Los números cambian al reordenar; quién ve qué se
    cambia en un único sitio.

## El prototipo

26. **Se puede hacer desde el DF del cliente sin funcional.** El `ref` de cada pantalla es su nombre en 2.3 y las capturas
    se llaman como las líneas de imagen del DF, así que el Word las recoge solas.
27. **Conviene hacer el prototipo antes de cerrar el 2.3.** Al construirlo salen cosas que el DF tiene que contar de otra
    forma (un listado de 12 columnas que se consolida en 7, filtros en la barra del listado).
28. **El estilo del cliente manda cuando ya trabaja así.** Si sus otras aplicaciones usan secciones que se abren y se
    cierran, con su icono y una marca en la abierta, se mantienen aunque la guía general pida pestañas, y se deja dicho.
29. **La marca del cliente es un fichero de su proyecto.** Se saca de su web pública o de su guía de marca; el logo se
    descarga con permiso; nunca entra en el plugin.

## El Word y la plantilla

30. **La plantilla original del cliente no sirve tal cual.** Le faltan las piezas que se añadieron a la neutra (nivel de
    pantalla, 2.6) y el generador lo dice. Se parte de la neutra y se le pasan sus logos de portada y pie y sus colores.
    → `siguiente-version.md`: una orden que lo haga.
31. **El PDF no es un entregable.** Quien revisa el DF lo abre en Word; no hace falta LibreOffice.
32. **Con el Word abierto no se puede regenerar.** El generador lo dice en vez de fallar con un error de Python.

## Cómo se trabaja

33. **Las piezas de una skill están conectadas.** Un cambio en `proyecto.py`, en una plantilla o en la descripción de la
    skill toca flujos, pruebas, el comprobador y otras skills. → Regla en `CLAUDE.md` y `CONTRIBUTING.md`: buscar qué usa
    cada pieza, añadir lo nuevo como opción y con su prueba.
34. **Añadir un requisito toca cuatro sitios** que tienen que coincidir (`requisitos.json`, `requisitos.py`, la tabla del
    README y `requisitos-esperado.json`) y la instalación en el flujo de GitHub.
35. **Las revisiones de quien conoce al cliente son la mejor fuente para afinar la skill.** Las dos revisiones del caso
    real dieron diez reglas nuevas que ninguna reunión habría dado.
36. **Lo que se hace fuera del repositorio se pierde.** Había un primer intento de este trabajo en un plugin aparte que
    nunca llegó a `main`.
37. **En un Windows corporativo solo puede existir `py`**, ni `python` ni `python3`, y PowerShell puede estar en modo
    restringido. → `siguiente-version.md`.
