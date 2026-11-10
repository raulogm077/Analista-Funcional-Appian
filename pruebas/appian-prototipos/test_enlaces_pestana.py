"""Enlaces #ver: nueva pestaña, parámetros, recarga, fragmentos e historial sin datos de cliente."""
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


def app():
    def link(label, **attrs):
        return {"type": "a!linkField", "links": [{"type": "a!safeLink", "label": label, **attrs}]}
    def action(label, act):
        return {"type": "a!linkField", "links": [{"type": "a!dynamicLink", "label": label, "$action": act}]}
    def screen(id_, title, contents, **more):
        return {"id": id_, "title": title, "type": "page", "pattern": "P11", "req": ["R1"],
                "interface": {"type": "a!headerContentLayout", "contents": [
                    {"type": "a!headingField", "text": title, "headingTag": "H1"}, *contents]}, **more}
    uri = "#ver=detalle&id=7&codigo={local!codigo}&texto={local!texto}&grande=9007199254740993"
    return {"app": {"name": "Enlaces de prueba", "language": "es", "appianVersion": "26.9"},
            "site": {"displayName": "Prueba", "home": "inicio", "pages": [{"title": "Inicio", "screen": "inicio"}]},
            "requirements": [{"id": "R1", "text": "Consultar una pantalla en otra pestaña sin perder sus parámetros"}],
            "screens": [screen("inicio", "Inicio", [
                link("Abrir pestaña", uri=uri, openLinkIn="NEW_TAB"),
                link("Abrir aquí", uri=uri, openLinkIn="SAME_TAB"),
                action("Ir normal", {"goto": "otra", "params": {"id": 9}}),
                link("Destino inexistente", uri="#ver=constructor", openLinkIn="NEW_TAB")],
                local={"local!codigo": "007", "local!texto": "A&B=dos + café/東京#fin"}),
                screen("detalle", "Detalle", [
                    {"type": "a!textField", "label": "Identificador", "value": "ri!id", "readOnly": True},
                    {"type": "a!textField", "label": "Código", "value": "ri!codigo", "readOnly": True},
                    {"type": "a!textField", "label": "Texto", "value": "ri!texto", "readOnly": True},
                    action("Otra pantalla", {"goto": "otra", "params": {"id": 9}})]),
                screen("otra", "Otra", [action("Volver", {"back": True})])], "data": {}}


