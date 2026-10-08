"""Utilidades comunes: proyectos temporales con una configuracion MCP que apunta a los mocks.

La skill que se prueba es la de $PLUGIN_A_PROBAR/skills/appian-reverse-engineering (por defecto, la de este
repositorio); los datos de las pruebas están en datos/ y el Dev MCP simulado en mock_devmcp/, junto a este fichero.
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parent
PLUGIN = Path(os.environ.get("PLUGIN_A_PROBAR") or AQUI.parents[1]).resolve()
SKILL = PLUGIN / "skills" / "appian-reverse-engineering"
DATOS = AQUI / "datos"
MOCK = AQUI / "mock_devmcp" / "lcp_mcp_server_mock.py"
HTTP_MOCK = AQUI / "mock_devmcp" / "appian_mcp_server_mock.py"
EXTRACT = SKILL / "scripts" / "devmcp_extract.py"
BUILD_MODEL = SKILL / "scripts" / "build_model.py"
BUILD_SUMMARY = SKILL / "scripts" / "build_summary.py"

sys.path.insert(0, str(SKILL / "scripts"))
import rutas  # noqa: E402


class Project:
    def __init__(self, base: Path):
        self.base = base
        self.proj = base / "proj"
        self.home = base / "home"
        self.out = base / "out"
        self.calls = base / "calls.jsonl"
        self.proj.mkdir(parents=True)
        self.home.mkdir()
        self.servers: dict = {}

    def add_devmcp(self, name="appian", variant="a", mode="full", **extra_env):
        env = {"LCP_URL": "https://demo.appiancloud.com", "LCP_TOOL_MODE": mode, "MOCK_VARIANT": variant,
               "MOCK_CALL_LOG": str(self.calls), **{k: str(v) for k, v in extra_env.items()}}
        self.servers[name] = {"command": sys.executable, "args": [str(MOCK), "--module", "lcp_mcp_server"],
                              "env": env}
        self._write()

    def add_http(self, name, url, headers=None):
        self.servers[name] = {"type": "http", "url": url, **({"headers": headers} if headers else {})}
        self._write()

    def _write(self):
        (self.proj / ".mcp.json").write_text(json.dumps({"mcpServers": self.servers}, indent=1))

    def run(self, *args, check=None, timeout=180):
        env = dict(os.environ, APPIAN_RE_HOME=str(self.home), APPDATA=str(self.home / "AppData"))
        p = subprocess.run([sys.executable, str(EXTRACT), *args], cwd=self.proj, env=env,
                           capture_output=True, text=True, timeout=timeout)
        if check is not None:
            assert p.returncode == check, f"exit {p.returncode}\nSTDOUT:\n{p.stdout}\nSTDERR:\n{p.stderr[-3000:]}"
        return p

    def calls_list(self) -> list[dict]:
        if not self.calls.exists():
            return []
        return [json.loads(line) for line in self.calls.read_text().splitlines() if line.strip()]

    def interm(self) -> Path:
        return rutas.work_dir(self.out)

    def load(self, rel: str):
        return json.loads((self.interm() / rel).read_text(encoding="utf-8"))


@pytest.fixture
def project(tmp_path):
    return Project(tmp_path)


def free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


@pytest.fixture
def http_server():
    port = free_port()
    proc = subprocess.Popen([sys.executable, str(HTTP_MOCK), str(port)], stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
    deadline = time.time() + 20
    while time.time() < deadline:
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.5).close()
            break
        except OSError:
            time.sleep(0.2)
    yield f"http://127.0.0.1:{port}/mcp"
    proc.terminate()
    proc.wait(timeout=10)
