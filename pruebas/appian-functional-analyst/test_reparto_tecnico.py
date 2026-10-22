"""El reparto del técnico entre issues: unidades de párrafo, DT de la Base, pasos manuales de §13 y un objeto que
una issue crea entero y otra solo cambia en una parte. Datos ficticios, sin red."""
import unittest
import test_automejora as base

iss, mo, un, fixture = base.iss, base.mo, base.un, base.fixture

DT_BASE = """**DT-90 — Seguridad de registro de la Base**

| Campo | Contenido |
|---|---|
| **Capa** | Seguridad |
| **Necesidad** | Base |
| **Decisión** | Las reglas de seguridad de registro se crean con el record type |
| **Por qué** | Ficticia |
| **Descartada** | Ninguna |
| **Riesgo** | Ninguno relevante |
| **Depende de** | — |
| **Verificar** | — |
| **Verificado** | No hace falta |

"""

DT_INTERFAZ = DT_BASE.replace("DT-90 — Seguridad de registro de la Base", "DT-91 — Filtro de la pantalla") \
    .replace("| **Necesidad** | Base |", "| **Necesidad** | HU-01 |") \
    .replace("Las reglas de seguridad de registro se crean con el record type",
             "La interfaz `AUT_SolicitudForm` lee el record type `AUT Solicitud`, que es de la Base")

PARRAFO = ("## 5. Estados", "La pantalla `AUT_SolicitudForm` solo la abre la unidad\n"
                            "solicitante con su grupo propio.\n\n## 5. Estados")


