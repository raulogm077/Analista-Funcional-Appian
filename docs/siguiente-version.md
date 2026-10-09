# Para la siguiente versión

El alcance de la 0.7.0 está congelado hasta F9 (Raúl, 8 de octubre de 2026): lo nuevo que surja mientras tanto se
apunta aquí y entra en la siguiente versión. Cada línea dice qué, dónde y de dónde sale.

## Prototipos

- Partir `scripts/marca.py` en módulos (lector web aparte; `crear` en validar, calcular, perfil y escribir). Hoy es un
  solo fichero, como pide el plan, y lo cubren las pruebas. Revisión de la Tarea 0c.
- `marca.py web` busca «logo» como palabra entera: se le escapan compuestos en minúsculas como `logomark` o `logoimg`.
  Revisión de la Tarea 0c.
- La lista «Comprobado con WCAG 2.2 AA» de `marca-<id>.md` da por hecho el 4,5:1 del texto del botón principal, que en
  Appian es automático. Revisión de la Tarea 0c.
- `$assumption` repite la fecha si `--fuente` ya acaba en una. Revisión de la Tarea 0c.
- Con más de 8 colores de marca, `marca.py` se queda con los 8 primeros sin decirlo, y `references/marca.md` dice que
  solo se quedan fuera los que no llegan a 3:1. Revisión de la Tarea 0c.
- `build.py` tiene su propia `_lum`, duplicada de `validate.py`. Revisión de la Tarea 0c.

## Ingeniería inversa

- `build_model.py` lee todos los `*.json` de la carpeta de cada objeto: si dos equipos extraen a la vez en una carpeta
  sincronizada, las copias de conflicto de OneDrive (`…-PC.json`) contarían como respuestas. Revisión de F2.
- `extraction_report.json`, `toolsUsed`: lista herramientas sin ninguna llamada (`getAiAgent` en una aplicación sin
  agentes de IA), y «usadas + omitidas» no da el catálogo que cuenta INVENTARIO. Medida «después» de F3.
- `datafabric`: `metadataRaw` trae record types de otras aplicaciones. Medida «después» de F3.
- Pasada de coherencia: ningún script comprueba que cada mención de otra área lleve su ID canónico. Medida «después» de F3.
- `build_datos.py` cuenta 80 aristas y `summary.json` 83 (las de fuera de la aplicación): decirlo en `datos.md`.
- `security-rules.md`: decir que el valor de un secreto se reproduce tal cual (nada se oculta) y dónde acaba (04,
  registro de 09, `datos/hallazgos.json`).
- Las URL de la documentación de Appian con versión fija (`/help/26.6/`) en `references/data-fabric.md`,
  `devmcp-setup.md` y `agents/data-modeler.md`, frente a `/latest/` de la regla «Dudas de Appian»: son del Appian MCP
  Server, que depende de la versión; revisar al cambiar de versión. Paso 3 de la Tarea 9.
- `comprobar_asis.py` (revisión de F3):
  - solo mira los nombres con el prefijo entre comillas invertidas; uno inventado en texto plano, en negrita o como texto
    de un enlace pasa. Buscar también `<prefijo>_\w+` fuera del código;
  - una evidencia que enlaza la ficha de otro objeto, o `anexo/indice.md`, pasa: comparar `mcp:<tipo>/<nombre>` con
    `inventario.json → anexo`, como `evidencia.py`;
  - un `H-…` citado que no existe pasa (los NV sí se comprueban);
  - sin prefijo en la aplicación, la comprobación de nombres se apaga sin avisar;
  - las cifras solo se miran en la línea «Volumen».
- `tambien` de `inventario.json`: también la tabla de cada CDT y las entidades de cada data store (revisión de F3).
- El aviso de respuestas reutilizadas compara con una hora; mejor con el `startedAt` del último `plan`.
- Retomar con el extractor de 0.7.0-alpha.2 una extracción de 0.7.0-alpha.1 deja 27 secciones «getAiAgent: No
  disponible» en el anexo, porque `build_model.py` lee todos los `*.json` de la carpeta de cada objeto (como las copias
  de OneDrive de arriba).
- Prototipos: `sys.dont_write_bytecode` en `sail_helpers.py` no evita su propio `.pyc`; lo escriben en el kit
  `templates/generar_plantillas.py`, `galerias/*/generar_app.py` y un generador que siga el docstring de
  `sail_helpers.py`. Poner el flag en esos cuatro y en el docstring, y ampliar la regla de `comprobar_plugin.py`.
