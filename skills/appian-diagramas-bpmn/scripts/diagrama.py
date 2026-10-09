#!/usr/bin/env python3
"""Diagramas de proceso BPMN en draw.io: crear, actualizar, leer, comparar, PNG y BPMN 2.0.

Uso:
  diagrama.py crear proceso.json [-o carpeta|ruta.drawio]   .drawio + .png (uno por tramo) + .json (el proceso que conoce el análisis)
  diagrama.py actualizar X.drawio cambios.json [--forzar]   aplica cambios (proceso completo o lista "cambios")
  diagrama.py leer X.drawio [--posiciones]                  el proceso del .drawio en JSON
  diagrama.py comparar X.drawio [--aceptar] [--json]        qué se cambió a mano respecto a X.json
  diagrama.py png X.drawio                                  vuelve a generar X.png
  diagrama.py bpmn X.drawio [-o X.bpmn]                     exporta BPMN 2.0 con posiciones
  diagrama.py validar proceso.json                          solo valida el JSON

Junto a cada X.drawio viven X.png (para el documento; X-1.png, X-2.png… si está en tramos) y X.json (el proceso según
el análisis; lo escribe esta herramienta, no se edita a mano). Códigos de salida: 0 bien, 1 error o cambios pendientes,
2 falta un requisito: sin navegador se escribe todo menos el PNG («sin PNG»).
"""
import argparse, json, os, pathlib, re, sys
sys.dont_write_bytecode = True  # sin __pycache__ en el plugin: no se escribe fuera del proyecto
import xml.etree.ElementTree as ET

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import colocacion  # noqa: E402
import drawio_modelo as dm  # noqa: E402
import navegador  # noqa: E402


def _salida_utf8():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            pass


def _json_compacto(proc):
    """Un paso y un flujo por línea: se lee de un vistazo y gasta pocos tokens."""
    linea = lambda o: json.dumps(o, ensure_ascii=False)
    partes = [f'  "proceso": {linea(proc.get("proceso", ""))}', f'  "carriles": {linea(proc["carriles"])}']
    partes.append('  "pasos": [\n' + ",\n".join("    " + linea(p) for p in proc["pasos"]) + "\n  ]")
    partes.append('  "flujos": [\n' + ",\n".join("    " + linea(f) for f in proc["flujos"]) + "\n  ]")
    if proc.get("externos"):
        partes.append(f'  "externos": {linea(proc["externos"])}')
    if proc.get("notas"):
        partes.append('  "notas": [\n' + ",\n".join("    " + linea(n) for n in proc["notas"]) + "\n  ]")
    if proc.get("tramos"):
        partes.append('  "tramos": true')
    if proc.get("colocacion"):
        partes.append(f'  "colocacion": {linea(proc["colocacion"])}')
    return "{\n" + ",\n".join(partes) + "\n}\n"


def _limpio(proc, geo=None):
    """Proceso listo para guardar o mostrar: sin ids internos de flujos, con los datos de Appian que tengan valor y, si
    se pide, con posiciones."""
    pasos = []
    for p in proc["pasos"]:
        q = {**{k: p[k] for k in ("id", "tipo", "carril", "nombre")}, **dm.datos(p, dm.DATOS_PASO)}
        if geo is not None and p["id"] in geo["pasos"]:
            q["posicion"] = [round(v) for v in geo["pasos"][p["id"]][:2]]
        pasos.append(q)
    flujos = []
    for f in proc["flujos"]:
        g = {"de": f["de"], "a": f["a"]}
        if f.get("etiqueta"):
            g["etiqueta"] = f["etiqueta"]
        if f.get("discontinuo"):
            g["discontinuo"] = True
        if f.get("defecto"):
            g["defecto"] = True
        g.update(dm.datos(f, dm.DATOS_FLUJO))
        flujos.append(g)
    out = {"proceso": proc.get("proceso", ""), "carriles": list(proc["carriles"]), "pasos": pasos, "flujos": flujos}
    if proc.get("externos"):
        out["externos"] = list(proc["externos"])
    if proc.get("notas"):
        out["notas"] = [{"paso": n["paso"], "texto": n.get("texto", "")} for n in proc["notas"]]
    if proc.get("tramos"):
        out["tramos"] = True
    return out


def _escribir_json(proc, ruta, drawio=None, automatica=False):
    """Guarda el proceso que conoce el análisis. Si la colocación la acaba de hacer esta herramienta,
    guarda también su huella: mientras nadie mueva nada en draw.io, se podrá recolocar entero sin perder trabajo."""
    datos = _limpio(proc)
    if drawio is not None:
        datos["colocacion"] = {"modo": "automatica", "huella": dm.Fichero(str(drawio)).huella()} if automatica else {"modo": "manual"}
    pathlib.Path(ruta).write_text(_json_compacto(datos), encoding="utf-8")


def _rutas(drawio):
    d = pathlib.Path(drawio)
    return d, d.with_suffix(".png"), d.with_suffix(".json")


def _informe_validacion(proc):
    err, av = dm.validar(proc)
    for e in err:
        print(f"ERROR: {e}", file=sys.stderr)
    for a in av:
        print(f"aviso: {a}")
    return not err


ANCHO_PNG_MAX = 3200   # px del PNG: más no se aprecia en un documento y solo pesa


def _pngs(drawio, hojas):
    """Los PNG de un .drawio: X.png, o X-1.png, X-2.png… si está en tramos."""
    d = pathlib.Path(drawio)
    return [d.with_suffix(".png")] if hojas == 1 else [d.with_name(f"{d.stem}-{k}.png") for k in range(1, hojas + 1)]


