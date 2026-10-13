#!/usr/bin/env python3
"""Crea el repositorio de un proyecto y dice en qué punto está.

  proyecto.py iniciar  <carpeta> --nombre "Solicitudes de autorización" [--cliente …] [--direccion …] [--tipo "evolutivo de X"]
                                     las carpetas y las plantillas, el repositorio git (rama main) con su .gitignore,
                                     AGENTS.md, CLAUDE.md («@AGENTS.md») y los flujos en .agents/workflows/
  proyecto.py iniciar  <carpeta>     en un proyecto que ya existe: pone al día AGENTS.md y los flujos con esta versión
                                     del plugin y añade lo que falte de lo anterior
  proyecto.py estado   <carpeta>     versión, cliente y marca, DF enviado, fuentes sin procesar, pendientes, pantallas;
                                     y avisa de lo que no está confirmado o subido, de lo que hay en el remoto sin traer
                                     y de si AGENTS.md o los flujos son de otra versión del plugin
  proyecto.py copia    <carpeta>     guarda analisis/*.md en versiones/v<versión>/ antes de cambiarlo
  proyecto.py version  <carpeta> --fuente FU-nn [FU-nn …] --que "…" [--informe impacto/URG-nn.md]
                       [--decision CAMBIA PAN-01 "lo nuevo" "lo de antes [FU-01 00:12:30]" …]
                                     antes de aplicar un informe que cambia el análisis: la copia, la versión +0.1 en
                                     funcional y técnico, su fila en decisiones.md, cada fuente en «Fuentes procesadas»
                                     y, con --decision (una por punto CAMBIA, ANULA, RESPONDE, VALIDA o ALCANCE, con
                                     la primera fuente), su fila D
  proyecto.py entregar <carpeta> [--cambio EV-02]   el Word sale hacia el cliente: «DF entregado» (el de un cambio, en su
                                     fila de Versiones de decisiones.md) y el fichero en «Entregados»
  proyecto.py cambio   <carpeta> <EV-nn|URG-nn> <estado> [opciones]   una unidad de cambio (analisis/cambios.md):
      abrir --titulo "…"                    Abierta
      aprobada --fuente FU-nn [--comparte "EV-03 en <objeto>: secuenciar (EV-02 primero)"]
                                            el jefe de proyecto la aprueba; otra vez si ha crecido (una fuente nueva
                                            para la unidad); sin --fuente, de Construida vuelve a Aprobada
      construida [--reaplicada URG-nn …] [--manual]   tras construir y verificar (construccion/verificacion/<ID>.json)
      produccion --ref "<referencia del pase>"        tras el pase (una URG, desde Abierta)
      descartada [--informe impacto/FU-nn.md]         desde Abierta, sin nada aplicado o con el informe que lo deshace
    Con --desatendida solo aprueba o pasa a producción con --fuente (el visto bueno del jefe de proyecto). Las
    condiciones, en references/cambios.md.

`iniciar` no toca nada que ya exista, salvo AGENTS.md y los flujos, que genera enteros. `entregar` solo cuando el Word se
envía, nunca en una sesión desatendida.
"""
import argparse
import datetime
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import unicodedata
sys.dont_write_bytecode = True  # sin __pycache__ en el plugin: no se escribe fuera del proyecto

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import modelo as mo
import unidades as un

SKILL = pathlib.Path(__file__).resolve().parents[1]
PLANTILLAS = SKILL / "assets" / "plantillas"
FLUJOS = SKILL / "assets" / "flujos"                             # los flujos del método, la única fuente
MANIFIESTO = SKILL.parents[1] / ".claude-plugin" / "plugin.json"  # una copia suelta de la skill no lo tiene
CARPETAS = ["fuentes", "notas", "impacto", "analisis/diagramas", "prototipo", "entregables", "versiones"]
# Lo que `iniciar` genera entero en el proyecto y pone al día con cada versión del plugin. Cada fichero lleva en su
# primera línea la versión que lo escribió (RX_GENERADO): `estado` avisa si es otra. Las notas del plan para quien
# mantiene el plugin («<!-- (T11) … -->», RX_TAREA) no van al proyecto.
GUIA, COPIA_FLUJOS = "AGENTS.md", ".agents/workflows"
RX_GENERADO = re.compile(r"<!-- appian-analisis-funcional (\S+) · ")
RX_TAREA = re.compile(r"[ \t]*<!-- \(T\d.*?-->")
RX_IMPORTA = re.compile(r"(?m)^\s*@(?:\./)?AGENTS\.md\b")           # el CLAUDE.md del proyecto importa AGENTS.md
ESPERA_REMOTO = 5   # segundos que `estado` espera al remoto; sin respuesta, compara con lo último que se trajo
# «DF entregado: 1.1 · 2026-10-10» (entregar) o, en proyectos anteriores, «DF entregado: 1.0 (2026-09-12)»
RX_ENTREGADO = re.compile(r"DF entregado:\s*v?(\d+\.\d+)(?:\s*(?:·\s*|\()(\d{4}-\d{2}-\d{2}))?")


def iniciar(a):
    raiz = pathlib.Path(a.carpeta)
    pm = raiz / "proyecto.md"
    titulo = re.match(r"# (.+)", pm.read_text(encoding="utf-8")) if pm.is_file() else None
    nombre = a.nombre or (titulo.group(1).strip() if titulo else None)
    if not nombre:
        sys.exit(f"{raiz} no es todavía un proyecto: dale nombre con --nombre \"…\"")
    for c in CARPETAS:
        (raiz / c).mkdir(parents=True, exist_ok=True)
    datos = {"proyecto": nombre, "cliente": a.cliente or "—", "direccion": a.direccion or "—",
             "tipo": a.tipo or "nuevo", "fecha": datetime.date.today().isoformat()}
    destinos = {"proyecto.md": pm, "funcional.md": raiz / "analisis" / "funcional.md",
                "tecnico.md": raiz / "analisis" / "tecnico.md", "decisiones.md": raiz / "analisis" / "decisiones.md"}
    for plantilla, destino in destinos.items():
        if destino.exists():
            print(f"= {destino} (ya existe, no se toca)")
            continue
        texto = (PLANTILLAS / plantilla).read_text(encoding="utf-8")
        for k, v in datos.items():
            texto = texto.replace("{" + k + "}", v)
        destino.write_text(texto, encoding="utf-8")
        print(f"+ {destino}")
    print(f"Carpetas: {', '.join(CARPETAS)}")
    # lo que solo se escribe si falta: qué no se sube y el CLAUDE.md que hace que Claude Code lea AGENTS.md
    for destino, texto in ((raiz / ".gitignore", (PLANTILLAS / "gitignore").read_text(encoding="utf-8")),
                           (raiz / "CLAUDE.md", f"@{GUIA}\n")):
        if not destino.exists():
            escribe(destino, texto)
            print(f"+ {destino}")
        elif destino.name == "CLAUDE.md" and not RX_IMPORTA.search(destino.read_text(encoding="utf-8", errors="replace")):
            print(f"= {destino} (ya existe, no se toca): no importa {GUIA}; añádele una línea «@{GUIA}»")
        else:
            print(f"= {destino} (ya existe, no se toca)")
    poner_al_dia(raiz)
    repositorio(raiz)


