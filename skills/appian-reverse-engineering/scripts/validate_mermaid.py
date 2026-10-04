#!/usr/bin/env python3
"""
validate_mermaid.py — Valida y sanea un diagrama Mermaid según las reglas
del skill appian-reverse-engineering (references/mermaid-rules.md).

Tipos admitidos:
  A  flowchart TD/LR sin subgraph ni classDef  -> se sanea (IDs N1..Nn, etiquetas limpias)
  A  flowchart agrupado por capas (subgraph sin classDef) -> se valida (<= 30 nodos) sin cambios
  B  erDiagram                                  -> se valida y se devuelve sin cambios
  C  flowchart con subgraph (carriles) y classDef -> se valida (<= 25 nodos) sin cambios

Uso:
    python validate_mermaid.py <fichero.mmd>
    python validate_mermaid.py -                # lee de stdin
    python validate_mermaid.py --check <archivo.md>   # busca bloques ```mermaid en un MD

Salida:
    - stdout: el diagrama saneado (o el original si ya es válido).
    - stderr: avisos y motivos de rechazo.
    - exit code:
        0 — válido (con o sin saneamiento)
        1 — no se ha podido sanear; usar tabla alternativa
        2 — error de uso
"""

from __future__ import annotations
import sys
import re
import argparse
from typing import List, Tuple

MAX_NODES = 30
MAX_LABEL_LEN = 50
ALLOWED_HEADERS = ("flowchart TD", "flowchart LR")

# Regex aproximadas (suficientes para nuestro subconjunto seguro).
RE_NODE = re.compile(
    r'(?P<id>[A-Za-z][A-Za-z0-9_]*)\s*'
    r'(?:\[(?P<rect>"[^"]*"|[^\[\]\n]+)\]|\{(?P<diam>"[^"]*"|[^{}\n]+)\})'
)
RE_ID_ONLY = re.compile(r'(?<![A-Za-z0-9_])([A-Za-z][A-Za-z0-9_]*)(?![A-Za-z0-9_\["{])')
RE_EDGE = re.compile(
    r'(?P<src>[A-Za-z][A-Za-z0-9_]*)\s*'
    r'(?P<arrow>-\.->|--->|-->)'
    r'(?:\s*\|\s*(?P<label>"[^"]*"|[^|]+)\s*\|\s*)?'
    r'\s*(?P<dst>[A-Za-z][A-Za-z0-9_]*)'
)


def _clean_label(raw: str) -> str:
    """Sanea una etiqueta: sin saltos, sin dobles comillas, max 50 chars."""
    s = raw.strip()
    # Si está entre comillas dobles, quita las externas.
    if s.startswith('"') and s.endswith('"') and len(s) >= 2:
        s = s[1:-1]
    s = s.replace("\n", " ").replace("\r", " ")
    s = s.replace('"', "'")
    s = re.sub(r"\s+", " ", s).strip()
    if not s:
        s = "Elemento sin nombre"
    if s.lower() == "end":
        s = "Finalización"
    if len(s) > MAX_LABEL_LEN:
        s = s[: MAX_LABEL_LEN - 1].rstrip() + "…"
    return s


