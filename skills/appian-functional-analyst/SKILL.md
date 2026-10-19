---
name: appian-functional-analyst
description: "Analista funcional de Appian. Convierte las fuentes (reuniones, correos, actas, notas, diagramas de flujo, un DF o ERS del cliente, la documentación de una aplicación o una propuesta de refactorización) en el diseño funcional en Word que valida el cliente (proceso, historias, pantallas y escenarios) y la especificación técnica. Úsala para levantar requisitos, escribir o actualizar un análisis o un DF, incorporar una reunión, un correo, una demo o los comentarios al DF, añadir historias a una aplicación existente, redactar las historias de una pantalla que alguien explica, preparar la especificación técnica o llevar un evolutivo o una incidencia urgente (la registra y prepara su corrección). No dibuja procesos (appian-diagramas-bpmn), no hace prototipos (appian-prototipos), no construye, revisa ni diagnostica objetos (appian-best-practices), no documenta lo que ya existe (appian-reverse-engineering) ni decide si rehacerlo (appian-refactorizacion)."
---

# Analista funcional · Appian

Convierte lo que el cliente dice y escribe en dos documentos con una sola fuente:
- **el diseño funcional** (`analisis/funcional.md`), que el cliente valida y del que sale el DF en Word;
- **la especificación técnica** (`analisis/tecnico.md`), con todo lo necesario para construir con el MCP de
  desarrollo de Appian sin preguntar ni suponer.

Sirve para cualquier proceso: perfiles, datos, estados y reglas salen de las fuentes del proyecto. Los
fragmentos de `references/funcional-plantilla.md` y `references/tecnico-plantilla.md` enseñan el formato con un
caso ficticio; no se copian sus nombres.

`<skill>` es la carpeta de este fichero y `<p>`, la del proyecto. En Windows, `python` en vez de `python3`.

## Qué hace y qué no

| Esta skill | Lo hace otra |
|---|---|
| Lee las fuentes, decide qué contiene el análisis y lo mantiene reunión a reunión | — |
| Describe cada proceso (pasos, carriles, decisiones) | Lo dibuja `appian-diagramas-bpmn` |
| Dice qué hace cada pantalla y quién la usa | La compone y la captura `appian-prototipos` |
| Diseña la solución técnica aplicando buenas prácticas | La doctrina está en `appian-best-practices`, que se consulta por secciones |
| Usa la descripción de una aplicación existente como fuente (`as-is/`) | La escribe `appian-reverse-engineering` |
| Valida con el cliente la propuesta de refactorización y la baja a objetos en el técnico | La escribe `appian-refactorizacion` (`refactorizacion/propuesta.md`) |
| — | Construir o revisar objetos en un entorno: `appian-best-practices` con el MCP de desarrollo |

## Requisitos

Antes de la primera tarea: `python3 <skill>/../../requisitos.py --skill appian-functional-analyst`. Dice qué falta en el
equipo, qué se pierde y cómo se instala. Si falta algo para esta tarea, díselo una vez y sigue. Sin `requisitos.py` (copia suelta), sigue sin comprobar.

Los correos `.msg` no se leen de forma fiable: pide el correo como `.eml` o PDF.

## Principios

- **No inventar.** Lo que las fuentes no dicen no se escribe: se pregunta (PC). Cada pieza lleva su estado
  y su fuente en un comentario de trazabilidad (`funcional-plantilla.md`). Lo validado por el cliente (🔒)
  solo cambia con el visto bueno del analista.
- **Una sola vez.** Cada cosa vive en un sitio y los demás la citan por su ID: el comportamiento en las
  historias, la composición de las pantallas en el prototipo, el cómo en la especificación técnica.
- **Escrito para leerse.** Frases cortas, concretas, con las palabras del cliente y sin relleno
  (`redaccion.md`). El DF no habla de Appian.
- **Contradicciones a la vista.** Ninguna se resuelve en silencio: se registra la decisión
  (`decisiones.md`) o se pregunta (PC).
- **Confidencialidad.** Las fuentes y el análisis son del cliente: no se publican ni se envían a servicios
  externos (conversores, renderizadores públicos de diagramas). Los nombres de las personas solo están en
  las notas de las fuentes.

