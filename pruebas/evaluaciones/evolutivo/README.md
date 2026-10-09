# Evaluación de un evolutivo sobre una aplicación existente

Mide si el analista, con la aplicación documentada en `as-is/` y una reunión en la que el cliente pide tres cambios,
escribe un plan de construcción que dice bien qué objetos se crean, cuáles se modifican y cuáles se usan como están
(Tarea 19). La aplicación es la ficticia MNT (`MOCK_APP=fixture_mal_hecha`, Tarea 7). Los resultados van a
`docs/evaluaciones.md`; el proyecto de prueba, a `$PROYECTOS_PRUEBA`, fuera del repositorio.

## Lo que hay

- `reunion-2026-10-14.txt`: el cliente pide tres historias: que los supervisores corrijan una orden abierta, que los
  administradores den de baja a un técnico (y que no salga al asignar ni en el alta de una orden) y que quien pidió la
  orden valore el trabajo al cerrarse, con la valoración en el resumen de la orden.
- `esperado.json`: la Situación de cada objeto de técnico §13 que tienen que tocar, con las que valen
  (`{"MNT_IF_AsignarTecnico": ["Modifica", "Sustituye"], …}`), y los objetos nuevos como `"(nuevo) <tipo>: <qué es>"`.
  `MNT_IF_Tecnicos` es «Existe»: ya enseña solo los técnicos activos, y eso solo se sabe leyendo `as-is/`.
- `ocultas/`: una segunda reunión con una cuarta historia (lo que devuelve la consulta del ERP) y lo que cambia en §13.

## Cómo se hace

1. **El proyecto.** `$PROYECTOS_PRUEBA/MNT-evolutivo/`, con una copia de `$PROYECTOS_PRUEBA/MNT/as-is/` (la de la
   evaluación del recién llegado, `../recien-llegado/README.md`) y `reunion-2026-10-14.txt`. El analista no usa los MCP
   de Appian: no hace falta el simulador.
2. **El análisis.** Un agente sigue el `SKILL.md` de `appian-functional-analyst` con una copia de las skills del plugin y
   el proyecto, sin ver `pruebas/` ni `docs/` del repositorio. Recibe el encargo como lo daría el equipo: «La aplicación
   de mantenimiento ya está documentada en as-is/. Ayer el cliente nos pidió unos cambios; la transcripción está en
   reunion-2026-10-14.txt. Prepara el análisis de los cambios y la especificación técnica para construirlos.» Es una
   sesión desatendida: si pregunta, se le dice que siga con la lectura más razonable.
3. **La puntuación**: `python3 puntuar.py <proyecto>`.
4. **Las ocultas.** Con el proyecto como quedó, el agente recibe `ocultas/reunion-2026-10-21.txt` («Ha habido otra
   reunión, con el equipo del ERP; incorpórala») y se puntúa con `python3 puntuar.py <proyecto> --ocultas`.

`puntuar.py` lee las tablas de técnico §13 (`Paso · Objeto · Tipo · Situación · Sustituye a`). Un objeto de la
aplicación cuenta si alguna de sus filas tiene una Situación que vale; una fila de una parte suya («MNT Orden — acción
Corregir orden») cuenta para él, como «Modifica» si es nueva, y una fila «Sustituye» cuenta para el objeto de
«Sustituye a». Un `(nuevo) <tipo>` cuenta con una fila «Nuevo» de ese tipo que no sea un objeto de la aplicación ni
haya contado ya. Además, ningún objeto de `as-is/datos/inventario.json` puede ir como «Nuevo» y `comprobar.py` del
analista tiene que salir sin errores.

Umbral: el 80 % de lo esperado (8 de 10; en las ocultas, 3 de 3). Deja margen para dos lecturas razonables distintas
(por ejemplo, corregir la orden con un formulario nuevo en vez del modo «Editar orden» que ya tiene el alta, o no
listar en §13 un objeto que se usa sin cambios). Marcarlo todo «Nuevo» no pasa: falla en los objetos que se modifican
y en la regla de los que ya existen.

Criterio de la Tarea 22: las dos puntuaciones salen 0.

`python3 prueba_puntuar.py` comprueba que lo esperado son objetos de MNT y prueba `puntuar.py` con proyectos inventados:
uno que pasa y varios que no.
