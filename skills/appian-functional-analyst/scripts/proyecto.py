#!/usr/bin/env python3
"""Crea la carpeta de un proyecto y dice en qué punto está.

  proyecto.py iniciar  <carpeta> --nombre "Solicitudes de autorización" [--cliente …] [--direccion …] [--tipo "evolutivo de X"]
  proyecto.py estado   <carpeta>     versión, cliente y marca, DF enviado, fuentes sin procesar, pendientes, pantallas
  proyecto.py copia    <carpeta>     guarda analisis/*.md en versiones/v<versión>/ antes de cambiarlo
  proyecto.py entregar <carpeta> [--cambio EV-02]   el Word sale hacia el cliente: «DF entregado» (el de un cambio, en su
                                     fila de Versiones de decisiones.md) y el fichero en «Entregados»
  proyecto.py cambio   <carpeta> <EV-nn|URG-nn> <estado> [opciones]   una unidad de cambio (analisis/cambios.md):
      abrir --titulo "…"                    Abierta
      aprobada --fuente FU-nn [--comparte "EV-03 en <objeto>: secuenciar (EV-02 primero)"]
                                            el jefe de proyecto la aprueba; otra vez si ha crecido (una fuente nueva
                                            para la unidad); sin --fuente, de Construida vuelve a Aprobada
      construida [--reaplicada URG-nn …] [--manual]   tras construir y verificar (construccion/verificacion/<ID>.json)
      produccion --ref "<referencia del pase>"        tras el pase (una URG, desde Abierta)
      descartada [--informe impacto/FU-nn.md]         desde Abierta, sin nada aplicado o con el informe que lo deshace
    Con --desatendida nunca aprueba ni pasa a producción. Las condiciones, en references/cambios.md.

`iniciar` no toca nada que ya exista. `entregar` solo cuando el Word se envía, nunca en una sesión desatendida.
"""
import argparse
import datetime
import json
import pathlib
import re
import shutil
import sys
import unicodedata
sys.dont_write_bytecode = True  # sin __pycache__ en el plugin: no se escribe fuera del proyecto

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import modelo as mo
import unidades as un

PLANTILLAS = pathlib.Path(__file__).resolve().parents[1] / "assets" / "plantillas"
CARPETAS = ["fuentes", "notas", "impacto", "analisis/diagramas", "prototipo", "entregables", "versiones"]
# «DF entregado: 1.1 · 2026-10-10» (entregar) o, en proyectos anteriores, «DF entregado: 1.0 (2026-09-12)»
RX_ENTREGADO = re.compile(r"DF entregado:\s*v?(\d+\.\d+)(?:\s*(?:·\s*|\()(\d{4}-\d{2}-\d{2}))?")


def iniciar(a):
    raiz = pathlib.Path(a.carpeta)
    for c in CARPETAS:
        (raiz / c).mkdir(parents=True, exist_ok=True)
    datos = {"proyecto": a.nombre, "cliente": a.cliente or "—", "direccion": a.direccion or "—",
             "tipo": a.tipo or "nuevo", "fecha": datetime.date.today().isoformat()}
    destinos = {"proyecto.md": raiz / "proyecto.md", "funcional.md": raiz / "analisis" / "funcional.md",
                "tecnico.md": raiz / "analisis" / "tecnico.md", "decisiones.md": raiz / "analisis" / "decisiones.md"}
    for nombre, destino in destinos.items():
        if destino.exists():
            print(f"= {destino} (ya existe, no se toca)")
            continue
        texto = (PLANTILLAS / nombre).read_text(encoding="utf-8")
        for k, v in datos.items():
            texto = texto.replace("{" + k + "}", v)
        destino.write_text(texto, encoding="utf-8")
        print(f"+ {destino}")
    print(f"Carpetas: {', '.join(CARPETAS)}")


