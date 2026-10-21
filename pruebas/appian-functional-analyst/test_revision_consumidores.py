"""Destinos URG sin elegir y textos de fuentes vigentes. Proyectos ficticios, sin red."""
import contextlib
import datetime
import importlib.util
import io
import json
import os
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
import leer_fuentes as lf


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
    ("Desarrollo (después se reaplica en el entorno de corrección)", "desarrollo"),
    ("Entorno de corrección (después se reaplica en desarrollo)", "correccion"),
    ("Desarrollo, después se reaplica en el entorno de corrección", "desarrollo"),
    ("Desarrollo.", "desarrollo"),
    ("Desarrollo — se reaplica después", "desarrollo"),
    ("Desarrollo - se reaplica después", "desarrollo"),
    ("En desarrollo", "desarrollo"),
    ("En el entorno de corrección", "correccion"),
    ("Corrección", "correccion"),
    ("Desarrollo; no se ha decidido", ""),
    ("Desarrollo: no elegido", ""),
    ("Desarrollo — o Entorno de corrección", ""),
    ("Desarrollo - Entorno de corrección", ""),
    ("En desarrollo o en el entorno de corrección", ""),
    ("Corrección o Desarrollo", ""),
    ("No Corrección", ""),
    ("Desarrollo —", ""),
    ("Desarrollo (servidor de ensayo)", "desarrollo"),
    ("Desarrollo (aún no decidido)", ""),
    ("Desarrollo: pendiente", ""),
    ("Desarrollo — o Corrección", ""),
    ("Desarrollo (el entorno de corrección se mantiene sin cambios)", "desarrollo"),
    ("Desarrollo (el entorno de corrección no está disponible)", "desarrollo"),
    ("Desarrollo (o Entorno de corrección)", ""),
    ("Entorno de corrección (o Desarrollo)", ""),
    ("**Desarrollo** (o Entorno de corrección)", ""),
    ("Entorno de corrección o Desarrollo", ""),
    ("Entorno de corrección · Desarrollo", ""),
    ("No Desarrollo", ""),
    ("No Entorno de corrección; Desarrollo", ""),
    ("Pendiente (Desarrollo o Entorno de corrección)", ""),
    ("Se decidirá entre Desarrollo y Entorno de corrección", ""),
    ("Desarrollo sin elegir todavía", ""),
    ("Producción", ""),
    ("", ""),
)


