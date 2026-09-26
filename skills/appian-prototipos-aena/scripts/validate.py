#!/usr/bin/env python3
"""
Valida un app spec de prototipo contra los schemas SAIL (mismos que usa appian-sail-generator),
el catálogo de iconos de Appian, la integridad de navegación, las reglas del patrón de diseño,
la versión de Appian del cliente (app.appianVersion, schemas/appian-versions.json) y la guía UX
del SAIL Design System (avisos «UX · »).

Uso:  python3 validate.py app.json [--brand aena] [--quiet]
Sale con código 1 si hay errores. Los avisos no bloquean.
"""
import json, re, sys, argparse
from pathlib import Path
from entorno import utf8_stdio

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_FILES = ["layouts", "display-components", "input-components", "grid-components", "button-components", "chart-components"]
EXPR = re.compile(r"[{}!(]")
HEX = re.compile(r"^#[0-9A-Fa-f]{6}([0-9A-Fa-f]{2})?$")
ICON_KEYS = {"icon", "stampIcon", "labelIcon", "$icon"}
SCREEN_TYPES = {"page", "record", "form", "dialog"}
# Funciones SAIL que no se pintan solas: las consume su componente padre
SUBOBJECTS = {
    "a!richTextItem", "a!richTextIcon", "a!richTextBulletedList", "a!richTextNumberedList", "a!richTextListItem", "a!richTextImage",
    "a!tagItem", "a!dynamicLink", "a!recordLink", "a!safeLink", "a!startProcessLink", "a!documentDownloadLink", "a!recordActionItem",
    "a!chartSeries", "a!save", "a!headerTemplateSimple", "a!headerTemplateFull", "a!headerTemplateImage", "a!webImage", "a!documentImage",
    "a!userImage", "a!sortInfo", "a!measure", "a!grouping", "a!queryFilter", "a!queryLogicalExpression", "a!pagingInfo", "a!queryRecordType",
    "a!recordData", "a!relatedRecordData", "a!aggregationFields", "a!gridColumn", "a!columnLayout", "a!sideBySideItem", "a!tabItem",
    "a!wizardStep", "a!pane", "a!barOverlay", "a!columnOverlay", "a!fullOverlay", "a!colorSchemeCustom", "a!gridLayoutHeaderCell",
    "a!gridLayoutColumnConfig", "a!columnChartConfig", "a!barChartConfig", "a!lineChartConfig", "a!areaChartConfig", "a!pieChartConfig",
    "a!gaugeFraction", "a!gaugeIcon", "a!gaugePercentage", "a!chatMessage", "a!eventData",
    "a!sidebarTemplate", "a!cardTemplateTile", "a!cardTemplateBarTextJustified", "a!cardTemplateBarTextStacked",
    "a!chartReferenceLine", "a!validationMessage", "a!submitLink", "a!processTaskLink", "a!userRecordLink", "a!webVideo",
    "a!suggestedQuestion", "a!pageLink",
}


def _ext_files(spec_dir=None):
    """Extensiones del kit y, si existe, prototype-extensions.json junto al app.json (extensiones del proyecto), en ese orden."""
    files = [ROOT / "schemas" / "prototype-extensions.json"]
    if spec_dir and (Path(spec_dir) / "prototype-extensions.json").exists():
        files.append(Path(spec_dir) / "prototype-extensions.json")
    return [json.loads(f.read_text(encoding="utf-8")) for f in files]


def _entries(section):
    """Entradas de una sección de corrección, sin las claves de documentación ('_source'…)."""
    return [(k, v) for k, v in (section or {}).items() if not k.startswith("_")]


def load_catalog(spec_dir=None):
    comps = {}
    for f in SCHEMA_FILES:
        d = json.loads((ROOT / "schemas" / f"{f}-schema.json").read_text(encoding="utf-8"))
        shared = d.get("sharedParameters", {})
        for name, c in d["components"].items():
            params = {}
            for inh in c.get("inherits") or []:
                for k, v in shared.get(inh, {}).items():
                    if k != "description" and isinstance(v, dict):
                        params[k] = v
            for k in c.get("excludedParameters") or []:  # heredados que el componente no tiene (p. ej. placeholder en a!dateField)
                params.pop(k, None)
            params.update(c.get("parameters", {}))
            comps[name] = params
    # extensiones: componentes que faltan en los schemas y parámetros/valores nuevos confirmados en docs.appian.com.
    # Tras fusionar los componentes de cada fichero se aplican sus correcciones (removeParameters, restrictValues);
    # un fichero posterior (el del proyecto) puede volver a declarar lo retirado.
    for ext in _ext_files(spec_dir):
        for name, c in ext.get("components", {}).items():
            base = comps.setdefault(name, {})
            for pname, pdef in c.get("parameters", {}).items():
                merged = {**base.get(pname, {}), **pdef}
                if base.get(pname, {}).get("validValues") and pdef.get("validValues"):
                    merged["validValues"] = list(dict.fromkeys(base[pname]["validValues"] + pdef["validValues"]))
                base[pname] = merged
        for name, plist in _entries(ext.get("removeParameters")):  # no están en la firma de Appian: pasan a ser desconocidos
            for p in plist:
                comps.get(name, {}).pop(p, None)
        for key, vals in _entries(ext.get("restrictValues")):  # 'a!x.param': sustituye los valores válidos (los hex siguen si el parámetro los admite)
            name, p = key.rsplit(".", 1)
            if p in comps.get(name, {}):
                comps[name][p] = {**comps[name][p], "validValues": list(vals)}  # copia: los parámetros heredados se comparten entre componentes
    return comps


def load_not_in_appian(spec_dir=None):
    """Funciones que aceptaban los schemas pero no existen en Appian -> mensaje de error con la alternativa."""
    out = {}
    for ext in _ext_files(spec_dir):
        for name in ext.get("components", {}):  # declararla en un fichero posterior la rehabilita
            out.pop(name, None)
        out.update(_entries(ext.get("notInAppian")))
    return out


def load_versions():
    """Mapa de versiones de Appian (schemas/appian-versions.json): en qué versión aparece cada componente, parámetro o valor."""
    f = ROOT / "schemas" / "appian-versions.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {"default": "26.6"}


def vtuple(v):
    """'25.4' -> (25, 4), para comparar versiones numéricamente ('25.4' < '26.1'); None si no es una versión."""
    m = re.fullmatch(r"\s*(\d+)\.(\d+)(?:\.\d+)*\s*", str(v))
    return (int(m.group(1)), int(m.group(2))) if m else None


