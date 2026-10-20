"""Bloques de historial contiguos: lectura, inserción y guard de versión por CLI."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
PLUGIN = Path(os.environ.get("PLUGIN_A_PROBAR") or Path(__file__).resolve().parents[2]).resolve()
S = PLUGIN / "skills" / "appian-functional-analyst" / "scripts"


class TablasProyecto(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="tablas-proyecto-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.p = self.base / "Proyecto ficticio"
        self.cli("proyecto.py", "iniciar", self.p, "--nombre", "Reserva de salas")
        originales = [self.base / f"acta-{n}.txt" for n in range(1, 4)]
        for n, f in enumerate(originales, 1):
            f.write_text(f"Fuente ficticia {n}. Dato independiente {n}.\n", encoding="utf-8")
        self.cli("leer_fuentes.py", *originales, "-o", self.p / "fuentes")
        self.ids = [f["id"] for f in json.loads((self.p / "fuentes/indice.json").read_text(encoding="utf-8"))["fuentes"]]
        self.pm = self.p / "proyecto.md"
        self.sep = "|---|---|---|---|---|"

    def cli(self, script, *args, check=True):
        r = subprocess.run([sys.executable, "-B", "-X", "utf8", str(S / script), *map(str, args)],
                           capture_output=True, text=True, encoding="utf-8", timeout=30,
                           env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1", GIT_TERMINAL_PROMPT="0"))
        if check:
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return r

    def fila(self, fu):
        return f"| {fu} | 2026-10-20 | Texto ficticio | — | 0.1 |"

    def filas_fuentes(self, contiguas=(), sueltas=(), separacion="\n"):
        cola = separacion + "\n".join(sueltas) + "\n" if sueltas else ""
        filas = "\n".join(contiguas)
        self.pm.write_text(self.pm.read_text(encoding="utf-8").replace(
            self.sep + "\n", self.sep + "\n" + (filas + "\n" if filas else "") + cola, 1), encoding="utf-8")
        return cola

    def snapshot(self):
        return {str(f.relative_to(self.p)): f.read_bytes() for f in self.p.rglob("*.md")}

    def repetir_sin_duplicar(self, fu):
        antes = self.snapshot()
        r = self.cli("proyecto.py", "version", self.p, "--fuente", fu, "--que", "Otra vez", check=False)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("ya tiene versión", r.stderr)
        self.assertEqual(self.snapshot(), antes)

    def test_fila_contigua_es_historial_y_bloquea_version(self):
        self.filas_fuentes(contiguas=[self.fila(self.ids[0])])
        self.assertIn("3 catalogadas, 1 procesadas", self.cli("proyecto.py", "estado", self.p).stdout)
        self.repetir_sin_duplicar(self.ids[0])
        self.assertFalse((self.p / "versiones/v0.1").exists())

    def test_fila_tras_blanco_no_cuenta_ni_bloquea_fuente(self):
        suelta = self.fila(self.ids[0])
        cola = self.filas_fuentes(sueltas=[suelta])
        estado = self.cli("proyecto.py", "estado", self.p).stdout
        r = self.cli("proyecto.py", "version", self.p, "--fuente", self.ids[0], "--que", "Cambio ficticio", check=False)
        with self.subTest(operacion="lectura"):
            self.assertIn("3 catalogadas, 0 procesadas", estado)
        with self.subTest(operacion="version"):
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        if r.returncode == 0:
            texto = self.pm.read_text(encoding="utf-8")
            self.assertIn(self.sep + "\n| " + self.ids[0] + " |", texto)
            self.assertIn(cola, texto)
            self.assertEqual(texto.count(suelta), 1)
            self.assertIn("3 catalogadas, 1 procesadas", self.cli("proyecto.py", "estado", self.p).stdout)
            self.repetir_sin_duplicar(self.ids[0])

    def test_inserta_en_tabla_antes_de_texto_y_fila_suelta(self):
        primera, nueva, suelta = self.ids
        fila = self.fila(primera)
        cola = self.filas_fuentes([fila], [self.fila(suelta)], "Nota conservada fuera de la tabla.\n")
        estado = self.cli("proyecto.py", "estado", self.p).stdout
        self.cli("proyecto.py", "version", self.p, "--fuente", nueva, "--que", "Nueva fuente")
        texto = self.pm.read_text(encoding="utf-8")
        with self.subTest(operacion="lectura"):
            self.assertIn("3 catalogadas, 1 procesadas", estado)
        with self.subTest(operacion="insercion"):
            self.assertIn(fila + "\n| " + nueva + " |", texto)
        self.assertIn(cola, texto)
        with self.subTest(operacion="estado_posterior"):
            self.assertIn("3 catalogadas, 2 procesadas", self.cli("proyecto.py", "estado", self.p).stdout)
        self.repetir_sin_duplicar(nueva)

    def test_tabla_vacia_sin_filas_sueltas_conserva_alta_y_guard(self):
        self.cli("proyecto.py", "version", self.p, "--fuente", self.ids[0], "--que", "Primera fuente")
        self.assertIn(self.sep + "\n| " + self.ids[0] + " |", self.pm.read_text(encoding="utf-8"))
        self.assertIn("3 catalogadas, 1 procesadas", self.cli("proyecto.py", "estado", self.p).stdout)
        self.repetir_sin_duplicar(self.ids[0])

    def test_nota_antes_de_la_tabla_conserva_lectura_y_alta(self):
        self.filas_fuentes(contiguas=[self.fila(self.ids[0])])
        nota = "Nota conservada antes de la tabla."
        self.pm.write_text(self.pm.read_text(encoding="utf-8").replace(
            "## Fuentes procesadas\n", "## Fuentes procesadas\n\n" + nota + "\n", 1), encoding="utf-8")
        self.assertIn("3 catalogadas, 1 procesadas", self.cli("proyecto.py", "estado", self.p).stdout)
        self.cli("proyecto.py", "version", self.p, "--fuente", self.ids[1], "--que", "Nueva fuente")
        self.assertIn(nota, self.pm.read_text(encoding="utf-8"))
        self.assertIn("3 catalogadas, 2 procesadas", self.cli("proyecto.py", "estado", self.p).stdout)
        self.repetir_sin_duplicar(self.ids[1])

    def test_sin_tabla_no_lee_ni_modifica_la_seccion_siguiente(self):
        texto = self.pm.read_text(encoding="utf-8")
        ini = texto.index("## Fuentes procesadas")
        fin = texto.index("\n## ", ini + 3)
        otra = ("## Otra tabla\n\n| Fuente | Fecha | Qué es | Informe | Versión |\n"
                + self.sep + "\n" + self.fila(self.ids[0]) + "\n")
        texto = texto[:ini] + "## Fuentes procesadas\n\nSin tabla de fuentes.\n\n" + otra + texto[fin:]
        self.pm.write_text(texto, encoding="utf-8")
        self.assertIn("3 catalogadas, 0 procesadas", self.cli("proyecto.py", "estado", self.p).stdout)
        r = self.cli("proyecto.py", "version", self.p, "--fuente", self.ids[0], "--que", "Nueva fuente")
        self.assertIn("No hay dónde escribirla, añádela a mano", r.stdout)
        self.assertEqual(texto, self.pm.read_text(encoding="utf-8"))

    def test_versiones_y_decisiones_usan_el_mismo_bloque(self):
        dec = self.p / "analisis/decisiones.md"
        texto = dec.read_text(encoding="utf-8")
        suelta_v = f"| 8.8 | 2026-10-20 | Nota suelta | {self.ids[2]} | — |"
        suelta_d = f"| D-99 | 2026-10-20 | {self.ids[2]} | CAMBIA | Nota suelta | — | — | Sí |"
        texto = texto.replace("\n\n## Decisiones del cliente", "\n\n" + suelta_v + "\n\n## Decisiones del cliente")
        dec.write_text(texto + "\n" + suelta_d + "\n", encoding="utf-8")
        self.cli("proyecto.py", "version", self.p, "--fuente", self.ids[0], "--que", "Decisión ficticia",
                 "--decision", "CAMBIA", "—", "Texto nuevo", "Texto anterior")
        despues = dec.read_text(encoding="utf-8")
        with self.subTest(tabla="Versiones"):
            self.assertRegex(despues, r"\| 0\.1 [^\n]*\n\| 0\.2 \|")
        with self.subTest(tabla="Decisiones"):
            self.assertIn("|---|---|---|---|---|---|---|---|\n| D-01 |", despues)
        self.assertIn("\n\n" + suelta_v + "\n\n## Decisiones del cliente", despues)
        self.assertIn("\n\n" + suelta_d + "\n", despues)
        self.repetir_sin_duplicar(self.ids[0])


if __name__ == "__main__":
    unittest.main()
