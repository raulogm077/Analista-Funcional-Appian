#!/usr/bin/env python3
"""Comprueba la coherencia de un ddf.md antes de entregarlo.

Uso:
  comprobar_ddf.py ddf.md [--fuentes fuentes/] [--corregir-citas]
  comprobar_ddf.py ddf.md --impacto impacto/FU-26.md --fuentes fuentes/           (informe listo, antes de aplicar)
  comprobar_ddf.py ddf.md --anterior ddf-v1.0.md [--impacto impacto/FU-26.md]   (tras aplicar)

Comprueba:
  - IDs definidos dos veces; criterios definidos más de una vez o citados sin existir;
  - RF vigentes sin criterio en «Se verifica en»;
  - piezas vigentes que remiten a una pieza anulada; IDs citados en cualquier parte que no están definidos;
  - con --fuentes: citas [FU-xx hh:mm:ss] cuyo minuto no es el de una intervención (--corregir-citas las
    lleva a la intervención anterior) y nombres de participantes que aparezcan en el documento;
  - con --anterior: ningún ID ha desaparecido (se tacha, no se borra), la versión sube y tiene su fila en
    el control de versiones; lista lo nuevo, lo modificado, lo anulado y los cambios de estado;
  - con --impacto sin --anterior (antes de aplicar): los IDs del informe existen y las citas del informe y
    de su nota son reales;
  - con --impacto y --anterior (después): cada dependencia tiene resultado, cada cambio está declarado,
    nada marcado «sin cambios» ha cambiado y lo 🔒 que cambia pasó por un punto aprobado.
Sale con 1 si hay algún problema.
"""
import argparse, bisect, collections, pathlib, re, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import ddf_modelo as dm

problemas = 0


def informe(nombre, lista, grave=True):
    global problemas
    mas = f" … y {len(lista) - 60} más" if len(lista) > 60 else ""
    print(("✓ " if not lista else ("✗ " if grave else "· ")) + nombre +
          ("" if not lista else f": {len(lista)} → {', '.join(map(str, lista[:60]))}{mas}"))
    if grave and lista:
        problemas += 1


def anulada(m, pid):
    p = m.piezas.get(pid)
    if not p:
        return False
    return p.anulada or (bool(p.padre) and m.piezas.get(p.padre) is not None and m.piezas[p.padre].anulada)


def comprobar_base(m):
    cnt = collections.Counter(p.tipo for p in m.piezas.values())
    print("  " + " · ".join(f"{t}: {cnt[t]}" for t in ["ACT", "PAN", "RF", "RB", "CA", "INT", "NOT", "P", "D"] if cnt[t]))
    secs = {mm.group(1) for l in m.lineas if (mm := dm.RX_SECCION.match(l))}
    informe("las 17 secciones, con título «## N. Título»", [str(n) for n in range(1, 18) if str(n) not in secs])
    informe("IDs definidos una sola vez", [f"{i} (l.{n})" for i, n in m.duplicados])
    texto = "\n".join(m.lineas)
    citados = {x for x in dm.ids_en(texto) if re.match(r"CA-(PAN|ACT|RF)-", x)}
    informe("criterios citados que existen", sorted(citados - set(m.piezas)))
    sin = []
    for p in m.por_tipo("RF"):
        if p.anulada:
            continue
        if "CA-" not in m.campo(p.id, "Se verifica en"):  # ficha vertical o fila de tabla con esa columna
            sin.append(p.id)
    informe("RF vigentes con criterio en «Se verifica en»", sorted(sin))
    malas = []
    for p in m.piezas.values():
        if anulada(m, p.id) or p.tipo == "D":
            continue
        for k, l in enumerate(m.bloque(p.id)):
            for r in dm.ids_en(l):
                if r != p.id and anulada(m, r) and f"~~{r}~~" not in l and "anulad" not in dm.normaliza(l):
                    malas.append(f"{p.id}→{r} (l.{p.ini + k + 1})")
    informe("ninguna pieza vigente remite a una anulada", sorted(set(malas)))
    rotas = collections.defaultdict(list)
    for k, l in enumerate(m.lineas):
        for r in dm.ids_en(l):
            if dm.tipo_de(r) in ("RF", "RB", "PAN", "ACT", "P", "D", "INT", "NOT") and r not in m.piezas:
                rotas[r].append(k + 1)
    informe("IDs citados que están definidos", sorted(f"{r} (l.{', '.join(map(str, ls[:3]))})" for r, ls in rotas.items()))


