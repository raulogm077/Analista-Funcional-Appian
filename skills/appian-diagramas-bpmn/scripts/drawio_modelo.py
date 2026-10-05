"""Modelo de un proceso BPMN y su fichero .drawio.

El proceso se intercambia en JSON (ver SKILL.md):
  {"proceso": str, "carriles": [str], "pasos": [{id, tipo, carril, nombre, posicion?}],
   "flujos": [{de, a, etiqueta?, discontinuo?}]}

Este módulo sabe:
- escribir un .drawio nuevo a partir del proceso y una geometría ya calculada;
- leer cualquier .drawio (también comprimido o editado a mano) y devolver el proceso;
- validar un proceso y comparar dos.
Solo usa la biblioteca estándar.
"""
import base64, copy, html, json, re, urllib.parse, zlib
import xml.etree.ElementTree as ET

# ---------------------------------------------------------------- tipos y estilos
EVENTOS = {"inicio", "fin", "temporizador", "mensaje", "intermedio"}
PUERTAS = {"exclusiva", "paralela", "inclusiva"}
TAREAS = {"tarea", "sistema", "manual", "subproceso"}
TIPOS = EVENTOS | PUERTAS | TAREAS
PREFIJO = {**{t: "EV" for t in EVENTOS}, **{t: "GW" for t in PUERTAS}, **{t: "ACT" for t in TAREAS}}
TAM = {**{t: (40, 40) for t in EVENTOS}, **{t: (50, 50) for t in PUERTAS}, **{t: (120, 80) for t in TAREAS}}

AZUL, VERDE, ROJO, AMBAR = "#1d659c", "#117c00", "#b2002c", "#b86e00"
_BASE = "points=[];html=1;fontSize=12;fontColor=#222222;"
_EV = _BASE + ("shape=mxgraph.bpmn.event;verticalLabelPosition=bottom;verticalAlign=top;align=center;"
               "perimeter=ellipsePerimeter;outlineConnect=0;aspect=fixed;labelBackgroundColor=none;")
_GW = _BASE + ("shape=mxgraph.bpmn.gateway2;outline=none;symbol=none;verticalLabelPosition=top;verticalAlign=bottom;"
               "align=center;perimeter=rhombusPerimeter;outlineConnect=0;strokeColor=" + AMBAR + ";fillColor=#fff8e6;"
               "labelBackgroundColor=none;")
_TK = _BASE + ("shape=mxgraph.bpmn.task;rectStyle=rounded;size=10;whiteSpace=wrap;strokeColor=" + AZUL + ";")
ESTILO = {
    "inicio": _EV + f"outline=standard;symbol=general;strokeColor={VERDE};",
    "fin": _EV + f"outline=end;symbol=general;strokeColor={ROJO};",
    "temporizador": _EV + f"outline=catching;symbol=timer;strokeColor={AZUL};",
    "mensaje": _EV + f"outline=throwing;symbol=message;strokeColor={AZUL};",
    "intermedio": _EV + f"outline=catching;symbol=general;strokeColor={AZUL};",
    "exclusiva": _GW + "gwType=exclusive;",
    "paralela": _GW + "gwType=parallel;",
    "inclusiva": _GW + "gwType=inclusive;",
    "tarea": _TK + "taskMarker=user;fillColor=#ffffff;",
    "sistema": _TK + "taskMarker=service;fillColor=#e8f0f6;",
    "manual": _TK + "taskMarker=manual;fillColor=#ffffff;",
    "subproceso": _TK + "taskMarker=abstract;isLoopSub=1;fillColor=#ffffff;",
}
ESTILO_CARRIL = ("swimlane;horizontal=0;startSize=40;html=1;whiteSpace=wrap;fontSize=12;fontStyle=1;fillColor=#f4f5f7;"
                 "swimlaneFillColor=#ffffff;strokeColor=#b8bec5;")
