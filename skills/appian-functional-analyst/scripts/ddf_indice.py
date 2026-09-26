#!/usr/bin/env python3
"""Consulta un ddf.md sin leerlo entero: índice, búsqueda, fichas, impacto y piezas derivadas.

Uso:
  ddf_indice.py resumen    ddf.md                         recuento por tipo y estado, versión, preguntas abiertas
  ddf_indice.py indice     ddf.md [--tipo RF,PAN] [--estado ⚠️] [--modulo M2]
  ddf_indice.py buscar     ddf.md "fecha límite" alerta [--tipo PAN] [-n 15]
  ddf_indice.py ficha      ddf.md RF-017 PAN-07 [--lineas]
  ddf_indice.py impacto    ddf.md RF-017 PAN-07 [--nivel 2] [--con "responsable del paso"]
  ddf_indice.py seccion    ddf.md 10 --modulo M2 [--con "tipo de documento"]   texto de una sección (lo que no tiene ID)
  ddf_indice.py siguientes ddf.md [--modulo M2]            siguiente ID libre de cada tipo
  ddf_indice.py grafo      ddf.md -o grafo.json            piezas y referencias (para otras herramientas)
  ddf_indice.py derivadas  ddf.md [--escribir]             regenera Sec 7 (casos de uso) y la matriz de la Sec 16
  ddf_indice.py diagramas  ddf.md -o diagramas/ [--escribir]  extrae cada bloque Mermaid a .mmd y enlaza su imagen

Estados: 🔒 Validado · ✅ Decidido · 🔶 Inferido · ⚠️ Pendiente · ❓ No definido · Anulada · Respondida.
"""
import argparse, collections, json, math, pathlib, re, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import ddf_modelo as dm

ORDEN_TIPOS = ["ACT", "PAN", "RF", "RB", "CA", "INT", "NOT", "S", "P", "D", "CU"]


def clave(pid):
    t = dm.tipo_de(pid)
    nums = [int(x) for x in re.findall(r"\d+", pid)]
    return (ORDEN_TIPOS.index(t) if t in ORDEN_TIPOS else 99, pid.split("-")[1] if t == "CA" else "", nums)


def etiqueta(m, pid, largo=70):
    p = m.piezas.get(pid)
    if not p:
        return f"{pid} (no existe)"
    donde = f"Sec {p.seccion}" + (f" {p.modulo}" if p.modulo else "")
    est = f" {p.estado}" if p.estado else ""
    padre = f" ∈ {p.padre}" if p.padre else ""
    return f"{pid}{est} — {p.titulo[:largo]}  [{donde}, l.{p.ini + 1}{padre}]"


# ---------------------------------------------------------------- comandos
def c_resumen(m, a):
    v = m.version()
    print(f"Versión: v{v[0]}.{v[1]}" if v else "Versión: ¿?")
    tab = collections.defaultdict(collections.Counter)
    for p in m.piezas.values():
        tab[p.tipo][p.estado or "—"] += 1
    cols = dm.ESTADOS + ["—", "Anulada", "Respondida", "Vigente", "Sustituida"]
    usadas = [c for c in cols if any(tab[t][c] for t in tab)]
    print("\n| Tipo | Total | " + " | ".join(usadas) + " |")
    print("|---|---|" + "---|" * len(usadas))
    for t in sorted(tab, key=lambda x: ORDEN_TIPOS.index(x) if x in ORDEN_TIPOS else 99):
        print(f"| {t} | {sum(tab[t].values())} | " + " | ".join(str(tab[t][c] or "") for c in usadas) + " |")
    abiertas = [p for p in m.por_tipo("P") if not p.anulada]
    prio = collections.Counter(next((e for e in "🔴🟡🟢" if e in m.lineas[p.ini]), "?") for p in abiertas)
    print(f"\nPreguntas abiertas: {len(abiertas)} (🔴 {prio['🔴']} · 🟡 {prio['🟡']} · 🟢 {prio['🟢']})")
    if m.duplicados:
        print(f"⚠ IDs definidos dos veces: {m.duplicados[:10]}")


