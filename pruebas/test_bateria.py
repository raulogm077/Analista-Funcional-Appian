"""Contrato del ejecutor de grupos, con procesos pequeños y aislados; no lanza la batería completa."""
import contextlib
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
import comprobar_plugin as cp


class Grupos(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="prueba-grupos-")
        self.addCleanup(self.tmp.cleanup)
        self.raiz = Path(self.tmp.name)
        self.patch_errores = patch.object(cp, "errores", [])
        self.patch_avisos = patch.object(cp, "avisos", [])
        self.patch_errores.start()
        self.patch_avisos.start()
        self.addCleanup(self.patch_errores.stop)
        self.addCleanup(self.patch_avisos.stop)

    def grupo(self, nombre, codigo, **extras):
        fichero = self.raiz / (nombre + ".py")
        fichero.write_text(codigo, encoding="utf-8")
        return {"nombre": nombre, "ruta": fichero.name, "orden": [sys.executable, str(fichero)], **extras}

    def ejecuta(self, grupos, trabajos=2, env=None):
        salida = io.StringIO()
        with contextlib.redirect_stdout(salida):
            medidas = cp.ejecuta_grupos(grupos, env or dict(os.environ), trabajos)
        return medidas, salida.getvalue()

    def test_procesos_realmente_coinciden_y_salida_no_se_mezcla(self):
        # Cada proceso espera al otro: ejecutarlos en serie falla. No exige un tiempo de máquina concreto.
        codigo = ("from pathlib import Path\nimport time\n"
                  "p=Path(__file__).parent\n(p / '{yo}.listo').touch()\n"
                  "fin=time.monotonic()+15\n"
                  "while not (p / '{otro}.listo').exists() and time.monotonic()<fin: time.sleep(.01)\n"
                  "assert (p / '{otro}.listo').exists(), 'el otro grupo no arrancó'\n"
                  "print('salida privada {yo}')\n")
        medidas, salida = self.ejecuta([self.grupo("uno", codigo.format(yo="uno", otro="dos")),
                                        self.grupo("dos", codigo.format(yo="dos", otro="uno"))])
        self.assertEqual([m["codigo"] for m in medidas], [0, 0])
        self.assertNotIn("salida privada", salida)
        self.assertEqual(salida.count("Prueba de "), 2)
        self.assertTrue(all(m["segundos"] >= 0 for m in medidas))

    def test_secuencial_respeta_orden_y_pasa_entorno_y_cwd(self):
        grupos = [self.grupo("uno", "from pathlib import Path\nPath('primero').write_text('ok')\n", cwd=str(self.raiz)),
                  self.grupo("dos", "import os\nfrom pathlib import Path\n"
                             "assert Path('primero').read_text()=='ok'\n"
                             "assert os.environ['PLUGIN_A_PROBAR']=='copia de prueba'\n", cwd=str(self.raiz))]
        medidas, _ = self.ejecuta(grupos, 1, dict(os.environ, PLUGIN_A_PROBAR="copia de prueba"))
        self.assertEqual([m["codigo"] for m in medidas], [0, 0])
        self.assertEqual([m["nombre"] for m in medidas], ["uno", "dos"])

    def test_fallo_no_oculta_otro_grupo_y_pytest_distingue_codigo_dos(self):
        grupos = [self.grupo("falla", "import sys\nprint('defecto reproducido',file=sys.stderr)\nsys.exit(1)"),
                  self.grupo("falta", "raise SystemExit(2)"),
                  self.grupo("pytest", "raise SystemExit(2)", pytest=True),
                  self.grupo("pasa", "print('ok')")]
        medidas, _ = self.ejecuta(grupos)
        self.assertEqual([m["codigo"] for m in medidas], [1, 2, 2, 0])
        self.assertEqual(len(cp.errores), 2)
        self.assertEqual(len(cp.avisos), 1)
        self.assertTrue(any("defecto reproducido" in e for e in cp.errores))

    def test_no_arranca_es_error_y_no_impide_los_demas(self):
        malo = {"nombre": "noexiste", "ruta": "noexiste", "orden": [str(self.raiz / "noexiste.exe")]}
        medidas, _ = self.ejecuta([malo, self.grupo("pasa", "pass")])
        self.assertEqual([m["codigo"] for m in medidas], [1, 0])
        self.assertEqual(len(cp.errores), 1)

    def test_limite_invalido_y_lista_vacia(self):
        with self.assertRaises(ValueError):
            self.ejecuta([], 0)
        medidas, _ = self.ejecuta([])
        self.assertEqual(medidas, [])


if __name__ == "__main__":
    unittest.main()