def load_icons():
    lines = (ROOT / "schemas" / "icon-aliases.md").read_text(encoding="utf-8").splitlines()
    return {l.strip() for l in lines if l.strip() and not l.startswith("#")}


def runtime_supported():
    js = (ROOT / "runtime" / "appian-kit.js").read_text(encoding="utf-8")
    return set(re.findall(r'R\["(a![A-Za-z]+)"\]\s*=', js))


class Report:
    def __init__(self):
        self.errors, self.warnings = [], []

    def err(self, where, msg):
        self.errors.append(f"ERROR  {where}: {msg}")

    def warn(self, where, msg):
        self.warnings.append(f"AVISO  {where}: {msg}")


def find_brand(brand_id, spec_dir=None):
    """brand-<id>.json junto al app.json (marca del proyecto) o en assets/ del kit. Devuelve (marca, carpeta de sus ficheros)."""
    for d in ([Path(spec_dir)] if spec_dir else []) + [ROOT / "assets"]:
        f = d / f"brand-{brand_id}.json"
        if f.exists():
            return json.loads(f.read_text(encoding="utf-8")), d
    print(f"No existe la marca «{brand_id}»: crea brand-{brand_id}.json junto al app.json "
          f"(o usa una de assets/: {', '.join(sorted(x.stem[6:] for x in (ROOT / 'assets').glob('brand-*.json')))})", file=sys.stderr)
    sys.exit(2)


