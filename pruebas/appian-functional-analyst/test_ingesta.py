"""Regresión de ingesta: catálogo, adjuntos y decisiones explícitas sobre duplicados."""
import importlib.util
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
PLUGIN = pathlib.Path(os.environ.get("PLUGIN_A_PROBAR") or pathlib.Path(__file__).resolve().parents[2])
SCRIPT = PLUGIN / "skills/appian-functional-analyst/scripts/leer_fuentes.py"
spec = importlib.util.spec_from_file_location("ingesta", SCRIPT)
ingesta = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ingesta)


class Ingesta(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.raiz = pathlib.Path(self.tmp.name)
        self.entrada = self.raiz / "originales"
        self.entrada.mkdir()
        self.salida = self.raiz / "fuentes"

    def corre(self, *args, valido=True):
        r = subprocess.run([sys.executable, str(SCRIPT), *map(str, args), "-o", str(self.salida)],
                           capture_output=True, encoding="utf-8", env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        self.assertEqual(r.returncode == 0, valido, r.stdout + r.stderr)
        return r.stdout + r.stderr

    def fuentes(self):
        return json.loads((self.salida / "indice.json").read_text(encoding="utf-8"))["fuentes"]

    def test_imagenes_asociadas_accesibles_e_independientes(self):
        (self.entrada / "img").mkdir()
        (self.entrada / "img/pantalla uno.png").write_bytes(b"imagen enlazada")
        (self.entrada / "independiente.png").write_bytes(b"imagen independiente")
        (self.entrada / "documento.md").write_text(
            "# Documento\n![Pantalla](<img/pantalla%20uno.png>)\n![Otra][vista]\n"
            "[vista]: <img/pantalla%20uno.png>\n", encoding="utf-8")
        self.corre(self.entrada)
        fuentes = self.fuentes()
        self.assertEqual(len(fuentes), 2)
        self.assertEqual(sum(e["tipo"] == "Imagen" for e in fuentes), 1)
        doc = next(e for e in fuentes if e["salida"])
        md = (self.salida / doc["salida"]).read_text(encoding="utf-8")
        enlaces = re.findall(r"adjuntos/[^\s)]+", md)
        self.assertEqual(len(enlaces), 2)
        self.assertTrue(all((self.salida / p).read_bytes() == b"imagen enlazada" for p in enlaces))
        self.corre(self.entrada)
        self.assertEqual(len(self.fuentes()), 2)
        (self.entrada / "img/pantalla uno.png").write_bytes(b"pantalla actualizada")
        self.corre(self.entrada)
        self.assertEqual(len(self.fuentes()), 3, "la imagen también forma parte de la huella de su fuente")

    def test_eml_no_arrastra_retorno_de_carro(self):
        (self.entrada / "correo.eml").write_bytes(
            b"From: rol@example.invalid\r\nSubject: Acuerdo\r\nContent-Type: text/plain; charset=utf-8\r\n"
            b"\r\nPrimera linea\r\nSegunda linea\r\n")
        self.corre(self.entrada)
        contenido = (self.salida / self.fuentes()[0]["salida"]).read_bytes()
        self.assertNotIn(b"\r", contenido)
        self.assertIn(b"Primera linea\nSegunda linea", contenido)

    def test_destinos_solapados_no_cambian_la_prosa(self):
        (self.entrada / "a.png").write_bytes(b"imagen A")
        (self.entrada / "otra.png").write_bytes(b"imagen B")
        (self.entrada / "nota.md").write_text("La ruta a.png y otra.png es literal.\n"
            "![A](a.png) ![B](otra.png)\n", encoding="utf-8")
        self.corre(self.entrada)
        md = (self.salida / self.fuentes()[0]["salida"]).read_text(encoding="utf-8")
        self.assertIn("La ruta a.png y otra.png es literal.", md)
        destinos = re.findall(r"!\[[AB]\]\(([^)]+)\)", md)
        self.assertEqual([(self.salida / p).read_bytes() for p in destinos], [b"imagen A", b"imagen B"])

    def test_conserva_crlf_y_cuenta_palabras(self):
        (self.entrada / "nota.txt").write_text("una dos tres\ncuatro", encoding="utf-8")
        self.corre(self.entrada)
        self.assertEqual(self.fuentes()[0]["palabras"], 4)
        for nombre in ("indice.md", "indice.json"):
            p = self.salida / nombre
            p.write_bytes(p.read_bytes().replace(b"\n", b"\r\n"))
        (self.entrada / "otra.txt").write_text("cinco seis", encoding="utf-8")
        self.corre(self.entrada)
        for nombre in ("indice.md", "indice.json"):
            contenido = (self.salida / nombre).read_bytes()
            self.assertIn(b"\r\n", contenido)
            self.assertNotIn(b"\n", contenido.replace(b"\r\n", b""))

    def test_similitud_no_excluye_y_seleccion_reversible(self):
        texto = " ".join(f"palabra{i}" for i in range(200))
        (self.entrada / "a.txt").write_text("Titulo original\n" + texto, encoding="utf-8")
        (self.entrada / "b.txt").write_text("Otro titulo\n" + texto, encoding="utf-8")
        salida = self.corre(self.entrada)
        self.assertIn("se parece a FU-01", salida)
        self.assertTrue(all(not e.get("duplicada_de") for e in self.fuentes()))
        self.corre("--duplicada", "FU-02=FU-01", valido=False)
        self.corre("--duplicada", "FU-02=FU-01", "--motivo", "Solo cambia el titulo")
        self.assertEqual(self.fuentes()[1]["duplicada_de"], "FU-01")
        self.corre("--duplicada", "FU-01=FU-02", "--motivo", "ciclo", valido=False)
        self.assertNotIn("duplicada_de", self.fuentes()[0])
        self.corre("--restaurar", "FU-02")
        self.assertNotIn("duplicada_de", self.fuentes()[1])
        self.corre("--duplicada", "FU-02=FU-99", "--motivo", "inexistente", valido=False)

    def test_help_utf8_antes_de_argparse(self):
        for script in (SCRIPT, SCRIPT.with_name("unir_modulos.py")):
            r = subprocess.run([sys.executable, str(script), "--help"], capture_output=True,
                               env={**os.environ, "PYTHONIOENCODING": "cp1252", "PYTHONDONTWRITEBYTECODE": "1"})
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("ó", r.stdout.decode("utf-8"))

    def test_df_avisa_solo_pantallas_modificadas(self):
        if not shutil.which("node"):
            self.skipTest("Node no disponible")
        fixture = importlib.util.spec_from_file_location("fixture_analista", pathlib.Path(__file__).with_name("selftest.py"))
        modulo = importlib.util.module_from_spec(fixture)
        fixture.loader.exec_module(modulo)
        proyecto = self.raiz / "proyecto"
        modulo.con_unidades(proyecto)
        def word(*args):
            r = subprocess.run(["node", str(SCRIPT.with_name("df_docx.js")), str(proyecto), *args],
                               capture_output=True, encoding="utf-8")
            if "Cannot find module 'docx'" in r.stderr or "Falta el paquete docx" in r.stderr:
                self.skipTest("Paquete docx no disponible")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            return r.stdout + r.stderr
        mensaje = word("--cambio", "EV-02")
        self.assertIn("PAN-01: revisa y regenera sus capturas", mensaje)
        self.assertNotIn("revisa y regenera sus capturas", word("--cambio", "EV-03"))
        self.assertNotIn("revisa y regenera sus capturas", word())


if __name__ == "__main__":
    unittest.main()
