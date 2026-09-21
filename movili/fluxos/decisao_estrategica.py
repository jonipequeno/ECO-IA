"""Decisao estrategica levada ao conselho de socios."""

from __future__ import annotations

from ..core.orquestrador import Etapa, Fluxo


def fluxo() -> Fluxo:
    return Fluxo(
        nome="Decisao estrategica do conselho",
        descricao=(
            "Uma decisao grande (novo mercado, novo produto, mudanca de modelo, "
            "investimento pesado) sobe para os dois socios, com os numeros da casa "
            "e o parecer das areas afetadas."
        ),
        etapas=[
            Etapa(
                agente="diretor",
                rotulo="Enquadramento da decisao",
                instrucao=(
                    "Enquadre a decisao para o conselho: o que exatamente esta sendo "
                    "decidido, quais sao as opcoes reais, o que ja foi tentado e qual o "
                    "prazo para decidir. Nao opine ainda - estruture."
                ),
            ),
            Etapa(
                agente="financeiro",
                rotulo="Numeros e viabilidade",
                usa_saida_de=["diretor"],
                instrucao=(
                    "Traga os numeros que sustentam ou derrubam cada opcao: investimento, "
                    "impacto em caixa, margem, payback e ponto de equilibrio. Mostre a conta."
                ),
            ),
            Etapa(
                agente="marketing",
                rotulo="Mercado e posicionamento",
                usa_saida_de=["diretor"],
                paralelo_com=["comercial"],
                instrucao=(
                    "Avalie o mercado: tamanho, concorrencia, quanto custaria construir "
                    "demanda nesse espaco e se a marca da Movili sustenta esse movimento."
                ),
            ),
            Etapa(
                agente="comercial",
                rotulo="Leitura de demanda real",
                usa_saida_de=["diretor"],
                instrucao=(
                    "Diga o que o pipeline real mostra sobre esta decisao: tem cliente "
                    "pedindo? Quanto estariam dispostos a pagar? O que voce ja ouviu de "
                    "objecao nesse tema?"
                ),
            ),
            Etapa(
                agente="socio_tecnologia",
                rotulo="Parecer tecnico do socio",
                usa_saida_de=["diretor", "financeiro"],
                instrucao=(
                    "De o seu parecer como socio e CTO: o que a casa precisa construir, o "
                    "custo de manutencao em 3 anos, o que vira ativo reutilizavel e quais "
                    "riscos tecnicos a empresa estaria assumindo. Aprova, condiciona ou veta?"
                ),
            ),
            Etapa(
                agente="socio_estrategia",
                rotulo="Parecer estrategico da socia",
                usa_saida_de=["diretor", "financeiro", "marketing", "comercial", "socio_tecnologia"],
                instrucao=(
                    "De o seu parecer como socia e CSO: o que isso faz com a tese da empresa "
                    "em 12, 24 e 60 meses, qual o custo de oportunidade e o que voce veta. "
                    "Se discordar do socio de tecnologia, diga onde e por que."
                ),
            ),
        ],
        consolidador="diretor",
        instrucao_consolidacao=(
            "Como CEO, feche a decisao respeitando os pareceres dos socios. Se os dois "
            "socios divergirem, explicite a divergencia e diga qual caminho a operacao vai "
            "seguir e sob qual condicao isso sera revisto. Termine com decisao, responsavel "
            "e prazo."
        ),
    )
