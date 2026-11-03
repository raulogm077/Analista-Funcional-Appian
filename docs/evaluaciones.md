# Evaluaciones

Resultados y límites que sirven para decidir sobre el plugin. Los escenarios reproducibles están en
`pruebas/evaluaciones/`; fuentes, proyectos y registros completos permanecen fuera del repositorio.
Lo pendiente se sigue en [siguiente-version.md](siguiente-version.md). Las cifras de cada fila pertenecen
al commit y al alcance indicados; no se suman controles repetidos ni se trasladan resultados a otro código.

## Pendientes de las pruebas aplicados en la rama, desde el 29 de octubre de 2026

Cada fila es un punto de [siguiente-version.md](siguiente-version.md), con lo que lo respalda.

| Punto | Commit | Prueba y alcance |
|---|---|---|
| 1.1 Trampas de SAIL y seguridad de los casos A y B de construcción | `663b4e3` | Contrastadas con docs.appian.com el 29-oct. **Documentado y citado:** `AND_ALL` en filtros sobre una relación uno a muchos (doc 05 §2, doc 06 §5.1); importes con `a!currency()` y la configuración regional, con `dollar()` y `euro()` obsoletos (doc 02 §10.3). La skill oficial recomienda `dollar()`: fila nueva del doc 14, marca comprobada (11 de 11, y desaparece si se corrige). **Visto una vez y sin documentar**, marcado así en el texto y no reproducido hoy: grid con lista vacía de mapas y con dos grupos de filtros vacíos (doc 02 §5.7), `append()` con un texto delante (doc 04 §11) y la cadena de herencia de seguridad en dos niveles, que queda como prueba obligada, no como regla (doc 06 §5.1). Sin prueba de comportamiento con `--plugin-dir` (paso 3) |
| 1.2 `listProcessInstances` no prueba que un proceso no se ejecutara | `e43d2f0` | Fila nueva en el doc 14 §3. Con el build 20261019-134534 (ensayo Informes, 25 y 26-oct) faltaban instancias del diario de IFB cuyo correo sí llegó, y el «total» cambiaba entre llamadas. Con el 20261026-140102 (29-oct, solo lectura): salen las 9 instancias del 22 al 29-oct, sin filtro da 9 de 9 y con paginación (`limit` 3, `offset` 3) 3 de 9, y con `statusFilter` COMPLETED 7 de 7, que es lo filtrado, pero el orden no es por `startTime` aunque la herramienta dice «newest-first». Una sola comprobación: no se da la omisión por corregida. La columna del build lleva solo el último comprobado, para que `comprobar_divergencias.py` no avise de una fila recién contrastada; el anterior va en el síntoma (revisión de Codex, `3f5d1ec`) |
| 1.3 Filas del doc 14 §3 de builds anteriores y el caso que crea `testInputs` | `c6ecd04` | Comprobado el 29-oct con el build 20261026-140102: `createExpressionRule` con `testInputs` sigue dejando «Test Case 1» (por defecto, `NO_ERRORS`, descripción «Test input values»), como en el caso B con el 20261008-132401. Fila nueva en el doc 14 §3: se deja, porque guarda los valores de prueba por defecto, y no cuenta como cobertura de un criterio solo por existir (revisión de Codex, `3f5d1ec`). La regla desechable `IFA_PruebaTestInputsDevMcp` de la aplicación IFA en Indra-spain se borró el 29-oct con la confirmación de Raúl (solo dependía de ella la aplicación; `listObjects` ya no la encuentra). Las demás filas de builds anteriores no se han vuelto a probar: `comprobar_divergencias.py` ya avisa de cada una cuando cambia el build instalado, y se quitan cuando no se vea el síntoma, como dice el doc |
| 1.4 Huecos de la plantilla técnica | `2dc3ade` | Una frase por hueco, del caso B. §0: cuentas de prueba con la configuración regional del cliente; la versión de Appian la da el equipo, porque `getDevMcpVersionInfo` solo da la del plugin; filas «Cuenta del Dev MCP» y «Fuente de datos» (también en `assets/plantillas/tecnico.md`). §1: importes con `a!currency()` (BP 02 §10.3). §3: tabla de relaciones con su nombre exacto. §4: si la aplicación se crea generando grupos y carpetas (una opción), Appian crea `<prefijo> Users` y `<prefijo> Administrators`, y la tabla dice qué perfil es cada uno de los que existan (revisión de Codex, `3f5d1ec`). §7: si se ocultan las vistas News y Related Actions. Las dos últimas, contrastadas con docs.appian.com el 29-oct (creating-applications, record-view). F1 «Cuándo»: una aplicación existente sin acceso ni análisis base se analiza con lo que respaldan las fuentes, separando lo actual y las mejoras, y el checkpoint recoge alcance y desconocidos; cómo seguir o conseguir acceso se acuerda con el cliente, sin decidir reconstruir por no poder leerla; con análisis base, F2 o F3 (revisión de Codex, `3f5d1ec`). La primera redacción (describirla entera; construir aparte o dar acceso) cerraba demasiado el método. Sin probar en un proyecto (paso 3) |
| 1.5 Casos de prueba de reglas con `NO_ERRORS` | `76fa4c4` | Del ensayo Informes (IFA EV-03, «AV-07 con motivo»): un caso guardado sin salida esperada solo probaba que la regla no fallaba. En el esquema de `createExpressionRuleTestCase` (build 20261026-140102), `NO_ERRORS` es la aserción por defecto. Técnico §14: un criterio sobre lo que devuelve la regla lleva `EXPECTED_OUTPUT` o `RESULT_ASSERTIONS`; `NO_ERRORS` responde a un criterio de que no falle (revisión de Codex, `3f5d1ec`). Sin validador nuevo |
| 1.6 Estado del DF tras validarlo y la línea de EV-01 | `f986f2a` | Reproducido el 29-oct con el proyecto ficticio de las pruebas: `version --decision VALIDA` de todas las piezas dejaba el funcional y `proyecto.md` «en validación» sin decir por qué. Ahora pone «Estado: validado» en los dos solo si no queda ninguna pieza del funcional sin 🔒 (un PC abierto cuenta) y, si quedan, las nombra; no toca «DF entregado». En `estado`, EV-01 de una aplicación nueva decía «fuentes: — · versión: —»: ahora «todas las del análisis inicial» y la versión al aprobarla (revisión de Codex, `3f5d1ec`). Si a uno de los dos le falta la línea «Estado:», dice dónde lo escribió y pide el otro a mano (`85dafb9`). Prueba nueva `test_estado_validado.py` (4 casos); selftest del analista: todo correcto (con el texto del 1.5, cuya primera pasada se cortó al cambiar `proyecto.py` mientras corría) |
| 1.7 Lo que `verificar` no compara | `6d8ae46` | Del caso B: `verificar` dio 18/18 sin mirar las vistas ocultas que pedía el cambio. Se elige decirlo, no compararlo: al terminar imprime que no compara relaciones, seguridad de registro, miembros de grupos, datos ni vistas por defecto ocultas, y que eso se lee aparte (`getRecordType`) o lo prueba el QA; lo mismo en «Verificar» de `appian-reverse-engineering/SKILL.md`, donde además «la extracción no ejecuta casos» contradecía los Principios (`validateDesignObjects` sí ejecuta los guardados) y se corrige (revisión de Codex, `3f5d1ec`). Pruebas de ingeniería inversa: 282 pasan, 1 omitida |
| 1.8 Dependencias entre issues: la vista de resumen y las correcciones que caducaban | `f43a018` | Del caso B: ISS-02 enlazaba con `a!recordLink` a un record type cuya vista de resumen hacía ISS-03, que el cálculo ponía detrás porque iba después en §13; y la corrección de una persona caducó cuando una DT nueva cambió el encargo de ISS-02. (a) Técnico §13: la vista de resumen (la fila de su configuración en el record type y la de su interfaz) va en un paso anterior al primer paso de la issue que enlaza a sus registros, porque el orden lo da el primer paso de cada issue (revisión de Codex: moverla dentro del mismo paso no bastaba); si no se puede, se corrige la dependencia. La planificación la prepara el LLM en el técnico y el script respeta ese orden: no se detecta `a!recordLink` en el texto. Su conducta, en el paso 3. (b) `aplica_dependencias`: una corrección caduca solo si desaparece una de sus issues o cambia la lista calculada, no por otro cambio del encargo; las versiones se siguen guardando como rastro. Revisión de Codex (reproducida por CLI): una corrección vigente podía formar un ciclo cuando el análisis cambiaba lo calculado de la otra issue, y entonces ni regenerar ni `--dependencias-automaticas` cargaban el plan. Arreglo (`2128470`): al regenerar, la corrección que forma un ciclo caduca y se avisa; al corregir, una persona sigue sin poder registrar un ciclo. Prueba de ese vecino con su recuperación por la orden existente; falla con el código anterior. Segunda revisión de Codex: el mensaje del ciclo traía también el camino que lleva hasta él, y caducaba una corrección que no estaba en el ciclo; ahora solo nombra el ciclo (`a981036`), con su prueba, que falla con el código anterior. Pruebas reescritas en `test_dependencias.py` (la nueva falla con el código anterior); `cambios.md` §5 al día; selftest del analista: todo correcto. Cambia una regla de diseño de Codex: revisión pedida |
| 1.9 Registrar una decisión que cambia el orden | `4ffa2d3` | Del caso B: el orden correcto (DT, regenerar y después las correcciones, la que deja de depender antes que la que pasa a depender) se dedujo del código. Ahora lo dice `cambios.md` §5, y la cabecera de la issue lleva el motivo de la corrección junto a «Depende de» («corregidas por una persona: <motivo>»). Prueba en `test_dependencias.py`; selftest del analista: todo correcto |
| 1.10 `fila` y `sin_fila` con varias filas; qué hace `show` | `c2d3930` | Del caso B: una fila por paso obligaba a un `show` por fila (8 en un «entonces»). Ahora `fila` y `sin_fila` admiten una lista, en `lo_que_falta` y en `mal_esperado`. `show` ya tenía ejemplo (el de «gasta»); se añade qué hace, contrastado con `sail show --help`: vuelve a leer la última página cargada, sin pedir nada al servidor. Tres casos nuevos en el selftest de QA, con SAIL simulado; todo bien. Su primera pasada dio 1 fallo de montaje: un caso positivo usaba «Env», que el comparador no acepta como principio de «Enviada» (pide la palabra entera); se corrigió el caso, no el comparador |
| 1.11 Datos que presupone cada prueba | `f92e720` | Del ensayo Informes (L5: tres casos de `IFA_TipologiasDelUsuario` fallaron por una tipología que se dejó para el QA) y del caso B (aplicación de solo consulta: el QA descubrió navegando los datos de §3.9). Técnico §14: el caso de una regla que consulta registros dice qué datos presupone; si el criterio pide un recuento, se cuenta sobre esos datos y, si no, la aserción no depende de registros ajenos; si falla por un dato ajeno, se mira el dato antes de reabrir la issue. `appian-qa`: en solo consulta, el «dado» son los datos de carga inicial de técnico §3, que el QA recibe (Entradas, Cuándo y F8 paso 8 lo dicen), no el resto del técnico; si falta uno, el guion no pasa y el escenario queda sin medir (revisión de Codex, `3f5d1ec`). La primera redacción («que esté lo esperado, no cuántos hay») debilitaba un criterio de recuento como el contador de IFA que el QA no cubrió. Sin limpiezas automáticas. Selftests de QA y del analista: bien |
| P5: `--skip` de `testInterface` en la entrada directa de ingeniería inversa | `0cf2344` | De `REVISION-mantenimiento.md` §1.1: F6 paso 2 y `devmcp-setup.md` ya lo decían, pero quien entra directamente por la skill componía `plan` y `extract` sin el filtro. Ahora lo dicen las fases 1 y 2 de `SKILL.md` y la lista de `analysis-workflow.md`, y remiten a `devmcp-setup.md` para el caso de pantallas ya guardadas. Sin flag ni comprobador nuevos. Hallazgo de Codex (3-nov), contrastado con los ficheros. Pytest de ingeniería inversa: 282 pasan, 1 omitida. Sin probar la conducta (paso 3) |

