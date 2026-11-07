# Adaptarse a las actualizaciones de Appian: diseño

Diseño del 4 de noviembre de 2026, revisado el 7 con las decisiones de Raúl y lo hablado en la sesión de Cowork
«Sail CLI en terminal». Sobre `main` (`37235be`), con el bundle DevMCP 26.9.10 (build `20261103-144057`) instalado. El
código empieza cuando Raúl dé paso a T1, que crea objetos en su entorno de desarrollo.

## El problema

Appian actualiza tres piezas de las que depende el plugin, y lo hace casi cada semana: en cinco semanas hubo cinco
bundles (builds del 30-sep, 8-oct, 19-oct, 26-oct y 3-nov; de la 26.6.110 a la 26.9.10). Cada bundle trae a la vez:

| Pieza | Qué usa el plugin de ella | Ejemplo de la 26.9.10 |
|---|---|---|
| **Herramientas del Dev MCP** | Ingeniería inversa y «verificar» (`devmcp_extract.py`); buenas prácticas y la construcción, a través de la IA | 5 herramientas nuevas de informes de tareas (`createTaskReport`…) |
| **Skill oficial `appian`** | Buenas prácticas remite a ella; el doc 14 recoge en qué contradice a la documentación | 9 reglas nuevas o ampliadas en su `SKILL.md` (`testInputs`, `x[i]` sobre un valor suelto, `a!headerContentLayout`…) |
| **SAIL CLI (`sail`)** | `appian-qa`: la IA escribe los guiones y `qa.py` los repite sin IA | Órdenes nuevas `tasks` y `preview` (`open` y `reload` ya estaban en la anterior) |

Hoy el plugin se entera tarde y a mano. La skill oficial sí tiene su aviso (`comprobar_divergencias.py`), pero:
- **SAIL CLI** no tiene ninguno. `qa.py` solo sabe `load`, `navigate`, `interact`, `back` y `show`, y su prueba usa un
  `sail` simulado que imita la 26.6.110. Si cambia el `--json`, la batería sigue en verde y el QA falla en un proyecto.
  Sin `tasks` y `open` no hay guion para un escenario con una tarea (enviar y aprobar), que es de los más comunes.
- **Herramientas del Dev MCP**: `devmcp_extract.py` ya lee el catálogo en cada ejecución, pero nadie avisa de que hay
  herramientas nuevas que alguna skill podría aprovechar, ni de si una que se cita ha desaparecido.

Y el plugin lo instala cualquiera: cada persona tiene su entorno (con su versión del plugin de Appian), su `sail` y sus
aplicaciones de prueba. Nada de esto puede quedar fijo en el plugin.

Lo que se busca: que una actualización cueste **un comando y tocar solo lo que señala**, que lo nuevo se aproveche
sin reescribir skills, y que quien use el plugin pueda comprobar su `sail` en su entorno y volver atrás si falla.

## El principio

El plugin **no copia lo que publica Appian: lo lee en vivo, guarda una foto para ver qué cambió y lleva un inventario
corto de lo que no puede dejar abierto.** Tres capas, las mismas para las tres piezas:

| Capa | Quién | Dev MCP | Skill oficial | SAIL CLI |
|---|---|---|---|---|
| **1. Leer en vivo** | IA y scripts, al trabajar | Ya se hace: `devmcp_extract.py` lee el catálogo y clasifica por firma con `devmcp_policy.json` | Ya se hace: buenas prácticas remite a sus ficheros | **Falta**: leer la ayuda de `sail` antes de escribir guiones |
| **2. Detectar el cambio** | Un script, al llegar un bundle | Catálogo instalado contra la foto | Manifiesto de la skill (huella por fichero) contra la foto | Órdenes, opciones y forma del `--json` contra la foto |
| **3. Inventario de lo fijo** | Fichero versionado, lo valida el script | Las herramientas que se citan por nombre (7 en la prosa) | Los ficheros de la oficial a los que se remite (ya lo mira `comprobar_divergencias.py`) | Las órdenes que repite `qa.py` y los campos del `--json` que lee |

Con la capa 1, lo nuevo se usa sin tocar el plugin. Con la 2 se sabe qué cambió. Con la 3 se distingue «hay algo
nuevo» de «esto rompe tal pieza».

## Quién hace qué

