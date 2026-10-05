#!/usr/bin/env python3
"""Comprueba el análisis de un proyecto antes de entregarlo.

Uso (<p> es la carpeta del proyecto o su carpeta analisis/):
  comprobar.py <p> [--fuentes fuentes/] [--corregir-citas]
  comprobar.py <p> --impacto impacto/FU-04.md --fuentes fuentes/        informe listo, antes de aplicar
  comprobar.py <p> --anterior versiones/v1.1 [--impacto impacto/FU-04.md]   después de aplicar

Errores (✗, salida 1) y avisos (·):
  - estructura: los apartados de cada fichero con su número;
  - IDs: definidos una vez y en su sitio, citados solo si existen, ninguna pieza vigente remite a una anulada;
  - completo: historias con perfil, pantalla, prioridad y criterios; pantallas con sus partes y captura;
    pasos con quién y pantalla; pendientes con a quién preguntar;
  - DF limpio: sin fuentes, marcas de estado ni términos de Appian a la vista, comentarios cerrados;
  - redacción (avisos): muletillas de references/redaccion.md, frases largas o repetidas, palabras vagas sin cifra;
  - funcional ↔ técnico, si hay tecnico.md: cada dato del DF con su campo y viceversa, cada pantalla, aviso,
    relación con otro sistema, perfil y criterio en su apartado técnico, decisiones con su porqué y su
    verificación, y la misma versión en los tres ficheros;
  - con --fuentes: citas con el minuto de una intervención real y sin nombres de participantes;
  - con --anterior: ningún ID desaparece, la versión sube y tiene su fila; lista lo nuevo y lo cambiado;
  - con --impacto: los IDs del informe existen o son nuevos; después de aplicar, cada dependencia tiene
    resultado, cada cambio está declarado y lo 🔒 solo cambia con aprobación.
"""
import argparse
import bisect
import collections
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import modelo as mo

SKILL = pathlib.Path(__file__).resolve().parents[1]
SECCIONES = {"F": [str(n) for n in range(1, 12)], "T": [str(n) for n in range(0, 16)], "D": ["versiones", "decisiones"]}
PRIORIDADES = ("imprescindible", "deseable")
TIPOS_D = ("CAMBIA", "ANULA", "VALIDA", "RESPONDE", "ALCANCE+", "ALCANCE−", "ALCANCE-")
TERMINOS_APPIAN = [r"record types?", r"record lists?", r"process models?", r"\bsail\b", r"expression rules?",
                   r"reglas? de expresi[oó]n", r"smart services?", r"data stores?", r"\bcdts?\b", r"\ba![a-z]\w*",
                   r"appian designer", r"record actions?", r"interface objects?", r"\bdesigner\b"]
VAGAS = ["rápido", "rápidamente", "pronto", "en breve", "periódicamente", "frecuentemente", "a tiempo", "muchos",
         "muchas", "varios", "varias", "gran volumen", "gran cantidad"]

errores = 0


def informe(nombre, lista, grave=True):
    global errores
    mas = f" … y {len(lista) - 40} más" if len(lista) > 40 else ""
    print(("✓ " if not lista else ("✗ " if grave else "· ")) + nombre +
          ("" if not lista else f": {len(lista)} → {', '.join(map(str, lista[:40]))}{mas}"))
    if grave and lista:
        errores += 1


def anulada(m, pid):
    p = m.piezas.get(pid)
    if not p:
        return False
    return p.anulada or (bool(p.padre) and m.piezas.get(p.padre) is not None and m.piezas[p.padre].anulada)


def visible(l):
    """Texto de una línea sin comentarios, enlaces de imagen ni código."""
    l = mo.sin_comentarios(l)
    l = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", l)
    return re.sub(r"`[^`]*`", "", l)


def nombres(texto):
    return [x.strip() for x in re.split(r",| y |;|/", mo.sin_comentarios(texto)) if x.strip()]


def clave_pid(pid):
    return (mo.tipo_de(pid), [int(x) for x in re.findall(r"\d+", pid)])


