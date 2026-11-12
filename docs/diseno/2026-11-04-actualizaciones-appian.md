# Adaptarse a las actualizaciones de Appian: diseño

Diseño del 4 de noviembre de 2026, rehecho el 11 con las decisiones de Raúl de ese día, el análisis de lo que han
costado las actualizaciones y el primer caso real (el paso del bundle 26.9.10 al 26.9.15). Sobre `main` (`37235be`).

## El problema

Appian actualiza casi cada semana tres piezas de las que depende el plugin, y llegan juntas en un bundle: seis en seis
semanas, de la 26.6.110 a la 26.9.15.

| Pieza | Qué usa el plugin de ella | Lo que cambió en la 26.9.15 |
|---|---|---|
| **Herramientas del Dev MCP** | Ingeniería inversa y «verificar» (`devmcp_extract.py`); buenas prácticas y la construcción, a través de la IA | 4 herramientas nuevas (decisiones) y 17 esquemas cambiados; nueve exigen ahora un parámetro que antes no, o con otro nombre |
| **Skill oficial `appian`** | Buenas prácticas remite a ella; el doc 14 recoge en qué contradice a la documentación | `SKILL.md` y un fichero nuevo, `references/decisions.md` |
| **SAIL CLI (`sail`)** | `appian-qa`: la IA escribe los guiones y `qa.py` los repite sin IA | `interact` valida un envío antes de mandarlo y trae `--no-validate` |

Mientras el servidor local y el plugin del entorno no son del mismo build, **el Dev MCP rechaza todas las llamadas**:
actualizar no es opcional ni se puede retrasar. Y el plugin lo instala cualquiera, cada uno con su equipo, su entorno
y sus cuentas.

## Lo que se busca

1. **Que el plugin siga funcionando** tras cada actualización, y que si algo se rompe se sepa ese día y no en un proyecto.
2. **Que lo nuevo se aproveche**: saber qué trae cada bundle y qué parte del plugin debería usarlo.
3. **Que sirva a cualquiera** (Raúl, 11-nov): nada atado a un equipo, un sistema, un cliente de IA, un entorno o unas
   cuentas concretas.
4. **Una solución limpia**: pocas piezas, cada una con su prueba, sin listas que mantener a mano.

## Lo que han costado las actualizaciones hasta hoy

Del registro (`docs/evaluaciones.md`, `docs/siguiente-version.md`) y de la 26.9.15:

| Qué pasó | Ejemplo | Por qué no se vio |
|---|---|---|
| Un script se rompe sin avisar | Al pasar al 26.9 el extractor perdía los modelos de proceso: cambió la forma de la respuesta | Sus pruebas usan un Dev MCP simulado. `qa.py` tiene el mismo riesgo: su simulador imita el `sail` 26.6.110 |
| Lo que el plugin afirma caduca | El doc 10 decía que los avisos de Design Guidance no se podían leer y `validateDesignObjects` ya los daba; con la 26.9.10 cambiaron 3 de 10 observaciones del doc 14 | Nadie relee una afirmación si no falla |
| Una herramienta nueva no se usa | Los filtros de usuario quedaron excluidos por llevar «user» en el nombre; `sail` trae `tasks`, `open` y `reload` y `qa.py` sigue con cinco órdenes | Nadie avisa de lo nuevo |

Donde conduce la IA (construir, revisar, escribir guiones), lo nuevo se ve en cada sesión. Donde conduce un script, la
respuesta tiene que tener la forma que espera, y lo nuevo solo se aprovecha cambiando el plugin. **El riesgo está en
los dos scripts que hablan con Appian (`qa.py` y `devmcp_extract.py`) y en lo que el plugin afirma.**

## La solución: una skill del plugin que actualiza y comprueba

Una skill nueva, `appian-actualizacion` (nombre por confirmar), para cualquiera que use el plugin. Hace lo que hoy hace
la skill personal de Raúl (`appian-devmcp-update`, atada a su equipo) y añade las comprobaciones. Tiene dos fases,
porque tras instalar hay que reiniciar el cliente de IA: hasta entonces la sesión sigue hablando con el servidor viejo.

**Fase 1, instalar** (un comando, `actualizar.py instalar <bundle>`):

