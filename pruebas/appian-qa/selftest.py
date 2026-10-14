#!/usr/bin/env python3
"""Prueba automática de appian-qa: qa.py repite guiones contra un SAIL CLI simulado (sail_simulado.py, que contesta con
un --json como el de verdad) en un proyecto ficticio con espacios y tildes en la ruta.

  python3 pruebas/appian-qa/selftest.py

Prueba la skill de $PLUGIN_A_PROBAR/skills/appian-qa (por defecto, la de este repositorio): la sesión de cada cuenta se
encuentra por su usuario y su host; los guiones pasan y dos repeticiones dan lo mismo; un defecto los hace fallar, con
su paso y su motivo, y devuelve su issue a pendiente (issues.py del analista); una ref que cambia en cada carga, un
error en texto, un paso que no cambia nada, un «entonces» que mira la página de antes de enviar y un guion a medias
fallan; una sesión caducada no cambia el resultado anterior; un escenario que cambió deja su guion desfasado; un load
que aún no enseña lo nuevo se repite. Sale con 1 si algo falla.
"""
import importlib.util
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace

sys.dont_write_bytecode = True  # importa issues.py del analista: sin __pycache__ dentro del plugin

AQUI = pathlib.Path(__file__).resolve().parent
PLUGIN = pathlib.Path(os.environ.get("PLUGIN_A_PROBAR") or AQUI.parents[1]).resolve()
QA = PLUGIN / "skills" / "appian-qa" / "scripts" / "qa.py"
ISSUES = PLUGIN / "skills" / "appian-functional-analyst" / "scripts"
SIMULADO = AQUI / "sail_simulado.py"
HOST = "dev.ejemplo.test"
fallos = []

FEATURES = {
    "ISS-01.feature": """# language: es
Característica: HU-01 Registrar una solicitud

  Escenario: HU-01.1
    Dado un gestor
    Cuando registra una solicitud con título y la envía
    Entonces la ve en su panel como «Enviada»

  Escenario: HU-01.2
    Dado un gestor
    Cuando envía una solicitud sin título
    Entonces se le pide el título
""",
    "ISS-02.feature": """# language: es
Característica: HU-02 Revisar una solicitud

  Escenario: HU-02.1
    Dada una solicitud enviada por un gestor
    Cuando el revisor la devuelve con un comentario
    Entonces queda «Devuelta»

  Escenario: HU-02.2
    Dada una solicitud devuelta
    Cuando el gestor la corrige
    Entonces vuelve a «Enviada»
""",
}

ALTA = [{"sail": ["load"]}, {"sail": ["navigate", "Nueva solicitud"]},
        {"sail": ["interact", "Título", "QA {pasada}", "Importe (€)", "12.50"]},
        {"sail": ["interact", "Enviar"], "espera": {"completado": True}}]
GUIONES = {
    "HU-01.1": {"escenario": "HU-01.1", "dice": ["Dado un gestor", "Cuando registra una solicitud con título y la envía",
                                                  "Entonces la ve en su panel como «Enviada»"],
                "host": HOST, "site": "solicitudes", "roles": {"gestor": "qa.gestor"},
                "dado": [], "cuando": ALTA,
                "entonces": [{"sail": ["load"]},
                             {"sail": ["interact", "🔍", "QA {pasada}"],
                              "espera": {"fila": {"con": "QA {pasada}", "Estado": "Enviada"}, "hay": ["Nueva solicitud"],
                                         "no_hay": ["Revisar"]}}]},
    "HU-01.2": {"escenario": "HU-01.2", "dice": ["Dado un gestor", "Cuando envía una solicitud sin título",
                                                  "Entonces se le pide el título"],
                "host": HOST, "site": "solicitudes", "roles": {"gestor": "qa.gestor"},
                "dado": [], "cuando": [{"sail": ["load"]}, {"sail": ["navigate", "Nueva solicitud"]}],
                "entonces": [{"sail": ["interact", "Enviar"], "espera": {"texto": ["Indica el título"]}},
                             # y no se ha dado de alta nada: lo buscado está en la caja de búsqueda, no en una fila
                             {"sail": ["load"]}, {"sail": ["interact", "🔍", "{pasada}"]},
                             {"sail": ["show"], "espera": {"sin_fila": "{pasada}", "texto": ["No hay solicitudes"]}}]},
    "HU-02.1": {"escenario": "HU-02.1", "dice": ["Dada una solicitud enviada por un gestor",
                                                  "Cuando el revisor la devuelve con un comentario",
                                                  "Entonces queda «Devuelta»"],
                "host": HOST, "site": "solicitudes", "roles": {"gestor": "qa.gestor", "revisor": "qa.revisor"},
                "dado": [{**p, "rol": "gestor"} for p in ALTA],
                "cuando": [{"rol": "revisor", "sail": ["load"]},
                           {"rol": "revisor", "sail": ["interact", "🔍", "QA {pasada}"]},
                           {"rol": "revisor", "selecciona": "QA {pasada}", "espera": {"hay": ["Revisar"]}},
                           {"rol": "revisor", "sail": ["navigate", "Revisar"]},
                           {"rol": "revisor", "sail": ["interact", "Comentario", "Falta el importe"]},
                           {"rol": "revisor", "sail": ["interact", "Devolver"], "espera": {"completado": True}}],
                "entonces": [{"rol": "gestor", "sail": ["load"]},
                             {"rol": "gestor", "sail": ["interact", "🔍", "QA {pasada}"],
                              "espera": {"fila": {"con": "QA {pasada}", "Estado": "Devuelta"}}},
                             {"rol": "revisor", "sail": ["load"], "espera": {"sin_texto": ["No hay solicitudes"]}}]},
}