ESTILO_FLUJO = ("edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;fontSize=11;strokeColor=#4a5563;endArrow=block;"
                "endFill=1;labelBackgroundColor=#ffffff;")
CABECERA = 40            # ancho de la cabecera de cada carril
ALTO_CARRIL = 140        # alto por defecto de un carril nuevo
COLUMNA = 150            # separación horizontal entre pasos al colocar a mano
ID_NUESTRO = re.compile(r"^(ACT|GW|EV)-\d+$")


class ErrorProceso(Exception):
    pass


# ---------------------------------------------------------------- proceso (JSON)
def cargar_json(ruta):
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def guardar_json(proc, ruta):
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(proc, f, ensure_ascii=False, indent=2)
        f.write("\n")


def estructura(proc):
    """El proceso sin posiciones, ordenado de forma estable, para comparar."""
    pasos = sorted(({k: p[k] for k in ("id", "tipo", "carril", "nombre")} for p in proc["pasos"]), key=lambda p: p["id"])
    flujos = sorted(({"de": f["de"], "a": f["a"], "etiqueta": f.get("etiqueta", "") or "",
                      "discontinuo": bool(f.get("discontinuo"))} for f in proc["flujos"]),
                    key=lambda f: (f["de"], f["a"], f["etiqueta"]))
    return {"proceso": proc.get("proceso", ""), "carriles": list(proc["carriles"]), "pasos": pasos, "flujos": flujos}


def aplicar_cambios(base, cambios):
    """Aplica una lista de cambios sobre un proceso completo y devuelve el nuevo.

    Cambios admitidos (uno por elemento de la lista):
      {"poner": paso}                 añade el paso (id, tipo, carril, nombre) o cambia los campos que traiga
      {"quitar": "ACT-04"}            quita el paso y sus flujos
      {"flujo": {de, a, etiqueta?, discontinuo?}}   añade el flujo o cambia su etiqueta
      {"quitar_flujo": {de, a}}
      {"carril": "Nombre"}            añade un carril al final, para poner pasos en él en la misma lista
      {"renombrar_carril": ["Viejo", "Nuevo"]}
      {"proceso": "Nombre"}
    Un carril que se queda sin pasos desaparece; uno añadido con "carril" tiene que acabar con algún paso.
    """
    p = copy.deepcopy(base)
    pasos = {x["id"]: x for x in p["pasos"]}
    con_pasos = {x["carril"] for x in p["pasos"]}
    anadidos = set()
    for c in cambios:
        if "poner" in c:
            nuevo = c["poner"]
            if not nuevo.get("id"):
                raise ErrorProceso(f"poner: falta el id en {json.dumps(nuevo, ensure_ascii=False)}")
            if nuevo["id"] in pasos:
                pasos[nuevo["id"]].update(nuevo)
            else:
                falta = [k for k in ("tipo", "carril") if not nuevo.get(k)]
                if nuevo.get("tipo") in TAREAS and not nuevo.get("nombre"):
                    falta.append("nombre")
                if falta:
                    raise ErrorProceso(f"poner {nuevo['id']}: es un paso nuevo y le falta: {', '.join(falta)}")
                p["pasos"].append(dict(nuevo)); pasos[nuevo["id"]] = p["pasos"][-1]
                pasos[nuevo["id"]].setdefault("nombre", "")
            if pasos[nuevo["id"]].get("carril") not in p["carriles"]:
                raise ErrorProceso(f"poner {nuevo['id']}: el carril «{pasos[nuevo['id']]['carril']}» no existe "
                                   f"(si es nuevo, añádelo antes en la lista con {{\"carril\": \"…\"}})")
        elif "quitar" in c:
            pid = c["quitar"]
            if pid not in pasos:
                raise ErrorProceso(f"quitar: no existe el paso {pid}")
            p["pasos"] = [x for x in p["pasos"] if x["id"] != pid]; del pasos[pid]
            p["flujos"] = [f for f in p["flujos"] if pid not in (f["de"], f["a"])]
        elif "flujo" in c:
            f = c["flujo"]
            hit = [x for x in p["flujos"] if x["de"] == f["de"] and x["a"] == f["a"]]
            if hit:
                hit[0].update(f)
            else:
                p["flujos"].append(dict(f))
        elif "quitar_flujo" in c:
            f = c["quitar_flujo"]
            antes = len(p["flujos"])
            p["flujos"] = [x for x in p["flujos"] if not (x["de"] == f["de"] and x["a"] == f["a"])]
            if len(p["flujos"]) == antes:
                raise ErrorProceso(f"quitar_flujo: no existe {f['de']} → {f['a']}")
        elif "carril" in c:
            if c["carril"] not in p["carriles"]:
                p["carriles"].append(c["carril"]); anadidos.add(c["carril"])
        elif "renombrar_carril" in c:
            viejo, nuevo = c["renombrar_carril"]
            if viejo not in p["carriles"]:
                raise ErrorProceso(f"renombrar_carril: no existe el carril «{viejo}»")
            if nuevo in p["carriles"]:
                raise ErrorProceso(f"renombrar_carril: ya existe un carril «{nuevo}»")
            p["carriles"] = [nuevo if x == viejo else x for x in p["carriles"]]
            con_pasos = {nuevo if x == viejo else x for x in con_pasos}
            for x in p["pasos"]:
                if x["carril"] == viejo:
                    x["carril"] = nuevo
        elif "proceso" in c:
            p["proceso"] = c["proceso"]
        else:
            raise ErrorProceso(f"cambio no reconocido: {json.dumps(c, ensure_ascii=False)}")
    usados = {x["carril"] for x in p["pasos"]}
    vacios = [c for c in p["carriles"] if c in anadidos and c not in usados]
    if vacios:
        raise ErrorProceso("un carril sin pasos no se dibuja; pon algún paso en: " + ", ".join(f"«{c}»" for c in vacios))
    p["carriles"] = [c for c in p["carriles"] if c in usados]   # los que se quedan sin pasos desaparecen
    return p


