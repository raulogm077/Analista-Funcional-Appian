# Descripción de pantallas (DF del cliente, 2.3)

Cómo se describe cada pantalla del DF del cliente (`df-cliente-plantilla.md` §2.3) y una pantalla suelta que alguien
explica (modo «Pantalla suelta» del `SKILL.md`). Es la parte del DF que más lee y más corrige el cliente: con ella
valida qué ve y qué pasa con cada cosa que toca, y con ella construye el equipo.

**La regla de esta guía: cada cosa que hay en la pantalla se describe, sin saltarse ninguna.** Cada columna, campo,
botón, vínculo, icono, pestaña, filtro, orden, tooltip, mensaje, estado vacío y modal. Lo que no se sabe no se omite:
se escribe «pendiente de confirmar» y se pregunta.

## 1. De dónde sale

- **De las fuentes**: una transcripción en la que se explica o se revisa la pantalla, un correo, un documento del
  cliente, lo que se cuenta por el chat. Si varias fuentes hablan de la misma pantalla, manda la más reciente
  (`df-cliente-construir.md` §2).
- **De la captura o el prototipo**: se mira antes de escribir. Lo que se ve y nadie dijo (el texto de un botón, una
  columna, un icono, un contador, un valor de ejemplo) también se describe o se pregunta. Si la captura contradice lo
  que dicen las fuentes, mandan las fuentes (la captura puede ser de un diseño anterior); si la diferencia importa, se
  pregunta.

## 2. Antes de escribir: el inventario

Con las fuentes y la captura delante, una lista de todo lo que tiene la pantalla, por partes y de arriba abajo:

| Parte | Qué se apunta |
|---|---|
| Cabecera | Título, chips de estado, botones, iconos, línea de progreso |
| Barra superior | Buscador, cada filtro, botones de la barra (descargar, nuevo, limpiar) |
| Cuerpo | Cada tabla, tarjeta, sección desplegable, pestaña, gráfico, banner, bloque |
| Cada tabla | Cada columna, en orden; la columna de acciones y cada botón; agrupaciones y contadores; paginación |
| Cada formulario | Cada campo, en orden; secciones; bloques que se repiten |
| Pie | Botones (Cancelar, la «X», el botón principal) |
| Lo que aparece al actuar | Modales, confirmaciones, mensajes de error, tooltips, estados vacíos, cambios de estado de un botón |

Cada línea del inventario termina descrita en uno de los apartados del §4 o en «pendiente de confirmar». El
inventario no va en el DF; sirve para el repaso del §9.

## 3. Cómo se organizan las pantallas

- Las pantallas se agrupan **por área** (`#### 2.3.n Pantallas <Área>`), las de cada proyecto.
- Es una pantalla aparte, con su propio título (`##### <Nombre>`): cada pantalla principal, **cada modal**, cada
  pestaña o sección de un registro que tenga su propia tabla o formulario, y cada funcionalidad con reglas propias
  (una exportación con su modal, un asistente por pasos).
- El nombre es el que ve el usuario: «Bandeja de solicitudes», «Nueva solicitud», «Solicitud – Documentación». Las
  demás pantallas la citan por ese nombre: «(se describe en la pantalla "Nueva solicitud")». Nunca por número.
- Lo que se repite igual en varias pantallas se describe una vez (en «Pantallas comunes» o en la primera) y las demás
  lo citan: «mismo comportamiento que en la pantalla "Bandeja de solicitudes"».
- **La ficha y la tarea son pantallas distintas.** La ficha de un registro es para consultarlo: se abre desde el
  listado y no lleva acciones de flujo. Lo que se hace en un paso (editar los datos del paso, elegir la acción que lo
  hace avanzar) va en la tarea, que se abre desde la bandeja de tareas. Una sección «Acciones» solo existe en la tarea.
