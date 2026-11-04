"""Avance por pasos con una sola issue, reserva y verificación. Datos ficticios, sin red."""
import subprocess
import unittest
import test_automejora as base

iss, mo, un, fixture = base.iss, base.mo, base.un, base.fixture


class Subtareas(unittest.TestCase):
    setUp = base.Automejora.setUp
    preparada = base.Automejora.preparada

    def carga(self):
        m = mo.Proyecto(self.p)
        return iss.calcula(m, un.Contexto(m), "EV-01")

    def archivos(self):
        return {str(f.relative_to(self.p)): f.read_bytes() for f in (self.p / "construccion").rglob("*") if f.is_file()}

    def test_reparto_completo_sin_duplicar_y_conserva_todas_las_filas(self):
        _, plan = self.preparada()
        i = plan.issues[0]
        tareas = iss.subtareas(i)
        self.assertEqual([x["paso"] for x in tareas], ["1", "2"])
        self.assertEqual(sum(x["objetos"].count("`AUT Solicitud`") for x in tareas), 1)
        tecnico = self.p / "analisis/tecnico.md"
        texto = tecnico.read_text(encoding="utf-8")
        fila = next(l for l in texto.splitlines() if l.startswith("| 2 | `AUT Documento`"))
        mo.escribe(tecnico, texto.replace(fila, fila + "\n" + fila.replace("| 2 |", "| 8 |").replace(
            "| Record type |", "| Revisión adicional del registro |")))
        i = self.carga().issues[0]
        o = "AUT Documento"
        tareas = iss.subtareas(i)
        self.assertEqual(sum(x["objetos"].count("`" + o + "`") for x in tareas), 1)
        self.assertIn("pasos 2, 8", " ".join(x["objetos"] for x in tareas))
        self.assertIn("| `AUT Documento` | Record type |", i.texto)
        self.assertIn("| `AUT Documento` | Revisión adicional del registro |", i.texto)
        self.assertIn("## Subtareas por paso", i.texto)
        self.assertIn("todas sus instrucciones", i.texto)

    def test_guardar_retomar_deshacer_sin_cambiar_encargo_reserva_o_verificacion(self):
        _, plan = self.preparada()
        plan.reservas["ISS-01"] = "Ana · 2026-10-19"
        iss.escribe(plan, self.p)
        antes = self.archivos()
        _, _, p, i, _ = iss.marca_subtarea(self.p, "EV-01", "ISS-01", "1", "hecha", "Ana")
        self.assertEqual(p.reservas, plan.reservas)
        self.assertEqual(i.esperado, plan.issues[0].esperado)
        self.assertEqual({k: v for k, v in self.archivos().items() if not k.endswith("indice.md")},
                         {k: v for k, v in antes.items() if not k.endswith("indice.md")})
        p = self.carga()
        self.assertEqual(p.avances[0]["quien"], "Ana")
        self.assertTrue(p.avances[0]["cuando"])
        self.assertIn("Siguiente subtarea pendiente: 2", "\n".join(iss.texto_avance(p, p.issues[0])))
        self.assertFalse(iss.estados(p, self.p)["ISS-01"][0])
        _, _, p, i, _ = iss.marca_subtarea(self.p, "EV-01", "ISS-01", "1", "pendiente", "Ana")
        self.assertIn("Siguiente subtarea pendiente: 1", "\n".join(iss.texto_avance(p, i)))
        self.assertEqual(p.avances[0]["avance"], "pendiente")

    def test_todas_hechas_no_cierran_ni_desbloquean_dependientes(self):
        _, plan = self.preparada()
        for t in iss.subtareas(plan.issues[0]):
            _, _, p, i, _ = iss.marca_subtarea(self.p, "EV-01", "ISS-01", t["paso"], "hecha", "Constructor")
        self.assertIn("queda verificar", "\n".join(iss.texto_avance(p, i)))
        self.assertFalse(iss.estados(p, self.p)["ISS-01"][0])
        self.assertEqual(iss.elige(p, self.p).id, "ISS-01")
        self.assertIn("ISS-01", p.issues[1].depende)
        self.assertFalse((self.p / "construccion/EV-01/verificacion").exists())

    def test_encargo_cambia_conserva_revisar_y_necesita_nueva_marca(self):
        m, plan = self.preparada()
        i = next(i for i in plan.issues if "HU-01" in i.requisitos)
        paso = iss.subtareas(i)[0]["paso"]
        iss.marca_subtarea(self.p, "EV-01", i.id, paso, "hecha", "Ana")
        f = m.ruta("F")
        original = f.read_text(encoding="utf-8")
        titulo = m.piezas["HU-01"].titulo
        mo.escribe(f, original.replace(titulo, titulo + " revisión del encargo", 1))
        p = self.carga()
        self.assertTrue(p.avances[0]["estado"].startswith("Revisar"))
        nuevo = next(x for x in p.issues if x.id == i.id)
        self.assertIn("Avance anterior para revisar", "\n".join(iss.texto_avance(p, nuevo)))
        iss.escribe(p, self.p)
        mo.escribe(f, original)
        p = self.carga()
        self.assertTrue(p.avances[0]["estado"].startswith("Revisar"))
        _, _, p, _, _ = iss.marca_subtarea(self.p, "EV-01", i.id, paso, "hecha", "Bea")
        self.assertEqual(len(p.avances), 2)
        self.assertEqual(p.avances[-1]["estado"], "Vigente")
        self.assertEqual(p.avances[0]["quien"], "Ana")
        # el aviso se apaga cuando el paso vuelve a estar marcado para esta versión; el rastro de «Revisar» se conserva
        self.assertNotIn("Avance anterior para revisar",
                         "\n".join(iss.texto_avance(p, next(x for x in p.issues if x.id == i.id))))

    def test_cambio_reparto_y_issue_retirada_no_pierden_rastro(self):
        _, plan = self.preparada()
        _, _, p, i, _ = iss.marca_subtarea(self.p, "EV-01", "ISS-01", "1", "hecha", "Ana")
        for f in i.filas:
            if f["paso"] == "1":
                f["paso"] = "3"
        iss.revisa_avances(p)
        self.assertTrue(p.avances[0]["estado"].startswith("Revisar"))
        p.issues = [x for x in p.issues if x.id != i.id]
        iss.revisa_avances(p)
        self.assertEqual(len(p.avances), 1)

    def test_issue_pequena_sin_ruido_y_marcas_invalidas_no_escriben(self):
        _, plan = self.preparada()
        pequena = next(i for i in plan.issues if not iss.subtareas(i))
        self.assertNotIn("## Subtareas por paso", pequena.texto)
        self.assertEqual(iss.texto_avance(plan, pequena), [])
        antes = self.archivos()
        for iid, paso in ((pequena.id, "5"), ("ISS-01", "999"), ("ISS-99", "1")):
            with self.assertRaises(iss.NoSePuede):
                iss.marca_subtarea(self.p, "EV-01", iid, paso, "hecha", "Ana")
            self.assertEqual(self.archivos(), antes)

    def test_cli_desatendido_y_siguiente_conservan_una_issue(self):
        _, plan = self.preparada()
        code, out = fixture.corre(fixture.S / "indice.py", "issues", self.p, "EV-01", "ISS-01", "--subtarea", "1",
                                  "--avance", "hecha", "--quien", "Constructor", "--desatendida")
        self.assertEqual(code, 0, out)
        self.assertIn("Siguiente subtarea pendiente: 2", out)
        antes = self.archivos()
        for extra in (("--regresion",), ("--manual", "--motivo", "No"), ("--depende-de", "ninguna")):
            code, out = fixture.corre(fixture.S / "indice.py", "issues", self.p, "EV-01", "ISS-01", "--subtarea", "1",
                                      "--avance", "hecha", *extra)
            self.assertNotEqual(code, 0, out)
            self.assertEqual(self.archivos(), antes)
        code, out = fixture.corre(fixture.S / "indice.py", "issues", self.p, "EV-01", "--siguiente", "--quien", "Constructor")
        self.assertEqual(code, 0, out)
        self.assertIn("ISS-01", out)
        self.assertIn("Siguiente subtarea pendiente: 2", out)
        self.assertEqual(len(self.carga().issues), len(plan.issues))

    def test_anotacion_incompleta_no_se_pierde_al_regenerar(self):
        self.preparada()
        iss.marca_subtarea(self.p, "EV-01", "ISS-01", "1", "hecha", "Ana")
        f = self.p / "construccion/EV-01/indice.md"
        mo.escribe(f, f.read_text(encoding="utf-8").replace("| Ana |", "|"))
        antes = self.archivos()
        m = mo.Proyecto(self.p)
        with self.assertRaisesRegex(iss.NoSePuede, "fila incompleta"):
            iss.genera(m, un.Contexto(m), "EV-01")
        self.assertEqual(self.archivos(), antes)


