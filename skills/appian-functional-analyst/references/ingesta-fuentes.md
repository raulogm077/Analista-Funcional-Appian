# Lectura de fuentes

Cómo convertir las fuentes del proyecto en hechos citables para el análisis.

## 1. Catalogar

```bash
python3 <skill>/scripts/leer_fuentes.py <ficheros o carpetas> -o <proyecto>/fuentes/
```

- Cada fuente recibe un ID estable `FU-01`, `FU-02`… y un `.md` con marcas de
  posición. `fuentes/indice.md` es el catálogo; `proyecto.md` dice cuáles se han procesado.
- En iteraciones, ejecútalo con las fuentes nuevas sobre la **misma carpeta**
  `fuentes/`: las ya catalogadas conservan su ID y las nuevas se numeran a
  continuación. Nunca renumeres a mano.
- Lo que el script no puede leer queda en el índice con el motivo:
  - PDF sin `pdftotext` ni `pypdf`, o escaneado: léelo con la herramienta Read.
  - `.msg` sin el paquete `extract-msg`: pide el correo como `.eml` (Outlook:
    Archivo → Guardar como) o PDF. No intentes instalar `extract-msg`: en muchos
    equipos no compila.
  - Imágenes: revísalas con Read.
- **Lo que llega por el chat** (texto pegado, una decisión, la aprobación del jefe de proyecto) es una fuente: guárdalo
  en `<p>/fuentes/chat-AAAA-MM-DD-<tema>.txt` con esta cabecera y catalógalo igual, para que tenga ID:
  ```
  Tipo de fuente: chat | aprobación
  De: <rol de quien lo dice, sin su nombre>
  Fecha: AAAA-MM-DD
  ```
  La aprobación del jefe de proyecto es una FU de tipo Aprobación (por correo, de tipo Correo), y el informe de
  impacto la cita en la Decisión: «✔ FU-09». Si tomas una decisión sin respuesta (sesión desatendida, nadie contesta),
  la pieza queda 🔶 con «(pendiente: PC-nn)» y una PC «Supuesto: ¿confirmas que…?», con la opción aplicada primero en
  «Opciones»; solo en lo que no requiere aprobación: lo que la requiere queda «Pendiente» (`actualizacion.md` §5).
- Aplicación existente: `as-is/` entra como una sola fuente, con el índice de sus documentos y sin su extracción en
  bruto; la propuesta de refactorización, como cualquier fichero. Primero ellas, que son la base:
  ```bash
  python3 <skill>/scripts/leer_fuentes.py --una-fuente <p>/as-is <p>/refactorizacion/propuesta.md -o <p>/fuentes/
  ```

## 2. Citar

Cada hecho del análisis lleva su fuente. En `funcional.md` va en el comentario de trazabilidad
(`<!-- ✅ FU-03 00:14:32 -->`), porque el cliente no la ve; en `tecnico.md` y en los informes, a la vista:

| Fuente | Cita |
|---|---|
| Transcripción | `[FU-03 00:14:32]` (minuto de la intervención) |
| Presentación | `[FU-01 diap. 40]` |
| PDF / Word paginado | `[FU-06 p. 12]` |
| Word o texto sin paginar | `[FU-01 §4]` (apartado) o `[FU-01 RF-05]` (ID del documento) |
| Correo | `[FU-04]` (el índice ya da fecha y asunto) |
| Diagrama | `[FU-10 «Revisar expediente»]` (nombre del elemento) |
| Comentario al DF devuelto | `[FU-12 C3]` (número que le da `leer_fuentes.py`) |
| Aplicación existente (`as-is/`) | `[FU-01 H-SEG-01]`, `[FU-01 NV-ARQ-01]` (el hallazgo o lo sin verificar) o `[FU-01 02-arquitectura.md]` |
| Propuesta de refactorización | `[FU-02 REF-01]` |
| Inferencia | `FU-03, FU-10` con el estado 🔶 |

Dentro de un comentario o de una celda de tabla van sin corchetes (`FU-03 00:14:32`), salvo las que citan un ID de
otra skill (`[FU-01 NV-ARQ-01]`, `[FU-07 PAN-03]`), que los llevan siempre: así no se confunden con los IDs del
análisis. Quien lea el análisis debe poder ir de cualquier regla a la frase exacta que la justifica.

## 3. Qué extraer de cada tipo

### Transcripciones de reuniones
- **Separa decisiones de conversación.** Una decisión tiene marca explícita
  («decidimos», «queda así», «entonces lo hacemos…», «vale, eso sí») o es la
  última palabra de quien tiene autoridad sobre el tema. Lo que se discute sin
  cerrar es un PC (funcional §11), no una historia.
- **Personas → perfiles.** Construye en la nota de la fuente una tabla hablante → rol a
  partir de lo que se dice («como jefe de servicio…») y usa el perfil en el
  análisis. Los nombres reales solo están en la nota de la fuente.
