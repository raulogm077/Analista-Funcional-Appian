"""Un proceso con una pestaña por fase en un solo .drawio.

El JSON lleva `paginas`, un proceso por pestaña, y cada pestaña es una página del .drawio con id `pagina-N` y el
nombre de su proceso. Cada orden de diagrama.py trabaja sobre todas: copia cada pestaña a una carpeta temporal como un
.drawio de una página, le aplica la orden de siempre y la vuelve a unir. Así cada pestaña se coloca, se compara y se
pinta igual que un proceso suelto. Un PNG por pestaña: X-1.png, X-2.png…

Un subproceso o una llamada que se llama como otra pestaña enlaza con ella: en draw.io, un clic la abre.
"""
import argparse, contextlib, copy, io, json, pathlib, re, shutil, sys, tempfile
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True  # sin __pycache__ en el plugin
import drawio_modelo as dm

ID_PAGINA = re.compile(r"pagina-(\d+)$")


def es_libro_json(ruta):
    try:
        return "paginas" in dm.cargar_json(ruta)
    except (OSError, ValueError, dm.ErrorProceso):
        return False


def es_libro_drawio(ruta):
    try:
        top = ET.parse(ruta).getroot()
    except (OSError, ET.ParseError):
        return False
    return any(ID_PAGINA.match(d.get("id") or "") for d in top.findall("diagram"))


def _nombre(p):
    return dm.CODIGO.match(p.get("nombre") or "").group(1) if dm.CODIGO.match(p.get("nombre") or "") else (p.get("nombre") or "")


def validar_libro(libro):
    """Errores del libro en sí (las pestañas se validan cada una como un proceso)."""
    paginas = libro.get("paginas")
    if not isinstance(paginas, list) or not paginas:
        return ["«paginas» es la lista de procesos, uno por pestaña"]
    err = []
    nombres = [p.get("proceso") for p in paginas]
    if any(not n for n in nombres):
        err.append("cada pestaña necesita su «proceso»: es el nombre de la pestaña")
    dobles = sorted({n for n in nombres if n and nombres.count(n) > 1})
    if dobles:
        err.append(f"dos pestañas se llaman igual: {', '.join(dobles)}")
    if any(p.get("tramos") for p in paginas):
        err.append("una pestaña no va en tramos: si una fase no cabe, es otra pestaña")
    return err


def _json_libro(libro):
    import diagrama
    paginas = [diagrama._json_compacto(p).rstrip("\n").replace("\n", "\n  ") for p in libro["paginas"]]
    return ("{\n  " + f'"proceso": {json.dumps(libro.get("proceso", ""), ensure_ascii=False)},\n  "paginas": [\n  '
            + ",\n  ".join(paginas) + "\n  ]\n}\n")


def _escribir_libro(libro, ruta):
    dm.escribir_texto(ruta, _json_libro(libro))


def _paginas(drawio):
    arbol = ET.parse(drawio)
    pags = sorted((d for d in arbol.getroot().findall("diagram") if ID_PAGINA.match(d.get("id") or "")),
                  key=lambda d: int(ID_PAGINA.match(d.get("id")).group(1)))
    return arbol, pags


def _suelta(diagrama, ruta):
    """Una página del libro como un .drawio de una sola página."""
    top = ET.Element("mxfile", {"host": "appian-analisis-funcional"})
    top.append(copy.deepcopy(diagrama))
    ET.ElementTree(top).write(ruta, encoding="unicode")


def _pagina_de(ruta, k, nombre):
    """La página (única o la primera) de un .drawio suelto, con su id y su nombre de pestaña."""
    d = ET.parse(ruta).getroot().find("diagram")
    d.set("id", f"pagina-{k}")
    d.set("name", nombre)
    return d


