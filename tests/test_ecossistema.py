"""Agentes, orquestracao, fluxos e reuniao - tudo no backend simulado."""

from __future__ import annotations

from pathlib import Path

import pytest

from movili import agentes as quadro
from movili import fluxos as processos
from movili.core.mensagem import Prioridade, Tipo


def test_prompt_de_sistema_tem_persona_e_empresa(eco):
    agente = eco.agente("financeiro")
    prompt = agente.prompt_sistema(eco.diretorio(exceto="financeiro"))
    assert "Patricia Souza" in prompt
    assert "Movili Tecnologia" in prompt
    assert "SUA MISSAO" in prompt and "KPIs" in prompt
    assert "@comercial" in prompt          # conhece os colegas
    assert "portugues do Brasil" in prompt


def test_agente_nao_ve_a_si_mesmo_como_colega(eco):
    prompt = eco.agente("copy").prompt_sistema(eco.diretorio(exceto="copy"))
    assert "@copy:" not in prompt


def test_delegar_registra_ida_e_volta_no_barramento(eco_pequeno):
    resultado = eco_pequeno.delegar("dev_backend", "desenhe a arquitetura", projeto="p1")
    assert resultado.agente == "dev_backend"
    assert resultado.nome_agente == "Rafael Andrade"
    assert resultado.entrega

    historico = eco_pequeno.barramento.por_projeto("p1")
    assert len(historico) == 2
    assert historico[0].tipo is Tipo.TAREFA
    assert historico[1].tipo is Tipo.ENTREGA


def test_delegar_publica_alerta_quando_o_agente_falha(eco_pequeno):
    """Sem isto, uma falha e muda: nada volta ao barramento.

    Antes desta correcao, quando agente.responder() levantava excecao, a
    funcao saia de delegar() antes da linha que publica a entrega - sucesso
    OU falha. Quem olhava o barramento (o painel, a rede, a memoria) via
    so o pedido saindo, nunca um retorno. Na pratica: a interface mostrava a
    pergunta enviada e depois nada, para sempre - "o sistema nao responde".
    """
    from movili.llm.base import LLMIndisponivel

    agente = eco_pequeno.agente("financeiro")
    mensagem_erro = "backend fora do ar: connection refused"
    agente.responder = lambda *a, **k: (_ for _ in ()).throw(LLMIndisponivel(mensagem_erro))

    with pytest.raises(LLMIndisponivel, match=mensagem_erro):
        eco_pequeno.delegar("financeiro", "qual a margem minima?", projeto="p-falha")

    historico = eco_pequeno.barramento.por_projeto("p-falha")
    alertas = [m for m in historico if m.tipo is Tipo.ALERTA]
    assert len(alertas) == 1, "a falha precisa deixar rastro no barramento"

    alerta = alertas[0]
    assert alerta.remetente == "financeiro"
    assert alerta.prioridade is Prioridade.ALTA
    assert mensagem_erro in alerta.conteudo


def test_falha_de_agente_nao_impede_o_worker_de_seguir(eco_pequeno):
    """O worker do painel processa tarefas em fila: uma que falha nao pode travar as seguintes."""
    from movili.llm.base import LLMIndisponivel

    agente = eco_pequeno.agente("financeiro")
    agente.responder = lambda *a, **k: (_ for _ in ()).throw(LLMIndisponivel("fora do ar"))

    with pytest.raises(LLMIndisponivel):
        eco_pequeno.delegar("financeiro", "primeira", projeto="p1")

    # o proximo delegar, a outro agente saudavel, funciona normalmente
    resultado = eco_pequeno.delegar("copy", "segunda", projeto="p2")
    assert resultado.entrega


def test_entregavel_fica_na_memoria_corporativa(eco_pequeno):
    eco_pequeno.delegar("copy", "escreva a headline", projeto="campanha-x")
    itens = eco_pequeno.memoria.entregaveis("campanha-x")
    assert any(i["agente"] == "copy" for i in itens)


def test_fila_de_pendentes_do_agente_tem_teto(eco_pequeno):
    """Sem teto, um agente guardaria toda mensagem da sessao - o painel roda por horas."""
    financeiro = eco_pequeno.agente("financeiro")
    financeiro.limite_pendentes  # existe e e configuravel

    for i in range(financeiro.limite_pendentes + 150):
        eco_pequeno.barramento.enviar("diretor", "financeiro", f"t{i}", "corpo")

    assert len(financeiro._pendentes) == financeiro.limite_pendentes
    pendentes = financeiro.pendentes()
    assert pendentes[-1].assunto == f"t{financeiro.limite_pendentes + 149}"
    assert financeiro.pendentes() == []       # ler esvazia


def test_agente_nao_enfileira_as_proprias_mensagens(eco_pequeno):
    financeiro = eco_pequeno.agente("financeiro")
    financeiro.pendentes()
    eco_pequeno.barramento.enviar("financeiro", "*", "Comunicado", "avisando todo mundo")
    assert financeiro.pendentes() == []