def validar(proc):
    """Devuelve (errores, avisos). Los errores impiden dibujar."""
    err, av = [], []
    ids = [p.get("id") for p in proc.get("pasos", [])]
    for i in {i for i in ids if ids.count(i) > 1}:
        err.append(f"el id {i} está repetido")
    carriles = proc.get("carriles", [])
    for c in {c for c in carriles if carriles.count(c) > 1}:
        err.append(f"el carril «{c}» está repetido")
    pasos = {p.get("id"): p for p in proc.get("pasos", [])}
    for p in proc.get("pasos", []):
        falta = [k for k in ("id", "tipo", "carril", "nombre") if not p.get(k) and not (k == "nombre" and p.get("tipo") in PUERTAS | EVENTOS)]
        if falta:
            err.append(f"al paso {p.get('id', '?')} le falta: {', '.join(falta)}")
        if p.get("tipo") not in TIPOS:
            err.append(f"{p.get('id')}: tipo «{p.get('tipo')}» desconocido (usa: {', '.join(sorted(TIPOS))})")
        if p.get("carril") not in carriles:
            err.append(f"{p.get('id')}: el carril «{p.get('carril')}» no está en «carriles»")
        if p.get("tipo") in TIPOS and ID_NUESTRO.match(str(p.get("id"))) and not str(p["id"]).startswith(PREFIJO[p["tipo"]] + "-"):
            av.append(f"{p['id']} es de tipo {p['tipo']}: su código debería empezar por {PREFIJO[p['tipo']]}-")
    ent, sal = {}, {}
    for f in proc.get("flujos", []):
        for k in ("de", "a"):
            if f.get(k) not in pasos:
                err.append(f"flujo {f.get('de')} → {f.get('a')}: no existe el paso {f.get(k)}")
        sal.setdefault(f.get("de"), []).append(f); ent.setdefault(f.get("a"), []).append(f)
    if err:
        return err, av
    tipos = [p["tipo"] for p in pasos.values()]
    if "inicio" not in tipos:
        av.append("no hay evento de inicio")
    if "fin" not in tipos:
        av.append("no hay evento de fin")
    for pid, p in pasos.items():
        if p["tipo"] == "inicio" and pid in ent:
            av.append(f"{pid} es un inicio y le llega un flujo")
        if p["tipo"] == "fin" and pid in sal:
            av.append(f"{pid} es un fin y sale un flujo de él")
        if p["tipo"] != "inicio" and pid not in ent:
            av.append(f"{pid} ({p.get('nombre', '')}) no tiene flujo de entrada")
        if p["tipo"] != "fin" and pid not in sal:
            av.append(f"{pid} ({p.get('nombre', '')}) no tiene flujo de salida")
        if p["tipo"] in ("exclusiva", "inclusiva") and len(sal.get(pid, [])) > 1:
            sin = [f["a"] for f in sal[pid] if not f.get("etiqueta")]
            if sin:
                av.append(f"{pid}: las salidas hacia {', '.join(sin)} no tienen etiqueta")
    n = sum(1 for p in pasos.values() if p["tipo"] in TAREAS)
    if n > 20:
        av.append(f"{n} tareas en un diagrama: pártelo en subprocesos para que se lea bien")
    return err, av


