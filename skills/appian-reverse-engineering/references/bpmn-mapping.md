# Mapeo Appian → diagrama y BPMN 2.0

Cómo traducir un process model de Appian al proceso que dibuja la skill de diagramas (`appian-diagramas-bpmn`, la de este mismo plugin: `<diagramas>` = `<skill>/../appian-diagramas-bpmn`). Ella dibuja el `.drawio` y su imagen y exporta el `.bpmn`; aquí se decide qué lleva el proceso. Lo usa process-modeler para `08-procesos-bpmn/`. La estructura de cada `<slug>.md` la da `assets/markdown-templates/08-procesos-bpmn/pm-template.md` y la del índice, `indice.md` en esa misma carpeta. El formato del JSON, sus órdenes y sus límites están en el `SKILL.md` de la skill de diagramas.

---

## Qué se entrega por proceso

En `08-procesos-bpmn/`, con el `<slug>` del process model en `inventory.json`:

| Fichero | Qué es |
|---|---|
| `<slug>.json` | El proceso en el formato de la skill de diagramas. Lo escribe `diagrama.py` y lo mantiene; lo leen las demás skills (`datos/procesos.json`) |
| `<slug>.drawio` | El diagrama, editable en draw.io |
| `<slug>.png` | La imagen del documento. Si el proceso va en tramos, una por tramo: `<slug>-1.png`, `<slug>-2.png`… Sin navegador no hay imagen |
| `<slug>.bpmn` | BPMN 2.0 con coordenadas de dibujo, uno con todos los nodos |
| `<slug>.md` | El documento del proceso |

**Procesos grandes.** El JSON lleva siempre `"tramos": true`: es un proceso que ya existe y no se le inventan subprocesos. Si no cabe en una página, la skill de diagramas lo dibuja en tramos de una página unidos por eventos de enlace («Sigue en el tramo N», «Viene del tramo M»), que son del dibujo y no del proceso. El `.bpmn` sigue siendo uno y completo, sin los enlaces. El `.md` muestra las imágenes en orden, cada una con una frase que dice qué pasos cubre.

