"""Regresión focal de iniciar/estado y del contrato de la primera versión.

Se ejecuta con unittest o pytest. Los proyectos ficticios se crean fuera del plugin.
"""
import json
import os
import pathlib
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
PLUGIN = pathlib.Path(os.environ.get("PLUGIN_A_PROBAR") or pathlib.Path(__file__).resolve().parents[2]).resolve()
SKILL = PLUGIN / "skills" / "appian-functional-analyst"
SCRIPT = SKILL / "scripts" / "proyecto.py"


class RevisionInicio(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="revision-inicio-")
        self.addCleanup(self.tmp.cleanup)
        self.base = pathlib.Path(self.tmp.name)
        self.p = self.base / "Proyecto ficticio con espacios"
        self.corre("iniciar", self.p, "--nombre", "Reserva de salas")

    def corre(self, *args, check=True):
        r = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True,
                           text=True, encoding="utf-8", env=dict(os.environ, PYTHONUTF8="1"), timeout=30)
        if check:
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return r

    def estado(self):
        return self.corre("estado", self.p).stdout

    def localizador(self, dato):
        (self.p / ".appian-plugin.json").write_text(json.dumps(dato), encoding="utf-8")

    def test_localizador_sano_resuelve_estado_y_flujos(self):
        dato = json.loads((self.p / ".appian-plugin.json").read_text(encoding="utf-8"))
        script = pathlib.Path(dato["ruta"]) / "skills" / "appian-functional-analyst" / "scripts" / "proyecto.py"
        self.assertEqual(script.resolve(), SCRIPT)
        self.assertNotIn("Localizador:", self.estado())
        generados = [self.p / "AGENTS.md", *sorted((self.p / ".agents/workflows").glob("F*.md"))]
        self.assertEqual(len(generados), 10)
        for ruta in generados:
            texto = ruta.read_text(encoding="utf-8")
            self.assertIn(".appian-plugin.json", texto, ruta)
            self.assertNotIn("no busques el plugin en el disco", texto, ruta)
            # La orden de recuperación debe funcionar sin cambiar la carpeta del proyecto.
            orden = 'python "<ruta>/skills/appian-functional-analyst/scripts/proyecto.py" iniciar .'
            self.assertIn(orden, texto, ruta)
            ejecutable = texto.split('`' + orden + '`', 1)[0]  # el contexto de la orden fija el cwd
            self.assertIn("desde la carpeta del proyecto", ejecutable, ruta)
        cmd = shlex.split(orden.replace("<ruta>", PLUGIN.as_posix()))
        cmd[0] = sys.executable
        self.localizador({"ruta": str(self.base / "plugin retirado")})
        r = subprocess.run(cmd, cwd=self.p, capture_output=True, text=True, encoding="utf-8",
                           env=dict(os.environ, PYTHONUTF8="1"), timeout=30)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("Localizador:", self.estado())

    def test_localizador_ausente_avisa_y_se_repara_sin_tocar_analisis(self):
        (self.p / ".appian-plugin.json").rename(self.p / "localizador-anterior.json")
        antes = {f.name: f.read_bytes() for f in (self.p / "analisis").glob("*.md")}
        self.assertIn(".appian-plugin.json", self.estado())
        self.corre("iniciar", self.p)
        self.assertNotIn("Localizador:", self.estado())
        self.assertEqual(antes, {f.name: f.read_bytes() for f in (self.p / "analisis").glob("*.md")})

    def test_localizador_ruta_retirada_avisa(self):
        self.localizador({"ruta": str(self.base / "plugin retirado")})
        self.assertIn("Localizador:", self.estado())

    def test_localizador_se_repara_con_flujos_posteriores_sin_sobrescribirlos(self):
        guia = self.p / "AGENTS.md"
        guia.write_text(re.sub(r"0\.\d+\.\d+(?:-[\w.]+)?", "99.0.0", guia.read_text(encoding="utf-8"), count=1),
                        encoding="utf-8")
        (self.p / ".appian-plugin.json").rename(self.p / "localizador-anterior.json")
        ign = self.p / ".gitignore"
        ign.write_text("# Exclusión del proyecto\nlocal/\n", encoding="utf-8")
        antes = self.huellas()
        self.assertIn("Localizador:", self.estado())
        self.corre("iniciar", self.p)
        self.assertNotIn("Localizador:", self.estado())
        self.assertEqual(ign.read_text(encoding="utf-8"), "# Exclusión del proyecto\nlocal/\n.appian-plugin.json\n")
        for rel, contenido in antes.items():
            if rel != pathlib.Path(".gitignore"):
                self.assertEqual((self.p / rel).read_bytes(), contenido, rel)

    def test_localizador_invalido_no_rompe_estado(self):
        for dato in ([], {}, {"ruta": None}, {"ruta": 1}, {"ruta": ""}, {"ruta": "\u0000"}):
            with self.subTest(dato=dato):
                self.localizador(dato)
                self.assertIn("Localizador:", self.estado())
        (self.p / ".appian-plugin.json").write_text("{", encoding="utf-8")
        self.assertIn("Localizador:", self.estado())

    def test_localizador_no_acepta_carpeta_ajena(self):
        self.localizador({"ruta": str(self.base)})
        self.assertIn("Localizador:", self.estado())

    def test_plan_de_construccion_admite_fila_sin_recrear_cabecera(self):
        ruta = self.p / "analisis/tecnico.md"
        texto = ruta.read_text(encoding="utf-8")
        plan = texto.split("## 13. Plan de construcción", 1)[1].split("### Supuestos", 1)[0]
        cabecera = "| Paso | Objeto | Tipo | Situación | Sustituye a | Cambio | Para |"
        self.assertIn(cabecera, plan)
        # El lector real reconoce la tabla y el objeto al rellenar una fila.
        sys.path.insert(0, str(SKILL / "scripts"))
        import modelo
        import unidades
        ruta.write_text(texto.replace("|---|---|---|---|---|---|---|", "|---|---|---|---|---|---|---|\n"
                        "| 1 | FIC_Reserva | Record Type | Nuevo | — | EV-01 | HU-01 |", 1), encoding="utf-8")
        contexto = unidades.Contexto(modelo.Proyecto(self.p))
        self.assertTrue(any("FIC_Reserva" in f["objetos"] for f in contexto.filas), contexto.filas)

    @unittest.skipUnless(shutil.which("git"), "requiere git")
    def test_iniciar_crea_git_main_sin_commit_ni_inicializacion_extra(self):
        self.assertTrue((self.p / ".git").is_dir())
        rama = subprocess.run(["git", "-C", str(self.p), "symbolic-ref", "--short", "HEAD"],
                              capture_output=True, text=True)
        self.assertEqual(rama.stdout.strip(), "main")
        commit = subprocess.run(["git", "-C", str(self.p), "rev-parse", "--verify", "HEAD"],
                                capture_output=True)
        self.assertNotEqual(commit.returncode, 0)

    def fuente(self, cantidad=1):
        (self.p / "fuentes/indice.json").write_text(json.dumps({"fuentes": [
            {"id": f"FU-{i:02d}", "fecha": "2026-10-20", "tipo": "Acta"}
            for i in range(1, cantidad + 1)]}), encoding="utf-8")

    def huellas(self):
        return {f.relative_to(self.p): f.read_bytes() for f in self.p.rglob("*")
                if f.is_file() and ".git" not in f.relative_to(self.p).parts}

    def test_inicial_promueve_borrador_sin_cambiar_contenido_ni_aprobacion(self):
        self.fuente()
        antes = self.huellas()
        self.corre("version", self.p, "--inicial", "--fuente", "FU-01", "--que", "Primera entrega")
        for nombre in ("funcional", "tecnico"):
            rel = pathlib.Path("analisis") / (nombre + ".md")
            self.assertEqual((self.p / rel).read_bytes(), antes[rel].replace(b"0.1", b"1.0", 1))
        dec = (self.p / "analisis/decisiones.md").read_text(encoding="utf-8")
        self.assertNotIn("| 0.1 |", dec)
        self.assertIn("| Inicio del análisis | FU-01 | — |", dec)
        self.assertEqual(dec.split("## Decisiones del cliente")[1],
                         antes[pathlib.Path("analisis/decisiones.md")].decode("utf-8").split("## Decisiones del cliente")[1])
        self.assertFalse(list((self.p / "versiones").iterdir()))

    def test_inicial_rechaza_versiones_sin_historial_coherente_sin_escribir(self):
        self.fuente()
        for doc, numero in (("funcional", "0.2"), ("funcional", "1.1"), ("tecnico", "0.2")):
            with self.subTest(doc=doc, numero=numero):
                ruta = self.p / "analisis" / (doc + ".md")
                original = ruta.read_bytes()
                ruta.write_bytes(original.replace(b"0.1", numero.encode(), 1))
                antes = self.huellas()
                r = self.corre("version", self.p, "--inicial", "--fuente", "FU-01", "--que", "Primera entrega", check=False)
                self.assertNotEqual(r.returncode, 0)
                self.assertEqual(antes, self.huellas())
                ruta.write_bytes(original)

    def test_inicial_rechaza_snapshot_no_inicial_sin_escribir(self):
        self.fuente()
        (self.p / "versiones/v1.0").mkdir()
        antes = self.huellas()
        r = self.corre("version", self.p, "--inicial", "--fuente", "FU-01", "--que", "Primera entrega", check=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(antes, self.huellas())

    def test_inicial_tras_dos_actualizaciones_conserva_historia_fuentes_y_snapshots(self):
        self.fuente(3)
        self.corre("version", self.p, "--fuente", "FU-01", "--que", "Primer ajuste",
                   "--decision", "CAMBIA", "HU-01", "Reserva con responsable", "Reserva sin responsable")
        self.corre("version", self.p, "--fuente", "FU-02", "--que", "Segundo ajuste")
        dec = self.p / "analisis/decisiones.md"
        texto = dec.read_text(encoding="utf-8")
        texto = texto.replace("| Segundo ajuste | FU-02 | — |", "| Segundo ajuste | FU-02 | Aceptada |")
        # La posición física de las filas no cambia el significado del historial.
        filas = [l for l in texto.splitlines() if l.startswith("| 0.")]
        texto = texto.replace("\n".join(filas), "\n".join(reversed(filas)))
        dec.write_text(texto, encoding="utf-8")
        antes = self.huellas()
        proy = (self.p / "proyecto.md").read_text(encoding="utf-8")
        salida = self.corre("version", self.p, "--inicial", "--fuente", "FU-03", "--que", "Primera entrega").stdout
        despues = dec.read_text(encoding="utf-8")
        for fila in texto.splitlines():
            self.assertIn(fila, despues)
        fila_1 = next(l for l in despues.splitlines() if l.startswith("| 1.0 |"))
        self.assertEqual(set(re.findall(r"FU-\d+", fila_1)), {"FU-01", "FU-02", "FU-03"})
        self.assertIn("| FU-03 | 2026-10-20 | Acta | — | 1.0 |", (self.p / "proyecto.md").read_text(encoding="utf-8"))
        for fila in proy.splitlines():
            self.assertIn(fila, (self.p / "proyecto.md").read_text(encoding="utf-8"))
        for rel, contenido in antes.items():
            if rel.parts[0] == "versiones":
                self.assertEqual((self.p / rel).read_bytes(), contenido)
        for nombre in ("funcional", "tecnico"):
            rel = pathlib.Path("analisis") / (nombre + ".md")
            self.assertEqual((self.p / rel).read_bytes(), antes[rel].replace(b"0.3", b"1.0", 1))
        self.assertEqual({x.name for x in (self.p / "versiones").iterdir()}, {"v0.1", "v0.2"})
        self.assertNotIn("a mano", salida)

    def test_inicial_reutiliza_fuentes_borrador_sin_duplicar_ni_reasignar_primera_version(self):
        self.fuente(3)
        pm = self.p / "proyecto.md"
        self.corre("version", self.p, "--fuente", "FU-01", "--que", "Ajuste del borrador")
        antes = pm.read_bytes()
        self.corre("version", self.p, "--inicial", "--fuente", "FU-01", "FU-02", "--que", "Primera entrega")
        despues = pm.read_text(encoding="utf-8")
        fila = next(l for l in antes.decode("utf-8").splitlines() if l.startswith("| FU-01 |"))
        self.assertEqual(despues.count("| FU-01 |"), 1)
        self.assertIn(fila, despues)
        self.assertIn("| FU-02 | 2026-10-20 | Acta | — | 1.0 |", despues)
        antes = self.huellas()
        for fuentes in (("FU-01", "FU-02"), ("FU-01",)):
            r = self.corre("version", self.p, "--inicial", "--fuente", *fuentes, "--que", "Repetida", check=False)
            self.assertNotEqual(r.returncode, 0)
            self.assertEqual(antes, self.huellas())

    def test_inicial_completa_fuente_omitida_antes_de_entregar(self):
        self.fuente(2)
        self.corre("version", self.p, "--inicial", "--fuente", "FU-01", "--que", "Primera entrega")
        antes = self.huellas()
        self.corre("version", self.p, "--inicial", "--fuente", "FU-02", "--que", "Fuente omitida")
        despues = self.huellas()
        self.assertIn(b"| FU-02 |", despues[pathlib.Path("proyecto.md")])
        self.assertEqual(despues[pathlib.Path("analisis/decisiones.md")].count(b"| 1.0 |"), 1)
        for rel, contenido in antes.items():
            if rel not in (pathlib.Path("proyecto.md"), pathlib.Path("analisis/decisiones.md")):
                self.assertEqual(despues[rel], contenido, rel)
        self.assertFalse(list((self.p / "versiones").iterdir()))
        r = self.corre("version", self.p, "--inicial", "--fuente", "FU-02", "--que", "Repetida", check=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(despues, self.huellas())

    def test_inicial_fuentes_mixtas_conservan_orden_y_primera_version(self):
        self.fuente(3)
        for borrador in (False, True):
            with self.subTest(borrador=borrador):
                if borrador:
                    self.p = self.base / "Con borrador"
                    self.corre("iniciar", self.p, "--nombre", "Reserva de salas")
                    self.fuente(3)
                    self.corre("version", self.p, "--fuente", "FU-01", "--que", "Borrador")
                self.corre("version", self.p, "--inicial", "--fuente", "FU-01", "FU-02", "--que", "Primera entrega")
                antes = self.huellas()
                self.corre("version", self.p, "--inicial", "--fuente", "FU-01", "FU-03", "--que", "Completar mixta")
                pm = (self.p / "proyecto.md").read_text(encoding="utf-8")
                for fu in ("FU-01", "FU-02", "FU-03"):
                    self.assertEqual(pm.count(f"| {fu} |"), 1)
                primera = next(l for l in antes[pathlib.Path("proyecto.md")].decode("utf-8").splitlines()
                               if l.startswith("| FU-01 |"))
                self.assertIn(primera, pm)
                dec = (self.p / "analisis/decisiones.md").read_text(encoding="utf-8")
                fila = next(l for l in dec.splitlines() if l.startswith("| 1.0 |"))
                self.assertIn("| FU-01, FU-02, FU-03 |", fila)
                self.assertEqual(dec.count("| 1.0 |"), 1)
                for rel, contenido in antes.items():
                    if rel.parts[0] == "versiones":
                        self.assertEqual((self.p / rel).read_bytes(), contenido)

    def test_inicial_completa_1_0_nacida_de_borradores_con_aprobaciones_y_copias(self):
        self.fuente(4)
        self.corre("version", self.p, "--fuente", "FU-01", "--que", "Primer ajuste")
        self.corre("version", self.p, "--fuente", "FU-02", "--que", "Segundo ajuste")
        self.corre("version", self.p, "--inicial", "--fuente", "FU-03", "--que", "Primera entrega")
        dec = self.p / "analisis/decisiones.md"
        dec.write_text(dec.read_text(encoding="utf-8").replace("| FU-03, FU-01, FU-02 | — |",
                       "| FU-03, FU-01, FU-02 | Aceptada |"), encoding="utf-8")
        antes = self.huellas()
        self.corre("version", self.p, "--inicial", "--fuente", "FU-04", "--que", "Fuente omitida")
        despues = self.huellas()
        self.assertEqual(set(antes), set(despues))
        for rel, contenido in antes.items():
            if rel not in (pathlib.Path("proyecto.md"), pathlib.Path("analisis/decisiones.md")):
                self.assertEqual(despues[rel], contenido, rel)
        nuevo = dec.read_text(encoding="utf-8")
        self.assertIn("| FU-03, FU-01, FU-02, FU-04 | Aceptada |", nuevo)
        self.assertEqual(nuevo.count("| 1.0 |"), 1)
        for fila in antes[pathlib.Path("proyecto.md")].decode("utf-8").splitlines():
            self.assertIn(fila, (self.p / "proyecto.md").read_text(encoding="utf-8"))
        for fila in antes[pathlib.Path("analisis/decisiones.md")].decode("utf-8").splitlines():
            if fila.startswith("| 0."):
                self.assertIn(fila, nuevo)
        for entrega in ("DF entregado: 1.0", "Entregados: DF-ficticio-v1.0.docx"):
            pm = self.p / "proyecto.md"
            pm.write_bytes(despues[pathlib.Path("proyecto.md")] + ("\n" + entrega + "\n").encode("utf-8"))
            previa = self.huellas()
            r = self.corre("version", self.p, "--inicial", "--fuente", "FU-04", "--que", "Entregada", check=False)
            self.assertNotEqual(r.returncode, 0)
            self.assertEqual(previa, self.huellas())

    def test_inicial_recupera_primera_version_explicita_de_fuente_solo_en_historial(self):
        self.fuente(2)
        self.corre("version", self.p, "--fuente", "FU-01", "--que", "Ajuste del borrador")
        pm = self.p / "proyecto.md"
        texto = pm.read_text(encoding="utf-8")
        pm.write_text("\n".join(l for l in texto.split("\n") if not l.startswith("| FU-01 |")), encoding="utf-8")
        self.corre("version", self.p, "--inicial", "--fuente", "FU-02", "--que", "Primera entrega")
        self.assertIn("| FU-01 | 2026-10-20 | Acta | — | 0.2 |", pm.read_text(encoding="utf-8"))

    def test_inicial_rechaza_entrega_previa_o_fuente_historica_inexistente_sin_escribir(self):
        self.fuente(2)
        self.corre("version", self.p, "--fuente", "FU-01", "--que", "Ajuste del borrador")
        pm, dec = self.p / "proyecto.md", self.p / "analisis/decisiones.md"
        inicial_p, inicial_d = pm.read_bytes(), dec.read_bytes()
        casos = ((pm, inicial_p.replace("DF entregado: —".encode(), b"DF entregado: 0.2")),
                 (pm, inicial_p + b"\nEntregados: DF-ficticio-v0.2.docx\n"),
                 (dec, inicial_d.replace(b"| FU-01 |", b"| FU-99 |")))
        for ruta, texto in casos:
            with self.subTest(ruta=ruta.name, texto=texto[-80:]):
                pm.write_bytes(inicial_p)
                dec.write_bytes(inicial_d)
                ruta.write_bytes(texto)
                antes = self.huellas()
                r = self.corre("version", self.p, "--inicial", "--fuente", "FU-02", "--que", "Primera entrega", check=False)
                self.assertNotEqual(r.returncode, 0)
                self.assertEqual(antes, self.huellas())

    def test_inicial_no_reinterpreta_historial_del_borrador(self):
        self.fuente()
        dec = self.p / "analisis/decisiones.md"
        original = dec.read_bytes()
        texto = original.decode("utf-8")
        fila = next(l for l in texto.splitlines() if l.startswith("| 0.1 |"))
        duplicado = texto.replace(fila, fila + "\n" + fila).encode("utf-8")
        for historial in (original.replace(b"0.1", b"1.1", 1), duplicado):
            with self.subTest(historial=historial):
                dec.write_bytes(historial)
                antes = self.huellas()
                r = self.corre("version", self.p, "--inicial", "--fuente", "FU-01", "--que", "Primera entrega", check=False)
                self.assertNotEqual(r.returncode, 0)
                self.assertEqual(antes, self.huellas())

    def test_inicial_reutiliza_fila_1_0_preservando_su_aprobacion(self):
        self.fuente()
        dec = self.p / "analisis/decisiones.md"
        texto = dec.read_text(encoding="utf-8")
        fila = next(l for l in texto.splitlines() if l.startswith("| 0.1 |"))
        texto = texto.replace(fila, "| 1.0 | 2026-09-01 | Acuerdo existente | FU-01 | Aceptada |")
        texto += "\n## Tabla ajena\n| Clave | Texto |\n|---|---|\n| 0.1 | Conservar |\n"
        dec.write_text(texto, encoding="utf-8")
        self.corre("version", self.p, "--inicial", "--fuente", "FU-01", "--que", "Primera entrega")
        despues = dec.read_text(encoding="utf-8")
        self.assertEqual(despues.count("| 1.0 |"), 1)
        self.assertIn("| 1.0 | 2026-09-01 | Acuerdo existente | FU-01 | Aceptada |", despues)
        self.assertIn("| 0.1 | Conservar |", despues)

    def test_inicial_rechaza_fuente_inexistente_sin_escribir(self):
        antes = self.huellas()
        r = self.corre("version", self.p, "--inicial", "--fuente", "FU-99", "--que", "Primera entrega", check=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(antes, self.huellas())

    def test_inicial_preserva_tecnico_sin_empezar_y_rechaza_repeticion(self):
        self.fuente()
        tecnico = self.p / "analisis/tecnico.md"
        tecnico.write_text("# Técnico sin empezar\n", encoding="utf-8")
        self.corre("version", self.p, "--inicial", "--fuente", "FU-01", "--que", "Primera entrega")
        self.assertEqual(tecnico.read_text(encoding="utf-8"), "# Técnico sin empezar\n")
        antes = self.huellas()
        r = self.corre("version", self.p, "--inicial", "--fuente", "FU-01", "--que", "Repetida", check=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(antes, self.huellas())

    def test_inicial_registra_1_0_sin_subir_ni_copiar_version(self):
        self.fuente()
        for nombre in ("funcional", "tecnico", "decisiones"):
            ruta = self.p / "analisis" / (nombre + ".md")
            ruta.write_text(ruta.read_text(encoding="utf-8").replace("0.1", "1.0", 1), encoding="utf-8")
        self.corre("version", self.p, "--inicial", "--fuente", "FU-01", "--que", "Primera entrega")
        self.assertFalse(list((self.p / "versiones").iterdir()))
        self.assertIn("FU-01", (self.p / "analisis/decisiones.md").read_text(encoding="utf-8"))
        self.assertIn("| 1.0 |", (self.p / "proyecto.md").read_text(encoding="utf-8"))
        for nombre in ("funcional", "tecnico"):
            self.assertIn("Versión: 1.0", (self.p / "analisis" / (nombre + ".md")).read_text(encoding="utf-8"))

    def test_inicial_conserva_combinaciones_legadas_y_entregados_vacio(self):
        self.fuente()
        originales = self.huellas()
        for f_version, t_version in (("0.1", "1.0"), ("1.0", "0.1")):
            with self.subTest(funcional=f_version, tecnico=t_version):
                for rel, texto in originales.items():
                    (self.p / rel).write_bytes(texto)
                for nombre, numero in (("funcional", f_version), ("tecnico", t_version)):
                    ruta = self.p / "analisis" / (nombre + ".md")
                    ruta.write_bytes(ruta.read_bytes().replace(b"0.1", numero.encode(), 1))
                pm = self.p / "proyecto.md"
                pm.write_bytes(pm.read_bytes() + b"\nEntregados:\n")
                self.corre("version", self.p, "--inicial", "--fuente", "FU-01", "--que", "Primera entrega")
                self.assertIn("| 1.0 |", (self.p / "analisis/decisiones.md").read_text(encoding="utf-8"))

    def test_inicial_semantica_conserva_0_1_si_ya_tiene_fuentes_procesadas(self):
        self.fuente(2)
        originales = self.huellas()
        pm, dec = self.p / "proyecto.md", self.p / "analisis/decisiones.md"
        for registro in ("procesadas", "historial"):
            with self.subTest(registro=registro):
                for rel, texto in originales.items():
                    (self.p / rel).write_bytes(texto)
                if registro == "procesadas":
                    texto = pm.read_text(encoding="utf-8")
                    pm.write_text(texto.replace("|---|---|---|---|---|", "|---|---|---|---|---|\n"
                                  "| FU-01 | 2026-10-20 | Acta inicial | notas/FU-01.md | 0.1 |", 1), encoding="utf-8")
                else:
                    texto = dec.read_text(encoding="utf-8")
                    dec.write_text(texto.replace("| Inicio del análisis | — |", "| Inicio del análisis | FU-01 |"), encoding="utf-8")
                fila = next(l for l in dec.read_text(encoding="utf-8").splitlines() if l.startswith("| 0.1 |"))
                self.corre("version", self.p, "--inicial", "--fuente", "FU-02", "--que", "Primera entrega")
                despues = dec.read_text(encoding="utf-8")
                self.assertIn(fila, despues)
                self.assertEqual(despues.count("| 1.0 |"), 1)
                self.assertRegex(pm.read_text(encoding="utf-8"), r"\| FU-01 \|[^|\n]+\|[^|\n]+\|[^|\n]+\| 0\.1 \|")

    def test_inicial_semantica_admite_historial_con_salto_sin_inventar_filas(self):
        self.fuente(3)
        self.corre("version", self.p, "--fuente", "FU-01", "--que", "Primer ajuste")
        self.corre("version", self.p, "--fuente", "FU-02", "--que", "Segundo ajuste")
        dec, pm = self.p / "analisis/decisiones.md", self.p / "proyecto.md"
        # Historial legado inequívoco: no se afirma una versión intermedia ni se deja una FU apuntando a ella.
        for ruta, prefijo in ((dec, "| 0.2 |"), (pm, "| FU-01 |")):
            ruta.write_text("\n".join(l for l in ruta.read_text(encoding="utf-8").split("\n")
                                      if not l.startswith(prefijo)), encoding="utf-8")
        anteriores = self.huellas()
        self.corre("version", self.p, "--inicial", "--fuente", "FU-03", "--que", "Primera entrega")
        despues = dec.read_text(encoding="utf-8")
        self.assertNotIn("| 0.2 |", despues)
        for fila in anteriores[pathlib.Path("analisis/decisiones.md")].decode("utf-8").splitlines():
            self.assertIn(fila, despues)

    def test_inicial_flags_fuente_repetidos_equivalen_lista_sin_duplicar(self):
        self.fuente(2)
        originales, esperado = self.huellas(), None
        for args in (("--fuente", "FU-01", "--fuente", "FU-02"),
                     ("--fuente", "FU-01", "FU-02"),
                     ("--fuente", "FU-01", "--fuente", "FU-02", "FU-01")):
            with self.subTest(args=args):
                for rel, texto in originales.items():
                    (self.p / rel).write_bytes(texto)
                self.corre("version", self.p, "--inicial", *args, "--que", "Primera entrega")
                pm = (self.p / "proyecto.md").read_text(encoding="utf-8")
                dec = (self.p / "analisis/decisiones.md").read_text(encoding="utf-8")
                for fu in ("FU-01", "FU-02"):
                    self.assertEqual(pm.count(f"| {fu} |"), 1)
                fila = next(l for l in dec.splitlines() if l.startswith("| 1.0 |"))
                self.assertEqual(re.findall(r"FU-\d+", fila), ["FU-01", "FU-02"])
                if esperado is None:
                    esperado = self.huellas()
                else:
                    self.assertEqual(self.huellas(), esperado)


if __name__ == "__main__":
    unittest.main(verbosity=2)