def _filtra(m, a):
    tipos = set(a.tipo.split(",")) if getattr(a, "tipo", None) else None
    for p in sorted(m.piezas.values(), key=lambda p: clave(p.id)):
        if tipos and p.tipo not in tipos:
            continue
        if getattr(a, "estado", None) and p.estado != a.estado:
            continue
        if getattr(a, "modulo", None) and p.modulo != a.modulo:
            continue
        yield p


def c_indice(m, a):
    for p in _filtra(m, a):
        if p.tipo == "CA" and not a.tipo:
            continue
        print(etiqueta(m, p.id, 90))


def patron(termino):
    """«tipos de documento» encuentra también «tipo de documento» y «tipología de documentos»."""
    raices = [w[:-1] if len(w) > 4 and w.endswith("s") else w for w in re.findall(r"\w+", dm.normaliza(termino))]
    return re.compile(r"\b" + r"\w*\W+".join(re.escape(w) for w in raices) + r"\w*")


def c_buscar(m, a):
    terminos = [dm.normaliza(t) for t in a.terminos]
    pats = [patron(t) for t in a.terminos]
    tipos = set(a.tipo.split(",")) if a.tipo else None
    res = []
    candidatas = [p for p in m.piezas.values() if p.tipo != "CA" and not (tipos and p.tipo not in tipos)]
    textos = {p.id: dm.normaliza(m.texto(p.id)) for p in candidatas}
    # un término raro pesa más que uno que sale en todas partes («título», «comentario»)
    peso = {t: math.log((len(candidatas) + 1) / (1 + sum(bool(pt.search(x)) for x in textos.values()))) + 1
            for t, pt in zip(terminos, pats)}
    for p in candidatas:
        txt = textos[p.id]
        tit = dm.normaliza(p.titulo)
        hallados = [(t, pt) for t, pt in zip(terminos, pats) if pt.search(txt)]
        if not hallados:
            continue
        score = sum(peso[t] * (4 + math.log1p(len(pt.findall(txt))) + 3 * bool(pt.search(tit))) for t, pt in hallados)
        hallados = [t for t, _ in hallados]
        if p.forma == "ficha":
            score -= math.log1p(p.fin - p.ini)  # una ficha larga lo contiene todo: desempata a favor de las concretas
        res.append((score, p.id, hallados))
    res.sort(key=lambda x: -x[0])
    if not res:
        print("Sin resultados.")
    for s, pid, h in res[: a.n]:
        print(f"{s:5.1f}  {etiqueta(m, pid)}  ← {', '.join(h)}")
    # menciones fuera de piezas (texto de procesos, estados, datos)
    cubiertas = set()
    for p in m.piezas.values():
        cubiertas.update(range(p.ini, p.fin))
        cubiertas.update(p.apariciones)
    sueltas = []
    for i, l in enumerate(m.lineas):
        sec, mod = m.seccion_de_linea[i]
        if sec in dm.SECCIONES_DERIVADAS or i in cubiertas or l.startswith("#"):
            continue
        nl = dm.normaliza(l)
        if all(pt.search(nl) for pt in pats):
            sueltas.append((i, l.strip()[:90]))
    if sueltas:
        print(f"\nTexto sin ID que también lo menciona ({len(sueltas)}):")
        for i, l in sueltas[:8]:
            print(f"  {contexto(m, i)} (l.{i + 1}): {l}")


