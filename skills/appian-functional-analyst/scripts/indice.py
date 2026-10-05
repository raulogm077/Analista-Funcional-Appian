#!/usr/bin/env python3
"""Consulta el análisis de un proyecto sin leerlo entero.

<p> es la carpeta del proyecto (o su carpeta analisis/). Lee funcional.md, tecnico.md y decisiones.md.

  indice.py resumen    <p>                              versión, piezas por tipo y estado, pendientes
  indice.py indice     <p> [--tipo HU,PAN] [--estado ⚠️]
  indice.py buscar     <p> "fecha límite" aviso [--tipo HU] [-n 15]
  indice.py ficha      <p> HU-07 PAN-04 [--lineas]
  indice.py impacto    <p> HU-07 PAN-04 [--nivel 2] [--con "plazo"]
  indice.py seccion    <p> F6 [--con "documento"]          texto de una sección: F (funcional), T (técnico), D (decisiones)
  indice.py siguientes <p>                              siguiente ID libre de cada tipo
  indice.py derivadas  <p> [--escribir]                 anexo «Quién puede hacer qué» del funcional
  indice.py grafo      <p> -o grafo.json

Estados: 🔒 Validado · ✅ Decidido · 🔶 Inferido · ⚠️ Pendiente · ❓ No definido · Anulada · Respondida.
"""
import argparse
import collections
import json
import math
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import modelo as mo

ORDEN = ["ACT", "ESC", "HU", "CA", "RB", "PAN", "AV", "DOC", "INT", "PC", "D", "DT", "PT"]
ANCHO = 2


def clave(pid):
    t = mo.tipo_de(pid)
    return (ORDEN.index(t) if t in ORDEN else 99, [int(x) for x in re.findall(r"\d+", pid)])


def etiqueta(m, pid, largo=70):
    p = m.piezas.get(pid)
    if not p:
        return f"{pid} (no existe)"
    est = f" {p.estado}" if p.estado else ""
    padre = f" ∈ {p.padre}" if p.padre else ""
    return f"{pid}{est} — {p.titulo[:largo]}  [{p.donde()}{padre}]"


def contexto(m, doc, linea):
    """«funcional §6 · 6.1 Solicitud»: dónde está una línea, estable aunque cambien los números de línea."""
    D = m.docs[doc]
    sec = D.seccion_de_linea[linea]
    tit = ""
    for k in range(linea, -1, -1):
        l = D.lineas[k]
        if l.startswith("## "):
            break
        if l.startswith("#"):
            tit = l.strip("# ").strip()
            break
        mf = mo.RX_FICHA.match(l)
        if mf:
            tit = mf.group(2)
            break
    return f"{mo.NOMBRE_DOC[doc]} §{sec}" + (f" · {tit[:50]}" if tit else "")


def patron(termino):
    """«tipos de documento» encuentra también «tipo de documento» y «tipología de documentos»."""
    raices = [w[:-1] if len(w) > 4 and w.endswith("s") else w for w in re.findall(r"\w+", mo.normaliza(termino))]
    return re.compile(r"\b" + r"\w*\W+".join(re.escape(w) for w in raices) + r"\w*")


