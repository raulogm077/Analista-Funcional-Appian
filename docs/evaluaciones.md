# Evaluaciones y cierre de fases

Resultados de las evaluaciones del plan `docs/plan/2026-10-07-integracion-ingenieria-inversa.md` y, al cerrar cada
fase, el resumen de cambios, lo aprendido y lo que queda aplazado, con la tarea que lo recoge. Los proyectos de prueba
están en `$PROYECTOS_PRUEBA`, fuera del repositorio; aquí solo los resultados.

## F4 · Diagramas (9 de octubre de 2026)

Rama `f4-diagramas`, de `main` c656d21 al merge. Versión 0.7.0-alpha.3.

### Qué cambia

- **Un solo exportador y un solo pintor (Tarea 12).** Ingeniería inversa dibuja y exporta con `diagrama.py` de la skill
  de diagramas; se retiran `bpmn_layout.py`, `validate_mermaid.py` y `render_diagrams.sh`. El carril de lo que hace
  Appian es «Aplicación», una integración sin connected system es un participante externo y el índice de procesos no
  pide «Vista» si ningún proceso lanza a otro.
- **Procesos grandes en tramos (Tarea 12).** Con `"tramos": true`, un proceso que existe y no cabe en 1.600 px sale en
  varias páginas del `.drawio`, unidas por eventos de enlace, y un PNG por página; `leer`, `comparar` y `bpmn` deshacen
  los enlaces y el `.bpmn` es uno. `crear` y `actualizar` dicen qué pasos lleva cada tramo, y el nombre de la página
  también.
- **Sin navegador (Tarea 12).** Con la colocación por capas, `crear`, `actualizar` y `comparar --aceptar` escriben el
  `.drawio` y el `.json` igual, avisan «sin PNG» y salen con 2; si había PNG, lo quitan. Se prueba con
  `DIAGRAMAS_SIN_NAVEGADOR=1`.
- **Los datos de Appian en el diagrama (Tarea 10).** El nodo, la expresión del temporizador, el proceso llamado y la
  condición de cada salida, en «Editar datos» de draw.io y en el `.bpmn` (válido contra el XSD de BPMN 2.0). Un paso
  para los errores; la nota es un corchete que se ensancha con su texto.
- **`mermaid.py` en la skill de diagramas (Tarea 11).** Comprueba y pinta los bloques Mermaid de un Markdown (`--md`),
  avisa si uno pasa del ancho legible y acepta comodines también en Windows. El analista lo usa en lugar del suyo.

### Pruebas

| | Antes (F3) | Después |
|---|---|---|
| `MNT_PM_GestionOrden` (130 nodos), `.drawio` | una página de 29.536 px | 14 tramos de 1.244 a 1.528 px |
| PNG | uno de 22.171 px (la skill promete 3.200) | uno por tramo |
| `.bpmn` | del exportador de ingeniería inversa | uno, de `diagrama.py`, válido contra el XSD |
| Pruebas de ingeniería inversa | 139 | 140 |

- Selftest de la skill de diagramas con y sin navegador; `--completo` en verde, también con Python 3.9.
- La revisión de la fase reprodujo con tres puertas seguidas conexiones que no existen en la colocación por capas. El
  selftest comprueba ahora sobre la geometría que sale (no sobre un caso) que ningún flujo pasa por un paso ajeno ni por
  la etiqueta de otro flujo y que dos flujos sin extremo común no van por la misma recta; con el JSON del revisor, de 9
  conexiones falsas a 0.

### Lo aprendido

- Un dibujo puede ser correcto en el `.drawio` y engañar a la vista. La prueba que lo atrapa mide la geometría (qué
  cruza qué), no el XML; conviene que toda colocación nueva pase por ella.
- Lo que se hace sin navegador tiene que dejar la carpeta coherente: un PNG que ya no es del dibujo es peor que ninguno.
- Partir en páginas resuelve el ancho pero crea otro problema, encontrar un paso; la salida de `crear` tiene que decir
  dónde está cada uno.
- El comprobador del plugin también es código del plugin: la anotación `int | None` de F3 lo rompía en Python 3.9 y
  ninguna prueba lo veía, porque todas corren con el Python del equipo.

### Aplazado

Ocho menores de la revisión y de su pasada de correcciones, en `docs/siguiente-version.md` («Diagramas»): la línea de
una nota sobre la etiqueta de su puerta, el `.tmp` que queda si falla la relectura, `calledElement` y los errores sin
tarea en el BPMN, el bucle de dos pasos en Mermaid, `__pycache__` de las pruebas, verticales largas en la colocación por
capas, el nombre de la página tras renombrar a mano y la salida de `mermaid.py` sin argumentos.

## F3 · Precisa y sin relleno (8 de octubre de 2026)