def _png(drawio):
    """Pinta el PNG de cada página del proceso y quita los que sobren de una versión con otros tramos. Sin navegador,
    lanza navegador.SinNavegador sin tocar nada."""
    f = dm.Fichero(str(drawio))
    hojas = f.hojas_png()
    destinos = _pngs(drawio, len(hojas))
    pisaria = [p.name for p in destinos if p.with_suffix(".drawio") != pathlib.Path(drawio) and p.with_suffix(".drawio").exists()]
    if pisaria:
        raise dm.ErrorProceso(f"la imagen de un tramo pisaría la de otro diagrama ({', '.join(pisaria)}): cambia el "
                              "nombre de uno de los dos")
    trabajos = []
    for (xml, ancho), destino in zip(hojas, destinos):
        aviso = colocacion.aviso_ancho(ancho)
        if aviso:
            print(f"aviso: {aviso}" + (f" ({destino.name})" if len(hojas) > 1 else ""))
        escala = max(0.75, min(2.0, ANCHO_PNG_MAX / (ancho + 24)))   # nítido en un documento, sin pesar de más
        trabajos.append((xml, destino, escala))
    navegador.pintar_pngs(trabajos)
    d = pathlib.Path(drawio)

    def ajeno(p):   # X-2.png es de otro diagrama si existe X-2.drawio
        return p.with_suffix(".drawio") != d and p.with_suffix(".drawio").exists()
    # los de cuando tenía otros tramos (o ninguno) ya no son de este diagrama
    viejos = [p for p in d.parent.iterdir() if p not in destinos and not ajeno(p)
              and (p.name == f"{d.stem}.png" or re.fullmatch(re.escape(d.stem) + r"-\d+\.png", p.name))]
    for p in viejos:
        p.unlink()
        print(f"quitado {p.name}: es de una versión con otros tramos")
    return destinos


def _imagen(drawio):
    """Los PNG, o el aviso «sin PNG» si no hay navegador: True si se han pintado."""
    try:
        for p in _png(drawio):
            print(f"   {p}")
        return True
    except navegador.SinNavegador as e:
        print("aviso: sin PNG: no hay navegador para pintar la imagen. Lo demás está hecho; cuando lo haya, "
              f"«diagrama.py png {pathlib.Path(drawio).name}» la genera.")
        print(str(e), file=sys.stderr)
        return False


# ---------------------------------------------------------------- crear
def _geometria_por_posiciones(proc):
    """Cuando cada paso trae «posicion» (por ejemplo, leída de Appian): x de la posición, carriles apilados."""
    xs = [p["posicion"][0] for p in proc["pasos"]]
    x0 = min(xs)
    geo = {"carriles": {}, "pasos": {}, "flujos": []}
    y = 0
    for c in proc["carriles"]:
        filas = {}
        for p in (p for p in proc["pasos"] if p["carril"] == c):
            cx = dm.CABECERA + 70 + (p["posicion"][0] - x0)
            fila = 0
            while any(abs(cx - ox) < 150 for ox in filas.get(fila, [])):
                fila += 1
            filas.setdefault(fila, []).append(cx)
            geo["pasos"][p["id"]] = (cx, fila)
        h = max(dm.ALTO_CARRIL, 60 + 110 * (len(filas) or 1))
        for p in (p for p in proc["pasos"] if p["carril"] == c):
            cx, fila = geo["pasos"][p["id"]]
            geo["pasos"][p["id"]] = (cx, y + 70 + 110 * fila)
        geo["carriles"][c] = (y, h)
        y += h
    geo["ancho"] = max(cx for cx, _ in geo["pasos"].values()) + 120
    geo["flujos"] = [[] for _ in proc["flujos"]]
    return geo


def _motor(procs, por_capas=False):
    """Geometría ajustada de cada proceso: la del motor de Mermaid o, sin navegador (o si se pide), la colocación por
    capas, que no necesita navegador y mide lo que se espera (la de los tramos)."""
    eventos = dm.FORMAS_EVENTO
    geos = None
    if not por_capas:
        try:
            geos = navegador.colocar_varios(procs, eventos, dm.PUERTAS, dm.CABECERA)
        except navegador.SinNavegador:
            pass
    if geos is None:
        geos = [colocacion.por_capas(p, eventos, dm.PUERTAS, dm.CABECERA) for p in procs]
    return [colocacion.ajustar(p, g, dm.TAM, eventos, dm.PUERTAS, dm.CABECERA) for p, g in zip(procs, geos)]


def _colocar(proc, posiciones=True):
    """Las páginas del dibujo, [(proceso, geometría)]: una o, si el proceso lleva «tramos» y no cabe en una página, una
    por tramo. La geometría, la del motor (o la de las posiciones dadas) ajustada para que nada se pise."""
    cabe = lambda geo: geo["ancho"] <= colocacion.ANCHO_LEGIBLE      # noqa: E731
    if posiciones and all(p.get("posicion") for p in proc["pasos"]):
        geo = colocacion.ajustar(proc, _geometria_por_posiciones(proc), dm.TAM, dm.EVENTOS, dm.PUERTAS, dm.CABECERA)
        if not proc.get("tramos") or cabe(geo):
            return [(proc, geo)]
    if not proc.get("tramos") or \
            colocacion.ancho_estimado(proc, dm.EVENTOS, dm.PUERTAS, dm.CABECERA) <= colocacion.ANCHO_LEGIBLE:
        geo = _motor([proc])[0]
        if not proc.get("tramos") or cabe(geo):
            return [(proc, geo)]
    # en tramos, siempre por capas: el motor de Mermaid coloca los cortes de forma irregular y no se sabe lo que medirá
    grupos = colocacion.tramos(proc, dm.EVENTOS, dm.PUERTAS, dm.TAREAS, dm.CABECERA)
    while True:   # un tramo que aun así no cabe se parte en dos (si tiene más de una capa) y se colocan de nuevo
        procs = dm.partir(proc, grupos)
        geos = _motor(procs, por_capas=True)
        nuevos = []
        for g, geo in zip(grupos, geos):
            nuevos += [g] if cabe(geo) else colocacion.partir_en_dos(proc, g, dm.TAREAS)
        if len(nuevos) == len(grupos):
            return list(zip(procs, geos))
        grupos = nuevos


