"""Campanha de marketing de ponta a ponta."""

from __future__ import annotations

from ..core.orquestrador import Etapa, Fluxo


def fluxo() -> Fluxo:
    return Fluxo(
        nome="Campanha de marketing",
        descricao=(
            "Marketing define a estrategia, SEO mapeia a busca, copy escreve, design "
            "especifica a landing, frontend implementa, dados instrumenta e o financeiro "
            "aprova o orcamento pelo CAC."
        ),
        etapas=[
            Etapa(
                agente="marketing",
                rotulo="Estrategia e plano de campanha",
                instrucao=(
                    "Monte a estrategia da campanha: diagnostico, publico, oferta, canais com "
                    "papel no funil, orcamento sugerido, cronograma e metas numericas. Diga o "
                    "que voce precisa de SEO, copy e financeiro."
                ),
            ),
            Etapa(
                agente="seo",
                rotulo="Mapa de palavras-chave e SEO tecnico",
                usa_saida_de=["marketing"],
                instrucao=(
                    "Entregue o mapa de palavras-chave por intencao de busca, a arquitetura "
                    "de conteudo em clusters e os requisitos tecnicos de SEO para as paginas "
                    "da campanha. Briefe o copywriter sobre o que cada pagina precisa ranquear."
                ),
            ),
            Etapa(
                agente="copy",
                rotulo="Textos da campanha",
                usa_saida_de=["marketing", "seo"],
                instrucao=(
                    "Escreva os textos finais: landing page completa, 5 anuncios por canal, "
                    "sequencia de 4 e-mails e 3 variacoes de headline para teste A/B. Cubra as "
                    "palavras-chave do SEO sem forcar a leitura."
                ),
            ),
            Etapa(
                agente="design",
                rotulo="Especificacao visual da landing",
                usa_saida_de=["copy", "marketing"],
                instrucao=(
                    "Especifique a landing page: blocos na ordem, hierarquia visual, "
                    "posicionamento de CTA, prova social e estados. Foque em conversao."
                ),
            ),
            Etapa(
                agente="dev_frontend",
                rotulo="Implementacao da landing",
                usa_saida_de=["design", "seo", "copy"],
                instrucao=(
                    "Implemente a landing page em Next.js com o texto do copy e os requisitos "
                    "tecnicos do SEO. Entregue o codigo e o plano de Core Web Vitals."
                ),
            ),
            Etapa(
                agente="dados",
                rotulo="Tracking e leitura de resultado",
                usa_saida_de=["marketing", "dev_frontend"],
                instrucao=(
                    "Monte o plano de tracking da campanha, o desenho do teste A/B (com "
                    "tamanho de amostra minimo) e o painel de acompanhamento por canal."
                ),
            ),
            Etapa(
                agente="financeiro",
                rotulo="Aprovacao do orcamento de midia",
                usa_saida_de=["marketing", "dados"],
                instrucao=(
                    "Analise o orcamento proposto pelo marketing contra o CAC e o LTV da casa. "
                    "Calcule o ROAS minimo para a campanha se pagar e de o parecer: aprova, "
                    "aprova com corte, ou reprova. Mostre a conta."
                ),
            ),
            Etapa(
                agente="comercial",
                rotulo="Preparo do time comercial",
                usa_saida_de=["marketing", "copy"],
                instrucao=(
                    "Diga como o comercial vai receber e tratar os leads desta campanha: "
                    "criterio de qualificacao, SLA de contato, script de abordagem e as "
                    "objecoes que voce espera deste publico."
                ),
            ),
        ],
    )
