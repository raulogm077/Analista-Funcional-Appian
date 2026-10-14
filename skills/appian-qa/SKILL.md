---
name: appian-qa
description: "QA de una unidad de cambio Appian ya construida, con SAIL CLI: en otra sesión distinta de la de construir y solo con los escenarios en Gherkin de la unidad (sus .feature), recorre cada escenario como lo haría cada rol, con su cuenta, y comprueba el «entonces» en lo que devuelve Appian. Cada recorrido queda como guion en qa/ del proyecto, y un script lo repite sin IA antes de cada paquete; un escenario que falla devuelve su issue a pendiente. Úsala cuando una unidad tenga todas sus issues hechas y toque probarla como usuario, para repetir los guiones de QA antes de preparar un paquete o para rehacer el guion de una pantalla que cambió a propósito. No construye ni corrige objetos (appian-best-practices), no escribe criterios ni escenarios (appian-functional-analyst), no verifica los objetos contra el técnico (appian-reverse-engineering) y no mira la maquetación ni los estilos: eso lo mira una persona."
---

# QA · Appian

Prueba una unidad construida como la usaría cada rol, con SAIL CLI, y deja cada recorrido como un guion que un script
repite sin IA. Prueba lo que se pidió, los escenarios, no lo que entendió quien construyó: no carga la skill oficial de
Appian ni lee el funcional, las issues ni el técnico, salvo el site y las cuentas de su §0 («Entradas»).

`<skill>` es la carpeta de este fichero; `<p>`, la del proyecto, y `<U>`, la unidad (`EV-nn`). En Windows, `python` en
vez de `python3`.

## Qué hace y qué no

| Esta skill | Lo hace otra |
|---|---|
| Recorre los escenarios de la unidad con la cuenta de cada rol y comprueba su «entonces» | Escribir los criterios y sus escenarios: `appian-functional-analyst` |
| Deja cada recorrido como guion en `qa/<U>/` y lo repite sin IA | Los casos de prueba de reglas e interfaces: quien construye, con `appian-best-practices` |
| Dice qué escenario falla y qué issue vuelve a pendiente | Corregirlo en el entorno: `appian-best-practices` |
| — | Comprobar que los objetos son los del técnico: «verificar», de `appian-reverse-engineering` |

SAIL CLI no ve colores, maquetación ni accesibilidad (no trae el color de una etiqueta): por defecto lo mira una persona
en el navegador, con la captura de la pantalla; Playwright, solo para un criterio cuyo «Con qué» de técnico §14 lo pida,
y sin guion: `qa.py` no lo repite.

## Requisitos

Antes de la primera tarea: `python3 <skill>/../../requisitos.py --skill appian-qa`. Dice qué falta en el equipo, qué se
pierde y cómo se instala. Sin SAIL CLI no hay QA: viene en el paquete del Dev MCP (`bin/`) y `bin/setup-*` lo deja en el
PATH como `sail`. Sin `requisitos.py` (copia suelta), sigue sin comprobar.

## Cuándo, y cuándo no

- **Con la unidad completa**: todas sus issues hechas. Por unidad, no por issue: un escenario cruza pantallas de varias.
- **En otra sesión**: una nueva, o un subagente que solo recibe los `.feature`, el site y la cuenta de cada rol, nunca el
  contexto de quien construyó; también otro agente (el flujo F8 está en `.agents/workflows/` de cada proyecto) o una
  persona. Basta un modelo pequeño (medido: Sonnet encontró lo mismo que Opus por un tercio del coste).
- **Solo en desarrollo**, porque crea datos y lanza procesos; en una urgencia, en el entorno de corrección. `qa.py
  repetir` solo repite contra la «URL de desarrollo» o la «URL del entorno de corrección» de técnico §0: si un guion
  apunta a otro host, o §0 no las dice, no repite nada.
- **En un retoque cosmético no hay QA.** Si cambia un texto que usa un guion, la repetición falla en ese paso y se
  cambia ese texto en el guion; nada más.

## Entradas

