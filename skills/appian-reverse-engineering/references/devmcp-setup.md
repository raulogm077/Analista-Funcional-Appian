# Instalar y conectar los MCP de Appian

Guía para quien use la skill por primera vez. La fase 0 de la skill (`devmcp_extract.py doctor`) indica qué paso falta; vuelve aquí a ese paso.

| MCP | ¿Obligatorio? | Para qué lo usa la skill |
|---|---|---|
| Appian Dev MCP | **Sí** | Leer la aplicación: definiciones, dependencias, historial, pantallas. |
| Appian MCP Server | No | Metadatos y recuento de filas del data fabric. |
| Appian Docs MCP | No | Resolver con la documentación oficial las dudas de Appian: qué hace un nodo, una función o un componente. |

Fuente de esta guía: [Appian Developer MCP Servers](https://docs.appian.com/suite/help/latest/devmcp.html), [ficha de AppMarket](https://appmarket.appian.com/listings/appian-dev-mcp) y [Connect your AI application to Appian MCP Server](https://docs.appian.com/suite/help/26.6/connect-ai-application-to-mcp.html).

---

## 1. Appian Dev MCP (obligatorio)

### Requisitos

- Entorno Appian **26.5 o superior**, con el plugin *Appian Dev MCP* instalado desde AppMarket por un administrador.
- Usuario con rol **Designer** (o administrador). La skill ve lo mismo que ese usuario.
- En tu equipo: **Python 3.13+** y **uv**.
  - Mac/Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
  - Windows (PowerShell): `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
- El Dev MCP tiene **soporte de comunidad**: Appian Support no atiende incidencias sobre él.
- Los scripts de la skill son Python (`detect_secrets.sh` es un atajo opcional en bash de `detect_secrets.py`). En Windows, si `python3` no existe, usa `python`.
- Para las imágenes de los diagramas, Playwright y un navegador (los usa la skill de diagramas del plugin). Sin ellos, la documentación sale sin imágenes: los procesos llevan su `.drawio` y su `.bpmn`, y los demás diagramas, el bloque mermaid.

### Instalación

1. Descarga el bundle del servidor desde tu entorno: `https://<tu-entorno>/suite/plugins/servlet/stateless/downloads`.
2. Descomprímelo e instala dependencias.

   Mac/Linux:
   ```bash
   mkdir -p ~/appian-dev-mcp-server
   tar -xzf ~/Downloads/appian-dev-mcp-server-bundle.tar.gz -C ~/appian-dev-mcp-server
   cd ~/appian-dev-mcp-server
   uv sync
   uv run playwright install chromium
   ```

   Windows (PowerShell):
   ```powershell
   mkdir $HOME\appian-dev-mcp-server
   tar -xzf $HOME\Downloads\appian-dev-mcp-server-bundle.tar.gz -C $HOME\appian-dev-mcp-server
   cd $HOME\appian-dev-mcp-server
   uv sync
   uv run playwright install chromium
   ```

   Chromium solo hace falta para la autenticación por navegador (SSO).

3. Configura el cliente. En Claude Code, en el fichero `.mcp.json` de la carpeta donde vayas a trabajar:

   ```json
   {
     "mcpServers": {
       "appian": {
         "command": "uv",
         "args": ["run", "--directory", "/RUTA/ABSOLUTA/appian-dev-mcp-server", "python", "-m", "lcp_mcp_server"],
         "env": {
           "LCP_URL": "https://tu-entorno.appiancloud.com"
         }
       }
     }
   }
   ```

   - En Windows la ruta va con barras dobles o normales: `"C:/Users/<usuario>/appian-dev-mcp-server"`.
   - `LCP_URL` es solo el host, sin barra final.
   - Con qué cuenta entra en cada entorno (en desarrollo, una que construye; en los demás, una que solo lee), en
     «Solo se escribe en desarrollo», más abajo. La skill nunca escribe: lo garantiza su política, en cualquier entorno.
   - Autenticación básica en lugar de SSO: añade `"LCP_AUTH_METHOD": "basic"`, `"USERNAME"` y `"PASSWORD"`. Mejor como variables de entorno (`"PASSWORD": "${APPIAN_PASSWORD}"`) que escritas en el fichero.
   - Con proxy corporativo: `HTTPS_PROXY`, `HTTP_PROXY` y `SSL_CERT_FILE`.
   - Otros clientes: Claude Desktop (`claude_desktop_config.json`), Cursor (`~/.cursor/mcp.json`), Kiro (`.kiro/settings/mcp.json`). La skill busca en todos ellos.

4. Primera conexión: con SSO se abrirá el navegador para iniciar sesión. La sesión se guarda y se reabre cuando caduca.

### Comprobación

Desde la carpeta donde está tu `.mcp.json`, con la ruta absoluta de la skill (`<skill>`):

```bash
uv run --no-project --python ">=3.10" --with "mcp>=1.2,<2" python "<skill>/scripts/devmcp_extract.py" doctor
```

Debe mostrar `Dev MCP ... ok` y el número de aplicaciones visibles.

| Mensaje de `doctor` | Qué hacer |
|---|---|
| `no_configurado` | Falta el paso 3, o el fichero está en otra carpeta. Usa `--config <fichero>` o `--bundle-dir` y `--url`. |
| `ambiguo` | Hay varias configuraciones (p. ej. varios usuarios). Elige con `--server-name`. |
| `No arranca o no autentica` | Revisa la ruta del bundle, `uv sync`, la URL y el inicio de sesión. Prueba el servidor desde tu cliente. |
| `sin_apps` | El usuario no ve ninguna aplicación: revisa permisos en Appian. |
| Aviso de herramientas de escritura | Es lo normal: el Dev MCP ofrece herramientas que escriben (también con `LCP_TOOL_MODE=readonly`). La skill pasa a modo estricto y solo usa las de lectura evidentes. |

### Solo se escribe en desarrollo

La IA escribe en Appian solo en el entorno de desarrollo y, en una urgencia, en el entorno de corrección. A pruebas y a
producción llega un paquete cuyos objetos ha revisado una persona. Cómo se cumple:

| Entorno | Dev MCP | SAIL CLI |
|---|---|---|
| Desarrollo | Con la cuenta de quien construye (Designer) | Sí: crea datos y lanza procesos |
| Entorno de corrección | En una urgencia, como en desarrollo; si no, como en producción | Solo en una urgencia |
| Pruebas, preproducción y producción | Con una cuenta Designer, solo para leer (documentar, comparar) | No |

- **La cuenta**: el Dev MCP solo admite cuentas Designer (una que no lo es recibe un 403 en toda llamada; comprobado
  con el Dev MCP 26.6.110) y hace cada operación con sus permisos. Fuera de desarrollo se entra con una cuenta
  Designer para leer; que la IA no escriba allí lo garantiza el método: solo se construye en desarrollo y, en una
  urgencia, en el entorno de corrección.
- **`LCP_TOOL_MODE=readonly` no protege.** La documentación de Appian la describe («restricts to read-only tools»),
  pero el Dev MCP 26.6.110 no la aplica: ofrece las mismas 200 herramientas con ella y sin ella. Si un Dev MCP futuro
  la aplica, añadirla en los entornos que no son de desarrollo no cuesta nada; hoy no cambia lo de arriba.
- **Esta skill** (extracción, `verificar`, `regresion`, `deriva`) es de solo lectura por su política
  (`scripts/devmcp_policy.json`), en cualquier entorno. `verificar` y `regresion` ejecutan casos de prueba que ya
  existen, que no modifican nada: se pasan en desarrollo.

---

## 2. Appian MCP Server (opcional)

Lo activa un **administrador** en el Admin Console → *MCP Server* (Appian 26.6+, tiers *advanced* y *premium*), con una cuenta de servicio con API key y rol Designer.

Configuración en `.mcp.json`, con la clave en una variable de entorno:

```json
{
  "mcpServers": {
    "appian-mcp-server": {
      "type": "http",
      "url": "https://tu-entorno.appiancloud.com/mcp",
      "headers": {"Authorization": "Bearer ${APPIAN_MCP_API_KEY}"}
    }
  }
}
```

La URL es la del mismo entorno que el `LCP_URL` del Dev MCP más `/mcp`: así lo reconoce la skill, y nunca toma por él otro servidor de la configuración. Si usas otra URL (un proxy, por ejemplo), indícalo con `--mcp-server-name appian-mcp-server`.

Sin él, los entregables no incluyen volúmenes de datos.

---

## 3. Appian Docs MCP (opcional)

Viene con el plugin (`appian-docs`, en su `.mcp.json`) y pide iniciar sesión con Google o GitHub la primera vez. Límite: 300 consultas al día y 60 por minuto.

Si no está en la sesión, en Claude Code:

```bash
claude mcp add --transport http appian-docs https://appian-docs-public.mcp.kapa.ai
```

En Claude Desktop: *Settings* → *MCP Servers*, nombre `appian-docs` y la URL anterior.

Sin él, las dudas se consultan en docs.appian.com por la web («Dudas de Appian», en `SKILL.md`). Si tampoco se puede, los entregables no explican con la documentación oficial de Appian los nodos y funciones que no se conocen, y lo que dependa de ella se marca «sin verificar».
