"""as-is/datos/: lo que las demás skills leen de la ingeniería inversa (build_datos.py)."""
from __future__ import annotations

import json
import subprocess
import sys

from conftest import BUILD_MODEL, SKILL

BUILD_ANNEX = SKILL / "scripts" / "build_annex.py"
REGISTRO = SKILL / "scripts" / "build_registry.py"
RESUMEN = SKILL / "scripts" / "build_summary.py"
DATOS = SKILL / "scripts" / "build_datos.py"
CLAVES = {"inventario.json": {"aplicacion", "objetos"}, "dependencias.json": {"aristas", "fueraDeLaAplicacion"},
          "hallazgos.json": {"hallazgos"}, "procesos.json": {"procesos"}, "sin-verificar.json": {"sinVerificar"}}
CAMPOS = {"id", "titulo", "area", "severidad", "certeza", "objetos", "documento", "evidencia"}


def corre(script, salida):
    p = subprocess.run([sys.executable, str(script), str(salida)], capture_output=True, text=True, encoding="utf-8")
    assert p.returncode == 0, p.stderr
    return p


def hallazgo(id_, **kw):
    return {"id": id_, "titulo": "Token del ERP escrito en una constante", "area": "secretos", "severidad": "Alta",
            "certeza": "verificado", "objetos": ["DEM_ERP_API_TOKEN"], "documento": "04-seguridad-grupos.md#hallazgos",
            "evidencia": "mcp:constant/DEM_ERP_API_TOKEN#value", **kw}


def flujo(project):
    """El flujo con el simulador hasta datos/: extracción, modelo, anexo, hallazgos, registro, resumen y datos."""
    project.add_devmcp()
    project.run("extract", "--app", "DEM", "--out", str(project.out), "--retry-delay", "0.1", check=0)
    corre(BUILD_MODEL, project.out)
    corre(BUILD_ANNEX, project.out)
    (project.out / "04-seguridad-grupos.md").write_text("# Seguridad\n\n## Hallazgos\n", encoding="utf-8")
    carpeta = project.interm() / "hallazgos"
    carpeta.mkdir()
    (carpeta / "prueba.json").write_text(json.dumps(
        [hallazgo("H-SEG-01"), hallazgo("H-SEG-02", duplicadoDe="H-SEG-01"),
         hallazgo("H-SEG-03", titulo="Token del ERP en una cabecera", severidad="Media", certeza="inferido",
                  base=["mcp:constant/DEM_ERP_API_TOKEN#value", "mcp:integration/DEM_INT_NotificarERP#headers"])],
        ensure_ascii=False), encoding="utf-8")
    corre(REGISTRO, project.out)
    corre(RESUMEN, project.out)
    corre(DATOS, project.out)
    return project.out / "datos"


def test_datos_formato(project):
    datos = flujo(project)
    leidos = {n: json.loads((datos / n).read_text(encoding="utf-8")) for n in CLAVES}
    assert {n: set(d) for n, d in leidos.items()} == CLAVES
    inv = leidos["inventario.json"]
    assert set(inv["aplicacion"]) == {"nombre", "prefijo", "uuid"} and inv["aplicacion"]["prefijo"] == "DEM"
    assert inv["objetos"] and all(set(o) == {"nombre", "tipo", "uuid", "anexo", "tambien"} for o in inv["objetos"])
    assert all(o["anexo"] is None or (project.out / o["anexo"]).is_file() for o in inv["objetos"])
    aristas = leidos["dependencias.json"]["aristas"]
    assert aristas and all(set(a) == {"de", "a", "donde"} for a in aristas)
    assert {"de": "DEM Solicitud", "a": "DEM_SolicitudResumen", "donde": "Record View: Resumen"} in aristas
    assert leidos["dependencias.json"]["fueraDeLaAplicacion"] == []      # DEM no llama a nada de fuera
    assert leidos["sin-verificar.json"]["sinVerificar"] == []
    hallazgos = leidos["hallazgos.json"]["hallazgos"]
    assert [h["id"] for h in hallazgos] == ["H-SEG-01", "H-SEG-03"]        # sin el duplicado
    assert set(hallazgos[0]) == CAMPOS                                      # los campos de siempre…
    assert set(hallazgos[1]) == CAMPOS | {"base"} and len(hallazgos[1]["base"]) == 2   # …y base, en los inferidos
    nombres = {o["nombre"] for o in inv["objetos"]}
    assert all(o in nombres for h in hallazgos for o in h["objetos"])      # cada objeto de un hallazgo, en el inventario
    procesos = leidos["procesos.json"]["procesos"]
    assert procesos and all(set(p) == {"nombre", "json", "nodos", "ejecuciones"} for p in procesos)
    solicitud = next(o for o in inv["objetos"] if o["nombre"] == "DEM Solicitud")
    assert {"DEM_SOLICITUD", "Resumen"} <= set(solicitud["tambien"])        # la tabla y la vista, con su record type
