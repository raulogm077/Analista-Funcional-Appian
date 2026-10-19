"""Regresiones de los fallos observados al documentar y construir aplicaciones."""
import asyncio
import json
from types import SimpleNamespace

import pytest

import build_annex as ba
import build_inventario as bi
import build_model as bm
import comprobar_asis as ca
import devmcp_extract as dx
from rutas import escribe


def test_constante_tipo_valor_y_catalogo():
    p = dx.Policy(dx.DEFAULT_POLICY)
    ex = dx.Extractor(None, p, None)
    tool = SimpleNamespace(name="listConstants", description="", annotations=None,
                           inputSchema={"properties": {"applicationUuid": {"type": "string"}},
                                        "required": ["applicationUuid"]})
    ex.catalog = [tool]
    ex.classify(ex.base_type_phrases())
    result = SimpleNamespace(ok=True, data={"items": [
        {"uuid": "fake-uuid-text", "name": "DEM_TEXT", "type": "TEXT"},
        {"uuid": "fake-uuid-group", "name": "DEM_GROUP", "type": "GROUP"}]})
    _, objetos = ex.harvest_objects("fake-uuid-app", {"listConstants": result})
    assert {o["type"] for o in objetos} == {"constant"}
    assert {o["mcpType"] for o in objetos} == {"TEXT", "GROUP"}
    for nombre, tipo in (("getAgent", "aiAgent"), ("getAiSkill", "aiSkill"), ("getPackage", "package"),
                         ("getPortal", "portal"), ("getRelease", "release"), ("getRoboticTask", "roboticTask")):
        tool = SimpleNamespace(name=nombre, description="", annotations=None,
                               inputSchema={"properties": {"uuid": {"type": "string"}}, "required": ["uuid"]})
        ti = dx.analyze_tool(tool, p, False, ex.base_type_phrases())
        assert ti.types == [tipo] and not ti.generic


def test_localizacion_y_autor():
    o = {"type": "processModel"}
    bm.enrich_by_type(o, {"description": {"en": "English", "es": "Descripción"},
                         "startForm": {"es": {"interfaceUuid": "form-uuid"}}, "nodes": []},
                      {"form-uuid": "DEM_Formulario"})
    assert o["description"] == "Descripción" and o["startFormInterface"] == "DEM_Formulario"
    assert bm.ultima_version({"versions": [{"savedOn": "2026-10-18T10:00:00Z", "savedBy": "ana"}]})["lastModifiedBy"] == "ana"
    assert "| Revisar |" in "\n".join(ba.node_table({"nodes": [{"id": 1, "type": "internal.17",
                                                                "name": {"es": "Revisar"}}]}))
    assert bm.localized({"fr": "Bonjour", "en": "Hello"}) == "Hello"
    assert bm.localized({"interfaceUuid": "form-uuid"}) == {"interfaceUuid": "form-uuid"}
    assert "group" in bm.ENTRY_TYPES


def test_help_y_nombre_guion(capsys):
    assert ca.main(["--help"]) == 0
    assert "Uso:" in capsys.readouterr().out
    assert ca.nombre_citado("DEM_Nombre - Texto", "DEM", {"DEM_Nombre - Texto"}) == "DEM_Nombre - Texto"


def test_no_apps_explica_filtro(capsys):
    async def nada(*_):
        return []
    ex = SimpleNamespace(load_catalog=nada, list_apps=nada, check_interrupted=lambda: None,
                         tools=[SimpleNamespace(scope="env", toks=["list", "application"], allowed=False,
                                                name="listApplications", safety_reason="Excluida por --only.")])
    with pytest.raises(SystemExit) as err:
        asyncio.run(dx.aplicacion_de(ex, SimpleNamespace(app="DEM")))
    assert err.value.code == 14 and "--only" in capsys.readouterr().err


