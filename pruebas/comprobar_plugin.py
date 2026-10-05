#!/usr/bin/env python3
"""Comprueba que las skills del plugin encajan entre sí.

    python3 pruebas/comprobar_plugin.py              # comprobaciones estáticas (segundos)
    python3 pruebas/comprobar_plugin.py --completo   # además, la prueba automática de cada skill

Qué mira:
- cada SKILL.md: nombre igual a su carpeta, descripción de 1024 caracteres como mucho y que diga qué no hace;
- que las skills que se citan existan en el plugin (o estén en EXTERNAS);
- que existan los ficheros que cita cada SKILL.md y las rutas de una skill a otra;
- que los servidores MCP que se citan estén en .mcp.json;
- que la regla «Dudas de Appian» esté, igual, en las skills de REGLA_DOCS;
- que no haya frases largas repetidas entre SKILL.md;
- que la versión de plugin.json sea la última del README.
Sale con 1 si hay errores.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
SKILLS = RAIZ / "skills"

# Skills que se citan y no están en el plugin, con el motivo.
EXTERNAS = {
    "appian-reverse-engineering": "skill de ingeniería inversa, se incorporará al plugin",
}
# Nombres que empiezan por appian- y no son skills.
NO_SKILLS = {"appian-docs", "appian-dev", "appian-analisis-funcional"}
# Skills que tienen que llevar la regla de dudas de Appian (appian-best-practices la lleva en *Tools*).
REGLA_DOCS = ["appian-functional-analyst", "appian-prototipos-aena"]
TITULO_REGLA = "## Dudas de Appian"
CARPETAS = ("references", "scripts", "templates", "assets", "schemas", "examples", "runtime")

errores, avisos = [], []


def frontmatter(texto):
    m = re.match(r"^---\n(.*?)\n---\n", texto, re.S)
    if not m:
        return {}
    campos, actual = {}, None
    for linea in m.group(1).splitlines():
        if re.match(r"^[a-z-]+:", linea):
            actual, _, valor = linea.partition(":")
            campos[actual] = valor.strip()
        elif actual:
            campos[actual] += " " + linea.strip()
    for k, v in campos.items():
        v = v.lstrip(">|").strip()
        if len(v) > 1 and v[0] == v[-1] and v[0] in "\"'":
            v = v[1:-1]
        campos[k] = v
    return campos


def seccion(texto, titulo):
    i = texto.find(titulo + "\n")
    if i < 0:
        return None
    resto = texto[i + len(titulo) + 1:]
    fin = re.search(r"^## ", resto, re.M)
    return resto[: fin.start()] if fin else resto


def sin_urls(texto):
    return re.sub(r"https?://\S+", " ", texto)


def main(completo):
    nombres = sorted(p.parent.name for p in SKILLS.glob("*/SKILL.md"))
    textos = {n: (SKILLS / n / "SKILL.md").read_text(encoding="utf-8") for n in nombres}
    servidores = set(json.loads((RAIZ / ".mcp.json").read_text(encoding="utf-8")).get("mcpServers", {}))

    for n, t in textos.items():
        fm = frontmatter(t)
        d = fm.get("description", "")
        if fm.get("name") != n:
            errores.append(f"{n}: el name del SKILL.md es «{fm.get('name')}»")
        if not d:
            errores.append(f"{n}: sin descripción")
        elif len(d) > 1024:
            errores.append(f"{n}: la descripción tiene {len(d)} caracteres (máximo 1024)")
        if "<" in d or ">" in d:
            errores.append(f"{n}: la descripción lleva < o >")
        if d and not re.search(r"(^|[.:;] )(No|Not) ", d):
            errores.append(f"{n}: la descripción no dice qué no hace")

    # Skills citadas
    documentos = [RAIZ / "README.md"] + [SKILLS / n / "SKILL.md" for n in nombres]
    for n in nombres:
        if n != "appian-best-practices":  # sus referencias citan documentación, no skills
            documentos += sorted((SKILLS / n / "references").glob("*.md"))
    for doc in documentos:
        texto = sin_urls(doc.read_text(encoding="utf-8"))
        for m in re.finditer(r"(?<![\w./-])(appian-[a-z0-9]+(?:-[a-z0-9]+)*)", texto):
            nombre = m.group(1)
            if nombre not in nombres and nombre not in EXTERNAS and nombre not in NO_SKILLS:
                errores.append(f"{doc.relative_to(RAIZ)}: cita «{nombre}», que no está en el plugin")

    # Ficheros que cita cada SKILL.md
    for n, t in textos.items():
        codigo = re.findall(r"`([^`\n]+)`", t) + re.findall(r"^```\w*\n(.*?)^```", t, re.S | re.M)
        for palabra in " ".join(codigo).split():
            ruta = re.sub(r"^(<skill>|\$KIT|<KIT>|KIT)/", "", palabra.strip("\"'()[],;:").rstrip("."))
            if not ruta.startswith(CARPETAS) or re.search(r"[*<>{}$|]", ruta):
                continue
            if not (SKILLS / n / ruta).exists():
                errores.append(f"{n}/SKILL.md cita `{ruta}`, que no existe")

    # Rutas de una skill a otra
    for py in SKILLS.glob("*/**/*.py"):
        for m in re.finditer(r'"(appian-[a-z0-9-]+)"((?:\s*/\s*"[^"]+")+)', py.read_text(encoding="utf-8")):
            if m.group(1) in nombres:
                partes = re.findall(r'"([^"]+)"', m.group(2))
                if not SKILLS.joinpath(m.group(1), *partes).exists():
                    errores.append(f"{py.relative_to(RAIZ)}: no existe {m.group(1)}/{'/'.join(partes)}")
    for doc in documentos:
        for m in re.finditer(r"(?<![\w-])(appian-[a-z0-9-]+)/([\w.-]+(?:/[\w.-]+)*)", doc.read_text(encoding="utf-8")):
            if m.group(1) in nombres and not (SKILLS / m.group(1) / m.group(2)).exists():
                errores.append(f"{doc.relative_to(RAIZ)}: no existe {m.group(1)}/{m.group(2)}")

    # MCP
    for doc in documentos:
        for s in set(re.findall(r"mcp__([a-zA-Z0-9-]+)__", doc.read_text(encoding="utf-8"))):
            if s not in servidores:
                errores.append(f"{doc.relative_to(RAIZ)}: cita el MCP «{s}», que no está en .mcp.json")

    # Regla de dudas de Appian
    reglas = {}
    for n in REGLA_DOCS:
        bloque = seccion(textos.get(n, ""), TITULO_REGLA)
        if bloque is None:
            errores.append(f"{n}: falta el apartado «{TITULO_REGLA[3:]}»")
            continue
        regla = bloque.split("\n\n**")[0].strip()  # lo propio de la skill va después, en párrafos con negrita
        if "appian-docs" not in regla:
            errores.append(f"{n}: «{TITULO_REGLA[3:]}» no nombra el MCP appian-docs")
        reglas[n] = regla
    if len(set(reglas.values())) > 1:
        errores.append("La regla «Dudas de Appian» no es igual en " + ", ".join(reglas))

    # Frases largas repetidas entre SKILL.md
    vistas = {}
    for n, t in textos.items():
        regla = seccion(t, TITULO_REGLA) or ""
        cuerpo = t.replace(regla, "")
        for frase in re.split(r"(?<=[.:;])\s+|\n", re.sub(r"`[^`]*`", "X", cuerpo)):
            palabras = re.findall(r"\w+", frase.lower())
            if len(palabras) >= 14:
                vistas.setdefault(" ".join(palabras), set()).add(n)
    for frase, en in vistas.items():
        if len(en) > 1:
            avisos.append(f"Frase repetida en {', '.join(sorted(en))}: «{frase[:80]}…»")

    # Versión
    version = json.loads((RAIZ / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"]
    filas = re.findall(r"^\| (\d+\.\d+\.\d+[\w.-]*) \|", (RAIZ / "README.md").read_text(encoding="utf-8"), re.M)
    if not filas or filas[0] != version:
        errores.append(f"plugin.json dice {version} y la última versión del README es {filas[0] if filas else 'ninguna'}")

    if completo:
        pruebas = sorted(SKILLS.glob("*/scripts/selftest.py"))
        for p in pruebas:
            r = subprocess.run([sys.executable, str(p)], capture_output=True, text=True)
            estado = "bien" if r.returncode == 0 else f"falla (código {r.returncode})"
            print(f"Prueba de {p.parents[1].name}: {estado}")
            if r.returncode == 1:
                errores.append(f"{p.relative_to(RAIZ)} falla:\n" + (r.stdout + r.stderr)[-1500:])
            elif r.returncode:
                avisos.append(f"{p.relative_to(RAIZ)} no se pudo completar (falta un requisito)")

    for a in avisos:
        print("Aviso ·", a)
    for e in errores:
        print("Error ·", e)
    print(f"{len(nombres)} skills · {len(errores)} errores · {len(avisos)} avisos")
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main("--completo" in sys.argv[1:]))
