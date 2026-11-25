---
name: appian-diagramas-bpmn
description: "Dibuja y mantiene los diagramas de proceso BPMN del proyecto (flujograma, diagrama de flujo, swimlanes) en draw.io (fichero .drawio editable, con carriles por perfil y, si el proceso tiene fases, una pestaña por fase) y su PNG para el documento, sin conexión. Úsala para crear o cambiar el diagrama de un proceso, dibujar el proceso de una aplicación existente, pasar un Visio (.vsdx) o un BPMN al formato del proyecto, compararlo con el diagrama aprobado, revisar qué se cambió a mano en draw.io (por ejemplo, en una reunión con el usuario), leer un .drawio o exportar un proceso a BPMN 2.0. La usan appian-functional-analyst (procesos del análisis) y appian-reverse-engineering (procesos de una aplicación existente, que los lee de la aplicación si no están extraídos). No decide qué contiene el proceso: si sale de reuniones o documentos, primero lo describe appian-functional-analyst, que hace también los diagramas de estados y de datos del funcional."
---

# Diagramas de proceso BPMN

Esta skill es dueña del dibujo de los procesos y de su formato. El contenido (qué pasos hay y quién los hace) lo decide quien la llama: el analista o ingeniería inversa.

`<p>` es la carpeta del proyecto y `<skill>`, la carpeta de esta skill.

## Cómo se trabaja

1. **¿De dónde sale el proceso?** Si quien llama ya lo describe, ve al paso 3. Si sale de reuniones, transcripciones, actas o un DF y el proyecto lleva análisis funcional, lo describe `appian-functional-analyst` y vuelve aquí para dibujarlo. Si el usuario solo quiere el dibujo, lee `references/fuentes.md` y descríbelo tú.
2. **Busca el diagrama aprobado** del mismo proceso (`.vsdx`, `.drawio`, `.bpmn`, un DF en Word) en la carpeta del proyecto y en la de la que cuelga. Si lo hay, compara antes su fecha con la de las fuentes y di qué caso aplica: si las fuentes son posteriores y lo rediseñan, mandan ellas y del aprobado salen los nombres; si no, es la referencia: `importar` un `.vsdx` o un `.bpmn` y usa las fuentes solo para lo que cambió (`references/fuentes.md`). Si las fuentes citan un DF que no está, pídelo antes de dibujar o, si no puedes esperar, entrega un «Borrador sin el DF».
3. **Escribe el JSON** del proceso («Formato del proceso») con las reglas de `references/buen-proceso.md`. Lo que no dice ninguna fuente va en `supuesto`. Si tiene fases que el cliente ve por separado, una pestaña por fase (`paginas`, en `references/formato.md`).
4. **`validar` y `crear`** («Órdenes»). Corrige los avisos de estructura antes de entregar.
5. **Mira el PNG.** Si algo queda apretado o cruzado, acorta una etiqueta o prueba la otra colocación (`--colocacion`).
6. **Responde** con las fuentes, los supuestos que listó `crear`, lo pendiente de validar y, por cada puerta, la salida que ninguna fuente explica. Si hay diagrama aprobado, `comparar --con` y da la tabla de diferencias.
7. **Después:** un cambio del análisis, con `actualizar` («Cambiar un proceso»); lo que se cambie en draw.io con el usuario, con `comparar` («Edición en una reunión»).

## Ficheros de cada proceso

Van juntos en la misma carpeta (`analisis/diagramas/` o la que indique quien llama). Sin `-o`, `crear` los deja junto al JSON de entrada. `X` es el nombre del fichero JSON que se pasa a `crear` (no el campo `proceso`): ponle al JSON el nombre que deba tener el diagrama.

| Fichero | Qué es |
|---|---|
| `X.drawio` | El diagrama. Se abre y se edita en draw.io |
| `X.png` | La imagen para el documento. La regenera la herramienta. Si el proceso va en tramos o en pestañas, una por tramo o por pestaña: `X-1.png`, `X-2.png`… |
| `X.json` | El proceso que conoce el análisis. La primera vez puede ser el propio JSON que se pasa a `crear`; después lo mantiene la herramienta y no se edita a mano: los cambios van con `actualizar` |
| `supuestos-X.md` | Solo si el proceso sale de fuentes y no de un diagrama aprobado. Lo escribe quien dibuja, sin herramienta: las fuentes con su fecha (y el DF que citan y no está, si lo hay), una tabla «paso, supuesto o tema abierto, origen», lo que no se dibuja, los nombres de sistema por confirmar y lo que queda fuera. Sirve para repasarlo con el usuario sin abrir el diagrama |
| `X.bpmn` | Solo si se exporta con `bpmn`, y uno con el proceso entero aunque vaya en tramos (en pestañas, uno por pestaña): conserva los tipos de inicio y de tarea, el flujo por defecto, los plazos y los errores, los participantes externos con sus mensajes, las notas, el lado de cada etiqueta y los datos de Appian |

