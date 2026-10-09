#!/usr/bin/env bash
# detect_secrets.sh — Compatibilidad: la búsqueda la hace detect_secrets.py (mismas opciones y salida).
# Uso: bash detect_secrets.sh <ruta> [<ruta> ...]
# Usa el primer Python 3.9 o superior que funcione: en Windows solo suele haber «python», y «python3» puede ser el
# alias de la Microsoft Store, que no ejecuta nada.
for py in python3 python; do
  if command -v "$py" >/dev/null 2>&1 && "$py" -c 'import sys; sys.exit(sys.version_info < (3, 9))' >/dev/null 2>&1; then
    exec "$py" "$(dirname "$0")/detect_secrets.py" "$@"
  fi
done
echo "detect_secrets.sh: hace falta Python 3.9 o superior (python3 o python)" >&2
exit 2
