# Pendiente

La única lista de lo que falta, en el orden en que se hace: un paso cada vez, y cada punto con su commit y su prueba.
Lo hecho, con sus pruebas y límites, pasa a [evaluaciones.md](evaluaciones.md). Cada punto dice a quién toca. Esta
lista no autoriza publicar, desplegar, enviar ni borrar.

**Ahora:** paso 2: decide Raúl con la recomendación de cada punto. El feedback de las pruebas que no pedía decisión
ya está corregido (`evaluaciones.md`).

## 1. En la rama actual, por orden

### Paso 2 · Decisiones de Raúl

Claude trae una recomendación por punto; se aplica lo que Raúl decida. Cada una está revisada por un agente escéptico
contra el código y las notas; nada de esto está aplicado.

- **2.1 Documentos al cerrar un incremento.** En la prueba con y sin el plugin, los documentos quedaron a medias:
  decisiones antiguas marcadas como vigentes, contradicciones puntuales, DT con «pendiente: al construir» ya construidas
  y el estado del proyecto sin cerrar. Los diagramas de estados sí se pusieron al día. Raúl quiere que el funcional, el
  técnico, los prototipos y los diagramas draw.io digan cómo está hecho el proyecto, sin nada obsoleto y sin que cada
  construcción sea tediosa. Una primera redacción, en dos momentos (`ef0104b`), se retiró el 29-oct. [flujo]
  **Recomendación:** ningún paso nuevo. El contenido se deja al día al aplicar cada fuente, como ya está escrito; lo que
  se decide al construir entra como DT en ese momento; tras construir nadie edita documentos, porque reescribir una DT
  cambia la versión de su issue. Se quitan los campos de estado que se estropeaban: la columna «Vigente» de
  `decisiones.md` (historial; marcar «No» hace fallar `comprobar.py`) y «Siguiente paso» de `proyecto.md` (estaba viejo
  en los tres cortes, el método se contradice y `estado` ya lo da). «Verificado» pasa a decir dónde se comprueba, y no se
  reescribe. Una frase dice cuándo toca el diagrama de datos, sin aviso ni código. **Límite:** las contradicciones por
  paráfrasis siguen; solo las caza una lectura en frío, que queda fuera. **Pregunta:** ¿se aplica?
- **2.2 Coste del análisis.** Con el plugin, el análisis costó más en los tres incrementos. Un reparto contable de las
  transcripciones (hipótesis, no ahorro causal) apunta a dos causas:
  - los pasos del método por incremento: unos 155 de 482 turnos usan órdenes o ficheros propios del plugin;
  - los documentos vivos grandes (`funcional.md` ~94 KB y `tecnico.md` ~196 KB), que se editan por parches y se
    releen con un contexto de hasta 760–930k tokens.

  **Recomendación:** no juntar pasos ni pasarlos a scripts (como mucho un 12 % de los turnos, sin ahorro acreditado) y no
  tocar las issues sin medir, también tras `97fa604`, que las agranda un 2–15 %. Solo una línea fija en `resumen` con el
  tamaño de los documentos y «no los leas enteros: buscar y `ficha --lineas`». Medir los KB leídos en el paso 3 o en el
  próximo incremento real, sin ronda de pago. La regla de F8 «varias issues por sesión» sigue siendo una hipótesis.
  **Pregunta:** ¿se añade esa línea, sin más cambios? [flujo y scripts]
- **2.3 Aviso «criterios sin objeto».** No se apaga al marcar la unidad construida, porque las historias no tienen la
  marca «Otra unidad». **Recomendación:** una frase al final del aviso (si esta unidad no las construye, no hace falta
  nada; si las construye, falta su fila «Para»), sin marca para historias. **Pregunta:** ¿basta? [`issues.py`]
- **2.4 Cambiar una issue ya verificada.** Falta un camino corto: dónde se escribe, qué subtareas lleva y qué cambió.
  **Recomendación:** tres líneas en F8 que remiten a la plantilla técnica y a `cambios.md`: se escribe en el técnico, se
  regenera y solo vuelve a pendiente la issue cuyo encargo cambia; lo cambiado se ve con `git diff`; las subtareas de una
  issue ya verificada no hace falta volver a marcarlas. **Pregunta:** ¿se aplica? [F8]
