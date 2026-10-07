# Primera ejecución contra un Appian real

La skill se ha probado con un Dev MCP simulado. Antes de documentar una aplicación grande, haz esta comprobación sobre una aplicación pequeña de un entorno que no sea producción. Todo es de solo lectura.

Las órdenes se ejecutan desde tu carpeta (donde está tu `.mcp.json`), con la ruta absoluta de la skill en lugar de `<skill>`.

## 1. Estado de los 3 MCP

```
uv run --no-project --with "mcp>=1.2,<2" python "<skill>/scripts/devmcp_extract.py" doctor
```

- Dev MCP en `ok`. Si no, el código de salida dice qué falta (11 sin configuración, 12 varias configuraciones, 13 no arranca o no autentica) y `references/devmcp-setup.md` cómo arreglarlo.
- Si aparece el aviso «El servidor expone herramientas de escritura aunque se pidió readonly», para: la versión del Dev MCP no respeta `LCP_TOOL_MODE=readonly`. La skill no llamará a esas herramientas (el modo pasa a estricto), pero conviene saberlo.

## 2. Plan, sin extraer nada

```
uv run --no-project --with "mcp>=1.2,<2" python "<skill>/scripts/devmcp_extract.py" apps
uv run --no-project --with "mcp>=1.2,<2" python "<skill>/scripts/devmcp_extract.py" plan --app <prefijo> --out ./appian-docs/<prefijo>
```

Revisa la lista de herramientas (`USA` / `NO`) y `appian-docs/_trabajo/<prefijo>/extraction_plan.json`:

- [ ] Ninguna herramienta de escritura figura como `USA`.
- [ ] Ninguna herramienta que lea filas de datos, usuarios o variables de procesos figura como `USA`.
- [ ] Las herramientas de definición de cada tipo de objeto figuran como `USA` (si una sale `NO` por «verbo desconocido», la clasificación por firma no la reconoce: revisa `scripts/devmcp_policy.json`).
- [ ] Los objetos por tipo cuadran con lo que ves en Appian Designer.
- [ ] Las llamadas estimadas son razonables para el tamaño de la aplicación.

## 3. Extracción y revisión de lo extraído

```
uv run --no-project --with "mcp>=1.2,<2" python "<skill>/scripts/devmcp_extract.py" extract --app <prefijo> --out ./appian-docs/<prefijo>
```

- [ ] `extraction_report.json`: en `callStatsByRole.definition`, menos del 20 % de llamadas fallidas; mira el motivo de las herramientas desactivadas.
- [ ] Abre 2 o 3 respuestas de `mcp_raw/` (una interfaz, un process model, un record type) y comprueba que traen la definición.
- [ ] `python3 "<skill>/scripts/detect_secrets.py" appian-docs/_trabajo/<prefijo>/mcp_raw`: si algo sale, los entregables dicen dónde está sin reproducirlo.

## 4. Documentación

Pide a Claude «documenta la aplicación <prefijo>» y sigue las fases de `SKILL.md`. Al terminar:

- [ ] Ningún nombre de usuario en `appian-docs/<prefijo>/` (la carpeta `_trabajo/` no se comparte).
- [ ] Contrasta 3 o 4 afirmaciones de `01` y `08` con Appian Designer.
- [ ] Abre un `.bpmn` de `08-procesos-bpmn/` en https://demo.bpmn.io.

Si algo no cuadra con el Dev MCP real (nombres de campos distintos, herramientas nuevas), anótalo: es lo que hay que ajustar en `references/lectura-mcp-raw.md` o en la política.
