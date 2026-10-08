# Reglas de seguridad

Cómo se detecta y se registra un secreto escrito en la aplicación, y qué otros riesgos de seguridad se registran. Es la única regla sobre secretos: las plantillas y los agentes la aplican, no la redefinen.

## Principio

Se trabaja en entornos controlados: la extracción, el anexo y los documentos llevan los usuarios, los datos de la aplicación y los secretos tal cual.

Las definiciones extraídas (connected systems, integraciones, constantes, Web APIs) pueden contener contraseñas, tokens o API keys, certificados privados, URLs con credenciales embebidas (`https://user:pass@host`) y cadenas de conexión con contraseña. Un secreto escrito en la aplicación es un hallazgo de seguridad: se registra con el objeto y la propiedad donde está.

## Patrones de detección

`python3 <skill>/scripts/detect_secrets.py <ruta>` aplica estos patrones (orientativos); `bash <skill>/scripts/detect_secrets.sh <ruta>` hace lo mismo. Ejecútalo sobre `<trabajo>/mcp_raw/` justo después de la extracción (fase 3): da el patrón de cada posible secreto y dónde está. Un JSON lo recorre entero, sin el `_meta` de la extracción, y da el fichero y la propiedad (`…/getX.json#response.headers[0].value`); otro fichero, la línea. No cuenta las referencias (`=cons!X`, `ri!`, `pv!`, `rule!`, `local!`), los valores de asteriscos (`***`) ni las claves que describen el secreto sin serlo (`tokenUrl`, `passwordPolicy`). `inventory.json` lo resume por objeto: `secrets` son las coincidencias en sus respuestas y, en una constante, `secret: true` dice que su nombre o su valor parecen un secreto.

| Tipo | Patrón |
|---|---|
| Clave de secreto con valor | Una clave que contiene `password`, `passwd`, `pwd`, `secret`, `api_key`/`apikey`, `token`, `credential`, `private_key` o `authorization` (también `sapPassword`, `authToken`) con un valor escrito, o una cabecera `{name, value}` con ese nombre; en un texto o una expresión, seguida de `:` o `=` y un valor (`password: "x"`, `apiKey: "x"`) |
| Token de API con prefijo conocido | `(sk\|pk\|rk)_(live\|test)_[A-Za-z0-9]{8,}` |
| Cabecera Authorization con valor | `(?i)bearer\s+[A-Za-z0-9._~+/-]{16,}` |
| Credenciales en URL | `https?://usuario:clave@host` |
| String de conexión JDBC | `jdbc:[a-z]+://[^?\s]+\?[^\s]*password=[^&\s]+` |
| AWS access key | `AKIA[0-9A-Z]{16}` |
| Private key PEM | `-----BEGIN (RSA \|EC \|OPENSSH \|DSA )?PRIVATE KEY-----` |
| GitHub PAT | `gh[pousr]_[A-Za-z0-9]{36,}` |
| Slack token | `xox[abps]-[A-Za-z0-9-]{10,}` |
| JWT (sospechoso si está en un literal) | `eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+` |

## Acción ante un secreto

1. **Descarta los falsos positivos** (abajo).
2. **Regístralo como hallazgo de seguridad.** Lo registra `integration-security-analyzer`, propietario del área; si lo ve otro agente, lo cuenta en «Para otras áreas» de su informe.
   - ID `H-SEG-NN`, `"area": "secretos"`, severidad **Alta**.
   - Certeza: ✅ si la definición lo contiene; ❓ si dudas de que sea un secreto real, con la pregunta para el responsable de seguridad.
   - Fila en la sección Hallazgos de `04-seguridad-grupos.md` y una línea debajo de la tabla con su impacto.
   - Entrada en `<trabajo>/hallazgos/integration-security-analyzer.json` con `impacto`.
   - Evidencia: `mcp:<tipo>/<nombre>#<propiedad>`.
3. **Impacto**: el valor de una constante o de un connected system se ve desde el diseño de Appian y en los paquetes de despliegue; un usuario final no lo ve desde el portal aunque tenga Viewer. Descríbelo así: «visible para quien tenga acceso de diseño a la aplicación y en cualquier exportación del paquete». Qué hacer con el secreto no se escribe (`execution-principles.md`, principio 10).
4. El registro de `09-valor-adicional.md` lo genera `scripts/build_registry.py` a partir del JSON. Nadie añade el secreto a mano en 09.

## Falsos positivos comunes

Antes de registrar un secreto, descarta:

- Placeholders: `${SECRET_NAME}`, `<<PUT_TOKEN_HERE>>`, `<your-token>`.
- Textos de ayuda, descripciones o etiquetas que solo nombran la palabra («Introduzca su password»).
- Constantes o campos con nombre de secreto pero sin valor.

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

**Grupo de alcance amplio**: un grupo de sistema (p. ej. Application Users) o uno que agrupa a todos los usuarios de la aplicación. Appian no trae un grupo «All Users», «Everyone» ni «Public»: el nombre no prueba el alcance; decide por sus subgrupos y miembros (✅) o por nombre y descripción (🔵). Fuente: https://docs.appian.com/suite/help/26.6/System_Groups.html

## Política para Markdown

Los entregables son Markdown plano que se abre en visores variados (GitHub, VS Code, herramientas internas):

- **Sin bloques HTML crudos** (`<script>`, `<iframe>`, `<style>`).
- **Diagramas Mermaid** saneados con `python3 <skill>/scripts/validate_mermaid.py` antes de escribirse (`mermaid-rules.md`).
