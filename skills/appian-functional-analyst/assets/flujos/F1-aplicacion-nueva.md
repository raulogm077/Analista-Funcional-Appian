# F1 · Aplicación nueva

**Cuándo.** Hay reuniones, correos, notas o el DF del cliente para una aplicación que todavía no existe.
**Empieza.** El analista, con `appian-functional-analyst`. **Termina en.** El DF validado por el cliente, el técnico y la unidad `EV-01` aprobada, con sus issues de construcción (`construccion/EV-01/`); sigue F8.

| # | Paso | Quién | Con qué | Detalle |
|---|---|---|---|---|
| 1 | Crear el proyecto: repositorio git, plantillas, `AGENTS.md` y flujos | Script | `appian-functional-analyst` · `proyecto.py iniciar` | `appian-functional-analyst/SKILL.md` «La carpeta del proyecto» |
| 2 | Catalogar las fuentes | Script | `appian-functional-analyst` · `leer_fuentes.py` | `appian-functional-analyst/references/ingesta-fuentes.md` §1 |
| 3 | Leer todas las fuentes y presentar el checkpoint: problema, perfiles, procesos, reglas, contradicciones y lo que falta | IA | `appian-functional-analyst` | `appian-functional-analyst/SKILL.md` «Proyecto nuevo» |
| 4 | Confirmar o corregir el checkpoint | Analista | — | El mismo apartado |
| 5 | Escribir el funcional, apartado a apartado | IA | `appian-functional-analyst` | `appian-functional-analyst/references/funcional-plantilla.md` y `appian-functional-analyst/references/redaccion.md` |
| 6 | Describir cada proceso y dibujarlo | IA lo describe; Script lo dibuja | `appian-diagramas-bpmn` · `diagrama.py crear` | `appian-diagramas-bpmn/SKILL.md` «Órdenes» |
| 7 | Prototipo y capturas, si se pide | IA | `appian-prototipos` | `appian-prototipos/SKILL.md` «Flujo» |
| 8 | Escribir el técnico, con el funcional estable | IA | `appian-functional-analyst`, que consulta `appian-best-practices` por secciones | `appian-functional-analyst/references/tecnico-plantilla.md` |
| 9 | Comprobar el análisis | Script | `appian-functional-analyst` · `indice.py derivadas --escribir` y `comprobar.py` | `appian-functional-analyst/SKILL.md` «Proyecto nuevo» |
| 10 | Generar el DF en Word | Script | `appian-functional-analyst` · `df_docx.js` | El mismo apartado |
| 11 | Enviar el DF al cliente y anotarlo | Analista lo envía; Script lo anota | `appian-functional-analyst` · `proyecto.py entregar` | El mismo apartado |
| 12 | Validar el DF | Cliente | — | Sus comentarios entran por F2 |
| 13 | Abrir la unidad `EV-01` y aprobarla: al aprobarla quedan escritas sus issues, una por requisito | Jefe de proyecto la aprueba; Script | `appian-functional-analyst` · `proyecto.py cambio` | `appian-functional-analyst/references/cambios.md` §1, §2 y §5 |

**Variante: el cliente trae su DF ya hecho.** Entra como versión 1.0, sin reinterpretar, y los pasos 3 a 5 parten de él: `appian-functional-analyst/SKILL.md` «Modos» y `appian-functional-analyst/references/ingesta-fuentes.md` §3.
