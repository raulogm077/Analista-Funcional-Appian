"""Navegador sin conexión para colocar los pasos (motor de carriles de Mermaid) y pintar el .drawio a PNG
(visor de draw.io). Todo va dentro de la skill: el diagrama no sale del equipo."""
import pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"
MERMAID_JS = ASSETS / "mermaid.min.js"
VIEWER_JS = ASSETS / "drawio" / "viewer-static.min.js"
STENCILS = ASSETS / "drawio" / "stencils"


class SinNavegador(Exception):
    pass


def _launch(p):
    """Chromium de Playwright; si no está descargado, Chrome o Edge del sistema."""
    errores = []
    for opts in ({}, {"channel": "chrome"}, {"channel": "msedge"}):
        try:
            return p.chromium.launch(**opts)
        except Exception as e:  # noqa: BLE001 - se prueba el siguiente navegador
            errores.append(f"{opts.get('channel', 'chromium de Playwright')}: {str(e).splitlines()[0]}")
    raise SinNavegador("No hay navegador disponible. Instala uno de estos:\n  - playwright install chromium\n"
                       "  - o Google Chrome / Microsoft Edge (se usan sin descargar nada más)\nDetalle:\n  " + "\n  ".join(errores))


def _playwright():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise SinNavegador("Falta Playwright para Python: pip install playwright\n"
                           "(con Chrome o Edge instalados no hace falta 'playwright install').")
    return sync_playwright


def _pagina(p, ancho=2400, alto=1400, escala=2):
    b = _launch(p)
    pg = b.new_page(device_scale_factor=escala, viewport={"width": ancho, "height": alto})

    def ruta(r):
        u = r.request.url
        if u.startswith(("about:", "data:")):
            return r.continue_()
        if "/stencils/" in u:  # formas BPMN de draw.io, servidas desde la skill
            f = STENCILS / u.split("/stencils/")[-1].split("?")[0]
            if f.is_file():
                return r.fulfill(body=f.read_bytes(), content_type="application/xml")
        r.abort()  # nada más sale del equipo
    pg.route("**/*", ruta)
    pg.set_content("<!doctype html><html><head><meta charset='utf-8'><style>body{margin:0;background:#fff}</style>"
                   "<script>window.DRAW_MATH_URL='';</script></head><body><div id='out'></div></body></html>")
    return b, pg


# ---------------------------------------------------------------- colocación con Mermaid
_ICONOS = r"""
const circ = (r, w) => `<circle cx="18" cy="18" r="${r}" fill="#fff" stroke="#000" stroke-width="${w}"/>`;
const dia = `<path d="M18 2 34 18 18 34 2 18Z" fill="#fff" stroke="#000"/>`;
mermaid.registerIconPacks([{name: 'bpmn', icons: {prefix: 'bpmn', width: 36, height: 36, icons: {
  ev: {body: circ(15, 1.5)}, gw: {body: dia}}}}]);
"""
_JS_COLOCAR = """async (code) => {
  ICONOS
  mermaid.initialize({startOnLoad: false, theme: 'base', securityLevel: 'strict',
    flowchart: {useMaxWidth: false, nodeSpacing: 24, rankSpacing: 30, wrappingWidth: 110, padding: 8}});
  try { await mermaid.parse(code); } catch (e) { return {error: String(e && e.message || e)}; }
  const {svg} = await mermaid.render('m', code);
  const out = document.getElementById('out'); out.innerHTML = svg;
  const nodos = {}, carriles = {}, flujos = [];
  out.querySelectorAll('g.node, g.icon-shape').forEach(g => {
    const m = /flowchart-(n\\d+)-\\d+$/.exec(g.id); if (!m) return;
    const c = new DOMPoint(0, 0).matrixTransform(g.getScreenCTM());
    nodos[m[1]] = [c.x, c.y];
  });
  out.querySelectorAll('g.cluster').forEach(g => {
    const m = /(c\\d+)$/.exec(g.id); if (!m) return;
    const rs = [...g.querySelectorAll('rect')].map(r => r.getBoundingClientRect());
    const x = Math.min(...rs.map(r => r.left)), y = Math.min(...rs.map(r => r.top));
    const r = Math.max(...rs.map(r => r.right)), b = Math.max(...rs.map(r => r.bottom));
    carriles[m[1]] = [x, y, r - x, b - y];
  });
  out.querySelectorAll('path.flowchart-link').forEach(p => {
    const m = /L_(n\\d+)_(n\\d+)_(\\d+)$/.exec(p.id); if (!m) return;
    const ctm = p.getScreenCTM(), pts = [];
    const re = /Q\\s*([-\\d.e]+)[ ,]([-\\d.e]+)/g; let q;
    while ((q = re.exec(p.getAttribute('d')))) { const s = new DOMPoint(+q[1], +q[2]).matrixTransform(ctm); pts.push([s.x, s.y]); }
    flujos.push([m[1], m[2], +m[3], pts]);
  });
  return {nodos, carriles, flujos};
}""".replace("ICONOS", _ICONOS)


