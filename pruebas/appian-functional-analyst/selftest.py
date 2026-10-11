#!/usr/bin/env python3
"""Prueba automática de la skill del analista. Usa los proyectos ficticios de datos/: autorizaciones/ (nuevo) y
evolutivo/ (sobre una aplicación existente, con as-is/ y una propuesta de refactorización).

  python3 pruebas/appian-functional-analyst/selftest.py

Prueba la skill de $PLUGIN_A_PROBAR/skills/appian-functional-analyst (por defecto, la de este repositorio).
Comprueba los scripts del análisis (proyecto, índice, comprobación, actualización con informe de
impacto, unión de módulos y lectura de fuentes) y, si están instalados, el Word (Node con docx) y los
diagramas de estados (Playwright). Sale con 1 si algo falla.
"""
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

sys.dont_write_bytecode = True  # importa un módulo de la skill (redaccion): sin __pycache__ en el plugin
AQUI = pathlib.Path(__file__).resolve().parent
PLUGIN = pathlib.Path(os.environ.get("PLUGIN_A_PROBAR") or AQUI.parents[1]).resolve()
SKILL = PLUGIN / "skills" / "appian-functional-analyst"
S = SKILL / "scripts"
DATOS = AQUI / "datos"
EJEMPLO = DATOS / "autorizaciones"
EVOLUTIVO = DATOS / "evolutivo"     # una aplicación existente (as-is/ de DEM, del simulador) con una propuesta
fallos = []


def corre(*args, entrada=None, env=None):
    r = subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True, input=entrada,
                       env={**os.environ, **env} if env else None, encoding="utf-8", errors="replace")
    return r.returncode, r.stdout + r.stderr


def ok(nombre, cond, detalle=""):
    print(("✓ " if cond else "✗ ") + nombre + ("" if cond else f"\n    {detalle[-800:]}"))
    if not cond:
        fallos.append(nombre)


def editar(ruta, viejo, nuevo):
    t = ruta.read_text(encoding="utf-8")
    assert viejo in t, f"no está «{viejo[:50]}» en {ruta.name}"
    ruta.write_text(t.replace(viejo, nuevo, 1), encoding="utf-8")


