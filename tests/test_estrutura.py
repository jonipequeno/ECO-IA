"""A empresa esta montada e consistente."""

from __future__ import annotations

from movili import agentes as quadro
from movili import fluxos as processos


def test_todos_os_perfis_carregam():
    perfis = quadro.todos_os_perfis()
    assert len(perfis) == len(quadro.REGISTRO)
    for ident, p in perfis.items():
        assert p.id == ident
        assert p.nome and " " in p.nome, f"{ident} precisa de nome proprio completo"
        assert p.cargo and p.setor
        assert p.missao, f"{ident} sem missao definida"
        assert p.especialidades and p.responsabilidades and p.kpis


def test_quadro_minimo_pedido():
    """O nucleo solicitado: 3 devs e as seis areas de negocio."""
    devs = [i for i in quadro.REGISTRO if i.startswith("dev_")]
    assert len(devs) == 3
    for area in ("marketing", "seo", "copy", "comercial", "prospeccao", "financeiro"):
        assert area in quadro.REGISTRO


def test_socios_e_areas_de_apoio():
    assert quadro.CONSELHO == ["socio_estrategia", "socio_tecnologia"]
    for ident in ("produto", "projetos", "seguranca", "juridico", "rh", "cs", "dados", "design"):
        assert ident in quadro.REGISTRO


def test_produto_e_projetos_sao_papeis_distintos():
    pm = quadro.perfil_de("produto")
    pmo = quadro.perfil_de("projetos")
    assert pm.nome != pmo.nome
    assert "Product Manager" in pm.cargo
    assert "Gerente de Projetos" in pmo.cargo


def test_setores_cobrem_todos_os_agentes():
    de_setores = {i for ids in quadro.SETORES.values() for i in ids}
    assert de_setores == set(quadro.REGISTRO)


def test_ids_de_interlocutores_existem():
    for ident, p in quadro.todos_os_perfis().items():
        for outro in p.interlocutores:
            if outro == "*":
                continue
            assert outro in quadro.REGISTRO, f"{ident} cita colega inexistente: {outro}"


def test_fluxos_so_acionam_agentes_existentes():
    for nome in processos.REGISTRO:
        fluxo = processos.obter(nome)
        assert fluxo.etapas, f"fluxo '{nome}' esta vazio"
        for etapa in fluxo.etapas:
            assert etapa.agente in quadro.REGISTRO, f"{nome} -> {etapa.agente}"
            assert etapa.instrucao.strip()
            for dep in etapa.usa_saida_de:
                assert dep in quadro.REGISTRO


def test_dependencia_de_etapa_vem_antes():
    """Uma etapa nao pode usar a saida de quem ainda nao trabalhou."""
    for nome in processos.REGISTRO:
        fluxo = processos.obter(nome)
        ja_atuaram: set[str] = set()
        for etapa in fluxo.etapas:
            for dep in etapa.usa_saida_de:
                assert dep in ja_atuaram, f"{nome}: {etapa.agente} depende de {dep}, que ainda nao atuou"
            ja_atuaram.add(etapa.agente)


def test_organograma_lista_todo_mundo():
    texto = quadro.organograma()
    for ident in quadro.REGISTRO:
        assert f"@{ident}" in texto
