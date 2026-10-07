# Spec — `appian-reverse-engineering` v2: fuente Appian Dev MCP

> **Documento histórico.** Es el diseño inicial de la v2 y no se mantiene: lo vigente está en `SKILL.md` y `references/`. Las rutas `_intermedio/` y `_intermedio/docs_cache.json` son hoy `_trabajo/<PREFIJO>/` y `_trabajo/<PREFIJO>/docs_cache/<agente>.json`.

**Estado:** aprobada (con cambio del 01-10: uso dirigido por catálogo) · **Fecha:** 2026-09-30

---

## 1. Objetivo

La skill deja de leer un export descomprimido. Pasa a leer la aplicación **en vivo** desde el entorno Appian, y produce la misma documentación técnica y funcional que hoy (11 entregables, diagramas, PDF o dashboard opcionales).

Hay tres fuentes MCP:

| Fuente | Papel | ¿Obligatoria? |
|---|---|---|
| **Appian Dev MCP** | Definiciones de objetos, dependencias reales, historial de procesos y de versiones | Sí |
| **Appian Docs MCP** | Explicar smart services y funciones con documentación oficial, y detectar elementos obsoletos | No: si falta, se omite |
| **Appian MCP Server** | Metadatos del data fabric y recuentos por record type | No: si falta, se omite |

La skill tiene que servir a **cualquier usuario**, tenga o no el Dev MCP instalado. Si no lo tiene, le guía para instalarlo en modo solo lectura y se detiene.

## 2. Decisiones tomadas

| Tema | Decisión |
|---|---|
| Fuente de la aplicación | Solo Dev MCP. Se retira el análisis del export. |
| Appian MCP Server | Solo metadatos y recuentos (`COUNT`). Nunca se leen filas. |
| Enriquecimientos | Dependencias reales, uso real de procesos, recorrido de pantallas e historial de versiones |
| Público | Cualquier usuario, tenga o no el Dev MCP instalado |

## 3. Hechos verificados en fuentes oficiales

