"""Pruebas del registro único de hallazgos (build_registry.py) y su uso en build_summary.py."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from conftest import SKILL

sys.path.insert(0, str(SKILL / "scripts"))
from rutas import work_dir  # noqa: E402

REG = SKILL / "scripts" / "build_registry.py"
SUM = SKILL / "scripts" / "build_summary.py"


def setup(tmp_path: Path):
    out = tmp_path / "DEM" / "as-is"
    work = work_dir(out)
    (out / "08-procesos-bpmn").mkdir(parents=True)
    (work / "hallazgos").mkdir(parents=True)
    (out / "08-procesos-bpmn" / "DEM_Alta_Solicitud.md").write_text("# Alta\n## Hallazgos\n", encoding="utf-8")
    (out / "04-seguridad-grupos.md").write_text("# Seguridad\n", encoding="utf-8")
    (out / "09-valor-adicional.md").write_text("# 09\n\n## Registro de hallazgos\n\n<!-- registro:inicio -->\n"
                                               "(lo rellena build_registry.py)\n<!-- registro:fin -->\n\n## Glosario\n", encoding="utf-8")
    return out, work


def h(id_, **kw):
    base = {"id": id_, "titulo": "Cancelar no anula el alta", "area": "procesos", "severidad": "Alta",
            "certeza": "verificado", "documento": "08-procesos-bpmn/DEM_Alta_Solicitud.md#hallazgos",
            "evidencia": "mcp:processModel/DEM Alta Solicitud#nodes[id=1]"}
    base.update(kw)
    return base


def run(script, out):
    return subprocess.run([sys.executable, str(script), str(out)], capture_output=True, text=True, encoding="utf-8", errors="replace")


def test_registry_fills_09(tmp_path):
    out, work = setup(tmp_path)
    (work / "hallazgos" / "process-modeler.json").write_text(json.dumps([h("H-PRO-01")]), encoding="utf-8")
    (work / "hallazgos" / "integration-security-analyzer.json").write_text(json.dumps([
        h("H-SEG-01", titulo="Alta abierta a todos los usuarios", area="seguridad", severidad="Media",
          certeza="inferido", documento="04-seguridad-grupos.md#hallazgos", evidencia="mcp:processModel/X@other:roleMap",
          base=["mcp:processModel/X@other:roleMap", "mcp:group/DEM Users@members"]),
        h("H-SEG-02", titulo="Cancelar | no anula", duplicadoDe="H-PRO-01", documento="04-seguridad-grupos.md")]), encoding="utf-8")
    p = run(REG, out)
    assert p.returncode == 0, p.stderr
    t = (out / "09-valor-adicional.md").read_text(encoding="utf-8")
    assert "| ID | Hallazgo | Área | Severidad | Certeza | Dónde |\n|---|---|---|---|---|---|\n" in t
    assert ("| H-PRO-01 | Cancelar no anula el alta | procesos | Alta | ✅ "
            "| [08 DEM Alta Solicitud](./08-procesos-bpmn/DEM_Alta_Solicitud.md#hallazgos) |\n") in t
    assert "| H-SEG-01 | Alta abierta a todos los usuarios | seguridad | Media | 🔶 |" in t      # inferido: 🔶
    assert "| H-SEG-02 |" not in t and "H-SEG-02 → H-PRO-01" in t        # fusionado, no se repite
    assert t.index("H-PRO-01 |") < t.index("H-SEG-01 |")                 # Alta antes que Media
    assert "## Glosario" in t and "(lo rellena" not in t
    assert run(REG, out).returncode == 0 and (out / "09-valor-adicional.md").read_text(encoding="utf-8") == t   # idempotente
    reg = json.loads((work / "registro.json").read_text(encoding="utf-8"))
    assert set(reg) == {"hallazgos", "porSeveridad", "porCerteza", "retirados"} and reg["retirados"] == []
    assert reg["porSeveridad"] == {"Alta": 1, "Media": 1, "Baja": 0}
    assert reg["porCerteza"] == {"verificado": 1, "inferido": 1, "pendiente": 0}             # el JSON dice «inferido»
    assert next(x for x in reg["hallazgos"] if x["id"] == "H-SEG-01")["base"][1] == "mcp:group/DEM Users@members"
    # build_summary toma el registro (sin inventario: solo se comprueba la parte de hallazgos)
    (work / "inventory.json").write_text(json.dumps({"counts": {}, "objects": {}}), encoding="utf-8")
    p = run(SUM, out)
    assert p.returncode == 0, p.stderr
    s = json.loads((work / "summary.json").read_text(encoding="utf-8"))
    assert [f["id"] for f in s["findings"]] == ["H-PRO-01", "H-SEG-01"]
    assert "modernization" not in s and all("tratamiento" not in f for f in s["findings"])


def test_recomendacion_es_aviso(tmp_path):
    """Un hallazgo dice qué pasa y qué riesgo tiene, no qué hacer: una «recomendacion» se avisa y no para el registro."""
    out, work = setup(tmp_path)
    (work / "hallazgos" / "process-modeler.json").write_text(json.dumps([
        h("H-PRO-01", impacto="Una solicitud cancelada se registra igualmente.",
          recomendacion="Pasarela tras el inicio que compruebe la cancelación."),
        h("H-PRO-02", titulo="La pasarela no tiene salida por defecto", severidad="Media", recomendacion=""),
        h("H-PRO-03", titulo="Tarea sin asignación", severidad="Baja", impacto="Nadie la ve en su bandeja.")]), encoding="utf-8")
    p = run(REG, out)
    assert p.returncode == 0, p.stderr
    avisos = [l for l in p.stderr.splitlines() if l.startswith("AVISO")]
    assert len(avisos) == 1 and "H-PRO-01" in avisos[0] and "recomendacion" in avisos[0], p.stderr
    assert "| H-PRO-01 |" in (out / "09-valor-adicional.md").read_text(encoding="utf-8")


def test_senales_del_mismo_problema(tmp_path):
    """Un objeto, un problema, un hallazgo (T27): dos hallazgos vivos del mismo objeto con señales del mismo grupo
    (huerfano y sin-ejecuciones; mas-50-nodos y aviso-validacion-nodos) son un error; con duplicadoDe, no. Señales de
    grupos distintos, u otros objetos, tampoco."""
    out, work = setup(tmp_path)
    (out / "02-arquitectura.md").write_text("# Arquitectura\n", encoding="utf-8")
    huerfana = ["DEM Utilidad Huérfana"]
    fichero = work / "hallazgos" / "orquestador.json"

    def registra(*hs):
        fichero.write_text(json.dumps(list(hs)), encoding="utf-8")
        return run(REG, out)

    arq = h("H-ARQ-01", titulo="Objetos sin referencias entrantes", area="arquitectura", severidad="Baja",
            documento="02-arquitectura.md#hallazgos", objetos=["DEM_Otro", *huerfana], senal="huerfano")
    gen = h("H-PRO-01", titulo="Proceso sin ejecuciones", area="uso", severidad="Baja", objetos=huerfana,
            senal="sin-ejecuciones")
    p = registra(arq, gen)
    assert p.returncode == 1 and "H-ARQ-01" in p.stderr and "H-PRO-01" in p.stderr and "DEM Utilidad Huérfana" in p.stderr
    assert registra(arq, {**gen, "duplicadoDe": "H-ARQ-01"}).returncode == 0
    nodos = h("H-PRO-02", titulo="130 nodos", severidad="Media", objetos=["DEM Alta Solicitud"], senal="mas-50-nodos")
    aviso = h("H-PRO-03", titulo="Aviso de la validación", severidad="Baja", objetos=["DEM Alta Solicitud"],
              senal="aviso-validacion-nodos")
    p = registra(nodos, aviso)
    assert p.returncode == 1 and "H-PRO-02" in p.stderr and "H-PRO-03" in p.stderr, p.stderr
    assert registra(nodos, {**aviso, "objetos": ["DEM Revisar Solicitud"]}).returncode == 0
    assert registra(nodos, {**gen, "objetos": ["DEM Alta Solicitud"]}).returncode == 0      # grupos distintos
    p = registra({**nodos, "senal": ""})
    assert p.returncode == 1 and "senal" in p.stderr, p.stderr


def test_registry_rejects_bad_entries(tmp_path):
    out, work = setup(tmp_path)
    (work / "hallazgos" / "a.json").write_text(json.dumps([
        h("H-PRO-01"), h("H-PRO-01"), h("PRO-2"), h("H-PRO-03", severidad="🔴"), h("H-PRO-04", certeza="seguro"),
        h("H-PRO-05", documento="no-existe.md"), h("H-PRO-06", evidencia=""), h("H-PRO-07", duplicadoDe="H-XXX-99"),
        h("H-PRO-08", certeza="inferido")]), encoding="utf-8")
    p = run(REG, out)
    assert p.returncode == 1
    for frag in ("repetido", "no sigue H-", "severidad", "certeza", "no existe en la salida", "sin evidencia",
                 "duplicadoDe 'H-XXX-99'", "H-PRO-08: inferido sin base"):
        assert frag in p.stderr, frag
    assert "(lo rellena" in (out / "09-valor-adicional.md").read_text(encoding="utf-8")      # con errores no toca 09


# ---------------------------------------------------------------- IDs estables (correcciones de la revisión de G1)

def rehace(out, work, hallazgos=(), nvs=None, previos_nv=None):
    """El agente vuelve a escribir sus hallazgos (y NV) con otra numeración; build_registry.py los casa con el registro
    anterior. Devuelve la salida de build_registry y lo que queda en el JSON de hallazgos."""
    (work / "hallazgos" / "process-modeler.json").write_text(json.dumps(list(hallazgos), ensure_ascii=False),
                                                              encoding="utf-8")
    if nvs is not None:
        (work / "sin-verificar").mkdir(exist_ok=True)
        (work / "sin-verificar" / "process-modeler.json").write_text(json.dumps(nvs, ensure_ascii=False),
                                                                      encoding="utf-8")
    if previos_nv is not None:
        (out / "datos").mkdir(exist_ok=True)
        (out / "datos" / "sin-verificar.json").write_text(json.dumps({"sinVerificar": previos_nv}, ensure_ascii=False),
                                                          encoding="utf-8")
    p = run(REG, out)
    assert p.returncode == 0, p.stdout + p.stderr
    return p, json.loads((work / "hallazgos" / "process-modeler.json").read_text(encoding="utf-8"))


def nv(id_, pregunta, objetos):
    return {"id": id_, "pregunta": pregunta, "objetos": objetos}


def test_ids_estables_en_otro_orden(tmp_path):
    """Dos hallazgos del mismo proceso, sin señal, rehechos en el orden contrario: cada uno conserva su ID (mandan la
    clave y el título juntos, antes que el ID que el agente le puso). Igual con dos NV del mismo objeto."""
    out, work = setup(tmp_path)
    alta = ["DEM Alta Solicitud"]
    a = h("H-PRO-01", titulo="Cancelar no anula el alta", objetos=alta)
    b = h("H-PRO-02", titulo="La pasarela no tiene salida por defecto", objetos=alta)
    rehace(out, work, [a, b], [nv("NV-PRO-01", "¿Quién revisa?", alta), nv("NV-PRO-02", "¿Cuándo vence?", alta)])
    (out / "08-procesos-bpmn" / "DEM_Alta_Solicitud.md").write_text(
        "# Alta\n## Hallazgos\n\nH-PRO-01 (pasarela) y H-PRO-02 (cancelar); NV-PRO-01 (vence) y NV-PRO-02 (revisa).\n",
        encoding="utf-8")
    p, js = rehace(out, work, [{**b, "id": "H-PRO-01"}, {**a, "id": "H-PRO-02"}],
                   [nv("NV-PRO-01", "¿Cuándo vence?", alta), nv("NV-PRO-02", "¿Quién revisa?", alta)],
                   previos_nv=[nv("NV-PRO-01", "¿Quién revisa?", alta), nv("NV-PRO-02", "¿Cuándo vence?", alta)])
    assert {x["titulo"]: x["id"] for x in js} == {a["titulo"]: "H-PRO-01", b["titulo"]: "H-PRO-02"}, p.stdout
    nvs = json.loads((work / "sin-verificar" / "process-modeler.json").read_text(encoding="utf-8"))
    assert {x["pregunta"]: x["id"] for x in nvs} == {"¿Quién revisa?": "NV-PRO-01", "¿Cuándo vence?": "NV-PRO-02"}
    assert ("H-PRO-02 (pasarela) y H-PRO-01 (cancelar); NV-PRO-02 (vence) y NV-PRO-01 (revisa)."
            in (out / "08-procesos-bpmn" / "DEM_Alta_Solicitud.md").read_text(encoding="utf-8"))


def test_ids_estables_titulo_generico_y_objetos_cruzados(tmp_path):
    """Dos hallazgos con el mismo título genérico en procesos distintos, rehechos con los objetos cruzados: el ID va
    con el objeto, no con el título."""
    out, work = setup(tmp_path)
    titulo = "Tarea sin asignación"
    rehace(out, work, [h("H-PRO-01", titulo=titulo, objetos=["DEM Alta Solicitud"]),
                       h("H-PRO-02", titulo=titulo, objetos=["DEM Revisar Solicitud"])])
    _, js = rehace(out, work, [h("H-PRO-01", titulo=titulo, objetos=["DEM Revisar Solicitud"]),
                               h("H-PRO-02", titulo=titulo, objetos=["DEM Alta Solicitud"])])
    assert {x["objetos"][0]: x["id"] for x in js} == {"DEM Alta Solicitud": "H-PRO-01", "DEM Revisar Solicitud": "H-PRO-02"}


def test_ids_estables_senal_de_grupo_y_retirados(tmp_path):
    """Un hallazgo de una señal de grupo (huerfano, sin-prefijo) se casa por área y señal, porque sus objetos y sus
    cifras cambian. Un ID anterior que no se casa con ninguno queda en el registro como retirado (en registro.json y en
    09), también en las ejecuciones siguientes, y no se reutiliza."""
    out, work = setup(tmp_path)
    (out / "02-arquitectura.md").write_text("# Arquitectura\n", encoding="utf-8")
    huerfanos = h("H-ARQ-01", titulo="Tres objetos sin referencias entrantes", area="arquitectura",
                  documento="02-arquitectura.md#hallazgos", objetos=["DEM_A", "DEM_B", "DEM_C"], senal="huerfano")
    tarea = h("H-PRO-01", titulo="Tarea sin asignación", objetos=["DEM Revisar Solicitud"])
    rehace(out, work, [huerfanos, tarea])
    otra = h("H-PRO-01", titulo="La pasarela no tiene salida por defecto", objetos=["DEM Alta Solicitud"])
    p, js = rehace(out, work, [{**huerfanos, "id": "H-ARQ-02", "titulo": "Cuatro objetos sin referencias entrantes",
                                "objetos": ["DEM_A", "DEM_D", "DEM_E", "DEM_F"]}, otra])
    assert {x["titulo"]: x["id"] for x in js} == {"Cuatro objetos sin referencias entrantes": "H-ARQ-01",
                                                  otra["titulo"]: "H-PRO-02"}, p.stdout
    retirados = json.loads((work / "registro.json").read_text(encoding="utf-8"))["retirados"]
    assert [(r["id"], r["titulo"], r["objetos"]) for r in retirados] == [
        ("H-PRO-01", "Tarea sin asignación", ["DEM Revisar Solicitud"])]
    assert "H-PRO-01" in p.stdout and "retirad" in p.stdout
    t = (out / "09-valor-adicional.md").read_text(encoding="utf-8")
    assert "Retirados" in t and "H-PRO-01" in t.split("Retirados", 1)[1]
    run(REG, out)                                                    # de nuevo: sigue retirado
    assert json.loads((work / "registro.json").read_text(encoding="utf-8"))["retirados"] == retirados
    # si vuelve (un agente que faltaba), recupera su ID y deja de estar retirado
    _, js = rehace(out, work, [*js, {**tarea, "id": "H-PRO-09"}])
    assert {x["titulo"]: x["id"] for x in js}["Tarea sin asignación"] == "H-PRO-01"
    assert json.loads((work / "registro.json").read_text(encoding="utf-8"))["retirados"] == []
