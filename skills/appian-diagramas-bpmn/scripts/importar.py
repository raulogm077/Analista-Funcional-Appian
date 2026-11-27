"""Pasa un diagrama de otra herramienta al JSON de la skill: un Visio (.vsdx) o un BPMN 2.0 (.bpmn).

Sale lo que el dibujo dice: pasos con su tipo, carril y nombre, flujos con su etiqueta, participantes externos con
sus mensajes y notas. Los códigos (ACT-, GW-, EV-) se dan por orden de izquierda a derecha, salvo los que ya lo son
(un .bpmn exportado por esta skill conserva los suyos). Lo que no se puede saber del dibujo se avisa: un paso fuera de
cualquier carril, una forma que no es de BPMN, un conector suelto.

Un Visio con varias páginas da un proceso por página (`paginas`: una pestaña por fase en el .drawio).
"""
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

sys.dont_write_bytecode = True  # sin __pycache__ en el plugin
import drawio_modelo as dm

BP = "{http://www.omg.org/spec/BPMN/20100524/MODEL}"
DC = "{http://www.omg.org/spec/DD/20100524/DC}"
BPMNDI = "{http://www.omg.org/spec/BPMN/20100524/DI}"
V = "{http://schemas.microsoft.com/office/visio/2012/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
CODIGO = re.compile(r"(ACT|GW|EV)[-_](\d+)$")

TAREA_BPMN = {"userTask": "tarea", "task": "tarea", "serviceTask": "sistema", "sendTask": "sistema",
              "receiveTask": "sistema", "businessRuleTask": "sistema", "scriptTask": "script", "manualTask": "manual",
              "subProcess": "subproceso", "callActivity": "llamada", "transaction": "subproceso"}
PUERTA_BPMN = {"exclusiveGateway": "exclusiva", "eventBasedGateway": "exclusiva", "complexGateway": "inclusiva",
               "parallelGateway": "paralela", "inclusiveGateway": "inclusiva"}


def _codigos(pasos, x):
    """Da a cada paso su código, por orden de izquierda a derecha; respeta los que ya son códigos de la skill."""
    usados = {}
    for p in pasos:
        m = CODIGO.match(p["id"])
        if m and dm.PREFIJO[p["tipo"]] == m.group(1):
            p["id"] = f"{m.group(1)}-{int(m.group(2)):02d}"
            usados.setdefault(m.group(1), set()).add(int(m.group(2)))
        else:
            p["_nuevo"] = True
    mapa = {}
    for p in sorted(pasos, key=lambda p: (x.get(p["_orig"], 0), p["_orig"])):
        if p.pop("_nuevo", False):
            pre = dm.PREFIJO[p["tipo"]]
            n = 1
            while n in usados.setdefault(pre, set()):
                n += 1
            usados[pre].add(n)
            p["id"] = f"{pre}-{n:02d}"
    for p in pasos:
        mapa[p.pop("_orig")] = p["id"]
    return mapa


