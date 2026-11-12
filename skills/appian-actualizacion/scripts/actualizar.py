#!/usr/bin/env python3
"""actualizar.py - Instala un bundle del Dev MCP de Appian y dice qué hay instalado y qué cambió.

  python3 actualizar.py estado   [--servidor DIR] [--bundle FICHERO] [--proyecto DIR]
  python3 actualizar.py foto     [--servidor DIR] [--catalogo FICHERO]
  python3 actualizar.py instalar BUNDLE [--servidor DIR] [--plugin-sha SHA] [--uv RUTA] [--skills-dir DIR]…
                                 [--catalogo FICHERO]
  python3 actualizar.py informe  [--servidor DIR] [--catalogo FICHERO] [--antes DIR] [--despues DIR] [--json]
  python3 actualizar.py sail-anterior [--servidor DIR]
  python3 actualizar.py comprobar [--extraccion DIR] [--host ENTORNO --solicitante USUARIO --aprobador USUARIO]

Una foto es una copia, sin transformar, de lo que un bundle de Appian publica y el plugin usa:
  BUILD-INFO.txt          el build del servidor del Dev MCP
  skill.bundle-manifest   el manifiesto de la skill oficial `appian` (una huella por fichero)
  sail-help/<orden>.txt   la ayuda de cada orden de SAIL CLI (_general.txt y _version.txt, las de `sail`)
  devmcp.json             el catálogo de herramientas del Dev MCP, si se da con --catalogo:
                          {herramienta: {"parametros": {nombre: tipo}, "obligatorios": [...],
                                         "descripcion": huella, "esquema": huella}}
                          --catalogo admite el mcp_catalog.json que deja el extractor de ingeniería inversa
                          (`devmcp_extract.py plan`, en <salida>/extraccion/) y lo resume así
Se guardan por instalación y build en ~/.appian-analisis-funcional/actualizaciones/ (con $APPIAN_RE_HOME, en esa
carpeta personal). `foto` rehace entera la del build instalado: lo que ahora no hay, no queda de antes. `instalar` e
`informe` usan la que haya de ese build y solo la hacen si falta o si se les da un catálogo. `informe` compara la
del build instalado con la del build anterior (o las dos que se le den): herramientas nuevas, desaparecidas y con
otro esquema, ficheros de la skill oficial y órdenes y opciones de SAIL CLI, y en qué ficheros de las skills del
plugin aparece el nombre de una herramienta que cambió o desapareció.

El informe dice qué cambió, no qué se rompió. Una pieza que falta en una foto (sin SAIL CLI, sin catálogo) sale como
«sin foto», no como «sin cambios».

`instalar` hace lo que manda la guía de Appian (https://docs.appian.com/suite/help/latest/devmcp.html) y, antes, lo que
Appian no hace. Por este orden:
  1. Comprueba, sin tocar nada, que el bundle se puede instalar: es un bundle con la forma que este script conoce,
     solo trae ficheros y carpetas dentro de su sitio, no es más antiguo que lo instalado, es el del plugin del
     entorno (--plugin-sha, el mcpSrcSha que da el Dev MCP) y hay `uv`.
  2. Lo extrae entero en una carpeta aparte, dentro de la del servidor. Si no se puede, la instalación sigue igual.
  3. Hace la foto de lo instalado y guarda el bundle anterior (lo instalado menos el entorno de `uv`) como
     bundle.tar.gz en la carpeta de esa foto, y lo relee entero antes de darlo por bueno.
  4. Solo entonces sustituye lo que trae el bundle y quita lo que el anterior trajo en la raíz y este ya no trae (si
     lo instaló este script, que lo apunta; queda en el bundle anterior guardado); lo demás de la carpeta del servidor
     no se toca. Mientras dura, deja una
     marca: si se corta, las demás órdenes lo dicen y `instalar`, con ese mismo bundle, la termina sin repetir la
     foto ni la copia.
  5. Lanza `uv sync`, el `bin/setup-*` del sistema (SAIL CLI) y `bin/install-skills` (la skill oficial: en los
     clientes que detecta Appian y en cada --skills-dir), en ese orden. Ninguno depende de otro: se hacen todos y,
     si alguno falla, dice cuáles y sale con 1.
La misma orden se puede repetir. Un bundle es el instalado si coinciden su fecha de build y su mcp_src_sha: repetida
con él, vuelve a dejar lo que trae, sin foto ni copia, y un cambio hecho a mano en esas carpetas se pierde. Se guarda
un solo bundle anterior. `sail-anterior` saca de él el SAIL CLI de este sistema y dice cómo usarlo. El bundle se
descarga del propio entorno: --plugin-sha comprueba que es el que ese entorno espera, no quién lo hizo. No hay
bloqueo entre dos instalaciones: no lances dos a la vez sobre la misma carpeta.

`comprobar` pasa el banco de pruebas (assets/banco/), entero o la parte que se le pida:
  --extraccion DIR   mira la extracción de su aplicación hecha con el extractor de ingeniería inversa, contra
                     assets/banco/esperado.json: que encuentre al menos los objetos de cada tipo, que el modelo que el
                     extractor arma con las respuestas (lanza su build_model.py, que lo deja en esa carpeta) diga lo
                     que dice la especificación y que no haya errores fuera de los previstos. Una herramienta con
                     errores en tres tipos de objeto o más suele ser de un tipo que la política del extractor no
                     conoce.
  --host ENTORNO --solicitante USUARIO --aprobador USUARIO [--site SITE]
                     repite con `qa.py`, de appian-qa, los guiones de assets/banco/guiones/ en ese entorno y con esas
                     cuentas, que tienen que tener su sesión de sail abierta.

--servidor es la carpeta donde está extraído el bundle; sin él, la de la guía de Appian (~/appian-dev-mcp-server).
SAIL CLI es `sail` del PATH o el de $SAIL_CLI, como en appian-qa.

Códigos de salida: 0 bien | 1 instalar: falló después de empezar a sustituir (se puede repetir); comprobar: el
banco no pasa | 2 falta algo o uso incorrecto, sin haber tocado la instalación (no la hay, no hay
foto anterior, un fichero ilegible, un bundle que no vale), o comprobar: no se pudo comprobar.
"""
import argparse
import difflib
import gzip
import hashlib
import json
import os
import pathlib
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zlib

sys.dont_write_bytecode = True

ESTADO = ".appian-analisis-funcional"       # la carpeta personal del plugin; el nombre, solo aquí
GUIA = "appian-dev-mcp-server"              # donde la guía de Appian manda extraer el bundle
GUIA_WEB = "https://docs.appian.com/suite/help/latest/devmcp.html"
PLUGIN = pathlib.Path(__file__).resolve().parents[3]
CITAN = (".md", ".py", ".json")             # los ficheros de las skills donde se busca lo que cambió
SIN_AYUDA = {"completion", "help"}          # órdenes de sail que no son suyas: las pone su biblioteca
ESPERA = 60                                 # segundos que se espera a cada orden de sail
ESPERA_INSTALAR = 900                       # y a cada paso de la instalación (uv sync puede descargar)
MAX_LINEAS = 12                             # líneas de ayuda cambiadas que enseña el informe por orden
RX_BUILD = re.compile(r"[0-9]{8}-[0-9]{6}")  # build_timestamp: nombra la carpeta de la foto y ordena los builds
# Lo que puede fallar al leer un .tar.gz que no está entero o no lo es: una descarga cortada es lo más corriente
NO_ES_TAR = (OSError, tarfile.TarError, EOFError, zlib.error, ValueError)
DE_LA_FOTO = ("BUILD-INFO.txt", "skill.bundle-manifest", "sail-help", "devmcp.json")
A_MEDIAS = ".instalando"                    # marca en la carpeta del servidor mientras se sustituye su contenido
APARTE = ".nuevo"                           # donde se extrae el bundle antes de sustituir nada
# En la carpeta del servidor, lo que no es del bundle: el entorno que crea `uv sync` y lo que usa `instalar`. Un bundle
# no puede traerlo, con estas u otras mayúsculas; no entra en el bundle anterior que se guarda y no se borra.
RESERVADAS = {".venv", A_MEDIAS, APARTE}
# Nombres que Windows no admite como fichero: un bundle que los trajera no se podría extraer igual en todos los sistemas
DISPOSITIVOS = {"CON", "PRN", "AUX", "NUL", *(f"{d}{i}" for d in ("COM", "LPT") for i in "123456789¹²³")}
SIN_SU_AYUDA = "(sail {orden} --help falló al hacer la foto)"   # la orden está, pero no se pudo leer su ayuda
SIN_CLIENTES = "No AI client detected"      # lo que dice install-skills de Appian cuando no encuentra ningún cliente suyo
ESPERADO = pathlib.Path(__file__).resolve().parents[1] / "assets" / "banco" / "esperado.json"
MODELO = PLUGIN / "skills" / "appian-reverse-engineering" / "scripts" / "build_model.py"   # el que arma el extractor
GUIONES = ESPERADO.parent / "guiones"       # los recorridos del banco, como guiones de appian-qa sin entorno ni cuentas
UNIDAD_BANCO = "BPS-01"                     # el nombre de unidad con el que qa.py repite esos guiones
TIPOS_DE_GENERICA = 3   # una herramienta con errores en tantos tipos de objeto no es de ninguno: se probó en todos
# Lo que `instalar` lanza de un bundle, además de `uv sync` sobre su pyproject.toml. Por sistema: cómo llama Appian a su
# SAIL CLI en bin/, el script que lo instala y el que instala la skill oficial.
SISTEMAS = {"Windows": ("windows", "setup-windows.bat", "install-skills.bat"),
            "Darwin": ("darwin", "setup-mac.sh", "install-skills.sh"),
            "Linux": ("linux", "setup-linux.sh", "install-skills.sh")}


