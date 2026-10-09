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
  - con --anterior: ningún ID desaparece, la versión sube y tiene su fila; lista lo nuevo y lo cambiado, y avisa
    del texto que queda viejo (lo que una pieza cambiada ya no dice y sigue en otra línea, sin tocar en esta versión);
  - con --impacto: los IDs del informe existen o son nuevos; «Requiere» es «—» o «Sí (motivo)», y «Sí» en lo que
    cambia o anula algo 🔒; después de aplicar, cada dependencia tiene resultado, cada cambio está declarado y lo 🔒
    solo cambia con aprobación;
  - con una aplicación existente (<p>/as-is/datos/inventario.json): cada historia con su «Origen»; hallazgos, NV y
    REF solo en la trazabilidad del DF y citados solo si existen; la Situación de cada objeto de técnico §13 contra el
    inventario y los objetos de fuera de la aplicación; con propuesta de refactorización, una DT por cada REF de su
    Solución y la tabla de migración en técnico §3. Avisa de lo que se modifica o se usa con un hallazgo Alta
    (¿refactorización antes?) o con algo sin verificar (¿PC o PT?) que no cita ninguna PT ni PC. Sin as-is/, nada
    de esto.
"""
import argparse
import bisect
import collections
import json
import pathlib
import re
import sys
sys.dont_write_bytecode = True  # sin __pycache__ en el plugin: no se escribe fuera del proyecto

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import modelo as mo
import redaccion as rd

SECCIONES = {"F": [str(n) for n in range(1, 12)], "T": [str(n) for n in range(0, 16)], "D": ["versiones", "decisiones"]}
PRIORIDADES = ("imprescindible", "deseable")
TIPOS_D = ("CAMBIA", "ANULA", "VALIDA", "RESPONDE", "ALCANCE+", "ALCANCE−", "ALCANCE-")
TERMINOS_APPIAN = [r"record types?", r"record lists?", r"process models?", r"\bsail\b", r"expression rules?",
                   r"reglas? de expresi[oó]n", r"smart services?", r"data stores?", r"\bcdts?\b", r"\ba![a-z]\w*",
                   r"appian designer", r"record actions?", r"interface objects?", r"\bdesigner\b",
                   r"vistas? de registro", r"acci[oó]n(es)? de registro", r"listas? de registros", r"tipos? de registro",
                   r"modelos? de proceso", r"\bsites?\b", r"\bportal(es)? de appian", r"grupos? de appian"]
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


def nombres(texto, conocidos=()):
    """Nombres de una celda: la celda entera si es un nombre conocido; si no, la lista separada por comas."""
    t = mo.sin_comentarios(texto).strip()
    if mo.normaliza(t) in conocidos:
        return [t]
    return [x.strip() for x in re.split(r",|;", t) if x.strip()]


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
    sin_campos, perfil_mal, pan_mal, prio_mal, sin_ca, sin_como, otro_perfil = [], [], [], [], [], [], []
    usados = set()
    for p in m.vigentes("HU"):
        c = m.campos(p.id)
        if not all(c.get(k) for k in ("perfil", "pantalla", "prioridad")):
            sin_campos.append(p.id)
            continue
        for x in nombres(c["perfil"], pf):
            usados.add(mo.normaliza(x))
            if pf and mo.normaliza(x) not in pf:
                perfil_mal.append(f"{p.id} «{x}»")
        if c["pantalla"].strip() not in ("—", "-") and not mo.ids_en(c["pantalla"]):
            pan_mal.append(p.id)
        if mo.normaliza(c["prioridad"]) not in PRIORIDADES:
            prio_mal.append(f"{p.id} «{c['prioridad']}»")
        if not [h for h in p.hijos if not anulada(m, h)]:
            sin_ca.append(p.id)
        for paso in mo.ids_en(c.get("paso", "")):
            quien = m.campos(paso).get("quien", "") if paso in m.piezas else ""
            if quien and not any(mo.normaliza(x) in mo.normaliza(quien) for x in nombres(c["perfil"], pf)):
                otro_perfil.append(f"{p.id} ({paso}: {mo.sin_comentarios(quien).strip()})")
        if not re.search(r"^Como .+ quiero .+ para ", m.texto(p.id), re.M):
            sin_como.append(p.id)
    informe("historias con la tabla Perfil · Pantalla · Paso · Prioridad", sin_campos)
    informe("perfiles de las historias que están en §2", perfil_mal)
    informe("pantalla de cada historia: PAN-nn o —", pan_mal)
    informe("prioridad «Imprescindible» o «Deseable»", prio_mal)
    informe("historias con criterios («Se acepta si:»)", sin_ca)
    informe("historias con «Como… quiero… para…»", sin_como, grave=False)
    informe("el perfil de cada historia es quien hace su paso", otro_perfil, grave=False)
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


def comprobar_redaccion(m):
    lista = rd.muletillas()
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
                for f in rd.frases(c):
                    pal = re.findall(r"\w+", f)
                    if len(pal) > rd.MAX_PALABRAS:
                        largas.append(f"l.{i + 1} ({len(pal)} palabras)")
                    if d == "F":
                        nf = mo.normaliza(f)
                        propias = re.findall(r"\w+", mo.RX_ID.sub(" ", nf).replace("pan-", " "))
                        if len([w for w in propias if not w.isdigit()]) >= 10:  # una lista de IDs no es una frase
                            vistas[" ".join(re.findall(r"\w+", nf))].append(i + 1)
                        if not re.search(r"\d", f) and not l.startswith("|"):
                            for v in VAGAS:
                                if re.search(rf"(?<!\w){re.escape(mo.normaliza(v))}(?!\w)", nf):
                                    vagas.append(f"l.{i + 1} «{v}»")
        n = mo.DOCS[d]
        informe(f"{n}: sin muletillas (references/redaccion.md)", mul, grave=False)
        informe(f"{n}: frases de {rd.MAX_PALABRAS} palabras o menos", largas, grave=False)
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


def estado_tecnico(m):
    """(empezado, completo): empezado si tiene decisiones o modelo de datos; completo si dice «Estado: completo»."""
    if "T" not in m.docs:
        return False, False
    empezado = bool(m.vigentes("DT")) or any(
        "campo" in [mo.normaliza(c) for c in cab] for _, cab, _ in m.tablas("T", "3"))
    est = re.search(r"Estado:\s*([^·\n]+)", "\n".join(m.docs["T"].lineas[:12]))
    return empezado, bool(est) and mo.normaliza(est.group(1)).strip().startswith("completo")


def comprobar_tecnico(m):
    empezado, completo = estado_tecnico(m)
    if not empezado:
        print("· técnico: sin empezar (sin decisiones ni modelo de datos); se comprueba cuando lo esté")
        return
    T = m.docs["T"]
    print(f"  técnico {'completo: lo que falta es error' if completo else 'en curso: lo que falta es aviso'}")
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
                for x in nombres(uso.split(":", 1)[1] if ":" in uso else "", nombres_df):
                    usados.add(mo.normaliza(x))
                    if mo.normaliza(x) not in nombres_df:
                        sin_dato.append(f"{f[0]} → «{x}»")
            elif not nu.startswith("tecnico"):
                sin_uso.append(f[0])
    informe("técnico §3: cada campo con «Uso: Funcional: <dato del DF>» o «Técnico: para qué»", sin_uso)
    informe("técnico §3: los campos funcionales remiten a un dato de funcional §6", sin_dato)
    informe("funcional §6: cada dato tiene su campo en técnico §3",
            sorted(v for k, v in df.items() if k[1] not in usados), grave=completo)

    def falta_en(seccion, ids):
        rango = T.seccion(seccion)
        texto = "\n".join(T.lineas[rango[0]:rango[1]]) if rango else ""
        citados = mo.ids_en(texto)
        return sorted((x for x in ids if x not in citados), key=clave_pid)
    informe("técnico §7: cada pantalla", falta_en("7", [p.id for p in m.vigentes("PAN")]), grave=completo)
    en_app = [p.id for p in m.vigentes("ACT")
              if "fuera de la aplicacion" not in mo.normaliza(m.campos(p.id).get("pantalla", ""))]
    informe("técnico §8: cada paso que ocurre en la aplicación", falta_en("8", en_app), grave=completo)
    informe("técnico §9: cada aviso", falta_en("9", [p.id for p in m.vigentes("AV")]), grave=completo)
    informe("técnico §10: cada relación con otro sistema", falta_en("10", [p.id for p in m.vigentes("INT")]),
            grave=completo)
    citadas_t = mo.ids_en(mo.sin_comentarios("\n".join(T.lineas)))
    informe("técnico: cada regla común aplicada en algún apartado",
            sorted((p.id for p in m.vigentes("RB") if p.id not in citadas_t), key=clave_pid), grave=completo)
    informe("técnico §14: cada criterio de aceptación",
            falta_en("14", [p.id for p in m.por_tipo("CA") if not anulada(m, p.id)]), grave=completo)
    informe("técnico §14: cada escenario", falta_en("14", [p.id for p in m.vigentes("ESC")]), grave=False)
    r4 = T.seccion("4")
    t4 = mo.normaliza("\n".join(T.lineas[r4[0]:r4[1]])) if r4 else ""
    informe("técnico §4: cada perfil con su grupo", [x for x in perfiles(m) if mo.normaliza(x) not in t4],
            grave=completo)
    vacios = []
    for clave, titulo, ini, fin in T.secciones:
        if clave.isdigit() and int(clave) <= 14 and not any(l.strip() for l in T.lineas[ini + 1:fin]):
            vacios.append(f"§{clave}")
    informe("técnico: apartados con contenido («No aplica: …» si no aplica)", vacios, grave=completo)
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


# ------------------------------------------------------------------ aplicación existente (as-is/)
# IDs de ingeniería inversa y de refactorización: se citan dentro de su fuente («[FU-01 H-SEG-01]», D1), así que
# modelo.ids_en no los cuenta; se buscan aquí en el texto tal cual, también en los comentarios.
RX_HALLAZGO = re.compile(r"\bH-[A-Z]{2,4}-\d{2,3}\b")
RX_NV = re.compile(r"\bNV-[A-Z]{2,4}-\d{2,3}\b")
RX_REF = re.compile(r"\bREF-\d{2,3}\b")
ORIGENES = ("se conserva", "cambia", "nueva")
SITUACIONES = ("nuevo", "modifica", "existe", "sustituye")


def lee_json(ruta):
    return json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else None


def objetos_celda(celda):
    """Los objetos de una celda: los nombres entre comillas invertidas o, si no hay, la celda; sin el prefijo de tipo
    («rule!», «recordType!», como comprobar_asis.py) ni los paréntesis del final («MNT_IF_Panel()»)."""
    t = mo.sin_comentarios(celda).strip()
    nombres = re.findall(r"`([^`]+)`", t) or ([t] if t.strip(" —-") else [])
    return [re.sub(r"\(.*\)\s*$", "", re.sub(r"^[A-Za-z]+!(\{[^}]*\})?", "", n.strip())).strip() for n in nombres]


def citas(m, rx):
    """{ID: [«funcional l.12», …]}: dónde se cita cada ID que casa con rx, también dentro de los comentarios."""
    out = collections.defaultdict(list)
    for d, D in m.docs.items():
        for i, l in enumerate(D.lineas):
            for x in rx.findall(l):
                out[x].append(f"{mo.NOMBRE_DOC[d]} l.{i + 1}")
    return out


def comprobar_as_is(m):
    """Solo con <p>/as-is/datos/inventario.json. Lo que depende de sin-verificar.json o de fueraDeLaAplicacion (un
    as-is/ anterior a ellos) no se comprueba."""
    datos = m.raiz / "as-is" / "datos"
    inv = lee_json(datos / "inventario.json")
    if inv is None:
        return
    inventario = {o["nombre"] for o in inv.get("objetos", [])} | {inv.get("aplicacion", {}).get("nombre", "")}
    dep = lee_json(datos / "dependencias.json") or {}
    fuera = {o["nombre"] for o in dep["fueraDeLaAplicacion"]} if "fueraDeLaAplicacion" in dep else None
    hallazgos = {h["id"]: h for h in (lee_json(datos / "hallazgos.json") or {}).get("hallazgos", [])}
    sv = lee_json(datos / "sin-verificar.json")
    nvs = {n["id"]: n for n in sv.get("sinVerificar", [])} if sv is not None else None
    faltan = [x for x, v in (("los objetos de fuera de la aplicación", fuera), ("sin-verificar.json", nvs)) if v is None]
    if faltan:
        print(f"· as-is/datos/ sin {' ni '.join(faltan)}, de una ingeniería inversa anterior: lo que depende de ello "
              "no se comprueba")

    sin_origen = []
    for p in m.vigentes("HU"):
        o = mo.sin_comentarios(m.campos(p.id).get("origen", "")).strip()
        if mo.normaliza(o) not in ORIGENES:
            sin_origen.append(f"{p.id} «{o}»" if o.strip(" —-") else p.id)
    informe("as-is: cada historia con «Origen»: Se conserva, Cambia o Nueva", sin_origen)
    a_la_vista = [f"l.{i + 1} {x}" for i, l in lineas_prosa(m, "F")
                  for rx in (RX_HALLAZGO, RX_NV, RX_REF) for x in rx.findall(l)]
    informe("DF: hallazgos, NV y REF solo en la trazabilidad (dentro del comentario)", a_la_vista)
    informe("as-is: los hallazgos citados están en hallazgos.json",
            sorted(f"{x} ({', '.join(v[:3])})" for x, v in citas(m, RX_HALLAZGO).items() if x not in hallazgos))
    if nvs is not None:
        informe("as-is: los NV citados están en sin-verificar.json",
                sorted(f"{x} ({', '.join(v[:3])})" for x, v in citas(m, RX_NV).items() if x not in nvs))

    empezado, completo = estado_tecnico(m)
    if not empezado:
        return
    tabla = next(((cab, filas) for _, cab, filas in m.tablas("T", "13")
                  if "situacion" in [mo.normaliza(c) for c in cab]), None)
    informe("técnico §13: tabla Paso · Objeto · Tipo · Situación · Sustituye a", [] if tabla else ["falta"], grave=completo)
    malas, de_fuera, sin_inventario, usados = [], [], [], []
    if tabla:
        cab = [mo.normaliza(c) for c in tabla[0]]
        celda = lambda f, k: f[cab.index(k)] if k in cab and cab.index(k) < len(f) else ""
        for f in tabla[1]:
            sit = mo.sin_comentarios(celda(f, "situacion")).strip()
            s = mo.normaliza(sit)
            objetos = objetos_celda(celda(f, "objeto"))
            nombre = ", ".join(objetos) or f"paso {celda(f, 'paso')}"
            if s not in SITUACIONES:
                malas.append(f"{nombre}: Situación «{sit}» (Nuevo, Modifica, Existe o Sustituye)")
                continue
            if s in ("modifica", "existe"):
                usados += objetos
            for o in objetos:
                if s == "nuevo" and o in inventario:
                    malas.append(f"{o}: «Nuevo» y ya está en el inventario")
                elif s == "nuevo" and fuera and o in fuera:
                    malas.append(f"{o}: «Nuevo» y es de otra aplicación")
                elif s in ("modifica", "existe") and o not in inventario:
                    if fuera is None:
                        sin_inventario.append(o)
                    elif o not in fuera:
                        malas.append(f"{o}: «{sit}» y no está en el inventario ni fuera de la aplicación")
                    elif s == "modifica":
                        de_fuera.append(f"{o} es de otra aplicación: ¿quién la cambia?")
            if s == "sustituye":
                sust = objetos_celda(celda(f, "sustituye a"))
                if not sust or any(o not in inventario for o in sust):
                    malas.append(f"{nombre}: «Sustituye» sin un objeto del inventario en «Sustituye a» "
                                 f"({', '.join(sust) or '—'})")
    informe("técnico §13: la Situación de cada objeto cuadra con as-is/ (inventario y objetos de fuera)", malas)
    informe("técnico §13: objetos de otra aplicación que se modifican", de_fuera, grave=False)
    if fuera is None:
        informe("técnico §13: objetos que no están en el inventario (as-is/ no dice cuáles son de otra aplicación)",
                sin_inventario, grave=False)
    # Parte mal hecha: construir encima de un objeto con un hallazgo grave o con algo sin verificar, salvo que una PT o
    # una PC ya lo cite («[FU-nn H-…]», «[FU-nn NV-…]»): entonces ya está recogido
    en_pendientes = {x for p in m.por_tipo("PT") + m.por_tipo("PC") for rx in (RX_HALLAZGO, RX_NV)
                     for x in rx.findall(m.texto(p.id))}
    graves, sin_verificar = [], []
    for o in dict.fromkeys(usados):     # en el orden de §13, una vez cada objeto
        for h in sorted(hallazgos.values(), key=lambda h: h["id"]):
            if (mo.normaliza(h.get("severidad", "")) == "alta" and o in h.get("objetos", [])
                    and h["id"] not in en_pendientes):
                graves.append(f"{o} tiene {h['id']} (Alta): ¿pasa antes por refactorización?")
        for n in sorted((nvs or {}).values(), key=lambda n: n["id"]):
            if (mo.normaliza(n.get("estado", "")) in ("abierto", "parcial") and o in n.get("objetos", [])
                    and n["id"] not in en_pendientes):
                negocio = mo.normaliza(n.get("queHaceFalta", "")).startswith("negocio")
                sin_verificar.append(f"{o} tiene {n['id']} sin verificar: ¿{'PC' if negocio else 'PT'}?")
    informe("técnico §13: lo que se modifica o se usa con un hallazgo Alta que no cita ninguna PT ni PC", graves,
            grave=False)
    informe("técnico §13: lo que se modifica o se usa con algo sin verificar que no cita ninguna PT ni PC",
            sin_verificar, grave=False)

    propuesta = m.raiz / "refactorizacion" / "propuesta.md"
    if propuesta.exists():
        sol = re.search(r"^## 3\. Soluci[oó]n\s*$(.*?)(?=^## |\Z)", propuesta.read_text(encoding="utf-8"), re.M | re.S)
        refs = sorted(set(RX_REF.findall(mo.sin_comentarios(sol.group(1))))) if sol else []
        en_dt = {x for p in m.vigentes("DT") for x in RX_REF.findall(m.texto(p.id))}
        informe("propuesta: cada REF de su Solución con una DT que la cite («[FU-nn REF-nn]» en «Necesidad»; si el "
                "cliente la rechaza, con «Decisión: No se hace: …»)", [r for r in refs if r not in en_dt], grave=completo)
        migracion = any(cab and mo.normaliza(cab[0]).startswith("origen en la app") for _, cab, _ in m.tablas("T", "3"))
        informe("técnico §3: tabla «Carga inicial y migración» (hay propuesta de refactorización)",
                [] if migracion else ["falta"], grave=completo)


# ------------------------------------------------------------------ fuentes
def comprobar_fuentes(m, carpeta, corregir):
    src, gente, sin_gente = {}, set(), []
    for f in pathlib.Path(carpeta).glob("FU-*.md"):
        txt = f.read_text(encoding="utf-8")
        num = re.match(r"FU-(\d+)", f.name).group(1)
        src[num] = sorted(set(re.findall(r"^\[(\d{2}:\d{2}:\d{2})\]", txt, re.M)))
        mm = re.search(r"^- Participantes: (.*)$", txt, re.M)
        if mm and "sin identificar" not in mm.group(1):
            gente |= {n.strip() for n in mm.group(1).split(";") if n.strip()}
        elif src[num]:
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
    # nombres de personas: el completo es error; el nombre de pila suelto, aviso (puede ser otra cosa)
    todo = "\n".join("\n".join(D.lineas) for D in m.docs.values())
    completos = sorted(n for n in gente if re.search(rf"(?<!\w){re.escape(n)}(?!\w)", todo))
    pila = sorted({n.split()[0] for n in gente if len(n.split()) > 1 and n not in completos
                   and len(n.split()[0]) > 2 and re.search(rf"(?<!\w){re.escape(n.split()[0])}(?!\w)", todo)})
    informe("sin nombres de participantes", completos)
    informe("sin nombres de pila de participantes (revisa si es una persona)", pila, grave=False)
    if sin_gente:
        print(f"· {', '.join(sorted(sin_gente))}: transcripción sin participantes identificados; revisa a mano que no salgan nombres")
    # cada tramo de 10 minutos con conversación tiene alguna cita en el análisis o en la nota de la fuente
    notas = m.raiz / "notas"
    citas = collections.defaultdict(set)
    seg = lambda h: sum(int(x) * f for x, f in zip(h.split(":"), (3600, 60, 1))) // 600
    textos = [todo] + [f.read_text(encoding="utf-8") for f in notas.glob("FU-*.md")] if notas.is_dir() else [todo]
    for tx in textos:
        for x, y in rx.findall(tx):
            citas[x].add(seg(y))
    huecos = []
    for num, marcas in src.items():
        habla = collections.Counter(seg(h) for h in marcas)
        huecos += [f"FU-{num} {s * 10:02d}–{s * 10 + 10:02d} min" for s, n in sorted(habla.items())
                   if n >= 5 and s not in citas[num]]
    informe("cada tramo de 10 minutos de cada reunión tiene alguna cita (en el análisis o en su nota)", huecos,
            grave=False)


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


SECUENCIA = 5   # palabras seguidas que, si una pieza cambiada ya no las dice, no deberían seguir en otra


def _palabras(linea):
    """Las palabras visibles de una línea: (normalizada, tal cual)."""
    return [(mo.normaliza(w), w) for w in re.findall(r"\w+", visible(linea))]


def _secuencias(lineas):
    out = set()
    for l in lineas:
        ws = [w for w, _ in _palabras(l)]
        out |= {tuple(ws[k:k + SECUENCIA]) for k in range(len(ws) - SECUENCIA + 1)}
    return out


def texto_viejo(m, ant, modif):
    """Para cada pieza modificada, las secuencias de cinco palabras que tenía antes y ya no tiene, y cada otra línea del
    funcional o del técnico que aún las dice: «HU-07: "…" sigue en PAN-04, l.212». Una vez por línea, y solo de las
    líneas que ya estaban tal cual en la versión anterior: lo reescrito en esta versión ya se ha revisado."""
    duenio = {}     # (doc, línea) -> la pieza más pequeña que la contiene
    for p in m.piezas.values():
        for i in range(p.ini, p.fin):
            otro = duenio.get((p.doc, i))
            if otro is None or p.fin - p.ini < m.piezas[otro].fin - m.piezas[otro].ini:
                duenio[(p.doc, i)] = p.id
    de_antes = {(d, l) for d, D in ant.docs.items() for l in D.lineas}
    avisos, vistos = [], set()
    for pid in modif:
        p = m.piezas.get(pid)
        if not p or p.doc not in ("F", "T") or pid not in ant.piezas or (p.padre and p.padre in modif):
            continue
        quitadas = _secuencias(ant.bloque(pid)) - _secuencias(m.bloque(pid))
        if not quitadas:
            continue
        raiz = m.piezas[m.raiz_de(pid)]
        propias = {(raiz.doc, i) for i in range(raiz.ini, raiz.fin)}
        for d in ("F", "T"):
            if d not in m.docs:
                continue
            for i, l in enumerate(m.docs[d].lineas):
                otro = duenio.get((d, i))
                if (d, i) in propias or (d, i) in vistos or (d, l) not in de_antes or (otro and anulada(m, otro)):
                    continue
                pal = _palabras(l)
                ws = [w for w, _ in pal]
                k = next((k for k in range(len(ws) - SECUENCIA + 1) if tuple(ws[k:k + SECUENCIA]) in quitadas), None)
                if k is None:
                    continue
                vistos.add((d, i))
                donde = otro or f"{mo.NOMBRE_DOC[d]} §{m.docs[d].seccion_de_linea[i]}"
                fin = k + 1     # la frase entera: las secuencias quitadas seguidas desde la primera
                while fin < len(ws) - SECUENCIA + 1 and tuple(ws[fin:fin + SECUENCIA]) in quitadas:
                    fin += 1
                frase = " ".join(o for _, o in pal[k:fin - 1 + SECUENCIA])
                avisos.append(f'{pid}: "{frase}" sigue en {donde}, l.{i + 1}')
    return avisos


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


def comprobar_requiere(base, puntos):
    """«Requiere» de cada punto: «—» o «Sí (motivo)»; y «Sí» si el punto CAMBIA o ANULA una pieza 🔒 de «Encaja en»
    (🔒 en base: el análisis antes de aplicar el informe)."""
    formato, sin_si = [], []
    for f in puntos:
        col = next((k for k in f if k.startswith("requiere")), None)
        if col is None:
            continue
        req = mo.sin_comentarios(f[col]).strip()
        si = re.match(r"si(?!\w)", mo.normaliza(req).strip(" *")) is not None
        if not si and req not in ("—", "-"):
            formato.append(f"punto {f.get('#', '?')} «{req}»")
        if not si and mo.normaliza(f.get("tipo", "")).strip(" *").startswith(("cambia", "anula")):
            validadas = sorted(x for x in mo.ids_en(f.get("encaja en", "")) if x in base.piezas
                               and "🔒" in (base.piezas[x].estado, base.piezas[base.raiz_de(x)].estado))
            if validadas:
                sin_si.append(f"punto {f.get('#', '?')} ({', '.join(validadas)})")
    informe("«Requiere» de cada punto: «—» o «Sí (motivo)»", formato)
    informe("«Requiere: Sí» en cada punto que cambia o anula algo 🔒 de «Encaja en»", sin_si)


def comprobar_informe_previo(m, ruta_imp, carpeta_fuentes):
    t, puntos, revision = lee_informe(ruta_imp)
    comprobar_requiere(m, puntos)
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
                ok = previo in m.piezas or previo in aceptados or (int(num) == 1 and not m.por_tipo(mo.tipo_de(x)))
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
    comprobar_requiere(ant, puntos)
    revisar, resueltos, sin_cambios = set(), set(), set()
    for f in puntos:
        if "✗" not in f.get("decision", ""):
            revisar |= mo.ids_en(f.get("revisar tambien", ""))
    for f in revision:
        res = mo.normaliza(mo.sin_comentarios(f.get("resultado", ""))).strip(" *")
        ids = {m.raiz_de(x) for x in mo.ids_en(f.get("pieza", ""))}
        if res and not res.startswith("pendiente"):     # sin resolver: vacío o «Pendiente…»
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
        if "✔" in f.get("decision", ""):
            for col in ("encaja en", "cambio propuesto"):
                aprobado |= {m.raiz_de(x) for x in mo.ids_en(f.get(col, ""))}
    sin_coment = lambda t: normaliza_pieza(mo.sin_comentarios(t))
    tocadas = [i for i in m.piezas if i in ant.piezas and ant.piezas[i].estado == "🔒" and
               (m.piezas[i].estado != "🔒" or sin_coment(m.texto(i)) != sin_coment(ant.texto(i)))]
    informe("lo 🔒 que cambia pasó por un punto aprobado (✔)", sorted(i for i in tocadas if m.raiz_de(i) not in aprobado))


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
        comprobar_as_is(m)
    if a.fuentes:
        comprobar_fuentes(m, a.fuentes, a.corregir_citas)
    if a.anterior:
        nuevas, modif, anul, ant = comprobar_anterior(m, a.anterior)
        informe("texto que queda viejo (lo que una pieza cambiada ya no dice y sigue en otra: corrígelo o dilo)",
                texto_viejo(m, ant, modif), grave=False)
        if a.impacto:
            comprobar_impacto(m, ant, a.impacto, (nuevas, modif, anul))
    elif a.impacto:
        print("  (informe antes de aplicar: sin --anterior solo se revisan IDs y citas)")
        comprobar_informe_previo(m, a.impacto, a.fuentes)
    print("\nSin errores." if not errores else f"\n{errores} comprobaciones con errores.")
    sys.exit(1 if errores else 0)


if __name__ == "__main__":
    main()
