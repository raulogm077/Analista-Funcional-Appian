# F8 · Construir y verificar

**Cuándo.** Hay una unidad aprobada: sus issues de construcción, una por requisito, están en `construccion/<U>/`.
**Empieza.** Quien construye, con `appian-best-practices` y la skill oficial `appian`; solo en el entorno de desarrollo. Fuera de él (y del entorno de corrección en una urgencia), el Dev MCP entra con una cuenta que solo lee y SAIL CLI no se usa: `appian-reverse-engineering/references/devmcp-setup.md` «Solo se escribe en desarrollo». **Termina en.** Todas sus issues hechas (verificadas o aceptadas manualmente con motivo), la unidad con su QA y marcada «Construida»; sigue F9.

| # | Paso | Quién | Con qué | Detalle |
|---|---|---|---|---|
| 1 | Pedir la siguiente issue: la primera sin hacer cuyas dependencias están hechas, reservada para que nadie más se la lleve. Se repite tras cada una, hasta que no quede ninguna. Cada sesión pide con su nombre (`--quien`): una que se reinicia recupera la suya pidiendo con el mismo | Script | `appian-functional-analyst` · `indice.py issues <p> <U> --siguiente` | `appian-functional-analyst/references/cambios.md` §6 |
| 2 | Leer la issue: es el alcance, se construyen solo sus objetos y lleva lo que hace falta del funcional y del técnico | Quien construye: IA o una persona | `appian-best-practices` | `appian-best-practices/SKILL.md` «Discovering Project Context» |
| 3 | Medir el esfuerzo según el cambio | Quien construye | `appian-best-practices` | `appian-best-practices/SKILL.md` «Calibrate the effort to the change» |
| 4 | Construir en desarrollo, en el orden que da la skill oficial | IA por el Dev MCP, o una persona en Designer | `appian-best-practices`, con la skill oficial `appian` | `appian-best-practices/SKILL.md` «Tools» y `appian-best-practices/references/14-official-skill-divergences.md` |
| 5 | Probar lo construido y pasar las puertas de calidad que tocan: los casos de prueba guardados de los criterios que la issue dice (técnico §14); si dice que no hay pruebas que ejecutar, ninguna | Quien construye | `appian-best-practices` | `appian-best-practices/references/10-quality-gates.md` |
| 6 | Reaplicar las correcciones urgentes que pida la issue | Quien construye | `appian-best-practices` | `appian-functional-analyst/references/urgentes.md` §2 |
| 7 | Verificar la issue contra el técnico, en solo lectura, con la orden que trae, que ejecuta también sus pruebas (los casos de sus reglas e interfaces y de lo que las usa): con eso está hecha. Si una falla, `cambios.md` §6 | Script; marcar una prueba, una persona | `appian-reverse-engineering` · `devmcp_extract.py verificar`; `appian-functional-analyst` · `indice.py issues <p> <U> ISS-nn --sin-prueba "<objeto> «<caso>»" --motivo "…"` | `appian-reverse-engineering/SKILL.md` «Verificar o deriva» y `appian-functional-analyst/references/cambios.md` §6 |
| 8 | Con todas hechas, el QA de la unidad: recorrer cada escenario con SAIL CLI como cada rol; cada recorrido queda como guion en `qa/<U>/`. Quien construye no lo hace ni corrige en esa pasada lo que encuentre: un escenario que falla devuelve su issue a pendiente (`cambios.md` §6), y se corrige como cualquier otra, desde el paso 1 | QA, no quien construye: otra sesión, o un subagente que solo recibe los `.feature`, el site y la cuenta de cada rol (técnico §0), con un modelo pequeño y sin la skill oficial; el script repite; marcar un escenario, una persona | `appian-qa` · `qa.py repetir <p> <U>`; `appian-functional-analyst` · `indice.py issues <p> <U> ISS-nn --sin-prueba HU-nn.m --motivo "…"` | `appian-qa/SKILL.md` «Cuándo, y cuándo no», «Flujo» y «El guion» y `appian-functional-analyst/references/cambios.md` §6 |
| 9 | Con todas hechas, marcar la unidad construida, confirmando cada corrección urgente reaplicada | Script | `appian-functional-analyst` · `proyecto.py cambio <p> <U> construida [--reaplicada URG-nn]` | `appian-functional-analyst/references/cambios.md` §1 y §6 |

El avance entre sesiones lo dicen la verificación o el cierre manual de cada issue y el resultado del QA
(`indice.py issues <p> <U>` identifica cada procedencia).

**Variante: un retoque cosmético.** El texto de un botón o una etiqueta: una fila «Modifica» en técnico §13, sin DT, una sola issue que dice qué cambia y que no hay pruebas que ejecutar, solo la primera puerta de calidad y sin QA. Si un guion de `qa/` usa el texto que cambia, al repetirlo falla en ese paso y se cambia el texto en el guion. `appian-functional-analyst/references/cambios.md` §4 y `appian-best-practices/SKILL.md` «Calibrate the effort to the change». <!-- (T6, T17) Según el coste medido, se hace a mano en Designer. -->

**Variante: cierre manual de una issue.** Una persona puede aceptar lo construido con
`indice.py issues <p> <U> ISS-nn --manual --motivo "…" [--quien "…"]`, también si no tiene Dev MCP.
Se registra su identidad, fecha, motivo y versión; habilita las dependencias, caduca si cambia el encargo y
`--automatico` lo retira. Los fallos vigentes de pruebas o QA siguen su excepción separada (`--sin-prueba`);
`--desatendida` no admite cierres manuales. El QA es el mismo y el cierre de la unidad identifica esta procedencia.
