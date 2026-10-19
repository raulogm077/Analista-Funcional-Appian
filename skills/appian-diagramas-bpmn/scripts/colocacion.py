"""Colocación de los pasos sin navegador y ajustes para que el dibujo de draw.io no se pise.

- `por_capas`: la colocación de reserva, cuando no hay navegador para el motor de Mermaid: capas de izquierda a
  derecha (el camino más largo desde el inicio, sin contar las vueltas atrás) y un carril por perfil; los flujos
  largos y las vueltas atrás van por huecos que no pisan ningún paso, y las salidas de una puerta que compartirían el
  tramo de su derecha salen por su vértice (el codo), para que la etiqueta de cada una vaya en un tramo suyo.
- `tramos`: parte un proceso que no cabe en una página en tramos de capas seguidas (sin inventar subprocesos).
- `ajustar`: el motor da a cada paso el ancho de su texto, pero en draw.io las tareas miden siempre 120×80 y las
  etiquetas de eventos y puertas ocupan hasta 110 px de ancho. Se elige a qué lado va la etiqueta de cada evento o
  puerta, para que ningún flujo la cruce; se separan los pasos solo lo necesario (nunca se acercan) para que ninguna
  forma, etiqueta o nota pise a otra (cada eje se transforma con una función creciente, así que los tramos rectos
  siguen rectos), y se colocan las notas junto a su paso y los participantes externos debajo de los carriles.
Solo usa la biblioteca estándar.
"""
import bisect
from collections import defaultdict

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
COLUMNA = 160            # colocación de reserva: entre los centros de dos capas (tarea, 120, y hueco)
FILA = 110               # y entre los centros de dos filas de un carril
CORREDOR = 30            # alto del pasillo de una vuelta atrás, debajo de las filas del carril
BORDE = ("temporizador", "mensaje", "intermedio", "error")   # eventos que, unidos a una tarea, van en su borde


# ---------------------------------------------------------------- colocación de reserva (sin navegador)
def capas(proc):
    """Capa de cada paso (el camino más largo desde un paso sin entradas, sin contar las vueltas atrás) y los índices
    de los flujos que vuelven atrás. Los flujos de mensaje no cuentan."""
    ids = [p["id"] for p in proc["pasos"]]
    salen = {pid: [] for pid in ids}
    entran = {pid: 0 for pid in ids}
    for i, f in enumerate(proc["flujos"]):
        if f["de"] in salen and f["a"] in salen:
            salen[f["de"]].append((f["a"], i))
            entran[f["a"]] += 1
    atras, estado, orden = set(), {}, []
    for raiz in [pid for pid in ids if not entran[pid]] + ids:
        if raiz in estado:
            continue
        estado[raiz] = 1
        pila = [(raiz, iter(salen[raiz]))]
        while pila:
            v, hijos = pila[-1]
            sig = next(hijos, None)
            if sig is None:
                estado[v] = 2
                orden.append(v)
                pila.pop()
            elif estado.get(sig[0]) == 1:
                atras.add(sig[1])
            elif sig[0] not in estado:
                estado[sig[0]] = 1
                pila.append((sig[0], iter(salen[sig[0]])))
    capa = {pid: 0 for pid in ids}
    for u in reversed(orden):
        for v, i in salen[u]:
            if i not in atras:
                capa[v] = max(capa[v], capa[u] + 1)
    return capa, atras


