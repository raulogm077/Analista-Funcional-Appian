# Reglas de seguridad

Cómo tratar secretos, credenciales, hosts y usuarios antes de escribir cualquier entregable o la web. Es la única regla sobre estos datos: las plantillas y los agentes la aplican, no la redefinen.

## Principio

Las definiciones extraídas (connected systems, integraciones, constantes, Web APIs) pueden contener contraseñas, tokens o API keys, certificados privados, URLs con credenciales embebidas (`https://user:pass@host`) y cadenas de conexión con contraseña. La extracción ya enmascara lo que reconoce (`***ENMASCARADO***`, `https://***:***@host`), pero algo puede escaparse.

**Nunca** se reproducen en los entregables, ni en claro ni enmascarados: se dice dónde están (objeto y propiedad) y se registran como hallazgo.

## Patrones de detección

`python3 <skill>/scripts/detect_secrets.py <ruta>` aplica estos patrones (orientativos); `bash <skill>/scripts/detect_secrets.sh <ruta>` hace lo mismo. Ejecútalo sobre `<trabajo>/mcp_raw/` justo después de la extracción (fase 3) y sobre toda `<salida>/` al final, `extraccion/` incluida. La extracción ya llega enmascarada y está en el proyecto: lo que encuentre ahí es un secreto que el enmascarado no reconoce, y la carpeta no se comparte hasta quitarlo. Solo imprime fichero y línea, nunca el valor. No cuenta las referencias (`=cons!X`, `ri!`, `pv!`, `rule!`, `local!`), los valores ya enmascarados ni las claves que describen el secreto sin serlo (`tokenUrl`, `passwordPolicy`).

| Tipo | Patrón |
|---|---|
| Clave de secreto con valor | Una clave que contiene `password`, `passwd`, `pwd`, `secret`, `api_key`/`apikey`, `token` o `credential` (también `sapPassword`, `authToken`), seguida de `:` o `=` y un valor |
| Token de API con prefijo conocido | `(sk\|pk\|rk)_(live\|test)_[A-Za-z0-9]{8,}` |
| Cabecera Authorization con valor | `(?i)bearer\s+[A-Za-z0-9._~+/-]{16,}` |
| Credenciales en URL | `https?://usuario:clave@host` |
| String de conexión JDBC | `jdbc:[a-z]+://[^?\s]+\?[^\s]*password=[^&\s]+` |
| AWS access key | `AKIA[0-9A-Z]{16}` |
| Private key PEM | `-----BEGIN (RSA \|EC \|OPENSSH \|DSA )?PRIVATE KEY-----` |
| GitHub PAT | `gh[pousr]_[A-Za-z0-9]{36,}` |
| Slack token | `xox[abps]-[A-Za-z0-9-]{10,}` |
| JWT (sospechoso si está en un literal) | `eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+` |

Una URL ya enmascarada por completo (`https://***:***@host`) no cuenta como coincidencia, pero indica que la definición lleva credenciales embebidas: es un hallazgo y tampoco se escribe así en un entregable (tabla siguiente).

## Cómo se escribe cada dato en los entregables

| Dato | Cómo se escribe |
|---|---|
| Secreto (contraseña, token, clave, certificado) | No se escribe; se dice dónde está («la cabecera `Authorization` usa `CON_SAP_TOKEN`»). En un payload: `***`. |
| URL con credenciales embebidas | La URL sin ellas y «la URL base lleva credenciales embebidas (enmascaradas)». Nunca `***:***@`. |
| Usuario de una credencial (Basic, cuenta de servicio) | No se escribe: es dato sensible. «Usuario y contraseña en el connected system». |
| Host de un servicio externo o público | Se escribe, porque dice a qué sistema llama la integración: `https://api.proveedor.com/v1`. |
| Host interno | Se sustituye por `‹host interno›` y se conserva la ruta: `https://‹host interno›/sap/api`. |
| Cadena de conexión (JDBC) | Tipo de base de datos y host según los criterios anteriores; sin usuario ni contraseña. |
| Usuarios de Appian (miembros, versiones, ejecuciones) | Nunca. Recuentos o rol (`presentation-rules.md`, Regla 8). |
| Constante de tipo Usuario o usuario escrito en el código | «una cuenta de ‹grupo›» si se conoce su grupo (p. ej. «una cuenta de DEM Gestores»); si no, «una cuenta personal». |
| Dirección de correo personal | `‹correo›`. |

**Host interno** es una IP privada (`10.*`, `172.16.*`–`172.31.*`, `192.168.*`, `127.*`), `localhost`, un nombre acabado en `.local`, `.internal`, `.corp` o `.intra`, o un nombre sin dominio (`sapprd01`). Cualquier otro nombre con dominio se muestra.

El valor de una constante o de un connected system se ve desde el diseño de Appian y en los paquetes de despliegue; un usuario final no lo ve desde el portal aunque tenga Viewer. Describe el impacto así: «visible para quien tenga acceso de diseño a la aplicación y en cualquier exportación del paquete».

## Acción ante un secreto

