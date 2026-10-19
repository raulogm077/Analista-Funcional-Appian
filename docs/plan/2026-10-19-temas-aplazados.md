# Temas aplazados antes de publicar

El 19 de octubre Raúl pidió trabajar los temas aplazados antes de publicar y preguntar por las decisiones necesarias.
Esta fase parte de `84d2b24`, con la primera tanda aplicada y comprobada. Rama de integración: `codex/aplazados`, en
`Proyectos IA/Plugin-aplazados-codex`. La rama anterior conserva su cierre. `main` permanece intacta y sincronizada.

**Estado de integración posterior:** a petición de Raúl, la rama de Claude `automejora-pruebas` absorbió por avance
rápido los 21 commits de `codex/aplazados` y es ahora la única rama de trabajo. Las ramas auxiliares se eliminaron;
el repositorio original está en `automejora-pruebas`. Las rutas y ramas del párrafo anterior documentan dónde se hizo
la fase, no dónde continuarla. Tras comprobar que estaban limpios y que solo contenían cachés ignoradas, se retiraron
los nueve worktrees auxiliares. Las pruebas y evidencias quedan bajo `Proyectos IA/Pruebas-plugin/`. No se ha publicado
una nueva versión.

## Decisiones y respuestas

Las preguntas enviadas al usuario no se consideran aceptadas por silencio. Mientras llegan las respuestas, se avanza
en las tareas independientes y en la lectura de evidencia ya guardada.

| Pregunta | Propuesta | Estado |
|---|---|---|
| C8: una diferencia confirmada de permisos de acción o inicio de proceso | Bloquear la issue salvo aceptación humana expresa de ese comportamiento, registrada para la diferencia concreta; permisos ilegibles como no comprobados | Aceptado por Raúl |
| D1: dos unidades cambian una misma pieza | Secuenciar la pieza compartida, manteniendo el trabajo independiente; no guardar encargos históricos por unidad | Opción 2 elegida por Raúl tras comparar pros y contras |
| Aplicación/proyecto para deriva, LEEME y comparación de refactorización | Usar la aplicación y el entorno de desarrollo indicados por Raúl; concretar aparte cualquier ejecución de reglas o procesos | Aplicación y entorno elegidos; lectura autorizada |
| D7: issues grandes | Mantener una issue con subtareas y avance guardado, sin sustituir la verificación final | Elegido por Raúl tras comparar pros y contras |

## Trabajo

