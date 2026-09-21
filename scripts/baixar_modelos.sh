#!/usr/bin/env bash
# =====================================================================
# Baixa os modelos abertos do Ollama usados pelo ecossistema Movili.
#
#   ./scripts/baixar_modelos.sh                 # grupo essenciais
#   ./scripts/baixar_modelos.sh especializado   # o melhor por funcao (24-32 GB)
#   ./scripts/baixar_modelos.sh codigo          # so os modelos de codigo
#   ./scripts/baixar_modelos.sh todos           # o catalogo inteiro (~200 GB)
#   ./scripts/baixar_modelos.sh --listar        # mostra os grupos
#
# Modelos que nao existirem mais no registro sao pulados com aviso, sem
# derrubar o script.
# =====================================================================
set -uo pipefail

GRUPO="${1:-essenciais}"
OLLAMA_BIN="${OLLAMA_BIN:-ollama}"

essenciais=(
  "qwen3:8b"
  "qwen2.5-coder:7b"
  "nomic-embed-text"
)

leve=(
  "qwen3:4b"
  "qwen2.5-coder:7b"
  "gemma3:4b"
  "nomic-embed-text"
)

equilibrado=(
  "qwen3:8b"
  "qwen2.5-coder:14b"
  "qwen2.5-coder:7b"
  "deepseek-r1:8b"
  "gemma3:12b"
  "mistral-nemo:12b"
  "nomic-embed-text"
)

especializado=(
  "qwen3:14b"
  "qwen3:8b"
  "qwen3-coder:30b-a3b"
  "qwen2.5-coder:14b"
  "deepseek-r1:14b"
  "mistral-small:24b"
  "mistral-nemo:12b"
  "gemma3:12b"
  "nomic-embed-text"
)

maximo=(
  "qwen3:32b"
  "qwen3-coder:30b-a3b"
  "qwen2.5-coder:32b"
  "deepseek-r1:32b"
  "llama3.3:70b"
  "mistral-small:24b"
  "gemma3:27b"
  "bge-m3"
)

codigo=(
  "qwen2.5-coder:1.5b"
  "qwen2.5-coder:7b"
  "qwen2.5-coder:14b"
  "qwen2.5-coder:32b"
  "qwen3-coder:30b-a3b"
  "deepseek-coder-v2:16b"
  "codegemma:7b"
  "starcoder2:7b"
  "sqlcoder:15b"
)

generalistas=(
  "qwen3:0.6b" "qwen3:1.7b" "qwen3:4b" "qwen3:8b" "qwen3:14b"
  "qwen3:30b-a3b" "qwen3:32b"
  "gemma3:4b" "gemma3:12b" "gemma3:27b"
  "llama3.1:8b" "llama3.2:3b"
  "mistral-nemo:12b" "mistral-small:24b"
  "phi4:14b" "granite3.3:8b"
)

raciocinio=(
  "deepseek-r1:8b" "deepseek-r1:14b" "deepseek-r1:32b" "qwq:32b"
)

embeddings=(
  "nomic-embed-text" "mxbai-embed-large" "bge-m3" "all-minilm"
)

visao=(
  "llama3.2-vision:11b" "llava:13b" "minicpm-v:8b" "moondream"
)

leves=(
  "llama3.2:1b" "smollm2:1.7b" "gemma3:1b"
)

if [[ "$GRUPO" == "--listar" || "$GRUPO" == "-l" ]]; then
  echo "Grupos disponiveis:"
  echo "  essenciais      minimo para rodar (3 modelos, ~12 GB)"
  echo "  leve            notebook de 8 GB"
  echo "  equilibrado     maquina de 16 GB"
  echo "  especializado   o melhor modelo por funcao (24-32 GB)"
  echo "  maximo          workstation 48 GB+"
  echo "  codigo | generalistas | raciocinio | embeddings | visao | leves"
  echo "  todos           tudo acima"
  exit 0
fi

if ! command -v "$OLLAMA_BIN" >/dev/null 2>&1; then
  echo "ERRO: '$OLLAMA_BIN' nao encontrado no PATH."
  echo "Instale em https://ollama.com/download e rode 'ollama serve'."
  exit 1
fi

if ! "$OLLAMA_BIN" list >/dev/null 2>&1; then
  echo "ERRO: o Ollama esta instalado mas nao responde. Rode 'ollama serve' em outro terminal."
  exit 1
fi

case "$GRUPO" in
  todos)
    MODELOS=("${generalistas[@]}" "${raciocinio[@]}" "${codigo[@]}"
             "${embeddings[@]}" "${visao[@]}" "${leves[@]}")
    ;;
  essenciais|leve|equilibrado|especializado|maximo|codigo|generalistas|raciocinio|embeddings|visao|leves)
    declare -n ref="$GRUPO"
    MODELOS=("${ref[@]}")
    ;;
  *)
    echo "Grupo desconhecido: $GRUPO"
    echo "Use: ./scripts/baixar_modelos.sh --listar"
    exit 1
    ;;
esac

# remove duplicados preservando a ordem
declare -A vistos=()
UNICOS=()
for m in "${MODELOS[@]}"; do
  [[ -n "${vistos[$m]:-}" ]] && continue
  vistos[$m]=1
  UNICOS+=("$m")
done

echo "======================================================================"
echo " Movili - baixando o grupo '$GRUPO' (${#UNICOS[@]} modelos)"
echo "======================================================================"

OK=0; FALHOU=0; PULADOS=()
for modelo in "${UNICOS[@]}"; do
  echo ""
  echo ">> $modelo"
  if "$OLLAMA_BIN" pull "$modelo"; then
    OK=$((OK + 1))
  else
    FALHOU=$((FALHOU + 1))
    PULADOS+=("$modelo")
    echo "   !! falhou (tag inexistente, sem espaco em disco ou sem rede). Seguindo."
  fi
done

echo ""
echo "======================================================================"
echo " Concluido: $OK baixados, $FALHOU falharam."
if ((FALHOU > 0)); then
  echo " Nao baixados: ${PULADOS[*]}"
  echo " Confira a tag exata em https://ollama.com/library"
fi
echo "======================================================================"
echo ""
"$OLLAMA_BIN" list