| | Quien mantiene el plugin (Raúl y colaboradores) | Quien usa el plugin |
|---|---|---|
| **Cuándo** | Al salir un bundle | Al actualizar su `sail`, o cuando `qa.py` avisa |
| **Qué** | Capas 2 y 3 en el repositorio: `comprobar_bundle.py`, las notas de versión, adaptar el plugin y publicarlo | Capa 1 y las comprobaciones de `qa.py`: pasar su banco de pruebas; si falla, seguir con el `sail` anterior |
| **Dónde prueba** | En su banco de pruebas | En su banco de pruebas |

El servidor del Dev MCP no se elige: desde la 26.6.105 rechaza las llamadas si su `mcp_src_sha` no coincide con el del
plugin de Appian del entorno (`version_gate.py`), así que sigue al entorno en cuanto cambia. La skill oficial no entra
en esa comprobación: llega en el mismo bundle y se instala con él, pero su integridad es otra cuestión (su manifiesto,
capa 2). `sail` es un programa aparte (el `INSTALL.txt` del bundle: «unrelated to the MCP server») y es lo único que se
puede retrasar a propósito.

## Capa 1: leer en vivo

**Reglas de redacción** para todas las skills (van a `CLAUDE.md`):
- Una skill dice **qué hay que conseguir** («leer la interfaz y sus casos de prueba»), no qué herramienta llamar. Un
  nombre de herramienta solo donde un script depende de él, y entonces va al inventario.
- Lo que explica la skill oficial o la ayuda de `sail` **no se copia**: se remite a ello. Ya lo dice `CLAUDE.md` («Lo que
  ya garantizan la skill oficial o el Dev MCP no se repite»); se extiende a SAIL CLI.
- Si el contrato técnico instalado (el esquema de una herramienta, la ayuda y las opciones de `sail`) contradice lo
  que dice una skill sobre él, **manda lo instalado**, y la sesión lo apunta en `docs/siguiente-version.md`. Solo eso:
  las autorizaciones, el método del plugin y las divergencias documentadas (doc 14) siguen vigentes.

**SAIL CLI en `appian-qa`.** Antes de escribir guiones, la IA lee `sail --version`, `sail --help` y la ayuda de cada
orden que vaya a usar. Esa ayuda está escrita para agentes (valores por tipo de componente, confirmaciones, lotes) y
llega con cada versión; `SKILL.md` deja de explicar cómo se maneja `sail` y se queda con lo que es del plugin: el guion,
las esperas y la repetición. Para no cargar de más cada sesión (la ayuda de `interact` son unas 150 líneas): primero
`sail --version`; si coincide con la versión con la que se escribieron los guiones de la unidad (se guarda en su
`resultado.json`), no se lee más; si no, solo la ayuda general y la de las órdenes que vayan a usarse, una vez por sesión.

**Dev MCP.** Lo nuevo lo descubre la IA en la lista de herramientas de cada sesión. Para los scripts, la política de
`devmcp_policy.json` ya clasifica una herramienta nueva por su nombre; el primer caso a mirar con la foto inicial son los
`TaskReport` (si `devmcp_extract.py plan` los reconoce como tipo o los toma por genéricos). Cada entorno tiene su versión
del plugin de Appian, así que dos personas pueden ver catálogos distintos: `devmcp_extract.py` debe seguir si falta una
herramienta, con un aviso (se comprueba en T2).

## Capa 2: un comando que dice qué cambió

`python3 pruebas/comprobar_bundle.py`, al llegar un bundle. Es del mantenedor: vive en `pruebas/`, que no entra en el
paquete. Da un solo informe, por pieza. Ejemplo ilustrativo, con lo que sí se comprobó al pasar de la 26.9.5 a la
26.9.10 (los «…» no se midieron):

```
Foto: bundle 26.9.5 (20261026-140102) · Instalado: 26.9.10 (20261103-144057)

Dev MCP     nuevas: createTaskReport, getTaskReport, listTaskReports, updateTaskReport, deleteTaskReport
            cambiadas (parámetros): …            desaparecidas y citadas por el plugin: ninguna
Skill       ficheros cambiados: SKILL.md, …   → revisar doc 14 (comprobar_divergencias.py)
SAIL CLI    órdenes nuevas: tasks, preview   opciones nuevas: …
            forma del --json: …
Rompe       …
```

