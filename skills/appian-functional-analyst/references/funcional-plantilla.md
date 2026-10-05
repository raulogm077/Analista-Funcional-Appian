# Análisis funcional (`analisis/funcional.md`)

Es lo que el cliente valida. De aquí sale el DF en Word (`df_docx.js`) y lo leen el prototipo y la
especificación técnica. Ejemplo completo: `ejemplos/autorizaciones/analisis/funcional.md`.

## Lo que leen los scripts

- Cabecera: `# <Proyecto> — Diseño funcional` y la línea `Versión: 1.0 · Estado: borrador`
  (estados: borrador, en validación, validado).
- Apartados `## N. Título` con los números de abajo; dentro, `### …` libre.
- **Ficha**: `**HU-07 — Título**` y, en la misma línea, el comentario de trazabilidad
  `<!-- ✅ FU-03 00:14:32; FU-05 -->`. Llega hasta la siguiente ficha o título.
- **Fila**: `| AV-03 | … |`, con la trazabilidad en un comentario dentro de la última celda.
- **Criterio**: `` - `HU-07.1` texto ``, dentro de su historia.
- **Trazabilidad**: el comentario lleva el estado y las fuentes. El Word no lo enseña.

  | | Estado |
  |---|---|
  | 🔒 | Validado: el cliente lo aprobó por escrito o en la revisión del DF |
  | ✅ | Decidido: lo dice una fuente |
  | 🔶 | Inferido de lo que dicen las fuentes |
  | ⚠️ | Propuesta o pendiente: tiene su PC |
  | ❓ | No se sabe: tiene su PC |

- **IDs estables**: no se renumeran ni se reutilizan; el siguiente libre lo da `indice.py siguientes`.
  Lo que deja de valer se tacha y dice qué lo anuló, y el Word no lo enseña:
  `**~~HU-11~~ — Título** Anulada por D-02`, `| ~~PC-03~~ | … | Respondida por D-01 |`,
  `` - ~~`HU-07.2`~~ Anulado por D-04: ~~texto~~ ``.

## Lo que no va en el DF

El cliente lo lee para decidir si es lo que quiere. Por eso:
- Las fuentes, los estados y los nombres de las personas van solo en los comentarios.
- Nada de Appian: ni objetos, ni componentes, ni términos técnicos. Eso es la especificación técnica.
- Lo que está pendiente se dice en la frase que afecta, «(pendiente: PC-04)», y se pregunta en el 11.
- Los campos que solo sirven a la lógica de la aplicación no van: solo los datos que el cliente reconoce,
  aunque no salgan en ninguna pantalla.
- Se escribe como dice `redaccion.md`.

## Apartados

### 1. Objetivo y alcance
Qué problema hay hoy, qué se construye y qué cambia para el cliente, en dos o tres párrafos. Lo que queda
fuera, con su motivo y la fase en que irá. Tabla `Término · Significa` con las palabras del cliente que
tienen un significado preciso.

### 2. Perfiles
Tabla `Perfil · Quién es · Qué hace en la aplicación`. Un perfil es un grupo de personas, no una persona.
Normalmente de 3 a 6. Los nombres de esta tabla son los que usan las historias, las pantallas y los
carriles del diagrama.

### 3. Proceso
Por cada proceso, `### 3.n <Proceso>`:
- La imagen del diagrama, `![Proceso de …](diagramas/<proceso>.png)`, que dibuja `appian-diagramas-bpmn`.
- Una ficha por paso, con el mismo `ACT-nn` que el diagrama. Tabla `Quién · Empieza cuando · Pantalla ·
  Plazo` y un párrafo con lo que hace. Si decide algo, una línea por opción y adónde lleva. Los plazos y
  los avisos (AV-nn) van en el paso. En «Pantalla», `PAN-nn`, «—» si lo hace la aplicación o «Fuera de la
  aplicación».