- **Los escenarios**: `construccion/<U>/ISS-nn.feature`. Nada más del proyecto, salvo técnico §0 (abajo).
- **El entorno y el site**: el host de desarrollo y el nombre del site en su URL (`/suite/sites/<site>`).
- **Una cuenta local de Appian por rol** de los escenarios, en desarrollo. Si hace falta comprobar que alguien *no* ve
  algo de otro, dos cuentas del mismo rol.

Si no te los dan, están en técnico §0 («URL de desarrollo», «Site» y «Cuentas de prueba en desarrollo»: `indice.py
seccion <p> T0` de `appian-functional-analyst`); si tampoco, pídelos en un solo mensaje. La contraseña nunca va a un
fichero del proyecto ni a la conversación: la persona entra con cada cuenta (abajo) o te pasa la sesión ya abierta.

## Flujo

Cada orden de SAIL CLI y de `qa.py` se espera en primer plano hasta que termina, sin vigilancias en segundo plano
(`tail -f`, un Monitor): una que queda abierta deja la sesión colgada al terminar.

1. **Sesiones.** `python3 <skill>/scripts/qa.py sesiones <host> <usuario> …` dice la carpeta de sesión de SAIL CLI de
   cada cuenta en este equipo, o la orden para entrar: `sail login <host> --data-dir <carpeta>` con `SAIL_USERNAME` y
   `SAIL_PASSWORD` en el entorno solo para esa orden. Una carpeta por cuenta; no leas sus ficheros (llevan las
   cookies). Con SSO, `--from-devmcp` importa la sesión del Dev MCP, pero es la de una persona, no la de un rol.
2. **Por escenario**, en el orden de los `.feature`:
   - **Dado**: prepáralo como lo haría un usuario, desde el site y con la cuenta del rol que lo haría (nunca por el Dev
     MCP ni con SQL). Lo que teclees lleva `{pasada}` (abajo), para que no se confunda con lo de otra vez.
   - **Cuando**: recórrelo con la cuenta de su rol, `sail --data-dir <su carpeta> load|navigate|interact <site> …`.
     Para explorar, la salida normal, que es más corta; para comprobar, `--json`.
   - **Entonces**: compruébalo en el `--json`. Tras enviar un formulario, el `--json` trae `completed` y la página de
     antes (`viewIsStale`): el «entonces» se mira tras un `load`.
   - **Escribe el guion** en `qa/<U>/<escenario>.json` («El guion»), pase o no. Si falla en el «cuando», el guion llega
     hasta el paso que falla; corregido el fallo, ese guion queda «por terminar» hasta que lo completes.
   - **Repítelo sin IA**: `python3 <skill>/scripts/qa.py repetir <p> <U> --escenario <escenario>`. Tiene que dar lo
     mismo que a mano; si no, el guion depende de algo que cambia (una referencia, un dato de la vez anterior): corrígelo
     hasta que dé lo mismo dos veces.
   Un escenario que no se ve en pantalla (lo que manda una integración, un proceso nocturno) no lleva guion: dilo, lo
   cubren los casos de prueba.
3. **La unidad entera**: `python3 <skill>/scripts/qa.py repetir <p> <U>`. Escribe `qa/<U>/resultado.json`, y la issue de
   cada escenario que falla vuelve a pendiente: `indice.py issues <p> <U>` de `appian-functional-analyst` lo enseña, y la
   da otra vez con `--siguiente`. Quien la corrige repite los guiones. Un fallo en el «dado» puede venir de otra issue,
   la que construyó lo que se prepara: míralo antes de reabrir la del escenario.
4. **Entregar**, en pocas líneas: cada escenario y su resultado, de cada fallo qué se esperaba y qué salió, y lo que SAIL
   CLI no ve (las pantallas que recorrió, para que una persona mire en el navegador cómo se ven). Confirma y sube
   `qa/<U>/` (`git commit` y `git push`). Con la unidad sin fallos se marca construida; `proyecto.py … construida` avisa,
   sin impedirlo, si falta el QA o está a medias.
