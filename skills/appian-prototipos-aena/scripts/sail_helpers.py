"""Funciones auxiliares para escribir el app.json con la guía de diseño AENA (references/design-rules.md).

Uso en un generar_app.py:
    import sys; sys.path.insert(0, r"<KIT>/scripts")
    from sail_helpers import *

Cada función devuelve el dict del componente SAIL con los valores de la guía (SAIL Design System de Appian
adaptado a AENA); los **kw sobrescriben o añaden parámetros SAIL reales. Nada de lo que devuelven es exclusivo
del prototipo salvo los parámetros que empiezan por $.

Bloques (cuándo usar cada uno: references/bloques.md; galería: examples/bloques/):
  página ........ page_header, breadcrumbs, hero_header, filter_bar, side_nav, content_card, section_card, subsection,
                  action_banner, empty_state, link_all, inline_stats
  datos ......... key_facts, field_summary, kpi, kpi_strip, kpi_sparkline, kpi_progress, two_line, doc_line, milestone,
                  duration, stamp_steps, checklist, leaderboard, user_list
  listas/grids .. grid, gcol, gcol_num, gcol_link, tag, state_map, alert_icons, grid_with_detail, grid_with_selection,
                  drilldown, drill_link, chart_link, more_less, document_list, comments, dual_picklist, dynamic_inputs
  cards ......... cards_as_buttons, cards_as_info, call_to_action, choice_cards
  botones ....... primary, secondary, danger, tool_button, bl
  formularios ... txt, par, date, dd, upload, choice_cards, cols, ro
  IA ............ ai_agent_chat, ai_data_chat, ai_suggested, ai_side_pane, ai_toggle, ai_records_chat, ai_doc_chat,
                  ai_answer, ai_citation, ai_review_grid, ai_confidence_tag, match_quality, ai_notice, ai_feedback, AI_MAPS
  pantallas ..... dialog
"""
import json
from pathlib import Path

_BRAND = json.loads((Path(__file__).resolve().parent.parent / "assets" / "brand-aena.json").read_text(encoding="utf-8"))
PRIMARY = _BRAND["components"]["primaryButton"]["color"]   # botón principal de la marca (#90CE00)
GREEN = _BRAND["site"]["selectedPageHighlightColor"]        # verde AENA para barras decorativas
NAVY = _BRAND["palette"]["navy"]                            # azul marino (cabecera de registro, sidebar)
STATES = {k: v for k, v in _BRAND.get("states", {}).items() if isinstance(v, dict)}
BG = "TRANSPARENT"                                          # fondo de páginas con cards (gris claro en Appian)
REC = "rv!record"
HTML = lambda t: "".join(f"<p>{x}</p>" for x in t.split("\n\n"))  # a!styledTextEditorField guarda HTML


def _s(text):
    """Guía §11: los mensajes de una sola frase no llevan punto final."""
    if isinstance(text, str) and text.endswith(".") and not text.endswith("..") and ". " not in text.rstrip("."):
        return text[:-1]
    return text


# ------------------------------------------------------------------ página
def page_header(title, subtitle=None, buttons=None, crumbs=None, level="H1"):
    """Cabecera de página: (migas) + H1 + descripción de una línea + acción principal a la derecha."""
    left = ([breadcrumbs(crumbs, marginBelow="EVEN_LESS")] if crumbs else []) + [{"type": "a!headingField", "text": title, "size": "LARGE" if level == "H1" else "MEDIUM_PLUS", "headingTag": level, "marginBelow": "EVEN_LESS" if subtitle else "NONE"}]
    if subtitle:
        left.append({"type": "a!richTextDisplayField", "labelPosition": "COLLAPSED", "value": [{"type": "a!richTextItem", "text": subtitle, "color": "SECONDARY"}], "marginBelow": "NONE"})
    cl = [{"type": "a!columnLayout", "contents": left}]
    if buttons:
        cl.append({"type": "a!columnLayout", "width": "AUTO", "contents": [{"type": "a!buttonArrayLayout", "align": "END", "marginBelow": "NONE", "buttons": buttons if isinstance(buttons, list) else [buttons]}]})
    return {"type": "a!columnsLayout", "alignVertical": "MIDDLE", "marginBelow": "MORE", "columns": cl}


def content_card(contents, **kw):
    """Card de contenido sobre fondo gris: blanca, sombra, sin borde (borde o sombra, nunca ambos)."""
    c = {"type": "a!cardLayout", "style": "NONE", "showBorder": False, "showShadow": True, "shape": "SEMI_ROUNDED", "padding": "STANDARD", "contents": contents if isinstance(contents, list) else [contents]}
    c.update(kw); return c


def section_card(title, contents, card=None, **kw):
    """Título de sección H2 ENCIMA de la card (páginas con cards). card: parámetros extra de la card."""
    s = {"type": "a!sectionLayout", "label": title, "labelSize": "MEDIUM", "labelHeadingTag": "H2", "labelColor": "STANDARD", "marginBelow": "MORE",
         "contents": [content_card(contents, **(card or {}))]}
    s.update(kw); return s


def _upper(text):
    """Mayúsculas solo en el texto fijo (las expresiones {…} se dejan igual)."""
    import re
    return re.sub(r"(\{[^{}]*\})|([^{]+)", lambda m: m.group(1) or m.group(2).upper(), text)


def subsection(label, contents, **kw):
    """Subsección dentro de una card: SMALL, H3, gris, en mayúsculas."""
    s = {"type": "a!sectionLayout", "label": _upper(label), "labelSize": "SMALL", "labelHeadingTag": "H3", "labelColor": "SECONDARY", "marginBelow": "STANDARD", "contents": contents if isinstance(contents, list) else [contents]}
    s.update(kw); return s


def subsection_with_link(label, link_text, action, contents, icon="pencil", **kw):
    """Subsección con un enlace de acción a la derecha del título («Editar» en el paso de revisión de un asistente)."""
    head = {"type": "a!sideBySideLayout", "alignVertical": "MIDDLE", "marginBelow": "LESS", "items": [
        {"type": "a!sideBySideItem", "item": {"type": "a!headingField", "text": _upper(label), "size": "SMALL", "headingTag": "H3", "color": "SECONDARY", "fontWeight": "BOLD", "marginBelow": "NONE"}},
        {"type": "a!sideBySideItem", "width": "MINIMIZE", "item": {"type": "a!richTextDisplayField", "labelPosition": "COLLAPSED", "value": [
            {"type": "a!richTextIcon", "icon": icon, "color": "ACCENT"}, " ", {"type": "a!richTextItem", "text": link_text, "link": {"type": "a!dynamicLink", "$action": action}, "linkStyle": "STANDALONE", "style": "STRONG"}]}}]}
    out = [head] + (contents if isinstance(contents, list) else [contents])
    return {"type": "a!sectionLayout", "marginBelow": kw.pop("marginBelow", "MORE"), "contents": out, **kw}


def card(title, contents, **kw):
    """Compatibilidad con generadores anteriores: con título → section_card; sin título → content_card."""
    return section_card(title, contents, card=kw) if title else content_card(contents, **kw)


def action_banner(title, text=None, button=None, kind="WARN", icon=None, **kw):
    """Aviso que pide una acción, con el botón dentro (patrón Action Banner). kind: WARN, INFO, ERROR, SUCCESS."""
    bar = {"WARN": "WARN", "INFO": "INFO", "ERROR": "NEGATIVE", "SUCCESS": "POSITIVE"}[kind]
    ic = icon or {"WARN": "exclamation-triangle", "INFO": "info-circle", "ERROR": "exclamation-circle", "SUCCESS": "check-circle"}[kind]
    txtv = [{"type": "a!richTextItem", "text": _s(title), "style": "STRONG"}] + (["\n", _s(text)] if text else [])
    icol = {"WARN": "WARN", "INFO": "ACCENT", "ERROR": "NEGATIVE", "SUCCESS": "POSITIVE"}[kind]  # a!richTextIcon no admite INFO
    items = [{"type": "a!sideBySideItem", "width": "MINIMIZE", "item": {"type": "a!richTextDisplayField", "labelPosition": "COLLAPSED", "value": [{"type": "a!richTextIcon", "icon": ic, "color": icol, "size": "MEDIUM"}]}},
             {"type": "a!sideBySideItem", "item": {"type": "a!richTextDisplayField", "labelPosition": "COLLAPSED", "value": txtv}}]
    if button:
        items.append({"type": "a!sideBySideItem", "width": "MINIMIZE", "item": {"type": "a!buttonArrayLayout", "marginBelow": "NONE", "buttons": [button]}})
    c = {"type": "a!cardLayout", "style": kind, "showBorder": False, "padding": "STANDARD", "shape": "SEMI_ROUNDED", "decorativeBarPosition": "START", "decorativeBarColor": bar, "marginBelow": "STANDARD",
         "contents": [{"type": "a!sideBySideLayout", "alignVertical": "MIDDLE", "spacing": "STANDARD", "items": items}]}
    c.update(kw); return c


