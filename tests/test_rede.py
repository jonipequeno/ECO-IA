"""Rede Movili: topologia real, conversao de mensagens, pesos e rotas do painel."""

from __future__ import annotations

import json
import queue

import pytest

from movili import agentes as quadro
from movili.core.mensagem import Mensagem, Prioridade, Tipo
from movili.painel import rede
from movili.painel.servidor import ENCERRANDO, KIT, Central, _Handler

AGENTES = set(quadro.REGISTRO)


# --- topologia --------------------------------------------------------
def test_topologia_bate_com_as_contagens_do_kit():
    """20 agentes, 86 declaracoes, 67 sinapses, 19 reciprocas (guia/2-topologia.md)."""
    t = rede.topologia()
    perfis = quadro.todos_os_perfis()
    declaracoes = [(i, a) for i, p in perfis.items() for a in p.interlocutores if a != "*"]

    assert len(t["agentes"]) == 20
    assert len(declaracoes) == 86
    assert len(t["sinapses"]) == 67
    assert len(t["reciprocas"]) == 19
    assert t["declaraTodos"] == ["diretor"]


def test_topologia_traz_as_reciprocas_conhecidas():
    reciprocas = {tuple(p) for p in rede.topologia()["reciprocas"]}
    for par in [("comercial", "financeiro"), ("dev_backend", "dev_frontend"),
                ("marketing", "seo"), ("socio_estrategia", "socio_tecnologia")]:
        assert par in reciprocas


def test_topologia_pares_sao_unicos_ordenados_e_de_agentes_reais():
    t = rede.topologia()
    for a, b in t["sinapses"]:
        assert a < b and {a, b} <= AGENTES
    assert len({tuple(p) for p in t["sinapses"]}) == len(t["sinapses"])
    assert {tuple(p) for p in t["reciprocas"]} <= {tuple(p) for p in t["sinapses"]}


def test_topologia_regioes_cobrem_todos_os_agentes():
    t = rede.topologia()
    regioes = {r["id"] for r in t["regioes"]}
    assert regioes == set(quadro.SETORES)
    assert all(a["regiao"] in regioes for a in t["agentes"])
    comercial = next(a for a in t["agentes"] if a["id"] == "comercial")
    assert comercial["nome"] == "Eduardo Lima" and comercial["regiao"] == "comercial"


def test_topologia_nao_inventa_campos():
    """Sem modelo configurado: null. Sem limiar no perfil: campo ausente."""
    sem_modelo = rede.topologia()
    assert all(a["modelo"] is None for a in sem_modelo["agentes"])
    assert all("limiar" not in a for a in sem_modelo["agentes"])

    com_modelo = rede.topologia(lambda i: "qwen3:8b" if i == "dados" else None)
    modelos = {a["id"]: a["modelo"] for a in com_modelo["agentes"]}
    assert modelos["dados"] == "qwen3:8b" and modelos["copy"] is None


def test_topologia_e_serializavel():
    json.dumps(rede.topologia())


# --- conversao de mensagens -------------------------------------------
def _msg(de="comercial", para="financeiro", tipo=Tipo.TAREFA, prioridade=Prioridade.NORMAL,
         assunto="Precifique o projeto", conteudo="corpo com dado do cliente"):
    return Mensagem(remetente=de, destinatario=para, assunto=assunto, conteudo=conteudo,
                    tipo=tipo, prioridade=prioridade)


@pytest.mark.parametrize("tipo", list(Tipo))
def test_os_nove_tipos_viram_o_id_exato(tipo):
    ev = rede.evento_da_mensagem(_msg(tipo=tipo), AGENTES)
    assert ev["acao"] == "registrar"
    assert ev["dados"]["tipo"] == tipo.value
    assert ev["dados"]["tipo"] in {
        "briefing", "tarefa", "entrega", "pergunta", "resposta",
        "revisao", "decisao", "alerta", "informe",
    }


@pytest.mark.parametrize("prioridade", list(Prioridade))
def test_as_quatro_prioridades_passam(prioridade):
    ev = rede.evento_da_mensagem(_msg(prioridade=prioridade), AGENTES)
    assert ev["dados"]["prioridade"] == prioridade.value
    assert ev["dados"]["prioridade"] in {"baixa", "normal", "alta", "critica"}


def test_mensagem_entre_agentes_vira_registrar():
    ev = rede.evento_da_mensagem(_msg(), AGENTES)
    assert ev == {"acao": "registrar", "dados": {
        "tipo": "tarefa", "de": "comercial", "para": "financeiro",
        "prioridade": "normal", "texto": "Precifique o projeto",
    }}


def test_evento_nao_leva_horario_nem_conteudo():
    ev = rede.evento_da_mensagem(_msg(), AGENTES)
    assert "t" not in ev["dados"]
    assert "cliente" not in ev["dados"]["texto"]


