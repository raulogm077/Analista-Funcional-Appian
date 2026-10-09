#!/usr/bin/env python3
"""Prueba automática de la skill de refactorización. Usa el proyecto ficticio de datos/mantenimiento/.

  python3 pruebas/appian-refactorizacion/selftest.py

Prueba la skill de $PLUGIN_A_PROBAR/skills/appian-refactorizacion (por defecto, la de este repositorio): que
comprobar_propuesta.py da por buena la propuesta del ejemplo y que en copias rotas a propósito da el error o el aviso
de cada regla. Las copias van en una carpeta con espacios. Sale con 1 si algo falla.
"""
import importlib.util
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True  # importa un script de la skill: sin __pycache__ dentro del plugin

AQUI = pathlib.Path(__file__).resolve().parent
PLUGIN = pathlib.Path(os.environ.get("PLUGIN_A_PROBAR") or AQUI.parents[1]).resolve()
SKILL = PLUGIN / "skills" / "appian-refactorizacion"
SCRIPT = SKILL / "scripts" / "comprobar_propuesta.py"
EJEMPLO = AQUI / "datos" / "mantenimiento"
fallos = []


def ok(nombre, cond, detalle=""):
    print(("✓ " if cond else "✗ ") + nombre + ("" if cond else f"\n    {str(detalle)[-800:]}"))
    if not cond:
        fallos.append(nombre)


def editar(ruta, viejo, nuevo):
    t = ruta.read_text(encoding="utf-8")
    assert viejo in t, f"no está «{viejo[:60]}» en {ruta.name}"
    ruta.write_text(t.replace(viejo, nuevo, 1), encoding="utf-8")


