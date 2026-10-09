# Evaluación de los comentarios de una demo

Mide si, tras la demo de un prototipo, el analista lleva cada comentario a su pantalla y prototipos rehace solo esas
pantallas, sin tocar las validadas por el cliente (🔒) mientras el analista no lo apruebe (Tarea 21). Todo es ficticio:
el préstamo de equipos audiovisuales de una organización de ejemplo. Los resultados van a `docs/evaluaciones.md`; el
proyecto de prueba, a `$PROYECTOS_PRUEBA`, fuera del repositorio.

## Lo que hay

- `proyecto/`: el proyecto de partida. Análisis 1.1 con seis pantallas (PAN-01 a PAN-06), de las que el cliente validó
  dos por correo (PAN-02 y PAN-05, 🔒); técnico en curso, decisiones y `proyecto.md`. `prototipo/generar_app.py`
  escribe el `app.json` de las seis pantallas con los helpers del kit, a partir de ese análisis.
- `fuentes/`: las dos fuentes que cita el análisis (la reunión de requisitos y el correo que valida las dos pantallas).
- `demo-2026-10-06.txt`: la transcripción de la demo, con un comentario por pantalla. Los de PAN-02 y PAN-05 cambian
  pantallas validadas; los otros cuatro son retoques que no necesitan aprobación.
- `esperado.json`: las PAN que cambian (`cambian`) y las validadas (`con_aprobacion`), con el minuto de cada comentario.
- `ocultas/`: un correo del cliente posterior a la demo con un comentario más sobre una pantalla, y lo esperado de esa
  segunda ronda.

## Cómo se hace

1. **El proyecto.** Copia `proyecto/` a `$PROYECTOS_PRUEBA/PRE-demo/` (`<p>`) y `demo-2026-10-06.txt` a `<p>/`. Cataloga
   las fuentes anteriores en su orden, para que sean FU-01 y FU-02:

   ```bash
   python3 <repo>/skills/appian-functional-analyst/scripts/leer_fuentes.py fuentes/01-reunion-2026-09-15.txt fuentes/02-correo-2026-09-29-validacion.eml -o <p>/fuentes/
   python3 <p>/prototipo/generar_app.py <p>/prototipo/app.json --kit <plugin>/skills/appian-prototipos
   ```

   Con un navegador, construye el HTML y las capturas que enlaza el funcional (`build.py` y `capture.py` del kit, con
   salida en `<p>/prototipo/`).
2. **La demo.** Un agente sigue los `SKILL.md` del analista y de prototipos con una copia de las skills del plugin y el
   proyecto, sin ver `pruebas/` ni `docs/` del repositorio. Recibe el encargo como lo daría el equipo: «Ayer hicimos la
   demo del prototipo con el almacén de medios; la transcripción está en demo-2026-10-06.txt. Incorpórala al análisis y
   actualiza el prototipo.» Cuando presenta los puntos que requieren aprobación, el evaluador aprueba el de PAN-02 y deja
   pendiente el de PAN-05 («Aplica el de la solicitud; el de entregar y recoger, de momento no»): así se miden las dos
   ramas. En una sesión desatendida los dos quedan pendientes y ninguna de las dos pantallas cambia.
3. **La puntuación**: `python3 puntuar.py <p>`. Compara `<p>/prototipo/app.json` con el de partida, que vuelve a escribir
   con `proyecto/prototipo/generar_app.py`.
4. **Las ocultas.** Guarda una copia de `<p>/prototipo/app.json` fuera del proyecto
   (`$PROYECTOS_PRUEBA/PRE-demo-ronda1.json`), dale al agente `ocultas/correo-2026-10-07.eml` («Nos ha llegado este correo
   de Formación sobre el prototipo; incorpóralo») y puntúa:

   ```bash
   python3 puntuar.py <p> --ocultas --antes $PROYECTOS_PRUEBA/PRE-demo-ronda1.json
   ```

`puntuar.py` busca cada pantalla por su PAN en el `ref` del `app.json` y la da por cambiada si su JSON no es igual,
como `validate.py --anterior`. Las de `cambian` tienen que cambiar. Las validadas tienen que tener su punto en el
informe de impacto de la demo («Encaja en» con su PAN y «Requiere: Sí»); cambian si ese punto tiene «Decisión: ✔» y
no cambian si sigue «Pendiente». En la segunda ronda, solo cambia la pantalla del correo. Además, el `app.json` pasa
`validate.py` sin errores.

Criterio de la Tarea 22: las dos puntuaciones salen 0.

`python3 prueba_puntuar.py` comprueba el caso (el análisis pasa `comprobar.py`, el prototipo de partida sale siempre
igual y sin avisos de `validate.py`, hay un comentario por pantalla) y prueba `puntuar.py` con proyectos inventados: uno
que pasa y varios que no.
