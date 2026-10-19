# Resumen de la rama `yaroslav/plantilla-DF-cliente`

Qué se ha hecho en esta rama, para qué y en qué estado está. Parte de `main` en la 0.8.0-beta.1 (`2f9151d`) y no toca
la versión. El detalle de cada cambio, con su fecha, sus ficheros, cómo se probó y su commit, está en
`2026-10-16-plantilla-df-cliente-registro.md`; las decisiones y las tareas, en `2026-10-16-plantilla-df-cliente.md`; lo
aprendido, en `2026-10-16-plantilla-df-cliente-lecciones.md`.

## Objetivo general

Que `appian-functional-analyst` entregue, además del análisis funcional, el **DF del cliente**: el documento de diseño
funcional que el cliente revisa y valida, en Word y sobre la plantilla del equipo, escrito desde las fuentes del proyecto
(reuniones, correos, documentos, diagramas, prototipos) y con las pantallas descritas al detalle.

Tres ideas guían el trabajo:

- **Un documento propio, no derivado del funcional.** El DF del cliente se construye fuente a fuente; si el proyecto
  tiene funcional, es una fuente más.
- **Iterativo: la última decisión manda.** Cada fuente nueva se lee contra el DF y lo cambia, también lo aceptado antes;
  el cambio queda registrado y la entrega siguiente sube la versión.
- **Solo lo que lee el cliente.** De dónde sale cada bloque y lo que falta por confirmar van en dos ficheros aparte, que
  no salen en el Word.

## Qué hay nuevo

### El DF del cliente como entregable

| Pieza | Qué es |
|---|---|
| `assets/plantillas/df-cliente.docx` | Plantilla de Word **neutra**: la del equipo sin marca de ningún cliente, con las pantallas agrupadas por área (`2.3.n PANTALLAS <ÁREA>` y cada pantalla en `2.3.n.m`) y el apartado nuevo **2.6 Periodo de estabilización**. La de un cliente vive en su proyecto (`<p>/plantillas/df-cliente.docx`) |
| `assets/plantillas/df-cliente.md`, `df-cliente-fuentes.md`, `df-cliente-pendientes.md` | El esqueleto del DF y los dos ficheros que lo acompañan: las fuentes de cada bloque y las preguntas abiertas |
| `references/df-cliente-plantilla.md` | La guía de cada sección del DF: para qué la lee el cliente, qué se escribe, en qué formato y con qué tono, con un caso ficticio completo (reglas comunes, fichas de actividad de 10 campos, roles y matriz de permisos, notificaciones, KPIs, estabilización) |
| `references/df-cliente-construir.md` | Cómo se escribe el DF desde cero con todas las fuentes, cómo entra cada fuente nueva (la última decisión manda), cómo se registran las decisiones y cómo se incorporan los comentarios del cliente al Word |
| `references/requerimientos-pantallas.md` | La guía de descripción de pantallas, dentro del analista. Sustituye a la skill suelta `requerimientos-pantallas` |
| `scripts/df_cliente_docx.py` | Genera el Word rellenando la plantilla (python-docx): reglas comunes, actividades, pantallas numeradas por área, matriz, correos con su maqueta, KPIs y 2.6. Resalta lo pendiente, avisa de lo incompleto y no sobrescribe un Word entregado |
| `scripts/proyecto.py` | Opción nueva `--df-cliente` en `iniciar`, `copia`, `version` y `entregar`, con su propia versión; `estado` muestra la versión y las preguntas abiertas del DF del cliente. Sin la opción, todo funciona como antes |
| `SKILL.md`, flujos F1 y F2 | La skill conoce el DF del cliente: descripción, documentos que escribe, modo «DF del cliente», modo «Pantalla suelta» con la guía de pantallas y tres referencias nuevas |

### La guía de pantallas

Lo que dice `requerimientos-pantallas.md` y no decía la skill suelta:

- Cada cosa de la pantalla se describe, sin saltarse ninguna; lo que no se sabe se escribe «pendiente de confirmar».
- Un inventario de la pantalla antes de escribir, que la lista de repaso final contrasta.
- Los apartados y su frontera: **Lógica General** dice qué hay y qué hace; **Reglas de Validación**, qué se exige, se
  impide y se calcula. Ninguna restricción en Lógica General.