# ---------------------------------------------------------------- BPMN 2.0
def importar_bpmn(ruta):
    raiz = ET.parse(ruta).getroot()
    avisos = []
    bounds = {}
    for s in raiz.iter(f"{BPMNDI}BPMNShape"):
        b = s.find(f"{DC}Bounds")
        if b is not None:
            bounds[s.get("bpmnElement")] = tuple(float(b.get(k, 0)) for k in ("x", "y", "width", "height"))
    procesos = raiz.findall(f"{BP}process")
    colab = raiz.find(f"{BP}collaboration")
    participantes = colab.findall(f"{BP}participant") if colab is not None else []
    con_proceso = {p.get("processRef"): p.get("name") for p in participantes if p.get("processRef")}
    externos = {p.get("id"): p.get("name") or p.get("id") for p in participantes if not p.get("processRef")}
    if len(procesos) > 1:
        avisos.append(f"el .bpmn tiene {len(procesos)} procesos: tomo el primero con pasos")
    proc_el = next((p for p in procesos if len(p)), procesos[0] if procesos else None)
    if proc_el is None:
        raise dm.ErrorProceso(f"{ruta}: no tiene ningún proceso")
    nombre = proc_el.get("name") or con_proceso.get(proc_el.get("id")) or "Proceso"
    carril_de, carriles = {}, []
    lanes = list(proc_el.iter(f"{BP}lane"))
    lanes.sort(key=lambda l: bounds.get(l.get("id"), (0, 0, 0, 0))[1])
    for lane in lanes:
        if lane.find(f"{BP}childLaneSet") is not None:
            continue
        c = lane.get("name") or lane.get("id")
        carriles.append(c)
        for ref in lane.findall(f"{BP}flowNodeRef"):
            carril_de[(ref.text or "").strip()] = c
    if not carriles:
        carriles = [con_proceso.get(proc_el.get("id")) or nombre]
    pasos, flujos, notas = [], [], []
    borde = {}
    for el in proc_el:
        tag = el.tag.replace(BP, "")
        eid = el.get("id")
        defs = {d.tag.replace(BP, "") for d in el if d.tag.endswith("EventDefinition")}
        tipo = TAREA_BPMN.get(tag) or PUERTA_BPMN.get(tag)
        if tag == "startEvent":
            tipo = "inicio_temporizador" if "timerEventDefinition" in defs else \
                "inicio_mensaje" if "messageEventDefinition" in defs else "inicio"
        elif tag == "endEvent":
            tipo = "error" if "errorEventDefinition" in defs else "fin"
        elif tag in ("intermediateCatchEvent", "intermediateThrowEvent", "boundaryEvent"):
            tipo = "temporizador" if "timerEventDefinition" in defs else "mensaje" if "messageEventDefinition" in defs \
                else "error" if "errorEventDefinition" in defs else "intermedio"
        if tipo is None:
            continue
        p = {"_orig": eid, "id": eid, "tipo": tipo, "carril": carril_de.get(eid), "nombre": el.get("name") or ""}
        doc = el.find(f"{BP}documentation")
        if doc is not None and doc.text:
            for parte in doc.text.split("; "):
                if parte.startswith("nodo "):
                    p["nodo"] = parte[5:]
                elif parte.startswith("Supuesto: "):
                    p["supuesto"] = parte[10:]
        if tipo == "llamada" and el.get("calledElement"):
            p["proceso_llamado"] = el.get("calledElement").replace("_", " ")
        t = el.find(f".//{BP}timerEventDefinition")
        if t is not None and len(t) and (t[0].text or "").strip():
            p["temporizador"] = t[0].text.strip()
        if tag == "boundaryEvent":
            borde[eid] = el.get("attachedToRef")
            if tipo == "temporizador" and el.get("cancelActivity", "true") == "true":
                p["interrumpe"] = True
        pasos.append(p)
    ids = {p["_orig"] for p in pasos}
    por_id = {p["_orig"]: p for p in pasos}
    for ev, tarea in borde.items():
        if por_id[ev]["carril"] is None and tarea in por_id:
            por_id[ev]["carril"] = por_id[tarea]["carril"]
        flujos.append({"de": tarea, "a": ev, "discontinuo": True})
    defectos = {el.get("default") for el in proc_el if el.get("default")}
    for el in proc_el.findall(f"{BP}sequenceFlow"):
        de, a = el.get("sourceRef"), el.get("targetRef")
        if de not in ids or a not in ids:
            avisos.append(f"el flujo {el.get('id')} no une dos pasos y se ignora")
            continue
        f = {"de": de, "a": a}
        if el.get("name"):
            f["etiqueta"] = el.get("name")
        if el.get("id") in defectos:
            f["defecto"] = True
        cond = el.find(f"{BP}conditionExpression")
        if cond is not None and (cond.text or "").strip():
            f["condicion"] = cond.text.strip()
        flujos.append(f)
    usados_ext = []
    if colab is not None:
        for el in colab.findall(f"{BP}messageFlow"):
            de, a = el.get("sourceRef"), el.get("targetRef")
            de = externos.get(de, de)
            a = externos.get(a, a)
            if (de in ids or a in ids) and (de in externos.values() or a in externos.values()):
                f = {"de": de, "a": a}
                if el.get("name"):
                    f["etiqueta"] = el.get("name")
                flujos.append(f)
                usados_ext += [x for x in (de, a) if x in externos.values() and x not in usados_ext]
    texto = {el.get("id"): (el.findtext(f"{BP}text") or "").strip() for el in proc_el.findall(f"{BP}textAnnotation")}
    for el in proc_el.findall(f"{BP}association"):
        nota, paso = el.get("sourceRef"), el.get("targetRef")
        if paso in texto:
            nota, paso = paso, nota
        if nota in texto and paso in ids and texto[nota]:
            notas.append({"paso": paso, "texto": texto[nota]})
    return _cerrar(nombre, carriles, pasos, flujos, usados_ext, notas,
                   {k: v[0] for k, v in bounds.items()}, avisos)