## Ensayo con y sin el plugin, 22–27 de octubre de 2026

El mismo bloque de una aplicación, en tres incrementos y con las mismas reuniones reales, construido en desarrollo por
dos brazos: con el plugin congelado en `7b489e9` y sin él. Evaluó un subagente limpio por incremento con criterios
comunes. Con el plugin, 1 FAIL en los tres incrementos (un recuento que su QA no cubrió); sin él, 2 defectos de
análisis (supuestos sin preguntar), uno arrastrado a un segundo incremento. Coste observado de los brazos: +21 % con
el plugin (+50 %, +82 % y −35 % por incremento), sobre todo en el análisis. Un reparto contable de las transcripciones
(estimación por actividad del turno, con residual; no ahorro causal) asigna la mayor parte a los pasos del método por
incremento y a releer documentos vivos grandes, y poco al texto de skills y referencias. Es el recorrido observado, no
un efecto aislado: a mitad cambió el Dev MCP (26.6 → 26.9). Revisión independiente de Codex del 28-oct, que llevó a
rehacer L1, L17 y L8b. Lo aplicado, sobre la rama (28-oct):

| Problema | Commit | Prueba y alcance |
|---|---|---|
| El inventario del extractor perdía los modelos de proceso (nombre `{en_US: …}`) y dejaba el resto sin tipo (`{grupo: {total, items}}`) | `6503b5b` | Simulador con la forma del 26.9 (la huella cambia a propósito); sobre las respuestas guardadas del ensayo, 83→102 y 118→137 objetos. No es una extracción nueva |
| «Aplicación (con grupos…)» se esperaba como grupo | `318aa54` | Siete tipos de celda |
| `verificar` listaba los campos de más como «distintos de lo esperado» y se cerraron dos issues a mano sin hacer falta | `39d57da` | Se dicen aparte (`conCamposDeMas`) |
| El esperado de una issue pedía el campo de otra: la parte de «`X` — acción «…»», fuera de las comillas invertidas, se perdía | `375863d`, `069c783`, `921af3f` | Vecinos del parser (la lista de campos termina donde empieza otra parte; una parte por celda, como dice la plantilla); en el reparto real de 11 issues, la acción y el campo quedan cada uno en su issue. La heurística por menciones de `39d57da` se retiró: quitaba campos legítimos |
| «Comentar» casaba con «Comentarios»; un guion que gasta su precondición salía verde con la fila ya cerrada | `a7a67fb`, `7a306e6` | Selector por palabra completa; «gasta» en el paso que la comprueba (solo su fallo sale sin repetir) |
| El localizador apuntaba a la copia temporal de otra sesión | `a4aa38a`, `85bd95e`, `d10472b` | `estado` rehace la ruta que ya no existe; si falta, `iniciar`. Sin probar el arranque de una sesión real |
| `proyecto.md` seguía en «siguiente paso: construir» tras construir | `972ee8a`, `d10472b` | Línea «Unidades» automática; el siguiente paso lo escribe el analista, con aviso si aún nombra la unidad |
| `git push` sin remoto; la sesión no aceptaba la autorización que le llegaba en nombre de la persona | `e134698`, `d10472b`, `069c783` | Push si hay remoto y la persona ha autorizado subir (`069c783`); delegación limitada a la decisión y el alcance autorizados |
| Seis DT con un motivo del proyecto daban fallo por no citar BP ni URL | `d10472b` | El comprobador exige el «Por qué»; la cita de lo que afirma de Appian, la plantilla y la revisión (una lista de palabras daba falsos positivos y negativos) |
| Una fila del doc 14 cambiaba el diseño por un límite del Dev MCP | `5ffd52f` | Regla general: lo que el Dev MCP no construye lo hace una persona en Designer |
| La ingeniería inversa prometía no evaluar lógica y valida cada objeto | `acfdc34` | El contrato lo describe (decisión de Raúl: puede usar cualquier herramienta del Dev MCP) |
| Las sesiones en segundo plano no arrancaban en un proyecto nuevo («Workspace not trusted»): su repositorio no hereda la confianza de la carpeta de arriba | `7cfcea8` | `proyecto.py iniciar --confiar`, decidido por Raúl, la escribe en `~/.claude.json`, la vía que documenta Claude Code. Prueba focal, y real en Indra-spain: sin la opción, `claude --bg` no arranca; con ella, arranca, y la confianza sigue guardada con otra sesión abierta. No la marca si la carpeta trae ajustes de Claude Code o `.mcp.json`. `dc2c3aa`: si otra sesión guarda el fichero antes de la última lectura, se vuelve a leer y no se pierde lo suyo (prueba con una escritura inyectada); si guarda en el instante entre esa lectura y la sustitución, se pierde (reproducido por Codex en memoria). Raúl (29-oct) lo da por bueno así: se lanza una vez al crear el proyecto, en cada equipo, porque la confianza es de cada persona y no viaja con el proyecto |
| `verificar` tardaba 9–11 min por issue | `d7ee647` | Misma issue (7 objetos, 13 casos), mismo esperado y servidor 26.9.5: 368 s con el script del ensayo, que validaba la aplicación entera (con peticiones de página que se solapaban), frente a 17 s sin esa validación; otras tres issues, 9–17 s. Apoya que de ahí venían los 9–11 min del ensayo, sin ser un desglose aislado |

