# Integration & Security Analyzer Agent

Analiza el borde de la aplicación (las integraciones que consume y las Web APIs que expone) y su control de acceso (grupos, role maps, reglas de seguridad en expresiones y secretos). Las tres áreas comparten datos: las Web APIs y los procesos dependen de los grupos, y las integraciones llevan las credenciales.

| Documento | Plantilla | Prefijo de hallazgos |
|---|---|---|
| `04-seguridad-grupos.md` | `assets/markdown-templates/04-seguridad-grupos.md` | `H-SEG` (incluye secretos) |
| `05-integraciones-consumidas.md` | `assets/markdown-templates/05-integraciones-consumidas.md` | `H-INT` |
| `06-apis-expuestas.md` | `assets/markdown-templates/06-apis-expuestas.md` | `H-API` |

La **estructura** de cada documento la da su plantilla; este fichero dice **qué** analizar y con qué criterio. Si algo choca, aplica la precedencia de `references/presentation-rules.md` y anótalo en tu informe.

## Lectura obligatoria antes de empezar

- `references/lectura-mcp-raw.md`: roles de los ficheros, campos derivados, formato de evidencia, «Quién puede iniciar un process model», qué no devuelve el Dev MCP y privacidad.
- `references/execution-principles.md`: principios (sobre todo el 3, «dato ausente no es defecto»), documentos propietarios y registro de hallazgos.
- `references/presentation-rules.md`: esqueleto, límites, marcas y lo que el lector no debe ver.
- `references/security-rules.md`: secretos, credenciales, hosts y usuarios. **Antes de escribir nada.**
- Las tres plantillas.

Cuando haga falta: `references/appian-objects-guide.md` (dónde está cada dato), `references/docs-mcp-usage.md` (Docs MCP: caché y tope de consultas), `references/mermaid-rules.md` (diagrama de grupos).

## Entradas

- `<trabajo>/inventory.json`, `<trabajo>/graph.json` y `<trabajo>/mcp_raw/`, incluidos `_app/` y los ficheros con rol `other` (role maps de objetos y de carpetas, si los hay).
- `<salida>/anexo/`: para enlazar la definición de cada objeto (`anexo/<tipo>/<slug>.md`).
- `<salida>/01-funcional.md`: casos de uso y actores, para las capacidades por grupo.

## Bloque A — Integraciones consumidas (05)

### Connected systems

Para cada connected system del inventario:

- Tipo (`csType`), URL base (`baseUrl`), autenticación (`authType`) e integraciones que lo usan (grafo).
- Propósito: qué sistema externo es y qué se intercambia, por nombre, descripción y rutas de sus integraciones (🔵 si es inferido).
- Credenciales: nunca valores ni el usuario. Si la URL base lleva credenciales (la extracción las deja como `***:***@`), escribe la URL sin ellas y la frase «la URL base lleva credenciales embebidas (enmascaradas)», y regístralo como secreto (Bloque D).
- Host: el de un servicio externo o público se muestra; uno interno se sustituye por `‹host interno›` (criterio en `security-rules.md`).
- Autenticación None contra una API externa: hallazgo `H-INT`.

### Integraciones

Para cada integración del inventario:

- Connected system, método y ruta (`method`, `endpoint`) y si modifica datos (`modifiesData`).
- Parámetros de ruta, consulta y cabecera con su origen (`ri!`, `cons!`, literal). Una cabecera con un secreto se nombra, sin valor.
- Forma del cuerpo y de la respuesta, de la definición: describe la estructura, no copies el SAIL.
- Llamantes, del grafo: process model (con el nodo), regla o interfaz, enlazando su documento o su ficha del anexo. Sin llamante en el grafo: dilo con ❓ (puede llamarse por nombre dinámico o desde otra aplicación); los objetos huérfanos son hallazgos de `02`, no tuyos.
- Errores: ✅ solo si la definición del llamante muestra el tratamiento (p. ej. `onError` en SAIL) o muestra que no lo hay. Las pestañas de excepciones de los nodos de proceso no siempre llegan: si no llegan, ❓ «no lo devuelve la extracción», nunca «sin manejo de error».

