#!/usr/bin/env python3
"""build_registry.py - Registro único de hallazgos.

Uso:
  python3 <skill>/scripts/build_registry.py <carpeta_salida>

Lee   <trabajo>/hallazgos/*.json      (un fichero por autor: lista de hallazgos)
Crea  <trabajo>/registro.json         (hallazgos validados y sus recuentos por severidad y certeza)
      Rellena la tabla de 09-valor-adicional.md entre <!-- registro:inicio --> y <!-- registro:fin -->.

Cada hallazgo:
  {"id": "H-PRO-01", "titulo": "...", "area": "procesos", "severidad": "Alta|Media|Baja",
   "certeza": "verificado|inferido|pendiente", "objetos": ["..."], "documento": "08-procesos-bpmn/X.md#hallazgos",
   "evidencia": "mcp:processModel/X#nodes[id=1]", "impacto": "...", "duplicadoDe": "H-XXX-NN" (opcional),
   "base": ["mcp:…", "graph:…"] (las evidencias de las que sale; obligatoria con certeza inferido),
   "senal": "sin-ejecuciones" (opcional: la señal de la que sale, en minúsculas y con guiones)}
Un hallazgo dice qué pasa y qué riesgo tiene, no qué hacer: si trae «recomendacion», avisa. Un inferido sin «base» es
un error; uno de severidad Alta con menos de dos evidencias en «base», un aviso.
Un objeto, un problema, un hallazgo: dos hallazgos sin duplicadoDe que comparten un objeto y cuyas señales son del
mismo grupo (MISMO_PROBLEMA: huerfano y sin-ejecuciones; mas-50-nodos y aviso-validacion-nodos; o la misma señal)
son un error.

Salida: 0 sin errores, 1 con errores de validación (se listan), 2 uso.
"""
from __future__ import annotations

import json
import re
import sys
sys.dont_write_bytecode = True  # sin __pycache__ en el plugin: no se escribe fuera del proyecto
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rutas import work_dir  # noqa: E402

SEVERIDADES = ("Alta", "Media", "Baja")
CERTEZAS = {"verificado": "✅", "inferido": "🔶", "pendiente": "❓"}
AREAS = ("funcional", "arquitectura", "datos", "seguridad", "secretos", "integraciones", "apis", "procesos",
         "batches", "pantallas", "reglas", "mantenimiento", "rendimiento", "uso")
RE_ID = re.compile(r"^H-[A-Z]{2,4}-\d{2,3}$")
OBLIGATORIOS = ("id", "titulo", "area", "severidad", "certeza", "documento", "evidencia")
INICIO, FIN = "<!-- registro:inicio -->", "<!-- registro:fin -->"
RE_SENAL = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
# Señales que son el mismo problema de un objeto: un hallazgo por objeto (T27)
MISMO_PROBLEMA = (frozenset({"huerfano", "sin-ejecuciones"}), frozenset({"mas-50-nodos", "aviso-validacion-nodos"}))


def grupo(senal: str) -> frozenset:
    return next((g for g in MISMO_PROBLEMA if senal in g), frozenset({senal}))


def objeto(texto) -> str:
    """El nombre de un objeto como se cita en «objetos»: sin comillas invertidas ni «rule!»/«cons!» delante."""
    return re.sub(r"^(rule|cons)!", "", str(texto or "").strip().strip("`").strip())


def mismo_problema(hallazgos: list[dict], errores: list[str]) -> None:
    """Dos hallazgos vivos del mismo objeto con señales del mismo grupo dicen lo mismo: error, salvo duplicadoDe."""
    vivos = [h for h in hallazgos if not h.get("duplicadoDe") and isinstance(h.get("senal"), str)
             and RE_SENAL.match(h["senal"]) and isinstance(h.get("objetos"), list)]
    for i, a in enumerate(vivos):
        for b in vivos[i + 1:]:
            comunes = sorted({objeto(o) for o in a["objetos"]} & {objeto(o) for o in b["objetos"]})
            if comunes and grupo(a["senal"]) == grupo(b["senal"]):
                errores.append(f"{a.get('id')} y {b.get('id')} son el mismo problema de {', '.join(comunes)} "
                               f"({a['senal']}, {b['senal']}): un objeto, un problema, un hallazgo; fusiona uno en el "
                               "otro con duplicadoDe")


