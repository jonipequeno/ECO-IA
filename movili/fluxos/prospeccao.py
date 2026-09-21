"""Campanha de prospeccao outbound."""

from __future__ import annotations

from ..core.orquestrador import Etapa, Fluxo


def fluxo() -> Fluxo:
    return Fluxo(
        nome="Prospeccao outbound",
        descricao=(
            "SDR define ICP e cadencia, copy refina as mensagens, juridico valida frente "
            "a LGPD, comercial prepara o fechamento e o financeiro confere o custo por "
            "reuniao agendada."
        ),
        etapas=[
            Etapa(
                agente="prospeccao",
                rotulo="ICP, listas e cadencia",
                instrucao=(
                    "Defina o ICP com criterios de inclusao e exclusao, os segmentos e onde "
                    "conseguir cada lista. Monte a cadencia completa (toque, canal, dia, "
                    "objetivo) e escreva a primeira versao das mensagens."
                ),
            ),
            Etapa(
                agente="copy",
                rotulo="Refino das mensagens",
                usa_saida_de=["prospeccao"],
                instrucao=(
                    "Reescreva as mensagens da cadencia para maximizar taxa de resposta: "
                    "assunto curto, primeira linha sobre o prospect e nao sobre a Movili, "
                    "uma unica pergunta de fechamento. Entregue 3 variacoes de cada e-mail."
                ),
            ),
            Etapa(
                agente="juridico",
                rotulo="Conformidade LGPD da cadencia",
                usa_saida_de=["prospeccao", "copy"],
                instrucao=(
                    "Avalie a cadencia e as mensagens frente a LGPD (base legal de interesse "
                    "legitimo, direito de oposicao, origem do dado) e as boas praticas de "
                    "comunicacao comercial. Aponte o que precisa mudar e escreva o opt-out."
                ),
            ),
            Etapa(
                agente="comercial",
                rotulo="Handoff e roteiro de reuniao",
                usa_saida_de=["prospeccao", "copy"],
                instrucao=(
                    "Defina o criterio de aceite do lead vindo do SDR e escreva o roteiro da "
                    "primeira reuniao: perguntas de diagnostico, sinais de fit e de nao-fit, "
                    "e como voce conduz ao proximo passo."
                ),
            ),
            Etapa(
                agente="financeiro",
                rotulo="Custo por reuniao e viabilidade",
                usa_saida_de=["prospeccao", "comercial"],
                instrucao=(
                    "Calcule o custo por reuniao agendada e o CAC projetado deste canal, com "
                    "as premissas de taxa de resposta e de conversao da cadencia. Diga se o "
                    "canal se paga no ticket medio da casa."
                ),
            ),
        ],
    )
