# Pendiente

La única lista de lo que falta, en el orden en que se hace: un paso cada vez, y cada punto con su commit y su prueba.
Lo hecho, con sus pruebas y límites, pasa a [evaluaciones.md](evaluaciones.md). Cada punto dice a quién toca. Esta
lista no autoriza publicar, desplegar, enviar ni borrar.

Cada pendiente explica el problema, qué hay que hacer y el resultado esperado, conservando los acuerdos de la
conversación. Si el detalle ya está bien explicado en otro documento, se enlaza desde el punto en lugar de repetirlo.

**Ahora:** `main` lleva la campaña «el método de punta a punta» (PR #25, 24-nov) y su C4: el QA de EV-01 en verde y la regresión de un cambio aislado medida (`evaluaciones.md`). Para escribir la regla de regresión falta medir un cambio compartido (§2, lo decide Raúl). El trabajo «adaptarse a las actualizaciones de Appian» (rama `raul/estrategia-actualizaciones-appian`) y el PR #24 de diagramas se ponen al día sobre `main`; al unir el primero, se repiten los cinco guiones de FOR que falló la herramienta (§2).

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

- **La aplicación de prueba «FOR Formación Externa»** de Indra-spain y lo que lista `Pruebas-plugin/metodo-20261104/objetos-creados.md`, con el paquete borrador: Raúl la ve antes de borrarla (5-nov). Desde el 7-nov lleva además EV-01 de la campaña «entender y evolucionar» y una fila de prueba (`FOR_SOLICITUD` 338; la 339 ya no estaba el 10-nov) que la sesión no borró (el clasificador del modo automático paró el borrado antes de llegar a Appian): la borra Raúl. Las tablas `FOR_ESTADO`, `FOR_SOLICITUD`, `FOR_CERTIFICADO` y `FOR_MODALIDAD` de `jdbc/Appian` las quita después una persona con acceso a la base de datos. [persona y sesión]
- **Las tablas `DVG_CATEGORIA` y `DVG_SOLICITUD`** de `jdbc/Appian` (prueba de divergencias, sin valor): las quita una
  persona con acceso a la base de datos. [persona]
- **Residuos de la campaña de Codex en Indra-spain**, pendientes de decisión: la aplicación CML, las reglas `DEM_C26_*`
  y `DEM_E20_*`, las interfaces de laboratorio, las versiones v13 a v15 de `DEM_Dashboard` y las cuentas de QA `dem.*`.
  Sus listas están en las carpetas de la campaña, que se conservan (`paso3-20261103/inventario-paso4.json` las resume).
  Orden seguro: antes, decidir cómo dejar `DEM_Dashboard`, porque la v15 depende de `DEM_E20_EnsayoCantidad` y de
  `CML_CatalogoLaboratorio`, y volver a la v12 deshace el cambio de T3 en EV-02. [persona y sesión]

## 2. Cuando se dé su condición

- **Documentación del repositorio antes de integrar en `main` o publicar una versión.** Petición de Raúl, 5-nov:
  incorporar al cierre existente una revisión en ambos momentos para que la documentación del propio plugin (no los DF
  ni los técnicos de las aplicaciones) refleje lo que realmente hace. Dejar claro qué documentos y diagramas revisar
  según los cambios: README, manual o guías de usuario, guías de instalación y contribución, instrucciones, referencias y flujos de las skills, plantillas y ejemplos, documentación
  vigente de `docs/` y gráficos del repositorio. En los diagramas, revisar tanto la fuente editable como sus
  imágenes o exportaciones y los documentos que los incorporan. Contrastar instrucciones, ejemplos, capacidades,
  límites y enlaces con el código y las pruebas; actualizar lo afectado y resolver contradicciones antes de integrar
  o publicar. Resultado esperado: quien consulte el repositorio entiende la versión real que recibe, sin confundir
  propuestas pendientes ni resultados históricos con capacidades actuales. Aprovechar el flujo de cierre existente,
  sin crear una lista paralela ni un informe por cada cambio. [repositorio · persona y sesión]
- **Que cada punto de esta lista se entienda sin la conversación en la que nació.** Petición de Raúl, 17-nov.
  Problema: la cabecera ya pide que cada pendiente explique el problema, qué hay que hacer y el resultado esperado,
  pero quedan puntos de una o dos líneas que no dan contexto para abordarlos sin reconstruir su historia. Por ejemplo,
  «Índice del DOCX», «Diagramas. Reducir los 30/38 avisos residuales…» o «URL `/help/26.6/`…» no dicen de dónde
  salen, qué se midió ni qué falta por decidir. Qué hacer: reforzar la regla de la cabecera para que cada punto diga
  de dónde sale (la prueba o la conversación, la fecha y quién lo pidió), el problema con su evidencia o el enlace a
  ella, qué hay que hacer, lo ya decidido y lo que falta por decidir, el resultado esperado y a quién toca. Después,
  repasar los puntos actuales: completar los que no lo cumplan o enlazar el documento que ya lo explica, y proponer a
  Raúl quitar los que ya nadie sepa explicar. Mirar también si la frase de `CLAUDE.md` que manda apuntar aquí debe
  decirlo. Resultado esperado: una persona o una sesión nueva que abra un punto puede empezar a trabajar en él sin
  preguntar de qué se trataba. [repositorio · sesión]
- **Regresión en un evolutivo: falta medir un cambio compartido.** Decisión de Raúl (7-nov): repetir según el impacto
  real del cambio (presentación, lo afectado; una regla, acción o filtro, sus casos y los escenarios de otros flujos y
  roles que puedan verse afectados; transversal o sin acotar, todo), las pruebas de cada issue al construir y la
  regresión seleccionada en el QA del evolutivo; F9, completa. Antes de escribirlo en F8 y en la skill de QA, comparar
  un cambio aislado y otro compartido, midiendo qué detecta y cuánto tarda (`diseno/regresion-evolutivo.md`, «Lo que
  decidió Raúl»). El aislado ya está medido (C4, `evaluaciones.md`). Falta el compartido: un evolutivo que toque algo
  que usen varios flujos o roles, con la misma versión de SAIL CLI y de `qa.py` antes y después, todas las cuentas con
  sesión y un fallo funcional conocido metido a propósito, para ver qué detecta cada pasada (lo pide la revisión de
  Codex de C4). Qué cambio compartido y en qué aplicación de prueba lo decide Raúl. [flujo · QA · Raúl decide]
- **Un fallo de QA se clasifica antes de reabrir su issue.** En C4, cinco guiones de FOR fallaron porque SAIL CLI
  26.9.15 no deja enviar un formulario con un campo obligatorio vacío o con una validación, justo lo que esos guiones
  provocan para ver el mensaje; `qa.py repetir` devolvió a pendiente ISS-03 e ISS-06 de `formacion` sin que FOR
  tuviera ningún defecto. La rama `raul/estrategia-actualizaciones-appian` ya trae `RX_NO_ENVIADO` en `qa.py` para
  leer ese rechazo; al unirla, repetir esos cinco guiones (HU-01.2, 01.3, 01.4, 01.6 y 06.2) y comprobar que el
  motivo lleva el mensaje esperado (el de HU-01.2 y HU-06.2 solo dice «required, and empty»). Resultado esperado: un
  cambio de la herramienta no reabre issues que no tienen defecto. [QA · con la rama de actualizaciones]
- **Renovar las sesiones de SAIL de las cuentas de prueba sin improvisar.** En la campaña tres sesiones dejaron de
  valer y el QA se paró a la espera de la persona. `qa.py sesiones` da por buena una sesión caducada (solo mira que
  exista su fichero) y el fallo se ve a mitad de `repetir`; la orden que da `como_entrar` no se teclea tal cual en
  PowerShell, y en bash deja la contraseña en el historial; nada dice que la IA no puede entrar con las cuentas de rol,
  porque no tiene sus contraseñas (la cuenta propia sí, con `--from-devmcp`). Propuesta, sin aprobar: `qa.py entrar
  <host> <cuentas>`, que ejecuta la persona en su terminal (pide cada contraseña oculta, la pasa solo al entorno de
  `sail login` y se niega si no hay terminal), y que `qa.py repetir` compruebe antes de empezar con `sail pages <site>`,
  que no cambia nada (medido el 7 y el 10-nov: viva, 0; caducada, 1 con 401; sin acceso al site, sin medir).
  Resultado esperado: una sesión que no vale se ve antes de empezar y se renueva con una orden, sin que la contraseña
  pase por la IA ni por el historial. Hechos de la prueba: por qué caducaron no se sabe (`dem.gestor2` aguantó tres
  días sin uso); con una cuenta creada por `createUser` con `temporaryPassword: true`, `sail login` falla (Appian redirige a
  `setpassword`; una medida, sin probar después del cambio); el paquete 26.9.15 no trae `lcp-login` (visto en el
  disco; el login de `sail` por navegador no se ha probado con esta versión). Toca la misma skill que T3 del diseño de actualizaciones: se hace con él o antes, no dos veces.
  [QA · Raúl decide]
- **Publicar una versión.** Antes, las siete combinaciones de sistema y Python (Actions → Pruebas → Run workflow) y
  `pruebas/comprobar_anclas.py`, con red (pasado el 6-nov con la documentación ya en 26.10: 0 rotas); la versión, en `.claude-plugin/plugin.json` y en la primera fila de
  versiones del README. [persona y sesión]
- **Índice del DOCX.** Evaluar la caché editable solo si una entrega la necesita. [Word]
- **Huella de una issue y retrabajo.** Mientras la unidad está Aprobada, un paso manual del técnico que nombra objetos
  sigue caducando su verificación (E5-4), y una aclaración del técnico que entra en la issue también (V6c). Mejora
  posible, de Codex: que la huella compare las DT por su Decisión y Verificar y las líneas ya limpias, para que un
  cambio en el Riesgo de una DT o en un comentario no la caduque. Valorarlo con más casos. [flujo]
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
  `getAgent`, aparcado. Al reanudarla, decidir si reconoce el parámetro `object` de
  `getObjectDependents` o se queda con el grafo actual (límite en `evaluaciones.md`).
- **Próximo proyecto grande real.** Contar las historias duplicadas entre módulos (P3: 4-6 % de 78) y comprobar que
  una contradicción de alcance llega a su PC con las dos posturas citadas (T5). Se quedan como texto hasta entonces.
  [prueba]
- **Seguridad de acciones de registro con constante.** Diez acciones no salían a nadie (una vez, sin causa
  demostrada). Contrastarlo escribe en Indra-spain: solo si Raúl lo autoriza; hasta entonces, sin regla. [prueba]
- **Diagramas.** Reducir los 30/38 avisos residuales solo con una mejora medida, sin relajar detectores.
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
  `updateBehavior` en las relaciones; del DevMCP 26.9.20, el catálogo de comprobaciones de `validateDesignObjects`
  (`readout=true`), los grupos de páginas y el ancho de página en `createSite`/`updateSite` (probados el 17-nov) y,
  solo en el SDK del bundle y sin herramienta todavía, editar AI skills y leer tipos de datos. Se contrastan y se
  incorporan cuando una tarea las necesite. El Deployment MCP 2.0 existe desde el 2-sep: no es de la 26.10. [flujo]
- **Fila D con otra fuente que la que cita.** Un aviso de `comprobar.py` si la «Decisión» de una fila D cita fuentes y
  ninguna es la de su «Fuente» (es comparar, no entender). Solo si, tras el arreglo de `version --decision`, vuelven a
  aparecer filas así escritas a mano. [flujo]
- **URL `/help/26.6/`** de `data-fabric.md` y `agents/data-modeler.md`: revisarlas cuando cambie la versión de Appian
  del entorno.
- **Rama `yaroslav/plantilla-DF-cliente`** en GitHub, solo si Raúl lo pide: 17 commits del 19-oct sin PR, ni en
  `main` ni en esta rama; es independiente de ella. [persona]
- **Tarea no prioritaria**, solo cuando Raúl lo pida: renombrar el plugin a «Appian Software Factory» en todos los
  sitios (GitHub, carpeta local, `plugin.json`, el prefijo de las skills, README, gráficos y `CLAUDE.md`).

Los cinco puntos siguientes salen de probar el DevMCP 26.9.20 (build 20261116-162817) en Indra-spain el 17-nov, con
una aplicación de prueba ya borrada, y de leer sus release notes. Las pruebas, las respuestas literales y el
contraste con las release notes están en `Pruebas-plugin/actualizaciones-devmcp/20261117-26.9.15-a-26.9.20/novedades.md`.

- **El catálogo de comprobaciones no dice qué impide guardar.** Problema: `validateDesignObjects` con `readout=true`
  devuelve las comprobaciones de calidad del Dev MCP (más de cien) con un campo `enforcement` que dice que las BLOCK
  rechazan el guardado. En la prueba solo lo hizo `noTerminatingEndEvent` (un fin de proceso que no termina el
  proceso: 400 «Quality check failed»). Se guardaron sin error objetos con otras cinco claves BLOCK: `unusedRuleInput`,
  `duplicateRoleMapEntryWarning`, `individualUserDetectedWarning`, `noAdminGroupWarning` y `missing-description`. La
  tentación sería usar el catálogo para quitar de las puertas de calidad lo que «ya garantiza el Dev MCP»; con estos
  datos no se puede. Además, algunas comprobaciones (el prefijo del nombre, los grupos de la aplicación) solo salen al
  validar la aplicación o el paquete, no el objeto suelto. Qué hacer: en `10-quality-gates.md`, junto a la llamada a
  `validateDesignObjects`, decir que el catálogo dice qué se comprueba y no qué impide guardar, que un objeto guardado
  puede tener hallazgos de `lint`, y que al cerrar una unidad se valida también la aplicación o el paquete. Quitar de
  las puertas solo lo que se haya visto rechazar al guardar. Resultado esperado: nadie da un objeto por bueno porque se
  guardó ni recorta las puertas mirando el catálogo. [buenas prácticas]
- **Fila 13 de las divergencias (`duplicateRoleMapEntryWarning`): la causa ya está probada.** Problema: toda regla,
  interfaz y constante que el Dev MCP crea con `appUuid` sale con el aviso «Duplicate entries detected», también en
  una aplicación recién creada. La fila lo atribuye a que el objeto lleva los grupos de la aplicación además de los que
  hereda de su carpeta, pero dice que es una deducción sin probar. El 17-nov se probó: al quitar los grupos propios del
  objeto (roles vacíos y `inheritSecurity: true`, así que solo hereda de la carpeta), o al dejarlos y quitar la herencia
  (`inheritSecurity: false`), el aviso desaparece, también al validar la aplicación entera. Qué hacer: en la fila 13 de
  `14-official-skill-divergences.md`, cambiar la deducción por lo probado y dar las dos salidas, sin convertirlas en un
  paso obligatorio de cada creación: el aviso es MEDIUM y no impide guardar, y la fila ya pide revisar que los grupos y
  roles coincidan con el diseño. Resultado esperado: quien construye sabe de dónde sale el aviso, no lo toma por un
  fallo suyo y sabe quitarlo si el proyecto lo pide. [buenas prácticas]
- **Fila nueva en las divergencias: mover una página de un site entre un grupo y el primer nivel.** Problema: con
  `updateSite`, mover una página existente (con su `uuid`) fuera de un grupo o dentro de él da HTTP 500 en los dos
  sentidos («Batch update returned unexpected row count…» y «deleted object would be re-saved by cascade…»), y el
  site no cambia. Lo que funciona es quitarla y añadirla como página nueva, sin `uuid`. Entonces la página cambia de
  UUID y de dirección (`kI1hGw` → `v-OAoA`), así que los enlaces guardados a ella dejan de valer. La skill oficial no
  trata los grupos de páginas, y el doc 09 §2.6 ya avisa de que en Designer moverla también es borrarla y crearla. Qué
  hacer: una fila en §3 de `14-official-skill-divergences.md` con el síntoma, la salida y la consecuencia para los
  enlaces. Resultado esperado: quien reorganiza la navegación de un site la mueve sin reintentar el error y avisa
  antes de que cambie la dirección. [buenas prácticas]
- **Ingeniería inversa: contar las páginas que hay dentro de los grupos de un site.** Problema: con el DevMCP 26.9.20,
  `getSite` devuelve un grupo de páginas como una entrada con `kind: GROUP` y sus páginas dentro, en `pages`.
  `build_model.py` (rama `site`, `pageCount`) cuenta solo el primer nivel, así que un grupo de dos páginas cuenta como
  una y no cuenta las que lleva dentro. No se sabe cómo devolvía la 26.9.15 un site con grupos. Qué hacer: contar
  también las páginas de cada grupo (y cuántos grupos hay), mirar si otro script de la skill recorre las páginas de un
  site, y añadir el caso a `pruebas/appian-reverse-engineering`. Resultado esperado: el inventario y la documentación
  de una aplicación cuentan y nombran todas las páginas de sus sites. [ingeniería inversa]
- **Evolutivos: ¿un objeto que ya incumple una comprobación que bloquea rechaza cualquier cambio?** De dónde sale: las
  release notes de la 26.9.20 dicen que editar un nodo de proceso, o una vista, acción, filtro, campo, relación o fuente
  de un record type, pasa ahora las mismas comprobaciones de calidad que crear el objeto; Raúl pidió apuntarlo el
  17-nov. Problema: lo comprobado es que un cambio que introduce un fallo se rechaza (quitar el «terminar proceso» del
  fin: 400 «Quality check failed»). No se sabe si un objeto que ya traía un fallo marcado BLOCK, porque se hizo en
  Designer o antes de esta versión, rechaza también un cambio que no tiene nada que ver con ese fallo. Es el caso de
  las aplicaciones reales de un evolutivo, y de FOR, cuyos record types ya llevan `unrecognizedFieldReference` (BLOCK
  en el catálogo; fila 11 de las divergencias). La 26.9.15 tuvo un fallo de esta forma: `updateProcessModel`
  rechazaba todo modelo hecho en Designer. Si pasa, un evolutivo se para en el primer cambio sin que el error apunte a
  lo que se quería cambiar. Qué hacer: probarlo en una aplicación de usar y tirar de Indra-spain, nunca en FOR, IFA,
  IFB, DEM ni BPS. Primero, un modelo de proceso que una persona hace en Designer con un fallo común en modelos
  antiguos, una pasarela XOR con flujos sin etiqueta (`unlabeledGatewayFlow`, BLOCK); después, la sesión cambia por
  MCP algo que no toca la pasarela (el nombre de otro nodo con `updateProcessModelNode` y la descripción con
  `updateProcessModel`). Lo mismo con un record type que lleve un hallazgo BLOCK, añadiéndole una vista o un filtro.
  Falta por decidir: qué hacer si se rechaza (arreglar antes el fallo previo dentro de la issue, o dejarlo a una
  persona en Designer) y dónde se dice (una fila de las divergencias y el flujo de evolutivos de
  `appian-best-practices`). Resultado esperado: antes del siguiente evolutivo se sabe si los objetos antiguos con
  fallos admiten cambios por MCP y qué hacer cuando no. Cuándo: al preparar el siguiente evolutivo sobre una aplicación
  existente, o antes si un cambio en FOR falla así. [prueba · persona en Designer · buenas prácticas]

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
- **Solución técnica y diseño de arquitectura.** Revisar su generación y definir un agente arquitecto experto en
  diseñar soluciones Appian (petición de Raúl, 5-nov; ampliada el 7-nov). Primero analiza las necesidades, el alcance
  y las restricciones reales del proyecto y dedica el tiempo necesario a plantear la solución. Ajusta la
  complejidad y el detalle a esas necesidades, evitando siempre la sobreingeniería.
  Apoyar al agente en el material oficial vigente de Appian, sus buenas prácticas, patrones de diseño y
  recomendaciones para aplicaciones eficientes, robustas y escalables, incluida la gestión de versiones. Ante
  dudas técnicas, consulta el MCP de documentación de Appian. Justificar las decisiones y alternativas relevantes.
  Cuando esté disponible el cerebro corporativo (punto siguiente), usar su contexto funcional y técnico de la
  empresa y sus proyectos: directrices de arquitectura, componentes reutilizables, integraciones existentes,
  capas ya construidas, formatos y convenciones, para que la solución encaje con lo que existe.
  Definir cómo debe ser el diseño técnico como entregable Word profesional, visual y comprensible para su revisión
  y validación por un arquitecto o equipo técnico humano. Incluir los gráficos de arquitectura de la solución y
  sus integraciones con otras aplicaciones o sistemas, un modelo de datos bien definido (entidades, campos,
  relaciones y restricciones relevantes), los procesos, componentes y demás apartados que el proyecto necesite.
  Seleccionar el contenido y la profundidad por su utilidad para explicar y revisar la solución.
  Distinguir los Markdown de trabajo (.md), que aportan contexto y detalle para la IA y el desarrollo, de los
  entregables Word, que explican de forma estructurada lo que el cliente o el equipo técnico debe comprender y
  validar. Definir cómo se obtiene y mantiene cada entregable a partir del trabajo vigente, seleccionando la
  información relevante para sus lectores y evitando abrumarlos con contexto interno sin valor para su revisión.
  Mantener coherentes el diseño funcional y el técnico, sus diagramas BPM y de arquitectura, el modelo de datos
  y los prototipos de pantalla, de modo que ambos entregables describan la misma solución.
  Evaluar las herramientas para los gráficos y su incorporación al Word; incluir como candidato
  [stack-diagram](https://github.com/caru-ini/stack-diagram), señalado por Raúl. Comprobar su cobertura real de Appian
  y los sistemas relacionados, la procedencia de los iconos, la claridad de los diagramas y sus formatos para Word,
  el mantenimiento de las fuentes y gráficos cuando cambie la solución, las dependencias y las licencias.
  Comparar con las herramientas actuales y decidir con una prueba representativa si aporta valor o se deja fuera.
  Probar el impacto en las skills, los traspasos y la construcción: que el detalle de trabajo permita desarrollar,
  que los Word renderizados y sus gráficos se lean y se puedan revisar, y que ambos diseños sigan siendo coherentes
  cuando cambie el proyecto. Recoger conclusiones y límites en `evaluaciones.md`, evitando documentación o trámites
  sin utilidad. [arquitectura y Word]
- **Cerebro corporativo: información saneada y contexto transversal.** Analizar cómo integrar el plugin con un
  cerebro corporativo que sea la fuente de verdad de la empresa (petición de Raúl, 6-nov; ampliada el 7-nov).
  Debe reunir información de la empresa, información funcional del proyecto y de otros proyectos realizados,
  y conocimiento técnico, de arquitectura, integraciones existentes y componentes reutilizables.
  Definir un agente que analice las reuniones, documentos y demás información entrante y decida, con criterios
  explícitos, qué aporta conocimiento nuevo, qué actualiza o sustituye, qué no se incorpora y qué necesita
  aclaración antes de admitirse. Conservar el original, su procedencia y el motivo de la decisión, también cuando
  la información no se incorpore al conocimiento de referencia.
  Sanear, clasificar y contrastar el contenido con lo ya registrado, tratando duplicados, rectificaciones y
  contradicciones. Distinguir hechos, acuerdos, propuestas, dudas e inferencias, teniendo en cuenta la autoridad
  y el alcance de cada fuente, quién sostiene cada afirmación, su fecha, la empresa, el proyecto y su vigencia.
  Solo la información saneada se incorpora al conocimiento de referencia; lo contradictorio o sin respaldo
  suficiente queda identificado y pendiente de aclarar, sin presentarse como hecho confirmado.
  Definir los criterios de saneamiento y validación, qué puede resolver el agente por sí mismo y qué requiere
  aclaración, y evaluar las herramientas de integración. Las respuestas o deducciones de los agentes deben pasar
  por el mismo tratamiento antes de convertirse en conocimiento de referencia.
  Determinar cómo obtiene cada fase el contexto corporativo pertinente: análisis, diseño funcional y técnico,
  prototipos, construcción, QA y evolución, aprovechando también el conocimiento de otros proyectos de la empresa.
  Contemplar además las consultas del equipo mediante sus agentes y las preguntas muy específicas del cliente:
  responder con precisión y respaldo en fuentes vigentes, dejando claro para qué empresa, proyecto y situación
  vale la respuesta. Si la evidencia no permite una respuesta correcta y exacta, expresar qué falta o qué sigue
  sin resolver, y distinguir lo confirmado de lo que falta por comprobar.
  Identificar el impacto en las skills y los traspasos existentes. Probar la incorporación y reutilización entre
  proyectos, una reunión que rectifica información anterior, fuentes contradictorias u obsoletas y propuestas
  que aún no son acuerdos. Comprobar que una rectificación actualiza las respuestas posteriores y que el
  conocimiento sustituido deja de ofrecerse como vigente; probar también preguntas concretas del equipo y del
  cliente, con y sin respaldo suficiente.
  Verificar en esos casos la calidad de la admisión y de las respuestas, su vigencia y trazabilidad. Coordinarlo
  con el punto de arquitectura anterior; recoger conclusiones y límites en el seguimiento existente, sin añadir
  documentación ni trámites sin utilidad. [contexto corporativo]
- **Prototipos: repertorio hasta Appian 26.10 y elección UX.** Contrastar `appian-prototipos` con el catálogo oficial
  de componentes de interfaz hasta 26.10, detectar los ausentes o con soporte parcial y ampliarlos con ejemplos y
  criterios de cuándo usarlos o evitarlos, para disponer de alternativas usables, accesibles y adaptables. Revisar el
  impacto en catálogo, esquemas, helpers, runtime, plantillas y galerías, y en sus consumidores (capturas y
  documentación), preservando la compatibilidad. Extender las pruebas existentes según lo afectado y probar
  prototipos representativos que combinen elementos actuales y nuevos, sus estados e interacciones. Evaluar también
  con encargos de prototipo que el agente elige componentes adecuados a la necesidad y al contexto de UX, no solo
  que se dibujan; corregir los fallos y repetir los casos afectados. Conclusiones y límites, en este seguimiento y
  en `evaluaciones.md`. Hecho el 6-nov (`evaluaciones.md`): lo nuevo de 26.10 en el kit, lo que se valida y no se
  simula (`componentes.md`) y P26, la elección de componentes con encargos (14 de 14 en 26.10 y en 26.9). Queda, si
  Raúl lo quiere, simular alguno de los parámetros visibles que hoy no se pintan (cabecera fija, mensaje al terminar un
  proceso…) y medir con un funcional menos explícito. [prototipos]
- **Todas las entradas del plugin.** Inventariar y probar las entradas y variantes documentadas en el README, los
  flujos y los modos de cada skill, tanto su invocación directa como su uso dentro de un flujo.
  Incluir un caso representativo del uso real con decenas de reuniones y documentos, hasta construir y comprobar
  en Appian los casos de uso que describen. Revisar el trabajo por lotes, la continuidad entre sesiones, los cruces,
  las contradicciones y los cambios entre fuentes, y la coherencia de los traspasos a diseño, construcción y QA.
  Medir calidad, retrabajo y esfuerzo por fase, distinguiendo la ejecución del método de la revisión del ensayo.
  El recorrido pequeño de la campaña actual no acredita esa escala (indicación de Raúl, 5-nov).
- **Ingeniería inversa y refactorización a fondo.** Probar extracción, continuación, deriva, dependencias,
  planificación y verificación de las refactorizaciones, incluidos errores y recuperación. Recorrer tanto
  `F6 → F3 → F8` (entender y evolucionar) como `F6 → F7 → F8` (entender, refactorizar y construir). Evaluar como
  entradas aplicaciones existentes de Indra-spain y scripts o exportaciones que aporte Raúl, indicando qué permite
  verificar cada origen y qué queda sin comprobar. Raúl autoriza (7-nov) usar para estas pruebas en Indra-spain
  FOR Formación Externa (FOR), IFB Informes y Acciones (IFB) e IFA Informes y Acciones (IFA), también para los
  recorridos de evolución y refactorización. Elegir la aplicación según el caso que aporte valor, conservando la
  evidencia de los estados analizados y el registro de objetos creados. Las decisiones de borrado de §1 siguen
  separadas. Comprobar la conservación
  del comportamiento y la documentación resultante, y corregir los márgenes de mejora encontrados. Usar como casos de
  evaluación los ocho de `aplazados-codex-20261019/mnt-evaluacion-ciega/revision-ciega.md` (recordatorio repetido entre
  ejecuciones, selector con límite o inactivos, usuario fijo…): el puntuador de entonces no los veía. Hecho el 6-nov el
  primer paso, F6 en solo lectura sobre la aplicación de prueba FOR (`evaluaciones.md`). Sus fallos, menores
  incluidos, quedaron corregidos. Para la propia campaña, no para F6.
- **Agentes y skills, por separado y juntos.** Evaluar qué recibe, decide y entrega cada uno; después, comprobar sus
  relaciones y traspasos dentro del flujo completo, su calidad, fricción y coste. Repetir los casos afectados tras
  las correcciones y recoger las conclusiones en este seguimiento y en `evaluaciones.md`. Caso para `pdf-publisher`:
  una vez remitió cuatro procesos a la misma página («ver página N» sin comprobar el destino).
- **Demostración para cliente con una versión madura.** Cuando Raúl considere madura la versión, intentar construir
  una aplicación para enseñar al cliente a partir de los diseños funcionales del proyecto indicado abajo.
  Carpeta del proyecto: `C:\Users\rgmoya\Proyectos IA\Proyecto Contratacion Proveedores`.
  SharePoint es la fuente funcional de referencia; el enlace está en el `README.md` de esa carpeta. La información
  local está incompleta (Raúl, 4-nov).
  Usar también el caso para probar las capacidades y los traspasos del plugin que correspondan y sacar lecciones
  para mejorar el método y el código. Acordar entonces el alcance y el entorno de la demostración, sin interrumpir
  la campaña actual. Conclusiones en `evaluaciones.md` y mejoras pendientes aquí. [persona y sesión]

## 4. Prototipos: lo que pidió un proyecto de prueba (rama `yaroslav/prototipos`)

Lo que salió de usar `appian-prototipos` en un caso real, de octubre a noviembre de 2026, para enseñar un proceso entero
al cliente. Lo pidió la persona que revisaba el prototipo antes de cada demo. Hasta ahora estaba en la rama del DF del
cliente; aquí, junto con lo que se habló después. Casi todo se probó en el proyecto, en su script o con un ajuste local
del HTML construido. Falta llevarlo al plugin: a `design-rules.md`, a los helpers, al runtime y a las plantillas P01
(listado), P02 (ficha), P05 (tarea) y P07 (diálogo). Cada punto, con su prueba en el selftest. Los ejemplos son
genéricos (expediente, lote, registro). Es otro pendiente que el del repertorio de componentes de §3, que ya está hecho.
[prototipos]

### 4.1 Cómo se trabaja con el kit

- **El ajuste local se pierde al reconstruir.** El proyecto cambió con un script propio cómo se dibujan los
  desplegables, los selectores y las fechas (§4.3), sobre el HTML que deja `build.py`. Al reconstruir sin volver a
  pasarlo, el prototipo volvió al formato antiguo y la persona lo vio en la revisión. Que el kit traiga ya ese
  componente (§4.3), o que `build.py` pase solo el ajuste del proyecto si existe (por ejemplo,
  `prototipo/ajustar_kit.py`).
- **`capture.py` enlaza las capturas solo en las fichas PAN** del funcional. Las pantallas del DF del cliente van por
  nombre, y la línea de la imagen la pone el analista. Decidir si `capture.py` las enlaza también por el nombre de la
  pantalla.
- **Prototipo desde el DF del cliente.** `appian-prototipos` parte siempre de `funcional.md` (fichas PAN). Con solo el
  DF del cliente, no dice cómo se hace el inventario: las pantallas de 2.3 por nombre, las actividades de 2.2, la
  matriz de 2.4.1 y los pendientes. Además, el DF describe las secciones de un registro como desplegables editables,
  como las piden algunos clientes, mientras la guía del prototipo pide vistas de solo lectura con diálogos. Decidir
  cuál manda o cómo se dice en el DF. Cuando el cliente ya trabaja con secciones desplegables en sus otros BPM, se
  mantienen (§4.5) y se dice en el `$uxIgnore`.
- **Preparar la demo.** Para enseñar el proceso entero en una reunión, el prototipo necesitó cosas que la guía no pide.
  Valorar un apartado «Preparar la demo» en la skill y que el guion salga del inventario.
  - «Crear» abre la ficha del registro recién creado, con un enlace a la tarea del primer paso.
  - Cada acción vuelve con un aviso que dice en qué estado queda (un `map` de la acción al texto), no con un genérico
    «Acción confirmada».
  - El histórico de los datos de ejemplo recoge también lo que pasa fuera de la tarea: una aprobación de otro órgano,
    la firma y el envío a otro sistema.
  - La bandeja de tareas, de arriba abajo en el orden del flujo, con una tarea por paso, todas en su estado inicial,
    para recorrerlo en la demo. Si los campos cambian según un tipo (el subtipo), un desplegable en la bandeja para
    elegirlo, y una tarea por paso y por tipo.
  - Un registro del primer paso sin nada aportado (sin documentos), para que se vea cómo se genera o se sube lo primero.
  - Al menos un registro en cada estado final (finalizado, rechazado, cancelado), con su ficha completa.
  - Lo que hace otro sistema (crear el registro, generar un documento), simulado: el botón queda bloqueado con un aviso
    de espera unos segundos y después se elige el resultado, sin errores o con un error de ejemplo.
  - Un guion de la demo con un registro de ejemplo por estado, porque las acciones no cambian los datos.
- **Los cambios de diseño, también genéricos.** Lo que se pide cambiar en el prototipo de un proyecto se apunta además
  sin contexto del proyecto, para llevarlo a la skill. Así salió este apartado.

### 4.2 Listados y búsqueda

- **Una columna por dato** y, como mucho, una línea más debajo, con su icono y en gris: el lote bajo el expediente, el
  plazo bajo la fecha de registro. Nunca celdas de tres o más líneas. Al pasar el ratón por un icono de una celda, un
  texto dice qué dato es («Lote», «Plazo de vigencia»). Un texto largo de segunda línea (el adjudicatario) se recorta
  con «…» y se ve entero al pasar el ratón.
- **Columnas agrupadas por tema** (los datos del expediente, juntos). Un estado que pertenece a otra entidad (el estado
  del expediente) va en su propia columna, como etiqueta (chip) del mismo color que en la ficha.
- **Un único formato de identificador** en toda la tabla y en todas las pantallas. Paginación de 10, también en las
  tablas de las secciones y de los modales.
- **Un dato que hoy tiene un solo valor** pero puede crecer (un tipo con un único valor en esta fase) va como segunda
  línea de su columna, no como columna propia, y como filtro.
- **Una columna «Paso»** junto al estado cuando un mismo estado puede darse en dos pasos del flujo. Sin número delante
  del paso, y con un paso «Finalizado» al final, porque en el último paso todavía no se ha finalizado.
- **El mismo nombre en todas las pantallas**: la cabecera de la columna, el filtro, el campo de la ficha y el del modal
  («Estado registro» en la columna y en el filtro). Las cabeceras de fecha, con su nombre completo («Fecha inicio»,
  «Fecha registro»), no «Inicio» o «Registro», que en una tabla con varias fechas no se distinguen.
- **Importes y fechas sin partir**: el «€» en la misma línea que el importe, y la columna con el ancho justo para no
  cortarse. Dos datos en la misma línea de una celda solo caben si la columna es ancha; con nueve o diez columnas, el
  segundo dato va en la segunda línea.
- **La búsqueda, encima del grid**, fuera de los filtros.
- **Los filtros, en su propia tarjeta plegable** sobre el grid, con «Aplicar filtros» y «Limpiar». Hace falta un helper
  con el estado editado y el aplicado.
  - Con muchos filtros, agrupados por tema (registro, expediente, fechas…), y los menos usados tras «Más filtros (N)».
  - De selección múltiple, con la opción «Todos» o «Todas»: elegirla quita las demás, y elegir otra quita «Todos».
  - Pueden tener un valor por defecto (por ejemplo, solo los estados en trámite, sin los finales). El estado inicial
    lo dice el DF.
  - Con más valores elegidos de los que caben, el campo no crece: ver §4.3.
- **El histórico en un modal**, con las mismas columnas y el mismo formato que el listado: el identificador como
  enlace a su ficha, buscador y paginación.
- **Colores de los estados**, los mismos en el listado y en la ficha, por grupos:
  - en trabajo, azul;
  - en revisión, lila, con otro tono que el de «en trabajo» para que no se confundan;
  - esperando a otro órgano o sistema, amarillo;
  - aprobado y cerrado, verdes de distinta intensidad;
  - rechazado, naranja;
  - cancelado, rojo.

  La ficha del estado lleva además un icono propio.

### 4.3 Desplegables, selectores y fechas como los componentes de Appian

El kit dibuja el desplegable múltiple como fichas que crecen con cada valor, el simple con el `<select>` del navegador
y la fecha con su calendario nativo. En una revisión con el equipo nada de eso se parecía a los BPM del cliente, que
usan un componente de Appian visto en un BPM real. Se pide que la skill use siempre, para todos los desplegables y
selectores, un mismo componente; solo cambia si es de selección única o múltiple. Probado en un proyecto con un ajuste
local del HTML construido:
- **El campo** tiene siempre una línea. Enseña los valores elegidos separados por comas, recortados, y en la selección
  múltiple «•••», que al pasar el ratón enseña todos. Lleva una «x» para quitarlos y la flecha. Sin botón «Listo».
- **La lista** lleva buscador (en los filtros, con `searchDisplay: "ON"` o con más de 8 opciones) y una marca en cada
  opción; las elegidas, resaltadas con el color de la marca.
- **Al elegir:** en la múltiple, las opciones se marcan sin cerrar la lista ni pulsar ningún botón; en la única, elegir
  la cierra. Se cierra al pulsar fuera.
- **En los filtros de un listado**, como el filtro de usuario de una lista de registros: la etiqueta dentro del campo,
  en mayúsculas, y vacío «Cualquiera». En los formularios, la etiqueta encima.
- **La fecha:** se puede escribir, y el icono abre un calendario propio (mes, días de lunes a domingo, hoy marcado). En
  los filtros, una sola fecha de rango («desde – hasta»): en el calendario, el primer día marca el inicio y el segundo,
  el fin.
- **Selección única:** un selector (picker) de un solo valor parece de selección múltiple (ficha con «×»). Para elegir
  uno, desplegable con búsqueda; los selectores con búsqueda de un solo valor (`a!pickerFieldCustom`) pasan a
  desplegables con buscador. Si lo que se puede elegir depende de otro campo (los lotes según el tipo de expediente),
  un desplegable por caso con `showWhen`.
- **La lista y el calendario flotan sobre la página.** Dentro de un modal, la lista colocada en absoluto bajo el campo
  la recortaba el cuerpo del modal y no se veían los últimos valores. Se arregló colocándola fija sobre la página según
  el campo, hacia arriba si abajo no cabe, y recolocándola al desplazar. La prueba: con el modal abierto, todas las
  opciones se ven.
- **Dónde va:** en el runtime (`choiceSingle`, `choiceMulti` y `dateInput` de `appian-kit.js`) y en `design-rules.md`.
  Lleva su prueba en el selftest: altura constante, «•••» con todos los valores, la lista que no se cierra al marcar en
  la múltiple y el rango de fechas. Los selectores de usuarios y grupos (`a!pickerFieldUsers`) no se tocaron.

### 4.4 Modales y formularios

- **Ventanas de creación** algo más anchas (MEDIUM_PLUS), con los campos en bloques distinguibles: título más grande con
  su icono y una línea que separa un bloque de otro; si no, el título parece un campo más. Dos campos cortos que
  caben (el expediente y el lote), en la misma línea.
- **Botón principal desactivado** hasta que están los obligatorios, en todos los formularios y modales. Se activa al
  escribir, sin salir del campo (`refreshAfter: "KEYPRESS"`).
- **Un campo de sí o no que decide el flujo** («¿pasa por la comisión?»): un desplegable obligatorio y sin valor por
  defecto, porque con uno por defecto se puede pasar sin querer.
- **Un valor que sale de otro** (el importe al elegir el código presupuestario): un campo deshabilitado que solo enseña
  el valor, al lado. El desplegable no repite ese valor en sus opciones.
- **Opciones que otro sistema no admite.** Las decide ese sistema: si devuelve solo las válidas, solo se ofrecen esas.
  Si se ofrecen todas, al elegir una que no vale se explica por qué. Lo que no tiene sentido ofrecer (expedientes o
  lotes no válidos) se filtra. En el caso real se pasó de lo segundo a lo primero cuando el sistema confirmó lo que
  devolvía: preguntarlo antes de dibujarlo.

### 4.5 La ficha y la tarea de un registro

- **Ficha y tarea, la misma estructura y el mismo ancho.** La sección Acciones solo está en la tarea, que se abre desde
  la bandeja. La ficha lleva un enlace a la tarea para quien la tiene asignada.
- **La cabecera:**
  - una banda con la ficha del estado (su color y su icono, como en el listado), la tarea en curso y, a la derecha, los
    botones de la cabecera (por ejemplo, «Cancelar»), visibles solo para quien puede usarlos;
  - debajo, una tarjeta con los datos generales de solo lectura en dos bloques distinguibles, el del registro y el de su
    entidad asociada (el expediente), y la línea de progreso a todo el ancho;
  - sin migas de pan, sin datos repetidos en la cabecera y en las secciones, sin subtítulos que no aporten, y sin un
    dato que hoy tiene un solo valor (el tipo).

  Lo que el usuario marca o edita va en su sección, no en la cabecera. En el caso real se probó también una tarjeta
  lateral plegable con los datos generales, y se descartó porque quitaba ancho a las secciones.
- **La línea de progreso:**
  - las fases son las tareas del flujo, con un paso final «Finalizado», y se nombran por lo que hace el paso, no por el
    sistema con el que se comunica;
  - un paso opcional (una revisión previa) solo aparece en los registros que han pasado por él: dos líneas de progreso
    con `showWhen`, con y sin ese paso.
- **Secciones desplegables**, como las de los BPM de algunos clientes. En el caso real se hicieron en el script del
  proyecto, con dos tarjetas y una variable por sección; hace falta un helper:
  - el título en el color de la marca, con su icono y el chevron; cerrada, solo el texto va en color, no la línea
    entera;
  - abierta, la barra decorativa a la izquierda;
  - dentro, cada bloque en blanco con borde sobre el fondo gris de la sección;
  - las acciones de la sección («Añadir comentario», «Nueva consulta») en la banda del título, solo con la sección
    abierta.
- **Una sección con muchos datos**, agrupada en subsecciones, cada una con su título e icono:
  - las que están en la misma fila, con la misma altura; crece solo la que enseña un aviso mientras lo enseña;
  - las partes de una subsección, con un fondo algo más gris que la subsección;
  - con margen entre el botón de la subsección y sus campos.
- **Edición por subsección:**
  - los campos se ven de solo lectura, y «Editar» en cada subsección los abre, con «Guardar» y «Cancelar» en su lugar;
  - un campo que casi nunca cambia (una ruta de red) se ve como un campo de texto, no como texto plano, con su
    «Editar»;
  - el asterisco de obligatorio se ve también en lectura.
- **Las tarjetas de datos de solo lectura:** la etiqueta en negrita a la izquierda y el valor a la derecha, alineados en
  columna.
- **Botones en su sección.** Una acción que produce algo de una sección (generar un documento) va en esa sección,
  visible aunque esté desactivada, con un aviso que dice qué falta para activarla. Si el documento generado entra solo
  en la tabla, no hace falta otro botón ni elegir su etiqueta.
- **Las tablas de una sección** tienen búsqueda y paginación, y la columna «Acciones» al final, con los iconos de
  editar y borrar juntos. Si solo el autor puede editar o borrar (un comentario), los iconos salen solo en sus filas.
- **Un total** (la suma de las filas hijas) va como un campo aparte, en negrita, con una ayuda que dice cómo se calcula.
- **Filas hijas** que se eligen de una lista larga:
  - «Modificar…» abre un modal con un desplegable múltiple con búsqueda y «Todos», vacío al abrir;
  - cada fila se edita con su lápiz;
  - antes de guardar, un aviso dice qué se quita, y se puede quitar todo.
- **Avisos tras una acción** (de éxito o de error), que se pueden cerrar. Un error que devuelve otro sistema por campo
  sale junto a su campo, y la subsección se abre para corregirlo.

### 4.6 Las acciones de una tarea

- **Una tarjeta por acción, una debajo de otra y todas del mismo tamaño**, con el icono y el nombre a la izquierda. La
  elegida, marcada con la barra a la izquierda. En horizontal, las tarjetas con nombres de dos líneas quedaban de
  distinto alto.
- **Lo que pide una acción** (un comentario, la persona a la que se envía, un aviso de lo que falta) sale justo debajo de
  su tarjeta, no al final de todas.
- **Volver a pulsar la acción elegida la quita.**
- **«Confirmar»**, el único botón, al final: desactivado hasta tener lo que pide la acción y lo que exige el flujo (por
  ejemplo, el registro creado en otro sistema).
- **El nombre de la acción** dice adónde va («Enviar a revisión a Jefe de Departamento»). Si depende de un campo
  («¿pasa por la comisión?»), cambia con él: «Enviar a la comisión» o «Enviar a firma».
- **Las acciones que valen en cualquier paso** («Guardar», «Consultar») van en todos. «Consultar» solo envía lo
  preparado en la sección de consultas y, si no hay nada, avisa.

### 4.7 Bandeja de tareas

- Coherente con la lista de tareas de Appian (`a!queryTaskList`): vistas «Asignadas a mí» y «De mis grupos», tarea,
  registro, asignada a, estado (aceptada o asignada al grupo), recibida y fecha límite. Las páginas de la documentación
  sobre la lista de tareas de Sites dieron 404 (`Tasks_Tab`, `task-reports`): buscar las vigentes antes de escribir el
  patrón.
- Si el cliente ya tiene una bandeja común en sus otros BPM, se copia su estructura:
  - contadores por grupo, por usuario y completadas, con el de la vista activa resaltado y pulsable;
  - búsqueda y búsqueda avanzada plegable;
  - «Ver las tareas retrasadas», ausencias y exportar;
  - en el grid, la fecha límite en rojo con «Vencida hace N días» debajo, y una bandera en las retrasadas.
- Para la demo: §4.1.
