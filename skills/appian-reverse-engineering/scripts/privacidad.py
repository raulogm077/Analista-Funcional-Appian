"""Lo que nunca sale de la extracción tal cual: secretos, usuarios, correos y valores evaluados de una interfaz.

devmcp_extract.py escribe la extracción ya saneada (mask_secrets, redact_screen y sanea): secretos enmascarados, cada
usuario con su seudónimo (‹usuario-xxxxxx›) y cada correo como ‹correo›. build_annex.py parte de ahí (scrub): quita las
credenciales de las URLs, oculta los hosts internos y cambia cada seudónimo por los grupos de la aplicación a los que
pertenece. Las mismas reglas, se ejecute lo que se ejecute.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Any

MASK = "***ENMASCARADO***"
URL_CRED = re.compile(r"(https?://)([^/@\s:]+):([^/@\s]+)@")
STRONG_SECRET = re.compile(
    r"(?:sk|pk|rk)_(?:live|test)_[A-Za-z0-9]{8,}|AKIA[0-9A-Z]{16}|(?i:bearer)\s+[A-Za-z0-9._~+/=-]{16,}"
    r"|-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"
    r"|eyJ[\w-]{10,}\.eyJ[\w-]{10,}\.[\w-]+|gh[pousr]_[A-Za-z0-9]{36,}|xox[abps]-[A-Za-z0-9-]{10,}")
# nombre de una clave, cabecera o constante que guarda un secreto (por subcadena: authToken, sapPassword…)
SECRET_NAME = re.compile(r"(?i)(token|secret|passw|pwd|api[_\-]?key|credential|private[_\-]?key|authorization)")
# …salvo las que describen el secreto sin serlo (tokenUrl, passwordPolicy, secretName…)
NO_SECRET = re.compile(r"(?i)(url|uri|endpoint|type|expir|ttl|name|label|policy|enabled|required|hint|mode)$")
# literales en una expresión SAIL: a!httpAuthenticationBasic(username: "x", password: "y"), apiKey: "…"
SAIL_LITERAL = re.compile(r'(?i)\b(password|passwd|pwd|secret|client_?secret|api_?key|apikey|access_?token|'
                          r'refresh_?token|token|username)(\s*:\s*)"([^"]+)"')


def is_reference(v: str) -> bool:
    """Una expresión que referencia un secreto (=cons!X, ri!y) no es el secreto."""
    return v.startswith("=") or re.search(r"\b(cons|ri|pv|rule|local)!", v) is not None


def secret_key(k) -> bool:
    k = str(k)
    return bool(SECRET_NAME.search(k)) and not NO_SECRET.search(k)


def mask_text(s: str, counter: list) -> str:
    out = URL_CRED.sub(lambda m: m.group(1) + "***:***@", s)
    out = STRONG_SECRET.sub(MASK, out)

    def literal(m):
        return m.group(0) if is_reference(m.group(3)) else f'{m.group(1)}{m.group(2)}"{MASK}"'
    out = SAIL_LITERAL.sub(literal, out)
    if out != s:
        counter[0] += 1
    return out


def mask_secrets(data: Any, counter: list, secret_values: bool = False) -> Any:
    """Enmascara credenciales: URLs con usuario:clave, tokens con formato conocido, claves que guardan un
    secreto (también por subcadena y en cabeceras {name, value}), literales SAIL de autenticación y, en
    constantes con nombre de secreto, su valor."""
    if isinstance(data, dict):
        etiqueta = next((data[k] for k in ("name", "key", "header", "headerName") if isinstance(data.get(k), str)), "")
        cabecera_secreta = bool(etiqueta) and secret_key(etiqueta)
        out = {}
        for k, v in data.items():
            if isinstance(v, str) and v and not is_reference(v) and (
                    secret_key(k) or ((secret_values or cabecera_secreta) and str(k).lower() == "value")):
                out[k] = MASK
                counter[0] += 1
            else:
                out[k] = mask_secrets(v, counter, secret_values)
        return out
    if isinstance(data, list):
        return [mask_secrets(x, counter, secret_values) for x in data]
    if isinstance(data, str):
        return mask_text(data, counter)
    return data


SCREEN_KEEP = {"type", "label", "title", "heading", "columns", "instructions", "placeholder", "tooltip",
               "buttonLabel", "componentType", "caption", "labels"}


def redact_screen(x, key: str = ""):
    """Render de una interfaz: conserva la estructura y las etiquetas; los valores (pueden ser datos reales
    evaluados: recuentos, filas) se sustituyen por ‹valor›."""
    if isinstance(x, dict):
        return {k: redact_screen(v, k) for k, v in x.items()}
    if isinstance(x, list):
        if key in SCREEN_KEEP and all(isinstance(v, str) for v in x):
            return x
        return [redact_screen(v, key) for v in x]
    if isinstance(x, str) and key in SCREEN_KEEP:
        return x
    return "‹valor›" if x not in (None, "", [], {}) else x


# ------------------------------------------------------------------------ usuarios, correos y hosts (anexo)

USER_KEY = re.compile(r"(?i)^(user(name|id)?|login|initiator|startedby|starter|author|owner|creator|modifier|assignee|usuario|"
                      r"displayname|fullname|firstname|lastname|e-?mail|mail|"
                      r".*(by|byuser|user|username|userid|fullname|displayname|email|author|owner|creator|modifier))$")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+")
USER_PH = "‹usuario›"
# Cómo se escriben los datos sensibles en un entregable (references/security-rules.md):
URL_CREDS = re.compile(r"(https?://)\*+:\*+@")                 # credenciales ya enmascaradas: se retiran
MASKED = re.compile(r"\*\*\*ENMASCARADO\*\*\*")
URL_HOST = re.compile(r"(https?://)([^/\s:'\"?#]+)")
INTERNAL_HOST = re.compile(r"^(10\.\d+\.\d+\.\d+|127\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|172\.(1[6-9]|2\d|3[01])\.\d+\.\d+"
                           r"|localhost|[^.]+|.+\.(local|internal|corp|intra))$", re.I)


def load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def sensitive(text: str, notes: set[str], key: str = "") -> str:
    """Quita credenciales de las URLs, deja los secretos como *** y oculta los hosts internos."""
    if URL_CREDS.search(text):
        donde = f" de `{key}`" if key else ""
        notes.add(f"La URL{donde} llevaba credenciales embebidas (usuario y contraseña): se han retirado.")
        text = URL_CREDS.sub(r"\1", text)
    text = MASKED.sub("***", text)

    def host(m):
        if INTERNAL_HOST.match(m.group(2)):
            notes.add("Los hosts internos se muestran como ‹host interno›.")
            return m.group(1) + "‹host interno›"
        return m.group(0)
    return URL_HOST.sub(host, text)


def users_seen(raw: Path) -> set[str]:
    """Identificadores de usuario que aparecen en miembros, versiones y ejecuciones."""
    found: set[str] = set()

    def walk(x, key=""):
        if isinstance(x, dict):
            if str(x.get("type", x.get("kind", ""))).lower() == "user":
                found.update(v for k, v in x.items() if k in ("name", "username", "id", "value") and isinstance(v, str))
            for k, v in x.items():
                walk(v, k)
        elif isinstance(x, list):
            for v in x:
                walk(v, key)
        elif isinstance(x, str) and USER_KEY.match(key or "") and 3 <= len(x) <= 80 and " " not in x.strip():
            found.add(x.strip())
    for f in raw.rglob("*.json"):
        try:
            d = load(f)
        except Exception:  # noqa: BLE001
            continue
        if isinstance(d, dict) and (d.get("_meta") or {}).get("role") in ("members", "versions", "history"):
            walk(d.get("response"))
    return {u for u in found if u != USER_PH}


def user_labels(users: set[str], trabajo: Path, inv: dict) -> dict[str, str]:
    """Etiqueta de cada usuario: los grupos de la aplicación de los que es miembro directo, sin su nombre."""
    groups: dict[str, list[str]] = defaultdict(list)
    for g in inv.get("objects", {}).get("group", []):
        for f in g.get("files", []):
            if f.get("role") != "members" or not f.get("ok"):
                continue
            try:
                resp = load(trabajo / f["path"]).get("response")
            except Exception:  # noqa: BLE001
                continue
            found = users_in(resp)
            for u in found:
                groups[u].append(g.get("name"))
    return {u: (f"‹usuario de {', '.join(sorted(set(groups[u])))}›" if groups.get(u) else USER_PH) for u in users}


def users_in(x) -> set[str]:
    out: set[str] = set()

    def walk(v, key=""):
        if isinstance(v, dict):
            if str(v.get("type", v.get("kind", ""))).lower() == "user":
                out.update(w for k, w in v.items() if k in ("name", "username", "id", "value") and isinstance(w, str))
            for k, w in v.items():
                walk(w, k)
        elif isinstance(v, list):
            for w in v:
                walk(w, key)
        elif isinstance(v, str) and USER_KEY.match(key or ""):
            out.add(v.strip())
    walk(x)
    return out


def scrub(x, users: dict[str, str], notes: set[str] | None = None, names: dict[str, str] | None = None):
    notes = set() if notes is None else notes
    names = names or {}
    if isinstance(x, dict):
        # un objeto de usuario (por su tipo o por tener usuario o correo): no queda ningún texto suyo
        is_user = str(x.get("type", x.get("kind", ""))).lower() == "user" or any(k.lower() == "username" for k in x)
        ident = next((str(x[k]).strip() for k in ("username", "userName", "name", "id", "value") if isinstance(x.get(k), str)), "")
        propia = users.get(ident, USER_PH) if is_user else USER_PH
        out = {}
        for k, v in x.items():
            if USER_KEY.match(k) and isinstance(v, (str, int)):
                out[k] = users.get(str(v).strip(), propia)
            elif is_user and isinstance(v, str) and k not in ("type", "kind"):
                out[k] = users.get(v.strip(), propia)
            elif isinstance(v, str) and v not in names:
                out[k] = scrub_text(v, users, notes, k)
            else:
                out[k] = scrub(v, users, notes, names)
        return out
    if isinstance(x, list):
        return [scrub(v, users, notes, names) for v in x]
    if isinstance(x, str):
        if x in names:
            return f"{x} ‹{names[x]}›"
        return scrub_text(x, users, notes)
    return x


def scrub_text(x: str, users: dict[str, str], notes: set[str], key: str = "") -> str:
    x = mask_text(x, [0])          # literales de autenticación y tokens que se hubieran escapado
    x = sensitive(x, notes, key)
    x = EMAIL.sub("‹correo›", x)
    if "‹correo›" in x:            # también los que ya vienen así de la extracción
        notes.add("Las direcciones de correo se muestran como ‹correo›.")
    for u, label in users.items():
        if u in x:
            x = re.sub(rf"(?<![\w.]){re.escape(u)}(?![\w])", label, x)
    return x


# ------------------------------------------------------------------------ seudónimos (la extracción)

HUELLAS = "_huellas.json"   # en mcp_raw/: la huella de cada usuario que ha salido en la extracción, nunca su nombre
# Un usuario de Appian solo lleva letras ASCII, números y @ . _ - ' (https://docs.appian.com/suite/help/26.6/User_Management.html)
PALABRA = re.compile(r"[A-Za-z0-9@._'-]+")
APRENDE = re.compile(r"^(?=.*[A-Za-z])[A-Za-z0-9@._'-]{3,255}$")   # el usuario que luego se busca en los textos
MARCA = re.compile(r"(‹[^‹›]*›)")                                    # lo ya saneado (‹usuario-…›, ‹correo›…)
CAMPO_PERSONA = re.compile(r"(?i)^(displayname|fullname|firstname|lastname)$")   # fuera de un usuario, la etiqueta de un objeto
CAMPO_CORREO = re.compile(r"(?i)^(e-?mail|mail|.*email)$")                      # su valor es un correo: ‹correo›
NO_ES_USUARIO = re.compile(r"(?i)^(group|order|sort|partition|filter|index)by$")
# entradas, variables y campos de tipo usuario: {name: "aprobador", type: "User"} es una definición, no un usuario
DEFINICIONES = re.compile(r"(?i)^(inputs|ruleinputs|processvariables|variables|parameters|params|fields|properties|"
                          r"attributes|outputs|columns|arguments)$")
CLAVES_UUID = ("uuid", "objectUuid", "designObjectUuid")


def seudonimo(usuario: str) -> str:
    """‹usuario-xxxxxx›, con los 6 primeros hex del sha256 del usuario en minúsculas. El mismo usuario da el mismo en
    cualquier respuesta, sesión o equipo: se puede retomar la extracción y user_labels agrupa por grupos."""
    return "‹usuario-" + hashlib.sha256(usuario.strip().lower().encode("utf-8")).hexdigest()[:6] + "›"


@lru_cache(maxsize=100_000)
def huella(usuario: str) -> str:
    """sha256 del usuario tal como se escribe: lo reconoce en un texto sin guardar su nombre."""
    return hashlib.sha256(usuario.encode("utf-8")).hexdigest()


def _valor(v) -> bool:
    """Un texto que puede ser un usuario: ni vacío, ni ya saneado (‹…›), ni una expresión o una referencia."""
    return isinstance(v, str) and bool(v.strip()) and not v.startswith("‹") and not is_reference(v)


def _campo_usuario(k) -> bool:
    k = str(k)
    return bool(USER_KEY.match(k)) and not (CAMPO_PERSONA.match(k) or CAMPO_CORREO.match(k) or NO_ES_USUARIO.match(k))


def _campos(x, hallados: set[str], padre: str = ""):
    """Los usuarios de los campos de usuario, de los objetos de tipo usuario y de las constantes, variables y valores
    de tipo usuario, cada uno por su seudónimo. Los que cambia los añade a `hallados`."""
    if isinstance(x, list):
        return [_campos(v, hallados, padre) for v in x]
    if not isinstance(x, dict):
        return x
    diseno = any(k in x for k in CLAVES_UUID)                  # un objeto de diseño (p. ej. una constante) no es un usuario
    de_tipo_usuario = any(str(x.get(k, "")).lower() == "user" for k in ("type", "kind", "objectType"))
    con_valor = de_tipo_usuario and "value" in x               # constante, variable o valor: el usuario es el valor
    usuario = not diseno and (any(str(k).lower() in ("username", "login") for k in x) or (
        de_tipo_usuario and not con_valor and not DEFINICIONES.match(padre)))
    ident = next((x[k] for k in ("username", "userName", "login", "name", "id") if _valor(x.get(k))), None)
    propio = seudonimo(ident) if usuario and ident else None

    def cambia(v: str) -> str:
        hallados.add(v.strip())
        return seudonimo(v)

    out = {}
    for k, v in x.items():
        if usuario and _valor(v) and (k in ("name", "id") or USER_KEY.match(str(k))):
            hallados.add(v.strip())
            out[k] = propio or seudonimo(v)                    # todo lo que identifica a la persona, con su seudónimo
        elif con_valor and k == "value" and (_valor(v) or isinstance(v, list)):
            out[k] = cambia(v) if isinstance(v, str) else [cambia(w) if _valor(w) else w for w in v]
        elif _campo_usuario(k) and _valor(v):
            out[k] = cambia(v)
        else:
            out[k] = _campos(v, hallados, str(k))
    return out


def _trozos(palabra: str) -> list[tuple[int, int]]:
    """Dónde puede estar un usuario dentro de una palabra: empieza al principio o tras - ' @ y acaba al final o
    antes de . - ' @ (como un usuario escrito en un texto: «ana.garcia.», «'ana.garcia'»)."""
    inicios = [0] + [i + 1 for i, c in enumerate(palabra) if c in "-'@"]
    finales = sorted({len(palabra)} | {i for i, c in enumerate(palabra) if c in ".-'@"}, reverse=True)
    return [(s, e) for s in inicios for e in finales if e - s >= 3]


