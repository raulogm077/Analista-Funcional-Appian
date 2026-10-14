#!/usr/bin/env python3
"""Un SAIL CLI de mentira para el selftest de appian-qa: contesta con un --json como el de SAIL CLI 26.6.110 (status,
site, page, options con ref, label, verb, handles…, ui, validations; tras enviar un formulario, completed, processId y
viewIsStale con la página de antes) y, con un error, un texto en la salida de error y el código 1, como el de verdad.

La aplicación es una de solicitudes: un gestor las da de alta y las ve solo suyas; un revisor ve todas menos los
borradores y devuelve las enviadas. Su estado está en el fichero de SAIL_SIMULADO_APP:
  {"filas": [{"Número", "Título", "Estado", "solicitante", "comentario"}], "defecto": {…}, "cargas": n}
  defecto "estado_alta": el estado con el que queda una solicitud enviada (en vez de «Enviada»)
  defecto "lento": una solicitud nueva no sale en la primera carga del panel (el proceso aún no ha terminado)
  defecto "cuelga_desde": n, desde la llamada n (contando desde 1) SAIL CLI no responde
  defecto "sin_red": SAIL CLI no llega al servidor (el error de Go sin DNS)
  defecto "lee_stdin": SAIL CLI lee su entrada antes de nada (si se la dejan abierta, espera)
El panel lleva dos enlaces «Ver detalle», que el --json da con nth y of: no se distinguen.
La sesión de cada cuenta, en su --data-dir: session.json ({"hostname", "username", "cookies"}; con "caducada": true, la
del servidor ya no vale) y la página en la que está (pagina.json).
"""
import json
import os
import pathlib
import secrets
import sys
import time

BOTONES = {"Enviar", "Guardar borrador", "Devolver", "Aprobar", "Cancelar"}
COLUMNAS = ["Número", "Título", "Importe", "Estado"]


def sale(d):
    print(json.dumps(d, ensure_ascii=False, indent=2))
    sys.exit(0)


def error(texto):
    print("error: " + texto, file=sys.stderr)
    sys.exit(1)


def lee(f, defecto):
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return defecto


