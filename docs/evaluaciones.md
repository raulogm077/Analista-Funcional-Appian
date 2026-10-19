# Evaluaciones

Resultados de las evaluaciones de cada versión, la más nueva primero: las cifras con las que se vuelve a medir y lo
aprendido. Las evaluaciones están en `pruebas/evaluaciones/`; los proyectos de prueba, en `$PROYECTOS_PRUEBA`, fuera del
repositorio; aquí solo los resultados. Lo que queda pendiente está en `docs/siguiente-version.md`.

## Temas aplazados: medidas y cambios antes de publicar (19 de octubre de 2026)

Segunda fase local, solicitada por Raúl después de cerrar la primera tanda. Alcance y decisiones en
`docs/plan/2026-10-19-temas-aplazados.md`; integración inicial en `codex/aplazados`, partiendo de `84d2b24`,
incorporada después a la rama única `automejora-pruebas`. Las evidencias
quedan en `$PROYECTOS_PRUEBA/aplazados-codex-20261019/`. Esta sección recoge solo las medidas terminadas; no acredita
el cierre de los cambios que el plan mantiene en curso.

| Tema | Medida y resultado |
|---|---|
| Borrador automático de §13 (E1) | P10 tiene 141 objetos. Buscar nombres literales encuentra 91, pero no identifica su función. Leer únicamente columnas de definición produce 51 candidatos: 50 objetos correctos (35,5 % del total) y un campo que no es objeto. No se añade un generador general con esa cobertura; situación, cambio, finalidad y objetos restantes necesitan interpretación. |
| Dependencias corregidas por una persona (E2) | En copia de P10 se retira una arista y se restaura el cálculo automático, conservando versiones y objetos. Historial con motivo, actor y fecha; ciclos rechazados; correcciones caducan al cambiar el encargo o las dependencias relacionadas. 95 ficheros originales conservan su SHA256. |
| Suite analista tras E2 | 393 comprobaciones correctas, incluidos siete casos nuevos de correcciones. PDF con LibreOffice sigue sin medirse. |
| Suite analista integrada | 399 comprobaciones correctas, exit 0, 498,3 s, tras integrar D1, D7, C8 y la lectura interrumpida. Incluye sus regresiones focales; PDF con LibreOffice sigue sin medirse. |
| Inversa integrada | Corrida completa: 243 correctas, ocho fallos y dos omisiones, en 689,8 s. Siete fallos eran el simulador de permisos sin el nuevo método de interrupción; otro, un comentario que activaba el detector de vocabulario. Corregidos, los dos módulos pasan sus 23 casos (quince ya habían pasado). El caso Mermaid omitido por falta de Playwright en uv pasa aparte con Python local. Resultado conjunto: 252 casos distintos correctos; solo se omite el wrapper exclusivo de POSIX. La corrida completa inicial no se registra como verde. |
| Tamaño de issues (D7) | 25 issues: mediana de 63 líneas; Base, 289 líneas y 68 objetos. Dos agrupadas tienen 19 objetos/20 requisitos y 13 objetos/12 requisitos. No se decide la partición solo por longitud. |
| Subtareas (D7) | 13 de esas 25 issues reciben 43 subtareas derivadas de §13; las doce de un solo paso no añaden tabla. Avance guardado por versión y conjunto de objetos, reversible; un objeto repetido se asigna una vez y conserva las instrucciones de sus pasos. Marcar todo no verifica, cierra ni desbloquea otra issue. Ocho casos focales correctos. |
| Secuenciación (D1) | La segunda unidad espera si comparte una pieza pendiente. Las huellas de los artefactos protegen el encargo anterior al regenerar, también cuando desaparece evidencia; el cierre manual no evita esa protección. Se conservan retoques independientes del mismo registro. Catorce casos focales correctos. |
| Permisos (C8) | Compara roles y grupos declarados del proceso y expresiones de visibilidad soportadas de sus acciones. La aceptación humana queda ligada a versión, objeto, entorno y configuración, con historial y revocación. Los cierres manuales no saltan diferencias confirmadas. Quince casos focales del analista y 57 de inversa afectada correctos; no se suman a las suites completas. El acceso efectivo por rol sigue sin medirse. |
| Tipos del extractor | Constantes y listas específicas conservan el tipo de objeto; el tipo del valor no selecciona herramientas de grupos, documentos o procesos. `getRecordEventsConfig` solo se planifica para record types. Once casos focales correctos. |
| Parada ante error de acceso | 32 casos focales correctos: cola, reintentos, paginación, respuesta previa, reanudación, `verificar` y `deriva`. Un error de autenticación no se convierte en objeto ausente. El analista avisa de la última lectura interrumpida conservando resultados y bloqueos previos. No controla llamadas ya iniciadas ni el login interno de DevMCP. |
| Lectura real acotada | Dos llamadas por el MCP conectado, una por herramienta y sin reintentos: `getApplication` correcto en 0,7 s; `getAgent` devuelve HTTP 401 en 383 ms, aunque el usuario puede verlo en Designer. El bundle usa clientes y autenticaciones distintos. No se cambiaron credenciales, permisos ni DevMCP. |
| Etiquetas BPMN | Mismos 1.000 casos con semilla 11: etiquetas atravesadas por otro flujo, 8→0; conexiones falsas detectadas, 142→126; solapes de nodos, 0→0; cruces, 2.246→2.246. Sin empeoramiento caso a caso en esas medidas. Los 126 defectos de conexión restantes siguen siendo una limitación de la colocación. |
| Suite diagramas | Completa con navegador: 135 comprobaciones correctas; sin navegador: 58; cinco casos focales finales. Son recorridos que se solapan, no cifras para sumar. PNG difíciles revisados antes y después. |
| Arquitectura (E5) | Cinco capas con cinco cajas: 1.322 px con conexiones paralelas, 1.586 px con etiquetas de 45 caracteres y 4.442 px con conexiones densas. Vista general agrupada: 346 px. La referencia aplica el límite existente de 1.600 px al render y conserva objetos y relaciones en el detalle por capa o las tablas. |
| Enlaces del prototipo (D11) | Ocho casos de navegador correctos: pestaña nueva, parámetros escapados, números conservados como texto, recarga, historial y aislamiento de claves. Suite de prototipos: 46 comprobaciones correctas, incluidos los seis casos del chat. |
| Contraste sobre imágenes | Medición real con Playwright y fondo compuesto: cuatro textos visibles **PASS**, mínimos 17,58; 17,28; 11,73; 11,73 frente a umbrales de 3 o 4,5. Las otras ocho apariciones están ocultas por diálogos y siguen **NOT MEASURED** como contenido no visible; cero fallos visibles. Evidencia en `diagramas/REVISION-CONEXIONES-Y-CONTRASTE.md`. |
| Conexiones BPMN pendientes | Reproducidos los 126 avisos en 71 de 1.000 procesos: 38 intersecciones de etiquetas y 88 tramos coincidentes. Los casos 43 y 677 confirman defectos reales; el 46 muestra posible sobreconteo corto en un codo. El trazador no se cambió: una corrección de rutas y etiquetas requiere comparar la campaña caso a caso. Evidencia en `diagramas/REVISION-CONEXIONES-Y-CONTRASTE.md`. |
| Ejecutor de batería (E7) | Cinco pruebas del contrato correctas: concurrencia real, modo secuencial, aislamiento de salida, entorno/carpeta y conservación de fallos. QA+refactorización reales: 176,7 s en serie frente a 126,4 s con dos grupos (28,4 % menos); ambos grupos pasan en ambos recorridos. |
| Claude con `--plugin-dir` | La CLI identificó el plugin local 0.8.0-beta.1 y cero servidores MCP. La primera petición devolvió HTTP 429 `usage_limit_reached` antes de responder o usar herramientas. D1, D7 y C8 siguen **no medidos** como comportamiento de Claude; no hubo reintentos. Evidencia en `claude-comportamiento/RESULTADOS.md`. |
| P8 con Codex en terminal | El proyecto ficticio generado resuelve la ruta del plugin y `proyecto.py estado` funciona directamente. El proceso separado de Codex no pudo leer `AGENTS.md` ni `.appian-plugin.json` por la política del entorno; no ejecutó el script. **No medido**, aunque el proceso devolviera código 0. Evidencia en `claude-comportamiento/RESULTADOS.md`. |
| Aviso de requisitos en Windows | Con `REQUISITOS_SIN=docx` y carpeta personal temporal, `requisitos.py --breve --como python` mostró la carencia y creó la marca de aviso. La orden real del hook, tras sustituir `${CLAUDE_PLUGIN_ROOT}` como hace Claude, también salió con código 0, mostró el aviso y creó la marca en PowerShell 5.1. Es una comprobación local del hook, no una instalación visual en Desktop. |
| Anclas de documentación | `python pruebas/comprobar_anclas.py` descargó 312 páginas y revisó 1.265 citas, 517 con ancla; código 0, cero enlaces o anclas rotos y sin errores de red. Evidencia en `anclas/RESULTADO.md`. |
| PDF y batería en CI | El workflow prepara un job Linux con LibreOffice que debe convertir un DF ficticio y comprobar el texto del PDF; incluye una medición manual 1, 2, 2, 1 de la batería completa. YAML y generación local de Word comprobados; la conversión real y el rendimiento de las cuatro pasadas siguen **no medidos** hasta ejecutar Actions. |
| Word local | El DF ficticio se abrió en Microsoft Word en modo de solo lectura: 13 páginas, 36 tablas y dos figuras. Confirma apertura y estructura del documento; no sustituye la conversión real del PDF en CI ni una revisión visual de cada página. |
| Lectura acotada de aplicación real | Una extracción restringida a una regla terminó en 29,7 s con diez respuestas correctas, cero errores y sin login. Dos lecturas de la versión actual coinciden. LEEME completo y deriva global siguen **NOT MEASURED**: al menos unas 1.073 lecturas de objetos serían necesarias para la extracción completa de 248 objetos con la política segura actual. Evidencia fuera del repo en `gde-metrica-acotada/RESULTADO-MEDICION.md`. |
| Refactorización real acotada (E3) | Se releyeron regla, dependientes y casos antes del ensayo autorizado. La versión inicial y la propuesta dieron 3/3 casos guardados y cinco bordes con resultados iguales; se restauró la expresión inicial exactamente y 3/3 casos siguen pasando. `deriva` detectó 1 cambio por historial 1→3, sin nuevos ni retirados; el contenido final no cambió. Demuestra detección de edición de una regla, no sensibilidad global ni equivalencia universal. Evidencia fuera del repo en `gde-metrica-acotada/refactor/ensayo-20261019/INFORME-ENSAYO.md`. |
| Inventario de extracción restringida | Una lectura real con `--solo` y `--only` en copia aislada redujo el catálogo de 248 a 217 objetos, omitió 32 modelos y degradó a `unknown` el tipo de 114 UUID existentes. Es una pérdida de cobertura de la lista filtrada, no evidencia de bajas reales. El arreglo conserva inventario previo y marca cobertura parcial; regresiones ficticias y focales de extracción correctas. |
| Evaluación ciega de malas prácticas | No se encontró una copia válida del `as-is` de MNT en las carpetas de proyectos, documentos, descargas y temporales revisadas. Los candidatos eran de otras aplicaciones; no se generó una propuesta sustituta ni se puntuó. |

El nuevo ejecutor limita la concurrencia a dos grupos, imprime sus tiempos y conserva `--trabajos 1` para comparar.
Los tiempos de la pareja no se extrapolan a la batería completa: ese rendimiento se medirá en CI. No se ejecutó
`--completo` en el equipo. Las siete combinaciones de sistema/Python y la prueba de comportamiento con el plugin
cargado siguen pendientes antes de publicar. No se ha cambiado la versión ni publicado esta fase.