# ---------------------------------------------------------------- comandos
def c_resumen(m, a):
    for d in ("F", "T"):
        v = m.version(d)
        if d in m.docs:
            print(f"{mo.NOMBRE_DOC[d].capitalize()}: versión {v[0]}.{v[1]}" if v else f"{mo.NOMBRE_DOC[d]}: sin versión")
    if "T" not in m.docs:
        print("Técnico: todavía no existe")
    tab = collections.defaultdict(collections.Counter)
    for p in m.piezas.values():
        tab[p.tipo][p.estado or "—"] += 1
    cols = mo.ESTADOS + ["—", "Anulada", "Respondida", "Vigente", "Sustituida"]
    usadas = [c for c in cols if any(tab[t][c] for t in tab)]
    print("\n| Tipo | Total | " + " | ".join(usadas) + " |")
    print("|---|---|" + "---|" * len(usadas))
    for t in sorted(tab, key=lambda x: ORDEN.index(x) if x in ORDEN else 99):
        print(f"| {t} | {sum(tab[t].values())} | " + " | ".join(str(tab[t][c] or "") for c in usadas) + " |")
    pc = [p.id for p in m.vigentes("PC")]
    pt = [p.id for p in m.vigentes("PT")]
    print(f"\nPendiente de confirmar con el cliente: {len(pc)}" + (f" ({', '.join(sorted(pc, key=clave))})" if pc else ""))
    print(f"Pendientes técnicos: {len(pt)}" + (f" ({', '.join(sorted(pt, key=clave))})" if pt else ""))
    if m.duplicados:
        print(f"⚠ IDs definidos dos veces: {m.duplicados[:10]}")


def _filtra(m, a):
    tipos = set(a.tipo.split(",")) if getattr(a, "tipo", None) else None
    for p in sorted(m.piezas.values(), key=lambda p: clave(p.id)):
        if tipos and p.tipo not in tipos:
            continue
        if getattr(a, "estado", None) and p.estado != a.estado:
            continue
        yield p


def c_indice(m, a):
    for p in _filtra(m, a):
        if p.tipo == "CA" and not a.tipo:
            continue
        print(etiqueta(m, p.id, 90))


def c_buscar(m, a):
    terminos = [mo.normaliza(t) for t in a.terminos]
    pats = [patron(t) for t in a.terminos]
    tipos = set(a.tipo.split(",")) if a.tipo else None
    candidatas = [p for p in m.piezas.values() if p.tipo != "CA" and not (tipos and p.tipo not in tipos)]
    textos = {p.id: mo.normaliza(m.texto(p.id)) for p in candidatas}
    # un término raro pesa más que uno que sale en todas partes
    peso = {t: math.log((len(candidatas) + 1) / (1 + sum(bool(pt.search(x)) for x in textos.values()))) + 1
            for t, pt in zip(terminos, pats)}
    res = []
    for p in candidatas:
        txt, tit = textos[p.id], mo.normaliza(p.titulo)
        hallados = [(t, pt) for t, pt in zip(terminos, pats) if pt.search(txt)]
        if not hallados:
            continue
        score = sum(peso[t] * (4 + math.log1p(len(pt.findall(txt))) + 3 * bool(pt.search(tit))) for t, pt in hallados)
        if p.forma == "ficha":
            score -= math.log1p(p.fin - p.ini)
        res.append((score, p.id, [t for t, _ in hallados]))
    res.sort(key=lambda x: -x[0])
    if not res:
        print("Sin resultados entre las piezas con ID.")
    for s, pid, h in res[: a.n]:
        print(f"{s:5.1f}  {etiqueta(m, pid)}  ← {', '.join(h)}")
    cubiertas = {(p.doc, i) for p in m.piezas.values() for i in range(p.ini, p.fin)}
    sueltas = []
    for d, D in m.docs.items():
        for i, l in enumerate(D.lineas):
            if (d, i) in cubiertas or l.startswith("#"):
                continue
            if all(pt.search(mo.normaliza(l)) for pt in pats):
                sueltas.append((d, i, l.strip()[:90]))
    if sueltas:
        print(f"\nTexto sin ID que también lo menciona ({len(sueltas)}):")
        for d, i, l in sueltas[:10]:
            print(f"  {contexto(m, d, i)} (l.{i + 1}): {l}")


