#!/bin/bash

# Script para build e execução do ambiente Docker LAPOMED
# Seguindo BMAD-METHOD

echo "=== 🐳 Iniciando Dockerização LAPOMED ==="

# 1. Garantir que o banco de dados local tenha as permissões corretas (se existir)
if [ -f "db.sqlite3" ]; then
    chmod 666 db.sqlite3
fi

# 2. Build das imagens (Frontend Tailwind + Backend Django)
echo "-> 🛠️  Construindo imagens (isso pode demorar na primeira vez)..."
docker compose build

# 3. Rodar migrações dentro do container para garantir que o banco esteja ok
echo "-> 🔄 Rodando migrações do banco de dados..."
docker compose run --rm web uv run python manage.py migrate

# 4. Coletar arquivos estáticos
echo "-> 📂 Coletando arquivos estáticos..."
docker compose run --rm web uv run python manage.py collectstatic --noinput

# 5. Subir os containers
echo "-> 🚀 Subindo o sistema..."
docker compose up -d

echo "=== ✅ Sistema pronto em http://localhost:4008 ==="
echo "Dica: Use 'docker compose logs -f' para acompanhar o log em tempo real."
