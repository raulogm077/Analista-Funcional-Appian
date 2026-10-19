# Para la siguiente versión

Trabajo que queda abierto después de aplicar las lecciones de automejora del 19 de octubre de 2026, sobre la
0.8.0-beta.1. Raúl pidió abordar los temas aplazados antes de publicar: la fase activa está en
`docs/plan/2026-10-19-temas-aplazados.md`. Los cambios terminados y sus pruebas están en `docs/evaluaciones.md`;
la primera tanda quedó cerrada en `docs/plan/2026-10-19-aplicar-automejora.md`. Esta lista no autoriza publicar ni actuar en un entorno.

## Antes de subir y publicar

- Probar el comportamiento de las skills modificadas con `claude --plugin-dir <carpeta>` en un proyecto fuera del
  repositorio. Los selftests y las regresiones sobre copias de P10 no sustituyen esa prueba.
- Cuando Raúl autorice subir: PR y batería completa en Linux. Antes de publicar una versión, las siete combinaciones
  de sistema/Python y la comprobación de anclas, como indica `CLAUDE.md`. La versión sigue sin cambiar.
- Instalar el paquete en la app de escritorio y en un Windows con algún requisito sin instalar; comprobar que el primer
  mensaje lo explica. En Linux con Claude Code ya se vio; el hook de Windows dejó su marca con 0.7.0-beta.1, pero falta
  ver el mensaje con un requisito ausente.

## Construcción y verificación: decisiones e implementación en curso

- Dos unidades sobre la misma pieza sin construir (D1): Raúl eligió secuenciar esa pieza. Se implementan guardias
  para que una propuesta ajena no contamine el encargo aprobado. La aprobación sigue siendo de la unidad entera;
  no hay aprobación parcial ni nuevos encargos históricos por unidad.
- Issues grandes (D7): medidas las 25 de P10 y explicados los pros y contras. Espera elección entre subtareas con
  avance guardado e issues independientes tras separar sus objetos. No se ha aplicado una opción por silencio.
- Prueba diferencial de una refactorización (E3): buscar un caso real en la aplicación de Indra elegida por Raúl,
  con diferencias aceptadas y motivo. Las lecturas están autorizadas; cualquier ejecución se concretará por separado.
- Permisos (C8): Raúl eligió bloquear una diferencia confirmada salvo aceptación humana expresa del comportamiento.
  Se implementa comparación de configuración decidible y excepción acotada a la diferencia; lo ilegible o no
  resoluble será «no comprobado». El acceso efectivo sigue requiriendo QA con usuarios de cada rol.
- «No evaluable» reconoce el límite de la rejilla con filtros de usuario (`flow!userFilterSetData`). Añadir otro límite
  a `devmcp_policy.json` solo si aparece y se comprueba.

## Ingeniería inversa y diagramas

- Ejecutar `deriva` de punta a punta y medir LEEME con la aplicación real elegida en Indra (lectura en curso).
  El historial existe en el Dev MCP real; el LEEME anterior llegó al 96 % con 42 objetos y los demás documentos
  quedaron al 20–54 %. No se cambia el presupuesto antes de medirlo (E6).
- Volver a medir la evaluación de malas prácticas con propuestas reales; sus `claves` se fijaron sin esas propuestas.
- La campaña de 1.000 procesos (semilla 11) ya deja cero etiquetas atravesadas. Persisten 126 conexiones falsas
  detectadas, frente a 142 antes de esta fase; medir esos casos por separado antes de ampliar el cambio de rutas.
- La política permite `testInterface` en desarrollo con datos ficticios. Si se lee un entorno con datos reales,
  documentar `--skip "^testInterface$"` en F6 y `devmcp-setup.md` antes de esa lectura.
- Revisar las URL fijas `/help/26.6/` de `data-fabric.md`, `devmcp-setup.md` y `agents/data-modeler.md` cuando cambie
  la versión del Appian MCP Server.

## Comprobaciones pendientes de los cambios terminados

- Medir el fondo compuesto real bajo los cuatro textos sobre imágenes que el auditor de contraste no mide:
  doce apariciones entre pantalla y diálogos. El diagnóstico conserva esa limitación explícita.
- Medir en CI la batería completa con la concurrencia limitada y los tiempos por grupo (E7). La pareja QA y
  refactorización pasa en serie y en paralelo; esa mejora local no acredita aún el tiempo del conjunto.

## Pasos de Raúl

- Archivar la skill suelta `~/Proyectos IA/appian-reverse-engineering` en el equipo donde esté y avisar a quien la tenga;
  no estaba en su cuenta de claude.ai ni en el portátil de trabajo.
- Avisar a Appian de que `LCP_TOOL_MODE=readonly`, descrito en su documentación, no está en Dev MCP 26.6.110
  (`docs/evaluaciones.md`, «Fase 2 · T5»).
- Borrar, con autorización y desde la base de datos, las seis tablas vacías `cpr_*` de P6 en Indra-spain. El Dev MCP no
  borra tablas; la aplicación y sus objetos ya se borraron. Este trabajo no toca esas tablas.
- Repetir P8 con Codex desde un terminal normal: el intento anterior dentro de otra sesión no fue concluyente porque
  no arrancó su sandbox. La ruta local del plugin ya tiene solución; falta repetir la prueba de comportamiento.
- Conciliar el índice del cerebro corporativo: marca 1.692 reuniones transcritas y se encontraron 1.095 en disco.
