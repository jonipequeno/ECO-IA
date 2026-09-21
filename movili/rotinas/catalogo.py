"""Os compromissos fixos da Movili: o calendario interno da empresa."""

from __future__ import annotations

from .modelo import Agendamento, Rotina

SEG_A_SEX = frozenset({0, 1, 2, 3, 4})


def catalogo() -> list[Rotina]:
    """Rotinas de fabrica. Edite aqui para ajustar o ritmo da sua operacao."""
    return [
        Rotina(
            id="daily",
            nome="Daily da engenharia",
            descricao=(
                "Alinhamento curto de produto e engenharia: o que avancou, o que travou "
                "e qual e o risco de prazo do dia."
            ),
            agendamento=Agendamento(hora=9, minuto=0, dias_da_semana=SEG_A_SEX),
            tipo="reuniao",
            alvo=(
                "Daily da engenharia: cada um diz em duas linhas o que entregou desde "
                "ontem, o que vai entregar hoje e o que esta travando. Se houver risco "
                "de prazo, diga qual marco e quantos dias."
            ),
            participantes=["projetos", "dev_backend", "dev_frontend", "dev_mobile", "produto"],
            rodadas=1,
        ),
        Rotina(
            id="pipeline",
            nome="Revisao semanal de pipeline",
            descricao=(
                "Comercial, prospeccao e marketing revisam o funil: o que entrou, o que "
                "avancou, o que esfriou e o forecast do mes."
            ),
            agendamento=Agendamento(hora=10, minuto=0, dias_da_semana=frozenset({0})),
            tipo="reuniao",
            alvo=(
                "Revisao semanal de pipeline. Cada area traz numero, nao impressao: "
                "leads gerados, reunioes agendadas, propostas em aberto, forecast do mes "
                "e o que precisa de decisao esta semana."
            ),
            participantes=["prospeccao", "comercial", "marketing", "financeiro"],
            rodadas=2,
        ),
        Rotina(
            id="seguranca",
            nome="Revisao de seguranca",
            descricao=(
                "Seguranca e engenharia revisam exposicao: dependencia vulneravel, "
                "segredo vazado, controle pendente e o que vai para producao."
            ),
            agendamento=Agendamento(hora=14, minuto=0, dias_da_semana=frozenset({2})),
            tipo="reuniao",
            alvo=(
                "Revisao semanal de seguranca. O que mudou na superficie de ataque, quais "
                "achados continuam abertos e o que esta previsto ir para producao nesta "
                "semana e ainda nao passou por modelagem de ameaca."
            ),
            participantes=["seguranca", "dev_backend", "dev_mobile", "socio_tecnologia"],
            rodadas=1,
        ),
        Rotina(
            id="saude-financeira",
            nome="Fecho financeiro da semana",
            descricao="Margem dos projetos em andamento, caixa e o que ameaca o mes.",
            agendamento=Agendamento(hora=16, minuto=0, dias_da_semana=frozenset({4})),
            tipo="agente",
            agente="financeiro",
            alvo=(
                "Feche a semana: margem dos projetos em andamento, posicao de caixa, "
                "contas a receber em risco e o que ameaca a meta do mes. Mostre a conta "
                "e termine com as tres acoes que voce precisa da operacao."
            ),
        ),
        Rotina(
            id="fechamento-mensal",
            nome="Fechamento do mes",
            descricao="Diretoria e financeiro fecham o mes e ajustam a meta do proximo.",
            agendamento=Agendamento(hora=9, minuto=0, dias_do_mes=frozenset({1})),
            tipo="reuniao",
            alvo=(
                "Fechamento do mes. Resultado contra a meta, margem media dos projetos "
                "entregues, CAC e retencao. Cada area diz o que muda no proximo mes."
            ),
            participantes=["diretor", "financeiro", "comercial", "marketing", "rh", "cs"],
            rodadas=2,
        ),
        Rotina(
            id="conselho",
            nome="Conselho trimestral de socios",
            descricao="Os socios revisam a tese da empresa e o que muda no trimestre.",
            agendamento=Agendamento(
                hora=9, minuto=0, dias_do_mes=frozenset({1}), meses=frozenset({1, 4, 7, 10})
            ),
            tipo="reuniao",
            alvo=(
                "Conselho trimestral. A tese da empresa continua valendo? O que os numeros "
                "do trimestre provaram ou desmentiram, onde estamos concentrados demais e "
                "o que a empresa precisa parar de fazer."
            ),
            participantes=["socio_estrategia", "socio_tecnologia", "diretor", "financeiro"],
            rodadas=2,
        ),
        Rotina(
            id="higiene-memoria",
            nome="Higiene da memoria semantica",
            descricao=(
                "Manutencao: confere o indice semantico e avisa se ha trechos orfaos "
                "de uma troca de modelo de embedding. Nao gasta modelo de linguagem."
            ),
            agendamento=Agendamento(hora=3, minuto=0, dias_da_semana=frozenset({6})),
            tipo="manutencao",
            alvo="memoria",
        ),
    ]


REGISTRO = {r.id: r for r in catalogo()}


def obter(ident: str) -> Rotina:
    rotina = REGISTRO.get(ident)
    if rotina is None:
        raise KeyError(f"rotina '{ident}' nao existe. Disponiveis: {', '.join(sorted(REGISTRO))}")
    return rotina