def validate(spec, brand=None, spec_dir=None):
    comps, icons, supported = load_catalog(spec_dir), load_icons(), runtime_supported()
    not_in_appian, versions = load_not_in_appian(spec_dir), load_versions()
    rep = Report()
    # versión de Appian del cliente: lo que aparece en una versión posterior es error
    app = spec.get("app") if isinstance(spec.get("app"), dict) else {}
    declared = str(app.get("appianVersion") or versions.get("default", "26.6"))
    if vtuple(declared) is None:
        rep.warn("app.appianVersion", f"'{declared}' no es una versión de Appian (formato 25.4): se valida contra {versions.get('default', '26.6')}")
        declared = versions.get("default", "26.6")
    target = vtuple(declared)

    def newer(table, key):
        """Versión en la que aparece 'key' (components/parameters/values/placements) si es posterior a la declarada."""
        v = versions.get(table, {}).get(key)
        return v if v and vtuple(v) and vtuple(v) > target else None

    patterns = json.loads((ROOT / "templates" / "patterns.json").read_text(encoding="utf-8"))["patterns"]
    brand_hex = set()
    primary = None
    if brand:
        brand_hex = {v.upper() for v in brand.get("palette", {}).values() if isinstance(v, str) and v.startswith("#")}
        brand_hex |= {v.upper() for v in brand.get("components", {}).get("chartColorScheme", [])}
        # paleta semántica de estados (tags apagados y colores de icono)
        for st in (brand.get("states") or {}).values():
            if isinstance(st, dict):
                brand_hex |= {x.upper() for x in (st.get("tag"), st.get("enum")) if isinstance(x, str) and x.startswith("#")}
        primary = (brand.get("components", {}).get("primaryButton") or {}).get("color")

    screens = spec.get("screens", [])
    bad = [i for i, s in enumerate(screens) if not isinstance(s, dict)]
    for i in bad:
        rep.err(f"screens[{i}]", f"cada pantalla debe ser un objeto JSON; se encontró {type(screens[i]).__name__} (¿coma sobrante al generar el JSON?)")
    screens = [s for s in screens if isinstance(s, dict)]
    ids = [s.get("id") for s in screens]
    byid = {s.get("id"): s for s in screens}
    for i in set(x for x in ids if ids.count(x) > 1):
        rep.err("screens", f"id de pantalla duplicado '{i}'")
    datasets = spec.get("data", {})
    record_types = {d.get("recordType") for d in datasets.values() if isinstance(d, dict)}
    req_ids = {r["id"] for r in spec.get("requirements", [])}
    record_screens = {s.get("recordType") for s in screens if s.get("type") == "record"}

    def rows_of(d):
        return d.get("rows", []) if isinstance(d, dict) else d if isinstance(d, list) else []

    def check_target(where, sid, kind):
        m = re.fullmatch(r"\{(?:fv!row|fv!item|rv!record)\.(\w+)\}", str(sid))
        if m:  # destino dinámico: todos los valores de ese campo en los datos deben ser pantallas
            vals = {r.get(m.group(1)) for d in datasets.values() for r in rows_of(d) if isinstance(r, dict) and m.group(1) in r}
            if not vals:
                rep.warn(where, f"{kind} dinámico '{sid}': ningún dataset tiene el campo '{m.group(1)}'")
            for v in sorted(x for x in vals if x not in byid):
                rep.err(where, f"{kind} dinámico '{sid}' toma el valor '{v}', que no es una pantalla")
            return
        if sid not in byid:
            rep.err(where, f"{kind} apunta a una pantalla inexistente '{sid}'")

    def walk(node, where, parent_param=None, too_new=False):
        """too_new: un antecesor ya tiene error de versión; no se repite en su contenido (p. ej. cada a!tabItem)."""
        if isinstance(node, list):
            for i, n in enumerate(node):
                walk(n, f"{where}[{i}]", parent_param, too_new)
            return
        if not isinstance(node, dict):
            return
        t = node.get("type")
        if t is None:
            for k, v in node.items():
                if not k.startswith("$"):
                    walk(v, f"{where}.{k}", k, too_new)
            return
        here = f"{where}<{t}>"
        if t in not_in_appian:
            rep.err(here, f"{t} {not_in_appian[t]}")
        elif t not in comps:
            rep.err(here, f"'{t}' no es un componente SAIL conocido (revisa el nombre o schemas/)")
        else:
            ver = None if too_new else newer("components", t)
            if ver:
                rep.err(here, f"{t} requiere Appian {ver} (el prototipo declara {declared})")
                too_new = True
            params = comps[t]
            for k, v in node.items():
                if k == "type" or k.startswith("$"):
                    continue
                if k not in params:
                    rep.err(here, f"parámetro '{k}' no existe en {t}")
                    continue
                spec_p = params[k]
                vv = spec_p.get("validValues")
                if vv and isinstance(v, str) and not EXPR.search(v):
                    if v not in vv and not (spec_p.get("acceptsHexColors") and HEX.match(v)):
                        rep.err(here, f"{k}: \"{v}\" no es válido. Valores permitidos: {', '.join(map(str, vv))}{' o hex #RRGGBB' if spec_p.get('acceptsHexColors') else ''}")
                if isinstance(v, str) and HEX.match(v) and brand_hex and v[:7].upper() not in brand_hex:
                    rep.warn(here, f"{k}: color {v} fuera de la paleta de marca")
                ver = None if too_new else newer("parameters", f"{t}.{k}")
                if ver:
                    rep.err(here, f"{t}.{k} requiere Appian {ver} (el prototipo declara {declared})")
                for s in (v if isinstance(v, list) else [v]):
                    ver = newer("values", f"{t}.{k}={s}") if not too_new and isinstance(s, str) and not EXPR.search(s) else None
                    if ver:
                        rep.err(here, f"{t}.{k} \"{s}\" requiere Appian {ver} (el prototipo declara {declared})")
            if t not in supported and t not in SUBOBJECTS:
                rep.warn(here, f"{t} existe en SAIL pero el prototipo lo pinta como marcador")
        for k in ICON_KEYS:
            v = node.get(k)
            if isinstance(v, str) and not EXPR.search(v) and v not in icons:
                rep.err(here, f"icono '{v}' no existe en Appian (schemas/icon-aliases.md)")
        if t == "a!recordLink" and isinstance(node.get("recordType"), str):
            rt = node["recordType"].replace("recordType!", "").split(".")[0]
            if rt not in record_screens:
                rep.err(here, f"a!recordLink a '{rt}' sin pantalla de tipo record")
        if t in ("a!gridField",) and isinstance(node.get("data"), str) and node["data"].startswith("recordType!"):
            rt = node["data"].replace("recordType!", "").split(".")[0]
            if rt not in record_types:
                rep.err(here, f"data '{node['data']}' no tiene dataset de ejemplo en spec.data")
        # reglas de diseño (el recuento de botones SOLID por pantalla y el SOLID + NEGATIVE están en check_ux)
        if t == "a!buttonWidget" and node.get("style") == "SOLID" and primary:
            c = node.get("color", "ACCENT")
            if c not in (primary, "NEGATIVE") and not EXPR.search(str(c)):
                rep.warn(here, f"botón SOLID con color {c}: el patrón de marca usa {primary} para la acción principal (las destructivas van en GHOST + NEGATIVE)")
        if t in ("a!textField", "a!paragraphField", "a!dropdownField", "a!dateField", "a!integerField", "a!floatingPointField") and node.get("labelPosition") == "ADJACENT" and not node.get("readOnly"):
            rep.warn(here, "campo editable con labelPosition ADJACENT: el patrón usa ABOVE en formularios")
        act = node.get("$action")
        for a in (act if isinstance(act, list) else [act] if act else []):
            for kind in ("goto", "dialog"):
                if a.get(kind):
                    check_target(here, a[kind], f"$action.{kind}")
        for k, v in node.items():
            if k != "type" and not k.startswith("$"):
                walk(v, f"{here}.{k}", k, too_new)
            elif k in ("$template",):
                pass

    for s in screens:
        sid = s.get("id", "?")
        where = f"screen '{sid}'"
        st = s.get("type", "page")
        if st not in SCREEN_TYPES:
            rep.err(where, f"type '{st}' no válido ({', '.join(sorted(SCREEN_TYPES))})")
        pat = s.get("pattern")
        if not pat:
            rep.err(where, "falta 'pattern' (catálogo en templates/patterns.json)")
        elif pat not in patterns:
            rep.err(where, f"pattern '{pat}' no existe en el catálogo")
        else:
            p = patterns[pat]
            if st != p["screenType"]:
                rep.err(where, f"el patrón {pat} ({p['name']}) exige type '{p['screenType']}'")
            root = s.get("interface", {}).get("type") if st != "record" else None
            if st != "record" and root not in p["rootTypes"]:
                rep.err(where, f"el patrón {pat} exige como raíz {' o '.join(p['rootTypes'])} (encontrado {root})")
        for r in s.get("req", []) or []:
            if req_ids and r not in req_ids:
                rep.warn(where, f"requisito '{r}' no está en spec.requirements")
        if not s.get("req"):
            rep.warn(where, "pantalla sin requisitos asociados (req)")
        if st == "record":
            if s.get("recordType") not in record_types:
                rep.err(where, f"recordType '{s.get('recordType')}' sin dataset en spec.data")
            for i, v in enumerate(s.get("views", [])):
                walk(v.get("interface"), f"{where}.views[{i}]")
            walk(s.get("recordActions", []), f"{where}.recordActions")
            if s.get("breadcrumb", {}).get("goto"):
                check_target(where, s["breadcrumb"]["goto"], "breadcrumb")
        else:
            if not s.get("interface"):
                rep.err(where, "falta 'interface'")
            walk(s.get("interface"), where)
        if st == "dialog" and s.get("openFrom"):
            check_target(where, s["openFrom"], "openFrom")

    for i, p in enumerate(spec.get("site", {}).get("pages", [])):
        if p.get("screen"):
            check_target(f"site.pages[{i}]", p["screen"], "página del site")
        for x in p.get("includes", []) or []:
            if x not in byid:
                rep.warn(f"site.pages[{i}]", f"includes '{x}' no es una pantalla")
    if len(spec.get("site", {}).get("pages", [])) > 10:
        rep.err("site.pages", "Appian admite como máximo 10 páginas o grupos de primer nivel")
    for q in spec.get("openQuestions", []):
        if q.get("priority") and q["priority"] not in ("CRITICA", "IMPORTANTE", "MEJORA"):
            rep.err(f"openQuestions '{q.get('id')}'", f"priority '{q['priority']}' no válida (CRITICA, IMPORTANTE, MEJORA)")
        if q.get("screen") and q["screen"] not in byid:
            rep.warn(f"openQuestions '{q.get('id')}'", f"screen '{q['screen']}' no existe")
    for i, c in enumerate(spec.get("captures", [])):
        check_target(f"captures[{i}]", c.get("screen"), "captura")
    check_expressions(spec, rep)
    check_placement(spec, rep, newer, declared)
    covered = {r for s in screens for r in (s.get("req") or [])}
    for r in spec.get("requirements", []):
        if r["id"] not in covered and not r.get("outOfScope"):
            rep.warn("cobertura", f"requisito {r['id']} ({r.get('title', '')}) sin pantalla")
    check_ux(spec, rep)
    return rep