def c_ficha(m, a):
    for pid in a.ids:
        p = m.piezas.get(pid)
        if not p:
            print(f"── {pid}: no existe\n")
            continue
        D = m.docs[p.doc]
        veces = collections.Counter(l for l in D.lineas if l.strip())
        print(f"── {etiqueta(m, pid, 90)} · {mo.DOCS[p.doc]} líneas {p.ini + 1}–{p.fin}")
        if p.forma == "fila" and p.cabecera:
            print(p.cabecera)
        for k, l in enumerate(m.bloque(pid)):
            marca = "⟂" if a.lineas and veces[l] > 1 else " "
            print(f"{p.ini + k + 1:6d}{marca} {l}" if a.lineas else l)
        print()
    if a.lineas:
        print("⟂ = la línea está igual en otro sitio del fichero: al editar, incluye la de al lado para que sea única.")


def c_seccion(m, a):
    doc, n = (a.n[0].upper(), a.n[1:]) if a.n[0].isalpha() else ("F", a.n)
    if doc not in m.docs:
        sys.exit(f"No existe {mo.DOCS.get(doc, a.n)}")
    D = m.docs[doc]
    rango = D.seccion(mo.normaliza(n) if not n.isdigit() else n)
    if not rango:
        sys.exit(f"No hay sección {n} en {mo.DOCS[doc]}. Secciones: " + ", ".join(s[0] for s in D.secciones))
    lineas = list(range(*rango))
    if a.con:
        pats = [patron(x) for x in a.con]
        elegidas = set()
        for i in lineas:
            if any(pt.search(mo.normaliza(D.lineas[i])) for pt in pats):
                if D.lineas[i].startswith("|"):  # la tabla entera y lo que la precede
                    a0 = b0 = i
                    while a0 - 1 >= rango[0] and D.lineas[a0 - 1].startswith("|"):
                        a0 -= 1
                    while b0 + 1 < rango[1] and D.lineas[b0 + 1].startswith("|"):
                        b0 += 1
                    t0 = next((k for k in range(a0 - 1, max(a0 - 4, rango[0] - 1), -1) if D.lineas[k].strip()), None)
                    elegidas |= set(range(a0, b0 + 1)) | ({t0} if t0 is not None else set())
                else:
                    elegidas.add(i)
        lineas = sorted(elegidas)
    if not lineas:
        print("Nada.")
    for i in lineas[: a.max]:
        print(f"{i + 1:6d}  {D.lineas[i]}")
    if len(lineas) > a.max:
        print(f"… {len(lineas) - a.max} líneas más (acota con --con)")


def dependencias(m, ids, nivel=1, con=None):
    """Qué hay que revisar si cambian estas piezas: las que las citan y a las que remiten."""
    entrada = {m.raiz_de(i) for i in ids}
    citan, remite, sueltas = {}, {}, {}
    frontera = set(entrada)
    for n in range(nivel):
        nueva = set()
        for pid in frontera:
            p = m.piezas.get(pid)
            if not p:
                continue
            for o in {pid} | set(p.hijos):
                for c in m.citada_por.get(o, ()):
                    r = m.raiz_de(c)
                    if r in entrada or r == pid:
                        continue
                    if con and not any(x in mo.normaliza(m.texto(c)) for x in con):
                        continue
                    citan.setdefault(r, set()).add(f"cita {o}" if n == 0 else f"cita {o} (nivel {n + 1})")
                    nueva.add(r)
                for d, l in m.menciones.get(o, ()):
                    if con and not any(x in mo.normaliza(m.docs[d].lineas[l]) for x in con):
                        continue
                    sueltas.setdefault((d, l), set()).add(o)
            if n == 0:
                for r0 in p.refs:
                    r = m.raiz_de(r0)
                    if r not in entrada and r in m.piezas:
                        if con and not any(x in mo.normaliza(m.texto(r)) for x in con):
                            continue
                        remite.setdefault(r, set()).add(f"{pid} la cita")
        frontera = nueva - entrada
    for r in citan:
        remite.pop(r, None)
    return entrada, citan, remite, sueltas


