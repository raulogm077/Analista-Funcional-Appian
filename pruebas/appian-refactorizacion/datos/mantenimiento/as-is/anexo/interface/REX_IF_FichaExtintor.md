<!-- anexo generado por build_annex.py -->
# REX_IF_FichaExtintor (Interfaz)

## Expresiones

### Bloque 1: `definition`

```text
 1  a!localVariables(
 2    local!extintor: rv!record,
 3    {
 4      a!sectionLayout(
 5        label: "Extintor " & local!extintor[recordType!REX Extintor.fields.codigo],
 6        contents: {
 7          a!textField(label: "Ubicación", value: local!extintor[recordType!REX Extintor.fields.ubicacion], readOnly: true)
 8        }
 9      ),
10      a!buttonArrayLayout(
11        buttons: a!buttonWidget(
12          label: "Dar de baja",
13          saveInto: a!startProcess(
14            processModel: cons!REX_PM_BAJA_EXTINTOR,
15            processParameters: {extintor: local!extintor}
16          )
17        )
18      )
19    }
20  )
```
