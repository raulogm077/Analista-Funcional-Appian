# Para la siguiente versión

Lo que sigue abierto tras la 0.7.0-beta.2 (plan `docs/plan/2026-10-10-0.7.0-beta.2.md`). Todo lo que estaba apuntado
hasta F9 se cerró en esa versión o está aquí. Cada línea dice qué, dónde y de dónde sale.

## Pasos de Raúl (para publicar la 0.7.0)

- Instalar el paquete en la app de escritorio y en un Windows con algo de la tabla de requisitos sin instalar, y ver que
  el primer mensaje lo dice (Paso 4 de la Tarea 24). En Linux con Claude Code ya está visto.
- Ingeniería inversa y refactorización con una aplicación real (Paso 3 de la Tarea 30). Con ella:
  - confirmar que el Dev MCP real da el historial de versiones de cada objeto (lo usan `deriva` y la colisión real de
    una urgencia; sin él, el plugin lo dice y no supone nada);
  - afinar los presupuestos de palabras de ingeniería inversa (hoy la mayoría de documentos van al 20-50 %);
  - volver a medir la evaluación de malas prácticas con propuestas reales (las `claves` se fijaron a ciegas).
- Retirar la skill suelta de ingeniería inversa y archivar su carpeta (Paso 3 de la Tarea 31).
- Si `appian-sail-generator` es tuya, añadir a su descripción que no es para prototipos navegables para el cliente
  (appian-prototipos) ni para revisiones de buenas prácticas (appian-best-practices).

## Ligereza

- Un retoque de texto sobre algo construido costó 34, 34 y 47 llamadas frente al tope de 25 de la prueba de coste
  (`docs/evaluaciones.md`, tarea 5.12). La calidad fue completa. Medir de nuevo con el plugin instalado y, si sigue por
  encima, un camino corto para una fuente de un punto que no requiere aprobación (informe y aplicación en un paso).

## Evaluaciones

- La del recién llegado no se ha vuelto a pasar con la 0.7.0-beta.2.
- El enrutado con las skills vecinas (`appian-sail-generator`, Word) se midió con el mismo lote con el que se ajustaron
  las descripciones: añadir peticiones ocultas de esa frontera.

## Menores (de las revisiones de G1-G6)

- Ingeniería inversa: en el informe de un `extract --solo` o con herramientas cuyas llamadas son todas `notApplicable`,
  usadas + omitidas no da el catálogo.
- Diagramas: la salida de una puerta que comparte el tramo de su derecha sale ya por su vértice (el codo) y su etiqueta
  va en un tramo suyo; en 1.000 procesos al azar (semilla 11 del generador de `selftest.py`) quedan 8 (antes, 46) con
  una etiqueta donde pasa otro flujo: puertas con tres o más salidas por la derecha, con salidas por los tres vértices
  y el hueco lleno, o cuyo codo añadiría un cruce.
- `requisitos.py`: cualquier servidor http configurado (GitHub, Notion…) deja el Appian MCP Server en «no se puede
  comprobar».
- Las URL de la documentación de Appian con versión fija (`/help/26.6/`) en `references/data-fabric.md`,
  `devmcp-setup.md` y `agents/data-modeler.md` son del Appian MCP Server: revisar al cambiar de versión.