def _en_palabra(palabra: str, usuarios: set[str]) -> str:
    out, hecho = [], 0
    for s, e in _trozos(palabra):                            # de izquierda a derecha y, en cada inicio, el más largo
        if s >= hecho and palabra[s:e] in usuarios:
            out += [palabra[hecho:s], seudonimo(palabra[s:e])]
            hecho = e
    return "".join(out + [palabra[hecho:]])


def _texto(s: str, usuarios: set[str]) -> str:
    s = EMAIL.sub("‹correo›", s)
    if not usuarios:
        return s
    partes = MARCA.split(s)                                   # lo ya saneado no se toca
    for i in range(0, len(partes), 2):
        partes[i] = PALABRA.sub(lambda m: _en_palabra(m.group(0), usuarios), partes[i])
    return "".join(partes)


def _textos(x, usuarios: set[str]):
    if isinstance(x, dict):
        return {k: _textos(v, usuarios) for k, v in x.items()}
    if isinstance(x, list):
        return [_textos(v, usuarios) for v in x]
    return _texto(x, usuarios) if isinstance(x, str) else x


def sanea(data: Any, usuarios: set[str]) -> Any:
    """Lo que se guarda de la extracción, después de mask_secrets: cada usuario pasa a su seudónimo (los de los campos
    de usuario de USER_KEY, de los objetos de tipo usuario y de las constantes, variables y valores de tipo usuario, y
    los usuarios ya conocidos que aparezcan en cualquier texto) y cada correo, a ‹correo›. Añade a `usuarios` los que
    encuentra, para sanear con ellos las respuestas siguientes. Sanear dos veces da lo mismo que una."""
    hallados: set[str] = set()
    data = _campos(data, hallados)
    usuarios.update(u for u in hallados if APRENDE.match(u))
    return _textos(data, usuarios)


