"""Ajustes de la colocación del motor (Mermaid) para que el dibujo de draw.io no se pise.

El motor da a cada paso el ancho de su texto, pero en draw.io las tareas miden siempre 120×80 y las
etiquetas de eventos y puertas ocupan hasta 110 px de ancho. Aquí, sin navegador:
- se elige a qué lado va la etiqueta de cada evento o puerta, para que ningún flujo la cruce;
- se separan los pasos solo lo necesario (nunca se acercan) para que ninguna forma, etiqueta o nota
  pise a otra; cada eje se transforma con una función creciente, así que los tramos rectos siguen rectos;
- se colocan las notas junto a su paso y los participantes externos debajo de los carriles.
Solo usa la biblioteca estándar.
"""
import bisect

ANCHO_ETIQUETA = 110     # ancho al que se ajusta la etiqueta de un evento o una puerta
LINEA = 15               # alto de una línea de texto (12 px)
SEPARACION_X = 36        # hueco mínimo entre formas en horizontal
SEPARACION_Y = 28        # hueco mínimo entre formas en vertical, dentro de un carril
MARGEN = 16              # hueco mínimo entre una forma y el borde de su carril
NOTA_ANCHO = 160
NOTA_HUECO = 18          # distancia entre la nota y su paso (se ve la línea de asociación)
EXTERNO_ALTO = 60
EXTERNO_HUECO = 40      # hueco entre carriles y participantes: ahí va la etiqueta del flujo de mensaje
ANCHO_LEGIBLE = 1600     # más ancho que esto, en una página vertical el texto queda pequeño


def alto_texto(texto, ancho=ANCHO_ETIQUETA):
    """Alto aproximado de un texto de 12 px ajustado a `ancho` (por exceso: mejor sobra que se pise)."""
    if not texto:
        return 0
    lineas, actual = 1, 0
    for palabra in str(texto).split():
        largo = len(palabra) * 7
        if actual and actual + 4 + largo > ancho - 8:
            lineas += 1
            actual = largo
        else:
            actual += (4 if actual else 0) + largo
    return lineas * LINEA + 6


def ancho_nota(texto):
    """El ancho normal de una nota, o más si una palabra no cabe en él (el nombre de una regla, una expresión): draw.io
    no parte las palabras y se saldría de la caja. 8 px por letra, por exceso, también con mayúsculas."""
    palabra = max((len(p) for p in str(texto or "").split()), default=0)
    return max(NOTA_ANCHO, palabra * 8 + 20)


def alto_nota(texto):
    return max(36, alto_texto(texto, ancho_nota(texto)) + 12)


# ---------------------------------------------------------------- lado de las etiquetas y las notas
def lados_usados(proc, geo):
    """Para cada paso, qué lados (arriba/abajo) usan sus flujos según la geometría del motor y hacia dónde
    siguen en horizontal (-1 izquierda, 0, 1 derecha): {paso: {lado: {sentidos}}}. Los flujos de mensaje van
    a los participantes externos, que están debajo: usan el lado de abajo en vertical."""
    centro = {pid: geo["pasos"][pid][:2] for pid in geo["pasos"]}
    externos = set(proc.get("externos") or [])
    usados = {pid: {} for pid in centro}
    for i, f in enumerate(proc["flujos"]):
        pts = geo["flujos"][i] if i < len(geo.get("flujos", [])) else []
        for extremo, otro, vecino in (("de", "a", pts[0] if pts else None), ("a", "de", pts[-1] if pts else None)):
            pid = f[extremo]
            if pid not in usados:
                continue
            if f[otro] in externos:
                usados[pid].setdefault("abajo", set()).add(0)
                continue
            vecino = vecino or centro.get(f[otro])
            if vecino is None:
                continue
            dx, dy = vecino[0] - centro[pid][0], vecino[1] - centro[pid][1]
            if abs(dy) > abs(dx) + 1:
                destino = centro.get(f[otro], vecino)[0] - centro[pid][0]
                usados[pid].setdefault("abajo" if dy > 0 else "arriba", set()).add(
                    0 if abs(destino) < 2 else (1 if destino > 0 else -1))
    return usados


def lados_etiqueta(proc, usados, eventos, puertas):
    """Lado de la etiqueta de cada evento (abajo por defecto) y puerta (arriba): el contrario si un flujo
    llega o sale por ese lado y el otro está libre."""
    lados = {}
    for p in proc["pasos"]:
        if p["tipo"] not in eventos | puertas or not p.get("nombre"):
            continue
        normal, otro = ("abajo", "arriba") if p["tipo"] in eventos else ("arriba", "abajo")
        u = usados.get(p["id"], {})
        lados[p["id"]] = otro if normal in u and otro not in u else normal
    return lados


