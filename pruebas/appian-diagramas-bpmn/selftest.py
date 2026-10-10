#!/usr/bin/env python3
"""Prueba de la skill de diagramas de principio a fin, en una carpeta temporal.

Crea el ejemplo, lo cambia, simula una edición a mano en draw.io (también guardada comprimida),
la compara y la acepta, vuelve a cambiarlo respetando lo movido a mano, exporta BPMN 2.0 y
comprueba los errores de validación. Con el segundo ejemplo comprueba que nada se pisa, el lado de las
etiquetas, los tipos de inicio y tarea, el flujo por defecto, los participantes externos, las notas y el
ancho del PNG. Comprueba también lo que se hace sin navegador, un proceso que no cabe en una página (tramos), que la
colocación por capas no dibuje conexiones falsas ni deje las etiquetas pegadas a la flecha, que la línea de una nota no
cruce la etiqueta de su paso, el temporizador que interrumpe, los avisos sin capa y el error suelto en BPMN.
Sale con 0 si todo va bien (tarda unos tres minutos).

  python3 pruebas/appian-diagramas-bpmn/selftest.py
  DIAGRAMAS_SIN_NAVEGADOR=1 python3 pruebas/appian-diagramas-bpmn/selftest.py   # solo lo que no necesita navegador

Prueba la skill de $PLUGIN_A_PROBAR/skills/appian-diagramas-bpmn (por defecto, la de este repositorio) con los
procesos de ejemplo de datos/."""
import base64, json, os, pathlib, re, shutil, subprocess, sys, tempfile, urllib.parse, zlib
import xml.etree.ElementTree as ET
from struct import unpack

sys.dont_write_bytecode = True  # importa los módulos de la skill: sin __pycache__ en el plugin
AQUI = pathlib.Path(__file__).resolve().parent
PLUGIN = pathlib.Path(os.environ.get("PLUGIN_A_PROBAR") or AQUI.parents[1]).resolve()
SCRIPTS = PLUGIN / "skills" / "appian-diagramas-bpmn" / "scripts"
CLI = [sys.executable, str(SCRIPTS / "diagrama.py")]
EJEMPLO = AQUI / "datos" / "solicitud.json"
PEDIDO = AQUI / "datos" / "pedido.json"
SIN_NAVEGADOR = os.environ.get("DIAGRAMAS_SIN_NAVEGADOR") == "1"   # el propio selftest, sin navegador
ANCHO_PAGINA = 1600     # lo que se lee en una página vertical
ANCHO_PNG = 3300        # el PNG, a doble resolución como mucho
fallos = []


def entorno(sin_navegador=False, temporales=None):
    """El entorno de una orden: sin navegador (DIAGRAMAS_SIN_NAVEGADOR=1) y con la carpeta temporal que se diga."""
    env = dict(os.environ)
    if sin_navegador:
        env["DIAGRAMAS_SIN_NAVEGADOR"] = "1"
    if temporales:
        env.update(TMPDIR=str(temporales), TEMP=str(temporales), TMP=str(temporales))
    return env


def run(*args, esperado=0, env=None):
    r = subprocess.run(CLI + [str(a) for a in args], capture_output=True, text=True, encoding="utf-8", env=env)
    if r.returncode == 2 and esperado != 2:
        print(r.stdout + r.stderr); sys.exit(2)
    if r.returncode != esperado:
        fallos.append(f"{' '.join(map(str, args[:1]))}: salida {r.returncode} (esperaba {esperado})\n{r.stdout}{r.stderr}")
    return r.stdout + r.stderr


def check(cond, texto):
    print(("OK   " if cond else "FALLO ") + texto)
    if not cond:
        fallos.append(texto)


def celdas(ruta):
    root = ET.parse(ruta).getroot().find("diagram/mxGraphModel/root")
    return root, {c.get("id"): c for c in root}


# ---------------------------------------------------------------- Tarea 10: datos de Appian y notas
NS_BPMN = {"bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL", "bpmndi": "http://www.omg.org/spec/BPMN/20100524/DI",
           "di": "http://www.omg.org/spec/DD/20100524/DI"}
XSI_TYPE = "{http://www.w3.org/2001/XMLSchema-instance}type"


def datos_de_appian(tmp):
    """Los datos de Appian (nodo, temporizador, proceso llamado y condición) y el evento de error de borde pasan por
    crear, leer, bpmn, actualizar (colocación automática y a mano) y comparar --aceptar sin perderse."""
    import drawio_modelo as dm
    ns = NS_BPMN
    origen = AQUI / "datos" / "semantico.json"   # un proceso con datos de Appian, como los que dibuja ingeniería inversa
    base = json.loads(origen.read_text(encoding="utf-8"))
    d = tmp / "Carpeta con espacios" / "Gestión app" / "semántico.drawio"
    run("crear", origen, "-o", d)
    proc = dm.leer(str(d))[0]
    paso = {p["id"]: p for p in proc["pasos"]}
    cond = {(f["de"], f["a"]): f.get("condicion") for f in proc["flujos"]}
    check(paso["EV-01"].get("nodo") == "1" and paso["ACT-02"].get("nodo") == "4" and cond[("GW-01", "ACT-02")] == "pv!ok"
          and paso["EV-02"]["tipo"] == "error" and dm.comparar(base, proc) == [],
          "datos de Appian: leer() devuelve nodo, condicion y el evento de error")
    leido = json.loads(run("leer", d).split("\naviso")[0])
    check(dm.comparar(base, leido) == [] and any(f.get("condicion") == "pv!ok" for f in leido["flujos"]),
          "datos de Appian: la orden leer los devuelve")
    obj = next((e for e in ET.parse(d).getroot().iter("object") if e.get("id") == "EV-01"), None)
    check(obj is not None and obj.get("nodo") == "1" and obj.find("mxCell") is not None and obj.find("mxCell").get("id") is None,
          "datos de Appian: en el .drawio son atributos de un <object> que envuelve la celda («Editar datos»)")
    # BPMN 2.0
    bpmn = d.with_suffix(".bpmn")
    run("bpmn", d)
    primero = bpmn.read_bytes()
    run("bpmn", d)
    check(bpmn.read_bytes() == primero, "bpmn: dos exportaciones iguales")
    b = ET.fromstring(primero)
    pr = b.find("bpmn:process", ns)
    inicio = pr.find("bpmn:startEvent[@id='EV-01']", ns)
    check([c.tag.split("}")[1] for c in inicio] == ["documentation", "outgoing"] and inicio[0].text == "nodo 1",
          "bpmn: «nodo 1» en la documentación del inicio, y los hijos en el orden del esquema")
    si = pr.find("bpmn:sequenceFlow[@name='Sí']/bpmn:conditionExpression", ns)
    check(si is not None and si.text == "pv!ok" and si.get(XSI_TYPE) == "bpmn:tFormalExpression",
          "bpmn: condición «pv!ok» con su xsi:type en el flujo «Sí»")
    check(pr.find("bpmn:exclusiveGateway[@id='GW-01']", ns).get("default") == pr.find("bpmn:sequenceFlow[@name='No']", ns).get("id"),
          "bpmn: flujo por defecto en la puerta")
    guardar = pr.find("bpmn:serviceTask[@name='Guardar']", ns).get("id")
    err = [e for e in pr.findall("bpmn:boundaryEvent", ns) if e.find("bpmn:errorEventDefinition", ns) is not None]
    check(len(err) == 1 and err[0].get("attachedToRef") == guardar and err[0].get("cancelActivity") == "true",
          "bpmn: evento de error en el borde de «Guardar», que interrumpe")
    nodos = [e.get("id") for e in pr if e.tag.split("}")[1] not in ("laneSet", "sequenceFlow", "textAnnotation", "association")]
    carriles = [e.get("id") for e in pr.iter(f"{{{ns['bpmn']}}}lane")]
    formas = [e.get("bpmnElement") for e in b.iter(f"{{{ns['bpmndi']}}}BPMNShape")]
    puntos = {e.get("bpmnElement"): len(e.findall("di:waypoint", ns)) for e in b.iter(f"{{{ns['bpmndi']}}}BPMNEdge")}
    check(len(nodos) == 7 and all(formas.count(i) == 1 for i in nodos + carriles)
          and all(puntos.get(f.get("id"), 0) >= 2 for f in pr.findall("bpmn:sequenceFlow", ns)),
          "bpmn: un BPMNShape por nodo y carril y un BPMNEdge con dos o más puntos por flujo")
    # actualizar con la colocación automática: claves nuevas, cambiadas y quitadas
    expresion = 'pv!ok and\n  pv!importe < 1000 & "sí"'
    (tmp / "d1.json").write_text(json.dumps({"cambios": [
        {"poner": {"id": "EV-01", "tipo": "inicio_temporizador", "nombre": "Cada día a las 08:00",
                   "temporizador": "R/2026-10-05T08:00:00+02:00/P1D"}},
        {"poner": {"id": "EV-05", "tipo": "temporizador", "carril": "Revisores", "nombre": "Diez días", "temporizador": "P10D"}},
        {"poner": {"id": "EV-06", "tipo": "fin", "carril": "Revisores", "nombre": "Plazo vencido"}},
        {"flujo": {"de": "ACT-01", "a": "EV-05", "discontinuo": True}}, {"flujo": {"de": "EV-05", "a": "EV-06"}},
        {"poner": {"id": "ACT-03", "tipo": "llamada", "carril": "Aplicación", "nombre": "Notificar", "nodo": "7",
                   "proceso_llamado": "Notificación de resolución"}},
        {"quitar_flujo": {"de": "ACT-02", "a": "EV-03"}}, {"flujo": {"de": "ACT-02", "a": "ACT-03"}},
        {"flujo": {"de": "ACT-03", "a": "EV-03"}},
        {"flujo": {"de": "GW-01", "a": "ACT-02", "condicion": expresion}},
        {"poner": {"id": "ACT-01", "nodo": ""}}]}, ensure_ascii=False), encoding="utf-8")
    run("actualizar", d, tmp / "d1.json")
    paso = {p["id"]: p for p in dm.leer(str(d))[0]["pasos"]}
    cond = {(f["de"], f["a"]): f.get("condicion") for f in dm.leer(str(d))[0]["flujos"]}
    check(paso["EV-01"].get("temporizador") == "R/2026-10-05T08:00:00+02:00/P1D" and paso["EV-05"].get("temporizador") == "P10D"
          and paso["ACT-03"].get("proceso_llamado") == "Notificación de resolución" and "nodo" not in paso["ACT-01"]
          and cond[("GW-01", "ACT-02")] == expresion and run("comparar", d).startswith("Sin cambios"),
          "actualizar (automática): pone, cambia y quita datos de Appian, también con < & \" y saltos de línea")
    run("bpmn", d)
    pr = ET.parse(bpmn).getroot().find("bpmn:process", ns)
    ciclo = pr.find("bpmn:startEvent[@id='EV-01']/bpmn:timerEventDefinition/bpmn:timeCycle", ns)
    plazo = pr.find("bpmn:boundaryEvent[@id='EV-05']", ns)
    duracion = plazo.find("bpmn:timerEventDefinition/bpmn:timeDuration", ns) if plazo is not None else None
    llamada = pr.find("bpmn:callActivity[@id='ACT-03']", ns)
    si = pr.find("bpmn:sequenceFlow[@name='Sí']/bpmn:conditionExpression", ns)
    check(ciclo is not None and ciclo.text == "R/2026-10-05T08:00:00+02:00/P1D" and ciclo.get(XSI_TYPE) == "bpmn:tFormalExpression"
          and duracion is not None and duracion.text == "P10D" and plazo.get("cancelActivity") == "false"
          and llamada is not None and llamada.get("calledElement") == "Notificación_de_resolución"
          and si is not None and si.text == expresion and pr.find("bpmn:userTask[@id='ACT-01']/bpmn:documentation", ns) is None,
          "bpmn: temporizador (timeCycle o timeDuration), proceso llamado, condición con < & \" y el plazo sin interrumpir")
    # en draw.io se cambia un dato («Editar datos») y se mueve una forma; comparar lo lista y --aceptar no pierde nada
    t = ET.parse(d)
    obj = next(e for e in t.getroot().iter("object") if e.get("id") == "ACT-02")
    obj.set("nodo", "40")
    g = obj.find("mxCell/mxGeometry"); g.set("y", str(float(g.get("y")) + 10))
    t.write(d, encoding="utf-8")
    check("ACT-02: nodo «4» → «40»" in run("comparar", d, esperado=1), "comparar: lista un dato de Appian cambiado en draw.io")
    run("comparar", d, "--aceptar")
    g = json.loads(d.with_suffix(".json").read_text(encoding="utf-8"))
    paso = {p["id"]: p for p in g["pasos"]}
    check(g["colocacion"]["modo"] == "manual" and paso["ACT-02"].get("nodo") == "40" and paso["EV-01"].get("nodo") == "1"
          and paso["EV-05"].get("temporizador") == "P10D" and paso["ACT-03"].get("proceso_llamado") == "Notificación de resolución"
          and any(f.get("condicion") == expresion for f in g["flujos"]),
          "comparar --aceptar: no pierde nodo, temporizador, proceso_llamado ni condicion")
    # actualizar con la colocación hecha a mano: celdas que pasan a llevar datos, datos que se quitan y pasos nuevos
    (tmp / "d2.json").write_text(json.dumps({"cambios": [
        {"poner": {"id": "ACT-01", "nodo": "2"}},
        {"poner": {"id": "ACT-03", "proceso_llamado": "Aviso de resolución"}},
        {"flujo": {"de": "ACT-02", "a": "ACT-03", "condicion": "pv!avisar"}},
        {"flujo": {"de": "GW-01", "a": "ACT-02", "condicion": ""}},
        {"poner": {"id": "ACT-04", "tipo": "script", "carril": "Aplicación", "nombre": "Calcular plazo", "nodo": "8"}},
        {"quitar_flujo": {"de": "ACT-03", "a": "EV-03"}}, {"flujo": {"de": "ACT-03", "a": "ACT-04"}},
        {"flujo": {"de": "ACT-04", "a": "EV-03", "condicion": "pv!plazo <> null"}}]}, ensure_ascii=False), encoding="utf-8")
    out = run("actualizar", d, tmp / "d2.json")
    proc = dm.leer(str(d))[0]
    paso = {p["id"]: p for p in proc["pasos"]}
    cond = {(f["de"], f["a"]): f.get("condicion") for f in proc["flujos"]}
    check("se ha respetado la colocación" in out and run("comparar", d).startswith("Sin cambios")
          and paso["ACT-01"].get("nodo") == "2" and paso["ACT-04"].get("nodo") == "8" and paso["ACT-02"].get("nodo") == "40"
          and paso["ACT-03"].get("proceso_llamado") == "Aviso de resolución" and cond[("ACT-02", "ACT-03")] == "pv!avisar"
          and cond[("GW-01", "ACT-02")] is None and cond[("ACT-04", "EV-03")] == "pv!plazo <> null",
          "actualizar (a mano): pone, cambia y quita datos de Appian en celdas que los tenían o no")
    # validar: un evento de error tiene que ir en el borde de su tarea
    suelto = json.loads(origen.read_text(encoding="utf-8"))
    for f in suelto["flujos"]:
        f.pop("discontinuo", None)
    (tmp / "suelto.json").write_text(json.dumps(suelto, ensure_ascii=False), encoding="utf-8")
    check("EV-02: un evento de error va en el borde" in run("validar", tmp / "suelto.json"),
          "validar: avisa de un evento de error que no está en el borde de una tarea")


