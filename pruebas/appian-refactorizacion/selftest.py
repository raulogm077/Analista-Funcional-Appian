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
import re
import shutil
import subprocess
import sys
import tempfile
import warnings

sys.dont_write_bytecode = True  # importa un script de la skill: sin __pycache__ dentro del plugin
# un aviso de obsolescencia del script es un fallo: con otra versión de Python será un error (re.split con maxsplit
# por posición, en 3.13). Como PYTHONWARNINGS=error::DeprecationWarning, pero para el script importado
warnings.simplefilter("error", DeprecationWarning)

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

        # Rutas físicas: una raíz o as-is con alias vale; una evidencia que escapa no.
        # Windows usa junction (no requiere permiso de symlink); otros sistemas, symlink.
        # Si no se pueden crear enlaces, se declara NO MEDIDO y falla la prueba, nunca PASS.
        def enlace_directorio(enlace, destino):
            if os.name == "nt":
                shell = shutil.which("pwsh") or shutil.which("powershell")
                if not shell:
                    raise OSError("no hay PowerShell para crear junctions")
                subprocess.run([shell, "-NoProfile", "-NonInteractive", "-Command",
                                "$ErrorActionPreference='Stop'; New-Item -ItemType Junction "
                                "-Path $env:REFACTOR_LINK -Target $env:REFACTOR_TARGET | Out-Null"],
                               env=dict(os.environ, REFACTOR_LINK=str(enlace), REFACTOR_TARGET=str(destino)),
                               check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
            else:
                enlace.symlink_to(destino, target_is_directory=True)
            if not enlace.exists() or enlace.resolve() != destino.resolve():
                raise OSError(f"el alias no resuelve al destino: {enlace}")

        try:
            alias_raiz = tmp / "Alias raíz"
            enlace_directorio(alias_raiz, p)
            errores, avisos = cp.comprobar(alias_raiz)
            ok("raíz del proyecto con alias válido", errores == [] and avisos == [], errores + avisos)

            p_alias, prop_alias = copia()
            destino_asis = tmp / "Entrada as-is"
            (p_alias / "as-is").rename(destino_asis)
            enlace_directorio(p_alias / "as-is", destino_asis)
            errores, avisos = cp.comprobar(p_alias)
            ok("as-is con alias válido", errores == [] and avisos == [], errores + avisos)

            cruda_alias = destino_asis / "extraccion" / "inventory.json"
            cruda_alias.parent.mkdir()
            cruda_alias.write_text("{}\n", encoding="utf-8")
            editar(prop_alias, "(../as-is/anexo/cdt/REX_Revision.md)", "(../as-is/extraccion/inventory.json)")
            errores, avisos = cp.comprobar(p_alias)
            ok("as-is con alias no permite extracción en bruto",
               len(errores) == 1 and "extracción" in errores[0] and avisos == [], errores + avisos)

            p_escape, prop_escape = copia()
            externo = tmp / "Evidencia externa ficticia"
            externo.mkdir()
            (externo / "evidencia.md").write_text("Señuelo ficticio fuera de as-is.\n", encoding="utf-8")
            enlace_directorio(p_escape / "as-is" / "salida", externo)
            editar(prop_escape, "(../as-is/anexo/processModel/REX_PM_AvisoAnual.md)",
                   "(../as-is/salida/evidencia.md)")
            errores, avisos = cp.comprobar(p_escape)
            ok("alias interno que escapa de as-is se rechaza",
               len(errores) == 1 and "REF-04" in errores[0] and "evidencia no enlaza" in errores[0] and avisos == [],
               errores + avisos)
        except (OSError, subprocess.CalledProcessError) as exc:
            ok("alias de directorio: NO MEDIDO por limitación del entorno", False,
               str(exc) + (f"\n{exc.stderr}" if isinstance(exc, subprocess.CalledProcessError) else ""))

        p, prop = copia()
        (p / "fuera.md").write_text("Señuelo ficticio fuera de as-is.\n", encoding="utf-8")
        editar(prop, "(../as-is/anexo/processModel/REX_PM_AvisoAnual.md)", "(../as-is/../fuera.md)")
        errores, avisos = cp.comprobar(p)
        ok("escape relativo desde as-is se rechaza",
           len(errores) == 1 and "REF-04" in errores[0] and "evidencia no enlaza" in errores[0] and avisos == [],
           errores + avisos)

        # 2. Los cinco errores que tiene que ver
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

        def da_aviso(nombre, cambios, *esperado, datos=()):
            """Una copia con `cambios` en la propuesta y `datos` [(fichero de as-is/datos, viejo, nuevo)] no da
            errores y da un solo aviso, que contiene todo lo `esperado`."""
            p, prop = copia()
            for viejo, nuevo in cambios:
                editar(prop, viejo, nuevo)
            for fichero, viejo, nuevo in datos:
                editar(p / "as-is" / "datos" / fichero, viejo, nuevo)
            errores, avisos = cp.comprobar(p)
            ok(nombre, errores == [] and len(avisos) == 1 and all(x in avisos[0] for x in esperado), errores + avisos)

        def da_nada(nombre, cambios, datos=()):
            p, prop = copia()
            for viejo, nuevo in cambios:
                editar(prop, viejo, nuevo)
            for fichero, viejo, nuevo in datos:
                editar(p / "as-is" / "datos" / fichero, viejo, nuevo)
            errores, avisos = cp.comprobar(p)
            ok(nombre, errores == [] and avisos == [], errores + avisos)

        sin_verificar = ("| 0 | Verificar H-DAT-02: confirmar", "| 0 | Confirmar")
        # Un campo es su línea y las sangradas que la siguen; si se repite, la unión
        da_aviso("hallazgo inferido en la línea de continuación de la Evidencia, sin «Verificar»: aviso",
                 [("- Evidencia: H-DAT-02 🔶", "- Evidencia: [`mcp:dataStore/REX Datos#entities`]"
                   "(../as-is/anexo/dataStore/REX_Datos.md) y\n  H-DAT-02 🔶"), sin_verificar],
                 "REF-02", "Verificar H-DAT-02")
        da_aviso("hallazgo inferido en una segunda «- Evidencia:», sin «Verificar»: aviso",
                 [("- Evidencia: H-DAT-02 🔶", "- Evidencia: [as-is](../as-is/LEEME.md)\n- Evidencia: H-DAT-02 🔶"),
                  sin_verificar], "REF-02", "Verificar H-DAT-02")
        da_nada("Evidencia con sub-viñetas no da errores", [("- Evidencia: H-DAT-02 🔶", "- Evidencia:\n  - H-DAT-02 🔶")])

        # Lo no verificado no desaparece sin aviso
        da_aviso("NV de sin-verificar.json que la propuesta no cita: aviso",
                 [("(NV-ARQ-01).", "."), ("Fase 0 y NV-ARQ-01", "Fase 0"),
                  ("| NV-ARQ-01 | ¿Qué hace `AVI_EnviarAviso` y qué recibe?; hace falta acceso de lectura a la "
                   "aplicación de avisos o un export de ella | Equipo de la aplicación de avisos | REF-01 |\n", "")],
                 "NV-ARQ-01", "sin-verificar.json")
        da_aviso("hallazgo inferido marcado ✅: aviso", [("H-DAT-02 🔶 inferido de", "H-DAT-02 ✅ se ve en")],
                 "H-DAT-02", "inferido", "✅")
        da_aviso("hallazgo Media que no está en ninguna REF ni en Pendientes: aviso",
                 [("- Evidencia: H-UI-01 ✅ el botón", "- Evidencia: el botón")], "H-UI-01", "Media", "Pendientes")
        da_nada("hallazgo Media en «- **Fuera del alcance:** H-…» del Alcance: sin aviso",
                [("- Evidencia: H-UI-01 ✅ el botón", "- Evidencia: el botón"),
                 ("- **Límites:**", "- **Fuera del alcance:** H-UI-01, la baja se revisa en otro proyecto.\n"
                                    "- **Límites:**")])
        plantilla = (SKILL / "assets" / "plantillas" / "propuesta.md").read_text(encoding="utf-8")
        linea = next((l for l in plantilla.splitlines() if l.startswith("- **Fuera del alcance:**")), "")
        da_nada("la línea «Fuera del alcance» de la plantilla, rellena, cuenta",
                [("- Evidencia: H-UI-01 ✅ el botón", "- Evidencia: el botón"),
                 ("- **Límites:**", re.sub(r"\{\{[^{}]*\}\}", "H-UI-01", linea) + "\n- **Límites:**")])
        da_aviso("hallazgo Media citado en otra línea del Alcance: sigue el aviso",
                 [("- Evidencia: H-UI-01 ✅ el botón", "- Evidencia: el botón"),
                  ("que ya siguen el diseño recomendado.", "que ya siguen el diseño recomendado (salvo H-UI-01).")],
                 "H-UI-01", "Media", "Fuera del alcance")
        for fichero, cita in (("hallazgos.json", "H-"), ("sin-verificar.json", "NV-")):
            p, prop = copia()
            (p / "as-is" / "datos" / fichero).unlink()
            errores, avisos = cp.comprobar(p)
            ok(f"sin as-is/datos/{fichero}, la propuesta cita {cita}…: aviso de que no se comprueban",
               errores == [] and len(avisos) == 1 and fichero in avisos[0] and cita in avisos[0], errores + avisos)

        # La Hoja de ruta se lee en su tabla: la prosa de encima no cuenta
        da_aviso("REF citada en la prosa de la Hoja de ruta y no en su tabla: aviso",
                 [("| 2 | REF-02: eventos de record. REF-03: acción", "| 2 | REF-02: eventos de record. Acción"),
                  ("## 5. Hoja de ruta\n", "## 5. Hoja de ruta\n\nLa baja (REF-03) va con la fase 2.\n")],
                 "REF-03", "Hoja de ruta")
        da_aviso("«Verificar H-…» en la prosa de la Hoja de ruta y no en su tabla: aviso",
                 [sin_verificar, ("## 5. Hoja de ruta\n", "## 5. Hoja de ruta\n\nAntes, Verificar H-DAT-02: con el equipo.\n")],
                 "REF-02", "Verificar H-DAT-02")

        # Fichas con otro separador o como título
        da_nada("fichas «### REF-01 · …» y «**REF-02: …**» valen",
                [("**REF-01 — Las revisiones se guardan con un CDT y un data store, sin record type**",
                  "### REF-01 · Las revisiones se guardan con un CDT y un data store, sin record type"),
                 ("**REF-02 — El historial", "**REF-02: El historial")])

        # Patrones de nombre, marcadores, dos BP en la Regla y «Verificar H-X y H-Y»
        da_nada("patrones de nombre en el Diagnóstico (`REX_IF_*`, `REX_ER_…`, `REX_`) no dan errores",
                [("con `a!queryEntity`", "con `a!queryEntity` (`REX_IF_*`)"),
                 ("no llegan al data fabric.", "no llegan al data fabric ni a las `REX_ER_…` ni a nada `REX_`.")])
        da_error("marcador {{…}} sin sustituir", [("seis semanas", "{{plazo}}")], "{{plazo}}")
        da_nada("Regla con dos BP válidas no da errores", [("- Regla: BP 01 §11", "- Regla: BP 01 §11; BP 03 §4")])
        da_error("Regla con dos BP y la segunda inexistente", [("- Regla: BP 01 §11", "- Regla: BP 01 §11; BP 01 §99")],
                 "BP 01 §99", "appian-best-practices")
        da_error("Regla con una segunda sección sin su documento («BP 01 §11 y §99»)",
                 [("- Regla: BP 01 §11", "- Regla: BP 01 §11 y §99")], "REF-02", "§99", "BP nn §x; BP mm §y")
        da_nada("«Verificar H-X y H-Y» vale para los dos",
                [("H-UI-01 ✅ el botón", "H-UI-01 🔶 inferido: el botón"),
                 ("| 0 | Verificar H-DAT-02: confirmar", "| 0 | Verificar H-DAT-02 y H-UI-01: confirmar")],
                datos=[("hallazgos.json", '"severidad": "Media", "certeza": "verificado",\n   "objetos": ["REX_IF_Ficha',
                        '"severidad": "Media", "certeza": "inferido",\n   "objetos": ["REX_IF_Ficha')])

        # 5. Lo que no es error
        p, prop = copia()
        editar(prop, "y el botón se quita |", "y el botón se quita; la regla nueva `REX_ER_PuedeDarDeBaja` dice quién |")
        errores, avisos = cp.comprobar(p)
        ok("un objeto nuevo en la Solución no da error", errores == [] and avisos == [], errores + avisos)

        # 6. Las señales citan secciones que existen, con el criterio de buenas prácticas
        senales = (SKILL / "references" / "senales.md").read_text(encoding="utf-8")
        citadas = sorted({(m.group(1).zfill(2), m.group(2)) for m in cp.BP.finditer(senales)})
        faltan = [f"BP {nn} §{x}" for nn, x in citadas if cp.en_buenas_practicas(nn, x, {}) is False]
        ok("cada «BP nn §x» de references/senales.md está en buenas prácticas", citadas and not faltan, faltan)
        def bp_de_la_fila(senal):
            """Las «BP nn §x» de la última columna de la fila de la tabla cuya señal contiene `senal`."""
            fila = next((l for l in senales.splitlines() if l.startswith("|") and senal in l.split("|")[1]), "|")
            bp = fila.strip().strip("|").split("|")[-1]
            return {f"BP {m.group(1).zfill(2)} §{m.group(2)}" for m in cp.BP.finditer(bp)}
        for senal, esperadas in (("muy frecuente", {"BP 03 §13"}), ("None", {"BP 07 §1", "BP 06 §7"}),
                                 ("_17r1", {"BP 08 §7"}), ("huérfano", {"BP 08 §6", "BP 11 §8"}),
                                 ("Cancelar", {"BP 03 §7"}), ("aunque no haga falta", {"BP 03 §5"})):
            ok(f"señales: la fila «{senal}» va a {'; '.join(sorted(esperadas))}", bp_de_la_fila(senal) == esperadas,
               bp_de_la_fila(senal))

        # 7. Salida 1 con errores y 2 sin as-is/datos/
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
