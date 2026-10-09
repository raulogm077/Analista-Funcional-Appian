---
name: appian-refactorizacion
description: "Refactorización de aplicaciones Appian: a partir de lo que documentó la ingeniería inversa (as-is/), plantea cómo debería estar hecha una aplicación existente, entera o una parte, con buenas prácticas y eficiencia. Escribe refactorizacion/propuesta.md: el diagnóstico de cada problema con su evidencia y la regla de buenas prácticas que incumple, la solución por capas (datos, seguridad, procesos, pantallas, integraciones), la migración y la convivencia con lo actual, la hoja de ruta y lo que falta por decidir. Úsala después de ingeniería inversa cuando se quiera rehacer o mejorar una aplicación, o decidir si se rehace o se evoluciona, aunque no se diga «refactorización». No documenta la aplicación (appian-reverse-engineering), no escribe requisitos ni la especificación objeto a objeto (appian-functional-analyst), no revisa un objeto suelto (appian-best-practices) y no crea ni modifica objetos."
---

# Refactorización · Appian

Plantea cómo debería estar hecha una aplicación Appian que ya existe, entera o una parte, a partir de lo que documentó
la ingeniería inversa. Un solo documento, `refactorizacion/propuesta.md`: qué está mal hecho y por qué, cómo debería
estar, cómo se pasa de lo que hay a lo nuevo y qué falta por decidir.

`<skill>` es la carpeta de este fichero y `<p>`, la del proyecto. En Windows, `python` en vez de `python3`.

## Qué hace y qué no

| Esta skill | Lo hace otra |
|---|---|
| Diagnostica cada problema con su evidencia en `as-is/` y la regla de buenas prácticas que incumple | Documentar la aplicación: `appian-reverse-engineering` |
| Propone la solución por capas, hasta entidades, procesos y patrones de pantalla | Bajarla a objetos, campos y nodos: el técnico de `appian-functional-analyst`, que cita cada REF |
| Dice cómo pasan los datos y cómo conviven lo viejo y lo nuevo | Requisitos y DF para el cliente: `appian-functional-analyst` |
| Aplica las reglas de buenas prácticas a la aplicación entera o a una parte | La doctrina y la revisión de un objeto suelto: `appian-best-practices` |
| — | Dibujar procesos: `appian-diagramas-bpmn` |
| — | Crear o modificar objetos en un entorno |

## Entradas

- **`as-is/`**, escrito por `appian-reverse-engineering`. No se vuelve a leer el entorno.
  - `as-is/datos/`: inventario, dependencias, hallazgos, procesos y lo que quedó sin verificar. Es la base del
    diagnóstico. Formato en `<skill>/../appian-reverse-engineering/references/datos.md`.
  - `as-is/LEEME.md` (entorno, versión de Appian, confianza y lo que no incluye), los documentos `01`–`11`,
    `INVENTARIO.md` y el `anexo/`: se leen para entender y se enlazan como evidencia.
  - La extracción en bruto es interna de ingeniería inversa: no se lee ni se enlaza.
- **El alcance**: la aplicación entera o qué módulos y procesos.
- **Los límites del equipo**: plazo y lo que no se puede tocar (otras aplicaciones, contratos externos, tablas
  compartidas).

Sin `as-is/datos/inventario.json` no se empieza: primero, ingeniería inversa.

## Flujo

1. **Base.** Lee `as-is/LEEME.md` y `as-is/datos/`. Di al usuario en pocas líneas qué hay: objetos, procesos,
   hallazgos por severidad y lo que quedó sin verificar.
2. **Alcance y límites.** Si no los ha dado, pregúntalos en un solo mensaje: qué se rehace, plazo y qué no se puede
   tocar. Sin respuesta, la aplicación entera y sin plazo, y el Alcance lo dice.
3. **Propuesta.** Lee entero `agents/arquitecto-refactorizacion.md` y síguelo, o pásaselo a un subagente con
   `<skill>`, `<p>`, el alcance, los límites y el apartado «Dudas de Appian» de este fichero. Escribe
   `refactorizacion/propuesta.md` con `assets/plantillas/propuesta.md` y las señales de `references/senales.md`.