## Qué escribe

En la carpeta que indique quien llama, dentro de `<p>`:
- `analisis/diagramas/*.{drawio,png,bpmn,svg}`: los procesos del análisis y la imagen de cada Mermaid
- `analisis/diagramas/*.json`: el proceso de cada diagrama, del analista; se reescribe al aceptar lo cambiado a mano
- `analisis/diagramas/supuestos-*.md`: las fuentes y los supuestos de un proceso sacado de fuentes, sin diagrama aprobado
- `as-is/08-procesos-bpmn/*.{drawio,png,bpmn}`: los procesos de una aplicación existente
- `as-is/08-procesos-bpmn/*.json`: el proceso de cada diagrama, de ingeniería inversa; igual que el del analista
- `as-is/diagrams/*.{png,svg}`: la imagen de cada Mermaid de ingeniería inversa (`mermaid.py`)

## Formato del proceso

Es un JSON con un paso y un flujo por línea:

```json
{
  "proceso": "Solicitud de autorización",
  "carriles": ["Unidad solicitante", "Técnico", "Aplicación"],
  "pasos": [
    {"id": "EV-01", "tipo": "inicio", "carril": "Unidad solicitante", "nombre": "Necesidad de autorización"},
    {"id": "ACT-01", "tipo": "tarea", "carril": "Unidad solicitante", "nombre": "Registrar solicitud"},
    {"id": "GW-01", "tipo": "exclusiva", "carril": "Técnico", "nombre": "¿Completa?"}
  ],
  "flujos": [
    {"de": "EV-01", "a": "ACT-01"},
    {"de": "GW-01", "a": "ACT-06", "etiqueta": "No"},
    {"de": "GW-01", "a": "ACT-02", "etiqueta": "Sí", "defecto": true},
    {"de": "ACT-04", "a": "EV-02", "discontinuo": true},
    {"de": "ACT-05", "a": "Registro mercantil", "etiqueta": "Consulta de la empresa"}
  ],
  "externos": ["Registro mercantil"],
  "notas": [{"paso": "ACT-05", "texto": "Si el registro no responde, se sigue sin el dato"}]
}
```

`externos`, `notas`, `supuesto` y `tramos` son opcionales, como los datos de Appian.

| Tipo | Qué representa | Código |
|---|---|---|
| `tarea` | Tarea de una persona en la aplicación | `ACT-nn` |
| `sistema` | Tarea automática (servicio, integración, escritura de datos) | `ACT-nn` |
| `script` | Tarea automática que solo calcula (expresión, regla) | `ACT-nn` |
| `manual` | Tarea fuera de la aplicación | `ACT-nn` |
| `subproceso` | Subproceso de este mismo proceso, con su propio diagrama | `ACT-nn` |
| `llamada` | Llamada a otro proceso que existe por sí solo (borde grueso) | `ACT-nn` |
| `exclusiva` | Puerta: se sigue un solo camino | `GW-nn` |
| `paralela` | Puerta: todos los caminos a la vez | `GW-nn` |
| `inclusiva` | Puerta: uno o varios caminos | `GW-nn` |
| `inicio` | Evento de inicio | `EV-nn` |
| `inicio_temporizador` | El proceso arranca a una hora o cada cierto tiempo | `EV-nn` |
| `inicio_mensaje` | El proceso arranca al recibir un aviso | `EV-nn` |
| `fin` | Evento de fin | `EV-nn` |
| `temporizador` | Espera o plazo | `EV-nn` |
| `mensaje` | Aviso o correo que envía el proceso (ver «Avisos») | `EV-nn` |
| `intermedio` | Otro evento intermedio | `EV-nn` |
| `error` | Error que interrumpe la tarea en la que salta | `EV-nn` |

**Códigos.** Son estables: no se renumeran ni se reutilizan. El `ACT-nn` de cada tarea es el mismo que el de su paso en el documento. En el dibujo solo se ve el nombre.

**Carriles.** Son los perfiles, de arriba abajo en el orden de la lista. Lo automático va en un carril «Aplicación» y un organismo externo que hace tareas del proceso es un carril más.

