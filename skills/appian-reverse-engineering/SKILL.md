---
name: appian-reverse-engineering
description: "Ingeniería inversa de aplicaciones Appian: lee la aplicación en vivo por el Dev MCP, en solo lectura, y documenta cómo está hecha para que el equipo la entienda: funcional, arquitectura, datos, seguridad, integraciones, APIs, batches, procesos, pantallas, reglas de negocio, inventario y anexo con las definiciones, cada dato con su evidencia. Úsala para entender, documentar o hacer el onboarding de una aplicación Appian existente, o cuando se pida su modelo de datos, sus integraciones, procesos, pantallas o reglas, aunque no se diga «ingeniería inversa». No juzga ni propone cómo rehacerla (appian-refactorizacion), no escribe requisitos ni especificaciones (appian-functional-analyst), no dibuja (appian-diagramas-bpmn) y no crea ni modifica objetos."
---

# Appian Reverse Engineering (Dev MCP)

Lee una aplicación Appian **en vivo y en solo lectura** a través del Appian Dev MCP y documenta cómo está hecha, para el onboarding y el mantenimiento: `LEEME` (la entrada), `01`–`11`, `INVENTARIO` y el `anexo/` con las definiciones.

Todo con evidencia verificable (`mcp:<tipo>/<nombre>#<ubicación>`), certeza explícita (✅ verificado, 🔶 inferido, ❓ pendiente) y sin inventar. Lo que no se encuentra dice dónde se buscó, lo configurado no se toma por lo ejecutado y lo que no se pudo verificar queda registrado con lo que hace falta para resolverlo (NV). Los hallazgos tienen un ID y un registro único. Cada documento empieza por las preguntas que responde, y un hallazgo dice qué pasa y qué riesgo tiene, no qué hacer. La revisión empieza por lo que el equipo necesita saber y termina diciendo qué queda abierto.

## Principios de funcionamiento

- **Solo lectura, siempre.** La extracción la hace `scripts/devmcp_extract.py`, que arranca su propia instancia del Dev MCP con `LCP_TOOL_MODE=readonly` forzado y aplica la política de `scripts/devmcp_policy.json`: bloquea escritura, interacción, evaluación de lógica y lectura de datos (filas de record, SQL, variables de procesos, datos de tareas, usuarios y credenciales). La única evaluación permitida es el render de interfaces con entradas vacías, la versión segura del recorrido del site: Appian evalúa la interfaz en el servidor (puede ejecutar sus consultas de lectura) y la respuesta se guarda tal cual. **No llames tú a herramientas de escritura del Dev MCP** aunque estén en la sesión. Aparte del script y del data fabric de la fase 2, una llamada de lectura al Dev MCP o al Appian MCP Server solo responde a una pregunta de la revisión o a un NV (`references/execution-principles.md`, «Sin verificar»).
- **Sin herramientas fijas.** El extractor usa todas las herramientas de lectura que ofrezca el catálogo del servidor en cada momento, clasificándolas por su firma. Cuando Appian actualiza el Dev MCP, las herramientas nuevas se aprovechan solas.
- **Extracción por script, análisis por agentes.** El script vuelca todo a disco (miles de llamadas sin pasar por el contexto). Los subagentes leen esos ficheros.
- **Tres MCP, y solo esos.** Dev MCP es obligatorio. Appian MCP Server (volúmenes) y Docs MCP (documentación oficial) son opcionales: si faltan, se indica qué se pierde y se sigue. Ningún otro conector o servidor MCP de la sesión (finanzas, presentaciones, diseño, bases de datos…) interviene: no los llames, no los listes en el preflight y no pidas autorizarlos. El Appian MCP Server es el del mismo entorno que el Dev MCP (`<URL del entorno>/mcp`); el Docs MCP, el de la documentación de Appian.

## Cómo ejecutar los scripts

Desde la **carpeta del usuario** (donde está su configuración MCP, p. ej. `.mcp.json`), con la ruta absoluta de esta skill (`<skill>`):

```bash
uv run --no-project --with "mcp>=1.2,<2" python "<skill>/scripts/devmcp_extract.py" <subcomando> [opciones]
python3 "<skill>/scripts/build_model.py" <salida>
```