def _cerrar(nombre, carriles, pasos, flujos, externos, notas, x, avisos):
    sueltos = [p for p in pasos if p["carril"] is None]
    if sueltos:
        avisos.append(f"{len(sueltos)} paso{'s' * (len(sueltos) > 1)} fuera de cualquier carril; van al primero: "
                      + ", ".join(f"«{p['nombre'] or p['_orig']}»" for p in sueltos))
        for p in sueltos:
            p["carril"] = carriles[0]
    mapa = _codigos(pasos, x)
    for f in flujos:
        f["de"], f["a"] = mapa.get(f["de"], f["de"]), mapa.get(f["a"], f["a"])
    for n in notas:
        n["paso"] = mapa[n["paso"]]
    usados = {p["carril"] for p in pasos}
    proc = {"proceso": nombre, "carriles": [c for c in carriles if c in usados], "pasos": pasos, "flujos": flujos}
    if externos:
        proc["externos"] = externos
    if notas:
        proc["notas"] = notas
    return proc, avisos


# ---------------------------------------------------------------- Visio
def _tipo_visio(master):
    m = (master or "").lower()
    if any(k in m for k in ("message flow", "flujo de mensaje")):
        return "mensaje_flujo"
    if any(k in m for k in ("sequence flow", "connector", "conector", "flujo de secuencia", "association", "asociación")):
        return "flujo"
    if any(k in m for k in ("annotation", "anotación", "comentario")):
        return "nota"
    if any(k in m for k in ("pool", "lane", "swimlane", "carril", "calle", "función", "function", "separator")):
        return "carril"
    if re.search(r"\b(start|inicio)\b", m):
        return "inicio"
    if re.search(r"\b(end|fin|terminador|terminator)\b", m):
        return "fin"
    if any(k in m for k in ("intermediate", "intermedio", "timer", "temporizador")):
        return "temporizador" if any(k in m for k in ("timer", "temporizador")) else "intermedio"
    if any(k in m for k in ("gateway", "puerta", "decision", "decisión")):
        return "paralela" if any(k in m for k in ("parallel", "paralela")) else \
            "inclusiva" if any(k in m for k in ("inclusive", "inclusiva")) else "exclusiva"
    if any(k in m for k in ("sub-process", "subprocess", "subproceso")):
        return "subproceso"
    if any(k in m for k in ("task", "tarea", "process", "proceso", "activity", "actividad")):
        return "tarea"
    return None


def _celdas(shape):
    return {c.get("N"): c.get("V") for c in shape.findall(f"{V}Cell")}


def _texto_visio(shape):
    t = shape.find(f"{V}Text")
    return re.sub(r"\s+", " ", "".join(t.itertext())).strip() if t is not None else ""


def importar_vsdx(ruta):
    """[(proceso, avisos)] de cada página del Visio que tiene pasos."""
    z = zipfile.ZipFile(ruta)
    nombres = set(z.namelist())
    masters = {}
    if "visio/masters/masters.xml" in nombres:
        for m in ET.fromstring(z.read("visio/masters/masters.xml")).findall(f"{V}Master"):
            masters[m.get("ID")] = m.get("NameU") or m.get("Name") or ""
    paginas = ET.fromstring(z.read("visio/pages/pages.xml"))
    rels = {}
    if "visio/pages/_rels/pages.xml.rels" in nombres:
        for r in ET.fromstring(z.read("visio/pages/_rels/pages.xml.rels")):
            rels[r.get("Id")] = r.get("Target")
    salida = []
    for k, pag in enumerate(paginas.findall(f"{V}Page"), 1):
        rel = pag.find(f"{V}Rel")
        fichero = rels.get(rel.get(f"{R}id")) if rel is not None else None
        fichero = f"visio/pages/{fichero or f'page{k}.xml'}"
        if fichero not in nombres:
            continue
        proc, avisos = _pagina_visio(ET.fromstring(z.read(fichero)), masters, pag.get("NameU") or pag.get("Name") or f"Página {k}")
        if proc["pasos"]:
            salida.append((proc, avisos))
    if not salida:
        raise dm.ErrorProceso(f"{ruta}: ninguna página tiene formas de proceso")
    return salida