# ------------------------------------------------------------------ estructura e IDs
def comprobar_estructura(m):
    for d, esperadas in SECCIONES.items():
        if d not in m.docs:
            if d == "F":
                informe("existe funcional.md", ["falta"])
            continue
        hay = {s[0] for s in m.docs[d].secciones}
        faltan = [s for s in esperadas if s not in hay and not any(h.startswith(s) for h in hay if not h.isdigit())]
        informe(f"{mo.DOCS[d]}: apartados con su título («## N. Título»)", faltan)


def comprobar_ids(m):
    cnt = collections.Counter(p.tipo for p in m.piezas.values() if not p.anulada)
    print("  " + " · ".join(f"{t}: {cnt[t]}" for t in mo.TIPOS if cnt[t]))
    informe("IDs definidos una sola vez", [f"{i} ({mo.DOCS[d]} l.{n})" for i, d, n in m.duplicados])
    informe("cada ficha o fila con ID está en su apartado (si no, es una cita y no debe abrir ficha o fila)",
            [f"{i} ({mo.DOCS[d]} l.{n + 1})" for i, d, n in m.fuera_de_casa])
    rotas = collections.defaultdict(list)
    for d, D in m.docs.items():
        for k, l in enumerate(D.lineas):
            for r in mo.ids_en(mo.sin_comentarios(l)):
                if r not in m.piezas:
                    rotas[r].append(f"{d}{k + 1}")
    informe("IDs citados que existen", sorted(f"{r} ({', '.join(v[:3])})" for r, v in rotas.items()))
    malas = []
    for p in m.piezas.values():
        if anulada(m, p.id) or p.tipo == "D":
            continue
        for k, l in enumerate(m.bloque(p.id)):
            for r in mo.ids_en(mo.sin_comentarios(l)):
                if r != p.id and anulada(m, r) and f"~~{r}~~" not in l and not re.search(r"anulad|respondid", mo.normaliza(l)):
                    malas.append(f"{p.id}→{r}")
    informe("ninguna pieza vigente remite a una anulada", sorted(set(malas)))


# ------------------------------------------------------------------ completo
def perfiles(m):
    for _, cab, filas in m.tablas("F", "2"):
        if cab and mo.normaliza(cab[0]) == "perfil":
            return [f[0] for f in filas if f and f[0]]
    return []


