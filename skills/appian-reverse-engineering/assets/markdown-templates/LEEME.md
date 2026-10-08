<!--
  Plantilla LEEME — Guía de lectura (orquestador, fase 6, lo último que se escribe). Objetivo 1-2 pantallas, máximo 3.
  - No repite datos de otros documentos: las cifras, el entorno y la fecha están en 00.
  - «Preguntas de esta revisión»: una fila por pregunta de `preguntas` (<trabajo>/output_preferences.json), copiada tal
    cual. Estado: Respondida, Parcial o Sin resolver. «Dónde se responde»: el enlace al documento que la responde; si
    no se respondió del todo, el ID de su NV o, si lo impide una limitación global, el enlace a «Qué no incluye». Se
    cierra en la fase 8.
  - «Qué documento responde a cada pregunta»: las preguntas de cada documento, resumidas, y el rango real de IDs de esta
    ejecución (p. ej. PAN-001…PAN-006, H-SEG-01…H-SEG-04); «—» si no tiene.
  - «Sin verificar»: la tabla la escribe build_datos.py entre los dos marcadores, desde los NV de los agentes. No
    escribas dentro ni cambies los marcadores.
  - «Qué no incluye»: las tres primeras líneas van siempre; añade las de esta ejecución que de verdad falten (omite las
    que no apliquen: si hubo role maps o MCP opcionales, no van aquí). Las limitaciones globales (entorno, versión,
    muestra de ejecuciones, configuración que el Dev MCP no devuelve) se explican aquí una vez y no son NV; los demás
    documentos marcan las cifras afectadas con «orientativo (ver LEEME)». Si ningún documento usa esa marca, quita su
    fila de «Cómo leer».
  - «Términos de Appian»: un enlace a la documentación oficial por término que usen los documentos, sin definirlo.
    Quita los que no aparezcan; uno que falte va con la página que dé el Docs MCP.
  - Celdas ≤ 100 caracteres. Un solo TL;DR.
-->

# {{Nombre visible de la aplicación}}: documentación de ingeniería inversa

> **Responde a:** ¿Qué se preguntó en esta revisión y dónde se responde? ¿Por dónde empiezo según mi perfil y qué documento responde a cada pregunta? ¿Cómo se leen las marcas, los identificadores y las evidencias? ¿Qué quedó sin verificar y qué hace falta para verificarlo? ¿Qué no incluye esta documentación?

> **TL;DR**: Cómo está hecha `{{nombre técnico}}`, leída del entorno en solo lectura: la aplicación no se modificó. Empieza por [00-resumen-ejecutivo.md](./00-resumen-ejecutivo.md) y sigue la ruta de tu perfil.

## Preguntas de esta revisión

Lo que el equipo quería saber al empezar{{, o «qué hace, cómo está hecha y qué riesgos tiene» si no dijo otra cosa}}.

