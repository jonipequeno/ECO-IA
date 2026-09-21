"""Descoberta e construcao de um MVP interno ou de cliente."""

from __future__ import annotations

from ..core.orquestrador import Etapa, Fluxo


def fluxo() -> Fluxo:
    return Fluxo(
        nome="Produto - descoberta ao MVP",
        descricao=(
            "Produto descobre, design desenha, engenharia constroi e dados instrumenta. "
            "Sem passar pelo comercial: usado para produto proprio ou squad alocada."
        ),
        etapas=[
            Etapa(
                agente="produto",
                rotulo="Descoberta e definicao do MVP",
                instrucao=(
                    "Faca a descoberta: qual problema, de quem, como e resolvido hoje e qual "
                    "a metrica de sucesso. Defina o MVP com epicos, historias e criterio de "
                    "aceite, e diga explicitamente o que NAO entra."
                ),
            ),
            Etapa(
                agente="design",
                rotulo="Jornada, fluxo e interface",
                usa_saida_de=["produto"],
                instrucao=(
                    "Mapeie a jornada, desenhe o fluxo de telas e especifique a interface do "
                    "MVP com tokens e componentes. Inclua o checklist de acessibilidade."
                ),
            ),
            Etapa(
                agente="dev_backend",
                rotulo="Arquitetura e backend",
                usa_saida_de=["produto"],
                instrucao=(
                    "Desenhe a arquitetura do MVP priorizando simplicidade e velocidade de "
                    "entrega, sem hipotecar o futuro. Entregue modelo de dados, contratos de "
                    "API e o codigo de referencia dos pontos criticos."
                ),
            ),
            Etapa(
                agente="dev_frontend",
                rotulo="Implementacao do frontend",
                usa_saida_de=["design", "dev_backend"],
                paralelo_com=["dev_mobile"],
                instrucao=(
                    "Implemente a arquitetura de componentes do MVP a partir do design e dos "
                    "contratos do backend. Entregue o codigo dos componentes principais."
                ),
            ),
            Etapa(
                agente="dev_mobile",
                rotulo="Mobile, pipeline e testes",
                usa_saida_de=["design", "dev_backend"],
                instrucao=(
                    "Defina a estrategia mobile do MVP, monte o pipeline de CI/CD e escreva o "
                    "plano de testes com os casos criticos de regressao."
                ),
            ),
            Etapa(
                agente="seguranca",
                rotulo="Seguranca do MVP",
                usa_saida_de=["dev_backend", "produto"],
                instrucao=(
                    "Modele as ameacas do MVP e defina o conjunto minimo de controles que "
                    "NAO pode ser adiado para depois do lancamento. Separe o que e "
                    "obrigatorio agora do que pode entrar na fase 2."
                ),
            ),
            Etapa(
                agente="projetos",
                rotulo="Cronograma do MVP",
                usa_saida_de=["produto", "dev_backend", "dev_frontend", "dev_mobile"],
                instrucao=(
                    "Monte o cronograma do MVP com marcos semanais, caminho critico e a "
                    "matriz de riscos. Diga qual e a data realista de lancamento."
                ),
            ),
            Etapa(
                agente="dados",
                rotulo="Instrumentacao e metricas",
                usa_saida_de=["produto", "design", "dev_backend"],
                instrucao=(
                    "Monte o plano de tracking do MVP: eventos, propriedades e quando cada um "
                    "dispara. Defina as metricas de ativacao e retencao e a estrutura do painel."
                ),
            ),
        ],
    )
