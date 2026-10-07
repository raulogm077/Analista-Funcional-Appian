# Flujo completo: de cualquier punto de partida a la aplicación construida

> Propuesta trabajada con Raúl el 2026-10-07 en el hilo «Flujo de trabajo Appian». Decidido: el flujo llega
> hasta construir en Appian con IA, y construir va en una skill (o skills) propia, no dentro de buenas prácticas.
> Después se importó lo que ya estaba decidido en otros hilos (abajo, «Lo que ya existe»), y Raúl decidió que el
> método de construcción vive en el plugin, generalizado; cada proyecto pone solo lo suyo (`docs/appian.md`). Lo
> marcado como **abierto** está sin cerrar.

## El flujo

Tres entradas y un mismo camino. Lo que se construye sale del análisis; la construcción la hace un equipo de agentes
con papel fijo.

| Fase | Qué se hace | Quién | Sale |
|---|---|---|---|
| 0 · Punto de partida | App nueva: reuniones, correos, DF del cliente | Analista | `fuentes/` |
| | App existente que se amplía | Ingeniería inversa → analista | `as-is/` |
| | App legacy que se rehace (toda o una parte) | Ingeniería inversa → refactorización → analista | `as-is/`, `refactorizacion/propuesta.md` |
| 1 · Especificar | Funcional que valida el cliente y técnico para construir; procesos en BPMN | Analista, diagramas | `analisis/funcional.md`, DF en Word, `analisis/tecnico.md` |
| 2 · Validar con el cliente | Prototipo navegable; su feedback vuelve al analista como fuente | Prototipos → analista | `prototipo/` |
| 3 · Épicas y tareas | El técnico se parte en épicas (un recorrido de usuario cada una) y tareas, con sus objetos declarados | Jefe técnico (Claude Code) | Especificación de cada épica, tablero |
| 4 · Construir | Cada tarea por el Dev MCP, con la skill oficial `appian`, verificada según el tipo de cambio | Constructores (Codex, Copilot) | Objetos en el entorno, evidencia en la tarea |
| 5 · QA | Los escenarios de la épica con SAIL CLI por rol, y `testRule` en las reglas | QA (Antigravity) | Escenarios guardados, veredicto |
| 6 · Revisión y despliegue | Revisión visual contra el prototipo, cierre de la épica y despliegue autorizado | Jefe técnico y Raúl | Épica cerrada, paquete |

Las fases 0 a 2 son del plugin (existen o están en el plan, F2 a F9). Las fases 3 a 6 ya funcionan en un proyecto real
(abajo) y se generalizan en F10.

## Lo que ya existe (importado de otros hilos)

**Método por etapas con cuatro agentes.** Elegido por Raúl el 2026-10-07 en un proyecto real (pendiente de fusionar
allí). Es el que cubre las fases 3 a 6:

- **Papeles fijos:** Claude Code especifica, gobierna el tablero y cierra; Codex y Copilot construyen en Appian;
  Antigravity hace el QA de cada épica. Nadie revisa lo que ha construido.
- **Estado en GitHub:** un manifiesto versionado de tareas publica issues y un Project. Un script cambia el estado con
  **candado por objeto** (dos tareas a la vez nunca declaran el mismo objeto: el Dev MCP no tiene control de
  concurrencia) y exige evidencia para cerrar. Cada agente deja un parte en la issue antes de cerrar sesión.
- **Skills del proyecto:** especificar una épica, construir una tarea y hacer el QA de una épica.
- **Verificación según el tipo de cambio** (cosmético, lógica, contrato) y siete puertas de calidad, A1 a A7, las mismas
  siete de `appian-best-practices/references/10-quality-gates.md`.
- **Dev MCP:** además de leer y escribir objetos, valida (`validateExpression`, `validateDesignObject`) y prueba
  (`testRule`, `testInterface`, casos de prueba de reglas e interfaces, `testProcessModel`). No consta que monte
  paquetes. Las pantallas se prueban con SAIL CLI, una sesión por rol.
- **Lo que hace Raúl:** aprobar el mapa de épicas y sus especificaciones de una vez, las tareas `Manual` (lo que el Dev
  MCP no hace: Designer, Admin Console, base de datos, publicación), abrir la pestaña de cada agente y autorizar
  despliegues.

**Retirado el 2026-10-01:** un plugin anterior con la cadena especificar → planificar → construir → verificar → revisar
y hooks que bloqueaban. Se cambió por el método de arriba. La construcción nueva no lo repite: es método y scripts,
no hooks.

**Instalación de los agentes:** los cuatro agentes usan el mismo Dev MCP local, con un servidor por entorno. La skill
personal `appian-devmcp-update` lo actualiza en los cuatro a la vez. Es mantenimiento del equipo, no una fase del
flujo, y sigue fuera del plugin.

**`appian-sail-generator`:** se decidió el 2026-10-04 que sigue fuera del plugin por ahora.

## Cómo se unen el análisis y la construcción

El riesgo es tener dos especificaciones: el técnico del plugin y la especificación de cada épica. Propuesta: el técnico
es la fuente y la épica solo lo cita, igual que hoy la épica cita la fuente por sus ID.

- El **plan de construcción** del técnico (apartado 13) da el mapa de épicas y el orden de las tareas.
- Los **objetos** de la épica salen de los apartados 3 a 11 del técnico, con su nombre; la épica añade solo quién
  construye cada uno y qué es `Manual`.
- **Cómo se prueba** sale del apartado 14 (`HU-nn.m` y `ESC-nn`), y el QA lo convierte en escenarios de SAIL CLI.
- La **revisión visual** compara con las capturas del prototipo.
- Lo que el constructor no puede hacer como dice el técnico vuelve al analista como pendiente técnico (`PT-nn`).

## Abierto

- Si el portal web fuera de Appian entra en este flujo. En el proyecto real va por su propia superficie, con sus
  puertas P1 a P7.
- Si el despliegue (paquete, ICF y scripts de BD) se automatiza o sigue como tarea `Manual`.
