#!/usr/bin/env python3
"""detect_secrets.py - Busca secretos escritos en carpetas o ficheros y dice dónde están.

Uso: python3 detect_secrets.py <ruta> [<ruta> ...]   (cada ruta, carpeta o fichero)
Salida: tabla Markdown con el patrón y dónde está: en un .json, el fichero y la propiedad
(fichero#response.headers[0].value); en otro fichero, el fichero y la línea. Código de salida 1 si encuentra algo,
2 si una ruta no existe.

Un .json se recorre entero, sin el _meta de la extracción: una clave con nombre de secreto (authToken, sapPassword,
Authorization…), el valor de una cabecera {name, value} con nombre de secreto y los patrones de cada texto, también
de una expresión (password: "x", apiKey: "x"). Otro fichero se mira línea a línea.
No cuenta como secreto una referencia (=cons!X, ri!y, pv!z, rule!…, local!…), un valor de asteriscos (***), un sí o
no (true, false, null) ni una clave que describe el secreto sin serlo (tokenUrl, passwordPolicy…). build_model.py lo
usa para contar los secretos de cada objeto.
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

# nombre de una clave o una cabecera que guarda un secreto (por subcadena: authToken, sapPassword, X-Api-Key…)
SECRETO = r"(?:passw|pwd|secret|api[_-]?key|token|credential|private[_-]?key|authorization)"
NOMBRE_SECRETO = re.compile(r"(?i)" + SECRETO)
# «clave: valor» o «clave=valor» en un texto
CLAVE_VALOR = re.compile(r"(?i)([A-Za-z0-9_-]*" + SECRETO + r"[A-Za-z0-9_-]*)"
                         r"[\"']?\s*[:=]\s*[\"']?([^\s\"',}*][^\s\"',}]{3,})")
# …salvo las claves que describen el secreto sin serlo (tokenUrl, passwordPolicy, secretName…)
NO_SECRET = re.compile(r"(?i)(url|uri|endpoint|type|expir|ttl|name|label|policy|enabled|required|hint|mode)$")
CABECERA = ("name", "objectName", "key", "header", "headerName")   # el nombre de una cabecera {name, value}
PATRONES = [
    ("Token de API con prefijo conocido", re.compile(r"(sk|pk|rk)_(live|test)_[A-Za-z0-9]{8,}")),
    ("Cabecera Authorization con valor", re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+/-]{16,}")),
    # Una URL con asteriscos en lugar de usuario y contraseña (https://***:***@host) no es un secreto; con usuario, sí.
    ("URL con credenciales embebidas", re.compile(r"https?://(?!\*+:\*+@)[^/\s:@]+:[^@\s]+@\S+")),
    ("JDBC connection string con password", re.compile(r"(?i)jdbc:[a-z]+://[^\s?]+\?\S*password=[^&\s*]+")),
    ("Private key PEM", re.compile(r"BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY")),
    ("AWS access key id", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("GitHub PAT", re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}")),
    ("Slack token", re.compile(r"xox[abps]-[A-Za-z0-9-]{10,}")),
    ("JWT hardcoded (sospechoso)", re.compile(r"eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+")),
]
SALTAR = {".git", "node_modules"}
# palabras de un texto («Secretos: ninguno detectado»), no claves
PROSA = re.compile(r"(?i)^(secretos?|secrets|tokens|credenciales?|credentials|contraseñas?|passwords)$")


def is_reference(v: str) -> bool:
    """Una expresión que referencia un secreto (=cons!X, ri!y) no es el secreto."""
    return v.startswith("=") or re.search(r"\b(cons|ri|pv|rule|local)!", v) is not None


def secreta(clave) -> bool:
    """Una clave o una cabecera que guarda un secreto, salvo las que lo describen (tokenUrl, apiKeyName…)."""
    return bool(NOMBRE_SECRETO.search(str(clave))) and not NO_SECRET.search(str(clave))


def escrito(valor) -> bool:
    """Un valor escrito en la aplicación: un texto que no es una referencia, un sí o no ni asteriscos."""
    return isinstance(valor, str) and valor.strip() != "" and not valor.startswith("*") and not is_reference(valor) \
        and valor.strip().lower() not in ("true", "false", "null")


def en_texto(texto: str):
    """Los patrones de un texto: una línea de un fichero o un texto de un JSON."""
    for m in CLAVE_VALOR.finditer(texto):
        clave, valor = m.group(1), m.group(2)
        if not NO_SECRET.search(clave) and not PROSA.match(clave) and not is_reference(valor) \
                and valor.lower() not in ("true", "false", "null"):
            yield "Password/Secret/Token en propiedad"
            break
    for etiqueta, rx in PATRONES:
        if rx.search(texto):
            yield etiqueta


def en_json(x, ruta: str = ""):
    """(patrón, propiedad) en un JSON: una clave con nombre de secreto y valor escrito, el valor de una cabecera
    {name, value} con nombre de secreto y los patrones de cada texto (ya sin las comillas escapadas)."""
    if isinstance(x, dict):
        nombre = next((x[k] for k in CABECERA if isinstance(x.get(k), str)), "")
        for k, v in x.items():
            donde = f"{ruta}.{k}" if ruta else str(k)
            if escrito(v) and (secreta(k) or (str(k).lower() == "value" and secreta(nombre))):
                yield "Password/Secret/Token en propiedad", donde
            else:
                yield from en_json(v, donde)
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from en_json(v, f"{ruta}[{i}]")
    elif isinstance(x, str):
        for etiqueta in en_texto(x):
            yield etiqueta, ruta


def ficheros(rutas):
    for r in rutas:
        p = Path(r)
        if p.is_file():
            yield p
        else:
            for f in sorted(p.rglob("*")):
                if f.is_file() and not SALTAR & set(f.parts):
                    yield f


def buscar(f: Path):
    """(patrón, dónde) de cada posible secreto: en un .json, la propiedad; en otro fichero, el número de línea."""
    try:
        datos = f.read_bytes()
    except OSError:
        return
    if b"\0" in datos[:4096]:
        return  # binario
    texto = datos.decode("utf-8", errors="replace")
    if f.suffix.lower() == ".json":
        try:
            doc = json.loads(texto)
        except ValueError:
            pass                                    # no es un JSON válido: se mira línea a línea
        else:
            if isinstance(doc, dict):
                doc.pop("_meta", None)              # lo que anota la extracción, no la aplicación
            yield from en_json(doc)
            return
    for n, linea in enumerate(texto.splitlines(), 1):
        for etiqueta in en_texto(linea):
            yield etiqueta, n


def main(rutas) -> int:
    rutas = rutas or ["."]
    for r in rutas:
        if not Path(r).exists():
            print(f"[error] No existe la ruta: {r}", file=sys.stderr)
            return 2
    filas = [f"| {etiqueta} | {f}#{donde} |" if isinstance(donde, str) else f"| {etiqueta} | {f}:{donde} |"
             for f in ficheros(rutas) for etiqueta, donde in buscar(f)]
    print(f"# Resultado de la búsqueda de secretos en `{' '.join(rutas)}`")
    print(f"_Generado: {datetime.now().astimezone().isoformat(timespec='seconds')}_\n")
    if filas:
        print("## Coincidencias detectadas\n\n| Patrón | Ubicación |\n|---|---|")
        print("\n".join(filas))
        print("\n**Acción:** en la extracción, cada coincidencia es un posible secreto escrito en la aplicación: "
              "regístralo como hallazgo H-SEG (área secretos, severidad Alta) en 04, con el objeto y la propiedad donde "
              "está; si es un falso positivo, descártalo (security-rules.md).")
        return 1
    print("## Sin coincidencias\nNo se han detectado patrones de secretos en la ruta analizada.")
    return 0


if __name__ == "__main__":
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            pass
    sys.exit(main(sys.argv[1:]))
