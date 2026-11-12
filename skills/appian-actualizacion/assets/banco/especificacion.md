# Banco de pruebas de SAIL CLI: la aplicación ficticia

Una aplicación pequeña y ficticia para comprobar, en el entorno de desarrollo de quien use el plugin, que cada versión
de `sail` sigue funcionando con `qa.py` y que el extractor de ingeniería inversa sigue viendo todos sus objetos con cada
versión del Dev MCP (`esperado.json` dice cuántos de cada tipo, como mínimo; si esta especificación gana o pierde un
objeto, se cambia a la vez). No es un proyecto ni un ejemplo de cómo hacer una aplicación: es el banco de pruebas de la
herramienta. Nombres y datos inventados; nada de un cliente.

Se construye una vez por entorno, con el Dev MCP y siguiendo `appian-best-practices`, en este orden (el de la skill
oficial). Si el prefijo `BPS` ya está usado en el entorno, se elige otro y se cambia en todos los nombres.

## Qué cubre

Una pantalla o acción por cada tipo de lo que documenta `sail` (un tipo nuevo es una fila más):

| Pantalla o acción | Lo que ejercita |
|---|---|
| Página «Solicitudes»: tabla de registros con filtros | `pages`, `load`, filtro de índice («Estado»), filtro de rango de fechas («Fecha de inicio»), búsqueda y orden de la tabla |
| «Nueva solicitud» (acción de la lista, con formulario de inicio) | Texto, decimal, entero, desplegable, casillas, fecha, fecha y hora, selector de usuario, fichero, una validación que bloquea el envío, `back` |
| Vista del registro | `navigate` a un registro, `reload` tras enviar y leer lo escrito |
| «Enviar a aprobación» (acción del registro, sin formulario de inicio) | Encadena a la tarea «Confirmar envío» de quien la lanza; su botón pide confirmación (`interact --confirm`) |
| Tarea «Aprobar solicitud», asignada al grupo de aprobadores | `tasks`, `open --accept` y completarla con la otra cuenta |
| «Nueva solicitud» solo para solicitantes | Que el aprobador no la ve (un permiso que se niega) |

## Objetos

1. **Aplicación** `BPS Banco de pruebas SAIL`, prefijo `BPS`.
2. **Grupos**: `BPS Solicitantes` y `BPS Aprobadores`, los dos miembros de `BPS Users`.
3. **Constantes**: `BPS_GRUPO_SOLICITANTES` y `BPS_GRUPO_APROBADORES` (grupo); `BPS_ESTADO_BORRADOR` (1),
   `BPS_ESTADO_PENDIENTE` (2), `BPS_ESTADO_APROBADA` (3) y `BPS_ESTADO_RECHAZADA` (4); `BPS_CARPETA_ADJUNTOS` (carpeta
   de documentos donde se suben los ficheros).
4. **Tipos de registro** (base de datos del entorno, la de los demás tipos de registro):
   - `BPS Estado` y `BPS Categoria`, de referencia: `id`, `nombre`, `orden`, `isActive`. Valores de `BPS Estado`:
     Borrador, Pendiente de aprobación, Aprobada, Rechazada (ids 1 a 4). De `BPS Categoria`: Material, Formación, Viaje.
   - `BPS Solicitud`: `id`, `titulo` (texto, 100), `importe` (decimal), `unidades` (entero), `opciones` (texto: las
     casillas marcadas), `fechaInicio` (fecha), `citaPrevia` (fecha y hora), `adjunto` (documento), `comentario`
     (texto, 255), `categoriaId`, `estadoId`, `responsable` (usuario), `aprobadoPor` (usuario), `createdBy` (usuario),
     `createdOn` (fecha y hora). Relaciones con `BPS Categoria`, `BPS Estado` y la de usuarios de cada campo de usuario.
   - Filtros de usuario de `BPS Solicitud`: «Estado» (lista de valores del estado) y «Fecha de inicio» (rango).
5. **Reglas de expresión**, cada una con sus casos de prueba guardados (con salida esperada: el valor que vale, el
   que no y el vacío):
   - `BPS_ImporteEsValido(importe)`: el importe está informado y es mayor que cero. La usa la validación del
     formulario.
   - `BPS_MotivoEsObligatorio(decision)`: la decisión es rechazar. La usa el motivo de la tarea de aprobación.
6. **Interfaces**: `BPS_ResumenSolicitud` (vista del registro), `BPS_FormularioSolicitud` (formulario de inicio de la
   nueva solicitud), `BPS_ConfirmarEnvio` (tarea encadenada: un comentario obligatorio, que el proceso exige, y un botón «Enviar a
   aprobación» que lleva confirmación),
   `BPS_AprobarSolicitud` (tarea del grupo: «Decisión» Aprobar o Rechazar y un comentario) y `BPS_PaginaSolicitudes`
   (la tabla de la página, con los filtros, la búsqueda y la acción «Nueva solicitud»).
7. **Procesos**:
   - `BPS Crear Solicitud`: formulario de inicio; si no se cancela, guarda la solicitud en Borrador con quién y cuándo.
   - `BPS Enviar a Aprobacion`: sin formulario de inicio. Tarea «Confirmar envío» a quien lo lanza, encadenada desde el
     inicio; guarda Pendiente de aprobación; tarea «Aprobar solicitud» al grupo `BPS Aprobadores`; guarda la decisión y
     quién la tomó.
8. **Acciones de `BPS Solicitud`**: «Nueva solicitud» (de la lista, solo `BPS Solicitantes`) y «Enviar a aprobación»
   (del registro, solo en Borrador).
9. **Site** `BPS Banco de pruebas` (`bps-banco-pruebas`) con la página «Solicitudes».
10. **Seguridad**: `BPS Users` ve los tipos de registro, el site y los procesos; solo `BPS Solicitantes` inicia los dos
   procesos y escribe en la carpeta `BPS Adjuntos` (la subida del fichero). La tarea de aprobación llega por asignación.

## Cuentas

Dos cuentas locales de prueba, que crea la persona en la consola de administración (sus contraseñas no pasan por la
IA ni por ningún fichero):
- una solicitante, en `BPS Solicitantes`;
- una aprobadora, en `BPS Aprobadores`.

Sin contraseña temporal: una cuenta a la que Appian obliga a cambiar la contraseña al entrar no puede abrir sesión
con `sail` (`verifying login: … setpassword`) hasta que se cambia en el navegador. Y con un nombre y apellidos que
no tenga ninguna otra cuenta del entorno: el selector de usuario del formulario las enseña por ese nombre, y dos
iguales no se distinguen.

Con cada una entra en `sail` desde su terminal, en la carpeta de sesión común de esa cuenta, `~/.sail/<entorno>/<usuario>`
(`sail login <host> --data-dir ~/.sail/<entorno>/<usuario>`, con `SAIL_USERNAME` y `SAIL_PASSWORD` solo para esa orden).
Es donde `qa.py` busca la sesión de cada cuenta; el banco no tiene carpetas propias.

## Guiones

En `guiones/`, uno o más por fila de «Qué cubre» (falta el de la tarea del grupo). Están escritos tras recorrer la
aplicación con `sail`, como cualquier guion de `appian-qa`, y crean sus propias solicitudes con un título único.
Van sin entorno ni cuentas: `comprobar` pone los de quien lo lanza y, donde un paso teclea el usuario de un rol
(`{cuenta de aprobador}`, en el selector de usuario), el suyo. Si se cambia una etiqueta o un mensaje de la
aplicación, se cambia en su guion.
