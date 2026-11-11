# Pendiente

La única lista de lo que falta, en el orden en que se hace: un paso cada vez, y cada punto con su commit y su prueba.
Lo hecho, con sus pruebas y límites, pasa a [evaluaciones.md](evaluaciones.md). Cada punto dice a quién toca. Esta
lista no autoriza publicar, desplegar, enviar ni borrar.

**Ahora:** ningún trabajo en curso. El 5-nov se publicó la 0.8.0-beta.3 con lo que había en `main` (`evaluaciones.md`, «Entrega 0.8.0-beta.3»); los 54 commits de `claude/pruebas-metodo-20261104`, sin PR ese día, quedan para la siguiente. Queda lo de §1; lo siguiente, cuando Raúl lo pida, §2 y §3, cada trabajo en su rama (`CLAUDE.md`).

## 1. Del trabajo anterior

### Paso 4 · Residuos de las pruebas

Raúl autorizó (3-nov) borrar lo que ya no haga falta, sin perder contexto útil, y el 4-nov delegó en Claude decidir qué
puede servir y qué se borra. La evidencia que citan, directa o indirectamente, este documento, `evaluaciones.md`, la
memoria y los informes que se conservan se queda, no solo su resumen. Por eso se conservan las carpetas de
`Pruebas-plugin`, con los datos de clientes que guardan (decisión prudente, `evaluaciones.md`, «Paso 4»); las
aplicaciones IFA e IFB de Indra-spain, que sostienen el ensayo y P6 del paso 3; la aplicación DEM, la de pruebas del
método con datos ficticios; y las galerías HTML de `appian-prototipos/galerias/`. Retirar sus seis salidas generadas
(HTML y trazabilidad) queda como opción de Raúl, sabiendo que hay que construirlas antes de navegarlas. Las lecciones
útiles de esas pruebas tienen destino aquí o en `evaluaciones.md`; las que lo tenían pendiente, abajo y en §2. Falta:

- **Las tablas `DVG_CATEGORIA` y `DVG_SOLICITUD`** de `jdbc/Appian` (prueba de divergencias, sin valor): las quita una
  persona con acceso a la base de datos. [persona]
- **Residuos de la campaña de Codex en Indra-spain**, pendientes de decisión: la aplicación CML, las reglas `DEM_C26_*`
  y `DEM_E20_*`, las interfaces de laboratorio, las versiones v13 a v15 de `DEM_Dashboard` y las cuentas de QA `dem.*`.
  Sus listas están en las carpetas de la campaña, que se conservan (`paso3-20261103/inventario-paso4.json` las resume).
  Orden seguro: antes, decidir cómo dejar `DEM_Dashboard`, porque la v15 depende de `DEM_E20_EnsayoCantidad` y de
  `CML_CatalogoLaboratorio`, y volver a la v12 deshace el cambio de T3 en EV-02. [persona y sesión]
- **La vigencia de las decisiones anteriores (L12 del ensayo, `SEGUIMIENTO.md`).** Cuando una D nueva cambia otra, en
  todo o en parte, `actualizacion.md` §6 no dice que se revise la columna «Vigente» de la anterior: «No» si queda
  sustituida y «En parte» si conserva cláusulas, con la D nueva. `proyecto.py` escribe siempre «Sí», y `modelo.py` ya
  admite «En parte». Corrección mínima propuesta por Codex: una frase en la fila D de §6, con el juicio del LLM, sin
  script ni paso nuevo. Cambia la conducta de la skill: con su prueba con el plugin cargado. [flujo]

## 2. Cuando se dé su condición

- **Publicar una versión.** Antes, las siete combinaciones de sistema y Python (Actions → Pruebas → Run workflow) y
  `pruebas/comprobar_anclas.py`, con red; la versión, en `.claude-plugin/plugin.json` y en la primera fila de
  versiones del README. [persona y sesión]
- **Índice del DOCX.** Evaluar la caché editable solo si una entrega la necesita. [Word]
- **Coste de agrupar fuentes del mismo tema (2.2).** Medido una vez en el paso 3 (`evaluaciones.md`): es uso
  observado, no coste, y un solo par; tampoco quedó acreditada una calidad equivalente. No se cambia el método. Si se
  vuelve a plantear, medir el coste en un incremento real con fuentes del mismo tema, sin deducir ahorro del número
  de llamadas. [flujo]