def guarda(f, d):
    with open(f, "w", encoding="utf-8", newline="\n") as s:
        s.write(json.dumps(d, ensure_ascii=False, indent=1))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = sys.argv[1:]
    carpeta = None
    if "--data-dir" in args:
        k = args.index("--data-dir")
        carpeta = pathlib.Path(args[k + 1])
        del args[k:k + 2]
    args = [a for a in args if a not in ("--json", "--confirm")]
    fresh = "--fresh" in args
    args = [a for a in args if a != "--fresh"]
    orden, site, resto = args[0], args[1], args[2:]
    sesion = lee(carpeta / "session.json", None) if carpeta else None
    if not sesion:
        error('no session found; run "sail login <hostname>" first')
    if sesion.get("caducada"):
        error(f'could not read the navigation for site "{site}" (status 401): {{"error":"APNX-1-4187-000","message":'
              '"Authentication failed. Please check your credentials and try again."}')
    usuario = sesion["username"]
    revisor = "revisor" in usuario
    fapp = pathlib.Path(os.environ["SAIL_SIMULADO_APP"])
    app = lee(fapp, {"filas": []})
    app.setdefault("filas", [])
    defecto = app.get("defecto") or {}
    app["llamadas"] = app.get("llamadas", 0) + 1
    guarda(fapp, app)
    if defecto.get("lee_stdin"):
        sys.stdin.read()
    if defecto.get("cuelga_desde") and app["llamadas"] >= defecto["cuelga_desde"]:
        time.sleep(30)
    if defecto.get("sin_red"):
        error(f'Post "https://{sesion["hostname"]}/suite/rest/a/sites/latest/{site}/nav": dial tcp: lookup '
              f'{sesion["hostname"]}: no such host')
    fpag = carpeta / "pagina.json"
    pag = lee(fpag, {"pagina": "panel", "campos": {}, "seleccion": None, "busqueda": ""})

    def visibles():
        filas = [f for f in app["filas"] if (f["Estado"] != "Borrador" if revisor else f["solicitante"] == usuario)
                 and not f.get("oculta")]
        return [f for f in filas if pag["busqueda"].casefold() in f["Título"].casefold()]

    def panel():
        filas = visibles()
        opciones = [{"group": "Solicitudes", "id": secrets.token_hex(16), "label": "Estado", "ref": "Estado",
                     "verb": "indexes", "options": ["Borrador", "Enviada", "Devuelta"]},
                    # como «En riesgo (22)» en un panel de verdad: lleva un dato y su ref es la de esta carga
                    {"id": (i := secrets.token_hex(16)), "ref": i, "refIsPerRender": True, "nth": 1, "of": 2,
                     "label": f"Pendientes ({len(filas)})", "value": f"Pendientes ({len(filas)})", "verb": "display"}]
        opciones += [{"label": "Ver detalle", "ref": f"⌗ Ver detalle {n}", "nth": n, "of": 2, "verb": "click"}
                     for n in (1, 2)]
        if not revisor:
            opciones.append({"group": "Solicitudes", "label": "Nueva solicitud", "navKind": "StartProcessLink",
                             "ref": "⤴ Nueva solicitud", "verb": "navigate"})
        sel = next((f for f in filas if f["Número"] == pag["seleccion"]), None)
        if sel and revisor and sel["Estado"] == "Enviada":
            opciones.append({"group": "Solicitudes", "label": "Revisar", "navKind": "RelatedActionLink",
                             "ref": "⤴ Revisar", "verb": "navigate"})
        marca = lambda f: ("☑ " if f["Número"] == pag["seleccion"] else "☐ ") + f["Número"]
        opciones.append({"group": "Solicitudes", "id": secrets.token_hex(16), "label": "Solicitudes", "ref": "Solicitudes",
                         "verb": "grid", "handles": [f"⇅ {c}" for c in COLUMNAS] + [marca(f) for f in filas] + ["🔍"],
                         "value": f"showing 1-{len(filas)} of {len(filas)}"})
        ui = {"#t": "ContentLayout", "contents": [
            {"#t": "Heading", "text": "Panel de solicitudes", "testLabel": "heading-Panel"},
            {"#t": "PagingGridLayout", "_cId": secrets.token_hex(16), "columns": COLUMNAS,
             "emptyGridMessage": "No hay solicitudes", "totalCount": len(filas),
             # como la de verdad: una rejilla vacía no trae «rows»
             **({"rows": [{**{c: f.get(c, "–") for c in COLUMNAS}, "handle": marca(f)} for f in filas]} if filas else {})},
            {"#t": "SearchBoxWidget", "value": pag["busqueda"], "placeholder": "Search Solicitudes"}]}
        return {"status": "ok", "site": site, "page": "panel", "options": opciones, "ui": ui, "validations": None}

    def formulario():
        c = pag["campos"]
        if pag["pagina"] == "alta":
            campos = [("Título", "text"), ("Importe (€)", "text")]
            botones = ["Enviar", "Guardar borrador", "Cancelar"]
        else:
            campos = [("Comentario", "text")]
            botones = ["Devolver", "Aprobar", "Cancelar"]
        opciones = [{"group": "Datos", "id": secrets.token_hex(16), "label": n, "ref": n, "verb": v,
                     **({"value": c[n]} if c.get(n) else {})} for n, v in campos]
        opciones += [{"id": secrets.token_hex(16), "label": b, "ref": b, "verb": "click"} for b in botones]
        datos = []
        if pag["pagina"] == "revision":
            f = next(f for f in app["filas"] if f["Número"] == pag["seleccion"])
            datos = [{"#t": "TextField", "label": "Título", "value": f["Título"], "readOnly": True}]
        ui = {"#t": "FormLayout", "contents": datos + [{"#t": "TextField", "_cId": o["id"], "label": o["label"],
                                                        "value": c.get(o["label"], "")} for o in opciones[:len(campos)]],
              "validations": [{"message": m} for m in pag.get("validaciones", [])]}
        return {"status": "ok", "site": site, "options": opciones, "ui": ui,
                "validations": pag.get("validaciones") or None}

    def pagina():
        return panel() if pag["pagina"] == "panel" else formulario()

    def fin(d, **mas):
        guarda(fpag, pag)
        guarda(fapp, app)
        sale({**d, **mas})

    if orden == "load":
        if pag["campos"] and not fresh:
            error(f'site "{site}" has values entered that a load would discard; pass --fresh to start over, or "sail show"')
        app["cargas"] = app.get("cargas", 0) + 1
        for f in app["filas"]:      # «lento»: la solicitud nueva aparece en la segunda carga
            if f.get("oculta"):
                f["oculta"] -= 1
        pag.update(pagina="panel", campos={}, seleccion=None, busqueda="", validaciones=[])
        fin(panel())
    if orden == "show":
        fin(pagina())
    if orden == "back":
        pag.update(pagina="panel", campos={}, validaciones=[])
        fin(pagina(), location="site page panel")
    if orden in ("navigate", "nav"):
        destino = resto[0].lstrip("⤴ ").strip()
        disponibles = [o["label"] for o in pagina()["options"] if o.get("verb") == "navigate"]
        if destino.casefold() not in [x.casefold() for x in disponibles]:
            error(f'no navigation target matches "{resto[0]}"; available: ' + ", ".join(f'"{x}"' for x in disponibles))
        pag.update(pagina="alta" if destino.casefold() == "nueva solicitud" else "revision", campos={}, validaciones=[])
        fin(pagina(), kind="navigate", navigated=destino)
    if orden != "interact":
        error(f'unknown command "{orden}" for "sail"')
    actual = pagina()
    refs = [o["ref"] for o in actual["options"]] + [h for o in actual["options"] for h in o.get("handles", [])]
    pares, k = [], 0
    while k < len(resto):
        objetivo = resto[k]
        if objetivo not in refs and not any(r.casefold().startswith(objetivo.casefold()) for r in refs):
            error(f'no component matches "{objetivo}" in site "{site}", and <value> is missing.\ninteractive components: '
                  + ", ".join(f'"{r}"' for r in refs))
        sin_valor = objetivo in BOTONES or objetivo[:1] in "☐☑"
        pares.append((objetivo, None if sin_valor else resto[k + 1] if k + 1 < len(resto) else ""))
        k += 1 if sin_valor else 2
    antes, cambia = panel() if pag["pagina"] != "panel" else None, False
    for objetivo, valor in pares:
        if objetivo == "🔍":
            cambia, pag["busqueda"] = cambia or pag["busqueda"] != valor, valor
        elif objetivo[:1] in "☐☑":
            pag["seleccion"], cambia = (None if objetivo[:1] == "☑" else objetivo[2:]), True
        elif valor is not None:
            cambia = cambia or pag["campos"].get(objetivo, "") != valor
            pag["campos"][objetivo] = valor
        elif objetivo == "Enviar":
            if not pag["campos"].get("Título"):
                pag["validaciones"] = ["Indica el título y el importe"]
                fin(formulario(), changedFields=[{"key": "validations"}])
            n = len(app["filas"]) + 1
            app["filas"].insert(0, {"Número": f"SIM-{n:04d}", "Título": pag["campos"]["Título"],
                                    "Importe": pag["campos"].get("Importe (€)", ""),
                                    "Estado": defecto.get("estado_alta", "Enviada"), "solicitante": usuario,
                                    **({"oculta": 2} if defecto.get("lento") else {})})
            pag.update(pagina="panel", campos={}, validaciones=[])
            fin(antes, completed="start form: Nueva solicitud", processId=str(n), location="site page panel",
                viewIsStale=True, viewStaleReason="the page below is as it was before the form opened")
        elif objetivo == "Devolver":
            f = next(f for f in app["filas"] if f["Número"] == pag["seleccion"])
            f.update(Estado="Devuelta", comentario=pag["campos"].get("Comentario", ""))
            pag.update(pagina="panel", campos={}, validaciones=[])
            fin(antes, completed="related action: Revisar", processId="99", location="site page panel",
                viewIsStale=True, viewStaleReason="the page below is as it was before the form opened")
    resultado = pagina()
    if not cambia:
        resultado["movedNothing"] = True
    fin(resultado, changedFields=[] if not cambia else [{"key": "value"}])


if __name__ == "__main__":
    main()
