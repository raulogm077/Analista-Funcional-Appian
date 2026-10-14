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


def corre(*args, entrada=None, env=None, cwd=None):
    r = subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True, input=entrada, cwd=cwd,
                       env={**os.environ, **env} if env else None, encoding="utf-8", errors="replace")
    return r.returncode, r.stdout + r.stderr


def git(carpeta, *args):
    """Una orden de git en una carpeta de la prueba, con el entorno que pone main: sin la configuración del equipo."""
    r = subprocess.run(["git", *args], cwd=str(carpeta), capture_output=True, text=True, stdin=subprocess.DEVNULL,
                       encoding="utf-8", errors="replace")
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
    # git, igual en cualquier equipo y sin red: sin la configuración de quien lanza la prueba (firma de commits, rama
    # inicial, plantillas), con un autor fijo y sin subir más allá de la carpeta temporal ni de los datos de prueba, para
    # que proyecto.py no tome un proyecto de prueba por parte del repositorio del plugin ni pregunte a su remoto. Y con
    # core.autocrlf, como instala Git para Windows: sin el .gitattributes del proyecto, un clon cambiaría los finales
    # de línea
    (tmp / "gitconfig").write_text("[core]\n\tautocrlf = true\n", encoding="utf-8")
    os.environ.update(GIT_CONFIG_GLOBAL=str(tmp / "gitconfig"), GIT_CONFIG_NOSYSTEM="1", GIT_TERMINAL_PROMPT="0",
                      GIT_CEILING_DIRECTORIES=os.pathsep.join(map(str, (tmp.resolve(), tmp, DATOS))),
                      GIT_AUTHOR_NAME="Prueba", GIT_AUTHOR_EMAIL="prueba@example.com",
                      GIT_COMMITTER_NAME="Prueba", GIT_COMMITTER_EMAIL="prueba@example.com")
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
        c, out = corre(S / "proyecto.py", "--help", env={"PYTHONIOENCODING": "cp1252"})
        ok("proyecto.py --help con la consola en cp1252 conserva las tildes",
           c == 0 and "versión, cliente y marca" in out and "«DF entregado»" in out, out)

        # 3a. El método: los flujos del plugin y el repositorio git de cada proyecto, con AGENTS.md y su copia de los flujos
        pruebas_flujos()
        pruebas_repositorio(tmp)

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
        pruebas_issues(tmp)

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

        # 5c. Criterios con dado, cuando y entonces (método L.U.C.I.A., fase 4): el .feature sale sin IA
        gherkin = pruebas_gherkin(tmp)

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
        con_cr = [f.name for f in sorted((tmp / "fuentes").glob("*")) if f.is_file() and b"\r" in f.read_bytes()]
        ok("leer_fuentes.py escribe con \\n en cualquier sistema, también en Windows: cada fuente y los índices",
           c == 0 and not con_cr, str(con_cr))
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
                d = docx_de(gherkin, tmp / "gherkin.docx") if gherkin else None
                xml = zipfile.ZipFile(d).read("word/document.xml").decode("utf-8").replace(GUION, "-") if d else ""
                vinetas = [re.sub(r"<[^>]+>", "", x) for x in re.findall(r"<w:p>.*?</w:p>", xml, re.S) if "<w:numPr>" in x]
                ok("un criterio con dado, cuando y entonces sale en el Word entero, en su viñeta y con su ID",
                   f"HU-03.2 {DEVUELTA}" in vinetas, xml[:300])
                ok("un criterio en dos líneas es en el Word la misma frase que en su .feature",
                   f"HU-06.3 {' '.join(DOS_LINEAS)}" in vinetas, str([v for v in vinetas if v.startswith("HU-06.")]))
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
        for carpeta, _, ficheros in os.walk(tmp):   # en Windows los objetos de git son de solo lectura y no se borran
            for f in ficheros:
                try:
                    os.chmod(os.path.join(carpeta, f), 0o600)
                except OSError:
                    pass
        shutil.rmtree(tmp, ignore_errors=True)
    print("\nTodo correcto." if not fallos else f"\n{len(fallos)} pruebas fallan: {', '.join(fallos)}")
    return 1 if fallos else 0


def pruebas_flujos():
    """El catálogo de flujos del plugin (assets/flujos/): los nueve, cada uno con cuándo se usa, quién empieza, dónde
    termina y sus pasos numerados con quién hace cada uno y con qué; y lo que citan existe: las skills, sus scripts y el
    fichero y el apartado de cada «Detalle»."""
    flujos = sorted((SKILL / "assets" / "flujos").glob("F*.md"))
    ok("hay nueve flujos, de F1 a F9", [f.name.split("-")[0] for f in flujos] == [f"F{n}" for n in range(1, 10)],
       str([f.name for f in flujos]))
    mal = []
    for f in flujos:
        t = f.read_text(encoding="utf-8")
        filas = [[c.strip() for c in l.strip().strip("|").split("|")] for l in t.splitlines() if re.match(r"\| \d+ \|", l)]
        if not re.match(rf"# {f.name.split('-')[0]} · \S", t):
            mal.append(f"{f.name}: el título no es «# {f.name.split('-')[0]} · …»")
        if not all(re.search(rf"^\*\*{x}\.\*\* \S", t, re.M) for x in ("Cuándo", "Empieza")) or "**Termina en.** " not in t:
            mal.append(f"{f.name}: falta «Cuándo», «Empieza» o «Termina en»")
        if ("| # | Paso | Quién | Con qué | Detalle |" not in t or len(filas) < 3 or any(len(r) != 5 or not all(r) for r in filas)
                or [r[0] for r in filas] != [str(n) for n in range(1, len(filas) + 1)]):
            mal.append(f"{f.name}: los pasos no son una tabla «# · Paso · Quién · Con qué · Detalle» numerada desde 1")
        for skill in set(re.findall(r"`(appian(?:-[a-z]+)*)`", t)) - {"appian"}:   # `appian` es la oficial de Appian
            if not (PLUGIN / "skills" / skill / "SKILL.md").is_file():
                mal.append(f"{f.name}: nombra la skill {skill}, que no está en el plugin")
        for r in filas:   # «`skill` · `script.py orden`; `otra skill` · `otro.py`»: cada script, en su skill
            for trozo in r[3].split(";") if len(r) == 5 else []:
                skill = re.search(r"`(appian-[a-z-]+)`", trozo)
                for script in re.findall(r"`([\w-]+\.(?:py|js))\b", trozo):
                    if not (skill and (PLUGIN / "skills" / skill.group(1) / "scripts" / script).is_file()):
                        mal.append(f"{f.name}, paso {r[0]}: {script} no está en scripts/ de la skill que se nombra")
        for ruta, apartados in re.findall(r"`(appian-[a-z-]+/[^`\s]+)`((?:[ ,y]*(?:§\d+|«[^»]+»))*)", t):
            destino = PLUGIN / "skills" / ruta
            if not destino.is_file():
                mal.append(f"{f.name}: cita {ruta}, que no existe")
                continue
            texto = destino.read_text(encoding="utf-8")
            for ap in re.findall(r"§\d+|«[^»]+»", apartados):
                titulo = rf"{ap[1:]}\. " if ap.startswith("§") else re.escape(ap[1:-1])
                if not re.search(rf"^#+ {titulo}", texto, re.M):
                    mal.append(f"{f.name}: cita {ruta} {ap}, y ese fichero no tiene ese apartado")
    ok("cada flujo dice cuándo se usa, quién hace cada paso, con qué y dónde termina, y lo que cita existe", not mal,
       "\n".join(mal))


def arbol(p):
    """Los ficheros y las carpetas de un proyecto, sin lo de dentro de .git."""
    return sorted(x.relative_to(p).as_posix() + ("/" if x.is_dir() else "") for x in p.rglob("*")
                  if ".git" not in x.relative_to(p).parts)