# ---------------------------------------------------------------------------
# Reglas de ubicación de componentes (Appian rechaza estas anidaciones en SAIL)
# Fuente: guías de la skill appian-sail-generator (layouts/*, components/*, 06-common-syntax-errors)
# ---------------------------------------------------------------------------
ROOT_ONLY = {"a!formLayout", "a!headerContentLayout", "a!wizardLayout", "a!paneLayout"}
LAYOUTS = {"a!cardLayout", "a!columnsLayout", "a!sectionLayout", "a!boxLayout", "a!tabLayout", "a!cardGroupLayout",
           "a!billboardLayout", "a!sideBySideLayout"} | ROOT_ONLY
INPUTS = {"a!textField", "a!paragraphField", "a!integerField", "a!floatingPointField", "a!dateField", "a!dateTimeField",
          "a!dropdownField", "a!multipleDropdownField", "a!radioButtonField", "a!checkboxField",
          "a!booleanCheckboxField", "a!toggleField", "a!pickerFieldUsers", "a!pickerFieldGroups", "a!pickerFieldUsersAndGroups",
          "a!pickerFieldRecords", "a!pickerFieldCustom", "a!pickerFieldDocuments", "a!pickerFieldFolders",
          "a!fileUploadField", "a!styledTextEditorField", "a!cardChoiceField", "a!encryptedTextField"}
RICH = {"a!richTextItem", "a!richTextIcon", "a!richTextBulletedList", "a!richTextNumberedList", "a!richTextListItem", "a!richTextImage"}
REFERENCE_LINE_CHARTS = ("a!columnChartField", "a!barChartField", "a!lineChartField", "a!areaChartField", "a!scatterChartField")
CARD_TEMPLATES = ("a!cardTemplateTile", "a!cardTemplateBarTextJustified", "a!cardTemplateBarTextStacked")
PARENT = {  # componente -> (tipo padre, parámetro) permitidos
    "a!buttonWidget": {("a!buttonArrayLayout", "buttons"), ("a!buttonLayout", "primaryButtons"), ("a!buttonLayout", "secondaryButtons"),
                       ("a!wizardLayout", "primaryButtons"), ("a!wizardLayout", "secondaryButtons")},
    "a!columnLayout": {("a!columnsLayout", "columns")},
    "a!sideBySideItem": {("a!sideBySideLayout", "items")},
    "a!tabItem": {("a!tabLayout", "tabs")},
    "a!wizardStep": {("a!wizardLayout", "steps")},
    "a!gridColumn": {("a!gridField", "columns")},
    "a!gridRowLayout": {("a!gridLayout", "rows")},
    "a!pane": {("a!paneLayout", "panes")},
    "a!tagItem": {("a!tagField", "tags")},
    # Sidebar_Template.html: plantilla de barra de título de un formulario o asistente
    "a!sidebarTemplate": {("a!formLayout", "titleBar"), ("a!wizardLayout", "titleBar")},
    # Chart_Reference_Line_Component.html: referenceLines de los gráficos de ejes (el de dispersión también la admite)
    "a!chartReferenceLine": {(c, "referenceLines") for c in REFERENCE_LINE_CHARTS},
    # card-choices-component.html: plantillas de a!cardChoiceField.cardTemplate
    **{t: {("a!cardChoiceField", "cardTemplate")} for t in CARD_TEMPLATES},
}
PANE_PARENTS = {("a!headerContentLayout", "contents"), ("a!formLayout", "contents")}  # Pane_Layout.html (en formulario desde 25.3)
GRID_CELL_OK = {"a!richTextDisplayField", "a!linkField", "a!tagField", "a!imageField", "a!progressBarField",
                "a!buttonArrayLayout", "a!recordActionField"}
# Grid_Column_Component.html (26.9): a!sideBySideLayout en el value de a!gridColumn para varios componentes (o varias imágenes)
# en una celda de a!gridField, desde la versión de placements 'a!sideBySideLayout@a!gridColumn.value' (appian-versions.json).
# Cada a!sideBySideItem de la celda solo admite GRID_CELL_OK y a!sideBySideLayout anidados. En a!gridLayout sigue sin admitirse.
GRID_CELL_SBS = "a!sideBySideLayout"


def check_placement(spec, rep, newer=None, declared=None):
    """newer(tabla, clave): versión posterior a la declarada en la que se admite una anidación (appian-versions.json)."""
    def visit(node, where, anc):
        """anc: lista de (tipo, parámetro) de los componentes antecesores, del más externo al más interno."""
        if isinstance(node, list):
            for i, n in enumerate(node):
                visit(n, f"{where}[{i}]", anc)
            return
        if not isinstance(node, dict):
            return
        t = node.get("type")
        if t is None:
            for k, v in node.items():
                if not k.startswith("$"):
                    visit(v, f"{where}.{k}", anc)
            return
        here = f"{where}<{t}>"
        if t == "a!forEach":  # transparente: la expresión ocupa el lugar del forEach
            visit(node.get("expression"), here + ".expression", anc)
            return
        parent = anc[-1] if anc else None
        types = [a[0] for a in anc]
        pane_ok = t == "a!paneLayout" and parent in PANE_PARENTS and len(anc) == 1
        if t in ROOT_ONLY and anc and not pane_ok:
            rep.err(here, f"{t} solo puede ser el layout raíz de la interfaz o ir en contents de a!formLayout/a!headerContentLayout"
                    if t == "a!paneLayout" else f"{t} solo puede ser el layout raíz de la interfaz (no se puede anidar)")
        ver = newer("placements", f"{t}@{parent[0]}.{parent[1]}") if newer and pane_ok else None
        if ver:
            rep.err(here, f"{t} dentro de {parent[0]}.{parent[1]} requiere Appian {ver} (el prototipo declara {declared})")
        if t in PARENT and parent not in PARENT[t]:
            ok = " o ".join(f"{p}.{q}" for p, q in sorted(PARENT[t]))
            rep.err(here, f"{t} solo puede ir dentro de {ok}")
        if t in RICH and not (anc and (parent[0] == "a!richTextDisplayField" or parent[0] in RICH)):
            rep.err(here, f"{t} solo puede ir dentro de a!richTextDisplayField")
        if parent == ("a!richTextDisplayField", "value") and t not in RICH:
            rep.err(here, f"{t} no puede ir en el value de a!richTextDisplayField (solo texto y a!richText…)")
        if parent == ("a!headerContentLayout", "header") and t not in ("a!cardLayout", "a!billboardLayout"):
            rep.err(here, "el header de a!headerContentLayout solo admite a!cardLayout o a!billboardLayout")
        column = parent == ("a!gridColumn", "value")
        in_cell = column or (parent == ("a!sideBySideItem", "item") and ("a!gridColumn", "value") in anc)  # side by side en una celda
        if parent == ("a!sideBySideItem", "item") and not in_cell and (t in LAYOUTS - {"a!sideBySideLayout"} or t in ("a!gridField", "a!gridLayout", "a!eventHistoryListField")):
            rep.err(here, f"{t} no se admite dentro de a!sideBySideItem (solo componentes y a!sideBySideLayout)")
        if in_cell and t not in GRID_CELL_OK:
            if t == GRID_CELL_SBS:
                ver = newer("placements", f"{t}@a!gridColumn.value") if newer and column else None  # los anidados ya van en uno
                if ver:
                    rep.err(here, f"{t} dentro de a!gridColumn.value requiere Appian {ver} (el prototipo declara {declared}): "
                                  "hasta entonces, un solo componente por celda")
            elif t in LAYOUTS or t in INPUTS:
                rep.err(here, f"{t} no se admite en una columna de a!gridField (usa a!gridLayout para edición)" if column else
                        f"{t} no se admite en un a!sideBySideItem de una celda de a!gridField (solo {', '.join(sorted(GRID_CELL_OK))} y {GRID_CELL_SBS})")
            else:
                rep.warn(here, f"{t} en una columna de a!gridField: Appian recomienda {', '.join(sorted(GRID_CELL_OK))}")
        if parent == ("a!gridRowLayout", "contents") and t in LAYOUTS:
            rep.err(here, f"{t} no se admite en las filas de a!gridLayout")
        if t == "a!tabLayout" and any(x in ("a!sideBySideLayout", "a!gridLayout", "a!gridField") for x in types):
            rep.err(here, "a!tabLayout no se puede anidar dentro de a!sideBySideLayout ni de un grid")
        for k, v in node.items():
            if k != "type" and not k.startswith("$"):
                visit(v, f"{here}.{k}", anc + [(t, k)])

    for s in [x for x in spec.get("screens", []) if isinstance(x, dict)]:
        where = f"screen '{s.get('id')}'"
        if s.get("type") == "record":
            for i, v in enumerate(s.get("views", [])):
                visit(v.get("interface"), f"{where}.views[{i}]", [])
            visit(s.get("recordActions", []), f"{where}.recordActions", [("a!recordActionField", "actions")])
        else:
            visit(s.get("interface"), where, [])


