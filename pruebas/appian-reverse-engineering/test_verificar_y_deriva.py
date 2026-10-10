"""Verificar, deriva y reextracción (tarea 1.9 de la 0.7.0-beta.2; diseño 3.4 y 3.6), con el Dev MCP simulado.

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
import subprocess
import sys
from pathlib import Path

from conftest import BUILD_MODEL, SKILL

sys.path.insert(0, str(Path(__file__).parent / "mock_devmcp"))
import fixture  # noqa: E402

OBJS, KEY_BY_UUID, _ = fixture.build()
APP = OBJS[fixture.APP_KEY]["uuid"]
SCRIPTS = SKILL / "scripts"


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
    con §3; de cada uno, su última modificación; de una regla, sus casos de prueba si el Dev MCP los expone."""
    project.add_devmcp(MOCK_CASOS_DE_PRUEBA="1")
    destino = tmp_path / "construccion" / "verificacion" / "EV-02.json"
    p = project.run("verificar", "--app", "DEM", "--objetos", "DEM Solicitud,dem_er_esadmin,DEM_ER_Inventada",
                    "--out", str(destino), check=0)
    assert "DEM_ER_Inventada" in p.stdout
    v = json.loads(destino.read_text(encoding="utf-8"))
    assert v["entorno"] == "https://demo.appiancloud.com" and v["aplicacion"]["prefijo"] == "DEM"
    assert v["conHistorialDeVersiones"] is True and v["conCasosDePrueba"] is True
    solicitud, regla, falta = v["objetos"]
    assert (solicitud["existe"], solicitud["tipo"], solicitud["nombre"]) == (True, "recordType", "DEM Solicitud")
    assert {"nombre": "titulo", "tipo": "TEXT", "longitud": 255} in solicitud["campos"]
    assert {"nombre": "id", "tipo": "INTEGER", "clavePrimaria": True} in solicitud["campos"]
    assert solicitud["ultimaModificacion"] == {"fecha": "2026-09-01T10:00:00Z", "autor": "marta.ruiz", "versiones": 3}
    assert (regla["pedido"], regla["nombre"], regla["tipo"]) == ("dem_er_esadmin", "DEM_ER_EsAdmin", "expressionRule")
    assert "campos" not in regla and regla["casosDePrueba"][0]["name"].startswith("DEM_ER_EsAdmin")
    assert falta == {"pedido": "DEM_ER_Inventada", "existe": False} and v["faltan"] == ["DEM_ER_Inventada"]
    assert not project.out.exists()                                 # no escribe en ninguna extracción
    # @fichero, uno por línea; sin casos de prueba en el Dev MCP, no hay casos
    project.add_devmcp()
    lista = tmp_path / "objetos.txt"
    lista.write_text("# los de EV-02\nDEM Estado\n\n", encoding="utf-8")
    project.run("verificar", "--app", "DEM", "--objetos", f"@{lista}", "--out", str(destino), check=0)
    v = json.loads(destino.read_text(encoding="utf-8"))
    assert [o["nombre"] for o in v["objetos"]] == ["DEM Estado"] and v["conCasosDePrueba"] is False
    assert [c["nombre"] for c in v["objetos"][0]["campos"]] == ["id", "label"]


def test_verificar_sin_conexion(project, tmp_path):
    p = project.run("verificar", "--app", "DEM", "--objetos", "DEM Solicitud", "--out", str(tmp_path / "v.json"), check=2)
    assert "Dev MCP" in p.stderr and not (tmp_path / "v.json").exists()


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
    n = len(project.calls_list())
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
    assert any((d["tool"], d["type"]) == ("validateDesignObject", "constant") for d in rep["disabledAfterProbe"])
    extrae(project, "--solo", "DEM_Nada", check=2)
    extrae(project, "--solo", "DEM_Dashboard", "--refresh", check=2)


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
