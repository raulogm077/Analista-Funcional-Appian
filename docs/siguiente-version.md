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
- **El SKILL.md, del mismo commit que los scripts.** Una sesión dibujó con los scripts de una rama y siguió el SKILL.md del plugin instalado, de otra versión, y no aplicó las reglas nuevas (pedir el DF, prefijos «Supuesto:»). Al usar una skill desde una rama o una copia, se lee su SKILL.md de esa misma copia. Si vuelve a pasar, una frase en `CLAUDE.md`. Segundo caso (24-nov): un hilo dibujó con el plugin instalado en su sesión (0.8.0-beta.3) y no con la rama del PR abierto, y el diagrama salió sin el aspecto nuevo; se rehízo con los scripts de la rama. El encargo de un hilo de diagramas debería decir de qué copia se usan los scripts. [persona y sesión]
- **Diagramas: lo que queda de las órdenes que faltaban** (auditoría del 10-nov). Se hicieron pestañas, `importar`,
  `comparar --con`, `supuesto`, carriles por sistema y un PNG por pestaña (`evaluaciones.md`). No se hizo el campo `ref`:
  el código del cliente entre corchetes al final del nombre ya se dibuja aparte y `leer` lo devuelve; si un DF necesita
  más de un código por tarea, se retoma. Tampoco «bajar una puerta de fila cuando quede más claro»: hace falta un
  criterio medible antes de tocar la colocación. [diagramas]
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
- **Diagramas: variante oscura del PNG.** El aspecto nuevo (tarjetas con pictograma, cabecera y paleta) es solo
  claro. Una variante oscura, si un documento o una web la pide; el `.drawio` no cambia. [diagramas]
- **Diagramas: abanico en más casos.** Las salidas en abanico solo cubren las de una puerta hacia su misma fila y a
  la derecha. Si un proceso real muestra cruces en otros casos (destinos a la izquierda o en otra fila), ampliarlo con
  su prueba en `selftest.py` (`cruces`). [diagramas]
- **Diagramas: elegir la colocación con menos cruces.** En un proceso real con tres vueltas atrás a la misma tarea
  (rechazos y errores que vuelven a «Rellenar la plantilla»), Mermaid dejó muchos cruces y la colocación por capas
  ninguno; se entregó la de capas (`DIAGRAMAS_SIN_NAVEGADOR=1` al crear y `png` después). Medir los cruces de las dos
  y quedarse con la mejor, con su prueba; mientras, `actualizar` con navegador vuelve a colocar con Mermaid. Segundo
  caso (24-nov): un circuito de aprobación con tres revisiones que devuelven a la misma tarea; Mermaid lo dejó de
  derecha a izquierda y con cruces largos, y por capas se leía de izquierda a derecha. Tercer caso (24-nov): el
  de inversiones, rehecho con las reglas de estructura, salía con Mermaid de derecha a izquierda y con vueltas largas;
  se entregó por capas (más ancho, 6.025 px, pero de izquierda a derecha). Cuarto caso (24-nov): un ciclo mensual
  con vueltas a un temporizador intermedio y a la tarea que registra; Mermaid intercalaba el alta con el ciclo y por
  capas salía en orden. Alternativa mínima, si medir
  las dos cuesta: una opción `--colocacion capas` en `crear` y `actualizar`. [diagramas]
- **Diagramas: flujos pegados en la colocación por capas.** `mejorar` no cuenta dos flujos cerca cuando coloca por
  capas («ya va cada uno por su fila»), pero en un proceso real dos verticales de vueltas atrás distintas quedaron a
  11 px y se leían como una sola línea con cruces (24-nov). Contar también ahí los pegados (`_pegados`, menos de
  `HUECO`) y medir en los procesos al azar de `selftest.py` si añade cruces. [diagramas]
- **Diagramas: qué hace Appian con varias salidas de un nodo.** Desde el 24-nov, `validar` avisa de una tarea con
  varias salidas sin puerta, porque en BPMN se siguen todas a la vez, y el SKILL.md pide una puerta exclusiva detrás.
  Falta mirar en el Dev MCP (un process model real) si Appian hace lo mismo, para decir en ingeniería inversa si esas
  salidas son paralelas o condiciones, y si `bpmn_export.py` debe escribir la condición cuando venga de Appian. [diagramas]
- **Diagramas: la línea de un plazo por la misma recta que la salida de su tarea.** En una prueba con el plugin
  cargado (25-nov, proceso ficticio por capas), la entrada a la tarea ocupaba su lado de abajo; la línea discontinua
  al plazo salió por arriba, rodeó la tarea y bajó por la misma vertical por la que subía su salida hacia la puerta
  (60 px pegadas). `mejorar` la deja así aunque `trazar_todo` no deja que dos flujos ajenos compartan tramo, y
  `separar_pegados` no lo ve (`_pegados` excluye la misma recta) ni puede apartarla sin un cruce. Mirar en qué paso de
  `mejorar` entran los dos caminos sin pasar por esa regla; lo natural era la salida por arriba (la puerta está arriba)
  y el plazo por la derecha. Relacionado con 4.20 del recopilatorio (dos plazos que comparten tramo). [diagramas]
- **Diagramas: el fichero de supuestos cuando el DF pasa a ser la referencia.** En la prueba con el plugin cargado del
  25-nov (caso real GC-011), al llegar el DF la sesión borró `supuestos-X.md` porque «solo se hace sin diagrama
  aprobado», aunque quedaban un supuesto, cuatro contradicciones entre el DF y las reuniones y lo pendiente de validar.
  Decidir si el fichero se queda mientras haya algo por confirmar. [diagramas]
- **Diagramas: cuándo las fuentes «rediseñan» el aprobado.** En la misma prueba, la sesión dijo que las reuniones,
  dos meses posteriores, «no cambian el proceso» aunque añaden una revisión manual y otra forma de subir, y tomó el DF
  como referencia; aun así dibujó lo de las reuniones en los dos puntos. En la primera pasada, sin el arreglo, ni
  comparó las fechas. Si vuelve a pasar con otro caso, dar en `fuentes.md` un criterio más concreto. [diagramas]
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