**El `.bpmn`** lo exporta `diagrama.py bpmn` del `.drawio`: un participante para el proceso con un carril por carril, los sistemas externos como participantes caja negra con sus flujos de mensaje, los tipos de inicio y de tarea, el flujo por defecto, los eventos de borde y los datos de Appian (el id del nodo en `documentation`, la condición de cada salida, la expresión del temporizador y el proceso llamado). Se abre en **Camunda Modeler** (Archivo → Abrir) y en **bpmn.io** (arrastrar el fichero a https://demo.bpmn.io).

---

## Tabla de mapeo

`type` es el id de esquema del nodo en la definición extraída. El inicio programado o por mensaje se distingue por `startType` del inventario.

| `type` | Nodo Appian | Tipo de paso (código) | Datos de Appian y flujos |
|---|---|---|---|
| `core.0` | Inicio | `inicio` (EV) | `nodo` |
| `core.0`, `startType: timer` | Inicio programado | `inicio_temporizador` (EV), con la frecuencia en el nombre | `nodo`, `temporizador` (ver «Temporizador») |
| `core.0`, `startType: message` | Inicio por mensaje | `inicio_mensaje` (EV) | `nodo` |
| `core.1` | Fin | `fin` (EV); si la configuración dice que termina todo el proceso, el nombre lo dice | `nodo` |
| `core.4` | Pasarela exclusiva (XOR) | `exclusiva` (GW) | `nodo`; en cada salida, `etiqueta` y `condicion`; `defaultPath`, `"defecto": true` |
| `internal.16` | Script task | `script` (ACT), también si consulta datos | `nodo` |
| `internal.17` | User input task | `tarea` (ACT) | `nodo` |
| `internal3.write_records_to_source_23r3` | Write Records | `sistema` (ACT) | `nodo` |
| `internal3.sendemail3` | Send E-Mail | `mensaje` (EV), en «Aplicación» | `nodo` |
| `internal3.integration` | Call Integration | `sistema` (ACT), en «Aplicación» | `nodo`; un flujo hasta su sistema externo con la operación como `etiqueta` |
| `internal3.subprocess` | Subproceso | `llamada` (ACT) | `nodo`, `proceso_llamado` (el nombre del process model hijo) |
| (ver catálogo) | Pasarela paralela / inclusiva | `paralela` / `inclusiva` (GW) | `nodo`; en las inclusivas, como en las exclusivas |
| (ver catálogo) | Write to Data Store Entity | `sistema` (ACT) | `nodo` |

- **Códigos:** uno por tipo (`EV-01`, `ACT-01`, `GW-01`…), numerados en el orden de los `id` de los nodos de Appian. `nodo` es ese id, como texto.
- **`nombre`:** el nombre visible del nodo, nunca su SAIL. En una salida de pasarela, `etiqueta` es la condición en lenguaje de negocio (la salida por defecto, «En otro caso») y `condicion`, la expresión de `decision.conditions[]` tal cual.
- **Todos los nodos** del process model, también los técnicos, cada uno en un carril.

**Tipos que no están en la tabla.** Búscalos en el catálogo de tipos de nodo de `<trabajo>/mcp_raw/_env/` o en el Docs MCP y usa el tipo de paso equivalente: un smart service desatendido es `sistema`; una tarea de una persona, `tarea`. Si no consigues identificarlo, `sistema` (o `tarea` si lo atiende una persona) con el nombre del nodo y ❓ en el paso a paso.

**Excepciones y alertas.** La extracción no devuelve las pestañas de excepciones, alertas ni escalados de los nodos. No los dibujes ni digas que no existen: es ❓ «no lo devuelve la extracción». Solo si la definición trae un flujo de excepción explícito, dibújalo: un `error` unido a su tarea con un flujo discontinuo, y de él, el camino que sigue (en el BPMN, un evento de borde que la interrumpe); si es un plazo, un `temporizador` unido igual (no la interrumpe).

---

## Carriles y participantes

- **Un carril por grupo** asignado a tareas de personas (`assignment.assignees` de tipo grupo), con el nombre del grupo.
- **Asignaciones que no son un grupo**: al iniciador del proceso → carril «Iniciador»; a una expresión o regla → el rol que se deduzca de ella (🔶) o «Asignación por expresión» (❓); a un usuario concreto o a una constante de tipo Usuario → un carril con el usuario o, si aclara más, con su grupo.
- **«Aplicación»** para todo lo desatendido: scripts, escritura de records, integraciones, correos y subprocesos.
- El **inicio** va en el carril del primer nodo; si el proceso arranca con un formulario de inicio, en el carril de quien lo rellena («Iniciador», o el grupo si solo puede iniciarlo uno). Cada **pasarela** y cada **fin**, en el carril del nodo que tienen antes; si tienen varios en carriles distintos, en «Aplicación».
- Orden: los grupos según aparecen en el flujo y «Aplicación» al final.

**Sistemas externos** (en `externos`), uno por sistema al que llaman las integraciones del proceso:

- **Con connected system:** `<sistema> (<connected system>)`, p. ej. «ERP (DEM_CS_ERP)».
- **Sin connected system** (la URL va en la propia integración, «Enter connection details below», o en una constante que esta lee): el sistema al que apunta su URL, `<sistema> (<integración>)`, p. ej. «ERP (DEM_INT_ConsultarERP)». `<sistema>` sale del host de la URL, con la constante resuelta si la URL la toma de una (`cons!DEM_URL_ERP` = `https://erp.example.org/api` → «ERP»); si el host no dice qué sistema es, va el host tal cual. Si varias integraciones sin connected system llaman al mismo host, un solo participante, con el host entre paréntesis: «ERP (erp.example.org)». Que no use connected system es de `05-integraciones-consumidas.md`, no de este documento. Fuente: https://docs.appian.com/suite/help/latest/Integration_Object.html#integration-definition
- Un flujo desde la tarea de integración hasta su sistema externo (flujo de mensaje) con la operación como `etiqueta`.

---

## Temporizador

Inicio programado (`startType: timer`; la configuración está en el nodo de inicio y en `schedule` del inventario): un paso `inicio_temporizador` con la frecuencia legible en el `nombre`, con la zona por su nombre si la trae («Cada día a las 08:00 (Europe/Madrid)»), y la repetición en `temporizador`:

```json
{"id": "EV-01", "tipo": "inicio_temporizador", "carril": "Aplicación", "nombre": "Cada día a las 08:00 (Europe/Madrid)", "nodo": "1", "temporizador": "R/2026-10-05T08:00:00+02:00/P1D"}
```

- `temporizador` = `R/<inicio>/<periodo>` (repetición ISO 8601). En el BPMN va en `timeCycle`.
  - `<inicio>`: la fecha de inicio de la configuración o, si no la trae, la de la extracción (`startedAt` de `<trabajo>/extraction_report.json`), con la hora del temporizador y el desfase UTC de su zona en esa fecha (`+02:00` para Europe/Madrid en verano).
  - `<periodo>`: `P1D` diario, `P1W` semanal, `P1M` mensual, `PT1H` cada hora, `PT<n>M` cada n minutos.
- Si la configuración no trae la hora o la zona, no las inventes: `R/<periodo>` y el nombre dice «hora no devuelta por la extracción».
- Si la recurrencia no cabe en un periodo (p. ej. solo días laborables), usa el periodo base y explica la regla en el paso a paso del `.md`.
