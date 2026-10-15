# Para la siguiente versión

Lo que sigue abierto tras la 0.8.0-beta.1. Cada línea dice qué, dónde y de dónde sale.

## Pasos de Raúl (antes de la primera versión estable)

- Instalar el paquete en la app de escritorio y en un Windows con algo de la tabla de requisitos sin instalar, y ver que
  el primer mensaje lo dice. En Linux con Claude Code ya está visto; en el portátil con Windows el hook corrió con la
  0.7.0-beta.1 (dejó su marca el 10 de octubre de 2026), falta ver el mensaje con algo sin instalar.
- Ingeniería inversa y refactorización con una aplicación real. Con ella:
  - ~~confirmar que el Dev MCP real da el historial de versiones~~: lo da, en desarrollo y en un entorno de cliente
    (`listObjectVersions`, plan de automejora P4 y P5); falta ejecutar `deriva` de punta a punta;
  - afinar los presupuestos de palabras de ingeniería inversa (hoy la mayoría de documentos van al 20-50 %; con una
    aplicación real de 42 objetos, igual, y LEEME al 96 %);
  - volver a medir la evaluación de malas prácticas con propuestas reales (las `claves` se fijaron a ciegas).
- Archivar `~/Proyectos IA/appian-reverse-engineering` en el equipo donde esté: no está en su cuenta de claude.ai ni en
  el portátil de trabajo. Avisar a quien tenga la skill suelta.
- Avisar a Appian de que `LCP_TOOL_MODE=readonly`, que su documentación describe, no está en el Dev MCP 26.6.110
  (`docs/evaluaciones.md`, «Fase 2 · T5»).

## Ingeniería inversa (del recién llegado de la 0.7.0-beta.3)

- Un proceso grande no cabe en el presupuesto de su `.md` (1.350 palabras) con «cada nodo citado» de
  `agents/process-modeler.md`. Medido en el plan de automejora (P5b): el mayor de 1.464 process models de un entorno de
  cliente tiene 58 nodos; un paso por nodo da 1.450 palabras (107 %) y agrupar lo repetido, 1.080 (80 %), citando cada
  nodo. Basta una frase en `process-modeler.md`: una secuencia que se repite 3 veces o más se describe una vez, con una
  tabla de una fila por repetición y el código e `id` de cada nodo. El presupuesto que crece con los nodos, solo si
  aparece un proceso que no quepa así.
- `references/mermaid-rules.md`: «como mucho 5 cajas por capa» no garantiza el ancho de la arquitectura; partirla en dos
  no encaja con `arquitectura-<capa>.mmd`.

## Pruebas del plugin

- Medir cuánto tarda cada grupo de `comprobar_plugin.py --completo` y lanzarlos en paralelo; con la misma batería,
  Windows tarda el doble que Linux (17 y 8,5 minutos en GitHub).

## Del método L.U.C.I.A. (14 de octubre de 2026)

Lo que salió al ejecutar `docs/plan/2026-10-14-metodo-lucia.md` y no entra en él.

- `leer_fuentes.py --help` y `unir_modulos.py --help` salen con los acentos rotos en Windows (pasan la consola a UTF-8
  después de leer los argumentos); en `proyecto.py` ya está corregido.
- Issues sin Dev MCP: una issue solo queda hecha con lo que deja «verificar». Quien construye a mano sin Dev MCP sigue
  el índice y marca la unidad con `--manual`, pero `indice.py issues --siguiente` no pasa de las que no dependen de
  otra. Si un equipo trabaja así, falta poder dar una issue por hecha a mano.
- Issues: las dependencias salen de los objetos que dos issues comparten o que el técnico nombra al hablar de una; si el
  técnico las da de más, van en serie issues que podrían ir a la vez, y no hay cómo corregirlo a mano.
- Issues: el número de una issue que deja de existir se vuelve a dar si era el mayor de su unidad.
- Un `.eml` con finales de línea de Windows deja el retorno de carro (`\r`) en su `FU-nn.md`: viene de la lectura y sale
  igual en todos los sistemas, pero ensucia el fichero.
- Ingeniería inversa: la extracción no usa la herramienta de dependientes del Dev MCP real (`getObjectDependents`): su
  parámetro se llama `object` y el extractor no lo reconoce como el uuid del objeto (alcance manual). `verificar` sí la
  usa. Decidir si la extracción la llama: una llamada más por objeto.
- Pruebas de la issue: «no evaluable» reconoce solo la rejilla de registros con filtros de usuario
  (`flow!userFilterSetData`, `devmcp_policy.json`). Si aparece otro límite del ejecutor de Appian, se añade allí.