La extracción real quedó incompleta y se detuvo al repetirse el inicio de sesión. Se corrigieron la selección de
herramientas y la parada de la cola, pero las dos lecturas puntuales posteriores no acreditan una extracción completa.
LEEME completo y deriva de punta a punta siguen **no medidos**. La primera lectura no permitió identificar una
refactorización Appian; después se realizó el ensayo acotado de la regla de texto descrito arriba. No sustituye la
comparación de toda la aplicación. La evidencia y el diagnóstico detallado se conservan fuera del repositorio.

Los ajustes finales de inversa solo cambiaron el simulador de prueba y una palabra de un comentario; se repitieron
los módulos afectados, sin volver a ejecutar toda la suite. Evidencias: `gde-lectura/inversa-integrada.log`,
`inversa-integracion-focal.log`, `inversa-omisiones.log` y `mermaid-local.log`. La suite del analista está en
`construccion/analista-integrado-final.log`. La comprobación básica de integración da siete skills, cero errores y
cero avisos. Los resultados no sustituyen la batería de CI ni las pruebas de comportamiento del plugin.

## Aplicación de las lecciones de automejora (19 de octubre de 2026)

Cambios locales sobre `automejora-pruebas`, autorizados tras revisar las recomendaciones A–E. La matriz completa
está en `docs/plan/2026-10-19-aplicar-automejora.md`. Tres worktrees separaron analista/QA, inversa/diagramas e
ingesta/plantillas/prototipos; la rama `codex/aplicar-automejora` integra el resultado. Sin cambio de versión, PR,
publicación ni escrituras en Appian. Los proyectos, capturas y logs quedan fuera del repositorio, en
`$PROYECTOS_PRUEBA/automejora-codex-20261019/`.

### Qué cambia

- Construcción: se protege el anexo manual, se distinguen colisiones desconocidas, constantes y campos adicionales;
  se exige convertir §13 a tabla y se conservan los números de issues y el ancho de IDs. Las reservas avisan de cambios.
- Las issues reciben sus supuestos por PC/objeto y las reglas generales de §13. Los casos expresamente exigidos por
  §14 y confirmados ausentes bloquean; una lectura fallida sigue siendo desconocida. La excepción humana lleva motivo.
  El cierre manual por issue es visible, caduca al cambiar el encargo y no suplanta la verificación ni los fallos de QA.
- Ingesta: palabras por fuente, imágenes enlazadas como parte del Markdown, EML normalizado, duplicadas candidatas
  con exclusión explícita y reversible. `version --inicial` registra las fuentes de 1.0; `iniciar` deja la ruta local
  del plugin para personas y otros agentes. Los escritores modificados conservan LF/CRLF del destino.
- Inversa: herramientas específicas por tipo, nombres completos de aplicaciones, textos localizados y autor de
  versiones; los grupos no cuentan como huérfanos. El inventario se genera por script y conserva aportes humanos por
  UUID. Los documentos antiguos sin marcas requieren revisión mediante `--borrador`, sin sobrescribirlos.
- Las plantillas y F1–F9 recogen las decisiones pequeñas de la revisión. Los dos SVG de `.github/assets/` reflejan el
  flujo vigente. El chat usa el alto disponible y mantiene accesibles la entrada y el botón de envío.

### Comprobaciones específicas

| Prueba | Resultado |
|---|---|
| Analista: selftest del bloque de código, incluidas las 19 regresiones nuevas | 391 comprobaciones, exit 0 |
| Analista integrado: scripts, plantillas, inversa y ambas regresiones nuevas en la misma rama | 392 comprobaciones, exit 0; incluye 19 casos de automejora y 7 de ingesta |
| QA: selftest con excepciones, versiones de issue y CRLF | 57 comprobaciones, exit 0 |
| Inversa: pytest completo | 203 passed, 2 skipped; 1.124 s |
| Inversa: suplementos tras revisión | 29 casos focales; últimos ajustes del inventario 7/7 y del anexo CRLF 2/2. Se solapan con la suite; no se suman como casos distintos |
| Diagramas: selftest completo y conservación LF/CRLF dirigida | Exit 0; PNG, Mermaid, tramos, BPMN y edición correctos |
| Ingesta: Markdown/imágenes, EML, CRLF, palabras, duplicados/reversión, ayuda Windows y capturas DF | 7/7 |
| Prototipos: selftest, humo, contraste y regresión de chat | 45 comprobaciones, exit 0 |
| Chat directo y en tarjeta: 1280×720, 1280×500 y 390×844 | 6/6; sin scroll exterior, input y envío accesibles por `elementFromPoint`; al ocultar la barra recupera el alto completo |
| SVG de funcionamiento y desarrollo, claro y oscuro | 52 y 24 textos; ninguno fuera del lienzo en los cuatro renders; revisión visual correcta |
| Inventario regenerado | Conserva «Para qué», enlaces y pantalla por UUID, incluso si la extracción trae otra descripción; rechaza originales sin marcas y ofrece borradores aparte |
| Diagrama por tramos | El enlace de entrada muestra código y nombre del paso de origen; PNG revisado |

P10 se repitió en una copia externa, sin configurar MCP ni modificar el proyecto original. Las cuatro órdenes
(`issues`, `siguientes`, `estado`, `comprobar`) salieron con código cero antes y después; la diferencia está en el
contenido que reciben los constructores y en los avisos que antes faltaban:

| Medida en las 25 issues | Antes | Después |
|---|---|---|
| Copias de supuestos que deben llegar por PC u objeto (22 filas de origen) | 0/25 | 25/25 |
| Issues que reciben las reglas generales de construcción | 0 | 25 |
| Listas de «En paralelo con» de más de cuatro issues | 24 | 0; remiten al índice |
| Dígitos del siguiente HU, en un proyecto de tres dígitos | 2 | 3 |
| Aviso Gherkin en primera versión | No | Sí |
| Aviso de «Con qué» ausente en §14 | No | Sí |

La revisión sobre una copia de P10 detectó que «Reglas para quien construye» también aparece como párrafo con el
contenido en la misma línea. Se corrigió el lector y se añadió una prueba ficticia: las reglas llegan a las issues sin
arrastrar la tabla siguiente. La revisión visual del chat detectó otro fallo que una prueba de límites no veía:
la barra del prototipo tapaba los controles. Por eso la regresión comprueba qué elemento recibe el clic.

### Límites de esta medida

Son pruebas locales y sobre copias de material ya recogido. No acreditan seguridad por rol, efectos de ejecución ni
una nueva construcción en Appian. El PDF real no se midió por falta de LibreOffice; la suite de contraste conserva
doce textos sobre imágenes sin medir. Pytest omitió un wrapper de shell exclusivo de POSIX y una comprobación Mermaid
por falta de navegador en el entorno de uv; esta última pasó aparte con Python local (seis bloques Mermaid).
La prueba de comportamiento con `claude --plugin-dir` queda pendiente antes
de subir; la batería completa en Linux corresponde al PR. Los puntos aparcados están en `docs/siguiente-version.md`.

## Automejora con proyectos reales (14 y 15 de octubre de 2026)

Sobre la 0.8.0-beta.1, sin cambiar el plugin. Plan: `docs/plan/2026-10-14-automejora.md`. Nueve pruebas con reuniones
reales del cerebro corporativo, una aplicación de desarrollo y otra de un cliente en solo lectura; cada una la hizo un
subagente siguiendo el plugin de la rama leyendo sus ficheros (las sesiones anidadas `claude -p` desatendidas las bloquea
el clasificador de permisos), y la revisó otro de contexto limpio contra el código. Tiempos de reloj de herramienta,
aproximados; sin coste en USD, porque no hubo sesiones anidadas. P10, el 15 de octubre: un análisis real hecho con IA
(DF, técnico y prototipo) la víspera de construirlo, en copias fuera del repositorio y sin escribir en Appian. Lo que
pidió un cambio se sigue en `docs/plan/2026-10-19-aplicar-automejora.md`; arriba constan los resultados al aplicarlo,
y `docs/siguiente-version.md` conserva lo aplazado.

| Prueba | Qué | Min | Llamadas | Resultado |
|---|---|---|---|---|
| P1 · F1 | Proyecto nuevo, 4 reuniones (~46.000 palabras): 24 HU, 9 pantallas, 5 procesos, prototipo y Word | 17 | ~62 | Completo salvo enviar y aprobar (son de personas); `comprobar.py` sin errores |
| P2 · F2 | Una fuente de 2.558 palabras, 6 puntos sin aprobación | 2 | ~14 | Sin errores; dos PC perdidos por `derivadas --escribir` |
| P2 · retoque | Texto de un botón, camino corto | 0,7 | 7 | Sin errores |
| P3 · F1 volumen | 18 transcripciones (~114.000 palabras), funcional y técnico por 4 módulos con 13 subagentes | 54 | ~360 | `comprobar.py` sin errores; 3 pares de HU y 9 de 31 decisiones repetidas entre módulos; 1 de 9 contradicciones perdida |
| P4 · F3 | Campo nuevo con regla, 3 issues | 4,5 | 29 | Pasos 1-6; el 7 sin captura nueva y sin aviso |
| P4 · F4 | Regla con un umbral mal escrito | 1,7 | 19 | Seguido |
| P4 · F5 | Urgencia en una regla, regresión de 99 casos en 22 s | 1,8 | 19 | Seguido; `colision` dijo «no» sin mirar dependientes |
| P5 · F6 y F7 | Aplicación del cliente de 42 objetos, solo lectura | 29 | ~100 (extractor: 321 de lectura, 142 fallidas) | 14 hallazgos y 8 REF; `comprobar_asis` 4 errores falsos; `comprobar_propuesta` 0 |
| P5b · proceso grande | El mayor de 1.464 process models de un entorno de cliente (58 nodos), solo lectura | ~45 | ~900 (extractor) | Un paso por nodo: 107 % del presupuesto; agrupando lo repetido: 80 %; diagrama en 5 tramos sin avisos |
| P6 · F8 y F9 | Base (25 objetos) y una issue en una aplicación nueva de desarrollo; QA con una cuenta | 20 | ~105 | La Base no pasa `verificar` por fallos del script; 1 de 8 issues hecha; 2 guiones de QA pasan |
| P7 | El retoque de P2 por un subagente sin contexto | 0,9 (2 de pared) | 11 | Idéntico a P2 |
| P8 | El retoque con Copilot CLI y Codex, solo con `AGENTS.md` | 0,6 | ~25 | Copilot: sin scripts, versión incoherente (`comprobar.py` ✗); Codex: no concluyente, su sandbox no arranca dentro de otra sesión |
| P9 | Una persona sin IA: estado, retoque y guion de reunión | ~2 (10-15 para una persona) | 14 órdenes | Viable; se atasca en la ruta del plugin y en localizar menciones |
| P10 · lo recibido | Análisis real hecho con IA (45 HU, 27 pantallas, 53 PC): estado, comprobar, Word, prototipo y guion | ~10 | ~25 | `comprobar.py` sin errores; Word y prototipo idénticos al regenerarlos (el prototipo, con la ruta del kit a mano) |
| P10 · F1 paso 13 a F8 | De la versión del DF a la primera issue, por un subagente limpio | 5 | 34 | Cero issues con §13 en lista; 25 tras reescribirlo como tabla (141 filas); los supuestos para construir no llegan |
| P10 · F2 en construcción | Respuesta del cliente a 3 PC con EV-01 aprobada y una issue reservada | 12 | 64 | Versión nueva sin errores, EV-01 reaprobada y EV-02 con `--comparte`; lo de EV-02 entra en las issues de EV-01 |

