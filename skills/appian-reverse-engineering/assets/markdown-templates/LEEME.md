<!--
  Plantilla LEEME: la entrada a la documentación (orquestador, fase 6, lo último que se escribe, después de
  build_summary.py). Objetivo 2 pantallas, máximo 3. Un solo TL;DR. Celdas ≤ 100 caracteres. Las secciones sin datos
  se omiten.
  - Cifras: de <trabajo>/summary.json, sin recalcularlas ni copiarlas de otros documentos. Si summary.json contradice
    un documento, corrige el documento en la pasada de coherencia y vuelve a generar summary.json.
      Datos ............... meta.environment {url, isProduction, appianVersion}; fecha: meta.source.extractedAt;
                            confianza: meta.confidence + meta.confidenceBasis (unidos por «; »)
      En cifras ........... counts, totals y layerBreakdown (sus 6 claves, en el orden y con los nombres de 02; una
                            capa con 0 objetos se omite)
      Procesos críticos ... criticalProcesses (ya ordenados; máx. 5). Enlace: slug de objects.processModel
      Hallazgos ........... findingsBySeverity, findingsByCertainty y findings de severidad Alta (si no hay Alta, los
                            Media, máx. 5, y dilo en el TL;DR), por su ID y sin severidad. Evidencia: la de cada uno en
                            <trabajo>/registro.json, enlazada a la ficha de su objeto (anexo/<tipo>/<slug>.md, slug de
                            inventory.json). Los secretos son hallazgos H-SEG de severidad Alta.
      Uso real ............ usage de los procesos críticos y de los 3-5 más ejecutados (failedInSampleOf = fallos en una
                            muestra) y signals[type=processModelsWithoutExecutions]. Los fallos citan su H-PRO (08);
                            los procesos sin ejecuciones, su H-GEN (09). Sin historial, una línea: «La extracción no
                            trae historial de ejecuciones.»
  - Ejecuciones: si el entorno no consta como producción, «orientativas» en la cabecera, con el enlace a «Qué no
    incluye»; si consta, sin la marca.
  - «Preguntas de esta revisión»: una fila por pregunta de `preguntas` (<trabajo>/output_preferences.json), copiada tal
    cual. Estado: Respondida, Parcial o Sin resolver. «Dónde se responde»: el enlace al documento que la responde; si no
    se respondió del todo, el ID de su NV o, si lo impide una limitación global, el enlace a «Qué no incluye». Se cierra
    en la fase 8.
  - «Sin verificar»: la tabla la escribe build_datos.py entre los dos marcadores. No escribas dentro ni cambies los
    marcadores.
  - «Qué no incluye»: cada línea, solo si es verdad en esta extracción; compruébalo en ella antes de escribirla (si los
    nodos de correo traen sus destinatarios, no digas que faltan). Añade lo que falte de verdad. Las limitaciones
    globales se explican aquí una vez y no son NV; los demás documentos marcan las cifras afectadas con «orientativo
    (ver LEEME)».
  - «Términos de Appian»: un enlace a la documentación oficial por término que usen los documentos, sin definirlo.
    Quita los que no aparezcan; uno que falte va con la página que dé el Docs MCP, en la forma /latest/.
-->

# {{meta.appName}}: documentación de ingeniería inversa

> **Responde a:** ¿Qué es la aplicación, qué tamaño tiene y qué es lo más grave? ¿Qué procesos son críticos y cuánto se usan? ¿Qué se preguntó en esta revisión y dónde se responde? ¿Por dónde empiezo y cómo se leen las marcas y las evidencias? ¿Cuánto se puede confiar en esta documentación, qué no incluye y qué quedó sin verificar?

> **TL;DR**: {{Qué hace la aplicación y para quién, en lenguaje de negocio, 1-2 frases}}. {{Lo más grave: el hallazgo Alta principal en una frase}}.
> **Volumen**: {{totals.objects}} objetos ({{n}} process models, {{n}} interfaces, {{n}} record types). **Hallazgos**: {{N}} (Alta: {{findingsBySeverity.Alta}}).

