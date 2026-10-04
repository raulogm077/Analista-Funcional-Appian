---
name: appian-reverse-engineering
description: Reingeniería inversa de aplicaciones Appian leyendo el entorno en vivo por MCP (Appian Dev MCP, en solo lectura; opcionalmente Appian MCP Server y Appian Docs MCP). Genera documentación funcional y técnica para que alguien nuevo entienda cómo está hecha la aplicación (funcional, arquitectura, modelo de datos, seguridad, integraciones, APIs, batches, BPMN por proceso, pantallas, reglas de negocio, inventario) y documentación para reconstruirla y modernizarla (especificación de requisitos independiente de la implementación, diagnóstico de obsolescencia y antipatrones con fuentes oficiales, arquitectura objetivo y plan de migración). Úsala cuando el usuario quiera documentar, entender, hacer onboarding, auditar, reconstruir, refactorizar o modernizar una aplicación Appian existente, o pida su BPMN, modelo de datos, mapa de integraciones, pantallas o reglas de negocio, aunque no diga «reingeniería inversa». No es para crear ni modificar objetos Appian.
---

# Appian Reverse Engineering (Dev MCP)

Lee una aplicación Appian **en vivo y en solo lectura** a través del Appian Dev MCP y produce dos bloques de documentación:

- **A. Entender cómo está hecha** (onboarding y mantenimiento): `00`–`11` e `INVENTARIO`.
- **B. Reconstruirla y modernizarla**: `12-especificacion-reconstruccion.md` y `13-modernizacion-refactor.md`.

Todo con evidencia verificable (`mcp:<tipo>/<nombre>#<ubicación>`) y sin inventar: lo que no se puede obtener se dice.

## Principios de funcionamiento

- **Solo lectura, siempre.** La extracción la hace `scripts/devmcp_extract.py`, que arranca su propia instancia del Dev MCP con `LCP_TOOL_MODE=readonly` forzado y aplica la política de `scripts/devmcp_policy.json` (bloquea escritura, interacción, evaluación de lógica y lectura de filas de negocio). **No llames tú a herramientas de escritura del Dev MCP** aunque estén en la sesión.
- **Sin herramientas fijas.** El extractor usa todas las herramientas de lectura que ofrezca el catálogo del servidor en cada momento, clasificándolas por su firma. Cuando Appian actualiza el Dev MCP, las herramientas nuevas se aprovechan solas.
- **Extracción por script, análisis por agentes.** El script vuelca todo a disco (miles de llamadas sin pasar por el contexto). Los subagentes leen esos ficheros.
- **Tres MCP.** Dev MCP es obligatorio. Appian MCP Server (volúmenes) y Docs MCP (documentación oficial) son opcionales: si faltan, se indica qué se pierde y se sigue.

## Cómo ejecutar los scripts

Desde la **carpeta de trabajo del usuario** (donde está su configuración MCP, p. ej. `.mcp.json`), con la ruta absoluta de esta skill:

```bash
uv run --with "mcp>=1.2,<2" python "<carpeta-de-esta-skill>/scripts/devmcp_extract.py" <subcomando> [opciones]
python3 "<carpeta-de-esta-skill>/scripts/build_model.py" <salida>
```

`uv` ya es requisito del Dev MCP. Añade `--json` para salida legible por máquina. Códigos de salida en la cabecera de `devmcp_extract.py`.

## Argumentos

| Argumento | Obligatorio | Por defecto |
|---|---|---|
| Aplicación (nombre, prefijo o uuid) | Sí; si no lo da, se elige de la lista en la fase 0 | — |
| Idioma | No | español |
| Carpeta de salida | No | `./appian-docs/<PREFIJO>/` |

**Dos carpetas.** `<salida>` (p. ej. `appian-docs/DEM/`) solo tiene entregables y se puede compartir. Los datos de trabajo (respuestas en bruto, inventario, grafo, cachés, resumen) van en `<trabajo>` = `appian-docs/_trabajo/<PREFIJO>/`, que los scripts deducen de `<salida>`. **`<trabajo>` no se comparte**: tiene usuarios, hosts y definiciones completas.

---

## Flujo de trabajo

Detalle operativo y checklists en `references/analysis-workflow.md`. Crea una lista de tareas con las fases y ve marcándolas.

### Fase 0 — Preflight de los 3 MCP (obligatoria)

