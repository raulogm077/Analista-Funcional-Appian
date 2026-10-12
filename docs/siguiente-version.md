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
- Probar en un entorno si una página oculta de un sitio se abre por su URL (usuario con permiso sobre la interfaz,
  «Only show when» en falso): la documentación no lo dice y `09` §7.3 de buenas prácticas lo deja como no documentado
  (plan del 12 de octubre, §4).
- Cada vez que se actualice la skill oficial `appian` (`appian-devmcp-update`): `python3
  pruebas/comprobar_divergencias.py`, y quitar de `14-official-skill-divergences.md` y de
  `pruebas/divergencias-oficial.json` lo que Appian haya corregido. De vez en cuando, con red, `python3
  pruebas/comprobar_anclas.py` (las anclas de la documentación cambian con cada versión de Appian).

## Ingeniería inversa (del recién llegado de la 0.7.0-beta.3)

- Un proceso de 130 nodos no cabe en el presupuesto de su `.md` (1.350 palabras) con «cada nodo citado» de
  `agents/process-modeler.md`: decidir si el presupuesto crece con los nodos o el paso a paso agrupa lo repetido.
- `references/mermaid-rules.md`: «como mucho 5 cajas por capa» no garantiza el ancho de la arquitectura; partirla en dos
  no encaja con `arquitectura-<capa>.mmd`.

## Menores

- Diagramas: la salida de una puerta que comparte el tramo de su derecha sale ya por su vértice (el codo) y su etiqueta
  va en un tramo suyo; en 1.000 procesos al azar (semilla 11 del generador de `selftest.py`) quedan 8 (antes, 46) con
  una etiqueta donde pasa otro flujo: puertas con tres o más salidas por la derecha, con salidas por los tres vértices
  y el hueco lleno, o cuyo codo añadiría un cruce.
- Las URL de la documentación de Appian con versión fija (`/help/26.6/`) en `references/data-fabric.md`,
  `devmcp-setup.md` y `agents/data-modeler.md` son del Appian MCP Server: revisar al cambiar de versión.
