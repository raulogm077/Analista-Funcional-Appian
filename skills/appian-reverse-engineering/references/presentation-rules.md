# Reglas de presentación

Cómo se escribe **cada** entregable de `<salida>/`. Son la única fuente de estructura, evidencia y marcas: las plantillas de `assets/markdown-templates/` las concretan para cada documento y los ficheros de agente dicen **qué** analizar, no cómo maquetar.

**Prosa.** Sigue las reglas comunes del plugin, en `appian-functional-analyst/references/redaccion.md` (junto a esta skill: `<skill>/../appian-functional-analyst/references/redaccion.md`): frases cortas de una idea, concretas, cada cosa una sola vez, sin relleno ni muletillas. Lo que allí es solo del DF (nada de Appian, perfiles y no personas, negrita) no vale aquí: los objetos y los usuarios de la aplicación se nombran tal cual.

**Precedencia** (si aun así algo choca): la **plantilla** manda en la estructura del documento; el **fichero del agente** manda en el contenido y el criterio de análisis; estas reglas mandan en la presentación y los límites. Si encuentras un choque, aplica este orden y anótalo en tu informe al orquestador.

---

## Regla 1: esqueleto único

Todo documento sigue este orden. Las secciones sin contenido **se omiten** (no escribas «ninguno» ni «no aplica»); si la ausencia es un dato relevante, dilo en una frase del TL;DR.

```markdown
# <Título>

> **Responde a:** <las preguntas de su plantilla, tal cual>

> **TL;DR**: <2-3 frases: qué es y lo más importante que debe saber el lector>.
> **Volumen**: <cifras que sitúan el documento>. **Hallazgos**: <N (Alta: n)> — principales: [H-PRO-01](#hallazgos), … (o «sin hallazgos»).

## Vista
<diagrama principal (si aporta) + tabla resumen con una fila por elemento>

## Detalle
<una ficha por elemento, todas con la misma estructura>

## Hallazgos
<solo los del área de este documento (ver execution-principles.md, «Registro de hallazgos»)>

## Cobertura y límites
<1-5 líneas: qué no se pudo obtener o verificar en este documento y por qué. Lo global está en LEEME (Regla 8)>
```

- «Responde a» lleva las preguntas de la plantilla del documento, copiadas tal cual. Lo que no responde a ninguna de ellas no va en el documento.
- El TL;DR es el **único** resumen del documento. No añadas «Resumen rápido», «Resumen» ni otro TL;DR más abajo.
- La plantilla puede concretar el nombre de una sección («Vista: mapa de procesos») o subdividirla (`## Detalle: datos`…), pero no cambiar el orden.
- `09` añade «Registro de hallazgos» tras sus Hallazgos.
- Encabezados sin emojis.
- `00-resumen-ejecutivo.md`, `LEEME.md` e `INVENTARIO.md` tienen su propia estructura en la plantilla; también empiezan por «Responde a» y el TL;DR.

## Regla 2: diagrama, luego tabla, luego prosa

Si hay relaciones, diagrama; si hay N elementos comparables, tabla; el matiz, en prosa breve. Cada diagrama lleva una frase que dice qué muestra.

Un diagrama aparece **una sola vez** por documento:

