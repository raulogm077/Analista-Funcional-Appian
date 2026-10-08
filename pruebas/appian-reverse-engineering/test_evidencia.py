"""Disciplina de evidencia: lo que no se pudo verificar queda registrado (NV) con lo que hace falta para resolverlo,
nada se da por inexistente sin decir dónde se buscó, la definición no se toma por la ejecución y la revisión cierra las
preguntas con las que empezó.

Con el simulador del Dev MCP (variante A) y, en test_fuera_de_la_aplicacion, con la aplicación ficticia MNT
(MOCK_APP=fixture_mal_hecha), que llama a tres reglas de otra aplicación (prefijo CMN) que no están en la extracción.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import BUILD_MODEL, BUILD_SUMMARY, SKILL, Project, extraccion_a_mano

sys.path.insert(0, str(SKILL / "scripts"))
from rutas import work_dir  # noqa: E402

SCRIPTS = SKILL / "scripts"
BUILD_ANNEX = SCRIPTS / "build_annex.py"
REGISTRO = SCRIPTS / "build_registry.py"
DATOS = SCRIPTS / "build_datos.py"
COMPROBAR = SCRIPTS / "comprobar_asis.py"
AZUL = "\U0001F535"                                   # la marca de inferido de antes; hoy es 🔶, la del analista
MNT = {"MOCK_APP": "fixture_mal_hecha", "LCP_URL": "https://pre.mnt.example.org"}
CMN = {"CMN_FormatearFecha": "MNT_IF_FormularioOrden", "CMN_UsuarioActual": "MNT_PM_GestionOrden",
       "CMN_IF_Cabecera": "MNT_IF_Panel"}             # regla de otra aplicación → quién la llama en MNT
CAMPOS_NV = {"id", "pregunta", "porQue", "queHaceFalta", "aQuien", "dondeSeBusco", "objetos", "indicios", "estado",
             "documento"}
PREGUNTAS = ["¿Qué hace la aplicación?", "¿Cómo está hecha?", "¿Qué riesgos tiene?"]
LEEME = ("# DEM Gestión de Solicitudes: documentación de ingeniería inversa\n\n## Sin verificar\n\n"
         "<!-- sin-verificar:inicio -->\n(lo rellena build_datos.py)\n<!-- sin-verificar:fin -->\n\n"
         "## Qué no incluye\n\n- Valores de otros entornos.\n")
OBJETOS = [("DEM Solicitud", "recordType", "full"), ("DEM_SolicitudDTO", "cdt", "none"),
           ("DEM_SolicitudForm", "interface", "full")]


# ---------------------------------------------------------------- utilidades

def corre(script, salida, check=0):
    p = subprocess.run([sys.executable, str(script), str(salida)], capture_output=True, text=True, encoding="utf-8")
    if check is not None:
        assert p.returncode == check, p.stdout + p.stderr
    return p


def comprueba(salida: Path):
    p = corre(COMPROBAR, salida, check=None)
    assert p.returncode in (0, 1), p.stdout + p.stderr
    errores = [l for l in p.stdout.splitlines() if l.startswith("✗")]
    assert p.returncode == (1 if errores else 0), p.stdout
    return errores, [l for l in p.stdout.splitlines() if l.startswith("·")]


def escribe(ruta: Path, datos) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(datos if isinstance(datos, str) else json.dumps(datos, ensure_ascii=False), encoding="utf-8")


def nv(id_="NV-ARQ-01", **kw) -> dict:
    return {"id": id_, "pregunta": "¿Qué hace UTL_DiasLaborables?",
            "porQue": "La llama DEM_SolicitudForm y no está en la aplicación.",
            "queHaceFalta": "Export de la aplicación que la contiene", "aQuien": "Equipo de la aplicación de utilidades",
            "dondeSeBusco": "Inventario de la aplicación y dependencias del Dev MCP",
            "objetos": ["DEM_SolicitudForm", "UTL_DiasLaborables"], "indicios": "Calcula el plazo de la solicitud.",
            "estado": "abierto", "documento": "02-arquitectura.md#dependencias-externas", **kw}


def hallazgo(id_="H-ARQ-01", **kw) -> dict:
    return {"id": id_, "titulo": "Tres objetos sin referencias entrantes", "area": "arquitectura", "severidad": "Alta",
            "certeza": "verificado", "objetos": ["DEM Solicitud"], "documento": "02-arquitectura.md#hallazgos",
            "evidencia": "graph:orphans", **kw}


def as_is(base: Path, docs: dict, nvs=(), preguntas=None, hallazgos=(), fuera=()) -> Path:
    """Una carpeta as-is mínima: datos/ (inventario, sin verificar, hallazgos y dependencias), el inventario y el
    resumen de la extracción, las preguntas de la revisión si se pasan y los documentos."""
    salida = base / "as-is"
    escribe(salida / "datos" / "inventario.json", {
        "aplicacion": {"nombre": "DEM Gestión de Solicitudes", "prefijo": "DEM", "uuid": "u-app"},
        "objetos": [{"nombre": n, "tipo": t, "uuid": f"u-{i}", "anexo": None, "tambien": []}
                    for i, (n, t, _d) in enumerate(OBJETOS)]})
    escribe(salida / "datos" / "sin-verificar.json", {"sinVerificar": list(nvs)})
    escribe(salida / "datos" / "hallazgos.json", {"hallazgos": list(hallazgos)})
    escribe(salida / "datos" / "dependencias.json", {"aristas": [], "fueraDeLaAplicacion": list(fuera)})
    trabajo = work_dir(salida)
    escribe(trabajo / "summary.json", {"counts": {}, "totals": {"objects": len(OBJETOS)}})
    escribe(trabajo / "inventory.json", {"objects": {t: [{"name": n, "type": t, "detail": d}]
                                                     for n, t, d in OBJETOS}})
    if preguntas is not None:
        escribe(trabajo / "output_preferences.json", {"pdf": False, "dashboard": False, "preguntas": preguntas})
    for rel, texto in docs.items():
        escribe(salida / rel, texto)
    return salida


def leeme(filas: list[str]) -> str:
    """LEEME con la tabla «Preguntas de esta revisión» (una fila por elemento: «pregunta | estado | dónde»)."""
    return ("# Guía\n\n## Preguntas de esta revisión\n\n| Pregunta | Estado | Dónde se responde |\n|---|---|---|\n"
            + "".join(f"| {f} |\n" for f in filas) + "\n## Sin verificar\n\n## Qué no incluye\n\n- Valores de otros entornos.\n")


DOCS = {"01-funcional.md": "# Funcional\n", "02-arquitectura.md": "# Arquitectura\n",
        "09-valor-adicional.md": "# Valor adicional\n"}


# ---------------------------------------------------------------- lo que no se pudo verificar (NV)

def flujo_dem(project: Project) -> Path:
    """Del simulador (DEM, variante A) a la salida: extracción, modelo, anexo, registro sin hallazgos, resumen, 02 y
    un LEEME con los marcadores de «Sin verificar»."""
    project.add_devmcp()
    project.run("extract", "--app", "DEM", "--out", str(project.out), "--retry-delay", "0.1", check=0)
    for script in (BUILD_MODEL, BUILD_ANNEX):
        corre(script, project.out)
    escribe(project.interm() / "hallazgos" / "orquestador.json", [])
    corre(REGISTRO, project.out)
    corre(BUILD_SUMMARY, project.out)
    escribe(project.out / "02-arquitectura.md", "# Arquitectura\n\n## Dependencias externas\n")
    escribe(project.out / "LEEME.md", LEEME)
    return project.out


def test_sin_verificar_formato(project):
    """Un NV de sin-verificar/ llega validado a datos/sin-verificar.json (sin los duplicados) y a la tabla de LEEME;
    con un id, un estado o un «qué hace falta» fuera de formato, build_datos.py da error y no toca nada."""
    salida = flujo_dem(project)
    prueba = project.interm() / "sin-verificar" / "prueba.json"
    solo_dem = {"objetos": ["DEM_SolicitudForm"]}            # en DEM no hay ningún objeto de fuera de la aplicación
    escribe(prueba, [nv(**solo_dem), nv("NV-ARQ-02", duplicadoDe="NV-ARQ-01", **solo_dem)])
    corre(DATOS, salida)
    datos = json.loads((salida / "datos" / "sin-verificar.json").read_text(encoding="utf-8"))
    assert [n["id"] for n in datos["sinVerificar"]] == ["NV-ARQ-01"]                  # sin el duplicado
    assert set(datos["sinVerificar"][0]) == CAMPOS_NV
    texto = (salida / "LEEME.md").read_text(encoding="utf-8")
    assert ("<!-- sin-verificar:inicio -->\n| ID | Pregunta | Qué hace falta | A quién | Estado |\n|---|---|---|---|---|\n"
            "| [NV-ARQ-01](./02-arquitectura.md#dependencias-externas) | ¿Qué hace UTL_DiasLaborables? "
            "| Export de la aplicación que la contiene | Equipo de la aplicación de utilidades | Abierto |\n"
            "<!-- sin-verificar:fin -->") in texto
    assert "NV-ARQ-02" not in texto and "(lo rellena" not in texto and "## Qué no incluye" in texto
    corre(DATOS, salida)
    assert (salida / "LEEME.md").read_text(encoding="utf-8") == texto              # idempotente
    assert comprueba(salida)[0] == []
    for malo, dice in ((nv("PV-ARQ-01"), "PV-ARQ-01"), (nv(estado="pendiente"), "pendiente"),
                       (nv(queHaceFalta="Preguntar al equipo"), "queHaceFalta"), (nv(objetos="DEM_SolicitudForm"), "objetos")):
        escribe(prueba, [malo])
        p = corre(DATOS, salida, check=1)
        assert dice in p.stderr, p.stderr
    assert (salida / "LEEME.md").read_text(encoding="utf-8") == texto              # con errores no toca LEEME
    assert json.loads((salida / "datos" / "sin-verificar.json").read_text(encoding="utf-8")) == datos


def test_nv_inexistente(tmp_path):
    """Un NV citado en un entregable tiene que estar en datos/sin-verificar.json."""
    texto = ("# Arquitectura\n\nQué hace `UTL_DiasLaborables`: ❓ ([NV-ARQ-01](./LEEME.md#sin-verificar)).\n\n"
             "Su versión: ❓ (NV-ARQ-02).\n")
    errores, _ = comprueba(as_is(tmp_path, {"02-arquitectura.md": texto, "LEEME.md": "# Guía\n\n## Sin verificar\n"},
                                 nvs=[nv()]))
    assert len(errores) == 1 and "02-arquitectura.md:5" in errores[0] and "NV-ARQ-02" in errores[0], errores


def test_pregunta_sin_cerrar(tmp_path):
    """Cada pregunta de la revisión lleva su estado; Parcial o Sin resolver, su NV o el enlace a «Qué no incluye»."""
    filas = ["¿Qué hace la aplicación? | Respondida | [01](./01-funcional.md)",
             "¿Cómo está hecha? |  | [02](./02-arquitectura.md)",                                  # sin estado
             "¿Qué riesgos tiene? | Parcial | [09](./09-valor-adicional.md)"]                     # sin NV ni límite
    errores, _ = comprueba(as_is(tmp_path / "a", {**DOCS, "LEEME.md": leeme(filas)}, nvs=[nv()], preguntas=PREGUNTAS))
    assert len(errores) == 2 and "¿Cómo está hecha?" in errores[0] and "¿Qué riesgos tiene?" in errores[1], errores
    filas[1] = "¿Cómo está hecha? | Sin resolver | NV-ARQ-01"
    filas[2] = "¿Qué riesgos tiene? | Parcial | [09](./09-valor-adicional.md) · [Qué no incluye](#qué-no-incluye)"
    assert comprueba(as_is(tmp_path / "b", {**DOCS, "LEEME.md": leeme(filas)}, nvs=[nv()], preguntas=PREGUNTAS)) == ([], [])


def test_pregunta_que_falta(tmp_path):
    """Una pregunta de la revisión que no está en la tabla de LEEME es un error (se compara sin tildes ni mayúsculas)."""
    filas = ["¿que hace la aplicacion? | Respondida | [01](./01-funcional.md)",
             "¿Cómo está hecha? | Respondida | [02](./02-arquitectura.md)"]
    errores, _ = comprueba(as_is(tmp_path, {**DOCS, "LEEME.md": leeme(filas)}, preguntas=PREGUNTAS))
    assert len(errores) == 1 and "¿Qué riesgos tiene?" in errores[0], errores


# ---------------------------------------------------------------- dónde se buscó y de dónde sale

def test_negativo_sin_ambito(tmp_path):
    """«No existe» en un entregable es un aviso (di dónde se buscó); en el anexo, que es la definición, no."""
    texto = ("# Arquitectura\n\nLa regla `UTL_DiasLaborables` no existe.\n\nNo hay ningún plug-in.\n\n"
             "`UTL_Otra`: no encontrada en la aplicación.\n")
    salida = as_is(tmp_path, {"02-arquitectura.md": texto,
                              "anexo/interface/DEM_SolicitudForm.md": "# DEM_SolicitudForm\n\nEl campo no existe.\n"})
    errores, avisos = comprueba(salida)
    assert errores == []
    negativos = [a.split()[1] for a in avisos if "dónde se buscó" in a]
    assert negativos == ["02-arquitectura.md:3", "02-arquitectura.md:5"], avisos


def test_segun_su_nombre_con_definicion(tmp_path):
    """«Según su nombre» en INVENTARIO solo vale para un objeto sin definición: si la tiene, el «Para qué» sale de ella."""
    inventario = ("# Inventario\n\n## Record types\n\n| Nombre | uuid | Para qué | Ficha |\n|---|---|---|---|\n"
                  "| [`DEM Solicitud`](./03-modelo-datos.md) | `u-0` | 🔶 según su nombre, las solicitudes | — |\n\n"
                  "## CDTs\n\n| Nombre | uuid | Para qué | Ficha |\n|---|---|---|---|\n"
                  "| `DEM_SolicitudDTO` | `u-1` | 🔶 según su nombre, los datos de una solicitud | — |\n")
    errores, avisos = comprueba(as_is(tmp_path, {"INVENTARIO.md": inventario, "03-modelo-datos.md": "# Datos\n"}))
    assert errores == []
    nombre = [a for a in avisos if "según su nombre" in a]
    assert len(nombre) == 1 and "INVENTARIO.md:7" in nombre[0] and "DEM Solicitud" in nombre[0], avisos


@pytest.fixture(scope="module")
def mnt(tmp_path_factory):
    """MNT (variante A) hasta datos/: extracción, modelo, anexo, registro sin hallazgos, resumen y datos."""
    p = Project(tmp_path_factory.mktemp("mnt"))
    p.add_devmcp(mode="readonly", **MNT)
    p.run("extract", "--app", "MNT", "--out", str(p.out), "--retry-delay", "0.1", check=0)
    for script in (BUILD_MODEL, BUILD_ANNEX):
        corre(script, p.out)
    escribe(p.interm() / "hallazgos" / "orquestador.json", [])
    for script in (REGISTRO, BUILD_SUMMARY, DATOS):
        corre(script, p.out)
    return p


def test_fuera_de_la_aplicacion(mnt):
    """Las tres reglas CMN que llama MNT y no están en la extracción son nodos externos del grafo, sin uuid, y salen
    en fueraDeLaAplicacion con quién las usa. Sin un NV que las tenga en «objetos», dan aviso; con él, no."""
    grafo = mnt.load("graph.json")
    externos = {n["name"]: n for n in grafo["nodes"] if n.get("external")}
    assert set(externos) == set(CMN) and grafo["stats"]["externalNodes"] == 3
    assert all(n["id"] == f"rule!{nombre}" and n["type"] == "llamado con rule!" for nombre, n in externos.items())
    dependencias = mnt.out / "datos" / "dependencias.json"
    fuera = {f["nombre"]: f for f in json.loads(dependencias.read_text(encoding="utf-8"))["fueraDeLaAplicacion"]}
    assert set(fuera) == set(CMN)
    for regla, quien in CMN.items():
        assert set(fuera[regla]) == {"nombre", "tipo", "usadoPor", "usa", "nv"}
        assert quien in fuera[regla]["usadoPor"] and fuera[regla]["nv"] is None, fuera[regla]
    _, avisos = comprueba(mnt.out)
    assert all(any(regla in a and "NV" in a for a in avisos) for regla in CMN), avisos
    escribe(mnt.out / "02-arquitectura.md", "# Arquitectura\n\n## Dependencias externas\n")
    escribe(mnt.interm() / "sin-verificar" / "interface-analyzer.json", [nv(
        pregunta="¿Qué hacen las reglas CMN que llama la aplicación?", objetos=[*CMN.values(), *CMN])])
    corre(DATOS, mnt.out)
    fuera = json.loads(dependencias.read_text(encoding="utf-8"))["fueraDeLaAplicacion"]
    assert {f["nombre"]: f["nv"] for f in fuera} == {regla: "NV-ARQ-01" for regla in CMN}
    _, avisos = comprueba(mnt.out)
    assert not any(regla in a for regla in CMN for a in avisos), avisos


def test_externo_unido_por_nombre(tmp_path):
    """Un rule! de fuera que una herramienta de dependencias ya trajo con uuid es un solo nodo, con el tipo canónico
    de esa herramienta; un cons! de fuera, un nodo sin uuid de tipo constante."""
    form = {"type": "interface", "uuid": "u-form-0001", "name": "DEM_SolicitudForm", "respuestas": {
        "definition": {"name": "DEM_SolicitudForm",
                       "expression": "=a!formLayout(contents: {a!textField(value: rule!UTL_DiasLaborables(fecha: today())),"
                                     " a!linkField(links: a!safeLink(uri: cons!UTL_URL_AYUDA))})"},
        "dependencies": {"dependencies": [{"uuid": "u-utl-0001", "name": "UTL_DiasLaborables", "type": "FREEFORM_RULE"}]}}}
    salida = extraccion_a_mano(tmp_path / "as-is", [form])
    corre(BUILD_MODEL, salida)
    grafo = json.loads((work_dir(salida) / "graph.json").read_text(encoding="utf-8"))
    externos = {n["name"]: n for n in grafo["nodes"] if n.get("external")}
    assert externos == {
        "UTL_DiasLaborables": {"id": "u-utl-0001", "type": "expressionRule", "name": "UTL_DiasLaborables", "external": True},
        "UTL_URL_AYUDA": {"id": "cons!UTL_URL_AYUDA", "type": "constant", "name": "UTL_URL_AYUDA", "external": True}}
    aristas = {(e["source"], e["target"], e["refType"]) for e in grafo["edges"]}
    assert {("u-form-0001", "u-utl-0001", "ruleRef"), ("u-form-0001", "cons!UTL_URL_AYUDA", "constRef")} <= aristas


def test_base_en_inferidos(tmp_path):
    """Un hallazgo inferido dice en «base» de qué evidencias sale: sin ella, error; Alta con una sola, aviso."""
    salida = tmp_path / "as-is"
    escribe(salida / "02-arquitectura.md", "# Arquitectura\n\n## Hallazgos\n")
    fichero = work_dir(salida) / "hallazgos" / "interface-analyzer.json"

    def registra(**kw):
        escribe(fichero, [hallazgo(**kw)])
        return corre(REGISTRO, salida, check=None)

    p = registra(certeza="inferido")
    assert p.returncode == 1 and "H-ARQ-01" in p.stderr and "base" in p.stderr, p.stderr
    una, dos = ["graph:orphans"], ["graph:orphans", "mcp:processModel/DEM Utilidad Huérfana@history#totalCount"]
    p = registra(certeza="inferido", base=una)
    assert p.returncode == 0 and [l for l in p.stderr.splitlines() if l.startswith("AVISO") and "base" in l], p.stderr
    for kw in ({"base": dos}, {"base": una, "severidad": "Media"}):
        p = registra(certeza="inferido", **kw)
        assert p.returncode == 0 and "AVISO" not in p.stderr, p.stderr
    # comprobar_asis.py lo mira en datos/hallazgos.json, que es lo que leen las demás skills
    for n, base in ((1, una), (0, dos)):
        _, avisos = comprueba(as_is(tmp_path / str(n), {}, hallazgos=[hallazgo(certeza="inferido", base=base)]))
        assert len([a for a in avisos if "H-ARQ-01" in a and "base" in a]) == n, avisos


def test_marca_de_inferido(tmp_path):
    """La marca de inferido es 🔶, la del analista: la de antes (AZUL) no está en la skill, y los JSON siguen diciendo
    «inferido»."""
    azules = [f"{p.relative_to(SKILL)}:{n}" for p in sorted(SKILL.rglob("*"))
              if p.is_file() and p.suffix in (".md", ".py", ".json", ".sh")
              for n, l in enumerate(p.read_text(encoding="utf-8").splitlines(), 1) if AZUL in l]
    assert azules == []
    salida = tmp_path / "as-is"
    escribe(salida / "02-arquitectura.md", "# Arquitectura\n\n## Hallazgos\n")
    escribe(salida / "09-valor-adicional.md", "# Valor adicional\n\n<!-- registro:inicio -->\n<!-- registro:fin -->\n")
    trabajo = work_dir(salida)
    escribe(trabajo / "hallazgos" / "interface-analyzer.json",
            [hallazgo(certeza="inferido", severidad="Media", base=["graph:orphans"])])
    corre(REGISTRO, salida)
    registro = json.loads((trabajo / "registro.json").read_text(encoding="utf-8"))
    assert registro["hallazgos"][0]["certeza"] == "inferido" and registro["porCerteza"]["inferido"] == 1
    assert ("| H-ARQ-01 | Tres objetos sin referencias entrantes | arquitectura | Media | 🔶 |"
            in (salida / "09-valor-adicional.md").read_text(encoding="utf-8"))
    escribe(trabajo / "inventory.json", {"objects": {"application": [{"name": "DEM", "prefix": "DEM", "uuid": "u"}],
                                                      "recordType": [{"name": "DEM Solicitud", "type": "recordType",
                                                                      "uuid": "u-1"}]}})
    corre(DATOS, salida)
    datos = json.loads((salida / "datos" / "hallazgos.json").read_text(encoding="utf-8"))["hallazgos"]
    assert [(h["certeza"], h["base"]) for h in datos] == [("inferido", ["graph:orphans"])]
