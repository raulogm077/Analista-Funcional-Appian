"""Sin cita explícita desde su especificación, una DT nueva solo cambia la huella de las issues cuyos requisitos cita
su «Necesidad», no las de los objetos que nombra en su texto. Datos ficticios, sin red."""
import re
import unittest
import test_automejora as base

iss, mo, un, fixture = base.iss, base.mo, base.un, base.fixture


class HuellaDeLaDecision(unittest.TestCase):
    setUp = base.Automejora.setUp
    preparada = base.Automejora.preparada

    def versiones(self):
        m = mo.Proyecto(self.p)
        return {i.id: i.version for i in iss.calcula(m, un.Contexto(m), "EV-01").issues}

    def añade_dt(self, necesidad):
        f = self.p / "analisis/tecnico.md"
        t = f.read_text(encoding="utf-8")
        dt = ("**DT-90 — Decisión ficticia**\n\n| Campo | Contenido |\n|---|---|\n| **Capa** | Interfaz |\n"
              f"| **Necesidad** | {necesidad} |\n"
              "| **Decisión** | `AUT_FichaSolicitud` consulta `AUT Solicitud` y usa `AUT_GenerarNumero` |\n"
              "| **Por qué** | Prueba (BP 01 §1.1) |\n| **Descartada** | — |\n| **Riesgo** | Ninguno relevante |\n"
              "| **Depende de** | — |\n| **Verificar** | — |\n| **Verificado** | No hace falta |\n\n")
        i = re.search(r"^## 3\. ", t, re.M).start()
        f.write_text(t[:i] + dt + t[i:], encoding="utf-8", newline="")

    def test_nombrar_un_objeto_no_cuenta_solo_la_necesidad(self):
        self.preparada()
        antes = self.versiones()
        self.añade_dt("HU-06")      # la HU de ISS-03; el texto nombra objetos de la Base, de ISS-02 y de ISS-03
        despues = self.versiones()
        cambian = {k for k in antes if antes[k] != despues[k]}
        self.assertEqual(cambian, {"ISS-03"}, (antes, despues))

    def test_una_regla_compartida_alcanza_a_las_issues_que_la_citan(self):
        self.preparada()
        antes = self.versiones()
        self.añade_dt("RB-01")      # sin citar la HU: la citan los criterios de ISS-05
        despues = self.versiones()
        cambian = {k for k in antes if antes[k] != despues[k]}
        self.assertEqual(cambian, {"ISS-05"}, (antes, despues))


if __name__ == "__main__":
    unittest.main()
