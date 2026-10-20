"""Destinos URG sin elegir y textos de fuentes vigentes. Proyectos ficticios, sin red."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock

sys.dont_write_bytecode = True
import selftest as fixture
sys.path.insert(0, str(fixture.S))
import comprobar as cp
import modelo as mo
import unidades as un


DESTINOS = (
    ("Pendiente: el equipo debe decidir Desarrollo o Entorno de corrección", ""),
    ("Por decidir: Entorno de corrección", ""),
    ("Sin decidir: Desarrollo", ""),
    ("Desarrollo / Entorno de corrección", ""),
    ("Desarrollo o Entorno de corrección", ""),
    ("Desarrollo · Entorno de corrección", ""),
    ("Entorno de corrección / Desarrollo", ""),
    ("**Pendiente**: Entorno de corrección", ""),
    ("Desarrollo", "desarrollo"),
    ("Entorno de corrección", "correccion"),
    ("`Entorno de corrección`, reaplicar después en Desarrollo", "correccion"),
    ("Desarrollo <!-- plantilla: Entorno de corrección -->", "desarrollo"),
    ("Producción", ""),
    ("", ""),
)


class Consumidores(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="consumidores-")
        self.addCleanup(self.tmp.cleanup)
        self.raiz = Path(self.tmp.name)

    def test_destino_debe_estar_elegido(self):
        for valor, esperado in DESTINOS:
            with self.subTest(valor=valor):
                self.assertEqual(un.donde_se_corrige({"donde se corrige": valor}), esperado)
        self.assertEqual(un.donde_se_corrige(None), "")

    def test_puntuador_y_motor_interpretan_igual_sin_cambiar_puntuador(self):
        ruta = fixture.PLUGIN / "pruebas/evaluaciones/evolutivo-urgencia/puntuar.py"
        antes = ruta.read_bytes()
        spec = importlib.util.spec_from_file_location("puntuador_revision_consumidores", ruta)
        puntuador = importlib.util.module_from_spec(spec)
        with mock.patch.object(sys, "path", [str(ruta.parent), *sys.path]):
            spec.loader.exec_module(puntuador)
        for valor, esperado in DESTINOS:
            with self.subTest(valor=valor):
                campos = {"donde se corrige": valor}
                self.assertEqual(puntuador.donde_es(campos), esperado)
                self.assertEqual(puntuador.donde_es(campos), un.donde_se_corrige(campos))
        self.assertEqual(ruta.read_bytes(), antes)

    def test_cli_produccion_rechaza_indecision_con_colision_sin_escribir(self):
        for n, valor in enumerate((DESTINOS[0][0], DESTINOS[3][0], DESTINOS[6][0])):
            with self.subTest(valor=valor):
                p = fixture.con_unidades(self.raiz / str(n))
                f = p / "impacto/URG-01.md"
                f.write_text(f.read_text(encoding="utf-8").replace("| Dónde se corrige | Entorno de corrección |",
                             f"| Dónde se corrige | {valor} |"), encoding="utf-8")
                self.assertTrue(un.Contexto(mo.Proyecto(p)).colision("URG-01")["choques"])
                cambios = p / "analisis/cambios.md"
                antes = cambios.read_bytes()
                code, out = fixture.corre(fixture.S / "proyecto.py", "cambio", p, "URG-01", "produccion", "--ref", "PASE-FICTICIO")
                self.assertEqual(code, 1, out)
                self.assertIn("Dónde se corrige", out)
                self.assertEqual(cambios.read_bytes(), antes)

    def test_cli_destino_elegido_permite_cierre_con_comprobacion_pendiente(self):
        p = fixture.con_unidades(self.raiz / "urgencia")
        f = p / "impacto/URG-01.md"
        f.write_text(f.read_text(encoding="utf-8").replace("| Cierre | — |",
                     "| Cierre | Pendiente: comprobar en producción tras el pase |"), encoding="utf-8")
        code, out = fixture.corre(fixture.S / "proyecto.py", "cambio", p, "URG-01", "produccion", "--ref", "PASE-FICTICIO")
        self.assertEqual(code, 0, out)
        self.assertIn("En producción", fixture.fila_de(p, "URG-01"))
        self.assertIn("Pendiente: comprobar", f.read_text(encoding="utf-8"))

    def proyecto(self):
        p = self.raiz / "proyecto"
        shutil.copytree(fixture.EJEMPLO, p)
        fuentes = p / "fuentes"
        fuentes.mkdir()
        return p, fuentes

    def catalogo(self, fuentes, filas):
        (fuentes / "indice.json").write_text(json.dumps({"fuentes": filas}), encoding="utf-8")

    def fuente(self, fuentes, nombre="FU-91-anterior.md", marcas=("00:01:00",)):
        f = fuentes / nombre
        f.write_text("# Fuente ficticia\n- Participantes: Persona Ficticia\n\n---\n" +
                     "\n".join(f"[{h}] Persona Ficticia: texto anterior." for h in marcas) + "\n", encoding="utf-8")
        return f

    def captura(self, fn, *args):
        out = io.StringIO()
        with mock.patch.object(cp, "errores", 0), contextlib.redirect_stdout(out):
            fn(*args)
        return out.getvalue()

    def test_recatalogar_vacia_conserva_derivado_pero_no_lo_consume(self):
        p, fuentes = self.proyecto()
        entrada = p / "vacio.txt"
        entrada.write_text("", encoding="utf-8")
        code, out = fixture.corre(fixture.S / "leer_fuentes.py", entrada, "-o", fuentes)
        self.assertEqual(code, 0, out)
        indice = fuentes / "indice.json"
        estado = json.loads(indice.read_text(encoding="utf-8"))
        estado["fuentes"][0].update(salida="FU-01-vacio.md", detalle="1 líneas")
        derivado = fuentes / "FU-01-vacio.md"
        derivado.write_text("# FU-01\n\n---\n\n", encoding="utf-8")
        antes = derivado.read_bytes()
        indice.write_text(json.dumps(estado), encoding="utf-8")
        code, out = fixture.corre(fixture.S / "leer_fuentes.py", entrada, "-o", fuentes)
        self.assertEqual(code, 0, out)
        self.assertEqual(json.loads(indice.read_text(encoding="utf-8"))["fuentes"][0]["salida"], "")
        self.assertEqual(derivado.read_bytes(), antes)
        self.assertEqual(cp.textos_fuentes(fuentes), [])

    def test_cli_no_usa_residual_para_citas_participantes_ni_informe(self):
        p, fuentes = self.proyecto()
        residual = self.fuente(fuentes)
        antes = residual.read_bytes()
        self.catalogo(fuentes, [{"id": "FU-91", "salida": "", "detalle": "no leído: sin texto", "palabras": 0}])
        f = p / "analisis/funcional.md"
        f.write_text(f.read_text(encoding="utf-8") + "\n<!-- Persona Ficticia FU-91 00:01:30 -->\n", encoding="utf-8")
        impacto = p / "impacto/FU-91.md"
        impacto.parent.mkdir()
        impacto.write_text("# Impacto de FU-91\nAnálisis base: versión 1.0 · Estado: pendiente\n\nFU-91 00:01:30\n", encoding="utf-8")
        code, out = fixture.corre(fixture.S / "comprobar.py", p, "--fuentes", fuentes, "--impacto", impacto)
        self.assertEqual(code, 0, out)
        self.assertNotIn("Persona Ficticia", out)
        self.assertNotIn("→ FU-91 00:01:30", out)
        self.assertEqual(residual.read_bytes(), antes)

    def test_no_corrige_cita_con_marcas_de_un_derivado_fuera_del_catalogo(self):
        p, fuentes = self.proyecto()
        residual = self.fuente(fuentes)
        self.catalogo(fuentes, [])
        f = p / "analisis/funcional.md"
        f.write_text(f.read_text(encoding="utf-8") + "\n<!-- FU-91 00:01:30 -->\n", encoding="utf-8")
        antes = f.read_bytes()
        self.captura(cp.comprobar_fuentes, mo.Proyecto(p), fuentes, True)
        self.assertEqual(f.read_bytes(), antes)
        self.assertTrue(residual.is_file())

    def test_solo_salida_vigente_del_mismo_id_y_no_archivo_anterior(self):
        p, fuentes = self.proyecto()
        residual = self.fuente(fuentes)
        activa = self.fuente(fuentes, "FU-91-vigente.md", ("00:02:00",))
        self.catalogo(fuentes, [{"id": "FU-91", "salida": activa.name}])
        self.assertEqual(cp.textos_fuentes(fuentes), [("91", activa)])
        f = p / "analisis/funcional.md"
        f.write_text(f.read_text(encoding="utf-8") + "\n<!-- FU-91 00:02:00 -->\n", encoding="utf-8")
        out = self.captura(cp.comprobar_fuentes, mo.Proyecto(p), fuentes, False)
        self.assertNotIn("✗", out)
        self.assertTrue(residual.is_file())

    def test_activa_aun_detecta_minuto_incorrecto_y_participantes(self):
        p, fuentes = self.proyecto()
        activa = self.fuente(fuentes)
        self.catalogo(fuentes, [{"id": "FU-91", "salida": activa.name}])
        f = p / "analisis/funcional.md"
        f.write_text(f.read_text(encoding="utf-8") + "\n<!-- Persona Ficticia FU-91 00:01:30 -->\n", encoding="utf-8")
        out = self.captura(cp.comprobar_fuentes, mo.Proyecto(p), fuentes, False)
        self.assertIn("✗ citas con el minuto", out)
        self.assertIn("✗ sin nombres de participantes", out)
        self.captura(cp.comprobar_fuentes, mo.Proyecto(p), fuentes, True)
        self.assertIn("FU-91 00:01:00", f.read_text(encoding="utf-8"))

    def test_cobertura_solo_de_texto_vigente_y_respeta_duplicadas(self):
        p, fuentes = self.proyecto()
        residual = self.fuente(fuentes, marcas=tuple(f"00:01:0{i}" for i in range(5)))
        self.catalogo(fuentes, [{"id": "FU-91", "salida": ""}])
        out = self.captura(cp.comprobar_fuentes, mo.Proyecto(p), fuentes, False)
        self.assertNotIn("→ FU-91 00–10 min", out)
        filas = [{"id": "FU-91", "salida": residual.name}, {"id": "FU-92", "salida": ""}]
        self.catalogo(fuentes, filas)
        out = self.captura(cp.comprobar_fuentes, mo.Proyecto(p), fuentes, False)
        self.assertIn("→ FU-91 00–10 min", out)
        filas[0].update(duplicada_de="FU-92", motivo_duplicada="Misma reunión")
        self.catalogo(fuentes, filas)
        out = self.captura(cp.comprobar_fuentes, mo.Proyecto(p), fuentes, False)
        self.assertNotIn("→ FU-91 00–10 min", out)

    def test_informe_activo_sigue_detectando_citas_incorrectas(self):
        p, fuentes = self.proyecto()
        activa = self.fuente(fuentes)
        self.catalogo(fuentes, [{"id": "FU-91", "salida": activa.name}])
        impacto = p / "FU-91.md"
        impacto.write_text("# Impacto de FU-91\n\nFU-91 00:01:30\n", encoding="utf-8")
        out = self.captura(cp.comprobar_informe_previo, mo.Proyecto(p), impacto, fuentes)
        self.assertIn("✗ citas del informe", out)

    def test_proyecto_legado_sin_indice_sigue_leyendo_fu_md(self):
        p, fuentes = self.proyecto()
        activa = self.fuente(fuentes)
        self.assertEqual(cp.textos_fuentes(fuentes), [("91", activa)])
        f = p / "analisis/funcional.md"
        f.write_text(f.read_text(encoding="utf-8") + "\n<!-- FU-91 00:01:30 -->\n", encoding="utf-8")
        out = self.captura(cp.comprobar_fuentes, mo.Proyecto(p), fuentes, False)
        self.assertIn("✗ citas con el minuto", out)

    def test_indice_existente_invalido_falla_sin_volver_a_derivados(self):
        p, fuentes = self.proyecto()
        residual = self.fuente(fuentes)
        antes = residual.read_bytes()
        for contenido in ("null", "{}", '{"fuentes": [}'):
            with self.subTest(indice=contenido):
                (fuentes / "indice.json").write_text(contenido, encoding="utf-8")
                code, out = fixture.corre(fixture.S / "comprobar.py", p, "--fuentes", fuentes)
                self.assertEqual(code, 1, out)
                self.assertIn("No puedo leer el catálogo de fuentes", out)
                self.assertIn("indice.json", out)
                self.assertNotIn("Sin errores.", out)
                self.assertEqual(residual.read_bytes(), antes)


if __name__ == "__main__":
    unittest.main()
