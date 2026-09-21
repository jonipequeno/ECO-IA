#!/usr/bin/env bash
# =====================================================================
# Instalacao do ecossistema Movili.
#   ./scripts/instalar.sh            # basico (CLI + Ollama)
#   ./scripts/instalar.sh completo   # + API + voz do OpenJarvis
# =====================================================================
set -euo pipefail

MODO="${1:-basico}"
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RAIZ"

echo "======================================================================"
echo " Movili Tecnologia - instalacao ($MODO)"
echo "======================================================================"

# --- Python ----------------------------------------------------------
if ! command -v python3 >/dev/null 2>&1; then
  echo "ERRO: python3 nao encontrado. Instale Python 3.10 ou superior."
  exit 1
fi
VERSAO=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo ">> Python $VERSAO detectado"
python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)' || {
  echo "ERRO: e necessario Python 3.10 ou superior."; exit 1; }

# --- ambiente virtual -------------------------------------------------
if [[ ! -d .venv ]]; then
  echo ">> criando ambiente virtual em .venv"
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

echo ">> instalando dependencias"
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
if [[ "$MODO" == "completo" ]]; then
  pip install --quiet -r requirements-api.txt
  pip install --quiet -r requirements-voz.txt || echo "   (voz opcional falhou - o Jarvis roda em modo texto)"
fi
pip install --quiet -e .

# --- pastas de trabalho ----------------------------------------------
mkdir -p data workspace
[[ -f .env ]] || { cp .env.example .env; echo ">> .env criado a partir do .env.example"; }

# --- Ollama -----------------------------------------------------------
echo ""
if command -v ollama >/dev/null 2>&1; then
  echo ">> Ollama encontrado"
  if ollama list >/dev/null 2>&1; then
    if ollama list | grep -q "qwen3:8b"; then
      echo ">> qwen3:8b ja esta instalado"
    else
      echo ">> baixando qwen3:8b (modelo padrao da casa)"
      ollama pull qwen3:8b || echo "   !! falhou; rode depois: ollama pull qwen3:8b"
    fi
  else
    echo "   !! o Ollama nao esta rodando. Abra outro terminal e rode: ollama serve"
  fi
else
  echo ">> Ollama nao encontrado."
  echo "   Instale em https://ollama.com/download e depois rode:"
  echo "     ollama serve"
  echo "     ./scripts/baixar_modelos.sh essenciais"
fi

echo ""
echo "======================================================================"
echo " Pronto. Ative o ambiente e confira o status:"
echo ""
echo "   source .venv/bin/activate"
echo "   movili status"
echo "   movili equipe"
echo "   movili fluxo novo-projeto \"app de logistica para transportadora\""
echo "   movili jarvis --diagnostico"
echo "======================================================================"