def empty_state(icon, title, text=None, button=None, **kw):
    """Estado vacío: card gris, icono centrado, mensaje, siguiente paso y acción."""
    val = [{"type": "a!richTextIcon", "icon": icon, "size": "LARGE", "color": "SECONDARY"}, "\n", {"type": "a!richTextItem", "text": title, "size": "MEDIUM_PLUS"}]
    if text: val += ["\n", {"type": "a!richTextItem", "text": _s(text), "color": "SECONDARY"}]
    cont = [{"type": "a!richTextDisplayField", "labelPosition": "COLLAPSED", "align": "CENTER", "value": val}]
    if button: cont.append({"type": "a!buttonArrayLayout", "align": "CENTER", "buttons": [button]})
    c = {"type": "a!cardLayout", "style": "STANDARD", "showBorder": False, "padding": "MORE", "shape": "SEMI_ROUNDED", "contents": cont}
    c.update(kw); return c


def link_all(label, action, icon="arrow-right", align="RIGHT"):
    """Enlace «Ver todos» al final de una lista corta."""
    return {"type": "a!richTextDisplayField", "labelPosition": "COLLAPSED", "align": align, "marginAbove": "LESS",
            "value": [{"type": "a!richTextItem", "text": label, "link": {"type": "a!dynamicLink", "$action": action}, "linkStyle": "STANDALONE", "style": "STRONG"}, " ", {"type": "a!richTextIcon", "icon": icon, "color": "ACCENT", "link": {"type": "a!dynamicLink", "$action": action}, "altText": label}]}


# ------------------------------------------------------------------ datos
def _dash(value):
    """Un valor que es una sola expresión {…} muestra «–» si está vacío (en SAIL: a!defaultValue(valor, "–"))."""
    if isinstance(value, str) and value.startswith("{") and value.endswith("}") and value.count("{") == 1 and "|dash" not in value:
        return value[:-1] + "|dash}"
    return value


def _label_value(label, value, size="MEDIUM", sub=None):
    val = [{"type": "a!richTextItem", "text": label, "color": "SECONDARY", "size": "SMALL"}, "\n", {"type": "a!richTextItem", "text": _dash(value), "size": size}]
    if sub: val += ["\n", {"type": "a!richTextItem", "text": sub, "color": "SECONDARY", "size": "SMALL"}]
    return {"type": "a!richTextDisplayField", "label": label, "labelPosition": "COLLAPSED", "value": val, "marginBelow": "NONE"}


def key_facts(items, extra=None, **kw):
    """Franja de datos clave: card con 3–6 datos en columnas con divisor. items: [(etiqueta, valor) | (etiqueta, componente)].
    extra: componentes debajo (hito del ciclo de vida, aviso)."""
    def cell(label, value):
        if isinstance(value, str):
            return [_label_value(label, value, "MEDIUM")]
        if label is None:
            return [value]
        # componente (tag, avatar...) con su etiqueta encima, del mismo estilo que el resto (no es un título: texto SECONDARY)
        return [{"type": "a!richTextDisplayField", "labelPosition": "COLLAPSED", "marginBelow": "EVEN_LESS", "value": [{"type": "a!richTextItem", "text": label, "color": "SECONDARY", "size": "SMALL"}]}, dict(value, marginBelow="NONE")]
    colsl = [{"type": "a!columnLayout", "contents": cell(label, value)} for label, value in items]
    cont = [{"type": "a!columnsLayout", "showDividers": True, "spacing": "SPARSE", "alignVertical": "TOP", "stackWhen": ["PHONE", "TABLET_PORTRAIT"], "columns": colsl, "marginBelow": "STANDARD" if extra else "NONE"}]
    if extra: cont += extra if isinstance(extra, list) else [extra]
    c = content_card(cont, marginBelow="MORE")
    c.update(kw); return c


def field_summary(pairs, columns=3):
    """Resumen de datos fácil de leer: etiqueta SECONDARY encima y valor grande, en 2–3 columnas.
    pairs: [(etiqueta, valor-expresión) | (etiqueta, valor, True=ancho completo)]."""
    out, row = [], []
    def flush():
        if row:
            out.append({"type": "a!columnsLayout", "marginBelow": "STANDARD", "columns": [{"type": "a!columnLayout", "contents": [x]} for x in row] + [{"type": "a!columnLayout", "contents": []} for _ in range(columns - len(row))]})
            row.clear()
    for p in pairs:
        label, value, wide = (p + (False,))[:3]
        cell = _label_value(label, value)
        if wide:
            flush(); out.append({**cell, "marginBelow": "STANDARD"})
        else:
            row.append(cell)
            if len(row) == columns: flush()
    flush()
    return out


def kpi(text, icon, value=None, secondary=None, sec_text=None, reverse=False, **kw):
    """KPI COMPACT. value: fijo ($value) o se calcula con data + primaryMeasure (kw). secondary: valor de comparación → tendencia."""
    k = {"type": "a!kpiField", "primaryText": text, "icon": icon, "template": "COMPACT", "iconColor": "SECONDARY"}
    if value is not None: k["$value"] = value
    if secondary is not None: k["$secondaryValue"] = secondary
    if sec_text: k["secondaryText"] = sec_text
    if reverse: k["trendColor"] = "REVERSE"
    k.update(kw); return k


def kpi_strip(kpis, **kw):
    """Franja de KPI: 2–4 KPI en UNA card con divisores, sombra y barra decorativa verde arriba."""
    return content_card([{"type": "a!columnsLayout", "showDividers": True, "spacing": "SPARSE", "stackWhen": ["PHONE", "TABLET_PORTRAIT"],
                          "columns": [{"type": "a!columnLayout", "contents": [k]} for k in kpis]}],
                        decorativeBarPosition="TOP", decorativeBarColor=GREEN, marginBelow="MORE", **kw)


def two_line(main, sub=None, link=None, strong=True):
    """Celda consolidada: línea principal (enlace opcional) + línea secundaria gris."""
    m = {"type": "a!richTextItem", "text": main}
    if strong: m["style"] = "STRONG"
    if link: m["link"] = link; m["linkStyle"] = "STANDALONE"
    val = [m] + (["\n", {"type": "a!richTextItem", "text": sub, "color": "SECONDARY", "size": "SMALL"}] if sub else [])
    return {"type": "a!richTextDisplayField", "labelPosition": "COLLAPSED", "value": val}


def doc_line(name, meta=None, action=None, icon="file-pdf-o"):
    """Línea de la lista de documentos: icono por tipo, nombre (enlace) y metadatos grises."""
    val = [{"type": "a!richTextIcon", "icon": icon, "color": "SECONDARY", "size": "MEDIUM"}, "  ",
           {"type": "a!richTextItem", "text": name, **({"link": {"type": "a!dynamicLink", "$action": action}, "linkStyle": "STANDALONE"} if action else {})}]
    if meta: val += ["\n", {"type": "a!richTextItem", "text": meta, "color": "SECONDARY", "size": "SMALL"}]
    return {"type": "a!richTextDisplayField", "labelPosition": "COLLAPSED", "marginBelow": "LESS", "value": val}


def milestone(steps, active_expr, **kw):
    m = {"type": "a!milestoneField", "labelPosition": "COLLAPSED", "steps": steps, "active": active_expr, "stepStyle": "LINE", "color": "ACCENT"}
    m.update(kw); return m


# ------------------------------------------------------------------ grids
def state_map(mapping, default="neutral", grid=False):
    """Mapa estado → color de tag con la paleta semántica. mapping: {"Vigente": "positivo", ...} → {"Vigente": "#E3EFD3", ...}.
    grid=True: versión para filas de un grid (máximo dos colores no neutros): solo «atencion» y «negativo» llevan color."""
    keep = {"atencion", "negativo"}
    m = {k: STATES[v if not grid or v in keep else "neutral"]["tag"] for k, v in mapping.items()}
    m["*"] = STATES[default]["tag"]
    return m


def tag(expr, mapname="estadoColor", size="SMALL"):
    return {"type": "a!tagField", "labelPosition": "COLLAPSED", "size": size, "tags": [{"type": "a!tagItem", "text": "{" + expr + "}", "backgroundColor": "{" + expr + f"|map:{mapname}" + "}"}]}


def gcol(label, value, **kw):
    c = {"type": "a!gridColumn", "label": label, "value": value}; c.update(kw); return c


def gcol_num(label, value, **kw):
    """Columna de cifras: alineada a la derecha."""
    return gcol(label, value, align="END", **kw)


def gcol_link(label, text, action, sub=None, **kw):
    """Primera columna: enlace a la ficha (y línea secundaria opcional)."""
    return gcol(label, two_line(text, sub, {"type": "a!dynamicLink", "$action": action}), **kw)


