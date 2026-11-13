# Pendiente

La única lista de lo que falta, en el orden en que se hace: un paso cada vez, y cada punto con su commit y su prueba.
Lo hecho, con sus pruebas y límites, pasa a [evaluaciones.md](evaluaciones.md). Cada punto dice a quién toca. Esta
lista no autoriza publicar, desplegar, enviar ni borrar.

Cada pendiente explica el problema, qué hay que hacer y el resultado esperado, conservando los acuerdos de la
conversación. Si el detalle ya está bien explicado en otro documento, se enlaza desde el punto en lugar de repetirlo.

**Ahora:** rama `claude/pruebas-metodo-20261104`, subida sin PR, con `main` unido (la 0.8.0-beta.3 se publicó el 5-nov sin esta rama). La campaña «el método de punta a punta» (4-7 nov.) recorrió F1-F9 con un proyecto ficticio en la aplicación de prueba FOR de Indra-spain y aplicó las decisiones de Raúl del 7-nov (aprobación por impacto real, rúbrica UX y regresión por impacto, que se mide antes de escribirla); la campaña «entender y evolucionar» llegó a construir EV-01 (C1-C3). Todo en `evaluaciones.md`. Falta C4, el QA de EV-01 y la medición de la regresión (§2), parado por las sesiones de SAIL de las cuentas de prueba. El trabajo «adaptarse a las actualizaciones de Appian» (rama `raul/estrategia-actualizaciones-appian`) espera a que esta rama entre en `main`, porque toca los mismos ficheros.

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
- **Regresión en un evolutivo: medir antes de escribirla.** Decisión de Raúl (7-nov): repetir según el impacto
  real del cambio (presentación, lo afectado; una regla, acción o filtro, sus casos y los escenarios de otros flujos y
  roles que puedan verse afectados; transversal o sin acotar, todo), las pruebas de cada issue al construir y la
  regresión seleccionada en el QA del evolutivo; F9, completa. Antes de escribirlo en F8 y en la skill de QA, comparar
  un cambio aislado y otro compartido, midiendo qué detecta y cuánto tarda (`diseno/regresion-evolutivo.md`, «Lo que
  decidió Raúl»). Se hace dentro de la campaña «entender y evolucionar» de §3, que ya llegó a construir EV-01 en
  FOR (`evaluaciones.md`): falta su QA y la medición (`Pruebas-plugin/metodo-20261104/regresion-C4-seleccion.md`).
  Necesita sesión de SAIL CLI de `dem.gestor` y `dem.revisor`, que dan 401 desde el 7-nov (`dem.gestor2` sigue viva),
  y de `dem.revisor2`, la segunda cuenta de `FOR Formación` para probar que quien pide no decide (PT-12 de
  `evolucion-for`): se creó con contraseña temporal y con ella `sail login` falla (Appian pide cambiarla); que entre tras
  cambiarla en el navegador está sin medir. Cada cuenta la renueva la persona en su terminal con `login-sail.ps1 <cuenta>` de esa carpeta, que pide la
  contraseña sin mostrarla. [flujo · QA · persona]
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
