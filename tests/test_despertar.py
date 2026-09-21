"""Palavra de despertar do OpenJarvis: casamento tolerante e detectores."""

from __future__ import annotations

import pytest

from movili.jarvis.despertar import (
    PALAVRA_PADRAO,
    SEMELHANCA_MINIMA,
    DespertarOpenWakeWord,
    DespertarPorTecla,
    DespertarPorTranscricao,
    contem_palavra,
    detectar_despertar,
    normalizar,
    remover_palavra,
)
from movili.jarvis.voz import MotorEscuta, Teclado


# ---------------------------------------------------------------- normalizacao
def test_normalizar_tira_acento_caixa_e_pontuacao():
    assert normalizar("JÁRVIS!") == "jarvis"
    assert normalizar("Olá, Jarvis...") == "ola  jarvis"
    assert normalizar("ação") == "acao"
    assert normalizar("") == ""


# ---------------------------------------------------------------- casamento
@pytest.mark.parametrize("fala", [
    "jarvis",
    "Jarvis",
    "JÁRVIS!",
    "jarvis, chama a Patricia",
    "ei jarvis tudo bem",
    "jarves",        # confusoes plausiveis do Whisper em pt-BR
    "darvis",
    "javis",
    "jarviz",
    "jarbis",
])
def test_acorda_com_o_nome_e_suas_confusoes(fala):
    assert contem_palavra(fala, "jarvis"), f"deveria acordar com {fala!r}"


@pytest.mark.parametrize("fala", [
    "jardins",       # 0.769 de semelhanca: o falso positivo que motivou o limiar
    "jantar",
    "jarra",
    "jarbas",
    "javascript",
    "arquivos",
    "servico",
    "chama a Patricia",
    "",
])
def test_nao_acorda_com_palavra_comum(fala):
    assert not contem_palavra(fala, "jarvis"), f"nao deveria acordar com {fala!r}"


def test_limiar_foi_escolhido_por_medicao():
    """Entre 0.769 ('jardins') e 0.833 (pior verdadeiro mantido). Ver o comentario no modulo.

    Acordar sozinho incomoda mais do que perder uma chamada, entao o corte
    pende para o conservador.
    """
    assert 0.769 < SEMELHANCA_MINIMA <= 0.833
    assert not contem_palavra("jardins", "jarvis")
    assert contem_palavra("jarves", "jarvis")


def test_palavra_de_varios_termos():
    assert contem_palavra("ola movili, bom dia", "ola movili")
    assert contem_palavra("ola movilli", "ola movili")       # erro de STT
    assert not contem_palavra("ola pessoal", "ola movili")


def test_palavra_vazia_nunca_casa():
    assert not contem_palavra("qualquer coisa", "")


def test_limiar_customizado():
    assert contem_palavra("jardins", "jarvis", minimo=0.7)
    assert not contem_palavra("jarves", "jarvis", minimo=0.99)


# ---------------------------------------------------------------- extracao
@pytest.mark.parametrize("fala,esperado", [
    ("Jarvis, chama a Patricia", "chama a Patricia"),
    ("jarves monta uma proposta", "monta uma proposta"),
    ("JÁRVIS! quem trabalha aqui", "quem trabalha aqui"),
    ("Jarvis", ""),
    ("jarvis.", ""),
    ("chama a Patricia", "chama a Patricia"),   # sem o nome, devolve inteiro
    ("", ""),
])
def test_remover_o_nome_do_comando(fala, esperado):
    assert remover_palavra(fala, "jarvis") == esperado


def test_remover_preserva_acento_do_comando():
    """A normalizacao e so para comparar; o comando volta como foi dito."""
    assert remover_palavra("Jarvis, chama a Patrícia", "jarvis") == "chama a Patrícia"


def test_remover_palavra_de_varios_termos():
    assert remover_palavra("ola movili, monta a proposta", "ola movili") == "monta a proposta"