- **Los modales que siempre hay.** Aunque nadie los nombre en una reunión, cada pantalla con elementos que se crean,
  cambian o borran lleva, cada uno con su pantalla:
  - el alta de cada elemento de una tabla («Añadir comentario») y su edición si se puede editar («Editar comentario»);
  - la confirmación de cada borrado («Eliminar documento», «Eliminar comentario»): qué se borra, qué consecuencia tiene y
    sus botones;
  - el detalle que abre cada vínculo de una tabla («Detalle de la consulta»);
  - la edición de los datos propios de una fila que tiene los suyos (un lote, una línea), que no se mezclan con los del
    registro («Editar lote hijo»);
  - el paso de un documento de una sección a otra si pide datos («Mover a Documentación», con la etiqueta).
  Si las fuentes no dan su texto, la pantalla existe igual y su texto queda «pendiente de confirmar». Mira también los
  modales del prototipo o del concepto del cliente, si los hay: suelen estar todos.

## 4. Los apartados

Cada pantalla tiene estos apartados `######`, en este orden y con estos nombres. «Ejemplo ilustrativo» y «Lógica
General» van siempre; los demás, solo si la pantalla los tiene. No se inventan otros («Acciones», «Modal»,
«Validaciones»). Cada apartado es una lista numerada con sub-viñetas, una idea por punto, y empieza su numeración en 1.

| Apartado | Qué va | Qué no va |
|---|---|---|
| Ejemplo ilustrativo | Un «Caso n: …» por captura, con el estado que enseña, y la captura debajo | — |
| Lógica General | Qué es, cómo se organiza, estado inicial, cada elemento con lo que muestra y lo que hace, el modo de edición | Validaciones, cálculos con condiciones, casuística, confirmaciones de borrado |
| Búsqueda y Filtros (o Filtros, si no hay buscador) | El buscador y cada filtro, cómo se combinan, qué pasa al filtrar | — |
| Ordenación | El orden por defecto y el de cada columna | — |
| Reglas de Validación | Obligatorios, formatos, longitudes y sus mensajes; cálculos; truncados; casuística (Caso A, B…); confirmaciones; estados de un botón; reglas que dependen de otra parte | Quién ve qué: va en Roles y Permisos (2.4.1) |

**La frontera entre Lógica General y Reglas de Validación.** Lógica General dice **qué hay y qué hace**; Reglas de
Validación, **qué se exige, qué se impide y qué se calcula**. Ninguna restricción se escribe en Lógica General, ni
siquiera de pasada en la línea del campo: tampoco «campo obligatorio», «máximo 255 caracteres» u «opcional».

| De un campo o una acción | Lógica General | Reglas de Validación |
|---|---|---|
| Qué es y qué representa | Sí | — |
| Tipo de control (texto libre, desplegable, fecha, solo lectura) | Sí | — |
| De dónde salen el valor y las opciones | Sí | Las opciones que se excluyen y por qué |
| Formato en que se muestra («(DD/MM/AAAA)») y qué se ve si está vacío («-») | Sí | — |
| Qué pasa al pulsarlo, qué campos muestra u oculta | Sí | Las condiciones con casos |
| Obligatorio u opcional | No | Sí |
| Longitud, caracteres, formato o tamaño admitidos, rangos («no anterior a hoy») | No | Sí |
| Valor preseleccionado de un campo de formulario | No | Sí |
| Mensajes de error y de confirmación | No | Sí |
| Cálculos automáticos con condiciones, casuística, cuándo un botón está activo | No | Sí |

```
Mal (Lógica General):  - Motivo: área de texto libre, obligatoria, de 500 caracteres como máximo.
Bien (Lógica General): - Motivo: área de texto libre, para explicar para qué se pide el espacio.
Bien (Reglas de Validación):
                       1. Motivo: campo obligatorio, de 500 caracteres como máximo.
                          - Si está vacío: "Debes indicar el motivo.".
```

El valor por defecto de un **filtro** y el **orden por defecto** sí van en sus apartados (Búsqueda y Filtros,
Ordenación): son su estado inicial, no una restricción.

### Ejemplo ilustrativo

1. «Caso 1: …» describe el estado que enseña la captura: la bandeja con datos, la bandeja vacía, el formulario con
   errores, el modal abierto, un registro cancelado. Varios estados que el cliente debe ver, varios casos.
2. Debajo, la captura (`![Nombre](../prototipo/capturas/…png)`). Sin captura, el caso y la línea de la imagen quedan.
3. Una nota que explica algo de la captura que no se ve a simple vista, en una línea: «Si se crea desde una consulta,
   estos campos vienen rellenos».

### Lógica General

En este orden; se salta lo que la pantalla no tiene:

