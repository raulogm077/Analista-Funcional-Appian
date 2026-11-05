"""Una pregunta por fila en «Pendiente de confirmar»: comprobar.py avisa, sin error. Datos ficticios, sin red.

Campaña del 5-nov: en el proyecto de formación, PC-04 y PC-10 juntaban dos preguntas cada una, y quien hizo de cliente
(revisión «¿sirve sin IA?») no podía contestarlas por separado. La regla ya estaba (funcional-plantilla.md §11).
"""
import tempfile
import unittest
from pathlib import Path

import test_automejora as base

fixture = base.fixture


class UnaPreguntaPorFila(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="pc-una-")
        self.addCleanup(self.temp.cleanup)
        self.p = Path(self.temp.name) / "p"
        fixture.nueva_con_issues(self.p)

    def comprueba(self):
        code, out = fixture.corre(fixture.S / "comprobar.py", self.p)
        return code, next((l for l in out.splitlines() if "una sola pregunta por fila" in l), "")

    def test_avisa_de_dos_preguntas_en_una_fila_sin_error(self):
        code, linea = self.comprueba()
        self.assertEqual((code, linea), (0, "✓ pendientes de confirmar con una sola pregunta por fila"))
        f = self.p / "analisis/funcional.md"
        t = f.read_text(encoding="utf-8")
        antes = "| PC-01 | ¿Cuántos años se conservan las solicitudes denegadas? |"
        self.assertIn(antes, t)
        f.write_text(t.replace(antes, "| PC-01 | ¿Cuántos años se conservan las denegadas? ¿Se carga el histórico? |", 1),
                     encoding="utf-8", newline="")
        code, linea = self.comprueba()
        self.assertEqual(code, 0)
        self.assertEqual(linea, "· pendientes de confirmar con una sola pregunta por fila: 1 → PC-01")


if __name__ == "__main__":
    unittest.main()