def por_capas(proc, eventos, puertas, cabecera):
    """Geometría como la del motor: {"carriles": {nombre: (y, h)}, "pasos": {id: (cx, cy)}, "flujos": [[(x, y)…]],
    "ancho"}. Una columna por capa y, en cada carril, una fila por paso de la misma capa (ordenadas como sus
    predecesores, para que se crucen poco). Un flujo que salta capas ocupa una fila en las capas que cruza y una vuelta
    atrás va por un pasillo debajo de las filas del carril al que vuelve: así ninguno atraviesa un paso."""
    capa, atras = capas(proc)
    carril = {p["id"]: p["carril"] for p in proc["pasos"]}
    orden_paso = {p["id"]: k for k, p in enumerate(proc["pasos"])}
    secuencia = [(i, f) for i, f in enumerate(proc["flujos"]) if f["de"] in carril and f["a"] in carril]
    por_capa, lado_de, previos = defaultdict(list), {}, defaultdict(list)
    for pid in carril:
        por_capa[capa[pid]].append(("paso", pid))
        lado_de[("paso", pid)] = carril[pid]
    pasillos = defaultdict(list)                     # carril -> vueltas atrás que van por su pasillo
    for i, f in secuencia:
        a, b = capa[f["de"]], capa[f["a"]]
        if i in atras:
            if f["de"] != f["a"]:
                pasillos[carril[f["a"]]].append(i)
            continue
        anterior = ("paso", f["de"])
        for capa_hueco in range(a + 1, b):           # el flujo largo reserva su fila en cada capa que cruza
            hueco = ("hueco", i, capa_hueco)
            por_capa[capa_hueco].append(hueco)
            lado_de[hueco] = carril[f["de"]]
            previos[hueco].append(anterior)
            anterior = hueco
        previos[("paso", f["a"])].append(anterior)
    # filas: capa a capa, en el orden medio de sus predecesores. Una puerta reserva una fila por cada salida que sigue en
    # su carril: así sale en vertical hacia sus destinos sin que otro paso de su columna se lo tape
    tipo = {p["id"]: p["tipo"] for p in proc["pasos"]}
    salidas = defaultdict(int)
    for i, f in secuencia:
        if tipo[f["de"]] in puertas and i not in atras and f["de"] != f["a"]:
            sig = ("hueco", i, capa[f["de"]] + 1) if capa[f["a"]] > capa[f["de"]] + 1 else ("paso", f["a"])
            if lado_de[sig] == carril[f["de"]]:
                salidas[("paso", f["de"])] += 1
    posicion, fila = {}, {}
    indice = {c: k for k, c in enumerate(proc["carriles"])}
    for c in sorted(por_capa):
        for nombre in proc["carriles"]:
            suyos = [e for e in por_capa[c] if lado_de[e] == nombre]
            def clave(e):
                ps = [posicion[x] for x in previos[e] if x in posicion]
                media = sum(ps) / len(ps) if ps else None
                return (media is None, media or 0, orden_paso.get(e[1], 0) if e[0] == "paso" else e[1])
            libre = 0
            for e in sorted(suyos, key=clave):
                # con una sola entrada, desde su carril, en la fila del anterior (si está libre): sin vertical entre los dos
                unico = previos[e][0] if len(previos[e]) == 1 and lado_de.get(previos[e][0]) == nombre else None
                fila[e] = max(libre, fila.get(unico, 0))
                posicion[e] = indice[nombre] * 1000 + fila[e]
                libre = fila[e] + max(1, salidas[e])
    bajar_a_su_siguiente(por_capa, previos, lado_de, fila, salidas)
    filas = {c: max([fila[e] + 1 for e in fila if lado_de[e] == c] or [1]) for c in proc["carriles"]}
    geo = {"carriles": {}, "pasos": {}, "flujos": [], "etiqueta_en_horizontal": True}
    y = 0.0
    for c in proc["carriles"]:
        h = 2 * MARGEN + filas[c] * FILA + len(pasillos[c]) * CORREDOR
        geo["carriles"][c] = (y, h)
        y += h
    yy = lambda e: geo["carriles"][lado_de[e]][0] + MARGEN + fila[e] * FILA + FILA / 2    # noqa: E731
    pasillo = {i: geo["carriles"][c][0] + MARGEN + filas[c] * FILA + (k + 0.5) * CORREDOR
               for c, vueltas in pasillos.items() for k, i in enumerate(vueltas)}
    # trazado: los tramos verticales van por el hueco entre dos columnas, cada flujo a su altura del hueco para que no
    # se monten; los de una puerta salen en vertical desde ella, salvo que otro paso de su columna lo tape (entonces
    # por su derecha o, si allí comparten tramo con otra salida, por el codo: salidas_por_codo)
    en_columna = {c: [yy(e) for e in lista] for c, lista in por_capa.items()}
    nombre = {p["id"]: p.get("nombre") for p in proc["pasos"]}

    def tapado(pid, y2):
        """Si al salir en vertical de `pid` hasta y2 (y seguir en horizontal) se cruzaría otro paso de su columna o un
        flujo largo que la atraviesa."""
        y1 = yy(("paso", pid))
        return any(abs(y - y1) > 1 and min(y1, y2) - 1 <= y <= max(y1, y2) + 1 for y in en_columna[capa[pid]])

    def cabe_debajo(pid):
        """Si la etiqueta de la puerta cabe debajo de ella sin que la cruce el pasillo de una vuelta atrás."""
        y, alto = yy(("paso", pid)), 25 + alto_texto(nombre[pid]) + 2 + AIRE_ETIQUETA
        return not any(y < pasillo[i] < y + alto and capa[f["a"]] <= capa[pid] <= capa[f["de"]]
                       for i, f in secuencia if i in pasillo)

    def trazar(codo):
        """Con las salidas que van por el codo ({flujo: y del codo}): la ruta de cada flujo, lo que usa cada uno de cada
        hueco ({hueco (capa a su izquierda): {flujo: [y al entrar, y al salir]}}) y, en el hueco, qué salidas por el
        codo van a la izquierda de cada flujo: las de su puerta, que si no lo cruzarían."""
        usos, rutas = defaultdict(dict), []
        for i, f in enumerate(proc["flujos"]):
            ruta = []
            if f["de"] not in carril or f["a"] not in carril or f["de"] == f["a"]:
                pass
            elif i in pasillo:
                # vuelta atrás: por el hueco de su derecha, el pasillo y el hueco de la izquierda del destino
                sy, ty = yy(("paso", f["de"])), yy(("paso", f["a"]))
                ruta = [("hueco", capa[f["de"]], sy), ("hueco", capa[f["de"]], pasillo[i]),
                        ("hueco", capa[f["a"]] - 1, pasillo[i]), ("hueco", capa[f["a"]] - 1, ty)]
            else:
                cadena = ([("paso", f["de"])] + [("hueco", i, c) for c in range(capa[f["de"]] + 1, capa[f["a"]])]
                          + [("paso", f["a"])])
                for k, (e, sig) in enumerate(zip(cadena, cadena[1:])):
                    if abs(yy(e) - yy(sig)) <= 1 and not (k == 0 and i in codo):
                        continue
                    if k == 0 and i in codo:      # por su vértice hasta el codo y por él al hueco
                        ruta += [("columna", capa[f["de"]], codo[i]), ("hueco", capa[f["de"]], codo[i]),
                                 ("hueco", capa[f["de"]], yy(sig))]
                    elif k == 0 and tipo[f["de"]] in puertas and not tapado(f["de"], yy(sig)):
                        ruta.append(("columna", capa[f["de"]], yy(sig)))
                    else:
                        ruta += [("hueco", capa[f["de"]] + k, yy(e)), ("hueco", capa[f["de"]] + k, yy(sig))]
            for punto in ruta:
                if punto[0] == "hueco":
                    usos[punto[1]].setdefault(i, [punto[2], punto[2]])[1] = punto[2]
            rutas.append(ruta)
        izquierda = {j: {i for i in codo if i != j and proc["flujos"][i]["de"] == f["de"]} for j, f in secuencia}
        return rutas, usos, izquierda

    def colocar_columnas(ancho_col, trazado):
        """Las x: de cada columna, de cada paso y de cada flujo en los huecos entre columnas."""
        rutas, usos, a_su_izquierda = trazado
        xs = [cabecera + MARGEN + 60 + (40 if any(capa[f["a"]] == 0 for i, f in secuencia if i in atras) else 0)]
        for c in range(ultima + 1):
            xs.append(xs[-1] + ancho_col[c])
        for pid in carril:
            geo["pasos"][pid] = (xs[capa[pid]], yy(("paso", pid)))
        sitio = {}
        for hueco, extremos in usos.items():
            izquierda = xs[hueco] if hueco >= 0 else xs[0] - COLUMNA
            derecha = xs[hueco + 1] if hueco + 1 < len(xs) else izquierda + COLUMNA
            centro, libre = (izquierda + derecha) / 2, (derecha - izquierda - 120) / 2 - 6
            orden = orden_en_hueco(extremos, a_su_izquierda)
            separaciones = separacion_hueco.get(hueco, {})
            distancias = [max(10, separaciones.get(i, 10), separaciones.get(j, 10)) for i, j in zip(orden, orden[1:])]
            escala = min(1, 2 * libre / max(sum(distancias), 1))
            x = centro - sum(distancias) * escala / 2
            for k, i in enumerate(orden):
                sitio[(hueco, i)] = x
                if k < len(distancias):
                    x += distancias[k] * escala
        geo["flujos"] = [[(sitio[(p[1], i)], p[2]) if p[0] == "hueco" else (xs[p[1]], p[2]) if p[0] == "columna" else p
                          for p in ruta] for i, ruta in enumerate(rutas)]
        geo["ancho"] = max([cx for cx, _ in geo["pasos"].values()] + [xs[0]]) + COLUMNA / 2 + MARGEN

    # columnas: la de después de una puerta, ancha para la etiqueta de sus salidas, que va en el tramo horizontal (y para
    # la marca del flujo por defecto, al salir de la puerta); si un flujo que sube o baja por el hueco la corta, más
    ultima = max(capa.values(), default=0)
    ancho_col = [COLUMNA] * (ultima + 2)
    separacion_hueco = {}
    for i, f in secuencia:
        if f.get("etiqueta") and tipo[f["de"]] in puertas and i not in atras:
            ancho_col[capa[f["de"]]] = max(ancho_col[capa[f["de"]]], ancho_columna_puerta(proc, f))
    # una salida va por el codo solo si así no se cruza con más flujos: si no, se queda en el tramo que comparte
    colocar_columnas(ancho_col, trazar({}))
    codo = salidas_por_codo(proc, secuencia, atras, capa, tipo, puertas, eventos, yy, tapado, cabe_debajo, geo)
    for i in sorted(codo):
        sin = {j: y for j, y in codo.items() if j != i}
        cuenta = []
        for prueba in (codo, sin):
            trazado = trazar(prueba)
            colocar_columnas(ancho_col, trazado)
            cuenta.append(cruces(proc, geo, set(trazado[1][capa[proc["flujos"][i]["de"]]]) | {i}))
        if cuenta[0] > cuenta[1]:
            codo = sin
    trazado = trazar(codo)
    for _ in range(3):
        colocar_columnas(ancho_col, trazado)
        falta = etiquetas_cortadas(proc, geo, capa, atras, eventos, puertas, codo, separacion_hueco)
        for c, distancias in separacion_hueco.items():
            orden = orden_en_hueco(trazado[1][c], trazado[2])
            necesita = sum(max(10, distancias.get(i, 10), distancias.get(j, 10)) for i, j in zip(orden, orden[1:])) + 132
            if necesita > ancho_col[c]:
                falta[c] = max(falta.get(c, 0), necesita - ancho_col[c])
        if not falta:
            break
        for c, px in falta.items():
            ancho_col[c] += px
    return geo