1. **Qué es y para qué sirve**: «Esta pantalla corresponde a … Muestra … ». Se dice desde dónde se entra (menú,
   pestaña, botón, vínculo desde otra pantalla) y, si hay varias formas, todas.
2. **Cómo se organiza**: tabla, formulario, tarjetas, agrupaciones, pestañas, secciones; qué representa cada fila o
   bloque. Una pantalla compuesta se presenta por partes («se estructura en tres partes: cabecera, tarjetas
   informativas y secciones») y después cada parte en su punto, en ese orden (§6).
3. **Estado inicial**: qué se ve al entrar, qué viene relleno o seleccionado, qué sección está abierta y cuáles
   cerradas, qué se ve si no hay ningún registro (la tabla vacía o el mensaje literal).
4. **Elementos de la parte superior**: la barra de búsqueda y filtros («se describe en la sección Búsqueda y
   Filtros») y cada botón con su efecto. Un botón que abre otra pantalla o un modal: «al pulsarlo, se abre el modal
   "Nueva solicitud" (se describe en la pantalla "Nueva solicitud")», sin describir su contenido.
5. **Columnas o campos**, uno por punto y en el orden en que se ven, cada uno como dice el §5.
6. **Acciones por fila**: «columna con dos botones por fila: "Ver detalle" y "Borrar"», y cada botón con su efecto;
   si tiene casuística, «el comportamiento detallado se describe en la sección Reglas de Validación».
7. **Tooltips**: el texto literal entre comillas y qué lo muestra («al pasar el ratón sobre …»).
8. **Modo lectura y edición**: el modo por defecto, qué botón pasa a edición y qué campos se vuelven editables, qué
   hace «Cancelar» (o la «X») y qué hace «Guardar» si todo es correcto (se cierra, se queda, se abre otra pantalla, en
   qué estado queda el registro).
9. **Paginación**: «La tabla incluye paginación, mostrando un máximo de 10 registros por página». En una tabla con
   agrupaciones, si es por agrupación.

### Búsqueda y Filtros

1. Dónde está la barra y a qué afecta: la tabla, todas las agrupaciones, todas las secciones y gráficos.
2. **Buscar**: sobre qué campos busca (las columnas visibles y, si los hay, campos que no son columna); si la
   coincidencia es parcial o exacta; si distingue mayúsculas; valor por defecto (vacío); qué muestra la tabla al
   escribir.
3. **Cada filtro**, en su punto:
   - el tipo y si es de selección única o múltiple;
   - de dónde salen las opciones (valores fijos entre comillas; de datos maestros; los valores que tienen los
     registros visibles) y en qué orden;
   - el valor por defecto («Todos»);
   - qué muestra la tabla al seleccionar («la tabla muestra únicamente las solicitudes de los espacios
     seleccionados»);
   - lo especial: si se bloquea cuando solo hay una opción, si depende de otro filtro.
4. La regla de «Todos» en los de selección múltiple: «si se selecciona "Todos", las demás opciones se deseleccionan;
   si se selecciona otra opción con "Todos" seleccionado, "Todos" se deselecciona».
5. Cómo se combinan: «todos los filtros y la búsqueda se combinan; la tabla muestra lo que cumple todos a la vez».
6. Qué pasa tras filtrar: qué se oculta, qué sigue visible aunque quede vacío (una agrupación sin resultados), cómo
   cambian los contadores, qué se ve si nada cumple (la tabla vacía o el mensaje literal).
7. Los botones de la barra («Limpiar», «Guardar filtros») con su efecto o, si son los de siempre, «con el mismo
   comportamiento que en el resto de pantallas».

### Ordenación

1. **Orden por defecto**: la columna y el sentido, con lo que significa («por ID descendente, mostrando primero las
   más recientes»).
2. **Cada columna ordenable**, con su criterio: alfabéticamente de A a Z o de Z a A; de la fecha más antigua a la más
   reciente o al revés; de menor a mayor o al revés; en una columna especial, cómo («agrupando primero las que tienen
   alertas»). Cómo se trata el guion («-»): como valor vacío.
3. Qué pasa al cambiar el orden: se reordena manteniendo la búsqueda y los filtros; en una tabla con agrupaciones, si
   ordena dentro de cada una sin mezclarlas.

