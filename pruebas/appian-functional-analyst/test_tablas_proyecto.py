"""Bloques de historial contiguos: lectura, inserción y guard de versión por CLI."""
import json
import os
import shutil
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
        estado = self.cli("proyecto.py", "estado", self.p).stdout
        self.assertIn("3 catalogadas, 0 procesadas", estado)
        self.assertNotIn("Historial:", estado)
        r = self.cli("proyecto.py", "version", self.p, "--fuente", self.ids[0], "--que", "Nueva fuente")
        self.assertIn("No hay dónde escribirla, añádela a mano", r.stdout)
        self.assertEqual(texto, self.pm.read_text(encoding="utf-8"))

    def test_estado_avisa_filas_sueltas_por_seccion_sin_contarlas_ni_modificarlas(self):
        primera, nueva, suelta = self.ids
        self.filas_fuentes([self.fila(primera)], [self.fila(suelta), self.fila(nueva)])
        dec = self.p / "analisis/decisiones.md"
        filas_v = (f"| 8.8 | 2026-10-20 | Nota suelta | {suelta} | — |",
                   f"| 8.9 | 2026-10-20 | Otra nota | {nueva} | — |")
        dec.write_text(dec.read_text(encoding="utf-8").replace("\n\n## Decisiones del cliente",
                       "\n\n" + "\n".join(filas_v) + "\n\n## Decisiones del cliente"), encoding="utf-8")
        antes = {f: f.read_bytes() for f in (self.pm, dec)}
        respuesta = self.cli("proyecto.py", "estado", self.p)
        self.assertIn("3 catalogadas, 1 procesadas", respuesta.stdout)
        for archivo, titulo, filas in ((self.pm, "Fuentes procesadas", (self.fila(suelta), self.fila(nueva))),
                                        (dec, "Versiones", filas_v)):
            with self.subTest(seccion=titulo):
                aviso = [l for l in respuesta.stdout.splitlines() if f"Historial: {archivo.relative_to(self.p).as_posix()}" in l]
                self.assertEqual(len(aviso), 1, respuesta.stdout)
                self.assertIn(titulo, aviso[0])
                lineas = archivo.read_text(encoding="utf-8").splitlines()
                for fila in filas:
                    self.assertIn(str(lineas.index(fila) + 1), aviso[0])
                self.assertIn("Si son historial, únelas a la tabla", aviso[0])
                self.assertEqual(archivo.read_bytes(), antes[archivo])
        self.cli("proyecto.py", "version", self.p, "--fuente", nueva, "--que", "Nueva fuente")
        self.assertIn(self.fila(primera) + "\n| " + nueva + " |", self.pm.read_text(encoding="utf-8"))
        self.assertIn("\n\n" + "\n".join(filas_v) + "\n\n## Decisiones del cliente", dec.read_text(encoding="utf-8"))
        self.repetir_sin_duplicar(nueva)

    def test_estado_no_avisa_tabla_normal_prosa_ni_tabla_de_seccion_siguiente(self):
        for archivo, titulo in ((self.pm, "Fuentes procesadas"),
                                (self.p / "analisis/decisiones.md", "Versiones")):
            lineas = archivo.read_text(encoding="utf-8").splitlines()
            ini = lineas.index("## " + titulo)
            fin = next((i for i in range(ini + 1, len(lineas)) if lineas[i].startswith("## ")), len(lineas))
            lineas[fin:fin] = ["Prosa conservada después de la tabla.", "", "## Otras anotaciones",
                               "", "| Dato | Valor |", "|---|---|", "| Ajeno | Conservado |", ""]
            archivo.write_text("\n".join(lineas) + "\n", encoding="utf-8")
        antes = {f: f.read_bytes() for f in (self.pm, self.p / "analisis/decisiones.md")}
        self.assertNotIn("Historial:", self.cli("proyecto.py", "estado", self.p).stdout)
        self.assertTrue(all(f.read_bytes() == contenido for f, contenido in antes.items()))
        self.cli("proyecto.py", "version", self.p, "--fuente", self.ids[0], "--que", "Primera fuente")
        self.assertNotIn("Historial:", self.cli("proyecto.py", "estado", self.p).stdout)
        self.assertIn("| Ajeno | Conservado |", self.pm.read_text(encoding="utf-8"))
        self.repetir_sin_duplicar(self.ids[0])

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


class FilasAnalisis(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="filas-analisis-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.fixture = Path(__file__).resolve().parent / "datos" / "autorizaciones"
        sys.path.insert(0, str(S))
        import modelo
        self.mo = modelo

    def copia(self, nombre):
        p = self.base / nombre
        shutil.copytree(self.fixture, p)
        return p

    def comprobar(self, p):
        return subprocess.run([sys.executable, "-B", "-X", "utf8", str(S / "comprobar.py"), str(p)],
                              capture_output=True, text=True, encoding="utf-8", timeout=30,
                              env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))

    def test_filas_sueltas_se_rechazan_sin_mutar_el_analisis(self):
        for tipo in ("RB", "AV", "DOC", "INT", "PC", "D", "PT"):
            with self.subTest(tipo=tipo):
                p = self.copia(tipo)
                m = self.mo.cargar(p)
                pieza = next(x for x in m.piezas.values() if x.tipo == tipo and x.forma == "fila")
                f = m.ruta(pieza.doc)
                lineas = f.read_text(encoding="utf-8").splitlines()
                lineas.insert(pieza.ini, "")
                f.write_text("\n".join(lineas) + "\n", encoding="utf-8")
                antes = {str(a.relative_to(p)): a.read_bytes() for a in p.rglob("*.md")}
                r = self.comprobar(p)
                self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
                self.assertIn("filas con ID dentro de una tabla con cabecera", r.stdout)
                self.assertIn(pieza.id + " (", r.stdout)
                self.assertIn("restaura la cabecera o une la fila a su tabla", r.stdout)
                self.assertEqual({str(a.relative_to(p)): a.read_bytes() for a in p.rglob("*.md")}, antes)

    def test_tablas_validas_conservan_decisiones_y_admiten_tablas_separadas(self):
        for tipo in (None, "PC", "D"):
            with self.subTest(tipo=tipo):
                p = self.copia(tipo or "control")
                m = self.mo.cargar(p)
                if tipo:
                    pieza = next(x for x in reversed(list(m.piezas.values())) if x.tipo == tipo and x.forma == "fila")
                    f = m.ruta(pieza.doc)
                    lineas = f.read_text(encoding="utf-8").splitlines()
                    separador = "|" + "---|" * len(self.mo.celdas(pieza.cabecera))
                    lineas[pieza.ini:pieza.ini] = ["", pieza.cabecera, separador]
                    f.write_text("\n".join(lineas) + "\n", encoding="utf-8")
                r = self.comprobar(p)
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
                self.assertNotIn("filas con ID dentro de una tabla con cabecera", r.stdout)
                self.assertEqual(self.mo.cargar(p).piezas["D-02"].estado, "Vigente")


if __name__ == "__main__":
    unittest.main()