**Participantes externos.** Un sistema u organismo con el que solo se intercambian mensajes (un ERP, un registro público), sin pasos propios en el proceso, va en `externos`: se dibuja como una franja debajo de los carriles. Un flujo entre un paso y un externo es un flujo de mensaje (línea discontinua con círculo y flecha hueca), en cualquiera de los dos sentidos.

**Flujo por defecto.** `"defecto": true` marca la salida que se toma cuando no se cumple ninguna otra (una barra en el origen). Solo en puertas exclusivas o inclusivas, y una por paso. Se admite en una tarea con varias salidas por los diagramas de antes, pero una tarea con varios resultados va seguida de una puerta (ver «Cómo se describe un buen proceso»).

**Notas.** Cada nota de `notas` va unida a su paso con una línea de puntos y sale en el PNG: úsalas para señalar algo que quien lee el diagrama no debe pasar por alto (un riesgo, una duda pendiente).

**Supuestos.** `"supuesto": "texto"` en un paso marca lo que ninguna fuente dice (quién lo hace, el orden de dos pasos), con lo que se supone. Sale con el borde ámbar (discontinuo en una tarea), `crear` y `actualizar` lo listan para confirmarlo con el usuario, y en el BPMN va en `documentation`. Confirmado, se quita con `{"poner": {"id": "ACT-03", "supuesto": ""}}`.

**Más:** los tramos (`"tramos": true`, solo si se piden), `posicion`, los datos de Appian (`nodo`, `temporizador`, `proceso_llamado`, `condicion`), las pestañas por fase (`paginas`) y el aspecto del dibujo están en `references/formato.md`.

## Órdenes

`<skill>` es la carpeta de esta skill.

```bash
python3 <skill>/scripts/diagrama.py validar proceso.json                     # comprueba el JSON
python3 <skill>/scripts/diagrama.py crear proceso.json -o analisis/diagramas/ # .drawio + .png + .json
python3 <skill>/scripts/diagrama.py actualizar X.drawio cambios.json          # cambios del análisis (temporal, fuera de <p>)
python3 <skill>/scripts/diagrama.py comparar X.drawio [--aceptar] [--json]   # qué se cambió a mano
python3 <skill>/scripts/diagrama.py leer X.drawio [--posiciones]             # el proceso en JSON
python3 <skill>/scripts/diagrama.py png X.drawio                             # regenera el PNG
python3 <skill>/scripts/diagrama.py bpmn X.drawio [-o X.bpmn]                # BPMN 2.0 para otra herramienta
python3 <skill>/scripts/diagrama.py importar X.vsdx [-o X.json]              # un Visio o un .bpmn, al JSON
python3 <skill>/scripts/diagrama.py comparar X.drawio --con aprobado.vsdx    # qué cambia respecto al aprobado
```

`crear` y `actualizar` colocan con Mermaid y por capas y se quedan con la que deja menos cruces; `--colocacion mermaid|capas` fuerza una (ver `references/colocacion.md`).

Códigos de salida:
- **0:** todo ha ido bien.
- **1:** hay un error: el proceso no es válido, falta un fichero o el `.drawio` ya existe. Se corrige y se repite.
- **3:** hay cambios hechos a mano en draw.io que el análisis no recoge. `comparar` los lista y sale con 3; `actualizar` se niega con 3 hasta que se acepten (`comparar --aceptar`) o, si van en tramos colocados a mano, hasta que se use `--recolocar`.
- **2:** falta Playwright o un navegador. Solo falta la imagen: `crear`, `actualizar` y `comparar --aceptar` escriben el `.drawio` y el `.json` igual, con la colocación por capas, y avisan «sin PNG»; si había PNG, lo quitan, porque ya no es del dibujo. `png` la genera cuando haya navegador. `leer`, `comparar`, `bpmn` y `validar` no lo necesitan.

`validar`, `crear` y `actualizar` avisan si el proceso está incompleto:
- falta un inicio o un fin;
- un paso no tiene entrada o salida, o sale un flujo de un fin;
- una decisión tiene salidas sin etiqueta (salvo la de por defecto) o más de un flujo por defecto;
- un código no corresponde a su tipo;
- un `error` con salidas no está unido a su tarea con un flujo discontinuo, un dato de Appian está en un paso de otro tipo o `interrumpe` no va en un temporizador unido a su tarea;
- un participante externo no tiene flujos de mensaje;
- una tarea tiene varias salidas sin puerta (en BPMN se siguen todas a la vez), una puerta une y divide a la vez o una exclusiva que divide no lleva pregunta;
- los caminos que abre una paralela o una inclusiva se juntan en algo que no es una puerta del mismo tipo, o los de una exclusiva, en una paralela (que esperaría a todos y pararía el proceso);
- dos tareas se llaman igual.