def alert_icons(items):
    """Columna de alertas: iconos con tooltip (caption). items: [(expresión showWhen, icono, texto, color)]."""
    val = []
    for when, ic, text, col in items:
        val.append({"type": "a!richTextIcon", "icon": ic, "color": col, "caption": text, "altText": text, "showWhen": when})
        val.append(" ")
    return {"type": "a!richTextDisplayField", "labelPosition": "COLLAPSED", "value": val}


def grid(data, flt, columns, empty, page_size=10, **kw):
    """Grid de solo lectura con la guía: LIGHT, sin sombreado, rowHeader en la 1.ª columna y vacío concreto."""
    g = {"type": "a!gridField", "labelPosition": "COLLAPSED", "data": data, "borderStyle": "LIGHT", "shadeAlternateRows": False, "spacing": "STANDARD",
         "pageSize": page_size, "rowHeader": 1, "emptyGridMessage": empty, "columns": columns}
    if flt: g["$filter"] = flt
    g.update(kw); return g


# ------------------------------------------------------------------ botones
def primary(label, action=None, icon=None, **kw):
    """Acción principal: SOLID verde AENA. Una por pantalla."""
    b = {"type": "a!buttonWidget", "label": label, "style": "SOLID", "color": PRIMARY}
    if icon: b["icon"] = icon
    if action: b["$action"] = action
    b.update(kw); return b


def secondary(label, action=None, icon=None, **kw):
    b = {"type": "a!buttonWidget", "label": label, "style": "OUTLINE", "color": "ACCENT"}
    if icon: b["icon"] = icon
    if action: b["$action"] = action
    b.update(kw); return b


def danger(label, action=None, confirm=None, icon=None, **kw):
    """Destructiva: GHOST + NEGATIVE, con confirmación (confirm = (cabecera, mensaje))."""
    b = {"type": "a!buttonWidget", "label": label, "style": "GHOST", "color": "NEGATIVE"}
    if icon: b["icon"] = icon
    if confirm: b["confirmHeader"], b["confirmMessage"] = confirm
    if action: b["$action"] = action
    b.update(kw); return b


def tool_button(label, action=None, icon=None, **kw):
    """Barra de herramientas (encima de un grid, dentro de una card): SMALL, OUTLINE, SECONDARY."""
    b = {"type": "a!buttonWidget", "label": label, "style": "OUTLINE", "color": "SECONDARY", "size": "SMALL"}
    if icon: b["icon"] = icon
    if action: b["$action"] = action
    b.update(kw); return b


def bl(prim, sec=None):
    return {"type": "a!buttonLayout", "primaryButtons": prim if isinstance(prim, list) else [prim], "secondaryButtons": sec or [secondary("Cancelar", {"close": True})]}


# ------------------------------------------------------------------ formularios
def ro(label, value, **kw):
    """Dato de solo lectura con etiqueta encima (resúmenes); usa labelPosition="ADJACENT" solo en listas cortas."""
    n = {"type": "a!textField", "label": label, "labelPosition": "ABOVE", "value": value, "readOnly": True}
    n.update(kw); return n


def cols(*items, widths=None, **kw):
    c = {"type": "a!columnsLayout", "columns": [{"type": "a!columnLayout", "contents": it if isinstance(it, list) else [it], **({"width": widths[k]} if widths else {})} for k, it in enumerate(items)]}
    c.update(kw); return c


def dd(label, opts, var, values=None, **kw):
    n = {"type": "a!dropdownField", "label": label, "placeholder": "Seleccione", "choiceLabels": opts, "choiceValues": values or opts, "value": var, "saveInto": var}
    n.update(kw); return n


def txt(label, var, **kw):
    n = {"type": "a!textField", "label": label, "value": var, "saveInto": var}; n.update(kw); return n


def par(label, var, **kw):
    n = {"type": "a!paragraphField", "label": label, "value": var, "saveInto": var, "height": "MEDIUM"}; n.update(kw); return n


def date(label, var, **kw):
    n = {"type": "a!dateField", "label": label, "value": var, "saveInto": var}; n.update(kw); return n


def upload(label, var, **kw):
    n = {"type": "a!fileUploadField", "label": label, "value": var, "saveInto": var}; n.update(kw); return n


def choice_cards(label, options, var, template="a!cardTemplateBarTextStacked", **kw):
    """Selección con cards (≤6 opciones con icono y explicación). options: [{"id", "texto", "detalle"?, "icono", "color"?}]."""
    tpl = {"type": template, "id": "fv!data.id", "primaryText": "{fv!data.texto}", "icon": "{fv!data.icono}"}
    if any(o.get("detalle") for o in options): tpl["secondaryText"] = "{fv!data.detalle}"
    if any(o.get("color") for o in options): tpl["iconColor"] = "{fv!data.color}"
    n = {"type": "a!cardChoiceField", "label": label, "data": options, "cardTemplate": tpl, "value": var, "saveInto": var, "maxSelections": 1}
    n.update(kw); return n


def link_right(items):
    """Enlaces de acción de una sección, alineados a la derecha («Nuevo comentario», «Cargar documentación»...). items: [(texto, $action o None, icono)]."""
    val = []
    for k, (label, action, icon) in enumerate(items):
        if k: val.append("     ")
        val += [{"type": "a!richTextIcon", "icon": icon, "color": "ACCENT"}, " ", {"type": "a!richTextItem", "text": label, "link": {"type": "a!dynamicLink", **({"$action": action} if action else {})}, "linkStyle": "STANDALONE", "style": "STRONG"}]
    return {"type": "a!richTextDisplayField", "labelPosition": "COLLAPSED", "align": "RIGHT", "marginBelow": "LESS", "value": val}


def seccion(sid, label, contents, abierta=False, **kw):
    """Sección plegable de un registro (úsala solo con motivo claro; las áreas 1:N van en vistas). ri!abrir = sid la abre."""
    s = {"type": "a!sectionLayout", "label": label, "labelSize": "SMALL", "labelHeadingTag": "H3", "labelColor": "SECONDARY", "isCollapsible": True,
         "isInitiallyCollapsed": ("and(a!isNotNullOrEmpty(ri!abrir), ri!abrir <> \"%s\")" % sid) if abierta else ("ri!abrir <> \"%s\"" % sid),
         "divider": "BELOW", "dividerColor": "SECONDARY", "marginBelow": "STANDARD", "contents": contents}
    s.update(kw); return s


def dfecha(field, real_field, prefix="fv!row"):
    """Fecha estimada en gris / real en negrita (planificaciones)."""
    return {"type": "a!richTextDisplayField", "value": [
        {"type": "a!richTextItem", "text": "{%s.%s|date}" % (prefix, field), "style": "STRONG", "showWhen": "%s.%s" % (prefix, real_field)},
        {"type": "a!richTextItem", "text": "{%s.%s|date}" % (prefix, field), "color": "SECONDARY", "showWhen": "not(%s.%s)" % (prefix, real_field)}]}


def si_no(expr):
    return "{%s|map:siNo}" % expr


def clean(o):
    if isinstance(o, list): return [clean(x) for x in o if x is not None]
    if isinstance(o, dict): return {k: clean(v) for k, v in o.items()}
    return o


# ------------------------------------------------------------------ pantallas
def dialog(sid, title, contents, buttons, req, ref, width="NARROW", openFrom=None, recordType=None, **kw):
    """Diálogo P07: formulario de una columna; el ancho del diálogo se ajusta al contenido."""
    d = {"id": sid, "title": title, "type": "dialog", "pattern": "P07", "req": req, "ref": ref,
         "interface": {"type": "a!formLayout", "titleBar": title, "contentsWidth": width, "contents": contents, "buttons": buttons}}
    if openFrom: d["openFrom"] = openFrom
    if recordType: d["recordType"] = recordType
    d.update(kw); return d


# ------------------------------------------------------------------ bloques (patrones de Appian, references/bloques.md)
def _rtd(value, **kw):
    n = {"type": "a!richTextDisplayField", "labelPosition": "COLLAPSED", "value": value if isinstance(value, list) else [value]}
    n.update(kw); return n


def _link(text, action=None, saves=None, **kw):
    """a!richTextItem con enlace: $action (navegación del prototipo) y/o saveInto real [(variable, valor)]."""
    lk = {"type": "a!dynamicLink"}
    if action: lk["$action"] = action
    if saves: lk["saveInto"] = [{"type": "a!save", "target": t, "value": v} for t, v in saves]
    it = {"type": "a!richTextItem", "text": text, "link": lk, "linkStyle": "STANDALONE"}
    it.update(kw); return it