def crear(a):
    proc = dm.cargar_json(a.proceso)
    if not _informe_validacion(proc):
        return 1
    destino = pathlib.Path(a.o) if a.o else pathlib.Path(a.proceso).with_suffix(".drawio")
    if destino.suffix != ".drawio":
        destino.mkdir(parents=True, exist_ok=True)
        destino = destino / (pathlib.Path(a.proceso).stem + ".drawio")
    destino.parent.mkdir(parents=True, exist_ok=True)
    if destino.exists() and not a.forzar:
        print(f"ERROR: {destino} ya existe. Para cambiarlo usa «actualizar» (respeta lo editado a mano) "
              "o repite con --forzar para rehacerlo entero.", file=sys.stderr)
        return 1
    paginas = _colocar(proc)
    drawio, png, js = _rutas(destino)
    dm.escribir_paginas(paginas, drawio)
    _escribir_json(proc, js, drawio, automatica=True)
    print(f"OK {drawio}" + (f" ({len(paginas)} tramos)" if len(paginas) > 1 else "") + f"\n   {js}")
    return 0 if _imagen(drawio) else 2


# ---------------------------------------------------------------- edición del .drawio
class Editor:
    """Cambios puntuales sobre un .drawio existente, sin tocar lo demás."""

    def __init__(self, ruta):
        self.f = dm.Fichero(str(ruta))
        self.recargar()

    def recargar(self):
        self.proc, self.geo, self.avisos = self.f.leer()

    # -- acceso a celdas
    def _cell(self, cid):
        el, cell = self.f.por_id(cid)
        if cell is None:
            raise dm.ErrorProceso(f"no encuentro la celda {cid}")
        return el, cell

    def _geom(self, cid):
        return self._cell(cid)[1].find("mxGeometry")

    def _abs_padre(self, cid):
        """Origen absoluto del padre de la celda."""
        info = {el.get("id"): cell for el, cell in self.f.celdas()}
        x = y = 0.0
        p = info[cid].get("parent")
        while p in info and p not in ("0", "1"):
            g = info[p].find("mxGeometry")
            if g is not None:
                x += float(g.get("x", 0)); y += float(g.get("y", 0))
            p = info[p].get("parent")
        return x, y

    def centro(self, cid):
        g = self._geom(cid)
        ox, oy = self._abs_padre(cid)
        return ox + float(g.get("x", 0)) + float(g.get("width", 0)) / 2, oy + float(g.get("y", 0)) + float(g.get("height", 0)) / 2

    def poner_centro(self, cid, cx, cy):
        g = self._geom(cid)
        ox, oy = self._abs_padre(cid)
        g.set("x", f"{cx - ox - float(g.get('width', 0)) / 2:.0f}")
        g.set("y", f"{cy - oy - float(g.get('height', 0)) / 2:.0f}")

    def carril_id(self, nombre):
        return self.geo["carriles"][nombre][4]

    def carril_caja(self, nombre):
        y, h, x, w, _ = self.geo["carriles"][nombre]
        return x, y, w, h

    def ref(self, nombre):
        """Id de la celda de un paso o de un participante externo."""
        e = self.geo.get("externos", {}).get(nombre)
        return e[4] if e else nombre

    def _externos_ids(self):
        return {g[4] for g in self.geo.get("externos", {}).values()}

    # -- operaciones de geometría global
    def desplazar_derecha(self, desde_x, dx):
        """Hace sitio: todo lo que está a la derecha de desde_x se mueve dx; los carriles se ensanchan."""
        carriles = {g[4] for g in self.geo["carriles"].values()} | self._externos_ids()
        for el, cell in self.f.celdas():
            cid = el.get("id")
            g = cell.find("mxGeometry")
            if g is None:
                continue
            if cid in carriles or (cell.get("vertex") == "1" and "swimlane" in (cell.get("style") or "")):
                g.set("width", f"{float(g.get('width', 0)) + dx:.0f}")
                continue
            if cell.get("vertex") == "1":
                par = cell.get("parent")
                if par not in ("1",) and par not in carriles:
                    continue  # etiquetas de flujo y contenido de otras formas se mueven con su padre
                cx, _ = self.centro(cid)
                if cx > desde_x:
                    g.set("x", f"{float(g.get('x', 0)) + dx:.0f}")
            elif cell.get("edge") == "1":
                arr = g.find("Array")
                if arr is not None:
                    for pt in arr.findall("mxPoint"):
                        if float(pt.get("x", 0)) > desde_x:
                            pt.set("x", f"{float(pt.get('x', 0)) + dx:.0f}")

    def desplazar_abajo(self, desde_y, dy, excepto=()):
        """Carriles y puntos por debajo de desde_y bajan dy (o suben, si dy < 0)."""
        carriles = {g[4] for g in self.geo["carriles"].values()}
        for el, cell in self.f.celdas():
            cid = el.get("id")
            g = cell.find("mxGeometry")
            if g is None or cid in excepto:
                continue
            if cid in carriles or (cell.get("parent") == "1" and cell.get("vertex") == "1"):
                y = float(g.get("y", 0))
                if y >= desde_y:
                    g.set("y", f"{y + dy:.0f}")
            elif cell.get("edge") == "1":
                arr = g.find("Array")
                if arr is not None:
                    for pt in arr.findall("mxPoint"):
                        if float(pt.get("y", 0)) >= desde_y:
                            pt.set("y", f"{float(pt.get('y', 0)) + dy:.0f}")

    # -- carriles
    def anadir_carril(self, nombre):
        ultimos = sorted(self.geo["carriles"].values(), key=lambda g: g[0])
        if ultimos:
            y, h, x, w, cid = ultimos[-1]
            _, ultimo = self._cell(cid)
            padre = ultimo.get("parent")
            gy = float(ultimo.find("mxGeometry").get("y", 0)) + h
            gx = float(ultimo.find("mxGeometry").get("x", 0))
            estilo = ultimo.get("style") or dm.ESTILO_CARRIL
        else:
            padre, gx, gy, w, estilo = "1", 0.0, 0.0, 800.0, dm.ESTILO_CARRIL
        if self.geo.get("externos"):   # los participantes externos, debajo de los carriles, bajan para hacer sitio
            self.desplazar_abajo(gy, dm.ALTO_CARRIL)
        nuevo_id = self._id_libre("carril-")
        cell = ET.SubElement(self.f.root, "mxCell", {"id": nuevo_id, "value": nombre, "style": estilo, "vertex": "1", "parent": padre})
        ET.SubElement(cell, "mxGeometry", {"x": f"{gx:.0f}", "y": f"{gy:.0f}", "width": f"{w:.0f}",
                                           "height": str(dm.ALTO_CARRIL), "as": "geometry"})
        self.recargar()

    def quitar_carril(self, nombre):
        y, h, x, w, cid = self.geo["carriles"][nombre]
        hijos = [el.get("id") for el, cell in self.f.celdas() if cell.get("parent") == cid]
        if hijos:
            return False
        el, _ = self._cell(cid)
        self.f.root.remove(el)
        self.desplazar_abajo(y + h - 1, -h)
        self.recargar()
        return True

    def renombrar_carril(self, viejo, nuevo):
        el, cell = self._cell(self.carril_id(viejo))
        self.f.poner_etiqueta(el, cell, nuevo)
        self.recargar()

    # -- pasos
    def _id_libre(self, prefijo):
        usados = {el.get("id") for el, _ in self.f.celdas()}
        n = 1
        while f"{prefijo}{n}" in usados or f"{prefijo}{n:02d}" in usados:
            n += 1
        return f"{prefijo}{n}"

    def quitar_paso(self, pid):
        notas = set(self.geo.get("ids_nota", []))
        quitar = {pid} | {el.get("id") for el, cell in self.f.celdas()
                          if cell.get("source") == pid or cell.get("target") == pid or cell.get("parent") == pid}
        quitar |= {cell.get("source") for el, cell in self.f.celdas()   # sus notas
                   if cell.get("target") == pid and cell.get("source") in notas}
        quitar |= {cell.get("target") for el, cell in self.f.celdas() if cell.get("source") == pid and cell.get("target") in notas}
        for el, cell in list(self.f.celdas()):
            if el.get("id") in quitar:
                self.f.root.remove(el)

    def cambiar_paso(self, pid, nuevo, antes):
        el, cell = self._cell(pid)
        if nuevo.get("nombre", "") != antes["nombre"]:
            self.f.poner_etiqueta(el, cell, nuevo.get("nombre", ""))
        if nuevo["tipo"] != antes["tipo"]:
            cx, cy = self.centro(pid)
            cell.set("style", dm.ESTILO[nuevo["tipo"]])
            w, h = dm.TAM[nuevo["tipo"]]
            g = cell.find("mxGeometry"); g.set("width", str(w)); g.set("height", str(h))
            self.poner_centro(pid, cx, cy)
        if nuevo["carril"] != antes["carril"]:
            cx, _ = self.centro(pid)
            x, y, w, h = self.carril_caja(nuevo["carril"])
            cell.set("parent", self.carril_id(nuevo["carril"]))
            self.poner_centro(pid, cx, self._fila_libre(nuevo["carril"], cx, pid))
            self._limpiar_puntos(pid)
        if dm.datos(nuevo, dm.DATOS_PASO) != dm.datos(antes, dm.DATOS_PASO):
            self.f.poner_datos(el, cell, nuevo, dm.DATOS_PASO)

    def _limpiar_puntos(self, pid):
        for el, cell in self.f.celdas():
            if cell.get("edge") == "1" and pid in (cell.get("source"), cell.get("target")):
                g = cell.find("mxGeometry")
                arr = g.find("Array") if g is not None else None
                if arr is not None:
                    g.remove(arr)

    def _fila_libre(self, carril, cx, excepto=None):
        """y para un paso en ese carril y esa x sin pisar otro paso; si no cabe, el carril crece."""
        x, y, w, h = self.carril_caja(carril)
        ocupadas = []
        for p in self.proc["pasos"]:
            if p["carril"] == carril and p["id"] != excepto and p["id"] in self.geo["pasos"]:
                px, py = self.centro(p["id"])
                if abs(px - cx) < 140:
                    ocupadas.append(py)
        filas = []
        for q in self.proc["pasos"]:
            if q["carril"] == carril and q["id"] != excepto and q["id"] in self.geo["pasos"]:
                filas.append(round(self.centro(q["id"])[1]))
        preferidas = sorted(set(filas), key=lambda v: -filas.count(v))
        for cand in preferidas + [y + h / 2] + [y + 55 + 100 * k for k in range(int(h // 100) + 1)]:
            if y + 30 <= cand <= y + h - 30 and all(abs(cand - o) >= 95 for o in ocupadas):
                return cand
        # no cabe: el carril crece 100 y los de debajo bajan
        _, cell = self._cell(self.carril_id(carril))
        g = cell.find("mxGeometry")
        g.set("height", f"{h + 100:.0f}")
        self.desplazar_abajo(y + h, 100, excepto={self.carril_id(carril)})
        self.recargar()
        return y + h + 50

    def anadir_paso(self, p, ancla, lado):
        """Coloca un paso nuevo junto al ancla (paso ya dibujado): a su derecha (lado=1) o en su lugar,
        empujando el ancla y lo que sigue (lado=0). Sin ancla, al final del carril."""
        if ancla:
            ax, ay = self.centro(ancla)
            if lado == 1:
                self.desplazar_derecha(ax + 1, dm.COLUMNA); cx = ax + dm.COLUMNA
            else:
                self.desplazar_derecha(ax - 1, dm.COLUMNA); cx = ax
            self.recargar()
            anc = next(q for q in self.proc["pasos"] if q["id"] == ancla)
            cy = ay if anc["carril"] == p["carril"] else None
        else:
            xs = [self.centro(q["id"])[0] for q in self.proc["pasos"]]
            cx = (max(xs) + dm.COLUMNA) if xs else dm.CABECERA + 80
            cy = None
            x, y, w, h = self.carril_caja(p["carril"])
            if cx + 80 > x + w:
                self._ensanchar(cx + 80 - (x + w))
                self.recargar()
        if cy is None or not self._libre(p["carril"], cx, cy):
            cy = self._fila_libre(p["carril"], cx)
        w, h = dm.TAM[p["tipo"]]
        lx, ly = self._origen(self.carril_id(p["carril"]))
        _, cell = self.f.nueva_celda(p["id"], p.get("nombre", ""), {"style": dm.ESTILO[p["tipo"]], "vertex": "1",
                                                                     "parent": self.carril_id(p["carril"])}, dm.DATOS_PASO, p)
        ET.SubElement(cell, "mxGeometry", {"x": f"{cx - lx - w / 2:.0f}", "y": f"{cy - ly - h / 2:.0f}",
                                           "width": str(w), "height": str(h), "as": "geometry"})
        self.recargar()

    def _ensanchar(self, dx):
        for g in self.geo["carriles"].values():
            _, cell = self._cell(g[4])
            geo = cell.find("mxGeometry"); geo.set("width", f"{float(geo.get('width', 0)) + dx:.0f}")

    def _origen(self, cid):
        g = self._geom(cid)
        ox, oy = self._abs_padre(cid)
        return ox + float(g.get("x", 0)), oy + float(g.get("y", 0))

    def _libre(self, carril, cx, cy):
        for q in self.proc["pasos"]:
            if q["carril"] == carril:
                qx, qy = self.centro(q["id"])
                if abs(qx - cx) < 140 and abs(qy - cy) < 95:
                    return False
        return True

    # -- participantes externos y notas
    def anadir_externo(self, nombre):
        cajas = [(y, h, x, w) for y, h, x, w, _ in list(self.geo["carriles"].values()) + list(self.geo.get("externos", {}).values())]
        y = max((a + b for a, b, _, _ in cajas), default=0) + colocacion.EXTERNO_HUECO
        x = min((c for _, _, c, _ in cajas), default=0)
        w = max((c + d for _, _, c, d in cajas), default=800) - x
        cell = ET.SubElement(self.f.root, "mxCell", {"id": self._id_libre("externo-"), "value": nombre, "style": dm.ESTILO_EXTERNO,
                                                     "vertex": "1", "parent": "1"})
        ET.SubElement(cell, "mxGeometry", {"x": f"{x:.0f}", "y": f"{y:.0f}", "width": f"{w:.0f}",
                                           "height": str(colocacion.EXTERNO_ALTO), "as": "geometry"})
        self.recargar()

    def quitar_externo(self, nombre):
        cid = self.ref(nombre)
        for el, cell in list(self.f.celdas()):
            if el.get("id") == cid or cell.get("source") == cid or cell.get("target") == cid:
                self.f.root.remove(el)
        self.recargar()

    def anadir_nota(self, n):
        """Una nota nueva encima de su paso (debajo si no cabe en el carril), unida a él. En horizontal, dentro del
        carril: sin pisar su cabecera y, si no cabe a la derecha, los carriles se ensanchan."""
        paso = next(q for q in self.proc["pasos"] if q["id"] == n["paso"])
        cx, cy = self.centro(n["paso"])
        pw, h = dm.TAM[paso["tipo"]]
        alto, ancho = colocacion.alto_nota(n.get("texto")), colocacion.ancho_nota(n.get("texto"))
        lx, ly = self._origen(self.carril_id(paso["carril"]))
        x, y, w, hc = self.carril_caja(paso["carril"])
        nx = max(cx - ancho / 2, x + dm.CABECERA + 6)
        if nx + ancho > x + w - 6:
            self._ensanchar(nx + ancho - (x + w - 6))
            self.recargar()
        arriba = cy - h / 2 - colocacion.NOTA_HUECO - alto >= y + 4
        ny = cy - h / 2 - colocacion.NOTA_HUECO - alto if arriba else cy + h / 2 + colocacion.NOTA_HUECO
        nid = self._id_libre("NOTA-")
        cell = ET.SubElement(self.f.root, "mxCell", {"id": nid, "value": n.get("texto", ""), "style": dm.ESTILO_NOTA,
                                                     "vertex": "1", "parent": self.carril_id(paso["carril"])})
        ET.SubElement(cell, "mxGeometry", {"x": f"{nx - lx:.0f}", "y": f"{ny - ly:.0f}",
                                           "width": f"{ancho:.0f}", "height": f"{alto:.0f}", "as": "geometry"})
        asociacion = dm.entrada_asociacion("arriba" if arriba else "abajo", (nx, ancho), (cx - pw / 2, pw))
        e = ET.SubElement(self.f.root, "mxCell", {"id": self._id_libre("A"), "value": "", "edge": "1", "parent": "1",
                                                  "style": dm.ESTILO_ASOCIACION + asociacion,
                                                  "source": nid, "target": n["paso"]})
        ET.SubElement(e, "mxGeometry", {"relative": "1", "as": "geometry"})
        self.recargar()

    def quitar_nota(self, n):
        for nid, actual in zip(self.geo.get("ids_nota", []), self.proc.get("notas", [])):
            if actual == n:
                for el, cell in list(self.f.celdas()):
                    if el.get("id") == nid or nid in (cell.get("source"), cell.get("target")):
                        self.f.root.remove(el)
                self.recargar()
                return

    def reajustar_mensajes(self):
        """Los flujos de mensaje, en vertical entre su paso y su participante (tras mover o ensanchar)."""
        ext = {g[4]: g for g in self.geo.get("externos", {}).values()}
        for el, cell in self.f.celdas():
            s, t = cell.get("source"), cell.get("target")
            if cell.get("edge") != "1" or (s not in ext and t not in ext):
                continue
            paso, pool = (s, ext[t]) if t in ext else (t, ext[s])
            if paso in ext:
                continue
            cx, _ = self.centro(paso)
            rel = (cx - pool[2]) / pool[3] if pool[3] else 0.5
            base = ";".join(x for x in (cell.get("style") or "").split(";")
                            if x and not x.startswith(("exitX", "exitY", "exitDx", "exitDy", "entryX", "entryY", "entryDx", "entryDy")))
            puntos = (f"exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX={rel:.4f};entryY=0;entryDx=0;entryDy=0;" if t in ext else
                      f"exitX={rel:.4f};exitY=0;exitDx=0;exitDy=0;entryX=0.5;entryY=1;entryDx=0;entryDy=0;")
            cell.set("style", base + ";" + puntos)

    # -- flujos
    def quitar_flujo(self, de, a):
        de, a = self.ref(de), self.ref(a)
        for el, cell in list(self.f.celdas()):
            if cell.get("edge") == "1" and cell.get("source") == de and cell.get("target") == a:
                hijos = [e for e, c in self.f.celdas() if c.get("parent") == el.get("id")]
                for h in hijos:
                    self.f.root.remove(h)
                self.f.root.remove(el)
                return

    def poner_flujo(self, f):
        de, a = self.ref(f["de"]), self.ref(f["a"])
        mensaje = de in self._externos_ids() or a in self._externos_ids()
        for el, cell in self.f.celdas():
            if cell.get("edge") == "1" and cell.get("source") == de and cell.get("target") == a:
                for e, c in list(self.f.celdas()):  # etiquetas sueltas del flujo: se sustituyen por la etiqueta
                    if c.get("parent") == el.get("id") and c.get("vertex") == "1":
                        self.f.root.remove(e)
                self.f.poner_etiqueta(el, cell, f.get("etiqueta", ""))
                self.f.poner_datos(el, cell, f, dm.DATOS_FLUJO)
                if mensaje:
                    return
                estilo = dm._estilo(cell.get("style"))
                if bool(f.get("discontinuo")) != (estilo.get("dashed") == "1"):
                    base = ";".join(t for t in (cell.get("style") or "").split(";") if t and not t.startswith("dashed="))
                    cell.set("style", base + (";dashed=1;" if f.get("discontinuo") else ";"))
                if bool(f.get("defecto")) != (estilo.get("startArrow") == "dash"):
                    base = ";".join(t for t in (cell.get("style") or "").split(";")
                                    if t and not t.startswith(("startArrow=", "startFill=", "startSize=")))
                    cell.set("style", base + ";" + (dm.DEFECTO if f.get("defecto") else ""))
                return
        n = 1
        usados = {el.get("id") for el, _ in self.f.celdas()}
        while f"F{n:02d}" in usados:
            n += 1
        estilo = dm.ESTILO_MENSAJE if mensaje else dm.estilo_flujo(f)
        _, cell = self.f.nueva_celda(f"F{n:02d}", f.get("etiqueta", ""), {"style": estilo, "edge": "1", "parent": "1",
                                                                          "source": de, "target": a}, dm.DATOS_FLUJO, f)
        ET.SubElement(cell, "mxGeometry", {"relative": "1", "as": "geometry"})

    # -- ids
    def renombrar_id(self, viejo, nuevo):
        for el, cell in self.f.celdas():
            if el.get("id") == viejo:
                el.set("id", nuevo)
            for k in ("source", "target", "parent"):
                if cell.get(k) == viejo:
                    cell.set(k, nuevo)


def _orden_insercion(nuevos, flujos, dibujados):
    """Primero los que cuelgan de algo ya dibujado; así cada paso nuevo tiene ancla."""
    pendientes, orden, hechos = list(nuevos), [], set(dibujados)
    while pendientes:
        elegido = next((p for p in pendientes if any(f["a"] == p["id"] and f["de"] in hechos for f in flujos)), None) \
            or next((p for p in pendientes if any(f["de"] == p["id"] and f["a"] in hechos for f in flujos)), None) \
            or pendientes[0]
        pendientes.remove(elegido); orden.append(elegido); hechos.add(elegido["id"])
    return orden


def aplicar(editor, nuevo):
    """Lleva el .drawio del editor al proceso `nuevo` cambiando solo lo necesario. Devuelve avisos."""
    avisos = []
    actual = editor.proc
    pa = {p["id"]: p for p in actual["pasos"]}
    pn = {p["id"]: p for p in nuevo["pasos"]}
    # 1. carriles: renombres (mismo conjunto de pasos) y altas
    quitados = [c for c in actual["carriles"] if c not in nuevo["carriles"]]
    anadidos = [c for c in nuevo["carriles"] if c not in actual["carriles"]]
    for c in list(quitados):
        suyos = {p["id"] for p in actual["pasos"] if p["carril"] == c}
        gemelo = next((n for n in anadidos if suyos and {p["id"] for p in nuevo["pasos"] if p["carril"] == n} == suyos), None)
        if gemelo:
            editor.renombrar_carril(c, gemelo)
            quitados.remove(c); anadidos.remove(gemelo)
            for p in actual["pasos"]:
                if p["carril"] == c:
                    p["carril"] = gemelo
    for c in anadidos:
        editor.anadir_carril(c)
    # participantes externos: los quitados se van con sus flujos de mensaje; los nuevos, debajo de todo
    ext_n = list(nuevo.get("externos") or [])
    for e in actual.get("externos") or []:
        if e not in ext_n:
            editor.quitar_externo(e)
    for e in ext_n:
        if e not in (actual.get("externos") or []):
            editor.anadir_externo(e)
    # 2. flujos que desaparecen y pasos que desaparecen
    clave = lambda f: (f["de"], f["a"])
    fn = {clave(f): f for f in nuevo["flujos"]}
    for f in actual["flujos"]:
        if clave(f) not in fn and (f["de"] in pn or f["de"] in ext_n) and (f["a"] in pn or f["a"] in ext_n):
            editor.quitar_flujo(f["de"], f["a"])
    for pid in pa:
        if pid not in pn:
            editor.quitar_paso(pid)
    editor.recargar()
    # 3. pasos que cambian
    for pid, p in pn.items():
        if pid in pa and (p["tipo"], p.get("nombre", ""), p["carril"], dm.datos(p, dm.DATOS_PASO)) != \
                (pa[pid]["tipo"], pa[pid]["nombre"], pa[pid]["carril"], dm.datos(pa[pid], dm.DATOS_PASO)):
            editor.cambiar_paso(pid, p, pa[pid])
            editor.recargar()
    # 4. pasos nuevos, junto a su predecesor
    dibujados = {p["id"] for p in editor.proc["pasos"]}
    for p in _orden_insercion([p for pid, p in pn.items() if pid not in pa], nuevo["flujos"], dibujados):
        pred = next((f["de"] for f in nuevo["flujos"] if f["a"] == p["id"] and f["de"] in dibujados), None)
        suc = next((f["a"] for f in nuevo["flujos"] if f["de"] == p["id"] and f["a"] in dibujados), None)
        editor.anadir_paso(p, pred or suc, 1 if pred else 0)
        dibujados.add(p["id"])
    # 5. flujos nuevos o cambiados
    fa = {clave(f): f for f in actual["flujos"]}
    for k, f in fn.items():
        g = fa.get(k)
        if g is None or any((g.get(c) or "") != (f.get(c) or "") for c in ("etiqueta", "discontinuo", "defecto")) \
                or dm.datos(g, dm.DATOS_FLUJO) != dm.datos(f, dm.DATOS_FLUJO):
            editor.poner_flujo(f)
    editor.recargar()
    # notas: las quitadas y las nuevas (encima de su paso)
    notas_n = [{"paso": n["paso"], "texto": n.get("texto", "")} for n in nuevo.get("notas") or []]
    for n in list(editor.proc.get("notas") or []):
        if n not in notas_n:
            editor.quitar_nota(n)
    for n in notas_n:
        if n not in (editor.proc.get("notas") or []):
            editor.anadir_nota(n)
    editor.reajustar_mensajes()
    editor.recargar()
    # 6. carriles vacíos
    for c in quitados:
        if c in editor.geo["carriles"] and not editor.quitar_carril(c):
            avisos.append(f"el carril «{c}» ya no tiene pasos, pero conserva otras formas: quítalo a mano si sobra")
    # 7. nombre del proceso: la etiqueta del pool si lo hay; si no, el nombre de la página
    if nuevo.get("proceso"):
        if editor.geo.get("pool"):
            el, cell = editor._cell(editor.geo["pool"])
            editor.f.poner_etiqueta(el, cell, nuevo["proceso"])
        elif editor.f.diagram is not None:
            editor.f.diagram.set("name", nuevo["proceso"])
    return avisos


def recolocar(editor, nuevo, drawio):
    """Vuelve a colocar todo el diagrama (nadie lo ha movido a mano), conservando el estilo de lo que ya existía. Las
    páginas del proceso (una, o una por tramo) se sustituyen por las nuevas; las demás no se tocan."""
    antes = {el.get("id"): cell.get("style") for el, cell in editor.f.celdas()}
    tipos_antes = {p["id"]: p["tipo"] for p in editor.proc["pasos"]}
    carril_estilo = {n: antes.get(g[4]) for n, g in editor.geo["carriles"].items()}
    paginas = _colocar(nuevo, posiciones=False)
    lados = {pid: lado for _, geo in paginas for pid, lado in geo.get("etiquetas", {}).items()}
    editor.f.poner_paginas(dm.diagramas(paginas))
    tipo_nuevo = {p["id"]: p["tipo"] for p in nuevo["pasos"]}
    for el, cell in editor.f.celdas():
        cid = el.get("id")
        if cid in tipos_antes and tipo_nuevo.get(cid) == tipos_antes[cid] and antes.get(cid):
            cell.set("style", dm.con_lado(antes[cid], lados.get(cid)))   # el lado de la etiqueta es el nuevo
        if cell.get("vertex") == "1" and "swimlane" in (cell.get("style") or "") and carril_estilo.get(cell.get("value")):
            cell.set("style", carril_estilo[cell.get("value")])
    editor.recargar()
    return []


def actualizar(a):
    drawio, png, js = _rutas(a.drawio)
    ed = Editor(drawio)
    if js.exists():
        base = dm.cargar_json(js)
        if dm.comparar(base, ed.proc):
            if not a.forzar:
                print(f"ERROR: {drawio.name} tiene cambios hechos a mano que el análisis aún no recoge.\n"
                      f"Revísalos con: diagrama.py comparar {drawio}\n"
                      "y, cuando el análisis los recoja, acéptalos con --aceptar. (--forzar los pisa.)", file=sys.stderr)
                return 1
    else:
        base = _limpio(ed.proc)
    cambios = dm.cargar_json(a.cambios)
    nuevo = cambios if "pasos" in cambios else dm.aplicar_cambios(base, cambios.get("cambios", []))
    if not _informe_validacion(nuevo):
        return 1
    colocacion_antes = base.get("colocacion") or {}
    automatica = a.recolocar or (colocacion_antes.get("modo") == "automatica"
                                 and colocacion_antes.get("huella") == ed.f.huella())
    if not automatica and ed.f.en_tramos:
        print(f"ERROR: {drawio.name} está en {len(ed.f.hojas)} tramos y alguien los ha colocado a mano en draw.io: no "
              "encajo cambios en tramos colocados a mano sin descolocarlos. Haz el cambio en draw.io y después "
              "«comparar --aceptar», o repite con --recolocar para colocar de nuevo todos los tramos (se pierde lo "
              "colocado a mano).", file=sys.stderr)
        return 1
    if automatica:
        avisos = recolocar(ed, nuevo, drawio)
    else:
        avisos = aplicar(ed, nuevo)
        avisos.append("se ha respetado la colocación hecha a mano en draw.io; lo nuevo va junto a su paso anterior "
                      "(para recolocar todo el diagrama: --recolocar)")
    # se escribe al lado, se comprueba y solo entonces sustituye al original
    provisional = drawio.with_name(drawio.name + ".tmp")
    ed.f.guardar(str(provisional))
    comprobado, _, _ = dm.leer(str(provisional))
    dif = dm.comparar(nuevo, comprobado)
    if dif:  # no debería pasar: el dibujo no refleja el proceso pedido; el original queda intacto
        provisional.unlink()
        print("ERROR: no he cambiado nada; el resultado no coincidía con el proceso pedido:\n  "
              + "\n  ".join(t for _, t in dif), file=sys.stderr)
        return 1
    os.replace(provisional, drawio)
    for av in avisos:
        print(f"aviso: {av}")
    _escribir_json(nuevo, js, drawio, automatica=automatica)
    cambios_hechos = dm.comparar(base, nuevo)
    print(f"OK {drawio} ({len(cambios_hechos)} cambios)")
    for _, t in cambios_hechos:
        print(f"  - {t}")
    return 0 if _imagen(drawio) else 2


# ---------------------------------------------------------------- leer, comparar, png
def leer(a):
    proc, geo, avisos = dm.leer(a.drawio)
    sys.stdout.write(_json_compacto(_limpio(proc, geo if a.posiciones else None)))
    for av in avisos:
        print(f"aviso: {av}", file=sys.stderr)
    return 0


def comparar(a):
    drawio, png, js = _rutas(a.drawio)
    ed = Editor(drawio)
    base = dm.cargar_json(js) if js.exists() else None
    # los pasos añadidos a mano reciben un código como los demás (ACT-, GW-, EV-)
    renombres = []
    maximo = {}
    for p in (base["pasos"] if base else []) + ed.proc["pasos"]:
        if dm.ID_NUESTRO.match(p["id"]):
            pre, n = p["id"].split("-")
            maximo[pre] = max(maximo.get(pre, 0), int(n))
    for p in ed.proc["pasos"]:
        if not dm.ID_NUESTRO.match(p["id"]):
            pre = dm.PREFIJO[p["tipo"]]
            maximo[pre] = maximo.get(pre, 0) + 1
            nuevo_id = f"{pre}-{maximo[pre]:02d}"
            renombres.append((p["id"], nuevo_id))
    if renombres:
        tipos = {p["id"]: p["tipo"] for p in ed.proc["pasos"]}
        for viejo, nuevo_id in renombres:
            ed.renombrar_id(viejo, nuevo_id)
            el, cell = ed._cell(nuevo_id)
            estilo = cell.get("style") or ""
            if "mxgraph.bpmn" not in estilo:  # rectángulo, rombo o círculo de draw.io: se le da la forma BPMN
                cx, cy = ed.centro(nuevo_id)
                cell.set("style", dm.ESTILO[tipos[viejo]])
                w, h = dm.TAM[tipos[viejo]]
                g = cell.find("mxGeometry"); g.set("width", str(w)); g.set("height", str(h))
                ed.poner_centro(nuevo_id, cx, cy)
        ed.f.guardar()
        ed.recargar()
    avisos = list(ed.avisos)
    if base is None:
        print(f"No hay {js.name}: no sé qué conocía el análisis. Contenido actual:")
        sys.stdout.write(_json_compacto(_limpio(ed.proc)))
        dif = []
    else:
        dif = dm.comparar(base, ed.proc)
    if a.json:
        print(json.dumps({"diferencias": [t for _, t in dif], "codigos_asignados": dict(renombres), "avisos": avisos,
                          "notas": ed.geo.get("notas", [])},
                         ensure_ascii=False, indent=1))
    else:
        for viejo, nuevo_id in renombres:
            print(f"código asignado: {nuevo_id} (en draw.io era {viejo})")
        if base is not None:
            print("Sin cambios respecto al análisis." if not dif else f"{len(dif)} cambios hechos en draw.io:")
            for _, t in dif:
                print(f"  - {t}")
        for av in avisos:
            print(f"aviso: {av}")
        for n in ed.geo.get("notas", []):
            print(f"nota en el dibujo (sale en el PNG): «{n}»")
    if a.aceptar:
        antes = (base or {}).get("colocacion") or {}
        sigue_auto = antes.get("modo") == "automatica" and antes.get("huella") == ed.f.huella()
        aceptado = dict(ed.proc, tramos=True) if (base or {}).get("tramos") else ed.proc
        _escribir_json(aceptado, js, drawio, automatica=sigue_auto)
        print(f"Aceptado: {js.name} actualizado.")
        return 0 if _imagen(drawio) else 2
    return 1 if dif else 0


def png(a):
    print(f"OK {a.drawio}")
    return 0 if _imagen(a.drawio) else 2


def validar(a):
    if _informe_validacion(dm.cargar_json(a.proceso)):
        print("OK: el proceso se puede dibujar")
        return 0
    return 1


def bpmn(a):
    import bpmn_export
    destino = pathlib.Path(a.o) if a.o else pathlib.Path(a.drawio).with_suffix(".bpmn")
    proc, geo, avisos = dm.leer(a.drawio)
    for av in avisos:
        print(f"aviso: {av}")
    bpmn_export.exportar(proc, geo, destino)
    print(f"OK {destino}")
    return 0


def main():
    _salida_utf8()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="orden", required=True)
    s = sub.add_parser("crear"); s.add_argument("proceso"); s.add_argument("-o"); s.add_argument("--forzar", action="store_true"); s.set_defaults(fn=crear)
    s = sub.add_parser("actualizar"); s.add_argument("drawio"); s.add_argument("cambios"); s.add_argument("--forzar", action="store_true")
    s.add_argument("--recolocar", action="store_true"); s.set_defaults(fn=actualizar)
    s = sub.add_parser("leer"); s.add_argument("drawio"); s.add_argument("--posiciones", action="store_true"); s.set_defaults(fn=leer)
    s = sub.add_parser("comparar"); s.add_argument("drawio"); s.add_argument("--aceptar", action="store_true"); s.add_argument("--json", action="store_true"); s.set_defaults(fn=comparar)
    s = sub.add_parser("png"); s.add_argument("drawio"); s.set_defaults(fn=png)
    s = sub.add_parser("bpmn"); s.add_argument("drawio"); s.add_argument("-o"); s.set_defaults(fn=bpmn)
    s = sub.add_parser("validar"); s.add_argument("proceso"); s.set_defaults(fn=validar)
    a = ap.parse_args()
    try:
        sys.exit(a.fn(a))
    except navegador.SinNavegador as e:
        print(str(e), file=sys.stderr); sys.exit(2)
    except (dm.ErrorProceso, RuntimeError, FileNotFoundError, json.JSONDecodeError, ET.ParseError) as e:
        print(f"ERROR: {e}", file=sys.stderr); sys.exit(1)


if __name__ == "__main__":
    main()
