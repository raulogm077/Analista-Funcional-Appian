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
- Texto pegado en el chat: guárdalo como `.txt` con un nombre descriptivo
  (`reunion-2026-09-03.txt`) y catalógalo igual, para que también tenga ID.
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

### Diseño funcional o ERS existente (modo fiel)
- **Extrae, no reinterpretes.** Conserva los IDs y la numeración del documento
  (actividades, requisitos, pantallas), los nombres de campos y los textos
  literales: etiquetas, botones, tooltips, mensajes de error y de confirmación.
- Cada pantalla (§5) e historia cita su diapositiva o página. Si la diapositiva
  tiene imágenes de la pantalla (el `.md` de la fuente lo indica), mírala antes
  de completar la ficha:
  - Entorno con LibreOffice y poppler (Claude en la nube los tiene):
    `soffice --headless --convert-to pdf doc.pptx` y
    `pdftoppm -f N -l N -png -r 80 doc.pdf diap`; luego Read del PNG.
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
- Lo que hace hoy la aplicación es un hecho: cada historia dice si se conserva, cambia o es nueva (funcional §4).
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
