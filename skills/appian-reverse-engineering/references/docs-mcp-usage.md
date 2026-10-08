# Uso del Appian Docs MCP

El Docs MCP es el servidor público de documentación de Appian (`https://appian-docs-public.mcp.kapa.ai`). Ofrece una búsqueda semántica sobre docs.appian.com. Es **opcional**: si no está disponible, la skill funciona igual y las afirmaciones que dependan de la documentación se marcan «sin verificar».

## Límites

- **300 consultas al día y 60 por minuto** (límite del servicio). La skill se impone un tope de **30 consultas por ejecución** entre todos los agentes.
- Requiere OAuth (Google o GitHub) en el cliente: el script de preflight no puede comprobarlo; se comprueba desde la sesión con una consulta de prueba (fase 0). El orquestador apunta esa consulta en `<trabajo>/docs_cache/orquestador.json` y cuenta para el tope.

Reparto orientativo del tope (el orquestador dice a cada subagente cuántas le quedan; lo que uno no gaste puede pasar a otro):

| Quién | Consultas |
|---|---|
| Preflight (fase 0) | 1 |
| `interface-analyzer` (4.1) | 5 |
| Cada uno de los 4 agentes de 4.2 | 5 (20 en total) |
| Orquestador (07, 09 y pasada de coherencia) | 4 |
| **Total** | **30** |

## Cómo localizar la herramienta

No dependas de un nombre fijo. En la sesión, busca una herramienta de un servidor de documentación de Appian cuya descripción hable de buscar en las fuentes de conocimiento o la documentación de Appian (hoy se llama `search_appian_knowledge_sources`). Si no hay ninguna, el Docs MCP no está disponible.

## Cuándo consultarlo

Solo cuando cambie lo que vas a escribir:

1. **Explicar** un tipo de nodo, smart service, función o componente que no conozcas con seguridad.
2. **Verificar** si algo está deprecado, antes de registrarlo como hallazgo.
3. **Confirmar** un comportamiento dudoso (p. ej. semántica de un temporizador o de una opción de seguridad).

No lo consultes para cosas que ya dicen `references/` o la propia definición del objeto.

## Cómo consultarlo

- Una pregunta por tema, en lenguaje natural y concreta: «¿Está deprecado el componente Paging Grid y qué lo sustituye?».
- Incluye la versión si la conoces: «en Appian 26.6».
- Agrupa: si hay 12 interfaces con el mismo componente obsoleto, **una** consulta.

## Caché compartida

Antes de consultar, lee los ficheros `<trabajo>/docs_cache/*.json` (uno por agente). Si la pregunta, o una equivalente, ya está respondida, reutilízala.

Después de consultar, añade la entrada a **tu** fichero (`<trabajo>/docs_cache/<nombre-del-agente>.json`, un **array JSON** de entradas; el orquestador usa `orquestador.json`), para no pisar el de otros agentes que trabajan en paralelo:

```json
{"query": "…", "askedAt": "2026-09-30T10:00:00Z", "answer": "resumen en 1-3 frases", "urls": ["https://docs.appian.com/..."]}
```

El orquestador suma las consultas de todos los ficheros para respetar el tope. Cada agente dice en su informe final cuántas hizo.

## Cómo citarlo

Toda afirmación que salga de la documentación lleva la URL:

```
Fuente: https://docs.appian.com/suite/help/26.6/Deprecated_Features.html
```
