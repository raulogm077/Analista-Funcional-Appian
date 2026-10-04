<!--
  Plantilla 06 — APIs expuestas (Web APIs). Autor: integration-security-analyzer. Prefijo de hallazgos: H-API.
  Los comentarios son instrucciones: no se copian al documento. Las secciones sin contenido se omiten.
  Objetivo: resumen + ½ pantalla por Web API (máximo 1).
  Una Web API solo la puede llamar un usuario o cuenta de servicio autenticado, y hace falta al menos Viewer en su role map.
  El método de autenticación (API key, Basic, OAuth 2.0, TLS mutuo) lo configura cada consumidor fuera de la Web API.
  Fuentes: https://docs.appian.com/suite/help/26.6/Web_APIs.html#prodlink-security
           https://docs.appian.com/suite/help/26.6/Web_API_Authentication.html#authentication
-->

# APIs expuestas

> **TL;DR**: {{qué ofrece la aplicación a otros sistemas, quién puede llamarlo y qué dispara, en 2-3 frases}}.
> **Volumen**: {{N}} Web APIs ({{N}} GET, {{N}} POST…), {{N}} que escriben datos o lanzan procesos. **Hallazgos**: {{N (Alta: n)}} — principales: [H-API-01](#hallazgos), … {{o «sin hallazgos»}}.

## Vista

<!--
  Sin diagrama: la tabla ya relaciona cada Web API con lo que dispara. Tabla ≤ 15 filas.
  «Pueden llamarla»: grupos con Viewer o superior en su role map; sin role map, «❓ role map no disponible».
-->

Lo que la aplicación ofrece a otros sistemas. Todas exigen un usuario o cuenta de servicio autenticado.

| Web API | Método | Ruta | Pueden llamarla | Qué hace | Certeza |
|---|---|---|---|---|---|
| `{{DEM_API_AltaSolicitud}}` | POST | `/suite/webapi/{{dem-solicitudes}}` | `{{DEM Integraciones}}` | {{Registra una solicitud y lanza DEM Alta Solicitud}} | ✅ |
| `{{DEM_API_Estado}}` | GET | `/suite/webapi/{{dem-estado}}` | ❓ role map no disponible | {{Devuelve el estado de una solicitud}} | ✅ |

## Detalle

<!-- Con más de 5 fichas, empieza por un índice de enlaces. -->

### {{DEM_API_AltaSolicitud}} — {{Alta de solicitud}}

{{Permite a un sistema externo registrar una solicitud sin pasar por el site.}}

| Campo | Valor |
|---|---|
| Método y ruta | `{{POST /suite/webapi/dem-solicitudes}}` |
| Pueden llamarla | {{`DEM Integraciones` (Viewer)}} |
| Parámetros | {{`origen` (consulta, texto, obligatorio)}} |
| Cuerpo | {{JSON con solicitante, tipo e importe (forma abajo)}} |
| Respuesta | {{201 con el id de la solicitud; 400 si falta un campo obligatorio}} |
| Consumidores | {{No constan en la definición}} ❓ |

Forma del cuerpo (de la definición, sin valores):

```json
{"solicitante": "texto", "tipo": "texto", "importe": "decimal"}
```

Qué invoca:

| Acción | Objeto |
|---|---|
| Valida la entrada | [{{DEM_ValidarSolicitud}}](anexo/expressionRule/{{DEM_ValidarSolicitud}}.md) |
| Lanza un proceso | [{{DEM Alta Solicitud}}](08-procesos-bpmn/{{DEM_Alta_Solicitud}}.md) (con `a!startProcess`) |

<!--
  Respuesta: solo los códigos que devuelve la expresión (a!httpResponse); los que da la plataforma (p. ej. 404 si el llamante no tiene permiso) no se listan.
  Consumidores: quién la llama y para qué solo si consta (descripción, documentación o un llamante conocido); si no, ❓.
-->

Evidencia: `mcp:webApi/{{DEM_API_AltaSolicitud}}#expression (líneas {{4-30}})` · Certeza: ✅ · [Definición](anexo/webApi/{{DEM_API_AltaSolicitud}}.md)

## Hallazgos

| ID | Hallazgo | Severidad | Certeza | Evidencia |
|---|---|---|---|---|
| H-API-01 | {{DEM_API_Estado la puede llamar cualquier usuario de la aplicación (DEM Users con Viewer)}} | Media | ✅ | `mcp:webApi/{{DEM_API_Estado}}@other:{{herramienta}}#roleMap` |
| H-API-02 | {{DEM_API_AltaSolicitud lanza el proceso sin validar el importe}} | Media | 🔵 | `mcp:webApi/{{DEM_API_AltaSolicitud}}#expression (línea {{12}})` |

<!--
  Solo hallazgos de Web APIs. Mismos ID, título, severidad y certeza que en <trabajo>/hallazgos/integration-security-analyzer.json.
  Un hallazgo Alta lleva debajo una línea con su impacto y la recomendación.
-->

## Cobertura y límites

- {{Consumidores y método de autenticación que usan: no constan en la definición; validar con el equipo de integración}} ❓
- {{Role maps: no los devuelve la extracción para N Web APIs; validar en Appian Designer quién puede llamarlas}} ❓
