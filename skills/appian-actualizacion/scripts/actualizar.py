#!/usr/bin/env python3
"""actualizar.py - Qué hay instalado del Dev MCP de Appian y qué cambió con una actualización.

  python3 actualizar.py estado  [--servidor DIR] [--bundle FICHERO]
  python3 actualizar.py foto    [--servidor DIR] [--catalogo FICHERO]
  python3 actualizar.py informe [--servidor DIR] [--catalogo FICHERO] [--antes DIR] [--despues DIR] [--json]

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

--servidor es la carpeta donde está extraído el bundle; sin él, la de la guía de Appian (~/appian-dev-mcp-server).
SAIL CLI es `sail` del PATH o el de $SAIL_CLI, como en appian-qa.

Códigos de salida: 0 bien | 2 falta algo o uso incorrecto (sin instalación, sin foto anterior, un fichero ilegible).
"""
import argparse
import difflib
import hashlib
import json
import os
import pathlib
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
MAX_LINEAS = 12                             # líneas de ayuda cambiadas que enseña el informe por orden


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


def build_de_bundle(fichero):
    try:
        with tarfile.open(fichero) as t:
            return claves(t.extractfile("BUILD-INFO.txt").read().decode("utf-8"))
    except (OSError, KeyError, tarfile.TarError, AttributeError) as e:
        fin(2, f"error: {fichero} no es un bundle del Dev MCP (no se puede leer su BUILD-INFO.txt): {e}")


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
        nuevo = build_de_bundle(args.bundle)
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
    p = argparse.ArgumentParser(description="Qué hay instalado del Dev MCP de Appian y qué cambió con una actualización.")
    sub = p.add_subparsers(dest="orden", required=True)
    comun = argparse.ArgumentParser(add_help=False)
    comun.add_argument("--servidor", help="carpeta donde está extraído el bundle (por defecto, ~/appian-dev-mcp-server)")
    e = sub.add_parser("estado", parents=[comun], help="qué hay instalado y qué fotos hay guardadas")
    e.add_argument("--bundle", help="un bundle descargado, para saber si es más nuevo que lo instalado")
    f = sub.add_parser("foto", parents=[comun], help="guarda la foto de lo instalado (antes de instalar otro bundle)")
    i = sub.add_parser("informe", parents=[comun], help="qué cambió entre la foto anterior y lo instalado")
    for x in (f, i):
        x.add_argument("--catalogo", help="el catálogo de herramientas del Dev MCP, en JSON, para la foto de lo instalado")
    i.add_argument("--antes", help="carpeta de la foto de antes (por defecto, la del build anterior)")
    i.add_argument("--despues", help="carpeta de la foto de después (por defecto, se hace ahora)")
    i.add_argument("--json", action="store_true", help="el informe como datos")
    args = p.parse_args()
    {"estado": cmd_estado, "foto": cmd_foto, "informe": cmd_informe}[args.orden](args)


if __name__ == "__main__":
    main()
