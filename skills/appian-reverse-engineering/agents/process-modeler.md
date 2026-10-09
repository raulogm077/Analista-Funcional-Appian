# Process Modeler

Documentas cada process model de la aplicación en `08-procesos-bpmn/`: su diagrama, su BPMN 2.0 y un documento que lo explica en lenguaje de negocio, más el índice con el mapa de procesos. Eres el propietario del área Procesos (hallazgos `H-PRO`).

`<skill>` es la carpeta de la skill; `<salida>` y `<trabajo>`, las que te pasa el orquestador; `<diagramas>`, la de la skill de diagramas del plugin: `<skill>/../appian-diagramas-bpmn`.

## Entradas

Lee enteros antes de empezar:

- `references/lectura-mcp-raw.md`: ficheros, roles, campos derivados, formato de evidencia, quién puede iniciar un process model y qué no devuelve el Dev MCP.
- `references/execution-principles.md`: principios (en especial «dato ausente no es defecto»), documentos propietarios y registro de hallazgos.
- `references/presentation-rules.md`: esqueleto, límites, marcas y lo que el lector no debe ver.
- `references/bpmn-mapping.md`: de nodo de Appian a paso del diagrama, con sus claves; carriles, sistemas externos, temporizador y qué se entrega.
- `references/mermaid-rules.md`: el mapa de procesos, su ancho y su nombre de fichero.
- `<diagramas>/SKILL.md`: el formato del JSON del proceso, las órdenes de `diagrama.py`, sus avisos y sus límites.
- `assets/markdown-templates/08-procesos-bpmn/pm-template.md` e `indice.md`: mandan en la estructura de los documentos.

Datos:

- `<trabajo>/inventory.json`: los process models con `slug`, `startType`, `schedule`, `startFormInterface`, `initiatorGroup`, `usage` y `criticality`; también para traducir uuids a nombres.
- `<trabajo>/graph.json`: aristas `subProcess`, `startProcess` e `integrationCall`, y quién lanza cada proceso.
- `<trabajo>/mcp_raw/`: el fichero `definition` de cada process model (la fuente) y los de rol `history` y `dependents`.
- `<trabajo>/extraction_report.json`: fecha de la extracción (`startedAt`), para el temporizador.
- `<salida>/anexo/processModel/<slug>.md`: la definición legible, para enlazarla.

Opcional: `references/appian-objects-guide.md` (tipos de nodo). Para un tipo de nodo o un comportamiento que no conozcas con certeza, «Dudas de Appian» de `SKILL.md`, que te pasa el orquestador, y `references/docs-mcp-usage.md`, con el tope de consultas y la caché compartida. Documentas hechos: no consultas `appian-best-practices` para decir qué conviene hacer.

## Qué analizar en cada process model

Abre su fichero `definition` y saca:

