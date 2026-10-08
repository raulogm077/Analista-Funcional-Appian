<!--
  Plantilla 04 — Seguridad y grupos. Autor: integration-security-analyzer. Prefijo de hallazgos: H-SEG (incluye secretos).
  Los comentarios son instrucciones: no se copian al documento. Las secciones sin contenido se omiten.
  Objetivo: 2-3 pantallas (máximo 5).
  Cuentas personales en un role map: cuántas y cuáles. Un usuario escrito en el código o en una constante de tipo
  Usuario va con su grupo si aclara algo.
  Evidencia: siempre enlazada a la ficha del objeto en el anexo.
  «Cobertura y límites»: solo lo de este documento; lo global está en LEEME.
-->

# Seguridad y grupos

> **Responde a:** ¿Qué grupos hay y quién está en cada uno? ¿Quién puede ver, iniciar o administrar cada objeto? ¿Qué puede hacer cada grupo? ¿Dónde decide el código quién accede a qué? ¿Qué secretos hay escritos en la aplicación?

> **TL;DR**: {{quién accede a qué en 2-3 frases: grupos principales, cómo se controla el acceso (role maps, visibilidad, expresiones) y lo más importante que debe saber el lector}}.
> **Volumen**: {{N}} grupos ({{N}} de la aplicación, {{N}} de sistema), profundidad {{N}}, {{N}} objetos en la matriz ({{fuente: role maps / lo verificable sin role maps}}). **Hallazgos**: {{N (Alta: n)}} — principales: [H-SEG-01](#hallazgos), … {{o «sin hallazgos»}}.

## Vista

Jerarquía de grupos de la aplicación: cada flecha va del grupo padre al subgrupo; entre paréntesis, usuarios directos.

![Jerarquía de grupos](diagrams/grupos.svg)

Fuente: [grupos.mmd](diagrams/grupos.mmd)

<!--
  Sin SVG: bloque mermaid embebido (flowchart TD, idéntico al .mmd), nunca los dos.
  Más de 30 grupos: el diagrama solo con los grupos que tienen subgrupos; el resto, en la tabla.
  Tabla: ≤ 15 filas. Si hay más grupos, aquí los que aparecen en la matriz y el resto en INVENTARIO.md.
  "Usuarios directos" = userCount: no suma los usuarios de los subgrupos. Sin herramienta de miembros, sin la columna
  (y se dice en «Cobertura y límites»). Un grupo vacío (0 usuarios directos y 0 subgrupos) se ve aquí: en un entorno
  que no es producción no es hallazgo.
-->

| Grupo | Padre | Subgrupos | Usuarios directos | Para qué sirve |
|---|---|---|---|---|
| `{{DEM Administrators}}` | — | 0 | {{2}} | {{Administra los objetos de la aplicación}} |
| `{{DEM Gestores}}` | `{{DEM Users}}` | 0 | {{5}} | {{Tramita solicitudes y aprueba altas}} |

## Detalle

### Matriz de seguridad

<!--
  Fuente: role maps (ficheros con rol other), si llegan. Sin role maps, usa la variante "sin role maps" de más abajo y borra estas tablas.
  Objetos: sites, process models, record types, Web APIs, connected systems y carpetas de nivel superior (rule folders, knowledge centers).
  Interfaces, reglas, constantes e integraciones solo si su role map no es el de su carpeta.
  Celda: grupos con ese rol (máx. 4; si hay más, «5 grupos» y la lista en la ficha del anexo). Vacía: «—».
  Process models: todo sale de su role map, así que la tabla no lleva certeza; la evidencia de cada fila es ese role map.
-->

Process models: pueden iniciarlos los grupos con cualquier rol salvo Deny ([fuente](https://docs.appian.com/suite/help/latest/process-model-object.html#process-model-security)).

| Process model | Administrator | Editor | Manager | Viewer | Initiator | Deny | Evidencia |
|---|---|---|---|---|---|---|---|
| `{{DEM Alta Solicitud}}` | `{{DEM Administrators}}` | — | — | — | `{{DEM Gestores}}` | — | [`mcp:processModel/{{DEM Alta Solicitud}}@other:{{herramienta}}#roleMap`](./anexo/processModel/{{slug}}.md) |

<!-- Una línea por cada process model cuyo grupo de seguridad declarado no figure en su role map: -->
`{{DEM Alta Solicitud}}`: la definición declara el grupo `{{DEM Revisores}}`, que no figura en su role map.

Otros objetos ([qué tipos heredan la seguridad de su carpeta](https://docs.appian.com/suite/help/latest/object-security.html#security-inheritance-by-object-type)):

<!--
  Hereda de: la carpeta cuyo role map se aplica, con su certeza. ✅ si la respuesta dice que hereda; 🔶 si solo llega el
  role map de la carpeta y el tipo hereda por defecto; ❓ si no llega ninguno de los dos. «—» si tiene role map propio.
  La evidencia es el role map que se aplica: el del objeto o el de su carpeta.
-->

| Objeto | Tipo | Administrator | Editor | Viewer | Deny | Hereda de | Evidencia |
|---|---|---|---|---|---|---|---|
| `{{DEM Rules}}` | Carpeta de reglas | `{{DEM Administrators}}` | — | `{{DEM Users}}` | — | — | [`mcp:folder/{{DEM Rules}}@other:{{herramienta}}#roleMap`](./anexo/folder/{{slug}}.md) |
| `{{DEM_SolicitudForm}}` | Interfaz | `{{DEM Administrators}}` | — | `{{DEM Users}}` | — | `{{DEM Rules}}` 🔶 | [`mcp:folder/{{DEM Rules}}@other:{{herramienta}}#roleMap`](./anexo/folder/{{slug}}.md) |
| `{{DEM Solicitudes}}` | Site | `{{DEM Administrators}}` | — | `{{DEM Users}}` | — | — | [`mcp:site/{{DEM Solicitudes}}@other:{{herramienta}}#roleMap`](./anexo/site/{{slug}}.md) |

<!-- Variante sin role maps: sustituye a las dos tablas anteriores. -->

No se obtuvieron role maps: la matriz recoge solo lo que la definición de cada objeto muestra.

| Objeto | Tipo | Quién accede según la definición | Certeza | Evidencia |
|---|---|---|---|---|
| `{{DEM Alta Solicitud}}` | Process model | Grupo de seguridad declarado: `{{DEM Gestores}}`; role map no disponible | ❓ | [`mcp:processModel/{{DEM Alta Solicitud}}#securityGroupName`](./anexo/processModel/{{slug}}.md) |
| `{{DEM Solicitudes}}` — página «{{Bandeja}}» | Página de site | `{{DEM Gestores}}` (expresión de visibilidad) | ✅ | [`mcp:site/{{DEM Solicitudes}}#pages[1].visibilityExpr`](./anexo/site/{{slug}}.md) |
| `{{DEM Solicitud}}` — acción «{{Nueva solicitud}}» | Acción de record | No la devuelve la extracción. ¿Qué grupos ven la acción? | ❓ | [`mcp:recordType/{{DEM Solicitud}}#actions[{{0}}]`](./anexo/recordType/{{slug}}.md) |

### Capacidades por grupo

<!--
  Filas: grupos. Columnas: capacidades funcionales (casos de uso de 01-funcional.md o puntos de entrada), máx. 7.
  Celda: Inicia, Tarea, Aprueba, Ve, Administra o «—», solo con evidencia (role map, asignación de tarea, visibilidad).
  Si una celda depende de un dato que no llega, «❓».
-->

| Grupo | {{Registrar solicitud}} | {{Aprobar solicitud}} | {{Consultar bandeja}} |
|---|---|---|---|
| `{{DEM Gestores}}` | Inicia | Aprueba | Ve |
| `{{DEM Users}}` | Inicia | — | ❓ |

### Reglas de seguridad en expresiones

<!--
  Dónde se decide el acceso dentro del código: a!isUserMemberOfGroup (o su versión antigua isusermemberofgroup), a!groupsForUser,
  comparaciones con loggedInUser(), a!groupsByName, asignaciones de tarea por expresión, showWhen o visibilidad con condición de grupo,
  reglas de seguridad de registro de los record types (si la definición las trae).
  Las reglas de permiso de pantalla también están en 11-reglas-negocio.md: aquí, la vista de seguridad (qué controla y con qué grupo).
-->

| Objeto | Patrón | Qué controla | Certeza | Evidencia |
|---|---|---|---|---|
| `{{DEM_SolicitudForm}}` | `a!isUserMemberOfGroup(loggedInUser(), cons!{{DEM_GRP_GESTORES}})` | {{La sección «Resolución» solo la ve DEM Gestores}} | ✅ | [`mcp:interface/{{DEM_SolicitudForm}}#expression (línea {{12}})`](./anexo/interface/{{slug}}.md) |
| `{{DEM Alta Solicitud}}` | Asignación por expresión `rule!{{DEM_AsignarRevisor}}` | {{La tarea «Revisar» va al grupo que devuelve la regla}} | ✅ | [`mcp:processModel/{{DEM Alta Solicitud}}#nodes[id={{3}}].assignment`](./anexo/processModel/{{slug}}.md) |

## Hallazgos

| ID | Hallazgo | Severidad | Certeza | Evidencia |
|---|---|---|---|---|
| H-SEG-01 | {{Credencial en claro en la constante CON_SAP_TOKEN}} | Alta | ✅ | [`mcp:constant/{{CON_SAP_TOKEN}}#value`](./anexo/constant/{{slug}}.md) |
| H-SEG-02 | {{DEM Users (todos los usuarios de la aplicación) puede ver el site de administración}} | Media | ✅ | [`mcp:site/{{DEM Admin}}@other:{{herramienta}}#roleMap`](./anexo/site/{{slug}}.md) |

**H-SEG-01** — Impacto: {{la credencial de SAP la ve quien tenga acceso de diseño a la aplicación y va en cualquier exportación de su paquete}}.

<!--
  Solo hallazgos de seguridad, grupos y secretos (los de integraciones van en 05 y los de Web APIs en 06).
  Mismos ID, título, severidad y certeza que en <trabajo>/hallazgos/integration-security-analyzer.json.
  Para secretos: area "secretos", severidad Alta y una línea de impacto como la de H-SEG-01. Qué hacer no se escribe.
-->

## Cobertura y límites

- {{Role maps: obtenidos para N de M objetos / no los devuelve la extracción}} ❓
- {{Seguridad de las acciones de record: no la devuelve la extracción; validar en Appian Designer}} ❓
- {{Miembros de grupos: sin herramienta de miembros, no se sabe qué grupos están vacíos}} ❓
- {{Entorno extraído: no es producción; los miembros pueden diferir de los de producción}}
