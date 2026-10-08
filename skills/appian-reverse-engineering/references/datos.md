# `as-is/datos/`: lo que leen las demás skills

`build_datos.py <salida>` lo escribe en la fase 6, después de `build_summary.py`, a partir del inventario, el grafo, el
registro de hallazgos y la definición de cada record type. Es lo único de ingeniería inversa que leen las demás skills
(analista y refactorización): nunca leen `extraccion/`. Si cambia el formato, cambian también ellas.

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
{"aristas": [{"de": "DEM Solicitud", "a": "DEM_SolicitudResumen", "donde": "Record View: Resumen"}]}
```

Quién usa a quién, entre objetos de la aplicación (las referencias a objetos de fuera están en `anexo/grafo.md`).
`donde` es dónde está la referencia en `de` («Node: Revisar», «rule!DEM_ER_EsAdmin»…) o, si el entorno no lo dice, el
tipo de referencia (`integrationCall`, `constRef`…).

## `hallazgos.json`

```json
{"hallazgos": [{"id": "H-SEG-01", "titulo": "…", "area": "secretos", "severidad": "Alta", "certeza": "verificado",
                "objetos": ["DEM_ERP_API_TOKEN"], "documento": "04-seguridad-grupos.md#hallazgos",
                "evidencia": "mcp:constant/DEM_ERP_API_TOKEN#value"}]}
```

Los del registro de `09`, sin los fusionados (`duplicadoDe`), ordenados por ID. `severidad`: Alta, Media o Baja.
`certeza`: verificado, inferido o pendiente. `documento`: dónde se explica. `objetos`: nombres de `inventario.json`.

## `procesos.json`

```json
{"procesos": [{"nombre": "DEM Alta Solicitud", "json": "08-procesos-bpmn/DEM_Alta_Solicitud.json", "nodos": 5,
               "ejecuciones": 120}]}
```

Un elemento por process model. `json`: el diagrama en el formato de la skill de diagramas, `null` si no se dibujó con
ella. `nodos`: nodos de la definición. `ejecuciones`: las que devolvió el entorno, `null` si no las devolvió.