def sanitize(diagram_text: str) -> Tuple[str, List[str]]:
    """
    Devuelve (diagrama_saneado, lista_de_avisos).
    Lanza ValueError si el diagrama no puede sanearse.
    """
    warnings: List[str] = []
    lines = [ln.rstrip() for ln in diagram_text.strip().splitlines() if ln.strip()]
    if not lines:
        raise ValueError("Diagrama vacío.")

    header = lines[0].strip()
    if header not in ALLOWED_HEADERS:
        # Intenta corregir flowchart sin dirección o con dirección distinta.
        if header.startswith("flowchart"):
            warnings.append(f"Cabecera '{header}' normalizada a 'flowchart TD'.")
            header = "flowchart TD"
        elif header.startswith("graph"):
            warnings.append(f"Cabecera '{header}' convertida a 'flowchart TD'.")
            header = "flowchart TD"
        else:
            raise ValueError(
                f"Cabecera no permitida: '{header}'. Solo 'flowchart TD' o 'flowchart LR'."
            )
    body = lines[1:]

    # Detección de sintaxis prohibida.
    for ln in body:
        if re.search(r"\bsubgraph\b", ln):
            raise ValueError("'subgraph' no permitido en este subconjunto.")
        if re.search(r"\bclassDef\b|:::\w+|\bstyle\b", ln):
            warnings.append("Se ignoran estilos avanzados (classDef/style).")
        if "<br>" in ln or "<br/>" in ln or "<b>" in ln:
            warnings.append("Etiquetas con HTML detectadas: se eliminará el HTML.")
            # se limpiará al sanear etiquetas más abajo.

    # Recopila IDs originales y sus etiquetas/forma.
    id_to_label: dict[str, str] = {}
    id_to_shape: dict[str, str] = {}  # 'rect' | 'diam'
    id_order: List[str] = []

    edges_raw: List[Tuple[str, str, str, str]] = []  # (src, arrow, label, dst)

    # Primera pasada: identifica nodos con etiqueta explícita.
    for ln in body:
        clean_ln = re.sub(r"<[^>]+>", "", ln)  # quita HTML inline
        for m in RE_NODE.finditer(clean_ln):
            nid = m.group("id")
            if m.group("rect") is not None:
                label = _clean_label(m.group("rect"))
                shape = "rect"
            else:
                label = _clean_label(m.group("diam"))
                shape = "diam"
            # Si el ID ya existe con otra etiqueta, primer registro gana.
            if nid not in id_to_label:
                id_to_label[nid] = label
                id_to_shape[nid] = shape
                id_order.append(nid)

    # Segunda pasada: aristas. Permitimos referenciar IDs no declarados
    # explícitamente: se crearán como nodo rectangular con su propio nombre.
    for ln in body:
        clean_ln = re.sub(r"<[^>]+>", "", ln)
        # Sustituye nodos declarados para no confundir la regex de aristas.
        edge_line = RE_NODE.sub(lambda m: m.group("id"), clean_ln)
        for m in RE_EDGE.finditer(edge_line):
            src = m.group("src")
            dst = m.group("dst")
            arrow = m.group("arrow")
            label = m.group("label") or ""
            label = _clean_label(label) if label else ""
            edges_raw.append((src, arrow, label, dst))
            for nid in (src, dst):
                if nid not in id_to_label:
                    auto_label = _clean_label(nid)
                    id_to_label[nid] = auto_label
                    id_to_shape[nid] = "rect"
                    id_order.append(nid)
                    warnings.append(f"Nodo '{nid}' sin etiqueta declarada; se autocompleta.")

    if not id_order:
        raise ValueError("No se han detectado nodos válidos.")

    # Validación de cantidad.
    if len(id_order) > MAX_NODES:
        raise ValueError(
            f"Diagrama con {len(id_order)} nodos supera el máximo permitido ({MAX_NODES}). "
            "Dividir en varios diagramas o usar tabla."
        )

    # Renombrado a N1, N2, N3...
    remap = {old: f"N{i + 1}" for i, old in enumerate(id_order)}

    # Detección de IDs problemáticos para informar.
    problematic = [oid for oid in id_order if oid.lower() in ("end", "o", "x")
                   or re.search(r"[^A-Za-z0-9_]", oid)
                   or oid[0].lower() in ("o", "x")]
    if problematic:
        warnings.append(
            "IDs problemáticos renombrados: " + ", ".join(problematic)
        )

    # Construcción del diagrama saneado.
    out_lines: List[str] = [header]
    seen_edges: set[tuple] = set()
    declared: set[str] = set()

    # Declarar todos los nodos explícitamente para evitar ambigüedades.
    for old in id_order:
        new = remap[old]
        label = id_to_label[old]
        shape = id_to_shape[old]
        if shape == "diam":
            out_lines.append(f'  {new}{{"{label}"}}')
        else:
            out_lines.append(f'  {new}["{label}"]')
        declared.add(new)

    # Añadir aristas.
    for (src, arrow, label, dst) in edges_raw:
        nsrc, ndst = remap[src], remap[dst]
        key = (nsrc, arrow, label, ndst)
        if key in seen_edges:
            continue
        seen_edges.add(key)
        if label:
            out_lines.append(f'  {nsrc} {arrow}|"{label}"| {ndst}')
        else:
            out_lines.append(f'  {nsrc} {arrow} {ndst}')

    return "\n".join(out_lines) + "\n", warnings


