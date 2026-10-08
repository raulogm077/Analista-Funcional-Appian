"""Funciones auxiliares para escribir el app.json con la guía de diseño (references/design-rules.md).

Uso en un generar_app.py:
    import sys; sys.path.insert(0, r"<KIT>/scripts")
    from sail_helpers import *
Con la marca del proyecto (brand-<id>.json junto al app.json, en <p>/prototipo/), antes de esa línea:
    import sail_helpers; sail_helpers.usar_marca("<id>", r"<p>/prototipo")
Sin usar_marca(), los colores son los de la marca estándar de Appian (assets/brand-appian.json).

Cada función devuelve el dict del componente SAIL con los valores de la guía (SAIL Design System de Appian);
los **kw sobrescriben o añaden parámetros SAIL reales. Nada de lo que devuelven es exclusivo
del prototipo salvo los parámetros que empiezan por $.

Bloques (cuándo usar cada uno: references/bloques.md; galería: galerias/bloques/):
  página ........ page_header, breadcrumbs, hero_header, filter_bar, side_nav, content_card, section_card, subsection,
                  action_banner, empty_state, link_all, inline_stats
  datos ......... key_facts, field_summary, kpi, kpi_strip, kpi_sparkline, kpi_progress, two_line, doc_line, milestone,
                  duration, stamp_steps, checklist, leaderboard, user_list
  listas/grids .. grid, gcol, gcol_num, gcol_link, tag, state_map, alert_icons, grid_with_detail, grid_with_selection,
                  drilldown, drill_link, chart_link, chart_table, more_less, document_list, comments, dual_picklist, dynamic_inputs
  cards ......... cards_as_buttons, cards_as_info, call_to_action, choice_cards
  botones ....... primary, secondary, danger, tool_button, bl
  formularios ... txt, par, date, dd, upload, choice_cards, cols, ro
  IA ............ ai_agent_chat, ai_data_chat, ai_suggested, ai_side_pane, ai_toggle, ai_records_chat, ai_doc_chat,
                  ai_answer, ai_citation, ai_review_grid, ai_review_validation, ai_confidence_tag, match_quality, ai_notice, ai_feedback, AI_MAPS
  patrones 26.9 . calendar_month, calendar_week, event_maps, comment_thread, ATTACH_MAPS, kanban, KANBAN_STATES
  color ......... state_chart_colors (gráfico con el color de cada estado), CHART (series en orden), NAVY (oscuro de la
                  marca), GREEN (resaltado de la marca), STATES; usar_marca (la marca del proyecto)
  pantallas ..... dialog, por_perfil (visibilidad por perfil con su capa de seguridad, CAPAS)
"""
import json  # noqa: F401 (los generadores lo reciben con «from sail_helpers import *»)
from pathlib import Path  # noqa: F401


def usar_marca(marca="appian", carpeta=None):
    """Colores de los helpers según la marca del prototipo: brand-<marca>.json de `carpeta` (la del proyecto, junto al
    app.json en <p>/prototipo/) o, si no está ahí, de assets/ del kit, donde solo está la estándar de Appian («appian»).
    Lo que la marca no define sale de la estándar. Va antes de «from sail_helpers import *», que copia estos nombres al
    importar; sin la llamada, los de la marca estándar (la última línea de este fichero llama a usar_marca())."""
    global _BRAND, PRIMARY, GREEN, NAVY, STATES, CHART, GREY_TXT, SURFACE, LINE, LINE_STRONG, EVENT_TYPES, KANBAN_STATES, ICONO_AVISO
    from validate import find_brand, contrast  # la misma búsqueda y el mismo aviso que validate.py y build.py
    propia = find_brand(marca, carpeta)[0]
    neutra = find_brand("appian")[0]
    _BRAND = {**neutra, **propia, **{k: {**(neutra.get(k) or {}), **(propia.get(k) or {})} for k in ("site", "palette", "components", "states")}}
    pal = _BRAND["palette"]
    prof = {k: v for g in (propia.get("cssProfile") or {}).get("groups") or [] for k, v in (g.get("properties") or {}).items()}
    PRIMARY = _BRAND["components"]["primaryButton"]["color"]   # botón principal de la marca (ACCENT en la estándar)
    GREEN = _BRAND["site"]["selectedPageHighlightColor"]        # resaltado de la marca: barras decorativas y el día de hoy
    NAVY = pal["navy"]                                          # oscuro de la marca: cabecera de registro, hero, barra lateral
    STATES = {k: v for k, v in _BRAND["states"].items() if isinstance(v, dict)}
    CHART = _BRAND["components"]["chartColorScheme"]            # series de gráficos en orden (3:1 sobre blanco; la más clara, la última)
    GREY_TXT = pal["slate"]      # texto secundario: 4,5:1 o más sobre blanco y sobre los grises claros de la paleta
    SURFACE = pal["pageBg"]      # superficie gris suave (días de otro mes, respuestas, eventos pasados)
    LINE = pal["grayLight"]      # bordes y líneas finas
    # líneas y elementos gráficos que deben verse (3:1 sobre blanco y sobre el gris de página): los de la marca o, si no los
    # define, el borde de los campos de su perfil CSS, que cumple lo mismo
    LINE_STRONG = (propia.get("palette") or {}).get("lineStrong") or prof.get("input-box-on-light-border-color") or neutra["palette"]["lineStrong"]
    # tipo de evento → (icono, color): tonos distintos (azul, rojo, verde) para que el tinte de cada tipo se distinga; todos 4,5:1 sobre blanco
    EVENT_TYPES = {"Evento": ("calendar-day", pal["steel"]), "Plazo": ("flag", pal["red"]), "Turno": ("clock-o", pal["greenDark"])}
    KANBAN_STATES = [("Pendiente", GREY_TXT, STATES["neutral"]["tag"]), ("En curso", NAVY, STATES["enCurso"]["tag"]), ("Hecho", pal["greenDark"], STATES["positivo"]["tag"])]
    # icono de un aviso WARN (action_banner): el enumerado si llega a 3:1 sobre el fondo de aviso de la marca; si no (el ámbar
    # estándar de Appian sobre su fondo, sin perfil CSS, se queda en 2,95:1), el ámbar de la paleta
    ICONO_AVISO = "WARN" if contrast(prof.get("warn-on-light-color", "#D97706"), prof.get("warn-background-color", "#FFF5E6")) >= 3 else pal["amber"]
    AI_MAPS["confianzaColor"] = {"ALTA": STATES["neutral"]["tag"], "MEDIA": STATES["neutral"]["tag"], "BAJA": STATES["atencion"]["tag"], "*": STATES["neutral"]["tag"]}


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
    icol = {"WARN": ICONO_AVISO, "INFO": "#115EBB", "ERROR": "NEGATIVE", "SUCCESS": "POSITIVE"}[kind]  # a!richTextIcon no admite INFO: el azul informativo estándar de Appian
    items = [{"type": "a!sideBySideItem", "width": "MINIMIZE", "item": {"type": "a!richTextDisplayField", "labelPosition": "COLLAPSED", "value": [{"type": "a!richTextIcon", "icon": ic, "color": icol, "size": "MEDIUM"}]}},
             {"type": "a!sideBySideItem", "item": {"type": "a!richTextDisplayField", "labelPosition": "COLLAPSED", "value": txtv}}]
    if button:
        if kind in ("INFO", "ERROR") and button.get("style") != "SOLID" and button.get("color", "ACCENT") == "ACCENT":
            button = dict(button, color=NAVY)  # el oscuro de la marca llega a 4,5:1 sobre el fondo azul o rojo claro con cualquier acento
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
    """KPI con el icono en un sello de color suave (iconStyle STAMP, ADJACENT): más visual y fácil de escanear.
    value: fijo ($value) o se calcula con data + primaryMeasure (kw). secondary: valor de comparación → tendencia.
    Para KPI en columnas estrechas o dentro de tarjetas pequeñas: template="COMPACT", iconStyle="ICON"."""
    k = {"type": "a!kpiField", "primaryText": text, "icon": icon, "template": "ADJACENT", "iconStyle": "STAMP", "iconColor": "ACCENT"}
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
def _enum_hex(v):
    """Color de texto/gráfico de un estado (enum de la paleta de estados) resuelto con el perfil CSS de la marca."""
    prof = {k: x for g in (_BRAND.get("cssProfile") or {}).get("groups") or [] for k, x in (g.get("properties") or {}).items()}
    return {"SECONDARY": _BRAND["palette"]["slate"], "POSITIVE": prof.get("positive-on-light-color", "#117C00"), "NEGATIVE": prof.get("negative-on-light-color", "#B2002C"),
            "WARN": prof.get("warn-on-light-color", "#D97706"), "INFO": prof.get("info-on-light-color", "#115EBB"), "ACCENT": _BRAND["site"]["accentColor"]}.get(v, v)