Al actualizar el plugin en un proyecto a medias, las issues de una unidad con filas «`X` — parte» vuelven a pendiente
porque cambia su texto: basta verificarlas otra vez.

## Campaña de mejora del 19–21 de octubre de 2026

Código final evaluado: `093b56f`, del 21 de octubre, y después `2b9319c` (QA, con su suite). Es trabajo
local posterior a la entrega anterior; no implica integración en main, publicación ni despliegue. Esta sección
consolida las pruebas de la campaña, conservando los fallos iniciales y las correcciones posteriores como
resultados distintos.

| Problema | Commit | Prueba y alcance acreditado |
|---|---|---|
| Fuentes vacías figuraban como leídas | `5d345d6` | Ocho casos, tres repeticiones: 15/24→24/24 PASS; IDs y originales conservados. Sin ahorro acreditado. |
| El resumen de impacto omitía técnico §13 y la guía describía mal la conservación de IDs | `6fe7c98` | Dos regresiones de impacto y vecinos; mismos casos de IDs y suite 48/48. No mide conducta ante la frase corregida. |
| Destino pendiente de urgencia aceptado por coincidencia de texto | `c27742d`, `5034276` | Ocho casos del puntuador y reproducción separada del motor. La corrección del puntuador no convierte en correcta la ejecución incompleta original. |
| Inicio/localizador, plantilla técnica, primera promoción y derivados históricos | `5034276` | Reproducciones y focales de sus consumidores; suite integrada inicial con un fallo de aserción, seguido de repetición focal. La corrida completa posterior de 401 controles pasa; no se atribuye verde a la fallida. |
| Retornos y evento de borde en diagramas automáticos | `d334d05` | Suite con navegador 145 controles y revisión visual acotada; se conservan avisos previos y geometría manual/importada. |
| Una urgencia aprobada no podía versionarse sobre un evolutivo pendiente | `15b191d` | Secuenciación 22/22 y subtareas 8/8; suite analista 401/0; reaplicación viva posterior PASS. No acredita producción. |
| Un técnico declarado completo sin DT ni datos omitía revisión | `a175330` | Tres regresiones y un vecino; CLI detecta dos errores antes omitidos. Suite 401/0. Detectar el montaje inválido no lo corrige. |
| El cierre administrativo de una urgencia caducaba verificaciones | `2c4bde3` | 26 pruebas de secuenciación y suite 401/0; repetición viva conserva tres issues hechas y verificaciones intactas. Cambios reales de encargo/pruebas siguen invalidando. Al actualizar desde 0.8.0-beta.2 se verifica una vez más la issue con una urgencia ya cumplida o de desarrollo con prueba (siete estados medidos); una huella por datos, en vez del texto, no evitaba ninguno y añadía tres: descartada. |
| Fecha explícita de transcripción ignorada | `25ad755`, `b4ffd2a`, `516bbad` | Alta y recatalogación conservan ID/cuerpo; cabeceras estructurales, campos vacíos, YAML y vecinos negativos probados. La prosa sin marcado estructuralmente indistinguible se acepta por contrato. |
| Primera entrega desde borradores actualizados y varias opciones `--fuente` | `e6ff000`, `952854d` | Módulo de 23 pruebas, reservados y promoción viva con historial/copias conservados; corrección posterior de fuente omitida/mixta, localizador y destino de urgencias. Controles solapados. |
| Un `valor` numérico en `campo` pasaba la revisión del guion y daba un falso defecto: SAIL CLI da `value` como texto también en campos numéricos | `2b9319c` | Reproducido con la respuesta real de la refactorización DEM (`"4"`); QA 87→88/0. La revisión rechaza números antes de repetir; el comparador no cambia. |
| QA no podía afirmar el valor vacío de un campo | `b1fb552` | Suite 57→86 controles, reservado de 13 y repetición viva PASS; distingue vacío, nulo, cero, falso y propiedad ausente. No mide apariencia ni backend universal. |
| Evidencia válida rechazada cuando `as-is` era un alias | `77c8d41` | Siete casos CLI y suite 53/53; mantiene rechazo de escapes/extracción bruta. La propuesta pasa de veinte errores de ruta a cero; no mide calidad semántica. |
| En una construcción de punta a punta en una sola sesión, el 65 % del coste de construir fue releer el contexto del análisis | `8f46534` | F8: una sesión limpia por issue; trampas del Dev MCP comprobadas en esa prueba en el doc 14 §3 (prefijo ya usado, GROUP como entero, ID de grupo, casos de prueba, columnas relacionadas) y comprobación del prefijo en la plantilla técnica. No medido todavía en una repetición. |
| En una segunda prueba, una sesión limpia por issue repitió el arranque en cada una (57 % del coste de construir antes de la primera escritura) y el contexto creció igual | `02620c5` | F8: varias issues por sesión, con corte antes de una segunda pantalla o proceso y tras una compactación. Hipótesis sin medir: la prueba costó unos 85 USD (estimado) frente a 69, con otras fuentes y otro alcance; no acredita ahorro. Doc 14: cuatro filas del Dev MCP y una divergencia, con marcador (19/19). |
| El primer commit automático de `iniciar` confirmó `.env` y `.mcp.json` al migrar una carpeta, y no desbloqueaba la edición en sesiones en segundo plano | `e37e205`, `25499c6` | Retirado. Reproducción con ficheros ficticios, con y sin `.gitignore` previo: sin commit ni índice. El consejo manual ya no dice `git add -A`. |
| Las issues perdían lo que necesita una sesión limpia: párrafos partidos, la DT de seguridad de la Base, los pasos manuales de §13 | `9a604b8`, `25499c6` | Pruebas ficticias nuevas que fallaban antes; selftest 434/0. Descartado quitar la línea repetida en la Base y en la issue que solo cambia una parte del objeto: una línea sobre esa parte que no la nombraba como §13 dejaba de llegar a quien la construye (reproducido). Se tolera la repetición; una prueba lo fija. |
| Puntuación ignoraba campos de evidencia repetidos | `0a07319` | Consumidor corregido y propuestas congeladas reevaluadas: persisten 8/11 visibles FAIL y 3/3 reservadas PASS. No se retocan claves para convertir el fallo en éxito. |
| Se perdía selección al regenerar una fuente idéntica | `b4ffd2a` | Ausente/vacía se regeneran conservando selección por hash; contenido nuevo crea otra identidad sin heredarla. |
| Word incremental perdía preguntas y alcance funcional | `cc76edc` | Focal 6 PASS/9 FAIL→15 PASS/0 FAIL y dos vecinos; suite 416/0. El PDF externo posterior del final se recoge más abajo. |
| Historial no contiguo y resolución de objetos de otras aplicaciones | `0683d43` | Siete métodos CLI, 24 casos de verificador y cinco subcasos de alias; integrados en suites, no cobertura adicional sumable. Ambigüedad/cobertura incompleta detienen resolución sin afirmar ausencia. |
| Auditoría final: tablas, promoción, fechas, Word, notas y QA; avisos de verificación e historial | `093b56f` | Reproducciones antes/después y vecinos en las capacidades existentes. Filas sin cabecera se diagnostican; fuentes y aprobación históricas se conservan; copias idénticas reparan fecha; Índice queda fuera del índice; nota aprovecha lado libre; QA ignora contenedores homónimos. Resultado anterior tras resolución incierta conserva aviso y recuperación. |

