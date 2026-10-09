# `as-is/datos/`: lo que leen las demás skills

`build_datos.py <salida>` lo escribe en la fase 6, después de escribir LEEME, a partir del inventario, el grafo, el
registro de hallazgos, lo que no se pudo verificar y la definición de cada record type. Es lo único de ingeniería
inversa que leen las demás skills (analista y refactorización): nunca leen `extraccion/`. Si cambia el formato,
cambian también ellas; lo nuevo se añade sin cambiar el nombre de nada.

Todo en JSON, UTF-8. Las rutas son relativas a `<salida>` (la carpeta `as-is/`). Los objetos se nombran como en
Appian.

## `inventario.json`

```json
{"aplicacion": {"nombre": "DEM Gestión de Solicitudes", "prefijo": "DEM", "uuid": "…"},
 "objetos": [{"nombre": "DEM Solicitud", "tipo": "recordType", "uuid": "…",
              "anexo": "anexo/recordType/DEM_Solicitud.md",
              "tambien": ["DEM_SOLICITUD", "Resumen", "id", "titulo", "estado", "Nueva solicitud"]}]}
```

- `objetos`: todos los de la aplicación salvo ella misma, ordenados por tipo y nombre. `tipo` es el del inventario
  (`processModel`, `interface`, `recordType`…).
- `anexo`: la ficha del objeto con su definición; `null` si la extracción no la trae.
- `tambien`: los nombres que no son objetos pero se citan con él. Hoy, los de un record type: su tabla, sus vistas, sus
  campos y relaciones y sus acciones. Para el resto, `[]`.

## `dependencias.json`

```json
{"aristas": [{"de": "DEM Solicitud", "a": "DEM_SolicitudResumen", "donde": "Record View: Resumen"}],
 "fueraDeLaAplicacion": [{"nombre": "UTL_DiasLaborables", "tipo": "llamado con rule!",
                          "usadoPor": ["DEM_SolicitudForm"], "usa": [], "nv": "NV-ARQ-01"}]}
```

- `aristas`: quién usa a quién, entre objetos de la aplicación. `donde` es dónde está la referencia en `de` («Node:
  Revisar», «rule!DEM_ER_EsAdmin»…) o, si el entorno no lo dice, el tipo de referencia (`integrationCall`,
  `constRef`…).
- `fueraDeLaAplicacion`: los objetos de fuera de la aplicación que esta llama o que la llaman (los nodos externos del
  grafo). `usadoPor`: los objetos de la aplicación que lo llaman; `usa`: los que él llama. `nv`: el NV de
  `sin-verificar.json` que lo tiene en `objetos`, o `null`. `tipo`: el canónico, como en el inventario, si una
  herramienta de dependencias lo trajo (`expressionRule`, `constant`…); `constant` para un `cons!`, y «llamado con
  rule!» para un `rule!` que no trajo ninguna, porque puede ser una regla, una interfaz, una integración o una
  decisión ([fuente](https://docs.appian.com/suite/help/latest/reference-objects.html)).

## `hallazgos.json`

```json
{"hallazgos": [{"id": "H-SEG-01", "titulo": "…", "area": "secretos", "severidad": "Alta", "certeza": "verificado",
                "objetos": ["DEM_ERP_API_TOKEN"], "documento": "04-seguridad-grupos.md#hallazgos",
                "evidencia": "mcp:constant/DEM_ERP_API_TOKEN#value"}]}
```

Los del registro de `09`, sin los fusionados (`duplicadoDe`), ordenados por ID. `severidad`: Alta, Media o Baja.
`certeza`: verificado, inferido o pendiente. `documento`: dónde se explica. `objetos`: nombres de `inventario.json` o de `fueraDeLaAplicacion`; `build_datos.py` da error con uno que no esté en ninguno de los dos.
Los de certeza `inferido` llevan además `base`: las evidencias de las que salen.

## `procesos.json`

```json
{"procesos": [{"nombre": "DEM Alta Solicitud", "json": "08-procesos-bpmn/DEM_Alta_Solicitud.json", "nodos": 5,
               "ejecuciones": 120}]}
```

Un elemento por process model. `json`: el proceso en el formato de la skill de diagramas, que lo dibuja; con él se
abre su `.drawio`, al lado. `nodos`: nodos de la definición. `ejecuciones`: las que devolvió el entorno, `null` si no
las devolvió.

## `sin-verificar.json`

```json
{"sinVerificar": [{"id": "NV-ARQ-01", "pregunta": "¿Qué hace UTL_DiasLaborables?",
                   "porQue": "DEM_SolicitudForm la llama con rule! y no está en la aplicación.",
                   "queHaceFalta": "Export de la aplicación que la contiene o acceso de lectura a ella",
                   "aQuien": "Equipo de la aplicación de utilidades",
                   "dondeSeBusco": "Inventario de la aplicación y dependencias de DEM_SolicitudForm (Dev MCP)",
                   "objetos": ["DEM_SolicitudForm", "UTL_DiasLaborables"], "indicios": "…", "estado": "abierto",
                   "documento": "02-arquitectura.md#dependencias-externas"}]}
```

Lo que la revisión no pudo verificar, sin los fusionados (`duplicadoDe`), ordenado por ID. Es pendiente, no un hecho:
quien lo lea lo trata como una pregunta abierta. `queHaceFalta` empieza por acceso, export, permiso, entorno o
negocio. `estado`: abierto, parcial o resuelto. `objetos`: los de la aplicación afectados y los de fuera, por su
nombre. Formato y reglas, en `references/execution-principles.md`, «Sin verificar».
