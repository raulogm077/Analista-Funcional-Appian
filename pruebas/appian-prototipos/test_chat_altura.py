"""Prueba visual del chat FILL en un panel, directo y dentro de una tarjeta."""
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


def main():
    utf8_stdio()
    evidencia = pathlib.Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else None
    if evidencia:
        evidencia.mkdir(parents=True, exist_ok=True)
    fallos, medidas = [], []
    with tempfile.TemporaryDirectory() as tmp, sync_playwright() as p:
        carpeta = pathlib.Path(tmp)
        navegador = launch_browser(p)
        pagina = navegador.new_page()
        for tarjeta in (False, True):
            app = json.loads((KIT / "galerias/ia/app.json").read_text(encoding="utf-8"))
            chat = {"type": "a!agentChatField", "title": "Asistente", "height": "FILL",
                    "welcomeMessage": "Consulta el estado de tus solicitudes.", "$replies": ["Respuesta de prueba."]}
            contenido = {"type": "a!cardLayout", "contents": [chat]} if tarjeta else chat
            app["screens"][0]["interface"] = {"type": "a!paneLayout", "panes": [{"type": "a!pane",
                "contents": [{"type": "a!headingField", "text": "Consultas", "size": "MEDIUM"}, contenido]}]}
            spec, html = carpeta / "app.json", carpeta / "prototipo.html"
            spec.write_text(json.dumps(app), encoding="utf-8")
            r = subprocess.run([sys.executable, str(KIT / "scripts/build.py"), str(spec), "-o", str(html)],
                               capture_output=True, encoding="utf-8")
            if r.returncode:
                raise AssertionError(r.stdout + r.stderr)
            for ancho, alto in ((1280, 720), (1280, 500), (390, 844)):
                pagina.set_viewport_size({"width": ancho, "height": alto})
                pagina.goto(html.as_uri())
                pagina.locator(".pane .aic").wait_for()
                pagina.evaluate("document.fonts.ready")
                pagina.evaluate("dispatchEvent(new Event('resize'))")
                pagina.wait_for_timeout(150)
                estado = pagina.evaluate("""() => {
                  const c = document.querySelector('.pane .aic'), p = c.closest('.pane');
                  const chat = c.getBoundingClientRect(), pane = p.getBoundingClientRect();
                  const entrada = c.querySelector('.aic-in').getBoundingClientRect();
                  const libres = [...c.querySelectorAll('.aic-in input,.aic-in textarea,.aic-in button')].every(e => {
                    const r = e.getBoundingClientRect(), encima = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
                    return encima && (encima === e || e.contains(encima));
                  });
                  return {chatTop: chat.top, chatBottom: chat.bottom, paneBottom: pane.bottom,
                    inputBottom: entrada.bottom, viewport: innerHeight, scroll: p.scrollHeight - p.clientHeight,
                    padding: parseFloat(getComputedStyle(p).paddingBottom), controlesLibres: libres,
                    barraTop: document.querySelector('.px-bar').getBoundingClientRect().top,
                    layoutHeight: c.closest('.pane-layout').style.height};
                }""")
                etiqueta = f"{'tarjeta' if tarjeta else 'directo'}-{ancho}x{alto}"
                medidas.append({"caso": etiqueta, **estado})
                if estado["inputBottom"] > alto + 1 or estado["scroll"] > 1:
                    fallos.append(f"{etiqueta}: entrada fuera del panel o scroll exterior: {estado}")
                if not estado["controlesLibres"] or estado["inputBottom"] > estado["barraTop"]:
                    fallos.append(f"{etiqueta}: la barra tapa el input o el botón enviar: {estado}")
                if abs(estado["chatBottom"] - (estado["paneBottom"] - estado["padding"])) > (16 if tarjeta else 1):
                    fallos.append(f"{etiqueta}: chat no ocupa el alto disponible: {estado}")
                if evidencia:
                    pagina.screenshot(path=str(evidencia / (etiqueta + ".png")))
                pagina.add_style_tag(content=".px-bar { display: none !important; }")
                pagina.evaluate("dispatchEvent(new Event('resize'))")
                pagina.wait_for_function("Math.abs(document.querySelector('.pane').getBoundingClientRect().bottom - innerHeight) < 1")
                medidas[-1]["sinBarraHastaViewport"] = True
        navegador.close()
    if evidencia:
        (evidencia / "medidas.json").write_text(json.dumps(medidas, indent=2), encoding="utf-8")
    print(json.dumps(medidas, ensure_ascii=False))
    if fallos:
        print("\n".join(fallos))
        return 1
    print("✓ Chat: seis combinaciones de contenedor y viewport, entrada visible y alto completo")
    return 0


if __name__ == "__main__":
    sys.exit(main())