`crear`, `actualizar` y `png` avisan si el diagrama mide más de 1.600 px de ancho: en una página vertical el texto quedará pequeño. El PNG conserva el doble de resolución del dibujo, también en procesos grandes, para ampliar sin reducir antes su detalle.

**Qué se niega a hacer:**
- `crear` no sobrescribe un `.drawio` que ya existe; para cambiarlo, `actualizar`.
- `crear --forzar` y `actualizar --forzar` descartan lo que se haya hecho a mano en draw.io. Pregunta antes de usarlos.

## Cambiar un proceso

Pasa solo los cambios, que gasta muchos menos tokens que repetir el proceso entero. El fichero de cambios es temporal: va fuera de `<p>` (en la carpeta temporal del sistema o la de la sesión) y no se guarda; lo que queda del cambio es `X.json`.

```json
{"cambios": [
  {"carril": "Registro"},
  {"poner": {"id": "ACT-10", "tipo": "manual", "carril": "Registro", "nombre": "Archivar en papel"}},
  {"poner": {"id": "ACT-05", "nombre": "Resolver la solicitud"}},
  {"quitar": "EV-04"},
  {"flujo": {"de": "ACT-04", "a": "ACT-10", "etiqueta": "Sí"}},
  {"quitar_flujo": {"de": "ACT-04", "a": "GW-03"}},
  {"renombrar_carril": ["Técnico", "Técnico de la unidad gestora"]},
  {"proceso": "Solicitud de autorización"},
  {"externo": "Registro mercantil"},
  {"flujo": {"de": "ACT-05", "a": "Registro mercantil", "etiqueta": "Consulta"}},
  {"flujo": {"de": "GW-01", "a": "ACT-02", "defecto": true}},
  {"nota": {"paso": "ACT-05", "texto": "Si el registro no responde, se sigue sin el dato"}},
  {"quitar_nota": {"paso": "ACT-03", "texto": "Texto exacto de la nota"}},
  {"quitar_externo": "Notaría"}
]}
```

- **`poner`** añade un paso o cambia los campos que traiga uno existente. Un paso nuevo necesita `id`, `tipo`, `carril` y, si es una tarea, `nombre`. Un dato de Appian vacío (`"nodo": ""`) lo quita, también en `flujo`.
- **`quitar`** borra el paso y sus flujos.
- **`flujo`** añade el flujo o cambia su etiqueta, su `condicion`, si es discontinuo o si es el de por defecto (`"defecto": false` lo quita). **`quitar_flujo`** lo borra.
- **`externo`** añade un participante externo y **`quitar_externo`** lo quita con sus flujos de mensaje.
- **`nota`** une una nota a un paso y **`quitar_nota`** la quita (con su texto exacto). Quitar un paso quita sus notas.
- **`carril`** añade un carril al final. Tiene que ir antes, en la misma lista, que el `poner` que lo use: `poner` no crea carriles, para que una errata no invente uno. Un carril que se queda sin pasos desaparece.
- **`renombrar_carril`** cambia el nombre y conserva sus pasos. **`proceso`** cambia el nombre del proceso.
- En vez de la lista de cambios también se puede pasar el proceso completo, con `pasos` y `flujos`.

Si algo falla, el `.drawio` no se toca.

Cómo se coloca lo que cambia:
- **Si nadie ha movido nada en draw.io** desde la última vez, el diagrama se vuelve a colocar entero, sin que nada se pise (el detalle, en `references/colocacion.md`). **Mira siempre el PNG antes de entregar**: si algo queda apretado, acorta la etiqueta.
- **Si alguien lo ha colocado a mano**, se respeta. Lo nuevo va a la derecha de su paso anterior y lo que sigue se desplaza para hacer sitio; un participante nuevo va debajo de todo y una nota nueva encima de su paso.
- **Si está en tramos y alguien los ha colocado a mano**, `actualizar` se niega: el cambio se hace en draw.io (y después `comparar --aceptar`) o con `--recolocar`.
- `--recolocar` coloca todo de nuevo aunque se haya colocado a mano. Pregunta antes de usarlo.

## Edición en una reunión

1. **Se abre `X.drawio` en draw.io** (Desktop, app.diagrams.net o la integración de SharePoint/OneDrive), se recorre con el usuario (el camino normal, cada puerta con sus preguntas y cada fin) y se cambia con él:
   - mover, renombrar y arrastrar pasos de un carril a otro;
   - unir con flechas;
   - añadir formas de la biblioteca BPMN (Más formas → BPMN General) o formas básicas: un rectángulo es una tarea, un rombo una decisión y un círculo un inicio o un fin.
