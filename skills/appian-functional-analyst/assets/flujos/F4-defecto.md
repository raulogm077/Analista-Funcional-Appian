# F4 · Defecto

**Cuándo.** La aplicación no hace lo acordado en el análisis y nadie lo declara crítico.
**Empieza.** El analista, con `appian-functional-analyst`; si es crítico va por F5 y, si hace lo acordado y se quiere otra cosa, por F3. **Termina en.** La prueba que reproduce el fallo, en el técnico, y su corrección en una unidad aprobada con su encargo; sigue F8. <!-- (T9, T11) El escenario en Gherkin que lo reproduce y su issue de corrección. -->

| # | Paso | Quién | Con qué | Detalle |
|---|---|---|---|---|
| 1 | Catalogar el aviso | Script | `appian-functional-analyst` · `leer_fuentes.py` | `appian-functional-analyst/references/ingesta-fuentes.md` §1 |
| 2 | Contrastarlo con lo acordado: la historia y sus criterios | IA, con lo que imprimen `indice.py buscar` y `ficha` | `appian-functional-analyst` | `appian-functional-analyst/references/actualizacion.md` §3 |
| 3 | Diagnosticar: síntoma, causa y objetos, leyendo solo los implicados | IA | `appian-best-practices` | `appian-best-practices/references/13-maintenance-runbooks.md` |
| 4 | Llevarlo a la unidad Abierta o abrir una | Script | `appian-functional-analyst` · `proyecto.py cambio <p> EV-nn abrir` | `appian-functional-analyst/references/cambios.md` §1 |
| 5 | Informe de impacto por F2: el funcional no cambia; el técnico gana en §14 la prueba que reproduce el fallo y en §13 los objetos que se corrigen | IA | `appian-functional-analyst` | `appian-functional-analyst/references/cambios.md` §2 y `appian-functional-analyst/references/actualizacion.md` «Camino corto» |
| 6 | Aprobar la unidad y sacar su encargo | Jefe de proyecto; Script | `appian-functional-analyst` · `proyecto.py cambio <p> EV-nn aprobada --fuente FU-nn` e `indice.py encargo` | `appian-functional-analyst/references/cambios.md` §1 y §5 |