def tabla(texto, titulo):
    m = re.search(rf"^## {re.escape(titulo)}\s*$(.*?)(?=^## |\Z)", texto, re.M | re.S)
    if not m:
        return []
    filas = [mo.celdas(l) for l in m.group(1).split("\n") if l.startswith("|")]
    return [f for f in filas[2:] if any(f)]


def estado(a):
    raiz = pathlib.Path(a.carpeta)
    pm = raiz / "proyecto.md"
    texto = pm.read_text(encoding="utf-8") if pm.exists() else ""
    m = mo.Proyecto(raiz)
    print(f"# {texto.splitlines()[0][2:] if texto else raiz.name}")
    v = m.version("F")
    vs = f"{v[0]}.{v[1]}" if v else "—"
    print(f"Análisis: versión {vs}")
    cliente = re.search(r"Cliente:\s*([^·\n]+)", texto)
    marcas = sorted(f"prototipo/{b.name}" for b in (raiz / "prototipo").glob("brand-*.json"))
    print(f"Cliente: {cliente.group(1).strip() if cliente else '—'} · Marca: {', '.join(marcas) or 'sin marca'}")
    entregado = RX_ENTREGADO.search(texto)
    if entregado:   # el Word se genera al enviarlo o si se pide: aquí solo se informa
        fecha = f" ({entregado.group(2)})" if entregado.group(2) else ""
        print(f"DF en Word: último enviado {entregado.group(1)}{fecha}, versión actual {vs}")

    # informes de impacto: los pendientes; las PAN de un cambio aprobado (✔) en una versión posterior al prototipo que se
    # enseñó (el último prototipo/app-vX.Y.json; sin ninguno, todas), que el prototipo rehace; y las fuentes que cuentan
    # como procesadas aunque no estén en la tabla: la de un informe «sin cambios» y la que cita una Decisión («✔ FU-09»)
    ensenadas = [tuple(map(int, x.groups())) for b in (raiz / "prototipo").glob("app-v*.json")
                 for x in [re.match(r"app-v(\d+)\.(\d+)\.json$", b.name)] if x]
    ultima = max(ensenadas) if ensenadas else None
    aprobadas, procesadas, pendientes = set(), {f[0] for f in tabla(texto, "Fuentes procesadas")}, []
    cerradas = {u.id for u in un.leer(raiz) or [] if u.estado in (un.PRODUCCION, un.DESCARTADA)}
    for nombre, t, puntos, _ in mo.informes(raiz):
        if nombre in cerradas:   # la ficha de una URG ya pasada a producción (o descartada) no queda pendiente
            continue
        # «Estado: pendiente» o «Estado: aplicado en 1.2; pendientes de aprobación: puntos 4 y 7» (actualizacion.md)
        e = mo.estado_informe(t)
        if re.search(r"pendientes? de aprobaci[oó]n:\s*puntos?\s+\d", e, re.I):
            pendientes.append(f"· {nombre}.md: {e}")
        elif re.match(r"pendiente", e, re.I):
            pendientes.append(f"· {nombre}.md: informe pendiente de aprobar o de aplicar")
        if re.match(r"sin cambios", e, re.I):
            procesadas |= set(re.findall(r"FU-\d+", nombre))
        procesadas |= {x for f in puntos for x in re.findall(r"FU-\d+", f.get("decision", ""))}
        aplicado = re.match(r"aplicado en v?(\d+)\.(\d+)", e, re.I)
        if aplicado and (ultima is None or tuple(map(int, aplicado.groups())) > ultima):
            aprobadas |= {x for f in puntos if "✔" in f.get("decision", "")
                          for col in ("encaja en", "cambio propuesto") for x in mo.ids_en(f.get(col, ""))
                          if x.startswith("PAN-")}
    catalogadas = sorted({re.match(r"(FU-\d+)", f.name).group(1) for f in (raiz / "fuentes").glob("FU-*.md")})
    sin = [x for x in catalogadas if x not in procesadas]
    print(f"Fuentes: {len(catalogadas)} catalogadas, {len(procesadas)} procesadas" +
          (f"; sin procesar: {', '.join(sin)}" if sin else ""))
    for x in pendientes:
        print(x)
    unidades(un.Contexto(m))

    if not m.docs:
        print("Sin análisis todavía.")
        return
    pc = sorted(p.id for p in m.vigentes("PC"))
    pt = sorted(p.id for p in m.vigentes("PT"))
    print(f"Pendiente de confirmar: {len(pc)}" + (f" ({', '.join(pc)})" if pc else ""))
    print(f"Pendientes técnicos: {len(pt)}" + (f" ({', '.join(pt)})" if pt else ""))
    pan = sorted(p.id for p in m.vigentes("PAN"))
    sin_cap = [p for p in pan if not re.search(r"!\[[^\]]*\]\([^)]+\)", m.texto(p))]
    print(f"Pantallas: {len(pan)}" + (f"; sin captura: {', '.join(sin_cap)}" if sin_cap else ""))
    conf = [p for p in pan if m.piezas[p].estado == "🔒"]
    if conf:
        print(f"Pantallas validadas por el cliente (🔒; no se cambian sin el visto bueno del analista): {', '.join(conf)}")
        cambian = [p for p in conf if p in aprobadas]
        if cambian:
            desde = f"después de app-v{ultima[0]}.{ultima[1]}.json" if ultima else "(sin app-vX.Y.json)"
            print(f"  con un cambio aprobado {desde}, el prototipo las rehace: {', '.join(cambian)}")
        quedan = [p for p in conf if p not in aprobadas]
        print(f"  para el prototipo: --confirmadas {','.join(quedan)}" if quedan else
              "  para el prototipo: ninguna va en --confirmadas")
    if "T" in m.docs:
        tv = m.version("T")
        empezado = bool(m.vigentes("DT")) or any("campo" in [mo.normaliza(c) for c in cab] for _, cab, _ in m.tablas("T", "3"))
        print("Técnico: " + (f"versión {tv[0]}.{tv[1]}" if tv else "sin versión") + ("" if empezado else ", sin empezar"))
    sig = re.search(r"^## Siguiente paso\s*\n+(.+)", texto, re.M)
    if sig:
        print(f"Siguiente paso: {sig.group(1).strip()}")