def main():
    for st in (sys.stdout, sys.stderr):
        st.reconfigure(encoding="utf-8", errors="replace")
    if not SCRIPT.exists():
        ok("existe scripts/comprobar_propuesta.py", False, str(SCRIPT))
        return 1
    spec = importlib.util.spec_from_file_location("comprobar_propuesta", SCRIPT)
    cp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cp)

    tmp = pathlib.Path(tempfile.mkdtemp(prefix="refactorizacion-"))
    try:
        n = 0

        def copia():
            nonlocal n
            n += 1
            destino = tmp / "Carpeta con espacios" / f"Gestión app {n}"
            shutil.copytree(EJEMPLO, destino)
            return destino, destino / "refactorizacion" / "propuesta.md"

        def da_error(nombre, cambios, *esperado):
            """Una copia con `cambios` [(viejo, nuevo)] da un solo error, que contiene todo lo `esperado`."""
            p, prop = copia()
            for viejo, nuevo in cambios:
                editar(prop, viejo, nuevo)
            errores, avisos = cp.comprobar(p)
            ok(nombre, len(errores) == 1 and all(e in errores[0] for e in esperado), errores)

        # 1. El ejemplo pasa, en una ruta con espacios y desde la línea de órdenes
        p, prop = copia()
        errores, avisos = cp.comprobar(p)
        ok("el ejemplo pasa sin errores ni avisos (0/0)", errores == [] and avisos == [], errores + avisos)
        r = subprocess.run([sys.executable, str(SCRIPT), str(p)], capture_output=True, text=True, encoding="utf-8",
                           env=dict(os.environ, PYTHONUTF8="1"))
        ok("comprobar_propuesta.py sale con 0 y lo dice", r.returncode == 0 and "0 errores · 0 avisos" in r.stdout,
           r.stdout + r.stderr)
        ok("comprobar_propuesta.py no deja __pycache__ en la skill", not (SKILL / "scripts" / "__pycache__").exists())

        # 2. Los cinco errores del plan
        da_error("evidencia rota: enlace a una ficha del anexo que no existe",
                 [("anexo/cdt/REX_Revision.md", "anexo/cdt/REX_Revisiones.md")], "REX_Revisiones.md", "no existe")
        da_error("«BP 99 §1» que buenas prácticas no tiene",
                 [("- Regla: BP 01 §7", "- Regla: BP 99 §1")], "BP 99 §1", "appian-best-practices")
        da_error("objeto inventado en el Diagnóstico",
                 [("no llegan al data fabric.", "no llegan al data fabric ni a `REX_ER_PlazoRevision`.")],
                 "REX_ER_PlazoRevision", "inventario")
        da_error("REF sin alternativa en la Solución",
                 [("REF-03 (BP 01 §9.2)", "(BP 01 §9.2)")], "REF-03", "Solución")
        da_error("NV que no está en sin-verificar.json",
                 [("| NV-ARQ-01 | ¿Qué hace", "| NV-ARQ-02 | ¿Qué hace")], "NV-ARQ-02", "sin-verificar.json")

        # 3. El resto de errores
        da_error("falta un apartado", [("## 4. Migración y convivencia", "## 4. Migración")],
                 "4. Migración y convivencia")
        da_error("REF sin evidencia", [("- Evidencia: H-ARQ-01", "- Notas: H-ARQ-01")], "REF-04", "Evidencia")
        da_error("evidencia sin enlace a as-is/",
                 [(" · [`mcp:processModel/REX_PM_AvisoAnual@history`](../as-is/anexo/processModel/REX_PM_AvisoAnual.md)",
                   "")], "REF-04", "as-is/")
        da_error("REF sin «BP nn §x» en la Regla", [("- Regla: BP 11 §8", "- Regla: retirar lo que no se usa")],
                 "REF-04", "BP nn §x")
        da_error("prioridad fuera de la escala", [("- Prioridad: Media\n- Esfuerzo: S, una acción",
                                                   "- Prioridad: Urgente\n- Esfuerzo: S, una acción")],
                 "REF-03", "Urgente")
        da_error("hallazgo que no está en hallazgos.json", [("- Evidencia: H-UI-01", "- Evidencia: H-UI-07")],
                 "H-UI-07", "hallazgos.json")
        da_error("REF citada que no está en el Diagnóstico", [("| Negocio | REF-04 |", "| Negocio | REF-09 |")],
                 "REF-09", "Diagnóstico")
        p, prop = copia()
        cruda = p / "as-is" / "extraccion" / "inventory.json"
        cruda.parent.mkdir()
        cruda.write_text("{}\n", encoding="utf-8")
        editar(prop, "(../as-is/anexo/cdt/REX_Revision.md)", "(../as-is/extraccion/inventory.json)")
        errores, _ = cp.comprobar(p)
        ok("enlace a la extracción en bruto", len(errores) == 1 and "extracción" in errores[0] and "anexo" in errores[0],
           errores)

        # 4. Avisos
        p, prop = copia()
        editar(prop, "| 0 | Verificar H-DAT-02: confirmar", "| 0 | Confirmar")
        errores, avisos = cp.comprobar(p)
        ok("REF sobre un hallazgo inferido sin «Verificar H-…» antes: aviso",
           errores == [] and len(avisos) == 1 and "REF-02" in avisos[0] and "Verificar H-DAT-02" in avisos[0],
           errores + avisos)
        p, prop = copia()
        editar(prop, "| 2 | REF-02: eventos de record. REF-03: acción", "| 2 | REF-02: eventos de record. Acción")
        errores, avisos = cp.comprobar(p)
        ok("REF que no está en la Hoja de ruta: aviso",
           errores == [] and len(avisos) == 1 and "REF-03" in avisos[0] and "Hoja de ruta" in avisos[0],
           errores + avisos)

        # 5. Lo que no es error
        p, prop = copia()
        editar(prop, "y el botón se quita |", "y el botón se quita; la regla nueva `REX_ER_PuedeDarDeBaja` dice quién |")
        errores, avisos = cp.comprobar(p)
        ok("un objeto nuevo en la Solución no da error", errores == [] and avisos == [], errores + avisos)

        # 6. Salida 1 con errores y 2 sin as-is/datos/
        p, prop = copia()
        editar(prop, "- Regla: BP 01 §7", "- Regla: BP 99 §1")
        r = subprocess.run([sys.executable, str(SCRIPT), str(p)], capture_output=True, text=True, encoding="utf-8",
                           env=dict(os.environ, PYTHONUTF8="1"))
        ok("con un error sale con 1 y lo marca con ✗", r.returncode == 1 and "✗" in r.stdout, r.stdout + r.stderr)
        p, prop = copia()
        shutil.rmtree(p / "as-is" / "datos")
        r = subprocess.run([sys.executable, str(SCRIPT), str(p)], capture_output=True, text=True, encoding="utf-8",
                           env=dict(os.environ, PYTHONUTF8="1"))
        ok("sin as-is/datos/inventario.json sale con 2 y dice qué falta",
           r.returncode == 2 and "inventario.json" in r.stderr, r.stdout + r.stderr)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"\n{'Todo bien' if not fallos else f'{len(fallos)} fallos'}")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
