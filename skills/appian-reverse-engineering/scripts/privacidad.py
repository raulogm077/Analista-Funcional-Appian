"""Lo que nunca sale de la extracción tal cual: secretos y valores evaluados de una interfaz.

Lo usan devmcp_extract.py (antes de escribir nada a disco) y build_annex.py (antes de publicar el anexo),
para que el resultado sea el mismo se ejecute lo que se ejecute.
"""
import re
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