def _esc(s):
    return (s or " ").replace('"', "#quot;").replace("\n", " ")


def codigo_mermaid(proc, eventos, puertas):
    """Mermaid (carriles) equivalente al proceso, solo para calcular la colocación."""
    alias = {p["id"]: f"n{i}" for i, p in enumerate(proc["pasos"])}
    lineas = ["swimlane-beta LR"]
    for i, c in enumerate(proc["carriles"]):
        lineas.append(f'  subgraph c{i}["{_esc(c)}"]')
        for p in proc["pasos"]:
            if p["carril"] != c:
                continue
            n = alias[p["id"]]
            if p["tipo"] in eventos:
                lineas.append(f'    {n}@{{ icon: "bpmn:ev", label: "{_esc(p.get("nombre"))}", pos: "b", h: 36 }}')
            elif p["tipo"] in puertas:
                lineas.append(f'    {n}@{{ icon: "bpmn:gw", label: "{_esc(p.get("nombre"))}", pos: "t", h: 36 }}')
            else:
                lineas.append(f'    {n}("{_esc(p.get("nombre"))}")')
        lineas.append("  end")
    for f in proc["flujos"]:
        flecha = "-.->" if f.get("discontinuo") else "-->"
        eti = f'|"{_esc(f["etiqueta"])}"|' if f.get("etiqueta") else ""
        lineas.append(f"  {alias[f['de']]} {flecha}{eti} {alias[f['a']]}")
    return "\n".join(lineas), alias


def colocar(proc, eventos, puertas, cabecera):
    """Geometría para escribir_drawio: carriles, centros de los pasos y puntos de cada flujo."""
    code, alias = codigo_mermaid(proc, eventos, puertas)
    sp = _playwright()
    with sp() as p:
        b, pg = _pagina(p, ancho=3000, alto=2000, escala=1)
        pg.add_script_tag(content=MERMAID_JS.read_text(encoding="utf-8"))
        res = pg.evaluate(_JS_COLOCAR, code)
        b.close()
    if "error" in res:
        raise RuntimeError("El motor de colocación no aceptó el proceso:\n" + res["error"] + "\n\n" + code)
    rects = [res["carriles"][f"c{i}"] for i in range(len(proc["carriles"]))]
    x0 = min(r[0] for r in rects); y0 = min(r[1] for r in rects)
    derecha = max(r[0] + r[2] for r in rects)
    geo = {"carriles": {}, "pasos": {}, "flujos": [], "ancho": derecha - x0 + cabecera}
    # carriles apilados sin huecos, en el orden del proceso
    for c, r in zip(proc["carriles"], rects):
        geo["carriles"][c] = (r[1] - y0, r[3])
    for p in proc["pasos"]:
        cx, cy = res["nodos"][alias[p["id"]]]
        geo["pasos"][p["id"]] = (cx - x0 + cabecera, cy - y0)
    # los puntos de paso se quedan dentro de los carriles (el motor a veces rodea el diagrama por fuera)
    alto = max(y + h for y, h in geo["carriles"].values())
    dentro = lambda x, y: (min(max(x - x0 + cabecera, cabecera + 6), geo["ancho"] - 6), min(max(y - y0, 6), alto - 6))
    puntos = {}
    for de, a, _, pts in sorted(res["flujos"], key=lambda f: f[2]):
        puntos.setdefault((de, a), []).append([dentro(x, y) for x, y in pts])
    for f in proc["flujos"]:
        lista = puntos.get((alias[f["de"]], alias[f["a"]]), [])
        geo["flujos"].append(lista.pop(0) if lista else [])
    return geo


# ---------------------------------------------------------------- PNG con el visor de draw.io
_JS_PINTAR = """(xml) => new Promise(ok => {
  const out = document.getElementById('out');
  const div = document.createElement('div'); out.appendChild(div);
  const graph = new Graph(div);
  graph.setEnabled(false); graph.foldingEnabled = false;
  const node = mxUtils.parseXml(xml).documentElement;
  new mxCodec(node.ownerDocument).decode(node, graph.getModel());
  const b = graph.getGraphBounds();
  graph.view.setTranslate(-b.x + 12, -b.y + 12);
  div.style.width = Math.ceil(b.width + 24) + 'px'; div.style.height = Math.ceil(b.height + 24) + 'px';
  setTimeout(() => ok({ancho: b.width, alto: b.height}), 400);
})"""


def pintar_png(xml_modelo, destino, escala=2):
    sp = _playwright()
    with sp() as p:
        b, pg = _pagina(p, escala=escala)
        pg.add_script_tag(content=VIEWER_JS.read_text(encoding="utf-8"))
        res = pg.evaluate(_JS_PINTAR, xml_modelo)
        pg.locator("#out > div").screenshot(path=str(destino))
        b.close()
    return res