def escribe(ruta, texto):
    """Escribe un fichero generado, con finales de línea \\n en cualquier sistema para que sea el mismo en todos; False si
    ya decía eso y no lo toca."""
    if ruta.is_file() and ruta.read_text(encoding="utf-8", errors="replace") == texto:
        return False
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", encoding="utf-8", newline="\n") as f:
        f.write(texto)
    return True


def version_plugin():
    """La versión del plugin, o None en una copia suelta de la skill."""
    try:
        return json.loads(MANIFIESTO.read_text(encoding="utf-8"))["version"]
    except (OSError, ValueError, KeyError):
        return None


def orden_version(v):
    """«0.7.0-beta.4» → (0, 7, 0, "beta", 4), para saber cuál es posterior (la final, después de sus alfas y betas);
    None si no tiene esa forma."""
    m = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)(?:-([a-z]+)\.?(\d*))?", v or "")
    return m and (int(m.group(1)), int(m.group(2)), int(m.group(3)), m.group(4) or "~", int(m.group(5) or 0))


def version_generada(ruta):
    """La versión del plugin que generó un fichero, de su primera línea; None si no existe o no lo generó el plugin."""
    try:
        with open(ruta, encoding="utf-8", errors="replace") as f:
            m = RX_GENERADO.match(f.readline())
    except OSError:
        return None
    return m.group(1) if m else None


def generados(version):
    """{ruta en el proyecto: texto} de lo que se genera entero: AGENTS.md, de su plantilla y con la tabla de los flujos
    que hay en el plugin, y la copia de cada flujo."""
    marca = (f"<!-- appian-analisis-funcional {version or 'sin-version'} · Generado por proyecto.py iniciar: no se edita. "
             "Lo propio del proyecto va en proyecto.md -->\n")
    copias, filas = {}, []
    for f in sorted(FLUJOS.glob("F*.md"), key=lambda f: mo.numero(f.stem.split("-")[0])):
        texto = RX_TAREA.sub("", f.read_text(encoding="utf-8"))
        cuando = re.search(r"^\*\*Cuándo\.\*\* (.+)$", texto, re.M)
        filas.append(f"| [{texto.splitlines()[0].lstrip('# ')}]({COPIA_FLUJOS}/{f.name}) "
                     f"| {cuando.group(1).strip() if cuando else '—'} |")
        copias[f"{COPIA_FLUJOS}/{f.name}"] = marca + texto
    guia = RX_TAREA.sub("", (PLANTILLAS / "agentes.md").read_text(encoding="utf-8"))
    return {GUIA: marca + guia.replace("{flujos}", "\n".join(filas)), **copias}


def poner_al_dia(raiz):
    """AGENTS.md y los flujos, con la versión de este plugin. No pisa un fichero con ese nombre que no generó el plugin,
    ni lo que generó una versión posterior (otra persona del equipo tiene el plugin más nuevo, o esta copia de la skill
    no sabe su versión): los dos irían deshaciendo lo del otro."""
    version = version_plugin()
    nuevos = generados(version)
    en_proyecto = {r: version_generada(raiz / r) for r in nuevos}
    actual = orden_version(version)
    posterior = [v for v in set(en_proyecto.values())
                 if orden_version(v) and (actual is None or orden_version(v) > actual)]
    if posterior:
        print(f"= {raiz / GUIA} y los flujos son de la versión {max(posterior, key=orden_version)} del plugin, posterior "
              f"a la de este equipo ({version or 'sin versión'}): no se tocan; actualiza el plugin")
        return
    ajenos = [r for r in nuevos if (raiz / r).exists() and not en_proyecto[r]]
    cambiados = [r for r, texto in nuevos.items() if r not in ajenos and escribe(raiz / r, texto)]
    retirados = [f for f in sorted((raiz / COPIA_FLUJOS).glob("*.md"))   # un flujo que el plugin ya no tiene
                 if f"{COPIA_FLUJOS}/{f.name}" not in nuevos and version_generada(f)]
    for f in retirados:
        f.unlink()
    que = f"{raiz / GUIA} y {raiz / COPIA_FLUJOS} ({len(nuevos) - 1} flujos)"
    if not (cambiados or retirados):
        print(f"= {que}: ya están al día con la versión {version or 'sin versión'} del plugin")
    else:
        print(f"{'~' if any(en_proyecto.values()) else '+'} {que}, con la versión {version or 'sin versión'} del plugin")
    for r in ajenos:
        print(f"= {raiz / r} no lo generó el plugin y no se toca: para que se genere, quítalo o cámbiale el nombre")


def git(raiz, *args, espera=20, salida=True):
    """La salida de una orden de git lanzada en el proyecto; None si no hay git, falla o tarda más de `espera` segundos.
    Nunca pregunta: va sin terminal y, sin credenciales a mano, falla en vez de pedir una contraseña. Con `salida=False`
    no se lee lo que imprime, para que una orden que habla con el remoto no deje el script esperando a un proceso que
    git haya lanzado."""
    entorno = dict(os.environ, GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="never")
    sin_terminal = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {"start_new_session": True}
    try:
        r = subprocess.run(["git", *args], cwd=str(raiz), env=entorno, timeout=espera, stdin=subprocess.DEVNULL,
                           stdout=subprocess.PIPE if salida else subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           encoding="utf-8", errors="replace", **sin_terminal)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return (r.stdout or "") if r.returncode == 0 else None


def repositorio(raiz):
    """Deja el proyecto como repositorio git, en la rama main, si no lo es ya. No crea uno dentro de otro, no confirma
    nada y no toca un repositorio que ya existe."""
    if not shutil.which("git"):
        print("· Sin git en este equipo no se crea el repositorio: instálalo y repite «proyecto.py iniciar»")
        return
    dentro = git(raiz, "rev-parse", "--show-toplevel")
    if dentro is not None:
        print("= repositorio git (ya lo es)" if (raiz / ".git").exists() else
              f"= repositorio git: la carpeta ya está dentro de uno ({dentro.strip()}) y no se crea otro dentro")
        return
    if git(raiz, "init", "--quiet") is None or git(raiz, "symbolic-ref", "HEAD", "refs/heads/main") is None:
        print("· No se pudo crear el repositorio (git init): créalo a mano en la carpeta del proyecto")
        return
    print("+ repositorio git, en la rama main. Falta decirle dónde se sube: git remote add origin <URL>; después, "
          "git add -A, git commit y git push -u origin main")


