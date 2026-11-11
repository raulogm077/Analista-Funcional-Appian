---
name: appian-actualizacion
description: "Actualización del Dev MCP de Appian: cada bundle trae a la vez el servidor MCP, la skill oficial appian y SAIL CLI. Dice qué hay instalado y, tras instalar un bundle nuevo, qué cambió: herramientas nuevas, desaparecidas o con otros parámetros, ficheros de la skill oficial y órdenes y opciones de SAIL CLI, y qué partes del plugin citan lo que cambió, para releerlas. Guarda una foto de lo instalado antes de cada actualización. Úsala cuando salga un bundle nuevo del Dev MCP, cuando el Dev MCP rechace las llamadas porque el servidor y el plugin de Appian son de builds distintos, antes y después de instalarlo, o para saber qué versión hay instalada. No construye, revisa ni diagnostica objetos (appian-best-practices), no prueba una unidad construida (appian-qa) y no documenta una aplicación (appian-reverse-engineering)."
---

# Actualización del Dev MCP · Appian

Appian publica el Dev MCP en un bundle que trae tres piezas a la vez: el servidor MCP, la skill oficial `appian` y
SAIL CLI (`sail`). Sale uno nuevo casi cada semana. Cuando el plugin de Appian del entorno se actualiza, el servidor
local deja de valer: mientras no sean del mismo build, el Dev MCP rechaza todas las llamadas.

## Qué hace y qué no

- Dice qué hay instalado y si un bundle descargado es más nuevo.
- Guarda una foto de lo instalado antes de instalar otro bundle.
- Tras instalar, dice qué cambió entre la foto y lo instalado, y qué ficheros del plugin citan lo que cambió.

El informe dice **qué cambió**, no qué se rompió. No decide por ti qué hacer con cada cambio: eso es leerlo (paso 4).

## Requisitos

Antes de la primera tarea: `python3 <skill>/../../requisitos.py --skill appian-actualizacion`. Solo pide Python. SAIL
CLI y el servidor del Dev MCP son lo que se actualiza: si falta alguno, el script lo dice y sigue con lo que hay.

## Flujo

`<skill>` es la carpeta de esta skill. Si el bundle no está extraído en `~/appian-dev-mcp-server`, que es donde manda
la guía de Appian, añade `--servidor <carpeta>` a cada orden.

1. **Qué hay.** `python3 <skill>/scripts/actualizar.py estado [--bundle <descarga>]`: el build del servidor, la versión
   de SAIL CLI y de la skill oficial, y si el bundle descargado es más nuevo, el instalado o más antiguo. La versión
   del plugin de Appian de cada entorno la da el Dev MCP: la herramienta que informa de las versiones responde aunque
   las demás se rechacen. El bundle lo descarga la persona, con su sesión, de
   `https://<su entorno>/suite/plugins/servlet/stateless/downloads`.
2. **Foto de antes**, con lo instalado todavía sin tocar: `python3 <skill>/scripts/actualizar.py foto`. Appian no
   guarda la versión anterior y el navegador suele pisar la descarga vieja: guarda también el bundle anterior.
3. **Instalar**, como dice la guía de Appian (`https://docs.appian.com/suite/help/latest/devmcp.html`): extraer el
   bundle en la carpeta del servidor, `uv sync`, el `bin/setup-*` de tu sistema (deja `sail` en el PATH) y
   `bin/install-skills` (la skill oficial en cada cliente de IA). Después, **reinicia tus clientes de IA**: hasta
   entonces la sesión sigue hablando con el servidor anterior.
4. **Qué cambió**: `python3 <skill>/scripts/actualizar.py informe`. Compara la foto del build anterior con lo instalado.
   Léelo y reparte cada cambio:
   - **Puede romper**: una herramienta que el plugin cita ha desaparecido o exige otra cosa, o una orden de SAIL CLI
     cambia de opciones o de conducta. Se prueba antes de fiarse.
   - **Cambió algo que el plugin documenta**: relee los ficheros que da «Lo citan las skills del plugin» y lo que
     dicen de esa herramienta.
   - **Nuevo**: si se usa sin cambiar nada, no hay nada que hacer; si una skill debería usarlo, apúntalo.

El catálogo de herramientas entra en la foto cuando se le da (`--catalogo <fichero.json>`). Sin él, el informe compara
la skill oficial y SAIL CLI, y lo dice.

## Qué escribe

Nada en `<p>`. En la carpeta personal de quien lo lanza, `~/.appian-analisis-funcional/actualizaciones/`, una carpeta
por instalación y build con la foto: una copia de `BUILD-INFO.txt`, del manifiesto de la skill oficial y de la ayuda
de cada orden de SAIL CLI.

## Recursos

| Fichero | Cuándo |
|---|---|
| `scripts/actualizar.py` | `estado`, `foto` e `informe`; su cabecera dice qué lleva una foto y los códigos de salida |
| `assets/banco/especificacion.md` | Para construir, una vez por entorno, la aplicación ficticia con la que se prueba cada versión de SAIL CLI y del Dev MCP |
