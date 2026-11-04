# Pendiente

La única lista de lo que falta, en el orden en que se hace: un paso cada vez, y cada punto con su commit y su prueba.
Lo hecho, con sus pruebas y límites, pasa a [evaluaciones.md](evaluaciones.md). Cada punto dice a quién toca. Esta
lista no autoriza publicar, desplegar, enviar ni borrar.

**Ahora:** del paso 3, llevar las dos reglas que P7 quinquies no vio adonde las lee quien aplica, y medirlo en P7
sexies (`Pruebas-plugin/paso3-20261103/PRUEBA-ter.md`). Después, con Raúl en persona, P3 en una sesión atendida, P8 y
P9 (`PRUEBA.md`). Lo demás del paso 3 está hecho (`evaluaciones.md`). Después, el paso 4.

## 1. En la rama actual, por orden

### Paso 3 · Prueba con el plugin cargado desde la carpeta

Hecho el 4-nov en sesiones en segundo plano que arrancó Claude con `claude --bg --plugin-dir`, aceptadas por el
clasificador del modo auto (`evaluaciones.md`, «Paso 3 con el plugin cargado»). Falta:

- **Las rectificaciones con fuentes agrupadas, y el Word de las otras unidades.** La regla de `9d044d4` («Varias
  fuentes juntas»: la rectificación lleva su fila D, a mano si `version --decision` le pondría la primera fuente) no
  pasó en conducta. P7 quinquies aplicó en un informe conjunto, pero sin esas filas: el agente leyó `actualizacion.md`
  hasta la línea 250, el párrafo está en la 295, y la tabla de §3, que sí leyó, dice NUEVO → sin fila D. En la misma
  pasada no regeneró el Word de EV-02, Construida y con Word. La regla está en §7 y en `cambios.md` §5, que no leyó, y
  el paso 8 del `SKILL.md` no nombra los vigentes. Falta llevar la rectificación a §3 (casos frontera) y a la fila D
  de §6, y los Word vigentes al paso 8 del `SKILL.md`. Sin script, opción ni control nuevos: ver una rectificación
  entre fuentes es entender, no comparar. Después, medirlo en P7 sexies, un montaje nuevo con la receta de P7
  quinquies. P7 quater, con Raúl aprobando en persona, queda como alternativa. Aparte, el selftest completo sobre el
  árbol de `9d044d4`, adicional porque `CLAUDE.md` no lo pide para un cambio en una referencia, quedó interrumpido por
  falta de memoria (437 bien y 0 mal, sin terminar): no cuenta como verde. [flujo]
- **P3 en una sesión atendida.** Marcar Construida con `--manual` lo decide una persona y está prohibido en una
  desatendida. La primera ejecución lo hizo por un error del guion y no cuenta. [persona]
- **P8, una autorización que llega por otra sesión.** Raúl abre la sesión con su delegación en el primer mensaje.
  [persona]
- **P9, Write y Edit en `claude --bg`.** Raúl aprueba `--confiar` y lanza él la sesión en segundo plano. Dato de la
  primera ejecución: el bloqueo de Edit en repositorios git es el aislamiento de las sesiones en segundo plano del host,
  una salvaguarda. No se rodea ni se desactiva desde el plugin: la prueba documenta el límite y las vías que admite el
  host. [persona]

### Paso 4 · Residuos de las pruebas

Va después del paso 3: IFA e IFB sirven para probar el 2.6. Raúl autoriza (3-nov) borrar lo que ya no haga falta, sin
perder contexto útil: lo que pueda servir pasa a estos dos documentos, sin datos del cliente; la evidencia que todavía
citan se conserva, no solo su resumen, y se le enseña la lista exacta de lo que se borra.

- En `Pruebas-plugin`, revisar `automejora/`, `automejora-codex-20261019/`, `campana-codex-20261019/`,
  `aplazados-codex-20261019/`, `construccion-cerebro/`, `informes-comparativa-20261022/`, `informes-con-plugin/`,
  `informes-sin-plugin/`, `T1-agilidad/`, `T5-devmcp-sail/`, `T6-retoque-construido/`, `T13-pruebas-issue/`, `T15-qa/`,
  `T16-ensayo-qa/` y `retoque-analisis/`. Primero las que guardan fuentes reales del cliente
  (`campana-codex-20261019/`, `informes-con-plugin/`). Antes de borrar
  cada una, comprobar que sus lecciones estén aquí o en `evaluaciones.md`, si la cita como evidencia algún documento
  que se conserva (el seguimiento del ensayo, la revisión de Codex) y qué objetos dejó en Indra-spain
  (`T6-retoque-construido/objetos-creados.md`). Se guarda lo que haga falta, como los ocho casos de
  `aplazados-codex-20261019/mnt-evaluacion-ciega/revision-ciega.md`, que cita §3; lo demás, y sobre todo lo que lleve
  datos del cliente, se borra con esa lista; si la sesión no puede, lo lanza Raúl. [sesión]
