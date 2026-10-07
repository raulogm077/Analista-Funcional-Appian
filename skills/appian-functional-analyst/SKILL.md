---
name: appian-functional-analyst
description: Analista funcional de Appian. Convierte las fuentes de un proyecto (transcripciones de reuniones, correos, actas, notas, diagramas de flujo, un DF o ERS del cliente, o la descripción de una aplicación existente) en su análisis, el diseño funcional que valida el cliente (DF en Word con proceso, historias de usuario, pantallas y escenarios) y la especificación técnica para construir en Appian con buenas prácticas. Úsala para levantar requisitos, escribir o actualizar un análisis o un DF, incorporar una reunión, un correo o los comentarios del cliente al DF, redactar las historias de una pantalla que alguien explica o preparar la especificación técnica. No dibuja procesos (appian-diagramas-bpmn), no hace prototipos (appian-prototipos), no construye ni revisa objetos en un entorno (appian-best-practices) y no audita aplicaciones existentes (appian-reverse-engineering).
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
| — | Construir o revisar objetos en un entorno: `appian-best-practices` con el MCP de desarrollo |

## Requisitos

| Para | Necesita | Si falta |
|---|---|---|
| Scripts de análisis | Python 3.9+, sin paquetes | Imprescindible |
| PDF | `pdftotext` o `pip install pypdf` | Read lee el PDF |
| Correos `.msg` | Nada fiable | Pide el correo como `.eml` o PDF |
| Diagramas y su PNG | `pip install playwright` y un navegador (el de Playwright, Chrome o Edge) | Se entrega el `.drawio` o el `.mmd` sin imagen y se dice |
| DF en Word | Node.js con el paquete `docx` (`npm install docx` en la carpeta de trabajo o `npm install -g docx`) | Se entrega el `funcional.md` y se dice |

En Claude (web o escritorio) todo esto ya está.

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

```
<p>/proyecto.md      estado, fuentes procesadas, DF entregado, siguiente paso
<p>/fuentes/         FU-nn.md e indice.md (leer_fuentes.py)
<p>/notas/           una nota por fuente
<p>/impacto/         un informe por fuente nueva
<p>/as-is/           la aplicación existente (ingeniería inversa)
<p>/analisis/        funcional.md, tecnico.md, decisiones.md y diagramas/
<p>/prototipo/       el prototipo y sus capturas (skill de prototipos)
<p>/entregables/     el DF en Word
<p>/versiones/       copia del análisis antes de cada cambio
```

Formatos: `funcional-plantilla.md`, `tecnico-plantilla.md` y la cabecera de `decisiones.md` en
`assets/plantillas/`. `proyecto.py estado <p>` dice en qué punto está el proyecto: empieza siempre por ahí
si el proyecto ya existe.

## Modos

| Modo | Cuándo | Qué sale |
|---|---|---|
| **Síntesis** | Reuniones, correos, notas | Funcional y diagramas; el técnico cuando el funcional esté estable o se pida; DF en Word |
| **Fiel** | Hay un DF o una ERS del cliente | Funcional extraído sin reinterpretar (el ID del cliente va en la trazabilidad) y técnico; sin Word: el documento oficial es el del cliente |
| **Evolutivo** | Hay que cambiar una aplicación existente | Como síntesis, con `as-is/` como fuente; el técnico marca cada objeto Nuevo, Modifica o Existe |
| **Actualización** | Ya hay análisis y llega una reunión, un correo o los comentarios al DF | Informe de impacto y cambios puntuales: `actualizacion.md` |
| **Pantalla suelta** | Alguien explica una pantalla, con o sin captura | La ficha PAN y sus historias, en el chat y en el funcional si existe |

Di el modo al empezar.

## Proyecto nuevo

1. **Carpeta y fuentes.**
   ```bash
   python3 <skill>/scripts/proyecto.py iniciar <p> --nombre "…" --cliente "…"
   python3 <skill>/scripts/leer_fuentes.py <ficheros o carpetas> -o <p>/fuentes/
   ```
   Lee `ingesta-fuentes.md` y después **todas** las fuentes antes de escribir: las reuniones posteriores
   cambian lo anterior. Con muchas fuentes o más de 5 procesos, `volumen-grande.md`.
2. **Checkpoint.** En un solo mensaje, una o dos líneas por punto: modo y fuentes, problema, perfiles,
   procesos, reglas clave, contradicciones y lo que falta. Termina con «¿Es correcto o ajusto algo antes de
   escribir?». Con cualquier confirmación, sigue. Si el usuario no está, sigue con la lectura más razonable
   y deja las dudas como PC.
3. **Funcional.** Escribe `analisis/funcional.md` con `funcional-plantilla.md`, apartado a apartado,
   guardando al terminar cada uno. Las preguntas de condiciones de uso (§10) se hacen desde el principio.