def comprobar_fuentes(m, carpeta, ruta, corregir):
    src, nombres, sin_nombres = {}, set(), []
    for f in pathlib.Path(carpeta).glob("FU-*.md"):
        txt = f.read_text(encoding="utf-8")
        src[f.name[3:5]] = sorted(set(re.findall(r"^\[(\d{2}:\d{2}:\d{2})\]", txt, re.M)))
        mm = re.search(r"Participantes: (.*)", txt)
        if mm:
            nombres |= {n.strip() for n in mm.group(1).split(";") if n.strip() and "identificad" not in n}
        # hablantes de las transcripciones con «[hh:mm:ss] Nombre Apellido:»
        nombres |= {n.strip() for n in re.findall(r"^\[\d{1,2}:\d{2}:\d{2}\] ([^:\n]{3,60}):\s*$", txt, re.M)}
        if not mm or "identificad" in mm.group(1):
            sin_nombres.append(f.name[:5])
    texto = "\n".join(m.lineas)
    malas = sorted({f"FU-{x} {y}" for x, y in re.findall(r"FU-(\d\d) (\d\d:\d\d:\d\d)", texto)
                    if src.get(x) and y not in src[x]})
    if malas and corregir:
        def arregla(mt):
            x, y = mt.group(1), mt.group(2)
            ts = src.get(x)
            if not ts or y in ts:
                return mt.group(0)
            k = bisect.bisect_right(ts, y) - 1
            return f"FU-{x} {ts[max(k, 0)]}"
        pathlib.Path(ruta).write_text(re.sub(r"FU-(\d\d) (\d\d:\d\d:\d\d)", arregla, texto), encoding="utf-8")
        print(f"· {len(malas)} citas llevadas a la intervención anterior: {malas[:10]}")
    else:
        informe("citas con minuto de una intervención real", malas)
    informe("sin nombres de participantes", sorted(n for n in nombres if n in texto))
    if sin_nombres:
        print(f"· {', '.join(sorted(sin_nombres))}: sin participantes identificados en la fuente; "
              "revisa a mano que el documento no cite a personas por su nombre (roles, no personas)")


def comprobar_anterior(m, ruta_ant):
    ant = dm.cargar(ruta_ant)
    va, vn = ant.version(), m.version()
    print(f"  versión anterior v{va[0]}.{va[1]} → nueva v{vn[0]}.{vn[1]}" if va and vn else "  versión: ¿?")
    informe("la versión sube", [] if (va and vn and vn > va) else [f"{va} → {vn}"])
    if vn:
        fila = re.search(rf"^\|\s*v?{vn[0]}\.{vn[1]}\s*\|", "\n".join(m.lineas[:120]), re.M)
        informe("la versión nueva tiene su fila en el control de versiones", [] if fila else [f"v{vn[0]}.{vn[1]}"])
    informe("ningún ID ha desaparecido (lo que ya no vale se tacha)",
            sorted(i for i in ant.piezas if i not in m.piezas))
    # las capturas del prototipo que se añaden a las fichas (![pie](…png)) no son un cambio funcional
    norm = lambda s: re.sub(r"\s+", " ", re.sub(r"(?m)^.*!\[[^\]]*\]\([^)]+\.png\).*$|^\*\*Capturas\*\*.*$", "", s)).strip()
    nuevas = sorted(i for i in m.piezas if i not in ant.piezas)
    comunes = [i for i in m.piezas if i in ant.piezas]
    modif = sorted(i for i in comunes if norm(m.texto(i)) != norm(ant.texto(i)))
    anul = sorted(i for i in comunes if m.piezas[i].anulada and not ant.piezas[i].anulada)
    estado = sorted(f"{i} {ant.piezas[i].estado or '—'}→{m.piezas[i].estado or '—'}" for i in comunes
                    if m.piezas[i].estado != ant.piezas[i].estado and i not in anul)
    dentro = []
    for i in modif:
        a_, n_ = ant.texto(i), m.texto(i)
        d = [f"{e}{n_.count(e) - a_.count(e):+d}" for e in dm.ESTADOS if n_.count(e) != a_.count(e)]
        if d:
            dentro.append(f"{i} ({' '.join(d)})")
    informe("nuevas", nuevas, grave=False)
    informe("modificadas", modif, grave=False)
    informe("anuladas o respondidas en esta versión", anul, grave=False)
    informe("cambios de estado", estado, grave=False)
    informe("marcas de estado que cambian dentro de las piezas", dentro, grave=False)
    return nuevas, modif, anul


