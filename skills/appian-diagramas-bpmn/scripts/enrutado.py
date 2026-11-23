"""Mejora conservadora de las rutas generadas (por capas o con Mermaid).

`mover_pasos` puede mover un paso dentro de su carril si así el trazado global cruza menos. `mejorar`, sin mover
pasos, notas ni carriles: primero vuelve a trazar todos los flujos por
una rejilla que esquiva formas, nombres, etiquetas y los demás flujos; después
prueba corredores flujo a flujo. Un cambio solo se conserva si quita conexiones
ambiguas (un flujo sobre un nombre, una forma o una etiqueta, o dos flujos por la
misma recta) o cruces sin añadir otras. Las rutas importadas y manuales no pasan
por aquí.
"""
from collections import Counter
import itertools
import math
import sys

sys.dont_write_bytecode = True

MAX_INTENTOS = 1200       # trabajo acotado incluso en un proceso muy conectado
MAX_CANDIDATOS = 6000     # también los que se descartan con las guardas baratas
POR_FLUJO = 16            # caminos que se miden de cada flujo en cada vuelta


def _cruza(p, q, caja):
    x, y, w, h = caja
    if p[0] == q[0]:
        return x < p[0] < x + w and min(p[1], q[1]) < y + h and max(p[1], q[1]) > y
    return y < p[1] < y + h and min(p[0], q[0]) < x + w and max(p[0], q[0]) > x


def _punto(camino, sitio):
    largos = [abs(q[0] - p[0]) + abs(q[1] - p[1]) for p, q in zip(camino, camino[1:])]
    falta = (sitio + 1) / 2 * sum(largos)
    for p, q, largo in zip(camino, camino[1:], largos):
        if largo and falta <= largo:
            return tuple(p[e] + (q[e] - p[e]) * falta / largo for e in (0, 1))
        falta -= largo
    return camino[-1]


def _limpiar(camino):
    out = []
    for p in camino:
        p = tuple(p)
        if out and p == out[-1]:
            continue
        if len(out) > 1 and (out[-2][0] == out[-1][0] == p[0] or out[-2][1] == out[-1][1] == p[1]):
            # No quitar un giro de 180 grados: podría cambiar el puerto.
            e = 1 if p[0] == out[-1][0] else 0
            if (out[-1][e] - out[-2][e]) * (p[e] - out[-1][e]) >= 0:
                out.pop()
        out.append(p)
    return out


def _candidatos(camino, cajas, ancho, alto, cabecera):
    """Desvíos de segmentos y corredores entre las cajas, con los mismos puertos."""
    vistos = {tuple(camino)}

    def dar(c):
        c = _limpiar(c)
        if len(c) < 2 or tuple(c) in vistos:
            return None
        vistos.add(tuple(c))
        if any(not cabecera + 6 <= x <= ancho - 6 or not 6 <= y <= alto - 6 for x, y in c):
            return None
        if any(p[0] != q[0] and p[1] != q[1] for p, q in zip(c, c[1:])):
            return None
        # El primer y último tramo deben conservar la dirección del puerto.
        for a, b, u, v in ((camino[0], camino[1], c[0], c[1]),
                            (camino[-1], camino[-2], c[-1], c[-2])):
            if any((b[e] - a[e]) * (v[e] - u[e]) < 0 for e in (0, 1)):
                return None
            if (a[0] == b[0]) != (u[0] == v[0]):
                return None
        return c

    for k, (p, q) in enumerate(zip(camino, camino[1:])):
        horizontal = p[1] == q[1]
        eje = 1 if horizontal else 0
        valores = [p[eje] + d for d in (-12, 12, -24, 24, -40, 40, -64, 64)]
        for x, y, w, h in cajas:
            valores += [y - 12, y + h + 12] if horizontal else [x - 12, x + w + 12]
        for valor in dict.fromkeys(valores):
            a, b = list(p), list(q)
            a[eje] = b[eje] = valor
            if 0 < k < len(camino) - 2:
                # Deslizar el corredor y alargar/acortar sus dos conexiones,
                # sin conservar los codos antiguos como un retroceso de 180°.
                c = dar(camino[:k] + [tuple(a), tuple(b)] + camino[k + 2:])
                if c:
                    yield c
            c = dar(camino[:k + 1] + [tuple(a), tuple(b)] + camino[k + 1:])
            if c:
                yield c
            # Si el segmento toca un puerto, conservar un pequeño tramo recto
            # antes de cambiar de corredor; el desvío no puede cambiar de lado.
            inicio, fin = list(p), list(q)
            a, b = list(a), list(b)
            otro = 1 - eje
            if k == 0:
                inicio[otro] += math.copysign(min(12, abs(q[otro] - p[otro]) / 3), q[otro] - p[otro])
                a[otro] = inicio[otro]
            if k == len(camino) - 2:
                fin[otro] += math.copysign(min(12, abs(q[otro] - p[otro]) / 3), p[otro] - q[otro])
                b[otro] = fin[otro]
            c = dar(camino[:k + 1] + [tuple(inicio), tuple(a), tuple(b), tuple(fin)] + camino[k + 1:])
            if c:
                yield c

    a, b = camino[0], camino[-1]
    # Un tramo propio entre dos puertos horizontales, incluso cuando
    # el camino actual es una sola recta compartida con las otras ramas.
    if a[1] == camino[1][1] and b[1] == camino[-2][1]:
        for salida, llegada in ((12, 12), (24, 24), (40, 40), (12, 64), (12, 96), (24, 64), (24, 96)):
            sx = a[0] + math.copysign(salida, camino[1][0] - a[0])
            tx = b[0] + math.copysign(llegada, camino[-2][0] - b[0])
            ys = [a[1] + d for d in (-24, 24, -40, 40, -64, 64)]
            ys += [v for x, y, w, h in cajas for v in (y - 12, y + h + 12)]
            for y in dict.fromkeys(ys):
                c = dar([a, (sx, a[1]), (sx, y), (tx, y), (tx, b[1]), b])
                if c:
                    yield c


CRUCE = 600               # lo que «cuesta» cruzar otro flujo al buscar un camino: preferible dar un rodeo
CODO = 40                 # cada giro: entre dos caminos igual de largos, el de menos codos
HUECO = 12                # menos entre dos flujos paralelos y se leen como uno pegado al otro
SALIDA = 14               # tramo recto junto a cada puerto antes de girar