def avisos_repositorio(raiz):
    """Lo que no está confirmado o subido y lo que hay en el remoto sin traer. Son avisos: sin git, sin repositorio o
    sin remoto no falla. Al remoto se le pregunta como mucho ESPERA_REMOTO segundos; sin red o sin acceso, se compara
    con lo último que se trajo y se dice."""
    if not shutil.which("git"):
        return ["sin git en este equipo no se sabe qué está subido"]
    con_remoto = bool((git(raiz, "remote") or "").strip())
    consultado = con_remoto and git(raiz, "fetch", "--quiet", "--all", espera=ESPERA_REMOTO, salida=False) is not None
    situacion = git(raiz, "--no-optional-locks", "status", "--porcelain=v2", "--branch", "--", ".")
    if situacion is None:
        return []
    lineas = situacion.splitlines()
    cab = dict(l[2:].split(" ", 1) for l in lineas if l.startswith("# ") and " " in l[2:])
    rama, cambios = cab.get("branch.head", "main"), sum(1 for l in lineas if l and not l.startswith("#"))
    plural = lambda n, palabra: f"{n} {palabra}{'' if n == 1 else 's'}"
    avisos = [f"{plural(cambios, 'cambio')} sin confirmar (git add y git commit)"] if cambios else []
    if not con_remoto:
        avisos.append(f"sin remoto, nada está subido (git remote add origin <URL> y git push -u origin {rama})")
    elif rama.startswith("("):
        pass   # sin rama activa (HEAD suelta): no hay con qué comparar
    elif "branch.ab" not in cab:
        avisos.append(f"la rama {rama} no está en el remoto, nada está subido (git push -u origin {rama})")
    else:
        delante, detras = (abs(int(x)) for x in cab["branch.ab"].split())
        if delante:
            avisos.append(f"{plural(delante, 'commit')} sin subir a {cab.get('branch.upstream')} (git push)")
        if detras:
            avisos.append(f"va {plural(detras, 'commit')} por detrás de {cab.get('branch.upstream')} (git pull)")
    if con_remoto and not consultado:
        avisos.append("no se pudo consultar el remoto (sin red o sin acceso): se compara con lo último que se trajo")
    return avisos


def avisos_proyecto(raiz):
    """Los avisos de `estado` sobre el repositorio del proyecto y lo que genera `iniciar`: lo que falta, lo que no está
    subido, AGENTS.md o los flujos de otra versión del plugin y un CLAUDE.md que no importa AGENTS.md."""
    version = version_plugin()
    flujos = [f"{COPIA_FLUJOS}/{f.name}" for f in FLUJOS.glob("F*.md")]
    es_repo = not shutil.which("git") or git(raiz, "rev-parse", "--is-inside-work-tree") is not None
    faltan = [] if es_repo else ["ser un repositorio git"]
    faltan += [r for r in (GUIA, "CLAUDE.md") if not (raiz / r).is_file()]
    faltan += [f"algún flujo de {COPIA_FLUJOS}/"] if any(not (raiz / r).is_file() for r in flujos) else []
    avisos = [f"Al proyecto le falta {', '.join(faltan)}: «proyecto.py iniciar <p>» lo añade sin tocar lo demás"
              ] if faltan else []
    avisos += [f"Repositorio: {x}" for x in (avisos_repositorio(raiz) if es_repo else [])]
    generado = {r: version_generada(raiz / r) for r in [GUIA, *flujos] if (raiz / r).is_file()}
    ajenos, otras = sorted(r for r, v in generado.items() if not v), sorted({v for v in generado.values() if v} - {version})
    if ajenos:
        avisos.append(f"{', '.join(ajenos)} no lo generó el plugin y «proyecto.py iniciar» no lo toca: para que lo genere, "
                      "quítalo o cámbiale el nombre")
    if otras and version:
        actual = orden_version(version)
        posterior = bool(actual) and any(orden_version(v) and orden_version(v) > actual for v in otras)
        avisos.append(f"{GUIA} y los flujos son de otra versión del plugin ({', '.join(otras)}; la de este equipo, {version}): "
                      + ("actualiza el plugin" if posterior else "«proyecto.py iniciar <p>» los pone al día"))
    claude = raiz / "CLAUDE.md"
    if claude.is_file() and not RX_IMPORTA.search(claude.read_text(encoding="utf-8", errors="replace")):
        avisos.append(f"CLAUDE.md no importa {GUIA}: añádele una línea «@{GUIA}»")
    return avisos


def tabla(texto, titulo):
    m = re.search(rf"^## {re.escape(titulo)}\s*$(.*?)(?=^## |\Z)", texto, re.M | re.S)
    if not m:
        return []
    filas = [mo.celdas(l) for l in m.group(1).split("\n") if l.startswith("|")]
    return [f for f in filas[2:] if any(f)]


