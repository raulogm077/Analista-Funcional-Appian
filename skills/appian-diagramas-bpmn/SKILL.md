---
name: appian-diagramas-bpmn
description: Dibuja y mantiene los diagramas de proceso BPMN del proyecto en draw.io (fichero .drawio editable, con carriles por perfil) y su PNG para el documento, sin conexión. Úsala para crear o cambiar el diagrama de un proceso, revisar qué se cambió a mano en draw.io (por ejemplo, en una reunión con el usuario), leer un .drawio o exportar un proceso a BPMN 2.0. La usan appian-functional-analyst (procesos del análisis) y appian-reverse-engineering (procesos de una aplicación existente). No decide qué contiene el proceso: si sale de reuniones o documentos, primero lo describe appian-functional-analyst.
---

# Diagramas de proceso BPMN

Esta skill es dueña del dibujo de los procesos y de su formato. El contenido (qué pasos hay y quién los hace) lo decide quien la llama: el analista o ingeniería inversa.

## Ficheros de cada proceso

Van juntos en la misma carpeta (`analisis/diagramas/` o la que indique quien llama). Sin `-o`, `crear` los deja junto al JSON de entrada.

| Fichero | Qué es |
|---|---|
| `X.drawio` | El diagrama. Se abre y se edita en draw.io |
| `X.png` | La imagen para el documento. La regenera la herramienta |
| `X.json` | El proceso que conoce el análisis. La primera vez puede ser el propio JSON que se pasa a `crear`; después lo mantiene la herramienta y no se edita a mano: los cambios van con `actualizar` |
| `X.bpmn` | Solo si se exporta con `bpmn`: conserva los tipos de inicio y de tarea, el flujo por defecto, los plazos, los participantes externos con sus mensajes, las notas y el lado de cada etiqueta |

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

`externos` y `notas` son opcionales.

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
| `mensaje` | Aviso que se envía | `EV-nn` |
| `intermedio` | Otro evento intermedio | `EV-nn` |

**Códigos.** Son estables: no se renumeran ni se reutilizan. El `ACT-nn` de cada tarea es el mismo que el de su paso en el documento. En el dibujo solo se ve el nombre.

**Carriles.** Son los perfiles, de arriba abajo en el orden de la lista. Lo automático va en un carril «Aplicación» y un organismo externo que hace tareas del proceso es un carril más.

**Participantes externos.** Un sistema u organismo con el que solo se intercambian mensajes (un ERP, un registro público), sin pasos propios en el proceso, va en `externos`: se dibuja como una franja debajo de los carriles. Un flujo entre un paso y un externo es un flujo de mensaje (línea discontinua con círculo y flecha hueca), en cualquiera de los dos sentidos.

**Flujo por defecto.** `"defecto": true` marca la salida que se toma cuando no se cumple ninguna otra (una barra en el origen). Solo en puertas exclusivas o inclusivas, o en tareas con varias salidas, y una por paso.

**Notas.** Cada nota de `notas` va unida a su paso con una línea de puntos y sale en el PNG: úsalas para señalar algo que quien lee el diagrama no debe pasar por alto (un riesgo, una duda pendiente).

**Posición.** `"posicion": [x, y]` en un paso es opcional. Solo la usa ingeniería inversa, cuando lee de Appian dónde está cada nodo, y tiene que venir en todos los pasos para que se use.

## Órdenes

`<skill>` es la carpeta de esta skill.

```bash
python3 <skill>/scripts/diagrama.py validar proceso.json                     # comprueba el JSON
python3 <skill>/scripts/diagrama.py crear proceso.json -o analisis/diagramas/ # .drawio + .png + .json
python3 <skill>/scripts/diagrama.py actualizar X.drawio cambios.json          # cambios del análisis
python3 <skill>/scripts/diagrama.py comparar X.drawio [--aceptar] [--json]   # qué se cambió a mano
python3 <skill>/scripts/diagrama.py leer X.drawio [--posiciones]             # el proceso en JSON
python3 <skill>/scripts/diagrama.py png X.drawio                             # regenera el PNG
python3 <skill>/scripts/diagrama.py bpmn X.drawio [-o X.bpmn]                # BPMN 2.0 para otra herramienta
```

