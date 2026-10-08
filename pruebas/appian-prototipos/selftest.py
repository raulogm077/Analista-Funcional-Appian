#!/usr/bin/env python3
"""Comprueba que el kit funciona en este equipo.

Uso:  python3 pruebas/appian-prototipos/selftest.py

Prueba el kit de $PLUGIN_A_PROBAR/skills/appian-prototipos (por defecto, el de este repositorio).
1. Valida y construye, en una carpeta temporal, el catálogo de patrones, el prototipo de prueba de dos pantallas
   que genera datos/autorizaciones/generar_app.py a partir del análisis ficticio del analista y cada galería
   (galerias/<galería>/app.json: las que haya).
2. La marca: sin --brand, la estándar de Appian y sin logo; con --brand x, la de brand-x.json junto al app.json (con su
   logo); con una marca que no está junto al app.json, error que dice dónde ponerla; y los helpers, con la neutra por
   defecto y la del proyecto con usar_marca().
3. La configuración de marca de un cliente con marca.py, con la de una empresa ficticia: crear (con y sin perfil CSS y
   ROUNDED con un botón principal propio; el contraste de cada color, el logo, el perfil, la guía, la salida y los
   errores, también al escribir) y construir con cada una el catálogo de patrones; y web: qué es el mismo sitio y «logo»
   como palabra, y contra datos/web-ficticia/ y otra página (logo SVG en línea, hoja de localhost y un PDF), servidas en
   127.0.0.1 por la propia prueba, y contra un puerto cerrado.
4. Si hay Playwright y un navegador, pasa la prueba de humo y la auditoría de contraste a todo lo construido y comprueba
   las iniciales del avatar de la cabecera: con la marca estándar, siguen con el oscuro del site; con un realce de
   luminancia media, en negro puro.
Sale con 0 si validar y construir funcionan (lo imprescindible); la prueba de humo y
las capturas son opcionales y se informa de lo que falta para tenerlas.
"""
import colorsys, functools, http.server, json, os, pathlib, re, shutil, socket, subprocess, sys, tempfile, threading

AQUI = pathlib.Path(__file__).resolve().parent
PLUGIN = pathlib.Path(os.environ.get("PLUGIN_A_PROBAR") or AQUI.parents[1]).resolve()
ROOT = PLUGIN / "skills" / "appian-prototipos"
HERE = ROOT / "scripts"
sys.path.insert(0, str(HERE))
from entorno import utf8_stdio  # noqa: E402


def run(args):
    r = subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, (r.stdout + r.stderr).strip()


def coverage():
    """Cada función del catálogo oficial de Appian (schemas/catalogo-appian.json) la conocen los schemas, la pinta el runtime
    (o la consume su componente padre) y aparece en la galería galerias/componentes."""
    from validate import load_catalog, SUBOBJECTS
    cat = json.loads((ROOT / "schemas" / "catalogo-appian.json").read_text(encoding="utf-8"))
    funcs = [f for fs in cat["categories"].values() for f in fs]
    known = load_catalog()
    rend = set(re.findall(r'R\["(a![A-Za-z]+)"\]\s*=', (ROOT / "runtime" / "appian-kit.js").read_text(encoding="utf-8")))
    used = set()

    def walk(o):
        if isinstance(o, dict):
            if isinstance(o.get("type"), str):
                used.add(o["type"])
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(json.loads((ROOT / "galerias" / "componentes" / "app.json").read_text(encoding="utf-8")))
    probs = [f"{f}: no está en los schemas" for f in funcs if f not in known]
    probs += [f"{f}: el runtime no lo pinta" for f in funcs if f not in rend and f not in SUBOBJECTS]
    probs += [f"{f}: falta en la galería de componentes" for f in funcs if f not in used]
    return cat, funcs, probs


# marca de prueba que va junto al app.json, como la de un cliente en <p>/prototipo/ (colores que no son de ninguna otra)
MARCA_PRUEBA = {"id": "prueba", "name": "Marca de prueba",
                "site": {"navigationLayout": "HEADER_BAR", "headerBarStyle": "MERCURY", "backgroundColor": "#22313F",
                         "selectedPageHighlightColor": "#F2C14E", "accentColor": "#7B2D8E", "logo": "logo-prueba.svg", "logoAltText": "Prueba"},
                "palette": {"navy": "#22313F"}}
LOGO_PRUEBA = "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 10 10'><title>logo de prueba</title></svg>"


def built_with(html):
    """La marca con la que se construyó un HTML (el JSON de px-brand) y su logo (la plantilla px-logo)."""
    t = pathlib.Path(html).read_text(encoding="utf-8")
    m = re.search(r'<script type="application/json" id="px-brand">(.*?)</script>', t, re.S)
    logo = re.search(r'<template id="px-logo">(.*?)</template>', t, re.S)
    return (json.loads(m.group(1)) if m else {}), (logo.group(1) if logo else None), t