| Paso | Quién | Qué |
|---|---|---|
| 1 | IA | Pregunta al Dev MCP la versión del plugin de cada entorno (`getDevMcpVersionInfo` responde aunque lo demás se rechace) |
| 2 | Persona | Descarga el bundle de su entorno (`/suite/plugins/servlet/stateless/downloads`): pide su sesión |
| 3 | Script | Comprueba lo que hace falta (Python, `uv`, dónde está instalado el servidor) y que el bundle es el del plugin (`mcp_src_sha`) y no es más antiguo que lo instalado. Si algo falta, para sin tocar nada |
| 4 | Script | **Foto de antes**: catálogo de herramientas, manifiesto de la skill oficial y ayuda de cada orden de `sail` |
| 5 | Script | **Guarda el bundle anterior** (lo instalado, sin el entorno virtual) y lo relee entero. Appian no deja volver atrás y el navegador pisa la descarga vieja |
| 6 | Script | Solo entonces sustituye el servidor, con el bundle ya extraído aparte y una marca mientras dura: si se corta, la misma orden lo termina sin repetir la foto ni la copia. Después, como dice la guía oficial, `uv sync`, el `setup` de `sail` de su sistema e `install-skills`: hace los tres, que no dependen uno de otro, y dice cuáles fallaron. Si falta el Chromium de Playwright lo dice el propio Dev MCP, con la orden que lo instala |
| 7 | Persona | Reinicia sus clientes de IA |

**Fase 2, comprobar** (tras reiniciar, `actualizar.py comprobar`):

| Paso | Quién | Qué |
|---|---|---|
| 8 | IA | Confirma, con la herramienta de versión del Dev MCP, que servidor y plugin son del mismo build (`actualizar.py estado` dice el instalado). Si no lo son, el Dev MCP rechaza las demás llamadas: falta reconectar el servidor en el cliente |
| 9 | Script | **Informe de qué cambió** entre la foto de antes y lo instalado, y qué de ello cita el plugin |
| 10 | Script | **Banco de pruebas**: repite sus guiones con `qa.py` y extrae la aplicación con `devmcp_extract.py`, contra un resultado esperado |
| 11 | IA | Lee el informe: clasifica cada cambio, relee lo que el plugin afirma de lo que cambió y dice qué novedad merece usarse |

El resultado es uno de tres, sin término medio:

- **En verde**: se hicieron todas las comprobaciones y pasaron.
- **Falla**: una incompatibilidad demostrada (un guion del banco o la extracción no dan lo esperado). Dice cuál y cómo
  seguir con el `sail` anterior.
- **No se pudo comprobar**: falta evidencia (el banco no está construido, una sesión caducada, builds distintos). No es
  un verde.

Una actualización instalada cuya comprobación falla o no se hizo no queda como correcta.

### El informe de qué cambió

Compara dos fotos y es el mismo para las tres piezas. El de la 26.9.15, sacado a mano el 11-nov:

```
Foto: 26.9.10 (20261103-144057) · Instalado: 26.9.15 (20261109-154835)

DEV MCP   223 -> 227 herramientas
  nuevas: deleteDecision, getDecision, listDecisions, updateDecision
  desaparecidas: ninguna
  cambia el esquema de addPackageObjects: +objectUuids, -objects (obligatorio)
  cambia el esquema de createExpressionRule: +testCases; description pasa a obligatorio
  cambia el esquema de getDocumentContent: +savePath (obligatorio)
  …
SKILL appian   64 -> 65 ficheros   nuevos: references/decisions.md   cambiados: SKILL.md
SAIL CLI  órdenes nuevas: ninguna
  interact: opción nueva --no-validate; un envío con un campo obligatorio vacío se rechaza sin mandarlo
```

El informe dice **qué cambió**, no qué se rompió: una incompatibilidad solo la demuestra el banco. Lo que sí hace es
cruzar los cambios con las herramientas y órdenes que citan las skills del plugin, para que la IA sepa qué releer. Con
eso, la IA reparte cada cambio en tres:

- **Puede romper**: algo que el plugin usa o cita ha desaparecido o exige otra cosa. De la 26.9.15: `addPackageObjects`
  ya no admite `objects` (buenas prácticas, doc 08, habla de «UUID y tipo»), y un guion que comprueba una validación
  al enviar, porque `sail` ahora rechaza ese envío en vez de devolver el mensaje. Lo segundo se confirma o se descarta
  en el banco.
- **Cambió algo que el plugin documenta**: se relee. De la 26.9.15: `createExpressionRule` admite `testCases` (el
  doc 14 describe el caso que deja `testInputs`) y las nueve observaciones de conducta del doc 14 vistas con el build
  anterior.
