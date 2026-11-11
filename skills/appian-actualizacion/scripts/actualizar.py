#!/usr/bin/env python3
"""actualizar.py - Instala un bundle del Dev MCP de Appian y dice qué hay instalado y qué cambió.

  python3 actualizar.py estado   [--servidor DIR] [--bundle FICHERO]
  python3 actualizar.py foto     [--servidor DIR] [--catalogo FICHERO]
  python3 actualizar.py instalar BUNDLE [--servidor DIR] [--plugin-sha SHA] [--uv RUTA] [--skills-dir DIR]…
                                 [--catalogo FICHERO]
  python3 actualizar.py informe  [--servidor DIR] [--catalogo FICHERO] [--antes DIR] [--despues DIR] [--json]
  python3 actualizar.py sail-anterior [--servidor DIR]

Una foto es una copia, sin transformar, de lo que un bundle de Appian publica y el plugin usa:
  BUILD-INFO.txt          el build del servidor del Dev MCP
  skill.bundle-manifest   el manifiesto de la skill oficial `appian` (una huella por fichero)
  sail-help/<orden>.txt   la ayuda de cada orden de SAIL CLI (_general.txt y _version.txt, las de `sail`)
  devmcp.json             el catálogo de herramientas del Dev MCP, si se da con --catalogo:
                          {herramienta: {"parametros": {nombre: tipo}, "obligatorios": [...],
                                         "descripcion": huella, "esquema": huella}}
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
     lo instaló este script, que lo apunta); lo demás de la carpeta del servidor no se toca. Mientras dura, deja una
     marca: si se corta, las demás órdenes lo dicen y `instalar`, con ese mismo bundle, la termina sin repetir la
     foto ni la copia.
  5. Lanza `uv sync`, el `bin/setup-*` del sistema (SAIL CLI) y `bin/install-skills` (la skill oficial: en los
     clientes que detecta Appian y en cada --skills-dir), en ese orden; si uno falla, para ahí y lo dice.
La misma orden se puede repetir. Un bundle es el instalado si coinciden su fecha de build y su mcp_src_sha: repetida
con él, vuelve a dejar lo que trae, sin foto ni copia, y un cambio hecho a mano en esas carpetas se pierde. Se guarda
un solo bundle anterior. `sail-anterior` saca de él el SAIL CLI de este sistema y dice cómo usarlo. El bundle se
descarga del propio entorno: --plugin-sha comprueba que es el que ese entorno espera, no quién lo hizo. No hay
bloqueo entre dos instalaciones: no lances dos a la vez sobre la misma carpeta.

--servidor es la carpeta donde está extraído el bundle; sin él, la de la guía de Appian (~/appian-dev-mcp-server).
SAIL CLI es `sail` del PATH o el de $SAIL_CLI, como en appian-qa.

Códigos de salida: 0 bien | 1 instalar: falló después de empezar a sustituir (se puede repetir) | 2 falta algo o uso
incorrecto, sin haber tocado la instalación (no la hay, no hay foto anterior, un fichero ilegible, un bundle que no
vale).
"""
import argparse
import difflib
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

sys.dont_write_bytecode = True

ESTADO = ".appian-analisis-funcional"       # la carpeta personal del plugin; el nombre, solo aquí
GUIA = "appian-dev-mcp-server"              # donde la guía de Appian manda extraer el bundle
PLUGIN = pathlib.Path(__file__).resolve().parents[3]
CITAN = (".md", ".py", ".json")             # los ficheros de las skills donde se busca lo que cambió
SIN_AYUDA = {"completion", "help"}          # órdenes de sail que no son suyas: las pone su biblioteca
ESPERA = 60                                 # segundos que se espera a cada orden de sail
ESPERA_INSTALAR = 900                       # y a cada paso de la instalación (uv sync puede descargar)
MAX_LINEAS = 12                             # líneas de ayuda cambiadas que enseña el informe por orden
RX_BUILD = re.compile(r"\d{8}-\d{6}")       # build_timestamp: nombra la carpeta de la foto y ordena los builds
DE_LA_FOTO = ("BUILD-INFO.txt", "skill.bundle-manifest", "sail-help", "devmcp.json")
A_MEDIAS = ".instalando"                    # marca en la carpeta del servidor mientras se sustituye su contenido
APARTE = ".nuevo"                           # donde se extrae el bundle antes de sustituir nada
# En la carpeta del servidor, lo que no es del bundle: el entorno que crea `uv sync` y lo que usa `instalar`. Un bundle
# no puede traerlo, con estas u otras mayúsculas; no entra en el bundle anterior que se guarda y no se borra.
RESERVADAS = {".venv", A_MEDIAS, APARTE}
# Nombres que Windows no admite como fichero: un bundle que los trajera no se podría extraer igual en todos los sistemas
DISPOSITIVOS = {"CON", "PRN", "AUX", "NUL", *(f"{d}{i}" for d in ("COM", "LPT") for i in "123456789¹²³")}
SIN_SU_AYUDA = "(sail {orden} --help falló al hacer la foto)"   # la orden está, pero no se pudo leer su ayuda
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
    print(texto, file=sys.stderr if codigo else sys.stdout)
    sys.exit(codigo)