- Evaluación del recién llegado: el docstring de `palabras.py` dice «como las cuenta `comprobar_asis.py`», pero cuenta
  también los títulos y el texto generado.
- Presupuestos de palabras: con MNT, la mayoría de documentos van al 20-50 % de su límite; afinarlos con más medidas.
- Los role maps de los objetos no están en `as-is/` ni quedan como NV: refactorización solo puede preguntarlos como
  decisión. Evaluación de la Tarea 15.
- La propuesta de MNT sacó del anexo dos señales que ingeniería inversa no registró como hallazgo: nombres fijos del
  proceso y sus tareas, y dos reglas sin el prefijo de la aplicación. Evaluación de la Tarea 15.

## Buenas prácticas

- No hay sección sobre funcionalidades deprecadas: `senales.md` de refactorización las manda a BP 08 §7, la más
  cercana. Tarea 13.
- No hay sección sobre objetos huérfanos o sin ejecuciones: `senales.md` de refactorización los manda a BP 11 §8,
  que solo lo dice en una línea (política de retirada). Revisión de F5.
- No hay sección sobre el «Cancelar» de un formulario de inicio de proceso (el patrón solo está en la documentación de
  Appian): la propuesta de MNT usó BP 10 §2, genérica. Evaluación de la Tarea 15.
- Ninguna sección trata un paso de proceso que se hace siempre aunque no haga falta (la orden pasa siempre por
  «Pendiente de material»): la segunda propuesta de MNT lo dejó como decisión. Evaluación de la Tarea 15.

## Diagramas

- La línea de puntos de una nota cruza la etiqueta de su puerta. Revisión de F4.
- `X.drawio.tmp` se queda en la carpeta si falla la relectura de comprobación al escribir. Revisión de F4.
- BPMN: `calledElement` guarda solo el nombre (QName) del proceso llamado, y un evento de error que no va unido a una
  tarea se exporta como evento intermedio. Revisión de F4.
- Mermaid dibuja las dos líneas de un bucle de dos pasos una encima de otra. Revisión de F4.
- Las pruebas que importan scripts de una skill dejan `__pycache__` dentro de `skills/`; `sin_bytecode()` de
  `comprobar_plugin.py` solo mira los scripts. Revisión de F4.
- Colocación por capas: las filas de la columna que sigue a una puerta se compactan y quedan verticales largas en los
  huecos; en el ejemplo semántico, «Sí» cabe justa, pegada a la flecha. Pasada de correcciones de F4.
- Si se renombra un paso a mano en draw.io, el nombre de la página de su tramo no cambia hasta que se vuelve a colocar.
  Pasada de correcciones de F4.
- `mermaid.py` sin argumentos sale con 2 (el de argparse), que en el script significa «falta un requisito». Pasada de
  correcciones de F4.

## Refactorización

- `comprobar_propuesta.py` (revisión de F5):
  - `re.split(…, 1)` pasa `maxsplit` por posición: dos DeprecationWarning en cada ejecución con Python 3.13 (también
    `comprobar_asis.py:110`);
  - una REF citada en la prosa de encima de la tabla de la Hoja de ruta da el aviso de «Verificar» aunque la tabla lo
    ponga;
  - una ficha escrita «### REF-01 · …» no se reconoce y da errores de REF que no está en el Diagnóstico;
  - sin `hallazgos.json` deja de comprobar los `H-…` sin avisar;
  - el aviso de hallazgos Alta o Media sin REF no conoce el alcance: con una propuesta de una parte de la aplicación,
    salta con los de fuera de esa parte.
- `puntuar.py` de la evaluación de malas prácticas solo acepta fichas `**REF-`, no dice nada si `as-is/` no trae NV de
  objetos de fuera, y `prueba_puntuar.py` no lo corre `--completo`. Revisión de F5.
- `senales.md`: «funciones HTTP deprecadas» (BP 07 §1) y «connected system sin autenticación» (BP 07 §2) apuntan a
  secciones que no tratan el problema como tal, y no hay otra mejor. Pasada de correcciones de F5.
