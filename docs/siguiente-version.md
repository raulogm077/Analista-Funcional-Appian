# Pendiente

La única lista de lo que falta, en el orden en que se hace: un paso cada vez, y cada punto con su commit y su prueba.
Lo hecho, con sus pruebas y límites, pasa a [evaluaciones.md](evaluaciones.md). Cada punto dice a quién toca. Esta
lista no autoriza publicar, desplegar, enviar ni borrar.

**Ahora:** revisar las recomendaciones del paso 2 y cerrar las aclaraciones que ya tienen respuesta en el método.
Los arreglos comprobados de esta tanda están en `evaluaciones.md`. El 2.1 sigue retirado y pendiente.

## 1. En la rama actual, por orden

### Paso 2 · Decisiones de Raúl

Claude trae una recomendación por punto; se aplica lo que Raúl decida. Son borradores contrastados con el código y las
notas; el 2.1 sigue por revisar con las reservas siguientes. Nada de estas propuestas está aplicado.

- **2.1 Documentos al cerrar un incremento.** En la prueba con y sin el plugin, los documentos quedaron a medias:
  decisiones antiguas marcadas como vigentes, contradicciones puntuales, DT con «pendiente: al construir» ya construidas
  y el estado del proyecto sin cerrar. Los diagramas de estados sí se pusieron al día. Raúl quiere que el funcional, el
  técnico, los prototipos y los diagramas draw.io digan cómo está hecho el proyecto, sin nada obsoleto y sin que cada
  construcción sea tediosa. Una primera redacción, en dos momentos (`ef0104b`), se retiró el 29-oct. [flujo]
  **Por revisar, sin propuesta aprobada.** Falta concretar cuándo actualizar solo los documentos afectados por una
  fuente, una decisión o un cambio real durante la construcción y el QA, para que los cuatro reflejen el proyecto sin
  reescribir lo que no cambia. La caducidad de una huella no justifica dejar documentación obsoleta: hay que resolver
  cómo registrar lo construido sin repetir trabajo innecesario. La alternativa de retirar «Vigente» y «Siguiente paso»
  tampoco está validada: `modelo.py` lee «Vigente» y reconoce «No» como sustituida; `comprobar.py` rechaza que una pieza
  vigente siga citando esa decisión sin indicar su anulación, no el «No» por sí solo. `estado` imprime el texto de
  «Siguiente paso» de `proyecto.md`; no lo calcula ni sustituye sus posibles acciones de negocio. Antes de recomendar
  retirar campos, hay que revisar sus consumidores y qué información los reemplazaría. No se retira ninguno. Entra
  aquí también lo que solo puede hacer una persona en Designer: un campo de §3 que el Dev MCP no crea sale en lo
  esperado de cada issue y para la cadena; no se rebaja lo esperado para que pase sin configurarlo.
- **2.2 Coste del análisis.** Con el plugin, el análisis costó más en los tres incrementos. La clasificación heurística
  identifica 155 de 482 llamadas del modelo con órdenes o ficheros propios del método; no son pasos prescindibles ni
  ahorro medido. Los documentos finales `funcional.md` y `tecnico.md` pesaban unos 94 y 196 KB. Los 761–928k tokens son
  caché/contexto final de las sesiones, no tokens de esos documentos ni KB releídos. El reparto contable identifica
  focos para revisar, sin aislar causas ni acreditar un techo de ahorro (límites de `coste-analisis.md`, §0 y §4.2).
  **Por revisar, sin propuesta aprobada:** qué pasos agrupar o automatizar y qué lecturas limitar, manteniendo la
  calidad. Buscar y leer el tramo de `ficha --lineas` ya está en el método; la utilidad adicional de una línea fija en
  `resumen` no se ha probado. Medir el efecto en el paso 3 o en el próximo incremento real, sin deducir ahorro del
  número de llamadas. El crecimiento de caracteres tras `97fa604` incorpora contenido antes omitido y no mide coste
  entre alternativas de igual cobertura. «Varias issues por sesión» sigue siendo una hipótesis. [flujo y scripts]
- **2.3 Aviso «criterios sin objeto».** El cálculo señala historias que considera de la unidad, con criterios nuevos
  o cambiados cuyos escenarios no entran en ninguna issue. No consulta si la unidad está Construida; la ausencia de
  «Otra unidad» en las historias no es su condición de disparo (esa marca reparte texto técnico).
  **Por revisar:** distinguir un aviso residual del alcance de una falta real de cobertura. Si esos escenarios
  corresponden a la unidad, revisar su asignación en §13; la marca Construida no acredita que se hayan cubierto.
  No se propone ignorarlos ni añadir una marca nueva sin resolver ese alcance. [`issues.py`]
- **2.4 Cambiar una issue ya verificada.** Falta un camino corto: dónde se escribe, qué subtareas lleva y qué cambió.
  **Borrador para F8:** los ajustes técnicos dentro del encargo aprobado se escriben en el técnico según su plantilla
  y se regenera. Si hay informes nuevos o puntos Pendiente de la unidad, se respeta la aprobación o reasignación que ya
  exige el método.
  Vuelven a pendiente las issues cuyo encargo cambia; las demás conservan su verificación vigente. Para ver el cambio,
  comparar en git con la revisión anterior. Las subtareas son avance declarado: pueden quedar en Revisar y la
  verificación antigua no vale para la nueva versión. Tras verificar la versión vigente, no hace falta remarcar
  subtareas para cerrar la issue. **Pregunta:** ¿se incorpora esta aclaración? [F8]
