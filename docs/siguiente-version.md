# Para la siguiente versión

Sólo trabajo pendiente. Resultados, commits y límites medidos en [evaluaciones.md](evaluaciones.md).
Esta lista no autoriza publicar, desplegar, enviar ni borrar.

## Cierre de la campaña actual

- Borrar las cachés locales inventariadas (`__pycache__`, `.pytest_cache`; no versionadas) sólo cuando se
  confirme. Se conservan galerías, esquemas y flujos: sí tienen consumidores.
- Terminar la QA independiente del Word C abierto con Microsoft Word real (índice con páginas, figuras y
  destinos): valida un procedimiento externo, no el plugin, y quedó a medias.

## Mejoras que requieren un caso o una decisión

- Índice Word/PDF: decidir la salida que se quiere entregar y medir la solución del exportador estándar.
  Guardar y reabrir copias conserva la caché DOCX en dos ensayos externos; Microsoft Word, figuras y
  otros sistemas siguen sin medir. El exportador estándar no actualiza el índice.
- Diagramas: reducir los 30/38 avisos residuales sólo con mejora medida, sin relajar detectores ni cambiar
  un motor por intuición. Un orden distinto de notas no implica pérdida si asociación y texto se conservan.
- PDF de procesos grandes: resolver la reducción de resolución observada al exportar desde Word; la opción
  de calidad no la evitó. Falta medir LibreOffice. El DOCX sí conserva los píxeles; véase `evaluaciones.md`.
- LEEME completo y deriva interna de una aplicación real siguen sin medir. Mantener la extracción masiva
  detenida; `getAgent` está aparcado tras el reporte a Appian. No ampliar presupuesto por el caso ficticio.
- QA: completar sólo las dimensiones necesarias para la entrega: visual/accesibilidad, roles con cuenta,
  autorización de servidor, vigencia causal y atomicidad/concurrencia. Los resultados acotados existentes
  no acreditan esas dimensiones; no crear cuentas ni escribir datos por esta lista.
- Revisar el contraste automático de texto sobre fondo compuesto si un caso visible lo requiere.
- Revisar las URL `/help/26.6/` de `data-fabric.md`, `devmcp-setup.md` y `agents/data-modeler.md`
  al cambiar la versión del servidor MCP.
- Comunicar la discrepancia comprobada de `LCP_TOOL_MODE=readonly` en Dev MCP 26.6.110, si aún procede.

La activación/comportamiento con Claude y la instalación visual de escritorio permanecen sin medir;
no son obligatorias en esta fase ni autorizan comparaciones entre herramientas. Una nueva medida de eficiencia
necesita casos equivalentes: las comparaciones actuales no acreditan el objetivo del 20 %.
