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
