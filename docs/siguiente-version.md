# Para la siguiente versión

Lo que sigue abierto tras la 0.7.0-beta.4 (planes `docs/plan/2026-10-11-0.7.0-beta.3.md` y
`docs/plan/2026-10-12-correccion-buenas-practicas.md`). Cada línea dice qué, dónde y de dónde sale.

## Pasos de Raúl (para publicar la 0.7.0)

- Instalar el paquete en la app de escritorio y en un Windows con algo de la tabla de requisitos sin instalar, y ver que
  el primer mensaje lo dice (Paso 4 de la Tarea 24). En Linux con Claude Code ya está visto; en el portátil con Windows
  el hook corrió con la 0.7.0-beta.1 (dejó su marca el 10 de octubre), falta ver el mensaje con algo sin instalar.
- Ingeniería inversa y refactorización con una aplicación real (Paso 3 de la Tarea 30). Con ella:
  - confirmar que el Dev MCP real da el historial de versiones de cada objeto (lo usan `deriva` y la colisión real de
    una urgencia; sin él, el plugin lo dice y no supone nada);
  - afinar los presupuestos de palabras de ingeniería inversa (hoy la mayoría de documentos van al 20-50 %);
  - volver a medir la evaluación de malas prácticas con propuestas reales (las `claves` se fijaron a ciegas).
- Archivar `~/Proyectos IA/appian-reverse-engineering` en el equipo donde esté (Paso 3 de la Tarea 31): no está en su
  cuenta de claude.ai ni en el portátil de trabajo. Avisar a quien tenga la skill suelta.

## Ingeniería inversa (del recién llegado de la 0.7.0-beta.3)

- Un proceso de 130 nodos no cabe en el presupuesto de su `.md` (1.350 palabras) con «cada nodo citado» de
  `agents/process-modeler.md`: decidir si el presupuesto crece con los nodos o el paso a paso agrupa lo repetido.
- `references/mermaid-rules.md`: «como mucho 5 cajas por capa» no garantiza el ancho de la arquitectura; partirla en dos
  no encaja con `arquitectura-<capa>.mmd`.

## Agilidad (de medir un uso real y los despliegues, 12 de octubre de 2026)

Medido en una sesión real con la 0.6.0-beta.1 (incorporar una fuente corta con su prototipo, 70 minutos): comprobar
cada punto con la versión actual antes de cambiar nada.

- Prototipos: para retocar un prototipo que ya existía, se leyeron la guía de diseño entera y el código de los scripts
  antes de tocar nada (18 de 43 minutos). Falta decir qué se lee en un retoque.
- Analista: se leyeron el técnico y el funcional enteros, aunque `references/actualizacion.md` dice que no (17 minutos).
- Analista: en documentos cortos, la nota de la fuente salió de 3 a 7 veces más larga que el original.
- El análisis esperó al prototipo para generar el DF (28 minutos): decidir si el DF sale antes y las capturas se
  añaden después.
- Método de trabajo: probar una vez el plugin cargado desde la carpeta local (`claude --plugin-dir <carpeta>`) con una
  tarea real en un proyecto de prueba, y ver qué pasa con el plugin instalado del mismo nombre y si la app de escritorio
  tiene un equivalente. Si funciona, pasa a `CLAUDE.md` como condición para subir un cambio que altera cómo se comporta
  una skill.
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
- Un `.eml` con finales de línea de Windows deja `` en su `FU-nn.md`: viene de la lectura y sale igual en todos
  los sistemas, pero ensucia el fichero.

## Menores

- Diagramas: la salida de una puerta que comparte el tramo de su derecha sale ya por su vértice (el codo) y su etiqueta
  va en un tramo suyo; en 1.000 procesos al azar (semilla 11 del generador de `selftest.py`) quedan 8 (antes, 46) con
  una etiqueta donde pasa otro flujo: puertas con tres o más salidas por la derecha, con salidas por los tres vértices
  y el hueco lleno, o cuyo codo añadiría un cruce.
- Las URL de la documentación de Appian con versión fija (`/help/26.6/`) en `references/data-fabric.md`,
  `devmcp-setup.md` y `agents/data-modeler.md` son del Appian MCP Server: revisar al cambiar de versión.