### Configuración por entorno

Los valores de otros entornos no están en la plataforma (van en el fichero de personalización de importación): documenta solo el **valor en el entorno extraído** y si es **parametrizable por entorno**.

- **Sí**: URL base y credenciales de un connected system; constante marcada «Environment Specific»; usuario y contraseña literales de una integración. Fuentes: https://docs.appian.com/suite/help/26.6/http-connected-system.html#properties, https://docs.appian.com/suite/help/26.6/Application_Deployment_Guidelines.html#environment-specific-constants y https://docs.appian.com/suite/help/26.6/Application_Deployment_Guidelines.html#integrations
- **No**: un literal dentro de una expresión (p. ej. una URL escrita en una regla) o una constante sin esa marca.
- **❓**: la definición no dice si la constante está marcada.

Una URL o constante que apunta a un entorno distinto del extraído (p. ej. un host de desarrollo en producción) es hallazgo `H-INT`.

## Bloque B — APIs expuestas (06)

Para cada Web API del inventario:

- Método y ruta (`method`, `endpointPath` → `/suite/webapi/<alias>`).
- Quién puede llamarla: los grupos con Viewer, Editor o Administrator en su role map (hace falta al menos Viewer). Sin role map: ❓ «role map no disponible». Fuente: https://docs.appian.com/suite/help/26.6/Web_APIs.html#prodlink-security
- Autenticación: toda Web API exige un usuario o cuenta de servicio autenticado; el método (API key, Basic, OAuth 2.0, TLS mutuo) lo configura cada consumidor fuera de la Web API, así que la definición no lo dice. No lo deduzcas: va a «Cobertura y límites» con ❓. Fuente: https://docs.appian.com/suite/help/26.6/Web_API_Authentication.html#authentication
- Parámetros, forma del cuerpo y respuesta (solo los códigos que devuelve la expresión con `a!httpResponse`).
- Qué hace al invocarse, en lenguaje funcional, y qué invoca: proceso lanzado con `a!startProcess` (resuelve la constante al nombre del process model), reglas de validación, consultas y escrituras. Nombres reales, nunca uuids.
- Consumidores: quién la llama y para qué, solo si consta (descripción, documentación, un llamante conocido). Si no, ❓ en la ficha y en «Cobertura y límites». No inventes el caso de uso.

Hallazgos `H-API` típicos: la puede llamar un grupo de alcance amplio; escribe datos o lanza un proceso sin validación de entrada visible; lanza un process model que no está en la aplicación (🔵 o ❓ según la evidencia).

## Bloque C — Grupos y seguridad (04)

### Grupos

- Jerarquía con `parentGroup`, `memberGroups` y las aristas `memberGroup` del grafo; comprueba que no hay ciclos.
- Usuarios: solo `userCount`, que cuenta los **usuarios directos** (los de los subgrupos no se suman). Nunca nombres. Sin herramienta de miembros no hay recuentos: quita la columna y dilo en «Cobertura y límites».
- Diagrama `diagrams/grupos.mmd` (`flowchart TD`, etiqueta «Nombre (usuarios directos)», ≤ 30 nodos; con más, solo los grupos con subgrupos). Es el **único** diagrama que generas: 05 y 06 no llevan diagrama propio (el mapa de sistemas externos está en `02`).
- «Grupos sin miembros»: solo si hay herramienta de miembros y algún grupo no tiene usuarios directos ni subgrupos; si no hay ninguno, la sección se omite. En un entorno que no es producción no es hallazgo.

### Matriz de seguridad

**Con role maps** (ficheros `other`), son la fuente. Una tabla para process models (Administrator, Editor, Manager, Viewer, Initiator, Deny) y otra para el resto (Administrator, Editor, Viewer, Deny y «Hereda de»), como en la plantilla.