def main():
    utf8_stdio()
    evidencia = pathlib.Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else None
    if evidencia:
        evidencia.mkdir(parents=True, exist_ok=True)
    casos, errores = [], []
    with tempfile.TemporaryDirectory() as tmp, sync_playwright() as p:
        carpeta = pathlib.Path(tmp)
        spec, html = carpeta / "app.json", carpeta / "prototipo.html"
        spec.write_text(json.dumps(app(), ensure_ascii=False), encoding="utf-8")
        r = subprocess.run([sys.executable, str(KIT / "scripts/build.py"), str(spec), "-o", str(html)],
                           capture_output=True, encoding="utf-8")
        assert r.returncode == 0, r.stdout + r.stderr
        navegador = launch_browser(p)
        ctx = navegador.new_context(viewport={"width": 1100, "height": 800})
        ctx.on("page", lambda pg: pg.on("pageerror", lambda e: errores.append(str(e))))
        pagina = ctx.new_page()
        pagina.goto(html.as_uri())
        pagina.get_by_role("heading", name="Inicio", exact=True).wait_for()
        with ctx.expect_page() as nueva:
            pagina.get_by_text("Abrir pestaña", exact=True).click()
        abierta = nueva.value
        abierta.get_by_role("heading", name="Detalle", exact=True).wait_for()
        esperado = {"id": 7, "codigo": "007", "texto": "A&B=dos + café/東京#fin", "grande": "9007199254740993"}
        def parametros(pg):
            return pg.evaluate("Object.fromEntries(Object.entries(PROTO.state).filter(([k]) => k.startsWith('ri!')).map(([k,v]) => [k.slice(3),v]))")
        assert parametros(abierta) == esperado, parametros(abierta)
        assert abierta.evaluate("window.opener === null")
        assert pagina.get_by_role("heading", name="Inicio", exact=True).is_visible()
        assert "%26" in abierta.url and "%3D" in abierta.url and "%2B" in abierta.url
        casos.append("nueva pestaña, origen intacto, noopener y parámetros escapados sin perder identidad")
        abierta.reload()
        abierta.get_by_role("heading", name="Detalle", exact=True).wait_for()
        assert parametros(abierta) == esperado
        casos.append("recarga conserva pantalla y parámetros")
        abierta.get_by_text("Otra pantalla", exact=True).click()
        abierta.get_by_role("heading", name="Otra", exact=True).wait_for()
        assert parametros(abierta) == {"id": 9}
        abierta.get_by_text("Volver", exact=True).click()
        assert parametros(abierta) == esperado, parametros(abierta)
        casos.append("goto y back internos restauran los parámetros de la pantalla")
        abierta.evaluate("location.hash = '#ver=otra&id=-3'")
        abierta.get_by_role("heading", name="Otra", exact=True).wait_for()
        assert parametros(abierta) == {"id": -3}
        abierta.go_back()
        abierta.get_by_role("heading", name="Detalle", exact=True).wait_for()
        assert parametros(abierta) == esperado
        casos.append("hashchange y atrás del navegador restauran el enlace")
        abierta.evaluate("location.hash = '#ver=detalle&__proto__=dato&constructor=otro&ready=no&id=0'")
        abierta.wait_for_function("PROTO.state['ri!id'] === 0")
        assert abierta.evaluate("Object.getPrototypeOf(PROTO.state) === Object.prototype && Object.prototype.dato === undefined && PROTO.ready === true")
        assert abierta.evaluate("[PROTO.state['ri!__proto__'], PROTO.state['ri!constructor'], PROTO.state['ri!ready']]") == ["dato", "otro", "no"]
        casos.append("parámetros con nombres internos quedan aislados como ri!")
        for fragmento in ("#ver=constructor", "#ver=ausente", "#%E0%A4%A"):
            abierta.evaluate("h => location.hash = h", fragmento)
            abierta.wait_for_timeout(40)
            assert abierta.get_by_role("heading", name="Detalle", exact=True).is_visible()
        casos.append("destino desconocido y fragmento malformado no rompen la pantalla actual")
        abierta.goto(html.as_uri() + "#detalle")
        abierta.get_by_role("heading", name="Detalle", exact=True).wait_for()
        casos.append("enlace legacy #pantalla sigue funcionando")
        pagina.get_by_text("Abrir aquí", exact=True).click()
        pagina.get_by_role("heading", name="Detalle", exact=True).wait_for()
        assert len(ctx.pages) == 2 and parametros(pagina) == esperado
        pagina.go_back()
        pagina.get_by_role("heading", name="Inicio", exact=True).wait_for()
        pagina.get_by_text("Ir normal", exact=True).click()
        pagina.get_by_role("heading", name="Otra", exact=True).wait_for()
        assert len(ctx.pages) == 2 and parametros(pagina) == {"id": 9}
        pagina.get_by_text("Volver", exact=True).click()
        pagina.get_by_role("heading", name="Inicio", exact=True).wait_for()
        pagina.get_by_text("Destino inexistente", exact=True).click()
        assert len(ctx.pages) == 2
        casos.append("SAME_TAB y goto no abren pestañas; enlace inválido no abre otra")
        assert not errores, errores
        if evidencia:
            abierta.goto(html.as_uri() + "#ver=detalle&id=7&codigo=007&texto=Caf%C3%A9%20%26%20consulta")
            abierta.get_by_role("heading", name="Detalle", exact=True).wait_for()
            abierta.screenshot(path=str(evidencia / "enlace-destino.png"))
            (evidencia / "enlaces-resultados.json").write_text(json.dumps({"casos": casos, "erroresJS": errores}, ensure_ascii=False, indent=2), encoding="utf-8")
        navegador.close()
    print("\n".join("✓ " + c for c in casos))
    print(f"{len(casos)} casos, 0 errores JavaScript")


if __name__ == "__main__":
    main()
