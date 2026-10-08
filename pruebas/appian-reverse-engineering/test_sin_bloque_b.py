"""Ingeniería inversa sin el bloque B (reconstrucción, modernización y diseño objetivo), que se aparta para F5, ni
«reingeniería», que es rehacer: la skill documenta lo que hay."""
import re

from conftest import SKILL  # carpeta de la skill (Tarea 0)

PROHIBIDO = re.compile(
    r"12-especificacion|13-modernizacion|14-diseno|rebuild-architect|target-designer|modernizacion\.json|"
    r"moderniz|reconstru|[Vv]eredicto|\b(MOD|PQ|DEC|RF|RNF)-|17 documentos|00.{1,3}14\b|"
    r"tratamiento (de|en) 13|\"tratamiento\"|tratamiento\[|\| Tratamiento \|"
    r"|`1[234]`|(?i:moderniz|reconstru|reingenier)|\b(MOD|PQ)\b|(?:\b(?:de|en|y)|→) 1[234]\b(?![\w ]*(referencias|interfaces|constantes|tareas))|\| (\d\d, )*1[234] [|(]")

def test_ingenieria_inversa_no_menciona_el_bloque_b():
    malos = [f"{p.relative_to(SKILL)}:{n}" for p in SKILL.rglob("*") if p.suffix in (".md", ".py", ".json")
             for n, l in enumerate(p.read_text(encoding="utf-8").splitlines(), 1) if PROHIBIDO.search(l)]
    assert malos == []
