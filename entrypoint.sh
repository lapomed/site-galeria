#!/bin/bash

# Encerra o script se algum comando falhar
set -e

echo "=== 🚀 Iniciando Entrypoint LAPOMED ==="

# 1. Migrações do banco de dados
echo "-> 🔄 Rodando migrações..."
uv run python manage.py migrate --noinput

# 2. Coletar arquivos estáticos
echo "-> 📂 Coletando arquivos estáticos..."
uv run python manage.py collectstatic --noinput

# 3. Iniciar o servidor (usando porta definida ou default 4008)
PORT=${PORT:-4008}
echo "-> 🚀 Iniciando Gunicorn na porta $PORT..."

# Gunicorn para produção, ou runserver para dev se DEBUG for true
if [ "$DEBUG" = "True" ] || [ "$DEBUG" = "true" ] || [ "$DEBUG" = "1" ]; then
    echo "MODO DEBUG ATIVO: Usando runserver"
    exec uv run python manage.py runserver 0.0.0.0:$PORT
else
    echo "MODO PRODUÇÃO: Usando Gunicorn"
    exec uv run gunicorn lapomed_gallery.wsgi:application --bind 0.0.0.0:$PORT --workers 3
fi
