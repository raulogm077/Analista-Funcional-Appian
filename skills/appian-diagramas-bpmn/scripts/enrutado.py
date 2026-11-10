"""Mejora conservadora de las rutas generadas por capas.

Prueba corredores ortogonales sin mover pasos, notas, puertos ni carriles. Una
ruta solo se conserva si quita conexiones ambiguas del diagrama completo sin
añadir otras ni cruces. Las rutas importadas y manuales no pasan por aquí.
"""
from collections import Counter
import math
import sys

sys.dont_write_bytecode = True

MAX_INTENTOS = 1200       # trabajo acotado incluso en un proceso muy conectado
MAX_CANDIDATOS = 6000     # también los que se descartan con las guardas baratas


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


def mejorar(proc, geo, tam, cabecera):
    """Modifica solo si mejora el diagrama; de lo contrario deja `geo` intacta."""
    import drawio_modelo as dm
    import colocacion as co
    if not geo.get("etiqueta_en_horizontal"):
        return geo
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
            if clave[0] in ("etiqueta", "juntos", "reserva", "etiquetas"):
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
                if sitio is None or i in cambiados:
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
    if not actual[0]:
        return geo
    originales = [list(p) for p in geo["flujos"]]
    base = actual
    intentos = revisados = 0
    # Una evaluación crece con los pares de flujos. Reducir su número en los
    # procesos densos mantiene acotada esta mejora opcional.
    limite = min(MAX_INTENTOS, max(1, MAX_INTENTOS * 20 * 20 // len(indices) ** 2))

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
            if not actual[0]:
                break
            if i not in actual[4]:
                continue
            antes = geo["flujos"][i]
            elegido = False
            for candidato in _candidatos(actual[4][i], cajas, geo["ancho"], alto, cabecera):
                if intentos >= limite or revisados >= MAX_CANDIDATOS:
                    break
                revisados += 1
                if any(_cruza(p, q, box) for p, q in zip(candidato, candidato[1:]) for box in cajas):
                    continue
                if any(_cruza(p, q, box) for p, q in zip(candidato, candidato[1:])
                       for pid, cs in cajas_paso.items() if pid not in (flujos[i]["de"], flujos[i]["a"]) for box in cs):
                    continue
                geo["flujos"][i] = candidato[1:-1]
                intentos += 1
                prueba = medir(actual, (i,))
                if aceptar(prueba):
                    actual = prueba
                    elegido = True
                    cambio = True
                    break
            if not elegido:
                geo["flujos"][i] = antes
        if not cambio or not actual[0] or intentos >= limite or revisados >= MAX_CANDIDATOS:
            break
    if sum(actual[0].values()) < sum(base[0].values()):
        geo["etiquetas_flujo"] = actual[3]
    else:
        geo["flujos"] = originales
    return geo