MAX_NODES_C = 25
RE_ER_ENTITY = re.compile(r"^(?:[A-Z][A-Za-z0-9]*|[A-Z][A-Z0-9_]*)$")
RE_ER_REL = re.compile(
    r'^(?P<a>[A-Za-z][A-Za-z0-9_]*)\s+(?P<card>[|}o][|o]--[|o][|{o]|[|}o][|o]\.\.[|o][|{o])\s+'
    r'(?P<b>[A-Za-z][A-Za-z0-9_]*)\s*:\s*(?P<label>"[^"]*"|\S+)$')
RE_ER_ATTR = re.compile(r'^[A-Za-z][A-Za-z0-9_\[\]()]*\s+[A-Za-z_][A-Za-z0-9_]*(\s+(PK|FK|UK)(\s*,\s*(PK|FK|UK))*)?(\s+"[^"]*")?$')
RE_C_NODE = re.compile(
    r'(?<![A-Za-z0-9_])(?P<id>[A-Za-z][A-Za-z0-9_]*)\s*'
    r'(?=\(\(\(|\(\(|\(\[|\[\[|\[/|\[\(|\[|\{\{|\{|\(|>)')


def validate_er(diagram_text: str) -> Tuple[str, List[str]]:
    """Tipo B: valida la sintaxis del subconjunto erDiagram y devuelve el texto sin cambios."""
    warnings: List[str] = []
    lines = [ln.strip() for ln in diagram_text.strip().splitlines() if ln.strip()]
    if not lines or lines[0] != "erDiagram":
        raise ValueError("Un diagrama de tipo B debe empezar por 'erDiagram'.")
    entities: set[str] = set()
    depth, current = 0, None
    for i, ln in enumerate(lines[1:], 2):
        if ln.startswith("%%"):
            continue
        if depth == 0:
            m = re.match(r"^([A-Za-z][A-Za-z0-9_]*)\s*\{$", ln)
            if m:
                current, depth = m.group(1), 1
                entities.add(current)
                continue
            m = RE_ER_REL.match(ln)
            if m:
                entities.update((m.group("a"), m.group("b")))
                continue
            raise ValueError(f"Línea {i} no válida en erDiagram: '{ln}'")
        if ln == "}":
            depth, current = 0, None
            continue
        if not RE_ER_ATTR.match(ln):
            raise ValueError(f"Atributo no válido en la entidad {current} (línea {i}): '{ln}'")
    if depth != 0:
        raise ValueError("Llave '{' sin cerrar en erDiagram.")
    bad = sorted(e for e in entities if not RE_ER_ENTITY.match(e))
    if bad:
        raise ValueError("Entidades con nombre no permitido (usa PascalCase o SCREAMING_SNAKE_CASE): " + ", ".join(bad))
    if not entities:
        raise ValueError("erDiagram sin entidades.")
    if len(entities) > 30:
        warnings.append(f"{len(entities)} entidades: valora partir por subdominio (mermaid-rules.md).")
    if re.search(r"<[^>]+>", diagram_text):
        raise ValueError("HTML no permitido en erDiagram.")
    return diagram_text.strip() + "\n", warnings