def test_inventario_regenera_sin_perder_aportes(tmp_path, capsys):
    work = tmp_path / "extraccion"
    work.mkdir()
    obj = {"uuid": "demo-uuid", "name": "DEM_Regla", "type": "expressionRule", "slug": "DEM_Regla",
           "detail": "full", "sailLines": 3}
    inv = {"objects": {"application": [{"name": "DEM Demo", "prefix": "DEM", "uuid": "app-uuid"}],
                       "expressionRule": [obj]}}
    (work / "inventory.json").write_text(json.dumps(inv), encoding="utf-8")
    (work / "graph.json").write_text(json.dumps({"orphans": ["demo-uuid"], "edges": []}), encoding="utf-8")
    nueve = tmp_path / "09-valor-adicional.md"
    nueve.write_bytes(("# Valor\r\n\r\nMi explicación.\r\n" + "\r\n".join(bi.HUERFANOS) + "\r\n").encode())
    assert bi.main([str(tmp_path)]) == 0
    assert "DEM_Regla" in capsys.readouterr().out
    f = tmp_path / "INVENTARIO.md"
    texto = f.read_text(encoding="utf-8").replace("| `DEM_Regla` |", "| [`DEM_Regla`](./11-reglas-negocio.md#regla) |")
    texto = texto.replace("| 3 | 0 | — |", "| 3 | 0 | 🔶 decide el plazo |")
    f.write_bytes((texto + "\nNota del analista.\n").replace("\n", "\r\n").encode())
    obj["sailLines"] = 5
    obj["description"] = "La plataforma aporta ahora otra descripción"
    (work / "inventory.json").write_text(json.dumps(inv), encoding="utf-8")
    assert bi.main([str(tmp_path)]) == 0
    nuevo = f.read_text(encoding="utf-8")
    assert "11-reglas-negocio.md#regla" in nuevo and "🔶 decide el plazo" in nuevo and "| 5 |" in nuevo
    assert "La plataforma aporta ahora" not in nuevo
    assert nuevo.endswith("Nota del analista.\n") and "Mi explicación." in nueve.read_text(encoding="utf-8")
    assert b"\r\n" in f.read_bytes() and b"\r\r\n" not in f.read_bytes()
    antes = f.read_bytes()
    nueve.write_text("Documento antiguo sin marcadores", encoding="utf-8")
    assert bi.main([str(tmp_path)]) == 2 and f.read_bytes() == antes
    assert bi.main([str(tmp_path), "--borrador"]) == 0
    assert (tmp_path / "INVENTARIO.borrador.md").exists() and nueve.read_text(encoding="utf-8") == "Documento antiguo sin marcadores"
    assert bi.main([str(tmp_path), "--borrador"]) == 2


def test_escribe_preserva_crlf(tmp_path):
    p = tmp_path / "documento.md"
    p.write_bytes(b"uno\r\ndos\r\n")
    escribe(p, "uno\ndos nuevos\n")
    assert p.read_bytes() == b"uno\r\ndos nuevos\r\n"


def test_inventario_tipos_cobertura_y_huerfanos_produccion(tmp_path):
    work = tmp_path / "extraccion"
    work.mkdir()
    objetos = {tipo: [{"uuid": f"demo-{tipo}", "name": f"DEM_{tipo}", "type": tipo, "slug": tipo,
                       "description": "Una descripción", "detail": "full"}]
               for tipo in (*bi.EXTRAS, "aiSkill", "package", "cdt")}
    objetos["recordType"][0]["fieldCount"] = 4
    objetos["processModel"][0]["usage"] = {"executions": 0}
    objetos["integration"][0].update(connectedSystemRef="DEM_CS", modifiesData=True)
    (work / "datafabric.json").write_text(json.dumps({"recordTypes": [{"uuid": "demo-recordType", "count": 123}]}), encoding="utf-8")
    (work / "preflight.json").write_text(json.dumps({"environment": {"isProduction": True}}), encoding="utf-8")
    report = {"toolsUsed": ["getAgent"], "toolsOmitted": [{"name": "createAgent", "reason": "escribe"}],
              "disabledAfterProbe": [{"tool": "getObject", "type": "aiSkill", "reason": "no compatible"}],
              "errorCount": 1}
    cuerpo, huerfanos, faltan = bi.generar(tmp_path, {"objects": objetos}, {"orphans": [], "edges": []}, report, {})
    assert not faltan and "123" in cuerpo and "DEM_CS" in cuerpo and "True" in cuerpo
    assert "2: 1 usadas y 1 omitidas" in cuerpo and "Desactivada para aiSkill: no compatible" in cuerpo
    assert "DEM_processModel" in huerfanos and "DEM_recordType" not in huerfanos
    assert set(bi.anteriores(cuerpo)) == {o["uuid"] for ls in objetos.values() for o in ls}
    assert all(len(l.split("|")) - 2 <= 8 for l in cuerpo.splitlines() if l.startswith("|"))