def c_ficha(m, a):
    veces = collections.Counter(l for l in m.lineas if l.strip())
    for pid in a.ids:
        p = m.piezas.get(pid)
        if not p:
            print(f"── {pid}: no existe\n")
            continue
        print(f"── {etiqueta(m, pid, 90)} · líneas {p.ini + 1}–{p.fin}")
        if p.forma == "fila" and p.cabecera:
            print(p.cabecera)
        for k, l in enumerate(m.bloque(pid)):
            rep_ = "⟂" if a.lineas and veces[l] > 1 else " "
            print(f"{p.ini + k + 1:6d}{rep_} {l}" if a.lineas else l)
        for ap in p.apariciones:
            print(f"   (también en l.{ap + 1}: {m.lineas[ap][:110]})")
        print()
    if a.lineas:
        print("⟂ = la línea está igual en otro sitio del ddf.md: al editar, incluye la línea de al lado para que sea única.")


def contexto(m, linea):
    """«Sec 10 M1 · 10.3 Informe»: dónde está una línea, estable aunque cambien los números de línea."""
    sec, mod = m.seccion_de_linea[linea]
    tit = ""
    for k in range(linea, -1, -1):
        l = m.lineas[k]
        if dm.RX_SECCION.match(l) or dm.RX_MODULO_H3.match(l):
            break
        mb = re.match(r"^\*\*([^*]{3,80})\*\*", l)
        if l.startswith("#") or (mb and not dm.RX_FICHA.match(l)):
            tit = l.strip("#* ").strip() if l.startswith("#") else mb.group(1)
            break
    return f"Sec {sec}" + (f" {mod}" if mod else "") + (f" · {tit[:50]}" if tit else "")


def c_seccion(m, a):
    """Imprime una sección (o la parte de un módulo) con números de línea: para el texto sin ID."""
    lineas = [i for i, (sec, mod) in enumerate(m.seccion_de_linea)
              if sec == a.n and (not a.modulo or mod == a.modulo)]
    if a.con:
        pats = [patron(x) for x in a.con]
        dentro = set(lineas)
        elegidas = set()
        for i in lineas:
            if any(pt.search(dm.normaliza(m.lineas[i])) for pt in pats):
                if m.lineas[i].startswith("|"):  # la tabla entera y el título que la precede
                    a0 = i
                    while a0 - 1 in dentro and m.lineas[a0 - 1].startswith("|"):
                        a0 -= 1
                    b0 = i
                    while b0 + 1 in dentro and m.lineas[b0 + 1].startswith("|"):
                        b0 += 1
                    t0 = next((k for k in range(a0 - 1, max(a0 - 4, -1), -1) if m.lineas[k].strip()), None)
                    elegidas |= set(range(a0, b0 + 1)) | ({t0} if t0 is not None else set())
                else:
                    elegidas.add(i)
        lineas = sorted(elegidas)
    if not lineas:
        print("Nada.")
    for i in lineas[: a.max]:
        print(f"{i + 1:6d}  {m.lineas[i]}")
    if len(lineas) > a.max:
        print(f"… {len(lineas) - a.max} líneas más (acota con --modulo o --con)")


def dependencias(m, ids, nivel=1, con=None):
    """Qué hay que revisar si cambian estas piezas: las que las citan (fuerte) y a las que remiten (débil)."""
    entrada = {m.raiz(i) for i in ids}
    citan, remite, sueltas = {}, {}, {}
    frontera = set(entrada)
    for n in range(nivel):
        nueva = set()
        for pid in frontera:
            p = m.piezas.get(pid)
            if not p:
                continue
            objetivos = {pid} | set(p.hijos)
            for o in objetivos:
                for c in m.citada_por.get(o, ()):
                    r = m.raiz(c)
                    if r in entrada or r == pid:
                        continue
                    # con --con se descartan las que no hablan del tema, salvo las que se verifican con los
                    # criterios de la pieza (sus RF): si cambian o se añaden criterios, hay que tocarlas
                    if con and o == pid and not any(x in dm.normaliza(m.texto(c)) for x in con):
                        continue
                    citan.setdefault(r, set()).add(f"cita {o}" if n == 0 else f"cita {o} (nivel {n + 1})")
                    nueva.add(r)
                for l in m.menciones.get(o, ()):
                    if con and not any(x in dm.normaliza(m.lineas[l]) for x in con):
                        continue
                    sueltas.setdefault(l, set()).add(o)
            if n == 0:
                for r0 in p.refs:
                    r = m.raiz(r0)
                    if r not in entrada and r in m.piezas:
                        if con and not any(x in dm.normaliza(m.texto(r)) for x in con):
                            continue
                        remite.setdefault(r, set()).add(f"{pid} la cita")
        frontera = nueva - entrada
    for r in citan:
        remite.pop(r, None)
    return entrada, citan, remite, sueltas


