"""Quadro de funcionarios da Movili Tecnologia.

Cada modulo deste pacote define o perfil de um funcionario senior. O
registro abaixo e a fonte unica de verdade do organograma - o orquestrador,
a CLI e a API leem daqui.
"""

from __future__ import annotations

from typing import Callable

from ..core.agente import Perfil
from . import (
    comercial,
    copy,
    cs,
    dados,
    design,
    dev_backend,
    dev_frontend,
    dev_mobile,
    diretor,
    financeiro,
    juridico,
    marketing,
    produto,
    projetos,
    prospeccao,
    rh,
    seguranca,
    seo,
    socio_estrategia,
    socio_tecnologia,
)

_MODULOS = [
    socio_estrategia,
    socio_tecnologia,
    diretor,
    produto,
    projetos,
    design,
    dev_backend,
    dev_frontend,
    dev_mobile,
    dados,
    marketing,
    seo,
    copy,
    prospeccao,
    comercial,
    financeiro,
    juridico,
    seguranca,
    rh,
    cs,
]

# Fabricas de perfil, na ordem do organograma.
REGISTRO: dict[str, Callable[[], Perfil]] = {m.ID: m.perfil for m in _MODULOS}

# Quem coordena o ecossistema no dia a dia (os socios sao conselho, nao operacao).
ORQUESTRADOR = diretor.ID

# Conselho societario: acionado em decisao estrategica e em veto.
CONSELHO = [socio_estrategia.ID, socio_tecnologia.ID]

# Agrupamento por setor, usado em reunioes departamentais.
SETORES: dict[str, list[str]] = {
    "socios": [socio_estrategia.ID, socio_tecnologia.ID],
    "diretoria": [diretor.ID],
    "produto": [produto.ID, projetos.ID, design.ID],
    "engenharia": [dev_backend.ID, dev_frontend.ID, dev_mobile.ID],
    "dados": [dados.ID],
    "marketing": [marketing.ID, seo.ID, copy.ID],
    "comercial": [prospeccao.ID, comercial.ID],
    "financeiro": [financeiro.ID],
    "juridico": [juridico.ID],
    "seguranca": [seguranca.ID],
    "pessoas": [rh.ID],
    "sucesso_do_cliente": [cs.ID],
}


def todos_os_perfis() -> dict[str, Perfil]:
    """Instancia todos os perfis do organograma."""
    return {ident: fabrica() for ident, fabrica in REGISTRO.items()}


def perfil_de(ident: str) -> Perfil:
    """Instancia um perfil pelo identificador, com erro legivel."""
    fabrica = REGISTRO.get(ident)
    if fabrica is None:
        raise KeyError(
            f"agente '{ident}' nao existe. Disponiveis: {', '.join(sorted(REGISTRO))}"
        )
    return fabrica()


def organograma() -> str:
    """Texto do organograma, usado na CLI e nos prompts de reuniao."""
    linhas: list[str] = []
    perfis = todos_os_perfis()
    for setor, ids in SETORES.items():
        linhas.append(f"{setor.replace('_', ' ').upper()}")
        for ident in ids:
            p = perfis[ident]
            linhas.append(f"  @{ident:<14} {p.nome} - {p.cargo}")
    return "\n".join(linhas)


__all__ = [
    "REGISTRO",
    "SETORES",
    "ORQUESTRADOR",
    "CONSELHO",
    "todos_os_perfis",
    "perfil_de",
    "organograma",
]
