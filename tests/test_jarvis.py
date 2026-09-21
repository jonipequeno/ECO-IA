"""OpenJarvis: interpretacao de intencao, conversa e ponte OpenAI."""

from __future__ import annotations

import json

import pytest

from movili.jarvis.conversa import Jarvis
from movili.jarvis.ponte import _modelos_expostos
from movili.jarvis.voz import SemFala, Teclado, detectar_escuta, detectar_fala, diagnostico


@pytest.fixture
def jarvis(eco):
    return Jarvis(eco, frases=3)


def test_interpreta_comandos_basicos(jarvis):
    assert jarvis.interpretar("sair")["acao"] == "sair"
    assert jarvis.interpretar("ajuda")["acao"] == "ajuda"
    assert jarvis.interpretar("quem trabalha aqui")["acao"] == "equipe"


def test_interpreta_mencao_direta_por_id(jarvis):
    intencao = jarvis.interpretar("@financeiro qual a margem minima?")
    assert intencao["acao"] == "agente" and intencao["alvo"] == "financeiro"


def test_interpreta_chamada_pelo_primeiro_nome(jarvis):
    intencao = jarvis.interpretar("chama a Patricia e pergunta o preco por hora")
    assert intencao["acao"] == "agente" and intencao["alvo"] == "financeiro"


def test_interpreta_pedido_de_reuniao(jarvis):
    assert jarvis.interpretar("convoca uma reuniao sobre o mercado de saude")["acao"] == "reuniao"


def test_mencao_solta_a_id_ambiguo_nao_vira_chamada(jarvis):
    """'produto' e palavra comum: so vale como pessoa com '@' ou verbo de chamada."""
    assert jarvis.interpretar("o produto novo vende bem?")["acao"] != "agente"
    assert jarvis.interpretar("@produto o produto novo vende bem?")["alvo"] == "produto"
    assert jarvis.interpretar("fala com o produto sobre isso")["alvo"] == "produto"


def test_interpreta_fluxo_por_palavra_chave(jarvis):
    intencao = jarvis.interpretar("monta uma proposta para um app de logistica")
    assert intencao["acao"] == "fluxo" and intencao["alvo"] == "novo-projeto"

    intencao = jarvis.interpretar("quero uma campanha para o produto novo")
    assert intencao["acao"] == "fluxo" and intencao["alvo"] == "campanha"


def test_pergunta_aberta_cai_na_triagem(jarvis):
    assert jarvis.interpretar("como anda a empresa esse mes?")["acao"] == "triagem"


def test_responder_mantem_historico(jarvis):
    jarvis.responder("@copy escreva uma headline")
    assert len(jarvis.historico) == 2
    assert jarvis.historico[0].quem == "voce"
    assert jarvis.historico[1].quem == "jarvis"
    assert jarvis.ultimo_agente == "copy"


def test_resposta_pede_estilo_falado(jarvis, eco):
    jarvis.responder("@seo me da um resumo do mapa de palavras-chave")
    texto = "\n".join(m["content"] for c in eco.roteador.provedor("simulado").chamadas for m in c)
    assert "Voce esta FALANDO" in texto
    assert "Sem markdown" in texto


def test_equipe_falada_cita_os_setores(jarvis):
    fala = jarvis.responder("quem trabalha aqui")["fala"]
    assert "engenharia" in fala.lower()
    assert "Rafael" in fala or "Camila" in fala


def test_saida_encerra(jarvis):
    assert jarvis.responder("tchau")["acao"] == "sair"


# --- voz --------------------------------------------------------------
def test_deteccao_de_voz_sempre_devolve_algo():
    assert detectar_fala("texto").nome == "texto"
    assert isinstance(detectar_fala("texto"), SemFala)
    assert detectar_escuta("teclado").nome == "teclado"
    assert isinstance(detectar_escuta("teclado"), Teclado)


def test_diagnostico_lista_os_quatro_motores():
    d = diagnostico()
    assert set(d) == {"tts_piper", "tts_sistema", "stt_faster_whisper", "stt_whisper_cpp"}
    assert all("disponivel" in v for v in d.values())


# --- ponte ------------------------------------------------------------
def test_ponte_expoe_todos_os_agentes_como_modelos():
    modelos = {m["id"] for m in _modelos_expostos()}
    assert "movili-jarvis" in modelos
    assert "movili-empresa" in modelos
    assert "movili-financeiro" in modelos
    assert "movili-socio_estrategia" in modelos


def test_ponte_responde_no_formato_openai(eco_pequeno):
    """Valida o despacho sem subir socket: chama o handler diretamente."""
    from movili.jarvis.ponte import _Handler

    _Handler.eco = eco_pequeno
    _Handler.jarvis = Jarvis(eco_pequeno, frases=3)
    handler = _Handler.__new__(_Handler)

    texto = handler._despachar("movili-financeiro", "qual a margem minima?")
    assert isinstance(texto, str) and texto

    corpo = {
        "id": "x", "object": "chat.completion",
        "choices": [{"index": 0, "message": {"role": "assistant", "content": texto},
                     "finish_reason": "stop"}],
    }
    assert json.loads(json.dumps(corpo))["choices"][0]["message"]["content"] == texto
