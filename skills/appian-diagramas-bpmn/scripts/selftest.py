#!/usr/bin/env python3
"""Prueba de la skill de diagramas de principio a fin, en una carpeta temporal (tarda unos 30 segundos).

Crea el ejemplo, lo cambia, simula una edición a mano en draw.io (también guardada comprimida),
la compara y la acepta, vuelve a cambiarlo respetando lo movido a mano, exporta BPMN 2.0 y
comprueba los errores de validación. Sale con 0 si todo va bien."""
import base64, json, pathlib, shutil, subprocess, sys, tempfile, urllib.parse, zlib
import xml.etree.ElementTree as ET

HERE = pathlib.Path(__file__).resolve().parent
CLI = [sys.executable, str(HERE / "diagrama.py")]
EJEMPLO = HERE.parent / "ejemplos" / "solicitud.json"
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


def main():
    for s in (sys.stdout, sys.stderr):
        s.reconfigure(encoding="utf-8", errors="replace")
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
        sys.path.insert(0, str(HERE)); import drawio_modelo as dm
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
            {"poner": {"id": "ACT-12", "tipo": "sistema", "carril": "Sistema", "nombre": "Calcular tasa"}},
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
        (tmp / "c3.json").write_text(json.dumps({"cambios": [{"renombrar_carril": ["Sistema", "Plataforma"]},
                                                              {"poner": {"id": "ACT-01", "nombre": "Registrar la solicitud"}}]}), encoding="utf-8")
        out = run("actualizar", pag, tmp / "c3.json")
        check("Página-2" in pag.read_text(encoding="utf-8"), "actualizar: conserva las demás páginas del fichero")
        check("carril renombrado: «Sistema» → «Plataforma»" in out and "cambia de carril" not in out,
              "actualizar: un carril renombrado se informa en una línea")
        (tmp / "c4.json").write_text(json.dumps({"cambios": [{"poner": {"id": "ACT-99", "nombre": "Solo nombre"}}]}), encoding="utf-8")
        check("le falta: tipo, carril" in run("actualizar", pag, tmp / "c4.json", esperado=1), "actualizar: paso nuevo incompleto")
        (tmp / "c5.json").write_text(json.dumps({"cambios": [{"poner": {"id": "ACT-98", "tipo": "tarea", "carril": "Sistemas", "nombre": "x"}}]}), encoding="utf-8")
        check("no existe" in run("actualizar", pag, tmp / "c5.json", esperado=1), "actualizar: carril inexistente es un error")
        run("bpmn", pag)
        bb = (pag.with_suffix(".bpmn")).read_text(encoding="utf-8")
        check('boundaryEvent id="EV-02"' in bb and 'attachedToRef="ACT-04"' in bb, "bpmn: el plazo se exporta como evento de borde")
        check(run("validar", EJEMPLO).startswith("OK"), "validar: dice OK cuando está bien")
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


if __name__ == "__main__":
    main()