5. **Cerrar las sesiones** al terminar la campaña de QA (la unidad entregada sin fallos y sus guiones repetidos): `sail
   logout --data-dir <su carpeta>` de cada cuenta local. Cierra la sesión en el servidor y borra lo guardado y lo
   tecleado, que es como termina cada prueba; no se hace tras cada escenario porque, para repetir los guiones antes del
   paquete, quien los repite tiene que volver a entrar con la contraseña. Una sesión importada del Dev MCP no se cierra:
   no se sabe qué le pasa al Dev MCP.

## El guion

Un fichero JSON por escenario, `qa/<U>/HU-01.1.json`. Ejemplo ficticio:

```json
{
 "escenario": "HU-01.1",
 "dice": ["Dado un gestor", "Cuando registra una solicitud con título e importe y la envía",
          "Entonces la ve en su panel como «Enviada»"],
 "host": "dev.ejemplo.com",
 "site": "solicitudes",
 "roles": {"gestor": "qa.gestor"},
 "dado": [],
 "cuando": [
  {"rol": "gestor", "sail": ["load"]},
  {"rol": "gestor", "sail": ["navigate", "Nueva solicitud"]},
  {"rol": "gestor", "sail": ["interact", "Título", "QA {pasada}", "Importe (€)", "12.50"]},
  {"rol": "gestor", "sail": ["interact", "Enviar"], "espera": {"completado": true}}
 ],
 "entonces": [
  {"rol": "gestor", "sail": ["load"]},
  {"rol": "gestor", "sail": ["interact", "🔍", "QA {pasada}"], "espera": {"fila": {"con": "QA {pasada}", "Estado": "Enviada"}}}
 ]
}
```

- **`dice`**: las líneas del escenario tal como están en su `.feature`. Se comparan con lo que dice hoy el funcional
  (sin funcional, con el `.feature`): si el escenario cambió, también a propósito en una unidad posterior, el guion sale
  «desfasado» y no se repite hasta que QA lo rehaga.
- **`host`, `site` y `roles`**: el entorno, el site y el usuario de Appian de cada rol. El usuario no es secreto; el
  script busca su sesión en cada equipo (`session.json` bajo `$SAIL_HOME` y `~/.sail`, por usuario y host), así que no
  hay que decir en ningún fichero dónde está la de cada uno.
- **Un paso**: `{"rol", "sail": [orden y sus argumentos, sin el site], "espera"}`. Las órdenes son `load` (siempre
  `--fresh`), `navigate`, `interact`, `back` y `show`; `--confirm` va en la orden si el destino lo pide. Una fila de una
  rejilla se marca por su contenido, `{"rol": "revisor", "selecciona": "QA {pasada}"}`, nunca por el número que le dio
  Appian. Con un solo rol, «rol» se puede omitir.
- **`espera`**: `"completado": true` (el formulario se envió); `"hay"` y `"no_hay"`, refs o etiquetas, o su principio;
  `"texto"` y `"sin_texto"`, en lo que se ve de la página y en sus validaciones; `"fila": {"con": "…", "<columna>":
  "<valor o su principio>"}`, una fila de una rejilla que lleva ese texto y tiene esos valores, y `"sin_fila": "…"`,
  ninguna fila con ese texto (lo que se buscó también está en la caja de búsqueda: para decir que no se ve, `sin_fila`,
  no `sin_texto`). Cada paso falla además si SAIL CLI da error o si el servidor no cambió nada.
- **El «entonces» afirma algo**: al menos un `completado`, `hay`, `texto` o `fila`. Solo con `no_hay`, `sin_texto` o
  `sin_fila` pasaría también con una página vacía. Una clave que no existe o una comprobación vacía (`"hay": []`,
  `"texto": [""]`) tampoco valen: el guion sale «por terminar».
- **`{pasada}`** es distinto en cada escenario de cada repetición; **`{hoy}`**, la fecha.

Para que el guion dé lo mismo cada vez:
- Ninguna referencia que cambie entre cargas: ni `_cId`, ni las que el `--json` marca con `refIsPerRender` (el script
  las rechaza).
