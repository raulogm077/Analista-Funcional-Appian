#!/usr/bin/env python3
"""PDF real: imágenes, índice y editables portables. Sólo el job PDF, con LibreOffice y Poppler.

Ejecutar: python3 -B pruebas/appian-functional-analyst/test_pdf_libreoffice.py
pypdf se utiliza sólo para inspeccionar los artefactos de esta prueba, no en el plugin.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET
import zlib

sys.dont_write_bytecode = True


def _obj(value):
    return value.get_object() if hasattr(value, "get_object") else value


def _fichero(value):
    value = _obj(value)
    return str(value.get("/UF", value.get("/F", ""))) if isinstance(value, dict) else str(value or "")


def verificar_pdf(pdf, proyecto, dimensiones, titulos):
    """Devuelve defectos observables del PDF final; también sirve sobre una conversión ya existente."""
    from pypdf import PdfReader

    pdf, proyecto = Path(pdf), Path(proyecto).resolve()
    reader = PdfReader(pdf)
    errores, medidas, externos = [], [], []
    textos = [p.extract_text() or "" for p in reader.pages]
    paginas_indice = [i for i, texto in enumerate(textos) if re.search(r"(?m)^\s*Índice\s*$", texto)]
    for pagina in reader.pages:
        recursos = _obj(pagina.get("/Resources", {}))
        for referencia in _obj(recursos.get("/XObject", {})).values():
            imagen = _obj(referencia)
            if imagen.get("/Subtype") == "/Image":
                medidas.append((int(imagen["/Width"]), int(imagen["/Height"])))
        for ref in pagina.get("/Annots", []):
            anotacion = _obj(ref)
            if anotacion.get("/Subtype") != "/Link":
                continue
            accion = _obj(anotacion.get("/A", {}))
            tipo = accion.get("/S")
            if tipo == "/URI":
                externos.append(str(accion.get("/URI", "")))
            elif tipo in ("/Launch", "/GoToR"):
                externos.append(_fichero(accion.get("/F", "")))

    for medida in dimensiones:
        if tuple(medida) not in medidas:
            errores.append(f"imagen sin sus píxeles originales {tuple(medida)}; PDF: {medidas}")
    esperados = {p.resolve() for p in (proyecto / "analisis" / "diagramas").glob("*.drawio")}
    encontrados = []
    for enlace in externos:
        uri = urlsplit(enlace)
        if not unquote(uri.path).lower().endswith(".drawio"):
            continue
        ruta = Path(unquote(uri.path))
        destino = (pdf.parent / ruta).resolve()
        encontrados.append(destino)
        if uri.scheme or uri.netloc or uri.fragment or ruta.is_absolute():
            errores.append(f"editable no portable desde el PDF final: {enlace}")
        if destino not in esperados or not destino.is_file():
            errores.append(f"editable no resuelto desde {pdf.parent}: {enlace} -> {destino}")
    if len(encontrados) != 3 or set(encontrados) != esperados:
        errores.append(f"se esperaban los tres enlaces a editables; encontrados: {encontrados}")

    if not paginas_indice:
        errores.append("no se encuentra la página del índice")
    # Poppler asocia el texto visible de CADA entrada con su acción real; no basta un conjunto de destinos.
    extraccion = subprocess.run(["pdftohtml", "-xml", "-i", "-stdout", str(pdf)], capture_output=True,
                                text=True, encoding="utf-8", errors="replace")
    pdf.with_suffix(".enlaces.xml").write_text(extraccion.stdout + extraccion.stderr, encoding="utf-8")
    enlaces_indice = []
    if extraccion.returncode:
        errores.append(f"pdftohtml exit {extraccion.returncode}")
    else:
        xml = ET.fromstring(extraccion.stdout)
        enlaces_indice = [a for p in xml.findall("page") if int(p.get("number")) - 1 in paginas_indice
                          for a in p.findall(".//a")]
    indice = "\n".join(textos[i] for i in paginas_indice)
    for titulo in titulos:
        paginas_titulo = [i for i, texto in enumerate(textos) if i not in paginas_indice
                          and re.search(r"(?m)^\s*" + re.escape(titulo) + r"\s*$", texto)]
        entrada = re.search(re.escape(titulo) + r"[ \t.·]+(\d+)[ \t]*$", indice, re.M)
        if not paginas_titulo or not entrada or int(entrada[1]) - 1 not in paginas_titulo:
            errores.append(f"índice sin número correcto para {titulo!r}; páginas reales: {[i + 1 for i in paginas_titulo]}")
        enlaces = [a for a in enlaces_indice if "".join(a.itertext()).startswith(titulo)]
        if len(enlaces) != 1 or not urlsplit(enlaces[0].get("href", "")).fragment.isdigit() \
                or int(urlsplit(enlaces[0].get("href", "")).fragment) - 1 not in paginas_titulo:
            errores.append(f"entrada del índice sin su destino correcto: {titulo!r}")
    return errores


def _png(ruta, ancho, alto, color):
    # El mismo formato mínimo struct/zlib de imagenes_docx(), con patrón para evitar una figura uniforme.
    def bloque(tipo, datos):
        return struct.pack(">I", len(datos)) + tipo + datos + struct.pack(">I", zlib.crc32(tipo + datos))
    pixeles = b"".join(b"\0" + bytes(v for x in range(ancho) for v in
                                    ((x + color) % 256, (y * 7 + color) % 256, (x // 11 + y) % 256))
                       for y in range(alto))
    ruta.write_bytes(b"\x89PNG\r\n\x1a\n" + bloque(b"IHDR", struct.pack(">IIBBBBB", ancho, alto, 8, 2, 0, 0, 0))
                     + bloque(b"IDAT", zlib.compress(pixeles)) + bloque(b"IEND", b""))


def main():
    raiz = Path(tempfile.mkdtemp(prefix="pdf-diagramas-", dir=os.environ.get("RUNNER_TEMP")))
    print(f"Artefactos: {raiz}", flush=True)
    repo = Path(os.environ.get("PLUGIN_A_PROBAR") or Path(__file__).resolve().parents[2])
    script = repo / "skills/appian-functional-analyst/scripts/df_docx.js"
    proyecto = raiz / "proyecto"
    diagramas = proyecto / "analisis/diagramas"
    diagramas.mkdir(parents=True)
    figuras = (("Proceso revisión #1", 4096, 128), ("Proceso auxiliar", 256, 96), ("Proceso final", 192, 80))
    for i, (nombre, ancho, alto) in enumerate(figuras):
        _png(diagramas / f"{nombre}.png", ancho, alto, i * 41)
        (diagramas / f"{nombre}.drawio").write_text('<mxfile><diagram name="Proceso ficticio"/></mxfile>', encoding="utf-8")
    titulos = ("Anexo A. Proceso ancho", "Anexo B. Proceso auxiliar", "Anexo C. Proceso final")
    md = ["# Prueba de PDF\n\nVersión: 0.1\n"]
    for i, titulo in enumerate(titulos):
        md.append(f"## {titulo}\n\n![Figura ficticia {i + 1}](diagramas/{figuras[i][0]}.png)\n")
        md.append(f"Contenido ficticio del anexo {i + 1}: comprobar su entrada y destino en el índice.\n")
    (proyecto / "analisis/funcional.md").write_text("\n".join(md), encoding="utf-8")
    fuentes = {p.relative_to(proyecto): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in (proyecto / "analisis").rglob("*") if p.is_file()}
    errores, resultados, pdfs, docx_hashes = [], [], [], {}
    for caso, extra in (("normal", []), ("salida-extra", ["-o", str(proyecto / "entregables/extra/otro.docx")])):
        r = subprocess.run(["node", str(script), str(proyecto), *extra, *(["--pdf"] if extra else [])], capture_output=True,
                           text=True, encoding="utf-8", errors="replace")
        if not extra and not r.returncode:
            (raiz / "normal-generar-docx.log").write_text(r.stdout + r.stderr, encoding="utf-8")
            fuente_docx = next((proyecto / "entregables").glob("*.docx"))
            docx_hashes["antes"] = hashlib.sha256(fuente_docx.read_bytes()).hexdigest()
            r = subprocess.run(["node", str(script), str(proyecto), "--pdf-de", str(fuente_docx)], capture_output=True,
                               text=True, encoding="utf-8", errors="replace")
            docx_hashes["despues"] = hashlib.sha256(fuente_docx.read_bytes()).hexdigest()
            if docx_hashes["antes"] != docx_hashes["despues"]:
                errores.append("--pdf-de modificó el DOCX válido de origen")
        (raiz / f"{caso}.log").write_text(r.stdout + r.stderr, encoding="utf-8")
        if r.returncode:
            errores.append(f"{caso}: conversión exit {r.returncode}")
            continue
        docx = proyecto / "entregables/extra/otro.docx" if extra else next((proyecto / "entregables").glob("*.docx"))
        pdf = proyecto / "entregables/revision" / docx.with_suffix(".pdf").name
        if not pdf.is_file():
            errores.append(f"{caso}: falta el PDF final {pdf}")
            continue
        pdfs.append(pdf.relative_to(proyecto))
        for herramienta, opciones in (("pdfimages", ["-list"]), ("pdfinfo", []), ("pdftotext", ["-layout"])):
            args = [herramienta, *opciones, str(pdf)] + (["-"] if herramienta == "pdftotext" else [])
            inspeccion = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
            (raiz / f"{caso}-{herramienta}.txt").write_text(inspeccion.stdout + inspeccion.stderr, encoding="utf-8")
            if inspeccion.returncode:
                errores.append(f"{caso}: {herramienta} exit {inspeccion.returncode}")
        fallos = verificar_pdf(pdf, proyecto, [(w, h) for _, w, h in figuras], titulos)
        resultados.append({"caso": caso, "pdf": str(pdf), "fallos": fallos})
        errores.extend(f"{caso}: {f}" for f in fallos)
    copia = raiz / "proyecto movido"
    shutil.copytree(proyecto, copia)
    for relativo in pdfs:
        fallos = verificar_pdf(copia / relativo, copia, [(w, h) for _, w, h in figuras], titulos)
        resultados.append({"caso": "copia movida", "pdf": str(copia / relativo), "fallos": fallos})
        errores.extend(f"copia movida: {f}" for f in fallos)
    # --pdf-de también admite documentos Writer ajenos al generador y sin índice.
    externo = proyecto / "documento externo.fodt"
    externo.write_text('<?xml version="1.0" encoding="UTF-8"?>'
                       '<office:document xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
                       'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" office:version="1.2" '
                       'office:mimetype="application/vnd.oasis.opendocument.text">'
                       '<office:body><office:text><text:p>Documento externo ficticio sin índice</text:p>'
                       '</office:text></office:body></office:document>', encoding="utf-8")
    hash_externo = hashlib.sha256(externo.read_bytes()).hexdigest()
    r = subprocess.run(["node", str(script), str(proyecto), "--pdf-de", str(externo)], capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    (raiz / "documento-externo.log").write_text(r.stdout + r.stderr, encoding="utf-8")
    pdf_externo = proyecto / "entregables/revision/documento externo.pdf"
    if r.returncode or not pdf_externo.is_file():
        errores.append(f"--pdf-de documento externo sin índice: exit {r.returncode}, PDF presente {pdf_externo.is_file()}")
    else:
        from pypdf import PdfReader
        if "Documento externo ficticio sin índice" not in "\n".join(p.extract_text() or "" for p in PdfReader(pdf_externo).pages):
            errores.append("--pdf-de: falta el texto del documento externo")
    if hashlib.sha256(externo.read_bytes()).hexdigest() != hash_externo:
        errores.append("--pdf-de modificó el documento externo")
    # Un origen inválido con el mismo nombre no debe sustituir un PDF anterior válido.
    if pdfs:
        anterior = proyecto / pdfs[0]
        hash_pdf = hashlib.sha256(anterior.read_bytes()).hexdigest()
        invalido = proyecto / "entrada invalida" / anterior.with_suffix(".docx").name
        invalido.parent.mkdir()
        invalido.write_bytes(b"PK\x03\x04" + bytes(range(256)))
        r = subprocess.run(["node", str(script), str(proyecto), "--pdf-de", str(invalido)], capture_output=True,
                           text=True, encoding="utf-8", errors="replace")
        (raiz / "entrada-invalida.log").write_text(r.stdout + r.stderr, encoding="utf-8")
        if r.returncode == 0 or hashlib.sha256(anterior.read_bytes()).hexdigest() != hash_pdf:
            errores.append("una entrada inválida no falló o sustituyó el PDF anterior")
    if any(hashlib.sha256((proyecto / p).read_bytes()).hexdigest() != h for p, h in fuentes.items()):
        errores.append("las fuentes cambiaron al convertir")
    (raiz / "resultado.json").write_text(json.dumps({"resultados": resultados, "errores": errores,
                                                    "docx_sha256": docx_hashes,
                                                    "fuentes_sha256": {str(p): h for p, h in fuentes.items()}},
                                                   ensure_ascii=False, indent=2), encoding="utf-8")
    for fallo in errores:
        print(f"FAIL {fallo}", flush=True)
    print(f"{'FAIL' if errores else 'PASS'} PDF real, dos salidas, copia movida y documento externo", flush=True)
    return bool(errores)


if __name__ == "__main__":
    sys.exit(main())
