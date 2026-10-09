# Evaluación de incoherencias con un DF ya validado

Mide si el analista, con el DF del cliente ya validado y reuniones anteriores a él, encuentra lo que las reuniones dicen
distinto del DF, lo pone en su pieza como pendiente de aprobación y no lo aplica (modo «DF ya hecho», Tarea 21). Todo es
ficticio: el Consorcio Cultural de Montelar y sus ayudas a proyectos culturales. Los resultados van a
`docs/evaluaciones.md`; el proyecto de prueba, a `$PROYECTOS_PRUEBA`, fuera del repositorio.

## Las fuentes

- `fuentes/DF-ayudas-cultura-v1.0-2026-06-19.md`: el DF del cliente, versión 1.0 y validado, con sus propios IDs (ROL-,
  PR-, RF-, RN-, NT-, IU-).
- `fuentes/reunion-2026-05-06.txt`, `reunion-2026-05-20.txt` y `reunion-2026-06-03.txt`: tres reuniones anteriores al DF,
  con marcas `[hh:mm:ss] Persona:`.

Las reuniones tienen 10 incoherencias con el DF (`esperado.json`) y 3 más que solo están en `ocultas/esperado.json`,
mezcladas con las demás. Son de tipos distintos: un campo obligatorio, el tamaño de un documento, dos plazos (uno dicho
de pasada), un estado, dos reglas, un perfil que resuelve, un aviso y lo que ve un perfil. Además, tres frases dicen lo
mismo que el DF con otras palabras (tipo «SIN IMPACTO» en `esperado.json`): no deben salir como cambio. El resto de lo que
se dice coincide con el DF o es conversación.

## Cómo se hace

1. **El proyecto.** `$PROYECTOS_PRUEBA/AYC-incoherencias/`, vacío salvo `fuentes/` con copia de las cuatro fuentes.
2. **El análisis.** Un agente sigue el `SKILL.md` de `appian-functional-analyst` con una copia de las skills del plugin y
   el proyecto, sin ver `pruebas/` ni `docs/` del repositorio. Recibe el encargo como lo daría el equipo: «El cliente nos
   ha pasado su DF, ya validado (versión 1.0), y las transcripciones de tres reuniones anteriores con el Servicio de
   Cultura. Están en fuentes/. Prepara el análisis.» Es una sesión desatendida: nadie aprueba nada, y si pregunta se le
   dice que siga. Escribe el funcional y los informes de impacto en el proyecto.
3. **La puntuación**:

   ```bash
   python3 puntuar.py <proyecto>
   python3 puntuar.py <proyecto> --ocultas
   ```

`puntuar.py` busca cada incoherencia en los informes de impacto (`<proyecto>/impacto/*.md`): un punto que cita su reunión
en su minuto (o en la intervención anterior o en una de las dos siguientes), encaja en su pieza y requiere aprobación
con la decisión pendiente. La pieza se reconoce por el ID original del DF, que el funcional lleva en su comentario de
trazabilidad (`**HU-03 — Título** <!-- 🔒 FU-01 RF-07 -->`); también vale citar ese ID en «Encaja en». Comprueba
además que ninguna se aplicó: las piezas con su ID original siguen como en `versiones/v1.0` y 🔒; sin esa copia, que no
dicen lo de la reunión (`reunion` en `esperado.json`). Y que las tres coincidencias no salen como cambio. El tipo del
punto se imprime, pero no cuenta.

Criterio de la Tarea 22: todas, las 10 visibles y las 3 ocultas, sin ninguna aplicada ni ninguna coincidencia como
cambio; las dos puntuaciones salen 0.

`python3 prueba_puntuar.py` comprueba que lo esperado encaja con las fuentes y prueba `puntuar.py` con proyectos
inventados: uno que pasa y varios que no.