- Las intervenciones de usuarios operativos suelen revelar excepciones
  (rechazos, urgencias, casos raros) que los responsables no mencionan: son
  escenarios y caminos alternativos del proceso (funcional §3).
- Con varias reuniones, lee todas antes de escribir y agrupa por tema, no por
  reunión. El criterio evoluciona: queda la última decisión, pero el cambio se
  registra (ver §4).
- **Léelas por la columna Fecha del índice**, no por el ID: los IDs siguen el nombre del fichero y un nombre sin fecha
  delante (las grabaciones de Teams llevan la suya en medio) queda fuera de orden. La de Teams descargada en Word ya
  es una Transcripción, con la fecha de su cabecera; un Word que no la lleve en ningún sitio toma la de hoy: dedúcela
  del contenido («la reunión de mañana», el acta anterior) y dilo en la nota.
- **Interna o con el cliente.** Una reunión solo del equipo («[INTERNA]» en el título, nadie del cliente entre los
  hablantes) o una sesión técnica con otro proveedor sin el cliente da propuestas ⚠️, nunca decisiones: las confirma o
  las cambia la siguiente reunión con él. Lo mismo un documento de trabajo del equipo (un análisis o un resumen que
  consolida reuniones): es una fuente más, no la base, y sus preguntas abiertas son pendientes. Dilo en la cabecera de
  la nota.
- **Quién decide.** Sin hablantes, el rol sale de lo que se dice («como jefe de departamento…»); cuando un tema lo
  zanja alguien de más arriba que no está («lo ha decidido la directora»), la decisión es de ese rol y vale sobre lo
  acordado antes. Un cambio de criterio entre reuniones (dónde se dan de alta los datos, cuándo se crea un registro en
  otro sistema) se apunta en la nota con la reunión a la que sustituye.
- **Los términos del cliente**: cuando el cliente corrige una palabra («no digáis unidad técnica, para nosotros es
  otra cosa»), es una decisión: anótala en la nota y úsala en todo el análisis, también al citar fuentes anteriores.

### Correos
- Ordena el hilo por fecha y lee solo el texto nuevo de cada mensaje: el texto
  citado ya está en el mensaje anterior.
- Un correo que confirma o cambia algo dicho en reunión es **más fuerte** que la
  reunión (es una confirmación por escrito): actualiza el hecho y cita ambas
  fuentes.
- Los adjuntos quedan en `fuentes/adjuntos/FU-xx/`. Si son relevantes (plantillas,
  listados de campos, capturas), catalógalos también.

### Diagramas de flujo (BPMN, draw.io, Visio, imágenes)
- Actividades → pasos del proceso (funcional §3) y tareas de usuario (candidatas a
  pantalla de tarea). Carriles → perfiles (§2). Decisiones → opciones del paso y
  reglas de las historias (§4).
- Marca qué pasos **no ocurren en la aplicación** (los hace otro sistema, un
  organismo externo o se hacen en papel): «Fuera de la aplicación» en su Pantalla.
- De Visio solo se extraen los textos. Si el flujo importa, pide una exportación
  a PDF o PNG y revísala con Read.
- **Varias páginas** (el índice dice «en N páginas»): suele haber una vigente y una copia antigua o un flujo de otra
  fase. La vigente es la que casa con las reuniones más recientes; di en la nota cuál es y qué queda fuera, y compara
  sus estados y acciones con los de las reuniones: cada diferencia, a la nota.

### Prototipo en código (Figma Make, React)
- Entra como una sola fuente: `leer_fuentes.py --una-fuente <carpeta>`. Su `.md` lleva los textos de pantalla de cada
  componente; se citan por el componente: `[FU-01 CrearTramiteModal]`. Lee el código del componente solo si hace falta
  saber qué pasa al pulsar algo.
- Un prototipo hecho sobre otro proyecto arrastra secciones, datos de ejemplo y textos de aquel: lo que no sale en
  ninguna reunión no entra. Es una fuente de pantallas (qué se ve, etiquetas, columnas, mensajes), no de reglas, y
  pierde frente a cualquier reunión posterior.

### Documento de trabajo con capturas (un análisis previo, un resumen)
- Sus imágenes quedan en `fuentes/adjuntos/FU-xx/` y marcadas en su texto donde están: mira cada una con Read antes de
  escribir la pantalla. La captura da lo que el texto no dice (etiquetas, columnas, textos de ayuda); si los dos no
  coinciden, manda el texto más reciente y la diferencia va a la nota.

### Diseño funcional o ERS existente (modo «DF ya hecho»)
- **Entra como versión 1.0.** El DF es la base: se pasa al formato del plugin (funcional, técnico y Word) como
  versión 1.0, con su fila en `decisiones.md`. Cada pieza lleva su ID del plugin (HU-, PAN-…), el estado 🔒 (lo
  aprobó el cliente) y, en el comentario, la fuente y su ID original: `**HU-03 — Título** <!-- 🔒 FU-01 RF-07 -->`.
  Si el cliente no lo ha aprobado, dilo en el checkpoint y entra como ✅.
