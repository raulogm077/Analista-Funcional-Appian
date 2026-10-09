# Señales

Qué buscar en `as-is/` para encontrar un problema y qué sección de `appian-best-practices` lo trata. Aquí solo se
reconoce el problema; qué hacer y por qué lo dice esa sección: `python3 <skill>/../appian-best-practices/scripts/seccion.py nn x`
la imprime, y su número es la «Regla» de la REF.

- **Un hallazgo ya es la señal.** Si `as-is/datos/hallazgos.json` lo tiene, la REF cita su `H-…` y su certeza.
- **Evidencia en objetos concretos.** Una señal sin hallazgo cuenta si se ve en la ficha del anexo de un objeto del
  inventario. Lo que solo dice un nombre (una entidad `*_HIST`) es 🔶 «según su nombre» hasta verlo en la definición.
- **Dato ausente no es defecto.** Las señales marcadas «si la trae» dependen de configuración que la extracción no
  siempre devuelve. Si `as-is/` no la trae, la señal no se cumple; como mucho, es un pendiente.
- **La lista no es cerrada.** Otro problema se trata igual: su evidencia en `as-is/` y la sección que lo dice.

Documentos de `as-is/`: `03` modelo de datos, `04` seguridad, `05` integraciones consumidas, `06` APIs expuestas, `07`
batches, `08-procesos-bpmn/`, `09` valor adicional (avisos de validación, huérfanos y registro de hallazgos), `10`
pantallas y `11` reglas de negocio. En el anexo, cada ficha trae la definición, las expresiones con número de línea,
los nodos de un proceso y las respuestas de la plataforma (validación, ejecuciones, dependientes).

## Datos

| Señal | Dónde se ve en as-is/ | Problema | BP |
|---|---|---|---|
| CDT y data store en la aplicación; `a!queryEntity`, query rules o Write to Data Store Entity | `datos/inventario.json` (tipos `cdt` y `dataStore`), `03`, expresiones y nodos del anexo | Modelo antiguo: sin relaciones de record ni data fabric | BP 01 §7 |
| Record type sin sincronizar o legacy | `03`, ficha del record type (origen y acceso) | Sin relaciones ni las funcionalidades que dependen de ellas | BP 01 §2 |
| Campos que hacen de clave ajena (`…Id`) sin relación declarada | `03`, ficha del record type (`relationships`) | Navegación y consultas a mano entre entidades | BP 01 §4 |
| Un catálogo guardado como texto libre en varias entidades | `03` | Valores incoherentes entre entidades | BP 01 §1.1 |
| Tabla grande sincronizada sin filtros | `03` (volúmenes del data fabric) | Consumo, consultas lentas y límite de filas del tier | BP 01 §3.5 |
| Historial o auditoría a mano: entidades `*_HIST` o `*_LOG`, escrituras extra en cada proceso | `03`, nodos de escritura en la ficha de los process models | Lógica repetida en cada proceso y sin datos para Process HQ | BP 01 §11 |
| Seguridad por fila con una expresión (si la trae) | ficha del record type, `04` | Lógica de seguridad que no se hereda ni se prueba por reglas | BP 06 §5.1 |
| Filas que no todos deberían ver, sin seguridad por fila | `04`, ficha del record type | Quien ve el record type ve todas las filas | BP 06 §5.1 |

## Procesos

| Señal | Dónde se ve en as-is/ | Problema | BP |
|---|---|---|---|
| Más de 50 nodos | `datos/procesos.json` (`nodos`), `08-procesos-bpmn/`, `H-GEN` de `09` | Difícil de mantener; más memoria y más tiempo | BP 03 §1 |
| Muchas variables de proceso, o sin usar | avisos de validación (`09`, ficha `@validation`) | Memoria del motor y mantenimiento | BP 03 §3 |
| Nombre del proceso o de las tareas fijo | ficha del process model, avisos de validación | Instancias y tareas que no se distinguen | BP 03 §7 |
| CDT por referencia a un subproceso (si la trae) | ficha del process model | Instancias que se detienen al publicar el CDT | BP 03 §2 |
| Instancias múltiples (MNI) sobre un nodo que acepta listas | tabla de nodos de la ficha | Una escritura por elemento en vez de una con la lista | BP 03 §5 |
| Proceso con solo script tasks y puertas | tabla de nodos de la ficha | Un proceso donde basta una regla | BP 03 §8 |
| Mensaje sin proceso destino | ficha del process model, avisos de validación | Se revisan todas las instancias que escuchan | BP 03 §13 |
| Proceso programado muy frecuente que casi nunca tiene trabajo | `07`, `datos/procesos.json` (`ejecuciones`) | Instancias y memoria sin trabajo que hacer | BP 03 §9 |
| Procesos que repiten la misma secuencia o escriben la misma entidad igual | `08-procesos-bpmn/`, `datos/dependencias.json` | Cada cambio hay que hacerlo varias veces | BP 03 §2 |
| Sin ejecuciones o huérfano | `datos/procesos.json` (`ejecuciones: 0`), `H-ARQ` de `02`, huérfanos de `09` | Código muerto o abandonado que se mantiene igual | BP 11 §8 |
| Botón con `a!startProcess` para actuar sobre un registro | expresiones de la ficha de la interfaz, `10` | Acciones fuera del record, sin su seguridad | BP 01 §9.2 |
| Instancias completadas sin archivar (si la trae) | ficha del process model | Memoria del motor | BP 03 §9 |