# ---------------------------------------------------------------- escribir .drawio
def _xml_attr(s):
    return html.escape(str(s), quote=True)


def escribir_drawio(proc, geo, ruta):
    """Escribe un .drawio nuevo. `geo` = {"carriles": {nombre: (y, h)}, "ancho": w,
    "pasos": {id: (cx, cy)} (centro absoluto), "flujos": [[(x, y), ...] por flujo en el orden de proc]}."""
    celdas = ['<mxCell id="0"/>', '<mxCell id="1" parent="0"/>']
    lane_id = {}
    for i, c in enumerate(proc["carriles"], 1):
        y, h = geo["carriles"][c]
        lane_id[c] = f"carril-{i}"
        celdas.append(f'<mxCell id="{lane_id[c]}" value="{_xml_attr(c)}" style="{ESTILO_CARRIL}" vertex="1" parent="1">'
                      f'<mxGeometry y="{y:.0f}" width="{geo["ancho"]:.0f}" height="{h:.0f}" as="geometry"/></mxCell>')
    for p in proc["pasos"]:
        w, h = TAM[p["tipo"]]
        cx, cy = geo["pasos"][p["id"]]
        ly = geo["carriles"][p["carril"]][0]
        celdas.append(f'<mxCell id="{_xml_attr(p["id"])}" value="{_xml_attr(p.get("nombre", ""))}" style="{ESTILO[p["tipo"]]}" '
                      f'vertex="1" parent="{lane_id[p["carril"]]}"><mxGeometry x="{cx - w / 2:.0f}" y="{cy - ly - h / 2:.0f}" '
                      f'width="{w}" height="{h}" as="geometry"/></mxCell>')
    for i, f in enumerate(proc["flujos"], 1):
        st = ESTILO_FLUJO + ("dashed=1;" if f.get("discontinuo") else "")
        pts = geo["flujos"][i - 1] if i - 1 < len(geo.get("flujos", [])) else []
        arr = ('<Array as="points">' + "".join(f'<mxPoint x="{x:.0f}" y="{y:.0f}"/>' for x, y in pts) + "</Array>") if pts else ""
        celdas.append(f'<mxCell id="F{i:02d}" value="{_xml_attr(f.get("etiqueta", ""))}" style="{st}" edge="1" parent="1" '
                      f'source="{_xml_attr(f["de"])}" target="{_xml_attr(f["a"])}"><mxGeometry relative="1" as="geometry">{arr}'
                      f'</mxGeometry></mxCell>')
    xml = ('<mxfile host="appian-analisis-funcional"><diagram id="proceso" name="' + _xml_attr(proc.get("proceso") or "Proceso") +
           '"><mxGraphModel grid="1" gridSize="10" page="0" math="0"><root>' + "".join(celdas) +
           "</root></mxGraphModel></diagram></mxfile>")
    with open(ruta, "w", encoding="utf-8") as fh:
        fh.write(xml)