1. Ejecuta `devmcp_extract.py doctor --json`.
2. Comprueba en la sesión:
   - **Docs MCP**: busca una herramienta de búsqueda en la documentación de Appian (ver `references/docs-mcp-usage.md`). Si existe, haz **una** consulta de prueba corta; cuenta para el tope.
   - **Appian MCP Server**: si `doctor` dice `no_configurado` pero en la sesión hay herramientas del data fabric de Appian, márcalo «disponible en sesión».
3. Muestra al usuario esta tabla (una fila por MCP): **estado · qué se pierde si falta · cómo activarlo** (sección correspondiente de `references/devmcp-setup.md`).
4. Si el Dev MCP no está `ok`: explica el paso concreto de `devmcp-setup.md` que falta y **detente**.
5. Con el Dev MCP `ok`:
   - Confirma la aplicación. Si no la ha dado, muéstrale las apps de `doctor` y pregunta.
   - Pregunta los formatos adicionales, igual que antes: *«Además de los documentos Markdown, ¿quieres 📄 PDF maquetado, 🖥️ dashboard web, o solo los .md?»*. Sin respuesta explícita: solo Markdown.
   - Indica el entorno (`url` de `doctor`): el uso real de procesos solo es representativo en producción. Todo es lectura, sea cual sea el entorno.
6. Guarda la salida de `doctor` en `<trabajo>/preflight.json` (con tus comprobaciones de sesión añadidas) y las preferencias en `<trabajo>/output_preferences.json`.

### Fase 1 — Plan de extracción

`devmcp_extract.py plan --app <app> --out <salida>`. Resume al usuario: objetos por tipo, herramientas que se usarán y excluidas (con motivo) y llamadas estimadas. Si `needsConfirmation` es `true`, pide confirmación antes de seguir.

### Fase 2 — Extracción

1. `devmcp_extract.py extract --app <app> --out <salida>` (añade `--yes` si el usuario confirmó un plan grande). Es reanudable: si se corta, repítelo.
2. Revisa `extraction_report.json`. Si fallan más del 20 % de las llamadas de definición, díselo al usuario antes de seguir.
3. Data fabric (opcional, `references/data-fabric.md`): `devmcp_extract.py datafabric --out <salida>` si hay servidor en la configuración; si solo está en la sesión, hazlo desde la sesión; si no, sáltalo.

### Fase 3 — Modelo

1. `build_model.py <salida>` → `inventory.json` y `graph.json`.
2. `bash scripts/detect_secrets.sh <trabajo>/mcp_raw`: lo que salga hay que enmascararlo en los entregables. **No muestres los valores.**

### Fase 4 — Análisis con subagentes

Lee antes `references/execution-principles.md`. Cada subagente recibe:

- el contenido de `agents/<rol>.md`, o su ruta absoluta con la orden de leerlo entero antes de empezar (si el subagente puede leer ficheros);
- la ruta de la skill, para que abra `references/` y `assets/` que cite su fichero;
- la carpeta de salida;
- si el Docs MCP está disponible y cuántas consultas le quedan (tope global de 30);
- el entorno y la versión si se conoce.

| Paso | Subagente | Genera |
|---|---|---|
| 4.1 | `interface-analyzer` | `01-funcional.md`, `02-arquitectura.md` |
| 4.2 (en paralelo, un solo turno) | `data-modeler` | `03-modelo-datos.md` |
| | `integration-security-analyzer` | `04`, `05`, `06` |
| | `process-modeler` | `08-procesos-bpmn/` |
| | `ui-rules-analyzer` | `10-pantallas.md`, `11-reglas-negocio.md` |
| 4.3 | orquestador | `07-batches.md`, `09-valor-adicional.md` |
| 4.4 | `rebuild-architect` | `12-especificacion-reconstruccion.md`, `13-modernizacion-refactor.md` |

**Patrón de invocación** (Claude Code): `Agent({description, subagent_type: "general-purpose", prompt: <agents/rol.md> + entradas})`, varios en el mismo mensaje cuando van en paralelo. Sin herramienta de subagentes: aplica tú mismo cada `agents/<rol>.md` en el mismo orden.

### Fase 5 — Diagramas

Cada bloque Mermaid pasa `scripts/validate_mermaid.py`, que admite los tipos A, B y C de `references/mermaid-rules.md`. `scripts/render_diagrams.sh --batch <salida>` genera los SVG si hay `mmdc`. Si un diagrama falla 3 veces, sustitúyelo por una tabla. Los `.bpmn` se entregan como XML.

### Fase 6 — Resumen, inventario y guía

El orquestador escribe:

