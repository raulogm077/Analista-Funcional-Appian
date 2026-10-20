"""La pieza compartida espera sin mezclar el texto de dos encargos. Datos ficticios, sin red."""
import json
import unittest
import test_automejora as base

iss, mo, un, fixture = base.iss, base.mo, base.un, base.fixture


class Secuenciacion(unittest.TestCase):
    setUp = base.Automejora.setUp
    preparada = base.Automejora.preparada

    def segunda(self, destino="HU-01", decision="Pendiente", tipo="CAMBIA", contexto="—"):
        code, out = fixture.corre(fixture.S / "proyecto.py", "cambio", self.p, "EV-02", "abrir", "--titulo", "Siguiente entrega")
        self.assertEqual(code, 0, out)
        self.informe(destino, decision, tipo, contexto)

    def informe(self, destino, decision="Pendiente", tipo="CAMBIA", contexto="—"):
        f = self.p / "impacto/FU-99.md"
        f.parent.mkdir(exist_ok=True)
        f.write_text("# Impacto de FU-99\nAnálisis base: versión 1.1 · Cambio: EV-02 · Estado: pendiente\n\n"
                     "## Puntos\n| # | Tipo | Qué se dice | Encaja en | Cambio propuesto | Revisar también | Requiere | Decisión |\n"
                     "|---|---|---|---|---|---|---|---|\n"
                     f"| 1 | {tipo} | Petición ficticia | {destino} | {destino}: revisión posterior | {contexto} | Sí | {decision} |\n",
                     encoding="utf-8")

    def carga(self):
        m = mo.Proyecto(self.p)
        return m, un.Contexto(m)

    def artefactos(self):
        return {str(f.relative_to(self.p)): f.read_bytes() for carpeta in ("construccion", "versiones")
                for f in (self.p / carpeta).rglob("*") if f.is_file()}

    def cambia_titulo(self, pid):
        m, _ = self.carga()
        f = m.ruta("F")
        lineas = f.read_text(encoding="utf-8").splitlines()
        linea = m.piezas[pid].ini
        titulo = m.piezas[pid].titulo
        self.assertIn(titulo, lineas[linea])
        lineas[linea] = lineas[linea].replace(titulo, titulo + " contenido posterior")
        mo.escribe(f, "\n".join(lineas) + "\n")

    def urgencia(self, uid="URG-01", decision="✔ FU-99", registrada=True, donde="Entorno de corrección",
                 informe="URG-01", tipo="Cambio de comportamiento"):
        if registrada:
            code, out = fixture.corre(fixture.S / "proyecto.py", "cambio", self.p, uid, "abrir", "--titulo", "Corrección ficticia")
            self.assertEqual(code, 0, out)
        self.informe("HU-01", decision)
        texto = (self.p / "impacto/FU-99.md").read_text(encoding="utf-8").replace("Cambio: EV-02", "Cambio: " + uid)
        texto += ("\n## Urgencia\n| Campo | Valor |\n|---|---|\n"
                  f"| Tipo | {tipo} |\n| Objetos | `AUT_GenerarNumero` |\n| Dónde se corrige | {donde} |\n")
        (self.p / "impacto/FU-99.md").unlink()
        mo.escribe(self.p / "impacto" / (informe + ".md"), texto)
        fuentes = self.p / "fuentes/indice.json"
        fuentes.parent.mkdir(exist_ok=True)
        cat = json.loads(fuentes.read_text(encoding="utf-8")) if fuentes.exists() else {"fuentes": []}
        cat["fuentes"].append({"id": "FU-99", "fecha": "2026-10-20", "nombre": "Corrección ficticia aprobada"})
        mo.escribe(fuentes, json.dumps(cat))

    def version_urgente(self, informe="URG-01", pieza="HU-01"):
        return fixture.corre(fixture.S / "proyecto.py", "version", self.p, "--fuente", "FU-99", "--que", "Corrección",
                             "--informe", "impacto/" + informe + ".md", "--decision", "CAMBIA", pieza, "Nuevo texto", "Antes")

    def archivos(self):
        return {str(f.relative_to(self.p)): f.read_bytes() for f in self.p.rglob("*") if f.is_file()}

    def test_urgente_aprobada_versiona_sin_esperar_evolutivo(self):
        for donde, decision in (("Entorno de corrección", "✔ FU-99"), ("Pendiente", "✅ FU-99")):
            with self.subTest(donde=donde, decision=decision):
                self.p = self.root / donde
                self.preparada()
                self.urgencia(donde=donde, decision=decision)
                antes = self.artefactos()
                code, out = self.version_urgente()
                self.assertEqual(code, 0, out)
                self.assertIn("Versión 1.2", out)
                _, ctx = self.carga()
                self.assertEqual(ctx.por_id["EV-01"].estado, un.APROBADA)
                self.assertEqual(ctx.por_id["URG-01"].estado, un.ABIERTA)
                self.assertTrue(all(self.artefactos()[k] == v for k, v in antes.items()))
                if donde == "Pendiente":
                    antes = self.archivos()
                    code, out = fixture.corre(fixture.S / "proyecto.py", "cambio", self.p, "URG-01", "produccion", "--ref", "FICTICIO")
                    self.assertNotEqual(code, 0, out)
                    self.assertIn("Dónde se corrige", out)
                    self.assertEqual(self.archivos(), antes)

    def test_prefijo_urg_sin_unidad_o_ficha_y_punto_pendiente_no_eximen(self):
        for caso in ("desconocida", "sin ficha", "sin puntos", "pendiente", "vacía", "descartada", "rechazada", "otra pieza"):
            with self.subTest(caso=caso):
                self.p = self.root / caso
                self.preparada()
                self.urgencia(uid="URG-99" if caso == "desconocida" else "URG-01",
                              registrada=caso != "desconocida", informe="FU-99" if caso == "sin ficha" else "URG-01",
                              decision="Pendiente" if caso == "pendiente" else "" if caso == "vacía"
                              else "✗" if caso == "rechazada" else "✔ FU-99")
                if caso == "sin puntos":
                    f = self.p / "impacto/URG-01.md"
                    texto = f.read_text(encoding="utf-8")
                    ini, fin = texto.index("## Puntos"), texto.index("## Urgencia")
                    mo.escribe(f, (texto[:ini] + texto[fin:]).replace("Estado: pendiente", "Estado: aplicado en 1.1")
                               + "\n## Aplicado\nHU-01\n")
                if caso == "descartada":
                    code, out = fixture.corre(fixture.S / "proyecto.py", "cambio", self.p, "URG-01", "descartada")
                    self.assertEqual(code, 0, out)
                antes = self.archivos()
                code, out = self.version_urgente(informe="FU-99" if caso == "sin ficha" else "URG-01",
                                                pieza="HU-03" if caso == "otra pieza" else "HU-01")
                self.assertNotEqual(code, 0, out)
                self.assertIn("sin construir", out)
                self.assertEqual(self.archivos(), antes)

    def test_urgente_parcial_solo_exime_el_punto_aprobado(self):
        for decision in ("Pendiente", ""):
            with self.subTest(decision=decision):
                self.p = self.root / (decision or "vacía")
                self.preparada()
                self.urgencia()
                f = self.p / "impacto/URG-01.md"
                mo.escribe(f, f.read_text(encoding="utf-8").replace("\n\n## Urgencia",
                           f"\n| 2 | CAMBIA | Otra petición | HU-03 | HU-03 posterior | — | Sí | {decision} |\n\n## Urgencia"))
                self.assertEqual(len(mo.lee_informe(f)[1]), 2)
                if decision:
                    # Sin --decision sobre el punto pendiente, el versionado del aprobado sigue disponible.
                    code, out = self.version_urgente()
                    self.assertEqual(code, 0, out)
                else:
                    # Una decisión vacía ya entraba en el ámbito general; no gana la excepción de urgencias.
                    antes = self.archivos()
                    code, out = self.version_urgente()
                    self.assertNotEqual(code, 0, out)
                    self.assertEqual(self.archivos(), antes)
                m, _ = self.carga()
                a = base.SimpleNamespace(informe="impacto/URG-01.md", fuente=["FU-99"],
                                         decision=[("CAMBIA", "HU-03", "Nuevo texto", "Antes")])
                with self.assertRaisesRegex(SystemExit, "sin construir"):
                    base.proyecto.comprueba_secuencia_version(m, a)

    def mixto_urgente(self, independiente=False):
        self.preparada()
        self.urgencia()
        code, out = fixture.corre(fixture.S / "proyecto.py", "cambio", self.p, "EV-02", "abrir", "--titulo", "Otra entrega")
        self.assertEqual(code, 0, out)
        f = self.p / "impacto/URG-01.md"
        texto = f.read_text(encoding="utf-8").replace("| Decisión |", "| Decisión | Cambio |")
        texto = texto.replace("|---|---|---|---|---|---|---|---|", "|---|---|---|---|---|---|---|---|---|")
        fila = ("| 2 | NUEVO | Independiente | — | HU-99 nueva | — | No | ✔ FU-99 | EV-02 |" if independiente else
                "| 2 | CAMBIA | Otra petición | HU-01 | HU-01 posterior | — | Sí | ✔ FU-99 | EV-02 |")
        texto = texto.replace("| ✔ FU-99 |", "| ✔ FU-99 | URG-01 |\n" + fila)
        mo.escribe(f, texto)

    def test_informe_mixto_no_exime_el_evolutivo(self):
        self.mixto_urgente()
        antes = self.archivos()
        code, out = self.version_urgente()
        self.assertNotEqual(code, 0, out)
        self.assertIn("sin construir", out)
        self.assertEqual(self.archivos(), antes)

    def test_informe_mixto_independiente_atribuye_decision_sin_eximir_extras(self):
        self.mixto_urgente(independiente=True)
        antes = self.archivos()
        code, out = self.version_urgente(pieza="HU-03")
        self.assertNotEqual(code, 0, out)
        self.assertIn("sin construir", out)
        self.assertEqual(self.archivos(), antes)
        code, out = self.version_urgente()
        self.assertEqual(code, 0, out)
        self.assertIn("Versión 1.2", out)

    def test_defecto_versiona_prueba_tecnica_sin_cambia(self):
        self.preparada()
        self.urgencia(tipo="Defecto")
        f = self.p / "impacto/URG-01.md"
        texto = f.read_text(encoding="utf-8")
        ini, fin = texto.index("## Puntos"), texto.index("## Urgencia")
        mo.escribe(f, texto[:ini] + texto[fin:])
        code, out = fixture.corre(fixture.S / "proyecto.py", "version", self.p, "--fuente", "FU-99", "--que",
                                  "Prueba técnica del defecto en §14", "--informe", "impacto/URG-01.md")
        self.assertEqual(code, 0, out)
        self.assertIn("Versión 1.2", out)

    def test_urgencia_en_desarrollo_conserva_congelacion_hasta_pase(self):
        self.preparada()
        self.urgencia(donde="Desarrollo")
        code, out = self.version_urgente()
        self.assertEqual(code, 0, out)
        m, ctx = self.carga()
        self.assertEqual(ctx.congelados("EV-01"), [("URG-01", ["AUT_GenerarNumero"])])
        self.assertEqual(ctx.reaplicar("EV-01"), [])
        plan, _, _ = iss.genera(m, ctx, "EV-01")
        self.assertIn("No tocar `AUT_GenerarNumero` hasta el pase de URG-01",
                      next(i for i in plan.issues if "HU-01" in i.requisitos).texto)

    def test_reaplicar_urgencia_no_pierde_avance_ajeno_ni_cierra_sin_confirmacion(self):
        _, plan = self.preparada()
        ajena = next(i for i in plan.issues if "HU-01" not in i.requisitos and iss.subtareas(i))
        iss.marca_subtarea(self.p, "EV-01", ajena.id, iss.subtareas(ajena)[0]["paso"], "hecha", "Ana")
        for i in plan.issues:
            fixture.verifica(self.p, "EV-01", i.id)
        verificacion = (self.p / "construccion/EV-01/verificacion" / (ajena.id + ".json")).read_bytes()
        avances = iss.avances_de(self.p, "EV-01")
        self.urgencia()
        code, out = self.version_urgente()
        self.assertEqual(code, 0, out)
        self.cambia_titulo("HU-01")
        f = self.p / "impacto/URG-01.md"
        mo.escribe(f, f.read_text(encoding="utf-8").replace("Estado: pendiente", "Estado: aplicado en 1.2"))
        m, ctx = self.carga()
        nuevo, _, _ = iss.genera(m, ctx, "EV-01")
        self.assertEqual(nuevo.avances, avances)
        self.assertEqual((self.p / "construccion/EV-01/verificacion" / (ajena.id + ".json")).read_bytes(), verificacion)
        self.assertEqual(next(i for i in nuevo.issues if i.id == ajena.id).version, ajena.version)
        cambiada = next(i for i in nuevo.issues if "HU-01" in i.requisitos)
        self.assertIn("Reaplicar URG-01", cambiada.texto)
        self.assertFalse(iss.estados(nuevo, self.p)[cambiada.id][0])
        for extra in ((), ("--manual",)):
            antes = self.archivos()
            code, out = fixture.corre(fixture.S / "proyecto.py", "cambio", self.p, "EV-01", "construida", *extra)
            self.assertNotEqual(code, 0, out)
            self.assertIn("faltan correcciones urgentes", out)
            self.assertEqual(self.archivos(), antes)
        for i in nuevo.issues:
            fixture.verifica(self.p, "EV-01", i.id)
        code, out = fixture.corre(fixture.S / "proyecto.py", "cambio", self.p, "EV-01", "construida", "--reaplicada", "URG-01")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.carga()[1].por_id["EV-01"].estado, un.CONSTRUIDA)

    def test_propuesta_abierta_deja_construir_encargo_intacto(self):
        self.preparada()
        antes = self.artefactos()
        self.segunda()
        m, ctx = self.carga()
        plan, _, _ = iss.genera(m, ctx, "EV-01")
        self.assertTrue(plan.issues)
        self.assertEqual(self.artefactos(), antes)
        code, out = fixture.corre(fixture.S / "indice.py", "impacto", self.p, "HU-01", "--cambio", "EV-02")
        self.assertEqual(code, 0, out)
        self.assertIn("no edites su texto", out)

    def test_texto_ajeno_no_reescribe_issues_ni_esperados(self):
        self.preparada()
        self.segunda()
        antes = self.artefactos()
        self.cambia_titulo("HU-01")
        m, ctx = self.carga()
        with self.assertRaisesRegex(iss.NoSePuede, "contenido compartido"):
            iss.genera(m, ctx, "EV-01")
        self.assertEqual(self.artefactos(), antes)

    def test_cambio_independiente_en_misma_issue_no_se_bloquea(self):
        _, plan = self.preparada()
        self.assertTrue(any({"HU-01", "HU-03"} <= set(i.requisitos) for i in plan.issues))
        self.segunda()
        self.cambia_titulo("HU-03")
        m, ctx = self.carga()
        nuevo, escritos, _ = iss.genera(m, ctx, "EV-01")
        self.assertTrue(escritos)
        self.assertEqual(len(nuevo.issues), len(plan.issues))

    def test_objeto_compartido_desaparecido_se_busca_en_artefacto(self):
        _, plan = self.preparada()
        nombre = plan.issues[0].objetos[0]
        self.segunda("`" + nombre + "`")
        antes = self.artefactos()
        m, _ = self.carga()
        ini, fin = m.docs["T"].seccion("13")
        lineas = m.lineas("T")
        lineas[ini:fin] = [l for l in lineas[ini:fin] if "`" + nombre + "`" not in l]
        mo.escribe(m.ruta("T"), "\n".join(lineas))
        m, ctx = self.carga()
        with self.assertRaisesRegex(iss.NoSePuede, "contenido compartido"):
            iss.genera(m, ctx, "EV-01")
        self.assertEqual(self.artefactos(), antes)

    def test_legacy_migra_solo_con_version_igual_y_falta_evidencia_bloquea(self):
        self.preparada()
        self.segunda()
        def quita_huellas():
            for f in (self.p / "construccion/EV-01").glob("*-esperado.json"):
                datos = json.loads(f.read_text(encoding="utf-8"))
                datos["_issue"].pop("ambito", None)
                mo.escribe(f, json.dumps(datos))
        quita_huellas()
        m, ctx = self.carga()
        iss.genera(m, ctx, "EV-01")
        self.assertTrue(all("ambito" in json.loads(f.read_text(encoding="utf-8"))["_issue"]
                            for f in (self.p / "construccion/EV-01").glob("*-esperado.json")))
        quita_huellas()
        self.cambia_titulo("HU-01")
        antes = self.artefactos()
        m, ctx = self.carga()
        with self.assertRaisesRegex(iss.NoSePuede, "no hay huellas suficientes"):
            iss.genera(m, ctx, "EV-01")
        self.assertEqual(self.artefactos(), antes)
        for f in (self.p / "construccion/EV-01").glob("ISS-02-esperado.json"):
            f.unlink()
        antes = self.artefactos()
        with self.assertRaisesRegex(iss.NoSePuede, "falta el artefacto"):
            iss.genera(m, ctx, "EV-01")
        self.assertEqual(self.artefactos(), antes)

    def test_no_aprueba_segunda_ni_abre_version_sobre_primera(self):
        self.preparada()
        self.segunda(decision="✔")
        fuentes = self.p / "fuentes/indice.json"
        fuentes.parent.mkdir(exist_ok=True)
        (fuentes.parent / "FU-05-aprobacion.md").write_text("Aprobación ficticia", encoding="utf-8")
        cat = json.loads(fuentes.read_text(encoding="utf-8")) if fuentes.exists() else {"fuentes": []}
        cat["fuentes"].append({"id": "FU-99", "fecha": "2026-10-19", "nombre": "Cambio ficticio"})
        mo.escribe(fuentes, json.dumps(cat))
        antes = self.artefactos()
        documentos = {str(f): f.read_bytes() for f in (self.p / "analisis").glob("*.md")}
        for script, args in (("proyecto.py", ("cambio", self.p, "EV-02", "aprobada", "--fuente", "FU-05", "--comparte", "EV-01 primero")),
                             ("proyecto.py", ("version", self.p, "--fuente", "FU-99", "--que", "Revisión", "--informe", "impacto/FU-99.md"))):
            code, out = fixture.corre(fixture.S / script, *args)
            self.assertNotEqual(code, 0, out)
            self.assertIn("sin construir", out)
            self.assertEqual(self.artefactos(), antes)
            self.assertEqual({str(f): f.read_bytes() for f in (self.p / "analisis").glob("*.md")}, documentos)
        code, out = fixture.corre(fixture.S / "proyecto.py", "cambio", self.p, "EV-01", "construida", "--manual")
        self.assertEqual(code, 0, out)
        code, out = fixture.corre(fixture.S / "proyecto.py", "cambio", self.p, "EV-02", "aprobada", "--fuente", "FU-05")
        self.assertEqual(code, 0, out)

    def test_contexto_y_existe_no_son_cambio_y_dos_abiertas_admiten_primera(self):
        fixture.nueva_con_issues(self.p)
        self.segunda()
        code, out = fixture.corre(fixture.S / "proyecto.py", "cambio", self.p, "EV-01", "aprobada", "--fuente", "FU-05")
        self.assertEqual(code, 0, out)
        self.assertTrue((self.p / "construccion/EV-01/ISS-02-esperado.json").exists(), out)
        self.informe("HU-99", "✔", "NUEVO", "HU-01 solo de contexto")
        m, ctx = self.carga()
        self.assertFalse(ctx.solapes_secuencia("EV-02"))
        self.informe("HU-01", "✔", "EXISTE")
        m, ctx = self.carga()
        self.assertFalse(ctx.solapes_secuencia("EV-02"))

    def test_otro_cambio_ya_aplicado_impide_aprobar_y_decision_impide_version(self):
        fixture.nueva_con_issues(self.p)
        self.segunda(decision="✔")
        informe = self.p / "impacto/FU-99.md"
        mo.escribe(informe, informe.read_text(encoding="utf-8").replace("Estado: pendiente", "Estado: aplicado en 1.1"))
        antes = self.artefactos()
        cambios = (self.p / "analisis/cambios.md").read_bytes()
        code, out = fixture.corre(fixture.S / "proyecto.py", "cambio", self.p, "EV-01", "aprobada", "--fuente", "FU-05")
        self.assertNotEqual(code, 0, out)
        self.assertIn("ya tiene cambios", out)
        self.assertEqual((self.p / "analisis/cambios.md").read_bytes(), cambios)
        self.assertEqual(self.artefactos(), antes)
        mo.escribe(informe, informe.read_text(encoding="utf-8").replace("Estado: aplicado en 1.1", "Estado: pendiente"))
        code, out = fixture.corre(fixture.S / "proyecto.py", "cambio", self.p, "EV-01", "aprobada", "--fuente", "FU-05")
        self.assertEqual(code, 0, out)
        m, _ = self.carga()
        a = base.SimpleNamespace(informe=None, fuente=["FU-98"], decision=[("CAMBIA", "HU-01", "Nuevo texto", "Antes")])
        with self.assertRaisesRegex(SystemExit, "No se abre versión"):
            base.proyecto.comprueba_secuencia_version(m, a)

    def test_huellas_no_cambian_por_reserva_ni_orden(self):
        _, plan = self.preparada()
        antes = {i.id: i.esperado["_issue"]["ambito"] for i in plan.issues}
        _, _, plan, _, _ = iss.corrige_dependencias(self.p, "EV-01", "ISS-02", [], "Orden revisado", "Ana")
        plan.reservas["ISS-01"] = "Otra sesión"
        iss.escribe(plan, self.p)
        m, ctx = self.carga()
        actual = iss.calcula(m, ctx, "EV-01")
        self.assertEqual(antes, {i.id: i.esperado["_issue"]["ambito"] for i in actual.issues})

    def test_construir_manual_no_salta_mezcla_y_limpia_sigue_permitida(self):
        m, _ = self.preparada()
        self.segunda()
        original = m.ruta("F").read_bytes()
        self.cambia_titulo("HU-01")
        cambios = (self.p / "analisis/cambios.md").read_bytes()
        antes = self.artefactos()
        for extra in ((), ("--manual",)):
            code, out = fixture.corre(fixture.S / "proyecto.py", "cambio", self.p, "EV-01", "construida", *extra)
            self.assertNotEqual(code, 0, out)
            self.assertIn("contenido compartido", out)
            self.assertNotIn("márcala con --manual", out)
            self.assertEqual((self.p / "analisis/cambios.md").read_bytes(), cambios)
            self.assertEqual(self.artefactos(), antes)
        m.ruta("F").write_bytes(original)
        code, out = fixture.corre(fixture.S / "proyecto.py", "cambio", self.p, "EV-01", "construida", "--manual")
        self.assertEqual(code, 0, out)
        _, ctx = self.carga()
        self.assertEqual(ctx.por_id["EV-01"].estado, un.CONSTRUIDA)
        self.assertEqual(ctx.por_id["EV-02"].estado, un.ABIERTA)

    def test_manual_no_salta_evidencia_ilegible_o_ausente(self):
        self.preparada()
        self.segunda()
        f = self.p / "construccion/EV-01/ISS-02-esperado.json"
        original = f.read_bytes()
        cambios = (self.p / "analisis/cambios.md").read_bytes()
        for dato in (b"{", b"[]", b'{"_issue":{"ambito":[]}}', None):
            if dato is None:
                f.unlink()
            else:
                f.write_bytes(dato)
            antes = self.artefactos()
            code, out = fixture.corre(fixture.S / "proyecto.py", "cambio", self.p, "EV-01", "construida", "--manual")
            self.assertNotEqual(code, 0, out)
            self.assertIn("recupera", out)
            self.assertNotIn("Traceback", out)
            self.assertEqual(self.artefactos(), antes)
            self.assertEqual((self.p / "analisis/cambios.md").read_bytes(), cambios)
            f.write_bytes(original)

    def test_tabla_desaparecida_con_encargo_compartido_no_es_ausencia_legitima(self):
        m, _ = self.preparada()
        self.segunda()
        ini, fin = m.docs["T"].seccion("13")
        lineas = m.lineas("T")
        lineas[ini:fin] = [l for l in lineas[ini:fin] if not l.startswith("|")]
        mo.escribe(m.ruta("T"), "\n".join(lineas))
        for f in (self.p / "construccion/EV-01").glob("*-esperado.json"):
            f.unlink()  # queda el índice: no se puede ignorar el encargo porque falten otros artefactos
        antes = self.artefactos()
        cambios = (self.p / "analisis/cambios.md").read_bytes()
        code, out = fixture.corre(fixture.S / "proyecto.py", "cambio", self.p, "EV-01", "construida", "--manual")
        self.assertNotEqual(code, 0, out)
        self.assertIn("falta el artefacto", out)
        self.assertEqual(self.artefactos(), antes)
        self.assertEqual((self.p / "analisis/cambios.md").read_bytes(), cambios)
        self.informe("HU-99", "✔", "NUEVO")  # nada compartido: el cierre humano sin tabla sigue disponible
        code, out = fixture.corre(fixture.S / "proyecto.py", "cambio", self.p, "EV-01", "construida", "--manual")
        self.assertEqual(code, 0, out)

    def test_renombres_de_partes_distintas_del_mismo_registro_generan_issues(self):
        fixture.con_unidades(self.p)
        t = self.p / "analisis/tecnico.md"
        fila = "| 8 | `DEM Alta Solicitud` | Process model | Modifica | — | EV-03 |"
        accion = "| 8 | `DEM Solicitud — acción «Nueva solicitud»` | Record type | Modifica | — | EV-03 |"
        otra = "| 9 | `DEM Solicitud — vista «Resumen»` | Record type | Modifica | — | EV-05 |"
        fixture.editar(t, fila, accion + "\n" + otra)
        fixture.editar(self.p / "impacto/FU-06.md", "| Sí (alcance) | Pendiente |", "| Sí (alcance) | ✔ FU-05 |")
        c = self.p / "analisis/cambios.md"
        fixture.editar(c, "| EV-02 | Firma de la revisión | Evolutivo | Aprobada |",
                       "| EV-02 | Firma de la revisión | Evolutivo | En producción |")
        mo.escribe(c, c.read_text(encoding="utf-8") +
                   "| EV-05 | La vista | Evolutivo | Aprobada | 2026-10-12 · FU-05 | — | — | — |\n")
        code, out = fixture.corre(fixture.S / "proyecto.py", "cambio", self.p, "EV-03", "aprobada", "--fuente", "FU-05")
        self.assertEqual(code, 0, out)
        self.assertIn("Issues de construcción: construccion/EV-03/", out)
        self.assertTrue((self.p / "construccion/EV-03/ISS-01-esperado.json").exists())
        code, out = fixture.corre(fixture.S / "indice.py", "issues", self.p, "EV-03")
        self.assertEqual(code, 0, out)

    def test_primera_construida_antes_de_aplicar_retoque_compartido(self):
        fixture.con_unidades(self.p)
        code, out = fixture.corre(fixture.S / "proyecto.py", "cambio", self.p, "EV-02", "construida", "--manual",
                                  "--reaplicada", "URG-01")
        self.assertEqual(code, 0, out)
        fixture.editar(self.p / "analisis/tecnico.md",
                       "| 8 | `DEM Alta Solicitud` | Process model | Modifica | — | EV-03 |",
                       "| 8 | `DEM Solicitud — acción «Nueva solicitud»` | Record type | Modifica | — | EV-03 |")
        fixture.editar(self.p / "impacto/FU-06.md", "| Sí (alcance) | Pendiente |", "| Sí (alcance) | ✔ FU-05 |")
        code, out = fixture.corre(fixture.S / "proyecto.py", "cambio", self.p, "EV-03", "aprobada", "--fuente", "FU-05",
                                  "--comparte", "EV-02 construido primero")
        self.assertEqual(code, 0, out)
        self.assertIn("Issues de construcción", out)
        self.assertNotIn("Que una persona revise", out)


if __name__ == "__main__":
    unittest.main()
