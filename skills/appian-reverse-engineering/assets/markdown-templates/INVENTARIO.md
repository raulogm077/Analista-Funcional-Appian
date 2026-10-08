<!--
  Plantilla INVENTARIO — Todos los objetos de la aplicación (orquestador, fase 6).
  Fuentes: <trabajo>/inventory.json (objetos y campos derivados), graph.json («Llamado por»: aristas entrantes),
  extraction_report.json y preflight.json (cobertura). Cubre el 100 % de inventory.json.
  Una sección por tipo presente en `counts` (también los que esta plantilla no prevé, en «Otros tipos»);
  omite las secciones de tipos sin objetos. Sin límite de filas; ≤ 8 columnas y celdas ≤ 100 caracteres.
  - uuid: tal cual, entre comillas invertidas (INVENTARIO y anexo/ son los únicos sitios con uuids).
  - Nombre: enlaza su ficha en el documento propietario cuando la tiene: process model → 08-procesos-bpmn/<slug>.md;
    record type, CDT y data store → 03; integración y connected system → 05; Web API → 06; grupo → 04; interfaz que es
    pantalla → su PAN de 10; regla o decisión que implementa una RN → su RN de 11; constante de entorno → 09.
    Sin documento propietario, el nombre va sin enlace.
  - Ficha: [anexo](./anexo/<tipo>/<slug>.md) si existe ese fichero (el anexo lo crea para todo objeto con alguna respuesta, aunque no tenga definición); si no, «—».
  - Para qué: la `description` de Appian, literal y recortada a 100 caracteres. Si el objeto no tiene descripción en
    Appian (o la extracción no la trae), una frase deducida de su nombre, su uso o su documento propietario, que
    empieza por 🔵 (p. ej. «🔵 según su nombre, plantilla del correo de aviso»).
-->

# Inventario de la aplicación

