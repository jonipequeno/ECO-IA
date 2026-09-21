"""Diagnostico tecnico de sistema legado (servico de entrada da Movili)."""

from __future__ import annotations

from ..core.orquestrador import Etapa, Fluxo


def fluxo() -> Fluxo:
    return Fluxo(
        nome="Diagnostico tecnico de legado",
        descricao=(
            "Engenharia audita o sistema existente, produto prioriza a modernizacao, "
            "juridico olha dado pessoal e o financeiro precifica o plano de evolucao."
        ),
        etapas=[
            Etapa(
                agente="dev_backend",
                rotulo="Auditoria de arquitetura e codigo",
                instrucao=(
                    "Audite o sistema descrito: arquitetura, modelo de dados, acoplamento, "
                    "divida tecnica e seguranca (OWASP). Classifique cada achado por "
                    "severidade e esforco de correcao."
                ),
            ),
            Etapa(
                agente="dev_mobile",
                rotulo="Infraestrutura, deploy e qualidade",
                usa_saida_de=["dev_backend"],
                instrucao=(
                    "Avalie infraestrutura, processo de deploy, cobertura de testes e "
                    "observabilidade. Diga qual e o maior risco de producao hoje e o que "
                    "daria para estabilizar em 30 dias."
                ),
            ),
            Etapa(
                agente="dados",
                rotulo="Qualidade e governanca de dados",
                usa_saida_de=["dev_backend"],
                instrucao=(
                    "Avalie a qualidade dos dados, a instrumentacao existente e o que a "
                    "empresa consegue (ou nao consegue) medir hoje com esse sistema."
                ),
            ),
            Etapa(
                agente="seguranca",
                rotulo="Auditoria de seguranca do legado",
                usa_saida_de=["dev_backend", "dev_mobile"],
                instrucao=(
                    "Audite o sistema pelo angulo do atacante: autenticacao, autorizacao, "
                    "exposicao de dado, dependencia vulneravel e segredo em codigo. "
                    "Classifique por risco e diga o que precisa ser corrigido em 30 dias."
                ),
            ),
            Etapa(
                agente="produto",
                rotulo="Roadmap de modernizacao",
                usa_saida_de=["dev_backend", "dev_mobile", "dados", "seguranca"],
                instrucao=(
                    "Priorize os achados em um roadmap de modernizacao por ondas, com "
                    "objetivo de negocio de cada onda e criterio de sucesso. Separe o que e "
                    "urgente do que e desejavel."
                ),
            ),
            Etapa(
                agente="juridico",
                rotulo="Exposicao regulatoria",
                usa_saida_de=["dev_backend", "dados", "seguranca"],
                instrucao=(
                    "Aponte a exposicao regulatoria do sistema atual (LGPD, retencao, "
                    "consentimento, seguranca de dado pessoal) e o que precisa ser corrigido "
                    "com prioridade."
                ),
            ),
            Etapa(
                agente="financeiro",
                rotulo="Investimento do plano de modernizacao",
                usa_saida_de=["produto", "dev_backend", "dev_mobile", "seguranca"],
                instrucao=(
                    "Precifique cada onda do roadmap, com memoria de calculo, e compare o "
                    "investimento com o custo de manter o legado como esta (risco, retrabalho, "
                    "indisponibilidade)."
                ),
            ),
        ],
    )
