#!/usr/bin/env python3
"""detect_secrets.py - Busca secretos en carpetas o ficheros, sin mostrar nunca su valor.

Uso: python3 detect_secrets.py <ruta> [<ruta> ...]   (cada ruta, carpeta o fichero)
Salida: tabla Markdown con el patrón y fichero:línea. Código de salida 1 si encuentra algo, 2 si una ruta no existe.

No cuenta como secreto una referencia (=cons!X, ri!y, pv!z, rule!…, local!…), un valor ya enmascarado (***)
ni una clave que describe el secreto sin serlo (tokenUrl, passwordPolicy…). Mismas reglas que privacidad.py.
"""
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from privacidad import NO_SECRET, is_reference  # noqa: E402

CLAVE_VALOR = re.compile(r"(?i)([A-Za-z0-9_-]*(?:password|passwd|pwd|secret|api[_-]?key|apikey|token|credential)[A-Za-z0-9_-]*)"
                         r"[\"']?\s*[:=]\s*[\"']?([^\s\"',}*][^\s\"',}]{3,})")
PATRONES = [
    ("Token de API con prefijo conocido", re.compile(r"(sk|pk|rk)_(live|test)_[A-Za-z0-9]{8,}")),
    ("Cabecera Authorization con valor", re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+/-]{16,}")),
    # Una URL ya enmascarada por completo (https://***:***@host) no es un secreto; con usuario visible, sí cuenta.
    ("URL con credenciales embebidas", re.compile(r"https?://(?!\*+:\*+@)[^/\s:@]+:[^@\s]+@\S+")),
    ("JDBC connection string con password", re.compile(r"(?i)jdbc:[a-z]+://[^\s?]+\?\S*password=[^&\s*]+")),
    ("Private key PEM", re.compile(r"BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY")),
    ("AWS access key id", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("GitHub PAT", re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}")),
    ("Slack token", re.compile(r"xox[abps]-[A-Za-z0-9-]{10,}")),
    ("JWT hardcoded (sospechoso)", re.compile(r"eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+")),
]
SALTAR = {".git", "node_modules"}


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
    try:
        datos = f.read_bytes()
    except OSError:
        return
    if b"\0" in datos[:4096]:
        return  # binario
    for n, linea in enumerate(datos.decode("utf-8", errors="replace").splitlines(), 1):
        for m in CLAVE_VALOR.finditer(linea):
            clave, valor = m.group(1), m.group(2)
            if not NO_SECRET.search(clave) and not is_reference(valor) and not valor.startswith("‹"):
                yield "Password/Secret/Token en propiedad", n
                break
        for etiqueta, rx in PATRONES:
            if rx.search(linea):
                yield etiqueta, n


def main(rutas) -> int:
    rutas = rutas or ["."]
    for r in rutas:
        if not Path(r).exists():
            print(f"[error] No existe la ruta: {r}", file=sys.stderr)
            return 2
    filas = [f"| {etiqueta} | {f}:{n} [VALOR ENMASCARADO] |" for f in ficheros(rutas) for etiqueta, n in buscar(f)]
    print(f"# Resultado de la búsqueda de secretos en `{' '.join(rutas)}`")
    print(f"_Generado: {datetime.now().astimezone().isoformat(timespec='seconds')}_\n")
    if filas:
        print("## Coincidencias detectadas\n\n| Patrón | Ubicación |\n|---|---|")
        print("\n".join(filas))
        print("\n**Acción:** si es la extracción, registra un hallazgo H-SEG (área secretos, severidad Alta) en 04 sin "
              "reproducir el valor y recomienda rotarlo y moverlo a la autenticación del connected system. Si es un "
              "entregable, no lo edites a mano: corrige la causa (enmascarado de la extracción o del anexo) y vuelve a generarlo.")
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
