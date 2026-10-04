#!/usr/bin/env bash
# detect_secrets.sh — Detección de patrones de secretos en carpetas o ficheros.
# Uso: bash detect_secrets.sh <ruta> [<ruta> ...]   (cada ruta puede ser carpeta o fichero)
# Salida: tabla Markdown a stdout. Exit code 1 si se detecta algo, 2 si una ruta no existe.

set -u
if [ "$#" -eq 0 ]; then
  set -- .
fi
for p in "$@"; do
  if [ ! -e "$p" ]; then
    echo "[error] No existe la ruta: $p" >&2
    exit 2
  fi
done
ROOT="$*"

found=0
tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT

scan() {
  local label="$1"
  local pattern="$2"
  shift 2
  # -I: ignora binarios. -n: número de línea. -E: regex extendida.
  # Solo se imprime fichero:línea. El contenido de la línea NUNCA se muestra.
  grep -rIEn --exclude-dir='.git' --exclude-dir='node_modules' \
    -- "$pattern" "$@" 2>/dev/null \
    | sed -E 's/^(.*:[0-9]+):.*$/\1/' \
    | while IFS= read -r loc; do
        printf '| %s | %s [VALOR ENMASCARADO] |\n' "$label" "$loc" >> "$tmp"
      done
}

scan "Password/Secret/Token en propiedad" '(^|[^A-Za-z0-9_])(password|passwd|pwd|secret|api[_-]?key|apikey|token|bearer)["'"'"']?[[:space:]]*[:=][[:space:]]*"?[^[:space:]"*]{4,}' "$@"
scan "Token de API con prefijo conocido"  '(sk|pk|rk)_(live|test)_[A-Za-z0-9]{8,}' "$@"
scan "Cabecera Authorization con valor"   '[Bb]earer[[:space:]]+[A-Za-z0-9._~+/-]{16,}' "$@"
# Una URL ya enmascarada por completo (https://***:***@host) no es un secreto; con usuario visible, sí cuenta.
scan "URL con credenciales embebidas"     'https?://([^/[:space:]:*][^/[:space:]:]*|[*]+[^/[:space:]:*][^/[:space:]:]*):[^@[:space:]]+@[^[:space:]]+' "$@"
scan "JDBC connection string con password" 'jdbc:[a-z]+://[^[:space:]?]+\?[^[:space:]]*password=[^&[:space:]]+' "$@"
scan "Private key PEM"                    'BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY' "$@"
scan "AWS access key id"                  'AKIA[0-9A-Z]{16}' "$@"
scan "GitHub PAT"                         'gh[pousr]_[A-Za-z0-9]{36,}' "$@"
scan "Slack token"                        'xox[abps]-[A-Za-z0-9-]{10,}' "$@"
scan "JWT hardcoded (sospechoso)"         'eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+' "$@"

echo "# Resultado de la búsqueda de secretos en \`$ROOT\`"
echo "_Generado: $(date -Iseconds)_"
echo

if [ -s "$tmp" ]; then
  echo "## Coincidencias detectadas"
  echo
  echo '| Patrón | Ubicación |'
  echo '|---|---|'
  cat "$tmp"
  echo
  echo "**Acción:** si es la extracción, registra un hallazgo H-SEG (área secretos, severidad Alta) en 04 sin reproducir el valor y recomienda rotarlo y moverlo a la autenticación del connected system. Si es un entregable, enmascáralo antes de seguir."
  exit 1
else
  echo "## Sin coincidencias"
  echo "No se han detectado patrones de secretos en la ruta analizada."
  exit 0
fi