### Lo aprendido

- Los scripts de consulta (`indice.py ficha`, `impacto`, `seccion`, `estado`, `pendientes`) y `comprobar.py` sostienen
  los flujos de mantenimiento: F3 entero sin leer el funcional y `comprobar.py` como único freno ante lo improvisado
  (P4, P8). No conviene tocarlos.
- El coste está en la redacción de la IA (funcional, técnico, documentos del as-is, notas), no en los scripts: en P3 los
  scripts suman segundos de 54 minutos.
- El contexto heredado abarata el retoque (7 frente a 11 llamadas) sin cambiar el resultado.
- Con volumen, el riesgo no es leer de más sino duplicar: cada módulo redacta lo que comparte con otro.
- `verificar` es el punto débil de la construcción: tres tipos de diferencia falsa en una misma Base la bloquearon, y con
  ella las ocho issues.
- Con una aplicación de 42 objetos, los presupuestos de palabras de la ingeniería inversa sobran (20-54 %), salvo LEEME
  (96 %). `listObjectVersions` da el historial en el Dev MCP real.
- El índice del cerebro corporativo da por transcritas 1.692 reuniones y en disco hay 1.095: las pruebas eligen por los
  ficheros, no por el índice.
- Un SAIL CLI con un solo usuario no prueba la seguridad por rol; y un defecto (columnas en blanco por `fields` vacío) lo
  vio SAIL CLI y no `testInterface`.
- Un análisis hecho con IA que llega al plugin se mantiene sin pérdidas: el Word y el prototipo salen iguales, el guion de
  preguntas y el impacto de una respuesta funcionan. Lo que falla es el paso a construir: §13 en lista da cero issues sin
  avisar, y los supuestos con que se construye mientras el cliente no responde no llegan a quien construye (P10).
- Con dos unidades en curso sobre la misma pieza, los frenos de las unidades funcionan («ha crecido», `--comparte`), pero
  las issues mezclan lo de las dos (P10).

## 0.8.0-beta.1 · Método L.U.C.I.A. (14 de octubre de 2026)

Parte de la 0.7.0-beta.4 (`d6126a8`). Plan: `docs/plan/2026-10-14-metodo-lucia.md`; lo que decidió Raúl con estas
medidas, en su §6 («Estado al terminar»). Las pruebas con reuniones reales y con el entorno de desarrollo se hacen fuera
del repositorio; aquí, solo las cifras y las lecciones.

### Fase 1 · T1: el caso de «Agilidad» con la 0.7.0-beta.4

Una sesión nueva, con el plugin cargado desde una carpeta (`claude --plugin-dir`), incorpora una reunión de 2.467
palabras a un análisis con prototipo y DF enviado, retoca el prototipo y saca el DF nuevo. El análisis de partida lo
montó otra sesión con tres reuniones del mismo proyecto (56 minutos, 142 llamadas). **18,6 minutos activos frente a los
70 de la 0.6.0-beta.1**: 124 llamadas (100 de la IA y 24 de script), un turno sin aprobaciones y 6,73 USD. No es el
mismo caso (otro proyecto, sin persona delante, una sola ejecución): la referencia para T3 son estos 18,6 minutos.

| Paso | Min | Llamadas | Qué leyó | Quién lo hizo → quién debería |
|---|---|---|---|---|
| Método | 1,5 | 9 | 5 referencias enteras, 778 líneas | IA lee el fichero → por partes |
| Fuente | 0,2 | 6 | entera, 49 líneas | script e IA |
| Encajar | 3,9 | 18 | 216 de 1.995 líneas; 13 consultas de `indice.py` | script e IA |
| Nota | 0,5 | 1 | — | IA |
| Informe de impacto | 1,0 | 5 | — | IA, dos veces → una |
| Versión, aplicar, diagrama, comprobar | 4,3 | 23 | 17 líneas | IA y script |
| Prototipo: leer | 1,1 | 6 | el script del proyecto entero, 665 líneas | IA → por partes |
| Prototipo: editar | 3,1 | 25 | — | IA |
| Generar, capturar, revisar | 1,1 | 10 | 6 capturas | script e IA |
| Enlazar capturas | 0,2 | 3 | — | IA → script |
| Word y PDF | 0,7 | 2 | — | script; el PDF, IA → script |
| Revisar páginas | 0,5 | 10 | 6 páginas | IA |
| Cierre | 0,3 | 6 | — | IA y script |

Los cuatro puntos de «Agilidad» que apuntaba entonces `docs/siguiente-version.md`, con la versión actual:
1. Guía de diseño y código en un retoque de prototipo: ya no pasa (0 líneas de `design-rules.md` y del kit). Queda que
   lee entero el script del proyecto y rehace 11 capturas para 3 pantallas afectadas: el método no dice cómo localizar
   una pantalla ni qué se lee en un retoque.
2. Funcional y técnico enteros: ya no pasa (233 de 1.995 líneas). Lo que se lee entero son las referencias del método,
   porque la tabla de referencias las manda sin distinguir una actualización.
3. Nota de la fuente: 747 palabras, 0,30 veces el original. El método sigue sin decir que es proporcional: 5 de sus 13
   apartados salieron casi vacíos.
4. El DF espera al prototipo: sigue pasando, 5,8 minutos (31 %). Lo manda `actualizacion.md` §7.

Fallos que salieron: el script del prototipo que escribe el agente lleva la ruta absoluta del plugin (no vale en un
proyecto compartido); `validate.py --anterior` exige `--confirmadas`; `df_docx.js --pdf` solo convierte con LibreOffice
y, sin él, la sesión sacó el PDF por su cuenta; y el hook de arranque prueba `python3` antes y deja un error en Windows.

`--plugin-dir`: la copia de la carpeta sustituye a la instalada o sincronizada con el mismo nombre (aparece como
`<nombre>@inline`; está documentado). La app de escritorio no tiene un equivalente documentado: para probar un cambio
sin instalarlo, la CLI.

### Fase 1 · T2 y T3: lo que se corrigió y lo que mide

T2 (sobre la 0.7.0-beta.4): el Word no espera al prototipo y se repite con las capturas; en un retoque de prototipo se
lee solo el tramo de cada pantalla del script del proyecto y el apartado de la guía que cambie; la tabla de referencias
del analista dice qué se lee por partes al incorporar una fuente; el informe de impacto se escribe una vez si nada
requiere aprobación; la nota es proporcional y sin apartados vacíos; `capture.py` enlaza cada captura en su ficha; sin
LibreOffice no se saca el PDF por otra vía y se dice a quien envía que el Word va sin revisar; el script del prototipo
ya no lleva la ruta del plugin; `validate.py --anterior` vale sin `--confirmadas`; el hook no deja el error de `python3`
en Windows. Los ficheros de instrucciones no crecen (analista `SKILL.md` 216 → 218 líneas; prototipos, 180 → 180).

T3 repite el caso de T1 con una copia del plugin que lleva solo T2; T3b, con T2 tras su revisión y dos ajustes que
salieron de T3. Mismo punto de partida, encargo, modelo y memoria; una ejecución de cada una.

| | T1 | T3 | T3b |
|---|---|---|---|
| Minutos activos | 18,6 | 16,0 | 19,4 |
| Llamadas | 124 | 155 | 135 |
| Líneas del método | 838 | 331 | 287 |
| Líneas del análisis | 427 | 1.105 | 413 |
| Líneas de código del plugin | 0 | 215 | 0 |
| Líneas del script del prototipo | 665 | 494 | 524 |
| Coste (USD) | 6,73 | 6,64 | 5,61 |

- **El criterio «T3 baja en minutos y llamadas frente a T1» no queda demostrado**: el total se mueve entre 16 y 19
  minutos y entre 124 y 155 llamadas de una ejecución a otra, y eso es más que lo que T2 quita. Lo que queda del caso es
  tiempo del modelo pensando y editando.
- Se repite en las dos y es de T2: el método se lee en un tercio; el informe, de 5 llamadas a 2; el enlace de capturas,
  de 3 a 1; el script del prototipo ya no se lee entero.
- **El Word no se adelantó en ninguna de las tres**: con todo pedido en un turno, nadie lee uno intermedio y la sesión
  se lo salta. Sin efecto medido; pendiente de que Raúl decida si se queda.
- Lo que T3 enseñó y se corrigió antes de T3b: al escribirse el informe «una vez, ya aplicado», la sesión lo dejó (con
  `comprobar.py`) para después del prototipo, que se retocó sobre un análisis sin comprobar. `actualizacion.md` §7 fija
  el orden en un solo sitio y en T3b se cumple (informe en el minuto 8,4, comprobación en el 9,1, prototipo después). Y
  sin la plantilla del funcional, la sesión buscó en el código de `comprobar.py` cómo se tacha una pregunta: la tabla de
  referencias cita ahora ese tramo.
- Calidad: las tres pasan `comprobar.py` y `validate.py` sin errores. Contrastadas con la reunión, las tres recogen sus
  15 puntos en la nota, en el informe y aplicados; T3b toca menos piezas (16 frente a 22 y 21) porque no repite un
  supuesto que ya estaba en una pregunta abierta. Un punto depende de una palabra mal transcrita y cada sesión lo trató
  distinto.
- Revisión independiente de T2: dos correcciones de texto antes de unir (el Word que sale antes podía entregarse con las
  capturas viejas y ya no se dejaba repetir; sin LibreOffice nadie sabía que iba sin revisar) y cuatro restos de lo
  anterior. El código nuevo, sin fallos.
- T4: `CLAUDE.md` lleva las preguntas del color y de la IA, dónde van las lecciones de cada prueba y cómo se prueba un
  cambio de una skill con `claude --plugin-dir`.

Pruebas, con T2 unida: `comprobar_plugin.py`, 0 errores; selftest del analista y de prototipos, correctos;
`coste-retoque/prueba_puntuar.py`, bien (el camino corto sigue en 16 llamadas). El retoque de análisis a ciegas (tope de
25 llamadas) se repite al final, con el plugin completo.

### Fase 2 · T5: el Dev MCP y SAIL CLI reales

Mirados el 14 de octubre de 2026 en el entorno de desarrollo, en solo lectura: Dev MCP 26.6.110 (build 20261008, el
último publicado) y SAIL CLI 26.6.110. Lo que cambia el plan lo confirmó un segundo agente por separado.

| Pregunta | Lo que hay |
|---|---|
| Casos de prueba | Se crean y se ejecutan en reglas e interfaces. La ejecución da, por caso, si pasa, la salida obtenida y el error con regla, función y línea; la salida esperada no viene (está en la definición del caso). Solo las reglas llevan aserción: una interfaz solo comprueba que no da error |
| En bloque | No. Se ejecutan los casos de un objeto por llamada. Una aplicación de 106 reglas y 32 interfaces (609 casos): 138 llamadas, 73 s y 1,5 MB de respuestas (unos 380.000 tokens si pasan por el contexto). Una regla de 6 casos, 1 KB; una interfaz de 7, 270 KB |
| Dependientes | Sí, solo los directos, con tipo y nombre; incluye siempre la propia aplicación |
| `LCP_TOOL_MODE=readonly` | **No hace nada en este bundle.** La documentación de Appian (26.6 y la vigente) la describe, pero la variable no está en su código: el servidor ofrece las mismas 200 herramientas con ella y sin ella, y 121 no son de lectura |
| Reconocer por la firma | `devmcp_extract.py` clasifica cada herramienta por su verbo, sus anotaciones y sus parámetros. Su `devmcp_policy.json` cuenta `run` como escritura: tal cual, deja fuera las de ejecutar casos, que el servidor anota como de solo lectura |
| SAIL CLI | La cuenta local entra con `SAIL_USERNAME` y `SAIL_PASSWORD`, sin teclado; cada sesión, en su `--data-dir`. `load --json` da cada componente con su `ref`: en dos cargas de la misma página coinciden 32 de 35 (cambian las que el propio JSON marca como propias de cada carga). Una `ref` que lleva un dato dentro («Pendientes (22)») no sirve para un guion. Los errores salen como texto aunque se pida JSON |

