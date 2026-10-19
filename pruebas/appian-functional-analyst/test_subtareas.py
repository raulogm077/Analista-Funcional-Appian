"""Avance por pasos con una sola issue, reserva y verificación. Datos ficticios, sin red."""
import unittest
import test_automejora as base

iss, mo, un, fixture = base.iss, base.mo, base.un, base.fixture


class Subtareas(unittest.TestCase):
    setUp = base.Automejora.setUp
    preparada = base.Automejora.preparada

    def carga(self):
        m = mo.Proyecto(self.p)
        return iss.calcula(m, un.Contexto(m), "EV-01")

    def archivos(self):
        return {str(f.relative_to(self.p)): f.read_bytes() for f in (self.p / "construccion").rglob("*") if f.is_file()}

    def test_reparto_completo_sin_duplicar_y_conserva_todas_las_filas(self):
        _, plan = self.preparada()
        i = plan.issues[0]
        tareas = iss.subtareas(i)
        self.assertEqual([x["paso"] for x in tareas], ["1", "2"])
        self.assertEqual(sum(x["objetos"].count("`AUT Solicitud`") for x in tareas), 1)
        tecnico = self.p / "analisis/tecnico.md"
        texto = tecnico.read_text(encoding="utf-8")
        fila = next(l for l in texto.splitlines() if l.startswith("| 2 | `AUT Documento`"))
        mo.escribe(tecnico, texto.replace(fila, fila + "\n" + fila.replace("| 2 |", "| 8 |").replace(
            "| Record type |", "| Revisión adicional del registro |")))
        i = self.carga().issues[0]
        o = "AUT Documento"
        tareas = iss.subtareas(i)
        self.assertEqual(sum(x["objetos"].count("`" + o + "`") for x in tareas), 1)
        self.assertIn("pasos 2, 8", " ".join(x["objetos"] for x in tareas))
        self.assertIn("| `AUT Documento` | Record type |", i.texto)
        self.assertIn("| `AUT Documento` | Revisión adicional del registro |", i.texto)
        self.assertIn("## Subtareas por paso", i.texto)
        self.assertIn("todas sus instrucciones", i.texto)

    def test_guardar_retomar_deshacer_sin_cambiar_encargo_reserva_o_verificacion(self):
        _, plan = self.preparada()
        plan.reservas["ISS-01"] = "Ana · 2026-10-19"
        iss.escribe(plan, self.p)
        antes = self.archivos()
        _, _, p, i, _ = iss.marca_subtarea(self.p, "EV-01", "ISS-01", "1", "hecha", "Ana")
        self.assertEqual(p.reservas, plan.reservas)
        self.assertEqual(i.esperado, plan.issues[0].esperado)
        self.assertEqual({k: v for k, v in self.archivos().items() if not k.endswith("indice.md")},
                         {k: v for k, v in antes.items() if not k.endswith("indice.md")})
        p = self.carga()
        self.assertEqual(p.avances[0]["quien"], "Ana")
        self.assertTrue(p.avances[0]["cuando"])
        self.assertIn("Siguiente subtarea pendiente: 2", "\n".join(iss.texto_avance(p, p.issues[0])))
        self.assertFalse(iss.estados(p, self.p)["ISS-01"][0])
        _, _, p, i, _ = iss.marca_subtarea(self.p, "EV-01", "ISS-01", "1", "pendiente", "Ana")
        self.assertIn("Siguiente subtarea pendiente: 1", "\n".join(iss.texto_avance(p, i)))
        self.assertEqual(p.avances[0]["avance"], "pendiente")

    def test_todas_hechas_no_cierran_ni_desbloquean_dependientes(self):
        _, plan = self.preparada()
        for t in iss.subtareas(plan.issues[0]):
            _, _, p, i, _ = iss.marca_subtarea(self.p, "EV-01", "ISS-01", t["paso"], "hecha", "Constructor")
        self.assertIn("queda verificar", "\n".join(iss.texto_avance(p, i)))
        self.assertFalse(iss.estados(p, self.p)["ISS-01"][0])
        self.assertEqual(iss.elige(p, self.p).id, "ISS-01")
        self.assertIn("ISS-01", p.issues[1].depende)
        self.assertFalse((self.p / "construccion/EV-01/verificacion").exists())

    def test_encargo_cambia_conserva_revisar_y_necesita_nueva_marca(self):
        m, plan = self.preparada()
        i = next(i for i in plan.issues if "HU-01" in i.requisitos)
        paso = iss.subtareas(i)[0]["paso"]
        iss.marca_subtarea(self.p, "EV-01", i.id, paso, "hecha", "Ana")
        f = m.ruta("F")
        original = f.read_text(encoding="utf-8")
        titulo = m.piezas["HU-01"].titulo
        mo.escribe(f, original.replace(titulo, titulo + " revisión del encargo", 1))
        p = self.carga()
        self.assertTrue(p.avances[0]["estado"].startswith("Revisar"))
        nuevo = next(x for x in p.issues if x.id == i.id)
        self.assertIn("Avance anterior para revisar", "\n".join(iss.texto_avance(p, nuevo)))
        iss.escribe(p, self.p)
        mo.escribe(f, original)
        p = self.carga()
        self.assertTrue(p.avances[0]["estado"].startswith("Revisar"))
        _, _, p, _, _ = iss.marca_subtarea(self.p, "EV-01", i.id, paso, "hecha", "Bea")
        self.assertEqual(len(p.avances), 2)
        self.assertEqual(p.avances[-1]["estado"], "Vigente")
        self.assertEqual(p.avances[0]["quien"], "Ana")

    def test_cambio_reparto_y_issue_retirada_no_pierden_rastro(self):
        _, plan = self.preparada()
        _, _, p, i, _ = iss.marca_subtarea(self.p, "EV-01", "ISS-01", "1", "hecha", "Ana")
        for f in i.filas:
            if f["paso"] == "1":
                f["paso"] = "3"
        iss.revisa_avances(p)
        self.assertTrue(p.avances[0]["estado"].startswith("Revisar"))
        p.issues = [x for x in p.issues if x.id != i.id]
        iss.revisa_avances(p)
        self.assertEqual(len(p.avances), 1)

    def test_issue_pequena_sin_ruido_y_marcas_invalidas_no_escriben(self):
        _, plan = self.preparada()
        pequena = next(i for i in plan.issues if not iss.subtareas(i))
        self.assertNotIn("## Subtareas por paso", pequena.texto)
        self.assertEqual(iss.texto_avance(plan, pequena), [])
        antes = self.archivos()
        for iid, paso in ((pequena.id, "5"), ("ISS-01", "999"), ("ISS-99", "1")):
            with self.assertRaises(iss.NoSePuede):
                iss.marca_subtarea(self.p, "EV-01", iid, paso, "hecha", "Ana")
            self.assertEqual(self.archivos(), antes)

    def test_cli_desatendido_y_siguiente_conservan_una_issue(self):
        _, plan = self.preparada()
        code, out = fixture.corre(fixture.S / "indice.py", "issues", self.p, "EV-01", "ISS-01", "--subtarea", "1",
                                  "--avance", "hecha", "--quien", "Constructor", "--desatendida")
        self.assertEqual(code, 0, out)
        self.assertIn("Siguiente subtarea pendiente: 2", out)
        antes = self.archivos()
        for extra in (("--regresion",), ("--manual", "--motivo", "No"), ("--depende-de", "ninguna")):
            code, out = fixture.corre(fixture.S / "indice.py", "issues", self.p, "EV-01", "ISS-01", "--subtarea", "1",
                                      "--avance", "hecha", *extra)
            self.assertNotEqual(code, 0, out)
            self.assertEqual(self.archivos(), antes)
        code, out = fixture.corre(fixture.S / "indice.py", "issues", self.p, "EV-01", "--siguiente", "--quien", "Constructor")
        self.assertEqual(code, 0, out)
        self.assertIn("ISS-01", out)
        self.assertIn("Siguiente subtarea pendiente: 2", out)
        self.assertEqual(len(self.carga().issues), len(plan.issues))

    def test_anotacion_incompleta_no_se_pierde_al_regenerar(self):
        self.preparada()
        iss.marca_subtarea(self.p, "EV-01", "ISS-01", "1", "hecha", "Ana")
        f = self.p / "construccion/EV-01/indice.md"
        mo.escribe(f, f.read_text(encoding="utf-8").replace("| Ana |", "|"))
        antes = self.archivos()
        m = mo.Proyecto(self.p)
        with self.assertRaisesRegex(iss.NoSePuede, "fila incompleta"):
            iss.genera(m, un.Contexto(m), "EV-01")
        self.assertEqual(self.archivos(), antes)


if __name__ == "__main__":
    unittest.main()
