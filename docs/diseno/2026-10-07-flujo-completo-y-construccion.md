# Flujo completo: de cualquier punto de partida a la aplicación construida

> Propuesta trabajada con Raúl el 2026-10-07 en el hilo «Flujo de trabajo Appian». Decidido: el flujo llega
> hasta construir en Appian con IA, y construir es una skill nueva. Lo marcado como **abierto** está sin cerrar.

## El flujo

Tres entradas y un mismo camino. Todo lo que se construye pasa por el analista.

| Fase | Qué se hace | Quién | Sale |
|---|---|---|---|
| 0 · Punto de partida | App nueva: reuniones, correos, DF del cliente | Analista | `fuentes/` |
| | App existente que se amplía | Ingeniería inversa → analista | `as-is/` |
| | App legacy que se rehace (toda o una parte) | Ingeniería inversa → refactorización → analista | `as-is/`, `refactorizacion/propuesta.md` |
| 1 · Especificar | Funcional que valida el cliente y técnico para construir; procesos en BPMN | Analista, diagramas | `analisis/funcional.md`, DF en Word, `analisis/tecnico.md` |
| 2 · Validar con el cliente | Prototipo navegable; su feedback vuelve al analista como fuente | Prototipos → analista | `prototipo/` |
| 3 · Construir | El plan de construcción del técnico, paso a paso, por el Dev MCP | **Construcción (nueva)** | Objetos en el entorno, `construccion/registro.md` |
| 4 · Verificar | Las pruebas del técnico (apartado 14) y las siete quality gates sobre lo construido | **Construcción (nueva)** con buenas prácticas en modo revisión | `construccion/verificacion.md` |
| 5 · Desplegar y mantener | Paquete, ICF y scripts de BD; runbooks; cada incidencia vuelve al analista como fuente | **Construcción (nueva)** para el paquete; buenas prácticas para los runbooks | Paquete y notas de despliegue |

Las fases 0 a 2 ya existen o están en el plan (F2 a F9). Las fases 3 a 5 son nuevas (F10).

## La skill de construcción

**Se ocupa de:** ejecutar en el entorno lo que el técnico especifica, comprobar que lo construido lo cumple y preparar el
paquete. **No hace:** decidir requisitos ni diseño (analista), doctrina de Appian (buenas prácticas), pantallas de
prototipo (prototipos).

**Entradas:** `analisis/tecnico.md` (apartado 13, plan de construcción en orden de dependencias, y apartado 14,
pruebas y trazabilidad), el `app.json` del prototipo como punto de partida del SAIL de cada interfaz, y el Dev MCP de
la persona, con sus credenciales.

**Por cada paso del plan:**

1. Lee la sección de buenas prácticas que aplica (`seccion.py`).
2. Sigue la skill oficial `dev-mcp-skills` para la mecánica (nombres, orden de creación, UUID reales).
3. Escribe por el Dev MCP; antes de modificar un objeto existente, mira sus dependientes.
4. Pasa la quality gate del objeto (`10-quality-gates.md`).
5. Anota en `construccion/registro.md`: paso del plan, objeto, Nuevo / Modifica, gate y pendientes.

Lo que no se puede construir como dice el técnico no se improvisa: vuelve al analista como pendiente técnico (`PT-nn`).

**Verificar:** recorre la tabla del apartado 14 (cada criterio `HU-nn.m` con su prueba y cada `ESC-nn` de extremo a
extremo), con test cases en las reglas donde aplique, y revisa el conjunto con las siete gates. Cada criterio queda
como cumple, no cumple o sin verificar, con su evidencia.

**Desplegar:** monta el paquete, el ICF y los scripts de BD según `08-alm-testing-naming.md` §3, con la lista de pasos
manuales del técnico.

**Dónde se ejecuta:** en el equipo de quien construye, porque el Dev MCP es local. Sin Dev MCP, la skill deja los mismos
pasos como cambios para Designer.

## Abierto

- Si el portal web fuera de Appian (como el de GDE) entra en este flujo o queda fuera.
- Qué ofrece el Dev MCP para ejecutar test cases y montar paquetes: sin verificar; se comprueba antes de escribir la skill.
- Cómo encaja la skill propia `appian-devmcp-update` de Raúl: si la absorbe la de construcción o sigue aparte.
- Si `appian-sail-generator` entra en el plugin para el SAIL funcional de las interfaces o sigue fuera.