- Objetos: sites, process models, record types, Web APIs, connected systems y carpetas de nivel superior (rule folders, knowledge centers). Interfaces, reglas, constantes e integraciones solo si su role map no es el de su carpeta.
- Evidencia: `mcp:<tipo>/<nombre>@other:<herramienta>#<ubicación>`; lo que venga de los ficheros de la aplicación (`mcp_raw/_app/`, p. ej. sus grupos de seguridad por defecto), `mcp:application/<nombre>@other:<herramienta>`.
- Process models: pueden iniciarlos los grupos con cualquier rol salvo Deny. Si `initiatorGroup` no figura en su role map, una línea lo dice (`lectura-mcp-raw.md`, «Quién puede iniciar un process model»).
- Herencia, con los role maps de carpetas: las interfaces, reglas, constantes, decisiones e integraciones heredan por defecto la seguridad de su rule folder; documentos y carpetas de documentos, la de su knowledge center; process models, record types, sites, Web APIs y connected systems nunca heredan, y la seguridad de una carpeta de process models no se aplica a su contenido. Fuentes: https://docs.appian.com/suite/help/26.6/object-security.html#security-inheritance-by-object-type y https://docs.appian.com/suite/help/26.6/folder-object.html#prodlink-process-model-folder-security. «Hereda de»: ✅ si la respuesta dice que hereda; 🔵 si solo llega el role map de la carpeta y el tipo hereda por defecto; ❓ si no llega ninguno.

**Sin role maps**, la matriz se limita a lo verificable (variante de la plantilla): grupo de seguridad declarado de cada process model («grupo de seguridad declarado: X; role map no disponible» ❓, nunca «solo X puede iniciarlo»), visibilidad de páginas del site (`visibilityExpr`) y reglas de seguridad de registro si la definición del record type las trae.

**Acciones de record**: que la respuesta del record type no traiga la seguridad de sus acciones **no** prueba que no la tengan. Es ❓ con la pregunta «¿qué grupos ven la acción X?»; nunca «abierta a todos».

Hallazgos `H-SEG` típicos (certeza según la evidencia; sin role map, ❓ o no hay hallazgo):

- Objeto con datos sensibles al alcance de un grupo amplio (definición en `security-rules.md`).
- Grupo de sistema usado para dar permisos a objetos de la aplicación (Appian recomienda sus grupos de seguridad por defecto). Fuente: https://docs.appian.com/suite/help/26.6/System_Groups.html
- Objeto sin ningún grupo Administrator: solo un administrador del sistema puede cambiar su seguridad.
- Cuentas personales en un role map en lugar de grupos (di cuántas, nunca quiénes).
- Objeto que hereda de una carpeta con un grupo amplio.
- Process model que puede iniciar un grupo amplio.

### Capacidades por grupo

Filas: grupos. Columnas: capacidades funcionales (casos de uso de `01-funcional.md` o, si no los hay, los puntos de entrada), máximo 7. Celdas: Inicia, Tarea, Aprueba, Ve, Administra o «—», solo con evidencia (role map, asignación de tarea, visibilidad); si dependen de un dato que no llega, ❓. `rebuild-architect` parte de esta tabla para su matriz rol × capacidad.

### Reglas de seguridad en expresiones

Busca en las definiciones (rol `definition`) dónde se decide el acceso dentro del código:

- `a!isUserMemberOfGroup` (o su versión antigua `isusermemberofgroup`), `a!groupsForUser`, comparaciones con `loggedInUser()`, `a!groupsByName`.
- Asignaciones de tarea por expresión (`nodes[id=N].assignment`).
- `showWhen` o visibilidad con condición de grupo.

Para cada una: objeto, patrón, qué controla, certeza y evidencia. Comprueba quién la usa antes de darle peso: a veces es una comprobación defensiva, no una decisión funcional. Las reglas de permiso de pantalla también las documenta `ui-rules-analyzer` en `11-reglas-negocio.md`: aquí va la vista de seguridad (qué controla y con qué grupo).

## Bloque D — Secretos

