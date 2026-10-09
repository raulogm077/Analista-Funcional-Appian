# Propuesta de refactorización: REX Revisiones de Extintores

> **Responde a:** qué está mal hecho y por qué, cómo debería estar hecho, cómo se pasa de lo que hay a lo nuevo y qué
> falta por decidir.

Base: [as-is](../as-is/LEEME.md) del 2 de octubre de 2026, entorno de preproducción, Appian 26.6.

## 1. Alcance

- **Se rehace:** el registro de revisiones (datos, proceso y lista) y la baja de extintores.
- **Se queda como está:** el record type `REX Extintor` y los grupos, que ya siguen el diseño recomendado.
- **Límites:** seis semanas; no se puede tocar `AVI_EnviarAviso`, que es de la aplicación de avisos.

## 2. Diagnóstico

**REF-01 — Las revisiones se guardan con un CDT y un data store, sin record type**

- Evidencia: H-DAT-01 ✅ `REX_Revision` se guarda en `REX Datos` y `REX_IF_ListaRevisiones` la lee con `a!queryEntity` · [`mcp:cdt/REX_Revision#fields`](../as-is/anexo/cdt/REX_Revision.md) · [`mcp:interface/REX_IF_ListaRevisiones#línea 2`](../as-is/anexo/interface/REX_IF_ListaRevisiones.md)
- Regla: BP 01 §7
- Efecto: mantenimiento; las revisiones no se relacionan con `REX Extintor` y no llegan al data fabric.
- Prioridad: Media
- Esfuerzo: M, un record type, una lista y un proceso, sin migrar la tabla

**REF-02 — El historial de cada revisión se lleva a mano**

- Evidencia: H-DAT-02 🔶 inferido de los nodos de `REX_PM_RegistrarRevision` y de las entidades de `REX Datos`: cada revisión se escribe dos veces · [`mcp:processModel/REX_PM_RegistrarRevision#nodes[id=5]`](../as-is/anexo/processModel/REX_PM_RegistrarRevision.md) · [`mcp:dataStore/REX Datos#entities`](../as-is/anexo/dataStore/REX_Datos.md)
- Regla: BP 01 §11
- Efecto: mantenimiento; cada proceso que cambie una revisión tiene que repetir la escritura del historial.
- Prioridad: Baja
- Esfuerzo: S, eventos de record en un record type y un nodo menos

**REF-03 — La baja se inicia con un botón de la ficha y no con una acción de record**

- Evidencia: H-UI-01 ✅ el botón de `REX_IF_FichaExtintor` inicia `REX_PM_BajaExtintor` con `a!startProcess` · [`mcp:interface/REX_IF_FichaExtintor#línea 13`](../as-is/anexo/interface/REX_IF_FichaExtintor.md)
- Regla: BP 01 §9.2
- Efecto: riesgo; quién puede dar de baja depende de la interfaz y no de la seguridad de una acción de record.
- Prioridad: Media
- Esfuerzo: S, una acción de record en `REX Extintor` y quitar el botón

**REF-04 — `REX_PM_AvisoAnual` no lo usa nada**

- Evidencia: H-ARQ-01 ✅ huérfano y H-GEN-01 ✅ sin ejecuciones, el mismo problema visto por dos señales · [`mcp:processModel/REX_PM_AvisoAnual@history`](../as-is/anexo/processModel/REX_PM_AvisoAnual.md)
- Regla: BP 11 §8
- Efecto: mantenimiento de un proceso que no se ejecuta.
- Prioridad: Baja
- Esfuerzo: S, retirarlo cuando lo decida el negocio

## 3. Solución

| Capa | Qué se hace | Por qué | Se descarta |
|---|---|---|---|
| Datos | Un record type sincronizado, `REX Revisión`, sobre la tabla actual de revisiones, relacionado con `REX Extintor` (muchas a una) y con eventos de record | REF-01: convive con el CDT mientras cambia lo demás (BP 01 §7). REF-02: los eventos de record dan el historial (BP 01 §11) | Tablas nuevas: no hacen falta para tener relaciones y obligan a migrar |
| Procesos | `REX_PM_RegistrarRevision` escribe con Write Records en `REX Revisión` y deja de copiar el historial; `REX_PM_AvisoAnual` se retira si el negocio lo confirma (DEC-01) | REF-01, REF-02 (BP 03 §4). REF-04 (BP 11 §8) | Mantener la escritura doble: el historial ya lo dan los eventos |
| Pantallas | La lista de revisiones pasa a una lista de record de `REX Revisión`; la baja, a una acción de record de `REX Extintor` con su seguridad, y el botón se quita | REF-01 (BP 02 §5.3). REF-03 (BP 01 §9.2) | Ocultar el botón por grupo: la seguridad seguiría en la interfaz |

## 4. Migración y convivencia

**Estrategia:** en la aplicación actual. Los problemas están en una parte (revisiones y baja) y `REX Extintor` ya sigue
el diseño recomendado. Una aplicación nueva obligaría a migrar los extintores sin necesidad, y la mixta no aporta nada
con una sola parte que cambia.

- **Datos:** `REX Revisión` se crea sobre la misma tabla, así que no se migra nada. El historial anterior se queda en su
  entidad de `REX Datos`, de solo lectura, hasta que el negocio decida qué hacer con él (DEC-02).
- **Procesos en curso:** las instancias abiertas de `REX_PM_RegistrarRevision` terminan con la versión anterior; la
  nueva solo cambia la escritura (BP 03 §12).
- **Contratos con fuera:** `AVI_EnviarAviso` recibe hoy la revisión. Si recibe el CDT `REX_Revision`, el CDT se queda
  hasta que cambie la aplicación de avisos (NV-ARQ-01).
- **Convivencia y retirada:** el CDT y la entidad de historial conviven con `REX Revisión` hasta que nada los use, y se
  retiran en la fase 3.

## 5. Hoja de ruta

| Fase | Qué | Depende de |
|---|---|---|
| 0 | Verificar H-DAT-02: confirmar con el equipo que la segunda entidad de `REX Datos` es el historial y que nadie más la lee | — |
| 1 | REF-01: record type `REX Revisión`, lista de record y escritura con Write Records | Fase 0 y NV-ARQ-01 |
| 2 | REF-02: eventos de record. REF-03: acción de record para la baja | Fase 1 |
| 3 | REF-04: retirar `REX_PM_AvisoAnual`; retirar el CDT si `AVI_EnviarAviso` ya no lo usa | Fase 2 y DEC-01 |

## 6. Pendientes

| ID | Qué falta | Quién | Condiciona |
|---|---|---|---|
| DEC-01 | Retirar `REX_PM_AvisoAnual` o volver a programarlo; recomendado: retirarlo, porque no tiene ejecuciones | Negocio | REF-04 |
| DEC-02 | Cargar el historial anterior como eventos de record o dejarlo de solo lectura; recomendado: de solo lectura | Negocio | REF-02 |
| NV-ARQ-01 | ¿Qué hace `AVI_EnviarAviso` y qué recibe?; hace falta acceso de lectura a la aplicación de avisos o un export de ella | Equipo de la aplicación de avisos | REF-01 |