def _enlazar(arbol, libro):
    """Un subproceso o una llamada que se llama como otra pestaña enlaza con ella (en draw.io, un clic la abre)."""
    pestana = {p.get("proceso"): k for k, p in enumerate(libro["paginas"], 1)}
    for k, (d, proc) in enumerate(zip(_paginas_de_arbol(arbol), libro["paginas"]), 1):
        objetivo = {p["id"]: pestana[_nombre(p)] for p in proc["pasos"]
                    if p["tipo"] in ("subproceso", "llamada") and pestana.get(_nombre(p)) not in (None, k)}
        raiz = dm.Fichero._modelo(d).find("root")
        for el in list(raiz):
            cid = el.get("id")
            if cid not in objetivo:
                continue
            if el.tag == "mxCell":     # la celda pasa a un <object>, como hace draw.io al añadir un enlace
                i = list(raiz).index(el)
                obj = ET.Element("object", {"id": el.attrib.pop("id"), "label": el.attrib.pop("value", "")})
                raiz.remove(el)
                obj.append(el)
                raiz.insert(i, obj)
                el = obj
            el.set("link", f"data:page/id,pagina-{objetivo[cid]}")


def _paginas_de_arbol(arbol):
    return sorted((d for d in arbol.getroot().findall("diagram") if ID_PAGINA.match(d.get("id") or "")),
                  key=lambda d: int(ID_PAGINA.match(d.get("id")).group(1)))


def _guardar(arbol, ruta):
    ET.indent(arbol, space="")
    dm.escribir_texto(ruta, ET.tostring(arbol.getroot(), encoding="unicode"))


class _Trabajo:
    """Una pestaña en la carpeta temporal: su .drawio, su .json y su PNG, con los nombres de verdad para la salida."""

    def __init__(self, tmp, real, k):
        self.k = k
        self.drawio = tmp / f"p{k}.drawio"
        self.json = self.drawio.with_suffix(".json")
        self.png = self.drawio.with_suffix(".png")
        self.real_png = real.with_name(f"{real.stem}-{k}.png")
        self.real = real

    def traducir(self, texto):
        for de, a in ((self.png, self.real_png), (self.json, self.real.with_suffix(".json")), (self.drawio, self.real),
                      (self.png.name, self.real_png.name), (self.drawio.name, self.real.name)):
            texto = texto.replace(str(de), str(a))
        return texto