def cargar(path: Path, errores: list[str]) -> list:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as ex:  # noqa: BLE001
        errores.append(f"{path.name}: JSON no válido ({ex})")
        return []
    if not isinstance(data, list):
        errores.append(f"{path.name}: debe ser una lista de hallazgos")
        return []
    return data


def validar(hallazgos: list[dict], salida: Path, errores: list[str], avisos: list[str]) -> None:
    ids = {}
    for h in hallazgos:
        origen = h.get("_fichero", "?")
        falta = [k for k in OBLIGATORIOS if not str(h.get(k) or "").strip()]
        if falta:
            errores.append(f"{origen}: {h.get('id', '(sin id)')} sin {', '.join(falta)}")
            continue
        if not RE_ID.match(h["id"]):
            errores.append(f"{origen}: id '{h['id']}' no sigue H-<ÁREA>-NN")
        if h["id"] in ids:
            errores.append(f"{origen}: id '{h['id']}' repetido (también en {ids[h['id']]})")
        ids[h["id"]] = origen
        if h["severidad"] not in SEVERIDADES:
            errores.append(f"{h['id']}: severidad '{h['severidad']}' no es {'/'.join(SEVERIDADES)}")
        if h["certeza"] not in CERTEZAS:
            errores.append(f"{h['id']}: certeza '{h['certeza']}' no es {'/'.join(CERTEZAS)}")
        elif h["certeza"] == "inferido":
            base = h.get("base")
            if not (isinstance(base, list) and base and all(isinstance(b, str) and b.strip() for b in base)):
                errores.append(f"{h['id']}: inferido sin base: la lista de evidencias de las que sale")
            elif h["severidad"] == "Alta" and len(base) < 2:
                avisos.append(f"{h['id']}: inferido de severidad Alta con una sola evidencia en «base»: crúzalo con lo "
                              "que podría desmentirlo (contraevidencia) y añade a «base» lo que lo sostiene")
        if h["area"] not in AREAS:
            avisos.append(f"{h['id']}: área '{h['area']}' fuera de la lista ({', '.join(AREAS)})")
        if "senal" in h and not (isinstance(h["senal"], str) and RE_SENAL.match(h["senal"])):
            errores.append(f"{h['id']}: senal '{h['senal']}' no es una señal: minúsculas y guiones (huerfano, "
                           "sin-ejecuciones, mas-50-nodos…)")
        if str(h.get("recomendacion") or "").strip():
            avisos.append(f"{h['id']}: trae «recomendacion»; un hallazgo dice qué pasa y qué riesgo tiene, no qué hacer: "
                          "quítala del JSON y del documento")
        doc = h["documento"].split("#", 1)[0]
        if not (salida / doc).exists():
            errores.append(f"{h['id']}: el documento '{doc}' no existe en la salida")
    for h in hallazgos:
        d = h.get("duplicadoDe")
        if d:
            if d == h.get("id") or d not in ids:
                errores.append(f"{h.get('id')}: duplicadoDe '{d}' no existe")
            elif any(x.get("id") == d and x.get("duplicadoDe") for x in hallazgos):
                errores.append(f"{h.get('id')}: duplicadoDe apunta a otro duplicado ({d})")
    mismo_problema(hallazgos, errores)


# --------------------------------------------------------------------------- IDs estables al repetir

RE_NV = re.compile(r"^NV-[A-Z]{2,4}-\d{2,3}$")
RE_CITA = re.compile(r"\b(?:H|NV)-[A-Z]{2,4}-\d{2,3}\b")
SIN_RENOMBRAR = ("anexo", "extraccion")   # de <salida>: la definición original y la extracción no citan IDs


def _lista(p: Path) -> list[dict]:
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    d = d.get("hallazgos", d.get("sinVerificar")) if isinstance(d, dict) else d
    return [x for x in d if isinstance(x, dict)] if isinstance(d, list) else []


def _objetos(x: dict) -> frozenset:
    return frozenset(objeto(o) for o in (x.get("objetos") if isinstance(x.get("objetos"), list) else []))


def clave_h(h: dict):
    return (h.get("area"), _objetos(h), h.get("senal") or None)


def clave_nv(n: dict):
    return (str(n.get("id", "")).rsplit("-", 1)[0], _objetos(n))   # el área de un NV es su prefijo