def main():
    for st in (sys.stdout, sys.stderr):
        st.reconfigure(encoding="utf-8", errors="replace")
    ok("Python 3.9 o posterior", sys.version_info >= (3, 9), sys.version)
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="analista-"))
    try:
        # 1. El ejemplo está bien
        c, out = corre(S / "comprobar.py", EJEMPLO)
        ok("el ejemplo pasa comprobar.py sin errores", c == 0, out)
        ok("solo avisa de las capturas que faltan", "· pantallas con su captura" in out and
           len(re.findall(r"^· ", out, re.M)) == 1, out)

        # 1b. Reglas de prosa en un solo sitio (redaccion.py, que usa también ingeniería inversa)
        sys.path.insert(0, str(S))
        try:
            import redaccion
        except ImportError as e:
            ok("redaccion.py se importa", False, repr(e))
        else:
            guia = tmp / "Carpeta con espacios" / "redaccion.md"
            guia.parent.mkdir(parents=True)
            guia.write_text("# Muletillas\n\n- «Cabe destacar» → quítalo\n- «Así mismo» → quítalo\n", encoding="utf-8")
            ok("redaccion.muletillas(ruta) las devuelve normalizadas",
               redaccion.muletillas(guia) == ["cabe destacar", "asi mismo"], str(redaccion.muletillas(guia)))
            ok("redaccion.frases y MAX_PALABRAS",
               redaccion.frases("Una frase. Otra más.") == ["Una frase.", "Otra más."] and redaccion.MAX_PALABRAS == 35)
            p25 = " ".join(f"palabra{n}" for n in range(25)) + "."
            p15 = " ".join(f"otra{n}" for n in range(15)) + "."
            rep = redaccion.parrafos_repetidos({"uno.md": f"# Uno\n\n{p25}\n\n{p15}\n",
                                                "dos.md": f"Algo distinto.\n\n{p15}\n\n{p25}\n"})
            ok("redaccion.parrafos_repetidos: el de 25 palabras en dos textos, no el de 15",
               rep == [(p25, ["uno.md", "dos.md"])], str(rep))

        # 2. Consultas
        for args, espera in [(("resumen",), "Pendiente de confirmar con el cliente: 2"),
                             (("buscar", "informe", "organismo", "-n", "3"), "HU-07"),
                             (("ficha", "HU-04", "--lineas"), "HU-04.3"),
                             (("impacto", "RB-01"), "DT-02"),
                             (("seccion", "T0", "--con", "calendario"), "Calendario laboral"),
                             (("siguientes",), "HU-12"),
                             (("derivadas",), "El anexo está al día")]:
            c, out = corre(S / "indice.py", args[0], EJEMPLO, *args[1:])
            ok(f"indice.py {' '.join(args)}", c == 0 and espera in out, out)

        # 2a. indice.py grafo escribe en el proyecto, no en la carpeta desde la que se ejecuta
        g = tmp / "grafo"
        shutil.copytree(EJEMPLO, g)
        fuera = tmp / "otra carpeta"
        fuera.mkdir()
        r = subprocess.run([sys.executable, str(S / "indice.py"), "grafo", str(g)], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", cwd=str(fuera))
        ok("indice.py grafo escribe analisis/grafo.json del proyecto y nada fuera",
           r.returncode == 0 and (g / "analisis" / "grafo.json").is_file() and not any(fuera.iterdir()), r.stdout + r.stderr)

        # 2b. Un ID de otra skill citado en su fuente («[FU-07 PAN-03]», la pantalla del prototipo) no es una
        # referencia a la pieza del análisis que se llama igual
        cita = tmp / "con cita"
        shutil.copytree(EJEMPLO, cita)
        editar(cita / "analisis" / "funcional.md", "Se aplica RB-01.\n\nSe acepta si:\n- `HU-02.1`",
               "Se aplica RB-01. La lista es la del prototipo [FU-07 PAN-03].\n\nSe acepta si:\n- `HU-02.1`")
        editar(cita / "analisis" / "funcional.md", "\n## 6.", "\nLa ayuda de la pantalla es la del prototipo [FU-07 PAN-03 · ayuda].\n\n## 6.")
        c, out = corre(S / "indice.py", "impacto", cita, "PAN-03")
        ok("indice.py impacto PAN-03 no cuenta «[FU-07 PAN-03]» (ni en una pieza ni suelto)",
           c == 0 and "HU-02" not in out and "es la del prototipo" not in out, out)
        try:
            import modelo
            sin = modelo.quita_citas("Ver PAN-03 y la del prototipo [FU-07 PAN-03] o [FU-07 00:01:00].")
            m_cita = modelo.cargar(cita)
            ok("modelo.quita_citas borra las citas y la HU-02 no cita PAN-03",
               "PAN-03" in sin and sin.count("PAN-03") == 1 and "FU-07" not in sin
               and "HU-02" not in m_cita.citada_por.get("PAN-03", set()), sin)
        except (ImportError, AttributeError) as e:
            ok("modelo.quita_citas existe", False, repr(e))

        # 2c. Guion de la próxima reunión: las PC abiertas por «A quién», de más peso a menos
        c, out = corre(S / "indice.py", "pendientes", EJEMPLO)
        grupo = out.split("## Responsable de la unidad", 1)[-1]
        ok("indice.py pendientes: PC-01 y PC-02 bajo «Responsable de la unidad», sin PC-03",
           c == 0 and "## Responsable de la unidad" in out and "PC-01" in grupo and "PC-02" in grupo
           and grupo.index("PC-01") < grupo.index("PC-02") and "PC-03" not in out
           and "5 años / 10 años" in out and "ACT-06, HU-03" in out, out)
        pend = tmp / "pendientes"
        shutil.copytree(EJEMPLO, pend)
        editar(pend / "analisis" / "funcional.md", "| ~~PC-03~~ |",
               "| PC-04 | ¿Puede una unidad retirar una solicitud ya enviada? | Sí, hasta que se revise / No | "
               "Responsable de la unidad | HU-01, HU-02, PAN-01, 6.1 <!-- ❓ FU-03 00:30:00 --> |\n| ~~PC-03~~ |")
        editar(pend / "analisis" / "funcional.md", "Se aplica RB-01.\n\nSe acepta si:\n- `HU-02.1`",
               "Se aplica RB-01. Si se puede retirar una solicitud está por decidir (pendiente: PC-04).\n\nSe acepta si:\n- `HU-02.1`")
        c, out = corre(S / "indice.py", "pendientes", pend)
        grupo = out.split("## Responsable de la unidad", 1)[-1]
        ok("indice.py pendientes: la PC-04, que afecta a más, sale la primera",
           c == 0 and "PC-04" in grupo and grupo.index("PC-04") < grupo.index("PC-01") < grupo.index("PC-02"), out)
        # Lo que el equipo tiene que decidir (T1): las filas «Decisión: Pendiente» de los informes, antes que las PC
        (pend / "impacto").mkdir(exist_ok=True)
        (pend / "impacto" / "FU-04.md").write_text(
            "# Impacto de FU-04\nAnálisis base: versión 1.1 · Estado: aplicado en 1.2; pendientes de aprobación: punto 4\n\n"
            "## Puntos\n| # | Tipo | Qué se dice | Encaja en | Cambio propuesto | Revisar también | Requiere | Decisión |\n"
            "|---|---|---|---|---|---|---|---|\n"
            "| 1 | COMPLETA | Un texto [FU-04 00:01:00] | HU-02 | HU-02 con el texto | — | — | ✔ |\n"
            "| 4 | CAMBIA | Los planos pesan más: hasta 30 MB [FU-04 00:20:10] | HU-07 | HU-07.1 a 30 MB | DOC-01 "
            "| Sí (🔒) | Pendiente |\n", encoding="utf-8")
        c, out = corre(S / "indice.py", "pendientes", pend)
        bloque = out.split("## Para decidir (equipo)", 1)[-1].split("\n## ", 1)[0]
        ok("indice.py pendientes: «Para decidir (equipo)» primero, con el punto pendiente, su cambio y el motivo",
           c == 0 and "## Para decidir (equipo)" in out and out.index("## Para decidir") < out.index("## Responsable")
           and "FU-04 · punto 4" in bloque and "hasta 30 MB" in bloque and "HU-07.1 a 30 MB" in bloque
           and "Requiere: 🔒" in bloque and "punto 1" not in bloque, out)
        (pend / "impacto" / "FU-04.md").unlink()
        # Una consola de Windows en cp1252 no rompe la salida con «≥» o «→» (indice.py escribe en UTF-8)
        editar(pend / "analisis" / "funcional.md", "Sí, hasta que se revise / No", "Sí, si faltan ≥ 2 días → retirada / No")
        for orden in (("pendientes",), ("ficha", "PC-04")):
            c, out = corre(S / "indice.py", orden[0], pend, *orden[1:], env={"PYTHONIOENCODING": "cp1252"})
            ok(f"indice.py {orden[0]} con la consola en cp1252 y una PC con «≥» y «→»",
               c == 0 and "≥ 2 días → retirada" in out, out)

        # 3. Proyecto nuevo
        nuevo = tmp / "nuevo"
        c, out = corre(S / "proyecto.py", "iniciar", nuevo, "--nombre", "Prueba", "--cliente", "Ejemplo")
        ok("proyecto.py iniciar crea la carpeta y las plantillas",
           c == 0 and (nuevo / "analisis" / "funcional.md").exists() and (nuevo / "fuentes").is_dir(), out)
        c, out = corre(S / "proyecto.py", "estado", nuevo)
        ok("proyecto.py estado", c == 0 and "versión 0.1" in out, out)

        # 3b. proyecto.py estado: cliente y marca; el DF enviado se informa; --confirmadas sin las PAN de un cambio
        # aprobado después del prototipo que se enseñó (app-vX.Y.json), leyendo todos los informes (impacto/*.md);
        # fuentes sin cambios y aprobaciones cuentan como procesadas; entregar escribe «DF entregado» y el fichero
        e = tmp / "estado"
        shutil.copytree(EJEMPLO, e)
        c, out = corre(S / "proyecto.py", "estado", e)
        ok("proyecto.py estado: cliente, sin marca y el último DF enviado sin pedir el Word",
           c == 0 and "Cliente: Organización de ejemplo · Marca: sin marca" in out
           and "último enviado 1.0 (2026-09-12), versión actual 1.1" in out and "desactualizado" not in out, out)
        (e / "prototipo").mkdir(exist_ok=True)
        (e / "prototipo" / "brand-ejemplo.json").write_text('{"id": "ejemplo"}', encoding="utf-8")
        fe = e / "analisis" / "funcional.md"
        fe.write_text(re.sub(r"(\*\*PAN-0[123] — [^*]+\*\* <!-- )✅", r"\1🔒", fe.read_text(encoding="utf-8")),
                      encoding="utf-8")
        (e / "impacto").mkdir(exist_ok=True)
        cab = "| # | Tipo | Qué se dice | Encaja en | Cambio propuesto | Revisar también | Requiere | Decisión |\n|---|---|---|---|---|---|---|---|\n"
        (e / "impacto" / "FU-04.md").write_text(
            "# Impacto de FU-04\nAnálisis base: versión 1.0 · Estado: aplicado en 1.1; pendientes de aprobación: punto 2\n\n"
            "## Puntos\n" + cab + "| 1 | CAMBIA | Sin descarga [FU-04 00:01:00] | PAN-01 | PAN-01 sin descarga | — | Sí (🔒) "
            "| ✔ FU-06 |\n| 2 | CAMBIA | Otro orden [FU-04 00:02:00] | PAN-02 | PAN-02 con otro orden | — | Sí (🔒) | Pendiente |\n",
            encoding="utf-8")
        (e / "impacto" / "URG-01.md").write_text(   # cualquier informe de impacto/, no solo los FU-nn
            "# Impacto de URG-01\nAnálisis base: versión 0.9 · Estado: aplicado en 1.0\n\n"
            "## Puntos\n" + cab + "| 1 | CAMBIA | Filtro [FU-03 00:01:00] | PAN-03 | PAN-03 con filtro | — | Sí (🔒) | ✔ |\n",
            encoding="utf-8")
        (e / "impacto" / "FU-05.md").write_text("# Impacto de FU-05\nAnálisis base: versión 1.1 · Estado: sin cambios\n",
                                                encoding="utf-8")
        (e / "fuentes").mkdir()
        for n in (5, 6, 7):
            (e / "fuentes" / f"FU-0{n}-fuente.md").write_text(f"# FU-0{n}\n", encoding="utf-8")
        c, out = corre(S / "proyecto.py", "estado", e)
        conf = next((l for l in out.splitlines() if "--confirmadas" in l), "")
        fuentes = next((l for l in out.splitlines() if l.startswith("Fuentes:")), "")
        ok("proyecto.py estado: la marca del prototipo; sin app-vX.Y.json, --confirmadas sin las PAN aprobadas de todos los informes",
           c == 0 and "Marca: prototipo/brand-ejemplo.json" in out and conf.endswith("--confirmadas PAN-02"), out)
        ok("proyecto.py estado: una fuente «sin cambios» y una aprobación citada en un informe no salen sin procesar",
           fuentes.endswith("sin procesar: FU-07"), out)
        (e / "prototipo" / "app-v1.0.json").write_text("{}", encoding="utf-8")
        c, out = corre(S / "proyecto.py", "estado", e)
        conf = next((l for l in out.splitlines() if "--confirmadas" in l), "")
        ok("proyecto.py estado: con app-v1.0.json, solo salen de --confirmadas las PAN aprobadas después de la 1.0",
           c == 0 and conf.endswith("--confirmadas PAN-02,PAN-03"), out)
        hoy = __import__("datetime").date.today().isoformat()
        (e / "entregables").mkdir(exist_ok=True)
        (e / "entregables" / "DF-Solicitudes-de-autorizacion-v1.1.docx").write_bytes(b"word")
        c, out = corre(S / "proyecto.py", "entregar", e)
        pm = (e / "proyecto.md").read_text(encoding="utf-8")
        ok("proyecto.py entregar escribe «DF entregado: <versión> · <fecha>» y el fichero en «Entregados»",
           c == 0 and f"DF entregado: 1.1 · {hoy} · Estado: en validación" in pm
           and "\nEntregados: DF-Solicitudes-de-autorizacion-v1.1.docx\n" in pm, out + pm)
        c, out = corre(S / "proyecto.py", "entregar", e)
        pm = (e / "proyecto.md").read_text(encoding="utf-8")
        ok("proyecto.py entregar otra vez: el fichero una sola vez", c == 0 and pm.count("DF-Solicitudes-de-autorizacion-v1.1") == 1,
           pm)
        c, out = corre(S / "proyecto.py", "estado", e)
        ok("proyecto.py estado tras entregar: el último enviado es la versión actual",
           c == 0 and f"último enviado 1.1 ({hoy}), versión actual 1.1" in out, out)
        c, out = corre(S / "proyecto.py", "entregar", e, "--cambio", "EV-02")
        ok("proyecto.py entregar --cambio de una unidad que no existe: error y no toca proyecto.md",
           c != 0 and "EV-02" in out and (e / "proyecto.md").read_text(encoding="utf-8") == pm, out)

        # G5: unidades de cambio, señales, técnico por unidad, derivados y urgentes
        pruebas_unidades(tmp)

        # proyecto.py version: la copia, la versión +0.1 en funcional y técnico, su fila en decisiones.md y la fuente en
        # «Fuentes procesadas»; una fuente sin catalogar o que ya tiene versión, error sin tocar nada
        pv = tmp / "version"
        shutil.copytree(EJEMPLO, pv)
        (pv / "fuentes").mkdir()
        (pv / "fuentes" / "indice.json").write_text(json.dumps({"fuentes": [
            {"id": f"FU-0{i}", "fichero": f"f{i}.txt", "tipo": "Transcripción", "detalle": "8 intervenciones",
             "fecha": "2026-09-03 10:00"} for i in (1, 2, 3)] + [
            {"id": "FU-04", "fichero": "planos.eml", "tipo": "Correo", "detalle": "correo «Tamaño de los planos»",
             "fecha": "2026-10-01 09:30"}]}), encoding="utf-8")
        antes = {x: (pv / x).read_text(encoding="utf-8") for x in ("proyecto.md", "analisis/decisiones.md")}
        for args, que in ((("FU-03",), "ya tiene versión"), (("FU-09",), "no está en fuentes")):
            c, out = corre(S / "proyecto.py", "version", pv, "--fuente", *args, "--que", "x")
            ok(f"proyecto.py version con {args[0]}: error «{que}» y nada tocado",
               c != 0 and que in out and not (pv / "versiones").exists()
               and all((pv / x).read_text(encoding="utf-8") == v for x, v in antes.items()), out)
        c, out = corre(S / "proyecto.py", "version", pv, "--fuente", "FU-04", "--que", "Planos | hasta 30 MB")
        pf, pt, pd, pp = ((pv / x).read_text(encoding="utf-8") for x in ("analisis/funcional.md", "analisis/tecnico.md",
                                                                         "analisis/decisiones.md", "proyecto.md"))
        ok("proyecto.py version: copia la 1.1, sube los dos a la 1.2, la fila de la versión y la fuente en proyecto.md",
           c == 0 and (pv / "versiones" / "v1.1" / "funcional.md").exists() and "Versión: 1.2" in pf
           and "Versión: 1.2" in pt and f"| 1.1 | 2026-09-24 | Plazos en días hábiles; recordatorio al organismo; se "
           f"quita la urgencia | FU-03 | Analista, 2026-09-24 |\n| 1.2 | {hoy} | Planos / hasta 30 MB | FU-04 | — |" in pd
           and "| FU-03 | 2026-09-23 | Seguimiento con la unidad gestora | impacto/FU-03.md | 1.1 |\n| FU-04 | 2026-10-01 | "
               "Correo «Tamaño de los planos» | impacto/FU-04.md | 1.2 |" in pp
           and "--anterior" in out and "impacto/FU-04.md" in out, out + pd + pp)
        c, out = corre(S / "proyecto.py", "version", pv, "--fuente", "FU-04", "--que", "otra vez")
        ok("proyecto.py version dos veces con la misma fuente: error, la versión sigue en 1.2",
           c != 0 and "ya tiene versión" in out and "Versión: 1.2" in (pv / "analisis" / "funcional.md").read_text(encoding="utf-8"), out)
        # sin «## Fuentes procesadas» en proyecto.md ni técnico con versión: lo dice, y solo nombra lo que sube
        pv3 = tmp / "version a medias"
        shutil.copytree(EJEMPLO, pv3)
        shutil.copytree(pv / "fuentes", pv3 / "fuentes")
        editar(pv3 / "proyecto.md", "## Fuentes procesadas", "## Otras fuentes")
        editar(pv3 / "analisis" / "tecnico.md", "Versión: 1.1", "Revisión: 1.1")
        c, out = corre(S / "proyecto.py", "version", pv3 / "analisis", "--fuente", "FU-04", "--que", "x")
        ok("proyecto.py version (también con la carpeta analisis/): sin tabla de fuentes lo dice para hacerlo a mano y "
           "sin versión en el técnico solo sube el funcional",
           c == 0 and "Versión 1.2: funcional en 1.2" in out and "a mano: FU-04 en «## Fuentes procesadas»" in out, out)
        pd2 = tmp / "version con decisiones"
        shutil.copytree(EJEMPLO, pd2)
        shutil.copytree(pv / "fuentes", pd2 / "fuentes")
        c, out = corre(S / "proyecto.py", "version", pd2, "--fuente", "FU-04", "--que", "x",
                       "--decision", "CAMBIO", "HU-07", "a", "b")
        ok("proyecto.py version --decision con un tipo que no existe: error sin tocar nada",
           c != 0 and "CAMBIO" in out and not (pd2 / "versiones").exists(), out)
        c, out = corre(S / "proyecto.py", "version", pd2, "--fuente", "FU-04", "--que", "Planos de hasta 30 MB",
                       "--decision", "CAMBIA", "HU-07", "Los planos, hasta 30 MB", "Hasta 20 MB [FU-01 00:20:10]",
                       "--decision", "RESPONDE", "PC-03", "Lo firma el responsable", "—")
        dd = (pd2 / "analisis" / "decisiones.md").read_text(encoding="utf-8")
        ok("proyecto.py version --decision: una fila D por punto, numeradas tras las que hay, con la fecha y la fuente",
           c == 0 and "| D-03 | 2026-10-01 | FU-04 | CAMBIA | Los planos, hasta 30 MB | Hasta 20 MB [FU-01 00:20:10] | "
           "HU-07 | Sí |" in dd and "| D-04 | 2026-10-01 | FU-04 | RESPONDE | Lo firma el responsable | — | PC-03 | Sí |" in dd
           and "D-03, D-04" in out, out + dd)

        # el anexo «Quién puede hacer qué» que se queda viejo al renombrar una parte de una pantalla: aviso, no error
        px = tmp / "anexo viejo"
        shutil.copytree(EJEMPLO, px)
        fx = px / "analisis" / "funcional.md"
        parte = next(l for l in fx.read_text(encoding="utf-8").split("\n") if l.startswith("| Nueva solicitud |"))
        editar(fx, parte, parte.replace("| Nueva solicitud |", "| Pedir autorización |", 1))
        c, out = corre(S / "comprobar.py", px)
        ok("comprobar.py: el anexo viejo tras renombrar una parte de una pantalla es aviso (derivadas --escribir)",
           c == 0 and "· el anexo «Quién puede hacer qué» al día" in out, out)
        corre(S / "indice.py", "derivadas", px, "--escribir")
        c, out = corre(S / "comprobar.py", px)
        ok("comprobar.py: con el anexo regenerado, sin aviso", "✓ el anexo «Quién puede hacer qué» al día" in out, out)

        # 4. Actualización con informe de impacto
        p = tmp / "autorizaciones"
        shutil.copytree(EJEMPLO, p)
        c, out = corre(S / "proyecto.py", "copia", p)
        ok("proyecto.py copia guarda la versión vigente", c == 0 and (p / "versiones" / "v1.1" / "funcional.md").exists(), out)
        f, t, d = p / "analisis" / "funcional.md", p / "analisis" / "tecnico.md", p / "analisis" / "decisiones.md"
        editar(f, "Versión: 1.1", "Versión: 1.2")
        editar(t, "Versión: 1.1", "Versión: 1.2")
        editar(f, "- `HU-07.1` Solo admite PDF de hasta 20 MB.", "- `HU-07.1` Solo admite PDF de hasta 30 MB. <!-- FU-04 00:03:10 -->")
        editar(f, "| ~~PC-03~~ |", "| PC-04 | ¿Quién firma las autorizaciones? | Responsable / Dirección | Responsable de la unidad | DOC-01 <!-- ❓ FU-04 00:05:00 --> |\n| ~~PC-03~~ |")
        editar(d, "| 1.1 | 2026-09-24 |", "| 1.2 | 2026-10-01 | Tamaño de documentos | FU-04 | Analista |\n| 1.1 | 2026-09-24 |")
        texto = d.read_text(encoding="utf-8").rstrip("\n").split("\n")
        filas = [l for l in texto if l.startswith("| 1.")]
        orden = sorted(filas, key=lambda l: l.split("|")[1].strip())
        d.write_text("\n".join(l if not l.startswith("| 1.") else orden.pop(0) for l in texto) + "\n", encoding="utf-8")
        editar(t, "| HU-07.1, HU-07.2 | Subir un .docx y un PDF de 25 MB |", "| HU-07.1, HU-07.2 | Subir un .docx y un PDF de 35 MB |")
        (p / "impacto").mkdir()
        informe = p / "impacto" / "FU-04.md"
        informe.write_text("""# Impacto de FU-04 · Seguimiento · 2026-10-01
Análisis base: versión 1.1 · Estado: aplicado en 1.2

## Puntos
| # | Tipo | Qué se dice | Encaja en | Cambio propuesto | Revisar también | Requiere | Decisión |
|---|---|---|---|---|---|---|---|
| 1 | CAMBIA | Los planos pesan más: hasta 30 MB [FU-04 00:03:10] | HU-07 | HU-07.1 a 30 MB | DOC-01 | — | ✔ |
| 2 | PREGUNTA | No está claro quién firma [FU-04 00:05:00] | — | PC-04 nuevo | — | — | ✔ |

## Revisión de dependencias
| Pieza | Punto | Resultado |
|---|---|---|
| DOC-01 | 1 | Revisada, sin cambios |

## Aplicado
Versión 1.2: HU-07.1 a 30 MB · PC-04 nuevo · técnico §14 con 35 MB
""", encoding="utf-8")
        c, out = corre(S / "comprobar.py", p, "--anterior", p / "versiones" / "v1.1", "--impacto", informe)
        ok("actualización correcta: comprobar.py --anterior --impacto sin errores", c == 0, out)
        # «Revisión de dependencias»: sin resolver es un resultado vacío o que empieza por «Pendiente»; la palabra
        # dentro de la frase no
        bien_inf = informe.read_text(encoding="utf-8")
        for resultado, resuelta in [("Sin cambios: el punto 2 queda pendiente de la respuesta", True),
                                    ("Pendiente: la revisa el analista", False), ("", False)]:
            informe.write_text(bien_inf.replace("| Revisada, sin cambios |", f"| {resultado} |"), encoding="utf-8")
            c, out = corre(S / "comprobar.py", p, "--anterior", p / "versiones" / "v1.1", "--impacto", informe)
            linea = next((l for l in out.splitlines() if "cada dependencia del informe tiene resultado" in l), "")
            ok(f"revisión de dependencias «{resultado}»: {'resuelta' if resuelta else 'sin resolver'}",
               linea.startswith("✓") if resuelta else (linea.startswith("✗") and "DOC-01" in linea), out)
        informe.write_text(bien_inf, encoding="utf-8")
        # La cabecera de un informe con puntos sin aplicar: proyecto.py estado los reconoce y los lista
        (p / "impacto" / "FU-05.md").write_text("# Impacto de FU-05\nAnálisis base: versión 1.2 · Estado: aplicado en 1.3; "
                                                "pendientes de aprobación: puntos 4 y 7\n", encoding="utf-8")
        (p / "impacto" / "FU-06.md").write_text("# Impacto de FU-06\nAnálisis base: versión 1.3 · Estado: pendiente\n",
                                                encoding="utf-8")
        c, out = corre(S / "proyecto.py", "estado", p)
        lineas = {x: next((l for l in out.splitlines() if x in l), "") for x in ("FU-04.md", "FU-05.md", "FU-06.md")}
        ok("proyecto.py estado: informe aplicado con puntos pendientes de aprobación, y pendiente entero",
           c == 0 and not lineas["FU-04.md"] and "aplicado en 1.3" in lineas["FU-05.md"]
           and "puntos 4 y 7" in lineas["FU-05.md"] and "pendiente" in lineas["FU-06.md"], out)
        for x in ("FU-05.md", "FU-06.md"):
            (p / "impacto" / x).unlink()
        editar(f, "| Título | Qué se quiere hacer, en una línea |", "| Título | Qué se quiere hacer, en una frase |")
        editar(f, "**HU-06 — Redactar el informe técnico**", "**HU-06 — Redactar el informe técnico de la solicitud**")
        c, out = corre(S / "comprobar.py", p, "--anterior", p / "versiones" / "v1.1", "--impacto", informe)
        ok("detecta un cambio que el informe no declara", c == 1 and "cada cambio está declarado" in out and "HU-06" in out, out)

        # 4-R2. La versión sube solo si cambia el funcional o el técnico: con cambios y sin subir, error; sin cambios y
        # subida, aviso (subir de más no pierde trabajo), salvo a la 1.0, la primera entrega. Una cita o un estado que
        # cambian son un cambio. Un informe sin nada que aplicar («Estado: sin cambios») se comprueba sin --anterior
        r2 = tmp / "R2"
        shutil.copytree(EJEMPLO, r2)
        corre(S / "proyecto.py", "copia", r2)
        for x in (r2 / "analisis" / "funcional.md", r2 / "analisis" / "tecnico.md"):
            editar(x, "Versión: 1.1", "Versión: 1.2")
        editar(r2 / "analisis" / "decisiones.md", "| 1.1 | 2026-09-24 | Plazos en días hábiles; recordatorio al organismo; "
               "se quita la urgencia | FU-03 | Analista, 2026-09-24 |", "| 1.1 | 2026-09-24 | Plazos en días hábiles; "
               "recordatorio al organismo; se quita la urgencia | FU-03 | Analista, 2026-09-24 |\n| 1.2 | 2026-10-02 | "
               "Nada | FU-05 | — |")
        c, out = corre(S / "comprobar.py", r2, "--anterior", r2 / "versiones" / "v1.1")
        ok("R2: sin ningún cambio, subir la versión es aviso", c == 0 and any(
            l.startswith("· ") and "sin cambios" in l and "1.2" in l for l in out.splitlines()), out)
        for x in (r2 / "analisis" / "funcional.md", r2 / "analisis" / "tecnico.md"):
            editar(x, "Versión: 1.2", "Versión: 1.1")
        editar(r2 / "analisis" / "decisiones.md", "\n| 1.2 | 2026-10-02 | Nada | FU-05 | — |", "")
        for nombre, antes, despues in [
                ("un texto", "| Descargar | Descargar la lista filtrada en Excel |", "| Descargar | Descargar la lista filtrada en CSV |"),
                ("solo una cita", "**PAN-01 — Solicitudes** <!-- ✅ FU-02 00:08:15 -->", "**PAN-01 — Solicitudes** <!-- ✅ FU-02 00:09:00 -->"),
                ("solo un estado", "**PAN-01 — Solicitudes** <!-- ✅ FU-02 00:08:15 -->", "**PAN-01 — Solicitudes** <!-- 🔒 FU-02 00:08:15 -->")]:
            shutil.copy(r2 / "versiones" / "v1.1" / "funcional.md", r2 / "analisis" / "funcional.md")
            editar(r2 / "analisis" / "funcional.md", antes, despues)
            c, out = corre(S / "comprobar.py", r2, "--anterior", r2 / "versiones" / "v1.1")
            ok(f"R2: con un cambio ({nombre}), no subir la versión es error",
               c == 1 and any(l.startswith("✗ la versión sube") for l in out.splitlines()), out)
        pe = tmp / "primera entrega"
        shutil.copytree(EJEMPLO, pe)
        for x in (pe / "analisis" / "funcional.md", pe / "analisis" / "tecnico.md"):
            editar(x, "Versión: 1.1", "Versión: 0.9")
        corre(S / "proyecto.py", "copia", pe)
        for x in (pe / "analisis" / "funcional.md", pe / "analisis" / "tecnico.md"):
            editar(x, "Versión: 0.9", "Versión: 1.0")
        editar(pe / "analisis" / "decisiones.md", "\n| 1.1 | 2026-09-24 | Plazos en días hábiles; recordatorio al organismo; "
               "se quita la urgencia | FU-03 | Analista, 2026-09-24 |", "")
        c, out = corre(S / "comprobar.py", pe, "--anterior", pe / "versiones" / "v0.9")
        ok("R2: la subida a la 1.0 de la primera entrega, sin cambios, no es error ni aviso",
           c == 0 and not [l for l in out.splitlines() if l.startswith(("✗", "·")) and "versión" in l], out)
        shutil.rmtree(r2)
        shutil.copytree(EJEMPLO, r2)
        (r2 / "impacto").mkdir()
        sin = ("# Impacto de FU-05\nAnálisis base: versión {v} · Estado: sin cambios\n\n## Puntos\n"
               "| # | Tipo | Qué se dice | Encaja en | Cambio propuesto | Revisar también | Requiere | Decisión |\n"
               "|---|---|---|---|---|---|---|---|\n| 1 | SIN IMPACTO | Repite lo de la lista [FU-05 00:01:00] | PAN-01 | "
               "Nada: ya lo dice PAN-01 | — | — | ✔ |\n"
               "| 2 | PROYECTO | La entrega se retrasa una semana [FU-05 00:01:30] | — | proyecto.md | — | — | ✔ |\n{extra}")
        (r2 / "impacto" / "FU-05.md").write_text(sin.format(v="1.1", extra=""), encoding="utf-8")
        c, out = corre(S / "comprobar.py", r2, "--impacto", r2 / "impacto" / "FU-05.md")
        ok("R2: un informe «sin cambios» (SIN IMPACTO que cita una pieza, PROYECTO) pasa sin --anterior",
           c == 0 and "sin cambios" in out, out)
        for extra in ("| 3 | PREGUNTA | Quién firma [FU-05 00:02:00] | — | PC nueva: quién firma | — | — | ❓ |\n",
                      "| 3 | CAMBIA | Otro plazo [FU-05 00:02:00] | HU-07 | HU-07.1 a 30 MB | — | Sí (🔒) | Pendiente |\n"):
            (r2 / "impacto" / "FU-05.md").write_text(sin.format(v="1.1", extra=extra), encoding="utf-8")
            c, out = corre(S / "comprobar.py", r2, "--impacto", r2 / "impacto" / "FU-05.md")
            ok(f"R2: «sin cambios» con un punto {extra.split('|')[2].strip()} por aplicar o pendiente es error",
               c == 1 and any(l.startswith("✗") and "sin cambios" in l and "punto 3" in l for l in out.splitlines()), out)
        (r2 / "impacto" / "FU-05.md").write_text(sin.format(v="1.0", extra=""), encoding="utf-8")
        c, out = corre(S / "comprobar.py", r2, "--impacto", r2 / "impacto" / "FU-05.md")
        ok("R2: «sin cambios» y la versión ha subido desde el análisis base es aviso", c == 0 and any(
            l.startswith("· ") and "sin cambios" in l and "1.0" in l for l in out.splitlines()), out)

        # 4-control. La columna «Qué cambia» de decisiones.md sale en el Word (control del documento, versión ≥ 1.0):
        # sin fuentes, estados ni Appian (error), ni jerga del análisis o muletillas (aviso); una 0.x no sale
        q = tmp / "control"
        fila11 = "| 1.1 | 2026-09-24 | Plazos en días hábiles; recordatorio al organismo; se quita la urgencia |"
        for texto, grave, cita in [("Plazos [FU-03 00:11:00] en días hábiles ✅", True, "FU-03"),
                                   ("Plazos en el record type de la solicitud", True, "record type"),
                                   ("Aplica los puntos 1 a 3 del informe de impacto (D-01); cabe destacar los plazos",
                                    False, "D-01")]:
            shutil.rmtree(q, ignore_errors=True)
            shutil.copytree(EJEMPLO, q)
            editar(q / "analisis" / "decisiones.md", fila11, f"| 1.1 | 2026-09-24 | {texto} |")
            c, out = corre(S / "comprobar.py", q)
            linea = next((l for l in out.splitlines() if "«Qué cambia»" in l and l.startswith("✗" if grave else "·")), "")
            ok(f"control del documento: «{texto[:30]}…» es {'error' if grave else 'aviso'}",
               (c == 1 if grave else c == 0) and cita in linea and "1.1" in linea, out)
        ok("control del documento: el aviso dice «punto N», «informe» y la muletilla",
           all(x in linea for x in ("puntos 1", "informe", "cabe destacar")), linea)
        shutil.rmtree(q)
        shutil.copytree(EJEMPLO, q)
        editar(q / "analisis" / "decisiones.md", "| 1.0 | 2026-09-10 | Primera versión del análisis |",
               "| 0.9 | 2026-09-01 | Borrador con FU-01 y el record type |\n| 1.0 | 2026-09-10 | Primera versión del análisis |")
        c, out = corre(S / "comprobar.py", q)
        ok("control del documento: una fila 0.x no sale en el Word y no se mira",
           c == 0 and not [l for l in out.splitlines() if "«Qué cambia»" in l and not l.startswith("✓")], out)

        # 4-Q. Una pregunta del prototipo (Q-nn de su trazabilidad) que no ha pasado a una PC es aviso; con su PC, no
        (q / "prototipo").mkdir(exist_ok=True)
        (q / "prototipo" / "prototipo-autorizaciones-trazabilidad.md").write_text(
            "# Trazabilidad\n\n## Preguntas abiertas para el cliente\n\n- **PC-01** ¿Cuánto se guardan?\n"
            "- 🔴 **Q-03** ¿Se puede filtrar por organismo? _(pantalla: PAN-01)_\n\n## Supuestos a validar\n\n- Q-09 no es pregunta\n",
            encoding="utf-8")
        c, out = corre(S / "comprobar.py", q)
        linea = next((l for l in out.splitlines() if "prototipo" in l and "Q-" in l), "")
        ok("Q-nn del prototipo sin PC: aviso con su ID (solo las de «Preguntas abiertas»)",
           c == 0 and linea.startswith("· ") and "Q-03" in linea and "Q-09" not in linea, out)
        editar(q / "analisis" / "funcional.md", "| ~~PC-03~~ |",
               "| PC-04 | ¿Se puede filtrar la lista por organismo? | Sí / No | Responsable de la unidad | PAN-01 "
               "<!-- ❓ prototipo Q-03 --> |\n| ~~PC-03~~ |")
        c, out = corre(S / "comprobar.py", q)
        ok("Q-nn del prototipo con su PC: sin aviso", c == 0 and any(l.startswith("✓") and "Q-nn" in l
                                                                   for l in out.splitlines()), out)

        # 4a. Texto que queda viejo: lo que una pieza cambiada ya no dice y sigue en otra (aviso, con --anterior)
        viejo = tmp / "texto viejo"
        shutil.copytree(EJEMPLO, viejo)
        fo = viejo / "analisis" / "funcional.md"
        editar(fo, "Como técnico, quiero ver juntos los datos y los documentos",
               "La revisión se hace en un plazo de cinco días hábiles desde el envío.\n\n"
               "Como técnico, quiero ver juntos los datos y los documentos")
        editar(fo, "Tarea del técnico. Se abre desde su bandeja de tareas.",
               "Tarea del técnico. Se abre desde su bandeja de tareas y vence en un plazo de cinco días hábiles desde el envío.")
        corre(S / "proyecto.py", "copia", viejo)
        for x in (fo, viejo / "analisis" / "tecnico.md"):
            editar(x, "Versión: 1.1", "Versión: 1.2")
        editar(fo, "La revisión se hace en un plazo de cinco días hábiles desde el envío.",
               "La revisión se hace en un plazo de ocho días hábiles desde el envío.")
        c, out = corre(S / "comprobar.py", viejo, "--anterior", viejo / "versiones" / "v1.1")
        aviso = [l for l in out.splitlines() if "queda viejo" in l]
        ok("texto que queda viejo: avisa de la frase vieja que sigue en otra pieza, con los dos IDs",
           len(aviso) == 1 and aviso[0].startswith("· ") and "HU-04" in aviso[0] and "PAN-04" in aviso[0]
           and "cinco días hábiles" in aviso[0], out)
        editar(fo, "vence en un plazo de cinco días hábiles desde el envío.", "vence en un plazo de ocho días hábiles desde el envío.")
        c, out = corre(S / "comprobar.py", viejo, "--anterior", viejo / "versiones" / "v1.1")
        ok("texto que queda viejo: sin la frase vieja, sin aviso", "✓ texto que queda viejo" in out, out)
        # Una línea reescrita en esta misma versión ya se ha revisado: no se avisa de ella
        r = tmp / "texto viejo reescrito"
        shutil.copytree(viejo, r)
        editar(r / "analisis" / "funcional.md", "vence en un plazo de ocho días hábiles desde el envío.",
               "vence en un plazo de cinco días hábiles desde el envío de la solicitud.")
        c, out = corre(S / "comprobar.py", r, "--anterior", r / "versiones" / "v1.1")
        ok("texto que queda viejo: una línea reescrita en esta versión no es aviso", "✓ texto que queda viejo" in out, out)
        # Dos piezas cambiadas que ya no dicen lo mismo: un aviso por línea, no uno por pieza
        r = tmp / "texto viejo dos piezas"
        shutil.copytree(EJEMPLO, r)
        fr = r / "analisis" / "funcional.md"
        editar(fr, "Como técnico, quiero ver juntos los datos y los documentos",
               "La revisión se hace en un plazo de cinco días hábiles desde el envío.\n\n"
               "Como técnico, quiero ver juntos los datos y los documentos")
        for pan in ("técnico", "responsable"):
            editar(fr, f"Tarea del {pan}. Se abre desde su bandeja de tareas.",
                   f"Tarea del {pan}. Se abre desde su bandeja de tareas y vence en un plazo de cinco días hábiles desde el envío.")
        corre(S / "proyecto.py", "copia", r)
        for x in (fr, r / "analisis" / "tecnico.md"):
            editar(x, "Versión: 1.1", "Versión: 1.2")
        editar(fr, "en un plazo de cinco días hábiles desde el envío.\n\nComo técnico",
               "en un plazo de ocho días hábiles desde el envío.\n\nComo técnico")
        editar(fr, "Tarea del técnico. Se abre desde su bandeja de tareas y vence en un plazo de cinco",
               "Tarea del técnico. Se abre desde su bandeja de tareas y vence en un plazo de ocho")
        c, out = corre(S / "comprobar.py", r, "--anterior", r / "versiones" / "v1.1")
        aviso = next((l for l in out.splitlines() if "queda viejo" in l), "")
        ok("texto que queda viejo: la línea que sigue igual (PAN-05) sale una vez aunque cambien HU-04 y PAN-04",
           aviso.startswith("· ") and aviso.count('" sigue en PAN-05') == 1, out)
        # Una URL que se repite en dos piezas no es texto que se quede viejo, suelta o como destino de un enlace
        r = tmp / "texto viejo URL"
        shutil.copytree(EJEMPLO, r)
        tr = r / "analisis" / "tecnico.md"
        editar(tr, "https://docs.appian.com/suite/help/latest/record-level-security.html",
               "[seguridad de registro](https://docs.appian.com/suite/help/latest/record-level-security.html)")
        corre(S / "proyecto.py", "copia", r)
        for x in (r / "analisis" / "funcional.md", tr):
            editar(x, "Versión: 1.1", "Versión: 1.2")
        editar(tr, "https://docs.appian.com/suite/help/latest/build-best-data-fabric.html",
               "https://docs.appian.com/suite/help/26.6/build-best-data-fabric.html")
        c, out = corre(S / "comprobar.py", r, "--anterior", r / "versiones" / "v1.1")
        ok("texto que queda viejo: una URL que se repite en dos piezas no es aviso", "✓ texto que queda viejo" in out,
           next((l for l in out.splitlines() if "queda viejo" in l), out))
        # Cinco palabras que coinciden por casualidad («la fecha de cierre y») no son texto viejo
        r = tmp / "texto viejo frase corta"
        shutil.copytree(EJEMPLO, r)
        fr = r / "analisis" / "funcional.md"
        editar(fr, "Como técnico, quiero ver juntos los datos y los documentos",
               "Al resolver, guarda la fecha de cierre y el resultado.\n\n"
               "Como técnico, quiero ver juntos los datos y los documentos")
        editar(fr, "Tarea del técnico. Se abre desde su bandeja de tareas.",
               "Tarea del técnico. Se abre desde su bandeja de tareas. Muestra la fecha límite, la fecha de cierre y las horas.")
        corre(S / "proyecto.py", "copia", r)
        for x in (fr, r / "analisis" / "tecnico.md"):
            editar(x, "Versión: 1.1", "Versión: 1.2")
        editar(fr, "Al resolver, guarda la fecha de cierre y el resultado.", "Al resolver, guarda el resultado.")
        c, out = corre(S / "comprobar.py", r, "--anterior", r / "versiones" / "v1.1")
        ok("texto que queda viejo: cinco palabras que coinciden por casualidad no son aviso", "✓ texto que queda viejo" in out,
           next((l for l in out.splitlines() if "queda viejo" in l), out))

        # 4b. Lo validado (🔒) solo cambia con un punto aprobado
        v = tmp / "validado"
        shutil.copytree(EJEMPLO, v)
        fv, tv, dv = v / "analisis" / "funcional.md", v / "analisis" / "tecnico.md", v / "analisis" / "decisiones.md"
        editar(fv, "**PAN-01 — Solicitudes** <!-- ✅ FU-02 00:08:15 -->", "**PAN-01 — Solicitudes** <!-- 🔒 FU-02 00:08:15; FU-03 00:20:00 -->")
        corre(S / "proyecto.py", "copia", v)
        for x in (fv, tv):
            editar(x, "Versión: 1.1", "Versión: 1.2")
        editar(dv, "| 1.1 | 2026-09-24 | Plazos en días hábiles; recordatorio al organismo; se quita la urgencia | FU-03 | Analista, 2026-09-24 |",
               "| 1.1 | 2026-09-24 | Plazos en días hábiles; recordatorio al organismo; se quita la urgencia | FU-03 | Analista, 2026-09-24 |\n| 1.2 | 2026-10-02 | Lista sin descarga | FU-05 | — |")
        editar(fv, "| Descargar | Descargar la lista filtrada en Excel | Consulta |", "| Descargar | Descargar la lista filtrada en CSV | Consulta |")
        (v / "impacto").mkdir()
        inf = v / "impacto" / "FU-05.md"
        plantilla_inf = """# Impacto de FU-05 · 2026-10-02
Análisis base: versión 1.1 · Estado: aplicado en 1.2

## Puntos
| # | Tipo | Qué se dice | Encaja en | Cambio propuesto | Revisar también | Requiere | Decisión |
|---|---|---|---|---|---|---|---|
| 1 | CAMBIA | La descarga es en CSV [FU-05 00:01:00] | PAN-01 | PAN-01 descarga en CSV | — | Sí (🔒) | {d} |

## Aplicado
Versión 1.2: PAN-01
"""
        inf.write_text(plantilla_inf.format(d="Pendiente"), encoding="utf-8")
        c, out = corre(S / "comprobar.py", v, "--anterior", v / "versiones" / "v1.1", "--impacto", inf)
        ok("una pieza 🔒 que cambia con el punto pendiente es error", c == 1 and "✗ lo 🔒 que cambia" in out, out)
        inf.write_text(plantilla_inf.format(d="✔"), encoding="utf-8")
        c, out = corre(S / "comprobar.py", v, "--anterior", v / "versiones" / "v1.1", "--impacto", inf)
        ok("con el punto aprobado (✔) pasa", "✓ lo 🔒 que cambia" in out, out)
        # «Requiere»: «—» o «Sí (motivo)»; un punto que cambia o anula algo 🔒 de «Encaja en» lleva «Sí». Antes de
        # aplicar (sin --anterior) y después, igual
        for requiere, falla in [("Aprobación: cambia PAN-01 🔒", "«Requiere» de cada punto"),
                                ("—", "«Requiere: Sí» en cada punto que cambia o anula algo 🔒"), ("Sí (🔒)", None)]:
            inf.write_text(plantilla_inf.format(d="✔").replace("| Sí (🔒) |", f"| {requiere} |"), encoding="utf-8")
            for antes in (False, True):
                extra = () if antes else ("--anterior", v / "versiones" / "v1.1")
                c, out = corre(S / "comprobar.py", v, *extra, "--impacto", inf)
                req = [l for l in out.splitlines() if "«Requiere" in l]
                ok(f"«Requiere: {requiere}» {'antes de aplicar' if antes else 'después'}: "
                   + (f"error en «{falla}»" if falla else "sin errores"),
                   len(req) == 2 and (all(l.startswith("✓") for l in req) if not falla else
                                      any(l.startswith("✗ " + falla) and ("PAN-01" in l or "punto 1" in l) for l in req)),
                   out)

        # 4c. La primera decisión de un proyecto (D-01) es un ID nuevo válido
        inf0 = nuevo / "impacto" / "FU-01.md"
        inf0.write_text("""# Impacto de FU-01
## Puntos
| # | Tipo | Qué se dice | Encaja en | Cambio propuesto | Revisar también | Requiere | Decisión |
|---|---|---|---|---|---|---|---|
| 1 | NUEVO | Alta de solicitudes | nuevo en funcional §4 | HU-01 y D-01 | — | — | ✔ |
""", encoding="utf-8")
        c, out = corre(S / "comprobar.py", nuevo, "--impacto", inf0)
        ok("acepta HU-01 y D-01 como primeros IDs nuevos", "✓ los IDs del informe existen" in out, out)

        # 5. DF limpio y coherencia con el técnico
        q = tmp / "sucio"
        shutil.copytree(EJEMPLO, q)
        editar(q / "analisis" / "funcional.md", "Rellena los datos, adjunta", "Rellena los datos [FU-01 00:04:10] en el record type, adjunta")
        editar(q / "analisis" / "tecnico.md", "| titulo | Texto | 120 |", "| asunto | Texto | 120 |")
        editar(q / "analisis" / "tecnico.md", "Funcional: Título |", "Funcional: Asunto |")
        c, out = corre(S / "comprobar.py", q)
        ok("detecta fuentes y términos de Appian en el DF", "✗ DF: fuentes" in out and "✗ DF: sin términos de Appian" in out, out)
        ok("detecta un dato del DF sin su campo en el técnico", "✗ funcional §6: cada dato tiene su campo" in out and "Título" in out, out)

        # 5a. DF ya hecho: una historia 🔒 que trae su ID original no se avisa por no decir «para qué» (no se inventa); las
        # demás, sí
        dfh = tmp / "DF ya hecho"
        shutil.copytree(EJEMPLO, dfh)
        fd = dfh / "analisis" / "funcional.md"
        editar(fd, "**HU-07 — Adjuntar el informe del organismo** <!-- ✅ FU-01 00:20:05 -->",
               "**HU-07 — Adjuntar el informe del organismo** <!-- 🔒 FU-01 RF-07 -->")
        editar(fd, "cuando llega para que se pare el recordatorio y la solicitud avance.", "cuando llega.")
        editar(fd, "en la propia solicitud para que el responsable lo tenga junto al resto.", "en la propia solicitud.")
        c, out = corre(S / "comprobar.py", dfh)
        linea = next((l for l in out.splitlines() if "Como… quiero… para…" in l), "")
        ok("DF ya hecho: sin aviso del «para qué» en la historia 🔒 con su ID original; con aviso en la otra",
           c == 0 and linea.startswith("· ") and "HU-06" in linea and "HU-07" not in linea, out)

        # 5b. Ficha INT con criterios (R6): un intercambio con reglas es una ficha en §9 con criterios INT-nn.m que bajan a
        # técnico §14; la fila sencilla sigue valiendo
        intp = tmp / "con ficha INT"
        shutil.copytree(EJEMPLO, intp)
        editar(intp / "analisis" / "funcional.md", "Se usa la copia del día anterior <!-- ✅ FU-02 00:14:30 --> |\n",
               "Se usa la copia del día anterior <!-- ✅ FU-02 00:14:30 --> |\n\n"
               "**INT-02 — Comprobar el organismo en su registro** <!-- ✅ FU-02 00:15:00 -->\n\n"
               "| Sistema | Cuándo | Qué pide | Qué devuelve | Si falla |\n|---|---|---|---|---|\n"
               "| Registro de organismos | Al enviar la solicitud | El código del organismo | Si está de alta | "
               "La solicitud se envía y se comprueba al revisarla |\n\n"
               "Se acepta si:\n- `INT-02.1` Un organismo de baja no se puede elegir.\n"
               "- `INT-02.2` Si el registro no responde, la solicitud se envía igual.\n\n"
               "| ID | Sistema | Qué se intercambia | Cuándo | Si falla |\n|---|---|---|---|---|\n"
               "| INT-03 | Registro mercantil | Datos de la empresa | Al dar de alta | Se piden a mano <!-- ✅ FU-02 00:16:00 --> |\n")
        editar(intp / "analisis" / "tecnico.md", "| INT-01 Directorio |",
               "| INT-02 Registro | Integración REST con la clave del organismo; reintento al revisar | Se envía igual |\n"
               "| INT-03 Registro mercantil | Fuera de la aplicación: se piden a mano | — |\n| INT-01 Directorio |")
        try:
            m_int = modelo.cargar(intp)
            ok("modelo: la ficha INT-02 y sus criterios INT-02.1 y INT-02.2; INT-01 sigue siendo fila",
               m_int.piezas["INT-02"].forma == "ficha" and m_int.piezas["INT-02"].hijos == ["INT-02.1", "INT-02.2"]
               and m_int.piezas["INT-02.1"].tipo == "CA" and m_int.piezas["INT-01"].forma == "fila"
               and not m_int.fuera_de_casa, str(m_int.fuera_de_casa))
            ok("modelo: una fila INT debajo de una ficha INT es una pieza y cierra la ficha antes de su tabla",
               "INT-03" in m_int.piezas and m_int.piezas["INT-03"].forma == "fila"
               and "| ID | Sistema |" not in m_int.texto("INT-02"), str(m_int.piezas.get("INT-03")))
        except (KeyError, NameError) as e:
            ok("modelo: la ficha INT-02 y sus criterios", False, repr(e))
        c, out = corre(S / "comprobar.py", intp)
        ok("ficha INT: con el técnico completo, sus criterios sin prueba en §14 son error",
           c == 1 and any(l.startswith("✗ técnico §14") and "INT-02.1" in l for l in out.splitlines()), out)
        editar(intp / "analisis" / "tecnico.md", "| ESC-01 a ESC-04 |",
               "| INT-02.1, INT-02.2 | Elegir un organismo de baja; registro parado |\n| ESC-01 a ESC-04 |")
        c, out = corre(S / "comprobar.py", intp)
        ok("ficha INT: con sus criterios en §14, sin errores", c == 0, out)
        c, out = corre(S / "indice.py", "ficha", intp, "INT-02")
        ok("indice.py ficha INT-02 enseña sus criterios", c == 0 and "INT-02.2" in out and "registro no responde" in out, out)
        hu = tmp / "criterio INT en una historia"
        shutil.copytree(intp, hu)
        editar(hu / "analisis" / "funcional.md", "- `HU-07.1` Solo admite PDF de hasta 20 MB.",
               "- `HU-07.1` Solo admite PDF de hasta 20 MB.\n- `INT-02.3` El registro se consulta otra vez.")
        m_hu = modelo.cargar(hu)
        ok("modelo: un criterio INT-02.3 suelto en una historia no se cuelga de ella",
           "INT-02.3" not in m_hu.piezas["HU-07"].hijos and "INT-02.3" not in m_hu.piezas, str(m_hu.piezas["HU-07"].hijos))

        # 6. Unir módulos
        m = tmp / "modulos"
        corre(S / "proyecto.py", "iniciar", m, "--nombre", "Módulos")
        (m / "modulos").mkdir()
        (m / "modulos" / "M1-funcional.md").write_text("""## 2. Perfiles

| Gestor | Personal de la unidad | Tramita |

## 4. Funcionalidades

**HU-01 — Dar de alta un expediente** <!-- ✅ FU-01 00:01:00 -->

| Perfil | Pantalla | Paso | Prioridad |
|---|---|---|---|
| Gestor | — | — | Imprescindible |

Como gestor, quiero dar de alta un expediente para tramitarlo.

Se acepta si:
- `HU-01.1` El expediente queda en «Borrador».

## Decisiones

| D-? | 2026-09-02 | FU-01 00:01:00 | CAMBIA | Una sola fase | Dos fases | HU-01 | Sí |
| D-? | 2026-09-01 | FU-01 00:00:30 | RESPONDE | Sí | — | HU-01 | Sí |
""", encoding="utf-8")
        c, out = corre(S / "unir_modulos.py", m, m / "modulos" / "M1-funcional.md", "--escribir")
        c2, out2 = corre(S / "comprobar.py", m)
        dec = (m / "analisis" / "decisiones.md").read_text(encoding="utf-8")
        ok("unir_modulos.py une el módulo y numera las decisiones por fecha",
           c == 0 and c2 == 0 and re.search(r"\| D-01 \| 2026-09-01 .*\n\| D-02 \| 2026-09-02", dec), out + out2)

        # 7. Fuentes: transcripción, texto y Word con comentarios
        entrada = tmp / "entrada"
        entrada.mkdir()
        (entrada / "reunion-2026-09-03.txt").write_text(
            "".join(f"[00:{k:02d}:00] Persona {k % 2}:\nFrase {k}.\n" for k in range(6)), encoding="utf-8")
        (entrada / "notas.md").write_text("# Notas\nTexto.\n", encoding="utf-8")
        docx = entrada / "DF-revisado.docx"
        crear_docx_con_comentario(docx)
        # Lo pegado en el chat (R1): «Tipo de fuente: chat | aprobación», «De:» y «Fecha:» en la cabecera; la fecha de
        # la cabecera manda sobre la del nombre. El temporal de Office (~$…) no es una fuente
        (entrada / "chat-2026-10-09-plazos.txt").write_text(
            "Tipo de fuente: chat\nDe: Responsable de la unidad\nFecha: 2026-10-09\n\nLos plazos son de 10 días.\n", encoding="utf-8")
        (entrada / "aprobacion-2026-10-01-informe.txt").write_text(
            "Tipo de fuente: Aprobación\nDe: Jefe de proyecto\nFecha: 10/10/2026\n\nAplica el informe de FU-04.\n", encoding="utf-8")
        (entrada / "~$DF-revisado.docx").write_bytes(b"\x00temporal de Office")
        c, out = corre(S / "leer_fuentes.py", entrada, "-o", tmp / "fuentes")
        indice = (tmp / "fuentes" / "indice.md").read_text(encoding="utf-8") if (tmp / "fuentes" / "indice.md").exists() else ""
        ok("leer_fuentes.py cataloga transcripción, texto y Word",
           c == 0 and "Transcripción" in indice and "| Texto |" in indice and "Documento Word" in indice, out + indice)
        ok("leer_fuentes.py: chat y aprobación con su tipo, quién y la fecha de la cabecera",
           re.search(r"\| chat-2026-10-09-plazos\.txt \| Chat \| de Responsable de la unidad[^|]*\| 2026-10-09 \|", indice)
           and re.search(r"\| aprobacion-2026-10-01-informe\.txt \| Aprobación \| de Jefe de proyecto[^|]*\| 2026-10-10 \|",
                         indice), indice)
        ok("leer_fuentes.py: el temporal de Office (~$…) de una carpeta no se cataloga", "~$" not in indice, indice)
        c, out = corre(S / "leer_fuentes.py", entrada / "~$DF-revisado.docx", "-o", tmp / "fuentes")
        ok("leer_fuentes.py: un temporal de Office suelto da aviso y no se cataloga",
           "~$" not in (tmp / "fuentes" / "indice.md").read_text(encoding="utf-8") and "~$DF-revisado.docx" in out
           and "AVISO" in out, out)
        tr = next((x for x in (tmp / "fuentes").glob("FU-*-reunion-*.md")), None)
        ok("la transcripción lleva sus participantes", tr is not None and "- Participantes: Persona 0; Persona 1" in tr.read_text(encoding="utf-8"))
        w = tmp / "con-nombres"
        shutil.copytree(EJEMPLO, w)
        editar(w / "analisis" / "funcional.md", "Lee los dos informes y resuelve.", "Lee los dos informes y resuelve, como pidió Persona 1.")
        c, out = corre(S / "comprobar.py", w, "--fuentes", tmp / "fuentes")
        ok("detecta el nombre de un participante en el análisis", "✗ sin nombres de participantes" in out and "Persona 1" in out, out)
        fu = next((x for x in (tmp / "fuentes").glob("FU-*-df-revisado.md")), None)
        txt = fu.read_text(encoding="utf-8") if fu else ""
        ok("leer_fuentes.py saca los comentarios del Word con su historia",
           "## Comentarios del documento" in txt and "HU-07" in txt and "Mejor 30 MB" in txt, txt[-600:])

        # 7b. as-is/ entra como una sola fuente, con el índice de sus documentos y sin su extracción; la propuesta de
        # refactorización, como cualquier fichero
        app = tmp / "Carpeta con espacios" / "Gestión app"
        shutil.copytree(EVOLUTIVO / "as-is", app / "as-is")
        (app / "as-is" / "extraccion").mkdir()
        (app / "as-is" / "extraccion" / "LEEME.md").write_text("# Extracción en bruto\n", encoding="utf-8")
        c, out = corre(S / "leer_fuentes.py", EVOLUTIVO / "refactorizacion" / "propuesta.md",
                       "--una-fuente", app / "as-is", "-o", app / "fuentes")
        estado = (json.loads((app / "fuentes" / "indice.json").read_text(encoding="utf-8"))["fuentes"]
                  if (app / "fuentes" / "indice.json").exists() else [])
        fu = next((e for e in estado if e["fichero"] == "as-is/"), None)
        txt = (app / "fuentes" / fu["salida"]).read_text(encoding="utf-8") if fu and fu.get("salida") else ""
        ok("leer_fuentes.py --una-fuente: as-is/ es una FU con el índice de sus documentos, sin la extracción",
           c == 0 and len(estado) == 2 and fu is not None and "as-is/LEEME.md" in txt
           and "as-is/datos/inventario.json" in txt and "extraccion" not in txt.lower()
           and any(e["fichero"] == "propuesta.md" for e in estado), out + txt)
        c, out = corre(S / "leer_fuentes.py", "--una-fuente", app / "as-is", "-o", app / "fuentes")
        ok("leer_fuentes.py --una-fuente otra vez: la misma FU", c == 0 and fu is not None and f"= {fu['id']}" in out
           and len(json.loads((app / "fuentes" / "indice.json").read_text(encoding="utf-8"))["fuentes"]) == 2, out)
        # Lo que dejan el sistema y Office en la carpeta no es un documento: ni cambia la fuente ni sale en su índice
        for basura in ("desktop.ini", "Thumbs.db", ".DS_Store", "~$LEEME.md", "datos/Thumbs.db", "datos/~$notas.docx"):
            (app / "as-is" / basura).write_bytes(b"\x00basura")
        c, out = corre(S / "leer_fuentes.py", "--una-fuente", app / "as-is", "-o", app / "fuentes")
        txt = (app / "fuentes" / fu["salida"]).read_text(encoding="utf-8") if fu and fu.get("salida") else ""
        ok("leer_fuentes.py --una-fuente: desktop.ini, Thumbs.db, .DS_Store y ~$… no crean otra FU ni salen en el índice",
           c == 0 and fu is not None and f"= {fu['id']}" in out
           and len(json.loads((app / "fuentes" / "indice.json").read_text(encoding="utf-8"))["fuentes"]) == 2
           and not re.search(r"desktop\.ini|Thumbs|DS_Store|~\$", txt), out + txt)

        # 7b'. Repetir la ingeniería inversa: las citas «[FU-nn H-…]» y «[FU-nn NV-…]» son del as-is/ que catalogó FU-nn
        # (los H- y NV- se numeran de nuevo en cada ejecución); con otro as-is/ (otra huella), aviso
        r = tmp / "evolutivo otra ingeniería inversa"
        shutil.copytree(EVOLUTIVO, r)
        corre(S / "leer_fuentes.py", "--una-fuente", r / "as-is", "-o", r / "fuentes")    # FU-01, la que cita el análisis
        c, out = corre(S / "comprobar.py", r)
        ok("evolutivo: con el as-is/ que catalogó FU-01, sin aviso de un as-is anterior",
           c == 0 and "as-is anterior" not in out and "✓ as-is: las citas a hallazgos y NV" in out, out)
        with open(r / "as-is" / "datos" / "sin-verificar.json", "a", encoding="utf-8") as fj:
            fj.write("\n")
        c, out = corre(S / "comprobar.py", r)
        aviso = next((l for l in out.splitlines() if "as-is anterior" in l), "")
        ok("evolutivo: con otro as-is/ sin catalogar, aviso de que las citas a FU-01 son de un as-is anterior",
           c == 0 and aviso.startswith("· ") and "FU-01" in aviso and "no está catalogado" in aviso, out)
        corre(S / "leer_fuentes.py", "--una-fuente", r / "as-is", "-o", r / "fuentes")    # el as-is/ de ahora, FU-02
        c, out = corre(S / "comprobar.py", r)
        aviso = next((l for l in out.splitlines() if "as-is anterior" in l), "")
        ok("evolutivo: con otro as-is/ catalogado, el aviso dice qué FU es ahora",
           c == 0 and aviso.startswith("· ") and "las citas a FU-01" in aviso and "ahora es FU-02" in aviso, out)

        # 7c. Aplicación existente: con as-is/datos/, el origen de cada historia, la Situación de cada objeto de §13
        # contra el inventario, las citas de hallazgos, NV y REF, y la migración si hay propuesta
        c, out = corre(S / "comprobar.py", EVOLUTIVO)
        ok("evolutivo: pasa comprobar.py sin errores y comprueba lo de as-is/",
           c == 0 and "✓ as-is: los hallazgos citados están en hallazgos.json" in out, out)
        # 5.5: el «Origen» de cada historia ya no se escribe (lo deriva indice.py cambios): sin él, ni error ni aviso; si
        # está, vale
        r = tmp / "evolutivo sin origen"
        shutil.copytree(EVOLUTIVO, r)
        fo = r / "analisis" / "funcional.md"
        fo.write_text(fo.read_text(encoding="utf-8").replace("| Perfil | Pantalla | Paso | Prioridad | Origen |\n|---|---|---|---|---|",
                                                             "| Perfil | Pantalla | Paso | Prioridad |\n|---|---|---|---|")
                      .replace(" | Nueva |", " |"), encoding="utf-8")
        c, out2 = corre(S / "comprobar.py", r)
        ok("5.5: sin «Origen» en las historias, ni error ni aviso; con él, tampoco",
           c == 0 and "Origen" not in out2 and "Origen" not in out and "| Nueva |" not in fo.read_text(encoding="utf-8"),
           out2)
        # 5.8: con as-is/, las historias de lo que ya hace la aplicación no llevan prioridad («—»); sin as-is/, sí
        editar(fo, "| Revisor | PAN-03 | — | Deseable |", "| Revisor | PAN-03 | — | — |")
        c, out = corre(S / "comprobar.py", r)
        ok("5.8: con as-is/, una historia con prioridad «—» no es error", c == 0, out)
        shutil.rmtree(r / "as-is")
        c, out = corre(S / "comprobar.py", r)
        ok("5.8: sin as-is/, una historia con prioridad «—» es error",
           c == 1 and any(l.startswith("✗ prioridad") and "HU-03" in l for l in out.splitlines()), out)
        ok("evolutivo: «Existe» con un objeto de otra aplicación no es error",
           not [l for l in out.splitlines() if l.startswith("✗") and "UTL_DiasLaborables" in l], out)
        rotas = [  # (qué se rompe, fichero, texto, cambio, comprobación que falla, lo que cita)
            ("«Corrige H-…» en una tabla del DF", "funcional", "| Datos | Corregir el título y el importe | Gestor |",
             "| Datos | Corregir el título y el importe. Corrige H-DAT-01 | Gestor |", "solo en la trazabilidad",
             "H-DAT-01"),
            ("cita de un hallazgo que no está en hallazgos.json", "funcional", "[FU-01 H-DAT-01]", "[FU-01 H-DAT-07]",
             "hallazgos.json", "H-DAT-07"),
            ("cita de un NV que no está en sin-verificar.json", "funcional", "[FU-01 NV-PRO-01]", "[FU-01 NV-PRO-09]",
             "sin-verificar.json", "NV-PRO-09"),
            ("cita de una REF que no está en el Diagnóstico de la propuesta", "funcional", "[FU-01 H-DAT-01] -->",
             "[FU-01 H-DAT-01]; [FU-02 REF-99] -->", "Diagnóstico", "REF-99"),
            ("cita de una DEC que no está en los Pendientes de la propuesta", "funcional", "[FU-01 H-DAT-01] -->",
             "[FU-01 H-DAT-01]; [FU-02 DEC-99] -->", "Pendientes", "DEC-99"),
            ("§13: «Nuevo» con el objeto de otra aplicación", "tecnico", "| Regla de otra aplicación | Existe |",
             "| Regla de otra aplicación | Nuevo |", "Situación", "UTL_DiasLaborables"),
            ("§13: «Nuevo» con un objeto del inventario", "tecnico", "| `DEM_ER_DiasPendiente` | Regla de expresión |",
             "| `DEM_ER_EsAdmin` | Regla de expresión |", "Situación", "DEM_ER_EsAdmin"),
            ("§13: «Modifica» con un objeto que no está", "tecnico", "| `DEM_Dashboard` | Interfaz |",
             "| `DEM_Panel` | Interfaz |", "Situación", "DEM_Panel"),
            ("§13: «Sustituye» sin un objeto del inventario", "tecnico", "| Sustituye | `DEM_ESTADOS_VALIDOS` |",
             "| Sustituye | — |", "Situación", "DEM_ER_IdEstado"),
            ("§13: «Sustituye» con un objeto nuevo que ya está en el inventario", "tecnico",
             "| `DEM_ER_IdEstado` | Regla de expresión | Sustituye |", "| `DEM_ER_EsAdmin` | Regla de expresión | Sustituye |",
             "Situación", "DEM_ER_EsAdmin"),
            ("§13: «Sustituye» con un objeto nuevo de otra aplicación", "tecnico",
             "| `DEM_ER_IdEstado` | Regla de expresión | Sustituye |",
             "| `UTL_DiasLaborables` | Regla de expresión | Sustituye |", "Situación", "«Sustituye» y es de otra aplicación"),
            ("una REF de la propuesta sin DT que la cite", "tecnico", "| **Necesidad** | [FU-02 REF-01], HU-02 |",
             "| **Necesidad** | HU-02 |", "cada REF", "REF-01"),
            ("§3 sin la tabla de migración", "tecnico", "| Origen en la app actual |", "| Origen anterior |",
             "Carga inicial y migración", "falta"),
        ]
        for nombre, doc, viejo, nuevo, comprobacion, cita in rotas:
            r = tmp / "evolutivo roto"
            shutil.rmtree(r, ignore_errors=True)
            shutil.copytree(EVOLUTIVO, r)
            editar(r / "analisis" / f"{doc}.md", viejo, nuevo)
            c, out = corre(S / "comprobar.py", r)
            linea = next((l for l in out.splitlines() if l.startswith("✗") and comprobacion in l), "")
            ok(f"evolutivo: {nombre} es error", c == 1 and cita in linea, out)
        # §13 se comprueba siempre que su tabla tenga filas, también con el técnico sin empezar (sin DT ni modelo)
        r = tmp / "evolutivo técnico sin empezar"
        shutil.copytree(EVOLUTIVO, r)
        (r / "analisis" / "tecnico.md").write_text(
            "# Devoluciones de solicitudes — Especificación técnica\n\nVersión: 1.0 · Estado: en curso\n\n"
            + "\n".join(f"## {n}. Apartado\n" for n in range(13))
            + "## 13. Plan de construcción\n\n| Paso | Objeto | Tipo | Situación | Sustituye a |\n|---|---|---|---|---|\n"
            "| 1 | `DEM_ER_EsAdmin` | Regla de expresión | Nuevo | — |\n\n## 14. Pruebas\n\n## 15. Pendientes\n",
            encoding="utf-8")
        c, out = corre(S / "comprobar.py", r)
        ok("evolutivo: §13 con filas se comprueba aunque el técnico no esté empezado",
           c == 1 and any(l.startswith("✗ técnico §13") and "DEM_ER_EsAdmin" in l for l in out.splitlines()), out)
        r = tmp / "evolutivo REF y DEC que existen"
        shutil.copytree(EVOLUTIVO, r)
        editar(r / "analisis" / "funcional.md", "[FU-01 H-DAT-01] -->", "[FU-01 H-DAT-01]; [FU-02 REF-01]; [FU-02 DEC-01] -->")
        c, out = corre(S / "comprobar.py", r)
        ok("evolutivo: las REF y DEC citadas que están en la propuesta no son error",
           c == 0 and "✓ propuesta: las REF citadas" in out and "✓ propuesta: las DEC citadas" in out, out)
        # Con el técnico «en curso», una REF sin DT y la falta de la tabla de migración son aviso, como lo demás del
        # técnico; con «completo», error (lo de arriba)
        r = tmp / "evolutivo en curso"
        shutil.copytree(EVOLUTIVO, r)
        editar(r / "analisis" / "tecnico.md", "Versión: 1.0 · Estado: completo", "Versión: 1.0 · Estado: en curso")
        editar(r / "analisis" / "tecnico.md", "| **Necesidad** | [FU-02 REF-01], HU-02 |", "| **Necesidad** | HU-02 |")
        editar(r / "analisis" / "tecnico.md", "| Origen en la app actual |", "| Origen anterior |")
        c, out = corre(S / "comprobar.py", r)
        avisos = [l for l in out.splitlines() if l.startswith("· ")]
        ok("evolutivo en curso: REF sin DT y sin tabla de migración, aviso",
           c == 0 and any("cada REF" in l and "REF-01" in l for l in avisos)
           and any("Carga inicial y migración" in l for l in avisos), out)
        # Una REF que el cliente rechaza se cierra con su DT: «No se hace: …»
        r = tmp / "evolutivo REF rechazada"
        shutil.copytree(EVOLUTIVO, r)
        editar(r / "analisis" / "tecnico.md", "| **Decisión** | `DEM_ER_IdEstado` da el id de un estado de `DEM Estado`;",
               "| **Decisión** | No se hace: el cliente mantiene la constante `DEM_ESTADOS_VALIDOS` (FU-03); antes, "
               "`DEM_ER_IdEstado` iba a dar el id de un estado de `DEM Estado`;")
        c, out = corre(S / "comprobar.py", r)
        ok("evolutivo: una REF rechazada con «No se hace: …» en su DT pasa", c == 0 and "✓ propuesta: cada REF" in out, out)
        # Los objetos de §13 con su prefijo de tipo o con paréntesis («recordType!DEM Solicitud», «DEM_Dashboard()»)
        r = tmp / "evolutivo con prefijos"
        shutil.copytree(EVOLUTIVO, r)
        editar(r / "analisis" / "tecnico.md", "| `DEM Solicitud` | Record type |", "| `recordType!DEM Solicitud` | Record type |")
        editar(r / "analisis" / "tecnico.md", "| `DEM_Dashboard` | Interfaz |", "| `DEM_Dashboard()` | Interfaz |")
        c, out = corre(S / "comprobar.py", r)
        ok("evolutivo: «recordType!…» y «…()» en §13 se leen como el objeto",
           c == 0 and not [l for l in out.splitlines() if l.startswith("✗")], out)
        r = tmp / "evolutivo modifica"
        shutil.copytree(EVOLUTIVO, r)
        editar(r / "analisis" / "tecnico.md", "| Regla de otra aplicación | Existe |", "| Regla de otra aplicación | Modifica |")
        c, out = corre(S / "comprobar.py", r)
        ok("evolutivo: «Modifica» con el objeto de otra aplicación es aviso",
           c == 0 and any(l.startswith("· ") and "UTL_DiasLaborables es de otra aplicación: ¿quién la cambia?" in l
                          for l in out.splitlines()), out)
        r = tmp / "as-is anterior"
        shutil.copytree(EVOLUTIVO, r)
        (r / "as-is" / "datos" / "sin-verificar.json").unlink()
        dep = r / "as-is" / "datos" / "dependencias.json"
        dep.write_text(json.dumps({"aristas": json.loads(dep.read_text(encoding="utf-8"))["aristas"]}), encoding="utf-8")
        editar(r / "analisis" / "funcional.md", "[FU-01 NV-PRO-01]", "[FU-01 NV-PRO-09]")
        c, out = corre(S / "comprobar.py", r)
        ok("as-is/ sin NV ni objetos de fuera (anterior): no se comprueban; lo que no está en el inventario, aviso",
           c == 0 and "NV-PRO-09" not in out
           and any(l.startswith("· ") and "UTL_DiasLaborables" in l for l in out.splitlines()), out)

        # 7d. Parte mal hecha: un objeto que se modifica o se usa (§13 «Modifica» o «Existe») con un hallazgo Alta o
        # con algo sin verificar (abierto o parcial) es aviso, con su H o su NV, salvo que una PT o una PC ya lo cite.
        # En el ejemplo, PT-01 cita NV-ARQ-01, y PT-02 y PC-01, NV-PRO-01; H-SEG-01 no lo cita ninguna
        c, out = corre(S / "comprobar.py", EVOLUTIVO)
        avisos = "\n".join(l for l in out.splitlines() if l.startswith("· "))
        ok("evolutivo: avisa del hallazgo Alta sin PT ni PC, con su ID; de los NV que ya cita una PT o una PC, no",
           c == 0 and "DEM_INT_NotificarERP tiene H-SEG-01 (Alta): ¿pasa antes por refactorización?" in avisos
           and "NV-ARQ-01" not in avisos and "NV-PRO-01" not in avisos
           and "DEM_SolicitudForm tiene" not in avisos and "DEM_ER_IdEstado tiene" not in avisos, out)
        sin_citas = tmp / "evolutivo sin citas"
        shutil.copytree(EVOLUTIVO, sin_citas)
        editar(sin_citas / "analisis" / "tecnico.md", "`UTL_DiasLaborables`? [FU-01 NV-ARQ-01]", "`UTL_DiasLaborables`?")
        editar(sin_citas / "analisis" / "tecnico.md", "de la revisión? [FU-01 NV-PRO-01]", "de la revisión?")
        editar(sin_citas / "analisis" / "funcional.md", "ACT-01 <!-- ❓ [FU-01 NV-PRO-01] -->", "ACT-01 <!-- ❓ FU-01 -->")
        c, out = corre(S / "comprobar.py", sin_citas)
        avisos = "\n".join(l for l in out.splitlines() if l.startswith("· "))
        ok("evolutivo: sin PT ni PC que los cite, avisa de cada NV sin verificar con ¿PC? o ¿PT?",
           c == 0 and "UTL_DiasLaborables tiene NV-ARQ-01 sin verificar: ¿PT?" in avisos
           and "DEM Revisar Solicitud tiene NV-PRO-01 sin verificar: ¿PC?" in avisos, out)
        r = tmp / "evolutivo H citado"
        shutil.copytree(EVOLUTIVO, r)
        editar(r / "analisis" / "tecnico.md", "| Analista con el responsable de las solicitudes (PC-01) |",
               "| Analista con el responsable de las solicitudes (PC-01) |\n"
               "| PT-03 | ¿Se refactoriza antes la integración con el ERP? [FU-01 H-SEG-01] | §10 | Analista con el cliente |")
        c, out = corre(S / "comprobar.py", r)
        ok("evolutivo: con una PT que cita el hallazgo Alta, sin aviso", c == 0 and "H-SEG-01 (Alta)" not in out, out)
        r = tmp / "evolutivo resuelto"
        shutil.copytree(sin_citas, r)
        editar(r / "as-is" / "datos" / "sin-verificar.json", '"estado": "abierto",\n   "documento": "02-arquitectura',
               '"estado": "resuelto",\n   "documento": "02-arquitectura')
        c, out = corre(S / "comprobar.py", r)
        ok("evolutivo: un NV resuelto no es aviso", c == 0 and "NV-ARQ-01 sin verificar" not in out
           and "NV-PRO-01 sin verificar: ¿PC?" in out, out)

        # 7e. Sin as-is/ (riesgo 4): las comprobaciones de as-is/ no saltan y el ejemplo da los mismos errores y avisos
        # que antes de tenerlas (los de la versión e058107)
        c, out = corre(S / "comprobar.py", EJEMPLO)
        ok("sin as-is/, autorizaciones da los mismos errores y avisos que antes",
           c == 0 and "as-is" not in out and [l for l in out.splitlines() if l.startswith(("✗", "·"))]
           == ["· pantallas con su captura del prototipo: 5 → PAN-01, PAN-02, PAN-03, PAN-04, PAN-05"], out)

        # 8. Word del DF (opcional)
        if shutil.which("node"):
            r = subprocess.run(["node", str(S / "df_docx.js"), str(EJEMPLO), "-o", str(tmp / "df.docx")],
                               capture_output=True, text=True, encoding="utf-8", errors="replace")
            if r.returncode == 2 and "docx" in r.stderr:
                print("· DF en Word: falta el paquete docx de Node (npm install docx); no se prueba")
            else:
                ok("df_docx.js genera el DF", r.returncode == 0 and (tmp / "df.docx").exists(), r.stdout + r.stderr)
                if (tmp / "df.docx").exists():
                    xml = zipfile.ZipFile(tmp / "df.docx").read("word/document.xml").decode("utf-8").replace("\u2011", "-")
                    ok("el DF no enseña fuentes, anuladas ni respondidas",
                       "FU-0" not in xml and "HU-11" not in xml and "PC-03" not in xml and "PC-01" in xml
                       and "indice.py" not in xml and "Analista, 2026" not in xml)
                    toc = re.search(r"<w:sdt>.*?</w:sdt>", xml, re.S)
                    ok("el índice del DF lleva sus entradas (soffice no rellena un campo vacío)",
                       toc is not None and "1. Objetivo y alcance" in toc.group(0) and "HU-07 — " in toc.group(0),
                       toc.group(0)[:600] if toc else xml[:600])
                    estilos = zipfile.ZipFile(tmp / "df.docx").read("word/styles.xml").decode("utf-8")
                    ok("sin marca, los colores de siempre", 'w:fill="1F3864"' in xml and "1F3864" in estilos)
                d = docx_de(intp, tmp / "int.docx")
                xml = zipfile.ZipFile(d).read("word/document.xml").decode("utf-8").replace(GUION, "-") if d else ""
                ok("la ficha INT (R6) sale como título, igual que una historia",
                   any('w:val="Heading3"' in x and "INT-02 — Comprobar el organismo" in x  # como las fichas HU (####)
                       for x in re.findall(r"<w:p>.*?</w:p>", xml, re.S)),
                   xml[:300])
                # Una viñeta en varias líneas es un párrafo con su numeración; el color de la marca del cliente (T12)
                w = tmp / "Word con marca"
                shutil.copytree(EJEMPLO, w)
                editar(w / "analisis" / "funcional.md", "\n## 2. Perfiles",
                       "\n- Primera parte de la viñeta\n  que sigue en otra línea.\n- Otra viñeta.\n\n## 2. Perfiles")
                (w / "prototipo").mkdir()
                (w / "prototipo" / "brand-ejemplo.json").write_text(
                    json.dumps({"id": "ejemplo", "site": {"backgroundColor": "#7a1f3d"}}), encoding="utf-8")
                d = docx_de(w, tmp / "marca.docx")
                xml = zipfile.ZipFile(d).read("word/document.xml").decode("utf-8") if d else ""
                estilos = zipfile.ZipFile(d).read("word/styles.xml").decode("utf-8") if d else ""
                ok("una viñeta de varias líneas es un solo párrafo con numeración",
                   any("<w:numPr>" in x and "Primera parte de la viñeta que sigue en otra línea." in x
                       for x in re.findall(r"<w:p>.*?</w:p>", xml, re.S)) and xml.count("que sigue en otra línea") == 1,
                   xml[:300])
                ok("con prototipo/brand-<id>.json, su color en títulos y cabeceras de tabla",
                   'w:fill="7A1F3D"' in xml and 'w:fill="1F3864"' not in xml and 'w:color w:val="7A1F3D"' in estilos
                   and "1F3864" not in estilos and "2F5597" not in estilos, estilos[-600:])
                # El Word entregado (por fichero: «Entregados:» de proyecto.md) no se pisa; el que no se ha entregado se
                # reemplaza avisando, aunque «DF entregado» diga su versión
                (w / "entregables").mkdir(exist_ok=True)
                destino = w / "entregables" / "DF-Solicitudes-de-autorizacion-v1.1.docx"
                destino.write_bytes(b"el que se envio")
                editar(w / "proyecto.md", "DF entregado: 1.0 (2026-09-12)", "DF entregado: 1.1 · 2026-10-01")
                r = subprocess.run(["node", str(S / "df_docx.js"), str(w)], capture_output=True, text=True,
                                   encoding="utf-8", errors="replace")
                ok("un Word que no está en «Entregados» se reemplaza, avisando, aunque sea de la versión de «DF entregado»",
                   r.returncode == 0 and "se reemplaza" in r.stdout and destino.read_bytes() != b"el que se envio",
                   r.stdout + r.stderr)
                editar(w / "proyecto.md", "DF entregado: 1.1 · 2026-10-01 · Estado: en validación",
                       "DF entregado: 1.1 · 2026-10-01 · Estado: en validación\nEntregados: DF-Solicitudes-de-autorizacion-v1.1.docx")
                destino.write_bytes(b"el que se envio")
                r = subprocess.run(["node", str(S / "df_docx.js"), str(w)], capture_output=True, text=True,
                                   encoding="utf-8", errors="replace")
                ok("un Word de «Entregados» no se sobrescribe: sale con error y no lo toca",
                   r.returncode == 1 and "ya se entregó" in r.stderr and destino.read_bytes() == b"el que se envio",
                   r.stdout + r.stderr)
                editar(w / "proyecto.md", "\nEntregados: DF-Solicitudes-de-autorizacion-v1.1.docx", "")
                # Sin LibreOffice, el PDF que ya había se queda
                revision = w / "entregables" / "revision"
                revision.mkdir()
                (revision / "DF del cliente.pdf").write_bytes(b"%PDF anterior")
                (w / "fuentes").mkdir(exist_ok=True)
                otro = w / "fuentes" / "DF del cliente.docx"
                shutil.copy(destino, otro)
                r = subprocess.run(["node", str(S / "df_docx.js"), str(w), "--pdf-de", str(otro)], capture_output=True,
                                   text=True, encoding="utf-8", errors="replace",
                                   env={**os.environ, "PATH": str(pathlib.Path(shutil.which("node")).parent), "SOFFICE": ""})
                ok("df_docx.js --pdf-de sin LibreOffice: lo dice y no borra el PDF que había",
                   r.returncode == 1 and "Sin LibreOffice" in r.stdout
                   and (revision / "DF del cliente.pdf").is_file()
                   and (revision / "DF del cliente.pdf").read_bytes() == b"%PDF anterior", r.stdout + r.stderr)
                # --pdf: LibreOffice en un HOME temporal que se borra y el PDF en <p>/entregables/revision/
                if shutil.which("soffice"):
                    temporal = tmp / "temporal de soffice"
                    temporal.mkdir()
                    r = subprocess.run(["node", str(S / "df_docx.js"), str(w), "--pdf"], capture_output=True, text=True,
                                       encoding="utf-8", errors="replace", env={**os.environ, "TMPDIR": str(temporal)})
                    pdf = revision / "DF-Solicitudes-de-autorizacion-v1.1.pdf"
                    ok("df_docx.js --pdf: el PDF en entregables/revision/ y el HOME temporal borrado",
                       r.returncode == 0 and pdf.is_file() and pdf.read_bytes()[:4] == b"%PDF"
                       and not [x for x in temporal.iterdir() if x.name != "node-compile-cache"],  # la caché es de Node
                       r.stdout + r.stderr + str(list(temporal.iterdir())))
                    # --pdf-de: un documento cualquiera (el DF del cliente para ver sus diapositivas), sin generar el Word
                    r = subprocess.run(["node", str(S / "df_docx.js"), str(w), "--pdf-de", str(otro)], capture_output=True,
                                       text=True, encoding="utf-8", errors="replace", env={**os.environ, "TMPDIR": str(temporal)})
                    ok("df_docx.js --pdf-de: solo ese PDF, en entregables/revision/, y sustituye al anterior",
                       r.returncode == 0 and (revision / "DF del cliente.pdf").read_bytes()[:4] == b"%PDF"
                       and (revision / "DF del cliente.pdf").read_bytes() != b"%PDF anterior"
                       and not [x for x in temporal.iterdir() if x.name != "node-compile-cache"], r.stdout + r.stderr)
                else:
                    print("· df_docx.js --pdf: no hay LibreOffice (soffice); no se prueba")
        else:
            print("· DF en Word: no hay Node.js; no se prueba")

        # 9. Diagramas de estados y de datos (opcional): los pinta el mermaid.py de la skill de diagramas
        mermaid = PLUGIN / "skills" / "appian-diagramas-bpmn" / "scripts" / "mermaid.py"
        c, out = (corre(mermaid, "--check", DATOS / "prueba.mmd", "--md", SKILL / "references" / "mermaid-diagrams.md")
                  if mermaid.is_file() else (1, f"no existe {mermaid}"))
        if c == 2:
            print("· Diagramas: falta Playwright o un navegador; no se prueba")
        else:
            ok("mermaid.py valida un diagrama y los ejemplos de mermaid-diagrams.md", c == 0, out)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("\nTodo correcto." if not fallos else f"\n{len(fallos)} pruebas fallan: {', '.join(fallos)}")
    return 1 if fallos else 0


GUION = chr(0x2011)   # df_docx.js pone guiones que no se parten en los IDs (PAN‑02)
COLS = "| ID | Título | Tipo | Estado | Aprobada | Construida | En producción | Comparte objetos / decisión |\n|---|---|---|---|---|---|---|---|\n"
FILAS_BASE = {   # analisis/cambios.md del proyecto con unidades (con_unidades): ID → fila
    "EV-01": "| EV-01 | Devoluciones | Evolutivo | En producción | 2026-10-09 · FU-03 | 2026-10-10 · verificada | 2026-10-11 · PASE-1 | — |",
    "EV-02": "| EV-02 | Firma de la revisión | Evolutivo | Aprobada | 2026-10-12 · FU-05 | — | — | — |",
    "URG-01": "| URG-01 | El formulario de la solicitud falla | Urgente | Abierta | — | — | — | — |",
    "EV-03": "| EV-03 | Alta desde el panel | Evolutivo | Abierta | — | — | — | — |"}


def cambios_md(p, filas):
    """analisis/cambios.md con estas filas (ID → fila completa o, si es un estado, la de FILAS_BASE en ese estado)."""
    out = []
    for k, v in filas.items():
        if v.startswith("|"):
            out.append(v)
        else:
            c = FILAS_BASE.get(k, f"| {k} | Prueba | {'Urgente' if k.startswith('URG') else 'Evolutivo'} | Abierta | — | — | — | — |").split(" | ")
            c[3] = v
            out.append(" | ".join(c))
    (p / "analisis" / "cambios.md").write_text("# Devoluciones de solicitudes — Unidades de cambio\n\n" + COLS
                                               + "\n".join(out) + "\n", encoding="utf-8")


def con_unidades(destino):
    """Un proyecto con unidades de cambio, desde evolutivo/ (la aplicación existente DEM, versión 1.0): EV-01 (las
    devoluciones, sus filas de §13 con su ID: con as-is/, una fila sin ID no es de EV-01) en producción; EV-02 (firma de la revisión: cambia HU-02.2 y crea HU-04, con
    su informe FU-04 aplicado en la 1.1, sus filas de §13 y su DT «Cambio sobre lo construido») aprobada; URG-01 (el
    formulario de la solicitud falla, corregido en el entorno de corrección: choca con EV-02) abierta; y EV-03 (modifica
    DEM Alta Solicitud, que usa el formulario; su informe FU-06 tiene un punto pendiente) abierta."""
    shutil.copytree(EVOLUTIVO, destino)
    corre(S / "proyecto.py", "copia", destino)
    f, t, d = (destino / "analisis" / x for x in ("funcional.md", "tecnico.md", "decisiones.md"))
    for x in (f, t):
        editar(x, "Versión: 1.0", "Versión: 1.1")
    editar(f, "- `HU-02.2` Al reenviarla vuelve a «Enviada» con el mismo número.",
           "- `HU-02.2` Al reenviarla vuelve a «Enviada» con el mismo número y sin la firma anterior. <!-- ✅ FU-04 00:02:00 -->")
    editar(f, "### Seguimiento", "**HU-04 — Firmar la revisión** <!-- ✅ FU-04 00:05:00 -->\n\n"
           "| Perfil | Pantalla | Paso | Prioridad | Origen |\n|---|---|---|---|---|\n"
           "| Revisor | PAN-01 | ACT-01 | Imprescindible | Nueva |\n\n"
           "Como revisor, quiero firmar la revisión para que quede constancia de quién la hizo.\n\n"
           "Se acepta si:\n- `HU-04.1` Sin firma no se puede aprobar ni rechazar.\n\n### Seguimiento")
    editar(f, "Historias: HU-01.", "Historias: HU-01, HU-04.")
    editar(f, "| Fecha de envío |", "| Firma del revisor | Quién revisó | Texto | Al aprobar o rechazar | PAN-01 |\n| Fecha de envío |")
    editar(t, "| fechaEnvio | Fecha y hora |", "| firmaRevisor | Texto | 255 | — | No | Al decidir | — | Funcional: Firma del revisor |\n"
           "| fechaEnvio | Fecha y hora |")
    editar(t, "| Paso | Objeto | Tipo | Situación | Sustituye a |\n|---|---|---|---|---|",
           "| Paso | Objeto | Tipo | Situación | Sustituye a | Cambio |\n|---|---|---|---|---|---|")
    lineas, en13 = t.read_text(encoding="utf-8").split("\n"), False
    for k, l in enumerate(lineas):   # las filas de EV-01 llevan su ID (con as-is/, sin ID no son de ninguna unidad)
        en13 = l.startswith("## 13.") or (en13 and not l.startswith("## "))
        if en13 and l.startswith("| ") and l.count("|") == 6 and not l.startswith("| Paso"):
            lineas[k] = l + " EV-01 |"
    t.write_text("\n".join(lineas), encoding="utf-8")
    editar(t, "| 4 | `DEM_INT_NotificarERP` | Integración | Existe | — |",
           "| 4 | `DEM_INT_NotificarERP` | Integración | Existe | — |\n"
           "| 5 | `DEM Solicitud` | Record type | Modifica | — | EV-02 |\n"
           "| 6 | `DEM_ER_Firma` | Regla de expresión | Nuevo | — | EV-02 |\n"
           "| 7 | `DEM_RevisionForm` | Interfaz | Modifica | — | EV-02 |\n"
           "| 7 | `DEM_SolicitudForm` | Interfaz | Modifica | — | EV-02 |\n"
           "| 8 | `DEM Alta Solicitud` | Process model | Modifica | — | EV-03 |")
    editar(t, "| HU-03.1, HU-03.2 |", "| HU-04.1 | Aprobar sin firma |\n| URG-01 | Guardar una solicitud con el importe vacío |\n"
           "| HU-03.1, HU-03.2 |")
    editar(t, "| `DEM_ER_DiasPendiente` | fechaEnvio |", "| `DEM_ER_Firma` | solicitud | Booleano | Si tiene firma (HU-04, FU-04) | "
           "Sin firma: false |\n| `DEM_ER_DiasPendiente` | fechaEnvio |")
    editar(t, "## 3. Modelo de datos", "**DT-04 — Cambio sobre lo construido: EV-02**\n\n| Campo | Contenido |\n|---|---|\n"
           "| **Capa** | Operación |\n| **Necesidad** | HU-02, HU-04 |\n"
           "| **Datos existentes** | `firmaRevisor` queda vacío en las solicitudes que ya hay; no se migra nada |\n"
           "| **Despliegue y vuelta atrás** | Un paquete con los cuatro objetos; vuelta atrás con el de la 1.0 |\n"
           "| **Por qué** | Lo que ya está en producción no se rompe al desplegar (BP 08 §3) |\n"
           "| **Verificado** | No hace falta |\n\n## 3. Modelo de datos")
    editar(d, "| 1.0 | 2026-10-09 | Primera versión del análisis | FU-01, FU-02, FU-03 | — |",
           "| 1.0 | 2026-10-09 | Primera versión del análisis | FU-01, FU-02, FU-03 | — |\n"
           "| 1.1 | 2026-10-12 | Firma de la revisión | FU-04 | — |")
    (destino / "impacto").mkdir()
    cab = ("| # | Tipo | Qué se dice | Encaja en | Cambio propuesto | Revisar también | Requiere | Decisión |\n"
           "|---|---|---|---|---|---|---|---|\n")
    (destino / "impacto" / "FU-04.md").write_text(
        "# Impacto de FU-04 · Firma · 2026-10-12\nAnálisis base: versión 1.0 · Cambio: EV-02 · Estado: aplicado en 1.1\n\n"
        "## Puntos\n" + cab +
        "| 1 | CAMBIA | Al reenviar se borra la firma [FU-04 00:02:00] | HU-02 | HU-02.2 sin la firma | — | — | ✔ |\n"
        "| 2 | NUEVO | El revisor firma [FU-04 00:05:00] | nuevo en funcional §4 | HU-04 y HU-04.1 nuevas; PAN-01 | — | — | ✔ |\n\n"
        "## Aplicado\nVersión 1.1: HU-02.2 · nuevas: HU-04, HU-04.1 · PAN-01\n", encoding="utf-8")
    (destino / "impacto" / "FU-06.md").write_text(
        "# Impacto de FU-06 · Alta desde el panel · 2026-10-14\nAnálisis base: versión 1.1 · Cambio: EV-03 · "
        "Estado: pendiente\n\n## Puntos\n" + cab +
        "| 1 | ALCANCE+ | Dar de alta desde el panel [FU-06 00:01:00] | PAN-03 | PAN-03 con «Nueva solicitud» | — | "
        "Sí (alcance) | Pendiente |\n", encoding="utf-8")
    (destino / "impacto" / "URG-01.md").write_text(
        "# URG-01 · El formulario de la solicitud falla al guardar · 2026-10-15\n"
        "Análisis base: versión 1.1 · Cambio: URG-01 · Estado: sin cambios\n\n## Urgencia\n\n| Campo | Valor |\n|---|---|\n"
        "| Tipo | Defecto |\n| Síntoma | Guardar con el importe vacío da un error |\n"
        "| Quién la declara crítica | Responsable de las solicitudes (FU-07) |\n| Causa | El importe vacío no se comprueba |\n"
        "| Objetos | `DEM_SolicitudForm` |\n| Colisión | EV-02 modifica `DEM_SolicitudForm` |\n"
        "| Dónde se corrige | Entorno de corrección |\n| Despliegue y vuelta atrás | Paquete con el formulario |\n"
        "| Cierre | — |\n", encoding="utf-8")
    (destino / "fuentes").mkdir()
    for n in (4, 5, 6, 7, 8):
        (destino / "fuentes" / f"FU-0{n}-fuente.md").write_text(f"# FU-0{n}\n", encoding="utf-8")
    cambios_md(destino, dict(FILAS_BASE))
    return destino


def fila_de(p, uid):
    """La fila de una unidad en analisis/cambios.md, o ""."""
    t = (p / "analisis" / "cambios.md").read_text(encoding="utf-8") if (p / "analisis" / "cambios.md").exists() else ""
    return next((l for l in t.splitlines() if l.startswith(f"| {uid} ")), "")


def pruebas_unidades(tmp):
    """G5 5.1: proyecto.py cambio con las condiciones de references/cambios.md, estado con las unidades y entregar --cambio."""
    # Abrir crea analisis/cambios.md desde la plantilla, con la versión del análisis al abrirla; dos veces, error
    nuevo = tmp / "unidades nuevo"
    shutil.copytree(EVOLUTIVO, nuevo)
    c, out = corre(S / "proyecto.py", "cambio", nuevo, "EV-01", "abrir", "--titulo", "Devoluciones")
    ok("cambio abrir: crea analisis/cambios.md con la unidad Abierta y la versión al abrirla",
       c == 0 and fila_de(nuevo, "EV-01").startswith("| EV-01 <!-- desde 1.0 --> | Devoluciones | Evolutivo | Abierta |")
       and "| ID | Título | Tipo | Estado |" in (nuevo / "analisis" / "cambios.md").read_text(encoding="utf-8"), out)
    c, out = corre(S / "proyecto.py", "cambio", nuevo, "EV-01", "abrir", "--titulo", "Otra")
    ok("cambio abrir: una unidad que ya existe es error", c == 1 and "ya existe" in out, out)
    c, out = corre(S / "proyecto.py", "cambio", nuevo, "XX-01", "abrir", "--titulo", "Otra")
    ok("cambio: un ID que no es EV-nn ni URG-nn es error", c == 1 and "EV-nn" in out, out)
    c, out = corre(S / "proyecto.py", "cambio", nuevo, "URG-01", "abrir", "--titulo", "Falla")
    ok("cambio abrir URG: Urgente, y dice dónde va su ficha",
       c == 0 and "| Urgente | Abierta |" in fila_de(nuevo, "URG-01") and "impacto/URG-01.md" in out, out)

    # Cada transición: las permitidas pasan y las prohibidas fallan sin tocar cambios.md (una unidad sin nada aplicado)
    extra = {"abrir": ["--titulo", "Otra"], "aprobada": ["--fuente", "FU-05"], "construida": ["--manual"],
             "produccion": ["--ref", "PASE-9"], "descartada": []}
    permitidas = {("EV", "Abierta"): {"aprobada", "descartada"}, ("EV", "Aprobada"): {"aprobada", "construida"},
                  ("EV", "Construida"): {"aprobada", "produccion"}, ("EV", "En producción"): set(),
                  ("EV", "Descartada"): set(), ("URG", "Abierta"): {"produccion", "descartada"},
                  ("URG", "En producción"): set(), ("URG", "Descartada"): set()}
    llega = {"aprobada": "Aprobada", "construida": "Construida", "produccion": "En producción", "descartada": "Descartada"}
    mal = []
    m9 = con_unidades(tmp / "unidades matriz")
    (m9 / "impacto" / "URG-09.md").write_text("# URG-09\nCambio: URG-09 · Estado: sin cambios\n\n## Urgencia\n\n"
                                              "| Campo | Valor |\n|---|---|\n| Tipo | Datos u operación |\n"
                                              "| Dónde se corrige | Producción: se corrige el dato |\n", encoding="utf-8")
    for (pre, estado), bien in permitidas.items():
        uid = f"{pre}-09"
        for orden in extra:
            cambios_md(m9, {**FILAS_BASE, uid: estado})
            antes = (m9 / "analisis" / "cambios.md").read_text(encoding="utf-8")
            c, out = corre(S / "proyecto.py", "cambio", m9, uid, orden, *extra[orden])
            despues = fila_de(m9, uid)
            if orden in bien:
                if c != 0 or f"| {llega[orden]} |" not in despues:
                    mal.append(f"{uid} {estado} → {orden} debería pasar: {out.strip()[-200:]}")
            elif c != 1 or (m9 / "analisis" / "cambios.md").read_text(encoding="utf-8") != antes or "Salida:" not in out:
                mal.append(f"{uid} {estado} → {orden} debería fallar sin tocar cambios.md y decir la salida (sale {c}): "
                           f"{out.strip()[-200:]}")
    ok("cambio: cada transición permitida pasa y cada prohibida falla sin tocar cambios.md, diciendo la salida",
       not mal, "\n".join(mal))

    # Aprobada: con --fuente catalogada, sin puntos pendientes y sin objetos de otra unidad aprobada sin decisión
    p = con_unidades(tmp / "unidades aprobar")
    cambios_md(p, {**FILAS_BASE, "EV-02": "Abierta"})
    for args, falla in [((), "--fuente"), (("--fuente", "FU-99"), "no está en fuentes"),
                        (("--desatendida",), "visto bueno"), (("--fuente", "FU-99", "--desatendida"), "no está en fuentes")]:
        c, out = corre(S / "proyecto.py", "cambio", p, "EV-02", "aprobada", *args)
        ok(f"cambio aprobada {' '.join(args) or 'sin --fuente'}: error ({falla})",
           c == 1 and falla in out and "| Abierta |" in fila_de(p, "EV-02"), out)
    c, out = corre(S / "proyecto.py", "cambio", p, "EV-02", "aprobada", "--fuente", "FU-05", "--desatendida")
    ok("cambio aprobada: pasa con la fuente, también desatendida (el visto bueno es la fuente), y anota fecha y fuente",
       c == 0 and re.search(r"\| Aprobada \| \d{4}-\d\d-\d\d · FU-05 \|", fila_de(p, "EV-02")), out)
    c, out = corre(S / "proyecto.py", "cambio", p, "EV-03", "aprobada", "--fuente", "FU-05")
    ok("cambio aprobada: un punto «Pendiente» en sus informes es error", c == 1 and "FU-06 punto 1" in out, out)
    editar(p / "impacto" / "FU-06.md", "| Sí (alcance) | Pendiente |", "| Sí (alcance) | ✔ FU-05 |")
    editar(p / "analisis" / "tecnico.md", "| 8 | `DEM Alta Solicitud` | Process model | Modifica | — | EV-03 |",
           "| 8 | `DEM Alta Solicitud` | Process model | Modifica | — | EV-03 |\n"
           "| 8 | `DEM_SolicitudForm` | Interfaz | Modifica | — | EV-03 |")
    c, out = corre(S / "proyecto.py", "cambio", p, "EV-03", "aprobada", "--fuente", "FU-05")
    ok("cambio aprobada: un objeto de otra unidad aprobada sin decisión es error, y dice cómo escribirla",
       c == 1 and "EV-02 (DEM_SolicitudForm)" in out and "--comparte" in out and "| Abierta |" in fila_de(p, "EV-03"), out)
    c, out = corre(S / "proyecto.py", "cambio", p, "EV-03", "aprobada", "--fuente", "FU-05", "--comparte",
                   "EV-02 en DEM_SolicitudForm: secuenciar (EV-02 primero)")
    ok("cambio aprobada: con la decisión (--comparte) pasa y queda escrita",
       c == 0 and "| Aprobada |" in fila_de(p, "EV-03") and "secuenciar (EV-02 primero) |" in fila_de(p, "EV-03"), out)
    ok("cambio aprobada: guarda la versión y los informes con que se aprobó",
       "<!-- aprobada 1.1: FU-04 -->" in fila_de(p, "EV-02"), fila_de(p, "EV-02"))

    # A1: lo que se añade a una unidad Aprobada (otro informe, un punto pendiente) no se construye sin aprobarlo
    p = con_unidades(tmp / "unidades crece")
    cambios_md(p, {**FILAS_BASE, "EV-02": "Abierta"})
    corre(S / "proyecto.py", "cambio", p, "EV-02", "aprobada", "--fuente", "FU-05")
    c, out = corre(S / "indice.py", "encargo", p, "EV-02")
    ok("A1: el encargo de la unidad tal como se aprobó se genera", c == 0, out)
    (p / "impacto" / "FU-11.md").write_text(
        "# Impacto de FU-11\nAnálisis base: versión 1.1 · Cambio: EV-02 · Estado: aplicado en 1.2; pendientes de "
        "aprobación: punto 1\n\n## Puntos\n| # | Tipo | Qué se dice | Encaja en | Cambio propuesto | Revisar también | "
        "Requiere | Decisión |\n|---|---|---|---|---|---|---|---|\n"
        "| 1 | ALCANCE+ | Firmar también en el panel [FU-08 00:01:00] | PAN-03 | PAN-03 con la firma | — | Sí (alcance) "
        "| Pendiente |\n| 2 | CAMBIA | La firma lleva fecha [FU-08 00:02:00] | HU-04 | HU-04.1 con la fecha | — | — | ✔ |\n",
        encoding="utf-8")
    editar(p / "analisis" / "tecnico.md", "| 8 | `DEM Alta Solicitud` | Process model | Modifica | — | EV-03 |",
           "| 8 | `DEM Alta Solicitud` | Process model | Modifica | — | EV-03 |\n| 9 | `DEM_Dashboard` | Interfaz | Modifica | — | EV-02 |")
    c, out = corre(S / "indice.py", "encargo", p, "EV-02")
    ok("A1: con un informe nuevo de la unidad después de aprobarla, el encargo es error y dice cómo volver a aprobarla",
       c == 1 and "EV-02 ha crecido desde que se aprobó" in out and "FU-11" in out and "aprobada --fuente" in out
       and "DEM_Dashboard" not in (p / "construccion" / "EV-02.md").read_text(encoding="utf-8"), out)
    (p / "construccion" / "verificacion").mkdir(parents=True)
    (p / "construccion" / "verificacion" / "EV-02.json").write_text(json.dumps({"objetos": [
        {"pedido": o, "existe": True, "diferencias": {}} for o in
        ("DEM Solicitud", "DEM_ER_Firma", "DEM_RevisionForm", "DEM_SolicitudForm", "DEM_Dashboard")]}), encoding="utf-8")
    c, out = corre(S / "proyecto.py", "cambio", p, "EV-02", "construida", "--reaplicada", "URG-01")
    ok("A1: construida también es error («ha crecido») y no cambia el estado",
       c == 1 and "EV-02 ha crecido desde que se aprobó" in out and "| Aprobada |" in fila_de(p, "EV-02"), out)
    c, out = corre(S / "proyecto.py", "cambio", p, "EV-02", "aprobada", "--fuente", "FU-08")
    ok("A1: volver a aprobarla con un punto pendiente es error", c == 1 and "FU-11 punto 1" in out, out)
    editar(p / "impacto" / "FU-11.md", "| Sí (alcance) | Pendiente |", "| Sí (alcance) | ✔ FU-08 |")
    c, out = corre(S / "proyecto.py", "cambio", p, "EV-02", "aprobada", "--fuente", "FU-08")
    c2, out2 = corre(S / "indice.py", "encargo", p, "EV-02")
    ok("A1: aprobada otra vez desde Aprobada, el encargo crece con lo nuevo",
       c == 0 and "aprobada 1.1: FU-04, FU-11" in fila_de(p, "EV-02") and "· FU-08 |" in fila_de(p, "EV-02")
       and c2 == 0 and "`DEM_Dashboard`" in (p / "construccion" / "EV-02.md").read_text(encoding="utf-8"), out + out2)

    # Construida: verificación sin diferencias (o --manual) y cada «reaplicar URG-nn» confirmado
    p = con_unidades(tmp / "unidades construir")
    ver = p / "construccion" / "verificacion" / "EV-02.json"
    bien = {"objetos": [{"pedido": "DEM Solicitud", "existe": True, "diferencias": {"sobranCampos": ["titulo"]}},
                        {"pedido": "DEM_ER_Firma", "existe": True, "diferencias": {}},
                        {"pedido": "DEM_RevisionForm", "existe": True, "diferencias": {}},
                        {"pedido": "DEM_SolicitudForm", "existe": True, "diferencias": {}}],
            "faltan": [], "conDiferencias": ["DEM Solicitud"]}
    c, out = corre(S / "proyecto.py", "cambio", p, "EV-02", "construida", "--reaplicada", "URG-01")
    ok("cambio construida: sin verificar es error y dice dónde está la orden",
       c == 1 and "construccion/verificacion/EV-02.json" in out and "construccion/EV-02.md" in out, out)
    ver.parent.mkdir(parents=True)
    for nombre, datos, falla in [
            ("un objeto nuevo que no existe", {**bien, "objetos": bien["objetos"][:1] + [
                {"pedido": "DEM_ER_Firma", "existe": False, "diferencias": {"falta": True}}] + bien["objetos"][2:]},
             "DEM_ER_Firma: falta"),
            ("un campo de otro tipo", {**bien, "objetos": [{"pedido": "DEM Solicitud", "existe": True, "diferencias": {
                "camposDeOtroTipo": [{"nombre": "firmaRevisor"}]}}] + bien["objetos"][1:]}, "DEM Solicitud: camposDeOtroTipo"),
            ("sin uno de sus objetos", {**bien, "objetos": bien["objetos"][:3]}, "no incluye DEM_SolicitudForm"),
            ("campos que no se pudieron leer", {**bien, "objetos": [{"pedido": "DEM Solicitud", "existe": True,
                                                                    "diferencias": {"camposSinLeer": True}}]
                                                + bien["objetos"][1:]}, "no se pudo leer DEM Solicitud")]:
        ver.write_text(json.dumps(datos), encoding="utf-8")
        c, out = corre(S / "proyecto.py", "cambio", p, "EV-02", "construida", "--reaplicada", "URG-01")
        ok(f"cambio construida: verificación con {nombre} es error", c == 1 and falla in out and "Salida:" in out
           and ("--manual" in out) == (nombre == "campos que no se pudieron leer")
           and ("no es lo del técnico" in out) == (nombre in ("un objeto nuevo que no existe", "un campo de otro tipo")), out)
    ver.write_text(json.dumps(bien), encoding="utf-8")
    c, out = corre(S / "proyecto.py", "cambio", p, "EV-02", "construida")
    ok("cambio construida: sin --reaplicada de la URG corregida en el entorno de corrección es error",
       c == 1 and "URG-01 en DEM_SolicitudForm" in out and "--reaplicada URG-01" in out, out)
    c, out = corre(S / "proyecto.py", "estado", p)
    ok("proyecto.py estado: unidades en curso con fuentes, versión y objetos, y lo que hay que reaplicar",
       c == 0 and re.search(r"EV-02 · Firma de la revisión · Aprobada · fuentes: FU-04 · versión: 1\.1 · objetos: "
                            r"DEM Solicitud, DEM_ER_Firma, DEM_RevisionForm, DEM_SolicitudForm", out)
       and "reaplicar URG-01 en DEM_SolicitudForm" in out and "EV-01 ·" not in out
       and "URG-01 · El formulario de la solicitud falla · Abierta" in out, out)
    c, out = corre(S / "proyecto.py", "cambio", p, "EV-02", "construida", "--reaplicada", "URG-01")
    ok("cambio construida: con la verificación (sobranCampos de un objeto que se modifica no cuenta) y --reaplicada pasa; "
       "la URG queda reaplicada",
       c == 0 and re.search(r"\| Construida \| [^|]+ · FU-05 \| \d{4}-\d\d-\d\d · verificada \|", fila_de(p, "EV-02"))
       and "reaplicada en EV-02" in fila_de(p, "URG-01"), out)
    c, out = corre(S / "proyecto.py", "cambio", p, "EV-02", "aprobada")
    ok("cambio aprobada desde Construida: vuelve a Aprobada (otra URG obliga a reaplicar) sin perder la aprobación",
       c == 0 and "| Aprobada | " in fila_de(p, "EV-02") and "· FU-05 | — |" in fila_de(p, "EV-02"), out)
    c, out = corre(S / "proyecto.py", "cambio", p, "EV-02", "construida", "--manual")
    ok("cambio construida --manual: la URG ya reaplicada no se pide otra vez y la marca dice «manual»",
       c == 0 and "· manual |" in fila_de(p, "EV-02"), out)
    for args, falla in [(("--ref", "PASE-2", "--desatendida"), "visto bueno"), ((), "--ref")]:
        c, out = corre(S / "proyecto.py", "cambio", p, "EV-02", "produccion", *args)
        ok(f"cambio produccion {' '.join(args) or 'sin --ref'}: error", c == 1 and falla in out, out)
    c, out = corre(S / "proyecto.py", "cambio", p, "EV-02", "produccion", "--ref", "PASE-2", "--fecha", "8/10/2026")
    ok("cambio produccion --fecha que no es AAAA-MM-DD: error", c == 1 and "AAAA-MM-DD" in out, out)
    c, out = corre(S / "proyecto.py", "cambio", p, "EV-02", "produccion", "--ref", "PASE-2", "--desatendida",
                   "--fuente", "FU-05", "--fecha", "2026-10-08")
    ok("cambio produccion: desatendida con el visto bueno (--fuente) pasa, anota la referencia y recuerda actualizar el "
       "entorno de corrección",
       c == 0 and "| 2026-10-08 · PASE-2 |" in fila_de(p, "EV-02") and "entorno de corrección" in out, out)
    editar(p / "impacto" / "URG-01.md", "| Dónde se corrige | Entorno de corrección |", "| Dónde se corrige | — |")
    c, out = corre(S / "proyecto.py", "cambio", p, "URG-01", "produccion", "--ref", "URG")
    ok("cambio produccion de una URG sin «Dónde se corrige» en su ficha es error", c == 1 and "Dónde se corrige" in out, out)

    # M1: un «Dónde se corrige» que no dice desarrollo ni entorno de corrección, con unidades que chocan, es error; sin
    # choque, pasa. B1: tras el pase, estado no lista la ficha como pendiente
    p = con_unidades(tmp / "unidades urgente")
    editar(p / "impacto" / "URG-01.md", "| Dónde se corrige | Entorno de corrección |",
           "| Dónde se corrige | En el entorno de pruebas |")
    editar(p / "impacto" / "URG-01.md", "Estado: sin cambios", "Estado: pendiente")
    c, out = corre(S / "proyecto.py", "cambio", p, "URG-01", "produccion", "--ref", "URG-1")
    ok("M1: produccion de una URG con «Dónde se corrige» que no se reconoce y unidades que chocan es error",
       c == 1 and "EV-02" in out and "Desarrollo" in out and "Entorno de corrección" in out and "Salida:" in out
       and "| Abierta |" in fila_de(p, "URG-01"), out)
    c, out = corre(S / "proyecto.py", "estado", p)
    ok("B1: antes del pase, estado lista la ficha de la URG pendiente", "URG-01.md" in out, out)
    editar(p / "impacto" / "URG-01.md", "| Dónde se corrige | En el entorno de pruebas |",
           "| Dónde se corrige | Entorno de corrección |")
    c, out = corre(S / "proyecto.py", "cambio", p, "URG-01", "produccion", "--ref", "URG-1")
    c2, out2 = corre(S / "proyecto.py", "estado", p)
    ok("B1: tras el pase, estado no lista la ficha de la URG como pendiente",
       c == 0 and c2 == 0 and "URG-01.md" not in out2, out + out2)
    (p / "impacto" / "URG-02.md").write_text(
        "# URG-02 · El panel de administración no carga\nAnálisis base: versión 1.1 · Cambio: URG-02 · Estado: pendiente\n\n"
        "## Urgencia\n\n| Campo | Valor |\n|---|---|\n| Tipo | Defecto |\n| Objetos | `DEM_ER_EsAdmin` |\n"
        "| Dónde se corrige | Desarrollo |\n", encoding="utf-8")
    corre(S / "proyecto.py", "cambio", p, "URG-02", "abrir", "--titulo", "El panel no carga")
    c, out = corre(S / "indice.py", "colision", p, "URG-02")
    c2, out2 = corre(S / "indice.py", "cambios", p, "EV-02", "--json")
    ok("URG sin colisión: colision dice «no» (aunque la usen otros objetos) y ninguna unidad la reaplica ni la congela",
       c == 0 and "los usan: DEM_SolicitudResumen" in out and "Colisión: no" in out and "congelados" in out
       and all(x["urgente"] != "URG-02" for k in ("reaplicar", "congelados") for x in json.loads(out2)[k]), out + out2)
    editar(p / "impacto" / "URG-02.md", "| Dónde se corrige | Desarrollo |", "| Dónde se corrige | Producción |")
    c, out = corre(S / "proyecto.py", "cambio", p, "URG-02", "produccion", "--ref", "URG-2")
    ok("M1: sin choques, un «Dónde se corrige» distinto no impide el pase", c == 0, out)

    # Descartada: sin nada aplicado; con algo aplicado, solo con el informe (aplicado) que lo deshace
    p = con_unidades(tmp / "unidades descartar")
    cambios_md(p, {**FILAS_BASE, "EV-02": "Abierta"})
    c, out = corre(S / "proyecto.py", "cambio", p, "EV-02", "descartada")
    ok("cambio descartada con cambios aplicados y sin --informe es error", c == 1 and "--informe" in out and "HU-04" in out, out)
    c, out = corre(S / "proyecto.py", "cambio", p, "EV-02", "descartada", "--informe", "impacto/FU-06.md")
    ok("cambio descartada con un informe sin aplicar es error", c == 1 and "no está aplicado" in out, out)
    (p / "impacto" / "FU-08.md").write_text("# Impacto de FU-08\nAnálisis base: versión 1.1 · Cambio: EV-02 · "
                                            "Estado: aplicado en 1.2\n", encoding="utf-8")
    c, out = corre(S / "proyecto.py", "cambio", p, "EV-02", "descartada", "--informe", "impacto/FU-08.md")
    ok("cambio descartada con el informe aplicado pero con sus filas en §13 es error", c == 1 and "§13" in out, out)
    t = p / "analisis" / "tecnico.md"
    t.write_text("\n".join(l for l in t.read_text(encoding="utf-8").split("\n") if "| EV-02 |" not in l), encoding="utf-8")
    c, out = corre(S / "proyecto.py", "cambio", p, "EV-02", "descartada", "--informe", "impacto/FU-08.md")
    ok("cambio descartada con el informe aplicado que lo deshace pasa", c == 0 and "| Descartada |" in fila_de(p, "EV-02"), out)

    # entregar --cambio: el DF del cambio en la fila de su versión de decisiones.md y en «Entregados»
    p = con_unidades(tmp / "unidades entregar")
    c, out = corre(S / "proyecto.py", "entregar", p, "--cambio", "EV-02")
    ok("entregar --cambio sin el Word del cambio: error que dice cómo generarlo", c == 1 and "--cambio EV-02" in out, out)
    (p / "entregables").mkdir(exist_ok=True)
    (p / "entregables" / "DF-Devoluciones-de-solicitudes-EV-02-v1.1.docx").write_bytes(b"word")
    pm_antes = (p / "proyecto.md").read_text(encoding="utf-8")
    c, out = corre(S / "proyecto.py", "entregar", p, "--cambio", "EV-02")
    dec = (p / "analisis" / "decisiones.md").read_text(encoding="utf-8")
    pm = (p / "proyecto.md").read_text(encoding="utf-8")
    hoy = __import__("datetime").date.today().isoformat()
    ok("entregar --cambio: «DF del cambio EV-02 entregado» en la fila 1.1 y el fichero en «Entregados»; «DF entregado» no cambia",
       c == 0 and f"| 1.1 | 2026-10-12 | Firma de la revisión | FU-04 | DF del cambio EV-02 entregado {hoy} |" in dec
       and "Entregados: DF-Devoluciones-de-solicitudes-EV-02-v1.1.docx" in pm
       and pm.split("\n")[3] == pm_antes.split("\n")[3], out + dec + pm)

    # Un informe sin «Cambio» es de la única unidad Abierta, si es de después de abrirla; con dos Abiertas, estado avisa
    p = con_unidades(tmp / "unidades sin cabecera")
    for n, base in (("FU-10", "1.1"), ("FU-11", "1.0")):
        (p / "impacto" / f"{n}.md").write_text(f"# Impacto de {n}\nAnálisis base: versión {base} · Estado: aplicado en 1.2\n\n"
                                               "## Aplicado\nVersión 1.2: HU-03\n", encoding="utf-8")
    c, out = corre(S / "proyecto.py", "estado", p)
    ok("proyecto.py estado: con dos unidades Abiertas, avisa del informe sin «Cambio»",
       c == 0 and "impacto/FU-10.md no dice «Cambio:»" in out, out)
    cambios_md(p, {**FILAS_BASE, "URG-01": "En producción",
                   "EV-03": FILAS_BASE["EV-03"].replace("| EV-03 |", "| EV-03 <!-- desde 1.1 --> |")})
    c, out = corre(S / "proyecto.py", "estado", p)
    ok("proyecto.py estado: sin «Cambio», el informe de después de abrirla es de la única Abierta; el de antes, no",
       c == 0 and "fuentes: FU-06, FU-10 ·" in out and "no dice «Cambio:»" not in out, out)

    # M2: en una aplicación ajena (as-is/), abrir el primer evolutivo como EV-01 no le da las filas de §13 sin ID
    p = tmp / "unidades ajena EV-01"
    shutil.copytree(EVOLUTIVO, p)
    editar(p / "analisis" / "tecnico.md", "| Paso | Objeto | Tipo | Situación | Sustituye a |\n|---|---|---|---|---|",
           "| Paso | Objeto | Tipo | Situación | Sustituye a | Cambio |\n|---|---|---|---|---|---|")
    corre(S / "proyecto.py", "cambio", p, "EV-01", "abrir", "--titulo", "Primer evolutivo")
    c, out = corre(S / "proyecto.py", "estado", p)
    ok("M2: con as-is/, el primer evolutivo EV-01 no se queda con las filas de §13 sin ID",
       c == 0 and "EV-01 · Primer evolutivo · Abierta · fuentes: — · versión: — · objetos: —" in out, out)

    # Sin analisis/cambios.md, estado no habla de unidades
    c, out = corre(S / "proyecto.py", "estado", EVOLUTIVO)
    ok("sin analisis/cambios.md, proyecto.py estado no habla de unidades", c == 0 and "Unidades" not in out, out)

    # 5.2 Señales calculadas: «Construido: … · En curso: …» por pieza en ficha e impacto
    p = con_unidades(tmp / "unidades señales")
    for pid, senal in [("HU-02", "Construido: as-is · En curso: EV-02"), ("HU-04", "Construido: — · En curso: EV-02"),
                       ("HU-01", "Construido: as-is · En curso: —"), ("HU-04.1", "Construido: — · En curso: EV-02")]:
        c, out = corre(S / "indice.py", "ficha", p, pid)
        ok(f"indice.py ficha {pid}: «{senal}»", c == 0 and senal in out, out)
    c, out = corre(S / "indice.py", "impacto", p, "HU-02")
    ok("indice.py impacto: la señal por pieza, «Posible petición de cambio» y «Requiere: Sí (EV-02)» para copiarlas",
       c == 0 and "Construido: as-is · En curso: EV-02" in out and "Posible petición de cambio" in out
       and "Requiere: Sí (EV-02)" in out, out)
    c, out = corre(S / "indice.py", "impacto", p, "PAN-01", "--cambio", "EV-03")
    ok("indice.py impacto --cambio EV-03 de una pantalla construida: la fila de técnico §13 que lleva, con el objeto que "
       "la implementa (el primero de su fila de §7), el siguiente paso y la unidad",
       c == 0 and "Técnico §13" in out and "| 9 | `DEM_RevisionForm` | Interfaz | Modifica | — | EV-03 |" in out, out)
    c, out = corre(S / "indice.py", "impacto", p, "PAN-01")
    ok("indice.py impacto sin --cambio, con URG-01 y EV-03 Abiertas: la fila de §13 es de la única EV Abierta",
       c == 0 and "| 9 | `DEM_RevisionForm` | Interfaz | Modifica | — | EV-03 |" in out and "de URG-01" not in out, out)
    c, out = corre(S / "indice.py", "impacto", p, "HU-02", "--cambio", "EV-03")
    ok("indice.py impacto de una historia construida: la fila de §13 con el objeto de la fila de su pantalla (PAN-02)",
       c == 0 and "`DEM_SolicitudForm` | Interfaz | Modifica | — | EV-03 |" in out, out)
    sin_t = tmp / "unidades sin técnico"
    shutil.copytree(p, sin_t)
    (sin_t / "analisis" / "tecnico.md").unlink()
    c, out = corre(S / "indice.py", "impacto", sin_t, "PAN-01", "--cambio", "EV-03")
    ok("indice.py impacto con unidades y sin técnico todavía: sin fila de §13 y sin fallar",
       c == 0 and "Traceback" not in out and "Técnico §13" not in out, out)
    c, out = corre(S / "indice.py", "impacto", p, "HU-02", "--cambio", "EV-02")
    ok("B4: indice.py impacto --cambio EV-02 no sugiere «Requiere: Sí (EV-02)» para la propia unidad",
       c == 0 and "Construido: as-is · En curso: EV-02" in out and "Requiere: Sí" not in out, out)
    c, out = corre(S / "indice.py", "impacto", p, "HU-01")
    ok("indice.py impacto con una unidad Abierta no sugiere abrir otra", c == 0 and "Ninguna unidad Abierta" not in out, out)
    cambios_md(p, {**FILAS_BASE, "EV-03": "Descartada"})
    c, out = corre(S / "indice.py", "impacto", p, "HU-01")
    ok("indice.py impacto sin unidad Abierta y algo construido: dice que abra EV-04 y no la meta en la Aprobada",
       c == 0 and "Ninguna unidad Abierta" in out and "EV-04 abrir" in out and "Cambio: EV-04" in out, out)
    cambios_md(p, {**FILAS_BASE, "EV-02": "En producción"})
    c, out = corre(S / "indice.py", "ficha", p, "HU-04")
    ok("indice.py ficha: lo de una unidad en producción está construido", "Construido: EV-02 · En curso: —" in out, out)
    c, out = corre(S / "indice.py", "ficha", EVOLUTIVO, "HU-02")
    ok("indice.py ficha sin analisis/cambios.md: sin señales", c == 0 and "Construido:" not in out, out)
    nueva = tmp / "unidades aplicación nueva"
    shutil.copytree(EJEMPLO, nueva)
    cambios_md(nueva, {"EV-01": FILAS_BASE["EV-01"].replace("Devoluciones", "Construcción inicial")})
    c, out = corre(S / "indice.py", "ficha", nueva, "HU-01")
    ok("aplicación nueva: lo que no es de ninguna unidad es de la construcción inicial (EV-01)",
       "Construido: EV-01 · En curso: —" in out, out)
    (nueva / "impacto").mkdir()
    (nueva / "impacto" / "FU-04.md").write_text(
        "# Impacto de FU-04\nAnálisis base: versión 1.1 · Cambio: EV-02 · Estado: aplicado en 1.2\n\n## Puntos\n"
        "| # | Tipo | Qué se dice | Encaja en | Cambio propuesto | Revisar también | Requiere | Decisión |\n"
        "|---|---|---|---|---|---|---|---|\n| 1 | CAMBIA | Otro texto [FU-04 00:01:00] | HU-01 | HU-01.1 con otro texto | — | — "
        "| ✔ |\n", encoding="utf-8")
    cambios_md(nueva, {"EV-01": FILAS_BASE["EV-01"], "EV-02": "Abierta"})
    c, out = corre(S / "indice.py", "ficha", nueva, "HU-01")
    ok("M4: aplicación nueva: lo que construyó EV-01 sigue «Construido: EV-01» cuando lo cambia otra unidad",
       c == 0 and "Construido: EV-01 · En curso: EV-02" in out, out)
    (nueva / "impacto" / "FU-04.md").unlink()
    cambios_md(nueva, {"EV-01": FILAS_BASE["EV-01"].replace("Devoluciones", "Construcción inicial")})
    c, out = corre(S / "comprobar.py", nueva)
    ok("aplicación nueva con unidades y §13 en lista: sin comprobaciones de Situación", c == 0 and "Situación" not in out,
       out)
    t = nueva / "analisis" / "tecnico.md"
    t.write_text(re.sub(r"(?ms)^## 13\. .*?(?=^## 14\.)", lambda _: (
        "## 13. Plan de construcción\n\n| Paso | Objeto | Tipo | Situación | Sustituye a | Cambio |\n|---|---|---|---|---|---|\n"
        "| 1 | `AUT Solicitud` | Record type | Nuevo | — | |\n| 1 | `AUT_GenerarNumero` | Regla de expresión | Nuevo | — | |\n"
        "| 2 | `AUT Solicitud` | Record type | Modifica | — | EV-02 |\n| 2 | `AUT_GenerarNumero` | Regla de expresión | "
        "Nuevo | — | EV-02 |\n\n"), t.read_text(encoding="utf-8")), encoding="utf-8")
    cambios_md(nueva, {"EV-01": FILAS_BASE["EV-01"], "EV-02": FILAS_BASE["EV-02"]})
    c, out = corre(S / "comprobar.py", nueva)
    ok("aplicación nueva: «Modifica» de lo que construyó EV-01 vale; «Nuevo» de lo mismo es error",
       c == 1 and any(l.startswith("✗ técnico §13") and "AUT_GenerarNumero" in l and "lo construido" in l
                      and "AUT Solicitud" not in l for l in out.splitlines()), out)
    # El informe admite la cabecera «Cambio», una columna «Cambio» por punto y «Requiere: Sí (EV-02)»
    (p / "impacto" / "FU-09.md").write_text(
        "# Impacto de FU-09\nAnálisis base: versión 1.1 · Cambio: EV-03 · Estado: pendiente\n\n## Resumen\n"
        "- Posible petición de cambio: punto 1\n\n## Puntos\n"
        "| # | Tipo | Qué se dice | Encaja en | Cambio propuesto | Revisar también | Requiere | Decisión | Cambio |\n"
        "|---|---|---|---|---|---|---|---|---|\n"
        "| 1 | COMPLETA | El comentario se ve en rojo [FU-08 00:01:00] | HU-02 | HU-02.1 en rojo | — | Sí (EV-02) | Pendiente | EV-03 |\n"
        "| 2 | COMPLETA | La firma lleva la fecha [FU-08 00:02:00] | HU-04 | HU-04.1 con la fecha | — | — | ✔ | EV-02 |\n",
        encoding="utf-8")
    c, out = corre(S / "comprobar.py", p, "--impacto", p / "impacto" / "FU-09.md")
    ok("comprobar.py --impacto admite «Cambio», la columna por punto y «Requiere: Sí (EV-02)»",
       c == 0 and "✓ «Requiere» de cada punto" in out, out)
    c, out = corre(S / "proyecto.py", "cambio", p, "EV-03", "aprobada", "--fuente", "FU-05")
    c2, out2 = corre(S / "indice.py", "ficha", p, "HU-02.1")
    ok("con columna «Cambio», cada punto es de su unidad: el pendiente de EV-03 impide aprobarla y HU-02.1 está en curso "
       "en EV-03, no en EV-02",
       c == 1 and "FU-09 punto 1" in out and "FU-06 punto 1" in out and "En curso: EV-03" in out2, out + out2)

    # 5.3 y 5.9 Técnico por unidad: completitud solo de lo de las unidades en curso, Situación contra la línea base,
    # DT «Cambio sobre lo construido» por tipo de objeto y avisos que se apagan solos
    p = con_unidades(tmp / "unidades técnico")
    c, out = corre(S / "comprobar.py", p)
    avisos = [l for l in out.splitlines() if l.startswith("· ")]
    ok("con unidades: el proyecto pasa comprobar.py", c == 0, out)
    editar(p / "analisis" / "tecnico.md", "| 2 | `DEM_ER_DiasPendiente` | Regla de expresión | Nuevo | — | EV-01 |",
           "| 2 | `DEM_ER_DiasPendiente` | Regla de expresión | Nuevo | — | EV-01 |\n"
           "| 2 | `DEM_ER_EsAdmin` | Regla de expresión | Nuevo | — | EV-01 |")
    c, out = corre(S / "comprobar.py", p)
    ok("las filas de una unidad ya construida (EV-01, en producción) no se vuelven a mirar: su «Nuevo» de hoy no es error",
       c == 0 and not any(l.startswith("✗") for l in out.splitlines()), out)
    cambios_md(p, {**FILAS_BASE, "EV-01": "Aprobada"})
    c, out = corre(S / "comprobar.py", p)
    ok("… y las de una unidad sin construir sí", c == 1 and any(
        l.startswith("✗ técnico §13") and "DEM_ER_EsAdmin" in l for l in out.splitlines()), out)
    cambios_md(p, dict(FILAS_BASE))
    editar(p / "analisis" / "tecnico.md", "\n| 2 | `DEM_ER_EsAdmin` | Regla de expresión | Nuevo | — | EV-01 |", "")
    ok("aviso: EV-03 modifica un process model construido y no tiene su DT «Cambio sobre lo construido»",
       any("Cambio sobre lo construido" in l and "EV-03: «Procesos en curso» (DEM Alta Solicitud)" in l
           and "«Despliegue y vuelta atrás»" in l and "EV-02" not in l for l in avisos), out)
    editar(p / "analisis" / "tecnico.md", "| **Datos existentes** | `firmaRevisor` queda vacío en las solicitudes que ya hay; "
           "no se migra nada |\n", "")
    c, out = corre(S / "comprobar.py", p)
    ok("aviso: a la DT de EV-02 le falta «Datos existentes» (modifica un record type construido)",
       c == 0 and any(l.startswith("· ") and "EV-02: «Datos existentes» (DEM Solicitud)" in l for l in out.splitlines()), out)
    editar(p / "analisis" / "tecnico.md", "| 7 | `DEM_RevisionForm` | Interfaz | Modifica | — | EV-02 |\n",
           "| 7 | `DEM_RevisionForm` | Interfaz | Modifica | — | EV-02 |\n| 7 | `DEM_ER_DiasPendiente` | Regla de expresión | "
           "Nuevo | — | EV-02 |\n")
    c, out = corre(S / "comprobar.py", p)
    ok("Situación: «Nuevo» de un objeto que construyó otra unidad (EV-01) es error",
       c == 1 and any(l.startswith("✗ técnico §13") and "DEM_ER_DiasPendiente" in l and "lo construido" in l
                      for l in out.splitlines()), out)
    editar(p / "analisis" / "tecnico.md", "| 7 | `DEM_ER_DiasPendiente` | Regla de expresión | Nuevo | — | EV-02 |\n", "")
    editar(p / "analisis" / "tecnico.md", "| 8 | `DEM Alta Solicitud` | Process model | Modifica | — | EV-03 |",
           "| 8 | `DEM Alta Solicitud` | Process model | Modifica | — | EV-03 |\n| 8 | `DEM_ER_Firma` | Regla de expresión | "
           "Modifica | — | EV-03 |")
    c, out = corre(S / "comprobar.py", p)
    ok("Situación: «Modifica» de lo que crea una unidad aún sin construir (EV-02) es error",
       c == 1 and any(l.startswith("✗ técnico §13") and "DEM_ER_Firma" in l for l in out.splitlines()), out)
    cambios_md(p, {**FILAS_BASE, "EV-02": "Construida"})
    c, out = corre(S / "comprobar.py", p)
    ok("Situación: con EV-02 Construida, su DEM_ER_Firma es línea base y EV-03 puede modificarlo",
       not any(l.startswith("✗ técnico §13") for l in out.splitlines()), out)
    cambios_md(p, dict(FILAS_BASE))
    editar(p / "analisis" / "tecnico.md", "| 8 | `DEM_ER_Firma` | Regla de expresión | Modifica | — | EV-03 |", "")
    t = p / "analisis" / "tecnico.md"
    sin_pan = lambda pan: "\n".join(l for l in t.read_text(encoding="utf-8").split("\n") if not l.startswith(f"| {pan} |"))
    t.write_text(sin_pan("PAN-03"), encoding="utf-8")
    c, out = corre(S / "comprobar.py", p)
    ok("completitud: con el técnico completo, una pantalla que no toca ninguna unidad en curso no hace falta en §7",
       c == 0 and "✓ técnico §7: cada pantalla" in out, out)
    t.write_text(sin_pan("PAN-01"), encoding="utf-8")
    c, out = corre(S / "comprobar.py", p)
    ok("completitud: una pantalla de EV-02 sin su fila en §7 es error", c == 1 and any(
        l.startswith("✗ técnico §7") and "PAN-01" in l for l in out.splitlines()), out)
    p = con_unidades(tmp / "unidades reflejo")
    t = p / "analisis" / "tecnico.md"
    t.write_text("\n".join(l for l in t.read_text(encoding="utf-8").split("\n") if "| EV-02 |" not in l), encoding="utf-8")
    editar(t, "**DT-04 — Cambio sobre lo construido: EV-02**", "**DT-04 — Firma**")
    c, out = corre(S / "comprobar.py", p)
    linea = next((l for l in out.splitlines() if "se refleja en el técnico" in l), "")
    ok("aviso: un punto aplicado sin filas de §13 de su unidad ni DT que cite su fuente",
       c == 0 and linea.startswith("· ") and "EV-02: FU-04 punto 1" in linea and "EV-02: FU-04 punto 2" in linea, out)
    editar(p / "impacto" / "FU-04.md", "| HU-02.2 sin la firma | — | — | ✔ |",
           "| HU-02.2 sin la firma; Sin cambio técnico: lo hace el formulario que ya está | — | — | ✔ |")
    editar(t, "| **Necesidad** | HU-02, HU-04 |", "| **Necesidad** | HU-02, HU-04 (FU-04) |")
    c, out = corre(S / "comprobar.py", p)
    ok("aviso que se apaga solo: con «Sin cambio técnico: …» en el punto y una DT que cita la fuente",
       c == 0 and "✓ unidades: cada punto aplicado se refleja" in out, out)
    editar(t, "| URG-01 | Guardar una solicitud con el importe vacío |\n", "")
    c, out = corre(S / "comprobar.py", p)
    ok("aviso: un defecto urgente sin la prueba que lo reproduce en §14",
       c == 0 and any(l.startswith("· urgentes") and "URG-01" in l for l in out.splitlines()), out)
    c, out = corre(S / "comprobar.py", EVOLUTIVO)
    ok("sin analisis/cambios.md, comprobar.py no habla de unidades ni de urgentes",
       "unidades" not in out and "urgentes" not in out, out)
    # B2: con unidades y sin saber qué es de otra aplicación, «Existe» de un objeto que no está no es aviso (no se apagaría);
    # «Modifica», sí
    t = nueva / "analisis" / "tecnico.md"
    editar(t, "| 2 | `AUT_GenerarNumero` | Regla de expresión | Nuevo | — | EV-02 |",
           "| 2 | `UTL_Calendario` | Regla de otra aplicación | Existe | — | EV-02 |\n"
           "| 2 | `UTL_Festivos` | Regla de otra aplicación | Modifica | — | EV-02 |")
    c, out = corre(S / "comprobar.py", nueva)
    linea = next((l for l in out.splitlines() if "ninguna unidad ha construido" in l), "")
    ok("B2: «Existe» de un objeto que ninguna unidad ha construido no es aviso; «Modifica», sí",
       c == 0 and linea.startswith("· ") and "UTL_Festivos" in linea and "UTL_Calendario" not in out, out)

    # 5.4 Derivados: indice.py cambios, colision y encargo; df_docx.js --cambio
    p = con_unidades(tmp / "unidades derivados")
    c, out = corre(S / "indice.py", "cambios", p, "EV-02", "--json")
    try:
        r = json.loads(out)
    except ValueError:
        r = {}
    cambian = {x["id"]: x for x in r.get("piezas", {}).get("cambian", [])}
    ok("indice.py cambios --json: nuevas, cambian (con antes y después frente a versiones/) y las que se conservan (T5)",
       c == 0 and [x["id"] for x in r["piezas"]["nuevas"]] == ["HU-04"] and set(cambian) == {"HU-02", "PAN-01"}
       and any("sin la firma anterior" in l for l in cambian["HU-02"]["despues"])
       and any("con el mismo número." in l for l in cambian["HU-02"]["antes"])
       and r["historias"]["seConservan"] == ["HU-01"] and r["pantallas"] == ["PAN-01", "PAN-02"], out)
    ok("indice.py cambios --json: objetos, pruebas a repetir (criterios, escenarios y la URG sobre sus objetos), "
       "colisión con la URG y lo que hay que reaplicar",
       bool(r) and [o["objeto"] for o in r["objetos"]] == ["DEM Solicitud", "DEM_ER_Firma", "DEM_RevisionForm",
                                                           "DEM_SolicitudForm"]
       and r["pruebas"]["criterios"] == ["HU-01.1", "HU-01.2", "HU-02.1", "HU-02.2", "HU-04.1"]   # HU-01: su PAN-01 cambia
       and r["pruebas"]["escenarios"] == ["ESC-01"]
       and [g["id"] for g in r["pruebas"]["urgentes"]] == ["URG-01"] and "importe vacío" in r["pruebas"]["urgentes"][0]["prueba"]
       and [x["unidad"] for x in r["colisiones"]] == ["URG-01"]
       and r["reaplicar"] == [{"urgente": "URG-01", "objetos": ["DEM_SolicitudForm"]}]
       and "DT-04" in r["tecnico"] and "§13" in r["tecnico"], out)
    ok("M5: indice.py cambios --json trae los datos de §6 que cambian (solo los nuevos o cambiados)",
       bool(r) and r.get("datos") == [{"entidad": "Solicitud", "dato": "Firma del revisor"}], out)
    c, out = corre(S / "indice.py", "cambios", p, "EV-02")
    ok("indice.py cambios: en texto, con el antes y después y la orden de capturas; una URG no lleva «sin decisión»",
       c == 0 and "antes  :" in out and "después:" in out and "--solo PAN-01,PAN-02" in out and "Reaplicar URG-01" in out
       and "sin decisión" not in out and "Colisión: URG-01" in out, out)
    c, out = corre(S / "indice.py", "colision", p, "URG-01")
    ok("indice.py colision: los objetos que corrige y los que los usan, frente a las unidades sin pasar a producción",
       c == 0 and "corrige: DEM_SolicitudForm · los usan: DEM Alta Solicitud" in out and "Colisión: sí" in out
       and "EV-02 (Aprobada) cambia DEM_SolicitudForm" in out
       and "EV-03 (Abierta) cambia DEM Alta Solicitud, que usa lo que se corrige" in out
       and "deriva --out" in out and "entorno de corrección" in out, out)
    (p / "as-is" / "datos" / "deriva.json").write_text(json.dumps({"cambiados": [{"nombre": "DEM Alta Solicitud"}]}),
                                                        encoding="utf-8")
    cambios_md(p, {k: v for k, v in FILAS_BASE.items() if k != "EV-03"} | {"EV-02": "En producción"})
    c, out = corre(S / "indice.py", "colision", p, "URG-01")
    ok("indice.py colision: lo modificado en desarrollo (as-is/datos/deriva.json) también choca",
       c == 0 and "Colisión: sí" in out and "deriva.json): DEM Alta Solicitud" in out and "EV-02" not in out, out)
    (p / "as-is" / "datos" / "deriva.json").write_text(json.dumps({"cambiados": [
        {"nombre": "DEM Alta Solicitud", "ahora": {"fecha": "2026-10-10T09:00:00Z"}}]}), encoding="utf-8")
    c, out = corre(S / "indice.py", "colision", p, "URG-01")
    ok("B6: lo modificado antes del último pase (EV-01, 2026-10-11) ya está en producción: no choca",
       c == 0 and "Colisión: no" in out, out)
    (p / "as-is" / "datos" / "deriva.json").write_text(json.dumps({"cambiados": None}), encoding="utf-8")
    c, out = corre(S / "indice.py", "colision", p, "URG-01")
    ok("indice.py colision: sin choques, se corrige en desarrollo; sin historial, lo dice",
       c == 0 and "Colisión: no" in out and "congelados" in out and "no da el historial" in out, out)
    c, out = corre(S / "indice.py", "colision", p, "EV-02")
    ok("indice.py colision de un EV es error", c == 1 and "no es una URG" in out, out)
    p = con_unidades(tmp / "unidades encargo")
    c, out = corre(S / "indice.py", "encargo", p, "EV-03")
    ok("indice.py encargo de una unidad sin aprobar es error (no se construye sin aprobar)",
       c == 1 and "aprobada" in out and not (p / "construccion").exists(), out)
    c, out = corre(S / "indice.py", "encargo", p, "EV-02")
    enc = (p / "construccion" / "EV-02.md").read_text(encoding="utf-8") if (p / "construccion" / "EV-02.md").exists() else ""
    esp = json.loads((p / "construccion" / "EV-02-esperado.json").read_text(encoding="utf-8")) \
        if (p / "construccion" / "EV-02-esperado.json").exists() else {}
    ok("indice.py encargo: construccion/EV-02.md con sus objetos, dónde están en el técnico, el cambio sobre lo construido, "
       "las pruebas, la URG que reaplicar y la orden de verificar",
       c == 0 and "| `DEM Solicitud` | Record type | Modifica | campos: firmaRevisor | §3.1 |" in enc
       and "| `DEM_ER_Firma` | Regla de expresión | Nuevo | DEM_ER_Firma · solicitud · Booleano · Si tiene firma (HU-04, FU-04)"
       in enc and "| `DEM_SolicitudForm` | Interfaz | Modifica | ver técnico §7 |" in enc
       and "**Datos existentes** (DEM Solicitud): `firmaRevisor`" in enc
       and "URG-01 sobre DEM_SolicitudForm: Guardar una solicitud con el importe vacío" in enc
       and "HU-01.1, HU-01.2, HU-02.1, HU-02.2, HU-04.1" in enc and "Reaplicar URG-01 en `DEM_SolicitudForm`" in enc
       and 'verificar --app "DEM Gestión de Solicitudes" --objetos "DEM Solicitud,DEM_ER_Firma,DEM_RevisionForm,'
           'DEM_SolicitudForm" --esperado "<p>/construccion/EV-02-esperado.json" --out "<p>/construccion/verificacion/EV-02.json"'
       in enc and "construida --reaplicada URG-01" in enc and "change-planning" in enc, out + enc)
    ok("indice.py encargo: --esperado con el tipo de cada objeto y, del record type que se modifica, solo sus campos nuevos",
       esp == {"DEM Solicitud": {"tipo": "recordType", "campos": [{"nombre": "firmaRevisor", "tipo": "Text"}]},
               "DEM_ER_Firma": {"tipo": "expressionRule"}, "DEM_RevisionForm": {"tipo": "interface"},
               "DEM_SolicitudForm": {"tipo": "interface"}}, json.dumps(esp, ensure_ascii=False))
    fechas = [(p / "construccion" / x).stat().st_mtime_ns for x in ("EV-02.md", "EV-02-esperado.json")]
    __import__("time").sleep(0.05)
    c, out = corre(S / "indice.py", "encargo", p, "EV-02")
    ok("indice.py encargo otra vez sin cambios: no reescribe nada (R2): la fecha de los ficheros no cambia",
       c == 0 and "Al día" in out and fechas == [(p / "construccion" / x).stat().st_mtime_ns
                                                for x in ("EV-02.md", "EV-02-esperado.json")], out)
    # B5: un cambio de una pantalla sin historias tocadas repite las pruebas y conserva las historias que la usan
    (p / "impacto" / "FU-12.md").write_text(
        "# Impacto de FU-12\nAnálisis base: versión 1.1 · Cambio: EV-03 · Estado: aplicado en 1.2\n\n## Puntos\n"
        "| # | Tipo | Qué se dice | Encaja en | Cambio propuesto | Revisar también | Requiere | Decisión |\n"
        "|---|---|---|---|---|---|---|---|\n| 1 | COMPLETA | Un filtro por estado [FU-12 00:01:00] | PAN-03 | PAN-03 con un "
        "filtro | — | — | ✔ |\n\n## Aplicado\nVersión 1.2: PAN-03\n", encoding="utf-8")
    c, out = corre(S / "indice.py", "cambios", p, "EV-03", "--json")
    r3 = json.loads(out) if c == 0 else {}
    ok("B5: un cambio de PAN-03 sin historias tocadas: HU-03 se conserva y sus criterios se repiten",
       r3.get("historias", {}).get("seConservan") == ["HU-03"]
       and r3.get("pruebas", {}).get("criterios") == ["HU-03.1", "HU-03.2"], out)
    if shutil.which("node"):
        r = subprocess.run(["node", str(S / "df_docx.js"), str(p), "--cambio", "EV-02"], capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        d = p / "entregables" / "DF-Devoluciones-de-solicitudes-EV-02-v1.1.docx"
        if r.returncode == 2 and "docx" in r.stderr:
            print("· DF del cambio: falta el paquete docx de Node; no se prueba")
        else:
            xml = zipfile.ZipFile(d).read("word/document.xml").decode("utf-8").replace(GUION, "-") if d.exists() else ""
            ok("df_docx.js --cambio: el DF del cambio con lo nuevo, lo que cambia y lo que se conserva y comparte pantalla "
               "o paso; sin lo demás",
               r.returncode == 0 and "Qué cambia" in xml and "HU-04 — Firmar la revisión" in xml
               and "HU-02 — Corregir y reenviar" in xml and "HU-01 — Devolver una solicitud" in xml
               and "HU-03" not in xml and "Se conserva" in xml and "Nueva" in xml and "cambio EV-02" in xml,
               r.stdout + r.stderr + xml[:500])
            ok("M5: el DF del cambio lleva los datos nuevos de §6 (no los que no cambian) y no la columna «Origen»",
               "Firma del revisor" in xml and "Comentario de devolución" not in xml and "Origen" not in xml,
               xml[:500])


def docx_de(proyecto, salida):
    """El Word del DF de un proyecto (df_docx.js -o salida), o None si no se genera."""
    r = subprocess.run(["node", str(S / "df_docx.js"), str(proyecto), "-o", str(salida)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode or not salida.exists():
        print(r.stdout + r.stderr)
        return None
    return salida


def crear_docx_con_comentario(ruta):
    """Un Word mínimo con un comentario sobre un criterio de HU-07, sin dependencias."""
    w = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
    doc = (f'<w:document {w}><w:body>'
           '<w:p><w:r><w:t>HU-07 — Adjuntar el informe del organismo</w:t></w:r></w:p>'
           '<w:p><w:commentRangeStart w:id="0"/><w:r><w:t>HU-07.1 Solo admite PDF de hasta 20 MB.</w:t></w:r>'
           '<w:commentRangeEnd w:id="0"/><w:r><w:commentReference w:id="0"/></w:r></w:p>'
           '</w:body></w:document>')
    com = (f'<w:comments {w}><w:comment w:id="0" w:author="Técnico" w:date="2026-10-01T10:00:00Z">'
           '<w:p><w:r><w:t>Mejor 30 MB, los planos pesan mucho.</w:t></w:r></w:p></w:comment></w:comments>')
    tipos = ('<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
             '<Default Extension="xml" ContentType="application/xml"/>'
             '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
             '</Types>')
    with zipfile.ZipFile(ruta, "w") as z:
        z.writestr("[Content_Types].xml", tipos)
        z.writestr("word/document.xml", doc)
        z.writestr("word/comments.xml", com)


if __name__ == "__main__":
    sys.exit(main())
