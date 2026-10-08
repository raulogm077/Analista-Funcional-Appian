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
- 09, «Configuración por entorno»: la columna «Por entorno» dice si la constante tiene la marca de Appian, y un lector
  entiende que su valor no cambia por entorno (Q-10 de la evaluación de F3). Separar las dos cosas.
- Guía de 09 en `analysis-workflow.md`: una misma señal sale en dos hallazgos (validación y más de 50 nodos; huérfano y
  sin ejecuciones), contra «un dueño por señal». Medida «después» de F3.
- Pasada de coherencia: ningún script comprueba que cada mención de otra área lleve su ID canónico. Medida «después» de F3.
- `build_datos.py` cuenta 80 aristas y `summary.json` 83 (las de fuera de la aplicación): decirlo en `datos.md`.
- `security-rules.md`: decir que el valor de un secreto se reproduce tal cual (nada se oculta) y dónde acaba (04,
  registro de 09, `datos/hallazgos.json`).
- Las URL de la documentación de Appian con versión fija (`/help/26.6/`) en `references/data-fabric.md`,
  `devmcp-setup.md` y `agents/data-modeler.md`, frente a `/latest/` de la regla «Dudas de Appian»: son del Appian MCP
  Server, que depende de la versión; revisar al cambiar de versión. Paso 3 de la Tarea 9.