def estado(a):
    raiz = pathlib.Path(a.carpeta)
    pm = raiz / "proyecto.md"
    texto = pm.read_text(encoding="utf-8") if pm.exists() else ""
    m = mo.Proyecto(raiz)
    print(f"# {texto.splitlines()[0][2:] if texto else raiz.name}")
    v = m.version("F")
    vs = f"{v[0]}.{v[1]}" if v else "—"
    print(f"Análisis: versión {vs}")
    cliente = re.search(r"Cliente:\s*([^·\n]+)", texto)
    marcas = sorted(f"prototipo/{b.name}" for b in (raiz / "prototipo").glob("brand-*.json"))
    print(f"Cliente: {cliente.group(1).strip() if cliente else '—'} · Marca: {', '.join(marcas) or 'sin marca'}")
    entregado = RX_ENTREGADO.search(texto)
    if entregado:   # el Word se genera al enviarlo o si se pide: aquí solo se informa
        fecha = f" ({entregado.group(2)})" if entregado.group(2) else ""
        print(f"DF en Word: último enviado {entregado.group(1)}{fecha}, versión actual {vs}")
    for x in avisos_proyecto(raiz):
        print(f"· {x}")

    # informes de impacto: los pendientes; las PAN de un cambio aprobado (✔) en una versión posterior al prototipo que se
    # enseñó (el último prototipo/app-vX.Y.json; sin ninguno, todas), que el prototipo rehace; y las fuentes que cuentan
    # como procesadas aunque no estén en la tabla: la de un informe «sin cambios» y la que cita una Decisión («✔ FU-09»)
    ensenadas = [tuple(map(int, x.groups())) for b in (raiz / "prototipo").glob("app-v*.json")
                 for x in [re.match(r"app-v(\d+)\.(\d+)\.json$", b.name)] if x]
    ultima = max(ensenadas) if ensenadas else None
    aprobadas, procesadas, pendientes = set(), {f[0] for f in tabla(texto, "Fuentes procesadas")}, []
    cerradas = {u.id for u in un.leer(raiz) or [] if u.estado in (un.PRODUCCION, un.DESCARTADA)}
    for nombre, t, puntos, _ in mo.informes(raiz):
        if nombre in cerradas:   # la ficha de una URG ya pasada a producción (o descartada) no queda pendiente
            continue
        # «Estado: pendiente» o «Estado: aplicado en 1.2; pendientes de aprobación: puntos 4 y 7» (actualizacion.md)
        e = mo.estado_informe(t)
        if re.search(r"pendientes? de aprobaci[oó]n:\s*puntos?\s+\d", e, re.I):
            pendientes.append(f"· {nombre}.md: {e}")
        elif re.match(r"pendiente", e, re.I):
            pendientes.append(f"· {nombre}.md: informe pendiente de aprobar o de aplicar")
        if re.match(r"sin cambios", e, re.I):
            procesadas |= set(re.findall(r"FU-\d+", nombre))
        procesadas |= {x for f in puntos for x in re.findall(r"FU-\d+", f.get("decision", ""))}
        aplicado = re.match(r"aplicado en v?(\d+)\.(\d+)", e, re.I)
        if aplicado and (ultima is None or tuple(map(int, aplicado.groups())) > ultima):
            aprobadas |= {x for f in puntos if "✔" in f.get("decision", "")
                          for col in ("encaja en", "cambio propuesto") for x in mo.ids_en(f.get(col, ""))
                          if x.startswith("PAN-")}
    catalogadas = sorted({re.match(r"(FU-\d+)", f.name).group(1) for f in (raiz / "fuentes").glob("FU-*.md")})
    sin = [x for x in catalogadas if x not in procesadas]
    print(f"Fuentes: {len(catalogadas)} catalogadas, {len(procesadas)} procesadas" +
          (f"; sin procesar: {', '.join(sin)}" if sin else ""))
    for x in pendientes:
        print(x)
    unidades(un.Contexto(m))

    if not m.docs:
        print("Sin análisis todavía.")
        return
    pc = sorted(p.id for p in m.vigentes("PC"))
    pt = sorted(p.id for p in m.vigentes("PT"))
    print(f"Pendiente de confirmar: {len(pc)}" + (f" ({', '.join(pc)})" if pc else ""))
    print(f"Pendientes técnicos: {len(pt)}" + (f" ({', '.join(pt)})" if pt else ""))
    pan = sorted(p.id for p in m.vigentes("PAN"))
    sin_cap = [p for p in pan if not re.search(r"!\[[^\]]*\]\([^)]+\)", m.texto(p))]
    print(f"Pantallas: {len(pan)}" + (f"; sin captura: {', '.join(sin_cap)}" if sin_cap else ""))
    conf = [p for p in pan if m.piezas[p].estado == "🔒"]
    if conf:
        print(f"Pantallas validadas por el cliente (🔒; no se cambian sin el visto bueno del analista): {', '.join(conf)}")
        cambian = [p for p in conf if p in aprobadas]
        if cambian:
            desde = f"después de app-v{ultima[0]}.{ultima[1]}.json" if ultima else "(sin app-vX.Y.json)"
            print(f"  con un cambio aprobado {desde}, el prototipo las rehace: {', '.join(cambian)}")
        quedan = [p for p in conf if p not in aprobadas]
        print(f"  para el prototipo: --confirmadas {','.join(quedan)}" if quedan else
              "  para el prototipo: ninguna va en --confirmadas")
    if "T" in m.docs:
        tv = m.version("T")
        empezado = bool(m.vigentes("DT")) or any("campo" in [mo.normaliza(c) for c in cab] for _, cab, _ in m.tablas("T", "3"))
        print("Técnico: " + (f"versión {tv[0]}.{tv[1]}" if tv else "sin versión") + ("" if empezado else ", sin empezar"))
    sig = re.search(r"^## Siguiente paso\s*\n+(.+)", texto, re.M)
    if sig:
        print(f"Siguiente paso: {sig.group(1).strip()}")


def unidades(ctx):
    """Las unidades en curso de analisis/cambios.md con sus fuentes, versiones y objetos, que no se guardan: se derivan."""
    if not ctx.hay:
        return
    curso = [u for u in ctx.unidades if u.estado in un.EN_CURSO]
    print(f"Unidades en curso (analisis/cambios.md; references/cambios.md): {len(curso) or 'ninguna'}")
    for u in curso:
        fu = sorted({x for n in ctx.informes_de(u.id) for x in re.findall(r"(?:FU|URG)-\d+", n)}, key=mo.numero)
        vs = ", ".join(f"{v[0]}.{v[1]}" for v in ctx.versiones_de(u.id))
        obj = ctx.cambian(u.id) if not u.urgente else ctx.objetos_urg(u.id)
        print(f"  {u.id} · {u.titulo} · {u.estado} · fuentes: {', '.join(fu) or '—'} · versión: {vs or '—'}"
              f" · objetos: {', '.join(obj) or '—'}")
        for g, objs in ctx.reaplicar(u.id):
            print(f"    reaplicar {g} en {', '.join(objs)} antes de marcarla Construida (--reaplicada {g})")
    for n in ctx.sin_unidad():
        print(f"· impacto/{n}.md no dice «Cambio:» y hay varias unidades Abiertas: ¿de cuál es?")


def _copia(raiz, m):
    v = m.version("F")
    if not v:
        sys.exit("funcional.md no tiene «Versión: x.y»")
    destino = raiz / "versiones" / f"v{v[0]}.{v[1]}"
    destino.mkdir(parents=True, exist_ok=True)
    for nombre in mo.DOCS.values():
        f = m.analisis / nombre
        if f.exists():
            shutil.copy2(f, destino / nombre)
    return v, destino


def copia(a):
    raiz = pathlib.Path(a.carpeta)
    v, destino = _copia(raiz, mo.Proyecto(raiz))
    print(f"Copia de la versión {v[0]}.{v[1]} en {destino}. Al terminar: comprobar.py {raiz} --anterior {destino}")


RX_VERSION = re.compile(r"(Versi[oó]n:\s*v?)(\d+)\.(\d+)")


def anade_fila(texto, titulo, fila):
    """Añade una fila al final de la tabla de la sección «## <titulo>» (tras su cabecera si está vacía)."""
    lineas = texto.split("\n")
    ini = next((i for i, l in enumerate(lineas) if l.strip() == f"## {titulo}"), None)
    if ini is None:
        return None
    fin = next((i for i in range(ini + 1, len(lineas)) if lineas[i].startswith("## ")), len(lineas))
    ultima = max((i for i in range(ini + 1, fin) if lineas[i].startswith("|")), default=None)
    if ultima is None:
        return None
    return "\n".join(lineas[:ultima + 1] + [fila] + lineas[ultima + 1:])


def que_es_fuente(e):
    """«Qué es» de una fuente catalogada: su tipo y, si lo hay, el asunto («…») o de quién es («de Jefe de proyecto»)."""
    tipo, detalle = str(e.get("tipo") or "Fuente"), str(e.get("detalle") or "")
    asunto = re.search(r"«[^»]+»", detalle) if detalle.lower().startswith("correo") else None
    if asunto:
        return f"{tipo} {asunto.group(0)}"
    if detalle.startswith("de "):
        return f"{tipo} {detalle.split(',')[0]}"
    return tipo


