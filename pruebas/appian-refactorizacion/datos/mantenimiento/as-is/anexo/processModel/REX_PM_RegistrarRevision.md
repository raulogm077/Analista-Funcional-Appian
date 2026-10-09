<!-- anexo generado por build_annex.py -->
# REX_PM_RegistrarRevision (Modelo de proceso)

## Nodos

| id | Tipo | Nombre | Siguientes |
|---|---|---|---|
| 1 | Inicio | Inicio | 2 |
| 2 | Tarea de usuario | Rellenar revisión | 3 |
| 3 | Script | Preparar revisión | 4 |
| 4 | Write to Data Store Entity | Guardar revisión | 5 |
| 5 | Write to Data Store Entity | Guardar historial | 6 |
| 6 | Subproceso | Avisar (rule!AVI_EnviarAviso) | 7 |
| 7 | Fin | Fin | — |