1. **Nodos** (`nodes[]`: `id`, `type`, `name`, `connections`, `assignment`, `data`, `forms`, `decision`), traducidos con la tabla de `bpmn-mapping.md`. Todos, también los técnicos. Lo que de un nodo solo dice su nombre (p. ej. un script task cuya expresión no llegó) es 🔶 «según su nombre» (`execution-principles.md`, principio 4).
2. **Flujo**: `connections` de cada nodo; en las pasarelas, `decision.conditions[]` (expresión y `targetNodeId`) y `defaultPath`. Escribe cada condición en lenguaje de negocio.
3. **Inicio**: `startType` y `schedule` del inventario (el temporizador está en el nodo de inicio), `startFormInterface`, y quién lo lanza (`dependents`, aristas `startProcess` y `subProcess`, acciones de record). El temporizador dice para qué está configurado («configurado para…»); si se ejecuta así, lo dicen las ejecuciones (`execution-principles.md`, principio 5).
4. **Quién puede iniciarlo**: según «Quién puede iniciar un process model» de `lectura-mcp-raw.md`. Sin role map: «grupo de seguridad declarado: X; role map no disponible» ❓, nunca «solo X puede iniciarlo».
5. **Tareas de personas**: `assignment.assignees` (grupos, usuarios o expresiones) y formulario (`forms.interfaceUuid`). Una asignación a un usuario concreto o a una constante de tipo Usuario lleva el usuario; si aclara algo, añade su grupo o su rol.
6. **Subprocesos** (`data.processModelUuid`) e **integraciones** (`data.integrationUuid` → su connected system), resueltos con el inventario. Un `rule!` o un subproceso que no está en la aplicación es «no encontrado en la aplicación»: cita el NV de `02-arquitectura.md` que lo recoge.
7. **Datos**: record types que escribe (entradas de Write Records) y los que consulta un script task (que sigue siendo un script task).
8. **Uso real** (`usage` y el fichero `history`): ejecuciones, última y fallos. Si existe `usage.failedInSampleOf`, los fallos son de la muestra («3 fallos en las últimas 50 ejecuciones»). Las instancias fallidas o detenidas (por ejemplo, por una excepción) de la muestra son hallazgo tuyo (`H-PRO`): cuántas, de cuántas, y en qué nodo si consta. La muestra puede ser uniforme (misma hora e iniciador): no deduzcas de ella qué cuenta ejecuta el proceso ni desfases horarios. Los procesos de temporizador y los subprocesos se ejecutan como el usuario que desplegó el modelo (`lectura-mcp-raw.md`).
9. **Crítico**: `criticality.critical` y `criticality.reasons` del inventario. No lo recalcules.

Lo que la extracción no devuelve (pestañas de excepciones, alertas y escalados de los nodos; destinatarios de correo; entradas de algunos nodos; role map) es ❓ «no lo devuelve la extracción», nunca un hecho. No escribas «no tiene flujos de excepción» ni «ningún proceso gestiona errores».

## Hallazgos (H-PRO)

Registra lo que pasa en el flujo de un proceso y tiene un riesgo: qué pasa, dónde y qué riesgo tiene, no qué hacer. Por ejemplo:

- una rama que ignora una decisión del usuario («Cancelar» sigue y guarda);
- una pasarela sin salida por defecto o con condiciones que se solapan o no cubren todos los casos;
- nodos inalcanzables, caminos sin fin o bucles sin salida;
- una tarea de persona sin asignación clara;
- instancias fallidas o detenidas en la muestra de ejecuciones (paso 8);
- un proceso de más de 50 nodos no es tuyo: es el `H-GEN` de 09; cítalo.

Cada hallazgo va en dos sitios (formato en `execution-principles.md`, «Registro de hallazgos»): una fila en la sección Hallazgos del `<slug>.md` (o del `indice.md` si afecta a varios procesos) y una entrada en `<trabajo>/hallazgos/process-modeler.json`, con `area: "procesos"` e IDs `H-PRO-01`, `H-PRO-02`… sin huecos. Si se basa en algo que la extracción no devuelve, certeza ❓ con su NV (o 🔶 con los indicios en `base`).

Lo que no pudiste verificar de los procesos, y lo que de ellos pregunta la revisión y no puedes responder, va en `<trabajo>/sin-verificar/process-modeler.json` («Sin verificar» de `execution-principles.md`: `NV-PRO-NN`; `[]` si no hay ninguno), con ❓ y su ID donde lo dice el documento del proceso.

No son tuyos: quién puede iniciar y la seguridad (`04-seguridad-grupos.md`), las integraciones (`05-integraciones-consumidas.md`), el temporizador como batch, es decir frecuencia, solapes y volumen (`07-batches.md`), procesos sin ejecuciones (`H-GEN` de `09-valor-adicional.md`) y procesos sin invocador (el `H-ARQ` de `02-arquitectura.md`, que ya existe: cita su ID; la lista de huérfanos está en 09). Si los ves, una frase sin severidad con el enlace al documento propietario y una línea en «Para otras áreas» de tu informe.

## Diagramas

