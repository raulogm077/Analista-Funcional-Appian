<!--
  Plantilla 05 — Integraciones consumidas. Autor: integration-security-analyzer. Prefijo de hallazgos: H-INT.
  Los comentarios son instrucciones: no se copian al documento. Las secciones sin contenido se omiten.
  Objetivo: resumen + ½ pantalla por integración (máximo 1).
  Un secreto escrito (credenciales en la URL base, una cabecera con un token…) es un hallazgo H-SEG de 04:
  references/security-rules.md.
  Lo que cambia por entorno (URL base y credenciales de los connected systems, constantes) está en 09: aquí se enlaza.
  «Cobertura y límites»: solo lo de este documento; lo global está en LEEME.
-->

# Integraciones consumidas

> **Responde a:** ¿A qué sistemas externos llama la aplicación y para qué? ¿Desde qué procesos o pantallas? ¿Cómo se conecta y se autentica con cada uno? ¿Qué falla si cae una integración?

> **TL;DR**: {{qué sistemas externos usa la aplicación, para qué y desde qué procesos o pantallas, en 2-3 frases}}.
> **Volumen**: {{N}} connected systems, {{N}} integraciones ({{N}} modifican datos), {{N}} sistemas externos. **Hallazgos**: {{N (Alta: n)}} — principales: [H-INT-01](#hallazgos), … {{o «sin hallazgos»}}.

## Vista

<!--
  Sin diagrama propio: el mapa de la aplicación con sus sistemas externos está en 02. Tabla ≤ 15 filas (si hay más, parte por sistema externo).
  Integraciones sin connected system: «—» en esa columna. Connected systems sin integraciones: una línea debajo de la tabla.
-->

El mapa con los sistemas externos está en [02-arquitectura.md](./02-arquitectura.md#vista).

| Integración | Connected system | Sistema externo | Método | Modifica datos | Llamantes | Certeza | Evidencia |
|---|---|---|---|---|---|---|---|
| `{{INT_SAP_Crear}}` | `{{CS_SAP}}` | {{SAP: alta de expedientes}} | POST | Sí | {{2}} | ✅ | [`mcp:integration/{{INT_SAP_Crear}}`](./anexo/integration/{{slug}}.md) |
| `{{INT_Catastro_Consulta}}` | `{{CS_Catastro}}` | {{Catastro: datos de una parcela}} | GET | No | {{1}} | ✅ | [`mcp:integration/{{INT_Catastro_Consulta}}`](./anexo/integration/{{slug}}.md) |

## Detalle

<!-- Con más de 5 fichas, empieza por un índice de enlaces. -->

### Connected systems

#### {{CS_SAP}} — {{SAP ERP}}

{{Conexión con el ERP SAP para dar de alta expedientes.}}

| Campo | Valor |
|---|---|
| Tipo | {{HTTP}} |
| URL base | `{{https://sap.example.org/sap/api/v1}}` |
| Autenticación | {{Basic: usuario y contraseña en el connected system}} |
| Integraciones | [{{INT_SAP_Crear}}](#{{int_sap_crear--sap-crear-expediente}}) |

<!-- Si la URL base lleva credenciales embebidas, añade: «La URL base lleva credenciales embebidas.» y regístralo como H-SEG en 04. -->

Evidencia: [`mcp:connectedSystem/{{CS_SAP}}#baseUrl`](./anexo/connectedSystem/{{slug}}.md) · Certeza: ✅

### Integraciones

#### {{INT_SAP_Crear}} — {{SAP Crear expediente}}

{{Envía a SAP un expediente aprobado y recibe su número de expediente en SAP.}}

| Campo | Valor |
|---|---|
| Connected system | [{{CS_SAP}}](#{{cs_sap--sap-erp}}) |
| Método y ruta | `{{POST /expedientes}}` |
| Modifica datos | {{Sí}} |
| Parámetros | {{`idExpediente` (ruta) ← `ri!idExpediente`; `Authorization` ← `CON_SAP_TOKEN`}} |
| Cuerpo | {{JSON con expediente, solicitante e importe (forma abajo)}} |
| Respuesta | {{`numeroSap` y `estado`, que el proceso guarda en `pv!numeroSap`}} |
| Errores | {{El proceso llamante no muestra tratamiento de error en la definición extraída}} ❓ |
| Llamantes | {{[DEM Alta Solicitud](08-procesos-bpmn/DEM_Alta_Solicitud.md) (nodo 4) y `DEM_ReenviarSap`}} |

Forma del cuerpo (de la definición, con los tipos):

```json
{"expediente": "texto", "solicitante": "texto", "importe": "decimal"}
```

Evidencia: [`mcp:integration/{{INT_SAP_Crear}}#expression (líneas {{3-18}})`](./anexo/integration/{{slug}}.md) · Certeza: ✅

<!--
  Errores: ✅ solo si la definición del llamante muestra el tratamiento (p. ej. onError en SAIL) o muestra que no lo hay.
  Las pestañas de excepciones de los nodos de proceso no siempre llegan: si no llegan, ❓ y la pregunta.
-->

Lo que cambia por entorno (URL base, credenciales y constantes): [09](./09-valor-adicional.md#configuración-por-entorno).

## Hallazgos

| ID | Hallazgo | Severidad | Certeza | Evidencia |
|---|---|---|---|---|
| H-INT-01 | {{La URL de Catastro es literal en una regla y no cambia por entorno}} | Media | ✅ | [`mcp:expressionRule/{{DEM_UrlCatastro}}#expression (línea 2)`](./anexo/expressionRule/{{slug}}.md) |
| H-INT-02 | {{CS_Catastro usa autenticación None contra una API externa}} | Media | ✅ | [`mcp:connectedSystem/{{CS_Catastro}}#authType`](./anexo/connectedSystem/{{slug}}.md) |

<!--
  Solo hallazgos de integraciones. Un secreto o una URL con credenciales es H-SEG (04): aquí, una frase sin severidad con enlace a 04.
  Mismos ID, título, severidad y certeza que en <trabajo>/hallazgos/integration-security-analyzer.json.
  Un hallazgo Alta lleva debajo una línea con su impacto: qué puede pasar y a quién afecta.
-->

## Cobertura y límites

- {{Tratamiento de errores en los nodos de proceso: la extracción no devuelve las pestañas de excepciones}} ❓
