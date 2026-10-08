# Principios de ejecución

Lectura obligatoria antes de la fase 4 y para todos los subagentes. Concentra los criterios no negociables. El formato de los documentos está en `references/presentation-rules.md`; cómo leer los datos, en `references/lectura-mcp-raw.md`.

---

## 1. Principios

1. **No inventar.** Lo que no está en los datos no se completa con suposiciones plausibles: se marca ❓ y se dice qué falta.
2. **Certeza en cada afirmación importante**: ✅ verificado, 🔵 inferido (di de qué), ❓ pendiente (di quién valida). Ver `presentation-rules.md`, Regla 7.
3. **Dato ausente no es defecto.** Que un campo no aparezca en la respuesta no prueba que no esté configurado: el Dev MCP no devuelve toda la configuración (p. ej. pestañas de excepciones y alertas de los nodos, seguridad de las acciones de record, destinatarios de correo, entradas de algunos nodos, variables de algunos procesos). Solo es ✅ si la respuesta muestra el campo vacío o nulo de forma explícita, o si otra fuente lo corrobora (render, validación de la plataforma, dependencias). Si no, la afirmación es ❓ «no lo devuelve la extracción», y un hallazgo basado en ella lleva certeza ❓ (o 🔵 con indicios) y una pregunta para validarlo. Una muestra de ejecuciones no da cifras globales y sus datos uniformes (la misma hora en todas) pueden ser un artefacto; pero lo que sí dice se usa como indicio y se contrasta: fechas posteriores a un despliegue, el grupo de la cuenta iniciadora, estados.
4. **Lo que solo dice un nombre es 🔵.** Lo que se deduce solo del nombre de un nodo, objeto o variable (sin ver su configuración ni su uso) se marca 🔵 «según su nombre». Una regla no es ✅ si un parámetro de su enunciado es ❓ (p. ej. un umbral cuya constante no llegó): lleva la certeza más baja de sus partes.
5. **Contraevidencia.** Antes de registrar un hallazgo Alta inferido (🔵), crúzalo con lo que podría desmentirlo: ejecuciones (fechas frente a versiones, grupo del iniciador), render de las interfaces, recuentos del data fabric y validación de la plataforma. Si algo lo contradice, dilo en la explicación del hallazgo y añade la pregunta que lo resuelve; si la contradicción pesa, baja la severidad o la certeza.
6. **Trazabilidad.** Cada afirmación importante lleva `Evidencia: mcp:<tipo>/<nombre>[@<rol>]#<ubicación>` (formato en `lectura-mcp-raw.md`), enlazada a la ficha del objeto en el anexo (`presentation-rules.md`, Regla 5); lo que viene de la documentación oficial, `Fuente: <URL>`.
7. **Cero relleno.** Cada documento responde a las preguntas de su plantilla (`> **Responde a:**`) y solo lleva lo que las responde. Sin placeholders, sin secciones vacías y sin explicar qué es un objeto de Appian: se enlaza su documentación. Cada objeto que se lista dice qué hace.
8. **Cada cosa en un sitio.** Un objeto tiene una ficha y un hallazgo tiene un ID, en su documento propietario; el resto enlaza (tabla de propietarios abajo).
9. **Nombres reales** (técnico y visible), nunca genéricos.
10. **Hechos, no consejos.** Un hallazgo dice qué pasa, dónde y qué riesgo tiene. Qué hacer (corregirlo, cambiar una credencial, rehacer un proceso) no se escribe: lo propone `appian-refactorizacion`.
11. **Seguridad.** Un secreto escrito en la aplicación es un hallazgo (`H-SEG`): se registra como dice `references/security-rules.md`.
12. **Diagramas que pasan el validador** (`references/mermaid-rules.md`); si no, tabla equivalente. Los `.bpmn` siguen `references/bpmn-mapping.md`.
13. **Idioma**: español técnico neutro salvo que el usuario pida otro.

---

## 2. Documentos propietarios

Cada área tiene un documento propietario y un prefijo para los IDs de sus hallazgos. Solo el propietario registra hallazgos de su área.

| Área | Documento | Autor | Prefijo |
|---|---|---|---|
| Funcional: casos de uso, funcionalidades ausentes | `01-funcional.md` | interface-analyzer | `H-FUN` |
| Arquitectura: acoplamientos, hubs, dependencias externas, objetos huérfanos (el hallazgo) | `02-arquitectura.md` | interface-analyzer | `H-ARQ` |
| Datos: record types, CDTs, relaciones, volúmenes | `03-modelo-datos.md` | data-modeler | `H-DAT` |
| Seguridad, grupos y secretos | `04-seguridad-grupos.md` | integration-security-analyzer | `H-SEG` |
| Integraciones consumidas | `05-integraciones-consumidas.md` | integration-security-analyzer | `H-INT` |
| APIs expuestas | `06-apis-expuestas.md` | integration-security-analyzer | `H-API` |
| Batches | `07-batches.md` | orquestador | `H-BAT` |
| Procesos, también las instancias fallidas o detenidas de la muestra de ejecuciones | `08-procesos-bpmn/<slug>.md` | process-modeler | `H-PRO` |
| Mantenimiento, validación de la plataforma, versionado, métricas, procesos sin ejecuciones (área `uso`) y la lista de objetos huérfanos | `09-valor-adicional.md` | orquestador | `H-GEN` |
| Pantallas | `10-pantallas.md` | ui-rules-analyzer | `H-UI` |
| Reglas de negocio | `11-reglas-negocio.md` | ui-rules-analyzer | `H-RN` |

