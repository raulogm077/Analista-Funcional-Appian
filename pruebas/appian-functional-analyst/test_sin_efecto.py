"""Reaprobación (Raúl, 6-nov; docs/diseno/reaprobacion.md): un informe «sin efecto» no hace crecer la unidad aprobada
salvo sus topes, que van al JP; y con la unidad construida, un técnico que cambia después no devuelve sus issues a
pendiente. Sin red ni Appian."""
import json
import re
import unittest

import test_automejora as compartido
fixture, iss, mo, un = compartido.fixture, compartido.iss, compartido.mo, compartido.un

EFECTO = "Efecto: sin cambio de alcance, esfuerzo ni riesgo"


class SinEfecto(unittest.TestCase):
    setUp = compartido.Automejora.setUp
    preparada = compartido.Automejora.preparada

    def informe(self, efecto=True, tipo="CAMBIA", requiere="—", decision="✔", aplicado="técnico §7", encaja="HU-01",
                extra=""):
        (self.p / "impacto").mkdir(exist_ok=True)
        (self.p / "impacto" / "FU-90.md").write_text(
            "# Impacto de FU-90 · un texto · 2026-11-06\n"
            f"Análisis base: versión 1.1 · Cambio: EV-01 · Estado: aplicado en 1.1{' · ' + EFECTO if efecto else ''}\n\n"
            "## Resumen\n- 1 punto\n- Requieren aprobación: ninguno\n\n## Puntos\n"
            "| # | Tipo | Qué se dice | Encaja en | Cambio propuesto | Revisar también | Requiere | Decisión |\n"
            "|---|---|---|---|---|---|---|---|\n"
            f"| 1 | {tipo} | Otro texto [FU-90] | {encaja} | El texto nuevo | — | {requiere} | {decision} |\n{extra}\n"
            f"## Aplicado\nVersión 1.1: {aplicado}\n", encoding="utf-8")
        return un.Contexto(mo.Proyecto(self.p))

    def test_formatos_validos_y_descartes(self):
        """Revisión de Codex (6-nov): «T §3», una DT en «Encaja en» y un punto descartado; con columna «Cambio», solo
        cuentan los puntos de la unidad."""
        self.preparada()
        tecnico = self.p / "analisis" / "tecnico.md"
        tecnico.write_text(tecnico.read_text(encoding="utf-8") + "\n**DT-99 — Quién ve qué**\n\n| Campo | Contenido |\n"
                           "|---|---|\n| **Capa** | Seguridad |\n", encoding="utf-8")
        ctx = self.informe(aplicado="T §3")
        self.assertTrue(any("§3 (datos)" in x for x in ctx.crecida("EV-01")), ctx.crecida("EV-01"))
        ctx = self.informe(encaja="DT-99", aplicado="técnico §2")
        self.assertTrue(any("DT-99 es de seguridad" in x for x in ctx.crecida("EV-01")), ctx.crecida("EV-01"))
        descartada = "| 2 | ALCANCE+ | Firmar también [FU-90] | PAN-03 | — | — | Sí (alcance) | ✗ Descartado |\n"
        ctx = self.informe(extra=descartada)
        self.assertEqual(ctx.crecida("EV-01"), [])
        (self.p / "impacto" / "FU-90.md").write_text(
            "# Impacto de FU-90\n"
            f"Análisis base: versión 1.1 · Estado: aplicado en 1.1 · {EFECTO}\n\n## Puntos\n"
            "| # | Tipo | Qué se dice | Encaja en | Cambio propuesto | Revisar también | Requiere | Decisión | Cambio |\n"
            "|---|---|---|---|---|---|---|---|---|\n"
            "| 1 | CAMBIA | Otro texto [FU-90] | HU-01 | El texto nuevo | — | — | ✔ | EV-01 |\n"
            "| 2 | ALCANCE+ | Un campo [FU-90] | PAN-03 | Campo nuevo | — | Sí (alcance) | ✔ | EV-02 |\n",
            encoding="utf-8")
        ctx = un.Contexto(mo.Proyecto(self.p))
        self.assertEqual(ctx.crecida("EV-01"), [])
        self.assertEqual(ctx.validados_ia("EV-01"), ["FU-90"])
        # con el resumen «## Aplicado» de todo el informe: lo de EV-02 no para a EV-01 (Codex, 6-nov)
        f = self.p / "impacto" / "FU-90.md"
        f.write_text(f.read_text(encoding="utf-8")
                     + "\n## Aplicado\nEV-01: PAN-01 con otro label · EV-02: técnico §3 con un campo nuevo\n", encoding="utf-8")
        self.assertEqual(un.Contexto(mo.Proyecto(self.p)).crecida("EV-01"), [])
        # un § del funcional no es del técnico: «funcional §4 y técnico §7» no toca seguridad
        ctx = self.informe(aplicado="funcional §4 y técnico §7")
        self.assertEqual(ctx.crecida("EV-01"), [])

    def test_sin_efecto_no_hace_crecer_y_lo_ve_el_jp(self):
        self.preparada()
        ctx = self.informe(efecto=False)
        self.assertEqual(ctx.crecida("EV-01"), ["FU-90"])        # como hasta ahora
        ctx = self.informe()
        self.assertEqual(ctx.crecida("EV-01"), [])
        self.assertEqual(ctx.validados_ia("EV-01"), ["FU-90"])

    def test_los_topes_van_al_jp(self):
        self.preparada()
        tecnico = self.p / "analisis" / "tecnico.md"
        tecnico.write_text(tecnico.read_text(encoding="utf-8") + "\n**DT-99 — Quién ve qué**\n\n| Campo | Contenido |\n"
                           "|---|---|\n| **Capa** | Seguridad |\n", encoding="utf-8")
        for que, kw, tope in (("alcance", {"tipo": "ALCANCE+"}, "de alcance"),
                              ("requiere aprobación", {"requiere": "Sí (alcance)"}, "requiere"),
                              ("pendiente", {"decision": "Pendiente"}, "pendiente"),
                              ("seguridad por sección", {"aplicado": "técnico §4 y §13"}, "§4 (seguridad)"),
                              ("datos por sección", {"aplicado": "técnico §3"}, "§3 (datos)"),
                              ("una DT de seguridad", {"aplicado": "técnico §2 · DT-99"}, "DT-99 es de seguridad")):
            with self.subTest(que):
                ctx = self.informe(**kw)
                crece = ctx.crecida("EV-01")
                self.assertTrue(crece and any(tope in x for x in crece), crece)
                self.assertEqual(ctx.validados_ia("EV-01"), [])
        # el cliente ya aprobó (✔) un cambio sobre algo 🔒: no pide además la del JP (sin doble aprobación)
        ctx = self.informe(requiere="Sí (🔒)")
        self.assertEqual(ctx.crecida("EV-01"), [])
        ctx = self.informe(requiere="Sí (🔒)", decision="Pendiente")
        self.assertTrue(any("pendiente" in x for x in ctx.crecida("EV-01")), ctx.crecida("EV-01"))
        # otra razón, aunque esté aprobada, sigue yendo al JP: la aprobación del cliente no es la del JP (Codex)
        for razon in ("Sí (seguridad)", "Sí (esfuerzo)", "Sí (🔒, seguridad)"):
            ctx = self.informe(requiere=razon)
            self.assertTrue(any("requiere" in x for x in ctx.crecida("EV-01")), (razon, ctx.crecida("EV-01")))

    def test_estructura_con_cambios_reales_del_tecnico(self):
        """La pareja que pidió Codex, con el técnico de verdad: una nota de operación (§12) cambia la versión y no la
        estructura; una línea de §7 que dice qué hace un objeto cambia las dos."""
        m, plan = self.preparada()
        issue = next(i for i in plan.issues if i.criterios and any(" — " not in o for o in i.objetos))
        obj = next(o for o in issue.objetos if " — " not in o)
        antes = issue.esperado["_issue"]
        tecnico = self.p / "analisis" / "tecnico.md"
        def con(linea, seccion):
            texto = tecnico.read_text(encoding="utf-8")
            cab = next(l for l in texto.splitlines() if l.startswith(f"## {seccion}."))
            tecnico.write_text(texto.replace(cab, f"{cab}\n\n- {linea}\n", 1), encoding="utf-8")
            m2 = mo.Proyecto(self.p)
            return next(i for i in iss.calcula(m2, un.Contexto(m2), "EV-01").issues if i.id == issue.id).esperado["_issue"]
        nota = con(f"Se vigila el volumen de `{obj}` cada mes.", "12")
        self.assertNotEqual(nota["version"], antes["version"], "la nota no entró en la issue: la prueba no prueba nada")
        self.assertEqual(nota["estructura"], antes["estructura"])
        real = con(f"`{obj}` filtra por la fecha de fin, no por la de inicio.", "7")
        self.assertNotEqual(real["estructura"], antes["estructura"])

    def test_construida_no_vuelve_a_pendiente_por_el_tecnico(self):
        _, plan = self.preparada()
        issue = next(i for i in plan.issues if i.criterios)
        fixture.verifica(self.p, "EV-01", issue.id)
        self.assertTrue(iss.estado(self.p, "EV-01", issue)[0])
        issue.version = "otra-version"      # solo cambió el texto del técnico: la estructura es la de la verificación
        hecha, motivo = iss.estado(self.p, "EV-01", issue)
        self.assertFalse(hecha)
        self.assertIn("ha cambiado desde su última verificación", motivo)        # aún Aprobada: caduca
        cambios = self.p / "analisis" / "cambios.md"
        texto = cambios.read_text(encoding="utf-8")
        fila = next(l for l in texto.splitlines() if l.startswith("| EV-01"))
        cambios.write_text(texto.replace(fila, re.sub(r"\|\s*Aprobada\s*\|", "| Construida |", fila, count=1)),
                           encoding="utf-8")
        hecha, motivo = iss.estado(self.p, "EV-01", issue)
        self.assertTrue(hecha, motivo)
        self.assertIn("verificada con su versión anterior", motivo)
        # si cambió la estructura (un requisito, un escenario, un objeto…), caduca aunque esté Construida (Codex)
        issue.esperado = {**issue.esperado, "_issue": {**issue.esperado["_issue"], "estructura": "otra"}}
        hecha, motivo = iss.estado(self.p, "EV-01", issue)
        self.assertFalse(hecha)
        self.assertIn("ha cambiado desde su última verificación", motivo)
        issue.esperado["_issue"].update(estructura=json.loads(next(
            (self.p / "construccion" / "EV-01" / "verificacion").glob(f"{issue.id}.json")).read_text(
                encoding="utf-8"))["issue"]["estructura"])
        # pero un fallo de QA de la versión anterior no se pierde por ello (revisión de Codex)
        qa = self.p / "qa" / "EV-01" / "resultado.json"
        qa.parent.mkdir(parents=True, exist_ok=True)
        qa.write_text(json.dumps({"escenarios": {issue.criterios[0]: {
            "resultado": "falla", "motivo": "Oculto", "versionIssue": "antes"}}}), encoding="utf-8")
        hecha, motivo = iss.estado(self.p, "EV-01", issue)
        self.assertFalse(hecha, motivo)
        self.assertIn("falla en QA", motivo)


if __name__ == "__main__":
    unittest.main()