def breadcrumbs(items, **kw):
    """Ruta de migas (jerarquía, nunca historial): [("Incidencias", {"goto": "incidencias"}), ..., "Actual"]."""
    val = []
    for k, it in enumerate(items):
        if k: val.append({"type": "a!richTextItem", "text": "  /  ", "color": "SECONDARY"})
        val.append(_link(it[0], it[1]) if isinstance(it, tuple) else {"type": "a!richTextItem", "text": it, "style": "STRONG"})
    return _rtd(val, marginBelow=kw.pop("marginBelow", "LESS"), **kw)


def filter_bar(filters, clear=None, **kw):
    """Barra de filtros de página: 2–4 filtros en columnas y «Borrar filtros» (clear: variables que vacía)."""
    colsl = [{"type": "a!columnLayout", "contents": [f]} for f in filters]
    if clear:
        colsl.append({"type": "a!columnLayout", "width": "AUTO", "contents": [_rtd([{"type": "a!richTextIcon", "icon": "times", "color": "ACCENT"}, " ", _link("Borrar filtros", saves=[(v, None) for v in clear], style="STRONG")], marginBelow="LESS")]})
    c = {"type": "a!columnsLayout", "alignVertical": "BOTTOM", "marginBelow": "STANDARD", "stackWhen": ["PHONE"], "columns": colsl}
    c.update(kw); return c


def hero_header(title, subtitle=None, stats=None, buttons=None, level="H1", **kw):
    """Cabecera «hero»: card del color de la barra del site con título (H1: sustituye a page_header), subtítulo,
    estadísticas en línea y acciones (una SOLID como máximo; las demás OUTLINE en blanco)."""
    left = [{"type": "a!headingField", "text": title, "size": "LARGE" if level == "H1" else "MEDIUM_PLUS", "headingTag": level, "color": "#FFFFFF", "marginBelow": "EVEN_LESS"}]
    if subtitle: left.append(_rtd({"type": "a!richTextItem", "text": _s(subtitle), "color": "#FFFFFF"}, marginBelow="STANDARD" if stats else "NONE"))
    if stats: left.append(inline_stats(stats, color="#FFFFFF"))
    cl = [{"type": "a!columnLayout", "contents": left}]
    if buttons: cl.append({"type": "a!columnLayout", "width": "AUTO", "contents": [{"type": "a!buttonArrayLayout", "align": "END", "marginBelow": "NONE", "buttons": buttons}]})
    c = {"type": "a!cardLayout", "style": NAVY, "showBorder": False, "shape": "SEMI_ROUNDED", "padding": "MORE", "marginBelow": "MORE",
         "contents": [{"type": "a!columnsLayout", "alignVertical": "MIDDLE", "columns": cl}]}
    c.update(kw); return c


def side_nav(items, var, content, width="NARROW", **kw):
    """Navegación lateral (patrón Navigation, variante ligera) para >6 secciones o etiquetas largas en 26.6
    (con 26.7+ usa a!tabLayout orientation VERTICAL). items: [(clave, texto, icono)]; content: componentes con showWhen var = clave."""
    nav = []
    for key, label, ic in items:
        on = '%s = "%s"' % (var, key)
        nav.append({"type": "a!cardLayout", "showBorder": False, "padding": "LESS", "marginBelow": "EVEN_LESS",
                    "style": "{if(%s, \"STANDARD\", \"TRANSPARENT\")}" % on, "decorativeBarPosition": "{if(%s, \"START\", \"NONE\")}" % on, "decorativeBarColor": "ACCENT",
                    "link": {"type": "a!dynamicLink", "saveInto": [{"type": "a!save", "target": var, "value": key}]}, "accessibilityText": "{if(%s, \"Sección actual\", \"\")}" % on,
                    "contents": [_rtd([{"type": "a!richTextIcon", "icon": ic, "color": "{if(%s, \"ACCENT\", \"SECONDARY\")}" % on}, "  ",
                                       {"type": "a!richTextItem", "text": label, "style": "{if(%s, \"STRONG\", \"PLAIN\")}" % on}])]})
    c = {"type": "a!columnsLayout", "spacing": "SPARSE", "stackWhen": ["PHONE"], "columns": [
        {"type": "a!columnLayout", "width": width, "contents": nav}, {"type": "a!columnLayout", "contents": content}]}
    c.update(kw); return c


def inline_stats(items, color=None, **kw):
    """Estadísticas en línea bajo un título: [(icono, valor, texto)] con el valor en negrita."""
    its = []
    for ic, value, text in items:
        v = [{"type": "a!richTextIcon", "icon": ic, "color": color or "SECONDARY"}, " ", {"type": "a!richTextItem", "text": value, "style": "STRONG", **({"color": color} if color else {})}, " ",
             {"type": "a!richTextItem", "text": text, "color": color or "SECONDARY"}]
        its.append({"type": "a!sideBySideItem", "width": "MINIMIZE", "item": _rtd(v)})
    s = {"type": "a!sideBySideLayout", "spacing": "SPARSE", "alignVertical": "MIDDLE", "marginBelow": "NONE", "items": its}
    s.update(kw); return s


def kpi_sparkline(text, value, cats, values, sec_text=None, icon=None, **kw):
    """KPI con minigráfico de tendencia (patrón KPI with Sparkline): KPI + línea MICRO."""
    k = kpi(text, icon, value, sec_text=sec_text)
    if not icon: k.pop("icon")
    chart = {"type": "a!lineChartField", "labelPosition": "COLLAPSED", "height": "MICRO", "categories": cats, "series": [{"type": "a!chartSeries", "label": text, "data": values, "color": "ACCENT"}],
             "accessibilityText": "Tendencia de %s: %s" % (text.lower(), ", ".join(str(v) for v in values))}
    s = {"type": "a!sideBySideLayout", "alignVertical": "MIDDLE", "items": [{"type": "a!sideBySideItem", "width": "1X", "item": k}, {"type": "a!sideBySideItem", "width": "1X", "item": chart}]}
    s.update(kw); return s


def kpi_progress(text, value, pct, icon, color="POSITIVE", sec_text=None, **kw):
    """KPI con barra de progreso (patrón KPI with Progress Bar): ADJACENT con icono en sello + barra THIN."""
    k = {"type": "a!kpiField", "primaryText": text, "$value": value, "icon": icon, "iconStyle": "STAMP", "template": "ADJACENT"}
    if sec_text: k["secondaryText"] = sec_text
    k.update(kw)
    return [k, {"type": "a!progressBarField", "labelPosition": "COLLAPSED", "percentage": pct, "style": "THIN", "color": color, "showPercentage": False, "accessibilityText": "%s: %s %%" % (text, pct)}]


def duration(start, end, days, late_when=None, late_text="Supera el plazo objetivo", goal=None, **kw):
    """Duración entre dos hitos (patrón Duration Display): fecha — días — fecha; con aviso si supera el objetivo
    y el objetivo debajo (goal: «Objetivo: 3 días»)."""
    mid = [{"type": "a!richTextItem", "text": days, "style": "STRONG"}]
    if late_when:
        mid += [" ", {"type": "a!richTextIcon", "icon": "exclamation-triangle", "color": "NEGATIVE", "caption": late_text, "altText": late_text, "showWhen": late_when}]
    if goal:
        mid += ["\n", {"type": "a!richTextItem", "text": goal, "size": "SMALL", "color": "SECONDARY"}]
    date = lambda d: {"type": "a!columnLayout", "width": "NARROW", "contents": [_rtd({"type": "a!richTextItem", "text": d, "size": "MEDIUM_PLUS", "color": "SECONDARY"}, align="CENTER")]}
    line = {"type": "a!columnLayout", "contents": [{"type": "a!horizontalLine", "weight": "MEDIUM", "color": "SECONDARY"}]}
    c = {"type": "a!columnsLayout", "alignVertical": "MIDDLE", "stackWhen": ["NEVER"], "spacing": "DENSE", "columns": [
        date(start), line, {"type": "a!columnLayout", "width": "NARROW", "contents": [_rtd(mid, align="CENTER")]}, line, date(end)]}
    c.update(kw); return c


def stamp_steps(steps, **kw):
    """Cómo funciona (patrón Stamp Steps): pasos numerados con título y explicación. steps: [(título, texto)]."""
    cards = [{"type": "a!cardLayout", "style": "NONE", "showBorder": False, "showShadow": True, "shape": "SEMI_ROUNDED", "padding": "STANDARD", "contents": [
        {"type": "a!stampField", "text": str(k + 1), "size": "SMALL", "backgroundColor": "ACCENT", "align": "CENTER", "marginBelow": "LESS", "accessibilityText": "Paso %d" % (k + 1)},
        _rtd([{"type": "a!richTextItem", "text": t, "style": "STRONG", "size": "MEDIUM"}, "\n", {"type": "a!richTextItem", "text": _s(d), "color": "SECONDARY"}], align="CENTER")]} for k, (t, d) in enumerate(steps)]
    c = {"type": "a!columnsLayout", "stackWhen": ["TABLET_PORTRAIT", "PHONE"], "marginBelow": "MORE", "columns": [{"type": "a!columnLayout", "contents": [cd]} for cd in cards]}
    c.update(kw); return c