- **2.6 F9.** Decidir si la IA puede dejar preparado el paquete en desarrollo; hoy lo prepara una persona.
  **Borrador por aprobar:** que la IA prepare un borrador en desarrollo, con la revisión del paso 4 siempre humana;
  exportar y desplegar siguen a cargo de una persona. La asignación del ICF y los scripts de base de datos a una persona
  es una elección de roles, no una falta de herramientas: el esquema disponible expone ambos. `addPackageObjects`
  advierte de éxito parcial en `success`/`errors`; no basta el estado de la llamada para dar el lote por completo.
  No se ha probado aquí una preparación real de paquete. **Pregunta:** ¿se autoriza ese reparto? [F9]

### Paso 3 · Prueba con el plugin cargado desde la carpeta

Con subagentes que leen la rama ya se vieron el push con y sin autorización, la autorización delegada, «gasta» y el
localizador (`evaluaciones.md`). Falta repetirlo con el plugin cargado y lo que necesita Appian.

- **Probar los cambios de comportamiento con el plugin cargado desde la carpeta** (`claude --plugin-dir`) en un
  proyecto de prueba, como pide `CLAUDE.md`. Comprobar: el localizador con una sesión real; «gasta» en un guion de QA,
  que la skill lo pone al preparar el guion y no solo que el motor lo respeta; la línea «Unidades», el aviso y que el
  analista pone al día «Siguiente paso»; una tarea de una persona en Designer en la entrega; `git push` con un remoto
  local, con y sin autorización, y sin remoto; una autorización que llega por otro agente para un cierre manual o un
  borrado, dentro y fuera de lo delegado (L6); si Write y Edit quedan bloqueados en `claude --bg`, distinguiendo
  un fallo del host de una denegación, que no se rodea; y lo que cambien los pasos 1 y 2. Aprobarla no autoriza escribir en
  Indra-spain ni subir a GitHub. [prueba]

### Paso 4 · Residuos de las pruebas

- En `Pruebas-plugin`, revisar `automejora/`, `automejora-codex-20261019/`, `campana-codex-20261019/`,
  `aplazados-codex-20261019/`, `construccion-cerebro/`, `informes-comparativa-20261022/`, `informes-con-plugin/`,
  `informes-sin-plugin/`, `T1-agilidad/`, `T5-devmcp-sail/`, `T6-retoque-construido/`, `T13-pruebas-issue/`, `T15-qa/`,
  `T16-ensayo-qa/` y `retoque-analisis/`. Primero las que guardan fuentes reales del cliente
  (`campana-codex-20261019/`, `informes-con-plugin/`). Antes de borrar
  cada una, comprobar que sus lecciones estén aquí o en `evaluaciones.md`, si la cita como evidencia algún documento
  que se conserva (el seguimiento del ensayo, la revisión de Codex) y qué objetos dejó en Indra-spain
  (`T6-retoque-construido/objetos-creados.md`). Se guarda lo que haga falta; lo demás, y sobre todo lo que lleve datos
  del cliente, se borra con la confirmación de Raúl, que lanza él el borrado si la sesión no puede. [persona y sesión]
- En Indra-spain, las consultas de solo lectura del 3-nov no encontraron las aplicaciones PCA y CTC, las tablas `CTC_*`
  ni los grupos CTC (no prueba que no existan con otros permisos). Siguen
  las aplicaciones IFA e IFB del ensayo con sus datos, y dos instancias activas de `IFA Revisar Fechas Limite` desde el
  24-oct, que se repiten cada día y envían correo; solo las cancela una persona. La de IFB no se puede leer (403). Qué
  se quita lo confirma Raúl. [persona]

- En el repositorio, las galerías HTML de `appian-prototipos/galerias/` (1,8 MB, no las cita nadie y se regeneran con
  `generar_app.py` y `build.py`): retirarlas o dejarlas lo confirma Raúl. [persona]

### Paso 5 · Cierre de la rama

- **Cierre**, cuando Raúl diga «sube». Antes del PR, poner al día «Trabajo en curso» de `CLAUDE.local.md`. La batería
  completa pasa en GitHub. Antes de publicar una versión, las siete combinaciones y `pruebas/comprobar_anclas.py` (con
  red). [persona y sesión]
- **Copia de seguridad.** La rama no está en GitHub; se sube como copia, sin PR, cuando Raúl lo autorice. [persona]

## 2. Cuando se dé su condición

- **Índice del DOCX.** Evaluar la caché editable solo si una entrega la necesita. [Word]
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
- **URL `/help/26.6/`** de `data-fabric.md` y `agents/data-modeler.md`: revisarlas cuando cambie la versión de Appian
  del entorno.
- **Aviso a Appian** (`aviso-appian-devmcp.md`, en la carpeta de pruebas): revisarlo con el servidor 26.9.5, porque el
  punto 10 ya está en parte corregido. Añadir la discrepancia de `LCP_TOOL_MODE=readonly` y lo visto en el ensayo: cada
  copia del servidor borra el `cookies.json` compartido al caducar su sesión (hay un parche local que cada bundle pisa),
  `listProcessInstances` omite instancias y su «total» cambia, no hay forma de cancelar instancias, el rechazo del MCP
  por «builds distintas» a mitad de un trabajo y el caso que crea `testInputs`. Lo envía Raúl. [persona]
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