def lados_nota(proc, usados, lados):
    """Sitio de cada nota respecto a su paso: (lado, desplazamiento). Arriba, salvo que lo usen la etiqueta o
    un flujo y abajo esté libre. Si un flujo sale por ese lado y sigue hacia la derecha, la nota se corre a la
    izquierda (y al revés), para que el flujo no la cruce."""
    out = []
    for n in proc.get("notas") or []:
        u = usados.get(n["paso"], {})
        ocupado = set(u) | ({lados[n["paso"]]} if n["paso"] in lados else set())
        lado = "abajo" if "arriba" in ocupado and "abajo" not in ocupado else "arriba"
        sentidos = u.get(lado, set()) - {0}
        desplazamiento = "izquierda" if sentidos == {1} else "derecha" if sentidos == {-1} else "centro"
        out.append((lado, desplazamiento))
    return out


def x_nota(cx, desplazamiento, ancho=NOTA_ANCHO):
    """x del borde izquierdo de una nota según su desplazamiento respecto al centro de su paso."""
    return {"izquierda": cx - 10 - ancho, "derecha": cx + 10}.get(desplazamiento, cx - ancho / 2)


# ---------------------------------------------------------------- separación
def _mapa(pares):
    """Función creciente que lleva cada coordenada vieja a la nueva, lineal entre los puntos dados."""
    pares = sorted(pares)
    xs, ys = [a for a, _ in pares], [b for _, b in pares]

    def f(v):
        if not xs:
            return v
        if v <= xs[0]:
            return v + ys[0] - xs[0]
        if v >= xs[-1]:
            return v + ys[-1] - xs[-1]
        k = bisect.bisect_right(xs, v) - 1
        if xs[k + 1] == xs[k]:
            return ys[k]
        return ys[k] + (v - xs[k]) * (ys[k + 1] - ys[k]) / (xs[k + 1] - xs[k])
    return f


def extensiones(proc, lados, notas_lado, tam, eventos, puertas):
    """Cuánto ocupa cada paso alrededor de su centro (izquierda, derecha, arriba, abajo), con etiqueta y notas."""
    ext = {}
    for p in proc["pasos"]:
        w, h = tam[p["tipo"]]
        izq = der = w / 2
        arr = aba = h / 2
        lado = lados.get(p["id"])
        if lado:
            izq = der = max(w / 2, ANCHO_ETIQUETA / 2)
            alto = alto_texto(p.get("nombre")) + 2
            if lado == "abajo":
                aba += alto
            else:
                arr += alto
        ext[p["id"]] = [izq, der, arr, aba]
    for n, (lado, desplazamiento) in zip(proc.get("notas") or [], notas_lado):
        e = ext.get(n["paso"])
        if e is None:
            continue
        ancho = ancho_nota(n.get("texto"))
        izq = -x_nota(0, desplazamiento, ancho)
        e[0] = max(e[0], izq)
        e[1] = max(e[1], ancho - izq)
        extra = NOTA_HUECO + alto_nota(n.get("texto"))
        if lado == "arriba":
            e[2] += extra
        else:
            e[3] += extra
    return ext


