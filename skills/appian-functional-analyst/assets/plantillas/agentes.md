# Cómo se trabaja en este proyecto
Proyecto de una aplicación Appian, llevado con el plugin `appian-analisis-funcional`; lo propio del proyecto (cliente, estado y siguiente paso) está en `proyecto.md`. Lee la `ruta` del plugin en `.appian-plugin.json` (local, no se sube a git): las rutas de skills se resuelven bajo `<ruta>/skills/`. Empieza por `python <ruta>/skills/appian-functional-analyst/scripts/proyecto.py estado .`: dice en qué punto está el proyecto, qué falta por subir y si va por detrás del remoto (entonces, `git pull`). Si falta el localizador o su ruta ya no existe, pide dónde está instalado el plugin y ejecuta desde allí `proyecto.py iniciar .`.

## Dónde está cada cosa
| Ruta | Qué hay |
|---|---|
| `fuentes/`, `notas/`, `impacto/` | Lo que entra (`FU-nn`), la nota de cada fuente y su informe de impacto |
| `analisis/` | `funcional.md` (la visión del producto, en §1), `tecnico.md`, `decisiones.md`, `cambios.md` (las unidades de cambio) y `diagramas/` |
| `construccion/<U>/` | Las issues de construcción de cada unidad (`indice.md` y, por issue, `ISS-nn.md`, `ISS-nn.feature` y lo esperado) y su verificación. La siguiente la da y la reserva `appian-functional-analyst/scripts/indice.py issues . <U> --siguiente --quien <el nombre de esta sesión>` |
| `qa/<U>/` | El QA de cada unidad, con todas sus issues hechas y antes de marcarla construida: un guion de SAIL CLI por escenario y `resultado.json`. Los repite sin IA `appian-qa/scripts/qa.py repetir . <U>`, también antes de cada paquete; si uno falla, `appian-functional-analyst/references/cambios.md` §6 |
| `prototipo/`, `entregables/`, `versiones/` | El prototipo navegable y sus capturas, el DF en Word y la copia del análisis antes de cada cambio |
| `as-is/`, `refactorizacion/` | Solo con una aplicación existente: cómo está hecha y cómo rehacerla |

## Reglas
- **El código vive en Appian; aquí, todo lo demás.** Sobre `main`, sin ramas ni PR: `git commit` y `git push` al terminar cada trabajo. Lo que se regenera no se fusiona: si chocan el Word, una captura o el PNG de un diagrama, se vuelve a generar.
- **Se sube todo, también las fuentes**, menos los secretos y las grabaciones (`.gitignore`). Si ingeniería inversa encontró secretos escritos en la aplicación, sus valores están en claro en `as-is/`: el equipo decide antes de subirla. El remoto es privado.
- **La IA escribe en Appian solo en desarrollo** y, en una urgencia, en el entorno de corrección; a pruebas y a producción llega un paquete que ha revisado una persona. En los demás entornos, el Dev MCP entra con una cuenta que solo lee y SAIL CLI no se usa, porque crea datos y lanza procesos (`appian-reverse-engineering/references/devmcp-setup.md`, «Solo se escribe en desarrollo»).
- **Las skills no se copian aquí**: son las del plugin y la oficial de Appian (`appian`). {ordenes}

## Flujos
{flujos}
