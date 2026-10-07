# Mapeo Appian → BPMN 2.0

Cómo traducir un process model de Appian a BPMN 2.0 y a su diagrama. Lo usa process-modeler para `08-procesos-bpmn/`. La estructura de cada `<slug>.md` la da `assets/markdown-templates/08-procesos-bpmn/pm-template.md` y la del índice, `indice.md` en esa misma carpeta; el diagrama Mermaid, `references/mermaid-rules.md`.

---

## Qué se entrega por proceso

| Vía | Ficheros en `08-procesos-bpmn/` | Imagen del `.md` |
|---|---|---|
| Propia (por defecto) | `<slug>.bpmn`, `<slug>.mmd`, `<slug>.svg`, `<slug>.md` | `<slug>.svg`; sin render, el bloque mermaid |
| draw.io (si el orquestador pasa la skill `appian-diagramas-bpmn`) | `<slug>.drawio`, `<slug>.png`, `<slug>.json`, `<slug>.md`, y el `<slug>.bpmn` de la vía propia | `<slug>.png` |

`<slug>` es el del process model en `inventory.json`. Cómo se recorre cada vía, en `agents/process-modeler.md`.

**Procesos de más de 25 nodos** (vía propia): el diagrama Mermaid se parte en tramos del flujo, `<slug>-1.mmd`, `<slug>-2.mmd`… (con su `.svg`), y el `.md` los muestra en orden, cada uno con una frase que dice qué pasos cubre; el `.bpmn` sigue siendo uno y completo. No inventes subprocesos para partirlo.