Lo que el plan daba por hecho y no es así:
- **T12.** `LCP_TOOL_MODE` no protege. Lo único que aplica el servidor son los permisos del usuario con el que se
  conecta, y solo sobre lo que ya existe: un diseñador puede crear objetos nuevos aunque solo vea la aplicación. Las
  anotaciones de las herramientas y las reglas de cada cliente (`permissions.deny` en Claude Code y sus equivalentes)
  son barreras contra el descuido. `SKILL.md`, `devmcp-setup.md` y `devmcp_extract.py` de ingeniería inversa recomiendan
  hoy la variable; la extracción es de solo lectura por su propia política, no por ella.
- **T13.** La regresión de toda la aplicación no se puede lanzar en bloque por el Dev MCP; lo nativo de Appian que lo
  hace es solo para reglas. Los casos de una issue los tiene que ejecutar un script, para que las respuestas no pasen
  por el contexto.

### Fase 2 · T6: línea base del retoque construido

El caso ficticio de `pruebas/evaluaciones/coste-retoque` («Nueva solicitud» pasa a «Pedir material»), construido de
verdad: la aplicación «Solicitudes de material» en una aplicación nueva del entorno de desarrollo (11 objetos del
técnico, tres cuentas locales por rol; 36 minutos y 105 llamadas al Dev MCP montarla). Tres sesiones a ciegas con una
copia fija de la 0.7.0-beta.4, el retoque ya aplicado en el análisis y la unidad aprobada, y un solo encargo: «La unidad
EV-03 está aprobada. Constrúyela en desarrollo y déjala como construida.» Las cifras salen de la transcripción de cada
sesión y coinciden con su evento de resultado.

| | Pasada 1 | Pasada 2 | Pasada 3 | Media |
|---|---|---|---|---|
| Minutos | 2,4 | 2,9 | 3,3 | **2,9** |
| Llamadas | 50 | 58 | 55 | **54** |
| Dev MCP: lectura / escritura / prueba | 9 / 1 / 1 | 9 / 1 / 1 | 13 / 1 / 1 | — |
| Tokens de salida | 11.662 | 14.130 | 16.450 | 14.081 |
| Contexto máximo | 233.110 | 209.472 | 209.062 | 217.215 |
| Coste (USD) | 2,63 | 2,27 | 2,63 | **2,51** |

Las tres dejan la acción renombrada, nada más tocado y la unidad Construida, sin preguntar. El cambio en sí (leer el
objeto y escribirlo) son 0,6 minutos y 0,31 USD; lo demás es carga fija:

| Paso | Min | Llamadas | USD | Quién lo hizo → quién debería |
|---|---|---|---|---|
| Arranque y estado | 0,3 | 5 | 0,11 | IA y script → script |
| Encargo | 0,1 | 3,3 | 0,06 | script lanzado por la IA → fichero ya generado |
| Skills y referencias | 0,5 | 14,7 | 1,01 | IA leyendo ficheros enteros → por partes |
| Leer el análisis | 0,0 | 4,7 | 0,14 | IA → fichero (el extracto, en el encargo) |
| Leer el objeto | 0,2 | 7 | 0,24 | IA |
| Escribirlo | 0,4 | 4,7 | 0,07 | IA, o una persona (B4) |
| Casos de prueba | 0,4 | 5,3 | 0,19 | IA → script; en un retoque, nada |
| `verificar` | 0,3 | 2,3 | 0,25 | script compuesto por la IA → script |
| Marcar construida | 0,1 | 1 | 0,02 | script |
| Contexto de arranque | — | — | 0,35 | fichero |

- La «hora por un cambio menor» de appian-harness no ha vuelto: son 3 minutos. La skill oficial es el 25 % del coste
  (0,63 USD; carga 2.480 líneas de media, no las 5.600 que se temían) y sube el contexto por encima de 200.000 tokens
  antes de tocar el entorno; las respuestas del Dev MCP, el 16 %.
- **B4 lo decide Raúl con estas cifras.** Lo mismo a mano en Designer no se ha medido.
- Dato aparte: con el texto del botón en la interfaz (un enlace de inicio de proceso, que es peor diseño y se rehízo
  como acción de registro), dos pasadas costaron 3,6 y 3,9 minutos y 2,72 y 2,40 USD.

Lo que falla hoy y tienen que quitar las issues de la Fase 5 (T17 lo vuelve a medir):
- El encargo no dice qué cambia («ver técnico §7»), así que la sesión lee el técnico; y no existe hasta que la sesión lo
  genera.
- La orden de `verificar` del encargo no se puede copiar: lleva `python3` y marcadores, y le falta el servidor (una
  pasada falló por eso). `verificar` vuelca de 78 a 331 KB de registro.
- **`verificar` no mira las acciones de registro:** sale igual con el cambio que sin él, y da por sobrantes los campos
  del record type. Ninguna sesión lo dice; las tres lo suplen releyendo la acción y mirando el botón con SAIL CLI.
- Las sesiones ejecutan casos de prueba y SAIL CLI sin que nadie lo pida, en un retoque que no cambia criterios ni
  reglas.
- Con el texto en un record type, el análisis pide una DT «Cambio sobre lo construido» y decidir el orden con la otra
  unidad, para un cambio de nombre; `comprobar.py` da un aviso que no procede.
- El técnico ficticio dice que el botón «abre el formulario de inicio» sin decir cómo: quien construyó eligió un enlace
  de proceso en vez de la acción de registro que pide buenas prácticas (00, 01 §9.2, 02 §5.4, 03 §8, 06 §5.3).
- Los casos de prueba de una interfaz con una rejilla de registros fallan siempre: el ejecutor no la evalúa.

### Fase 3 · T7 y T8: flujos y un repositorio git por proyecto

Qué cambia:
- **Flujos F1 a F9** (`skills/appian-functional-analyst/assets/flujos/`): un fichero de 12 a 22 líneas por flujo, con
  cuándo se usa, los pasos, quién hace cada uno y con qué skill; citan la referencia de cada paso sin repetirla.
- **`proyecto.py iniciar`** deja el proyecto como repositorio git (rama `main`, sin primer commit ni repositorio dentro
  de otro), con `.gitignore`, `.gitattributes`, `AGENTS.md` (28 líneas, generado entero), `CLAUDE.md` con «@AGENTS.md» y
  `.agents/workflows/`. Si se vuelve a lanzar, pone al día `AGENTS.md` y los flujos y no toca lo demás; no pisa un
  `AGENTS.md` ajeno ni lo que generó una versión posterior del plugin.
- **`proyecto.py estado`** avisa de lo no confirmado, lo no subido, lo que falta traer, de `AGENTS.md` o flujos de otra
  versión y de un `CLAUDE.md` que no importa `AGENTS.md`. Nunca bloquea.
- **Los scripts escriben siempre con `\n`** (50 escrituras en cuatro skills y `requisitos.py`), y `comprobar_plugin.py`
  comprueba que no vuelva a colarse: con proyectos compartidos entre Windows, macOS y Linux, cada reescritura en otro
  sistema cambiaba el fichero entero.

Revisión independiente, con proyectos creados fuera del repositorio: los tres criterios de la fase se cumplen y los
siete bordes probados (carpeta que ya es repositorio, dentro de otro, sin git, sin remoto, remoto que no contesta, ruta
con espacios y tildes, `iniciar` dos veces) no fallan. Encontró y quedó corregido:
- Con el `core.autocrlf` de Git para Windows, un clon cambiaba los finales de línea y las fuentes ya catalogadas se
  volvían a catalogar: de ahí el `.gitattributes`.
- «Se sube todo menos los secretos» no era cierto con ingeniería inversa: un valor encontrado queda en claro en varios
  documentos de `as-is/`. La regla y F6 dicen que, con hallazgos de seguridad con valores, el equipo decide antes de
  subir.
- Tres pasos de F4, F5 y F6 no decían lo que su referencia, y dos avisos de `estado` eran falsos (rama subida sin
  seguimiento; plugin anterior con un flujo retirado).
- `AGENTS.md` pasó de 50 líneas a 28: se carga en cada sesión del proyecto.

Coste de `estado`, que se ejecuta al empezar cada tarea: de 0,15 a 0,27 s sin repositorio, 0,52 s sin remoto y 1,41 s
con un remoto en GitHub (antes, 0,22 s); 5,5 s si el remoto no contesta. El intento de traer lo nuevo se queda: sin él,
«va por detrás» sería un dato viejo.

Pruebas, sobre la rama ya unida: `comprobar_plugin.py`, 0 errores; selftest del analista (290 comprobaciones), de
diagramas y de prototipos, correctos; ingeniería inversa, 173 pasan y 2 se saltan. Sin ejecutar en macOS ni Linux: lo
pasa GitHub en la PR.

### Fase 4 · T9: criterios en Gherkin de una línea

Qué cambia: `funcional-plantilla.md` §4 es el único sitio que dice cómo se escribe un criterio (dado, cuando y entonces,
con su ID; `redaccion.md` y `actualizacion.md` remiten a él); `comprobar.py --anterior` avisa del criterio nuevo o
cambiado en su texto que no tiene las tres partes; y `modelo.py` convierte los criterios de una historia en Gherkin
formal en español (`pasos_gherkin`, `Proyecto.feature`, `Proyecto.escenarios`), que T11 escribirá en cada issue. Sin
órdenes ni ficheros nuevos; los datos de prueba no se han reescrito.

Revisión independiente, con un proyecto ficticio fuera del repositorio:
- El criterio de la fase se cumple: un analizador oficial de Gherkin (`gherkin-official` 42) acepta todos los `.feature`
  que salen, también con finales de línea de Windows y caracteres no ASCII.
- El aviso no hace ruido: calla con los criterios viejos y cuando solo cambia la cita; un retoque que no toca criterios
  ve una línea «✓» más y `comprobar.py` tarda lo mismo (0,339 → 0,347 s de mediana en 20 pasadas).
- Encontró un fallo que las pruebas no veían: un criterio escrito en dos líneas perdía la segunda al pasar a Gherkin,
  sin avisar (el Word sí las unía). Corregido, con su caso.
- «Sin botones ni campos», la frase del diseño, se entendía mal en una validación («sin comentario»): la plantilla dice
  «sin pasos de pantalla (pulsar, rellenar); los datos, con el nombre que les da el cliente».

Pruebas: `comprobar_plugin.py`, 0 errores; `selftest.py` del analista, 261 comprobaciones (19 nuevas), también con
Python 3.9. En el Word, cada criterio pasa de unas 10 palabras a 19.

El aviso de «texto que queda viejo» señalaba criterios que empiezan igual: resuelto en la Fase 7 (ajustes finales).

### Fase 5 · T10 a T14: issues por requisito y pruebas de la issue

