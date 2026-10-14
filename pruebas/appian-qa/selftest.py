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
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

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
                "entonces": [{"sail": ["interact", "Enviar"], "espera": {"texto": ["Indica el título"]}}]},
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
             "objetos": [{"pedido": "SIM_Form", "existe": True, "diferencias": {}}]}))
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
        t.defecto()
        c, out = t.repetir("--escenario", "HU-01.1")
        ok("corregido, repetir solo su escenario lo deja pasando y la issue, hecha; los demás se quedan como estaban",
           c == 0 and resultados()["HU-01.1"] == "pasa" and resultados()["HU-02.1"] == "falla"
           and "HU-02.1" not in out and iss.estado(t.p, "EV-01", hecha) == (True, "hecha"), out)
        c, out = t.repetir()
        ok("y la unidad entera vuelve a pasar", c == 0 and set(resultados().values()) == {"pasa"}, out)

        # lo que hace fallar un guion mal escrito o un paso que no se cumple
        def variante(nombre, cambio, esperado, que):
            g = json.loads(json.dumps(GUIONES[nombre]))
            cambio(g)
            t.guion(nombre, g)
            c, out = t.repetir("--escenario", nombre)
            e = t.resultado()[0]["escenarios"][nombre]
            ok(que, c == 1 and e["resultado"] == "falla" and esperado in e["motivo"], out)
            t.guion(nombre, GUIONES[nombre])
        variante("HU-01.2", lambda g: g["cuando"].append({"sail": ["interact", "0123456789abcdef0123456789abcdef"]}),
                 "cambia en cada carga", "una ref de un solo render (refIsPerRender) o un _cId se rechazan")
        variante("HU-01.2", lambda g: g["cuando"].append({"sail": ["interact", "Guardar y salir"]}),
                 "no component matches", "un error de SAIL CLI, que sale en texto, es el motivo del fallo")
        variante("HU-01.2", lambda g: g["cuando"].append({"sail": ["interact", "Título", ""]}),
                 "no cambió nada", "un paso que el servidor acepta sin cambiar nada falla")
        variante("HU-01.1", lambda g: g.update(entonces=[{"sail": ["interact", "🔍", "QA {pasada}"]}]),
                 "no llega a comprobar el «entonces»", "un guion que no comprueba nada en «entonces» (a medias) falla")
        variante("HU-01.1", lambda g: g["cuando"][-1]["espera"].update(fila={"con": "QA {pasada}", "Estado": "Enviada"}),
                 "tras un «load»", "comprobar la página justo tras enviar el formulario (la de antes) falla y dice por qué")
        variante("HU-02.1", lambda g: g["cuando"].insert(0, {"rol": "jefe", "sail": ["load"]}),
                 "no está en «roles»", "un paso con un rol que el guion no declara falla")

        # un load que aún no enseña lo nuevo (el proceso no ha terminado) se repite antes de fallar
        t.defecto(lento=True)
        c, out = t.repetir("--escenario", "HU-01.1")
        ok("si la solicitud nueva aún no se ve tras cargar y buscar, se vuelve a cargar y a buscar, y el guion pasa",
           c == 0 and resultados()["HU-01.1"] == "pasa", out)
        t.defecto()
        c, out = t.repetir()
        ok("con los guiones como estaban, todo vuelve a pasar", c == 0 and set(resultados().values()) == {"pasa"}, out)

        # una sesión caducada o que falta: no se puede repetir, y se queda el resultado anterior
        t.sesion("qa.revisor", caducada=True)
        c, out = t.repetir()
        e = t.resultado()[0]["escenarios"]["HU-02.1"]
        ok("con la sesión del revisor caducada, HU-02.1 sale sin repetir, conserva su «pasa» y dice cómo entrar",
           c == 2 and e["resultado"] == "pasa" and "caducado" in e["sinRepetir"]
           and f"sail login {HOST} --data-dir" in e["sinRepetir"] and resultados()["HU-01.1"] == "pasa", out)
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