PLAZOS = {"proceso": "Plazos", "carriles": ["Técnico", "Aplicación"],
          "pasos": [{"id": "EV-01", "tipo": "inicio", "carril": "Técnico", "nombre": "Solicitud recibida"},
                    {"id": "ACT-01", "tipo": "tarea", "carril": "Técnico", "nombre": "Revisar"},
                    {"id": "EV-02", "tipo": "temporizador", "carril": "Técnico", "nombre": "Cinco días", "temporizador": "P5D",
                     "interrumpe": True},
                    {"id": "ACT-02", "tipo": "sistema", "carril": "Aplicación", "nombre": "Reclamar"},
                    {"id": "EV-03", "tipo": "temporizador", "carril": "Aplicación", "nombre": "Diez días"},
                    {"id": "EV-04", "tipo": "fin", "carril": "Técnico", "nombre": "Revisada"},
                    {"id": "EV-05", "tipo": "fin", "carril": "Aplicación", "nombre": "Reclamada"},
                    {"id": "EV-06", "tipo": "fin", "carril": "Aplicación", "nombre": "Vencida"}],
          "flujos": [{"de": "EV-01", "a": "ACT-01"}, {"de": "ACT-01", "a": "EV-04"},
                     {"de": "ACT-01", "a": "EV-02", "discontinuo": True}, {"de": "EV-02", "a": "ACT-02"},
                     {"de": "ACT-02", "a": "EV-05"}, {"de": "ACT-02", "a": "EV-03", "discontinuo": True},
                     {"de": "EV-03", "a": "EV-06"}]}


def interrumpe(tmp):
    """T8: «"interrumpe": true» en un temporizador unido a su tarea va y vuelve: crear lo dibuja con el borde de un evento
    que interrumpe (continuo) y el que no, con el de uno que no (discontinuo); leer lo devuelve; el BPMN lleva
    cancelActivity; actualizar lo pone y lo quita (colocación automática y a mano) y cambia el borde; comparar ve que
    se quita en draw.io; validar avisa si va en otro tipo."""
    import drawio_modelo as dm
    sin = entorno(sin_navegador=True)
    origen = tmp / "plazos.json"
    origen.write_text(json.dumps(PLAZOS, ensure_ascii=False), encoding="utf-8")
    d = tmp / "plazos" / "plazos.drawio"
    run("crear", origen, "-o", d, esperado=2, env=sin)

    def estado():
        leido = json.loads(run("leer", d).split("\naviso")[0])
        paso = {p["id"]: p for p in leido["pasos"]}
        _, c = celdas(d)
        borde = {i: dm._estilo((c[i] if c[i].tag == "mxCell" else c[i].find("mxCell")).get("style")).get("outline")
                 for i in ("EV-02", "EV-03")}
        return paso, borde, leido
    paso, borde, leido = estado()
    check(paso["EV-02"].get("interrumpe") is True and "interrumpe" not in paso["EV-03"] and dm.comparar(PLAZOS, leido) == []
          and borde == {"EV-02": "boundInt", "EV-03": "boundNonint"},
          f"interrumpe: crear y leer lo conservan (true, no «True») y el borde es el de interrumpir o no ({borde})")
    run("bpmn", d)
    pr = ET.parse(d.with_suffix(".bpmn")).getroot().find("bpmn:process", NS_BPMN)
    cancela = {e.get("id"): e.get("cancelActivity") for e in pr.findall("bpmn:boundaryEvent", NS_BPMN)}
    check(cancela == {"EV-02": "true", "EV-03": "false"}, f"interrumpe: cancelActivity en el BPMN ({cancela})")
    cambio = tmp / "plazos" / "cambio.json"
    for modo in ("automática", "a mano"):
        if modo == "a mano":     # se mueve un paso en draw.io y se acepta: la colocación pasa a ser a mano
            t = ET.parse(d)
            g = next(e for e in t.getroot().iter("mxCell") if e.get("id") == "ACT-02").find("mxGeometry")
            g.set("y", str(float(g.get("y")) + 10))
            t.write(d, encoding="utf-8")
            run("comparar", d, "--aceptar", esperado=2, env=sin)
        uno, otro = ("EV-03", "EV-02") if modo == "automática" else ("EV-02", "EV-03")
        cambio.write_text(json.dumps({"cambios": [{"poner": {"id": uno, "interrumpe": True}},
                                                  {"poner": {"id": otro, "interrumpe": False}}]}), encoding="utf-8")
        out = run("actualizar", d, cambio, esperado=2, env=sin)
        paso, borde, _ = estado()
        bien = (paso[uno].get("interrumpe") is True and "interrumpe" not in paso[otro]
                and borde == {uno: "boundInt", otro: "boundNonint"} and run("comparar", d, env=sin).startswith("Sin cambios")
                and f"{uno}: pasa a interrumpir su tarea" in out and f"{otro}: deja de interrumpir su tarea" in out)
        check(bien, f"interrumpe: actualizar (colocación {modo}) lo pone y lo quita, lo dice y cambia el borde ({borde})"
              + ("" if bien else "\n" + out))
    t = ET.parse(d)                       # en draw.io, «Editar datos»: se borra el dato
    next(e for e in t.getroot().iter("object") if e.get("id") == "EV-02").attrib.pop("interrumpe")
    t.write(d, encoding="utf-8")
    check("EV-02: deja de interrumpir su tarea" in run("comparar", d, esperado=1, env=sin),
          "interrumpe: comparar ve que se ha quitado en draw.io")
    run("comparar", d, "--aceptar", esperado=2, env=sin)
    paso, borde, _ = estado()
    check("interrumpe" not in paso["EV-02"] and borde["EV-02"] == "boundNonint",
          f"interrumpe: comparar --aceptar cambia el borde del que se ha quitado en draw.io ({borde})")
    cambio.write_text(json.dumps({"cambios": [{"flujo": {"de": "ACT-01", "a": "EV-02", "discontinuo": False}}]}), encoding="utf-8")
    out = run("actualizar", d, cambio, esperado=2, env=sin)
    paso, borde, _ = estado()
    check(borde["EV-02"] == "catching" and "se ha respetado la colocación" in out,
          f"interrumpe: un temporizador que deja de ir en el borde de su tarea (colocación a mano) vuelve a su borde ({borde})")
    malo = json.loads(json.dumps(PLAZOS))
    malo["pasos"][1]["interrumpe"] = True
    (tmp / "plazos-malo.json").write_text(json.dumps(malo, ensure_ascii=False), encoding="utf-8")
    check("ACT-01: interrumpe solo se usa en un temporizador" in run("validar", tmp / "plazos-malo.json"),
          "interrumpe: validar avisa si va en un paso que no es un temporizador")


def avisos(tmp):
    """T7: un aviso a un perfil del proceso no se dibuja (SKILL.md lo dice) y uno a un sistema externo es un flujo de
    mensaje desde la tarea, que no añade capa: un proceso de 9 tareas con dos avisos al registro mide lo mismo que sin
    ellos."""
    sin = entorno(sin_navegador=True)
    nombres = ["Registrar solicitud", "Revisar solicitud", "Pedir informe", "Emitir informe", "Valorar informe",
               "Resolver", "Generar autorización", "Registrar salida", "Cerrar expediente"]
    carril = ["Solicitante", "Técnico", "Técnico", "Aplicación", "Técnico", "Técnico", "Aplicación", "Aplicación", "Técnico"]

    def proceso(regla):
        pasos = [{"id": "EV-01", "tipo": "inicio", "carril": "Solicitante", "nombre": "Necesidad"}]
        pasos += [{"id": f"ACT-{i:02d}", "tipo": "tarea", "carril": c, "nombre": n} for i, (n, c) in enumerate(zip(nombres, carril), 1)]
        cadena = ["EV-01"] + [f"ACT-{i:02d}" for i in range(1, 10)]
        flujos, externos = [], []
        if regla == "con avisos":     # los dos avisos al registro, flujos de mensaje desde la tarea
            externos = ["Registro de entrada"]
            flujos = [{"de": "ACT-04", "a": externos[0], "etiqueta": "Aviso de informe"},
                      {"de": "ACT-08", "a": externos[0], "etiqueta": "Aviso de salida"}]
        pasos.append({"id": "EV-02", "tipo": "fin", "carril": "Técnico", "nombre": "Expediente cerrado"})
        cadena.append("EV-02")
        flujos += [{"de": a, "a": b} for a, b in zip(cadena, cadena[1:])]
        return {"proceso": "Avisos", "carriles": ["Solicitante", "Técnico", "Aplicación"], "pasos": pasos, "flujos": flujos,
                **({"externos": externos} if externos else {})}
    ancho = {}
    for regla in ("sin avisos", "con avisos"):
        origen = tmp / f"avisos {regla}.json"
        origen.write_text(json.dumps(proceso(regla), ensure_ascii=False), encoding="utf-8")
        run("crear", origen, "-o", tmp / "avisos", esperado=2, env=sin)
        ancho[regla] = paginas(tmp / "avisos" / f"avisos {regla}.drawio")[0][1]
    check(ancho["con avisos"] == ancho["sin avisos"],
          "avisos: los avisos a un sistema externo, flujos de mensaje desde la tarea, no añaden capa "
          f"({', '.join(f'{k}: {v:.0f} px' for k, v in ancho.items())})")
    skill = (SCRIPTS.parent / "SKILL.md").read_text(encoding="utf-8")
    check("un aviso a un perfil del proceso no se dibuja" in skill.lower() and "en el carril «Aplicación»" not in skill,
          "avisos: SKILL.md dice que un aviso a un perfil no se dibuja y ya no pide un mensaje en el carril «Aplicación»")


def cambios_temporales(tmp):
    """T17: SKILL.md dice que el fichero de cambios de actualizar es temporal, va fuera de <p> y no se guarda, en la orden
    y donde explica cómo se cambia un proceso."""
    skill = (SCRIPTS.parent / "SKILL.md").read_text(encoding="utf-8")
    orden = next((l for l in skill.splitlines() if "diagrama.py actualizar X.drawio cambios.json" in l), "")
    cambiar = skill.split("## Cambiar un proceso")[-1].split("```")[0]
    check("temporal, fuera de <p>" in orden and "temporal" in cambiar and "fuera de `<p>`" in cambiar and "no se guarda" in cambiar,
          "actualizar: SKILL.md dice que el fichero de cambios es temporal, va fuera de <p> y no se guarda")


def error_suelto(tmp):
    """Un evento de error que no va en el borde de una tarea y no tiene salidas se exporta como un fin de error (endEvent
    con errorEventDefinition): BPMN 2.0 no admite un evento intermedio que capture un error."""
    suelto = json.loads((AQUI / "datos" / "semantico.json").read_text(encoding="utf-8"))
    suelto["pasos"] = [p for p in suelto["pasos"] if p["id"] != "EV-04"]
    suelto["flujos"] = [{k: v for k, v in f.items() if k != "discontinuo"} for f in suelto["flujos"] if f["a"] != "EV-04"]
    (tmp / "error suelto.json").write_text(json.dumps(suelto, ensure_ascii=False), encoding="utf-8")
    d = tmp / "error suelto" / "error.drawio"
    out = run("crear", tmp / "error suelto.json", "-o", d, esperado=2, env=entorno(sin_navegador=True))
    check("EV-02" not in out, "validar: un error suelto y sin salidas es un fin: no avisa de él" + ("" if "EV-02" not in out
                                                                                                   else "\n" + out))
    run("bpmn", d)
    pr = ET.parse(d.with_suffix(".bpmn")).getroot().find("bpmn:process", NS_BPMN)
    fin = pr.find("bpmn:endEvent[@id='EV-02']", NS_BPMN)
    check(fin is not None and fin.find("bpmn:errorEventDefinition", NS_BPMN) is not None
          and pr.find("bpmn:intermediateCatchEvent[@id='EV-02']", NS_BPMN) is None and not bpmn_valido(d.with_suffix(".bpmn")),
          "bpmn: un error suelto y sin salidas es un fin de error (endEvent con errorEventDefinition)")
    # el dibujo dice lo mismo que el BPMN: el error suelto, con el borde de un fin (y se lee como error); un mensaje en el
    # borde de su tarea, que no la interrumpe, con borde discontinuo
    import drawio_modelo as dm
    suelto["pasos"].append({"id": "EV-05", "tipo": "mensaje", "carril": "Revisores", "nombre": "Recordatorio"})
    suelto["pasos"].append({"id": "EV-06", "tipo": "fin", "carril": "Revisores", "nombre": "Recordado"})
    suelto["flujos"] += [{"de": "ACT-01", "a": "EV-05", "discontinuo": True}, {"de": "EV-05", "a": "EV-06"}]
    (tmp / "error suelto.json").write_text(json.dumps(suelto, ensure_ascii=False), encoding="utf-8")
    d = tmp / "error suelto 2" / "error.drawio"
    run("crear", tmp / "error suelto.json", "-o", d, esperado=2, env=entorno(sin_navegador=True))
    _, c = celdas(d)
    borde = {i: dm._estilo((c[i] if c[i].tag == "mxCell" else c[i].find("mxCell")).get("style")).get("outline")
             for i in ("EV-02", "EV-05")}
    run("bpmn", d)
    pr = ET.parse(d.with_suffix(".bpmn")).getroot().find("bpmn:process", NS_BPMN)
    mensaje = pr.find("bpmn:boundaryEvent[@id='EV-05']", NS_BPMN)
    check(borde == {"EV-02": "end", "EV-05": "boundNonint"} and dm.comparar(suelto, dm.leer(str(d))[0]) == []
          and mensaje is not None and mensaje.get("cancelActivity") == "false",
          f"error suelto con el borde de un fin y mensaje en el borde, discontinuo como en el BPMN ({borde})")