def unidades(ctx):
    """Las unidades en curso de analisis/cambios.md con sus fuentes, versiones y objetos, que no se guardan: se derivan."""
    if not ctx.hay:
        return
    curso = [u for u in ctx.unidades if u.estado in un.EN_CURSO]
    print(f"Unidades en curso (analisis/cambios.md; references/cambios.md): {len(curso) or 'ninguna'}")
    for u in curso:
        fu = sorted({x for n in ctx.informes_de(u.id) for x in re.findall(r"(?:FU|URG)-\d+", n)}, key=mo.numero)
        vs = ", ".join(f"{v[0]}.{v[1]}" for v in ctx.versiones_de(u.id))
        obj = ctx.cambian(u.id) if not u.urgente else ctx.objetos_urg(u.id)
        print(f"  {u.id} · {u.titulo} · {u.estado} · fuentes: {', '.join(fu) or '—'} · versión: {vs or '—'}"
              f" · objetos: {', '.join(obj) or '—'}")
        for g, objs in ctx.reaplicar(u.id):
            print(f"    reaplicar {g} en {', '.join(objs)} antes de marcarla Construida (--reaplicada {g})")
    for n in ctx.sin_unidad():
        print(f"· impacto/{n}.md no dice «Cambio:» y hay varias unidades Abiertas: ¿de cuál es?")


def copia(a):
    raiz = pathlib.Path(a.carpeta)
    m = mo.Proyecto(raiz)
    v = m.version("F")
    if not v:
        sys.exit("funcional.md no tiene «Versión: x.y»")
    destino = raiz / "versiones" / f"v{v[0]}.{v[1]}"
    destino.mkdir(parents=True, exist_ok=True)
    for nombre in mo.DOCS.values():
        f = m.analisis / nombre
        if f.exists():
            shutil.copy2(f, destino / nombre)
    print(f"Copia de la versión {v[0]}.{v[1]} en {destino}. Al terminar: comprobar.py {raiz} --anterior {destino}")


