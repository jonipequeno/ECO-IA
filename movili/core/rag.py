"""Memoria semantica da Movili: busca no que a empresa ja produziu.

Sem isto, cada execucao comeca do zero. Com isto, quando o comercial recebe
um briefing de logistica, ele ve o que o arquiteto decidiu no ultimo projeto
de logistica e quanto o financeiro cobrou por ele.

Armazenamento em SQLite (mesmo banco da memoria corporativa) e busca por
similaridade de cosseno em Python puro - sem banco vetorial externo.
"""

from __future__ import annotations

import json
import math
import re
import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from ..llm.base import LLMIndisponivel
from ..llm.router import RoteadorLLM

ESQUEMA = """
CREATE TABLE IF NOT EXISTS vetores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    origem TEXT NOT NULL,
    referencia TEXT NOT NULL,
    projeto TEXT,
    agente TEXT,
    titulo TEXT,
    trecho TEXT NOT NULL,
    vetor TEXT NOT NULL,
    modelo TEXT,
    criado_em TEXT,
    UNIQUE(origem, referencia)
);
CREATE INDEX IF NOT EXISTS idx_vet_projeto ON vetores(projeto);
CREATE INDEX IF NOT EXISTS idx_vet_agente ON vetores(agente);
"""

# Um pedaco por vez: grande o bastante para ter contexto, pequeno o bastante
# para a busca ser precisa e caber na janela do modelo.
TAMANHO_TRECHO = 1200
SOBREPOSICAO = 150

# Caractere de escape do LIKE. Ver _padrao_de_referencia().
ESCAPE_LIKE = "\\"


def _padrao_de_referencia(referencia: str) -> str:
    """Monta o padrao LIKE que casa com os trechos de UM documento.

    '_' e '%' sao curingas no LIKE do SQL. Sem escapar, reindexar
    'docs/a_b.md' apagaria silenciosamente os trechos de 'docs/aXb.md',
    porque '_' casa qualquer caractere. Referencias vem de caminho de
    arquivo informado pelo usuario, entao isso acontece de verdade.
    """
    escapada = (
        referencia.replace(ESCAPE_LIKE, ESCAPE_LIKE + ESCAPE_LIKE)
        .replace("%", ESCAPE_LIKE + "%")
        .replace("_", ESCAPE_LIKE + "_")
    )
    return f"{escapada}#%"


@dataclass
class Achado:
    """Um trecho recuperado da memoria, com a proveniencia."""

    trecho: str
    similaridade: float
    projeto: str
    agente: str
    titulo: str
    criado_em: str

    def citacao(self, limite: int = 700) -> str:
        corpo = self.trecho if len(self.trecho) <= limite else self.trecho[:limite] + "..."
        origem = f"{self.agente or 'equipe'}"
        if self.projeto:
            origem += f", projeto {self.projeto}"
        return f"[{origem} | relevancia {self.similaridade:.0%}]\n{corpo}"


