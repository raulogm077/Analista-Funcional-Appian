#!/usr/bin/env python3
"""build_datos.py - <salida>/datos/: lo que las demás skills leen de la ingeniería inversa.

Uso:
  python3 <skill>/scripts/build_datos.py <carpeta_salida>

Lee   <trabajo>/inventory.json, graph.json, registro.json, sin-verificar/*.json y la definición de cada record type
Crea  <salida>/datos/inventario.json, dependencias.json, hallazgos.json, procesos.json y sin-verificar.json (formato
      en references/datos.md). Las demás skills leen estos ficheros, nunca <trabajo>/.
      Rellena la tabla «Sin verificar» de LEEME.md entre <!-- sin-verificar:inicio --> y <!-- sin-verificar:fin -->.

Lo que no se pudo verificar (NV), un fichero por autor en <trabajo>/sin-verificar/<agente>.json, una lista:
  {"id": "NV-ARQ-01", "pregunta", "porQue", "queHaceFalta", "aQuien", "dondeSeBusco", "objetos": [], "indicios",
   "estado": "abierto|parcial|resuelto", "documento": "02-arquitectura.md#…", "duplicadoDe": "NV-…" (opcional)}
Se validan como los hallazgos en build_registry.py: con un id, un estado o un queHaceFalta fuera de formato, no se
escribe nada.
Solo librería estándar. Salida: 0 bien, 1 con NV fuera de formato (se listan), 2 uso o falta el inventario.
"""
from __future__ import annotations

import json
import re
import sys
sys.dont_write_bytecode = True  # sin __pycache__ en el plugin: no se escribe fuera del proyecto
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_model import find_list, load, pick, unwrap  # noqa: E402
from rutas import work_dir  # noqa: E402

CAMPOS_HALLAZGO = ("id", "titulo", "area", "severidad", "certeza", "objetos", "documento", "evidencia")
CAMPOS_NV = ("id", "pregunta", "porQue", "queHaceFalta", "aQuien", "dondeSeBusco", "objetos", "indicios", "estado",
             "documento")
OBLIGATORIOS_NV = ("id", "pregunta", "porQue", "queHaceFalta", "aQuien", "dondeSeBusco", "estado", "documento")
RE_NV = re.compile(r"^NV-[A-Z]{2,4}-\d{2,3}$")
ESTADOS_NV = ("abierto", "parcial", "resuelto")
HACE_FALTA = re.compile(r"(?i)(acceso|export|permiso|entorno|negocio)")   # por dónde empieza «queHaceFalta»
LEEME = ("<!-- sin-verificar:inicio -->", "<!-- sin-verificar:fin -->")


class NoValido(ValueError):
    """Hay NV fuera de formato: `errores` dice cuáles y por qué."""

    def __init__(self, errores: list[str]):
        super().__init__("; ".join(errores))
        self.errores = errores


def _json(p: Path) -> dict:
    return load(p) if p.exists() else {}


def _nombres(lista: list, claves: tuple[str, ...]) -> list[str]:
    return [n for n in (pick(x, claves) for x in lista) if n]


def tambien(o: dict, trabajo: Path) -> list[str]:
    """Lo que se cita con un record type sin ser un objeto: su tabla, vistas, campos, relaciones y acciones."""
    if o.get("type") != "recordType":
        return []
    out = [o["tableName"]] if o.get("tableName") else []
    if o.get("detail") == "full" and o.get("path"):
        try:
            d = unwrap(load(trabajo / o["path"]).get("response"))
        except (OSError, ValueError, AttributeError):
            d = None
        if d is not None:
            out += _nombres(find_list(d, ("views",)), ("name", "viewName", "label", "displayName"))
            out += _nombres(find_list(d, ("fields",)), ("fieldName", "name"))
            out += _nombres(find_list(d, ("relationships",)), ("relationshipName", "name"))
            out += _nombres(find_list(d, ("actions",)), ("displayName", "name", "key"))
    return list(dict.fromkeys(out))


def _relativa(salida: Path, rel: str) -> str | None:
    return rel if (salida / rel).is_file() else None


