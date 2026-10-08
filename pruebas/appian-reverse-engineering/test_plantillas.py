"""Plantillas de ingeniería inversa: empiezan por sus preguntas, cada certeza lleva su evidencia y no aconsejan.

Las tablas y la prosa se leen con las mismas funciones que comprobar_asis.py, para que un documento escrito con las
plantillas pase el comprobador.
"""
from __future__ import annotations

import re
import sys

from conftest import SKILL

sys.path.insert(0, str(SKILL / "scripts"))
import comprobar_asis as ca  # noqa: E402

CARPETA = SKILL / "assets" / "markdown-templates"
PLANTILLAS = sorted(CARPETA.rglob("*.md"))
PREGUNTAS = "> **Responde a:**"
PREGUNTA = re.compile(r"¿[^¿?\n]+\?")
CONSEJO = re.compile(r"(?i)recomendaci|recomienda")    # recomendación, recomendaciones, recomienda, recomiendan
REGISTRO = re.compile(r"<!-- registro:inicio -->.*?<!-- registro:fin -->", re.S)   # lo escribe build_registry.py
ANEXO = re.compile(r"\]\((?:\./|\.\./)anexo/")
PROCESO = "08-procesos-bpmn/pm-template.md"            # se escribe una vez por process model


def rel(p) -> str:
    return p.relative_to(CARPETA).as_posix() if CARPETA in p.parents else p.relative_to(SKILL).as_posix()


def sin_comentarios(texto: str) -> str:
    return re.sub(r"<!--.*?-->", "", texto, flags=re.S)


def fijo(texto: str, relleno: str = "x") -> str:
    """Lo que la plantilla deja escrito tal cual: cada {{marcador}}, también los anidados, pasa a `relleno`. Con un
    relleno distinto por documento, dos documentos solo coinciden en lo que la plantilla no deja rellenar."""
    while True:
        nuevo = re.sub(r"\{\{[^{}]*\}\}", relleno, texto)
        if nuevo == texto:
            return texto
        texto = nuevo


def test_hay_plantillas():
    """LEEME es la entrada a la documentación: no hay un 00 aparte ni nada que lo enlace."""
    assert {"LEEME.md", "INVENTARIO.md", PROCESO} <= {rel(p) for p in PLANTILLAS}
    assert not any(rel(p).startswith("00") or "00-resumen" in p.read_text(encoding="utf-8") for p in PLANTILLAS)


def secciones(texto: str) -> list[str]:
    return [l[3:].strip() for _, l in ca.lineas(texto) if l.startswith("## ")]


def test_leeme_es_la_entrada():
    """En este orden: las preguntas, el TL;DR con el volumen, los datos de la extracción, lo que era el resumen
    ejecutivo y la guía. Sin la tabla de preguntas por documento ni otra «Cobertura y límites»."""
    texto = (CARPETA / "LEEME.md").read_text(encoding="utf-8")
    lineas = [l.strip() for l in sin_comentarios(texto).splitlines() if l.strip()]
    assert lineas[1].startswith(PREGUNTAS)
    assert lineas[2].startswith("> **TL;DR**") and lineas[3].startswith("> **Volumen**"), lineas[2:4]
    datos = lineas[4:lineas.index(next(l for l in lineas if l.startswith("## ")))]
    assert [ca.celdas(l)[0] for l in datos[2:]] == ["Entorno", "Versión de Appian", "Extracción",
                                                   "Confianza de la documentación"], datos
    assert secciones(texto) == ["La aplicación en cifras", "Procesos críticos", "Hallazgos principales", "Uso real",
                                "Preguntas de esta revisión", "Por dónde empezar", "Cómo leer", "Sin verificar",
                                "Qué no incluye", "Términos de Appian"]
    sin_verificar = texto.split("## Sin verificar", 1)[1].split("\n## ", 1)[0]
    assert "<!-- sin-verificar:inicio -->" in sin_verificar and "<!-- sin-verificar:fin -->" in sin_verificar


def test_que_no_incluye_sin_lineas_fijas():
    """Cada línea de «Qué no incluye» se escribe solo si es verdad en esa extracción: ninguna va fija."""
    seccion = (CARPETA / "LEEME.md").read_text(encoding="utf-8").split("## Qué no incluye", 1)[1].split("\n## ", 1)[0]
    lineas = [l for _, l in ca.lineas(seccion) if l.strip()]
    assert lineas and all(l.startswith("- {{") and l.rstrip().endswith("}}") for l in lineas), lineas


def test_documentacion_de_appian_en_latest():
    """Lo que acaba en un entregable enlaza la documentación de Appian en la forma /latest/ («Dudas de Appian»)."""
    versiones = [f"{rel(p)}:{n} {m.group(0)}" for p in PLANTILLAS
                 for n, l in enumerate(p.read_text(encoding="utf-8").splitlines(), 1)
                 for m in re.finditer(r"docs\.appian\.com/suite/help/(?!latest/)[^/\s]+/", l)]
    assert versiones == []


