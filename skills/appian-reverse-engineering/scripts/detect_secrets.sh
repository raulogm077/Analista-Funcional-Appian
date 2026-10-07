#!/usr/bin/env bash
# detect_secrets.sh — Compatibilidad: la búsqueda la hace detect_secrets.py (mismas opciones y salida).
# Uso: bash detect_secrets.sh <ruta> [<ruta> ...]
exec python3 "$(dirname "$0")/detect_secrets.py" "$@"
