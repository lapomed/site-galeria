#!/bin/bash

# Script de inicialização do ambiente de desenvolvimento
# Executa o Tailwind CSS (watch) e o servidor Django em paralelo

# Função para encerrar processos filhos ao sair
cleanup() {
    echo ""
    echo "Encerrando serviços..."
    # Mata todos os jobs em background
    kill $(jobs -p) 2>/dev/null
}

# Configura o trap para executar cleanup ao receber SIGINT (Ctrl+C) ou EXIT
trap cleanup SIGINT EXIT

echo "=== Inicializando LAPOMED DEV ==="

# 1. Iniciar o Tailwind Watcher
if [ -d "lapomed/static_src" ]; then
    echo "-> Iniciando Tailwind Watcher (npm run dev)..."
    # Entra no diretório, roda o comando em background e volta
    (cd lapomed/static_src && npm run dev) &
else
    echo "ERRO: Diretório 'lapomed/static_src' não encontrado."
    exit 1
fi

# Pequena pausa para o output do npm não misturar imediatamente com o do Django
sleep 2

# 2. Iniciar o Servidor Django
echo "-> Iniciando Django Server..."
python manage.py runserver

# O script aguarda o término do comando python (que roda em foreground)
# Ao encerrar o Django (Ctrl+C), o trap é acionado e mata o processo do npm
