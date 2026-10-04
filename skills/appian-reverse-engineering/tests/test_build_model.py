"""Pruebas de build_model.py y de la compatibilidad con build_summary.py (sin modificarlo)."""
from __future__ import annotations

import json
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
    assert by["C_TOKEN"]["maskedSecret"] is True and by["C_TOKEN"]["value"] == "***"
    assert "P4ssw0rd" not in json.dumps(inv)
    assert by["CS_ERP"]["baseUrl"] == "https://svc_erp:***@erp.example.org/api"
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


def test_work_data_outside_deliverables(built):
    """Los datos en bruto no viven en la carpeta de entregables (se comparte); van en _trabajo/<app>."""
    assert built.interm() == built.out.parent / "_trabajo" / built.out.name
    assert (built.interm() / "mcp_raw").is_dir() and (built.interm() / "inventory.json").exists()
    assert not built.out.exists() or not any(built.out.rglob("*.json"))


def test_raw_files_have_no_secrets(built):
    raw = built.interm() / "mcp_raw"
    blob = "\n".join(p.read_text(encoding="utf-8") for p in raw.rglob("*.json"))
    assert "P4ssw0rd" not in blob and "sk_live_51Hc9" not in blob
    assert "=cons!DEM_ERP_API_TOKEN" in blob                 # las referencias no se enmascaran
    inv = built.load("inventory.json")
    tok = next(o for o in inv["objects"]["constant"] if o["name"] == "DEM_ERP_API_TOKEN")
    assert tok["maskedSecret"] is True


def test_build_summary_unchanged_contract(built):
    p = subprocess.run([sys.executable, str(BUILD_SUMMARY), str(built.out)], capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    s = built.load("summary.json")
    crit = {c["name"]: c for c in s["criticalProcesses"]}
    assert crit["DEM Alta Solicitud"]["callsIntegrations"] == 1 and crit["DEM Alta Solicitud"]["calledBy"] >= 2
    assert crit["DEM Batch Recordatorios"]["isBatch"] is True
    assert s["meta"]["appPrefix"] == "DEM"
    assert any(r["category"] == "security" for r in s["risks"])
