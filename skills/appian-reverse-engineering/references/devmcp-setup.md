# Instalar y conectar los MCP de Appian

Guía para quien use la skill por primera vez. La fase 0 de la skill (`devmcp_extract.py doctor`) indica qué paso falta; vuelve aquí a ese paso.

| MCP | ¿Obligatorio? | Para qué lo usa la skill |
|---|---|---|
| Appian Dev MCP | **Sí** | Leer la aplicación: definiciones, dependencias, historial, pantallas. |
| Appian MCP Server | No | Metadatos y recuento de filas del data fabric. |
| Appian Docs MCP | No | Explicaciones y verificación de buenas prácticas con la documentación oficial. |

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
           "LCP_URL": "https://tu-entorno.appiancloud.com",
           "LCP_TOOL_MODE": "readonly"
         }
       }
     }
   }
   ```

   - En Windows la ruta va con barras dobles o normales: `"C:/Users/<usuario>/appian-dev-mcp-server"`.
   - `LCP_URL` es solo el host, sin barra final.
   - `LCP_TOOL_MODE: readonly` es recomendable para esta skill. En cualquier caso, **la skill fuerza `readonly`** en su propia conexión.
   - Autenticación básica en lugar de SSO: añade `"LCP_AUTH_METHOD": "basic"`, `"USERNAME"` y `"PASSWORD"`. Mejor como variables de entorno (`"PASSWORD": "${APPIAN_PASSWORD}"`) que escritas en el fichero.
   - Con proxy corporativo: `HTTPS_PROXY`, `HTTP_PROXY` y `SSL_CERT_FILE`.
   - Otros clientes: Claude Desktop (`claude_desktop_config.json`), Cursor (`~/.cursor/mcp.json`), Kiro (`.kiro/settings/mcp.json`). La skill busca en todos ellos.

4. Primera conexión: con SSO se abrirá el navegador para iniciar sesión. La sesión se guarda y se reabre cuando caduca.

### Comprobación

```bash
uv run --with "mcp>=1.2,<2" python <carpeta-de-la-skill>/scripts/devmcp_extract.py doctor
```

Debe mostrar `Dev MCP ... ok` y el número de aplicaciones visibles.

| Mensaje de `doctor` | Qué hacer |
|---|---|
| `no_configurado` | Falta el paso 3, o el fichero está en otra carpeta. Usa `--config <fichero>` o `--bundle-dir` y `--url`. |
| `ambiguo` | Hay varias configuraciones (p. ej. varios usuarios). Elige con `--server-name`. |
| `No arranca o no autentica` | Revisa la ruta del bundle, `uv sync`, la URL y el inicio de sesión. Prueba el servidor desde tu cliente. |
| `sin_apps` | El usuario no ve ninguna aplicación: revisa permisos en Appian. |
| Aviso de herramientas de escritura | El servidor no respeta `readonly`. La skill pasa a modo estricto y solo usa herramientas de lectura evidentes. |

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

Sin él, la documentación no incluye volúmenes de datos.

---

## 3. Appian Docs MCP (opcional)

En Claude Code:

```bash
claude mcp add --transport http appian-public-docs https://appian-docs-public.mcp.kapa.ai
```

En Claude Desktop: *Settings* → *MCP Servers*, nombre `appian-public-docs` y la URL anterior. Pide iniciar sesión con Google o GitHub la primera vez. Límite: 300 consultas al día.

Sin él, las recomendaciones de modernización se basan en las URLs de `references/modernization-guide.md` y se marcan «sin verificar para la versión del entorno».