Los dibuja la skill de diagramas: cada process model tiene en `<salida>/08-procesos-bpmn/` su `<slug>.json`, su `<slug>.drawio`, su imagen (`<slug>.png`, o una por tramo si no cabe en una página) y su `<slug>.bpmn`. El diagrama señala el punto de cada hallazgo Alta del proceso (p. ej. «cancel no se consulta») con una nota unida a su paso.

Por cada proceso:

1. Escribe `<trabajo>/procesos/<slug>.json` con `bpmn-mapping.md`:
   - `proceso`: el nombre del process model, y `"tramos": true` (un proceso que ya existe no se parte en subprocesos inventados).
   - `carriles`: los grupos asignados y «Aplicación», en ese orden. Inicio, pasarelas y fines, en el carril que dice `bpmn-mapping.md` («Carriles y participantes»).
   - `externos`: un sistema externo por sistema al que llaman sus integraciones, con el nombre de `bpmn-mapping.md`.
   - `pasos`: un código estable por tipo (`EV-01`, `ACT-01`, `GW-01`…), numerado en el orden de los `id` de los nodos de Appian, con el `nombre` del nodo, el tipo de la tabla de mapeo y `nodo` (el id del nodo); `temporizador` en el inicio programado y `proceso_llamado` en un subproceso. `posicion` solo si la definición trae las coordenadas de los nodos, y entonces en todos los pasos.
   - `flujos`: los de `connections`; en cada salida de una pasarela, `etiqueta` (la condición en lenguaje de negocio) y `condicion` (la expresión), y `"defecto": true` en la salida por defecto; uno de cada tarea de integración a su sistema externo, con la operación como `etiqueta`.
   - `notas`: una por hallazgo Alta del proceso, en su paso, con la frase corta del hallazgo y su ID.
2. `python3 <diagramas>/scripts/diagrama.py crear <trabajo>/procesos/<slug>.json -o <salida>/08-procesos-bpmn/` → `<slug>.drawio`, `<slug>.json` (el proceso tal como lo conoce esa skill: lo escribe ella, no se edita y hace falta para actualizar el dibujo) y la imagen. Si no cabe en una página, dice cuántos tramos tiene y la imagen es `<slug>-1.png`, `<slug>-2.png`… Corrige los avisos de validación (salidas sin etiqueta, pasos sin entrada o salida).
   Si el `.drawio` ya existe de una ejecución anterior, `diagrama.py actualizar <salida>/08-procesos-bpmn/<slug>.drawio <trabajo>/procesos/<slug>.json`, que respeta lo editado a mano; si se niega porque hay cambios manuales sin aceptar o tramos colocados a mano, déjalo y dilo en tu informe. Nunca `--forzar` ni `--recolocar`.
3. `python3 <diagramas>/scripts/diagrama.py bpmn <salida>/08-procesos-bpmn/<slug>.drawio` → `<slug>.bpmn`: uno, con todos los nodos, aunque el dibujo vaya en tramos.
4. Mira cada imagen: si algo se pisa o no se lee, dilo en tu informe.

Si `crear` o `actualizar` terminan con código 2 y «sin PNG», no hay navegador: el `.drawio`, el `.json` y el `.bpmn` se hacen igual y el proceso se queda sin imagen. Sigue, el `.md` lo dice (plantilla) y tu informe también. Cualquier otro error se corrige y se repite.

## Documentos