def comprobar_completo(m):
    pf = {mo.normaliza(x) for x in perfiles(m)}
    informe("funcional §2: tabla de perfiles («| Perfil | …»)", [] if pf else ["falta"])
    sin_campos, perfil_mal, pan_mal, prio_mal, sin_ca, sin_como = [], [], [], [], [], []
    usados = set()
    for p in m.vigentes("HU"):
        c = m.campos(p.id)
        if not all(c.get(k) for k in ("perfil", "pantalla", "prioridad")):
            sin_campos.append(p.id)
            continue
        for x in nombres(c["perfil"]):
            usados.add(mo.normaliza(x))
            if pf and mo.normaliza(x) not in pf:
                perfil_mal.append(f"{p.id} «{x}»")
        if c["pantalla"].strip() not in ("—", "-") and not mo.ids_en(c["pantalla"]):
            pan_mal.append(p.id)
        if mo.normaliza(c["prioridad"]) not in PRIORIDADES:
            prio_mal.append(f"{p.id} «{c['prioridad']}»")
        if not [h for h in p.hijos if not anulada(m, h)]:
            sin_ca.append(p.id)
        if not re.search(r"^Como .+ quiero .+ para ", m.texto(p.id), re.M):
            sin_como.append(p.id)
    informe("historias con la tabla Perfil · Pantalla · Paso · Prioridad", sin_campos)
    informe("perfiles de las historias que están en §2", perfil_mal)
    informe("pantalla de cada historia: PAN-nn o —", pan_mal)
    informe("prioridad «Imprescindible» o «Deseable»", prio_mal)
    informe("historias con criterios («Se acepta si:»)", sin_ca)
    informe("historias con «Como… quiero… para…»", sin_como, grave=False)
    informe("perfiles de §2 que tienen alguna historia", sorted(x for x in perfiles(m) if mo.normaliza(x) not in usados),
            grave=False)

    sin_partes, sin_captura, sin_hu = [], [], []
    hu_de_pan = collections.defaultdict(set)
    for h in m.vigentes("HU"):
        for x in mo.ids_en(m.campos(h.id).get("pantalla", "")):
            hu_de_pan[x].add(h.id)
    for p in m.vigentes("PAN"):
        txt = m.texto(p.id)
        if not re.search(r"^\|\s*Parte\s*\|", txt, re.M):
            sin_partes.append(p.id)
        if not re.search(r"!\[[^\]]*\]\([^)]+\)", txt):
            sin_captura.append(p.id)
        if not hu_de_pan.get(p.id):
            sin_hu.append(p.id)
    informe("pantallas con la tabla Parte · Qué permite · Quién", sin_partes)
    informe("pantallas con su captura del prototipo", sin_captura, grave=False)
    informe("pantallas que son la pantalla de alguna historia", sin_hu, grave=False)

    sin_quien, sin_hu_act = [], []
    pasos_con_hu = {x for h in m.vigentes("HU") for x in mo.ids_en(m.campos(h.id).get("paso", ""))}
    for p in m.vigentes("ACT"):
        c = m.campos(p.id)
        if not c.get("quien") or not c.get("pantalla"):
            sin_quien.append(p.id)
        elif mo.ids_en(c["pantalla"]) and p.id not in pasos_con_hu:
            sin_hu_act.append(p.id)
    informe("pasos con Quién y Pantalla", sin_quien)
    informe("pasos con pantalla que son el paso de alguna historia", sin_hu_act, grave=False)

    pc_mal = []
    for p in m.vigentes("PC"):
        cab = [mo.normaliza(x) for x in mo.celdas(p.cabecera)]
        cel = mo.celdas(m.docs["F"].lineas[p.ini])
        if "a quien" in cab and not mo.sin_comentarios(cel[cab.index("a quien")] if cab.index("a quien") < len(cel) else "").strip(" —-"):
            pc_mal.append(p.id)
    informe("pendientes de confirmar con «A quién»", pc_mal)
    d_mal = []
    for p in m.por_tipo("D"):
        cab = [mo.normaliza(x) for x in mo.celdas(p.cabecera)]
        cel = mo.celdas(m.docs["D"].lineas[p.ini])
        if "tipo" in cab and cab.index("tipo") < len(cel) and cel[cab.index("tipo")].strip() not in TIPOS_D:
            d_mal.append(f"{p.id} «{cel[cab.index('tipo')]}»")
    informe("decisiones con tipo CAMBIA, ANULA, VALIDA, RESPONDE o ALCANCE±", d_mal)


# ------------------------------------------------------------------ DF limpio y redacción
def lineas_prosa(m, d):
    """(número, texto visible) de las líneas de un fichero que se leen: sin títulos, código ni anexo."""
    D = m.docs[d]
    en_codigo = False
    for i, l in enumerate(D.lineas):
        if l.startswith("```"):
            en_codigo = not en_codigo
            continue
        if en_codigo or l.startswith("#") or D.seccion_de_linea[i] == "anexo" or re.match(r"^\|[\s:|-]+\|?\s*$", l):
            continue
        yield i, visible(l)


def comprobar_limpieza(m):
    if "F" not in m.docs:
        return
    fuentes, marcas, appian, abiertos = [], [], [], []
    texto = "\n".join(m.docs["F"].lineas)
    if texto.count("<!--") != texto.count("-->"):
        abiertos.append(f"{texto.count('<!--')} aperturas y {texto.count('-->')} cierres")
    for i, l in lineas_prosa(m, "F"):
        if mo.RX_FUENTE.search(l):
            fuentes.append(f"l.{i + 1}")
        if any(e in l for e in mo.ESTADOS):
            marcas.append(f"l.{i + 1}")
        for t in TERMINOS_APPIAN:
            mt = re.search(t, mo.normaliza(l))
            if mt:
                appian.append(f"l.{i + 1} «{mt.group(0)}»")
    informe("DF: comentarios <!-- --> cerrados", abiertos)
    informe("DF: fuentes (FU-) solo dentro de comentarios", fuentes)
    informe("DF: marcas de estado solo dentro de comentarios", marcas)
    informe("DF: sin términos de Appian (van en el técnico)", appian)


