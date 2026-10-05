<!--
  Plantilla INVENTARIO — Todos los objetos de la aplicación (orquestador, fase 6).
  Fuentes: <trabajo>/inventory.json (objetos y campos derivados), graph.json («Llamado por»: aristas entrantes),
  extraction_report.json y preflight.json (cobertura). Cubre el 100 % de inventory.json.
  Una sección por tipo presente en `counts` (también los que esta plantilla no prevé, en «Otros tipos»);
  omite las secciones de tipos sin objetos. Sin límite de filas; ≤ 8 columnas y celdas ≤ 100 caracteres.
  - uuid: tal cual, entre comillas invertidas (INVENTARIO y anexo/ son los únicos sitios con uuids).
  - Ficha: [anexo](./anexo/<tipo>/<slug>.md) si existe ese fichero (el anexo lo crea para todo objeto con alguna respuesta, aunque no tenga definición); si no, «—».
  - Descripción: la `description` de Appian, literal y recortada a 100 caracteres. Si la extracción no la trae,
    «—». Nunca un resumen tuyo en esta columna.
  - Sin usuarios: los grupos dan recuentos (`userCount`), nunca nombres.
-->

# Inventario de la aplicación

> **TL;DR**: {{N}} objetos de {{N}} tipos; {{N}} de {{N}} ({{%}}, sin contar carpetas: `meta.coverage` de summary.json) con definición. Cada objeto con definición enlaza su ficha del anexo, con la definición original.
> **Volumen**: {{n}} process models · {{n}} interfaces · {{n}} reglas · {{n}} record types · {{n}} otros. {{N}} objetos sin definición (ver [Cobertura](#cobertura-de-la-extracción)).

**Aplicación:** {{nombre visible}} (prefijo `{{prefijo}}`, uuid `{{uuid de la aplicación}}`)
**Fuente:** entorno `{{url}}`, extraído el {{AAAA-MM-DD}} en solo lectura

Cómo leer las tablas:

- **Ficha**: la definición original del objeto y el resto de respuestas de la plataforma en el [anexo](./anexo/indice.md). «—»: la extracción no trajo nada de ese objeto.
- **Descripción**: la que tiene el objeto en Appian. «—»: la extracción no trae descripción (puede no tenerla o el Dev MCP no devolverla para ese tipo).
- **Llamado por**: objetos que lo referencian según el grafo de la aplicación. Puede ser mayor que lo que muestra la herramienta de dependientes de Appian, porque también cuenta las referencias encontradas en las definiciones.

## Conteo por tipo

| Tipo | Objetos | Con definición | Sin definición |
|---|---|---|---|
| {{Record types}} | {{N}} | {{N}} | {{N}} |
| {{Interfaces}} | {{N}} | {{N}} | {{N}} |
| **Total** | **{{N}}** | **{{N}}** | **{{N}}** |

## Record types

| Nombre | uuid | Origen | Tabla | Campos | Filas | Descripción | Ficha |
|---|---|---|---|---|---|---|---|
| `{{nombre}}` | `{{uuid}}` | {{sourceType}} | `{{tableName}}` | {{fieldCount}} | {{count de data fabric o «—»}} | {{descripción o «—»}} | [anexo](./anexo/recordType/{{slug}}.md) |

## CDTs

| Nombre | uuid | Llamado por | Descripción | Ficha |
|---|---|---|---|---|
| `{{nombre}}` | `{{uuid}}` | {{N}} | {{descripción o «—»}} | {{[anexo](./anexo/cdt/{{slug}}.md) o «—»}} |

## Process models

| Nombre | uuid | Inicio | Nodos | Tareas humanas | Ejecuciones | Descripción | Ficha |
|---|---|---|---|---|---|---|---|
| `{{nombre}}` | `{{uuid}}` | {{Manual / Temporizador / Mensaje / Subproceso}} | {{N}} | {{N}} | {{N o «—»}} | {{descripción o «—»}} | [anexo](./anexo/processModel/{{slug}}.md) |

## Interfaces

| Nombre | uuid | Pantalla | Líneas | Avisos de validación | Descripción | Ficha |
|---|---|---|---|---|---|---|
| `{{nombre}}` | `{{uuid}}` | {{PAN-001 o «—»}} | {{sailLines}} | {{N}} | {{descripción o «—»}} | [anexo](./anexo/interface/{{slug}}.md) |

## Expression rules

| Nombre | uuid | Líneas | Llamado por | Descripción | Ficha |
|---|---|---|---|---|---|
| `{{nombre}}` | `{{uuid}}` | {{sailLines}} | {{N}} | {{descripción o «—»}} | [anexo](./anexo/expressionRule/{{slug}}.md) |

## Decisiones

| Nombre | uuid | Llamado por | Descripción | Ficha |
|---|---|---|---|---|
| `{{nombre}}` | `{{uuid}}` | {{N}} | {{descripción o «—»}} | {{[anexo](./anexo/decision/{{slug}}.md) o «—»}} |

## Integraciones

| Nombre | uuid | Método | Endpoint | Connected system | Modifica datos | Ficha |
|---|---|---|---|---|---|---|
| `{{nombre}}` | `{{uuid}}` | {{GET}} | `{{ruta relativa, sin credenciales}}` | `{{connected system}}` | {{Sí / No / «—»}} | [anexo](./anexo/integration/{{slug}}.md) |

## Connected systems

| Nombre | uuid | Tipo | URL base | Autenticación | Ficha |
|---|---|---|---|---|---|
| `{{nombre}}` | `{{uuid}}` | {{csType}} | `{{URL base, sin credenciales}}` | {{authType o «—»}} | [anexo](./anexo/connectedSystem/{{slug}}.md) |

## Web APIs

| Nombre | uuid | Método | Endpoint | Descripción | Ficha |
|---|---|---|---|---|---|
| `{{nombre}}` | `{{uuid}}` | {{POST}} | `/suite/webapi/{{endpointPath}}` | {{descripción o «—»}} | [anexo](./anexo/webApi/{{slug}}.md) |

## Sites

| Nombre | uuid | URL | Páginas | Ficha |
|---|---|---|---|---|
| `{{nombre}}` | `{{uuid}}` | `/sites/{{urlStub}}` | {{pageCount}} | [anexo](./anexo/site/{{slug}}.md) |

## Grupos

| Nombre | uuid | Tipo | Grupo padre | Grupos miembro | Usuarios directos | Ficha |
|---|---|---|---|---|---|---|
| `{{nombre}}` | `{{uuid}}` | {{groupType}} | `{{padre}}` o «—» | {{lista o «—»}} | {{userCount}} | [anexo](./anexo/group/{{slug}}.md) |

## Constantes

| Nombre | uuid | Tipo | Valor | Referencia | Ficha |
|---|---|---|---|---|---|
| `{{nombre}}` | `{{uuid}}` | {{typeRef}} | `{{valor}}` o «enmascarado» | {{valueRef o «—»}} | [anexo](./anexo/constant/{{slug}}.md) |

## Otros tipos

Una tabla por cada tipo restante de `counts` (carpetas, documentos, agentes de IA, tipos nuevos…):

| Nombre | uuid | Descripción | Ficha |
|---|---|---|---|
| `{{nombre}}` | `{{uuid}}` | {{descripción o «—»}} | {{[anexo](./anexo/{{tipo}}/{{slug}}.md) o «—»}} |

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
