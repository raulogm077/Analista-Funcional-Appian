<!--
  Plantilla 11 — Reglas de negocio (ui-rules-analyzer).
  Estructura: Responde a → TL;DR → Vista → Detalle → Hallazgos → Cobertura y límites. Las secciones sin contenido se omiten.
  Reglas RN-001…, sin SAIL en los enunciados; hallazgos H-RN-01….
  Los {{marcadores}} se sustituyen y los comentarios se borran.
  Certeza de una regla: 🔵 «según su nombre» si solo se deduce del nombre de un nodo, objeto o variable; nunca ✅ si
  un parámetro de su enunciado es ❓ (lleva la certeza más baja de sus partes).
  Ninguna regla se recorta ni se omite por longitud. Evidencia: siempre enlazada a la ficha del objeto en el anexo.
  «Cobertura y límites»: solo lo de este documento; lo global está en LEEME.
-->

# Reglas de negocio

> **Responde a:** ¿Qué decide la aplicación y dónde se aplica cada regla? ¿Qué estados tiene la entidad principal y qué los cambia? ¿Qué reglas se contradicen o se repiten? ¿Qué valores de negocio están escritos en el código?

> **TL;DR**: {{2-3 frases: qué decide la aplicación y lo más importante que debe saber el lector}}.
> **Volumen**: {{N}} reglas ({{n}} de validación, {{n}} de cálculo, {{n}} de decisión, {{n}} de permiso, {{n}} de ciclo de vida, {{n}} de plazo o notificación). **Hallazgos**: {{N (Alta: n)}} — principales: [H-RN-01](#hallazgos), {{…}} (o «sin hallazgos»).

## Vista

<!-- Diagrama solo si se pueden deducir los estados y sus transiciones; si no, la Vista es la tabla. -->

Estados de {{la entidad principal}} y qué los cambia.

![Ciclo de vida de {{entidad}}](diagrams/estados-{{entidad}}.svg)

Fuente: [estados-{{entidad}}.mmd](diagrams/estados-{{entidad}}.mmd)

| ID | Tipo | Enunciado | Dónde se aplica | Certeza | Evidencia |
|---|---|---|---|---|---|
| [RN-001](#rn-001--{{ancla}}) | {{Decisión}} | {{Una solicitud solo se aprueba si el revisor elige «Aprobar».}} | {{PAN-004, proceso Revisión}} | ✅ | [`mcp:processModel/{{nombre}}#nodes[id={{N}}].decision`](./anexo/processModel/{{slug}}.md) |

<!-- Más de 15 reglas: una tabla por tipo (### Validación, ### Cálculo, ### Decisión, ### Permiso, ### Ciclo de vida, ### Plazo o notificación). -->

## Detalle

<!-- Más de 5 fichas: empieza con un índice de enlaces a ellas. -->

### RN-001 — {{título corto}}

{{Enunciado en lenguaje de negocio, en una línea.}}

| Campo | Valor |
|---|---|
| Tipo | {{Validación · Cálculo · Decisión · Permiso · Ciclo de vida · Plazo o notificación}} |
| Parámetros | {{valor y dónde está: constante, literal en un objeto (ver «Parámetros en literales») o «ninguno»}} |
| Dónde se aplica | [PAN-004](./10-pantallas.md#pan-004--{{ancla}}), {{proceso}} |
| Implementado en | [`{{objeto}}`](./anexo/{{tipo}}/{{slug}}.md) |
| Duplicidades | {{otros sitios con la misma regla y la misma lógica, o «ninguna»}} |

{{Notas (si aplica, 3-5 líneas): uso real del proceso que la aplica si no tiene ejecuciones; comportamiento de otra área con enlace, sin severidad; hallazgos por su ID.}}

Evidencia: [`mcp:{{tipo}}/{{nombre}}#{{ubicación}}`](./anexo/{{tipo}}/{{slug}}.md) · Certeza: ✅

### Contradicciones entre reglas

<!-- Solo si hay. Dos reglas que no pueden cumplirse a la vez o que deciden distinto lo mismo. Las duplicidades van en la ficha. -->

| Reglas | Qué choca | Hallazgo | Evidencia |
|---|---|---|---|
| RN-003 / RN-008 | {{El umbral de aprobación es 1000 en el formulario y 5000 en el proceso}} | H-RN-02 | [`mcp:{{tipo}}/{{nombre}}#{{ubicación}}`](./anexo/{{tipo}}/{{slug}}.md) |

### Parámetros en literales

<!--
  Solo si hay. Parámetro en un literal: un valor de negocio (estado, umbral, nombre o id de grupo, correo, URL) escrito en
  una expresión o en una configuración, y no en una constante ni en un dato. La configuración de un temporizador no lo es.
  «Escrito en»: todos los objetos donde aparece el mismo literal.
-->

| Regla | Valor | Escrito en | Hallazgo | Evidencia |
|---|---|---|---|---|
| RN-001 | {{«Aprobar»}} | {{`DEM_RevisionForm` y `DEM Revisión`}} | H-RN-01 | [`mcp:processModel/{{nombre}}#nodes[id={{N}}].decision`](./anexo/processModel/{{slug}}.md) |

## Hallazgos

| ID | Hallazgo | Severidad | Certeza | Evidencia |
|---|---|---|---|---|
| H-RN-01 | {{El literal «Aprobar» se repite en el formulario y en el proceso}} | {{Baja}} | ✅ | [`mcp:interface/{{nombre}}#expression (línea {{N}})`](./anexo/interface/{{slug}}.md) |

{{Debajo de cada hallazgo Alta, si hace falta: una línea con su impacto, qué puede pasar y a quién afecta.}}

## Cobertura y límites

{{1-5 líneas: pasarelas que no son reglas de negocio y por qué, decisiones sin definición disponible, reglas de procesos sin ejecuciones…}}
