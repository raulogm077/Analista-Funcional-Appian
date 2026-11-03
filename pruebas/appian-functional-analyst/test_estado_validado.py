"""Estado del DF tras validarlo y la línea de la construcción inicial en `estado` (caso B), en proyectos ficticios."""
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

import selftest as fixture

S = fixture.S


class EstadoValidado(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="validado-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def proyecto(self, nombre, sin_pc=False):
        p = self.tmp / nombre
        shutil.copytree(fixture.EJEMPLO, p)
        (p / "fuentes").mkdir()
        (p / "fuentes" / "indice.json").write_text(json.dumps({"fuentes": [
            {"id": f"FU-0{i}", "fichero": f"f{i}.txt", "tipo": "Transcripción", "detalle": "x",
             "fecha": "2026-09-03 10:00"} for i in (1, 2, 3)] + [
            {"id": "FU-04", "fichero": "v.eml", "tipo": "Correo", "detalle": "validación",
             "fecha": "2026-10-01 09:30"}]}), encoding="utf-8")
        if sin_pc:   # sin preguntas abiertas: lo único que queda sin 🔒 es lo que se valida
            f = p / "analisis" / "funcional.md"
            f.write_text("\n".join(l for l in f.read_text(encoding="utf-8").split("\n")
                                   if not l.startswith(("| PC-01 |", "| PC-02 |"))), encoding="utf-8")
        return p

    def valida(self, p):
        return fixture.corre(S / "proyecto.py", "version", p, "--fuente", "FU-04", "--que", "Validación del DF",
                             "--decision", "VALIDA", "ACT-01 a ACT-08, AV-01 a AV-05, DOC-01 a DOC-02, ESC-01 a ESC-04, "
                             "HU-01 a HU-09, INT-01, PAN-01 a PAN-05, RB-01 a RB-02", "Validado", "—")

    def cabeceras(self, p):
        return ((p / "analisis" / "funcional.md").read_text(encoding="utf-8").split("\n")[2],
                (p / "proyecto.md").read_text(encoding="utf-8").split("\n")[3])

    def test_valida_todo_pone_validado_sin_tocar_la_entrega(self):
        p = self.proyecto("todo", sin_pc=True)
        c, out = self.valida(p)
        self.assertEqual(c, 0, out)
        self.assertIn("«Estado: validado» en el funcional y en proyecto.md", out)
        self.assertEqual(self.cabeceras(p), ("Versión: 1.2 · Estado: validado",
                                             "DF entregado: 1.0 (2026-09-12) · Estado: validado"))

    def test_sin_linea_de_estado_lo_dice_y_no_lo_da_por_escrito(self):
        p = self.proyecto("sin estado", sin_pc=True)
        pm = p / "proyecto.md"
        pm.write_text(pm.read_text(encoding="utf-8").replace(" · Estado: en validación", ""), encoding="utf-8")
        c, out = self.valida(p)
        self.assertEqual(c, 0, out)
        self.assertIn("«Estado: validado» en el funcional.", out)
        self.assertIn("a mano: «Estado: validado» donde falta la línea «Estado:»", out)
        self.assertEqual(self.cabeceras(p)[1], "DF entregado: 1.0 (2026-09-12)")

    def test_con_preguntas_abiertas_no_cambia_y_dice_cuales(self):
        p = self.proyecto("con PC")
        c, out = self.valida(p)
        self.assertEqual(c, 0, out)
        self.assertIn("El DF no pasa a «validado»: quedan sin 🔒 PC-01, PC-02", out)
        self.assertEqual(self.cabeceras(p), ("Versión: 1.2 · Estado: en validación",
                                             "DF entregado: 1.0 (2026-09-12) · Estado: en validación"))

    def test_pantalla_solo_validada_sigue_entre_las_confirmadas(self):
        """Caso B: «estado» decía que el prototipo rehacía una pantalla que el informe solo validaba."""
        p = self.proyecto("validada")
        f = p / "analisis" / "funcional.md"
        f.write_text(re.sub(r"(\*\*PAN-01 — [^*]+\*\* <!-- )✅", r"\1🔒", f.read_text(encoding="utf-8")), encoding="utf-8")
        (p / "impacto").mkdir(exist_ok=True)
        (p / "impacto" / "FU-04.md").write_text(
            "# Impacto de FU-04\nAnálisis base: versión 1.0 · Estado: aplicado en 1.1\n\n## Puntos\n"
            "| # | Tipo | Qué se dice | Encaja en | Cambio propuesto | Revisar también | Requiere | Decisión |\n"
            "|---|---|---|---|---|---|---|---|\n"
            "| 1 | VALIDA | Visto bueno [FU-04 00:01:00] | PAN-01 | — | — | Sí (🔒) | ✔ FU-04 |\n", encoding="utf-8")
        c, out = fixture.corre(S / "proyecto.py", "estado", p)
        self.assertEqual(c, 0, out)
        self.assertNotIn("el prototipo las rehace", out)
        self.assertRegex(next(l for l in out.splitlines() if "--confirmadas" in l), r"--confirmadas .*PAN-01")

    def test_estado_de_la_construccion_inicial(self):
        p = fixture.nueva_con_issues(self.tmp / "inicial")
        fixture.corre(S / "proyecto.py", "iniciar", p)
        (p / "fuentes" / "FU-05-aprobacion.md").write_text("# FU-05\n", encoding="utf-8")
        c, out = fixture.corre(S / "proyecto.py", "cambio", p, "EV-01", "aprobada", "--fuente", "FU-05")
        self.assertEqual(c, 0, out)
        c, out = fixture.corre(S / "proyecto.py", "estado", p)
        self.assertEqual(c, 0, out)
        self.assertRegex(out, r"EV-01 · .* · Aprobada · fuentes: todas las del análisis inicial · versión: 1\.1, al aprobarla")


if __name__ == "__main__":
    unittest.main()
