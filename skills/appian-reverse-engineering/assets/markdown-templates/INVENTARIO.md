<!--
  Plantilla INVENTARIO — Inventario completo por tipo de objeto
  Debe cubrir el 100% de los objetos de la aplicación (inventory.json).
  Lo genera el orquestador en la fase 6 a partir de <trabajo>/inventory.json y extraction_report.json.
  Una sección por tipo presente en counts, incluidos tipos que la skill no conozca (se listan igual).
-->

# Inventario de la aplicación

**Aplicación:** {{nombre_visible}} (prefijo `{{prefijo}}`, uuid `{{uuid_app}}`)
**Fuente:** Appian Dev MCP · entorno `{{url_entorno}}` · extraído el {{fecha_extraccion}} (solo lectura)
**Fecha de análisis:** {{fecha_iso}}

## Conteo por tipo

> Una fila por clave de `counts` en `inventory.json`, con el nombre legible del tipo.

| Tipo de objeto | Cantidad | Con definición | Sin definición (🟡) |
|---|---|---|---|
| {{Record Types}} | {{N}} | {{N}} | {{N}} |
| {{Interfaces}} | {{N}} | {{N}} | {{N}} |
| {{...}} | | | |
| **Total** | **{{TOTAL}}** | | |

## Records / Record Types

| Nombre | Origen de datos | Tabla | Campos | Filas (data fabric) | Descripción | Última modificación |
|---|---|---|---|---|---|---|
| `{{rt_1}}` | {{sourceType}} | `{{tableName}}` | {{fieldCount}} | {{count o —}} | {{desc}} | {{lastModifiedOn}} |

## CDTs

| Nombre | Definición | Usado por |
|---|---|---|
| `{{cdt_1}}` | ✅ / 🟡 no disponible por Dev MCP | {{objetos que lo referencian}} |

## Process Models

| Nombre | Inicio | Nodos | Tareas humanas | Ejecuciones reales | Última ejecución |
|---|---|---|---|---|---|
| `{{pm_1}}` | none/timer/message | {{n}} | {{n}} | {{N o —}} | {{fecha o —}} |

## Interfaces

| Nombre | Pantalla (`PAN-xxx`) | Tamaño SAIL | Avisos de validación | Descripción |
|---|---|---|---|---|
| `{{if_1}}` | {{PAN-001 o —}} | {{sailBytes}} | {{N}} | {{desc}} |

## Expression Rules

| Nombre | Tamaño SAIL | Llamada por | Descripción |
|---|---|---|---|
| `{{rule_1}}` | {{sailBytes}} | {{N objetos}} | {{desc}} |

## Decisions

| Nombre | Definición | Descripción |
|---|---|---|
| `{{decision_1}}` | ✅ / 🟡 | {{desc}} |

## Integrations

| Nombre | Método | Endpoint (enmascarado) | Connected System | Modifica datos |
|---|---|---|---|---|
| `{{int_1}}` | {{verb}} | `{{endpoint}}` | `{{cs}}` | Sí/No |

## Connected Systems

| Nombre | Tipo | Base URL (enmascarada) | Autenticación |
|---|---|---|---|
| `{{cs_1}}` | HTTP/OAuth/… | `{{url}}` | {{auth_type}} |

## Web APIs

| Nombre | Método | Endpoint | Descripción |
|---|---|---|---|
| `{{wa_1}}` | {{verb}} | `/suite/webapi/{{path}}` | {{desc}} |

## Sites

| Nombre | URL | Páginas |
|---|---|---|
| `{{site_1}}` | `/sites/{{urlStub}}` | {{n}} |

## Groups

| Nombre | Tipo | Padre | Grupos miembro | Nº de usuarios |
|---|---|---|---|---|
| `{{grupo_1}}` | {{groupType}} | `{{padre_o_vacio}}` | {{lista}} | {{userCount}} |

## Constants

| Nombre | Tipo | Valor | Referencia |
|---|---|---|---|
| `{{cons_1}}` | TEXT/GROUP/PROCESS_MODEL/… | `{{valor_o_🔒}}` | {{valueRef o —}} |

## Otros tipos

> Un apartado por cada tipo restante de `counts` (carpetas, documentos, agentes de IA, tipos nuevos…), con nombre y descripción.

## Cobertura de la extracción

| Métrica | Valor |
|---|---|
| Objetos listados por la aplicación | {{N}} |
| Objetos con definición | {{N}} |
| Objetos sin definición (tipo sin herramienta o error) | {{N}} |
| Herramientas del Dev MCP usadas | {{N}} (ver `extraction_report.json`) |
| Herramientas excluidas por seguridad | {{N}} |
| Llamadas con error | {{N}} |
| Herramientas desactivadas por tipo tras fallar | {{lista tipo/herramienta}} |
| Appian MCP Server (volúmenes) | disponible / no disponible |
| Docs MCP | disponible / no disponible |

### Objetos sin definición

{{Lista `nombre (tipo) — motivo`. Si está vacía, escribir "Ninguno".}}

## Notas del inventario

- {{Anomalías: tipos desconocidos, errores de extracción relevantes, objetos externos a la aplicación referenciados.}}
- {{Si todo cuadra, escribir: "Inventario consistente. 100% de los objetos cubiertos."}}
