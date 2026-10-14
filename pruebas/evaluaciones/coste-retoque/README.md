# Prueba de coste: el texto de un botón construido

Mide si un retoque sobre algo ya construido sigue siendo ligero con unidades de cambio. El cliente pide cambiar el texto
de un botón de una pantalla que está en producción: eso no pide aprobación por punto ni DT, se aplica con `comprobar.py`
sin errores en una sola pasada, no regenera ningún documento y cabe en un tope de llamadas fijado antes de medir. Todo
es ficticio. Los resultados van a `docs/evaluaciones.md`; el proyecto de prueba, a `$PROYECTOS_PRUEBA`, fuera del
repositorio.

## Lo que hay

- El proyecto es el de `../evolutivo-urgencia/` («Solicitudes de material», sin `as-is/`): `EV-01` en producción y
  `EV-02`, la firma de la revisión, aprobada. Sin urgencia. Se monta con su `montar.py`.
- `correo-2026-10-08-boton.eml`: la jefa de Servicios generales pide que el botón «Nueva solicitud» del panel diga
  «Pedir material». El panel (PAN-01, `DEM_Dashboard`) está construido en `EV-01`, validado por el equipo (✅, no 🔒) y
  fuera de `EV-02`: nada pide aprobación (`indice.py ficha PAN-01` dice «Construido: EV-01 · En curso: —»), y una
  interfaz no pide DT «Cambio sobre lo construido» (`references/cambios.md` §4).
- `esperado.json`: los puntos, el tope de llamadas y el umbral, fijados antes de medir.

## Cómo se hace

1. **El proyecto.**

   ```bash
   python3 ../evolutivo-urgencia/montar.py "$PROYECTOS_PRUEBA/DEM-retoque" --fuente correo-2026-10-08-boton.eml
   ```

   Lo mismo que en `../evolutivo-urgencia/` (fuentes FU-01 a FU-04, capturas, los dos Word entregados si hay Node con
   `docx`, las issues de `EV-02` y la huella `DEM-retoque.montaje.json` junto a la carpeta), con este correo en la
   carpeta en vez de la incidencia. Con `PLUGIN_A_PROBAR=<carpeta>` usa esa copia del plugin.
2. **El retoque, a ciegas.** Un agente sigue el `SKILL.md` de `appian-functional-analyst` con una copia de las skills
   del plugin y el proyecto, sin ver `pruebas/` ni `docs/` del repositorio, en una sesión desatendida: si pregunta, se
   le dice que siga con la lectura más razonable. Recibe el encargo como lo daría el equipo:

   > Ha llegado este correo de Servicios generales sobre el panel (correo-2026-10-08-boton.eml); incorpóralo.

3. **Contar**, en la sesión del agente, desde el encargo hasta su último mensaje:
   - **N**: todas sus llamadas a herramientas: cargar la skill, leer, buscar, ejecutar, editar, escribir, las de
     seguimiento de tareas y las de sus subagentes, si lanza alguno.
   - **K**: las veces que ejecutó `comprobar.py` (con cualquier opción) y salió con errores («✗» y «N comprobaciones con
     errores»).
4. **La puntuación**:

   ```bash
   python3 puntuar.py "$PROYECTOS_PRUEBA/DEM-retoque" --llamadas N --comprobar-con-errores K
   ```

## Qué se mide

| Punto | Se cumple si |
|---|---|
| `hecho` | El correo está catalogado, su informe de impacto (`impacto/<FU>.md`) aplicado, la ficha de PAN-01 dice «Pedir material» y técnico §13 tiene `DEM_Dashboard` «Modifica» en una unidad Abierta, que el jefe de proyecto aprobará una vez. No hacer nada no pasa, ni meterlo en `EV-02`, ya aprobada con su alcance (la devolvería a aprobación: `issues` y `construida` fallan con «ha crecido»), ni dejar la fila sin unidad (quedaría en `EV-01`, en producción, y no se construiría) |
| `sin_aprobacion` | Ningún punto de ese informe pide aprobación («Requiere: Sí…») ni queda «Pendiente». Que esté construido sale, como mucho, en «Posible petición de cambio» del Resumen |
| `sin_dt` | Ninguna DT «Cambio sobre lo construido» nueva (la de `EV-02` ya estaba) |
| `comprobar_una_pasada` | `comprobar.py` sin errores, con `--fuentes`, y K = 0 |
| `sin_word_ni_capturas` | Ningún `.docx`, `.pdf` ni `.png` (salvo en `fuentes/`) nuevo o distinto del montaje: el Word y las capturas se regeneran al enviar o al construir, no con cada fuente |
| `llamadas` | N ≤ 25 |