def nombre_df(m, vs):
    """El nombre del Word que escribe df_docx.js por defecto: DF-<título sin tildes ni signos>-v<versión>.docx."""
    tit = re.search(r"^# (.+)$", "\n".join(m.docs["F"].lineas), re.M) if "F" in m.docs else None
    tit = re.sub(r"\s+—\s+Diseño funcional\s*$", "", tit.group(1)) if tit else "Diseño funcional"
    slug = re.sub(r"[^A-Za-z0-9_]+", "-", re.sub(r"[\u0300-\u036f]", "", unicodedata.normalize("NFD", tit))).strip("-")
    return f"DF-{slug}-v{vs}.docx"


def entregados(texto, word):
    """proyecto.md con el fichero en «Entregados: a.docx, b.docx» (tras «DF entregado» o tras la línea del cliente)."""
    lineas = texto.split("\n")
    k = next((i for i, l in enumerate(lineas) if l.startswith("Entregados:")), None)
    if k is None:
        k = next((i for i, l in enumerate(lineas) if "DF entregado:" in l),
                 next((i for i, l in enumerate(lineas) if l.startswith("Cliente:")), 0)) + 1
        lineas.insert(k, "Entregados:")
    ya = [x.strip() for x in lineas[k].split(":", 1)[1].split(",") if x.strip()]
    lineas[k] = "Entregados: " + ", ".join(ya + ([word] if word not in ya else []))
    return "\n".join(lineas)


def entregar(a):
    """El Word sale hacia el cliente: «DF entregado: <versión> · <fecha>» en proyecto.md (el de un cambio, en la fila de
    su versión en decisiones.md) y el fichero en «Entregados:», que df_docx.js no vuelve a escribir."""
    raiz = pathlib.Path(a.carpeta)
    pm = raiz / "proyecto.md"
    if not pm.exists():
        sys.exit(f"No existe {pm}")
    m = mo.Proyecto(raiz)
    v = m.version("F")
    if not v:
        sys.exit("funcional.md no tiene «Versión: x.y»")
    vs, fecha = f"{v[0]}.{v[1]}", datetime.date.today().isoformat()
    texto = pm.read_text(encoding="utf-8")
    if a.cambio:
        return entregar_cambio(a.cambio.upper(), raiz, m, vs, fecha, texto)
    valor = f"DF entregado: {vs} · {fecha}"
    if re.search(r"DF entregado:", texto):
        texto = re.sub(r"DF entregado:[^\n]*?(?=\s+·\s+Estado:|$)", valor, texto, count=1, flags=re.M)
    else:   # tras la línea del cliente o, si no está, tras el título
        lineas = texto.split("\n")
        k = next((i for i, l in enumerate(lineas) if l.startswith("Cliente:")), 0)
        lineas.insert(k + 1, valor)
        texto = "\n".join(lineas)
    word = nombre_df(m, vs)
    if not (raiz / "entregables" / word).is_file():
        print(f"· No encuentro entregables/{word}: genéralo con df_docx.js antes de enviarlo")
    else:
        texto = entregados(texto, word)
    pm.write_text(texto, encoding="utf-8")
    print(f"{valor} en {pm}")


