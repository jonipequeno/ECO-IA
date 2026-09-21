"""Processos internos da Movili: a sequencia em que as areas se acionam."""

from __future__ import annotations

from ..core.orquestrador import Etapa, Fluxo
from .campanha import fluxo as _campanha
from .decisao_estrategica import fluxo as _decisao
from .diagnostico import fluxo as _diagnostico
from .novo_projeto import fluxo as _novo_projeto
from .pos_venda import fluxo as _pos_venda
from .produto_mvp import fluxo as _produto_mvp
from .prospeccao import fluxo as _prospeccao

REGISTRO = {
    "novo-projeto": _novo_projeto,
    "produto-mvp": _produto_mvp,
    "campanha": _campanha,
    "prospeccao": _prospeccao,
    "diagnostico": _diagnostico,
    "pos-venda": _pos_venda,
    "decisao-estrategica": _decisao,
}


def obter(nome: str) -> Fluxo:
    fabrica = REGISTRO.get(nome)
    if fabrica is None:
        raise KeyError(f"fluxo '{nome}' nao existe. Disponiveis: {', '.join(sorted(REGISTRO))}")
    return fabrica()


def listar() -> list[tuple[str, str, int]]:
    """(nome, descricao, numero de etapas) de cada fluxo."""
    itens = []
    for nome, fabrica in REGISTRO.items():
        f = fabrica()
        itens.append((nome, f.descricao, len(f.etapas)))
    return itens


__all__ = ["REGISTRO", "obter", "listar", "Fluxo", "Etapa"]