- `verificar` no comprueba quién ve una acción de registro ni quién inicia un proceso: en el ensayo de QA (T16) habría
  cazado dos de los cuatro defectos sembrados.
- QA: `qa.py` dice «ISS-nn vuelve a pendiente» aunque el escenario esté marcado como no necesario (no lee el índice);
  quien manda es `issues.estado()`, que sí lo respeta.
- Issues: un process model con varias actividades en «Para» junta en una sola issue varias historias y pantallas (en el
  proyecto de prueba, el 64 % del técnico); si molesta al construir, partirla por actividad. En P10 (automejora) salen
  issues de 12 y 20 requisitos con el título de su primera historia, que no dice lo que agrupan, y «En paralelo con»
  enumera hasta 22 issues: nadie lo lee.
- Analista: `indice.py impacto` da el texto de la fila de técnico §13 pero no en qué línea va; en el retoque a ciegas
  cuesta dos llamadas por pasada encontrarla.
- Evaluaciones: `montar.py` de `pruebas/evaluaciones/` monta los proyectos sin `proyecto.py iniciar`, así que `estado`
  avisa en ellos de que faltan git y `AGENTS.md`; montarlos como los deja el plugin.

## Del plan de automejora (14 y 15 de octubre de 2026)

Lo que salió de `docs/plan/2026-10-14-automejora.md`, verificado en el código por un revisor de contexto limpio; lo de
P10 (un análisis real hecho con IA, con prototipo y DF, la víspera de construirlo), comprobado en los ficheros que dejaron
las pruebas. Las medidas, en `docs/evaluaciones.md` («Automejora con proyectos reales»). Por gravedad.

### Datos que se pierden o avisos que faltan

- Urgencias: `indice.py colision` (`c_colision`) dice «Colisión: no» sin `as-is/datos/dependencias.json`, que no tiene
  ninguna aplicación nacida en el plugin, sin decir que no ha mirado lo que usa lo corregido. Una línea de aviso en la
  salida y en `urgentes.md` §2 paso 3. Sale de P4 (F5).
- Análisis: `indice.py derivadas --escribir` (`c_derivadas`) sustituye desde «## Anexo» hasta el final del fichero y
  borra en silencio lo que se haya añadido detrás. Negarse o avisar si hay líneas que el anexo no genera. Sale de P2 (dos
  PC perdidos).

### Construcción

- Del análisis a la construcción (F1 paso 13): con técnico §13 en lista, como pide la plantilla mientras no se construye,
  `proyecto.py cambio <p> EV-01 aprobada` aprueba la unidad con cero issues y dice «Técnico §13 no tiene objetos de EV-01
  (columna «Cambio»): no hay nada que construir». Ni F1 paso 13 ni «Proyecto nuevo» del `SKILL.md` dicen que antes se
  pasa §13 a la tabla (`tecnico-plantilla.md` §13), y `cambios.md` §5 dice que sin «Para» sale una sola issue con toda la
  unidad: con una lista salen cero. Media línea en F1 paso 13 y en `cambios.md` §1; que `issues_de` (`proyecto.py`), en
  la construcción inicial, diga que falta la tabla en vez de «no hay nada que construir»; corregir la frase de §5; y que
  `comprobar.py` avise de una unidad en curso con §13 sin tabla. Tras escribirla, `indice.py issues` (repetir `aprobada`
  dice «sin cambios»). Sale de P10.
- Dos unidades en curso sobre la misma pieza: las issues de cada una copian el texto vigente de la historia, la pantalla
  o el paso, que ya lleva lo de la otra. En P10, con EV-02 (una respuesta del cliente que amplía el alcance) aprobada sobre
  piezas de EV-01 sin construir, una issue de EV-01 pidió construir los criterios nuevos de EV-02, y las de EV-02
  llevaron 4 líneas del técnico de EV-01: quien construye EV-01 construiría lo de EV-02. Los frenos de `cambios.md` («ha
  crecido», `--comparte`) funcionaron. Decisión de diseño: que la issue tome el texto de la pieza de la versión con que se
  aprobó su unidad (`versiones/v<versión>/`; `cambios.md` ya guarda «aprobada 1.7») o que marque lo que es de otra unidad.
  Mientras, lo que cambia una pieza de una unidad sin construir va en esa misma unidad. Sale de P10.
