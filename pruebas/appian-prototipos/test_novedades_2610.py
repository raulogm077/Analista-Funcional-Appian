"""Prueba de lo que añade Appian 26.10 al kit: que se pinte y se comporte como dice la documentación y que un
prototipo que declara 26.9 no pueda usarlo.

- a!decimalField, que con PRECISE (también por defecto) no pierde cifras; a!tagField LARGE; a!tagItem con borde, icono al final y fondo TRANSPARENT.
- a!recordKnowledgeGraph: enableLevelSlider empieza en el nivel 1 y abre el 2; selectionSaveInto guarda el registro pulsado,
  con el recordIdentifier de la raíz y sin marcar dos nodos que se llaman igual; el nodo guardado sale marcado
  también sin pulsarlo (el estado de una captura).
- a!agentChatField: con showReasoning false, la acción se ve mientras se hace y desaparece al terminar; por defecto, se queda.
- a!headerContentLayout: contentsWidth limita el contenido y el footer queda abajo si el contenido es corto.
"""
import json
import os
import pathlib
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
PLUGIN = pathlib.Path(os.environ.get("PLUGIN_A_PROBAR") or pathlib.Path(__file__).resolve().parents[2])
KIT = PLUGIN / "skills/appian-prototipos"
sys.path.insert(0, str(KIT / "scripts"))
from entorno import sync_playwright, launch_browser, utf8_stdio

TAGS = {"type": "a!tagField", "labelPosition": "COLLAPSED", "size": "LARGE", "tags": [
    {"type": "a!tagItem", "text": "Urgente", "backgroundColor": "TRANSPARENT", "showBorder": True, "borderColor": "NEGATIVE",
     "icon": "exclamation-triangle", "iconPosition": "END"}]}
GRAFO = {"type": "a!recordKnowledgeGraph", "label": "Relaciones", "recordType": "recordType!X Caso", "recordIdentifier": 1,
         "relationshipLevel": 2, "enableLevelSlider": True, "selectionSaveInto": "local!nodo",
         "$root": {"recordType": "Caso", "name": "C-1"},
         "$nodes": [{"recordType": "Sede", "name": "Norte", "id": 7}, {"recordType": "Sede", "name": "Norte", "id": 8}, {"recordType": "Parte", "name": "P-9"},
                    {"recordType": "Proveedor", "name": "Prov SA", "parent": "P-9"}]}
ELEGIDO = {"type": "a!textField", "label": "Elegido", "readOnly": True,
           "value": "{local!nodo.recordTypePluralName}|{local!nodo.recordTitle}|{local!nodo.recordIdentifier}"}


def chat(mostrar):
    n = {"type": "a!agentChatField", "title": "Asistente", "height": "SHORT", "showSessionPicker": False,
         "$replies": [{"text": "Hecho.", "tools": [{"tool": "Buscar casos", "text": "2 resultados"}]}]}
    if mostrar is not None:
        n["showReasoning"] = mostrar
    return n


def spec(version):
    return {"app": {"name": "Prueba 26.10", "language": "es", "today": "2026-11-06", "appianVersion": version},
            "site": {"displayName": "Prueba", "home": "p", "pages": [{"title": "P", "icon": "home", "screen": "p"}]},
            "requirements": [{"id": "C1", "title": "Novedades de 26.10"}],
            "screens": [{"id": "p", "title": "P", "type": "page", "pattern": "P06", "req": ["C1"],
                         "local": {"local!nodo": None, "local!importe": 12.5, "local!grande": None, "local!km": None},
                         "interface": {"type": "a!headerContentLayout", "contentsWidth": "NARROW",
                                       "footer": {"type": "a!cardLayout", "contents": [
                                           {"type": "a!richTextDisplayField", "labelPosition": "COLLAPSED", "value": [
                                               {"type": "a!richTextItem", "text": "Pie"}]}]},
                                       "contents": [{"type": "a!decimalField", "label": "Importe", "value": "local!importe",
                                                     "saveInto": "local!importe", "decimalType": "PRECISE"},
                                                    {"type": "a!decimalField", "label": "Grande", "value": "local!grande", "saveInto": "local!grande"},
                                                    {"type": "a!decimalField", "label": "Km", "value": "local!km", "saveInto": "local!km", "decimalType": "FLOATING"}]}},
                        {"id": "q", "title": "Q", "type": "page", "pattern": "P06", "req": ["C1"],
                         "local": {"local!nodo": None},
                         "interface": {"type": "a!headerContentLayout",
                                       "contents": [TAGS, GRAFO, ELEGIDO, chat(False), chat(None)]}},
                        {"id": "r", "title": "R", "type": "page", "pattern": "P06", "req": ["C1"],
                         "local": {"local!nodo": {"recordTypeReference": "recordType!Sede", "recordTypePluralName": "Sede",
                                                  "recordTitle": "Norte", "recordIdentifier": 8}},
                         "interface": {"type": "a!headerContentLayout", "contents": [GRAFO]}}]}


