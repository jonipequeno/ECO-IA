"""Camada de LLM: normalizacao, fallback e limpeza de raciocinio."""

from __future__ import annotations

import pytest

from movili.llm.base import LLMIndisponivel, Mensagem, limpar_raciocinio
from movili.llm.lmstudio import LMStudioProvider
from movili.llm.ollama import OllamaProvider
from movili.llm.router import ConfigBackend, ProvedorSimulado, RoteadorLLM


def test_limpa_bloco_think_do_qwen3():
    bruto = "<think>o usuario quer X, vou responder Y</think>\nResposta final."
    assert limpar_raciocinio(bruto) == "Resposta final."
    assert limpar_raciocinio("sem think") == "sem think"
    # bloco aberto sem fechar nao pode vazar raciocinio
    assert "usuario" not in limpar_raciocinio("<think>usuario quer")


def test_normalizacao_aceita_dataclass_e_dict():
    normalizadas = OllamaProvider._normalizar(
        [Mensagem("system", "a"), {"role": "user", "content": "b"}]
    )
    assert normalizadas == [{"role": "system", "content": "a"}, {"role": "user", "content": "b"}]
    with pytest.raises(TypeError):
        OllamaProvider._normalizar(["texto solto"])


@pytest.mark.parametrize("raciocinio", [False, True])
def test_ollama_manda_o_think_configurado(monkeypatch, raciocinio):
    """Sem 'think': false o qwen3 gera o raciocinio que limpar_raciocinio() descarta."""
    enviado = {}

    def post(_self, rota, payload):
        enviado.update(payload)
        return {"message": {"content": "ok"}, "model": payload["model"]}

    monkeypatch.setattr(OllamaProvider, "_post", post)
    provedor = ConfigBackend(tipo="ollama", base_url="http://x", modelo_padrao="qwen3:4b",
                             raciocinio=raciocinio).construir()
    provedor.chat([{"role": "user", "content": "oi"}])
    assert enviado["think"] is raciocinio


def test_urls_sao_normalizadas():
    assert OllamaProvider("http://localhost:11434/", "qwen3:8b").base_url == "http://localhost:11434"
    assert LMStudioProvider("http://localhost:1234/v1/", "qwen3-8b").base_url == "http://localhost:1234/v1"


def test_provedor_simulado_identifica_a_persona():
    prov = ProvedorSimulado()
    r = prov.chat([
        {"role": "system", "content": "Voce e Patricia Souza, Controller."},
        {"role": "user", "content": "precifique o projeto"},
    ])
    assert "SIMULADA" in r.conteudo
    assert "Patricia" in r.conteudo
    assert len(prov.chamadas) == 1


def test_roteador_cai_para_o_proximo_backend():
    backends = {
        "quebrado": ConfigBackend("ollama", "http://127.0.0.1:1", "x", timeout=1),
        "simulado": ConfigBackend("simulado", "", "simulado"),
    }
    roteador = RoteadorLLM(backends, ["quebrado", "simulado"], tentativas=1)
    resposta = roteador.gerar([{"role": "user", "content": "oi"}], agente="teste")
    assert resposta.provedor == "simulado"


def test_roteador_erra_claro_quando_nada_responde():
    backends = {"quebrado": ConfigBackend("ollama", "http://127.0.0.1:1", "x", timeout=1)}
    roteador = RoteadorLLM(backends, ["quebrado"], tentativas=1)
    with pytest.raises(LLMIndisponivel, match="Ollama"):
        roteador.gerar([{"role": "user", "content": "oi"}])


def test_roteador_contabiliza_uso_por_agente():
    roteador = RoteadorLLM({"simulado": ConfigBackend("simulado", "", "simulado")})
    roteador.gerar([{"role": "user", "content": "a"}], agente="copy")
    roteador.gerar([{"role": "user", "content": "b"}], agente="copy")
    assert roteador.metricas["copy"]["chamadas"] == 2


def test_backend_desconhecido_da_erro():
    with pytest.raises(ValueError, match="desconhecido"):
        ConfigBackend("inventado", "http://x", "y").construir()
