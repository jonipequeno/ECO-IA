"""Mensagem trocada entre os agentes da Movili."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class Tipo(str, Enum):
    """Natureza da mensagem no barramento corporativo."""

    BRIEFING = "briefing"        # demanda entrando na empresa
    TAREFA = "tarefa"            # atribuicao direta a um agente
    ENTREGA = "entrega"          # resultado de uma tarefa
    PERGUNTA = "pergunta"        # agente pedindo informacao a outro
    RESPOSTA = "resposta"        # retorno de uma pergunta
    REVISAO = "revisao"          # critica/aprovacao de uma entrega
    DECISAO = "decisao"          # deliberacao da lideranca
    ALERTA = "alerta"            # risco, bloqueio ou erro
    INFORME = "informe"          # comunicado geral (broadcast)


class Prioridade(str, Enum):
    BAIXA = "baixa"
    NORMAL = "normal"
    ALTA = "alta"
    CRITICA = "critica"


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class Mensagem:
    """Unidade de comunicacao do ecossistema.

    `destinatario` em "*" significa broadcast para toda a empresa.
    """

    remetente: str
    destinatario: str
    assunto: str
    conteudo: str
    tipo: Tipo = Tipo.INFORME
    prioridade: Prioridade = Prioridade.NORMAL
    thread: str = ""
    projeto: str = ""
    anexos: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    criada_em: str = field(default_factory=_agora)

    def __post_init__(self) -> None:
        if isinstance(self.tipo, str):
            self.tipo = Tipo(self.tipo)
        if isinstance(self.prioridade, str):
            self.prioridade = Prioridade(self.prioridade)
        if not self.thread:
            self.thread = self.id

    @property
    def broadcast(self) -> bool:
        return self.destinatario == "*"

    def responder(
        self,
        remetente: str,
        conteudo: str,
        *,
        tipo: Tipo = Tipo.RESPOSTA,
        assunto: str | None = None,
        anexos: dict[str, Any] | None = None,
    ) -> "Mensagem":
        """Cria a resposta mantendo a mesma thread e projeto."""
        return Mensagem(
            remetente=remetente,
            destinatario=self.remetente,
            assunto=assunto or f"Re: {self.assunto}",
            conteudo=conteudo,
            tipo=tipo,
            prioridade=self.prioridade,
            thread=self.thread,
            projeto=self.projeto,
            anexos=anexos or {},
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "thread": self.thread,
            "projeto": self.projeto,
            "remetente": self.remetente,
            "destinatario": self.destinatario,
            "assunto": self.assunto,
            "conteudo": self.conteudo,
            "tipo": self.tipo.value,
            "prioridade": self.prioridade.value,
            "anexos": self.anexos,
            "criada_em": self.criada_em,
        }

    @classmethod
    def from_dict(cls, dados: dict[str, Any]) -> "Mensagem":
        return cls(
            remetente=dados["remetente"],
            destinatario=dados["destinatario"],
            assunto=dados.get("assunto", ""),
            conteudo=dados.get("conteudo", ""),
            tipo=Tipo(dados.get("tipo", "informe")),
            prioridade=Prioridade(dados.get("prioridade", "normal")),
            thread=dados.get("thread", ""),
            projeto=dados.get("projeto", ""),
            anexos=dados.get("anexos", {}) or {},
            id=dados.get("id") or uuid.uuid4().hex[:12],
            criada_em=dados.get("criada_em") or _agora(),
        )

    def resumo(self, limite: int = 220) -> str:
        corpo = " ".join(self.conteudo.split())
        if len(corpo) > limite:
            corpo = corpo[: limite - 3] + "..."
        return f"[{self.tipo.value}] {self.remetente} -> {self.destinatario}: {self.assunto} | {corpo}"
