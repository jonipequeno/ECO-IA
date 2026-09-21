"""Configuracao, roteamento de modelo e perfis de hardware."""

from __future__ import annotations

import pytest

from movili import agentes as quadro
from movili.config import carregar


def test_padrao_de_fabrica_e_qwen3_8b():
    cfg = carregar()
    for ident in quadro.REGISTRO:
        backend, modelo = cfg.modelo_do_agente(ident)
        assert backend == "ollama"
        assert modelo == "qwen3:8b", f"{ident} deveria usar qwen3:8b por padrao"


def test_todo_agente_tem_regra_de_roteamento():
    cfg = carregar()
    for ident in quadro.REGISTRO:
        assert ident in cfg.roteamento, f"{ident} sem regra em config/modelos.yaml"


def test_backends_declarados():
    cfg = carregar()
    assert {"ollama", "lmstudio", "simulado"} <= set(cfg.backends)
    assert cfg.ordem_fallback[0] == "ollama"
    assert "simulado" not in cfg.ordem_fallback  # nunca mascara backend fora do ar


def test_forcar_backend_e_modelo():
    cfg = carregar(backend_forcado="lmstudio", modelo_forcado="qwen3:14b")
    backend, modelo = cfg.modelo_do_agente("copy")
    assert backend == "lmstudio"
    assert modelo == "qwen3:14b"
    assert cfg.ordem_fallback[0] == "lmstudio"


def test_perfil_de_hardware_troca_os_modelos():
    cfg = carregar(perfil_hardware="especializado")
    assert cfg.modelo_do_agente("dev_backend")[1] == "qwen3-coder:30b-a3b"
    assert cfg.modelo_do_agente("financeiro")[1] == "deepseek-r1:14b"
    assert cfg.modelo_do_agente("juridico")[1] == "mistral-small:24b"
    # quem nao esta no preset herda o modelo padrao do perfil
    assert cfg.modelo_do_agente("cs")[1] in {"gemma3:12b", "qwen3:14b"}


def test_perfis_de_hardware_cobrem_o_quadro():
    cfg = carregar()
    esp = cfg.perfis_hardware["especializado"]["agentes"]
    faltando = [i for i in quadro.REGISTRO if i not in esp]
    assert not faltando, f"perfil especializado nao cobre: {faltando}"


def test_perfil_inexistente_da_erro_legivel():
    with pytest.raises(KeyError, match="nao existe"):
        carregar(perfil_hardware="turbo")


def test_catalogo_tem_grupos_e_recomendacoes():
    cfg = carregar()
    assert {"essenciais", "codigo", "raciocinio", "embeddings", "visao"} <= set(cfg.catalogo)
    for grupo, dados in cfg.catalogo.items():
        assert dados.get("descricao")
        for m in dados["modelos"]:
            assert m.get("nome") and m.get("usar_para"), f"{grupo}: modelo sem recomendacao"
