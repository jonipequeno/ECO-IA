"""Pos-venda: onboarding, suporte, retencao e expansao de contrato."""

from __future__ import annotations

from ..core.orquestrador import Etapa, Fluxo


def fluxo() -> Fluxo:
    return Fluxo(
        nome="Pos-venda e retencao",
        descricao=(
            "CS conduz o cliente depois da entrega, dados medem adocao, produto e "
            "engenharia tratam o feedback e o comercial trabalha a expansao."
        ),
        etapas=[
            Etapa(
                agente="cs",
                rotulo="Situacao do cliente e plano",
                instrucao=(
                    "Avalie a situacao do cliente descrito: health score, sinais de risco e "
                    "plano de onboarding ou de recuperacao com marcos. Consolide o feedback "
                    "em problemas acionaveis, priorizados."
                ),
            ),
            Etapa(
                agente="dados",
                rotulo="Leitura de adocao e churn",
                usa_saida_de=["cs"],
                instrucao=(
                    "Defina quais metricas comprovam (ou nao) o que o CS esta relatando: "
                    "adocao por funcionalidade, coorte, frequencia de uso e sinal antecedente "
                    "de churn. Diga o que ainda nao esta instrumentado."
                ),
            ),
            Etapa(
                agente="produto",
                rotulo="Priorizacao do feedback",
                usa_saida_de=["cs", "dados"],
                instrucao=(
                    "Transforme o feedback em itens de backlog com criterio de aceite e "
                    "prioridade. Separe bug de melhoria e de pedido fora de escopo contratado."
                ),
            ),
            Etapa(
                agente="dev_mobile",
                rotulo="Correcao, SLA e estabilidade",
                usa_saida_de=["produto", "cs"],
                instrucao=(
                    "Avalie os itens criticos: o que da para corrigir dentro do SLA, o que "
                    "exige janela de manutencao e o que precisa de teste de regressao. Diga o "
                    "plano de release e o rollback."
                ),
            ),
            Etapa(
                agente="comercial",
                rotulo="Renovacao e expansao",
                usa_saida_de=["cs", "produto"],
                instrucao=(
                    "Monte a estrategia de renovacao e a proposta de expansao: o que o cliente "
                    "ja demonstrou precisar, qual o valor a apresentar e como tratar o que "
                    "ficou fora do contrato atual."
                ),
            ),
            Etapa(
                agente="financeiro",
                rotulo="Rentabilidade da conta",
                usa_saida_de=["cs", "comercial", "dev_mobile"],
                instrucao=(
                    "Calcule a rentabilidade real desta conta considerando as horas gastas em "
                    "suporte e correcao. Diga se a renovacao deve vir com reajuste e de quanto."
                ),
            ),
        ],
    )
