# Regresión en un evolutivo que toca un área

Análisis para que decida Raúl (petición del 6-nov, recogida por Codex; `siguiente-version.md` §2). No se ha cambiado
nada del plugin. Revisado con Codex el 6-nov: sus cuatro precisiones están incorporadas.

## Lo que hay hoy

- **F8, al construir cada issue**: `verificar` ejecuta los casos de prueba de sus objetos y los de quien los usa
  directamente (los de estos últimos salen como avisos).
- **F8, paso 8**: el QA de la unidad recorre solo sus escenarios.
- **F9, antes del paquete**: la regresión ejecuta todos los casos de prueba de la aplicación y `qa.py repetir <p>`
  repite los guiones de todas las unidades.

El hueco: mientras se construye un evolutivo, nadie repite los escenarios de otras unidades que pueden romperse por lo
que comparten. Se descubre en F9, al final, o no se descubre si sus guiones no distinguen la regla (E7: el filtro por
la fecha de fin pasaba el guion antiguo).

## Lo medido, y lo que no

- **Cuánto selecciona cruzar por objeto, en este proyecto.** EV-02 solo cambiaba un filtro de `FOR Solicitud`. Elegir
  los criterios de EV-01 cuyas issues comparten objeto con EV-02 selecciona 27 de 29: aquí un record type central lo
  comparte casi todo. Una aplicación modular puede dar otra cifra; no se ha medido.
- **Cuánto cuesta repetir todo.** Los 23 guiones de EV-01 suman 318 s en su último `resultado.json` (unos 5 minutos de
  ejecución, sin IA). No incluye entrar con cada cuenta ni preparar datos, y no es tiempo de pared medido. Criterios
  (29) y guiones (23) no son la misma población: algunos criterios no tienen guion.
- **Sin medir:** ninguna opción se ha comparado con otra en un cambio aislado y en otro compartido.

## Las opciones

| Opción | Cómo | Pros | Contras |
|---|---|---|---|
| A. Como está | Solo F9 repite todo | Nada nuevo | Una regresión se ve al final, cuando ya está todo construido |
| B. Repetir todo en el QA de la unidad | En F8 paso 8, además de su QA, `qa.py repetir <p>` de todas las unidades | Una orden que ya existe; ve la regresión pronto; sin criterio que mantener | El coste crece con la aplicación; una orden sencilla puede tardar mucho |
| C. Elegir por objetos compartidos | Un script elige los escenarios de otras unidades cuyas issues comparten objeto | Menos que todo, en teoría | En este proyecto selecciona casi todo (27 de 29); un script más que mantener |
| D. Elegir por la parte que cambia | Por filtro, acción o vista, no por objeto | Lo más preciso | La plantilla del técnico ya admite nombrar la parte en §13 (el proyecto de formación lo hace en una fila: «FOR Solicitud — filtro fechaInicio»), pero no todas las filas lo hacen: un cruce automático completo no sería fiable sin revisar cómo se escriben |
| E. Selección razonada | Quien conoce el cambio elige, con técnico §14, los criterios, los roles y los guiones que hay, qué escenarios de otras unidades repetir, y los repite con `qa.py repetir <p> <U> --escenario …` | Proporcional al cambio; sin script ni ficha nuevos | Depende del juicio: puede dejar fuera un efecto indirecto; tiene que decir qué no repitió |

Ninguna resuelve lo que enseñó E7: si el guion no distingue la regla, repetirlo no detecta nada. Eso lo cubre la regla
de la skill de QA («lo que no debe salir incumple solo la regla que se prueba»).

**Distinguir un fallo que ya estaba de una regresión.** El `resultado.json` anterior no basta: `qa.py repetir` lo
sobrescribe, y puede ser de otra versión de la issue o de otros datos. Sirve el que quedó en el historial de git del
proyecto, si es de la misma versión y de los mismos datos; si no lo hay, el origen del fallo queda sin determinar, y se
dice. No hace falta otro registro.

## Recomendación

La E por defecto, y la B cuando el impacto es global o no se sabe bien (un record type central, la seguridad, un
proceso que usan varias unidades). F9 se queda entero. Antes de escribirlo en F8, medir las dos (E y B) en un cambio
aislado y en otro compartido, con su tiempo y lo que cada una detecta. La B sola es la opción conservadora, pero que
cueste menos no está demostrado.

## Lo que decide Raúl

1. **E por defecto y B cuando el impacto es global o incierto**, medidas antes en dos casos (recomendada).
2. **B siempre**: repetir todos los guiones en el QA de cada unidad, sabiendo que el coste crece con la aplicación.
3. **A**: dejarlo como está, sabiendo que la regresión se ve en F9.