| Dato | Valor |
|---|---|
| Entorno | `{{meta.environment.url}}` ({{producción / no productivo / no consta si es producción}}) |
| Versión de Appian | {{meta.environment.appianVersion o «no determinada»}} |
| Extracción | {{AAAA-MM-DD de meta.source.extractedAt}}, en solo lectura |
| Confianza de la documentación | **{{meta.confidence}}**: {{meta.confidenceBasis}} |

## La aplicación en cifras

| Capa | Objetos | Qué incluye | Dónde |
|---|---|---|---|
| Entrada y presentación | {{layerBreakdown["Entrada y presentación"]}} | {{n}} sites, {{n}} interfaces, {{n}} Web APIs | [10](./10-pantallas.md), [06](./06-apis-expuestas.md) |
| Lógica | {{layerBreakdown["Lógica"]}} | {{n}} process models ({{n}} programados), {{n}} reglas, {{n}} decisiones, {{n}} agentes de IA | [08](./08-procesos-bpmn/indice.md), [11](./11-reglas-negocio.md) |
| Datos | {{layerBreakdown["Datos"]}} | {{n}} record types, {{n}} CDTs, {{n}} data stores | [03](./03-modelo-datos.md) |
| Integración | {{layerBreakdown["Integración"]}} | {{n}} integraciones, {{n}} connected systems | [05](./05-integraciones-consumidas.md) |
| Transversal | {{layerBreakdown["Transversal"]}} | {{n}} constantes | [02](./02-arquitectura.md), [09](./09-valor-adicional.md#configuración-por-entorno) |
| Seguridad | {{layerBreakdown["Seguridad"]}} | {{n}} grupos | [04](./04-seguridad-grupos.md) |

{{totals.withDefinition}} de {{totals.objects}} objetos con definición ([INVENTARIO](./INVENTARIO.md)){{; fuera de las capas: n carpetas, n …}} · {{totals.hubs}} muy referenciados ([02](./02-arquitectura.md)) · {{totals.orphans}} sin referencias ([09](./09-valor-adicional.md#objetos-huérfanos)).

## Procesos críticos

| Proceso | Por qué es crítico | Programado |
|---|---|---|
| [`{{name}}`](./08-procesos-bpmn/{{slug}}.md) | {{reasons, unidas por «, »}} | Sí/No |

{{Si hay más de 5: «Hay N procesos críticos; el resto, en el [índice de procesos](./08-procesos-bpmn/indice.md).»}}

## Hallazgos principales

Por severidad: Alta {{n}} · Media {{n}} · Baja {{n}}. Por certeza: verificados {{n}} · inferidos {{n}} · pendientes {{n}}. Todos, en el [registro de 09](./09-valor-adicional.md#registro-de-hallazgos).

| ID | Hallazgo | Área | Certeza | Evidencia |
|---|---|---|---|---|
| [{{H-SEG-01}}](./{{documento}}) | {{titulo}} | {{area}} | ✅ | [`mcp:{{tipo}}/{{nombre}}#{{ubicación}}`](./anexo/{{tipo}}/{{slug}}.md) |

## Uso real

| Proceso | Ejecuciones{{, orientativas ([Qué no incluye](#qué-no-incluye))}} | Última | Fallos en la muestra |
|---|---|---|---|
| [`{{name}}`](./08-procesos-bpmn/{{slug}}.md) | {{executions}} | {{AAAA-MM-DD}} | {{«3 de las últimas 50» ([H-PRO-NN](./08-procesos-bpmn/{{slug}}.md#hallazgos)) o «—»}} |

{{N}} process models sin ejecuciones: `{{a}}`, `{{b}}` ([{{H-GEN-NN}}](./09-valor-adicional.md#hallazgos)).

## Preguntas de esta revisión

Lo que el equipo quería saber al empezar{{, o «qué hace, cómo está hecha y qué riesgos tiene» si no dijo otra cosa}}.

| Pregunta | Estado | Dónde se responde |
|---|---|---|
| {{¿Qué hace la aplicación?}} | Respondida | [01-funcional.md](./01-funcional.md) |
| {{¿Qué riesgos tiene?}} | Parcial | [Registro de 09](./09-valor-adicional.md#registro-de-hallazgos) · {{NV-SEG-01}} |

## Por dónde empezar

Documentos: [01 Funcional](./01-funcional.md) · [02 Arquitectura](./02-arquitectura.md) · [03 Datos](./03-modelo-datos.md) · [04 Seguridad](./04-seguridad-grupos.md) · [05 Integraciones](./05-integraciones-consumidas.md) · [06 APIs](./06-apis-expuestas.md) · [07 Batches](./07-batches.md) · [08 Procesos](./08-procesos-bpmn/indice.md) · [09 Valor adicional](./09-valor-adicional.md) · [10 Pantallas](./10-pantallas.md) · [11 Reglas de negocio](./11-reglas-negocio.md) · [INVENTARIO](./INVENTARIO.md) · [anexo](./anexo/indice.md).

| Perfil | Ruta de lectura |
|---|---|
| Nuevo en el proyecto | [01](./01-funcional.md) → [10](./10-pantallas.md) → [02](./02-arquitectura.md) → [08](./08-procesos-bpmn/indice.md) → [03](./03-modelo-datos.md) |
| Quien la mantiene | [02](./02-arquitectura.md) → [03](./03-modelo-datos.md) → [08](./08-procesos-bpmn/indice.md) → [05](./05-integraciones-consumidas.md) y [06](./06-apis-expuestas.md) → [04](./04-seguridad-grupos.md) → [07](./07-batches.md) → [09](./09-valor-adicional.md) → [INVENTARIO](./INVENTARIO.md) → [anexo](./anexo/indice.md) |
| Negocio, para validar | [01](./01-funcional.md) → [11](./11-reglas-negocio.md) |
| Auditoría o seguridad | [04](./04-seguridad-grupos.md) → [06](./06-apis-expuestas.md) → [05](./05-integraciones-consumidas.md) → [registro de 09](./09-valor-adicional.md#registro-de-hallazgos) |

## Cómo leer

| Marca o término | Qué significa |
|---|---|
| ✅ | Verificado: la definición o la respuesta de Appian lo muestra. |
| 🔶 | Inferido: el documento dice de qué evidencia indirecta («según su nombre»: solo lo dice el nombre). |
| ❓ | Pendiente, no un defecto: falta el dato o lo valida negocio. |
| Alta | Hallazgo que rompe un requisito de negocio o de seguridad, pierde datos o expone credenciales. |
| Media | Hallazgo que degrada el mantenimiento, el rendimiento o el control. |
| Baja | Hallazgo de higiene: nombres, tamaño o restos sin uso. |
| `H-<ÁREA>-NN` | Hallazgo, en el documento de su área y en el [registro de 09](./09-valor-adicional.md#registro-de-hallazgos). |
| `NV-<ÁREA>-NN` | Lo que no se pudo verificar, en [Sin verificar](#sin-verificar). |
| `PAN-NNN` · `RN-NNN` | Pantalla de [10](./10-pantallas.md) · regla de negocio de [11](./11-reglas-negocio.md). |
| Referencias | Veces que lo citan otros objetos, según Appian y las definiciones: pueden ser más que en Appian. |

Cada evidencia enlaza la ficha de su objeto en el [anexo](./anexo/indice.md): `mcp:<tipo>/<nombre>#<ubicación>` es un punto de la definición y `@<rol>` tras el nombre, otra respuesta de Appian, con su apartado en la ficha. Las de `graph:` llevan al [grafo de referencias](./anexo/grafo.md).

## Sin verificar

<!-- sin-verificar:inicio -->
(lo rellena build_datos.py)
<!-- sin-verificar:fin -->

## Qué no incluye

- {{Datos de negocio: ninguna herramienta de datos (filas, variables de procesos, datos de tareas){{; el render (`@screen`) muestra lo que cada interfaz consulta al evaluarse con entradas vacías}}.}}
- {{Valores de otros entornos: solo los de `{{meta.environment.url}}`; los demás están en el paquete de despliegue.}}
- {{Configuración que la extracción no trae, solo la que de verdad falte (excepciones y alertas de los nodos, destinatarios de correo, seguridad de las acciones de record…): marcada ❓.}}
- {{Definición de N CDTs y N decisiones: el Dev MCP no la devuelve (ver INVENTARIO).}}
- {{Seguridad por objeto (role maps): no disponible.}}
- {{Volúmenes de datos: Appian MCP Server no disponible.}}
- {{Verificación con la documentación oficial: sin Docs MCP ni acceso a docs.appian.com; lo que depende de ella va marcado «sin verificar».}}
- {{Versión de Appian: no determinada; las fuentes son de la documentación más reciente.}}
- {{Imágenes de los diagramas: no había navegador al generarlas. Los procesos se ven abriendo su `.drawio` en draw.io (o su `.bpmn` en Camunda Modeler o bpmn.io) y los demás diagramas van como bloque mermaid, sin validar.}}
- {{Uso real: el entorno no consta como producción y la muestra son las últimas N ejecuciones de cada proceso. Las cifras son orientativas y los documentos las marcan «orientativo (ver LEEME)»{{; la muestra es uniforme (mismo iniciador y hora): no dice quién usa cada proceso ni cuándo}}.}}

## Términos de Appian

| Tema | Documentación de Appian |
|---|---|
| Datos | [Record type](https://docs.appian.com/suite/help/latest/Record_Type_Object.html) · [relación](https://docs.appian.com/suite/help/latest/record-type-relationships.html) · [sincronización](https://docs.appian.com/suite/help/latest/about-data-sync.html) · [evento de record](https://docs.appian.com/suite/help/latest/record-events.html) · [CDT](https://docs.appian.com/suite/help/latest/Custom_Data_Types.html) · [data store](https://docs.appian.com/suite/help/latest/Data_Stores.html) |
| Pantallas | [Interfaz](https://docs.appian.com/suite/help/latest/interface_object.html) · [site](https://docs.appian.com/suite/help/latest/Sites.html) · [vista de record](https://docs.appian.com/suite/help/latest/record-view.html) · [acción de lista](https://docs.appian.com/suite/help/latest/record-actions.html#record-list-actions) · [acción relacionada](https://docs.appian.com/suite/help/latest/record-actions.html#related-actions) |
| Procesos | [Process model](https://docs.appian.com/suite/help/latest/process-model-object.html) · [subproceso](https://docs.appian.com/suite/help/latest/Sub-Process_Activity.html) · [temporizador](https://docs.appian.com/suite/help/latest/Intermediate_Event_-_Timer.html) · [Write Records](https://docs.appian.com/suite/help/latest/Write_Records_Smart_Service.html) |
| Reglas | [Expresiones](https://docs.appian.com/suite/help/latest/Expressions.html) · [expression rule](https://docs.appian.com/suite/help/latest/Expression_Rules.html) · [decisión](https://docs.appian.com/suite/help/latest/Decisions.html) · [constante](https://docs.appian.com/suite/help/latest/Constants.html) · [agente de IA](https://docs.appian.com/suite/help/latest/about-ai-agents.html) |
| Integración | [Integración](https://docs.appian.com/suite/help/latest/Integration_Object.html) · [connected system](https://docs.appian.com/suite/help/latest/Connected_System_Object.html) · [Web API](https://docs.appian.com/suite/help/latest/Web_APIs.html) |
| Seguridad | [Grupo](https://docs.appian.com/suite/help/latest/Creating_Groups.html) · [grupos de sistema](https://docs.appian.com/suite/help/latest/System_Groups.html) · [role map](https://docs.appian.com/suite/help/latest/object-security.html#groups-and-role-maps) · [seguridad de un process model](https://docs.appian.com/suite/help/latest/process-model-object.html#process-model-security) |
| Fuera de la aplicación | [Plug-in](https://docs.appian.com/suite/help/latest/prepare-deployment-packages.html#add-plugins) · [knowledge center](https://docs.appian.com/suite/help/latest/folder-object.html#knowledge-centers) · [translation set](https://docs.appian.com/suite/help/latest/translation-set-object.html) · [`rule!` y `cons!`](https://docs.appian.com/suite/help/latest/reference-objects.html) |
| Negocio | El vocabulario de la aplicación, en el [glosario de 09](./09-valor-adicional.md#glosario-de-negocio) |
