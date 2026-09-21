"""Fixtures comuns dos testes. Tudo roda no backend simulado - sem modelo real."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from movili.config import carregar  # noqa: E402
from movili.core.orquestrador import Ecossistema  # noqa: E402


@pytest.fixture
def config(tmp_path):
    cfg = carregar(backend_forcado="simulado")
    cfg.caminho_db = str(tmp_path / "teste.db")
    cfg.workspace = str(tmp_path / "workspace")
    # o padrao aponta para o cofre de verdade, relativo ao diretorio atual
    cfg.obsidian = str(tmp_path / "cofre")
    return cfg


@pytest.fixture
def eco(config):
    ecossistema = Ecossistema(config, verboso=False)
    yield ecossistema
    ecossistema.encerrar()


@pytest.fixture
def eco_pequeno(config):
    """Ecossistema reduzido: mais rapido para testes de encanamento."""
    ecossistema = Ecossistema(
        config, verboso=False, somente=["diretor", "dev_backend", "financeiro", "copy"]
    )
    yield ecossistema
    ecossistema.encerrar()