- **Nuevo**: si la IA lo usa sin cambios, nada; si una skill debería usarlo de otra manera, un pendiente con su porqué.
  De la 26.9.15: las cuatro herramientas de decisiones en ingeniería inversa.

Se revisan también los pendientes que esperan a Appian («mientras el bundle no lo permita, lo hace una persona»).

El catálogo de herramientas lo da el extractor, que ya sabe encontrar la configuración del Dev MCP y conectar: al
planificar cualquier aplicación deja `extraccion/mcp_catalog.json`, y la foto admite ese fichero tal cual. La skill de
actualización solo lee esa salida; no importa nada del interior de otra skill. Se toma tras reiniciar, con `informe`, y
esa foto es la de antes en la siguiente actualización: antes de instalar no se puede, porque el servidor viejo ya no
habla con el entorno. Su límite: el extractor guarda los 500 primeros caracteres de cada descripción.

### El banco de pruebas

Una aplicación ficticia, `BPS`, que cada persona construye **una vez** en su entorno de desarrollo con el Dev MCP,
siguiendo su especificación. Es el accesorio de la comprobación, así que va con la skill de actualización y no con
`appian-qa`. Sirve a los dos scripts:

- **`qa.py`**: un guion por tipo de lo que hace `sail` (lista con filtros, formulario con cada tipo de campo y una
  validación, envío y lectura, confirmación, tarea encadenada, tarea de grupo con otra cuenta).
- **`devmcp_extract.py`**: extraer `BPS` y comparar con un resultado esperado **escrito a mano** (objetos por tipo,
  campos, relaciones, casos de prueba), no generado por el propio extractor. Para que ejercite `verificar` y
  `regresion`, `BPS` gana dos o tres reglas con sus casos de prueba.

Es lo que detecta la rotura que ya hubo: una extracción incompleta o un guion que falla se ven el día de la
actualización. Sustituye a fotografiar la forma de cada respuesta. El banco cubre lo que contiene: una rotura conocida
que no reproduzca se queda como caso en la prueba local del script.

Sin banco construido, la comprobación lo dice y se queda en el informe: nunca usa una aplicación de proyecto.

### Recuperar el `sail` anterior

No es deshacer la actualización: el servidor del Dev MCP no se puede retrasar, sigue al plugin del entorno. `sail` sí,
porque es un programa aparte. Si el banco falla con un `sail` nuevo, la skill saca el `sail` del bundle anterior, que
guardó en el paso 5, y da la orden para seguir con él (`SAIL_CLI=<ruta>`, que `qa.py` ya admite) hasta que el plugin
se adapte.

### Lo que se lee en vivo

Reglas de redacción para todas las skills (van a `CLAUDE.md`):

- Una skill dice **qué hay que conseguir**, no qué herramienta llamar. Un nombre de herramienta solo donde un script
  depende de él.
- Lo que explican la skill oficial o la ayuda de `sail` **no se copia**: se remite a ello. `appian-qa` deja de
  explicar cómo se maneja `sail`; antes de escribir guiones la IA lee `sail --help` y la ayuda de las órdenes que use.
- Si el esquema de una herramienta o la ayuda de `sail` contradicen lo que dice una skill sobre ellos, **manda lo
  instalado** y la sesión lo apunta como pendiente. Solo eso: las autorizaciones, el método del plugin y las
  divergencias documentadas (doc 14) siguen vigentes.

## Genérico: qué no puede tener y cómo se prueba

| No puede depender de | Cómo se resuelve |
|---|---|
| Una ruta o un equipo | La carpeta del servidor es la de la guía de Appian (`~/appian-dev-mcp-server`) o la que diga la persona (`--servidor`). Si no es una instalación, el script para y lo dice |
| Un sistema operativo | Un solo script en Python; llama al `setup` y al `install-skills` que trae el bundle para cada sistema |
| Un cliente de IA | `install-skills` de Appian detecta los suyos; los demás, con la carpeta que diga la persona |
| Un entorno o una aplicación | El banco se construye en el entorno de cada uno; host y site son variables de los guiones |
| Unas cuentas | Dos cuentas de prueba que crea cada persona; el plugin no guarda usuarios ni contraseñas |
| Arreglos locales | Un parche propio sobre el servidor no entra en el plugin; se avisa de que la instalación lo pisa |

El estado de cada persona va en `~/.appian-analisis-funcional/`, fuera del repositorio, de los proyectos y de las
carpetas de sesión de `sail`: las fotos y el bundle anterior, por instalación del servidor y build; la configuración y
el resultado del banco, por entorno. Nada de eso se distribuye, ni credenciales ni sesiones.

