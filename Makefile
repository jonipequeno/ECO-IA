# Atalhos do ecossistema Movili.
.PHONY: ajuda instalar modelos status equipe verificar teste memoria painel ponte jarvis api limpar

PY ?= python3

ajuda:
	@echo "Movili Tecnologia - ecossistema de agentes de IA"
	@echo ""
	@echo "  make instalar     instala dependencias e prepara o ambiente"
	@echo "  make modelos      baixa os modelos essenciais do Ollama"
	@echo "  make verificar    checa estrutura, backends e modelos faltando"
	@echo "  make status       mostra Ollama, LM Studio e o roteamento"
	@echo "  make equipe       mostra o organograma"
	@echo "  make teste        roda a suite de testes (backend simulado)"
	@echo "  make memoria      estado da memoria semantica (RAG)"
	@echo "  make painel       painel web ao vivo na porta 8080"
	@echo "  make jarvis       abre a conversa por voz (OpenJarvis)"
	@echo "  make ponte        sobe a ponte OpenAI-compativel na porta 8123"
	@echo "  make api          sobe a API HTTP na porta 8000"
	@echo "  make limpar       remove caches e artefatos de execucao"

instalar:
	./scripts/instalar.sh completo

modelos:
	./scripts/baixar_modelos.sh essenciais

verificar:
	$(PY) scripts/verificar.py

status:
	$(PY) -m movili status

equipe:
	$(PY) -m movili equipe

teste:
	$(PY) -m pytest tests -q

memoria:
	$(PY) -m movili memoria status

painel:
	$(PY) -m movili painel

jarvis:
	$(PY) -m movili jarvis

ponte:
	$(PY) -m movili ponte

api:
	$(PY) -m movili api

limpar:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache build dist *.egg-info