4. **Comprobar.** `python3 <skill>/scripts/comprobar_propuesta.py <p>`, sin errores antes de entregar: apartados y
   fichas completos, evidencia que existe en `as-is/`, reglas que buenas prácticas tiene, objetos del Diagnóstico que
   están en el inventario, cada REF con su alternativa en la Solución y los `H-…` y NV que existen. Sus avisos (una REF
   fuera de la Hoja de ruta o sin su «Verificar H-…» antes) se corrigen.
5. **Entregar.** En pocas líneas: qué se rehace, los problemas de prioridad Alta, la estrategia, las fases y lo que
   tiene que decidir el equipo o el cliente. Después, el analista escribe el funcional (lo que se conserva y lo que
   cambia) y el técnico, que baja a objetos cada REF.

Reglas que no se negocian:

- **Hechos del as-is, propuesta propia.** El Diagnóstico solo afirma lo que está en `as-is/` y lo enlaza; la Solución
  propone, y un objeto nuevo que proponga no está en el inventario.
- **Una REF por problema.** Si dos hallazgos tratan del mismo objeto y del mismo problema visto por dos señales (un
  proceso huérfano y sin ejecuciones), una sola REF cita los dos `H-…`.
- **Lo pendiente no se da por hecho.** Una REF sobre un hallazgo inferido (🔶) o pendiente (❓) lo dice, y la Hoja de
  ruta pone antes «Verificar H-…». Lo que ingeniería inversa no pudo verificar y condiciona la solución va a
  Pendientes con su NV.
- **Cada regla, de buenas prácticas.** La Regla de una REF es una sección de `appian-best-practices` («BP nn §x»),
  nunca un consejo de memoria.

## Qué escribe

- `refactorizacion/propuesta.md`

Nada más: no toca `as-is/` ni `analisis/`.

## Dudas de Appian

Lo que no sepas con certeza de Appian se consulta en el MCP de documentación `appian-docs` (sus herramientas llevan `appian-docs` en el nombre o su descripción habla de buscar en la documentación de Appian) antes de escribirlo, nunca de memoria: si existe un componente, una función, un parámetro o un objeto, qué admite, sus límites, si depende de la licencia y desde qué versión.
- Una duda por consulta, escrita como una frase completa.
- Vale lo que diga la documentación de la versión del entorno del proyecto (va en la URL: `/help/26.6/`). Si solo lo dice una versión posterior, se avisa de que puede no estar disponible.
- Lo que se escribe a partir de la respuesta lleva su URL, en la forma `/latest/`.
- Sin el MCP, se consulta docs.appian.com con WebFetch o WebSearch. Si tampoco se puede, se escribe «sin verificar» y la duda pasa a pendientes.
- Qué conviene hacer (qué mecanismo elegir, cómo diseñarlo) no es una duda de documentación: se consulta en `appian-best-practices`, solo la sección que toca. Esa skill está junto a esta: `python3 <esta skill>/../appian-best-practices/scripts/seccion.py 02 4.8` imprime solo §4.8 del doc 02.

**En la refactorización**, buenas prácticas es la fuente principal: la Regla de cada REF es la sección que imprime
`seccion.py nn x`, y cada decisión de la Solución se apoya en ella (`00-solution-decisions.md` dice qué mecanismo
elegir). Al MCP de documentación se le pregunta si lo que se propone existe en la versión del entorno, que dice
`as-is/LEEME.md`, y sus límites (filas de un record type sincronizado, eventos de record, tier). Su URL va en el «Por
qué» de la Solución; lo que quede sin verificar va a Pendientes.

## Recursos

| Fichero | Cuándo |
|---|---|
| `agents/arquitecto-refactorizacion.md` | Al empezar la propuesta: criterio y pasos |
| `references/senales.md` | En el diagnóstico: qué buscar en `as-is/` y qué sección de buenas prácticas lo trata |
| `assets/plantillas/propuesta.md` | Al escribir la propuesta |
| `scripts/comprobar_propuesta.py` | Antes de entregar |