class FechasFuentes(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="fechas-fuentes-")
        self.addCleanup(self.tmp.cleanup)
        self.raiz = Path(self.tmp.name)
        self.entrada = self.raiz / "entrada"
        self.entrada.mkdir()
        self.fuentes = self.raiz / "fuentes"
        self.turnos = "".join(f"[00:0{i}:00] Persona {i % 2}:\nFrase ficticia {i}.\n" for i in range(6))

    def original(self, nombre, texto):
        f = self.entrada / nombre
        f.write_text(texto, encoding="utf-8")
        ts = datetime.datetime(2026, 10, 20, 12).timestamp()
        os.utime(f, (ts, ts))
        return f

    def ingerir(self, *args):
        code, out = fixture.corre(fixture.S / "leer_fuentes.py", *args, "-o", self.fuentes)
        self.assertEqual(code, 0, out)
        return json.loads((self.fuentes / "indice.json").read_text(encoding="utf-8"))["fuentes"]

    def test_cabecera_transcripcion_valida_precede_nombre_y_mtime(self):
        for i, (fecha, cuerpo) in enumerate((("2026-08-04", self.turnos),
                                           ("24/7/2026", self.turnos),
                                           ("2026-07-29", "[00:01:00]\nTexto ficticio.\n" * 5),
                                           ("4/8/2026", "Sin marcas, transcripción parcial.\n"))):
            with self.subTest(fecha=fecha):
                f = self.original(f"sesion-{i}-2026-10-01.md", "# Sesión ficticia\n\n"
                                  f"Tipo de fuente: transcripción parcial\nFecha: {fecha}\nOrigen: ficticio\n\n{cuerpo}")
                body, kind, _, date = lf.convert(f, self.fuentes, "FU-01")
                self.assertEqual(kind, "Transcripción")
                self.assertEqual(date, "2026-07-24" if i == 1 else "2026-07-29" if i == 2 else "2026-08-04")
                self.assertEqual(body, f.read_text(encoding="utf-8"))

    def test_cabecera_sin_tipo_con_cinco_marcas(self):
        for cuerpo in (self.turnos, "[00:01:00]\nTexto ficticio.\n" * 5):
            with self.subTest(con_hablantes="Persona" in cuerpo):
                f = self.original("sesion.txt", "Fecha: 2026-07-29\n\n" + cuerpo)
                _, kind, _, date = lf.convert(f, self.fuentes, "FU-01")
                self.assertEqual((kind, date), ("Transcripción", "2026-07-29"))

    def test_fecha_interna_invalida_o_ausente_conserva_nombre_o_mtime(self):
        casos = (
            "Tipo de fuente: transcripción parcial\n\n" + self.turnos + "Fecha: 2026-07-24\n",
            "Tipo de fuente: transcripción parcial\n\n## Documento citado\nFecha: 2026-07-24\n" + self.turnos,
            "Tipo de fuente: transcripción parcial\nFecha: 2026-02-31\n\n" + self.turnos,
            "Tipo de fuente: transcripción parcial\nFecha: 31/2/2026\n\n" + self.turnos,
            "Tipo de fuente: transcripción parcial\nFecha: 24-07-2026\n\n" + self.turnos,
            self.turnos,
        )
        for i, texto in enumerate(casos):
            for nombre, esperado in ((f"sesion-{i}.md", "2026-10-20"),
                                      (f"sesion-{i}-20260729.md", "2026-07-29")):
                with self.subTest(caso=i, nombre=nombre):
                    f = self.original(nombre, texto)
                    self.assertEqual(lf.convert(f, self.fuentes, "FU-01")[3], esperado)

    def test_no_promueve_fecha_del_cuerpo_de_un_convertido(self):
        texto = ("# FU-01 · sesion.txt\n\n- Tipo: Transcripción\n- Fecha: 2026-10-01\n\n---\n\n"
                 "Tipo de fuente: transcripción parcial\nFecha: 2026-07-24\n\n" + self.turnos)
        f = self.original("convertido.md", texto)
        self.assertEqual(lf.convert(f, self.fuentes, "FU-01")[3], "2026-10-20")

    def test_chat_aprobacion_y_texto_conservan_su_contrato(self):
        for tipo, fecha, esperado in (("chat", "2026-07-24", "2026-07-24"),
                                      ("aprobación", "4/8/2026", "2026-08-04"),
                                      ("documento", "2026-07-24", "2026-10-01")):
            with self.subTest(tipo=tipo):
                f = self.original("fuente-2026-10-01.txt", f"Tipo de fuente: {tipo}\nDe: Responsable ficticio\n"
                                  f"Fecha: {fecha}\n\nTexto ficticio.\n")
                _, kind, _, date = lf.convert(f, self.fuentes, "FU-01")
                self.assertEqual(date, esperado)
                self.assertEqual(kind, {"chat": "Chat", "aprobación": "Aprobación", "documento": "Texto"}[tipo])

    def test_mismo_catalogo_corrige_solo_fecha_y_preserva_duplicada_original_y_copia(self):
        f = self.original("sesion.md", "# Sesión ficticia\n\nTipo de fuente: transcripción parcial\n"
                          "Fecha: 24/7/2026\n\n" + self.turnos + "\n- Fecha: cita interna intacta\n")
        otro = self.original("otra.md", "Otra fuente ficticia.\n")
        filas = self.ingerir(f, otro)
        filas = self.ingerir("--duplicada", "FU-01=FU-02", "--motivo", "Copia revisada ficticia")
        indice = self.fuentes / "indice.json"
        filas[0]["fecha"] = "2026-10-20"
        indice.write_text(json.dumps({"fuentes": filas}, ensure_ascii=False), encoding="utf-8")
        derivado = self.fuentes / filas[0]["salida"]
        raw = derivado.read_bytes().replace(b"- Fecha: 2026-07-24", b"- Fecha: 2026-10-20", 1).replace(b"\n", b"\r\n")
        derivado.write_bytes(raw)
        original = f.read_bytes()
        reparadas = self.ingerir(f)
        esperado = {**filas[0], "fecha": "2026-07-24"}
        self.assertEqual(reparadas, [esperado, filas[1]])
        self.assertEqual(derivado.read_bytes(), raw.replace(b"- Fecha: 2026-10-20", b"- Fecha: 2026-07-24", 1))
        self.assertEqual(f.read_bytes(), original)
        snapshot = {p.name: p.read_bytes() for p in self.fuentes.iterdir() if p.is_file()}
        tiempos = {p.name: p.stat().st_mtime_ns for p in self.fuentes.glob("FU-*.md")}
        self.assertEqual(self.ingerir(f), reparadas)
        self.assertEqual({p.name: p.read_bytes() for p in self.fuentes.iterdir() if p.is_file()}, snapshot)
        self.assertEqual({p.name: p.stat().st_mtime_ns for p in self.fuentes.glob("FU-*.md")}, tiempos)
        copia = self.entrada / "copia-renombrada.md"
        shutil.copyfile(f, copia)
        self.assertEqual(self.ingerir(copia), reparadas)
        self.assertEqual({p.name: p.read_bytes() for p in self.fuentes.iterdir() if p.is_file()}, snapshot)
        self.assertEqual(copia.read_bytes(), original)

    def test_copia_renombrada_repara_fecha_sin_reconvertir_ni_cambiar_identidad(self):
        for salida in ("presente", "ausente", "vacia"):
            with self.subTest(salida=salida):
                self.fuentes = self.raiz / salida
                f = self.original("sesion.md", "Tipo de fuente: transcripción\nFecha: 24/7/2026\n\n" + self.turnos)
                otro = self.original("otra.md", "Resumen ficticio independiente.\n")
                filas = self.ingerir(f, otro)
                filas = self.ingerir("--duplicada", "FU-01=FU-02", "--motivo", "Resumen revisado")
                filas[0]["fecha"] = "2026-10-20"
                derivado = self.fuentes / filas[0]["salida"]
                raw = derivado.read_bytes().replace(b"- Fecha: 2026-07-24", b"- Fecha: 2026-10-20", 1)
                if salida == "ausente":
                    filas[0]["salida"] = "FU-01-no-existe.md"
                    derivado = self.fuentes / filas[0]["salida"]
                elif salida == "vacia":
                    raw = b""
                if salida != "ausente":
                    derivado.write_bytes(raw)
                (self.fuentes / "indice.json").write_text(json.dumps({"fuentes": filas}), encoding="utf-8")
                copia = self.entrada / "renombrada.md"
                original = f.read_bytes()
                copia.write_bytes(original)
                fecha = "2026-07-24" if salida == "presente" else "2026-10-20"
                esperadas = [{**filas[0], "fecha": fecha, **({"palabras": 0} if salida == "vacia" else {})}, filas[1]]
                self.assertEqual(self.ingerir(copia), esperadas)
                self.assertEqual(self.ingerir(copia), esperadas)
                if salida == "ausente":
                    self.assertFalse(derivado.exists())
                else:
                    esperado = raw.replace(b"- Fecha: 2026-10-20", b"- Fecha: 2026-07-24", 1) if raw else raw
                    self.assertEqual(derivado.read_bytes(), esperado)
                self.assertEqual(f.read_bytes(), original)
                self.assertEqual(copia.read_bytes(), original)
                if salida == "presente":
                    copia.write_bytes(original + b"\nContenido nuevo ficticio.\n")
                    nuevas = self.ingerir(copia)
                    self.assertEqual(nuevas[:2], esperadas)
                    self.assertEqual((nuevas[2]["id"], nuevas[2]["fecha"]), ("FU-03", "2026-07-24"))
                    self.assertNotIn("duplicada_de", nuevas[2])
                    self.assertNotIn("motivo_duplicada", nuevas[2])

    def test_mismo_catalogo_sin_cabecera_no_recalcula_fallback(self):
        f = self.original("sesion.txt", self.turnos + "Fecha: 2026-07-24\n")
        filas = self.ingerir(f)
        derivado = self.fuentes / filas[0]["salida"]
        antes = derivado.read_bytes()
        ts = datetime.datetime(2026, 11, 1, 12).timestamp()
        os.utime(f, (ts, ts))
        self.assertEqual(self.ingerir(f), filas)
        self.assertEqual(derivado.read_bytes(), antes)


    def test_formatos_cabecera_en_alta_y_reparacion_conservan_duplicada_y_bytes(self):
        formatos = ("Participantes:\nFecha: 2026-10-01", "Tema:\nFecha: 2026-10-01", "Reunión de seguimiento\nFecha: 2026-10-01",
                    "---\nFecha: 2026-10-01\n---", "Fecha: 2026-10-01 10:00")
        for n, cabecera in enumerate(formatos):
            with self.subTest(cabecera=cabecera):
                self.fuentes = self.raiz / f"formato-{n}"
                f = self.original(f"sesion-{n}.txt", cabecera + "\nTipo de fuente: transcripción\n\n" + self.turnos)
                otro = self.original(f"resumen-{n}.txt", "Resumen ficticio independiente.\n")
                original = f.read_bytes()
                filas = self.ingerir(f, otro)
                self.assertEqual((filas[0]["tipo"], filas[0]["fecha"]), ("Transcripción", "2026-10-01"))
                filas = self.ingerir("--duplicada", "FU-01=FU-02", "--motivo", "Resumen revisado")
                filas[0]["fecha"] = "2026-10-20"
                (self.fuentes / "indice.json").write_text(json.dumps({"fuentes": filas}), encoding="utf-8")
                derivado = self.fuentes / filas[0]["salida"]
                antes = derivado.read_bytes().replace(b"- Fecha: 2026-10-01", b"- Fecha: 2026-10-20", 1)
                derivado.write_bytes(antes)
                nuevas = self.ingerir(f)
                self.assertEqual(nuevas[0], {**filas[0], "fecha": "2026-10-01"})
                self.assertEqual(derivado.read_bytes(), antes.replace(b"- Fecha: 2026-10-20", b"- Fecha: 2026-10-01", 1))
                self.assertEqual(f.read_bytes(), original)

    def test_cabecera_acotada_no_promueve_narrativa_ni_hora_invalida(self):
        invalidas = ("Fecha: 2026-02-30", "Fecha: 2026-10-01 24:00", "Fecha: 2026-10-01 10:60",
                     "Fecha: 2026-10-01 10:00:00", "Fecha: 2026-10-01 10:00Z",
                     "Fecha: 2026-10-01 fue acordada", "> Fecha: 2026-10-01",
                     "[00:00:01] Persona:\nFecha: 2026-10-01", "---\nFecha: 2026-10-01",
                     "---\nTema: reunión\n---\nFecha: 2026-10-01",
                     "Reunión inicial\nSesión posterior\nFecha: 2026-10-01",
                     "Una frase libre\n\nFecha: 2026-10-01", "```\nFecha: 2026-10-01\n```",
                     "~~~texto\nFecha: 2026-10-01\n~~~", "## Sección del cuerpo\nFecha: 2026-10-01",
                     "Tipo de fuente: transcripción\n\nFecha: 2026-10-01")
        for cabecera in invalidas:
            with self.subTest(cabecera=cabecera):
                self.assertIsNone(lf.fecha_transcripcion(cabecera + "\n\n" + self.turnos))
        for sangria in ("", " ", "  ", "   ", "    ", "\t", " \t", "  \t", "   \t"):
            for marca in ("> cita", "```texto", "[00:00:00] Persona:", "## Cuerpo"):
                with self.subTest(sangria=sangria, marca=marca):
                    self.assertIsNone(lf.fecha_transcripcion(sangria + marca + "\nFecha: 04/08/2026"))
        for sangria in ("    ", "\t", " \t", "  \t", "   \t"):
            with self.subTest(codigo=sangria):
                self.assertIsNone(lf.fecha_transcripcion(sangria + "Fecha: 04/08/2026"))
        for titulo in ("Transcripción", "Sesión de coordinación", "# Reunión ficticia"):
            with self.subTest(titulo=titulo):
                self.assertEqual(lf.fecha_transcripcion(titulo + "\nFecha: 1/10/2026 00:00\n\n" + self.turnos),
                                 "2026-10-01")

    def test_cabecera_estructural_sin_vocabulario_de_titulos_ni_claves(self):
        for cabecera in ("- Fecha: 04/08/2026", "* Fecha: 04/08/2026", "**Fecha:** 04/08/2026",
                         "**Fecha**: 04/08/2026", "+ __Fecha:__ 04/08/2026", "Comité de seguimiento\nFecha: 04/08/2026",
                         "  - **Fecha:** 04/08/2026", "   # Título\nFecha: 04/08/2026",
                         "Asistentes:\nFecha: 04/08/2026", "Clave desconocida:\nFecha: 04/08/2026",
                         "---\nClave desconocida:\nFecha: 04/08/2026\n---"):
            with self.subTest(cabecera=cabecera):
                self.assertEqual(lf.fecha_transcripcion(cabecera + "\n\n" + self.turnos), "2026-08-04")

        # Cambio de contrato deliberado: sin marcado, estas líneas son un título
        # o campos iniciales. No se promete distinguir su significado narrativo.
        for cabecera in ("Una frase libre\nFecha: 04/08/2026",
                         "En la reunión se acordó lo siguiente\nFecha: 04/08/2026",
                         "Texto citado de otra reunión:\nFecha: 04/08/2026",
                         "Tipo de fuente: transcripción parcial\nTexto citado de otra reunión:\nFecha: 04/08/2026"):
            with self.subTest(ambigua=cabecera):
                self.assertEqual(lf.fecha_transcripcion(cabecera + "\n\n" + self.turnos), "2026-08-04")

        self.assertIsNone(lf.fecha_transcripcion("x" * 2000 + "\nFecha: 04/08/2026"))
        for cabecera in ("Fecha: **04/08/2026**",
                         "# FU-01 · sesion.txt\n\n- Tipo: Transcripción\n- Fecha: 2026-10-01\n\n---\n\nFecha: 04/08/2026"):
            with self.subTest(limite=cabecera[:80]):
                self.assertIsNone(lf.fecha_transcripcion(cabecera))

    def test_cinco_cabeceras_en_cli_alta_y_reparacion_preservan_ids_cuerpo_y_duplicada(self):
        cabeceras = ("- Fecha: 04/08/2026", "* Fecha: 04/08/2026", "**Fecha:** 04/08/2026",
                     "Comité de seguimiento\nFecha: 04/08/2026", "Asistentes:\nFecha: 04/08/2026")
        for n, cabecera in enumerate(cabeceras):
            with self.subTest(cabecera=cabecera):
                self.fuentes = self.raiz / f"cli-cabecera-{n}"
                f = self.original(f"sesion-{n}-2026-10-01.txt", cabecera + "\n\n" + self.turnos)
                otro = self.original(f"resumen-{n}.txt", "Resumen ficticio independiente.\n")
                original = f.read_bytes()
                filas = self.ingerir(f, otro)
                alta = filas[0].copy()
                filas = self.ingerir("--duplicada", "FU-01=FU-02", "--motivo", "Resumen revisado")
                filas[0]["fecha"] = "2026-10-20"
                (self.fuentes / "indice.json").write_text(json.dumps({"fuentes": filas}), encoding="utf-8")
                derivado = self.fuentes / filas[0]["salida"]
                antes = derivado.read_bytes().replace(f"- Fecha: {alta['fecha']}".encode(), b"- Fecha: 2026-10-20", 1)
                derivado.write_bytes(antes)
                nuevas = self.ingerir(f)
                self.assertEqual(f.read_bytes(), original)
                self.assertEqual(nuevas[0]["duplicada_de"], "FU-02")
                with self.subTest(operacion="alta"):
                    self.assertEqual((alta["id"], alta["tipo"], alta["fecha"]), ("FU-01", "Transcripción", "2026-08-04"))
                with self.subTest(operacion="reparacion"):
                    self.assertEqual(nuevas, [{**filas[0], "fecha": "2026-08-04"}, filas[1]])
                    self.assertEqual(derivado.read_bytes(), antes.replace(b"- Fecha: 2026-10-20", b"- Fecha: 2026-08-04", 1))

    def test_regenerar_misma_fuente_conserva_seleccion_sin_heredarla_al_contenido_nuevo(self):
        for ausente in (True, False):
            for modificada in (False, True):
                with self.subTest(ausente=ausente, modificada=modificada):
                    self.fuentes = self.raiz / f"regenerar-{ausente}-{modificada}"
                    f = self.original(f"sesion-{ausente}-{modificada}.txt", "Fecha: 2026-10-01\n\n" + self.turnos)
                    otro = self.original(f"resumen-{ausente}-{modificada}.txt", "Resumen ficticio.\n")
                    self.ingerir(f, otro)
                    filas = self.ingerir("--duplicada", "FU-01=FU-02", "--motivo", "Resumen revisado")
                    if ausente:
                        filas[0]["salida"] = "registrada-pero-ausente.md"
                    else:
                        (self.fuentes / filas[0]["salida"]).write_bytes(b"")
                    (self.fuentes / "indice.json").write_text(json.dumps({"fuentes": filas}), encoding="utf-8")
                    if modificada:
                        f.write_bytes(f.read_bytes() + b"\nCambio nuevo que requiere revisar la cobertura.\n")
                    nuevas = self.ingerir(f)
                    if modificada:
                        self.assertEqual(len(nuevas), 3)
                        self.assertEqual(nuevas[0]["duplicada_de"], "FU-02")
                        self.assertEqual(nuevas[-1]["id"], "FU-03")
                        self.assertNotEqual(nuevas[0]["hash"], nuevas[-1]["hash"])
                        self.assertNotIn("duplicada_de", nuevas[-1])
                        self.assertNotIn("motivo_duplicada", nuevas[-1])
                    else:
                        self.assertEqual(len(nuevas), 2)
                        self.assertEqual(nuevas[0]["id"], "FU-01")
                        self.assertEqual(nuevas[0]["hash"], filas[0]["hash"])
                        self.assertEqual(nuevas[0]["duplicada_de"], "FU-02")
                        self.assertEqual(nuevas[0]["motivo_duplicada"], "Resumen revisado")
                        self.assertTrue((self.fuentes / nuevas[0]["salida"]).read_text(encoding="utf-8").strip())

    def test_regenerar_no_borra_selecciones_invalidas_para_eludir_validacion(self):
        for destino in ("inexistente", "cadena", "ciclo"):
            with self.subTest(destino=destino):
                self.fuentes = self.raiz / destino
                fuentes = [self.original(f"{destino}-{n}.txt", f"Fuente ficticia independiente {n}.\n") for n in range(3)]
                filas = self.ingerir(*fuentes)
                filas[0].update(duplicada_de="FU-99" if destino == "inexistente" else "FU-02", motivo_duplicada="Selección previa")
                if destino != "inexistente":
                    filas[1].update(duplicada_de="FU-01" if destino == "ciclo" else "FU-03", motivo_duplicada="Selección previa")
                (self.fuentes / filas[0]["salida"]).write_bytes(b"")
                (self.fuentes / "indice.json").write_text(json.dumps({"fuentes": filas}), encoding="utf-8")
                code, out = fixture.corre(fixture.S / "leer_fuentes.py", fuentes[0], "-o", self.fuentes)
                self.assertNotEqual(code, 0, out)
                self.assertIn("debe seguir activa", out)


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
        for n, valor in enumerate((DESTINOS[0][0], DESTINOS[3][0], DESTINOS[6][0],
                                  "No Desarrollo", "Desarrollo (o Entorno de corrección)",
                                  "Entorno de corrección (o Desarrollo)", "Desarrollo; no se ha decidido",
                                  "Desarrollo — o Entorno de corrección", "En desarrollo o en el entorno de corrección")):
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

    def test_cli_destinos_compatibles_con_aclaracion_conservan_ficha(self):
        for n, valor in enumerate(("Desarrollo.", "Desarrollo — se reaplica después", "En desarrollo",
                                  "En el entorno de corrección", "Corrección")):
            with self.subTest(valor=valor):
                p = fixture.con_unidades(self.raiz / str(n))
                f = p / "impacto/URG-01.md"
                f.write_text(f.read_text(encoding="utf-8").replace("| Dónde se corrige | Entorno de corrección |",
                             f"| Dónde se corrige | {valor} |"), encoding="utf-8")
                antes = f.read_bytes()
                code, out = fixture.corre(fixture.S / "proyecto.py", "cambio", p, "URG-01", "produccion",
                                          "--ref", "PASE-FICTICIO")
                self.assertEqual(code, 0, out)
                self.assertIn("En producción", fixture.fila_de(p, "URG-01"))
                self.assertEqual(f.read_bytes(), antes)

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
