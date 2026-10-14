#!/usr/bin/env python3
"""Prueba de puntuar.py y de las cuatro baterías de peticiones: `python3 prueba_puntuar.py`. Sale 0 si todo va bien.

Las respuestas se hacen a partir de lo esperado: todas bien, una mal, con el prefijo del plugin, una de menos, dos
cambiadas de orden. Las de las fronteras no llevan las palabras que delatan la skill (DELATAN); las de las vecinas, sí
(miden la frontera con skills de fuera del plugin, vecinas.json, que también pueden ser la esperada). No imprime las
peticiones ocultas, las de las fronteras ni las de las vecinas, ni las descripciones."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True
AQUI = Path(__file__).resolve().parent
PUNTUAR = AQUI / "puntuar.py"
REPO = AQUI.parents[2]
PLUGIN = Path(os.environ.get("PLUGIN_A_PROBAR") or REPO).resolve()
VISIBLES = json.loads((REPO / "pruebas" / "enrutado.json").read_text(encoding="utf-8"))
OCULTAS = json.loads((AQUI / "ocultas" / "enrutado.json").read_text(encoding="utf-8"))
FRONTERAS = json.loads((AQUI / "fronteras" / "enrutado.json").read_text(encoding="utf-8"))
VECINAS = json.loads((AQUI / "vecinas" / "enrutado.json").read_text(encoding="utf-8"))
VECINAS_OCULTAS = json.loads((AQUI / "vecinas" / "ocultas.json").read_text(encoding="utf-8"))
DESCRIPCIONES_VECINAS = json.loads((AQUI / "vecinas.json").read_text(encoding="utf-8"))
NOMBRES_VECINAS = sorted(v.get("skill", "") for v in DESCRIPCIONES_VECINAS if isinstance(v, dict))
SKILLS = sorted(md.parent.name for md in (PLUGIN / "skills").glob("*/SKILL.md"))
MINIMO_POR_SKILL = 4
# Lo que resuelve una frontera sin pensar («ya tenemos el as-is», «en draw.io», «las capturas para el DF»): no va en
# las peticiones de fronteras/.
DELATAN = re.compile(r"\bas[- ]is\b|ingenier[ií]a\s+inversa|draw\.?io|bpmn|prototip|maquet|mockup|\bDF\b|\bhistorias\b"
                     r"|refactori|buenas\s+pr[aá]cticas|best\s+practices?|\bcapturas?\b", re.I)
fallos: list[str] = []


def espera(cond: bool, que: str, salida: str = "") -> None:
    if not cond:
        fallos.append(que + (f"\n{salida[-1200:]}" if salida else ""))


def puntua(carpeta: Path, nombre: str, respuestas, *args: str) -> tuple[int, str]:
    ruta = carpeta / nombre
    ruta.write_text(json.dumps(respuestas, ensure_ascii=False, indent=2), encoding="utf-8")
    return corre(str(ruta), *args)


def corre(*args: str) -> tuple[int, str]:
    r = subprocess.run([sys.executable, str(PUNTUAR), *args], capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    return r.returncode, r.stdout + r.stderr


def otra_skill(skill: str) -> str:
    return next(s for s in SKILLS if s != skill)


def baterias() -> None:
    espera(len(SKILLS) == 7, f"hay {len(SKILLS)} skills en skills/, no siete")
    todas = VISIBLES + OCULTAS
    for nombre, lista, validas in (("enrutado.json", VISIBLES, SKILLS), ("ocultas/enrutado.json", OCULTAS, SKILLS),
                                   ("fronteras/enrutado.json", FRONTERAS, SKILLS),
                                   ("vecinas/enrutado.json", VECINAS, SKILLS + NOMBRES_VECINAS),
                                   ("vecinas/ocultas.json", VECINAS_OCULTAS, SKILLS + NOMBRES_VECINAS)):
        malas = [k for k, p in enumerate(lista, 1) if set(p) != {"peticion", "skill"} or p["skill"] not in validas]
        espera(not malas, f"{nombre}: entradas sin {{peticion, skill}} o con una skill que no existe: {malas}")
    espera(len(DESCRIPCIONES_VECINAS) >= 1 and all(
        isinstance(v, dict) and set(v) == {"skill", "descripcion"} and len(v["descripcion"]) > 100
        and v["skill"] not in SKILLS for v in DESCRIPCIONES_VECINAS),
        "vecinas.json: tiene que ser una lista de {\"skill\", \"descripcion\"} de skills que no son del plugin")
    sin_peticion = set(NOMBRES_VECINAS) - {p["skill"] for p in VECINAS}
    espera(not sin_peticion, f"vecinas/enrutado.json: ninguna petición espera {sorted(sin_peticion)}")
    espera(len(VECINAS) >= 10, f"vecinas/enrutado.json tiene {len(VECINAS)} peticiones; al menos 10")
    sin_oculta = set(NOMBRES_VECINAS) - {p["skill"] for p in VECINAS_OCULTAS}
    espera(not sin_oculta and len(VECINAS_OCULTAS) >= 8,
           f"vecinas/ocultas.json: al menos 8 peticiones y alguna para cada vecina (falta {sorted(sin_oculta)})")
    cuenta = Counter(p["skill"] for p in todas)
    pocas = {s: cuenta[s] for s in SKILLS if cuenta[s] < MINIMO_POR_SKILL}
    espera(not pocas, f"menos de {MINIMO_POR_SKILL} peticiones de: {pocas}")
    repetidas = [p for p, n in Counter(p["peticion"].strip() for p in todas + FRONTERAS + VECINAS + VECINAS_OCULTAS)
                 .items() if n > 1]
    espera(not repetidas, f"{len(repetidas)} peticiones repetidas")
    espera(3 * len(OCULTAS) >= len(todas) - 3, f"{len(OCULTAS)} ocultas de {len(todas)}: tendría que ser un tercio")
    espera(len(FRONTERAS) >= 8, f"fronteras/enrutado.json tiene {len(FRONTERAS)} peticiones; al menos 8")
    delatoras = {k: sorted({m.group(0) for m in DELATAN.finditer(p["peticion"])}) for k, p in enumerate(FRONTERAS, 1)}
    delatoras = {k: v for k, v in delatoras.items() if v}
    espera(not delatoras, f"fronteras/enrutado.json: peticiones con palabras que delatan la skill: {delatoras}")


def puntuacion(carpeta: Path) -> None:
    n = len(VISIBLES)
    c, out = puntua(carpeta, "todas bien.json", VISIBLES)
    espera(c == 0 and f"Total: {n}/{n}" in out and "FALLO" not in out, "todas bien no sale 0", out)

    una_mal = [dict(p) for p in VISIBLES]
    una_mal[2]["skill"] = otra_skill(una_mal[2]["skill"])
    c, out = puntua(carpeta, "una mal.json", una_mal)
    espera(c == 1 and f"Total: {n - 1}/{n}" in out and re.search(r"(?m)^FALLO\s+3 esperada", out)
           and out.count("FALLO") == 1, "una mal no sale 1 con su FALLO", out)

    inventada = [dict(p) for p in VISIBLES]
    inventada[0]["skill"] = "appian-sail-generator"
    c, out = puntua(carpeta, "inventada.json", inventada)
    espera(c == 1 and "no es una de las skills" in out, "una skill que no existe no se dice", out)

    con_prefijo = [{"peticion": p["peticion"], "skill": f"appian-analisis-funcional:{p['skill']}"} for p in VISIBLES]
    c, out = puntua(carpeta, "con prefijo.json", con_prefijo)
    espera(c == 0, "la skill con el prefijo del plugin no vale", out)

    espacios = [{"peticion": "  " + p["peticion"].replace(" ", "\n", 1) + " ", "skill": p["skill"]} for p in VISIBLES]
    c, out = puntua(carpeta, "espacios.json", espacios)
    espera(c == 0, "la petición con otros espacios no vale", out)

    c, out = puntua(carpeta, "una de menos.json", VISIBLES[:-1])
    espera(c == 2 and f"{n - 1} respuestas para {n}" in out, "una respuesta de menos no sale 2", out)

    cambiadas = [dict(p) for p in VISIBLES]
    cambiadas[0], cambiadas[1] = cambiadas[1], cambiadas[0]
    c, out = puntua(carpeta, "cambiadas.json", cambiadas)
    espera(c == 2 and "1, 2" in out, "dos respuestas cambiadas de orden no salen 2", out)

    c, out = puntua(carpeta, "no es lista.json", {"respuestas": VISIBLES})
    espera(c == 2, "unas respuestas que no son una lista no salen 2", out)

    c, out = corre(str(carpeta / "no existe.json"))
    espera(c == 2 and "No encuentro" in out, "un fichero que no existe no sale 2", out)

    m = len(OCULTAS)
    c, out = puntua(carpeta, "ocultas bien.json", OCULTAS, "--ocultas")
    espera(c == 0 and f"Total: {m}/{m} (ocultas)" in out, "las ocultas bien no salen 0")
    ocultas_mal = [dict(p) for p in OCULTAS]
    ocultas_mal[-1]["skill"] = otra_skill(ocultas_mal[-1]["skill"])
    c, out = puntua(carpeta, "ocultas mal.json", ocultas_mal, "--ocultas")
    espera(c == 1 and f"Total: {m - 1}/{m}" in out, "una oculta mal no sale 1")

    nf = len(FRONTERAS)
    c, out = puntua(carpeta, "fronteras bien.json", FRONTERAS, "--fronteras")
    espera(c == 0 and f"Total: {nf}/{nf} (fronteras)" in out, "las de las fronteras bien no salen 0")
    fronteras_mal = [dict(p) for p in FRONTERAS]
    fronteras_mal[0]["skill"] = otra_skill(fronteras_mal[0]["skill"])
    c, out = puntua(carpeta, "fronteras mal.json", fronteras_mal, "--fronteras")
    espera(c == 1 and f"Total: {nf - 1}/{nf} (fronteras)" in out and re.search(r"(?m)^FALLO\s+1 esperada", out),
           "una de las fronteras mal no sale 1 con su FALLO")
    c, out = puntua(carpeta, "visibles con fronteras.json", VISIBLES, "--fronteras")
    espera(c == 2, "las respuestas de las visibles puntuadas con --fronteras no salen 2")
    c, out = puntua(carpeta, "ocultas y fronteras.json", FRONTERAS, "--ocultas", "--fronteras")
    espera(c == 2 and "--fronteras" in out, "--ocultas y --fronteras a la vez no salen 2")

    # con --vecinas, las skills de vecinas.json también valen como respuesta (y como esperada)
    nv = len(VECINAS)
    c, out = puntua(carpeta, "vecinas bien.json", VECINAS, "--vecinas")
    espera(c == 0 and f"Total: {nv}/{nv} (vecinas)" in out and "no es una de las skills" not in out,
           "las de las vecinas bien no salen 0", out)
    con_prefijo = [{"peticion": p["peticion"], "skill": f"otro-plugin:{p['skill']}"} for p in VECINAS]
    c, out = puntua(carpeta, "vecinas con prefijo.json", con_prefijo, "--vecinas")
    espera(c == 0, "una vecina con el prefijo de su plugin no vale", out)
    vecina = next(k for k, p in enumerate(VECINAS) if p["skill"] in NOMBRES_VECINAS)
    vecinas_mal = [dict(p) for p in VECINAS]
    vecinas_mal[vecina]["skill"] = SKILLS[0]
    c, out = puntua(carpeta, "vecinas mal.json", vecinas_mal, "--vecinas")
    espera(c == 1 and f"Total: {nv - 1}/{nv} (vecinas)" in out
           and re.search(rf"(?m)^FALLO\s+{vecina + 1} esperada {re.escape(VECINAS[vecina]['skill'])}", out),
           "una de las vecinas mal no sale 1 con su FALLO", out)
    sin_vecinas = [dict(p) for p in VISIBLES]
    sin_vecinas[0]["skill"] = NOMBRES_VECINAS[0]
    c, out = puntua(carpeta, "vecina sin --vecinas.json", sin_vecinas)
    espera(c == 1 and "no es una de las skills" in out, "sin --vecinas, una vecina vale como respuesta", out)
    c, out = puntua(carpeta, "vecinas y fronteras.json", VECINAS, "--vecinas", "--fronteras")
    espera(c == 2, "--vecinas y --fronteras a la vez no salen 2")
    no = len(VECINAS_OCULTAS)
    c, out = puntua(carpeta, "vecinas ocultas bien.json", VECINAS_OCULTAS, "--vecinas-ocultas")
    espera(c == 0 and f"Total: {no}/{no} (vecinas ocultas)" in out and "no es una de las skills" not in out,
           "las vecinas ocultas bien no salen 0")
    c, out = puntua(carpeta, "vecinas ocultas con las visibles.json", VECINAS, "--vecinas-ocultas")
    espera(c == 2, "las respuestas de las vecinas visibles puntuadas con --vecinas-ocultas no salen 2")


def enunciado() -> None:
    for args, lista, nombre in (((), VISIBLES, "visibles"), (("--ocultas",), OCULTAS, "ocultas"),
                                (("--fronteras",), FRONTERAS, "fronteras"), (("--vecinas",), VECINAS, "vecinas"),
                                (("--vecinas-ocultas",), VECINAS_OCULTAS, "vecinas ocultas")):
        c, out = corre("--enunciado", *args)
        espera(c == 0, f"--enunciado con las {nombre} no sale 0")
        lineas = dict(re.findall(r"(?m)^- `([\w-]+)`: (.*)$", out))
        con_vecinas = args in (("--vecinas",), ("--vecinas-ocultas",))
        skills = sorted(SKILLS + (NOMBRES_VECINAS if con_vecinas else []))
        espera(sorted(lineas) == skills, f"--enunciado con las {nombre} no trae {', '.join(skills)}")
        if con_vecinas:
            espera(all(lineas.get(v["skill"]) == v["descripcion"] for v in DESCRIPCIONES_VECINAS),
                   "--enunciado con las vecinas no trae su descripción tal cual")
        espera(all(len(d) > 100 for d in lineas.values()), f"--enunciado con las {nombre}: alguna descripción vacía o "
               "cortada")
        bloque = out.split("## Peticiones", 1)[-1]
        try:
            peticiones = json.loads(bloque)
        except json.JSONDecodeError:
            peticiones = None
        espera(peticiones == [p["peticion"] for p in lista],
               f"--enunciado con las {nombre} no trae sus peticiones en orden como lista JSON")
        espera('"skill"' not in bloque, f"--enunciado con las {nombre} da la skill esperada")
    c, out = corre()
    espera(c == 2, "sin respuestas ni --enunciado no sale 2", out)


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")
    baterias()
    with tempfile.TemporaryDirectory() as tmp:
        carpeta = Path(tmp) / "Carpeta con espacios" / "Gestión app"
        carpeta.mkdir(parents=True)
        puntuacion(carpeta)
    enunciado()
    for f in fallos:
        print("FALLO: " + f)
    print(f"prueba_puntuar.py: {'OK' if not fallos else f'{len(fallos)} fallos'} ({len(VISIBLES)} visibles, "
          f"{len(OCULTAS)} ocultas, {len(FRONTERAS)} de fronteras, {len(VECINAS)} con vecinas y "
          f"{len(VECINAS_OCULTAS)} ocultas con vecinas)")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
