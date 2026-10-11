"""
El lector web de marca.py: los colores, el theme-color, los logos y las tipografías de la web de una empresa, para sacar
su marca (references/marca.md). Se usa con «marca.py web <url> [--max-css 10] [--timeout 10]».

Descarga la página y las hojas de estilo que enlaza del mismo sitio (el mismo dominio, como www.x.es y estaticos.x.es;
como mucho --max-css, de 2 MB cada una) y escribe en la salida estándar un JSON con sus colores (los 20 más usados, sin
blancos, negros ni grises; con las variables CSS que los definen y su contraste), su theme-color, sus logos (los de la
cabecera con «logo» primero; el icono del sitio, al final) y sus tipografías. Con la URL de una hoja de estilo, lo mismo
de esa hoja. Sin red o sin respuesta, o si la URL es un PDF u otra cosa que no es HTML ni CSS, sale con 2 y lo dice; sin
una URL (solo el nombre de la empresa), también, y dice cómo encontrar su web.

Solo biblioteca estándar. Reutiliza color_hex() y hls() de marca.py y contrast() de validate.py.
"""
import http.client, ipaddress, json, re, socket, sys
sys.dont_write_bytecode = True  # sin __pycache__ en el plugin: no se escribe fuera del proyecto
import urllib.error, urllib.parse, urllib.request
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate import contrast  # noqa: E402
from marca import BLANCO, NEGRO, color_hex, hls  # noqa: E402

MAX_HOJA = 2 * 1024 * 1024     # bytes de una hoja de estilo
MAX_PAGINA = 5 * 1024 * 1024   # bytes de la página
MAX_COLORES = 20
UA = "Mozilla/5.0 (compatible; appian-prototipos marca.py)"


# ------------------------------------------------------------------ color
def neutro(h):
    """Blanco o negro (luminosidad HLS de 96 % o más, o de 4 % o menos) o gris (saturación por debajo del 10 %)."""
    _, l, s = hls(h)
    return l >= 0.96 or l <= 0.04 or s < 0.10


# ------------------------------------------------------------------ CSS
COMENTARIO = re.compile(r"/\*.*?\*/", re.S)
COLOR = re.compile(r"#[0-9a-fA-F]{3,8}(?![\w-])|\b(?:rgba?|hsla?)\([^()]*\)", re.I)
IMPORT = re.compile(r"@import\s+(?:url\(\s*)?[\"']?([^\"')\s;]+)", re.I)
VAR = re.compile(r"var\(\s*(--[\w-]+)")
VAR_SOLA = re.compile(r"var\(\s*(--[\w-]+)\s*(?:,\s*(.*))?\)")  # un valor que es solo var(--x) o var(--x, respaldo)
GENERICAS = {"serif", "sans-serif", "monospace", "cursive", "fantasy", "system-ui", "ui-serif", "ui-sans-serif",
             "ui-monospace", "ui-rounded", "emoji", "math", "fangsong", "inherit", "initial", "unset", "revert",
             "revert-layer", "-apple-system", "blinkmacsystemfont"}


def declaraciones(texto, bloques=True):
    """(propiedad, valor) de una hoja de estilo, sin selectores ni preludios de @-reglas (solo lo que hay entre una llave
    y la «}» que la cierra); con bloques=False, de un atributo style."""
    texto = COMENTARIO.sub(" ", texto)
    trozos, inicio = [], 0
    if bloques:
        for m in re.finditer(r"[{}]", texto):
            if m.group() == "}":
                trozos.append(texto[inicio:m.start()])
            inicio = m.end()
    else:
        trozos = [texto]
    out = []
    for trozo in trozos:
        for d in trozo.split(";"):
            if ":" in d:
                p, v = (x.strip() for x in d.split(":", 1))
                if re.fullmatch(r"-?-?[A-Za-z][\w-]*", p):
                    out.append((p if p.startswith("--") else p.lower(), v))
    return out


def resolver(nombre, defs, nivel=0):
    """Valor de una variable CSS (su primera definición), siguiendo los var() encadenados."""
    vals = defs.get(nombre)
    if not vals or nivel > 5:
        return None
    m = VAR_SOLA.fullmatch(vals[0].strip())
    return (resolver(m.group(1), defs, nivel + 1) or m.group(2)) if m else vals[0].strip()


