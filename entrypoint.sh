#!/bin/bash

# Encerra o script se algum comando falhar
set -e

echo "=== 🚀 Iniciando Entrypoint LAPOMED ==="

# Usa o Python do .venv criado pelo `uv sync --frozen --no-dev` no Dockerfile.
# Evita que `uv run` resolva dependencias em runtime e baixe playwright (~45MiB)
# a cada restart do container.
PYTHON=/app/.venv/bin/python
GUNICORN=/app/.venv/bin/gunicorn

# 1. Migrações do banco de dados
echo "-> 🔄 Rodando migrações..."
"$PYTHON" manage.py migrate --noinput

# 2. Coletar arquivos estáticos
echo "-> 📂 Coletando arquivos estáticos..."
"$PYTHON" manage.py collectstatic --noinput

# 3. Iniciar o servidor (usando porta definida ou default 4008)
PORT=${PORT:-4008}
echo "-> 🚀 Iniciando Gunicorn na porta $PORT..."

# Gunicorn para produção, ou runserver para dev se DEBUG for true
if [ "$DEBUG" = "True" ] || [ "$DEBUG" = "true" ] || [ "$DEBUG" = "1" ]; then
    echo "MODO DEBUG ATIVO: Usando runserver"
    exec "$PYTHON" manage.py runserver 0.0.0.0:$PORT
else
    echo "MODO PRODUÇÃO: Usando Gunicorn"
    exec "$GUNICORN" lapomed_gallery.wsgi:application \
        --bind 0.0.0.0:$PORT \
        --workers 3 \
        --timeout 300 \
        --graceful-timeout 60 \
        --limit-request-line 0 \
        --limit-request-field_size 0
fi