def leaderboard(items, value_label=None, **kw):
    """Clasificación (patrón Leaderboard): [(nombre, valor, cambio)] con posición, avatar, valor y variación (+/−)."""
    rows = []
    for k, (name, value, change) in enumerate(items):
        up_ = not str(change).startswith("-")
        rows.append({"type": "a!sideBySideLayout", "alignVertical": "MIDDLE", "marginBelow": "LESS", "items": [
            {"type": "a!sideBySideItem", "width": "MINIMIZE", "item": _rtd({"type": "a!richTextItem", "text": str(k + 1), "style": "STRONG", "color": "SECONDARY"})},
            {"type": "a!sideBySideItem", "width": "MINIMIZE", "item": {"type": "a!imageField", "labelPosition": "COLLAPSED", "size": "TINY", "style": "AVATAR", "images": [{"type": "a!userImage", "user": name}]}},
            {"type": "a!sideBySideItem", "item": _rtd({"type": "a!richTextItem", "text": name, "style": "STRONG"})},
            {"type": "a!sideBySideItem", "width": "MINIMIZE", "item": _rtd([{"type": "a!richTextItem", "text": value, "size": "MEDIUM_PLUS", "style": "STRONG"}] + ([" ", {"type": "a!richTextItem", "text": value_label, "size": "SMALL", "color": "SECONDARY"}] if value_label else []) + ["\n",
                {"type": "a!richTextIcon", "icon": "caret-up" if up_ else "caret-down", "color": "POSITIVE" if up_ else "NEGATIVE"}, {"type": "a!richTextItem", "text": " " + str(change).lstrip("+-"), "size": "SMALL", "color": "POSITIVE" if up_ else "NEGATIVE"}], align="RIGHT")}]})
    s = {"type": "a!sectionLayout", "contents": rows, "marginBelow": "NONE"}
    s.update(kw); return s


def user_list(users, **kw):
    """Personas de un equipo (patrón User List): [(nombre, cargo)] con avatar, nombre y cargo; mejor que un grid para contactos."""
    rows = [{"type": "a!sideBySideLayout", "alignVertical": "MIDDLE", "marginBelow": "LESS", "items": [
        {"type": "a!sideBySideItem", "width": "MINIMIZE", "item": {"type": "a!imageField", "labelPosition": "COLLAPSED", "size": "TINY", "style": "AVATAR", "images": [{"type": "a!userImage", "user": n}]}},
        {"type": "a!sideBySideItem", "item": _rtd([{"type": "a!richTextItem", "text": n, "style": "STRONG"}, "\n", {"type": "a!richTextItem", "text": r, "color": "SECONDARY", "size": "SMALL"}])}]} for n, r in users]
    s = {"type": "a!sectionLayout", "contents": rows, "marginBelow": "NONE"}
    s.update(kw); return s


def comments(items_expr, author="fv!item.autor", when="fv!item.fecha", text="fv!item.texto", **kw):
    """Comentarios (patrón Comments): iniciales en sello, autor, fecha y texto, del más reciente al más antiguo."""
    f = {"type": "a!forEach", "items": items_expr, "expression": {"type": "a!sectionLayout", "marginBelow": "STANDARD", "contents": [
        {"type": "a!sideBySideLayout", "alignVertical": "TOP", "items": [
            {"type": "a!sideBySideItem", "width": "MINIMIZE", "item": {"type": "a!stampField", "text": "{%s|initials}" % author, "size": "TINY", "backgroundColor": "SECONDARY", "accessibilityText": "{%s}" % author}},
            {"type": "a!sideBySideItem", "item": _rtd([{"type": "a!richTextItem", "text": "{%s}" % author, "style": "STRONG"}, "  ", {"type": "a!richTextItem", "text": "{%s|datetime}" % when, "color": "SECONDARY", "size": "SMALL"}, "\n", "{%s}" % text])}]}]}}
    f.update(kw); return f


def document_list(items_expr, search_var=None, name="fv!item.nombre", meta="fv!item.meta", icon="fv!item.icono", action=None, flt=None, **kw):
    """Lista de documentos (patrón Document List): buscador, icono por tipo, nombre (enlace) y metadatos; separadas por líneas.
    flt: filtro de filas (p. ej. los documentos del registro: "fv!item.expedienteId = rv!record.id")."""
    out = []
    if search_var:
        out.append({"type": "a!textField", "label": "Buscar documentos", "labelPosition": "COLLAPSED", "placeholder": "Buscar por nombre", "value": search_var, "saveInto": search_var, "marginBelow": "STANDARD"})
    lk = {"type": "a!dynamicLink", **({"$action": action} if action else {})}
    row = {"type": "a!sectionLayout", "marginBelow": "NONE", "contents": [
        {"type": "a!sideBySideLayout", "alignVertical": "MIDDLE", "marginBelow": "LESS", "items": [
            {"type": "a!sideBySideItem", "width": "MINIMIZE", "item": _rtd({"type": "a!richTextIcon", "icon": "{%s}" % icon, "size": "LARGE", "color": "ACCENT"})},
            {"type": "a!sideBySideItem", "item": _rtd([{"type": "a!richTextItem", "text": "{%s}" % name, "style": "STRONG", "link": lk, "linkStyle": "STANDALONE"}, "\n", {"type": "a!richTextItem", "text": "{%s}" % meta, "color": "SECONDARY", "size": "SMALL"}])}]},
        {"type": "a!horizontalLine", "color": "SECONDARY", "marginBelow": "LESS", "showWhen": "not(fv!isLast)"}]}
    f = {"type": "a!forEach", "items": items_expr, "expression": row}
    conds = ([flt] if flt else []) + (["or(a!isNullOrEmpty(%s), search(%s, %s) > 0)" % (search_var, search_var, name)] if search_var else [])
    if conds: f["$filter"] = conds[0] if len(conds) == 1 else "and(%s)" % ", ".join(conds)
    out.append(f)
    s = {"type": "a!sectionLayout", "contents": out, "marginBelow": "NONE"}
    s.update(kw); return s


def checklist(items, **kw):
    """Lista de comprobación: [(texto, expresión «hecho»)] con icono de hecho o pendiente."""
    val = []
    for k, (text, done) in enumerate(items):
        if k: val.append("\n")
        val += [{"type": "a!richTextIcon", "icon": "check-circle", "color": "POSITIVE", "showWhen": done, "altText": "Hecho"},
                {"type": "a!richTextIcon", "icon": "circle-o", "color": "SECONDARY", "showWhen": "not(%s)" % done, "altText": "Pendiente"}, "  ", text]
    return _rtd(val, **kw)


def more_less(text_expr, var, id_expr="fv!row.id", limit=120):
    """Texto largo en un grid con «Más» / «Menos» (patrón More-Less Link). var: lista de filas desplegadas."""
    opened = "contains(%s, %s)" % (var, id_expr)
    long_ = "len(%s) > %d" % (text_expr, limit)
    return _rtd([{"type": "a!richTextItem", "text": "{%s}" % text_expr, "showWhen": "or(not(%s), %s)" % (long_, opened)},
                 {"type": "a!richTextItem", "text": "{left(%s, %d)}…" % (text_expr, limit), "showWhen": "and(%s, not(%s))" % (long_, opened)}, " ",
                 {**_link("Más", saves=[(var, "{append(%s, %s)}" % (var, id_expr))], style="STRONG"), "showWhen": "and(%s, not(%s))" % (long_, opened)},
                 {**_link("Menos", saves=[(var, "{difference(%s, %s)}" % (var, id_expr))], style="STRONG"), "showWhen": "and(%s, %s)" % (long_, opened)}])


def cards_as_buttons(items, **kw):
    """Opciones o navegación con destinos grandes (patrón Cards as Buttons): [(icono, título, texto, $action)]."""
    cards = [{"type": "a!cardLayout", "style": "NONE", "showBorder": False, "showShadow": True, "shape": "SEMI_ROUNDED", "padding": "MORE", "height": "SHORT",
              "link": {"type": "a!dynamicLink", "$action": act}, "accessibilityText": t, "contents": [
                  _rtd([{"type": "a!richTextIcon", "icon": ic, "size": "LARGE", "color": "ACCENT"}, "\n", {"type": "a!richTextItem", "text": t, "size": "MEDIUM", "style": "STRONG", "color": "ACCENT"}, "\n", {"type": "a!richTextItem", "text": _s(d), "color": "SECONDARY"}], align="CENTER")]}
             for ic, t, d, act in items]
    if len(cards) <= 4:  # pocas opciones: columnas iguales, que ocupan el ancho y siguen la rejilla de la página
        g = {"type": "a!columnsLayout", "marginBelow": "MORE", "stackWhen": ["PHONE", "TABLET_PORTRAIT"], "columns": [{"type": "a!columnLayout", "contents": [c]} for c in cards]}
    else:
        g = {"type": "a!cardGroupLayout", "labelPosition": "COLLAPSED", "cardWidth": "MEDIUM_PLUS", "spacing": "STANDARD", "cards": cards, "marginBelow": "MORE"}
    g.update(kw); return g


