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
  indice.py pendientes <p>                              guion de la próxima reunión: lo que decide el equipo
                                                        (puntos «Pendiente» de los informes) y las PC, por «A quién»
  indice.py grafo      <p> [-o analisis/grafo.json]       las piezas y sus referencias en JSON (en el proyecto)

Con unidades de cambio (analisis/cambios.md, references/cambios.md):
  indice.py cambios    <p> EV-02 [--json]               lo de una unidad: piezas nuevas, que cambian (antes y después) y
                                                        anuladas, pantallas, técnico, objetos, pruebas, colisiones
  indice.py colision   <p> URG-01                       la corrección urgente frente a las unidades sin pasar a producción
  indice.py encargo    <p> EV-02                        construccion/EV-02.md y EV-02-esperado.json (unidad aprobada)
  ficha e impacto imprimen además «Construido: … · En curso: …» por pieza.

Estados: 🔒 Validado · ✅ Decidido · 🔶 Inferido · ⚠️ Pendiente · ❓ No definido · Anulada · Respondida.
"""
import argparse
import collections
import json
import math
import pathlib
import re
import sys
sys.dont_write_bytecode = True  # sin __pycache__ en el plugin: no se escribe fuera del proyecto

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import modelo as mo
import unidades as un

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
    ctx = un.Contexto(m)
    for pid in a.ids:
        p = m.piezas.get(pid)
        if not p:
            print(f"── {pid}: no existe\n")
            continue
        D = m.docs[p.doc]
        veces = collections.Counter(l for l in D.lineas if l.strip())
        print(f"── {etiqueta(m, pid, 90)} · {mo.DOCS[p.doc]} líneas {p.ini + 1}–{p.fin}")
        if ctx.hay:
            print(f"   {ctx.texto_senales(pid)}")
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
    ctx = un.Contexto(m)
    construidas, en_curso = [], set()
    for pid in sorted(entrada, key=clave):
        print("  " + etiqueta(m, pid))
        p = m.piezas.get(pid)
        if p and p.hijos:
            print(f"      criterios: {', '.join(p.hijos)}")
        if ctx.hay and p:
            hecho, curso = ctx.senales(pid)
            print(f"      {ctx.texto_senales(pid)}")
            construidas += [pid] if hecho else []
            en_curso |= set(curso)
    if construidas:   # señales del informe (references/cambios.md): el modelo las copia, no las deduce
        print(f"  → Si el punto las cambia, «Posible petición de cambio» en el Resumen: {', '.join(construidas)} "
              "están construidas (no pide aprobación)")
    # la unidad del informe (--cambio o, sin él, la única Abierta) no se sugiere: tocar lo suyo no pide aprobación
    abiertas = [u.id for u in ctx.unidades if u.estado == un.ABIERTA]
    propia = (a.cambio or "").upper() or (abiertas[0] if len(abiertas) == 1 else None)
    ev_abiertas = [u for u in abiertas if u.startswith("EV-")]
    sugerida = None
    if ctx.hay and construidas and not a.cambio and not ev_abiertas:   # dónde va: lo dice el script, no el modelo
        sig = 1 + max([int(u.id.split("-")[1]) for u in ctx.unidades if u.id.startswith("EV-")] or [0])
        sugerida = f"EV-{sig:02d}"
        print(f"  → Ninguna unidad Abierta: si aplicas el cambio, ábrela antes (proyecto.py cambio <p> {sugerida} "
              f"abrir --titulo \"…\") y pon «Cambio: {sugerida}» en el informe; meterlo en una Aprobada la "
              "devuelve a aprobación")
    # la fila de §13 sin leer §13 (la unidad: --cambio, la única EV Abierta o la que se acaba de sugerir abrir)
    unidad13 = (a.cambio or "").upper() or (ev_abiertas[0] if len(ev_abiertas) == 1 else None) or sugerida
    if ctx.hay and construidas and unidad13 and "T" in m.docs:
        fila_13(m, ctx, construidas, unidad13)
    otras = sorted(en_curso - {propia})
    if otras:
        print(f"  → En curso en {', '.join(otras)}: si el punto es de {propia or 'otra unidad'}, «Requiere: Sí "
              f"({', '.join(otras)})»: hay que decidir el orden")

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


def pantallas_de(m, pid):
    """Las pantallas de una pieza: ella misma si es una PAN; si no, las de la columna «Pantalla» de su ficha."""
    r = m.raiz_de(pid)
    if r.startswith("PAN-"):
        return [r]
    col, out = None, []
    for l in m.bloque(r) if r in m.piezas else []:
        if not l.startswith("|"):
            if out:
                break
            continue
        c = mo.celdas(l)
        if col is None:
            col = next((i for i, x in enumerate(c) if mo.normaliza(x) == "pantalla"), None)
        elif col < len(c):
            out += re.findall(r"PAN-\d+", c[col])
    return list(dict.fromkeys(out))


def fila_13(m, ctx, construidas, unidad):
    """La fila de técnico §13 que lleva lo construido que cambia, sin leer §13: el formato, el siguiente paso y los
    objetos construidos de la fila del técnico de su pantalla («| PAN-01 | `DEM_Dashboard`, … |»), en su orden (el
    primero es el que la implementa). Sin pantalla o sin esa fila, solo el formato."""
    tipos = {}
    for f in ctx.filas:
        for o in f["objetos"]:
            tipos.setdefault(un.objeto(o), f["tipo"])
    hechos, ya = ctx.linea_base(), set(ctx.cambian(unidad))
    pantallas = {x for pid in construidas for x in pantallas_de(m, pid)}
    T, objetos = m.docs["T"], []
    for i, l in enumerate(T.lineas):
        if not l.startswith("|") or T.seccion_de_linea[i] in ("13", "14", "15"):
            continue
        c = mo.celdas(l)
        if c and mo.sin_comentarios(c[0]).strip() in pantallas:
            for o in un.objetos_celda(" ".join(re.findall(r"`[^`]+`", l))):
                o = un.objeto(o)
                if o in hechos and o not in ya and o not in objetos:
                    objetos.append(o)
    pasos = [int(x) for f in ctx.filas for x in re.findall(r"^\s*(\d+)", mo.sin_comentarios(f["paso"]))]
    o = objetos[0] if objetos else None
    ejemplo = (f"| {max(pasos or [0]) + 1} | `{o or '<objeto>'}` | {tipos.get(o, '<tipo>')} | Modifica | — | "
               f"{unidad} |")
    print(f"  → Técnico §13: cada objeto construido que cambie lleva su fila de {unidad} (los que no cambian, "
          f"ninguna), así: «{ejemplo}»" + (". Los de la fila de su pantalla en el técnico: " + ", ".join(
              f"`{x}` ({tipos.get(x, '?')})" for x in objetos) if objetos else ""))


def c_siguientes(m, a):
    usados = collections.defaultdict(set)
    for pid, p in m.piezas.items():
        if p.tipo != "CA":
            usados[p.tipo].add(mo.numero(pid))
    for t in ORDEN:
        if t != "CA":
            n = (max(usados[t]) + 1) if usados[t] else 1
            print(f"{t}-{n:0{ANCHO}d}")
    print("Criterios: el siguiente .n de su historia o de su ficha INT (HU-07.4 tras HU-07.3)")


def c_grafo(m, a):
    nodos = [{"id": p.id, "tipo": p.tipo, "titulo": p.titulo, "doc": mo.DOCS[p.doc], "seccion": p.seccion,
              "estado": p.estado, "padre": p.padre, "fuentes": sorted(p.fuentes), "linea": p.ini + 1}
             for p in sorted(m.piezas.values(), key=lambda p: clave(p.id))]
    aristas = [{"de": p.id, "a": r} for p in m.piezas.values() for r in sorted(p.refs) if r in m.piezas]
    aristas += [{"de": p.id, "a": h, "tipo": "contiene"} for p in m.piezas.values() for h in p.hijos]
    destino = pathlib.Path(a.o) if a.o else m.analisis / "grafo.json"   # en el proyecto: el plugin no escribe fuera
    mo.escribe(destino, json.dumps({"nodos": nodos, "aristas": aristas}, ensure_ascii=False, indent=1))
    print(f"{destino}: {len(nodos)} piezas, {len(aristas)} referencias")


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
            quien = mo.normaliza(mo.sin_comentarios(c[2])).strip()
            lista = {x.strip() for x in re.split(r",|;", re.sub(r"^todos\s*(menos|salvo|excepto)?", "", quien)) if x.strip()}
            if quien.startswith("todos"):
                marcas = ["" if mo.normaliza(x) in lista else "✔" for x in pf]
            else:
                marcas = ["✔" if mo.normaliza(x) in lista else "" for x in pf]
            filas.append(f"| {p.id} {p.titulo} · {c[0]} | " + " | ".join(marcas) + " |")
    return [TITULO_ANEXO, "",
            "<!-- Lo genera indice.py derivadas a partir de las pantallas (apartado 5); no se edita a mano. -->", "",
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
        mo.escribe(m.ruta("F"), texto)
        print(f"Anexo escrito en {m.ruta('F')} ({len(nuevo) - 6} filas).")
    else:
        print("\n".join(nuevo))
        print("\n(El anexo ha cambiado. Con --escribir se guarda en funcional.md.)")


def peso_pc(m, p):
    """Lo que pesa una PC abierta: los elementos de su «Afecta a» y las líneas que la citan fuera del §11."""
    cel = celda(m, p, "afecta a")
    elementos = [x for x in re.split(r",", mo.sin_comentarios(cel)) if x.strip(" —-")]
    citas = 0
    for d, D in m.docs.items():
        for i, l in enumerate(D.lineas):
            if d == "F" and D.seccion_de_linea[i] == "11":
                continue
            if p.id in mo.ids_en(mo.sin_comentarios(l)):
                citas += 1
    return len(elementos) + citas


def celda(m, p, nombre):
    """El valor de la columna `nombre` (normalizado) de una pieza de tipo fila."""
    cab = [mo.normaliza(c) for c in mo.celdas(p.cabecera)]
    cel = mo.celdas(m.lineas(p.doc)[p.ini])
    return cel[cab.index(nombre)] if nombre in cab and cab.index(nombre) < len(cel) else ""


def para_decidir(m):
    """[(informe, punto)] de los puntos «Decisión: Pendiente» de impacto/*.md: lo que tiene que decidir el equipo."""
    return [(nombre, f) for nombre, _, puntos, _ in mo.informes(m.raiz) for f in puntos
            if mo.normaliza(f.get("decision", "")).strip(" *").startswith("pendiente")]


def c_pendientes(m, a):
    """Guion de la próxima reunión: primero lo que tiene que decidir el equipo (los puntos pendientes de aprobación de los
    informes, que no llegan solos a §11 ni al Word); después, las PC abiertas agrupadas por «A quién», en cada grupo de
    más peso a menos."""
    grupos = collections.defaultdict(list)
    for p in m.vigentes("PC"):
        quien = mo.sin_comentarios(celda(m, p, "a quien")).strip(" —-") or "Sin asignar"
        grupos[quien].append((-peso_pc(m, p), clave(p.id), p))
    decidir = para_decidir(m)
    if not grupos and not decidir:
        print("No hay preguntas pendientes de confirmar.")
        return
    print("# Próxima reunión: lo pendiente de confirmar\n")
    if decidir:
        print("## Para decidir (equipo)\n")
        print("Puntos pendientes de aprobación: no se aplican ni van al cliente hasta que el equipo decida.\n")
        for inf, f in decidir:
            print(f"- **{inf} · punto {f.get('#', '?')}** {mo.sin_comentarios(f.get('que se dice', '')).strip()}")
            cambio = mo.sin_comentarios(f.get("cambio propuesto", "")).strip(" —-")
            if cambio:
                print(f"  - Cambio propuesto: {cambio}")
            req = mo.sin_comentarios(next((v for k, v in f.items() if k.startswith("requiere")), "")).strip()
            motivo = re.search(r"\(([^)]*)\)", req)
            if req.strip(" —-"):
                print(f"  - Requiere: {motivo.group(1) if motivo else req}")
        print()
    if not grupos:
        print("No hay preguntas pendientes de confirmar con el cliente.")
        return
    print("De más a menos peso en cada grupo: lo que afecta a más partes del análisis va primero.\n")
    orden = sorted(grupos, key=lambda q: (min(x[0] for x in grupos[q]), mo.normaliza(q)))
    for quien in orden:
        print(f"## {quien}\n")
        for peso, _, p in sorted(grupos[quien], key=lambda x: x[:2]):
            pregunta = mo.sin_comentarios(celda(m, p, "pregunta")).strip() or p.titulo
            print(f"- **{p.id}** {pregunta}")
            opciones = mo.sin_comentarios(celda(m, p, "opciones")).strip(" —-")
            if opciones:
                print(f"  - Opciones: {opciones}")
            afecta = mo.sin_comentarios(celda(m, p, "afecta a")).strip(" —-")
            if afecta:
                print(f"  - Afecta a: {afecta}")
        print()


# ------------------------------------------------------- unidades de cambio (references/cambios.md)
DX = ('uv run --no-project --python ">=3.10" --with "mcp>=1.2,<2" python '
      '"<skill de ingeniería inversa>/scripts/devmcp_extract.py"')


def unidad(m, uid):
    """El contexto de las unidades y el ID, o sale: sin analisis/cambios.md o sin esa unidad no hay nada que derivar."""
    ctx = un.Contexto(m)
    uid = uid.upper()
    if not ctx.hay:
        sys.exit(f"No hay {m.analisis / un.FICHERO}: las unidades se abren con proyecto.py cambio <p> <ID> abrir")
    if uid not in ctx.por_id:
        sys.exit(f"{uid} no está en analisis/cambios.md ({', '.join(ctx.por_id) or 'sin unidades'})")
    return ctx, uid


def c_cambios(m, a):
    """Lo de una unidad: piezas, historias, pantallas, diagramas, técnico, objetos, pruebas a repetir y colisiones."""
    ctx, uid = unidad(m, a.unidad)
    r = ctx.resumen(uid)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return
    lista = lambda xs: ", ".join(xs) or "—"
    print(f"# {uid} · {r['titulo']} · {r['estado']}")
    print(f"Fuentes: {lista(r['informes'])} · versión {r['base'] or '?'} → {r['version']}"
          + ("" if r["copiaBase"] else " (sin la copia de la versión base en versiones/: Nueva o Cambia sale de los "
                                       "puntos de sus informes)"))
    piezas = r["piezas"]
    print("\nNuevas: " + lista(p["id"] + " " + p["titulo"][:50] for p in piezas["nuevas"]))
    print(f"Cambian ({len(piezas['cambian'])}):")
    for p in piezas["cambian"]:
        print(f"  {p['id']} — {p['titulo'][:60]}")
        for k in ("antes", "despues"):
            for l in p[k]:
                print(f"    {'antes  ' if k == 'antes' else 'después'}: {l[:120]}")
    print(f"Anuladas: {lista(p['id'] for p in piezas['anuladas'])}")
    print(f"Historias que se conservan y comparten pantalla o paso (van en el DF del cambio): "
          f"{lista(r['historias']['seConservan'])}")
    print(f"\nPantallas: {lista(r['pantallas'])}" + (f" (capture.py … --solo {','.join(r['pantallas'])})"
                                                     if r["pantallas"] else ""))
    print(f"Diagramas: {lista(r['diagramas'])}")
    print(f"Técnico: {lista(r['tecnico'])}")
    print("Objetos (técnico §13): " + lista(o["objeto"] + " (" + o["situacion"] + ")" for o in r["objetos"]))
    pr = r["pruebas"]
    print(f"\nPruebas a repetir: criterios {lista(pr['criterios'])} · escenarios {lista(pr['escenarios'])} · urgentes "
          + lista(g["id"] + " (" + ", ".join(g["objetos"]) + ")" for g in pr["urgentes"]))
    for c in r["colisiones"]:
        if c["unidad"].startswith("URG"):
            print(f"Colisión: {c['unidad']} ({c['estado']}) corrige {', '.join(c['objetos'])} (urgentes.md)")
            continue
        print(f"Colisión: {c['unidad']} ({c['estado']}) también cambia {', '.join(c['objetos'])}"
              + (f" · decisión: {c['decision']}" if c["decision"] else " · sin decisión"))
    for t in r["reaplicar"]:
        print(f"Reaplicar {t['urgente']} en {', '.join(t['objetos'])} (proyecto.py cambio … construida --reaplicada "
              f"{t['urgente']})")
    for t in r["congelados"]:
        print(f"Congelados hasta el pase de {t['urgente']}: {', '.join(t['objetos'])}")


def c_colision(m, a):
    """Una corrección urgente frente a las unidades en curso (sin pasar a producción): los objetos que corrige y los que
    los usan (as-is/datos/dependencias.json) y, si hay as-is/datos/deriva.json, lo modificado en desarrollo después del
    último pase."""
    ctx, uid = unidad(m, a.unidad)
    if not ctx.por_id[uid].urgente:
        sys.exit(f"{uid} no es una URG: la colisión es de un cambio urgente (references/urgentes.md)")
    col = ctx.colision(uid)
    if not col["corregidos"]:
        sys.exit(f"impacto/{uid}.md no dice «Objetos» en «Urgencia» (references/urgentes.md)")
    print(f"{uid} corrige: {', '.join(col['corregidos'])}" + (f" · los usan: {', '.join(col['usan'])}" if col["usan"] else ""))
    if col["deriva"] == "sin historial":
        print("Deriva: el Dev MCP no da el historial de versiones; no se sabe si se han modificado en desarrollo")
    elif col["deriva"] == "sin fichero" and (m.raiz / "as-is").is_dir():
        print(f"Sin as-is/datos/deriva.json. Si el Dev MCP da el historial, solo de esos objetos:\n  {DX} deriva --out "
              f"\"<p>/as-is\" --objetos \"{','.join(col['corregidos'] + col['usan'])}\"")
    print(f"Colisión: {'sí' if col['choques'] else 'no'}")
    for c in col["choques"]:
        print(f"  {c}")
    print("→ " + ("«Dónde se corrige: Entorno de corrección» (igual que producción); cada unidad que cambia esos objetos "
                  "recibe en su encargo «reaplicar " + uid + "». Sin entorno de corrección, la ficha registra lo que "
                  "decide el equipo." if col["choques"] else
                  "«Dónde se corrige: Desarrollo»; esos objetos quedan congelados para las unidades en curso hasta el pase."))
    print(f"Escríbelo en «Colisión» y «Dónde se corrige» de impacto/{uid}.md.")


def donde_en_tecnico(m, objeto, fuentes=(), suyas=()):
    """Los apartados del técnico y las DT que nombran un objeto (sin Entorno, Convenciones ni §13; un record type, por su
    «### 3.n <nombre>»), y qué cambia en él con esta unidad: la «Decisión» de una DT de la unidad (de sus piezas o que
    cita una de sus fuentes) que lo nombra o, si no, una fila que lo nombra y cita una de sus fuentes; "" si no hay."""
    if "T" not in m.docs:
        return [], ""
    T, rx = m.docs["T"], re.compile(rf"`{re.escape(objeto)}(?:\(\))?`")
    secs, dts, fila = [], [], ""
    cita = lambda texto: any(re.search(rf"\b{x}\b", texto) for x in fuentes)
    for p in m.vigentes("DT"):
        if (p.id in suyas or cita(m.texto(p.id))) and rx.search(m.texto(p.id)):
            decision = mo.sin_comentarios(m.campos(p.id).get("decision", "")).replace("`", "").strip()
            fila = fila or (f"{p.id}: {decision}" if decision else "")
    for i, l in enumerate(T.lineas):
        s = T.seccion_de_linea[i]
        apartado = re.match(r"^###\s+([\d.]+)\s+(.+)$", l)
        if apartado and mo.normaliza(apartado.group(2).strip(" `")) == mo.normaliza(objeto):
            secs.append(f"§{apartado.group(1).rstrip('.')}")
            continue
        if s in ("0", "1", "13", "") or not rx.search(l):
            continue
        if s == "2":
            dt = next((p.id for p in m.vigentes("DT") if p.ini <= i < p.fin), None)
            dts += [dt] if dt else []
        else:
            secs.append(f"§{s}")
            if not fila and l.startswith("|") and cita(l):
                fila = " · ".join(c for c in mo.celdas(mo.sin_comentarios(l).replace("`", "")) if c.strip(" —-"))
    return list(dict.fromkeys(dts + secs)), fila[:140]


def c_encargo(m, a):
    """construccion/<U>.md: qué construir (por objeto, su situación, qué cambia y dónde está en el técnico), los puntos
    de «Cambio sobre lo construido», las pruebas, lo que hay que reaplicar y la orden de verificar; y
    construccion/<U>-esperado.json para verificar --esperado. Sin orden ni lista de cierre propios: los dan la skill
    oficial de Appian (change-planning) y las puertas de appian-best-practices. Se genera, no se edita."""
    ctx, uid = unidad(m, a.unidad)
    u = ctx.por_id[uid]
    if u.urgente:
        sys.exit(f"{uid} es una URG: se corrige con su ficha, impacto/{uid}.md (references/urgentes.md)")
    if u.estado not in (un.APROBADA, un.CONSTRUIDA):
        sys.exit(f"{uid} está {u.estado}: solo se construye una unidad aprobada "
                 f"(proyecto.py cambio <p> {uid} aprobada --fuente FU-nn)")
    crecida = ctx.crecida(uid)
    if crecida:   # lo añadido después de aprobarla no se construye sin aprobarlo (references/cambios.md)
        sys.exit(f"{uid} ha crecido desde que se aprobó ({'; '.join(crecida)}): vuelve a aprobarla "
                 f"(`proyecto.py cambio <p> {uid} aprobada --fuente FU-nn`) o lleva lo nuevo a otra unidad")
    filas = [f for f in ctx.filas_de(uid) if f["situacion"] in un.CAMBIAN]
    if not filas:
        sys.exit(f"Técnico §13 no tiene objetos de {uid} (columna «Cambio»): no hay nada que construir")
    r, esperado = ctx.resumen(uid), ctx.esperado(uid)
    inv = m.raiz / "as-is" / "datos" / "inventario.json"
    app = json.loads(inv.read_text(encoding="utf-8")).get("aplicacion", {}).get("nombre") if inv.is_file() else None
    if not app:
        fila0 = next((f for _, cab, fs in m.tablas("T", "0") for f in fs if f and mo.normaliza(f[0]) == "aplicacion"), None)
        app = (re.findall(r"`([^`]+)`", fila0[1]) or ["<aplicación>"])[0] if fila0 and len(fila0) > 1 else "<aplicación>"
    L = [f"# Encargo de construcción · {uid} · {u.titulo}", "",
         "<!-- Lo genera indice.py encargo a partir del análisis; no se edita: se vuelve a generar. -->", "",
         f"Unidad {uid} · {u.estado} ({u.aprobada}) · análisis {r['version']} · aplicación `{app}`", "",
         "Se construye solo esto. El orden lo da la skill oficial de Appian (`change-planning`) y las puertas, la "
         "calibración de `appian-best-practices`. Lo que hay que construir está en el técnico; aquí, dónde.", "",
         "## Objetos", "", "| Objeto | Tipo | Situación | Qué cambia | Dónde, en el técnico |", "|---|---|---|---|---|"]
    fuentes = sorted({x for n in r["informes"] for x in re.findall(r"FU-\d+", n)})
    for f in filas:
        for o in f["objetos"]:
            donde, fila = donde_en_tecnico(m, un.objeto(o), fuentes, ctx.piezas_de(uid))
            campos = esperado.get(un.objeto(o), {}).get("campos")
            secs = [x for x in donde if x.startswith("§")]
            que = (f"campos: {', '.join(c['nombre'] for c in campos)}" if campos else fila) or \
                (f"ver técnico {', '.join(secs)}" if secs else "—")
            sust = f" (sustituye a {', '.join(f['sustituye'])})" if f["sustituye"] else ""
            L.append(f"| `{o}` | {f['tipo']} | {f['situacion'].capitalize()}{sust} | {que.replace('|', '/')} | "
                     f"{', '.join(donde) or '—'} |")
    puntos = ctx.puntos_construido(uid)
    if puntos:
        dt = ctx.dt_construido(uid)
        campos = m.campos(dt.id) if dt else {}
        L += ["", f"## Cambio sobre lo construido ({dt.id if dt else 'sin DT: comprobar.py lo avisa'})", ""]
        L += [f"- **{p}** ({', '.join(o)}): {mo.sin_comentarios(campos.get(mo.normaliza(p), '')).strip() or 'falta en la DT'}"
              for p, o in puntos.items()]
    pr = r["pruebas"]
    L += ["", "## Pruebas (técnico §14)", "", f"- Criterios: {', '.join(pr['criterios']) or '—'}",
          f"- Escenarios: {', '.join(pr['escenarios']) or '—'}"]
    L += [f"- {g['id']} sobre {', '.join(g['objetos'])}: {g['prueba'] or 'su prueba en técnico §14'}" for g in pr["urgentes"]]
    if r["reaplicar"] or r["congelados"]:
        L += ["", "## Correcciones urgentes", ""]
        L += [f"- Reaplicar {t['urgente']} en {', '.join(f'`{o}`' for o in t['objetos'])}: la corrección se hizo en el "
              f"entorno de corrección; cuando su prueba pase en desarrollo, se confirma con `--reaplicada {t['urgente']}`"
              for t in r["reaplicar"]]
        L += [f"- No tocar {', '.join(f'`{o}`' for o in t['objetos'])} hasta el pase de {t['urgente']} (se corrige en "
              "desarrollo)" for t in r["congelados"]]
    otras = [c for c in r["colisiones"] if not c["unidad"].startswith("URG")]
    if otras:
        L += ["", "## Otras unidades sobre los mismos objetos", ""]
        L += [f"- {c['unidad']} ({c['estado']}): {', '.join(c['objetos'])} · {c['decision'] or 'sin decisión escrita'}"
              for c in otras]
    objetos = list(esperado)
    reap = "".join(f" --reaplicada {t['urgente']}" for t in r["reaplicar"])
    L += ["", "## Verificar y marcar", "",
          "Al terminar, solo lectura, con el atajo «Verificar» de `appian-reverse-engineering` (`<p>` es esta carpeta "
          "del proyecto; sin Dev MCP, `--manual`):", "", "```",
          f"{DX} verificar --app \"{app}\" --objetos \"{','.join(objetos)}\" --esperado \"<p>/construccion/{uid}-esperado.json\" "
          f"--out \"<p>/construccion/verificacion/{uid}.json\"",
          f"python3 <skill del analista>/scripts/proyecto.py cambio <p> {uid} construida{reap}", "```", ""]
    destino = m.raiz / "construccion" / f"{uid}.md"
    texto = "\n".join(L)
    destino.parent.mkdir(parents=True, exist_ok=True)
    esp = m.raiz / "construccion" / f"{uid}-esperado.json"
    nuevo_esp = json.dumps(esperado, ensure_ascii=False, indent=1) + "\n"
    cambia = [x for x, t in ((destino, texto), (esp, nuevo_esp))
              if not x.is_file() or x.read_text(encoding="utf-8") != t]
    for x, t in ((destino, texto), (esp, nuevo_esp)):
        if x in cambia:
            mo.escribe(x, t)
    print(f"{'Escrito' if cambia else 'Al día, sin cambios'}: construccion/{uid}.md y construccion/{uid}-esperado.json "
          f"({len(objetos)} objetos)")


def main():
    for s in (sys.stdout, sys.stderr):   # una consola en cp1252 no puede con «≥», «→» ni los estados
        s.reconfigure(encoding="utf-8", errors="replace")
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
    s.add_argument("--cambio", help="la unidad del informe (EV-02): no se sugiere «Requiere: Sí» por ella")
    s.add_argument("--con", nargs="+", help="solo dependencias cuyo texto menciona alguno de estos términos")
    s = nuevo("seccion", c_seccion); s.add_argument("n"); s.add_argument("--con", nargs="+")
    s.add_argument("--max", type=int, default=150)
    nuevo("siguientes", c_siguientes)
    s = nuevo("derivadas", c_derivadas); s.add_argument("--escribir", action="store_true")
    nuevo("pendientes", c_pendientes)
    s = nuevo("grafo", c_grafo); s.add_argument("-o", help="por defecto, analisis/grafo.json del proyecto")
    s = nuevo("cambios", c_cambios); s.add_argument("unidad"); s.add_argument("--json", action="store_true")
    s = nuevo("colision", c_colision); s.add_argument("unidad")
    s = nuevo("encargo", c_encargo); s.add_argument("unidad")
    a = ap.parse_args()
    m = mo.Proyecto(a.proyecto)
    if not m.docs:
        sys.exit(f"No encuentro funcional.md, tecnico.md ni decisiones.md en {m.analisis}")
    a.f(m, a)


if __name__ == "__main__":
    main()