### Reglas de Validación

1. **Cada campo de un formulario**, en su punto, en el orden del formulario, también los opcionales («campo
   opcional»):
   - obligatorio u opcional; longitud máxima; caracteres permitidos; formato (fecha, número, importe, correo, URL);
   - **un mensaje literal por cada incumplimiento**: vacío, demasiado largo, carácter no permitido, formato erróneo:
     «Si al pulsar "Enviar" el campo está vacío, se muestra el mensaje de error: "Debes indicar el espacio."»;
   - las opciones que no aparecen y por qué («solo los espacios activos»);
   - el valor preseleccionado.
2. **Al guardar con errores**: «si algún campo obligatorio no está informado o incumple alguna regla, se muestra el
   mensaje de error junto al campo y la solicitud no se guarda».
3. **Cálculos automáticos**: cómo se calcula y que no es editable (un número, una versión, una fecha que se rellena al
   cambiar de estado, un contador).
4. **Truncados**: la columna, el límite de caracteres, los puntos suspensivos y el tooltip con el texto completo.
5. **Casuística**, siempre enumerada y sin solapes:

   ```
   N. [Nombre de la regla]: [de qué depende].
      - Caso A: [condición] → [efecto].
      - Caso B: [condición] → [efecto].
   ```

6. **Confirmaciones**: el texto literal y sus botones, junto a la acción que lo pide; si cambia según el caso, uno por
   caso.
7. **Estados de un botón**: los que tiene (inicial, en curso con un indicador, disponible) y qué cambia en cada uno.
8. **Si algo falla al guardar o al consultar otro sistema**: qué ve el usuario (el mensaje literal) y qué pasa con
   lo que estaba haciendo (se guarda, no se guarda, se reintenta).
9. **Reglas que dependen de otra parte**: qué cambia en la pantalla según el estado del registro («si la solicitud
   está cancelada, todas las secciones pasan a solo lectura»), según otro campo o según una configuración de datos
   maestros.

## 5. Cómo se describe cada elemento

Cada elemento, en su punto, con lo que le aplique de su fila:

| Elemento | Qué se dice |
|---|---|
| Columna de una tabla | El nombre en mayúsculas (`NÚMERO:`); qué representa; de dónde sale (elegido al crear, calculado, de datos maestros, heredado de otro registro); el formato entre paréntesis («(DD/MM/AAAA)», «(nombre y apellidos)»); qué se ve si está vacío («-»); qué pasa al pulsarlo (vínculo al registro, descarga, copiar). Los valores posibles, entre comillas |
| Campo de un formulario | Nombre; qué es; tipo de control: campo de texto libre, área de texto, desplegable de selección única o múltiple, campo combinado de búsqueda y texto libre, botones de opción, casilla de verificación, campo de fecha, campo numérico, importe, carga de ficheros, solo lectura; de dónde salen sus opciones y en qué orden; si se rellena solo y si se puede cambiar; si muestra u oculta otros campos |
| Botón | El texto literal; dónde está; qué pasa al pulsarlo y después (cambio de estado, correo, se cierra, se abre otra pantalla) |
| Vínculo | Qué texto lleva y adónde lleva |
| Icono o indicador | Qué significa cada icono o color y cuándo aparece |
| Chip, etiqueta o estado | Los valores posibles, entre comillas, y cuándo toma cada uno |
| Contador | Qué cuenta y si cambia con los filtros |
| Tooltip | El texto literal y sobre qué aparece |
| Pestaña o sección desplegable | Su nombre, qué contiene (se describe en su pantalla si tiene la suya) y si está abierta al entrar |
| Tarjeta de cifras | El título y qué cuenta exactamente, con qué filtros |
| Gráfico | El título; el tipo (barras horizontales apiladas, líneas, circular); qué representa cada eje o segmento; el color de cada valor; el tooltip; qué pasa con los valores a cero |
| Banner o aviso | Cuándo aparece y el texto que muestra |
| Línea de progreso | Qué fases muestra y cómo marca las hechas, la actual y las pendientes |
| Bloque que se repite | El primero que se ve, el botón que añade otro, cómo se numeran y cómo se quita uno |
| Exportación | El formato; qué contiene (hojas, columnas en orden, una fila por qué); qué filtros respeta y cuáles no; cómo se representan los vacíos |
| Mensaje de éxito o aviso | El texto literal y cuándo aparece («Solicitud enviada correctamente») |
| Componente común | Se nombra y se dice que funciona como en el resto de aplicaciones del cliente, sin redefinirlo |

