"""Barramento de mensagens: o 'Slack interno' da Movili.

Todo agente publica e assina topicos aqui. E o que faz o ecossistema
conversar de verdade em vez de ser uma fila linear de chamadas.
"""

from __future__ import annotations

import json
import threading
from collections import defaultdict, deque
from pathlib import Path
from typing import Callable, Iterable

from .mensagem import Mensagem, Prioridade, Tipo

Assinante = Callable[[Mensagem], None]


class Barramento:
    """Pub/sub em memoria, thread-safe, com historico auditavel."""

    def __init__(self, limite_historico: int = 5000, verboso: bool = False) -> None:
        self._assinantes: dict[str, list[Assinante]] = defaultdict(list)
        self._caixas: dict[str, deque[Mensagem]] = defaultdict(deque)
        self._lock = threading.RLock()
        self.historico: deque[Mensagem] = deque(maxlen=limite_historico)
        self.verboso = verboso
        self._observadores: list[Assinante] = []

    # --- assinatura ---------------------------------------------------
    def assinar(self, destinatario: str, callback: Assinante) -> None:
        """Registra um agente para receber mensagens endercadas a ele."""
        with self._lock:
            self._assinantes[destinatario].append(callback)

    def observar(self, callback: Assinante) -> None:
        """Registra um observador que ve TODO o trafego (log, UI, auditoria)."""
        with self._lock:
            self._observadores.append(callback)

    # --- publicacao ---------------------------------------------------
    def publicar(self, mensagem: Mensagem) -> Mensagem:
        with self._lock:
            self.historico.append(mensagem)
            observadores = list(self._observadores)
            if mensagem.broadcast:
                alvos = [d for d in self._assinantes if d != mensagem.remetente]
            else:
                alvos = [mensagem.destinatario]
            entregas: list[tuple[str, list[Assinante]]] = [
                (alvo, list(self._assinantes.get(alvo, []))) for alvo in alvos
            ]
            for alvo in alvos:
                self._caixas[alvo].append(mensagem)

        if self.verboso:
            print(f"  ~ {mensagem.resumo()}")

        for obs in observadores:
            obs(mensagem)
        for _alvo, callbacks in entregas:
            for cb in callbacks:
                cb(mensagem)
        return mensagem

    def enviar(
        self,
        remetente: str,
        destinatario: str,
        assunto: str,
        conteudo: str,
        *,
        tipo: Tipo = Tipo.INFORME,
        prioridade: Prioridade = Prioridade.NORMAL,
        thread: str = "",
        projeto: str = "",
        anexos: dict | None = None,
    ) -> Mensagem:
        """Atalho para montar e publicar uma mensagem."""
        return self.publicar(
            Mensagem(
                remetente=remetente,
                destinatario=destinatario,
                assunto=assunto,
                conteudo=conteudo,
                tipo=tipo,
                prioridade=prioridade,
                thread=thread,
                projeto=projeto,
                anexos=anexos or {},
            )
        )

    # --- leitura ------------------------------------------------------
    def caixa_de_entrada(self, destinatario: str, limpar: bool = True) -> list[Mensagem]:
        with self._lock:
            caixa = self._caixas.get(destinatario)
            if not caixa:
                return []
            itens = list(caixa)
            if limpar:
                caixa.clear()
            return itens

    def thread(self, thread_id: str) -> list[Mensagem]:
        return [m for m in self.historico if m.thread == thread_id]

    def por_projeto(self, projeto: str) -> list[Mensagem]:
        return [m for m in self.historico if m.projeto == projeto]

    def transcricao(self, mensagens: Iterable[Mensagem] | None = None) -> str:
        fonte = list(mensagens if mensagens is not None else self.historico)
        return "\n".join(m.resumo(400) for m in fonte)

    # --- persistencia -------------------------------------------------
    def exportar(self, caminho: str | Path) -> Path:
        destino = Path(caminho)
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(
            json.dumps([m.to_dict() for m in self.historico], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return destino

    def limpar(self) -> None:
        with self._lock:
            self.historico.clear()
            self._caixas.clear()