def citada(ruta):
    """La ruta tal cual o entre comillas si lleva espacios, para copiar la orden."""
    return f'"{ruta}"' if " " in str(ruta) else str(ruta)


def version(a):
    """Abre la versión siguiente para aplicar el informe de una o varias fuentes: copia la actual (como copia), sube
    0.1 la del funcional y la del técnico y escribe la fila de la versión en decisiones.md, las D de --decision y cada
    fuente en «Fuentes procesadas» de proyecto.md. No toca ninguna pieza: las edita quien aplica el informe. Lo que no
    puede escribir (falta la tabla) lo dice, para hacerlo a mano."""
    m = mo.Proyecto(pathlib.Path(a.carpeta))
    raiz = m.raiz
    fuentes = list(dict.fromkeys(f.strip().upper() for f in a.fuente))
    try:
        cat = {f["id"]: f for f in json.loads((raiz / "fuentes" / "indice.json").read_text(encoding="utf-8"))
               .get("fuentes", [])}
    except (OSError, ValueError):
        cat = {}
    fuera = [f for f in fuentes if f not in cat]
    if fuera:
        sys.exit(f"{', '.join(fuera)} no está en fuentes/: catalógala antes con leer_fuentes.py")
    proy, dec = raiz / "proyecto.md", m.ruta("D")
    texto_p = proy.read_text(encoding="utf-8") if proy.exists() else ""
    texto_d = dec.read_text(encoding="utf-8") if dec.exists() else ""
    ya = {f[0]: f[-1] for f in tabla(texto_p, "Fuentes procesadas") if f}
    for f in tabla(texto_d, "Versiones"):
        for x in re.findall(r"FU-\d+", f[3] if len(f) > 3 else ""):
            ya.setdefault(x, f[0])
    repetidas = [f"{f} (versión {ya[f]})" for f in fuentes if f in ya]
    if repetidas:
        sys.exit(f"{', '.join(repetidas)} ya tiene versión: si sigues aplicándola, edita esa versión sin abrir otra (una "
                 "fila D que falte, a mano con el formato de references/actualizacion.md §6)")
    decisiones = a.decision or []
    malas = [d[0] for d in decisiones if d[0].upper() not in mo.TIPOS_D]
    if malas:
        sys.exit(f"--decision {', '.join(malas)}: el tipo es uno de {', '.join(mo.TIPOS_D)}")
    v, destino = _copia(raiz, m)
    nueva = f"{v[0]}.{v[1] + 1}"
    subidos, escrito, a_mano = [], [], []
    for doc, nombre in (("F", "funcional"), ("T", "técnico")):
        if doc not in m.docs or not m.version(doc):
            continue   # técnico sin empezar
        ruta = m.ruta(doc)
        lineas = ruta.read_text(encoding="utf-8").split("\n")
        i = next(i for i, l in enumerate(lineas[:20]) if RX_VERSION.search(l))
        lineas[i] = RX_VERSION.sub(lambda x: f"{x.group(1)}{nueva}", lineas[i], count=1)
        ruta.write_text("\n".join(lineas), encoding="utf-8")
        subidos.append(nombre)
    hoy = datetime.date.today().isoformat()
    que = " ".join(a.que.split()).replace("|", "/")
    nuevo_d = anade_fila(texto_d, "Versiones", f"| {nueva} | {hoy} | {que} | {', '.join(fuentes)} | — |")
    if nuevo_d is None:
        a_mano.append(f"la fila de la versión {nueva} en «## Versiones» de decisiones.md")
    else:
        escrito.append("su fila en decisiones.md")
        texto_d = nuevo_d
    ids_d = []
    n = max([int(x) for f in tabla(texto_d, "Decisiones del cliente") for x in re.findall(r"^D-(\d+)", f[0])] or [0])
    fecha_fu = str(cat[fuentes[0]].get("fecha", ""))[:10] or hoy
    for tipo, afecta, nuevo_txt, antes in decisiones:
        celdas = [" ".join(x.split()).replace("|", "/") for x in (tipo.upper(), nuevo_txt, antes, afecta)]
        fila = (f"| D-{n + 1:02d} | {fecha_fu} | {fuentes[0]} | {celdas[0]} | {celdas[1]} | {celdas[2]} | {celdas[3]} "
                "| Sí |")
        nuevo_d = anade_fila(texto_d, "Decisiones del cliente", fila)
        if nuevo_d is None:
            a_mano.append(f"la D de {celdas[0]} {celdas[3]} en «## Decisiones del cliente» de decisiones.md")
            continue
        n += 1
        texto_d = nuevo_d
        ids_d.append(f"D-{n:02d}")
    if ids_d:
        escrito.append(f"{', '.join(ids_d)} en decisiones.md")
    if texto_d != (dec.read_text(encoding="utf-8") if dec.exists() else ""):
        dec.write_text(texto_d, encoding="utf-8")
    informe = (a.informe or f"impacto/{fuentes[0]}.md").replace("\\", "/")
    for fu in fuentes:
        e = cat[fu]
        fila = f"| {fu} | {str(e.get('fecha', ''))[:10]} | {que_es_fuente(e).replace('|', '/')} | {informe} | {nueva} |"
        nuevo_p = anade_fila(texto_p, "Fuentes procesadas", fila)
        if nuevo_p is None:
            a_mano.append(f"{fu} en «## Fuentes procesadas» de proyecto.md")
        else:
            texto_p = nuevo_p
    if texto_p and texto_p != (proy.read_text(encoding="utf-8") if proy.exists() else ""):
        proy.write_text(texto_p, encoding="utf-8")
        escrito.append(f"{', '.join(fuentes)} en «Fuentes procesadas» de proyecto.md")
    print(f"Versión {nueva}: {' y '.join(subidos)} en {nueva}" + (f"; {'; '.join(escrito)}" if escrito else "")
          + f". Copia de la {v[0]}.{v[1]} en {destino}.")
    for x in a_mano:
        print(f"· No hay dónde escribirla, añádela a mano: {x}")
    filas_d = "" if ids_d else " y, si hay CAMBIA, ANULA, RESPONDE, VALIDA o ALCANCE, sus filas D"
    print(f"Ahora: edita solo las piezas del informe (indice.py ficha --lineas){filas_d}; escribe {informe} con "
          f"«Estado: aplicado en {nueva}» y verifica:")
    print(f"  comprobar.py {citada(raiz)} --fuentes {citada(raiz / 'fuentes')} --anterior {citada(destino)} "
          f"--impacto {citada(raiz / informe)}")


def nombre_df(m, vs):
    """El nombre del Word que escribe df_docx.js por defecto: DF-<título sin tildes ni signos>-v<versión>.docx."""
    tit = re.search(r"^# (.+)$", "\n".join(m.docs["F"].lineas), re.M) if "F" in m.docs else None
    tit = re.sub(r"\s+—\s+Diseño funcional\s*$", "", tit.group(1)) if tit else "Diseño funcional"
    slug = re.sub(r"[^A-Za-z0-9_]+", "-", re.sub(r"[\u0300-\u036f]", "", unicodedata.normalize("NFD", tit))).strip("-")
    return f"DF-{slug}-v{vs}.docx"


