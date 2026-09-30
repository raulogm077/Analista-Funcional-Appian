"""Appian MCP Server simulado (streamable HTTP) para probar el preflight y el data fabric.

Nombres de herramientas tomados de la referencia publica de Appian 26.6 (MCP System Tools Reference).
Uso: python appian_mcp_server_mock.py <puerto>
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

sys.path.insert(0, str(Path(__file__).parent))
import fixture  # noqa: E402

OBJ, _KEYS, _NAMES = fixture.build()
COUNTS = {"DEM_SOLICITUD": 152, "DEM_ESTADO": 4}

port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
mcp = FastMCP("appian-mcp-server-mock", host="127.0.0.1", port=port)


@mcp.tool()
def appian_data_fabric_metadata(recordType: str = "") -> str:
    """Retrieve metadata about available record types, including field names, field types, and relationships."""
    rts = []
    for o in OBJ.values():
        if o["objType"] == "RECORD_TYPE":
            rts.append({"name": o["name"], "sqlReferenceName": o["tableName"],
                        "fields": [{"name": f["fieldName"], "type": f["fieldType"]} for f in o["fields"]],
                        "relationships": [{"name": r["relationshipName"]} for r in o.get("relationships", [])]})
    return json.dumps({"recordTypes": rts})


@mcp.tool()
def appian_data_fabric_sql_query(query: str) -> str:
    """Execute a SQL query against Appian record data."""
    m = re.fullmatch(r"SELECT COUNT\(\*\) AS total FROM ([A-Za-z_][A-Za-z0-9_]*)", query.strip())
    if not m:
        raise ValueError("Only COUNT queries are allowed in this mock")
    return json.dumps({"results": [{"total": COUNTS.get(m.group(1), 0)}], "rowCount": 1})


@mcp.tool()
def appian_search_tools(query: str) -> str:
    """Search for available MCP tools by keyword."""
    return json.dumps({"tools": []})


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