Corte anterior, validación registrada de `0683d43`: analista **417 correctos/0 fallos**, inversa **277 correctos/2 omitidos**,
básica **7 skills/0 errores/0 avisos**, códigos 0 y huellas conservadas. El primer intento de inversa
falló por SDK ausente; se conserva como fallo de entorno. No se ha pasado la batería global de CI de esta campaña.
Las pruebas locales del verificador no acreditan por sí solas ejecución en Appian ni ahorro.

| Recorrido | Resultado medido al corte y límite |
|---|---|
| Aplicación nueva y entrega técnica (M1/F9) | PASS acotado de construcción, identidad/estructura, 16 criterios de QA y regresión+una repetición F9. Son los mismos 16 criterios repetidos, no 48 distintos. Regresión: 4/4 casos sobre seis reglas/interfaces; dos sin casos. Doce artículos y 24 autorizaciones restaurados y cotejados. FAIL inicial de cronología conservado: no todas las mutaciones siguieron apertura/reserva/verificación. No PASS integral. |
| Documento existente y evolutivo (M2/M3) | Importación/continuidad y construcción/QA acotadas PASS. Procedimiento PDF externo revisado, sin resolver el índice del exportador estándar ni la caché del DOCX. |
| Refactorización (M4) | Unidad Construida por CLI; comparación del bloque original y nuevo, cuatro estados técnicos, dos roles y dos repeticiones QA PASS acotado. Sin persistencia, visual completa ni seguridad global acreditadas. |
| Fuentes y volumen (M5/V1) | Flujo documental, lotes 1/4/12 y variante orden/duplicado ejecutados. Muestras semánticas PASS tras reparaciones locales; fallos autónomos iniciales de reconciliación/formato conservados. No cobertura semántica exhaustiva ni ahorro causal. |
| Pantalla suelta y extracción (M6/F6) | PASS documental de pantalla y continuación; extracción acotada/reanudación y preflight bajo SDK compatible PASS. Extracción CLI integral NOT MEASURED. |
| Urgencia, defecto y continuidad (M7/F4/D1/D7/C8) | Urgencia/reaplicación técnica, defecto sintético con QA repetida, secuencia temporal nueva y recuperación técnica PASS acotado. Doce casos únicos en reservado de recuperación. Fallo histórico de logger conserva coste exacto desconocido; la aceptación de permisos no sustituye acceso efectivo. |
| QA automatizada | Cinco escenarios únicos y otro escenario con tres cuentas PASS acotado. Los resultados de persistencia observable y aislamiento de lista no acreditan acceso directo, SQL independiente ni seguridad global. |
| Ocho encargos especializados | Ejecutados y revisados con límites; el evaluado de arquitectura mantiene 8/11 visible FAIL y 3/3 reservado PASS. Dashboard estático PASS; ejecución sin red NOT MEASURED. |