- si existe el `.svg`: `![<qué muestra>](diagrams/<nombre>.svg)` y debajo `Fuente: [<nombre>.mmd](diagrams/<nombre>.mmd)`;
- si no se pudo renderizar: el bloque ` ```mermaid ` embebido (idéntico al `.mmd`).

Los diagramas se leen al ancho de una página: más de ~1600 px de ancho es ilegible (el render avisa). Usa `flowchart TD`, pocas cajas por fila y etiquetas de arista solo si aportan; si no cabe, parte el diagrama. Nombres de fichero en `references/mermaid-rules.md`.

## Regla 3: límites

| Elemento | Límite |
|---|---|
| Columnas por tabla | ≤ 8 |
| Filas por tabla de la Vista | ≤ 15 (si hay más, parte por tipo o subdominio). No aplica al catálogo completo del Detalle, al registro de hallazgos de 09 ni a INVENTARIO. |
| Caracteres por celda | ≤ 100 de texto visible (sin contar la sintaxis de los enlaces), salvo la columna Evidencia |
| Nodos por diagrama Tipo A (flowchart, también por capas) | ≤ 30 y sin aviso de ancho del render (en la práctica, unos 15: agrupa o parte) |
| Entidades por diagrama Tipo B (erDiagram) | sin techo fijo; por legibilidad, parte por subdominio a partir de ~15 (ver `mermaid-rules.md`) |
| Nodos por diagrama Tipo C (proceso) | ≤ 25 |

## Regla 4: tablas escaneables

- Columna 1: el identificador del elemento (nombre técnico).
- Columnas de respuesta corta (Sí/No, número, etiqueta) a la izquierda; las largas a la derecha.
- Certeza con su marca (Regla 7) en una columna corta; severidad con la palabra (Alta/Media/Baja).
- Sí/No en texto: no uses ✔, ✗ ni similares.

## Regla 5: fichas de Detalle uniformes

Todas las fichas de un mismo tipo tienen los mismos campos en el mismo orden:

```markdown
### <nombre técnico> — <nombre visible>

<1 línea: qué es y para qué sirve>

| Campo | Valor |
|---|---|
| … 5-10 campos clave … |

<Notas (si aplica, 3-5 líneas)>

Evidencia: [`mcp:<tipo>/<nombre>[@<rol>]#<ubicación>`](./anexo/<tipo>/<slug>.md) · Certeza: ✅/🔵/❓
```

Toda evidencia, en las fichas y en las columnas «Evidencia» de las tablas (también las de Hallazgos), enlaza la ficha del objeto en el anexo para que el lector la compruebe: `` [`mcp:<tipo>/<nombre>#<ubicación>`](./anexo/<tipo>/<slug>.md) ``; las de `graph:`, `./anexo/grafo.md`. Desde `08-procesos-bpmn/`, `../anexo/…`. Con el enlace en la evidencia, la ficha no repite otro «Definición» al anexo.

Si el documento tiene más de 5 fichas, el Detalle empieza con un índice de enlaces a ellas.

## Regla 6: enlaces, no copias

Cada cosa se documenta una vez, en su documento propietario (ver `execution-principles.md`), y desde los demás se enlaza:

```markdown
La integración `INT_SAP_Crear` la llama `PM_GestionExpedientes` ([ficha](./05-integraciones-consumidas.md#int_sap_crear--sap-crear-expediente)).
```

No dupliques fichas. `00-resumen-ejecutivo.md` cita lo clave en una línea y enlaza. Lo que es de Appian (qué es un record type, qué tipos heredan la seguridad de su carpeta) no se explica: se enlaza su página de la documentación oficial.

## Regla 7: marcas

**Certeza** (de una afirmación o un hallazgo), siempre estas tres:

| Marca | Significado |
|---|---|
| ✅ | Verificado: la definición o la respuesta lo muestra directamente. |
| 🔵 | Inferido: se deduce de evidencia indirecta; di en una línea de qué. |
| ❓ | Pendiente: depende de un dato que la extracción no trae o de validarlo con negocio; di quién debe validarlo. |

**Severidad** (solo de hallazgos), con palabra, según su riesgo: **Alta** (rompe un requisito de negocio o de seguridad, pierde datos o expone credenciales), **Media** (degrada el mantenimiento, el rendimiento o el control), **Baja** (higiene: nombres, tamaño, restos sin uso). La severidad dice cuánto riesgo hay, no qué hacer.

No uses otras marcas de estado (🔴, 🟡, ⚠️, ❗, ✔️…). ✅ es certeza, no una valoración: no marca que algo esté bien hecho. Los emojis temáticos de los diagramas Tipo C (👤, 🔌, 💾…) son parte de la notación y sí se usan.

## Regla 8: lo que el lector no debe ver

