<!--
  Plantilla 10 — Catálogo de pantallas (ui-rules-analyzer).
  Estructura: Responde a → TL;DR → Vista → Detalle → Hallazgos → Cobertura y límites. Las secciones sin contenido se omiten.
  Pantallas PAN-001…; hallazgos H-UI-01…. Los {{marcadores}} se sustituyen y los comentarios se borran.
  Ninguna pantalla se recorta ni se omite por longitud. Evidencia: siempre enlazada a la ficha del objeto en el anexo.
  Interfaces que no son pantalla ni las usa ninguna pantalla: no se catalogan aquí; la lista de objetos huérfanos
  es la de 09 (ver «Cobertura y límites»).
  «Cobertura y límites»: solo lo de este documento; lo global está en LEEME.
-->

# Catálogo de pantallas

> **Responde a:** ¿Qué pantallas hay y cómo se llega a cada una? ¿Quién ve cada pantalla? ¿Qué datos muestra y guarda cada una? ¿Qué hace cada botón?

> **TL;DR**: {{2-3 frases: qué pantallas hay, quién las usa y lo más importante que debe saber el lector}}.
> **Volumen**: {{N}} pantallas ({{n}} páginas, {{n}} vistas de registro, {{n}} formularios de inicio, {{n}} tareas){{; n interfaces sin punto de entrada}}. **Hallazgos**: {{N (Alta: n)}} — principales: [H-UI-01](#hallazgos), {{…}} (o «sin hallazgos»).

## Vista

Cómo se llega a cada pantalla y a qué proceso lleva cada acción.

![Mapa de navegación entre pantallas y procesos](diagrams/navegacion.svg)

Fuente: [navegacion.mmd](diagrams/navegacion.mmd)

<!-- Sin SVG: sustituye las dos líneas anteriores por el bloque mermaid idéntico a navegacion.mmd (flowchart TD, ≤ 30 nodos). -->

| ID | Pantalla | Tipo | Quién la ve | Cómo se llega | Certeza | Evidencia |
|---|---|---|---|---|---|---|
| [PAN-001](#pan-001--{{ancla}}) | {{Panel de solicitudes}} | {{Página}} | {{Usuarios de la aplicación}} | {{Site Solicitudes › Panel}} | ✅ | [`mcp:interface/{{nombre}}@screen`](./anexo/interface/{{slug}}.md) |
| [PAN-002](#pan-002--{{ancla}}) | {{Nueva solicitud}} | {{Formulario de inicio}} | {{Gestores}} | {{Lista de solicitudes › Nueva solicitud}} | 🔶 | [`mcp:interface/{{nombre}}#expression`](./anexo/interface/{{slug}}.md) |

Certeza: ✅ la definición y el render coinciden · 🔶 solo de la definición (sin render, o con diferencias que explica la ficha) · ❓ no se pudo renderizar y la definición no trae el contenido.

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
| Implementado en | [`{{interfaz}}`](./anexo/interface/{{slug}}.md){{ + interfaces hijas y reglas}} |
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

Evidencia: [`mcp:interface/{{nombre}}#expression (línea {{N}})`](./anexo/interface/{{slug}}.md), [`mcp:site/{{nombre}}#pages[{{i}}]`](./anexo/site/{{slug}}.md) · Certeza: ✅

## Hallazgos

| ID | Hallazgo | Severidad | Certeza | Evidencia |
|---|---|---|---|---|
| H-UI-01 | {{El alta no guarda lo que el usuario escribe}} | {{Alta}} | ✅ | [`mcp:interface/{{nombre}}#expression (líneas {{2-5}})`](./anexo/interface/{{slug}}.md) |

{{Debajo de cada hallazgo Alta, si hace falta: una línea con su impacto, qué puede pasar y a quién afecta.}}

## Cobertura y límites

{{1-5 líneas: pantallas sin render, configuración de listas de record que no devuelve la extracción, mapeos de formularios no disponibles…}}
{{Si hay interfaces sin punto de entrada: «N interfaces no son pantalla ni las usa ninguna pantalla: ver la lista de objetos huérfanos de [09](./09-valor-adicional.md#objetos-huérfanos) ([H-ARQ-NN](./02-arquitectura.md#hallazgos))». Las que usa otro objeto que no es pantalla, por su nombre y con quién las usa.}}
