"""Painel web: estado, validacao de entrada, fila de trabalho e eventos.

Os testes chamam o handler e a Central diretamente, sem abrir socket: o que
importa e o contrato das rotas e o comportamento da fila, nao o transporte.
"""

from __future__ import annotations

import json
import queue
import time

import pytest

from movili.painel.servidor import WEB, Central, TarefaInvalida, _Handler


@pytest.fixture
def central(eco_pequeno):
    c = Central(eco_pequeno)
    yield c
    # sem isto o worker sobrevive ao teardown do eco e escreve em banco fechado
    c.encerrar(timeout=30)


def _esperar(central: Central, tarefa_id: str, limite: float = 15.0) -> str:
    """Espera a tarefa sair da fila do worker."""
    fim = time.monotonic() + limite
    while time.monotonic() < fim:
        estado = central.tarefas[tarefa_id].estado
        if estado in {"concluida", "erro"}:
            return estado
        time.sleep(0.05)
    return central.tarefas[tarefa_id].estado


# --- pagina -----------------------------------------------------------
def test_html_do_painel_viaja_com_o_pacote():
    arquivo = WEB / "index.html"
    assert arquivo.is_file(), "movili/painel/web/index.html precisa existir no pacote"
    html = arquivo.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in html
    assert "/api/rede/eventos" in html and "/api/executar" in html
    assert 'lang="pt-BR"' in html


def test_painel_classico_segue_disponivel():
    """A tela anterior (feed, fluxos, reunioes, rotinas) fica em /classico."""
    html = (WEB / "classico.html").read_text(encoding="utf-8")
    assert "/api/eventos" in html and "/api/executar" in html


def test_pacote_declara_o_html_como_dado():
    """Sem package-data o HTML nao entra no wheel e o painel devolve 500."""
    from pathlib import Path

    toml = Path("pyproject.toml").read_text(encoding="utf-8")
    assert "[tool.setuptools.package-data]" in toml
    assert "web/*.html" in toml


# --- estado -----------------------------------------------------------
def test_estado_traz_equipe_fluxos_e_memoria(central):
    estado = central.estado()
    assert estado["empresa"]
    assert estado["setores"] and estado["fluxos"]
    pessoas = [p for gente in estado["setores"].values() for p in gente]
    assert len(pessoas) == 20                      # o organograma inteiro aparece
    assert sum(1 for p in pessoas if p["ativo"]) == 4   # so 4 estao ativos no eco_pequeno
    assert all({"id", "nome", "cargo", "ativo", "modelo"} <= set(p) for p in pessoas)
    assert "ligada" in estado["memoria"]


def test_estado_marca_quem_nao_esta_ativo(central):
    pessoas = {p["id"]: p for gente in central.estado()["setores"].values() for p in gente}
    assert pessoas["financeiro"]["ativo"] is True
    assert pessoas["seo"]["ativo"] is False


# --- eventos ----------------------------------------------------------
def test_trafego_do_barramento_vira_evento(central, eco_pequeno):
    eco_pequeno.barramento.enviar("copy", "seo", "Briefing", "preciso das palavras-chave")
    mensagens = [e for e in central.eventos if e["evento"] == "mensagem"]
    assert mensagens
    ultima = mensagens[-1]
    assert ultima["de"] == "copy" and ultima["para"] == "seo"
    assert ultima["nome"] == "Marina Duarte"       # resolve o id para o nome da pessoa


def test_assinante_recebe_evento_ao_vivo(central, eco_pequeno):
    fila = central.assinar()
    try:
        eco_pequeno.barramento.enviar("financeiro", "comercial", "Preco", "R$ 180 mil")
        evento = fila.get(timeout=5)
        assert evento["evento"] == "mensagem"
        assert evento["nome"] == "Patricia Souza"
    finally:
        central.desassinar(fila)


def test_desassinar_para_de_receber(central, eco_pequeno):
    fila = central.assinar()
    central.desassinar(fila)
    eco_pequeno.barramento.enviar("copy", "seo", "x", "y")
    with pytest.raises(queue.Empty):
        fila.get(timeout=0.3)


def test_fila_cheia_nao_derruba_o_servidor(central, eco_pequeno):
    """Aba abandonada enche a fila; o barramento nao pode travar por isso."""
    fila = central.assinar()
    try:
        while not fila.full():
            fila.put_nowait({"enchendo": True})
        eco_pequeno.barramento.enviar("copy", "seo", "x", "y")   # nao levanta
    finally:
        central.desassinar(fila)


def test_historico_de_eventos_e_limitado(central, eco_pequeno):
    from movili.painel.servidor import MAX_EVENTOS

    for i in range(MAX_EVENTOS + 40):
        central.emitir("mensagem", {"de": "copy", "para": "seo", "conteudo": str(i),
                                    "tipo": "informe", "assunto": "x"})
    assert len(central.eventos) == MAX_EVENTOS


# --- fila de trabalho -------------------------------------------------
def test_tarefa_de_agente_roda_e_guarda_a_entrega(central):
    tarefa = central.agendar("agente", "teste", agente="financeiro", texto="precifique")
    assert _esperar(central, tarefa.id) == "concluida"
    assert tarefa.resultado["entrega"]
    assert tarefa.resultado["agente"] == "financeiro"


