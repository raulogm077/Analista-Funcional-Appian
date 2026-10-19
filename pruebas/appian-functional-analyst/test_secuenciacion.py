"""La pieza compartida espera sin mezclar el texto de dos encargos. Datos ficticios, sin red."""
import json
import unittest
import test_automejora as base

iss, mo, un, fixture = base.iss, base.mo, base.un, base.fixture


class Secuenciacion(unittest.TestCase):
    setUp = base.Automejora.setUp
    preparada = base.Automejora.preparada

    def segunda(self, destino="HU-01", decision="Pendiente", tipo="CAMBIA", contexto="—"):
        code, out = fixture.corre(fixture.S / "proyecto.py", "cambio", self.p, "EV-02", "abrir", "--titulo", "Siguiente entrega")
        self.assertEqual(code, 0, out)
        self.informe(destino, decision, tipo, contexto)

    def informe(self, destino, decision="Pendiente", tipo="CAMBIA", contexto="—"):
        f = self.p / "impacto/FU-99.md"
        f.parent.mkdir(exist_ok=True)
        f.write_text("# Impacto de FU-99\nAnálisis base: versión 1.1 · Cambio: EV-02 · Estado: pendiente\n\n"
                     "## Puntos\n| # | Tipo | Qué se dice | Encaja en | Cambio propuesto | Revisar también | Requiere | Decisión |\n"
                     "|---|---|---|---|---|---|---|---|\n"
                     f"| 1 | {tipo} | Petición ficticia | {destino} | {destino}: revisión posterior | {contexto} | Sí | {decision} |\n",
                     encoding="utf-8")

    def carga(self):
        m = mo.Proyecto(self.p)
        return m, un.Contexto(m)

    def artefactos(self):
        return {str(f.relative_to(self.p)): f.read_bytes() for carpeta in ("construccion", "versiones")
                for f in (self.p / carpeta).rglob("*") if f.is_file()}

    def cambia_titulo(self, pid):
        m, _ = self.carga()
        f = m.ruta("F")
        lineas = f.read_text(encoding="utf-8").splitlines()
        linea = m.piezas[pid].ini
        titulo = m.piezas[pid].titulo
        self.assertIn(titulo, lineas[linea])
        lineas[linea] = lineas[linea].replace(titulo, titulo + " contenido posterior")
        mo.escribe(f, "\n".join(lineas) + "\n")

    def test_propuesta_abierta_deja_construir_encargo_intacto(self):
        self.preparada()
        antes = self.artefactos()
        self.segunda()
        m, ctx = self.carga()
        plan, _, _ = iss.genera(m, ctx, "EV-01")
        self.assertTrue(plan.issues)
        self.assertEqual(self.artefactos(), antes)
        code, out = fixture.corre(fixture.S / "indice.py", "impacto", self.p, "HU-01", "--cambio", "EV-02")
        self.assertEqual(code, 0, out)
        self.assertIn("no edites su texto", out)

    def test_texto_ajeno_no_reescribe_issues_ni_esperados(self):
        self.preparada()
        self.segunda()
        antes = self.artefactos()
        self.cambia_titulo("HU-01")
        m, ctx = self.carga()
        with self.assertRaisesRegex(iss.NoSePuede, "contenido compartido"):
            iss.genera(m, ctx, "EV-01")
        self.assertEqual(self.artefactos(), antes)

    def test_cambio_independiente_en_misma_issue_no_se_bloquea(self):
        _, plan = self.preparada()
        self.assertTrue(any({"HU-01", "HU-03"} <= set(i.requisitos) for i in plan.issues))
        self.segunda()
        self.cambia_titulo("HU-03")
        m, ctx = self.carga()
        nuevo, escritos, _ = iss.genera(m, ctx, "EV-01")
        self.assertTrue(escritos)
        self.assertEqual(len(nuevo.issues), len(plan.issues))

    def test_objeto_compartido_desaparecido_se_busca_en_artefacto(self):
        _, plan = self.preparada()
        nombre = plan.issues[0].objetos[0]
        self.segunda("`" + nombre + "`")
        antes = self.artefactos()
        m, _ = self.carga()
        ini, fin = m.docs["T"].seccion("13")
        lineas = m.lineas("T")
        lineas[ini:fin] = [l for l in lineas[ini:fin] if "`" + nombre + "`" not in l]
        mo.escribe(m.ruta("T"), "\n".join(lineas))
        m, ctx = self.carga()
        with self.assertRaisesRegex(iss.NoSePuede, "contenido compartido"):
            iss.genera(m, ctx, "EV-01")
        self.assertEqual(self.artefactos(), antes)

    def test_legacy_migra_solo_con_version_igual_y_falta_evidencia_bloquea(self):
        self.preparada()
        self.segunda()
        def quita_huellas():
            for f in (self.p / "construccion/EV-01").glob("*-esperado.json"):
                datos = json.loads(f.read_text(encoding="utf-8"))
                datos["_issue"].pop("ambito", None)
                mo.escribe(f, json.dumps(datos))
        quita_huellas()
        m, ctx = self.carga()
        iss.genera(m, ctx, "EV-01")
        self.assertTrue(all("ambito" in json.loads(f.read_text(encoding="utf-8"))["_issue"]
                            for f in (self.p / "construccion/EV-01").glob("*-esperado.json")))
        quita_huellas()
        self.cambia_titulo("HU-01")
        antes = self.artefactos()
        m, ctx = self.carga()
        with self.assertRaisesRegex(iss.NoSePuede, "no hay huellas suficientes"):
            iss.genera(m, ctx, "EV-01")
        self.assertEqual(self.artefactos(), antes)
        for f in (self.p / "construccion/EV-01").glob("ISS-02-esperado.json"):
            f.unlink()
        antes = self.artefactos()
        with self.assertRaisesRegex(iss.NoSePuede, "falta el artefacto"):
            iss.genera(m, ctx, "EV-01")
        self.assertEqual(self.artefactos(), antes)

    def test_no_aprueba_segunda_ni_abre_version_sobre_primera(self):
        self.preparada()
        self.segunda(decision="✔")
        fuentes = self.p / "fuentes/indice.json"
        fuentes.parent.mkdir(exist_ok=True)
        (fuentes.parent / "FU-05-aprobacion.md").write_text("Aprobación ficticia", encoding="utf-8")
        cat = json.loads(fuentes.read_text(encoding="utf-8")) if fuentes.exists() else {"fuentes": []}
        cat["fuentes"].append({"id": "FU-99", "fecha": "2026-10-19", "nombre": "Cambio ficticio"})
        mo.escribe(fuentes, json.dumps(cat))
        antes = self.artefactos()
        documentos = {str(f): f.read_bytes() for f in (self.p / "analisis").glob("*.md")}
        for script, args in (("proyecto.py", ("cambio", self.p, "EV-02", "aprobada", "--fuente", "FU-05", "--comparte", "EV-01 primero")),
                             ("proyecto.py", ("version", self.p, "--fuente", "FU-99", "--que", "Revisión", "--informe", "impacto/FU-99.md"))):
            code, out = fixture.corre(fixture.S / script, *args)
            self.assertNotEqual(code, 0, out)
            self.assertIn("sin construir", out)
            self.assertEqual(self.artefactos(), antes)
            self.assertEqual({str(f): f.read_bytes() for f in (self.p / "analisis").glob("*.md")}, documentos)
        code, out = fixture.corre(fixture.S / "proyecto.py", "cambio", self.p, "EV-01", "construida", "--manual")
        self.assertEqual(code, 0, out)
        code, out = fixture.corre(fixture.S / "proyecto.py", "cambio", self.p, "EV-02", "aprobada", "--fuente", "FU-05")
        self.assertEqual(code, 0, out)

    def test_contexto_y_existe_no_son_cambio_y_dos_abiertas_admiten_primera(self):
        fixture.nueva_con_issues(self.p)
        self.segunda()
        code, out = fixture.corre(fixture.S / "proyecto.py", "cambio", self.p, "EV-01", "aprobada", "--fuente", "FU-05")
        self.assertEqual(code, 0, out)
        self.assertTrue((self.p / "construccion/EV-01/ISS-02-esperado.json").exists(), out)
        self.informe("HU-99", "✔", "NUEVO", "HU-01 solo de contexto")
        m, ctx = self.carga()
        self.assertFalse(ctx.solapes_secuencia("EV-02"))
        self.informe("HU-01", "✔", "EXISTE")
        m, ctx = self.carga()
        self.assertFalse(ctx.solapes_secuencia("EV-02"))

    def test_otro_cambio_ya_aplicado_impide_aprobar_y_decision_impide_version(self):
        fixture.nueva_con_issues(self.p)
        self.segunda(decision="✔")
        informe = self.p / "impacto/FU-99.md"
        mo.escribe(informe, informe.read_text(encoding="utf-8").replace("Estado: pendiente", "Estado: aplicado en 1.1"))
        antes = self.artefactos()
        cambios = (self.p / "analisis/cambios.md").read_bytes()
        code, out = fixture.corre(fixture.S / "proyecto.py", "cambio", self.p, "EV-01", "aprobada", "--fuente", "FU-05")
        self.assertNotEqual(code, 0, out)
        self.assertIn("ya tiene cambios", out)
        self.assertEqual((self.p / "analisis/cambios.md").read_bytes(), cambios)
        self.assertEqual(self.artefactos(), antes)
        mo.escribe(informe, informe.read_text(encoding="utf-8").replace("Estado: aplicado en 1.1", "Estado: pendiente"))
        code, out = fixture.corre(fixture.S / "proyecto.py", "cambio", self.p, "EV-01", "aprobada", "--fuente", "FU-05")
        self.assertEqual(code, 0, out)
        m, _ = self.carga()
        a = base.SimpleNamespace(informe=None, fuente=["FU-98"], decision=[("CAMBIA", "HU-01", "Nuevo texto", "Antes")])
        with self.assertRaisesRegex(SystemExit, "No se abre versión"):
            base.proyecto.comprueba_secuencia_version(m, a)

    def test_huellas_no_cambian_por_reserva_ni_orden(self):
        _, plan = self.preparada()
        antes = {i.id: i.esperado["_issue"]["ambito"] for i in plan.issues}
        _, _, plan, _, _ = iss.corrige_dependencias(self.p, "EV-01", "ISS-02", [], "Orden revisado", "Ana")
        plan.reservas["ISS-01"] = "Otra sesión"
        iss.escribe(plan, self.p)
        m, ctx = self.carga()
        actual = iss.calcula(m, ctx, "EV-01")
        self.assertEqual(antes, {i.id: i.esperado["_issue"]["ambito"] for i in actual.issues})


if __name__ == "__main__":
    unittest.main()