def muletillas():
    f = SKILL / "references" / "redaccion.md"
    if not f.exists():
        return []
    return [mo.normaliza(x) for x in re.findall(r"^- «([^»]+)» →", f.read_text(encoding="utf-8"), re.M)]


def frases(texto):
    texto = re.sub(r"\*\*|~~|\||https?://\S+", " ", texto)
    return [f.strip() for f in re.split(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÑ«¿])", texto) if f.strip()]


def comprobar_redaccion(m):
    lista = muletillas()
    for d in ("F", "T"):
        if d not in m.docs:
            continue
        mul, largas, vagas = [], [], []
        vistas = collections.defaultdict(list)
        for i, l in lineas_prosa(m, d):
            nl = mo.normaliza(l)
            for x in lista:
                if re.search(rf"(?<!\w){re.escape(x)}(?!\w)", nl):
                    mul.append(f"l.{i + 1} «{x}»")
            celdas = mo.celdas(l) if l.startswith("|") else [l]
            for c in celdas:
                for f in frases(c):
                    pal = re.findall(r"\w+", f)
                    if len(pal) > 35:
                        largas.append(f"l.{i + 1} ({len(pal)} palabras)")
                    if d == "F":
                        nf = mo.normaliza(f)
                        propias = re.findall(r"\w+", mo.RX_ID.sub(" ", nf).replace("pan-", " "))
                        if len([w for w in propias if not w.isdigit()]) >= 10:  # una lista de IDs no es una frase
                            vistas[" ".join(re.findall(r"\w+", nf))].append(i + 1)
                        if not re.search(r"\d", f):
                            for v in VAGAS:
                                if re.search(rf"(?<!\w){re.escape(mo.normaliza(v))}(?!\w)", nf):
                                    vagas.append(f"l.{i + 1} «{v}»")
        n = mo.DOCS[d]
        informe(f"{n}: sin muletillas (references/redaccion.md)", mul, grave=False)
        informe(f"{n}: frases de 35 palabras o menos", largas, grave=False)
        if d == "F":
            informe(f"{n}: palabras vagas con su cifra", vagas, grave=False)
            rep = [f"l.{', '.join(map(str, v[:3]))} «{k[:50]}…»" for k, v in vistas.items() if len(v) > 1]
            informe(f"{n}: ninguna frase escrita dos veces", rep, grave=False)


# ------------------------------------------------------------------ funcional ↔ técnico
def datos_df(m):
    """{(entidad, dato normalizado): dato} de las tablas «| Dato | …» de funcional §6."""
    out = {}
    D = m.docs["F"]
    rango = D.seccion("6")
    if not rango:
        return out
    entidad = ""
    for i in range(*rango):
        l = D.lineas[i]
        if l.startswith("### "):
            entidad = re.sub(r"^###\s+[\d.]*\s*", "", l).strip()
    for ini, cab, filas in m.tablas("F", "6"):
        if cab and mo.normaliza(cab[0]) == "dato":
            ent = next((re.sub(r"^###\s+[\d.]*\s*", "", D.lineas[k]).strip() for k in range(ini, rango[0], -1)
                        if D.lineas[k].startswith("### ")), "")
            for f in filas:
                if f and f[0]:
                    out[(mo.normaliza(ent), mo.normaliza(mo.sin_comentarios(f[0])))] = f"{ent} · {f[0]}"
    return out