## La carpeta del proyecto

Un repositorio git por proyecto, siempre con la misma forma (la de «Qué escribe», más `as-is/` de ingeniería inversa y
`qa/` de `appian-qa`): el código vive en Appian y aquí va todo lo demás, también las fuentes. Lo crea `proyecto.py iniciar`.
`AGENTS.md` y `.agents/workflows/` salen enteros del plugin y no se editan: `proyecto.py iniciar <p>` en un proyecto
que ya existe los pone al día y no toca nada más. Se trabaja sobre main, sin ramas ni PR, con `git commit` y `git push`
al terminar; `iniciar` no confirma ni sube nada, y el remoto, privado, lo decide el proyecto.

Formatos: `funcional-plantilla.md`, `tecnico-plantilla.md` y la cabecera de `decisiones.md` en
`assets/plantillas/`. `proyecto.py estado <p>` dice en qué punto está el proyecto: empieza siempre por ahí
si el proyecto ya existe. Avisa también, sin frenar nada, de lo que falta por subir, de si va por detrás del remoto
(entonces, `git pull`) y de lo que `iniciar` tiene que poner al día. Si dice que al proyecto le falta git, `AGENTS.md`
o los flujos, lanza `proyecto.py iniciar <p>` antes de seguir: los añade y no toca nada más.

## Qué escribe

En `<p>`:
- `proyecto.md`: el estado del proyecto
- `.appian-plugin.json`: la ruta local del plugin para resolver scripts y referencias desde cualquier agente;
  `iniciar` la escribe y git la ignora (cada equipo tiene su ruta).
- `AGENTS.md`: dónde está cada cosa, las reglas y los flujos; lo genera entero `proyecto.py iniciar`
- `CLAUDE.md`: solo «@AGENTS.md»; si ya existe, no se toca
- `.agents/workflows/`: la copia de los flujos del plugin, generada
- `.gitignore`: lo que no se sube; si ya existe, no se toca
- `.gitattributes`: git no cambia los finales de línea; si ya existe, no se toca
- `fuentes/`: las fuentes catalogadas, con su índice y sus adjuntos
- `notas/`: una nota por fuente
- `impacto/`: un informe por fuente nueva
- `impacto/URG-nn.md`: la ficha de un cambio urgente (`urgentes.md`)
- `analisis/cambios.md`: las unidades de cambio, solo con `proyecto.py cambio` (`cambios.md`)
- `construccion/<U>/`: las issues de construcción de una unidad aprobada: `indice.md` y, por issue, `ISS-nn.md`, `ISS-nn.feature` e `ISS-nn-esperado.json`; se escriben al aprobarla (`proyecto.py cambio`) y con `indice.py issues`, que con `--siguiente` anota además quién tiene cada una
- `analisis/funcional.md`: el diseño funcional
- `analisis/tecnico.md`: la especificación técnica
- `analisis/decisiones.md`: las versiones y las decisiones del cliente
- `analisis/grafo.json`: las piezas y sus referencias, si se pide (`indice.py grafo`)
- `analisis/diagramas/<proceso>.json`: cada proceso, en el formato de `appian-diagramas-bpmn`
- `analisis/diagramas/<nombre>.mmd`: los diagramas de estados y de datos
- `entregables/`: el DF en Word y, para revisarlo, su PDF (`entregables/revision/`)
- `versiones/`: la copia del análisis antes de cada cambio
- `modulos/`: el funcional y el técnico de cada módulo, en un análisis grande (`volumen-grande.md`)
- `prototipo/`: solo la crea vacía al iniciar el proyecto; la llena `appian-prototipos`

El `.drawio`, el `.png` y el `.bpmn` de cada proceso y la imagen de cada `.mmd` los escribe `appian-diagramas-bpmn`.

## Modos

