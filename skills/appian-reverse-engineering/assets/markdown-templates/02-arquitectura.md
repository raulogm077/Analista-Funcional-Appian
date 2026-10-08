<!--
  Plantilla 02 — Arquitectura de la aplicación (agente interface-analyzer). Borra estos comentarios en el documento final.
  Solo los objetos reales de esta aplicación y sus relaciones; nada de la arquitectura genérica de Appian.
  Capas, en este orden (las de layerBreakdown de summary.json: mismos nombres, orden y cifras que LEEME):
    Entrada y presentación: sites, interfaces, Web APIs (entradas desde otros sistemas); también páginas, vistas y acciones de record.
    Lógica: process models, expression rules, decisiones, agentes de IA.
    Datos: record types, CDTs, data stores.
    Integración: connected systems e integraciones (llamadas salientes).
    Transversal: constantes (solo en tablas).
    Seguridad: grupos (solo la fila de la Vista; el detalle está en 04). Las carpetas no son capa: INVENTARIO.
  Diagrama: un subgraph por capa (sin Transversal ni Seguridad) y, al final, «Sistemas externos» con un nodo por sistema
  externo y la flecha desde la integración que lo llama (05 remite a este diagrama). Si existe el .svg, imagen +
  «Fuente»; si no, en su lugar, el bloque mermaid idéntico al .mmd. Si se partió por capas, una imagen por fichero
  arquitectura-<capa>.svg.
  «Referencias»: aristas entrantes del objeto en graph.json (qué cuentan, en LEEME, «Cómo leer»).
  Huérfanos: un solo H-ARQ que los agrupa y enlaza la lista de 09; aquí no se listan.
  Evidencia: siempre enlazada (anexo/<tipo>/<slug>.md; las de graph:, anexo/grafo.md).
  Secciones sin contenido: se omiten. «Cobertura y límites»: solo lo de este documento; lo global está en LEEME.
-->

# Arquitectura de la aplicación

> **Responde a:** ¿Qué objetos forman cada capa y quién llama a quién? ¿De qué objetos dependen muchos otros? ¿Qué usa la aplicación que no viaja con ella? ¿Por dónde pasan las escrituras de datos y las llamadas a otros sistemas?

