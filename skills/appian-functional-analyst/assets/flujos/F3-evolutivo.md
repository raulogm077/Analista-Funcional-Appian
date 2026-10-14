# F3 · Evolutivo

**Cuándo.** Hay que cambiar o ampliar una aplicación ya construida, propia o ajena (documentada en `as-is/`; si no lo está, antes F6); también una integración nueva.
**Empieza.** El analista, con `appian-functional-analyst`. **Termina en.** La unidad `EV-nn` aprobada, con sus issues de construcción (`construccion/<U>/`), y el DF del cambio; sigue F8.

| # | Paso | Quién | Con qué | Detalle |
|---|---|---|---|---|
| 1 | Solo en una aplicación ajena sin análisis: el análisis base de toda la aplicación, con `as-is/` como fuente | IA | `appian-functional-analyst` | `appian-functional-analyst/SKILL.md` «Aplicación existente» y `appian-functional-analyst/references/cambios.md` §2 |
| 2 | Abrir la unidad del cambio | Script | `appian-functional-analyst` · `proyecto.py cambio <p> EV-nn abrir` | `appian-functional-analyst/references/cambios.md` §1 |
| 3 | Incorporar cada fuente del cambio por F2, con `Cambio: EV-nn` en la cabecera de su informe | Como en F2 | `appian-functional-analyst` | `appian-functional-analyst/references/cambios.md` §3 |
| 4 | Bajar el cambio al técnico: en §13, la unidad de cada objeto y el requisito al que sirve («Para»), y la DT «Cambio sobre lo construido» si cambia datos, permisos, integraciones o procesos en curso | IA | `appian-functional-analyst`, que consulta `appian-best-practices` por secciones | `appian-functional-analyst/references/cambios.md` §4 |
| 5 | Comprobar | Script | `appian-functional-analyst` · `comprobar.py` | `appian-functional-analyst/references/cambios.md` §7 |
| 6 | Aprobar la unidad entera, con su alcance y su coste: al aprobarla quedan escritas sus issues, una por requisito. Si cambia datos, permisos, procesos en curso o lo que usan otros, o usa IA, avisa de la DT que una persona revisa antes de construir (un aviso, no una puerta) | Jefe de proyecto; Script lo registra | `appian-functional-analyst` · `proyecto.py cambio <p> EV-nn aprobada --fuente FU-nn` | `appian-functional-analyst/references/cambios.md` §1 y §5 |
| 7 | Al enviarlo: el DF del cambio y las capturas de las pantallas que cambian | Script; Analista lo envía | `appian-functional-analyst` · `df_docx.js --cambio` y `proyecto.py entregar --cambio`; `appian-prototipos` · `capture.py --solo` | `appian-functional-analyst/references/cambios.md` §5 |

**Variante: una integración nueva.** Su ficha INT con criterios en el funcional y su diseño en el técnico, antes del paso 5: `appian-functional-analyst/references/funcional-plantilla.md` §9, `appian-functional-analyst/references/tecnico-plantilla.md` §10 y `appian-best-practices/references/07-integrations.md`.