def bajar_a_su_siguiente(por_capa, previos, lado_de, fila, salidas):
    """De la última columna a la primera: lo que solo sale hacia otro de su carril, que solo entra desde él, baja a su
    fila si en su columna está libre y sin saltar por encima de otro: así no queda una vertical entre los dos."""
    siguientes = defaultdict(list)
    for e, ps in previos.items():
        for p in ps:
            siguientes[p].append(e)
    for c in sorted(por_capa, reverse=True):
        for e in sorted(por_capa[c], key=lambda x: -fila[x]):
            sig = siguientes.get(e, [])
            if len(sig) != 1 or len(previos[sig[0]]) != 1 or lado_de[sig[0]] != lado_de[e] or fila[sig[0]] <= fila[e]:
                continue
            hasta = fila[sig[0]] + max(1, salidas[e]) - 1
            if all(fila[x] < fila[e] or fila[x] > hasta for x in por_capa[c] if x != e and lado_de[x] == lado_de[e]):
                fila[e] = fila[sig[0]]


MARCA_DEFECTO = 20       # lo que ocupa la marca del flujo por defecto al salir de una puerta, con su aire
AIRE_ETIQUETA = 6        # entre la etiqueta de un flujo y lo que la rodea (la flecha, otro flujo)
CODO = 40                # lo que baja o sube por su vértice una salida de una puerta antes de ir al hueco: pasada la
                         # puerta (25) y con sitio para su etiqueta (14 de alto) sin llegar a lo de la fila de al lado