Si al analizar tu área ves algo de otra (p. ej. ui-rules-analyzer nota que un proceso ignora «Cancelar»), descríbelo en una frase **sin severidad** donde tu documento lo necesite, enlaza el documento propietario y menciónalo en tu informe final bajo «Para otras áreas». El orquestador decide en la pasada de coherencia.

**Un solo dueño por señal.** Las señales que ven varios agentes tienen un único dueño; los demás citan su ID:

- Process model sin ejecuciones: `H-GEN` (09). 07 y 02 citan el ID.
- Instancias fallidas o detenidas en la muestra de ejecuciones: `H-PRO` (08). 07 y 00 citan el ID.
- Process model de más de 50 nodos: `H-GEN` (09). 08 y 02 citan el ID.
- Objetos huérfanos: la lista es una sola, en 09 («Objetos huérfanos»); el hallazgo es `H-ARQ` (02). 03, 10 y los demás citan `H-ARQ`/`H-GEN` o enlazan esa lista, sin repetirla.

---

## 3. Registro de hallazgos

Un hallazgo es algo que pasa en la aplicación y tiene un riesgo de negocio, de seguridad, de mantenimiento o de rendimiento: dice qué pasa, dónde y qué riesgo tiene, no qué hacer (principio 10). Cada propietario los registra en dos sitios:

1. En su documento, sección `## Hallazgos`:

   ```markdown
   | ID | Hallazgo | Severidad | Certeza | Evidencia |
   |---|---|---|---|---|
   | H-PRO-01 | «Cancelar» no anula el alta | Alta | ✅ | [`mcp:processModel/DEM Alta Solicitud#nodes[id=1].connections`](../anexo/processModel/DEM_Alta_Solicitud.md) |
   ```

   Un hallazgo Alta lleva debajo una línea con su impacto: qué puede pasar y a quién afecta.

2. En `<trabajo>/hallazgos/<agente>.json` (el orquestador usa `orquestador.json`), una lista con un objeto por hallazgo:

   ```json
   [{"id": "H-PRO-01", "titulo": "«Cancelar» no anula el alta", "area": "procesos",
     "severidad": "Alta", "certeza": "verificado", "objetos": ["DEM Alta Solicitud"],
     "documento": "08-procesos-bpmn/DEM_Alta_Solicitud.md#hallazgos",
     "evidencia": "mcp:processModel/DEM Alta Solicitud#nodes[id=1].connections",
     "impacto": "Una solicitud cancelada se registra igualmente."}]
   ```

   - `id`: prefijo del área + número de dos cifras, sin huecos (`H-PRO-01`, `H-PRO-02`…).
   - `impacto`: qué puede pasar y a quién afecta. Qué hacer no va en ningún campo: `build_registry.py` avisa si un hallazgo lo trae.
   - `area`: funcional, arquitectura, datos, seguridad, secretos, integraciones, apis, batches, procesos, pantallas, reglas, mantenimiento, rendimiento o uso.
   - `severidad`: Alta, Media o Baja. `certeza`: verificado, inferido o pendiente.
   - `documento`: ruta relativa a `<salida>` (con ancla si quieres).
   - `duplicadoDe` (solo lo pone el orquestador): ID canónico cuando dos entradas son el mismo hallazgo.

**La certeza viaja con el hallazgo.** Un hallazgo 🔵 o ❓ conserva su marca, o se redacta en condicional («probablemente», «la definición indica»), allí donde se resuma: TL;DR, 00 y tablas de reglas. Un hallazgo se explica solo en su documento propietario; en los demás, una línea con su ID.

`<skill>/scripts/build_registry.py` valida estos ficheros y genera la tabla del registro en `09-valor-adicional.md`. El resto de documentos citan el hallazgo por su ID y no repiten su severidad.

---

## 4. Pasada de coherencia (orquestador, fase 6)

Antes de escribir `00`, el orquestador lee todos los documentos y:

1. **Contradicciones** (una cifra, un comportamiento o un hecho distinto según el documento): comprueba en `<trabajo>/` cuál es correcto y **corrige el documento equivocado** en su sitio. Prohibido dejar notas del tipo «X todavía dice…» o «esto matiza a…».
2. **Duplicados**: si dos propietarios registraron lo mismo, pon `duplicadoDe` en el JSON del que no es propietario y sustituye en su documento la fila por una línea que enlace el ID canónico. Donde se cite el ID fusionado, cámbialo por el canónico.
3. **Lo pendiente, igual en todas partes**: un comportamiento ❓ (p. ej. si un subproceso es síncrono, cuándo se avisa a un sistema externo) se formula con la misma frase en todos los documentos que lo citan, y ninguno lo da por hecho.
4. **Severidad repetida**: fuera del documento propietario, una mención a un hallazgo lleva su ID y no su severidad.
5. **«Para otras áreas»** de los informes: si el propietario no lo recogió, regístralo tú con el prefijo del área y el siguiente número libre en `orquestador.json`, y añade su fila en la sección Hallazgos del documento propietario.
6. **IDs en las menciones**: completa en 01–11 cada mención a otra área con el ID canónico del hallazgo y su enlace (los agentes escriben sin conocer los IDs de los que van a la vez o después).
7. Vuelve a ejecutar `python3 <skill>/scripts/build_registry.py <salida>` y corrige lo que reporte.