# ---------------------------------------------------------------- leer .drawio
def _estilo(s):
    d, base = {}, []
    for t in (s or "").split(";"):
        if "=" in t:
            k, v = t.split("=", 1); d[k.strip()] = v.strip()
        elif t.strip():
            base.append(t.strip())
    d["_base"] = base
    return d


def _texto(v):
    v = re.sub(r"<br\s*/?>|</div>|</p>|<div[^>]*>|<p[^>]*>", " ", v or "", flags=re.I)
    v = re.sub(r"<[^>]+>", "", v)
    return re.sub(r"\s+", " ", html.unescape(v)).strip()


class Fichero:
    """Un .drawio abierto: el árbol XML (primera página) y acceso a sus celdas."""

    def __init__(self, ruta):
        self.ruta = ruta
        self.tree = ET.parse(ruta)
        top = self.tree.getroot()
        diagramas = [top] if top.tag == "diagram" else top.findall("diagram")
        self.paginas = len(diagramas) if diagramas else 1
        if top.tag == "mxGraphModel":
            self.diagram, self.model = None, top
        else:
            if not diagramas:
                raise ErrorProceso(f"{ruta}: no parece un fichero de draw.io")
            self.diagram = diagramas[0]
            self.model = self.diagram.find("mxGraphModel")
            if self.model is None:  # contenido comprimido (deflate + base64 + URL)
                raw = zlib.decompress(base64.b64decode((self.diagram.text or "").strip()), -15)
                self.model = ET.fromstring(urllib.parse.unquote(raw.decode("utf-8")))
                self.diagram.text = None
                self.diagram.append(self.model)
        self.root = self.model.find("root")

    # celdas: el elemento que lleva el id (mxCell, o UserObject/object con un mxCell dentro)
    def celdas(self):
        for el in list(self.root):
            cell = el if el.tag == "mxCell" else el.find("mxCell")
            if cell is None:
                continue
            yield el, cell

    def por_id(self, cid):
        for el, cell in self.celdas():
            if el.get("id") == cid:
                return el, cell
        return None, None

    def etiqueta(self, el, cell):
        return _texto(el.get("label") if el is not cell else cell.get("value"))

    def poner_etiqueta(self, el, cell, texto):
        if el is not cell:
            el.set("label", texto)
        else:
            cell.set("value", texto)

    def guardar(self, ruta=None):
        ET.indent(self.tree, space="")  # sin sangría: draw.io lo lee igual y el diff queda limpio
        self.tree.write(ruta or self.ruta, encoding="utf-8", xml_declaration=False)

    def huella(self):
        """Resumen de la colocación (posiciones y puntos de los flujos): cambia si alguien mueve algo en draw.io."""
        import hashlib
        partes = []
        for el, cell in self.celdas():
            g = cell.find("mxGeometry")
            if g is None:
                continue
            pts = ";".join(f"{pt.get('x')},{pt.get('y')}" for pt in g.iter("mxPoint"))
            partes.append(f"{el.get('id')}|{cell.get('parent')}|{g.get('x')}|{g.get('y')}|{g.get('width')}|{g.get('height')}|{pts}")
        return hashlib.sha1("\n".join(sorted(partes)).encode("utf-8")).hexdigest()[:16]

    def xml_modelo(self):
        return ET.tostring(self.model, encoding="unicode")

    # ----------------------------------------------------------- interpretación
    def leer(self):
        """Devuelve (proceso, geometria, avisos). Geometría absoluta de carriles, pasos y flujos."""
        avisos = []
        info = {}
        for el, cell in self.celdas():
            cid = el.get("id")
            if cid in ("0", "1"):
                continue
            g = cell.find("mxGeometry")
            info[cid] = {"el": el, "cell": cell, "estilo": _estilo(cell.get("style")), "padre": cell.get("parent"),
                         "vertex": cell.get("vertex") == "1", "edge": cell.get("edge") == "1",
                         "x": float(g.get("x", 0)) if g is not None else 0.0, "y": float(g.get("y", 0)) if g is not None else 0.0,
                         "w": float(g.get("width", 0)) if g is not None else 0.0, "h": float(g.get("height", 0)) if g is not None else 0.0,
                         "g": g, "texto": self.etiqueta(el, cell)}

        def absoluto(cid):
            x = y = 0.0
            while cid in info:
                x += info[cid]["x"]; y += info[cid]["y"]
                cid = info[cid]["padre"]
            return x, y

        es_carril = {cid for cid, i in info.items() if i["vertex"] and ("swimlane" in i["estilo"]["_base"]
                     or i["estilo"].get("shape") in ("swimlane", "mxgraph.bpmn.swimlane"))}
        # un carril que contiene otros carriles es un pool: su nombre es el del proceso
        pools = {i["padre"] for cid, i in info.items() if cid in es_carril and i["padre"] in es_carril}
        carriles_ids = sorted(es_carril - pools, key=lambda c: absoluto(c)[1])
        nombre_pool = next((info[p]["texto"] for p in pools), "")
        carriles, geo_carril = [], {}
        for c in carriles_ids:
            nombre = info[c]["texto"] or c
            if nombre in carriles:
                avisos.append(f"hay dos carriles llamados «{nombre}»")
                nombre = f"{nombre} ({c})"
            carriles.append(nombre)
            ax, ay = absoluto(c)
            geo_carril[nombre] = (ay, info[c]["h"], ax, info[c]["w"], c)
        # vértices que son etiquetas de un flujo (hijos de una arista)
        etiquetas_flujo = {}
        for cid, i in info.items():
            if i["vertex"] and i["padre"] in info and info[i["padre"]]["edge"]:
                etiquetas_flujo.setdefault(i["padre"], []).append(i["texto"])
        # grado de cada vértice para clasificar elipses sin tipo
        ent, sal = {}, {}
        for cid, i in info.items():
            if i["edge"]:
                s, t = i["cell"].get("source"), i["cell"].get("target")
                sal[s] = sal.get(s, 0) + 1; ent[t] = ent.get(t, 0) + 1
        pasos, geo_pasos, notas = [], {}, []
        for cid, i in info.items():
            if not i["vertex"] or cid in es_carril or (i["padre"] in info and info[i["padre"]]["edge"]):
                continue
            tipo = tipo_de_estilo(i["estilo"], ent.get(cid, 0), sal.get(cid, 0))
            if tipo is None:
                if i["texto"] and es_nota(i["estilo"]):
                    notas.append(i["texto"])
                elif i["texto"]:
                    avisos.append(f"se ignora «{i['texto']}» ({cid}): no es una forma de proceso (documento, imagen…)")
                continue
            ax, ay = absoluto(cid)
            cx, cy = ax + i["w"] / 2, ay + i["h"] / 2
            carril = _carril_de(cid, info, es_carril - pools, geo_carril, cx, cy)
            if carril is None:
                avisos.append(f"{cid} («{i['texto']}») está fuera de los carriles")
                carril = "(sin carril)"
                if carril not in carriles:
                    carriles.append(carril)
            pasos.append({"id": cid, "tipo": tipo, "carril": carril, "nombre": i["texto"]})
            geo_pasos[cid] = (cx, cy, i["w"], i["h"])
        ids_pasos = {p["id"] for p in pasos}
        flujos, geo_flujos = [], []
        for cid, i in info.items():
            if not i["edge"]:
                continue
            s, t = i["cell"].get("source"), i["cell"].get("target")
            if s not in ids_pasos or t not in ids_pasos:
                avisos.append(f"el flujo {cid} no une dos pasos (le falta el origen o el destino) y se ignora")
                continue
            etiqueta = " ".join([x for x in [i["texto"]] + etiquetas_flujo.get(cid, []) if x])
            f = {"de": s, "a": t, "id": cid}
            if etiqueta:
                f["etiqueta"] = etiqueta
            if i["estilo"].get("dashed") == "1":
                f["discontinuo"] = True
            flujos.append(f)
            pts = []
            arr = i["g"].find("Array") if i["g"] is not None else None
            if arr is not None:
                ox, oy = absoluto(i["padre"]) if i["padre"] not in ("1", None) else (0.0, 0.0)
                pts = [(float(pt.get("x", 0)) + ox, float(pt.get("y", 0)) + oy) for pt in arr.findall("mxPoint")]
            geo_flujos.append(pts)
        nombre = nombre_pool or (self.diagram.get("name") if self.diagram is not None else "") or "Proceso"
        if self.paginas > 1:
            avisos.append(f"el fichero tiene {self.paginas} páginas; solo se lee la primera")
        usados = {p["carril"] for p in pasos}
        vacios = [c for c in carriles if c not in usados]
        proc = {"proceso": nombre, "carriles": carriles, "pasos": pasos, "flujos": flujos}
        geo = {"carriles": geo_carril, "pasos": geo_pasos, "flujos": geo_flujos, "vacios": vacios, "notas": notas,
               "pool": next(iter(pools), None)}
        return proc, geo, avisos