- **Dimensiones de QA sin medir:** visual y accesibilidad, roles con cuenta, autorización de servidor, vigencia causal,
  atomicidad y concurrencia. Solo las que necesite la entrega; no crear cuentas ni escribir datos por esta lista. El
  contraste automático de texto sobre fondo compuesto, si un caso visible lo pide. En T16, Playwright mostró una
  descripción técnica interna como nombre accesible de una acción (`T16-ensayo-qa/medicion/D-transcripcion.jsonl`,
  líneas 177 y 247). No se pasó un lector de pantalla: esa parte sigue sin medir. [pruebas]
- **Dos observaciones de IFB sin contrastar** (`informes-sin-plugin/ESTADO.md`, «Aprendido»). En un Script Task, los
  `customOutputs` se evalúan con los valores previos al nodo, así que uno que dependa de otro va en otro nodo. Y
  `a!fromJson` devolvió un escalar con un JSON de un elemento, que hizo fallar un filtro `in`. Lo demás de esa lista ya
  lo cubre la skill oficial. Se contrastan cuando una tarea los use; hasta entonces, sin regla. [prueba]
- **LEEME completo y deriva interna** de una aplicación real: siguen sin medir. La extracción masiva sigue detenida y
  `getAgent`, aparcado tras el aviso a Appian. Al reanudarla, decidir si reconoce el parámetro `object` de
  `getObjectDependents` o se queda con el grafo actual (límite en `evaluaciones.md`).
- **Próximo proyecto grande real.** Contar las historias duplicadas entre módulos (P3: 4-6 % de 78) y comprobar que
  una contradicción de alcance llega a su PC con las dos posturas citadas (T5). Se quedan como texto hasta entonces.
  [prueba]
- **Seguridad de acciones de registro con constante.** Diez acciones no salían a nadie (una vez, sin causa
  demostrada). Contrastarlo escribe en Indra-spain: solo si Raúl lo autoriza; hasta entonces, sin regla. [prueba]
- **Diagramas.** Reducir los 30/38 avisos residuales solo con una mejora medida, sin relajar detectores.
- **Diagramas: órdenes que faltan** (auditoría del 10-nov): pestañas por fase nativas (`pagina`), `importar` un
  `.vsdx`, `comparar --con` una referencia, campos `ref` y `supuesto`, carriles por sistema y un PNG por pestaña. El
  SKILL.md ya explica cómo hacerlo a mano mientras tanto. [diagramas]
- **Un literal propuesto, bajo ✅.** En P7 («juntas») y en P7 quinquies, el texto del aviso «Indica el centro de
  coste», que ninguna fuente da, quedó en HU-06.2 con ✅ y la fuente del correo. La entrega lo declaraba propuesto, y
  lo que propone el analista va con 🔶. Es el mismo caso ficticio tres veces (también en P7 sexies). En P7 septies el
  aviso fue con 🔶, pero otra deducción suya quedó bajo ✅ («la columna queda vacía si no lo tiene», en HU-04.3).
  Revisarlo si aparece en otra prueba o en un proyecto real; `comprobar.py` no lo puede ver. [flujo]
- **Sesiones en segundo plano y aislamiento.** La vía del host (`EnterWorktree`) deja los cambios en una rama propia
  que la sesión nunca fusiona: los integra la persona, por PR o a mano (documentación oficial, agent-view y worktrees).
  Con «sobre `main`, sin ramas ni PR» no encaja sin decidir cómo integrarlos. Quitar el aislamiento
  (`worktree.bgIsolation: none`) lo decide Raúl por proyecto; el 4-nov, solo en la copia de prueba de P9 y con un solo
  escritor (P9 bis). Si quiere usar sesiones en segundo plano en proyectos reales, decide él cuál de las dos y con qué
  límites. Aparte, en P9 ter la sesión, tras fallar `EnterWorktree`, siguió con órdenes del plugin que escriben en la
  copia compartida y dejó el proyecto a medias, aunque lo dijo. Si eso molesta, adelantar la frase de `AGENTS.md` al
  fallo del aislamiento. [persona]
- **Otras novedades, sin consumidor todavía** (señaladas por Codex): de Appian 26.10, el ancestro común en el ALM de
  las expression rules; del DevMCP 26.9.10, no de la plataforma, las cinco herramientas de Task Reports y
  `updateBehavior` en las relaciones. Se contrastan y se incorporan cuando una tarea las necesite. El Deployment MCP
  2.0 existe desde el 2-sep: no es de la 26.10. [flujo]