Nada de esta tabla es una restricción: si un campo es obligatorio, su longitud, sus caracteres, su valor preseleccionado
o sus mensajes de error, se escriben en Reglas de Validación (§4, «La frontera»).

## 6. Patrones

Un catálogo para cuando aparece un tipo de pantalla, no una lista de pantallas que tenga que haber:

- **Listado principal**: qué registros muestra (también a cuáles tiene acceso el usuario, en una frase, sin roles),
  botones de la barra (nuevo, descargar), columnas, paginación; con sus apartados de Búsqueda y Filtros y Ordenación.
- **Alta o edición en un modal**: desde dónde se abre, cada campo, los botones del pie y qué pasa tras guardar; con
  sus Reglas de Validación campo a campo.
- **Modal que cambia según desde dónde se abre** (vacío desde la bandeja, relleno desde otro registro): cada variante
  como un punto aparte, con lo que viene relleno, lo que se puede cambiar, qué se vincula al guardar y qué pasa al
  cancelar.
- **Registro**: la cabecera (título, chips de estado, botones de flujo, iconos, línea de progreso), las confirmaciones
  de cada botón de flujo, las tarjetas, el banner de estado (cancelado, finalizado) y las secciones, cada una con su
  pantalla si tiene tabla o formulario propios.
  - La cabecera, estructurada: el tipo de registro (y el paso, en la tarea), el título con su estado al lado, una línea
    con su descripción y una fila de datos clave (número, expediente, fechas, quién lo tiene); la línea de progreso,
    debajo y centrada.
  - Secciones que se abren y se cierran: cómo se ven cerradas y abiertas (icono de cada sección, marca de la abierta),
    cuáles están abiertas al entrar en la ficha y en la tarea.
  - Una sección con muchos datos se agrupa en bloques con su título (identificación, datos de otro sistema, importes,
    fechas, datos propios, filas hijas, firmantes, cierre) y dice de dónde sale cada bloque (otro sistema o la propia
    aplicación). Cada bloque, sus datos en columnas, etiqueta encima del valor.
  - Las filas hijas con datos propios (lotes, líneas): un resumen encima de la tabla (cuántas hay, cuántas afectan, el
    total), qué es común a todas y qué propio de cada una, y la edición de cada fila en su modal.
- **Sección de un registro con tabla agrupada**: las agrupaciones, sus contadores y si se despliegan; filtros que
  afectan a todas por igual; orden dentro de cada agrupación.
- **Cuadro de mando**: la barra de filtros que afecta a todo; cada sección con sus tarjetas y sus gráficos; las tablas
  que incluya.
- **Datos maestros o configuración**: las pestañas, quién la usa (en Roles y Permisos), cada tabla y su modal de alta.
- **Exportación**: el botón y sus estados, el modal con sus opciones y el contenido del fichero.
- **Historial o histórico**: qué cambios se registran, las columnas (qué, quién, cuándo) y el orden.
- **Asistente por pasos**: cada paso como un punto (sus campos), los botones «Anterior» y «Siguiente», qué se valida
  al pasar de un paso a otro (en Reglas de Validación) y qué pasa si se sale a medias.
- **Bandeja de tareas u otro componente común**: qué tareas aporta esta solución y qué pasa al completarlas; el resto,
  como en el componente común.

## 7. Reglas fijas

1. **Nada sin describir.** Todo lo del inventario está en un apartado o en «pendiente de confirmar».
2. **Todo borrado o cancelación pide confirmación**, con su texto literal y sus botones, en Reglas de Validación. Si
   no se sabe el texto, se pregunta: un borrado no se cierra sin su confirmación. La confirmación de un borrado es un
   modal con su propia pantalla («Eliminar documento»), como los demás que siempre hay (§3).