| Tema | Qué se hace primero | Estado |
|---|---|---|
| E1: borrador §13 | Medida sobre P10: las columnas de definición dan 50/141 objetos correctos y un falso positivo; los restantes requieren interpretación | No se añade un generador general con esa cobertura |
| E2: corregir dependencias | Corrección humana motivada, reversible, sin ciclos y con caducidad si cambia el encargo o sus dependencias | Integrado en 1868acd; 393 comprobaciones del analista correctas |
| D7: issues grandes | Una issue con avance por pasos, sin duplicar objetos ni sustituir la verificación final; en P10, 13 de 25 issues reciben 43 subtareas | Integrado en 9242e5a; ocho casos focales y suite analista conjunta correctos |
| D1: secuenciar piezas | Impedir que el texto de una segunda unidad contamine el encargo de la primera, también con cierre manual; conservar retoques independientes | Integrado en 8738a06 y 9088bd2; 14 casos focales y suite analista conjunta correctos |
| C8: permisos | Contratos y respuestas reales; comparar configuración decidible y registrar aceptación humana acotada, sin perder historial | Integrado en 12646ae, c6ac2a4 y 616680e; 15 casos focales y suite analista conjunta correctos |
| E3: comparación de refactorización | Ensayo autorizado sobre una regla pura de texto, con casos guardados y de borde antes/después; restauración posterior | 3/3 casos guardados y cinco bordes iguales. Regla restaurada y verificada; `deriva` detecta edición por historial 1→3, no un cambio semántico persistente. Medida acotada, no global |
| E5: ancho de arquitectura | Cinco cajas pueden producir 4.442 px; aplicar el límite ya existente de 1.600 px a la vista general y usar detalles por capa | Integrado en 40578bd; renders medidos |
| Etiquetas de puertas | 1.000 casos, semilla 11: etiquetas ambiguas 8→0, sin empeorar cruces ni solapes caso por caso | Integrado en 40578bd; selftest y revisión de PNG correctos |
| Conexiones BPMN | Enrutar y reservar etiquetas conjuntamente, conservar puertos y geometría anterior si el candidato empeora | Semilla 11: 126→30 avisos; semilla 23: 103→38, con 1.000 procesos cada una y cero regresiones por caso en la auditoría final. 43/46/677 resueltos; persisten casos fuera de la mejora conservadora |
| PDF con LibreOffice | Convertir el Word ficticio por la orden real del plugin y revisar texto, figuras y páginas | Código 0; 12 páginas, 725 párrafos, 51 títulos y dos figuras conservados. Índice sin números de página frente a Word; el script avisa de revisarlo. Selftest analista y básica correctos; CI de esta rama pendiente |
| Evaluación ciega de malas prácticas | Reconstruir el as-is ficticio de MNT y redactar una propuesta sin acceso a las claves | As-is validado (44 objetos, 0 errores/avisos); última propuesta ciega 10/11 visibles, 3/3 ocultas y 0 errores/avisos tras precisar la comparación de catálogos compartidos. Auditoría independiente dejó ocho matices fuera del puntuador |
| D11: nueva pestaña | Navegación y parámetros, recarga, historial, aislamiento de claves y números que deben conservarse como texto | Integrado en f87d903; suite de prototipos correcta, ocho casos nuevos |
| E6: LEEME | Medir la aplicación elegida antes de cambiar el presupuesto | LEEME real completo no medido: la extracción tiene definiciones correctas de 24/248 UUID. MNT ficticia validada: 731/1.350 palabras con 44 objetos; no justifica cambiar el presupuesto |
| E7: batería | Dos grupos reales: 176,7 s en serie y 126,4 s en paralelo; cinco pruebas del ejecutor correctas | Integrado en 327cfa4; rendimiento de batería completa pendiente de CI |

La CLI de Claude cargó el plugin de esta rama con `--plugin-dir`, pero la primera petición terminó en HTTP 429 antes
de actuar. D1, D7 y C8 siguen sin medirse con Claude; no se repitió la llamada. Se preparó una campaña de seis fases,
con diez controles offline correctos y parada previa al restablecimiento de cuota (20/10, 16:00 de Madrid). P8 sí
se completó después con una sesión real de Codex: leyó ambos localizadores y ejecutó `proyecto.py estado .` con
código 0 y hashes idénticos. Elegir MXC por invocación permitió completar el ensayo, manteniendo solo lectura y
aprobación `never`; el ejecutor legacy fallaba al arrancar su helper. La prueba del hook de requisitos en
PowerShell 5.1 sí mostró el aviso con una
dependencia simulada como ausente y dejó la marca de una vez por versión. Evidencias en
`$PROYECTOS_PRUEBA/aplazados-codex-20261019/claude-comportamiento/`.

La medida de E7 solo comprende QA y refactorización, con todos sus resultados correctos. No se extrapola al conjunto:
los logs antiguos de CI imprimían los grupos al terminar y no permiten recuperar sus tiempos individuales. El
ejecutor ahora informa de cada duración, limita la concurrencia a dos grupos y admite `--trabajos 1` para comparar.
No se ha ejecutado `--completo` localmente.

La suite analista integrada terminó con 399 comprobaciones correctas (498,3 s, exit 0). La integración incluyó
dos correcciones de borde: el cierre manual no salta una protección de encargo y una fila ilegible del historial de
permisos no desaparece al regenerar. Las marcas de lectura interrumpida añaden un aviso sin borrar bloqueos previos.
La corrida completa de inversa dio 243 correctas, ocho fallos y dos omisiones. Los ocho fallos pertenecían a dos
módulos: el simulador de permisos no implementaba el método nuevo y un comentario activaba un detector de vocabulario.
Tras corregirlos, pasan sus 23 casos; el caso Mermaid omitido en uv pasa con Python local. Son 252 casos distintos
correctos entre los recorridos y una omisión exclusiva de POSIX. No se registra la corrida inicial como verde ni se
suman dos veces los quince casos que se repitieron. Detalle y límites en `docs/evaluaciones.md`.