def c_impacto(m, a):
    con = [dm.normaliza(x) for x in a.con] if a.con else None
    entrada, citan, remite, sueltas = dependencias(m, a.ids, a.nivel, con)
    if con:
        print(f"(solo dependencias cuyo texto menciona: {', '.join(a.con)})")
    print("Piezas de entrada:")
    for pid in sorted(entrada, key=clave):
        print("  " + etiqueta(m, pid))
        p = m.piezas.get(pid)
        if p and p.hijos:
            print(f"      criterios propios: {', '.join(p.hijos)}")
    def lista(titulo, d):
        print(f"\n{titulo} ({len(d)}):")
        por_tipo = collections.defaultdict(list)
        for pid in d:
            por_tipo[dm.tipo_de(pid)].append(pid)
        for t in sorted(por_tipo, key=lambda x: ORDEN_TIPOS.index(x) if x in ORDEN_TIPOS else 99):
            for pid in sorted(por_tipo[t], key=clave):
                print(f"  {etiqueta(m, pid, 60)}  ← {'; '.join(sorted(d[pid]))}")
    lista("Revisar: dependen de ellas (las citan)", citan)
    lista("Revisar si cambia el contenido: ellas remiten a", remite)
    if sueltas:
        print(f"\nTexto sin ID que las menciona ({len(sueltas)} líneas; cítalo por su sección, no por el número de línea):")
        for l in sorted(sueltas)[:25]:
            print(f"  {contexto(m, l)} [{', '.join(sorted(sueltas[l]))}] (l.{l + 1}): {m.lineas[l].strip()[:80]}")
    if con:
        pats = [patron(x) for x in a.con]
        ps = []
        for p in m.por_tipo("P"):
            if p.anulada or p.id in citan or p.id in entrada:
                continue
            txt = dm.normaliza(m.texto(p.id))
            n = sum(len(pt.findall(txt)) for pt in pats)
            if all(pt.search(txt) for pt in pats):
                ps.append((-n, p.id))
        if ps:
            print(f"\nPreguntas abiertas del mismo tema ({len(ps)}, las 6 que más lo mencionan): ¿las contesta el punto?")
            for _, x in sorted(ps)[:6]:
                print("  " + etiqueta(m, x, 80))
    pan = sorted({x for x in list(entrada) + list(citan) if x.startswith("PAN-")}, key=clave)
    if pan:
        print(f"\nPantallas afectadas (para el prototipo, si lo hay): {', '.join(pan)}")
    val = [x for x in list(entrada) + list(citan) if m.piezas.get(x) and m.piezas[x].estado == "🔒"]
    if val:
        print(f"\n🔒 Validadas por el cliente (cambiarlas requiere aprobación): {', '.join(sorted(val, key=clave))}")


def c_siguientes(m, a):
    usados = collections.defaultdict(set)
    del_mod = collections.defaultdict(set)
    for pid, p in m.piezas.items():
        if p.tipo == "CA":
            continue
        n = dm.numero(pid)
        usados[p.tipo].add(n)
        if a.modulo and p.modulo == a.modulo:
            del_mod[p.tipo].add(n)
    ancho = {"RF": 3, "RB": 3, "PAN": 2, "ACT": 2, "CU": 3, "INT": 3, "NOT": 3, "P": 3, "S": 3, "D": 3}
    for t in ["ACT", "PAN", "RF", "RB", "INT", "NOT", "P", "S", "D"]:
        glob = (max(usados[t]) + 1) if usados[t] else 1
        nota = ""
        if a.modulo and del_mod[t]:
            n = max(del_mod[t]) + 1
            nota = f"   (tras el último de {a.modulo})"
            if n in usados[t]:
                n, nota = glob, f"   (el hueco de {a.modulo} está lleno: siguiente libre al final)"
        else:
            n = glob
        print(f"{t}-{n:0{ancho[t]}d}{nota}")
    print("Criterios: siguiente .n de la ficha (p. ej. CA-PAN-07.12 tras CA-PAN-07.11)")