- **La foto** vive en `pruebas/bundle/`, sellada con el commit del bundle y su `mcp_src_sha` (`BUILD-INFO.txt`):
  - `devmcp.json`: cada herramienta con sus parámetros y una huella de su descripción. Lo saca un subcomando nuevo de
    `devmcp_extract.py` (`catalogo`), que ya sabe leer el catálogo.
  - `skill-appian.json`: el `.bundle-manifest` de la skill oficial (SHA-256 por fichero), que dice exactamente qué
    ficheros cambiaron. Cuando cambia uno que el doc 14 cita, lanza `comprobar_divergencias.py`, que sigue como está.
  - `sail.json`: versión, órdenes, opciones de cada una y la **forma** del `--json` de cada orden: las rutas de sus
    campos, nunca sus valores (así no entra nada de un cliente).
- **La forma del `--json`** no se puede sacar sin servidor. Se captura con `--capturar`, en local y contra el banco de
  pruebas de quien lo lanza; el resto del script trabaja con lo guardado.
- **Las notas de versión.** Appian las publica en la ficha del App Market (`appmarket.appian.com/listings/appian-dev-mcp`),
  con apartados «SAIL CLI» y «Skills» por versión. No separan lo que rompe de lo nuevo, la entrada más reciente no lleva
  número y la 26.9.10 no figura en el historial: la fuente fiable es la comparación con la foto. La IA las lee después,
  para clasificar cada línea del informe.
- **Es un aviso**: sale con 0 salvo que lo que el inventario usa haya desaparecido o cambiado (1), o falten la foto o
  lo instalado (2). Con `--actualizar-foto` reescribe la foto tras revisar el informe, y eso se confirma en la rama.
- **En GitHub** (Linux, sin `sail` ni Dev MCP) solo corre la parte sin conexión: que el inventario cuadre con la foto
  versionada. Lo que necesita lo instalado se salta y lo dice.
- El simulador de las pruebas (`sail_simulado.py`) lleva la versión que imita; el script avisa si la foto es más nueva
  que el simulador, porque entonces la batería prueba un `sail` que ya no existe.

## Capa 3: el inventario de lo fijo

Corto y escrito a mano, solo con lo que rompe algo si cambia. Va en dos sitios, según quién lo lea:
- **`skills/appian-qa/scripts/sail-inventario.json`**, en el paquete, porque `qa.py` lo lee al arrancar en el equipo de
  cualquiera: las órdenes que admite un guion, cada una con la forma de sus argumentos (con el site o con una URL, si
  `qa.py` le añade `--fresh`); los campos del `--json` que lee `qa.py` (`status`, `completed`, `viewIsStale`, `ui`,
  `validations`, `options`, `movedNothing`, `nth`, `of`, `refIsPerRender`…), y la versión de `sail` con la que se
  verificó el plugin. La lista de órdenes de `qa.py` sale de aquí y deja de estar escrita en el código: añadir una
  orden es añadir una línea.
- **`pruebas/bundle/inventario.json`**, solo del mantenedor: las herramientas del Dev MCP citadas por nombre en skills y
  scripts. La skill oficial no lo necesita: `divergencias-oficial.json` ya lo lleva.

Las órdenes de un guion siguen siendo una **lista cerrada**: los guiones se repiten sin IA y no deben poder hacer
`login`, `logout` ni un `load` que tire lo tecleado. Lo flexible es que la lista sea un dato que se valida, no código.

## El banco de pruebas de cada persona

Un `sail` nuevo se prueba en una aplicación de pruebas de quien lo lanza, nunca en una fija del plugin:
1. **La app de pruebas ficticia del plugin**, construida en el entorno de desarrollo de esa persona. Su especificación
   y sus guiones van en `skills/appian-qa/assets/banco/`; se construye una vez por entorno con el Dev MCP, siguiendo
   `appian-best-practices`. Nombres y datos ficticios; el host y el site son variables del guion, así que los mismos
   guiones sirven en cualquier entorno.
2. **Si no puede o no quiere construirla, una aplicación de pruebas que nombre la persona.** La IA la recorre una vez
   con `sail`, como hace `appian-qa` con una unidad, y deja los guiones en su carpeta; `qa.py` los repite. Cubre solo lo
   que esa app ofrece, y el resultado dice qué tipos quedaron sin probar.
3. Sin ninguna de las dos, `qa.py banco` lo dice y no prueba nada: nunca elige por su cuenta una app de proyecto.

**Lo que cubre la app ficticia**, uno por tipo de lo que documenta `sail` (un tipo nuevo es una línea más):

