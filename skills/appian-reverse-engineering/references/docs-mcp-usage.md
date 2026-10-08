# Docs MCP: tope de consultas y caché

Qué se consulta, cómo se cita y qué se hace sin el Docs MCP lo dice «Dudas de Appian» en `SKILL.md`, igual que en las demás skills del plugin. Aquí va lo propio de esta skill, en la que consultan varios agentes a la vez: el tope y la caché compartida.

## Tope: 30 consultas por ejecución

Entre todos los agentes, por el Docs MCP o por la web. El Docs MCP admite 300 consultas al día y 60 por minuto. La consulta de prueba de la fase 0 cuenta: el orquestador la apunta en `<trabajo>/docs_cache/orquestador.json`.

Reparto orientativo (el orquestador dice a cada subagente cuántas le quedan; lo que uno no gaste puede pasar a otro):

| Quién | Consultas |
|---|---|
| Preflight (fase 0) | 1 |
| `interface-analyzer` (4.1) | 5 |
| Cada uno de los 4 agentes de 4.2 | 5 (20 en total) |
| Orquestador (07, 09 y pasada de coherencia) | 4 |
| **Total** | **30** |

Para no gastarlas:

- Lo que ya dicen `references/` o la propia definición del objeto no se consulta.
- Las dudas iguales se agrupan: si 12 interfaces usan el mismo componente, **una** consulta («¿Está deprecado el componente Paging Grid en Appian 26.6?»).

## Caché compartida

Antes de consultar, lee los ficheros `<trabajo>/docs_cache/*.json` (uno por agente). Si la pregunta, o una equivalente, ya está respondida, reutilízala.

Después de consultar, añade la entrada a **tu** fichero (`<trabajo>/docs_cache/<nombre-del-agente>.json`, un **array JSON** de entradas; el orquestador usa `orquestador.json`), para no pisar el de otros agentes que trabajan en paralelo:

```json
{"query": "…", "askedAt": "2026-09-30T10:00:00Z", "answer": "resumen en 1-3 frases", "urls": ["https://docs.appian.com/..."]}
```

El orquestador suma las consultas de todos los ficheros para respetar el tope. Cada agente dice en su informe final cuántas hizo.