def sin_verificar(salida: Path, trabajo: Path) -> list[dict]:
    """Los NV de <trabajo>/sin-verificar/, validados (NoValido si alguno está fuera de formato), sin duplicados y
    ordenados por id, con los campos de CAMPOS_NV."""
    errores: list[str] = []
    nvs: list[tuple[str, dict]] = []
    for f in sorted((trabajo / "sin-verificar").glob("*.json")):
        try:
            lista = json.loads(f.read_text(encoding="utf-8"))
        except ValueError as ex:
            errores.append(f"{f.name}: JSON no válido ({ex})")
            continue
        if not isinstance(lista, list):
            errores.append(f"{f.name}: debe ser una lista de NV")
            continue
        for n in lista:
            if isinstance(n, dict):
                nvs.append((f.name, n))
            else:
                errores.append(f"{f.name}: cada NV debe ser un objeto")
    ids: dict[str, str] = {}
    for origen, n in nvs:
        falta = [k for k in OBLIGATORIOS_NV if not str(n.get(k) or "").strip()]
        if falta:
            errores.append(f"{origen}: {n.get('id', '(sin id)')} sin {', '.join(falta)}")
            continue
        if not RE_NV.match(n["id"]):
            errores.append(f"{origen}: id '{n['id']}' no sigue NV-<ÁREA>-NN, con el prefijo de área de los hallazgos")
        if n["id"] in ids:
            errores.append(f"{origen}: id '{n['id']}' repetido (también en {ids[n['id']]})")
        ids[n["id"]] = origen
        if n["estado"] not in ESTADOS_NV:
            errores.append(f"{n['id']}: estado '{n['estado']}' no es {'/'.join(ESTADOS_NV)}")
        if not HACE_FALTA.match(n["queHaceFalta"].strip()):
            errores.append(f"{n['id']}: queHaceFalta no empieza por acceso, export, permiso, entorno o negocio")
        if not isinstance(n.get("objetos", []), list):
            errores.append(f"{n['id']}: objetos debe ser una lista de nombres")
        if not (salida / n["documento"].split("#", 1)[0]).is_file():
            errores.append(f"{n['id']}: el documento '{n['documento'].split('#', 1)[0]}' no existe en la salida")
    for _, n in nvs:
        d = n.get("duplicadoDe")
        if d and (d == n.get("id") or d not in ids):
            errores.append(f"{n.get('id')}: duplicadoDe '{d}' no existe")
        elif d and any(x.get("id") == d and x.get("duplicadoDe") for _, x in nvs):
            errores.append(f"{n.get('id')}: duplicadoDe apunta a otro duplicado ({d})")
    if errores:
        raise NoValido(errores)
    vivos = [n for _, n in nvs if not n.get("duplicadoDe")]
    return sorted(({k: n.get(k, [] if k == "objetos" else None) for k in CAMPOS_NV} for n in vivos),
                  key=lambda n: n["id"])


def fuera_de_la_aplicacion(grafo: dict, nombre: dict, nvs: list[dict]) -> list[dict]:
    """Los nodos externos del grafo: quién de la aplicación los usa, a quién usan y el NV que los tiene en objetos."""
    externos = {n["id"]: n for n in grafo.get("nodes", []) if n.get("external")}
    usado_por, usa = defaultdict(set), defaultdict(set)
    for e in grafo.get("edges", []):
        if e.get("target") in externos and nombre.get(e.get("source")):
            usado_por[e["target"]].add(nombre[e["source"]])
        if e.get("source") in externos and nombre.get(e.get("target")):
            usa[e["source"]].add(nombre[e["target"]])
    nv_de: dict[str, str] = {}
    for n in nvs:
        for o in n.get("objetos") or []:
            nv_de.setdefault(o, n["id"])
    fuera = [{"nombre": n.get("name") or i, "tipo": n.get("type"), "usadoPor": sorted(usado_por[i]),
              "usa": sorted(usa[i]), "nv": nv_de.get(n.get("name") or i)} for i, n in externos.items()]
    return sorted(fuera, key=lambda f: str(f["nombre"]).lower())


def _celda(texto) -> str:
    return " ".join(str(texto or "").replace("|", "/").split())


def tabla_sin_verificar(nvs: list[dict]) -> str:
    if not nvs:
        return "Ninguna pregunta quedó sin verificar."
    filas = ["| ID | Pregunta | Qué hace falta | A quién | Estado |", "|---|---|---|---|---|"]
    filas += [f"| [{n['id']}](./{n['documento']}) | {_celda(n['pregunta'])} | {_celda(n['queHaceFalta'])} "
              f"| {_celda(n['aQuien'])} | {n['estado'].capitalize()} |" for n in nvs]
    return "\n".join(filas)