def _correr(fn, ns, trabajo, titulo):
    """Ejecuta la orden de siempre sobre una pestaña y escribe su salida con los nombres de verdad."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            codigo = fn(ns)
        except dm.ErrorProceso as e:
            print(f"ERROR: {e}", file=sys.stderr)
            codigo = 1
    print(f"pestaña {trabajo.k} «{titulo}»:")
    for linea in trabajo.traducir(out.getvalue()).splitlines():
        print(f"  {linea}")
    sys.stderr.write("".join(f"  {l}\n" for l in trabajo.traducir(err.getvalue()).splitlines()))
    return codigo or 0


def _peor(codigos):
    """El código de salida del libro: 1 si alguna pestaña falla, si no 3 si hay cambios a mano, 2 si falta el PNG."""
    for c in (1, 3, 2):
        if c in codigos:
            return c
    return 0


def _mover_png(trabajo):
    if trabajo.png.exists():
        shutil.move(str(trabajo.png), str(trabajo.real_png))


def _quitar_pngs_sobrantes(real, n):
    for p in real.parent.glob(f"{real.stem}-*.png"):
        m = re.fullmatch(re.escape(real.stem) + r"-(\d+)\.png", p.name)
        if m and int(m.group(1)) > n and not p.with_suffix(".drawio").exists():
            p.unlink()
            print(f"quitado {p.name}: es de una pestaña que ya no está")


def crear(a, crear_uno):
    libro = dm.cargar_json(a.proceso)
    err = validar_libro(libro)
    for e in err:
        print(f"ERROR: {e}", file=sys.stderr)
    if err:
        return 1
    destino = pathlib.Path(a.o) if a.o else pathlib.Path(a.proceso).with_suffix(".drawio")
    if destino.suffix != ".drawio":
        destino = destino / (pathlib.Path(a.proceso).stem + ".drawio")
    if destino.exists() and not a.forzar:
        print(f"ERROR: {destino} ya existe. Para cambiarlo usa «actualizar» o repite con --forzar para rehacerlo entero.",
              file=sys.stderr)
        return 1
    destino.parent.mkdir(parents=True, exist_ok=True)
    codigos, paginas = [], []
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        for k, proc in enumerate(libro["paginas"], 1):
            t = _Trabajo(tmp, destino, k)
            dm.escribir_texto(tmp / f"p{k}.entrada.json", json.dumps(proc, ensure_ascii=False))
            ns = argparse.Namespace(**{**vars(a), "proceso": str(tmp / f"p{k}.entrada.json"), "o": str(t.drawio),
                                       "forzar": False})
            codigos.append(_correr(crear_uno, ns, t, proc["proceso"]))
            if codigos[-1] == 1:
                print("ERROR: no he escrito nada: corrige esa pestaña y repite.", file=sys.stderr)
                return 1
            paginas.append(_pagina_de(t.drawio, k, proc["proceso"]))
            libro["paginas"][k - 1] = dm.cargar_json(t.json)
            _mover_png(t)
        arbol = ET.ElementTree(ET.Element("mxfile", {"host": "appian-analisis-funcional"}))
        for d in paginas:
            arbol.getroot().append(d)
        _enlazar(arbol, libro)
        _guardar(arbol, destino)
        _escribir_libro(libro, destino.with_suffix(".json"))
    _quitar_pngs_sobrantes(destino, len(paginas))
    print(f"OK {destino} ({len(paginas)} pestañas)\n   {destino.with_suffix('.json')}")
    return _peor(codigos)


def _por_pagina(a, fn, cambia, que=None, preparar=None):
    """Aplica `fn` a cada pestaña (o solo a la `que`, un número o un nombre). Si `cambia`, une de nuevo las páginas y
    el JSON del libro. `preparar(k, ns)` ajusta la orden de cada pestaña."""
    drawio = pathlib.Path(a.drawio)
    js = drawio.with_suffix(".json")
    arbol, pags = _paginas(drawio)
    libro = dm.cargar_json(js) if js.exists() else None
    if libro is not None and len(libro.get("paginas", [])) != len(pags):
        raise dm.ErrorProceso(f"{js.name} tiene {len(libro.get('paginas', []))} pestañas y {drawio.name}, {len(pags)}: "
                              "no sé cuál es cuál")
    elegidas = range(1, len(pags) + 1)
    if que is not None:
        nombres = [d.get("name") for d in pags]
        k = int(que) if str(que).isdigit() else (nombres.index(que) + 1 if que in nombres else None)
        if k is None or not 1 <= k <= len(pags):
            raise dm.ErrorProceso(f"no hay ninguna pestaña «{que}»: son {', '.join(f'{i} «{n}»' for i, n in enumerate(nombres, 1))}")
        elegidas = [k]
    codigos = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        for k in elegidas:
            d = pags[k - 1]
            t = _Trabajo(tmp, drawio, k)
            _suelta(d, t.drawio)
            if libro is not None:
                dm.escribir_texto(t.json, json.dumps(libro["paginas"][k - 1], ensure_ascii=False))
            if (drawio.with_name(f"{drawio.stem}-{k}.png")).exists():
                shutil.copy(drawio.with_name(f"{drawio.stem}-{k}.png"), t.png)
            ns = argparse.Namespace(**{**vars(a), "drawio": str(t.drawio)})
            if preparar:
                preparar(k, ns, tmp)
            codigos.append(_correr(fn, ns, t, d.get("name")))
            if codigos[-1] == 1:
                continue
            if cambia:
                nombre = dm.cargar_json(t.json).get("proceso") if t.json.exists() else d.get("name")
                nueva = _pagina_de(t.drawio, k, nombre or d.get("name"))
                top = arbol.getroot()
                i = list(top).index(d)
                top.remove(d)
                top.insert(i, nueva)
                pags[k - 1] = nueva
                if t.json.exists():
                    libro = libro or {"proceso": drawio.stem, "paginas": [{} for _ in pags]}
                    libro["paginas"][k - 1] = dm.cargar_json(t.json)
            if t.png.exists():
                _mover_png(t)
            else:
                drawio.with_name(f"{drawio.stem}-{k}.png").unlink(missing_ok=True)
        if cambia and 1 not in codigos:
            if libro is not None:
                _enlazar(arbol, libro)
                _escribir_libro(libro, js)
            _guardar(arbol, drawio)
    return _peor(codigos)


def actualizar(a, fn):
    cambios = dm.cargar_json(a.cambios)
    if "paginas" in cambios:            # el libro entero: cada pestaña, su proceso completo
        _, pags = _paginas(a.drawio)
        if len(cambios["paginas"]) != len(pags):
            raise dm.ErrorProceso(f"el libro tiene {len(pags)} pestañas y los cambios, {len(cambios['paginas'])}: para "
                                  "añadir o quitar una pestaña, vuelve a crear el .drawio con --forzar")

        def preparar(k, ns, tmp):
            ns.cambios = str(tmp / f"p{k}.cambios.json")
            dm.escribir_texto(ns.cambios, json.dumps(cambios["paginas"][k - 1], ensure_ascii=False))
        return _por_pagina(a, fn, True, preparar=preparar)
    if "pagina" not in cambios:
        raise dm.ErrorProceso("en un .drawio con pestañas, los cambios dicen a qué pestaña van: "
                              '{"pagina": "<número o nombre>", "cambios": [...]}')

    def preparar(k, ns, tmp):
        ns.cambios = str(tmp / f"p{k}.cambios.json")
        dm.escribir_texto(ns.cambios, json.dumps({c: v for c, v in cambios.items() if c != "pagina"}, ensure_ascii=False))
    return _por_pagina(a, fn, True, que=cambios["pagina"], preparar=preparar)


def leer(a):
    import diagrama
    _, pags = _paginas(a.drawio)
    partes = []
    with tempfile.TemporaryDirectory() as tmp:
        for k, d in enumerate(pags, 1):
            ruta = pathlib.Path(tmp) / f"p{k}.drawio"
            _suelta(d, ruta)
            proc, geo, avisos = dm.leer(str(ruta))
            partes.append(diagrama._limpio(proc, geo if a.posiciones else None))
            for av in avisos:
                print(f"aviso: pestaña {k}: {av}", file=sys.stderr)
    js = pathlib.Path(a.drawio).with_suffix(".json")
    nombre = (dm.cargar_json(js).get("proceso") if js.exists() else None) or pathlib.Path(a.drawio).stem
    sys.stdout.write(_json_libro({"proceso": nombre, "paginas": partes}))
    return 0


def comparar(a, fn):
    return _por_pagina(a, fn, True)      # comparar da código a lo añadido a mano: también cambia el .drawio


def png(a, fn):
    return _por_pagina(a, fn, False)


def bpmn(a, fn):
    drawio = pathlib.Path(a.drawio)
    carpeta = pathlib.Path(a.o) if a.o else drawio.parent
    carpeta.mkdir(parents=True, exist_ok=True)

    def preparar(k, ns, tmp):
        ns.o = str(carpeta / f"{drawio.stem}-{k}.bpmn")
    return _por_pagina(a, fn, False, preparar=preparar)


def validar(a, fn):
    libro = dm.cargar_json(a.proceso)
    err = validar_libro(libro)
    for e in err:
        print(f"ERROR: {e}", file=sys.stderr)
    codigos = [1] if err else []
    with tempfile.TemporaryDirectory() as tmp:
        for k, proc in enumerate(libro.get("paginas") or [], 1):
            ruta = pathlib.Path(tmp) / f"p{k}.json"
            dm.escribir_texto(ruta, json.dumps(proc, ensure_ascii=False))
            print(f"pestaña {k} «{proc.get('proceso', '')}»:")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                codigos.append(fn(argparse.Namespace(proceso=str(ruta))))
            print("".join(f"  {l}\n" for l in out.getvalue().splitlines()), end="")
    return _peor(codigos)
