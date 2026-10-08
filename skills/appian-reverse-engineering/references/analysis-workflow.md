# Flujo de análisis: checklists por fase

Detalle operativo de las fases de `SKILL.md`, que manda si algo no coincide. Marca cada casilla en tu lista de tareas. Incluye la guía de análisis de los dos documentos que escribe el orquestador (`07` y `09`).

**Convenciones**

- `<salida>` = `<p>/as-is/` si la carpeta es un proyecto (tiene `proyecto.md`) o el usuario da la del proyecto, y si no `./<PREFIJO>/as-is/`; `<trabajo>` = `<salida>/extraccion/` (la extracción, tal cual, y los datos de trabajo; ningún entregable lo enlaza).
- Scripts, desde la carpeta del usuario (donde está su `.mcp.json`): `uv run --no-project --with "mcp>=1.2,<2" python "<skill>/scripts/devmcp_extract.py" …`; los demás, `python3 <skill>/scripts/<script>.py <salida>`. `<skill>` es la carpeta de la skill.
- Evidencia: `mcp:<tipo>/<nombre>[@<rol>]#<ubicación>`, con los nodos de proceso como `nodes[id=N]` (`lectura-mcp-raw.md`).
- Hallazgos: ID con el prefijo del área, tabla en el documento propietario y `<trabajo>/hallazgos/<agente>.json` (`execution-principles.md`, secciones 2 y 3). Lo que no se pudo verificar: un NV con el mismo prefijo, en `<trabajo>/sin-verificar/<agente>.json` (sección 4).

---

## Fase 0 — Preflight

- [ ] `doctor --json` ejecutado. Con `appsNote` (más de 50 apps), la del usuario buscada con `apps --json`.
- [ ] Docs MCP: herramienta localizada y una consulta de prueba, apuntada en `<trabajo>/docs_cache/orquestador.json` (cuenta para el tope de 30).
- [ ] Appian MCP Server: estado según `doctor`, o «disponible en sesión» si sus herramientas están en la sesión.
- [ ] Tabla de estado mostrada al usuario (estado · qué se pierde · cómo activarlo).
- [ ] Si el Dev MCP no está `ok`: mostrado el paso de `devmcp-setup.md` que falta y **parada**.
- [ ] En una sola pregunta: aplicación, formatos adicionales, si el entorno es producción (con su versión de Appian, si la sabe) y qué necesita saber el equipo.
- [ ] `preflight.json` (con `environment: {url, isProduction, appianVersion}`) y `output_preferences.json` (`pdf`, `dashboard`, `preguntas`; formato en `SKILL.md`) guardados.

**Qué pierde el usuario sin cada MCP opcional**

| Falta | Consecuencia |
|---|---|
| Appian MCP Server | Sin volúmenes de datos: 03 no tiene filas por entidad. |
| Docs MCP | Las dudas se consultan en docs.appian.com por la web; si tampoco se puede, lo que depende de la documentación oficial se marca «sin verificar». |

## Fase 1 — Plan

- [ ] `plan --app <app> --out <salida>` sin errores.
- [ ] Resumen mostrado al usuario: objetos por tipo, herramientas usadas y excluidas (con motivo), llamadas estimadas.
- [ ] Si `trustedMode` es `false`: avisado de que el servidor no respeta `readonly` y de que solo se usan herramientas de lectura evidentes.
- [ ] Si `needsConfirmation`: confirmación del usuario.
- [ ] Herramientas `manual` o excluidas que parezcan útiles y seguras: anotadas para el usuario (puede ajustar `devmcp_policy.json`).

## Fase 2 — Extracción

- [ ] `extract` terminado. Si se corta, repetirlo: reanuda desde lo descargado. Si la aplicación ha cambiado desde la extracción que ya hay, o es la de otro entorno, `--refresh`: lo pide todo otra vez.
- [ ] `extraction_report.json` revisado: `errorCount`, `disabledAfterProbe`, `toolsExcluded`, `callStatsByRole`.
- [ ] Si en `callStatsByRole.definition` fallan más del 20 % de las llamadas: avisado al usuario antes de seguir.
- [ ] Data fabric: `datafabric.json` generado (script o sesión, ver `data-fabric.md`) o anotado como no disponible.

**Errores típicos**

| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| Código 13 al arrancar | Sesión SSO caducada o bundle mal instalado | Repetir: se abre el navegador. Si persiste, `devmcp-setup.md`. |
| Código 15 | Aplicación no encontrada o ambigua, o la carpeta ya tiene otra aplicación u otro entorno | Usar el uuid o el prefijo exacto de `doctor`; para otra aplicación, otra `<salida>`; para otro entorno, otra `<salida>` o `--refresh`. |
| Muchas llamadas de un tipo desactivadas | La herramienta no admite ese tipo | Normal. Aparece en el informe y en `INVENTARIO`. |
| Timeouts | Entorno lento | `--concurrency 2` y repetir (reanuda). |

## Fase 3 — Modelo y anexo

- [ ] `build_model.py <salida>` sin errores; revisada la línea de resumen (objetos, aristas por origen, huérfanos, hubs).
- [ ] `build_annex.py <salida>` → `<salida>/anexo/` (`indice.md` y `<tipo>/<slug>.md` por objeto con definición).
- [ ] `python3 <skill>/scripts/detect_secrets.py <trabajo>/mcp_raw`: anotado qué tipos de secreto hay y en qué objetos, para registrarlos como `H-SEG`.
- [ ] Si `graph.json` tiene pocas aristas de origen `dependents` (la herramienta de dependencias no estaba o falló), las conclusiones sobre quién llama a quién llevan 🔶.
- [ ] Nodos `external: true` de `graph.json` (`stats.externalNodes`): objetos de fuera que llama la aplicación, también los de un `rule!` o un `cons!` que no está en ella. Los documenta 02, con su NV.

## Fase 4 — Análisis

- [ ] `execution-principles.md` leído. Cada subagente recibe lo que lista `SKILL.md` (fase 4), incluidas las consultas a la documentación que le tocan, por el Docs MCP o por la web (reparto en `docs-mcp-usage.md`).
- [ ] 4.1 `interface-analyzer` → 01, 02.
- [ ] 4.2 en paralelo, en un solo turno: `data-modeler` (03), `integration-security-analyzer` (04–06), `process-modeler` (08), `ui-rules-analyzer` (10, 11).
- [ ] Cada agente dejó `<trabajo>/hallazgos/<agente>.json`, `<trabajo>/sin-verificar/<agente>.json` y su informe; sus «Para otras áreas» y choques, anotados para la fase 6.
- [ ] 4.3 orquestador: `build_summary.py <salida>` para ver `signals` → `07` y `09` con sus plantillas y las guías de abajo → hallazgos `H-BAT` y `H-GEN` en `<trabajo>/hallazgos/orquestador.json` y sus NV en `<trabajo>/sin-verificar/orquestador.json` → `build_registry.py <salida>` sin errores (lo que reporte se corrige en el JSON del agente que corresponda).
- [ ] Consultas a la documentación (suma de `<trabajo>/docs_cache/*.json`) ≤ 30.

### Guía de 07 (procesos programados)

Proceso programado = process model con `startType: timer` en `inventory.json`. Por cada uno, lee su definición (nodo de inicio y `schedule`), su `usage`, su `versions` y su documento de 08. Sin ninguno, 07 lleva solo el título y la frase de su plantilla.

