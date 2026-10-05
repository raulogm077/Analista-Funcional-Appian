#!/usr/bin/env python3
"""Prueba automática de la skill del analista. Usa el ejemplo ficticio de ejemplos/autorizaciones/.

  python3 scripts/selftest.py

Comprueba los scripts del análisis (proyecto, índice, comprobación, actualización con informe de
impacto, unión de módulos y lectura de fuentes) y, si están instalados, el Word (Node con docx) y los
diagramas de estados (Playwright). Sale con 1 si algo falla.
"""
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

SKILL = pathlib.Path(__file__).resolve().parents[1]
S = SKILL / "scripts"
EJEMPLO = SKILL / "ejemplos" / "autorizaciones"
fallos = []


def corre(*args, entrada=None):
    r = subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True, input=entrada)
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

        # 3. Proyecto nuevo
        nuevo = tmp / "nuevo"
        c, out = corre(S / "proyecto.py", "iniciar", nuevo, "--nombre", "Prueba", "--cliente", "Ejemplo")
        ok("proyecto.py iniciar crea la carpeta y las plantillas",
           c == 0 and (nuevo / "analisis" / "funcional.md").exists() and (nuevo / "fuentes").is_dir(), out)
        c, out = corre(S / "proyecto.py", "estado", nuevo)
        ok("proyecto.py estado", c == 0 and "versión 0.1" in out, out)

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
        editar(f, "| Título | Qué se quiere hacer, en una línea |", "| Título | Qué se quiere hacer, en una frase |")
        editar(f, "**HU-06 — Redactar el informe técnico**", "**HU-06 — Redactar el informe técnico de la solicitud**")
        c, out = corre(S / "comprobar.py", p, "--anterior", p / "versiones" / "v1.1", "--impacto", informe)
        ok("detecta un cambio que el informe no declara", c == 1 and "cada cambio está declarado" in out and "HU-06" in out, out)

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
        c, out = corre(S / "leer_fuentes.py", entrada, "-o", tmp / "fuentes")
        indice = (tmp / "fuentes" / "indice.md").read_text(encoding="utf-8") if (tmp / "fuentes" / "indice.md").exists() else ""
        ok("leer_fuentes.py cataloga transcripción, texto y Word",
           c == 0 and "Transcripción" in indice and "| Texto |" in indice and "Documento Word" in indice, out + indice)
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

        # 8. Word del DF (opcional)
        if shutil.which("node"):
            r = subprocess.run(["node", str(S / "df_docx.js"), str(EJEMPLO), "-o", str(tmp / "df.docx")],
                               capture_output=True, text=True)
            if r.returncode == 2 and "docx" in r.stderr:
                print("· DF en Word: falta el paquete docx de Node (npm install docx); no se prueba")
            else:
                ok("df_docx.js genera el DF", r.returncode == 0 and (tmp / "df.docx").exists(), r.stdout + r.stderr)
                if (tmp / "df.docx").exists():
                    xml = zipfile.ZipFile(tmp / "df.docx").read("word/document.xml").decode("utf-8").replace("\u2011", "-")
                    ok("el DF no enseña fuentes, anuladas ni respondidas",
                       "FU-0" not in xml and "HU-11" not in xml and "PC-03" not in xml and "PC-01" in xml
                       and "indice.py" not in xml and "Analista, 2026" not in xml)
        else:
            print("· DF en Word: no hay Node.js; no se prueba")

        # 9. Diagramas de estados (opcional)
        c, out = corre(S / "render_mermaid.py", "--check", SKILL / "assets" / "prueba.mmd")
        if c == 2:
            print("· Diagramas: falta Playwright o un navegador; no se prueba")
        else:
            ok("render_mermaid.py valida un diagrama", c == 0, out)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("\nTodo correcto." if not fallos else f"\n{len(fallos)} pruebas fallan: {', '.join(fallos)}")
    return 1 if fallos else 0


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