- **Las reuniones de antes del DF** no se mezclan con él: después de la versión 1.0 pasan una a una, por orden de
  fecha, por el informe de impacto (`actualizacion.md`). Lo que dicen igual que el DF, con otras palabras, es «SIN
  IMPACTO»; lo que no coincide es un punto que cambia una pieza 🔒 y requiere aprobación. El DF es posterior: puede
  que el cliente cambiara de idea, y eso lo decide el analista, no tú.
- **Las de después**, como siempre.
- **Extrae, no reinterpretes.** Cada pieza lleva su ID del plugin y, en el comentario, el ID original del documento
  (actividad, requisito, pantalla), como arriba. Conserva los nombres de campos y los textos literales: etiquetas,
  botones, tooltips, mensajes de error y de confirmación.
  - Un elemento del DF con dos actores (dos perfiles hacen cosas distintas) da varias piezas con el mismo ID original;
    nunca al revés: dos elementos del DF no se juntan en una pieza.
  - Una pantalla sin requisito que la pida: la PAN entra 🔒 y su historia 🔶 si el texto de la pantalla la sostiene;
    si no, una PC.
  - Un DF que no prioriza: las historias, Imprescindible, inferida (`<!-- 🔒 FU-01 RF-07; prioridad 🔶 -->`), y una sola
    PC «El DF no prioriza: ¿hay algo deseable?».
  - Un CAMBIA pendiente de aprobación que respondería a una PC abierta se añade como opción de esa PC: el cliente
    decide con todo delante.
  - No inventes el «para qué» de una historia que el DF no da (`comprobar.py` no lo pide en las 🔒 con su ID original).
- Cada pantalla (§5) e historia cita su diapositiva o página. Si la diapositiva
  tiene imágenes de la pantalla (el `.md` de la fuente lo indica), mírala antes
  de completar la ficha:
  - Entorno con LibreOffice y poppler (Claude en la nube los tiene): a PDF con LibreOffice en un perfil temporal, la
    diapositiva a PNG y Read del PNG:
    ```bash
    node <skill>/scripts/df_docx.js <p> --pdf-de doc.pptx      # <p>/entregables/revision/doc.pdf
    pdftoppm -f N -l N -png -r 80 <p>/entregables/revision/doc.pdf <p>/entregables/revision/diap
    ```
  - Sin esas herramientas: pide al usuario el documento exportado a PDF y usa
    Read con `pages`.
- **Imagen de pantalla frente a texto**: la imagen completa lo que el texto no
  dice (textos de botones, columnas, iconos, valores de ejemplo, tooltips
  visibles) y eso se incorpora a la ficha citando la diapositiva. Si la imagen
  contradice al texto, manda el texto (la imagen suele ser un diseño anterior) y
  la discrepancia es un PC con las dos citas.
- Las incoherencias internas del documento (un campo que cambia de nombre entre
  diapositivas, un estado que no aparece en el ciclo de vida) son PC con
  las dos citas. No las corrijas por tu cuenta.

### Aplicación existente y propuesta de refactorización
- De `as-is/` se leen `LEEME.md`, los documentos de lo que toca el cambio y `as-is/datos/` (inventario, dependencias,
  hallazgos y lo que no se pudo verificar). Nunca la extracción en bruto.
- Lo que hace hoy la aplicación es un hecho: su comportamiento real, con su evidencia. Lo que es nuevo o cambia lo deriva
  `indice.py cambios` (`cambios.md`).
- Lo de `sin-verificar.json` es una pregunta abierta, no un hecho: un PT y, si lo resuelve negocio, también un PC.
- La propuesta de refactorización propone: sus REF se validan con el cliente, en sus palabras, y el técnico las
  baja a objetos (una DT por REF).

### Hojas de cálculo
- Suelen ser catálogos de campos, listas de valores o datos maestros: van al
  datos (funcional §6, técnico §3) y a las listas de valores.

## 4. Jerarquía entre fuentes y contradicciones

1. Documento aprobado y versionado por el cliente (DF, ERS).
2. Confirmación posterior por escrito (correo del responsable).
3. Decisión posterior en reunión.
4. Decisión anterior en reunión.

La fuente de mayor rango y más reciente fija el valor del análisis, pero **ninguna
contradicción se resuelve en silencio**: fila en `decisiones.md` (qué se decide,
cuándo, qué había antes, con las dos citas) o, si no está cerrada, la pieza
marcada ⚠️ y un PC. Lo 🔒 validado por el
cliente solo cambia con el visto bueno del analista (`actualizacion.md`).

## 5. Confidencialidad

- La carpeta `fuentes/` contiene información del cliente: no se publica ni se
  comparte fuera del equipo del proyecto.
- No copies al análisis correos, teléfonos ni datos personales de las fuentes.
- No envíes contenido de las fuentes a servicios externos para verlo o
  convertirlo (conversores online, renderizadores públicos de diagramas).