def brands(tmp, built):
    """[(qué se comprueba, problemas)] de la marca en build.py y en los helpers."""
    out = []
    cat = next((html for _, html, spec in built if spec.name == "catalogo-patrones.json"), None)
    probs = []
    if cat is None:
        probs.append("no se construyó el catálogo de patrones")
    else:
        b, logo, _ = built_with(cat)
        if b.get("id") != "appian":
            probs.append(f"sin --brand, build.py construye con «{b.get('id')}» y no con «appian»")
        if logo:
            probs.append("la marca estándar de Appian no lleva logo y el HTML trae uno")
    out.append(("marca por defecto (sin --brand): appian, sin logo", probs))
    # la marca del proyecto: brand-prueba.json y su logo junto al app.json
    carpeta = tmp / "Carpeta con espacios" / "prototipo"
    carpeta.mkdir(parents=True)
    spec = carpeta / "app.json"
    spec.write_text((ROOT / "templates" / "catalogo-patrones.json").read_text(encoding="utf-8"), encoding="utf-8")
    (carpeta / "brand-prueba.json").write_text(json.dumps(MARCA_PRUEBA, ensure_ascii=False), encoding="utf-8")
    (carpeta / "logo-prueba.svg").write_text(LOGO_PRUEBA, encoding="utf-8")
    html = carpeta / "prototipo.html"
    code, salida = run([HERE / "build.py", spec, "-o", html, "--brand", "prueba"])
    probs = []
    if code or not html.exists():
        probs.append(f"build.py --brand prueba falla:\n{salida[-800:]}")
    else:
        b, logo, t = built_with(html)
        if b.get("id") != "prueba":
            probs.append(f"con --brand prueba construye con «{b.get('id')}»")
        if f"--accent: {MARCA_PRUEBA['site']['accentColor']};" not in t:
            probs.append("el HTML no lleva el acento de la marca del proyecto")
        if "logo de prueba" not in (logo or ""):
            probs.append("el HTML no lleva el logo de la marca del proyecto")
    out.append(("marca del proyecto (--brand prueba, junto al app.json): sus colores y su logo", probs))
    # una marca que no está junto al app.json: error que dice dónde ponerla
    sin = tmp / "sin marca"
    sin.mkdir()
    (sin / "app.json").write_text(spec.read_text(encoding="utf-8"), encoding="utf-8")
    code, salida = run([HERE / "build.py", sin / "app.json", "-o", sin / "prototipo.html", "--brand", "aena"])
    falta = str(sin.resolve() / "brand-aena.json")
    probs = [] if code and falta in salida else [f"build.py --brand aena sin brand-aena.json sale con {code} y no dice «{falta}»:\n{salida[-600:]}"]
    out.append(("marca que falta (--brand aena sin su fichero): error con la ruta donde ponerla", probs))
    # los helpers: la marca neutra por defecto y la del proyecto con usar_marca(), antes de from sail_helpers import *
    prog = ("import sys; sys.path.insert(0, sys.argv[1]); import sail_helpers as s; print(s._BRAND.get('id'), s.PRIMARY); "
            "s.usar_marca('prueba', sys.argv[2]); from sail_helpers import NAVY, GREEN; print(NAVY, GREEN)")
    code, salida = run(["-c", prog, HERE, carpeta])
    lineas = salida.splitlines()
    esperado = ["appian ACCENT", f"{MARCA_PRUEBA['palette']['navy']} {MARCA_PRUEBA['site']['selectedPageHighlightColor']}"]
    probs = [] if code == 0 and lineas[-2:] == esperado else [f"esperaba {esperado} y sale ({code}):\n{salida[-600:]}"]
    out.append(("helpers: marca neutra por defecto y la del proyecto con usar_marca()", probs))
    # al entregar, el perfil CSS es el que deja build.py junto al HTML, también con una marca hecha a mano (sin marca.py)
    paso = re.search(r"### 5\. Entregar\n(.*?)(?=\n## |\Z)", (ROOT / "SKILL.md").read_text(encoding="utf-8"), re.S)
    probs = [] if paso and "`prototipo-<app>-perfil-css.txt`" in paso.group(1) else \
        ["el paso 5 de SKILL.md no entrega `prototipo-<app>-perfil-css.txt`, el perfil CSS que escribe build.py"]
    out.append(("entrega: el perfil CSS que escribe build.py, con cualquier marca", probs))
    return out


# la configuración de marca de un cliente con marca.py: la de una empresa ficticia (datos/web-ficticia/), con un acento
# que no llega a 4,5:1 sobre blanco (#5DA9E9)
WEB = AQUI / "datos" / "web-ficticia"
WEB_MARCA = ("#1D2B4A", "#5DA9E9")  # sus dos colores de marca: --nb-noche y --nb-cielo de estilos.css
CLIENTE = {"--id": "x", "--nombre": "Nubarrón Mensajería", "--fuente": "Web ficticia de prueba (datos/web-ficticia), 8 de octubre de 2026",
           "--oscuro": "#1D2B4A", "--realce": "#F2B134", "--acento": "#5DA9E9", "--secundarios": "#C0563B", "--tipografia": "Nunito Sans"}
GRIS_PAGINA = "#F4F5F7"
SEMANTICOS = (("negative-on-light-color", "error-background-color"), ("positive-on-light-color", "success-background-color"),
              ("warn-on-light-color", "warn-background-color"), ("info-on-light-color", "info-background-color"))
FONDOS_AVISO = ("success-background-color", "info-background-color", "error-background-color", "warn-background-color")
# otra página de la empresa ficticia: el logo, un SVG en línea en la cabecera; la hoja de estilo, servida con otro nombre del
# mismo equipo (localhost, la página va en 127.0.0.1). {puerto} es el del servidor de la prueba
PAGINA_EXTRA = """<!doctype html>
<html lang="es"><head><meta charset="utf-8"><title>Nubarrón Mensajería · Área de clientes</title>
<link rel="stylesheet" href="http://localhost:{puerto}/otra.css"></head>
<body><header class="cabecera"><a href="./" class="inicio"><svg class="logo" viewBox="0 0 120 24" role="img" aria-label="Nubarrón Mensajería"><rect width="24" height="24" rx="4" fill="#1D2B4A"/><path d="M6 16h12" stroke="#5DA9E9" stroke-width="3"/></svg></a></header>
<main><p class="aviso">Área de clientes</p></main></body></html>
"""
ASSUMPTION = re.compile(r"«Marca de Nubarrón Mensajería sacada de .+ el \d{1,2} de [a-z]+ de \d{4}; falta que la confirme el cliente»")