| Modo | Cuándo | Qué sale |
|---|---|---|
| **Síntesis** | Reuniones, correos, notas | Funcional y diagramas; el técnico cuando el funcional esté estable o se pida; DF en Word |
| **DF ya hecho** | Hay un DF o una ERS del cliente | El DF entra como versión 1.0 en el formato del plugin, sin reinterpretar: cada pieza 🔒 con su ID original en la trazabilidad (`<!-- 🔒 FU-01 RF-07 -->`); funcional y técnico, y el Word al enviarlo. Las reuniones anteriores al DF pasan por el informe de impacto y lo que no coincide con el DF requiere aprobación; las posteriores, como siempre (`ingesta-fuentes.md`, `actualizacion.md`) |
| **Evolutivo** | Hay que cambiar o ampliar una aplicación existente (`as-is/`) | Como síntesis, con lo de «Aplicación existente»: la situación de cada objeto; cada cambio que se construye, una unidad (`cambios.md`) |
| **Refactorización** | Hay una propuesta de refactorización (`refactorizacion/propuesta.md`) | Como evolutivo: el DF dice lo que se conserva, lo que cambia y lo nuevo; el técnico baja cada REF a objetos, con «Sustituye a» y la migración de datos |
| **Actualización** | Ya hay análisis y llega una reunión, un correo o los comentarios al DF | Informe de impacto y cambios puntuales: `actualizacion.md`; un retoque que nadie tiene que aprobar, por su «Camino corto» |
| **Pantalla suelta** | Alguien explica una pantalla, con o sin captura | La ficha PAN y sus historias, en el chat y en el funcional si existe |
| **Urgente** | El cliente o el equipo declaran crítico algo de producción | La ficha `impacto/URG-nn.md` y el flujo corto de `urgentes.md`, sin DF ni prototipo |

Di el modo al empezar.

## Flujos

El recorrido entero de cada caso, de F1 (aplicación nueva) a F9 (pase a producción), está en `assets/flujos/`: quién
hace cada paso, con qué skill y la referencia que lo detalla. `proyecto.py iniciar` los copia al proyecto.

## Proyecto nuevo

1. **Repositorio y fuentes.**
   ```bash
   python3 <skill>/scripts/proyecto.py iniciar <p> --nombre "…" --cliente "…"
   python3 <skill>/scripts/leer_fuentes.py <ficheros o carpetas> -o <p>/fuentes/
   ```
   Lee `ingesta-fuentes.md` y después **todas** las fuentes antes de escribir: las reuniones posteriores
   cambian lo anterior. Guarda una nota por fuente (`volumen-grande.md` §1), salvo las cortas (correo o chat);
   las marcadas explícitamente como duplicadas ya están cubiertas por la fuente indicada en el catálogo.
   Con muchas fuentes o más de 5 procesos, `volumen-grande.md`.
2. **Checkpoint.** En un solo mensaje, una o dos líneas por punto: modo y fuentes, problema, perfiles,
   procesos, reglas clave, contradicciones y lo que falta. Termina con «¿Es correcto o ajusto algo antes de
   escribir?». Con cualquier confirmación, sigue. Si el usuario no está, sigue con la lectura más razonable
   y deja las dudas como PC.
3. **Funcional.** Escribe `analisis/funcional.md` con `funcional-plantilla.md`, apartado a apartado,
   guardando al terminar cada uno. Las preguntas de condiciones de uso (§10) se hacen desde el principio.
4. **Diagramas.** Lee el `SKILL.md` de `appian-diagramas-bpmn`, describe cada proceso en su formato JSON en
   `analisis/diagramas/<proceso>.json`, con un carril por perfil y los mismos `ACT-nn`, y ejecuta su
   `diagrama.py crear`. Los de estados y de datos, en Mermaid con `mermaid-diagrams.md`; los pinta el `mermaid.py`
   de esa misma skill.
5. **Prototipo**, si se pide (suele ser con la primera versión del funcional, para validar las pantallas).
   Lo hace `appian-prototipos` a partir del funcional y pone las capturas en las fichas de pantalla. Sus preguntas
   nuevas (Q-nn) pasan a PC (`funcional-plantilla.md` §11).
6. **Técnico.** Escribe `analisis/tecnico.md` con `tecnico-plantilla.md` cuando el funcional esté estable
   (normalmente tras la primera validación) o cuando se pida. El Entorno (§0) y las Convenciones (§1) se
   rellenan antes, en cuanto se sepan.
