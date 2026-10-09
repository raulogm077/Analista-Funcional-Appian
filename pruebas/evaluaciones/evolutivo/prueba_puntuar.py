#!/usr/bin/env python3
"""Prueba de puntuar.py con proyectos inventados: `python3 prueba_puntuar.py`. Sale 0 si todo va bien.

Primero comprueba el propio caso: cada objeto de lo esperado (salvo los «(nuevo) …») es de la aplicación ficticia MNT
del simulador (`MOCK_APP=fixture_mal_hecha`) y cada «(nuevo) <tipo>: …» trae un tipo que puntuar.py conoce. Después monta
proyectos con el análisis de ejemplo del analista (datos/autorizaciones, que pasa comprobar.py) y un técnico §13
inventado, y mira la salida de puntuar.py."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
AQUI = Path(__file__).resolve().parent
PRUEBAS = AQUI.parents[1]
PUNTUAR = AQUI / "puntuar.py"
EJEMPLO = PRUEBAS / "appian-functional-analyst" / "datos" / "autorizaciones"
VISIBLE = json.loads((AQUI / "esperado.json").read_text(encoding="utf-8"))
OCULTO = json.loads((AQUI / "ocultas" / "esperado.json").read_text(encoding="utf-8"))
sys.path.insert(0, str(PRUEBAS / "appian-reverse-engineering" / "mock_devmcp"))
import fixture_mal_hecha  # noqa: E402

MNT = set(fixture_mal_hecha.build()[2].values())
TIPO = {"MNT Orden": "Record type", "MNT Técnico": "Record type", "MNT_PM_GestionOrden": "Process model",
        "MNT_WS_EstadoOrden": "Web API"}
NUEVOS = {"proceso": ("MNT_PM_CorregirOrden", "MNT_PM_BajaTecnico"), "interfaz": ("MNT_IF_ValorarTrabajo",)}


def filas_bien(esperado: dict) -> list[tuple]:
    """(objeto, tipo, situación, sustituye a) que resuelven lo esperado con su primera situación."""
    filas, usados = [], {}
    for clave, valen in esperado.items():
        m = re.match(r"\(nuevo\)\s*([^:]+):", clave)
        if m:
            tipo = m.group(1).strip()
            k = usados.get(tipo, 0)
            usados[tipo] = k + 1
            filas.append((NUEVOS[tipo][k], tipo.capitalize(), "Nuevo", "—"))
        else:
            filas.append((clave, TIPO.get(clave, "Interfaz"), valen[0], "—"))
    return filas


def tecnico(filas) -> str:
    """El técnico del ejemplo con §13 como tabla del plan de construcción de un evolutivo."""
    t = (EJEMPLO / "analisis" / "tecnico.md").read_text(encoding="utf-8")
    tabla = ("## 13. Plan de construcción\n\n| Paso | Objeto | Tipo | Situación | Sustituye a |\n|---|---|---|---|---|\n"
             + "\n".join(f"| {k} | `{o}` | {ti} | {s} | {su} |" for k, (o, ti, s, su) in enumerate(filas, 1)) + "\n\n")
    return re.sub(r"(?ms)^## 13\. .*?(?=^## 14\.)", lambda _: tabla, t)


def proyecto(raiz: Path, filas, inventario=False, roto=False) -> Path:
    p = raiz / f"Carpeta con espacios {len(list(raiz.iterdir())) + 1}" / "Gestión app"
    shutil.copytree(EJEMPLO / "analisis", p / "analisis")
    (p / "analisis" / "tecnico.md").write_text(tecnico(filas), encoding="utf-8")
    if roto:
        f = p / "analisis" / "funcional.md"
        f.write_text(f.read_text(encoding="utf-8").replace("## 2. Perfiles", "Perfiles"), encoding="utf-8")
    if inventario:
        datos = p / "as-is" / "datos"
        datos.mkdir(parents=True)
        (datos / "inventario.json").write_text(json.dumps({"objetos": [{"nombre": n} for n in sorted(MNT)]},
                                                          ensure_ascii=False), encoding="utf-8")
    return p


def corre(p: Path, *extra) -> tuple[int, str]:
    r = subprocess.run([sys.executable, str(PUNTUAR), str(p), *extra], capture_output=True, text=True, encoding="utf-8")
    return r.returncode, r.stdout + r.stderr


def main() -> int:
    fallos = 0
    sys.path.insert(0, str(AQUI))
    import puntuar  # noqa: E402  (para TIPOS)
    mal = [c for c in {**VISIBLE, **OCULTO} if not c.startswith("(nuevo)") and c not in MNT]
    mal += [c for c in {**VISIBLE, **OCULTO} if c.startswith("(nuevo)")
            and re.match(r"\(nuevo\)\s*([^:]+):", c).group(1).strip() not in puntuar.TIPOS]
    mal += [c for c, v in {**VISIBLE, **OCULTO}.items() if not set(v) <= {"Nuevo", "Modifica", "Existe", "Sustituye"}]
    if all(v == ["Nuevo"] for v in VISIBLE.values()):
        mal.append("todo lo esperado es «Nuevo»")
    fallos += bool(mal)
    print(("OK   " if not mal else "FALLO ") + "lo esperado son objetos de MNT, tipos conocidos y situaciones válidas"
          + "".join(f"\n  {x}" for x in mal))
    bien = filas_bien(VISIBLE)
    sin = lambda nombres: [f for f in bien if f[0] not in nombres]
    con = lambda nombre, fila: [fila if f[0] == nombre else f for f in bien]
    with tempfile.TemporaryDirectory(prefix="puntuar con espacios ") as t:
        raiz = Path(t)
        casos = [
            ("las diez como se esperan", proyecto(raiz, bien), (), 0, "Total: 10/10"),
            ("dos que faltan: 8/10 basta", proyecto(raiz, sin(["MNT_IF_Tecnicos", "MNT_IF_ResumenOrden"])), (), 0,
             "Total: 8/10"),
            ("tres que faltan: 7/10 no basta", proyecto(raiz, sin(["MNT_IF_Tecnicos", "MNT_IF_ResumenOrden", "MNT Orden"])),
             (), 1, "Total: 7/10"),
            ("todo «Nuevo» no pasa", proyecto(raiz, [(o, ti, "Nuevo", su) for o, ti, _, su in bien], inventario=True), (), 1,
             "ya existen en la aplicación"),
            ("«Existe» donde se modifica no cuenta",
             proyecto(raiz, con("MNT_PM_GestionOrden", ("MNT_PM_GestionOrden", "Process model", "Existe", "—"))), (), 0,
             "MNT_PM_GestionOrden: existe; vale Modifica o Sustituye"),
            ("una fila «Sustituye» cuenta para el objeto que sustituye",
             proyecto(raiz, con("MNT_IF_AsignarTecnico", ("MNT_IF_ElegirTecnico", "Interfaz", "Sustituye", "`MNT_IF_AsignarTecnico`"))),
             (), 0, "MNT_IF_AsignarTecnico: sustituye"),
            ("una parte nueva cuenta como «Modifica» del objeto",
             proyecto(raiz, con("MNT Orden", ("MNT Orden — acción «Corregir orden»", "Acción de registro", "Nuevo", "—"))),
             (), 0, "MNT Orden: modifica"),
            ("un nuevo de otro tipo no cuenta",
             proyecto(raiz, con("MNT_IF_ValorarTrabajo", ("MNT Valoracion", "Record type", "Nuevo", "—"))), (), 0,
             "ninguna fila «Nuevo» de tipo interfaz"),
            ("comprobar.py con errores no pasa", proyecto(raiz, bien, roto=True), (), 1, "FALLO comprobar.py"),
            ("--ocultas sin la cuarta historia", proyecto(raiz, bien), ("--ocultas",), 1, "MNT_WS_EstadoOrden: no está en §13"),
            ("--ocultas con la cuarta historia",
             proyecto(raiz, bien + [("MNT_WS_EstadoOrden", "Web API", "Modifica", "—")]), ("--ocultas",), 0, "Total: 3/3"),
        ]
        for nombre, p, extra, codigo, debe in casos:
            c, salida = corre(p, *extra)
            ok = c == codigo and debe in salida
            fallos += not ok
            print(("OK   " if ok else "FALLO ") + nombre + ("" if ok else f" (sale {c}):\n{salida}"))
        c, salida = corre(raiz / "no existe")
        ok = c == 2 and "No encuentro" in salida
        fallos += not ok
        print(("OK   " if ok else "FALLO ") + "sin técnico sale con 2" + ("" if ok else f" (sale {c}):\n{salida}"))
    print("Todo bien" if not fallos else f"{fallos} fallos")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
