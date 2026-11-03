# Pendiente

La única lista de lo que falta, en el orden en que se hace: un paso cada vez, y cada punto con su commit y su prueba.
Lo hecho, con sus pruebas y límites, pasa a [evaluaciones.md](evaluaciones.md). Cada punto dice a quién toca. Esta
lista no autoriza publicar, desplegar, enviar ni borrar.

**Ahora:** el paso 3, la prueba con el plugin cargado desde la carpeta, con el guion de
`Pruebas-plugin/paso3-20261103/PRUEBA.md`; mide también el 2.2. P1 a P7, en una sesión en segundo plano que arranca
Claude; P8 y P9 necesitan a Raúl.

## 1. En la rama actual, por orden

### Paso 2 · Aplicar lo que decidió Raúl

Raúl decidió el 3-nov, en el chat: el 2.1 se acepta con el Word siempre al día; el 2.2 se mide (paso 3); el 2.6 se
acepta y hay que probarlo bien. El 2.1 y el 2.6 están aplicados (`evaluaciones.md`) y su conducta se prueba en el
paso 3.

- **2.2 Coste del análisis. Raúl aprueba medirlo (3-nov); se mide en el paso 3.** Con el plugin, el análisis costó
  más en los tres incrementos. La clasificación heurística identifica 155 de 482 llamadas del modelo con órdenes o
  ficheros propios del método; no son pasos prescindibles ni ahorro medido. Los documentos finales `funcional.md` y
  `tecnico.md` pesaban unos 94 y 196 KB. Los 761–928k tokens son
  caché/contexto final de las sesiones, no tokens de esos documentos ni KB releídos. El reparto contable identifica
  focos para revisar, sin aislar causas ni acreditar un techo de ahorro (límites de `coste-analisis.md`, §0 y §4.2).
  **Candidato para medir, sin cambiar el método:** comparar el tratamiento separado con un solo informe para fuentes
  ya disponibles del mismo tema, en orden de fecha (`actualizacion.md`, «Varias fuentes juntas»), partiendo de la misma
  base, fuentes y modelo. Conservar igual cobertura y coherencia, con citas, decisiones y autorizaciones correctas,
  y comparar el coste total observado del modelo principal y del asesor. No anticipar respuestas futuras ni agrupar
  temas distintos. Hay un límite concreto: `version --decision` usa la primera `--fuente` para la fuente y fecha de las
  D y para las marcas 🔒 de VALIDA; si las vías existentes no conservan la procedencia y autorización de cada decisión
  y marca, se mantienen las fuentes separadas, sin forzar la agrupación. Medir en el paso 3 o, si allí no hay fuentes
  del mismo tema para compararlo, en el próximo incremento real, sin deducir ahorro del número de llamadas. La
  consulta por tramos ya está prevista; no se añade una línea fija
  a `resumen`. El crecimiento de caracteres tras `97fa604` incorpora contenido antes omitido y no mide coste entre
  alternativas de igual cobertura. «Varias issues por sesión» es otra hipótesis, sin ahorro acreditado para este
  análisis. No se ha ejecutado esta comparación ni se ha aplicado una regla nueva. [flujo y scripts]

### Paso 3 · Prueba con el plugin cargado desde la carpeta

Con subagentes que leen la rama ya se vieron el push con y sin autorización, la autorización delegada, «gasta» y el
localizador (`evaluaciones.md`). Falta repetirlo con el plugin cargado y lo que necesita Appian. Raúl la aprobó el
3-nov. P1 a P7 los hace una sesión que arranca Claude con `claude --bg --plugin-dir`, con el permiso
`Bash(claude --bg:*)` que Raúl dio el 22-oct (así se arrancaron las del ensayo; lo denegado el 14-oct fue otra cosa,
`claude -p` con `bypassPermissions`). P8 y P9 necesitan a Raúl en persona: su delegación al abrir la sesión, y
`--confiar` con una sesión en segundo plano que lanza él.

- **Probar los cambios de comportamiento con el plugin cargado desde la carpeta** (`claude --plugin-dir`) en un
  proyecto de prueba, como pide `CLAUDE.md`. Comprobar: el localizador con una sesión real; «gasta» en un guion de QA,
  que la skill lo pone al preparar el guion y no solo que el motor lo respeta; la línea «Unidades», el aviso y que el
  analista pone al día «Siguiente paso»; una tarea de una persona en Designer en la entrega; `git push` con un remoto
  local, con y sin autorización, y sin remoto; una autorización que llega por otro agente para un cierre manual o un
  borrado, dentro y fuera de lo delegado (L6); si Write y Edit quedan bloqueados en `claude --bg`, distinguiendo
  un fallo del host de una denegación, que no se rodea; un paquete preparado según F9 (2.6); la medición del 2.2, y lo
  que cambie el paso 2. Puede escribir en Indra-spain si hace falta (Raúl, 3-nov); no sube nada a GitHub. [prueba]

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
