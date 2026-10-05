#!/usr/bin/env python3
"""Une al análisis del proyecto los módulos escritos por separado (análisis grandes, references/volumen-grande.md).

Uso:
  unir_modulos.py <proyecto> modulos/M1-funcional.md modulos/M2-funcional.md modulos/M1-tecnico.md … [--escribir]

- Cada módulo tiene los apartados «## N. Título» del fichero al que va (funcional o técnico, según el nombre
  del módulo) con solo su parte. Su contenido se añade al final del mismo apartado del proyecto, en el orden
  en que se pasan los módulos.
- Las decisiones del cliente van en un apartado «## Decisiones» del módulo, como filas «| D-? | fecha | … |».
  Se añaden a decisiones.md ordenadas por fecha y numeradas a continuación de la última.
- Sin --escribir solo dice qué haría. Después: indice.py derivadas --escribir y comprobar.py.
"""
import argparse
import glob
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import modelo as mo


def partes(texto):
    """{clave: [líneas]} del contenido de cada «## …» (sin el título)."""
    out, clave = {}, None
    for l in texto.split("\n"):
        m = mo.RX_SECCION.match(l)
        if m:
            clave = m.group(1) or mo.normaliza(m.group(2))
            out.setdefault(clave, [])
            continue
        if clave is not None:
            out[clave].append(l)
    return {k: v for k, v in out.items() if any(x.strip() for x in v)}


def inserta(lineas, clave, nuevas):
    """Añade `nuevas` al final del apartado `clave` de `lineas`."""
    ini = next((i for i, l in enumerate(lineas) if (m := mo.RX_SECCION.match(l)) and
                (m.group(1) or mo.normaliza(m.group(2))) == clave), None)
    if ini is None:
        raise SystemExit(f"El proyecto no tiene el apartado «## {clave}.»")
    fin = next((i for i in range(ini + 1, len(lineas)) if lineas[i].startswith("## ")), len(lineas))
    while fin > ini + 1 and not lineas[fin - 1].strip():
        fin -= 1
    bloque = list(nuevas)
    while bloque and not bloque[0].strip():
        bloque.pop(0)
    while bloque and not bloque[-1].strip():
        bloque.pop()
    if not (bloque and bloque[0].startswith("|") and lineas[fin - 1].startswith("|")):
        bloque = [""] + bloque  # una fila sigue la tabla anterior; lo demás va separado
    resto = lineas[fin:]
    return lineas[:fin] + bloque + ([] if resto and not resto[0].strip() else [""]) + resto


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("proyecto")
    ap.add_argument("modulos", nargs="+")
    ap.add_argument("--escribir", action="store_true")
    a = ap.parse_args()
    m = mo.Proyecto(a.proyecto)
    textos = {d: list(m.docs[d].lineas) for d in m.docs}
    decisiones = []
    rutas = [x for r in a.modulos for x in (sorted(glob.glob(r)) if glob.has_magic(r) else [r])]  # también en PowerShell y cmd
    for ruta in rutas:
        nombre = pathlib.Path(ruta).stem
        doc = "T" if "tecnico" in mo.normaliza(nombre) else "F"
        if doc not in textos:
            sys.exit(f"No existe {mo.DOCS[doc]} en el proyecto")
        for clave, lineas in partes(pathlib.Path(ruta).read_text(encoding="utf-8")).items():
            if clave == "decisiones":
                decisiones += [l for l in lineas if re.match(r"^\|\s*D-\?\s*\|", l)]
                continue
            textos[doc] = inserta(textos[doc], clave, lineas)
            print(f"{nombre} → {mo.DOCS[doc]} §{clave}: {sum(1 for x in lineas if x.strip())} líneas")
    if decisiones:
        if "D" not in textos:
            sys.exit("No existe decisiones.md en el proyecto")
        usados = [mo.numero(p.id) for p in m.por_tipo("D")]
        n = max(usados, default=0)
        fecha = lambda l: (mo.celdas(l)[1] if len(mo.celdas(l)) > 1 else "")
        nuevas = []
        for l in sorted(decisiones, key=fecha):
            n += 1
            nuevas.append(re.sub(r"^\|\s*D-\?\s*\|", f"| D-{n:02d} |", l))
        textos["D"] = inserta(textos["D"], "decisiones", nuevas)
        print(f"decisiones.md: {len(nuevas)} decisiones nuevas, D-{n - len(nuevas) + 1:02d} a D-{n:02d}")
    if a.escribir:
        for d, lineas in textos.items():
            m.ruta(d).write_text("\n".join(lineas).rstrip("\n") + "\n", encoding="utf-8")
        print("Escrito. Ahora: indice.py derivadas --escribir y comprobar.py")
    else:
        print("(Sin --escribir no se ha cambiado nada.)")


if __name__ == "__main__":
    main()