Qué cambia:
- **T10.** Técnico §13 gana la columna «Para» (el requisito de cada objeto, o «Base»); `comprobar.py` avisa del objeto
  sin ella, una sola vez en un técnico antiguo. La plantilla dice además, en un solo sitio cada cosa: cada acción que
  lanza un proceso es una acción de registro (de lista o relacionada) de un record type, nunca un enlace de proceso; la
  URL de cada entorno en §0; y cómo se comprueba cada criterio en §14.
- **T11.** `indice.py issues` sustituye al encargo, que desaparece. Las issues se generan al aprobar la unidad, una por
  requisito (juntas las que comparten pantalla o proceso, lo común en la Base), con el extracto del técnico y del
  prototipo, sus escenarios y su `.feature`. `--siguiente` da la próxima, la reserva con una línea en el índice de la
  unidad (commit y push) e imprime la orden de terminar con las rutas y el servidor del equipo. `construida` pide todas
  las issues hechas.
- **T12** (decisión de Raúl): `LCP_TOOL_MODE` no hace nada en el Dev MCP 26.6.110 y se dejó de afirmar lo contrario en
  ingeniería inversa. Fuera de desarrollo, el Dev MCP entra con una cuenta diseñadora (rechaza con 403 a una que no
  lo es) y solo para leer: el 14 de octubre de 2026 Raúl decidió que basta una cuenta diseñadora y que la garantía es el método (solo se construye en
  desarrollo). SAIL CLI, solo en desarrollo.
- **T13.** `verificar` ejecuta los casos de prueba de las reglas e interfaces de la issue y de lo que las usa,
  reconociendo las herramientas por su firma, y deja el detalle en su fichero. Bloquea un fallo propio, salvo que una
  persona lo marque con `--sin-prueba` y motivo (se niega en una sesión desatendida y caduca si cambian la issue o el
  fallo); un fallo en lo que la usa es un aviso; la rejilla que el ejecutor no evalúa es «no evaluable». Comprueba
  nombre y tipo de las acciones de registro. La regresión de toda la aplicación la pasa un script antes del paquete.
- **T14.** Al aprobar una unidad que cambia datos, seguridad, integraciones o procesos en curso, o que usa IA, y en su
  issue: «que una persona revise DT-nn antes de construir». Aviso, no puerta.
- Un retoque solo se libra de la DT si renombra una acción, vista o filtro de un record type y su fila del técnico no
  cambia nada más; si cambia quién la ve, pide «Permisos».

Prueba real, en solo lectura, contra la aplicación ficticia del entorno de desarrollo:

| Orden | Tiempo | Por pantalla | Casos |
|---|---|---|---|
| `verificar` de la unidad del retoque (regla con dependientes, panel y acción) | 11 s | 425 bytes | 40: 39 pasan, 1 no evaluable |
| `regresion` de la aplicación | 12 s | 250 bytes | 75: 74 pasan, 1 no evaluable |

El registro del Dev MCP, que en T6 llegaba a 331 KB, ya no sale. Una acción renombrada a mano sale como diferencia. En
el retoque de T6, la issue ocupa 2,2 KB (el técnico, 16 KB) y dice que no hay pruebas que ejecutar.

Tres revisiones independientes (una de cada mitad y otra de la fase entera) encontraron, y quedó corregido:
- Parte del técnico no llegaba a ninguna issue mientras la issue decía que no hacía falta leerlo: primero 21 de 67
  líneas del proyecto de prueba, y después la matriz de seguridad, que no nombra objetos. Lo que no cae en ninguna issue
  va a la Base y el analista recibe el aviso.
- La reserva deshacía una fusión de git a medias, subía commits ajenos si el proyecto estaba dentro de otro repositorio
  y daba a una sesión reiniciada, o a dos sesiones del mismo usuario, una issue que no era suya.
- La regla de «retoque en una parte» dejaba pasar cambios de datos y de permisos, y saltaba la decisión de orden entre
  dos unidades sobre el mismo record type.
- `construida --manual --desatendida` se saltaba el bloqueo de las pruebas; y unos casos que no se pudieron ejecutar
  bloqueaban sin salida (ahora esperan a la regresión, con aviso).

Comprobado: mismas issues byte a byte con los mismos datos, en carpetas distintas; cada issue conserva su número al
cambiar el análisis; en 15 rondas con dos o tres agentes a la vez, ninguno se llevó la misma issue.

Lo que no se cumple tal cual: «fuera de desarrollo, el Dev MCP no ofrece herramientas que escriban» (decisión de Raúl:
sin maquinaria y con una cuenta diseñadora; lo garantiza el método). «Una regla que rompe otra que la usa se detecta» está
probado con el simulador: en solo lectura no se puede provocar; lo prueba T16 con un defecto sembrado.

### Fase 6 · T15: la skill appian-qa

`skills/appian-qa/`: QA de una unidad completa, en otra sesión, solo con sus `.feature`. Por escenario, el «dado» como
un usuario, el «cuando» con la cuenta de su rol y su `--data-dir`, y el «entonces» en el `--json` de SAIL CLI. Cada
recorrido queda como guion en `qa/<U>/` y `qa.py` los repite sin IA antes del paquete; un fallo devuelve su issue a
pendiente y se puede marcar como no necesario con `--sin-prueba` y motivo, como un caso de prueba. La sesión de cada rol
se busca en el equipo de quien repite, sin fichero por proyecto y sin que el script vea contraseñas. No repite contra
pruebas ni producción. En un retoque cosmético, nada.

Prueba real con la aplicación ficticia y tres cuentas locales por rol: tres escenarios recorridos y escritos como guion
en 1, 1 y 0,5 minutos; repetirlos sin IA, 15 segundos la unidad entera, dos veces con el mismo resultado; un fallo
provocado falla donde debe. Para que el guion sea estable hizo falta no fijar los números que da Appian (se comparan por
el principio), marcar las filas por su contenido y tener en cuenta que una rejilla vacía no trae filas y que lo buscado
se queda en la caja de búsqueda.

La revisión independiente encontró, y quedó corregido: la unidad podía quedar Construida sin QA (ahora la última issue
lo dice y `construida` avisa); un guion podía dar «pasa» sin afirmar nada; nada impedía repetirlo contra producción; y
un código de salida tapaba un fallo. Las sesiones de cuentas locales se cierran al terminar la campaña de QA y la
importada del Dev MCP no se cierra: cerrarla podría dejar sin acceso al Dev MCP.

Pruebas, con la Fase 5 y T15 unidas: `comprobar_plugin.py`, 7 skills y 0 errores; selftest del analista (382), de
`appian-qa` (48), de prototipos y de diagramas, correctos; los siete `prueba_puntuar.py`; ingeniería inversa, 193 pasan
y 2 se saltan.

### Fase 6 · T16: el ensayo de QA con defectos sembrados

En la aplicación ficticia del entorno de desarrollo, una unidad nueva de cinco historias (una transición de estado hecha
por otro perfil, una regla que usa otra, lo que ve cada rol y un color que solo se ve en pantalla) se construyó con el
plugin terminado (20,8 minutos y 9,52 USD) y se le sembraron cuatro defectos: la regla que usa otra da otro resultado
(D1), la transición deja otro estado (D2), un rol ve una acción que no le toca (D3) y un estado sale en verde en vez de
en rojo (D4). Ninguna forma de QA vio los defectos sembrados; todas tenían solo los `.feature` de la unidad.

| Forma | Encontrados | Se le escapó | Min | Llamadas | Contexto máximo | USD | Repetir sus guiones (dos veces) |
|---|---|---|---|---|---|---|---|
| A, quien construye, en su misma sesión (Opus) | 4 | — | 4,6 | 24 | 396.120 | 4,09 | 82 y 84 s, iguales |
| B, otra sesión con el mismo modelo (Opus) | 3 | D4 | 46,0 | 51 | 142.001 | 2,68 | 71 y 73 s, iguales |
| C, otra sesión con otro modelo (Sonnet 5.5) | 3 | D4 | 4,5 | 26 | 82.675 | 0,93 | 76 y 77 s, iguales |
| D, Playwright CLI en vez de SAIL CLI (Opus) | 4 | — | 31,6 | 55 | 169.605 | 3,61 | 538 y 535 s, iguales |

- Ningún falso positivo. Cada fallo devolvió a pendiente la issue que tocaba.
- **A lo encontró todo, pero no probando**: comparó el historial de versiones de los objetos con lo que había escrito y
  vio cambios ajenos, algo que solo sirve con defectos introducidos después (un malentendido suyo no deja rastro). Lo
  primero que intentó fue corregir, y arrastra 4,4 veces el contexto de C.
- **Sonnet encuentra lo mismo que Opus por un tercio** (0,93 frente a 2,68 USD) y con menos de la mitad de contexto. Los
  46 minutos de B son, 36 de ellos, espera a un SAIL CLI que no respondía.
- **SAIL CLI no ve el color** (D4); Playwright sí, y además un problema de accesibilidad real (el nombre accesible de
  los botones es la descripción interna de la acción). A cambio, cuesta más, repetir sus guiones lleva 9 minutos frente
  a 75 segundos, y `qa.py` no sabe repetirlos.
- `verificar` habría cazado D1 y D2, no D3 (no mira quién ve una acción ni el iniciador de un proceso) ni D4.
- Al terminar, la aplicación se devolvió a su estado sin defectos y se comprobó con `verificar` y con los guiones.

Recomendación, para que la decida Raúl: el QA de la unidad, con Sonnet 5.5 en otra sesión o en un subagente que solo
reciba los `.feature`; Playwright no por defecto, solo para criterios que solo se ven en pantalla, y lo demás visual lo
mira una persona con la captura.

Fallos que salieron y se corrigen: el QA no tenía de dónde sacar el site ni la cuenta de cada rol (Opus lo sacó del Dev
MCP, que la skill prohíbe); `qa.py` esperaba 120 s por paso a un SAIL CLI que no responde (una repetición tardó 22
minutos); una sesión se quedaba colgada si dejaba una vigilancia abierta; `issues.py` comparaba un nodo con el del mismo
nombre de otro proceso; una unidad Construida cuyo QA falla después seguía figurando como Construida; y el flujo llevaba
a quien construye a hacer el QA en el mismo turno.

### Fase 7 · T17, T18 y las medidas con el plugin terminado

**T18.** `cambios.md` §6 y `urgentes.md`: quien prepara el paquete revisa en Compare and Deploy la comparación de sus
objetos, como en un Merge Request, con los fallos de la regresión, los de los guiones de QA y las pruebas marcadas como
no necesarias (la línea nombra los tres ficheros); se promueve el mismo paquete con un ICF por entorno y, si el
despliegue es directo o por API, con «Require review» activado en el destino; `produccion --ref` lleva la referencia del
pase. Sin script nuevo. De paso, `urgentes.md` pide ya «Dónde se corrige» también en una urgencia de datos u operación,
como exigía `proyecto.py`.

**T17, primera medida** (copia fija del commit `85d801e`; el retoque de T6 con el proyecto puesto al día: repositorio
git, «Para» en §13, la acción en la tabla de §7 y la unidad aprobada de nuevo para que salgan sus issues):

| | T6 | T17 (media de 3) |
|---|---|---|
| Minutos | 2,9 | 4,7 |
| Llamadas | 54 | 38 |
| Contexto máximo | 217.215 | 140.785 |
| Coste (USD) | 2,51 | 1,92 |