def pruebas_repositorio(tmp):
    """Fase 3 del método: dos proyectos nuevos tienen la misma estructura y son repositorios git; tras cambiar de versión
    del plugin, AGENTS.md y los flujos se ponen al día sin tocar proyecto.md; y estado avisa de lo que no está subido.
    Sin red: el remoto es otra carpeta."""
    iniciar = lambda p, *args, **k: corre(S / "proyecto.py", "iniciar", p, *args, **k)
    estado = lambda p, **k: corre(S / "proyecto.py", "estado", p, **k)
    version = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"]
    base = tmp / "Repositorios con espacios"
    (base / "sin programas").mkdir(parents=True)

    # Sin git en el equipo (un PATH sin nada) nada falla: iniciar crea lo demás y lo dice
    sin_git = {"PATH": str(base / "sin programas")}
    c, out = iniciar(base / "sin git", "--nombre", "Sin git", env=sin_git)
    c2, out2 = estado(base / "sin git", env=sin_git)
    ok("sin git en el equipo, iniciar crea el proyecto sin repositorio y lo dice, y estado no falla",
       c == 0 and "Sin git en este equipo" in out and (base / "sin git" / "AGENTS.md").is_file()
       and not (base / "sin git" / ".git").exists() and c2 == 0 and "sin git en este equipo" in out2, out + out2)
    c, out = iniciar(base / "sin nombre")
    ok("iniciar sin --nombre en una carpeta que no es un proyecto: lo pide y no crea nada",
       c != 0 and "--nombre" in out and not (base / "sin nombre").exists(), out)
    if not shutil.which("git"):
        print("· Repositorio del proyecto: no hay git en este equipo; no se prueba")
        return

    # Dos proyectos nuevos: la misma estructura, repositorios git en main y lo generado, igual en los dos
    a, b = base / "uno", base / "dos"
    ca, outa = iniciar(a, "--nombre", "Permisos de obra", "--cliente", "Organización de ejemplo")
    cb, outb = iniciar(b, "--nombre", "Reserva de salas")
    flujos = [f".agents/workflows/{f.name}" for f in sorted((SKILL / "assets" / "flujos").glob("F*.md"))]
    generados = ["AGENTS.md", *flujos]
    propios_de_git = [".gitignore", ".gitattributes"]
    completos = all((p / x).is_file() for p in (a, b) for x in [*generados, "CLAUDE.md", *propios_de_git, "proyecto.md"])
    ok("dos proyectos nuevos tienen la misma estructura: AGENTS.md, CLAUDE.md, lo de git, los flujos y nada de más",
       ca == 0 and cb == 0 and completos and arbol(a) == arbol(b) and len(flujos) == 9
       and not any((a / x).exists() for x in (".agents/skills", "product_vision.md", "qa", "construccion")),
       outa + outb + str(arbol(a)) + str(arbol(b)))
    if not completos:   # sin lo que genera iniciar no hay nada más que probar
        return
    ramas = [git(p, "symbolic-ref", "--short", "HEAD") for p in (a, b)]
    ok("los dos son repositorios git, en la rama main",
       all((p / ".git").is_dir() for p in (a, b)) and all(c == 0 and o.strip() == "main" for c, o in ramas), str(ramas))
    guia = (a / "AGENTS.md").read_text(encoding="utf-8")
    textos = {x: (a / x).read_bytes() for x in [*generados, "CLAUDE.md", *propios_de_git]}
    ok("lo generado es igual en los dos proyectos y en cualquier sistema, con la versión del plugin y sin notas del plan",
       all(v == (b / x).read_bytes() and b"\r" not in v and b"<!-- (T" not in v for x, v in textos.items())
       and all(textos[x].decode("utf-8").startswith(f"<!-- appian-analisis-funcional {version} · ") for x in generados)
       and textos["CLAUDE.md"] == b"@AGENTS.md\n" and textos[".gitattributes"].endswith(b"\n* -text\n")
       and all(f"]({x})" in guia for x in flujos), guia[:600])
    con_cr = [x for x in arbol(a) if (a / x).is_file() and b"\r" in (a / x).read_bytes()]
    ok("nada de lo que escribe iniciar lleva \\r, tampoco en Windows: proyecto.md y las plantillas del análisis",
       not con_cr and b"\n" in (a / "analisis" / "funcional.md").read_bytes(), str(con_cr))
    ok("AGENTS.md no nombra lo que todavía no escribe nadie (qa/) ni pide un git pull antes de mirar el estado",
       "qa/" not in guia and "git pull" in guia and guia.index("proyecto.py estado") < guia.index("git pull"), guia)
    # dos fuentes, una con cada final de línea: tienen que llegar igual, byte a byte, a quien clone el proyecto
    fuentes = {"fuentes/FU-01-acta.md": "# FU-01\nActa de la reunión\n".encode("utf-8"),
               "fuentes/correo.eml": b"Subject: Plazos\r\n\r\nSe mantienen.\r\n"}
    for x, dato in {**fuentes, "fuentes/reunion.mp4": b"video", ".env": b"CLAVE=x\n"}.items():
        (a / x).write_bytes(dato)
    fuera = {x: git(a, "check-ignore", "-q", x)[0] == 0 for x in ("fuentes/reunion.mp4", ".env", "fuentes/FU-01-acta.md")}
    ok(".gitignore deja fuera las grabaciones y los secretos, y no las fuentes",
       fuera == {"fuentes/reunion.mp4": True, ".env": True, "fuentes/FU-01-acta.md": False}, str(fuera))

    # estado avisa de lo que no está confirmado ni subido, sin fallar; con todo subido, calla
    c, out = estado(a)
    ok("estado de un proyecto recién creado: nada confirmado y sin remoto, y no le falta nada de iniciar",
       c == 0 and "cambios sin confirmar" in out and "sin remoto, nada está subido" in out and "le falta" not in out
       and "otra versión" not in out, out)
    remoto = base / "remoto.git"
    git(base, "init", "--quiet", "--bare", str(remoto))
    git(a, "remote", "add", "origin", str(remoto))
    git(a, "add", "-A")
    c0, o0 = git(a, "commit", "--quiet", "-m", "Inicio del proyecto")
    c, out = estado(a)
    ok("estado con todo confirmado y nada subido: la rama no está en el remoto",
       c0 == 0 and c == 0 and "sin confirmar" not in out and "la rama main no está en el remoto" in out, o0 + out)
    c0, o0 = git(a, "push", "--quiet", "origin", "main")   # sin -u: está subida, aunque la rama no «siga» a la del remoto
    c, out = estado(a)
    ok("estado con la rama subida sin -u no dice que no está en el remoto", c0 == 0 and c == 0
       and not re.search(r"^· ", out, re.M), o0 + out)
    (a / "notas" / "aviso.md").write_bytes(b"# Aviso\n")
    git(a, "add", "-A")
    git(a, "commit", "--quiet", "-m", "Aviso")
    c, out = estado(a)
    ok("y de un commit posterior dice que está sin subir, con la orden que dice a dónde",
       c == 0 and "Repositorio: 1 commit sin subir a origin/main (git push -u origin main)" in out, out)
    c0, o0 = git(a, "push", "--quiet", "-u", "origin", "main")
    c, out = estado(a)
    ok("estado con todo subido no avisa de nada", c0 == 0 and c == 0 and not re.search(r"^· ", out, re.M), o0 + out)
    editar(a / "proyecto.md", "Catalogar las fuentes.", "Preparar la reunión del jueves.")
    c, out = estado(a)
    ok("estado avisa de un cambio sin confirmar", c == 0 and "Repositorio: 1 cambio sin confirmar" in out, out)
    git(a, "commit", "--quiet", "-am", "Siguiente paso")
    c, out = estado(a)
    ok("estado avisa de un commit sin subir",
       c == 0 and "Repositorio: 1 commit sin subir a origin/main" in out and "sin confirmar" not in out, out)
    otra = base / "otra persona"   # otra persona sube un cambio: estado lo ve sin que nadie lo traiga antes
    git(base, "clone", "--quiet", "-b", "main", str(remoto), str(otra))
    ok("un clon tiene las fuentes byte a byte, también con core.autocrlf: su huella es la misma en cualquier equipo",
       all((otra / x).is_file() and (otra / x).read_bytes() == dato for x, dato in fuentes.items()),
       str({x: (otra / x).read_bytes() if (otra / x).is_file() else None for x in fuentes}))
    (otra / "notas").mkdir(exist_ok=True)
    (otra / "notas" / "FU-01.md").write_text("# Nota de FU-01\n", encoding="utf-8")
    git(otra, "add", "-A")
    git(otra, "commit", "--quiet", "-m", "Nota de FU-01")
    c0, o0 = git(otra, "push", "--quiet")
    c, out = estado(a)
    ok("estado avisa de que el proyecto va por detrás del remoto",
       c0 == 0 and c == 0 and "Repositorio: va 1 commit por detrás de origin/main" in out and "1 commit sin subir" in out,
       o0 + out)
    git(a, "remote", "set-url", "origin", str(base / "no existe.git"))
    c, out = estado(a)
    ok("sin poder consultar el remoto, estado no falla: lo dice y compara con lo último que se trajo",
       c == 0 and "no se pudo consultar el remoto" in out and "va 1 commit por detrás" in out
       and "1 commit sin subir" in out, out)
    git(a, "remote", "set-url", "origin", str(remoto))

    # Otra versión del plugin (una copia de la skill con otro plugin.json y un flujo cambiado): su estado lo avisa y su
    # iniciar pone al día AGENTS.md y los flujos, sin tocar proyecto.md, el CLAUDE.md del equipo ni nada más
    otro = base / "plugin 9.9.9"
    shutil.copytree(SKILL, otro / "skills" / SKILL.name, ignore=shutil.ignore_patterns("__pycache__"))
    (otro / ".claude-plugin").mkdir()
    (otro / ".claude-plugin" / "plugin.json").write_text('{"name": "appian-analisis-funcional", "version": "9.9.9"}',
                                                         encoding="utf-8")
    s9 = otro / "skills" / SKILL.name / "scripts"
    f2 = otro / "skills" / SKILL.name / "assets" / "flujos" / "F2-incorporar-una-fuente.md"
    f2.write_text(f2.read_text(encoding="utf-8") + "\nUn paso que llega con la versión nueva.\n", encoding="utf-8")
    (a / "CLAUDE.md").write_text("@AGENTS.md\n\nNotas del equipo.\n", encoding="utf-8")
    retirado = a / ".agents" / "workflows" / "F0-retirado.md"   # un flujo de antes, que este plugin ya no trae
    retirado.write_bytes((a / flujos[0]).read_bytes())
    (a / ".agents" / "workflows" / "notas.md").write_text("# Notas del equipo\n", encoding="utf-8")
    propios = ["proyecto.md", "CLAUDE.md", *propios_de_git, "analisis/funcional.md", "analisis/tecnico.md",
               "analisis/decisiones.md", ".agents/workflows/notas.md"]
    antes = {x: (a / x).read_bytes() for x in propios}
    de_la = lambda v, rutas=generados: all(
        (a / x).read_text(encoding="utf-8").startswith(f"<!-- appian-analisis-funcional {v} · ") for x in rutas)
    c, out = corre(s9 / "proyecto.py", "estado", a)
    ok("estado, con otra versión del plugin, avisa de que AGENTS.md y los flujos son de otra y dice cómo ponerlos al día",
       c == 0 and f"otra versión del plugin ({version}; la de este equipo, 9.9.9)" in out
       and "«proyecto.py iniciar <p>» los pone al día" in out, out)
    c, out = corre(s9 / "proyecto.py", "iniciar", a)
    ok("tras cambiar de versión, iniciar pone al día AGENTS.md y los flujos sin tocar proyecto.md ni nada más",
       c == 0 and de_la("9.9.9") and "Preparar la reunión del jueves." in antes["proyecto.md"].decode("utf-8")
       and "Un paso que llega con la versión nueva." in (a / flujos[1]).read_text(encoding="utf-8")
       and not retirado.exists() and all((a / x).read_bytes() == v for x, v in antes.items()), out)
    c, out = corre(s9 / "proyecto.py", "estado", a)
    ok("y estado deja de avisar de la versión", c == 0 and "otra versión" not in out, out)
    (a / flujos[-1]).unlink()   # la versión posterior retiró un flujo que este plugin, anterior, todavía trae
    c, out = estado(a)
    c2, out2 = iniciar(a)
    ok("con un plugin anterior al que generó AGENTS.md y los flujos, estado solo pide actualizar el plugin (no dice que "
       "falte un flujo) e iniciar no los toca",
       c == 0 and "actualiza el plugin" in out and "le falta" not in out and c2 == 0 and "no se tocan" in out2
       and not (a / flujos[-1]).exists() and de_la("9.9.9", generados[:-1]), out + out2)

    # Lo que no generó el plugin no se pisa: un CLAUDE.md y un AGENTS.md propios
    (b / "CLAUDE.md").write_text("# Notas del equipo\n", encoding="utf-8")
    (b / "AGENTS.md").write_text("# Nuestras reglas\n", encoding="utf-8")
    c, out = iniciar(b)
    c2, out2 = estado(b)
    ok("un CLAUDE.md y un AGENTS.md que no generó el plugin no se pisan, y estado avisa de los dos",
       c == 0 and (b / "CLAUDE.md").read_text(encoding="utf-8") == "# Notas del equipo\n"
       and (b / "AGENTS.md").read_text(encoding="utf-8") == "# Nuestras reglas\n" and "no lo generó el plugin" in out
       and c2 == 0 and "CLAUDE.md no importa AGENTS.md" in out2 and "AGENTS.md no lo generó el plugin" in out2,
       out + out2)

    # Dentro de otro repositorio no se crea uno anidado; y un proyecto de los datos de prueba no es del repositorio del
    # plugin (GIT_CEILING_DIRECTORIES, en main): estado no pregunta a su remoto
    varios = base / "varios proyectos"
    varios.mkdir()
    git(varios, "init", "--quiet")
    c, out = iniciar(varios / "dentro", "--nombre", "Dentro de otro")
    ok("dentro de otro repositorio, iniciar no crea uno anidado y lo dice",
       c == 0 and "ya está dentro de uno" in out and not (varios / "dentro" / ".git").exists()
       and (varios / "dentro" / "AGENTS.md").is_file(), out)
    c, out = estado(EVOLUTIVO)
    ok("estado de un proyecto sin repositorio dice lo que le falta y cómo añadirlo, en una línea",
       c == 0 and len(re.findall(r"^· Al proyecto le falta ser un repositorio git, AGENTS\.md, CLAUDE\.md, algún flujo",
                                 out, re.M)) == 1 and "Repositorio:" not in out, out)


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


def de_issue(p, uid, iid):
    """De qué issue y de qué versión es lo esperado de una issue: lo que «verificar» copia a su resultado."""
    return json.loads((p / "construccion" / uid / f"{iid}-esperado.json").read_text(encoding="utf-8"))["_issue"]


def verifica(p, uid, iid, objetos=None, **diferencias):
    """Deja la verificación de una issue como la dejaría «verificar --esperado» con todo construido (o con las
    diferencias que se digan por objeto): construccion/<U>/verificacion/ISS-nn.json."""
    esperado = json.loads((p / "construccion" / uid / f"{iid}-esperado.json").read_text(encoding="utf-8"))
    f = p / "construccion" / uid / "verificacion" / f"{iid}.json"
    f.parent.mkdir(parents=True, exist_ok=True)
    with open(f, "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"generadoEn": "2026-10-14T10:00:00Z", "issue": esperado["_issue"], "objetos": [
            {"pedido": o, "existe": True, "diferencias": diferencias.get(o, {})}
            for o in objetos or [k for k in esperado if k != "_issue"]]}, fh, ensure_ascii=False, indent=1)
    return f