| Pregunta | Estado | Dónde se responde |
|---|---|---|
| {{¿Qué hace la aplicación?}} | Respondida | [01-funcional.md](./01-funcional.md) |
| {{¿Qué riesgos tiene?}} | Parcial | [Registro de 09](./09-valor-adicional.md#registro-de-hallazgos) · {{NV-SEG-01}} |

## Por dónde empezar

| Perfil | Ruta de lectura |
|---|---|
| Nuevo en el proyecto | 00 → 01 → 10 → 02 → 08 (índice) → 03 |
| Quien la mantiene | 02 → 03 → 08 → 05 y 06 → 04 → 07 → 09 → INVENTARIO → anexo/ |
| Negocio, para validar | 01 → 11 |
| Auditoría o seguridad | 04 → 06 → 05 → 09 (registro de hallazgos) |

## Qué documento responde a cada pregunta

| Documento | Responde a | IDs |
|---|---|---|
| [00-resumen-ejecutivo.md](./00-resumen-ejecutivo.md) | ¿Qué es, qué tamaño tiene y qué es lo más grave? ¿Cuánto se puede confiar en esta documentación? | — |
| [01-funcional.md](./01-funcional.md) | ¿Qué hace, para quién y cómo empieza cada caso de uso? ¿Qué pasos sigue? | {{H-FUN-01…H-FUN-02}} |
| [02-arquitectura.md](./02-arquitectura.md) | ¿Qué objetos hay por capa y quién llama a quién? ¿Qué no viaja con la aplicación? | {{H-ARQ-01…H-ARQ-03}} |
| [03-modelo-datos.md](./03-modelo-datos.md) | ¿Qué entidades hay, cómo se relacionan y cuántos registros tienen? | {{H-DAT-01…H-DAT-04}} |
| [04-seguridad-grupos.md](./04-seguridad-grupos.md) | ¿Quién puede ver, iniciar o administrar cada cosa? ¿Qué secretos hay escritos? | {{H-SEG-01…H-SEG-03}} |
| [05-integraciones-consumidas.md](./05-integraciones-consumidas.md) | ¿A qué sistemas llama, desde dónde y qué falla si cae una integración? | {{H-INT-01…H-INT-02}} |
| [06-apis-expuestas.md](./06-apis-expuestas.md) | ¿Qué ofrece a otros sistemas y quién puede llamarlo? | {{H-API-01}} |
| [07-batches.md](./07-batches.md) | ¿Qué se ejecuta solo, cada cuánto y con qué cuenta? | {{H-BAT-01}} |
| [08-procesos-bpmn/indice.md](./08-procesos-bpmn/indice.md) | ¿Qué procesos hay, cómo empieza cada uno y qué pasos sigue? | {{H-PRO-01…H-PRO-05}} |
| [09-valor-adicional.md](./09-valor-adicional.md) | ¿Qué cambia por entorno, qué no usa nadie y quién la cambió? ¿Qué hallazgos hay? | {{H-GEN-01…H-GEN-02}} |
| [10-pantallas.md](./10-pantallas.md) | ¿Qué pantallas hay, quién las ve y qué guarda cada una? | {{PAN-001…PAN-006}} |
| [11-reglas-negocio.md](./11-reglas-negocio.md) | ¿Qué decide la aplicación y dónde? | {{RN-001…RN-012}} |
| [INVENTARIO.md](./INVENTARIO.md) | ¿Qué objetos tiene, con su uuid, y de cuáles no hay definición? | — |
| [anexo/indice.md](./anexo/indice.md) | ¿Qué dice exactamente la definición de un objeto? | — |

## Cómo leer

| Marca o término | Qué significa |
|---|---|
| ✅ | Verificado: la definición o la respuesta de Appian lo muestra. |
| 🔶 | Inferido: el documento dice de qué evidencia indirecta («según su nombre»: solo lo dice el nombre). |
| ❓ | Pendiente, no un defecto: falta el dato o lo valida negocio. Si tiene NV, en «Sin verificar». |
| no encontrado en … | Se buscó en ese ámbito (la aplicación, el entorno o una herramienta) y no está; puede estar fuera. |
| Alta | Hallazgo que rompe un requisito de negocio o de seguridad, pierde datos o expone credenciales. |
| Media | Hallazgo que degrada el mantenimiento, el rendimiento o el control. |
| Baja | Hallazgo de higiene: nombres, tamaño o restos sin uso. |
| Proceso crítico | Lo deciden los objetos que lo lanzan, las integraciones que llama, su temporizador y sus tareas. |
| Referencias | Veces que lo citan otros objetos, según Appian y las definiciones: pueden ser más que en Appian. |
| orientativo (ver LEEME) | Cifra que depende de una limitación de esta extracción (ver «Qué no incluye»). |

**Identificadores**

| Prefijo | Qué es | Dónde |
|---|---|---|
| `H-<ÁREA>-NN` | Hallazgo: qué pasa y qué riesgo tiene; el área dice su documento | Su documento y el [registro de 09](./09-valor-adicional.md#registro-de-hallazgos) |
| `NV-<ÁREA>-NN` | Sin verificar: dónde se buscó, qué hace falta y a quién pedirlo | Su documento y [Sin verificar](#sin-verificar) |
| `PAN-NNN` | Pantalla | 10 |
| `RN-NNN` | Regla de negocio | 11 |

**Evidencia**

| Forma | Qué indica |
|---|---|
| `mcp:tipo/nombre#ubicación` | Objeto y punto de su definición; el enlace abre su ficha en el [anexo](./anexo/indice.md). |
| `@dependents` · `@history` · `@versions` | Tras el nombre, la respuesta de la que sale: quién lo usa · ejecuciones · versiones. |
| `@validation` · `@screen` · `@members` | Avisos de la plataforma · pantalla renderizada · miembros del grupo. |
| `@other:<herramienta>` | Otra respuesta de la plataforma (p. ej. el role map). |
| `graph:hubs` · `graph:orphans` · `graph:edge/A→B` | Conclusión del grafo de referencias entre objetos ([anexo/grafo.md](./anexo/grafo.md)). |
| `Fuente: <URL>` | Documentación oficial de Appian. |

## Sin verificar

Lo que esta revisión no pudo verificar, qué hace falta para hacerlo y a quién pedirlo. Lo que falta en toda la documentación está en [Qué no incluye](#qué-no-incluye).

<!-- sin-verificar:inicio -->
(lo rellena build_datos.py)
<!-- sin-verificar:fin -->

## Qué no incluye

- Datos de negocio: ninguna herramienta de datos (filas, variables de procesos, datos de tareas); el render (`@screen`) muestra lo que cada interfaz consulta al evaluarse con entradas vacías.
- Valores de otros entornos: solo los de `{{url}}`; los demás están en el paquete de despliegue.
- Configuración que el Dev MCP no devuelve (excepciones y alertas de nodos, destinatarios de correo, seguridad de acciones de record): marcada ❓.
- {{Definición de N CDTs y N decisiones: el Dev MCP no la devuelve (ver INVENTARIO).}}
- {{Seguridad por objeto (role maps): no disponible.}}
- {{Volúmenes de datos: Appian MCP Server no disponible.}}
- {{Verificación con la documentación oficial: sin Docs MCP ni acceso a docs.appian.com; lo que depende de ella va marcado «sin verificar».}}
- {{Versión de Appian: no determinada; las fuentes son de la documentación más reciente.}}
- {{Uso real: el entorno no consta como producción y la muestra son las últimas N ejecuciones de cada proceso. Las cifras son orientativas y los documentos las marcan «orientativo (ver LEEME)»{{; la muestra es uniforme (mismo iniciador y hora): no dice quién usa cada proceso ni cuándo}}.}}

## Términos de Appian

| Tema | Documentación de Appian |
|---|---|
| Datos | [Record type](https://docs.appian.com/suite/help/26.6/Record_Type_Object.html) · [relación](https://docs.appian.com/suite/help/26.6/record-type-relationships.html) · [sincronización](https://docs.appian.com/suite/help/26.6/about-data-sync.html) · [evento de record](https://docs.appian.com/suite/help/26.6/record-events.html) · [CDT](https://docs.appian.com/suite/help/26.6/Custom_Data_Types.html) · [data store](https://docs.appian.com/suite/help/26.6/Data_Stores.html) |
| Pantallas | [Interfaz](https://docs.appian.com/suite/help/26.6/interface_object.html) · [site](https://docs.appian.com/suite/help/26.6/Sites.html) · [vista de record](https://docs.appian.com/suite/help/26.6/record-view.html) · [acción de lista](https://docs.appian.com/suite/help/26.6/record-actions.html#record-list-actions) · [acción relacionada](https://docs.appian.com/suite/help/26.6/record-actions.html#related-actions) |
| Procesos | [Process model](https://docs.appian.com/suite/help/26.6/process-model-object.html) · [subproceso](https://docs.appian.com/suite/help/26.6/Sub-Process_Activity.html) · [temporizador](https://docs.appian.com/suite/help/26.6/Intermediate_Event_-_Timer.html) · [Write Records](https://docs.appian.com/suite/help/26.6/Write_Records_Smart_Service.html) |
| Reglas | [Expresiones](https://docs.appian.com/suite/help/26.6/Expressions.html) · [expression rule](https://docs.appian.com/suite/help/26.6/Expression_Rules.html) · [decisión](https://docs.appian.com/suite/help/26.6/Decisions.html) · [constante](https://docs.appian.com/suite/help/26.6/Constants.html) · [agente de IA](https://docs.appian.com/suite/help/26.6/about-ai-agents.html) |
| Integración | [Integración](https://docs.appian.com/suite/help/26.6/Integration_Object.html) · [connected system](https://docs.appian.com/suite/help/26.6/Connected_System_Object.html) · [Web API](https://docs.appian.com/suite/help/26.6/Web_APIs.html) |
| Seguridad | [Grupo](https://docs.appian.com/suite/help/26.6/Creating_Groups.html) · [grupos de sistema](https://docs.appian.com/suite/help/26.6/System_Groups.html) · [role map](https://docs.appian.com/suite/help/26.6/object-security.html#groups-and-role-maps) · [seguridad de un process model](https://docs.appian.com/suite/help/26.6/process-model-object.html#process-model-security) |
| Fuera de la aplicación | [Plug-in](https://docs.appian.com/suite/help/26.6/prepare-deployment-packages.html#add-plugins) · [knowledge center](https://docs.appian.com/suite/help/26.6/folder-object.html#knowledge-centers) · [translation set](https://docs.appian.com/suite/help/26.6/translation-set-object.html) · [`rule!` y `cons!`](https://docs.appian.com/suite/help/26.6/reference-objects.html) |
| Negocio | El vocabulario de la aplicación, en el [glosario de 09](./09-valor-adicional.md#glosario-de-negocio) |

> Esta carpeta lleva también la extracción de la que sale la documentación, tal cual la devolvió el Dev MCP. Para consultar un objeto, usa su ficha del [anexo](./anexo/indice.md).