El `.bpmn` es BPMN 2.0 estándar con coordenadas de dibujo (BPMN DI). Se abre en **Camunda Modeler** (Archivo → Abrir) y en **bpmn.io** (arrastrar el fichero a https://demo.bpmn.io). Estas herramientas no calculan el dibujo: sin DI no muestran nada. Por eso el agente escribe el XML semántico y `<skill>/scripts/bpmn_layout.py` añade el resto. Es así también cuando la imagen se dibuja en draw.io: el `.bpmn` sale siempre de aquí, porque lleva datos de Appian que el dibujo no tiene (la expresión del temporizador, el proceso llamado, las condiciones de las pasarelas y el id de cada nodo).

---

## Tabla de mapeo

`type` es el id de esquema del nodo en la definición extraída. El inicio programado o por mensaje se distingue por `startType` del inventario.

| `type` | Nodo Appian | BPMN 2.0 | Mermaid | JSON draw.io |
|---|---|---|---|---|
| `core.0` | Inicio | `startEvent` | `Start1((Inicio)):::startNode` | `inicio` (EV) |
| `core.0`, `startType: timer` | Inicio programado | `startEvent` + `timerEventDefinition` (ver «Temporizador») | `Start1((⏰ Inicio)):::startNode` | `inicio_temporizador`, con la frecuencia en el nombre |
| `core.0`, `startType: message` | Inicio por mensaje | `startEvent` + `messageEventDefinition` | `Start1((✉ Inicio)):::startNode` | `inicio_mensaje` |
| `core.1` | Fin | `endEvent` (+ `terminateEventDefinition` si la configuración lo indica) | `End5(((Fin))):::endNode` o `:::endNodeTerm` | `fin` (EV) |
| `core.4` | Pasarela exclusiva (XOR) | `exclusiveGateway` | `G3{¿Aprobada?}:::gateway` | `exclusiva` (GW) |
| `internal.16` | Script task | `scriptTask` (también si consulta datos) | `T2[📜 …]:::scriptTask` | `script` (ACT) |
| `internal.17` | User input task | `userTask` | `T2[👤 …]:::userTask` | `tarea` (ACT) |
| `internal3.write_records_to_source_23r3` | Write Records | `serviceTask` «[Records] …» | `T2[📋 …]:::dataTask` | `sistema` (ACT) |
| `internal3.sendemail3` | Send E-Mail | `sendTask` | `T2[📧 …]:::sendTask` | `mensaje` (EV) |
| `internal3.integration` | Call Integration | `serviceTask` «[Integración] …» + `messageFlow` al sistema externo | `T2[🔌 …]:::serviceTask` | `sistema` (ACT), en «Sistema», + flujo al sistema externo de `externos` |
| `internal3.subprocess` | Subproceso | `callActivity`, `calledElement` = id del proceso llamado | `S2[➡️ …]:::callActivity` | `llamada` (ACT) |
| (ver catálogo) | Pasarela paralela / inclusiva | `parallelGateway` / `inclusiveGateway` | `G3{+}` / `G3{O}`, `:::gateway` | `paralela` / `inclusiva` (GW) |
| (ver catálogo) | Write to Data Store Entity | `serviceTask` «[Data store] …» | `T2[💾 …]:::dataTask` | `sistema` (ACT) |

**Tipos que no están en la tabla.** Búscalos en el catálogo de tipos de nodo de `<trabajo>/mcp_raw/_env/` o en el Docs MCP y usa el elemento BPMN equivalente: un smart service desatendido es `serviceTask` «[<smart service>] …»; una tarea de una persona, `userTask`. Si no consigues identificarlo, `task` con el nombre del nodo y ❓ en el paso a paso.

**Excepciones y alertas.** La extracción no devuelve las pestañas de excepciones, alertas ni escalados de los nodos. No los dibujes ni digas que no existen: es ❓ «no lo devuelve la extracción». Solo si la definición trae un flujo de excepción explícito, dibújalo como `boundaryEvent` adjunto a la actividad (`errorEventDefinition`, o `timerEventDefinition` si es un plazo) y en Mermaid como `T2 -.->|"excepción"| H1`.

---

## Carriles y participantes

Igual en las dos vías:

- **Un carril por grupo** asignado a tareas de personas (`assignment.assignees` de tipo grupo), con el nombre del grupo.
- **Asignaciones que no son un grupo**: al iniciador del proceso → carril «Iniciador»; a una expresión o regla → el rol que se deduzca de ella (🔵) o «Asignación por expresión» (❓); a un usuario concreto o a una constante de tipo Usuario → «Cuenta de ‹grupo›» si se conoce su grupo o «Cuenta personal», nunca su nombre.
- **«Sistema»** para todo lo desatendido: scripts, escritura de records, integraciones, correos y subprocesos.
- El **inicio** va en el carril del primer nodo; si el proceso arranca con un formulario de inicio, en el carril de quien lo rellena («Iniciador», o el grupo si solo puede iniciarlo uno). Cada **pasarela** y cada **fin**, en el carril del nodo que tienen antes; si tienen varios en carriles distintos, en «Sistema».
- Orden: los grupos según aparecen en el flujo y «Sistema» al final.

Sistemas externos (uno por connected system de las integraciones que llama el proceso):

- **Vía propia**: un `participant` sin `processRef` (pool caja negra) llamado `<sistema> (<connected system>)`, y un `messageFlow` desde la tarea de integración hasta él con la operación como `name`. Con participantes externos, el `.bpmn` lleva `collaboration` con un `participant` para el proceso (`processRef`) más los externos.
- **Vía draw.io**: el sistema externo va en `externos` con el mismo nombre, y un flujo desde la tarea de integración hasta él (flujo de mensaje) con la operación como `etiqueta`. Si la versión instalada de esa skill no admite `externos` (`validar` lo rechaza), la tarea de integración nombra el sistema externo y se explica en el `.md`.
- **Diagrama Mermaid**: un `subgraph` con un solo nodo `:::external` y flecha discontinua desde la tarea de integración (ver `mermaid-rules.md`).

Si el único carril sería «Sistema», el `.bpmn` va sin `laneSet` y el Mermaid sin `subgraph` para él; con sistemas externos, el `.bpmn` lleva igualmente `collaboration` con sus participantes.

---

## Temporizador

Inicio programado (`startType: timer`; la configuración está en el nodo de inicio y en `schedule` del inventario):

```xml
<bpmn:startEvent id="Start_1" name="Cada día 08:00">
  <bpmn:documentation>Diario a las 08:00 (Europe/Madrid)</bpmn:documentation>
  <bpmn:timerEventDefinition id="Timer_1">
    <bpmn:timeCycle xsi:type="bpmn:tFormalExpression">R/2026-10-05T08:00:00+02:00/P1D</bpmn:timeCycle>
  </bpmn:timerEventDefinition>
</bpmn:startEvent>
```

- `timeCycle` = `R/<inicio>/<periodo>` (repetición ISO 8601).
  - `<inicio>`: la fecha de inicio de la configuración o, si no la trae, la de la extracción (`startedAt` de `<trabajo>/extraction_report.json`), con la hora del temporizador y el desfase UTC de su zona en esa fecha (`+02:00` para Europe/Madrid en verano).
  - `<periodo>`: `P1D` diario, `P1W` semanal, `P1M` mensual, `PT1H` cada hora, `PT<n>M` cada n minutos.
- La frecuencia legible, con la zona por su nombre, va en `documentation`: ISO 8601 solo guarda el desfase.
- Si la configuración no trae la hora o la zona, no las inventes: `R/<periodo>` y en `documentation` «hora no devuelta por la extracción».
- Si la recurrencia no cabe en un periodo (p. ej. solo días laborables), usa el periodo base y explica la regla en `documentation`.

---

## Plantilla del `.bpmn` semántico (vía propia)

Es lo que escribe el agente: sin `<bpmndi:BPMNDiagram>` ni `incoming`/`outgoing`, que añade `bpmn_layout.py`. Ejemplo con un carril de grupo, «Sistema» y un sistema externo:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                  id="Definitions_DEM_Alta_Solicitud"
                  targetNamespace="http://bpmn.io/schema/bpmn">

  <bpmn:collaboration id="Collaboration_1">
    <bpmn:participant id="Participant_Proceso" name="DEM Alta Solicitud" processRef="Process_DEM_Alta_Solicitud"/>
    <bpmn:participant id="Participant_ERP" name="ERP (DEM_CS_ERP)"/>
    <bpmn:messageFlow id="MF_5" name="Crear expediente" sourceRef="Task_5" targetRef="Participant_ERP"/>
  </bpmn:collaboration>

  <bpmn:process id="Process_DEM_Alta_Solicitud" name="DEM Alta Solicitud" isExecutable="false">
    <bpmn:laneSet id="LaneSet_1">
      <bpmn:lane id="Lane_DEM_Revisores" name="DEM Revisores">
        <bpmn:flowNodeRef>Start_1</bpmn:flowNodeRef>
        <bpmn:flowNodeRef>Task_2</bpmn:flowNodeRef>
        <bpmn:flowNodeRef>Gateway_3</bpmn:flowNodeRef>
        <bpmn:flowNodeRef>End_7</bpmn:flowNodeRef>
      </bpmn:lane>
      <bpmn:lane id="Lane_Sistema" name="Sistema">
        <bpmn:flowNodeRef>Task_4</bpmn:flowNodeRef>
        <bpmn:flowNodeRef>Task_5</bpmn:flowNodeRef>
        <bpmn:flowNodeRef>Task_6</bpmn:flowNodeRef>
        <bpmn:flowNodeRef>End_8</bpmn:flowNodeRef>
      </bpmn:lane>
    </bpmn:laneSet>

    <bpmn:startEvent id="Start_1" name="Inicio"/>
    <bpmn:userTask id="Task_2" name="Revisar solicitud"/>
    <bpmn:exclusiveGateway id="Gateway_3" name="¿Aprobada?" default="F_3_7"/>
    <bpmn:serviceTask id="Task_4" name="[Records] Guardar solicitud"/>
    <bpmn:serviceTask id="Task_5" name="[Integración] Notificar ERP"/>
    <bpmn:sendTask id="Task_6" name="Avisar solicitante"/>
    <bpmn:endEvent id="End_7" name="Rechazada"/>
    <bpmn:endEvent id="End_8" name="Fin"/>

    <bpmn:sequenceFlow id="F_1_2" sourceRef="Start_1" targetRef="Task_2"/>
    <bpmn:sequenceFlow id="F_2_3" sourceRef="Task_2" targetRef="Gateway_3"/>
    <bpmn:sequenceFlow id="F_3_4" name="Aprobar" sourceRef="Gateway_3" targetRef="Task_4">
      <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">pv!decision = "Aprobar"</bpmn:conditionExpression>
    </bpmn:sequenceFlow>
    <bpmn:sequenceFlow id="F_3_7" name="En otro caso" sourceRef="Gateway_3" targetRef="End_7"/>
    <bpmn:sequenceFlow id="F_4_5" sourceRef="Task_4" targetRef="Task_5"/>
    <bpmn:sequenceFlow id="F_5_6" sourceRef="Task_5" targetRef="Task_6"/>
    <bpmn:sequenceFlow id="F_6_8" sourceRef="Task_6" targetRef="End_8"/>
  </bpmn:process>
</bpmn:definitions>
```

Reglas:

- **Ids** sin espacios, guiones ni tildes, con el id del nodo Appian para rastrear cada elemento hasta `nodes[id=N]`: `Start_1`, `Task_2`, `Gateway_3`, `Call_4`, `End_7`; flujos `F_<origen>_<destino>`; carriles `Lane_<grupo>`. El proceso es `Process_<slug>` y el `calledElement` de un subproceso, `Process_<slug del hijo>`.
- **`name`**: el nombre visible del nodo, nunca su SAIL. Escapa `&lt;`, `&gt;`, `&amp;` y `&quot;`.
- **Pasarelas**: cada salida con `name` = la condición en lenguaje de negocio y la expresión de `decision.conditions[]` en `conditionExpression` (escapada); `defaultPath` es el atributo `default` de la pasarela.
- **Todos los nodos** del process model, también los técnicos. Cada nodo en exactamente un carril (si hay `laneSet`).
- `sourceRef` y `targetRef` apuntan a ids que existen.

Después:

1. `xmllint --noout <slug>.bpmn`, si está disponible.
2. `python3 <skill>/scripts/bpmn_layout.py <salida>/08-procesos-bpmn` (o un fichero concreto). Completa `incoming`/`outgoing`, crea la colaboración y el pool si hay carriles sin ellos, dibuja de izquierda a derecha con un carril por lane y los sistemas externos como pools debajo, y escribe el `<bpmndi:BPMNDiagram>`. Se puede repetir: sustituye el DI anterior.
3. Cada `.bpmn` tiene `bpmndi:BPMNDiagram`.