def entregar_cambio(uid, raiz, m, vs, fecha, texto):
    """El DF de un cambio (df_docx.js --cambio): «DF del cambio <U> entregado <fecha>» en la columna «Aprobación» de la
    fila de la versión en decisiones.md (no sale en el Word) y el fichero en «Entregados» de proyecto.md."""
    if uid not in {u.id for u in un.leer(raiz) or []}:
        sys.exit(f"{uid} no está en analisis/cambios.md")
    word = nombre_df(m, vs).replace(f"-v{vs}.docx", f"-{uid}-v{vs}.docx")
    if not (raiz / "entregables" / word).is_file():
        sys.exit(f"No encuentro entregables/{word}: genéralo con «df_docx.js {raiz} --cambio {uid}» antes de enviarlo")
    dm = m.analisis / "decisiones.md"
    lineas = dm.read_text(encoding="utf-8").split("\n") if dm.is_file() else []
    k = next((i for i, l in enumerate(lineas) if re.match(rf"^\|\s*v?{re.escape(vs)}\s*\|", l)), None)
    if k is None:
        sys.exit(f"decisiones.md no tiene la fila de la versión {vs} en «Versiones»")
    c = mo.celdas(lineas[k])
    nota = f"DF del cambio {uid} entregado {fecha}"
    if nota not in c[-1]:
        c[-1] = nota if c[-1].strip(" —-") == "" else f"{c[-1]} · {nota}"
        lineas[k] = "| " + " | ".join(c) + " |"
        dm.write_text("\n".join(lineas), encoding="utf-8")
    (raiz / "proyecto.md").write_text(entregados(texto, word), encoding="utf-8")
    print(f"{nota}: en la versión {vs} de decisiones.md y {word} en «Entregados» de proyecto.md")