def comprobar_tecnico(m):
    empezado = "T" in m.docs and (bool(m.vigentes("DT")) or any(
        "campo" in [mo.normaliza(c) for c in cab] for _, cab, _ in m.tablas("T", "3")))
    if not empezado:
        print("· técnico: sin empezar (sin decisiones ni modelo de datos); se comprueba cuando lo esté")
        return
    T = m.docs["T"]
    # datos ↔ campos
    df = datos_df(m)
    nombres_df = {k[1] for k in df}
    usados, sin_uso, sin_dato = set(), [], []
    for ini, cab, filas in m.tablas("T", "3"):
        ncab = [mo.normaliza(c) for c in cab]
        if "campo" not in ncab or "uso" not in ncab:
            continue
        iu = ncab.index("uso")
        for f in filas:
            uso = f[iu] if iu < len(f) else ""
            nu = mo.normaliza(uso)
            if nu.startswith("funcional"):
                for x in nombres(uso.split(":", 1)[1] if ":" in uso else ""):
                    usados.add(mo.normaliza(x))
                    if mo.normaliza(x) not in nombres_df:
                        sin_dato.append(f"{f[0]} → «{x}»")
            elif not nu.startswith("tecnico"):
                sin_uso.append(f[0])
    informe("técnico §3: cada campo con «Uso: Funcional: <dato del DF>» o «Técnico: para qué»", sin_uso)
    informe("técnico §3: los campos funcionales remiten a un dato de funcional §6", sin_dato)
    informe("funcional §6: cada dato tiene su campo en técnico §3",
            sorted(v for k, v in df.items() if k[1] not in usados))

    def falta_en(seccion, ids):
        rango = T.seccion(seccion)
        texto = "\n".join(T.lineas[rango[0]:rango[1]]) if rango else ""
        citados = mo.ids_en(texto)
        return sorted((x for x in ids if x not in citados), key=clave_pid)
    informe("técnico §7: cada pantalla", falta_en("7", [p.id for p in m.vigentes("PAN")]))
    informe("técnico §9: cada aviso", falta_en("9", [p.id for p in m.vigentes("AV")]))
    informe("técnico §10: cada relación con otro sistema", falta_en("10", [p.id for p in m.vigentes("INT")]))
    informe("técnico §14: cada criterio de aceptación",
            falta_en("14", [p.id for p in m.por_tipo("CA") if not anulada(m, p.id)]))
    informe("técnico §14: cada escenario", falta_en("14", [p.id for p in m.vigentes("ESC")]), grave=False)
    r4 = T.seccion("4")
    t4 = mo.normaliza("\n".join(T.lineas[r4[0]:r4[1]])) if r4 else ""
    informe("técnico §4: cada perfil con su grupo", [x for x in perfiles(m) if mo.normaliza(x) not in t4])
    # decisiones técnicas
    sin_porque, sin_verif, sin_verificado = [], [], []
    for p in m.vigentes("DT"):
        c = m.campos(p.id)
        if not re.search(r"\bBP \d|https?://", c.get("por que", "")):
            sin_porque.append(p.id)
        dep = c.get("depende de", "").strip(" —-")
        if dep and not c.get("verificar", "").strip(" —-"):
            sin_verif.append(p.id)
        if not c.get("verificado", "").strip():
            sin_verificado.append(p.id)
    informe("decisiones técnicas con «Por qué» (BP nn §x o URL de la documentación)", sin_porque)
    informe("decisiones que dependen de versión, tier u otra cosa, con «Verificar»", sin_verif, grave=False)
    informe("decisiones técnicas con «Verificado» (fuente o «pendiente»)", sin_verificado)
    entorno = [f for _, cab, filas in m.tablas("T", "0") for f in filas]
    version_appian = [f for f in entorno if f and "version de appian" in mo.normaliza(f[0])]
    informe("técnico §0: versión de Appian", [] if version_appian and version_appian[0][1].strip(" —-") else ["falta"],
            grave=False)