2. **Se guarda y se cierra el fichero en draw.io.** `comparar` reescribe el `.drawio` para dar código a lo nuevo, y si sigue abierto, draw.io podría pisarlo al guardar.
3. **Se ejecuta `comparar`:**
   ```bash
   python3 <skill>/scripts/diagrama.py comparar X.drawio
   ```
   - Da un código (`ACT-`, `GW-`, `EV-`) a lo añadido a mano.
   - Da su forma a los rectángulos, rombos y círculos (a un rectángulo, la tarjeta de tarea con su pictograma).
   - Lista qué ha cambiado respecto a `X.json` y las notas de texto sueltas del dibujo. Una nota unida a un paso con una línea pasa a ser una nota del proceso.
4. **Quien llama actualiza su análisis** con esa lista (el paso a paso y las historias afectadas) y después acepta:
   ```bash
   python3 <skill>/scripts/diagrama.py comparar X.drawio --aceptar
   ```

Mientras haya cambios hechos a mano sin aceptar, `actualizar` se niega a tocar el fichero. Así no se pierde nada de lo hecho en la reunión.

**Un `.drawio` sin `X.json`** (hecho a mano o recibido del cliente) se adopta igual: `comparar X.drawio --aceptar` da los códigos y crea `X.json`.

## Leer un diagrama

No leas el XML del `.drawio`, que es largo y caro. Usa `leer`, que devuelve el proceso en el formato de arriba.

## Requisitos y privacidad

El plugin ya comprueba los requisitos al empezar la sesión, una vez por versión. Solo si una orden sale con 2, ejecuta `python3 <skill>/../../requisitos.py --skill appian-diagramas-bpmn`, que dice qué falta, qué se pierde y cómo se instala; díselo al usuario una vez y sigue. Sin `requisitos.py` (copia suelta), sigue sin comprobar.

Para la imagen hacen falta Playwright y un navegador. Con navegador, los pasos se colocan con el motor de carriles de Mermaid o por capas, la que quede mejor (los tramos, siempre por capas). Sin él se hace todo menos la imagen: los pasos se colocan por capas, de izquierda a derecha, con un carril por perfil y sin que nada se pise. `DIAGRAMAS_SIN_NAVEGADOR=1` simula que no hay navegador.

El diagrama no sale del equipo. El motor de colocación (Mermaid, licencia MIT), el visor de draw.io (licencia Apache 2.0) y los pictogramas de las tareas (Lucide, licencia ISC) van en `assets/`. Solo se escribe junto al `.drawio`: ni temporales ni `__pycache__` fuera de ahí.

## Diagramas Mermaid

Los diagramas que no son procesos (estados, datos, arquitectura) van en Mermaid. Qué llevan lo decide quien llama; esta skill los valida y los pinta sin conexión:

```bash
python3 <skill>/scripts/mermaid.py <carpeta>/*.mmd [-o carpeta] [--svg]   # PNG (y SVG) de cada diagrama
python3 <skill>/scripts/mermaid.py <carpeta>/*.mmd --check                # solo valida
python3 <skill>/scripts/mermaid.py --md documento.md [otro.md …]          # valida los bloques mermaid de un Markdown
```

- Sale con 1 si un diagrama tiene un error de sintaxis (con `--md`, dice en qué línea del documento empieza el bloque) o la orden está mal (sin ningún `.mmd` ni `--md`), y con 2 si falta Playwright o un navegador.
- Avisa de los que miden más de 1.600 px de ancho: se ponen de arriba abajo o se parten.
- Solo escribe en la carpeta de salida (`-o`, o la de cada `.mmd`) y no deja temporales.
- El SVG lleva las etiquetas como HTML: se ve bien en un navegador (una web, un dashboard), no en Word ni en un PDF. Ahí va el PNG.

## Más detalle

- `references/fuentes.md`: sacar el proceso de reuniones, transcripciones y un DF; partir del aprobado; importar un Visio o un BPMN; comparar con el aprobado.
- `references/buen-proceso.md`: cómo se nombran las tareas, las puertas, los inicios y fines, los avisos, los perfiles y los carriles por sistema.
- `references/formato.md`: tramos, posiciones, datos de Appian, pestañas por fase y el aspecto del dibujo.
- `references/colocacion.md`: cómo se coloca, cómo elige entre Mermaid y por capas, y los límites (varias páginas, pools, mensajes, eventos de borde).