Códigos de salida:
- **0:** todo ha ido bien.
- **1:** hay un error o hay cambios pendientes de revisar.
- **2:** falta Playwright o un navegador.

`validar`, `crear` y `actualizar` avisan si el proceso está incompleto:
- falta un inicio o un fin;
- un paso no tiene entrada o salida, o sale un flujo de un fin;
- una decisión tiene salidas sin etiqueta (salvo la de por defecto) o más de un flujo por defecto;
- un código no corresponde a su tipo;
- un participante externo no tiene flujos de mensaje;
- hay más de 20 tareas.

`crear`, `actualizar` y `png` avisan si el diagrama mide más de 1.600 px de ancho: en una página vertical el texto quedará pequeño. El PNG se limita a unos 3.200 px de ancho.

**Qué se niega a hacer:**
- `crear` no sobrescribe un `.drawio` que ya existe; para cambiarlo, `actualizar`.
- `crear --forzar` y `actualizar --forzar` descartan lo que se haya hecho a mano en draw.io. Pregunta antes de usarlos.

## Cambiar un proceso

Pasa solo los cambios, que gasta muchos menos tokens que repetir el proceso entero:

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

- **`poner`** añade un paso o cambia los campos que traiga uno existente. Un paso nuevo necesita `id`, `tipo`, `carril` y, si es una tarea, `nombre`.
- **`quitar`** borra el paso y sus flujos.
- **`flujo`** añade el flujo o cambia su etiqueta, si es discontinuo o si es el de por defecto (`"defecto": false` lo quita). **`quitar_flujo`** lo borra.
- **`externo`** añade un participante externo y **`quitar_externo`** lo quita con sus flujos de mensaje.
- **`nota`** une una nota a un paso y **`quitar_nota`** la quita (con su texto exacto). Quitar un paso quita sus notas.
- **`carril`** añade un carril al final. Tiene que ir antes, en la misma lista, que el `poner` que lo use: `poner` no crea carriles, para que una errata no invente uno. Un carril que se queda sin pasos desaparece.
- **`renombrar_carril`** cambia el nombre y conserva sus pasos. **`proceso`** cambia el nombre del proceso.
- En vez de la lista de cambios también se puede pasar el proceso completo, con `pasos` y `flujos`.

Si algo falla, el `.drawio` no se toca.

Cómo se coloca lo que cambia:
- **Si nadie ha movido nada en draw.io** desde la última vez, el diagrama se vuelve a colocar entero y queda limpio: ninguna forma, etiqueta o nota pisa a otra, y la etiqueta de un evento o una puerta va al lado por el que no llega ningún flujo.
- **Si alguien lo ha colocado a mano**, se respeta. Lo nuevo va a la derecha de su paso anterior y lo que sigue se desplaza para hacer sitio; un participante nuevo va debajo de todo y una nota nueva encima de su paso.
- `--recolocar` coloca todo de nuevo aunque se haya colocado a mano. Pregunta antes de usarlo.

## Edición en una reunión

1. **Se abre `X.drawio` en draw.io** (Desktop, app.diagrams.net o la integración de SharePoint/OneDrive) y se cambia con el usuario:
   - mover, renombrar y arrastrar pasos de un carril a otro;
   - unir con flechas;
   - añadir formas de la biblioteca BPMN (Más formas → BPMN General) o formas básicas: un rectángulo es una tarea, un rombo una decisión y un círculo un inicio o un fin.
2. **Se guarda y se cierra el fichero en draw.io.** `comparar` reescribe el `.drawio` para dar código a lo nuevo, y si sigue abierto, draw.io podría pisarlo al guardar.
3. **Se ejecuta `comparar`:**
   ```bash
   python3 <skill>/scripts/diagrama.py comparar X.drawio
   ```
   - Da un código (`ACT-`, `GW-`, `EV-`) a lo añadido a mano.
   - Da forma BPMN a los rectángulos, rombos y círculos.
   - Lista qué ha cambiado respecto a `X.json` y las notas de texto sueltas del dibujo. Una nota unida a un paso con una línea pasa a ser una nota del proceso.
4. **Quien llama actualiza su análisis** con esa lista (el paso a paso y las historias afectadas) y después acepta:
   ```bash
   python3 <skill>/scripts/diagrama.py comparar X.drawio --aceptar
   ```