def test_cada_plantilla_empieza_por_sus_preguntas():
    """Tras el título, la línea «Responde a» con 2 a 5 preguntas fijas, que el documento copia tal cual."""
    malas = []
    for p in PLANTILLAS:
        lineas = [l.strip() for l in sin_comentarios(p.read_text(encoding="utf-8")).splitlines() if l.strip()]
        titulo, linea = (lineas + ["", ""])[:2]
        preguntas = PREGUNTA.findall(linea)
        resto = PREGUNTA.sub("", linea[len(PREGUNTAS):]) if linea.startswith(PREGUNTAS) else linea
        if not (titulo.startswith("# ") and linea.startswith(PREGUNTAS) and 2 <= len(preguntas) <= 5 and not resto.strip()):
            malas.append(f"{rel(p)}: «{linea[:90]}» ({len(preguntas)} preguntas)")
    assert malas == []


def test_toda_tabla_con_certeza_tiene_evidencia():
    """Una tabla con «Certeza» lleva «Evidencia» y cada fila enlaza al anexo (salvo el registro de 09)."""
    malas = []
    for p in PLANTILLAS:
        texto = REGISTRO.sub("", p.read_text(encoding="utf-8"))
        for n, cabecera, filas in ca.tablas(ca.lineas(texto)):
            cols = [c.replace("*", "").lower() for c in cabecera]
            if not any(c.startswith("certeza") for c in cols):
                continue
            evid = next((k for k, c in enumerate(cols) if c.startswith("evidencia")), None)
            if evid is None:
                malas.append(f"{rel(p)}:{n} tabla con «Certeza» sin «Evidencia»")
                continue
            malas += [f"{rel(p)}:{fn} la evidencia no enlaza al anexo" for fn, fila in filas
                      if evid >= len(fila) or not ANEXO.search(fila[evid])]
    assert malas == []


def test_sin_recomendaciones():
    """Ingeniería inversa documenta hechos: qué hacer lo propone refactorización."""
    ficheros = PLANTILLAS + sorted((SKILL / "agents").glob("*.md")) + sorted((SKILL / "references").glob("*.md"))
    malas = [f"{rel(p)}:{n}" for p in ficheros
             for n, l in enumerate(p.read_text(encoding="utf-8").splitlines(), 1) if CONSEJO.search(l)]
    assert malas == []


def test_texto_fijo_sin_avisos():
    """Lo que las plantillas dejan escrito no da avisos de comprobar_asis.py: muletillas, frases de más de
    35 palabras, negativos sin decir dónde se buscó («no existe») ni párrafos repetidos entre documentos (el de cada
    proceso se compara también consigo mismo)."""
    rd = ca.rd
    assert rd is not None, "falta appian-functional-analyst/scripts/redaccion.py"
    muletillas = rd.muletillas()
    textos, avisos = {}, []
    for i, p in enumerate(PLANTILLAS):
        texto = fijo(p.read_text(encoding="utf-8"), f"x{i}")
        textos[rel(p)] = sin_comentarios(texto)
        for n, l in ca.lineas(texto):
            if l.lstrip().startswith("#"):
                continue
            leida = ca.prosa(l)
            normal = rd.normaliza(leida)
            avisos += [f"{rel(p)}:{n} muletilla «{x}»" for x in muletillas
                       if re.search(rf"(?<!\w){re.escape(x)}(?!\w)", normal)]
            avisos += [f"{rel(p)}:{n} «{m.group(0)}»" for m in ca.NEGATIVO.finditer(leida)]
            for trozo in ca.celdas(leida) if l.lstrip().startswith("|") else [leida]:
                for frase in rd.frases(trozo):
                    k = len(re.findall(r"\w+", frase))
                    if k > rd.MAX_PALABRAS:
                        avisos.append(f"{rel(p)}:{n} frase de {k} palabras")
    textos["otro proceso"] = sin_comentarios(fijo((CARPETA / PROCESO).read_text(encoding="utf-8"), "otro"))
    avisos += [f"párrafo repetido en {' y '.join(n)}: «{par[:60]}…»" for par, n in rd.parrafos_repetidos(textos)]
    assert avisos == []


def test_por_entorno_separa_marca_y_dependencia():
    """09: que el valor dependa del entorno y que la constante tenga la marca «Environment Specific» son dos columnas
    (con una sola, un lector concluía que una URL de preproducción sin la marca no cambia por entorno)."""
    texto = sin_comentarios((CARPETA / "09-valor-adicional.md").read_text(encoding="utf-8"))
    tabla = next(cab for _, cab, _ in ca.tablas(ca.lineas(texto)) if "Valor en este entorno" in cab)
    assert "Depende del entorno" in tabla and "Marca de entorno" in tabla and "Por entorno" not in tabla, tabla
    assert len(tabla) <= 8
    guia = (SKILL / "references" / "analysis-workflow.md").read_text(encoding="utf-8")
    assert "«Depende del entorno»" in guia and "«Marca de entorno»" in guia and "«Por entorno»" not in guia