def c_impacto(m, a):
    con = [mo.normaliza(x) for x in a.con] if a.con else None
    entrada, citan, remite, sueltas = dependencias(m, a.ids, a.nivel, con)
    if con:
        print(f"(solo dependencias cuyo texto menciona: {', '.join(a.con)})")
    print("Piezas de entrada:")
    for pid in sorted(entrada, key=clave):
        print("  " + etiqueta(m, pid))
        p = m.piezas.get(pid)
        if p and p.hijos:
            print(f"      criterios: {', '.join(p.hijos)}")

    def lista(titulo, d):
        print(f"\n{titulo} ({len(d)}):")
        for pid in sorted(d, key=clave):
            print(f"  {etiqueta(m, pid, 60)}  ← {'; '.join(sorted(d[pid]))}")
    lista("Revisar: dependen de ellas (las citan)", citan)
    lista("Revisar si cambia el contenido: ellas remiten a", remite)
    if sueltas:
        print(f"\nTexto sin ID que las menciona ({len(sueltas)} líneas; cítalo por su sección):")
        for (d, l) in sorted(sueltas)[:30]:
            print(f"  {contexto(m, d, l)} [{', '.join(sorted(sueltas[(d, l)]))}] (l.{l + 1}): "
                  f"{m.docs[d].lineas[l].strip()[:80]}")
    if con:
        pats = [patron(x) for x in a.con]
        ps = []
        for p in m.vigentes("PC") + m.vigentes("PT"):
            if p.id in citan or p.id in entrada:
                continue
            txt = mo.normaliza(m.texto(p.id))
            if all(pt.search(txt) for pt in pats):
                ps.append((-sum(len(pt.findall(txt)) for pt in pats), p.id))
        if ps:
            print(f"\nPendientes del mismo tema ({len(ps)}): ¿los contesta el punto?")
            for _, x in sorted(ps)[:6]:
                print("  " + etiqueta(m, x, 80))
    todas = list(entrada) + list(citan)
    pan = sorted({x for x in todas if x.startswith("PAN-")}, key=clave)
    if pan:
        print(f"\nPantallas afectadas (prototipo): {', '.join(pan)}")
    tec = sorted({x for x in todas if m.piezas.get(x) and m.piezas[x].doc == "T"} |
                 {f"técnico §{m.docs['T'].seccion_de_linea[l]}" for (d, l) in sueltas if d == "T"}, key=str)
    if tec:
        print(f"Especificación técnica afectada: {', '.join(tec)}")
    val = [x for x in todas if m.piezas.get(x) and m.piezas[x].estado == "🔒"]
    if val:
        print(f"\n🔒 Validadas por el cliente (cambiarlas requiere aprobación): {', '.join(sorted(val, key=clave))}")


def c_siguientes(m, a):
    usados = collections.defaultdict(set)
    for pid, p in m.piezas.items():
        if p.tipo != "CA":
            usados[p.tipo].add(mo.numero(pid))
    for t in ORDEN:
        if t != "CA":
            n = (max(usados[t]) + 1) if usados[t] else 1
            print(f"{t}-{n:0{ANCHO}d}")
    print("Criterios: el siguiente .n de su historia (HU-07.4 tras HU-07.3)")


def c_grafo(m, a):
    nodos = [{"id": p.id, "tipo": p.tipo, "titulo": p.titulo, "doc": mo.DOCS[p.doc], "seccion": p.seccion,
              "estado": p.estado, "padre": p.padre, "fuentes": sorted(p.fuentes), "linea": p.ini + 1}
             for p in sorted(m.piezas.values(), key=lambda p: clave(p.id))]
    aristas = [{"de": p.id, "a": r} for p in m.piezas.values() for r in sorted(p.refs) if r in m.piezas]
    aristas += [{"de": p.id, "a": h, "tipo": "contiene"} for p in m.piezas.values() for h in p.hijos]
    pathlib.Path(a.o).write_text(json.dumps({"nodos": nodos, "aristas": aristas}, ensure_ascii=False, indent=1),
                                 encoding="utf-8")
    print(f"{a.o}: {len(nodos)} piezas, {len(aristas)} referencias")