# ---------------------------------------------------------------------------
# Calidad UX: SAIL Design System de Appian (https://docs.appian.com/suite/help/26.6/sail/guidance.html)
# Avisos con el prefijo "UX · ", uno por nodo (sus problemas van juntos) o por pantalla; nunca bloquean.
# ---------------------------------------------------------------------------
UX = "UX · "
# ux-accessibility.html: etiqueta de sección -> H por defecto; heading-component.html: tamaño -> H por defecto
SECTION_TAG = {"LARGE_PLUS": "H1", "LARGE": "H1", "MEDIUM_PLUS": "H2", "MEDIUM": "H2", "SMALL": "H3", "EXTRA_SMALL": "H4"}
HEADING_TAG = {"LARGE_PLUS": "H1", "LARGE": "H2", "MEDIUM_PLUS": "H3", "MEDIUM": "H4", "SMALL": "H5", "EXTRA_SMALL": "H6"}
BIG_SECTION = {"MEDIUM", "MEDIUM_PLUS", "LARGE", "LARGE_PLUS"}
GREY_BG = {"TRANSPARENT", "#F4F5F7", "#F5F5F5", "#FAFAFC"}
WHITE_BG = {"WHITE", "#FFFFFF", "#FFF"}
CONTENT_CARD = {"NONE", "STANDARD", "#FFFFFF", "#FFF"}  # cards de contenido (blancas); las de color o esquema no se evalúan
_HCL = ("a!headerContentLayout", "contents")
CONTENT_CARD_PATHS = ([_HCL], [_HCL, ("a!columnsLayout", "columns"), ("a!columnLayout", "contents")],  # cards directas del contenido
                      [_HCL, ("a!cardGroupLayout", "cards")])
NUM_LABEL = re.compile(r"importe|total|n\.?º|número|cantidad|%", re.I)
NUM_FILTER = re.compile(r"\|\s*(eur|num|pct)\b")


def _nodes(node, where, anc=()):
    """Componentes SAIL en orden de documento: (nodo, ruta, antecesores). Antecesores = ((tipo, parámetro, nodo), …),
    del más externo al más interno. a!forEach es transparente (su expresión ocupa su lugar)."""
    if isinstance(node, list):
        for i, n in enumerate(node):
            yield from _nodes(n, f"{where}[{i}]", anc)
        return
    if not isinstance(node, dict):
        return
    t = node.get("type")
    if t is None:
        for k, v in node.items():
            if not k.startswith("$"):
                yield from _nodes(v, f"{where}.{k}", anc)
        return
    here = f"{where}<{t}>"
    if t == "a!forEach":
        yield from _nodes(node.get("expression"), here + ".expression", anc)
        return
    yield node, here, anc
    for k, v in node.items():
        if k != "type" and not k.startswith("$"):
            yield from _nodes(v, f"{here}.{k}", anc + ((t, k, node),))


def _solid_count(buttons):
    """Botones SOLID que se ven a la vez: los condicionados (showWhen) se asumen alternativos entre sí y cuentan como uno."""
    fixed = [b for b in buttons if "showWhen" not in b]
    return len(fixed) + (1 if len(buttons) > len(fixed) else 0)


def _has_border(n):
    return n.get("showBorder", True) is True  # por defecto true en a!cardLayout y a!boxLayout; una expresión no se evalúa