def lee_informe(ruta):
    """Tablas del informe de impacto: puntos (con «Revisar también») y revisión de dependencias."""
    t = pathlib.Path(ruta).read_text(encoding="utf-8")
    puntos, revision, cab = [], [], None
    for l in t.split("\n"):
        if not l.startswith("|"):
            cab = None
            continue
        c = [x.strip() for x in l.strip().strip("|").split("|")]
        if cab is None:
            cab = [dm.normaliza(x) for x in c]
            continue
        if re.match(r"^[-:\s]+$", c[0]):
            continue
        fila = {k: (c[i] if i < len(c) else "") for i, k in enumerate(cab)}
        if "revisar tambien" in cab:
            puntos.append(fila)
        elif cab[0] == "pieza" and "resultado" in cab:
            revision.append(fila)
    return t, puntos, revision


def comprobar_informe_previo(m, ruta_imp, carpeta_fuentes):
    """Antes de aplicar: los IDs del informe existen (o se declaran nuevos) y las citas son reales."""
    t, puntos, revision = lee_informe(ruta_imp)
    en_revision = set()
    for f in revision:
        en_revision |= {m.raiz(x) for x in dm.ids_en(f.get("pieza", ""))}
    faltan = set()
    for f in puntos:
        if "✗" not in f.get("decision", ""):
            faltan |= {m.raiz(x) for x in dm.ids_en(f.get("revisar tambien", "")) if x in m.piezas}
    informe("cada pieza de «Revisar también» tiene su fila en «Revisión de dependencias»", sorted(faltan - en_revision))
    # un ID que no existe vale si es una pieza nueva: continúa la numeración (el anterior existe o también es
    # nuevo en el informe, como da `ddf_indice.py siguientes`); si no, es una errata
    candidatos = set()
    for f in puntos:
        for col in ("encaja en", "cambio propuesto", "revisar tambien"):
            candidatos |= {x for x in dm.ids_en(f.get(col, "")) if x not in m.piezas}
    candidatos |= {x for x in dm.ids_en(t) if x not in m.piezas and dm.tipo_de(x) != "CA"}
    aceptados, cambio = set(), True
    while cambio:
        cambio = False
        for x in candidatos - aceptados:
            if dm.tipo_de(x) == "CA":
                ok = re.sub(r"^CA-|\.\d+$", "", x) in m.piezas or re.sub(r"^CA-|\.\d+$", "", x) in aceptados
            else:
                pre, num = x.rsplit("-", 1)
                ant = f"{pre}-{int(num) - 1:0{len(num)}d}"
                ok = ant in m.piezas or ant in aceptados
            if ok:
                aceptados.add(x)
                cambio = True
    inexistentes = [x for x in dm.ids_en(t) if x not in m.piezas and x not in aceptados]
    informe("los IDs del informe existen o son nuevos que continúan la numeración", sorted(set(inexistentes)))
    if carpeta_fuentes:
        mfu = re.search(r"FU-(\d\d)", pathlib.Path(ruta_imp).name)
        textos = [t]
        if mfu:
            nota = pathlib.Path(ruta_imp).parent.parent / "notas" / f"FU-{mfu.group(1)}.md"
            if nota.exists():
                textos.append(nota.read_text(encoding="utf-8"))
        src = {f.name[3:5]: set(re.findall(r"^\[(\d{2}:\d{2}:\d{2})\]", f.read_text(encoding="utf-8"), re.M))
               for f in pathlib.Path(carpeta_fuentes).glob("FU-*.md")}
        malas = sorted({f"FU-{x} {y}" for tx in textos for x, y in re.findall(r"FU-(\d\d) (\d\d:\d\d:\d\d)", tx)
                        if src.get(x) and y not in src[x]})
        informe("citas del informe y de la nota con minuto de una intervención real", malas)
        if mfu and src.get(mfu.group(1)):
            # toda la reunión leída: cada tramo de 10 minutos con conversación tiene alguna cita
            seg = lambda h: sum(int(x) * f for x, f in zip(h.split(":"), (3600, 60, 1))) // 600
            habla = collections.Counter(seg(h) for h in src[mfu.group(1)])
            citado = {seg(y) for tx in textos for x, y in re.findall(r"FU-(\d\d) (\d\d:\d\d:\d\d)", tx) if x == mfu.group(1)}
            huecos = [f"{s * 10:02d}–{s * 10 + 10:02d} min ({n} intervenciones)" for s, n in sorted(habla.items())
                      if n >= 5 and s not in citado]
            informe("cada tramo de 10 minutos de la reunión tiene alguna cita (también los SIN IMPACTO)", huecos)