7. **Comprobar.**
   ```bash
   python3 <skill>/scripts/indice.py derivadas <p> --escribir   # anexo «Quién puede hacer qué»
   python3 <skill>/scripts/comprobar.py <p> --fuentes <p>/fuentes/
   ```
   Sin errores antes de entregar. Revisa los avisos: los de redacción se corrigen casi siempre.
8. **DF en Word**, solo para enviarlo o si se pide (síntesis, evolutivo y refactorización), una vez y, si hay
   prototipo, después de él, con sus capturas. La primera entrega es la versión 1.0: con funcional y técnico en 1.0,
   `proyecto.py version <p> --inicial --fuente FU-01 --fuente FU-02 --que "Análisis inicial"` registra sus fuentes y
   su fila en `decisiones.md` sin abrir la 1.1 (incluye todas las fuentes procesadas). Nunca sobrescribe uno entregado. Mira algunas páginas del PDF antes de
   enviarlo; sin LibreOffice no lo hay ni se saca por otra vía: lo revisa quien lo envía; díselo al entregar.
   ```bash
   node <skill>/scripts/df_docx.js <p> --pdf    # entregables/DF-<proyecto>-v<versión>.docx; el PDF, en revision/
   ```
9. **Entregar.** Actualiza el siguiente paso de `proyecto.md` (las fuentes ya las registró `version --inicial`) y envía el Word y el `funcional.md`
   (SendUserFile en Claude). Cuando el Word sale hacia el cliente, `proyecto.py entregar <p>` apunta «DF entregado» y
   el fichero; nunca en una sesión desatendida. En pocas líneas: modo, historias, pantallas, pendientes de confirmar con el
   cliente y siguiente paso.

Para buscar en el análisis sin leerlo entero: `indice.py` (`resumen`, `buscar`, `ficha`, `impacto`,
`seccion`, `siguientes`). Para preparar la próxima reunión, `indice.py pendientes <p>`: lo que decide el equipo y
las preguntas abiertas por «A quién», de las que afectan a más partes del análisis a las que menos.

## Aplicación existente

En los modos evolutivo y de refactorización, los pasos de «Proyecto nuevo» con esto:
1. **Fuentes.** `as-is/` es una sola fuente y la propuesta, otra, antes que las reuniones:
   `leer_fuentes.py --una-fuente <p>/as-is <p>/refactorizacion/propuesta.md -o <p>/fuentes/`. De `as-is/` se leen
   `LEEME.md`, los documentos de lo que toca el cambio y `as-is/datos/`; nunca la extracción en bruto
   (`ingesta-fuentes.md`).
2. **Funcional.** De toda la aplicación y con detalle, por módulos (`volumen-grande.md` §4): criterios y escenarios del
   comportamiento real con su evidencia (✅ directa, 🔶 inferida; 🔒 solo lo de un DF validado), sin prioridad («—»). El
   técnico no repite `as-is/` (`cambios.md` §4). Lo nuevo y lo que cambia lo dice `indice.py cambios`, no un «Origen»
   escrito. Los hallazgos que corrige, las REF y los NV se citan dentro de su fuente
   («[FU-01 H-DAT-01]») y solo en la trazabilidad: el DF no los enseña.
3. **Lo sin verificar.** Un NV que condiciona lo que se construye es un PT con su cita; si lo resuelve negocio, también
   un PC, en palabras del cliente.
4. **Técnico.** Los nombres reales del inventario; §13 con la Situación de cada objeto (Nuevo, Modifica, Existe o
   Sustituye); con propuesta, una DT por cada REF de su Solución y la carga inicial y migración en §3
   (`tecnico-plantilla.md`).
5. **Comprobar.** `comprobar.py` lo contrasta con `as-is/datos/`: nombres, situaciones y citas.
6. **Parte mal hecha.** Si `comprobar.py` avisa de que algo que se modifica o se usa tiene un hallazgo Alta, dilo al
   usuario y propón pasar esa parte por refactorización (`appian-refactorizacion`) antes de construir encima. Si
   tiene algo sin verificar, que sea un PT o, si lo resuelve negocio, también un PC.

