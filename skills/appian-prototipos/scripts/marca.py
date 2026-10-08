#!/usr/bin/env python3
"""
La configuración de marca de un cliente, para el prototipo y para Appian (references/marca.md).

Uso:
  python3 marca.py web <url> [--max-css 10] [--timeout 10]
  python3 marca.py crear --id <id> --nombre <nombre> --fuente "<de dónde sale, con la fecha>" --oscuro <hex>
      --realce <hex> --acento <hex> [--principal <hex>] [--secundarios <hex,hex…>] [--logo <svg>] [--logo-claro <svg>]
      [--formas SQUARED|SEMI_ROUNDED|ROUNDED] [--mayusculas si|no] [--tipografia <nombre>] [--sin-perfil-css] <carpeta>

web: descarga la página y las hojas de estilo que enlaza del mismo sitio (el mismo dominio, como www.x.es y
estaticos.x.es; como mucho --max-css, de 2 MB cada una) y escribe en la salida estándar un JSON con sus colores (los 20
más usados, sin blancos, negros ni grises; con las variables CSS que los definen y su contraste), su theme-color, sus
logos (los de la cabecera con «logo» primero; el icono del sitio, al final) y sus tipografías. Con la URL de una hoja de
estilo, lo mismo de esa hoja. Sin red o sin respuesta, o si la URL es un PDF u otra cosa que no es HTML ni CSS, sale con 2
y lo dice.

crear: escribe en <carpeta> (prototipo/ del proyecto, nunca dentro del plugin) brand-<id>.json, el logo junto a él
(logo-<id>-on-dark.svg y, con --logo-claro, logo-<id>-on-light.svg), perfil-css-<id>.txt (salvo con --sin-perfil-css) y
marca-<id>.md, la guía de marca para quien construye. Lo que no llega a WCAG 2.2 AA lo ajusta cambiando solo la
luminosidad (HLS), en pasos pequeños, y lo dice. Sale con 2 si un dato no vale o un ajuste no llega, sin escribir nada, y
si no puede escribir un fichero, diciendo cuáles llegó a escribir.

Solo biblioteca estándar. Reutiliza contrast(), _lineal() y check_css_profile() de validate.py y css_profile_text(),
mix_white() y on_color() de build.py.
"""
import argparse, colorsys, copy, http.client, ipaddress, json, math, os, re, socket, sys
sys.dont_write_bytecode = True  # sin __pycache__ en el plugin: no se escribe fuera del proyecto
import urllib.error, urllib.parse, urllib.request
from collections import Counter
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate import contrast, _lineal, check_css_profile, Report  # noqa: E402
from build import css_profile_text, mix_white, on_color  # noqa: E402
from entorno import utf8_stdio  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent  # la skill
# la carpeta del plugin: la que contiene skills/, lleve o no .claude-plugin/plugin.json (si la skill no está en una carpeta
# skills/, la propia skill)
PLUGIN = ROOT.parents[1] if ROOT.parent.name == "skills" else ROOT
BLANCO, NEGRO, GRIS_PAGINA, TEXTO = "#FFFFFF", "#000000", "#F4F5F7", "#222222"
PASO = 0.005                   # paso de luminosidad (HLS) de cada ajuste
MAX_HOJA = 2 * 1024 * 1024     # bytes de una hoja de estilo
MAX_PAGINA = 5 * 1024 * 1024   # bytes de la página
MAX_COLORES = 20
CASI_IGUAL = 15                # ΔE (CIE76) por debajo del cual dos series de un gráfico no se distinguen
# fondos estándar de los avisos de Appian (appianStandardColors de schemas/css-profile-properties.json; el perfil no los cambia)
FONDOS_AVISO = ("success-background-color", "info-background-color", "warn-background-color", "error-background-color")
UA = "Mozilla/5.0 (compatible; appian-prototipos marca.py)"
HEX6 = re.compile(r"#[0-9A-Fa-f]{6}")
FORMAS = ("SQUARED", "SEMI_ROUNDED", "ROUNDED")
FORMA_UI = {"SQUARED": "Squared", "SEMI_ROUNDED": "Semi-rounded", "ROUNDED": "Rounded"}
# radios del perfil CSS: los mismos píxeles que build.py da a cada forma (botones y campos, como los controles; tarjetas,
# como los diálogos). Con SQUARED no hay radios que cambiar: las esquinas rectas son las de Appian.
RADIO_CONTROL = {"SEMI_ROUNDED": "4px", "ROUNDED": "999px"}
RADIO_CONTENEDOR = {"SEMI_ROUNDED": "8px", "ROUNDED": "16px"}
MESES = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre")
DOCS = {"objeto Site": "https://docs.appian.com/suite/help/latest/sites_object.html",
        "perfiles CSS": "https://docs.appian.com/suite/help/latest/css-profiles.html",
        "propiedades del perfil CSS": "https://docs.appian.com/suite/help/latest/css-properties.html",
        "tipografías en perfiles CSS": "https://docs.appian.com/suite/help/latest/css-profile-typefaces.html",
        "Admin Console › Branding": "https://docs.appian.com/suite/help/latest/admin-branding.html"}


# ------------------------------------------------------------------ color
def rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def a_hex(r, g, b):
    return "#%02X%02X%02X" % tuple(max(0, min(255, round(x))) for x in (r, g, b))


def hls(h):
    return colorsys.rgb_to_hls(*(x / 255 for x in rgb(h)))


def de_hls(h, l, s):
    return a_hex(*(x * 255 for x in colorsys.hls_to_rgb(h, l, s)))


def razon(r):
    """4,56 → «4,5»: con un decimal y sin redondear hacia arriba (nunca se lee 4,5 donde hay 4,49)."""
    return f"{math.floor(r * 10 + 1e-9) / 10:g}".replace(".", ",")


def ajustar(color, cumple, sentido):
    """El color con solo la luminosidad (HLS) cambiada, en pasos de PASO (sentido -1 oscurece, +1 aclara), hasta que
    cumple(color). El mismo color si ya cumple; None si no llega ni en el extremo."""
    h, l, s = hls(color)
    c = color
    while not cumple(c):
        siguiente = min(1.0, max(0.0, l + sentido * PASO))
        if siguiente == l:
            return None
        l = siguiente
        c = de_hls(h, l, s)
    return c


