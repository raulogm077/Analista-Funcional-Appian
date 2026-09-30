# Metadatos y recuentos del data fabric (Appian MCP Server)

El **Appian MCP Server** es distinto del Dev MCP: lo activa un administrador en el Admin Console (Appian 26.6+, tiers *advanced* y *premium*) y se conecta a `<URL del entorno>/mcp` con la API key de una cuenta de servicio con rol Designer. Es **opcional**.

La skill lo usa para dos cosas, y solo para ellas:

1. **Metadatos** de los record types sincronizados: referencia SQL, campos y relaciones.
2. **Recuento de filas** de cada record type de la app: `SELECT COUNT(*) AS total FROM <referencia SQL>`.

**Nunca** se leen filas de datos de negocio.

## Cómo se obtiene

**Opción 1: script (preferente).** Si la configuración MCP del proyecto tiene un servidor HTTP cuya URL termina en `/mcp`:

```bash
uv run --with "mcp>=1.2,<2" python scripts/devmcp_extract.py datafabric --out <salida>
```

Escribe `_intermedio/datafabric.json`. La consulta SQL solo se construye si la referencia SQL es un identificador válido (`[A-Za-z_][A-Za-z0-9_]*`).

**Opción 2: en la sesión.** Úsala si el servidor está conectado al cliente pero no en ficheros de configuración.

1. Localiza por su descripción la herramienta de metadatos del data fabric (hoy `appian_data_fabric_metadata`) y llámala sin parámetros.
2. Localiza la herramienta de consulta SQL (hoy `appian_data_fabric_sql_query`) y ejecuta **solo** `SELECT COUNT(*) AS total FROM <referencia>` para cada record type de la app.
3. Escribe el resultado en `_intermedio/datafabric.json` con esta forma:

```json
{"generatedAt": "…", "server": {"source": "sesión"},
 "recordTypes": [{"name": "…", "uuid": "…", "sqlReference": "…", "fieldCount": 0, "relationshipCount": 0, "count": 0}],
 "unmatchedRecordTypes": ["…"]}
```

**Opción 3: no disponible.** No hay `datafabric.json`. Los documentos lo indican en una línea («volúmenes no disponibles: Appian MCP Server no configurado») y los requisitos de volumen de `12` pasan a «Preguntas abiertas».

## Limitaciones (documentación oficial)

- No se pueden consultar record types no sincronizados, *legacy* ni con seguridad a nivel de registro basada en una expresión. Aparecen en `unmatchedRecordTypes` y el hallazgo DAT-04 de `modernization-guide.md` puede aplicar.
- Los resultados se filtran por la seguridad de la cuenta de servicio: si un recuento parece bajo, puede ser por permisos. Indícalo como supuesto.

Fuente: [MCP System Tools Reference](https://docs.appian.com/suite/help/26.6/mcp-system-tools.html) · [Appian MCP Server Security](https://docs.appian.com/suite/help/26.6/mcp-server-security.html)