def _cadenas(x):
    if isinstance(x, dict):
        for v in x.values():
            yield from _cadenas(v)
    elif isinstance(x, list):
        for v in x:
            yield from _cadenas(v)
    elif isinstance(x, str):
        yield x


def conocidos(data: Any, huellas: set[str]) -> set[str]:
    """Los usuarios que aparecen en los textos de `data` y cuya huella está en `huellas`: con ellos se sanea lo que se
    escribió antes de conocerlos, sin haber guardado nunca su nombre."""
    out: set[str] = set()
    if not huellas:
        return out
    for s in _cadenas(data):
        for parte in MARCA.split(s)[::2]:
            for m in PALABRA.finditer(parte):
                palabra = m.group(0)
                out.update(palabra[a:b] for a, b in _trozos(palabra) if huella(palabra[a:b]) in huellas)
    return out


def lee_huellas(raw: Path) -> set[str]:
    try:
        return set(load(Path(raw) / HUELLAS).get("huellas", []))
    except (OSError, ValueError, AttributeError):
        return set()


def guarda_huellas(raw: Path, usuarios: set[str]) -> None:
    """Añade a mcp_raw/_huellas.json la huella de estos usuarios (nunca su nombre)."""
    todas = lee_huellas(raw) | {huella(u) for u in usuarios}
    f = Path(raw) / HUELLAS
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps({"_doc": "Huella (sha256) de cada usuario que ha salido en la extracción, nunca su nombre: "
                                     "con ella se reconoce a un usuario en un texto escrito antes de conocerlo.",
                             "huellas": sorted(todas)}, ensure_ascii=False, indent=1), encoding="utf-8")