def cambio(a):
    """Mueve una unidad de cambio en analisis/cambios.md. Solo bloquea lo que haría perder trabajo o construir algo
    equivocado (references/cambios.md): aprobar con puntos pendientes o con objetos de otra unidad aprobada sin decisión,
    construir lo que ha crecido desde la aprobación, marcar Construida sin verificar o sin reaplicar una corrección
    urgente, pasar a producción sin construir. Cada error dice la salida."""
    raiz, uid, destino = pathlib.Path(a.carpeta), a.id.upper(), a.estado
    hoy = datetime.date.today().isoformat()
    orden = f"proyecto.py cambio <p> {uid}"

    def no(motivo, salida):
        sys.exit(f"✗ {uid} {destino}: {motivo}. Salida: {salida}")
    if not re.fullmatch(r"(EV|URG)-\d+", uid):
        no("el ID de una unidad es EV-nn (evolutivo) o URG-nn (urgente)", "usa uno de esos, p. ej. EV-02")
    if destino in ("aprobada", "produccion") and a.desatendida:
        no("en una sesión desatendida no se aprueba ni se pasa a producción",
           "déjalo para el jefe de proyecto: proyecto.py estado lo lista")
    m = mo.Proyecto(raiz)
    ctx = un.Contexto(m)
    u = ctx.por_id.get(uid)
    if destino == "abrir":
        if u:
            no(f"ya existe ({u.estado})", "usa el siguiente ID libre (proyecto.py estado)")
        if not (a.titulo or "").strip():
            no("falta el título", f"{orden} abrir --titulo \"…\"")
        u = un.Unidad(uid, a.titulo.strip(), "Urgente" if uid.startswith("URG") else "Evolutivo", desde=m.version("F"))
        ctx.unidades.append(u)
    elif not u:
        no("no está en analisis/cambios.md", f"ábrela antes: {orden} abrir --titulo \"…\"")
    elif destino == "aprobada":
        if u.urgente:
            no("una URG no se aprueba como unidad: va de Abierta a En producción (references/urgentes.md)",
               f"{orden} produccion --ref \"…\" tras el pase")
        if u.estado == un.CONSTRUIDA and not a.fuente:     # vuelve a Aprobada: una URG obliga a reaplicar
            u.estado, u.construida = un.APROBADA, "—"
        elif u.estado not in (un.ABIERTA, un.APROBADA, un.CONSTRUIDA):
            no(f"está {u.estado}", "un cambio sobre lo que ya está en producción es una unidad nueva: "
               "proyecto.py cambio <p> EV-nn abrir --titulo \"…\"")
        else:
            u.construida = "—" if u.estado == un.CONSTRUIDA else u.construida
            aprobar(a, ctx, u, hoy, no, raiz, orden)
    elif destino == "construida":
        if u.urgente:
            no("una URG no pasa por Construida: va de Abierta a En producción", f"{orden} produccion --ref \"…\"")
        if u.estado != un.APROBADA:
            no(f"está {u.estado}: se marca Construida una unidad Aprobada",
               f"apruébala antes ({orden} aprobada --fuente FU-nn)" if u.estado == un.ABIERTA else
               "ninguna: ya pasó por Construida")
        construir(a, ctx, u, hoy, no, raiz, orden)
    elif destino == "produccion":
        if not (a.ref or "").strip():
            no("falta la referencia del pase", f"{orden} produccion --ref \"<referencia>\"")
        if u.urgente:
            if u.estado != un.ABIERTA:
                no(f"está {u.estado}: una URG pasa a producción desde Abierta", "ninguna: ya está cerrada")
            urgente_a_produccion(ctx, uid, no)
        elif u.estado != un.CONSTRUIDA:
            no(f"está {u.estado}: pasa a producción una unidad Construida",
               f"constrúyela y verifícala antes ({orden} construida)" if u.estado in (un.ABIERTA, un.APROBADA) else
               "ninguna: ya está cerrada")
        u.estado, u.produccion = un.PRODUCCION, f"{hoy} · {a.ref.strip()}"
    elif destino == "descartada":
        if u.estado != un.ABIERTA:
            no(f"está {u.estado}: se descarta una unidad Abierta",
               "lo aprobado o construido que ya no se quiere lo deshace una unidad nueva" if u.estado != un.DESCARTADA
               else "ninguna: ya está descartada")
        hecho = sorted(ctx.piezas_de(uid), key=mo.numero) + ctx.cambian(uid)
        if hecho and not a.informe:
            no(f"tiene cambios aplicados ({', '.join(hecho[:8])})",
               f"aplica un informe que los deshaga y descártala con él: {orden} descartada --informe impacto/FU-nn.md")
        if hecho:
            f = pathlib.Path(a.informe)
            f = f if f.is_file() else raiz / a.informe
            if not f.is_file():
                no(f"no existe {a.informe}", "da la ruta del informe que deshace los cambios (impacto/FU-nn.md)")
            if not mo.normaliza(mo.estado_informe(f.read_text(encoding="utf-8"))).startswith("aplicado"):
                no(f"{f.name} no está aplicado", "aplícalo (actualizacion.md) y vuelve a descartarla")
            if ctx.filas_de(uid):
                no(f"técnico §13 sigue teniendo filas de {uid}", "el informe que deshace los cambios también las quita")
        u.estado = un.DESCARTADA
    un.escribir(raiz, ctx.unidades, PLANTILLAS / "cambios.md")
    print(f"{uid}: {u.estado} · analisis/cambios.md\n{u.fila()}")
    if destino == "abrir":
        print("Sus fuentes llevan «Cambio: " + uid + "» en la cabecera del informe" +
              (f"; su ficha es impacto/{uid}.md (assets/plantillas/urgencia.md, references/urgentes.md)" if u.urgente
               else " (references/cambios.md)"))
    if destino == "produccion":
        print("Actualiza el entorno de corrección con este pase: las correcciones urgentes se hacen sobre lo que hay en "
              "producción (references/urgentes.md)")


def urgente_a_produccion(ctx, uid, no):
    """Una URG pasa a producción con su ficha y su «Dónde se corrige»: sin él, o con uno que no dice «Desarrollo» ni
    «Entorno de corrección» cuando hay unidades en curso que chocan, se perdería la tarea de reaplicarla."""
    campos = ctx.ficha_urg(uid)
    if campos is None:
        no(f"falta su ficha impacto/{uid}.md", "escríbela con assets/plantillas/urgencia.md (references/urgentes.md)")
    if un.vacio(campos.get("donde se corrige")):
        no(f"impacto/{uid}.md no dice «Dónde se corrige»: sin eso no se sabe qué unidades tienen que reaplicarla",
           "escribe «Desarrollo» o «Entorno de corrección» (indice.py colision lo dice)")
    choques = ctx.colision(uid)["choques"]
    if not un.donde_se_corrige(campos) and choques:
        no(f"«Dónde se corrige» de impacto/{uid}.md no dice «Desarrollo» ni «Entorno de corrección» y choca con "
           f"unidades en curso ({'; '.join(choques)}): no se sabría quién tiene que reaplicarla",
           "escribe una de las dos en la ficha")