- «Supuestos para construir»: para construir mientras el cliente no responde, el equipo de P10 añadió bajo técnico §13 una
  tabla `Pregunta · Se construye con · Dónde cambia`, que el plugin no tiene. No llega a ninguna issue (una dice «pendiente
  de definir (PC-nn)» con el supuesto escrito en §13, y el valor de una constante no llega a la Base), ni las «Reglas para
  quien construye» del mismo apartado; al responderse el PC nada dice qué hacer con su fila ni
  `comprobar.py` lo avisa. `indice.py impacto <PC>` sí la encuentra, pero nada pide pasarle el PC. Propuesta: la tabla en
  `tecnico-plantilla.md` §13; `issues.py` copia en cada issue las filas cuyo PC cita o cuyo «Dónde cambia» es un objeto
  suyo, y lo general de §13 en todas; `actualizacion.md`, al responder un PC, `impacto` con el PC; `comprobar.py` avisa de
  una fila cuyo PC ya no está abierto. Sale de P10.
- La tabla de §13 la escribe la IA a mano: 141 filas en P10, con el «Para» de cada objeto elegido sin ayuda, y de él sale
  el tamaño de las issues (una Base de 68 objetos y 5.600 palabras; otra de 20 requisitos). §3, §4, §6, §7 y §8 ya dicen
  qué es común y qué es de cada pantalla y paso, pero no el nombre de cada objeto. Un borrador por script (lo común,
  «Base»; cada interfaz, su PAN; cada process model, sus ACT) que la IA completa con los nombres. Medir antes con P10. Sale
  de P10.
- Una issue reservada que cambia al regenerarse (la unidad reaprobada con otra fuente) no se lo dice a quien la tiene:
  cambian su `.md` y la `version` de su esperado, y se entera al verificar, porque falla. `aprobada` no lista qué issues
  cambian (una segunda pasada de `indice.py issues` sí). Que regenerar diga qué issues cambian y quién tiene cada una, y
  que `--siguiente` con el mismo `--quien` avise si la suya ha cambiado. Sale de P10.
- `comprobar.py` no avisa de criterios sin «Dado…, cuando…, entonces…» (`funcional-plantilla.md`) ni de técnico §14 sin
  «Con qué» (`tecnico-plantilla.md` §14). Sin los dos, en P10, los `.feature` salen con pasos `*` (`issues.py` avisa de
  ~140 criterios al generar, tarde) y `verificar` no ejecuta ningún caso de prueba. Dos avisos. Sale de P10.
- `tecnico-plantilla.md` §0 no da la etiqueta «Aplicación», que lee la orden de terminar una issue (`--app`), y esa orden
  toma la celda entera, también un paréntesis. Sale de P10.
- `verificar` da a una constante el tipo de su valor (`TEXT`, `GROUP`…) y no «constant»: toda Base con una constante
  falla, y con ella todas las issues. `devmcp_extract.py`, al listar (`pick(it, TYPE_KEYS)` toma `type` antes que el
  contexto de la herramienta); en ingeniería inversa, una constante de grupo se inventaría como grupo. El fixture del
  mock ya lo reproduce. Sale de P6.
- `construida --manual` da la unidad por construida sin decir qué issues quedan sin hacer (P6: 6 de 8). Que imprima las
  pendientes. Confirma, también con Dev MCP, la línea «Issues sin Dev MCP» de arriba: una diferencia de `verificar` que no
  es de quien construye no tiene otra salida. Sale de P6.
- `verificar` bloquea un objeto nuevo por `sobranCampos` (`issues.py` ya lo ignora en uno que se modifica); un campo de
  más no rompe nada y quitarlo exige borrar. Ignorarlo también en los nuevos. La causa de fondo: `tecnico-plantilla.md`
  §1 pide campos de auditoría y §3 no dice que van en cada tabla; una frase. Sale de P6.
- `tecnico-plantilla.md` §13 no dice dónde va el site: lo común va a la Base y el site acabó allí sin páginas. «El site y
  sus páginas, en la issue de la primera pantalla que publican.» Sale de P6.
- Un texto de más de 255 caracteres: `createRecordType` del Dev MCP ignora `length` y lo deja en 255. Una frase en
  `tecnico-plantilla.md` §3 («más de 255: Long Text», como ya dice BP 01 §8) y, si se confirma el límite, una fila en el
  documento 14. Sale de P6.
- `appian-qa/SKILL.md` («El guion») no dice que se cambia de página con `["load","<página>"]`. Sale de P6.
- `indice.py issues <p> <U> ISS-nn` enseña una issue que espera a otra sin avisarlo arriba. Sale de P6.

### Análisis