def sombra_del_runtime(valor, oscuro):
    """Problemas de una sombra de tarjeta que tiene que ser la del runtime (--card-shadow de appian-kit.css): los mismos
    desplazamientos, desenfoques y opacidades, con el color del oscuro."""
    css = (ROOT / "runtime" / "appian-kit.css").read_text(encoding="utf-8")
    runtime = re.search(r"--card-shadow:\s*([^;]+);", css).group(1)
    forma = lambda v: re.sub(r"\s+", " ", re.sub(r"rgba\([^)]*\)", "C", v)).strip()
    canales = lambda v: [[float(x) for x in m.split(",")] for m in re.findall(r"rgba\(([^)]*)\)", v)]
    r, g, b = (int(oscuro[i:i + 2], 16) for i in (1, 3, 5))
    if not valor or forma(valor) != forma(runtime) or [c[3] for c in canales(valor)] != [c[3] for c in canales(runtime)] \
            or any(c[:3] != [r, g, b] for c in canales(valor)):
        return [f"card-box-shadow «{valor}» no es la del runtime («{runtime}») con el color del oscuro {oscuro}"]
    return []


def opciones(**cambios):
    """Las opciones de CLIENTE para marca.py crear, con cambios (nombre_con_guiones_bajos=valor; None la quita)."""
    o = dict(CLIENTE)
    for k, v in cambios.items():
        k = "--" + k.replace("_", "-")
        if v is None:
            o.pop(k, None)
        else:
            o[k] = str(v)
    return [x for kv in o.items() for x in kv]


def matiz(h):
    """Matiz (grados) de un color #RRGGBB."""
    return colorsys.rgb_to_hls(*(int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)))[0] * 360


