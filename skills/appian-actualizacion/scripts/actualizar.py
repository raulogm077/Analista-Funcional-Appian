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
carpeta personal). `foto` se hace antes de instalar un bundle; `informe` fotografía lo instalado y lo compara con la
foto del build anterior (o las dos que se le den): herramientas nuevas, desaparecidas y con otro esquema, ficheros de
la skill oficial y órdenes y opciones de SAIL CLI, y qué ficheros de las skills del plugin citan las herramientas
que cambiaron o desaparecieron.

El informe dice qué cambió, no qué se rompió. Una pieza que falta en una foto (sin SAIL CLI, sin catálogo) sale como
«sin foto», no como «sin cambios».

`instalar` hace lo que manda la guía de Appian (https://docs.appian.com/suite/help/latest/devmcp.html) y, antes, lo que
Appian no hace: primero comprueba, sin tocar nada, que el bundle es un bundle, que no es más antiguo que lo instalado,
que es el del plugin del entorno (--plugin-sha, el mcpSrcSha que da el Dev MCP) y que hay `uv`; después hace la foto de
lo instalado y guarda el bundle anterior (lo instalado menos lo que crea `uv sync`) en la carpeta de esa foto, como
bundle.tar.gz; y solo entonces sustituye lo que trae el bundle, lanza `uv sync`, el `bin/setup-*` del sistema (SAIL
CLI) y `bin/install-skills` (la skill oficial: en los clientes que detecta Appian y en cada --skills-dir). Lo demás de
la carpeta del servidor no se toca. Se guarda un solo bundle anterior. Si un paso falla, lo dice y la misma orden se
puede repetir. `sail-anterior` saca de ese bundle el SAIL CLI de este sistema y dice cómo usarlo.

--servidor es la carpeta donde está extraído el bundle; sin él, la de la guía de Appian (~/appian-dev-mcp-server).
SAIL CLI es `sail` del PATH o el de $SAIL_CLI, como en appian-qa.

Códigos de salida: 0 bien | 1 instalar: un paso falló después de empezar (se puede repetir) | 2 falta algo o uso
incorrecto, sin haber tocado nada (sin instalación, sin foto anterior, un fichero ilegible, un bundle que no vale).
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
NO_SON_DEL_BUNDLE = {".venv", "uv.lock"}    # lo que crea `uv sync` en la carpeta del servidor: ni se guarda ni se toca
# Por sistema: cómo llama Appian a su SAIL CLI en bin/ y los scripts del bundle que lo instalan y que instalan la skill
SISTEMAS = {"Windows": ("windows", "setup-windows.bat", "install-skills.bat"),
            "Darwin": ("darwin", "setup-mac.sh", "install-skills.sh"),
            "Linux": ("linux", "setup-linux.sh", "install-skills.sh")}


def escribe(fichero, texto):
    """Con finales de línea de Unix en cualquier sistema (write_text no admite newline hasta Python 3.10)."""
    fichero.write_bytes(texto.replace("\r\n", "\n").encode("utf-8"))


def fin(codigo, texto):
    print(texto, file=sys.stderr if codigo else sys.stdout)
    sys.exit(codigo)


def casa():
    return pathlib.Path(os.environ.get("APPIAN_RE_HOME") or pathlib.Path.home())


def claves(texto):
    """Las líneas clave=valor de un BUILD-INFO.txt o de la cabecera de un manifiesto."""
    return dict(l.split("=", 1) for l in texto.splitlines() if "=" in l and not l.startswith("#"))


def servidor(dado):
    """La carpeta del servidor del Dev MCP: la dada o la de la guía de Appian. Para si no es una instalación."""
    d = pathlib.Path(dado).expanduser() if dado else casa() / GUIA
    info = d / "BUILD-INFO.txt"
    if not info.is_file() or "mcp_src_sha" not in claves(info.read_text(encoding="utf-8")):
        fin(2, f"error: {d} no es una instalación del Dev MCP (falta BUILD-INFO.txt con mcp_src_sha). "
               "Indica la carpeta donde extrajiste el bundle con --servidor.")
    return d.resolve()


def carpeta_fotos(srv):
    """Una carpeta por instalación: dos servidores en el mismo equipo no mezclan sus fotos."""
    marca = hashlib.sha256(str(srv).encode("utf-8")).hexdigest()[:8]
    return casa() / ESTADO / "actualizaciones" / f"{srv.name}-{marca}"


def sail_cli():
    orden = os.environ.get("SAIL_CLI")
    if orden:
        if not pathlib.Path(orden).is_file():
            return None
        return [sys.executable, orden] if orden.endswith(".py") else [orden]
    ruta = shutil.which("sail")
    return [ruta] if ruta else None


def sail(cli, *args):
    try:
        r = subprocess.run([*cli, *args], capture_output=True, stdin=subprocess.DEVNULL, timeout=ESPERA)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return (r.stdout or r.stderr).decode("utf-8", "replace").replace("\r\n", "\n")


def ayuda_de_sail():
    """{orden: su ayuda}, con _version y _general; None sin SAIL CLI. Las órdenes se leen de la ayuda general."""
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
            ayudas[linea.split()[0]] = sail(cli, linea.split()[0], "--help") or ""
    return ayudas


def hacer_foto(srv, catalogo=None):
    """Copia lo instalado a la carpeta de su build y la devuelve. Rehace la que hubiera de ese build."""
    info = (srv / "BUILD-INFO.txt").read_text(encoding="utf-8")
    foto = carpeta_fotos(srv) / claves(info)["build_timestamp"]
    if catalogo:
        try:
            herramientas = json.loads(pathlib.Path(catalogo).read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            fin(2, f"error: no se puede leer el catálogo {catalogo}: {e}")
        if not isinstance(herramientas, dict) or not all(isinstance(v, dict) for v in herramientas.values()):
            fin(2, f"error: {catalogo} no es un catálogo: se espera {{herramienta: {{parametros, obligatorios, …}}}}")
    foto.mkdir(parents=True, exist_ok=True)
    escribe(foto / "BUILD-INFO.txt", info)
    manifiesto = srv / "skills" / "appian" / ".bundle-manifest"
    if manifiesto.is_file():
        shutil.copyfile(manifiesto, foto / "skill.bundle-manifest")
    ayudas = ayuda_de_sail()
    if ayudas is not None:
        shutil.rmtree(foto / "sail-help", ignore_errors=True)
        (foto / "sail-help").mkdir()
        for orden, texto in ayudas.items():
            escribe(foto / "sail-help" / f"{orden}.txt", texto)
    if catalogo:
        escribe(foto / "devmcp.json", json.dumps(herramientas, ensure_ascii=False, indent=1, sort_keys=True))
    return foto


def leer_foto(foto):
    """{build, skill, sail, devmcp}; None en la pieza que la foto no tiene."""
    foto = pathlib.Path(foto)
    if not (foto / "BUILD-INFO.txt").is_file():
        fin(2, f"error: {foto} no es una foto (falta BUILD-INFO.txt)")
    lee = lambda f: f.read_text(encoding="utf-8", errors="replace")
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
    devmcp = None
    if (foto / "devmcp.json").is_file():
        try:
            devmcp = json.loads(lee(foto / "devmcp.json"))
        except ValueError as e:
            fin(2, f"error: {foto / 'devmcp.json'} no es JSON: {e}")
    return {"carpeta": str(foto), "build": claves(lee(foto / "BUILD-INFO.txt")), "skill": skill, "sail": ayudas,
            "devmcp": devmcp}


def foto_anterior(srv, build):
    """La foto guardada más reciente de un build anterior al dado, o None."""
    antes = [d for d in carpeta_fotos(srv).glob("*") if (d / "BUILD-INFO.txt").is_file() and d.name < build]
    return max(antes, key=lambda d: d.name) if antes else None


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
        px, py = x.get("parametros") or {}, y.get("parametros") or {}
        ox, oy = set(x.get("obligatorios") or []), set(y.get("obligatorios") or [])
        if x.get("esquema") != y.get("esquema") or px != py or ox != oy:
            comunes = set(px) & set(py)
            cambiadas[n] = {"parametros_nuevos": sorted(set(py) - set(px)),
                            "parametros_quitados": sorted(set(px) - set(py)),
                            "cambian_de_tipo": sorted(p for p in comunes if px[p] != py[p]),
                            "pasan_a_obligatorio": sorted(p for p in (oy - ox) & comunes),
                            "pasan_a_opcional": sorted(p for p in (ox - oy) & comunes),
                            "nuevos_obligatorios": sorted((oy - ox) - comunes)}
        elif x.get("descripcion") != y.get("descripcion"):
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
        if a[o] != b[o]:
            lineas = [l for l in difflib.unified_diff(a[o].splitlines(), b[o].splitlines(), lineterm="", n=0)
                      if l[:1] in "+-" and l[:3] not in ("+++", "---")]
            cambiadas[o] = {"opciones_nuevas": sorted(opciones(b[o]) - opciones(a[o])),
                            "opciones_quitadas": sorted(opciones(a[o]) - opciones(b[o])), "lineas": lineas}
    return {"antes": version_de_sail(a), "despues": version_de_sail(b), "nuevas": sorted(ordenes(b) - ordenes(a)),
            "retiradas": sorted(ordenes(a) - ordenes(b)), "cambiadas": cambiadas}


def citas(herramientas):
    """{herramienta: [ficheros de skills/ que la citan por su nombre]}. De SAIL CLI no se busca: sus órdenes son
    palabras corrientes, y quien lo usa es siempre appian-qa."""
    out = {}
    for f in sorted(p for p in (PLUGIN / "skills").rglob("*") if herramientas and p.is_file() and p.suffix in CITAN):
        texto = f.read_text(encoding="utf-8", errors="replace")
        for n in herramientas:
            if re.search(rf"\b{re.escape(n)}\b", texto):
                out.setdefault(n, []).append(f.relative_to(PLUGIN).as_posix())
    return out


def compara(a, b):
    """El informe, como datos: cada pieza, o None si falta en alguna de las dos fotos."""
    par = lambda k, f: f(a[k], b[k]) if a[k] is not None and b[k] is not None else None
    inf = {"antes": {"build": a["build"].get("build_timestamp"), "carpeta": a["carpeta"]},
           "despues": {"build": b["build"].get("build_timestamp"), "carpeta": b["carpeta"]},
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
            out.append(f"  cambia {n}: " + ("; ".join(partes) or "solo textos o valores admitidos"))
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
            out.append(f"  cambia {nombre}: opciones nuevas: {lista(c['opciones_nuevas'])}; quitadas: "
                       f"{lista(c['opciones_quitadas'])}; {len(c['lineas'])} líneas de ayuda distintas")
            out += [f"      {l}" for l in c["lineas"][:MAX_LINEAS]]
            if len(c["lineas"]) > MAX_LINEAS:
                out.append(f"      … y {len(c['lineas']) - MAX_LINEAS} más: "
                           f"{pathlib.Path(inf['despues']['carpeta'], 'sail-help', o + '.txt')}")
    if inf["citas"]:
        out += ["", "LO CITAN LAS SKILLS DEL PLUGIN (para releer lo que dicen)"]
        out += [f"  {n}: {', '.join(fs)}" for n, fs in inf["citas"].items()]
    return "\n".join(out)


def miembros(tar):
    """Los miembros de un bundle, tras comprobar que ninguno se sale de la carpeta donde se extrae."""
    todos = tar.getmembers()
    for m in todos:
        rutas = [m.name] + ([m.linkname] if m.issym() or m.islnk() else [])
        fuera = any(".." in pathlib.PurePosixPath(r).parts or r.startswith(("/", "\\")) or re.match(r"[A-Za-z]:", r)
                    for r in rutas)
        if fuera or not (m.isfile() or m.isdir() or m.issym() or m.islnk()):
            raise ValueError(f"«{m.name}» se sale de la carpeta donde se extrae o no es un fichero")
    return todos


def build_de_bundle(fichero):
    """(su BUILD-INFO, lo que trae en la raíz). Para si no es un bundle del Dev MCP."""
    try:
        with tarfile.open(fichero) as t:
            todos = miembros(t)
            info = next(m for m in todos if pathlib.PurePosixPath(m.name).as_posix() == "BUILD-INFO.txt")
            build = claves(t.extractfile(info).read().decode("utf-8"))
    except (OSError, StopIteration, tarfile.TarError, ValueError, AttributeError) as e:
        fin(2, f"error: {fichero} no es un bundle del Dev MCP ({e or 'no trae BUILD-INFO.txt'})")
    if "mcp_src_sha" not in build or "build_timestamp" not in build:
        fin(2, f"error: {fichero} no es un bundle del Dev MCP (su BUILD-INFO.txt no dice mcp_src_sha y build_timestamp)")
    return build, sorted({pathlib.PurePosixPath(m.name).parts[0] for m in todos if pathlib.PurePosixPath(m.name).parts})


def sistema():
    if platform.system() not in SISTEMAS:
        fin(2, f"error: el bundle de Appian no trae SAIL CLI ni instaladores para {platform.system()}")
    return SISTEMAS[platform.system()]


def borra(ruta):
    """Un fichero o una carpeta entera, también con ficheros de solo lectura (en Windows, los que el bundle trae así)."""
    def con_permiso(funcion, que, _):
        os.chmod(que, 0o700)
        funcion(que)
    if ruta.is_dir() and not ruta.is_symlink():
        shutil.rmtree(ruta, **({"onexc": con_permiso} if sys.version_info >= (3, 12) else {"onerror": con_permiso}))
    elif ruta.exists() or ruta.is_symlink():
        ruta.unlink()


def guardar_anterior(srv, foto):
    """Lo instalado, menos lo que crea `uv sync`, como bundle.tar.gz en la carpeta de su foto. Lo relee antes de darlo
    por bueno y borra el de builds más viejos: se guarda uno."""
    destino, parcial = foto / "bundle.tar.gz", foto / "bundle.tar.gz.parcial"
    sin_cache = lambda m: None if "__pycache__" in pathlib.PurePosixPath(m.name).parts else m
    with tarfile.open(parcial, "w:gz") as t:
        for p in sorted(srv.iterdir()):
            if p.name not in NO_SON_DEL_BUNDLE:
                t.add(p, arcname=p.name, filter=sin_cache)
    with tarfile.open(parcial) as t:
        if "BUILD-INFO.txt" not in t.getnames():
            raise OSError(f"la copia de {srv} no se puede releer")
    os.replace(parcial, destino)
    for vieja in carpeta_fotos(srv).glob("*/bundle.tar.gz"):
        if vieja != destino:
            vieja.unlink()
    return destino


def lanza(orden, cwd=None):
    """(código, salida) de un paso de la instalación; el código es None si no arranca o no termina."""
    entorno = dict(os.environ)
    if platform.system() == "Windows":   # el find de Windows antes que otro del PATH: lo usan los .bat de Appian
        system32 = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32")
        entorno["PATH"] = system32 + os.pathsep + entorno.get("PATH", "")
    try:
        r = subprocess.run([str(x) for x in orden], cwd=cwd, env=entorno, stdin=subprocess.DEVNULL,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=ESPERA_INSTALAR)
    except (OSError, subprocess.TimeoutExpired) as e:
        return None, str(e)
    return r.returncode, r.stdout.decode("utf-8", "replace").replace("\r\n", "\n").strip()


def del_bundle(srv, script, *args):
    """Lanza un script de bin/ del bundle instalado: los .bat, tal cual; los .sh, con bash."""
    ruta = srv / "bin" / script
    if not ruta.is_file():
        return None, f"el bundle no trae bin/{script}"
    return lanza([ruta, *args] if script.endswith(".bat") else ["bash", ruta, *args])


def cmd_instalar(args):
    _, setup, skills = sistema()
    nuevo, raiz = build_de_bundle(args.bundle)
    srv = pathlib.Path(args.servidor).expanduser() if args.servidor else casa() / GUIA
    instalado = None
    if srv.is_dir() and any(srv.iterdir()):
        info = srv / "BUILD-INFO.txt"
        instalado = claves(info.read_text(encoding="utf-8")) if info.is_file() else {}
        if "mcp_src_sha" not in instalado:
            fin(2, f"error: {srv} tiene ficheros y no es una instalación del Dev MCP: no se instala encima. "
                   "Indica con --servidor la carpeta del servidor, o una vacía para una instalación nueva.")
    elif srv.exists() and not srv.is_dir():
        fin(2, f"error: {srv} no es una carpeta")
    if args.plugin_sha and args.plugin_sha != nuevo["mcp_src_sha"]:
        fin(2, f"error: el bundle es del build {nuevo['build_timestamp']} (mcp_src_sha {nuevo['mcp_src_sha']}) y el "
               f"plugin de tu entorno espera {args.plugin_sha}: descarga el bundle de ese entorno. No se ha tocado nada.")
    if instalado and nuevo["build_timestamp"] < instalado.get("build_timestamp", ""):
        fin(2, f"error: el bundle ({nuevo['build_timestamp']}) es más antiguo que lo instalado "
               f"({instalado.get('build_timestamp')}). No se ha tocado nada.")
    uv = shutil.which(args.uv or "uv")
    if not uv:
        fin(2, "error: no encuentro `uv`, que instala las dependencias del servidor (la guía de Appian dice cómo "
               "instalarlo). Si no está en el PATH, dime dónde con --uv. No se ha tocado nada.")
    if args.catalogo and not pathlib.Path(args.catalogo).is_file():
        fin(2, f"error: no se puede leer el catálogo {args.catalogo}. No se ha tocado nada.")

    srv.mkdir(parents=True, exist_ok=True)
    srv = srv.resolve()
    foto = copia = None
    try:
        if instalado and instalado["mcp_src_sha"] != nuevo["mcp_src_sha"]:
            foto = hacer_foto(srv, args.catalogo)
            copia = guardar_anterior(srv, foto)
        for nombre in raiz:
            borra(srv / nombre)
        with tarfile.open(args.bundle) as t:
            t.extractall(srv, members=miembros(t), **({"filter": "data"} if hasattr(tarfile, "data_filter") else {}))
    except (OSError, tarfile.TarError) as e:
        fin(1, f"error: no se pudo sustituir el servidor en {srv}: {e}\nCierra los clientes de IA que lo tengan en "
               "marcha y repite la misma orden.")

    pasos = [("uv sync", *lanza([uv, "sync"], cwd=srv)), ("SAIL CLI", *del_bundle(srv, setup)),
             ("skill appian", *del_bundle(srv, skills))]
    pasos += [(f"skill appian en {d}", *del_bundle(srv, skills, "--skills-dir", d)) for d in args.skills_dir]
    print(f"Build {nuevo['build_timestamp']} (mcp_src_sha {nuevo['mcp_src_sha']}) en {srv}")
    if foto:
        print(f"  antes había el build {instalado.get('build_timestamp')}: su foto y su bundle, en {foto}")
    elif instalado:
        print("  era el build instalado: se ha repetido la instalación, sin foto ni copia")
    fallan = []
    for nombre, codigo, salida in pasos:
        editada = re.search(r"not overwriting|LOCAL EDITS", salida)
        print(f"  {nombre}: " + ("bien" if codigo == 0 and not editada else
                                 "REVISAR, la copia instalada tiene cambios tuyos y no se ha pisado" if codigo == 0 else "FALLA"))
        if codigo != 0 or editada:
            print("\n".join(f"      {l}" for l in salida.splitlines()[-12:]))
        if codigo != 0:
            fallan.append(nombre)
    if fallan:
        fin(1, f"error: falló {', '.join(fallan)}. Arréglalo y repite la misma orden: se puede repetir.")
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


def cmd_estado(args):
    srv = servidor(args.servidor)
    info = claves((srv / "BUILD-INFO.txt").read_text(encoding="utf-8"))
    print(f"Servidor Dev MCP   build {info.get('build_timestamp')} (mcp_src_sha {info.get('mcp_src_sha')}) en {srv}")
    cli = sail_cli()
    version = cli and sail(cli, "--version")
    print(f"SAIL CLI           {version.strip() if version else 'no está: ni en el PATH ni en $SAIL_CLI'}")
    manifiesto = srv / "skills" / "appian" / ".bundle-manifest"
    if manifiesto.is_file():
        texto = manifiesto.read_text(encoding="utf-8")
        print(f"Skill appian       versión {claves(texto).get('version', '?')[:12]} en el bundle instalado")
    fotos = sorted(d.name for d in carpeta_fotos(srv).glob("*") if (d / "BUILD-INFO.txt").is_file())
    print(f"Fotos guardadas    {lista(fotos)} en {carpeta_fotos(srv)}")
    if args.bundle:
        nuevo, _ = build_de_bundle(args.bundle)
        if nuevo.get("mcp_src_sha") == info.get("mcp_src_sha"):
            que = "es el instalado"
        elif nuevo.get("build_timestamp", "") < info.get("build_timestamp", ""):
            que = "es MÁS ANTIGUO que el instalado"
        else:
            que = "es más nuevo que el instalado"
        print(f"Bundle             build {nuevo.get('build_timestamp')} (mcp_src_sha {nuevo.get('mcp_src_sha')}): {que}")


def cmd_foto(args):
    foto = hacer_foto(servidor(args.servidor), args.catalogo)
    f = leer_foto(foto)
    faltan = [n for n, k in (("SAIL CLI", "sail"), ("skill appian", "skill"), ("catálogo del Dev MCP", "devmcp"))
              if f[k] is None]
    print(f"Foto del build {foto.name} en {foto}" + (f" (sin {', '.join(faltan)})" if faltan else ""))


def cmd_informe(args):
    if args.despues:
        despues = leer_foto(args.despues)
    else:
        despues = leer_foto(hacer_foto(servidor(args.servidor), args.catalogo))
    if args.antes:
        antes = leer_foto(args.antes)
    else:
        anterior = foto_anterior(servidor(args.servidor), despues["build"].get("build_timestamp", ""))
        if anterior is None:
            fin(2, "error: no hay foto de un build anterior con la que comparar. La foto se hace antes de instalar "
                   "(`actualizar.py foto`); si la tienes en otra carpeta, dásela con --antes.")
        antes = leer_foto(anterior)
    inf = compara(antes, despues)
    print(json.dumps(inf, ensure_ascii=False, indent=1) if args.json else pinta(inf))


def main():
    for flujo in (sys.stdout, sys.stderr):
        flujo.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="Instala un bundle del Dev MCP de Appian y dice qué hay y qué cambió.")
    sub = p.add_subparsers(dest="orden", required=True)
    comun = argparse.ArgumentParser(add_help=False)
    comun.add_argument("--servidor", help="carpeta donde está extraído el bundle (por defecto, ~/appian-dev-mcp-server)")
    e = sub.add_parser("estado", parents=[comun], help="qué hay instalado y qué fotos hay guardadas")
    e.add_argument("--bundle", help="un bundle descargado, para saber si es más nuevo que lo instalado")
    f = sub.add_parser("foto", parents=[comun], help="guarda la foto de lo instalado")
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
    i.add_argument("--despues", help="carpeta de la foto de después (por defecto, se hace ahora)")
    i.add_argument("--json", action="store_true", help="el informe como datos")
    sub.add_parser("sail-anterior", parents=[comun], help="saca el SAIL CLI del bundle anterior guardado")
    args = p.parse_args()
    {"estado": cmd_estado, "foto": cmd_foto, "instalar": cmd_instalar, "informe": cmd_informe,
     "sail-anterior": cmd_sail_anterior}[args.orden](args)


if __name__ == "__main__":
    main()
