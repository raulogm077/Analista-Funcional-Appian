#!/usr/bin/env python3
"""Dice qué falta en este equipo para usar el plugin: para qué sirve cada cosa, qué se pierde sin ella y cómo se
instala en Windows, macOS o Linux. No instala nada ni abre ningún programa: solo busca ejecutables y rutas.

    python3 requisitos.py                  # todo el plugin (en Windows, python)
    python3 requisitos.py --skill NOMBRE   # solo lo que usa esa skill
    python3 requisitos.py --json           # lo mismo, legible por máquina
    python3 requisitos.py --breve          # para el hook de inicio de sesión (hooks/hooks.json)
    python3 requisitos.py --tabla-readme   # la tabla de requisitos del README

La lista de requisitos está en requisitos.json, junto a este fichero.
Sale con 1 si falta algo imprescindible para lo pedido (Python 3.9 o superior) y con 2 si la skill no existe.
--breve sale siempre con 0, imprime solo lo que falta y, después, deja la marca
~/.cache/appian-analisis-funcional/avisado-<versión>: con ella no vuelve a decir nada a esa versión.
REQUISITOS_SIN=id,id da esos requisitos por ausentes, para las pruebas.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.dont_write_bytecode = True  # sin __pycache__ en el plugin: no se escribe fuera del proyecto

RAIZ = Path(__file__).resolve().parent
SKILLS = RAIZ / "skills"
sys.path.append(str(SKILLS / "appian-reverse-engineering" / "scripts"))
try:  # la configuración MCP y la carpeta personal se buscan como lo hace el extractor de ingeniería inversa
    import devmcp_extract as dx
except Exception:  # noqa: BLE001 - un Python demasiado antiguo para el extractor: se dice que falta Python
    dx = None

SIMULAR = "REQUISITOS_SIN"
# Nombre anterior de una skill del plugin → el de hoy: una copia suelta con ese nombre también es la skill dos veces.
ANTERIORES = {"appian-prototipos-aena": "appian-prototipos"}
NO_SE_DETECTA = {"skill-pdf"}  # se informa, sin comprobar


def carpeta_personal() -> Path:
    return dx.home_dir() if dx else Path(os.environ.get("APPIAN_RE_HOME") or Path.home())


def sistema() -> str:
    if sys.platform.startswith("win"):
        return "windows"
    return "macos" if sys.platform == "darwin" else "linux"


def cargar() -> list:
    return json.loads((RAIZ / "requisitos.json").read_text(encoding="utf-8"))


def skills_del_plugin() -> list:
    return sorted(p.parent.name for p in SKILLS.glob("*/SKILL.md"))


# ---------------------------------------------------------------- detección: (presente, ruta)

def _python():
    return sys.version_info >= (3, 9), sys.executable


def _modulo(nombre):
    def detectar():
        spec = importlib.util.find_spec(nombre)
        if spec is None:
            return False, None
        origen = Path(spec.origin) if spec.origin else None
        return True, str(origen.parent if origen and origen.name == "__init__.py" else origen)
    return detectar


def _ejecutable(*nombres, rutas=()):
    def detectar():
        for n in nombres:
            ruta = shutil.which(n)
            if ruta:
                return True, ruta
        for r in rutas:
            if r and Path(r).is_file():
                return True, str(r)
        return False, None
    return detectar


def _programas_windows(*partes):
    """La misma ruta dentro de las carpetas de programas de Windows (las que mira Playwright para Chrome y Edge)."""
    raices = [os.environ.get(v) for v in ("LOCALAPPDATA", "PROGRAMFILES", "PROGRAMFILES(X86)")]
    return [Path(r, *partes) for r in raices if r]


def _navegador():
    """El Chromium de Playwright (descargado con «playwright install chromium») o Chrome o Edge donde los busca
    Playwright. No se abre ninguno."""
    so = sistema()
    base = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
    if base == "0":
        spec = importlib.util.find_spec("playwright")
        cache = [Path(p, "driver", "package", ".local-browsers") for p in (spec.submodule_search_locations or [])] \
            if spec else []
    elif base:
        cache = [Path(base)]
    elif so == "windows":
        cache = [Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local", "ms-playwright")]
    elif so == "macos":
        cache = [Path.home() / "Library" / "Caches" / "ms-playwright"]
    else:
        cache = [Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache", "ms-playwright")]
    for c in cache:
        if c.is_dir():
            for d in sorted(c.iterdir()):
                if d.is_dir() and d.name.startswith(("chromium-", "chromium_headless_shell-")):
                    return True, str(d)
    if so == "windows":
        sistema_ = (_programas_windows("Google", "Chrome", "Application", "chrome.exe")
                    + _programas_windows("Microsoft", "Edge", "Application", "msedge.exe"))
    elif so == "macos":
        sistema_ = [Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
                    Path("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge")]
    else:
        sistema_ = [Path("/opt/google/chrome/chrome"), Path("/opt/microsoft/msedge/msedge")]
    for p in sistema_:
        if p.is_file():
            return True, str(p)
    return False, None


def _docx():
    """El paquete docx donde lo busca df_docx.js: la carpeta de trabajo (y las de encima, como Node) y la global de npm."""
    sitios = [d / "node_modules" for d in (Path.cwd(), *Path.cwd().parents)]
    npm = shutil.which("npm")
    if npm:
        try:
            r = subprocess.run([npm, "root", "-g"], capture_output=True, text=True, encoding="utf-8",
                               errors="replace", timeout=20)
            if r.returncode == 0 and r.stdout.strip():
                sitios.append(Path(r.stdout.strip()))
        except (OSError, subprocess.SubprocessError):
            pass
    for s in sitios:
        if (s / "docx" / "package.json").is_file():
            return True, str(s / "docx")
    return False, None


def _libreoffice():
    if sistema() == "windows":
        rutas = _programas_windows("LibreOffice", "program", "soffice.exe")
    else:
        rutas = [Path("/Applications/LibreOffice.app/Contents/MacOS/soffice")]
    return _ejecutable("soffice", "libreoffice", rutas=rutas)()


def _pdf():
    ok, ruta = _ejecutable("pdftotext")()
    if ok:
        return ok, ruta
    return _modulo("pypdf")()


_entradas = None


def _servidores():
    """Los servidores MCP configurados para esta carpeta, como los encuentra el extractor."""
    global _entradas
    if _entradas is None:
        _entradas = dx.server_entries(Path.cwd(), []) if dx else []
    return _entradas


def _hosts_devmcp():
    hosts = set()
    for _f, _n, e in _servidores():
        if dx.is_devmcp(e):
            url = dx.expand_vars(dict(e.get("env") or {}), dict(os.environ)).get("LCP_URL", "")
            if urlparse(url).hostname:
                hosts.add(urlparse(url).hostname.lower())
    return hosts


def _devmcp():
    for f, n, e in _servidores():
        if dx.is_devmcp(e):
            return True, f"{n} ({f})"
    return False, None


def _appian_mcp_server():
    hosts = _hosts_devmcp()
    for f, n, e in _servidores():
        if dx.is_http(e) and any(dx.is_appian_mcp_server(e, h) for h in hosts):
            return True, f"{n} ({f})"
    return False, None


DETECTORES = {
    "python": _python,
    "playwright": _modulo("playwright"),
    "navegador": _navegador,
    "node": _ejecutable("node"),
    "docx": _docx,
    "libreoffice": _libreoffice,
    "pdf": _pdf,
    "uv": _ejecutable("uv"),
    "devmcp": _devmcp,
    "appian-mcp-server": _appian_mcp_server,
    "pytest": _modulo("pytest"),
    "mcp": _modulo("mcp"),
}


def copias_sueltas() -> list:
    """Una skill del plugin copiada suelta en ~/.claude/skills/ (también con su nombre anterior) existe dos veces."""
    carpeta = carpeta_personal() / ".claude" / "skills"
    avisos = []
    for n in skills_del_plugin() + sorted(ANTERIORES):
        copia = carpeta / n
        if (copia / "SKILL.md").is_file():
            nombre = f"{n} (hoy {ANTERIORES[n]})" if n in ANTERIORES else n
            avisos.append(f"Hay una copia suelta de {nombre} en {copia}: con el plugin, la skill está dos veces y no se "
                          "sabe cuál se activa. Bórrala para usar la del plugin.")
    return avisos


def comprobar(skill=None) -> dict:
    """Cada requisito de lo pedido, con «presente» (None si no se puede comprobar) y la ruta donde está."""
    sin = {s.strip() for s in os.environ.get(SIMULAR, "").split(",") if s.strip()}
    requisitos = []
    for r in cargar():
        if skill and skill not in r["skills"]:
            continue
        if r["id"] in sin:
            presente, ruta = False, None
        elif r["id"] in NO_SE_DETECTA:
            presente, ruta = None, None
        else:
            try:
                presente, ruta = DETECTORES[r["id"]]()
            except Exception:  # noqa: BLE001 - lo que no se puede mirar se da por ausente
                presente, ruta = False, None
        requisitos.append({**r, "presente": presente, "ruta": ruta})
    return {"python": ".".join(str(v) for v in sys.version_info[:3]), "requisitos": requisitos,
            "avisos": copias_sueltas()}


def falta_imprescindible(datos) -> bool:
    return any(r["imprescindible"] and r["presente"] is False for r in datos["requisitos"])


def version_plugin() -> str:
    try:
        return json.loads((RAIZ / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"]
    except (OSError, ValueError, KeyError):
        return "?"


# ---------------------------------------------------------------- salida

def quien(r) -> str:
    if not r["skills"]:
        return ""
    return " (todas las skills)" if set(r["skills"]) >= set(skills_del_plugin()) else f" ({', '.join(r['skills'])})"


def detalle(r, so) -> list:
    """Lo que hay que saber de un requisito que falta o no se puede comprobar."""
    return [f"  - {r['nombre']}{quien(r)}", f"    Para: {r['para']}", f"    Si falta: {r['sin_el']}",
            f"    Cómo se instala: {r['instalar'][so]}"]


def texto(datos, skill) -> str:
    so = sistema()
    de = f", skill {skill}" if skill else ""
    lineas = [f"Requisitos de appian-analisis-funcional {version_plugin()} en este equipo "
              f"({so}, Python {datos['python']}{de})"]
    de_las_skills = [r for r in datos["requisitos"] if not r["solo_pruebas"]]
    esta = [r for r in de_las_skills if r["presente"] is True]
    if esta:
        lineas += ["", "Está"] + [f"  - {r['nombre']}" + (f": {r['ruta']}" if r["ruta"] else "") for r in esta]
    for titulo, presente in (("Falta", False), ("No se puede comprobar desde aquí", None)):
        filas = [r for r in de_las_skills if r["presente"] is presente]
        if filas:
            lineas += ["", titulo] + [linea for r in filas for linea in detalle(r, so)]
    pruebas = [r for r in datos["requisitos"] if r["solo_pruebas"]]
    if pruebas:
        lineas += ["", "Solo para las pruebas del repositorio (pruebas/comprobar_plugin.py --completo)"]
        for r in pruebas:
            lineas += [f"  - {r['nombre']}: está"] if r["presente"] else detalle(r, so)
    if datos["avisos"]:
        lineas += ["", "Avisos"] + [f"  - {a}" for a in datos["avisos"]]
    lineas.append("")
    if falta_imprescindible(datos):
        lineas.append("Falta Python 3.9 o superior" + (f" (este es {datos['python']})" if sys.version_info < (3, 9) else "")
                      + ": no funciona nada.")
    elif any(r["presente"] is False for r in de_las_skills):
        lineas.append("Lo imprescindible está. Sin lo que falta, se sigue con lo que hay y se dice qué se pierde.")
    else:
        lineas.append("Está todo lo que se puede comprobar.")
    return "\n".join(lineas)


def tabla_readme() -> str:
    """La tabla de requisitos del README, que sale de requisitos.json para que no diverjan. En negrita, lo imprescindible;
    los comandos iguales en varios sistemas, una sola vez."""
    sistemas = (("windows", "Windows"), ("macos", "macOS"), ("linux", "Linux"))
    filas = ["| Requisito | Lo usa | Para qué | Si falta | Cómo se instala |", "|---|---|---|---|---|"]
    for r in cargar():
        if r["solo_pruebas"]:
            usa = "Las pruebas del repositorio"
        elif set(r["skills"]) >= set(skills_del_plugin()):
            usa = "Todas las skills"
        else:
            usa = ", ".join(f"`{s}`" for s in r["skills"])
        grupos = {}
        for clave, nombre in sistemas:
            grupos.setdefault(r["instalar"][clave], []).append(nombre)
        como = next(iter(grupos)) if len(grupos) == 1 else "<br>".join(
            f"{' y '.join(nombres)}: {orden}" for orden, nombres in grupos.items())
        nombre = f"**{r['nombre']}**" if r["imprescindible"] else r["nombre"]
        filas.append("| " + " | ".join(c.replace("|", "\\|") for c in (nombre, usa, r["para"], r["sin_el"], como)) + " |")
    return "\n".join(filas)


def marca() -> Path:
    """Que ya se avisó a esta versión del plugin en este equipo: lo único que el plugin escribe fuera de un proyecto."""
    return carpeta_personal() / ".cache" / "appian-analisis-funcional" / f"avisado-{version_plugin()}"


def breve(skill) -> int:
    """Para el hook de inicio de sesión: la primera vez de cada versión, solo lo que falta y las copias sueltas; después,
    nada. Sale siempre con 0, porque Claude solo recibe lo que imprime un hook que sale con 0."""
    try:
        hecho = marca()
        if hecho.exists():
            return 0
        datos = comprobar(skill)
        faltan = [r for r in datos["requisitos"] if r["presente"] is False and not r["solo_pruebas"]]
        if faltan or datos["avisos"]:
            so = sistema()
            print(f"Plugin appian-analisis-funcional {version_plugin()}: comprobación de este equipo, que solo se hace "
                  "una vez por versión. Díselo al usuario en tu primera respuesta, con cómo instalar lo que falta.")
            for r in faltan:
                print(f"- Falta {r['nombre']}{quien(r)}: {r['para']}. Si falta: {r['sin_el']}. "
                      f"Cómo se instala: {r['instalar'][so]}")
            for a in datos["avisos"]:
                print(f"- {a}")
            print(f"Detalle: {'python' if so == 'windows' else 'python3'} \"{RAIZ / 'requisitos.py'}\"")
            sys.stdout.flush()
        hecho.parent.mkdir(parents=True, exist_ok=True)
        hecho.write_text("Avisado de lo que falta en este equipo.\n", encoding="utf-8")
    except Exception:  # noqa: BLE001 - el aviso no puede impedir que empiece la sesión
        import traceback
        traceback.print_exc()
    return 0


def main(argv=None) -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--skill", help="solo lo que usa esta skill")
    ap.add_argument("--json", action="store_true", help="salida legible por máquina")
    ap.add_argument("--breve", action="store_true",
                    help="para el hook de inicio de sesión: solo lo que falta, una vez por versión; sale siempre con 0")
    ap.add_argument("--tabla-readme", action="store_true", help="la tabla de requisitos del README, en Markdown")
    args = ap.parse_args(argv)
    if args.tabla_readme:
        print(tabla_readme())
        return 0
    if args.breve:
        return breve(args.skill if args.skill in skills_del_plugin() else None)
    if args.skill and args.skill not in skills_del_plugin():
        print(f"No hay ninguna skill «{args.skill}» en el plugin. Son: {', '.join(skills_del_plugin())}",
              file=sys.stderr)
        return 2
    datos = comprobar(args.skill)
    print(json.dumps(datos, ensure_ascii=False, indent=2) if args.json else texto(datos, args.skill))
    return 1 if falta_imprescindible(datos) else 0


if __name__ == "__main__":
    sys.exit(main())