class SubirAlRemoto(unittest.TestCase):
    """Reservar no autoriza subir: lo autoriza la persona, una vez por proyecto, en proyecto.md."""
    setUp = base.Automejora.setUp
    preparada = base.Automejora.preparada
    SIN_SUBIR = "sin subir: no hay autorización registrada"

    def git(self, *args, donde=None):
        return subprocess.run(["git", "-C", str(donde or self.p), *args], check=True, capture_output=True,
                              text=True, encoding="utf-8").stdout.strip()

    def con_remoto(self, linea=None):
        self.preparada()
        fixture.corre(fixture.S / "proyecto.py", "iniciar", self.p)
        self.autoriza(linea)
        self.git("add", "-A")
        self.git("commit", "--quiet", "-m", "Punto de partida")
        self.remoto = self.root / "remoto.git"
        self.git("init", "--quiet", "--bare", str(self.remoto))
        self.git("remote", "add", "origin", str(self.remoto))
        self.git("push", "--quiet", "-u", "origin", "main")

    def autoriza(self, linea):
        f = self.p / "proyecto.md"
        texto = "\n".join(l for l in f.read_text(encoding="utf-8").split("\n") if not l.startswith("Subir al remoto:"))
        f.write_text(texto.rstrip("\n") + (f"\n\n{linea}\n" if linea else "\n"), encoding="utf-8")

    def subidos(self):
        return self.git("rev-list", "--count", "main", donde=self.remoto)

    def test_nombre_con_letra_o_cifra_no_solo_guiones_bajos(self):
        self.p.mkdir()
        f = self.p / "proyecto.md"
        for nombre, valida in (("_", False), ("__", False), ("José_García", True),
                               ("_usuario_2", True), ("王", True), ("123", True)):
            with self.subTest(nombre=nombre):
                f.write_text(f"Subir al remoto: autorizado por {nombre}, 2026-11-03\n", encoding="utf-8")
                self.assertEqual(iss.subir_autorizado(self.p), valida)

    def test_sin_autorizar_commit_local_en_todos_los_caminos(self):
        self.con_remoto()
        antes = self.subidos()
        local = self.git("rev-parse", "HEAD")
        *_, como = iss.siguiente(self.p, "EV-01", "Ana")
        self.assertIn(self.SIN_SUBIR, como)
        self.assertNotEqual(self.git("rev-parse", "HEAD"), local)
        *_, como = iss.marca_subtarea(self.p, "EV-01", "ISS-01", "1", "hecha", "Ana")
        self.assertIn(self.SIN_SUBIR, como)
        *_, como = iss.corrige_dependencias(self.p, "EV-01", "ISS-02", [], "Base disponible", "Ana")
        self.assertIn(self.SIN_SUBIR, como)
        *_, como = iss.libera(self.p, "EV-01", "ISS-01")
        self.assertIn(self.SIN_SUBIR, como)
        self.assertEqual(self.subidos(), antes)

    def test_autorizada_sube_y_retirarla_deja_de_subir(self):
        self.con_remoto("Subir al remoto: autorizado por Ana, 2026-10-30")
        antes = int(self.subidos())
        *_, como = iss.siguiente(self.p, "EV-01", "Ana")
        self.assertEqual(como, "con un commit, subido a origin/main")
        self.assertEqual(int(self.subidos()), antes + 1)
        self.autoriza("Subir al remoto: no")
        *_, como = iss.libera(self.p, "EV-01", "ISS-01")
        self.assertIn(self.SIN_SUBIR, como)
        self.assertEqual(int(self.subidos()), antes + 1)
        self.autoriza(None)
        *_, como = iss.siguiente(self.p, "EV-01", "Ana")
        self.assertIn(self.SIN_SUBIR, como)
        self.assertEqual(int(self.subidos()), antes + 1)

    def test_lo_que_no_es_una_autorizacion_no_sube(self):
        self.con_remoto()
        antes = self.subidos()
        for linea in ("Subir al remoto: no autorizado", "Subir al remoto: pendiente", "Subir al remoto: autorizado",
                      "Subir al remoto: autorizado por <quién>, <AAAA-MM-DD>", "Subir al remoto: autorizado por {quien}",
                      "Subir al remoto: no autorizado por Ana", "Subir al remoto:",
                      "Subir al remoto: autorizado por —, 2026-10-30", "Subir al remoto: autorizado por Ana, <AAAA-MM-DD>",
                      "Subir al remoto: autorizado por Ana", "Subir al remoto: autorizado por Ana, 2026-10-30 pero no"):
            self.autoriza(linea)
            self.assertFalse(iss.subir_autorizado(self.p), linea)
        *_, como = iss.siguiente(self.p, "EV-01", "Ana")
        self.assertIn(self.SIN_SUBIR, como)
        self.assertEqual(self.subidos(), antes)

    def test_una_retirada_que_llega_al_traer_no_sube(self):
        self.con_remoto("Subir al remoto: autorizado por Ana, 2026-10-30")
        antes = self.subidos()
        local = self.git("rev-parse", "HEAD")

        def trae_la_retirada(raiz, remoto):
            self.autoriza("Subir al remoto: no")
            return True, ""
        de_verdad, iss.al_dia = iss.al_dia, trae_la_retirada
        try:
            *_, como = iss.siguiente(self.p, "EV-01", "Ana")
        finally:
            iss.al_dia = de_verdad
        self.assertIn(self.SIN_SUBIR, como)
        self.assertEqual(self.subidos(), antes)
        self.assertNotEqual(self.git("rev-parse", "HEAD"), local)

    def test_la_ultima_linea_manda_y_sin_remoto_lo_dice(self):
        self.preparada()
        fixture.corre(fixture.S / "proyecto.py", "iniciar", self.p)
        self.autoriza("Subir al remoto: autorizado por Ana, 2026-10-30")
        self.git("add", "-A")
        self.git("commit", "--quiet", "-m", "Punto de partida")
        *_, como = iss.siguiente(self.p, "EV-01", "Ana")
        self.assertIn("sin subir: el repositorio no tiene remoto", como)
        f = self.p / "proyecto.md"
        f.write_text(f.read_text(encoding="utf-8") + "Subir al remoto: no\n", encoding="utf-8")
        self.assertFalse(iss.subir_autorizado(self.p))


if __name__ == "__main__":
    unittest.main()
