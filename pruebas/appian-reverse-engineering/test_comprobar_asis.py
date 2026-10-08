"""comprobar_asis.py: la documentación de ingeniería inversa, antes de entregarla."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from conftest import SKILL

COMPROBAR = SKILL / "scripts" / "comprobar_asis.py"

CERO = "# DEM Gestión de Solicitudes: resumen ejecutivo\n\n" \
       "> **TL;DR**: La aplicación gestiona las solicitudes internas.\n" \
       "> **Volumen**: 2 objetos (0 process models, 0 interfaces, 1 record types).\n"
DATOS = """# Modelo de datos

> **TL;DR**: `DEM Solicitud` guarda las solicitudes en la tabla `DEM_SOLICITUD` y las muestra en su vista `Resumen`.

## Vista

| Record type | Tabla | Certeza | Evidencia |
|---|---|---|---|
| `DEM Solicitud` | `DEM_SOLICITUD` | ✅ | [`mcp:recordType/DEM Solicitud#tableName`](./anexo/recordType/DEM_Solicitud.md) |

La regla `DEM_ER_EsAdmin` decide quién administra ([ficha](./anexo/expressionRule/DEM_ER_EsAdmin.md)).
"""
PARRAFO = ("El gestor revisa cada solicitud nueva, comprueba que trae los documentos obligatorios y la aprueba o la "
           "devuelve al solicitante con un motivo escrito.")


def as_is(base: Path, docs: dict | None = None) -> Path:
    """Una carpeta as-is mínima: inventario, resumen, dos fichas del anexo, 00, 03 y los documentos que se pasen."""
    salida = base / "as-is"
    (salida / "datos").mkdir(parents=True)
    (salida / "datos" / "inventario.json").write_text(json.dumps({
        "aplicacion": {"nombre": "DEM Gestión de Solicitudes", "prefijo": "DEM", "uuid": "u-app"},
        "objetos": [
            {"nombre": "DEM Solicitud", "tipo": "recordType", "uuid": "u-1", "anexo": "anexo/recordType/DEM_Solicitud.md",
             "tambien": ["DEM_SOLICITUD", "Resumen", "titulo"]},
            {"nombre": "DEM_ER_EsAdmin", "tipo": "expressionRule", "uuid": "u-2",
             "anexo": "anexo/expressionRule/DEM_ER_EsAdmin.md", "tambien": []}]}, ensure_ascii=False),
        encoding="utf-8")
    (salida / "extraccion").mkdir()
    (salida / "extraccion" / "summary.json").write_text(json.dumps({
        "counts": {"application": 1, "recordType": 1, "expressionRule": 1}, "totals": {"objects": 2}}), encoding="utf-8")
    for ficha in ("anexo/recordType/DEM_Solicitud.md", "anexo/expressionRule/DEM_ER_EsAdmin.md"):
        (salida / ficha).parent.mkdir(parents=True, exist_ok=True)
        (salida / ficha).write_text("# Ficha\n\n```text\n1 | {{1, 2}, {3}}\n```\n", encoding="utf-8")
    for rel, texto in {"00-resumen-ejecutivo.md": CERO, "03-modelo-datos.md": DATOS, **(docs or {})}.items():
        (salida / rel).parent.mkdir(parents=True, exist_ok=True)
        (salida / rel).write_text(texto, encoding="utf-8")
    return salida


def comprueba(salida: Path):
    p = subprocess.run([sys.executable, str(COMPROBAR), str(salida)], capture_output=True, text=True,
                       encoding="utf-8")
    assert p.returncode in (0, 1), p.stdout + p.stderr
    errores = [l for l in p.stdout.splitlines() if l.startswith("✗")]
    avisos = [l for l in p.stdout.splitlines() if l.startswith("·")]
    assert p.returncode == (1 if errores else 0), p.stdout
    return errores, avisos


def test_documento_correcto(tmp_path):
    assert comprueba(as_is(tmp_path)) == ([], [])


def test_objeto_inventado(tmp_path):
    salida = as_is(tmp_path, {"02-arquitectura.md": "# Arquitectura\n\nLa regla `DEM_ER_Inventada` calcula el plazo y "
                                                    "`rule!DEM_ER_Otra()` la avisa.\n"})
    errores, _ = comprueba(salida)
    assert len(errores) == 2 and "DEM_ER_Inventada" in errores[0] and "DEM_ER_Otra" in errores[1], errores
    assert "02-arquitectura.md:3" in errores[0]


def test_tabla_y_vista_no_son_inventadas(tmp_path):
    salida = as_is(tmp_path, {"10-pantallas.md": "# Pantallas\n\nLa vista `DEM Solicitud#Resumen` lee "
                                                 "`DEM Solicitud.fields.titulo` de la tabla `DEM_SOLICITUD`; "
                                                 "`recordType!DEM Solicitud` es su record type y el prefijo, `DEM_`.\n"})
    assert comprueba(salida) == ([], [])


def test_certeza_sin_evidencia(tmp_path):
    registro = ("# Valor adicional\n\n## Registro de hallazgos\n\n<!-- registro:inicio -->\n"
                "| ID | Hallazgo | Área | Severidad | Certeza | Dónde |\n|---|---|---|---|---|---|\n"
                "| H-SEG-01 | Token en una constante | seguridad | Alta | ✅ | [04](./03-modelo-datos.md) |\n"
                "<!-- registro:fin -->\n")
    salida = as_is(tmp_path, {"01-funcional.md": "# Funcional\n\n| Caso de uso | Certeza |\n|---|---|\n| Alta | ✅ |\n",
                              "09-valor-adicional.md": registro})
    errores, _ = comprueba(salida)
    assert len(errores) == 1 and "01-funcional.md:3" in errores[0] and "Evidencia" in errores[0], errores


def test_evidencia_rota(tmp_path):
    tabla = ("# Arquitectura\n\n| Objeto | Certeza | Evidencia |\n|---|---|---|\n"
             "| `DEM Solicitud` | ✅ | [`mcp:recordType/DEM Solicitud`](./anexo/recordType/DEM_Otra.md) |\n"
             "| `DEM_ER_EsAdmin` | 🔴 | [`mcp:expressionRule/DEM_ER_EsAdmin`](./anexo/expressionRule/DEM_ER_EsAdmin.md) |\n"
             "| `DEM_ER_EsAdmin` | ✅ | sin enlace |\n")
    errores, _ = comprueba(as_is(tmp_path, {"02-arquitectura.md": tabla}))
    assert [e.split()[1] for e in errores] == ["02-arquitectura.md:5", "02-arquitectura.md:5", "02-arquitectura.md:6",
                                              "02-arquitectura.md:7"], errores
    assert "🔴" in errores[2] and "anexo" in errores[3]


def test_cifra_distinta(tmp_path):
    salida = as_is(tmp_path, {"00-resumen-ejecutivo.md": CERO.replace("2 objetos", "3 objetos")})
    errores, _ = comprueba(salida)
    assert len(errores) == 1 and "3 objetos" in errores[0] and "2" in errores[0], errores


def test_marcador_y_enlace_roto(tmp_path):
    salida = as_is(tmp_path, {"04-seguridad-grupos.md": "# Seguridad\n\nLo administra {{grupo}}; ver "
                                                        "[el detalle](./no-existe.md#grupos).\n"})
    errores, _ = comprueba(salida)
    assert len(errores) == 2 and "{{" in errores[0] and "no-existe.md" in errores[1], errores   # el anexo, con su {{, no


def test_muletilla_es_aviso(tmp_path):
    salida = as_is(tmp_path, {"01-funcional.md": f"# Funcional\n\nCabe destacar que hay dos perfiles.\n\n{PARRAFO}\n",
                              "02-arquitectura.md": f"# Arquitectura\n\n{PARRAFO}\n\n" + "palabra " * 2400 + "\n"})
    errores, avisos = comprueba(salida)
    assert errores == []
    texto = "\n".join(avisos)
    assert "cabe destacar" in texto and "01-funcional.md:3" in texto
    assert "repetido" in texto and "01-funcional.md" in texto and "02-arquitectura.md" in texto
    assert "presupuesto" in texto and "palabras" in texto


def test_ruta_con_espacios(tmp_path):
    base = tmp_path / "Carpeta con espacios" / "Gestión app"
    assert comprueba(as_is(base)) == ([], [])