def comprobar_versiones(m):
    vf, vt = m.version("F"), m.version("T")
    filas = [f for _, cab, fs in m.tablas("D", "versiones") for f in fs if f]
    ultima = None
    if filas:
        mm = re.match(r"v?(\d+)\.(\d+)", filas[-1][0])
        ultima = (int(mm.group(1)), int(mm.group(2))) if mm else None
    malas = []
    if not vf:
        malas.append("funcional sin «Versión: x.y»")
    if vt and vt != vf and (m.vigentes("DT") or any("campo" in [mo.normaliza(c) for c in cab] for _, cab, _ in m.tablas("T", "3"))):
        malas.append(f"técnico {vt[0]}.{vt[1]} ≠ funcional")
    if "D" in m.docs and ultima != vf:
        malas.append(f"última fila de Versiones {ultima} ≠ funcional {vf}")
    informe("misma versión en funcional, técnico y la última fila de Versiones", malas)


# ------------------------------------------------------------------ fuentes
def comprobar_fuentes(m, carpeta, corregir):
    src, gente, sin_gente = {}, set(), []
    for f in pathlib.Path(carpeta).glob("FU-*.md"):
        txt = f.read_text(encoding="utf-8")
        num = re.match(r"FU-(\d+)", f.name).group(1)
        src[num] = sorted(set(re.findall(r"^\[(\d{2}:\d{2}:\d{2})\]", txt, re.M)))
        mm = re.search(r"Participantes: (.*)", txt)
        if mm:
            gente |= {n.strip() for n in mm.group(1).split(";") if n.strip() and "identificad" not in n}
        gente |= {n.strip() for n in re.findall(r"^\[\d{1,2}:\d{2}:\d{2}\] ([^:\n]{3,60}):\s*$", txt, re.M)}
        if not mm or "identificad" in mm.group(1):
            sin_gente.append(f.name[:5])
    rx = re.compile(r"FU-(\d+) (\d\d:\d\d:\d\d)")
    malas = []
    for d, D in m.docs.items():
        texto = "\n".join(D.lineas)
        malas += [f"FU-{x} {y}" for x, y in rx.findall(texto) if src.get(x) and y not in src[x]]
        if corregir and malas:
            def arregla(mt):
                x, y = mt.group(1), mt.group(2)
                ts = src.get(x)
                if not ts or y in ts:
                    return mt.group(0)
                return f"FU-{x} {ts[max(bisect.bisect_right(ts, y) - 1, 0)]}"
            m.ruta(d).write_text(rx.sub(arregla, texto), encoding="utf-8")
    if corregir and malas:
        print(f"· {len(set(malas))} citas llevadas a la intervención anterior: {sorted(set(malas))[:10]}")
    else:
        informe("citas con el minuto de una intervención real", sorted(set(malas)))
    todo = "\n".join("\n".join(D.lineas) for D in m.docs.values())
    informe("sin nombres de participantes", sorted(n for n in gente if n in todo))
    if sin_gente:
        print(f"· {', '.join(sorted(sin_gente))}: sin participantes identificados; revisa a mano que no salgan nombres")


# ------------------------------------------------------------------ versión anterior e impacto
def normaliza_pieza(t):
    t = re.sub(r"(?m)^.*!\[[^\]]*\]\([^)]+\.png\).*$", "", t)  # las capturas no son un cambio funcional
    return re.sub(r"\s+", " ", t).strip()


def comprobar_anterior(m, ruta_ant):
    ant = mo.Proyecto(ruta_ant)
    if not ant.docs:
        informe("la versión anterior existe", [str(ruta_ant)])
        return [], [], [], ant
    va, vn = ant.version("F"), m.version("F")
    print(f"  versión anterior {va[0]}.{va[1]} → nueva {vn[0]}.{vn[1]}" if va and vn else "  versión: ¿?")
    informe("la versión sube", [] if (va and vn and vn > va) else [f"{va} → {vn}"])
    informe("ningún ID ha desaparecido (lo que ya no vale se tacha)",
            sorted((i for i in ant.piezas if i not in m.piezas), key=clave_pid))
    nuevas = sorted((i for i in m.piezas if i not in ant.piezas), key=clave_pid)
    comunes = [i for i in m.piezas if i in ant.piezas]
    modif = sorted((i for i in comunes if normaliza_pieza(m.texto(i)) != normaliza_pieza(ant.texto(i))), key=clave_pid)
    anul = sorted((i for i in comunes if m.piezas[i].anulada and not ant.piezas[i].anulada), key=clave_pid)
    estado = [f"{i} {ant.piezas[i].estado or '—'}→{m.piezas[i].estado or '—'}" for i in comunes
              if m.piezas[i].estado != ant.piezas[i].estado and i not in anul]
    informe("nuevas", nuevas, grave=False)
    informe("modificadas", modif, grave=False)
    informe("anuladas o respondidas en esta versión", anul, grave=False)
    informe("cambios de estado", estado, grave=False)
    return nuevas, modif, anul, ant


