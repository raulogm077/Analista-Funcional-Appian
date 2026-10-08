#!/usr/bin/env python3
"""Prueba de la skill de diagramas de principio a fin, en una carpeta temporal (tarda unos 30 segundos).

Crea el ejemplo, lo cambia, simula una edición a mano en draw.io (también guardada comprimida),
la compara y la acepta, vuelve a cambiarlo respetando lo movido a mano, exporta BPMN 2.0 y
comprueba los errores de validación. Con el segundo ejemplo comprueba que nada se pisa, el lado de las
etiquetas, los tipos de inicio y tarea, el flujo por defecto, los participantes externos, las notas y el
ancho del PNG. Sale con 0 si todo va bien (tarda alrededor de un minuto).

  python3 pruebas/appian-diagramas-bpmn/selftest.py

Prueba la skill de $PLUGIN_A_PROBAR/skills/appian-diagramas-bpmn (por defecto, la de este repositorio) con los
procesos de ejemplo de datos/."""
import base64, json, os, pathlib, shutil, subprocess, sys, tempfile, urllib.parse, zlib
import xml.etree.ElementTree as ET

AQUI = pathlib.Path(__file__).resolve().parent
PLUGIN = pathlib.Path(os.environ.get("PLUGIN_A_PROBAR") or AQUI.parents[1]).resolve()
SCRIPTS = PLUGIN / "skills" / "appian-diagramas-bpmn" / "scripts"
CLI = [sys.executable, str(SCRIPTS / "diagrama.py")]
EJEMPLO = AQUI / "datos" / "solicitud.json"
PEDIDO = AQUI / "datos" / "pedido.json"
fallos = []


def run(*args, esperado=0):
    r = subprocess.run(CLI + [str(a) for a in args], capture_output=True, text=True, encoding="utf-8")
    if r.returncode == 2:
        print(r.stderr); sys.exit(2)
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
    origen = AQUI / "datos" / "semantico.json"   # el proceso de proceso_semantico.bpmn de ingeniería inversa
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
        {"poner": {"id": "ACT-03", "tipo": "llamada", "carril": "Sistema", "nombre": "Notificar", "nodo": "7",
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
        {"poner": {"id": "ACT-04", "tipo": "script", "carril": "Sistema", "nombre": "Calcular plazo", "nodo": "8"}},
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
        b.close()
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


def main():
    for s in (sys.stdout, sys.stderr):
        s.reconfigure(encoding="utf-8", errors="replace")
    probar_mermaid()
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="diagramas-"))
    try:
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
