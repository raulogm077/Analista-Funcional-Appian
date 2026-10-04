<!--
  Plantilla 05 — Integraciones consumidas. Autor: integration-security-analyzer. Prefijo de hallazgos: H-INT.
  Los comentarios son instrucciones: no se copian al documento. Las secciones sin contenido se omiten.
  Objetivo: resumen + ½ pantalla por integración (máximo 1).
  Secretos, credenciales y hosts: references/security-rules.md, «Cómo se escribe cada dato». Nunca una URL con credenciales,
  ni enmascaradas; nunca el usuario de una credencial; host interno → ‹host interno›.
-->

# Integraciones consumidas

> **TL;DR**: {{qué sistemas externos usa la aplicación, para qué y desde qué procesos o pantallas, en 2-3 frases}}.
> **Volumen**: {{N}} connected systems, {{N}} integraciones ({{N}} modifican datos), {{N}} sistemas externos. **Hallazgos**: {{N (Alta: n)}} — principales: [H-INT-01](#hallazgos), … {{o «sin hallazgos»}}.

## Vista

<!--
  Sin diagrama propio: el mapa de la aplicación con sus sistemas externos está en 02. Tabla ≤ 15 filas (si hay más, parte por sistema externo).
  Integraciones sin connected system: «—» en esa columna. Connected systems sin integraciones: una línea debajo de la tabla.
-->

Qué llama la aplicación hacia fuera. El mapa con los sistemas externos está en [02-arquitectura.md](./02-arquitectura.md).

| Integración | Connected system | Sistema externo | Método | Modifica datos | Llamantes | Certeza |
|---|---|---|---|---|---|---|
| `{{INT_SAP_Crear}}` | `{{CS_SAP}}` | {{SAP: alta de expedientes}} | POST | Sí | {{2}} | ✅ |
| `{{INT_Catastro_Consulta}}` | `{{CS_Catastro}}` | {{Catastro: datos de una parcela}} | GET | No | {{1}} | ✅ |

## Detalle

<!-- Con más de 5 fichas, empieza por un índice de enlaces. -->

### Connected systems

#### {{CS_SAP}} — {{SAP ERP}}

{{Conexión con el ERP SAP para dar de alta expedientes.}}

| Campo | Valor |
|---|---|
| Tipo | {{HTTP}} |
| URL base | `{{https://‹host interno›/sap/api/v1}}` |
| Autenticación | {{Basic: usuario y contraseña en el connected system (valores no mostrados)}} |
| Integraciones | [{{INT_SAP_Crear}}](#{{int_sap_crear--sap-crear-expediente}}) |
| Parametrizable por entorno | {{Sí: URL base y credenciales van en el fichero de personalización de importación}} |

<!-- Si la URL base lleva credenciales embebidas, añade: «La URL base lleva credenciales embebidas (enmascaradas).» y regístralo como H-SEG en 04. -->

Evidencia: `mcp:connectedSystem/{{CS_SAP}}#baseUrl` · Certeza: ✅ · [Definición](anexo/connectedSystem/{{CS_SAP}}.md)

### Integraciones

#### {{INT_SAP_Crear}} — {{SAP Crear expediente}}

{{Envía a SAP un expediente aprobado y recibe su número de expediente en SAP.}}

| Campo | Valor |
|---|---|
| Connected system | [{{CS_SAP}}](#{{cs_sap--sap-erp}}) |
| Método y ruta | `{{POST /expedientes}}` |
| Modifica datos | {{Sí}} |
| Parámetros | {{`idExpediente` (ruta) ← `ri!idExpediente`; `Authorization` ← `CON_SAP_TOKEN` (valor no mostrado)}} |
| Cuerpo | {{JSON con expediente, solicitante e importe (forma abajo)}} |
| Respuesta | {{`numeroSap` y `estado`, que el proceso guarda en `pv!numeroSap`}} |
| Errores | {{El proceso llamante no muestra tratamiento de error en la definición extraída}} ❓ |
| Llamantes | {{[DEM Alta Solicitud](08-procesos-bpmn/DEM_Alta_Solicitud.md) (nodo 4) y `DEM_ReenviarSap`}} |

Forma del cuerpo (de la definición, sin valores):

```json
{"expediente": "texto", "solicitante": "texto", "importe": "decimal"}
```

Evidencia: `mcp:integration/{{INT_SAP_Crear}}#expression (líneas {{3-18}})` · Certeza: ✅ · [Definición](anexo/integration/{{INT_SAP_Crear}}.md)

<!--
  Errores: ✅ solo si la definición del llamante muestra el tratamiento (p. ej. onError en SAIL) o muestra que no lo hay.
  Las pestañas de excepciones de los nodos de proceso no siempre llegan: si no llegan, ❓ y la pregunta.
-->

### Configuración por entorno

<!--
  Lo que cambia entre entornos. Los valores de otros entornos no están en la plataforma (fichero de personalización de importación):
  solo se ve el valor del entorno extraído. «Parametrizable por entorno»:
    Sí — URL base y credenciales de un connected system; constante marcada «Environment Specific»; usuario y contraseña literales de una integración.
    No — literal dentro de una expresión; constante sin esa marca.
    ❓ — la definición no dice si la constante está marcada.
  Los secretos nunca: «(valor no mostrado)».
-->

| Objeto | Propiedad | Valor en el entorno extraído | ¿Parametrizable por entorno? | Notas |
|---|---|---|---|---|
| `{{CS_SAP}}` | URL base | `{{https://‹host interno›/sap/api/v1}}` | Sí | — |
| `{{CS_SAP}}` | Credenciales | (valor no mostrado) | Sí | — |
| `{{CON_CATASTRO_URL}}` | Valor | `{{https://ovc.catastro.example.es/servicio}}` | ❓ | {{Validar si la constante está marcada como específica del entorno}} |

## Hallazgos

| ID | Hallazgo | Severidad | Certeza | Evidencia |
|---|---|---|---|---|
| H-INT-01 | {{La URL de Catastro es literal en una regla y no cambia por entorno}} | Media | ✅ | `mcp:expressionRule/{{DEM_UrlCatastro}}#expression (línea 2)` |
| H-INT-02 | {{CS_Catastro usa autenticación None contra una API externa}} | Media | ✅ | `mcp:connectedSystem/{{CS_Catastro}}#authType` |

<!--
  Solo hallazgos de integraciones. Un secreto o una URL con credenciales es H-SEG (04): aquí, una frase sin severidad con enlace a 04.
  Mismos ID, título, severidad y certeza que en <trabajo>/hallazgos/integration-security-analyzer.json.
  Un hallazgo Alta lleva debajo una línea con su impacto y la recomendación.
-->

## Cobertura y límites

- {{Valores de otros entornos: no están en la plataforma; solo se documenta el entorno extraído}} ❓
- {{Tratamiento de errores en los nodos de proceso: la extracción no devuelve las pestañas de excepciones}} ❓
