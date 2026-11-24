#!/usr/bin/env bash
# Lanzador del Sistema de Control de Inventario (Linux / macOS).
set -euo pipefail
cd "$(dirname "$0")"

PY_CMD=""
for candidato in python3 python; do
    if command -v "$candidato" >/dev/null 2>&1; then PY_CMD="$candidato"; break; fi
done
if [ -z "$PY_CMD" ]; then
    echo "[ERROR] No se encontro Python 3. Instalalo antes de continuar." >&2
    exit 1
fi

if [ ! -x ".venv/bin/python" ]; then
    echo "[1/3] Creando el entorno virtual .venv ..."
    "$PY_CMD" -m venv .venv
else
    echo "[1/3] Entorno virtual ya existente."
fi

echo "[2/3] Instalando dependencias ..."
.venv/bin/python -m pip install --quiet --disable-pip-version-check -r requirements.txt

echo "[3/3] Arrancando el servidor en http://127.0.0.1:5000"
echo "      Para detenerlo, pulsa Ctrl+C."
.venv/bin/python app.py
