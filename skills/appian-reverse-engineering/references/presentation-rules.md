# Reglas de presentación

Cómo se escribe **cada** entregable de `<salida>/`. Son la única fuente de estructura y estilo: las plantillas de `assets/markdown-templates/` las concretan para cada documento y los ficheros de agente dicen **qué** analizar, no cómo maquetar.

**Precedencia** (si aun así algo choca): la **plantilla** manda en la estructura del documento; el **fichero del agente** manda en el contenido y el criterio de análisis; estas reglas mandan en el estilo y los límites. Si encuentras un choque, aplica este orden y anótalo en tu informe al orquestador.

---

## Regla 1: esqueleto único

Todo documento sigue este orden. Las secciones sin contenido **se omiten** (no escribas «ninguno» ni «no aplica»); si la ausencia es un dato relevante, dilo en una frase del TL;DR.

```markdown
# <Título>

> **TL;DR**: <2-3 frases: qué es y lo más importante que debe saber el lector>.
> **Volumen**: <cifras que sitúan el documento>. **Hallazgos**: <N (Alta: n)> — principales: [H-PRO-01](#hallazgos), … (o «sin hallazgos»).

## Vista
<diagrama principal (si aporta) + tabla resumen con una fila por elemento>

## Detalle
<una ficha por elemento, todas con la misma estructura>

## Hallazgos
<solo los del área de este documento (ver execution-principles.md, «Registro de hallazgos»)>

## Cobertura y límites
<1-5 líneas: qué no se pudo obtener o verificar y por qué>
```

- El TL;DR es el **único** resumen del documento. No añadas «Resumen rápido», «Resumen» ni otro TL;DR más abajo.
- La plantilla puede concretar el nombre de una sección («Vista: mapa de procesos») o subdividirla, pero no cambiar el orden.
- Encabezados sin emojis.
- `00-resumen-ejecutivo.md`, `LEEME.md` e `INVENTARIO.md` tienen su propia estructura en la plantilla; también empiezan por el TL;DR.

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
| Caracteres por celda | ≤ 100, salvo la columna Evidencia |
| Nodos por diagrama Tipo A (flowchart, también por capas) | ≤ 30 |
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

Evidencia: `mcp:<tipo>/<nombre>[@<rol>]#<ubicación>` · Certeza: ✅/🔵/❓
```

Si el documento tiene más de 5 fichas, el Detalle empieza con un índice de enlaces a ellas.

## Regla 6: enlaces, no copias

Cada cosa se documenta una vez, en su documento propietario (ver `execution-principles.md`), y desde los demás se enlaza:

```markdown
La integración `INT_SAP_Crear` la llama `PM_GestionExpedientes` ([ficha](./05-integraciones-consumidas.md#int_sap_crear--sap-crear-expediente)).
```

No dupliques fichas. `00-resumen-ejecutivo.md` cita lo clave en una línea y enlaza.

## Regla 7: marcas

**Certeza** (de una afirmación o un hallazgo), siempre estas tres:

| Marca | Significado |
|---|---|
| ✅ | Verificado: la definición o la respuesta lo muestra directamente. |
| 🔵 | Inferido: se deduce de evidencia indirecta; di en una línea de qué. |
| ❓ | Pendiente: depende de un dato que la extracción no trae o de validarlo con negocio; di quién debe validarlo. |

**Severidad** (solo de hallazgos), con palabra: **Alta** (rompe un requisito de negocio o de seguridad, pierde datos o expone credenciales: actuar ya), **Media** (degrada mantenimiento, rendimiento o control: planificar), **Baja** (mejora o higiene).

No uses otras marcas de estado (🔴, 🟡, ⚠️, ❗, ✔️…). Una buena práctica se dice con palabras («buena práctica»), no con ✅. Los emojis temáticos de los diagramas Tipo C (👤, 🔌, 💾…) son parte de la notación y sí se usan.

## Regla 8: lo que el lector no debe ver

- **Usuarios**: ningún nombre de usuario en ningún entregable. Usa recuentos o el rol: «una cuenta personal del grupo DEM Gestores», «una cuenta de servicio».
- **La maquinaria de la skill**: no cites ficheros de la skill (`references/…`, `agents/…`), tipos de diagrama («Tipo C»), nombres de scripts, códigos internos de patrones (`DAT-02`) ni «heurística de la skill». Nombra la buena práctica y su fuente oficial.
- **Notas de parche**: nunca «01 todavía dice…», «esto matiza a…», «corrige lo que dice X». Si otro documento está mal, se corrige ese documento (pasada de coherencia de la fase 6).
- **`<trabajo>/`**: los entregables no lo enlazan (no se comparte). Para el detalle de un objeto, enlaza su ficha del `anexo/`.

## Regla 9: longitud

Objetivo de longitud; si un documento dobla el máximo, está mal estructurado. «1 pantalla» ≈ 50 líneas. En apps pequeñas (menos de ~50 objetos) apunta al objetivo, no al máximo.

| Entregable | Objetivo | Máximo |
|---|---|---|
| `LEEME.md` | 1 pantalla | 2 |
| `00-resumen-ejecutivo.md` | 1-2 pantallas | 3 |
| `01-funcional.md` | 3-5 | 10 |
| `02-arquitectura.md` | 2-3 | 5 |
| `03-modelo-datos.md` | 1 + ½ por entidad | 1 por entidad |
| `04-seguridad-grupos.md` | 2-3 | 5 |
| `05`, `06` | resumen + ½ por integración o API | 1 por integración o API |
| `07-batches.md` | ½ por batch + resumen | 5 |
| `08-procesos-bpmn/<PM>.md` | 1 | 3 |
| `08-procesos-bpmn/indice.md` | 1 | 2 |
| `09-valor-adicional.md` | según hallazgos | con índice |
| `10-pantallas.md`, `11-reglas-negocio.md` | ½ por pantalla o regla | 1 por pantalla o regla |
| `12-especificacion-reconstruccion.md` | 3-6 | 12 |
| `13-modernizacion-refactor.md` | 3-6 | 12 |
| `14-diseno-objetivo.md` | 4-8 | 15 |
| `INVENTARIO.md` | una tabla por tipo | sin límite |

## Checklist antes de escribir cada documento

- [ ] Empieza por el TL;DR (≤ 5 líneas) y no hay otro resumen.
- [ ] Orden Vista → Detalle → Hallazgos → Cobertura; sin secciones vacías.
- [ ] Tablas ≤ 8 columnas; Vista ≤ 15 filas; celdas ≤ 100 caracteres (salvo Evidencia).
- [ ] Cada diagrama una sola vez y legible al ancho de página.
- [ ] Solo ✅/🔵/❓ como certeza y Alta/Media/Baja como severidad.
- [ ] Hallazgos solo de tu área, con ID del registro.
- [ ] Sin usuarios, sin referencias a la skill, sin notas de parche, sin enlaces a `<trabajo>/`.
- [ ] Sin placeholders (`{{`, `TODO`, `TBD`, `xxx`, `lorem`).
- [ ] Cada ficha con evidencia y certeza.
