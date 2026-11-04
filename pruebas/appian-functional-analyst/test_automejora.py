"""Regresiones de automejora sobre proyectos ficticios, sin red ni Appian."""
import contextlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
from types import SimpleNamespace
import unittest
import unittest.mock

sys.dont_write_bytecode = True
import selftest as fixture
sys.path.insert(0, str(fixture.S))
import modelo as mo
import issues as iss
import unidades as un
import indice
import proyecto
import comprobar


class Automejora(unittest.TestCase):
    def test_aplicacion_en_plan_genera_tipo_esperado(self):
        m = self.copia()
        ctx = un.Contexto(m)
        for tipo, esperado in (("Aplicación", "application"), ("Aplicacion", "application"),
                               ("Application", "application"), ("Grupo de la aplicación", "group"),
                               ("Regla de expresión de la aplicación", "expressionRule"),
                               ("Aplicación (con grupos y carpetas generados)", "application"),
                               ("Interfaz sobre Record type", "interface")):
            with self.subTest(tipo=tipo):
                filas = [{"tipo": tipo, "situacion": "nuevo", "objetos": ["AUT Objeto ficticio"]}]
                self.assertEqual(ctx.esperado("EV-01", filas=filas), {"AUT Objeto ficticio": {"tipo": esperado}})

    def test_esperado_de_una_parte_de_record_type(self):
        """L1 del ensayo Informes: «`X` — acción «…»» perdía la parte (fuera de las comillas invertidas) y la issue de
        la acción heredaba los campos nuevos de toda la unidad. La parte se conserva; una parte de campos espera esos
        campos, y la de una acción, la acción."""
        for celda, objetos in (("`AUT Accion` — acción «Reenviar»", ["AUT Accion — acción «Reenviar»"]),
                               ("`A`, `B`", ["A", "B"]), ("`A` y `B`", ["A", "B"]),
                               # una fila con parte nombra un solo objeto: la parte llega hasta el final
                               ("`AUT Accion` — acción «Cancelar», de quien la creó",
                                ["AUT Accion — acción «Cancelar», de quien la creó"]),
                               ("`A` — campo `importe`, `fecha`", ["A — campo importe, fecha"]),
                               ("`AUT Accion — campo importe`", ["AUT Accion — campo importe"]),
                               ("`AUT Accion` — campo `importe`", ["AUT Accion — campo importe"]),
                               ("`MNT_IF_Panel()`", ["MNT_IF_Panel"]), ("`rule!X`", ["X"]), ("—", [])):
            with self.subTest(celda=celda):
                self.assertEqual(un.objetos_celda(celda), objetos)
        self.assertEqual(un.campos_de_parte("campos fechaEnvio y fechaCierre (DT-49)"), ["fechaEnvio", "fechaCierre"])
        self.assertEqual(un.campos_de_parte("acción «Reenviar»"), [])
        # revisión de Codex: lo que sigue a los campos («relación …») no es un campo
        self.assertEqual(un.campos_de_parte("campos motivo, canceladoPor y fecha y relación canceladoPorUsuario"),
                         ["motivo", "canceladoPor", "fecha"])
        self.assertEqual(un.campos_de_parte("campo descripcion (Text 255)"), ["descripcion"])
        ctx = un.Contexto(self.copia())
        campo = ctx.esperado("EV-01", filas=[{"tipo": "Record type (parte)", "situacion": "modifica",
                                              "objetos": ["AUT Solicitud — campo titulo"]}])
        self.assertEqual([c["nombre"] for c in campo["AUT Solicitud"]["campos"]], ["titulo"])
        accion = ctx.esperado("EV-01", filas=[{"tipo": "Record type (parte)", "situacion": "modifica",
                                               "objetos": ["AUT Solicitud — acción «Reenviar»"]}])
        self.assertNotIn("campos", accion["AUT Solicitud"])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="automejora-")
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        self.p = self.root / "proyecto"
        cfg = self.root / "gitconfig"
        cfg.write_text("", encoding="utf-8")
        self.env = unittest.mock.patch.dict(os.environ, {
            "GIT_CONFIG_GLOBAL": str(cfg), "GIT_CONFIG_NOSYSTEM": "1", "GIT_TERMINAL_PROMPT": "0",
            "GIT_AUTHOR_NAME": "Prueba", "GIT_AUTHOR_EMAIL": "prueba@example.com",
            "GIT_COMMITTER_NAME": "Prueba", "GIT_COMMITTER_EMAIL": "prueba@example.com"})
        self.env.start()
        self.addCleanup(self.env.stop)

    def copia(self):
        shutil.copytree(fixture.EJEMPLO, self.p)
        return mo.Proyecto(self.p)

    def preparada(self):
        fixture.nueva_con_issues(self.p)
        code, out = fixture.corre(fixture.S / "proyecto.py", "cambio", self.p, "EV-01", "aprobada", "--fuente", "FU-05")
        self.assertEqual(code, 0, out)
        m = mo.Proyecto(self.p)
        return m, iss.calcula(m, un.Contexto(m), "EV-01")

    def captura(self, fn, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            fn(*args)
        return out.getvalue()

    def test_aviso_requisito_sin_escenarios_remite_al_alcance_aprobado(self):
        """La inicial atribuye también requisitos sin objeto: puede faltar cobertura o estar diferidos expresamente.
        El aviso conserva ambos casos, sin ampliar el alcance por la prosa ni apagarse al marcar Construida."""
        for tipo, diferida in (("HU", False), ("HU", True), ("INT", False), ("INT", True)):
            with self.subTest(tipo=tipo, diferida=diferida):
                self.p = self.root / (tipo + ("-diferida" if diferida else "-omision"))
                fixture.nueva_con_issues(self.p)
                f = self.p / "analisis/funcional.md"
                pid = tipo + "-90"
                if tipo == "HU":
                    seccion = "## 5. Pantallas"
                    cuerpo = ("| Perfil | Pantalla | Paso | Prioridad |\n|---|---|---|---|\n"
                              "| Consulta | — | — | Deseable |\n\n"
                              "Como Consulta, quiero consultar el histórico para conocer las solicitudes anteriores.")
                else:
                    seccion = "## 10. Condiciones de uso"
                    cuerpo = "| Campo | Valor |\n|---|---|\n| Sistema | Histórico ficticio |"
                ficha = (f"**{pid} — Consultar el histórico ficticio** <!-- ✅ FU-05 -->\n\n{cuerpo}\n\n"
                         f"Se acepta si:\n\n- `{pid}.1` Dada una solicitud anterior, cuando se consulta el histórico, "
                         "entonces se obtiene la solicitud.\n\n")
                fixture.editar(f, seccion, ficha + seccion)
                alcance = (f"{pid} queda fuera de EV-01 y se planifica y prueba con una unidad posterior." if diferida else
                           f"{pid} y su criterio {pid}.1 forman parte del alcance aprobado de EV-01.")
                fixture.editar(self.p / "analisis/tecnico.md", "## 14.", alcance + "\n\n## 14.")
                fuente = self.p / "fuentes/FU-05-aprobacion.md"
                fuente.parent.mkdir(parents=True, exist_ok=True)
                mo.escribe(fuente, "# FU-05 · Aprobación ficticia\n\nApruebo EV-01 con el alcance de técnico §13. "
                           + alcance + "\n")
                code, out = fixture.corre(fixture.S / "proyecto.py", "cambio", self.p, "EV-01", "aprobada",
                                          "--fuente", "FU-05")
                self.assertEqual(code, 0, out)
                for estado in (un.APROBADA, un.CONSTRUIDA):
                    with self.subTest(estado=estado):
                        m = mo.Proyecto(self.p)
                        ctx = un.Contexto(m)
                        ctx.por_id["EV-01"].estado = estado
                        plan = iss.calcula(m, ctx, "EV-01")
                        self.assertFalse(any(pid in i.requisitos or pid + ".1" in i.criterios for i in plan.issues))
                        avisos = [a for a in plan.avisos if pid in a and "escenarios" in a]
                        self.assertEqual(len(avisos), 1)
                        self.assertTrue(avisos[0].startswith("requisitos con criterios"))
                        self.assertIn(f"sin escenarios en las issues de EV-01: {pid}", avisos[0])
                        self.assertIn("alcance aprobado", avisos[0])
                        self.assertIn("diferidos expresamente", avisos[0])
                        self.assertNotIn("criterios que construye EV-01", avisos[0])

    def test_dt_referida_desde_objeto_base_lleva_su_seguridad(self):
        """Caso B: la tabla del record type cita una DT cuya necesidad es una regla común, no «Base»."""
        self.preparada()
        tecnico = self.p / "analisis/tecnico.md"
        texto = tecnico.read_text(encoding="utf-8")
        self.assertIn("| **Necesidad** | RB-01, HU-02, HU-09 |", texto)
        texto = texto.replace("| **Necesidad** | RB-01, HU-02, HU-09 |", "| **Necesidad** | RB-01 |")
        condicion = "Nadie más entra (RB-01): los demás usuarios no tienen acceso al registro."
        texto = texto.replace("## 5.", condicion + "\n\n## 5.", 1)
        texto = texto.replace("## 3. Modelo de datos", "**DT-90 — Presentación ajena a la Base**\n\n"
                              "| Campo | Contenido |\n|---|---|\n"
                              "| **Necesidad** | HU-02 |\n"
                              "| **Decisión** | La pantalla presenta `AUT Solicitud` en dos columnas |\n"
                              "| **Por qué** | Presentación de HU-02 |\n\n## 3. Modelo de datos", 1)
        tecnico.write_text(texto, encoding="utf-8")
        m = mo.Proyecto(self.p)
        plan = iss.calcula(m, un.Contexto(m), "EV-01", estreno=True)
        base = next(i for i in plan.issues if i.comun)
        self.assertIn("- DT-02 Visibilidad por unidad con seguridad de registro", base.texto)
        self.assertIn("Users found in fields", base.texto)
        self.assertIn(condicion, base.texto)
        # Nombrar el mismo objeto sin que su especificación cite la DT sigue sin alterar la Base.
        self.assertNotIn("DT-90 Presentación ajena", base.texto)

    def test_dt_del_objeto_llega_tambien_a_una_issue_sin_base(self):
        self.preparada()
        tecnico = self.p / "analisis/tecnico.md"
        texto = tecnico.read_text(encoding="utf-8")
        texto = texto.replace("| **Necesidad** | RB-01, HU-02, HU-09 |", "| **Necesidad** | Seguridad del registro |")
        texto = texto.replace("| **Decisión** | `AUT Solicitud` lleva", "| **Decisión** | Para cumplir RB-01, `AUT Solicitud` lleva", 1)
        condicion = "Nadie más entra (RB-01): los demás usuarios no tienen acceso al registro."
        texto = texto.replace("## 5.", condicion + "\n\n## 5.", 1)
        texto = re.sub(r"## 13\..*?(?=## 14\.)", "## 13. Plan de construcción\n\n"
                       "| Paso | Objeto | Tipo | Situación | Sustituye a | Cambio | Para |\n"
                       "|---|---|---|---|---|---|---|\n"
                       "| 1 | `AUT Solicitud` | Record type | Nuevo | — | EV-01 | HU-01 |\n\n",
                       texto, flags=re.S)
        tecnico.write_text(texto, encoding="utf-8")
        m = mo.Proyecto(self.p)
        plan = iss.calcula(m, un.Contexto(m), "EV-01", estreno=True)
        self.assertEqual(len(plan.issues), 1)
        propia = plan.issues[0]
        self.assertFalse(propia.comun)
        self.assertIn("- DT-02 Visibilidad por unidad con seguridad de registro", propia.texto)
        self.assertIn(condicion, propia.texto)

    def test_dt_de_otra_definicion_no_entra_por_una_linea_de_contexto(self):
        self.preparada()
        tecnico = self.p / "analisis/tecnico.md"
        texto = tecnico.read_text(encoding="utf-8")
        lineas = texto.splitlines()
        for n, linea in enumerate(lineas):
            if linea.startswith("| PAN-02 |"):
                celdas = mo.celdas(linea)
                celdas[-1] += " (HU-01; DT-92)"
                lineas[n] = "| " + " | ".join(celdas) + " |"
        texto = "\n".join(lineas) + "\n"
        texto = texto.replace("## 3. Modelo de datos", "**DT-92 — Columnas propias de la ficha**\n\n"
                              "| Campo | Contenido |\n|---|---|\n"
                              "| **Necesidad** | Presentación de la ficha |\n"
                              "| **Decisión** | `AUT_FichaSolicitud` presenta `AUT Solicitud` en dos columnas |\n"
                              "| **Por qué** | Diseño de la ficha |\n\n## 3. Modelo de datos", 1)
        tecnico.write_text(texto, encoding="utf-8")
        m = mo.Proyecto(self.p)
        plan = iss.calcula(m, un.Contexto(m), "EV-01", estreno=True)
        ficha = next(i for i in plan.issues if "AUT_FichaSolicitud" in i.objetos)
        regla = next(i for i in plan.issues if "AUT_GenerarNumero" in i.objetos)
        base = next(i for i in plan.issues if i.comun)
        self.assertIn("- DT-92 Columnas propias de la ficha", ficha.texto)
        self.assertNotIn("- DT-92 Columnas propias de la ficha", regla.texto)
        self.assertNotIn("- DT-92 Columnas propias de la ficha", base.texto)

    def test_dt_de_contexto_no_convierte_sus_menciones_en_dependencias(self):
        self.preparada()
        tecnico = self.p / "analisis/tecnico.md"
        texto = tecnico.read_text(encoding="utf-8")
        lineas = texto.splitlines()
        for n, linea in enumerate(lineas):
            if linea.startswith("| PAN-02 |"):
                lineas[n] = linea[:-1] + " (DT-92) |"
        texto = "\n".join(lineas) + "\n"
        texto = texto.replace("## 3. Modelo de datos", "**DT-92 — Alcance de la ficha**\n\n"
                              "| Campo | Contenido |\n|---|---|\n"
                              "| **Necesidad** | Presentación de la ficha |\n"
                              "| **Decisión** | La ficha no modifica `AUT_PlantillaAutorizacion` |\n"
                              "| **Por qué** | Son objetos independientes |\n\n## 3. Modelo de datos", 1)
        tecnico.write_text(texto, encoding="utf-8")
        def ficha():
            m = mo.Proyecto(self.p)
            plan = iss.calcula(m, un.Contexto(m), "EV-01", estreno=True)
            return next(i for i in plan.issues if "AUT_FichaSolicitud" in i.objetos)
        propia = ficha()
        self.assertIn("La ficha no modifica `AUT_PlantillaAutorizacion`", propia.texto)
        self.assertNotIn("AUT_PlantillaAutorizacion", propia.nombra)
        # El comportamiento anterior de las DT seleccionadas por «Necesidad» se conserva.
        tecnico.write_text(texto.replace("| **Necesidad** | Presentación de la ficha |",
                                        "| **Necesidad** | HU-06 |").replace("La ficha no modifica", "La ficha usa"),
                           encoding="utf-8")
        self.assertIn("AUT_PlantillaAutorizacion", ficha().nombra)

    def test_dt_de_una_accion_no_arrastra_la_de_otra_parte_del_record(self):
        self.preparada()
        tecnico = self.p / "analisis/tecnico.md"
        texto = tecnico.read_text(encoding="utf-8")
        for dt, accion in (("DT-95", "Nueva solicitud"), ("DT-96", "Reenviar")):
            texto = texto.replace("## 3. Modelo de datos", f"**{dt} — Visibilidad de {accion}**\n\n"
                                  "| Campo | Contenido |\n|---|---|\n"
                                  "| **Necesidad** | Visibilidad de la acción |\n"
                                  f"| **Decisión** | Solo técnicos en {accion} |\n"
                                  "| **Por qué** | Segregación |\n\n## 3. Modelo de datos", 1)
        texto = texto.replace("## 8. Procesos", "Acciones de registro de `AUT Solicitud`\n\n"
                              "| Acción | Tipo | Proceso | Quién la ve |\n|---|---|---|---|\n"
                              "| «Nueva solicitud» | De lista | `AUT Tramitar Solicitud` | Técnicos (DT-95) |\n"
                              "| «Reenviar» | Relacionada | `AUT Tramitar Solicitud` | Técnicos (DT-96) |\n\n"
                              "## 8. Procesos", 1)
        texto = re.sub(r"## 13\..*?(?=## 14\.)", "## 13. Plan de construcción\n\n"
                       "| Paso | Objeto | Tipo | Situación | Sustituye a | Cambio | Para |\n"
                       "|---|---|---|---|---|---|---|\n"
                       "| 1 | `AUT Solicitud` — acción «Nueva solicitud» | Record type | Modifica | — | EV-01 | HU-01 |\n\n",
                       texto, flags=re.S)
        tecnico.write_text(texto, encoding="utf-8")
        m = mo.Proyecto(self.p)
        plan = iss.calcula(m, un.Contexto(m), "EV-01", estreno=True)
        self.assertEqual(len(plan.issues), 1)
        self.assertIn("- DT-95 Visibilidad de Nueva solicitud", plan.issues[0].texto)
        self.assertNotIn("- DT-96 Visibilidad de Reenviar", plan.issues[0].texto)

    def test_tecnico_completo_sin_dt_ni_datos_activa_criterios_y_estado_cli(self):
        self.copia()
        f = self.p / "analisis/tecnico.md"
        f.write_text("# Técnico ficticio\n\nVersión: 1.1 · Estado: completo para reglas puras\n\n"
                     "## 2. Decisiones técnicas\nSin decisiones específicas.\n"
                     "## 3. Modelo de datos\nNo hay datos persistentes.\n"
                     "## 6. Lógica\nReglas puras para HU-01.\n"
                     "## 13. Plan de construcción\n"
                     "| Paso | Objeto | Tipo | Situación | Sustituye a | Para |\n|---|---|---|---|---|---|\n"
                     "| 1 | `AUT_GenerarNumero` | Regla de expresión | Nuevo | — | HU-01 |\n"
                     "## 14. Pruebas y trazabilidad\n"
                     "| Criterio | Cómo se prueba | Con qué |\n|---|---|---|\n"
                     "| HU-01.2 | Prueba ficticia | Caso de prueba de `AUT_GenerarNumero` |\n",
                     encoding="utf-8")
        m = mo.Proyecto(self.p)
        self.assertFalse(m.vigentes("DT"))
        self.assertFalse(m.tablas("T", "3"))
        self.assertEqual(mo.estado_tecnico(m), (True, True))
        self.assertEqual(comprobar.estado_tecnico(m), mo.estado_tecnico(m))
        code, out = fixture.corre(fixture.S / "proyecto.py", "estado", self.p)
        self.assertEqual(code, 0, out)
        self.assertIn("Técnico: versión 1.1", out)
        self.assertNotIn("Técnico: versión 1.1, sin empezar", out)
        code, out = fixture.corre(fixture.S / "comprobar.py", self.p)
        self.assertNotEqual(code, 0, out)
        self.assertTrue(any(l.startswith("✗ técnico §14: cada criterio") and "HU-01.1" in l
                            for l in out.splitlines()), out)

    def test_tecnico_plantilla_y_ausente_conservan_sin_empezar(self):
        self.copia()
        tecnico = self.p / "analisis/tecnico.md"
        plantilla = fixture.SKILL / "assets/plantillas/tecnico.md"
        shutil.copyfile(plantilla, tecnico)
        m = mo.Proyecto(self.p)
        self.assertEqual(mo.estado_tecnico(m), (False, False))
        self.assertEqual(comprobar.estado_tecnico(m), (False, False))
        self.assertIn("sin empezar", self.captura(comprobar.comprobar_tecnico, m, un.Contexto(m)))
        code, out = fixture.corre(fixture.S / "proyecto.py", "estado", self.p)
        self.assertEqual(code, 0, out)
        self.assertIn("Técnico: versión 0.1, sin empezar", out)
        tecnico.unlink()
        self.assertEqual(mo.estado_tecnico(mo.Proyecto(self.p)), (False, False))

    def test_tecnico_dt_campos_y_cabecera_ambigua_conservan_semantica(self):
        self.copia()
        f = self.p / "analisis/tecnico.md"
        for estado in ("completo", "en curso", "pendiente de revisión", None):
            for contenido in ("vacío", "DT", "campos"):
                with self.subTest(estado=estado, contenido=contenido):
                    cabecera = "" if estado is None else " · Estado: " + estado
                    texto = "# Técnico ficticio\n\nVersión: 1.1" + cabecera + "\n\n## 2. Decisiones técnicas\n"
                    if contenido == "DT":
                        texto += "**DT-01 — Decisión ficticia**\nDetalle pendiente.\n"
                    texto += "\n## 3. Modelo de datos\n"
                    if contenido == "campos":
                        texto += "| Campo | Tipo | Uso |\n|---|---|---|\n| valor | Integer | Técnico: ensayo |\n"
                    f.write_text(texto, encoding="utf-8")
                    m = mo.Proyecto(self.p)
                    esperado = (estado == "completo" or contenido != "vacío", estado == "completo")
                    self.assertEqual(mo.estado_tecnico(m), esperado)
                    self.assertEqual(comprobar.estado_tecnico(m), esperado)
                    with unittest.mock.patch.object(comprobar, "errores", 0):
                        out = self.captura(comprobar.comprobar_tecnico, m, un.Contexto(m))
                    if esperado[0]:
                        self.assertIn("técnico completo: lo que falta es error" if esperado[1]
                                      else "técnico en curso: lo que falta es aviso", out)
                    else:
                        self.assertIn("sin empezar", out)

    def test_por_que_de_una_dt_lo_exige_el_comprobador_y_la_cita_la_revision(self):
        """L8b del ensayo Informes: el comprobador exige un «Por qué»; la cita de lo que afirma de Appian (BP o URL, también
        en «Verificado») la pide la plantilla y la mira la revisión, no una lista de palabras (que marcaba «el cliente no
        permite…» y dejaba pasar «queryRecordType requiere pagingInfo»)."""
        self.copia()
        dt = lambda n, porque, verificado="pendiente": (
            f"**DT-0{n} — Decisión ficticia {n}**\n\n| Campo | Contenido |\n|---|---|\n| **Capa** | Datos |\n"
            f"| **Necesidad** | Base |\n| **Decisión** | Algo |\n| **Por qué** | {porque} |\n"
            f"| **Verificado** | {verificado} |\n\n")
        (self.p / "analisis/tecnico.md").write_text(
            "# Técnico ficticio\n\nVersión: 1.1 · Estado: completo\n\n## 2. Decisiones técnicas\n\n"
            + dt(1, "El funcional fija el texto del cuerpo, no el asunto")
            + dt(2, "Appian no admite campos agregados sobre esta relación")
            + dt(3, "Appian no admite campos agregados sobre esta relación",
                 "https://docs.appian.com/suite/help/latest/custom-record-fields.html")
            + dt(4, "—") + "## 3. Modelo de datos\n", encoding="utf-8")
        m = mo.Proyecto(self.p)
        with unittest.mock.patch.object(comprobar, "errores", 0):
            out = self.captura(comprobar.comprobar_tecnico, m, un.Contexto(m))
        linea = next(l for l in out.splitlines() if "decisiones técnicas con «Por qué»" in l)
        self.assertIn("DT-04", linea)
        for otra in ("DT-01", "DT-02", "DT-03"):
            self.assertNotIn(otra, linea)

    def test_confiar_no_pisa_lo_que_guarda_otra_sesion(self):
        """Revisión de Codex (L7): si otra sesión de Claude Code guarda su configuración entre la lectura y la sustitución,
        se vuelve a leer, y no se pierde lo suyo."""
        cfg_dir = self.root / "config"
        cfg_dir.mkdir()
        cfg = cfg_dir / ".claude.json"
        cfg.write_text(json.dumps({"numStartups": 2, "projects": {"otro": {"hasTrustDialogAccepted": True}}}),
                       encoding="utf-8")
        raiz = self.root / "proyecto nuevo"
        raiz.mkdir()
        real, llamadas = proyecto.lee_config, []

        def con_otra_sesion(c):
            llamadas.append(c)
            if len(llamadas) == 2:      # justo antes de sustituir, otra sesión guarda la suya
                c.write_text(json.dumps({"numStartups": 3, "projects": {"otro": {"hasTrustDialogAccepted": True},
                                                                         "paralelo": {"hasTrustDialogAccepted": True}}}),
                             encoding="utf-8")
            return real(c)
        with unittest.mock.patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": str(cfg_dir)}), \
                unittest.mock.patch.object(proyecto, "lee_config", con_otra_sesion):
            out = self.captura(proyecto.confiar, raiz)
        datos = json.loads(cfg.read_text(encoding="utf-8"))
        self.assertEqual(datos["numStartups"], 3)
        self.assertIn("paralelo", datos["projects"])
        self.assertIs(datos["projects"][raiz.resolve().as_posix()]["hasTrustDialogAccepted"], True)
        self.assertIn("De confianza para Claude Code", out)
        self.assertEqual(list(cfg_dir.iterdir()), [cfg])          # sin provisionales

    def test_anexo_preserva_notas_y_consulta(self):
        self.copia()
        f = self.p / "analisis" / "funcional.md"
        original = f.read_text(encoding="utf-8")
        for manual in ("\nNota manual pendiente\n", "\n### Preguntas\nPC nueva\n",
                       "\n| PAN-01 Listado · Botón | no borrar esta nota | ✔ |\n"):
            f.write_text(original + manual, encoding="utf-8")
            antes = f.read_bytes()
            with self.assertRaises(SystemExit):
                indice.c_derivadas(mo.Proyecto(self.p), SimpleNamespace(escribir=True))
            self.assertEqual(f.read_bytes(), antes)
            self.captura(indice.c_derivadas, mo.Proyecto(self.p), SimpleNamespace(escribir=False))
        f.write_text(original + "\n## Otro apartado\nNo perder\n", encoding="utf-8")
        self.captura(indice.c_derivadas, mo.Proyecto(self.p), SimpleNamespace(escribir=True))
        self.assertIn("No perder", f.read_text(encoding="utf-8"))
        f.write_text(original.replace(indice.TITULO_ANEXO, "## Anexo. Otra cosa"), encoding="utf-8")
        with self.assertRaises(SystemExit):
            indice.c_derivadas(mo.Proyecto(self.p), SimpleNamespace(escribir=True))

    def test_crlf_e_ids(self):
        f = self.root / "crlf.md"
        f.write_bytes(b"primera\r\nsegunda\r\n")
        mo.escribe(f, "primera\ntercera\n")
        self.assertEqual(f.read_bytes(), b"primera\r\ntercera\r\n")
        self.assertEqual(mo.ancho_ids(["HU-054", "D-01"], "HU"), 3)
        self.assertEqual(mo.ancho_ids(["HU-054", "D-01"], "D"), 2)
        self.copia()
        f = self.p / "analisis" / "funcional.md"
        f.write_text(f.read_text(encoding="utf-8").replace("HU-01", "HU-001"), encoding="utf-8")
        out = self.captura(indice.c_siguientes, mo.Proyecto(self.p), SimpleNamespace())
        self.assertIn("HU-012", out)

    def test_colision_desconocida_no_recomienda_desarrollo(self):
        fixture.con_unidades(self.p)
        dep = self.p / "as-is" / "datos" / "dependencias.json"
        if dep.exists():
            dep.unlink()
        m = mo.Proyecto(self.p)
        ctx = un.Contexto(m)
        self.assertFalse(ctx.colision("URG-01")["dependenciasDisponibles"])
        # Sin choques conocidos: dependencia ausente no equivale a ausencia de colisión.
        with unittest.mock.patch.object(un.Contexto, "colision", return_value={
                "corregidos": ["X"], "usan": [], "choques": [], "deriva": "sin fichero",
                "dependenciasDisponibles": False}):
            out = self.captura(indice.c_colision, m, SimpleNamespace(unidad="URG-01"))
        self.assertIn("desconocida", out)
        self.assertNotIn("Dónde se corrige: Desarrollo", out)

    def test_resumen_impacto_incluye_plan_de_construccion(self):
        fixture.con_unidades(self.p)
        m = mo.Proyecto(self.p)
        # HU-01 es independiente; HU-02 comparte EV-02. Ambas están construidas.
        for pieza in ("HU-01", "HU-02"):
            with self.subTest(pieza=pieza):
                out = self.captura(indice.c_impacto, m,
                                   SimpleNamespace(con=None, ids=[pieza], nivel=1, cambio="EV-03"))
                self.assertIn("→ Técnico §13:", out)
                resumen = next(l for l in out.splitlines() if l.startswith("Especificación técnica afectada:"))
                self.assertIn("técnico §13", resumen)

    def test_resumen_impacto_sin_plan_construido(self):
        m = self.copia()
        out = self.captura(indice.c_impacto, m,
                           SimpleNamespace(con=None, ids=["PAN-01"], nivel=1, cambio=None))
        self.assertNotIn("→ Técnico §13:", out)
        resumen = next((l for l in out.splitlines() if l.startswith("Especificación técnica afectada:")), "")
        self.assertNotIn("técnico §13", resumen)

    def test_tabla_ausente_diagnostico(self):
        m, _ = self.preparada()
        f = self.p / "analisis" / "tecnico.md"
        t = f.read_text(encoding="utf-8")
        f.write_text(re.sub(r"## 13\..*?(?=## 14\.)", "## 13. Plan\n1. Crear objetos\n\n", t, flags=re.S), encoding="utf-8")
        m = mo.Proyecto(self.p)
        with self.assertRaisesRegex(iss.NoSePuede, "no tiene tabla"):
            iss.calcula(m, un.Contexto(m), "EV-01")
        out = self.captura(comprobar.comprobar_unidades, m, un.Contexto(m))
        self.assertIn("EV-01", out)

    def test_campos_extra_nuevos_y_diferencias_reales(self):
        m, plan = self.preparada()
        i = plan.issues[0]
        f = fixture.verifica(self.p, "EV-01", i.id, **{i.objetos[0]: {"sobranCampos": ["auditoria"]}})
        self.assertTrue(iss.estado(self.p, "EV-01", i)[0])
        v = json.loads(f.read_text(encoding="utf-8"))
        v["objetos"][0]["diferencias"]["faltanCampos"] = ["solicitud"]
        f.write_text(json.dumps(v), encoding="utf-8")
        self.assertFalse(iss.estado(self.p, "EV-01", i)[0])

    def test_aplicacion_parentesis_legitimos(self):
        m = self.copia()
        f = self.p / "analisis" / "tecnico.md"
        fixture.editar(f, "| Versión de Appian |", "| Aplicación | Gestión (Europa) | Equipo |\n| Prefijo | AUT | Equipo |\n| Versión de Appian |")
        self.assertEqual(iss.aplicacion(mo.Proyecto(self.p)), "Gestión (Europa)")

    def test_numero_issue_no_reutiliza_maximo_eliminado(self):
        m, plan = self.preparada()
        maximo = max(iss.numero(i.id) for i in plan.issues)
        plan.issues = plan.issues[:-1]
        iss.escribe(plan, self.p)
        m = mo.Proyecto(self.p)
        nuevo = iss.calcula(m, un.Contexto(m), "EV-01")
        self.assertGreater(max(iss.numero(i.id) for i in nuevo.issues), maximo)

    def test_exigidas_ausentes_con_excepcion_humana(self):
        m, plan = self.preparada()
        i = next(x for x in plan.issues if x.esperado["_issue"].get("casosExigidos"))
        fixture.verifica(self.p, "EV-01", i.id, pruebas={"ejecutadas": True, "objetos": [{"objeto": o, "de": "issue", "casos": 0} for o in i.esperado["_issue"]["casosExigidos"]]})
        self.assertIn("faltan casos exigidos", iss.estado(self.p, "EV-01", i)[1])
        objeto = i.esperado["_issue"]["casosExigidos"][0]
        _, _, plan, i, _ = iss.sin_prueba(self.p, "EV-01", i.id,
                                        objeto + " «casos exigidos ausentes»", "Validación manual acordada")
        self.assertTrue(iss.estado(self.p, "EV-01", i, plan.marcas)[0])
        self.assertEqual(len(plan.marcas), 1)
        fixture.verifica(self.p, "EV-01", i.id, pruebas=fixture.pruebas_de((objeto, "issue", [], [])))
        self.assertFalse(iss.sigue_marcada(self.p, plan, plan.marcas[0]))
        c, out = fixture.corre(fixture.S / "indice.py", "issues", self.p, "EV-01", i.id,
                               "--sin-prueba", "casos exigidos ausentes", "--motivo", "x", "--desatendida")
        self.assertNotEqual(c, 0, out)

    def test_migra_indice_legacy_sin_reutilizar_el_mayor(self):
        m, plan = self.preparada()
        mayor = max(plan.issues, key=lambda i: iss.numero(i.id))
        indice_path = self.p / "construccion" / "EV-01" / "indice.md"
        t = indice_path.read_text(encoding="utf-8")
        indice_path.write_text(re.sub(r"<!-- ultimo-numero-issue: \d+ -->\n", "", t), encoding="utf-8")
        tecnico = self.p / "analisis" / "tecnico.md"
        original = tecnico.read_text(encoding="utf-8")
        objeto = mayor.objetos[0]
        tecnico.write_text("\n".join(l for l in original.split("\n")
                                    if not (l.startswith("| 7 |") and f"`{objeto}`" in l)), encoding="utf-8")
        m = mo.Proyecto(self.p)
        nuevo, _, _ = iss.genera(m, un.Contexto(m), "EV-01")
        self.assertNotIn(mayor.id, [i.id for i in nuevo.issues])
        self.assertGreaterEqual(nuevo.ultimo_numero, iss.numero(mayor.id))
        tecnico.write_text(original, encoding="utf-8")
        m = mo.Proyecto(self.p)
        nuevo = iss.calcula(m, un.Contexto(m), "EV-01")
        self.assertGreater(max(iss.numero(i.id) for i in nuevo.issues), iss.numero(mayor.id))

    def test_ausencia_casos_no_se_infiere_de_error_o_transporte(self):
        i = iss.Issue([], objetos=["R"], esperado={"_issue": {"casosExigidos": ["R"]}})
        for pruebas in ({"ejecutadas": False}, {"ejecutadas": True, "objetos": [
                {"objeto": "R", "casos": 0, "error": "HTTP 401"}]}, {"ejecutadas": True, "objetos": []}):
            self.assertEqual(iss.casos_ausentes({"pruebas": pruebas}, i), [])
        self.assertEqual(len(iss.casos_ausentes({"pruebas": {"ejecutadas": True, "objetos": [
            {"objeto": "R", "casos": 0}]}}, i)), 1)

    def test_reserva_avisa_version_cambiada_y_dependencia(self):
        m, plan = self.preparada()
        c, out = fixture.corre(fixture.S / "proyecto.py", "iniciar", self.p)
        self.assertEqual(c, 0, out)
        _, _, plan, i, _ = iss.siguiente(self.p, "EV-01", "Ana")
        self.assertIn("versión", plan.reservas[i.id])
        dependiente = next(x for x in plan.issues if x.depende)
        self.assertIn("ESPERA a", iss.para_construir(m, un.Contexto(m), plan, dependiente))
        f = self.p / "analisis" / "tecnico.md"
        fixture.editar(f, "## 14.", "### Reglas para quien construye\nConservar auditoría.\n\n## 14.")
        m = mo.Proyecto(self.p)
        nuevo, _, _ = iss.genera(m, un.Contexto(m), "EV-01")
        self.assertTrue(any(i.id in a and "Ana" in a for a in nuevo.avisos))
        _, _, _, misma, aviso = iss.siguiente(self.p, "EV-01", "Ana")
        self.assertEqual(misma.id, i.id)
        self.assertIn("ha cambiado desde tu reserva", aviso)
        _, _, _, _, aviso = iss.siguiente(self.p, "EV-01", "Ana")
        self.assertNotIn("ha cambiado desde tu reserva", aviso)

    def test_supuestos_reglas_y_impacto(self):
        m, plan = self.preparada()
        i = next(x for x in plan.issues if "AUT_GenerarNumero" in x.objetos)
        f = self.p / "analisis" / "tecnico.md"
        fixture.editar(f, "## 14.", "### Supuestos para construir\n\n| Pregunta | Se construye con | Dónde cambia |\n|---|---|---|\n| PC-01 | 30 días | `AUT_GenerarNumero` |\n| PC-02 | Otro supuesto | `NoEsObjeto` |\n\n### Reglas para quien construye\nNo duplicar registros.\n\n## 14.")
        m = mo.Proyecto(self.p)
        salida = "\n".join(iss.supuestos_y_reglas(m, i, []))
        self.assertIn("30 días", salida)
        self.assertNotIn("Otro supuesto", salida)
        self.assertIn("No duplicar registros", salida)
        fixture.editar(f, "### Reglas para quien construye\nNo duplicar registros.",
                       "Reglas para quien construye: No duplicar registros.\nConservar el identificador.\n\n"
                       "| Pregunta | Se construye con | Dónde cambia |\n|---|---|---|\n"
                       "| PC-02 | Supuesto ajeno después | `NoEsObjeto` |")
        m = mo.Proyecto(self.p)
        salida = "\n".join(iss.supuestos_y_reglas(m, i, []))
        self.assertIn("No duplicar registros", salida)
        self.assertIn("Conservar el identificador", salida)
        self.assertNotIn("Supuesto ajeno después", salida)
        fixture.editar(f, "| PC-01 | 30 días |", "| PC-03 | 30 días |")
        m = mo.Proyecto(self.p)
        avisos = self.captura(comprobar.comprobar_unidades, m, un.Contexto(m))
        self.assertIn("PC-03", avisos)
        out = self.captura(indice.c_impacto, m, SimpleNamespace(con=["30 días"], ids=["HU-01"], nivel=1, cambio=None))
        self.assertRegex(out, r"l\.\d+.*30 días")

    def test_manual_informa_pendientes_y_aprobacion_procesada(self):
        m, plan = self.preparada()
        pm = self.p / "proyecto.md"
        texto = pm.read_text(encoding="utf-8")
        pm.write_text(texto.split("## Siguiente paso")[0] + "## Siguiente paso\n\nConstruir EV-01.\n", encoding="utf-8")
        c, out = fixture.corre(fixture.S / "proyecto.py", "cambio", self.p, "EV-01", "construida", "--manual")
        self.assertEqual(c, 0, out)
        self.assertIn("pendiente de verificación", out)
        self.assertIn(plan.issues[0].id, out)
        # L15 del ensayo Informes: proyecto.md dice en qué punto está cada unidad; el siguiente paso sigue siendo suyo
        cabecera = (self.p / "proyecto.md").read_text(encoding="utf-8").split("## ")[0]
        self.assertIn("Unidades: EV-01 construida", cabecera)
        self.assertIn("El «Siguiente paso» es tuyo: aún habla de EV-01", out)
        self.assertIn("Construir EV-01.", pm.read_text(encoding="utf-8"))   # el texto del analista no lo cambia el script
        out = self.captura(proyecto.estado, SimpleNamespace(carpeta=str(self.p)))
        linea = next(l for l in out.splitlines() if l.startswith("Fuentes:"))
        self.assertNotIn("FU-05", linea.split("sin procesar:")[-1] if "sin procesar:" in linea else "")

    def test_quien_vacio_recupera_identidad(self):
        with unittest.mock.patch.object(mo, "git", return_value="  Persona de git  "):
            self.assertEqual(iss.quien_soy(self.root, "   "), "Persona de git")
        with unittest.mock.patch.object(mo, "git", return_value=" \t "), \
                unittest.mock.patch.dict(os.environ, {"USERNAME": "  ", "USER": " \t "}):
            self.assertEqual(iss.quien_soy(self.root, "   "), "alguien")

    def test_manual_issue_humana_sin_fingir_verificacion(self):
        m, plan = self.preparada()
        i = plan.issues[0]
        for args in (("--manual",), ("--manual", "--motivo", "Revisión Designer", "--desatendida")):
            code, out = fixture.corre(fixture.S / "indice.py", "issues", self.p, "EV-01", i.id, *args)
            self.assertNotEqual(code, 0, out)
        code, out = fixture.corre(fixture.S / "indice.py", "issues", self.p, "EV-01", i.id,
                                  "--manual", "--motivo", "Revisión Designer", "--quien", "Ana")
        self.assertEqual(code, 0, out)
        self.assertIn("hecha manualmente por Ana", out)
        self.assertFalse((self.p / "construccion" / "EV-01" / "verificacion" / (i.id + ".json")).exists())
        m = mo.Proyecto(self.p)
        plan = iss.calcula(m, un.Contexto(m), "EV-01")
        siguiente = iss.elige(plan, self.p)
        self.assertIsNotNone(siguiente)
        self.assertNotEqual(siguiente.id, i.id)
        code, out = fixture.corre(fixture.S / "indice.py", "issues", self.p, "EV-01", i.id, "--automatico")
        self.assertEqual(code, 0, out)
        self.assertFalse(iss.estado(self.p, "EV-01", i)[0])

    def test_manual_caduca_y_no_tapa_fallos_actuales(self):
        m, plan = self.preparada()
        i = next(x for x in plan.issues if x.esperado["_issue"].get("casosExigidos"))
        objeto = i.esperado["_issue"]["casosExigidos"][0]
        iss.cierre_manual(self.p, "EV-01", i.id, "Comparación manual revisada", "Ana")
        f = fixture.verifica(self.p, "EV-01", i.id, pruebas=fixture.pruebas_de((objeto, "issue", ["caso"], [])),
                             **{objeto: {"falta": True}})
        self.assertFalse(iss.estado(self.p, "EV-01", i)[0])
        _, _, p2, i, _ = iss.sin_prueba(self.p, "EV-01", i.id, objeto + " «caso»", "Acordado")
        self.assertTrue(iss.estado(self.p, "EV-01", i, p2.marcas)[0])
        qa = self.p / "qa" / "EV-01" / "resultado.json"
        qa.parent.mkdir(parents=True)
        escenario = i.criterios[0]
        error = {"escenarios": {escenario: {"resultado": "falla", "paso": "entonces 1", "motivo": "Error",
                                            "versionIssue": i.version}}}
        qa.write_text(json.dumps(error), encoding="utf-8")
        self.assertFalse(iss.estado(self.p, "EV-01", i, p2.marcas)[0])
        _, _, p2, i, _ = iss.sin_prueba(self.p, "EV-01", i.id, escenario, "Excepción humana QA")
        self.assertTrue(iss.estado(self.p, "EV-01", i, p2.marcas)[0])
        # Una verificación y un QA que declaran otra versión no aportan fallos de esta versión.
        v = json.loads(f.read_text(encoding="utf-8")); v["issue"]["version"] = "anterior"
        f.write_text(json.dumps(v), encoding="utf-8")
        error["escenarios"][escenario]["versionIssue"] = "anterior"
        qa.write_text(json.dumps(error), encoding="utf-8")
        self.assertTrue(iss.estado(self.p, "EV-01", i)[0])
        fixture.editar(self.p / "analisis" / "tecnico.md", "## 14.",
                       "Reglas para quien construye: Cambia lo requerido.\n\n## 14.")
        m = mo.Proyecto(self.p)
        nuevo, _, _ = iss.genera(m, un.Contexto(m), "EV-01")
        actual = next(x for x in nuevo.issues if x.id == i.id)
        self.assertNotEqual(actual.version, i.version)
        self.assertFalse(iss.estado(self.p, "EV-01", actual)[0])
        self.assertEqual(nuevo.manuales, [])

    def test_unidad_con_issues_manuales_no_afirma_verificacion(self):
        m, plan = self.preparada()
        for i in plan.issues:
            iss.cierre_manual(self.p, "EV-01", i.id, "Revisión humana", "Ana")
        code, out = fixture.corre(fixture.S / "proyecto.py", "cambio", self.p, "EV-01", "construida")
        self.assertEqual(code, 0, out)
        self.assertIn("con cierres manuales", out)
        self.assertNotIn("· verificada", fixture.fila_de(self.p, "EV-01"))

    def test_avisos_gherkin_y_con_que(self):
        self.copia()
        c, out = fixture.corre(fixture.S / "comprobar.py", self.p)
        self.assertEqual(c, 0, out)
        self.assertIn("· criterios con dado", out)
        self.assertIn("· técnico §14: cada criterio con «Con qué»", out)

    def test_inicial_no_incrementa_ni_duplica(self):
        c, out = fixture.corre(fixture.S / "proyecto.py", "iniciar", self.p, "--nombre", "Inicial")
        self.assertEqual(c, 0, out)
        for nombre in ("funcional", "tecnico"):
            f = self.p / "analisis" / (nombre + ".md")
            t = f.read_text(encoding="utf-8")
            f.write_text(re.sub(r"Versión:.*", "Versión: 1.0", t), encoding="utf-8")
        (self.p / "fuentes" / "indice.json").write_text(json.dumps({"fuentes": [{"id": "FU-01", "fecha": "2026-10-01", "tipo": "Reunión"}]}), encoding="utf-8")
        dec = self.p / "analisis" / "decisiones.md"
        t = dec.read_text(encoding="utf-8")
        t = re.sub(r"(?m)^\|\s*0\.1\s*\|[^\n]*$", "| 1.0 | 2026-09-01 | Decisión original | FU-01 | Aceptada |", t)
        t += "\n## Tabla ajena\n| Clave | Texto |\n|---|---|\n| 1.0 | Conservar |\n"
        dec.write_text(t, encoding="utf-8")
        c, out = fixture.corre(fixture.S / "proyecto.py", "version", self.p, "--inicial", "--fuente", "FU-01", "--que", "Análisis inicial")
        self.assertEqual(c, 0, out)
        self.assertEqual(mo.Proyecto(self.p).version("F"), (1, 0))
        self.assertEqual(list((self.p / "versiones").iterdir()), [])
        self.assertIn("FU-01", (self.p / "proyecto.md").read_text(encoding="utf-8"))
        t = dec.read_text(encoding="utf-8")
        self.assertEqual(len(re.findall(r"(?m)^\| 1\.0 \|", t)), 2)
        self.assertIn("| 1.0 | Conservar |", t)
        self.assertIn("| 1.0 | 2026-09-01 | Decisión original | FU-01 | Aceptada |", t)
        self.assertEqual(json.loads((self.p / ".appian-plugin.json").read_text(encoding="utf-8"))["ruta"], str(fixture.PLUGIN))
        c, out = fixture.git(self.p, "check-ignore", ".appian-plugin.json")
        self.assertEqual(c, 0, out)


if __name__ == "__main__":
    import unittest.mock
    unittest.main()