def escribe(fichero, texto):
    """Entero o nada: lo escribe aparte y lo pone en su sitio de una vez, para que un corte no deje medio fichero. Con
    finales de línea de Unix en cualquier sistema (write_text no admite newline hasta Python 3.10)."""
    parcial = fichero.with_name(fichero.name + ".parcial")
    parcial.write_bytes(texto.replace("\r\n", "\n").encode("utf-8"))
    os.replace(parcial, fichero)


def fin(codigo, texto):
    sys.stdout.flush()   # lo ya dicho, antes que el cierre: si no, al redirigir los dos, el cierre puede salir primero
    print(texto, file=sys.stderr if codigo else sys.stdout)
    sys.exit(codigo)


def desde_aqui(ruta):
    """La ruta, entera desde donde se lanza la orden y con sus enlaces sin tocar. En Windows, con abspath: con Python
    3.9, resolve() deja relativa una ruta que aún no existe. En los demás sistemas solo se le pone delante la carpeta
    actual: abspath quita los `..` sin mirar los enlaces y, detrás de un enlace, eso es otra carpeta."""
    return os.path.abspath(ruta) if platform.system() == "Windows" else os.path.join(os.getcwd(), ruta)


def absoluta(ruta):
    """Una ruta que da la persona, entera y con los enlaces resueltos: los instaladores se lanzan desde otra carpeta."""
    return pathlib.Path(desde_aqui(pathlib.Path(ruta).expanduser())).resolve()


def ruta_dada(texto):
    """El tipo de los argumentos que son rutas: las órdenes las reciben ya absolutas. Una que no se puede entender (un
    `~usuario` que no existe, un enlace que da vueltas) la dice argparse, que sale con 2, y no una traza."""
    try:
        return absoluta(texto)
    except (OSError, RuntimeError) as e:
        raise argparse.ArgumentTypeError(f"no se entiende la ruta {texto!r} ({e})")


def casa():
    return absoluta(os.environ.get("APPIAN_RE_HOME") or pathlib.Path.home())