def comprobar_impacto(m, ant, ruta_imp, cambios):
    t, puntos, revision = lee_informe(ruta_imp)
    declarados = dm.ids_en(t)
    revisar, resueltos, sin_cambios = set(), set(), set()
    for f in puntos:
        if "✗" not in f.get("decision", ""):
            revisar |= dm.ids_en(f.get("revisar tambien", ""))
    for f in revision:
        res = dm.normaliza(f.get("resultado", ""))
        ids = {m.raiz(x) for x in dm.ids_en(f.get("pieza", ""))}
        if res and "pendiente" not in res:
            resueltos |= ids
        if "sin cambios" in res:
            sin_cambios |= ids
    revisar = {m.raiz(x) for x in revisar}
    informe("cada dependencia del informe de impacto tiene resultado", sorted(revisar - resueltos))
    # «declarado como cambio»: en «Cambio propuesto» de un punto aplicado, en una fila de revisión
    # cuyo resultado no es «sin cambios», o en el apartado «Aplicado»
    cambio_decl = set()
    for f in puntos:
        if "✗" in f.get("decision", ""):
            continue
        cambio_decl |= dm.ids_en(f.get("cambio propuesto", ""))
    for f in revision:
        if "sin cambios" not in dm.normaliza(f.get("resultado", "")):
            cambio_decl |= dm.ids_en(f.get("pieza", "")) | dm.ids_en(f.get("resultado", ""))
    ma = re.search(r"^## Aplicado\s*$(.*?)(?=^## |\Z)", t, re.M | re.S)
    if ma:
        cambio_decl |= dm.ids_en(ma.group(1))
    cambio_decl |= {m.raiz(x) for x in cambio_decl}
    nuevas, modif, anul = cambios
    no_decl = [i for i in set(nuevas) | set(modif) | set(anul) if i not in cambio_decl and m.raiz(i) not in cambio_decl]
    informe("cada cambio está declarado en el informe («Cambio propuesto», revisión con cambios o «Aplicado»)", sorted(no_decl))
    marcadas = sorted(i for i in (set(modif) | set(anul)) if m.raiz(i) in sin_cambios and i not in cambio_decl
                      and m.raiz(i) not in cambio_decl)
    informe("nada marcado «sin cambios» ha cambiado", marcadas)
    con_aprobacion = set()
    for f in puntos:
        req = dm.normaliza(f.get("requiere", ""))
        if req and req not in ("—", "-", "no") and "✔" in f.get("decision", "") + "✔" * ("✗" not in f.get("decision", "") and "⚠" not in f.get("decision", "")):
            for col in ("encaja en", "cambio propuesto"):
                con_aprobacion |= {m.raiz(x) for x in dm.ids_en(f.get(col, ""))}
    pierden = sorted(i for i in m.piezas if i in ant.piezas and ant.piezas[i].estado == "🔒"
                     and m.piezas[i].estado != "🔒" and m.raiz(i) not in con_aprobacion and i not in con_aprobacion)
    informe("lo 🔒 que cambia pasó por aprobación (punto con «Requiere» aprobado)", pierden)


def main():
    if hasattr(__import__("signal"), "SIGPIPE"):
        import signal
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    for s in (sys.stdout, sys.stderr):
        s.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ddf")
    ap.add_argument("--fuentes")
    ap.add_argument("--corregir-citas", action="store_true")
    ap.add_argument("--anterior")
    ap.add_argument("--impacto")
    a = ap.parse_args()
    m = dm.cargar(a.ddf)
    comprobar_base(m)
    if a.fuentes:
        comprobar_fuentes(m, a.fuentes, a.ddf, a.corregir_citas)
    if a.anterior:
        cambios = comprobar_anterior(m, a.anterior)
        if a.impacto:
            comprobar_impacto(m, dm.cargar(a.anterior), a.impacto, cambios)
    elif a.impacto:
        print("  (informe de impacto antes de aplicar: sin --anterior solo se revisan IDs y citas)")
        comprobar_informe_previo(m, a.impacto, a.fuentes)
    print("\nSin problemas." if not problemas else f"\n{problemas} comprobaciones con problemas.")
    sys.exit(1 if problemas else 0)


if __name__ == "__main__":
    main()