_JS_MEDIR_NOTAS = """async (xml) => {
  const div = document.getElementById('out');
  const graph = new Graph(div); graph.setEnabled(false);
  const node = mxUtils.parseXml(xml).documentElement;
  new mxCodec(node.ownerDocument).decode(node, graph.getModel());
  await new Promise(r => setTimeout(r, 400));
  const o = div.getBoundingClientRect(), res = [];
  for (const c of Object.values(graph.getModel().cells)) {
    if (!/(^|;)nota=1(;|$)/.test(c.style || '')) continue;
    const s = graph.view.getState(c);
    const caja = [o.left + s.x, o.top + s.y, s.width, s.height];
    let letras = [Infinity, Infinity, -Infinity, -Infinity];
    const w = document.createTreeWalker(s.text.node, NodeFilter.SHOW_TEXT);
    while (w.nextNode()) {
      const r = document.createRange(); r.selectNodeContents(w.currentNode);
      for (const q of r.getClientRects())
        letras = [Math.min(letras[0], q.left), Math.min(letras[1], q.top), Math.max(letras[2], q.right), Math.max(letras[3], q.bottom)];
    }
    // por dónde pasa el trazo: el centro de cada lado de la caja
    const lados = {arriba: 0, abajo: 0, izquierda: 0, derecha: 0};
    const centro = {arriba: [caja[0] + caja[2] / 2, caja[1]], abajo: [caja[0] + caja[2] / 2, caja[1] + caja[3]],
                    izquierda: [caja[0], caja[1] + caja[3] / 2], derecha: [caja[0] + caja[2], caja[1] + caja[3] / 2]};
    for (const el of s.shape.node.querySelectorAll('path')) {
      const st = el.getAttribute('stroke');
      if (!st || st === 'none' || st === 'transparent' || el.getAttribute('visibility') === 'hidden') continue;
      const m = el.getScreenCTM(), largo = el.getTotalLength();
      for (let k = 0; k <= largo; k += 1) {
        const p = el.getPointAtLength(k).matrixTransform(m);
        for (const l in centro) if (Math.abs(p.x - centro[l][0]) < 3 && Math.abs(p.y - centro[l][1]) < 3) lados[l]++;
      }
    }
    res.push({texto: String(c.value), caja, letras, lados});
  }
  return res;
}"""


def medir_notas(drawio):
    """Caja de cada nota, lo que ocupa su texto y por qué lados pasa su trazo, pintado con el visor de draw.io."""
    import drawio_modelo as dm, navegador
    sp = navegador._playwright()
    with sp() as p:
        b, pg = navegador._pagina(p)
        pg.add_script_tag(content=navegador.VIEWER_JS.read_text(encoding="utf-8"))
        res = pg.evaluate(_JS_MEDIR_NOTAS, dm.Fichero(str(drawio)).xml_modelo())
        navegador.cerrar(b)
    return res


def nota_larga(tmp):
    """Una nota de texto largo, con una palabra muy larga (el nombre de una regla), cabe entera en su caja, también en
    el último paso y al añadirla con actualizar; y se dibuja como anotación BPMN, un corchete abierto a la derecha,
    no como una caja a la que le falta un lado."""
    proc = {"proceso": "Nota larga", "carriles": ["Revisor", "Aplicación"],
            "pasos": [{"id": "EV-01", "tipo": "inicio", "carril": "Revisor", "nombre": "Solicitud recibida"},
                      {"id": "ACT-01", "tipo": "tarea", "carril": "Revisor", "nombre": "Revisar solicitud"},
                      {"id": "ACT-02", "tipo": "sistema", "carril": "Aplicación", "nombre": "Guardar"},
                      {"id": "EV-02", "tipo": "fin", "carril": "Aplicación", "nombre": "Fin"}],
            "flujos": [{"de": "EV-01", "a": "ACT-01"}, {"de": "ACT-01", "a": "ACT-02"}, {"de": "ACT-02", "a": "EV-02"}],
            "notas": [{"paso": "ACT-01", "texto": "Pendiente de confirmar con el cliente si la revisión la hace siempre el "
                                                  "mismo técnico o cualquiera del grupo, y qué pasa si vence el plazo"},
                      {"paso": "EV-02", "texto": "Lo decide MNT_ER_ObtenerTecnicoResponsableDelExpediente con el grupo de "
                                                 "la zona; si no devuelve a nadie, el proceso se queda parado"}]}
    (tmp / "nota.json").write_text(json.dumps(proc, ensure_ascii=False), encoding="utf-8")
    d = tmp / "nota" / "nota.drawio"
    run("crear", tmp / "nota.json", "-o", d)
    check(solapes(d) == [], "notas: una nota larga no pisa a otra forma " + "; ".join(solapes(d)))
    # a mano: se mueve una forma y se añade otra nota larga, en el primer paso, con actualizar
    t = ET.parse(d)
    g = next(e for e in t.getroot().iter("mxCell") if e.get("id") == "ACT-02").find("mxGeometry")
    g.set("y", str(float(g.get("y")) + 10))
    t.write(d, encoding="utf-8")
    run("comparar", d, "--aceptar")
    (tmp / "n1.json").write_text(json.dumps({"cambios": [{"nota": {"paso": "EV-01", "texto":
        "Llega desde pv!solicitud.estadoDelExpedienteAdministrativo"}}]}, ensure_ascii=False), encoding="utf-8")
    run("actualizar", d, tmp / "n1.json")
    import drawio_modelo as dm
    _, geo, _ = dm.leer(str(d))
    izquierda = min(x for _, _, x, _, _ in geo["carriles"].values()) + dm.CABECERA
    derecha = max(x + w for _, _, x, w, _ in geo["carriles"].values())
    check(all(izquierda <= cx - w / 2 and cx + w / 2 <= derecha for cx, _, w, _ in geo["anotaciones"]),
          "notas: una nota ancha añadida a mano queda dentro de los carriles, sin pisar su cabecera")
    medidas = medir_notas(d)
    fuera = [m["texto"][:30] for m in medidas
             if m["letras"][0] < m["caja"][0] - 1 or m["letras"][1] < m["caja"][1] - 1
             or m["letras"][2] > m["caja"][0] + m["caja"][2] + 1 or m["letras"][3] > m["caja"][1] + m["caja"][3] + 1]
    check(len(medidas) == 3 and not fuera, "notas: el texto largo cabe en su caja " + "; ".join(fuera))
    abiertas = [m for m in medidas if m["lados"]["izquierda"] and not (m["lados"]["arriba"] or m["lados"]["abajo"] or m["lados"]["derecha"])]
    check(len(abiertas) == 3, "notas: se dibujan como un corchete (sin los lados de arriba, abajo y derecha de punta a punta)")


def caja_etiqueta(geo, paso, nombre):
    """La caja de la etiqueta de un evento o una puerta (la misma que mira solapes), o None si no tiene."""
    import colocacion as co
    cx, cy, w, h = geo["pasos"][paso]
    lado = geo["etiquetas"].get(paso)
    if not lado or not nombre:
        return None
    lh = co.alto_texto(nombre) - 6
    return (cx - co.ANCHO_ETIQUETA / 2 + 4, cy - h / 2 - lh if lado == "arriba" else cy + h / 2, co.ANCHO_ETIQUETA - 8, lh)


def lineas_de_notas(drawio):
    """[(paso, caja de la nota, (punto en la nota, punto en el paso))] de cada nota unida a su paso: la línea de puntos
    según los exitX/exitY y entryX/entryY de su estilo, sobre las cajas de la nota y del paso."""
    import drawio_modelo as dm
    f = dm.Fichero(str(drawio))
    proc, geo, _ = f.leer()
    caja = dict(zip(geo["ids_nota"], geo["anotaciones"]))
    out = []
    for el, cell in f.celdas():
        if cell.get("edge") != "1" or "asociacion=1" not in (cell.get("style") or ""):
            continue
        st = dm._estilo(cell.get("style"))
        nota, paso = cell.get("source"), cell.get("target")
        (nx, ny, nw, nh), (px, py, pw, ph) = caja[nota], geo["pasos"][paso]
        x0, y0, x1, y1 = nx - nw / 2, ny - nh / 2, px - pw / 2, py - ph / 2
        out.append((paso, (x0, y0, nw, nh), ((x0 + nw * float(st["exitX"]), y0 + nh * float(st["exitY"])),
                                              (x1 + pw * float(st["entryX"]), y1 + ph * float(st["entryY"])))))
    return proc, geo, out


def nota_y_etiqueta(tmp, env=None):
    """La línea de la nota de una puerta no cruza su etiqueta: con la etiqueta encima y «No» saliendo por abajo, la nota
    va debajo, corrida hacia donde no va «No»; si no queda ningún lado, va al lado de la etiqueta."""
    import colocacion as co, drawio_modelo as dm
    d = tmp / "puerta con nota" / "puerta.drawio"
    run("crear", AQUI / "datos" / "puerta-nota.json", "-o", d, esperado=2 if env else 0, env=env)
    proc, geo, lineas = lineas_de_notas(d)
    nombre = {p["id"]: p["nombre"] for p in proc["pasos"]}
    mal = [f"la línea de la nota de {paso} cruza su etiqueta" for paso, _, (p, q) in lineas
           if (e := caja_etiqueta(geo, paso, nombre[paso])) and _cruza(p, q, e)]
    for fl, pts in zip(proc["flujos"], geo["flujos"]):     # y ningún flujo de la puerta cruza la nota
        camino = _camino(geo["pasos"][fl["de"]][:2], geo["pasos"][fl["de"]][2:], pts, geo["pasos"][fl["a"]][:2],
                         geo["pasos"][fl["a"]][2:])
        mal += [f"{fl['de']} → {fl['a']} cruza la nota de {paso}" for paso, n, _ in lineas
                if any(_cruza(p, q, n) for p, q in zip(camino, camino[1:]))]
    check(len(lineas) == 1 and not mal and not solapes(d),
          "notas: la línea de la nota de una puerta no cruza su etiqueta ni la cruza un flujo " + "; ".join(mal + solapes(d)))
    # sin ningún lado libre (flujos por arriba y por abajo, hacia los dos lados): la nota va al lado de la etiqueta
    p = {"pasos": [{"id": "GW-01", "tipo": "exclusiva", "nombre": "¿Completa?"}], "notas": [{"paso": "GW-01", "texto": "x"}]}
    lados = {"GW-01": "arriba"}
    sitio = co.lados_nota(p, {"GW-01": {"arriba": {1, -1}, "abajo": {1, -1}}}, lados)
    g = co.colocar_notas(p, {"pasos": {"GW-01": (500, 300)}, "etiquetas": lados}, sitio, {"exclusiva": (50, 50)})
    x, y, w, h = g["anotaciones"][0]
    st = {k: float(v) for k, v in dm._estilo(dm.entrada_asociacion("arriba", (x, w), (475, 50))).items() if k != "_base"}
    linea = ((x + w * st["exitX"], y + h * st["exitY"]), (475 + 50 * st["entryX"], 275 + 50 * st["entryY"]))
    e = caja_etiqueta({"pasos": {"GW-01": (500, 300, 50, 50)}, "etiquetas": lados}, "GW-01", "¿Completa?")
    check(not _cruza(*linea, e) and (x + w < e[0] or x > e[0] + e[2]),
          f"notas: sin ningún lado libre, la nota va al lado de la etiqueta y su línea no la cruza ({sitio})")


def nota_a_mano(tmp):
    """Una nota que se añade con actualizar a una puerta con la etiqueta encima, en un diagrama colocado a mano, no pisa
    la etiqueta ni otra forma, y su línea no la cruza."""
    sin = entorno(sin_navegador=True)
    mal = []
    for nombre, paso in (("pedido", "GW-02"), ("tres-puertas", "GW-03")):
        d = tmp / nombre / f"{nombre}.drawio"
        run("crear", AQUI / "datos" / f"{nombre}.json", "-o", d, esperado=2, env=sin)
        t = ET.parse(d)                     # se mueve un paso a mano y se acepta: la colocación pasa a ser a mano
        g = next(e for e in t.getroot().iter("mxCell") if e.get("id") == "EV-01").find("mxGeometry")
        g.set("y", str(float(g.get("y")) + 10))
        t.write(d, encoding="utf-8")
        run("comparar", d, "--aceptar", esperado=2, env=sin)
        cambio = tmp / nombre / "nota.json"
        cambio.write_text(json.dumps({"cambios": [{"nota": {"paso": paso, "texto": "Confirmar con el cliente si esta "
                                                                                   "pregunta sigue haciendo falta"}}]},
                                     ensure_ascii=False), encoding="utf-8")
        out = run("actualizar", d, cambio, esperado=2, env=sin)
        proc, geo, lineas = lineas_de_notas(d)
        nombres = {p["id"]: p["nombre"] for p in proc["pasos"]}
        mal += [f"{nombre}: {s}" for s in solapes(d)]
        mal += [f"{nombre}: la línea de la nota de {p} cruza su etiqueta" for p, _, (a, b) in lineas
                if (e := caja_etiqueta(geo, p, nombres[p])) and _cruza(a, b, e)]
        if "se ha respetado la colocación" not in out:
            mal.append(f"{nombre}: actualizar no respetó la colocación a mano\n{out}")
    check(not mal, "notas: una nota añadida a mano a una puerta con la etiqueta encima no la pisa ni la cruza "
          + "; ".join(mal))