Se prueba sin Appian: `pruebas/appian-actualizacion/selftest.py` instala bundles de mentira (con su `BUILD-INFO`, sus
`setup` y su manifiesto) en una carpeta personal temporal, en los tres sistemas de la batería de GitHub, y compara
fotos preparadas. Lo que necesita un entorno (el banco) se prueba en el de quien lo lanza.

## Quién hace qué

| | Quien usa el plugin | Quien lo mantiene, además |
|---|---|---|
| **Cuándo** | Al salir un bundle | Lo mismo, en una rama del repositorio |
| **Qué** | Las dos fases. Si el banco falla, sigue con el `sail` anterior y avisa | Corrige lo que rompe, relee lo documentado (`comprobar_divergencias.py`, que sigue aparte), apunta lo nuevo, pone al día los simuladores con lo que el banco enseñó y la versión verificada |

**La versión verificada** es una línea en la skill: el bundle con el que el plugin pasó su banco, con la fecha y lo
que se probó, que queda en `docs/evaluaciones.md`. Con un bundle más nuevo, la comprobación lo dice y manda pasar el
banco; no impide trabajar.

## Las pruebas de los scripts: simulado y real

Los simuladores siguen: la batería corre en GitHub sin servidor ni cuentas y provoca lo que en un servidor real no se
puede (un `sail` colgado, sin red). Lo que cambia es que ahora algo los ata a lo real: cuando el banco enseña una
diferencia, se corrige el script y su simulador a la vez, y el simulador lleva la versión que imita.

Con la cuenta propia, sobre `BPS`, las respuestas de `load`, `show`, `reload`, `tasks` e `interact` (búsqueda y filtro)
tienen la misma forma en la 26.9.10 y en la 26.9.15, y traen lo que `qa.py` lee. Falta lo que pide las cuentas de
prueba: formulario, validación, `navigate`, `back`, `open` y las tareas.

## Decisiones

**Raúl, 12-nov** (preguntado, tras plantear él que una actualización no puede traer retrabajo en los proyectos ya
hechos, con una instalación de usuario y proyectos de versiones distintas):
1. A veces tiene a la vez entornos con el plugin del Dev MCP en builds distintos.
2. Que lo existente «siga funcionando» es poder repetir su QA y seguir construyendo sobre ello.
3. La versión con que se probó se anota sola en `qa/<U>/resultado.json`; sin fichero ni orden nuevos.
4. Al retomar un proyecto probado con otra versión, la sesión avisa y él decide; no se repite ni se cambia nada solo.

De ahí, con la segunda opinión de Codex (compatibilidad por defecto, lo nuevo cuando aporta, ajuste a demanda; la
versión identifica de dónde sale un resultado, no prueba que sea compatible): `qa.py` anota la procedencia de cada
escenario recorrido, `estado --proyecto` la compara con lo instalado sin tocar nada, y la skill dice qué se hace y
qué no con un proyecto ya hecho y con dos builds a la vez. **Sin medir:** dos carpetas de servidor con dos entornos
reales en builds distintos, y repetir con la versión nueva el QA de un proyecto real anterior.

**Raúl, 11-nov:**
1. **El enfoque del análisis, aplicado**: pruebas reales de los dos scripts sobre el banco, revisar lo que el plugin
   afirma y fuera los inventarios escritos a mano.
2. **Las comprobaciones van con la actualización**, en una skill, y esa skill es del plugin. Su objetivo: que lo use
   cualquiera sin depender de su equipo ni de sus proyectos, con una solución limpia.
3. **El banco sale de `appian-qa`** y va con esa skill. **Por confirmar** la letra en `CLAUDE.md`: «ninguna skill lleva
   un proyecto» no cuenta para el banco de pruebas de una herramienta, ficticio y sin cliente.
4. **Las cuentas de prueba de su entorno las crea la IA** y guarda sus contraseñas, fuera del repositorio. Es su
   decisión para su entorno de desarrollo; el plugin no la impone a nadie.