## Criterio

Umbral: los seis. Cada punto es un coste que un retoque no necesita (una aprobación, una DT, una vuelta de correcciones,
un documento regenerado, llamadas de más); con que vuelva uno, el retoque ya no es ligero, que es lo que esta prueba
mide. `hecho` evita que pase sin hacer el cambio. La puntuación sale 0.

## El tope: 25 llamadas

Fijado antes de medir (0.7.0-beta.2) y no se cambia. El camino corto de un retoque (`actualizacion.md`, «Camino corto»,
desde la 0.7.0-beta.3) lo deja así:

| Paso | Llamadas |
|---|---|
| Cargar la skill y `proyecto.py estado` | 2 |
| Leer `actualizacion.md` (su «Camino corto» cubre las unidades: `cambios.md` no hace falta) | 1 |
| Catalogar el correo (`leer_fuentes.py`) y leerlo | 2 |
| `proyecto.py cambio … EV-03 abrir`: `EV-02` está Aprobada, y una fuente nueva para ella la devolvería a aprobación | 1 |
| `indice.py ficha PAN-01 --lineas` e `indice.py impacto PAN-01 --cambio EV-03` (las señales y la fila de §13) | 2 |
| `proyecto.py version … --decision CAMBIA …`: la copia, la 1.2 en los dos, la fila de la versión, la D-01 y la fuente en `proyecto.md` | 1 |
| Funcional: leer el tramo de PAN-01 y editarlo (la herramienta de edición pide leer antes) | 2 |
| Técnico: leer el tramo de §7 a §13 y editar §7 y la fila de §13 | 3 |
| El informe, ya aplicado, de una vez | 1 |
| `comprobar.py --anterior --impacto --fuentes` | 1 |
| **Total** | **16** |

`prueba_puntuar.py` recorre este camino con las órdenes del plugin y comprueba que son 16 llamadas y que la pasada de
`comprobar.py` sale sin errores. El tope deja 9 de margen para lo razonable que no está en esa cuenta: `requisitos.py`
al empezar, `indice.py resumen`, leer `cambios.md`, una búsqueda más o leer una plantilla. Lo que ya no cabe es lo que
un retoque no necesita: regenerar el Word, el prototipo o las capturas, escribir una DT, presentar puntos para
aprobarlos, leer el funcional o el técnico enteros o dar una vuelta de correcciones a `comprobar.py`. Cada uno suma de 2
a 10 llamadas. En la 0.7.0-beta.2, con el camino entero (22 llamadas como mínimo), las tres pasadas costaron 34, 34 y 47
(`docs/evaluaciones.md`).

## Lo que no mide

La calidad del análisis más allá de `comprobar.py` (que «Nueva solicitud» se quede en técnico §7, por ejemplo) ni la
issue de la unidad nueva, que se escribe al aprobarla.

## Prueba del puntuador

`python3 prueba_puntuar.py` monta el proyecto, comprueba el caso (PAN-01 construida, ✅ y fuera de `EV-02`, el correo, el
tope, el camino más corto) y prueba `puntuar.py` con proyectos inventados: ese camino, que pasa, y variantes que no (una
llamada de más, una pasada con errores, la aprobación por construido, una DT, el Word o una captura regenerados, la fila
sin unidad o en `EV-02`, nada hecho). Lee el plugin de `PLUGIN_A_PROBAR`.