def provisional(tmp):
    """Si falla la relectura de comprobación de actualizar, no queda X.drawio.tmp y el .drawio sigue como estaba."""
    import argparse, diagrama, drawio_modelo as dm
    sin = entorno(sin_navegador=True)
    d = tmp / "provisional" / "semántico.drawio"
    run("crear", AQUI / "datos" / "semantico.json", "-o", d, esperado=2, env=sin)
    cambios = tmp / "provisional" / "cambio.json"
    cambios.write_text(json.dumps({"cambios": [{"poner": {"id": "ACT-02", "nombre": "Guardar todo"}}]}), encoding="utf-8")
    antes, leer, simulado = d.read_bytes(), dm.leer, os.environ.get("DIAGRAMAS_SIN_NAVEGADOR")

    def falla(ruta):
        raise dm.ErrorProceso(f"relectura simulada de {ruta}")
    dm.leer, os.environ["DIAGRAMAS_SIN_NAVEGADOR"] = falla, "1"
    try:
        diagrama.actualizar(argparse.Namespace(drawio=str(d), cambios=str(cambios), forzar=False, recolocar=False))
    except dm.ErrorProceso:
        pass
    finally:
        dm.leer = leer
        if simulado is None:
            del os.environ["DIAGRAMAS_SIN_NAVEGADOR"]
    sobra = [p.name for p in d.parent.iterdir() if p.name.endswith(".tmp")]
    check(not sobra and d.read_bytes() == antes, "actualizar: si falla la relectura, no deja el .drawio.tmp ni toca el "
          ".drawio " + ", ".join(sobra))


def solapes(drawio):
    """Pares de cosas que se pisan en el dibujo: formas, etiquetas de eventos y puertas, y notas."""
    import drawio_modelo as dm, colocacion as co
    proc, geo, _ = dm.leer(str(drawio))
    cajas = []
    for p in proc["pasos"]:
        cx, cy, w, h = geo["pasos"][p["id"]]
        cajas.append((p["id"], (cx - w / 2, cy - h / 2, w, h)))
        lado = geo["etiquetas"].get(p["id"])
        if lado and p["nombre"]:
            lh = co.alto_texto(p["nombre"]) - 6
            cajas.append((p["id"], (cx - co.ANCHO_ETIQUETA / 2 + 4, cy - h / 2 - lh if lado == "arriba" else cy + h / 2, co.ANCHO_ETIQUETA - 8, lh)))
    for n, (cx, cy, w, h) in zip(proc.get("notas") or [], geo["anotaciones"]):
        cajas.append(("nota " + n["paso"], (cx - w / 2, cy - h / 2, w, h)))
    out = []
    for i, (a, (ax, ay, aw, ah)) in enumerate(cajas):
        for b, (bx, by, bw, bh) in cajas[i + 1:]:
            if a != b and ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah:
                out.append(f"{a} / {b}")
    return out


# ---------------------------------------------------------------- conexiones falsas
ANCHO_LETRA_FLUJO = 6    # la etiqueta de un flujo (11 px): unos 5 px por letra; 6, por exceso, y 4 de margen
HOLGURA = 6              # un flujo que pasa a menos de esto de un paso parece que sale o entra de él


def _camino(a, ta, pts, b, tb):
    """El trazado de un flujo como lo dibuja draw.io con sus puntos: del borde del origen (por el lado hacia el primer
    punto), por los puntos, al borde del destino. `a` y `b`, centros; `ta` y `tb`, (ancho, alto)."""
    def borde(c, tam, hacia):
        (cx, cy), (w, h) = c, tam
        if abs(hacia[1] - cy) <= 1:
            return (cx + (w / 2 if hacia[0] > cx else -w / 2), cy)
        if abs(hacia[0] - cx) <= 1:
            return (cx, cy + (h / 2 if hacia[1] > cy else -h / 2))
        return c
    camino = [tuple(a)] + [tuple(p) for p in pts] + [tuple(b)]
    camino[0], camino[-1] = borde(a, ta, camino[1]), borde(b, tb, camino[-2])
    return camino


def _punto_a(camino, t):
    """El punto a la fracción t (0 a 1) del largo del camino."""
    largos = [abs(q[0] - p[0]) + abs(q[1] - p[1]) for p, q in zip(camino, camino[1:])]
    falta = t * sum(largos)
    for (p, q), largo in zip(zip(camino, camino[1:]), largos):
        if falta <= largo and largo:
            return (p[0] + (q[0] - p[0]) * falta / largo, p[1] + (q[1] - p[1]) * falta / largo)
        falta -= largo
    return camino[-1]


def _cruza(p, q, caja):
    """Si el segmento p-q entra en el interior de la caja (x, y, w, h)."""
    x0, y0, x1, y1 = caja[0], caja[1], caja[0] + caja[2], caja[1] + caja[3]
    t0, t1 = 0.0, 1.0
    dx, dy = q[0] - p[0], q[1] - p[1]
    for d, desde, lo, hi in ((dx, p[0], x0, x1), (dy, p[1], y0, y1)):
        if abs(d) < 1e-9:
            if not lo < desde < hi:
                return False
            continue
        a, b = (lo - desde) / d, (hi - desde) / d
        t0, t1 = max(t0, min(a, b)), min(t1, max(a, b))
    return t1 - t0 > 1e-6


def conexiones_falsas(drawio):
    """Lo que hace parecer que un flujo sale o entra de donde no, página a página y sobre la geometría del .drawio: un
    tramo de un flujo que pasa por encima de un paso que no es el suyo o de su etiqueta (o a menos de HOLGURA del paso),
    o por encima de la etiqueta de otro flujo; y dos flujos que no comparten origen ni destino con tramos en la misma
    recta que se solapan (los que salen de un mismo paso o llegan a uno pueden compartir el tramo de salida o de
    llegada). Los flujos de mensaje van en vertical hasta su participante y no se miran."""
    import drawio_modelo as dm, colocacion as co
    f = dm.Fichero(str(drawio))
    out = []
    for k, (hoja, modelo) in enumerate(f.hojas, 1):
        proc, geo, _ = f._leer_hoja(hoja, modelo.find("root"))
        pagina = f"tramo {k}: " if len(f.hojas) > 1 else ""
        nombre = {p["id"]: p["nombre"] for p in proc["pasos"]}
        cajas = {}
        for p in proc["pasos"]:
            cx, cy, w, h = geo["pasos"][p["id"]]
            cajas[p["id"]] = [(cx - w / 2 - HOLGURA, cy - h / 2 - HOLGURA, w + 2 * HOLGURA, h + 2 * HOLGURA)]
            lado = geo["etiquetas"].get(p["id"])
            if lado and p["nombre"]:
                lh = co.alto_texto(p["nombre"]) - 6
                cajas[p["id"]].append((cx - co.ANCHO_ETIQUETA / 2 + 4, cy - h / 2 - lh if lado == "arriba" else cy + h / 2,
                                       co.ANCHO_ETIQUETA - 8, lh))
        caminos, etiquetas = [], []
        for fl, pts in zip(proc["flujos"], geo["flujos"]):
            if fl["de"] not in geo["pasos"] or fl["a"] not in geo["pasos"]:
                continue
            (ax, ay, aw, ah), (bx, by, bw, bh) = geo["pasos"][fl["de"]], geo["pasos"][fl["a"]]
            camino = _camino((ax, ay), (aw, ah), pts, (bx, by), (bw, bh))
            caminos.append((fl, camino))
            if fl.get("etiqueta"):
                g = f.por_id(fl["id"])[1].find("mxGeometry")
                cx, cy = _punto_a(camino, (float(g.get("x", 0)) + 1) / 2)
                ancho = len(fl["etiqueta"]) * ANCHO_LETRA_FLUJO + 4
                etiquetas.append((fl, (cx - ancho / 2, cy - 7, ancho, 14)))
        texto = lambda fl: f"{fl['de']} → {fl['a']}"   # noqa: E731
        for fl, camino in caminos:
            segmentos = list(zip(camino, camino[1:]))
            for pid, lista in cajas.items():
                if pid not in (fl["de"], fl["a"]) and any(_cruza(p, q, c) for p, q in segmentos for c in lista):
                    out.append(f"{pagina}{texto(fl)} pasa por {pid} («{nombre[pid]}»)")
            for otro, caja in etiquetas:
                if otro is not fl and any(_cruza(p, q, caja) for p, q in segmentos):
                    out.append(f"{pagina}{texto(fl)} pasa por la etiqueta «{otro['etiqueta']}» de {texto(otro)}")
        for i, (f1, c1) in enumerate(caminos):
            for f2, c2 in caminos[i + 1:]:
                if f1["de"] == f2["de"] or f1["a"] == f2["a"]:
                    continue
                for p1, q1 in zip(c1, c1[1:]):
                    for p2, q2 in zip(c2, c2[1:]):
                        for eje in (0, 1):   # 0: tramos verticales (misma x); 1: horizontales (misma y)
                            if not (abs(p1[eje] - q1[eje]) <= 1 and abs(p2[eje] - q2[eje]) <= 1 and abs(p1[eje] - p2[eje]) <= 1):
                                continue
                            o = 1 - eje
                            solape = min(max(p1[o], q1[o]), max(p2[o], q2[o])) - max(min(p1[o], q1[o]), min(p2[o], q2[o]))
                            if solape > 1:
                                out.append(f"{pagina}{texto(f1)} y {texto(f2)} van juntos {solape:.0f} px")
    return sorted(set(out))


FLECHA = 8              # la punta de la flecha de un flujo (6 px) y algo de aire: la etiqueta no llega hasta aquí
MARCA_DEFECTO = 14      # la marca del flujo por defecto (10 px desde el origen) y algo de aire


def holgura(tmp):
    """Colocación por capas: la etiqueta de un flujo no llega a la flecha ni a la marca del flujo por defecto, y un paso
    con una sola entrada va en la fila de su paso anterior cuando este solo sale hacia él (sin verticales largas)."""
    import drawio_modelo as dm, colocacion as co
    sin = entorno(sin_navegador=True)
    mal = []
    for nombre in ("semantico", "tres-puertas", "pedido", "solicitud", "puerta-nota"):
        d = tmp / "holgura" / f"{nombre}.drawio"
        run("crear", AQUI / "datos" / f"{nombre}.json", "-o", d, esperado=2, env=sin)
        f = dm.Fichero(str(d))
        proc, geo, _ = f.leer()
        for fl, pts in zip(proc["flujos"], geo["flujos"]):
            if not fl.get("etiqueta") or fl["de"] not in geo["pasos"] or fl["a"] not in geo["pasos"]:
                continue
            (ax, ay, aw, ah), (bx, by, bw, bh) = geo["pasos"][fl["de"]], geo["pasos"][fl["a"]]
            camino = _camino((ax, ay), (aw, ah), pts, (bx, by), (bw, bh))
            total = sum(abs(q[0] - p[0]) + abs(q[1] - p[1]) for p, q in zip(camino, camino[1:]))
            centro = (float(f.por_id(fl["id"])[1].find("mxGeometry").get("x", 0)) + 1) / 2 * total
            mitad = (len(fl["etiqueta"]) * ANCHO_LETRA_FLUJO + 4) / 2
            if total - centro - mitad < FLECHA:
                mal.append(f"{nombre}: «{fl['etiqueta']}» ({fl['de']} → {fl['a']}) a {total - centro - mitad:.0f} px de la flecha")
            if fl.get("defecto") and centro - mitad < MARCA_DEFECTO:
                mal.append(f"{nombre}: «{fl['etiqueta']}» ({fl['de']} → {fl['a']}) pisa la marca del flujo por defecto")
        capa, atras = co.capas(proc)
        carril = {p["id"]: p["carril"] for p in proc["pasos"]}
        salen = [fl for fl in proc["flujos"] if fl["de"] in carril and fl["a"] in carril]
        for i, fl in enumerate(salen):
            if (proc["flujos"].index(fl) not in atras and carril[fl["de"]] == carril[fl["a"]]
                    and capa[fl["a"]] == capa[fl["de"]] + 1 and sum(g["de"] == fl["de"] for g in salen) == 1
                    and sum(g["a"] == fl["a"] for g in salen) == 1 and abs(geo["pasos"][fl["de"]][1] - geo["pasos"][fl["a"]][1]) > 1):
                mal.append(f"{nombre}: {fl['de']} → {fl['a']} no va en línea recta (su único paso anterior está en otra fila)")
    check(not mal, "por capas: las etiquetas no llegan a la flecha ni a la marca del flujo por defecto y un paso con una "
          "sola entrada va en la fila del anterior " + "; ".join(mal))


def conexiones(tmp):
    """La colocación por capas no dibuja conexiones falsas (conexiones_falsas): con tres puertas seguidas que se apilan
    en una columna, la salida de una que tapa otro paso va por el hueco entre columnas, no pegada a la puerta."""
    sin = entorno(sin_navegador=True)
    d = tmp / "Carpeta con espacios" / "tres puertas" / "tres.drawio"
    run("crear", AQUI / "datos" / "tres-puertas.json", "-o", d, esperado=2, env=sin)
    mal = conexiones_falsas(d)
    check(not mal and not solapes(d), "por capas: tres puertas seguidas, sin conexiones falsas ni nada que se pise ("
          + f"{len(mal)}) " + "; ".join(mal[:6] + solapes(d)))