- En Indra-spain, las consultas de solo lectura del 3-nov no encontraron las aplicaciones PCA y CTC, las tablas `CTC_*`
  ni los grupos CTC (no prueba que no existan con otros permisos). Siguen
  las aplicaciones IFA e IFB del ensayo con sus datos, y dos instancias activas de `IFA Revisar Fechas Limite` desde el
  24-oct, que se repiten cada día y envían correo; solo las cancela una persona. La de IFB no se puede leer (403). Las
  dos instancias las cancela Raúl; lo demás entra en la lista. [persona y sesión]
- De la prueba del 2.6 y del paso 3: en Indra-spain, dos borradores de paquete de IFA, el de la prueba del 2.6
  («PRUEBA 2.6 EV-03 (borrar)», `2478033f…`, con su script), anterior al paso 3, y el del paso 3 («PRUEBA PASO 3
  EV-02 (borrar)», `90918f3c…`); los dos, en `paso3-20261103/objetos-creados.md`. En `Pruebas-plugin/paso3-20261103/`,
  los proyectos y remotos de prueba; fuera, la copia temporal de Codex
  (`C:\Users\rgmoya\AppData\Local\Temp\codex-factibilidad-d-zuj_i2bw`). Se conserva lo que sostiene el registro:
  la evidencia que citan, directa o indirectamente, `evaluaciones.md` y `resultados.md` (artefactos y
  transcripciones incluidos), y lo que necesita esta limpieza (`objetos-creados.md`, con los UUID). [sesión]
- En el repositorio, las galerías HTML de `appian-prototipos/galerias/` (1,8 MB, no las cita nadie y se regeneran con
  `generar_app.py` y `build.py`): entran en la lista. [sesión]

### Paso 5 · Cierre de la rama

- **Cierre.** Se sigue en esta única rama y se integra con `main` cuando todo esté probado y validado (Raúl, 3-nov).
  Antes del PR, poner al día «Trabajo en curso» de `CLAUDE.local.md`. La batería completa pasa en GitHub. Antes de
  publicar una versión, las siete combinaciones y `pruebas/comprobar_anclas.py` (con
  red). [persona y sesión]
- **Copia de seguridad.** La rama no está en GitHub; se sube como copia, sin PR, cuando Raúl lo autorice. [persona]

## 2. Cuando se dé su condición

- **Índice del DOCX.** Evaluar la caché editable solo si una entrega la necesita. [Word]
- **Coste de agrupar fuentes del mismo tema (2.2).** Medido una vez en el paso 3 (`evaluaciones.md`): es uso
  observado, no coste, y un solo par; tampoco quedó acreditada una calidad equivalente. No se cambia el método. Si se
  vuelve a plantear, medir el coste en un incremento real con fuentes del mismo tema, sin deducir ahorro del número
  de llamadas. [flujo]
- **Dimensiones de QA sin medir:** visual y accesibilidad, roles con cuenta, autorización de servidor, vigencia causal,
  atomicidad y concurrencia. Solo las que necesite la entrega; no crear cuentas ni escribir datos por esta lista. El
  contraste automático de texto sobre fondo compuesto, si un caso visible lo pide. [pruebas]
- **LEEME completo y deriva interna** de una aplicación real: siguen sin medir. La extracción masiva sigue detenida y
  `getAgent`, aparcado tras el aviso a Appian. Al reanudarla, decidir si reconoce el parámetro `object` de
  `getObjectDependents` o se queda con el grafo actual (límite en `evaluaciones.md`).
- **Próximo proyecto grande real.** Contar las historias duplicadas entre módulos (P3: 4-6 % de 78) y comprobar que
  una contradicción de alcance llega a su PC con las dos posturas citadas (T5). Se quedan como texto hasta entonces.
  [prueba]
- **Seguridad de acciones de registro con constante.** Diez acciones no salían a nadie (una vez, sin causa
  demostrada). Contrastarlo escribe en Indra-spain: solo si Raúl lo autoriza; hasta entonces, sin regla. [prueba]
- **Diagramas.** Reducir los 30/38 avisos residuales solo con una mejora medida, sin relajar detectores.
- **Un literal propuesto, bajo ✅.** En P7 («juntas») y en P7 quinquies, el texto del aviso «Indica el centro de
  coste», que ninguna fuente da, quedó en HU-06.2 con ✅ y la fuente del correo. La entrega lo declaraba propuesto, y
  lo que propone el analista va con 🔶. Es el mismo caso ficticio dos veces. Revisarlo si aparece en otra prueba o en
  un proyecto real; `comprobar.py` no lo puede ver. [flujo]
- **URL `/help/26.6/`** de `data-fabric.md` y `agents/data-modeler.md`: revisarlas cuando cambie la versión de Appian
  del entorno.