- **Frecuencia**: traduce la configuración del temporizador a lenguaje natural («configurado para…», ✅) y, si es posible, a cron. Lo que no conste (hora, días) es ❓, no se supone. Si se ejecuta con esa frecuencia lo dicen las ejecuciones, no la configuración (`execution-principles.md`, principio 5): si la última ejecución no cuadra con la frecuencia, se dicen las dos cosas y queda un NV (`NV-BAT`).
- **Zona horaria**: la que fija el temporizador; por defecto, la del process model (`pp!timezone`). Si no consta, ❓. Fuente: https://docs.appian.com/suite/help/26.6/Intermediate_Event_-_Timer.html#configuring-the-time-zone-used
- **Próximas 3 ejecuciones**: calculadas desde la fecha de extracción (`source.extractedAt` de `inventory.json`) en la zona del temporizador. Si falta la zona o la hora, o la recurrencia es por intervalo sin hora de referencia, «no calculable» ❓.
- **Cuenta de ejecución**: un proceso que arranca un temporizador se ejecuta con la cuenta de quien desplegó el process model (Fuente: https://docs.appian.com/suite/help/26.6/Testing_and_Debugging_Problems_with_Process_Models.html#issues-that-return-process-errors). Si `versions` da el autor de la última versión, indícalo, con su tipo de cuenta y su grupo si constan (🔶: la última versión guardada no tiene por qué ser la desplegada); si no, ❓. No la deduzcas de las ejecuciones de la muestra.
- **Uso real**: `usage`. Con `failedInSampleOf`, «N fallos en las últimas M ejecuciones», nunca una tasa global. Si el entorno no consta como producción, las cifras son orientativas.
- **Volumen por ejecución**: identifica la consulta de origen (`a!queryRecordType`, `a!queryEntity`, una regla…; no supongas cuál) y su tamaño de lote (`pagingInfo`/`batchSize`). Cita el nodo: `nodes[id=N]`.
- **Manejo de errores**: lo que muestre la definición. El Dev MCP no devuelve las pestañas de excepciones y alertas de los nodos: su ausencia es ❓ «no lo devuelve la extracción», no «sin manejo de errores».

Hallazgos `H-BAT` (severidad orientativa; ajústala al impacto real). Los fallos de ejecución y los defectos del flujo de un batch son del proceso (`H-PRO`, en 08): 07 los cita por su ID.

| Situación | Severidad | Certeza |
|---|---|---|
| Lee sin tamaño de lote y la definición lo muestra | Media | ✅ |
| Programado y sin ejecuciones | No es H-BAT: cita el H-GEN de 09 (dueño de los procesos sin ejecuciones) | — |
| Usa `loggedInUser()`: no hay una persona detrás ([fuente](https://docs.appian.com/suite/help/26.6/fnc_people_loggedinuser.html)) | Media | ✅ |
| Intervalo de menos de una hora sobre integraciones o escrituras | Baja (vigilar) | ✅ |
| Sin manejo de errores | Solo si la definición muestra que no lo hay; si no, no es hallazgo (❓ en la ficha) | ✅ |

### Guía de 09 (valor adicional)

Solo las subsecciones con contenido. Hallazgos propios: `H-GEN` (áreas mantenimiento, rendimiento o uso). Lo que sea de otra área se enlaza por su ID; si el propietario no lo registró, anótalo para la pasada de coherencia.

- **Métricas** (Vista): de `inventory.json` (`counts`, `sailLines`, `sailBytes`, `nodeCount`, `validationIssues`, `usage`).
- **Configuración por entorno**: la única tabla de lo que cambia por entorno (05 la enlaza). Lleva la URL base y las credenciales de cada connected system y las constantes con URLs, hosts, identificadores o interruptores de entorno (`DEV`/`PRE`/`PRO`). Solo se ve el valor del entorno extraído; los de los demás van en el fichero de personalización de importación. «Por entorno»:
  - **Sí**: URL base y credenciales de un connected system; constante marcada «Environment Specific»; usuario y contraseña literales de una integración. Fuentes: https://docs.appian.com/suite/help/26.6/http-connected-system.html#properties, https://docs.appian.com/suite/help/26.6/Application_Deployment_Guidelines.html#environment-specific-constants y https://docs.appian.com/suite/help/26.6/Application_Deployment_Guidelines.html#integrations
  - **No**: un literal dentro de una expresión (p. ej. una URL escrita en una regla) o una constante sin esa marca.
  - **❓**: la definición no dice si la constante está marcada.

  Un valor que es un secreto (`secret`, `secrets`, `detect_secrets.py`) lleva en «Hallazgo» el `H-SEG` de 04; uno que apunta a otro entorno, el `H-INT` de 05.
- **Huérfanos**: `graph.orphans` (ya excluye puntos de entrada y procesos programados) y, solo si el entorno es producción, los process models sin ejecuciones (`signals`). Aquí va la lista; el hallazgo es el `H-ARQ` de 02. Los objetos muy referenciados (hubs) también son de 02.
- **Avisos de validación**: `validationIssues`; un `H-GEN` por tipo de aviso, agrupando objetos.
- **Versionado**: `versions` (`count`, `lastModifiedOn`, `lastModifiedBy`). El autor se escribe tal cual; clasifícalo como cuenta personal, de servicio o «tipo no determinado» y busca su grupo en los ficheros `members` de `mcp_raw`. Cuenta de servicio solo si su grupo o su nombre lo indican claramente (🔶).
- **Glosario de negocio**: términos de nombres y descripciones de records, campos, procesos y pantallas; ✅ si sale de una descripción de Appian, 🔶 si se deduce del nombre.

Hallazgos `H-GEN` (severidad orientativa):

| Situación | Severidad | Certeza |
|---|---|---|
| Aviso de validación de la plataforma (función obsoleta, referencia rota) | Media; Alta si rompe una funcionalidad | ✅ |
| Constante con un valor de entorno (URL, host) sin la marca «Environment Specific» (si apunta a otro entorno, es el `H-INT` de 05) | Media | ✅ o 🔶 |
| Process model de más de 50 nodos ([fuente](https://docs.appian.com/suite/help/26.6/appian-recommendations.html#process-model-design-guidance)) | Media | ✅ |
| Expression rule de más de 200 líneas o interfaz de más de 80 KB | Baja | ✅ |
| Process models sin ejecuciones (`signals`) | Baja | ✅ en producción; 🔶 «orientativo (ver LEEME)» si no consta como producción |

## Fase 5 — Diagramas

- [ ] Cada `.mmd` pasa `python3 <skill>/scripts/validate_mermaid.py <fichero.mmd>`.
- [ ] `bash <skill>/scripts/render_diagrams.sh --check`; con `mmdc`, `bash <skill>/scripts/render_diagrams.sh --batch <salida>`. Los que avise por ancho (más de ~1600 px) se rehacen: `flowchart TD`, menos cajas por fila o partidos en dos.
- [ ] Un diagrama que falla 3 veces se sustituye por su tabla equivalente.
- [ ] `bpmn_layout.py <salida>/08-procesos-bpmn` ejecutado (lo hace `process-modeler`; repítelo si alguien tocó un `.bpmn`).
- [ ] Cada diagrama aparece una sola vez en su documento: SVG con «Fuente: [x.mmd](…)», o el bloque mermaid si no hay SVG.

## Fase 6 — Coherencia, resumen, inventario y guía

- [ ] Pasada de coherencia (`execution-principles.md`, sección 5): contradicciones corregidas en su documento, duplicados de hallazgos y de NV marcados con `duplicadoDe`, severidades fuera del propietario quitadas, «Para otras áreas» registrados, menciones a otras áreas en 01–11 con el ID canónico y su enlace, sin notas de parche; al terminar, `build_registry.py <salida>` sin errores.
- [ ] `build_summary.py <salida>` → `<trabajo>/summary.json`.
- [ ] `00-resumen-ejecutivo.md` con su plantilla: todas las cifras de `summary.json` (confianza con su motivo, procesos críticos, hallazgos Alta con su evidencia y uso real con aviso de entorno).
- [ ] `INVENTARIO.md`: 100 % de `inventory.json`, con uuid, enlace al anexo, el «Para qué» de cada objeto (su descripción; si no la tiene, una frase de su definición, 🔶; «🔶 según su nombre» solo sin definición) y la cobertura de la extracción (herramientas usadas y omitidas, con el motivo).
- [ ] `LEEME.md`: las preguntas de esta revisión (las de `preguntas`), rutas por perfil, qué documento responde a cada pregunta (con los rangos reales de IDs), cómo leer, qué no incluye y términos de Appian (enlaces a su documentación).
- [ ] `build_datos.py <salida>` → `<salida>/datos/` y la tabla «Sin verificar» de LEEME. Un NV fuera de formato se corrige en el JSON de su agente y se repite.

## Fase 7 — Publicación opcional

- [ ] Según `output_preferences.json`: `pdf-publisher` y/o `dashboard-publisher`, en paralelo, con `summary.json` ya generado.

## Fase 8 — Validación y respuesta

- [ ] Cada pregunta de `preguntas`, cerrada en «Preguntas de esta revisión» de LEEME: Respondida (con el enlace a donde se responde), Parcial o Sin resolver (con su NV o, si lo impide una limitación global, el enlace a «Qué no incluye»). Si para cerrarla se creó un NV, `build_datos.py <salida>` otra vez.
- [ ] Validación final de `SKILL.md` superada.
- [ ] `comprobar_asis.py <salida>` sin errores y con sus avisos corregidos.
- [ ] Respuesta con la plantilla de `response-format.md`, que dice qué preguntas quedan abiertas.
