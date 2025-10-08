#!/bin/bash

# =========================================================
# 🚀 Script Visual de Execução Local (Flask + Gunicorn)
# =========================================================
# Autor: Aryan Adrix (ajustado por ChatGPT)
# Compatível com: macOS e Linux
# Funções:
#   - Liberta porta ocupada (8000)
#   - Ativa o ambiente virtual (.venv)
#   - Inicia o Gunicorn com reload automático
# =========================================================

# 🌍 Configurações
PORT=8000
APP="app:create_app()"
VENV=".venv/bin/activate"

# 🎨 Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
RESET='\033[0m'

echo ""
echo -e "${CYAN}🔍 Verificando se a porta ${YELLOW}$PORT${CYAN} está ocupada...${RESET}"
PID=$(lsof -ti :$PORT)

if [ -n "$PID" ]; then
  echo -e "${RED}⚠️  Porta $PORT ocupada pelo processo $PID. Encerrando...${RESET}"
  kill -9 $PID
  echo -e "${GREEN}✅ Porta $PORT liberada com sucesso.${RESET}"
else
  echo -e "${GREEN}✅ Porta $PORT já está livre.${RESET}"
fi

echo ""
echo -e "${CYAN}🧠 Ativando ambiente virtual...${RESET}"
if [ -f "$VENV" ]; then
  source $VENV
  echo -e "${GREEN}✅ Ambiente virtual ativado.${RESET}"
else
  echo -e "${RED}❌ Ambiente virtual não encontrado. Crie com:${RESET}"
  echo -e "${YELLOW}python3 -m venv .venv${RESET}"
  exit 1
fi

echo ""
echo -e "${CYAN}🔥 Iniciando aplicação Flask com Gunicorn...${RESET}"
sleep 1
echo ""

gunicorn "$APP" --bind 0.0.0.0:$PORT --reload

echo ""
echo -e "${GREEN}✨ Aplicação rodando com sucesso em:${RESET} ${YELLOW}http://127.0.0.1:$PORT${RESET}"
echo ""