def primera_familia(valor, defs):
    """La primera familia de un font-family (resuelve var()); None si es genérica o de sistema."""
    m = VAR_SOLA.fullmatch(valor.strip())
    if m:
        valor = resolver(m.group(1), defs) or m.group(2) or ""
    fam = re.split(r",(?=(?:[^\"']*[\"'][^\"']*[\"'])*[^\"']*$)", valor)[0].strip().strip("\"'").strip()
    return fam if fam and fam.lower() not in GENERICAS and not fam.lower().startswith("var(") else None


def familia_font(valor):
    """La lista de familias del atajo font (lo que va tras el tamaño y la altura de línea)."""
    m = re.search(r"(?:^|\s)(?:\d[\w.%]*|xx-small|x-small|small|medium|large|x-large|xx-large|smaller|larger)"
                  r"(?:\s*/\s*[\w.%-]+)?\s+([^\d\s].*)$", valor.strip(), re.I)
    return m.group(1) if m else None


# ------------------------------------------------------------------ web
def _es_ip(host):
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return False


def _local(host):
    """Este mismo equipo: localhost o una IP de loopback (127.0.0.1, ::1)."""
    return host == "localhost" or host.endswith(".localhost") or (_es_ip(host) and ipaddress.ip_address(host).is_loopback)


# segundo nivel de los sufijos públicos más usados (empresa.co.uk, empresa.com.es, ministerio.gob.es…): con uno de ellos
# en la penúltima etiqueta, el dominio son las tres últimas
SUFIJOS = {"ac", "co", "com", "edu", "go", "gob", "gouv", "gov", "govt", "gv", "int", "ltd", "mil", "ne", "net", "nom", "or",
           "org", "plc", "sch"}


def _base(host):
    """El dominio de un servidor: sus dos últimas etiquetas (x.es) o tres si la penúltima es un sufijo (empresa.co.uk)."""
    partes = host.rstrip(".").split(".")
    return partes[-3:] if len(partes) >= 3 and partes[-2] in SUFIJOS else partes[-2:]


def mismo_sitio(a, b):
    """Mismo servidor, mismo dominio (www.x.es y estaticos.x.es) o este mismo equipo (localhost y 127.0.0.1); otra IP, solo
    ella misma."""
    ha, hb = ((urllib.parse.urlsplit(u).hostname or "").lower() for u in (a, b))
    if ha == hb or (_local(ha) and _local(hb)):
        return True
    return not (_es_ip(ha) or _es_ip(hb)) and "." in ha and "." in hb and _base(ha) == _base(hb)