def aprobar(a, ctx, u, hoy, no, raiz, orden):
    """Aprueba una unidad Abierta, o vuelve a aprobar una Aprobada o Construida que ha crecido. Guarda la versión y los
    informes con que se aprueba: lo que llegue después pide otra aprobación antes de construirse."""
    fu = (a.fuente or "").strip().upper()
    if not re.fullmatch(r"FU-\d+", fu):
        no("falta la fuente de la aprobación del jefe de proyecto (chat o correo, R1)",
           f"catalógala con leer_fuentes.py y {orden} aprobada --fuente FU-nn")
    if (raiz / "fuentes").is_dir() and not list((raiz / "fuentes").glob(f"{fu}*.md")):
        no(f"{fu} no está en fuentes/", f"catalógala antes con leer_fuentes.py y repite {orden} aprobada --fuente {fu}")
    pend = [f"{n} punto {p.get('#', '?')}" for n, t, p in ctx.puntos_de(u.id)
            if p and mo.normaliza(p.get("decision", "")).strip(" *").startswith("pendiente")]
    if pend:
        no(f"puntos pendientes de aprobación en sus informes: {', '.join(pend)}",
           "decídelos (✔, ✗ o ❓ en «Decisión») y vuelve a aprobarla")
    if (a.comparte or "").strip():
        u.comparte = a.comparte.strip() if un.vacio(u.comparte) else f"{u.comparte}; {a.comparte.strip()}"
    mias, choques = set(ctx.cambian(u.id)), []
    for v in ctx.unidades:
        if v.id == u.id or v.urgente or v.estado not in (un.APROBADA, un.CONSTRUIDA):
            continue
        comunes = [o for o in ctx.cambian(v.id) if o in mias]
        decidido = v.id in un.RX_UNIDAD.findall(u.comparte) or u.id in un.RX_UNIDAD.findall(v.comparte)
        if comunes and not decidido:
            choques.append((v.id, comunes))
    if choques:
        v0, o0 = choques[0]
        no("comparte objetos con otra unidad aprobada y no hay decisión: "
           + "; ".join(f"{v} ({', '.join(o)})" for v, o in choques),
           f"decidid el orden o unidlas y escribidlo: --comparte \"{v0} en {o0[0]}: secuenciar ({v0} primero)\"")
    u.estado, u.aprobada = un.APROBADA, f"{hoy} · {fu}"
    u.aprobada_en, u.aprobada_con = ctx.m.version("F"), tuple(ctx.informes_de(u.id))