def entregados(texto, word):
    """proyecto.md con el fichero en «Entregados: a.docx, b.docx» (tras «DF entregado» o tras la línea del cliente)."""
    lineas = texto.split("\n")
    k = next((i for i, l in enumerate(lineas) if l.startswith("Entregados:")), None)
    if k is None:
        k = next((i for i, l in enumerate(lineas) if "DF entregado:" in l),
                 next((i for i, l in enumerate(lineas) if l.startswith("Cliente:")), 0)) + 1
        lineas.insert(k, "Entregados:")
    ya = [x.strip() for x in lineas[k].split(":", 1)[1].split(",") if x.strip()]
    lineas[k] = "Entregados: " + ", ".join(ya + ([word] if word not in ya else []))
    return "\n".join(lineas)


def entregar(a):
    """El Word sale hacia el cliente: «DF entregado: <versión> · <fecha>» en proyecto.md (el de un cambio, en la fila de
    su versión en decisiones.md) y el fichero en «Entregados:», que df_docx.js no vuelve a escribir."""
    raiz = pathlib.Path(a.carpeta)
    pm = raiz / "proyecto.md"
    if not pm.exists():
        sys.exit(f"No existe {pm}")
    m = mo.Proyecto(raiz)
    v = m.version("F")
    if not v:
        sys.exit("funcional.md no tiene «Versión: x.y»")
    vs, fecha = f"{v[0]}.{v[1]}", datetime.date.today().isoformat()
    texto = pm.read_text(encoding="utf-8")
    if a.cambio:
        return entregar_cambio(a.cambio.upper(), raiz, m, vs, fecha, texto)
    valor = f"DF entregado: {vs} · {fecha}"
    if re.search(r"DF entregado:", texto):
        texto = re.sub(r"DF entregado:[^\n]*?(?=\s+·\s+Estado:|$)", valor, texto, count=1, flags=re.M)
    else:   # tras la línea del cliente o, si no está, tras el título
        lineas = texto.split("\n")
        k = next((i for i, l in enumerate(lineas) if l.startswith("Cliente:")), 0)
        lineas.insert(k + 1, valor)
        texto = "\n".join(lineas)
    word = nombre_df(m, vs)
    if not (raiz / "entregables" / word).is_file():
        print(f"· No encuentro entregables/{word}: genéralo con df_docx.js antes de enviarlo")
    else:
        texto = entregados(texto, word)
    pm.write_text(texto, encoding="utf-8")
    print(f"{valor} en {pm}")


def entregar_cambio(uid, raiz, m, vs, fecha, texto):
    """El DF de un cambio (df_docx.js --cambio): «DF del cambio <U> entregado <fecha>» en la columna «Aprobación» de la
    fila de la versión en decisiones.md (no sale en el Word) y el fichero en «Entregados» de proyecto.md."""
    if uid not in {u.id for u in un.leer(raiz) or []}:
        sys.exit(f"{uid} no está en analisis/cambios.md")
    word = nombre_df(m, vs).replace(f"-v{vs}.docx", f"-{uid}-v{vs}.docx")
    if not (raiz / "entregables" / word).is_file():
        sys.exit(f"No encuentro entregables/{word}: genéralo con «df_docx.js {raiz} --cambio {uid}» antes de enviarlo")
    dm = m.analisis / "decisiones.md"
    lineas = dm.read_text(encoding="utf-8").split("\n") if dm.is_file() else []
    k = next((i for i, l in enumerate(lineas) if re.match(rf"^\|\s*v?{re.escape(vs)}\s*\|", l)), None)
    if k is None:
        sys.exit(f"decisiones.md no tiene la fila de la versión {vs} en «Versiones»")
    c = mo.celdas(lineas[k])
    nota = f"DF del cambio {uid} entregado {fecha}"
    if nota not in c[-1]:
        c[-1] = nota if c[-1].strip(" —-") == "" else f"{c[-1]} · {nota}"
        lineas[k] = "| " + " | ".join(c) + " |"
        dm.write_text("\n".join(lineas), encoding="utf-8")
    (raiz / "proyecto.md").write_text(entregados(texto, word), encoding="utf-8")
    print(f"{nota}: en la versión {vs} de decisiones.md y {word} en «Entregados» de proyecto.md")


