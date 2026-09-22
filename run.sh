#!/usr/bin/env bash
set -e

# Diretorio base do projeto
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# 1. Verifica ou cria o ambiente virtual
if [ ! -d ".venv" ]; then
    echo "[SETUP] Criando ambiente virtual em .venv..."
    python3 -m venv .venv
    echo "[SETUP] Instalando dependencias..."
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -r requirements.txt
fi

# 2. Verifica se o .env existe
if [ ! -f ".env" ]; then
    echo "[SETUP] Criando arquivo .env a partir de .env.example..."
    cp .env.example .env
    echo "[AVISO] Preencha suas chaves no arquivo .env antes de rodar o modo conectado ao Telegram."
    echo "[AVISO] Iniciando modo simulacao por padrao..."
    exec .venv/bin/python main.py --mode simulate "$@"
fi

# 3. Executa a aplicacao passando quaisquer argumentos adicionais
exec .venv/bin/python main.py "$@"