def es_nota(e):
    shape = e.get("shape") or (e["_base"][0] if e["_base"] else "")
    return shape in ("text", "note", "mxgraph.bpmn.textAnnotation") or "text" in e["_base"] or "note" in e["_base"]


def tipo_de_estilo(e, n_ent, n_sal):
    """Tipo de paso según el estilo de draw.io. None si la forma no es un paso del proceso."""
    shape = e.get("shape") or (e["_base"][0] if e["_base"] else "")
    if shape in ("text", "edgeLabel", "label", "note") or es_nota(e):
        return None
    if shape in ("mxgraph.bpmn.event", "mxgraph.bpmn.shape"):
        outline, symbol = e.get("outline", "standard"), e.get("symbol", "general")
        if symbol in ("exclusiveGw", "parallelGw", "inclusiveGw", "gateway"):
            return {"parallelGw": "paralela", "inclusiveGw": "inclusiva"}.get(symbol, "exclusiva")
        if outline == "end":
            return "fin"
        if outline == "standard":
            return "inicio"
        return {"timer": "temporizador", "message": "mensaje"}.get(symbol, "intermedio")
    if shape == "mxgraph.bpmn.gateway2":
        return {"parallel": "paralela", "inclusive": "inclusiva"}.get(e.get("gwType", "exclusive"), "exclusiva")
    if shape in ("mxgraph.bpmn.task", "mxgraph.bpmn.task2"):
        if e.get("isLoopSub") == "1" or e.get("outline") == "call":
            return "subproceso"
        return {"service": "sistema", "script": "sistema", "businessRule": "sistema", "send": "sistema",
                "manual": "manual"}.get(e.get("taskMarker", "abstract"), "tarea")
    if shape in ("rhombus",):
        return "exclusiva"
    if shape in ("ellipse", "doubleEllipse") or "ellipse" in e["_base"]:
        return "inicio" if n_ent == 0 else "fin" if n_sal == 0 else "intermedio"
    if shape in ("", "rounded", "rectangle", "process") or e.get("rounded") in ("0", "1"):
        return "tarea"
    return None


