<!--
  Plantilla LEEME — Guía de lectura de la documentación (la genera el orquestador al final)
-->

# {{Nombre de la aplicación}} — Documentación de reingeniería

**Generada el** {{fecha}} a partir del entorno `{{url_entorno}}` (lectura en vivo con Appian Dev MCP, sin cambios en la aplicación).

## Por dónde empezar

| Si eres… | Lee en este orden |
|---|---|
| **Nuevo en el proyecto** y quieres entender la aplicación | `00-resumen-ejecutivo` → `01-funcional` → `10-pantallas` → `02-arquitectura` → `08-procesos-bpmn/indice` → `03-modelo-datos` |
| **Desarrollador** que va a mantenerla | `02-arquitectura` → `03-modelo-datos` → `08-procesos-bpmn` → `05`/`06` integraciones → `04-seguridad-grupos` → `09-valor-adicional` → `INVENTARIO` |
| **Arquitecto o responsable** de reconstruirla o modernizarla | `00-resumen-ejecutivo` → `13-modernizacion-refactor` → `12-especificacion-reconstruccion` → `11-reglas-negocio` → `10-pantallas` |
| **Negocio**, para validar | `01-funcional` → `11-reglas-negocio` → `12-especificacion-reconstruccion` (preguntas abiertas y funcionalidad candidata a no migrar) |

## Contenido

| Documento | Qué contiene |
|---|---|
| `00-resumen-ejecutivo.md` | Hallazgos clave, riesgos y veredicto de modernización. |
| `01-funcional.md` | Qué hace la aplicación, para quién y casos de uso. |
| `02-arquitectura.md` | Cómo está construida: capas, objetos principales y acoplamientos. |
| `03-modelo-datos.md` | Entidades, relaciones y volúmenes. |
| `04-seguridad-grupos.md` | Grupos, permisos y reglas de seguridad. |
| `05-integraciones-consumidas.md` | Sistemas externos a los que llama. |
| `06-apis-expuestas.md` | APIs que ofrece a otros sistemas. |
| `07-batches.md` | Procesos programados. |
| `08-procesos-bpmn/` | Cada proceso en BPMN 2.0 y su explicación. |
| `09-valor-adicional.md` | Constantes, reglas reutilizables, huérfanos, métricas y riesgos técnicos. |
| `10-pantallas.md` | Catálogo de pantallas (`PAN-xxx`). |
| `11-reglas-negocio.md` | Catálogo de reglas de negocio (`RN-xxx`). |
| `12-especificacion-reconstruccion.md` | Requisitos para reconstruirla (`RF-xxx`), con criterios de aceptación y trazabilidad. |
| `13-modernizacion-refactor.md` | Diagnóstico (`MOD-xxx`), arquitectura objetivo y plan de migración. |
| `INVENTARIO.md` | Todos los objetos y cobertura de la extracción. |

## Cómo leer las marcas

| Marca | Significado |
|---|---|
| ✅ | Confirmado con la definición del objeto. |
| 🔵 | Inferido (se explica de qué). |
| 🟡 | Pendiente de validar o dato no disponible. |
| 🔴 | Riesgo. |
| `mcp:tipo/nombre#ubicación` | Evidencia: objeto y lugar de la definición donde se comprueba. |

## Qué no incluye esta documentación

{{Lista de lo que no estuvo disponible en esta ejecución: tipos sin definición, seguridad por objeto, valores por entorno, volúmenes (si no había Appian MCP Server), verificación con documentación oficial (si no había Docs MCP), historial (si no había herramienta).}}

## Glosario

| Término | Significado |
|---|---|
| {{término de negocio o Appian}} | {{definición breve}} |

> La carpeta `_intermedio/` contiene datos en bruto de la aplicación. No la compartas.