def _rutas_libres(camino, cajas, otros, ancho, alto, cabecera, formas=None, codos=(CODO, 3 * CODO)):
    """Caminos ortogonales del origen al destino de `camino` que no pasan por ninguna caja y cruzan los menos flujos
    de `otros` posibles: una búsqueda A* por una rejilla hecha con los bordes de las cajas y de los demás flujos.
    Salen y llegan por el puerto de `camino` o, si se dan las `formas` ((centro, (ancho, alto)) del origen y del
    destino), por el centro de otro lado de la forma, con un pequeño recargo. Uno por cada coste de codo de `codos`."""
    import heapq
    if len(camino) < 2:
        return
    s, e = camino[0], camino[-1]

    def sentido(p, q):
        return (int(math.copysign(1, q[0] - p[0])) if abs(q[0] - p[0]) > 1 else 0,
                int(math.copysign(1, q[1] - p[1])) if abs(q[1] - p[1]) > 1 else 0)

    def junto(c, p, m=SALIDA + 2):
        return c[0] - m <= p[0] <= c[0] + c[2] + m and c[1] - m <= p[1] <= c[1] + c[3] + m

    def puertos(punto, hacia, forma, sale):
        """[(punto en el borde, sentido hacia fuera, recargo)]: el actual y los centros de los otros lados."""
        out = []
        if 0 in hacia and hacia != (0, 0):
            out.append((punto, hacia if sale else (-hacia[0], -hacia[1]), 0))
        if forma:
            (cx, cy), (w, h) = forma
            for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                p = (cx + d[0] * w / 2, cy + d[1] * h / 2)
                if all(abs(p[0] - q[0]) > 1 or abs(p[1] - q[1]) > 1 for q, _, _ in out):
                    out.append((p, d, 2 * CODO))
        return out
    salidas = puertos(s, sentido(s, camino[1]), formas and formas[0], True)
    llegadas = puertos(e, sentido(camino[-2], e), formas and formas[1], False)
    if not salidas or not llegadas:
        return
    # la forma de cada extremo no estorba a sus propios puertos; su etiqueta, sí
    if formas:
        cajas = [c for c in cajas if not any(junto(c, centro, 0) for centro, _ in formas)]
    else:
        cajas = [c for c in cajas if not junto(c, s) and not junto(c, e)]
    xs, ys = set(), set()
    fuera = {}
    for lista, signo in ((salidas, 1), (llegadas, -1)):
        for p, d, _ in lista:
            q = (p[0] + d[0] * SALIDA, p[1] + d[1] * SALIDA)
            fuera[(p, signo)] = q
            xs.add(q[0])
            ys.add(q[1])
    for x, y, w, h in cajas:
        xs.update((x - SALIDA, x + w + SALIDA))
        ys.update((y - SALIDA, y + h + SALIDA))
    for c in otros:
        for x, y in c:
            xs.update((x - SALIDA, x + SALIDA))
            ys.update((y - SALIDA, y + SALIDA))
    xs = sorted(x for x in xs if cabecera + 6 <= x <= ancho - 6)
    ys = sorted(y for y in ys if 6 <= y <= alto - 6)
    for lista in (xs, ys):           # pasillos también por el medio de cada hueco ancho
        lista.extend([(a + b) / 2 for a, b in zip(lista, lista[1:]) if b - a > 3 * SALIDA])
        lista.sort()
    xs, ys = sorted(set(xs)), sorted(set(ys))
    ix, iy = {x: n for n, x in enumerate(xs)}, {y: n for n, y in enumerate(ys)}
    horizontales = [(min(p[0], q[0]), max(p[0], q[0]), p[1]) for c in otros for p, q in zip(c, c[1:]) if abs(p[1] - q[1]) <= 1]
    verticales = [(min(p[1], q[1]), max(p[1], q[1]), p[0]) for c in otros for p, q in zip(c, c[1:]) if abs(p[0] - q[0]) <= 1]

    def tramo(p, q):
        """None si el tramo no se puede usar; si no, cuántos flujos cruza."""
        if any(_cruza(p, q, caja) for caja in cajas):
            return None
        if abs(p[1] - q[1]) <= 1:
            a, b = sorted((p[0], q[0]))
            if any(abs(y - p[1]) <= 2 and min(b, hi) - max(a, lo) > -2 for lo, hi, y in horizontales):
                return None              # por la misma recta que otro: parecería el mismo flujo
            return sum(1 for lo, hi, x in verticales if a < x < b and lo < p[1] < hi)
        a, b = sorted((p[1], q[1]))
        if any(abs(x - p[0]) <= 2 and min(b, hi) - max(a, lo) > -2 for lo, hi, x in verticales):
            return None
        return sum(1 for lo, hi, y in horizontales if a < y < b and lo < p[0] < hi)

    inicios = []
    for p, d, extra in salidas:
        q = fuera[(p, 1)]
        n = tramo(p, q)
        if n is not None and q[0] in ix and q[1] in iy:
            inicios.append(((ix[q[0]], iy[q[1]], d), extra + CRUCE * n, p))
    metas = {}
    for p, d, extra in llegadas:
        q = fuera[(p, -1)]
        n = tramo(q, p)
        if n is not None and q[0] in ix and q[1] in iy:
            entra = (-d[0], -d[1])
            metas.setdefault((ix[q[0]], iy[q[1]]), []).append((entra, extra + CRUCE * n, p))
    if not inicios or not metas:
        return
    ex = sum(xs[i] for i, _ in metas) / len(metas)
    ey = sum(ys[j] for _, j in metas) / len(metas)
    for codo in codos:
        coste, previo, cola = {}, {}, []
        origen = {}
        for nodo, g, p in inicios:
            if g < coste.get(nodo, math.inf):
                coste[nodo] = g
                origen[nodo] = p
                heapq.heappush(cola, (g, g, nodo))
        visitados, final, mejor = 0, None, math.inf
        while cola and visitados < 60000:
            f, g, nodo = heapq.heappop(cola)
            if f >= mejor:
                break
            if g > coste.get(nodo, math.inf):
                continue
            visitados += 1
            i, j, d = nodo
            for entra, extra, p in metas.get((i, j), ()):
                if entra == (-d[0], -d[1]):
                    continue
                total = g + extra + (codo if entra != d else 0)
                if total < mejor:
                    mejor, final = total, (nodo, p)
            q0 = (xs[i], ys[j])
            for nd in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if nd == (-d[0], -d[1]):
                    continue
                ni, nj = i + nd[0], j + nd[1]
                if not (0 <= ni < len(xs) and 0 <= nj < len(ys)):
                    continue
                q = (xs[ni], ys[nj])
                n = tramo(q0, q)
                if n is None:
                    continue
                ng = g + abs(q[0] - q0[0]) + abs(q[1] - q0[1]) + CRUCE * n + (codo if nd != d else 0)
                clave = (ni, nj, nd)
                if ng < coste.get(clave, math.inf):
                    coste[clave] = ng
                    previo[clave] = nodo
                    heapq.heappush(cola, (ng + abs(ex - q[0]) + abs(ey - q[1]), ng, clave))
        if final is None:
            continue
        nodo, llegada = final
        puntos = []
        while True:
            puntos.append((xs[nodo[0]], ys[nodo[1]]))
            if nodo not in previo:
                break
            nodo = previo[nodo]
        yield _limpiar([origen[nodo]] + puntos[::-1] + [llegada])

def ortogonalizar(proc, geo, tam):
    """Los puntos de cada flujo, en ángulo recto. El motor de Mermaid deja a veces un tramo en diagonal (sobre todo
    el último, hacia el centro del destino) y draw.io lo dibuja con codos que nadie ha medido: un flujo así puede
    atravesar una forma o el nombre de un evento sin que la colocación lo vea. Cada diagonal pasa a ser dos tramos:
    el que sale de una forma o llega a ella, por el lado hacia el que va; los de en medio, primero en horizontal."""
    tipo = {p["id"]: p["tipo"] for p in proc["pasos"]}
    for i, f in enumerate(proc["flujos"]):
        if f["de"] not in geo["pasos"] or f["a"] not in geo["pasos"] or f["de"] == f["a"] or i >= len(geo["flujos"]):
            continue
        a, b = tuple(geo["pasos"][f["de"]][:2]), tuple(geo["pasos"][f["a"]][:2])
        (_, ha), (_, hb) = tam[tipo[f["de"]]], tam[tipo[f["a"]]]
        camino = [a] + [tuple(p) for p in geo["flujos"][i]] + [b]
        # casi en línea: a la misma coordenada
        for k in range(1, len(camino) - 1):
            p, q = camino[k - 1], camino[k]
            if abs(q[0] - p[0]) <= 1.5:
                camino[k] = (p[0], q[1])
            elif abs(q[1] - p[1]) <= 1.5:
                camino[k] = (q[0], p[1])
        if len(camino) > 2:
            p, q = camino[-2], camino[-1]
            if abs(q[0] - p[0]) <= 1.5:
                camino[-2] = (q[0], p[1])
            elif abs(q[1] - p[1]) <= 1.5:
                camino[-2] = (p[0], q[1])
        nuevo = [camino[0]]
        for k, q in enumerate(camino[1:], 1):
            p = nuevo[-1]
            if abs(q[0] - p[0]) > 1 and abs(q[1] - p[1]) > 1:
                if k == 1:                                   # sale de la forma de origen
                    codo = (p[0], q[1]) if abs(q[1] - p[1]) > ha / 2 else (q[0], p[1])
                elif k == len(camino) - 1:                   # llega a la forma de destino
                    codo = (q[0], p[1]) if abs(q[1] - p[1]) > hb / 2 else (p[0], q[1])
                else:
                    codo = (q[0], p[1])
                nuevo.append(codo)
            nuevo.append(q)
        geo["flujos"][i] = _limpiar(nuevo)[1:-1]
    return geo