def leer_json(fichero):
    """El objeto JSON de un fichero: None si no existe y {} si no se puede leer o no es un objeto."""
    if not fichero.is_file():
        return None
    try:
        d = json.loads(fichero.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return d if isinstance(d, dict) else {}


def claves(texto):
    """Las líneas clave=valor de un BUILD-INFO.txt o de la cabecera de un manifiesto."""
    return dict(l.split("=", 1) for l in texto.splitlines() if "=" in l and not l.startswith("#"))


def es_build(info):
    """Un BUILD-INFO vale si dice mcp_src_sha y un build_timestamp con su forma (AAAAMMDD-HHMMSS)."""
    return bool(str(info.get("mcp_src_sha", "")).strip()) and bool(RX_BUILD.fullmatch(info.get("build_timestamp", "")))


def identidad(info):
    """Lo que distingue un bundle de otro: su fecha de build y su mcp_src_sha, las dos."""
    return f"{info['build_timestamp']} {info['mcp_src_sha']}"


def instalado_en(carpeta):
    """El BUILD-INFO de la instalación del Dev MCP que hay en una carpeta, o None si no lo es."""
    fichero = carpeta / "BUILD-INFO.txt"
    info = claves(fichero.read_text(encoding="utf-8", errors="replace")) if fichero.is_file() else {}
    return info if es_build(info) else None


def carpeta_servidor(dada):
    return dada or (casa() / GUIA).resolve()


def servidor(dada):
    """La carpeta del servidor del Dev MCP: la dada o la de la guía de Appian. Para si no hay una instalación entera."""
    d = carpeta_servidor(dada)
    if (d / A_MEDIAS).is_file():
        fin(2, f"error: la instalación de {d} se quedó a medias. Repite `actualizar.py instalar <bundle>` para terminarla.")
    if instalado_en(d) is None:
        fin(2, f"error: {d} no es una instalación del Dev MCP (falta BUILD-INFO.txt con mcp_src_sha y build_timestamp). "
               "Indica la carpeta donde extrajiste el bundle con --servidor.")
    return d


def carpeta_fotos(srv):
    """Una carpeta por instalación: dos servidores en el mismo equipo no mezclan sus fotos."""
    marca = hashlib.sha256(str(srv).encode("utf-8")).hexdigest()[:8]
    return casa() / ESTADO / "actualizaciones" / f"{srv.name}-{marca}"


def borra(ruta):
    """Un fichero o una carpeta entera, también con ficheros de solo lectura (en Windows, los que un bundle trae así)."""
    def con_permiso(funcion, que, _):
        os.chmod(que, 0o700)
        funcion(que)
    if ruta.is_dir() and not ruta.is_symlink():
        shutil.rmtree(ruta, **({"onexc": con_permiso} if sys.version_info >= (3, 12) else {"onerror": con_permiso}))
    elif ruta.exists() or ruta.is_symlink():
        try:
            ruta.unlink()
        except PermissionError:
            os.chmod(ruta, 0o700)
            ruta.unlink()


def nombre_de_raiz(n):
    """Si n vale como nombre de una entrada de la raíz del servidor en cualquier sistema: el de un fichero o carpeta,
    sin separadores, sin punto ni espacio final (Windows los quita: sería otro nombre) y sin ser un dispositivo."""
    return (isinstance(n, str) and n not in ("", ".", "..") and not re.search(r"[/\\:]", n) and n == n.rstrip(". ")
            and n.split(".")[0].upper() not in DISPOSITIVOS)


# ---- SAIL CLI y la foto -----------------------------------------------------------------------------------------

def sail_cli():
    orden = os.environ.get("SAIL_CLI")
    if orden:
        if not pathlib.Path(orden).is_file():
            return None
        return [sys.executable, orden] if orden.endswith(".py") else [orden]
    ruta = shutil.which("sail")
    return [ruta] if ruta else None


def sail(cli, *args):
    """Lo que contesta sail, o None si no arranca, no termina o sale con error: un error no es una ayuda."""
    try:
        r = subprocess.run([*cli, *args], capture_output=True, stdin=subprocess.DEVNULL, timeout=ESPERA)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if r.returncode != 0:
        return None
    return (r.stdout or r.stderr).decode("utf-8", "replace").replace("\r\n", "\n")


def ayuda_de_sail():
    """{orden: su ayuda}, con _version y _general; None sin SAIL CLI. Las órdenes se leen de su ayuda general, que
    las lista bajo «Available Commands:»; si un día no las lista así, quedan la general y la versión."""
    cli = sail_cli()
    general = cli and sail(cli, "--help")
    if not general:
        return None
    ayudas = {"_version": sail(cli, "--version") or "", "_general": general}
    dentro = False
    for linea in general.splitlines():
        if linea.strip() == "Available Commands:":
            dentro = True
        elif dentro and not linea.strip():
            break
        elif dentro and linea.split()[0] not in SIN_AYUDA:
            orden = linea.split()[0]
            ayuda = sail(cli, orden, "--help")
            # si su ayuda falla, la orden sigue en la foto: que falte no se lea después como que Appian la retiró
            ayudas[orden] = ayuda if ayuda is not None else SIN_SU_AYUDA.format(orden=orden)
    return ayudas


def es_catalogo(d):
    """El contrato del catálogo, el mismo al guardarlo en una foto y al leerlo: lo que usa la comparación."""
    return isinstance(d, dict) and all(
        isinstance(h, dict) and isinstance(h.get("parametros"), dict) and isinstance(h.get("obligatorios"), list)
        and all(isinstance(p, str) for p in [*h["parametros"], *h["obligatorios"]])
        and isinstance(h.get("descripcion"), str) and isinstance(h.get("esquema"), str) for h in d.values())


def resumen_del_catalogo(herramientas):
    """El catálogo de una foto a partir del que deja el extractor de ingeniería inversa: de cada herramienta, sus
    parámetros con su tipo, los obligatorios y una huella de su descripción y de su esquema entero. ValueError, con lo
    que no cuadra, si no tiene esa forma. La huella del esquema cambia con cualquier cambio suyo, también de orden o de
    texto; la de la descripción solo ve lo que guarda el extractor, sus 500 primeros caracteres."""
    huella = lambda texto: hashlib.sha256(texto.encode("utf-8", "replace")).hexdigest()[:12]

    def tipo(p):   # de un parámetro: su «type», los de su «anyOf», o None si su esquema no lo dice
        if not isinstance(p, dict):
            return None
        varios = p.get("anyOf") if isinstance(p.get("anyOf"), list) else []
        return p.get("type") or [x.get("type") for x in varios if isinstance(x, dict)] or None

    resumen = {}
    for h in herramientas:
        nombre = h.get("name") if isinstance(h, dict) else None
        esquema = h.get("inputSchema") if isinstance(h, dict) else None
        if not isinstance(nombre, str) or not nombre or not isinstance(esquema, dict):
            raise ValueError("una herramienta no tiene «name» o «inputSchema»")
        propiedades, obligatorios, descripcion = esquema.get("properties", {}), esquema.get("required", []), h.get("description")
        if nombre in resumen:
            raise ValueError(f"«{nombre}» viene dos veces")
        if not isinstance(propiedades, dict) or not isinstance(obligatorios, list) \
                or not all(isinstance(x, str) for x in obligatorios) or not isinstance(descripcion, (str, type(None))):
            raise ValueError(f"«{nombre}» no tiene «properties», «required» o «description» con su forma")
        resumen[nombre] = {"parametros": {n: tipo(p) for n, p in propiedades.items()}, "obligatorios": sorted(obligatorios),
                           "descripcion": huella(descripcion or ""), "esquema": huella(json.dumps(esquema, sort_keys=True))}
    return resumen


def leer_catalogo(fichero):
    """El catálogo de herramientas de un fichero, con el contrato de una foto. Admite el que deja el extractor de
    ingeniería inversa en `extraccion/mcp_catalog.json` ({"tools": [{"name", "description", "inputSchema"}]}), y lo
    resume."""
    try:
        d = json.loads(pathlib.Path(fichero).read_text(encoding="utf-8"))
        if isinstance(d, dict) and isinstance(d.get("tools"), list):
            d = resumen_del_catalogo(d["tools"])
    except (OSError, ValueError, RecursionError) as e:   # ValueError: no es JSON, no es UTF-8 o no tiene su forma
        fin(2, f"error: {fichero} no es un catálogo que se pueda leer: {str(e)[:300] or type(e).__name__}")
    if not es_catalogo(d):
        fin(2, f"error: {fichero} no es un catálogo: se espera el mcp_catalog.json que deja el extractor de ingeniería "
               "inversa o {herramienta: {\"parametros\": {…}, \"obligatorios\": […], \"descripcion\": huella, "
               "\"esquema\": huella}}")
    return d


def hacer_foto(srv, catalogo=None):
    """Rehace entera la foto del build instalado y devuelve su carpeta. BUILD-INFO.txt se borra lo primero y se
    escribe lo último: es lo que dice que la foto está, así que una que se corta a medias no cuenta como hecha."""
    # Primero se reúne todo; solo con todo en la mano se borra la foto que hubiera: si algo falla, la anterior sigue
    herramientas = leer_catalogo(catalogo) if catalogo else None
    foto = carpeta_fotos(srv) / instalado_en(srv)["build_timestamp"]
    manifiesto = srv / "skills" / "appian" / ".bundle-manifest"
    textos = {"BUILD-INFO.txt": (srv / "BUILD-INFO.txt").read_text(encoding="utf-8", errors="replace")}
    if manifiesto.is_file():
        textos["skill.bundle-manifest"] = manifiesto.read_text(encoding="utf-8", errors="replace")
    ayudas = ayuda_de_sail()
    if herramientas is not None:   # en ASCII: un nombre con un carácter que no se puede codificar no rompe la escritura
        textos["devmcp.json"] = json.dumps(herramientas, indent=1, sort_keys=True)
    foto.mkdir(parents=True, exist_ok=True)
    for suyo in DE_LA_FOTO:
        borra(foto / suyo)
    if ayudas is not None:
        (foto / "sail-help").mkdir()
        for orden, texto in ayudas.items():
            escribe(foto / "sail-help" / f"{orden}.txt", texto)
    for nombre in sorted(textos, key=lambda n: n == "BUILD-INFO.txt"):   # BUILD-INFO.txt, lo último
        escribe(foto / nombre, textos[nombre])
    return foto


def foto_de(srv, catalogo=None):
    """La foto del build instalado: la que haya de ese mismo bundle, o una nueva si falta o si se da un catálogo."""
    instalado = instalado_en(srv)
    foto = carpeta_fotos(srv) / instalado["build_timestamp"]
    hecha = instalado_en(foto) if foto.is_dir() else None
    return foto if hecha and identidad(hecha) == identidad(instalado) and not catalogo else hacer_foto(srv, catalogo)


def leer_foto(foto):
    """{build, skill, sail, devmcp}; None en la pieza que la foto no tiene."""
    foto = pathlib.Path(foto)
    lee = lambda f: f.read_text(encoding="utf-8", errors="replace")
    try:
        if not (foto / "BUILD-INFO.txt").is_file() or not es_build(claves(lee(foto / "BUILD-INFO.txt"))):
            fin(2, f"error: {foto} no es una foto (falta BUILD-INFO.txt con mcp_src_sha y build_timestamp)")
        skill = None
        if (foto / "skill.bundle-manifest").is_file():
            skill = {}
            for linea in lee(foto / "skill.bundle-manifest").splitlines():
                partes = linea.split(None, 1)
                if len(partes) == 2 and "=" not in partes[0]:
                    skill[partes[1].strip().lstrip("*")] = partes[0]
        ayudas = None
        if (foto / "sail-help").is_dir():
            ayudas = {f.stem: lee(f) for f in sorted((foto / "sail-help").glob("*.txt")) if f.is_file()}
        build = claves(lee(foto / "BUILD-INFO.txt"))
    except OSError as e:
        fin(2, f"error: no se puede leer la foto {foto}: {e}")
    devmcp = leer_catalogo(foto / "devmcp.json") if (foto / "devmcp.json").is_file() else None
    return {"carpeta": str(foto), "build": build, "skill": skill, "sail": ayudas, "devmcp": devmcp}


def foto_anterior(srv, build):
    """La foto guardada más reciente de un build anterior al dado, o None."""
    antes = [d for d in carpeta_fotos(srv).glob("*")
             if RX_BUILD.fullmatch(d.name) and (d / "BUILD-INFO.txt").is_file() and d.name < build]
    return max(antes, key=lambda d: d.name) if antes else None


# ---- El informe ---------------------------------------------------------------------------------------------------

def version_de_sail(ayudas):
    """«26.9.15» de «sail version 26.9.15 (…)»; lo que haya, si no tiene esa forma."""
    texto = (ayudas or {}).get("_version", "").strip()
    m = re.search(r"\d+(?:\.\d+)+", texto)
    return m.group(0) if m else texto


def opciones(ayuda):
    return set(re.findall(r"^\s+(?:-\w, )?(--[\w-]+)", ayuda, re.M))


def compara_devmcp(a, b):
    cambiadas, descripcion = {}, []
    for n in sorted(set(a) & set(b)):
        x, y = a[n], b[n]
        px, py, ox, oy = x["parametros"], y["parametros"], set(x["obligatorios"]), set(y["obligatorios"])
        if x["esquema"] != y["esquema"] or px != py or ox != oy:
            comunes = set(px) & set(py)
            cambiadas[n] = {"parametros_nuevos": sorted(set(py) - set(px)),
                            "parametros_quitados": sorted(set(px) - set(py)),
                            "cambian_de_tipo": sorted(p for p in comunes if px[p] != py[p]),
                            "pasan_a_obligatorio": sorted(p for p in (oy - ox) & comunes),
                            "pasan_a_opcional": sorted(p for p in (ox - oy) & comunes),
                            "nuevos_obligatorios": sorted((oy - ox) - comunes)}
        elif x["descripcion"] != y["descripcion"]:
            descripcion.append(n)
    return {"antes": len(a), "despues": len(b), "nuevas": sorted(set(b) - set(a)),
            "desaparecidas": sorted(set(a) - set(b)), "cambiadas": cambiadas, "solo_descripcion": descripcion}


def compara_skill(a, b):
    return {"antes": len(a), "despues": len(b), "nuevos": sorted(set(b) - set(a)),
            "retirados": sorted(set(a) - set(b)), "cambiados": sorted(f for f in set(a) & set(b) if a[f] != b[f])}


def compara_sail(a, b):
    ordenes = lambda x: {o for o in x if not o.startswith("_")}
    cambiadas = {}
    for o in sorted((set(a) & set(b)) - {"_version"}):
        if SIN_SU_AYUDA.format(orden=o) in (a[o].strip(), b[o].strip()):
            # en alguna de las dos fotos no se pudo leer su ayuda: de sus opciones no se sabe nada, y se dice
            cambiadas[o] = {"sin_ayuda": True, "opciones_nuevas": [], "opciones_quitadas": [], "lineas": []}
        elif a[o] != b[o]:
            lineas = [l for l in difflib.unified_diff(a[o].splitlines(), b[o].splitlines(), lineterm="", n=0)
                      if l[:1] in "+-" and l[:3] not in ("+++", "---")]
            cambiadas[o] = {"sin_ayuda": False, "opciones_nuevas": sorted(opciones(b[o]) - opciones(a[o])),
                            "opciones_quitadas": sorted(opciones(a[o]) - opciones(b[o])), "lineas": lineas}
    return {"antes": version_de_sail(a), "despues": version_de_sail(b), "nuevas": sorted(ordenes(b) - ordenes(a)),
            "retiradas": sorted(ordenes(a) - ordenes(b)), "cambiadas": cambiadas}


def citas(herramientas):
    """{herramienta: [ficheros de skills/ donde aparece su nombre]}. Es una búsqueda en el texto: dice dónde releer,
    no que se use. De SAIL CLI no se busca: sus órdenes son palabras corrientes, y quien lo usa es appian-qa."""
    out = {}
    for f in sorted(p for p in (PLUGIN / "skills").rglob("*") if herramientas and p.is_file() and p.suffix in CITAN):
        texto = f.read_text(encoding="utf-8", errors="replace")
        for n in herramientas:
            if re.search(rf"(?<![A-Za-z0-9_]){re.escape(n)}(?![A-Za-z0-9_])", texto):
                out.setdefault(n, []).append(f.relative_to(PLUGIN).as_posix())
    return out


def compara(a, b):
    """El informe, como datos: cada pieza, o None si falta en alguna de las dos fotos."""
    par = lambda k, f: f(a[k], b[k]) if a[k] is not None and b[k] is not None else None
    inf = {"antes": {"build": a["build"]["build_timestamp"], "carpeta": a["carpeta"]},
           "despues": {"build": b["build"]["build_timestamp"], "carpeta": b["carpeta"]},
           "devmcp": par("devmcp", compara_devmcp), "skill": par("skill", compara_skill),
           "sail": par("sail", compara_sail)}
    d = inf["devmcp"] or {}
    inf["citas"] = citas([*d.get("desaparecidas", []), *d.get("cambiadas", {})])
    inf["aviso"] = None
    if inf["despues"]["build"] < inf["antes"]["build"]:
        inf["aviso"] = ("la foto de «después» es de un build anterior a la de «antes»: lo que sale como nuevo es lo "
                        "que se quitó, y al revés")
    elif inf["despues"]["build"] == inf["antes"]["build"]:
        inf["aviso"] = "las dos fotos son del mismo build"
    return inf


def lista(nombres, vacio="ninguna"):
    return ", ".join(nombres) or vacio


def pinta(inf):
    out = [f"Foto: {inf['antes']['build']} · Instalado: {inf['despues']['build']}"]
    out += [f"OJO: {inf['aviso']}.", ""] if inf["aviso"] else [""]
    d = inf["devmcp"]
    if d is None:
        out.append("DEV MCP    sin foto del catálogo en alguna de las dos: no se compara")
    else:
        out += [f"DEV MCP    {d['antes']} -> {d['despues']} herramientas", f"  nuevas: {lista(d['nuevas'])}",
                f"  desaparecidas: {lista(d['desaparecidas'])}"]
        for n, c in d["cambiadas"].items():
            partes = [f"{texto} {lista(c[k])}" for k, texto in (
                ("parametros_nuevos", "parámetros nuevos:"), ("parametros_quitados", "quitados:"),
                ("cambian_de_tipo", "cambian de tipo:"), ("pasan_a_obligatorio", "pasan a obligatorios:"),
                ("pasan_a_opcional", "pasan a opcionales:"), ("nuevos_obligatorios", "de los nuevos, obligatorios:"))
                if c[k]]
            out.append(f"  cambia {n}: " + ("; ".join(partes) or "el esquema, con los mismos parámetros y obligatorios"))
        out.append(f"  cambia solo la descripción: {lista(d['solo_descripcion'])}")
    k = inf["skill"]
    if k is None:
        out += ["", "SKILL appian   sin foto del manifiesto en alguna de las dos: no se compara"]
    else:
        out += ["", f"SKILL appian   {k['antes']} -> {k['despues']} ficheros", f"  nuevos: {lista(k['nuevos'], 'ninguno')}",
                f"  retirados: {lista(k['retirados'], 'ninguno')}", f"  cambiados: {lista(k['cambiados'], 'ninguno')}"]
    s = inf["sail"]
    if s is None:
        out += ["", "SAIL CLI   sin foto de su ayuda en alguna de las dos: no se compara"]
    else:
        out += ["", f"SAIL CLI   {s['antes']} -> {s['despues']}",
                f"  órdenes nuevas: {lista(s['nuevas'])} | retiradas: {lista(s['retiradas'])}"]
        for o, c in s["cambiadas"].items():
            nombre = "ayuda general" if o == "_general" else o
            if c["sin_ayuda"]:
                out.append(f"  {nombre}: en alguna de las dos fotos no se pudo leer su ayuda; no se comparan sus opciones")
                continue
            out.append(f"  cambia {nombre}: opciones nuevas: {lista(c['opciones_nuevas'])}; quitadas: "
                       f"{lista(c['opciones_quitadas'])}; {len(c['lineas'])} líneas de ayuda distintas")
            out += [f"      {l}" for l in c["lineas"][:MAX_LINEAS]]
            if len(c["lineas"]) > MAX_LINEAS:
                out.append(f"      … y {len(c['lineas']) - MAX_LINEAS} más: "
                           f"{pathlib.Path(inf['despues']['carpeta'], 'sail-help', o + '.txt')}")
    if inf["citas"]:
        out += ["", "SU NOMBRE APARECE EN ESTOS FICHEROS DEL PLUGIN (para releer lo que dicen)"]
        out += [f"  {n}: {', '.join(fs)}" for n, fs in inf["citas"].items()]
    return "\n".join(out)


# ---- El bundle y su instalación ------------------------------------------------------------------------------------

def sistema():
    if platform.system() not in SISTEMAS:
        fin(2, f"error: el bundle de Appian no trae SAIL CLI ni instaladores para {platform.system()}")
    return SISTEMAS[platform.system()]


def miembros(tar):
    """Los miembros de un bundle si se pueden extraer sin riesgo y dan lo mismo en cualquier sistema: solo ficheros y
    carpetas, con una ruta relativa que no sale de donde se extrae, con nombres que valen en Windows y sin dos que
    allí serían el mismo (repetidos, o distintos solo en las mayúsculas). Si no, ValueError. No se fía de los filtros
    de tarfile, que no están en todos los Python que el plugin admite."""
    # la carpeta «.» es la propia raíz, como la mete `tar -C carpeta .`: no es una entrada
    todos = [m for m in tar.getmembers() if not (m.isdir() and not pathlib.PurePosixPath(m.name).parts)]
    formas, ficheros = {}, set()
    for m in todos:
        partes = pathlib.PurePosixPath(m.name).parts
        if not (m.isfile() or m.isdir()):
            raise ValueError(f"«{m.name}» no es un fichero ni una carpeta (un enlace o un dispositivo)")
        if (not partes or m.name.startswith("/") or "\\" in m.name or ":" in m.name
                or any(p == ".." or p != p.rstrip(". ") or p.split(".")[0].upper() in DISPOSITIVOS for p in partes)):
            raise ValueError(f"«{m.name}» no es una ruta dentro de la carpeta donde se extrae que valga en todos los sistemas")
        for k in range(1, len(partes) + 1):
            if formas.setdefault(tuple(p.casefold() for p in partes[:k]), partes[:k]) != partes[:k]:
                raise ValueError(f"«{m.name}» y otra entrada solo se distinguen en las mayúsculas")
        if m.isfile() and partes in ficheros:
            raise ValueError(f"«{m.name}» viene dos veces")
        ficheros.add(partes)
    return todos


def leer_hasta_el_final(fichero):
    """Lee un .tar.gz hasta el final. tarfile para en el último fichero y no mira lo que queda: un bundle cortado en
    sus últimos bytes o con la suma de comprobación cambiada pasaría por bueno."""
    with open(fichero, "rb") as f:
        comprimido = f.read(2) == b"\x1f\x8b"
    if comprimido:
        with gzip.open(fichero) as g:
            while g.read(1 << 20):
                pass


def leer_bundle(fichero, lanza_del_bundle=()):
    """(su BUILD-INFO, lo que trae en la raíz). Para si no es un bundle del Dev MCP que se pueda extraer sin riesgo o,
    para instalarlo, si no trae lo que se va a lanzar de él."""
    try:
        leer_hasta_el_final(fichero)
        with tarfile.open(fichero) as t:
            todos = miembros(t)
            rutas = {pathlib.PurePosixPath(m.name).as_posix(): m for m in todos if m.isfile()}
            build = claves(t.extractfile(rutas["BUILD-INFO.txt"]).read().decode("utf-8", "replace"))
    except KeyError:
        fin(2, f"error: {fichero} no es un bundle del Dev MCP (no trae BUILD-INFO.txt)")
    except NO_ES_TAR as e:
        fin(2, f"error: {fichero} no es un bundle del Dev MCP que se pueda extraer; si es una descarga, puede haberse "
               f"cortado: vuelve a descargarlo ({str(e)[:200] or type(e).__name__})")
    if not es_build(build):
        fin(2, f"error: {fichero} no es un bundle del Dev MCP (su BUILD-INFO.txt no dice mcp_src_sha y un "
               "build_timestamp con la forma AAAAMMDD-HHMMSS)")
    raiz = sorted({pathlib.PurePosixPath(m.name).parts[0] for m in todos})
    suyas = [n for n in raiz if n.casefold() in RESERVADAS]
    faltan = [f for f in lanza_del_bundle if f not in rutas]
    if suyas or faltan:
        fin(2, f"error: {fichero} no tiene la forma de bundle que conoce esta versión del plugin ("
               + "; ".join(x for x in (suyas and f"trae {', '.join(suyas)}", faltan and f"le falta {', '.join(faltan)}") if x)
               + "). Instálalo como dice la guía de Appian y avisa a quien mantiene el plugin.")
    return build, raiz


def guardar_anterior(srv, foto):
    """Lo instalado, menos el entorno de uv, como bundle.tar.gz en la carpeta de su foto. Lo relee entero antes de
    darlo por bueno. Los enlaces se guardan como enlaces."""
    destino, parcial = foto / "bundle.tar.gz", foto / "bundle.tar.gz.parcial"
    sin_cache = lambda m: None if "__pycache__" in pathlib.PurePosixPath(m.name).parts else m
    with tarfile.open(parcial, "w:gz") as t:
        for p in sorted(srv.iterdir()):
            if p.name not in RESERVADAS:
                t.add(p, arcname=p.name, filter=sin_cache)
    nombres = set()
    with tarfile.open(parcial) as t:
        for m in t:
            nombres.add(m.name)
            contenido = t.extractfile(m) if m.isfile() else None
            while contenido is not None and contenido.read(1 << 20):
                pass
    if "BUILD-INFO.txt" not in nombres:
        raise OSError(f"la copia de {srv} no se puede releer")
    os.replace(parcial, destino)
    return destino


def lanza(orden, cwd):
    """(código, salida) de un paso de la instalación; el código es None si no arranca o no termina a tiempo."""
    entorno = dict(os.environ)
    if platform.system() == "Windows":   # el find de Windows antes que otro del PATH: lo usan los .bat de Appian
        system32 = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32")
        entorno["PATH"] = system32 + os.pathsep + entorno.get("PATH", "")
    try:
        r = subprocess.run([str(x) for x in orden], cwd=cwd, env=entorno, stdin=subprocess.DEVNULL,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=ESPERA_INSTALAR)
    except subprocess.TimeoutExpired:
        return None, f"no terminó en {ESPERA_INSTALAR} segundos; puede seguir en marcha: espera antes de repetir"
    except OSError as e:
        return None, str(e)
    return r.returncode, r.stdout.decode("utf-8", "replace").replace("\r\n", "\n").strip()


def del_bundle(srv, script, *args):
    """Lanza un script de bin/ del bundle instalado: los .bat, tal cual; los .sh, con bash."""
    ruta = srv / "bin" / script
    return lanza([ruta, *args] if script.endswith(".bat") else ["bash", ruta, *args], cwd=srv)


def cmd_instalar(args):
    _, setup, skills = sistema()
    sin_tocar = "No se ha tocado la instalación."
    nuevo, raiz = leer_bundle(args.bundle, ("pyproject.toml", f"bin/{setup}", f"bin/{skills}"))
    srv = carpeta_servidor(args.servidor)
    marca = leer_json(srv / A_MEDIAS)         # si la hay, una instalación anterior no terminó de sustituir el servidor
    a_medias = marca is not None
    nueva = not srv.exists() or (srv.is_dir() and not any(srv.iterdir()))
    instalado = instalado_en(srv) if srv.is_dir() else None
    if not nueva and not srv.is_dir():
        fin(2, f"error: {srv} no es una carpeta")
    if not nueva and instalado is None and not a_medias:
        fin(2, f"error: {srv} tiene ficheros y no es una instalación del Dev MCP: no se instala encima. "
               "Indica con --servidor la carpeta del servidor, o una vacía para una instalación nueva.")
    suya = casa() / ESTADO
    suyas = {suya.resolve(), carpeta_fotos(srv).resolve()}   # resueltas: un enlace de carpeta puede llevarlas a otro sitio
    if srv in args.bundle.parents or any(srv == x or srv in x.parents or x in srv.parents for x in suyas):
        fin(2, f"error: el bundle no puede estar dentro de la carpeta del servidor ({srv}), que es la que se sustituye, "
               f"ni esa carpeta dentro de {suya} o al revés: las fotos y la copia acabarían dentro de lo que guardan. "
               f"{sin_tocar}")
    if args.plugin_sha is not None and args.plugin_sha.strip() != nuevo["mcp_src_sha"]:
        fin(2, f"error: el bundle es del build {nuevo['build_timestamp']} (mcp_src_sha {nuevo['mcp_src_sha']}) y el "
               f"plugin de tu entorno espera {args.plugin_sha}: descarga el bundle de ese entorno. {sin_tocar}")
    if a_medias and (marca.get("build") != identidad(nuevo) or not isinstance(marca.get("sobran"), list)):
        fin(2, f"error: la instalación de {srv} se quedó a medias con el build "
               f"{str(marca.get('build') or 'desconocido').split()[0]}, que no es el de este bundle: termínala con aquel. "
               f"Si ya no lo tienes, instala este como dice la guía de Appian y borra {srv / A_MEDIAS}.")
    if instalado and not a_medias and nuevo["build_timestamp"] < instalado["build_timestamp"]:
        fin(2, f"error: el bundle ({nuevo['build_timestamp']}) es más antiguo que lo instalado "
               f"({instalado['build_timestamp']}). {sin_tocar}")
    if instalado and not a_medias and nuevo["build_timestamp"] == instalado["build_timestamp"] \
            and nuevo["mcp_src_sha"] != instalado["mcp_src_sha"]:
        fin(2, f"error: el bundle tiene la misma fecha de build que lo instalado ({nuevo['build_timestamp']}) y otro "
               f"mcp_src_sha: no se sabe cuál es más nuevo. Instálalo como dice la guía de Appian. {sin_tocar}")
    mismo = bool(instalado) and identidad(instalado) == identidad(nuevo)
    uv = shutil.which(args.uv or "uv")
    if not uv:
        fin(2, "error: no encuentro `uv`, que instala las dependencias del servidor (la guía de Appian dice cómo "
               f"instalarlo). Si no está en el PATH, dime dónde con --uv. {sin_tocar}")
    # Se lanza desde la carpeta del servidor. Sin resolver enlaces: hay instalaciones de uv que son un enlace a otro
    # programa, que mira con qué nombre lo llaman.
    uv = desde_aqui(uv)
    if not setup.endswith(".bat") and not shutil.which("bash"):
        fin(2, f"error: no encuentro `bash`, que lanza los instaladores del bundle. {sin_tocar}")
    if args.catalogo:
        leer_catalogo(args.catalogo)
    # Lo que el bundle instalado trajo en la raíz y este ya no trae, sobra. Solo se sabe si lo instaló este script, que
    # lo apunta; al terminar una sustitución que se cortó, es lo que se apuntó en la marca.
    registro = carpeta_fotos(srv) / "instalado.json"
    previo = leer_json(registro) or {}
    antes = previo.get("raiz") if isinstance(previo.get("raiz"), list) else []
    # Solo en una actualización, que es cuando se guarda antes el bundle anterior: lo que se quita queda en esa copia
    sobran = marca["sobran"] if a_medias else (
        antes if instalado and not mismo and previo.get("build") == identidad(instalado) else [])
    # ...y salvo lo que no es un nombre de la raíz, lo reservado y lo que este bundle sí trae
    sobran = sorted({n for n in sobran if nombre_de_raiz(n) and n.casefold() not in RESERVADAS and n not in raiz})

    # Extraer aparte: si el bundle no se puede extraer entero, la instalación sigue como estaba
    aparte = srv / APARTE
    try:
        srv.mkdir(parents=True, exist_ok=True)
        borra(aparte)
        aparte.mkdir()
        with tarfile.open(args.bundle) as t:
            t.extractall(aparte, members=miembros(t), **({"filter": "data"} if hasattr(tarfile, "data_filter") else {}))
        foto = None
        # La foto y la copia, con el servidor entero. Si se está terminando una sustitución que se cortó, ya se
        # hicieron entonces: repetirlas guardaría como «anterior» un servidor a medio borrar.
        if instalado and not a_medias and not mismo:
            foto = foto_de(srv, args.catalogo)
            guardar_anterior(srv, foto)
    except NO_ES_TAR as e:
        try:
            borra(aparte)
            if nueva:
                srv.rmdir()
        except OSError:
            pass
        fin(2, f"error: no se pudo preparar la instalación: {e}. {sin_tocar}")

    try:
        if not a_medias:   # al terminar una que se cortó, la marca que hay es la buena: no se vuelve a escribir
            escribe(srv / A_MEDIAS, json.dumps({"build": identidad(nuevo), "sobran": sobran}))
        for nombre in raiz:
            borra(srv / nombre)
            os.replace(aparte / nombre, srv / nombre)
        for nombre in sobran:
            # Si solo cambia en las mayúsculas respecto a una entrada nueva, en Windows y en muchos macOS es el mismo
            # fichero, el recién instalado: ahí no sobra. Donde las mayúsculas distinguen, es otro y sí sobra.
            if not any(n.casefold() == nombre.casefold() and (srv / nombre).exists()
                       and os.path.samefile(srv / nombre, srv / n) for n in raiz):
                borra(srv / nombre)
        borra(aparte)
        registro.parent.mkdir(parents=True, exist_ok=True)
        escribe(registro, json.dumps({"build": identidad(nuevo), "raiz": raiz}))
        (srv / A_MEDIAS).unlink()
    except OSError as e:
        fin(1, f"error: no se pudo sustituir el servidor en {srv}: {e}\nCierra los clientes de IA que lo tengan en "
               "marcha y repite la misma orden: termina lo que quedó a medias.")
    sin_retirar = None
    try:   # con el servidor nuevo en su sitio, se guarda un bundle anterior: el del build más reciente
        for vieja in sorted(carpeta_fotos(srv).glob("*/bundle.tar.gz"))[:-1]:
            vieja.unlink()
    except OSError as e:
        sin_retirar = e

    print(f"Build {nuevo['build_timestamp']} (mcp_src_sha {nuevo['mcp_src_sha']}) en {srv}")
    if foto:
        print(f"  antes había el build {instalado['build_timestamp']}: su foto y su bundle, en {foto}")
    elif a_medias:
        print("  se ha terminado una instalación que se quedó a medias; la foto y el bundle anterior son los de entonces")
    elif mismo:
        print("  era el build instalado: se ha vuelto a dejar lo que trae el bundle, sin foto ni copia")
    elif nueva:
        print("  es una instalación nueva: queda lo que dice la guía de Appian y este script no hace, que es dar de alta "
              f"el servidor en tus clientes de IA y, si entras por navegador, tener el navegador que usa ({GUIA_WEB})")
    if sin_retirar:
        print(f"  el servidor está sustituido, pero no se pudo retirar la copia de un build más viejo ({sin_retirar}): "
              "bórrala a mano o repite la orden")
    pasos = [("uv sync", lambda: lanza([uv, "sync"], cwd=srv)), ("SAIL CLI", lambda: del_bundle(srv, setup)),
             ("skill appian", lambda: del_bundle(srv, skills))]
    pasos += [(f"skill appian en {d}", lambda d=d: del_bundle(srv, skills, "--skills-dir", d)) for d in args.skills_dir]
    # Ningún paso depende de otro, y se hacen todos: en un Mac con Intel o un Linux con ARM el instalador de SAIL CLI
    # se niega (el bundle no trae su binario) y la skill oficial tiene que quedar instalada igual.
    fallan = []
    for nombre, paso in pasos:
        codigo, salida = paso()
        # Sin ninguno de los clientes que Appian detecta, su instalador sale con error. Si la skill va a los que se
        # le dan con --skills-dir, eso no es un fallo: repetir la orden no lo cambiaría.
        if nombre == "skill appian" and args.skills_dir and codigo not in (0, None) and SIN_CLIENTES in salida:
            print(f"  {nombre}: Appian no detecta ninguno de sus clientes; va a los que das con --skills-dir")
            continue
        # Los instaladores de Appian avisan sin fallar: la skill instalada tiene cambios de la persona y no se pisa, la
        # carpeta de skills de un cliente es un enlace y se la salta, o sail queda instalado pero fuera del PATH (en
        # Linux y macOS, si no hay dónde enlazarlo). Se enseña lo que dicen.
        avisa = codigo == 0 and re.search(r"not overwriting|LOCAL EDITS|^\s*Skipped\b|^\s*\[!\]|not on your PATH",
                                          salida, re.M)
        print(f"  {nombre}: " + ("bien" if codigo == 0 and not avisa else
                                 "REVISAR, el instalador de Appian avisa de algo:" if codigo == 0 else "FALLA"))
        if codigo != 0 or avisa:
            print("\n".join(f"      {l}" for l in salida.splitlines()[-12:]))
        if codigo != 0:
            fallan.append(nombre)
    if fallan:
        fin(1, f"error: falló {lista([f'«{n}»' for n in fallan])}; los demás pasos se han hecho. Mira arriba lo que "
               "dice cada uno; cuando esté arreglado, repite la misma orden: se puede repetir.")
    print("Reinicia tus clientes de IA: hasta entonces siguen hablando con el servidor anterior. Después, "
          "`actualizar.py informe` dice qué cambió.")


def cmd_sail_anterior(args):
    srv = servidor(args.servidor)
    marca = sistema()[0]
    copias = sorted(carpeta_fotos(srv).glob("*/bundle.tar.gz"))
    if not copias:
        fin(2, "error: no hay bundle anterior guardado. Se guarda al instalar con `actualizar.py instalar`.")
    destino = copias[-1].parent / ("sail.exe" if marca == "windows" else "sail")
    try:
        with tarfile.open(copias[-1]) as t:
            suyo = next((m for m in t.getmembers() if m.isfile() and re.fullmatch(rf"bin/sail-{marca}[^/]*", m.name)),
                        None)
            if suyo is None:
                fin(2, f"error: el bundle del build {copias[-1].parent.name} no trae SAIL CLI para este sistema")
            binario = t.extractfile(suyo).read()
        borra(destino)
        destino.write_bytes(binario)
        os.chmod(destino, 0o755)
    except NO_ES_TAR as e:
        fin(2, f"error: no se pudo sacar SAIL CLI de {copias[-1]}: {str(e)[:200] or type(e).__name__}. Si el fichero "
               "está dañado, ya no sirve; si es que ese SAIL CLI está en uso, ciérralo y repite.")
    print(f"SAIL CLI del build {copias[-1].parent.name}: {destino}\nPara seguir con él, pon la variable de entorno "
          f"SAIL_CLI con esa ruta; quítala cuando el plugin se haya adaptado al nuevo.")


# ---- El banco de pruebas -------------------------------------------------------------------------------------------

def comprueba_extraccion(carpeta):
    """(resultado, lo que hay que decir) de mirar la extracción de la aplicación del banco que deja `devmcp_extract.py
    extract`: su informe (los objetos de cada tipo y los errores) y el modelo que el propio extractor construye con las
    respuestas (`build_model.py`), que tiene que decir lo que dice la especificación. «no se pudo» sin informe, con uno
    que no tiene su forma o con una extracción que no terminó: una sesión caducada no es un fallo del extractor."""
    fichero = carpeta / "extraccion" / "extraction_report.json"
    informe, esperado = leer_json(fichero), leer_json(ESPERADO) or {}
    entero = lambda n: isinstance(n, int) and not isinstance(n, bool) and n >= 0
    igual = lambda a, b: type(a) is type(b) and a == b     # el mismo valor y del mismo tipo: `true` no es 1
    minimos, hechos, previstos = esperado.get("objetos"), esperado.get("hechos"), esperado.get("errores_previstos")
    if not isinstance(minimos, dict) or not minimos or not all(entero(n) and n > 0 for n in minimos.values()) \
            or not isinstance(hechos, list) or not all(
                isinstance(h, dict) and all(isinstance(h.get(k), str) for k in ("tipo", "nombre_acaba_en", "campo"))
                and ("vale" in h) != ("acaba_en" in h) for h in hechos) \
            or not isinstance(previstos, list) or not all(
                isinstance(e, dict) and isinstance(e.get("herramienta"), str) and isinstance(e.get("empieza_por"), str)
                for e in previstos):
        return "no se pudo", [f"{ESPERADO} no dice con su forma lo que se espera del banco."]
    hay, errores, app = (informe or {}).get("objectsByType"), (informe or {}).get("errors"), (informe or {}).get("app")
    if not isinstance(hay, dict) or not all(entero(n) for n in hay.values()) or not isinstance(errores, list) \
            or not all(isinstance(e, dict) and isinstance(e.get("tool"), str) for e in errores) \
            or not isinstance(app, (dict, type(None))):
        return "no se pudo", [f"{fichero} no es el informe de una extracción. Se hace con `devmcp_extract.py extract "
                              "--app <la aplicación del banco> --out <carpeta>` y aquí se da esa carpeta."]
    if informe.get("status") != "complete" or informe.get("objectListComplete") is not True:
        return "no se pudo", [f"la extracción no terminó (estado «{informe.get('status')}»). Si fue por la sesión del Dev "
                              "MCP, entra de nuevo y repítela."]
    # Qué extracción es: se mira la que se da; no se sabe si es la del banco ni de qué versión del Dev MCP
    servidor_de = informe.get("server") if isinstance(informe.get("server"), dict) else {}
    dice = [f"de «{(app or {}).get('name', '?')}», del {informe.get('startedAt', '?')}, en {servidor_de.get('url', '?')}: "
            f"{sum(hay.values())} objetos y {len(errores)} errores"]
    mal = []
    faltan = [f"{tipo}: {hay.get(tipo, 0)} de {minimo}" for tipo, minimo in minimos.items() if hay.get(tipo, 0) < minimo]
    if faltan:
        mal.append("faltan objetos de los que tiene la aplicación del banco: " + "; ".join(faltan))
    # Los errores: los que Appian da en esta aplicación sin que sea un fallo, y los demás
    # por cómo empieza el mensaje entero: uno de sesión o de permisos que solo lo mencione no es el previsto
    previsto = lambda e: any(x["herramienta"] == e["tool"] and str(e.get("error")).startswith(x["empieza_por"])
                             for x in previstos)
    en_tipos = {}
    for e in errores:
        if not previsto(e):
            en_tipos.setdefault(e["tool"], set()).add(str(e.get("objectType") or "?"))
    if en_tipos:
        mal.append("errores que el banco no espera: " + ", ".join(
            f"{h} (en {', '.join(sorted(tipos))})" for h, tipos in sorted(en_tipos.items())) + ". Míralos en el informe.")
    en_varios = sorted(h for h, tipos in en_tipos.items() if len(tipos) >= TIPOS_DE_GENERICA)
    if en_varios:
        mal.append(f"de esas, {', '.join(en_varios)} fallan en {TIPOS_DE_GENERICA} tipos de objeto o más: si son de un tipo "
                   "que la política del extractor (devmcp_policy.json) no conoce, es que las prueba en todos.")
    # El modelo: lo arma el extractor con las respuestas; es donde se nota si ha dejado de entenderlas
    codigo, salida = lanza([sys.executable, MODELO, carpeta], cwd=carpeta) if MODELO.is_file() else (None, f"no está {MODELO}")
    modelo = leer_json(carpeta / "extraccion" / "inventory.json") or {}
    objetos = modelo.get("objects")
    if codigo != 0 or not isinstance(objetos, dict):
        mal.append("el extractor no pudo armar su modelo con las respuestas (build_model.py): "
                   + " / ".join(salida.splitlines()[-3:]))
    else:
        if modelo.get("parseErrors"):
            mal.append(f"el extractor no supo leer {modelo['parseErrors']} respuestas (parseErrors de inventory.json)")
        for h in hechos:
            suyos = [o for o in objetos.get(h["tipo"]) or [] if isinstance(o, dict)
                     and str(o.get("name", "")).endswith(h["nombre_acaba_en"])]
            quiere = h["vale"] if "vale" in h else h["acaba_en"]
            if len(suyos) != 1:
                mal.append(f"el modelo trae {len(suyos)} {h['tipo']} cuyo nombre acaba en «{h['nombre_acaba_en']}», no uno")
            elif not igual(suyos[0].get(h["campo"]), quiere) if "vale" in h                     else not str(suyos[0].get(h["campo"])).endswith(quiere):
                mal.append(f"{suyos[0].get('name')}: {h['campo']} es {suyos[0].get(h['campo'])!r} y la especificación dice "
                           f"{quiere!r}")
    if mal:
        return "no pasa", dice + mal
    quedan = sorted({e["tool"] for e in errores})
    return "pasa", dice + [f"están los objetos de cada tipo, el modelo dice los {len(hechos)} hechos de la especificación que "
                           f"se miran y no hay errores fuera de los previstos (quedan los de {', '.join(quedan) or 'ninguna herramienta'})."]


def comprueba_recorridos(host, site, cuentas):
    """(resultado, lo que hay que decir) de repetir con `qa.py`, de appian-qa, los guiones del banco. Monta en una
    carpeta temporal lo que `qa.py` necesita de un proyecto (el entorno, los escenarios, el fichero que sube el guion
    del formulario y los guiones, con el host, el
    site y la cuenta de cada rol de quien lo lanza) y la borra al terminar."""
    qa = PLUGIN / "skills" / "appian-qa" / "scripts" / "qa.py"
    guiones = [leer_json(f) or {} for f in sorted(GUIONES.glob("*.json"))]
    if not qa.is_file() or not guiones or not all(
            isinstance(g.get("escenario"), str) and isinstance(g.get("dice"), list) and isinstance(g.get("roles"), dict)
            for g in guiones):
        return "no se pudo", [f"no están `qa.py` de appian-qa o los guiones del banco ({GUIONES})"]
    sin_cuenta = sorted({rol for g in guiones for rol in g["roles"] if not cuentas.get(rol)})
    if sin_cuenta:
        return "no se pudo", ["falta la cuenta de " + ", ".join(f"{r} (--{r})" for r in sin_cuenta)]
    with tempfile.TemporaryDirectory(prefix="banco-") as tmp:
        tmp = pathlib.Path(tmp)
        for carpeta in ("analisis", f"construccion/{UNIDAD_BANCO}", f"qa/{UNIDAD_BANCO}"):
            (tmp / carpeta).mkdir(parents=True)
        escribe(tmp / "analisis" / "tecnico.md", "# Especificación técnica\n\n## 0. Entorno\n\n| Dato | Valor |\n|---|---|\n"
                                                 f"| URL de desarrollo | https://{host}/suite |\n")
        escribe(tmp / "construccion" / UNIDAD_BANCO / "ISS-01.feature",
                "# language: es\nCaracterística: Banco de pruebas\n" + "".join(
                    f"\n  Escenario: {g['escenario']}\n" + "".join(f"    {linea}\n" for linea in g["dice"]) for g in guiones))
        escribe(tmp / "adjunto.txt", "Fichero ficticio del banco de pruebas.\n")   # el que sube el guion del formulario
        for g in guiones:
            suyo = {**g, "host": host, "site": site, "roles": {rol: cuentas[rol] for rol in g["roles"]}}
            texto = json.dumps(suyo, ensure_ascii=False, indent=1)
            for rol, cuenta in suyo["roles"].items():   # «{cuenta de <rol>}»: su usuario, donde un paso lo teclea
                texto = texto.replace("{cuenta de %s}" % rol, json.dumps(cuenta, ensure_ascii=False)[1:-1])
            escribe(tmp / "qa" / UNIDAD_BANCO / f"{g['escenario']}.json", texto)
        codigo, salida = lanza([sys.executable, qa, "repetir", tmp, UNIDAD_BANCO], cwd=tmp)
    # De lo que dice qa.py, una línea por escenario: sin la ruta de la carpeta temporal, que ya no existe
    dice = [l.strip() for l in salida.splitlines() if l.strip() and str(tmp) not in l and tmp.as_posix() not in l]
    return {0: "pasa", 1: "no pasa"}.get(codigo, "no se pudo"), dice


def cmd_comprobar(args):
    """El banco de pruebas: la extracción de su aplicación y sus recorridos con SAIL CLI. 0 si pasa lo que se pidió
    comprobar, 1 si algo no pasa y 2 si algo no se pudo comprobar. Dice también lo que no se pidió."""
    if not args.extraccion and not args.host:
        fin(2, "error: di qué comprobar: --extraccion <carpeta> (la extracción de la aplicación del banco), "
               "--host <entorno> --solicitante <usuario> --aprobador <usuario> (sus recorridos con SAIL CLI), o las dos cosas.")
    partes = [("La extracción", comprueba_extraccion(args.extraccion) if args.extraccion else None,
               "no se dio --extraccion"),
              ("Los recorridos con SAIL CLI", comprueba_recorridos(args.host, args.site, {
                  "solicitante": args.solicitante, "aprobador": args.aprobador}) if args.host else None,
               "no se dio --host")]
    resultados = set()
    for nombre, hecho, por_que_no in partes:
        if hecho is None:
            print(f"{nombre}: sin comprobar ({por_que_no})")
            continue
        resultados.add(hecho[0])
        print(f"{nombre}: {hecho[0].upper()}")
        print("\n".join(f"  {linea}" for linea in hecho[1]))
    if "no pasa" in resultados:
        fin(1, "El banco no pasa.")
    if "no se pudo" in resultados:
        fin(2, "No se pudo comprobar todo lo pedido.")


# ---- Las demás órdenes --------------------------------------------------------------------------------------------

def qa_del_proyecto(proyecto, instalado):
    """En una línea, con qué SAIL CLI se obtuvieron los resultados del QA de un proyecto (qa/<U>/resultado.json, que
    escribe `qa.py`) y cuál hay instalado. No repite ni cambia nada: un resultado de otra versión no dice nada de esta,
    y repetirlo lo decide la persona."""
    de_version = lambda texto: (re.search(r"\bversion\s+(\S+)", texto or "") or [None, None])[1]
    cuenta, ilegibles = {}, []
    for f in sorted((proyecto / "qa").glob("*/resultado.json")):
        escenarios = (leer_json(f) or {}).get("escenarios")
        if not isinstance(escenarios, dict):      # cortado, o con otra forma: se dice cuál, no se da por «sin QA»
            ilegibles.append(f.parent.name)
            continue
        for e in escenarios.values():
            if isinstance(e, dict) and e.get("resultado") in ("pasa", "falla"):
                con = e.get("con") if isinstance(e.get("con"), dict) else {}
                cuenta[con.get("sail")] = cuenta.get(con.get("sail"), 0) + 1
    no_leidos = f" No se puede leer el resultado de {lista(ilegibles)}." if ilegibles else ""
    if not cuenta:
        return f"no hay escenarios recorridos en {proyecto / 'qa'}.{no_leidos}"
    ahora = de_version(instalado)
    partes = [f"{n} con SAIL CLI {v}" for v, n in sorted(cuenta.items(), key=lambda par: str(par[0])) if v]
    if cuenta.get(None):
        partes.append(f"{cuenta[None]} sin que conste con cuál")
    dice = f"{', '.join(partes)}; instalado, {ahora or 'no se sabe cuál'}.{no_leidos}"
    otros = sum(n for v, n in cuenta.items() if v and v != ahora)
    if not ahora:
        return dice
    if otros:      # solo los que se sabe que son de otra: de los que no consta no se dice nada
        return dice + (f" {otros} se recorrieron con otra versión: siguen valiendo para la suya; se repiten con "
                       "`qa.py repetir` si se decide")
    return dice + (" Todos, con el instalado" if not cuenta.get(None) else "")


def cmd_estado(args):
    srv = servidor(args.servidor)
    info = instalado_en(srv)
    print(f"Servidor Dev MCP   build {info['build_timestamp']} (mcp_src_sha {info['mcp_src_sha']}) en {srv}")
    cli = sail_cli()
    version = cli and sail(cli, "--version")
    de_donde = " (el de $SAIL_CLI, no el del PATH)" if version and os.environ.get("SAIL_CLI") else ""
    print(f"SAIL CLI           {version.strip() + de_donde if version else 'no está: ni en el PATH ni en $SAIL_CLI'}")
    manifiesto = srv / "skills" / "appian" / ".bundle-manifest"
    if manifiesto.is_file():
        texto = manifiesto.read_text(encoding="utf-8", errors="replace")
        print(f"Skill appian       versión {claves(texto).get('version', '?')[:12]} en el bundle instalado")
    fotos = sorted(d.name for d in carpeta_fotos(srv).glob("*") if (d / "BUILD-INFO.txt").is_file())
    print(f"Fotos guardadas    {lista(fotos)} en {carpeta_fotos(srv)}")
    if args.proyecto:
        print(f"QA del proyecto    {qa_del_proyecto(args.proyecto, version)}")
    if args.bundle:
        nuevo, _ = leer_bundle(args.bundle)
        if identidad(nuevo) == identidad(info):
            que = "es el instalado"
        elif nuevo["build_timestamp"] < info["build_timestamp"]:
            que = "es MÁS ANTIGUO que el instalado"
        elif nuevo["build_timestamp"] == info["build_timestamp"]:
            que = "tiene la misma fecha de build que el instalado y otro mcp_src_sha: `instalar` no lo instala"
        else:
            que = "es más nuevo que el instalado"
        print(f"Bundle             build {nuevo['build_timestamp']} (mcp_src_sha {nuevo['mcp_src_sha']}): {que}")


def cmd_foto(args):
    foto = hacer_foto(servidor(args.servidor), args.catalogo)
    f = leer_foto(foto)
    faltan = [n for n, k in (("SAIL CLI", "sail"), ("skill appian", "skill"), ("catálogo del Dev MCP", "devmcp"))
              if f[k] is None]
    print(f"Foto del build {foto.name} en {foto}" + (f" (sin {', '.join(faltan)})" if faltan else ""))


def cmd_informe(args):
    despues = leer_foto(args.despues or foto_de(servidor(args.servidor), args.catalogo))
    if args.antes:
        antes = leer_foto(args.antes)
    else:
        anterior = foto_anterior(servidor(args.servidor), despues["build"]["build_timestamp"])
        if anterior is None:
            fin(2, "error: no hay foto de un build anterior con la que comparar. La hace `actualizar.py instalar` antes "
                   "de sustituir el servidor; si la tienes en otra carpeta, dásela con --antes.")
        antes = leer_foto(anterior)
    inf = compara(antes, despues)
    print(json.dumps(inf, ensure_ascii=False, indent=1) if args.json else pinta(inf))


def main():
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="Instala un bundle del Dev MCP de Appian y dice qué hay y qué cambió.")
    sub = p.add_subparsers(dest="orden", required=True)
    comun = argparse.ArgumentParser(add_help=False)
    comun.add_argument("--servidor", type=ruta_dada,
                       help="carpeta donde está extraído el bundle (por defecto, ~/appian-dev-mcp-server)")
    e = sub.add_parser("estado", parents=[comun], help="qué hay instalado y qué fotos hay guardadas")
    e.add_argument("--bundle", type=ruta_dada, help="un bundle descargado, para saber si es más nuevo que lo instalado")
    e.add_argument("--proyecto", type=ruta_dada, metavar="DIR",
                   help="un proyecto con QA, para saber con qué SAIL CLI se obtuvieron sus resultados")
    f = sub.add_parser("foto", parents=[comun], help="rehace la foto de lo instalado")
    n = sub.add_parser("instalar", parents=[comun], help="instala un bundle, con foto y copia de lo anterior")
    n.add_argument("bundle", type=ruta_dada, help="el bundle descargado (appian-dev-mcp-server-bundle.tar.gz)")
    n.add_argument("--plugin-sha", help="el mcpSrcSha del plugin de tu entorno: si el bundle es de otro, no se instala")
    n.add_argument("--uv", type=os.path.expanduser, help="dónde está uv, si no está en el PATH")
    n.add_argument("--skills-dir", action="append", default=[], metavar="DIR", type=ruta_dada,
                   help="carpeta de un cliente de IA que el instalador de Appian no detecta; la skill queda en "
                        "DIR/skills/appian (se puede repetir)")
    i = sub.add_parser("informe", parents=[comun], help="qué cambió entre la foto anterior y lo instalado")
    for x in (f, n, i):
        x.add_argument("--catalogo", type=ruta_dada,
                       help="el catálogo de herramientas del Dev MCP, en JSON, para la foto de lo instalado")
    i.add_argument("--antes", type=ruta_dada, help="carpeta de la foto de antes (por defecto, la del build anterior)")
    i.add_argument("--despues", type=ruta_dada, help="carpeta de la foto de después (por defecto, la del build instalado)")
    i.add_argument("--json", action="store_true", help="el informe como datos")
    sub.add_parser("sail-anterior", parents=[comun], help="saca el SAIL CLI del bundle anterior guardado")
    c = sub.add_parser("comprobar", help="el banco de pruebas: su extracción y sus recorridos con SAIL CLI")
    c.add_argument("--extraccion", metavar="DIR", type=ruta_dada,
                   help="la carpeta de salida de `devmcp_extract.py extract` sobre la aplicación del banco")
    c.add_argument("--host", help="el entorno donde está construido el banco, para repetir sus recorridos (sin https://)")
    c.add_argument("--site", default="bps-banco-pruebas", help="el site del banco (por defecto, bps-banco-pruebas)")
    c.add_argument("--solicitante", metavar="USUARIO", help="la cuenta de prueba que pide, con sesión de sail abierta")
    c.add_argument("--aprobador", metavar="USUARIO", help="la cuenta de prueba que aprueba")
    args = p.parse_args()
    {"estado": cmd_estado, "foto": cmd_foto, "instalar": cmd_instalar, "informe": cmd_informe,
     "sail-anterior": cmd_sail_anterior, "comprobar": cmd_comprobar}[args.orden](args)


if __name__ == "__main__":
    main()
