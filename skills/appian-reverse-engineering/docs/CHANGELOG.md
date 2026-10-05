# Cambios

## v2 — fuente Appian Dev MCP (octubre 2026)

**Extracción**
- Lee la aplicación en vivo con el Appian Dev MCP, en solo lectura forzada (`LCP_TOOL_MODE=readonly` y descarte de herramientas de escritura por firma). Ya no necesita el paquete exportado.
- Sin nombres de herramientas en el código: usa el catálogo del servidor en cada ejecución (`scripts/devmcp_extract.py`, política en `scripts/devmcp_policy.json`).
- Preflight de los 3 MCP (Dev MCP obligatorio; Appian MCP Server y Docs MCP opcionales), con qué se pierde si falta cada uno.
- Data fabric: solo metadatos y recuentos, nunca filas de negocio. Render de pantallas sin valores.

**Dos carpetas**
- `appian-docs/<APP>/`: solo entregables, se puede compartir.
- `appian-docs/_trabajo/<APP>/`: respuestas en bruto, inventario, grafo, hallazgos y cachés; no se comparte.

**Documentación**
- 17 documentos: 00–14, `LEEME` e `INVENTARIO`, con un mismo esqueleto (TL;DR → Vista → Detalle → Hallazgos → Cobertura y límites).
- Nuevo `14-diseno-objetivo.md` (agente `target-designer`): cómo quedaría la aplicación rehecha, con ciclo de vida, catálogo de objetos, correspondencia, migración y reconstrucción en una aplicación nueva.
- Registro único de hallazgos con dos ejes: certeza (✅ 🔵 ❓) y severidad (Alta, Media, Baja). `scripts/build_registry.py` lo valida y escribe la tabla de 09.
- `anexo/`: definición original de cada objeto y el resto de respuestas de la plataforma, sin usuarios ni secretos (`scripts/build_annex.py`). La evidencia de los documentos enlaza aquí.
- Procesos: `.bpmn` fiel a Appian (temporizador, llamada a proceso, tareas de script, sistemas externos) con coordenadas de dibujo (`scripts/bpmn_layout.py`); la imagen puede salir de la skill `appian-diagramas-bpmn` (draw.io editable).
- `summary.json` con nivel de confianza calculado (cobertura y proporción verificada), procesos críticos y uso real.
- Las limitaciones globales se explican una vez, en `LEEME`.

**Correcciones**
- `validate_mermaid.py` acepta `erDiagram` y `subgraph` (antes fallaban los diagramas de datos y los de procesos con carriles).
- `detect_secrets.sh` acepta ficheros sueltos y apunta al documento de seguridad; `render_diagrams.sh` ya no comparte un fichero de errores fijo entre subagentes.
- Nombres de ficheros y contrato de `summary.json` alineados entre scripts y agentes.

## v1 — fuente: paquete exportado

Versión inicial basada en el `.zip` exportado de Appian.
