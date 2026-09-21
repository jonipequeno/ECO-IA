"""Ordem de importacao: o pacote nao pode ter ciclo.

movili.agentes importa movili.core.agente, o que dispara movili/core/__init__.py.
Se esse __init__ carregar o orquestrador - que por sua vez importa movili.agentes -
qualquer valor de movili.agentes avaliado em tempo de import quebra, porque o
modulo ainda esta pela metade. Ja aconteceu uma vez; estes testes impedem a volta.
"""

from __future__ import annotations

import subprocess
import sys

import pytest

# Cada entrada e a PRIMEIRA coisa importada num interpretador limpo.
ORDENS = [
    "import movili.agentes, movili.core",
    "import movili.core, movili.agentes",
    "import movili.core.orquestrador",
    "import movili.core.agente",
    "import movili.fluxos",
    "import movili.jarvis",
    "import movili.cli",
    "from movili.core import Ecossistema, MemoriaSemantica, Fluxo",
    "from movili.agentes import REGISTRO",
]


@pytest.mark.parametrize("comando", ORDENS)
def test_importa_em_qualquer_ordem(comando):
    """Interpretador novo por caso: e a unica forma de pegar ciclo de import."""
    resultado = subprocess.run(
        [sys.executable, "-c", comando],
        capture_output=True, text=True, timeout=90,
    )
    assert resultado.returncode == 0, (
        f"'{comando}' falhou:\n{resultado.stderr[-1500:]}"
    )


def test_core_exporta_o_que_promete():
    """Tudo em __all__ existe de fato no pacote."""
    import movili.core as core

    faltando = [n for n in core.__all__ if not hasattr(core, n)]
    assert not faltando, f"__all__ promete o que nao existe: {faltando}"


def test_core_exporta_os_tipos_publicos_do_nucleo():
    import movili.core as core

    esperados = {
        "Agente", "Perfil", "Barramento", "Mensagem", "Tipo", "Prioridade",
        "MemoriaCorporativa", "MemoriaCurta", "MemoriaSemantica", "Achado",
        "CaixaDeFerramentas", "Ferramenta",
        "Ecossistema", "Fluxo", "Etapa", "ResultadoFluxo", "ResultadoEtapa",
    }
    assert esperados <= set(core.__all__)


def test_sentinela_do_orquestrador_e_resolvida():
    """O default de 'quem coordena' vira o id real do quadro em tempo de execucao."""
    from movili import agentes as quadro
    from movili.core.orquestrador import PADRAO, Fluxo, _resolver

    assert Fluxo("x", "y", []).consolidador == PADRAO       # guardado como sentinela
    assert _resolver(PADRAO) == quadro.ORQUESTRADOR          # resolvido no uso
    assert _resolver("financeiro") == "financeiro"           # valor explicito preservado
    assert _resolver(None) is None                           # 'sem consolidador' preservado


def test_fluxo_sem_consolidador_nao_consolida(eco_pequeno):
    from movili.core.orquestrador import Etapa, Fluxo

    fluxo = Fluxo(
        "Sem fecho", "teste",
        [Etapa(agente="financeiro", instrucao="faca uma conta")],
        consolidador=None,
    )
    resultado = eco_pequeno.executar_fluxo(fluxo, "briefing")
    assert resultado.consolidacao == ""
    assert len(resultado.etapas) == 1
