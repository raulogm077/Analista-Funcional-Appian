# F2 · Incorporar una fuente

**Cuándo.** Ya hay análisis y llega una reunión, un correo, un documento, una demo o los comentarios del cliente al DF; también un retoque (un texto, una etiqueta, una columna).
**Empieza.** El analista, con `appian-functional-analyst`. **Termina en.** El informe de impacto aprobado y aplicado, con el análisis coherente y su versión.

| # | Paso | Quién | Con qué | Detalle |
|---|---|---|---|---|
| 1 | Ver cómo está el análisis, sin leerlo entero | Script | `appian-functional-analyst` · `indice.py resumen` | `appian-functional-analyst/references/actualizacion.md` §0 |
| 2 | Catalogar la fuente | Script | `appian-functional-analyst` · `leer_fuentes.py` | `appian-functional-analyst/references/actualizacion.md` §1 |
| 3 | Nota de la fuente; una fuente corta no la lleva | IA | `appian-functional-analyst` | `appian-functional-analyst/references/actualizacion.md` §2 |
| 4 | Sacar los puntos, dónde encaja cada uno y de qué depende | IA, con lo que imprimen `indice.py buscar`, `ficha` e `impacto` | `appian-functional-analyst` | `appian-functional-analyst/references/actualizacion.md` §3 |
| 5 | Escribir el informe de impacto, `impacto/FU-nn.md` | IA | `appian-functional-analyst` | `appian-functional-analyst/references/actualizacion.md` §4 |
| 6 | Decidir los puntos que requieren aprobación | Analista | — | `appian-functional-analyst/references/actualizacion.md` §5 |
| 7 | Abrir la versión y aplicar solo lo aprobado, pieza a pieza | Script abre la versión; IA edita | `appian-functional-analyst` · `proyecto.py version` | `appian-functional-analyst/references/actualizacion.md` §6 |
| 8 | Verificar | Script | `appian-functional-analyst` · `comprobar.py --anterior --impacto` | `appian-functional-analyst/references/actualizacion.md` §7 |
| 9 | Decir qué cambió y qué queda pendiente; el guion de la próxima reunión | IA; Script | `appian-functional-analyst` · `indice.py pendientes` | `appian-functional-analyst/references/actualizacion.md` §8 |

El prototipo y el Word no se rehacen con cada fuente: las pantallas afectadas, después de verificar; el Word, al enviarlo.

**Variante: un retoque.** Pocos puntos y ninguno requiere aprobación: sin nota ni presentación, con el informe ya aplicado y una sola comprobación. `appian-functional-analyst/references/actualizacion.md` «Camino corto».

**Variante: una demo del prototipo.** Cada comentario es un punto del informe y, una vez aplicado, `appian-prototipos` rehace solo esas pantallas: `appian-functional-analyst/references/actualizacion.md` «Feedback de una demo» y `appian-prototipos/SKILL.md` «Después de una demo».