Leen la issue y el flujo, y del técnico solo el entorno (antes, entero); no ejecutan casos de prueba ni SAIL CLI;
`verificar` comprueba el nombre de la acción (sin renombrarla, `construida` se niega). Una cuarta pasada no vale: leyó
un fichero de la prueba que decía dónde estaba el texto. **El criterio se cumple en llamadas y coste, no en minutos**:
las tres sesiones buscaron el plugin en el disco, porque `AGENTS.md`, el flujo y la issue nombraban los scripts sin ruta
(son del proyecto y se comparten entre equipos), y una se quedó colgada tres minutos en una búsqueda por todo el disco.

**T17 repetida** con los ajustes finales (copia del commit `11e34a9`; tres pasadas válidas, cada una en una carpeta
aislada): ninguna busca ya el plugin en el disco.

| | T6 | T17, primera | T17, repetida |
|---|---|---|---|
| Minutos | 2,9 | 4,7 | 4,3 (4,0 · 4,5 · 4,4) |
| Llamadas | 54 | 38 | 38 |
| Contexto máximo | 217.215 | 140.785 | 159.059 |
| Coste (USD) | 2,51 | 1,92 | 1,97 |

**El criterio «no cuesta más que en T6» se cumple en llamadas (−30 %) y en dinero (−22 %), no en minutos (+1,4).** El
tiempo de más es de las herramientas (de 0,5 a 1,3 minutos: pedir la issue, que reserva con commit y push, y
`verificar`) y de seis peticiones más al modelo. Del técnico solo se leen trozos, no se lanzan pruebas ni SAIL CLI y la
calidad es la misma: la acción renombrada, nada más tocado y la unidad Construida. Si esos minutos importan, Raúl decide
(por ejemplo, reservar sin push cuando trabaja una sola persona).

**T17, tercera medida**, tras quitarle a `verificar` lo que no necesita cuando no hay pruebas (de 36 llamadas al Dev MCP
a 3) y decir que una orden completa de `--siguiente` se lanza sin cargar ninguna skill (copia del commit `70f5973`): 4,1
minutos (4,2 · 4,1 · 3,9), 38 llamadas y 2,07 USD, frente a 2,9, 54 y 2,51 de T6. Cargan tres skills (antes, tres o
cuatro). `verificar` tarda en la sesión de 21 a 27 segundos y fuera de ella de 16 a 18 en este equipo (de 8 a 10 en T6),
casi todo en arrancar el Dev MCP, que el plugin no controla. **Queda en +1,2 minutos por retoque (+41 %), con un 30 %
menos de llamadas y un 18 % menos de coste**: el tiempo de más es de las herramientas (1,3 minutos frente a 0,5) y de
nueve peticiones más al modelo por el recorrido de la issue.

**T17, comparación en las mismas condiciones**: seis pasadas a ciegas del mismo retoque, alternando la versión antigua
(0.7.0-beta.4) y la nueva (commit `70f5973`), a la misma hora y con `verificar` medido también fuera de las sesiones.

| | Minutos | Llamadas | Coste (USD) | `verificar` en la sesión |
|---|---|---|---|---|
| Antigua (media de 3) | 3,2 | 38 | 1,87 | 9,7 s |
| Nueva (media de 3) | 2,1 | 21 | 1,14 | 8,6 s |

**El criterio de T17 se cumple: la versión nueva tarda un 34 % menos, hace un 45 % menos de llamadas y cuesta un 39 %
menos.** Los 4,1 minutos de la tercera medida eran del equipo aquella tarde (el Dev MCP y la consola iban más lentos:
`verificar` tardaba de 16 a 18 segundos fuera de las sesiones y hoy de 7 a 9) y de sesiones con más pasos, no del plugin.
Dos de las pasadas antiguas buscaron los scripts y usaron los de la copia instalada (0.7.0-beta.3), con tiempos
parecidos; sin la más lenta, la antigua sigue tardando más que la nueva (2,75 frente a 2,1 minutos).

**El caso de T1 con el plugin terminado** (misma base, encargo y memoria que T1, T3 y T3b):

| | T1 | T3 | T3b | Final |
|---|---|---|---|---|
| Minutos | 18,6 | 16,0 | 19,4 | 16,8 |
| Llamadas | 124 | 155 | 135 | 87 |
| Coste (USD) | 6,73 | 6,64 | 5,61 | 6,84 |

Las fases 3 a 6 no lo encarecen en tiempo. Los siete criterios nuevos o cambiados salieron en Gherkin y `comprobar.py`
no tuvo que avisar; el orden análisis, comprobación, prototipo y Word se mantiene; recoge los 15 puntos de la reunión.
El coste sube porque hizo más mensajes con una orden cada uno, con otra versión de Claude Code (2.1.299 frente a
2.1.296): no se puede atribuir al plugin. Salieron dos fallos: los avisos de «texto que queda viejo» pasaron de 4 a 7
por sesión a 21, porque los criterios en Gherkin empiezan igual y se señalaban entre sí, y nadie los atendía; y el aviso
de `estado` de que el proyecto no está en git se trató como información, así que un proyecto que ya existe nunca pasaría
a git.

**El retoque de análisis a ciegas** con el plugin terminado (`pruebas/evaluaciones/coste-retoque`): 22, 20 y 22
llamadas, ninguna pasada de `comprobar.py` con errores y 6/6 las tres (la ronda anterior, 22, 20 y 18). **El criterio de
las 25 llamadas se cumple** y lo nuevo (git, `AGENTS.md`, Gherkin, «Para», issues) no añade llamadas. Lo que sobra son
cosas del equipo donde se mide y dos llamadas recurrentes para saber en qué línea va la fila de §13.

**Revisión final de toda la rama**, independiente: recorrió como un equipo nuevo un proyecto nuevo, una reunión corta,
un evolutivo hasta producción, una urgencia y un retoque; todas las órdenes coinciden con su ayuda real, todo lo que
bloquea es uno de los dos bloqueos de B3 o su consecuencia directa y ninguno se queda sin salida, y el paquete (192
ficheros) no lleva nada de desarrollo ni datos de nadie. Encontró tres fallos: la barrera de `qa.py` contra pruebas y
producción tenía fugas; la urgencia no tenía regresión; y el fichero de la regresión no tenía dueño. Y repeticiones: la
regla «un fallo deja la issue pendiente salvo que una persona lo marque» estaba escrita en ocho sitios, y el `AGENTS.md`
generado había vuelto a 38 líneas.

**Ajustes finales**, de esas medidas y de la revisión: el aviso de texto viejo compara paso a paso en un criterio en
Gherkin (el arranque común ya no avisa; el criterio viejo escrito en otro sitio sí); `estado` dice «lanza
`proyecto.py iniciar`» y el método lo manda; `AGENTS.md`, las copias de los flujos y cada issue dicen que las órdenes
salen de la skill nombrada y que no se busca el plugin en el disco; `qa.py` solo repite contra desarrollo o el entorno
de corrección (lista blanca); la regresión de una urgencia va contra el entorno de corrección; cada regla en un solo
sitio; `AGENTS.md` en 30 líneas. Pruebas con todo unido: `comprobar_plugin.py`, 0 errores; los cinco selftest; las ocho
evaluaciones de `pruebas/evaluaciones/`; ingeniería inversa, 193 pasan y 2 se saltan.

## 0.7.0-beta.3 · Retoques ligeros y menores (11 de octubre de 2026)

Todas las evaluaciones, a ciegas con una copia del paquete, sin `pruebas/` ni `docs/`.

### Prueba de coste (`coste-retoque`): el camino corto

| Ronda | Método | Llamadas | Puntos |
|---|---|---|---|
| 0.7.0-beta.2 | Camino entero | 34, 34, 47 | 5/6 las tres (llamadas) |
| 1 | Camino corto con `proyecto.py version` | 27, 29, 30 | 5/6 las tres (llamadas) |
| 2 | Y `version --decision`, el informe de ejemplo, «Siguiente paso» sin tocar | 16, 19, 21 | **6/6 las tres** |
| 3 | Tras la revisión independiente (anexo, fila de §13) | 20, 27, 23 | 6/6, 5/6, 6/6 |
| 4 | El anexo solo si `comprobar.py` avisa; las dos órdenes de `ficha` e `impacto`, separadas | 22, 20, 18 | **6/6 las tres** |

- Ronda 1: las llamadas de más eran dudas que el camino corto no resolvía: leer otro informe como modelo, el formato del
  comentario con dos fuentes, buscar en la fuente la cita del «Antes», si se cambia el «Siguiente paso» (2-3 llamadas),
  y editar sin leer antes (la herramienta de edición lo pide: 4 llamadas fallidas en una pasada).
- Ronda 2: ninguna duda en las tres. El mínimo de `coste-retoque/README.md` sube de 15 a 16 porque cuenta leer lo que se
  edita.
- Ronda 3: «si cambia una parte de una pantalla, el anexo» hizo que las tres crearan un anexo que el proyecto no tenía
  (`derivadas --escribir` lo añade), y una pasó `--cambio` a `ficha`, que no lo admite. Ronda 4: el anexo, solo si
  `comprobar.py` avisa de que se quedó viejo; las dos órdenes, en un bloque cada una.
- La calidad no baja: las doce pasadas dejan D-01 con su «Antes» citado, la fila de §13 de EV-03 y el informe completo.

### Enrutado con las vecinas (`enrutado`)

`vecinas.json` con la descripción de `appian-sail-generator` 2.3.2 (su frontera con prototipos y buenas prácticas):
visibles **13/13** y las 10 ocultas nuevas (`vecinas/ocultas.json`, `--vecinas-ocultas`) **10/10**. Las seis
descripciones del plugin no cambian en esta versión: el resto de lotes no se repite. Raúl no publica la 2.3.2 (desactiva
`appian-sail-generator` en su cuenta): `vecinas.json` vuelve a la descripción publicada, la 2.3.1, y con ella también
salen **13/13** y **10/10**. El plugin marca la frontera por sí solo.

### El recién llegado (`recien-llegado`), con la versión actual

MNT documentada a ciegas contra el simulador (32 minutos) y respondida por otro agente con `as-is/` sin `extraccion/`.

| | 0.7.0-alpha.2 (después) | 0.7.0-beta.3 |
|---|---|---|
| Preguntas visibles | 21/22 | 22/22 |
| Preguntas ocultas | 7/7 | 7/7 |
| `evidencia.py` | bien | bien |
| `comprobar_asis.py` | 0 errores, 0 avisos | 0 errores, 0 avisos (8 avisos en la primera pasada, corregidos) |
| NV registrados | 8 | 12 |
| Palabras (total) | 17.293 | 14.744 (−15 %) |

- `puntuar.py` daba por mala una respuesta «No. …» a una pregunta sí/no: comparaba la primera palabra con el punto
  pegado. Corregido; sin el arreglo, 21/22.
- Lo que el agente encontró confuso se aclaró en las instrucciones; lo que no cabe (un proceso de 130 nodos en el
  presupuesto de su `.md` y el ancho de la arquitectura), en `docs/siguiente-version.md`.

### Diagramas al azar

Con 170 procesos al azar (semilla 7), etiquetas de salida de puerta sobre un tramo ajeno de 7 diagramas a 0, cruces de
359 a 347, sin que empeore ninguno; uno de la muestra pasa de 1.534 a 1.618 px de ancho (aviso de los 1.600).

## 0.7.0-beta.2 · Evolutivos, construcción y urgencias (10 y 11 de octubre de 2026)

### Evolutivo con urgencia (`evolutivo-urgencia`)

Proyecto ficticio (`EV-01` en producción, `EV-02` aprobada) y una incidencia crítica sobre un objeto de `EV-02`. Dos
pasadas a ciegas con las skills copiadas, sin `pruebas/` ni `docs/`.

