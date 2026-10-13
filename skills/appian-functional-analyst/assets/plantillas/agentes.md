# Cómo se trabaja en este proyecto

Proyecto de una aplicación Appian. Lo que sigue vale para cualquier persona o agente. Lo propio del proyecto (cliente, estado, plazos y siguiente paso) está en `proyecto.md`: este fichero y `.agents/workflows/` los genera el plugin `appian-analisis-funcional` y se regeneran con cada versión, así que no se editan.

## Antes de empezar

1. `git pull`.
2. `python3 <plugin>/skills/appian-functional-analyst/scripts/proyecto.py estado .` (en Windows, `python`; `<plugin>` es la carpeta del plugin en este equipo): versión, fuentes sin procesar, unidades en curso, pendientes y lo que no está confirmado o subido.
3. El flujo que toca, de la tabla «Flujos». Al terminar cada trabajo, `git commit` y `git push`.

## Dónde está cada cosa

| Ruta | Qué hay |
|---|---|
| `proyecto.md` | Lo propio del proyecto: cliente, estado, fuentes procesadas y siguiente paso |
| `fuentes/`, `notas/`, `impacto/` | Lo que entra (`FU-nn`), la nota de cada fuente y su informe de impacto |
| `analisis/` | `funcional.md` (la visión del producto, en §1; historias, pantallas y criterios), `tecnico.md`, `decisiones.md`, `cambios.md` (las unidades de cambio) y `diagramas/` |
| `prototipo/` | El prototipo navegable y sus capturas |
| `construccion/` | El encargo de construcción de cada unidad y su verificación <!-- (T11) construccion/<U>/: el índice de las issues de la unidad y, por issue, ISS-nn.md, ISS-nn.feature y lo esperado. --> |
| `qa/<U>/` | El QA de cada unidad: un guion por escenario y sus resultados <!-- (T15) Los escribe la skill de QA con SAIL CLI. --> |
| `as-is/`, `refactorizacion/` | Solo si hay una aplicación existente: cómo está hecha y cómo rehacerla |
| `entregables/`, `versiones/` | El DF en Word y la copia del análisis antes de cada cambio |
| `.agents/workflows/` | Los flujos, copiados del plugin |

Las carpetas que no siempre hacen falta las crea, con ese nombre, el script que escribe en ellas.

## Reglas

- **Git guarda el proyecto, no el código.** El código vive en Appian. Se trabaja sobre `main`, sin ramas ni PR.
- **Se sube todo, también las fuentes**, menos los secretos y las grabaciones de vídeo o audio (`.gitignore`). El repositorio lleva información del cliente: su remoto es privado y lo decide el proyecto.
- **Lo que se regenera no se fusiona.** Si chocan el Word, una captura o el PNG de un diagrama, se vuelve a generar.
- **La IA escribe en Appian solo en desarrollo** y, en una urgencia, en el entorno de corrección. A pruebas y a producción llega un paquete que ha revisado una persona (F9). <!-- (T12) Cómo se impide: el Dev MCP de los demás entornos, en solo lectura. -->
- **Las skills no se copian al proyecto.** Son las del plugin y la oficial de Appian (`appian`). Cada flujo dice cuál usar; una ruta que empieza por `appian-` es de la carpeta `skills/` del plugin.

## Flujos

Cada flujo dice cuándo se usa, sus pasos en orden, quién hace cada uno y dónde termina. «Script» es una orden del plugin, la lance quien la lance. «IA» es un trabajo que pide juicio: lo hace un agente con la skill que se nombra, o una persona con la misma referencia.

| Flujo | Cuándo |
|---|---|
{flujos}
