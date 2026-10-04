<!--
  Plantilla 10 — Catálogo de pantallas (ui-rules-analyzer).
  Estructura: TL;DR → Vista → Detalle → Hallazgos → Cobertura y límites. Las secciones sin contenido se omiten.
  Pantallas PAN-001…; hallazgos H-UI-01…. Los {{marcadores}} se sustituyen y los comentarios se borran.
-->

# Catálogo de pantallas

> **TL;DR**: {{2-3 frases: qué pantallas hay, quién las usa y lo más importante que debe saber el lector}}.
> **Volumen**: {{N}} pantallas ({{n}} páginas, {{n}} vistas de registro, {{n}} formularios de inicio, {{n}} tareas){{; n interfaces sin punto de entrada}}. **Hallazgos**: {{N (Alta: n)}} — principales: [H-UI-01](#hallazgos), {{…}} (o «sin hallazgos»).

## Vista

Cómo se llega a cada pantalla y a qué proceso lleva cada acción.

![Mapa de navegación entre pantallas y procesos](diagrams/navegacion.svg)

Fuente: [navegacion.mmd](diagrams/navegacion.mmd)

<!-- Sin SVG: sustituye las dos líneas anteriores por el bloque mermaid idéntico a navegacion.mmd (flowchart TD, ≤ 30 nodos). -->

| ID | Pantalla | Tipo | Quién la ve | Cómo se llega | Certeza |
|---|---|---|---|---|---|
| [PAN-001](#pan-001--{{ancla}}) | {{Panel de solicitudes}} | {{Página}} | {{Usuarios de la aplicación}} | {{Site Solicitudes › Panel}} | ✅ |
| [PAN-002](#pan-002--{{ancla}}) | {{Nueva solicitud}} | {{Formulario de inicio}} | {{Gestores}} | {{Lista de solicitudes › Nueva solicitud}} | 🔵 |

Certeza: ✅ la definición y el render coinciden · 🔵 solo de la definición (sin render, o con diferencias que explica la ficha) · ❓ no se pudo renderizar y la definición no trae el contenido.

<!-- Más de 15 pantallas: una tabla por tipo (### Páginas, ### Vistas de registro, ### Formularios de inicio, ### Tareas). -->

## Detalle

<!-- Más de 5 fichas: empieza con un índice de enlaces a ellas. -->

### PAN-001 — {{nombre de negocio}}

{{1 línea: qué hace el usuario en esta pantalla.}}

| Campo | Valor |
|---|---|
| Tipo | {{Página · Vista de registro · Formulario de inicio · Tarea}} |
| Quién la ve | {{actor o grupo}} · {{condición de visibilidad o «sin condición»}} |
| Cómo se llega | {{site › página · acción de registro · tarea de un proceso}} |
| Implementado en | [`{{interfaz}}`](anexo/interface/{{slug}}.md){{ + interfaces hijas y reglas}} |
| Guarda | {{qué datos guarda y dónde, o «nada: solo consulta»}} |

**Datos**

| Etiqueta | Origen del dato | Editable | Obligatorio | Guarda en |
|---|---|---|---|---|
| {{Título}} | {{Solicitud.titulo}} | Sí | Sí | {{Solicitud.titulo}} |
| {{Estado}} | {{Lista fija de 4 estados}} | Sí | No | {{No se guarda}} |

**Validaciones**

- {{Regla en lenguaje de negocio}} → [RN-001](./11-reglas-negocio.md#rn-001--{{ancla}})

**Acciones**

| Botón o enlace | Qué hace | Condición | Lleva a |
|---|---|---|---|
| {{Enviar}} | {{Envía el formulario al proceso de alta}} | {{Exige el título}} | {{PAN-003 · proceso Alta de solicitud}} |

{{Notas (si aplica, 3-5 líneas): diferencias entre definición y render; comportamiento de otra área en una frase con enlace a su documento, sin severidad; hallazgos de esta pantalla por su ID.}}

Evidencia: `mcp:interface/{{nombre}}#expression (línea {{N}})`, `mcp:site/{{nombre}}#pages[{{i}}]` · Certeza: ✅

### Interfaces sin punto de entrada

<!-- Solo si hay alguna. Interfaces que no son pantalla ni las usa ninguna pantalla. El hallazgo de código muerto es de 02. -->

| Interfaz | Quién la referencia | Lectura | Evidencia |
|---|---|---|---|
| `{{interfaz}}` | {{nadie}} | {{Candidata a código muerto, ver [02](./02-arquitectura.md#hallazgos)}} | `graph:orphans` |

## Hallazgos

| ID | Hallazgo | Severidad | Certeza | Evidencia |
|---|---|---|---|---|
| H-UI-01 | {{El alta no guarda lo que el usuario escribe}} | {{Alta}} | ✅ | `mcp:interface/{{nombre}}#expression (líneas {{2-5}})` |

{{Debajo de cada hallazgo Alta, si hace falta: una línea con su impacto y la recomendación.}}

## Cobertura y límites

{{1-5 líneas: pantallas sin render, configuración de listas de record que no devuelve la extracción, mapeos de formularios no disponibles…}}