def cards_as_info(items, **kw):
    """Catálogo de opciones o servicios (patrón Cards as Info): [(icono, título, texto, etiqueta o None)] con sello de color suave."""
    cards = []
    for ic, t, d, tg in items:
        head = [{"type": "a!richTextItem", "text": t, "style": "STRONG", "size": "MEDIUM"}]
        cont = [{"type": "a!stampField", "icon": ic, "size": "SMALL", "backgroundColor": STATES["enCurso"]["tag"], "contentColor": "ACCENT", "align": "START", "marginBelow": "LESS"}, _rtd(head, marginBelow="EVEN_LESS")]
        if tg: cont.append({"type": "a!tagField", "labelPosition": "COLLAPSED", "size": "SMALL", "marginBelow": "EVEN_LESS", "tags": [{"type": "a!tagItem", "text": tg, "backgroundColor": STATES["neutral"]["tag"]}]})
        cont.append(_rtd({"type": "a!richTextItem", "text": _s(d), "color": "SECONDARY"}))
        cards.append({"type": "a!cardLayout", "style": "NONE", "showBorder": False, "showShadow": True, "shape": "SEMI_ROUNDED", "padding": "STANDARD", "contents": cont})
    g = {"type": "a!cardGroupLayout", "labelPosition": "COLLAPSED", "cardWidth": "MEDIUM_PLUS", "spacing": "STANDARD", "cards": cards, "marginBelow": "MORE"}
    g.update(kw); return g


def call_to_action(icon, title, text, button, **kw):
    """Página con una sola cosa que hacer (patrón Call to Action): centrada, con icono, título, texto y un botón SOLID grande."""
    center = [_rtd([{"type": "a!richTextIcon", "icon": icon, "size": "EXTRA_LARGE", "color": "ACCENT"}, "\n", {"type": "a!richTextItem", "text": title, "size": "LARGE", "style": "STRONG"}, "\n",
                    {"type": "a!richTextItem", "text": _s(text), "color": "SECONDARY"}], align="CENTER", marginBelow="MORE"),
              {"type": "a!buttonArrayLayout", "align": "CENTER", "buttons": [dict(button, size="LARGE")]}]
    c = {"type": "a!columnsLayout", "marginAbove": "EVEN_MORE", "columns": [{"type": "a!columnLayout", "contents": []}, {"type": "a!columnLayout", "width": "MEDIUM_PLUS", "contents": center}, {"type": "a!columnLayout", "contents": []}]}
    c.update(kw); return c


def grid_with_detail(data, sel_var, columns, detail, empty, hint="Seleccione una fila para ver el detalle", detail_width="MEDIUM_PLUS", flt=None, **kw):
    """Maestro-detalle en la misma página (patrón Grid With Detail): grid con resaltado de fila (una selección) y detalle al lado.
    sel_var empieza con una fila seleccionada; detail: componentes con fv!item (el registro seleccionado)."""
    g = grid(data, flt, columns, empty, page_size=kw.pop("page_size", 8), selectable=True, selectionStyle="ROW_HIGHLIGHT", maxSelections=1,
             selectionValue=sel_var, selectionSaveInto=sel_var)
    det = {"type": "a!forEach", "items": data, "$filter": "fv!item.id = index(%s, 1, null)" % sel_var, "expression": {"type": "a!sectionLayout", "marginBelow": "NONE", "contents": detail}}
    c = {"type": "a!columnsLayout", "stackWhen": ["PHONE", "TABLET_PORTRAIT"], "columns": [
        {"type": "a!columnLayout", "contents": [content_card([g])]},
        {"type": "a!columnLayout", "width": detail_width, "contents": [content_card([det, _rtd({"type": "a!richTextItem", "text": hint, "style": "EMPHASIS", "color": "SECONDARY"}, showWhen="a!isNullOrEmpty(%s)" % sel_var)])]}]}
    c.update(kw); return c


def drilldown(var, grid_block, detail, back_label="Volver a la lista", **kw):
    """Profundizar sustituyendo el grid por el detalle (patrón Drilldown): el grid guarda el id en var; «Volver» arriba a la izquierda."""
    back = _rtd([{"type": "a!richTextIcon", "icon": "arrow-left", "color": "ACCENT"}, " ", _link(back_label, saves=[(var, None)], style="STRONG")], marginBelow="STANDARD")
    s = {"type": "a!sectionLayout", "marginBelow": "NONE", "contents": [
        {"type": "a!sectionLayout", "showWhen": "a!isNullOrEmpty(%s)" % var, "marginBelow": "NONE", "contents": [grid_block]},
        {"type": "a!sectionLayout", "showWhen": "a!isNotNullOrEmpty(%s)" % var, "marginBelow": "NONE", "contents": [back] + (detail if isinstance(detail, list) else [detail])}]}
    s.update(kw); return s


def drill_link(text, var, id_expr="fv!row.id", sub=None):
    """Primera columna de un grid de drilldown: enlace que guarda el id de la fila."""
    return two_line(text, sub, {"type": "a!dynamicLink", "saveInto": [{"type": "a!save", "target": var, "value": "{%s}" % id_expr}]})


def chart_link(var, record_type, field):
    """Enlace de un gráfico de registros (config.link): guarda el valor de la agrupación pulsada (patrón Drilldown Report)."""
    return {"type": "a!dynamicLink", "saveInto": [{"type": "a!save", "target": var, "value": "{fv!selection[recordType!%s.fields.%s]}" % (record_type, field)}]}


def grid_with_selection(data, sel_var, columns, empty, label_expr, panel_title="Seleccionados", action=None, **kw):
    """Selección múltiple con panel de lo seleccionado (patrón Grid with Selection) y la acción sobre ellos."""
    g = grid(data, None, columns, empty, selectable=True, selectionStyle="CHECKBOX", selectionValue=sel_var, selectionSaveInto=sel_var)
    panel = [{"type": "a!headingField", "text": "%s ({count(%s)})" % (panel_title, sel_var), "size": "SMALL", "headingTag": "H3", "fontWeight": "BOLD", "marginBelow": "LESS"},
             {"type": "a!forEach", "items": data, "$filter": "contains(%s, fv!item.id)" % sel_var, "expression": _rtd([{"type": "a!richTextIcon", "icon": "check", "color": "ACCENT"}, " ", "{%s}" % label_expr], marginBelow="EVEN_LESS")},
             _rtd({"type": "a!richTextItem", "text": "Marque filas en la tabla", "style": "EMPHASIS", "color": "SECONDARY"}, showWhen="a!isNullOrEmpty(%s)" % sel_var)]
    if action: panel += [{"type": "a!horizontalLine", "color": "SECONDARY", "marginBelow": "STANDARD"}, {"type": "a!buttonArrayLayout", "marginBelow": "NONE", "buttons": [dict(action, disabled="a!isNullOrEmpty(%s)" % sel_var, width="FILL")]}]
    c = {"type": "a!columnsLayout", "stackWhen": ["PHONE", "TABLET_PORTRAIT"], "columns": [
        {"type": "a!columnLayout", "contents": [content_card([g])]}, {"type": "a!columnLayout", "width": "NARROW_PLUS", "contents": [content_card(panel)]}]}
    c.update(kw); return c


