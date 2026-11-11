---
name: appian-actualizacion
description: "Actualización del Dev MCP de Appian: cada bundle trae a la vez el servidor MCP, la skill oficial appian y SAIL CLI. Instala un bundle descargado como manda la guía de Appian, guardando antes una foto de lo instalado y el bundle anterior, y después dice qué cambió: herramientas nuevas, desaparecidas o con otros parámetros, ficheros de la skill oficial y órdenes y opciones de SAIL CLI, y qué partes del plugin citan lo que cambió, para releerlas. Úsala cuando salga un bundle nuevo del Dev MCP, cuando el Dev MCP rechace las llamadas porque el servidor y el plugin de Appian son de builds distintos, para saber qué versión hay instalada o para seguir con el SAIL CLI anterior. No construye, revisa ni diagnostica objetos (appian-best-practices), no prueba una unidad construida (appian-qa) y no documenta una aplicación (appian-reverse-engineering)."
---

# Actualización del Dev MCP · Appian

Appian publica el Dev MCP en un bundle que trae tres piezas a la vez: el servidor MCP, la skill oficial `appian` y
SAIL CLI (`sail`). Sale uno nuevo casi cada semana. Cuando el plugin de Appian del entorno se actualiza, el servidor
local deja de valer: mientras no sean del mismo build, el Dev MCP rechaza todas las llamadas.

## Qué hace y qué no

- Dice qué hay instalado y si un bundle descargado es más nuevo.
- Instala el bundle como manda la guía de Appian. Antes guarda una foto de lo instalado y el bundle anterior, que
  Appian no guarda.
- Tras instalar, dice qué cambió entre la foto y lo instalado, y qué ficheros del plugin citan lo que cambió.
- Saca el SAIL CLI del bundle anterior, para seguir con él si el nuevo da problemas.

El informe dice **qué cambió**, no qué se rompió, y no decide qué hacer con cada cambio: eso es leerlo (paso 4). El
servidor no se puede volver atrás: tiene que ser del mismo build que el plugin de Appian del entorno.

## Requisitos

Antes de la primera tarea: `python3 <skill>/../../requisitos.py --skill appian-actualizacion`. Solo pide Python. Para
instalar hace falta además `uv`, como pide la guía de Appian; si no está, el script lo dice antes de tocar nada.

## Flujo

`<skill>` es la carpeta de esta skill. Si el bundle no está extraído en `~/appian-dev-mcp-server`, que es donde manda
la guía de Appian, añade `--servidor <carpeta>` a cada orden.

1. **Qué hay.** `python3 <skill>/scripts/actualizar.py estado [--bundle <descarga>]`: el build del servidor, la versión
   de SAIL CLI y de la skill oficial, y si el bundle descargado es más nuevo, el instalado o más antiguo. La versión
   del plugin de Appian de cada entorno la da el Dev MCP: la herramienta que informa de las versiones responde aunque
   las demás se rechacen, y dice el `mcpSrcSha` que espera. El bundle lo descarga la persona, con su sesión, de
   `https://<su entorno>/suite/plugins/servlet/stateless/downloads`.
2. **Instalar**, con el visto bueno de la persona, porque sustituye el servidor:
   `python3 <skill>/scripts/actualizar.py instalar <descarga> --plugin-sha <mcpSrcSha>`. Primero comprueba, sin tocar
   nada, que el bundle vale; después hace la foto de lo instalado y guarda el bundle anterior; y solo entonces
   sustituye lo que trae el bundle y lanza `uv sync`, el instalador de SAIL CLI y el de la skill oficial. Con
   `--skills-dir <carpeta>` instala la skill también en un cliente de IA que el instalador de Appian no detecta. Si
   un paso falla, dice cuál y la misma orden se puede repetir.
3. **Reiniciar los clientes de IA.** Hasta entonces la sesión sigue hablando con el servidor anterior y el Dev MCP
   sigue rechazando las llamadas.
4. **Qué cambió**: `python3 <skill>/scripts/actualizar.py informe`. Compara la foto del build anterior con lo instalado.
   Léelo y reparte cada cambio:
   - **Puede romper**: una herramienta que el plugin cita ha desaparecido o exige otra cosa, o una orden de SAIL CLI
     cambia de opciones o de conducta. Se prueba antes de fiarse.
   - **Cambió algo que el plugin documenta**: relee los ficheros que da «Lo citan las skills del plugin» y lo que
     dicen de esa herramienta.
   - **Nuevo**: si se usa sin cambiar nada, no hay nada que hacer; si una skill debería usarlo, apúntalo.
5. **Si el SAIL CLI nuevo da problemas**: `python3 <skill>/scripts/actualizar.py sail-anterior` saca el del bundle
   anterior y dice cómo seguir con él (`SAIL_CLI`), hasta que el plugin se adapte.

El catálogo de herramientas entra en la foto cuando se le da (`--catalogo <fichero.json>`). Sin él, el informe compara
la skill oficial y SAIL CLI, y lo dice. Una foto suelta, sin instalar: `actualizar.py foto`.

Un arreglo que hayas hecho a mano dentro de la carpeta del servidor se pierde al instalar: queda en el bundle
anterior guardado.

## Qué escribe

Nada en `<p>`. Al instalar, lo que trae el bundle en la carpeta del servidor (lo demás de esa carpeta no se toca) y,
con los instaladores de Appian, `sail` y la skill oficial de cada cliente. En la carpeta personal de quien lo lanza,
`~/.appian-analisis-funcional/actualizaciones/`, una carpeta por instalación y build con la foto (una copia de
`BUILD-INFO.txt`, del manifiesto de la skill oficial y de la ayuda de cada orden de SAIL CLI) y, en la del último
build anterior, su `bundle.tar.gz`.

## Recursos

| Fichero | Cuándo |
|---|---|
| `scripts/actualizar.py` | `estado`, `instalar`, `informe`, `sail-anterior` y `foto`; su cabecera dice qué lleva una foto y los códigos de salida |
| `assets/banco/especificacion.md` | Para construir, una vez por entorno, la aplicación ficticia con la que se prueba cada versión de SAIL CLI y del Dev MCP |
