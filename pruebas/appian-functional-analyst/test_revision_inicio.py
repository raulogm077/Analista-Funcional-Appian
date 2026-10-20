"""Regresión focal de iniciar/estado y del contrato de la primera versión.

Se ejecuta con unittest o pytest. Los proyectos ficticios se crean fuera del plugin.
"""
import json
import os
import pathlib
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

    def fuente(self):
        (self.p / "fuentes/indice.json").write_text(json.dumps({"fuentes": [
            {"id": "FU-01", "fecha": "2026-10-20", "tipo": "Acta"}]}), encoding="utf-8")

    def huellas(self):
        return {f.relative_to(self.p): f.read_bytes() for f in self.p.rglob("*.md")}

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

    def test_inicial_rechaza_versiones_ajenas_sin_escribir(self):
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

    def test_inicial_rechaza_snapshot_sin_escribir(self):
        self.fuente()
        (self.p / "versiones/v0.1").mkdir()
        antes = self.huellas()
        r = self.corre("version", self.p, "--inicial", "--fuente", "FU-01", "--que", "Primera entrega", check=False)
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
