# F7 · Refactorización

**Cuándo.** Se quiere plantear cómo rehacer una aplicación existente, entera o una parte, o decidir si se rehace; necesita `as-is/` (F6).
**Empieza.** Refactorización, con `appian-refactorizacion`. **Termina en.** La propuesta validada, el técnico con la migración y una unidad por fase de la hoja de ruta; cada fase sigue F8.

| # | Paso | Quién | Con qué | Detalle |
|---|---|---|---|---|
| 1 | Leer `as-is/` y decir qué hay: objetos, procesos, hallazgos y lo que quedó sin verificar | IA | `appian-refactorizacion` | `appian-refactorizacion/SKILL.md` «Flujo» |
| 2 | Dar el alcance y los límites: qué se rehace, plazo y qué no se puede tocar | Quien lo pide | — | El mismo apartado |
| 3 | Escribir `refactorizacion/propuesta.md`: diagnóstico, solución por capas, migración y hoja de ruta | IA | `appian-refactorizacion`, que cita `appian-best-practices` en cada regla | El mismo apartado |
| 4 | Comprobar la propuesta | Script | `appian-refactorizacion` · `comprobar_propuesta.py` | El mismo apartado |
| 5 | Validar la propuesta | El equipo y el cliente | — | Lo que decidan entra como fuente por F2 |
| 6 | Escribir el funcional (lo que se conserva, lo que cambia y lo nuevo) y el técnico, que baja cada propuesta a objetos con su migración | IA | `appian-functional-analyst`, con la propuesta como fuente | `appian-functional-analyst/SKILL.md` «Aplicación existente» y `appian-functional-analyst/references/tecnico-plantilla.md` |
| 7 | Abrir una unidad por fase de la hoja de ruta; cada una se aprueba y saca su encargo como en F3 | Jefe de proyecto; Script | `appian-functional-analyst` · `proyecto.py cambio` e `indice.py encargo` | `appian-functional-analyst/references/cambios.md` §2 |