- Ninguna etiqueta con un dato dentro («Pendientes (22)»): su principio, «Pendientes», también vale para SAIL CLI.
- Nada que dependa de la vez anterior: lo que se teclea y se busca lleva `{pasada}`, y en una lista se busca con la caja
  de búsqueda de la rejilla (`"🔍"`) antes de mirarla, para que una fila nueva no quede en otra página.
- Un «no lo ve» lleva antes la prueba de que existe (en el «dado», quien lo creó lo ve): si no, el guion pasaría
  aunque el alta hubiera fallado.
- Dos enlaces con el mismo texto no se distinguen (el `--json` los da con `nth` y `of`): el script no pulsa uno al azar,
  el paso falla. Dilo en la entrega, que además es un problema de accesibilidad. Lo mismo si «selecciona» encuentra
  varias filas.
- Si lo esperado aún no se ve tras cargar y, como mucho, buscar o marcar una fila, el script vuelve a cargar y a mirar
  antes de darlo por fallado: el proceso puede no haber terminado.
- Nunca una contraseña ni un dato personal de verdad.

## Repetir

`python3 <skill>/scripts/qa.py repetir <p> [<U> …]`, sin IA: antes de cada paquete (F9), con todas las unidades de
`qa/`, y tras corregir un fallo. Sale con 0 si todo pasa, 1 si algo falla y 2 si no pudo repetir algo o está por hacer
(sin SAIL CLI, sin sesión, un guion por terminar o una unidad sin guiones). Escribe `qa/<U>/resultado.json`, que se sube
y no lleva rutas del equipo de nadie:

```json
{"unidad": "EV-01", "generadoEn": "2026-10-14T15:30:12Z",
 "escenarios": {"HU-01.1": {"resultado": "pasa", "guion": "HU-01.1.json", "issue": "ISS-02", "fecha": "…", "segundos": 9.1},
                "HU-03.2": {"resultado": "falla", "paso": "entonces 2", "motivo": "la fila con «QA {pasada}» tiene Estado «Enviada» y se esperaba Estado «Devuelta»", …}},
 "sinGuion": ["HU-02.1"]}
```

- **pasa** o **falla**: la última vez que se repitió. Lo que pasa con su issue si falla, en
  `appian-functional-analyst/references/cambios.md` §6. El motivo lleva `{pasada}` y `{hoy}`, no lo que valieron: el
  mismo fallo dice lo mismo en cada repetición, y la marca de una persona sigue valiendo para él.
- **desfasado**: el escenario ya no dice lo del guion; no cuenta como fallo, y QA lo rehace.
- **guion por terminar**: el guion está mal escrito o no llega a afirmar nada en el «entonces»; no devuelve la issue a
  quien construye: lo termina QA.
- **sinRepetir**: esta vez no se pudo, y dice por qué. Con una sesión caducada se queda el resultado anterior y dice
  cómo entrar. Si SAIL CLI no responde en 120 s o no llega al servidor, se para en ese paso y no repite nada más; lo que
  no repite deja de «pasar» (una pantalla que se cuelga no se esconde): sale **sin repetir**, con la fecha de su
  último «pasa» (`ultimoPasa`), y un «falla» se queda. Sin repetir no devuelve la issue a pendiente, pero
  `proyecto.py … construida` y `estado` lo avisan.
- **sinGuion**: escenarios de la unidad que QA aún no ha recorrido.

Si una pantalla cambió a propósito, se rehace solo su guion.

## Qué escribe

En `<p>`:
- `qa/<U>/<escenario>.json`: el guion de cada escenario recorrido
- `qa/<U>/resultado.json`: lo deja `qa.py repetir`, la última vez que se repitieron

Nada más: no toca `construccion/` ni `analisis/`, ni objetos del entorno.

## Recursos

| Fichero | Cuándo |
|---|---|
| `scripts/qa.py` | Para saber la sesión de cada cuenta y para repetir los guiones |