| Pantalla o acción | Lo que ejercita |
|---|---|
| Lista de registros con filtros | `pages`, `load`, filtro de índice, filtro de rango de fechas, búsqueda y orden de la tabla |
| Formulario de alta (acción de registro) | Texto, número, desplegable, casillas, fecha, fecha y hora, selector de usuario, fichero, una validación que bloquea el envío, `back` |
| Envío y lectura | Enviar, `reload` y leer lo escrito en la vista del registro |
| Botón con confirmación | `interact --confirm` |
| Acción sin formulario de inicio | Encadena a la tarea (cambió en la 26.6.105) |
| Tarea de usuario asignada a un grupo | `tasks`, `open --accept`, completar la tarea con la otra cuenta |

Dos cuentas locales de prueba (un rol que pide y otro que aprueba), que crea cada persona en su entorno.

**La configuración de cada persona** va en `~/.appian-analisis-funcional/` (nombre a confirmar en T3), fuera del
repositorio, de los proyectos y de las carpetas de sesión de `sail`, que guardan cookies:
- `banco-pruebas.json`: por host, el site, el origen (ficticia o propia), el usuario de cada rol (nunca contraseñas) y
  la versión de `sail` con la que pasó la última vez, con su fecha.
- `banco/<host>/`: los guiones de una app propia.
- `sail/`: la copia del último `sail` con el que `qa.py` terminó todo en verde.

## La marcha atrás de `sail`

Appian no deja volver atrás: su `setup` sobrescribe `sail` sin guardar el anterior, y el bundle se descarga del plugin
instalado en el entorno, que sirve el de su versión. Sin copia, si un `sail` nuevo rompe `qa.py`, nadie puede repetir
sus guiones hasta que el plugin se adapte. Por eso la copia la guarda el plugin, para todos:
- Cada vez que `qa.py` termina todo en verde, guarda una copia del `sail` con el que lo hizo; solo la última (unos
  10 MB). «Todo en verde» es una pasada completa (el banco entero o todos los guiones de la unidad, sin elegir unos
  pocos) en la que cada guion pasó: una pasada parcial, con guiones desfasados o sin repetir no promueve la copia,
  aunque `qa.py` salga con 0.
- Si un `sail` nuevo falla, `qa.py` lo dice y da la orden para seguir con la copia: `SAIL_CLI=<copia>`, que `qa.py` ya
  admite (`sail_cli()`). No se reinstala nada; cuando el plugin se adapta, se quita la variable.

**Al arrancar**, `qa.py` compara `sail --version` con la versión verificada del inventario, con la del `resultado.json`
de la unidad y con la última que pasó el banco. Si es otra y no ha pasado el banco, avisa («`sail` 26.10.x no ha pasado
tu banco de pruebas: `qa.py banco`») y sigue. Si al `sail` instalado le falta una orden del inventario, no repite ese
guion y lo dice. `requisitos.py` muestra también la versión.

## La rutina de cada actualización

**Quien mantiene el plugin:**
1. Instala el bundle: Raúl con `appian-devmcp-update`; un colaborador, con el `setup` de Appian. Raúl añade como último
   paso de su skill lanzar `comprobar_bundle.py` en el repositorio del plugin, en una rama nueva sacada de `main`.
2. Si cambió `sail`, `--capturar` contra su banco.
3. La IA lee las notas de versión y clasifica cada línea del informe en corrección, capacidad nueva o cambio de
   comportamiento. Cada línea va a uno de tres sitios:
   - **Rompe**: se corrige en esa rama antes de seguir usando la pieza afectada.
   - **Cambió algo que el plugin documenta** (una guía de la oficial, una divergencia): lo revisa la IA, y lo que Appian
     haya corregido se quita del plugin.
   - **Nuevo**: si lo aprovecha la capa 1 sin cambios, no se hace nada; si una skill tendría que usarlo de otra manera
     (los `TaskReport` en ingeniería inversa, `tasks` en el QA), va como pendiente a `docs/siguiente-version.md`, con su
     porqué. Una capacidad nueva de `sail` señala además, para los proyectos, los escenarios marcados como «no
     automatizable» que ya podrían repetirse.
4. `--actualizar-foto`, la versión verificada en `sail-inventario.json`, commit y PR como cualquier otro trabajo.

Una actualización sin nada que rompa ni nada documentado que cambie se queda en los pasos 1 y 2 y la foto.