def _carril_de(cid, info, carriles, geo_carril, cx, cy):
    p = info[cid]["padre"]
    while p in info:
        if p in carriles:
            return next(n for n, g in geo_carril.items() if g[4] == p)
        p = info[p]["padre"]
    for n, (y, h, x, w, _) in geo_carril.items():   # suelto: el carril que lo contiene
        if y <= cy <= y + h and x <= cx <= x + w:
            return n
    return None


def leer(ruta):
    return Fichero(ruta).leer()


# ---------------------------------------------------------------- comparar
def comparar(antes, despues):
    """Diferencias entre dos procesos (sin posiciones). Devuelve lista de (clase, texto)."""
    a, d = estructura(antes), estructura(despues)
    out = []
    pa, pd = {p["id"]: p for p in a["pasos"]}, {p["id"]: p for p in d["pasos"]}
    # un carril renombrado: todos sus pasos pasan juntos a un carril nuevo que solo tiene esos pasos
    renombrado = {}
    nuevos_c = [c for c in d["carriles"] if c not in a["carriles"]]
    for c in [c for c in a["carriles"] if c not in d["carriles"]]:
        suyos = {i for i, p in pa.items() if p["carril"] == c}
        for n in nuevos_c:
            if suyos and suyos == {i for i, p in pd.items() if p["carril"] == n}:
                renombrado[c] = n
    for c in d["carriles"]:
        if c not in a["carriles"] and c not in renombrado.values():
            out.append(("carril", f"carril nuevo: «{c}»"))
    for c in a["carriles"]:
        if c in renombrado:
            out.append(("carril", f"carril renombrado: «{c}» → «{renombrado[c]}»"))
        elif c not in d["carriles"]:
            out.append(("carril", f"carril quitado: «{c}»"))
    for pid, p in pd.items():
        if pid not in pa:
            out.append(("paso", f"paso nuevo: {pid} {p['tipo']} «{p['nombre']}» en «{p['carril']}»"))
            continue
        q = pa[pid]
        if q["nombre"] != p["nombre"]:
            out.append(("paso", f"{pid} renombrado: «{q['nombre']}» → «{p['nombre']}»"))
        if q["tipo"] != p["tipo"]:
            out.append(("paso", f"{pid} cambia de tipo: {q['tipo']} → {p['tipo']}"))
        if q["carril"] != p["carril"] and renombrado.get(q["carril"]) != p["carril"]:
            out.append(("paso", f"{pid} cambia de carril: «{q['carril']}» → «{p['carril']}»"))
    for pid, q in pa.items():
        if pid not in pd:
            out.append(("paso", f"paso quitado: {pid} «{q['nombre']}»"))
    clave = lambda f: (f["de"], f["a"])
    fa, fd = {clave(f): f for f in a["flujos"]}, {clave(f): f for f in d["flujos"]}
    for k, f in fd.items():
        if k not in fa:
            out.append(("flujo", f"flujo nuevo: {f['de']} → {f['a']}" + (f" «{f['etiqueta']}»" if f["etiqueta"] else "")
                        + (" (discontinuo)" if f["discontinuo"] else "")))
        else:
            g = fa[k]
            if g["etiqueta"] != f["etiqueta"]:
                out.append(("flujo", f"flujo {f['de']} → {f['a']}: etiqueta «{g['etiqueta']}» → «{f['etiqueta']}»"))
            if g["discontinuo"] != f["discontinuo"]:
                out.append(("flujo", f"flujo {f['de']} → {f['a']}: " + ("pasa a discontinuo" if f["discontinuo"] else "pasa a continuo")))
    for k, g in fa.items():
        if k not in fd:
            out.append(("flujo", f"flujo quitado: {g['de']} → {g['a']}"))
    if a["proceso"] != d["proceso"]:
        out.append(("proceso", f"nombre del proceso: «{a['proceso']}» → «{d['proceso']}»"))
    return out
