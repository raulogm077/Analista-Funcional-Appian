# Principios de ejecución

Lectura obligatoria antes de la fase 4 y para todos los subagentes. Concentra los criterios no negociables. El formato de los documentos está en `references/presentation-rules.md`; cómo leer los datos, en `references/lectura-mcp-raw.md`.

---

## 1. Principios

1. **No inventar.** Lo que no está en los datos no se completa con suposiciones plausibles: se marca ❓ y se dice qué falta.
2. **Certeza en cada afirmación importante**: ✅ verificado, 🔵 inferido (di de qué), ❓ pendiente (di quién valida). Ver `presentation-rules.md`, Regla 7.
3. **Dato ausente no es defecto.** Que un campo no aparezca en la respuesta no prueba que no esté configurado: el Dev MCP no devuelve toda la configuración (p. ej. pestañas de excepciones y alertas de los nodos, seguridad de las acciones de record, destinatarios de correo, entradas de algunos nodos, variables de algunos procesos). Solo es ✅ si la respuesta muestra el campo vacío o nulo de forma explícita, o si otra fuente lo corrobora (render, validación de la plataforma, dependencias). Si no, la afirmación es ❓ «no lo devuelve la extracción», y un hallazgo basado en ella lleva certeza ❓ (o 🔵 con indicios) y una pregunta para validarlo. Lo mismo con muestras: una muestra de ejecuciones no sirve para afirmar nada sobre el total ni sobre quién las ejecutó si sus datos son uniformes o incoherentes.
4. **Trazabilidad.** Cada afirmación importante lleva `Evidencia: mcp:<tipo>/<nombre>[@<rol>]#<ubicación>` (formato en `lectura-mcp-raw.md`); lo que viene de la documentación oficial, `Fuente: <URL>`.
5. **Cero relleno.** Sin placeholders ni secciones vacías.
6. **Cada cosa en un sitio.** Un objeto tiene una ficha y un hallazgo tiene un ID, en su documento propietario; el resto enlaza (tabla de propietarios abajo).
7. **Nombres reales** (técnico y visible), nunca genéricos.
8. **Accionable.** Todo objeto listado se conecta con lo que hace para el negocio o con lo que hay que hacer con él.
9. **Seguridad.** Ningún secreto, credencial ni usuario en los entregables (`references/security-rules.md` y `presentation-rules.md`, Regla 8).
10. **Diagramas que pasan el validador** (`references/mermaid-rules.md`); si no, tabla equivalente. Los `.bpmn` siguen `references/bpmn-mapping.md`.
11. **Idioma**: español técnico neutro salvo que el usuario pida otro.

---

## 2. Documentos propietarios

Cada área tiene un documento propietario y un prefijo para los IDs de sus hallazgos. Solo el propietario registra hallazgos de su área.

| Área | Documento | Autor | Prefijo |
|---|---|---|---|
| Funcional: casos de uso, funcionalidades ausentes | `01-funcional.md` | interface-analyzer | `H-FUN` |
| Arquitectura: acoplamientos, hubs, objetos huérfanos | `02-arquitectura.md` | interface-analyzer | `H-ARQ` |
| Datos: record types, CDTs, relaciones, volúmenes | `03-modelo-datos.md` | data-modeler | `H-DAT` |
| Seguridad, grupos y secretos | `04-seguridad-grupos.md` | integration-security-analyzer | `H-SEG` |
| Integraciones consumidas | `05-integraciones-consumidas.md` | integration-security-analyzer | `H-INT` |
| APIs expuestas | `06-apis-expuestas.md` | integration-security-analyzer | `H-API` |
| Batches | `07-batches.md` | orquestador | `H-BAT` |
| Procesos | `08-procesos-bpmn/<slug>.md` | process-modeler | `H-PRO` |
| Mantenimiento, validación de la plataforma, versionado, métricas, procesos sin ejecuciones (área `uso`) | `09-valor-adicional.md` | orquestador | `H-GEN` |
| Pantallas | `10-pantallas.md` | ui-rules-analyzer | `H-UI` |
| Reglas de negocio | `11-reglas-negocio.md` | ui-rules-analyzer | `H-RN` |