def _pagina_visio(page, masters, nombre):
    avisos = []
    formas = {}

    def recorrer(shapes, dx=0.0, dy=0.0, master_padre=None):
        for s in shapes.findall(f"{V}Shape"):
            c = _celdas(s)
            master = masters.get(s.get("Master")) or masters.get(master_padre) or s.get("NameU") or s.get("Name") or ""
            px, py = float(c.get("PinX") or 0) + dx, float(c.get("PinY") or 0) + dy
            w, h = float(c.get("Width") or 0), float(c.get("Height") or 0)
            formas[s.get("ID")] = {"tipo": _tipo_visio(master), "texto": _texto_visio(s), "x": px, "y": py, "w": w, "h": h,
                                   "master": master}
            hijos = s.find(f"{V}Shapes")
            if hijos is not None:
                lx, ly = float(c.get("LocPinX") or w / 2), float(c.get("LocPinY") or h / 2)
                recorrer(hijos, px - lx, py - ly, s.get("Master"))
    shapes = page.find(f"{V}Shapes")
    if shapes is not None:
        recorrer(shapes)
    # carriles: de arriba abajo (en Visio la y crece hacia arriba)
    lanes = sorted(((i, f) for i, f in formas.items() if f["tipo"] == "carril" and f["texto"]), key=lambda kv: -kv[1]["y"])
    carriles = []
    for _, f in lanes:
        if f["texto"] not in carriles:
            carriles.append(f["texto"])

    def carril(f):
        dentro = [l for _, l in lanes if abs(f["x"] - l["x"]) <= l["w"] / 2 and abs(f["y"] - l["y"]) <= l["h"] / 2]
        # el más pequeño que lo contiene: un pool contiene a sus carriles
        return min(dentro, key=lambda l: l["w"] * l["h"])["texto"] if dentro else None
    conexiones = {}
    for c in page.iter(f"{V}Connect"):
        conexiones.setdefault(c.get("FromSheet"), {})["de" if c.get("FromCell") == "BeginX" else "a"] = c.get("ToSheet")
    pasos, flujos, notas = [], [], []
    for i, f in formas.items():
        if f["tipo"] in dm.TIPOS:
            pasos.append({"_orig": i, "id": i, "tipo": f["tipo"], "carril": carril(f), "nombre": f["texto"]})
        elif f["tipo"] is None and f["texto"] and i not in conexiones:
            avisos.append(f"forma «{f['texto']}» ({f['master'] or 'sin patrón'}) no es de BPMN: no la paso")
    ids = {p["_orig"] for p in pasos}
    # un pool o un carril sin pasos con el que se cruzan mensajes es un participante externo
    con_pasos = {p["carril"] for p in pasos}
    externo = {i: f["texto"] for i, f in lanes if f["texto"] not in con_pasos}
    externos = []
    for i, ends in conexiones.items():
        de, a = ends.get("de"), ends.get("a")
        if formas.get(de, {}).get("tipo") == "nota" or formas.get(a, {}).get("tipo") == "nota":
            nota, paso = (de, a) if formas.get(de, {}).get("tipo") == "nota" else (a, de)
            if paso in ids and formas[nota]["texto"]:
                notas.append({"paso": paso, "texto": formas[nota]["texto"]})
            continue
        if (de in externo and a in ids) or (a in externo and de in ids):
            f = {"de": externo.get(de, de), "a": externo.get(a, a)}
            if formas[i]["texto"]:
                f["etiqueta"] = formas[i]["texto"]
            flujos.append(f)
            externos += [e for e in (f["de"], f["a"]) if e in externo.values() and e not in externos]
            continue
        if de not in ids or a not in ids:
            avisos.append(f"un conector{' «' + formas[i]['texto'] + '»' if formas.get(i, {}).get('texto') else ''} "
                          "no une dos pasos y se ignora")
            continue
        f = {"de": de, "a": a}
        if formas[i]["texto"]:
            f["etiqueta"] = formas[i]["texto"]
        flujos.append(f)
    carriles = [c for c in carriles if c not in externo.values()] or [nombre]
    return _cerrar(nombre, carriles, pasos, flujos, externos, notas, {i: f["x"] for i, f in formas.items()}, avisos)