`uv` ya es requisito del Dev MCP; `--no-project` evita que adopte el `pyproject.toml` que pueda haber en la carpeta del usuario. `doctor`, `apps` y `plan` admiten `--json` (salida legible por máquina). Códigos de salida en la cabecera de `devmcp_extract.py`.

## Argumentos

| Argumento | Obligatorio | Por defecto |
|---|---|---|
| Aplicación (nombre, prefijo o uuid) | Sí; si no lo da, se elige de la lista en la fase 0 | — |
| Idioma | No | español |
| Carpeta de salida | No | `<p>/as-is/` si la carpeta tiene `proyecto.md` o el usuario da la del proyecto; si no, `./<PREFIJO>/as-is/` |

**Una carpeta.** Todo va en `<salida>`: los documentos y, en `<salida>/extraccion/` (`<trabajo>`, que los scripts deducen de `<salida>`), la extracción y los datos de trabajo (respuestas, inventario, grafo, cachés, resumen). Se trabaja en entornos controlados y no se oculta nada: la extracción se guarda tal cual la devuelve el Dev MCP, con los usuarios, los datos de la aplicación y los secretos, y con rutas cortas, para que el proyecto quepa en Windows y en OneDrive. Como está en el proyecto, al repetir o retomar la ingeniería inversa, en otra sesión o en otro equipo, no se vuelve a pedir lo que ya está. Una carpeta es de una aplicación y un entorno. Los documentos no enlazan `<trabajo>/` y las demás skills no lo leen.

---

## Flujo de trabajo

Detalle operativo y checklists en `references/analysis-workflow.md`. Crea una lista de tareas con las fases y ve marcándolas.

### Fase 0 — Preflight de los 3 MCP (obligatoria)

1. Ejecuta `uv run --no-project --with "mcp>=1.2,<2" python "<skill>/scripts/devmcp_extract.py" doctor --json --out <salida>` (deja su salida en `<trabajo>/preflight.json`, dentro del proyecto). Si trae `appsNote` (más de 50 apps), busca la del usuario con `apps --json`.
2. Comprueba en la sesión:
   - **Docs MCP**: si la sesión tiene sus herramientas (se reconocen como dice «Dudas de Appian»), haz **una** consulta de prueba corta; cuenta para el tope de `references/docs-mcp-usage.md`.
   - **Appian MCP Server**: si `doctor` dice `no_configurado` y la configuración tiene un Appian MCP Server con otra URL que `<entorno>/mcp`, repite `doctor` con `--mcp-server-name <nombre en la configuración>` (y úsalo también en `datafabric`); si no lo tiene pero en la sesión hay herramientas del data fabric de Appian, márcalo «disponible en sesión».
3. Muestra al usuario esta tabla (una fila por MCP): **estado · qué se pierde si falta · cómo activarlo** (sección correspondiente de `references/devmcp-setup.md`).
4. Si el Dev MCP no está `ok`: explica el paso concreto de `devmcp-setup.md` que falta y **detente**.
5. Con el Dev MCP `ok`, en una sola pregunta:
   - la aplicación, si no la ha dado (muéstrale las apps de `doctor`);
   - los formatos adicionales: *«Además de los documentos Markdown, ¿quieres 📄 PDF maquetado, 🖥️ dashboard web, o solo los .md?»* (sin respuesta: solo Markdown);
   - si el entorno (`url` de `doctor`) es producción y su versión de Appian, si la sabe: el uso real de procesos solo es representativo en producción. Todo es lectura, sea cual sea el entorno;
   - qué necesita saber el equipo de esta aplicación (sin respuesta: qué hace, cómo está hecha y qué riesgos tiene).
6. Añade a `<trabajo>/preflight.json` tus comprobaciones de sesión (`docsMcp.status: "operativo"` si respondió la consulta de prueba) y `environment: {url, isProduction, appianVersion}` (`null` lo que no se sepa). Las preferencias y las preguntas de la revisión, en `<trabajo>/output_preferences.json`, con este formato: `{"pdf": true|false, "dashboard": true|false, "preguntas": ["¿Qué hace la aplicación?", "¿Cómo está hecha?", "¿Qué riesgos tiene?"]}` (esas tres si no dice otras). Apunta la consulta de prueba del Docs MCP en `<trabajo>/docs_cache/orquestador.json`.