- **Fila D con otra fuente que la que cita.** Un aviso de `comprobar.py` si la «Decisión» de una fila D cita fuentes y
  ninguna es la de su «Fuente» (es comparar, no entender). Solo si, tras el arreglo de `version --decision`, vuelven a
  aparecer filas así escritas a mano. [flujo]
- **URL `/help/26.6/`** de `data-fabric.md` y `agents/data-modeler.md`: revisarlas cuando cambie la versión de Appian
  del entorno.
- **Aviso a Appian** (`aviso-appian-devmcp.md`, en la carpeta de pruebas): revisarlo con el DevMCP 26.9.10 (build
  20261103-144057) y lo comprobado con él (`evaluaciones.md`, «Divergencias con la skill oficial, con el DevMCP
  26.9.10»), separando lo histórico de lo actual. El punto 10 ya estaba en parte corregido. Añadir la discrepancia de
  `LCP_TOOL_MODE=readonly` y lo visto en el ensayo. Cada copia del servidor borra el `cookies.json` compartido al
  caducar su sesión; hay un parche local, y el bundle 26.9.10 tampoco lo corrige. En `listProcessInstances`, el
  `total` sigue mal con el build nuevo (depende de `limit` y `offset`), y la omisión de instancias, vista con builds
  anteriores, no se volvió a medir. Tampoco hay forma de cancelar instancias. Faltan además el rechazo del MCP por
  «builds distintas» a mitad de un trabajo y el caso que crea `testInputs`, que sigue con el build nuevo. Y, del 2.6,
  con su build histórico 26.9.5, un caso observado: en `addPackageObjects`, un lote con una entrada de tipo cambiado
  devolvió como inexistentes («Could not resolve the object's type… may not exist») también las reglas, constantes e
  interfaces válidas, que sin ella entraron. Lo envía Raúl. [persona]
- **Rama `yaroslav/plantilla-DF-cliente`** en GitHub, solo si Raúl lo pide: 17 commits del 19-oct sin PR, ni en
  `main` ni en esta rama; es independiente de ella. [persona]
- **Tarea no prioritaria**, solo cuando Raúl lo pida: renombrar el plugin a «Appian Software Factory» en todos los
  sitios (GitHub, carpeta local, `plugin.json`, el prefijo de las skills, README, gráficos y `CLAUDE.md`).

## 3. Campañas posteriores al trabajo actual

Se empiezan después de terminar las tareas actuales, por indicación de Raúl del 3 de noviembre.

- **Versión 26.10: lo que queda.** El contraste de versiones, bundle, skill oficial, documentación y herramientas, y
  la corrección de lo obsoleto en las buenas prácticas y en las divergencias, se hizo el 4-nov (paso 3 bis;
  `evaluaciones.md`). Queda probar las capacidades en un entorno Appian 26.10 real cuando lo haya. Ahí, mirar si el
  bundle configura ya el inicio programado de un proceso (mientras, rige L3: lo hace una persona, sin un bucle de
  temporizador como sustituto) y volver a contrastar el botón «Limpiar» tras uno que valida, que dejó «A value is
  required» aunque llevara `validationGroup` (laboratorio de la campaña de Codex). Y las novedades sin consumidor de
  §2.
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
- **Prototipos: repertorio hasta Appian 26.10 y elección UX.** Contrastar `appian-prototipos` con el catálogo oficial
  de componentes de interfaz hasta 26.10, detectar los ausentes o con soporte parcial y ampliarlos con ejemplos y
  criterios de cuándo usarlos o evitarlos, para disponer de alternativas usables, accesibles y adaptables. Revisar el
  impacto en catálogo, esquemas, helpers, runtime, plantillas y galerías, y en sus consumidores (capturas y
  documentación), preservando la compatibilidad. Extender las pruebas existentes según lo afectado y probar
  prototipos representativos que combinen elementos actuales y nuevos, sus estados e interacciones. Evaluar también
  con encargos de prototipo que el agente elige componentes adecuados a la necesidad y al contexto de UX, no solo
  que se dibujan; corregir los fallos y repetir los casos afectados. Conclusiones y límites, en este seguimiento y
  en `evaluaciones.md`. [prototipos]
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