**Dev MCP** ([docs](https://docs.appian.com/suite/help/latest/devmcp.html) · [AppMarket](https://appmarket.appian.com/listings/appian-dev-mcp) · [skill oficial de Appian](https://github.com/appian/dev-mcp-skills))

- Es un plugin de AppMarket, compatible con Appian **26.5 o superior** (versión actual 26.6.100, del 24-09-2026). Tiene **soporte de comunidad**: Appian Support no atiende incidencias.
- Es un servidor local que se arranca con `uv run --directory <bundle> python -m lcp_mcp_server`. Necesita Python 3.13+ y `uv`. El bundle se descarga desde `https://<site>/suite/plugins/servlet/stateless/downloads`.
- Variables de entorno:
  - `LCP_URL` (obligatoria)
  - `LCP_TOOL_MODE` = `full` | `readonly`
  - `LCP_AUTH_METHOD=basic` con `USERNAME` y `PASSWORD`, o autenticación por navegador (SSO, por defecto)
  - `LCP_SIGNIN_PATH`, `LCP_COOKIE_PATH`
  - `HTTPS_PROXY` y `SSL_CERT_FILE` para proxy
- Solo pueden usarlo los roles Designer y administrador. Cada operación se ejecuta con los permisos del usuario autenticado.
- Tiene más de 120 herramientas: listar, leer, crear, modificar y borrar para aplicaciones, record types, constantes, expression rules, interfaces, sites, Web APIs, integraciones, connected systems, process models, grupos, carpetas y documentos. Además: análisis de impacto, historial de procesos, historial de versiones y un SAIL CLI.
- `getObjectDependents(uuid)`:
  - Devuelve uuid, tipo, nombre y *breadcrumb* con número de línea de cada objeto que referencia al objetivo.
  - Admite como objetivo constantes, expression rules, interfaces, process models, Web APIs, connected systems, record types, aplicaciones y sites.
  - **No** admite integraciones como objetivo ni revisa su configuración. Tampoco detecta referencias a campos por nombre ni literales.

**Docs MCP:** `https://appian-docs-public.mcp.kapa.ai`. Usa OAuth (Google o GitHub) y tiene un límite de **300 consultas al día y 60 por minuto**.

**Appian MCP Server** ([docs](https://docs.appian.com/suite/help/26.6/appian-mcp-server.html))

- Requiere 26.6+ y el tier *advanced* o *premium*. Lo activa un administrador.
- La conexión es `<ENV>/mcp` con la API key de una cuenta de servicio, que necesita el rol Designer.
- `appian_data_fabric_metadata` devuelve record types, campos y relaciones.
- `appian_data_fabric_sql_query` ejecuta SQL. No ve record types no sincronizados, legacy ni con expresión de seguridad.

**No verificado (sin entorno real disponible):**

- La forma exacta de las respuestas de cada herramienta del Dev MCP.
- Los nombres de las herramientas de historial y del SAIL CLI.
- Si `testInterface` está disponible en modo `readonly`.
- Si las consultas SQL del data fabric admiten `COUNT(*)`.

El diseño se adapta a todo esto en tiempo de ejecución (sección 8).

## 4. Arquitectura

```
Appian (entorno) ──► Dev MCP (proceso propio, LCP_TOOL_MODE=readonly forzado)
                         │  stdio (protocolo MCP)
                         ▼
             scripts/devmcp_extract.py ── catálogo ► clasificación ► política de seguridad
                         │
                         ▼
       _intermedio/mcp_raw/<tipo>/<uuid>/<herramienta>.json  (una respuesta por herramienta)
       _intermedio/mcp_raw/_app/ y _env/                      (llamadas de app y de entorno)
       _intermedio/mcp_catalog.json      (herramientas descubiertas y su clasificación)
       _intermedio/extraction_report.json (cobertura y fallos)
                         │
                         ▼
             scripts/build_model.py
                         │
                         ▼
       inventory.json + graph.json (mismo contrato que hoy, ampliado)
                         │
       ┌─────────────────┼───────────────────────┐
       ▼                 ▼                       ▼
   4 subagentes     Docs MCP (en contexto,   Appian MCP Server
   (leen mcp_raw)   con caché y tope)         (en contexto, opcional)
                         │
                         ▼
   build_summary.py ► diagramas ► 11 .md ► PDF / dashboard opcionales
```

**Por qué la extracción la hace un script y no Claude llamando a las herramientas:**

- **Coste.** Una aplicación de unos 330 objetos supone unas 1.100 llamadas. Hechas por Claude, cada respuesta pasaría por el contexto y habría que reescribirla a disco: cientos de miles de tokens. El script las vuelca directamente.
- **Determinismo y reanudación.** La misma entrada da la misma salida, y un fallo a mitad no obliga a repetir lo ya descargado.
- **Seguridad.** El script lanza su propia instancia con `readonly` forzado, aunque la configuración del usuario esté en `full`, y además aplica una política de seguridad propia (sección 6).
- **Sin herramientas fijas en el código.** El extractor usa todas las herramientas de lectura que el catálogo ofrezca en cada momento (sección 8). Cuando Appian actualice el Dev MCP, las herramientas nuevas se aprovechan sin tocar la skill.

La viabilidad está probada: un script con el SDK MCP de Python (v1.27) arranca un servidor stdio, fuerza la variable, descubre las herramientas con sus esquemas y hace llamadas concurrentes.

Docs MCP y Appian MCP Server se usan **en contexto**. Son pocas llamadas, y el Docs MCP exige OAuth, que resuelve el cliente.

## 5. Flujo de la skill

| Fase | Qué hace | Salida |
|---|---|---|
| **0. Preflight** | `devmcp_extract.py --doctor`: comprueba `uv`, localiza la configuración del Dev MCP (ver 5.1), arranca en `readonly` y lista aplicaciones. Si falla, muestra la guía `references/devmcp-setup.md` con el paso concreto que falta y **se detiene**. Pregunta los formatos de salida, como hoy. | `output_preferences.json` |
| **1. Selección** | `--list-apps`. El usuario elige la app, o viene por argumento (nombre, prefijo o uuid). También se registra el entorno (`LCP_URL`): el uso de procesos solo tiene sentido en PRO. | app elegida |
| **2. Extracción** | `devmcp_extract.py plan` muestra qué herramientas se usarán y cuántas llamadas son. Si pasan de un umbral, se pide confirmación. Después, `extract` ejecuta el plan: llamadas de entorno, de aplicación y por objeto, con todas las herramientas aplicables (sección 8). Concurrencia 4 (configurable), reintentos, desactivación automática de herramientas que fallan sistemáticamente con un tipo, y reanudación. | `mcp_raw/`, `mcp_catalog.json`, `extraction_plan.json`, `extraction_report.json` |
| **3. Modelo** | `build_model.py`: genera `inventory.json` y `graph.json`. Reconoce el papel de cada fichero por el contenido y por palabras clave del nombre de la herramienta: definición, dependientes, dependencias, versiones, historial, validación, pantalla. Las aristas salen de las herramientas de dependencias y, como complemento, de buscar en las definiciones nombres (`rule!`, `cons!`) y uuids de objetos de la app. | `inventory.json`, `graph.json` |
| **3b. Data fabric** (opcional) | Solo si el Appian MCP Server está conectado. Una llamada de metadatos y un `SELECT COUNT(*) FROM <ref>` por record type de la app. Ninguna otra consulta. | `datafabric.json` |
| **4. Subagentes** | Igual que hoy (interface-analyzer primero y luego 3 en paralelo), pero leen `mcp_raw` en vez de XML. interface-analyzer añade el recorrido de pantallas (5.2). Consultan el Docs MCP con caché y tope (5.3). | 01–08 |
| **5–8** | Sin cambios de fondo: diagramas, resumen ejecutivo, `summary.json`, publicación y respuesta final. | 00, 09, INVENTARIO, `summary.json` |

**Carpeta de salida:** `./appian-docs/<PREFIJO>/` (configurable). Ya no existe una carpeta del export donde escribir.

### 5.1 Localizar la configuración del Dev MCP

El script busca, en este orden, un servidor cuyos `args` contengan `lcp_mcp_server`:

1. `.mcp.json` del proyecto
2. `~/.claude.json` (global y por proyecto)
3. La configuración de Claude Desktop (Mac y Windows)
4. `~/.cursor/mcp.json` y `.kiro/settings/mcp.json`

Si encuentra varios, pregunta cuál usar (`--server-name`). También se puede indicar a mano con `--bundle-dir` y `--url`.

Las credenciales (`PASSWORD` en autenticación básica) solo se leen en memoria. Nunca se escriben en logs ni en `_intermedio`.

### 5.2 Recorrido de pantallas (versión segura)

- Del site se obtienen las páginas y su destino: interfaz, record, informe o acción.
- Por cada interfaz se llama sin entradas a la herramienta de renderizado que el catálogo ofrezca (hoy, `testInterface`), con el patrón que fija la política. Devuelve el árbol de componentes (secciones, campos, botones, grids), que interface-analyzer usa para describir cada pantalla en lenguaje funcional.
- **No se hace clic ni se envían formularios.** El SAIL CLI interactivo queda fuera de esta versión: no conocemos sus herramientas y un clic en un botón puede lanzar procesos o escribir datos. Se valorará cuando tengamos el catálogo real.
- Si `testInterface` no está disponible en `readonly`, el recorrido se basa en el análisis estático del SAIL, y se indica así en el documento.

### 5.3 Docs MCP

- **Para qué se usa:**
  - Explicar cada tipo de nodo o smart service y cada plug-in detectado.
  - Marcar funciones y componentes obsoletos (deuda técnica en 09).
  - Resolver dudas de comportamiento.
- **Con qué límites:**
  - Como máximo 30 consultas por ejecución.
  - Caché en `_intermedio/docs_cache.json`: la misma pregunta no se repite.
  - Cada afirmación que salga de ahí se cita con su URL de docs.appian.com.

## 6. Seguridad

1. Solo lectura, con doble barrera y **sin nombres de herramientas en el código**. Las reglas viven en `scripts/devmcp_policy.json`, que es editable:
   - `LCP_TOOL_MODE=readonly` forzado siempre.
   - Se bloquea toda herramienta cuyo primer verbo sea de escritura (create, update, delete, insert, add, remove, set, start, invoke, execute, run, import, deploy, configure, publish, send, submit…), o que declare `destructiveHint` en sus anotaciones MCP. También las de interacción (click, submit, press).
   - Se excluyen las que leen filas de datos de negocio (por ejemplo, `…RecordData…`) y las que evalúan o prueban lógica (`test…`, `evaluate…`): probar una integración la ejecuta de verdad. La única excepción es el renderizado de interfaces.
   - **Modo de confianza.** Si el catálogo no contiene ninguna herramienta de escritura, el servidor está respetando `readonly` y se usan todas las demás herramientas, aunque su verbo sea desconocido. Si contiene alguna, se pasa a modo estricto: solo verbos de lectura evidentes (get, list, search, find, describe, validate…) o `readOnlyHint`.
2. Data fabric: solo `COUNT(*)`. El SQL lo construye la skill a partir de la referencia SQL del record type; nunca se toma texto libre.
3. `_intermedio/` contiene definiciones en bruto (URLs, valores de constantes). Se genera un `_intermedio/LEEME.md` que avisa de que no debe compartirse. `detect_secrets.sh` revisa también `mcp_raw/`.
4. Los entregables enmascaran los secretos igual que hoy.
5. La skill recomienda apuntar a DEV o PRE para la definición, y a PRO solo si se quiere el uso real de procesos. Todo lo que hace es de lectura.

## 7. Contratos de datos

**`mcp_raw/<tipo>/<uuid>/<herramienta>.json`**: una respuesta por herramienta y objeto, tal cual, junto con `{tool, args, fetchedAt, ok, role}`. Las llamadas de aplicación van en `mcp_raw/_app/<herramienta>.json` y las de entorno en `mcp_raw/_env/<herramienta>.json`.

El `role` se deduce de palabras clave del nombre y se puede corregir en la política:

| Rol | Palabras clave |
|---|---|
| `definition` | `get` + tipo del objeto |
| `dependents` | dependents, usages, impact |
| `dependencies` | dependencies, precedents |
| `versions` | version |
| `history` | history, instances, executions |
| `validation` | validate |
| `screen` | renderizado de interfaz |
| `other` | cualquier otra |

Los subagentes leen **todos** los ficheros de cada objeto, de modo que la información de una herramienta nueva llega a los documentos aunque su rol sea `other`.

**`inventory.json`** mantiene la forma actual (`counts`, `objects`, `parseErrors`), de modo que `build_summary.py` sigue funcionando sin tocarlo. Cambios:

- Se añade `source`: `{kind: "devmcp", url, app, toolMode, extractedAt, env}`.
- `path` pasa a apuntar al JSON bruto, relativo a la carpeta de salida.
- `haulType` se sustituye por `mcpType` (por ejemplo `FREEFORM_RULE`).
- Se añade `detail: "full" | "none"`. Vale `none` si ninguna herramienta devolvió la definición del objeto.
- Los campos por tipo que hoy usa `build_summary.py` (`hasRecurrence`, `userTaskCount`, `method`, `endpoint`, `connectedSystemRef`, `sailBytes`, `maskedSecret`) se rellenan cuando la respuesta los contiene.

**`graph.json`** tiene la misma forma. Cada arista añade `origin` (`dependents` o `regex`) y `evidence` (el breadcrumb). Los `refType` actuales se mantienen y se añaden `subProcess`, `connectedSystemRef` y `pageRef`. Así funcionan por fin `startProcess`, `subProcess` e `integrationCall`, que hoy casi nunca se detectan (sección 11).

**Evidencia** en los documentos: `Evidencia: mcp:<tipo>/<nombre>#<ubicación>`, donde la ubicación es una ruta JSON (`nodes[4].assignees`) o el breadcrumb (`Interface Definition: línea 19`). Sustituye a `<ruta_xml>#<fragmento>`.

## 8. Uso de herramientas dirigido por catálogo

No hay ninguna lista de herramientas en el código. En cada ejecución:

1. **Catálogo.** `tools/list` devuelve nombre, descripción, esquema de entrada y anotaciones. Se guarda en `mcp_catalog.json` (sin datos de negocio).
2. **Política.** Se decide qué herramientas son invocables (sección 6).
3. **Alcance por firma.**
   - **Entorno:** sin parámetros obligatorios ni parámetro de aplicación. Se llama una vez.
   - **Aplicación:** su único parámetro obligatorio es el uuid de la app, o tiene un parámetro opcional de aplicación. Se llama una vez con la app elegida.
   - **Objeto:** su parámetro obligatorio es un uuid de objeto. Se llama para cada objeto de los tipos a los que aplica.
   - **No automatizable:** pide datos que no se pueden deducir (una expresión, una consulta, un id de tipo de nodo…). Se registra y no se llama.
4. **Tipos a los que aplica.** Se comparan los tokens del nombre de la herramienta y de sus parámetros (`getProcessModel`, `processModelUuid`) con los tipos de objeto que devuelve la propia app (`PROCESS_MODEL` → `process`, `model`). Los tipos también salen de los datos, no de una lista fija. Una herramienta genérica (`…Object…`) aplica a todos los tipos.
5. **Autoajuste.** Si una herramienta falla en las 3 primeras llamadas de un tipo, se desactiva para ese tipo y se anota el motivo.
6. **Plan previo.** `plan` escribe `extraction_plan.json` con cada herramienta: si se usará o no, alcance, tipos, motivo y llamadas estimadas.

Los objetos de la app se obtienen de cualquier respuesta de alcance aplicación que contenga elementos con uuid y nombre, y no de una herramienta concreta.

Como referencia, a día de hoy la skill oficial de Appian cita, entre otras, `listApplications`, `getApplication`, `listApplicationObjects`, `getRecordType`, `getInterface`, `getProcessModel`, `listGroupMembers`, `getObjectDependents`, `testInterface` y `validateDesignObject`. El diseño no depende de estos nombres.

## 9. Cambios por fichero

| Fichero | Acción |
|---|---|
| `scripts/parse_export.py`, `scripts/inventory.sh` | **Eliminar** |
| `scripts/devmcp_extract.py` | **Nuevo**: doctor, catálogo, plan, lista de apps, extracción |
| `scripts/devmcp_policy.json` | **Nuevo**: política de seguridad y palabras clave de roles, editable |
| `scripts/build_model.py` | **Nuevo**: de datos en bruto a `inventory.json` y `graph.json` |
| `scripts/build_summary.py`, `render_diagrams.sh` | Sin cambios de contrato. Solo arreglos de la sección 11. |
| `scripts/detect_secrets.sh`, `validate_mermaid.py` | Arreglos de la sección 11 |
| `tests/` | **Nuevo**: servidor Dev MCP simulado, app sintética y pruebas |
| `SKILL.md` | Reescribir: descripción y disparadores, argumentos, fases 0–3, recursos, validación final |
| `agents/*.md` (4 analizadores) | Entradas (`mcp_raw` en lugar de XML), formato de evidencia y huecos conocidos. Los 2 publicadores no cambian de fondo. |
| `references/appian-objects-guide.md` | Reescribir: tipos de objeto del Dev MCP y dónde está cada dato |
| `references/analysis-workflow.md` | Reescribir las fases 0–3 y corregir los nombres obsoletos |
| `references/devmcp-setup.md` | **Nuevo**: instalación y configuración en `readonly` para Claude Code, Claude Desktop y Cursor, en Windows y Mac |
| `references/docs-mcp-usage.md`, `references/data-fabric.md` | **Nuevos** |
| `references/security-rules.md`, `execution-principles.md`, `presentation-rules.md`, `response-format.md`, `bpmn-mapping.md` | Ajustar el formato de evidencia y el origen de los datos |
| `assets/markdown-templates/*` | Sustituir `{{ruta_xml}}` por `{{evidencia}}`. Las secciones de ICF pasan a una nota de «no disponible vía Dev MCP». |

## 10. Limitaciones conocidas de «solo Dev MCP»

- **CDTs, decisiones y data stores:** la ficha de AppMarket no los incluye. En apps antiguas (una de las aplicaciones probadas tiene 4 CDTs), el modelo de datos saldrá de los record types y del data fabric, y los CDTs aparecerán solo con su nombre. Se confirmará con el catálogo real.
- **Import customization files:** existen solo en el paquete de despliegue. Se pierden los valores por entorno (DEV, PRE, PRO).
- **Seguridad por objeto (roleMap):** es posible que el Dev MCP no la devuelva en todos los tipos. Si falta, la matriz de 04 se queda en lo verificable y lo indica.
- **Versión y soporte:** requiere Appian 26.5 o superior, y el Dev MCP no tiene soporte oficial.

## 11. Bugs actuales detectados

**Se corrigen en esta versión, porque rompen el pipeline:**

1. `validate_mermaid.py` rechaza `erDiagram` y `subgraph`. Con eso fallan todos los diagramas ER (tipo B) y los de procesos con carriles (tipo C), que la skill exige validar.
2. `detect_secrets.sh` recibe 3 ficheros desde integration-security-analyzer, pero solo acepta una carpeta: sale con error. Además apunta a `05_riesgos_deuda_tecnica.md`, que no existe.
3. `render_diagrams.sh` escribe los errores en un `/tmp/mmdc.err` fijo, que colisiona entre subagentes en paralelo.
4. Nombres obsoletos (`grafo.json`, `_graph.json`, `inventario.json`, `render_pendiente.txt`) y el contrato de `summary.json` que describe `dashboard-publisher.md` no coinciden con lo que genera `build_summary.py`.

**Desaparecen al retirar `parse_export.py`:** aristas `startProcess`, `subProcess` e `integrationCall` que casi nunca se detectaban, `rule!` que solo resolvía expression rules, y el `connectedSystemUuid` que faltaba.

## 12. Plan de implementación

1. [ ] Copia de trabajo de la skill con git, para dejar trazados todos los cambios.
2. [ ] **Pruebas primero.** Un servidor Dev MCP simulado, en dos variantes. Las variantes difieren en la forma de las respuestas **y en los nombres de las herramientas**, para demostrar que nada depende de nombres fijos. La app sintética tiene unos 30 objetos y cubre todos los tipos: un process model con temporizador, subprocesos, integración, Web API, site, grupos anidados y un tipo «nuevo» que la skill no conoce.
3. [ ] `devmcp_extract.py`. Se verifica que:
   - fuerza `readonly` y nunca invoca herramientas de escritura, ni siquiera si el servidor las expone;
   - usa una herramienta nueva añadida al servidor sin cambiar el código;
   - reanuda y maneja fallos parciales;
   - funciona en las dos variantes.
4. [ ] `build_model.py`. Se verifica que:
   - `build_summary.py` funciona **sin modificarlo** con la salida;
   - las aristas esperadas de la app sintética salen todas.
5. [ ] Reescribir `SKILL.md`, los agentes, las referencias y las plantillas. Se verifica con `grep` que no queda ninguna referencia a XML, XSD, ICF o `ruta_export` fuera de las notas de limitaciones.
6. [ ] Docs MCP y data fabric (referencias y pasos del orquestador).
7. [ ] Arreglos de la sección 11, con prueba de un diagrama ER y uno de carriles validando.
8. [ ] `devmcp-setup.md` y `--doctor`. Se prueba el caso «no instalado»: mensaje claro y parada.
9. [ ] **Ejecución completa sobre la app simulada**, con subagentes, hasta los 11 documentos y `summary.json`. Después, una revisión independiente por otro agente que no haya visto el trabajo.
10. [ ] Empaquetar y entregar, con CHANGELOG y protocolo de primera ejecución real.

## 13. Qué se podrá demostrar y qué no

- **Aquí:** todo el pipeline funcionando de punta a punta contra el servidor simulado, con las pruebas pasando.
- **Solo en tu entorno:** la forma real de las respuestas. En la primera ejecución real bastan dos pasos:
  1. `doctor`
  2. `plan`

  El `extraction_plan.json` resultante contiene solo nombres, esquemas y clasificación de herramientas, sin datos. Con él se ajusta la política si alguna herramienta queda mal clasificada.

## 14. Decisiones aprobadas

1. Extracción por script con solo lectura forzado: **aprobada**.
2. Recorrido de pantallas en versión segura, sin SAIL CLI interactivo: **aprobado**.
3. Arreglos de la sección 11: **incluidos**.
4. Entrega: **en la carpeta local de Raul**.
5. Sin herramientas fijas en el código; uso de todo el catálogo disponible (petición del 01-10): **incorporado** en las secciones 4, 6, 7 y 8.