Siguen **NOT MEASURED** apariencia/accesibilidad completas, autorización de gestión en servidor,
vigencia causal de la variante interrumpida, atomicidad/concurrencia, roles sin cuenta y producción.
La lectura final de contratos igual a la base no prueba el efecto de las escrituras sin respuesta.
La QA runtime del prototipo HTML permanece sin medir por la política de la herramienta.
El procedimiento externo PDF suma 23 páginas y 68 destinos revisados; no acredita portabilidad ni reparación del producto.
En dos copias de ensayo, otro procedimiento externo conserva la caché editable del índice Word al guardar
y reabrir: 17 y 100 entradas, con páginas/destinos correctos y 19 páginas revisadas. Originales intactos;
Microsoft Word, figuras y otros sistemas sin medir. El exportador estándar no se ha modificado.

**Eficiencia:** el objetivo del 20 % no está acreditado. La primera comparación corregida da
17→15 actividades observables (−11,76 %) y tiempo −14,12 %; omitía ediciones en su recuento inicial.
La comparación posterior 3+3 da medianas 104,87→105,87 s (+0,96 %) y 11→10 actividades (−9,09 %).
La candidata de optimización no se incorpora. Actividad observable, `call_tool` y HTTP son denominadores distintos.
Otra candidata de lectura por apartados, sobre `aee6c56`, tampoco se incorpora: tres repeticiones por versión
dan medianas 91,54→115,82 s (+26,51 %) y 10→11 eventos (+10 %). Las tres candidatas siguieron leyendo
la referencia completa; la mediana de `input_tokens` acumulados por sesión tampoco baja (431.244→435.020).
Una candidata necesitó corregir su propia edición; ese fallo y su coste se conservan, sin atribuirlo a la celda.
La demora de 13.028 s no se reprodujo (714 y 455,56 s); causa no determinada.