- Cómo se describe cada tipo de elemento (columnas, campos, botones, filtros, gráficos, exportaciones…): los desplegables
  y selectores, siempre con su selección única o múltiple; las columnas de una tabla y los campos de un bloque, uno por
  línea.
- Las pantallas se agrupan por área, se citan por su nombre y nunca dicen qué rol las ve: eso va solo en Roles y
  permisos.
- La ficha de un registro y la tarea de un paso son pantallas distintas; la sección de acciones solo está en la tarea.
- Los modales que siempre hay: alta y edición de cada tabla, confirmación de cada borrado, detalle de cada vínculo,
  edición de las filas con datos propios.
- Catálogo de patrones: listado, modal, registro (cabecera estructurada, secciones que se abren, datos agrupados en
  bloques, filas hijas), cuadro de mando, datos maestros, exportación, historial, asistente, componente común.

### Lectura de fuentes (`leer_fuentes.py`)

- La transcripción de Teams descargada en Word se reconoce como transcripción, con sus hablantes y su duración.
- **Formato único de transcripción**: venga de `.vtt`, `.txt` o Word, una intervención por párrafo,
  `[00:14:32] Hablante: texto`.
- Si el nombre del fichero no lleva la fecha, se toma la de la cabecera de la transcripción, no la de hoy.
- Las imágenes de un Word (capturas de pantallas) se guardan en `fuentes/adjuntos/FU-xx/`, marcadas donde están.
- Un prototipo en código (Figma Make, React) entra con `--una-fuente` y da los textos visibles de cada componente.
- El índice avisa cuando un diagrama tiene varias páginas.
- Pautas nuevas en `ingesta-fuentes.md`: leer por fecha, distinguir las fuentes internas de las del cliente, quién
  decide, los términos del cliente, diagramas de varias páginas, prototipos en código y documentos con capturas.

### Reglas para cambios futuros

`CLAUDE.md` y `.github/CONTRIBUTING.md` dicen ahora que las piezas de una skill están conectadas: antes de cambiar una,
se busca qué la usa; lo nuevo se añade como opción, sin cambiar lo de antes, y con su prueba; y la descripción de una
skill no pasa de 1000 bytes.

## Qué cambia en lo que ya existía

- `proyecto.py`: solo añade la opción `--df-cliente`; sin ella, el comportamiento es el de antes.
- `leer_fuentes.py`: las transcripciones en `.txt` pasan al formato único (el mismo que ya tenían las `.vtt`); las
  marcas de tiempo siguen siendo `[hh:mm:ss]`, así que las citas no cambian.
- python-docx entra como requisito opcional: `requisitos.json`, `requisitos.py`, la tabla del README,
  `pruebas/requisitos-esperado.json` y la instalación en `.github/workflows/pruebas.yml`.

## Cómo se ha probado

- `comprobar_plugin.py`: 0 errores en cada commit.
- Selftest del analista: 23 pruebas nuevas (DF del cliente, su Word y la lectura de fuentes), todo en verde.
- **Un caso real completo**, fuera del repositorio: 16 fuentes (12 transcripciones, un diagrama, un prototipo en código,
  un análisis previo con capturas y una hoja de campos) → el DF del cliente sobre la plantilla del cliente, con su
  diagrama y 26 capturas del prototipo hecho con `appian-prototipos`. Yaroslav lo revisó dos veces; cada corrección se
  llevó a la skill (ver las lecciones).

## Qué falta

- **T18 y T19**: seguir iterando con el caso real (las fuentes nuevas que lleguen, los comentarios del cliente al Word)
  hasta que el DF se dé por bueno.
- **T20**: abrir el PR cuando Raúl lo diga, con la descripción sacada del registro.
- En `docs/siguiente-version.md`, fuera de este trabajo: crear la plantilla del cliente a partir de su Word original con
  una orden; que `appian-prototipos` parta del DF del cliente y enlace sus capturas por nombre; un helper de secciones
  desplegables y de cabecera estructurada en el prototipo; las órdenes en un Windows sin `python` ni `python3`.
- La skill suelta `requerimientos-pantallas` se retira cuando esto esté en `main`.
