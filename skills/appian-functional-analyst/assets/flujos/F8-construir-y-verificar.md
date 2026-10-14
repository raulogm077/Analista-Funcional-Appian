# F8 · Construir y verificar

**Cuándo.** Hay una unidad aprobada: sus issues de construcción, una por requisito, están en `construccion/<U>/`.
**Empieza.** Quien construye, con `appian-best-practices` y la skill oficial `appian`; solo en el entorno de desarrollo. <!-- (T12) Fuera de desarrollo y del entorno de corrección, el Dev MCP va en solo lectura. --> **Termina en.** Todas sus issues construidas y verificadas en desarrollo, la unidad con su QA y marcada «Construida»; sigue F9.

| # | Paso | Quién | Con qué | Detalle |
|---|---|---|---|---|
| 1 | Pedir la siguiente issue: la primera sin hacer cuyas dependencias están hechas, reservada para que nadie más se la lleve. Se repite tras cada una, hasta que no quede ninguna | Script | `appian-functional-analyst` · `indice.py issues <p> <U> --siguiente` | `appian-functional-analyst/references/cambios.md` §6 |
| 2 | Leer la issue: es el alcance, se construyen solo sus objetos y lleva lo que hace falta del funcional y del técnico | Quien construye: IA o una persona | `appian-best-practices` | `appian-best-practices/SKILL.md` «Discovering Project Context» |
| 3 | Medir el esfuerzo según el cambio | Quien construye | `appian-best-practices` | `appian-best-practices/SKILL.md` «Calibrate the effort to the change» |
| 4 | Construir en desarrollo, en el orden que da la skill oficial | IA por el Dev MCP, o una persona en Designer | `appian-best-practices`, con la skill oficial `appian` | `appian-best-practices/SKILL.md` «Tools» y `appian-best-practices/references/14-official-skill-divergences.md` |
| 5 | Probar lo construido y pasar las puertas de calidad que tocan; si la issue dice que no hay pruebas que ejecutar, ninguna <!-- (T13) Pruebas de la issue: técnico §14 dice cómo se comprueba cada criterio; se ejecutan solo los casos de sus reglas e interfaces y de lo que las usa, y un fallo en lo de la issue bloquea. --> | Quien construye | `appian-best-practices` | `appian-best-practices/references/10-quality-gates.md` |
| 6 | Reaplicar las correcciones urgentes que pida la issue | Quien construye | `appian-best-practices` | `appian-functional-analyst/references/urgentes.md` §2 |
| 7 | Verificar la issue contra el técnico, en solo lectura, con la orden que trae: con eso está hecha | Script | `appian-reverse-engineering` · `devmcp_extract.py verificar` | `appian-reverse-engineering/SKILL.md` «Verificar o deriva» y `appian-functional-analyst/references/cambios.md` §6 |
| 8 | Con todas hechas, el QA de la unidad: en otra sesión y solo con sus `.feature`, recorrer cada escenario con SAIL CLI como cada rol; cada recorrido queda como guion en `qa/<U>/`. Un escenario que falla devuelve su issue a pendiente: se corrige (pasos 4 a 7) y se repiten sus guiones | QA: otro agente o una persona, sin la skill oficial; el script repite | `appian-qa` · `qa.py repetir <p> <U>` | `appian-qa/SKILL.md` «Flujo» y «El guion» |
| 9 | Con todas hechas, marcar la unidad construida, confirmando cada corrección urgente reaplicada | Script | `appian-functional-analyst` · `proyecto.py cambio <p> <U> construida [--reaplicada URG-nn]` | `appian-functional-analyst/references/cambios.md` §1 y §6 |

El avance entre sesiones lo dicen la verificación de cada issue y el resultado del QA (`indice.py issues <p> <U>` lo enseña): no hay otro estado que mantener.

**Variante: un retoque cosmético.** El texto de un botón o una etiqueta: una fila «Modifica» en técnico §13, sin DT, una sola issue que dice qué cambia y que no hay pruebas que ejecutar, solo la primera puerta de calidad y sin QA. Si un guion de `qa/` usa el texto que cambia, al repetirlo falla en ese paso y se cambia el texto en el guion. `appian-functional-analyst/references/cambios.md` §4 y `appian-best-practices/SKILL.md` «Calibrate the effort to the change». <!-- (T6, T17) Según el coste medido, se hace a mano en Designer. -->

**Variante: sin Dev MCP.** Construye una persona en Designer, con las issues en el orden de su índice (`construccion/<U>/indice.md`); el QA es el mismo, y el paso 9 lleva `--manual`.
