"""Do briefing do cliente ate a proposta comercial assinavel."""

from __future__ import annotations

from ..core.orquestrador import Etapa, Fluxo


def fluxo() -> Fluxo:
    return Fluxo(
        nome="Novo projeto - do briefing a proposta",
        descricao=(
            "Cliente traz uma demanda. Comercial qualifica, engenharia dimensiona, "
            "produto escopa, RH confere capacidade, financeiro precifica, juridico "
            "revisa e a diretoria fecha a proposta."
        ),
        etapas=[
            Etapa(
                agente="comercial",
                rotulo="Qualificacao e briefing comercial",
                instrucao=(
                    "Qualifique esta oportunidade e transforme o pedido do cliente em um "
                    "briefing tecnico para a engenharia. Liste o que ficou ambiguo e as "
                    "perguntas que precisam ser feitas ao cliente antes de fechar escopo."
                ),
            ),
            Etapa(
                agente="dev_backend",
                rotulo="Arquitetura e estimativa de engenharia",
                usa_saida_de=["comercial"],
                instrucao=(
                    "Com base no briefing comercial, proponha a arquitetura da solucao, o "
                    "modelo de dados e os contratos de API principais. Estime as horas de "
                    "backend por entregavel e aponte os riscos tecnicos."
                ),
            ),
            Etapa(
                agente="produto",
                rotulo="Problema, MVP e criterios de aceite",
                usa_saida_de=["comercial", "dev_backend"],
                instrucao=(
                    "Defina o problema de negocio e a metrica de sucesso. Quebre o projeto "
                    "em epicos e historias com criterio de aceite testavel, delimite o MVP "
                    "e diga o que fica para a fase 2 e por que."
                ),
            ),
            Etapa(
                agente="seguranca",
                rotulo="Modelagem de ameaca e controles",
                usa_saida_de=["dev_backend", "produto"],
                instrucao=(
                    "Faca a modelagem de ameaca desta arquitetura (STRIDE): ativos, vetores "
                    "e impacto. Defina os controles obrigatorios, os requisitos de pipeline "
                    "(SAST, SCA, segredo) e estime as horas de seguranca do projeto."
                ),
            ),
            Etapa(
                agente="design",
                rotulo="Jornada e especificacao de interface",
                usa_saida_de=["produto"],
                instrucao=(
                    "Desenhe a jornada do usuario e especifique as telas do MVP: blocos, "
                    "hierarquia, estados e CTA. Entregue algo que o frontend consiga "
                    "implementar sem adivinhar."
                ),
            ),
            Etapa(
                agente="dev_frontend",
                rotulo="Plano de frontend e estimativa",
                usa_saida_de=["produto", "design", "dev_backend"],
                paralelo_com=["dev_mobile"],
                instrucao=(
                    "Defina a arquitetura de componentes e rotas do frontend, estime as "
                    "horas por tela e liste exatamente o que voce precisa do backend."
                ),
            ),
            Etapa(
                agente="dev_mobile",
                rotulo="Estrategia mobile, CI/CD e qualidade",
                usa_saida_de=["produto", "dev_backend"],
                instrucao=(
                    "Defina a estrategia mobile, o pipeline de CI/CD e o plano de testes. "
                    "Estime as horas de mobile e DevOps e aponte o que pode quebrar em "
                    "producao nesta arquitetura."
                ),
            ),
            Etapa(
                agente="projetos",
                rotulo="Cronograma, caminho critico e riscos",
                usa_saida_de=["produto", "dev_backend", "dev_frontend", "dev_mobile", "seguranca"],
                instrucao=(
                    "Monte o cronograma real do projeto com marcos, caminho critico e "
                    "dependencias entre as frentes. Entregue a matriz de riscos com plano "
                    "de resposta e a alocacao necessaria por perfil e periodo."
                ),
            ),
            Etapa(
                agente="rh",
                rotulo="Capacidade do time e custo de pessoas",
                usa_saida_de=["dev_backend", "dev_frontend", "dev_mobile", "projetos"],
                instrucao=(
                    "Some as horas estimadas pelas tres frentes de engenharia e diga se o "
                    "time atual comporta este projeto no cronograma proposto. Informe o "
                    "custo de pessoas por mes e o que falta contratar ou realocar."
                ),
            ),
            Etapa(
                agente="financeiro",
                rotulo="Precificacao e margem",
                usa_saida_de=["dev_backend", "dev_frontend", "dev_mobile", "projetos", "rh", "seguranca"],
                instrucao=(
                    "Precifique o projeto a partir das horas estimadas e do custo de pessoas. "
                    "Mostre a memoria de calculo aberta, o preco minimo e o ideal, a margem "
                    "resultante e o fluxo de caixa por marco. Se a margem ficar abaixo da "
                    "minima da casa, diga o que precisa mudar."
                ),
            ),
            Etapa(
                agente="juridico",
                rotulo="Risco contratual e clausulas",
                usa_saida_de=["produto", "financeiro", "comercial", "seguranca"],
                instrucao=(
                    "Revise o escopo e as condicoes comerciais. Aponte os riscos contratuais, "
                    "as clausulas necessarias (propriedade intelectual, SLA, multa, rescisao) "
                    "e a base legal LGPD aplicavel aos dados que o sistema vai tratar."
                ),
            ),
            Etapa(
                agente="comercial",
                rotulo="Proposta comercial final",
                usa_saida_de=["produto", "projetos", "financeiro", "juridico"],
                instrucao=(
                    "Monte a proposta comercial final para o cliente: escopo em entregaveis, "
                    "investimento, prazo, condicoes de pagamento, o que nao esta incluso e as "
                    "objecoes esperadas com resposta. Respeite o preco do financeiro e as "
                    "ressalvas do juridico."
                ),
            ),
        ],
        instrucao_consolidacao=(
            "Aprove, ajuste ou reprove esta proposta como CEO. Diga o preco final que vai "
            "ao cliente, o prazo que a casa assume, os riscos que voce aceita e o que ficou "
            "fora. Se engenharia, financeiro e comercial divergirem, decida voce."
        ),
    )
