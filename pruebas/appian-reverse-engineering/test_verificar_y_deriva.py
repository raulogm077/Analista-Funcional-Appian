"""Verificar, deriva y reextracción, con el Dev MCP simulado.

- verificar: por objeto, si existe, su tipo, su última modificación y, de record types y CDT, sus campos; sale 0
  aunque falte alguno y 2 sin conexión. No escribe en ninguna extracción.
- deriva: frente al as-is, cambiados (historial de versiones), nuevos y retirados; --ignorar descarta los de nuestras
  unidades modificados después de una fecha; sin historial en el Dev MCP, lo dice y no supone nada.
- extract --solo: vuelve a pedir solo esos objetos y rehace el modelo.
- build_registry.py mantiene los IDs de hallazgos y NV al repetir la ingeniería inversa.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
import asyncio
from types import SimpleNamespace

import pytest
import devmcp_extract as dx

from conftest import BUILD_MODEL, SKILL

sys.path.insert(0, str(Path(__file__).parent / "mock_devmcp"))
import fixture  # noqa: E402

OBJS, KEY_BY_UUID, _ = fixture.build()
APP = OBJS[fixture.APP_KEY]["uuid"]
SCRIPTS = SKILL / "scripts"


class SesionVerificarExterno:
    """Cliente en memoria: el inventario contextual y la busqueda global son distintos."""
    app = {"uuid": "app-contexto", "name": "LAB Catalogo", "type": "application", "mcpType": "APPLICATION"}
    panel = {"uuid": "panel-externo", "name": "LAB_Panel", "type": "INTERFACE"}

    def __init__(self, paginas=None):
        self.calls = []
        self.paginas = paginas or [{"items": [self.panel], "total": 1}]

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        pass

    async def list_tools(self):
        def tool(name, properties, required=()):
            return SimpleNamespace(name=name, description="", annotations=None,
                                   inputSchema={"properties": properties, "required": list(required)})
        return [tool("listObjects", {"query": {"type": "string"}, "types": {"type": "array", "items": {"type": "string"}},
                                     "limit": {"type": "integer"}, "offset": {"type": "integer"},
                                     "appUuid": {"type": "string"}}),
                tool("getObjectVersionHistory", {"uuid": {"type": "string"}}, ["uuid"]),
                tool("runAllInterfaceTestCases", {"uuid": {"type": "string"}}, ["uuid"])]

    async def call(self, name, args):
        self.calls.append({"tool": name, "args": args.copy()})
        if name == "listObjects":
            pagina = self.paginas[min(len([c for c in self.calls if c["tool"] == name]) - 1, len(self.paginas) - 1)]
            return pagina if isinstance(pagina, dx.CallResult) else dx.CallResult(True, pagina)
        if name == "runAllInterfaceTestCases":
            return dx.CallResult(True, {"results": [{"name": "Caso ficticio", "success": True}]})
        return dx.CallResult(True, {"versions": []})


def ejecutar_verificador_externo(monkeypatch, tmp_path, session, objetos, locales=()):
    async def preparar(ex, *_):
        await ex.load_catalog()
        return session.app, list(locales), []
    monkeypatch.setattr(dx, "prepare", preparar)
    choice = dx.ServerChoice("mock", "mock", "", [], {"LCP_URL": "https://demo.example.org"})
    monkeypatch.setattr(dx, "open_session", lambda *_: (session, choice, 0, ""))
    esperado = tmp_path / "esperado.json"
    esperado.write_text(json.dumps({"_issue": {"id": "ISS-01", "unidad": "EV-01", "version": "ficticia"}, **objetos}),
                        encoding="utf-8")
    salida = tmp_path / "resultado.json"
    args = SimpleNamespace(objetos=None, esperado=str(esperado), registro=False, policy=dx.DEFAULT_POLICY,
                           out=str(salida), json=False)
    code = asyncio.run(dx.cmd_verificar(args))
    return code, json.loads(salida.read_text(encoding="utf-8")) if salida.exists() else None


def test_verificador_app_contextual_y_panel_externo_comparten_resolucion(monkeypatch, tmp_path):
    s = SesionVerificarExterno()
    code, r = ejecutar_verificador_externo(monkeypatch, tmp_path, s, {s.app["name"]: {}, s.panel["name"]: {"tipo": "interface"}})
    assert code == 0 and r["faltan"] == [] and r["conDiferencias"] == []
    assert {o["uuid"] for o in r["objetos"]} == {s.app["uuid"], s.panel["uuid"]}
    assert [(o["objeto"], o["de"], o["casos"]) for o in r["pruebas"]["objetos"]] == [(s.panel["name"], "issue", 1)]
    consultas = [c["args"] for c in s.calls if c["tool"] == "listObjects"]
    assert consultas == [{"query": s.panel["name"], "types": ["INTERFACE"], "limit": 10, "offset": 0}]


@pytest.mark.parametrize("tipo", ["application", "interface"])
def test_verificador_app_homonima_no_sustituye_objeto_de_otro_tipo(monkeypatch, tmp_path, tipo):
    s = SesionVerificarExterno()
    homonimo = {"uuid": "interfaz-homonima", "name": s.app["name"], "type": "interface"}
    _, r = ejecutar_verificador_externo(monkeypatch, tmp_path, s, {s.app["name"]: {"tipo": tipo}}, [homonimo])
    assert r["objetos"][0]["uuid"] == (s.app["uuid"] if tipo == "application" else homonimo["uuid"])
    assert not any(c["tool"] == "listObjects" for c in s.calls)


def test_verificador_busqueda_paginada_exige_nombre_y_tipo_exacto(monkeypatch, tmp_path):
    s = SesionVerificarExterno([{"items": [{"uuid": "parecido", "name": "LAB_Panel_Anterior", "type": "INTERFACE"}], "total": 2},
                              {"items": [SesionVerificarExterno.panel], "total": 2}])
    _, r = ejecutar_verificador_externo(monkeypatch, tmp_path, s, {s.panel["name"]: {"tipo": "interface"}})
    assert r["objetos"][0]["uuid"] == s.panel["uuid"] and not r["faltan"]
    assert [c["args"]["offset"] for c in s.calls if c["tool"] == "listObjects"] == [0, 1]


@pytest.mark.parametrize("paginas", [
    [{"items": [SesionVerificarExterno.panel, {**SesionVerificarExterno.panel, "uuid": "otro-panel"}], "total": 2}],
    [dx.CallResult(False, error="lectura fallida")],
    [{"items": [SesionVerificarExterno.panel], "total": 2}],
    [{"items": [SesionVerificarExterno.panel]}],
    [{"items": [{"name": "LAB_Panel"}], "total": 1}],
    [dx.CallResult(False, error="HTTP 403 Forbidden")],
])
def test_verificador_busqueda_incierta_no_sobrescribe_resultado(monkeypatch, tmp_path, paginas):
    s = SesionVerificarExterno(paginas)
    previo = tmp_path / "resultado.json"
    previo.write_text('{"anterior": true}', encoding="utf-8")
    antes = previo.read_bytes()
    code, _ = ejecutar_verificador_externo(monkeypatch, tmp_path, s, {s.panel["name"]: {"tipo": "interface"}})
    expected_code = dx.EXIT_START if isinstance(paginas[0], dx.CallResult) else dx.EXIT_APP
    assert code == expected_code and previo.read_bytes() == antes
    assert not any(c["tool"] == "runAllInterfaceTestCases" for c in s.calls)


@pytest.mark.parametrize("tipo", [None, "tipo no reconocido", "interface"])
def test_verificador_ausencia_y_tipo_desconocido_sin_busqueda_amplia(monkeypatch, tmp_path, tipo):
    s = SesionVerificarExterno([{"items": [{"uuid": "otro", "name": "LAB_Panel_Anterior", "type": "INTERFACE"}], "total": 1}])
    _, r = ejecutar_verificador_externo(monkeypatch, tmp_path, s, {s.panel["name"]: {"tipo": tipo} if tipo else {}})
    assert r["faltan"] == [s.panel["name"]]
    assert bool([c for c in s.calls if c["tool"] == "listObjects"]) == (tipo == "interface")


def test_verificador_uuid_contextual_prevalece_sin_busqueda(monkeypatch, tmp_path):
    s = SesionVerificarExterno()
    _, r = ejecutar_verificador_externo(monkeypatch, tmp_path, s, {s.app["uuid"]: {"tipo": "application"}})
    assert r["objetos"][0]["uuid"] == s.app["uuid"] and not r["faltan"]
    assert not any(c["tool"] == "listObjects" for c in s.calls)


def test_verificador_nombre_vacio_no_abre_busqueda_global(monkeypatch, tmp_path):
    s = SesionVerificarExterno()
    _, r = ejecutar_verificador_externo(monkeypatch, tmp_path, s, {"": {"tipo": "interface"}})
    assert r["faltan"] == [""] and not any(c["tool"] == "listObjects" for c in s.calls)


@pytest.mark.parametrize("inversa", [False, True])
def test_verificador_homonimos_locales_no_dependen_del_orden(monkeypatch, tmp_path, inversa):
    s = SesionVerificarExterno()
    locales = [{**s.panel, "type": "recordType", "uuid": "record-homonimo"}, {**s.panel, "type": "interface"}]
    _, r = ejecutar_verificador_externo(monkeypatch, tmp_path, s, {s.panel["name"]: {"tipo": "interface"}},
                                       locales[::-1] if inversa else locales)
    assert r["objetos"][0]["uuid"] == s.panel["uuid"]
    assert not any(c["tool"] == "listObjects" for c in s.calls)


def test_verificador_app_homonima_sin_tipo_conserva_resultado(monkeypatch, tmp_path):
    s = SesionVerificarExterno()
    previo = tmp_path / "resultado.json"
    previo.write_text('{"anterior": true}', encoding="utf-8")
    homonimo = {"uuid": "interfaz-homonima", "name": s.app["name"], "type": "interface"}
    code, r = ejecutar_verificador_externo(monkeypatch, tmp_path, s, {s.app["name"]: {}}, [homonimo])
    assert code == dx.EXIT_APP and r == {"anterior": True} and not s.calls


def test_verificador_respeta_exclusion_de_busqueda(monkeypatch, tmp_path, capsys):
    original = dx.Policy
    def policy(path):
        p = original(path)
        p.excludes.append((re.compile(r"^listObjects$"), "Exclusion ficticia"))
        return p
    monkeypatch.setattr(dx, "Policy", policy)
    s = SesionVerificarExterno()
    _, r = ejecutar_verificador_externo(monkeypatch, tmp_path, s, {s.panel["name"]: {"tipo": "interface"}})
    assert r["faltan"] == [s.panel["name"]] and not s.calls
    assert "catalogo no permite buscar" in capsys.readouterr().err


def uuids_de(llamadas: list[dict]) -> set[str]:
    """Los uuids de la aplicación o de sus objetos que llevan unas llamadas al simulador."""
    return {v for c in llamadas for v in c["args"].values() if v in KEY_BY_UUID}


def corre(script, salida, check=0):
    p = subprocess.run([sys.executable, str(SCRIPTS / script), str(salida)], capture_output=True, text=True,
                       encoding="utf-8")
    assert check is None or p.returncode == check, p.stdout + p.stderr
    return p


def extrae(project, *extra, check=0):
    return project.run("extract", "--app", "DEM", "--out", str(project.out), "--retry-delay", "0.1", *extra, check=check)


def huella(carpeta: Path) -> dict[str, str]:
    return {f.relative_to(carpeta).as_posix(): hashlib.sha1(f.read_bytes()).hexdigest()
            for f in sorted(carpeta.rglob("*")) if f.is_file()}


# ---------------------------------------------------------------- verificar

def test_verificar(project, tmp_path):
    """Un objeto que falta sale «existe: false» y en «faltan» (salida 0); de un record type, sus campos para comparar
    con §3; de cada uno, su última modificación. Sin lo esperado de una issue no ejecuta casos de prueba ni copia sus
    definiciones (eran 2.301 líneas para 20 objetos en T6)."""
    project.add_devmcp(MOCK_PRUEBAS="1")
    destino = tmp_path / "construccion" / "verificacion" / "EV-02.json"
    p = project.run("verificar", "--app", "DEM", "--objetos", "DEM Solicitud,dem_er_esadmin,DEM_ER_Inventada",
                    "--out", str(destino), check=0)
    assert "DEM_ER_Inventada" in p.stdout
    v = json.loads(destino.read_text(encoding="utf-8"))
    assert v["entorno"] == "https://demo.appiancloud.com" and v["aplicacion"]["prefijo"] == "DEM"
    assert v["conHistorialDeVersiones"] is True and "pruebas" not in v
    solicitud, regla, falta = v["objetos"]
    assert (solicitud["existe"], solicitud["tipo"], solicitud["nombre"]) == (True, "recordType", "DEM Solicitud")
    assert {"nombre": "titulo", "tipo": "TEXT", "longitud": 255} in solicitud["campos"]
    assert {"nombre": "id", "tipo": "INTEGER", "clavePrimaria": True} in solicitud["campos"]
    assert solicitud["ultimaModificacion"] == {"fecha": "2026-09-01T10:00:00Z", "autor": "marta.ruiz", "versiones": 3}
    assert (regla["pedido"], regla["nombre"], regla["tipo"]) == ("dem_er_esadmin", "DEM_ER_EsAdmin", "expressionRule")
    assert "campos" not in regla and "casosDePrueba" not in regla and "acciones" not in solicitud
    assert falta == {"pedido": "DEM_ER_Inventada", "existe": False} and v["faltan"] == ["DEM_ER_Inventada"]
    assert not any(c["tool"].startswith("run") for c in project.calls_list())
    assert not project.out.exists()                                 # no escribe en ninguna extracción
    # @fichero, uno por línea
    project.add_devmcp()
    lista = tmp_path / "objetos.txt"
    lista.write_text("# los de EV-02\nDEM Estado\n\n", encoding="utf-8-sig")       # con BOM, como el Bloc de notas
    project.run("verificar", "--app", "DEM", "--objetos", f"@{lista}", "--out", str(destino), check=0)
    v = json.loads(destino.read_text(encoding="utf-8"))
    assert [o["nombre"] for o in v["objetos"]] == ["DEM Estado"]
    assert [c["nombre"] for c in v["objetos"][0]["campos"]] == ["id", "label"]


def test_verificar_con_esperado(project, tmp_path):
    """Con --esperado (lo que dice el técnico de la unidad), verificar calcula las diferencias, que no deduce quien
    lee: el objeto que falta, el tipo distinto y los campos que faltan, sobran o cambian de tipo. Los tipos se comparan
    sin mayúsculas y con sus sinónimos (Integer = Number (Integer) = INTEGER). Verifica los de --esperado aunque no
    estén en --objetos."""
    project.add_devmcp()
    campos = [("id", "Number (Integer)"), ("titulo", "Text"), ("estadoId", "Integer"), ("solicitante", "User"),
              ("fechaAlta", "Date and Time"), ("importe", "Integer"), ("prioridad", "Text")]
    esperado = tmp_path / "esperado.json"
    esperado.write_text(json.dumps({
        "DEM Solicitud": {"tipo": "recordType", "campos": [{"nombre": n, "tipo": t} for n, t in campos]},
        "DEM Estado": {"tipo": "Record Type", "campos": [{"nombre": "ID", "tipo": "integer"}, {"nombre": "label",
                                                                                              "tipo": "Text"}]},
        "DEM_ER_EsAdmin": {"tipo": "interface"},
        "DEM_ER_Inventada": {"tipo": "expressionRule"}}, ensure_ascii=False), encoding="utf-8-sig")
    destino = tmp_path / "v.json"
    project.run("verificar", "--app", "DEM", "--objetos", "DEM_Dashboard", "--esperado", str(esperado),
                "--out", str(destino), check=0)
    v = json.loads(destino.read_text(encoding="utf-8"))
    por = {o["pedido"]: o for o in v["objetos"]}
    assert list(por) == ["DEM_Dashboard", "DEM Solicitud", "DEM Estado", "DEM_ER_EsAdmin", "DEM_ER_Inventada"]
    assert "diferencias" not in por["DEM_Dashboard"]                     # sin esperado, no se compara
    assert por["DEM Solicitud"]["diferencias"] == {
        "faltanCampos": ["prioridad"], "camposDeOtroTipo": [{"nombre": "importe", "esperado": "Integer", "real": "DECIMAL"}]}
    assert por["DEM Estado"]["diferencias"] == {}
    assert por["DEM_ER_EsAdmin"]["diferencias"] == {"tipo": {"esperado": "interface", "real": "expressionRule"}}
    assert por["DEM_ER_Inventada"]["diferencias"] == {"falta": True}
    assert v["conDiferencias"] == ["DEM Solicitud", "DEM_ER_EsAdmin", "DEM_ER_Inventada"]
    assert "issue" not in v                                              # lo esperado no era el de una issue
    project.run("verificar", "--app", "DEM", "--out", str(destino), check=2)    # sin --objetos ni --esperado


def test_verificar_dice_de_que_issue_es(project, tmp_path):
    """Lo esperado de una issue (indice.py issues del analista) lleva en «_issue» su id, su unidad y su versión. No es un
    objeto que verificar: pasa tal cual al resultado, en «issue», y así se sabe si la verificación es de la versión de
    ahora de la issue o de una anterior."""
    project.add_devmcp()
    de = {"id": "ISS-02", "unidad": "EV-02", "version": "3f9a0c1d2b7e"}
    esperado = tmp_path / "ISS-02-esperado.json"
    esperado.write_text(json.dumps({"_issue": de, "DEM Estado": {"tipo": "recordType"}}), encoding="utf-8")
    destino = tmp_path / "construccion" / "EV-02" / "verificacion" / "ISS-02.json"
    project.run("verificar", "--app", "DEM", "--esperado", str(esperado), "--out", str(destino), check=0)
    v = json.loads(destino.read_text(encoding="utf-8"))
    assert v["issue"] == de
    assert [o["pedido"] for o in v["objetos"]] == ["DEM Estado"] and v["faltan"] == [] and v["conDiferencias"] == []
    assert list(v)[:3] == ["generadoEn", "entorno", "issue"]


def test_atajo_con_comillas():
    """En el atajo de SKILL.md, los valores de --objetos, --esperado, --ignorar y --solo van entre comillas: en
    PowerShell, un @fichero sin comillas no llega como texto."""
    atajo = (SKILL / "SKILL.md").read_text(encoding="utf-8").split("## Verificar o deriva (atajo)", 1)[1]
    atajo = atajo.split("\n---", 1)[0]
    valores = re.findall(r"--(?:objetos|esperado|ignorar|solo) (\S)", atajo)
    assert len(valores) >= 4 and set(valores) == {'"'}, valores


def test_verificar_y_deriva_sin_configuracion(project, tmp_path):
    """Sin el Dev MCP en la configuración, los mismos códigos que el resto de subcomandos (11) y nada escrito."""
    p = project.run("verificar", "--app", "DEM", "--objetos", "DEM Solicitud", "--out", str(tmp_path / "v.json"), check=11)
    assert "Dev MCP" in p.stderr and not (tmp_path / "v.json").exists()
    project.add_devmcp()
    extrae(project)
    project.servers.clear()
    project._write()
    project.run("deriva", "--out", str(project.out), check=11)
    assert not (project.out / "datos" / "deriva.json").exists()


# ---------------------------------------------------------------- deriva

def test_deriva(project, tmp_path):
    """Frente al as-is: una versión posterior es «cambiado»; un objeto que ya no está, «retirado»; uno que no estaba,
    «nuevo». Pide solo la lista de la aplicación y el historial de versiones, y no toca la extracción."""
    project.add_devmcp(MOCK_OCULTAR="PM_BATCH")                   # el as-is, sin el proceso batch
    extrae(project)
    antes, n = huella(project.interm()), len(project.calls_list())
    project.add_devmcp(MOCK_OCULTAR="PM_HUERF",
                       MOCK_VERSION_NUEVA="I_DASH=2026-10-05T09:00:00Z,R_CONT=2026-10-06T11:00:00Z")
    p = project.run("deriva", "--out", str(project.out), check=0)
    assert "2 cambiados, 1 nuevos, 1 retirados" in p.stdout, p.stdout
    d = json.loads((project.out / "datos" / "deriva.json").read_text(encoding="utf-8"))
    assert d["conHistorialDeVersiones"] is True and d["alcance"] == "todos"
    cambiados = {c["nombre"]: c for c in d["cambiados"]}
    assert set(cambiados) == {"DEM_Dashboard", "DEM_ER_ContarPorEstado"}
    assert cambiados["DEM_Dashboard"]["asIs"]["fecha"] == "2026-09-01T10:00:00Z"
    assert cambiados["DEM_Dashboard"]["ahora"] == {"fecha": "2026-10-05T09:00:00Z", "autor": "otro.equipo", "versiones": 4}
    assert [x["nombre"] for x in d["nuevos"]] == ["DEM Batch Recordatorios"]
    assert [x["nombre"] for x in d["retirados"]] == ["DEM Utilidad Huérfana"]
    assert d["ignorados"] == [] and d["sinDato"] == []
    llamadas = project.calls_list()[n:]
    por_objeto = {c["tool"] for c in llamadas if uuids_de([c]) - {APP}}
    assert por_objeto == {"getObjectVersionHistory"}, por_objeto
    assert huella(project.interm()) == antes                       # la extracción, igual
    # --ignorar: lo de nuestras unidades modificado después de aprobarlas no cuenta; lo de antes, sí
    project.run("deriva", "--out", str(project.out), "--ignorar",
                "DEM_Dashboard@2026-10-01,DEM_ER_ContarPorEstado@2026-10-07", check=0)
    d = json.loads((project.out / "datos" / "deriva.json").read_text(encoding="utf-8"))
    assert [c["nombre"] for c in d["cambiados"]] == ["DEM_ER_ContarPorEstado"]
    assert [(i["nombre"], i["desde"]) for i in d["ignorados"]] == [("DEM_Dashboard", "2026-10-01")]
    # --objetos: solo esos, y solo su historial
    n = len(project.calls_list())
    project.run("deriva", "--out", str(project.out), "--objetos", "DEM_Dashboard,DEM_Nada", check=0)
    d = json.loads((project.out / "datos" / "deriva.json").read_text(encoding="utf-8"))
    assert [c["nombre"] for c in d["cambiados"]] == ["DEM_Dashboard"] and d["nuevos"] == d["retirados"] == []
    assert d["noEncontrados"] == ["DEM_Nada"]
    assert uuids_de(project.calls_list()[n:]) - {APP} == {OBJS["I_DASH"]["uuid"]}
    project.run("deriva", "--out", str(project.out), "--ignorar", "DEM_Dashboard", check=2)   # sin fecha


def test_deriva_sin_historial(project, tmp_path):
    """Si el Dev MCP no da el historial de versiones, la deriva lo dice y no supone nada: no hay «cambiados»."""
    project.add_devmcp(MOCK_OCULTAR="PM_BATCH")
    extrae(project)
    project.add_devmcp(MOCK_VERSION_NUEVA="I_DASH=2026-10-05T09:00:00Z")   # ahora está el batch y cambió una interfaz
    politica = json.loads((SCRIPTS / "devmcp_policy.json").read_text(encoding="utf-8"))
    politica["excludePatterns"].append({"pattern": "(?i)version", "reason": "Sin historial (prueba)."})
    (tmp_path / "politica.json").write_text(json.dumps(politica), encoding="utf-8")
    p = project.run("deriva", "--out", str(project.out), "--policy", str(tmp_path / "politica.json"), check=0)
    d = json.loads((project.out / "datos" / "deriva.json").read_text(encoding="utf-8"))
    assert d["conHistorialDeVersiones"] is False and d["cambiados"] is None and "historial" in d["nota"]
    assert [x["nombre"] for x in d["nuevos"]] == ["DEM Batch Recordatorios"]
    assert "sin historial" in p.stdout


def test_deriva_sin_as_is(project):
    project.add_devmcp()
    p = project.run("deriva", "--out", str(project.out), check=2)
    assert "No hay extraccion" in p.stderr


# ---------------------------------------------------------------- extract --solo

def test_extract_solo(project):
    """--solo vuelve a pedir solo esos objetos (y la lista de la aplicación); de los demás usa lo guardado, sin llamar
    al Dev MCP. Rehace el modelo, con lo nuevo de esos objetos y lo de siempre de los demás."""
    project.add_devmcp()
    extrae(project)
    n, completa = len(project.calls_list()), project.load("extraction_report.json")["startedAt"]
    project.add_devmcp(MOCK_VERSION_NUEVA="I_DASH=2026-10-05T09:00:00Z,R_CONT=2026-10-06T11:00:00Z")
    p = extrae(project, "--solo", "DEM_Dashboard,DEM_Nada")
    assert "DEM_Nada" in p.stderr and "inventory.json" in p.stdout, p.stdout + p.stderr
    llamadas = project.calls_list()[n:]
    assert uuids_de(llamadas) == {APP, OBJS["I_DASH"]["uuid"]}, uuids_de(llamadas)
    assert any(OBJS["I_DASH"]["uuid"] in c["args"].values() for c in llamadas)
    inv = project.load("inventory.json")
    por = {o["uuid"]: o for objs in inv["objects"].values() for o in objs}
    assert por[OBJS["I_DASH"]["uuid"]]["versions"]["lastModifiedOn"] == "2026-10-05T09:00:00Z"
    assert por[OBJS["R_CONT"]["uuid"]]["versions"]["lastModifiedOn"] == "2026-09-01T10:00:00Z"   # lo guardado
    assert por[OBJS["RT_SOL"]["uuid"]]["detail"] == "full"
    rep = project.load("extraction_report.json")
    assert rep["solo"] == ["DEM_Dashboard"] and "getRecordType" in rep["toolsUsed"]
    # usadas más omitidas son el catálogo también al reextraer unos pocos (lo cuenta INVENTARIO)
    catalogo = {t["name"] for t in project.load("mcp_catalog.json")["tools"]}
    omitidas = {t["name"] for t in rep["toolsOmitted"]}
    assert not set(rep["toolsUsed"]) & omitidas and set(rep["toolsUsed"]) | omitidas == catalogo
    assert any((d["tool"], d["type"]) == ("validateDesignObject", "constant") for d in rep["disabledAfterProbe"])
    # la fecha de la extracción es la de la completa; la reextracción va aparte
    assert rep["startedAt"] == completa and rep["reextraidoEn"] >= completa
    assert inv["source"]["extractedAt"] == completa
    # los nombres se comprueban antes de guardar nada: si no hay ninguno, la extracción no cambia
    antes = huella(project.interm())
    extrae(project, "--solo", "DEM_Nada", check=2)
    assert huella(project.interm()) == antes
    extrae(project, "--solo", "DEM_Dashboard", "--refresh", check=2)


def test_extract_solo_con_listas_filtradas_conserva_inventario(project):
    """Una lista parcial no retira los modelos ni cambia a unknown los tipos leidos antes."""
    project.add_devmcp()
    extrae(project)
    anterior = {o["uuid"]: o for o in project.load("mcp_raw/_objects.json")["objects"]}
    n = len(project.calls_list())
    extrae(project, "--solo", "DEM Solicitud", "--only",
           "^(listApplications|getApplication|listRecordTypes|getRecordType)$")

    actual = {o["uuid"]: o for o in project.load("mcp_raw/_objects.json")["objects"]}
    assert set(anterior) <= set(actual)
    assert {u: o["type"] for u, o in anterior.items()} == {u: actual[u]["type"] for u in anterior}
    assert actual[OBJS["PM_BATCH"]["uuid"]]["type"] == "processModel"
    inventario = project.load("inventory.json")
    inventariados = {o["uuid"] for lista in inventario["objects"].values() for o in lista}
    assert set(anterior) <= inventariados
    assert project.load("extraction_report.json")["objectListComplete"] is False
    assert uuids_de(project.calls_list()[n:]) <= {APP, OBJS["RT_SOL"]["uuid"]}


def test_inventario_parcial_no_degrada_tipo_conocido():
    from devmcp_extract import conservar_objetos_parciales

    anteriores = [{"uuid": "obj-regla", "name": "DEM Regla", "type": "expressionRule",
                   "mcpType": "FREEFORM_RULE", "sources": ["listExpressionRules"]},
                  {"uuid": "obj-proceso", "name": "DEM Proceso", "type": "processModel",
                   "sources": ["listProcessModels"]},
                  {"uuid": "obj-cambiado", "name": "DEM Antes", "type": "processModel",
                   "mcpType": "PROCESS_MODEL", "sources": ["listProcessModels"]}]
    actuales = [{"uuid": "obj-regla", "name": "DEM Regla", "type": "unknown",
                 "mcpType": None, "sources": ["listApplicationObjects"]},
                {"uuid": "obj-nuevo", "name": "DEM Nueva interfaz", "type": "interface",
                 "sources": ["listInterfaces"]},
                {"uuid": "obj-cambiado", "name": "DEM Ahora", "type": "interface",
                 "sources": ["listInterfaces"]}]
    merged = {o["uuid"]: o for o in conservar_objetos_parciales(anteriores, actuales)}
    assert set(merged) == {"obj-regla", "obj-proceso", "obj-nuevo", "obj-cambiado"}
    assert merged["obj-regla"]["type"] == "expressionRule"
    assert merged["obj-regla"]["mcpType"] == "FREEFORM_RULE"
    assert merged["obj-proceso"] == anteriores[1]
    assert merged["obj-nuevo"] == actuales[1]
    assert merged["obj-cambiado"]["type"] == "interface" and merged["obj-cambiado"]["mcpType"] is None


def test_extract_solo_con_fallos_guardados(project):
    """Con --solo, lo guardado de los demás objetos se lee sin sonda: los fallos guardados de otras interfaces (las
    tres primeras, que desactivaron getInterface en la extracción completa) no dejan sin llamadas al objeto pedido."""
    from rutas import carpeta_objeto
    project.add_devmcp(MOCK_FAIL_KEYS="I_ADMIN,I_DASH,I_REV")
    extrae(project)
    resumen = carpeta_objeto(project.interm() / "mcp_raw", "interface", OBJS["I_RES"]["uuid"])
    assert not (resumen / "getInterface.json").exists()                 # desactivada tras la sonda
    n = len(project.calls_list())
    project.add_devmcp()                                                # ya funciona
    extrae(project, "--solo", "DEM_SolicitudResumen")
    llamadas = project.calls_list()[n:]
    assert uuids_de(llamadas) == {APP, OBJS["I_RES"]["uuid"]}
    assert any(c["tool"] == "getInterface" and OBJS["I_RES"]["uuid"] in c["args"].values() for c in llamadas)
    por = {o["uuid"]: o for objs in project.load("inventory.json")["objects"].values() for o in objs}
    assert por[OBJS["I_RES"]["uuid"]]["detail"] == "full" and por[OBJS["I_DASH"]["uuid"]]["detail"] == "none"


def test_extract_solo_sin_extraccion(project):
    project.add_devmcp()
    p = extrae(project, "--solo", "DEM_Dashboard", check=2)
    assert "extract sin --solo" in p.stderr and project.calls_list() == []


# ---------------------------------------------------------------- IDs estables

def escribe(ruta: Path, datos) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(datos if isinstance(datos, str) else json.dumps(datos, ensure_ascii=False), encoding="utf-8")


def hallazgo(id_, titulo, objetos, **kw):
    return {"id": id_, "titulo": titulo, "area": "procesos", "severidad": "Baja", "certeza": "verificado",
            "objetos": objetos, "documento": "08-procesos-bpmn/indice.md#hallazgos",
            "evidencia": f"mcp:processModel/{objetos[0]}#nodes", **kw}


def nv(id_, pregunta, objetos):
    return {"id": id_, "pregunta": pregunta, "porQue": "La extracción no lo trae.", "queHaceFalta": "Acceso de lectura",
            "aQuien": "Equipo de la aplicación", "dondeSeBusco": "Dev MCP", "objetos": objetos, "indicios": "",
            "estado": "abierto", "documento": "08-procesos-bpmn/indice.md#sin-verificar"}


def test_ids_estables_al_reextraer(project):
    """Al repetir la ingeniería inversa (extract --solo y los agentes de nuevo), un hallazgo y un NV que ya existían
    conservan su ID aunque el agente los numere de otra forma (se casan por área, objetos y señal); los nuevos siguen
    la numeración y un ID retirado no se reutiliza. Los documentos se corrigen con ellos."""
    project.add_devmcp()
    extrae(project)
    corre(BUILD_MODEL.name, project.out)
    salida, trabajo = project.out, project.interm()
    huerfana, alta, revisar = "DEM Utilidad Huérfana", "DEM Alta Solicitud", "DEM Revisar Solicitud"
    escribe(salida / "08-procesos-bpmn" / "indice.md", "# Procesos\n\n## Hallazgos\n\nH-PRO-01 y H-PRO-02. NV-PRO-01.\n")
    escribe(trabajo / "hallazgos" / "process-modeler.json", [
        hallazgo("H-PRO-01", "Sin ejecuciones", [huerfana], senal="sin-ejecuciones"),
        hallazgo("H-PRO-02", "Cancelar no anula el alta", [alta])])
    escribe(trabajo / "sin-verificar" / "process-modeler.json", [nv("NV-PRO-01", "¿Quién revisa?", [revisar])])
    for script in ("build_registry.py", "build_datos.py"):
        corre(script, salida)
    extrae(project, "--solo", alta)
    # el agente lo rehace: numera de nuevo, cambia un título y añade un hallazgo y un NV
    escribe(trabajo / "hallazgos" / "process-modeler.json", [
        hallazgo("H-PRO-01", "La revisión no tiene salida por defecto", [revisar]),
        hallazgo("H-PRO-02", "Cancelar no anula el alta", [alta]),
        hallazgo("H-PRO-03", "Sin ejecuciones en el último año", [huerfana], senal="sin-ejecuciones")])
    escribe(trabajo / "sin-verificar" / "process-modeler.json", [
        nv("NV-PRO-01", "¿Quién da de alta?", [alta]), nv("NV-PRO-02", "¿Quién revisa?", [revisar])])
    escribe(salida / "08-procesos-bpmn" / "indice.md",
            "# Procesos\n\n## Hallazgos\n\nH-PRO-01 (revisión), H-PRO-02 (alta) y H-PRO-03 (huérfana). "
            "NV-PRO-01 (alta) y NV-PRO-02 (revisión).\n")
    p = corre("build_registry.py", salida)
    assert "H-PRO-01 → H-PRO-03" in p.stdout and "H-PRO-03 → H-PRO-01" in p.stdout, p.stdout
    ids = {h["titulo"]: h["id"] for h in json.loads((trabajo / "hallazgos" / "process-modeler.json").read_text("utf-8"))}
    assert ids == {"Sin ejecuciones en el último año": "H-PRO-01", "Cancelar no anula el alta": "H-PRO-02",
                   "La revisión no tiene salida por defecto": "H-PRO-03"}
    nvs = {n["pregunta"]: n["id"] for n in json.loads((trabajo / "sin-verificar" / "process-modeler.json").read_text("utf-8"))}
    assert nvs == {"¿Quién revisa?": "NV-PRO-01", "¿Quién da de alta?": "NV-PRO-02"}
    assert ("H-PRO-03 (revisión), H-PRO-02 (alta) y H-PRO-01 (huérfana). NV-PRO-02 (alta) y NV-PRO-01 (revisión)."
            in (salida / "08-procesos-bpmn" / "indice.md").read_text(encoding="utf-8"))
    corre("build_datos.py", salida)
    datos = json.loads((salida / "datos" / "hallazgos.json").read_text(encoding="utf-8"))["hallazgos"]
    assert [(h["id"], h["objetos"]) for h in datos] == [("H-PRO-01", [huerfana]), ("H-PRO-02", [alta]),
                                                       ("H-PRO-03", [revisar])]
    p = corre("build_registry.py", salida)                       # de nuevo: nada cambia
    assert "IDs que se mantienen" not in p.stdout
    # un hallazgo nuevo con el número de uno retirado no lo reutiliza: sigue la numeración (la de H-PRO-03 también)
    escribe(trabajo / "hallazgos" / "process-modeler.json", [
        hallazgo("H-PRO-01", "Sin ejecuciones en el último año", [huerfana], senal="sin-ejecuciones"),
        hallazgo("H-PRO-02", "El batch no controla los errores", ["DEM Batch Recordatorios"])])
    corre("build_registry.py", salida)
    ids = {h["titulo"]: h["id"] for h in json.loads((trabajo / "hallazgos" / "process-modeler.json").read_text("utf-8"))}
    assert ids == {"Sin ejecuciones en el último año": "H-PRO-01", "El batch no controla los errores": "H-PRO-04"}, ids


def test_omitidas_con_su_motivo():
    """Una herramienta del catálogo sin llamadas sale en toolsOmitted con su motivo: el del plan, que solo había objetos
    no pedidos con --solo (notRequested) o que no aplicaba a ninguno (notApplicable). Usadas más omitidas, el catálogo."""
    sys.path.insert(0, str(SCRIPTS))
    import devmcp_extract as dx
    from types import SimpleNamespace as N
    ex = N(tools=[N(name=n) for n in ("a", "b", "c", "d", "e")],
           stats={"a": {"ok": 3}, "c": {"notRequested": 2}, "d": {"notApplicable": 4}, "e": {}})
    plan = {"tools": [{"name": "a", "use": True}, {"name": "b", "use": False, "reason": "Escribe."},
                      {"name": "c", "use": True}, {"name": "d", "use": True}, {"name": "e", "use": True}]}
    om = {t["name"]: t["reason"] for t in dx.omitidas(ex, plan)}
    assert dx.usadas(ex) == ["a"] and set(om) == {"b", "c", "d", "e"}
    assert om["b"] == "Escribe." and "--solo" in om["c"] and "No aplicaba" in om["d"] and om["e"]


@pytest.mark.parametrize("inversa", [False, True])
def test_verificador_app_tipada_con_varios_objetos_homonimos(monkeypatch, tmp_path, inversa):
    s = SesionVerificarExterno()
    locales = [{"uuid": "interfaz-homonima", "name": s.app["name"], "type": "interface"},
               {"uuid": "registro-homonimo", "name": s.app["name"], "type": "recordType"}]
    code, r = ejecutar_verificador_externo(monkeypatch, tmp_path, s, {s.app["name"]: {"tipo": "application"}},
                                         locales[::-1] if inversa else locales)
    assert code == 0 and r["objetos"][0]["uuid"] == s.app["uuid"]
    assert not any(c["tool"] == "listObjects" for c in s.calls)


def test_verificador_interfaz_externa_homonima_a_la_aplicacion(monkeypatch, tmp_path):
    s = SesionVerificarExterno()
    s.paginas = [{"items": [{**s.panel, "name": s.app["name"]}], "total": 1}]
    code, r = ejecutar_verificador_externo(monkeypatch, tmp_path, s, {s.app["name"]: {"tipo": "interface"}})
    assert code == 0 and r["objetos"][0]["uuid"] == s.panel["uuid"]
    assert r["pruebas"]["objetos"][0]["de"] == "issue"


def test_verificador_ambiguedad_no_diagnostica_fallo_de_arranque(monkeypatch, tmp_path, capsys):
    s = SesionVerificarExterno()
    homonimo = {"uuid": "interfaz-homonima", "name": s.app["name"], "type": "interface"}
    code, _ = ejecutar_verificador_externo(monkeypatch, tmp_path, s, {s.app["name"]: {}}, [homonimo])
    err = capsys.readouterr().err
    assert code == dx.EXIT_APP
    assert "tipo o UUID" in err and "arrancar" not in err


def test_verificador_fallo_de_prueba_del_consumidor_externo_no_se_pierde(monkeypatch, tmp_path):
    class SesionConFallo(SesionVerificarExterno):
        async def call(self, name, args):
            if name == "runAllInterfaceTestCases":
                self.calls.append({"tool": name, "args": args.copy()})
                return dx.CallResult(True, {"results": [{"name": "Caso ficticio", "success": False}]})
            return await super().call(name, args)

    s = SesionConFallo()
    code, r = ejecutar_verificador_externo(monkeypatch, tmp_path, s, {s.panel["name"]: {"tipo": "interface"}})
    assert code == 0 and r["faltan"] == []
    assert r["pruebas"]["fallan"] == 1
    assert r["pruebas"]["objetos"][0]["de"] == "issue"
    assert len(r["pruebas"]["objetos"][0]["fallan"]) == 1


@pytest.mark.parametrize("fallo", ["ambiguo", "incompleto"])
def test_verificador_resolucion_incierta_avisa_al_consumidor_y_se_recupera(monkeypatch, tmp_path, fallo):
    from conftest import PLUGIN
    monkeypatch.syspath_prepend(str(PLUGIN / "skills/appian-functional-analyst/scripts"))
    import issues

    destino = tmp_path / "construccion/EV-01/verificacion/ISS-01.json"
    destino.parent.mkdir(parents=True)
    marca = destino.with_name("ISS-01.interrumpido.json")
    esperado = {"_issue": {"id": "ISS-01", "unidad": "EV-01", "version": "ficticia"},
                "LAB_Panel": {"tipo": "interface"}}
    entrada = tmp_path / "esperado.json"
    entrada.write_text(json.dumps(esperado), encoding="utf-8")
    issue = issues.Issue(filas=[], id="ISS-01", version="ficticia", objetos=["LAB_Panel"], esperado=esperado)
    args = SimpleNamespace(objetos=None, esperado=str(entrada), registro=False, policy=dx.DEFAULT_POLICY,
                           out=str(destino), json=False)
    choice = dx.ServerChoice("mock", "mock", "", [], {"LCP_URL": "https://demo.example.org"})

    def ejecutar(s):
        async def preparar(ex, *_):
            await ex.load_catalog()
            return s.app, [], []
        monkeypatch.setattr(dx, "prepare", preparar)
        monkeypatch.setattr(dx, "open_session", lambda *_: (s, choice, 0, ""))
        return asyncio.run(dx.cmd_verificar(args))

    assert ejecutar(SesionVerificarExterno()) == 0
    assert issues.estado(tmp_path, "EV-01", issue) == (True, "hecha")
    anterior, fuente = destino.read_bytes(), entrada.read_bytes()
    paginas = ([{"items": [SesionVerificarExterno.panel, {**SesionVerificarExterno.panel, "uuid": "otro"}], "total": 2}]
               if fallo == "ambiguo" else [{"items": [SesionVerificarExterno.panel]}])
    sesion = SesionVerificarExterno(paginas)
    assert ejecutar(sesion) == dx.EXIT_APP
    assert destino.read_bytes() == anterior and entrada.read_bytes() == fuente
    parcial = json.loads(marca.read_text(encoding="utf-8"))
    assert parcial["status"] == "partial" and parcial["previousResultIsCurrent"] is False
    assert "LAB_Panel" in parcial["interruption"]["error"]
    hecha, motivo = issues.estado(tmp_path, "EV-01", issue)
    assert hecha and "última lectura interrumpida" in motivo and "verificación anterior" in motivo
    assert [c["tool"] for c in sesion.calls] == ["listObjects"]
    assert ejecutar(SesionVerificarExterno()) == 0
    assert json.loads(marca.read_text(encoding="utf-8"))["status"] == "superseded"
    assert issues.estado(tmp_path, "EV-01", issue) == (True, "hecha")
