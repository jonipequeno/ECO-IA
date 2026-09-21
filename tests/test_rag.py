"""Memoria semantica: fatiamento, similaridade, indexacao e procedencia."""

from __future__ import annotations

import pytest

from movili.core.rag import MemoriaSemantica, cosseno, fatiar
from movili.llm.base import LLMIndisponivel
from movili.llm.router import ConfigBackend, RoteadorLLM


@pytest.fixture
def roteador():
    return RoteadorLLM({"simulado": ConfigBackend("simulado", "", "simulado")})


@pytest.fixture
def semantica(roteador, tmp_path):
    mem = MemoriaSemantica(roteador, tmp_path / "sem.db", backend="simulado")
    yield mem
    mem.fechar()


# --- fatiamento -------------------------------------------------------
def test_texto_curto_vira_um_trecho():
    assert fatiar("uma frase curta") == ["uma frase curta"]
    assert fatiar("   ") == []
    assert fatiar("") == []


def test_texto_longo_e_quebrado_com_sobreposicao():
    texto = "\n\n".join(f"Paragrafo {i} com conteudo suficiente para ocupar espaco." * 6
                        for i in range(12))
    trechos = fatiar(texto, tamanho=600, sobreposicao=80)
    assert len(trechos) > 1
    assert all(t.strip() for t in trechos)
    # nenhum trecho estoura muito o tamanho pedido
    assert max(len(t) for t in trechos) <= 700


def test_fatiar_cobre_o_texto_inteiro():
    texto = " ".join(f"palavra{i}" for i in range(500))
    trechos = fatiar(texto, tamanho=400, sobreposicao=50)
    juntos = " ".join(trechos)
    assert "palavra0" in juntos and "palavra499" in juntos


