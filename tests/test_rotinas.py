"""Rotinas: matematica do agendamento, catalogo e execucao."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from movili.rotinas import REGISTRO, Agenda, Agendamento, Rotina, catalogo, obter

# 21/09/2026 e uma segunda-feira.
SEGUNDA = datetime(2026, 9, 21, 8, 0)
SEG_A_SEX = frozenset({0, 1, 2, 3, 4})


# ---------------------------------------------------------------- agendamento
def test_agendamento_diario():
    a = Agendamento(hora=9, minuto=30)
    assert a.proximo_disparo(SEGUNDA) == datetime(2026, 9, 21, 9, 30)
    # depois da hora, cai no dia seguinte
    assert a.proximo_disparo(datetime(2026, 9, 21, 10, 0)) == datetime(2026, 9, 22, 9, 30)


def test_agendamento_pula_o_fim_de_semana():
    a = Agendamento(hora=9, dias_da_semana=SEG_A_SEX)
    sexta_tarde = datetime(2026, 9, 25, 18, 0)
    assert a.proximo_disparo(sexta_tarde) == datetime(2026, 9, 28, 9, 0)   # segunda


def test_agendamento_semanal_em_um_dia():
    a = Agendamento(hora=14, dias_da_semana=frozenset({2}))      # quarta
    assert a.proximo_disparo(SEGUNDA) == datetime(2026, 9, 23, 14, 0)
    assert a.proximo_disparo(datetime(2026, 9, 23, 15, 0)) == datetime(2026, 9, 30, 14, 0)


def test_agendamento_mensal():
    a = Agendamento(hora=9, dias_do_mes=frozenset({1}))
    assert a.proximo_disparo(SEGUNDA) == datetime(2026, 10, 1, 9, 0)


def test_dia_31_cai_no_ultimo_dia_de_mes_curto():
    """Senao a rotina de dia 31 simplesmente nunca rodaria em fevereiro."""
    a = Agendamento(hora=18, dias_do_mes=frozenset({31}))
    fevereiro = a.proximo_disparo(datetime(2026, 2, 1, 0, 0))
    assert fevereiro == datetime(2026, 2, 28, 18, 0)
    # em mes de 31 dias, cai no 31 mesmo
    assert a.proximo_disparo(datetime(2026, 3, 1, 0, 0)) == datetime(2026, 3, 31, 18, 0)


def test_ano_bissexto():
    a = Agendamento(hora=12, dias_do_mes=frozenset({29}), meses=frozenset({2}))
    assert a.proximo_disparo(datetime(2028, 1, 1)) == datetime(2028, 2, 29, 12, 0)


def test_agendamento_trimestral():
    a = Agendamento(hora=9, dias_do_mes=frozenset({1}), meses=frozenset({1, 4, 7, 10}))
    assert a.proximo_disparo(SEGUNDA) == datetime(2026, 10, 1, 9, 0)
    assert a.proximo_disparo(datetime(2026, 10, 1, 10, 0)) == datetime(2027, 1, 1, 9, 0)


def test_dia_da_semana_e_do_mes_juntos_exigem_os_dois():
    a = Agendamento(hora=9, dias_da_semana=frozenset({0}), dias_do_mes=frozenset({1}))
    quando = a.proximo_disparo(datetime(2026, 1, 1))
    assert quando is not None
    assert quando.weekday() == 0 and quando.day == 1


def test_dia_30_de_fevereiro_cai_no_ultimo_dia():
    """A regra do ultimo dia resolve datas que nao existem no mes."""
    a = Agendamento(hora=9, dias_do_mes=frozenset({30}), meses=frozenset({2}))
    assert a.proximo_disparo(SEGUNDA) == datetime(2027, 2, 28, 9, 0)


def test_horizonte_limita_a_busca_em_vez_de_girar_para_sempre():
    """A guarda existe para nao varrer o calendario indefinidamente."""
    mensal = Agendamento(hora=9, dias_do_mes=frozenset({1}))
    assert mensal.proximo_disparo(SEGUNDA, limite_dias=3) is None
    assert mensal.proximo_disparo(SEGUNDA, limite_dias=30) == datetime(2026, 10, 1, 9, 0)


def test_proximo_disparo_e_estritamente_depois():
    a = Agendamento(hora=9, minuto=0)
    exato = datetime(2026, 9, 21, 9, 0)
    assert a.proximo_disparo(exato) == datetime(2026, 9, 22, 9, 0)


@pytest.mark.parametrize("kwargs", [
    {"hora": 24}, {"hora": -1}, {"minuto": 60},
    {"dias_da_semana": frozenset({7})}, {"dias_do_mes": frozenset({0})},
    {"dias_do_mes": frozenset({32})}, {"meses": frozenset({13})},
])
def test_agendamento_invalido_falha_na_criacao(kwargs):
    with pytest.raises(ValueError):
        Agendamento(**kwargs)


def test_descricao_em_portugues():
    assert Agendamento(hora=9, dias_da_semana=SEG_A_SEX).descrever() == \
        "de segunda a sexta as 09:00"
    assert Agendamento(hora=14, dias_da_semana=frozenset({2})).descrever() == \
        "toda quarta as 14:00"
    assert Agendamento(hora=9, dias_do_mes=frozenset({1})).descrever() == "dia 1 as 09:00"
    assert Agendamento(hora=7, minuto=5).descrever() == "todo dia as 07:05"


# ---------------------------------------------------------------- catalogo
def test_catalogo_esta_coerente():
    from movili import agentes as quadro
    from movili import fluxos as processos

    for r in catalogo():
        assert r.id and r.nome and r.descricao
        assert r.agendamento.proximo_disparo(SEGUNDA) is not None, f"{r.id} nunca dispara"
        for ident in r.participantes:
            assert ident in quadro.REGISTRO, f"rotina '{r.id}' cita agente inexistente: {ident}"
        if r.tipo == "agente":
            assert r.agente in quadro.REGISTRO
        if r.tipo == "fluxo":
            assert r.alvo in processos.REGISTRO


def test_ids_do_catalogo_sao_unicos():
    ids = [r.id for r in catalogo()]
    assert len(ids) == len(set(ids)) == len(REGISTRO)


def test_obter_rotina_inexistente_da_erro_legivel():
    with pytest.raises(KeyError, match="nao existe"):
        obter("inventada")


@pytest.mark.parametrize("kwargs,trecho", [
    ({"tipo": "fluxo", "alvo": ""}, "nome do fluxo"),
    ({"tipo": "agente", "agente": ""}, "id do funcionario"),
    ({"tipo": "reuniao", "alvo": ""}, "tema"),
])
def test_rotina_mal_definida_falha_na_criacao(kwargs, trecho):
    with pytest.raises(ValueError, match=trecho):
        Rotina(id="x", nome="x", descricao="x", agendamento=Agendamento(), **kwargs)


# ---------------------------------------------------------------- agenda
@pytest.fixture
def agenda(eco_pequeno):
    """Agenda com relogio controlado e uma rotina simples."""
    relogio = {"agora": SEGUNDA}
    rotina = Rotina(
        id="teste", nome="Teste", descricao="rotina de teste",
        agendamento=Agendamento(hora=9, dias_da_semana=SEG_A_SEX),
        tipo="agente", agente="financeiro", alvo="faca o fecho",
    )
    a = Agenda(eco_pequeno, [rotina], relogio=lambda: relogio["agora"])
    a._relogio_teste = relogio        # o teste avanca o tempo por aqui
    return a


def test_nao_dispara_antes_da_hora(agenda):
    assert agenda.devidas() == []


def test_dispara_quando_a_hora_chega(agenda):
    agenda._relogio_teste["agora"] = datetime(2026, 9, 21, 9, 5)
    devidas = agenda.devidas()
    assert [r.id for r in devidas] == ["teste"]


def test_nao_repete_depois_de_rodar(agenda):
    agenda._relogio_teste["agora"] = datetime(2026, 9, 21, 9, 5)
    execucao = agenda.executar(agenda.devidas()[0])
    assert execucao.estado == "concluida"
    assert agenda.devidas() == []                       # ja rodou hoje
    agenda._relogio_teste["agora"] = datetime(2026, 9, 22, 9, 5)
    assert [r.id for r in agenda.devidas()] == ["teste"]  # amanha volta


def test_ultima_execucao_persiste_no_banco(agenda):
    agenda._relogio_teste["agora"] = datetime(2026, 9, 21, 9, 5)
    agenda.executar("teste")
    assert agenda.ultima_execucao("teste") == datetime(2026, 9, 21, 9, 5)


def test_atraso_dentro_da_janela_ainda_roda(agenda):
    agenda._relogio_teste["agora"] = datetime(2026, 9, 21, 13, 0)   # 4h depois
    assert [r.id for r in agenda.devidas()] == ["teste"]


def test_atraso_grande_e_pulado_em_vez_de_acumular(agenda):
    """Maquina desligada a semana toda nao pode despejar 5 dailies de uma vez."""
    agenda._relogio_teste["agora"] = datetime(2026, 9, 21, 9, 5)
    agenda.executar(agenda.devidas()[0])               # roda a de segunda

    agenda._relogio_teste["agora"] = datetime(2026, 9, 25, 9, 5)   # so volta na sexta
    devidas = agenda.devidas()
    assert [r.id for r in devidas] == ["teste"]        # so a de hoje, nao quatro
    puladas = [e for e in agenda.historico if e.estado == "pulada"]
    assert len(puladas) == 3, "terca, quarta e quinta tinham de ser marcadas como puladas"


def test_catch_up_acontece_numa_passada_so(agenda):
    """Antes, cada passada adiantava um horario: um mes parado levava 15 min."""
    agenda._relogio_teste["agora"] = datetime(2026, 9, 21, 9, 5)
    agenda.executar(agenda.devidas()[0])

    agenda._relogio_teste["agora"] = datetime(2026, 11, 2, 9, 5)   # 6 semanas depois
    assert [r.id for r in agenda.devidas()] == ["teste"]
    # a proxima passada ja nao encontra nada pendente do passado
    assert agenda.devidas() == [] or agenda.executar("teste").estado == "concluida"


def test_rotina_inativa_nao_entra_na_agenda(eco_pequeno):
    rotina = Rotina(
        id="off", nome="Off", descricao="desligada", agendamento=Agendamento(hora=9),
        tipo="agente", agente="financeiro", alvo="x", ativa=False,
    )
    a = Agenda(eco_pequeno, [rotina], relogio=lambda: datetime(2026, 9, 21, 9, 5))
    assert a.devidas() == []
    assert a.proximas() == []


def test_proximas_vem_em_ordem_cronologica(eco_pequeno):
    a = Agenda(eco_pequeno, relogio=lambda: SEGUNDA)
    itens = a.proximas(6)
    assert len(itens) == 6
    assert [q for _, q in itens] == sorted(q for _, q in itens)


# --- execucao de cada tipo -------------------------------------------
def test_executa_rotina_de_agente(eco_pequeno):
    r = Rotina(id="a", nome="A", descricao="d", agendamento=Agendamento(),
               tipo="agente", agente="financeiro", alvo="precifique")
    execucao = Agenda(eco_pequeno, [r]).executar(r)
    assert execucao.estado == "concluida" and execucao.detalhe


def test_executa_rotina_de_reuniao(eco_pequeno):
    r = Rotina(id="b", nome="B", descricao="d", agendamento=Agendamento(),
               tipo="reuniao", alvo="tema qualquer",
               participantes=["dev_backend", "financeiro"], rodadas=1)
    execucao = Agenda(eco_pequeno, [r]).executar(r)
    assert execucao.estado == "concluida"
    assert execucao.projeto.startswith("rotina-b-")


def test_reuniao_ignora_participante_inativo(eco_pequeno):
    """'seo' nao esta no eco_pequeno: a rotina roda com quem existe."""
    r = Rotina(id="c", nome="C", descricao="d", agendamento=Agendamento(),
               tipo="reuniao", alvo="tema", participantes=["seo", "financeiro"], rodadas=1)
    assert Agenda(eco_pequeno, [r]).executar(r).estado == "concluida"


def test_manutencao_nao_gasta_modelo(eco_pequeno):
    antes = sum(m["chamadas"] for m in eco_pequeno.metricas().values())
    r = Rotina(id="m", nome="M", descricao="d", agendamento=Agendamento(),
               tipo="manutencao", alvo="memoria")
    execucao = Agenda(eco_pequeno, [r]).executar(r)
    assert execucao.estado == "concluida"
    assert "trechos" in execucao.detalhe
    assert sum(m["chamadas"] for m in eco_pequeno.metricas().values()) == antes


def test_rotina_com_agente_inativo_termina_em_erro(eco_pequeno):
    r = Rotina(id="d", nome="D", descricao="d", agendamento=Agendamento(),
               tipo="agente", agente="seo", alvo="x")
    execucao = Agenda(eco_pequeno, [r]).executar(r)
    assert execucao.estado == "erro"
    assert "seo" in execucao.erro
    assert agenda_nao_marcou_como_executada(eco_pequeno, "d")


def agenda_nao_marcou_como_executada(eco, ident: str) -> bool:
    """Rotina que falhou nao pode contar como feita - senao pula a proxima."""
    return eco.memoria.recordar(f"rotina:{ident}:ultima_execucao") is None


# --- laco -------------------------------------------------------------
def test_parar_interrompe_o_laco_na_hora(eco_pequeno):
    import threading
    import time

    a = Agenda(eco_pequeno, [], relogio=lambda: SEGUNDA)
    thread = threading.Thread(target=lambda: a.rodar(intervalo=300), daemon=True)
    thread.start()
    time.sleep(0.2)
    a.parar()
    thread.join(timeout=5)
    assert not thread.is_alive(), "parar() precisa acordar a espera, nao aguardar o ciclo"