### Fase 1 — Plan de extracción

`uv run --no-project --with "mcp>=1.2,<2" python "<skill>/scripts/devmcp_extract.py" plan --app <app> --out <salida>`. Resume al usuario: objetos por tipo, herramientas que se usarán y excluidas (con motivo) y llamadas estimadas. Si `needsConfirmation` es `true`, pide confirmación antes de seguir.

### Fase 2 — Extracción

1. `uv run --no-project --with "mcp>=1.2,<2" python "<skill>/scripts/devmcp_extract.py" extract --app <app> --out <salida>` (añade `--yes` si el usuario confirmó un plan grande). Es reanudable: si se corta, repítelo. Para documentar de nuevo una aplicación que ha cambiado desde la extracción que ya hay, o la de otro entorno, añade `--refresh`: lo pide todo otra vez.
2. Revisa `extraction_report.json`. Si en `callStatsByRole.definition` las fallidas (`failed`) pasan del 20 % del total (`ok` + `failed`), díselo al usuario antes de seguir.
3. Data fabric (opcional, `references/data-fabric.md`): `uv run --no-project --with "mcp>=1.2,<2" python "<skill>/scripts/devmcp_extract.py" datafabric --out <salida>` si hay servidor en la configuración; si solo está en la sesión, hazlo desde la sesión; si no, sáltalo.

### Fase 3 — Modelo y anexo

1. `python3 <skill>/scripts/build_model.py <salida>` → `inventory.json` y `graph.json` (con la criticidad de cada proceso).
2. `python3 <skill>/scripts/build_annex.py <salida>` → `anexo/`: por objeto, la definición legible y el resto de respuestas (role map, dependientes, validación, ejecuciones, versiones, render); y `anexo/grafo.md`. Repítelo si cambia `<trabajo>/`.
3. `python3 <skill>/scripts/detect_secrets.py <trabajo>/mcp_raw` (o `bash <skill>/scripts/detect_secrets.sh`, que lo llama): da cada posible secreto escrito en la aplicación con su fichero y su propiedad. Cada uno es un hallazgo `H-SEG` o un falso positivo (`references/security-rules.md`, «Acción ante un secreto»). No cuenta referencias (`cons!`, `=ri!…`).

### Fase 4 — Análisis con subagentes

Lee antes `references/execution-principles.md`. Cada subagente recibe:

- el contenido de `agents/<rol>.md`, o su ruta absoluta con la orden de leerlo entero antes de empezar (si el subagente puede leer ficheros);
- la ruta de la skill (`<skill>`), para abrir los `references/` y `assets/` que cite su fichero y ejecutar los `scripts/`;
- la carpeta de salida y la de trabajo;
- el apartado «Dudas de Appian» de este fichero, si el Docs MCP está disponible y cuántas consultas le quedan (tope global de 30);
- el entorno, si es producción y la versión si se conocen;
- las preguntas de la revisión (`preguntas`), para que registren como NV lo que de su área no puedan responder;
- a process-modeler: si la sesión ofrece la skill `appian-diagramas-bpmn` (plugin appian-analisis-funcional), cárgala y pásale su carpeta para dibujar los procesos en draw.io editable; si no, usa su vía propia (`.bpmn` + Mermaid);
- la orden de no crear tareas en tu lista y de terminar con un informe breve: ficheros generados, consultas a la documentación (por el Docs MCP o por la web), choques entre instrucciones y «Para otras áreas».

Todos escriben sus hallazgos en su documento y en `<trabajo>/hallazgos/<agente>.json`, y lo que no pudieron verificar, con ❓ y su NV en el documento y en `<trabajo>/sin-verificar/<agente>.json` (`references/execution-principles.md`, «Registro de hallazgos» y «Sin verificar»).