PLAN_13 = """## 13. Plan de construcción

| Paso | Objeto | Tipo | Situación | Sustituye a | Cambio | Para |
|---|---|---|---|---|---|---|
| 1 | `AUT Técnicos`, `AUT Responsables`, `AUT Consulta` | Grupo | Nuevo | — | | Base |
| 2 | `AUT Estado` | Record type | Nuevo | — | | Base |
| 2 | `AUT Tipo Autorizacion` | Record type | Nuevo | — | | Base |
| 2 | `AUT Solicitud` | Record type | Nuevo | — | | Base |
| 2 | `AUT Documento` | Record type | Nuevo | — | | Base |
| 4 | `AUT_GenerarNumero` | Regla de expresión | Nuevo | — | | HU-01 |
| 4 | `AUT_CalcularFechaLimite` | Regla de expresión | Nuevo | — | | HU-01 |
| 5 | `AUT_SolicitudForm` | Interfaz | Nuevo | — | | PAN-03 |
| 5 | `AUT_RevisarForm` | Interfaz | Nuevo | — | | PAN-04 |
| 5 | `AUT_ResolverForm` | Interfaz | Nuevo | — | | PAN-05 |
| 5 | `AUT_FichaSolicitud` | Interfaz | Nuevo | — | | PAN-02 |
| 5 | `AUT Solicitud — acción «Adjuntar informe del organismo»` | Acción de registro | Nuevo | — | | HU-07 |
| 6 | `AUT Tramitar Solicitud` | Process model | Nuevo | — | | ACT-01, ACT-02, ACT-05, ACT-06 |
| 6 | `AUT_PlantillaAutorizacion` | Documento | Nuevo | — | | ACT-07 |
| 7 | `AUT Autorizaciones` | Site | Nuevo | — | | PAN-01 |

Manual: calendario de procesos y buzón del organismo en cada entorno.

"""


def nueva_con_issues(destino):
    """Una aplicación nueva (autorizaciones/, versión 1.1) lista para construir por issues: técnico §13 como tabla con
    «Para», los objetos de cada pantalla nombrados en §7, cómo se comprueba cada criterio en §14 (caso de prueba o SAIL
    CLI), la aplicación y la URL de desarrollo en §0, dos criterios de HU-03 con dado, cuando y entonces y la captura de
    PAN-03. Con EV-01, la construcción inicial, abierta: las filas de §13 sin unidad son suyas."""
    shutil.copytree(EJEMPLO, destino)
    f, t = destino / "analisis" / "funcional.md", destino / "analisis" / "tecnico.md"
    editar(f, "- `HU-03.1` El comentario del técnico aparece encima del formulario mientras se subsana.\n"
           "- `HU-03.2` Al reenviarla vuelve a «En revisión» con el mismo número.",
           f"- `HU-03.1` {DEVUELTA}\n- `HU-03.2` {EN_REVISION}")
    editar(f, "Formulario de la solicitud. Se abre con «Nueva solicitud» o desde la tarea de subsanar.",
           "![PAN-03 Registrar o subsanar solicitud](../prototipo/capturas/03-alta.png)\n\n"
           "Formulario de la solicitud. Se abre con «Nueva solicitud» o desde la tarea de subsanar.")
    editar(t, "| Versión de Appian |", "| Aplicación | `AUT Autorizaciones`, prefijo `AUT` | Equipo |\n"
           "| URL de desarrollo | https://aut-desarrollo.example.com | Equipo |\n"
           "| URL de producción | https://aut.example.com | Equipo |\n| Versión de Appian |")
    editar(t, "| PAN-02 | Vista de registro «Resumen» + vistas «Documentos» e «Historial» |",
           "| PAN-02 | `AUT_FichaSolicitud`, vista de registro «Resumen» de `AUT Solicitud`, + vistas «Documentos» e «Historial» |")
    editar(t, "| PAN-03 | Acción de registro «Nueva solicitud» y formulario de la tarea de subsanar |",
           "| PAN-03 | `AUT_SolicitudForm`: acción de lista de registros «Nueva solicitud» de `AUT Solicitud` y formulario "
           "de la tarea de subsanar |")
    editar(t, "| PAN-04 | Formulario de tarea |", "| PAN-04 | `AUT_RevisarForm`, formulario de tarea |")
    editar(t, "| PAN-05 | Formulario de tarea |", "| PAN-05 | `AUT_ResolverForm`, formulario de tarea |")
    texto = t.read_text(encoding="utf-8")
    texto = texto[:texto.index("## 13. Plan de construcción")] + PLAN_13 + texto[texto.index("## 14. "):]
    texto = texto.replace("| Criterio | Cómo se prueba |\n|---|---|", "| Criterio | Cómo se prueba | Con qué |\n|---|---|---|")
    texto = texto.replace("| HU-01.1, HU-01.2, HU-01.3 | Alta con y sin documentos; dos envíos a la vez; otro usuario de otra unidad |",
                          "| HU-01.1, HU-01.3 | Alta con y sin documentos; otro usuario de otra unidad | SAIL CLI |\n"
                          "| HU-01.2 | Dos envíos a la vez no repiten número | Caso de prueba de `AUT_GenerarNumero` |")
    texto = texto.replace("| HU-03.1, HU-03.2 | Subsanar una devuelta |", "| HU-03.1, HU-03.2 | Subsanar una devuelta | SAIL CLI |")
    t.write_text(texto, encoding="utf-8")
    corre(S / "proyecto.py", "cambio", destino, "EV-01", "abrir", "--titulo", "Construcción inicial")
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
    c, out = corre(S / "proyecto.py", "cambio", p, "EV-02", "aprobada", "--fuente", "FU-05")
    issue = p / "construccion" / "EV-02" / "ISS-01.md"
    ok("A1: al aprobar la unidad quedan escritas sus issues, sin otro paso",
       c == 0 and "Issues de construcción: construccion/EV-02/, 1 issue" in out and issue.is_file()
       and (p / "construccion" / "EV-02" / "indice.md").is_file(), out)
    (p / "impacto" / "FU-11.md").write_text(
        "# Impacto de FU-11\nAnálisis base: versión 1.1 · Cambio: EV-02 · Estado: aplicado en 1.2; pendientes de "
        "aprobación: punto 1\n\n## Puntos\n| # | Tipo | Qué se dice | Encaja en | Cambio propuesto | Revisar también | "
        "Requiere | Decisión |\n|---|---|---|---|---|---|---|---|\n"
        "| 1 | ALCANCE+ | Firmar también en el panel [FU-08 00:01:00] | PAN-03 | PAN-03 con la firma | — | Sí (alcance) "
        "| Pendiente |\n| 2 | CAMBIA | La firma lleva fecha [FU-08 00:02:00] | HU-04 | HU-04.1 con la fecha | — | — | ✔ |\n",
        encoding="utf-8")
    editar(p / "analisis" / "tecnico.md", "| 8 | `DEM Alta Solicitud` | Process model | Modifica | — | EV-03 |",
           "| 8 | `DEM Alta Solicitud` | Process model | Modifica | — | EV-03 |\n| 9 | `DEM_Dashboard` | Interfaz | Modifica | — | EV-02 |")
    c, out = corre(S / "indice.py", "issues", p, "EV-02")
    ok("A1: con un informe nuevo de la unidad después de aprobarla, sus issues no se regeneran: es error y dice cómo "
       "volver a aprobarla",
       c == 1 and "EV-02 ha crecido desde que se aprobó" in out and "FU-11" in out and "aprobada --fuente" in out
       and "DEM_Dashboard" not in issue.read_text(encoding="utf-8"), out)
    verifica(p, "EV-02", "ISS-01", ("DEM Solicitud", "DEM_ER_Firma", "DEM_RevisionForm", "DEM_SolicitudForm",
                                    "DEM_Dashboard"))
    c, out = corre(S / "proyecto.py", "cambio", p, "EV-02", "construida", "--reaplicada", "URG-01")
    ok("A1: construida también es error («ha crecido») y no cambia el estado",
       c == 1 and "EV-02 ha crecido desde que se aprobó" in out and "| Aprobada |" in fila_de(p, "EV-02"), out)
    c, out = corre(S / "proyecto.py", "cambio", p, "EV-02", "aprobada", "--fuente", "FU-08")
    ok("A1: volver a aprobarla con un punto pendiente es error", c == 1 and "FU-11 punto 1" in out, out)
    editar(p / "impacto" / "FU-11.md", "| Sí (alcance) | Pendiente |", "| Sí (alcance) | ✔ FU-08 |")
    c, out = corre(S / "proyecto.py", "cambio", p, "EV-02", "aprobada", "--fuente", "FU-08")
    c2, out2 = corre(S / "proyecto.py", "cambio", p, "EV-02", "construida", "--reaplicada", "URG-01")
    ok("A1: aprobada otra vez desde Aprobada, sus issues crecen con lo nuevo, y la que estaba verificada vuelve a estar "
       "pendiente: ha cambiado",
       c == 0 and "aprobada 1.1: FU-04, FU-11" in fila_de(p, "EV-02") and "· FU-08 |" in fila_de(p, "EV-02")
       and "`DEM_Dashboard`" in issue.read_text(encoding="utf-8")
       and c2 == 1 and "ISS-01 (ha cambiado desde su última verificación)" in out2, out + out2)

    # Construida: verificación sin diferencias (o --manual) y cada «reaplicar URG-nn» confirmado
    p = con_unidades(tmp / "unidades construir")
    corre(S / "indice.py", "issues", p, "EV-02")     # un técnico sin «Para»: una sola issue, con toda la unidad
    ver = p / "construccion" / "EV-02" / "verificacion" / "ISS-01.json"
    de = de_issue(p, "EV-02", "ISS-01")
    bien = {"issue": de,
            "objetos": [{"pedido": "DEM Solicitud", "existe": True, "diferencias": {"sobranCampos": ["titulo"]}},
                        {"pedido": "DEM_ER_Firma", "existe": True, "diferencias": {}},
                        {"pedido": "DEM_RevisionForm", "existe": True, "diferencias": {}},
                        {"pedido": "DEM_SolicitudForm", "existe": True, "diferencias": {}}],
            "faltan": [], "conDiferencias": ["DEM Solicitud"]}
    c, out = corre(S / "proyecto.py", "cambio", p, "EV-02", "construida", "--reaplicada", "URG-01")
    ok("cambio construida: con una issue sin verificar es error y dice cómo se pide con su orden de terminar",
       c == 1 and "issues sin hacer: ISS-01 (sin verificar)" in out
       and "indice.py issues <p> EV-02 --siguiente" in out and "--manual" in out, out)
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
                                                + bien["objetos"][1:]}, "no se pudo leer DEM Solicitud"),
            ("lo esperado de otra versión de la issue", {**bien, "issue": {**de, "version": "0" * 12}},
             "ha cambiado desde su última verificación"),
            ("lo esperado de otra issue", {**bien, "issue": {**de, "id": "ISS-07"}}, "no es de esta issue"),
            ("un fichero que no dice de qué issue es", {k: v for k, v in bien.items() if k != "issue"},
             "no es de esta issue")]:
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

    # 5.4 Derivados: indice.py cambios, colision e issues; df_docx.js --cambio
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
    p = con_unidades(tmp / "unidades issues")
    c, out = corre(S / "indice.py", "issues", p, "EV-03")
    ok("indice.py issues de una unidad sin aprobar es error (no se construye sin aprobar)",
       c == 1 and "aprobada" in out and not (p / "construccion").exists(), out)
    c, out = corre(S / "indice.py", "issues", p, "URG-01")
    ok("indice.py issues de una URG es error: se corrige con su ficha", c == 1 and "impacto/URG-01.md" in out, out)
    c, out = corre(S / "indice.py", "issues", p, "EV-02")
    d = p / "construccion" / "EV-02"
    enc = (d / "ISS-01.md").read_text(encoding="utf-8") if (d / "ISS-01.md").exists() else ""
    esp = json.loads((d / "ISS-01-esperado.json").read_text(encoding="utf-8")) if (d / "ISS-01-esperado.json").exists() else {}
    ok("indice.py issues, con un técnico que aún no dice «Para»: una sola issue con toda la unidad, y lo avisa",
       c == 0 and sorted(x.name for x in d.iterdir()) == ["ISS-01-esperado.json", "ISS-01.feature", "ISS-01.md", "indice.md"]
       and "técnico §13 no tiene la columna «Para»" in out and "ISS-01 · HU-02, HU-04, PAN-01 · Firma de la revisión · "
       "pendiente: sin verificar" in out, out + str(sorted(x.name for x in d.iterdir()) if d.is_dir() else ""))
    ok("la issue lleva lo que cambia, sin mandar a leer el técnico: sus objetos, lo que el técnico dice de nuevo (lo que "
       "no cambia ya está construido), el cambio sobre lo construido, sus escenarios con cómo se comprueba cada uno y la "
       "URG que hay que reaplicar",
       "| `DEM Solicitud` | Record type | Modifica | §3.1 |" in enc and "| `DEM_SolicitudForm` | Interfaz | Modifica | §7, DT-01 |" in enc
       and "- §3.1 (nuevo) · Campo: firmaRevisor · Tipo: Texto · Long.: 255" in enc
       and "- §6 (nuevo) · Regla: `DEM_ER_Firma` · Entradas: solicitud · Devuelve: Booleano · Lógica: Si tiene firma (HU-04, FU-04)"
       in enc and "más del técnico que no cambian con EV-02" in enc and "Añade «Devolver»" not in enc
       and "- **Datos existentes** (`DEM Solicitud`): `firmaRevisor`" in enc
       and "- **HU-04 Firmar la revisión** (nueva)\n  Como revisor, quiero firmar la revisión" in enc
       and "- `HU-04.1` Sin firma no se puede aprobar ni rechazar. → Aprobar sin firma" in enc
       and "- `HU-02.2` Al reenviarla vuelve a «Enviada» con el mismo número y sin la firma anterior. → " in enc
       and "HU-02.1" not in enc and "HU-01.1" not in enc      # los criterios que la unidad no toca no son suyos
       and "Reaplicar URG-01 en `DEM_SolicitudForm`" in enc and "(Guardar una solicitud con el importe vacío)" in enc
       and "`--reaplicada URG-01`" in enc and "change-planning" in enc and "ver técnico" not in enc
       and "indice.py issues <p> EV-02 ISS-01" in enc, enc)
    ok("lo esperado dice de qué issue y de qué versión es, el tipo de cada objeto y, del record type que se modifica, "
       "solo sus campos nuevos",
       re.fullmatch(r"[0-9a-f]{12}", esp.get("_issue", {}).get("version", "")) is not None
       and esp == {"_issue": {"id": "ISS-01", "unidad": "EV-02", "version": esp["_issue"]["version"]},
                   "DEM Solicitud": {"tipo": "recordType", "campos": [{"nombre": "firmaRevisor", "tipo": "Text"}]},
                   "DEM_ER_Firma": {"tipo": "expressionRule"}, "DEM_RevisionForm": {"tipo": "interface"},
                   "DEM_SolicitudForm": {"tipo": "interface"}}, json.dumps(esp, ensure_ascii=False))
    fechas = [x.stat().st_mtime_ns for x in sorted(d.iterdir())]
    __import__("time").sleep(0.05)
    c, out = corre(S / "indice.py", "issues", p, "EV-02")
    ok("indice.py issues otra vez sin cambios: no reescribe nada (R2): la fecha de los ficheros no cambia",
       c == 0 and "Al día" in out and fechas == [x.stat().st_mtime_ns for x in sorted(d.iterdir())], out)
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