La revisión final aceptó los defectos reproducidos de filas sin cabecera, promoción inicial,
recatalogación de copias, título del índice, posición de notas, selección de campos y aviso de lecturas incompletas.
Rechazó migrar verificaciones sin equivalencia, convertir tipos automáticamente o ampliar snapshots sin consumidor.
El recorte visual denunciado resultó ser un error de evaluación propio y quedó rectificado sin cambiar el prototipo.

La tanda final está guardada en `093b56f`: analista **419 correctos/0 fallos**, 462,38 s;
diagramas **155/0**, QA **87/0**, inversa **279 correctos/2 omitidos**, refactorización **53/0** y
básica **7 skills/0 errores/0 avisos**. Quince huellas coinciden entre lo probado, el árbol y el commit.
Las omisiones son una simulación exclusiva de Linux/macOS y Mermaid sin navegador en el entorno SDK aislado;
la suite del analista sí valida Mermaid con el intérprete habitual. No es la batería global de CI.
El primer intento, 418 correctos/1 fallo, tenía un montaje que no escribía la aprobación por depender del antiguo
orden de fuentes. Se conserva el fallo; el montaje ahora crea una fila histórica aprobada explícita y exige
mantener su aprobación y orden. El producto no necesitó otro cambio para ese fallo.
M1/F9 se ejecutaron con el export fijado en `0683d43`; no se atribuyen a una nueva ejecución en este commit.
Coste: cero llamadas MCP y pasos añadidos al recorrido normal de construcción; consultar estado añade dos lecturas
locales para advertir filas sueltas. El marcador sólo se escribe en el aborto de resolución; no hay nuevo estado,
opción ni aprobación. No se atribuye ahorro a esta tanda.

## Diagramas completos en el documento, 21 de octubre de 2026

Sobre `02fa685`, se conserva el PNG completo a resolución doble también en procesos grandes, sin cambiar el
motor ni la geometría. Word mantiene sus píxeles y proporciones, y enlaza el `.drawio` existente. Se retira la
instrucción de partir por número de tareas. Suites: diagramas **156/0**, analista **424/0** y básica **7/0/0**.
El caso de 53 pasos pasa de 79.915 a 284.714 bytes; no se acredita ahorro de tiempo ni se añaden pasos al flujo.
La regeneración en una copia del documento con el motor actual pasa de 15 a 13 páginas, con el mismo texto y
27 tablas; no se recolocan los originales manuales. Revisión visual de las 13 páginas, sin recortes nuevos.
Límite comprobado: Word conserva las imágenes al guardar el DOCX, pero su PDF reduce las mayores a unos
1.332 píxeles incluso con la opción de calidad activada. No se acredita la misma nitidez en ese PDF. En aquel
corte LibreOffice estaba ausente; su conversión estándar se mide y corrige en la prueba siguiente.

## PDF estándar con diagramas completos, 21 de octubre de 2026

La conversión real de LibreOffice sobre `10cce89` reducía las imágenes grandes a unos 1.980 píxeles,
dejaba el índice sin páginas ni navegación y conservaba enlaces al editable relativos al DOCX, incorrectos
desde la carpeta final del PDF. La corrección usa el mismo LibreOffice y su perfil desechable: actualiza el
índice, conserva los píxeles y ajusta los enlaces a `.drawio` al destino final, sin guardar el DOCX.
Las macros y actualizaciones externas del documento de entrada permanecen desactivadas.