def salidas_por_codo(proc, secuencia, atras, capa, tipo, puertas, eventos, yy, tapado, cabe_debajo, geo):
    """{flujo: y del codo} de las salidas de una puerta que dejan de compartir el tramo que sale por su derecha. Por la
    derecha sale la que sigue en su fila, una vuelta atrás y las que van por el hueco porque algo de su columna les
    tapa la vertical (`tapado`): si son más de una, la que va más lejos hacia abajo sale por el vértice de abajo y, si
    por abajo no sale ninguna y la etiqueta de la puerta cabe debajo (`cabe_debajo`), la que va más lejos hacia arriba,
    por el de arriba (con salidas por los dos vértices, la etiqueta de la puerta pisaría una). Bajan o suben CODO y van
    al hueco por un tramo suyo, donde va su etiqueta: en el compartido no se sabría de qué salida es."""
    por_puerta = defaultdict(list)
    for i, f in secuencia:
        if tipo[f["de"]] in puertas and f["de"] != f["a"]:
            sig = ("hueco", i, capa[f["de"]] + 1) if capa[f["a"]] > capa[f["de"]] + 1 else ("paso", f["a"])
            # una vuelta atrás sale por la derecha, hacia el hueco de su pasillo: como la que sigue en su fila
            por_puerta[f["de"]].append((i, 0 if i in atras else yy(sig) - yy(("paso", f["de"]))))
    codo = {}
    def recto_compartido(i):
        f = proc["flujos"][i]
        x, y = geo["pasos"][f["de"]]
        mitad = 25 if tipo[f["a"]] in puertas else 20 if tipo[f["a"]] in eventos else 60
        fin = geo["pasos"][f["a"]][0] - mitad
        ocupado = []
        for j, g in secuencia:
            if i == j:
                continue
            camino = [geo["pasos"][g["de"]]] + geo["flujos"][j] + [geo["pasos"][g["a"]]]
            ocupado += [sorted((p[0], q[0])) for p, q in zip(camino, camino[1:])
                        if abs(p[1] - y) <= 1 and abs(q[1] - y) <= 1]
        hasta = x + 25
        for a, b in sorted(ocupado):
            if a > hasta + 1:
                break
            hasta = max(hasta, b)
        return hasta >= fin
    for pid, salidas in por_puerta.items():
        y = yy(("paso", pid))
        derecha = [(i, dy) for i, dy in salidas if abs(dy) <= 1 or tapado(pid, y + dy)]
        if len(derecha) < 2:
            continue
        por_abajo = any(dy > 1 and not tapado(pid, y + dy) for _, dy in salidas)
        for signo in (1, -1):
            lejos = max((s for s in derecha if s[1] * signo > 1), key=lambda s: s[1] * signo, default=None)
            if lejos is None and signo == 1:
                # Una salida recta puede compartir el inicio con otra salida y el final con
                # otra entrada al destino: también necesita un tramo propio para su etiqueta.
                lejos = next((s for s in derecha if abs(s[1]) <= 1 and s[0] not in atras
                              and recto_compartido(s[0])), None)
            if lejos and (signo == 1 or not por_abajo and cabe_debajo(pid)) and not tapado(pid, y + signo * CODO):
                codo[lejos[0]] = y + signo * CODO
                por_abajo = por_abajo or signo == 1
    return codo


