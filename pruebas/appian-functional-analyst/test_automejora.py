"""Regresiones de automejora sobre proyectos ficticios, sin red ni Appian."""
import contextlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
from types import SimpleNamespace
import unittest
import unittest.mock

sys.dont_write_bytecode = True
import selftest as fixture
sys.path.insert(0, str(fixture.S))
import modelo as mo
import issues as iss
import unidades as un
import indice
import proyecto
import comprobar


class Automejora(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="automejora-")
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        self.p = self.root / "proyecto"
        cfg = self.root / "gitconfig"
        cfg.write_text("", encoding="utf-8")
        self.env = unittest.mock.patch.dict(os.environ, {
            "GIT_CONFIG_GLOBAL": str(cfg), "GIT_CONFIG_NOSYSTEM": "1", "GIT_TERMINAL_PROMPT": "0",
            "GIT_AUTHOR_NAME": "Prueba", "GIT_AUTHOR_EMAIL": "prueba@example.com",
            "GIT_COMMITTER_NAME": "Prueba", "GIT_COMMITTER_EMAIL": "prueba@example.com"})
        self.env.start()
        self.addCleanup(self.env.stop)

    def copia(self):
        shutil.copytree(fixture.EJEMPLO, self.p)
        return mo.Proyecto(self.p)

    def preparada(self):
        fixture.nueva_con_issues(self.p)
        code, out = fixture.corre(fixture.S / "proyecto.py", "cambio", self.p, "EV-01", "aprobada", "--fuente", "FU-05")
        self.assertEqual(code, 0, out)
        m = mo.Proyecto(self.p)
        return m, iss.calcula(m, un.Contexto(m), "EV-01")

    def captura(self, fn, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            fn(*args)
        return out.getvalue()

    def test_anexo_preserva_notas_y_consulta(self):
        self.copia()
        f = self.p / "analisis" / "funcional.md"
        original = f.read_text(encoding="utf-8")
        for manual in ("\nNota manual pendiente\n", "\n### Preguntas\nPC nueva\n",
                       "\n| PAN-01 Listado · Botón | no borrar esta nota | ✔ |\n"):
            f.write_text(original + manual, encoding="utf-8")
            antes = f.read_bytes()
            with self.assertRaises(SystemExit):
                indice.c_derivadas(mo.Proyecto(self.p), SimpleNamespace(escribir=True))
            self.assertEqual(f.read_bytes(), antes)
            self.captura(indice.c_derivadas, mo.Proyecto(self.p), SimpleNamespace(escribir=False))
        f.write_text(original + "\n## Otro apartado\nNo perder\n", encoding="utf-8")
        self.captura(indice.c_derivadas, mo.Proyecto(self.p), SimpleNamespace(escribir=True))
        self.assertIn("No perder", f.read_text(encoding="utf-8"))
        f.write_text(original.replace(indice.TITULO_ANEXO, "## Anexo. Otra cosa"), encoding="utf-8")
        with self.assertRaises(SystemExit):
            indice.c_derivadas(mo.Proyecto(self.p), SimpleNamespace(escribir=True))

    def test_crlf_e_ids(self):
        f = self.root / "crlf.md"
        f.write_bytes(b"primera\r\nsegunda\r\n")
        mo.escribe(f, "primera\ntercera\n")
        self.assertEqual(f.read_bytes(), b"primera\r\ntercera\r\n")
        self.assertEqual(mo.ancho_ids(["HU-054", "D-01"], "HU"), 3)
        self.assertEqual(mo.ancho_ids(["HU-054", "D-01"], "D"), 2)
        self.copia()
        f = self.p / "analisis" / "funcional.md"
        f.write_text(f.read_text(encoding="utf-8").replace("HU-01", "HU-001"), encoding="utf-8")
        out = self.captura(indice.c_siguientes, mo.Proyecto(self.p), SimpleNamespace())
        self.assertIn("HU-012", out)

    def test_colision_desconocida_no_recomienda_desarrollo(self):
        fixture.con_unidades(self.p)
        dep = self.p / "as-is" / "datos" / "dependencias.json"
        if dep.exists():
            dep.unlink()
        m = mo.Proyecto(self.p)
        ctx = un.Contexto(m)
        self.assertFalse(ctx.colision("URG-01")["dependenciasDisponibles"])
        # Sin choques conocidos: dependencia ausente no equivale a ausencia de colisión.
        with unittest.mock.patch.object(un.Contexto, "colision", return_value={
                "corregidos": ["X"], "usan": [], "choques": [], "deriva": "sin fichero",
                "dependenciasDisponibles": False}):
            out = self.captura(indice.c_colision, m, SimpleNamespace(unidad="URG-01"))
        self.assertIn("desconocida", out)
        self.assertNotIn("Dónde se corrige: Desarrollo", out)

    def test_tabla_ausente_diagnostico(self):
        m, _ = self.preparada()
        f = self.p / "analisis" / "tecnico.md"
        t = f.read_text(encoding="utf-8")
        f.write_text(re.sub(r"## 13\..*?(?=## 14\.)", "## 13. Plan\n1. Crear objetos\n\n", t, flags=re.S), encoding="utf-8")
        m = mo.Proyecto(self.p)
        with self.assertRaisesRegex(iss.NoSePuede, "no tiene tabla"):
            iss.calcula(m, un.Contexto(m), "EV-01")
        out = self.captura(comprobar.comprobar_unidades, m, un.Contexto(m))
        self.assertIn("EV-01", out)

    def test_campos_extra_nuevos_y_diferencias_reales(self):
        m, plan = self.preparada()
        i = plan.issues[0]
        f = fixture.verifica(self.p, "EV-01", i.id, **{i.objetos[0]: {"sobranCampos": ["auditoria"]}})
        self.assertTrue(iss.estado(self.p, "EV-01", i)[0])
        v = json.loads(f.read_text(encoding="utf-8"))
        v["objetos"][0]["diferencias"]["faltanCampos"] = ["solicitud"]
        f.write_text(json.dumps(v), encoding="utf-8")
        self.assertFalse(iss.estado(self.p, "EV-01", i)[0])

    def test_aplicacion_parentesis_legitimos(self):
        m = self.copia()
        f = self.p / "analisis" / "tecnico.md"
        fixture.editar(f, "| Versión de Appian |", "| Aplicación | Gestión (Europa) | Equipo |\n| Prefijo | AUT | Equipo |\n| Versión de Appian |")
        self.assertEqual(iss.aplicacion(mo.Proyecto(self.p)), "Gestión (Europa)")

    def test_numero_issue_no_reutiliza_maximo_eliminado(self):
        m, plan = self.preparada()
        maximo = max(iss.numero(i.id) for i in plan.issues)
        plan.issues = plan.issues[:-1]
        iss.escribe(plan, self.p)
        m = mo.Proyecto(self.p)
        nuevo = iss.calcula(m, un.Contexto(m), "EV-01")
        self.assertGreater(max(iss.numero(i.id) for i in nuevo.issues), maximo)

    def test_exigidas_ausentes_con_excepcion_humana(self):
        m, plan = self.preparada()
        i = next(x for x in plan.issues if x.esperado["_issue"].get("casosExigidos"))
        fixture.verifica(self.p, "EV-01", i.id, pruebas={"ejecutadas": True, "objetos": [{"objeto": o, "de": "issue", "casos": 0} for o in i.esperado["_issue"]["casosExigidos"]]})
        self.assertIn("faltan casos exigidos", iss.estado(self.p, "EV-01", i)[1])
        objeto = i.esperado["_issue"]["casosExigidos"][0]
        _, _, plan, i, _ = iss.sin_prueba(self.p, "EV-01", i.id,
                                        objeto + " «casos exigidos ausentes»", "Validación manual acordada")
        self.assertTrue(iss.estado(self.p, "EV-01", i, plan.marcas)[0])
        self.assertEqual(len(plan.marcas), 1)
        fixture.verifica(self.p, "EV-01", i.id, pruebas=fixture.pruebas_de((objeto, "issue", [], [])))
        self.assertFalse(iss.sigue_marcada(self.p, plan, plan.marcas[0]))
        c, out = fixture.corre(fixture.S / "indice.py", "issues", self.p, "EV-01", i.id,
                               "--sin-prueba", "casos exigidos ausentes", "--motivo", "x", "--desatendida")
        self.assertNotEqual(c, 0, out)

    def test_migra_indice_legacy_sin_reutilizar_el_mayor(self):
        m, plan = self.preparada()
        mayor = max(plan.issues, key=lambda i: iss.numero(i.id))
        indice_path = self.p / "construccion" / "EV-01" / "indice.md"
        t = indice_path.read_text(encoding="utf-8")
        indice_path.write_text(re.sub(r"<!-- ultimo-numero-issue: \d+ -->\n", "", t), encoding="utf-8")
        tecnico = self.p / "analisis" / "tecnico.md"
        original = tecnico.read_text(encoding="utf-8")
        objeto = mayor.objetos[0]
        tecnico.write_text("\n".join(l for l in original.split("\n")
                                    if not (l.startswith("| 7 |") and f"`{objeto}`" in l)), encoding="utf-8")
        m = mo.Proyecto(self.p)
        nuevo, _, _ = iss.genera(m, un.Contexto(m), "EV-01")
        self.assertNotIn(mayor.id, [i.id for i in nuevo.issues])
        self.assertGreaterEqual(nuevo.ultimo_numero, iss.numero(mayor.id))
        tecnico.write_text(original, encoding="utf-8")
        m = mo.Proyecto(self.p)
        nuevo = iss.calcula(m, un.Contexto(m), "EV-01")
        self.assertGreater(max(iss.numero(i.id) for i in nuevo.issues), iss.numero(mayor.id))

    def test_ausencia_casos_no_se_infiere_de_error_o_transporte(self):
        i = iss.Issue([], objetos=["R"], esperado={"_issue": {"casosExigidos": ["R"]}})
        for pruebas in ({"ejecutadas": False}, {"ejecutadas": True, "objetos": [
                {"objeto": "R", "casos": 0, "error": "HTTP 401"}]}, {"ejecutadas": True, "objetos": []}):
            self.assertEqual(iss.casos_ausentes({"pruebas": pruebas}, i), [])
        self.assertEqual(len(iss.casos_ausentes({"pruebas": {"ejecutadas": True, "objetos": [
            {"objeto": "R", "casos": 0}]}}, i)), 1)

    def test_reserva_avisa_version_cambiada_y_dependencia(self):
        m, plan = self.preparada()
        c, out = fixture.corre(fixture.S / "proyecto.py", "iniciar", self.p)
        self.assertEqual(c, 0, out)
        _, _, plan, i, _ = iss.siguiente(self.p, "EV-01", "Ana")
        self.assertIn("versión", plan.reservas[i.id])
        dependiente = next(x for x in plan.issues if x.depende)
        self.assertIn("ESPERA a", iss.para_construir(m, un.Contexto(m), plan, dependiente))
        f = self.p / "analisis" / "tecnico.md"
        fixture.editar(f, "## 14.", "### Reglas para quien construye\nConservar auditoría.\n\n## 14.")
        m = mo.Proyecto(self.p)
        nuevo, _, _ = iss.genera(m, un.Contexto(m), "EV-01")
        self.assertTrue(any(i.id in a and "Ana" in a for a in nuevo.avisos))
        _, _, _, misma, aviso = iss.siguiente(self.p, "EV-01", "Ana")
        self.assertEqual(misma.id, i.id)
        self.assertIn("ha cambiado desde tu reserva", aviso)
        _, _, _, _, aviso = iss.siguiente(self.p, "EV-01", "Ana")
        self.assertNotIn("ha cambiado desde tu reserva", aviso)

    def test_supuestos_reglas_y_impacto(self):
        m, plan = self.preparada()
        i = next(x for x in plan.issues if "AUT_GenerarNumero" in x.objetos)
        f = self.p / "analisis" / "tecnico.md"
        fixture.editar(f, "## 14.", "### Supuestos para construir\n\n| Pregunta | Se construye con | Dónde cambia |\n|---|---|---|\n| PC-01 | 30 días | `AUT_GenerarNumero` |\n| PC-02 | Otro supuesto | `NoEsObjeto` |\n\n### Reglas para quien construye\nNo duplicar registros.\n\n## 14.")
        m = mo.Proyecto(self.p)
        salida = "\n".join(iss.supuestos_y_reglas(m, i, []))
        self.assertIn("30 días", salida)
        self.assertNotIn("Otro supuesto", salida)
        self.assertIn("No duplicar registros", salida)
        fixture.editar(f, "### Reglas para quien construye\nNo duplicar registros.",
                       "Reglas para quien construye: No duplicar registros.\nConservar el identificador.\n\n"
                       "| Pregunta | Se construye con | Dónde cambia |\n|---|---|---|\n"
                       "| PC-02 | Supuesto ajeno después | `NoEsObjeto` |")
        m = mo.Proyecto(self.p)
        salida = "\n".join(iss.supuestos_y_reglas(m, i, []))
        self.assertIn("No duplicar registros", salida)
        self.assertIn("Conservar el identificador", salida)
        self.assertNotIn("Supuesto ajeno después", salida)
        fixture.editar(f, "| PC-01 | 30 días |", "| PC-03 | 30 días |")
        m = mo.Proyecto(self.p)
        avisos = self.captura(comprobar.comprobar_unidades, m, un.Contexto(m))
        self.assertIn("PC-03", avisos)
        out = self.captura(indice.c_impacto, m, SimpleNamespace(con=["30 días"], ids=["HU-01"], nivel=1, cambio=None))
        self.assertRegex(out, r"l\.\d+.*30 días")

    def test_manual_informa_pendientes_y_aprobacion_procesada(self):
        m, plan = self.preparada()
        c, out = fixture.corre(fixture.S / "proyecto.py", "cambio", self.p, "EV-01", "construida", "--manual")
        self.assertEqual(c, 0, out)
        self.assertIn("pendiente de verificación", out)
        self.assertIn(plan.issues[0].id, out)
        out = self.captura(proyecto.estado, SimpleNamespace(carpeta=str(self.p)))
        linea = next(l for l in out.splitlines() if l.startswith("Fuentes:"))
        self.assertNotIn("FU-05", linea.split("sin procesar:")[-1] if "sin procesar:" in linea else "")

    def test_quien_vacio_recupera_identidad(self):
        with unittest.mock.patch.object(mo, "git", return_value="  Persona de git  "):
            self.assertEqual(iss.quien_soy(self.root, "   "), "Persona de git")
        with unittest.mock.patch.object(mo, "git", return_value=" \t "), \
                unittest.mock.patch.dict(os.environ, {"USERNAME": "  ", "USER": " \t "}):
            self.assertEqual(iss.quien_soy(self.root, "   "), "alguien")

    def test_manual_issue_humana_sin_fingir_verificacion(self):
        m, plan = self.preparada()
        i = plan.issues[0]
        for args in (("--manual",), ("--manual", "--motivo", "Revisión Designer", "--desatendida")):
            code, out = fixture.corre(fixture.S / "indice.py", "issues", self.p, "EV-01", i.id, *args)
            self.assertNotEqual(code, 0, out)
        code, out = fixture.corre(fixture.S / "indice.py", "issues", self.p, "EV-01", i.id,
                                  "--manual", "--motivo", "Revisión Designer", "--quien", "Ana")
        self.assertEqual(code, 0, out)
        self.assertIn("hecha manualmente por Ana", out)
        self.assertFalse((self.p / "construccion" / "EV-01" / "verificacion" / (i.id + ".json")).exists())
        m = mo.Proyecto(self.p)
        plan = iss.calcula(m, un.Contexto(m), "EV-01")
        siguiente = iss.elige(plan, self.p)
        self.assertIsNotNone(siguiente)
        self.assertNotEqual(siguiente.id, i.id)
        code, out = fixture.corre(fixture.S / "indice.py", "issues", self.p, "EV-01", i.id, "--automatico")
        self.assertEqual(code, 0, out)
        self.assertFalse(iss.estado(self.p, "EV-01", i)[0])

    def test_manual_caduca_y_no_tapa_fallos_actuales(self):
        m, plan = self.preparada()
        i = next(x for x in plan.issues if x.esperado["_issue"].get("casosExigidos"))
        objeto = i.esperado["_issue"]["casosExigidos"][0]
        iss.cierre_manual(self.p, "EV-01", i.id, "Comparación manual revisada", "Ana")
        f = fixture.verifica(self.p, "EV-01", i.id, pruebas=fixture.pruebas_de((objeto, "issue", ["caso"], [])),
                             **{objeto: {"falta": True}})
        self.assertFalse(iss.estado(self.p, "EV-01", i)[0])
        _, _, p2, i, _ = iss.sin_prueba(self.p, "EV-01", i.id, objeto + " «caso»", "Acordado")
        self.assertTrue(iss.estado(self.p, "EV-01", i, p2.marcas)[0])
        qa = self.p / "qa" / "EV-01" / "resultado.json"
        qa.parent.mkdir(parents=True)
        escenario = i.criterios[0]
        error = {"escenarios": {escenario: {"resultado": "falla", "paso": "entonces 1", "motivo": "Error",
                                            "versionIssue": i.version}}}
        qa.write_text(json.dumps(error), encoding="utf-8")
        self.assertFalse(iss.estado(self.p, "EV-01", i, p2.marcas)[0])
        _, _, p2, i, _ = iss.sin_prueba(self.p, "EV-01", i.id, escenario, "Excepción humana QA")
        self.assertTrue(iss.estado(self.p, "EV-01", i, p2.marcas)[0])
        # Una verificación y un QA que declaran otra versión no aportan fallos de esta versión.
        v = json.loads(f.read_text(encoding="utf-8")); v["issue"]["version"] = "anterior"
        f.write_text(json.dumps(v), encoding="utf-8")
        error["escenarios"][escenario]["versionIssue"] = "anterior"
        qa.write_text(json.dumps(error), encoding="utf-8")
        self.assertTrue(iss.estado(self.p, "EV-01", i)[0])
        fixture.editar(self.p / "analisis" / "tecnico.md", "## 14.",
                       "Reglas para quien construye: Cambia lo requerido.\n\n## 14.")
        m = mo.Proyecto(self.p)
        nuevo, _, _ = iss.genera(m, un.Contexto(m), "EV-01")
        actual = next(x for x in nuevo.issues if x.id == i.id)
        self.assertNotEqual(actual.version, i.version)
        self.assertFalse(iss.estado(self.p, "EV-01", actual)[0])
        self.assertEqual(nuevo.manuales, [])

    def test_unidad_con_issues_manuales_no_afirma_verificacion(self):
        m, plan = self.preparada()
        for i in plan.issues:
            iss.cierre_manual(self.p, "EV-01", i.id, "Revisión humana", "Ana")
        code, out = fixture.corre(fixture.S / "proyecto.py", "cambio", self.p, "EV-01", "construida")
        self.assertEqual(code, 0, out)
        self.assertIn("con cierres manuales", out)
        self.assertNotIn("· verificada", fixture.fila_de(self.p, "EV-01"))

    def test_avisos_gherkin_y_con_que(self):
        self.copia()
        c, out = fixture.corre(fixture.S / "comprobar.py", self.p)
        self.assertEqual(c, 0, out)
        self.assertIn("· criterios con dado", out)
        self.assertIn("· técnico §14: cada criterio con «Con qué»", out)

    def test_inicial_no_incrementa_ni_duplica(self):
        c, out = fixture.corre(fixture.S / "proyecto.py", "iniciar", self.p, "--nombre", "Inicial")
        self.assertEqual(c, 0, out)
        for nombre in ("funcional", "tecnico"):
            f = self.p / "analisis" / (nombre + ".md")
            t = f.read_text(encoding="utf-8")
            f.write_text(re.sub(r"Versión:.*", "Versión: 1.0", t), encoding="utf-8")
        (self.p / "fuentes" / "indice.json").write_text(json.dumps({"fuentes": [{"id": "FU-01", "fecha": "2026-10-01", "tipo": "Reunión"}]}), encoding="utf-8")
        dec = self.p / "analisis" / "decisiones.md"
        t = dec.read_text(encoding="utf-8")
        t = re.sub(r"(?m)^\|\s*0\.1\s*\|[^\n]*$", "| 1.0 | 2026-09-01 | Decisión original | FU-01 | Aceptada |", t)
        t += "\n## Tabla ajena\n| Clave | Texto |\n|---|---|\n| 1.0 | Conservar |\n"
        dec.write_text(t, encoding="utf-8")
        c, out = fixture.corre(fixture.S / "proyecto.py", "version", self.p, "--inicial", "--fuente", "FU-01", "--que", "Análisis inicial")
        self.assertEqual(c, 0, out)
        self.assertEqual(mo.Proyecto(self.p).version("F"), (1, 0))
        self.assertEqual(list((self.p / "versiones").iterdir()), [])
        self.assertIn("FU-01", (self.p / "proyecto.md").read_text(encoding="utf-8"))
        t = dec.read_text(encoding="utf-8")
        self.assertEqual(len(re.findall(r"(?m)^\| 1\.0 \|", t)), 2)
        self.assertIn("| 1.0 | Conservar |", t)
        self.assertIn("| 1.0 | 2026-09-01 | Decisión original | FU-01 | Aceptada |", t)
        self.assertEqual(json.loads((self.p / ".appian-plugin.json").read_text(encoding="utf-8"))["ruta"], str(fixture.PLUGIN))
        c, out = fixture.git(self.p, "check-ignore", ".appian-plugin.json")
        self.assertEqual(c, 0, out)


if __name__ == "__main__":
    import unittest.mock
    unittest.main()