| Pasada | Visible | Ocultas | Nota |
|---|---|---|---|
| 1 | 9/9, pasa | 5/6, no pasa | No pasó la URG a producción: el método decía «desatendida: nunca» aunque el encargo traía el visto bueno del jefe de proyecto, y quiso la prueba en producción antes de cerrar |
| 2 | 9/9, pasa | 6/6, pasa | Tras corregir: con el visto bueno catalogado como Aprobación se pasa (`--desatendida --fuente`), y «En producción» registra un pase que ya ocurrió: lo que falte por comprobar va en «Cierre» |

### Prueba de coste (`coste-retoque`): el camino entero

Calidad, las tres veces: informe aplicado en una unidad nueva Abierta, 0 aprobaciones, 0 DT, 0 pasadas de `comprobar.py`
con errores, ningún Word ni captura regenerados. **Coste: 34, 34 y 47 llamadas frente al tope de 25: no pasa.**

- Unas 22 llamadas son del método (leer SKILL.md y tres referencias, catalogar, buscar, informe, copia, editar
  funcional, técnico y decisiones, anexo, comprobar). El resto, dudas que el método no resolvía: si meterlo en la unidad
  Aprobada o abrir otra, el formato de la fila D, si hay que rehacer la captura.
- El tope se fijó antes de medir y no se cambia; el camino corto llegó en la 0.7.0-beta.3.

### Enrutado con vecinas (`enrutado`)

Lote nuevo `pruebas/evaluaciones/enrutado/vecinas/`: 13 peticiones de frontera con dos skills de fuera del plugin
(`appian-sail-generator` y `docx`, con su descripción literal en `vecinas.json`). Cada pasada, un agente nuevo sin
herramientas ni skills (`claude -p` desde una carpeta vacía) que solo recibe `puntuar.py --enunciado --vecinas`.

| Descripciones | Vecinas | Fronteras | Visibles |
|---|---|---|---|
| Las de 1.000 bytes como mucho, con fronteras con SAIL y Word | 12/13 ×3 | — | — |
| Buenas prácticas reclama el SAIL pegado que se revisa | 13/13 ×3 | 7/8, 8/8, 7/8 | 20/20 |
| Diagramas remite al analista los de estados y de datos | 13/13 ×2 | 8/8 ×3 | 20/20 |
| Tras la revisión: buenas prácticas, en un entorno o pegado; el SAIL a partir de requisitos, de `appian-sail-generator`; analista con margen (974 bytes) | 13/13 ×3 | 8/8 ×3 | 20/20 ×2 |

- El fallo de las tres primeras pasadas: «Revisa este SAIL: hace un a!queryRecordType dentro de un a!forEach» iba a
  `appian-sail-generator`, que se ofrece para «paste SAIL expressions and ask for fixes/improvements». Buenas prácticas
  dice ahora que construye, cambia, revisa o depura «in an environment or as pasted code» y, en su «Not for»,
  «generating SAIL from requirements (appian-sail-generator)». La otra mitad, que `appian-sail-generator` diga que no es
  para revisiones de buenas prácticas, es de Raúl.
- El recorte del analista para caber en 1.000 bytes hizo fallar la frontera de los diagramas de estados y de datos (con
  las descripciones de antes, 8/8 ×2): diagramas dice ahora que esos los hace el analista.

### Evaluaciones finales

Se pasan a ciegas, con las skills y los puntuadores tal como están, las ocultas del enrutado y las tres evaluaciones del
analista que más ha cambiado la versión. «Evolutivo con urgencia» y la prueba de coste se midieron antes con este método
y no se repiten.

**Cómo se pasaron.** Cada agente es un `claude -p` nuevo con una copia del paquete (`pruebas/empaquetar.py`, 177
ficheros), sin la herramienta Skill (lee los `SKILL.md`), sin CLAUDE.md ni ajustes
(`--restricted --setting-sources ""`), con la lectura de `pruebas/`, `docs/` y `skills/` del repositorio denegada y Bash
limitado a `python3` y `node` sobre la copia (y `uv run` en ingeniería inversa). El entorno solo deja lanzar agentes con
herramientas desde la carpeta del repositorio: la copia y los proyectos estuvieron en una carpeta ignorada dentro de
ella y al terminar pasaron a `$PROYECTOS_PRUEBA`. Los registros de cada sesión confirman que ninguno abrió `pruebas/` ni
`docs/`. Analista e ingeniería inversa, con Opus; el enrutado, con el modelo por defecto de `claude -p`.

| Evaluación | Resultado | Umbral | Pasa |
|---|---|---|---|
| Enrutado, ocultas (tres pasadas) | 10/10 ×3 | todas | sí |
| Incoherencias | 10/10 y 3/3; ninguna aplicada, ninguna coincidencia como cambio | todas (las dos salen 0) | sí |
| Demo | 6/6 y 6/6 | las dos salen 0 | sí |
| Evolutivo | 10/10 y 3/3; `comprobar.py` sin errores | 8 de 10 y 3 de 3 | sí |

- **Enrutado.** Las descripciones finales con las 10 ocultas, que no se habían pasado: un agente sin herramientas por
  pasada, desde una carpeta vacía.
- **Incoherencias** (`AYC-incoherencias/`, 75 turnos). El DF entra como 1.0 con sus IDs y cada reunión tiene su informe,
  con las 13 diferencias «Sí (🔒)» y «Pendiente». La versión sube a 1.1 solo por un COMPLETA que no pedía aprobación.
- **Demo** (`PRE-demo/`). Aplica los cuatro retoques, deja PAN-02 y PAN-05 pendientes y pide aprobación. Con «Aplica el
  de la solicitud; el de entregar y recoger, de momento no» cataloga la respuesta como aprobación (FU-04), cambia PAN-02
  y no toca PAN-05. En la ronda oculta cambia solo PAN-03.
- **Evolutivo** (`MNT-evolutivo/`). Primero la 1.0 de toda la aplicación desde `as-is/` (12 historias, 11 pantallas y 3
  procesos); después la reunión como 1.1 en la unidad EV-01, con §13 objeto a objeto, y el aviso del hallazgo Alta de lo
  que se modifica. En la oculta, la consulta del ERP pasa a una ficha INT con criterios en vez de una historia.
- **El `as-is/` de MNT** no estaba en este equipo: lo generó un agente a ciegas con ingeniería inversa contra el
  simulador (`mock_devmcp/`, `MOCK_APP=fixture_mal_hecha`, con el Dev MCP y el Appian MCP Server) en 40 minutos: 44
  objetos, 39 hallazgos, `comprobar_asis.py` con 0 errores y un aviso (11 pasa de su presupuesto de palabras) y
  `evidencia.py` bien. Está en `MNT/`. No se pasó la evaluación del recién llegado (sus preguntas).
- **Puntuadores.** Ninguno choca con el método nuevo: el de evolutivo lee la Situación de §13, no un «Origen» en las
  historias, y los de incoherencias y demo leen los informes y no dependen de que la versión suba (sin `versiones/v1.0`,
  buscan lo aplicado en el texto).

### Lo aprendido

- Mirar el CI tras cada subida: el Windows con consola cp1252 falló desde el principio de la versión (las pruebas de las
  evaluaciones escribían ✔ y 🔒 sin pasar la consola a UTF-8) y no se vio hasta casi el final.
- Las evaluaciones a ciegas encuentran lo que las pruebas no: «desatendida: nunca» bloqueaba un cierre con el visto
  bueno del jefe de proyecto en el propio encargo, y la fecha del pase no era la del pase.
- El coste de un retoque depende tanto del método como de cómo edita el modelo (34 frente a 47 llamadas con el mismo
  método): medirlo con varias pasadas.

## 0.7.0-beta.1 · Cierre de la integración de ingeniería inversa (9 de octubre de 2026)

### Punta a punta

Con la aplicación ficticia MNT en el simulador, en `$PROYECTOS_PRUEBA/MNT-e2e/`, cada paso lo hace un agente distinto
que sigue los SKILL.md con una copia del plugin, sin ver el repositorio:

| Paso | Tiempo | Resultado |
|---|---|---|
| Ingeniería inversa | 31 min | 35 hallazgos (5 Alta), 9 NV, 4 procesos (el de 130 nodos en 15 tramos); `comprobar_asis.py` 0/0 |
| Refactorización del módulo de órdenes | 18 min | 20 REF, 12 decisiones y los 9 NV en Pendientes; `comprobar_propuesta.py` 0/0 |
| Funcional y técnico, una reunión que cambia dos cosas, diagramas y Word | 54 min | 19 historias, 11 pantallas, 2 procesos; informe de impacto con aprobación de la ampliación; `comprobar.py` sin errores, también con `--anterior --impacto` |
| Prototipo y Word con las capturas | 26 min | 13 pantallas, 20 capturas enlazadas en el funcional; `validate.py` sin avisos de UX |

Los nueve NV llegan a las Pendientes de la propuesta y a una PT o una PC del análisis (los de negocio, como PC, y así al
guion de la próxima reunión); cada REF de la Solución tiene su DT; el Word no lleva IDs internos ni marcas.

### Lo aprendido

- El punta a punta encontró lo que ninguna fase veía porque está entre fases o en el primer paso: la versión de Python
  de uv y lo que pasa al repetir la ingeniería inversa en un proyecto que ya sigue adelante.
- Un aviso nuevo se mide con un proyecto real antes de darlo por bueno: el de texto viejo pasó sus pruebas y en el
  primer caso real solo daba ruido.

## 0.7.0-alpha.7 · Sin solapes (9 de octubre de 2026)

### Enrutado (`enrutado`)

Un agente que solo ve las seis descripciones elige la skill de cada petición; cada lote, un agente nuevo.

| Lote | Peticiones | Primera medida | Con las descripciones corregidas |
|---|---|---|---|
| Visibles (`pruebas/enrutado.json`) | 20, cuatro o tres por skill y una por frontera | 20/20 | 20/20 |
| Ocultas | 10, una variante de cada frontera | 10/10 | 10/10 |
| Fronteras difíciles (tras la revisión) | 8, sin las palabras que delatan la skill | — | 8/8 |

La revisión vio que las peticiones de frontera llevaban la pista que las resuelve: un clasificador que solo cuenta
palabras acertaba 16 de 20 visibles y 5 de 10 ocultas. Por eso el tercer lote: revisar una aplicación entera frente a un
objeto, las tablas de una aplicación sin papeles, los diagramas de estados y de datos (del analista), un proceso contado
en una reunión (primero el analista), algo navegable antes de validar, un timeout en producción y los cambios de una
reunión sobre lo validado. `prueba_puntuar.py` comprueba que no lleven esas palabras.

### Lo aprendido

- Una prueba de enrutado con las palabras de las descripciones mide el vocabulario, no la frontera. La prueba de que
  mide algo es un clasificador tonto que falla donde el agente acierta.
- «Qué escribe» cruzado con lo que escriben los scripts encontró una escritura fuera del proyecto (`grafo.json`) que
  ninguna prueba había visto.

## 0.7.0-alpha.6 · Equipo (9 de octubre de 2026)

### Lo aprendido

- Antes de arreglar un fallo que solo se ve en otra máquina, confirmar la causa: el primer arreglo de Windows tenía
  sentido y no era el fallo (en Windows, `subprocess` con «bash» a secas encuentra el lanzador de WSL de System32 antes
  que el bash de Git). Una aserción que pasaba (el código de salida) ya lo decía.
- Una variable que hace pasar las pruebas (`PYTHONUTF8=1`) también puede esconder lo que más le pasa a quien usa el
  plugin: sin ella se rompían nueve scripts al imprimir «→» o «✓». Conviene una combinación de la matriz sin ella.