# ---------------------------------------------------------------- Tarea 12: sin navegador y procesos grandes
def bpmn_valido(ruta):
    """Lo que necesitan Camunda Modeler y bpmn.io para abrir y dibujar un BPMN 2.0: ids únicos, referencias que
    existen, cada nodo en un carril, incoming y outgoing iguales a los flujos, un BPMNShape por nodo y carril y un
    BPMNEdge con dos o más puntos por flujo. Devuelve los problemas (vacío si es válido)."""
    ns = NS_BPMN
    b = ET.parse(ruta).getroot()
    mal = []
    todos = [e.get("id") for e in b.iter() if e.get("id")]
    mal += [f"id repetido: {i}" for i in sorted({i for i in todos if todos.count(i) > 1})]
    pr = b.find("bpmn:process", ns)
    nodos = {e.get("id"): e for e in pr if e.tag.split("}")[1] not in ("laneSet", "sequenceFlow", "textAnnotation",
                                                                         "association", "documentation")}
    flujos = pr.findall("bpmn:sequenceFlow", ns)
    for e in b.iter():
        for k in ("sourceRef", "targetRef", "attachedToRef", "default", "processRef", "bpmnElement"):
            if e.get(k) and e.get(k) not in todos:
                mal.append(f"{e.get('id')}: {k}={e.get(k)} no existe")
    for f in flujos:
        if f.get("sourceRef") not in nodos or f.get("targetRef") not in nodos:
            mal.append(f"{f.get('id')}: no une dos nodos del proceso")
    for nid, n in nodos.items():
        for lado, ref in (("incoming", "targetRef"), ("outgoing", "sourceRef")):
            if {x.text for x in n.findall(f"bpmn:{lado}", ns)} != {f.get("id") for f in flujos if f.get(ref) == nid}:
                mal.append(f"{nid}: {lado} no coincide con los flujos")
    refs = [r.text for r in pr.iter(f"{{{ns['bpmn']}}}flowNodeRef")]
    carriles = [e.get("id") for e in pr.iter(f"{{{ns['bpmn']}}}lane")]
    if carriles:
        mal += [f"{nid}: está en {refs.count(nid)} carriles" for nid in nodos if refs.count(nid) != 1]
    formas = [e.get("bpmnElement") for e in b.iter(f"{{{ns['bpmndi']}}}BPMNShape")]
    mal += [f"{i}: {formas.count(i)} BPMNShape" for i in list(nodos) + carriles if formas.count(i) != 1]
    puntos = {e.get("bpmnElement"): len(e.findall("di:waypoint", ns)) for e in b.iter(f"{{{ns['bpmndi']}}}BPMNEdge")}
    mal += [f"{f.get('id')}: sin trazado" for f in flujos if puntos.get(f.get("id"), 0) < 2]
    return mal


def paginas(drawio):
    """Las páginas del .drawio: [(nombre, ancho, {id de celda: estilo})]. El ancho, hasta donde llega lo que cuelga
    de la capa de la página (carriles y participantes externos)."""
    out = []
    for dg in ET.parse(drawio).getroot().findall("diagram"):
        celdas = {el.get("id"): (el if el.tag == "mxCell" else el.find("mxCell")) for el in dg.find("mxGraphModel/root")}
        raiz = {i for i, c in celdas.items() if not c.get("parent")}
        capa = {i for i, c in celdas.items() if c.get("parent") in raiz}
        ancho = max([float(c.find("mxGeometry").get("x", 0)) + float(c.find("mxGeometry").get("width", 0))
                     for c in celdas.values() if c.get("vertex") == "1" and c.get("parent") in capa] or [0])
        out.append((dg.get("name"), ancho, {i: c.get("style") or "" for i, c in celdas.items()}))
    return out


def nombres_de_tramos(drawio, proceso):
    """El nombre que tiene que tener cada página de un proceso en tramos, con los pasos que lleva ahora:
    «<proceso> (tramo N de M: <el de más a la izquierda> – <el de más a la derecha>)»."""
    import drawio_modelo as dm
    f = dm.Fichero(str(drawio))
    out = []
    for k, (hoja, modelo) in enumerate(f.hojas, 1):
        proc, geo, _ = f._leer_hoja(hoja, modelo.find("root"))
        pasos = sorted((p for p in proc["pasos"] if not p["id"].startswith("ENL-")), key=lambda p: geo["pasos"][p["id"]][0])
        out.append(f"{proceso} (tramo {k} de {len(f.hojas)}: {pasos[0]['nombre'] or pasos[0]['id']} – "
                   f"{pasos[-1]['nombre'] or pasos[-1]['id']})")
    return out


def ancho_png(ruta):
    return unpack(">I", pathlib.Path(ruta).read_bytes()[16:20])[0]


def sin_navegador(tmp):
    """Sin navegador (DIAGRAMAS_SIN_NAVEGADOR=1 simula que no hay): crear escribe el .drawio y el .json con la
    colocación de reserva, sin pasos que se pisen, dice «sin PNG» y sale con 2; bpmn da un BPMN válido; actualizar
    aplica el cambio y también sale con 2 solo por la imagen; png y mermaid.py dicen qué falta."""
    import drawio_modelo as dm
    tmp.mkdir(parents=True)
    sin = entorno(sin_navegador=True)
    origen = AQUI / "datos" / "semantico.json"
    base = json.loads(origen.read_text(encoding="utf-8"))
    d = tmp / "Carpeta con espacios" / "sin navegador" / "semántico.drawio"
    out = run("crear", origen, "-o", d, esperado=2, env=sin)
    check(d.exists() and d.with_suffix(".json").exists() and not d.with_suffix(".png").exists() and "sin PNG" in out,
          "sin navegador: crear escribe el .drawio y el .json, dice «sin PNG» y sale con 2")
    proc, geo, _ = dm.leer(str(d))
    izquierda = {p["id"]: geo["pasos"][p["id"]][0] for p in proc["pasos"]}
    check(dm.comparar(base, proc) == [] and solapes(d) == [] and izquierda["EV-01"] < izquierda["ACT-01"]
          < izquierda["GW-01"] < izquierda["ACT-02"] < izquierda["EV-03"],
          "sin navegador: el proceso entero, de izquierda a derecha y sin nada que se pise " + "; ".join(solapes(d)))
    check(not conexiones_falsas(d), "sin navegador: sin conexiones falsas " + "; ".join(conexiones_falsas(d)))
    dentro = [p["id"] for p in proc["pasos"] if not (geo["carriles"][p["carril"]][0] <= geo["pasos"][p["id"]][1]
                                                     <= sum(geo["carriles"][p["carril"]][:2]))]
    check(not dentro, "sin navegador: cada paso dentro de su carril " + ", ".join(dentro))
    run("bpmn", d, env=sin)
    mal = bpmn_valido(d.with_suffix(".bpmn"))
    check(not mal, "sin navegador: bpmn da un BPMN 2.0 válido " + "; ".join(mal[:5]))
    out = run("png", d, esperado=2, env=sin)
    check("sin PNG" in out and not d.with_suffix(".png").exists(), "sin navegador: png sale con 2 y dice «sin PNG»")
    (tmp / "sn1.json").write_text(json.dumps({"cambios": [
        {"poner": {"id": "ACT-03", "tipo": "script", "carril": "Aplicación", "nombre": "Calcular plazo", "nodo": "8"}},
        {"quitar_flujo": {"de": "ACT-02", "a": "EV-03"}}, {"flujo": {"de": "ACT-02", "a": "ACT-03"}},
        {"flujo": {"de": "ACT-03", "a": "EV-03"}}]}, ensure_ascii=False), encoding="utf-8")
    out = run("actualizar", d, tmp / "sn1.json", esperado=2, env=sin)
    check("sin PNG" in out and run("comparar", d, env=sin).startswith("Sin cambios") and solapes(d) == [],
          "sin navegador: actualizar aplica el cambio, sin nada que se pise, y sale con 2 solo por la imagen")
    # el ejemplo con participante externo, notas y etiquetas a los dos lados
    p = tmp / "sin navegador" / "pedido.drawio"
    run("crear", PEDIDO, "-o", p, esperado=2, env=sin)
    check(dm.comparar(json.loads(PEDIDO.read_text(encoding="utf-8")), dm.leer(str(p))[0]) == [] and solapes(p) == [],
          "sin navegador: pedido, con externo y notas, sin nada que se pise " + "; ".join(solapes(p)))
    check(not conexiones_falsas(p), "sin navegador: pedido, sin conexiones falsas " + "; ".join(conexiones_falsas(p)))
    (tmp / "no-hace-falta.mmd").write_text("flowchart TD\n  A --> B\n", encoding="utf-8")
    r = subprocess.run([sys.executable, str(SCRIPTS / "mermaid.py"), "--check", str(tmp / "no-hace-falta.mmd")],
                       capture_output=True, text=True, encoding="utf-8", env=sin)
    check(r.returncode == 2 and "DIAGRAMAS_SIN_NAVEGADOR" in r.stdout + r.stderr,
          "sin navegador: mermaid.py sale con 2 y dice por qué")
    for orden in (["no-existe/*.mmd"], ["--md", "no-existe/*.md"]):   # 2 es «falta un requisito», no esto
        r = subprocess.run([sys.executable, str(SCRIPTS / "mermaid.py"), *orden], capture_output=True, text=True,
                           encoding="utf-8", env=sin, cwd=str(tmp))
        check(r.returncode == 1 and f"No encuentro: {orden[-1]}" in r.stdout + r.stderr,
              f"mermaid.py {' '.join(orden)}: un comodín sin coincidencias sale con 1 y dice qué patrón no encuentra "
              f"(sale con {r.returncode}: {(r.stdout + r.stderr).strip()[-120:]})")
    r = subprocess.run([sys.executable, str(SCRIPTS / "mermaid.py")], capture_output=True, text=True, encoding="utf-8", env=sin)
    bien = r.returncode == 1 and ".mmd" in r.stderr and not r.stdout
    check(bien, "mermaid.py sin argumentos sale con 1 (2 es «falta un requisito») y dice qué falta en stderr"
          + ("" if bien else f" (sale con {r.returncode}: {(r.stdout + r.stderr).strip()[-120:]})"))


def png_viejo(tmp):
    """Un diagrama creado con navegador que se cambia sin él: actualizar y comparar --aceptar quitan sus PNG, que ya
    no son del dibujo (también uno de cuando iba en tramos), y lo dicen; el de otro diagrama no se toca."""
    sin = entorno(sin_navegador=True)
    carpeta = tmp / "Carpeta con espacios" / "png viejo"
    d = carpeta / "semántico.drawio"
    run("crear", AQUI / "datos" / "semantico.json", "-o", d)
    (carpeta / "semántico-3.png").write_bytes(b"de cuando iba en tramos")
    (carpeta / "semántico-9.drawio").write_text("<mxfile/>", encoding="utf-8")
    (carpeta / "semántico-9.png").write_bytes(b"de otro diagrama")
    (tmp / "pv1.json").write_text(json.dumps({"cambios": [{"poner": {"id": "ACT-02", "nombre": "Guardar la decisión"}}]},
                                             ensure_ascii=False), encoding="utf-8")
    out = run("actualizar", d, tmp / "pv1.json", esperado=2, env=sin)
    quedan = sorted(p.name for p in carpeta.glob("*.png"))
    check(quedan == ["semántico-9.png"] and "semántico.png" in out and "semántico-3.png" in out
          and "versión anterior" in out and "semántico-9.png" not in out,
          "sin navegador: actualizar quita los PNG del diagrama, que ya no son del dibujo, y lo dice "
          + ", ".join(quedan) + ("" if "versión anterior" in out else "\n" + out))
    run("png", d)
    t = ET.parse(d)
    el = next(e for e in t.getroot().iter() if e.get("id") == "ACT-02")
    g = (el if el.tag == "mxCell" else el.find("mxCell")).find("mxGeometry")
    g.set("y", str(float(g.get("y")) + 10))
    t.write(d, encoding="utf-8")
    out = run("comparar", d, "--aceptar", esperado=2, env=sin)
    quedan = sorted(p.name for p in carpeta.glob("*.png"))
    check(quedan == ["semántico-9.png"] and "semántico.png" in out and "versión anterior" in out,
          "sin navegador: comparar --aceptar quita el PNG del diagrama y lo dice " + ", ".join(quedan)
          + ("" if "versión anterior" in out else "\n" + out))