class RepartoTecnico(unittest.TestCase):
    setUp = base.Automejora.setUp
    preparada = base.Automejora.preparada

    def calcula(self, *cambios):
        """Aplica los reemplazos (antes, después) al técnico de una unidad preparada y devuelve su plan."""
        self.preparada()
        f = self.p / "analisis/tecnico.md"
        t = f.read_text(encoding="utf-8")
        for antes, despues in cambios:
            self.assertIn(antes, t)
            t = t.replace(antes, despues, 1)
        f.write_text(t, encoding="utf-8", newline="")
        m = mo.Proyecto(self.p)
        return iss.calcula(m, un.Contexto(m), "EV-01")

    @staticmethod
    def de(plan, objeto):
        return next(i for i in plan.issues if objeto in i.objetos)

    @staticmethod
    def la_base(plan):
        return next(i for i in plan.issues if i.comun)

    def test_un_parrafo_partido_va_entero_donde_lo_manda_una_de_sus_lineas(self):
        plan = self.calcula(PARRAFO)
        self.assertIn("solicitante con su grupo propio", self.de(plan, "AUT_SolicitudForm").texto)
        self.assertNotIn("solicitante con su grupo propio", self.la_base(plan).texto)
        self.assertFalse([a for a in plan.avisos if "solicitante con su grupo propio" in a])

    def test_una_vineta_con_continuacion_sangrada_va_entera(self):
        plan = self.calcula(("## 5. Estados", "- `AUT_RevisarForm` solo la ve el técnico de la unidad\n"
                                              "  gestora y nadie más.\n- Otra viñeta suelta de la Base.\n\n## 5. Estados"))
        issue = self.de(plan, "AUT_RevisarForm")
        self.assertIn("técnico de la unidad gestora y nadie más.", issue.texto)
        self.assertNotIn("gestora y nadie más", self.la_base(plan).texto)
        self.assertIn("Otra viñeta suelta de la Base", self.la_base(plan).texto)    # una viñeta nueva no se une a la anterior

    def test_la_marca_otra_unidad_de_la_primera_linea_vale_para_todo_el_parrafo(self):
        plan = self.calcula(("## 5. Estados", "Otra unidad (EV-02). Canal remoto de avisos que se construye\n"
                                              "con su propia unidad y su propio equipo.\n\n## 5. Estados"))
        for i in plan.issues:
            self.assertNotIn("propio equipo", i.texto)
        self.assertFalse([a for a in plan.avisos if "propio equipo" in a or "Canal remoto" in a])

    def test_unir_lineas_es_determinista(self):
        a = self.calcula(PARRAFO)
        m = mo.Proyecto(self.p)
        b = iss.calcula(m, un.Contexto(m), "EV-01")
        self.assertEqual([(i.id, i.version) for i in a.issues], [(i.id, i.version) for i in b.issues])

    def test_una_dt_con_necesidad_base_llega_a_la_base_y_solo_a_ella(self):
        antes = self.preparada()[1]
        version_antes = {i.id: i.version for i in antes.issues}
        self.p_ = None
        f = self.p / "analisis/tecnico.md"
        t = f.read_text(encoding="utf-8")
        f.write_text(t.replace("## 3. Modelo de datos", DT_BASE + "## 3. Modelo de datos", 1), encoding="utf-8", newline="")
        m = mo.Proyecto(self.p)
        plan = iss.calcula(m, un.Contexto(m), "EV-01")
        self.assertIn("DT-90", self.la_base(plan).texto)
        for i in plan.issues:
            if not i.comun:
                self.assertNotIn("DT-90", i.texto)
        self.assertNotEqual(self.la_base(plan).version, version_antes[self.la_base(plan).id])

    def test_una_dt_de_una_interfaz_que_nombra_un_objeto_de_la_base_no_llega_a_la_base(self):
        antes = self.preparada()[1]
        version_antes = {i.id: i.version for i in antes.issues}
        f = self.p / "analisis/tecnico.md"
        t = f.read_text(encoding="utf-8")
        f.write_text(t.replace("## 3. Modelo de datos", DT_INTERFAZ + "## 3. Modelo de datos", 1), encoding="utf-8", newline="")
        m = mo.Proyecto(self.p)
        plan = iss.calcula(m, un.Contexto(m), "EV-01")
        self.assertNotIn("DT-91", self.la_base(plan).texto)
        self.assertIn("DT-91", self.de(plan, "AUT_GenerarNumero").texto)      # la de HU-01
        self.assertEqual(self.la_base(plan).version, version_antes[self.la_base(plan).id])

    def test_un_paso_manual_de_13_va_a_la_issue_de_su_objeto_y_si_no_nombra_ninguno_a_la_base(self):
        manual = "Manual: calendario de procesos y buzón del organismo en cada entorno.\n"
        plan = self.calcula((manual, manual + "\n- Cargar la plantilla de `AUT_PlantillaAutorizacion` en la carpeta del organismo.\n\n"
                                              "Con preguntas sin respuesta se construye con un supuesto:\n\n"
                                              "| Pregunta | Se construye con | Dónde cambia |\n|---|---|---|\n"
                                              "| PC-90 | Un valor | `AUT_GenerarNumero` |\n\n"
                                              "**Reglas para quien construye**\n\nImportes siempre en euros.\n"))
        self.assertIn("Cargar la plantilla de", self.de(plan, "AUT_PlantillaAutorizacion").texto)
        self.assertNotIn("Cargar la plantilla de", self.la_base(plan).texto)
        self.assertIn("calendario de procesos", self.la_base(plan).texto)
        for i in plan.issues:
            self.assertNotIn("Con preguntas sin respuesta", i.texto)       # presenta una tabla, no es un paso
            self.assertEqual(i.texto.count("Importes siempre en euros"), 1, i.id)    # las reglas generales siguen su camino

    def test_una_linea_de_un_objeto_creado_entero_no_va_a_la_issue_que_solo_cambia_una_parte(self):
        # AUT Solicitud: la Base lo crea; la issue de HU-07 solo le añade la acción «Adjuntar informe del organismo»
        plan = self.calcula(("### 3.2 AUT Documento", "- Título del registro: número y asunto (HU-07).\n"
                                                      "- La acción «Adjuntar informe del organismo» se ofrece al técnico (HU-07).\n\n"
                                                      "### 3.2 AUT Documento"))
        con_parte = next(i for i in plan.issues if any("Adjuntar" in o for f in i.filas for o in f["objetos"]))
        self.assertFalse(con_parte.comun)
        self.assertNotIn("Título del registro", con_parte.texto)
        self.assertIn("Título del registro", self.la_base(plan).texto)
        self.assertIn("se ofrece al técnico", con_parte.texto)


if __name__ == "__main__":
    unittest.main()