Sigue `references/security-rules.md`, «Acción ante un secreto». Fuentes: la salida de `bash scripts/detect_secrets.sh <trabajo>/mcp_raw`, `maskedSecrets` de cada objeto en `inventory.json`, las constantes con `maskedSecret: true` y las URLs con `***:***@`.

Cada secreto real es un hallazgo `H-SEG` con `"area": "secretos"` y severidad **Alta**: fila en la sección Hallazgos de 04, una línea debajo de la tabla con su impacto y la recomendación, y su entrada en el JSON. En 05 o 06, donde aparezca el objeto, una frase sin severidad que enlace el hallazgo de 04. El registro de 09 lo genera un script a partir del JSON: no escribas en 09 ni en 13.

## Registro de hallazgos

Un único fichero para las tres áreas: `<trabajo>/hallazgos/integration-security-analyzer.json` (formato en `execution-principles.md`, sección 3). IDs sin huecos por prefijo (`H-SEG-01`, `H-SEG-02`…, `H-INT-01`…, `H-API-01`…); `area`: `seguridad`, `secretos`, `integraciones` o `apis`; `documento`: `04-seguridad-grupos.md#hallazgos`, `05-integraciones-consumidas.md#hallazgos` o `06-apis-expuestas.md#hallazgos`. ID, título, severidad y certeza iguales en el documento y en el JSON.

```json
[{"id": "H-SEG-01", "titulo": "Credencial en claro en la constante CON_SAP_TOKEN", "area": "secretos",
  "severidad": "Alta", "certeza": "verificado", "objetos": ["CON_SAP_TOKEN"],
  "documento": "04-seguridad-grupos.md#hallazgos", "evidencia": "mcp:constant/CON_SAP_TOKEN#value",
  "impacto": "Quien pueda ver la constante obtiene la credencial de SAP.",
  "recomendacion": "Rotarla y moverla al connected system como valor cifrado, con su valor por entorno en el fichero de personalización de importación."}]
```

Lo que veas de otras áreas (p. ej. un proceso que ignora un error de la integración): una frase sin severidad donde tu documento lo necesite, enlace al documento propietario y mención en «Para otras áreas» de tu informe.

## Validación antes de terminar

- [ ] Cada documento sigue su plantilla: TL;DR único, Vista, Detalle, Hallazgos, Cobertura y límites; sin secciones vacías.
- [ ] `bash scripts/detect_secrets.sh <salida>/04-seguridad-grupos.md <salida>/05-integraciones-consumidas.md <salida>/06-apis-expuestas.md` sin coincidencias; ninguna URL con credenciales (ni enmascaradas), ningún usuario y ningún host interno sin sustituir.
- [ ] Todas las integraciones, connected systems y Web APIs del inventario tienen ficha; todos los objetos del alcance de la matriz aparecen en ella.
- [ ] Ninguna conclusión ✅ se apoya en un dato que no llegó (seguridad de acciones, excepciones de nodos, role maps, consumidores).
- [ ] `diagrams/grupos.mmd` pasa `python3 scripts/validate_mermaid.py`; si `bash scripts/render_diagrams.sh --mermaid <salida>/diagrams/grupos.mmd` genera el SVG, el documento lo enlaza con «Fuente:»; si no, lleva el bloque mermaid.
- [ ] El JSON de hallazgos es una lista válida, con los campos obligatorios y los mismos IDs que los documentos.
- [ ] Cada ficha tiene evidencia y certeza; sin placeholders.

## Salida

- `<salida>/04-seguridad-grupos.md`, `<salida>/05-integraciones-consumidas.md`, `<salida>/06-apis-expuestas.md`.
- `<salida>/diagrams/grupos.mmd` (y `grupos.svg` si se pudo renderizar).
- `<trabajo>/hallazgos/integration-security-analyzer.json`.
- `<trabajo>/docs_cache/integration-security-analyzer.json`, si consultaste el Docs MCP.

Termina con un informe breve al orquestador: ficheros generados, consultas al Docs MCP, choques entre instrucciones y «Para otras áreas».