- `indice.py siguientes` y `proyecto.py version --decision` dan IDs de dos dígitos (`HU-55`, `D-75`) en un proyecto que
  numera con tres (`HU-054`, `D-074`, como suele llegar un DF hecho fuera): cada versión hay que corregirlos a mano. Que
  tomen el ancho que ya usa el proyecto. Sale de P10.
- La aprobación con que se aprueba una unidad (`cambio … aprobada --fuente FU-nn`) queda «sin procesar» en
  `proyecto.py estado` para siempre: solo cuentan «Fuentes procesadas» y las que cita la Decisión de un informe. Que cuente
  la fuente de una aprobación registrada en `cambios.md`. Sale de P10.
- `cambios.md` §1 da la columna «Cambio» por punto (una fuente que toca dos unidades) sin ejemplo; en P10 se sacó del
  código (`unidades.py`, `_de_informe`). Un ejemplo de dos filas. Sale de P10.
- `leer_fuentes.py` sobre una carpeta con un `.md` y las imágenes que enlaza (`![…](img/…)`) cataloga cada imagen como
  una fuente más (18 en P10). Que las tome como parte de su `.md`. Sale de P10.

### Otros agentes y personas

- Sin Claude Code no se encuentran los scripts ni las `references/`: `AGENTS.md` (`assets/plantillas/agentes.md`) y los
  flujos copiados citan `proyecto.py` sin ruta, y esos ficheros se comparten, así que no pueden llevar la de nadie. Que
  `proyecto.py iniciar` escriba la ruta del plugin en un fichero local ignorado por git y `AGENTS.md` lo cite. Sale de P8
  (Copilot hizo el retoque de memoria y dejó la versión a medias) y P9.
- Retoque que llega por el chat: «Camino corto» paso 1 (`actualizacion.md`) y F2 no dicen que antes se crea su fuente
  (`ingesta-fuentes.md` §1). Media línea. Sale de P7 y P9.
- La línea de arriba sobre `indice.py impacto` y la fila de técnico §13 se queda corta: tampoco da las secciones que
  contienen el texto cambiado (en P7, §5 y §14), y `comprobar.py` no lo detecta. Sale de P2 y P7.

### Volumen grande

- `volumen-grande.md` reparte en líneas y `leer_fuentes.py` solo da líneas: con transcripciones de líneas largas (~59
  palabras por línea), 18 reuniones caben en «un bloque» de ~170.000 tokens. Medir en palabras (unas 20.000-25.000 por
  bloque) y que `leer_fuentes.py` ponga las palabras de cada fuente en `indice.md`. Sale de P3.
- Fuentes duplicadas: `leer_fuentes.py` solo reconoce el mismo fichero byte a byte; dos de 18 transcripciones eran la
  misma grabación con otro título, se leerían dos veces y `comprobar.py` pide cobertura de sus tramos. Que el script avise
  de una fuente casi idéntica a otra, que `ingesta-fuentes.md` §1 diga que no se lee y que `comprobar.py` no le pida
  cobertura. Sale de P3.
- Con módulos, cada uno redacta lo que comparte con otro: 3 pares de historias que son la misma función, 9 de 31
  decisiones repetidas y una contradicción perdida al unir. En el checkpoint de `volumen-grande.md`, cada concepto y cada
  contradicción compartidos tienen un módulo dueño y los demás lo citan por su ID. Sale de P3.
- `volumen-grande.md` §3: los rangos no cubren RB, INT, DOC, DT, PT ni `3.n`/`6.n`, y no dice que §0, §1, §4, §10 y §11
  del técnico los escribe quien reparte. Y F1 no enlaza la variante de volumen grande. Sale de P3.
- La 1.0 de un proyecto nuevo deja «Fuentes procesadas» de `proyecto.md` a mano (18 filas en P3) y, mientras, `estado`
  dice «0 procesadas, siguiente paso: catalogar». `proyecto.py version` ya sabe escribirlas: reutilizarlo en la 1.0.
- F1 paso 3 no dice si cada fuente lleva nota fuera del volumen grande, e `ingesta-fuentes.md` §3 supone que sí. Una
  frase. Sale de P1.

### Ingeniería inversa

- El extractor no pide los dependientes al Dev MCP real: `getObjectDependents` recibe `object`, que `classify_param` no
  reconoce (`UUID_EXACT`). Confirma la línea de arriba; en una aplicación de 42 objetos los dependientes pedidos a mano
  dieron las mismas aristas que el grafo, así que el coste de no llamarla es bajo. Sale de P5.