def ids_estables(actuales: list[dict], previos: list[dict], clave, campo: str) -> dict[str, str]:
    """{ID actual: ID que se mantiene}, solo los que cambian. Cada actual conserva el ID anterior con su misma clave
    (área, objetos y señal): primero el suyo, si es la misma clave o el mismo `campo` (título o pregunta: el mismo
    hallazgo corregido); después el de otro anterior libre con su clave (si hay varios, el del mismo `campo`). Un
    actual sin anterior conserva su ID si no lo tuvo nadie; si no, el siguiente de su prefijo: un ID retirado no se
    reutiliza."""
    previo = {p["id"]: p for p in previos if p.get("id")}
    final: dict[str, str] = {}
    usados: set[str] = set()
    for h in actuales:
        p = previo.get(h["id"])
        if p and (clave(p) == clave(h) or (p.get(campo) and p.get(campo) == h.get(campo))):
            final[h["id"]] = h["id"]
            usados.add(h["id"])
    for h in sorted(actuales, key=lambda x: x["id"]):
        if h["id"] in final:
            continue
        libres = [p for i, p in sorted(previo.items()) if i not in usados and clave(p) == clave(h)]
        p = next((p for p in libres if p.get(campo) == h.get(campo)), libres[0] if libres else None)
        if p:
            final[h["id"]] = p["id"]
            usados.add(p["id"])
    ocupados = set(final.values()) | set(previo) | {h["id"] for h in actuales if h["id"] not in final}
    tomados = set(final.values())
    for h in sorted(actuales, key=lambda x: x["id"]):
        if h["id"] in final:
            continue
        if h["id"] not in previo and h["id"] not in tomados:
            final[h["id"]] = h["id"]
        else:
            prefijo = h["id"].rsplit("-", 1)[0]
            n = max(int(i.rsplit("-", 1)[1]) for i in ocupados | tomados if i.rsplit("-", 1)[0] == prefijo) + 1
            final[h["id"]] = f"{prefijo}-{n:02d}"
        tomados.add(final[h["id"]])
        ocupados.add(final[h["id"]])
    return {a: b for a, b in final.items() if a != b}


def mantener_ids(salida: Path, trabajo: Path) -> dict[str, str]:
    """Los cambios de ID que mantienen los del registro anterior (registro.json, o datos/hallazgos.json) y los NV de
    datos/sin-verificar.json al repetir la ingeniería inversa. Nada si los IDs actuales no son válidos o se repiten:
    eso lo dicen la validación y build_datos.py."""
    cambios: dict[str, str] = {}
    previos_h = _lista(trabajo / "registro.json") or _lista(salida / "datos" / "hallazgos.json")
    for actuales, previos, clave, campo, rx in (
            ([h for f in sorted((trabajo / "hallazgos").glob("*.json")) for h in _lista(f)], previos_h, clave_h,
             "titulo", RE_ID),
            ([n for f in sorted((trabajo / "sin-verificar").glob("*.json")) for n in _lista(f)],
             _lista(salida / "datos" / "sin-verificar.json"), clave_nv, "pregunta", RE_NV)):
        ids = [x.get("id") for x in actuales]
        if previos and ids and all(isinstance(i, str) and rx.match(i) for i in ids) and len(set(ids)) == len(ids):
            cambios.update(ids_estables(actuales, previos, clave, campo))
    return cambios


def renombra(salida: Path, trabajo: Path, cambios: dict[str, str]) -> None:
    """Cambia los IDs, de una pasada (sin cadenas: A→B y B→A se intercambian), en los JSON de hallazgos, sin verificar
    y procesos (entrada de los diagramas) y en los documentos de <salida>."""
    ficheros = [f for d in ("hallazgos", "sin-verificar", "procesos") for f in sorted((trabajo / d).glob("*.json"))]
    ficheros += [f for f in sorted(salida.rglob("*.md")) if f.relative_to(salida).parts[0] not in SIN_RENOMBRAR]
    for f in ficheros:
        texto = f.read_text(encoding="utf-8")
        nuevo = RE_CITA.sub(lambda m: cambios.get(m.group(0), m.group(0)), texto)
        if nuevo != texto:
            f.write_text(nuevo, encoding="utf-8")