def filas_del_indice(texto):
    """{issue: [celdas]} de un índice de issues (construccion/<U>/indice.md)."""
    return {c[0]: c for c in ([x.strip() for x in l.strip().strip("|").split("|")] for l in texto.splitlines()
                              if l.startswith("| ISS-"))}


def a_la_vez(*peticiones):
    """Varias sesiones que piden la siguiente issue de EV-01 a la vez, cada una en su carpeta y con su nombre:
    [(código de salida, salida, la issue que se lleva o None)]."""
    procesos = [subprocess.Popen([sys.executable, str(S / "indice.py"), "issues", str(p), "EV-01", "--siguiente", "--quien",
                                  quien], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                 encoding="utf-8", errors="replace") for p, quien in peticiones]
    out = []
    for pr in procesos:
        salida = pr.communicate(timeout=300)[0]
        dada = re.search(r"^(ISS-\d+) de EV-01", salida, re.M)
        out.append((pr.returncode, salida, dada.group(1) if dada else None))
    return out


def pruebas_issues(tmp):
    """Fase 5 del método L.U.C.I.A. (T10 y T11): la columna «Para» de técnico §13 y las issues de construcción que salen
    de ella (indice.py issues): una por requisito, la Base primero, en orden y con las que pueden ir a la vez; las mismas
    con los mismos datos y con su número aunque cambie el análisis; cada una con lo que necesita quien construye; hecha
    cuando su verificación pasa y es de su versión; y reservada con un commit y un push, sin que dos se lleven la misma.
    Con git de verdad y sin red: el remoto es otra carpeta."""
    issues = lambda p, *args, **k: corre(S / "indice.py", "issues", p, *args, **k)
    aprobar = lambda p, uid="EV-01": corre(S / "proyecto.py", "cambio", p, uid, "aprobada", "--fuente", "FU-05")
    aviso_para = lambda out: next((l for l in out.splitlines() if "cada objeto dice «Para»" in l), "")
    lee = lambda f: f.read_text(encoding="utf-8") if f.is_file() else ""

    # T10 · «Para»: de qué requisito es cada objeto de §13. Aviso, no error; sin la columna, uno solo
    p = nueva_con_issues(tmp / "issues para")
    c, out = corre(S / "comprobar.py", p)
    ok("T10: un técnico con «Para» en cada objeto de §13 pasa comprobar.py, sin aviso",
       c == 0 and aviso_para(out).startswith("✓ "), out)
    t = p / "analisis" / "tecnico.md"
    editar(t, "| 4 | `AUT_GenerarNumero` | Regla de expresión | Nuevo | — | | HU-01 |",
           "| 4 | `AUT_GenerarNumero` | Regla de expresión | Nuevo | — | | |")
    editar(t, "| 7 | `AUT Autorizaciones` | Site | Nuevo | — | | PAN-01 |",
           "| 7 | `AUT Autorizaciones` | Site | Nuevo | — | | la lista |")
    c, out = corre(S / "comprobar.py", p)
    ok("T10: el objeto sin «Para», o con uno que no es un requisito ni «Base», es un aviso (no un error) con su nombre",
       c == 0 and aviso_para(out).startswith("· ")
       and aviso_para(out).endswith(": 2 → AUT_GenerarNumero, AUT Autorizaciones"), out)
    q = con_unidades(tmp / "issues sin para")
    c, out = corre(S / "comprobar.py", q)
    ok("T10: en un técnico que aún no usa la columna, un solo aviso, no uno por objeto",
       c == 0 and aviso_para(out).startswith("· ") and ": 1 → la tabla no tiene la columna «Para»" in aviso_para(out), out)
    cambios_md(q, {**FILAS_BASE, "EV-02": "En producción", "EV-03": "Descartada"})
    c, out = corre(S / "comprobar.py", q)
    ok("T10: de los objetos de lo que ya está construido o descartado no avisa", "«Para»" not in out, out)

    # Un retoque se gradúa por lo que cambia, no por el tipo del objeto: el nombre de una acción de registro vive en un
    # record type y no pide DT, ni decidir el orden con la unidad que lo modifica, ni da el objeto por inexistente
    fila = "| 8 | `DEM Alta Solicitud` | Process model | Modifica | — | EV-03 |"
    accion = "| 8 | `DEM Solicitud — acción «Nueva solicitud»` | Record type | Modifica | — | EV-03 |"
    g = con_unidades(tmp / "issues parte")
    editar(g / "analisis" / "tecnico.md", fila, accion)
    editar(g / "impacto" / "FU-06.md", "| Sí (alcance) | Pendiente |", "| Sí (alcance) | ✔ FU-05 |")
    c, out = corre(S / "comprobar.py", g)
    dt = next((l for l in out.splitlines() if "Cambio sobre lo construido" in l), "")
    ok("cambiar el nombre de una acción de registro no pide DT «Cambio sobre lo construido» ni da el record type por "
       "inexistente", c == 0 and dt and "EV-03" not in dt and "DEM Solicitud — acción" not in out
       and "ninguna unidad ha construido" not in out, out)
    c, out = aprobar(g, "EV-03")
    esp = json.loads(lee(g / "construccion" / "EV-03" / "ISS-01-esperado.json") or "{}")
    ok("… ni decidir el orden con la unidad que modifica ese record type: se aprueba, lo avisa y sale su issue, sin "
       "pruebas que ejecutar y sin campos que comparar",
       c == 0 and "| Aprobada |" in fila_de(g, "EV-03") and "EV-03 y EV-02 cambian DEM Solicitud" in out
       and "no hace falta decidir el orden" in out and "Issues de construcción: construccion/EV-03/, 1 issue" in out
       and "no cambia criterios ni reglas: no hay pruebas que ejecutar" in lee(g / "construccion" / "EV-03" / "ISS-01.md")
       and {k: v for k, v in esp.items() if k != "_issue"} == {"DEM Solicitud": {"tipo": "recordType"}},
       out + json.dumps(esp, ensure_ascii=False))
    for nombre, punto in (("campo importe", "Datos existentes"), ("seguridad de la acción «Nueva solicitud»", "Permisos")):
        h = con_unidades(tmp / f"issues parte {punto}")
        editar(h / "analisis" / "tecnico.md", fila, accion.replace("acción «Nueva solicitud»", nombre))
        editar(h / "impacto" / "FU-06.md", "| Sí (alcance) | Pendiente |", "| Sí (alcance) | ✔ FU-05 |")
        c, out = corre(S / "comprobar.py", h)
        c2, out2 = aprobar(h, "EV-03")
        ok(f"si la parte que cambia guarda datos o da permisos ({nombre}), sí: pide «{punto}» y decidir el orden",
           any("Cambio sobre lo construido" in l and f"EV-03: «{punto}» (DEM Solicitud)" in l for l in out.splitlines())
           and c2 == 1 and "EV-02 (DEM Solicitud)" in out2 and "--comparte" in out2, out + out2)

    # T11 · Las issues de una aplicación nueva: al aprobar la unidad, sin otro paso
    p = nueva_con_issues(tmp / "issues app")
    f, t = p / "analisis" / "funcional.md", p / "analisis" / "tecnico.md"
    d = p / "construccion" / "EV-01"
    c, out = issues(p, "EV-01")
    ok("indice.py issues de una unidad sin aprobar es error y no escribe nada",
       c == 1 and "solo se construye una unidad aprobada" in out and not (p / "construccion").exists(), out)
    c, out = aprobar(p)
    nombres = sorted(x.name for x in d.iterdir()) if d.is_dir() else []
    ok("al aprobar la unidad quedan escritas sus issues, antes de que nadie vaya a construir: el índice y, por issue, su "
       ".md, lo esperado y, si tiene escenarios, su .feature",
       c == 0 and "Issues de construcción: construccion/EV-01/, 5 issues" in out
       and nombres == ["ISS-01-esperado.json", "ISS-01.md", "ISS-02-esperado.json", "ISS-02.feature", "ISS-02.md",
                       "ISS-03-esperado.json", "ISS-03.feature", "ISS-03.md", "ISS-04-esperado.json", "ISS-04.md",
                       "ISS-05-esperado.json", "ISS-05.feature", "ISS-05.md", "indice.md"], out + str(nombres))
    if not (d / "indice.md").is_file():      # sin issues no hay nada más que probar
        return
    ind = filas_del_indice(lee(d / "indice.md"))
    ok("una issue por requisito: lo «Base», la primera; los requisitos que comparten pantalla o proceso, juntos",
       list(ind) == ["ISS-01", "ISS-02", "ISS-03", "ISS-04", "ISS-05"] and ind["ISS-01"][1:3] == ["Base", "Base"]
       and ind["ISS-02"][1] == "HU-01, HU-03, HU-04, HU-05, HU-08, PAN-03, PAN-04, PAN-05, ACT-01, ACT-02, ACT-05, ACT-06"
       and ind["ISS-03"][1] == "HU-06, HU-07, PAN-02" and ind["ISS-04"][1] == "ACT-07"
       and ind["ISS-05"][1] == "HU-02, HU-09, PAN-01"
       and ind["ISS-01"][5] == "`AUT Técnicos`, `AUT Responsables`, `AUT Consulta`, `AUT Estado`, `AUT Tipo Autorizacion`, "
                               "`AUT Solicitud`, `AUT Documento`", lee(d / "indice.md"))
    ok("en orden y diciendo cuáles pueden ir a la vez: todas esperan a la Base, y las que comparten un objeto (el record "
       "type y una acción suya, o el que el técnico nombra al hablar de la otra) no van en paralelo",
       [ind[i][3] for i in ind] == ["—", "ISS-01", "ISS-01, ISS-02", "ISS-01", "ISS-01, ISS-03"]
       and [ind[i][4] for i in ind] == ["—", "ISS-04", "ISS-04", "ISS-02, ISS-03, ISS-05", "ISS-04"]
       and "`AUT Solicitud`" in ind["ISS-03"][5] and all(ind[i][6] == "—" for i in ind), lee(d / "indice.md"))
    otra = nueva_con_issues(tmp / "issues app otra vez")
    aprobar(otra)
    ok("con los mismos datos salen las mismas issues, con el mismo número, byte a byte y sin \\r en ningún sistema",
       all((otra / "construccion" / "EV-01" / n).is_file() and (otra / "construccion" / "EV-01" / n).read_bytes()
           == (d / n).read_bytes() and b"\r" not in (d / n).read_bytes() for n in nombres), str(nombres))
    i1, i2, i3 = (lee(d / f"ISS-0{n}.md") for n in (1, 2, 3))
    ok("la issue lleva lo que necesita quien construye: qué se pide (la historia, su pantalla con la captura y sus partes, "
       "su paso), sus objetos, lo que dice de ellos el técnico y lo que no debe tocar por ser de otra issue",
       i2.startswith("# ISS-02 · Registrar una solicitud · EV-01\n")
       and "Depende de: ISS-01 (Base) · En paralelo con: ISS-04 · Aplicación `AUT Autorizaciones`" in i2
       and "- **HU-03 Subsanar una solicitud**\n  Como unidad solicitante, quiero corregir la solicitud" in i2
       and "  - Perfil: Unidad solicitante · Pantalla: PAN-03 · Paso: ACT-06\n" in i2
       and "- **PAN-03 Registrar o subsanar solicitud** · captura `prototipo/capturas/03-alta.png`" in i2
       and "  - Datos · Qué permite: Escribir tipo, título, descripción y fechas · Quién: Unidad solicitante" in i2
       and "| `AUT Tramitar Solicitud` | Process model | Nuevo | §7, §8 |" in i2
       and "- §7 · Pantalla: PAN-03 · Qué es en Appian: `AUT_SolicitudForm`: acción de lista de registros «Nueva "
           "solicitud» de `AUT Solicitud`" in i2
       and "- §8 · Nodo: Subsanar (ACT-06) · Qué hace: Tarea PAN-03 · Asignado a: Grupo de la unidad" in i2
       and "- DT-03 Plazos en días hábiles con el calendario de procesos · Decisión: Temporizadores" in i2
       and "No tocar ni crear, son de otra issue: `AUT Solicitud` (ISS-01)." in i2 and "Citan: AV-01 «" in i2, i2)
    ok("de un objeto del que solo construye una parte (una acción del record type) lleva lo que el técnico dice de esa "
       "parte, no todo lo del objeto; y lo esperado lo comprueba como existente",
       "| `AUT Solicitud — acción «Adjuntar informe del organismo»` | Acción de registro | Nuevo | §4 |" in i3
       and "- §4 · Seguridad de acción de registro para «Nueva solicitud» y «Adjuntar informe del organismo»" in i3
       and "Campo: titulo" not in i3 and "Campo: titulo" in i1
       and {k: v for k, v in json.loads(lee(d / "ISS-03-esperado.json")).items() if k != "_issue"}
       == {"AUT_FichaSolicitud": {"tipo": "interface"}, "AUT Solicitud": {}}, i3)
    textos = [lee(d / n) for n in nombres if n.endswith(".md") and n != "indice.md"]
    ok("ninguna issue pide leer un documento entero: lleva el extracto, no «ver técnico §7»",
       len(textos) == 5 and all("no hay que leer el funcional ni el técnico" in x and "## Lo que dice el técnico" in x
                                and not re.search(r"(?i)\bver (?:el )?(?:técnico|funcional)\b", x)
                                for x in textos), "\n".join(x[:300] for x in textos))
    ok("sus escenarios, cada uno con cómo se comprueba (técnico §14): un caso de prueba guardado o SAIL CLI, que es del "
       "QA de la unidad; sin «Con qué», lo que diga §14",
       "- `HU-01.2` Al enviarla recibe un número con la forma AUT-2026-0001, correlativo por año. → Caso de prueba de "
       "`AUT_GenerarNumero`: Dos envíos a la vez no repiten número" in i2
       and f"- `HU-03.1` {DEVUELTA} → SAIL CLI (QA de la unidad): Subsanar una devuelta" in i2
       and "- `HU-04.1` La tarea aparece a todos los técnicos de la unidad gestora y desaparece para los demás cuando uno "
           "la acepta. → Dos técnicos; aceptar la tarea" in i2 and "## Escenarios (ISS-02.feature) y cómo se comprueban" in i2,
       i2)
    feature = lee(d / "ISS-02.feature")
    ok("el .feature: una sola Característica y una Regla por historia; el criterio con dado, cuando y entonces, en sus tres "
       "pasos; el que aún no los tiene pasa tal cual, con aviso",
       feature.startswith("# language: es\nCaracterística: EV-01 ISS-02 Registrar una solicitud\n\n  Regla: HU-01 Registrar "
                          "una solicitud\n\n    Escenario: HU-01.1\n      * Sin memoria o sin plano")
       and "\n  Regla: HU-03 Subsanar una solicitud\n\n    Escenario: HU-03.1\n      Dada una solicitud devuelta\n      Cuando "
           "la unidad solicitante la reenvía\n      Entonces vuelve a «En revisión» con el mismo número\n" in feature
       and feature.count("Característica:") == 1 and feature.count("\n  Regla: ") == 5 and feature.endswith("\n")
       and "· criterios sin dado, cuando y entonces (pasan tal cual al .feature): HU-01.1, HU-01.2, HU-01.3, HU-02.1" in out
       and "HU-03.1" not in out.split("criterios sin dado")[-1], feature[:700] + out)
    ok("la Base no tiene escenarios: lo dice, no hay pruebas que ejecutar y no lleva .feature",
       "Esta issue no cambia criterios ni reglas: no hay pruebas que ejecutar." in i1 and "Requisitos: Base · Depende de: — "
       in i1 and "## Qué se pide" not in i1, i1[:900])

    # Hecha o pendiente: lo dice la verificación que deja «verificar» (de su versión de ahora y sin diferencias)
    c, out = issues(p, "EV-01", "--siguiente")
    ok("--siguiente en un proyecto que no es un repositorio git: da la primera sin reservar, y lo dice",
       c == 0 and out.startswith("ISS-01 de EV-01: sin reservar: el proyecto no es un repositorio git")
       and "# ISS-01 · Base · EV-01" in out and filas_del_indice(lee(d / "indice.md"))["ISS-01"][6] == "—", out)
    verifica(p, "EV-01", "ISS-01")
    verifica(p, "EV-01", "ISS-02", **{"AUT_RevisarForm": {"falta": True}})
    c, out = issues(p, "EV-01")
    ok("indice.py issues dice cómo va cada una: hecha, pendiente y por qué, y a cuál espera",
       c == 0 and "Al día, sin cambios" in out and "  ISS-01 · Base · Base · hecha\n" in out
       and "  ISS-02 · HU-01, " in out and "· pendiente: lo construido no es lo del técnico: AUT_RevisarForm: falta\n" in out
       and "  ISS-03 · HU-06, HU-07, PAN-02 · Redactar el informe técnico · pendiente: sin verificar · espera a ISS-02\n"
       in out, out)
    c, out = issues(p, "EV-01", "--siguiente")
    ok("con la Base hecha, la siguiente es la primera sin hacer cuyas dependencias están hechas",
       c == 0 and out.startswith("ISS-02 de EV-01: sin reservar"), out)
    verifica(p, "EV-01", "ISS-02")
    verifica(p, "EV-01", "ISS-03")

    # La orden de terminar, lista para copiar en este equipo: sus rutas, su Python y el Dev MCP de desarrollo de su
    # configuración (el que apunta a la «URL de desarrollo» de técnico §0). Sin la configuración de quien lanza la prueba
    casa = tmp / "casa sin nada"
    casa.mkdir()
    aislado = {"APPIAN_RE_HOME": str(casa), "APPDATA": str(casa / "AppData")}
    servidor = lambda url: {"command": "uv", "args": ["run", "python", "-m", "lcp_mcp_server"], "env": {"LCP_URL": url}}
    (p / ".mcp.json").write_text(json.dumps({"mcpServers": {
        "appian-dev-produccion": servidor("https://aut.example.com"),
        "appian-dev-aut": servidor("https://aut-desarrollo.example.com")}}), encoding="utf-8")
    aqui = p.resolve().as_posix()
    verificar = (PLUGIN / "skills" / "appian-reverse-engineering" / "scripts" / "devmcp_extract.py").resolve().as_posix()
    orden = (f'uv run --no-project --python ">=3.10" --with "mcp>=1.2,<2" python "{verificar}" verificar --app "AUT '
             f'Autorizaciones" --esperado "{aqui}/construccion/EV-01/ISS-04-esperado.json" --out '
             f'"{aqui}/construccion/EV-01/verificacion/ISS-04.json"')
    c, out = issues(p, "EV-01", "ISS-04", env=aislado, cwd=p)
    bloque = out.split("```")[1].strip().split("\n") if out.count("```") == 2 else []
    ok("la orden de terminar se puede copiar tal cual: rutas de este equipo, sin marcadores, y el Dev MCP de desarrollo",
       c == 0 and bloque == [orden + ' --server-name "appian-dev-aut"'] and "<p>" not in out.split("```")[1]
       and "<skill" not in out.split("```")[1]
       and "No hay pruebas que ejecutar" in out and out.startswith("# ISS-04 · Generar autorización · EV-01"), out)
    editar(t, "| URL de desarrollo | https://aut-desarrollo.example.com | Equipo |\n", "")
    c, out = issues(p, "EV-01", "ISS-04", env=aislado, cwd=p)
    ok("con varios Dev MCP y sin la URL de desarrollo en técnico §0, no elige: lo dice",
       c == 0 and out.split("```")[1].strip() == orden and "técnico §0 no dice la «URL de desarrollo»" in out
       and "`--server-name <el de desarrollo>`" in out, out)
    editar(t, "| URL de producción |", "| URL de desarrollo | https://aut-desarrollo.example.com | Equipo |\n| URL de producción |")

    # Si cambia el análisis y se regeneran, cada issue conserva su número; la que cambia vuelve a estar pendiente
    editar(t, "| 4 | `AUT_GenerarNumero` |", "| 3 | `AUT_FiltroPorUnidad` | Regla de expresión | Nuevo | — | | HU-09 |\n"
           "| 4 | `AUT_GenerarNumero` |")
    editar(t, "| 7 | `AUT Autorizaciones` | Site | Nuevo | — | | PAN-01 |", "| 7 | `AUT Autorizaciones` | Site | Nuevo | — | "
           "| PAN-01 |\n| 7 | `AUT Reclamar Informe` | Process model | Nuevo | — | | ACT-08 |")
    editar(f, "- `HU-07.1` Solo admite PDF de hasta 20 MB.", "- `HU-07.1` Solo admite PDF de hasta 30 MB.")
    de_antes = {n: de_issue(p, "EV-01", n)["version"] for n in ("ISS-01", "ISS-02", "ISS-03", "ISS-04", "ISS-05")}
    c, out = issues(p, "EV-01")
    ind = filas_del_indice(lee(d / "indice.md"))
    ahora = {n: de_issue(p, "EV-01", n)["version"] for n in de_antes}
    ok("si cambia el análisis, cada issue conserva su número (aunque ahora se construya antes) y la nueva toma el siguiente",
       c == 0 and list(ind) == ["ISS-01", "ISS-05", "ISS-02", "ISS-03", "ISS-04", "ISS-06"]
       and ind["ISS-05"][1] == "HU-02, HU-09, PAN-01" and ind["ISS-05"][5] == "`AUT_FiltroPorUnidad`, `AUT Autorizaciones`"
       and ind["ISS-06"][1] == "ACT-08" and (d / "ISS-06.md").is_file(), out + lee(d / "indice.md"))
    ok("la issue que cambia (un criterio suyo, un objeto más) vuelve a estar pendiente; la que no, sigue hecha aunque "
       "cambie con cuáles va en paralelo",
       ahora["ISS-03"] != de_antes["ISS-03"] and ahora["ISS-05"] != de_antes["ISS-05"]
       and all(ahora[n] == de_antes[n] for n in ("ISS-01", "ISS-02", "ISS-04")) and "ISS-06" in ind["ISS-02"][4]
       and "  ISS-02 · HU-01, " in out and re.search(r"ISS-02 · [^\n]* · hecha\n", out)
       and re.search(r"ISS-03 · [^\n]* · pendiente: ha cambiado desde su última verificación", out), out)
    editar(t, "| 6 | `AUT_PlantillaAutorizacion` | Documento | Nuevo | — | | ACT-07 |\n", "")
    c, out = issues(p, "EV-01")
    ok("una issue que deja de existir se quita, con sus ficheros, y su número no se da a otra",
       c == 0 and "se quitan: ISS-04-esperado.json, ISS-04.md" in out and not (d / "ISS-04.md").exists()
       and "ISS-04" not in filas_del_indice(lee(d / "indice.md")), out)

    # Construida es todas sus issues hechas; al quedar una sola, la orden de terminar lleva también la de marcar la unidad
    c, out = corre(S / "proyecto.py", "cambio", p, "EV-01", "construida")
    ok("cambio construida con issues sin hacer es error: dice cuáles y por qué",
       c == 1 and "issues sin hacer: ISS-05 (sin verificar); ISS-03 (ha cambiado desde su última verificación); ISS-06 "
       "(sin verificar)" in out and "| Aprobada |" in fila_de(p, "EV-01"), out)
    verifica(p, "EV-01", "ISS-05")
    verifica(p, "EV-01", "ISS-03")
    c, out = issues(p, "EV-01", "ISS-06", env=aislado, cwd=p)
    bloque = out.split("```")[1].strip().split("\n") if out.count("```") == 2 else []
    python = "python" if os.name == "nt" else "python3"
    ok("la última issue que queda lleva también la orden de marcar la unidad, con el Python de este equipo",
       c == 0 and len(bloque) == 2 and bloque[0].endswith('ISS-06.json" --server-name "appian-dev-aut"')
       and bloque[1] == f'{python} "{(S / "proyecto.py").resolve().as_posix()}" cambio "{aqui}" EV-01 construida', out)
    verifica(p, "EV-01", "ISS-06")
    c, out = issues(p, "EV-01", "--siguiente")
    c2, out2 = corre(S / "proyecto.py", "cambio", p, "EV-01", "construida")
    ok("con todas hechas, --siguiente lo dice con la orden de marcar la unidad, y cambio construida pasa",
       c == 0 and "todas sus issues están hechas" in out and "EV-01 construida" in out
       and c2 == 0 and re.search(r"\| Construida \| [^|]+ \| \d{4}-\d\d-\d\d · verificada \|", fila_de(p, "EV-01")), out + out2)
    corre(S / "proyecto.py", "cambio", p, "EV-02", "abrir", "--titulo", "El botón de la lista")
    editar(t, "| 7 | `AUT Autorizaciones` | Site | Nuevo | — | | PAN-01 |", "| 7 | `AUT Autorizaciones` | Site | Nuevo | — | "
           "| PAN-01 |\n| 8 | `AUT Solicitud — acción «Nueva solicitud»` | Record type | Modifica | — | EV-02 | PAN-01 |")
    c, out = corre(S / "comprobar.py", p)
    ok("en una aplicación nueva ya construida, cambiar el nombre de una acción de un record type suyo no avisa de un "
       "«Modifica» de algo que nadie ha construido, ni pide DT, ni da error en §13",
       not any(l.startswith(("· ", "✗ ")) and ("ninguna unidad ha construido" in l or "Cambio sobre lo construido" in l
                                               or "técnico §13: la Situación" in l) for l in out.splitlines()), out)

    # Un retoque cosmético no gana ningún paso: una unidad con un solo cambio da una sola issue, que dice qué cambia
    # (el antes y el después, no «ver técnico §7»), que no hay pruebas que ejecutar, y la misma orden de siempre
    r = con_unidades(tmp / "issues retoque")
    corre(S / "proyecto.py", "copia", r)
    corre(S / "proyecto.py", "cambio", r, "EV-04", "abrir", "--titulo", "El panel dice «Días en espera»")
    for x in ("funcional.md", "tecnico.md"):
        editar(r / "analisis" / x, "Versión: 1.1", "Versión: 1.2")
    editar(r / "analisis" / "decisiones.md", "| 1.1 | 2026-10-12 | Firma de la revisión | FU-04 | — |",
           "| 1.1 | 2026-10-12 | Firma de la revisión | FU-04 | — |\n| 1.2 | 2026-10-14 | El panel dice «Días en espera» | FU-08 | — |")
    editar(r / "analisis" / "funcional.md", "| Lista | Ver título, estado, gestor y días pendiente | Revisor |",
           "| Lista | Ver título, estado, gestor y días en espera | Revisor |")
    editar(r / "analisis" / "tecnico.md", "| — | Columna «Días pendiente» con `DEM_ER_DiasPendiente` |",
           "| — | Columna «Días en espera» con `DEM_ER_DiasPendiente` |")
    editar(r / "analisis" / "tecnico.md", "| 8 | `DEM Alta Solicitud` | Process model | Modifica | — | EV-03 |",
           "| 8 | `DEM Alta Solicitud` | Process model | Modifica | — | EV-03 |\n| 9 | `DEM_Dashboard` | Interfaz | Modifica | — | EV-04 |")
    (r / "impacto" / "FU-08.md").write_text(
        "# Impacto de FU-08 · El título de la columna · 2026-10-14\nAnálisis base: versión 1.1 · Cambio: EV-04 · Estado: "
        "aplicado en 1.2\n\n## Puntos\n| # | Tipo | Qué se dice | Encaja en | Cambio propuesto | Revisar también | Requiere | "
        "Decisión |\n|---|---|---|---|---|---|---|---|\n| 1 | CAMBIA | La columna se llama «Días en espera» [FU-08] | PAN-03 | "
        "PAN-03 con el título nuevo | HU-03 | — | ✔ |\n\n## Aplicado\nVersión 1.2: PAN-03 modificada · técnico §7 y §13\n",
        encoding="utf-8")
    c, out = aprobar(r, "EV-04")
    dr = r / "construccion" / "EV-04"
    unica = lee(dr / "ISS-01.md")
    ok("un retoque: una unidad con un solo cambio da una sola issue, ya escrita al aprobarla, sin escenarios ni .feature",
       c == 0 and sorted(x.name for x in dr.iterdir()) == ["ISS-01-esperado.json", "ISS-01.md", "indice.md"]
       and unica.startswith("# ISS-01 · El panel dice «Días en espera» · EV-04\n") and "Requisitos: PAN-03 · " in unica
       and "Esta issue no cambia criterios ni reglas: no hay pruebas que ejecutar." in unica
       and json.loads(lee(dr / "ISS-01-esperado.json")).get("DEM_Dashboard") == {"tipo": "interface"}, out + unica)
    ok("y dice qué cambia, en el funcional y en el técnico, con lo que decía antes: no hay que leer el técnico para saberlo",
       "- **PAN-03 Panel de solicitudes** (cambia)\n  - antes: | Lista | Ver título, estado, gestor y días pendiente | "
       "Revisor |\n  - ahora: | Lista | Ver título, estado, gestor y días en espera | Revisor |\n" in unica
       and "- §7 (cambia) · Pantalla: PAN-03 · Qué es en Appian: `DEM_Dashboard`, página «Panel» del site · Notas: Columna "
           "«Días en espera» con `DEM_ER_DiasPendiente` (antes: Columna «Días pendiente» con `DEM_ER_DiasPendiente`)\n"
       in unica and "- Y 2 líneas más del técnico que no cambian con EV-04: lo que dicen ya está construido." in unica
       and "HU-03" not in unica and "Cambio sobre lo construido" not in unica, unica)
    c, out = issues(r, "EV-04", "--siguiente", env=aislado, cwd=r)
    bloque = out.split("```")[1].strip().split("\n") if out.count("```") == 2 else []
    ok("y la misma orden de siempre: verificar y marcar la unidad, sin pasos de más",
       c == 0 and len(bloque) == 2 and " verificar --app " in bloque[0] and "ISS-01-esperado.json" in bloque[0]
       and bloque[1].endswith(" EV-04 construida") and "No hay pruebas que ejecutar" in out, out)
    verifica(r, "EV-04", "ISS-01")
    c, out = corre(S / "proyecto.py", "cambio", r, "EV-04", "construida")
    ok("construido y verificado el retoque, la unidad se marca Construida", c == 0 and "· verificada |" in fila_de(r, "EV-04"),
       out)

    # Un evolutivo con «Para»: lo común del cambio (el record type) va en la Base y cada historia, en su issue, con lo
    # suyo: la DT de lo construido, la corrección urgente que hay que reaplicar y la orden de marcar con --reaplicada
    v = con_unidades(tmp / "issues evolutivo")
    tv, dv = v / "analisis" / "tecnico.md", v / "construccion" / "EV-02"
    editar(tv, "| Paso | Objeto | Tipo | Situación | Sustituye a | Cambio |\n|---|---|---|---|---|---|",
           "| Paso | Objeto | Tipo | Situación | Sustituye a | Cambio | Para |\n|---|---|---|---|---|---|---|")
    for fila_, para in (("`DEM Solicitud` | Record type | Modifica", "Base"), ("`DEM_ER_Firma` | Regla de expresión | Nuevo", "HU-04"),
                        ("`DEM_RevisionForm` | Interfaz | Modifica", "PAN-01"), ("`DEM_SolicitudForm` | Interfaz | Modifica", "HU-02")):
        editar(tv, f"{fila_} | — | EV-02 |", f"{fila_} | — | EV-02 | {para} |")
    c, out = issues(v, "EV-02")
    e1, e2, e3 = (lee(dv / f"ISS-0{n}.md") for n in (1, 2, 3))
    ind = filas_del_indice(lee(dv / "indice.md"))
    ok("un evolutivo con «Para»: la Base con el record type que cambia y una issue por historia, que pueden ir a la vez",
       c == 0 and [(ind[i][1], ind[i][3], ind[i][4], ind[i][5]) for i in ind] == [
           ("Base", "—", "—", "`DEM Solicitud`"), ("HU-04, PAN-01", "ISS-01", "ISS-03", "`DEM_ER_Firma`, `DEM_RevisionForm`"),
           ("HU-02", "ISS-01", "ISS-02", "`DEM_SolicitudForm`")], out + lee(dv / "indice.md"))
    ok("cada issue lleva solo lo suyo: la DT «Cambio sobre lo construido» en la del record type y la corrección urgente que "
       "hay que reaplicar en la del objeto que corrige; de lo que no cambia en el técnico, lo que ya dice de sus objetos",
       "## Cambio sobre lo construido (DT-04)" in e1 and "- §3.1 (nuevo) · Campo: firmaRevisor" in e1
       and "Cambio sobre lo construido" not in e2 + e3 and "Reaplicar URG-01 en `DEM_SolicitudForm`" in e3
       and "Reaplicar" not in e1 + e2 and "- **HU-04 Firmar la revisión** (nueva)" in e2
       and "El técnico no cambia para esta issue con EV-02. Lo que ya dice de sus objetos:" in e3
       and "- §7 · Pantalla: PAN-02 · Qué es en Appian: `DEM_SolicitudForm`, formulario de tarea" in e3, e1 + e2 + e3)
    ok("una issue con una sola historia lleva el .feature de esa historia, sin «Regla»",
       lee(dv / "ISS-03.feature") == "# language: es\nCaracterística: HU-02 Corregir y reenviar una solicitud devuelta\n\n"
       "  Escenario: HU-02.2\n    * Al reenviarla vuelve a «Enviada» con el mismo número y sin la firma anterior.\n",
       lee(dv / "ISS-03.feature"))
    verifica(v, "EV-02", "ISS-01")
    verifica(v, "EV-02", "ISS-02")
    c, out = issues(v, "EV-02", "ISS-03", env=aislado, cwd=v)
    ok("la orden de marcar la unidad lleva el --reaplicada de la corrección urgente que la issue pide reaplicar",
       c == 0 and out.count("```") == 2 and out.split("```")[1].strip().endswith(" EV-02 construida --reaplicada URG-01"), out)

    # Reservar: --siguiente escribe en el índice quién tiene la issue y desde cuándo, y hace commit y push de las issues
    # de la unidad. Dos que la piden a la vez no se llevan la misma. Nunca falla por git
    if not shutil.which("git"):
        print("· Reservar una issue: no hay git en este equipo; no se prueba")
        return
    base = tmp / "issues con git"
    ana = nueva_con_issues(base / "ana")
    corre(S / "proyecto.py", "iniciar", ana)
    (ana / "fuentes" / "FU-05-aprobacion.md").write_bytes("# FU-05\nAprobada la construcción inicial.\n".encode("utf-8"))
    c, out = issues(ana, "EV-01", "--siguiente", "--quien", "Ana") if aprobar(ana)[0] == 0 else (9, "no se aprueba")
    ok("en un repositorio recién creado, sin remoto ni ningún commit, --siguiente no falla: reserva con el primer commit, "
       "solo con las issues de la unidad, y dice que no está subido",
       c == 0 and out.startswith("ISS-01 de EV-01, reservada a nombre de Ana · ")
       and "con un commit, sin subir: el repositorio no tiene remoto" in out.splitlines()[0]
       and git(ana, "log", "--format=%s")[1].strip() == "EV-01: ISS-01 reservada por Ana"
       and all(x.startswith("construccion/EV-01/") for x in git(ana, "show", "--name-only", "--format=")[1].split()), out)
    git(ana, "add", "-A")
    git(ana, "commit", "--quiet", "-m", "Análisis de la 1.1 y las issues de EV-01")
    remoto = base / "remoto.git"
    git(base, "init", "--quiet", "--bare", str(remoto))
    git(ana, "remote", "add", "origin", str(remoto))
    c0, o0 = git(ana, "push", "--quiet", "-u", "origin", "main")
    c, out = issues(ana, "EV-01", "--liberar", "ISS-01")
    del_remoto = lambda: filas_del_indice(git(remoto, "show", "main:construccion/EV-01/indice.md")[1])
    ultimo = lambda donde=None: (git(donde or remoto, "log", "-1", "--format=%s", "main")[1].strip(),
                                 git(donde or remoto, "show", "--name-only", "--format=", "main")[1].split())
    ok("--liberar quita una reserva que nadie va a seguir, con su commit y su push",
       c0 == 0 and c == 0 and "ISS-01 de EV-01, sin reserva (con un commit, subido a origin/main)" in out
       and del_remoto()["ISS-01"][6] == "—" and ultimo() == ("EV-01: ISS-01 sin reserva", ["construccion/EV-01/indice.md"]),
       o0 + out + str(ultimo()))
    luis = base / "luis"
    git(base, "clone", "--quiet", "-b", "main", str(remoto), str(luis))
    (ana / "notas" / "pendiente.md").write_text("# Algo a medias\n", encoding="utf-8")
    uno, otro = a_la_vez((ana, "Ana"), (ana, "Berta"))
    ok("dos sesiones de la misma carpeta que piden la siguiente a la vez no se llevan la misma: solo está libre la Base, y "
       "la otra se queda sin ninguna",
       uno[0] == 0 and otro[0] == 0 and sorted([uno[2], otro[2]], key=str) == ["ISS-01", None]
       and "ninguna issue disponible ahora" in uno[1] + otro[1], uno[1][:600] + otro[1][:600])
    quien = "Ana" if uno[2] else "Berta"
    reserva = del_remoto()["ISS-01"][6]
    ok("la reserva dice quién tiene la issue y desde cuándo, y sube con un commit que solo lleva el índice de la unidad: lo "
       "que haya a medias en la carpeta no entra",
       re.fullmatch(rf"{quien} · \d{{4}}-\d\d-\d\dT\d\d:\d\dZ", reserva) is not None
       and ultimo() == (f"EV-01: ISS-01 reservada por {quien}", ["construccion/EV-01/indice.md"])
       and "?? notas/" in git(ana, "status", "--porcelain")[1]
       and f"ISS-01 de EV-01, reservada a nombre de {reserva}: con un commit, subido a origin/main" in uno[1] + otro[1],
       reserva + str(ultimo()) + uno[1][:300] + otro[1][:300])
    c, out = issues(luis, "EV-01", "--siguiente", "--quien", "Luis")
    ok("otra persona, en su copia, se pone al día antes de pedir: la Base está reservada y las demás la esperan",
       c == 0 and "ninguna issue disponible ahora" in out
       and f"  ISS-01 · Base · Base · pendiente: sin verificar · reservada: {reserva}\n" in out, out)
    verifica(ana, "EV-01", "ISS-01")
    git(ana, "add", "construccion")
    git(ana, "commit", "--quiet", "-m", "ISS-01 verificada")
    git(ana, "push", "--quiet")
    carla, dora = base / "carla", base / "dora"
    for copia in (carla, dora):
        git(base, "clone", "--quiet", "-b", "main", str(remoto), str(copia))
    uno, otro = a_la_vez((luis, "Luis"), (dora, "Dora"))
    ind = del_remoto()
    ok("dos personas que piden la siguiente a la vez, cada una en su copia, no se llevan la misma: la que llega tarde al "
       "push se pone al día y se lleva la siguiente",
       uno[0] == 0 and otro[0] == 0 and sorted([str(uno[2]), str(otro[2])]) == ["ISS-02", "ISS-04"]
       and ind[uno[2]][6].startswith("Luis · ") and ind[otro[2]][6].startswith("Dora · "),
       uno[1][:500] + otro[1][:500] + str(ind))
    ok("la reserva de la issue ya hecha se ha quitado sola", ind["ISS-01"][6] == "—", str(ind["ISS-01"]))
    de_luis = uno[2]
    c, out = issues(luis, "EV-01", "--liberar", "ISS-04" if de_luis == "ISS-02" else "ISS-02")
    libre = "ISS-04" if de_luis == "ISS-02" else "ISS-02"
    ok("--liberar, desde otra copia: se pone al día, quita esa reserva y la sube",
       c == 0 and del_remoto()[libre][6] == "—" and del_remoto()[de_luis][6].startswith("Luis · "), out)
    # Carla clonó antes de esas reservas. Si no llega a traerlas (la primera vez, al_dia no trae nada), reserva la que ve
    # libre y su push falla: quita su commit, se pone al día y se lleva la que de verdad queda libre
    import issues as iss
    de_verdad, veces = iss.al_dia, []

    def sin_traer_la_primera_vez(raiz, a_donde):
        veces.append(1)
        return (True, "") if len(veces) == 1 else de_verdad(raiz, a_donde)
    iss.al_dia = sin_traer_la_primera_vez
    try:
        _, _, plan, dada, como = iss.siguiente(carla, "EV-01", "Carla")
    finally:
        iss.al_dia = de_verdad
    registro = git(carla, "log", "--format=%s", "-5")[1]
    ok("si el push falla porque otro reservó antes, quita su commit, se pone al día y da la siguiente; no deja nada a "
       "medias en su copia",
       len(veces) == 2 and dada is not None and dada.id == libre and como == "con un commit, subido a origin/main"
       and del_remoto()[libre][6].startswith("Carla · ") and del_remoto()[de_luis][6].startswith("Luis · ")
       and registro.splitlines()[0] == f"EV-01: {libre} reservada por Carla"
       and registro.count("reservada por Carla") == 1
       and git(carla, "status", "--porcelain")[1].strip() == "", registro + como + str(del_remoto()))
    git(dora, "remote", "set-url", "origin", str(base / "no existe.git"))
    verifica(dora, "EV-01", "ISS-02")
    verifica(dora, "EV-01", "ISS-04")
    c, out = issues(dora, "EV-01", "--siguiente", "--quien", "Dora")
    ok("sin poder llegar al remoto no falla: reserva con un commit en su equipo y dice que no está subido",
       c == 0 and out.startswith("ISS-03 de EV-01, reservada a nombre de Dora · ")
       and "con un commit en este equipo, sin subir: no se pudo consultar el remoto" in out.splitlines()[0], out)