def proceso_grande():
    """Un proceso de una aplicación que ya existe y no cabe en una página (53 pasos): carriles, decisiones con
    condición que cruzan de un tramo a otro, una vuelta atrás, un plazo en el borde de una tarea, un participante
    externo, una nota y datos de Appian. «tramos»: se dibuja en tramos de una página, sin inventar subprocesos."""
    T, S, A = "Técnicos", "Supervisores", "Aplicación"
    pasos, flujos, cuenta = [], [], {"EV": 0, "ACT": 0, "GW": 0}

    def paso(tipo, carril, nombre, **kw):
        pre = {"inicio": "EV", "fin": "EV", "mensaje": "EV", "temporizador": "EV", "exclusiva": "GW"}.get(tipo, "ACT")
        cuenta[pre] += 1
        pasos.append({"id": f"{pre}-{cuenta[pre]:02d}", "tipo": tipo, "carril": carril, "nombre": nombre,
                      "nodo": str(len(pasos) + 1), **kw})
        return pasos[-1]["id"]

    def une(*ids):
        flujos.extend({"de": a, "a": b} for a, b in zip(ids, ids[1:]))

    inicio, registrar = paso("inicio", T, "Orden recibida"), paso("tarea", T, "Registrar orden")
    guardar, urgente = paso("sistema", A, "Guardar orden"), paso("exclusiva", A, "¿Urgente?")
    atender, asignar = paso("tarea", S, "Atender urgencia"), paso("tarea", S, "Asignar técnico")
    ejecutar = paso("tarea", T, "Ejecutar trabajo")
    plazo, vencido = paso("temporizador", T, "Diez días", temporizador="P10D"), paso("fin", T, "Plazo vencido")
    une(inicio, registrar, guardar, urgente)
    flujos += [{"de": urgente, "a": atender, "etiqueta": "Sí", "condicion": 'pv!prioridad = "Urgente"'},
               {"de": urgente, "a": asignar, "etiqueta": "No", "defecto": True},
               {"de": ejecutar, "a": plazo, "discontinuo": True}]
    une(atender, ejecutar)
    une(asignar, ejecutar)
    une(plazo, vencido)
    previo = ejecutar
    for i in range(1, 9):   # hitos repetidos, como en una aplicación mal hecha
        preparar, guarda = paso("script", A, f"Preparar hito {i}"), paso("sistema", A, f"Guardar hito {i}")
        avisar, aviso = paso("exclusiva", A, f"¿Avisar del hito {i}?"), paso("mensaje", A, f"Aviso del hito {i}")
        cierre = paso("script", A, f"Cerrar hito {i}")
        une(previo, preparar, guarda, avisar)
        flujos += [{"de": avisar, "a": aviso, "etiqueta": "Sí", "condicion": "pv!avisar"},
                   {"de": avisar, "a": cierre, "etiqueta": "No", "defecto": True}]
        une(aviso, cierre)
        previo = cierre
    validar, validado = paso("tarea", S, "Validar cierre"), paso("exclusiva", S, "¿Cierre validado?")
    cerrar, fin = paso("sistema", A, "Cerrar orden"), paso("fin", A, "Orden cerrada")
    une(previo, validar, validado)
    flujos += [{"de": validado, "a": cerrar, "etiqueta": "Validado", "condicion": 'pv!decision = "VALIDAR"'},
               {"de": validado, "a": ejecutar, "etiqueta": "Rechazado", "defecto": True},      # vuelve atrás
               {"de": guardar, "a": "ERP", "etiqueta": "Alta de la orden"}]
    une(cerrar, fin)
    return {"proceso": "Gestión de orden", "carriles": [T, S, A], "pasos": pasos, "flujos": flujos, "externos": ["ERP"],
            "notas": [{"paso": cerrar, "texto": "Sin validar el cierre, la orden queda abierta"}], "tramos": True}


def tramos(tmp, con_png=True):
    """Un proceso que no cabe en una página, con «tramos»: una página del .drawio por tramo, cada una de 1.600 px de
    ancho como mucho, con un PNG por tramo; los cortes, con un evento de enlace en cada lado; leer devuelve el
    proceso entero; un solo .bpmn válido con todos los pasos y sin los enlaces; comparar ve lo cambiado a mano en
    cualquier tramo; actualizar coloca de nuevo los tramos y, si se colocaron a mano, se niega sin --recolocar. Nada
    fuera de la carpeta de salida."""
    import drawio_modelo as dm
    con_imagen = 0 if con_png else 2
    temporales = tmp / "temporales del sistema"
    temporales.mkdir(parents=True)
    env = entorno(sin_navegador=not con_png, temporales=temporales)
    proc = proceso_grande()
    codigo = {p["nombre"]: p["id"] for p in proc["pasos"]}
    origen = tmp / "grande.json"
    origen.write_text(json.dumps(proc, ensure_ascii=False), encoding="utf-8")
    d = tmp / "Carpeta con espacios" / "grande" / "gestión.drawio"
    salida = run("crear", origen, "-o", d, esperado=con_imagen, env=env)
    pags = paginas(d)
    nombres_ok = all(re.fullmatch(rf"Gestión de orden \(tramo {k} de {len(pags)}: .+ – .+\)", n) for k, (n, _, _) in enumerate(pags, 1))
    check(len(pags) > 2 and nombres_ok and all(a <= ANCHO_PAGINA for _, a, _ in pags),
          f"tramos: una página por tramo, de {ANCHO_PAGINA} px de ancho como mucho ({len(pags)} tramos: "
          + ", ".join(f"{a:.0f}" for _, a, _ in pags) + " px)")
    if con_png:
        pngs = sorted(d.parent.glob("gestión-*.png"), key=lambda p: int(p.stem.rsplit("-", 1)[1]))
        check(len(pngs) == len(pags) and not d.with_suffix(".png").exists()
              and all(ancho_png(p) <= ANCHO_PNG for p in pngs),
              f"tramos: un PNG por tramo (gestión-1.png…), de {ANCHO_PNG} px como mucho ("
              + ", ".join(str(ancho_png(p)) for p in pngs) + ")")
    leido = dm.leer(str(d))[0]
    check(dm.comparar(proc, leido) == [] and leido.get("tramos") is True and solapes(d) == [],
          "tramos: leer devuelve el proceso entero, con la etiqueta, la condición y el flujo por defecto de los que "
          "cruzan de un tramo a otro " + "; ".join(t for _, t in dm.comparar(proc, leido)) + "; ".join(solapes(d)))
    mal = conexiones_falsas(d)
    check(not mal, f"tramos: sin conexiones falsas ({len(mal)}) " + "; ".join(mal[:6]))
    # cada flujo que cruza de un tramo a otro: un enlace que sale en el suyo, con el número del otro, y uno que entra
    pagina_de = {cid: k for k, (_, _, estilos) in enumerate(pags, 1) for cid in estilos}
    t = ET.parse(d).getroot()
    aristas = {(c.get("source"), c.get("target")) for c in t.iter("mxCell") if c.get("edge") == "1"}
    texto = {(c.get("id") or ""): (c.get("value") or c.get("label") or "") for c in t.iter() if c.tag in ("mxCell", "object")}
    for o in t.iter("object"):
        texto[o.get("id")] = o.get("label") or ""
    mal = []
    cruzan = [f for f in proc["flujos"] if f["a"] not in proc["externos"] and pagina_de[f["de"]] != pagina_de[f["a"]]]
    for f in cruzan:
        sale = next((a for s, a in aristas if s == f["de"] and a and re.fullmatch(r"ENL-\d+-S", a)
                     and (a[:-1] + "E", f["a"]) in aristas), None)
        if sale is None or pagina_de.get(sale) != pagina_de[f["de"]] or pagina_de.get(sale[:-1] + "E") != pagina_de[f["a"]] \
                or f"tramo {pagina_de[f['a']]}" not in texto.get(sale, ""):
            mal.append(f"{f['de']} → {f['a']}")
    enlaces = [cid for cid in pagina_de if re.fullmatch(r"ENL-\d+-[SE]", cid)]
    vuelta = next(f for f in proc["flujos"] if f.get("etiqueta") == "Rechazado")
    check(cruzan and not mal and len(enlaces) == 2 * len(cruzan)
          and pagina_de[codigo["Diez días"]] == pagina_de[codigo["Ejecutar trabajo"]]
          and pagina_de[vuelta["de"]] > pagina_de[vuelta["a"]]
          and all("enlace=1" in pags[pagina_de[e] - 1][2][e] and "symbol=link" in pags[pagina_de[e] - 1][2][e] for e in enlaces),
          f"tramos: {len(cruzan)} flujos cruzan de un tramo a otro, cada uno con un enlace que sale (con el número del "
          "otro tramo) y uno que entra; también la vuelta atrás; el plazo, en el tramo de su tarea " + ", ".join(mal))
    # qué pasos lleva cada tramo: una línea por tramo en lo que dice crear, y lo mismo en el nombre de su página
    lineas = re.findall(r"^\s*tramo (\d+): (.+) – (.+) \((\d+) pasos?\)$", salida, re.M)
    suyos = {k: {p["id"] for p in proc["pasos"] if pagina_de[p["id"]] == k} for k in range(1, len(pags) + 1)}
    mal = [f"tramo {n}" for n, primero, ultimo, cuantos in lineas
           if int(cuantos) != len(suyos[int(n)]) or codigo.get(primero) not in suyos[int(n)]
           or codigo.get(ultimo) not in suyos[int(n)]
           or pags[int(n) - 1][0] != f"Gestión de orden (tramo {n} de {len(pags)}: {primero} – {ultimo})"]
    check([int(n) for n, *_ in lineas] == list(range(1, len(pags) + 1)) and not mal
          and sum(int(c) for *_, c in lineas) == len(proc["pasos"])
          and dm.NOMBRE_TRAMO.match("Gestión de orden (tramo 2 de 8)").group(1) == "Gestión de orden",
          "tramos: crear dice qué pasos lleva cada tramo («tramo N: <primero> – <último> (K pasos)»), entre todos "
          "cubren el proceso y la página se llama igual " + ", ".join(mal) + ("" if lineas else "\n" + salida))
    run("bpmn", d, env=env)
    b = ET.parse(d.with_suffix(".bpmn")).getroot()
    nodos = [e for e in b.find("bpmn:process", NS_BPMN) if e.tag.split("}")[1] not in
             ("laneSet", "sequenceFlow", "textAnnotation", "association")]
    mal = bpmn_valido(d.with_suffix(".bpmn"))
    si = [e for e in b.iter(f"{{{NS_BPMN['bpmn']}}}sequenceFlow") if e.get("name") == "Sí"]
    check(not mal and len(nodos) == len(proc["pasos"]) and "linkEventDefinition" not in d.with_suffix(".bpmn").read_text(encoding="utf-8")
          and len(b.findall(f"{{{NS_BPMN['bpmndi']}}}BPMNDiagram")) == 1
          and len(si) == 9 and all(e.find("bpmn:conditionExpression", NS_BPMN) is not None for e in si),
          f"tramos: un solo .bpmn válido con los {len(proc['pasos'])} pasos ({len(nodos)}), sin los enlaces y con las "
          "condiciones " + "; ".join(mal[:5]))
    # actualizar con la colocación automática: los tramos se colocan de nuevo
    cerrar, fin = codigo["Cerrar orden"], codigo["Orden cerrada"]
    (tmp / "t1.json").write_text(json.dumps({"cambios": [
        {"poner": {"id": "ACT-99", "tipo": "script", "carril": "Aplicación", "nombre": "Calcular coste", "nodo": "99"}},
        {"quitar_flujo": {"de": cerrar, "a": fin}}, {"flujo": {"de": cerrar, "a": "ACT-99"}},
        {"flujo": {"de": "ACT-99", "a": fin}}]}, ensure_ascii=False), encoding="utf-8")
    salida = run("actualizar", d, tmp / "t1.json", esperado=con_imagen, env=env)
    pags = paginas(d)
    lineas = re.findall(r"^\s*tramo (\d+): (.+) – (.+) \((\d+) pasos?\)$", salida, re.M)
    check(run("comparar", d, env=env).startswith("Sin cambios") and len(pags) > 2 and all(a <= ANCHO_PAGINA for _, a, _ in pags)
          and len(lineas) == len(pags) and sum(int(c) for *_, c in lineas) == len(proc["pasos"]) + 1,
          "tramos: actualizar coloca de nuevo los tramos, dice qué pasos lleva cada uno y el dibujo queda igual que el "
          "análisis")
    mal = conexiones_falsas(d)
    check(not mal, f"tramos: actualizar, sin conexiones falsas ({len(mal)}) " + "; ".join(mal[:6]))
    # en draw.io se renombra el primer paso de un tramo que no es el primero y se mueve: comparar lo ve
    f2 = dm.Fichero(str(d))
    _, geo2, _ = f2._leer_hoja(f2.hojas[1][0], f2.hojas[1][1].find("root"))
    primero = min((pid for pid in geo2["pasos"] if not pid.startswith("ENL-")), key=lambda pid: geo2["pasos"][pid][0])
    t = ET.parse(d)
    pagina2 = t.getroot().findall("diagram")[1]
    celda = next(c for c in pagina2.iter() if c.tag in ("mxCell", "object") and c.get("id") == primero)
    viejo = celda.get("label") if celda.tag == "object" else celda.get("value")
    celda.set("label" if celda.tag == "object" else "value", "Revisar de nuevo")
    g = (celda.find("mxCell") if celda.tag == "object" else celda).find("mxGeometry")
    g.set("y", str(float(g.get("y")) + 10))
    t.write(d, encoding="utf-8")
    out = run("comparar", d, esperado=1, env=env)
    check(f"{celda.get('id')} renombrado: «{viejo}» → «Revisar de nuevo»" in out, "tramos: comparar ve un cambio a mano en el tramo 2")
    run("comparar", d, "--aceptar", esperado=con_imagen, env=env)
    js = json.loads(d.with_suffix(".json").read_text(encoding="utf-8"))
    check(js.get("tramos") is True and js["colocacion"]["modo"] == "manual", "tramos: comparar --aceptar conserva «tramos»")
    nombres = [n for n, _, _ in paginas(d)]
    check(len(nombres) > 1 and nombres[1].startswith("Gestión de orden (tramo 2 de ") and ": Revisar de nuevo – " in nombres[1]
          and nombres == nombres_de_tramos(d, "Gestión de orden"),
          "tramos: comparar --aceptar cambia el nombre de la página del tramo de un paso renombrado a mano " + nombres[1])
    (tmp / "t2.json").write_text(json.dumps({"cambios": [{"poner": {"id": "ACT-99", "nombre": "Calcular el coste"}}]},
                                            ensure_ascii=False), encoding="utf-8")
    out = run("actualizar", d, tmp / "t2.json", esperado=1, env=env)
    check("tramos" in out and "--recolocar" in out and "Calcular el coste" not in d.read_text(encoding="utf-8"),
          "tramos: actualizar se niega a encajar cambios en tramos colocados a mano y dice cómo seguir")
    run("actualizar", d, tmp / "t2.json", "--recolocar", esperado=con_imagen, env=env)
    check("Calcular el coste" in d.read_text(encoding="utf-8") and run("comparar", d, env=env).startswith("Sin cambios")
          and len(paginas(d)) > 2, "tramos: actualizar --recolocar coloca de nuevo los tramos")
    sobra = [p.name for p in temporales.iterdir()]
    check(not sobra, "tramos: nada fuera de la carpeta de salida, ni temporales " + ", ".join(sobra))
    # un proceso con «tramos» que cabe en una página: una sola página, con su nombre, y X.png
    pequeno = dict(json.loads((AQUI / "datos" / "semantico.json").read_text(encoding="utf-8")), tramos=True)
    (tmp / "pequeño.json").write_text(json.dumps(pequeno, ensure_ascii=False), encoding="utf-8")
    run("crear", tmp / "pequeño.json", "-o", tmp / "pequeño", esperado=con_imagen, env=env)
    pags = paginas(tmp / "pequeño" / "pequeño.drawio")
    check(len(pags) == 1 and pags[0][0] == "Proceso de prueba" and (not con_png or (tmp / "pequeño" / "pequeño.png").exists()),
          "tramos: un proceso que cabe en una página no se parte")
    # crece hasta no caber: actualizar lo pasa a tramos y quita el PNG de una sola página (el de otro diagrama, no)
    (tmp / "pequeño" / "pequeño-99.drawio").write_text("<mxfile/>", encoding="utf-8")
    (tmp / "pequeño" / "pequeño-99.png").write_bytes(b"de otro diagrama")
    run("actualizar", tmp / "pequeño" / "pequeño.drawio", origen, esperado=con_imagen, env=env)
    hechos = sorted(p.name for p in (tmp / "pequeño").glob("*.png"))
    check(len(paginas(tmp / "pequeño" / "pequeño.drawio")) > 2 and run("comparar", tmp / "pequeño" / "pequeño.drawio",
                                                                       env=env).startswith("Sin cambios")
          and (not con_png or ("pequeño.png" not in hechos and "pequeño-1.png" in hechos))
          and (tmp / "pequeño" / "pequeño-99.png").read_bytes() == b"de otro diagrama",
          "tramos: un proceso que deja de caber pasa a tramos y se quita su PNG de una página (no el de otro diagrama) "
          + ", ".join(hechos))