def importar(ruta):
    """(proceso o libro, avisos) de un .vsdx o un .bpmn. Un Visio de varias páginas da un libro (`paginas`)."""
    ruta = str(ruta)
    if ruta.lower().endswith(".bpmn") or ruta.lower().endswith(".xml"):
        return importar_bpmn(ruta)
    if ruta.lower().endswith(".vsdx"):
        partes = importar_vsdx(ruta)
        if len(partes) == 1:
            return partes[0]
        avisos = [f"página «{p['proceso']}»: {a}" for p, av in partes for a in av]
        return {"proceso": partes[0][0]["proceso"], "paginas": [p for p, _ in partes]}, avisos
    raise dm.ErrorProceso(f"{ruta}: importo .vsdx y .bpmn (un .vsd antiguo, ábrelo en Visio y guárdalo como .vsdx)")


# ---------------------------------------------------------------- comparar con una referencia
def _normal(nombre):
    import unicodedata
    m = dm.CODIGO.match(nombre or "")
    texto = m.group(1) if m and m.group(1) else (nombre or "")
    texto = unicodedata.normalize("NFD", texto.lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return re.sub(r"[^\w¿?]+", " ", texto).strip()


def referencia(ruta, proceso=None):
    """El proceso de referencia (de un .json, un .drawio, un .vsdx o un .bpmn) y sus avisos. Si trae varias páginas,
    la que se llama como `proceso` o, si ninguna, la primera."""
    ruta = str(ruta)
    avisos = []
    if ruta.lower().endswith(".json"):
        ref = dm.cargar_json(ruta)
    elif ruta.lower().endswith(".drawio"):
        import pestanas
        if pestanas.es_libro_drawio(ruta):
            import pathlib, tempfile
            _, pags = pestanas._paginas(ruta)
            d = next((d for d in pags if d.get("name") == proceso), pags[0])
            with tempfile.TemporaryDirectory() as tmp:
                suelta = pathlib.Path(tmp) / "ref.drawio"
                pestanas._suelta(d, suelta)
                ref, _, avisos = dm.leer(str(suelta))
        else:
            ref, _, avisos = dm.leer(ruta)
    else:
        ref, avisos = importar(ruta)
    if "paginas" in ref:
        paginas = ref["paginas"]
        elegida = next((p for p in paginas if _normal(p.get("proceso")) == _normal(proceso)), None)
        if elegida is None:
            avisos.append(f"ninguna página de la referencia se llama «{proceso}»: comparo con «{paginas[0].get('proceso')}»")
        ref = elegida or paginas[0]
    return ref, avisos


def cotejar(proc, ref):
    """Las diferencias entre el proceso del diagrama y una referencia, emparejando los pasos por nombre (sin
    mayúsculas, tildes ni códigos) y, si no, por un nombre parecido del mismo tipo de forma. [(clase, texto)], con
    clase «error» (perfil equivocado, paso o flujo que falta), «forma» (otro tipo, nombre parecido) o «añadido»."""
    import difflib
    out = []
    clase = lambda t: "tarea" if t in dm.TAREAS else "puerta" if t in dm.PUERTAS else "evento"   # noqa: E731
    sin_pareja_d = [p for p in proc["pasos"] if _normal(p.get("nombre"))]
    sin_pareja_r = [p for p in ref["pasos"] if _normal(p.get("nombre"))]
    pareja = {}
    for r in list(sin_pareja_r):
        d = next((d for d in sin_pareja_d if _normal(d["nombre"]) == _normal(r["nombre"])), None)
        if d:
            pareja[r["id"]] = d
            sin_pareja_d.remove(d)
            sin_pareja_r.remove(r)
    for r in list(sin_pareja_r):
        candidatos = [(difflib.SequenceMatcher(None, _normal(r["nombre"]), _normal(d["nombre"])).ratio(), d)
                      for d in sin_pareja_d if clase(d["tipo"]) == clase(r["tipo"])]
        if candidatos:
            ratio, d = max(candidatos, key=lambda c: c[0])
            if ratio >= 0.75:
                pareja[r["id"]] = d
                sin_pareja_d.remove(d)
                sin_pareja_r.remove(r)
                out.append(("forma", f"nombre parecido: «{r['nombre']}» en la referencia, «{d['nombre']}» en el diagrama"))
    for r in ref["pasos"]:
        d = pareja.get(r["id"])
        if d is None:
            continue
        if _normal(r["carril"]) != _normal(d["carril"]):
            out.append(("error", f"«{d['nombre']}»: lo hace «{r['carril']}» en la referencia y «{d['carril']}» en el diagrama"))
        if r["tipo"] != d["tipo"]:
            out.append(("forma", f"«{d['nombre']}»: {r['tipo']} en la referencia y {d['tipo']} en el diagrama"))
    for r in sin_pareja_r:
        out.append(("error", f"falta «{r['nombre']}» ({r['tipo']}, {r['carril']}): está en la referencia"))
    for d in sin_pareja_d:
        out.append(("añadido", f"«{d['nombre']}» ({d['tipo']}, {d['carril']}) no está en la referencia"))
    # flujos, entre pasos emparejados (los que tocan una forma sin nombre no se pueden emparejar)
    nombre_d = {d["id"]: _normal(d["nombre"]) for d in pareja.values()}
    nombre_r = {r: _normal(d["nombre"]) for r, d in pareja.items()}
    legible = {d["id"]: d["nombre"] for d in pareja.values()}
    for e in proc.get("externos") or []:          # los mensajes con un participante externo, por su nombre
        nombre_d[e], legible[e] = _normal(e), e
    for e in ref.get("externos") or []:
        nombre_r[e] = _normal(e)
    faltan_ext = [e for e in ref.get("externos") or [] if _normal(e) not in {_normal(x) for x in proc.get("externos") or []}]
    for e in faltan_ext:
        out.append(("error", f"falta el participante externo «{e}»: está en la referencia"))
    fd = {(nombre_d[f["de"]], nombre_d[f["a"]]): f for f in proc["flujos"] if f["de"] in nombre_d and f["a"] in nombre_d}
    fr = {(nombre_r[f["de"]], nombre_r[f["a"]]): f for f in ref["flujos"] if f["de"] in nombre_r and f["a"] in nombre_r}
    texto = {v: legible[k] for k, v in nombre_d.items()}
    texto.update({_normal(e): e for e in ref.get("externos") or [] if _normal(e) not in texto})
    for par, f in fr.items():
        if par not in fd:
            out.append(("error", f"falta el flujo «{texto[par[0]]}» → «{texto[par[1]]}»: está en la referencia"))
        elif _normal(f.get("etiqueta")) != _normal(fd[par].get("etiqueta")):
            out.append(("forma", f"flujo «{texto[par[0]]}» → «{texto[par[1]]}»: «{f.get('etiqueta') or ''}» en la "
                                 f"referencia y «{fd[par].get('etiqueta') or ''}» en el diagrama"))
    for par in fd:
        if par not in fr:
            out.append(("añadido", f"flujo «{texto[par[0]]}» → «{texto[par[1]]}» no está en la referencia"))
    sueltos = sum(1 for f in ref["flujos"] if f["de"] not in nombre_r or f["a"] not in nombre_r)
    if sueltos:
        out.append(("forma", f"{sueltos} flujo{'s' * (sueltos > 1)} de la referencia tocan un paso que falta o una "
                             "forma sin nombre (una puerta que une): no se comparan uno a uno"))
    return out