def ok(nombre, cond, detalle=""):
    print(("✓ " if cond else "✗ ") + nombre + ("" if cond else f"\n    {str(detalle)[-1500:]}"))
    if not cond:
        fallos.append(nombre)


def escribe(ruta, texto):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", encoding="utf-8", newline="\n") as f:
        f.write(texto)


def a_json(d):
    return json.dumps(d, ensure_ascii=False, indent=1) + "\n"


class Prueba:
    def __init__(self, tmp):
        self.p = tmp / "Proyecto de prueba" / "Gestión de solicitudes"
        self.sesiones = tmp / "sesiones de sail"
        self.app = tmp / "app.json"
        for nombre, texto in FEATURES.items():
            escribe(self.p / "construccion" / "EV-01" / nombre, texto)
        for nombre, g in GUIONES.items():
            self.guion(nombre, g)
        for u in ("qa.gestor", "qa.revisor"):
            self.sesion(u)
        escribe(self.app, a_json({"filas": []}))
        self.entorno = dict(os.environ, SAIL_CLI=str(SIMULADO), SAIL_SIMULADO_APP=str(self.app), PYTHONUTF8="1",
                            PYTHONDONTWRITEBYTECODE="1")

    def guion(self, nombre, g):
        escribe(self.p / "qa" / "EV-01" / f"{nombre}.json", a_json(g))

    def sesion(self, usuario, **mas):
        escribe(self.sesiones / "dev" / usuario / "session.json",
                a_json({"hostname": HOST, "username": usuario, "cookies": ["JSESSIONID=x"], "csrfToken": "x", **mas}))

    def defecto(self, **d):
        app = json.loads(self.app.read_text(encoding="utf-8"))
        app["defecto"] = d
        escribe(self.app, a_json(app))

    def qa(self, *args, sesiones=True, entorno=None):
        orden = [sys.executable, str(QA), *args] + (["--sesiones", str(self.sesiones)] if sesiones else [])
        r = subprocess.run(orden, capture_output=True, text=True, encoding="utf-8", errors="replace",
                           env=entorno or self.entorno, timeout=300)
        return r.returncode, r.stdout + r.stderr

    def repetir(self, *mas, **kw):
        return self.qa("repetir", str(self.p), "EV-01", *mas, **kw)

    def resultado(self):
        f = self.p / "qa" / "EV-01" / "resultado.json"
        return json.loads(f.read_text(encoding="utf-8")), f.read_bytes()


def llamadas(t):
    """Cuántas veces se ha llamado al SAIL CLI simulado."""
    return json.loads(t.app.read_text(encoding="utf-8")).get("llamadas", 0)


def issue(iss, iid, criterios):
    return iss.Issue(filas=[], requisitos=[], id=iid, version="v1", objetos=["SIM_Form"], criterios=criterios,
                     situacion={"SIM_Form": "nuevo"})