def ancho_columna_puerta(proc, f):
    """Ancho de la columna que sigue a la puerta de la que sale `f`, para su etiqueta en el tramo horizontal y, si la
    puerta tiene salida por defecto, su marca."""
    defecto = any(g.get("defecto") for g in proc["flujos"] if g["de"] == f["de"])
    return ancho_etiqueta_flujo(f["etiqueta"]) + 100 + (MARCA_DEFECTO if defecto else 0)


def etiquetas_cortadas(proc, geo, capa, atras, eventos, puertas, codo=(), separacion_hueco=None):
    """{capa: px}: lo que hay que ensanchar la columna que sigue a una puerta para que la etiqueta de una de sus salidas
    quepa en un trozo de su tramo que no cruza ni comparte otro flujo (donde la pone draw.io): el de la que va en recto
    al paso siguiente, el del codo al hueco (`codo`) o, en la que sale por la derecha y sube o baja por el hueco hasta
    el paso siguiente, el de la derecha o el último, que llega al paso. Un flujo que sube o baja por el hueco está en
    su centro: se aleja de la flecha (o del codo) la mitad de lo que se ensancha."""
    tipo = {p["id"]: p["tipo"] for p in proc["pasos"]}
    medio = lambda pid: 25 if tipo[pid] in puertas else 20 if tipo[pid] in eventos else 60    # noqa: E731

    def libres(i, lo, y, hi):
        """Los trozos (desde, hasta) del tramo de lo a hi a la altura y que no cruza ni comparte otro flujo que el i, y
        si hay alguno que lo haga."""
        ocupado = []
        for j, (g, pts) in enumerate(zip(proc["flujos"], geo["flujos"])):
            camino = [geo["pasos"][g["de"]]] + pts + [geo["pasos"][g["a"]]] if g["de"] in tipo and g["a"] in tipo else pts
            for p, q in zip(camino, camino[1:]):
                if j != i and abs(p[0] - q[0]) <= 1 and min(p[1], q[1]) - 1 <= y <= max(p[1], q[1]) + 1:
                    ocupado.append((p[0], p[0]))                                        # lo cruza
                elif j != i and abs(p[1] - q[1]) <= 1 and abs(p[1] - y) <= 1:
                    ocupado.append(tuple(sorted((p[0], q[0]))))                         # va por la misma recta
        trozos, desde = [], lo
        for a, b in sorted(ocupado):
            trozos.append((desde, min(a, hi)))
            desde = max(desde, b)
        return trozos + [(desde, hi)], bool(ocupado)
    falta = {}
    for i, f in enumerate(proc["flujos"]):
        if not f.get("etiqueta") or i in atras or tipo.get(f["de"]) not in puertas or f["a"] not in tipo:
            continue
        (gx, gy), (tx, ty), ruta = geo["pasos"][f["de"]], geo["pasos"][f["a"]], geo["flujos"][i]
        siguiente = capa[f["a"]] == capa[f["de"]] + 1
        al_paso = siguiente and len(ruta) == 2 and abs(ruta[0][0] - gx) > 1   # por la derecha al hueco y en él al paso
        if i in codo:
            tramos = [(gx, ruta[0][1], ruta[1][0])]
        elif siguiente and not ruta and abs(gy - ty) <= 1:
            tramos = [(gx + medio(f["de"]), gy, tx - medio(f["a"]))]
        elif al_paso:
            tramos = [(gx + medio(f["de"]), gy, ruta[0][0]), (ruta[-1][0], ty, tx - medio(f["a"]))]
        else:
            continue
        medidas = [libres(i, *t) for t in tramos]
        mayor = max(b - a for trozos, _ in medidas for a, b in trozos)
        necesita = ancho_etiqueta_flujo(f["etiqueta"]) + 2 * AIRE_ETIQUETA
        if mayor >= necesita or not (medidas[0][1] or i in codo or al_paso):
            continue
        if al_paso:   # al ensanchar, solo crece el trozo que llega al paso (ninguno si otro flujo llega por él)
            mayor = next((b - a for a, b in medidas[-1][0] if b == tramos[-1][2]), 0)
            if mayor <= 0:
                if separacion_hueco is not None:
                    # Los dos horizontales están ocupados. La etiqueta debe caber en la
                    # vertical entre columnas, sin tocar la vertical vecina a 10 px.
                    c = capa[f["de"]]
                    separacion_hueco.setdefault(c, {})[i] = max(separacion_hueco.get(c, {}).get(i, 10), necesita / 2 + 1)
                continue
        falta[capa[f["de"]]] = max(falta.get(capa[f["de"]], 0), 2 * (necesita - mayor))
    return falta


