"""Memoria corporativa: historico de conversas e conhecimento compartilhado."""

from __future__ import annotations

import json
import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ESQUEMA = """
CREATE TABLE IF NOT EXISTS mensagens (
    id TEXT PRIMARY KEY,
    thread TEXT,
    projeto TEXT,
    remetente TEXT,
    destinatario TEXT,
    assunto TEXT,
    conteudo TEXT,
    tipo TEXT,
    prioridade TEXT,
    criada_em TEXT
);
CREATE INDEX IF NOT EXISTS idx_msg_projeto ON mensagens(projeto);
CREATE INDEX IF NOT EXISTS idx_msg_thread ON mensagens(thread);

CREATE TABLE IF NOT EXISTS conhecimento (
    chave TEXT PRIMARY KEY,
    valor TEXT,
    autor TEXT,
    escopo TEXT,
    atualizado_em TEXT
);

CREATE TABLE IF NOT EXISTS entregaveis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    projeto TEXT,
    agente TEXT,
    titulo TEXT,
    conteudo TEXT,
    criado_em TEXT
);
CREATE INDEX IF NOT EXISTS idx_ent_projeto ON entregaveis(projeto);
"""


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class Lembranca:
    papel: str
    texto: str


class MemoriaCurta:
    """Janela deslizante de turnos de um unico agente."""

    def __init__(self, max_turnos: int = 12) -> None:
        self.max_turnos = max_turnos
        self._itens: list[Lembranca] = []

    def registrar(self, papel: str, texto: str) -> None:
        self._itens.append(Lembranca(papel, texto))
        excedente = len(self._itens) - self.max_turnos
        if excedente > 0:
            del self._itens[:excedente]

    def como_mensagens(self) -> list[dict[str, str]]:
        return [{"role": i.papel, "content": i.texto} for i in self._itens]

    def limpar(self) -> None:
        self._itens.clear()

    def __len__(self) -> int:
        return len(self._itens)


class MemoriaCorporativa:
    """Persistencia em SQLite compartilhada por todos os agentes."""

    def __init__(self, caminho: str | Path = "data/movili.db") -> None:
        self.caminho = Path(caminho)
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(str(self.caminho), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            self._conn.executescript(ESQUEMA)
            self._conn.commit()

    # --- mensagens ----------------------------------------------------
    def salvar_mensagem(self, dados: dict[str, Any]) -> None:
        with self._lock:
            self._conn.execute(
                """INSERT OR REPLACE INTO mensagens
                   (id, thread, projeto, remetente, destinatario, assunto,
                    conteudo, tipo, prioridade, criada_em)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (
                    dados["id"],
                    dados.get("thread", ""),
                    dados.get("projeto", ""),
                    dados["remetente"],
                    dados["destinatario"],
                    dados.get("assunto", ""),
                    dados.get("conteudo", ""),
                    dados.get("tipo", "informe"),
                    dados.get("prioridade", "normal"),
                    dados.get("criada_em", _agora()),
                ),
            )
            self._conn.commit()

    def mensagens_do_projeto(self, projeto: str, limite: int = 200) -> list[dict[str, Any]]:
        with self._lock:
            cur = self._conn.execute(
                "SELECT * FROM mensagens WHERE projeto=? ORDER BY criada_em LIMIT ?",
                (projeto, limite),
            )
            return [dict(r) for r in cur.fetchall()]

    # --- conhecimento -------------------------------------------------
    def lembrar(self, chave: str, valor: Any, autor: str = "sistema", escopo: str = "empresa") -> None:
        texto = valor if isinstance(valor, str) else json.dumps(valor, ensure_ascii=False)
        with self._lock:
            self._conn.execute(
                """INSERT OR REPLACE INTO conhecimento (chave, valor, autor, escopo, atualizado_em)
                   VALUES (?,?,?,?,?)""",
                (chave, texto, autor, escopo, _agora()),
            )
            self._conn.commit()

    def recordar(self, chave: str, padrao: Any = None) -> Any:
        with self._lock:
            cur = self._conn.execute("SELECT valor FROM conhecimento WHERE chave=?", (chave,))
            linha = cur.fetchone()
        if linha is None:
            return padrao
        try:
            return json.loads(linha["valor"])
        except (json.JSONDecodeError, TypeError):
            return linha["valor"]

    def conhecimento_do_escopo(self, escopo: str) -> dict[str, Any]:
        with self._lock:
            cur = self._conn.execute(
                "SELECT chave, valor FROM conhecimento WHERE escopo=?", (escopo,)
            )
            return {r["chave"]: r["valor"] for r in cur.fetchall()}

    # --- entregaveis --------------------------------------------------
    def salvar_entregavel(self, projeto: str, agente: str, titulo: str, conteudo: str) -> int:
        with self._lock:
            cur = self._conn.execute(
                """INSERT INTO entregaveis (projeto, agente, titulo, conteudo, criado_em)
                   VALUES (?,?,?,?,?)""",
                (projeto, agente, titulo, conteudo, _agora()),
            )
            self._conn.commit()
            return int(cur.lastrowid)

    def entregaveis(self, projeto: str) -> list[dict[str, Any]]:
        with self._lock:
            cur = self._conn.execute(
                "SELECT * FROM entregaveis WHERE projeto=? ORDER BY id", (projeto,)
            )
            return [dict(r) for r in cur.fetchall()]

    def fechar(self) -> None:
        with self._lock:
            self._conn.close()
