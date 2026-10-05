# Trazabilidad del prototipo · Acuerdos con Terceras Partes

Fuente: analisis/funcional.md v1.0 (modo fiel de la ERS de ejemplo, FU-01) · datos ficticios

## Requisitos → pantallas

| Requisito | Descripción | Pantallas |
|---|---|---|
| HU-01 | Ver los indicadores de la cartera | Inicio |
| HU-02 | Ver mis tareas pendientes | Inicio |
| HU-03 | Buscar, filtrar y exportar acuerdos | Acuerdos |
| HU-04 | Abrir la ficha desde la lista | Acuerdos |
| HU-05 | Dar de alta un acuerdo por pasos | Nuevo acuerdo |
| HU-06 | Pedir el importe solo si hay contenido económico | Nuevo acuerdo |
| HU-07 | Enviar el acuerdo a revisión jurídica | Nuevo acuerdo |
| HU-08 | Consultar la ficha del acuerdo | PAN-03 · Ficha del acuerdo |
| HU-09 | Editar los datos generales y añadir documentos | PAN-03 · Ficha del acuerdo, Editar datos generales, Añadir documento |
| HU-10 | Resolver la revisión jurídica | Revisar acuerdo |
| HU-11 | Avisar del vencimiento en la ficha | PAN-03 · Ficha del acuerdo |
| HU-12 | Consultar el informe de acuerdos | Informes |
| ACT-01 | Dar de alta el acuerdo | Nuevo acuerdo |
| ACT-02 | Resolver la revisión jurídica | Revisar acuerdo |
| ACT-03 | Firmar el acuerdo | _Sin pantalla propia: Pantalla por decidir (PC-01)_ |

## Inventario de pantallas

| Id | Pantalla | Tipo | Patrón | Requisitos | Referencia en el documento |
|---|---|---|---|---|---|
| inicio | Inicio | page | P06 | HU-01, HU-02 | PAN-01 · Inicio |
| acuerdos | Acuerdos | page | P01 | HU-03, HU-04 | PAN-02 · Acuerdos |
| acuerdo | PAN-03 · Ficha del acuerdo | record | P02 | HU-08, HU-09, HU-11 | PAN-03 · Ficha del acuerdo |
| alta | Nuevo acuerdo | form | P04 | HU-05, HU-06, HU-07, ACT-01 | PAN-04 · Alta de acuerdo |
| revision | Revisar acuerdo | form | P05 | HU-10, ACT-02 | PAN-05 · Revisión jurídica |
| editar | Editar datos generales | dialog | P07 | HU-09 | PAN-06 · Editar datos generales |
| documento | Añadir documento | dialog | P07 | HU-09 | PAN-07 · Añadir documento |
| informes | Informes | page | P08 | HU-12 | PAN-08 · Informe de acuerdos |

## Preguntas abiertas para el cliente

