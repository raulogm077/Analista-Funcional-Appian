<!-- anexo generado por build_annex.py -->
# REX_IF_ListaRevisiones (Interfaz)

## Expresiones

### Bloque 1: `definition`

```text
 1  a!localVariables(
 2    local!revisiones: a!queryEntity(
 3      entity: cons!REX_ENTIDAD_REVISION,
 4      query: a!query(pagingInfo: a!pagingInfo(startIndex: 1, batchSize: 50))
 5    ).data,
 6    a!gridField(data: local!revisiones, columns: {a!gridColumn(label: "Fecha", value: fv!row.fecha)})
 7  )
```
