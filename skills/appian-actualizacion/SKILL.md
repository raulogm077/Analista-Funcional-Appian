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
- Comprueba, con una aplicación de prueba, que el extractor de ingeniería inversa sigue viéndolo todo y que `qa.py`
  sigue repitiendo sus guiones con el SAIL CLI nuevo.
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
   nada, que el bundle vale, y lo extrae aparte; después hace la foto de lo instalado y guarda el bundle anterior; y
   solo entonces sustituye lo que trae el bundle y lanza `uv sync`, el instalador de SAIL CLI y el de la skill
   oficial. Con `--skills-dir <carpeta>` instala la skill también en un cliente de IA que el instalador de Appian no
   detecta. Esos pasos no dependen uno de otro: se hacen todos y, si alguno falla, dice cuál (por ejemplo, SAIL CLI
   en un equipo para el que el bundle no trae su binario) y la misma orden se puede repetir. Un bundle con otra forma que
   la que conoce el script no se instala: se instala a mano con la guía de Appian y se avisa a quien mantiene el
   plugin.
3. **Reiniciar los clientes de IA.** Hasta entonces la sesión sigue hablando con el servidor anterior y el Dev MCP
   sigue rechazando las llamadas.
4. **Qué cambió**: `python3 <skill>/scripts/actualizar.py informe`. Compara la foto del build anterior con lo instalado.
   Léelo y reparte cada cambio:
   - **Puede romper**: una herramienta que el plugin cita ha desaparecido o exige otra cosa, o una orden de SAIL CLI
     cambia de opciones o de conducta. Se prueba antes de fiarse.
   - **Cambió algo que el plugin documenta**: relee los ficheros que da «Lo citan las skills del plugin» y lo que
     dicen de esa herramienta.
   - **Nuevo**: si se usa sin cambiar nada, no hay nada que hacer; si una skill debería usarlo, apúntalo.
5. **¿Sigue funcionando el plugin?** Con la aplicación del banco construida en tu entorno
   (`assets/banco/especificacion.md`), `python3 <skill>/scripts/actualizar.py comprobar` pasa sus dos mitades, juntas
   o por separado:
   - **El extractor**, con `--extraccion <carpeta>`: antes extrae la aplicación del banco con el extractor de
     `appian-reverse-engineering` (`devmcp_extract.py extract --app <la del banco> --out <carpeta temporal>`). No pasa
     si faltan objetos de algún tipo, si el modelo que el extractor arma con las respuestas no dice lo que dice la
     especificación (campos, relaciones, tareas, valores) o si hay errores fuera de los que Appian da siempre en esa
     aplicación. Una herramienta con errores en todos los tipos de objeto suele ser de un tipo que la política del
     extractor no conoce. Esa misma extracción deja el catálogo para el informe.
   - **`qa.py` con SAIL CLI**, con `--host <tu entorno> --solicitante <usuario> --aprobador <usuario>`: repite los
     guiones del banco con `qa.py`, de `appian-qa`, con las dos cuentas de prueba que le das, que tienen que tener
     su sesión de `sail` abierta (`qa.py sesiones` dice cómo). Crean sus propias solicitudes, con un título
     distinto cada vez. El banco aún no trae el recorrido de la tarea del grupo, y lo dice.

   Sale con 0 si pasa lo pedido, 1 si algo no pasa y 2 si algo no se pudo comprobar (una sesión caducada, una
   extracción que no terminó): eso no es un fallo, pero tampoco un «pasa».
6. **Si el SAIL CLI nuevo da problemas**: `python3 <skill>/scripts/actualizar.py sail-anterior` saca el del bundle
   anterior y dice cómo seguir con él (`SAIL_CLI`), hasta que el plugin se adapte.

**El catálogo de herramientas** entra en la foto cuando se le da, con `--catalogo <fichero>`. Lo deja el extractor de
`appian-reverse-engineering` al planificar cualquier aplicación del entorno, con el servidor ya reiniciado:
`devmcp_extract.py plan --app <una aplicación> --out <carpeta temporal>` escribe `extraccion/mcp_catalog.json`, y ese
fichero es el que se pasa. Hazlo en el paso 4, con `informe --catalogo`: esa foto es la de antes en la siguiente
actualización. Sin catálogo, el informe compara la skill oficial y SAIL CLI, y lo dice. La foto de un build se hace
una vez; `actualizar.py foto` la rehace entera.

Una instalación nueva no acaba ahí: la guía de Appian (`https://docs.appian.com/suite/help/latest/devmcp.html`) dice
cómo dar de alta el servidor en cada cliente de IA y, si se entra por navegador, que es lo habitual, cómo tener el
navegador que usa el servidor (el suyo, que se descarga una vez, o el Chrome o Edge del equipo). Al actualizar no hay
que repetirlo; si después el servidor pide ese navegador, la misma guía.

Un arreglo que hayas hecho a mano en lo que trae el bundle se pierde al instalar. Al actualizar queda en el bundle
anterior guardado; al repetir la instalación del mismo bundle, no. Mientras se instala no debe haber otra instalación
en marcha sobre la misma carpeta.

## Qué escribe

Nada en `<p>`. Al instalar, lo que trae el bundle en la carpeta del servidor (lo demás de esa carpeta no se toca) y,
con los instaladores de Appian, `sail` y la skill oficial de cada cliente. En la carpeta personal de quien lo lanza,
`~/.appian-analisis-funcional/actualizaciones/`, una carpeta por instalación y build con la foto (una copia de
`BUILD-INFO.txt`, del manifiesto de la skill oficial y de la ayuda de cada orden de SAIL CLI) y, en la del último
build anterior, su `bundle.tar.gz`.

## Recursos

| Fichero | Cuándo |
|---|---|
| `scripts/actualizar.py` | `estado`, `instalar`, `informe`, `comprobar`, `sail-anterior` y `foto`; su cabecera dice qué lleva una foto y los códigos de salida |
| `assets/banco/especificacion.md` | Para construir, una vez por entorno, la aplicación ficticia con la que se prueba cada versión de SAIL CLI y del Dev MCP |
| `assets/banco/esperado.json` | Lo que el extractor tiene que encontrar en esa aplicación; lo lee `comprobar` |
| `assets/banco/guiones/` | Los recorridos del banco, como guiones de `appian-qa` sin entorno ni cuentas; los repite `comprobar` |