3. **Un modal es otra pantalla.** La que lo abre dice qué botón lo abre y su nombre; su contenido va en la suya.
4. **Quién ve qué, solo en Roles y Permisos (2.4.1).** Las pantallas describen todo lo que existe (todos los botones,
   todas las secciones) y no dicen qué rol lo ve; la nota fija de la plantilla lo recuerda. Cada acción de la pantalla
   tiene su fila en la matriz.
5. **Lógica General siempre**, como mínimo con qué es la pantalla y desde dónde se entra. Si ni eso está claro, se
   pregunta.
6. **Ninguna restricción en Lógica General.** Obligatoriedad, longitudes, caracteres, formatos admitidos, valores
   preseleccionados y mensajes de error van siempre en Reglas de Validación (§4, «La frontera»).
7. **Nada de Appian**: ni objetos ni componentes por su nombre técnico (`redaccion.md`).

## 8. Cómo se escribe

- Frases declarativas en presente: «se muestra», «al pulsarlo, se abre». Lo opcional para el usuario, con «puede».
- Lista numerada con sub-viñetas, hasta tres niveles; nada de párrafos largos.
- Los nombres de columna de una tabla, en mayúsculas; los de campo, como se ven.
- Textos literales entre comillas: botones, estados, valores por defecto, mensajes, tooltips, opciones.
- Siempre el después: toda acción dice qué pasa a continuación.
- Referencias entre paréntesis y por nombre: «(se describe en la pantalla "Nueva solicitud")», «(se describe en la
  sección Reglas de Validación)», «(ver regla común "Plazos")».
- Las palabras del cliente: si dice «expediente», es «expediente» en todas las pantallas.

## 9. Qué preguntar y repaso

Antes de cerrar una pantalla, con el inventario del §2:

- [ ] Cada elemento del inventario está descrito o en «pendiente de confirmar».
- [ ] Lógica General empieza por qué es la pantalla y desde dónde se entra, y dice el estado inicial y qué se ve sin
      registros.
- [ ] Cada columna dice qué es, de dónde sale, su formato y qué se ve vacía; cada campo, su tipo de control y de
      dónde salen sus opciones.
- [ ] Cada botón y cada vínculo dicen qué pasa al pulsarlos y después.
- [ ] Cada filtro dice tipo, selección, opciones, valor por defecto y efecto; está la combinación y el caso sin
      resultados.
- [ ] Cada columna ordenable tiene su criterio y está el orden por defecto.
- [ ] Cada campo obligatorio o con formato tiene un mensaje literal por incumplimiento.
- [ ] Cada borrado o cancelación tiene su confirmación literal.
- [ ] Lógica General no dice de ningún campo si es obligatorio u opcional, su longitud, sus caracteres, su formato
      admitido, su valor preseleccionado ni ningún mensaje de error; nada de casuística.
- [ ] Cada campo de un formulario está en Reglas de Validación con su obligatoriedad, aunque sea opcional («campo
      opcional»).
- [ ] Están los mensajes de éxito y qué pasa si algo falla al guardar.
- [ ] Ninguna pantalla dice qué rol ve qué; cada acción está en la matriz de 2.4.1.
- [ ] Cada modal tiene su pantalla y se cita por su nombre.
- [ ] Están los modales que siempre hay (§3): alta y edición de cada tabla, confirmación de cada borrado, detalle de
      cada vínculo, edición de las filas con datos propios.
- [ ] La ficha no tiene acciones de flujo; la sección de acciones está solo en la tarea, que se abre desde la bandeja.
- [ ] Una sección con muchos datos está agrupada en bloques con título y su origen.

Lo que falte va a `df-cliente-pendientes.md`, en una pregunta cerrada: «¿Qué mensaje se muestra si se intenta enviar
sin espacio?», «¿La búsqueda distingue mayúsculas?», «¿Qué columnas se pueden ordenar?».

## 10. Ejemplo (caso ficticio)

Un listado principal y el modal que abre, dentro del área de solicitudes.

