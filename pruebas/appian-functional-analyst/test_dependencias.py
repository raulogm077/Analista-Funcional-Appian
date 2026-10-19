"""Correcciones humanas del orden, en proyectos ficticios y sin red."""
import unittest
import test_automejora as base

iss, mo, un, fixture = base.iss, base.mo, base.un, base.fixture


class Dependencias(unittest.TestCase):
    setUp = base.Automejora.setUp
    preparada = base.Automejora.preparada

    def carga(self):
        m = mo.Proyecto(self.p)
        return iss.calcula(m, un.Contexto(m), "EV-01")

    def test_corrige_paralelismo_siguiente_y_conserva_version(self):
        _, antes = self.preparada()
        versiones = {i.id: i.version for i in antes.issues}
        _, _, plan, i, _ = iss.corrige_dependencias(self.p, "EV-01", "ISS-02", [], "Objeto externo ya preparado", "Ana")
        self.assertEqual(i.depende, [])
        self.assertIn("ISS-01", i.paralelo)
        self.assertIn("corregidas por una persona", i.texto)
        plan.reservas["ISS-01"] = "Otra persona"
        self.assertEqual(iss.elige(plan, self.p).id, "ISS-02")
        iss.escribe(plan, self.p)
        _, _, _, siguiente, _ = iss.siguiente(self.p, "EV-01", "Ana")
        self.assertEqual(siguiente.id, "ISS-02")
        self.assertEqual(versiones, {i.id: i.version for i in plan.issues})
        recargado = self.carga()
        self.assertEqual(recargado.issues[1].depende, [])
        x = recargado.dependencias[0]
        self.assertEqual((x["quien"], x["motivo"], x["estado"]), ("Ana", "Objeto externo ya preparado", "Vigente"))
        self.assertEqual(set(x["versiones"]), {"ISS-01"})
        self.assertTrue(x["cuando"])

    def test_rechaza_sin_motivo_desatendida_referencias_y_si_misma(self):
        self.preparada()
        iss.escribe(self.carga(), self.p)
        indice = self.p / "construccion/EV-01/indice.md"
        antes = indice.read_bytes()
        for args in (("--depende-de", "ninguna"),
                     ("--depende-de", "ninguna", "--motivo", "Acordado", "--desatendida"),
                     ("--dependencias-automaticas", "--desatendida"),
                     ("--depende-de", "ISS-99", "--motivo", "Acordado"),
                     ("--depende-de", "ISS-02", "--motivo", "Acordado"),
                     ("--depende-de", "ninguna", "--motivo", "Acordado", "--regresion")):
            code, out = fixture.corre(fixture.S / "indice.py", "issues", self.p, "EV-01", "ISS-02", *args)
            self.assertNotEqual(code, 0, out)
            self.assertEqual(indice.read_bytes(), antes)

    def test_ciclo_del_grafo_final_con_dos_correcciones(self):
        self.preparada()
        iss.corrige_dependencias(self.p, "EV-01", "ISS-03", ["ISS-01"], "No utiliza la interfaz", "Ana")
        _, _, plan, _, _ = iss.corrige_dependencias(self.p, "EV-01", "ISS-02", ["ISS-03"], "Leerá su ficha", "Ana")
        self.assertEqual(plan.issues[1].depende, ["ISS-03"])
        indice = self.p / "construccion/EV-01/indice.md"
        antes = indice.read_bytes()
        with self.assertRaisesRegex(iss.NoSePuede, "ciclo"):
            iss.corrige_dependencias(self.p, "EV-01", "ISS-03", ["ISS-02"], "Orden contradictorio", "Ana")
        self.assertEqual(indice.read_bytes(), antes)
        self.assertEqual(self.carga().issues[2].depende, ["ISS-01"])
        with self.assertRaisesRegex(iss.NoSePuede, "ciclo"):
            iss.corrige_dependencias(self.p, "EV-01", "ISS-03", [], None, "Ana", retirar=True)
        self.assertEqual(indice.read_bytes(), antes)

    def test_cambio_aguas_arriba_caduca_con_aviso_y_rastro(self):
        self.preparada()
        _, _, plan, _, _ = iss.corrige_dependencias(self.p, "EV-01", "ISS-02", [], "Base disponible", "Ana")
        plan.issues[0].version = "encargo-nuevo"
        iss.aplica_dependencias(plan)
        self.assertEqual(plan.issues[1].depende, ["ISS-01"])
        self.assertNotIn("ISS-01", plan.issues[1].paralelo)
        self.assertTrue(any("ISS-01" in a and "caducada" in a for a in plan.avisos))
        self.assertTrue(plan.dependencias[0]["estado"].startswith("Caducada"))
        plan.dependencias.append(dict(plan.dependencias[0]))
        iss.aplica_dependencias(plan)
        self.assertEqual(sum("corrección de dependencias caducada" in a for a in plan.avisos), 1)
        plan.dependencias.pop()
        iss.escribe(plan, self.p)
        recargado = self.carga()
        self.assertEqual(recargado.issues[1].depende, ["ISS-01"])
        self.assertEqual(recargado.dependencias[0]["motivo"], "Base disponible")
        code, out = fixture.corre(fixture.S / "indice.py", "issues", self.p, "EV-01", "ISS-02")
        self.assertEqual(code, 0, out)
        self.assertIn("corrección de dependencias caducada", out)
        _, _, revisado, _, _ = iss.corrige_dependencias(self.p, "EV-01", "ISS-02", [], "Revisado de nuevo", "Ana")
        self.assertFalse(any("corrección de dependencias caducada" in a for a in revisado.avisos))
        self.assertIn("antes: Caducada", revisado.dependencias[0]["estado"])
        self.assertEqual(revisado.dependencias[1]["estado"], "Vigente")

    def test_cambio_propio_y_nueva_relacion_automatica_caducan(self):
        self.preparada()
        _, _, plan, _, _ = iss.corrige_dependencias(self.p, "EV-01", "ISS-02", [], "Base disponible", "Ana")
        plan.issues[1].version = "encargo-nuevo"
        iss.aplica_dependencias(plan)
        self.assertIn("cambió su encargo", plan.dependencias[0]["estado"])
        plan = self.carga()
        plan.issues[0].comun = False
        plan.issues[1].nombra.clear()
        plan.issues[0].nombra.clear()
        iss.aplica_dependencias(plan)
        self.assertIn("cambiaron las dependencias calculadas", plan.dependencias[0]["estado"])

    def test_reversion_y_sustitucion_conservan_rastro(self):
        self.preparada()
        for destinos in ([], ["ISS-01"]):
            iss.corrige_dependencias(self.p, "EV-01", "ISS-02", destinos, "Decisión | revisada", "Ana")
        plan = self.carga()
        self.assertEqual(len(plan.dependencias), 2)
        self.assertTrue(plan.dependencias[0]["estado"].startswith("Sustituida"))
        code, out = fixture.corre(fixture.S / "indice.py", "issues", self.p, "EV-01", "ISS-02", "--dependencias-automaticas", "--quien", "Luis")
        self.assertEqual(code, 0, out)
        plan = self.carga()
        self.assertTrue(plan.dependencias[1]["estado"].startswith("Retirada por Luis"))
        self.assertEqual(plan.issues[1].depende, ["ISS-01"])
        self.assertNotIn("corregidas por una persona", plan.issues[1].texto)

    def test_ninguna_cli_y_no_referencias_huerfanas(self):
        self.preparada()
        code, out = fixture.corre(fixture.S / "indice.py", "issues", self.p, "EV-01", "ISS-02", "--depende-de", "ninguna", "--motivo", "Revisado", "--quien", "Ana")
        self.assertEqual(code, 0, out)
        self.assertIn("depende de ninguna", out)
        plan = self.carga()
        plan.issues = plan.issues[1:]
        iss.aplica_dependencias(plan)
        self.assertTrue(plan.dependencias[0]["estado"].startswith("Caducada"))


if __name__ == "__main__":
    unittest.main()
