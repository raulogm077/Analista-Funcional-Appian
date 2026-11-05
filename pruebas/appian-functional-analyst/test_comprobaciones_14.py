"""Las comprobaciones de técnico §14 llegan enteras a la issue y al QA. Datos ficticios, sin red.

Proyecto de formación del 5-nov (campaña del método de punta a punta): HU-01.4 y HU-08.1 tenían dos filas en §14, el
caso de prueba de su regla y su efecto en la pantalla con SAIL. La issue se quedaba con la primera, el escenario salía
como @caso-de-prueba y el QA no lo recorría. Y lo que §14 dice de cómo se prueba no llegaba al QA, que solo lee el .feature.
"""
import re
import unittest
import test_automejora as base

iss, mo, un, fixture = base.iss, base.mo, base.un, base.fixture


class Comprobaciones14(unittest.TestCase):
    setUp = base.Automejora.setUp
    preparada = base.Automejora.preparada

    def feature_de(self, plan, cid):
        return next(i.feature for i in plan.issues if cid in i.criterios)

    def test_un_criterio_con_su_regla_y_su_efecto_va_al_qa(self):
        _, plan = self.preparada()
        # solo con el caso de prueba de su regla: lo prueba ese caso, no el QA
        self.assertRegex(self.feature_de(plan, "HU-01.2"), r"@caso-de-prueba\s+Escenario: HU-01\.2")
        f = self.p / "analisis/tecnico.md"
        t = f.read_text(encoding="utf-8")
        fila = "| HU-01.2 | Dos envíos a la vez no repiten número | Caso de prueba de `AUT_GenerarNumero` |\n"
        self.assertIn(fila, t)
        f.write_text(t.replace(fila, fila + "| HU-01.2 (efecto) | Los dos envíos salen en la lista con números distintos | "
                                     "SAIL CLI y revisión del buzón de prueba, con dos cuentas |\n", 1), encoding="utf-8", newline="")
        m = mo.Proyecto(self.p)
        plan = iss.calcula(m, un.Contexto(m), "EV-01")
        feature = self.feature_de(plan, "HU-01.2")
        self.assertNotRegex(feature, r"@caso-de-prueba\s+Escenario: HU-01\.2")
        bloque = re.search(r"Escenario: HU-01\.2\n((?:[ ]+#.*\n)+)", feature)
        self.assertTrue(bloque, feature)
        self.assertIn("Caso de prueba de `AUT_GenerarNumero`", bloque.group(1))
        # lo que añade la celda «Con qué» al SAIL (el buzón, las cuentas) llega también
        self.assertIn("SAIL CLI (QA de la unidad) y revisión del buzón de prueba, con dos cuentas: Los dos envíos salen en la "
                      "lista con números distintos", bloque.group(1))
        self.assertNotIn("HU-01.2", " ".join(a for a in iss.avisos_qa(m.raiz, plan) if "caso de prueba de regla" in a))

    def test_como_se_prueba_llega_al_qa_en_el_feature(self):
        _, plan = self.preparada()
        # HU-02.1 no tiene «Con qué»: va solo cómo se prueba, también lo del perfil que no puede
        self.assertRegex(self.feature_de(plan, "HU-02.1"), r"Escenario: HU-02\.1\n[ ]+# Técnico §14: Usuario de la unidad A "
                         r"no ve solicitudes de la B \(perfil que puede y perfil que no\)\n")


if __name__ == "__main__":
    unittest.main()