5. Codex, como segunda opinión. La dio el 11-nov sobre un resumen, sin poder leer los ficheros: «adelante con
   cambios», todos recogidos aquí (el resultado en tres estados estrictos, la configuración por instalación y entorno
   sin suponer ninguna, «recuperar el `sail`» en vez de marcha atrás, el catálogo como salida de datos del extractor y
   acordar la base con la rama del método antes de tocar sus ficheros). Después revisó tres veces el código de
   `actualizar.py`, entero: «no listo» (una sustitución cortada que no se podía repetir o pisaba la copia buena, la
   validación del `.tar.gz` y el nombre del build usado como carpeta sin validar), «no listo» (nombres que en Windows
   son el mismo, con qué bundle se reanuda, lo que el bundle anterior deja en la raíz, fotos a medias) y «listo con
   arreglos», los cuatro aplicados. No se aplicaron dos cosas, y Codex las dio por aceptables para un uso manual:
   guardar copia también al repetir la instalación del mismo bundle (se avisa de que ese caso no la guarda) y un
   bloqueo entre dos instalaciones a la vez (se dice que no se haga). Sus revisiones son de lectura: no ejecutó nada.

**Raúl, 7-nov:** un `sail` nuevo se instala y se comprueba, con marcha atrás; los escenarios se pasan en la app ficticia
del plugin, construida en el entorno de cada uno; T1 autorizado en el desarrollo de Indra-spain, con el prefijo `BPS`.

**Raúl, 4-nov:** se vigila también el catálogo del Dev MCP; `comprobar_divergencias.py` sigue aparte.

**Lo que cambia respecto al diseño del 7-nov:** `pruebas/comprobar_bundle.py` y la foto versionada en el repositorio
pasan a ser la skill y las fotos de cada persona; los inventarios a mano (`sail-inventario.json`, `inventario.json`)
no se hacen; la aplicación de pruebas propia de cada persona se aplaza hasta que alguien la pida.

## Trabajo, en orden