- **Aviso a Appian** (`aviso-appian-devmcp.md`, en la carpeta de pruebas): revisarlo con el servidor 26.9.5, porque el
  punto 10 ya está en parte corregido. Añadir la discrepancia de `LCP_TOOL_MODE=readonly` y lo visto en el ensayo: cada
  copia del servidor borra el `cookies.json` compartido al caducar su sesión (hay un parche local que cada bundle pisa),
  `listProcessInstances` omite instancias y su «total» cambia, no hay forma de cancelar instancias, el rechazo del MCP
  por «builds distintas» a mitad de un trabajo y el caso que crea `testInputs`. Y, del 2.6 (26.9.5), un caso
  observado: en `addPackageObjects`, un lote con una entrada de tipo cambiado devolvió como inexistentes («Could not
  resolve the object's type… may not exist») también las reglas, constantes e interfaces válidas, que sin ella
  entraron. Lo envía Raúl. [persona]
- **Rama `yaroslav/plantilla-DF-cliente`** en GitHub, solo si Raúl lo pide: 17 commits del 19-oct sin PR, ni en
  `main` ni en esta rama; es independiente de ella. [persona]
- **Tarea no prioritaria**, solo cuando Raúl lo pida: renombrar el plugin a «Appian Software Factory» en todos los
  sitios (GitHub, carpeta local, `plugin.json`, el prefijo de las skills, README, gráficos y `CLAUDE.md`).

## 3. Campañas posteriores al trabajo actual

Se empiezan después de terminar las tareas actuales, por indicación de Raúl del 3 de noviembre.

- **Revisión de la versión 26.10.** Contrastar las versiones del entorno Appian y del bundle Dev MCP, la documentación
  nueva, las herramientas y la skill oficial. Actualizar el comportamiento del plugin con las capacidades nuevas
  que procedan, retirar indicaciones obsoletas o deprecadas y comprobar que lo que ya funcionaba sigue funcionando.
  Comprobar ahí si el bundle configura ya el inicio programado de un proceso (mientras, rige L3: lo hace una persona,
  sin un bucle de temporizador como sustituto) y volver a contrastar el botón «Limpiar» tras uno que valida, que dejó
  «A value is required» aunque llevara `validationGroup` (laboratorio de la campaña de Codex).
- **Desplegar con el MCP de despliegue de Appian.** Raúl, 3-nov: puede ser la siguiente integración, tras el 2.6, para
  desplegar en el siguiente entorno con la autorización de una persona. Es una integración posterior: probar paquetes en
  desarrollo no autoriza desplegar en otro entorno. Según su página
  (`https://docs.appian.com/suite/help/26.10/mcp-deployment.html`, leída el 3-nov; nombres documentados, sin esquemas
  ni prueba): utilidad del App Market mantenida por la comunidad, sin soporte de Appian, sobre la API de despliegue;
  exporta, inspecciona y despliega paquetes con su ICF, scripts de base de datos y plug-ins (`deploy_package`,
  `export_and_deploy`) y encadena entornos en pipelines con etapas que se aprueban (`run_pipeline`,
  `run_adhoc_pipeline`, `approve_pipeline_stage`). Pide activar los despliegues externos en cada entorno (Admin
  Console) y la clave o el token de una cuenta de servicio, nunca en el repositorio (la página propone el llavero del
  sistema). Quitarle a la IA la herramienta de aprobar no basta, porque tiene vías directas de despliegue: hay que
  comprobar los permisos reales y el gobierno de cada entorno, y no está probado que aprobar una etapa sustituya la
  revisión de Appian («Require review», con quien pide y quien revisa distintos:
  `https://docs.appian.com/suite/help/26.10/deployments-view.html#review-deployment-requests`). Cancelar un pipeline
  detiene las promociones siguientes, no un despliegue ya empezado. Hace falta un entorno de destino además de
  Indra-spain. [F9]
- **Todas las entradas del plugin.** Inventariar y probar las entradas y variantes documentadas en el README, los
  flujos y los modos de cada skill, tanto su invocación directa como su uso dentro de un flujo.
- **Ingeniería inversa y refactorización a fondo.** Probar extracción, continuación, deriva, dependencias,
  planificación y verificación de las refactorizaciones, incluidos errores y recuperación. Comprobar la conservación
  del comportamiento y la documentación resultante, y corregir los márgenes de mejora encontrados. Usar como casos de
  evaluación los ocho de `aplazados-codex-20261019/mnt-evaluacion-ciega/revision-ciega.md` (recordatorio repetido entre
  ejecuciones, selector con límite o inactivos, usuario fijo…): el puntuador de entonces no los veía.
- **Agentes y skills, por separado y juntos.** Evaluar qué recibe, decide y entrega cada uno; después, comprobar sus
  relaciones y traspasos dentro del flujo completo, su calidad, fricción y coste. Repetir los casos afectados tras
  las correcciones y recoger las conclusiones en este seguimiento y en `evaluaciones.md`. Caso para `pdf-publisher`:
  una vez remitió cuatro procesos a la misma página («ver página N» sin comprobar el destino).