> **TL;DR**: {{2-3 frases: cómo está montada la aplicación, p. ej. «Un site con 3 páginas lleva a interfaces que leen el record DEM Solicitud; el proceso DEM Alta Solicitud orquesta el alta, llama al ERP y lanza la revisión como subproceso.»}}
> **Volumen**: {{N}} objetos: {{n}} interfaces, {{n}} process models, {{n}} expression rules, {{n}} record types, {{n}} integraciones… **Hallazgos**: {{N (Alta: n)}} — principales: [H-ARQ-01](#hallazgos) (o «sin hallazgos»).

## Vista

{{Una frase: qué muestra el diagrama, p. ej. «Objetos clave por capa y quién llama a quién».}}

![{{qué muestra}}](diagrams/arquitectura.svg)

Fuente: [arquitectura.mmd](diagrams/arquitectura.mmd)

| Capa | Objetos | Núcleo |
|---|---|---|
| Entrada y presentación | {{n: 1 site, 6 interfaces, 1 Web API}} | `{{site}}`, `{{interfaz principal}}` |
| Lógica | {{n: 3 process models, 5 expression rules}} | `{{proceso central}}` |
| Datos | {{n: 2 record types}} | `{{record central}}` |
| Integración | {{n: 1 connected system, 2 integraciones}} | `{{integración}}` |
| Transversal | {{n: 8 constantes}} | `{{constante más usada}}` |
| Seguridad | {{n: 4 grupos}} | [04](./04-seguridad-grupos.md) |

## Detalle

Los objetos clave de cada capa; todos, en [INVENTARIO.md](./INVENTARIO.md).

### Entrada y presentación

| Objeto | Tipo | Qué hace | Usa | Referencias | Ficha |
|---|---|---|---|---|---|
| `{{site}}` | Site | {{Portal de los gestores: listado y alta de solicitudes}} | `{{interfaz}}`, `{{record}}` | {{n}} | [anexo](./anexo/site/{{slug}}.md) |
| `{{interfaz}}` | Interfaz | {{Formulario de alta}} | `{{regla}}`, `{{record}}` | {{n}} | [10](./10-pantallas.md) |
| `{{webApi}}` | Web API | {{Alta de solicitudes desde el ERP}} | `{{proceso}}` | {{n}} | [06](./06-apis-expuestas.md) |

### Lógica

| Objeto | Tipo | Qué hace | Usa | Referencias | Ficha |
|---|---|---|---|---|---|
| `{{proceso}}` | Process model | {{Registra la solicitud y la envía a revisión}} | `{{subproceso}}`, `{{integración}}` | {{n}} | [08](./08-procesos-bpmn/{{slug}}.md) |
| `{{regla}}` | Expression rule | {{Devuelve las solicitudes pendientes}} | `{{record}}` | {{n}} | [anexo](./anexo/expressionRule/{{slug}}.md) |

### Datos

| Objeto | Tipo | Qué hace | Usa | Referencias | Ficha |
|---|---|---|---|---|---|
| `{{record}}` | Record type | {{Solicitudes; tabla `dem_solicitud`}} | `{{record relacionado}}` | {{n}} | [03](./03-modelo-datos.md) |

### Integración

| Objeto | Tipo | Qué hace | Usa | Referencias | Ficha |
|---|---|---|---|---|---|
| `{{integración}}` | Integración | {{Crea el expediente en el ERP}} | `{{sistema conectado}}` | {{n}} | [05](./05-integraciones-consumidas.md) |

### Transversal

| Objeto | Tipo | Qué hace | Usa | Referencias | Ficha |
|---|---|---|---|---|---|
| `{{constante}}` | Constante | {{Grupo de gestores, usado en la visibilidad de páginas}} | — | {{n}} | [anexo](./anexo/constant/{{slug}}.md) |

### Dependencias externas

<!--
  Lo que la aplicación usa y no viaja con ella: plug-ins (nodos, funciones o componentes que no son del núcleo de Appian),
  objetos de otras aplicaciones (nodos external: true de graph.json, también los que llama con rule! o cons! y no están
  en ella), grupos de sistema, documentos o plantillas de knowledge center y translation sets. Lo no reconocido, ❓ con
  la pregunta. Un objeto de otra aplicación es «no encontrado en la aplicación»: que se usa es ✅; qué hace, ❓ con su
  NV-ARQ (lo registra este documento).
  Sin ninguna: se omite la sección y se dice en una línea de «Cobertura y límites».
-->

Lo que usa la aplicación y no viaja con ella ([plug-ins](https://docs.appian.com/suite/help/latest/prepare-deployment-packages.html#add-plugins), [objetos de otras aplicaciones](https://docs.appian.com/suite/help/latest/application-settings.html#missing-precedents)).

| Tipo | Objeto | Lo usa | Certeza | Evidencia |
|---|---|---|---|---|
| {{Plug-in (función)}} | `{{nombre}}` | `{{DEM_SolicitudForm}}` | 🔶 | [`mcp:interface/{{DEM_SolicitudForm}}#expression (línea {{n}})`](./anexo/interface/{{slug}}.md) |
| {{Objeto de otra aplicación}} | `{{nombre}}` ({{tipo}}) | `{{DEM Alta Solicitud}}` | ✅ | [`mcp:processModel/{{DEM Alta Solicitud}}@dependencies`](./anexo/processModel/{{slug}}.md) |
| {{Llamado con rule!, no encontrado en la aplicación}} | `{{UTL_DiasLaborables}}` | `{{DEM_SolicitudForm}}` | ✅; qué hace, ❓ [{{NV-ARQ-01}}](./LEEME.md#sin-verificar) | [`mcp:interface/{{DEM_SolicitudForm}}#expression (línea {{n}})`](./anexo/interface/{{slug}}.md) |
| {{Grupo de sistema}} | `{{All Users}}` | `{{DEM Solicitudes}}` (role map, ver [04](./04-seguridad-grupos.md)) | ✅ | [`mcp:site/{{DEM Solicitudes}}@other:{{herramienta}}#roleMap`](./anexo/site/{{slug}}.md) |

### Escrituras y llamadas a otros sistemas

<!--
  Por dónde pasa cada escritura en una entidad y cada llamada a un sistema externo: lo que hay que conocer antes de
  cambiar la aplicación. Hechos con su evidencia, sin valorar si está bien o mal hecho.
-->

| Qué | Por dónde pasa | Certeza | Evidencia |
|---|---|---|---|
| {{Escrituras en `DEM Solicitud`}} | {{Solo el proceso `DEM Persistir`; ninguna interfaz de la aplicación escribe en ella}} | ✅ | [`graph:edge/{{DEM Persistir}}→{{DEM Solicitud}}`](./anexo/grafo.md) |
| {{Llamadas al ERP}} | {{Todas por la integración `DEM_INT_ERP`}} | ✅ | [`mcp:integration/{{DEM_INT_ERP}}@dependents`](./anexo/integration/{{slug}}.md) |

## Hallazgos

| ID | Hallazgo | Severidad | Certeza | Evidencia |
|---|---|---|---|---|
| H-ARQ-01 | {{`DEM_getSolicitudes` (320 líneas) recibe 12 referencias: un cambio afecta a todas las pantallas}} | Media | ✅ | [`graph:hubs`](./anexo/grafo.md) |
| H-ARQ-02 | {{5 objetos sin referencias entrantes: 2 interfaces, 1 process model y 2 constantes ([lista en 09](./09-valor-adicional.md#objetos-huérfanos))}} | Baja | 🔶 | [`graph:orphans`](./anexo/grafo.md) |

{{Para cada hallazgo ❓ o 🔶: de qué se deduce y qué lo confirmaría. Un huérfano que es un process model sin ejecuciones: una frase sin severidad con el H-GEN de 09.}}

## Cobertura y límites

- {{Qué no se pudo obtener o verificar, p. ej. «Pocas referencias del análisis de dependencias de Appian: las relaciones salen sobre todo de las definiciones (🔶)».}}
- {{Sin dependencias externas: «En las definiciones no se encontraron plug-ins, objetos de otras aplicaciones, grupos de sistema, documentos de knowledge center ni translation sets».}}