def validate_type_c(diagram_text: str, max_nodes: int = MAX_NODES_C, layered: bool = False) -> Tuple[str, List[str]]:
    """Tipo C: flowchart BPMN con carriles (subgraph) y classDef. Valida y devuelve sin cambios.

    Con layered=True valida un tipo A agrupado por capas (subgraph sin classDef): límite de tipo A.
    """
    warnings: List[str] = []
    lines = [ln.rstrip() for ln in diagram_text.strip().splitlines() if ln.strip()]
    header = lines[0].strip()
    if header not in ALLOWED_HEADERS:
        raise ValueError(f"Cabecera no permitida en tipo C: '{header}'.")
    depth, node_ids = 0, set()
    for i, raw in enumerate(lines[1:], 2):
        ln = raw.strip()
        if ln.startswith("%%"):
            continue
        if re.match(r"^subgraph\b", ln):
            depth += 1
            m = re.match(r'^subgraph\s+([A-Za-z][A-Za-z0-9_]*)', ln)
            if not m:
                raise ValueError(f"subgraph sin ID válido (línea {i}): '{ln}'")
            continue
        if ln == "end":
            depth -= 1
            if depth < 0:
                raise ValueError(f"'end' sin subgraph abierto (línea {i}).")
            continue
        if ln.startswith(("classDef ", "class ", "style ", "linkStyle ", "direction ")):
            continue
        if "fa:fa-" in ln:
            raise ValueError(f"Iconos FontAwesome no permitidos (línea {i}).")
        if re.search(r"<(?!br\s*/?>)[^>]+>", ln):
            raise ValueError(f"HTML no permitido (línea {i}).")
        for m in RE_C_NODE.finditer(re.sub(r'"[^"]*"', '""', ln)):
            nid = m.group("id")
            if nid.lower() == "end":
                raise ValueError(f"'end' no puede usarse como ID de nodo (línea {i}).")
            if nid[0] in ("o", "x"):
                raise ValueError(f"ID '{nid}' empieza por 'o' o 'x' minúscula (línea {i}).")
            node_ids.add(nid)
        for m in RE_EDGE.finditer(re.sub(r'"[^"]*"', '""', ln)):
            node_ids.update((m.group("src"), m.group("dst")))
    if depth != 0:
        raise ValueError("Número de 'subgraph' y 'end' no cuadra.")
    node_ids -= {"subgraph", "classDef", "class", "style"}
    if len(node_ids) > max_nodes:
        what = "del tipo A por capas: parte por capa" if layered else "del tipo C: parte el proceso en subprocesos"
        raise ValueError(f"{len(node_ids)} nodos superan el máximo de {max_nodes} {what}.")
    if not layered and "classDef" not in diagram_text:
        warnings.append("Tipo C sin classDef: los nodos no tendrán el estilo BPMN.")
    return diagram_text.strip() + "\n", warnings


def validate(diagram_text: str) -> Tuple[str, List[str]]:
    """Detecta el tipo (A, B o C) y aplica la validación correspondiente."""
    first = next((ln.strip() for ln in diagram_text.splitlines() if ln.strip()), "")
    if first == "erDiagram":
        return validate_er(diagram_text)
    if first.startswith(("flowchart", "graph")):
        has_class = re.search(r"^\s*classDef\b", diagram_text, re.M)
        if has_class:
            return validate_type_c(diagram_text)
        if re.search(r"^\s*subgraph\b", diagram_text, re.M):
            return validate_type_c(diagram_text, max_nodes=MAX_NODES, layered=True)
    return sanitize(diagram_text)


def extract_mermaid_blocks(md_text: str) -> List[str]:
    """Extrae bloques ```mermaid ... ``` de un texto Markdown."""
    return re.findall(r"```mermaid\s*\n(.*?)```", md_text, flags=re.DOTALL)


def main() -> int:
    parser = argparse.ArgumentParser(description="Valida y sanea diagramas Mermaid.")
    parser.add_argument("source", help="Fichero a procesar, '-' para stdin.")
    parser.add_argument(
        "--check", action="store_true",
        help="Si el fichero es Markdown, busca bloques ```mermaid y valida cada uno."
    )
    args = parser.parse_args()

    if args.source == "-":
        raw = sys.stdin.read()
        diagrams = [raw]
    else:
        try:
            with open(args.source, encoding="utf-8") as f:
                raw = f.read()
        except OSError as e:
            print(f"[error] No se puede leer {args.source}: {e}", file=sys.stderr)
            return 2
        if args.check:
            diagrams = extract_mermaid_blocks(raw)
            if not diagrams:
                print("[info] No se han encontrado bloques mermaid.", file=sys.stderr)
                return 0
        else:
            diagrams = [raw]

    overall_ok = True
    for idx, diag in enumerate(diagrams, 1):
        try:
            clean, warns = validate(diag)
        except ValueError as e:
            print(f"[rechazado] Diagrama #{idx}: {e}", file=sys.stderr)
            print(
                "[acción]    Sustituir por tabla alternativa según mermaid-rules.md.",
                file=sys.stderr,
            )
            overall_ok = False
            continue
        for w in warns:
            print(f"[aviso #{idx}] {w}", file=sys.stderr)
        if len(diagrams) > 1:
            print(f"---- diagrama #{idx} ----")
        print(clean, end="")

    return 0 if overall_ok else 1


if __name__ == "__main__":
    sys.exit(main())