4. **Diagramas.** Lee el `SKILL.md` de `appian-diagramas-bpmn`, describe cada proceso en su formato JSON en
   `analisis/diagramas/<proceso>.json`, con un carril por perfil y los mismos `ACT-nn`, y ejecuta su
   `diagrama.py crear`. Los estados, con `mermaid-diagrams.md`.
5. **Prototipo**, si se pide (suele ser con la primera versión del funcional, para validar las pantallas).
   Lo hace `appian-prototipos` a partir del funcional y pone las capturas en las fichas de pantalla.
6. **Técnico.** Escribe `analisis/tecnico.md` con `tecnico-plantilla.md` cuando el funcional esté estable
   (normalmente tras la primera validación) o cuando se pida. El Entorno (§0) y las Convenciones (§1) se
   rellenan antes, en cuanto se sepan.
7. **Comprobar.**
   ```bash
   python3 <skill>/scripts/indice.py derivadas <p> --escribir   # anexo «Quién puede hacer qué»
   python3 <skill>/scripts/comprobar.py <p> --fuentes <p>/fuentes/
   ```
   Sin errores antes de entregar. Revisa los avisos: los de redacción se corrigen casi siempre.
8. **DF en Word** (síntesis y evolutivo; si el análisis es solo para un prototipo, cuando se pida). La
   primera entrega es la versión 1.0: sube la versión del funcional y del técnico y añade su fila en
   `decisiones.md`.
   ```bash
   node <skill>/scripts/df_docx.js <p>          # entregables/DF-<proyecto>-v<versión>.docx
   ```
   Ábrelo (conviértelo a PDF y mira algunas páginas) antes de entregarlo.
9. **Entregar.** Actualiza `proyecto.md` (fuentes procesadas, DF entregado y siguiente paso) y envía el Word
   y el `funcional.md` (SendUserFile en Claude). En pocas líneas: modo, historias, pantallas, pendientes de
   confirmar con el cliente y siguiente paso.

Para buscar en el análisis sin leerlo entero: `indice.py` (`resumen`, `buscar`, `ficha`, `impacto`,
`seccion`, `siguientes`).

## Pantalla suelta

1. Si hay captura, mírala antes de escribir: textos, columnas, botones y valores que no se han dicho. Si
   contradice lo explicado, manda lo explicado y se anota.
2. Escribe la ficha PAN y sus historias con el formato del funcional. Un diálogo que se abre desde la
   pantalla es otra ficha.
3. Lo que falte (quién ve una acción, el texto de una confirmación) se pregunta antes de cerrar; los
   detalles menores, con la opción más razonable dicha en el texto.
4. Entrégala en el chat. Si el proyecto ya tiene análisis, la explicación es una fuente más: guárdala como
   `.txt`, catalógala y sigue `actualizacion.md`.

## Comentarios del cliente al DF

El Word devuelto es una fuente más: se cataloga con `leer_fuentes.py`, que saca cada comentario y cada
cambio marcado con la historia o el apartado donde está, y se sigue `actualizacion.md`.

## Dudas de Appian

Lo que no sepas con certeza de Appian se consulta en el MCP de documentación `appian-docs` (sus herramientas empiezan por `mcp__appian-docs__`) antes de escribirlo, nunca de memoria: si existe un componente, una función, un parámetro o un objeto, qué admite, sus límites, si depende de la licencia y desde qué versión.
- Una duda por consulta, escrita como una frase completa.
- Vale lo que diga la documentación de la versión del entorno del proyecto (va en la URL: `/help/26.6/`). Si solo lo dice una versión posterior, se avisa de que puede no estar disponible.
- Lo que se escribe a partir de la respuesta lleva su URL, en la forma `/latest/`.
- Sin el MCP, se consulta docs.appian.com con WebFetch o WebSearch. Si tampoco se puede, se escribe «sin verificar» y la duda pasa a pendientes.
- Qué conviene hacer (qué mecanismo elegir, cómo diseñarlo) no es una duda de documentación: se consulta en `appian-best-practices`, solo la sección que toca. Esa skill está junto a esta: `python3 <esta skill>/../appian-best-practices/scripts/seccion.py 02 4.8` imprime solo §4.8 del doc 02.

**En el análisis**, las dudas típicas son si la versión o el tier del cliente permiten algo que pide el DF
y los límites que afectan a una decisión técnica. Su URL va en el «Por qué» o en el «Verificado» de la DT;
lo que quede sin verificar es un PT, o un PC si cambia lo que se promete al cliente.

## Referencias

| Fichero | Cuándo |
|---|---|
| `references/ingesta-fuentes.md` | Antes de leer las fuentes |
| `references/funcional-plantilla.md` | Al escribir el funcional |
| `references/tecnico-plantilla.md` | Al escribir el técnico (con la ruta a buenas prácticas de cada apartado) |
| `references/redaccion.md` | Al escribir cualquiera de los dos |
| `references/actualizacion.md` | Con cada fuente nueva |
| `references/volumen-grande.md` | Muchas fuentes o muchos procesos |
| `references/mermaid-diagrams.md` | Diagramas de estados y de datos |