def etiqueta_doc(doc: str) -> str:
    base = doc.split("#", 1)[0]
    nombre = Path(base).stem
    m = re.match(r"^(\d{2})-", nombre)
    if base.startswith("08-procesos-bpmn/"):
        return f"08 {nombre.replace('_', ' ')}"[:40]
    return m.group(1) if m else nombre


def tabla(registro: list[dict]) -> str:
    vivos = [h for h in registro if not h.get("duplicadoDe")]
    orden = {s: i for i, s in enumerate(SEVERIDADES)}
    vivos.sort(key=lambda h: (orden.get(h["severidad"], 9), h["id"]))
    lineas = ["| ID | Hallazgo | Área | Severidad | Certeza | Dónde |",
              "|---|---|---|---|---|---|"]
    for h in vivos:
        titulo = h["titulo"].replace("|", "/").strip()
        lineas.append(f"| {h['id']} | {titulo} | {h['area']} | {h['severidad']} | {CERTEZAS.get(h['certeza'], '?')} "
                      f"| [{etiqueta_doc(h['documento'])}](./{h['documento']}) |")
    dup = [h for h in registro if h.get("duplicadoDe")]
    if dup:
        lineas.append("")
        lineas.append("Fusionados: " + ", ".join(f"{h['id']} → {h['duplicadoDe']}" for h in sorted(dup, key=lambda x: x["id"])) + ".")
    lineas.append("")
    lineas.append("Certeza: ✅ verificado en la definición · 🔶 inferido (se explica en el documento) · ❓ pendiente de validar.")
    return "\n".join(lineas)


def main(salida_dir: str) -> int:
    salida = Path(salida_dir).resolve()
    trabajo = work_dir(salida)
    carpeta = trabajo / "hallazgos"
    if not carpeta.exists():
        print(f"ERROR: no existe {carpeta}", file=sys.stderr)
        return 2
    cambios = mantener_ids(salida, trabajo)
    if cambios:
        renombra(salida, trabajo, cambios)
        print("IDs que se mantienen del registro anterior: " + ", ".join(f"{a} → {b}" for a, b in sorted(cambios.items()))
              + " (cambiados en los JSON de hallazgos, sin verificar y procesos y en los documentos; si un diagrama de "
                "08 cita uno, vuelve a pasar diagrama.py actualizar)")
    errores: list[str] = []
    avisos: list[str] = []
    hallazgos: list[dict] = []
    for f in sorted(carpeta.glob("*.json")):
        for h in cargar(f, errores):
            if isinstance(h, dict):
                h["_fichero"] = f.name
                hallazgos.append(h)
            else:
                errores.append(f"{f.name}: cada hallazgo debe ser un objeto")
    validar(hallazgos, salida, errores, avisos)
    for h in hallazgos:
        h.pop("_fichero", None)
    for a in avisos:
        print(f"AVISO: {a}", file=sys.stderr)
    if errores:
        for e in errores:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1
    registro = {"hallazgos": hallazgos,
                "porSeveridad": {s: sum(1 for h in hallazgos if h["severidad"] == s and not h.get("duplicadoDe"))
                                 for s in SEVERIDADES},
                "porCerteza": {c: sum(1 for h in hallazgos if h["certeza"] == c and not h.get("duplicadoDe"))
                               for c in CERTEZAS}}
    (trabajo / "registro.json").write_text(json.dumps(registro, ensure_ascii=False, indent=2), encoding="utf-8")
    doc09 = salida / "09-valor-adicional.md"
    if doc09.exists():
        texto = doc09.read_text(encoding="utf-8")
        if INICIO in texto and FIN in texto:
            antes, resto = texto.split(INICIO, 1)
            _, despues = resto.split(FIN, 1)
            doc09.write_text(f"{antes}{INICIO}\n{tabla(hallazgos)}\n{FIN}{despues}", encoding="utf-8")
            print(f"09-valor-adicional.md: registro con {sum(1 for h in hallazgos if not h.get('duplicadoDe'))} hallazgos")
        else:
            print("AVISO: 09-valor-adicional.md no tiene los marcadores del registro", file=sys.stderr)
    print(f"registro.json: {len(hallazgos)} hallazgos {registro['porSeveridad']} {registro['porCerteza']}")
    return 0


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):  # consolas de Windows sin UTF-8: «→» o «✓» no caben en cp1252
        _s.reconfigure(encoding="utf-8", errors="replace")
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
