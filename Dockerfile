FROM python:3.12-slim

LABEL org.opencontainers.image.title="Movili Tecnologia - Ecossistema de Agentes"
LABEL org.opencontainers.image.description="Empresa de software operada por agentes de IA locais (Ollama / LM Studio)"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependencias primeiro, para aproveitar o cache de camada.
COPY requirements.txt requirements-api.txt ./
RUN pip install --no-cache-dir -r requirements-api.txt

COPY pyproject.toml README.md ./
COPY movili/ ./movili/
COPY config/ ./config/
COPY scripts/ ./scripts/
RUN pip install --no-cache-dir -e . && mkdir -p data workspace

EXPOSE 8000 8123

CMD ["movili", "status"]