def state_chart_colors(mapping, order):
    """Colores de gráfico por estado (mismo significado que las etiquetas, en tono fuerte con 3:1 o más sobre blanco).
    mapping: {"Aprobado": "positivo", …}; order: estados en el orden de las categorías del gráfico."""
    return {"type": "a!colorSchemeCustom", "colors": [_enum_hex(STATES[mapping.get(s, "neutral")]["enum"]) for s in order]}


def state_map(mapping, default="neutral", grid=False):
    """Mapa estado → color de tag con la paleta semántica. mapping: {"Vigente": "positivo", ...} → {"Vigente": "#DBEBD9", ...}.
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
    """Acción principal: SOLID con el color del botón principal de la marca (ACCENT en la estándar). Una por pantalla."""
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
    """Destructiva (pérdida real de datos: borrar, anular sin vuelta atrás): GHOST + NEGATIVE con confirmación obligatoria.
    confirm = (cabecera con el objeto, mensaje con la consecuencia). Cancelar algo que se puede retomar no es destructiva: secondary()."""
    if not confirm and not (kw.get("confirmHeader") and kw.get("confirmMessage")):
        raise ValueError(f"danger(«{label}»): falta confirm=(cabecera, mensaje); una acción destructiva siempre pide confirmación")
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
    """Diálogo P07: formulario de una columna con contentsWidth FULL (ocupa el cuadro). El ancho del cuadro se ajusta al contenido
    y lo fija la acción de registro (Dialog Width en el record type): width → $dialogWidth (NARROW, MEDIUM, MEDIUM_PLUS, WIDE)."""
    d = {"id": sid, "title": title, "type": "dialog", "pattern": "P07", "req": req, "ref": ref, "$dialogWidth": width,
         "interface": {"type": "a!formLayout", "titleBar": title, "contentsWidth": "FULL", "contents": contents, "buttons": buttons}}
    if openFrom: d["openFrom"] = openFrom
    if recordType: d["recordType"] = recordType
    d.update(kw); return d


# capa de seguridad de Appian que aplica «solo lo ve un perfil» (appian-best-practices 06 §5)
CAPAS = {"registro": "seguridad de registro del record type (qué filas ve)",
         "campo": "seguridad de campo del record type; en la interfaz, showWhen con a!doesUserHaveAccess() (sin acceso, el campo sale vacío)",
         "vista": "seguridad de vista de registro",
         "accion": "seguridad de acción de registro (y permiso Initiator en el modelo de proceso)",
         "interfaz": "visibilidad de interfaz (showWhen con a!isUserMemberOfGroup()): solo oculta, no protege; los datos se protegen en el record type"}


def por_perfil(node, perfil, capa, cuando=None):
    """Lo que solo ve un perfil: $note con el perfil y la capa de seguridad de Appian que lo aplica (CAPAS: registro, campo, vista,
    accion, interfaz). cuando: showWhen del prototipo para enseñarlo oculto en la demo (p. ej. "ri!perfil = \\"GESTOR\\"")."""
    n = dict(node)
    nota = "Solo para %s. En Appian: %s." % (perfil, CAPAS[capa])
    n["$note"] = (n["$note"] + " " + nota) if n.get("$note") else nota
    if cuando: n["showWhen"] = cuando
    return n


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


def chart_table(var, chart, cat_label="Categoría", value_labels=None, fmt="num", table=None, **kw):
    """Gráfico con su alternativa accesible (receta «Configure a Chart to Grid Toggle», BP 02 §9.5): un enlace alterna el gráfico y
    una tabla con los mismos datos. var: variable booleana declarada en 'local' (false = gráfico). La tabla sale del propio gráfico
    ($chart: mismas categorías, medidas y filtros); table sustituye a la generada (gráficos de dispersión o tablas propias)."""
    if table is None:
        cfg = chart.get("config") or {}
        ms, g1, g2 = cfg.get("measures") or [], (cfg.get("primaryGrouping") or {}).get("field"), (cfg.get("secondaryGrouping") or {}).get("field")
        if value_labels is None and g2 and g2 != g1:
            value_labels = chart.get("$series")  # una columna por valor de la agrupación secundaria
            if not value_labels:
                raise ValueError("chart_table: con agrupación secundaria, pasa value_labels o $series en el gráfico")
        elif value_labels is None:
            value_labels = ([ms[0].get("label") or "Total"] if g2 else [m.get("label") or "Total" for m in ms]) if ms else \
                ["Valor"] if chart.get("type") == "a!pieChartField" else [s.get("label") or "Valor" for s in chart.get("series") or []]
        src ={k: v for k, v in chart.items() if k not in ("showWhen", "$note", "$assumption", "$uxIgnore")}
        table = grid(None, None, [gcol(cat_label, "{fv!row.categoria}")] + [gcol_num(lb, "{fv!row.s%d|%s}" % (k + 1, fmt)) for k, lb in enumerate(value_labels)],
                     "No hay datos que mostrar", page_size=20, **{"$chart": src, "$note": "En Appian: a!gridField sobre a!queryRecordType con a!aggregationFields "
                                                                  "(la misma agrupación, medidas y filtros que el gráfico)."})
        table.pop("data")
    sw = lambda n, cond: {**n, "showWhen": cond}
    link = _rtd([{"type": "a!richTextIcon", "icon": "{if(%s, \"bar-chart\", \"table\")}" % var, "color": "ACCENT"}, " ",
                 _link("{if(%s, \"Ver como gráfico\", \"Ver como tabla\")}" % var, saves=[(var, "{not(%s)}" % var)], style="STRONG")], align="RIGHT", marginBelow="LESS")
    s = {"type": "a!sectionLayout", "marginBelow": "NONE", "contents": [link, sw(chart, "not(%s)" % var), sw(table, var)]}
    s.update(kw); return s


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
    {campo, valor, confianza ALTA|MEDIA|BAJA, origen IA|EDITADO, revisado, pagina}. Guardar valida: ai_review_validation(var) en
    validations del formulario (dice qué falta; nunca un botón desactivado sin explicación).
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


def ai_review_validation(var, message="Revise los datos de confianza baja: marque «Revisado» o corrija el valor"):
    """Validación del formulario de revisión (P12): al pulsar Guardar, si queda algún dato de confianza baja sin revisar,
    el mensaje dice qué falta (a!validationMessage en validations de a!formLayout, receta de validaciones de formulario)."""
    return {"type": "a!validationMessage", "message": message, "validateAfter": "SUBMIT", "showWhen": "contains(%s.revisado, false)" % var}


AI_MAPS = {"confianzaTexto": {"ALTA": "Confianza alta", "MEDIA": "Confianza media", "BAJA": "Confianza baja", "*": "Sin sugerencia"},
           "confianzaColor": {},  # los colores de la paleta de estados de la marca: los pone usar_marca()
           "origenTexto": {"IA": "Sugerido por IA", "EDITADO": "Editado", "USUARIO": "Introducido", "*": "Sin valor"}}


# compatibilidad con generadores anteriores
def ojo():
    return {"type": "a!richTextDisplayField", "value": [{"type": "a!richTextIcon", "icon": "eye", "color": "ACCENT", "altText": "Ver detalle", "link": {"type": "a!dynamicLink"}}]}


def alerta_icon(expr="fv!row.alerta"):
    return {"type": "a!richTextDisplayField", "value": [{"type": "a!richTextIcon", "icon": "exclamation-circle", "color": "NEGATIVE", "size": "MEDIUM", "altText": "Con alerta", "caption": "Con alerta", "showWhen": expr}]}


# ------------------------------------------------------------------ patrones del SAIL Design System 26.9: calendario, comentarios, kanban
# Fuentes: https://docs.appian.com/suite/help/26.9/sail/calendar.html, comment-thread.html y kanban.html
import datetime as _dt
# los colores de estos patrones (EVENT_TYPES, GREY_TXT, SURFACE, LINE, LINE_STRONG, KANBAN_STATES) salen de la marca: usar_marca()


def _q(v):
    return '"%s"' % v


def _event_line(small=True):
    """Icono de color del tipo y título del evento (fv!item) en una línea."""
    ic = "{fv!item.tipo|map:eventoIcono}"
    col = "{fv!item.tipo|map:eventoColor}"
    return [{"type": "a!richTextIcon", "icon": ic, "color": col, "size": "SMALL" if small else "STANDARD"}, " ", {"type": "a!richTextItem", "text": "{fv!item.titulo}", "size": "SMALL"}]


def event_maps(types=None):
    """Mapas eventoIcono / eventoColor / eventoFondo para los calendarios (añadir a spec["maps"]); «(pasado)»: gris de lo ya ocurrido."""
    t = types or EVENT_TYPES
    return {"eventoIcono": {k: v[0] for k, v in t.items()} | {"*": "calendar-o"}, "eventoColor": {k: v[1] for k, v in t.items()} | {"(pasado)": LINE_STRONG, "*": "SECONDARY"},
            "eventoFondo": {k: v[1] + "26" for k, v in t.items()} | {"*": SURFACE}}


def _chip(past, text_expr="{fv!item.titulo}", time=False):
    """Evento como «chip»: barra de color del tipo a la izquierda y tinte suave; lo pasado, en gris."""
    txt = [{"type": "a!richTextItem", "text": text_expr, "size": "SMALL", "color": GREY_TXT if past else "STANDARD"}]
    if time:
        txt = [{"type": "a!richTextItem", "text": "{fv!item.hora} ", "size": "SMALL", "style": "STRONG", "color": GREY_TXT if past else "STANDARD"}] + txt
    return {"type": "a!cardLayout", "showBorder": False, "shape": "SEMI_ROUNDED", "padding": "EVEN_LESS", "marginBelow": "EVEN_LESS",
            "style": "NONE" if past else "{fv!item.tipo|map:eventoFondo}",  # lo pasado, sin relleno: se distingue del tinte de los próximos
            "decorativeBarPosition": "START", "decorativeBarColor": LINE_STRONG if past else "{fv!item.tipo|map:eventoColor}",
            "tooltip": "{fv!item.hora} · {fv!item.titulo}", "contents": [_rtd(txt, preventWrapping=True, marginBelow="NONE")]}


def calendar_month(events, sel_var, today, months=None, month_var=None, detail=True, **kw):
    """Calendario mensual (patrón Calendar · Month view): rejilla de semanas de lunes a domingo; cada día es una card que se pulsa
    para ver sus eventos en el panel derecho. Hoy va resaltado, los días de otro mes en gris y lo pasado, atenuado.
    events: referencia a la lista de eventos ("local!eventos" o "data!eventos") con fecha (AAAA-MM-DD), hora, titulo, tipo y detalle.
    months: [(año, mes)] navegables con ‹ Hoy › (month_var guarda el índice, 1 = el primero); por defecto el mes de today.
    Añada event_maps() a spec["maps"]."""
    t = _dt.date.fromisoformat(today)
    months = months or [(t.year, t.month)]
    names = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    grids = []
    for k, (y, m) in enumerate(months):
        first = _dt.date(y, m, 1)
        start = first - _dt.timedelta(days=first.weekday())
        rows = []
        for w in range(6):
            days = [start + _dt.timedelta(days=w * 7 + d) for d in range(7)]
            if w == 5 and days[0].month != m:
                break
            cols_ = []
            for d in days:
                iso = d.isoformat()
                cur, past = d.month == m, d < t
                bg = GREEN + "33" if d == t else "#FFFFFF" if cur else SURFACE  # hoy: tinte del color de resaltado de la marca
                num = {"type": "a!richTextItem", "text": str(d.day) + ("  · hoy" if d == t else ""), "style": "STRONG" if d == t else "PLAIN", "color": "STANDARD" if cur and not past else GREY_TXT}
                cell = {"type": "a!cardLayout", "shape": "SEMI_ROUNDED", "padding": "LESS", "height": "SHORT", "style": bg,
                        "showBorder": "{%s = %s}" % (sel_var, _q(iso)), "borderColor": "ACCENT", "borderWeight": "MEDIUM",
                        "link": {"type": "a!dynamicLink", "value": iso, "saveInto": sel_var}, "accessibilityText": "%d de %s%s" % (d.day, names[d.month - 1], ", hoy" if d == t else ""),
                        "contents": [_rtd(num, marginBelow="EVEN_LESS"),
                                     {"type": "a!forEach", "items": events, "$filter": "fv!item.fecha = %s" % _q(iso), "$limit": 2, "expression": _chip(past)},
                                     _rtd({"type": "a!richTextItem", "text": "+{count(wherecontains(%s, %s.fecha)) - 2} más" % (_q(iso), events), "size": "SMALL", "color": GREY_TXT, "style": "STRONG"},
                                          showWhen="count(wherecontains(%s, %s.fecha)) > 2" % (_q(iso), events), marginBelow="NONE")]}
                head = [_rtd({"type": "a!richTextItem", "text": ["LUN", "MAR", "MIÉ", "JUE", "VIE", "SÁB", "DOM"][d.weekday()], "size": "SMALL", "color": GREY_TXT, "style": "STRONG"}, align="CENTER", marginBelow="EVEN_LESS")] if w == 0 else []
                cols_.append({"type": "a!columnLayout", "contents": head + [cell]})
            rows.append({"type": "a!columnsLayout", "spacing": "DENSE", "marginBelow": "LESS", "stackWhen": ["NEVER"], "columns": cols_})
        g = {"type": "a!sectionLayout", "marginBelow": "NONE", "contents": rows}
        if len(months) > 1:
            g["showWhen"] = "%s = %d" % (month_var, k + 1)
        grids.append(g)
    # cabecera: ‹ Hoy › y el mes (con varios meses, las flechas cambian de mes; en los extremos se ven en gris)
    multi = len(months) > 1
    def arrow(icon, cap, delta, cond):
        on = {"type": "a!richTextIcon", "icon": icon, "size": "MEDIUM", "color": "STANDARD", "caption": cap, "altText": cap, "showWhen": cond,
              "link": {"type": "a!dynamicLink", "value": "{%s %s 1}" % (month_var, "+" if delta > 0 else "-"), "saveInto": month_var}, "linkStyle": "STANDALONE"}
        off = {"type": "a!richTextIcon", "icon": icon, "size": "MEDIUM", "color": LINE_STRONG, "caption": cap + " (no disponible)", "altText": cap + " (no disponible)", "showWhen": "not(%s)" % cond}
        return {"type": "a!sideBySideItem", "width": "MINIMIZE", "item": _rtd([on, off], marginBelow="NONE")}
    today_k = next((k + 1 for k, (y, m) in enumerate(months) if (y, m) == (t.year, t.month)), 1)
    title = [{"type": "a!sideBySideItem", "width": "MINIMIZE", "item": {"type": "a!headingField", "text": "%s de %d" % (names[m - 1].capitalize(), y), "size": "MEDIUM_PLUS", "fontWeight": "BOLD", "headingTag": "H2", "marginBelow": "NONE",
              **({"showWhen": "%s = %d" % (month_var, k + 1)} if multi else {})}} for k, (y, m) in enumerate(months)]
    hoy = {"type": "a!sideBySideItem", "width": "MINIMIZE", "item": {"type": "a!buttonArrayLayout", "marginBelow": "NONE", "buttons": [
        {"type": "a!buttonWidget", "label": "Hoy", "style": "OUTLINE", "color": "SECONDARY", "size": "SMALL",
         "$action": {"set": {**({month_var: today_k} if multi else {}), sel_var: today}}}]}}
    nav = {"type": "a!sideBySideLayout", "alignVertical": "MIDDLE", "spacing": "STANDARD", "marginBelow": "STANDARD",
           "items": ([arrow("angle-left", "Mes anterior", -1, "%s > 1" % month_var)] if multi else []) + ([hoy] if multi else []) +
                    ([arrow("angle-right", "Mes siguiente", 1, "%s < %d" % (month_var, len(months)))] if multi else []) + title}
    grid_card = {"type": "a!cardLayout", "shape": "SEMI_ROUNDED", "padding": "LESS", "showBorder": False, "showShadow": True, "style": "NONE", "contents": grids}
    if not detail:
        s = {"type": "a!sectionLayout", "contents": [nav, grid_card], "marginBelow": "MORE"}
        s.update(kw); return s
    # panel del día seleccionado: eventos (pasados atenuados) o estado vacío
    past = "todate(fv!item.fecha) < todate(%s)" % _q(today)
    ev_card = {"type": "a!cardLayout", "marginBelow": "LESS", "padding": "STANDARD", "shape": "SEMI_ROUNDED", "showBorder": False,
               "showShadow": "{not(%s)}" % past, "style": "{if(%s, \"%s\", \"#FFFFFF\")}" % (past, SURFACE),
               "decorativeBarPosition": "START", "decorativeBarColor": "{if(%s, \"(pasado)\", fv!item.tipo)|map:eventoColor}" % past,
               "contents": [{"type": "a!sideBySideLayout", "marginBelow": "LESS", "items": [
                   {"type": "a!sideBySideItem", "item": _rtd([{"type": "a!richTextIcon", "icon": "{fv!item.tipo|map:eventoIcono}", "color": "{fv!item.tipo|map:eventoColor}"}, " ",
                                                              {"type": "a!richTextItem", "text": "{fv!item.tipo}", "style": "STRONG", "size": "SMALL", "color": "{fv!item.tipo|map:eventoColor}"}], marginBelow="NONE")},
                   {"type": "a!sideBySideItem", "width": "MINIMIZE", "item": _rtd({"type": "a!richTextItem", "text": "{fv!item.hora}", "size": "SMALL", "style": "STRONG", "color": "{if(%s, \"%s\", \"STANDARD\")}" % (past, GREY_TXT)}, marginBelow="NONE")}]},
                   _rtd({"type": "a!richTextItem", "text": "{fv!item.titulo}", "style": "STRONG"}, marginBelow="EVEN_LESS"),
                   _rtd({"type": "a!richTextItem", "text": "{fv!item.detalle}", "size": "SMALL", "color": GREY_TXT}, showWhen="a!isNotNullOrEmpty(fv!item.detalle)", marginBelow="NONE")]}
    empty = {"type": "a!cardLayout", "shape": "SEMI_ROUNDED", "showBorder": False, "showShadow": True, "padding": "MORE", "showWhen": "not(contains(%s.fecha, %s))" % (events, sel_var), "contents": [
        {"type": "a!stampField", "icon": "calendar-o", "size": "SMALL", "align": "CENTER", "backgroundColor": STATES["neutral"]["tag"], "contentColor": GREY_TXT, "marginBelow": "LESS"},
        _rtd({"type": "a!richTextItem", "text": "No hay eventos ni plazos este día", "size": "SMALL", "color": GREY_TXT}, align="CENTER")]}
    side = [{"type": "a!headingField", "headingTag": "H3", "text": "{%s|longdate}" % sel_var, "fontWeight": "SEMI_BOLD", "size": "MEDIUM_PLUS", "marginBelow": "STANDARD"},
            {"type": "a!forEach", "items": events, "$filter": "fv!item.fecha = %s" % sel_var, "expression": ev_card}, empty]
    c = {"type": "a!sectionLayout", "marginBelow": "MORE", "contents": [nav, {"type": "a!columnsLayout", "stackWhen": ["PHONE", "TABLET_PORTRAIT"], "columns": [
        {"type": "a!columnLayout", "width": "2X", "contents": [grid_card]}, {"type": "a!columnLayout", "width": "1X", "contents": side}]}]}
    c.update(kw); return c


def calendar_week(events, start, today, **kw):
    """Calendario semanal (patrón Calendar · Week view): un día por columna con sus eventos en tarjetas con la barra y el tinte
    del color de su tipo; lo pasado en gris y hoy resaltado. start: lunes de la semana (AAAA-MM-DD). Para ver pocos días con más detalle."""
    s0 = _dt.date.fromisoformat(start)
    t = _dt.date.fromisoformat(today)
    days = [s0 + _dt.timedelta(days=d) for d in range(7)]
    heads, bodies = [], []
    for day in days:
        iso = day.isoformat()
        past, now = day < t, day == t
        heads.append({"type": "a!columnLayout", "contents": [
            {"type": "a!headingField", "headingTag": "H3", "text": "{%s|dayname}" % _q(iso), "align": "CENTER", "size": "SMALL", "fontWeight": "BOLD", "marginAbove": "LESS", "marginBelow": "NONE",
             "color": "STANDARD" if not past else GREY_TXT},
            _rtd({"type": "a!richTextItem", "text": "{%s|daymonth}" % _q(iso) + (" · hoy" if now else ""), "size": "SMALL", "style": "STRONG" if now else "PLAIN", "color": "STANDARD" if now else GREY_TXT},
                 align="CENTER", marginBelow="LESS")]})
        card_ = {"type": "a!cardLayout", "marginBelow": "LESS", "shape": "SEMI_ROUNDED", "showBorder": False, "padding": "LESS",
                 "style": "NONE" if past else "{fv!item.tipo|map:eventoFondo}",  # lo pasado, sin relleno: se distingue del tinte de los próximos
                 "decorativeBarPosition": "START", "decorativeBarColor": LINE_STRONG if past else "{fv!item.tipo|map:eventoColor}",
                 "contents": [_rtd([{"type": "a!richTextIcon", "icon": "{fv!item.tipo|map:eventoIcono}", "color": GREY_TXT if past else "{fv!item.tipo|map:eventoColor}"}, " ",
                                    {"type": "a!richTextItem", "text": "{fv!item.hora}", "size": "SMALL", "style": "STRONG", "color": GREY_TXT if past else "STANDARD"}, "\n",
                                    {"type": "a!richTextItem", "text": "{fv!item.titulo}", "size": "SMALL", "style": "STRONG" if not past else "PLAIN", "color": GREY_TXT if past else "STANDARD"}], marginBelow="NONE")]}
        bodies.append({"type": "a!columnLayout", "contents": [{"type": "a!forEach", "items": events, "$filter": "fv!item.fecha = %s" % _q(iso), "expression": card_},
                                                             _rtd({"type": "a!richTextItem", "text": "Sin eventos", "size": "SMALL", "color": GREY_TXT}, align="CENTER",
                                                                  showWhen="not(contains(%s.fecha, %s))" % (events, _q(iso)), marginAbove="STANDARD")]})
    c = {"type": "a!cardLayout", "style": "NONE", "shape": "SEMI_ROUNDED", "padding": "LESS", "showShadow": True, "showBorder": False, "marginBelow": "MORE",
         "contents": [{"type": "a!columnsLayout", "spacing": "DENSE", "showDividers": True, "stackWhen": ["NEVER"], "marginBelow": "NONE", "columns": heads},
                      {"type": "a!horizontalLine", "color": LINE, "marginBelow": "LESS"},
                      {"type": "a!columnsLayout", "spacing": "DENSE", "showDividers": True, "stackWhen": ["PHONE", "TABLET_PORTRAIT"], "columns": bodies}]}
    c.update(kw); return c


def comment_thread(var, user, new_var, reply_to_var, reply_var, title="Comentarios", **kw):
    """Hilo de comentarios (patrón Comment Thread · With replies and attachments): comentario nuevo arriba, cada comentario con
    avatar, autor, fecha, texto, adjuntos y botón Responder; las respuestas se pliegan bajo su comentario.
    var: lista de comentarios [{id, autor, fecha (AAAA-MM-DDThh:mm), texto, adjuntos: [{nombre, tipo, tamano}], padre}] (padre = id del comentario
    al que responde). user: nombre de quien comenta. new_var / reply_var: textos en edición; reply_to_var: id del comentario al que se responde."""
    def meta(small=False):
        return [{"type": "a!sideBySideItem", "width": "MINIMIZE", "item": {"type": "a!imageField", "labelPosition": "COLLAPSED", "size": "ICON_PLUS" if small else "TINY", "style": "AVATAR", "images": [{"type": "a!userImage", "user": "{fv!item.autor}"}]}},
                {"type": "a!sideBySideItem", "width": "MINIMIZE", "item": _rtd({"type": "a!richTextItem", "text": "{fv!item.autor}", "style": "STRONG"}, marginBelow="NONE")},
                {"type": "a!sideBySideItem", "item": _rtd({"type": "a!richTextItem", "text": "{fv!item.fecha|datetime}", "size": "SMALL", "color": GREY_TXT}, marginBelow="NONE")}]
    attach = {"type": "a!cardGroupLayout", "labelPosition": "COLLAPSED", "cardWidth": "MEDIUM", "spacing": "DENSE", "marginAbove": "LESS", "showWhen": "a!isNotNullOrEmpty(fv!item.adjuntos)", "cards": [
        {"type": "a!forEach", "items": "fv!item.adjuntos", "expression": {"type": "a!cardLayout", "shape": "SEMI_ROUNDED", "padding": "LESS", "borderColor": LINE, "link": {"type": "a!documentDownloadLink", "document": "{fv!item.nombre}"}, "accessibilityText": "Descargar {fv!item.nombre}",
            "$uxIgnore": "Patrón Comment Thread de Appian 26.9: cada adjunto es una tarjeta con borde dentro del comentario", "contents": [
            {"type": "a!sideBySideLayout", "alignVertical": "MIDDLE", "items": [
                {"type": "a!sideBySideItem", "width": "MINIMIZE", "item": {"type": "a!stampField", "icon": "{fv!item.tipo|map:adjuntoIcono}", "size": "TINY", "shape": "SQUARED", "backgroundColor": STATES["enCurso"]["tag"], "contentColor": NAVY, "accessibilityText": "{fv!item.tipo}"}},
                {"type": "a!sideBySideItem", "item": _rtd([{"type": "a!richTextItem", "text": "{fv!item.nombre}", "style": "STRONG", "size": "SMALL"}, "\n", {"type": "a!richTextItem", "text": "{fv!item.tamano}", "size": "SMALL", "color": GREY_TXT}], marginBelow="NONE")}]}]}}]}
    reply_card = {"type": "a!cardLayout", "style": SURFACE, "showBorder": False, "shape": "SEMI_ROUNDED", "padding": "STANDARD", "marginBelow": "LESS", "contents": [
        {"type": "a!sideBySideLayout", "alignVertical": "MIDDLE", "marginBelow": "LESS", "items": meta(small=True)}, _rtd("{fv!item.texto}", marginBelow="NONE"), attach]}
    reply_box = {"type": "a!cardLayout", "showWhen": "%s = local!comentario.id" % reply_to_var, "shape": "SEMI_ROUNDED", "padding": "STANDARD", "borderColor": "ACCENT", "marginAbove": "STANDARD",
                 "$uxIgnore": "Cuadro de respuesta abierto: el borde de acento indica dónde se escribe", "contents": [
        {"type": "a!paragraphField", "label": "Respuesta a {local!comentario.autor}", "labelPosition": "COLLAPSED", "placeholder": "Escriba su respuesta", "height": "SHORT", "value": reply_var, "saveInto": reply_var},
        {"type": "a!buttonArrayLayout", "align": "END", "marginBelow": "NONE", "buttons": [
            {"type": "a!buttonWidget", "label": "Cancelar", "style": "LINK", "color": "SECONDARY", "size": "SMALL", "$action": {"set": {reply_to_var: None, reply_var: None}}},
            {"type": "a!buttonWidget", "label": "Responder", "style": "OUTLINE", "color": "ACCENT", "size": "SMALL", "disabled": "a!isNullOrEmpty(%s)" % reply_var,
             "$action": {"append": {var: {"id": "{count(%s) + 1}" % var, "autor": user, "fecha": "{now()}", "texto": "{%s}" % reply_var, "adjuntos": [], "padre": "{local!comentario.id}"}}, "set": {reply_var: None, reply_to_var: None}}}]}]}
    comment = {"type": "a!cardLayout", "shape": "SEMI_ROUNDED", "padding": "STANDARD", "showBorder": False, "showShadow": True, "marginBelow": "STANDARD", "contents": [
        {"type": "a!sideBySideLayout", "alignVertical": "MIDDLE", "marginBelow": "LESS", "items": meta() + [
            {"type": "a!sideBySideItem", "width": "MINIMIZE", "item": {"type": "a!buttonArrayLayout", "align": "END", "marginBelow": "NONE", "buttons": [
                {"type": "a!buttonWidget", "label": "Responder", "icon": "reply", "style": "LINK", "color": "ACCENT", "size": "SMALL", "value": "{local!comentario.id}", "saveInto": reply_to_var}]}}]},
        _rtd("{fv!item.texto}", marginBelow="NONE"), attach,
        {"type": "a!sectionLayout", "label": "Respuestas ({count(wherecontains(local!comentario.id, %s.padre))})" % var, "labelSize": "EXTRA_SMALL", "labelColor": "STANDARD", "labelHeadingTag": "H4",
         "isCollapsible": True, "marginAbove": "STANDARD", "marginBelow": "NONE", "showWhen": "contains(%s.padre, local!comentario.id)" % var,
         "contents": [{"type": "a!forEach", "items": var, "$filter": "fv!item.padre = local!comentario.id", "expression": reply_card}]},
        reply_box]}
    new = {"type": "a!cardLayout", "shape": "SEMI_ROUNDED", "padding": "STANDARD", "showBorder": False, "showShadow": True, "marginBelow": "STANDARD", "contents": [
        {"type": "a!paragraphField", "label": "Nuevo comentario", "labelPosition": "COLLAPSED", "placeholder": "Añada un comentario", "height": "SHORT", "value": new_var, "saveInto": new_var},
        {"type": "a!buttonArrayLayout", "align": "END", "marginBelow": "NONE", "buttons": [
            {"type": "a!buttonWidget", "label": "Publicar", "icon": "paper-plane", "style": "OUTLINE", "color": "ACCENT", "size": "SMALL", "disabled": "a!isNullOrEmpty(%s)" % new_var,
             "$action": {"prepend": {var: {"id": "{count(%s) + 1}" % var, "autor": user, "fecha": "{now()}", "texto": "{%s}" % new_var, "adjuntos": [], "padre": None}}, "set": {new_var: None}}}]}]}
    s = {"type": "a!sectionLayout", "marginBelow": "MORE", "contents": [
        {"type": "a!headingField", "text": "%s ({count(%s)})" % (title, var), "headingTag": "H2", "size": "MEDIUM", "fontWeight": "BOLD", "marginBelow": "STANDARD"}, new,
        {"type": "a!forEach", "items": var, "$filter": "a!isNullOrEmpty(fv!item.padre)", "$local": {"local!comentario": "fv!item"}, "expression": comment}]}
    s.update(kw); return s


ATTACH_MAPS = {"adjuntoIcono": {"pdf": "file-pdf-o", "imagen": "file-image-o", "word": "file-word-o", "excel": "file-excel-o", "*": "file-o"}}


def kanban(var, title, statuses=None, add_button=None, **kw):
    """Tablero kanban (patrón Kanban Board): una columna por estado con su cabecera de color (tinte + barra superior y recuento);
    cada tarjeta muestra tipo de trabajo, título, descripción, responsable, fecha límite y avance, con flechas para pasarla de columna.
    var: lista de tareas [{id, titulo, descripcion, tipo, tipoColor, responsable, fecha, avance, estado}]. statuses: [(estado, color, fondo)]."""
    st = statuses or KANBAN_STATES
    labels = [s[0] for s in st]
    heads, bodies = [], []
    for k, (lab, col, bg) in enumerate(st):
        heads.append({"type": "a!columnLayout", "contents": [{"type": "a!cardLayout", "showBorder": False, "shape": "SEMI_ROUNDED", "padding": "STANDARD", "style": bg, "decorativeBarPosition": "TOP", "decorativeBarColor": col, "marginBelow": "LESS", "contents": [
            {"type": "a!sideBySideLayout", "alignVertical": "MIDDLE", "items": [
                {"type": "a!sideBySideItem", "item": _rtd({"type": "a!richTextItem", "text": lab, "style": "STRONG"}, marginBelow="NONE")},
                {"type": "a!sideBySideItem", "width": "MINIMIZE", "item": {"type": "a!stampField", "text": "{count(wherecontains(%s, %s.estado))}" % (_q(lab), var), "size": "EXTRA_TINY", "backgroundColor": col,
                                                                          "accessibilityText": "{count(wherecontains(%s, %s.estado))} tareas" % (_q(lab), var)}}]}]}]})
        prev_b = {"type": "a!buttonWidget", "icon": "arrow-left", "size": "SMALL", "style": "LINK", "color": "SECONDARY", "accessibilityText": "Pasar a %s" % labels[k - 1] if k else "Primera columna",
                  "tooltip": "Pasar a %s" % labels[k - 1] if k else None, "disabled": k == 0}
        next_b = {"type": "a!buttonWidget", "icon": "arrow-right", "size": "SMALL", "style": "LINK", "color": "SECONDARY", "accessibilityText": "Pasar a %s" % labels[k + 1] if k + 1 < len(st) else "Última columna",
                  "tooltip": "Pasar a %s" % labels[k + 1] if k + 1 < len(st) else None, "disabled": k + 1 == len(st)}
        if k: prev_b.update({"value": labels[k - 1], "saveInto": "fv!item.estado"})
        if k + 1 < len(st): next_b.update({"value": labels[k + 1], "saveInto": "fv!item.estado"})
        prev_b = {x: y for x, y in prev_b.items() if y is not None}
        next_b = {x: y for x, y in next_b.items() if y is not None}
        card_ = {"type": "a!cardLayout", "padding": "NONE", "showBorder": False, "showShadow": True, "shape": "SEMI_ROUNDED", "marginBelow": "LESS", "contents": [
            {"type": "a!cardLayout", "showBorder": False, "padding": "STANDARD", "style": "TRANSPARENT", "contents": [
                {"type": "a!sideBySideLayout", "alignVertical": "MIDDLE", "spacing": "NONE", "marginBelow": "LESS", "items": [
                    {"type": "a!sideBySideItem", "item": {"type": "a!tagField", "labelPosition": "COLLAPSED", "size": "SMALL", "tags": [{"type": "a!tagItem", "text": "{fv!item.tipo}", "backgroundColor": "{fv!item.tipoColor}26", "textColor": NAVY}]}},
                    {"type": "a!sideBySideItem", "width": "MINIMIZE", "item": {"type": "a!buttonArrayLayout", "marginBelow": "NONE", "buttons": [prev_b]}},
                    {"type": "a!sideBySideItem", "width": "MINIMIZE", "item": {"type": "a!buttonArrayLayout", "marginBelow": "NONE", "buttons": [next_b]}}]},
                _rtd([{"type": "a!richTextItem", "text": "{fv!item.titulo}", "style": "STRONG"}, "\n", {"type": "a!richTextItem", "text": "{fv!item.descripcion}", "size": "SMALL", "color": GREY_TXT}], marginBelow="STANDARD"),
                {"type": "a!sideBySideLayout", "alignVertical": "MIDDLE", "marginBelow": "NONE", "items": [
                    {"type": "a!sideBySideItem", "width": "MINIMIZE", "item": _rtd([{"type": "a!richTextIcon", "icon": "user-circle", "size": "SMALL", "color": "SECONDARY"}, " ", {"type": "a!richTextItem", "text": "{fv!item.responsable}", "size": "SMALL"}], marginBelow="NONE")},
                    {"type": "a!sideBySideItem", "item": _rtd([{"type": "a!richTextIcon", "icon": "calendar-day", "size": "SMALL", "color": "SECONDARY"}, " ", {"type": "a!richTextItem", "text": "{fv!item.fecha|daymonth}", "size": "SMALL"}], marginBelow="NONE")},
                    {"type": "a!sideBySideItem", "width": "MINIMIZE", "item": _rtd({"type": "a!richTextItem", "text": "{fv!item.avance} %", "size": "SMALL", "style": "STRONG"}, marginBelow="NONE")}]}]},
            {"type": "a!progressBarField", "label": "Avance de la tarea", "labelPosition": "COLLAPSED", "showPercentage": False, "percentage": "{fv!item.avance}", "color": col, "style": "THIN", "marginBelow": "NONE", "accessibilityText": "Avance: {fv!item.avance} %"}]}
        bodies.append({"type": "a!columnLayout", "contents": [{"type": "a!forEach", "items": var, "$filter": "fv!item.estado = %s" % _q(lab), "expression": card_},
                                                              _rtd({"type": "a!richTextItem", "text": "Sin tareas", "size": "SMALL", "color": GREY_TXT}, align="CENTER", showWhen="not(contains(%s.estado, %s))" % (var, _q(lab)))]})
    done = st[-1][0]
    head = {"type": "a!sideBySideLayout", "alignVertical": "MIDDLE", "marginBelow": "STANDARD", "items": [
        {"type": "a!sideBySideItem", "item": [{"type": "a!headingField", "text": title, "headingTag": "H2", "size": "MEDIUM_PLUS", "fontWeight": "BOLD", "marginBelow": "EVEN_LESS"},
                                              _rtd({"type": "a!richTextItem", "text": "{count(wherecontains(%s, %s.estado))} de {count(%s)} tareas terminadas" % (_q(done), var, var), "size": "SMALL", "color": GREY_TXT}, marginBelow="NONE")]}] +
        ([{"type": "a!sideBySideItem", "width": "MINIMIZE", "item": {"type": "a!buttonArrayLayout", "align": "END", "marginBelow": "NONE", "buttons": [add_button]}}] if add_button else [])}
    s = {"type": "a!sectionLayout", "marginBelow": "MORE", "contents": [head, {"type": "a!columnsLayout", "marginBelow": "NONE", "stackWhen": ["PHONE", "TABLET_PORTRAIT"], "columns": heads},
                                                                       {"type": "a!columnsLayout", "stackWhen": ["PHONE", "TABLET_PORTRAIT"], "columns": bodies}]}
    s.update(kw); return s


usar_marca()  # por defecto, la marca estándar de Appian (assets/brand-appian.json)