def descargar(url, timeout, limite):
    """(bytes, URL final, charset, tipo): tipo, el Content-Type sin parámetros (None si no lo dice). A este mismo equipo
    se va sin proxy."""
    local = _local((urllib.parse.urlsplit(url).hostname or "").lower())
    opener = urllib.request.build_opener(*([urllib.request.ProxyHandler({})] if local else []))
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,text/css;q=0.9,*/*;q=0.8"})
    with opener.open(req, timeout=timeout) as r:
        tipo = r.headers.get_content_type() if r.headers.get("Content-Type") else None
        return r.read(limite + 1), r.geturl(), r.headers.get_content_charset(), tipo


def texto_de(datos, charset):
    if not charset:
        m = re.search(rb"(?:<meta[^>]+charset=|@charset\s+)[\"']?([\w-]+)", datos[:4096], re.I)
        charset = m.group(1).decode("ascii", "replace") if m else "utf-8"
    try:
        return datos.decode(charset, errors="replace")
    except LookupError:
        return datos.decode("utf-8", errors="replace")


def motivo(e, timeout):
    r = getattr(e, "reason", e)
    if isinstance(r, ConnectionRefusedError):
        return "conexión rechazada (nada responde en esa dirección)"
    if isinstance(r, socket.gaierror):
        return "no se encuentra el servidor (sin red o sin DNS)"
    if isinstance(r, (TimeoutError, socket.timeout)):
        return f"sin respuesta en {timeout:g} s"
    return str(r)


VACIOS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
CABECERAS = {"header", "cabecera", "masthead"}
NO_LOGO = ("logout", "logon", "logoff")   # empiezan por «logo» y son de la sesión


def palabras(texto):
    """Las palabras de un atributo, en minúsculas: corta por lo que no es letra (también acentuada) y donde una minúscula va
    seguida de una mayúscula: site-logo, header__logo, siteLogo y logoImg dan «logo»."""
    out = set()
    for trozo in re.findall(r"[^\W\d_]+", texto or ""):
        palabra = trozo[0]
        for antes, c in zip(trozo, trozo[1:]):
            if antes.islower() and c.isupper():
                out.add(palabra.lower())
                palabra = ""
            palabra += c
        out.add(palabra.lower())
    return out


def dice_logo(texto):
    """¿Lleva una palabra que empieza por «logo» (logo, logos, logotipo, logoImg, logomark, logoimg…)? logout, logon y
    logoff no cuentan; catálogo y blogger, tampoco (no empiezan por «logo»)."""
    return any(p.startswith("logo") and not p.startswith(NO_LOGO) for p in palabras(texto))


class Pagina(HTMLParser):
    """Lo que marca.py web lee de la página: hojas y bloques de estilo, atributos style, colores de los SVG en línea,
    candidatos a logo, iconos del sitio, theme-color y familias de Google Fonts."""

    def __init__(self, url, texto):
        super().__init__(convert_charrefs=True)
        self.url, self.texto = url, texto
        self.inicios = [0] + [m.end() for m in re.finditer("\n", texto)]
        self.pila, self.hojas, self.estilos, self.atributos_style, self.colores_svg = [], [], [], [], []
        self.candidatos, self.iconos, self.familias_enlazadas = [], [], []
        self.theme, self._estilo, self._svg, self._nivel_svg, self.n_svg = None, None, None, 0, 0
        self.feed(texto)
        self.close()

    def _pos(self):
        linea, col = self.getpos()
        return self.inicios[linea - 1] + col

    def _en_cabecera(self):
        return any(t == "header" or a.get("role") == "banner" or palabras(f"{a.get('class', '')} {a.get('id', '')}") & CABECERAS
                   for t, a in self.pila)

    def _pista(self, a):
        for k in ("src", "alt", "class", "id", "aria-label", "title"):
            if dice_logo(a.get(k)):
                return f"«logo» en {k}"
        for t, x in reversed(self.pila):
            for k in ("class", "id"):
                if dice_logo(x.get(k)):
                    return f"«logo» en {k} de <{t}>"
        return None

    def _candidato(self, entrada, cabecera):
        self.candidatos.append((not cabecera, len(self.candidatos), entrada))

    def handle_starttag(self, tag, attrs):
        a = {k: v or "" for k, v in attrs}
        if tag == "svg":
            if self._svg is None:
                self.n_svg += 1
                self._svg = (self._pos(), self.n_svg, self._en_cabecera(), self._pista(a))
                self._nivel_svg = 0
            else:
                self._nivel_svg += 1
        elif tag == "style":
            self._estilo = []
        self._comunes(tag, a)
        if tag not in VACIOS:
            self.pila.append((tag, a))

    def handle_startendtag(self, tag, attrs):
        self._comunes(tag, {k: v or "" for k, v in attrs})

    def _comunes(self, tag, a):
        if a.get("style"):
            self.atributos_style.append(a["style"])
        if self._svg is not None:
            self.colores_svg += [a[k] for k in ("fill", "stroke", "stop-color", "color", "flood-color") if a.get(k)]
        rel = set((a.get("rel") or "").lower().split())
        if tag == "img" and a.get("src"):
            pista, cab = self._pista(a), self._en_cabecera()
            if pista:
                self._candidato({"url": urllib.parse.urljoin(self.url, a["src"]), "pista": f"img{' en la cabecera' if cab else ''}; {pista}"}, cab)
        elif tag == "link" and a.get("href"):
            href = urllib.parse.urljoin(self.url, a["href"])
            if "stylesheet" in rel and "alternate" not in rel:
                self.hojas.append(href)
            if rel & {"icon", "apple-touch-icon", "mask-icon"}:
                self.iconos.append({"url": href, "pista": f"icono del sitio (rel=\"{a.get('rel')}\")"})
            if "fonts.googleapis.com" in href:
                for fam in urllib.parse.parse_qs(urllib.parse.urlsplit(href).query).get("family", []):
                    self.familias_enlazadas += [f.split(":")[0].strip() for f in fam.split("|") if f.strip()]
        elif tag == "meta" and (a.get("name") or "").lower() == "theme-color" and self.theme is None:
            self.theme = a.get("content")

    def handle_endtag(self, tag):
        if tag == "style" and self._estilo is not None:
            self.estilos.append("".join(self._estilo))
            self._estilo = None
        if tag == "svg" and self._svg is not None:
            if self._nivel_svg:
                self._nivel_svg -= 1
            else:
                inicio, n, cab, pista = self._svg
                fin = self.texto.find(">", self._pos()) + 1
                if pista:
                    self._candidato({"url": f"{urllib.parse.urldefrag(self.url)[0]}#svg-{n}",
                                     "pista": f"svg en línea{' en la cabecera' if cab else ''}; {pista}", "svg": self.texto[inicio:fin]}, cab)
                self._svg = None
        for i in range(len(self.pila) - 1, -1, -1):
            if self.pila[i][0] == tag:
                del self.pila[i:]
                break

    def handle_data(self, data):
        if self._estilo is not None:
            self._estilo.append(data)


def web(url, max_css, timeout):
    """El JSON de colores, theme-color, logos y tipografías de una web (ver el docstring del módulo)."""
    def fallo(msg, webfetch=True):
        print(f"marca.py web: {msg}" + ("\nSi el terminal no puede leer esa web, saca la marca con WebFetch: los colores en hex, la "
                                        "tipografía y la URL del logo, de la guía de marca o de la web oficial de la empresa." if webfetch else ""),
              file=sys.stderr)
        sys.exit(2)
    if urllib.parse.urlsplit(url).scheme not in ("http", "https"):
        if "://" in url or url.lower().startswith(("file:", "mailto:", "data:")):    # otra clase de URL (ftp://, file:…)
            fallo(f"la URL tiene que empezar por http:// o https://: {url}", webfetch=False)
        if re.fullmatch(r"[\w-]+(\.[\w-]+)+(/\S*)?", url.strip()):    # un dominio sin http(s)://
            fallo(f"la URL tiene que empezar por http:// o https://: prueba con https://{url.strip()}", webfetch=False)
        fallo(f"«{url}» no es una URL. Con solo el nombre de la empresa, busca con WebSearch «{url} manual de identidad "
              f"corporativa», «{url} brand guidelines» y «{url} logo SVG», y su web oficial; después pasa aquí su URL "
              "(https://…). Solo fuentes de la propia empresa.", webfetch=False)
    try:
        datos, final, charset, tipo = descargar(url, timeout, MAX_PAGINA)
    except urllib.error.HTTPError as e:
        fallo(f"{url} responde {e.code} ({e.reason})")
    except (urllib.error.URLError, OSError, ValueError, http.client.HTTPException) as e:
        fallo(f"no se pudo descargar {url}: {motivo(e, timeout)}")
    if tipo == "application/pdf" or datos.startswith(b"%PDF-"):
        fallo(f"{final} es un PDF ({tipo or 'sin Content-Type'}), no una página web: si es su guía de marca, léelo con la skill de "
              "PDF y saca de ahí los colores en hex, la tipografía y el logo.", webfetch=False)
    if tipo not in (None, "text/html", "application/xhtml+xml", "text/css"):
        fallo(f"{final} es {tipo}, no una página web (HTML) ni una hoja de estilo (CSS).", webfetch=False)
    if len(datos) > MAX_PAGINA:
        print(f"Aviso: la página pasa de {MAX_PAGINA // 2 ** 20} MB; se leen los primeros", file=sys.stderr)
    texto = texto_de(datos[:MAX_PAGINA], charset)
    css = tipo == "text/css"  # la URL de una hoja de estilo: sus colores y tipografías, sin logos
    pag = Pagina(final, "" if css else texto)
    # los bloques <style> (o la hoja) y, en cola, sus @import y las hojas enlazadas (las del mismo sitio, como mucho --max-css)
    hojas = [(final, t) for t in ([texto] if css else pag.estilos)]
    cola = [urllib.parse.urljoin(final, m) for _, t in hojas for m in IMPORT.findall(COMENTARIO.sub(" ", t))] + pag.hojas
    vistas, leidas = set(), 0
    while cola:
        u = urllib.parse.urldefrag(cola.pop(0))[0]
        if u in vistas:
            continue
        vistas.add(u)
        if not mismo_sitio(u, final):
            print(f"Hoja de otro sitio, sin descargar: {u}", file=sys.stderr)
            continue
        if leidas >= max_css:
            print(f"Hoja sin descargar (--max-css {max_css}): {u}", file=sys.stderr)
            continue
        try:
            d, uf, cs, _ = descargar(u, timeout, MAX_HOJA)
        except (urllib.error.URLError, OSError, ValueError, http.client.HTTPException) as e:
            print(f"Hoja de estilo sin descargar: {u} ({motivo(e, timeout)})", file=sys.stderr)
            continue
        leidas += 1
        if len(d) > MAX_HOJA:
            print(f"Hoja de estilo de más de 2 MB, sin leer: {u}", file=sys.stderr)
            continue
        t = texto_de(d, cs)
        hojas.append((uf, t))
        cola += [urllib.parse.urljoin(uf, m) for m in IMPORT.findall(COMENTARIO.sub(" ", t))]
    decl = [x for _, t in hojas for x in declaraciones(t)] + [x for s in pag.atributos_style for x in declaraciones(s, bloques=False)]
    defs = {}
    for p, v in decl:
        if p.startswith("--"):
            defs.setdefault(p, []).append(re.sub(r"url\([^)]*\)", "url()", v, flags=re.I))
    veces, orden, refs, familias = Counter(), {}, Counter(), Counter()

    def cuenta(c, n=1):
        veces[c] += n
        orden.setdefault(c, len(orden))
    for p, v in decl:
        v = re.sub(r"url\([^)]*\)", "url()", v, flags=re.I)
        for m in COLOR.finditer(v):
            c = color_hex(m.group())
            if c:
                cuenta(c)
        for m in VAR.finditer(v):
            refs[m.group(1)] += 1
        fam = primera_familia(v, defs) if p == "font-family" else primera_familia(familia_font(v) or "", defs) if p == "font" else None
        if fam:
            familias[fam] += 1
    for v in pag.colores_svg:
        c = color_hex(v)
        if c:
            cuenta(c)
    variables = {}
    for nombre in defs:
        valor = resolver(nombre, defs) or ""
        c = color_hex(valor) if COLOR.fullmatch(valor.strip()) else None
        if c:
            variables.setdefault(c, []).append(nombre)
            cuenta(c, refs[nombre])
    for fam in pag.familias_enlazadas:
        familias[fam] += 1
    colores = sorted((c for c in veces if not neutro(c)), key=lambda c: (-veces[c], orden[c]))[:MAX_COLORES]
    tipos, vistas_t = [], set()
    for fam, _ in sorted(familias.items(), key=lambda x: -x[1]):
        if fam.lower() not in vistas_t:
            vistas_t.add(fam.lower())
            tipos.append(fam)
    logos, urls = [], set()
    for entrada in [e for _, _, e in sorted(pag.candidatos, key=lambda x: x[:2])] + pag.iconos:
        if entrada["url"] not in urls:
            urls.add(entrada["url"])
            logos.append(entrada)
    tema = color_hex(pag.theme) if pag.theme else None
    json.dump({"url": final,
               "colores": [{"hex": c, "veces": veces[c], "variables": variables.get(c, []),
                            "contraste": {"blanco": round(contrast(c, BLANCO), 2), "negro": round(contrast(c, NEGRO), 2)}} for c in colores],
               "themeColor": tema or pag.theme, "logos": logos, "tipografias": tipos}, sys.stdout, ensure_ascii=False, indent=1)
    print()
