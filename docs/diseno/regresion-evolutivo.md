# Regresión en un evolutivo que toca un área

Análisis para que decida Raúl (petición del 6-nov, recogida por Codex; `siguiente-version.md` §2). No se ha cambiado
nada.

## Lo que hay hoy

- **F8, al construir cada issue**: `verificar` ejecuta los casos de prueba de sus objetos y los de quien los usa
  directamente (los de estos últimos salen como avisos).
- **F8, paso 8**: el QA de la unidad recorre solo sus escenarios.
- **F9, antes del paquete**: la regresión ejecuta todos los casos de prueba de la aplicación y `qa.py repetir <p>`
  repite los guiones de todas las unidades.

El hueco: mientras se construye un evolutivo, nadie repite los escenarios de otras unidades que pueden romperse por lo
que comparten. Se descubre en F9, al final, o no se descubre si sus guiones no distinguen la regla (E7: el filtro por
la fecha de fin pasaba el guion antiguo).

## Lo medido

En el proyecto de formación, EV-02 solo cambiaba un filtro de `FOR Solicitud`. Elegir los escenarios de EV-01 cuyas
issues comparten objeto con EV-02 selecciona **27 de 29**: el record type central lo comparte casi todo. Repetir todos
los guiones de EV-01 (23) con SAIL CLI tardó unos 9 minutos, sin IA.

## Las opciones

| Opción | Cómo | Pros | Contras |
|---|---|---|---|
| A. Como está | Solo F9 repite todo | Nada nuevo | Una regresión se ve al final, cuando ya está todo construido |
| B. Repetir todo en el QA de la unidad | En F8 paso 8, además de su QA, `qa.py repetir <p>` de todas las unidades | Una orden que ya existe; ve la regresión pronto; sin criterio que mantener | Tarda lo que tarden todos los guiones; en una aplicación grande, mucho |
| C. Elegir por objetos compartidos | Un script elige los escenarios de otras unidades cuyas issues comparten objeto | Menos que todo, en teoría | En la práctica selecciona casi todo (27 de 29); un script más que mantener |
| D. Elegir por la parte que cambia | Por filtro, acción o vista, no por objeto | Lo más preciso | Las filas de §13 de las unidades anteriores nombran objetos enteros: no hay con qué cruzar la parte sin cambiar cómo se escriben |

Ninguna resuelve lo que enseñó E7: si el guion no distingue la regla, repetirlo no detecta nada. Eso lo cubre la regla
de la skill de QA («lo que no debe salir incumple solo la regla que se prueba»).

## Recomendación

La B, por simplicidad: es una orden que ya existe, llevada al QA de cada unidad. Los fallos que ya estaban antes se
distinguen con el `resultado.json` anterior de cada unidad, que ya existe. Si en una aplicación grande tarda demasiado,
entonces medir la C con datos de esa aplicación antes de construirla. La D no compensa hoy.

## Lo que decide Raúl

1. **La B**, repetir todos los guiones en el QA de cada unidad (recomendada).
2. **La A**, dejarlo como está, sabiendo que la regresión se ve en F9.
3. **La C**, si prefiere seleccionar aunque hoy seleccione casi todo.