Rama `f3-precisa-sin-relleno`, de `main` 795ec61 al merge. Versión 0.7.0-alpha.2.

### Qué cambia

- **Reglas de prosa en un solo sitio (Tarea 4).** `redaccion.py` del analista (muletillas, frases, párrafos repetidos);
  la prosa de ingeniería inversa sigue `redaccion.md`, sin lo que allí es solo del DF.
- **`as-is/datos/` (Tareas 5 y 8b).** Lo único que leen las demás skills de ingeniería inversa: inventario (con lo que
  se cita con cada record type), dependencias (y lo que queda fuera de la aplicación), hallazgos, procesos y lo que no
  se pudo verificar. Formato en `references/datos.md`.
- **`comprobar_asis.py` (Tarea 6).** Objetos inventados, certezas sin evidencia, evidencias que no llevan al anexo,
  cifras distintas de `summary.json`, marcadores y enlaces rotos, NV y preguntas sin cerrar; avisos de redacción y de
  presupuesto de palabras. La fase 8 lo exige sin errores.
- **Aplicación ficticia MNT (Tarea 7).** 44 objetos con 11 malas prácticas, 22 preguntas y un conjunto oculto de 7
  preguntas y 3 malas prácticas escrito a ciegas. Tres reglas de una aplicación común (CMN) que no está en la extracción.
- **Preguntas primero, hechos y no consejos (Tarea 8).** Cada documento empieza por las preguntas que responde; toda
  tabla con certeza lleva evidencia; sin recomendaciones.
- **Disciplina de evidencia (Tarea 8b).** Lo no verificado queda como NV, con lo que hace falta para resolverlo; nada
  se da por inexistente sin decir dónde se buscó; la definición no se toma por la ejecución; la revisión cierra sus
  preguntas. La marca de inferido pasa a 🔶.
- **Una entrada (Tarea 9, paso 3).** LEEME y el resumen ejecutivo se remitían el uno al otro y ahora son un documento;
  fuera la tabla que repetía las preguntas de cada documento.
- **Lo que encontraron las medidas.** El extractor reconoce los tipos habituales aunque la aplicación no tenga ninguno
  (con MNT, `getAiAgent` daba 27 errores); ningún script deja `__pycache__` dentro del plugin, en las cinco skills, y
  `comprobar_plugin.py` lo exige; el aviso de respuestas reutilizadas solo sale si son de hace más de una hora; `doctor`
  guarda su salida en el proyecto (`--out`) y la fase 0 dice cuándo usar `--mcp-server-name`.

### La evaluación del recién llegado (Tarea 9)

La skill documenta MNT contra el simulador; otro agente, que solo lee `as-is/` sin `extraccion/`, responde las
preguntas. «Antes» es la skill en `f3-antes` (4a7a09f, tras la Tarea 7); «después», con las Tareas 8, 8b y el paso 3.

| | Antes | Después |
|---|---|---|
| Preguntas visibles | 21/22 (falla Q-21, obligatoria) | 21/22 (Q-21 bien) |
| Preguntas ocultas | 7/7 | 7/7 |
| `evidencia.py` | falla: los CMN no salen fuera de la aplicación | bien |
| `comprobar_asis.py` | 19 errores con el de entonces (58 con el de ahora) | 0 errores, 0 avisos |
| NV registrados | — | 8 |
| Palabras (total) | 16.741 | 17.293 (+3,3 %) |
| Palabras sin líneas «Responde a» ni tablas | 7.932 | 7.122 (−10 %) |

- **Criterio: se cumple todo salvo «menos palabras que antes».** Lo que crece son las líneas «Responde a» (523 palabras)
  y las tablas, por la columna de evidencia y el «Para qué» de INVENTARIO, que piden las Tareas 8 y 8b; la prosa baja un
  10 %. Una primera medida «después», sin el paso 3, tenía 17.741 palabras (contadas igual que las de la tabla).
- **Protocolo.** Con la primera instrucción («cada elemento corto»), quien respondía resumió los tres CMN como «las
  reglas CMN_» y Q-21 contaba como fallo aunque LEEME los nombra. La instrucción pasa a pedir cada objeto por su nombre
  (`recien-llegado/README.md`) y las cifras de la tabla son las de las dos medidas respondidas con ella.
- **Q-10, ambigua en la documentación.** 09 marcaba «Por entorno: No» en las constantes porque ninguna tiene la marca
  de Appian, y quien responde concluía que ninguna cambia por entorno, aunque `MNT_URL_ERP_PRE` guarda la URL de
  preproducción. Lo introdujo la Tarea 8; la revisión de la fase lo corrige con dos columnas, «Depende del entorno» y
  «Marca de entorno». Se vuelve a medir en el punta a punta de F9.
- **El criterio de palabras lo decide Raúl.** Aceptado de forma provisional en el merge (8 de octubre); si prefiere
  recortar las preguntas de las plantillas, se hace en F4.
