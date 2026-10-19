#!/usr/bin/env python3
"""Genera INVENTARIO.md y la tabla de huérfanos de 09 desde la extracción.

Uso: python3 build_inventario.py <salida>
Conserva las celdas interpretativas (Nombre enlazado, Para qué y Pantalla) por uuid y el texto fuera de los
marcadores. No sustituye documentos antiguos sin marcadores: primero delimita sus tablas según la plantilla.
No deduce para qué sirve un objeto sin descripción: lo indica para que el analista complete esa celda.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
sys.dont_write_bytecode = True
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rutas import escribe, work_dir  # noqa: E402
from build_model import localized  # noqa: E402

MARCAS = ("<!-- inventario:inicio -->", "<!-- inventario:fin -->")
HUERFANOS = ("<!-- huerfanos:inicio -->", "<!-- huerfanos:fin -->")
PROPIETARIO = {"recordType": "03-modelo-datos.md", "cdt": "03-modelo-datos.md", "dataStore": "03-modelo-datos.md",
               "group": "04-seguridad-grupos.md", "integration": "05-integraciones-consumidas.md",
               "connectedSystem": "05-integraciones-consumidas.md", "webApi": "06-apis-expuestas.md"}
TITULOS = {"recordType": "Record types", "cdt": "CDTs", "processModel": "Process models", "interface": "Interfaces",
           "expressionRule": "Expression rules", "decision": "Decisiones", "integration": "Integraciones",
           "connectedSystem": "Connected systems", "webApi": "Web APIs", "group": "Grupos", "constant": "Constantes",
           "site": "Sites", "dataStore": "Data stores"}
EXTRAS = {"recordType": ("Origen", "Tabla", "Campos", "Filas"),
          "processModel": ("Inicio", "Nodos", "Tareas humanas", "Ejecuciones"),
          "interface": ("Pantalla", "Líneas", "Avisos de validación"),
          "expressionRule": ("Líneas", "Referencias"),
          "integration": ("Método", "Endpoint", "Connected system", "Modifica datos"),
          "connectedSystem": ("Tipo", "URL base", "Autenticación"), "webApi": ("Método", "Endpoint"),
          "site": ("URL", "Páginas"), "group": ("Tipo", "Grupo padre", "Grupos miembro", "Usuarios directos"),
          "constant": ("Tipo", "Valor", "Referencia")}


def carga(p):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def celda(v):
    if v is None or v == "":
        return "—"
    return str(v).replace("|", "&#124;").replace("\r", " ").replace("\n", " ")


def tabla(cabecera, filas):
    return "\n".join(["| " + " | ".join(cabecera) + " |", "|" + "---|" * len(cabecera),
                      *("| " + " | ".join(celda(v) for v in fila) + " |" for fila in filas)])


def anteriores(texto):
    """Solo aportes de personas; los datos mecánicos se vuelven a leer de la extracción."""
    out, cabecera = {}, []
    for linea in texto.splitlines():
        if not linea.startswith("|"):
            cabecera = []
            continue
        c = [v.strip() for v in linea.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-+:?", v) for v in c):
            continue
        if "uuid" in c:
            cabecera = c
        elif cabecera and len(c) == len(cabecera):
            fila = dict(zip(cabecera, c))
            uuid = fila["uuid"].strip("`")
            out[uuid] = {k: fila[k] for k in ("Nombre", "Para qué", "Pantalla") if k in fila}
    return out


def sustituye(texto, marcas, contenido):
    inicio, fin = marcas
    if texto.count(inicio) != 1 or texto.count(fin) != 1 or texto.index(inicio) >= texto.index(fin):
        raise ValueError(f"Faltan o se repiten los marcadores {inicio} / {fin}; no se sustituye contenido ajeno. "
                         "Delimita únicamente las tablas generadas según la plantilla, dejando la prosa fuera, "
                         "o usa --borrador para obtener ficheros aparte y comparar antes de migrar.")
    a, b = texto.index(inicio) + len(inicio), texto.index(fin)
    return texto[:a] + "\n\n" + contenido + "\n\n" + texto[b:]


def ficha(o, salida):
    ruta = f"anexo/{o['type']}/{o.get('slug', '')}.md"
    return f"[anexo](./{ruta})" if (salida / ruta).exists() else "—"


def sin_definicion(o, salida):
    fallidas = [f for f in o.get("files", []) if f.get("role") == "definition" and not f.get("ok")]
    if fallidas:
        errores = []
        for f in fallidas:
            respuesta = carga(work_dir(salida) / f["path"]) if f.get("path") else {}
            errores.append(f"{f.get('tool')}: {(respuesta.get('_meta') or {}).get('error') or 'la llamada falló'}")
        return "; ".join(errores)[:100]
    return "No se obtuvo respuesta de definición; consulta las herramientas omitidas."


def generar(salida, inv, grafo, report, previo):
    objetos = [o for t, ls in inv["objects"].items() if t != "application" for o in ls]
    app = inv["objects"].get("application", [{}])[0]
    refs = Counter(e["target"] for e in grafo.get("edges", []))
    volumen = {o["uuid"]: o.get("count") for o in carga(work_dir(salida) / "datafabric.json").get("recordTypes", [])}
    disenados = [o for o in objetos if o["type"] not in ("folder", "processModelFolder", "knowledgeCenter")]
    definidos = sum(o.get("detail") == "full" for o in disenados)
    cobertura = definidos / len(disenados) if disenados else 0
    conteos = Counter(o["type"] for o in objetos)
    principales = ("processModel", "interface", "expressionRule", "recordType")
    partes = [f"> **TL;DR**: {len(objetos)} objetos de {len({o['type'] for o in objetos})} tipos; "
              f"{definidos} de {len(disenados)} ({cobertura:.0%}, sin contar carpetas) con definición.",
              f"> **Volumen**: {conteos['processModel']} process models · {conteos['interface']} interfaces · "
              f"{conteos['expressionRule']} reglas · {conteos['recordType']} record types · "
              f"{sum(v for t, v in conteos.items() if t not in principales)} otros.",
              f"**Aplicación:** {celda(app.get('name'))} (prefijo `{celda(app.get('prefix'))}`, "
              f"uuid `{celda(app.get('uuid'))}`)", "## Conteo por tipo"]
    grupos = [(t, ls) for t, ls in sorted(inv["objects"].items()) if t != "application"]
    partes.append(tabla(["Tipo", "Objetos", "Con definición", "Sin definición"],
                        [(t, len(ls), sum(o.get("detail") == "full" for o in ls),
                          sum(o.get("detail") != "full" for o in ls)) for t, ls in grupos]))
    faltan = []
    for tipo, lista in grupos:
        extra = EXTRAS.get(tipo, ("Referencias",))
        cab = ["Nombre", "uuid", *extra, "Para qué", "Ficha"]
        filas = []
        for o in sorted(lista, key=lambda o: (o.get("name", ""), o["uuid"])):
            guardado = previo.get(o["uuid"], {})
            nombre = f"`{celda(o.get('name'))}`"
            destino = f"08-procesos-bpmn/{o['slug']}.md" if tipo == "processModel" else PROPIETARIO.get(tipo)
            if destino and (salida / destino).exists():
                nombre = f"[{nombre}](./{destino})"
            enlace = re.fullmatch(r"\[.*\]\((.+)\)", guardado.get("Nombre", ""))
            if enlace:
                nombre = f"[`{celda(o.get('name'))}`]({enlace[1]})"
            desc = localized(o.get("description"))
            para = guardado.get("Para qué", "—")
            if para in ("—", "") or "{{" in para:
                para = celda(desc)[:100] if isinstance(desc, str) and desc else "—"
            if para == "—":
                faltan.append(o.get("name", o["uuid"]))
            vals = {"Origen": o.get("sourceType"), "Tabla": o.get("tableName"), "Campos": o.get("fieldCount"),
                    "Filas": volumen.get(o["uuid"]), "Inicio": o.get("startType"), "Nodos": o.get("nodeCount"),
                    "Tareas humanas": o.get("userTaskCount"), "Ejecuciones": (o.get("usage") or {}).get("executions"),
                    "Pantalla": guardado.get("Pantalla"), "Líneas": o.get("sailLines"),
                    "Avisos de validación": len(o["validationIssues"]) if "validationIssues" in o else None,
                    "Referencias": refs[o["uuid"]],
                    "Método": o.get("method"), "Endpoint": o.get("endpoint"),
                    "Connected system": o.get("connectedSystemRef"), "Modifica datos": o.get("modifiesData"),
                    "Tipo": o.get("csType") or o.get("groupType") or o.get("typeRef"),
                    "URL base": o.get("baseUrl"), "Autenticación": o.get("authType"),
                    "URL": f"/sites/{o['urlStub']}" if o.get("urlStub") else None,
                    "Páginas": o.get("pageCount"), "Grupo padre": o.get("parentGroup"),
                    "Grupos miembro": ", ".join(x for x in o.get("memberGroups", []) if x),
                    "Usuarios directos": o.get("userCount"), "Valor": o.get("value"), "Referencia": o.get("valueRef")}
            if tipo == "webApi":
                vals["Endpoint"] = f"/suite/webapi/{o['endpointPath']}" if o.get("endpointPath") else None
            filas.append([nombre, f"`{o['uuid']}`", *(vals.get(k) for k in extra), para, ficha(o, salida)])
        partes += ["## " + TITULOS.get(tipo, tipo), tabla(cab, filas)]
    preflight = carga(work_dir(salida) / "preflight.json")
    usadas, omitidas = report.get("toolsUsed", []), report.get("toolsOmitted", [])
    partes += ["## Cobertura de la extracción", tabla(["Métrica", "Valor"], [
               ("Objetos de la aplicación", len(objetos)),
               ("Con definición", sum(o.get("detail") == "full" for o in objetos)),
               ("Herramientas del Dev MCP", f"{len(usadas) + len(omitidas)}: {len(usadas)} usadas y {len(omitidas)} omitidas"),
               ("Llamadas con error", report.get("errorCount")),
               ("Appian MCP Server (volúmenes)", (preflight.get("appianMcpServer") or {}).get("status")),
               ("Docs MCP (documentación oficial)", (preflight.get("docsMcp") or {}).get("status"))]),
               "### Herramientas usadas",
               tabla(["Herramienta", "Detalle"], [(t.get("tool") or t.get("name"), celda(t.get("role") or t.get("calls")))
                      if isinstance(t, dict) else (t, "—") for t in report.get("toolsUsed", [])]),
               "### Herramientas omitidas",
               tabla(["Herramienta", "Motivo"], [(t.get("tool") or t.get("name"), t.get("reason"))
                      for t in report.get("toolsOmitted", [])] +
                     [(t.get("tool"), f"Desactivada para {t.get('type')}: {t.get('reason')}")
                      for t in report.get("disabledAfterProbe", [])]),
               "### Objetos sin definición", tabla(["Objeto", "Tipo", "Motivo"],
                    [(o.get("name"), o["type"], sin_definicion(o, salida))
                     for o in objetos if o.get("detail") != "full"])]
    huerfanos = set(grafo.get("orphans", []))
    # En producción también figuran los procesos sin ejecuciones, como establece la plantilla de 09.
    if (preflight.get("environment") or {}).get("isProduction") is True:
        huerfanos.update(o["uuid"] for o in objetos if o["type"] == "processModel" and
                        (o.get("usage") or {}).get("executions") == 0)
    h = tabla(["Objeto", "Tipo", "Última modificación", "Ejecuciones", "Ficha"],
              [(f"`{celda(o.get('name'))}`", o["type"], (o.get("versions") or {}).get("lastModifiedOn"),
                (o.get("usage") or {}).get("executions"), ficha(o, salida))
               for o in objetos if o["uuid"] in huerfanos])
    return "\n\n".join(partes), h, faltan


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("salida", type=Path)
    parser.add_argument("--borrador", action="store_true", help="crea INVENTARIO.borrador.md y huerfanos.borrador.md; no toca los documentos")
    args = parser.parse_args(argv)
    salida = args.salida.resolve()
    try:
        trabajo = work_dir(salida)
        inv = carga(trabajo / "inventory.json")
        if not inv.get("objects"):
            raise ValueError("Falta inventory.json: ejecuta build_model.py.")
        destino = salida / "INVENTARIO.md"
        texto = destino.read_text(encoding="utf-8") if destino.exists() else (
            "# Inventario de la aplicación\n\n> **Responde a:** ¿Qué objetos tiene la aplicación, para qué sirven "
            "y qué definición se obtuvo?\n\n" + "\n\n".join(MARCAS) + "\n")
        contenido, huerfanos, faltan = generar(salida, inv, carga(trabajo / "graph.json"),
                                              carga(trabajo / "extraction_report.json"), anteriores(texto))
        if args.borrador:
            borradores = [salida / "INVENTARIO.borrador.md", salida / "huerfanos.borrador.md"]
            if any(p.exists() for p in borradores):
                raise ValueError("Ya existe un borrador: revísalo y muévelo antes de generar otro.")
            escribe(borradores[0], "# Inventario de la aplicación\n\n" + MARCAS[0] + "\n\n" + contenido + "\n\n" + MARCAS[1] + "\n")
            escribe(borradores[1], HUERFANOS[0] + "\n\n" + huerfanos + "\n\n" + HUERFANOS[1] + "\n")
            print("Borradores creados para comparar; los documentos originales siguen intactos.")
            return 0
        cambios = [(destino, sustituye(texto, MARCAS, contenido))]
        nueve = salida / "09-valor-adicional.md"
        if nueve.exists():
            cambios.append((nueve, sustituye(nueve.read_text(encoding="utf-8"), HUERFANOS, huerfanos)))
        # Valida ambos destinos antes de escribir ninguno.
        for p, nuevo in cambios:
            escribe(p, nuevo)
        print(f"Inventario: {sum(len(v) for k, v in inv['objects'].items() if k != 'application')} objetos.")
        if not nueve.exists():
            print("Tabla de huérfanos pendiente: aún no existe 09-valor-adicional.md; repite después de redactarlo.")
        if faltan:
            print("Completa «Para qué» desde la definición (🔶): " + ", ".join(faltan))
        return 0
    except (OSError, ValueError, KeyError) as e:
        print(str(e), file=sys.stderr)
        return 2


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
