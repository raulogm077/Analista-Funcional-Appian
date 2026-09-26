# Trazabilidad del prototipo · Acuerdos con Terceras Partes

Fuente: examples/atp/ddf.md v1.1 (modo fiel de la ERS de ejemplo, FU-01) · datos ficticios

## Requisitos → pantallas

| Requisito | Descripción | Pantallas |
|---|---|---|
| RF-01 | Indicadores en la página de inicio | Inicio |
| RF-02 | Tareas pendientes del usuario | Inicio |
| RF-03 | Listado con búsqueda, filtros y exportación | Acuerdos |
| RF-04 | Acceso a la ficha desde el listado | Acuerdos, Ficha de ATP Acuerdo |
| RF-05 | Alta en varios pasos con resumen | Nuevo acuerdo |
| RF-06 | Importe solo con contenido económico | Nuevo acuerdo |
| RF-07 | Envío a revisión jurídica | Nuevo acuerdo |
| RF-08 | Ficha: ciclo de vida, datos, documentos e historial | Ficha de ATP Acuerdo |
| RF-09 | Editar datos y añadir documentos | Ficha de ATP Acuerdo, Editar datos generales, Añadir documento |
| RF-10 | Resolver la revisión jurídica | Revisar acuerdo |
| RF-11 | Aviso de vencimiento a 90 días | Inicio, Acuerdos, Ficha de ATP Acuerdo |
| RF-12 | Informe de acuerdos | Informes |

## Inventario de pantallas

| Id | Pantalla | Tipo | Patrón | Requisitos | Referencia en el documento |
|---|---|---|---|---|---|
| inicio | Inicio | page | P06 | RF-01, RF-02, RF-11 | PAN-01 · Inicio |
| acuerdos | Acuerdos | page | P01 | RF-03, RF-04, RF-11 | PAN-02 · Listado de acuerdos |
| acuerdo | Ficha de ATP Acuerdo | record | P02 | RF-04, RF-08, RF-09, RF-11 | PAN-03 · Ficha del acuerdo |
| alta | Nuevo acuerdo | form | P04 | RF-05, RF-06, RF-07 | PAN-04 · Alta de acuerdo |
| revision | Revisar acuerdo | form | P05 | RF-10 | PAN-05 · Revisión jurídica |
| editar | Editar datos generales | dialog | P07 | RF-09 | PAN-06 · Editar datos generales |
| documento | Añadir documento | dialog | P07 | RF-09 | PAN-07 · Añadir documento |
| informes | Informes | page | P08 | RF-12 | PAN-08 · Informe de acuerdos |

## Preguntas abiertas para el cliente

- 🔴 **P-001** ¿Quién pasa el acuerdo a «Pendiente de firma», «Vigente» y «Vencido»? ¿La firma se registra en la aplicación (fecha, firmantes) o solo se adjunta el PDF firmado? _(pantalla: acuerdo)_
- 🔴 **P-007** ¿«Devolver para cambios» genera una tarea al gestor o el acuerdo vuelve a Borrador sin tarea? _(pantalla: revision)_
- 🟡 **P-006** ¿Quién puede editar un acuerdo en estado «Vigente»? La ERS solo habla del gestor en el alta. _(pantalla: editar)_

## Supuestos a validar

- El código ATP-AAAA-NNNN lo genera el proceso al enviar; no se muestra en el alta. _(pantalla: Nuevo acuerdo)_
- La ERS no indica si el CIF se valida contra un servicio externo (AEAT). Se asume validación solo de formato. _(pantalla: Nuevo acuerdo)_
- El escalado por plazo no está en la ERS; se muestra solo el vencimiento de la tarea. _(pantalla: Revisar acuerdo)_