| | Qué | Depende de |
|---|---|---|
| T1 | Banco `BPS` en Indra-spain. **Hecho (11 y 12-nov):** la aplicación, lo esperado del extractor (`esperado.json`) y cinco guiones que cubren todas las filas de su especificación y pasan con el `sail` 26.9.15 y con el 26.9.10: la lista con filtros; el formulario con un campo de cada tipo y el registro; la validación que bloquea el envío; la confirmación de la tarea encadenada seguida de la tarea del grupo, que el aprobador abre, acepta y completa; y el permiso que se niega. Las dos cuentas de prueba, creadas con el Dev MCP de la sesión sin contraseña temporal, con su sesión de `sail` (las del 7-nov tenían contraseña temporal y `sail` no entra con ellas: quedan sin uso). Dos reglas de expresión con casos de prueba, usadas por el formulario y la tarea. Recorrer el banco destapó dos defectos suyos, ya corregidos en Appian: el proceso exige el comentario de «Confirmar envío» y un motivo en «Aprobar solicitud», y los formularios no los pedían ni los ponían. **Falta:** un retoque de la aplicación que no afecta a los guiones (`docs/siguiente-version.md`) | Raúl: desactivar en la consola de administración `bps.solicitante` y `bps.aprobador`, las dos cuentas sin uso (se llaman igual que las nuevas y el selector de usuario enseña las cuatro; el guion las distingue buscando por el usuario) |
| T2 | La skill, primero lo que no toca ficheros de otra rama. **Hecho (11-nov):** `actualizar.py` con `estado`, `foto`, `instalar`, `informe` y `sail-anterior`, y su prueba sin Appian (134 comprobaciones), que pasa en GitHub en Windows, macOS y Linux con Python 3.9 y 3.12; reproduce el informe de la 26.9.15 con las dos fotos reales y, en una carpeta de ensayo, instala la 26.9.10, actualiza de verdad a la 26.9.15 y recupera el `sail` 26.9.10, en Windows. Los instaladores de Linux y de macOS del bundle 26.9.15 se han leído enteros contra cómo los llama `instalar` (12-nov): de ahí sale que los pasos ya no paran en el primero que falla y que se avisa si Appian se salta un cliente. **Falta:** esa instalación con el bundle real en Linux y en macOS; el equipo donde se hizo no tiene WSL ni Docker (mirado el 12-nov) y el bundle no se sube a GitHub, así que la hace la primera persona que lo use en esos sistemas. En los README, los requisitos y el enrutado, la skill ya figura, con el enrutado medido. El catálogo sale del fichero que ya deja el extractor, sin tocarlo. Resultados en `docs/evaluaciones.md` | — |
| T3 | `comprobar` con el banco y lo que `qa.py` necesitaba. **Hecho (11 y 12-nov):** `comprobar` mira la extracción de la aplicación del banco contra `esperado.json` (objetos por tipo, hechos del modelo que arma el extractor y errores previstos) y repite con `qa.py` los guiones del banco en el entorno y con las cuentas de quien lo lanza; donde un paso teclea el usuario de un rol, pone el suyo. **Lo que enseñó el banco, ya en `qa.py`:** (1) con el `sail` 26.9.15, un envío que la validación pararía no se manda y sale como error, donde el 26.9.10 devolvía las validaciones: `qa.py` lo da por el rechazo esperado solo si el paso espera un texto que está en los motivos del rechazo; (2) un paso nuevo, «tarea», abre la tarea de un rol que se llama exactamente así, la acepta y la recarga (cuál es se sabe por el nombre, antes de abrir nada: si varias se llaman igual, falla sin abrir ninguna; un texto de su formulario se puede comprobar después), porque `open --accept` deja en pantalla el formulario de antes de aceptar; y la orden `reload`. Cada cosa, con su caso en el simulador y en la prueba de `appian-qa`. Unida de prueba con la rama del método, solo chocan `CLAUDE.md` y `docs/evaluaciones.md`, y la prueba de `appian-qa` del árbol unido pasa entera (123), con lo de las dos ramas. La primera orden sobre un formulario recién abierto devuelve `movedNothing` aunque el valor entra, con los dos `sail`: lo distingue el `qa.py` de la rama del método, y los guiones del banco no dependen de ello. `appian-qa` manda leer la ayuda de `sail` instalada antes del primer recorrido, y que mande ella si contradice a la skill | — |
| T4 | Simuladores al día con lo que enseñe el banco, con su versión. **Hecho (12-nov):** el SAIL CLI simulado de `appian-qa` sabe negarse a mandar un envío, como el 26.9.15, y tiene tareas que se listan, se abren por su dirección y, como en el de verdad, siguen enseñando el formulario de antes de aceptar hasta recargar. La prueba de `appian-actualizacion` repite con él solo los dos guiones del banco que ese simulador, que es de otra aplicación, sabe contestar; los otros tres se repiten en el entorno de cada uno | — |
| T5 | **Hecho (11-nov):** `CLAUDE.md` con las reglas de redacción, el banco y la rutina de cada bundle. **Falta:** que la skill personal de Raúl se quede en lo suyo (su parche y sus otros clientes, con `--skills-dir`) y llame a esta para instalar, que es suya y está fuera del repositorio. Se hace a la vez que se publica el plugin con esta skill: si no, en su equipo habría dos entradas para lo mismo y dos instaladores que pueden divergir | Raúl, y que el plugin esté publicado |
| T6 | Lo que deja la 26.9.15 en el plugin. **Hecho (11 y 12-nov):** los tipos de informes de tareas, de Tempo y de traducciones en la política del extractor. `addPackageObjects` en el doc 08, con el esquema nuevo leído y sin ejercitar. `testCases` de `createExpressionRule`, ejercitado al crear las dos reglas del banco: una regla con entradas exige dos casos, uno con todo vacío y otro con valores, y quedan como «Test Case 1» y «Test Case 2» sin salida esperada; los casos con salida esperada se crean después. **Falta:** que el modelo del extractor cuente los casos de prueba de una regla (hoy los lee y no los cuenta) y las nueve observaciones de conducta del doc 14, que hay que probar en Appian | La rama del método, que toca el extractor y esos documentos |

## Lo que no se hace

- **Generar skills a partir del bundle.** Lo que hay que entender lo hace la IA; el script instala, compara y prueba.
- **Depender de `sail` o del Dev MCP en la batería de GitHub.**
- **Fijar en el plugin aplicaciones, sites, entornos o cuentas.**
- **Probar en una aplicación de proyecto.**
- **`sail preview` en el QA**: solo funciona en servidores de rama `appian-dev`.
- **Fijar el plugin a una versión de Appian.** La versión verificada avisa, no impide.

## Límites

- Una herramienta que cambia de conducta sin cambiar de esquema ni de descripción solo la ve el banco, y solo si el
  banco la ejercita.
- Un resultado en un entorno no vale para otro con otra versión del plugin de Appian.
- El `sail` anterior solo existe si la actualización se hizo con la skill.
- La guía oficial no dice cómo actualizar, solo cómo instalar: borrar el código anterior antes de extraer es decisión
  de este diseño.
- Las URL de docs.appian.com con versión fija siguen con `comprobar_anclas.py` antes de publicar.