def g3(tmp):
    """Lo de la 0.7.0-beta.2 (G3) que no necesita navegador: la nota y la etiqueta de su puerta, el .drawio.tmp, el error
    suelto, la holgura de las etiquetas y las filas por capas, el temporizador que interrumpe, los avisos y el fichero de
    cambios temporal."""
    for nombre, prueba in (("nota", lambda t: nota_y_etiqueta(t, entorno(sin_navegador=True))), ("nota a mano", nota_a_mano),
                           ("provisional", provisional),
                           ("error suelto", error_suelto), ("holgura", holgura), ("interrumpe", interrumpe),
                           ("avisos", avisos), ("cambios", cambios_temporales)):
        (tmp / nombre).mkdir(parents=True)
        prueba(tmp / nombre)


def main_sin_navegador():
    """Con DIAGRAMAS_SIN_NAVEGADOR=1, lo que se puede hacer sin navegador: dibujar el .drawio (también en tramos),
    leerlo, compararlo, exportar el BPMN y validar."""
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="diagramas-sin-navegador-"))
    try:
        sin_navegador(tmp / "sin")
        conexiones(tmp / "conexiones")
        tramos(tmp / "tramos", con_png=False)
        g3(tmp)
        malo = {"proceso": "x", "carriles": ["A"], "pasos": [{"id": "ACT-01", "tipo": "tareas", "carril": "B", "nombre": "x"}],
                "flujos": [{"de": "ACT-01", "a": "ACT-02"}]}
        (tmp / "malo.json").write_text(json.dumps(malo), encoding="utf-8")
        out = run("validar", tmp / "malo.json", esperado=1)
        check("desconocido" in out and "no está en «carriles»" in out and "no existe el paso ACT-02" in out,
              "validar: tipo, carril y flujo incorrectos")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if fallos:
        print("\n" + "\n\n".join(fallos))
        sys.exit(1)
    print("\nTodo correcto (sin navegador: sin PNG ni pintor Mermaid).")