- `00-resumen-ejecutivo.md`, al final porque depende de todo lo anterior. Incluye el veredicto de 13 y el uso real.
- `INVENTARIO.md`, con la cobertura de la extracción.
- `LEEME.md`, con la guía de lectura por perfil y lo que no se pudo obtener.

Usa las plantillas de `assets/markdown-templates/`.

### Fase 6.5 — summary.json

`python3 scripts/build_summary.py <salida>` → `<trabajo>/summary.json` (lo usan los publicadores).

### Fase 7 — Publicación opcional

Según `output_preferences.json`: `agents/pdf-publisher.md` → `EXPORT.pdf`; `agents/dashboard-publisher.md` → `dashboard/index.html`. Pueden ir en paralelo.

### Fase 8 — Validación y respuesta

Pasa la validación final (abajo) y responde con la plantilla de `references/response-format.md`.

---

## Entregables

```
<salida>/
├── LEEME.md
├── 00-resumen-ejecutivo.md
├── 01-funcional.md                 ┐
├── 02-arquitectura.md              │
├── 03-modelo-datos.md              │
├── 04-seguridad-grupos.md          │  A. Cómo está hecha
├── 05-integraciones-consumidas.md  │     (onboarding y mantenimiento)
├── 06-apis-expuestas.md            │
├── 07-batches.md                   │
├── 08-procesos-bpmn/  (.bpmn + .mmd + .md por proceso, indice.md)
├── 09-valor-adicional.md           │
├── 10-pantallas.md                 │
├── 11-reglas-negocio.md            ┘
├── 12-especificacion-reconstruccion.md  ┐ B. Reconstruir y
├── 13-modernizacion-refactor.md         ┘    modernizar
├── INVENTARIO.md
└── diagrams/

appian-docs/_trabajo/<PREFIJO>/   = <trabajo>: datos en bruto, NO compartir
```

## Recursos (cárgalos cuando toque, no todos a la vez)

| Archivo | Cuándo |
|---|---|
| `references/devmcp-setup.md` | Fase 0, si falta o falla algún MCP. |
| `references/analysis-workflow.md` | Al empezar: checklists por fase. |
| `references/lectura-mcp-raw.md` | Antes de la fase 4 (y lo leen todos los subagentes). |
| `references/execution-principles.md` | Antes de la fase 4. |
| `references/docs-mcp-usage.md` | Si hay Docs MCP. |
| `references/data-fabric.md` | Fase 2, paso 3. |
| `references/modernization-guide.md` | Lo usa `rebuild-architect`. |
| `references/appian-objects-guide.md` | Dónde está cada dato y heurísticas. |
| `references/bpmn-mapping.md`, `mermaid-rules.md`, `presentation-rules.md` | Al generar diagramas y documentos. |
| `references/security-rules.md` | Fase 3 y antes de escribir documentos. |
| `references/response-format.md` | Fase 8. |
| `agents/*.md` | Como prompt de cada subagente. |
| `assets/markdown-templates/*.md` | Base de cada documento. |
| `scripts/devmcp_extract.py`, `devmcp_policy.json` | Fases 0–2. |
| `scripts/build_model.py`, `build_summary.py` | Fases 3 y 6.5. |
| `scripts/detect_secrets.sh`, `validate_mermaid.py`, `render_diagrams.sh` | Fases 3, 5 y 8. |

## Validación final (antes de responder)

1. Existen los 16 entregables. Los que no aplican llevan su frase de «no aplica» (p. ej. 07 sin batches).
2. `08-procesos-bpmn/` tiene `.bpmn`/`.mmd`/`.md` por cada process model y `indice.md` los lista todos.
3. Todos los diagramas pasan `validate_mermaid.py` o están sustituidos por tabla.
4. `bash scripts/detect_secrets.sh <salida>/*.md <salida>/08-procesos-bpmn <salida>/diagrams` no encuentra nada.
5. No quedan placeholders (`{{`, `TBD`, `xxx`, `lorem`).
6. Cada conclusión importante tiene evidencia `mcp:...` o está marcada como pendiente con responsable.
7. `INVENTARIO.md` cubre el 100 % de `inventory.json`.
8. Todos los `PAN-xxx` y `RN-xxx` aparecen en la trazabilidad de `12`, y cada `MOD-xxx` de `13` tiene evidencia y fuente (o está marcado como heurística).
9. `LEEME.md` dice qué no estuvo disponible (MCP opcionales, tipos sin definición, seguridad por objeto).
10. No se ha escrito nada fuera de `<salida>/` y `<trabajo>/`, y `<salida>/` no contiene datos en bruto.

Si algo falla, corrígelo y vuelve a validar antes de responder.
