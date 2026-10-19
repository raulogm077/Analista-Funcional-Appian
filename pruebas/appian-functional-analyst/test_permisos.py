"""Contrato técnico y aceptación humana acotada de permisos, sin red ni Appian."""
import json
import unittest
import unittest.mock

import test_automejora as compartido
fixture, iss, mo, un = compartido.fixture, compartido.iss, compartido.mo, compartido.un


class Permisos(unittest.TestCase):
    setUp = compartido.Automejora.setUp
    preparada = compartido.Automejora.preparada

    def hallazgo(self, issue, real="grupo-2", pruebas=None):
        h = {"comprobacion": "configuración de visibilidad de Abrir",
             "esperado": {"gruposReferenciados": ["grupo-1"]}, "real": {"gruposReferenciados": [real]}}
        f = fixture.verifica(self.p, "EV-01", issue.id, pruebas=pruebas,
                             **{issue.objetos[0]: {"permisosDiferentes": [h]}})
        v = json.loads(f.read_text(encoding="utf-8"))
        v["entorno"] = "https://demo.example.com"
        for n, obj in enumerate(v["objetos"]): obj["uuid"] = f"objeto-ficticio-{n}"
        f.write_text(json.dumps(v), encoding="utf-8")
        return f, v, iss.hallazgos_permisos(v)[0]["hallazgo"]

    def test_tecnico_conserva_contrato_grupos_y_declaracion_accion(self):
        _, plan = self.preparada()
        t = self.p / "analisis" / "tecnico.md"
        texto = t.read_text(encoding="utf-8")
        texto = texto.replace("## 5.", "| Proceso | Rol Appian | Grupos |\n|---|---|---|\n"
            "| `AUT Tramitar Solicitud` | viewer | `AUT Técnicos`; `AUT Consulta` |\n"
            "| `AUT Tramitar Solicitud` | initiator | — |\n"
            "| `AUT Tramitar Solicitud` | editor | |\n\n## 5.")
        texto = texto.replace("## 8.", "Acciones de registro de `AUT Solicitud`:\n\n"
            "| Acción | Tipo | Proceso | Quién la ve | Visibilidad verificable |\n|---|---|---|---|---|\n"
            "| «Adjuntar informe del organismo» | Relacionada | `AUT Tramitar Solicitud` | Técnicos | EXPRESSION: true() |\n\n## 8.")
        t.write_text(texto, encoding="utf-8")
        m = mo.Proyecto(self.p)
        esperado = un.Contexto(m).esperado("EV-01")
        p = esperado["AUT Tramitar Solicitud"]["permisosInicio"]
        self.assertEqual(p[0]["grupos"], ["AUT Técnicos", "AUT Consulta"])
        self.assertEqual(p[1]["grupos"], [])
        self.assertIsNone(p[2]["grupos"])
        self.assertEqual(esperado["AUT Solicitud"]["acciones"][0]["visibilidad"],
                         {"declaracion": "Técnicos", "configuracion": "EXPRESSION: true()"})
        base = next(i for i in plan.issues if i.comun)
        posterior = next(i for i in plan.issues if i is not base and "AUT Solicitud" in i.objetos)
        self.assertNotIn("acciones", un.Contexto(m).esperado("EV-01", base.filas)["AUT Solicitud"])
        self.assertIn("acciones", un.Contexto(m).esperado("EV-01", posterior.filas)["AUT Solicitud"])

    def test_sin_tabla_pm_no_cambia_esperado_con_metadata_vacia(self):
        m, _ = self.preparada()
        self.assertEqual(un.Contexto(m).esperado("EV-01")["AUT Tramitar Solicitud"], {"tipo": "processModel"})

    def test_aceptar_revocar_no_modifica_verificacion_ni_salva_otro_fallo(self):
        _, plan = self.preparada()
        issue = plan.issues[0]
        f, v, per = self.hallazgo(issue)
        v["objetos"][0]["diferencias"]["permisosDiferentes"][0]["esperado"]["grupos"] = ["DEM Área |  Norte"]
        f.write_text(json.dumps(v), encoding="utf-8")
        per = iss.hallazgos_permisos(v)[0]["hallazgo"]
        antes = f.read_bytes()
        self.assertFalse(iss.estado(self.p, "EV-01", issue)[0])
        self.assertIn(per, iss.estado(self.p, "EV-01", issue)[1])
        iss.acepta_permiso(self.p, "EV-01", issue.id, per, "Comportamiento revisado y aceptado", "Ana")
        self.assertEqual(f.read_bytes(), antes)
        hecha, razon = iss.estado(self.p, "EV-01", issue)
        self.assertTrue(hecha, razon)
        self.assertIn("aceptada por Ana", razon)
        marca = iss.permisos_de(self.p, "EV-01")[0]
        self.assertEqual(marca["version"], issue.version)
        self.assertTrue(marca["cuando"] and marca["detalle"] and marca["motivo"])
        detalle = json.loads(marca["detalle"])
        self.assertEqual(detalle["entorno"], v["entorno"])
        self.assertEqual(detalle["esperado"]["grupos"], ["DEM Área |  Norte"])
        v["objetos"][0]["diferencias"]["tipo"] = {"esperado": "recordType", "real": "group"}
        f.write_text(json.dumps(v), encoding="utf-8")
        self.assertFalse(iss.estado(self.p, "EV-01", issue)[0])
        del v["objetos"][0]["diferencias"]["tipo"]
        f.write_text(json.dumps(v), encoding="utf-8")
        iss.acepta_permiso(self.p, "EV-01", issue.id, per, None, "Ana", retirar=True)
        self.assertFalse(iss.estado(self.p, "EV-01", issue)[0])
        self.assertTrue(iss.permisos_de(self.p, "EV-01")[0]["estado"].startswith("Revocada por Ana"))

    def test_otro_hallazgo_entorno_uuid_o_version_vuelve_a_bloquear(self):
        _, plan = self.preparada()
        issue = plan.issues[0]
        f, v, per = self.hallazgo(issue)
        iss.acepta_permiso(self.p, "EV-01", issue.id, per, "Aceptado", "Ana")
        original = json.dumps(v)
        for cambia in (lambda x: x.update(entorno="https://otro.example.com"),
                       lambda x: x["objetos"][0].update(uuid="otro-objeto"),
                       lambda x: x["objetos"][0]["diferencias"]["permisosDiferentes"][0].update(real={"gruposReferenciados": ["grupo-3"]})):
            dato = json.loads(original)
            cambia(dato)
            f.write_text(json.dumps(dato), encoding="utf-8")
            self.assertFalse(iss.estado(self.p, "EV-01", issue)[0])
        f.write_text(original, encoding="utf-8")
        issue.version = "otra-version"
        self.assertFalse(iss.estado(self.p, "EV-01", issue)[0])

    def test_manual_issue_y_unidad_no_saltan_permisos(self):
        _, plan = self.preparada()
        issue = plan.issues[0]
        _, _, per = self.hallazgo(issue)
        iss.cierre_manual(self.p, "EV-01", issue.id, "Revisión de objetos", "Ana")
        self.assertFalse(iss.estado(self.p, "EV-01", issue)[0])
        code, out = fixture.corre(fixture.S / "proyecto.py", "cambio", self.p, "EV-01", "construida", "--manual")
        self.assertNotEqual(code, 0, out)
        self.assertIn(per, out)
        iss.acepta_permiso(self.p, "EV-01", issue.id, per, "Permiso aceptado", "Ana")
        self.assertTrue(iss.estado(self.p, "EV-01", issue)[0])

    def test_aceptacion_no_salta_pruebas_ni_qa(self):
        _, plan = self.preparada()
        issue = next(i for i in plan.issues if i.criterios and i.esperado["_issue"].get("casosExigidos"))
        objeto = issue.esperado["_issue"]["casosExigidos"][0]
        f, v, per = self.hallazgo(issue, pruebas=fixture.pruebas_de((objeto, "issue", ["Caso"], [])))
        iss.acepta_permiso(self.p, "EV-01", issue.id, per, "Permiso aceptado", "Ana")
        self.assertIn("fallan sus pruebas", iss.estado(self.p, "EV-01", issue)[1])
        v["pruebas"] = fixture.pruebas_de((objeto, "issue", [], []))
        f.write_text(json.dumps(v), encoding="utf-8")
        qa = self.p / "qa" / "EV-01" / "resultado.json"
        qa.parent.mkdir(parents=True)
        qa.write_text(json.dumps({"escenarios": {issue.criterios[0]: {"resultado": "falla", "motivo": "Oculto",
                                                                  "versionIssue": issue.version}}}), encoding="utf-8")
        self.assertIn("falla en QA", iss.estado(self.p, "EV-01", issue)[1])

    def test_cli_exige_persona_motivo_y_hallazgo_vigente(self):
        _, plan = self.preparada()
        issue = plan.issues[0]
        _, _, per = self.hallazgo(issue)
        for args in (("--aceptar-permiso", per),
                     ("--aceptar-permiso", per, "--motivo", "Revisado", "--desatendida"),
                     ("--revocar-permiso", per, "--desatendida"),
                     ("--aceptar-permiso", "PER-inventado", "--motivo", "Revisado")):
            c, out = fixture.corre(fixture.S / "indice.py", "issues", self.p, "EV-01", issue.id, *args)
            self.assertNotEqual(c, 0, out)
        self.assertEqual(iss.permisos_de(self.p, "EV-01"), [])
        c, out = fixture.corre(fixture.S / "indice.py", "issues", self.p, "EV-01", issue.id,
                               "--aceptar-permiso", per, "--motivo", "Revisado", "--quien", "Ana")
        self.assertEqual(c, 0, out)
        self.assertIn("aceptada por Ana", out)

    def test_no_comprobado_es_aviso_y_no_aceptable(self):
        _, plan = self.preparada()
        issue = plan.issues[0]
        fixture.verifica(self.p, "EV-01", issue.id, **{issue.objetos[0]: {"permisosNoComprobados": ["RULES no legible"]}})
        hecha, razon = iss.estado(self.p, "EV-01", issue)
        self.assertTrue(hecha, razon)
        self.assertIn("permisos no comprobados", razon)
        with self.assertRaises(iss.NoSePuede):
            iss.acepta_permiso(self.p, "EV-01", issue.id, "PER-inventado", "Aceptado", "Ana")

    def test_hallazgo_ilegible_no_se_limpia_sin_aviso(self):
        _, plan = self.preparada()
        issue = plan.issues[0]
        for mal in ("texto", [None], [{"comprobacion": "visibilidad"}], [{"comprobacion": "visibilidad", "esperado": None, "real": {}}]):
            fixture.verifica(self.p, "EV-01", issue.id, **{issue.objetos[0]: {"permisosDiferentes": mal}})
            self.assertIn("permisos no comprobados", iss.estado(self.p, "EV-01", issue)[1])

    def test_caducidad_conserva_historial_al_regenerar(self):
        _, plan = self.preparada()
        issue = plan.issues[0]
        _, _, per = self.hallazgo(issue)
        iss.acepta_permiso(self.p, "EV-01", issue.id, per, "Aceptación anterior", "Ana")
        fixture.editar(self.p / "analisis" / "tecnico.md", "## 14.",
                       "Reglas para quien construye: nueva instrucción de la misma unidad.\n\n## 14.")
        m = mo.Proyecto(self.p)
        nuevo, _, _ = iss.genera(m, un.Contexto(m), "EV-01")
        marca = iss.permisos_de(self.p, "EV-01")[0]
        self.assertEqual(marca["estado"], "Caducada")
        self.assertEqual(marca["version"], issue.version)
        self.assertEqual(marca["motivo"], "Aceptación anterior")


if __name__ == "__main__":
    unittest.main()