def main():
    for s in (sys.stdout, sys.stderr):
        s.reconfigure(encoding="utf-8", errors="replace")
    sys.path.insert(0, str(SCRIPTS))
    if SIN_NAVEGADOR:
        return main_sin_navegador()
    probar_mermaid()
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="diagramas-"))
    try:
        # Tarea 12: sin navegador y procesos que no caben en una página
        sin_navegador(tmp / "sin")
        conexiones(tmp / "conexiones")
        png_viejo(tmp / "png viejo")
        tramos(tmp / "tramos")
        tramos(tmp / "tramos sin navegador", con_png=False)
        g3(tmp / "g3")
        nota_y_etiqueta(tmp / "nota con el motor")
        d = tmp / "solicitud.drawio"
        # 1. crear
        run("validar", EJEMPLO)
        run("crear", EJEMPLO, "-o", tmp)
        check(d.exists() and (tmp / "solicitud.png").stat().st_size > 20000 and (tmp / "solicitud.json").exists(),
              "crear: .drawio, .png y .json")
        sidecar = json.loads((tmp / "solicitud.json").read_text(encoding="utf-8"))
        check(sidecar.get("colocacion", {}).get("modo") == "automatica", "crear: colocación automática con huella")
        leido = json.loads(run("leer", d).split("\naviso")[0])
        base = json.loads(EJEMPLO.read_text(encoding="utf-8"))
        sys.path.insert(0, str(SCRIPTS)); import drawio_modelo as dm
        check(dm.comparar(base, leido) == [], "leer: el .drawio devuelve el mismo proceso")
        run("crear", EJEMPLO, "-o", tmp, esperado=1)
        # 2. actualizar con colocación automática
        (tmp / "c1.json").write_text(json.dumps({"cambios": [
            {"poner": {"id": "ACT-09", "tipo": "tarea", "carril": "Técnico de la unidad gestora", "nombre": "Pedir aclaraciones"}},
            {"quitar_flujo": {"de": "ACT-04", "a": "GW-03"}}, {"flujo": {"de": "ACT-04", "a": "ACT-09"}},
            {"flujo": {"de": "ACT-09", "a": "GW-03"}}, {"poner": {"id": "ACT-06", "carril": "Técnico de la unidad gestora"}},
            {"quitar": "EV-04"}, {"flujo": {"de": "ACT-07", "a": "EV-05"}},
            {"flujo": {"de": "GW-04", "a": "EV-03", "etiqueta": "No favorable"}},
            {"carril": "Registro"},
            {"poner": {"id": "ACT-10", "tipo": "manual", "carril": "Registro", "nombre": "Archivar en papel"}},
            {"flujo": {"de": "ACT-10", "a": "EV-03"}}, {"quitar_flujo": {"de": "GW-04", "a": "EV-03"}},
            {"flujo": {"de": "GW-04", "a": "ACT-10", "etiqueta": "No favorable"}}]}), encoding="utf-8")
        out = run("actualizar", d, tmp / "c1.json")
        check("carril nuevo: «Registro»" in out and "paso quitado: EV-04" in out, "actualizar: informa de los cambios")
        check(run("comparar", d).startswith("Sin cambios"), "actualizar: el dibujo queda igual que el análisis")
        # 3. edición a mano en draw.io, guardada comprimida
        root, c = celdas(d)
        g = c["ACT-03"].find("mxGeometry"); x_movido = float(g.get("x")) + 60; g.set("x", str(x_movido))
        c["ACT-02"].set("value", "Revisar <b>la</b> documentación<br>aportada")
        carril = next(e for e in root if e.get("value") == "Técnico de la unidad gestora").get("id")
        n = ET.SubElement(root, "mxCell", {"id": "zZ1-2", "value": "Comprobar tasas", "vertex": "1", "parent": carril,
                                           "style": "shape=mxgraph.bpmn.task;taskMarker=abstract;html=1;"})
        ET.SubElement(n, "mxGeometry", {"x": "900", "y": "40", "width": "120", "height": "80", "as": "geometry"})
        r = ET.SubElement(root, "mxCell", {"id": "zZ1-3", "value": "¿Hay tasas?", "vertex": "1", "parent": carril,
                                           "style": "rhombus;whiteSpace=wrap;html=1;"})
        ET.SubElement(r, "mxGeometry", {"x": "1100", "y": "20", "width": "80", "height": "80", "as": "geometry"})
        for i, (s_, t_) in enumerate([("ACT-01", "zZ1-2"), ("zZ1-2", "ACT-02"), ("zZ1-2", "zZ1-3"), ("zZ1-3", "ACT-02")]):
            e = ET.SubElement(root, "mxCell", {"id": f"zZ1-{5 + i}" if i < 2 else f"zZ1-{20 + i}", "value": "", "edge": "1", "parent": "1", "source": s_,
                                               "target": t_, "style": "edgeStyle=orthogonalEdgeStyle;"})
            ET.SubElement(e, "mxGeometry", {"relative": "1", "as": "geometry"})
        et = ET.SubElement(root, "mxCell", {"id": "zZ1-9", "value": "si hay tasas", "vertex": "1", "parent": "zZ1-5", "style": "edgeLabel;"})
        ET.SubElement(et, "mxGeometry", {"relative": "1", "as": "geometry"})
        nota = ET.SubElement(root, "mxCell", {"id": "zZ1-8", "value": "Duda del cliente", "vertex": "1", "parent": "1", "style": "text;html=1;"})
        ET.SubElement(nota, "mxGeometry", {"x": "60", "y": "5", "width": "120", "height": "20", "as": "geometry"})
        full = ET.parse(d); full.getroot().find("diagram").remove(full.getroot().find("diagram/mxGraphModel"))
        modelo = ET.Element("mxGraphModel"); modelo.append(root)
        raw = urllib.parse.quote(ET.tostring(modelo, encoding="unicode"), safe="")
        co = zlib.compressobj(9, zlib.DEFLATED, -15)
        full.getroot().find("diagram").text = base64.b64encode(co.compress(raw.encode()) + co.flush()).decode()
        full.write(d, encoding="utf-8")
        run("actualizar", d, tmp / "c1.json", esperado=1)
        check(True, "actualizar: se niega mientras haya cambios a mano sin aceptar")
        out = run("comparar", d, esperado=1)
        check("código asignado: ACT-11" in out and "código asignado: GW-05" in out and "«Revisar la documentación aportada»" in out
              and "flujo nuevo: ACT-01 → ACT-11 «si hay tasas»" in out and "nota en el dibujo (sale en el PNG): «Duda del cliente»" in out,
              "comparar: códigos para lo añadido, etiquetas HTML limpias, notas listadas, fichero comprimido")
        _, c = celdas(d)
        check("mxgraph.bpmn.gateway2" in c["GW-05"].get("style", ""), "comparar: un rombo de draw.io pasa a puerta BPMN")
        run("comparar", d, "--aceptar")
        sidecar = json.loads((tmp / "solicitud.json").read_text(encoding="utf-8"))
        check(sidecar["colocacion"]["modo"] == "manual", "comparar --aceptar: la colocación pasa a manual")
        # 4. actualizar respetando lo movido a mano
        (tmp / "c2.json").write_text(json.dumps({"cambios": [
            {"poner": {"id": "ACT-12", "tipo": "sistema", "carril": "Aplicación", "nombre": "Calcular tasa"}},
            {"quitar_flujo": {"de": "ACT-11", "a": "ACT-02"}}, {"flujo": {"de": "ACT-11", "a": "ACT-12"}},
            {"flujo": {"de": "ACT-12", "a": "ACT-02"}}, {"poner": {"id": "ACT-08", "tipo": "tarea"}}]}), encoding="utf-8")
        out = run("actualizar", d, tmp / "c2.json")
        _, c = celdas(d)
        check("se ha respetado la colocación" in out, "actualizar: modo manual")
        x_ahora = float(c["ACT-03"].find("mxGeometry").get("x"))
        check(x_ahora in (x_movido, x_movido + dm.COLUMNA), "actualizar (manual): lo movido a mano sigue donde se dejó")
        check(run("comparar", d).startswith("Sin cambios"), "actualizar (manual): el dibujo queda igual que el análisis")
        check("Duda del cliente" in (d.read_text(encoding="utf-8")), "actualizar (manual): conserva las notas del analista")
        # 5. BPMN 2.0
        run("bpmn", d)
        b = ET.parse(tmp / "solicitud.bpmn").getroot()
        ns = {"bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL", "bpmndi": "http://www.omg.org/spec/BPMN/20100524/DI"}
        nodos = [e.get("id") for e in b.find("bpmn:process", ns) if e.tag.split("}")[1] not in ("laneSet", "sequenceFlow")]
        formas = {e.get("bpmnElement") for e in b.iter(f"{{{ns['bpmndi']}}}BPMNShape")}
        aristas = {e.get("bpmnElement"): len(list(e)) for e in b.iter(f"{{{ns['bpmndi']}}}BPMNEdge")}
        flujos = [e.get("id") for e in b.iter(f"{{{ns['bpmn']}}}sequenceFlow")]
        check(all(n in formas for n in nodos) and all(aristas.get(f, 0) >= 2 for f in flujos) and len(nodos) >= 18,
              "bpmn: cada paso con su forma y cada flujo con su trazado")
        # 6. posiciones dadas (ingeniería inversa)
        pos = json.loads(EJEMPLO.read_text(encoding="utf-8"))
        for i, p in enumerate(pos["pasos"]):
            p["posicion"] = [100 + 150 * i, 50]
        (tmp / "pos.json").write_text(json.dumps(pos), encoding="utf-8")
        run("crear", tmp / "pos.json", "-o", tmp / "pos.drawio")
        check(dm.comparar(base, dm.leer(str(tmp / "pos.drawio"))[0]) == [], "crear con posiciones dadas")
        # 7b. varias páginas: actualizar solo toca la primera
        pag = tmp / "sub" / "dos.drawio"
        run("crear", EJEMPLO, "-o", pag)
        t = ET.parse(pag); extra = ET.SubElement(t.getroot(), "diagram", {"id": "p2", "name": "Página-2"})
        ET.SubElement(ET.SubElement(ET.SubElement(extra, "mxGraphModel"), "root"), "mxCell", {"id": "0"})
        t.write(pag, encoding="utf-8")
        (tmp / "c3.json").write_text(json.dumps({"cambios": [{"renombrar_carril": ["Aplicación", "Plataforma"]},
                                                              {"poner": {"id": "ACT-01", "nombre": "Registrar la solicitud"}}]}), encoding="utf-8")
        out = run("actualizar", pag, tmp / "c3.json")
        check("Página-2" in pag.read_text(encoding="utf-8"), "actualizar: conserva las demás páginas del fichero")
        check("carril renombrado: «Aplicación» → «Plataforma»" in out and "cambia de carril" not in out,
              "actualizar: un carril renombrado se informa en una línea")
        (tmp / "c4.json").write_text(json.dumps({"cambios": [{"poner": {"id": "ACT-99", "nombre": "Solo nombre"}}]}), encoding="utf-8")
        check("le falta: tipo, carril" in run("actualizar", pag, tmp / "c4.json", esperado=1), "actualizar: paso nuevo incompleto")
        (tmp / "c5.json").write_text(json.dumps({"cambios": [{"poner": {"id": "ACT-98", "tipo": "tarea", "carril": "Aplicaciones", "nombre": "x"}}]}), encoding="utf-8")
        check("no existe" in run("actualizar", pag, tmp / "c5.json", esperado=1), "actualizar: carril inexistente es un error")
        run("bpmn", pag)
        bb = (pag.with_suffix(".bpmn")).read_text(encoding="utf-8")
        check('boundaryEvent id="EV-02"' in bb and 'attachedToRef="ACT-04"' in bb, "bpmn: el plazo se exporta como evento de borde")
        check(run("validar", EJEMPLO).startswith("OK"), "validar: dice OK cuando está bien")
        # 8. nada se pisa, tipos BPMN, flujo por defecto, participantes externos y notas
        ped = tmp / "pedido" / "pedido.drawio"
        run("crear", PEDIDO, "-o", ped)
        base_p = json.loads(PEDIDO.read_text(encoding="utf-8"))
        check(dm.comparar(base_p, dm.leer(str(ped))[0]) == [],
              "pedido: el .drawio devuelve el mismo proceso (tipos nuevos, por defecto, externos y notas)")
        limpio = tmp / "limpio" / "solicitud.drawio"
        run("crear", EJEMPLO, "-o", limpio)
        check(solapes(limpio) == [] and solapes(ped) == [], "colocación: ninguna forma, etiqueta o nota se pisa "
              + "; ".join(solapes(limpio) + solapes(ped)))
        run("bpmn", ped)
        bb = ped.with_suffix(".bpmn").read_text(encoding="utf-8")
        check(all(t in bb for t in ("<bpmn:timerEventDefinition/></bpmn:startEvent>", "<bpmn:scriptTask", "<bpmn:callActivity",
                                    ' default="Flujo_', '<bpmn:participant id="Externo_1" name="ERP de compras"/>',
                                    "<bpmn:messageFlow", "<bpmn:textAnnotation", "<bpmn:association", "<bpmndi:BPMNLabel>")),
              "bpmn: inicio con temporizador, script, llamada, flujo por defecto, participante externo, mensaje y nota")
        # cambios con la colocación hecha a mano
        t = ET.parse(ped); r2 = t.getroot().find("diagram/mxGraphModel/root")
        g2 = next(e for e in r2 if e.get("id") == "ACT-01").find("mxGeometry"); g2.set("y", str(float(g2.get("y")) + 10))
        t.write(ped, encoding="utf-8")
        run("comparar", ped, "--aceptar")
        (tmp / "c6.json").write_text(json.dumps({"cambios": [
            {"externo": "Banco"}, {"flujo": {"de": "ACT-01", "a": "Banco", "etiqueta": "Consultar saldo"}},
            {"nota": {"paso": "ACT-02", "texto": "Revisa importes y proveedor"}},
            {"quitar_nota": {"paso": "ACT-04", "texto": "Si el ERP no responde, no se reintenta"}},
            {"flujo": {"de": "GW-02", "a": "EV-04", "defecto": False}}]}), encoding="utf-8")
        out = run("actualizar", ped, tmp / "c6.json")
        check("participante externo nuevo: «Banco»" in out and "nota nueva en ACT-02" in out and "nota quitada de ACT-04" in out
              and "deja de ser el flujo por defecto" in out and "se ha respetado la colocación" in out,
              "actualizar (manual): externo, nota, flujo de mensaje y flujo por defecto")
        check(run("comparar", ped).startswith("Sin cambios"), "actualizar (manual): el dibujo queda igual que el análisis")
        (tmp / "c7.json").write_text(json.dumps({"cambios": [{"quitar_externo": "Banco"}, {"quitar": "ACT-02"},
            {"flujo": {"de": "GW-01", "a": "ACT-03", "etiqueta": "Sí"}}]}), encoding="utf-8")
        out = run("actualizar", ped, tmp / "c7.json")
        check("participante externo quitado: «Banco»" in out and "nota quitada de ACT-02" in out
              and run("comparar", ped).startswith("Sin cambios"), "actualizar (manual): quitar un externo y un paso con nota")
        # Tarea 10: datos de Appian en el diagrama y en el BPMN; notas de texto largo
        datos_de_appian(tmp)
        nota_larga(tmp)
        # 9. la etiqueta de un evento va al lado por el que no llega ningún flujo
        rev = {"proceso": "Revisión", "carriles": ["Revisor", "Aplicación"],
               "pasos": [{"id": "EV-01", "tipo": "inicio", "carril": "Revisor", "nombre": "Solicitud registrada"},
                         {"id": "ACT-01", "tipo": "tarea", "carril": "Revisor", "nombre": "Revisar solicitud"},
                         {"id": "ACT-02", "tipo": "sistema", "carril": "Aplicación", "nombre": "Guardar decisión"},
                         {"id": "GW-01", "tipo": "exclusiva", "carril": "Aplicación", "nombre": "¿Aprobada?"},
                         {"id": "EV-02", "tipo": "mensaje", "carril": "Aplicación", "nombre": "Avisar aprobación al solicitante"},
                         {"id": "EV-03", "tipo": "mensaje", "carril": "Aplicación", "nombre": "Avisar rechazo al solicitante"},
                         {"id": "EV-04", "tipo": "fin", "carril": "Aplicación", "nombre": "Revisión resuelta"}],
               "flujos": [{"de": "EV-01", "a": "ACT-01"}, {"de": "ACT-01", "a": "ACT-02"}, {"de": "ACT-02", "a": "GW-01"},
                          {"de": "GW-01", "a": "EV-02", "etiqueta": "Sí"}, {"de": "GW-01", "a": "EV-03", "etiqueta": "No"},
                          {"de": "EV-02", "a": "EV-04"}, {"de": "EV-03", "a": "EV-04"}]}
        (tmp / "rev.json").write_text(json.dumps(rev), encoding="utf-8")
        run("crear", tmp / "rev.json", "-o", tmp / "rev")
        proc_r, geo_r, _ = dm.leer(str(tmp / "rev" / "rev.drawio"))
        por_debajo = [f["a"] for i, f in enumerate(proc_r["flujos"]) if f["a"].startswith("EV")
                      and geo_r["flujos"][i] and geo_r["flujos"][i][-1][1] > geo_r["pasos"][f["a"]][1] + 25]
        check(por_debajo and all(geo_r["etiquetas"].get(e) == "arriba" for e in por_debajo) and not solapes(tmp / "rev" / "rev.drawio"),
              f"etiquetas: los eventos a los que llega un flujo por debajo llevan la etiqueta encima ({', '.join(por_debajo) or 'ninguno'})")
        # 10. un proceso muy largo: aviso de ancho y PNG de tamaño razonable
        largo = {"proceso": "Largo", "carriles": ["Aplicación"],
                 "pasos": [{"id": "EV-01", "tipo": "inicio", "carril": "Aplicación", "nombre": "Inicio"}] +
                          [{"id": f"ACT-{i:02d}", "tipo": "sistema", "carril": "Aplicación", "nombre": f"Paso {i}"} for i in range(1, 25)] +
                          [{"id": "EV-02", "tipo": "fin", "carril": "Aplicación", "nombre": "Fin"}],
                 "flujos": [{"de": "EV-01", "a": "ACT-01"}] + [{"de": f"ACT-{i:02d}", "a": f"ACT-{i + 1:02d}"} for i in range(1, 24)] +
                           [{"de": "ACT-24", "a": "EV-02"}]}
        (tmp / "largo.json").write_text(json.dumps(largo), encoding="utf-8")
        out = run("crear", tmp / "largo.json", "-o", tmp / "largo")
        from struct import unpack
        ancho_png = unpack(">I", (tmp / "largo" / "largo.png").read_bytes()[16:20])[0]
        check("aviso: el diagrama mide" in out and ancho_png <= 3300, f"ancho: aviso y PNG de {ancho_png} px como mucho 3300")
        # 7. errores de validación
        malo = {"proceso": "x", "carriles": ["A"], "pasos": [{"id": "ACT-01", "tipo": "tareas", "carril": "B", "nombre": "x"}],
                "flujos": [{"de": "ACT-01", "a": "ACT-02"}]}
        (tmp / "malo.json").write_text(json.dumps(malo), encoding="utf-8")
        out = run("validar", tmp / "malo.json", esperado=1)
        check("desconocido" in out and "no está en «carriles»" in out and "no existe el paso ACT-02" in out,
              "validar: tipo, carril y flujo incorrectos")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if fallos:
        print("\n" + "\n\n".join(fallos))
        sys.exit(1)
    print("\nTodo correcto.")


# ---------------------------------------------------------------- pintor Mermaid
def probar_mermaid():
    """mermaid.py: valida los .mmd y los bloques mermaid de un Markdown, avisa de los diagramas demasiado anchos y
    no escribe nada fuera de su carpeta de salida (ni temporales)."""
    script = SCRIPTS / "mermaid.py"
    check(script.is_file(), "mermaid: el pintor Mermaid está en la skill de diagramas")
    if not script.is_file():
        return
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="mermaid-"))
    try:
        carpeta = tmp / "Carpeta con espacios" / "Gestión app"
        temporales = tmp / "temporales"  # la carpeta temporal del sistema para el pintor: tiene que acabar vacía
        carpeta.mkdir(parents=True)
        temporales.mkdir()
        entorno = dict(os.environ, TMPDIR=str(temporales), TEMP=str(temporales), TMP=str(temporales))

        def pinta(*args):
            r = subprocess.run([sys.executable, str(script), *map(str, args)], capture_output=True, text=True,
                               encoding="utf-8", env=entorno)
            if r.returncode == 2:
                print(r.stdout + r.stderr); sys.exit(2)
            return r.returncode, r.stdout + r.stderr

        def comprueba(cond, texto, out):  # la salida del pintor, solo si falla
            check(cond, texto + ("" if cond else "\n" + out))

        valido = carpeta / "estados.mmd"
        valido.write_text("stateDiagram-v2\n    [*] --> Borrador\n    Borrador --> EnRevision: Unidad envía\n"
                          "    EnRevision --> [*]\n    EnRevision: En revisión\n", encoding="utf-8")
        roto = carpeta / "roto.mmd"
        roto.write_text("flowchart LR\n    A[Inicio] --> B[[[Sin cerrar\n", encoding="utf-8")
        ancho = carpeta / "ancho.mmd"
        ancho.write_text("flowchart LR\n    " + " --> ".join(f"P{i}[Paso {i}]" for i in range(1, 25)) + "\n", encoding="utf-8")
        lineas = ["# Documento", "", "```mermaid", "stateDiagram-v2", "    [*] --> Borrador", "    Borrador --> [*]",
                  "```", "", "Texto entre los dos diagramas.", "", "Otro párrafo.", "```mermaid", "flowchart LR",
                  "    A[Inicio] --> B[[[Sin cerrar", "```", ""]
        assert lineas[11] == "```mermaid"
        doc = carpeta / "documento.md"
        doc.write_text("\n".join(lineas), encoding="utf-8")
        antes = sorted(p.name for p in carpeta.iterdir())

        c, out = pinta("--check", valido)
        comprueba(c == 0 and "OK" in out and "px de ancho" not in out, "mermaid --check: un .mmd válido sale con 0", out)
        c, out = pinta("--check", roto)
        comprueba(c == 1 and "roto.mmd" in out, "mermaid --check: uno con un error de sintaxis sale con 1", out)
        c, out = pinta("--md", doc)
        comprueba(c == 1 and "línea 12" in out and "línea 3" not in out,
                  "mermaid --md: dice en qué línea empieza el bloque roto, y solo ese", out)
        c, out = pinta("--check", ancho)
        comprueba(c == 0 and "px de ancho" in out, "mermaid: avisa de un diagrama de más de 1.600 px de ancho", out)
        check(sorted(p.name for p in carpeta.iterdir()) == antes, "mermaid --check y --md: no escriben nada")
        imagenes = carpeta / "imágenes"
        c, out = pinta(valido, "--svg", "-o", imagenes)
        png = imagenes / "estados.png"
        comprueba(c == 0 and png.is_file() and png.stat().st_size > 2000
                  and sorted(p.name for p in imagenes.iterdir()) == ["estados.png", "estados.svg"],
                  "mermaid: PNG y SVG en la carpeta de salida, y nada más", out)
        sobra = [p.name for p in temporales.iterdir()]
        check(sorted(p.name for p in carpeta.iterdir()) == sorted(antes + ["imágenes"]) and not sobra,
              "mermaid: nada fuera de la carpeta de salida, ni temporales" + (": " + ", ".join(sobra) if sobra else ""))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