def marca_cliente(tmp, built):
    """[(qué se comprueba, problemas)] de marca.py: crear (con y sin perfil CSS, y sus errores) y web (contra la web
    ficticia servida en 127.0.0.1 y contra un puerto cerrado). El catálogo de patrones construido con la marca creada se
    añade a built para la prueba de humo y la auditoría de contraste."""
    from validate import contrast, check_css_profile, Report
    from build import css_profile_text, mix_white
    marca, out = HERE / "marca.py", []
    estandar = json.loads((ROOT / "assets" / "brand-appian.json").read_text(encoding="utf-8"))
    std_css = json.loads((ROOT / "schemas" / "css-profile-properties.json").read_text(encoding="utf-8"))["appianStandardColors"]
    claro = (WEB / "logo.svg").read_text(encoding="utf-8")
    negativo = tmp / "logo-negativo.svg"  # el logo para fondo oscuro: el de la web con el texto en blanco
    negativo.write_text(claro.replace('fill="#1D2B4A"', 'fill="#FFFFFF"'), encoding="utf-8")

    # 1. crear, con perfil CSS, el logo en negativo para la cabecera y el de la web para fondos claros; los botones y los
    # campos de la web ficticia tienen las esquinas redondeadas: SEMI_ROUNDED
    carpeta = tmp / "Carpeta con espacios" / "Gestión app" / "prototipo"
    code, salida = run([marca, "crear", *opciones(formas="SEMI_ROUNDED"), "--logo", negativo, "--logo-claro", WEB / "logo.svg", carpeta])
    f = {n: carpeta / n for n in ("brand-x.json", "logo-x-on-dark.svg", "logo-x-on-light.svg", "perfil-css-x.txt", "marca-x.md")}
    probs = []
    if code or not f["brand-x.json"].is_file():
        probs.append(f"marca.py crear sale con {code}:\n{salida[-800:]}")
    else:
        b = json.loads(f["brand-x.json"].read_text(encoding="utf-8"))
        site = b.get("site") or {}
        faltan = [k for k in [*estandar, "cssProfile"] if k not in b]
        if faltan:
            probs.append(f"a brand-x.json le faltan secciones de brand-appian.json: {', '.join(faltan)}")
        acento = str(site.get("accentColor", ""))
        if not re.fullmatch(r"#[0-9A-Fa-f]{6}", acento):
            probs.append(f"site.accentColor «{acento}» no es un color #RRGGBB")
        else:
            if min(contrast(acento, "#FFFFFF"), contrast(acento, GRIS_PAGINA)) < 4.5:
                probs.append(f"el acento {acento} no llega a 4,5:1 sobre blanco y sobre {GRIS_PAGINA}")
            flojos = [std_css[k] for k in FONDOS_AVISO if contrast(acento, std_css[k]) < 4.5]
            if flojos:  # los avisos llevan su botón (del acento) dentro
                probs.append(f"el acento {acento} no llega a 4,5:1 sobre los fondos de aviso de Appian {', '.join(flojos)}")
            d = abs(matiz(acento) - matiz(CLIENTE["--acento"])) % 360
            if min(d, 360 - d) >= 10:
                probs.append(f"el acento {acento} se aleja {min(d, 360 - d):.0f}° del matiz de {CLIENTE['--acento']}")
        navy = str((b.get("palette") or {}).get("navy", "")).upper()
        if navy != CLIENTE["--oscuro"] or navy != str(site.get("backgroundColor", "")).upper():
            probs.append(f"palette.navy es «{navy}» y el oscuro, {CLIENTE['--oscuro']} (site.backgroundColor {site.get('backgroundColor')})")
        rep = Report()
        check_css_profile(b, rep)
        probs += [f"perfil CSS: {e}" for e in rep.errors]
        grupos = (b.get("cssProfile") or {}).get("groups") or []
        if len(grupos) != 6:
            probs.append(f"el perfil CSS de una marca SEMI_ROUNDED lleva {len(grupos)} grupos y no seis: {[g.get('comment') for g in grupos]}")
        flat = {k: v for g in grupos for k, v in (g.get("properties") or {}).items()}
        for texto, fondo in SEMANTICOS:
            fg, bg = flat.get(texto, std_css[texto]), flat.get(fondo, std_css[fondo])
            if min(contrast(fg, "#FFFFFF"), contrast(fg, bg)) < 4.5:
                probs.append(f"{texto} {fg} no llega a 4,5:1 sobre blanco y sobre su fondo {bg} ({fondo})")
        borde = flat.get("input-box-on-light-border-color")
        if not borde or min(contrast(borde, "#FFFFFF"), contrast(borde, GRIS_PAGINA)) < 3:
            probs.append(f"el borde de los campos (input-box-on-light-border-color: {borde}) no llega a 3:1 sobre blanco y sobre {GRIS_PAGINA}")
        probs += sombra_del_runtime(flat.get("card-box-shadow"), CLIENTE["--oscuro"])
        if not ASSUMPTION.search(salida):
            probs.append(f"la salida no da el $assumption «Marca de <empresa> sacada de <fuente> el <fecha>; …»:\n{salida[-400:]}")
        if site.get("logo") != "logo-x-on-dark.svg" or not f["logo-x-on-dark.svg"].is_file() \
                or f["logo-x-on-dark.svg"].read_text(encoding="utf-8") != negativo.read_text(encoding="utf-8"):
            probs.append(f"el logo para fondo oscuro no está copiado como logo-x-on-dark.svg (site.logo: {site.get('logo')})")
        if not f["logo-x-on-light.svg"].is_file() or f["logo-x-on-light.svg"].read_text(encoding="utf-8") != claro:
            probs.append("el logo para fondo claro no está copiado como logo-x-on-light.svg")
        if not f["perfil-css-x.txt"].is_file() or f["perfil-css-x.txt"].read_text(encoding="utf-8") != css_profile_text(b):
            probs.append("perfil-css-x.txt no está o no es el texto del perfil que escribe build.py")
        guia = f["marca-x.md"].read_text(encoding="utf-8") if f["marca-x.md"].is_file() else ""
        if not guia:
            probs.append("no escribe marca-x.md")
        for prop, k in (("Background Color", "backgroundColor"), ("Selected Page Highlight Color", "selectedPageHighlightColor"), ("Accent Color", "accentColor")):
            if not any(prop in l and str(site.get(k)) in l for l in guia.splitlines()):
                probs.append(f"marca-x.md no da la configuración del Site: falta «{prop}» con {site.get(k)}")
        if "el logo de Nubarrón Mensajería" not in guia:
            probs.append("los pendientes de marca-x.md no nombran a la empresa (Nubarrón Mensajería)")
        # la guía no dice «AA» de lo que no se comprueba: lo dice aparte, y los secundarios van en «Sin comprobar»
        if "Comprobado con WCAG 2.2 AA" not in guia or not re.search(r"Sin comprobar:\s*\n\s*\n- Los colores secundarios", guia) \
                or "Los colores llegan a WCAG 2.2 AA" in guia:
            probs.append("marca-x.md no separa lo comprobado con WCAG 2.2 AA de lo que no se comprueba (los secundarios)")
        # estados (references/marca.md): «neutral», el tinte de slate, y cada etiqueta con su texto a 4,5:1
        pal, st = b.get("palette") or {}, b.get("states") or {}
        if (st.get("neutral") or {}).get("tag") != mix_white(str(pal.get("slate")), 0.15).upper() \
                or any(contrast("#222222", v["tag"]) < 4.5 for k, v in st.items() if not k.startswith("_")):
            probs.append(f"los estados no son los de references/marca.md (neutral, el tinte de slate {pal.get('slate')}): {st}")
        ajustes = [l.strip() for l in salida.splitlines() if re.search(r"#[0-9A-F]{6} → #[0-9A-F]{6}", l)]
        if not any(a.startswith(f"acento {CLIENTE['--acento']} → {acento}") for a in ajustes):
            probs.append(f"la salida no dice el ajuste del acento ({CLIENTE['--acento']} → {acento}):\n{salida[-600:]}")
        probs += [f"marca-x.md no recoge el ajuste «{a}»" for a in ajustes if a not in guia]
        # el catálogo de patrones, construido con esa marca (la auditoría de contraste va con el resto de lo construido)
        spec, html = carpeta / "app.json", carpeta / "prototipo.html"
        spec.write_text((ROOT / "templates" / "catalogo-patrones.json").read_text(encoding="utf-8"), encoding="utf-8")
        code, salida = run([HERE / "build.py", spec, "-o", html, "--brand", "x"])
        if code or not html.exists():
            probs.append(f"build.py --brand x falla con la marca de marca.py:\n{salida[-800:]}")
        elif f"--accent: {acento};" not in html.read_text(encoding="utf-8"):
            probs.append("el catálogo construido con --brand x no lleva el acento de la marca")
        else:
            built.append(("catálogo de patrones con la marca de marca.py", html, spec))
    out.append(("marca.py crear: brand-x.json con las secciones de la estándar y su perfil CSS, contraste AA (el acento también sobre los "
                "avisos), estados, sombra del kit, logos, perfil, guía con el Site, los ajustes y lo que no se comprueba, y el supuesto; "
                "el catálogo construido con ella", probs))

    # 2. crear --sin-perfil-css y sin --formas, con un realce que no se ve sobre el oscuro y el logo de la web (para fondo
    # claro); con esa marca, el catálogo de patrones (el avatar de la cabecera, sobre el realce a 3:1, tiene que leerse)
    carpeta = tmp / "Carpeta con espacios" / "Sin perfil" / "prototipo"
    code, salida = run([marca, "crear", *opciones(realce="#3E5C8A", secundarios=None, tipografia=None, mayusculas="no"),
                        "--logo", WEB / "logo.svg", "--sin-perfil-css", carpeta])
    probs = []
    if code or not (carpeta / "brand-x.json").is_file():
        probs.append(f"marca.py crear --sin-perfil-css sale con {code}:\n{salida[-800:]}")
    else:
        b = json.loads((carpeta / "brand-x.json").read_text(encoding="utf-8"))
        site = b.get("site") or {}
        if "cssProfile" in b or (carpeta / "perfil-css-x.txt").exists():
            probs.append("con --sin-perfil-css escribe el perfil CSS")
        realce, oscuro = str(site.get("selectedPageHighlightColor")), str(site.get("backgroundColor"))
        if not re.fullmatch(r"#[0-9A-Fa-f]{6}", realce) or contrast(realce, oscuro) < 3:
            probs.append(f"el realce {realce} no llega a 3:1 sobre el oscuro {oscuro}")
        guia = (carpeta / "marca-x.md").read_text(encoding="utf-8") if (carpeta / "marca-x.md").is_file() else ""
        linea = f"realce #3E5C8A → {realce}"
        if linea not in salida or linea not in guia:
            probs.append(f"la salida y marca-x.md no dicen el ajuste «{linea}…»:\n{salida[-600:]}")
        if not re.search(r"logo.*3:1.*negativo", salida, re.S):
            probs.append(f"no avisa de que el logo no llega a 3:1 sobre el oscuro (hace falta su versión en negativo):\n{salida[-600:]}")
        formas = {k: site.get(k) for k in ("buttonShape", "inputShape", "dialogShape", "useUppercase", "useUppercasePageTitles")}
        if formas != {"buttonShape": "SQUARED", "inputShape": "SQUARED", "dialogShape": "SQUARED", "useUppercase": False, "useUppercasePageTitles": False}:
            probs.append(f"sin --formas (SQUARED, la de Appian) y con --mayusculas no da {formas}")
        # gráficos: todas las series con 3:1 sobre blanco y los colores de la marca dentro (el realce ajustado, también)
        series = (b.get("components") or {}).get("chartColorScheme") or []
        flojas = [c for c in series if contrast(c, "#FFFFFF") < 3]
        if flojas or realce not in series:
            probs.append(f"chartColorScheme {series}: series con menos de 3:1 sobre blanco {flojas}; el realce ajustado {realce} "
                         f"{'está' if realce in series else 'no está'}")
        spec, html = carpeta / "app.json", carpeta / "prototipo.html"
        spec.write_text((ROOT / "templates" / "catalogo-patrones.json").read_text(encoding="utf-8"), encoding="utf-8")
        code, salida = run([HERE / "build.py", spec, "-o", html, "--brand", "x"])
        if code or not html.exists():
            probs.append(f"build.py --brand x falla con la marca sin perfil CSS:\n{salida[-800:]}")
        else:
            built.append(("catálogo de patrones con la marca de marca.py sin perfil CSS", html, spec))
    out.append(("marca.py crear --sin-perfil-css: sin perfil; SQUARED sin --formas; aclara el realce hasta 3:1 y avisa del logo que "
                "no se ve sobre el oscuro; gráficos con 3:1 y el realce dentro; el catálogo construido con ella", probs))

    # 3. crear ROUNDED, con un botón principal que no se distingue del fondo (#90CE00) y un realce de luminancia media
    # (#5B7FB5: ni blanco ni casi negro llegan a 4,5:1 sobre él; las iniciales del avatar de la cabecera, en negro)
    carpeta = tmp / "Carpeta con espacios" / "Redondeada" / "prototipo"
    code, salida = run([marca, "crear", *opciones(realce="#5B7FB5", principal="#90CE00", formas="ROUNDED", secundarios=None, tipografia=None), carpeta])
    probs = []
    if code or not (carpeta / "brand-x.json").is_file():
        probs.append(f"marca.py crear --formas ROUNDED sale con {code}:\n{salida[-800:]}")
    else:
        b = json.loads((carpeta / "brand-x.json").read_text(encoding="utf-8"))
        site = b.get("site") or {}
        formas = {k: site.get(k) for k in ("buttonShape", "inputShape", "dialogShape")}
        if formas != {"buttonShape": "ROUNDED", "inputShape": "SEMI_ROUNDED", "dialogShape": "ROUNDED"}:
            probs.append(f"--formas ROUNDED da {formas} (los campos solo admiten SEMI_ROUNDED)")
        rep = Report()
        check_css_profile(b, rep)
        probs += [f"perfil CSS: {e}" for e in rep.errors]
        flat = {k: v for g in (b.get("cssProfile") or {}).get("groups") or [] for k, v in (g.get("properties") or {}).items()}
        radios = {k: flat.get(k) for k in ("button-rounded-border-radius", "input-box-semi-rounded-border-radius")}
        if radios != {"button-rounded-border-radius": "999px", "input-box-semi-rounded-border-radius": "4px"}:
            probs.append(f"los radios de una marca ROUNDED son {radios}")
        p = str((b.get("components") or {}).get("primaryButton", {}).get("color", ""))
        if not re.fullmatch(r"#[0-9A-Fa-f]{6}", p) or min(contrast(p, c) for c in ("#FFFFFF", GRIS_PAGINA, *(std_css[k] for k in FONDOS_AVISO))) < 3 \
                or max(contrast(p, "#FFFFFF"), contrast(p, "#1A1A1A")) < 4.5:
            probs.append(f"el botón principal {p} no llega a 3:1 sobre blanco, sobre {GRIS_PAGINA} y sobre los fondos de aviso, o su texto a 4,5:1")
        else:
            d = abs(matiz(p) - matiz("#90CE00")) % 360
            guia = (carpeta / "marca-x.md").read_text(encoding="utf-8") if (carpeta / "marca-x.md").is_file() else ""
            linea = f"botón principal #90CE00 → {p}"
            if min(d, 360 - d) >= 10 or linea not in salida or linea not in guia:
                probs.append(f"el ajuste del botón principal ({linea}…, {min(d, 360 - d):.0f}° de matiz) no sale en la salida y en la guía:\n{salida[-600:]}")
        spec, html = carpeta / "app.json", carpeta / "prototipo.html"
        spec.write_text((ROOT / "templates" / "catalogo-patrones.json").read_text(encoding="utf-8"), encoding="utf-8")
        code, salida = run([HERE / "build.py", spec, "-o", html, "--brand", "x"])
        if code or not html.exists():
            probs.append(f"build.py --brand x falla con la marca ROUNDED:\n{salida[-800:]}")
        else:
            built.append(("catálogo de patrones con la marca de marca.py redondeada", html, spec))
    out.append(("marca.py crear --formas ROUNDED: formas y radios; el botón principal ajustado a 3:1 con su texto a 4,5:1; el "
                "catálogo construido con ella", probs))

    # 4. errores: sale con 2, dice por qué y no escribe nada
    probs = []
    for que, cambios, destino, dice in (("un color mal escrito", {"acento": "#5DA9E"}, tmp / "error color", "#RRGGBB"),
                                         ("un id que no es [a-z0-9-]", {"id": "Cliente X"}, tmp / "error id", "[a-z0-9-]"),
                                         ("un logo que no existe", {"logo": tmp / "no-existe.svg"}, tmp / "error logo", "no-existe.svg"),
                                         ("la carpeta del plugin como destino", {}, ROOT / "marca-de-prueba", "plugin")):
        code, salida = run([marca, "crear", *opciones(**cambios), destino])
        escrito = destino.exists()
        if code != 2 or dice not in salida or escrito:
            probs.append(f"con {que}, sale con {code}{' y escribe en ' + str(destino) if escrito else ''} (debe salir con 2 y decir «{dice}»):\n{salida[-400:]}")
        if escrito and ROOT in destino.parents:
            shutil.rmtree(destino, ignore_errors=True)
    # la carpeta del plugin es la que contiene skills/, lleve o no .claude-plugin/plugin.json: una copia de la skill sin él
    copia = tmp / "copia del plugin"
    shutil.copytree(ROOT, copia / "skills" / ROOT.name, ignore=shutil.ignore_patterns("galerias", "__pycache__"))
    destino = copia / "skills" / "otra-skill" / "prototipo"
    code, salida = run([copia / "skills" / ROOT.name / "scripts" / "marca.py", "crear", *opciones(), destino])
    if code != 2 or "plugin" not in salida or destino.exists():
        probs.append(f"con skills/otra-skill/prototipo de una copia del plugin sin plugin.json como destino, sale con {code}"
                     f"{' y escribe' if destino.exists() else ''} (debe salir con 2 y decir «plugin»):\n{salida[-400:]}")
    # un error al escribir (donde va la guía hay una carpeta): sale con 2, sin traza, y dice qué llegó a escribir
    carpeta = tmp / "error escritura" / "prototipo"
    (carpeta / "marca-x.md").mkdir(parents=True)
    code, salida = run([marca, "crear", *opciones(), carpeta])
    if code != 2 or "Traceback" in salida or "marca-x.md" not in salida or "brand-x.json" not in salida:
        probs.append(f"con un error al escribir marca-x.md, sale con {code} (debe salir con 2, sin traza, y decir qué ficheros "
                     f"llegaron a escribirse):\n{salida[-600:]}")
    out.append(("marca.py crear sale con 2 y no escribe nada con un color mal escrito, un id no válido, un logo que no existe o "
                "la carpeta del plugin (también la de una copia sin plugin.json); con un error al escribir, sale con 2 y dice qué "
                "escribió", probs))

    # 5. web, sin red: qué es el mismo sitio y «logo» como palabra entera (las funciones de marca.py)
    probs = []
    try:
        import marca as m
        for a, b, esperado in (("https://www.x.es/", "https://estaticos.x.es/a.css", True),
                               ("https://www.abc.es/", "https://cdn.abc.es/a.css", True),
                               ("https://www.empresa.co.uk/", "https://estaticos.empresa.co.uk/a.css", True),
                               ("https://www.empresa.co.uk/", "https://otra.co.uk/a.css", False),
                               ("https://www.x.es/", "https://www.y.es/a.css", False),
                               ("http://127.0.0.1:8000/", "http://localhost:8000/a.css", True),
                               ("http://192.168.1.10/", "http://192.168.1.11/a.css", False)):
            if m.mismo_sitio(a, b) != esperado:
                probs.append(f"mismo_sitio({a}, {b}) da {not esperado}")
        for texto, esperado in (("logo", True), ("site-logo", True), ("header__logo", True), ("siteLogo", True), ("logoImg", True),
                                ("Logotipo de la empresa", True), ("logos", True), ("logout", False), ("catálogo", False),
                                ("blogger", False), ("Cerrar sesión", False)):
            if m.dice_logo(texto) != esperado:
                probs.append(f"dice_logo(«{texto}») da {not esperado}")
    except Exception as e:  # noqa: BLE001 (la prueba dice qué falta en lugar de pararse)
        probs.append(f"no se puede probar mismo_sitio() y dice_logo() de marca.py: {e!r}")
    out.append(("marca.py web, sin red: mismo sitio con x.es, abc.es, empresa.co.uk y localhost = 127.0.0.1, y «logo» como palabra "
                "entera (no «logout» ni «catálogo»)", probs))

    # 6. web contra la web ficticia, contra otra página de la misma empresa (logo SVG en línea, hoja servida como localhost
    # y un PDF), servidas aquí mismo en 127.0.0.1, y contra un puerto cerrado
    class Silencioso(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

    def servir(directorio):
        srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Silencioso, directory=str(directorio)))
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        return srv, f"http://127.0.0.1:{srv.server_address[1]}/"

    def web(url):
        """(código, JSON o None, salida de error o todo lo que sale si no hay JSON) de marca.py web."""
        r = subprocess.run([sys.executable, str(marca), "web", url], capture_output=True, text=True, encoding="utf-8", errors="replace")
        try:
            return r.returncode, json.loads(r.stdout), r.stderr
        except ValueError:
            return r.returncode, None, r.stdout + r.stderr
    srv, base = servir(WEB)
    try:
        code, d, err = web(base)
        code_css, d_css, err_css = web(base + "estilos.css")
    finally:
        srv.shutdown()
        srv.server_close()
    probs = []
    if d is None:
        probs.append(f"marca.py web no escribe un JSON (sale con {code}):\n{err[-600:]}")
    else:
        colores = d.get("colores") or []
        hexes = [c.get("hex") for c in colores]
        if any(c not in hexes[:3] for c in WEB_MARCA):
            probs.append(f"los colores de marca {', '.join(WEB_MARCA)} no están entre los tres primeros: {hexes[:5]}")
        if "#FFAABB" in hexes:
            probs.append("toma el selector #fab por un color")
        cielo = next((c for c in colores if c.get("hex") == "#5DA9E9"), {})
        if "--nb-cielo" not in (cielo.get("variables") or []):
            probs.append(f"#5DA9E9 no lleva su variable --nb-cielo: {cielo}")
        urls = [x.get("url") for x in d.get("logos") or []]
        if len(urls) != 2 or urls[0] != base + "logo.svg" or not str(urls[1]).startswith("data:image/svg+xml"):
            probs.append(f"logos tiene que traer el de la cabecera ({base}logo.svg) y, al final, el icono del sitio; nada más (el "
                         f"icono de «logout» no es un logo): {urls}")
        if (d.get("tipografias") or [None])[0] != "Nunito Sans":
            probs.append(f"la tipografía de la web es Nunito Sans y da {d.get('tipografias')}")
    hexes = [c.get("hex") for c in (d_css or {}).get("colores") or []]
    if code_css or d_css is None or any(c not in hexes for c in WEB_MARCA) or d_css.get("logos"):
        probs.append(f"con la URL de su hoja de estilo, sale con {code_css} y no da sus colores de marca ni logos vacíos:\n{err_css[-400:]}")

    extra = tmp / "web extra"
    extra.mkdir()
    srv, base_extra = servir(extra)
    (extra / "pagina.html").write_text(PAGINA_EXTRA.replace("{puerto}", str(srv.server_address[1])), encoding="utf-8")
    (extra / "otra.css").write_text(":root { --nb-mar: #2A9D8F; }\n.aviso { border-color: var(--nb-mar); }\n", encoding="utf-8")
    (extra / "documento.pdf").write_bytes(b"%PDF-1.4\n1 0 obj << /Type /Catalog >> endobj\ntrailer << /Root 1 0 R >>\n%%EOF\n")
    (extra / "imagen.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    try:
        code, d, err = web(base_extra + "pagina.html")
        code_pdf, _, err_pdf = web(base_extra + "documento.pdf")
        code_png, _, err_png = web(base_extra + "imagen.png")
    finally:
        srv.shutdown()
        srv.server_close()
    if d is None:
        probs.append(f"marca.py web no escribe un JSON con la otra página (sale con {code}):\n{err[-600:]}")
    else:
        logo = (d.get("logos") or [{}])[0]
        codigo = str(logo.get("svg") or "")
        if logo.get("url") != base_extra + "pagina.html#svg-1" or not (codigo.startswith("<svg") and codigo.endswith("</svg>")) \
                or 'aria-label="Nubarrón Mensajería"' not in codigo:
            probs.append(f"el logo SVG en línea de la cabecera no es el primero de logos, con url {base_extra}pagina.html#svg-1 y "
                         f"su código en svg: {logo}")
        if "#2A9D8F" not in [c.get("hex") for c in d.get("colores") or []]:
            probs.append(f"no lee la hoja servida como localhost (el mismo equipo que 127.0.0.1): {d.get('colores')}\n{err[-400:]}")
    if code_pdf != 2 or "PDF" not in err_pdf or "skill de PDF" not in err_pdf:
        probs.append(f"con un PDF sale con {code_pdf} (debe salir con 2, decir que es un PDF y que se lee con la skill de PDF):\n{err_pdf[-400:]}")
    if code_png != 2 or "image/png" not in err_png:
        probs.append(f"con una imagen sale con {code_png} (debe salir con 2 y decir que es image/png):\n{err_png[-400:]}")
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    cerrado = f"http://127.0.0.1:{s.getsockname()[1]}/"
    s.close()
    code, salida = run([marca, "web", cerrado])
    if code != 2 or cerrado.rstrip("/") not in salida:
        probs.append(f"contra un puerto cerrado sale con {code} (debe salir con 2 y decir la URL):\n{salida[-400:]}")
    out.append(("marca.py web: los dos colores de marca de la web ficticia entre los tres primeros, el logo de la cabecera el "
                "primero y el icono del sitio al final (sin «logout») y su tipografía; con la URL de la hoja, sus colores; el logo "
                "SVG en línea (#svg-1 y su código) y la hoja de localhost de otra página; con un PDF, una imagen o sin respuesta, sale con 2", probs))
    return out


# color calculado de las iniciales del avatar de la cabecera y su color propio (style), en el navegador
AVATAR = ("import sys; from pathlib import Path; sys.path.insert(0, sys.argv[1]); from entorno import sync_playwright, launch_browser\n"
          "with sync_playwright() as p:\n"
          "    b = launch_browser(p); pg = b.new_page()\n"
          "    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith(('file:', 'data:', 'blob:')) else r.abort())\n"
          "    pg.goto(Path(sys.argv[2]).resolve().as_uri()); pg.wait_for_function('window.PROTO && window.PROTO.ready')\n"
          "    print(pg.evaluate(\"() => { const a = document.querySelector('.site-user .avatar'); return a ? getComputedStyle(a).color + '|' + a.style.color : 'sin avatar'; }\"))\n"
          "    b.close()\n")


def avatares(built):
    """[(qué, problemas)] de las iniciales del avatar de la cabecera, en el navegador: con la marca estándar siguen con el
    oscuro del site, el color del CSS, sin color propio (el mismo texto que antes); con el realce #5B7FB5 (la marca
    redondeada: ni blanco ni casi negro llegan a 4,5:1 sobre él), en negro puro. None si no hay navegador."""
    oscuro = json.loads((ROOT / "assets" / "brand-appian.json").read_text(encoding="utf-8"))["site"]["backgroundColor"]
    casos = (("marca estándar: las iniciales del avatar de la cabecera siguen con el oscuro del site, como antes",
              next((html for _, html, spec in built if spec.name == "catalogo-patrones.json"), None),
              "rgb(%d, %d, %d)|" % tuple(int(oscuro[i:i + 2], 16) for i in (1, 3, 5))),
             ("realce #5B7FB5, en el que ni blanco ni casi negro llegan a 4,5:1: las iniciales del avatar, en negro puro",
              next((html for n, html, _ in built if n == "catálogo de patrones con la marca de marca.py redondeada"), None),
              "rgb(0, 0, 0)|rgb(0, 0, 0)"))
    out = []
    for que, html, esperado in casos:
        if html is None:
            out.append((que, ["no se construyó ese catálogo de patrones"]))
            continue
        code, salida = run(["-c", AVATAR, HERE, html])
        if code == 2:
            return None
        ultima = salida.splitlines()[-1] if salida else ""
        out.append((que, [] if code == 0 and ultima == esperado else
                    [f"esperaba «{esperado}» (color calculado|color propio) y sale ({code}):\n{salida[-400:]}"]))
    return out


def main():
    utf8_stdio()
    ok = True
    print(f"Python {sys.version.split()[0]} ({sys.executable})")
    if sys.version_info < (3, 9):
        print("✗ Hace falta Python 3.9 o superior")
        sys.exit(1)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        # el prototipo de prueba sale del análisis ficticio del analista (modelo.py), como en un proyecto
        prueba = tmp / "autorizaciones" / "app.json"
        code, out = run([AQUI / "datos" / "autorizaciones" / "generar_app.py", prueba])
        if code:
            ok = False
            print(f"✗ Generar el prototipo de prueba «autorizaciones» desde el análisis\n{out}")
        # las galerías (el catálogo del kit) se descubren solas
        galerias = [(f"galería «{p.parent.name}»", p) for p in sorted((ROOT / "galerias").glob("*/app.json"))]
        cases = [("catálogo de patrones", ROOT / "templates" / "catalogo-patrones.json"),
                 *([("prototipo de prueba «autorizaciones»", prueba)] if not code else []), *galerias]
        cat, funcs, probs = coverage()
        if probs:
            ok = False
            print(f"✗ Catálogo de Appian {cat['version']}: " + "; ".join(probs))
        else:
            print(f"✓ Catálogo de Appian {cat['version']}: {len(funcs)} componentes en schemas, runtime y galería")
        built = []  # (nombre, html, spec) de lo que se ha construido
        for name, spec in cases:
            html = tmp / (spec.parent.name + ".html")  # nombres únicos: templates, autorizaciones y una por galería
            code, out = run([HERE / "build.py", spec, "-o", html])
            if code == 0 and html.exists():
                print(f"✓ Validar y construir: {name}")
                built.append((name, html, spec))
            else:
                ok = False
                print(f"✗ Validar y construir: {name}\n{out}")
        for que, probs in brands(tmp, built) + marca_cliente(tmp, built):
            if probs:
                ok = False
                print(f"✗ Marca: {que}\n  " + "\n  ".join(probs))
            else:
                print(f"✓ Marca: {que}")
        # prueba de humo (clics y expresiones) y contraste en todo lo construido
        browser = True
        for name, html, spec in built:
            code, out = run([HERE / "smoke_test.py", html, spec])
            if code == 0:
                print(f"✓ Prueba de humo ({name}, Playwright + navegador): {out.splitlines()[0] if out else 'sin errores'}")
            elif code == 2:
                print("· Prueba de humo y contraste no disponibles (opcional):\n  " + out.replace("\n", "\n  "))
                browser = False
                break
            else:
                ok = False
                print(f"✗ Prueba de humo con errores ({name}):\n{out}")
        for name, html, spec in built if browser else []:
            # contraste WCAG 2.2 AA de lo que se ve (texto, marcadores de posición, bordes de campo, textos de gráficos)
            code, out = run([HERE / "contrast_audit.py", html, spec])
            last = out.splitlines()[-1] if out else ""
            if code == 0:
                print(f"✓ Contraste ({name}): {last.replace('Contraste: ', '')}")
            else:
                ok = False
                print(f"✗ Contraste ({name}):\n{out}")
        for que, probs in (avatares(built) or []) if browser else []:
            ok = ok and not probs
            print(f"✗ Cabecera: {que}\n  " + "\n  ".join(probs) if probs else f"✓ Cabecera: {que}")
    print("\nKit listo." if ok else "\nEl kit tiene errores: revisa los mensajes anteriores.")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