- Seis herramientas (`getAgent`, `getAiSkill`, `getPackage`, `getPortal`, `getRelease`, `getRoboticTask`) no están en
  `typeSynonyms` de `devmcp_policy.json`, se toman por genéricas y se llaman con cada objeto: 136 de 142 llamadas
  fallidas y «No disponible» en todo el anexo. Solo datos, sin código. Sale de P5.
- `comprobar_asis.py` (`nombre_citado`, `en_prosa`) da error con un nombre de aplicación «Prefijo_Nombre - Texto»
  (habitual): una aplicación así no pasa nunca F6 paso 7. Y toma `--help` como carpeta. Sale de P5.
- `build_model.py` y `build_annex.py` no desenvuelven los textos localizados del Dev MCP 26.6 (`{es: …}`: formulario de
  inicio, descripción del proceso, nombres de nodo) ni leen `savedBy` del historial (autor de la versión). Sale de P5.
- Los huérfanos cuentan los grupos (`ENTRY_TYPES` de `build_model.py` excluye carpetas y documentos, no grupos), que se
  usan por permisos y el grafo no ve. Sale de P5.
- El inventario y la tabla de huérfanos los escribe la IA y son mecánicos: falta `build_inventario.py`. Sale de P5.
- LEEME iba al 96 % de su presupuesto con 42 objetos; los demás documentos, al 20-54 %. Medir LEEME con una aplicación
  grande antes de tocarlo. Sale de P5.
- `df_docx.js --cambio` no avisa de que una pantalla modificada lleva la captura anterior al cambio. Sale de P4 (F3).
- `devmcp_extract.py` sale con código 14 y sin mensaje cuando `--only` deja fuera la lista de aplicaciones
  (`aplicacion_de`); las demás salidas de ese tramo explican el motivo. Sale de P5b.
- Diagramas por tramos (`drawio_modelo.py`, `partir`): el enlace de entrada dice «Viene del tramo M» sin el paso de
  origen; con varios pasos de igual nombre no se sigue el proceso. Sale de P5b (58 nodos, 5 tramos).
- `bpmn-mapping.md` no tiene fila para el nodo que lanza otro proceso. Baja. Sale de P5b.

### Para Raúl

- Borrar las 6 tablas `cpr_*` (vacías) de la aplicación de prueba de P6 en la base de datos de Indra-spain: el Dev MCP no
  borra tablas. La aplicación y sus objetos ya están borrados.
- Repetir P8 con Codex desde un terminal normal: su sandbox de Windows no arranca dentro de otra sesión.
- El índice del cerebro corporativo da por transcritas 1.692 reuniones y en disco hay 1.095.

## Menores

- Ingeniería inversa: la política por defecto permite `testInterface`, que evalúa cada interfaz con la cuenta de quien
  lee y guarda la respuesta en el anexo. No es prioritario (Raúl, 15 de octubre): se trabaja en entornos de desarrollo,
  con datos ficticios. Si algún día se lee un entorno con datos reales, documentar `--skip "^testInterface$"` en F6 y
  `devmcp-setup.md`. Sale de P5.
- Diagramas: la salida de una puerta que comparte el tramo de su derecha sale ya por su vértice (el codo) y su etiqueta
  va en un tramo suyo; en 1.000 procesos al azar (semilla 11 del generador de `selftest.py`) quedan 8 (antes, 46) con
  una etiqueta donde pasa otro flujo: puertas con tres o más salidas por la derecha, con salidas por los tres vértices y
  el hueco lleno, o cuyo codo añadiría un cruce.
- Finales de línea: en un proyecto con ficheros en CRLF (de otro equipo o de un editor de Windows), los scripts que
  escriben LF (`proyecto.py version`, `leer_fuentes.py`) dan la primera vez un diff de todo el fichero; con `* -text` en
  `.gitattributes`, git no lo iguala. Que conserven el final de línea del fichero que reescriben. Sale de P10.
- Prototipos: el runtime no tiene dos cosas que un proyecto real parcheó tras `build.py` con un script propio: el chat del
  asistente de IA en un `paneLayout` ocupa el alto visible (si no, queda cortado o con hueco), y un enlace abre una
  pantalla del prototipo en otra pestaña (`#ver=<pantalla>&<parámetro>=<valor>`, para «Ver en <sistema>»). Sale de P10.
- Las URL de la documentación de Appian con versión fija (`/help/26.6/`) en `references/data-fabric.md`,
  `devmcp-setup.md` y `agents/data-modeler.md` son del Appian MCP Server: revisar al cambiar de versión.
