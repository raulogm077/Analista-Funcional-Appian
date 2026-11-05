"""Lo que el técnico dice de otra unidad no va a la Base ni avisa. Datos ficticios, sin red."""
import unittest
import test_automejora as base

iss, mo, un, fixture = base.iss, base.mo, base.un, base.fixture


class OtraUnidad(unittest.TestCase):
    setUp = base.Automejora.setUp
    preparada = base.Automejora.preparada

    def test_la_marca_de_otra_unidad_no_va_a_la_base_ni_avisa(self):
        f = self.p / "analisis/tecnico.md"
        self.preparada()
        t = f.read_text(encoding="utf-8")
        t = t.replace("## 4. Grupos y seguridad",
                      "### 3.4 AUT Registro Ajeno\n\nOtra unidad. Una por mes.\n\n| Campo | Tipo |\n|---|---|\n"
                      "| campoajeno | Text |\n\n## 4. Grupos y seguridad", 1)
        t = t.replace("## 10. Integraciones, documentos e IA",
                      "| Aviso | Qué | A quién | Tipo |\n|---|---|---|---|\n"
                      "| AV-90 | Correo de EV-02 sin marca ni objeto | Buzón ajeno | Texto |\n"
                      "| AV-91 | Correo de control sin marca ni objeto | Buzón de control | Texto |\n\n"
                      "Otra unidad (EV-02). Canal remoto sin objeto.\n\n"
                      "## 10. Integraciones, documentos e IA", 1)
        t = t.replace("## 5. Estados", "En EV-01, mantener la segregación de funciones ya implantada en EV-02.\n\n"
                      "## 5. Estados", 1)
        f.write_bytes((t).encode("utf-8"))
        m = mo.Proyecto(self.p)
        plan = iss.calcula(m, un.Contexto(m), "EV-01")
        aviso = next(a for a in plan.avisos if "no nombran ningún objeto" in a)
        self.assertIn("Correo de control", aviso)
        for ajeno in ("campoajeno", "Canal remoto", "Una por mes"):
            self.assertNotIn(ajeno, aviso)
        self.assertIn("Correo de EV-02", aviso)
        # una mención suelta de otro EV, o «otra unidad» a mitad de frase, no es la marca: sigue en el aviso
        self.assertIn("En EV-01, mantener la segregación", aviso)
        base_issue = next(i for i in plan.issues if i.comun)
        self.assertTrue(base_issue.sueltas)
        self.assertIn("En EV-01, mantener la segregación de funciones ya implantada en EV-02.",
                      "".join(m.docs["T"].lineas[i] for i in base_issue.sueltas))
        self.assertNotIn("campoajeno", "".join(m.docs["T"].lineas[i] for i in base_issue.sueltas
                                               if m.docs["T"].lineas[i].startswith("| campoajeno")))


    def test_no_aplica_solo_en_su_apartado_no_va_a_la_base_ni_avisa(self):
        """Casos A y B. Una condición parcial no es la marca de la plantilla: sigue en el aviso y en la Base."""
        f = self.p / "analisis/tecnico.md"
        self.preparada()
        t = f.read_text(encoding="utf-8")
        f.write_text(t.replace("## 10. Integraciones, documentos e IA",
                               "### 9.8 Canales\n\nNo aplica: ningún canal externo en esta prueba.\n\n"
                               "### 9.9 Canal parcial\n\nNo aplica en este incremento: el canal secundario.\n\n"
                               "## 10. Integraciones, documentos e IA", 1), encoding="utf-8", newline="")
        m = mo.Proyecto(self.p)
        plan = iss.calcula(m, un.Contexto(m), "EV-01", estreno=True)
        aviso = next(a for a in plan.avisos if "no nombran ningún objeto" in a)
        self.assertNotIn("ningún canal externo", aviso)
        self.assertIn("canal secundario", aviso)
        base_issue = next(i for i in plan.issues if i.comun)
        self.assertNotIn("ningún canal externo", base_issue.texto)
        self.assertIn("canal secundario", base_issue.texto)

    def test_caso_de_prueba_en_minuscula_marca_el_escenario(self):
        self.preparada()
        f = self.p / "analisis/tecnico.md"
        t = f.read_text(encoding="utf-8")
        self.assertIn("Caso de prueba de `AUT_GenerarNumero`", t)
        f.write_text(t.replace("Caso de prueba de `AUT_GenerarNumero`", "caso de prueba de `AUT_GenerarNumero`"),
                     encoding="utf-8", newline="")
        m = mo.Proyecto(self.p)
        plan = iss.calcula(m, un.Contexto(m), "EV-01")
        feature = "".join(i.feature for i in plan.issues)
        self.assertRegex(feature, r"@caso-de-prueba\s+Escenario: HU-01\.2")


if __name__ == "__main__":
    unittest.main()
