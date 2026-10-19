# Temas aplazados antes de publicar

El 19 de octubre Raúl pidió trabajar los temas aplazados antes de publicar y preguntar por las decisiones necesarias.
Esta fase parte de `84d2b24`, con la primera tanda aplicada y comprobada. Rama de integración: `codex/aplazados`, en
`Proyectos IA/Plugin-aplazados-codex`. La rama anterior conserva su cierre. `main` permanece intacta y sincronizada.

## Decisiones y respuestas

Las preguntas enviadas al usuario no se consideran aceptadas por silencio. Mientras llegan las respuestas, se avanza
en las tareas independientes y en la lectura de evidencia ya guardada.

| Pregunta | Propuesta | Estado |
|---|---|---|
| C8: una diferencia confirmada de permisos de acción o inicio de proceso | Bloquear la issue salvo aceptación humana expresa de ese comportamiento, registrada para la diferencia concreta; permisos ilegibles como no comprobados | Aceptado por Raúl |
| D1: dos unidades cambian una misma pieza | Secuenciar la pieza compartida, manteniendo el trabajo independiente; no guardar encargos históricos por unidad | Opción 2 elegida por Raúl tras comparar pros y contras |
| Aplicación/proyecto para deriva, LEEME y comparación de refactorización | Usar la aplicación indicada por Raúl en Indra; concretar aparte cualquier ejecución de reglas o procesos | Aplicación y entorno elegidos; lectura autorizada |
| D7: issues grandes | Subtareas con avance guardado, o issues independientes tras separar sus objetos | Pros y contras explicados; espera elección |

## Trabajo

| Tema | Qué se hace primero | Estado |
|---|---|---|
| E1: borrador §13 | Medida sobre P10: las columnas de definición dan 50/141 objetos correctos y un falso positivo; los restantes requieren interpretación | No se añade un generador general con esa cobertura |
| E2: corregir dependencias | Corrección humana motivada, reversible, sin ciclos y con caducidad si cambia el encargo o sus dependencias | Integrado en 1868acd; 393 comprobaciones del analista correctas |
| D7: issues grandes | P10: Base de 68 objetos; otras de 12–20 requisitos agrupados por objetos compartidos | Espera elección tras la medida |
| D1: secuenciar piezas | Impedir que el texto de una segunda unidad contamine el encargo de la primera, también antes de aprobarla | Implementación en curso |
| C8: permisos | Contratos y respuestas reales; comparar configuración decidible y registrar aceptación humana acotada | Implementación en curso |
| E3: comparación de refactorización | Buscar un caso real en la aplicación elegida y delimitar qué se ejecutaría en cada versión | Lectura en curso; sin ejecutar reglas ni procesos |
| E5: ancho de arquitectura | Cinco cajas pueden producir 4.442 px; aplicar el límite ya existente de 1.600 px a la vista general y usar detalles por capa | Integrado en 40578bd; renders medidos |
| Etiquetas de puertas | 1.000 casos, semilla 11: etiquetas ambiguas 8→0, sin empeorar cruces ni solapes caso por caso | Integrado en 40578bd; selftest y revisión de PNG correctos |
| D11: nueva pestaña | Navegación y parámetros, recarga, historial, aislamiento de claves y números que deben conservarse como texto | Integrado en f87d903; suite de prototipos correcta, ocho casos nuevos |
| E6: LEEME | Medir la aplicación elegida antes de cambiar el presupuesto | Lectura en curso |
| E7: batería | Dos grupos reales: 176,7 s en serie y 126,4 s en paralelo; cinco pruebas del ejecutor correctas | Integrado en 327cfa4; rendimiento de batería completa pendiente de CI |

La medida de E7 solo comprende QA y refactorización, con todos sus resultados correctos. No se extrapola al conjunto:
los logs antiguos de CI imprimían los grupos al terminar y no permiten recuperar sus tiempos individuales. El
ejecutor ahora informa de cada duración, limita la concurrencia a dos grupos y admite `--trabajos 1` para comparar.
No se ha ejecutado `--completo` localmente.

La sesión principal integra y mantiene el estado; tres subagentes trabajan en construcción, medición de inversa y
permisos, cada uno en su worktree (diagramas y prototipos ya entregados). Pruebas y datos reales van en
`Proyectos IA/Pruebas-plugin/aplazados-codex-20261019/`, nunca
en el repositorio. Se mantienen las comprobaciones de `CLAUDE.md`: básica antes de cada commit, pruebas de las
capacidades tocadas y batería completa en CI, sin `--completo` local. Esta petición no publica una versión.