def dual_picklist(all_expr, sel_var, mark_l, mark_r, left="Disponibles", right="Seleccionados", **kw):
    """Mover elementos entre dos listas (patrón Dual Picklist): para listas medianas (cortas: casillas; muy largas: selector)."""
    avail = "difference(%s, %s)" % (all_expr, sel_var)
    def side(title, labels, mark):
        return content_card([{"type": "a!headingField", "text": "%s ({count(%s)})" % (title, labels), "size": "SMALL", "headingTag": "H3", "fontWeight": "BOLD", "marginBelow": "LESS"},
                             {"type": "a!checkboxField", "label": title, "labelPosition": "COLLAPSED", "choiceLabels": "{%s}" % labels, "choiceValues": "{%s}" % labels, "choiceStyle": "CARDS", "value": mark, "saveInto": mark}])
    btn = lambda label, ic, saves, dis: {"type": "a!buttonWidget", "label": label, "icon": ic, "style": "OUTLINE", "color": "SECONDARY", "size": "SMALL", "width": "FILL", "disabled": dis,
                                         "saveInto": [{"type": "a!save", "target": t, "value": v} for t, v in saves]}
    mid = [{"type": "a!richTextDisplayField", "labelPosition": "COLLAPSED", "value": [""], "marginBelow": "EVEN_MORE"}, {"type": "a!buttonArrayLayout", "buttons": [
        btn("Añadir", "angle-right", [(sel_var, "{append(%s, %s)}" % (sel_var, mark_l)), (mark_l, None)], "a!isNullOrEmpty(%s)" % mark_l),
        btn("Quitar", "angle-left", [(sel_var, "{difference(%s, %s)}" % (sel_var, mark_r)), (mark_r, None)], "a!isNullOrEmpty(%s)" % mark_r),
        btn("Quitar todos", "angle-double-left", [(sel_var, None), (mark_r, None)], "a!isNullOrEmpty(%s)" % sel_var)]}]
    c = {"type": "a!columnsLayout", "alignVertical": "TOP", "stackWhen": ["PHONE"], "columns": [
        {"type": "a!columnLayout", "contents": [side(left, avail, mark_l)]}, {"type": "a!columnLayout", "width": "NARROW", "contents": mid}, {"type": "a!columnLayout", "contents": [side(right, sel_var, mark_r)]}]}
    c.update(kw); return c


def dynamic_inputs(var, label, add_label="Añadir otro", placeholder=None, **kw):
    """Lista de valores de longitud variable (patrón Dynamic Inputs): un campo por valor, quitar (si hay más de uno) y añadir."""
    row = {"type": "a!sideBySideLayout", "alignVertical": "MIDDLE", "marginBelow": "LESS", "items": [
        {"type": "a!sideBySideItem", "item": {"type": "a!textField", "label": "%s {fv!index}" % label, "labelPosition": "COLLAPSED", "placeholder": placeholder, "value": "fv!item", "saveInto": "fv!item"}},
        {"type": "a!sideBySideItem", "width": "MINIMIZE", "item": _rtd({"type": "a!richTextIcon", "icon": "times-circle", "color": "SECONDARY", "size": "MEDIUM", "altText": "Quitar", "caption": "Quitar",
                                                                        "link": {"type": "a!dynamicLink", "saveInto": [{"type": "a!save", "target": var, "value": "{remove(%s, fv!index)}" % var}]}}, showWhen="count(%s) > 1" % var)}]}
    out = [{"type": "a!headingField", "text": label, "size": "SMALL", "headingTag": "H3", "fontWeight": "SEMI_BOLD", "marginBelow": "LESS"},
           {"type": "a!forEach", "items": var, "expression": row},
           _rtd([{"type": "a!richTextIcon", "icon": "plus", "color": "ACCENT"}, " ", _link(add_label, saves=[(var, "{append(%s, \"\")}" % var)], style="STRONG")])]
    s = {"type": "a!sectionLayout", "contents": out, "marginBelow": "STANDARD"}
    s.update(kw); return s


# ------------------------------------------------------------------ IA (references/design-rules.md §14)
AI_NOTICE = "Respuestas generadas con IA: compruébelas antes de usarlas"


def ai_notice(text=AI_NOTICE, **kw):
    """Aviso de fiabilidad junto a cualquier salida de IA (regla: el usuario verifica; la IA ayuda, no decide)."""
    n = {"type": "a!richTextDisplayField", "labelPosition": "COLLAPSED", "marginBelow": "LESS",
         "value": [{"type": "a!richTextIcon", "icon": "info-circle", "color": "SECONDARY"}, " ", {"type": "a!richTextItem", "text": text, "color": "SECONDARY", "size": "SMALL"}]}
    n.update(kw); return n


def ai_feedback(var, question="¿Le ha resultado útil?", **kw):
    """Valoración de una respuesta de IA (pulgar arriba/abajo) alrededor del componente de IA. var guarda "UTIL" / "NO_UTIL"."""
    def ic(icon, value, alt):
        return {"type": "a!richTextIcon", "icon": icon, "color": "{if(%s = \"%s\", \"ACCENT\", \"SECONDARY\")}" % (var, value), "size": "MEDIUM", "altText": alt, "caption": alt,
                "link": {"type": "a!dynamicLink", "saveInto": [{"type": "a!save", "target": var, "value": value}]}}
    n = {"type": "a!richTextDisplayField", "labelPosition": "COLLAPSED", "marginBelow": "NONE",
         "value": [{"type": "a!richTextItem", "text": question + "  ", "color": "SECONDARY", "size": "SMALL"}, ic("thumbs-o-up", "UTIL", "Útil"), "  ", ic("thumbs-o-down", "NO_UTIL", "No útil"),
                   {"type": "a!richTextItem", "text": "   Gracias por su valoración", "color": "SECONDARY", "size": "SMALL", "showWhen": "a!isNotNullOrEmpty(%s)" % var}]}
    n.update(kw); return n


def ai_agent_chat(title, agent, welcome, placeholder="Escriba su pregunta", inputs=None, outputs=None, height="FILL", **kw):
    """Chat con un agente de IA (a!agentChatField, 26.6): título contextual, bienvenida que explica qué puede hacer y
    placeholder concreto. outputs: lista de a!save con save!value.<salida> para rellenar campos que el usuario revisa y guarda.
    Con 26.7+: shape="SEMI_ROUNDED", showBorder=True si convive con otro contenido. Simulación: $messages, $replies, $sessions."""
    n = {"type": "a!agentChatField", "title": title, "agent": agent, "welcomeMessage": welcome, "placeholder": placeholder, "height": height}
    if inputs: n["inputs"] = inputs
    if outputs: n["outputsSaveInto"] = outputs
    n.update(kw); return n


def ai_suggested(question, icon="lightbulb-o", color="ACCENT"):
    """Pregunta sugerida del Data Fabric Chatbot (máx. 3, concretas y que el chat sepa responder)."""
    return {"type": "a!suggestedQuestion", "iconName": icon, "iconColor": color, "question": question}


def ai_data_chat(title, record_types, questions, placeholder=None, **kw):
    """Chat sobre los datos (a!dataFabricChatField): va SOLO en un a!pane mostrable/ocultable (ver ai_side_pane)."""
    n = {"type": "a!dataFabricChatField", "title": title, "recordTypes": record_types, "suggestedQuestions": [ai_suggested(*q) if isinstance(q, tuple) else ai_suggested(q) for q in questions]}
    if placeholder: n["placeholder"] = placeholder
    n.update(kw); return n


def ai_records_chat(label, record_type, identifier, initial, questions, **kw):
    """Chat sobre un registro (a!recordsChatField) para la vista resumen: mensaje inicial en español y hasta 3 preguntas."""
    n = {"type": "a!recordsChatField", "label": label, "labelPosition": "ABOVE", "recordType": record_type, "identifier": identifier,
         "initialMessage": initial, "suggestedQuestions": questions[:3], "height": "MEDIUM", "buttonStyle": "PRIMARY"}
    n.update(kw); return n


def ai_side_pane(main, chat, open_var, width="MEDIUM", **kw):
    """Página con panel de chat lateral: a!paneLayout con el contenido principal (AUTO) y el chat en un pane de ancho fijo que
    se muestra u oculta con open_var (botón «Asistente» en la cabecera del contenido, ver ai_toggle). Nada encima ni debajo del chat."""
    return {"type": "a!paneLayout", "panes": [
        {"type": "a!pane", "width": "AUTO", "backgroundColor": BG, "contents": main if isinstance(main, list) else [main]},
        {"type": "a!pane", "width": width, "padding": "NONE", "showWhen": open_var, "contents": [chat]}], **kw}


def ai_toggle(open_var, label="Asistente", icon="magic"):
    """Botón que abre y cierra el panel del asistente (herramienta: OUTLINE SMALL, no compite con la acción principal)."""
    return {"type": "a!buttonWidget", "label": "{if(%s, \"Ocultar asistente\", \"%s\")}" % (open_var, label), "icon": icon, "style": "OUTLINE", "color": "ACCENT", "size": "SMALL",
            "saveInto": [{"type": "a!save", "target": open_var, "value": "{not(%s)}" % open_var}]}


def ai_citation(page, quote, page_var, quote_var, doc=None):
    """Cita de la fuente bajo una respuesta: al pulsarla, el visor va a la página y resalta el texto (initialPageDisplay + highlightedText)."""
    label = ("%s · " % doc if doc else "") + "p. %s · «%s»" % (page, quote)
    return [{"type": "a!richTextIcon", "icon": "quote-left", "color": "SECONDARY"}, " ",
            {"type": "a!richTextItem", "text": label, "size": "SMALL", "linkStyle": "STANDALONE",
             "link": {"type": "a!dynamicLink", "saveInto": [{"type": "a!save", "target": page_var, "value": page}, {"type": "a!save", "target": quote_var, "value": quote}]}}]


