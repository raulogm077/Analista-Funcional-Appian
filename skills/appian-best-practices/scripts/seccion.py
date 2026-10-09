#!/usr/bin/env python3
"""Read one section of a reference doc instead of the whole file.

    python3 scripts/seccion.py 06            # headings of references/06-*.md
    python3 scripts/seccion.py 06 5.3        # prints §5.3 (with its subsections)
    python3 scripts/seccion.py 10 hierarchy  # first heading that contains the text
"""
import re
import sys
import unicodedata
from pathlib import Path

REFS = Path(__file__).resolve().parents[1] / "references"
HEADING = re.compile(r"^(#{1,6})\s+(.*)$")


def plain(text):
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in text if not unicodedata.combining(c))


def find_doc(code):
    matches = sorted(REFS.glob(f"{code.zfill(2)}-*.md")) if code.isdigit() else sorted(REFS.glob(f"*{code}*.md"))
    if len(matches) != 1:
        names = ", ".join(p.name for p in sorted(REFS.glob("*.md")))
        sys.exit(f"No single reference matches '{code}'. Available: {names}")
    return matches[0]


def headings(lines):
    fence = False
    for i, line in enumerate(lines):
        if line.startswith("```"):
            fence = not fence
        m = None if fence else HEADING.match(line)
        if m:
            yield i, len(m.group(1)), m.group(2).strip()


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__.strip())
        return 0
    doc = find_doc(argv[0])
    lines = doc.read_text(encoding="utf-8").splitlines()
    heads = list(headings(lines))
    if len(argv) == 1:
        print(doc.name)
        for _, level, title in heads:
            print("  " * (level - 1) + title)
        return 0

    wanted = " ".join(argv[1:]).strip()
    number = re.fullmatch(r"§?(\d+(?:\.\d+)*)\.?", wanted)
    for n, (start, level, title) in enumerate(heads):
        if number:
            hit = re.match(rf"{re.escape(number.group(1))}\.?\s", title + " ")
        else:
            hit = plain(wanted) in plain(title)
        if hit:
            end = next((s for s, lv, _ in heads[n + 1:] if lv <= level), len(lines))
            print(f"{doc.name} · {title}\n")
            print("\n".join(lines[start:end]).rstrip())
            return 0
    sys.exit(f"'{wanted}' not found in {doc.name}. Run without it to list the headings.")


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):  # consolas de Windows sin UTF-8: «→» o «✓» no caben en cp1252
        _s.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv[1:]))
