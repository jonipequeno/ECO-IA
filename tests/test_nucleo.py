"""Mensagens, barramento, memoria e ferramentas."""

from __future__ import annotations

import pytest

from movili.core.barramento import Barramento
from movili.core.ferramentas import CaixaDeFerramentas, calcular
from movili.core.memoria import MemoriaCorporativa, MemoriaCurta
from movili.core.mensagem import Mensagem, Prioridade, Tipo


def test_mensagem_mantem_thread_na_resposta():
    original = Mensagem("comercial", "financeiro", "Precificar", "projeto X", tipo=Tipo.TAREFA)
    resposta = original.responder("financeiro", "R$ 180 mil")
    assert resposta.thread == original.thread
    assert resposta.destinatario == "comercial"
    assert resposta.assunto.startswith("Re:")


def test_mensagem_serializa_e_volta():
    m = Mensagem("copy", "seo", "Briefing", "texto", tipo=Tipo.PERGUNTA,
                 prioridade=Prioridade.ALTA, projeto="p1")
    volta = Mensagem.from_dict(m.to_dict())
    assert volta.id == m.id and volta.tipo is Tipo.PERGUNTA
    assert volta.prioridade is Prioridade.ALTA and volta.projeto == "p1"


def test_barramento_entrega_ao_destinatario():
    bus = Barramento()
    recebidas = []
    bus.assinar("seo", recebidas.append)
    bus.enviar("marketing", "seo", "Palavras-chave", "preciso do mapa")
    assert len(recebidas) == 1
    assert recebidas[0].remetente == "marketing"


def test_broadcast_alcanca_todos_menos_o_remetente():
    bus = Barramento()
    caixas = {i: [] for i in ("a", "b", "c")}
    for ident, caixa in caixas.items():
        bus.assinar(ident, caixa.append)
    bus.enviar("a", "*", "Comunicado", "reuniao as 10h", tipo=Tipo.INFORME)
    assert caixas["a"] == []
    assert len(caixas["b"]) == 1 and len(caixas["c"]) == 1


def test_barramento_filtra_por_thread_e_projeto():
    bus = Barramento()
    m = bus.enviar("a", "b", "x", "y", projeto="alpha")
    bus.enviar("b", "a", "z", "w", thread=m.thread, projeto="alpha")
    bus.enviar("a", "c", "outro", "coisa", projeto="beta")
    assert len(bus.thread(m.thread)) == 2
    assert len(bus.por_projeto("alpha")) == 2
    assert len(bus.por_projeto("beta")) == 1


def test_observador_ve_tudo():
    bus = Barramento()
    tudo = []
    bus.observar(tudo.append)
    bus.enviar("a", "b", "1", "1")
    bus.enviar("b", "a", "2", "2")
    assert len(tudo) == 2


def test_caixa_de_entrada_tem_teto():
    """Ninguem le a caixa no fluxo normal; sem teto ela guardaria a sessao toda."""
    bus = Barramento(limite_historico=50, limite_caixa=20)
    bus.assinar("seo", lambda m: None)
    for i in range(200):
        bus.enviar("copy", "seo", f"assunto {i}", "corpo")

    caixa = bus.caixa_de_entrada("seo")
    assert len(caixa) == 20
    assert caixa[-1].assunto == "assunto 199"      # descarta as antigas, nao as novas


def test_caixa_de_entrada_esvazia_ao_ler():
    bus = Barramento()
    bus.assinar("seo", lambda m: None)
    bus.enviar("copy", "seo", "x", "y")
    assert len(bus.caixa_de_entrada("seo")) == 1
    assert bus.caixa_de_entrada("seo") == []
    assert bus.caixa_de_entrada("ninguem") == []


def test_memoria_curta_respeita_a_janela():
    m = MemoriaCurta(max_turnos=4)
    for i in range(10):
        m.registrar("user", str(i))
    assert len(m) == 4
    assert m.como_mensagens()[-1]["content"] == "9"


def test_memoria_corporativa_persiste(tmp_path):
    mem = MemoriaCorporativa(tmp_path / "x.db")
    mem.lembrar("margem_minima", 0.35, autor="financeiro")
    assert mem.recordar("margem_minima") == 0.35
    assert mem.recordar("inexistente", "padrao") == "padrao"

    mem.salvar_entregavel("proj", "copy", "Landing", "texto final")
    itens = mem.entregaveis("proj")
    assert len(itens) == 1 and itens[0]["agente"] == "copy"
    mem.fechar()


def test_calculadora_resolve_e_barra_codigo():
    assert calcular("1200 * 320") == 384000.0
    assert calcular("(180000 - 99000) / 180000") == pytest.approx(0.45)
    with pytest.raises(ValueError):
        calcular("__import__('os').system('ls')")


def test_ferramenta_salva_e_le_no_workspace(tmp_path):
    caixa = CaixaDeFerramentas(tmp_path)
    assert "gravado" in caixa.executar("salvar_arquivo", {"caminho": "a/b.md", "conteudo": "oi"})
    assert caixa.executar("ler_arquivo", {"caminho": "a/b.md"}) == "oi"
    assert "a/b.md" in caixa.executar("listar_workspace", {})


def test_ferramenta_nao_escreve_fora_do_workspace(tmp_path):
    caixa = CaixaDeFerramentas(tmp_path / "ws")
    saida = caixa.executar("salvar_arquivo", {"caminho": "../fora.txt", "conteudo": "x"})
    assert saida.startswith("ERRO")
    assert not (tmp_path / "fora.txt").exists()


def test_extrair_chamada_de_ferramenta(tmp_path):
    caixa = CaixaDeFerramentas(tmp_path)
    texto = 'Vou calcular.\n```ferramenta\n{"ferramenta": "calcular", "args": {"expressao": "2+2"}}\n```'
    chamada = caixa.extrair_chamada(texto)
    assert chamada == {"ferramenta": "calcular", "args": {"expressao": "2+2"}}
    assert caixa.extrair_chamada("sem bloco nenhum") is None


def test_ferramenta_inexistente_devolve_erro(tmp_path):
    caixa = CaixaDeFerramentas(tmp_path)
    assert caixa.executar("hackear", {}).startswith("ERRO")
