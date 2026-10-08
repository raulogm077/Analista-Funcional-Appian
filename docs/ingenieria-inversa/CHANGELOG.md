# Cambios

## v2 — fuente Appian Dev MCP (octubre 2026)

**Extracción**
- Lee la aplicación en vivo con el Appian Dev MCP, en solo lectura forzada (`LCP_TOOL_MODE=readonly` y descarte de herramientas de escritura por firma). Ya no necesita el paquete exportado.
- Sin nombres de herramientas en el código: usa el catálogo del servidor en cada ejecución (`scripts/devmcp_extract.py`, política en `scripts/devmcp_policy.json`).
- Preflight de los 3 MCP (Dev MCP obligatorio; Appian MCP Server y Docs MCP opcionales), con qué se pierde si falta cada uno.
- Data fabric: solo metadatos y recuentos, nunca filas de negocio.
- `plan --json` imprime el plan; `extraction_report.json` trae `callStatsByRole` (correctas y fallidas por rol); `doctor` muestra 50 apps y remite a `apps --json` si hay más.

**Privacidad y solo lectura**
- Herramientas excluidas por palabras del nombre, se escriban como se escriban: filas de record, SQL, variables de procesos, datos de tareas, usuarios y credenciales.
- Única evaluación permitida: el render de interfaces con entradas vacías (versión segura del recorrido del site). Appian la evalúa en el servidor (puede ejecutar sus consultas de lectura) y se guarda ya sin valores: estructura y etiquetas, con los valores como `‹valor›`. Así aparece en el anexo.
- Enmascarado común de secretos (`scripts/privacidad.py`), también por parte del nombre de la clave, en cabeceras `{name, value}` y en literales SAIL (`password: "…"`).
- El anexo no lleva usuarios (tampoco `displayName`, `fullName`, campos `*By` o `*User` ni objetos de usuario) y muestra los correos como `‹correo›`.
- Detector de secretos en Python (`scripts/detect_secrets.py`; `detect_secrets.sh` lo llama): no cuenta referencias (`cons!`, `=ri!…`) ni valores ya enmascarados, y se pasa a toda la carpeta de salida.
- Appian MCP Server: solo el del mismo entorno que el Dev MCP (`<URL del entorno>/mcp`, u otro con `--mcp-server-name`), y solo con herramientas que no son de escritura.

**Dos carpetas**
- `appian-docs/<APP>/`: solo entregables, se puede compartir.
- `appian-docs/_trabajo/<APP>/`: respuestas en bruto, inventario, grafo, hallazgos y cachés; lleva un `.gitignore` con `*` y no se comparte.

**Documentación**
- 17 documentos: 00–14, `LEEME` e `INVENTARIO`, con un mismo esqueleto (TL;DR → Vista → Detalle → Hallazgos → Cobertura y límites).
- La fase 0 pregunta el objetivo: solo entender la aplicación, modernizarla sobre la actual o reconstruirla desde cero (por defecto, modernizar). La documentación de reconstrucción se genera siempre; el objetivo orienta su estrategia.
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
- Dos objetos del mismo tipo con el mismo slug ya no se pisan: se añade el principio del uuid.

## v1 — fuente: paquete exportado

Versión inicial basada en el `.zip` exportado de Appian.
