<!-- anexo generado por build_annex.py -->
# DEM_SolicitudForm

> Interfaz. Definición tal como la devolvió el entorno (solo lectura), 2026-10-09.

## Expresiones

### Bloque 1: `expression`

```text
1  =a!formLayout(titleBar: "Nueva solicitud", contents: {
2    a!textField(label: "Título", required: true, value: ri!record['recordType!DEM Solicitud.fields.titulo']),
3    a!floatingPointField(label: "Importe"),
4    a!dropdownField(label: "Estado", choiceLabels: cons!DEM_ESTADOS_VALIDOS, choiceValues: cons!DEM_ESTADOS_VALIDOS),
5    a!dropdownField(label: "Categoría", choiceLabels: rule!DEM_INT_ConsultarCatalogo().result.body)
6  },
7  buttons: a!buttonLayout(primaryButtons: a!buttonWidget(label: "Enviar", submit: true),
8    secondaryButtons: a!buttonWidget(label: "Cancelar", value: true, saveInto: ri!cancel, submit: true)))
```

## Definición completa

```json
{
  "uuid": "_a-0000e017-dem0-8000-9bb2-011c48011c48_00017 ‹DEM_SolicitudForm›",
  "name": "DEM_SolicitudForm",
  "inputs": [
    {
      "name": "record",
      "type": "recordType!DEM Solicitud"
    },
    {
      "name": "cancel",
      "type": "Boolean"
    }
  ],
  "expression": "‹ver bloque 1›"
}
```

## Quién lo usa (@dependents): `getObjectDependents`

```json
{
  "dependents": [
    {
      "uuid": "_a-0000e028-dem0-8000-9bb2-011c48011c48_00028 ‹DEM Alta Solicitud›",
      "type": "PROCESS_MODEL",
      "name": "DEM Alta Solicitud",
      "breadcrumb": "Start Form"
    }
  ]
}
```

## Validación de la plataforma (@validation): `validateDesignObject`

```json
{
  "valid": true,
  "issues": []
}
```

## Versiones (@versions): `getObjectVersionHistory`

```json
{
  "versions": [
    {
      "versionId": 3,
      "modifiedBy": "marta.ruiz",
      "modifiedOn": "2026-09-01T10:00:00Z"
    },
    {
      "versionId": 2,
      "modifiedBy": "pablo.soto",
      "modifiedOn": "2026-06-15T12:30:00Z"
    },
    {
      "versionId": 1,
      "modifiedBy": "admin.dem",
      "modifiedOn": "2026-03-02T08:00:00Z",
      "comment": "Creación de DEM_SolicitudForm"
    }
  ]
}
```

## Render de la interfaz (@screen): `testInterface`

```json
{
  "componentTree": {
    "type": "FormLayout",
    "titleBar": "Nueva solicitud",
    "contents": [
      {
        "type": "TextField",
        "label": "Título",
        "required": true
      },
      {
        "type": "FloatingPointField",
        "label": "Importe"
      },
      {
        "type": "DropdownField",
        "label": "Estado"
      },
      {
        "type": "DropdownField",
        "label": "Categoría"
      }
    ],
    "buttons": [
      "Enviar",
      "Cancelar"
    ]
  },
  "diagnostics": {
    "error": []
  }
}
```
