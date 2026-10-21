# Evaluaciones

Resultados y límites que sirven para decidir sobre el plugin. Los escenarios reproducibles están en
`pruebas/evaluaciones/`; fuentes, proyectos y registros completos permanecen fuera del repositorio.
Lo pendiente se sigue en [siguiente-version.md](siguiente-version.md). Las cifras de cada fila pertenecen
al commit y al alcance indicados; no se suman controles repetidos ni se trasladan resultados a otro código.

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
| Automejora del 14–19/10 | Las pruebas reales detectaron pérdidas entre §13, supuestos e issues, colisiones compartidas y límites de verificación. Tras aplicar las lecciones: 25/25 issues reciben sus supuestos/reglas; secuenciación, subtareas y aceptación humana acotada probadas. No sustituyen QA real por rol. |
| Método de la 0.8.0-beta.1, [PR #12](https://github.com/raulogm077/Analista-Funcional-Appian/pull/12), `eedff58` | Contexto por consultas, flujos únicos, repositorio por proyecto, Gherkin, issues y QA independiente. Comparación de retoque alternada 3+3: 3,2→2,1 min, 38→21 llamadas, 1,87→1,14 USD. Dos pasadas antiguas usaron una copia instalada anterior; no atribuir precisión universal. El caso documental largo bajó 124→87 llamadas, con coste 6,73→6,84 USD, sin ahorro monetario acreditado. |
| QA con defectos sembrados de esa fase | Sesiones independientes con SAIL detectaron 3/4; se escapó el color. Navegador detectó 4/4, repetición ~9 min frente a ~75 s. Justifica QA independiente y navegador para criterios visuales, sin deducir equivalencia de capas. El ensayo de quien construyó no era independiente. |
| 0.7.0: evaluaciones ciegas y refactorización | Incoherencias 10/10+3/3, demo 6/6+6/6, evolutivo 10/10+3/3 y enrutado reservado 10/10×3. Refactorización posterior: 10/11 visible y 3/3 oculto; auditoría con ocho matices fuera del puntuador. Las sondas revelaron puntuadores demasiado permisivos: el verde requiere revisar también lo que no cuentan. |
| 0.7.0: recién llegado y diagramas | Recién llegado 21/22→22/22 y 7/7 reservado; palabras 17.293→14.744 (−15 %). Proceso de 130 nodos pasa de una página de 29.536 px a catorce tramos de 1.244–1.528 px. No mide una aplicación real completa. |
| Diagramas antes de beta.2 | Dos lotes de 1.000 procesos: avisos 126→30 y 103→38, sin regresiones por caso ni aumento de dimensiones; residuos conservados. Geometría automática, no garantía de legibilidad universal. |
| Lectura y refactorización reales acotadas | Inventario 248→249 con 23 respuestas, sin leer definiciones; no deriva global. Una regla: 3 casos guardados y cinco bordes equivalentes, expresión original restaurada; historial 1→3 detectado. No equivalencia universal. |

Decisiones vigentes de esas fases: `getAgent` queda aparcado tras el reporte a Appian; no reiniciar en bucle
extracciones con error de acceso. La activación/comportamiento con Claude sigue **NOT MEASURED** y se omitió
expresamente para aquella entrega; no es obligatoria en la fase actual. La instalación visual tampoco se convirtió
en puerta automática. Un resultado técnico verde no aprueba visual, seguridad efectiva, efectos persistidos ni pase.
