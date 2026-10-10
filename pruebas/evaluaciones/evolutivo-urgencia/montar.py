#!/usr/bin/env python3
"""Monta el proyecto de partida de las evaluaciones «evolutivo con urgencia» y «coste de un retoque».

Uso:
  python3 montar.py <destino> [--fuente <fichero nuevo>]

<destino> es la carpeta del proyecto, fuera del repositorio ($PROYECTOS_PRUEBA/DEM-urgencia); si existe, tiene que estar
vacía. El proyecto es la aplicación ficticia «Solicitudes de material» (`DEM Gestión de Solicitudes`), nueva y hecha
desde reuniones (caso C, sin as-is/): EV-01, la construcción inicial, en producción, y EV-02, la firma de la revisión,
aprobada y sin construir.

  1. Copia datos/: el análisis 1.1, analisis/cambios.md (EV-01 en producción, EV-02 Abierta), el informe de EV-02
     (impacto/FU-03.md), la copia de la 1.0 en versiones/ y proyecto.md.
  2. Cataloga fuentes/ en su orden con leer_fuentes.py del plugin: FU-01 a FU-04.
  3. Escribe las capturas de las tres pantallas (prototipo/capturas/) y, con Node y el paquete docx, los dos Word
     entregados: el DF 1.0 y el DF del cambio EV-02 (1.1). Sin ellos, avisa y sigue sin Word.
  4. Aprueba EV-02 con la orden de verdad (proyecto.py cambio … EV-02 aprobada --fuente FU-04), que guarda con qué se
     aprueba, y escribe su encargo (indice.py encargo): construccion/EV-02.md y EV-02-esperado.json.
  5. Deja la fuente nueva en <destino>/: por defecto, el correo de la incidencia (correo-2026-10-08-incidencia.eml);
     la prueba de coste pasa el suyo con --fuente.
  6. Comprueba que el análisis pasa comprobar.py y escribe la huella de cada fichero (sha256) en
     <destino>.montaje.json, junto a la carpeta y fuera del proyecto: con ella, puntuar.py sabe si se ha regenerado
     algún documento.

El plugin es el de PLUGIN_A_PROBAR o, si no está, el de este repositorio. Sale 0 si todo va bien y 1 si algo falla.
Los puntuadores de las dos evaluaciones toman de aquí la huella, los documentos regenerados, las fuentes nuevas y
comprobar.py.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path

sys.dont_write_bytecode = True
AQUI = Path(__file__).resolve().parent
PLUGIN = Path(os.environ.get("PLUGIN_A_PROBAR") or AQUI.parents[2]).resolve()
ANALISTA = PLUGIN / "skills" / "appian-functional-analyst" / "scripts"
DATOS = AQUI / "datos"
FUENTES = sorted((AQUI / "fuentes").glob("0*"))
INCIDENCIA = AQUI / "correo-2026-10-08-incidencia.eml"
APROBACION = "FU-04"     # la aprobación de EV-02 por el jefe de proyecto (fuentes/04-aprobacion-2026-10-05.txt)
ENTORNO = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
WORD_10 = "DF-Solicitudes-de-material-v1.0.docx"

# Capturas: un esquema de cada pantalla (cabecera del site y bloques), sin texto; siempre los mismos bytes
AZUL, GRIS, CLARO, BORDE, VERDE, AMARILLO = (33, 62, 107), (210, 214, 220), (240, 242, 245), (190, 196, 204), \
    (46, 125, 50), (255, 244, 204)
CABECERA = [(0, 0, 720, 48, AZUL)]
PANTALLAS = {
    "PAN-01": ("Panel de solicitudes", CABECERA + [(24, 72, 200, 32, GRIS), (240, 72, 240, 32, GRIS),
                                                   (560, 72, 136, 32, VERDE), (24, 124, 672, 28, BORDE)]
               + [(24, 152 + 28 * k, 672, 27, CLARO if k % 2 else (255, 255, 255)) for k in range(8)]),
    "PAN-02": ("Solicitud", CABECERA + [(24, 72, 672, 40, AMARILLO)]
               + [r for k in range(3) for r in ((24, 132 + 72 * k, 120, 10, GRIS), (24, 148 + 72 * k, 672, 34, CLARO))]
               + [(424, 392, 128, 34, GRIS), (568, 392, 128, 34, VERDE)]),
    "PAN-03": ("Revisar solicitud", CABECERA + [(24, 72, 672, 136, CLARO), (24, 224, 320, 40, AMARILLO)]
               + [(24 + 160 * k, 392, 144, 34, VERDE if k == 0 else GRIS) for k in range(3)]),
}


def corre(*orden, cwd=None) -> subprocess.CompletedProcess:
    return subprocess.run([str(x) for x in orden], capture_output=True, text=True, encoding="utf-8", errors="replace",
                          env=ENTORNO, cwd=cwd)


def png(ruta: Path, rects, ancho=720, alto=450):
    """Un PNG RGB de ancho x alto en blanco con esos rectángulos (x, y, ancho, alto, color)."""
    filas = [bytearray(b"\xff" * 3 * ancho) for _ in range(alto)]
    for x, y, w, h, color in rects:
        fin = min(x + w, ancho)
        for yy in range(y, min(y + h, alto)):
            filas[yy][3 * x:3 * fin] = bytes(color) * (fin - x)
    crudo = b"".join(b"\x00" + bytes(f) for f in filas)

    def trozo(tipo, datos):
        return struct.pack(">I", len(datos)) + tipo + datos + struct.pack(">I", zlib.crc32(tipo + datos) & 0xFFFFFFFF)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_bytes(b"\x89PNG\r\n\x1a\n" + trozo(b"IHDR", struct.pack(">IIBBBBB", ancho, alto, 8, 2, 0, 0, 0))
                     + trozo(b"IDAT", zlib.compress(crudo, 9)) + trozo(b"IEND", b""))


def capturas(carpeta: Path):
    filas = []
    for pan, (pie, rects) in PANTALLAS.items():
        png(carpeta / f"{pan}.png", rects)
        filas.append(f"| {pan}.png | {pie} | {pan} | `![{pan} {pie}](../prototipo/capturas/{pan}.png)` |")
    (carpeta / "indice.md").write_text("# Capturas del prototipo\n\n| Fichero | Pie | Ficha | Línea para la ficha |\n"
                                       "|---|---|---|---|\n" + "\n".join(filas) + "\n", encoding="utf-8")


def words(p: Path) -> str:
    """Los dos Word entregados: el DF 1.0 (desde versiones/v1.0) y el DF del cambio EV-02. «» si están; si no, por qué."""
    if not shutil.which("node"):
        return "sin Node"
    script = ANALISTA / "df_docx.js"
    with tempfile.TemporaryDirectory(prefix="df 1.0 ") as t:
        t = Path(t)
        shutil.copytree(p / "versiones" / "v1.0", t / "analisis")
        shutil.copytree(p / "prototipo", t / "prototipo")
        shutil.copy2(p / "proyecto.md", t / "proyecto.md")
        r = corre("node", script, t, "-o", p / "entregables" / WORD_10)
    if r.returncode == 2 and "docx" in (r.stdout + r.stderr):
        return "sin el paquete docx de Node"
    if r.returncode:
        raise SystemExit(f"df_docx.js no genera el DF 1.0:\n{r.stdout}{r.stderr}")
    r = corre("node", script, p, "--cambio", "EV-02")
    if r.returncode:
        raise SystemExit(f"df_docx.js no genera el DF del cambio EV-02:\n{r.stdout}{r.stderr}")
    return ""


def huellas(p: Path) -> dict:
    """{ruta relativa: sha256} de cada fichero del proyecto."""
    return {f.relative_to(p).as_posix(): hashlib.sha256(f.read_bytes()).hexdigest()
            for f in sorted(p.rglob("*")) if f.is_file()}


def montaje_de(p: Path) -> Path:
    """La huella del montaje: <p>.montaje.json, junto a la carpeta del proyecto."""
    p = Path(p).resolve()
    return p.parent / f"{p.name}.montaje.json"


# ---------------------------------------------------------------- lo que usan los puntuadores de las dos evaluaciones
DOCUMENTOS = (".docx", ".pdf", ".png")      # el Word, su PDF y las capturas: se regeneran solo al enviar o al construir


def lee_huella(p: Path, montaje: str | None = None) -> dict | None:
    """{ruta relativa: sha256} del proyecto al montarlo (montaje o <p>.montaje.json), o None si no está."""
    f = Path(montaje) if montaje else montaje_de(p)
    return json.loads(f.read_text(encoding="utf-8"))["ficheros"] if f.is_file() else None


def regenerados(p: Path, inicio: dict) -> list[str]:
    """Los .docx, .pdf y .png del proyecto (salvo fuentes/) que no estaban al montarlo o han cambiado."""
    out = []
    for rel, sha in huellas(p).items():
        if Path(rel).suffix.lower() in DOCUMENTOS and not rel.startswith("fuentes/") and inicio.get(rel) != sha:
            out.append(rel + ("" if rel in inicio else " (nuevo)"))
    return out


def fuentes_nuevas(p: Path, inicio: dict) -> list[dict]:
    """Las fuentes de fuentes/indice.json catalogadas después del montaje: {id, fichero, …}."""
    indice = p / "fuentes" / "indice.json"
    if not indice.is_file():
        return []
    de_antes = {rel.split("/")[1][:5] for rel in inicio if rel.startswith("fuentes/FU-")}
    return [f for f in json.loads(indice.read_text(encoding="utf-8")).get("fuentes", []) if f.get("id") not in de_antes]


def comprobar(p: Path) -> tuple[bool, list[str]]:
    """comprobar.py del analista sobre el proyecto (con --fuentes si las tiene): (sin errores, líneas de error)."""
    orden = [sys.executable, ANALISTA / "comprobar.py", p]
    if (p / "fuentes").is_dir():
        orden += ["--fuentes", p / "fuentes"]
    r = corre(*orden)
    return r.returncode == 0, [l for l in r.stdout.splitlines() if l.startswith("✗")] or r.stderr.strip().splitlines()[-3:]


def montar(destino: Path, fuente: Path | None = INCIDENCIA) -> Path:
    """Monta el proyecto en destino y devuelve la ruta de su huella. Sale (SystemExit) si algo falla."""
    destino = Path(destino).resolve()
    if destino.exists() and any(destino.iterdir()):
        raise SystemExit(f"{destino} ya tiene contenido: monta el proyecto en una carpeta nueva")
    shutil.copytree(DATOS, destino, dirs_exist_ok=True)
    r = corre(sys.executable, ANALISTA / "leer_fuentes.py", *FUENTES, "-o", destino / "fuentes")
    if r.returncode:
        raise SystemExit(f"leer_fuentes.py falla:\n{r.stdout}{r.stderr}")
    capturas(destino / "prototipo" / "capturas")
    sin_word = words(destino)
    # EV-02 se aprueba con la orden de verdad: guarda con qué se aprueba (<!-- … · aprobada 1.1: FU-03 -->), y una
    # fuente nueva para ella después la devuelve a aprobación
    r = corre(sys.executable, ANALISTA / "proyecto.py", "cambio", destino, "EV-02", "aprobada", "--fuente", APROBACION)
    if r.returncode:
        raise SystemExit(f"proyecto.py cambio EV-02 aprobada falla:\n{r.stdout}{r.stderr}")
    r = corre(sys.executable, ANALISTA / "indice.py", "encargo", destino, "EV-02")
    if r.returncode:
        raise SystemExit(f"indice.py encargo falla:\n{r.stdout}{r.stderr}")
    if fuente is not None:
        shutil.copy2(fuente, destino / Path(fuente).name)
    r = corre(sys.executable, ANALISTA / "comprobar.py", destino, "--fuentes", destino / "fuentes")
    if r.returncode:
        raise SystemExit(f"El proyecto de partida no pasa comprobar.py:\n{r.stdout}{r.stderr}")
    huella = montaje_de(destino)
    huella.write_text(json.dumps({"proyecto": destino.name, "plugin": str(PLUGIN), "word": not sin_word,
                                  "ficheros": huellas(destino)}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"Proyecto montado en {destino}")
    print(f"  fuentes: FU-01 a FU-{len(FUENTES):02d}; fuente nueva: {Path(fuente).name if fuente else '—'}")
    print("  Word: " + (f"no ({sin_word}): el proyecto no tiene los Word entregados" if sin_word else
                        f"{WORD_10} y DF-Solicitudes-de-material-EV-02-v1.1.docx"))
    print(f"  comprobar.py: sin errores · huella: {huella}")
    return huella


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("destino")
    ap.add_argument("--fuente", default=str(INCIDENCIA), help="la fuente nueva que se deja en el proyecto")
    a = ap.parse_args()
    for s in (sys.stdout, sys.stderr):
        s.reconfigure(encoding="utf-8", errors="replace")
    try:
        montar(Path(a.destino), Path(a.fuente))
    except SystemExit as e:
        print(e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