def construir(a, ctx, u, hoy, no, raiz, orden):
    crecida = ctx.crecida(u.id)
    if crecida:
        no(f"{u.id} ha crecido desde que se aprobó ({'; '.join(crecida)})",
           f"vuelve a aprobarla ({orden} aprobada --fuente FU-nn) o lleva lo nuevo a otra unidad")
    reaplicadas = {x.upper() for x in a.reaplicada or []}
    for g in reaplicadas:
        if g not in ctx.por_id or not ctx.por_id[g].urgente:
            no(f"--reaplicada {g}: no es una URG de analisis/cambios.md", "pon solo las URG que pide el encargo")
    falta = [(g, objs) for g, objs in ctx.reaplicar(u.id) if g not in reaplicadas]
    if falta:
        no("faltan correcciones urgentes por reaplicar en desarrollo: "
           + "; ".join(f"{g} en {', '.join(o)}" for g, o in falta),
           "reaplícalas y, cuando su prueba pase, confírmalo: " + " ".join(f"--reaplicada {g}" for g, _ in falta))
    ver = raiz / "construccion" / "verificacion" / f"{u.id}.json"
    if a.manual:
        marca = "manual"
    elif not ver.is_file():
        no(f"falta construccion/verificacion/{u.id}.json",
           f"pasa la orden «verificar» de construccion/{u.id}.md (sin Dev MCP, --manual)")
    else:
        try:
            d = json.loads(ver.read_text(encoding="utf-8"))
        except ValueError as e:
            no(f"{ver} no es JSON: {e}", f"vuelve a pasar la orden «verificar» de construccion/{u.id}.md")
        objetos = d.get("objetos", [])
        sin = [o for o in ctx.cambian(u.id) if o not in {x.get("pedido") for x in objetos}]
        if sin:
            no(f"la verificación no incluye {', '.join(sin)}",
               f"vuelve a pasar «verificar» con los objetos de construccion/{u.id}.md (indice.py encargo)")
        situacion = {un.objeto(o): f["situacion"] for f in ctx.filas_de(u.id) for o in f["objetos"]}
        malos, sin_leer = [], []
        for o in objetos:
            dif = dict(o.get("diferencias") or ({} if o.get("existe") else {"falta": True}))
            if o.get("pedido") not in ctx.cambian(u.id) and not o.get("diferencias"):
                continue
            if dif.pop("camposSinLeer", None):   # no se pudo leer: no es que esté mal construido
                sin_leer.append(o.get("pedido"))
            # §3 de un objeto que se modifica lleva solo los campos de esta unidad: los demás «sobran» y no cuentan
            if dif and not (situacion.get(o.get("pedido")) in ("modifica", "existe") and set(dif) <= {"sobranCampos"}):
                malos.append(f"{o.get('pedido')}: {', '.join(dif)}")
        if malos:
            no(f"lo construido no es lo del técnico: {'; '.join(malos)} (detalle en {ver})",
               "corrígelo en el entorno y vuelve a verificar; si el técnico está mal, corrígelo con un informe")
        if sin_leer:
            no(f"no se pudo leer {', '.join(sin_leer)} en el entorno", "repite «verificar» o usa --manual")
        marca = "verificada"
    u.estado, u.construida = un.CONSTRUIDA, f"{hoy} · {marca}"
    for g in sorted(reaplicadas):
        ctx.por_id[g].construida = f"{hoy} · reaplicada en {u.id}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("iniciar"); s.add_argument("carpeta"); s.add_argument("--nombre", required=True)
    s.add_argument("--cliente"); s.add_argument("--direccion"); s.add_argument("--tipo")
    s.set_defaults(f=iniciar)
    s = sub.add_parser("estado"); s.add_argument("carpeta"); s.set_defaults(f=estado)
    s = sub.add_parser("copia"); s.add_argument("carpeta"); s.set_defaults(f=copia)
    s = sub.add_parser("entregar"); s.add_argument("carpeta"); s.set_defaults(f=entregar)
    s.add_argument("--cambio", help="el DF de un cambio (df_docx.js --cambio): se anota en decisiones.md")
    s = sub.add_parser("cambio"); s.add_argument("carpeta"); s.add_argument("id"); s.set_defaults(f=cambio)
    s.add_argument("estado", choices=["abrir", "aprobada", "construida", "produccion", "descartada"])
    s.add_argument("--titulo"); s.add_argument("--fuente"); s.add_argument("--comparte"); s.add_argument("--ref")
    s.add_argument("--reaplicada", nargs="+", metavar="URG-nn"); s.add_argument("--manual", action="store_true")
    s.add_argument("--informe"); s.add_argument("--desatendida", action="store_true")
    a = ap.parse_args()
    for st in (sys.stdout, sys.stderr):
        st.reconfigure(encoding="utf-8", errors="replace")
    a.f(a)


if __name__ == "__main__":
    main()