def test_handoff_entre_agentes_e_detectado(eco):
    agente = eco.agente("seo")
    achados = agente.handoffs("Fechei o mapa.\n@copy {escreva os titulos das 5 paginas}")
    assert achados == [("copy", "escreva os titulos das 5 paginas")]


def test_execucao_paralela_devolve_todas_as_entregas(eco_pequeno):
    lote = eco_pequeno.em_paralelo(
        [("dev_backend", "estime"), ("financeiro", "precifique")], projeto="par"
    )
    assert {r.agente for r in lote} == {"dev_backend", "financeiro"}
    assert all(r.entrega for r in lote)


def test_fluxo_executa_na_ordem_e_consolida(eco):
    fluxo = processos.obter("prospeccao")
    resultado = eco.executar_fluxo(fluxo, "vender squad dedicada para logistica", projeto="pr1")
    assert [e.agente for e in resultado.etapas[:5]] == [e.agente for e in fluxo.etapas]
    assert resultado.consolidacao          # o diretor fechou
    assert resultado.iniciado_em and resultado.concluido_em


def test_fluxo_passa_a_entrega_anterior_como_contexto(eco):
    fluxo = processos.obter("prospeccao")
    eco.executar_fluxo(fluxo, "briefing de teste", projeto="pr2")
    simulado = eco.roteador.provedor("simulado")
    # a chamada do copy (2a etapa) tem de citar a entrega do SDR
    concatenado = "\n".join(m["content"] for chamada in simulado.chamadas for m in chamada)
    assert "ENTREGA DE" in concatenado


def test_fluxo_de_projeto_envolve_todas_as_areas(eco):
    fluxo = processos.obter("novo-projeto")
    envolvidos = {e.agente for e in fluxo.etapas}
    assert {"comercial", "dev_backend", "produto", "projetos", "seguranca",
            "financeiro", "juridico", "rh"} <= envolvidos


def test_decisao_estrategica_termina_nos_socios(eco):
    fluxo = processos.obter("decisao-estrategica")
    ultimos = [e.agente for e in fluxo.etapas[-2:]]
    assert ultimos == ["socio_tecnologia", "socio_estrategia"]


def test_reuniao_faz_todos_falarem_em_cada_rodada(eco_pequeno):
    presentes = ["diretor", "dev_backend", "financeiro"]
    resultado = eco_pequeno.reuniao(
        "vale a pena entrar em saude?", participantes=presentes, rodadas=2
    )
    assert len(resultado.etapas) == len(presentes) * 2
    assert resultado.consolidacao          # ata final do mediador


def test_reuniao_leva_a_ata_para_a_segunda_rodada(eco_pequeno):
    eco_pequeno.reuniao("tema", participantes=["dev_backend", "financeiro"], rodadas=2)
    chamadas = eco_pequeno.roteador.provedor("simulado").chamadas
    texto = "\n".join(m["content"] for c in chamadas for m in c)
    assert "ATA ATE AQUI" in texto


def test_triagem_devolve_agentes_validos(eco):
    escolhidos = eco.triagem("preciso de um app de delivery", maximo=4)
    assert 1 <= len(escolhidos) <= 4
    assert all(i in eco for i in escolhidos)
    assert quadro.ORQUESTRADOR not in escolhidos


def test_atender_produz_relatorio_salvavel(eco_pequeno, tmp_path):
    resultado = eco_pequeno.atender("integrar ERP com marketplace", maximo=2)
    caminhos = eco_pequeno.salvar(resultado, tmp_path)
    assert caminhos["relatorio"].is_file()
    assert caminhos["conversas"].is_file()
    md = caminhos["relatorio"].read_text(encoding="utf-8")
    assert "# " in md and "Briefing" in md


def test_salvar_usa_o_workspace_configurado(eco_pequeno, tmp_path):
    """Sem destino explicito, respeita a configuracao - nao './workspace'."""
    destino = tmp_path / "meu-workspace"
    eco_pequeno.config.workspace = str(destino)

    resultado = eco_pequeno.atender("demanda de teste", maximo=1)
    caminhos = eco_pequeno.salvar(resultado)

    assert caminhos["relatorio"].is_file()
    assert destino in caminhos["relatorio"].parents
    assert not (Path.cwd() / "workspace" / resultado.projeto).exists()


def test_salvar_com_destino_explicito_vence(eco_pequeno, tmp_path):
    resultado = eco_pequeno.atender("outra demanda", maximo=1)
    caminhos = eco_pequeno.salvar(resultado, tmp_path / "escolhido")
    assert (tmp_path / "escolhido") in caminhos["relatorio"].parents


def test_metricas_de_uso_por_agente(eco_pequeno):
    eco_pequeno.delegar("copy", "headline")
    assert eco_pequeno.metricas()["copy"]["chamadas"] >= 1


def test_ecossistema_reduzido_ignora_etapa_de_agente_ausente(eco_pequeno):
    # 'prospeccao' nao esta no eco_pequeno: o fluxo tem de seguir sem quebrar
    resultado = eco_pequeno.executar_fluxo(processos.obter("prospeccao"), "briefing")
    agentes_usados = {e.agente for e in resultado.etapas}
    assert "prospeccao" not in agentes_usados
    assert "financeiro" in agentes_usados