# ---------------------------------------------------------------- detectores
class _EscutaFalsa(MotorEscuta):
    """Devolve falas roteirizadas, e depois silencio."""

    nome = "falsa"
    disponivel = True

    def __init__(self, falas: list[str]) -> None:
        self.falas = list(falas)
        self.chamadas = 0

    def ouvir(self, segundos: int = 8) -> str:
        self.chamadas += 1
        return self.falas.pop(0) if self.falas else ""


def test_transcricao_ignora_ruido_ate_ouvir_o_nome():
    escuta = _EscutaFalsa(["silencio", "conversa qualquer", "jarvis, chama a Patricia"])
    detector = DespertarPorTranscricao(escuta, "jarvis")
    assert detector.disponivel
    assert detector.esperar(timeout=10) == "chama a Patricia"
    assert escuta.chamadas == 3


def test_transcricao_devolve_none_no_timeout():
    detector = DespertarPorTranscricao(_EscutaFalsa([]), "jarvis")
    assert detector.esperar(timeout=0.01) is None


def test_transcricao_nao_se_oferece_com_teclado():
    """Quem digita nao precisa de palavra de despertar."""
    assert not DespertarPorTranscricao(Teclado(), "jarvis").disponivel


def test_tecla_tira_o_nome_do_que_foi_digitado(monkeypatch):
    """Digitar 'jarvis' e so acordar - nao mandar 'jarvis' ao CEO."""
    detector = DespertarPorTecla("jarvis")
    monkeypatch.setattr("builtins.input", lambda _="": "jarvis")
    assert detector.esperar() == ""
    monkeypatch.setattr("builtins.input", lambda _="": "jarvis, quem trabalha aqui")
    assert detector.esperar() == "quem trabalha aqui"
    monkeypatch.setattr("builtins.input", lambda _="": "")
    assert detector.esperar() == ""


def test_tecla_encerra_com_fim_de_entrada(monkeypatch):
    def explode(_=""):
        raise EOFError

    monkeypatch.setattr("builtins.input", explode)
    assert DespertarPorTecla().esperar() is None


def test_deteccao_cai_para_tecla_sem_microfone():
    detector = detectar_despertar(Teclado(), "jarvis")
    assert isinstance(detector, DespertarPorTecla)
    assert detector.palavra == "jarvis"


def test_deteccao_respeita_o_preferido():
    assert detectar_despertar(Teclado(), "jarvis", "tecla").nome == "tecla"
    escuta = _EscutaFalsa([])
    assert detectar_despertar(escuta, "jarvis", "transcricao").nome == "transcricao"


def test_openwakeword_ausente_nao_quebra():
    """A dependencia e opcional: sem ela o detector so se declara indisponivel."""
    detector = DespertarOpenWakeWord()
    assert detector.disponivel in {True, False}
    if not detector.disponivel:
        assert detector.esperar(timeout=0.01) is None


# ---------------------------------------------------------------- sessao
def test_sessao_sem_palavra_nao_monta_detector(eco_pequeno):
    from movili.jarvis.sessao import SessaoJarvis

    sessao = SessaoJarvis(eco_pequeno, tts="texto", stt="teclado")
    assert sessao.detector is None
    assert "despertar" not in sessao.modo


def test_sessao_com_palavra_monta_detector(eco_pequeno):
    from movili.jarvis.sessao import SessaoJarvis

    sessao = SessaoJarvis(eco_pequeno, tts="texto", stt="teclado",
                          palavra_despertar="jarvis", despertar="tecla")
    assert sessao.detector is not None
    assert sessao.palavra == "jarvis"
    assert "despertar=tecla:'jarvis'" in sessao.modo


def test_palavra_padrao_e_jarvis():
    assert PALAVRA_PADRAO == "jarvis"


# ---------------------------------------------------------------- CLI
def test_cli_palavra_e_opcional_com_valor_padrao():
    """--palavra sozinho liga com 'jarvis'; sem a flag, o modo nem existe."""
    from movili.cli import construir_parser

    parser = construir_parser()
    assert parser.parse_args(["jarvis"]).palavra is None
    assert parser.parse_args(["jarvis", "--palavra"]).palavra == "jarvis"
    assert parser.parse_args(["jarvis", "--palavra", "movili"]).palavra == "movili"