- **La maquinaria de la skill**: no cites ficheros de la skill (`references/…`, `agents/…`), tipos de diagrama («Tipo C»), nombres de scripts ni «heurística de la skill». Lo que sale de la documentación de Appian lleva su `Fuente: <URL>`.
- **Notas de parche**: nunca «01 todavía dice…», «esto matiza a…», «corrige lo que dice X». Si otro documento está mal, se corrige ese documento (pasada de coherencia de la fase 6).
- **`<trabajo>/`** (`extraccion/`): los entregables no lo enlazan ni escriben su ruta (son datos en bruto). Para el detalle de un objeto, enlaza su ficha del `anexo/`.
- **Limitaciones globales** (entorno no productivo, versión no determinada, muestra de ejecuciones, configuración que el Dev MCP no devuelve): se explican una vez en `LEEME.md`. Cada documento cita en su «Cobertura y límites» solo las que cambian lo que dice, en una línea. Donde una cifra dependa de ellas (p. ej. ejecuciones en un entorno que no consta como producción), no repitas la explicación: usa la marca corta «orientativo (ver [LEEME](./LEEME.md))» (`../LEEME.md` desde `08-procesos-bpmn/`), una vez por tabla o sección (p. ej. en la cabecera de la columna).

## Regla 9: longitud

Objetivo de longitud; si un documento (o una ficha) dobla el máximo, está mal estructurado. «1 pantalla» ≈ 50 líneas. En apps pequeñas (menos de ~50 objetos) apunta al objetivo, no al máximo.

**El objetivo crece con el contenido.** Nunca se recorta ni se omite un caso de uso, RN, pantalla u otra ficha para cumplir la longitud: lo que se acorta es cada ficha. En `01`, por encima de unas 15 fichas el documento se parte por área (subdominio, actor o módulo): un `## Detalle: <área>` por área, entre la Vista y los Hallazgos (Regla 1), y tras la Vista un índice de áreas con enlaces a sus fichas.

| Entregable | Objetivo | Máximo |
|---|---|---|
| `LEEME.md` | 1-2 pantallas | 3 |
| `00-resumen-ejecutivo.md` | 1-2 pantallas | 3 |
| `01-funcional.md` | 1 + ½ por caso de uso | 1 + 1 por caso de uso |
| `02-arquitectura.md` | 2-3 | 5 |
| `03-modelo-datos.md` | 1 + ½ por entidad | 1 por entidad |
| `04-seguridad-grupos.md` | 2-3 | 5 |
| `05`, `06` | resumen + ½ por integración o API | 1 por integración o API |
| `07-batches.md` | ½ por batch + resumen | 5 |
| `08-procesos-bpmn/<PM>.md` | 1 | 3 |
| `08-procesos-bpmn/indice.md` | 1 | 2 |
| `09-valor-adicional.md` | según hallazgos | con índice |
| `10-pantallas.md`, `11-reglas-negocio.md` | ½ por pantalla o regla | 1 por pantalla o regla |
| `INVENTARIO.md` | una tabla por tipo | sin límite |

## Checklist antes de escribir cada documento

- [ ] Empieza por «Responde a» (las preguntas de su plantilla) y el TL;DR (≤ 5 líneas); no hay otro resumen.
- [ ] Todo lo que lleva responde a alguna de sus preguntas; nada explica qué es un objeto de Appian (se enlaza).
- [ ] Orden Vista → Detalle → Hallazgos → Cobertura; sin secciones vacías.
- [ ] Tablas ≤ 8 columnas; Vista ≤ 15 filas; celdas ≤ 100 caracteres (salvo Evidencia).
- [ ] Cada diagrama una sola vez y legible al ancho de página.
- [ ] Solo ✅/🔵/❓ como certeza y Alta/Media/Baja como severidad.
- [ ] Hallazgos solo de tu área, con ID del registro: qué pasa y qué riesgo tiene, sin decir qué hacer.
- [ ] Sin referencias a la skill, sin notas de parche, sin enlaces a `<trabajo>/`.
- [ ] Sin placeholders (`{{`, `TODO`, `TBD`, `xxx`, `lorem`).
- [ ] Prosa como dice `redaccion.md`: sin muletillas, frases de 35 palabras como mucho y ningún párrafo copiado de otro documento.
- [ ] Cada ficha con evidencia y certeza, y cada tabla con «Certeza» con su columna «Evidencia»; cada evidencia enlaza su ficha del anexo.
- [ ] Ninguna ficha recortada u omitida por longitud.
