"""Pruebas de build_model.py y de la compatibilidad con build_summary.py (sin modificarlo)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent / "mock_devmcp"))
import fixture  # noqa: E402
from conftest import BUILD_MODEL, BUILD_SUMMARY  # noqa: E402

OBJS, KEY_BY_UUID, _ = fixture.build()

EXPECTED = {
    # desde las herramientas de dependencias
    ("I_DASH", "RT_SOL", "recordTypeRef"), ("I_DASH", "R_CONT", "ruleRef"), ("I_FORM", "RT_SOL", "recordTypeRef"),
    ("I_FORM", "C_ESTADOS", "constRef"), ("I_RES", "R_ADMIN", "ruleRef"), ("I_ADMIN", "C_PM_ALTA", "constRef"),
    ("R_CONT", "RT_SOL", "recordTypeRef"), ("R_ADMIN", "C_ADMIN", "constRef"),
    ("INT_CAT", "CS_CAT", "connectedSystemRef"), ("INT_ERP", "CS_ERP", "connectedSystemRef"),
    ("INT_ERP", "C_TOKEN", "constRef"), ("WS_SOL", "R_CONT", "ruleRef"), ("PM_ALTA", "I_FORM", "ruleRef"),
    ("PM_ALTA", "RT_SOL", "recordTypeRef"), ("PM_ALTA", "PM_REV", "subProcess"), ("PM_REV", "I_REV", "ruleRef"),
    ("PM_BATCH", "RT_SOL", "recordTypeRef"), ("RT_SOL", "I_RES", "viewRef"), ("RT_SOL", "PM_ALTA", "startProcess"),
    ("RT_SOL", "RT_EST", "recordTypeRef"), ("RT_EST", "RT_SOL", "recordTypeRef"), ("SITE", "I_DASH", "pageRef"),
    ("SITE", "RT_SOL", "pageRef"), ("SITE", "I_ADMIN", "pageRef"), ("SITE", "C_ADMIN", "constRef"),
    ("C_PM_ALTA", "PM_ALTA", "constValue"), ("AG_CLAS", "R_CONT", "ruleRef"),
    # integraciones: el analisis de dependencias no las admite -> nombre y uuid en la definicion
    ("I_FORM", "INT_CAT", "integrationCall"), ("PM_ALTA", "INT_ERP", "integrationCall"),
    # grupos por literal (securityGroupName, valor de constante, asignacion)
    ("C_ADMIN", "G_ADM", "groupRef"), ("PM_ALTA", "G_GES", "groupRef"), ("PM_REV", "G_REV", "groupRef"),
    # jerarquia de grupos por miembros
    ("G_USR", "G_GES", "memberGroup"), ("G_USR", "G_REV", "memberGroup"),
    # a!startProcess a traves de una constante
    ("I_ADMIN", "PM_ALTA", "startProcess"),
}


@pytest.fixture(params=["a", "b"])
def built(request, project):
    project.add_devmcp(variant=request.param, mode="readonly")
    project.run("extract", "--app", "DEM", "--out", str(project.out), "--retry-delay", "0.1", check=0)
    p = subprocess.run([sys.executable, str(BUILD_MODEL), str(project.out)], capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    return project


def key_edges(graph):
    return {(KEY_BY_UUID.get(e["source"]), KEY_BY_UUID.get(e["target"]), e["refType"]) for e in graph["edges"]}


def test_graph_edges(built):
    g = built.load("graph.json")
    edges = key_edges(g)
    missing = EXPECTED - edges
    assert not missing, f"Faltan aristas: {sorted(missing)}"
    assert not any(s == "APP" or t in ("APP", "F_RULES", "F_PM") for s, t, _ in edges)
    orph = {KEY_BY_UUID[u] for u in g["orphans"]}
    assert "PM_HUERF" in orph and "PM_BATCH" not in orph and "SITE" not in orph
    assert g["stats"]["edgesByOrigin"].get("dependents", 0) > 0


def test_inventory_fields(built):
    inv = built.load("inventory.json")
    by = {KEY_BY_UUID.get(o["uuid"]): o for objs in inv["objects"].values() for o in objs}
    assert inv["objects"]["application"][0]["prefix"] == "DEM"
    assert inv["source"]["kind"] == "devmcp" and inv["source"]["toolMode"] == "readonly"
    assert by["PM_BATCH"]["hasRecurrence"] is True and by["PM_BATCH"]["startType"] == "timer"
    assert by["PM_BATCH"]["schedule"]["recurrence"]["frequency"] == "DAILY"
    assert by["PM_REV"]["userTaskCount"] == 1
    assert by["PM_ALTA"]["subProcessCount"] == 1 and by["PM_ALTA"]["startFormInterface"] == "DEM_SolicitudForm"
    assert by["PM_ALTA"]["usage"]["executions"] == 120
    assert by["PM_HUERF"]["slug"] == "DEM_Utilidad_Huerfana"
    assert by["PM_HUERF"]["usage"]["executions"] == 0
    assert by["C_TOKEN"]["secret"] is True and by["C_TOKEN"]["value"] == OBJS["C_TOKEN"]["value"]   # tal cual
    assert "secret" not in by["C_URL"] and by["C_URL"]["value"] == OBJS["C_URL"]["value"]
    assert by["CS_ERP"]["baseUrl"] == OBJS["CS_ERP"]["baseUrl"]
    assert by["INT_ERP"]["method"] == "POST" and by["INT_ERP"]["connectedSystemRef"] == "DEM_CS_ERP"
    assert by["I_DASH"]["sailBytes"] > 100
    assert any("deprecated" in m for m in by["I_ADMIN"]["validationIssues"])
    assert by["G_USR"]["memberGroups"] and by["G_USR"]["userCount"] == 2
    assert by["RT_SOL"]["fieldCount"] == 6 and by["RT_SOL"]["tableName"] == "DEM_SOLICITUD"
    assert by["I_FORM"]["screen"].endswith(".json")
    assert by["PM_ALTA"]["versions"]["lastModifiedBy"] == "marta.ruiz"
    assert by["T_DTO"]["detail"] == "none" and by["AG_CLAS"]["detail"] == "full"
    for o in by.values():
        if o.get("path"):
            assert (built.interm() / o["path"]).exists()


def test_criticality_and_secrets(built):
    inv = built.load("inventory.json")
    by = {KEY_BY_UUID.get(o["uuid"]): o for objs in inv["objects"].values() for o in objs}
    alta = by["PM_ALTA"]["criticality"]
    assert alta["critical"] and alta["callsIntegrations"] == 1 and alta["calledBy"] >= 2
    assert by["PM_BATCH"]["criticality"]["critical"]                 # batch programado
    assert by["PM_REV"]["criticality"]["critical"]                   # subproceso con tarea humana
    assert not by["PM_HUERF"]["criticality"]["critical"]
    assert by["C_TOKEN"]["secrets"] >= 1 and by["CS_ERP"]["secrets"] >= 1        # lo que encuentra detect_secrets
    assert not any(o.get("secrets") for k, o in by.items() if k not in ("C_TOKEN", "CS_ERP"))


def test_build_summary_contract(built):
    p = subprocess.run([sys.executable, str(BUILD_SUMMARY), str(built.out)], capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    s = built.load("summary.json")
    crit = {c["name"]: c for c in s["criticalProcesses"]}
    assert crit["DEM Alta Solicitud"]["callsIntegrations"] == 1 and crit["DEM Alta Solicitud"]["calledBy"] >= 2
    assert crit["DEM Batch Recordatorios"]["isBatch"] is True
    assert "DEM Utilidad Huérfana" not in crit
    assert s["meta"]["appPrefix"] == "DEM" and s["meta"]["confidence"] in ("Alto", "Medio", "Bajo")
    assert s["meta"]["confidenceBasis"] and s["secrets"]["count"] == 2
    assert s["meta"]["coverage"]["objects"] == 31 and s["meta"]["coverage"]["withDefinition"] == 29
    assert {"DEM_ERP_API_TOKEN", "DEM_CS_ERP"} <= set(s["secrets"]["objects"])
    assert any(x["type"] == "processModelsWithoutExecutions" for x in s["signals"])
    assert s["findings"] == []                                        # sin registro todavia
    assert s["usage"][0]["name"] == "DEM Alta Solicitud" and s["usage"][0]["executions"] == 120


def test_annex(built):
    annex_py = Path(BUILD_MODEL).parent / "build_annex.py"
    run = lambda: subprocess.run([sys.executable, str(annex_py), str(built.out)], capture_output=True, text=True)
    p = run()
    assert p.returncode == 0, p.stderr
    anexo = built.out / "anexo"
    form = (anexo / "interface" / "DEM_SolicitudForm.md").read_text(encoding="utf-8")
    assert "\n1  =a!formLayout" in form or "\n 1  =a!formLayout" in form          # líneas numeradas
    assert "recordType!DEM Solicitud.fields.titulo" in form and "recordType!{" not in form
    alta_txt = (anexo / "processModel" / "DEM_Alta_Solicitud.md").read_text(encoding="utf-8")
    assert "| 3 | Sub-Process (`internal3.subprocess`) |" in alta_txt or "| 3 | `internal3.subprocess` |" in alta_txt
    erp = (anexo / "connectedSystem" / "DEM_CS_ERP.md").read_text(encoding="utf-8")
    assert OBJS["CS_ERP"]["baseUrl"] in erp                             # tal cual, con sus credenciales
    assert "[DEM_SolicitudForm.md](./interface/DEM_SolicitudForm.md)" in (anexo / "indice.md").read_text(encoding="utf-8")
    alta = (anexo / "processModel" / "DEM_Alta_Solicitud.md").read_text(encoding="utf-8")
    assert "## Ejecuciones (@history)" in alta and "## Quién lo usa (@dependents)" in alta
    assert "marta.ruiz" in alta                                         # el autor de la última versión
    dash = (anexo / "interface" / "DEM_Dashboard.md").read_text(encoding="utf-8")
    assert "(@screen)" in dash and '"12"' in dash and '"40"' in dash   # el render, con sus valores
    if '"instances"' in alta:                                       # variante con instancias: resumen
        assert "Resumen: 20 instancias en la muestra" in alta and "iniciadas por: ana.garcia (20)" in alta
    assert "No disponible: la plataforma respondió con un error" in (anexo / "cdt" / "DEM_SolicitudDTO.md").read_text(encoding="utf-8")
    assert (anexo / "application" / "DEM.md").exists()
    assert "La extracción no trae la definición" in (anexo / "cdt" / "DEM_SolicitudDTO.md").read_text(encoding="utf-8")
    grafo = (anexo / "grafo.md").read_text(encoding="utf-8")
    assert "| DEM Alta Solicitud | subProcess | DEM Revisar Solicitud | dependents |" in grafo
    assert run().returncode == 0                                   # repetible
    (anexo / "indice.md").write_text("mío")                        # un anexo ajeno no se borra
    assert run().returncode == 2 and (anexo / "interface").exists()