> **TL;DR**: {{N}} objetos de {{N}} tipos; {{N}} de {{N}} ({{%}}, sin contar carpetas: `meta.coverage` de summary.json) con definición. Cada objeto con definición enlaza su ficha del anexo, con la definición original.
> **Volumen**: {{n}} process models · {{n}} interfaces · {{n}} reglas · {{n}} record types · {{n}} otros. {{N}} objetos sin definición (ver [Cobertura](#cobertura-de-la-extracción)).

**Aplicación:** {{nombre visible}} (prefijo `{{prefijo}}`, uuid `{{uuid de la aplicación}}`)
**Fuente:** entorno `{{url}}`, extraído el {{AAAA-MM-DD}} en solo lectura

Cómo leer las tablas:

- **Nombre**: enlaza el documento que explica el objeto, si lo tiene.
- **Ficha**: la definición original del objeto y el resto de respuestas de la plataforma en el [anexo](./anexo/indice.md). «—»: la extracción no trajo nada de ese objeto.
- **Para qué**: la descripción que tiene el objeto en Appian. Si no la tiene (o el Dev MCP no la devuelve para ese tipo), una frase deducida, marcada 🔵.
- **Llamado por**: objetos que lo referencian según el grafo de la aplicación. Puede ser mayor que lo que muestra la herramienta de dependientes de Appian, porque también cuenta las referencias encontradas en las definiciones.

## Conteo por tipo

| Tipo | Objetos | Con definición | Sin definición |
|---|---|---|---|
| {{Record types}} | {{N}} | {{N}} | {{N}} |
| {{Interfaces}} | {{N}} | {{N}} | {{N}} |
| **Total** | **{{N}}** | **{{N}}** | **{{N}}** |

## Record types

| Nombre | uuid | Origen | Tabla | Campos | Filas | Para qué | Ficha |
|---|---|---|---|---|---|---|---|
| [`{{nombre}}`](./03-modelo-datos.md#{{ancla}}) | `{{uuid}}` | {{sourceType}} | `{{tableName}}` | {{fieldCount}} | {{count de data fabric o «—»}} | {{descripción o «🔵 frase deducida»}} | [anexo](./anexo/recordType/{{slug}}.md) |

## CDTs

| Nombre | uuid | Llamado por | Para qué | Ficha |
|---|---|---|---|---|
| [`{{nombre}}`](./03-modelo-datos.md#{{ancla}}) | `{{uuid}}` | {{N}} | {{descripción o «🔵 frase deducida»}} | {{[anexo](./anexo/cdt/{{slug}}.md) o «—»}} |

## Process models

| Nombre | uuid | Inicio | Nodos | Tareas humanas | Ejecuciones | Para qué | Ficha |
|---|---|---|---|---|---|---|---|
| [`{{nombre}}`](./08-procesos-bpmn/{{slug}}.md) | `{{uuid}}` | {{Manual / Temporizador / Mensaje / Subproceso}} | {{N}} | {{N}} | {{N o «—»}} | {{descripción o «🔵 frase deducida»}} | [anexo](./anexo/processModel/{{slug}}.md) |

## Interfaces

| Nombre | uuid | Pantalla | Líneas | Avisos de validación | Para qué | Ficha |
|---|---|---|---|---|---|---|
| [`{{nombre}}`](./10-pantallas.md#{{ancla}}) o `{{nombre}}` | `{{uuid}}` | {{PAN-001 o «—»}} | {{sailLines}} | {{N}} | {{descripción o «🔵 frase deducida»}} | [anexo](./anexo/interface/{{slug}}.md) |

## Expression rules

| Nombre | uuid | Líneas | Llamado por | Para qué | Ficha |
|---|---|---|---|---|---|
| [`{{nombre}}`](./11-reglas-negocio.md#{{ancla}}) o `{{nombre}}` | `{{uuid}}` | {{sailLines}} | {{N}} | {{descripción o «🔵 frase deducida»}} | [anexo](./anexo/expressionRule/{{slug}}.md) |

## Decisiones

| Nombre | uuid | Llamado por | Para qué | Ficha |
|---|---|---|---|---|
| [`{{nombre}}`](./11-reglas-negocio.md#{{ancla}}) o `{{nombre}}` | `{{uuid}}` | {{N}} | {{descripción o «🔵 frase deducida»}} | {{[anexo](./anexo/decision/{{slug}}.md) o «—»}} |

## Integraciones

| Nombre | uuid | Método | Endpoint | Connected system | Modifica datos | Para qué | Ficha |
|---|---|---|---|---|---|---|---|
| [`{{nombre}}`](./05-integraciones-consumidas.md#{{ancla}}) | `{{uuid}}` | {{GET}} | `{{ruta relativa}}` | `{{connected system}}` | {{Sí / No / «—»}} | {{descripción o «🔵 frase deducida»}} | [anexo](./anexo/integration/{{slug}}.md) |

## Connected systems

| Nombre | uuid | Tipo | URL base | Autenticación | Para qué | Ficha |
|---|---|---|---|---|---|---|
| [`{{nombre}}`](./05-integraciones-consumidas.md#{{ancla}}) | `{{uuid}}` | {{csType}} | `{{URL base}}` | {{authType o «—»}} | {{descripción o «🔵 frase deducida»}} | [anexo](./anexo/connectedSystem/{{slug}}.md) |

## Web APIs

| Nombre | uuid | Método | Endpoint | Para qué | Ficha |
|---|---|---|---|---|---|
| [`{{nombre}}`](./06-apis-expuestas.md#{{ancla}}) | `{{uuid}}` | {{POST}} | `/suite/webapi/{{endpointPath}}` | {{descripción o «🔵 frase deducida»}} | [anexo](./anexo/webApi/{{slug}}.md) |

## Sites

| Nombre | uuid | URL | Páginas | Para qué | Ficha |
|---|---|---|---|---|---|
| `{{nombre}}` | `{{uuid}}` | `/sites/{{urlStub}}` | {{pageCount}} | {{descripción o «🔵 frase deducida»}} | [anexo](./anexo/site/{{slug}}.md) |

## Grupos

| Nombre | uuid | Tipo | Grupo padre | Grupos miembro | Usuarios directos | Para qué | Ficha |
|---|---|---|---|---|---|---|---|
| [`{{nombre}}`](./04-seguridad-grupos.md#vista) | `{{uuid}}` | {{groupType}} | `{{padre}}` o «—» | {{lista o «—»}} | {{userCount}} | {{descripción o «🔵 frase deducida»}} | [anexo](./anexo/group/{{slug}}.md) |

## Constantes

| Nombre | uuid | Tipo | Valor | Referencia | Para qué | Ficha |
|---|---|---|---|---|---|---|
| `{{nombre}}` o [`{{nombre}}`](./09-valor-adicional.md#constantes-por-entorno-y-secretos) | `{{uuid}}` | {{typeRef}} | `{{valor}}` | {{valueRef o «—»}} | {{descripción o «🔵 frase deducida»}} | [anexo](./anexo/constant/{{slug}}.md) |

## Otros tipos

Una tabla por cada tipo restante de `counts` (carpetas, documentos, agentes de IA, tipos nuevos…):

| Nombre | uuid | Para qué | Ficha |
|---|---|---|---|
| `{{nombre}}` | `{{uuid}}` | {{descripción o «🔵 frase deducida»}} | {{[anexo](./anexo/{{tipo}}/{{slug}}.md) o «—»}} |

## Cobertura de la extracción

| Métrica | Valor |
|---|---|
| Objetos de la aplicación | {{N}} |
| Con definición | {{N}} ({{%}}) |
| Herramientas del Dev MCP usadas | {{N}} |
| Herramientas excluidas por seguridad | {{N}} |
| Llamadas con error | {{N}} |
| Herramientas desactivadas para un tipo tras fallar | {{tipo: herramienta, … o «ninguna»}} |
| Appian MCP Server (volúmenes) | {{Disponible / No disponible}} |
| Docs MCP (documentación oficial) | {{Disponible / No disponible}} |

### Objetos sin definición

| Objeto | Tipo | Motivo |
|---|---|---|
| `{{nombre}}` | {{tipo}} | {{el Dev MCP no tiene herramienta de definición para este tipo / la llamada falló}} |

{{Anomalías, si las hay, en 1-3 líneas: tipos desconocidos, objetos de otras aplicaciones referenciados, errores de extracción relevantes.}}