def casa():
    return pathlib.Path(os.environ.get("APPIAN_RE_HOME") or pathlib.Path.home()).expanduser().resolve()


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
    return "mcp_src_sha" in info and bool(RX_BUILD.fullmatch(info.get("build_timestamp", "")))


def identidad(info):
    """Lo que distingue un bundle de otro: su fecha de build y su mcp_src_sha, las dos."""
    return f"{info['build_timestamp']} {info['mcp_src_sha']}"


def instalado_en(carpeta):
    """El BUILD-INFO de la instalación del Dev MCP que hay en una carpeta, o None si no lo es."""
    fichero = carpeta / "BUILD-INFO.txt"
    info = claves(fichero.read_text(encoding="utf-8", errors="replace")) if fichero.is_file() else {}
    return info if es_build(info) else None


def carpeta_servidor(dada):
    return (pathlib.Path(dada).expanduser() if dada else casa() / GUIA).resolve()


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
        ruta.unlink()


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


def leer_catalogo(fichero):
    try:
        d = json.loads(pathlib.Path(fichero).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        fin(2, f"error: no se puede leer el catálogo {fichero}: {e}")
    if not es_catalogo(d):
        fin(2, f"error: {fichero} no es un catálogo: se espera {{herramienta: {{\"parametros\": {{…}}, \"obligatorios\": "
               "[…], \"descripcion\": huella, \"esquema\": huella}}")
    return d


def hacer_foto(srv, catalogo=None):
    """Rehace entera la foto del build instalado y devuelve su carpeta. BUILD-INFO.txt se borra lo primero y se
    escribe lo último: es lo que dice que la foto está, así que una que se corta a medias no cuenta como hecha."""
    herramientas = leer_catalogo(catalogo) if catalogo else None
    foto = carpeta_fotos(srv) / instalado_en(srv)["build_timestamp"]
    foto.mkdir(parents=True, exist_ok=True)
    for suyo in DE_LA_FOTO:
        borra(foto / suyo)
    manifiesto = srv / "skills" / "appian" / ".bundle-manifest"
    if manifiesto.is_file():
        shutil.copyfile(manifiesto, foto / "skill.bundle-manifest")
    ayudas = ayuda_de_sail()
    if ayudas is not None:
        (foto / "sail-help").mkdir()
        for orden, texto in ayudas.items():
            escribe(foto / "sail-help" / f"{orden}.txt", texto)
    if herramientas is not None:
        escribe(foto / "devmcp.json", json.dumps(herramientas, ensure_ascii=False, indent=1, sort_keys=True))
    escribe(foto / "BUILD-INFO.txt", (srv / "BUILD-INFO.txt").read_text(encoding="utf-8", errors="replace"))
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
        ayudas = {f.stem: lee(f) for f in sorted((foto / "sail-help").glob("*.txt"))}
    devmcp = leer_catalogo(foto / "devmcp.json") if (foto / "devmcp.json").is_file() else None
    return {"carpeta": str(foto), "build": claves(lee(foto / "BUILD-INFO.txt")), "skill": skill, "sail": ayudas,
            "devmcp": devmcp}


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
            if a[o] != b[o]:   # en una de las dos fotos no se pudo leer su ayuda: de sus opciones no se sabe nada
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
    return inf


def lista(nombres, vacio="ninguna"):
    return ", ".join(nombres) or vacio


def pinta(inf):
    out = [f"Foto: {inf['antes']['build']} · Instalado: {inf['despues']['build']}", ""]
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
                out.append(f"  {nombre}: en una de las dos fotos no se pudo leer su ayuda; no se comparan sus opciones")
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
    todos, formas, ficheros = tar.getmembers(), {}, set()
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


def leer_bundle(fichero, lanza_del_bundle=()):
    """(su BUILD-INFO, lo que trae en la raíz). Para si no es un bundle del Dev MCP que se pueda extraer sin riesgo o,
    para instalarlo, si no trae lo que se va a lanzar de él."""
    try:
        with tarfile.open(fichero) as t:
            todos = miembros(t)
            rutas = {pathlib.PurePosixPath(m.name).as_posix(): m for m in todos if m.isfile()}
            build = claves(t.extractfile(rutas["BUILD-INFO.txt"]).read().decode("utf-8", "replace"))
    except KeyError:
        fin(2, f"error: {fichero} no es un bundle del Dev MCP (no trae BUILD-INFO.txt)")
    except (OSError, tarfile.TarError, ValueError) as e:
        fin(2, f"error: {fichero} no es un bundle del Dev MCP que se pueda extraer: {e}")
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
    bundle = pathlib.Path(args.bundle).expanduser().resolve()
    nuevo, raiz = leer_bundle(bundle, ("pyproject.toml", f"bin/{setup}", f"bin/{skills}"))
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
    if srv in bundle.parents or srv in (casa() / ESTADO).parents or srv == casa() / ESTADO:
        fin(2, f"error: ni el bundle ni la carpeta {casa() / ESTADO} pueden estar dentro de la del servidor ({srv}), que "
               f"es la que se sustituye. {sin_tocar}")
    if args.plugin_sha and args.plugin_sha != nuevo["mcp_src_sha"]:
        fin(2, f"error: el bundle es del build {nuevo['build_timestamp']} (mcp_src_sha {nuevo['mcp_src_sha']}) y el "
               f"plugin de tu entorno espera {args.plugin_sha}: descarga el bundle de ese entorno. {sin_tocar}")
    if a_medias and marca.get("build") != identidad(nuevo):
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
    if not setup.endswith(".bat") and not shutil.which("bash"):
        fin(2, f"error: no encuentro `bash`, que lanza los instaladores del bundle. {sin_tocar}")
    if args.catalogo:
        leer_catalogo(args.catalogo)
    # Lo que el bundle instalado trajo en la raíz y este ya no trae, sobra. Solo se sabe si lo instaló este script, que
    # lo apunta; al terminar una sustitución que se cortó, es lo que se apuntó en la marca.
    registro = carpeta_fotos(srv) / "instalado.json"
    previo = leer_json(registro) or {}
    sobran = marca.get("sobran") if a_medias else (
        sorted(set(previo.get("raiz") or []) - set(raiz)) if instalado and previo.get("build") == identidad(instalado) else [])
    # ...salvo lo reservado y lo que este bundle sí trae, aunque sea con otras mayúsculas: en Windows sería lo mismo
    de_este = {n.casefold() for n in raiz} | RESERVADAS
    sobran = [n for n in sobran or [] if isinstance(n, str) and n not in ("", ".", "..") and not re.search(r"[/\\:]", n)
              and n.casefold() not in de_este]

    # Extraer aparte: si el bundle no se puede extraer entero, la instalación sigue como estaba
    aparte = srv / APARTE
    try:
        srv.mkdir(parents=True, exist_ok=True)
        borra(aparte)
        aparte.mkdir()
        with tarfile.open(bundle) as t:
            t.extractall(aparte, members=miembros(t), **({"filter": "data"} if hasattr(tarfile, "data_filter") else {}))
        foto = None
        # La foto y la copia, con el servidor entero. Si se está terminando una sustitución que se cortó, ya se
        # hicieron entonces: repetirlas guardaría como «anterior» un servidor a medio borrar.
        if instalado and not a_medias and not mismo:
            foto = foto_de(srv, args.catalogo)
            guardar_anterior(srv, foto)
    except (OSError, tarfile.TarError, ValueError) as e:
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
            borra(srv / nombre)
        borra(aparte)
        registro.parent.mkdir(parents=True, exist_ok=True)
        escribe(registro, json.dumps({"build": identidad(nuevo), "raiz": raiz}))
        (srv / A_MEDIAS).unlink()
        # con el servidor nuevo en su sitio, se guarda un bundle anterior: el del build más reciente
        for vieja in sorted(carpeta_fotos(srv).glob("*/bundle.tar.gz"))[:-1]:
            vieja.unlink()
    except OSError as e:
        fin(1, f"error: no se pudo sustituir el servidor en {srv}: {e}\nCierra los clientes de IA que lo tengan en "
               "marcha y repite la misma orden: termina lo que quedó a medias.")

    print(f"Build {nuevo['build_timestamp']} (mcp_src_sha {nuevo['mcp_src_sha']}) en {srv}")
    if foto:
        print(f"  antes había el build {instalado['build_timestamp']}: su foto y su bundle, en {foto}")
    elif a_medias:
        print("  se ha terminado una instalación que se quedó a medias; la foto y el bundle anterior son los de entonces")
    elif mismo:
        print("  era el build instalado: se ha vuelto a dejar lo que trae el bundle, sin foto ni copia")
    pasos = [("uv sync", lambda: lanza([uv, "sync"], cwd=srv)), ("SAIL CLI", lambda: del_bundle(srv, setup)),
             ("skill appian", lambda: del_bundle(srv, skills))]
    pasos += [(f"skill appian en {d}", lambda d=d: del_bundle(srv, skills, "--skills-dir", d)) for d in args.skills_dir]
    for nombre, paso in pasos:
        codigo, salida = paso()
        editada = re.search(r"not overwriting|LOCAL EDITS", salida)
        print(f"  {nombre}: " + ("bien" if codigo == 0 and not editada else
                                 "REVISAR, la copia instalada tiene cambios tuyos y no se ha pisado" if codigo == 0 else "FALLA"))
        if codigo != 0 or editada:
            print("\n".join(f"      {l}" for l in salida.splitlines()[-12:]))
        if codigo != 0:
            fin(1, f"error: falló «{nombre}» y no se ha seguido con los pasos siguientes. Arréglalo y repite la misma "
                   "orden: se puede repetir.")
    print("Reinicia tus clientes de IA: hasta entonces siguen hablando con el servidor anterior. Después, "
          "`actualizar.py informe` dice qué cambió.")


def cmd_sail_anterior(args):
    srv = servidor(args.servidor)
    marca = sistema()[0]
    copias = sorted(carpeta_fotos(srv).glob("*/bundle.tar.gz"))
    if not copias:
        fin(2, "error: no hay bundle anterior guardado. Se guarda al instalar con `actualizar.py instalar`.")
    destino = copias[-1].parent / ("sail.exe" if marca == "windows" else "sail")
    with tarfile.open(copias[-1]) as t:
        suyo = next((m for m in t.getmembers() if m.isfile() and re.fullmatch(rf"bin/sail-{marca}[^/]*", m.name)), None)
        if suyo is None:
            fin(2, f"error: el bundle del build {copias[-1].parent.name} no trae SAIL CLI para este sistema")
        destino.write_bytes(t.extractfile(suyo).read())
    os.chmod(destino, 0o755)
    print(f"SAIL CLI del build {copias[-1].parent.name}: {destino}\nPara seguir con él, pon la variable de entorno "
          f"SAIL_CLI con esa ruta; quítala cuando el plugin se haya adaptado al nuevo.")


# ---- Las demás órdenes --------------------------------------------------------------------------------------------

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
    comun.add_argument("--servidor", help="carpeta donde está extraído el bundle (por defecto, ~/appian-dev-mcp-server)")
    e = sub.add_parser("estado", parents=[comun], help="qué hay instalado y qué fotos hay guardadas")
    e.add_argument("--bundle", help="un bundle descargado, para saber si es más nuevo que lo instalado")
    f = sub.add_parser("foto", parents=[comun], help="rehace la foto de lo instalado")
    n = sub.add_parser("instalar", parents=[comun], help="instala un bundle, con foto y copia de lo anterior")
    n.add_argument("bundle", help="el bundle descargado (appian-dev-mcp-server-bundle.tar.gz)")
    n.add_argument("--plugin-sha", help="el mcpSrcSha del plugin de tu entorno: si el bundle es de otro, no se instala")
    n.add_argument("--uv", help="dónde está uv, si no está en el PATH")
    n.add_argument("--skills-dir", action="append", default=[], metavar="DIR",
                   help="carpeta de un cliente de IA que el instalador de Appian no detecta (se puede repetir)")
    i = sub.add_parser("informe", parents=[comun], help="qué cambió entre la foto anterior y lo instalado")
    for x in (f, n, i):
        x.add_argument("--catalogo", help="el catálogo de herramientas del Dev MCP, en JSON, para la foto de lo instalado")
    i.add_argument("--antes", help="carpeta de la foto de antes (por defecto, la del build anterior)")
    i.add_argument("--despues", help="carpeta de la foto de después (por defecto, la del build instalado)")
    i.add_argument("--json", action="store_true", help="el informe como datos")
    sub.add_parser("sail-anterior", parents=[comun], help="saca el SAIL CLI del bundle anterior guardado")
    args = p.parse_args()
    {"estado": cmd_estado, "foto": cmd_foto, "instalar": cmd_instalar, "informe": cmd_informe,
     "sail-anterior": cmd_sail_anterior}[args.orden](args)


if __name__ == "__main__":
    main()