def c_grafo(m, a):
    nodos = [{"id": p.id, "tipo": p.tipo, "titulo": p.titulo, "seccion": p.seccion, "modulo": p.modulo,
              "estado": p.estado, "padre": p.padre, "fuentes": sorted(p.fuentes), "linea": p.ini + 1}
             for p in sorted(m.piezas.values(), key=lambda p: clave(p.id))]
    aristas = [{"de": p.id, "a": r} for p in m.piezas.values() for r in sorted(p.refs) if r in m.piezas]
    aristas += [{"de": p.id, "a": h, "tipo": "contiene"} for p in m.piezas.values() for h in p.hijos]
    pathlib.Path(a.o).write_text(json.dumps({"nodos": nodos, "aristas": aristas}, ensure_ascii=False, indent=1),
                                 encoding="utf-8")
    print(f"{a.o}: {len(nodos)} piezas, {len(aristas)} referencias")


# ------------------------------------------------ secciones derivadas (7 y 16)
def _campo(m, pid, nombre):
    return m.campo(pid, nombre)


def seccion7(m):
    filas = []
    for p in sorted(m.por_tipo("ACT"), key=lambda p: clave(p.id)):
        if p.forma != "ficha":
            continue
        actor = _campo(m, p.id, "Actor")
        if dm.normaliza(actor).startswith("sistema"):
            continue
        cu = f"CU-{dm.numero(p.id):03d}"
        tit = f"~~{p.titulo}~~ (anulada)" if p.anulada else p.titulo
        actor = re.sub(r"\s*\[FU-[^]]*\]", "", actor)
        filas.append(f"| {cu} | {tit} | {actor} | {p.modulo} | {p.id} |")
    return ["Los casos de uso son las tareas de usuario de la Sec 6 (CU-0xx = ACT-xx): su detalle está en la ficha "
            "de la tarea. Tabla generada por `ddf_indice.py derivadas`.", "",
            "| CU | Caso de uso | Actor principal | Módulo | Actividad |", "|---|---|---|---|---|"] + filas


def matriz16(m):
    filas, sin = [], []
    for p in sorted(m.por_tipo("RF"), key=lambda p: clave(p.id)):
        prio = _campo(m, p.id, "Prioridad") or "—"
        if p.anulada:
            filas.append(f"| ~~{p.id}~~ | {p.modulo} | {prio} | — | Anulado |")
            continue
        ver = _campo(m, p.id, "Se verifica en")
        cas = sorted({x for x in dm.ids_en(ver) if x.startswith("CA-")}, key=clave)
        faltan = [x for x in cas if x not in m.piezas]
        if not cas:
            est = "❌ Falta criterio → Sec 17"
            sin.append(p.id)
        elif faltan:
            est = f"❌ No existe {', '.join(faltan)}"
            sin.append(p.id)
        else:
            est = "Sí"
        filas.append(f"| {p.id} | {p.modulo} | {prio} | {', '.join(cas) or '—'} | {est} |")
    vig = sum(1 for p in m.por_tipo("RF") if not p.anulada)
    return (["| RF | Módulo | Prioridad | Se verifica en | ¿Cubierto? |", "|---|---|---|---|---|"] + filas +
            ["", f"**Resultado**: {vig} RF vigentes; {len(sin)} sin criterio" + (f" ({', '.join(sin)})" if sin else "") +
             ". Matriz generada por `ddf_indice.py derivadas`."])


