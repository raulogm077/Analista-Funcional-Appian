"""La extracción vive en el proyecto, en <salida>/extraccion (D4), tal cual la devuelve el Dev MCP y con rutas cortas.

Tal cual: se trabaja en entornos controlados y no se oculta nada, ni usuarios, ni datos de la aplicación, ni secretos.
Rutas cortas, para que el proyecto quepa en Windows y en OneDrive.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from conftest import BUILD_MODEL, SKILL, extraccion_a_mano

sys.path.insert(0, str(SKILL / "scripts"))
sys.path.insert(0, str(Path(__file__).parent / "mock_devmcp"))
import devmcp_extract as dx  # noqa: E402
import fixture  # noqa: E402
import rutas  # noqa: E402

OBJS, _, _ = fixture.build()
BUILD_ANNEX = SKILL / "scripts" / "build_annex.py"
USUARIOS = sorted({u for us in fixture.GROUP_USERS.values() for u in us})
CORREO = "soporte.dem@example.org"                  # en copia del aviso de DEM Revisar Solicitud
CLAVE_DE_API = OBJS["C_TOKEN"]["value"]             # el valor de la constante DEM_ERP_API_TOKEN
URL_CON_CREDENCIALES = OBJS["CS_ERP"]["baseUrl"]    # la URL base de DEM_CS_ERP, con usuario y contraseña
CON_ESPACIOS = ("Carpeta con espacios", "Gestión app", "as-is")
TOPE_NOMBRE = len(dx.safe_name("x" * 200))         # 48: el nombre de una herramienta en la extracción
# lo que ningún texto de la skill pide: ocultar usuarios, correos, valores o secretos
OCULTAR = re.compile(r"(?i)seud[oó]nim|‹usuario|‹correo›|‹secreto›|‹valor›|‹nombre›|host interno|sin usuarios|"
                     r"no se comparte|_huellas|enmascar")


def env_of(url: str) -> str:
    """URL del entorno (LCP_URL) cuyo Appian MCP Server es `url` (<entorno>/mcp)."""
    return url.rsplit("/mcp", 1)[0]


def extrae(project, *extra, check=0):
    return project.run("extract", "--app", "DEM", "--out", str(project.out), "--retry-delay", "0.1", *extra,
                       check=check)


def modelo(project):
    p = subprocess.run([sys.executable, str(BUILD_MODEL), str(project.out)], capture_output=True, text=True,
                       encoding="utf-8")
    assert p.returncode == 0, p.stderr


def con_mcp_server(project, http_server):
    """Dev MCP y Appian MCP Server del mismo entorno: doctor y datafabric también escriben en la extracción."""
    project.add_devmcp(LCP_URL=env_of(http_server))
    project.add_http("appian-mcp", http_server, {"Authorization": "Bearer dummy"})


def textos(carpeta: Path) -> str:
    return "\n".join(f.read_text(encoding="utf-8") for f in sorted(carpeta.rglob("*")) if f.is_file())


# ---------------------------------------------------------------- comprobaciones

def dentro_del_proyecto(project):
    extraccion = project.out / "extraccion"
    assert project.interm() == extraccion and (extraccion / "mcp_raw" / "_objects.json").exists()
    # fuera de <salida>, solo lo que pone la prueba: la configuración MCP y el registro de llamadas del simulador
    fuera = sorted(f.relative_to(project.base).as_posix() for f in project.base.rglob("*")
                   if f.is_file() and project.out not in f.parents)
    assert fuera == ["calls.jsonl", "proj/.mcp.json"], fuera
    assert {p.name for p in project.base.iterdir()} == {"proj", "home", "calls.jsonl",
                                                       project.out.relative_to(project.base).parts[0]}
    assert not any(project.home.iterdir())                       # la carpeta home/ del conftest sigue vacía
    assert not list(project.base.rglob("_trabajo")) and not list(project.base.rglob(".gitignore"))


def rutas_cortas(project):
    extraccion = project.interm()
    largas = [r for r in (f.relative_to(extraccion).as_posix() for f in extraccion.rglob("*") if f.is_file())
              if len(r) > 100]
    assert not largas, largas


def modelo_sin_fecha(project):
    inv = project.load("inventory.json")
    inv["source"].pop("extractedAt")
    return inv, project.load("graph.json")


def envejece(project, fecha="2026-01-02T03:04:05+00:00"):
    """Las respuestas guardadas pasan a ser de `fecha`, como si se hubieran descargado hace tiempo."""
    for f in (project.interm() / "mcp_raw").rglob("*.json"):
        d = json.loads(f.read_text(encoding="utf-8"))
        if isinstance(d, dict) and isinstance(d.get("_meta"), dict):
            d["_meta"]["fetchedAt"] = fecha
            f.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")


def retomar(project):
    assert "--refresh" not in extrae(project).stdout
    modelo(project)
    antes, llamadas = modelo_sin_fecha(project), len(project.calls_list())
    assert "--refresh" not in extrae(project).stdout              # recién descargado: no avisa
    envejece(project)
    p = extrae(project)
    assert len(project.calls_list()) == llamadas                 # no vuelve a pedir lo que ya está
    assert "--refresh" in p.stdout and "2026-01-02 03:04" in p.stdout   # y avisa, con la fecha, de lo que reutiliza
    modelo(project)
    assert modelo_sin_fecha(project) == antes                    # y el modelo sale igual


# ---------------------------------------------------------------- pruebas

def test_extraccion_dentro_del_proyecto(project):
    project.add_devmcp()
    extrae(project)
    dentro_del_proyecto(project)


def test_tal_cual(project):
    """Nada se oculta: los usuarios, un correo y los secretos están en la extracción y en el anexo tal como los
    devuelve el Dev MCP."""
    project.add_devmcp()
    extrae(project)
    modelo(project)
    p = subprocess.run([sys.executable, str(BUILD_ANNEX), str(project.out)], capture_output=True, text=True,
                       encoding="utf-8")
    assert p.returncode == 0, p.stderr
    extraccion, anexo = textos(project.interm()), textos(project.out / "anexo")
    for valor in (*USUARIOS, CORREO, CLAVE_DE_API, URL_CON_CREDENCIALES):
        assert valor in extraccion, ("extraccion", valor)
        assert valor in anexo, ("anexo", valor)


def test_sin_ocultar():
    """Ningún texto de la skill pide ocultar usuarios, correos, valores o secretos."""
    malos = [f"{p.relative_to(SKILL)}:{n}" for p in sorted(SKILL.rglob("*"))
             if p.is_file() and p.suffix in (".md", ".py", ".json", ".sh")
             for n, linea in enumerate(p.read_text(encoding="utf-8").splitlines(), 1) if OCULTAR.search(linea)]
    assert malos == []


def test_rutas_cortas(project):
    project.add_devmcp(MOCK_EXTRA_TOOLS=1)       # también la herramienta nueva, que se llama en todos los objetos
    extrae(project)
    modelo(project)
    rutas_cortas(project)


def test_retomar(project):
    project.add_devmcp()
    retomar(project)


def test_ruta_con_espacios(project, http_server):
    project.out = project.base.joinpath(*CON_ESPACIOS)
    con_mcp_server(project, http_server)
    project.run("doctor", "--json", "--out", str(project.out), check=0)
    retomar(project)
    project.run("datafabric", "--out", str(project.out), check=0)
    dentro_del_proyecto(project)
    rutas_cortas(project)


def test_otra_aplicacion_en_la_misma_carpeta(project):
    """Una carpeta, una aplicación: con otra, las respuestas guardadas serían las de la primera."""
    project.add_devmcp()
    extrae(project)
    p = project.run("plan", "--app", "Otra", "--out", str(project.out), check=15)
    assert "usa otra carpeta" in p.stderr


def test_retomar_en_otro_entorno(project):
    """Una aplicación conserva su uuid en DEV, PRE y PRO: una carpeta, un entorno, salvo con --refresh."""
    project.add_devmcp(LCP_URL="https://desarrollo.example.com")
    extrae(project)
    project.add_devmcp(LCP_URL="https://produccion.example.com/")
    llamadas = len(project.calls_list())
    p = extrae(project, check=15)
    assert "https://desarrollo.example.com" in p.stderr and "--refresh" in p.stderr
    assert len(project.calls_list()) == llamadas                 # no llama al otro entorno
    extrae(project, "--refresh")
    assert len(project.calls_list()) > llamadas                  # lo pide todo de nuevo
    assert project.load("mcp_raw/_objects.json")["entorno"] == "https://produccion.example.com"
    llamadas = len(project.calls_list())
    extrae(project)                                              # ya es de producción: se retoma
    assert len(project.calls_list()) == llamadas


def test_rutas_cortas_con_tipo_largo(tmp_path):
    raw = tmp_path / "extraccion" / "mcp_raw"
    uuid = OBJS["PM_ALTA"]["uuid"]
    largo = "translationSetStringRecordTypeRelationshipFolder"   # un tipo largo del catálogo
    carpeta = rutas.carpeta_objeto(raw, largo, uuid)
    assert len((carpeta / f"{dx.safe_name('getDesignObject' * 10)}.json").relative_to(raw.parent).as_posix()) <= 100
    assert carpeta != rutas.carpeta_objeto(raw, largo + "Item", uuid)          # dos tipos largos no se pisan
    assert rutas.carpeta_objeto(raw, "processModel", uuid).parent.name == "processModel"   # los habituales, igual


def test_rutas_cortas_con_nombre_largo(tmp_path):
    """El slug de un objeto nombra extraccion/procesos/<slug>.json, anexo/<tipo>/<slug>.md y 08-procesos-bpmn/<slug>.*:
    con un nombre de 150 caracteres, se recorta como el de una herramienta (48 y 8 hex), las rutas no pasan de 100
    caracteres y build_annex.py y build_datos.py siguen encontrando las fichas."""
    largo = ("DEM Proceso de alta, revisión y aprobación de solicitudes de mantenimiento correctivo " * 2)[:150]
    otro = largo[:-1] + "x"                                                    # solo cambia la última letra
    salida = extraccion_a_mano(tmp_path / "Carpeta con espacios" / "as-is", [
        {"type": "processModel", "uuid": f"u-pm-000{i}", "name": n,
         "respuestas": {"definition": {"name": n, "nodes": [{"id": 1, "type": "core.0", "name": "Inicio"}]}}}
        for i, n in enumerate((largo, otro))])
    for script in ("build_model.py", "build_annex.py"):
        p = subprocess.run([sys.executable, str(SKILL / "scripts" / script), str(salida)], capture_output=True,
                           text=True, encoding="utf-8")
        assert p.returncode == 0, p.stderr
    inventario = json.loads((rutas.work_dir(salida) / "inventory.json").read_text(encoding="utf-8"))
    slugs = [o["slug"] for o in inventario["objects"]["processModel"]]
    assert len(slugs) == 2 and len(set(slugs)) == 2 and all(len(s) <= TOPE_NOMBRE for s in slugs), slugs
    for slug in slugs:
        (salida / "08-procesos-bpmn").mkdir(exist_ok=True)
        (salida / "08-procesos-bpmn" / f"{slug}.json").write_text("{}", encoding="utf-8")   # lo escribe process-modeler
        rutas_slug = [f"extraccion/procesos/{slug}.json", f"anexo/processModel/{slug}.md",
                      *(f"08-procesos-bpmn/{slug}{ext}" for ext in (".drawio", ".bpmn", "-12.png", ".json"))]
        assert all(len(r) <= 100 for r in rutas_slug), rutas_slug
        assert (salida / "anexo" / "processModel" / f"{slug}.md").is_file()
    p = subprocess.run([sys.executable, str(SKILL / "scripts" / "build_datos.py"), str(salida)], capture_output=True,
                       text=True, encoding="utf-8")
    assert p.returncode == 0, p.stderr
    datos = salida / "datos"
    anexos = [o["anexo"] for o in json.loads((datos / "inventario.json").read_text(encoding="utf-8"))["objetos"]]
    assert sorted(anexos) == sorted(f"anexo/processModel/{s}.md" for s in slugs)
    jsons = [x["json"] for x in json.loads((datos / "procesos.json").read_text(encoding="utf-8"))["procesos"]]
    assert sorted(jsons) == sorted(f"08-procesos-bpmn/{s}.json" for s in slugs)

