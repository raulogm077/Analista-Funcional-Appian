# appian-analisis-funcional

Repositorio único del plugin. Todo hilo, en la nube o en el equipo de Raúl, parte de aquí y sube aquí.

- Antes de empezar, `git pull`. Nunca se copia encima un plugin instalado ni una carpeta suelta: así se perdió trabajo con las dos 0.6.0-alpha.2.
- Aquí solo está el código del plugin y sus pruebas. Lo que el plugin genera al trabajar en un proyecto, también en los proyectos de prueba, va a la carpeta de ese proyecto, nunca a este repositorio.
- Ninguna skill lleva un proyecto, tampoco de ejemplo, ni la marca de un cliente. Las pruebas de cada skill y sus datos ficticios van en `pruebas/<skill>/`, que no entra en el paquete, y la marca de un cliente, en la carpeta de su proyecto (esto último se completa en la Tarea 0b del plan).
- El diseño aprobado está en `docs/diseno/`, el plan de implementación en `docs/plan/` y los resultados de las evaluaciones en `docs/evaluaciones.md`.
- Antes de cada commit: `python3 pruebas/comprobar_plugin.py --completo`, que pasa también las pruebas de ingeniería inversa. Solas: `python3 -m pytest -q pruebas/appian-reverse-engineering`; la de una skill: `python3 pruebas/<skill>/selftest.py`. Con `--plugin <carpeta>`, las mismas pruebas sobre otra copia del plugin (la del paquete).
- Nada del cliente en el repositorio: los ejemplos son ficticios y las transcripciones o salidas reales no se suben.
- Commits en español. La versión va en `.claude-plugin/plugin.json` y en la primera fila de versiones del README.
- El paquete `.plugin` se genera para entregarlo; no se versiona.
