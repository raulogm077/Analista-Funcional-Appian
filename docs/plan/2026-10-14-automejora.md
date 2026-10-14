# Plan: automejora del plugin con proyectos reales

Fecha: 14 de octubre de 2026. Parte de `main` (`2f9151d`, 0.8.0-beta.1). Rama `automejora-pruebas`, en su propia copia
de la carpeta (worktree `Proyectos IA/Plugin-automejora`), porque otra sesión trabaja en la principal.

**Objetivo.** Probar el plugin y su flujo de trabajo con reuniones reales del cerebro corporativo y con aplicaciones ya
construidas, en todos los modos en que se usa, y apuntar como mejora para la próxima versión cada lección que pida un
cambio.

**Decidido por Raúl antes de empezar (14 de octubre de 2026).**

- Solo probar y apuntar: no se tocan skills ni scripts; un fallo, aunque sea de una línea, se apunta y no se corrige.
- Hasta unos 150 USD en sesiones anidadas (`claude -p` con el plugin cargado desde la rama).
- Modos: los flujos F1 a F9 en Claude Code, otros agentes con `AGENTS.md` (Codex y Copilot CLI), subagente frente a
  sesión aparte y sin IA (una persona con lo que deja el plugin).
- Se escribe solo en Indra-spain: una aplicación de prueba con prefijo propio, que se deja para que Raúl la revise.
  BCP, sin escribir. Madrid Digital es del cliente: solo lectura, sin ninguna herramienta que cree, cambie, borre,
  publique o ejecute.

**Dónde va cada cosa.** Las pruebas, sus proyectos y lo medido, en `Proyectos IA/Pruebas-plugin/automejora/`, fuera del
repositorio. Aquí llegan solo las lecciones, sin datos del cliente: cada proyecto se describe por su forma (cuántas
reuniones, cuántos roles, qué tipo de proceso), nunca por su código ni su cliente. Lo medido, en
`docs/evaluaciones.md` («Automejora con proyectos reales»); lo que pide un cambio, en `docs/siguiente-version.md`
(«Del plan de automejora»), con qué, dónde y de dónde sale.

**Cómo se trabaja.** La sesión principal coordina; cada prueba la lanza y la mide un subagente con
`claude -p … --plugin-dir <rama>` y el arnés de T1 (`Pruebas-plugin/T1-agilidad/medicion/medir.py`). Cada sesión anidada
es desatendida: no pregunta y deja las dudas como PC. El coste de cada una se suma en `automejora/coste.md`. Un revisor
de contexto limpio por familia de flujos, con las salidas, el fichero del flujo (`assets/flujos/F*.md`) y estos
criterios, no con las conclusiones de quien probó.

## Pruebas

| # | Modo y flujo | Con qué | Pregunta que responde | Tope |
|---|---|---|---|---|
| P1 | F1 aplicación nueva | Proyecto pequeño: 13 reuniones, ~10.000 palabras; las 4 primeras | ¿Sale el análisis de punta a punta sin improvisar fuera del flujo? | 12 USD |
| P2 | F2 incorporar una fuente y su retoque | P1 + la reunión siguiente; después un retoque de una etiqueta | ¿El informe de impacto encaja la reunión real? ¿El retoque sigue el camino corto? | 8 USD |
| P3 | F1 con volumen grande | Proyecto mediano: 45 reuniones, ~113.000 palabras | ¿`volumen-grande.md` reparte bien? ¿Cuánto cuesta y dónde se va? | 25 USD |
| P4 | F3 evolutivo, F4 defecto y F5 urgente | El proyecto DEM de las pruebas L.U.C.I.A., con su aplicación en Indra | ¿Cada flujo deja lo que dice su fichero y nada más? | 15 USD |
| P5 | F6 ingeniería inversa y F7 refactorización | Una aplicación mediana de Madrid Digital, solo lectura | Las preguntas abiertas: historial de versiones, dependientes, presupuestos de palabras, procesos grandes | 30 USD |
| P6 | F8 construir y verificar, F9 pase a producción | Una unidad pequeña de P1, construida en Indra con prefijo de prueba; QA con SAIL CLI | ¿Las issues se construyen, se verifican y pasan el QA sin pasos de más? | 30 USD |
| P7 | Subagente frente a sesión aparte | El retoque de P2, lanzado de las dos formas | Minutos, llamadas, coste y si pasa `comprobar.py` | 5 USD |
| P8 | Otros agentes | El retoque de P2 con Codex y con Copilot CLI, con `AGENTS.md` y `.agents/workflows/` | ¿Siguen el flujo y lanzan los scripts, o improvisan? | sin coste Anthropic |
| P9 | Sin IA | Un revisor que actúa como persona: lee el Markdown del proyecto y lanza sus scripts, sin cargar skills | ¿Dónde se atasca una persona con lo que deja el plugin? | 5 USD |

Reserva: unos 20 USD para repetir una prueba que falle por el entorno.

## Criterios

- Cada prueba deja su medida (minutos, llamadas, coste, qué leyó y de qué color es cada paso) y su veredicto frente a su
  fichero de flujo.
- Ninguna escritura fuera de Indra-spain; en Madrid Digital, ninguna llamada que no sea de lectura.
- Cada lección que pide un cambio está en `siguiente-version.md` con qué, dónde y de dónde sale, sin datos del cliente;
  las que no piden cambio, en `evaluaciones.md` o fuera.
- La comprobación básica (`python pruebas/comprobar_plugin.py`) pasa antes del commit.
- Al terminar, la carpeta principal queda en `main` y la rama, con sus commits, sin PR.

## Pasos de Raúl

- Revisar las lecciones y decir cuáles se aplican.
- Revisar y, si quiere, borrar la aplicación de prueba de Indra.
- Decir cuándo se abre la PR.