def separar(proc, geo, ext, cabecera):
    """Separa los pasos para que nada se pise. Modifica `geo` (carriles, pasos, flujos y ancho)."""
    carril = {p["id"]: p["carril"] for p in proc["pasos"]}
    cx = {pid: geo["pasos"][pid][0] for pid in carril}
    cy = {pid: geo["pasos"][pid][1] for pid in carril}

    # eje x: dentro de un carril, dos pasos que se solapan en vertical no pueden acercarse en horizontal
    def solapan_y(a, b):
        return carril[a] == carril[b] and cy[a] - ext[a][2] < cy[b] + ext[b][3] and cy[b] - ext[b][2] < cy[a] + ext[a][3]

    orden = sorted(carril, key=lambda i: cx[i])
    grupos = []                       # (x viejo, [pasos]) con la misma x: siguen alineados
    for pid in orden:
        if grupos and abs(cx[pid] - grupos[-1][0]) <= 2:
            grupos[-1][1].append(pid)
        else:
            grupos.append((cx[pid], [pid]))
    nuevo_x, grupo_de = [], {}
    for k, (c, miembros) in enumerate(grupos):
        v = max(c, cabecera + MARGEN + max(ext[m][0] for m in miembros)) if k == 0 else nuevo_x[-1] + (c - grupos[k - 1][0])
        for j in miembros:
            for i in grupo_de:
                if solapan_y(i, j):
                    v = max(v, nuevo_x[grupo_de[i]] + ext[i][1] + SEPARACION_X + ext[j][0])
        nuevo_x.append(v)
        for j in miembros:
            grupo_de[j] = k
    fx = _mapa([(c, v) for (c, _), v in zip(grupos, nuevo_x)])

    # eje y, carril a carril: cada paso dentro de su carril con margen; en el carril, dos pasos que se
    # solapan en horizontal no pueden acercarse en vertical
    nx = {pid: fx(cx[pid]) for pid in carril}

    def solapan_x(a, b):
        return nx[a] - ext[a][0] < nx[b] + ext[b][1] and nx[b] - ext[b][0] < nx[a] + ext[a][1]

    pares, nuevo_y = [], {}
    arriba_nuevo = 0.0
    for c in proc["carriles"]:
        y, h = geo["carriles"][c][:2]
        pares.append((y, arriba_nuevo))
        suyos = sorted((pid for pid in carril if carril[pid] == c), key=lambda i: cy[i])
        filas = []
        for pid in suyos:
            if filas and abs(cy[pid] - filas[-1][0]) <= 2:
                filas[-1][1].append(pid)
            else:
                filas.append((cy[pid], [pid]))
        previo = (y, arriba_nuevo)
        for vy, miembros in filas:
            v = max(arriba_nuevo + MARGEN + max(ext[m][2] for m in miembros), previo[1] + (vy - previo[0]))
            for j in miembros:
                for i, ny in nuevo_y.items():
                    if carril[i] == c and solapan_x(i, j):
                        v = max(v, ny + ext[i][3] + SEPARACION_Y + ext[j][2])
            for j in miembros:
                nuevo_y[j] = v
            pares.append((vy, v))
            previo = (vy, v)
        abajo = max([previo[1] + (y + h - previo[0]), arriba_nuevo + h] +
                    [nuevo_y[j] + ext[j][3] + MARGEN for j in suyos])
        geo["carriles"][c] = (arriba_nuevo, abajo - arriba_nuevo)
        pares.append((y + h, abajo))
        arriba_nuevo = abajo
    fy = _mapa(pares)

    derecha = max([fx(geo["ancho"])] + [nx[pid] + ext[pid][1] + MARGEN for pid in carril])
    for pid in carril:
        geo["pasos"][pid] = (nx[pid], nuevo_y[pid])
    alto = arriba_nuevo
    geo["flujos"] = [[(min(max(fx(x), cabecera + 6), derecha - 6), min(max(fy(y), 6), alto - 6)) for x, y in pts]
                     for pts in geo.get("flujos", [])]
    geo["ancho"] = derecha
    return geo


# ---------------------------------------------------------------- notas y participantes externos
def colocar_notas(proc, geo, notas_lado, tam):
    """Caja (x, y, w, h) absoluta de cada nota, encima o debajo de su paso."""
    tipo = {p["id"]: p["tipo"] for p in proc["pasos"]}
    cajas = []
    for n, (lado, desplazamiento) in zip(proc.get("notas") or [], notas_lado):
        cx, cy = geo["pasos"][n["paso"]][:2]
        w, h = tam[tipo[n["paso"]]]
        alto = alto_nota(n.get("texto"))
        etiqueta = 0
        if lado == geo.get("etiquetas", {}).get(n["paso"]):
            etiqueta = alto_texto(next(p.get("nombre") for p in proc["pasos"] if p["id"] == n["paso"])) + 2
        if lado == "arriba":
            y = cy - h / 2 - etiqueta - NOTA_HUECO - alto
        else:
            y = cy + h / 2 + etiqueta + NOTA_HUECO
        ancho = ancho_nota(n.get("texto"))
        cajas.append((x_nota(cx, desplazamiento, ancho), y, ancho, alto))
    geo["anotaciones"] = cajas
    return geo


def colocar_externos(proc, geo):
    """Cada participante externo, una franja debajo de los carriles: {nombre: (y, alto)}."""
    y = max((a + b for a, b in (v[:2] for v in geo["carriles"].values())), default=0) + EXTERNO_HUECO
    geo["externos"] = {}
    for nombre in proc.get("externos") or []:
        geo["externos"][nombre] = (y, EXTERNO_ALTO)
        y += EXTERNO_ALTO + EXTERNO_HUECO / 2
    return geo


def ajustar(proc, geo, tam, eventos, puertas, cabecera):
    """Todo lo anterior, en orden: lados, separación, notas y externos."""
    usados = lados_usados(proc, geo)
    lados = lados_etiqueta(proc, usados, eventos, puertas)
    notas_lado = lados_nota(proc, usados, lados)
    separar(proc, geo, extensiones(proc, lados, notas_lado, tam, eventos, puertas), cabecera)
    geo["etiquetas"] = lados
    colocar_notas(proc, geo, notas_lado, tam)
    colocar_externos(proc, geo)
    return geo


def aviso_ancho(ancho):
    if ancho > ANCHO_LEGIBLE:
        return (f"el diagrama mide {ancho:.0f} px de ancho: en una página vertical el texto quedará pequeño. "
                "Parte el proceso en subprocesos o usa una página apaisada")
    return None