def aplica_derivadas(texto):
    m = dm.Modelo(texto)
    L = texto.split("\n")
    def rango(n):
        ini = next((i for i, l in enumerate(L) if re.match(rf"^## {n}\.", l)), None)
        if ini is None:
            return None, None
        fin = next((i for i in range(ini + 1, len(L)) if L[i].startswith("## ")), len(L))
        return ini, fin
    # Sec 16: sustituye la primera tabla y la línea «**Resultado**» siguiente
    ini, fin = rango(16)
    if ini is not None:
        t0 = next((i for i in range(ini, fin) if L[i].startswith("| RF")), None)
        if t0 is not None:
            t1 = t0
            while t1 < fin and L[t1].startswith("|"):
                t1 += 1
            r = next((i for i in range(t1, min(t1 + 4, fin)) if L[i].startswith("**Resultado**")), None)
            L[t0:(r + 1 if r is not None else t1)] = matriz16(m)
        else:
            L[ini + 1:ini + 1] = [""] + matriz16(m)
    # Sec 7: solo si ya es la tabla derivada (módulos, volumen-grande.md) o está vacía; la escrita a mano
    # según la plantilla (diagrama, tabla y fichas de CU con sus propios IDs) no se toca
    ini, fin = rango(7)
    sec7 = False
    if ini is not None:
        cuerpo = "\n".join(L[ini + 1:fin])
        if "generada por `ddf_indice.py derivadas`" in cuerpo or not re.sub(r"[\s❓—-]", "", cuerpo):
            L[ini + 1:fin] = [""] + seccion7(m) + [""]
            sec7 = True
    return "\n".join(L), sec7


def c_derivadas(m, a):
    texto = pathlib.Path(a.ddf).read_text(encoding="utf-8")
    nuevo, sec7 = aplica_derivadas(texto)
    if a.escribir:
        pathlib.Path(a.ddf).write_text(nuevo, encoding="utf-8")
        print(("Sec 7 y matriz" if sec7 else "Matriz") + f" de la Sec 16 regenerada{'s' if sec7 else ''} en {a.ddf}"
              + ("" if sec7 else " (la Sec 7 está escrita a mano: no se toca)"))
    else:
        print("\n".join(matriz16(m)[-1:]))
        print("(usa --escribir para actualizar el fichero)")


# ------------------------------------------------ diagramas
def extrae_diagramas(texto, carpeta, escribir=True):
    """Cada bloque ```mermaid se guarda como .mmd; si no le sigue una imagen, se añade ![pie](carpeta/x.png)."""
    L = texto.split("\n")
    out, i, n, nombres = [], 0, 0, []
    sec, mod, titulo = "", "", ""
    carpeta = pathlib.Path(carpeta)
    cambiados = []
    if escribir:
        carpeta.mkdir(parents=True, exist_ok=True)
    while i < len(L):
        l = L[i]
        ms = dm.RX_SECCION.match(l)
        if ms:
            sec, mod = ms.group(1), ""
            mm = dm.RX_MODULO_EN_H2.search(l)
            mod = mm.group(1) if mm else ""
        mm = dm.RX_MODULO_H3.match(l)
        if mm:
            mod = mm.group(1)
        if l.startswith("#"):
            titulo = l.lstrip("# ").strip()
        if l.strip() == "```mermaid":
            j = i + 1
            while j < len(L) and L[j].strip() != "```":
                j += 1
            codigo = "\n".join(L[i + 1:j]) + "\n"
            k = j + 1
            while k < len(L) and not L[k].strip():
                k += 1
            img = re.match(r"!\[([^\]]*)\]\(([^)]+)\.png\)", L[k]) if k < len(L) else None
            out.extend(L[i:j + 1])
            if img:
                nombre = pathlib.Path(img.group(2)).name
            else:
                n += 1
                # pie: la línea corta que precede al bloque («**Proceso P1 — Requerimiento**») o el título
                previa = next((L[x].strip() for x in range(i - 1, max(i - 4, -1), -1) if L[x].strip()), "")
                if previa and not previa.startswith(("#", "|", "-", "!")) and len(previa) <= 140:
                    titulo = re.sub(r"\s*\(.*?\)\s*$", "", previa.replace("**", "")).rstrip(".: ")
                base = re.sub(r"[^a-z0-9]+", "-", dm.normaliza(f"s{sec}-{mod}-{titulo}"))[:50].strip("-")
                nombre = base
                c = 2
                while nombre in nombres:
                    nombre, c = f"{base}-{c}", c + 1
                pie = re.sub(r"^[\d.]+\s*", "", titulo) or "Diagrama"
                out.extend(["", f"![{pie}]({carpeta.as_posix()}/{nombre}.png)"])
            nombres.append(nombre)
            f = carpeta / f"{nombre}.mmd"
            if not f.exists() or f.read_text(encoding="utf-8") != codigo:
                cambiados.append(f.name)
                if escribir:
                    f.write_text(codigo, encoding="utf-8")
            i = j + 1
            continue
        out.append(l)
        i += 1
    extrae_diagramas.cambiados = cambiados
    return "\n".join(out), nombres