def test_tarefa_de_fluxo_salva_relatorio(central):
    tarefa = central.agendar("fluxo", "teste", fluxo="prospeccao", texto="briefing")
    assert _esperar(central, tarefa.id, limite=30) == "concluida"
    assert tarefa.projeto
    assert tarefa.resultado["etapas"] >= 1
    from pathlib import Path
    assert Path(tarefa.resultado["relatorio"]).is_file()


def test_tarefa_com_tipo_invalido_termina_em_erro(central, capfd):
    tarefa = central.agendar("inventado", "teste", texto="x")
    assert _esperar(central, tarefa.id) == "erro"
    assert "desconhecido" in tarefa.erro
    # erro previsto nao suja o log com stack trace - senao ninguem le traceback
    assert "Traceback" not in capfd.readouterr().err
    # o worker continua vivo depois de um erro
    seguinte = central.agendar("agente", "ok", agente="copy", texto="headline")
    assert _esperar(central, seguinte.id) == "concluida"


def test_estados_da_tarefa_sao_emitidos(central):
    fila = central.assinar()
    try:
        tarefa = central.agendar("agente", "teste", agente="copy", texto="headline")
        _esperar(central, tarefa.id)
        estados = []
        while not fila.empty():
            ev = fila.get_nowait()
            if ev["evento"] == "tarefa" and ev["id"] == tarefa.id:
                estados.append(ev["estado"])
        assert "executando" in estados and "concluida" in estados
    finally:
        central.desassinar(fila)


# --- validacao das rotas ----------------------------------------------
class _Falso(_Handler):
    """Handler sem socket: captura o que seria respondido."""

    def __init__(self, central):  # noqa: D107 - nao chama o __init__ da stdlib
        self.central = central
        self.capturado = None

    def _json(self, codigo, corpo):
        self.capturado = (codigo, corpo)


def _post(central, corpo: dict):
    h = _Falso(central)
    h.path = "/api/executar"
    h._corpo = lambda: corpo
    h.do_POST()
    return h.capturado


@pytest.mark.parametrize("corpo,trecho", [
    ({"tipo": "fluxo", "fluxo": "inexistente", "texto": "x"}, "nao existe"),
    ({"tipo": "agente", "agente": "ninguem", "texto": "x"}, "nao esta ativo"),
    ({"tipo": "atender", "texto": "   "}, "informe o texto"),
    ({"tipo": "invalido", "texto": "x"}, "tipo deve ser"),
])
def test_entrada_invalida_devolve_400_explicando(central, corpo, trecho):
    codigo, resposta = _post(central, corpo)
    assert codigo == 400
    assert trecho in resposta["erro"]


def test_corpo_ausente_devolve_400(central):
    h = _Falso(central)
    h.path = "/api/executar"
    h._corpo = lambda: None
    h.do_POST()
    assert h.capturado[0] == 400


def test_rodadas_de_reuniao_sao_limitadas(central):
    codigo, resposta = _post(central, {"tipo": "reuniao", "texto": "tema", "rodadas": 99})
    assert codigo == 202
    assert central.tarefas[resposta["id"]].__dict__["extras"]["rodadas"] == 4


def test_pedido_valido_entra_na_fila(central):
    codigo, resposta = _post(central, {"tipo": "atender", "texto": "demanda real"})
    assert codigo == 202
    assert resposta["estado"] in {"na fila", "executando"}
    assert resposta["id"] in central.tarefas


def test_erro_inesperado_no_worker_deixa_rastro(central, monkeypatch, capfd):
    """O contrario do teste acima: bug de verdade precisa aparecer no log."""
    def explode(_tarefa):
        raise RuntimeError("falha inesperada")

    monkeypatch.setattr(central, "_executar", explode)
    tarefa = central.agendar("agente", "teste", agente="copy", texto="x")
    assert _esperar(central, tarefa.id) == "erro"
    assert "RuntimeError" in tarefa.erro
    assert "Traceback" in capfd.readouterr().err


def test_encerrar_para_o_worker_e_cancela_a_fila(eco_pequeno):
    c = Central(eco_pequeno)
    c.agendar("agente", "primeira", agente="copy", texto="x")
    pendente = c.agendar("agente", "segunda", agente="copy", texto="y")

    assert c.encerrar(timeout=30) is True
    assert not c._worker.is_alive()
    assert all(t.estado in {"concluida", "erro"} for t in c.tarefas.values())
    if pendente.estado == "erro":
        assert "encerrado" in pendente.erro

    with pytest.raises(TarefaInvalida, match="encerrando"):
        c.agendar("agente", "tarde demais", agente="copy", texto="z")


def test_encerrar_e_idempotente(eco_pequeno):
    c = Central(eco_pequeno)
    assert c.encerrar(timeout=30) is True
    assert c.encerrar(timeout=1) is True


def test_tarefa_invalida_e_um_erro_previsto():
    assert issubclass(TarefaInvalida, ValueError)


def test_json_do_estado_e_serializavel(central):
    """O painel manda tudo por JSON: nada de objeto solto no estado."""
    assert json.loads(json.dumps(central.estado(), ensure_ascii=False))