Tres conversiones de prueba (salida normal, salida en subcarpeta y documento con tablas) conservan
los DOCX originales y las imágenes de hasta 20.156 píxeles. Las 53 entradas de índice tienen página y
navegación correctas; nueve enlaces a editables se resuelven también en una copia movida del proyecto.
El test específico queda en el job PDF existente de CI; su lector de PDF es una dependencia de prueba.
La ejecución local usa LibreOffice 26.2.6.3 en Ubuntu mediante WSL; LibreOffice nativo Windows/macOS
no se ha medido. El PDF nativo de Microsoft Word mantiene la limitación anterior.

Revisión visual de las 19 páginas renderizadas, sin recortes nuevos en las vistas revisadas. El cuerpo de ambos
documentos conserva texto y número de páginas frente a la conversión anterior. Prueba PDF específica PASS:
dos salidas, copia movida, DOCX intacto, documento externo sin índice y error con PDF anterior conservado.
El primer ensayo de error agotó 300 s; se corrigió el cierre de la rutina y se repitió sin esa espera.
Suite del analista **424/0** en 901 s; básica **7 skills/0 errores/0 avisos**. CI queda pendiente del PR.

Coste: dos invocaciones locales de LibreOffice por DOCX, frente a una; ningún paso de usuario, llamada MCP,
opción ni dependencia de ejecución nueva. Los demás formatos conservan la conversión directa existente.
El DOCX sigue siendo editable y el proceso completo sigue en una figura: no se añade paginación del diagrama.

## Entrega 0.8.0-beta.2 y trabajo anterior

Este apartado resume resultados históricos; no se han repetido al redactar este corte.
El detalle de las versiones anteriores permanece en el historial de este archivo en git.

