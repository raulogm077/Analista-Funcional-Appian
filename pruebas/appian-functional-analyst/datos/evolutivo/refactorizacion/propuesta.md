# Propuesta de refactorización: estados de DEM Gestión de Solicitudes

> **Responde a:** qué está mal hecho y por qué, cómo debería estar hecho, cómo se pasa de lo que hay a lo nuevo y qué
> falta por decidir.

Base: [as-is](../as-is/LEEME.md) del 9 de octubre de 2026, entorno de preproducción, Appian 26.6.

## 1. Alcance

- **Se rehace:** de dónde salen los estados de la solicitud y quién los cambia.
- **Se queda como está:** el resto de la aplicación; la integración con el ERP tiene su propio pendiente (DEC-01).
- **Límites:** entra con el evolutivo de devoluciones; no se puede tocar `UTL_DiasLaborables`, que es de otra aplicación.

## 2. Diagnóstico

**REF-01 — Los estados salen de una constante y los elige quien crea la solicitud**

- Evidencia: H-DAT-01 ✅ `DEM_SolicitudForm` llena la lista «Estado» con `DEM_ESTADOS_VALIDOS` y no con `DEM Estado` · [`mcp:interface/DEM_SolicitudForm#línea 4`](../as-is/anexo/interface/DEM_SolicitudForm.md) · [`mcp:constant/DEM_ESTADOS_VALIDOS#value`](../as-is/anexo/constant/DEM_ESTADOS_VALIDOS.md)
- Regla: BP 01 §1.1
- Efecto: mantenimiento y riesgo; un estado nuevo obliga a cambiar la constante y el gestor puede saltarse la revisión.
- Prioridad: Media
- Esfuerzo: S, una regla, dos interfaces y retirar la constante

## 3. Solución

| Capa | Qué se hace | Por qué | Se descarta |
|---|---|---|---|
| Datos | Los estados salen solo de `DEM Estado` y la constante se retira | REF-01: los valores de una lista viven en un record type de referencia (BP 01 §1.1) | Añadir «Devuelta» a la constante: repite el problema |
| Procesos | El estado lo escribe el proceso; el formulario de la solicitud deja de enseñarlo | REF-01 (BP 03 §4) | Ocultar la lista por grupo: el estado seguiría en manos de la interfaz |

## 4. Migración y convivencia

**Estrategia:** en la aplicación actual. El cambio es pequeño y la tabla `DEM_ESTADO` ya existe.

- **Datos:** `DEM_ESTADO` recibe el valor «Devuelta»; las 152 solicitudes conservan su estado.
- **Procesos en curso:** las revisiones abiertas terminan con la versión anterior (BP 03 §12).
- **Contratos con fuera:** `DEM_WS_Solicitudes` sigue contando por los mismos estados y uno más.
- **Convivencia y retirada:** `DEM_ESTADOS_VALIDOS` se retira cuando ninguna interfaz la use.

## 5. Hoja de ruta

| Fase | Qué | Depende de |
|---|---|---|
| 1 | REF-01: estados desde `DEM Estado`, formularios y retirada de la constante | — |

## 6. Pendientes

| ID | Qué falta | Quién | Condiciona |
|---|---|---|---|
| DEC-01 | Rehacer la integración con el ERP (H-SEG-01) ahora o en otra propuesta; recomendado: en otra, antes de tocarla | Equipo | — |
| NV-ARQ-01 | ¿Qué hace `UTL_DiasLaborables` y con qué calendario cuenta?; hace falta un export de la aplicación que la contiene o acceso de lectura a ella | Equipo de la aplicación de utilidades | — |
| NV-PRO-01 | ¿A quién debe llegar el correo de «Avisar solicitante»?; hace falta que el responsable de las solicitudes diga quién lo recibe | Responsable de las solicitudes | — |