def lee_informe(ruta):
    t = pathlib.Path(ruta).read_text(encoding="utf-8")
    puntos, revision, cab = [], [], None
    for l in t.split("\n"):
        if not l.startswith("|"):
            cab = None
            continue
        c = mo.celdas(l)
        if cab is None:
            cab = [mo.normaliza(x) for x in c]
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
    t, puntos, revision = lee_informe(ruta_imp)
    en_revision = {m.raiz_de(x) for f in revision for x in mo.ids_en(f.get("pieza", ""))}
    faltan = set()
    for f in puntos:
        if "✗" not in f.get("decision", ""):
            faltan |= {m.raiz_de(x) for x in mo.ids_en(f.get("revisar tambien", "")) if x in m.piezas}
    informe("cada pieza de «Revisar también» tiene su fila en «Revisión de dependencias»", sorted(faltan - en_revision))
    candidatos = {x for x in mo.ids_en(t) if x not in m.piezas}
    aceptados, cambio = set(), True
    while cambio:
        cambio = False
        for x in candidatos - aceptados:
            if mo.tipo_de(x) == "CA":
                base = x.rsplit(".", 1)[0]
                ok = base in m.piezas or base in aceptados
            else:
                pre, num = x.rsplit("-", 1)
                previo = f"{pre}-{int(num) - 1:0{len(num)}d}"
                ok = previo in m.piezas or previo in aceptados
            if ok:
                aceptados.add(x)
                cambio = True
    informe("los IDs del informe existen o son nuevos que siguen la numeración", sorted(candidatos - aceptados))
    if carpeta_fuentes:
        mfu = re.search(r"FU-(\d+)", pathlib.Path(ruta_imp).name)
        textos = [t]
        if mfu:
            nota = pathlib.Path(ruta_imp).parent.parent / "notas" / f"FU-{mfu.group(1)}.md"
            if nota.exists():
                textos.append(nota.read_text(encoding="utf-8"))
        src = {re.match(r"FU-(\d+)", f.name).group(1):
               set(re.findall(r"^\[(\d{2}:\d{2}:\d{2})\]", f.read_text(encoding="utf-8"), re.M))
               for f in pathlib.Path(carpeta_fuentes).glob("FU-*.md")}
        rx = re.compile(r"FU-(\d+) (\d\d:\d\d:\d\d)")
        malas = sorted({f"FU-{x} {y}" for tx in textos for x, y in rx.findall(tx) if src.get(x) and y not in src[x]})
        informe("citas del informe y de la nota con el minuto de una intervención real", malas)
        if mfu and src.get(mfu.group(1)):
            seg = lambda h: sum(int(x) * f for x, f in zip(h.split(":"), (3600, 60, 1))) // 600
            habla = collections.Counter(seg(h) for h in src[mfu.group(1)])
            citado = {seg(y) for tx in textos for x, y in rx.findall(tx) if x == mfu.group(1)}
            huecos = [f"{s * 10:02d}–{s * 10 + 10:02d} min ({n} intervenciones)" for s, n in sorted(habla.items())
                      if n >= 5 and s not in citado]
            informe("cada tramo de 10 minutos de la reunión tiene alguna cita (también lo que no cambia nada)", huecos)