Mientras haya cambios hechos a mano sin aceptar, `actualizar` se niega a tocar el fichero. Así no se pierde nada de lo hecho en la reunión.

**Un `.drawio` sin `X.json`** (hecho a mano o recibido del cliente) se adopta igual: `comparar X.drawio --aceptar` da los códigos y crea `X.json`.

## Cómo se describe un buen proceso

- **Tareas:** verbo en infinitivo y objeto, por ejemplo «Revisar documentación».
- **Puertas exclusivas:** una pregunta cerrada («¿Completa?») y cada salida con su etiqueta.
- **Inicio y fin:** un inicio por proceso y un fin por cada resultado de negocio («Solicitud denegada», «Autorización emitida»).
- **Arranque:** `inicio_temporizador` si el proceso arranca solo a una hora o cada cierto tiempo (el nombre dice cuándo: «Cada día a las 08:00»); `inicio_mensaje` si arranca al recibir un aviso.
- **Plazos:** un `temporizador` unido a la tarea que vigila con un flujo discontinuo. Al exportar a BPMN pasa a ser un evento de borde de esa tarea.
- **Avisos:** un `mensaje` en el carril «Aplicación». Si el aviso va a un sistema u organismo externo, un flujo de mensaje desde el paso que lo envía hasta el participante externo. Si después del aviso no pasa nada más, la rama acaba en un `fin`.
- **Tamaño:** con más de 20 tareas, se parte en subprocesos. El proceso principal usa `subproceso` y cada subproceso tiene su diagrama.
- **Notas:** las explicaciones van en el paso a paso del documento; en `notas`, solo lo que hay que ver en el propio diagrama. Una nota suelta que se deje en draw.io también sale en el PNG: bórrala si no debe verla el cliente.

## Leer un diagrama

No leas el XML del `.drawio`, que es largo y caro. Usa `leer`, que devuelve el proceso en el formato de arriba.

## Requisitos y privacidad

Hace falta Python 3 con Playwright (`pip install playwright`) y un navegador: el Chromium de Playwright, o Chrome o Edge ya instalados.

El diagrama no sale del equipo. El motor de colocación (Mermaid, licencia MIT) y el visor de draw.io (licencia Apache 2.0) van en `assets/`.

## Diagramas Mermaid

Los diagramas que no son procesos (estados, datos, arquitectura) van en Mermaid. Qué llevan lo decide quien llama; esta skill los valida y los pinta sin conexión:

```bash
python3 <skill>/scripts/mermaid.py <carpeta>/*.mmd [-o carpeta] [--svg]   # PNG (y SVG) de cada diagrama
python3 <skill>/scripts/mermaid.py <carpeta>/*.mmd --check                # solo valida
python3 <skill>/scripts/mermaid.py --md documento.md [otro.md …]          # valida los bloques mermaid de un Markdown
```

- Sale con 1 si un diagrama tiene un error de sintaxis (con `--md`, dice en qué línea del documento empieza el bloque) y con 2 si falta Playwright o un navegador.
- Avisa de los que miden más de 1.600 px de ancho: se ponen de arriba abajo o se parten.
- Solo escribe en la carpeta de salida (`-o`, o la de cada `.mmd`) y no deja temporales.

## Límites

- **Varias páginas:** solo se lee y se cambia la primera página del `.drawio`; las demás se conservan.
- **Pools:** si los carriles están dentro de un pool, el nombre del pool es el del proceso. Un participante externo es una franja marcada por la herramienta: si en draw.io se dibuja un pool nuevo a mano, se lee como un carril; para un participante nuevo, usa `externo`.
- **Flujos de mensaje:** van en vertical entre el paso y su participante y pueden cruzar los carriles que hay entre los dos.
- **Eventos de borde:** en draw.io, un plazo sale como un evento unido a su tarea con línea discontinua. Se puede pegar a la tarea a mano.
- **Flujos nuevos en un diagrama colocado a mano:** los traza draw.io y pueden cruzar alguna forma. Se retocan en draw.io o se usa `--recolocar`.
- **Tamaño en un documento vertical:** a partir de unas 12 tareas en fila (más de 1.600 px), el texto queda pequeño en una página vertical. Usa una página apaisada o parte el proceso.