def cambio(a):
    """Mueve una unidad de cambio en analisis/cambios.md. Solo bloquea lo que haría perder trabajo o construir algo
    equivocado (references/cambios.md): aprobar con puntos pendientes o con objetos de otra unidad aprobada sin decisión,
    construir lo que ha crecido desde la aprobación, marcar Construida sin verificar o sin reaplicar una corrección
    urgente, pasar a producción sin construir. Cada error dice la salida."""
    raiz, uid, destino = pathlib.Path(a.carpeta), a.id.upper(), a.estado
    hoy = datetime.date.today().isoformat()
    orden = f"proyecto.py cambio <p> {uid}"

    def no(motivo, salida):
        sys.exit(f"✗ {uid} {destino}: {motivo}. Salida: {salida}")
    if not re.fullmatch(r"(EV|URG)-\d+", uid):
        no("el ID de una unidad es EV-nn (evolutivo) o URG-nn (urgente)", "usa uno de esos, p. ej. EV-02")
    if destino in ("aprobada", "produccion") and a.desatendida:
        fu = (a.fuente or "").strip().upper()
        if not fu:
            no("en una sesión desatendida no se aprueba ni se pasa a producción sin el visto bueno del jefe de proyecto",
               f"si lo ha dado (también en el encargo), catalógalo como Aprobación y repite con --fuente FU-nn; "
               "si no, déjalo para él: proyecto.py estado lo lista")
        if (raiz / "fuentes").is_dir() and not list((raiz / "fuentes").glob(f"{fu}*.md")):
            no(f"{fu} no está en fuentes/", f"catalógala antes con leer_fuentes.py y repite con --fuente {fu}")
    m = mo.Proyecto(raiz)
    ctx = un.Contexto(m)
    u = ctx.por_id.get(uid)
    if destino == "abrir":
        if u:
            no(f"ya existe ({u.estado})", "usa el siguiente ID libre (proyecto.py estado)")
        if not (a.titulo or "").strip():
            no("falta el título", f"{orden} abrir --titulo \"…\"")
        u = un.Unidad(uid, a.titulo.strip(), "Urgente" if uid.startswith("URG") else "Evolutivo", desde=m.version("F"))
        ctx.unidades.append(u)
    elif not u:
        no("no está en analisis/cambios.md", f"ábrela antes: {orden} abrir --titulo \"…\"")
    elif destino == "aprobada":
        if u.urgente:
            no("una URG no se aprueba como unidad: va de Abierta a En producción (references/urgentes.md)",
               f"{orden} produccion --ref \"…\" tras el pase")
        if u.estado == un.CONSTRUIDA and not a.fuente:     # vuelve a Aprobada: una URG obliga a reaplicar
            u.estado, u.construida = un.APROBADA, "—"
        elif u.estado not in (un.ABIERTA, un.APROBADA, un.CONSTRUIDA):
            no(f"está {u.estado}", "un cambio sobre lo que ya está en producción es una unidad nueva: "
               "proyecto.py cambio <p> EV-nn abrir --titulo \"…\"")
        else:
            u.construida = "—" if u.estado == un.CONSTRUIDA else u.construida
            aprobar(a, ctx, u, hoy, no, raiz, orden)
    elif destino == "construida":
        if u.urgente:
            no("una URG no pasa por Construida: va de Abierta a En producción", f"{orden} produccion --ref \"…\"")
        if u.estado != un.APROBADA:
            no(f"está {u.estado}: se marca Construida una unidad Aprobada",
               f"apruébala antes ({orden} aprobada --fuente FU-nn)" if u.estado == un.ABIERTA else
               "ninguna: ya pasó por Construida")
        construir(a, ctx, u, hoy, no, raiz, orden)
    elif destino == "produccion":
        if not (a.ref or "").strip():
            no("falta la referencia del pase", f"{orden} produccion --ref \"<referencia>\"")
        if u.urgente:
            if u.estado != un.ABIERTA:
                no(f"está {u.estado}: una URG pasa a producción desde Abierta", "ninguna: ya está cerrada")
            urgente_a_produccion(ctx, uid, no)
        elif u.estado != un.CONSTRUIDA:
            no(f"está {u.estado}: pasa a producción una unidad Construida",
               f"constrúyela y verifícala antes ({orden} construida)" if u.estado in (un.ABIERTA, un.APROBADA) else
               "ninguna: ya está cerrada")
        fecha = (a.fecha or hoy).strip()   # la del pase, no la del registro: la deriva compara con ella
        if not re.fullmatch(r"\d{4}-\d\d-\d\d", fecha):
            no(f"la fecha del pase «{fecha}» no es AAAA-MM-DD", f"{orden} produccion --ref \"…\" --fecha 2026-10-08")
        u.estado, u.produccion = un.PRODUCCION, f"{fecha} · {a.ref.strip()}"
    elif destino == "descartada":
        if u.estado != un.ABIERTA:
            no(f"está {u.estado}: se descarta una unidad Abierta",
               "lo aprobado o construido que ya no se quiere lo deshace una unidad nueva" if u.estado != un.DESCARTADA
               else "ninguna: ya está descartada")
        hecho = sorted(ctx.piezas_de(uid), key=mo.numero) + ctx.cambian(uid)
        if hecho and not a.informe:
            no(f"tiene cambios aplicados ({', '.join(hecho[:8])})",
               f"aplica un informe que los deshaga y descártala con él: {orden} descartada --informe impacto/FU-nn.md")
        if hecho:
            f = pathlib.Path(a.informe)
            f = f if f.is_file() else raiz / a.informe
            if not f.is_file():
                no(f"no existe {a.informe}", "da la ruta del informe que deshace los cambios (impacto/FU-nn.md)")
            if not mo.normaliza(mo.estado_informe(f.read_text(encoding="utf-8"))).startswith("aplicado"):
                no(f"{f.name} no está aplicado", "aplícalo (actualizacion.md) y vuelve a descartarla")
            if ctx.filas_de(uid):
                no(f"técnico §13 sigue teniendo filas de {uid}", "el informe que deshace los cambios también las quita")
        u.estado = un.DESCARTADA
    un.escribir(raiz, ctx.unidades, PLANTILLAS / "cambios.md")
    print(f"{uid}: {u.estado} · analisis/cambios.md\n{u.fila()}")
    if destino == "abrir":
        print("Sus fuentes llevan «Cambio: " + uid + "» en la cabecera del informe" +
              (f"; su ficha es impacto/{uid}.md (assets/plantillas/urgencia.md, references/urgentes.md)" if u.urgente
               else " (references/cambios.md)"))
    if destino == "produccion":
        print("Actualiza el entorno de corrección con este pase: las correcciones urgentes se hacen sobre lo que hay en "
              "producción (references/urgentes.md)")


def urgente_a_produccion(ctx, uid, no):
    """Una URG pasa a producción con su ficha y su «Dónde se corrige»: sin él, o con uno que no dice «Desarrollo» ni
    «Entorno de corrección» cuando hay unidades en curso que chocan, se perdería la tarea de reaplicarla."""
    campos = ctx.ficha_urg(uid)
    if campos is None:
        no(f"falta su ficha impacto/{uid}.md", "escríbela con assets/plantillas/urgencia.md (references/urgentes.md)")
    if un.vacio(campos.get("donde se corrige")):
        no(f"impacto/{uid}.md no dice «Dónde se corrige»: sin eso no se sabe qué unidades tienen que reaplicarla",
           "escribe «Desarrollo» o «Entorno de corrección» (indice.py colision lo dice)")
    choques = ctx.colision(uid)["choques"]
    if not un.donde_se_corrige(campos) and choques:
        no(f"«Dónde se corrige» de impacto/{uid}.md no dice «Desarrollo» ni «Entorno de corrección» y choca con "
           f"unidades en curso ({'; '.join(choques)}): no se sabría quién tiene que reaplicarla",
           "escribe una de las dos en la ficha")


def aprobar(a, ctx, u, hoy, no, raiz, orden):
    """Aprueba una unidad Abierta, o vuelve a aprobar una Aprobada o Construida que ha crecido. Guarda la versión y los
    informes con que se aprueba: lo que llegue después pide otra aprobación antes de construirse."""
    fu = (a.fuente or "").strip().upper()
    if not re.fullmatch(r"FU-\d+", fu):
        no("falta la fuente de la aprobación del jefe de proyecto (chat o correo, R1)",
           f"catalógala con leer_fuentes.py y {orden} aprobada --fuente FU-nn")
    if (raiz / "fuentes").is_dir() and not list((raiz / "fuentes").glob(f"{fu}*.md")):
        no(f"{fu} no está en fuentes/", f"catalógala antes con leer_fuentes.py y repite {orden} aprobada --fuente {fu}")
    pend = [f"{n} punto {p.get('#', '?')}" for n, t, p in ctx.puntos_de(u.id)
            if p and mo.normaliza(p.get("decision", "")).strip(" *").startswith("pendiente")]
    if pend:
        no(f"puntos pendientes de aprobación en sus informes: {', '.join(pend)}",
           "decídelos (✔, ✗ o ❓ en «Decisión») y vuelve a aprobarla")
    if (a.comparte or "").strip():
        u.comparte = a.comparte.strip() if un.vacio(u.comparte) else f"{u.comparte}; {a.comparte.strip()}"
    mias, choques = set(ctx.cambian(u.id)), []
    for v in ctx.unidades:
        if v.id == u.id or v.urgente or v.estado not in (un.APROBADA, un.CONSTRUIDA):
            continue
        comunes = [o for o in ctx.cambian(v.id) if o in mias]
        decidido = v.id in un.RX_UNIDAD.findall(u.comparte) or u.id in un.RX_UNIDAD.findall(v.comparte)
        if comunes and not decidido:
            choques.append((v.id, comunes))
    if choques:
        v0, o0 = choques[0]
        no("comparte objetos con otra unidad aprobada y no hay decisión: "
           + "; ".join(f"{v} ({', '.join(o)})" for v, o in choques),
           f"decidid el orden o unidlas y escribidlo: --comparte \"{v0} en {o0[0]}: secuenciar ({v0} primero)\"")
    u.estado, u.aprobada = un.APROBADA, f"{hoy} · {fu}"
    u.aprobada_en, u.aprobada_con = ctx.m.version("F"), tuple(ctx.informes_de(u.id))