def rt(text):
    """Texto con **negrita** → lista de a!richTextItem (STRONG); una lista se devuelve tal cual."""
    if not isinstance(text, str):
        return text
    import re
    out = []
    for k, part in enumerate(re.split(r"\*\*(.+?)\*\*", text)):
        if part:
            out.append({"type": "a!richTextItem", "text": part, "style": "STRONG"} if k % 2 else part)
    return out


def ai_answer(text, citations=None, feedback_var=None):
    """Contenido de un mensaje del asistente en a!chatField (a!chatMessage.messageContent): texto (admite **negrita**),
    fuentes y valoración."""
    cont = [{"type": "a!richTextDisplayField", "labelPosition": "COLLAPSED", "marginBelow": "LESS" if citations or feedback_var else "NONE", "value": rt(text)}]
    if citations:
        val = [{"type": "a!richTextItem", "text": "Fuentes: ", "color": "SECONDARY", "size": "SMALL", "style": "STRONG"}]
        for k, c in enumerate(citations):
            if k: val.append("   ")
            val += c
        cont.append({"type": "a!richTextDisplayField", "labelPosition": "COLLAPSED", "marginBelow": "LESS" if feedback_var else "NONE", "value": val})
    if feedback_var: cont.append(ai_feedback(feedback_var))
    return {"type": "a!cardLayout", "style": "STANDARD", "showBorder": False, "shape": "SEMI_ROUNDED", "padding": "STANDARD", "contents": cont}


def ai_doc_chat(title, doc_var, page_var, quote_var, messages, file_name, pages=6, content=None, replies=None, **kw):
    """Documento + chat (receta de Appian): chat a la izquierda y visor a la derecha que salta a la página de la cita y la resalta.
    messages: [("USER"|"ASSISTANT", texto o componente)]."""
    chat = {"type": "a!chatField", "title": title, "height": "EXTRA_TALL", "showBorder": True, "shape": "SEMI_ROUNDED", "placeholder": "Pregunte por el contenido del documento",
            "messages": [{"type": "a!chatMessage", "role": r, "messageContent": m} for r, m in messages]}
    if replies: chat["$replies"] = replies
    viewer = {"type": "a!documentViewerField", "label": file_name, "labelPosition": "COLLAPSED", "document": doc_var, "height": "TALL",
              "initialPageDisplay": page_var, "highlightedText": quote_var, "altText": file_name, "$fileName": file_name, "$pages": pages}
    if content: viewer["$content"] = content
    c = {"type": "a!columnsLayout", "columns": [{"type": "a!columnLayout", "width": "MEDIUM_PLUS", "contents": [chat, ai_notice(marginAbove="LESS")]}, {"type": "a!columnLayout", "contents": [viewer]}]}
    c.update(kw); return c


def match_quality(record_type, label="Coincidencia"):
    """Columna «Coincidencia» para grids con búsqueda inteligente: 3 círculos y texto cualitativo (nunca la puntuación numérica).
    Solo se ve cuando hay una búsqueda. Bandas orientativas de Appian: 1 exacta, ≥0,8 alta, ≥0,6 media, resto baja."""
    s = "fv!row[recordType!%s.searchResults.allSearchFields.similarityScore]" % record_type
    def dot(k):
        th = {1: 0, 2: 0.6, 3: 0.8}[k]
        return {"type": "a!richTextIcon", "icon": "{if(%s >= %s, \"circle\", \"circle-o\")}" % (s, th), "color": "{if(%s >= %s, \"ACCENT\", \"SECONDARY\")}" % (s, th), "size": "SMALL"}
    txt = "{if(%s >= 1, \"Exacta\", if(%s >= 0.8, \"Alta\", if(%s >= 0.6, \"Media\", \"Baja\")))}" % (s, s, s)
    has = "a!isNotNullOrEmpty(%s)" % s
    return gcol(label, {"type": "a!richTextDisplayField", "labelPosition": "COLLAPSED",
                        "value": [dict(dot(1), showWhen=has), dict(dot(2), showWhen=has), dict(dot(3), showWhen=has), "  ",
                                  {"type": "a!richTextItem", "text": txt, "color": "SECONDARY", "size": "SMALL", "showWhen": has},
                                  {"type": "a!richTextItem", "text": "–", "color": "SECONDARY", "showWhen": "not(%s)" % has}]},
                width="NARROW_PLUS", helpTooltip="Calidad de la coincidencia con la búsqueda")


def ai_confidence_tag(expr):
    """Tag de confianza de una sugerencia de IA: Alta (neutral), Media (neutral), Baja (atención). expr devuelve ALTA/MEDIA/BAJA."""
    return {"type": "a!tagField", "labelPosition": "COLLAPSED", "size": "SMALL", "tags": [{"type": "a!tagItem", "text": "{%s|map:confianzaTexto}" % expr, "backgroundColor": "{%s|map:confianzaColor}" % expr}]}


def ai_review_grid(var, source_page="fv!item.pagina", page_var=None, quote_var=None):
    """Revisión de datos sugeridos por IA (P12): campo, valor editable, origen (Sugerido por IA / Editado), confianza y
    casilla «Revisado» en los de confianza baja. Editar un valor lo marca como editado y revisado. var: lista de
    {campo, valor, confianza ALTA|MEDIA|BAJA, origen IA|EDITADO, revisado, pagina}. Guardar: disabled = contains(var.revisado, false).
    page_var/quote_var: «Página N» pasa a ser un enlace que lleva el visor de la fuente a esa página y resalta el valor."""
    pg = {"type": "a!richTextItem", "text": "Página {%s}" % source_page, "size": "SMALL", "color": "SECONDARY"}
    if page_var:
        pg = {"type": "a!richTextItem", "text": "Página {%s}" % source_page, "size": "SMALL", "linkStyle": "STANDALONE",
              "link": {"type": "a!dynamicLink", "saveInto": [{"type": "a!save", "target": page_var, "value": "{%s}" % source_page}] + ([{"type": "a!save", "target": quote_var, "value": "{fv!item.valor}"}] if quote_var else [])}}
    return {"type": "a!gridLayout", "label": "Datos sugeridos", "labelPosition": "COLLAPSED", "borderStyle": "LIGHT", "shadeAlternateRows": False,
            "headerCells": [{"type": "a!gridLayoutHeaderCell", "label": x} for x in ["Campo", "Valor", "Origen", "Confianza", "Revisado"]],
            "columnConfigs": [{"type": "a!gridLayoutColumnConfig", "width": w} if w else {"type": "a!gridLayoutColumnConfig"} for w in ["NARROW_PLUS", None, "NARROW_PLUS", "NARROW_PLUS", "NARROW_PLUS"]],
            "rows": [{"type": "a!forEach", "items": var, "expression": {"type": "a!gridRowLayout", "contents": [
                _rtd([{"type": "a!richTextItem", "text": "{fv!item.campo}", "style": "STRONG"}, "\n", pg]),
                {"type": "a!textField", "label": "{fv!item.campo}", "value": "fv!item.valor", "saveInto": ["fv!item.valor", {"type": "a!save", "target": "fv!item.origen", "value": "EDITADO"}, {"type": "a!save", "target": "fv!item.revisado", "value": True}]},
                {"type": "a!tagField", "size": "SMALL", "tags": [{"type": "a!tagItem", "text": "{fv!item.origen|map:origenTexto}", "backgroundColor": STATES["neutral"]["tag"]}]},
                ai_confidence_tag("fv!item.confianza"),
                {"type": "a!booleanCheckboxField", "choiceLabel": "Revisado", "value": "fv!item.revisado", "saveInto": "fv!item.revisado", "showWhen": "fv!item.confianza = \"BAJA\""}]}}]}


AI_MAPS = {"confianzaTexto": {"ALTA": "Confianza alta", "MEDIA": "Confianza media", "BAJA": "Confianza baja", "*": "Sin sugerencia"},
           "confianzaColor": {"ALTA": STATES["neutral"]["tag"], "MEDIA": STATES["neutral"]["tag"], "BAJA": STATES["atencion"]["tag"], "*": STATES["neutral"]["tag"]},
           "origenTexto": {"IA": "Sugerido por IA", "EDITADO": "Editado", "USUARIO": "Introducido", "*": "Sin valor"}}


# compatibilidad con generadores anteriores
def ojo():
    return {"type": "a!richTextDisplayField", "value": [{"type": "a!richTextIcon", "icon": "eye", "color": "ACCENT", "altText": "Ver detalle", "link": {"type": "a!dynamicLink"}}]}


def alerta_icon(expr="fv!row.alerta"):
    return {"type": "a!richTextDisplayField", "value": [{"type": "a!richTextIcon", "icon": "exclamation-circle", "color": "NEGATIVE", "size": "MEDIUM", "altText": "Con alerta", "caption": "Con alerta", "showWhen": expr}]}