**Quien usa el plugin:**
1. Tras actualizar `sail`, o cuando `qa.py` lo avisa: `qa.py banco`.
2. En verde, sigue. En rojo, sigue con la copia (`SAIL_CLI`) y se lo cuenta a quien mantiene el plugin.
3. No actualiza `sail` a mitad de una regresión ni justo antes de preparar un paquete (lo dice `appian-qa`).

## Las pruebas de `qa.py`: simulado y real

El selftest de `appian-qa` usa un `sail` simulado (`sail_simulado.py`), y debe seguir así: la batería corre en GitHub
sin servidor ni cuentas, no crea datos en ningún entorno, tarda segundos y provoca a voluntad lo que en un servidor
real no se puede (un `sail` que se cuelga, sin red, que lee su entrada). Lo que falla hoy no es el simulador, sino que
nada lo ata al `sail` real. Con este diseño, dos niveles:

| Nivel | Dónde y cuándo | Qué prueba |
|---|---|---|
| **Simulado** | GitHub y el equipo, en cada cambio | La lógica de `qa.py`: esperas, reintentos, fallos, resultado. El simulador responde con la forma capturada del `sail` real y lleva la versión de la que sale |
| **Real** | En el equipo, contra el banco de pruebas de quien lo lanza, con cada `sail` nuevo | Que `sail` sigue respondiendo con esa forma (`--capturar`, el mantenedor) y que los guiones del banco pasan (`qa.py banco`, cualquiera) |

Una orden nueva de `sail` no obliga a tocar el simulador: lo hace solo si `qa.py` la va a repetir, y entonces se añaden
a la vez la línea del inventario, la respuesta capturada, su guion en el banco y su prueba. Para escribir guiones a mano,
la IA ya la conoce por la ayuda (capa 1).

Es lo que recomienda Appian en la skill oficial (`references/site-testing.md`): leer `sail --help` y la ayuda de cada
orden una vez en vez de suponer opciones; una cuenta local por rol (`SAIL_USERNAME` y `SAIL_PASSWORD`), «la única
prueba completa»; `--from-devmcp` para actuar como quien usa el Dev MCP; una `--data-dir` por ejecución a la vez; pulsar
cada envío y leer después lo escrito. `appian-qa` ya sigue lo de las cuentas, las carpetas y el `--json`, y rechaza un
guion que apunte a un `_cId` o a una ref que cambia en cada carga; lo que le falta es leer la ayuda (capa 1).

## Decisiones

**Raúl, 7-nov:**
1. **Un `sail` nuevo se instala y se comprueba, con marcha atrás**, en vez de probarlo aparte antes de instalarlo. La
   marcha atrás queda en el plugin (la copia del último `sail` en verde y `SAIL_CLI`), así que sirve a cualquiera, no
   solo a quien tiene `appian-devmcp-update`.
2. **Los escenarios de prueba se pasan en la app ficticia del plugin**, construida en el entorno de cada uno; si no la
   hay, en una app de pruebas que nombre la persona. El plugin no fija aplicaciones, sites, entornos ni cuentas.
3. **Por confirmar:** la especificación y los guiones del banco van en el paquete (`skills/appian-qa/assets/banco/`),
   y eso choca con la letra de `CLAUDE.md` («Ninguna skill lleva un proyecto, tampoco de ejemplo»). No es un proyecto
   sino el banco de pruebas de la herramienta, con datos ficticios y sin cliente. Propuesta: decirlo como excepción en
   `CLAUDE.md` (T5).
4. **T1 autorizado** («doy paso con T1», con Codex supervisando): construir la app ficticia en el desarrollo de
   Indra-spain (`indra-spain.appiancloud.com`), solo con el prefijo `BPS`, y sus dos cuentas de prueba. Que las cuentas
   las cree y las estrene la persona es propuesta de Claude, no decisión de Raúl: `createUser` existe, pero recibe la
   contraseña como texto en la llamada, y una contraseña no pasa por la conversación.
   T2, T3 y T4 esperan a que la rama `claude/pruebas-metodo-20261104` entre en `main`, porque cambia los mismos
   ficheros (`qa.py`, el `SKILL.md` de `appian-qa`, `devmcp_extract.py`).

**Raúl, 4-nov:**
1. ~~Pruebas reales contra IFA Informes y Acciones~~: sustituida por la 2 del 7-nov. IFA no tiene tareas de usuario, y
   las aplicaciones de proyecto desaparecen (`ctc-tarjetas`, `cmde-cuadro-mando` y `contratacion-cpr-p6` ya responden
   «no existe o no tienes permisos»).