## Incidente de lectura en el entorno elegido

La lista conjunta contiene 248 objetos: los 245 de Designer, un agente y dos carpetas de listas específicas. La
medición detectó y corrigió dos errores del extractor: tipos de valor de constantes usados como tipos de objeto
(09872ee) y `getRecordEventsConfig` considerado genérico en vez de exclusivo de record types (13115f9).
Las pruebas son ficticias y locales; la corrección no acredita aún una extracción completa.

La extracción disparó repetidamente el inicio de sesión. El código instalado de DevMCP considera cualquier 401/403
como sesión caducada y vuelve a abrir el navegador; no distingue una denegación de permisos. Al avisar Raúl se
detuvieron ambos árboles de procesos del extractor y sus helpers de autenticación. La comprobación posterior dio
cero procesos de esta medición activos. No se modificó DevMCP ni se cambiaron credenciales o permisos.

Se conservan 76 respuestas (66 correctas y diez fallidas por cierre del navegador), inventario y lecturas puntuales;
no hay informe final de extracción ni historial suficiente para declarar medidos LEEME o deriva. La extracción
masiva permanece detenida. La parada ante acceso/login interrumpido está integrada en 250f8e9: cancela llamadas aún
en cola, conserva evidencia previa, informa de lectura parcial y evita deducir ausencias en `verificar` o `deriva`.
Sus 32 pruebas focales pasan; no controla llamadas ya iniciadas ni la reautenticación interna de DevMCP.
No reanudar una extracción masiva solo porque ya se corrigió el selector de eventos. El detalle y los límites están
en `aplazados-codex-20261019/gde-lectura/ESTADO-MEDICION.md`, fuera del repositorio.

Como medida más pequeña, se compararon dos enumeraciones completas del inventario real: 22 listas de aplicación y
una respuesta de entorno en la nueva lectura, sin definiciones ni historiales por objeto. Los 248 UUID de las listas
de las 12:42 pasaron a 249 a las 17:05: una interfaz nueva, ninguna baja. Esto detecta pertenencia al inventario,
pero no cambios internos; no se etiqueta como deriva global. El informe y ambos puntos de comparación están en
`aplazados-codex-20261019/gde-inventario-minimo/`, fuera del repositorio. La extracción amplia no se reanudó.

Raúl confirmó que puede abrir el agente y ver su configuración en Designer. El bundle instalado usa dos vías:
las listas se leen con el cliente del servlet autenticado en navegador; `getAgent` usa el cliente de la API nativa,
que espera un token del contexto de la petición. El acceso por Designer no acredita esa segunda vía. Esta limitación
es distinta del bucle de reautenticación del cliente del servlet; ninguna demuestra una contraseña incorrecta.
Una única llamada `getApplication` por el MCP ya conectado respondió correctamente en 0,7 s, sin reintentos.
Una llamada posterior `getAgent`, sin expansión ni reintentos, devolvió HTTP 401 en 383 ms. El contraste confirma
la limitación de esa lectura nativa en la sesión actual. No acredita una extracción completa ni ausencia del agente.

La sesión principal integra y mantiene el estado; tres subagentes entregaron construcción, medición de inversa y
permisos, cada uno desde su worktree, además de diagramas y prototipos. Pruebas y datos reales van en
`Proyectos IA/Pruebas-plugin/aplazados-codex-20261019/`, nunca
en el repositorio. Se mantienen las comprobaciones de `CLAUDE.md`: básica antes de cada commit, pruebas de las
capacidades tocadas y batería completa en CI, sin `--completo` local. Esta petición no publica una versión.