## Pantallas y reglas

| Señal | Dónde se ve en as-is/ | Problema | BP |
|---|---|---|---|
| Funciones o componentes deprecados, o versiones antiguas de funciones (`_17r1`, `_22r2`…) | avisos de validación (`09`, ficha `@validation`) | Funcionalidad que Appian retirará | BP 08 §7 |
| Consultas sin paginar (`batchSize: -1`), sin `fields` o dentro de un bucle | expresiones de la ficha | Memoria y lentitud | BP 05 §2 |
| Consultas o cálculos caros en los parámetros de un componente | expresiones de la ficha | Se recalculan en cada interacción | BP 02 §1.1 |
| Interfaz de más de 80 KB o con muchas responsabilidades | `H-GEN` de `09`, ficha de la interfaz | Difícil de mantener y de probar | BP 02 §1.3 |
| Listas y paneles hechos a mano con consultas a data stores | `10`, expresiones de la ficha | Más código y sin las funcionalidades del record | BP 02 §5.3 |
| Literales de negocio repetidos (estados, umbrales, grupos) | `11` | Reglas escondidas que hay que cambiar en varios sitios | BP 04 §9 |
| Reglas duplicadas, o lógica de negocio en la interfaz | `11`, `10` | El mismo cambio en varios sitios | BP 04 §1 |
| Llamadas con varias entradas sin palabra clave | avisos de validación | Se rompen al cambiar el orden de las entradas | BP 04 §2 |
| Objetos sin el prefijo de la aplicación o fuera de la convención de nombres | `datos/inventario.json`, `INVENTARIO.md` | No se sabe de qué aplicación son | BP 08 §1 |

## Integraciones

| Señal | Dónde se ve en as-is/ | Problema | BP |
|---|---|---|---|
| `a!httpQuery`, `a!httpWrite`, smart services HTTP o conectores deprecados | expresiones de la ficha, `05` | Mecanismos deprecados | BP 07 §1 |
| Integración sin connected system, o URL completa en la integración o en una constante | `05`, ficha de la integración o de la constante | Configuración por entorno frágil | BP 07 §1 |
| Connected system sin autenticación o hacia otro entorno | `H-INT` de `05` | Riesgo de seguridad y datos cruzados entre entornos | BP 07 §2 |
| Integración sin tiempo de espera, o que modifica datos y está clasificada como consulta | ficha de la integración | Llamadas colgadas o escrituras repetidas | BP 07 §3 |
| Integración que modifica datos sin tratar el error en el proceso (si la trae) | `05`, `08-procesos-bpmn/` | Fallos que nadie ve | BP 07 §5 |
| Web API con la lógica dentro o abierta a cualquier usuario | `06` | Difícil de probar y de proteger | BP 07 §6 |

## Seguridad

| Señal | Dónde se ve en as-is/ | Problema | BP |
|---|---|---|---|
| Role maps con usuarios sueltos (si la trae) | `04` | Permisos por persona, distintos en cada entorno | BP 06 §1 |
| Objetos sin grupo de lectura, o con administradores como único grupo (si la trae) | `04` | Permisos que no siguen el modelo de grupos | BP 06 §1 |
| Secreto escrito en una constante, una expresión o una cabecera | `H-SEG` de `04`, ficha del objeto | Credenciales expuestas a quien ve el objeto | BP 06 §7 |
| Acción reservada a un rol que cualquier usuario de la aplicación puede iniciar | `04` | Cualquiera hace lo que el negocio reserva a un rol | BP 06 §5.3 |

Un role map uniforme (administradores con Administrator y usuarios con Viewer) es lo que Appian crea por defecto al
generar los grupos de la aplicación (BP 08 §2): no es un problema por sí solo. Lo es su efecto concreto en el negocio,
como la última fila.

## Oportunidades

No son problemas. Se proponen solo si resuelven una necesidad que se ve en `as-is/`.

| Necesidad que se ve | Dónde se ve en as-is/ | Qué se gana | BP |
|---|---|---|---|
| Recuentos o informes de procesos hechos a mano | `10`, `11` | Análisis de procesos con Process HQ sobre record types | BP 01 §10 |
| Clasificación o extracción de documentos a mano | `01`, `10` | AI skills y procesamiento de documentos | BP 12 §10 |
| Análisis o redacción que hace una persona con datos de la aplicación | `01` | La automatización más simple que lo resuelve, quizá un agente | BP 12 §0 |
| Web API para que un frontal externo enseñe formularios a usuarios sin cuenta | `06` | Portals | BP 06 §9 |