# --- similaridade -----------------------------------------------------
def test_cosseno_de_vetores_identicos_e_um():
    assert cosseno([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) == pytest.approx(1.0)


def test_cosseno_de_vetores_ortogonais_e_zero():
    assert cosseno([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)


def test_cosseno_degenerado_nao_explode():
    assert cosseno([0.0, 0.0], [1.0, 1.0]) == 0.0      # vetor nulo
    assert cosseno([1.0, 2.0], [1.0]) == 0.0           # tamanhos diferentes
    assert cosseno([], []) == 0.0                      # vazio


# --- indexacao e busca ------------------------------------------------
def test_indexar_e_recuperar(semantica):
    n = semantica.indexar(
        "Arquitetura de roteirizacao de frota com rastreamento de caminhoes "
        "em tempo real e integracao com ERP Protheus.",
        origem="entrega", referencia="e1", projeto="frota", agente="dev_backend",
        titulo="Arquitetura",
    )
    assert n == 1

    achados = semantica.buscar("rastreamento de caminhoes e integracao com ERP", minimo=0.1)
    assert achados
    assert achados[0].projeto == "frota"
    assert achados[0].agente == "dev_backend"
    assert 0.0 < achados[0].similaridade <= 1.0


def test_assunto_distante_nao_e_recuperado(semantica):
    semantica.indexar(
        "Roteirizacao de frota, rastreamento de caminhoes, integracao com ERP Protheus.",
        origem="entrega", referencia="e1", projeto="frota", agente="dev_backend",
    )
    assert semantica.buscar("politica de ferias e banco de horas", minimo=0.35) == []


def test_reindexar_a_mesma_referencia_nao_duplica(semantica):
    texto = "Precificacao do projeto com margem de quarenta por cento. " * 40
    semantica.indexar(texto, origem="entrega", referencia="e1", projeto="p", agente="financeiro")
    primeiro = semantica.estatisticas()["trechos"]
    semantica.indexar(texto, origem="entrega", referencia="e1", projeto="p", agente="financeiro")
    assert semantica.estatisticas()["trechos"] == primeiro


@pytest.mark.parametrize("vizinha,alvo", [
    ("docs/aXb.md", "docs/a_b.md"),      # '_' casa qualquer caractere no LIKE
    ("relatorio-2026", "relatorio%2026"),  # '%' casa qualquer sequencia
    ("nota-x", "nota\\x"),                # a propria barra de escape
])
def test_reindexar_nao_apaga_documento_vizinho(semantica, vizinha, alvo):
    """Curinga de LIKE em referencia ja apagou indice de outro documento.

    As referencias vem de caminho de arquivo informado pelo usuario, e '_' e
    '%' sao curingas: sem escapar, indexar 'docs/a_b.md' destruia os trechos
    de 'docs/aXb.md' silenciosamente.
    """
    semantica.indexar("conteudo da vizinha " * 20, origem="arquivo", referencia=vizinha)
    semantica.indexar("conteudo do alvo " * 20, origem="arquivo", referencia=alvo)
    semantica.indexar("alvo reindexado " * 20, origem="arquivo", referencia=alvo)

    referencias = {
        linha[0].rsplit("#", 1)[0]
        for linha in semantica._conn.execute("SELECT referencia FROM vetores")
    }
    assert vizinha in referencias, f"indexar '{alvo}' apagou '{vizinha}'"
    assert alvo in referencias


def test_padrao_de_referencia_escapa_curingas():
    from movili.core.rag import _padrao_de_referencia

    assert _padrao_de_referencia("a_b") == "a\\_b#%"
    assert _padrao_de_referencia("50%") == "50\\%#%"
    assert _padrao_de_referencia("a\\b") == "a\\\\b#%"
    assert _padrao_de_referencia("simples") == "simples#%"


def test_indexar_texto_vazio_nao_grava(semantica):
    assert semantica.indexar("   ", origem="entrega", referencia="vazio") == 0
    assert semantica.estatisticas()["trechos"] == 0


def test_filtros_de_busca(semantica):
    semantica.indexar("contrato de desenvolvimento com clausula de SLA e multa",
                      origem="e", referencia="a", projeto="p1", agente="juridico")
    semantica.indexar("contrato de desenvolvimento com clausula de SLA e multa",
                      origem="e", referencia="b", projeto="p2", agente="comercial")

    so_juridico = semantica.buscar("clausula de SLA", agente="juridico", minimo=0.1)
    assert all(a.agente == "juridico" for a in so_juridico)

    so_p2 = semantica.buscar("clausula de SLA", projeto="p2", minimo=0.1)
    assert all(a.projeto == "p2" for a in so_p2)

    sem_p1 = semantica.buscar("clausula de SLA", excluir_projeto="p1", minimo=0.1)
    assert all(a.projeto != "p1" for a in sem_p1)


def test_contexto_vazio_quando_nada_casa(semantica):
    semantica.indexar("assunto totalmente diferente sobre jardinagem",
                      origem="e", referencia="a", projeto="p")
    assert semantica.contexto("arquitetura de microsservicos", minimo=0.9) == ""


def test_contexto_marca_a_origem(semantica):
    semantica.indexar("Margem minima da casa e de trinta e cinco por cento ao projeto.",
                      origem="e", referencia="a", projeto="orcamentos", agente="financeiro")
    bloco = semantica.contexto("qual a margem minima da casa", minimo=0.1)
    assert "MEMORIA DA EMPRESA" in bloco
    assert "financeiro" in bloco and "orcamentos" in bloco


def test_consulta_vazia_devolve_nada(semantica):
    assert semantica.buscar("   ") == []


# --- procedencia dos vetores -----------------------------------------
def test_assinatura_registra_backend_e_modelo(semantica):
    semantica.indexar("qualquer coisa", origem="e", referencia="a")
    assert semantica.assinatura == "simulado/nomic-embed-text"
    assert semantica.estatisticas()["assinaturas"] == {"simulado/nomic-embed-text": 1}


def test_vetores_de_outra_procedencia_sao_ignorados(semantica):
    """Cosseno entre espacos vetoriais diferentes nao significa nada."""
    semantica.indexar("integracao com ERP e rastreamento", origem="e", referencia="atual",
                      projeto="novo")
    semantica._conn.execute(
        "INSERT INTO vetores (origem,referencia,projeto,agente,titulo,trecho,vetor,modelo,criado_em)"
        " VALUES ('e','antigo#0','velho','copy','t','integracao com ERP e rastreamento',"
        " '[0.5,0.5]','outro-backend/outro-modelo','2026-01-01')"
    )
    semantica._conn.commit()

    achados = semantica.buscar("integracao com ERP e rastreamento", minimo=0.0, limite=10)
    assert all(a.projeto != "velho" for a in achados)

    stats = semantica.estatisticas()
    assert stats["inativos"] == 1
    assert len(stats["assinaturas"]) == 2


def test_limpar_por_projeto(semantica):
    semantica.indexar("a" * 50, origem="e", referencia="a", projeto="p1")
    semantica.indexar("b" * 50, origem="e", referencia="b", projeto="p2")
    assert semantica.limpar("p1") == 1
    assert list(semantica.estatisticas()["projetos"]) == ["p2"]


# --- degradacao sem backend de embedding ------------------------------
def test_busca_sem_backend_devolve_vazio_em_vez_de_quebrar(tmp_path):
    """Sem modelo de embedding, a empresa segue trabalhando - so sem memoria."""
    quebrado = RoteadorLLM(
        {"quebrado": ConfigBackend("ollama", "http://127.0.0.1:1", "x", timeout=1)},
        ["quebrado"], tentativas=1,
    )
    mem = MemoriaSemantica(quebrado, tmp_path / "x.db", backend="quebrado")
    assert mem.buscar("qualquer consulta") == []
    assert mem.contexto("qualquer consulta") == ""
    mem.fechar()


def test_indexar_sem_backend_levanta_erro_acionavel(tmp_path):
    quebrado = RoteadorLLM(
        {"quebrado": ConfigBackend("ollama", "http://127.0.0.1:1", "x", timeout=1)},
        ["quebrado"], tentativas=1,
    )
    mem = MemoriaSemantica(quebrado, tmp_path / "y.db", backend="quebrado")
    with pytest.raises(LLMIndisponivel, match="nomic-embed-text"):
        mem.indexar("texto", origem="e", referencia="a")
    mem.fechar()


# --- integracao com o ecossistema -------------------------------------
def test_entrega_e_indexada_automaticamente(eco_pequeno):
    assert eco_pequeno.semantica is not None
    eco_pequeno.delegar("dev_backend", "arquitete um sistema de rastreamento de frota",
                        projeto="frota-1")
    assert eco_pequeno.semantica.estatisticas()["trechos"] > 0


def test_projeto_seguinte_recupera_memoria_do_anterior(eco_pequeno):
    # O provedor simulado pontua numa escala propria (hashing lexical), que nao
    # e a do modelo de embedding real. O limiar aqui e do teste, nao da producao.
    eco_pequeno.config.embeddings["similaridade_minima"] = 0.2
    eco_pequeno.delegar(
        "dev_backend",
        "Arquitete rastreamento de frota com integracao ao ERP Protheus para transportadora.",
        projeto="frota-1",
    )
    contexto = eco_pequeno._com_memoria(
        "", "Precifique um rastreamento de frota com integracao ao ERP para transportadora.",
        "financeiro", "frota-2",
    )
    assert "MEMORIA DA EMPRESA" in contexto


def test_projeto_em_andamento_nao_recupera_a_si_mesmo(eco_pequeno):
    eco_pequeno.config.embeddings["similaridade_minima"] = 0.2
    eco_pequeno.delegar("dev_backend", "arquitete rastreamento de frota com ERP",
                        projeto="frota-1")
    contexto = eco_pequeno._com_memoria(
        "", "arquitete rastreamento de frota com ERP", "financeiro", "frota-1"
    )
    assert contexto == ""


def test_memoria_desligada_nao_altera_o_contexto(config):
    from movili.core.orquestrador import Ecossistema

    config.embeddings = {"habilitado": False}
    eco = Ecossistema(config, verboso=False, somente=["financeiro"])
    assert eco.semantica is None
    assert eco._com_memoria("contexto original", "instrucao", "financeiro", "p") == "contexto original"
    eco.encerrar()


# --- CLI --------------------------------------------------------------
def test_cli_aceita_projeto_antes_e_depois_do_subcomando():
    """--projeto e flag global; o subcomando 'memoria' tem a propria copia.

    Sem as duas, 'movili memoria indexar --projeto X' falharia, porque o
    argparse nao aceita opcao do parser principal depois do subcomando.
    """
    from movili.cli import construir_parser

    parser = construir_parser()

    depois = parser.parse_args(["memoria", "indexar", "--projeto", "frota"])
    assert depois.projeto_memoria == "frota"

    antes = parser.parse_args(["--projeto", "frota", "memoria", "indexar"])
    assert antes.projeto == "frota"
    # o subcomando nao pode apagar o valor global com o proprio default
    assert antes.projeto_memoria is None


def test_cli_memoria_expoe_as_quatro_acoes():
    from movili.cli import construir_parser

    parser = construir_parser()
    for acao in ("status", "buscar", "indexar", "limpar"):
        assert parser.parse_args(["memoria", acao]).acao == acao
