# Metadatos y recuentos del data fabric (Appian MCP Server)

El **Appian MCP Server** es distinto del Dev MCP: lo activa un administrador en el Admin Console (Appian 26.6+, solo Appian Cloud, tiers *advanced* y *premium*) y se conecta a `<URL del entorno>/mcp` con la API key de una cuenta de servicio con rol Designer. Es **opcional**.

La skill lo usa para dos cosas, y solo para ellas:

1. **Metadatos** de los record types sincronizados: referencia SQL, campos y relaciones.
2. **Recuento de filas** de cada record type de la app: `SELECT COUNT(*) AS total FROM <referencia SQL>`.

**Nunca** se leen filas de datos de negocio.

## Cómo se obtiene

**Opción 1: script (preferente).** Si la configuración MCP del proyecto tiene un servidor HTTP en `<URL del entorno>/mcp`, con el mismo host que el `LCP_URL` del Dev MCP (que la URL termine en `/mcp` no basta: muchos conectores ajenos a Appian también terminan así):

```bash
uv run --with "mcp>=1.2,<2" python scripts/devmcp_extract.py datafabric --out <salida>
```

Si el servidor tiene otra URL, nómbralo: `--mcp-server-name <nombre en la configuración>`. Escribe `<trabajo>/datafabric.json`. La consulta SQL solo se construye si la referencia SQL es un identificador válido (`[A-Za-z_][A-Za-z0-9_]*`).

**Opción 2: en la sesión.** Úsala si el servidor está conectado al cliente pero no en ficheros de configuración.

1. Usa solo un servidor de Appian del mismo entorno (su nombre o URL lo identifican; ante la duda, pregunta). Localiza por su descripción la herramienta de metadatos del data fabric (hoy `appian_data_fabric_metadata`) y llámala sin parámetros.
2. Localiza la herramienta de consulta SQL (hoy `appian_data_fabric_sql_query`) y ejecuta **solo** `SELECT COUNT(*) AS total FROM <referencia>` para cada record type de la app.
3. Escribe el resultado en `<trabajo>/datafabric.json` con esta forma:

```json
{"generatedAt": "…", "server": {"source": "sesión"},
 "recordTypes": [{"name": "…", "uuid": "…", "sqlReference": "…", "fieldCount": 0, "relationshipCount": 0, "count": 0}],
 "unmatchedRecordTypes": ["…"]}
```

**Opción 3: no disponible.** No hay `datafabric.json`. Los documentos afectados lo dicen en una línea de su «Cobertura y límites» («volúmenes no disponibles: Appian MCP Server no configurado») y los requisitos de volumen de `12` pasan a «Preguntas abiertas». La falta de volúmenes no es un hallazgo.

## Cómo se usan los recuentos

- Un record type sin `count` (en `unmatchedRecordTypes` o porque falló la consulta) tiene volumen ❓, nunca 0.
- Un recuento obtenido es ✅, con la salvedad de seguridad que se explica abajo.

## Limitaciones (documentación oficial)

- No se pueden consultar record types no sincronizados, *legacy* ni con seguridad a nivel de registro basada en una expresión. Aparecen en `unmatchedRecordTypes`; la seguridad por expresión es un patrón de `modernization-guide.md` que `13` recoge como `MOD-` con su fuente oficial (los documentos no citan el código interno del patrón).
- Los resultados se filtran por la seguridad de la cuenta de servicio: si un recuento parece bajo, puede ser por permisos. Márcalo 🔵 y dilo.

Fuente: [MCP System Tools Reference](https://docs.appian.com/suite/help/26.6/mcp-system-tools.html#data-fabric-tools) · [Appian MCP Server – limitaciones](https://docs.appian.com/suite/help/26.6/appian-mcp-server.html#limitations) · [Appian MCP Server Security](https://docs.appian.com/suite/help/26.6/mcp-server-security.html)
