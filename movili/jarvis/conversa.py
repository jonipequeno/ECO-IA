"""OpenJarvis: a recepcao conversacional da Movili.

O Jarvis nao e mais um funcionario - ele e a interface. Ele entende o que
voce quer, chama a pessoa certa da casa (ou a empresa inteira), e devolve
a resposta em linguagem falada, curta o bastante para ouvir.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .. import agentes as quadro
from .. import fluxos as processos
from ..core.orquestrador import Ecossistema
from ..llm.base import LLMIndisponivel

# Instrucao que transforma uma entrega escrita em fala natural.
ESTILO_FALADO = (
    "Voce esta FALANDO, nao escrevendo. Responda em portugues do Brasil, em no maximo "
    "{frases} frases curtas. Sem markdown, sem lista numerada, sem titulo, sem emoji. "
    "Numeros por extenso quando ficarem mais faceis de ouvir. Va direto ao ponto."
)

PADRAO_AGENTE = re.compile(r"^@([a-z_]+)\s*(.*)$", re.IGNORECASE | re.DOTALL)
PADRAO_CHAMADA = re.compile(
    r"\b(?:chama|chame|fala com|falar com|pergunta (?:pro|para o|pra)|"
    r"passa (?:pro|para o|pra))\s+(?:o |a )?([a-zA-ZçÇãÃéÉíÍóÓúÚâÂêÊôÔ_]+)",
    re.IGNORECASE,
)
PADRAO_REUNIAO = re.compile(r"\b(reuni[aã]o|reunir|mesa redonda|convoca[r]?)\b", re.IGNORECASE)
PADRAO_FLUXO = re.compile(
    r"\b(novo projeto|proposta|or[cç]amento de projeto|campanha|prospec[cç][aã]o|"
    r"diagn[oó]stico|mvp|p[oó]s-?venda|decis[aã]o estrat[eé]gica)\b",
    re.IGNORECASE,
)

MAPA_FLUXO = {
    "novo projeto": "novo-projeto",
    "proposta": "novo-projeto",
    "orcamento de projeto": "novo-projeto",
    "orçamento de projeto": "novo-projeto",
    "mvp": "produto-mvp",
    "campanha": "campanha",
    "prospeccao": "prospeccao",
    "prospecção": "prospeccao",
    "diagnostico": "diagnostico",
    "diagnóstico": "diagnostico",
    "pos-venda": "pos-venda",
    "pós-venda": "pos-venda",
    "posvenda": "pos-venda",
    "decisao estrategica": "decisao-estrategica",
    "decisão estratégica": "decisao-estrategica",
}

# Ids que tambem sao palavras comuns do dia a dia: so valem como mencao a
# uma pessoa quando vierem com verbo de chamada ou com "@".
IDS_AMBIGUOS = {
    "produto", "projetos", "design", "dados", "marketing", "copy",
    "comercial", "seguranca", "cs", "rh",
}

SAUDACAO = (
    "Jarvis na escuta. A Movili tem {n} pessoas disponiveis agora. "
    "Pode pedir direto, chamar alguem pelo nome, ou pedir uma reuniao."
)

AJUDA = (
    "Voce pode dizer: chama o financeiro e pergunta a margem de um projeto de duzentos mil; "
    "ou: monta uma proposta para um app de logistica; ou: convoca uma reuniao sobre entrar "
    "no mercado de saude. Diga sair para encerrar."
)


@dataclass
class Turno:
    quem: str
    texto: str
    em: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"))


class Jarvis:
    """Sessao conversacional sobre o ecossistema.

    Responsabilidades:
      1. entender a intencao do que foi dito (sem gastar modelo quando da);
      2. acionar o agente, o fluxo ou a reuniao correspondente;
      3. resumir a entrega em fala curta;
      4. manter o fio da conversa entre os turnos.
    """

    def __init__(
        self,
        eco: Ecossistema,
        *,
        frases: int = 4,
        voz_ativa: bool = False,
        porta_voz: str = quadro.ORQUESTRADOR,
    ) -> None:
        self.eco = eco
        self.frases = max(1, frases)
        self.voz_ativa = voz_ativa
        self.porta_voz = porta_voz if porta_voz in eco else next(iter(eco.agentes))
        self.historico: list[Turno] = []
        self.ultimo_agente: str | None = None
        self.ultimo_resultado: Any = None

    # ------------------------------------------------------------------
    def saudacao(self) -> str:
        return SAUDACAO.format(n=len(self.eco.agentes))

    def _lembrar(self, quem: str, texto: str) -> None:
        self.historico.append(Turno(quem, texto))
        if len(self.historico) > 20:
            del self.historico[:-20]

    def _contexto(self, limite: int = 6) -> str:
        if not self.historico:
            return ""
        linhas = [f"{t.quem}: {t.texto[:400]}" for t in self.historico[-limite:]]
        return "CONVERSA ATE AQUI\n" + "\n".join(linhas)

    # ------------------------------------------------------------------
    # Intencao
    # ------------------------------------------------------------------
    def interpretar(self, fala: str) -> dict[str, Any]:
        """Descobre a intencao. Primeiro por regra (barato), depois por modelo."""
        texto = fala.strip()
        baixo = texto.lower()

        if baixo in {"sair", "tchau", "encerrar", "/sair", "quit", "exit"}:
            return {"acao": "sair"}
        if baixo in {"ajuda", "help", "/ajuda", "o que voce faz", "o que você faz"}:
            return {"acao": "ajuda"}
        if baixo in {"equipe", "time", "/equipe", "quem trabalha aqui", "quem esta ai"}:
            return {"acao": "equipe"}

        # 1. mencao explicita: "@financeiro ..."
        casamento = PADRAO_AGENTE.match(texto)
        if casamento and casamento.group(1).lower() in self.eco:
            return {"acao": "agente", "alvo": casamento.group(1).lower(),
                    "pedido": casamento.group(2).strip() or texto}

        # 2. chamada explicita: "chama a Patricia", "pergunta pro financeiro"
        alvo = self._agente_chamado(texto)
        if alvo:
            return {"acao": "agente", "alvo": alvo, "pedido": texto}

        # 3. reuniao e fluxo vem ANTES da mencao solta, porque varios ids sao
        #    palavras comuns ("produto", "design", "dados") e apareceriam por
        #    acidente em frases como "quero uma campanha para o produto novo".
        if PADRAO_REUNIAO.search(baixo):
            return {"acao": "reuniao", "pedido": texto}

        achado = PADRAO_FLUXO.search(baixo)
        if achado:
            nome = MAPA_FLUXO.get(achado.group(1).lower())
            if nome:
                return {"acao": "fluxo", "alvo": nome, "pedido": texto}

        # 4. mencao solta: so por nome proprio ou por id que nao e palavra comum
        alvo = self._agente_citado(texto)
        if alvo:
            return {"acao": "agente", "alvo": alvo, "pedido": texto}

        return {"acao": "triagem", "pedido": texto}

    def _agente_chamado(self, texto: str) -> str | None:
        """Chamada explicita com verbo: 'chama o Rafael', 'fala com o juridico'."""
        chamada = PADRAO_CHAMADA.search(texto.lower())
        if not chamada:
            return None
        termo = chamada.group(1).lower()
        for ident, agente in self.eco.agentes.items():
            primeiro = agente.perfil.nome.split()[0].lower()
            if termo in {ident, primeiro}:
                return ident
        return None

    def _agente_citado(self, texto: str) -> str | None:
        """Mencao sem verbo de chamada. Conservador de proposito."""
        baixo = texto.lower()
        for ident, agente in self.eco.agentes.items():
            primeiro = agente.perfil.nome.split()[0].lower()
            if re.search(rf"\b{re.escape(primeiro)}\b", baixo):
                return ident
            if ident not in IDS_AMBIGUOS and re.search(rf"\b{re.escape(ident)}\b", baixo):
                return ident
        return None

    # ------------------------------------------------------------------
    # Execucao
    # ------------------------------------------------------------------
    def responder(self, fala: str) -> dict[str, Any]:
        """Processa um turno. Devolve {'fala': str, 'acao': str, 'detalhe': ...}."""
        self._lembrar("voce", fala)
        intencao = self.interpretar(fala)
        acao = intencao["acao"]

        try:
            if acao == "sair":
                saida = "Ate mais. A Movili fica de prontidao."
            elif acao == "ajuda":
                saida = AJUDA
            elif acao == "equipe":
                saida = self._falar_equipe()
            elif acao == "agente":
                saida = self._acionar_agente(intencao["alvo"], intencao["pedido"])
            elif acao == "reuniao":
                saida = self._convocar_reuniao(intencao["pedido"])
            elif acao == "fluxo":
                saida = self._rodar_fluxo(intencao["alvo"], intencao["pedido"])
            else:
                saida = self._triagem(intencao["pedido"])
        except LLMIndisponivel as exc:
            saida = (
                "Nao consegui falar com o modelo local. Confira se o Ollama ou o LM Studio "
                f"estao no ar. Detalhe tecnico: {str(exc)[:160]}"
            )
        except KeyError as exc:
            saida = f"Nao encontrei isso na casa. {exc}"

        self._lembrar("jarvis", saida)
        return {"acao": acao, "fala": saida, "detalhe": self.ultimo_resultado}

    def _falar_equipe(self) -> str:
        por_setor = []
        for setor, ids in quadro.SETORES.items():
            presentes = [self.eco.agentes[i].perfil.nome.split()[0] for i in ids if i in self.eco]
            if presentes:
                por_setor.append(f"{setor.replace('_', ' ')}: {', '.join(presentes)}")
        return "Temos " + "; ".join(por_setor) + "."

    def _acionar_agente(self, ident: str, pedido: str) -> str:
        agente = self.eco.agente(ident)
        self.ultimo_agente = ident
        instrucao = (
            f"{pedido}\n\n"
            + ESTILO_FALADO.format(frases=self.frases)
            + "\n\nSe a resposta completa exigir um documento, diga a conclusao em voz e "
            "avise que o detalhamento fica registrado no relatorio."
        )
        resultado = self.eco.delegar(
            ident, instrucao, contexto=self._contexto(), projeto="jarvis",
            remetente="jarvis",
        )
        self.ultimo_resultado = resultado
        return f"{agente.perfil.nome} responde: {resultado.entrega}"

    def _triagem(self, pedido: str) -> str:
        """Pergunta aberta: o porta-voz responde e chama reforco se precisar."""
        instrucao = (
            f"Chegou pelo Jarvis (canal de voz): {pedido}\n\n"
            + ESTILO_FALADO.format(frases=self.frases)
            + "\n\nSe isso exigir trabalho de outras areas, diga em uma frase quem voce vai "
            "acionar e o que vai pedir a cada um."
        )
        resultado = self.eco.delegar(
            self.porta_voz, instrucao, contexto=self._contexto(),
            projeto="jarvis", remetente="jarvis",
        )
        self.ultimo_resultado = resultado
        return resultado.entrega

    def _convocar_reuniao(self, pedido: str) -> str:
        tema = re.sub(
            r"^.*?(?:reuni[aã]o|reunir|mesa redonda|convocar?)\s*(?:sobre|de|para|com)?\s*",
            "", pedido, flags=re.IGNORECASE,
        ).strip() or pedido
        resultado = self.eco.reuniao(tema, rodadas=1, projeto="jarvis")
        self.ultimo_resultado = resultado
        return self._resumir_para_voz(
            f"reuniao sobre {tema}", resultado.consolidacao or resultado.markdown()
        )

    def _rodar_fluxo(self, nome: str, pedido: str) -> str:
        fluxo = processos.obter(nome)
        resultado = self.eco.executar_fluxo(fluxo, pedido, projeto="jarvis")
        self.ultimo_resultado = resultado
        return self._resumir_para_voz(fluxo.nome, resultado.consolidacao or resultado.markdown())

    def _resumir_para_voz(self, titulo: str, conteudo: str) -> str:
        """Comprime uma entrega longa em algo que da para ouvir."""
        instrucao = (
            f"Resuma para o cliente ouvir o resultado de: {titulo}.\n\n"
            f"MATERIAL COMPLETO:\n{conteudo[:6000]}\n\n"
            + ESTILO_FALADO.format(frases=self.frases + 2)
            + "\n\nComece pela conclusao. Termine dizendo que o relatorio completo ficou "
            "salvo no workspace."
        )
        return self.eco.agente(self.porta_voz).responder(
            instrucao, temperatura=0.4, max_tokens=500, usar_memoria=False, registrar=False
        )