| Paso | Subagente | Genera |
|---|---|---|
| 4.1 | `interface-analyzer` | `01-funcional.md`, `02-arquitectura.md` |
| 4.2 (en paralelo, un solo turno) | `data-modeler` | `03-modelo-datos.md` |
| | `integration-security-analyzer` | `04`, `05`, `06` |
| | `process-modeler` | `08-procesos-bpmn/` |
| | `ui-rules-analyzer` | `10-pantallas.md`, `11-reglas-negocio.md` |
| 4.3 | orquestador | `07-batches.md`, `09-valor-adicional.md` y el registro de hallazgos (ver abajo) |

**Paso 4.3 (orquestador).** `python3 <skill>/scripts/build_summary.py <salida>` para ver `signals` (procesos sin ejecuciones, avisos de validación, interfaces grandes, huérfanos). Escribe `07` y `09` con sus plantillas (guía en `references/analysis-workflow.md`), tus hallazgos `H-BAT`/`H-GEN` en `<trabajo>/hallazgos/orquestador.json` y tus NV en `<trabajo>/sin-verificar/orquestador.json`. Después `python3 <skill>/scripts/build_registry.py <salida>`: valida todos los hallazgos y escribe la tabla del registro en `09`. Corrige lo que reporte (en el JSON del agente que corresponda).

**Patrón de invocación** (Claude Code): `Agent({description, subagent_type: "general-purpose", prompt: <agents/rol.md> + entradas})`, varios en el mismo mensaje cuando van en paralelo. Sin herramienta de subagentes: aplica tú mismo cada `agents/<rol>.md` en el mismo orden.

### Fase 5 — Diagramas

Cada bloque Mermaid pasa `python3 <skill>/scripts/validate_mermaid.py <fichero.mmd>`, que admite los tipos A, B y C de `references/mermaid-rules.md`. `bash <skill>/scripts/render_diagrams.sh --batch <salida>` genera los SVG si hay `mmdc` y avisa de los que son demasiado anchos (rehazlos). Si un diagrama falla 3 veces, sustitúyelo por una tabla. Los `.bpmn` de 08 llevan coordenadas de dibujo: `python3 <skill>/scripts/bpmn_layout.py <salida>/08-procesos-bpmn` (lo ejecuta process-modeler; repítelo si alguien toca un `.bpmn`). En la vía draw.io la imagen sale de `appian-diagramas-bpmn`, pero el `.bpmn` es el propio.

### Fase 6 — Coherencia, inventario y LEEME

1. **Pasada de coherencia** (`references/execution-principles.md`, sección 5): corrige en su sitio las contradicciones entre documentos, fusiona duplicados (hallazgos y NV) y quita severidades repetidas. Completa en `01`–`11` las menciones a otras áreas con el ID canónico del hallazgo o del NV y su enlace. Nada de notas de parche. Termina con `build_registry.py` sin errores.
2. `python3 <skill>/scripts/build_summary.py <salida>` → `<trabajo>/summary.json`, la fuente de las cifras de `LEEME` y de los publicadores.
3. Escribe con sus plantillas:
   - `INVENTARIO.md`: todos los objetos con su uuid, enlace al anexo y para qué sirven, y la cobertura de la extracción.
   - `LEEME.md`, la entrada a la documentación: de `summary.json`, las cifras, la confianza y su motivo, los procesos críticos, los hallazgos principales y el uso real; y las preguntas de esta revisión, por dónde empezar, cómo leer y lo que no incluye (cada línea, solo si es verdad en esta extracción).
4. `python3 <skill>/scripts/build_datos.py <salida>` → `<salida>/datos/`, lo que leen las demás skills (`references/datos.md`), y la tabla «Sin verificar» de `LEEME.md`. Si da error con un NV, corrígelo en el JSON de su agente y repítelo.

### Fase 7 — Publicación opcional

Según `output_preferences.json` (`pdf`, `dashboard`): `agents/pdf-publisher.md` → `EXPORT.pdf`; `agents/dashboard-publisher.md` → `dashboard/index.html`. Pueden ir en paralelo. Cada publicador recibe `<skill>`, `<salida>` y `<trabajo>`.

### Fase 8 — Validación y respuesta