- Proyectos en `$PROYECTOS_PRUEBA`: `MNT-antes/`, `MNT-despues-1/` y `MNT/` (el que usan las Tareas 15 y 22).

### Lo aprendido

- Una medida con un agente que sigue la skill de punta a punta encuentra lo que las pruebas no ven: los dos informes
  dieron 17 y 18 puntos de fricción, la mitad de diagramas. Conviene repetirla al cerrar cada fase que toca una skill.
- La instrucción de quien responde también se mide: «corto» le hizo resumir nombres. Las instrucciones de las
  evaluaciones se fijan en su README y se usan iguales en «antes» y «después».
- Contar palabras sin separar lo que se añade a propósito (preguntas, evidencia) de la prosa da un criterio que castiga
  lo que la fase pide. La cifra útil es la prosa, que baja.
- Con una sola medida por lado, una diferencia de pocos cientos de palabras está dentro de lo que varía de una
  ejecución a otra.
- La batería tiene techo: 7/7 y 21/22 en los dos lados, y solo Q-21 distingue. Para las Tareas 15 y 22 hacen falta
  preguntas que «antes» falle.
- La revisión de la fase, con sondas sobre los proyectos reales, encontró lo que ni las pruebas ni las medidas vieron:
  una regresión de la propia fase (Q-10), `objetos` sin validar en el contrato de `datos/` y un error falso con los
  objetos de fuera de la aplicación.

### Aplazado

| Dónde | Qué | Tarea |
|---|---|---|
| Vía draw.io de `process-modeler.md` y `appian-diagramas-bpmn` | Un proceso de 130 nodos da un `.drawio` de 29.536 px y un PNG de 22.171 px (la skill promete 3.200); la vía draw.io no parte en tramos; «usa subprocesos» choca con «no inventes subprocesos» | 10 y 12 |
| `scripts/render_diagrams.sh`, `validate_mermaid.py` | Temporales en `/tmp`, `--batch` recorre `extraccion/`, aviso de caché de Chrome con `PUPPETEER_EXECUTABLE_PATH`; el validador reescribe sin avisar | 11 (se retiran) |
| `references/mermaid-rules.md` | Un subgraph de un solo carril se dibuja en horizontal; el diagrama por capas pasa del ancho | 11 |
| `references/bpmn-mapping.md`, `pm-template.md` | Carril «Sistema» frente a «Aplicación»; integración sin connected system como participante externo; caja de nota cortada en el PNG | 10 |
| Plantilla `08-procesos-bpmn/indice.md` | «Vista» obligatoria aunque ningún proceso lance a otro | 12 |

## F2 · Ingeniería inversa en el plugin (8 de octubre de 2026)

Rama `f2-ingenieria-inversa`, de `main` 4938606 al merge. Versión 0.7.0-alpha.1.

### Qué cambia

- **Skills solo con lo que usan al trabajar (Tareas 0 y 0b).** Las pruebas y sus datos ficticios pasan a
  `pruebas/<skill>/` y el caso de ejemplo de prototipos sale del plugin. `comprobar_plugin.py` da error si una skill
  lleva pruebas, ejemplos, un proyecto o la marca de un cliente, y `--completo --plugin` pasa las mismas pruebas sobre
  la copia del paquete.
- **La marca de cualquier cliente (Tareas 0b y 0c).** `appian-prototipos-aena` pasa a `appian-prototipos`, con la
  marca estándar de Appian por defecto; la de un cliente va en `<p>/prototipo/`. `marca.py web` saca de su web los
  colores, el logo y la tipografía, y `marca.py crear`, la configuración completa (Site, perfil CSS, paleta, estados,
  gráficos y `marca-<id>.md` para quien construye) con el contraste AA ya ajustado.
- **Ingeniería inversa, solo el bloque A (Tarea 1).** Documenta sin juzgar ni rehacer. El bloque B espera a F5 en
  `docs/bloque-b/`.
- **La extracción, en el proyecto y tal cual (Tareas 2 y 2b).** `as-is/extraccion/` con rutas cortas; al repetir o
  retomar no se vuelve a pedir lo descargado. Nada se oculta (Raúl, 8 de octubre): la detección de secretos sigue,
  también en cabeceras y literales SAIL, porque un secreto escrito en la app es un hallazgo.
- **Alta en el plugin (Tarea 3).** Ingeniería inversa entra en la prueba completa y en la regla común de dudas de
  Appian, igual en las tres skills que la llevan y válida con el plugin instalado. El comprobador exige `appian-docs`
  en `.mcp.json`.