def _ux_interface(iface, where, screen_type, add):
    """Reglas de una interfaz (pantalla o vista de registro). add(ruta, mensaje) acumula los problemas por nodo.
    Devuelve las rutas de sus nodos en orden de documento (para emitir los avisos en ese orden)."""
    nodes = list(_nodes(iface, where))
    # desviación deliberada y justificada: "$uxIgnore": "motivo" en un nodo silencia sus avisos UX (el motivo queda en el spec)
    ignored = {p for n, p, a in nodes if n.get("$uxIgnore")}
    report = add
    add = lambda path, msg: None if path in ignored else report(path, msg)
    root = iface.get("type")
    in_ = lambda anc, t, p=None: any(a[0] == t and (p is None or a[1] == p) for a in anc)
    buttons = [(n, p, a) for n, p, a in nodes if n["type"] == "a!buttonWidget"]

    # --- botones (ux-buttons.html) ---
    solids = [(n, p, a) for n, p, a in buttons if n.get("style") == "SOLID"]
    groups = [solids]
    if root == "a!wizardLayout":  # por paso: sus contents + primaryButtons/secondaryButtons, comunes a todos (el kit añade Siguiente)
        by_step = {}
        for s in solids:
            by_step.setdefault(next((id(x[2]) for x in s[2] if x[0] == "a!wizardStep"), None), []).append(s)
        common = by_step.pop(None, [])
        groups = [common + g for g in by_step.values()] or [common]
    for g in groups:
        if _solid_count([n for n, p, a in g]) > 1:
            add(g[1][1], "más de un botón SOLID en la pantalla: la guía admite uno (el más frecuente); el resto OUTLINE")
            break
    for n, p, a in buttons:
        if n.get("style") == "SOLID" and n.get("color") == "NEGATIVE":
            add(p, "acción destructiva: usa style GHOST con color NEGATIVE (nunca SOLID)")
        if not n.get("label") and not n.get("accessibilityText"):
            add(p, "botón solo con icono sin accessibilityText: los lectores de pantalla no sabrán qué hace")

    # --- cards y boxes (ux-card-layout.html, ux-box-layout.html, ux-avoiding-clutter.html) ---
    for n, p, a in nodes:
        if n["type"] not in ("a!cardLayout", "a!boxLayout"):
            continue
        if n.get("showShadow") is True and _has_border(n):
            add(p, "borde y sombra a la vez: la guía usa borde sobre fondo blanco o sombra sobre fondo gris, nunca ambos")
        if _has_border(n) and (in_(a, "a!cardLayout") or in_(a, "a!boxLayout")):
            add(p, "cards anidadas con borde: la interior va sin borde (showBorder: false)")
    if root == "a!headerContentLayout":
        bg = str(iface.get("backgroundColor", "WHITE")).upper()
        for n, p, a in nodes:
            if n["type"] != "a!cardLayout":
                continue
            content = [x[:2] for x in a] in CONTENT_CARD_PATHS and str(n.get("style", "NONE")).upper() in CONTENT_CARD
            shadow, border = n.get("showShadow") is True, _has_border(n)
            if content and bg in GREY_BG and border and not shadow:
                add(p, "fondo gris: la card lleva sombra y sin borde (showShadow: true, showBorder: false)")
            elif content and bg in WHITE_BG and shadow and not border:
                add(p, "fondo blanco: la card lleva borde, sin sombra")
            first = n.get("contents")
            first = first[0] if isinstance(first, list) and first else first
            if (isinstance(first, dict) and first.get("type") == "a!sectionLayout" and first.get("label")
                    and first.get("labelSize", "MEDIUM") in BIG_SECTION and not in_(a, "a!headerContentLayout", "header")):
                add(p, "título de sección dentro de la card: en páginas con cards el título H2 va encima de la card "
                       "(y dentro, subsecciones SMALL/H3 en SECONDARY)")

    # --- jerarquía de títulos (page-titles.html, content-structure.html, ux-accessibility.html) ---
    h1 = []
    for n, p, a in nodes:
        if n["type"] == "a!sectionLayout" and n.get("label"):
            size, tag = n.get("labelSize", "MEDIUM"), n.get("labelHeadingTag")
            ok = {SECTION_TAG.get(size)}
        elif n["type"] == "a!headingField" and n.get("text"):
            size, tag = n.get("size", "MEDIUM_PLUS"), n.get("headingTag")
            ok = {SECTION_TAG.get(size), HEADING_TAG.get(size)}
            if in_(a, "a!headerContentLayout", "header") or in_(a, "a!formLayout", "titleBar") or in_(a, "a!wizardLayout", "titleBar"):
                ok.add("H1")  # barra de título (heading MEDIUM SEMI_BOLD como H1 en la guía de títulos de página)
        else:
            continue
        if size not in SECTION_TAG or (tag and EXPR.search(str(tag))):
            continue
        if tag and tag not in ok:
            add(p, f"jerarquía de títulos: tamaño {size} con {tag} (corresponde {' o '.join(sorted(x for x in ok if x))})")
        if (tag or (SECTION_TAG if n["type"] == "a!sectionLayout" else HEADING_TAG)[size]) == "H1":
            h1.append(p)
    if len(h1) > 1:
        add(h1[1], "más de un H1 en la pantalla: solo el título de la página es H1 (secciones H2, subsecciones H3)")

    # --- grids (ux-grids.html, tabular-data-display.html) ---
    grids = [(n, p) for n, p, a in nodes if n["type"] == "a!gridField"]
    for n, p in grids:
        if not n.get("emptyGridMessage"):
            add(p, "define emptyGridMessage (mensaje concreto de vacío)")
        if not n.get("rowHeader"):
            add(p, "define rowHeader (accesibilidad)")
        ps = n.get("pageSize")
        if (isinstance(ps, int) or (isinstance(ps, str) and ps.isdigit())) and int(ps) > 50:
            add(p, f"pageSize {ps}: la guía usa 5–10 junto a otro contenido, 25 si hay dudas y 50 como máximo")
    styles = [(str(n.get("borderStyle", "LIGHT")), str(n.get("spacing", "STANDARD"))) for n, p in grids]
    for (n, p), st in zip(grids, styles):
        if st != styles[0]:
            add(p, "misma densidad y estilo para todos los grids de la pantalla (borderStyle y spacing)")
            break
    for n, p, a in nodes:  # cifras a la derecha, salvo la primera columna (siempre a la izquierda); los editables, a la izquierda
        if n["type"] != "a!gridColumn" or not a or a[-1][:2] != ("a!gridField", "columns"):
            continue
        cols = a[-1][2].get("columns")
        if not isinstance(cols, list) or not cols or cols[0] is n:
            continue
        val = n.get("value")
        txt = " ".join(_strings(val, []))
        is_link = isinstance(val, dict) and val.get("type") in ("a!linkField", "a!recordLink")
        numeric = bool(NUM_FILTER.search(txt)) or (bool(NUM_LABEL.search(str(n.get("label") or ""))) and not is_link and "|date" not in txt)
        if numeric and n.get("align", "START") != "END":
            add(p, "cifras alineadas a la derecha (align END)")

    # --- navegación y estructura ---
    for n, p, a in nodes:
        t = n["type"]
        if t == "a!tabLayout" and isinstance(n.get("tabs"), list) and len(n["tabs"]) > 7:
            add(p, f"{len(n['tabs'])} pestañas: la guía admite 5–7 (agrupa contenido o usa secciones)")
        if t == "a!wizardLayout" and isinstance(n.get("steps"), list):
            k, style = len(n["steps"]), str(n.get("style", "DOT_VERTICAL"))
            if k > 5 and style.endswith("_HORIZONTAL"):
                add(p, f"más de 5 pasos ({k}): usa un estilo vertical")
            elif 1 <= k <= 2 and style != "MINIMAL":
                add(p, f"asistente de {k} paso(s): usa style MINIMAL")
        if t == "a!richTextItem" and n.get("color") == "ACCENT" and not n.get("link") \
                and not any(x[0] in ("a!richTextItem", "a!cardLayout") and x[2].get("link") for x in a):  # dentro de una card-enlace sí se lee como clicable
            add(p, "texto en color de acento sin enlace: se lee como clicable")
    siblings = {}  # secciones con título que comparten lista de contenidos
    for n, p, a in nodes:
        if n["type"] == "a!sectionLayout" and n.get("label") and a:
            siblings.setdefault((id(a[-1][2]), a[-1][1]), []).append((n, p))
    for g in siblings.values():
        coll = [p for n, p in g if n.get("isCollapsible") is True]
        if coll and len(coll) < len(g):
            add(coll[0], "no mezcles secciones plegables y fijas en el mismo nivel")
    # --- IA (design-rules.md §14; páginas de Appian de cada componente de chat y de la búsqueda inteligente) ---
    for n, p, a in nodes:
        t = n["type"]
        if t in ("a!dataFabricChatField", "a!recordsChatField") and in_(a, "a!sideBySideItem"):
            add(p, "chat de IA dentro de a!sideBySideLayout: Appian no lo admite; ponlo en una columna o en un panel")
        if t == "a!dataFabricChatField":
            pane = next((x for x in reversed(a) if x[0] == "a!pane"), None)
            if pane is None:
                add(p, "chat de datos fuera de un a!pane: va solo en un panel lateral que se muestra u oculta (ai_side_pane)")
            else:
                cont = pane[2].get("contents")
                cont = [c for c in (cont if isinstance(cont, list) else [cont]) if c is not None]
                if len(cont) > 1:
                    add(p, "chat de datos con otros componentes en su panel: va solo, sin nada encima ni debajo")
        if t in ("a!agentChatField", "a!dataFabricChatField") and n.get("debugMode") is True:
            add(p, "debugMode activado: solo para desarrollo; el usuario no debe ver entradas y salidas de herramientas")
        if t in ("a!agentChatField", "a!dataFabricChatField") and not n.get("title"):
            add(p, "chat de IA sin título: el de Appian por defecto está en inglés; pon uno contextual en español")
        if t == "a!agentChatField" and not n.get("welcomeMessage"):
            add(p, "chat del agente sin welcomeMessage: di en español qué puede hacer y con un ejemplo")
        if t == "a!recordsChatField" and not n.get("initialMessage"):
            add(p, "chat del registro sin initialMessage: el de Appian por defecto está en inglés")
        if t == "a!dataFabricChatField" and not n.get("suggestedQuestions"):
            add(p, "chat de datos sin preguntas sugeridas: añade hasta 3 concretas que sepa responder")
        if t == "a!gridField" and n.get("smartSearchType") and n.get("showSearchBox") is not True:
            add(p, "smartSearchType sin showSearchBox: la búsqueda inteligente usa la caja de búsqueda del grid")
        texts = []
        if t == "a!richTextItem":
            texts = [n.get("text")]
        elif t == "a!richTextDisplayField":
            texts = [x for x in (n.get("value") if isinstance(n.get("value"), list) else [n.get("value")]) if isinstance(x, str)]
        elif t in ("a!textField", "a!gridColumn"):
            texts = [n.get("value")]
        for x in [x for x in texts if isinstance(x, str)]:
            for m in re.findall(r"\{([^{}]*similarityScore[^{}]*)\}", str(x or "")):
                if not re.match(r"\s*(if|a!match|choose|displayvalue)\s*\(", m):
                    add(p, "puntuación de similitud visible: no muestres el número; ordena por relevancia o usa la calidad en palabras (match_quality)")
    if screen_type == "form" and root == "a!formLayout" and str(iface.get("contentsWidth", "")) in ("WIDE", "FULL"):
        # las tablas (grid editable o de solo lectura) y los layouts de columnas o paneles justifican el ancho
        if not any(n["type"] in ("a!paneLayout", "a!columnsLayout", "a!gridLayout", "a!gridField") for n, p, a in _nodes(iface.get("contents"), where)):
            add(where + f"<{root}>", "formulario simple: usa contentsWidth NARROW o MEDIUM (una columna estrecha)")
    return [p for n, p, a in nodes]


