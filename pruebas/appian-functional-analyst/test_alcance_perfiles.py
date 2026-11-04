"""comprobar.py: con el técnico «completo», §14 exige los criterios de la unidad en curso (también la primera) y no los
de toda la aplicación; «Aplicación» vale como perfil de una historia. Datos ficticios, sin red."""
import re
import unittest
import test_automejora as base

iss, mo, un, fixture = base.iss, base.mo, base.un, base.fixture


class AlcanceYPerfiles(unittest.TestCase):
    setUp = base.Automejora.setUp
    preparada = base.Automejora.preparada

    def comprueba(self):
        code, out = fixture.corre(fixture.S / "comprobar.py", self.p)
        return code, chr(10).join(l for l in out.splitlines() if "técnico §14: cada criterio de aceptación" in l
                               or "perfiles de las historias" in l)

    def completo(self):
        f = self.p / "analisis/tecnico.md"
        t = f.read_text(encoding="utf-8")
        t = t.replace("| Nuevo | — | | PAN-01 |", "| Nuevo | — | | Base |").replace("| ACT-07 |", "| Base |")
        t = re.sub(r"Estado: [^\n]+", "Estado: completo", t, count=1)
        f.write_text(t, encoding="utf-8", newline="")

    def linea_14(self, texto):
        return next(l for l in self.p.joinpath("analisis/tecnico.md").read_text(encoding="utf-8").splitlines()
                    if l.startswith("| " + texto))

    def test_14_pide_lo_de_la_unidad_y_no_lo_de_otras_con_la_primera_unidad(self):
        self.preparada()
        self.completo()
        f = self.p / "analisis/tecnico.md"
        t = f.read_text(encoding="utf-8")
        fuera = self.linea_14("HU-09.1")           # HU-09 no es de la unidad: no se exige
        f.write_text(t.replace(fuera + "\n", ""), encoding="utf-8", newline="")
        code, out = self.comprueba()
        self.assertNotIn("HU-09.1", out, out)
        self.assertEqual(code, 0, out)
        propia = self.linea_14("HU-07.1")
        f.write_text(f.read_text(encoding="utf-8").replace(propia + "\n", ""), encoding="utf-8", newline="")
        code, out = self.comprueba()
        self.assertIn("✗ técnico §14: cada criterio de aceptación (de las historias que tocan las unidades): 2 → HU-07.1, HU-07.2", out)
        self.assertEqual(code, 1)

    def test_aplicacion_es_perfil_de_una_historia_sin_darla_de_alta(self):
        self.preparada()
        f = self.p / "analisis/funcional.md"
        t = f.read_text(encoding="utf-8")
        i = t.index("**HU-09 ")
        j = t.index("\n|---", i)
        fila = t.index("\n", j + 1) + 1
        fin = t.index("\n", fila)
        t = t[:fila] + re.sub(r"^\| [^|]+ \|", "| Aplicación |", t[fila:fin]) + t[fin:]
        f.write_text(t, encoding="utf-8", newline="")
        code, out = self.comprueba()
        self.assertIn("✓ perfiles de las historias que están en §2", out)


if __name__ == "__main__":
    unittest.main()