def test_informe_vai_para_a_rede_inteira():
    ev = rede.evento_da_mensagem(_msg(para="*", tipo=Tipo.INFORME), AGENTES)
    assert ev["dados"]["para"] is None and ev["dados"]["tipo"] == "informe"
    # informe enderecado a alguem tambem e para todos: e o que o tipo significa
    ev = rede.evento_da_mensagem(_msg(tipo=Tipo.INFORME), AGENTES)
    assert ev["dados"]["para"] is None


def test_demanda_externa_vira_estimulo_no_agente_que_recebe():
    ev = rede.evento_da_mensagem(_msg(de="painel", para="dev_backend"), AGENTES)
    assert ev == {"acao": "estimular", "dados": {"no": "dev_backend", "texto": "Precifique o projeto"}}
    assert "afinidade" not in ev["dados"]  # sem dado real de relevancia, so o no de entrada


@pytest.mark.parametrize("de,para", [
    ("comercial", "comercial"),  # consigo mesmo: nao ha sinapse
    ("sistema", "painel"),      # nada da empresa envolvido
])
def test_mensagem_sem_sinapse_nao_vira_evento(de, para):
    assert rede.evento_da_mensagem(_msg(de=de, para=para), AGENTES) is None


def test_entrega_para_fora_fica_registrada_no_agente():
    """Sem isto, a pergunta feita pela ficha nunca mostraria que foi atendida."""
    ev = rede.evento_da_mensagem(_msg(de="financeiro", para="painel", tipo=Tipo.ENTREGA), AGENTES)
    assert ev["acao"] == "registrar"
    assert ev["dados"]["de"] == "financeiro" and ev["dados"]["para"] is None
    assert ev["dados"]["tipo"] == "entrega"


def test_alerta_de_falha_fica_registrado_no_agente():
    """O mesmo caminho de test_entrega_para_fora_fica_registrada_no_agente,

    mas para o que a delegacao publica quando o agente falha (ver
    Ecossistema.delegar em core/orquestrador.py). Sem isto, uma falha nunca
    aparece na rede - o pedido sai e nada volta, silencio que parece "o
    sistema nao responde" quando na verdade so falhou.
    """
    ev = rede.evento_da_mensagem(
        _msg(de="financeiro", para="painel", tipo=Tipo.ALERTA, prioridade=Prioridade.ALTA),
        AGENTES,
    )
    assert ev["acao"] == "registrar"
    assert ev["dados"]["de"] == "financeiro" and ev["dados"]["para"] is None
    assert ev["dados"]["tipo"] == "alerta"
    assert ev["dados"]["prioridade"] == "alta"


def test_texto_e_resumido_em_140():
    ev = rede.evento_da_mensagem(_msg(assunto="palavra " * 60), AGENTES)
    assert len(ev["dados"]["texto"]) <= 140 and ev["dados"]["texto"].endswith("...")


def test_sem_assunto_usa_o_inicio_do_conteudo():
    ev = rede.evento_da_mensagem(_msg(assunto="", conteudo="linha\n\n  unica"), AGENTES)
    assert ev["dados"]["texto"] == "linha unica"


# --- pesos ------------------------------------------------------------
def test_pesos_salvam_e_carregam(tmp_path):
    arquivo = rede.ArquivoPesos(tmp_path / "pesos.json")
    arquivo.salvar({"comercial|financeiro": 0.8, "copy|seo": 0.3})
    assert arquivo.carregar(AGENTES) == {"comercial|financeiro": 0.8, "copy|seo": 0.3}


def test_pesos_ausentes_ou_corrompidos_viram_vazio(tmp_path):
    arquivo = rede.ArquivoPesos(tmp_path / "pesos.json")
    assert arquivo.carregar(AGENTES) == {}
    arquivo.caminho.write_text("{ quebrado", encoding="utf-8")
    assert arquivo.carregar(AGENTES) == {}


def test_escrita_atomica_nao_deixa_temporario(tmp_path):
    arquivo = rede.ArquivoPesos(tmp_path / "pesos.json")
    arquivo.salvar({"comercial|financeiro": 0.5})
    arquivo.salvar({"comercial|financeiro": 0.6})
    assert [p.name for p in tmp_path.iterdir()] == ["pesos.json"]


def test_validar_pesos_normaliza_e_descarta_lixo():
    limpos = rede.validar_pesos({
        "financeiro|comercial": 0.7,   # fora de ordem: vira a chave canonica
        "copy|seo": 1.9,               # acima de 1
        "seo|dados": -3,               # abaixo de 0
        "comercial|ninguem": 0.5,      # agente inexistente
        "comercial|comercial": 0.5,    # consigo mesmo
        "sem-barra": 0.5,
        "rh|cs": "0.4",                # texto
        "rh|dados": True,              # booleano nao e numero
        "rh|juridico": float("nan"),
    }, AGENTES)
    assert limpos == {"comercial|financeiro": 0.7, "copy|seo": 1.0, "dados|seo": 0.0}


def test_validar_pesos_recusa_o_que_nao_e_objeto():
    with pytest.raises(ValueError):
        rede.validar_pesos([["a", "b"]], AGENTES)