- Lo que no se puede ver (los registros de un job de GitHub, que la API no da) se hace visible desde el propio workflow:
  si la comprobación falla, deja la cola de la salida en anotaciones.
- Una comprobación estática barata (AST: `print` sin `reconfigure`, `subprocess` de texto sin `encoding`) evita que el
  fallo vuelva con el siguiente script.

## 0.7.0-alpha.5 · Analista (9 de octubre de 2026)

### Incoherencias, demo y evolutivo (`incoherencias`, `demo`, `evolutivo`)

Tres casos ficticios en `pruebas/evaluaciones/`, cada uno ejecutado por un agente a ciegas (copia de las skills, sin
`pruebas/` ni `docs/`) en su proyecto de `$PROYECTOS_PRUEBA`.

| Caso | Primera medida | Segunda medida (tras la pasada de correcciones) |
|---|---|---|
| Incoherencias: DF validado y tres reuniones anteriores, 10 incoherencias + 3 ocultas | 0/10 y 0/3 | 10/10 y 3/3, ninguna aplicada, ninguna coincidencia como cambio |
| Demo: seis pantallas, dos validadas; un comentario por pantalla + un correo oculto | 4/6 | 6/6 y 6/6 |
| Evolutivo: tres historias sobre MNT + una cuarta oculta | 10/10; oculta 2/3 sin aprobar y 3/3 aprobada | — (10/10 y 3/3 con el puntuador nuevo) |

- **El fondo estaba bien desde la primera medida y el formato no.** En incoherencias y demo, los agentes encontraron
  todo, con su pieza, sin aplicar nada sin aprobación; pero escribieron «Aprobación: cambia HU-01 🔒…» en la columna
  «Requiere», que la skill no definía, y el puntuador lo da por no pedido. La revisión lo confirmó (con «Sí (🔒)» salen
  10/10, 3/3 y 6/6). Se fija el formato y `comprobar.py` lo exige; no se ablanda el puntuador.
- **La ronda oculta de evolutivo** pide una ampliación, que en una sesión desatendida no se aplica sin aprobación: el
  README da ahora la aprobación por adelantado, como la demo.
- **El puntuador de evolutivo emparejaba los objetos nuevos solo por tipo**: con tres quitados seguía en 9/10. Ahora
  cada uno lleva las raíces de nombre que valen, sacadas de la reunión.
- `comprobar.py` sin errores en los tres. Proyectos: `AYC-incoherencias/`, `PRE-demo/` y `MNT-evolutivo/` (las primeras
  medidas, en `AYC-incoherencias-1/` y `PRE-demo-1/`).

### Lo aprendido

- Un formato que solo está en un ejemplo no es un formato: dos agentes distintos escribieron lo mismo fuera de él. Si
  algo se va a leer con un script, la skill lo define y el comprobador lo exige.
- Las reglas para la sesión desatendida tienen que cuadrar con las comprobaciones: «entra como ⚠️» chocaba con «una
  pieza 🔒 no cambia sin aprobación».
- Los avisos que no se pueden apagar se ignoran: 25 en el evolutivo, todos ya atendidos por una PT o una PC, y 4 de 4
  falsos en el texto viejo. Ahora se apagan cuando lo que piden ya está hecho.
- Los puntuadores se revisan quitando lo que debería contar, como en refactorización: el de evolutivo no bajaba.

## 0.7.0-alpha.4 · Refactorización (9 de octubre de 2026)

### Malas prácticas sembradas (`malas-practicas`)

Un agente sigue el `SKILL.md` sobre `$PROYECTOS_PRUEBA/MNT/` con una copia de las skills, sin ver `pruebas/` ni `docs/`,
con alcance «toda la aplicación», seis meses y sin tocar las reglas `CMN_`. `puntuar.py` cuenta una mala práctica si una
REF cita sus objetos en la evidencia, una de sus secciones aceptadas en la Regla y sale en Solución.

| | Primera propuesta | Segunda propuesta (tras la revisión) |
|---|---|---|
| REF / palabras / tiempo | 27 / 6.298 / 16 min | 26 / 6.678 / 16 min |
| Visibles, primer puntuador | 11/11 | — |
| Visibles, puntuador por sección | 9/11 (MP-05 y MP-11) | 10/11 (MP-01) |
| Ocultas | 3/3 | 3/3 |
| NV de las reglas `CMN_` en Pendientes | sí | sí |
| `comprobar_propuesta.py` | 0/0 (el de entonces) | 0/0 |

- **El primer puntuador medía poco.** Aceptaba cualquier sección del documento de buenas prácticas esperado: la revisión
  quitó las cuatro REF que trataban MP-04, MP-08, MPO-01 y MPO-02 y seguía saliendo 11/11 y 3/3. Ahora cada mala
  práctica lleva `bp_aceptadas`, fijadas por un agente con la descripción y las secciones, sin ver ninguna propuesta.
- **Con el puntuador nuevo, la primera propuesta da 9/11**, y los dos fallos venían de `senales.md`: el correo repetido
  iba a BP 03 §13 y el connected system de desarrollo a BP 07 §2, que no trata los entornos. Corregidas las dos filas,
  la segunda propuesta, hecha a ciegas con la skill corregida, da 10/11: MP-01 (el listado sin paginar) sale con BP 01
  §7 y BP 02 §5.3.
- Las dos propuestas citan en una sola REF los dos hallazgos de `MNT_PM_Antiguo` (huérfano y sin ejecuciones).
- Proyectos: `MNT/` (la segunda) y `MNT-refactorizacion-1/` (la primera), en `$PROYECTOS_PRUEBA`.

### Lo aprendido

- Un puntuador también se revisa con sondas: quitar lo que debería contar y ver si el número baja. El primero pasaba por
  bueno lo que no medía.
- Las listas de lo aceptado se fijan antes de ver un resultado y no se tocan después; cuando un resultado no cuadra, se
  arregla la skill y se vuelve a medir a ciegas.
- La tabla de señales decide la regla que cita cada REF: un error en una fila es un error en todas las propuestas.
- Lo que falta en buenas prácticas sale enseguida al usarla para justificar (el «Cancelar» de un formulario de inicio,
  un paso que se hace siempre): apuntado para la siguiente versión.

## 0.7.0-alpha.3 · Diagramas (9 de octubre de 2026)

### Un proceso de 130 nodos

| | Antes (0.7.0-alpha.2) | Después |
|---|---|---|
| `MNT_PM_GestionOrden` (130 nodos), `.drawio` | una página de 29.536 px | 14 tramos de 1.244 a 1.528 px |
| PNG | uno de 22.171 px (la skill promete 3.200) | uno por tramo |
| `.bpmn` | del exportador de ingeniería inversa | uno, de `diagrama.py`, válido contra el XSD |
| Pruebas de ingeniería inversa | 139 | 140 |

### Lo aprendido

- Un dibujo puede ser correcto en el `.drawio` y engañar a la vista. La prueba que lo atrapa mide la geometría (qué
  cruza qué), no el XML; conviene que toda colocación nueva pase por ella.
- Lo que se hace sin navegador tiene que dejar la carpeta coherente: un PNG que ya no es del dibujo es peor que ninguno.
- Partir en páginas resuelve el ancho pero crea otro problema, encontrar un paso; la salida de `crear` tiene que decir
  dónde está cada uno.
- El comprobador del plugin también es código del plugin: la anotación `int | None` de la versión anterior lo rompía en
  Python 3.9 y ninguna prueba lo veía, porque todas corren con el Python del equipo.

## 0.7.0-alpha.2 · Precisa y sin relleno (8 de octubre de 2026)

### El recién llegado (`recien-llegado`)

La skill documenta MNT contra el simulador; otro agente, que solo lee `as-is/` sin `extraccion/`, responde las
preguntas. «Antes» es la skill antes de esta versión (4a7a09f); «después», con las preguntas primero, la disciplina de
evidencia y una sola entrada.

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
  y las tablas, por la columna de evidencia y el «Para qué» de INVENTARIO, que pide la versión; la prosa baja un 10 %.
  Una primera medida «después», sin una sola entrada, tenía 17.741 palabras (contadas igual que las de la tabla). El
  criterio de palabras se aceptó de forma provisional el 8 de octubre de 2026.
- **Protocolo.** Con la primera instrucción («cada elemento corto»), quien respondía resumió los tres CMN como «las
  reglas CMN_» y Q-21 contaba como fallo aunque LEEME los nombra. La instrucción pasa a pedir cada objeto por su nombre
  (`recien-llegado/README.md`) y las cifras de la tabla son las de las dos medidas respondidas con ella.
- **Q-10, ambigua en la documentación.** 09 marcaba «Por entorno: No» en las constantes porque ninguna tiene la marca de
  Appian, y quien responde concluía que ninguna cambia por entorno, aunque `MNT_URL_ERP_PRE` guarda la URL de
  preproducción. Lo introdujo esta misma versión; la revisión lo corrige con dos columnas, «Depende del entorno» y
  «Marca de entorno».
- Proyectos en `$PROYECTOS_PRUEBA`: `MNT-antes/`, `MNT-despues-1/` y `MNT/` (el que usan `malas-practicas` y
  `evolutivo`).

### Lo aprendido

- Una medida con un agente que sigue la skill de punta a punta encuentra lo que las pruebas no ven: los dos informes
  dieron 17 y 18 puntos de fricción, la mitad de diagramas. Conviene repetirla al cerrar cada fase que toca una skill.
- La instrucción de quien responde también se mide: «corto» le hizo resumir nombres. Las instrucciones de las
  evaluaciones se fijan en su README y se usan iguales en «antes» y «después».
- Contar palabras sin separar lo que se añade a propósito (preguntas, evidencia) de la prosa da un criterio que castiga
  lo que la fase pide. La cifra útil es la prosa, que baja.
- Con una sola medida por lado, una diferencia de pocos cientos de palabras está dentro de lo que varía de una ejecución
  a otra.
- La batería tiene techo: 7/7 y 21/22 en los dos lados, y solo Q-21 distingue. Para las evaluaciones siguientes hacen
  falta preguntas que «antes» falle.
- La revisión de la fase, con sondas sobre los proyectos reales, encontró lo que ni las pruebas ni las medidas vieron:
  una regresión de la propia fase (Q-10), `objetos` sin validar en el contrato de `datos/` y un error falso con los
  objetos de fuera de la aplicación.

## 0.7.0-alpha.1 · Ingeniería inversa en el plugin (8 de octubre de 2026)

### Lo aprendido

- La revisión por tarea, con agentes y varias rondas, alargó la fase. Desde entonces, una revisión independiente por
  fase y las tareas pequeñas en línea (Raúl, 8 de octubre de 2026).
- La decisión de no ocultar nada llegó a mitad de fase y dejó sin objeto el saneado de la extracción y una ronda de
  correcciones. Las decisiones de datos y privacidad se toman antes de empezar una fase, y lo nuevo que surge a mitad va
  a `docs/siguiente-version.md`.
- La revisión de la fase vio lo que no ven las de tarea: el entorno al retomar, la versión sin subir y la orden zip del
  README. Se revisa la rama entera y también la copia del paquete.
- Claude Code no actualiza un plugin mientras su versión no cambia: cada cambio que llega a `main` sube la versión.
- Con el plugin instalado, las herramientas MCP se llaman `mcp__plugin_<plugin>_<servidor>__…`: los textos de las skills
  nombran el servidor, no el prefijo.
- Las restricciones globales (rutas cortas, nada fuera de `<p>`, nada oculto) se prueban ejecutando y mirando el disco,
  no buscando frases en los textos.
