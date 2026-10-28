# Para la siguiente versión

Sólo trabajo pendiente. Resultados, commits y límites medidos en [evaluaciones.md](evaluaciones.md).
Esta lista no autoriza publicar, desplegar, enviar ni borrar.

## Cierre de la campaña actual

- Borrar las cachés locales inventariadas (`__pycache__`, `.pytest_cache`; no versionadas) sólo cuando se
  confirme. Se conservan galerías, esquemas y flujos: sí tienen consumidores.
- Terminar la QA independiente del Word C abierto con Microsoft Word real (índice con páginas, figuras y
  destinos): valida un procedimiento externo, no el plugin, y quedó a medias.

## Mejoras que requieren un caso o una decisión

- Índice del DOCX: evaluar la caché editable sólo si la entrega la necesita. Guardar y reabrir copias la
  conserva en dos ensayos externos; otros sistemas siguen sin medir. El PDF estándar ya actualiza el índice.
- Diagramas: reducir los 30/38 avisos residuales sólo con mejora medida, sin relajar detectores ni cambiar
  un motor por intuición. Un orden distinto de notas no implica pérdida si asociación y texto se conservan.
- LEEME completo y deriva interna de una aplicación real siguen sin medir. Mantener la extracción masiva
  detenida; `getAgent` está aparcado tras el reporte a Appian. No ampliar presupuesto por el caso ficticio.
- QA: completar sólo las dimensiones necesarias para la entrega: visual/accesibilidad, roles con cuenta,
  autorización de servidor, vigencia causal y atomicidad/concurrencia. Los resultados acotados existentes
  no acreditan esas dimensiones; no crear cuentas ni escribir datos por esta lista.
- Revisar el contraste automático de texto sobre fondo compuesto si un caso visible lo requiere.
- Revisar las URL `/help/26.6/` de `data-fabric.md`, `devmcp-setup.md` y `agents/data-modeler.md`
  al cambiar la versión del servidor MCP.
- Comunicar la discrepancia comprobada de `LCP_TOOL_MODE=readonly` en Dev MCP 26.6.110, si aún procede.
- Buenas prácticas de SAIL y seguridad, de dos pruebas reales de construcción: un grid no acepta una lista vacía de mapas
  aunque esté oculto, ni dos grupos de filtros anidados vacíos a la vez; dos filtros en `AND` sobre una relación uno a
  muchos se cumplen con filas distintas (hace falta `AND_ALL`); `append()` con un texto como primer argumento concatena;
  la seguridad «quien ve el registro relacionado» encadenada en dos niveles no deja ver nada; las cuentas de prueba con
  el idioma de la máquina dan los importes en formato inglés.
- F8, de la segunda prueba (decisión pendiente): que el orden calculado vea que un `a!recordLink` necesita la vista de
  resumen que hace otra issue; que las correcciones de dependencias no caduquen por cualquier cambio de la issue; un
  camino corto para cambiar una issue ya verificada (dónde se escribe, subtareas, qué cambió); y si `verificar` dice lo
  que no comprueba (relaciones, seguridad de registro, grupos, datos, vistas ocultas) o lo comprueba.
- Medir en la siguiente unidad real la regla de F8 «varias issues por sesión»: es una hipótesis, no un ahorro medido.
- F9: si la IA puede dejar preparado el paquete en desarrollo (hoy lo prepara una persona); si sí, añadir que
  `addPackageObjects` en lote no admite los objetos de contenido.
- Sesiones en paralelo sin pedir confianza (ensayo con y sin el plugin, L7; Raúl quiere darla una vez al crear el
  proyecto): `proyecto.py iniciar` hace `git init` y un repositorio anidado no hereda la confianza de la carpeta padre,
  así que `claude --bg` no arranca («Workspace not trusted»). Fuera del diálogo interactivo, la única vía que documenta
  Claude Code es escribir `projects["<raíz>"].hasTrustDialogAccepted = true` en `~/.claude.json` (permissions, «Project
  allow rules and workspace trust»); la confianza no comparte las aprobaciones de permisos.
  Opciones por decidir: abrir una vez la carpeta en una sesión interactiva al crear el proyecto; que la sesión que
  orquesta escriba esa clave con el visto bueno de la persona, si el `.claude/` del proyecto no trae permisos sin revisar;
  o no anidar el repositorio.
- Coste del análisis con el plugin (mismo ensayo). Hipótesis para priorizar, de un reparto contable de las
  transcripciones (no ahorro causal): pesan los pasos del método por incremento (unos 155 de 482 turnos usan órdenes
  o ficheros propios del plugin) y los documentos vivos grandes (`funcional.md` ~94 KB y `tecnico.md` ~196 KB), que se
  editan por parches y se releen, con un contexto que llega a 760–930k tokens; el texto de skills y referencias pesa
  poco. Antes de recortar, decidir qué pasos se juntan o pasan a scripts y cómo leer solo la parte del técnico que
  toca, y medirlo en una unidad real.
- Divergencias con la skill oficial del bundle 26.9.5 (build 20261026-140102): Appian corrigió 9 de las 19 filas del
  doc 14 (`and()`/`or()`, `fetchTotalCount`, `a!forEach()` sobre null, `length()`, fecha de hoy, clave compuesta,
  filtros del grid, colores de rich text y reglas recursivas) y 5 siguen con otras palabras o en otro fichero (una o
  varias consultas, campos de auditoría, record list, botón destructivo, filas por página). Quitar y reanclar, con
  «aplica» de Raúl; y repetir con el servidor 26.9.5 las 8 filas de §3 vistas con builds anteriores.
- Tarea no prioritaria, solo cuando Raúl lo pida: renombrar el plugin a «Appian Software Factory» en todos los sitios
  (GitHub, carpeta local, `plugin.json`, el prefijo de las skills, README, gráficos y `CLAUDE.md`).

La activación/comportamiento con Claude y la instalación visual de escritorio permanecen sin medir;
no son obligatorias en esta fase ni autorizan comparaciones entre herramientas. Una nueva medida de eficiencia
necesita casos equivalentes: las comparaciones actuales no acreditan el objetivo del 20 %.