## Pantalla suelta

1. Si hay captura, mírala antes de escribir: textos, columnas, botones y valores que no se han dicho. Si
   contradice lo explicado, manda lo explicado y se anota.
2. Escribe la ficha PAN y sus historias con el formato del funcional. Un diálogo que se abre desde la
   pantalla es otra ficha.
3. Lo que falte (quién ve una acción, el texto de una confirmación) se pregunta antes de cerrar; los
   detalles menores, con la opción más razonable dicha en el texto.
4. Entrégala en el chat. Si el proyecto ya tiene análisis, la explicación es una fuente más (de chat,
   `ingesta-fuentes.md` §1): catalógala y sigue `actualizacion.md`.

## Comentarios del cliente al DF

El Word devuelto es una fuente más: se cataloga con `leer_fuentes.py`, que saca cada comentario y cada
cambio marcado con la historia o el apartado donde está, y se sigue `actualizacion.md`.

## Dudas de Appian

Lo que no sepas con certeza de Appian se consulta en el MCP de documentación `appian-docs` (sus herramientas llevan `appian-docs` en el nombre o su descripción habla de buscar en la documentación de Appian) antes de escribirlo, nunca de memoria: si existe un componente, una función, un parámetro o un objeto, qué admite, sus límites, si depende de la licencia y desde qué versión.
- Una duda por consulta, escrita como una frase completa.
- Vale lo que diga la documentación de la versión del entorno del proyecto (va en la URL: `/help/26.6/`). Si solo lo dice una versión posterior, se avisa de que puede no estar disponible.
- Lo que se escribe a partir de la respuesta lleva su URL, en la forma `/latest/`.
- Sin el MCP, se consulta docs.appian.com con WebFetch o WebSearch. Si tampoco se puede, se escribe «sin verificar» y la duda pasa a pendientes.
- Qué conviene hacer (qué mecanismo elegir, cómo diseñarlo) no es una duda de documentación: se consulta en `appian-best-practices`, solo la sección que toca. Esa skill está junto a esta: `python3 <esta skill>/../appian-best-practices/scripts/seccion.py 02 4.8` imprime solo §4.8 del doc 02.

**En el análisis**, las dudas típicas son si la versión o el tier del cliente permiten algo que pide el DF
y los límites que afectan a una decisión técnica. Su URL va en el «Por qué» o en el «Verificado» de la DT;
lo que quede sin verificar es un PT, o un PC si cambia lo que se promete al cliente.

## Referencias

| Fichero | Cuándo | Al incorporar una fuente, en vez de entero |
|---|---|---|
| `references/ingesta-fuentes.md` | Antes de leer las fuentes | Una reunión o un correo, nada: lo suyo está en `actualizacion.md` §2. Otro tipo de fuente, su fila de §2 y, si lo tiene, su apartado de §3 |
| `references/funcional-plantilla.md` | Al escribir el funcional | Solo el apartado de una pieza de un tipo que el análisis aún no tiene (las demás copian el formato de las que hay, `indice.py ficha`) y, al cambiar el estado de una pieza, tacharla o responderla, «Lo que leen los scripts»: estados, trazabilidad y tachado |
| `references/tecnico-plantilla.md` | Al escribir el técnico (con la ruta a buenas prácticas de cada apartado) | El apartado, igual; con una DT nueva, además «Buenas prácticas al diseñar» |
| `references/redaccion.md` | Al escribir cualquiera de los dos | Nada: `comprobar.py` avisa de lo que la incumple |
| `references/actualizacion.md` | Con cada fuente nueva | Entero |
| `references/volumen-grande.md` | Muchas fuentes o muchos procesos | Solo §1, si la fuente lleva nota |
| `references/cambios.md`, `references/urgentes.md` | Si `proyecto.py estado` lista unidades en curso (`analisis/cambios.md`), al abrir una, o si se declara una urgencia (un retoque no los necesita: «Camino corto» de `actualizacion.md`) | Entero, en esos casos |
| `references/mermaid-diagrams.md` | Diagramas de estados y de datos | Solo si cambia uno de esos diagramas |