- **Revisión de la fase.** Una carpeta es de una aplicación y un entorno: con otro entorno, el extractor sale con 15
  salvo con `extract --refresh`, y avisa cuando reutiliza respuestas de otra ejecución. La orden zip del README deja
  fuera lo de desarrollo (lo comprueba `comprobar_plugin.py`) y el paso 5 de prototipos entrega el perfil CSS que
  escribe `build.py`, también con una marca hecha a mano.

### Pruebas

- `comprobar_plugin.py --completo`: 5 skills, 0 errores y 0 avisos, en el repositorio y en la copia del paquete.
- Ingeniería inversa: 89 pruebas en verde, entre ellas retomar en otra ruta, con espacios y en otro entorno.
- Scripts de `skills/` y `pruebas/`: se analizan e importan con Python 3.9.
- Galerías y plantillas: se regeneran idénticas, byte a byte. La galería de antes, construida con el kit nuevo y la
  marca de AENA del historial, solo cambia el gris del pie del visor de documentos.

### Lo aprendido

- La revisión por tarea, con agentes y varias rondas, alargó la fase. Desde F3: una revisión independiente por fase y
  las tareas pequeñas en línea (Raúl, 8 de octubre).
- La decisión de no ocultar nada llegó a mitad de fase y dejó sin objeto el saneado de la Tarea 2 y una ronda de
  correcciones. Las decisiones de datos y privacidad se toman antes de empezar una fase. Desde ahora, el alcance está
  congelado hasta F9 y lo nuevo va a `docs/siguiente-version.md`.
- La revisión de la fase vio lo que no ven las de tarea: el entorno al retomar (cruza las Tareas 2 y 3), la versión
  sin subir y la orden zip del README. Se revisa la rama entera y también la copia del paquete.
- Claude Code no actualiza un plugin mientras su versión no cambia. Cada fase que llega a `main` sube la versión
  (0.7.0-alpha.N) y F9 cierra con la 0.7.0-beta.1.
- Con el plugin instalado, las herramientas MCP se llaman `mcp__plugin_<plugin>_<servidor>__…`: los textos de las
  skills nombran el servidor, no el prefijo.
- Las restricciones globales (rutas cortas, nada fuera de `<p>`, nada oculto) se prueban ejecutando y mirando el
  disco, no buscando frases en los textos.

### Aplazado

| Dónde | Qué | Tarea |
|---|---|---|
| `references/presentation-rules.md` | «códigos internos de patrones (DAT-02)», resto del bloque B. En el plan, «… y usuarios» ya sobra | 4 |
| `scripts/detect_secrets.py` | Falso positivo con `headers: {Authorization: "Bearer " & cons!X}` en un mapa SAIL, con su prueba | 6 u 8b |
| `assets/markdown-templates/LEEME.md`, `agents/pdf-publisher.md`, `references/response-format.md` | «reingeniería» → «ingeniería inversa», y `reingenier` en `PROHIBIDO` de `test_sin_bloque_b.py` | 8 |
| `agents/ui-rules-analyzer.md` | «independientes de la tecnología… sin abrir el código original» (enfoque de reconstrucción) | 8 |
| `agents/data-modeler.md`, `agents/interface-analyzer.md` | Punteros viejos a `docs-mcp-usage.md` y caché de consultas web | 8 |
| `SKILL.md` de ingeniería inversa | El último punto de la regla común («qué conviene hacer») llega a los subagentes | 8 |
| `scripts/build_model.py` | `slugify` sin tope nombra `extraccion/procesos/`, `anexo/<tipo>/` y `08-procesos-bpmn/`: el recorte de `safe_name` y una prueba con un nombre de 150 caracteres | 8b o 12 |
| `scripts/detect_secrets.py`, `references/response-format.md` | La ubicación de un secreto en un `.json` lleva el prefijo `response.`; «(detalle en el registro de 09)» | 8b |
| `README.md` | Quien solo tiene el paquete no puede comprobar su equipo: la comprobación pide el repositorio | 23 |
| `SKILL.md` de ingeniería inversa | Usa `python3` sin «en Windows, `python`» | 24 |
| `README.md` | Requisitos de ingeniería inversa (`uv`, Dev MCP 26.5+ con rol Designer, solo en el equipo); retirar también la `appian-reverse-engineering` suelta; en «Confidencialidad», que `as-is/` lleva la extracción tal cual y se sincroniza | 25 |
| `skills/appian-functional-analyst/SKILL.md` | La descripción dice «no audita aplicaciones existentes»: «no documenta…» | 28 |
| `.claude-plugin/plugin.json`, `marketplace.json` | La ingeniería inversa, en la descripción y en las keywords | 28 o 31 |

Sin tarea en este plan, en `docs/siguiente-version.md`: lo pendiente de `marca.py` y las copias de conflicto de
OneDrive en la extracción.

Hechas en F3 las filas de las Tareas 4, 6 u 8b, 8, 8b y 8b o 12; quedan las de las Tareas 23, 24, 25, 28 y 31.