1. Cierra cada pregunta de `preguntas` en «Preguntas de esta revisión» de `LEEME.md`: Respondida, con el enlace a donde se responde; Parcial o Sin resolver, con su NV o, si lo impide una limitación global, con el enlace a «Qué no incluye». Si para cerrarla registras un NV, vuelve a ejecutar `build_datos.py`.
2. Pasa la validación final (abajo), con `python3 <skill>/scripts/comprobar_asis.py <salida>` sin errores. Si para eso cambia algún documento y en la fase 7 se publicó algo, vuelve a publicarlo.
3. Responde con la plantilla de `references/response-format.md`: dice qué preguntas quedan abiertas.

---

## Entregables

```
<salida>/
├── LEEME.md
├── 01-funcional.md
├── 02-arquitectura.md
├── 03-modelo-datos.md
├── 04-seguridad-grupos.md
├── 05-integraciones-consumidas.md
├── 06-apis-expuestas.md
├── 07-batches.md
├── 08-procesos-bpmn/  (por proceso: .md + .bpmn + .mmd/.svg, o .drawio/.png/.json en la vía draw.io; indice.md)
├── 09-valor-adicional.md
├── 10-pantallas.md
├── 11-reglas-negocio.md
├── INVENTARIO.md
├── anexo/   (definiciones originales: indice.md + <tipo>/<slug>.md)
├── datos/   (inventario, dependencias, hallazgos, procesos y lo sin verificar, en JSON, para las demás skills)
├── diagrams/
└── extraccion/   = <trabajo>: la extracción, tal cual, y los datos de trabajo (no es un entregable)
```

## Dudas de Appian

Lo que no sepas con certeza de Appian se consulta en el MCP de documentación `appian-docs` (sus herramientas llevan `appian-docs` en el nombre o su descripción habla de buscar en la documentación de Appian) antes de escribirlo, nunca de memoria: si existe un componente, una función, un parámetro o un objeto, qué admite, sus límites, si depende de la licencia y desde qué versión.
- Una duda por consulta, escrita como una frase completa.
- Vale lo que diga la documentación de la versión del entorno del proyecto (va en la URL: `/help/26.6/`). Si solo lo dice una versión posterior, se avisa de que puede no estar disponible.
- Lo que se escribe a partir de la respuesta lleva su URL, en la forma `/latest/`.
- Sin el MCP, se consulta docs.appian.com con WebFetch o WebSearch. Si tampoco se puede, se escribe «sin verificar» y la duda pasa a pendientes.
- Qué conviene hacer (qué mecanismo elegir, cómo diseñarlo) no es una duda de documentación: se consulta en `appian-best-practices`, solo la sección que toca. Esa skill está junto a esta: `python3 <esta skill>/../appian-best-practices/scripts/seccion.py 02 4.8` imprime solo §4.8 del doc 02.

**En la ingeniería inversa**, las dudas típicas son qué hace un tipo de nodo, un smart service, una función o un componente que no conoces, si algo está deprecado y cómo se comporta un temporizador o una opción de seguridad. La versión del entorno es `environment.appianVersion` de `preflight.json`; si no consta, vale la documentación más reciente y `LEEME.md` lo dice. La URL acompaña a la afirmación como `Fuente: <URL>`; lo que quede sin verificar lleva ❓ y dice qué falta. El tope de consultas por ejecución y la caché que comparten los agentes están en `references/docs-mcp-usage.md`. Aquí no se pregunta qué conviene hacer: el orquestador y los agentes documentan hechos y no consultan `appian-best-practices` para proponer nada; eso lo hace `appian-refactorizacion`.

## Recursos (cárgalos cuando toque, no todos a la vez)