2. **El script vigila también el catálogo del Dev MCP.**
3. **`comprobar_divergencias.py` sigue aparte**, siempre que la rutina no se vuelva lenta. Medida orientativa, a
   confirmar en T2: la comparación con la foto y `comprobar_divergencias.py` tardan segundos y no necesitan conexión;
   leer el catálogo del Dev MCP, del orden de segundos; solo `--capturar` y el banco tardan minutos, y se lanzan una vez
   por `sail` nuevo, no en el trabajo diario. Si la rutina completa pasa de unos 5 minutos o de un comando, se vuelve a
   analizar con Raúl.

## Trabajo, en orden

| | Qué | Por qué en este orden |
|---|---|---|
| T1 | Banco: la especificación de la app ficticia y sus guiones (`skills/appian-qa/assets/banco/`); construirla en el desarrollo de Indra-spain con el Dev MCP; capturar allí el `--json` real de `sail` 26.9.10 de cada orden (`show`, `interact`, `load`, `navigate`, `back`, `tasks`, `open`, `reload`) y compararlo con el simulador | Es el dato del que depende todo lo demás: dice si algo ya se ha roto sin que se vea |
| T2 | `comprobar_bundle.py`, `pruebas/bundle/` con la foto inicial (26.9.10) y su inventario; subcomando `catalogo` de `devmcp_extract.py` (antes, comprobar que conecta en este equipo: su ayuda habla de `.mcp.json` y aquí el Dev MCP está en `~/.claude.json`) y que siga si falta una herramienta; `--capturar` contra el banco de quien lo lanza | Sin foto no hay qué comparar |
| T3 | `appian-qa`: leer la ayuda de `sail`; `sail-inventario.json` y las órdenes desde él; `open`, `tasks` y `reload` en los guiones; `qa.py banco` y la configuración de cada persona; el aviso al arrancar; la copia del último `sail` en verde y `SAIL_CLI`; no actualizar a mitad de una regresión; la versión en `requisitos.py` | Cubre los escenarios con tareas y deja a cualquiera probar y volver atrás |
| T4 | Simulador al día con lo capturado en T1, sellado con su versión, y sus pruebas en `selftest.py` | Que la batería pruebe el `sail` de verdad |
| T5 | `CLAUDE.md`: reglas de redacción, la excepción del banco (si Raúl la confirma) y la rutina del mantenedor en lugar de la línea de `comprobar_divergencias.py`; revisar las 7 herramientas citadas en prosa | Que lo nuevo que se escriba no vuelva a fijar nada |
| T6 | Último paso de `appian-devmcp-update` (skill global de Raúl, fuera del repositorio): se cambia una vez, en su `update.sh` común de `~/.claude`, al que remiten las copias de los demás clientes. Solo sirve a Raúl | Que su rutina no dependa de acordarse |

## Lo que no se hace

- **Generar skills a partir del bundle.** Lo que hay que entender o decidir lo hace la IA; el script solo avisa.
- **Depender de `sail` o del Dev MCP en la batería de GitHub.** Corre sin ellos.
- **Fijar en el plugin aplicaciones, sites, entornos o cuentas de prueba.** Cada persona tiene los suyos.
- **Probar un `sail` nuevo en una app de proyecto que la persona no haya nombrado.**
- **`sail preview` en el QA.** Solo funciona en servidores de rama `appian-dev`; los entornos de los proyectos no lo son.
- **Fijar el plugin a una versión de Appian.** La versión verificada dice desde cuál se ha revisado; no impide usar una
  más nueva, solo avisa.

## Límites

- Una herramienta que cambia de comportamiento sin cambiar de nombre, de parámetros ni de descripción no la detecta la
  foto. La cubren los selftest de cada script y las pruebas con proyectos.
- La forma del `--json` solo se actualiza cuando alguien lanza `--capturar` contra su banco. Si nadie lo hace, el
  informe lo dice («forma del --json: capturada con la 26.9.10»).
- Con una app de pruebas propia, el banco cubre solo lo que esa app ofrece.
- La copia del `sail` anterior solo existe si `qa.py` terminó alguna vez todo en verde en ese equipo.
- Las URL de docs.appian.com con versión fija siguen con `comprobar_anclas.py` antes de publicar.
