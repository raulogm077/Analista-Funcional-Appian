# ERS de ejemplo · Gestión de Acuerdos con Terceras Partes (ATP)

> Documento de ejemplo para probar la skill. No es la ERS oficial de OP_ATP: los requisitos, campos y datos son ficticios.

## 1. Objeto
Aplicación para registrar, revisar y hacer seguimiento de los acuerdos que AENA suscribe con terceras partes (empresas, administraciones públicas y otras entidades): convenios, contratos de colaboración, acuerdos de confidencialidad y protocolos generales de actuación.

## 2. Actores
- **Gestor de acuerdos** (unidad promotora): da de alta acuerdos, adjunta documentación y solicita la revisión.
- **Revisor jurídico** (Asesoría Jurídica): aprueba, rechaza o devuelve el acuerdo con comentarios.
- **Consulta**: cualquier usuario de AENA con acceso puede consultar acuerdos vigentes.

## 3. Entidad Acuerdo
| Campo | Tipo | Obligatorio | Observaciones |
|---|---|---|---|
| Código | Texto | Sí (automático) | Formato ATP-AAAA-NNNN |
| Título | Texto (200) | Sí | |
| Tipo de acuerdo | Lista | Sí | Convenio, Contrato de colaboración, Acuerdo de confidencialidad, Protocolo general de actuación |
| Tercero | Texto | Sí | Razón social |
| CIF/NIF del tercero | Texto | Sí | |
| Tipo de tercero | Lista | Sí | Empresa privada, Administración pública, Universidad o centro de investigación, Otro |
| Aeropuerto / unidad | Lista | Sí | Código IATA o Servicios Centrales |
| Responsable AENA | Usuario | Sí | |
| Fecha de inicio | Fecha | Sí | |
| Fecha de fin | Fecha | Sí | Posterior a la fecha de inicio |
| Prórroga automática | Sí/No | No | |
| Importe (€) | Decimal | Solo si el acuerdo tiene contenido económico | |
| Contraprestación | Texto largo | No | |
| Estado | Lista | Automático | Borrador, En revisión jurídica, Pendiente de firma, Vigente, Vencido, Rechazado |

## 4. Requisitos funcionales
- **RF-01** El sistema mostrará una página de inicio con indicadores: acuerdos vigentes, pendientes de revisión, acuerdos que vencen en los próximos 90 días e importe comprometido.
- **RF-02** La página de inicio mostrará las tareas pendientes del usuario conectado.
- **RF-03** El usuario podrá consultar el listado de acuerdos, buscar por texto y filtrar por estado, tipo y aeropuerto, y exportarlo a Excel.
- **RF-04** Desde el listado se accederá a la ficha del acuerdo.
- **RF-05** El gestor podrá dar de alta un acuerdo en varios pasos: datos generales, tercero, condiciones económicas y documentación, con un resumen final antes de enviarlo.
- **RF-06** El importe solo se pedirá si el acuerdo tiene contenido económico.
- **RF-07** Al enviar el alta, el acuerdo pasará a *En revisión jurídica* y se generará una tarea para Asesoría Jurídica.
- **RF-08** La ficha del acuerdo mostrará el ciclo de vida, los datos generales, el tercero, las condiciones económicas, los documentos y el historial de cambios.
- **RF-09** Desde la ficha, el gestor podrá editar los datos generales y añadir documentos.
- **RF-10** El revisor jurídico resolverá la tarea de revisión: aprobar, devolver para cambios o rechazar. Los comentarios serán obligatorios si no se aprueba.
- **RF-11** El sistema avisará en la ficha cuando un acuerdo vigente venza en menos de 90 días.
- **RF-12** Habrá un informe con acuerdos por tipo, por estado, altas por mes e importe por aeropuerto.

## 5. Reglas de negocio
- **RN-01** La fecha de fin debe ser posterior a la fecha de inicio.
- **RN-02** Los documentos admitidos son PDF y DOCX, con un máximo de 10 MB por fichero.