# --- central e rotas ----------------------------------------------------
@pytest.fixture
def central(eco_pequeno):
    c = Central(eco_pequeno)
    yield c
    c.encerrar(timeout=30)


class _Falso(_Handler):
    """Handler sem socket: captura o que seria respondido."""

    def __init__(self, central, path, corpo=None):  # noqa: D107
        self.central = central
        self.path = path
        self.capturado = None
        self._corpo = lambda: corpo

    def _json(self, codigo, corpo):
        self.capturado = (codigo, corpo)


def test_barramento_alimenta_a_rede_com_id_incremental(central, eco_pequeno):
    fila = central.assinar_rede(None)
    try:
        eco_pequeno.barramento.enviar("diretor", "dev_backend", "arquitetura", "x", tipo=Tipo.TAREFA)
        eco_pequeno.barramento.enviar("dev_backend", "diretor", "Re: arquitetura", "y",
                                      tipo=Tipo.ENTREGA)
        a, b = fila.get(timeout=2), fila.get(timeout=2)
        assert b[0] == a[0] + 1
        assert a[1]["dados"]["tipo"] == "tarefa" and b[1]["dados"]["tipo"] == "entrega"
    finally:
        central.desassinar_rede(fila)


def test_aba_nova_nao_recebe_trafego_antigo_mas_a_que_caiu_recupera(central, eco_pequeno):
    eco_pequeno.barramento.enviar("diretor", "financeiro", "a", "x", tipo=Tipo.TAREFA)
    primeiro = central.emitir_rede({"acao": "registrar", "dados": {"tipo": "alerta"}})
    eco_pequeno.barramento.enviar("diretor", "copy", "b", "x", tipo=Tipo.TAREFA)

    nova = central.assinar_rede(None)
    assert nova.empty()
    voltou = central.assinar_rede(primeiro)
    perdidos = [voltou.get_nowait()[1] for _ in range(voltou.qsize())]
    assert [p["dados"]["para"] for p in perdidos] == ["copy"]


def test_tarefa_do_painel_estimula_o_agente_marcando_a_aba(central):
    fila = central.assinar_rede(None)
    try:
        tarefa = central.agendar("agente", "x", agente="financeiro", texto="quanto cobrar?",
                                 cliente="aba-1")
        estimulo = None
        while estimulo is None:
            _, ev = fila.get(timeout=15)
            if ev["acao"] == "estimular":
                estimulo = ev
        assert estimulo["dados"]["no"] == "financeiro"
        assert estimulo["cliente"] == "aba-1"
        assert central.tarefas[tarefa.id].id == tarefa.id
    finally:
        central.desassinar_rede(fila)


def test_fluxo_disparado_pelo_painel_entra_pela_diretoria(central):
    fila = central.assinar_rede(None)
    try:
        central.agendar("atender", "x", texto="cliente quer um app")
        _, ev = fila.get(timeout=15)
        assert ev == {"acao": "estimular", "dados": {"no": "diretor", "texto": "cliente quer um app"}}
    finally:
        central.desassinar_rede(fila)


def test_encerrar_avisa_o_stream_da_rede(eco_pequeno):
    c = Central(eco_pequeno)
    fila = c.assinar_rede(None)
    c.encerrar(timeout=30)
    assert fila.get_nowait() is ENCERRANDO


def test_rota_topologia(central):
    h = _Falso(central, "/api/rede/topologia")
    h.do_GET()
    codigo, corpo = h.capturado
    assert codigo == 200 and len(corpo["sinapses"]) == 67
    assert all(a["modelo"] for a in corpo["agentes"])  # a config de teste tem modelo para todos


def test_rota_pesos_grava_e_devolve(central):
    h = _Falso(central, "/api/rede/pesos", {"financeiro|comercial": 0.9, "x|y": 1})
    h.do_POST()
    assert h.capturado == (200, {"salvos": 1})

    h = _Falso(central, "/api/rede/pesos")
    h.do_GET()
    assert h.capturado == (200, {"comercial|financeiro": 0.9})


@pytest.mark.parametrize("corpo", [None, ["lista"]])
def test_rota_pesos_recusa_corpo_invalido(central, corpo):
    h = _Falso(central, "/api/rede/pesos", corpo)
    h.do_POST()
    assert h.capturado[0] == 400


def test_estatico_nao_sai_da_pasta_do_kit(central):
    h = _Falso(central, "/rede-movili/../servidor.py")
    h.do_GET()
    assert h.capturado[0] == 404


def test_kit_traz_os_arquivos_que_a_pagina_carrega():
    for nome in ("tokens.css", "bundle.css", "bundle.js"):
        assert (KIT / nome).is_file(), f"falta o {nome} do kit Rede Movili"


def test_fila_da_rede_tem_teto(central):
    fila = central.assinar_rede(None)
    try:
        for i in range(fila.maxsize + 50):
            central.emitir_rede({"acao": "registrar", "dados": {"i": i}})
        assert fila.full()
    finally:
        central.desassinar_rede(fila)
    assert isinstance(fila, queue.Queue)