def comprobar_impacto(m, ant, ruta_imp, cambios):
    t, puntos, revision = lee_informe(ruta_imp)
    revisar, resueltos, sin_cambios = set(), set(), set()
    for f in puntos:
        if "✗" not in f.get("decision", ""):
            revisar |= mo.ids_en(f.get("revisar tambien", ""))
    for f in revision:
        res = mo.normaliza(f.get("resultado", ""))
        ids = {m.raiz_de(x) for x in mo.ids_en(f.get("pieza", ""))}
        if res and "pendiente" not in res:
            resueltos |= ids
        if "sin cambios" in res:
            sin_cambios |= ids
    revisar = {m.raiz_de(x) for x in revisar}
    informe("cada dependencia del informe tiene resultado", sorted(revisar - resueltos))
    declarado = set()
    for f in puntos:
        if "✗" not in f.get("decision", ""):
            declarado |= mo.ids_en(f.get("cambio propuesto", ""))
    for f in revision:
        if "sin cambios" not in mo.normaliza(f.get("resultado", "")):
            declarado |= mo.ids_en(f.get("pieza", "")) | mo.ids_en(f.get("resultado", ""))
    ma = re.search(r"^## Aplicado\s*$(.*?)(?=^## |\Z)", t, re.M | re.S)
    if ma:
        declarado |= mo.ids_en(ma.group(1))
    declarado |= {m.raiz_de(x) for x in declarado}
    nuevas, modif, anul = cambios
    no_decl = [i for i in set(nuevas) | set(modif) | set(anul) if i not in declarado and m.raiz_de(i) not in declarado]
    informe("cada cambio está declarado en el informe («Cambio propuesto», revisión con cambios o «Aplicado»)",
            sorted(no_decl, key=clave_pid))
    informe("nada marcado «sin cambios» ha cambiado",
            sorted(i for i in set(modif) | set(anul) if m.raiz_de(i) in sin_cambios and m.raiz_de(i) not in declarado))
    aprobado = set()
    for f in puntos:
        req = mo.normaliza(f.get("requiere", ""))
        dec = f.get("decision", "")
        if req and req not in ("—", "-", "no") and "✗" not in dec and "⚠" not in dec:
            for col in ("encaja en", "cambio propuesto"):
                aprobado |= {m.raiz_de(x) for x in mo.ids_en(f.get(col, ""))}
    pierden = sorted(i for i in m.piezas if i in ant.piezas and ant.piezas[i].estado == "🔒"
                     and m.piezas[i].estado != "🔒" and m.raiz_de(i) not in aprobado)
    informe("lo 🔒 que cambia pasó por un punto aprobado", pierden)


def main():
    for s in (sys.stdout, sys.stderr):
        s.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("proyecto")
    ap.add_argument("--fuentes")
    ap.add_argument("--corregir-citas", action="store_true")
    ap.add_argument("--anterior")
    ap.add_argument("--impacto")
    a = ap.parse_args()
    m = mo.Proyecto(a.proyecto)
    if not m.docs:
        sys.exit(f"No encuentro el análisis en {m.analisis}")
    comprobar_estructura(m)
    comprobar_ids(m)
    if "F" in m.docs:
        comprobar_completo(m)
        comprobar_limpieza(m)
        comprobar_redaccion(m)
        comprobar_tecnico(m)
        comprobar_versiones(m)
    if a.fuentes:
        comprobar_fuentes(m, a.fuentes, a.corregir_citas)
    if a.anterior:
        nuevas, modif, anul, ant = comprobar_anterior(m, a.anterior)
        if a.impacto:
            comprobar_impacto(m, ant, a.impacto, (nuevas, modif, anul))
    elif a.impacto:
        print("  (informe antes de aplicar: sin --anterior solo se revisan IDs y citas)")
        comprobar_informe_previo(m, a.impacto, a.fuentes)
    print("\nSin errores." if not errores else f"\n{errores} comprobaciones con errores.")
    sys.exit(1 if errores else 0)


if __name__ == "__main__":
    main()