def main():
    for st in (sys.stdout, sys.stderr):
        st.reconfigure(encoding="utf-8", errors="replace")
    if not QA.is_file():
        ok("existe skills/appian-qa/scripts/qa.py", False, str(QA))
        return 1
    sys.path.insert(0, str(ISSUES))
    import issues as iss
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="appian-qa-"))
    try:
        t = Prueba(tmp)
        resultados = lambda: {k: v["resultado"] for k, v in t.resultado()[0]["escenarios"].items()}

        # las sesiones: por usuario y host, en cualquier carpeta; sin ella, cómo entrar (sin contraseña)
        c, out = t.qa("sesiones", HOST, "qa.gestor", "qa.revisor", "qa.otro")
        ok("sesiones da la carpeta de cada cuenta y, de la que no la tiene, cómo entrar sin escribir la contraseña",
           c == 2 and (t.sesiones / "dev" / "qa.gestor").as_posix() in out and "qa.otro · sin sesión" in out
           and f"sail login {HOST} --data-dir" in out and "SAIL_PASSWORD" in out, out)
        c, out = t.qa("sesiones", "https://DEV.ejemplo.test/suite", "qa.gestor")
        ok("el host vale también como URL", c == 0 and "qa.gestor ·" in out and "sin sesión" not in out, out)

        # pasan, y dos repeticiones dan lo mismo; lo que se teclea es distinto cada vez ({pasada})
        c, out = t.repetir()
        datos, crudo = t.resultado()
        ok("los tres guiones pasan, con su issue, y el escenario sin guion se dice",
           c == 0 and resultados() == {"HU-01.1": "pasa", "HU-01.2": "pasa", "HU-02.1": "pasa"}
           and datos["escenarios"]["HU-02.1"]["issue"] == "ISS-02" and datos["sinGuion"] == ["HU-02.2"]
           and "HU-02.2 · sin guion" in out, out)
        ok("resultado.json va con finales de línea \\n", b"\r" not in crudo)
        primera = resultados()
        c, out = t.repetir()
        titulos = [f["Título"] for f in json.loads(t.app.read_text(encoding="utf-8"))["filas"]]
        ok("dos repeticiones dan lo mismo, con datos distintos cada vez",
           c == 0 and resultados() == primera and len(titulos) == 4 and len(set(titulos)) == 4, out + str(titulos))
        hecha = issue(iss, "ISS-01", ["HU-01.1", "HU-01.2"])
        escribe(t.p / "construccion" / "EV-01" / "verificacion" / "ISS-01.json", a_json(
            {"issue": {"id": "ISS-01", "unidad": "EV-01", "version": "v1"},
             "objetos": [{"pedido": "SIM_Form", "existe": True, "diferencias": {}}],
             "pruebas": {"ejecutadas": True, "objetos": [{"objeto": "SIM_Form", "de": "issue", "casos": 1, "pasan": 1,
                                                          "fallan": []}]}}))
        ok("con su QA pasando, la issue está hecha", iss.estado(t.p, "EV-01", hecha) == (True, "hecha"),
           iss.estado(t.p, "EV-01", hecha))

        # un defecto: falla, con el paso y lo que salió, y su issue vuelve a pendiente
        t.defecto(estado_alta="Borrador")
        c, out = t.repetir()
        e = t.resultado()[0]["escenarios"]["HU-01.1"]
        ok("con un defecto, el guion falla en su paso, dice qué salió y que su issue vuelve a pendiente",
           c == 1 and e["resultado"] == "falla" and e["paso"] == "entonces 2" and "Estado «Borrador»" in e["motivo"]
           and "ISS-01 vuelve a pendiente" in out and resultados()["HU-01.2"] == "pasa", out)
        hecha_qa = iss.estado(t.p, "EV-01", hecha)
        ok("issues.estado() da pendiente la issue con un escenario que falla en QA, y no la otra",
           hecha_qa[0] is False and "falla en QA: HU-01.1" in hecha_qa[1]
           and iss.estado(t.p, "EV-01", issue(iss, "ISS-03", ["HU-09.1"]))[0] is False   # sin verificar: no por QA
           and "QA" not in iss.estado(t.p, "EV-01", issue(iss, "ISS-03", ["HU-09.1"]))[1], hecha_qa)
        # B2: una persona puede marcar el escenario como no necesario (indice.py … --sin-prueba HU-01.1), y la marca vale
        # para ese fallo: el motivo lleva {pasada}, no lo que valió, y la misma repetición da el mismo
        c, out = t.repetir("--escenario", "HU-01.1")
        e2 = t.resultado()[0]["escenarios"]["HU-01.1"]
        ok("el motivo de un fallo lleva {pasada}, no lo que valió: repetido con el mismo defecto, dice lo mismo",
           c == 1 and "«QA {pasada}»" in e["motivo"] and e2["motivo"] == e["motivo"] and e2["paso"] == e["paso"],
           (e, e2))
        error = iss.error_de(f"{e['paso']}: {e['motivo']}")
        marca = {"issue": "ISS-01", "version": "v1", "objeto": "QA", "caso": "HU-01.1", "error": error,
                 "motivo": "x", "quien": "Ana", "cuando": "2026-10-14T10:00Z"}
        ok("el escenario de QA marcado como no necesario para ese fallo no la deja pendiente, y lo dice",
           iss.falla_en_qa(t.p, "EV-01", hecha, [marca]) == []
           and iss.estado(t.p, "EV-01", hecha, [marca]) == (True, "hecha · marcada como no necesaria: QA «HU-01.1»"),
           iss.estado(t.p, "EV-01", hecha, [marca]))
        otras = [{**marca, "error": "entonces 1: otro fallo"}, {**marca, "version": "v0"}, {**marca, "issue": "ISS-02"}]
        ok("… y no vale con otro fallo, para otra versión de la issue ni para otra issue",
           all(iss.falla_en_qa(t.p, "EV-01", hecha, [x]) == ["HU-01.1"] for x in otras), otras)
        t.defecto()
        c, out = t.repetir("--escenario", "HU-01.1")
        ok("corregido, repetir solo su escenario lo deja pasando y la issue, hecha; los demás se quedan como estaban",
           c == 0 and resultados()["HU-01.1"] == "pasa" and resultados()["HU-02.1"] == "falla"
           and "HU-02.1" not in out and iss.estado(t.p, "EV-01", hecha) == (True, "hecha"), out)
        c, out = t.repetir()
        ok("y la unidad entera vuelve a pasar", c == 0 and set(resultados().values()) == {"pasa"}, out)

        # lo que la aplicación hace mal: el guion falla y su issue vuelve a pendiente
        def variante(nombre, cambio, esperado, que, resultado="falla", codigo=1):
            g = json.loads(json.dumps(GUIONES[nombre]))
            cambio(g)
            t.guion(nombre, g)
            c, out = t.repetir("--escenario", nombre)
            e = t.resultado()[0]["escenarios"][nombre]
            ok(que, c == codigo and e["resultado"] == resultado and esperado in e.get("motivo", ""), out)
            t.guion(nombre, GUIONES[nombre])
            return out, e
        variante("HU-01.2", lambda g: g["cuando"].append({"sail": ["interact", "Guardar y salir"]}),
                 "no component matches", "un error de SAIL CLI, que sale en texto, es el motivo del fallo")
        variante("HU-01.2", lambda g: g["cuando"].append({"sail": ["interact", "Título", ""]}),
                 "no cambió nada", "un paso que el servidor acepta sin cambiar nada falla")
        variante("HU-01.1", lambda g: g["cuando"][-1]["espera"].update(fila={"con": "QA {pasada}", "Estado": "Enviada"}),
                 "tras un «load»", "comprobar la página justo tras enviar el formulario (la de antes) falla y dice por qué")
        variante("HU-01.1", lambda g: g["entonces"][-1]["espera"].update(sin_fila="QA {pasada}"),
                 "hay una fila con", "una fila que no debería estar hace fallar «sin_fila»")
        variante("HU-01.1", lambda g: g["cuando"].insert(1, {"sail": ["interact", "Ver detalle"]}),
                 "está 2 veces", "dos enlaces con el mismo texto (nth y of): el paso falla, no se pulsa uno al azar")
        variante("HU-02.1", lambda g: g.update(cuando=[g["cuando"][0], {"rol": "revisor", "sail": ["interact", "🔍", "QA"]},
                                                       {"rol": "revisor", "selecciona": "QA"}] + g["cuando"][3:]),
                 "filas llevan «QA»", "«selecciona» con varias filas que lo llevan falla, no marca una al azar")
        out, e = variante("HU-02.1", lambda g: g["dado"].append({"rol": "gestor", "sail": ["interact", "Guardar y salir"]}),
                          "no component matches", "un fallo al preparar el «dado» falla en su paso")
        ok("y dice que es del «dado», que puede venir de otra issue",
           e.get("paso") == "dado 5" and "puede venir de otra issue" in out, out)

        # un guion a medias o mal escrito no devuelve la issue a quien construye: queda «por terminar» para QA
        t.repetir()     # los guiones como estaban: todo pasa
        por_terminar = lambda nombre, cambio, esperado, que: variante(nombre, cambio, esperado, que,
                                                                      resultado="guion por terminar", codigo=2)
        por_terminar("HU-01.1", lambda g: g.update(entonces=[{"sail": ["interact", "🔍", "QA {pasada}"]}]),
                     "no comprueba nada que se vea", "un guion que no comprueba nada en «entonces» (a medias)")
        ok("un guion por terminar no devuelve su issue a pendiente", iss.estado(t.p, "EV-01", hecha) == (True, "hecha"),
           iss.estado(t.p, "EV-01", hecha))
        por_terminar("HU-01.1", lambda g: g["entonces"][-1].update(espera={"sin_fila": "nadie"}),
                     "no comprueba nada que se vea", "un «entonces» solo con comprobaciones negativas")
        por_terminar("HU-01.1", lambda g: g["entonces"][-1].update(espera={"filas": {"con": "QA {pasada}"}}),
                     "«filas» no es una comprobación", "una clave de «espera» mal escrita")
        por_terminar("HU-01.1", lambda g: g["entonces"][-1].update(espera={"hay": []}),
                     "«hay» es una lista de textos", "una comprobación vacía («hay»: [])")
        por_terminar("HU-01.1", lambda g: g["entonces"][-1].update(espera={"texto": [""]}),
                     "«texto» es una lista de textos", "un texto vacío («texto»: [\"\"])")
        por_terminar("HU-01.1", lambda g: g["cuando"][0].update(esperar={"hay": ["Nueva solicitud"]}),
                     "«esperar» no es una clave de un paso", "una clave de un paso mal escrita")
        por_terminar("HU-01.2", lambda g: g["cuando"].append({"sail": ["interact", "0123456789abcdef0123456789abcdef"]}),
                     "cambia en cada carga", "una ref de un solo render (refIsPerRender) o un _cId")
        por_terminar("HU-02.1", lambda g: g["cuando"].insert(0, {"rol": "jefe", "sail": ["load"]}),
                     "no está en «roles»", "un paso con un rol que el guion no declara")

        # un load que aún no enseña lo nuevo (el proceso no ha terminado) se repite antes de fallar
        t.defecto(lento=True)
        c, out = t.repetir("--escenario", "HU-01.1")
        ok("si la solicitud nueva aún no se ve tras cargar y buscar, se vuelve a cargar y a buscar, y el guion pasa",
           c == 0 and resultados()["HU-01.1"] == "pasa", out)
        t.defecto()
        c, out = t.repetir()
        ok("con los guiones como estaban, todo vuelve a pasar", c == 0 and set(resultados().values()) == {"pasa"}, out)

        # lo siguiente a la última issue es el QA de la unidad, en otra sesión; marcarla sin QA se avisa, no se impide
        m_, ctx_ = SimpleNamespace(raiz=t.p, tablas=lambda *a, **k: [], docs={}), SimpleNamespace(reaplicar=lambda u: [])
        ultima = issue(iss, "ISS-02", ["HU-02.1", "HU-02.2"])
        plan = iss.Plan("EV-01", "Solicitudes", "SIM", [hecha, ultima], [])
        ordenes, notas = iss.orden_de_terminar(m_, ctx_, plan, ultima)
        ok("la última issue de una unidad con escenarios dice que lo siguiente es su QA, en otra sesión, y no pone la orden "
           "de marcarla junto a la de verificar",
           len(ordenes) == 1 and " verificar " in ordenes[0] and any(
               "lo siguiente es el QA de la unidad, en otra sesión" in n and " EV-01 construida`" in n for n in notas),
           "\n".join(ordenes + notas))
        sin_escenarios = iss.Plan("EV-01", "Retoque", "SIM", [issue(iss, "ISS-01", []), issue(iss, "ISS-02", [])], [])
        ordenes, _ = iss.orden_de_terminar(m_, ctx_, sin_escenarios, sin_escenarios.issues[1])
        ok("en una unidad sin escenarios (un retoque) no hay QA: la última issue lleva la orden de marcarla, como siempre",
           len(ordenes) == 2 and ordenes[1].endswith(" EV-01 construida") and iss.avisos_qa(t.p, sin_escenarios) == [],
           "\n".join(ordenes))
        ok("al marcarla, avisa si a su QA le faltan escenarios (sin guion) o si la unidad no tiene QA",
           iss.avisos_qa(t.p, plan) == ["el QA de EV-01 no está completo (sin guion: HU-02.2): lo hace QA (appian-qa)"]
           and "EV-05 no tiene QA" in iss.avisos_qa(t.p, iss.Plan("EV-05", "Otra", "SIM", [ultima], []))[0],
           iss.avisos_qa(t.p, plan))

        # fuera de desarrollo no se repite nada: SAIL CLI crea datos y lanza procesos (técnico §0)
        tecnico = t.p / "analisis" / "tecnico.md"
        escribe(tecnico, "# Especificación técnica\n\n## 0. Contexto\n\n| Dato | Valor |\n|---|---|\n"
                         "| URL de desarrollo | https://otro.ejemplo.test |\n| URL de producción | https://dev.ejemplo.test/suite |\n")
        antes = llamadas(t)
        c, out = t.repetir()
        ok("un guion que apunta a la URL de producción de técnico §0 no se repite, y dice por qué",
           c == 2 and "entorno de producción (técnico §0)" in out and "solo se repiten en desarrollo" in out
           and llamadas(t) == antes, out)
        tecnico.unlink()

        # SAIL CLI que deja de responder a mitad del recorrido es un fallo; al primer paso, no se ha podido repetir
        spec = importlib.util.spec_from_file_location("qa_simulado", QA)
        qa = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(qa)
        os.environ.update(SAIL_CLI=str(SIMULADO), SAIL_SIMULADO_APP=str(t.app))
        qa.ESPERA_SAIL = 3
        t.defecto(cuelga_desde=llamadas(t) + 2)
        e = qa.repite_unidad(t.p, "EV-01", {"HU-01.2"}, qa.sesiones([str(t.sesiones)]))[1]["HU-01.2"]
        ok("si SAIL CLI responde al primer paso y deja de responder después, el escenario falla",
           e["resultado"] == "falla" and "no respondió" in e["motivo"] and "sinRepetir" not in e, e)
        t.defecto(cuelga_desde=llamadas(t) + 1)
        e = qa.repite_unidad(t.p, "EV-01", {"HU-01.2"}, qa.sesiones([str(t.sesiones)]))[1]["HU-01.2"]
        ok("si no responde ni al primero, no se ha podido repetir: se queda lo anterior",
           e["resultado"] == "falla" and "no respondió" in e.get("sinRepetir", ""), e)
        t.defecto(lee_stdin=True)
        salida = tmp / "salida stdin.txt"
        with open(salida, "w", encoding="utf-8") as s:
            pr = subprocess.Popen([sys.executable, str(QA), "repetir", str(t.p), "EV-01", "--escenario", "HU-01.2",
                                   "--sesiones", str(t.sesiones)], stdin=subprocess.PIPE, stdout=s,
                                  stderr=subprocess.STDOUT, env=t.entorno)
            try:
                codigo = pr.wait(timeout=60)
            except subprocess.TimeoutExpired:
                pr.kill()
                codigo = None
            pr.stdin.close()
        ok("SAIL CLI se lanza sin entrada: uno que la lee no se queda esperando", codigo == 0 and resultados()["HU-01.2"]
           == "pasa", salida.read_text(encoding="utf-8", errors="replace"))
        t.defecto()

        # una sesión caducada o que falta: no se puede repetir, y se queda el resultado anterior
        t.sesion("qa.revisor", caducada=True)
        c, out = t.repetir()
        e = t.resultado()[0]["escenarios"]["HU-02.1"]
        ok("con la sesión del revisor caducada, HU-02.1 sale sin repetir, conserva su «pasa» y dice cómo entrar",
           c == 2 and e["resultado"] == "pasa" and "caducado" in e["sinRepetir"]
           and f"sail login {HOST} --data-dir" in e["sinRepetir"] and resultados()["HU-01.1"] == "pasa", out)
        crudo = t.resultado()[1].decode("utf-8")
        ok("resultado.json, que se sube, no lleva la ruta de ninguna sesión ni de la carpeta personal",
           str(t.sesiones) not in crudo and t.sesiones.as_posix() not in crudo and str(pathlib.Path.home()) not in crudo
           and pathlib.Path.home().as_posix() not in crudo, crudo)
        t.sesion("qa.revisor")
        vacia = tmp / "otra carpeta"
        vacia.mkdir()
        c, out = t.qa("repetir", str(t.p), "EV-01", "--sesiones", str(vacia), sesiones=False)
        ok("sin ninguna sesión en el equipo, nada se repite (sale con 2) y los resultados se quedan",
           c == 2 and "no hay sesión de qa.gestor" in out and set(resultados().values()) == {"pasa"}, out)

        # el escenario cambia: su guion queda desfasado, no se repite y no devuelve la issue a pendiente
        t.defecto(estado_alta="Borrador")
        f = t.p / "construccion" / "EV-01" / "ISS-01.feature"
        escribe(f, f.read_text(encoding="utf-8").replace("como «Enviada»", "como «Enviada», con su número"))
        c, out = t.repetir()
        e = t.resultado()[0]["escenarios"]
        ok("si el escenario cambia, su guion sale desfasado (dice lo nuevo), no se repite y no cuenta como fallo",
           e["HU-01.1"]["resultado"] == "desfasado" and "con su número" in e["HU-01.1"]["motivo"]
           and e["HU-02.1"]["resultado"] == "falla" and c == 1, out)
        ok("un guion desfasado no devuelve su issue a pendiente", iss.estado(t.p, "EV-01", hecha) == (True, "hecha"),
           iss.estado(t.p, "EV-01", hecha))
        c, out = t.qa("repetir", str(t.p), "EV-01", "EV-09")
        ok("un fallo (1) pesa más que una unidad sin guiones (2)", c == 1 and "EV-09 · sin guiones" in out, out)
        t.defecto()

        # el escenario de hoy es el del funcional: una unidad posterior que lo cambió a propósito deja el guion
        # desfasado (para rehacerlo), no un fallo que reabra una issue ya en producción
        funcional = t.p / "analisis" / "funcional.md"
        escribe(funcional, "# Diseño funcional\n\nVersión: 1.1\n\n## 4. Historias de usuario\n\n"
                "**HU-01 — Registrar una solicitud** ✅\n\nSe acepta si:\n"
                "- `HU-01.1` Dado un gestor, cuando registra una solicitud con título y la envía, entonces la ve en su "
                "panel como «Enviada».\n"
                "- `HU-01.2` Dado un gestor, cuando envía una solicitud sin título, entonces se le pide el título.\n\n"
                "**HU-02 — Revisar una solicitud** ✅\n\nSe acepta si:\n"
                "- `HU-02.1` Dada una solicitud enviada por un gestor, cuando el revisor la devuelve con un comentario, "
                "entonces queda «Devuelta» y el gestor ve el comentario.\n"
                "- `HU-02.2` Dada una solicitud devuelta, cuando el gestor la corrige, entonces vuelve a «Enviada».\n")
        t.defecto(estado_alta="Borrador")     # HU-02.1 fallaría si se repitiera
        c, out = t.repetir()
        e = t.resultado()[0]["escenarios"]
        ok("con funcional, el guion se compara con lo que dice hoy: el que cambió en el funcional sale desfasado, no falla, "
           "y el que solo cambió en un .feature viejo se repite",
           e["HU-02.1"]["resultado"] == "desfasado" and "y el gestor ve el comentario" in e["HU-02.1"]["motivo"]
           and e["HU-01.1"]["resultado"] == "falla" and e["HU-01.2"]["resultado"] == "pasa", out)
        funcional.unlink()
        t.defecto()

        # sin SAIL CLI no se repite nada
        sin = dict(t.entorno, PATH=str(pathlib.Path(sys.executable).parent))
        sin.pop("SAIL_CLI")
        c, out = t.qa("repetir", str(t.p), entorno=sin)
        ok("sin SAIL CLI lo dice y sale con 2", c == 2 and "Sin SAIL CLI" in out, out)
        c, out = t.qa("repetir", str(t.p), "EV-09")
        ok("una unidad sin guiones sale con 2 y lo dice", c == 2 and "EV-09 · sin guiones" in out, out)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n{'Todo bien' if not fallos else f'{len(fallos)} fallos'}")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