def cruces(proc, geo, flujos=None):
    """Cuántas veces se cruzan dos flujos (un tramo horizontal de uno y uno vertical del otro, por dentro de los dos);
    con `flujos`, solo las de alguno de esos con otro."""
    tramos = {}
    for i, (f, pts) in enumerate(zip(proc["flujos"], geo["flujos"])):
        if f["de"] in geo["pasos"] and f["a"] in geo["pasos"]:
            camino = [geo["pasos"][f["de"]][:2]] + list(pts) + [geo["pasos"][f["a"]][:2]]
            tramos[i] = list(zip(camino, camino[1:]))
    n = 0
    for i, j in ((i, j) for i in tramos for j in tramos if i < j and (flujos is None or i in flujos or j in flujos)):
        for a in tramos[i]:
            for b in tramos[j]:
                for (h, h2), (v, v2) in ((a, b), (b, a)):
                    if abs(h[1] - h2[1]) <= 1 and abs(v[0] - v2[0]) <= 1 and min(h[0], h2[0]) + 1 < v[0] < \
                            max(h[0], h2[0]) - 1 and min(v[1], v2[1]) + 1 < h[1] < max(v[1], v2[1]) - 1:
                        n += 1
    return n


def orden_en_hueco(extremos, a_su_izquierda=None):
    """De izquierda a derecha, los flujos que suben o bajan por un hueco ({flujo: (y al entrar, y al salir)}): por la
    fila de la que vienen, salvo que uno salga de la fila a la que llega otro, que va a su izquierda; si no, el tramo
    horizontal del que llega pisaría al del que sale y parecería un solo flujo. `a_su_izquierda` ({flujo: {flujos}})
    dice además qué otros van a la izquierda de uno: la salida de su puerta por el codo, que si no lo cruzaría."""
    pendientes = sorted(extremos, key=lambda i: (extremos[i][0], i))
    antes = {i: {j for j in extremos if j != i and (abs(extremos[j][0] - extremos[i][1]) <= 1
                                                   or j in (a_su_izquierda or {}).get(i, ()))} for i in extremos}
    orden = []
    while pendientes:          # si dos se cruzan las filas (uno va de a a b y otro de b a a), el primero
        quedan = set(pendientes)
        i = next((i for i in pendientes if not antes[i] & quedan), pendientes[0])
        pendientes.remove(i)
        orden.append(i)
    return orden


