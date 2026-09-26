# Diagramas Mermaid para el DDF

Esta referencia cubre los **4 tipos de diagrama** que usamos en el DDF y el
**workflow de validación + render a PNG** para incrustarlos en el `.docx`.

Lee la sección que necesites según el diagrama a generar:

- [Workflow general](#workflow-general-escribir--validar-y-renderizar--incrustar) — cómo
  validar el Mermaid y obtener el PNG (válido para los 4 tipos).
- [1. Flowchart BPM](#1-flowchart-bpm-sección-6) — Sección 6 del DDF.
- [2. Diagrama de casos de uso](#2-diagrama-de-casos-de-uso-sección-7) — Sección 7.
- [3. erDiagram (modelo de datos)](#3-erdiagram-modelo-de-datos-sección-10) — Sección 10.
- [4. stateDiagram-v2 (ciclo de vida)](#4-statediagram-v2-ciclo-de-vida-sección-11) — Sección 11.

---

## Workflow general: escribir → validar y renderizar → incrustar

Patrón **obligatorio** para cualquier diagrama del DDF. Todo se hace en el
equipo: el contenido del diagrama es información del cliente y **no se envía a
servicios externos** (mermaid.live, mermaid.ink, kroki…).

### Paso 1 — Escribir el `.mmd`

Guarda cada diagrama en `diagramas/<nombre>.mmd` dentro de la carpeta de trabajo
del análisis (no en `/tmp`) y copia el mismo código en el bloque ```` ```mermaid ````
de la sección correspondiente del `ddf.md`. Nombres: `bpm-<proceso>`, `cu`,
`er`, `estados-<entidad>`.

### Paso 2 — Validar y renderizar a PNG

```bash
python3 <skill>/scripts/render_mermaid.py diagramas/*.mmd          # valida y genera diagramas/<nombre>.png
python3 <skill>/scripts/render_mermaid.py diagramas/er.mmd --check # solo valida
```

`<skill>` es la carpeta de esta skill (en Windows, `python` en vez de `python3`).
El script usa la copia de Mermaid incluida en `assets/` y un navegador headless
del propio equipo (Chromium de Playwright, Chrome o Edge). Códigos de salida:

- `0` todo correcto.
- `1` algún diagrama tiene un error de sintaxis: el mensaje indica la línea.
  **Corrige el código y vuelve a ejecutarlo**; nunca incrustes un diagrama que
  no ha validado.
- `2` falta un requisito (Playwright para Python o un navegador): el mensaje dice
  qué instalar. Díselo al usuario y sigue con el fallback.

Revisa cada PNG con Read antes de incrustarlo: textos cortados, nodos
solapados o un flujo ilegible por tamaño se corrigen dividiendo el diagrama.

**Fallback sin navegador**: deja el bloque Mermaid en el `ddf.md` y, en el docx,
el código en un bloque monoespaciado con la nota «Diagrama pendiente de
renderizar (requisito: Playwright + navegador)». Añade en Sec 17 un punto
🟡 IMPORTANTE. No lo pegues en webs públicas para verlo.

### Paso 3 — Enlazar la imagen en el `ddf.md`

Justo después de cada bloque ```` ```mermaid ````, una línea con su imagen:

```
![Flujo — Ciclo del informe](diagramas/bpm-informe.png)
```

`scripts/ddf_docx.js` sustituye el bloque por la imagen al generar el Word y la
numera como `Figura N — pie`. Si el PNG no existe, deja el código con el aviso
«Diagrama pendiente de renderizar».

---

## 1. Flowchart BPM (Sección 6)

Usa este tipo para el **flujo de proceso end-to-end** y subprocesos. El criterio
de división es: si supera 15 nodos, parte en subprocesos y genera un diagrama
por subproceso.

### Codificación de colores (classDef obligatorio)

```
classDef inicio fill:#388E3C,color:#fff,stroke:#2E7D32
classDef tarea fill:#1565C0,color:#fff,stroke:#0D47A1
classDef notif fill:#F57C00,color:#fff,stroke:#E65100
classDef sistema fill:#7B1FA2,color:#fff,stroke:#4A148C
```

| Estilo | Forma Mermaid | Uso |
|--------|--------------|-----|
| `:::inicio` (verde) | `(("Inicio: descripción"))` | Eventos de inicio y fin |
| `:::tarea` (azul) | `["Verbo + objeto"]` | Tareas manuales de usuario |
| `:::notif` (naranja) | `[/"Notif: destinatario — hecho"/]` | Notificaciones / mensajes |
| `:::sistema` (morado) | `[["Sistema: acción"]]` | Tareas automáticas / integraciones |
| Sin estilo | `{"¿Pregunta?"}` | Gateways de decisión |

### Nomenclatura BPMN

- **Tareas**: ID de la actividad + infinitivo + objeto — ✅ "ACT-01 · Registrar solicitud" / ❌ "El usuario registra". El ID enlaza cada caja con su fila de la tabla de actividades y su ficha de tarea (Sec 6.3)
- **Gateways**: pregunta cerrada — ✅ "¿Documentación completa?" / ❌ "Documentación completa"
- **Inicio**: `"Inicio: [hecho desencadenante]"`
- **Fin**: `"Fin: [resultado de negocio]"` — un nodo por cada resultado posible
- Toda salida de gateway lleva etiqueta: `-->|"Sí"|`, `-->|"No"|`, `-->|"Aprobado"|`
- Todo camino tiene cierre explícito (sin finales implícitos)
- **Sin comentarios dentro del diagrama**: nada de `note`, cajas de texto
  explicativas ni etiquetas largas. El diagrama solo muestra actividades,
  decisiones y salidas; todo lo que haya que explicar de un punto del flujo va
  en la ficha de esa actividad (Sec 6.3). Así el flujo se puede leer y
  actualizar como texto sin mezclar explicación y estructura

### Plantilla completa

```mermaid
flowchart LR
  classDef inicio fill:#388E3C,color:#fff,stroke:#2E7D32
  classDef tarea fill:#1565C0,color:#fff,stroke:#0D47A1
  classDef notif fill:#F57C00,color:#fff,stroke:#E65100
  classDef sistema fill:#7B1FA2,color:#fff,stroke:#4A148C

  A(("Inicio: Solicitud recibida")):::inicio
  B["ACT-01 · Registrar solicitud"]:::tarea
  C{"¿Documentación completa?"}
  D[/"Notif: Solicitante — Documentación incompleta"/]:::notif
  E["ACT-02 · Validar solicitud"]:::tarea
  F{"¿Aprobado?"}
  G[["ACT-03 · Sistema: Registrar en ERP"]]:::sistema
  H[/"Notif: Solicitante — Solicitud aprobada"/]:::notif
  Z(("Fin: Expediente cerrado")):::inicio
  ZZ(("Fin: Solicitud rechazada")):::inicio

  A --> B --> C
  C -->|"Sí"| E
  C -->|"No"| D --> B
  E --> F
  F -->|"Aprobado"| G --> H --> Z
  F -->|"Rechazado"| ZZ
```

---

## 2. Diagrama de casos de uso (Sección 7)

Mermaid no tiene un tipo nativo de "Use Case Diagram" (a lo UML), así que
usamos un `flowchart LR` con dos columnas visuales: actores a la izquierda
(círculos) y casos de uso a la derecha (elipses). Las líneas representan
"actor participa en CU".

Útil para que el cliente vea de un vistazo qué hace cada rol en el sistema.
**No reemplaza la ficha de cada CU** — la complementa.

### Convenciones

- **Actores**: círculo `(("Nombre del rol"))` con `:::actor`
- **Casos de uso**: elipse `(["CU-XXX — Nombre del caso"])` con `:::cu`
- **Subsistema** (opcional): `subgraph Sistema` que envuelve todos los CU
- Conexión actor → CU: línea simple `-->`. Si el actor solo consulta (sin
  modificar), usar `-.->` punteada.

### classDef

```
classDef actor fill:#FFF3E0,color:#E65100,stroke:#E65100,stroke-width:2px
classDef cu fill:#E3F2FD,color:#0D47A1,stroke:#0D47A1
```

### Plantilla completa

```mermaid
flowchart LR
  classDef actor fill:#FFF3E0,color:#E65100,stroke:#E65100,stroke-width:2px
  classDef cu fill:#E3F2FD,color:#0D47A1,stroke:#0D47A1

  A1(("Solicitante")):::actor
  A2(("Revisor")):::actor
  A3(("Coordinador")):::actor

  subgraph Sistema["Sistema de Expedientes"]
    CU1(["CU-001 — Crear expediente"]):::cu
    CU2(["CU-002 — Subir documentación"]):::cu
    CU3(["CU-003 — Revisar expediente"]):::cu
    CU4(["CU-004 — Aprobar / rechazar"]):::cu
    CU5(["CU-005 — Consultar histórico"]):::cu
  end

  A1 --> CU1
  A1 --> CU2
  A2 --> CU3
  A2 --> CU4
  A3 -.-> CU5
  A3 --> CU4
```

---

## 3. erDiagram (modelo de datos) (Sección 10)

Mermaid soporta diagramas entidad-relación de forma nativa con `erDiagram`.
Úsalo para visualizar las entidades del modelo funcional y sus cardinalidades.

### Sintaxis de relaciones

| Símbolo izquierda | Símbolo derecha | Significado |
|-------------------|-----------------|-------------|
| `\|\|` | `\|\|` | Uno a uno |
| `\|\|` | `o{` | Uno a cero-o-muchos |
| `\|\|` | `\|{` | Uno a uno-o-muchos |
| `}o` | `o{` | Muchos a muchos |

Las cardinalidades se escriben así: `ENTIDAD_A ||--o{ ENTIDAD_B : "verbo"`

### Convenciones

- **Nombres de entidad**: MAYÚSCULAS y sin espacios — `EXPEDIENTE`, `aTRP`,
  `ENTREGA`. Si el cliente usa una palabra concreta, respétala exactamente.
- **Atributos por entidad**: solo los que las transcripciones mencionan o que
  se derivan de forma directa. **Prohibido inventar campos de auditoría
  técnica sin evidencia.**
- **Tipos**: `string`, `int`, `date`, `decimal`, `bool`, o el tipo Appian si el
  cliente lo mencionó (`Text`, `Number (Integer)`, `Date and Time`, etc.).
- **PK / FK**: marca claves con `PK` y `FK` al final del atributo.

### Plantilla completa

```mermaid
erDiagram
  EXPEDIENTE ||--o{ ENTREGA : "contiene"
  EXPEDIENTE }o--|| aTRP : "asignado_a"
  ENTREGA ||--o{ DOCUMENTO : "incluye"
  ENTREGA }o--|| REVISOR : "revisado_por"

  EXPEDIENTE {
    string id_expediente PK
    string codigo
    string estado
    date fecha_apertura
    string aTRP_id FK
  }
  ENTREGA {
    string id_entrega PK
    string expediente_id FK
    int numero_entrega
    string estado
    date fecha_entrega
  }
  DOCUMENTO {
    string id_documento PK
    string entrega_id FK
    string tipo_documento
    string url_sharepoint
  }
  aTRP {
    string id_aTRP PK
    string nombre
    string email
  }
  REVISOR {
    string id_revisor PK
    string nombre
    string rol
  }
```

### Cuándo NO usar erDiagram

Si una entidad no tiene aún atributos definidos (solo se mencionó el nombre),
no la fuerces en el diagrama con campos inventados. Mejor déjala fuera del
erDiagram y márcala en la tabla de relaciones del DDF como "pendiente de
sesión de modelo de datos".

---

## 4. stateDiagram-v2 (ciclo de vida) (Sección 11)

Para cada entidad principal con ciclo de vida, genera un `stateDiagram-v2` que
muestre estados y transiciones. Es el complemento visual de las tablas de
estados/transiciones de la Sección 11.

### Convenciones

- **Estado inicial**: `[*] --> NombreEstado`
- **Estado final**: `NombreEstado --> [*]` (uno por cada cierre de negocio
  distinto, igual que en BPM no se mezclan finales)
- **Nombre del estado**: usar el **nombre de negocio**, no técnico.
  ✅ "En revisión" / ❌ "REV". Si el nombre tiene espacios o tildes, declara
  el estado con su etiqueta: `state "En revisión" as EnRevision`; si no, el
  diagrama muestra el identificador («EnRevision») en vez del nombre.
- **Etiqueta de transición**: `acción + actor` o solo `acción` si es obvia.
  ✅ `--> EnRevision : Enviar a revisión`
- **Estados compuestos**: usar `state Nombre { ... }` si el ciclo tiene
  sub-estados (ej. "En revisión" con sub-estados "Asignada / En curso").

### Plantilla completa (entidad Expediente)

```mermaid
stateDiagram-v2
  direction LR
  [*] --> Borrador : Crear expediente

  Borrador --> EnRevision : Enviar a revisar
  Borrador --> Cancelado : Cancelar

  EnRevision --> Aprobado : Aprobar (Revisor)
  EnRevision --> Rechazado : Rechazar con observaciones
  EnRevision --> Subsanacion : Solicitar subsanación

  Subsanacion --> EnRevision : Reenviar
  Subsanacion --> Cancelado : Cancelar

  Rechazado --> Borrador : Corregir y reenviar
  Rechazado --> Cancelado : Descartar

  Aprobado --> Cerrado : Cerrar expediente
  Aprobado --> Reabierto : Reabrir (Coordinador)
  Reabierto --> EnRevision : Reenviar a revisar

  Cancelado --> [*]
  Cerrado --> [*]
```

### Regla de coherencia con Sección 11

Toda transición del diagrama debe aparecer también en la **tabla de
transiciones** (estado origen / evento / estado destino / actor / condición).
Si una transición no está en la tabla, falta documentarla — el diagrama no
puede tener flechas "huérfanas" sin explicación textual.

---

## Tabla resumen — qué diagrama va en qué sección

| Sección DDF | Tipo Mermaid | Cuándo incluir | Cuándo omitir |
|-------------|--------------|----------------|---------------|
| 6 — Flujo BPM | `flowchart LR` | Siempre. Es la sección central. | Nunca: si no hay flujo, falta info crítica. |
| 7 — Casos de uso | `flowchart LR` (actor↔CU) | Cuando hay ≥3 actores o ≥6 CUs. | Si solo hay 1 actor y 2 CUs, la tabla basta. |
| 10 — Modelo de datos | `erDiagram` | Cuando ≥2 entidades tienen atributos definidos. | Si todas las entidades están en ❓. |
| 11 — Estados | `stateDiagram-v2` | Cuando una entidad tiene ≥3 estados. | Entidades sin ciclo de vida (catálogos, etc.). |