```markdown
#### 2.3.1 Pantallas Solicitudes

##### Bandeja de solicitudes

###### Ejemplo ilustrativo

Caso 1: bandeja con solicitudes en distintos estados.

![Bandeja de solicitudes](../prototipo/capturas/01-bandeja.png)

###### Lógica General

1. Esta pantalla corresponde a la página principal del apartado "Solicitudes". Muestra las solicitudes de ocupación
   de espacios a las que el usuario tiene acceso (se detalla en Roles y Permisos).
2. La información se presenta en formato de tabla, donde cada fila es una solicitud.
3. Estado inicial de la pantalla:
   - Al entrar, la tabla muestra todas las solicitudes, sin filtros, ordenadas por número descendente.
   - Si no existe ninguna solicitud, se muestra el mensaje "Todavía no hay solicitudes.".
4. En la parte superior se muestran la barra de búsqueda y filtros y los botones "Descargar vista actual" y "Nueva
   solicitud":
   - Barra de búsqueda y filtros: permite acotar el listado (se describe en la sección Búsqueda y Filtros).
   - "Descargar vista actual": descarga un fichero XLSX con las columnas de la tabla, respetando la búsqueda, los
     filtros y el orden vigentes. La cabecera del fichero incluye la fecha y hora de la descarga y los filtros
     aplicados.
   - "Nueva solicitud": al pulsarlo, se abre el modal "Nueva solicitud" (se describe en la pantalla "Nueva
     solicitud").
5. La tabla incluye las siguientes columnas:
   - NÚMERO: identificador de la solicitud, asignado por la aplicación al crearla, en formato de vínculo; al pulsarlo,
     se abre la solicitud.
   - UNIDAD: unidad que registra la solicitud, elegida al crearla.
   - ESPACIO: espacio que se pide, elegido al crearla.
   - FECHAS: fecha de inicio y fecha de fin de la ocupación (DD/MM/AAAA – DD/MM/AAAA).
   - ESTADO: estado actual de la solicitud. Valores posibles: "En revisión", "Pendiente de subsanar", "Pendiente de
     resolución", "Autorizada", "Denegada", "Cancelada".
   - FECHA DE RESOLUCIÓN: fecha en la que se resolvió (DD/MM/AAAA). Si la solicitud aún no está resuelta, se muestra
     un guion ("-").
   - ACCIONES: columna con un botón por fila, "Cancelar".
     - "Cancelar": al pulsarlo, se cancela la solicitud (el comportamiento detallado se describe en la sección Reglas
       de Validación).
6. Al pasar el ratón sobre el icono junto al ESTADO "Pendiente de subsanar", se muestra el tooltip "Falta
   documentación: revisa el motivo en la solicitud".
7. La tabla incluye paginación, mostrando un máximo de 10 solicitudes por página.

###### Búsqueda y Filtros

1. La barra de búsqueda y filtros está sobre la tabla y afecta al listado de solicitudes.
2. Buscar: campo de búsqueda libre, que busca por todas las columnas visibles.
   - La búsqueda es por coincidencia parcial y no distingue entre mayúsculas y minúsculas. Valor por defecto: vacío.
   - Al introducir un texto, la tabla muestra únicamente las solicitudes que contienen ese texto en alguna columna.
3. La pantalla incluye los siguientes filtros:
   - Estado: desplegable de selección múltiple. Opciones: "Todos", "En revisión", "Pendiente de subsanar",
     "Pendiente de resolución", "Autorizada", "Denegada", "Cancelada". Valor por defecto: "Todos".
     - Al seleccionar uno o varios estados, la tabla muestra únicamente las solicitudes en esos estados.
   - Espacio: desplegable de selección múltiple. Opciones: los espacios de las solicitudes visibles en la tabla,
     ordenados alfabéticamente. Valor por defecto: "Todos".
     - Al seleccionar uno o varios espacios, la tabla muestra únicamente las solicitudes de esos espacios.
4. En los dos filtros, si se selecciona "Todos", las demás opciones se deseleccionan; si se selecciona otra opción con
   "Todos" seleccionado, "Todos" se deselecciona.
5. La búsqueda y los filtros se combinan: la tabla muestra las solicitudes que cumplen todos a la vez.
6. Si ninguna solicitud cumple la combinación aplicada, se muestra la tabla vacía.

###### Ordenación

1. Por defecto, la tabla se ordena por NÚMERO descendente, mostrando primero las solicitudes más recientes.
2. Cada columna permite ordenar su contenido en sentido ascendente y descendente:
   - NÚMERO: de menor a mayor, o de mayor a menor.
   - UNIDAD, ESPACIO y ESTADO: alfabéticamente de A a Z, o de Z a A.
   - FECHAS: por la fecha de inicio, de la más antigua a la más reciente, o al revés.
   - FECHA DE RESOLUCIÓN: de la más antigua a la más reciente, o al revés, tratando el guion ("-") como valor vacío.
3. Al cambiar el orden, la tabla se reordena manteniendo la búsqueda y los filtros vigentes.

###### Reglas de Validación

1. La tabla solo muestra las solicitudes a las que el usuario tiene acceso, con independencia de los filtros.
2. "Descargar vista actual" descarga exactamente lo que muestra la tabla en ese momento: la búsqueda, los filtros y el
   orden vigentes.
3. Cancelar una solicitud (botón "Cancelar"):
   - El botón solo está activo si la solicitud no está resuelta ni cancelada.
   - Antes de ejecutarse, se muestra el mensaje de confirmación "¿Seguro que quieres cancelar esta solicitud? Esta
     acción no se puede deshacer.", con los botones "Volver" y "Cancelar solicitud".
   - Al confirmarlo, la solicitud pasa a "Cancelada" y se envía la notificación de cancelación (NOT-04).

##### Nueva solicitud

###### Ejemplo ilustrativo

Caso 1: modal vacío, abierto desde la bandeja.

![Nueva solicitud](../prototipo/capturas/02-nueva.png)

###### Lógica General

1. El modal "Nueva solicitud" se abre al pulsar el botón "Nueva solicitud" de la pantalla "Bandeja de solicitudes" y
   permite registrar una solicitud de ocupación.
2. El modal incluye los siguientes campos:
   - Unidad: campo de solo lectura. Muestra la unidad del usuario que crea la solicitud.
   - Espacio: desplegable de selección única. Opciones: los espacios activos de datos maestros, ordenados
     alfabéticamente.
   - Fecha de inicio y Fecha de fin: campos de fecha (DD/MM/AAAA).
   - Motivo: área de texto libre.
   - Documentación: carga de ficheros, para adjuntar la memoria y el plano; admite varios ficheros a la vez.
3. El modal incluye los botones "Cancelar" y "Enviar" en la parte inferior, además del icono de cierre ("X") en la
   esquina superior derecha:
   - "Cancelar" (o el icono "X"): cierra el modal sin guardar.
   - "Enviar": valida los campos (se describe en la sección Reglas de Validación) y, si todo es correcto, crea la
     solicitud en "En revisión", cierra el modal, muestra el mensaje "Solicitud enviada correctamente", envía la
     notificación NOT-01 y abre la solicitud creada.

###### Reglas de Validación

1. Espacio: campo obligatorio.
   - Si al pulsar "Enviar" no está seleccionado, se muestra el mensaje de error: "Debes seleccionar un espacio.".
2. Fecha de inicio y Fecha de fin: campos obligatorios; la fecha de inicio no puede ser anterior a hoy y la de fin no
   puede ser anterior a la de inicio.
   - Si alguna está vacía: "Debes indicar las fechas de la ocupación.".
   - Si la fecha de inicio es anterior a hoy: "La fecha de inicio no puede ser anterior a hoy.".
   - Si la fecha de fin es anterior a la de inicio: "La fecha de fin no puede ser anterior a la de inicio.".
3. Motivo: campo obligatorio, de 500 caracteres como máximo.
   - Si está vacío: "Debes indicar el motivo.".
   - Si supera la longitud: "El motivo no puede superar los 500 caracteres.".
4. Documentación: obligatoria; formatos PDF, DOCX y JPG; 20 MB como máximo por fichero.
   - Si no hay ningún fichero: "Debes adjuntar la documentación.".
   - Si un fichero tiene otro formato o pesa más: "El fichero [nombre] no es válido: solo PDF, DOCX o JPG de hasta 20
     MB.".
5. Unidad: se rellena con la unidad del usuario y no se puede cambiar.
6. Al pulsar "Enviar", si algún campo incumple alguna regla, se muestra su mensaje junto al campo y la solicitud no se
   crea.
7. Si el registro de organismos no responde al enviar, se muestra el mensaje "No se ha podido comprobar la unidad.
   Inténtalo de nuevo en unos minutos." y la solicitud no se crea (ver integración "Registro de organismos").
```