- **2.5 Referencias de la skill oficial por tipo de objeto.** Cargarla entera costaba un 37–72 % de una sesión hasta su
  primera escritura. La oficial ya no lo pide: trae su mapa de referencias. **Recomendación:** no tocar F8 ni añadir una
  tabla propia, que se desfasaría. Quitar del plugin las dos frases que dicen que la oficial obliga a cargar sus
  referencias antes de cada escritura (`appian-best-practices/SKILL.md` y doc 14). **Pregunta:** ¿se quitan? [buenas prácticas]
- **2.6 F9.** Decidir si la IA puede dejar preparado el paquete en desarrollo; hoy lo prepara una persona.
  **Recomendación:** sí, sin exportar ni desplegar; el ICF y los scripts de base de datos los pone una persona, y la
  revisión del paso 4 es siempre de una persona (decirlo en F9 y en el README). Sin regla sobre el alta en lote: la
  herramienta ya devuelve el error. **Pregunta:** ¿se aplica? [F9]
- **2.7 Decisiones pequeñas del barrido del feedback.** Cada una, una frase o nada:
  - Lo que solo hace una persona en Designer bloquea la cadena: un campo de §3 que el Dev MCP no crea sale en lo esperado
    de cada issue. Recomendación: que el técnico lo escriba como paso manual de §13, sin rebajar lo esperado de lo demás.
    Depende del 2.1. [plantilla técnica]
  - El Dev MCP no configura el inicio programado de un proceso y una sesión lo rodeó con un bucle que nadie puede parar.
    Recomendación: añadirlo a los ejemplos de «lo hace una persona» en `appian-best-practices/SKILL.md`. [buenas prácticas]
  - Con reuniones sin prioridades, la IA escribe «Pendiente» y `comprobar.py` falla. Recomendación: una frase en la
    plantilla del funcional: propuesta 🔶 y una PC, como ya dice la ingesta de un DF. [plantilla funcional]
  - Botón «Limpiar» tras uno que valida deja «A value is required»; `validationGroup` no bastó. Recomendación: una frase
    en el doc 02 marcada «seen once». [buenas prácticas]
  - `pdf-publisher` no comprueba los destinos de «ver página N» (una vez, corregido a mano). Recomendación: dejarlo como
    límite conocido. [agente]
  - Las galerías HTML de `appian-prototipos` (1,8 MB) no las cita nadie y se regeneran. Recomendación: retirarlas, con
    confirmación. [prototipos]
  - Volver a probar el método de volumen grande y la contradicción de alcance perdida cuesta 2,7–3,8 M de tokens.
    Recomendación: esperar al próximo proyecto grande real. [prueba]
  - La seguridad de acciones de registro con constante no salía a nadie (una vez, sin causa demostrada). Comprobarlo
    escribe en Indra-spain. Recomendación: una prueba corta solo si Raúl la autoriza; hasta entonces, sin regla. [prueba]

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
- En Indra-spain, comprobar qué sigue ahí: las aplicaciones PCA (vacía) y CTC, las 7 tablas `CTC_*` de `jdbc/Appian`, que
  el Dev MCP no borra, `dem.gestor`, `dem.gestor2` y `dem.revisor` en los grupos CTC, y del ensayo Informes los datos,
  los objetos y las instancias que solo cancela una persona, incluidas las cadenas diarias que envían correo. Se quita con
  la confirmación de Raúl. [persona y sesión]

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
- **Todas las entradas del plugin.** Inventariar y probar las entradas y variantes documentadas en el README, los
  flujos y los modos de cada skill, tanto su invocación directa como su uso dentro de un flujo.
- **Ingeniería inversa y refactorización a fondo.** Probar extracción, continuación, deriva, dependencias,
  planificación y verificación de las refactorizaciones, incluidos errores y recuperación. Comprobar la conservación
  del comportamiento y la documentación resultante, y corregir los márgenes de mejora encontrados. Usar como casos de
  evaluación los ocho de `aplazados-codex-20261019/mnt-evaluacion-ciega/revision-ciega.md` (recordatorio repetido entre
  ejecuciones, selector con límite o inactivos, usuario fijo…): el puntuador de entonces no los veía.
- **Agentes y skills, por separado y juntos.** Evaluar qué recibe, decide y entrega cada uno; después, comprobar sus
  relaciones y traspasos dentro del flujo completo, su calidad, fricción y coste. Repetir los casos afectados tras
  las correcciones y recoger las conclusiones en este seguimiento y en `evaluaciones.md`.