def check_ux(spec, rep):
    """Avisos de calidad UX según el SAIL Design System (prefijo 'UX · '). Uno por nodo, con todos sus problemas."""
    for s in [x for x in spec.get("screens", []) if isinstance(x, dict)]:
        where, st = f"screen '{s.get('id')}'", s.get("type", "page")
        issues, order = {}, [where]

        def add(path, msg):
            if msg not in issues.setdefault(path, []):
                issues[path].append(msg)
        if st == "record":
            views = s.get("views") or []
            if len(views) > 7:
                add(where, f"{len(views)} vistas de registro: la guía admite 5–7 pestañas")
            if len(s.get("recordActions") or []) > 3:
                add(where, "máximo 3 acciones de registro en la cabecera")
            for i, v in enumerate(views):
                if isinstance(v, dict) and isinstance(v.get("interface"), dict):
                    order += _ux_interface(v["interface"], f"{where}.views[{i}]", st, add)
        elif isinstance(s.get("interface"), dict):
            order += _ux_interface(s["interface"], where, st, add)
        pos = {p: i for i, p in enumerate(order)}
        for path in sorted(issues, key=lambda p: pos.get(p, len(pos))):
            rep.warn(path, UX + "; ".join(issues[path]))


def ux_summary(rep):
    """Resumen de una línea de los avisos UX."""
    ux = [w for w in rep.warnings if f": {UX}" in w]
    screens = {m.group(1) for w in ux for m in [re.search(r"screen '([^']*)'", w)] if m}
    return f"Calidad UX: {len(ux)} aviso(s) en {len(screens)} pantalla(s)" if ux else "Calidad UX: sin avisos"


FILTERS = {"date", "datetime", "eur", "num", "pct", "upper", "initials", "dash"}