def main():
    utf8_stdio()
    fallos = []
    with tempfile.TemporaryDirectory() as tmp:
        carpeta = pathlib.Path(tmp)
        # 1. Con 26.9 declarada, cada novedad es un error que dice su versión
        viejo = carpeta / "v269.json"
        viejo.write_text(json.dumps(spec("26.9")), encoding="utf-8")
        r = subprocess.run([sys.executable, str(KIT / "scripts/validate.py"), str(viejo)], capture_output=True, encoding="utf-8")
        salida = r.stdout + r.stderr
        for clave in ("a!decimalField requiere", "a!headerContentLayout.contentsWidth requiere", "a!headerContentLayout.footer requiere",
                      "a!tagField.size \"LARGE\" requiere", "a!tagItem.showBorder requiere", "a!tagItem.borderColor requiere",
                      "a!tagItem.icon requiere", "a!tagItem.iconPosition requiere", "a!tagItem.backgroundColor \"TRANSPARENT\" requiere",
                      "a!recordKnowledgeGraph.enableLevelSlider requiere", "a!recordKnowledgeGraph.selectionSaveInto requiere",
                      "a!agentChatField.showReasoning requiere"):
            if f"{clave} Appian 26.10" not in salida:
                fallos.append(f"con 26.9 falta el error «{clave} Appian 26.10»")
        if r.returncode == 0:
            fallos.append("con 26.9 la validación no falla")
        # 2. Con 26.10, se construye y se comporta como dice la documentación
        nuevo, html = carpeta / "app.json", carpeta / "prototipo.html"
        nuevo.write_text(json.dumps(spec("26.10")), encoding="utf-8")
        r = subprocess.run([sys.executable, str(KIT / "scripts/build.py"), str(nuevo), "-o", str(html)], capture_output=True, encoding="utf-8")
        if r.returncode:
            raise AssertionError(r.stdout + r.stderr)
        with sync_playwright() as p:
            navegador = launch_browser(p)
            pg = navegador.new_page(viewport={"width": 1280, "height": 900})
            pg.goto(html.as_uri())
            pg.wait_for_function("window.PROTO && window.PROTO.ready")
            # cabecera: contenido estrecho y pie abajo del todo con poco contenido
            pg.evaluate("PROTO.show('p', {})")
            pg.wait_for_timeout(200)
            cab = pg.evaluate("""() => { const c = document.querySelector('.hcl-contents'), f = document.querySelector('.hcl-footer');
              return { ancho: getComputedStyle(c).maxWidth, clase: c.className, pie: f ? Math.round(innerHeight - f.getBoundingClientRect().bottom) : null,
                       numero: document.querySelector('input.inp[type=number]') ? document.querySelector('input.inp[type=number]').step : null }; }""")
            if cab["ancho"] != "720px":
                fallos.append(f"contentsWidth NARROW no limita el contenido a 720px: {cab}")
            if cab["pie"] is None or abs(cab["pie"]) > 2:
                fallos.append(f"el footer no queda abajo con poco contenido: {cab}")
            if cab["numero"] != "any":
                fallos.append(f"a!decimalField no es un campo numérico con decimales: {cab}")
            # PRECISE (aquí, por defecto) conserva las cifras; FLOATING guarda un número
            for etiqueta, escrito in (("Grande", "9007199254740993"), ("Km", "124.6")):
                campo = pg.get_by_label(etiqueta, exact=True)
                campo.fill(escrito)
                campo.dispatch_event("change")
                pg.wait_for_timeout(150)
                visto = pg.get_by_label(etiqueta, exact=True).input_value()
                if visto != escrito:
                    fallos.append(f"a!decimalField «{etiqueta}»: se escribió {escrito} y muestra {visto}")
            pg.evaluate("PROTO.show('q', {})")
            pg.wait_for_timeout(200)
            # etiqueta LARGE con borde por dentro e icono al final
            tag = pg.evaluate("""() => { const t = document.querySelector('.tags.z-LARGE .tag'); if (!t) return null;
              return { borde: getComputedStyle(t).boxShadow, letra: getComputedStyle(t).fontSize, ultimo: t.lastElementChild && t.lastElementChild.className,
                       fondo: getComputedStyle(t).backgroundColor }; }""")
            if not tag or "inset" not in tag["borde"] or tag["letra"] != "14px" or tag["ultimo"] != "tag-ic" or tag["fondo"] != "rgba(0, 0, 0, 0)":
                fallos.append(f"etiqueta 26.10 mal pintada: {tag}")
            # grafo: nivel 1 al empezar, 2 con el control, y el registro pulsado se guarda
            nodos = lambda: pg.evaluate("document.querySelectorAll('.kg-n:not(.main)').length")
            n1 = nodos()
            pg.eval_on_selector(".kg-lv input", "el => { el.value = 2; el.dispatchEvent(new Event('input', {bubbles: true})); }")
            pg.wait_for_timeout(200)
            n2 = nodos()
            if (n1, n2) != (3, 4):
                fallos.append(f"enableLevelSlider: nodos {n1} en el nivel 1 y {n2} en el 2 (se esperaban 3 y 4)")
            elegido = lambda: pg.evaluate("() => [...document.querySelectorAll('.fld')].map(e => e.textContent).find(t => t.includes('Elegido'))") or ""
            pg.locator(".kg-n:not(.main)", has_text="Norte").first.click()
            pg.wait_for_timeout(200)
            if "Sede|Norte|7" not in elegido():
                fallos.append(f"selectionSaveInto no guarda tipo, título e identificador: «{elegido()}»")
            marcados = pg.evaluate("document.querySelectorAll('.kg-n.sel').length")
            if marcados != 1:
                fallos.append(f"selectionSaveInto: {marcados} nodos marcados al pulsar uno de dos que se llaman igual")
            pg.click(".kg-n.main")
            pg.wait_for_timeout(200)
            if "Caso|C-1|1" not in elegido():
                fallos.append(f"selectionSaveInto en la raíz sin $root.id: no guarda su recordIdentifier: «{elegido()}»")
            # estado guardado sin pulsar (como en una captura): solo el nodo con ese id sale marcado
            pg.evaluate("PROTO.show('r', {})")
            pg.wait_for_timeout(200)
            sel = pg.evaluate("() => [...document.querySelectorAll('.kg-n:not(.main)')].map((e, i) => e.classList.contains('sel') ? i : -1).filter(i => i >= 0)")
            if sel != [1]:
                fallos.append(f"selectionSaveInto: con Sede Norte id 8 guardado, salen marcados los nodos {sel} (se esperaba [1])")
            pg.evaluate("PROTO.show('q', {})")
            pg.wait_for_timeout(200)
            # chat: con showReasoning false la acción desaparece al terminar; por defecto se queda
            for i, queda in ((0, False), (1, True)):
                caso = f"showReasoning {'por defecto' if queda else 'false'}"
                caja = pg.locator(".aic").nth(i)
                caja.locator(".aic-in input").fill("¿Qué casos hay?")
                caja.locator(".aic-in input").press("Enter")
                try:
                    caja.locator(".cm.tool").first.wait_for(timeout=5000)
                except Exception:
                    fallos.append(f"{caso}: la acción no se ve mientras se hace")
                pg.wait_for_function("(i) => !document.querySelectorAll('.aic')[i].querySelector('.typing')", arg=i, timeout=10000)
                hay = caja.locator(".cm.tool").count()
                if (hay > 0) != queda:
                    fallos.append(f"{caso}: {hay} acciones a la vista al terminar")
            navegador.close()
    if fallos:
        print("\n".join(fallos))
        return 1
    print("Novedades de 26.10: bien")
    return 0


if __name__ == "__main__":
    sys.exit(main())