def ancho_etiqueta_flujo(texto):
    """Ancho de la etiqueta de un flujo (11 px, en una línea), por exceso."""
    return len(str(texto or "")) * 7 + 12


# ---------------------------------------------------------------- tramos de una página
def _ancho_capa(proc, eventos, puertas):
    """Lo que ocupa cada capa a lo ancho en la colocación final (forma o etiqueta, nota y hueco)."""
    capa, _ = capas(proc)
    notas = defaultdict(int)
    for n in proc.get("notas") or []:
        notas[n["paso"]] = max(notas[n["paso"]], ancho_nota(n.get("texto")))
    ancho = defaultdict(int)
    for p in proc["pasos"]:
        forma = 120 if p["tipo"] not in eventos | puertas else (ANCHO_ETIQUETA if p.get("nombre") else 50)
        ancho[capa[p["id"]]] = max(ancho[capa[p["id"]]], COLUMNA, forma + SEPARACION_X, notas[p["id"]] + SEPARACION_X)
    tipo = {p["id"]: p["tipo"] for p in proc["pasos"]}
    for f in proc["flujos"]:      # después de una puerta, el sitio de la etiqueta de sus salidas
        if f.get("etiqueta") and tipo.get(f["de"]) in puertas and f["a"] in tipo:
            ancho[capa[f["de"]]] = max(ancho[capa[f["de"]]], ancho_columna_puerta(proc, f))
    return capa, ancho


def _bordes(cabecera):
    """Lo que ocupa una página además de sus capas: la cabecera de los carriles y los márgenes (la primera capa empieza
    a 60 px del margen y la última acaba media columna después de su centro)."""
    return cabecera + 2 * MARGEN + 60 + COLUMNA / 2 - COLUMNA


def ancho_estimado(proc, eventos, puertas, cabecera):
    _, ancho = _ancho_capa(proc, eventos, puertas)
    return _bordes(cabecera) + sum(ancho.values())


def tramos(proc, eventos, puertas, tareas, cabecera, ancho_max=ANCHO_LEGIBLE):
    """Los pasos de cada tramo, en orden: capas seguidas que caben en `ancho_max` con una columna a cada lado para los
    eventos de enlace. Un evento en el borde de una tarea va en el tramo de la tarea."""
    capa, ancho = _ancho_capa(proc, eventos, puertas)
    util = ancho_max - _bordes(cabecera) - 2 * COLUMNA

    def reparto(limite):
        tramo_de_capa, k, ocupado = {}, 0, 0
        for c in sorted(ancho):
            if ocupado and ocupado + ancho[c] > limite:
                k, ocupado = k + 1, 0
            tramo_de_capa[c] = k
            ocupado += ancho[c]
        return tramo_de_capa, k + 1

    tramo_de_capa, n = reparto(util)
    if n > 1:     # los mismos tramos, igualados (que el último no se quede con un par de pasos), si caben
        total, acumulado, igualado = sum(ancho.values()), 0, {}
        for c in sorted(ancho):
            igualado[c] = min(n - 1, int((acumulado + ancho[c] / 2) / total * n))
            acumulado += ancho[c]
        ocupa = defaultdict(int)
        for c, t in igualado.items():
            ocupa[t] += ancho[c]
        if len(ocupa) == n and max(ocupa.values()) <= util:
            tramo_de_capa = igualado
    tramo = {pid: tramo_de_capa[c] for pid, c in capa.items()}
    return _agrupar(proc, tramo, tareas)