| Archivo | Cuándo |
|---|---|
| `references/devmcp-setup.md` | Fase 0, si falta o falla algún MCP. |
| `references/primera-ejecucion.md` | La primera vez contra un Appian real: comprobación sobre una aplicación pequeña. |
| `references/analysis-workflow.md` | Al empezar: checklists por fase. |
| `references/lectura-mcp-raw.md` | Antes de la fase 4 (y lo leen todos los subagentes). |
| `references/execution-principles.md` | Antes de la fase 4 (registro de hallazgos, sin verificar y pasada de coherencia). |
| `references/docs-mcp-usage.md` | Antes de consultar la documentación (tope y caché). |
| `references/data-fabric.md` | Fase 2, paso 3. |
| `references/datos.md` | Fase 6: el formato de `datos/`. |
| `references/appian-objects-guide.md` | Dónde está cada dato y heurísticas. |
| `references/bpmn-mapping.md`, `mermaid-rules.md`, `presentation-rules.md` | Al generar diagramas y documentos. |
| `references/security-rules.md` | Fase 3 y antes de escribir documentos. |
| `references/response-format.md` | Fase 8. |
| `agents/*.md` | Como prompt de cada subagente. |
| `assets/markdown-templates/*.md` | Base de cada documento. |
| `scripts/devmcp_extract.py`, `devmcp_policy.json` | Fases 0–2. |
| `scripts/build_model.py`, `build_annex.py` | Fase 3. |
| `scripts/build_registry.py`, `build_summary.py`, `build_datos.py` | Fases 4.3, 6 y 8. |
| `scripts/detect_secrets.py` (o `.sh`), `validate_mermaid.py`, `render_diagrams.sh`, `bpmn_layout.py`, `comprobar_asis.py` | Fases 3, 4, 5 y 8. |

## Validación final (antes de responder)

1. Existen `LEEME`, `01`–`11`, `INVENTARIO`, `anexo/indice.md` y `diagrams/`, y cada documento empieza por la línea «Responde a» de su plantilla. Los que no aplican llevan su frase de «no aplica» (p. ej. 07 sin batches).
2. `08-procesos-bpmn/` tiene por cada process model su `.md`, su `.bpmn` (con `bpmndi:BPMNDiagram`) y su diagrama (`.svg`/`.mmd`, o `.png`/`.drawio` con su `.json`, que es la especificación del dibujo y no datos en bruto), e `indice.md` los lista todos. Un proceso de más de 25 nodos se parte en `<slug>-1.mmd`, `<slug>-2.mmd`…: se admite `<slug>(-N)?.mmd` y `.svg`.
3. Todos los diagramas pasan `python3 <skill>/scripts/validate_mermaid.py` (o están sustituidos por tabla) y ninguno superó el aviso de ancho.
4. Cada posible secreto que encuentra `python3 <skill>/scripts/detect_secrets.py <trabajo>/mcp_raw`, y cada constante con `secret: true` en `inventory.json`, tiene su `H-SEG` en 04 o está descartado como falso positivo.
5. No quedan placeholders (`{{`, `TBD`, `TODO`, `lorem`) ni marcas fuera de la paleta (`🔴`, `🟡`, `⚠️`).
6. `build_registry.py` termina sin errores ni avisos de hallazgos que dicen qué hacer, y cada hallazgo de los documentos tiene su ID en el registro de 09.
7. `INVENTARIO.md` cubre el 100 % de `inventory.json`.
8. `LEEME.md` dice qué no estuvo disponible (MCP opcionales, tipos sin definición, seguridad por objeto), qué no se pudo verificar (tabla «Sin verificar», de `build_datos.py`) y cómo quedó cada pregunta de la revisión.
9. No se ha escrito nada fuera de `<salida>/`. Los datos en bruto solo están en `<salida>/extraccion/` y ningún documento enlaza esa carpeta.
10. `python3 <skill>/scripts/comprobar_asis.py <salida>` sale sin errores: nombres con el prefijo que no están en el inventario, certezas sin evidencia o con una evidencia que no lleva al anexo, cifras del volumen de LEEME distintas de `summary.json`, marcadores y enlaces rotos, NV citados que no están en `datos/` y preguntas de la revisión sin cerrar. Sus avisos (muletillas, frases largas, párrafos repetidos en dos documentos, documentos que pasan su presupuesto de palabras, «no existe» sin decir dónde se buscó, «según su nombre» en un objeto con definición, inferidos Alta con una sola evidencia en `base`, objetos de fuera de la aplicación sin NV) se corrigen.

Si algo falla, corrígelo y vuelve a validar antes de responder.