# ------------------------------------------------------- anexo derivado
TITULO_ANEXO = "## Anexo. Quién puede hacer qué"


def perfiles(m):
    for _, cab, filas in m.tablas("F", "2"):
        if cab and mo.normaliza(cab[0]) == "perfil":
            return [f[0] for f in filas if f and f[0]]
    return []


def anexo(m):
    pf = perfiles(m)
    filas = []
    for p in sorted(m.vigentes("PAN"), key=lambda p: clave(p.id)):
        for l in m.bloque(p.id):
            c = mo.celdas(l) if l.startswith("|") else []
            if len(c) < 3 or mo.normaliza(c[0]) in ("parte", "") or set(c[0]) <= set("-: "):
                continue
            quien = mo.normaliza(mo.sin_comentarios(c[2]))
            marcas = ["✔" if "todos" in quien or mo.normaliza(x) in quien else "" for x in pf]
            filas.append(f"| {p.id} {p.titulo} · {c[0]} | " + " | ".join(marcas) + " |")
    return [TITULO_ANEXO, "",
            "Se genera a partir de las pantallas (apartado 5) con `indice.py derivadas`; no se edita a mano.", "",
            "| Pantalla y parte | " + " | ".join(pf) + " |", "|---|" + "---|" * len(pf)] + filas


def c_derivadas(m, a):
    if "F" not in m.docs:
        sys.exit("No existe funcional.md")
    nuevo = anexo(m)
    L = m.docs["F"].lineas
    ini = next((i for i, l in enumerate(L) if l.startswith("## Anexo")), None)
    if ini is None:
        while L and not L[-1].strip():
            L = L[:-1]
        resultado = L + [""] + nuevo + [""]
    else:
        fin = next((i for i in range(ini + 1, len(L)) if L[i].startswith("## ")), len(L))
        resultado = L[:ini] + nuevo + [""] + L[fin:]
    texto = "\n".join(resultado).rstrip("\n") + "\n"
    actual = "\n".join(m.docs["F"].lineas)
    if texto.rstrip("\n") == actual.rstrip("\n"):
        print("El anexo está al día.")
    elif a.escribir:
        m.ruta("F").write_text(texto, encoding="utf-8")
        print(f"Anexo escrito en {m.ruta('F')} ({len(nuevo) - 6} filas).")
    else:
        print("\n".join(nuevo))
        print("\n(El anexo ha cambiado. Con --escribir se guarda en funcional.md.)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def nuevo(nombre, f):
        s = sub.add_parser(nombre)
        s.add_argument("proyecto")
        s.set_defaults(f=f)
        return s
    nuevo("resumen", c_resumen)
    s = nuevo("indice", c_indice); s.add_argument("--tipo"); s.add_argument("--estado")
    s = nuevo("buscar", c_buscar); s.add_argument("terminos", nargs="+"); s.add_argument("--tipo")
    s.add_argument("-n", type=int, default=15)
    s = nuevo("ficha", c_ficha); s.add_argument("ids", nargs="+"); s.add_argument("--lineas", action="store_true")
    s = nuevo("impacto", c_impacto); s.add_argument("ids", nargs="+"); s.add_argument("--nivel", type=int, default=1)
    s.add_argument("--con", nargs="+", help="solo dependencias cuyo texto menciona alguno de estos términos")
    s = nuevo("seccion", c_seccion); s.add_argument("n"); s.add_argument("--con", nargs="+")
    s.add_argument("--max", type=int, default=150)
    nuevo("siguientes", c_siguientes)
    s = nuevo("derivadas", c_derivadas); s.add_argument("--escribir", action="store_true")
    s = nuevo("grafo", c_grafo); s.add_argument("-o", default="grafo.json")
    a = ap.parse_args()
    m = mo.Proyecto(a.proyecto)
    if not m.docs:
        sys.exit(f"No encuentro funcional.md, tecnico.md ni decisiones.md en {m.analisis}")
    a.f(m, a)


if __name__ == "__main__":
    main()