def c_diagramas(m, a):
    texto = pathlib.Path(a.ddf).read_text(encoding="utf-8")
    nuevo, nombres = extrae_diagramas(texto, a.o, a.escribir)
    cambiados = extrae_diagramas.cambiados
    if a.escribir and nuevo != texto:
        pathlib.Path(a.ddf).write_text(nuevo, encoding="utf-8")
    print(f"{len(nombres)} diagramas; nuevos o cambiados: {len(cambiados)}" + (f" → {', '.join(cambiados)}" if cambiados else ""))
    if not a.escribir:
        print("(no se ha escrito nada: usa --escribir para guardar los .mmd y enlazar las imágenes que falten)")
    elif cambiados:
        print("Renderiza solo esos: render_mermaid.py " + " ".join(str(pathlib.Path(a.o) / c) for c in cambiados))


def main():
    if hasattr(__import__("signal"), "SIGPIPE"):
        import signal
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)  # `| head` sin traza de error
    for s in (sys.stdout, sys.stderr):
        s.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    def nuevo(nombre, f):
        s = sub.add_parser(nombre)
        s.add_argument("ddf")
        s.set_defaults(f=f)
        return s
    nuevo("resumen", c_resumen)
    s = nuevo("indice", c_indice); s.add_argument("--tipo"); s.add_argument("--estado"); s.add_argument("--modulo")
    s = nuevo("buscar", c_buscar); s.add_argument("terminos", nargs="+"); s.add_argument("--tipo"); s.add_argument("-n", type=int, default=15)
    s = nuevo("ficha", c_ficha); s.add_argument("ids", nargs="+"); s.add_argument("--lineas", action="store_true")
    s = nuevo("impacto", c_impacto); s.add_argument("ids", nargs="+"); s.add_argument("--nivel", type=int, default=1)
    s.add_argument("--con", nargs="+", help="solo dependencias cuyo texto menciona alguno de estos términos")
    s = nuevo("siguientes", c_siguientes); s.add_argument("--modulo")
    s = nuevo("seccion", c_seccion); s.add_argument("n"); s.add_argument("--modulo"); s.add_argument("--con", nargs="+")
    s.add_argument("--max", type=int, default=150)
    s = nuevo("grafo", c_grafo); s.add_argument("-o", default="grafo.json")
    s = nuevo("derivadas", c_derivadas); s.add_argument("--escribir", action="store_true")
    s = nuevo("diagramas", c_diagramas); s.add_argument("-o", default="diagramas"); s.add_argument("--escribir", action="store_true")
    a = ap.parse_args()
    a.f(dm.cargar(a.ddf), a)


if __name__ == "__main__":
    main()