def texto_sobre(c):
    """(color, contraste) del texto de un botón SOLID de color c: blanco o casi negro, el que más contraste da (on_color()
    de build.py, el mismo criterio que el runtime; en Appian el color del texto también es automático)."""
    t = on_color(c).upper()
    return t, contrast(t, c)


def gris(base, fondos, minimo, saturacion=0.12):
    """El gris más claro con el matiz de `base` (y saturación baja) que llega a `minimo` sobre cada fondo."""
    h, _, s = hls(base)
    s, l = min(s, saturacion), 1.0
    while l > 0:
        c = de_hls(h, l, s)
        if min(contrast(c, f) for f in fondos) >= minimo:
            return c
        l = round(l - PASO, 6)
    return de_hls(h, 0.0, s)


def tinte(c, pct=0.15):
    """El color al `pct` sobre blanco (fondos apagados de las etiquetas de estado, como en la marca estándar)."""
    return mix_white(c, pct).upper()


def lab(h):
    r, g, b = (_lineal(x) for x in rgb(h))
    xyz = ((0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047, 0.2126 * r + 0.7152 * g + 0.0722 * b,
           (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883)
    fx, fy, fz = (t ** (1 / 3) if t > 216 / 24389 else (24389 / 27 * t + 16) / 116 for t in xyz)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


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


def color_hex(t):
    """#RRGGBB de un color CSS (#rgb, #rgba, #rrggbb, #rrggbbaa, rgb(), rgba(), hsl(), hsla()); None si no lo es o es
    transparente del todo."""
    t = t.strip()
    if t.startswith("#"):
        x = t[1:]
        if len(x) in (3, 4):
            x = "".join(c * 2 for c in x)
        if len(x) not in (6, 8) or not re.fullmatch(r"[0-9a-fA-F]+", x) or (len(x) == 8 and int(x[6:], 16) == 0):
            return None
        return "#" + x[:6].upper()
    m = re.fullmatch(r"(rgba?|hsla?)\((.*)\)", t, re.I)
    if not m:
        return None
    partes = [p for p in re.split(r"[\s,/]+", m.group(2).strip()) if p]
    if len(partes) < 3:
        return None
    try:
        if len(partes) > 3 and (float(partes[3][:-1]) / 100 if partes[3].endswith("%") else float(partes[3])) == 0:
            return None
        if m.group(1).lower().startswith("rgb"):
            return a_hex(*(float(p[:-1]) * 2.55 if p.endswith("%") else float(p) for p in partes[:3]))
        h = partes[0].lower()
        for suf, f in (("deg", 1), ("grad", 0.9), ("rad", 180 / math.pi), ("turn", 360)):
            if h.endswith(suf):
                h = float(h[:-len(suf)]) * f
                break
        h, s, l = float(h) % 360 / 360, float(partes[1].rstrip("%")) / 100, float(partes[2].rstrip("%")) / 100
        return a_hex(*(x * 255 for x in colorsys.hls_to_rgb(h, l, s)))
    except ValueError:
        return None


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
LOGOS = {"logo", "logos", "logotipo", "logotipos", "logotype", "logotypes"}


def palabras(texto):
    """Las palabras de un atributo, en minúsculas: corta por lo que no es letra (también acentuada) y donde una minúscula va
    seguida de una mayúscula. site-logo, header__logo, siteLogo y logoImg llevan «logo»; catálogo, logout y blogger, no."""
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
    """¿Lleva «logo» (o logotipo, logos…) como palabra entera?"""
    return bool(palabras(texto) & LOGOS)


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
        fallo(f"la URL tiene que empezar por http:// o https://: {url}", webfetch=False)
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


# ------------------------------------------------------------------ crear
def dentro(carpeta, raiz):
    c, r = (Path(os.path.normcase(str(p.resolve()))) for p in (carpeta, raiz))
    return c == r or r in c.parents


def colores_svg(texto):
    """Colores de relleno y trazo de un SVG (atributos, style y <style>); sin ninguno, el negro por defecto del SVG."""
    out = []
    for m in re.finditer(r"(?:fill|stroke|stop-color)\s*(?:=\s*[\"']|:)\s*([^\"';}>]+)", texto, re.I):
        v = m.group(1).strip().lower()
        c = {"white": BLANCO, "black": NEGRO}.get(v) or color_hex(v)
        if c:
            out.append(c)
    return out or [NEGRO]


def limpiar_svg(texto):
    """El SVG sin lo que el navegador ejecutaría al pintarlo en la cabecera (scripts, foreignObject, atributos on…)."""
    t = re.sub(r"<script\b.*?</script\s*>", "", texto, flags=re.S | re.I)
    t = re.sub(r"<foreignObject\b.*?</foreignObject\s*>", "", t, flags=re.S | re.I)
    t = re.sub(r"\son[a-z]+\s*=\s*(\"[^\"]*\"|'[^']*'|[^\s>]+)", "", t, flags=re.I)
    t = re.sub(r"((?:xlink:)?href\s*=\s*[\"'])\s*javascript:[^\"']*", r"\1#", t, flags=re.I)
    return t


def fecha_larga(d):
    return f"{d.day} de {MESES[d.month - 1]} de {d.year}"


def esquema_graficos(marca, estandar):
    """([(color, origen)], [(color, origen)] de la marca que se quedan fuera): todas las series con 3:1 sobre blanco (WCAG
    1.4.11), como mucho 8. Primero los colores de la marca, sin repetir; después los de la estándar que no se parecen a
    ninguno de ellos (ΔE de CASI_IGUAL o más). El ΔE nunca quita un color de la marca."""
    out, fuera = [], []
    for c, origen in marca:
        if contrast(c, BLANCO) < 3:
            fuera.append((c, origen))
        elif all(c != o for o, _ in out):
            out.append((c, origen))
    propios = [c for c, _ in out]
    for c in estandar:
        c = c.upper()
        if contrast(c, BLANCO) >= 3 and c not in propios and all(math.dist(lab(c), lab(o)) >= CASI_IGUAL for o in propios):
            out.append((c, "estándar"))
    return out[:8], list(dict.fromkeys(fuera))


def sombra_tarjeta(color):
    """La sombra de las tarjetas del kit (--card-shadow de runtime/appian-kit.css) con el color `color`: los mismos
    desplazamientos, desenfoques y opacidades."""
    m = re.search(r"--card-shadow:\s*([^;]+);", (ROOT / "runtime" / "appian-kit.css").read_text(encoding="utf-8"))
    if not m:
        print("marca.py crear: no se encuentra --card-shadow en runtime/appian-kit.css; no se escribe nada.", file=sys.stderr)
        sys.exit(2)
    r, g, b = rgb(color)
    return re.sub(r"rgba\(\s*[\d.]+\s*,\s*[\d.]+\s*,\s*[\d.]+\s*,\s*([\d.]+)\s*\)",
                  lambda x: f"rgba({r}, {g}, {b}, {float(x.group(1)):g})", m.group(1).strip())


def crear(a):
    errores = []
    if not re.fullmatch(r"[a-z0-9-]+", a.id):
        errores.append(f"--id «{a.id}»: solo minúsculas, números y guiones ([a-z0-9-]); va en brand-<id>.json y en --brand")
    for opcion, valor in (("--nombre", a.nombre), ("--fuente", a.fuente)):
        if not valor.strip():
            errores.append(f"{opcion} vacío")
    colores = [("--oscuro", a.oscuro), ("--realce", a.realce), ("--acento", a.acento)] + ([("--principal", a.principal)] if a.principal else [])
    secundarios = [x.strip() for x in (a.secundarios or "").split(",") if x.strip()]
    colores += [("--secundarios", x) for x in secundarios]
    errores += [f"{o} «{v}» no es un color #RRGGBB" for o, v in colores if not HEX6.fullmatch(v)]
    logos = {}
    for opcion, ruta in (("--logo", a.logo), ("--logo-claro", a.logo_claro)):
        if ruta:
            p = Path(ruta)
            if not p.is_file():
                errores.append(f"{opcion}: no existe el logo {p}")
                continue
            try:
                t = p.read_text(encoding="utf-8", errors="replace")
            except OSError as e:
                errores.append(f"{opcion}: no se puede leer {p} ({e.strerror or e})")
                continue
            if not re.search(r"<svg\b", t, re.I):
                errores.append(f"{opcion}: {p} no es un SVG; si la marca solo lo tiene en PNG o JPG, crea la marca sin {opcion} y pide "
                               "el SVG (el PNG sirve para el Site de Appian)")
            logos[opcion] = t
    carpeta = Path(a.carpeta)
    if dentro(carpeta, PLUGIN):
        errores.append(f"{carpeta.resolve()} está dentro del plugin ({PLUGIN}): la marca de un cliente va en prototipo/ de su "
                       "proyecto, junto al app.json, nunca en el plugin")
    elif carpeta.exists() and not carpeta.is_dir():
        errores.append(f"{carpeta} no es una carpeta")
    if errores:
        print("marca.py crear: no se escribe nada.\n  " + "\n  ".join(errores), file=sys.stderr)
        sys.exit(2)

    est = json.loads((ROOT / "assets" / "brand-appian.json").read_text(encoding="utf-8"))
    std = json.loads((ROOT / "schemas" / "css-profile-properties.json").read_text(encoding="utf-8"))["appianStandardColors"]
    perfil = not a.sin_perfil_css
    ajustes, fallos, avisos = [], [], []

    def ajusta(rol, color, fondos, minimo, sentido, con_texto=False):
        """fondos: [(hex o lista de hex, cómo se dice)]; de una lista cuenta el que menos contraste da. con_texto: además, el
        texto encima (blanco o casi negro, el que más contraste da) con 4,5:1."""
        grupos = [([x] if isinstance(x, str) else list(x), d) for x, d in fondos]
        sobre = lambda c, fs: min(contrast(c, f) for f in fs)
        nuevo = ajustar(color, lambda c: all(sobre(c, fs) >= minimo for fs, _ in grupos) and (not con_texto or texto_sobre(c)[1] >= 4.5), sentido)
        if nuevo is None:
            fallos.append(f"{rol} {color}: ni {'oscureciéndolo' if sentido < 0 else 'aclarándolo'} del todo llega a {razon(minimo)}:1")
            return color
        if nuevo != color:
            partes = [f"{razon(sobre(nuevo, fs))}:1 {d}" for fs, d in grupos]
            dicho = f"{rol} {color} → {nuevo}: " + (", ".join(partes[:-1]) + " y " if len(partes) > 1 else "") + partes[-1] + f" (mínimo {razon(minimo)}:1)"
            if con_texto:
                t, rt = texto_sobre(nuevo)
                dicho += f"; su texto, {'blanco' if t == BLANCO else 'casi negro ' + t}, con {razon(rt)}:1 (mínimo 4,5:1)"
            ajustes.append(dicho)
        return nuevo
    up = {o: v.upper() for o, v in colores}
    oscuro = ajusta("oscuro", up["--oscuro"], [(BLANCO, "con texto blanco")], 4.5, -1)
    realce = ajusta("realce", up["--realce"], [(oscuro, f"sobre el oscuro {oscuro}")], 3, +1)
    # el acento (enlaces, pestañas, botones) y el botón principal van sobre blanco, el gris de página y los avisos de Appian
    # (sus fondos estándar, que el perfil no cambia): el acento, a 4,5:1; el botón principal, a 3:1, con su texto a 4,5:1
    claros = [(GRIS_PAGINA, f"sobre el gris de página {GRIS_PAGINA}"), (BLANCO, "sobre blanco"),
              ([std[k] for k in FONDOS_AVISO], "sobre los fondos de aviso de Appian")]
    acento = ajusta("acento", up["--acento"], claros, 4.5, -1)
    principal = ajusta("botón principal", up["--principal"], claros, 3, -1, con_texto=True) if "--principal" in up else None
    papeles = {oscuro, realce, acento, principal, *(up[o] for o in ("--oscuro", "--realce", "--acento", "--principal") if o in up)}
    secundarios = [x for x in dict.fromkeys(x.upper() for x in secundarios) if x not in papeles]  # sin repetir un color de otro papel
    # grises con el matiz del oscuro: texto secundario (tan legible como el SECONDARY de Appian sobre el gris de página),
    # marcador de posición (4,5:1), bordes y líneas que deben verse (3:1) y líneas finas
    fondos_claros = [BLANCO, GRIS_PAGINA]
    slate = gris(oscuro, fondos_claros, contrast(est["palette"]["slate"], GRIS_PAGINA))
    placeholder = gris(oscuro, fondos_claros, 4.5)
    linea = gris(oscuro, fondos_claros, 3)
    gris_claro = de_hls(hls(oscuro)[0], 0.91, min(hls(oscuro)[2], 0.12))

    # estados: el fondo de cada etiqueta, con su texto (STANDARD) a 4,5:1. «neutral», el tinte de slate (la estándar tiñe su
    # gris); «en curso», el del acento, con el oscuro como color; atención, positivo y negativo, los de la estándar
    def etiqueta_estado(c, *textos):
        pct = 0.15
        while pct > 0 and min(contrast(t, tinte(c, pct)) for t in textos) < 4.5:
            pct = round(pct - 0.01, 2)
        return tinte(c, pct)
    states = copy.deepcopy(est["states"])
    states["_comment"] = ("Paleta semántica de estados, común a toda la app. Tags en filas: fondo apagado (hex) con el texto STANDARD a 4,5:1. "
                          "Iconos, textos y barras: el enumerado. Neutral, el tinte del gris de la marca (slate); en curso, el oscuro de la "
                          "marca sobre el tinte del acento; atención, positivo y negativo, los de la marca estándar. Máximo dos colores no "
                          "neutros por grid; nunca el color solo (siempre con texto o icono).")
    states["neutral"]["tag"] = etiqueta_estado(slate, TEXTO)
    states["enCurso"].update({"tag": etiqueta_estado(acento, oscuro, TEXTO), "enum": oscuro})
    fallos += [f"etiqueta de estado «{k}» {v['tag']}: su texto no llega a 4,5:1" for k, v in states.items()
               if not k.startswith("_") and contrast(TEXTO, v["tag"]) < 4.5]
    # colores semánticos del perfil: el estándar de Appian, oscurecido hasta 4,5:1 sobre blanco y sobre su fondo. Los fondos se
    # quedan en los de Appian (más claros que las etiquetas): sobre ellos van los avisos con su botón, que es del acento
    semanticos = {}
    for texto, fondo, nombre in (("negative-on-light-color", "error-background-color", "negativo"),
                                 ("positive-on-light-color", "success-background-color", "positivo"),
                                 ("warn-on-light-color", "warn-background-color", "atención"),
                                 ("info-on-light-color", "info-background-color", "en curso")):
        bg = std[fondo]
        semanticos[texto] = ajusta(f"{texto} ({nombre})", std[texto], [(BLANCO, "sobre blanco"), (bg, f"sobre su fondo {bg}")], 4.5, -1) if perfil else std[texto]
    etiqueta = ajusta("etiqueta de los campos (el oscuro)", oscuro, [(BLANCO, "sobre blanco"), (GRIS_PAGINA, f"sobre {GRIS_PAGINA}")], 4.5, -1) if perfil else oscuro
    negativo = semanticos["negative-on-light-color"]
    asterisco = ajusta("asterisco de obligatorio", negativo, [(BLANCO, "sobre blanco"), (GRIS_PAGINA, f"sobre {GRIS_PAGINA}")], 4.5, -1) if perfil else negativo
    if fallos:
        print("marca.py crear: un ajuste de contraste no llega; no se escribe nada.\n  " + "\n  ".join(fallos), file=sys.stderr)
        sys.exit(2)

    forma = a.formas or "SQUARED"  # la de Appian: la marca solo cambia lo que dicta el cliente
    mayus = (a.mayusculas or "si") == "si"
    logo, logo_claro = (f"logo-{a.id}-on-dark.svg" if "--logo" in logos else None), (f"logo-{a.id}-on-light.svg" if "--logo-claro" in logos else None)
    limpios = {o: limpiar_svg(t) for o, t in logos.items()}
    avisos += [f"{o}: se quitan del SVG scripts y atributos de eventos (el prototipo no los ejecuta)" for o, t in logos.items() if limpios[o] != t]
    peor = min(colores_svg(logos["--logo"]), key=lambda c: contrast(c, oscuro)) if logo else None
    if peor and contrast(peor, oscuro) < 3:
        avisos.append(f"el logo lleva {peor}, con {razon(contrast(peor, oscuro))}:1 sobre el oscuro {oscuro} (mínimo 3:1): en la cabecera "
                      "no se verá; hace falta su versión en negativo (para fondo oscuro) en --logo")
    nombre_cp = a.nombre.replace("*/", "* /")
    tip = (a.tipografia or "").strip()
    site = {"_comment": f"Propiedades del objeto Site para {a.nombre}: el equipo de desarrollo las copia tal cual (marca-{a.id}.md).",
            "navigationLayout": "HEADER_BAR", "headerBarStyle": "MERCURY", "backgroundColor": oscuro, "selectedPageHighlightColor": realce,
            "accentColor": acento, "loadingBarColor": realce, "buttonShape": forma, "inputShape": "SEMI_ROUNDED" if forma == "ROUNDED" else forma,
            "dialogShape": forma, "useUppercase": mayus, "useUppercasePageTitles": mayus, "showUserMenu": True}
    if logo:
        site.update({"logo": logo, "logoAltText": a.nombre})
    marca_graf = [(acento, "acento")] + ([(principal, "botón principal")] if principal else []) + [(c, "secundario") for c in secundarios] \
        + [(oscuro, "oscuro"), (realce, "realce")]
    graf, graf_fuera = esquema_graficos(marca_graf, est["components"]["chartColorScheme"])
    palette = {"_comment": f"Colores de {a.nombre} para usar como hex en SAIL (fondos de cards y cajas, sellos, barras decorativas, gráficos). "
                           "Los helpers (scripts/sail_helpers.py) leen navy, slate, steel, red, greenDark, amber, lineStrong, pageBg y grayLight.",
               "navy": oscuro, "accent": acento, "highlight": realce}
    if principal:
        palette["principal"] = principal
    palette.update({f"secundario{i}": c for i, c in enumerate(secundarios, 1)})
    palette.update({"slate": slate, "steel": est["palette"]["steel"], "info": semanticos["info-on-light-color"],
                    "red": negativo, "greenDark": semanticos["positive-on-light-color"], "amber": est["palette"]["amber"],
                    "lineStrong": linea, "pageBg": GRIS_PAGINA, "grayLight": gris_claro, "white": BLANCO})
    components = copy.deepcopy(est["components"])
    components["primaryButton"]["color"] = principal or "ACCENT"
    components["primaryButton"]["_uso"] = "Un único botón SOLID por pantalla: la acción más frecuente" + ("" if principal else ". ACCENT, el acento de la marca")
    components["chartColorScheme"] = [c for c, _ in graf]
    components["_chartColorScheme"] = ("Series en este orden: primero los colores de la marca y después los de la marca estándar que no se parecen a "
                                       "ninguno de ellos; todas con 3:1 o más sobre blanco (WCAG 1.4.11)." +
                                       (" Fuera, por no llegar a 3:1: " + ", ".join(f"{c} ({o})" for c, o in graf_fuera) + "." if graf_fuera else ""))
    typeface = {"prototype": "Open Sans",
                "appian": (f"La tipografía de {a.nombre} es {tip}. En Appian se sube en Admin Console > Branding > Typefaces (WOFF2, WOFF, OTF o TTF, "
                           "pesos 300, 400, 600 y 700) y, desde 26.5, se elige en el perfil CSS del site; sin perfil CSS, se pone como tipografía "
                           "por defecto del entorno. El prototipo sigue con Open Sans.") if tip else est["typeface"]["appian"]}
    hoy = date.today()
    brand = {"id": a.id, "name": a.nombre, "source": f"{a.fuente.strip().rstrip('.')}. Configuración generada con scripts/marca.py el {fecha_larga(hoy)} (marca-{a.id}.md).",
             "site": site, "typeface": typeface, "palette": palette, "components": components,
             "appianSemanticApprox": copy.deepcopy(est["appianSemanticApprox"]), "states": states}
    if perfil:
        grupos = []
        sem = {t: c for t, c in semanticos.items() if c != std[t]}
        grupos.append(("Colores semánticos: texto e iconos de estado con 4,5:1 sobre blanco y sobre su fondo", sem))
        grupos.append(("Textos de los campos: etiqueta con el oscuro de la marca; instrucciones, marcador de posición y asterisco con 4,5:1",
                       {"label-on-light-color": etiqueta, "instructions-on-light-color": slate, "placeholder-text-on-light-color": placeholder,
                        "required-asterisk-on-light-color": asterisco}))
        campos = {"input-box-on-light-border-color": linea, "input-card-on-light-border-color": linea}
        if forma != "SQUARED":
            campos.update({"input-box-semi-rounded-border-radius": "4px", "input-card-semi-rounded-border-radius": "4px"})
        grupos.append(("Campos: borde con 3:1 sobre blanco y sobre el gris de página (WCAG 1.4.11)" + (" y esquinas de la marca" if forma != "SQUARED" else ""), campos))
        if forma != "SQUARED":
            grupos.append(("Botones: esquinas de la marca", {f"button-{'semi-' if forma == 'SEMI_ROUNDED' else ''}rounded-border-radius": RADIO_CONTROL[forma]}))
        tarjetas = {"card-box-shadow": sombra_tarjeta(oscuro),
                    "card-box-semi-rounded-border-radius": RADIO_CONTENEDOR["SEMI_ROUNDED"], "card-box-rounded-border-radius": RADIO_CONTENEDOR["ROUNDED"]}
        if forma != "SQUARED":
            tarjetas.update({"tag-standard-semi-rounded-border-radius": "4px", "tag-small-semi-rounded-border-radius": "4px"})
        grupos.append(("Tarjetas, cajas y etiquetas: la sombra del kit teñida del oscuro de la marca y esquinas", tarjetas))
        grupos.append(("Tooltips: fondo con el oscuro de la marca y texto blanco", {"tooltip-background-color": oscuro, "tooltip-text-color": BLANCO}))
        brand["cssProfile"] = {"_comment": f"Perfil CSS de Appian para los sites de {a.nombre} (Admin Console > Branding > CSS Profiles; capacidades "
                                           "avanzadas y premium). Solo lleva lo que cambia respecto a Appian: lo que no se incluye conserva el valor "
                                           f"estándar. build.py lo aplica al prototipo; perfil-css-{a.id}.txt es el texto para pegarlo tal cual.",
                               "name": nombre_cp,
                               "typeface": (f"{tip.replace('*/', '* /')}: súbela en Admin Console > Branding > Typefaces y elígela en este perfil "
                                            "(26.5 o posterior); hasta entonces, Open Sans") if tip else "Open Sans (la de Appian)",
                               "groups": [{"comment": c, "properties": p} for c, p in grupos if p]}
        rep = Report()
        check_css_profile(brand, rep)
        if rep.errors:
            print("marca.py crear: el perfil CSS no es válido; no se escribe nada.\n  " + "\n  ".join(rep.errors), file=sys.stderr)
            sys.exit(2)

    guia = guia_md(a, brand, graf, graf_fuera, ajustes, avisos, logo, logo_claro, peor, tip, hoy)
    ficheros = [(f"brand-{a.id}.json", json.dumps(brand, ensure_ascii=False, indent=2) + "\n", "")]
    ficheros += [(nombre, limpios[opcion], "") for opcion, nombre in (("--logo", logo), ("--logo-claro", logo_claro)) if nombre]
    if perfil:
        ficheros.append((f"perfil-css-{a.id}.txt", css_profile_text(brand), " (perfil CSS para Admin Console › Branding › CSS Profiles)"))
    ficheros.append((f"marca-{a.id}.md", guia, " (guía de marca para quien construye)"))
    escritos = []
    try:
        carpeta.mkdir(parents=True, exist_ok=True)
        for nombre, texto, nota in ficheros:
            (carpeta / nombre).write_text(texto, encoding="utf-8")
            escritos.append((nombre, nota))
    except OSError as e:
        print(f"marca.py crear: no se pudo escribir {e.filename or carpeta} ({e.strerror or e}). Llegaron a escribirse en {carpeta}: "
              + (", ".join(n for n, _ in escritos) if escritos else "ninguno") + ". Corrige el problema y vuelve a ejecutar crear.", file=sys.stderr)
        sys.exit(2)
    print(f"Marca «{a.nombre}» ({a.id}):")
    print("Ajustes de contraste (WCAG 2.2 AA; solo la luminosidad):\n  " + "\n  ".join(ajustes) if ajustes else
          f"Ajustes de contraste: ninguno; lo que se comprueba (marca-{a.id}.md) llega a WCAG 2.2 AA tal cual.")
    for x in avisos:
        print(f"Aviso: {x}")
    print("\n".join(f"OK → {carpeta / n}{nota}" for n, nota in escritos))
    print(f"Siguiente: validate.py y build.py con --brand {a.id} (app.json en {carpeta}) y contrast_audit.py sobre el HTML.")
    # la fecha de hoy al final de la fuente no se repite: «sacada de su web el 8 de octubre de 2026»
    fuente = re.sub(rf",?\s*(?:el\s+)?{re.escape(fecha_larga(hoy))}$", "", a.fuente.strip().rstrip(".")).strip() or a.fuente.strip()
    print(f"$assumption de app: «Marca de {a.nombre} sacada de {fuente} el {fecha_larga(hoy)}; falta que la confirme el cliente»")


def guia_md(a, brand, graf, graf_fuera, ajustes, avisos, logo, logo_claro, peor, tip, hoy):
    """marca-<id>.md: la guía de marca del proyecto para quien construye."""
    site, pal, st, cp = brand["site"], brand["palette"], brand["states"], brand.get("cssProfile")
    si = lambda v: "Sí" if v else "No"
    contr = lambda c: f"{razon(contrast(c, BLANCO))}:1"
    y = lambda xs: ", ".join(xs[:-1]) + " y " + xs[-1] if len(xs) > 1 else xs[0]
    fuente = a.fuente.strip().rstrip(".")
    L = [f"# Marca de {a.nombre}", "",
         f"Configuración de marca del proyecto para el prototipo y para Appian, generada con `marca.py` el {fecha_larga(hoy)}. Fuente: {fuente}. "
         "Qué contraste se ha comprobado y qué se ha ajustado está en «Ajustes de contraste». "
         f"En el prototipo: `--brand {a.id}` en `validate.py` y `build.py`, y `sail_helpers.usar_marca(\"{a.id}\", r\"<p>/prototipo\")` en el script del spec.",
         "", "## Configuración del Site", "", "En el objeto Site, tal cual:", "", "| Propiedad | Valor |", "|---|---|"]
    filas = [("Navigation Bar › Layout (`navigationLayout`)", "HEADER BAR"), ("Navigation Bar › Style (`headerBarStyle`)", "MERCURY"),
             ("Navigation Bar › Background Color (`backgroundColor`)", f"`{site['backgroundColor']}`"),
             ("Navigation Bar › Selected Page Highlight Color (`selectedPageHighlightColor`)", f"`{site['selectedPageHighlightColor']}`"),
             ("Navigation Bar › Logo (`logo`)", f"Documento PNG de `{logo}` (ver «Logo»)" if logo else "None (sin logo: pendiente)")]
    if logo:
        filas.append(("Navigation Bar › Logo Alternative Text (`logoAltText`)", site["logoAltText"]))
    filas += [("Navigation Bar › Use uppercase capitalization for page titles (`useUppercasePageTitles`)", si(site["useUppercasePageTitles"])),
              ("Navigation Bar › Show user menu (`showUserMenu`)", si(site["showUserMenu"])),
              ("Branding › Accent Color (`accentColor`)", f"`{site['accentColor']}`"),
              ("Branding › Loading Bar Color (`loadingBarColor`)", f"`{site['loadingBarColor']}`"),
              ("Branding › Favicon Image", "Pendiente: un ICO de 16 × 16 o 32 × 32 px y menos de 100 KB"),
              ("Branding › Use uppercase capitalization for button labels (`useUppercase`)", si(site["useUppercase"])),
              ("Branding › Button Shape (`buttonShape`)", FORMA_UI[site["buttonShape"]]),
              ("Branding › Input Shape (`inputShape`)", FORMA_UI[site["inputShape"]] + (" (los campos no admiten Rounded)" if site["buttonShape"] == "ROUNDED" else "")),
              ("Branding › Dialog Shape (`dialogShape`)", FORMA_UI[site["dialogShape"]]),
              ("Branding › CSS Profile", f"«{cp['name']}» (ver «Perfil CSS»)" if cp else "Default (esta marca no lleva perfil propio)")]
    L += [f"| {p} | {v} |" for p, v in filas]
    L += ["", "## Perfil CSS", ""]
    if cp:
        L += [f"Ajusta lo que el Site no alcanza: colores de estado, textos y bordes de los campos, esquinas, sombras y tooltips. Pide las "
              f"capacidades avanzadas o premium de Appian. Se crea en Admin Console › Branding › CSS Profiles › Add profile, con el nombre "
              f"«{cp['name']}», su tipografía y, en el cuadro de propiedades, el texto de `perfil-css-{a.id}.txt` tal cual; después se elige en "
              "el Site (Branding › CSS Profile). Lo que no está en el perfil conserva el valor estándar de Appian. Los comentarios `/* */` los "
              "admite Appian desde 26.9: en una versión anterior, quítalos antes de pegar. El perfil no se aplica en Appian Mobile.", "",
              "| Grupo | Propiedades |", "|---|---|"]
        L += [f"| {g['comment'].split(':')[0]} | " + " · ".join(f"`{k}: {v}`" for k, v in g["properties"].items()) + " |" for g in cp["groups"]]
    else:
        L += ["Esta marca no lleva perfil CSS: Appian usa sus colores estándar de estado, campos y tooltips, y el prototipo, igual. Si el "
              "cliente tiene las capacidades avanzadas o premium y quiere uno, se genera de nuevo sin `--sin-perfil-css`."]
    para = {"navy": "Oscuro: cabecera del site, de las fichas y del inicio («hero»), barra lateral del asistente" + (" y tooltips" if cp else ""),
            "accent": "Acento: enlaces, pestañas, bordes OUTLINE" + ("" if pal.get("principal") else " y botón principal"),
            "highlight": "Realce: página seleccionada, barra de carga y barra decorativa de la franja de KPI"
                         + ("; nunca texto sobre blanco" if contrast(pal["highlight"], BLANCO) < 4.5 else ""),
            "principal": "Botón principal (SOLID)", "slate": "Texto secundario e instrucciones de los campos",
            "steel": "Tipo «Evento» del calendario", "info": "Azul informativo (avisos INFO)", "red": "Rojo de error y tipo «Plazo» del calendario",
            "greenDark": "Verde de éxito y tipo «Turno» del calendario", "amber": "Icono de aviso cuando WARN no llega a 3:1 sobre su fondo",
            "lineStrong": "Bordes de campo y líneas que tienen que verse (3:1)", "pageBg": "Gris de las páginas con tarjetas",
            "grayLight": "Líneas finas y separadores", "white": "Tarjetas y formularios"}
    if pal.get("principal"):
        t, r = texto_sobre(pal["principal"])
        para["principal"] += f"; su texto, {'blanco' if t == BLANCO else 'casi negro ' + t}, con {razon(r)}:1 (en Appian, el color del texto es automático)"
    L += ["", "## Paleta", "", "| Color | Hex | Para qué | Contraste sobre blanco |", "|---|---|---|---|"]
    for k, v in pal.items():
        if not k.startswith("_"):
            L.append(f"| `{k}` | `{v}` | {para.get(k, 'Color de apoyo de la marca (gráficos y barras decorativas)')} | {contr(v)} |")
    comp = brand["components"]
    pb = comp["primaryButton"]["color"]
    L += ["", "## Botones y tarjetas", "", "| Uso | Configuración en SAIL |", "|---|---|",
          f"| Acción principal (una por pantalla) | `style: \"SOLID\"`, `color: \"{pb}\"` |",
          "| Resto de acciones | `style: \"OUTLINE\"`, `color: \"ACCENT\"` |",
          "| Destructiva (pérdida real de datos) | `style: \"GHOST\"`, `color: \"NEGATIVE\"`, con `confirmHeader` y `confirmMessage` |",
          "| Barra de herramientas | `size: \"SMALL\"`, `style: \"OUTLINE\"`, `color: \"SECONDARY\"` |",
          "| Tarjeta de contenido | `a!cardLayout(style: \"NONE\", showBorder: false, showShadow: true, shape: \"SEMI_ROUNDED\", padding: \"STANDARD\")` "
          "sobre `a!headerContentLayout(backgroundColor: \"TRANSPARENT\")` |",
          "| Formularios, asistentes y diálogos | Fondo `WHITE`, sin tarjetas de contenido |", "",
          f"Esquinas: botones y diálogos {FORMA_UI[site['buttonShape']]} y campos {FORMA_UI[site['inputShape']]} en el Site"
          + ("." if not cp else "; con el perfil, tarjetas 8px (16px las redondeadas)." if site["buttonShape"] == "SQUARED" else
             f"; con el perfil, botones {RADIO_CONTROL[site['buttonShape']]}, campos y etiquetas 4px y tarjetas 8px (16px las redondeadas).")]
    L += ["", "## Estados", "", "| Estado | Fondo de la etiqueta | Color | Para qué |", "|---|---|---|---|"]
    L += [f"| {k} | `{v['tag']}` | `{v['enum']}` | {v.get('uso', '')} |" for k, v in st.items() if not k.startswith("_")]
    L += ["", "Etiquetas con texto `STANDARD` sobre su fondo (4,5:1 o más); como mucho dos colores no neutros por grid; nunca el color solo."]
    L += ["", "## Gráficos", "", "Series en este orden (`chartColorScheme`):", ""]
    L += [f"{i}. `{c}` · {o} · {contr(c)} sobre blanco" for i, (c, o) in enumerate(graf, 1)]
    L += ["", "Todas llegan a 3:1 sobre blanco (WCAG 1.4.11): primero los colores de la marca y después los de la estándar que no se parecen "
          "a ninguno de ellos. Un gráfico usa como mucho 5 colores y lleva su tabla."]
    if graf_fuera:
        L += ["", "Fuera, por no llegar a 3:1 sobre blanco: " + y([f"`{c}` ({o}, {contr(c)})" for c, o in graf_fuera]) + "."]
    L += ["", "## Tipografía", "", "| Dónde | Tipografía |", "|---|---|", f"| Marca | {tip or 'Sin dato: pendiente'} |",
          "| Prototipo | Open Sans, la que lleva el kit |",
          "| Appian | " + (f"{tip}: se sube en Admin Console › Branding › Typefaces (WOFF2, WOFF, OTF o TTF, pesos 300, 400, 600 y 700) y, "
                            "desde 26.5, se elige en el perfil CSS del site; sin perfil, como tipografía por defecto del entorno |" if tip else
                            "Open Sans, la de Appian |")]
    L += ["", "## Logo", ""]
    ficheros = ([(logo, "Cabecera del site (fondo oscuro); el prototipo lo pinta tal cual")] if logo else []) + \
        ([(logo_claro, "Fondos claros (portadas, documentos)")] if logo_claro else [])
    if ficheros:
        L += ["| Fichero | Para qué |", "|---|---|"] + [f"| `{f}` | {u} |" for f, u in ficheros] + [""]
    nota = "En Appian, el logo del Site es un documento JPG, PNG, BMP o GIF de menos de 100 KB, con fondo transparente (no SVG)"
    if logo:
        r = contrast(peor, site["backgroundColor"])
        L.append(f"{nota}: exporta `{logo}` a PNG. Texto alternativo: «{site['logoAltText']}». Su color con menos contraste sobre el "
                 f"oscuro, `{peor}`, " + (f"llega a {razon(r)}:1 (mínimo 3:1)." if r >= 3 else
                                          f"se queda en {razon(r)}:1 (mínimo 3:1): hace falta su versión en negativo."))
    else:
        L.append(f"Falta el logo para fondo oscuro: la cabecera del prototipo va sin él. {nota}.")
    L += ["", "## Fuentes", "", f"- Marca: {fuente}.", f"- Configuración generada con `marca.py` el {fecha_larga(hoy)}.",
          "- Appian: " + "; ".join(f"{k} ({u})" for k, u in DOCS.items()) + "."]
    # lo que se comprueba, y nada más: la guía no dice «AA» de lo que no se ha medido
    hecho = ["El oscuro con texto blanco: 4,5:1.", "El realce sobre el oscuro: 3:1.",
             "El acento sobre blanco, sobre el gris de página y sobre los fondos de aviso de Appian: 4,5:1."]
    if pal.get("principal"):
        hecho.append("El botón principal sobre esos mismos fondos, 3:1, y su texto, 4,5:1.")
    hecho += ["El texto secundario (`slate`), 4,5:1, y las líneas que deben verse (`lineStrong`), 3:1, sobre blanco y sobre el gris de página.",
              "El texto de cada etiqueta de estado sobre su fondo: 4,5:1."]
    if cp:
        hecho.append("Con el perfil, los colores de estado sobre blanco y sobre su fondo y los textos de los campos: 4,5:1.")
    hecho.append("Las series de los gráficos sobre blanco: 3:1.")
    sin_medir = (["Los colores secundarios en las barras decorativas (en los gráficos solo van si llegan a 3:1)."] if any(k.startswith("secundario") for k in pal) else []) \
        + (["El logo, salvo su color con menos contraste sobre el oscuro (ver «Logo»)."] if logo else [])
    L += ["", "## Ajustes de contraste", "", "Comprobado con WCAG 2.2 AA, con estos mínimos:", ""] + [f"- {x}" for x in hecho]
    if sin_medir:
        L += ["", "Sin comprobar:", ""] + [f"- {x}" for x in sin_medir]
    L += [""] + ((["Ajustes (solo la luminosidad; matiz y saturación se mantienen):", ""] + [f"- {x}" for x in ajustes]) if ajustes else
                 ["Ajustes: ninguno; lo comprobado llega tal cual."])
    if avisos:
        L += ["", "Avisos:", ""] + [f"- {x}" for x in avisos]
    pend = [f"Que los colores y el logo de {a.nombre} son los vigentes y el papel de cada uno: oscuro, realce, acento y botón principal."]
    if ajustes:
        pend.append("Los colores ajustados por contraste: en Appian sustituyen a los de la marca.")
    pend.append("El logo en PNG para el Site y el icono del sitio (ICO)." if logo else "El logo para fondo oscuro (SVG para el prototipo; PNG para el Site) y el icono del sitio (ICO).")
    if any("logo lleva" in x for x in avisos):
        pend.append("La versión en negativo del logo: la de ahora no se ve sobre el oscuro.")
    if cp:
        pend.append("Que el entorno tiene las capacidades avanzadas o premium que pide el perfil CSS.")
    if not a.formas:
        pend.append("Las esquinas: Squared, las de Appian, sin dato de la marca (se eligen mirando los botones y los campos de su web).")
    if not a.mayusculas:
        pend.append("Las mayúsculas en botones y títulos de página: las de Appian (sí), sin dato de la marca.")
    pend.append(f"Los ficheros de la tipografía {tip} (WOFF2, WOFF, OTF o TTF) para subirlos a Appian." if tip else "La tipografía de la marca, si tiene una propia.")
    L += ["", "## Pendiente de confirmar con el cliente", ""] + [f"- {x}" for x in pend]
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(description="La configuración de marca de un cliente para el prototipo y para Appian (references/marca.md).")
    sub = ap.add_subparsers(dest="orden", required=True)
    w = sub.add_parser("web", help="colores, logos y tipografías de una web, en JSON")
    w.add_argument("url")
    w.add_argument("--max-css", type=int, default=10, help="hojas de estilo del mismo sitio que se descargan (por defecto, 10)")
    w.add_argument("--timeout", type=float, default=10, help="segundos de espera de cada descarga (por defecto, 10)")
    c = sub.add_parser("crear", help="brand-<id>.json, logo, perfil CSS y guía de marca en <carpeta>")
    c.add_argument("--id", required=True, help="[a-z0-9-]: va en brand-<id>.json y en --brand")
    c.add_argument("--nombre", required=True, help="nombre de la empresa")
    c.add_argument("--fuente", required=True, help="de dónde salen los valores, con la fecha")
    c.add_argument("--oscuro", required=True, help="color oscuro de la marca: cabecera del site, con texto blanco")
    c.add_argument("--realce", required=True, help="color de realce: página seleccionada, sobre el oscuro")
    c.add_argument("--acento", required=True, help="color de acento: enlaces, pestañas y botones")
    c.add_argument("--principal", help="color del botón principal (por defecto, ACCENT)")
    c.add_argument("--secundarios", help="otros colores de la marca, separados por comas")
    c.add_argument("--logo", help="SVG del logo para fondo oscuro (la cabecera del site)")
    c.add_argument("--logo-claro", help="SVG del logo para fondo claro")
    c.add_argument("--formas", choices=FORMAS, help="esquinas de botones, campos y diálogos, como las de su web: rectas, SQUARED "
                                                    "(por defecto, la de Appian); redondeadas, SEMI_ROUNDED; píldora, ROUNDED")
    c.add_argument("--mayusculas", choices=("si", "no"), help="mayúsculas en botones y títulos de página (por defecto, si, como el Site de Appian)")
    c.add_argument("--tipografia", help="tipografía de la marca")
    c.add_argument("--sin-perfil-css", action="store_true", help="sin perfil CSS (el entorno no tiene las capacidades avanzadas o premium)")
    c.add_argument("carpeta", help="prototipo/ del proyecto, junto al app.json")
    a = ap.parse_args()
    utf8_stdio()
    if a.orden == "web":
        web(a.url, a.max_css, a.timeout)
    else:
        crear(a)


if __name__ == "__main__":
    main()