def rellena_leeme(salida: Path, nvs: list[dict]) -> None:
    """La tabla «Sin verificar» de LEEME.md, entre sus marcadores. Sin LEEME todavía, nada."""
    leeme = salida / "LEEME.md"
    if not leeme.exists():
        return
    texto = leeme.read_text(encoding="utf-8")
    if LEEME[0] not in texto or LEEME[1] not in texto:
        print("AVISO: LEEME.md no tiene los marcadores de «Sin verificar»", file=sys.stderr)
        return
    antes, resto = texto.split(LEEME[0], 1)
    _, despues = resto.split(LEEME[1], 1)
    leeme.write_text(f"{antes}{LEEME[0]}\n{tabla_sin_verificar(nvs)}\n{LEEME[1]}{despues}", encoding="utf-8")


def construir(salida: Path) -> dict:
    """Escribe los cinco ficheros de <salida>/datos/ y la tabla «Sin verificar» de LEEME, y devuelve los ficheros
    ({nombre del fichero: contenido}). Con un NV fuera de formato lanza NoValido sin escribir nada."""
    salida = Path(salida).resolve()
    trabajo = work_dir(salida)
    nvs = sin_verificar(salida, trabajo)
    inv = load(trabajo / "inventory.json")
    por_tipo = inv.get("objects", {})
    app = (por_tipo.get("application") or [{}])[0]
    objs = [o for t, lista in por_tipo.items() if t != "application" for o in lista]
    nombre = {o["uuid"]: o.get("name") for o in objs + [app] if o.get("uuid")}
    grafo = _json(trabajo / "graph.json")

    inventario = {
        "aplicacion": {"nombre": app.get("name"), "prefijo": app.get("prefix"), "uuid": app.get("uuid")},
        "objetos": sorted(({"nombre": o.get("name"), "tipo": o["type"], "uuid": o.get("uuid"),
                            "anexo": _relativa(salida, f"anexo/{o['type']}/{o['slug']}.md") if o.get("slug") else None,
                            "tambien": tambien(o, trabajo)} for o in objs),
                          key=lambda x: (x["tipo"], str(x["nombre"]).lower())),
    }
    aristas = [{"de": nombre[e["source"]], "a": nombre[e["target"]],
                "donde": " · ".join(e.get("evidence") or []) or e.get("refType")}
               for e in grafo.get("edges", [])
               if nombre.get(e.get("source")) and nombre.get(e.get("target"))]
    hallazgos = []
    for h in _json(trabajo / "registro.json").get("hallazgos", []):
        if h.get("duplicadoDe"):
            continue
        hallazgos.append({k: h.get(k, [] if k == "objetos" else None) for k in CAMPOS_HALLAZGO})
        if h.get("certeza") == "inferido":
            hallazgos[-1]["base"] = list(h.get("base") or [])
    procesos = [{"nombre": o.get("name"),
                 "json": _relativa(salida, f"08-procesos-bpmn/{o['slug']}.json") if o.get("slug") else None,
                 "nodos": o.get("nodeCount"), "ejecuciones": (o.get("usage") or {}).get("executions")}
                for o in por_tipo.get("processModel", [])]
    datos = {"inventario.json": inventario,
             "dependencias.json": {"aristas": sorted(aristas, key=lambda a: (a["de"], a["a"], a["donde"] or "")),
                                   "fueraDeLaAplicacion": fuera_de_la_aplicacion(grafo, nombre, nvs)},
             "hallazgos.json": {"hallazgos": sorted(hallazgos, key=lambda h: h["id"] or "")},
             "procesos.json": {"procesos": sorted(procesos, key=lambda p: str(p["nombre"]).lower())},
             "sin-verificar.json": {"sinVerificar": nvs}}
    carpeta = salida / "datos"
    carpeta.mkdir(parents=True, exist_ok=True)
    for fichero, contenido in datos.items():
        (carpeta / fichero).write_text(json.dumps(contenido, ensure_ascii=False, indent=1), encoding="utf-8")
    rellena_leeme(salida, nvs)
    return datos


def main(salida_dir: str) -> int:
    salida = Path(salida_dir).resolve()
    if not (work_dir(salida) / "inventory.json").exists():
        print(f"ERROR: falta {work_dir(salida) / 'inventory.json'} (ejecuta antes build_model.py)", file=sys.stderr)
        return 2
    try:
        d = construir(salida)
    except NoValido as ex:
        for e in ex.errores:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1
    print(f"datos/: {len(d['inventario.json']['objetos'])} objetos, {len(d['dependencias.json']['aristas'])} aristas, "
          f"{len(d['dependencias.json']['fueraDeLaAplicacion'])} fuera de la aplicación, "
          f"{len(d['hallazgos.json']['hallazgos'])} hallazgos, {len(d['procesos.json']['procesos'])} procesos, "
          f"{len(d['sin-verificar.json']['sinVerificar'])} sin verificar")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
