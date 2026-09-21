"""Passeio guiado pelo ecossistema: prova que tudo esta de pe, em minutos.

Serve para duas situacoes:

  1. Na sua maquina, com Ollama ou LM Studio no ar: e o teste de fumaca do
     setup. Se o demo passa, o ecossistema inteiro funciona com modelo real.
  2. Sem backend nenhum (--backend simulado): exercita todo o encanamento -
     barramento, fluxos, reunioes, memoria, relatorios - deixando claro, em
     cada passo, que a inteligencia esta desligada.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from . import agentes as quadro
from . import fluxos as processos
from .core.orquestrador import Ecossistema
from .llm.base import LLMIndisponivel

BRIEFING = (
    "Transportadora de carga refrigerada com 80 caminhoes quer um app de "
    "roteirizacao com rastreamento em tempo real, integrado ao ERP Protheus. "
    "Orcamento indicado de R$ 200 mil, prazo de 4 meses."
)

TEMA_REUNIAO = "Vale a pena a Movili criar uma vertical so para logistica?"


@dataclass
class Passo:
    titulo: str
    detalhe: str = ""
    duracao_s: float = 0.0
    numeros: dict[str, Any] = field(default_factory=dict)
    erro: str = ""

    @property
    def ok(self) -> bool:
        return not self.erro


class Demo:
    """Roda o passeio e coleta os numeros de cada etapa."""

    def __init__(self, eco: Ecossistema, rapido: bool = False) -> None:
        self.eco = eco
        self.rapido = rapido
        self.passos: list[Passo] = []
        self.projeto = f"demo-{datetime.now():%Y%m%d-%H%M%S}"

    # ------------------------------------------------------------------
    def _faixa(self, texto: str) -> None:
        print(f"\n{'=' * 70}\n  {texto}\n{'=' * 70}")

    def _passo(self, numero: int, titulo: str, explicacao: str) -> None:
        print(f"\n--- {numero}. {titulo} ---")
        print(f"    {explicacao}\n")

    def _executar(self, passo: Passo, funcao) -> Passo:
        inicio = time.monotonic()
        try:
            funcao(passo)
        except LLMIndisponivel as exc:
            passo.erro = str(exc)
        except Exception as exc:
            passo.erro = f"{type(exc).__name__}: {exc}"
        passo.duracao_s = time.monotonic() - inicio
        self.passos.append(passo)
        marca = "ok" if passo.ok else "FALHOU"
        print(f"    [{marca}] {passo.detalhe or passo.erro} ({passo.duracao_s:.1f}s)")
        return passo

    # ------------------------------------------------------------------
    def rodar(self) -> int:
        real = self._backend_real()
        self._faixa("MOVILI TECNOLOGIA - DEMONSTRACAO DO ECOSSISTEMA")
        if real:
            print(f"\n  Backend em uso: {real}. As respostas abaixo sao de modelo de verdade.")
        else:
            print(
                "\n  ATENCAO: nenhum backend real respondeu - rodando no modo simulado.\n"
                "  Todo o encanamento e real (barramento, fluxos, memoria, relatorios),\n"
                "  mas as RESPOSTAS dos agentes sao marcadores, nao texto de modelo.\n"
                "  Para ver o ecossistema pensando: suba o Ollama e rode de novo."
            )

        self._passo(1, "A empresa existe", "20 funcionarios com ficha, cargo e modelo proprio.")
        self._executar(Passo("quadro"), self._ver_quadro)

        self._passo(2, "Um funcionario trabalha",
                    "O arquiteto recebe o briefing e responde na area dele.")
        self._executar(Passo("agente"), self._um_agente)

        self._passo(3, "As areas conversam entre si",
                    "Um fluxo completo: cada etapa recebe a entrega das anteriores.")
        self._executar(Passo("fluxo"), self._um_fluxo)

        self._passo(4, "Elas discordam e decidem",
                    "Reuniao: cada area traz sua posicao e o CEO fecha a ata.")
        self._executar(Passo("reuniao"), self._uma_reuniao)

        self._passo(5, "A empresa lembra",
                    "O trabalho anterior volta como contexto num projeto parecido.")
        self._executar(Passo("memoria"), self._memoria)

        self._passo(6, "Fica tudo registrado",
                    "Relatorio, JSON e o trafego completo do barramento, em disco.")
        self._executar(Passo("saida"), self._saida)

        return self._resumo(real)

    # ------------------------------------------------------------------
    def _backend_real(self) -> str | None:
        for nome, info in self.eco.roteador.status().items():
            if info["online"] and nome != "simulado":
                return f"{nome} ({info['modelo_padrao']})"
        return None

    def _ver_quadro(self, passo: Passo) -> None:
        for setor, ids in quadro.SETORES.items():
            presentes = [self.eco.agentes[i].perfil.nome.split()[0] for i in ids if i in self.eco]
            if presentes:
                print(f"      {setor.replace('_', ' '):<20} {', '.join(presentes)}")
        passo.numeros = {"agentes": len(self.eco.agentes), "fluxos": len(processos.REGISTRO)}
        passo.detalhe = f"{len(self.eco.agentes)} ativos, {len(processos.REGISTRO)} processos"

    def _um_agente(self, passo: Passo) -> None:
        resultado = self.eco.delegar(
            "dev_backend",
            f"{BRIEFING}\n\nEm ate 8 linhas: que arquitetura voce propoe e qual o maior risco tecnico?",
            projeto=self.projeto,
        )
        print(self._recortar(resultado.entrega, 12))
        passo.numeros = {"caracteres": len(resultado.entrega)}
        passo.detalhe = f"{resultado.nome_agente} respondeu {len(resultado.entrega)} caracteres"

    def _um_fluxo(self, passo: Passo) -> None:
        nome = "prospeccao" if self.rapido else "novo-projeto"
        resultado = self.eco.executar_fluxo(
            processos.obter(nome), BRIEFING, projeto=self.projeto, consolidar=not self.rapido
        )
        self.resultado_fluxo = resultado
        for etapa in resultado.etapas:
            print(f"      {etapa.nome_agente:<20} {etapa.duracao_s:>6.1f}s  {etapa.cargo[:38]}")
        passo.numeros = {"etapas": len(resultado.etapas)}
        passo.detalhe = f"fluxo '{nome}': {len(resultado.etapas)} entregas encadeadas"

    def _uma_reuniao(self, passo: Passo) -> None:
        presentes = [i for i in ("socio_estrategia", "dev_backend", "comercial", "financeiro")
                     if i in self.eco]
        resultado = self.eco.reuniao(
            TEMA_REUNIAO, participantes=presentes, rodadas=1, projeto=self.projeto
        )
        self.resultado_reuniao = resultado
        if resultado.consolidacao:
            print("      ATA FINAL (recorte):")
            print(self._recortar(resultado.consolidacao, 8))
        passo.numeros = {"falas": len(resultado.etapas)}
        passo.detalhe = f"{len(resultado.etapas)} falas e ata final"

    def _memoria(self, passo: Passo) -> None:
        if self.eco.semantica is None:
            passo.detalhe = "memoria semantica desligada (sem modelo de embedding)"
            return
        s = self.eco.semantica.estatisticas()
        achados = self.eco.semantica.buscar(
            "rastreamento de frota com integracao ao ERP para transportadora",
            limite=2, minimo=0.2,
        )
        for a in achados:
            print(f"      {a.similaridade:.0%}  {a.agente:<14} {a.trecho[:60].strip()}...")
        passo.numeros = {"trechos": s["trechos"], "recuperados": len(achados)}
        passo.detalhe = (
            f"{s['trechos']} trechos indexados, {len(achados)} recuperados "
            f"({self.eco.semantica.assinatura})"
        )

    def _saida(self, passo: Passo) -> None:
        caminhos = self.eco.salvar(self.resultado_fluxo)
        tamanho = caminhos["relatorio"].stat().st_size
        mensagens = len(self.eco.barramento.por_projeto(self.projeto))
        for rotulo, caminho in caminhos.items():
            print(f"      {rotulo:<12} {caminho}")
        passo.numeros = {"bytes": tamanho, "mensagens": mensagens}
        passo.detalhe = f"relatorio de {tamanho // 1024} KB, {mensagens} mensagens no barramento"

    # ------------------------------------------------------------------
    @staticmethod
    def _recortar(texto: str, linhas: int) -> str:
        corpo = [l for l in texto.strip().splitlines() if l.strip()][:linhas]
        saida = "\n".join(f"      {l[:90]}" for l in corpo)
        return saida + ("\n      [...]" if len(texto.splitlines()) > linhas else "")

    def _resumo(self, real: str | None) -> int:
        self._faixa("RESUMO")
        falhas = [p for p in self.passos if not p.ok]
        total = sum(p.duracao_s for p in self.passos)

        for p in self.passos:
            marca = "ok    " if p.ok else "FALHOU"
            print(f"  [{marca}] {p.titulo:<10} {p.duracao_s:>6.1f}s  {p.detalhe or p.erro}")

        metricas = self.eco.metricas()
        chamadas = sum(m["chamadas"] for m in metricas.values())
        tokens = sum(m["tokens_entrada"] + m["tokens_saida"] for m in metricas.values())
        print(f"\n  {len(self.passos)} passos em {total:.1f}s")
        print(f"  {chamadas} chamadas de modelo, ~{tokens} tokens, {len(metricas)} agentes acionados")

        if falhas:
            print(f"\n  {len(falhas)} passo(s) falharam. Rode 'movili status' para ver os backends.")
            return 1
        if real:
            print(f"\n  Tudo funcionando com modelo real em {real}.")
        else:
            print(
                "\n  O encanamento inteiro funcionou. Para ver com modelo de verdade:\n"
                "    ollama serve\n"
                "    ollama pull qwen3:8b\n"
                "    movili demo"
            )
        return 0
