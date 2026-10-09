# Prueba de enrutado

Mide si cada petición entra por la skill que le toca cuando solo se conocen las seis descripciones (el `description` de
cada SKILL.md). Son 30 peticiones como las diría alguien del equipo, sin nombrar la skill: 20 visibles en
`pruebas/enrutado.json` y 10 en `ocultas/enrutado.json`, que no lee quien ajusta las descripciones hasta medir. Formato
de las dos: `[{"peticion": "…", "skill": "appian-…"}]`. Los resultados van a `docs/evaluaciones.md`.

## Qué hay

| Skill | Visibles | Ocultas |
|---|---|---|
| `appian-functional-analyst` | 4 | 1 |
| `appian-diagramas-bpmn` | 3 | 2 |
| `appian-prototipos` | 3 | 2 |
| `appian-reverse-engineering` | 3 | 2 |
| `appian-refactorizacion` | 3 | 2 |
| `appian-best-practices` (tres en inglés) | 4 | 1 |

Las seis fronteras del plan, con su petición visible; las ocultas llevan otra variante de cada una:

| Frontera | Skill | Visible |
|---|---|---|
| «¿La rehacemos o la evolucionamos?» | refactorización | 4 |
| «Revisa esta interfaz» | buenas prácticas | 3 |
| «Documenta la app X» | ingeniería inversa | 2 |
| «Añade estas historias a lo que ya hay» | analista | 7 |
| «Dibuja el proceso de la app existente», ya documentada | diagramas | 6 |
| «Enséñale al cliente cómo quedaría» | prototipos | 5 |

Otras visibles tocan una frontera vecina: un cambio en una aplicación ya documentada con historias y técnico (12,
analista), «cómo debería estar hecho con buenas prácticas» un módulo con su `as-is/` (13, refactorización), una
aplicación lenta que se quiere rehacer (19, refactorización) y las capturas para el DF (11, prototipos).

## Cómo se hace

1. **El enunciado.** `python3 puntuar.py --enunciado > <carpeta temporal>/enunciado.md`: las seis descripciones,
   leídas de `skills/`, y las peticiones visibles, sin la skill esperada.
2. **El enrutado.** Un agente que no ha visto el repositorio recibe solo ese enunciado y devuelve
   `[{"peticion", "skill"}]` en el mismo orden, una skill por petición. Se guarda como `respuestas.json`, fuera del
   repositorio.
3. **La puntuación.** `python3 puntuar.py respuestas.json`. Imprime cada petición con la skill esperada y la elegida y
   sale 0 si coinciden todas, 1 si falla alguna y 2 si las respuestas no se pueden comparar (otro número de respuestas,
   otro orden, una petición que no está copiada tal cual). Vale la skill con el prefijo del plugin.
4. **Si falla alguna**, se ajustan las descripciones con lo que dice la salida, se repiten los pasos 1 a 3 con un agente
   nuevo y, cuando aciertan todas, se mide una sola vez con las ocultas, que quien ajusta no ha visto:
   `python3 puntuar.py --enunciado --ocultas` y `python3 puntuar.py respuestas-ocultas.json --ocultas`. Sin ellas no se
   sabe si el ajuste vale para peticiones nuevas o solo para las que fallaron.

Criterio de la Tarea 29: todas, también las ocultas cuando se pasan.

`claude plugin eval` espera otro formato de casos y llama a la API. Si se quiere, `enrutado.json` se convierte en
casos con el evaluador `tool_used: Skill`.

`python3 prueba_puntuar.py` prueba `puntuar.py` y las dos baterías (al menos 4 peticiones por skill, sin repetir y un
tercio ocultas) sin imprimir las ocultas. En Windows, `python` en vez de `python3`.