| Entrega / medida | Resultado útil y límite |
|---|---|
| 0.8.0-beta.2, [PR #19](https://github.com/raulogm077/Analista-Funcional-Appian/pull/19) | Batería Linux/PDF y matriz de siete combinaciones PASS sobre `62ec54b39b354dad5a5393f005e4456b87515ebe`: [batería](https://github.com/raulogm077/Analista-Funcional-Appian/actions/runs/39287727774), [matriz](https://github.com/raulogm077/Analista-Funcional-Appian/actions/runs/39287787906). Estado publicado en [Releases](https://github.com/raulogm077/Analista-Funcional-Appian/releases). No es CI de la campaña posterior. |
| Rendimiento de esa batería | [Ensayo](https://github.com/raulogm077/Analista-Funcional-Appian/actions/runs/39290798292) sobre el mismo SHA: orden 1/2/2/1, 684/441/455/677 s, mismos 13 grupos y códigos 0. Medias 680,5→448 s (−34,2 %); dos muestras por configuración, un runner. No generalizable al trabajo de IA ni a otros equipos. |
| PDF y requisitos de esa entrega | Fixture de 725 párrafos, 51 títulos y dos figuras conservado en CI, 13 páginas y revisión visual por muestra; índice sin números. Hook real Windows PASS en tres combinaciones, instalación visual de escritorio NOT MEASURED. 1.265 citas/312 páginas: cero anclas rotas en aquella comprobación. |
| Automejora del 14–19/10 | Las pruebas reales detectaron pérdidas entre §13, supuestos e issues, colisiones compartidas y límites de verificación. Tras aplicar las lecciones: 25/25 issues reciben sus supuestos/reglas; secuenciación, subtareas y aceptación humana acotada probadas. No sustituyen QA real por rol. Dejaron además mejoras que siguen en el código: `cf22965` (lectura repartida por palabras, un módulo dueño de cada concepto y contradicción compartidos, rangos de IDs técnicos y duplicadas marcadas de forma explícita; `test_ingesta.py`) y `f61e779` (`derivadas --escribir` no borra el texto escrito a mano en el anexo; `test_automejora.py`). |
| Método de la 0.8.0-beta.1, [PR #12](https://github.com/raulogm077/Analista-Funcional-Appian/pull/12), `eedff58` | Contexto por consultas, flujos únicos, repositorio por proyecto, Gherkin, issues y QA independiente. Comparación de retoque alternada 3+3: 3,2→2,1 min, 38→21 llamadas, 1,87→1,14 USD. Dos pasadas antiguas usaron una copia instalada anterior; no atribuir precisión universal. El caso documental largo bajó 124→87 llamadas, con coste 6,73→6,84 USD, sin ahorro monetario acreditado. |
| QA con defectos sembrados de esa fase | Sesiones independientes con SAIL detectaron 3/4; se escapó el color. Navegador detectó 4/4, repetición ~9 min frente a ~75 s. Justifica QA independiente y navegador para criterios visuales, sin deducir equivalencia de capas. El ensayo de quien construyó no era independiente. |
| 0.7.0: evaluaciones ciegas y refactorización | Incoherencias 10/10+3/3, demo 6/6+6/6, evolutivo 10/10+3/3 y enrutado reservado 10/10×3. Refactorización posterior: 10/11 visible y 3/3 oculto; auditoría con ocho matices fuera del puntuador. Las sondas revelaron puntuadores demasiado permisivos: el verde requiere revisar también lo que no cuentan. |
| 0.7.0: recién llegado y diagramas | Recién llegado 21/22→22/22 y 7/7 reservado; palabras 17.293→14.744 (−15 %). Proceso de 130 nodos pasa de una página de 29.536 px a catorce tramos de 1.244–1.528 px. No mide una aplicación real completa. |
| Diagramas antes de beta.2 | Dos lotes de 1.000 procesos: avisos 126→30 y 103→38, sin regresiones por caso ni aumento de dimensiones; residuos conservados. Geometría automática, no garantía de legibilidad universal. |
| Lectura y refactorización reales acotadas | Inventario 248→249 con 23 respuestas, sin leer definiciones; no deriva global. Una regla: 3 casos guardados y cinco bordes equivalentes, expresión original restaurada; historial 1→3 detectado. No equivalencia universal. |
| Pérdidas silenciosas de una prueba real de construcción | Reproducidas en una copia del proyecto y corregidas: tabla de §13 partida por una línea en blanco (error con la línea, sin issues a medias), perfil con paréntesis en el anexo de permisos, escenarios de caso de prueba (`@caso-de-prueba`) sin guion de QA esperado y con su aviso propio, guardado rechazado por la validación cuando lo esperado es el rechazo. La longitud de los textos en `verificar` no se toca: ninguna respuesta guardada trae la longitud. Con datos ficticios en `pruebas/`; no sustituye una nueva prueba real. |
| Fricción de una prueba real de construcción (2) | Medidas en una copia del proyecto: con el técnico «completo» y la primera unidad aprobada, §14 pedía los criterios de 32 historias de otras unidades y ahora pide solo los de la unidad; una historia con perfil «Aplicación» ya no es error; las líneas de apartados marcados «Otra unidad» o con otro EV/URG dejan de ir a la Base y de avisar (68→23 líneas); una DT nueva solo entra en la huella de una issue por lo que cita su «Necesidad» (la de la lista de directores ya no deja pendiente la Base; sigue alcanzando a las issues de las historias que cita). Coste aceptado: una DT que cambia el diseño de un objeto sin tocar §3–§12 ni citar un requisito de su issue no la deja pendiente. Con datos ficticios en `pruebas/`; no sustituye una nueva prueba real. |
| Validar el DF, F1 y permisos (bloque 2b) | Medido en una copia del proyecto real del caso A, sin llamar a Appian: con la validación del DF, `proyecto.py version --decision VALIDA` con las piezas de «Afecta a» (rangos incluidos) pone él mismo 48 marcas 🔒 en 48 piezas y el informe de impacto acepta los rangos al declararlas (la prueba hubo de cambiar 76 marcas a mano y declarar 48 piezas una a una). Quedan a mano las 28 marcas de texto que no es una pieza (objetivo, perfiles, datos, condiciones). F1 deja de pedir «pasar §13 a tabla» (la plantilla ya la trae). `verificar` compara los permisos con los roles declarados (ya no avisa de «contrato parcial») y solo espera la visibilidad de una acción si §7 tiene la columna «Visibilidad verificable»; «acceso efectivo no comprobado» sigue una vez por issue. Con datos ficticios en `pruebas/`. |
| «Otra unidad» solo con marca explícita | Medido en una copia del proyecto real del caso A: una línea (o el apartado `### 3.n` que la contiene) es de otra unidad solo si empieza por «Otra unidad», con su id si se quiere; una mención suelta de otro EV o «otra unidad» a mitad de frase ya no la saca de la Base ni del aviso (antes se perdía, por ejemplo, «En EV-01, mantener la segregación de funciones ya implantada en EV-02.»). Líneas en la Base y en el aviso: 23→30 (de 68); las 7 que vuelven son filas con «otra unidad» dentro de una celda, que la marca no cubre. Prueba: negativo con esa frase de §4, positivo con «Otra unidad (EV-02).» y «Correo de EV-02» pasa a ser negativo (solo demostraba la heurística). Con datos ficticios en `pruebas/`. |
| Cuatro huecos pequeños de una prueba real de construcción | Una frase cada uno, sin opción nueva: criterios que dependen de la fecha de hoy (fecha fija y caso de prueba de regla, en la plantilla del funcional §4 y en técnico §14); una fuente inservible usa la marca de duplicada con su motivo real; los valores de referencia que cambian por entorno se dicen en «Valores iniciales» (ningún script lee la columna «Cambia por entorno» de las constantes, así que no se añade otra). `proyecto.py iniciar` ya hacía `git init`: entonces hizo también el primer commit con lo que crea; se retiró después (`e37e205`, `25499c6`, en «El primer commit automático de `iniciar`»). Prueba: selftest de `appian-functional-analyst` con el proyecto recién creado ya confirmado. |

Decisiones vigentes de esas fases: `getAgent` queda aparcado tras el reporte a Appian; no reiniciar en bucle
extracciones con error de acceso. La activación/comportamiento con Claude sigue **NOT MEASURED** y se omitió
expresamente para aquella entrega, decisión de entonces: hoy, como dice `CLAUDE.md`, un cambio de comportamiento se
prueba con `--plugin-dir` (paso 3 de `siguiente-version.md`). La instalación visual tampoco se convirtió
en puerta automática. Un resultado técnico verde no aprueba visual, seguridad efectiva, efectos persistidos ni pase.
La extracción no usa `getObjectDependents`: su parámetro `object` no se deduce y la herramienta queda en alcance
manual (`dependientes_de` lo dice). En P5, los dependientes pedidos a mano coincidieron con las aristas del grafo; en
P5b, `calledBy` salió 0 donde la llamada a mano daba una constante, y quedó sin comprobar si al grafo le falta esa
arista. `verificar` sí la usa para los casos de lo que depende de una issue.