def construir(a, ctx, u, hoy, no, raiz, orden):
    crecida = ctx.crecida(u.id)
    if crecida:
        no(f"{u.id} ha crecido desde que se aprobó ({'; '.join(crecida)})",
           f"vuelve a aprobarla ({orden} aprobada --fuente FU-nn) o lleva lo nuevo a otra unidad")
    reaplicadas = {x.upper() for x in a.reaplicada or []}
    for g in reaplicadas:
        if g not in ctx.por_id or not ctx.por_id[g].urgente:
            no(f"--reaplicada {g}: no es una URG de analisis/cambios.md", "pon solo las URG que pide el encargo")
    falta = [(g, objs) for g, objs in ctx.reaplicar(u.id) if g not in reaplicadas]
    if falta:
        no("faltan correcciones urgentes por reaplicar en desarrollo: "
           + "; ".join(f"{g} en {', '.join(o)}" for g, o in falta),
           "reaplícalas y, cuando su prueba pase, confírmalo: " + " ".join(f"--reaplicada {g}" for g, _ in falta))
    ver = raiz / "construccion" / "verificacion" / f"{u.id}.json"
    if a.manual:
        marca = "manual"
    elif not ver.is_file():
        no(f"falta construccion/verificacion/{u.id}.json",
           f"pasa la orden «verificar» de construccion/{u.id}.md (sin Dev MCP, --manual)")
    else:
        try:
            d = json.loads(ver.read_text(encoding="utf-8"))
        except ValueError as e:
            no(f"{ver} no es JSON: {e}", f"vuelve a pasar la orden «verificar» de construccion/{u.id}.md")
        objetos = d.get("objetos", [])
        sin = [o for o in ctx.cambian(u.id) if o not in {x.get("pedido") for x in objetos}]
        if sin:
            no(f"la verificación no incluye {', '.join(sin)}",
               f"vuelve a pasar «verificar» con los objetos de construccion/{u.id}.md (indice.py encargo)")
        situacion = {un.objeto(o): f["situacion"] for f in ctx.filas_de(u.id) for o in f["objetos"]}
        malos, sin_leer = [], []
        for o in objetos:
            dif = dict(o.get("diferencias") or ({} if o.get("existe") else {"falta": True}))
            if o.get("pedido") not in ctx.cambian(u.id) and not o.get("diferencias"):
                continue
            if dif.pop("camposSinLeer", None):   # no se pudo leer: no es que esté mal construido
                sin_leer.append(o.get("pedido"))
            # §3 de un objeto que se modifica lleva solo los campos de esta unidad: los demás «sobran» y no cuentan
            if dif and not (situacion.get(o.get("pedido")) in ("modifica", "existe") and set(dif) <= {"sobranCampos"}):
                malos.append(f"{o.get('pedido')}: {', '.join(dif)}")
        if malos:
            no(f"lo construido no es lo del técnico: {'; '.join(malos)} (detalle en {ver})",
               "corrígelo en el entorno y vuelve a verificar; si el técnico está mal, corrígelo con un informe")
        if sin_leer:
            no(f"no se pudo leer {', '.join(sin_leer)} en el entorno", "repite «verificar» o usa --manual")
        marca = "verificada"
    u.estado, u.construida = un.CONSTRUIDA, f"{hoy} · {marca}"
    for g in sorted(reaplicadas):
        ctx.por_id[g].construida = f"{hoy} · reaplicada en {u.id}"


def main():
    for st in (sys.stdout, sys.stderr):   # antes de leer los argumentos: la ayuda y sus errores también llevan tildes
        st.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("iniciar"); s.add_argument("carpeta")
    s.add_argument("--nombre", help="el nombre del proyecto; hace falta solo la primera vez")
    s.add_argument("--cliente"); s.add_argument("--direccion"); s.add_argument("--tipo")
    s.set_defaults(f=iniciar)
    s = sub.add_parser("estado"); s.add_argument("carpeta"); s.set_defaults(f=estado)
    s = sub.add_parser("copia"); s.add_argument("carpeta"); s.set_defaults(f=copia)
    s = sub.add_parser("version"); s.add_argument("carpeta"); s.set_defaults(f=version)
    s.add_argument("--fuente", nargs="+", required=True, metavar="FU-nn", help="las fuentes del informe")
    s.add_argument("--que", required=True, help="qué cambia, en una frase y en palabras del cliente (sale en el Word): "
                                                 "la fila de la versión en decisiones.md")
    s.add_argument("--informe", help="el informe, si no es impacto/<primera fuente>.md (una urgencia: impacto/URG-nn.md)")
    s.add_argument("--decision", nargs=4, action="append", metavar=("TIPO", "AFECTA_A", "LO_NUEVO", "LO_DE_ANTES"),
                   help="la fila D de un punto CAMBIA, ANULA, RESPONDE, VALIDA o ALCANCE±, con la primera fuente de "
                        "--fuente; «lo de antes» con su cita")
    s = sub.add_parser("entregar"); s.add_argument("carpeta"); s.set_defaults(f=entregar)
    s.add_argument("--cambio", help="el DF de un cambio (df_docx.js --cambio): se anota en decisiones.md")
    s = sub.add_parser("cambio"); s.add_argument("carpeta"); s.add_argument("id"); s.set_defaults(f=cambio)
    s.add_argument("estado", choices=["abrir", "aprobada", "construida", "produccion", "descartada"])
    s.add_argument("--titulo"); s.add_argument("--fuente"); s.add_argument("--comparte"); s.add_argument("--ref")
    s.add_argument("--reaplicada", nargs="+", metavar="URG-nn"); s.add_argument("--manual", action="store_true")
    s.add_argument("--informe"); s.add_argument("--desatendida", action="store_true")
    s.add_argument("--fecha", help="produccion: la fecha del pase (AAAA-MM-DD); sin ella, hoy")
    a = ap.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