1. **No copies el valor** a ningún documento, informe, terminal ni dato de la web.
2. **Descarta los falsos positivos** (abajo).
3. **Regístralo como hallazgo de seguridad.** Lo registra `integration-security-analyzer`, propietario del área; si lo ve otro agente, lo cuenta en «Para otras áreas» de su informe.
   - ID `H-SEG-NN`, `"area": "secretos"`, severidad **Alta**.
   - Certeza: ✅ si la definición lo contiene (aunque la extracción lo enmascarara); ❓ si dudas de que sea un secreto real, con la pregunta para el responsable de seguridad.
   - Fila en la sección Hallazgos de `04-seguridad-grupos.md` y una línea debajo de la tabla con su impacto y la recomendación.
   - Entrada en `<trabajo>/hallazgos/integration-security-analyzer.json` con `impacto` y `recomendacion`.
   - Evidencia: `mcp:<tipo>/<nombre>#<propiedad>`, sin el valor.
4. **Recomendación habitual**: rotar la credencial y moverla a un campo cifrado del connected system o de la integración (valor introducido directamente, que Appian cifra y no exporta), con su valor por entorno en el fichero de personalización de importación; nunca a una constante ni a una expresión. Fuente: https://docs.appian.com/suite/help/26.6/Integration_Object.html#encrypted-values
5. El registro de `09-valor-adicional.md` lo genera `scripts/build_registry.py` a partir del JSON. Nadie añade el secreto a mano en 09.

## Falsos positivos comunes

Antes de registrar un secreto, descarta:

- Placeholders: `${SECRET_NAME}`, `<<PUT_TOKEN_HERE>>`, `<your-token>`.
- Textos de ayuda, descripciones o etiquetas que solo nombran la palabra («Introduzca su password»).
- Constantes o campos con nombre de secreto pero sin valor.

Un valor enmascarado por la extracción (`***ENMASCARADO***`, `***:***@`) **no** es falso positivo: la definición contiene un secreto. Si dudas, regístralo con certeza ❓ y la pregunta.

## Otros riesgos de seguridad (sin ser secretos)

Detéctalos y regístralos en el documento propietario. Un riesgo que depende de un dato que la extracción no trae (seguridad de acciones de record, destinatarios de correo, role maps) no es ✅: es ❓ «no lo devuelve la extracción», con la pregunta para validarlo (`execution-principles.md`, principio 3).

| Riesgo | Registro |
|---|---|
| Objeto con un grupo de alcance amplio en su role map y datos sensibles | `H-SEG` (04) |
| Grupo de sistema usado para dar permisos a objetos de la aplicación | `H-SEG` (04) |
| Proceso que envía correo con datos sensibles a destinatarios externos | `H-SEG` (04) |
| SQL construido concatenando variables o entrada de usuario sin validar usada en consultas | `H-SEG` (04) |
| Connected system con autenticación None contra una API externa | `H-INT` (05) |
| URL o constante que apunta a otro entorno (p. ej. un host de desarrollo en producción) | `H-INT` (05) |
| Web API que puede llamar un grupo de alcance amplio, o sin validación de entrada visible | `H-API` (06) |

**Grupo de alcance amplio**: un grupo de sistema (p. ej. Application Users) o uno que agrupa a todos los usuarios de la aplicación. Appian no trae un grupo «All Users», «Everyone» ni «Public»: el nombre no prueba el alcance; decide por sus subgrupos y miembros (✅) o por nombre y descripción (🔵). Appian recomienda no usar grupos de sistema para dar seguridad a objetos de una aplicación, sino sus grupos de seguridad por defecto. Fuente: https://docs.appian.com/suite/help/26.6/System_Groups.html

## Política para Markdown

Los entregables son Markdown plano que se abre en visores variados (GitHub, VS Code, herramientas internas):

- **Sin bloques HTML crudos** (`<script>`, `<iframe>`, `<style>`).
- **Sin URLs con credenciales**, ni enmascaradas (tabla de arriba).
- **Sin tokens ni secretos** en bloques de código, ni siquiera de ejemplo: `***`.
- **Diagramas Mermaid** saneados con `python3 <skill>/scripts/validate_mermaid.py` antes de escribirse (`mermaid-rules.md`).

## Comprobación final

Antes de devolver la respuesta:

```bash
python3 <skill>/scripts/detect_secrets.py <salida>
```

Recorre toda la carpeta, incluidos `anexo/`, `dashboard/` y `extraccion/`. Si encuentra algo, **detente**:

- En un documento que escribe un agente (`00`–`11`, `08-procesos-bpmn/`, `LEEME`, `INVENTARIO`): corrígelo con la tabla «Cómo se escribe cada dato».
- En un entregable generado (`anexo/`, `dashboard/`): no lo edites a mano. Corrige la causa (el enmascarado de la extracción o del anexo, o el documento de origen) y vuelve a generarlo.
- En `extraccion/`: el enmascarado no lo reconoce. Díselo al usuario con el fichero y la línea, sin el valor: la carpeta no se comparte hasta quitarlo.