def _keys(o, acc):
    if isinstance(o, dict):
        for k, v in o.items():
            acc.add(k)
            _keys(v, acc)
    elif isinstance(o, list):
        for v in o:
            _keys(v, acc)
    return acc


def _strings(o, out):
    if isinstance(o, str):
        out.append(o)
    elif isinstance(o, dict):
        for v in o.values():
            _strings(v, out)
    elif isinstance(o, list):
        for v in o:
            _strings(v, out)
    return out


def check_expressions(spec, rep):
    """Referencias dentro de expresiones: mapas, filtros, campos de datos y variables locales."""
    maps = set((spec.get("maps") or {}).keys())
    fields = set()
    for d in (spec.get("data") or {}).values():
        _keys(d.get("rows", d) if isinstance(d, dict) else d, fields)
    ds_fields = {}
    for d in (spec.get("data") or {}).values():
        if isinstance(d, dict) and d.get("recordType"):
            ds_fields[d["recordType"]] = _keys(d.get("rows", []), set())
    glob_vars = {k.split("!", 1)[1] for k in (spec.get("state") or {})}
    for s in [x for x in spec.get("screens", []) if isinstance(x, dict)]:
        where = f"screen '{s.get('id')}'"
        local_obj = s.get("local") or {}
        _keys(local_obj, fields)
        local_vars = {k.split("!", 1)[1] for k in local_obj} | glob_vars
        rec_fields = ds_fields.get(s.get("recordType"), fields)
        seen = set()
        for txt in _strings({k: v for k, v in s.items() if k not in ("id", "title_", "req", "assumptions")}, []):
            for m in re.finditer(r"\|\s*map:(\w+)", txt):
                if m.group(1) not in maps and ("map", m.group(1)) not in seen:
                    seen.add(("map", m.group(1)))
                    rep.err(where, f"mapa '{m.group(1)}' no definido en spec.maps")
            for m in re.finditer(r"\{[^{}]*\|\s*([a-z]+)(?![\w:])", txt):
                if m.group(1) not in FILTERS and ("f", m.group(1)) not in seen:
                    seen.add(("f", m.group(1)))
                    rep.err(where, f"filtro '|{m.group(1)}' no existe (usa: {', '.join(sorted(FILTERS))}, map:<nombre>)")
            for m in re.finditer(r"\bfv!(?:row|item)\.(\w+)", txt):
                if m.group(1) not in fields and ("fv", m.group(1)) not in seen:
                    seen.add(("fv", m.group(1)))
                    rep.warn(where, f"fv!…{m.group(1)}: ningún dataset ni variable local tiene ese campo")
            for m in re.finditer(r"\brv!record\.(\w+)", txt):
                if m.group(1) not in rec_fields and ("rv", m.group(1)) not in seen:
                    seen.add(("rv", m.group(1)))
                    rep.warn(where, f"rv!record.{m.group(1)}: el dataset de {s.get('recordType') or 'la pantalla'} no tiene ese campo")
            for m in re.finditer(r"\blocal!(\w+)", txt):
                if m.group(1) not in local_vars and ("l", m.group(1)) not in seen:
                    seen.add(("l", m.group(1)))
                    rep.warn(where, f"local!{m.group(1)} no está declarada en 'local' de la pantalla")


def display_title(s):
    t = s.get("title", s.get("id", ""))
    if "{" in t:
        return f"Ficha de {s['recordType']}" if s.get("recordType") and s.get("type") == "record" else re.sub(r"\{[^}]*\}", "…", t)
    return t


def trace_markdown(spec):
    screens = spec.get("screens", [])
    out = [f"# Trazabilidad del prototipo · {spec.get('app', {}).get('name', '')}", ""]
    if spec.get("app", {}).get("source"):
        out += [f"Fuente: {spec['app']['source']}", ""]
    out += ["## Requisitos → pantallas", "", "| Requisito | Descripción | Pantallas |", "|---|---|---|"]
    for r in spec.get("requirements", []):
        cov = [display_title(s) for s in screens if r["id"] in (s.get("req") or [])]
        cell = ", ".join(cov) if cov else (f"_Fuera del prototipo: {r['outOfScope']}_" if r.get("outOfScope") else "**SIN PANTALLA**")
        out.append(f"| {r['id']} | {r.get('title', '')} | {cell} |")
    out += ["", "## Inventario de pantallas", "", "| Id | Pantalla | Tipo | Patrón | Requisitos | Referencia en el documento |", "|---|---|---|---|---|---|"]
    for s in screens:
        out.append(f"| {s['id']} | {display_title(s)} | {s.get('type', 'page')} | {s.get('pattern', '')} | {', '.join(s.get('req') or []) or '—'} | {s.get('ref', '—')} |")
    qs = spec.get("openQuestions", [])
    if qs:
        pri = {"CRITICA": ("🔴", 0), "IMPORTANTE": ("🟡", 1), "MEJORA": ("🟢", 2)}
        qs = sorted(qs, key=lambda q: pri.get(q.get("priority"), ("", 3))[1])
        out += ["", "## Preguntas abiertas para el cliente", ""]
        out += [f"- {pri.get(q.get('priority'), ('',))[0]} **{q['id']}** {q['text']}".replace("-  **", "- **") + (f" _(pantalla: {q['screen']})_" if q.get("screen") else "") for q in qs]
    asum = []

    def walk(o, s):
        if isinstance(o, dict):
            if o.get("$assumption"):
                asum.append((s, o["$assumption"]))
            for v in o.values():
                walk(v, s)
        elif isinstance(o, list):
            for v in o:
                walk(v, s)
    for s in screens:
        for a in s.get("assumptions", []) or []:
            asum.append((s, a))
        walk(s.get("interface") or s.get("views"), s)
    if asum:
        out += ["", "## Supuestos a validar", ""]
        out += [f"- {a} _(pantalla: {display_title(s)})_" for s, a in asum]
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--brand", default="aena")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    utf8_stdio()
    spec = json.loads(Path(a.spec).read_text(encoding="utf-8"))
    spec_dir = Path(a.spec).resolve().parent
    brand, _ = find_brand(a.brand, spec_dir)
    rep = validate(spec, brand, spec_dir)
    for line in rep.errors + ([] if a.quiet else rep.warnings):
        print(line)
    print(f"\n{len(rep.errors)} error(es), {len(rep.warnings)} aviso(s)")
    print(ux_summary(rep))
    sys.exit(1 if rep.errors else 0)


if __name__ == "__main__":
    main()