def mejorar(proc, geo, tam, cabecera):
    """Modifica solo si mejora el diagrama; de lo contrario deja `geo` intacta."""
    import drawio_modelo as dm
    import colocacion as co
    # solo lo que ha colocado la herramienta (por capas o con Mermaid): una geometría importada o manual, no
    if not geo.get("etiqueta_en_horizontal") and not geo.get("trazado_generado"):
        return geo
    mermaid = bool(geo.get("trazado_generado"))     # por capas, dos flujos cerca no cuentan: ya va cada uno por su fila
    tipo = {p["id"]: p["tipo"] for p in proc["pasos"]}
    flujos = proc["flujos"]
    indices = [i for i, f in enumerate(flujos) if f["de"] in tipo and f["a"] in tipo and f["de"] != f["a"]]
    if not indices:
        return geo
    cajas_originales = dm._cajas(proc, geo)
    # El XML redondea las cajas respecto de su carril y los vértices a píxeles
    # enteros. Medir ese dibujo evita aceptar un hueco que desaparezca al guardar.
    centros = {}
    formas = {}
    for p in proc["pasos"]:
        cx, cy = geo["pasos"][p["id"]]
        w, h = tam[p["tipo"]]
        ly = geo["carriles"][p["carril"]][0]
        x = round(cx - w / 2)
        y = round(ly) + round(cy - ly - h / 2)
        centros[p["id"]] = (x + w / 2, y + h / 2)
        formas[p["id"]] = (x, y, w, h)
    notas = []
    for n, (x, y, w, h) in zip(proc.get("notas") or [], geo.get("anotaciones") or []):
        carril = next(p["carril"] for p in proc["pasos"] if p["id"] == n["paso"])
        ly = geo["carriles"][carril][0]
        notas.append((round(x), round(ly) + round(y - ly), round(w), round(h)))
    dibujo = dict(geo, pasos=centros, anotaciones=notas)
    cajas = dm._cajas(proc, dibujo)
    cajas_paso = {}
    for p in proc["pasos"]:
        x, y = centros[p["id"]]
        w, h = tam[p["tipo"]]
        cajas_paso[p["id"]] = [(x - w / 2 - 6, y - h / 2 - 6, w + 12, h + 12)]
        lado = geo.get("etiquetas", {}).get(p["id"])
        if lado and p.get("nombre"):
            lh = co.alto_texto(p["nombre"]) - 6
            cajas_paso[p["id"]].append((x - co.ANCHO_ETIQUETA / 2 + 4,
                                        y - h / 2 - lh if lado == "arriba" else y + h / 2,
                                        co.ANCHO_ETIQUETA - 8, lh))
    alto = max(y + h for y, h in geo["carriles"].values())

    def caminos():
        return {i: dm._camino(geo["pasos"][flujos[i]["de"]], tam[tipo[flujos[i]["de"]]], geo["flujos"][i],
                               geo["pasos"][flujos[i]["a"]], tam[tipo[flujos[i]["a"]]]) for i in indices}

    preferidos = {}     # el sitio de cada etiqueta que dejó libre el trazado completo

    def medir(previo=None, cambiados=()):
        rutas_originales = caminos()
        redondeadas = [[(round(x), round(y)) for x, y in pts] for pts in geo["flujos"]]
        rutas = {i: dm._camino(centros[flujos[i]["de"]], tam[tipo[flujos[i]["de"]]], redondeadas[i],
                               centros[flujos[i]["a"]], tam[tipo[flujos[i]["a"]]]) for i in indices}
        cambiados = set(cambiados) if previo else set(indices)
        if previo:
            # Una ruta nueva puede ocupar el sitio de una etiqueta cuya ruta
            # sigue igual. Recolocar también esa etiqueta antes de descartar el
            # corredor, conservando las restantes reservas como obstáculos.
            tocados = set()
            for i, sitio in previo[3].items():
                if i in cambiados:
                    continue
                x, y = _punto(rutas[i], sitio)
                w = co.ancho_etiqueta_flujo(flujos[i]["etiqueta"]) + 2 * co.AIRE_ETIQUETA
                box = (x - w / 2, y - 7 - co.AIRE_ETIQUETA, w, 14 + 2 * co.AIRE_ETIQUETA)
                if any(_cruza(p, q, box) for j in cambiados for p, q in zip(rutas[j], rutas[j][1:])):
                    tocados.add(i)
            cambiados.update(tocados)

        def afecta(clave):
            if clave[0] in ("etiqueta", "juntos", "reserva", "etiquetas", "cerca"):
                return clave[1] in cambiados or clave[2] in cambiados
            return clave[1] in cambiados

        avisos = Counter({k: v for k, v in previo[0].items() if not afecta(k)}) if previo else Counter()
        ajenas = {p for p in previo[1] if not cambiados.intersection(p)} if previo else set()
        guardas = {k for k in previo[5] if not afecta(k)} if previo else set()
        sitios, etiquetas, reservas = {}, {}, {}
        for i, c in rutas_originales.items():
            f = flujos[i]
            if f.get("etiqueta"):
                sitio = previo[3].get(i) if previo else geo.get("etiquetas_flujo", {}).get(i)
                if (sitio is None or i in cambiados) and not previo and i in preferidos:
                    sitio = preferidos[i]
                elif sitio is None or i in cambiados:
                    sitio = dm._sitio_etiqueta(c, [v for j, v in rutas_originales.items() if i != j],
                                               (co.ancho_etiqueta_flujo(f["etiqueta"]), cajas_originales))
                sitio = float(f"{sitio:.3f}") if sitio is not None else 0.0
                sitios[i] = sitio
                x, y = _punto(rutas[i], sitio)
                w = len(f["etiqueta"]) * 6 + 4
                etiquetas[i] = (x - w / 2, y - 7, w, 14)
                w = co.ancho_etiqueta_flujo(f["etiqueta"])
                reservas[i] = (x - w / 2 - co.AIRE_ETIQUETA, y - 7 - co.AIRE_ETIQUETA,
                               w + 2 * co.AIRE_ETIQUETA, 14 + 2 * co.AIRE_ETIQUETA)
                if i in cambiados:
                    mitad_x, mitad_y = w / 2 + co.AIRE_ETIQUETA, 7 + co.AIRE_ETIQUETA
                    cabe = any((abs(p[1] - q[1]) <= 1 and abs(y - p[1]) <= 1 and
                                min(p[0], q[0]) + mitad_x <= x <= max(p[0], q[0]) - mitad_x) or
                               (abs(p[0] - q[0]) <= 1 and abs(x - p[0]) <= 1 and
                                min(p[1], q[1]) + mitad_y <= y <= max(p[1], q[1]) - mitad_y)
                               for p, q in zip(rutas[i], rutas[i][1:]))
                    if not cabe:
                        guardas.add(("etiqueta-corta", i))
                largo = sum(abs(q[0] - p[0]) + abs(q[1] - p[1]) for p, q in zip(rutas[i], rutas[i][1:]))
                centro = (sitio + 1) / 2 * largo
                mitad = (len(f["etiqueta"]) * 6 + 4) / 2
                if i in cambiados and (largo - centro - mitad < 8 or f.get("defecto") and centro - mitad < 14):
                    guardas.add(("extremo", i))
        for i, c in rutas.items():
            f = flujos[i]
            segmentos = list(zip(c, c[1:]))
            for k, (p, q) in enumerate(segmentos if i in cambiados else []):
                for r, s in segmentos[k + 2:]:
                    for h, h2, v, v2 in ((p, q, r, s), (r, s, p, q)):
                        if h[1] == h2[1] and v[0] == v2[0] and min(h[0], h2[0]) < v[0] < max(h[0], h2[0]) \
                                and min(v[1], v2[1]) < h[1] < max(v[1], v2[1]):
                            guardas.add(("autocruce", i))
            for pid in ((f["de"], f["a"]) if i in cambiados else []):
                if any(_cruza(p, q, formas[pid]) for p, q in segmentos):
                    guardas.add(("propio", i, pid))
            for pid, cs in (cajas_paso.items() if i in cambiados else []):
                if pid not in (f["de"], f["a"]) and any(_cruza(p, q, box) for p, q in segmentos for box in cs):
                    avisos[("paso", i, pid)] = 1
                elif pid in (f["de"], f["a"]) and any(_cruza(p, q, box) for p, q in segmentos for box in cs[1:]):
                    avisos[("su-etiqueta", i, pid)] = 1     # pasa por encima del nombre de su propio evento o puerta
            for j, box in etiquetas.items():
                if i not in cambiados and j not in cambiados:
                    continue
                if i != j and any(_cruza(p, q, box) for p, q in segmentos):
                    avisos[("etiqueta", i, j)] = 1
                if i != j and tipo[flujos[j]["de"]] in dm.PUERTAS:
                    x, y = box[0] + box[2] / 2, box[1] + box[3] / 2
                    if any(min(p[0], q[0]) - 1 <= x <= max(p[0], q[0]) + 1 and
                           min(p[1], q[1]) - 1 <= y <= max(p[1], q[1]) + 1 for p, q in segmentos):
                        ajenas.add((i, j))
            for j, d in rutas.items():
                if i >= j or i not in cambiados and j not in cambiados or \
                        f["de"] == flujos[j]["de"] or f["a"] == flujos[j]["a"]:
                    continue
                longitudes = set()
                for p, q in segmentos:
                    for r, s in zip(d, d[1:]):
                        for eje in (0, 1):
                            if abs(p[eje] - q[eje]) <= 1 and abs(r[eje] - s[eje]) <= 1 and abs(p[eje] - r[eje]) <= 1:
                                o = 1 - eje
                                largo = min(max(p[o], q[o]), max(r[o], s[o])) - max(min(p[o], q[o]), min(r[o], s[o]))
                                if largo > 1:
                                    longitudes.add(round(largo))
                if longitudes:
                    avisos[("juntos", i, j)] = len(longitudes)
            for j, d in rutas.items():
                if mermaid and i < j and (i in cambiados or j in cambiados) and _pegados(c, d):
                    avisos[("cerca", i, j)] = 1
            # Las notas también son obstáculos, aunque el detector histórico no
            # las contaba entre las conexiones falsas.
            for n, box in enumerate(notas if i in cambiados else []):
                if any(_cruza(p, q, box) for p, q in segmentos):
                    avisos[("nota", i, n)] = 1
            for j, box in reservas.items():
                if i != j and (i in cambiados or j in cambiados) and any(_cruza(p, q, box) for p, q in segmentos):
                    guardas.add(("reserva", i, j))
        for i, box in reservas.items():
            for n, otra in enumerate(cajas if i in cambiados else []):
                if box[0] < otra[0] + otra[2] and box[0] + box[2] > otra[0] and \
                        box[1] < otra[1] + otra[3] and box[1] + box[3] > otra[1]:
                    guardas.add(("etiqueta-caja", i, n))
            for j, otra in reservas.items():
                if i < j and (i in cambiados or j in cambiados) and box[0] < otra[0] + otra[2] and box[0] + box[2] > otra[0] and \
                        box[1] < otra[1] + otra[3] and box[1] + box[3] > otra[1]:
                    guardas.add(("etiquetas", i, j))
        cruces = []
        for num, (posiciones, puntos) in enumerate(((geo["pasos"], geo["flujos"]), (centros, redondeadas))):
            pares = {p: n for p, n in previo[7 + num].items() if not cambiados.intersection(p)} if previo else {}
            for i in indices:
                c = [posiciones[flujos[i]["de"]]] + list(puntos[i]) + [posiciones[flujos[i]["a"]]]
                for j in indices:
                    if i >= j or not cambiados.intersection((i, j)):
                        continue
                    d = [posiciones[flujos[j]["de"]]] + list(puntos[j]) + [posiciones[flujos[j]["a"]]]
                    cuenta = 0
                    for p, q in zip(c, c[1:]):
                        for r, s in zip(d, d[1:]):
                            for h, h2, v, v2 in ((p, q, r, s), (r, s, p, q)):
                                if abs(h[1] - h2[1]) <= 1 and abs(v[0] - v2[0]) <= 1 and \
                                        min(h[0], h2[0]) + 1 < v[0] < max(h[0], h2[0]) - 1 and \
                                        min(v[1], v2[1]) + 1 < h[1] < max(v[1], v2[1]) - 1:
                                    cuenta += 1
                    if cuenta:
                        pares[(i, j)] = cuenta
            cruces.append(pares)
        return (avisos, ajenas, sum(cruces[0].values()), sitios, rutas_originales, guardas,
                sum(cruces[1].values()), cruces[0], cruces[1])

    actual = medir()
    if not actual[0] and not actual[2]:
        return geo
    originales = [list(p) for p in geo["flujos"]]
    base = inicial = actual
    # Una evaluación crece con los pares de flujos. Reducir su número en los
    # procesos densos mantiene acotada esta mejora opcional.
    limite = min(MAX_INTENTOS, max(300, MAX_INTENTOS * 20 * 20 // len(indices) ** 2))
    # Primero, todos los flujos de nuevo por la rejilla; se queda si deja el dibujo más claro. El nombre de cada
    # carril, arriba a la izquierda, tampoco se pisa.
    titulos = [(0, y, 24 + 7.5 * len(c), 26) for c, (y, _) in geo["carriles"].items()]
    nuevas = limite and trazar_todo(proc, dict(geo, pasos=centros), tam, cabecera, alto,
                         list(dict.fromkeys(cajas + [b for cs in cajas_paso.values() for b in cs] + titulos)), indices)
    if nuevas:
        nuevas, preferidos = nuevas
        for i, pts in nuevas.items():
            geo["flujos"][i] = pts
        prueba = medir()
        # ni más conexiones ambiguas ni más cruces, y menos de alguno
        if sum(prueba[0].values()) <= sum(actual[0].values()) and prueba[2] <= actual[2] and prueba[5] <= base[5] \
                and (sum(prueba[0].values()), prueba[2]) < (sum(actual[0].values()), actual[2]):
            actual = base = prueba
        else:
            geo["flujos"] = [list(p) for p in originales]
            preferidos = {}
    intentos = revisados = 0

    def aceptar(prueba):
        return (all(n <= actual[0][a] for a, n in prueba[0].items())
                and prueba[1] <= base[1] and prueba[2] <= base[2]
                and prueba[5] <= base[5] and prueba[6] <= base[6]
                and (sum(prueba[0].values()) < sum(actual[0].values())
                     or sum(prueba[0].values()) == sum(actual[0].values()) and prueba[2] < actual[2]))

    # Un origen puede compartir su tronco. Mover las ramas conjuntamente evita
    # sustituir una coincidencia entre puertas distintas por varios cruces.
    grupos = {}
    for i in indices:
        grupos.setdefault(flujos[i]["de"], []).append(i)

    for _ in range(3):
        cambio = False
        for origen, grupo in grupos.items():
            if len(grupo) < 2:
                continue
            rutas = {i: actual[4][i] for i in grupo}
            if any(c[-1][0] <= c[0][0] + 36 or c[-1][1] != c[-2][1] for c in rutas.values()):
                continue
            izquierda = max(c[0][0] for c in rutas.values()) + 12
            derecha = min(c[-1][0] for c in rutas.values()) - 12
            xs = [izquierda + (derecha - izquierda) * n / 4 for n in (1, 2, 3)]
            xs += [x + d for c in rutas.values() for x, y in c[1:-1] for d in (-12, 12, -24, 24)]
            antes = {i: geo["flujos"][i] for i in grupo}
            mejor, mejores = actual, None
            for x in sorted(set(round(x) for x in xs if izquierda <= x <= derecha)):
                if intentos >= limite or revisados >= MAX_CANDIDATOS:
                    break
                revisados += 1
                for i, c in rutas.items():
                    a, b = c[0], c[-1]
                    inicio = [a]
                    if a[0] == c[1][0]:
                        y = a[1] + math.copysign(12, c[1][1] - a[1])
                        inicio += [(a[0], y), (x, y)]
                    else:
                        inicio += [(x, a[1])]
                    geo["flujos"][i] = _limpiar(inicio + [(x, b[1]), b])[1:-1]
                candidatas = caminos()
                if any(not cabecera + 6 <= px <= geo["ancho"] - 6 or not 6 <= py <= alto - 6
                       for i in grupo for px, py in candidatas[i]) or \
                        any(_cruza(p, q, box) for i in grupo
                            for p, q in zip(candidatas[i], candidatas[i][1:]) for box in cajas):
                    continue
                intentos += 1
                prueba = medir(actual, grupo)
                if aceptar(prueba) and (sum(prueba[0].values()), prueba[2]) < (sum(mejor[0].values()), mejor[2]):
                    mejor = prueba
                    mejores = {i: geo["flujos"][i] for i in grupo}
            for i in grupo:
                geo["flujos"][i] = mejores[i] if mejores else antes[i]
            if mejores:
                actual = mejor
                cambio = True
        implicados = {i for aviso in actual[0] for i in aviso[1:] if isinstance(i, int)}
        cruzados = Counter()
        for par, cuenta in actual[7].items():
            for i in par:
                cruzados[i] += cuenta
        relevantes = [i for i in indices if i in implicados or i in cruzados]
        for i in sorted(relevantes, key=lambda j: (j not in implicados, -cruzados[j], not flujos[j].get("etiqueta"), j)):
            if not actual[0] and not actual[2]:
                break
            if i not in actual[4]:
                continue
            antes = geo["flujos"][i]
            elegido = False
            otros = [c for j, c in actual[4].items() if j != i]
            # sus propias formas no cuentan: el camino empieza y acaba en su borde (las guardas ya vigilan que no
            # las atraviese), y el redondeo de las cajas dejaría el puerto dentro
            propias = [geo["pasos"][flujos[i][k]][:2] for k in ("de", "a")]
            ajenas_i = [b for b in cajas if not any(b[0] <= cx <= b[0] + b[2] and b[1] <= cy <= b[1] + b[3]
                                                    for cx, cy in propias)]
            libres = _rutas_libres(actual[4][i], cajas + [b for pid, cs in cajas_paso.items()
                                                           if pid not in (flujos[i]["de"], flujos[i]["a"]) for b in cs],
                                   otros, geo["ancho"], alto, cabecera,
                                   ((geo["pasos"][flujos[i]["de"]][:2], tam[tipo[flujos[i]["de"]]]),
                                    (geo["pasos"][flujos[i]["a"]][:2], tam[tipo[flujos[i]["a"]]])))
            suyos = 0          # cada flujo, con su parte del trabajo: así llegan a probarse todos
            for candidato in itertools.chain(libres, _candidatos(actual[4][i], cajas, geo["ancho"], alto, cabecera)):
                if intentos >= limite or revisados >= MAX_CANDIDATOS or suyos >= POR_FLUJO:
                    break
                revisados += 1
                if any(_cruza(p, q, box) for p, q in zip(candidato, candidato[1:]) for box in ajenas_i):
                    continue
                if any(_cruza(p, q, box) for p, q in zip(candidato, candidato[1:])
                       for pid, cs in cajas_paso.items() if pid not in (flujos[i]["de"], flujos[i]["a"]) for box in cs):
                    continue
                geo["flujos"][i] = candidato[1:-1]
                intentos += 1
                suyos += 1
                prueba = medir(actual, (i,))
                if aceptar(prueba):
                    actual = prueba
                    elegido = True
                    cambio = True
                    break
            if not elegido:
                geo["flujos"][i] = antes
        if not cambio or not actual[0] and not actual[2] or intentos >= limite or revisados >= MAX_CANDIDATOS:
            break
    if sum(actual[0].values()) <= sum(inicial[0].values()) and actual[2] <= inicial[2] and \
            (sum(actual[0].values()), actual[2]) < (sum(inicial[0].values()), inicial[2]):
        geo["etiquetas_flujo"] = actual[3]
    else:
        geo["flujos"] = originales
    return geo


def _sentido(p, q):
    return (0 if abs(q[0] - p[0]) <= 1 else (1 if q[0] > p[0] else -1),
            0 if abs(q[1] - p[1]) <= 1 else (1 if q[1] > p[1] else -1))


def _a_rejilla(camino, xs, ys, cerca):
    """Los nodos de la rejilla por los que pasa un camino ortogonal ya trazado, o None si no va por ella."""
    if len(camino) < 2:
        return None
    d0, d1 = _sentido(camino[0], camino[1]), _sentido(camino[-2], camino[-1])
    if 0 not in d0 or 0 not in d1 or d0 == (0, 0) or d1 == (0, 0):
        return None
    clave = [(camino[0][0] + d0[0] * SALIDA, camino[0][1] + d0[1] * SALIDA)] + [tuple(p) for p in camino[1:-1]] + \
        [(camino[-1][0] - d1[0] * SALIDA, camino[-1][1] - d1[1] * SALIDA)]
    puntos = []
    for x, y in clave:
        i, j = cerca(xs, x), cerca(ys, y)
        if i is None or j is None:
            return None
        puntos.append((i, j))
    nodos = [puntos[0]]
    for a, b in zip(puntos, puntos[1:]):
        if a == b:
            continue
        if a[0] != b[0] and a[1] != b[1]:
            return None
        paso = (0 if a[0] == b[0] else (1 if b[0] > a[0] else -1), 0 if a[1] == b[1] else (1 if b[1] > a[1] else -1))
        n = a
        while n != b:
            n = (n[0] + paso[0], n[1] + paso[1])
            nodos.append(n)
    return nodos


def trazar_todo(proc, geo, tam, cabecera, alto, cajas, indices, orden=None, fijas=None, repasar=True, visitas=80000, hueco=4):
    """Vuelve a trazar desde cero los flujos de `indices` por una rejilla, uno tras otro: cada uno, por el camino más
    corto que no atraviesa ninguna caja de `cajas` (formas, sus nombres y notas), no va por la misma recta que otro
    flujo ni gira donde pasa otro, y cruza los menos flujos posibles. Sale y llega por el lado que convenga de cada
    forma, sin mezclar en un mismo lado flujos que entran con flujos que salen, y deja sitio a cada etiqueta en un
    tramo recto. Devuelve ({índice: puntos interiores}, {índice: sitio de su etiqueta, de -1 a 1}) o None si alguno
    no tiene camino."""
    import heapq
    flujos = proc["flujos"]
    tipo = {p["id"]: p["tipo"] for p in proc["pasos"]}
    lados = ((1, 0), (-1, 0), (0, 1), (0, -1))

    def forma(pid):
        (cx, cy), (w, h) = geo["pasos"][pid][:2], tam[tipo[pid]]
        return cx, cy, w, h

    def puerto(pid, d):
        cx, cy, w, h = forma(pid)
        p = (cx + d[0] * w / 2, cy + d[1] * h / 2)
        return p, (p[0] + d[0] * SALIDA, p[1] + d[1] * SALIDA)

    def propia(caja, pid):
        cx, cy, w, h = forma(pid)
        x, y, bw, bh = caja
        return x <= cx <= x + bw and y <= cy <= y + bh

    lo_x, hi_x, lo_y, hi_y = cabecera + 6, geo["ancho"] - 6, 6, alto - 6
    xs, ys = set(), set()
    for x, y, w, h in cajas:
        xs.update((x - SALIDA, x + w + SALIDA))
        ys.update((y - SALIDA, y + h + SALIDA))
    puertos_x, puertos_y = set(), set()
    for p in proc["pasos"]:
        for d in lados:
            _, q = puerto(p["id"], d)
            puertos_x.add(q[0])
            puertos_y.add(q[1])
    xs |= puertos_x
    ys |= puertos_y

    def rejilla(valores, lo, hi, puertos):
        import bisect
        v = sorted(x for x in valores if lo <= x <= hi)
        out = []
        for a, b in zip(v, v[1:]):
            out.append(a)
            n = int((b - a) // (2 * SALIDA))      # pasillos también por el medio de cada hueco ancho
            out.extend(a + (b - a) * k / n for k in range(1, n))
        out.extend(v[-1:])
        # dos rectas a menos de 4 px se ven como una, y a menos de `hueco` (con Mermaid, HUECO), como dos flechas
        # pegadas: de cada grupo así queda una, y siempre la de un puerto, por donde entra o sale un flujo
        limpio = sorted({x for x in out if x in puertos}) if hueco > 4 else []
        for x in sorted(out):
            k = bisect.bisect_left(limpio, x)
            if all(abs(limpio[j] - x) >= hueco for j in (k - 1, k) if 0 <= j < len(limpio)):
                limpio.insert(k, x)
        final = []
        for x in limpio:
            if not final or x - final[-1] >= 4:
                final.append(x)
        return final
    xs, ys = rejilla(xs, lo_x, hi_x, puertos_x), rejilla(ys, lo_y, hi_y, puertos_y)

    def cerca(valores, v):
        import bisect
        k = bisect.bisect_left(valores, v)
        mejor = min((abs(valores[j] - v), j) for j in (k - 1, k) if 0 <= j < len(valores))
        return mejor[1] if mejor[0] < 4 else None

    # tramos de la rejilla que atraviesan una caja (las formas de los extremos se descartan al buscar cada flujo)
    def bloqueos(lista):
        bloq_h, bloq_v = set(), set()
        for caja in lista:
            x, y, w, h = caja
            for j, yy in enumerate(ys):
                if y < yy < y + h:
                    for i in range(len(xs) - 1):
                        if xs[i] < x + w and xs[i + 1] > x:
                            bloq_h.add((i, j))
            for i, xx in enumerate(xs):
                if x < xx < x + w:
                    for j in range(len(ys) - 1):
                        if ys[j] < y + h and ys[j + 1] > y:
                            bloq_v.add((i, j))
        return bloq_h, bloq_v
    bloq_comun = bloqueos(cajas)
    reservas = {}      # flujo -> tramos que tapa su etiqueta (los demás no pueden pasar)
    centros_etiqueta = {}
    cajas_etiqueta = {}
    sin_sitio = set()   # flujos con etiqueta que no han encontrado un tramo libre para ella

    ocupa = {}          # nodo -> [(flujo, "H" | "V" | "B")]
    tramo_h, tramo_v = {}, {}   # tramo de la rejilla -> {flujos}
    usos = {}           # (paso, lado) -> {"sale" | "entra": {flujos}}
    rutas = {}

    def amigos(i, j):
        # los que llegan al mismo paso pueden unirse antes y los que salen del mismo, compartir el tronco; pero
        # este se cobra (`tronco`), para que se separen pronto y cada uno tenga sitio para su etiqueta
        return flujos[i]["a"] == flujos[j]["a"] or flujos[i]["de"] == flujos[j]["de"]

    def tronco(i, usan):
        return any(flujos[i]["de"] == flujos[o]["de"] and flujos[i]["a"] != flujos[o]["a"] for o in usan)

    def quitar(i):
        for k in list(ocupa):
            ocupa[k] = [o for o in ocupa[k] if o[0] != i]
        for t in (tramo_h, tramo_v):
            for k in t:
                t[k].discard(i)
        for k in usos:
            for v in usos[k].values():
                v.discard(i)
        rutas.pop(i, None)
        reservas.pop(i, None)
        centros_etiqueta.pop(i, None)
        cajas_etiqueta.pop(i, None)

    def reservar(i, nodos):
        """Guarda sitio para la etiqueta de `i` en el centro de su tramo recto más largo que no comparte."""
        import colocacion as co
        texto = flujos[i].get("etiqueta")
        if not texto or len(nodos) < 2:
            return
        w = co.ancho_etiqueta_flujo(texto) + 2 * co.AIRE_ETIQUETA
        h = 14 + 2 * co.AIRE_ETIQUETA
        tramos, k = [], 0
        while k < len(nodos) - 1:
            m = k
            horizontal = nodos[k][1] == nodos[k + 1][1]
            while m < len(nodos) - 1 and (nodos[m][1] == nodos[m + 1][1]) == horizontal:
                m += 1
            a, b = nodos[k], nodos[m]
            solo = all(len((tramo_h.get((min(p[0], q[0]), p[1])) if horizontal else
                            tramo_v.get((p[0], min(p[1], q[1])))) or ()) <= 1 for p, q in zip(nodos[k:m], nodos[k + 1:m + 1]))
            largo = abs(xs[b[0]] - xs[a[0]]) + abs(ys[b[1]] - ys[a[1]])
            tramos.append((solo, largo, horizontal, a, b))
            k = m
        ajenos = [[(xs[n[0]], ys[n[1]]) for n in r[1]] for j, r in rutas.items() if j != i]
        ocupadas = [c for j, c in cajas_etiqueta.items() if j != i]

        def libre(caja):
            x, y, bw, bh = caja
            solapa = lambda o: x < o[0] + o[2] and x + bw > o[0] and y < o[1] + o[3] and y + bh > o[1]   # noqa: E731
            # lejos también del tramo recto con que otro flujo llega a una forma
            return not any(solapa((o[0] - SALIDA, o[1] - SALIDA, o[2] + 2 * SALIDA, o[3] + 2 * SALIDA)) for o in cajas) \
                and not any(solapa(o) for o in ocupadas) and \
                not any(_cruza(p, q, (x - 3, y - 3, bw + 6, bh + 6)) for c in ajenos for p, q in zip(c, c[1:]))
        elegido = None
        for solo, largo, horizontal, a, b in sorted(tramos, key=lambda t: (not t[0], -t[1], not t[2])):
            p, q = (xs[a[0]], ys[a[1]]), (xs[b[0]], ys[b[1]])
            mitad = (w if horizontal else h) / 2 + 4
            if largo < 2 * mitad:
                continue
            centro = largo / 2
            # del centro del tramo hacia sus extremos, el primer sitio libre
            for d in sorted(range(0, int(largo / 2 - mitad) + 1, 6), key=abs):
                for t in ({centro + d, centro - d}):
                    x = p[0] + (q[0] - p[0]) * t / largo
                    y = p[1] + (q[1] - p[1]) * t / largo
                    if libre((x - w / 2, y - h / 2, w, h)):
                        elegido = (x, y)
                        break
                if elegido:
                    break
            if elegido:
                break
        if not elegido:
            solo, largo, horizontal, a, b = max(tramos, key=lambda t: (t[0], t[1], t[2]))
            elegido = ((xs[a[0]] + xs[b[0]]) / 2, (ys[a[1]] + ys[b[1]]) / 2)
            sin_sitio.add(i)
        else:
            sin_sitio.discard(i)
        x, y = elegido
        cajas_etiqueta[i] = (x - w / 2, y - h / 2, w, h)
        reservas[i] = bloqueos([(x - w / 2 - 3, y - h / 2 - 3, w + 6, h + 6)])    # con holgura para el redondeo
        centros_etiqueta[i] = (x, y)

    def poner(i, nodos, ls, la):
        for k, (a, b) in enumerate(zip(nodos, nodos[1:])):
            if a[1] == b[1]:
                tramo_h.setdefault((min(a[0], b[0]), a[1]), set()).add(i)
            else:
                tramo_v.setdefault((a[0], min(a[1], b[1])), set()).add(i)
        for k, n in enumerate(nodos):
            if 0 < k < len(nodos) - 1:
                a, b = nodos[k - 1], nodos[k + 1]
                clase = "B" if (a[0] == n[0]) != (b[0] == n[0]) else ("H" if a[1] == n[1] else "V")
            else:
                clase = "B"
            ocupa.setdefault(n, []).append((i, clase))
        usos.setdefault((flujos[i]["de"], ls), {}).setdefault("sale", set()).add(i)
        usos.setdefault((flujos[i]["a"], la), {}).setdefault("entra", set()).add(i)
        reservar(i, nodos)

    def coste_lado(d, sale):
        natural = (1, 0) if sale else (-1, 0)
        if d == natural:
            return 0
        return 3 * CODO if d == (-natural[0], -natural[1]) else CODO

    def buscar(i):
        f = flujos[i]
        de, a = f["de"], f["a"]
        bloq_h, bloq_v = set(bloq_comun[0]), set(bloq_comun[1])
        for j, (rh, rv) in reservas.items():
            if j != i:
                bloq_h |= rh
                bloq_v |= rv
        # su propia forma no estorba al tramo recto que sale de su borde; su nombre, sí
        otras = [c for c in cajas if not (propia(c, de) or propia(c, a))]

        def extremos(pid, sale, mezclar=False):
            out = []
            for d in lados:
                uso = usos.get((pid, d), {})
                if uso.get("entra" if sale else "sale") and not mezclar:
                    continue
                p, q = puerto(pid, d)
                if any(_cruza(p, q, c) for c in otras):
                    continue
                ni, nj = cerca(xs, q[0]), cerca(ys, q[1])
                if ni is None or nj is None:
                    continue
                out.append(((ni, nj), d, coste_lado(d, sale) + (CRUCE if mezclar else 0), p))
            # con todos los lados ocupados en el otro sentido, compartir uno es mejor que no trazarlo
            return out or (extremos(pid, sale, True) if not mezclar else [])
        salidas, llegadas = extremos(de, True), extremos(a, False)
        if not salidas or not llegadas:
            return None
        metas = {}
        for n, d, c, p in llegadas:
            metas.setdefault(n, []).append(((-d[0], -d[1]), c, p, d))

        def ajenos(n):
            return [o for o in ocupa.get(n, ()) if not amigos(i, o[0])]
        cola, coste, previo = [], {}, {}
        for n, d, c, p in salidas:
            if any(o[1] == "B" for o in ajenos(n)):
                continue
            clave = (n[0], n[1], d)
            if c < coste.get(clave, math.inf):
                coste[clave] = c
                previo[clave] = ("inicio", p, d)
                heapq.heappush(cola, (c, c, clave))
        ex = [xs[n[0]] for n in metas]
        ey = [ys[n[1]] for n in metas]
        mejor, final, visitados = math.inf, None, 0
        while cola and visitados < visitas:
            fc, g, clave = heapq.heappop(cola)
            if fc >= mejor:
                break
            if g > coste.get(clave, math.inf):
                continue
            visitados += 1
            ci, cj, d = clave
            for entra, c, p, lado in metas.get((ci, cj), ()):
                if entra == (-d[0], -d[1]):
                    continue
                gira = entra != d
                if gira and ajenos((ci, cj)):
                    continue
                total = g + c + (CODO if gira else 0)
                if total < mejor:
                    mejor, final = total, (clave, p, lado)
            for nd in lados:
                if nd == (-d[0], -d[1]):
                    continue
                gira = nd != d
                if gira and ajenos((ci, cj)):
                    continue
                ni, nj = ci + nd[0], cj + nd[1]
                if not (0 <= ni < len(xs) and 0 <= nj < len(ys)):
                    continue
                if nd[1] == 0:
                    t = (min(ci, ni), cj)
                    usan = tramo_h.get(t, ())
                    if t in bloq_h or any(not amigos(i, o) for o in usan):
                        continue
                else:
                    t = (ci, min(cj, nj))
                    usan = tramo_v.get(t, ())
                    if t in bloq_v or any(not amigos(i, o) for o in usan):
                        continue
                largo = abs(xs[ni] - xs[ci]) + abs(ys[nj] - ys[cj])
                otros = ajenos((ni, nj))
                if any(o[1] == "B" for o in otros):
                    continue
                # también cuenta cruzar a un hermano: dos salidas de la misma puerta que se cruzan confunden igual
                cruces = sum(1 for o in ocupa.get((ni, nj), ()) if o[0] != i and o[1] == ("V" if nd[1] == 0 else "H"))
                if any(o[1] == ("H" if nd[1] == 0 else "V") for o in otros):
                    continue
                ng = g + largo * (4 if tronco(i, usan) else 1) + CRUCE * cruces + (CODO if gira else 0)
                nc = (ni, nj, nd)
                if ng < coste.get(nc, math.inf):
                    coste[nc] = ng
                    previo[nc] = clave
                    h = min(abs(x - xs[ni]) + abs(y - ys[nj]) for x, y in zip(ex, ey))
                    heapq.heappush(cola, (ng + h, ng, nc))
        if final is None:
            return None
        clave, fin, lado_a = final
        nodos = []
        while True:
            nodos.append((clave[0], clave[1]))
            antes = previo[clave]
            if antes[0] == "inicio":
                inicio, lado_s = antes[1], antes[2]
                break
            clave = antes
        nodos.reverse()
        return mejor, nodos, inicio, fin, lado_s, lado_a

    if orden is None:
        # primero los que llevan etiqueta, que necesitan un tramo recto para ella; y los cortos antes que los largos
        orden = sorted(indices, key=lambda i: (not flujos[i].get("etiqueta"), abs(geo["pasos"][flujos[i]["de"]][0] - geo["pasos"][flujos[i]["a"]][0])
                                             + abs(geo["pasos"][flujos[i]["de"]][1] - geo["pasos"][flujos[i]["a"]][1]), i))
    else:
        orden = list(orden)

    def cruces_de(i):
        return sum(1 for n in rutas[i][1] for o in ocupa.get(n, ()) if o[0] != i and
                   {o[1], next(c for j, c in ocupa[n] if j == i)} == {"H", "V"})

    # los de `fijas` ({flujo: camino de borde a borde}) se quedan como estaban, si caben en esta rejilla
    for i, camino in (fijas or {}).items():
        nodos = _a_rejilla(camino, xs, ys, cerca)
        if nodos is None:
            orden.append(i)
            continue
        ls = _sentido(camino[0], camino[1])
        fin = _sentido(camino[-2], camino[-1])
        la = (-fin[0], -fin[1])
        rutas[i] = (0, nodos, ls, la, tuple(camino[0]), tuple(camino[-1]))
        poner(i, nodos, ls, la)
    for i in orden:
        r = buscar(i)
        if r is None:
            return None
        rutas[i] = (r[0], r[1], r[4], r[5], r[2], r[3])
        poner(i, r[1], r[4], r[5])
    # después, cada flujo que cruza otro o no tiene sitio para su etiqueta, otra vez con todos los demás ya puestos:
    # el cambio se queda si baja el total de cruces
    for _ in range(3 if repasar else 0):
        cambio = False
        for i in orden:
            antes = cruces_de(i)
            if not antes and i not in sin_sitio:
                continue
            total = sum(cruces_de(j) for j in rutas) // 2
            previa, faltaba = rutas[i], i in sin_sitio
            quitar(i)
            r = buscar(i)
            if r is not None:
                rutas[i] = (r[0], r[1], r[4], r[5], r[2], r[3])
                poner(i, r[1], r[4], r[5])
                nuevo = sum(cruces_de(j) for j in rutas) // 2
                if (nuevo, i in sin_sitio) < (total, faltaba):
                    cambio = True
                    continue
                quitar(i)
            rutas[i] = previa
            poner(i, previa[1], previa[2], previa[3])
        if not cambio:
            break
    out, sitios = {}, {}
    for i, (_, nodos, ls, la, inicio, fin) in rutas.items():
        puntos = _limpiar([inicio] + [(xs[a], ys[b]) for a, b in nodos] + [fin])
        out[i] = puntos[1:-1]
        if i in centros_etiqueta:
            x, y = centros_etiqueta[i]
            hecho = 0
            largos = [abs(q[0] - p[0]) + abs(q[1] - p[1]) for p, q in zip(puntos, puntos[1:])]
            for p, q, largo in zip(puntos, puntos[1:], largos):
                if min(p[0], q[0]) - 1 <= x <= max(p[0], q[0]) + 1 and min(p[1], q[1]) - 1 <= y <= max(p[1], q[1]) + 1:
                    sitios[i] = 2 * (hecho + abs(x - p[0]) + abs(y - p[1])) / sum(largos) - 1
                    break
                hecho += largo
    return out, sitios


VISITAS_PRUEBA = 12000     # al probar dónde mover un paso, un camino que cueste más se da por perdido
TIEMPO_MOVER = 40         # segundos, como mucho, buscando dónde mover un paso para quitar cruces


def _obstaculos(proc, geo, tam):
    """Lo que el trazado global esquiva, medido como queda en el XML: (centros redondeados, cajas, alto)."""
    import drawio_modelo as dm
    import colocacion as co
    centros = {}
    for p in proc["pasos"]:
        cx, cy = geo["pasos"][p["id"]][:2]
        w, h = tam[p["tipo"]]
        ly = geo["carriles"][p["carril"]][0]
        x = round(cx - w / 2)
        y = round(ly) + round(cy - ly - h / 2)
        centros[p["id"]] = (x + w / 2, y + h / 2)
    notas = []
    for n, (x, y, w, h) in zip(proc.get("notas") or [], geo.get("anotaciones") or []):
        carril = next(p["carril"] for p in proc["pasos"] if p["id"] == n["paso"])
        ly = geo["carriles"][carril][0]
        notas.append((round(x), round(ly) + round(y - ly), round(w), round(h)))
    cajas = dm._cajas(proc, dict(geo, pasos=centros, anotaciones=notas))
    for p in proc["pasos"]:
        x, y = centros[p["id"]]
        w, h = tam[p["tipo"]]
        cajas.append((x - w / 2 - 6, y - h / 2 - 6, w + 12, h + 12))
        lado = geo.get("etiquetas", {}).get(p["id"])
        if lado and p.get("nombre"):
            lh = co.alto_texto(p["nombre"]) - 6
            cajas.append((x - co.ANCHO_ETIQUETA / 2 + 4, y - h / 2 - lh if lado == "arriba" else y + h / 2,
                          co.ANCHO_ETIQUETA - 8, lh))
    cajas += [(0, y, 24 + 7.5 * len(c), 26) for c, (y, _) in geo["carriles"].items()]
    alto = max(y + h for y, h in geo["carriles"].values())
    return centros, list(dict.fromkeys(cajas)), alto


def _cruces_de_caminos(caminos, solo=None):
    """{(i, j): cruces} entre los caminos (de borde a borde); con `solo`, los pares en los que está alguno de esos."""
    pares = {}
    claves = sorted(caminos)
    for a, i in enumerate(claves):
        for j in claves[a + 1:]:
            if solo is not None and i not in solo and j not in solo:
                continue
            n = 0
            for p, q in zip(caminos[i], caminos[i][1:]):
                for r, s in zip(caminos[j], caminos[j][1:]):
                    for h, h2, v, v2 in ((p, q, r, s), (r, s, p, q)):
                        if abs(h[1] - h2[1]) <= 1 and abs(v[0] - v2[0]) <= 1 and \
                                min(h[0], h2[0]) + 1 < v[0] < max(h[0], h2[0]) - 1 and \
                                min(v[1], v2[1]) + 1 < h[1] < max(v[1], v2[1]) - 1:
                            n += 1
            if n:
                pares[(i, j)] = n
    return pares


def _pegados(c, d):
    """Si dos caminos van en paralelo a menos de HUECO (sin ir por la misma recta) a lo largo de más de 20 px."""
    for p, q in zip(c, c[1:]):
        for r, s in zip(d, d[1:]):
            for eje in (0, 1):
                if abs(p[eje] - q[eje]) <= 1 and abs(r[eje] - s[eje]) <= 1 and 1 < abs(p[eje] - r[eje]) < HUECO:
                    o = 1 - eje
                    if min(max(p[o], q[o]), max(r[o], s[o])) - max(min(p[o], q[o]), min(r[o], s[o])) > 20:
                        return True
    return False


def _etiquetas_pisadas(proc, caminos, sitios):
    """Cuántas etiquetas de flujo cruza otro flujo."""
    import colocacion as co
    n = 0
    for i, sitio in sitios.items():
        texto = proc["flujos"][i].get("etiqueta")
        if not texto or i not in caminos:
            continue
        x, y = _punto(caminos[i], sitio)
        w = co.ancho_etiqueta_flujo(texto)
        caja = (x - w / 2, y - 7, w, 14)
        n += sum(1 for j, c in caminos.items() if j != i and any(_cruza(p, q, caja) for p, q in zip(c, c[1:])))
    return n


def mover_pasos(proc, geo, tam, cabecera):
    """Mueve un paso (o un paso con su vecino del mismo carril) dentro de su carril cuando así el trazado global
    cruza menos flujos: por ejemplo, para que un flujo que baja por una columna no corte el de dos pasos que están
    en ella. Solo con Mermaid. Deja los flujos ya trazados por la rejilla y devuelve `geo`."""
    import time
    import drawio_modelo as dm
    import colocacion as co
    if not geo.get("trazado_generado"):     # por capas, cada paso ya está en su fila y su columna
        return geo
    tipo = {p["id"]: p["tipo"] for p in proc["pasos"]}
    carril = {p["id"]: p["carril"] for p in proc["pasos"]}
    nombre = {p["id"]: p.get("nombre") for p in proc["pasos"]}
    flujos = proc["flujos"]
    indices = [i for i, f in enumerate(flujos) if f["de"] in tipo and f["a"] in tipo and f["de"] != f["a"]]
    if len(indices) < 2:
        return geo

    def caminos_de(g, centros, rutas):
        return {i: dm._camino(centros[flujos[i]["de"]], tam[tipo[flujos[i]["de"]]], rutas[i],
                              centros[flujos[i]["a"]], tam[tipo[flujos[i]["a"]]]) for i in rutas}

    centros, cajas, alto = _obstaculos(proc, geo, tam)
    r = trazar_todo(proc, dict(geo, pasos=centros), tam, cabecera, alto, cajas, indices, hueco=HUECO)
    if not r:
        return geo
    caminos, sitios = caminos_de(geo, centros, r[0]), r[1]
    pares = _cruces_de_caminos(caminos)

    def defectos(pares, caminos, sitios):
        # cada cruce, cada etiqueta que pisa otro flujo y cada par de flujos pegados, lo mismo de malo
        pegados = sum(1 for i, j in itertools.combinations(sorted(caminos), 2) if _pegados(caminos[i], caminos[j]))
        return sum(pares.values()) + _etiquetas_pisadas(proc, caminos, sitios) + pegados
    actual = inicio = defectos(pares, caminos, sitios)
    if not inicio:
        return geo

    def cajas_paso(g, pid, m=0):
        (cx, cy), (w, h) = g["pasos"][pid][:2], tam[tipo[pid]]
        out = [(cx - w / 2 - m, cy - h / 2 - m, w + 2 * m, h + 2 * m)]
        lado = g.get("etiquetas", {}).get(pid)
        if lado and nombre[pid]:
            a = co.alto_texto(nombre[pid])
            out.append((cx - co.ANCHO_ETIQUETA / 2, cy - h / 2 - a if lado == "arriba" else cy + h / 2,
                        co.ANCHO_ETIQUETA, a))
        out += [tuple(b) for n, b in zip(proc.get("notas") or [], g.get("anotaciones") or []) if n["paso"] == pid]
        return out

    def solapa(a, b, m=0):
        return a[0] - m < b[0] + b[2] and a[0] + a[2] + m > b[0] and a[1] - m < b[1] + b[3] and a[1] + a[3] + m > b[1]

    def cabe(g, grupo):
        for pid in grupo:
            y, h = g["carriles"][carril[pid]]
            titulo = (0, y, 24 + 7.5 * len(carril[pid]), 26)
            for b in cajas_paso(g, pid):
                if b[1] < y + 6 or b[1] + b[3] > y + h - 6 or b[0] < cabecera + 10 or b[0] + b[2] > g["ancho"] - 10 \
                        or solapa(b, titulo, 12):
                    return False
            for q in tipo:
                if q not in grupo and any(solapa(a, b, co.SEPARACION_X * 2 / 3)
                                          for a in cajas_paso(g, pid) for b in cajas_paso(g, q)):
                    return False
        return True

    def mover(g, grupo, dx, dy):
        g = dict(g, pasos=dict(g["pasos"]), anotaciones=list(g.get("anotaciones") or []))
        for pid in grupo:
            v = g["pasos"][pid]
            g["pasos"][pid] = (v[0] + dx, v[1] + dy) + tuple(v[2:])
        for k, n in enumerate(proc.get("notas") or []):
            if n["paso"] in grupo and k < len(g["anotaciones"]):
                x, y, w, h = g["anotaciones"][k]
                g["anotaciones"][k] = (x + dx, y + dy, w, h)
        return g

    def probar(g, grupo):
        centros, cajas, alto = _obstaculos(proc, g, tam)
        nuevas = [b for pid in grupo for b in cajas_paso(dict(g, pasos=centros), pid, 6)]
        # de nuevo, los flujos de los pasos movidos y los que pasaban por donde ahora están; los demás, igual
        otra = [i for i in indices if flujos[i]["de"] in grupo or flujos[i]["a"] in grupo or
                any(_cruza(p, q, b) for p, q in zip(caminos[i], caminos[i][1:]) for b in nuevas)]
        r = trazar_todo(proc, dict(g, pasos=centros), tam, cabecera, alto, cajas, otra, orden=otra,
                        fijas={i: c for i, c in caminos.items() if i not in otra}, visitas=VISITAS_PRUEBA,
                        hueco=HUECO)
        if not r:
            return None
        nuevos = dict(caminos)
        nuevos.update(caminos_de(g, centros, {i: r[0][i] for i in otra if i in r[0]}))
        # una ruta fija que no cabía en la rejilla nueva también se ha trazado de nuevo
        nuevos.update(caminos_de(g, centros, {i: p for i, p in r[0].items() if i not in otra and
                                               p != caminos[i][1:-1]}))
        cambiados = set(otra) | {i for i in r[0] if nuevos[i] != caminos[i]}
        cuenta = {k: v for k, v in pares.items() if not cambiados.intersection(k)}
        cuenta.update(_cruces_de_caminos(nuevos, cambiados))
        return cuenta, nuevos, r[1]

    def candidatos():
        """Para cada cruce, cada extremo de los dos flujos (solo o con su vecino del carril) se lleva al otro
        lado del tramo que lo corta: lo justo para quedar fuera, primero lo más cerca."""
        vistos, out = set(), []
        for (i, j) in sorted(pares, key=lambda k: -pares[k]):
            for a, b in ((i, j), (j, i)):
                for pid in (flujos[a]["de"], flujos[a]["a"]):
                    vecinos = [f[k] for f in flujos for k in ("de", "a") if pid in (f["de"], f["a"]) and
                               f[k] != pid and f[k] in tipo and carril[f[k]] == carril[pid]]
                    for grupo in [(pid,)] + [tuple(sorted((pid, v))) for v in vecinos]:
                        izq = min(b2[0] for q in grupo for b2 in cajas_paso(geo_actual, q))
                        der = max(b2[0] + b2[2] for q in grupo for b2 in cajas_paso(geo_actual, q))
                        arr = min(b2[1] for q in grupo for b2 in cajas_paso(geo_actual, q))
                        aba = max(b2[1] + b2[3] for q in grupo for b2 in cajas_paso(geo_actual, q))
                        for p, q in zip(caminos[b], caminos[b][1:]):
                            if abs(p[0] - q[0]) <= 1 and izq - 200 < p[0] < der + 200:      # tramo vertical
                                movs = [(p[0] - 30 - der, 0), (p[0] + 30 - izq, 0)]
                            elif abs(p[1] - q[1]) <= 1 and arr - 120 < p[1] < aba + 120:    # horizontal
                                movs = [(0, p[1] - 20 - aba), (0, p[1] + 20 - arr)]
                            else:
                                continue
                            for dx, dy in movs:
                                dx, dy = round(dx / 8) * 8, round(dy / 8) * 8
                                # un empujón de pocos píxeles solo mueve la rejilla y desalinea el paso
                                if abs(dx) + abs(dy) >= 24 and abs(dx) <= 320 and abs(dy) <= 160 and (grupo, dx, dy) not in vistos:
                                    vistos.add((grupo, dx, dy))
                                    out.append((abs(dx) + abs(dy) + 40 * (len(grupo) - 1), grupo, dx, dy))
        return [c[1:] for c in sorted(out)]

    geo_actual = geo
    fin = time.monotonic() + TIEMPO_MOVER
    mejorado = True
    while mejorado and time.monotonic() < fin:
        mejorado = False
        for grupo, dx, dy in candidatos():
            if time.monotonic() >= fin:
                break
            g = mover(geo_actual, grupo, dx, dy)
            if not cabe(g, grupo):
                continue
            r = probar(g, grupo)
            if not r or sum(r[0].values()) > sum(pares.values()):
                continue
            nuevo = defectos(*r)
            if nuevo < actual:
                geo_actual, (pares, caminos, sitios), actual = g, r, nuevo
                mejorado = True
                break
    if actual >= inicio:
        return geo
    geo["pasos"], geo["anotaciones"] = geo_actual["pasos"], geo_actual["anotaciones"]
    for i, c in caminos.items():
        geo["flujos"][i] = [tuple(p) for p in c[1:-1]]
    geo["etiquetas_flujo"] = sitios
    return geo
