# Para la siguiente versión

Lo que sigue abierto tras la 0.8.0-beta.1. Cada línea dice qué, dónde y de dónde sale.

## Pasos de Raúl (antes de la primera versión estable)

- Instalar el paquete en la app de escritorio y en un Windows con algo de la tabla de requisitos sin instalar, y ver que
  el primer mensaje lo dice. En Linux con Claude Code ya está visto; en el portátil con Windows el hook corrió con la
  0.7.0-beta.1 (dejó su marca el 10 de octubre de 2026), falta ver el mensaje con algo sin instalar.
- Ingeniería inversa y refactorización con una aplicación real. Con ella:
  - confirmar que el Dev MCP real da el historial de versiones de cada objeto (lo usan `deriva` y la colisión real de
    una urgencia; sin él, el plugin lo dice y no supone nada);
  - afinar los presupuestos de palabras de ingeniería inversa (hoy la mayoría de documentos van al 20-50 %);
  - volver a medir la evaluación de malas prácticas con propuestas reales (las `claves` se fijaron a ciegas).
- Archivar `~/Proyectos IA/appian-reverse-engineering` en el equipo donde esté: no está en su cuenta de claude.ai ni en
  el portátil de trabajo. Avisar a quien tenga la skill suelta.

## Ingeniería inversa (del recién llegado de la 0.7.0-beta.3)

- Un proceso de 130 nodos no cabe en el presupuesto de su `.md` (1.350 palabras) con «cada nodo citado» de
  `agents/process-modeler.md`: decidir si el presupuesto crece con los nodos o el paso a paso agrupa lo repetido.
- `references/mermaid-rules.md`: «como mucho 5 cajas por capa» no garantiza el ancho de la arquitectura; partirla en dos
  no encaja con `arquitectura-<capa>.mmd`.

## Agilidad (de medir un uso real y los despliegues, 12 de octubre de 2026)

Los cuatro puntos de la sesión real con la 0.6.0-beta.1 y la prueba con `claude --plugin-dir` se comprobaron y se
corrigieron con el método L.U.C.I.A. (`docs/evaluaciones.md`, Fase 1). Queda:

- Pruebas: medir cuánto tarda cada grupo de `comprobar_plugin.py --completo` y lanzarlos en paralelo; con la misma
  batería, Windows tarda el doble que Linux (17 y 8,5 minutos en GitHub).

## Del método L.U.C.I.A. (14 de octubre de 2026)

Lo que salió al ejecutar `docs/plan/2026-10-14-metodo-lucia.md` y no entra en él.

- Paso de Raúl: avisar a Appian de que `LCP_TOOL_MODE=readonly`, que su documentación describe, no está en el Dev MCP
  26.6.110 (`docs/evaluaciones.md`, T5).
- Analista: con los criterios en Gherkin, el aviso de «texto que queda viejo» de `comprobar.py --anterior` señala
  criterios que comparten el arranque («Dada una solicitud en revisión, cuando el técnico…») y siguen siendo verdad:
  no contar el tramo común o pedir más palabras seguidas.
- `leer_fuentes.py --help` y `unir_modulos.py --help` salen con los acentos rotos en Windows (pasan la consola a
  UTF-8 después de leer los argumentos); en `proyecto.py` ya está corregido.
- Issues sin Dev MCP: una issue solo queda hecha con lo que deja «verificar». Quien construye a mano sin Dev MCP sigue
  el índice y marca la unidad con `--manual`, pero `indice.py issues --siguiente` no pasa de las que no dependen de
  otra. Si un equipo trabaja así, falta poder dar una issue por hecha a mano.
- Issues: las dependencias salen de los objetos que dos issues comparten o que el técnico nombra al hablar de una; si
  el técnico las da de más, van en serie issues que podrían ir a la vez, y no hay cómo corregirlo a mano.
- Issues: el número de una issue que deja de existir se vuelve a dar si era el mayor de su unidad.
- Un `.eml` con finales de línea de Windows deja el retorno de carro (`\r`) en su `FU-nn.md`: viene de la
  lectura y sale igual en todos los sistemas, pero ensucia el fichero.
- Ingeniería inversa: la extracción no usa la herramienta de dependientes del Dev MCP real (`getObjectDependents`): su
  parámetro se llama `object` y el extractor no lo reconoce como el uuid del objeto (alcance manual). `verificar` sí la
  usa. Decidir si la extracción la llama: una llamada más por objeto.
- Pruebas de la issue: «no evaluable» reconoce solo la rejilla de registros con filtros de usuario
  (`flow!userFilterSetData`, `devmcp_policy.json`). Si aparece otro límite del ejecutor de Appian, se añade allí.
- `verificar` no comprueba quién ve una acción de registro ni quién inicia un proceso: en el ensayo de QA (T16) habría
  cazado dos de los cuatro defectos sembrados.

- QA: `qa.py` dice «ISS-nn vuelve a pendiente» aunque el escenario esté marcado como no necesario (no lee el índice);
  quien manda es `issues.estado()`, que sí lo respeta.
- Issues: un process model con varias actividades en «Para» junta en una sola issue varias historias y pantallas (en el
  proyecto de prueba, el 64 % del técnico); si molesta al construir, partirla por actividad.

- Analista: `indice.py impacto` da el texto de la fila de técnico §13 pero no en qué línea va; en el retoque a ciegas
  cuesta dos llamadas por pasada encontrarla.
- Evaluaciones: `montar.py` de `pruebas/evaluaciones/` monta los proyectos sin `proyecto.py iniciar`, así que `estado`
  avisa en ellos de que faltan git y `AGENTS.md`; montarlos como los deja el plugin.

## Menores

- Diagramas: la salida de una puerta que comparte el tramo de su derecha sale ya por su vértice (el codo) y su etiqueta
  va en un tramo suyo; en 1.000 procesos al azar (semilla 11 del generador de `selftest.py`) quedan 8 (antes, 46) con
  una etiqueta donde pasa otro flujo: puertas con tres o más salidas por la derecha, con salidas por los tres vértices
  y el hueco lleno, o cuyo codo añadiría un cruce.
- Las URL de la documentación de Appian con versión fija (`/help/26.6/`) en `references/data-fabric.md`,
  `devmcp-setup.md` y `agents/data-modeler.md` son del Appian MCP Server: revisar al cambiar de versión.