- Segunda propuesta de MNT (evaluación de la Tarea 15), puntos de fricción:
  - lo que falta y no es decisión ni NV (versión de Appian no determinada, tier, tamaño del equipo) no tiene tipo de ID;
  - «una REF por problema» no dice si un hallazgo que mezcla varios problemas puede alimentar varias REF;
  - la tabla de estrategias define «Mixta» como datos y procesos nuevos; el caso de conservar los datos y rehacer la
    lógica no tiene nombre;
  - el orden fijo de la Hoja de ruta deja para el final los defectos Alta de los procesos: falta decir si arreglarlos ya
    en la aplicación actual es contención;
  - los pasos 1, 2 y 5 piden hablar con el usuario; sin nadie que responda, no dice dónde dejar el resumen inicial;
  - BP 03 §9 para el recordatorio frecuente: quien la usó dice que trata el archivado y la memoria, no la frecuencia (la
    pasada de correcciones la eligió frente a la §13; `bp_aceptadas` de MP-05 admite la §6 y la §9).

## Analista

- Revisión de F6: «Sustituye» no comprueba que el objeto nuevo no esté ya en el inventario; §13 solo se comprueba si el
  técnico tiene alguna DT o §3 con campos (un evolutivo de solo pantallas se la salta); el paso 8 de SKILL.md no nombra
  «DF ya hecho»; `comprobar_plugin.py` no ejecuta los `prueba_puntuar.py` de las evaluaciones (importan `modelo`);
  `leer_fuentes.py` sin `--una-fuente` cataloga un `~$x.docx` de Office como fuente; `requiere()` de los puntuadores de
  incoherencias y demo acepta también «Sin…».
- Evaluaciones de la Tarea 22, puntos de fricción:
  - en una sesión desatendida, los puntos pendientes de aprobación solo quedan en los informes: no llegan al guion de
    `indice.py pendientes` ni a ningún sitio que lea el cliente;
  - «cada fuente sube 0.1» saca versiones casi vacías cuando no se aplica nada, y un Word por versión aunque no se envíe;
  - falta un tipo de punto para plazos e hitos del proyecto, y no se dice si una pieza 🔒 sigue 🔒 tras un cambio
    aprobado ni cuándo se marca «DF entregado»;
  - `proyecto.py estado` da `--confirmadas` con todas las 🔒, también las que el informe acaba de aprobar;
  - «app-vX.Y.json» no dice si X.Y es la versión del prototipo o la del funcional;
  - un CAMBIA pendiente que respondería a una PC, una PR del DF con dos actores, una pantalla del DF sin requisito: sin
    pauta en «DF ya hecho» («no reinterpretes»);
  - el DF del cliente no trae prioridad ni «para qué», que la plantilla exige;
  - la columna «Qué cambia» de `decisiones.md` sale en el Word y no se vigila la jerga interna allí;
  - `df_docx.js` parte las viñetas de varias líneas, y el índice sale vacío o con una página en blanco en el PDF;
  - revisar el Word en PDF con `soffice` escribe su perfil fuera de `<p>` (`~/.cache/dconf`) si no se le da otro HOME;
  - en evolutivo no se dice si el funcional describe toda la aplicación o solo los cambios, ni cómo escribir un estado
    que la aplicación actual no mantiene;
  - una petición de un sistema (el ERP) no encaja como historia, porque no es un perfil de §2;
  - el BPMN de un proceso de 8-9 tareas pasa de 1.900 px por los avisos dibujados como eventos de mensaje;
  - el temporizador del diagrama siempre es «no interrumpe»;
  - `capture.py` no deja capturar solo las pantallas que cambian.

## Equipo (requisitos, aviso, paquete)

- «PMI» (Project Management Institute) da error como código de un cliente; los códigos de tres letras podrían mirarse
  solo en datos (`*.json`, galerías). Revisión de F7.
- El hook prueba `python3` antes que `python` también en Windows: con el de la Store y el de python.org a la vez,
  comprueba Playwright y pypdf en el primero y la marca calla al segundo. La línea «Detalle» de `--breve` dice
  `python3` aunque solo haya `python`. Revisión de F7.
- Sin verificar: si en Windows con PowerShell Claude Code sustituye `${CLAUDE_PLUGIN_ROOT}` en el texto del comando (la
  prueba lo hace así) o solo la exporta como variable; en el segundo caso el aviso callaría. Lo dirá el Paso 4 de la
  Tarea 24 si se prueba en un Windows. Revisión de F7.
- El Dev MCP se busca en la carpeta de la primera sesión: quien lo tiene configurado en otro proyecto recibe una vez
  por versión «falta Dev MCP». Revisión de F7.
- La matriz de GitHub avisa de que las acciones de Node 20 están obsoletas (checkout, setup-python, setup-node,
  setup-uv): subir de versión cuando haya las de Node 24.
