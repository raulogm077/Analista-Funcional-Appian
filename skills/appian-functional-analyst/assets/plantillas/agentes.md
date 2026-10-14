# Cómo se trabaja en este proyecto

Proyecto de una aplicación Appian, llevado con el plugin `appian-analisis-funcional`. Lo propio del proyecto (cliente, estado y siguiente paso) está en `proyecto.md`.

Empieza por `appian-functional-analyst/scripts/proyecto.py estado .`: dice en qué punto está el proyecto, qué falta por subir y si va por detrás del remoto (entonces, `git pull`).

## Dónde está cada cosa

| Ruta | Qué hay |
|---|---|
| `fuentes/`, `notas/`, `impacto/` | Lo que entra (`FU-nn`), la nota de cada fuente y su informe de impacto |
| `analisis/` | `funcional.md` (la visión del producto, en §1), `tecnico.md`, `decisiones.md`, `cambios.md` (las unidades de cambio) y `diagramas/` |
| `prototipo/` | El prototipo navegable y sus capturas |
| `construccion/<U>/` | Las issues de construcción de cada unidad (`indice.md` y, por issue, `ISS-nn.md`, `ISS-nn.feature` y lo esperado) y su verificación. La siguiente la da y la reserva `appian-functional-analyst/scripts/indice.py issues . <U> --siguiente` |
| `qa/<U>/` | El QA de cada unidad, con todas sus issues hechas y antes de marcarla construida: un guion de SAIL CLI por escenario (`<escenario>.json`) y `resultado.json`, la última vez que se repitieron; un escenario que falla devuelve su issue a pendiente, salvo que una persona lo marque como no necesario. Los repite sin IA `appian-qa/scripts/qa.py repetir . <U>`, también antes de cada paquete, tras la regresión |
| `as-is/`, `refactorizacion/` | Solo con una aplicación existente: cómo está hecha y cómo rehacerla |
| `entregables/`, `versiones/` | El DF en Word y la copia del análisis antes de cada cambio |

## Reglas

- **El código vive en Appian; aquí, todo lo demás.** Sobre `main`, sin ramas ni PR: `git commit` y `git push` al terminar cada trabajo.
- **Se sube todo, también las fuentes**, menos los secretos y las grabaciones (`.gitignore`). Si ingeniería inversa encontró secretos escritos en la aplicación, sus valores están en claro en `as-is/`: el equipo decide antes de subirla. El remoto es privado.
- **Lo que se regenera no se fusiona**: si chocan el Word, una captura o el PNG de un diagrama, se vuelve a generar.
- **La IA escribe en Appian solo en desarrollo** y, en una urgencia, en el entorno de corrección; a pruebas y a producción llega un paquete que ha revisado una persona. En los demás entornos, el Dev MCP entra con una cuenta que solo lee y SAIL CLI no se usa, porque crea datos y lanza procesos (`appian-reverse-engineering/references/devmcp-setup.md`, «Solo se escribe en desarrollo»). `LCP_TOOL_MODE=readonly` no protege: el Dev MCP no la aplica.
- **Las skills no se copian aquí**: son las del plugin y la oficial de Appian (`appian`). Una ruta que empieza por `appian-` es de la carpeta `skills/` del plugin.

## Flujos

{flujos}
