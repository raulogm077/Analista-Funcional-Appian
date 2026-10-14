# F8 · Construir y verificar

**Cuándo.** Hay una unidad aprobada con su encargo de construcción, `construccion/<U>.md`. <!-- (T11) El encargo pasa a ser una issue por requisito, en construccion/<U>/; un script da la siguiente y la reserva con un commit. -->
**Empieza.** Quien construye, con `appian-best-practices` y la skill oficial `appian`; solo en el entorno de desarrollo. <!-- (T12) Fuera de desarrollo y del entorno de corrección, el Dev MCP va en solo lectura. --> **Termina en.** La unidad construida y verificada en desarrollo, marcada «Construida»; sigue F9. <!-- (T15) Y con su QA: con la unidad completa, en otra sesión y solo con sus .feature, se recorre cada escenario con SAIL CLI; lo que pasa queda como guion en qa/<U>/ y un fallo devuelve su issue a pendiente. -->

| # | Paso | Quién | Con qué | Detalle |
|---|---|---|---|---|
| 1 | Leer el encargo: es el alcance, y se construyen solo sus objetos | Quien construye: IA o una persona | `appian-best-practices` | `appian-best-practices/SKILL.md` «Discovering Project Context» |
| 2 | Medir el esfuerzo según el cambio | Quien construye | `appian-best-practices` | `appian-best-practices/SKILL.md` «Calibrate the effort to the change» |
| 3 | Construir en desarrollo, en el orden que da la skill oficial | IA por el Dev MCP, o una persona en Designer | `appian-best-practices`, con la skill oficial `appian` | `appian-best-practices/SKILL.md` «Tools» y `appian-best-practices/references/14-official-skill-divergences.md` |
| 4 | Probar lo construido y pasar las puertas de calidad que tocan <!-- (T13) Pruebas de la issue: técnico §14 dice cómo se comprueba cada criterio; se ejecutan solo los casos de sus reglas e interfaces y de lo que las usa, y un fallo en lo de la issue bloquea. --> | Quien construye | `appian-best-practices` | `appian-best-practices/references/10-quality-gates.md` |
| 5 | Reaplicar las correcciones urgentes que pida el encargo | Quien construye | `appian-best-practices` | `appian-functional-analyst/references/urgentes.md` §2 |
| 6 | Verificar lo construido contra el técnico, en solo lectura | Script | `appian-reverse-engineering` · `devmcp_extract.py verificar` | `appian-reverse-engineering/SKILL.md` «Verificar o deriva» y `appian-functional-analyst/references/cambios.md` §6 |
| 7 | Marcar la unidad construida, confirmando cada corrección urgente reaplicada | Script | `appian-functional-analyst` · `proyecto.py cambio <p> <U> construida [--reaplicada URG-nn]` | `appian-functional-analyst/references/cambios.md` §1 y §6 |

El avance entre sesiones se ve volviendo a verificar: no hay otro estado que mantener.

**Variante: un retoque cosmético.** El texto de un botón o una etiqueta: una fila «Modifica» en técnico §13, sin DT, y solo la primera puerta de calidad. `appian-functional-analyst/references/cambios.md` §4 y `appian-best-practices/SKILL.md` «Calibrate the effort to the change». <!-- (T6, T17) Según el coste medido, se hace a mano en Designer. -->

**Variante: sin Dev MCP.** Construye una persona en Designer y el paso 7 lleva `--manual`.