def fatiar(texto: str, tamanho: int = TAMANHO_TRECHO, sobreposicao: int = SOBREPOSICAO) -> list[str]:
    """Quebra um texto longo em trechos, cortando em fim de paragrafo quando da."""
    texto = texto.strip()
    if not texto:
        return []
    if len(texto) <= tamanho:
        return [texto]

    trechos: list[str] = []
    inicio = 0
    while inicio < len(texto):
        fim = min(inicio + tamanho, len(texto))
        if fim < len(texto):
            # tenta cortar num limite natural, de tras para frente
            for separador in ("\n\n", "\n", ". "):
                corte = texto.rfind(separador, inicio + tamanho // 2, fim)
                if corte != -1:
                    fim = corte + len(separador)
                    break
        pedaco = texto[inicio:fim].strip()
        if pedaco:
            trechos.append(pedaco)
        if fim >= len(texto):
            break
        inicio = max(fim - sobreposicao, inicio + 1)
    return trechos


def cosseno(a: Iterable[float], b: Iterable[float]) -> float:
    """Similaridade de cosseno. Devolve 0.0 para vetor nulo ou de tamanho diferente."""
    va, vb = list(a), list(b)
    if len(va) != len(vb) or not va:
        return 0.0
    produto = sum(x * y for x, y in zip(va, vb))
    na = math.sqrt(sum(x * x for x in va))
    nb = math.sqrt(sum(x * x for x in vb))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return produto / (na * nb)


class MemoriaSemantica:
    """Indice vetorial sobre os entregaveis e conversas da empresa."""

    def __init__(
        self,
        roteador: RoteadorLLM,
        caminho: str | Path = "data/movili.db",
        *,
        modelo: str = "nomic-embed-text",
        backend: str | None = None,
    ) -> None:
        self.roteador = roteador
        self.modelo = modelo
        self.backend = backend
        # Preenchida na primeira vetorizacao: "<backend>/<modelo>". Vetores de
        # assinaturas diferentes nunca sao comparados entre si.
        self._assinatura: str = ""
        self.caminho = Path(caminho)
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(str(self.caminho), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            self._conn.executescript(ESQUEMA)
            self._conn.commit()

    # ------------------------------------------------------------------
    # Indexacao
    # ------------------------------------------------------------------
    def indexar(
        self,
        texto: str,
        *,
        origem: str,
        referencia: str,
        projeto: str = "",
        agente: str = "",
        titulo: str = "",
    ) -> int:
        """Indexa um documento. Devolve quantos trechos entraram.

        `referencia` identifica o documento: reindexar a mesma referencia
        substitui os trechos antigos em vez de duplicar.
        """
        trechos = fatiar(texto)
        if not trechos:
            return 0

        vetores, origem = self.roteador.vetorizar_com_origem(
            trechos, backend=self.backend, modelo=self.modelo
        )
        assinatura = self._registrar_assinatura(origem)
        agora = datetime.now(timezone.utc).isoformat(timespec="seconds")

        with self._lock:
            self._conn.execute(
                f"DELETE FROM vetores WHERE origem=? AND referencia LIKE ? ESCAPE '{ESCAPE_LIKE}'",
                (origem, _padrao_de_referencia(referencia)),
            )
            self._conn.executemany(
                """INSERT OR REPLACE INTO vetores
                   (origem, referencia, projeto, agente, titulo, trecho, vetor, modelo, criado_em)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                [
                    (origem, f"{referencia}#{i}", projeto, agente, titulo,
                     trecho, json.dumps(vetor), assinatura, agora)
                    for i, (trecho, vetor) in enumerate(zip(trechos, vetores))
                ],
            )
            self._conn.commit()
        return len(trechos)

    def indexar_entregaveis(self, memoria_corporativa, projeto: str) -> int:
        """Indexa todos os entregaveis de um projeto ja gravados no SQLite."""
        total = 0
        for item in memoria_corporativa.entregaveis(projeto):
            total += self.indexar(
                item["conteudo"],
                origem="entregavel",
                referencia=f"entregavel-{item['id']}",
                projeto=item["projeto"],
                agente=item["agente"],
                titulo=item["titulo"],
            )
        return total

    # ------------------------------------------------------------------
    # Busca
    # ------------------------------------------------------------------
    def buscar(
        self,
        consulta: str,
        *,
        limite: int = 4,
        minimo: float = 0.25,
        agente: str | None = None,
        projeto: str | None = None,
        excluir_projeto: str | None = None,
    ) -> list[Achado]:
        """Recupera os trechos mais parecidos com a consulta.

        `excluir_projeto` evita que o projeto em andamento recupere a si
        mesmo - o interessante e o que a empresa fez ANTES.
        """
        if not consulta.strip():
            return []
        try:
            vetores, origem = self.roteador.vetorizar_com_origem(
                [consulta], backend=self.backend, modelo=self.modelo
            )
        except LLMIndisponivel:
            return []  # sem modelo de embedding a empresa segue, so sem memoria
        vetor_consulta = vetores[0]
        assinatura = self._registrar_assinatura(origem)

        # So compara vetores produzidos pelo mesmo backend e modelo: cosseno
        # entre espacos vetoriais diferentes nao significa nada.
        sql = "SELECT * FROM vetores WHERE modelo=?"
        args: list[object] = [assinatura]
        if agente:
            sql += " AND agente=?"
            args.append(agente)
        if projeto:
            sql += " AND projeto=?"
            args.append(projeto)
        if excluir_projeto:
            sql += " AND projeto<>?"
            args.append(excluir_projeto)

        with self._lock:
            linhas = self._conn.execute(sql, args).fetchall()

        pontuados: list[Achado] = []
        for linha in linhas:
            try:
                vetor = json.loads(linha["vetor"])
            except (json.JSONDecodeError, TypeError):
                continue
            score = cosseno(vetor_consulta, vetor)
            if score >= minimo:
                pontuados.append(
                    Achado(
                        trecho=linha["trecho"],
                        similaridade=score,
                        projeto=linha["projeto"] or "",
                        agente=linha["agente"] or "",
                        titulo=linha["titulo"] or "",
                        criado_em=linha["criado_em"] or "",
                    )
                )
        pontuados.sort(key=lambda a: a.similaridade, reverse=True)
        return pontuados[:limite]

    def contexto(self, consulta: str, **kwargs) -> str:
        """Monta o bloco de memoria que vai no prompt do agente."""
        achados = self.buscar(consulta, **kwargs)
        if not achados:
            return ""
        return (
            "MEMORIA DA EMPRESA (trabalho anterior da Movili, use como referencia "
            "e diga quando estiver reaproveitando uma decisao)\n\n"
            + "\n\n".join(a.citacao() for a in achados)
        )

    def _registrar_assinatura(self, backend: str) -> str:
        self._assinatura = f"{backend}/{self.modelo}"
        return self._assinatura

    @property
    def assinatura(self) -> str:
        """Procedencia dos vetores desta sessao, no formato '<backend>/<modelo>'."""
        return self._assinatura or f"{self.backend or 'auto'}/{self.modelo}"

    # ------------------------------------------------------------------
    def estatisticas(self) -> dict[str, object]:
        with self._lock:
            total = self._conn.execute("SELECT COUNT(*) c FROM vetores").fetchone()["c"]
            projetos = self._conn.execute(
                "SELECT projeto, COUNT(*) c FROM vetores WHERE projeto<>'' "
                "GROUP BY projeto ORDER BY c DESC"
            ).fetchall()
            agentes = self._conn.execute(
                "SELECT agente, COUNT(*) c FROM vetores WHERE agente<>'' "
                "GROUP BY agente ORDER BY c DESC"
            ).fetchall()
            assinaturas = self._conn.execute(
                "SELECT modelo, COUNT(*) c FROM vetores GROUP BY modelo ORDER BY c DESC"
            ).fetchall()
        por_assinatura = {r["modelo"]: r["c"] for r in assinaturas}
        return {
            "trechos": total,
            "projetos": {r["projeto"]: r["c"] for r in projetos},
            "agentes": {r["agente"]: r["c"] for r in agentes},
            "assinaturas": por_assinatura,
            # Trechos gravados por outro backend/modelo sao invisiveis para a
            # busca atual - reindexe se quiser recupera-los.
            "inativos": sum(c for a, c in por_assinatura.items() if a != self.assinatura),
        }

    def limpar(self, projeto: str | None = None) -> int:
        with self._lock:
            if projeto:
                cur = self._conn.execute("DELETE FROM vetores WHERE projeto=?", (projeto,))
            else:
                cur = self._conn.execute("DELETE FROM vetores")
            self._conn.commit()
            return cur.rowcount

    def fechar(self) -> None:
        with self._lock:
            self._conn.close()