Si al analizar tu área ves algo de otra (p. ej. ui-rules-analyzer nota que un proceso ignora «Cancelar»), descríbelo en una frase **sin severidad** donde tu documento lo necesite, enlaza el documento propietario y menciónalo en tu informe final bajo «Para otras áreas». El orquestador decide en la pasada de coherencia.

---

## 3. Registro de hallazgos

Un hallazgo es algo que hay que corregir, decidir o vigilar. Cada propietario los registra en dos sitios:

1. En su documento, sección `## Hallazgos`:

   ```markdown
   | ID | Hallazgo | Severidad | Certeza | Evidencia |
   |---|---|---|---|---|
   | H-PRO-01 | «Cancelar» no anula el alta | Alta | ✅ | `mcp:processModel/DEM Alta Solicitud#nodes[id=1].connections` |
   ```

   Si un hallazgo Alta necesita explicación, añade debajo una línea con su impacto y la recomendación.

2. En `<trabajo>/hallazgos/<agente>.json` (el orquestador usa `orquestador.json`), una lista con un objeto por hallazgo:

   ```json
   [{"id": "H-PRO-01", "titulo": "«Cancelar» no anula el alta", "area": "procesos",
     "severidad": "Alta", "certeza": "verificado", "objetos": ["DEM Alta Solicitud"],
     "documento": "08-procesos-bpmn/DEM_Alta_Solicitud.md#hallazgos",
     "evidencia": "mcp:processModel/DEM Alta Solicitud#nodes[id=1].connections",
     "impacto": "Una solicitud cancelada se registra igualmente.", "recomendacion": "Pasarela tras el inicio que compruebe la cancelación."}]
   ```

   - `id`: prefijo del área + número de dos cifras, sin huecos (`H-PRO-01`, `H-PRO-02`…).
   - `area`: funcional, arquitectura, datos, seguridad, secretos, integraciones, apis, batches, procesos, pantallas, reglas, mantenimiento, rendimiento o uso.
   - `severidad`: Alta, Media o Baja. `certeza`: verificado, inferido o pendiente.
   - `documento`: ruta relativa a `<salida>` (con ancla si quieres).
   - `duplicadoDe` (solo lo pone el orquestador): ID canónico cuando dos entradas son el mismo hallazgo.

`scripts/build_registry.py` valida estos ficheros, une el tratamiento que propone `13` (MOD y PQ que lo resuelven) y genera la tabla del registro en `09-valor-adicional.md`. El resto de documentos citan el hallazgo por su ID y no repiten su severidad.

---

## 4. Pasada de coherencia (orquestador, fase 6)

Antes de escribir `00`, el orquestador lee todos los documentos y:

1. **Contradicciones** (una cifra, un comportamiento o un hecho distinto según el documento): comprueba en `<trabajo>/` cuál es correcto y **corrige el documento equivocado** en su sitio. Prohibido dejar notas del tipo «X todavía dice…» o «esto matiza a…».
2. **Duplicados**: si dos propietarios registraron lo mismo, pon `duplicadoDe` en el JSON del que no es propietario y sustituye en su documento la fila por una línea que enlace el ID canónico. Donde se cite el ID fusionado (otros documentos, `<trabajo>/modernizacion.json`), cámbialo por el canónico.
3. **Severidad repetida**: fuera del documento propietario, una mención a un hallazgo lleva su ID y no su severidad.
4. **«Para otras áreas»** de los informes: si el propietario no lo recogió, regístralo tú con el prefijo del área y el siguiente número libre en `orquestador.json`, y añade su fila en la sección Hallazgos del documento propietario. Si venía de rebuild-architect (un MOD con «Resuelve: —»), añade el nuevo ID a ese MOD en `<trabajo>/modernizacion.json` y en su ficha de `13`.
5. Vuelve a ejecutar `build_registry.py` y corrige lo que reporte.