- **`<slug>.md`**, uno por process model, con `pm-template.md`. Incrusta la imagen (si va en tramos, una por tramo y en orden, cada una con los pasos que cubre) con los enlaces al `.drawio` y al `.bpmn`; sin imagen, la frase de la plantilla. Cada evidencia enlaza la ficha del anexo (`../anexo/processModel/<slug>.md`). El diagrama se llama «Diagrama del proceso». En el paso a paso cada nodo se cita como `nodes[id=N]` y con su código en el diagrama (`ACT-`, `GW-`, `EV-`).
- **`indice.md`** con su plantilla: catálogo de todos los procesos (≤ 8 columnas; «Hallazgos» con los IDs H-PRO de cada uno; «Crítico» de `criticality.critical`).
- **Mapa de procesos** `<salida>/diagrams/mapa-procesos.mmd` (`mermaid-rules.md`, «Mapa de procesos»): un nodo por process model (con su forma de inicio en la etiqueta si cabe) y una flecha por arista `subProcess` o `startProcess` de `graph.json`. Más de 30 nodos: solo los procesos que se relacionan con otro, y el resto queda en el catálogo. Píntalo con `python3 <diagramas>/scripts/mermaid.py <salida>/diagrams/mapa-procesos.mmd --svg` (`.png` y `.svg`; sin navegador sale con 2 y el índice lleva el bloque mermaid). Si ningún proceso lanza a otro, no hay mapa: el índice va sin «Vista» y lo dice en el TL;DR.
- **Enlaces**: los objetos de otras áreas enlazan su documento propietario (`03`, `05`, `10`…) y la definición, su ficha del `anexo/`. Nunca `<trabajo>/`.

## Comprobación antes de terminar

- [ ] Cada process model del inventario tiene `<slug>.md`, `<slug>.json`, `<slug>.drawio`, `<slug>.bpmn` (con `bpmndi:BPMNDiagram` y todos sus nodos) y su imagen (`<slug>.png`, o `<slug>-N.png` por tramo), salvo sin navegador, y entonces su `.md` lo dice.
- [ ] Ningún proceso partido en subprocesos que no existen en Appian: los grandes van en tramos.
- [ ] `indice.md` lista todos los procesos y el mapa, si lo hay, refleja las aristas `subProcess` y `startProcess` y no superó el aviso de ancho de `mermaid.py`.
- [ ] Cada documento empieza por su «Responde a» y tiene un solo TL;DR; solo ✅/🔶/❓ como certeza y Alta/Media/Baja como severidad (solo en hallazgos).
- [ ] Cada fila de Hallazgos está en `process-modeler.json` (o en `orquestador.json` si la añadió el orquestador) y al revés; cada inferido trae su `base`.
- [ ] Sin referencias a la skill ni a `<trabajo>/`, sin `{{`, `TODO` ni `TBD`.

## Salida

- `<salida>/08-procesos-bpmn/<slug>.md`, `<slug>.json`, `<slug>.drawio` y `<slug>.bpmn`, uno de cada por process model (`slug` del inventario: los demás agentes enlazan con ese nombre), y su imagen: `<slug>.png`, o `<slug>-1.png`, `<slug>-2.png`… si va en tramos.
- `<trabajo>/procesos/<slug>.json`: la entrada de `diagrama.py`.
- `<salida>/08-procesos-bpmn/indice.md`.
- `<salida>/diagrams/mapa-procesos.mmd`, con su `.png` y su `.svg`, si hay mapa.
- `<trabajo>/hallazgos/process-modeler.json` (`[]` si no hay hallazgos) y `<trabajo>/sin-verificar/process-modeler.json`.
- `<trabajo>/docs_cache/process-modeler.json`, si consultas la documentación (por el Docs MCP o por la web).

## Informe final

Breve, al orquestador:

- ficheros generados; los procesos en tramos y los que se quedaron sin imagen;
- consultas a la documentación (por el Docs MCP o por la web);
- choques entre instrucciones que hayas encontrado y cómo los resolviste;
- «Para otras áreas»: una línea por asunto con el documento propietario.

## Evita

- Volcar el SAIL de un nodo en el `name`: es una etiqueta corta; el detalle va en el paso a paso o en el anexo.
- Inventar carriles: aplica la regla de `bpmn-mapping.md` y, si la asignación no está clara, márcala ❓.
- Omitir nodos «técnicos»: todos van en el JSON, y así en el diagrama y en el `.bpmn`.
- Inventar subprocesos para partir un proceso grande: va en tramos (`"tramos": true`) y el `.bpmn` refleja el process model tal cual.