def _agrupar(proc, tramo, tareas):
    tipo = {p["id"]: p["tipo"] for p in proc["pasos"]}
    for f in proc["flujos"]:      # el evento de borde, con su tarea
        if f.get("discontinuo") and tipo.get(f["a"]) in BORDE and tipo.get(f["de"]) in tareas:
            tramo[f["a"]] = tramo[f["de"]]
    numeros = sorted(set(tramo.values()))
    return [[p["id"] for p in proc["pasos"] if tramo[p["id"]] == n] for n in numeros]


def partir_en_dos(proc, grupo, tareas):
    """Un tramo que aun así no cabe, en dos por la mitad de sus capas. Si tiene una sola capa, no se parte."""
    capa, _ = capas(proc)
    suyas = sorted({capa[pid] for pid in grupo})
    if len(suyas) < 2:
        return [grupo]
    corte = suyas[len(suyas) // 2]
    dentro = set(grupo)
    tramo = {p["id"]: (0 if capa[p["id"]] < corte else 1) if p["id"] in dentro else -1 for p in proc["pasos"]}
    return [g for g in _agrupar(proc, tramo, tareas) if g and g[0] in dentro]


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


def _corrida(sentidos):
    """Hacia dónde se corre una nota en un lado por el que salen flujos que siguen hacia `sentidos` (-1 izquierda, 0 en
    vertical, 1 derecha): al lado contrario, para que no la crucen; None si van hacia los dos lados."""
    s = sentidos - {0}
    if s == {1} or (not s and 0 in sentidos):
        return "izquierda"
    return "derecha" if s == {-1} else "centro" if not s else None


def lados_nota(proc, usados, lados):
    """Sitio de cada nota respecto a su paso: (lado, desplazamiento). Arriba, salvo que lo usen la etiqueta o un flujo
    y abajo esté libre. Si los dos están ocupados, el de los flujos que no es el de la etiqueta (la línea de la nota la
    cruzaría), corrida para que los flujos no la crucen. Si no queda otro, el de la etiqueta, pero al lado de ella
    («fuera_izquierda» o «fuera_derecha»): su línea entra en el paso por debajo de la etiqueta."""
    out = []
    for n in proc.get("notas") or []:
        u = usados.get(n["paso"], {})
        etiqueta = lados.get(n["paso"])
        libres = [lado for lado in ("arriba", "abajo") if lado not in u and lado != etiqueta]
        con_flujos = [lado for lado in ("arriba", "abajo") if lado != etiqueta and _corrida(u.get(lado, set()))]
        if libres:
            out.append((libres[0], "centro"))
        elif con_flujos:
            out.append((con_flujos[0], _corrida(u[con_flujos[0]])))
        elif etiqueta:
            out.append((etiqueta, "fuera_derecha" if _corrida(u.get(etiqueta, set())) == "derecha" else "fuera_izquierda"))
        else:
            out.append(("arriba", "centro"))
    return out


def x_nota(cx, desplazamiento, ancho=NOTA_ANCHO):
    """x del borde izquierdo de una nota según su desplazamiento respecto al centro de su paso («fuera_…»: al lado de
    la etiqueta del paso)."""
    return {"izquierda": cx - 10 - ancho, "derecha": cx + 10, "fuera_izquierda": cx - ANCHO_ETIQUETA / 2 - 6 - ancho,
            "fuera_derecha": cx + ANCHO_ETIQUETA / 2 + 6}.get(desplazamiento, cx - ancho / 2)


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
        k = 2 if lado == "arriba" else 3
        if desplazamiento.startswith("fuera"):    # al lado de la etiqueta, desde el borde del paso
            e[k] = max(e[k], tam[next(p["tipo"] for p in proc["pasos"] if p["id"] == n["paso"])][1] / 2
                       + alto_nota(n.get("texto")))
        else:
            e[k] += NOTA_HUECO + alto_nota(n.get("texto"))
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
        if desplazamiento.startswith("fuera"):     # al lado de la etiqueta: pegada al borde del paso
            etiqueta = -NOTA_HUECO
        elif lado == geo.get("etiquetas", {}).get(n["paso"]):
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
