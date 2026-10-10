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

        # 3b. proyecto.py estado: cliente y marca; el DF enviado se informa (R2); --confirmadas sin las PAN de un cambio
        # aprobado en la versión vigente (R4); entregar escribe «DF entregado» (T2)
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
            "## Puntos\n" + cab + "| 1 | CAMBIA | Sin descarga [FU-04 00:01:00] | PAN-01 | PAN-01 sin descarga | — | Sí (🔒) | ✔ |\n"
            "| 2 | CAMBIA | Otro orden [FU-04 00:02:00] | PAN-02 | PAN-02 con otro orden | — | Sí (🔒) | Pendiente |\n",
            encoding="utf-8")
        (e / "impacto" / "FU-03.md").write_text(
            "# Impacto de FU-03\nAnálisis base: versión 0.9 · Estado: aplicado en 1.0\n\n"
            "## Puntos\n" + cab + "| 1 | CAMBIA | Filtro [FU-03 00:01:00] | PAN-03 | PAN-03 con filtro | — | Sí (🔒) | ✔ |\n",
            encoding="utf-8")
        c, out = corre(S / "proyecto.py", "estado", e)
        conf = next((l for l in out.splitlines() if "--confirmadas" in l), "")
        ok("proyecto.py estado: la marca del prototipo y --confirmadas sin la PAN de un cambio aprobado en la versión vigente",
           c == 0 and "Marca: prototipo/brand-ejemplo.json" in out and conf.endswith("--confirmadas PAN-02,PAN-03"), out)
        c, out = corre(S / "proyecto.py", "entregar", e)
        hoy = __import__("datetime").date.today().isoformat()
        pm = (e / "proyecto.md").read_text(encoding="utf-8")
        ok("proyecto.py entregar escribe «DF entregado: <versión> · <fecha>» en proyecto.md",
           c == 0 and f"DF entregado: 1.1 · {hoy} · Estado: en validación" in pm, out + pm)
        c, out = corre(S / "proyecto.py", "estado", e)
        ok("proyecto.py estado tras entregar: el último enviado es la versión actual",
           c == 0 and f"último enviado 1.1 ({hoy}), versión actual 1.1" in out, out)
        c, out = corre(S / "proyecto.py", "entregar", e, "--cambio", "EV-02")
        ok("proyecto.py entregar --cambio todavía no está: sale con error y no toca proyecto.md",
           c != 0 and (e / "proyecto.md").read_text(encoding="utf-8") == pm, out)

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

        # 4-R2. La versión sube solo si se aplica algún cambio: sin cambios y subida, error; con cambios y sin subir, error.
        # Un informe sin nada que aplicar («Estado: sin cambios») se comprueba sin --anterior
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
        ok("R2: sin ningún cambio, subir la versión es error", c == 1 and any(
            l.startswith("✗") and "sin cambios" in l and "1.2" in l for l in out.splitlines()), out)
        for x in (r2 / "analisis" / "funcional.md", r2 / "analisis" / "tecnico.md"):
            editar(x, "Versión: 1.2", "Versión: 1.1")
        editar(r2 / "analisis" / "decisiones.md", "\n| 1.2 | 2026-10-02 | Nada | FU-05 | — |", "")
        editar(r2 / "analisis" / "funcional.md", "| Descargar | Descargar la lista filtrada en Excel |",
               "| Descargar | Descargar la lista filtrada en CSV |")
        c, out = corre(S / "comprobar.py", r2, "--anterior", r2 / "versiones" / "v1.1")
        ok("R2: con un cambio, no subir la versión es error",
           c == 1 and any(l.startswith("✗ la versión sube") for l in out.splitlines()), out)
        shutil.rmtree(r2)
        shutil.copytree(EJEMPLO, r2)
        (r2 / "impacto").mkdir()
        sin = ("# Impacto de FU-05\nAnálisis base: versión {v} · Estado: sin cambios\n\n## Puntos\n"
               "| # | Tipo | Qué se dice | Encaja en | Cambio propuesto | Revisar también | Requiere | Decisión |\n"
               "|---|---|---|---|---|---|---|---|\n| 1 | SIN IMPACTO | Repite lo de la lista [FU-05 00:01:00] | PAN-01 | — | — "
               "| — | ✔ |\n{extra}")
        (r2 / "impacto" / "FU-05.md").write_text(sin.format(v="1.1", extra=""), encoding="utf-8")
        c, out = corre(S / "comprobar.py", r2, "--impacto", r2 / "impacto" / "FU-05.md")
        ok("R2: un informe «sin cambios» pasa sin --anterior", c == 0 and "sin cambios" in out, out)
        (r2 / "impacto" / "FU-05.md").write_text(sin.format(v="1.1", extra="| 2 | PREGUNTA | Quién firma [FU-05 00:02:00] "
                                                            "| — | PC-04 nuevo | — | — | ✔ |\n"), encoding="utf-8")
        c, out = corre(S / "comprobar.py", r2, "--impacto", r2 / "impacto" / "FU-05.md")
        ok("R2: «sin cambios» con un punto por aplicar es error", c == 1 and any(
            l.startswith("✗") and "sin cambios" in l and "punto 2" in l for l in out.splitlines()), out)
        (r2 / "impacto" / "FU-05.md").write_text(sin.format(v="1.0", extra=""), encoding="utf-8")
        c, out = corre(S / "comprobar.py", r2, "--impacto", r2 / "impacto" / "FU-05.md")
        ok("R2: «sin cambios» y la versión ha subido desde el análisis base es error", c == 1 and any(
            l.startswith("✗") and "sin cambios" in l and "1.0" in l for l in out.splitlines()), out)

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
               "- `INT-02.2` Si el registro no responde, la solicitud se envía igual.\n")
        editar(intp / "analisis" / "tecnico.md", "| INT-01 Directorio |",
               "| INT-02 Registro | Integración REST con la clave del organismo; reintento al revisar | Se envía igual |\n"
               "| INT-01 Directorio |")
        try:
            m_int = modelo.cargar(intp)
            ok("modelo: la ficha INT-02 y sus criterios INT-02.1 y INT-02.2; INT-01 sigue siendo fila",
               m_int.piezas["INT-02"].forma == "ficha" and m_int.piezas["INT-02"].hijos == ["INT-02.1", "INT-02.2"]
               and m_int.piezas["INT-02.1"].tipo == "CA" and m_int.piezas["INT-01"].forma == "fila"
               and not m_int.fuera_de_casa, str(m_int.fuera_de_casa))
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
           c == 0 and "✓ as-is: cada historia con «Origen»" in out, out)
        ok("evolutivo: «Existe» con un objeto de otra aplicación no es error",
           not [l for l in out.splitlines() if l.startswith("✗") and "UTL_DiasLaborables" in l], out)
        rotas = [  # (qué se rompe, fichero, texto, cambio, comprobación que falla, lo que cita)
            ("historia sin «Origen»", "funcional", "| Deseable | Nueva |", "| Deseable | — |", "«Origen»", "HU-03"),
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
                # El Word entregado no se pisa; el que no se ha entregado se reemplaza avisando
                (w / "entregables").mkdir(exist_ok=True)
                destino = w / "entregables" / "DF-Solicitudes-de-autorizacion-v1.1.docx"
                destino.write_bytes(b"el que se envio")
                r = subprocess.run(["node", str(S / "df_docx.js"), str(w)], capture_output=True, text=True,
                                   encoding="utf-8", errors="replace")
                ok("un Word de una versión no entregada se reemplaza, avisando",
                   r.returncode == 0 and "se reemplaza" in r.stdout and destino.read_bytes() != b"el que se envio",
                   r.stdout + r.stderr)
                editar(w / "proyecto.md", "DF entregado: 1.0 (2026-09-12)", "DF entregado: 1.1 · 2026-10-01")
                destino.write_bytes(b"el que se envio")
                r = subprocess.run(["node", str(S / "df_docx.js"), str(w)], capture_output=True, text=True,
                                   encoding="utf-8", errors="replace")
                ok("el Word de la versión entregada no se sobrescribe: sale con error y no lo toca",
                   r.returncode == 1 and "ya se entregó" in r.stderr and destino.read_bytes() == b"el que se envio",
                   r.stdout + r.stderr)
                # --pdf: LibreOffice en un HOME temporal que se borra y el PDF en <p>/entregables/revision/
                if shutil.which("soffice"):
                    temporal = tmp / "temporal de soffice"
                    temporal.mkdir()
                    editar(w / "proyecto.md", "DF entregado: 1.1 · 2026-10-01", "DF entregado: 1.0 · 2026-09-12")
                    r = subprocess.run(["node", str(S / "df_docx.js"), str(w), "--pdf"], capture_output=True, text=True,
                                       encoding="utf-8", errors="replace", env={**os.environ, "TMPDIR": str(temporal)})
                    pdf = w / "entregables" / "revision" / "DF-Solicitudes-de-autorizacion-v1.1.pdf"
                    ok("df_docx.js --pdf: el PDF en entregables/revision/ y el HOME temporal borrado",
                       r.returncode == 0 and pdf.is_file() and pdf.read_bytes()[:4] == b"%PDF"
                       and not [x for x in temporal.iterdir() if x.name != "node-compile-cache"],  # la caché es de Node
                       r.stdout + r.stderr + str(list(temporal.iterdir())))
                    # --pdf-de: un documento cualquiera (el DF del cliente para ver sus diapositivas), sin generar el Word
                    otro = w / "fuentes" / "DF del cliente.docx"
                    otro.parent.mkdir(exist_ok=True)
                    shutil.copy(w / "entregables" / "DF-Solicitudes-de-autorizacion-v1.1.docx", otro)
                    r = subprocess.run(["node", str(S / "df_docx.js"), str(w), "--pdf-de", str(otro)], capture_output=True,
                                       text=True, encoding="utf-8", errors="replace", env={**os.environ, "TMPDIR": str(temporal)})
                    ok("df_docx.js --pdf-de: solo ese PDF, en entregables/revision/",
                       r.returncode == 0 and (w / "entregables" / "revision" / "DF del cliente.pdf").is_file()
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