- **PC-01** ¿Cómo se registra la firma y quién pasa el acuerdo a «Pendiente de firma», «Vigente» y «Vencido»? (Se registran la fecha y los firmantes / Solo se adjunta el acuerdo firmado / La firma queda fuera de la aplicación) _(pantalla: revision)_
- **PC-02** ¿Qué columnas tiene la lista de acuerdos? (Código, título, tercero, tipo, aeropuerto, fecha de fin y estado / Otras) _(pantalla: acuerdos)_
- **PC-03** ¿Consulta ve solo los acuerdos vigentes también en la lista y en la ficha? (Sí, en todas las pantallas / En la lista ve todos) _(pantalla: acuerdos)_
- **PC-04** ¿Qué cambios recoge el historial del acuerdo? (Solo los cambios de estado / También cada cambio de dato) _(pantalla: acuerdo)_
- **PC-05** ¿Quién ve los indicadores de inicio y el informe? (Todos los perfiles / Solo el gestor y el revisor) _(pantalla: inicio)_
- **PC-06** ¿En qué estados puede el gestor editar los datos generales? (Solo antes de enviarlo a revisión / En cualquier estado salvo «Rechazado») _(pantalla: editar)_
- **PC-07** Al devolver para cambios, ¿el gestor recibe una tarea para corregir y reenviar el acuerdo? (Sí, una tarea / No: el acuerdo vuelve a «Borrador» sin tarea) _(pantalla: revision)_
- **PC-08** ¿Cada filtro de la lista admite un valor o más de uno, y en qué orden sale la lista? (Un valor por filtro / Más de uno) _(pantalla: acuerdos)_
- **PC-09** ¿Qué dicen los mensajes de RB-01 y RB-02, el aviso de vencimiento y la tarea de revisión? (Los que propone el prototipo / Otros) _(pantalla: alta)_
- **PC-10** ¿Hay plazo para resolver la revisión jurídica y qué pasa si vence? (Sin plazo / Un plazo en días hábiles con aviso al vencer) _(pantalla: revision)_
- **PC-11** ¿Qué avisos llegan también por correo? (Ninguno / La tarea de revisión / También la decisión al gestor)
- **PC-12** ¿Cuántos acuerdos se registran al año y cuántos años se conservan?
- **PC-13** ¿Quién mantiene las listas de tipos de acuerdo, tipos de tercero y aeropuertos? (Asesoría Jurídica / Un administrador de la aplicación)
- **PC-14** ¿Cuántas personas usan la aplicación, cuántas a la vez y en qué horario?
- **PC-15** ¿Qué se guarda de cada documento además del fichero? (El tipo de documento, quién lo sube y la fecha / Solo el fichero) _(pantalla: documento)_
- **PC-16** ¿El importe comprometido suma solo los acuerdos vigentes o también los pendientes de firma? (Solo vigentes / Vigentes y pendientes de firma) _(pantalla: inicio)_
- **Q-01** ¿Qué versión de Appian tiene el entorno? Va en técnico §0; el prototipo usa 26.9.

## Supuestos a validar

- Versión de Appian sin confirmar: el análisis no tiene especificación técnica (técnico §0). Se prototipa con 26.9. _(pantalla: Aplicación)_
- Pendiente: PC-05. Si Consulta también ve los indicadores. _(pantalla: Inicio)_
- Pendiente: PC-16. Suma los acuerdos vigentes. _(pantalla: Inicio)_
- Propuesta: aviso con acceso a la lista. PAN-01 solo pide el indicador. _(pantalla: Inicio)_
- Propuesta: resumen por estado. PAN-01 no lo pide. _(pantalla: Inicio)_
- Pendiente: PC-02 (columnas) y PC-08 (un valor por filtro; orden por fecha de alta). _(pantalla: Acuerdos)_
- Propuesta: aviso de vencimiento también en la lista. HU-11 lo pide en la ficha. _(pantalla: Acuerdos)_
- Pendiente: PC-09. Texto del aviso. _(pantalla: PAN-03 · Ficha del acuerdo)_
- Pendiente: PC-15. Tipo, quién lo sube y fecha de cada documento. _(pantalla: PAN-03 · Ficha del acuerdo)_
- Pendiente: PC-04. Se muestran los cambios de estado. _(pantalla: PAN-03 · Ficha del acuerdo)_
- El código ATP-AAAA-NNNN lo pone la aplicación al enviar (HU-07.2); no se muestra en el alta. _(pantalla: Nuevo acuerdo)_
- Pendiente: PC-10. Plazo de la revisión y qué pasa si vence. _(pantalla: Revisar acuerdo)_
- Pendiente: PC-01 (qué pasa tras aprobar) y PC-07 (cómo vuelve al gestor al devolver). _(pantalla: Revisar acuerdo)_
- Pendiente: PC-06. En qué estados se pueden editar los datos generales. _(pantalla: Editar datos generales)_
- Pendiente: PC-15. Si se guarda el tipo de cada documento y qué tipos hay. _(pantalla: Añadir documento)_
- Propuesta: filtrar el informe por tipo de acuerdo. PAN-08 no lo pide. _(pantalla: Informes)_
- Propuesta: totales del filtro. PAN-08 no los pide. _(pantalla: Informes)_