Después de los procesos:
- **Estados**: tabla `Estado · Qué significa` y tabla `De · A · Quién · Cuándo`. Con 3 o más estados, el
  diagrama de estados (`mermaid-diagrams.md`).
- **Escenarios**: de 3 a 6 fichas `ESC-nn`, cada una contada como una historia corta con un caso concreto
  (quién, qué pide, qué pasa) y la línea `Pasos: ACT-01, ACT-02…`. Uno por camino: el normal, una
  devolución, un rechazo, un plazo vencido. Son lo que mejor entiende el cliente y después sirven de
  pruebas de extremo a extremo.

### 4. Funcionalidades
Historias agrupadas por área (`### Área`). Cada una:
1. Título `**HU-nn — Verbo y objeto**` con su trazabilidad.
2. Tabla `Perfil · Pantalla · Paso · Prioridad`. Pantalla y paso, el ID o «—». Prioridad: Imprescindible
   o Deseable.
3. «Como <perfil>, quiero <qué> para <para qué>.»
4. Descripción con sus reglas, en frases cortas; si hay varios casos, uno por línea. Lo que ya dice una
   regla común se cita («Se aplica RB-01»).
5. «Se acepta si:» y los criterios `HU-nn.m`: frases que se pueden comprobar en la aplicación, con los
   textos literales entre comillas. Uno por comportamiento. Toda acción que borre o anule algo dice su
   confirmación literal; si no se sabe, va al 11.

Al final, `### Reglas comunes`: tabla `ID · Regla · Historias` con las `RB-nn` que afectan a varias
historias. Una regla de una sola historia va en su historia.

### 5. Pantallas
Una ficha `PAN-nn` por pantalla, vista o diálogo:
- La captura del prototipo, `![PAN-04 Revisar documentación](../prototipo/capturas/04-revisar.png)`, o
  varias si la pantalla tiene estados que el cliente debe ver (pasos, vistas, errores). Las pone el prototipo.
- Para qué sirve, quién entra y desde dónde se abre, en una o dos frases.
- Tabla `Parte · Qué permite · Quién`.
- `Historias: HU-04, HU-05.`

Lo que hace cada parte está en las historias. Cómo está compuesta (componentes, columnas, campos) está en
el prototipo. Aquí no se repite.

### 6. Información que gestiona
Por entidad de negocio, `### 6.n <Entidad>`:
- Qué es, cuántas hay y cuánto tiempo se conservan.
- Tabla `Dato · Qué significa · Formato · Obligatorio · Dónde se ve`. «Dónde se ve»: las pantallas, o
  «No se muestra: …» con para qué sirve.
- Las relaciones, en una frase.

Al final, `### 6.n Listas de valores`: `Lista · Valores · Quién la mantiene`.

### 7. Avisos
Tabla `ID · Cuándo · A quién · Qué dice · Cómo llega`. «Cómo llega»: correo, tarea o los dos.

### 8. Documentos e informes
Tabla `ID · Qué es · Quién lo genera o lo sube · Cuándo · Formato`. Si no hay, «No hay.».

### 9. Relación con otros sistemas
Tabla `ID · Sistema · Qué se intercambia · Cuándo · Si falla`. Si no hay, «No hay.».

### 10. Condiciones de uso
Una línea por tema, en lenguaje del cliente: personas que la usan y cuántas a la vez, volumen y
crecimiento, conservación y borrado, carga inicial, horario y tiempo máximo sin servicio, idiomas,
accesibilidad, móvil, personas de fuera de la organización, quién mantiene las listas, días hábiles o
naturales. Lo que no se sabe es un PC. De aquí sale el apartado Entorno de la especificación técnica.

### 11. Pendiente de confirmar
Tabla `ID · Pregunta · Opciones · A quién · Afecta a`. Una pregunta por fila, cerrada y con opciones
cuando se puede. Lo respondido se tacha con la decisión que lo responde. El Word solo enseña las abiertas.

### Anexo. Quién puede hacer qué
Lo genera `indice.py derivadas --escribir` a partir del 5. No se edita a mano.
