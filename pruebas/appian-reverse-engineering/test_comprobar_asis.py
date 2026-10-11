"""comprobar_asis.py: la documentación de ingeniería inversa, antes de entregarla."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from conftest import BUILD_MODEL, BUILD_SUMMARY, SKILL, extraccion_a_mano

COMPROBAR = SKILL / "scripts" / "comprobar_asis.py"
PALABRAS = Path(__file__).resolve().parent.parent / "evaluaciones" / "recien-llegado" / "palabras.py"

LEEME = "# DEM Gestión de Solicitudes: documentación de ingeniería inversa\n\n" \
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


def as_is(base: Path, docs: dict | None = None, objetos: tuple = ()) -> Path:
    """Una carpeta as-is mínima: inventario (con los `objetos` que se pasen, como (nombre, tipo)), resumen, dos fichas
    del anexo, LEEME, 03 y los documentos que se pasen."""
    salida = base / "as-is"
    (salida / "datos").mkdir(parents=True)
    (salida / "datos" / "inventario.json").write_text(json.dumps({
        "aplicacion": {"nombre": "DEM Gestión de Solicitudes", "prefijo": "DEM", "uuid": "u-app"},
        "objetos": [
            {"nombre": "DEM Solicitud", "tipo": "recordType", "uuid": "u-1", "anexo": "anexo/recordType/DEM_Solicitud.md",
             "tambien": ["DEM_SOLICITUD", "Resumen", "titulo"]},
            {"nombre": "DEM_ER_EsAdmin", "tipo": "expressionRule", "uuid": "u-2",
             "anexo": "anexo/expressionRule/DEM_ER_EsAdmin.md", "tambien": []},
            *({"nombre": n, "tipo": t, "uuid": f"u-x{i}", "anexo": None, "tambien": []}
              for i, (n, t) in enumerate(objetos))]}, ensure_ascii=False),
        encoding="utf-8")
    (salida / "extraccion").mkdir()
    (salida / "extraccion" / "summary.json").write_text(json.dumps({
        "counts": {"application": 1, "recordType": 1, "expressionRule": 1}, "totals": {"objects": 2}}), encoding="utf-8")
    for ficha in ("anexo/recordType/DEM_Solicitud.md", "anexo/expressionRule/DEM_ER_EsAdmin.md"):
        (salida / ficha).parent.mkdir(parents=True, exist_ok=True)
        (salida / ficha).write_text("# Ficha\n\n```text\n1 | {{1, 2}, {3}}\n```\n", encoding="utf-8")
    for rel, texto in {"LEEME.md": LEEME, "03-modelo-datos.md": DATOS, **(docs or {})}.items():
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
    """Las cifras del volumen de LEEME, que es la entrada a la documentación, son las de summary.json."""
    salida = as_is(tmp_path, {"LEEME.md": LEEME.replace("2 objetos", "3 objetos")})
    errores, _ = comprueba(salida)
    assert len(errores) == 1 and errores[0].split()[1] == "LEEME.md:4", errores
    assert "3 objetos" in errores[0] and "2" in errores[0], errores


def test_expresion_sail_no_es_un_nombre(tmp_path):
    """Una expresión SAIL entre comillas invertidas se corta donde acaba el nombre: en lo que no admite el nombre de
    una regla, una interfaz o una constante. Un nombre del inventario con esos caracteres (un grupo con «&») vale
    entero, y un patrón que solo es el prefijo no cita ningún objeto."""
    texto = ("# Integraciones\n\nLa URL es `cons!DEM_URL_ERP & \"/ordenes/\" & ri!id`, la condición "
             "`rule!DEM_ER_EsAdmin()=true` y la lista `{cons!DEM_URL_ERP, cons!DEM_URL_ERP}`; la usan "
             "`DEM Gestores & Revisores` y los objetos `DEM_*`.\n\nLa otra URL es `cons!DEM_URL_Inventada & \"/ruta\"`.\n")
    salida = as_is(tmp_path, {"05-integraciones-consumidas.md": texto},
                   objetos=(("DEM_URL_ERP", "constant"), ("DEM Gestores & Revisores", "group")))
    errores, _ = comprueba(salida)
    assert len(errores) == 1 and "05-integraciones-consumidas.md:5 `DEM_URL_Inventada` no es" in errores[0], errores


def test_frase_que_empieza_por_un_nombre(tmp_path):
    """Una frase que empieza por un nombre entre comillas invertidas no se suma a la anterior."""
    texto = ("# Arquitectura\n\nLa regla calcula el plazo de cada solicitud nueva y devuelve la fecha límite que ve "
             "el gestor en su bandeja de entrada cada mañana. `DEM_ER_EsAdmin` decide quién administra la aplicación "
             "y quién puede reabrir una solicitud cerrada por error.\n")
    assert comprueba(as_is(tmp_path, {"02-arquitectura.md": texto})) == ([], [])


def test_presupuesto_sin_lo_generado(tmp_path):
    """Lo que escriben los scripts entre sus marcadores (la tabla «Sin verificar» de LEEME, el registro de 09) no
    cuenta para el presupuesto de palabras: cada NV registrado no empuja LEEME por encima del suyo."""
    filas = "".join(f"| Pregunta número {i} que la revisión no pudo verificar con lo que había | Acceso de lectura "
                    f"a la aplicación de utilidades | Equipo de utilidades | Abierto |\n" for i in range(120))
    tabla = ("\n## Sin verificar\n\n<!-- sin-verificar:inicio -->\n| Pregunta | Qué hace falta | A quién | Estado |\n"
             f"|---|---|---|---|\n{filas}<!-- sin-verificar:fin -->\n")
    _, avisos = comprueba(as_is(tmp_path / "a", {"LEEME.md": LEEME + tabla}))
    assert avisos == []
    _, avisos = comprueba(as_is(tmp_path / "b", {"LEEME.md": LEEME + tabla.replace("<!-- sin-verificar:inicio -->\n", "")
                                                                         .replace("<!-- sin-verificar:fin -->\n", "")}))
    assert len(avisos) == 1 and "LEEME.md" in avisos[0] and "presupuesto" in avisos[0], avisos


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


def test_tabla_del_cdt_y_entidad_del_data_store(tmp_path):
    """Con datos/ hecho por build_datos.py, la tabla de un CDT y la entidad de un data store se citan sin ser objetos.
    El nombre del CDT pasado a mayúsculas (como lo dejaba en el diagrama ER la regla de antes) no es real."""
    salida = extraccion_a_mano(tmp_path / "as-is", [
        {"type": "cdt", "uuid": "u-cdt-00001", "name": "DEM_SolicitudDTO",
         "respuestas": {"definition": {"name": "DEM_SolicitudDTO", "jpa": {"tableName": "DEM_SOLICITUD_V1"},
                                       "fields": [{"name": "id", "type": "Number (Integer)"}]}}},
        {"type": "dataStore", "uuid": "u-ds-000001", "name": "DEM Datos",
         "respuestas": {"definition": {"name": "DEM Datos", "entities": [{"name": "DEM_ENT_Solicitudes",
                                                                         "dataTypeUuid": "u-cdt-00001"}]}}}])
    for script in (BUILD_MODEL, BUILD_SUMMARY, SKILL / "scripts" / "build_datos.py"):
        p = subprocess.run([sys.executable, str(script), str(salida)], capture_output=True, text=True, encoding="utf-8")
        assert p.returncode == 0, p.stderr
    (salida / "03-modelo-datos.md").write_text(
        "# Modelo de datos\n\n`DEM_SolicitudDTO` se guarda en la tabla `DEM_SOLICITUD_V1` por la entidad "
        "`DEM_ENT_Solicitudes` de `DEM Datos`; en el diagrama, `DEM_SOLICITUDDTO`.\n", encoding="utf-8")
    errores, _ = comprueba(salida)
    assert len(errores) == 1 and "`DEM_SOLICITUDDTO` no es" in errores[0], errores


def test_objeto_de_fuera_de_la_aplicacion(tmp_path):
    """Un objeto de otra aplicación que esta llama (en `fueraDeLaAplicacion`) es un nombre real, aunque lleve el prefijo."""
    salida = as_is(tmp_path, {"02-arquitectura.md": "# Arquitectura\n\n`DEM_ER_EsAdmin` llama a `DEM_ER_Compartida`, "
                                                    "que está en otra aplicación.\n"})
    (salida / "datos" / "dependencias.json").write_text(json.dumps({"aristas": [], "fueraDeLaAplicacion": [
        {"nombre": "DEM_ER_Compartida", "tipo": "llamado con rule!", "usadoPor": ["DEM_ER_EsAdmin"], "usa": [],
         "nv": "NV-ARQ-01"}]}, ensure_ascii=False), encoding="utf-8")
    assert comprueba(salida) == ([], [])


# ---------------------------------------------------------------- sin agujeros (tarea 1.5 de la 0.7.0-beta.2)

def test_nombre_inventado_fuera_del_codigo(tmp_path):
    """Un nombre con el prefijo también se mira fuera del código: en texto plano, en negrita o como texto de un enlace.
    Un nombre real, el slug de su ficha y una ruta no son inventados, y lo que ya se miró en el código no se repite."""
    texto = ("# Arquitectura\n\nDEM_ER_Plana calcula el plazo, **DEM_ER_Negrita** lo avisa y "
             "[DEM_ER_Enlace](./03-modelo-datos.md) lo guarda.\n\n"
             "DEM_ER_EsAdmin decide quién administra (ver anexo/expressionRule/DEM_ER_Ruta.md y la ficha "
             "DEM_Solicitud); `DEM_ER_Codigo` sale una vez.\n")
    errores, _ = comprueba(as_is(tmp_path, {"02-arquitectura.md": texto}))
    assert [e.split("`")[1] for e in errores] == ["DEM_ER_Plana", "DEM_ER_Negrita", "DEM_ER_Enlace", "DEM_ER_Codigo"], errores


def test_evidencia_de_otro_objeto(tmp_path):
    """Una evidencia «mcp:<tipo>/<nombre>» lleva a la ficha del anexo de ese objeto (inventario.json → anexo), no a la
    de otro ni al índice del anexo."""
    tabla = ("# Arquitectura\n\n| Objeto | Certeza | Evidencia |\n|---|---|---|\n"
             "| `DEM Solicitud` | ✅ | [`mcp:recordType/DEM Solicitud#fields`](./anexo/recordType/DEM_Solicitud.md) |\n"
             "| `DEM Solicitud` | ✅ | [`mcp:recordType/DEM Solicitud#tableName`](./anexo/expressionRule/DEM_ER_EsAdmin.md) |\n"
             "| `DEM_ER_EsAdmin` | ✅ | [`mcp:expressionRule/DEM_ER_EsAdmin@validation`](./anexo/indice.md) |\n\n"
             "La regla lo decide ([`mcp:expressionRule/DEM_ER_EsAdmin#expression`](./anexo/recordType/DEM_Solicitud.md)).\n")
    salida = as_is(tmp_path, {"02-arquitectura.md": tabla, "anexo/indice.md": "# Anexo\n"})
    errores, _ = comprueba(salida)
    assert [e.split()[1] for e in errores] == ["02-arquitectura.md:6", "02-arquitectura.md:7", "02-arquitectura.md:9"], errores
    assert "DEM Solicitud" in errores[0] and "anexo/recordType/DEM_Solicitud.md" in errores[0], errores


def test_hallazgo_que_no_existe(tmp_path):
    """Un H-… citado tiene que estar en datos/hallazgos.json (como los NV en sin-verificar.json); el registro de 09, que
    escribe build_registry.py, no se mira."""
    salida = as_is(tmp_path, {
        "04-seguridad-grupos.md": "# Seguridad\n\nEl token es H-SEG-01; la cabecera, H-SEG-09.\n",
        "09-valor-adicional.md": "# Valor adicional\n\n<!-- registro:inicio -->\nFusionados: H-SEG-02 → H-SEG-01.\n"
                                 "<!-- registro:fin -->\n"})
    (salida / "datos" / "hallazgos.json").write_text(json.dumps({"hallazgos": [{"id": "H-SEG-01"}]}), encoding="utf-8")
    errores, _ = comprueba(salida)
    assert len(errores) == 1 and "04-seguridad-grupos.md:3" in errores[0] and "H-SEG-09" in errores[0], errores


def test_sin_prefijo_avisa(tmp_path):
    """Sin prefijo en la aplicación, los nombres citados no se pueden comprobar: un aviso lo dice."""
    salida = as_is(tmp_path, {"02-arquitectura.md": "# Arquitectura\n\nLa regla `XYZ_Inventada` calcula el plazo.\n"})
    inventario = salida / "datos" / "inventario.json"
    datos = json.loads(inventario.read_text(encoding="utf-8"))
    datos["aplicacion"]["prefijo"] = None
    inventario.write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")
    errores, avisos = comprueba(salida)
    assert errores == [] and len(avisos) == 1 and "prefijo" in avisos[0], avisos


def test_mencion_a_otra_area_sin_id(tmp_path):
    """Una línea que enlaza los hallazgos de otro documento cita su H-… o su NV-… (T21): si no, un aviso. Los suyos y
    los que llevan ID, no."""
    texto = ("# Modelo de datos\n\nQuién usa la acción lo dice [04](./04-seguridad-grupos.md#hallazgos).\n\n"
             "El token es H-SEG-01 ([04](./04-seguridad-grupos.md#hallazgos)).\n\n"
             "Los del modelo, en [Hallazgos](#hallazgos) y [aquí](./03-modelo-datos.md#hallazgos).\n")
    salida = as_is(tmp_path, {"03-modelo-datos.md": texto, "04-seguridad-grupos.md": "# Seguridad\n\n## Hallazgos\n"})
    (salida / "datos" / "hallazgos.json").write_text(json.dumps({"hallazgos": [{"id": "H-SEG-01"}]}), encoding="utf-8")
    errores, avisos = comprueba(salida)
    assert errores == [] and len(avisos) == 1 and "03-modelo-datos.md:3" in avisos[0], avisos


def test_cifras_solo_en_el_volumen(tmp_path):
    """Las cifras se comparan solo en la línea «Volumen» de LEEME (T22, lo dice el docstring): otra cifra no se mira."""
    import comprobar_asis as ca
    assert "solo en la línea «Volumen»" in " ".join(ca.__doc__.split())
    salida = as_is(tmp_path, {"LEEME.md": LEEME + "\nDe los 7 objetos clave, 3 interfaces se ven en el portal.\n"})
    assert comprueba(salida) == ([], [])


def test_palabras_comun_con_la_evaluacion(tmp_path):
    """palabras() de comprobar_asis.py, la del presupuesto, no cuenta títulos ni lo que escriben los scripts, y
    palabras.py de la evaluación del recién llegado cuenta con ella."""
    import comprobar_asis as ca
    texto = ("# Un título largo de varias palabras\n\nUna frase de seis palabras aquí.\n\n<!-- registro:inicio -->\n"
             "| H-SEG-01 | Token | seguridad |\n<!-- registro:fin -->\n\n```text\ncódigo que no cuenta\n```\n")
    assert ca.palabras(texto) == 6
    salida = as_is(tmp_path, {"09-valor-adicional.md": texto})
    p = subprocess.run([sys.executable, str(PALABRAS), str(salida), "--json"], capture_output=True, text=True,
                       encoding="utf-8")
    assert p.returncode == 0, p.stderr
    cuenta = json.loads(p.stdout)["documentos"]
    assert cuenta["09-valor-adicional.md"] == 6
    assert cuenta == {rel: ca.palabras((salida / rel).read_text(encoding="utf-8")) for rel in cuenta}
