# Evaluación de malas prácticas sembradas

Mide si refactorización encuentra, a partir de `as-is/` y nada más, lo que está mal hecho en una aplicación, con la
regla que lo trata y una alternativa. La aplicación es la ficticia MNT (`MOCK_APP=fixture_mal_hecha`, Tarea 7), con 11
malas prácticas en `../aplicacion-ficticia/malas-practicas.json` y 3 más, escritas a ciegas, en `ocultas/`. Los
resultados van a `docs/evaluaciones.md`; el proyecto de prueba, a `$PROYECTOS_PRUEBA`, fuera del repositorio.

## Cómo se hace

1. **El proyecto.** `$PROYECTOS_PRUEBA/MNT/`, con el `as-is/` que hizo ingeniería inversa en la evaluación del recién
   llegado (`../recien-llegado/README.md`). Refactorización no usa los MCP de Appian: no hace falta el simulador.
2. **La propuesta.** Un agente sigue el `SKILL.md` de `appian-refactorizacion` con una copia de las skills del plugin y
   el proyecto, sin ver `pruebas/` ni `docs/` del repositorio (estarían las respuestas). Recibe el alcance y los límites
   como los daría el equipo: toda la aplicación, un plazo de seis meses y nada de lo que no es de la aplicación (las
   reglas `CMN_`) se puede tocar. Escribe `<proyecto>/refactorizacion/propuesta.md`.
3. **La puntuación**:

   ```bash
   python3 puntuar.py <proyecto>/refactorizacion/propuesta.md <proyecto>/as-is
   python3 puntuar.py <proyecto>/refactorizacion/propuesta.md <proyecto>/as-is --ocultas
   python3 <repo>/skills/appian-refactorizacion/scripts/comprobar_propuesta.py <proyecto>
   ```

Cada mala práctica lleva en `bp_aceptadas` las secciones de buenas prácticas que la tratan, empezando por la de `bp`:
las que, leídas, dan el problema y su alternativa, no las que solo tocan el tema. Se fijan con la descripción y las
secciones (`seccion.py nn x`), nunca mirando una propuesta. Una mala práctica cuenta si una REF cita en su evidencia
alguno de sus objetos, tiene en su Regla una de sus `bp_aceptadas`, la sección exacta («§1» no vale por «§1.3» si la
lista no lo dice), y sale en Solución. Pendientes tiene que citar los NV de los objetos de fuera de la
aplicación (en MNT, el de las reglas `CMN_`, que usan las malas prácticas 2, 3 y 4). `puntuar.py` sale 0 con el 90 % o
más y esa cita.

Criterio de la Tarea 15: 10 de 11 visibles y 3 de 3 ocultas, las dos puntuaciones salen 0 y `comprobar_propuesta.py` no
da errores.

`python3 prueba_puntuar.py` prueba `puntuar.py` con una propuesta inventada.