# Los dos criterios de ejemplo del diseño (docs/diseno/2026-10-14-metodo-lucia.md, «Requisitos en Gherkin») y su .feature
DEVUELTA = ("Dada una solicitud devuelta, cuando la unidad solicitante la reenvía, entonces vuelve a «En revisión» con "
            "el mismo número.")
EN_REVISION = "Dada una solicitud en revisión, cuando la unidad solicitante intenta cambiarla, entonces no puede."
# Un criterio escrito en dos líneas: la segunda, sangrada, es parte de él, como en el Word
DOS_LINEAS = ("Dada una solicitud devuelta, cuando el técnico abre su historial, entonces ve el comentario",
              "y la fecha de la devolución.")
FEATURE = """# language: es
Característica: HU-03 Subsanar una solicitud

  Escenario: HU-03.1
    Dada una solicitud devuelta
    Cuando la unidad solicitante la reenvía
    Entonces vuelve a «En revisión» con el mismo número

  Escenario: HU-03.2
    Dada una solicitud en revisión
    Cuando la unidad solicitante intenta cambiarla
    Entonces no puede
"""


def pruebas_gherkin(tmp):
    """Fase 4 del método L.U.C.I.A. (T9): cada criterio es una línea con dado, cuando y entonces. modelo.pasos_gherkin los
    separa, Proyecto.feature escribe el .feature de una historia sin IA (lo usará indice.py issues) y comprobar.py
    --anterior avisa del criterio nuevo o cambiado que no los lleva; los de antes que no se tocan, no. Devuelve el
    proyecto de la prueba, para mirar su Word, o None."""
    try:
        import modelo
        separa, _, _ = modelo.pasos_gherkin, modelo.Proyecto.escenarios, modelo.Proyecto.feature
    except (ImportError, AttributeError) as e:
        ok("modelo.pasos_gherkin, Proyecto.escenarios y Proyecto.feature existen", False, repr(e))
        return None
    ok("pasos_gherkin: el criterio de ejemplo del diseño, en sus tres pasos y sin el punto final",
       separa(DEVUELTA) == [("Dada", "una solicitud devuelta"), ("Cuando", "la unidad solicitante la reenvía"),
                            ("Entonces", "vuelve a «En revisión» con el mismo número")], str(separa(DEVUELTA)))
    variantes = [("Dado", "Dado un borrador sin plano, cuando la unidad lo envía, entonces aparece «Adjunte el plano»."),
                 ("Dados", "Dados dos técnicos de la unidad, cuando uno acepta la tarea, entonces desaparece para el otro."),
                 ("Dadas", "Dadas dos solicitudes enviadas a la vez, cuando se registran, entonces reciben números seguidos."),
                 ("Dado", "dado que la solicitud está devuelta, Cuando la unidad la reenvía; Entonces vuelve a «En revisión»"),
                 ("Dada", "Dada una solicitud devuelta cuando la unidad la reenvía entonces vuelve a «En revisión»")]
    leidas = [separa(c) or [("—", "")] for _, c in variantes]
    ok("pasos_gherkin: Dado, Dada, Dados y Dadas; con mayúsculas, con punto y coma o sin comas",
       [p[0][0] for p in leidas] == [k for k, _ in variantes] and all(len(p) == 3 for p in leidas)
       and leidas[3] == [("Dado", "que la solicitud está devuelta"), ("Cuando", "la unidad la reenvía"),
                         ("Entonces", "vuelve a «En revisión»")], str(leidas))
    pasos = separa("Dada una solicitud devuelta cuando faltaba el plano y con memoria, cuando el técnico la revisa y la da "
                   "por completa, entonces aparece «Completa, cuando entonces» y pasa a «En informe». <!-- ✅ FU-04 00:01:00 -->")
    ok("pasos_gherkin: una «y» se queda en su paso; un «cuando» sin coma o entre comillas no corta; sin el comentario",
       pasos == [("Dada", "una solicitud devuelta cuando faltaba el plano y con memoria"),
                 ("Cuando", "el técnico la revisa y la da por completa"),
                 ("Entonces", "aparece «Completa, cuando entonces» y pasa a «En informe»")], str(pasos))
    unidos = [separa(c) for c in ("Dada una solicitud en revisión, cuando el técnico la da por completa y entonces pasa a «En informe».",
                                  "Dada una solicitud en revisión, y cuando el técnico la da por completa, y entonces pasa a «En informe».",
                                  "Dada una solicitud en revisión e cuando el técnico la da por completa e entonces pasa a «En informe»")]
    ok("pasos_gherkin: la «y» o la «e» de «y entonces» y de «, y cuando» no se queda colgando del paso anterior",
       all(p == [("Dada", "una solicitud en revisión"), ("Cuando", "el técnico la da por completa"),
                 ("Entonces", "pasa a «En informe»")] for p in unidos), str(unidos))
    sueltos = ["Al reenviarla vuelve a «En revisión» con el mismo número.", "Un organismo dado de baja no se puede elegir.",
               "Dada una solicitud devuelta, entonces vuelve a «En revisión».",
               "Dada una solicitud devuelta, cuando la unidad la reenvía.",
               "Cuando la unidad la reenvía, entonces vuelve a «En revisión».", "Dada, cuando la reenvía, entonces vuelve."]
    ok("pasos_gherkin: sin dado, sin cuando o sin entonces no es un escenario",
       not any(separa(c) for c in sueltos), str([c for c in sueltos if separa(c)]))

    # La plantilla enseña lo mismo que leen los scripts: sus criterios de ejemplo son los del diseño y de su historia
    # sale, tal cual, el .feature del diseño; un criterio anulado no sale y la ficha de un intercambio vale igual
    plantilla = (SKILL / "references" / "funcional-plantilla.md").read_text(encoding="utf-8")
    ejemplos = [l for l in plantilla.split("\n") if re.match(r"- `(?:HU|INT)-\d+\.\d+` ", l)]
    ok("funcional-plantilla.md: sus criterios de ejemplo son los del diseño, con dado, cuando y entonces",
       f"- `HU-03.1` {DEVUELTA}" in ejemplos and f"- `HU-03.2` {EN_REVISION}" in ejemplos
       and any(l.startswith("- `INT-") for l in ejemplos) and all(separa(l.split("` ", 1)[1]) for l in ejemplos),
       "\n".join(ejemplos))
    fichas = [x.group(1) for k in ("HU-03", "INT-02")
              for x in [re.search(rf"```markdown\n(\*\*{k} — .*?)```", plantilla, re.S)] if x]
    mini = tmp / "feature" / "analisis"
    mini.mkdir(parents=True)
    if len(fichas) == 2:
        with open(mini / "funcional.md", "w", encoding="utf-8", newline="\n") as fh:
            fh.write("# Prueba — Diseño funcional\n\nVersión: 0.1 · Estado: borrador\n\n## 4. Funcionalidades\n\n" + fichas[0]
                     + "- ~~`HU-03.3`~~ Anulado por D-04: ~~Dada una solicitud, cuando se reenvía, entonces se duplica.~~\n\n"
                     "## 9. Relación con otros sistemas\n\n" + fichas[1])
    m = modelo.cargar(mini.parent)
    texto, sin = m.feature("HU-03") if "HU-03" in m.piezas else ("", ["sin la ficha HU-03 de la plantilla"])
    ok("Proyecto.feature: de la historia de la plantilla sale el .feature del diseño, sin el criterio anulado",
       texto == FEATURE and sin == [] and m.feature("HU-03") == (texto, sin), texto + str(sin))
    texto, sin = m.feature("INT-02") if "INT-02" in m.piezas else ("", ["sin la ficha INT-02 de la plantilla"])
    ok("Proyecto.feature: la ficha de un intercambio, igual que una historia",
       texto.startswith("# language: es\nCaracterística: INT-02 Comprobar el organismo en su registro\n\n"
                        "  Escenario: INT-02.1\n    Dad") and "\n    Cuando " in texto and "\n    Entonces " in texto
       and sin == [], texto + str(sin))

    # Un análisis que ya existe: en la 1.2 cambian HU-03.2 (ya con dado, cuando y entonces) y HU-07.1 (sin ellos), son
    # nuevos HU-03.3 (con), HU-05.3 (sin, y en dos líneas) y HU-06.3 y HU-06.4 (con, y en dos líneas: el Word las une y
    # el .feature también), y HU-02.1 solo gana una cita. Lo demás sigue como estaba
    g = tmp / "gherkin"
    shutil.copytree(EJEMPLO, g)
    corre(S / "proyecto.py", "copia", g)
    f, t, d = (g / "analisis" / x for x in ("funcional.md", "tecnico.md", "decisiones.md"))
    for x in (f, t):
        editar(x, "Versión: 1.1", "Versión: 1.2")
    editar(d, "se quita la urgencia | FU-03 | Analista, 2026-09-24 |", "se quita la urgencia | FU-03 | Analista, 2026-09-24 |\n"
           "| 1.2 | 2026-10-14 | Reenvío de la solicitud devuelta y tamaño del informe | FU-04 | — |")
    editar(f, "- `HU-03.2` Al reenviarla vuelve a «En revisión» con el mismo número.",
           f"- `HU-03.2` {DEVUELTA} <!-- ✅ FU-04 00:02:00 -->\n- `HU-03.3` {EN_REVISION} <!-- ✅ FU-04 00:03:00 -->")
    editar(f, "- `HU-07.1` Solo admite PDF de hasta 20 MB.", "- `HU-07.1` Solo admite PDF de hasta 30 MB.")
    editar(f, "recibe el aviso AV-05 con el comentario.", "recibe el aviso AV-05 con el comentario.\n"
           "- `HU-05.3` La devolución queda en el historial de la solicitud,\n  con su comentario y su fecha.")
    editar(f, "la solicitud pasa a «Pendiente de resolver».", "la solicitud pasa a «Pendiente de resolver».\n"
           f"- `HU-06.3` {DOS_LINEAS[0]}\n  {DOS_LINEAS[1]} <!-- ✅ FU-04 00:05:00 -->\n"
           "- `HU-06.4` Dado un informe técnico sin terminar, cuando la unidad solicitante abre la solicitud,\n"
           "  entonces no lo ve.")
    editar(f, "- `HU-02.1` La lista solo enseña solicitudes de la unidad de quien entra.",
           "- `HU-02.1` La lista solo enseña solicitudes de la unidad de quien entra. <!-- ✅ FU-04 00:04:00 -->")
    editar(t, "| HU-03.1, HU-03.2 |", "| HU-03.1, HU-03.2, HU-03.3 |")
    editar(t, "| HU-05.1, HU-05.2 |", "| HU-05.1, HU-05.2, HU-05.3 |")
    editar(t, "| HU-06.1, HU-06.2 |", "| HU-06.1, HU-06.2, HU-06.3, HU-06.4 |")
    c, out = corre(S / "comprobar.py", g, "--anterior", g / "versiones" / "v1.1")
    linea = next((l for l in out.splitlines() if "dado, cuando y entonces" in l), "")
    ok("comprobar.py --anterior: el criterio nuevo y el cambiado sin dado, cuando y entonces son aviso, no error, con "
       "su ID, su línea y cómo se arreglan",
       c == 0 and linea.startswith("· ") and "HU-05.3 (l." in linea and "HU-07.1 (l." in linea
       and "«Dado…, cuando…, entonces…»" in linea, out)
    ok("comprobar.py --anterior: no avisa de los criterios de antes que no se tocan, del que solo cambia su cita ni de "
       "los que ya los llevan", re.findall(r"[A-Z]+-\d+\.\d+", linea) == ["HU-05.3", "HU-07.1"], linea)
    c, out = corre(S / "comprobar.py", g)
    ok("comprobar.py sin --anterior: de dado, cuando y entonces no dice nada", c == 0 and "cuando y entonces" not in out, out)
    mg = modelo.cargar(g)
    texto, sin = mg.feature("HU-03")
    cabecera, escenarios = FEATURE.split("\n\n", 1)    # los dos del diseño son aquí HU-03.2 y HU-03.3
    ok("Proyecto.feature: un criterio sin dado, cuando y entonces pasa tal cual, como un paso «*», y se avisa de él",
       sin == ["HU-03.1"] and texto == cabecera + "\n\n  Escenario: HU-03.1\n    * El comentario del técnico aparece "
       "encima del formulario mientras se subsana.\n\n" + escenarios.replace("HU-03.2", "HU-03.3").replace("HU-03.1", "HU-03.2"),
       texto + str(sin))
    lineas, sin_cabecera = mg.escenarios("HU-03")
    ok("Proyecto.escenarios: los mismos escenarios sin la cabecera, para juntar los de varias historias en un .feature",
       lineas[:2] == ["", "  Escenario: HU-03.1"] and cabecera + "\n" + "\n".join(lineas) + "\n" == texto
       and sin_cabecera == sin, str(lineas))
    ok("Proyecto.feature: una historia anulada o una pieza sin criterios no tienen .feature",
       mg.feature("HU-11") == ("", []) and mg.feature("PAN-01") == ("", []))
    # Un criterio que sigue en la línea de debajo entra entero, como en el Word: ni se pierde la segunda línea del
    # «entonces», ni deja de verse el «entonces» que está en ella, ni se corta el que pasa tal cual
    texto, sin = mg.feature("HU-06")
    ok("Proyecto.feature: un criterio en dos líneas sale entero, con el «entonces» en la primera o en la segunda",
       "  Escenario: HU-06.3\n    Dada una solicitud devuelta\n    Cuando el técnico abre su historial\n"
       "    Entonces ve el comentario y la fecha de la devolución\n" in texto
       and "  Escenario: HU-06.4\n    Dado un informe técnico sin terminar\n    Cuando la unidad solicitante abre la "
       "solicitud\n    Entonces no lo ve\n" in texto and sin == ["HU-06.1", "HU-06.2"] and "FU-04" not in texto,
       texto + str(sin))
    texto, sin = mg.feature("HU-05")
    ok("Proyecto.feature: el criterio en dos líneas que pasa tal cual, también entero",
       "  Escenario: HU-05.3\n    * La devolución queda en el historial de la solicitud, con su comentario y su fecha.\n"
       in texto and "HU-05.3" in sin, texto + str(sin))
    editar(f, "- `HU-07.1` Solo admite PDF de hasta 30 MB.", "- `HU-07.1` Dado un informe del organismo que no es un PDF "
           "o pesa más de 30 MB, cuando el técnico lo adjunta, entonces no se guarda.")
    editar(f, "- `HU-05.3` La devolución queda en el historial de la solicitud,\n  con su comentario y su fecha.",
           "- `HU-05.3` Dada una solicitud devuelta, cuando alguien de su unidad abre el historial,\n"
           "  entonces ve la devolución con su comentario.")
    c, out = corre(S / "comprobar.py", g, "--anterior", g / "versiones" / "v1.1")
    ok("comprobar.py --anterior: con los dos reescritos, sin aviso",
       c == 0 and any(l.startswith("✓ criterios nuevos o cambiados con dado, cuando y entonces") for l in out.splitlines()),
       out)
    return g


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
