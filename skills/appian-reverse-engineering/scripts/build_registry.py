#!/usr/bin/env python3
"""build_registry.py - Registro único de hallazgos.

Uso:
  python3 scripts/build_registry.py <carpeta_salida>

Lee   <trabajo>/hallazgos/*.json      (un fichero por autor: lista de hallazgos)
      <trabajo>/modernizacion.json    (opcional, lo escribe rebuild-architect: MOD y PQ con los hallazgos que tratan)
Crea  <trabajo>/registro.json         (hallazgos validados, con su tratamiento)
      Rellena la tabla de 09-valor-adicional.md entre <!-- registro:inicio --> y <!-- registro:fin -->.

Cada hallazgo:
  {"id": "H-PRO-01", "titulo": "...", "area": "procesos", "severidad": "Alta|Media|Baja",
   "certeza": "verificado|inferido|pendiente", "objetos": ["..."], "documento": "08-procesos-bpmn/X.md#hallazgos",
   "evidencia": "mcp:processModel/X#nodes[id=1]", "impacto": "...", "recomendacion": "...",
   "duplicadoDe": "H-XXX-NN" (opcional)}

Salida: 0 sin errores, 1 con errores de validación (se listan), 2 uso.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rutas import work_dir  # noqa: E402

SEVERIDADES = ("Alta", "Media", "Baja")
CERTEZAS = {"verificado": "✅", "inferido": "🔵", "pendiente": "❓"}
AREAS = ("funcional", "arquitectura", "datos", "seguridad", "secretos", "integraciones", "apis", "procesos",
         "batches", "pantallas", "reglas", "mantenimiento", "rendimiento", "uso")
RE_ID = re.compile(r"^H-[A-Z]{2,4}-\d{2,3}$")
OBLIGATORIOS = ("id", "titulo", "area", "severidad", "certeza", "documento", "evidencia")
INICIO, FIN = "<!-- registro:inicio -->", "<!-- registro:fin -->"


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
        if h["area"] not in AREAS:
            avisos.append(f"{h['id']}: área '{h['area']}' fuera de la lista ({', '.join(AREAS)})")
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


def tratamiento(modern: dict) -> dict[str, list[str]]:
    trat: dict[str, list[str]] = {}
    for clave in ("mod", "pq"):
        for item in modern.get(clave, []) or []:
            for hid in item.get("hallazgos", []) or item.get("resuelve", []) or []:
                trat.setdefault(hid, []).append(item.get("id", "?"))
    return trat


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
    lineas = ["| ID | Hallazgo | Área | Severidad | Certeza | Dónde | Tratamiento |",
              "|---|---|---|---|---|---|---|"]
    for h in vivos:
        titulo = h["titulo"].replace("|", "/").strip()
        trat = ", ".join(h.get("tratamiento", [])) or "—"
        lineas.append(f"| {h['id']} | {titulo} | {h['area']} | {h['severidad']} | {CERTEZAS.get(h['certeza'], '?')} "
                      f"| [{etiqueta_doc(h['documento'])}](./{h['documento']}) | {trat} |")
    dup = [h for h in registro if h.get("duplicadoDe")]
    if dup:
        lineas.append("")
        lineas.append("Fusionados: " + ", ".join(f"{h['id']} → {h['duplicadoDe']}" for h in sorted(dup, key=lambda x: x["id"])) + ".")
    lineas.append("")
    lineas.append("Certeza: ✅ verificado en la definición · 🔵 inferido (se explica en el documento) · ❓ pendiente de validar.")
    return "\n".join(lineas)


def main(salida_dir: str) -> int:
    salida = Path(salida_dir).resolve()
    trabajo = work_dir(salida)
    carpeta = trabajo / "hallazgos"
    if not carpeta.exists():
        print(f"ERROR: no existe {carpeta}", file=sys.stderr)
        return 2
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
    modern_path = trabajo / "modernizacion.json"
    modern = json.loads(modern_path.read_text(encoding="utf-8")) if modern_path.exists() else {}
    trat = tratamiento(modern)
    ids = {h.get("id") for h in hallazgos}
    for hid in sorted(set(trat) - ids):
        avisos.append(f"modernizacion.json cita {hid}, que no está en el registro")
    for h in hallazgos:
        h["tratamiento"] = trat.get(h.get("id"), [])
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
                               for c in CERTEZAS},
                "veredicto": modern.get("veredicto"), "estrategia": modern.get("estrategia")}
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
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
