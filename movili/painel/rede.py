"""Rede Movili: os dados que a tela de rede neural consome.

Tres pecas, todas sem estado de servidor:

- topologia(): regioes, agentes e sinapses montados a partir das fichas em
  movili/agentes/ (o campo `interlocutores` de cada perfil);
- evento_da_mensagem(): converte uma Mensagem do barramento no evento que a
  tela entende - `registrar` para trafego entre agentes, `estimular` para
  demanda que chega de fora da empresa;
- ArquivoPesos: o que a rede aprendeu (peso de cada sinapse) persistido entre
  sessoes, para a topologia de hoje partir da de ontem.

O contrato do lado do navegador esta em painel/web/rede-movili/index.d.ts.
"""

from __future__ import annotations

import json
import os
import tempfile
import threading
from pathlib import Path
from typing import Any, Callable, Iterable

from .. import agentes as quadro
from ..core.mensagem import Mensagem, Tipo

# Destinatario de broadcast no barramento.
TODOS = "*"

# Resumo que viaja com o evento: curto, e so o assunto - nunca o conteudo da
# entrega, que pode ter dado de cliente.
LIMITE_TEXTO = 140

# 20 agentes -> no maximo 190 pares. Folga para o quadro crescer, teto para
# um POST malicioso nao encher o disco.
MAX_PESOS = 2000


def topologia(modelo_de: Callable[[str], str | None] | None = None) -> dict[str, Any]:
    """Topologia real da empresa no formato DadosTopologia do kit.

    `modelo_de(id)` devolve o modelo configurado para o agente; sem ele, ou
    sem modelo configurado, o campo vai null e a ficha mostra um travessao.
    """
    perfis = quadro.todos_os_perfis()
    regiao_de = {ident: setor for setor, ids in quadro.SETORES.items() for ident in ids}

    regioes = []
    for setor, ids in quadro.SETORES.items():
        nome = next((perfis[i].setor for i in ids if i in perfis), setor)
        regioes.append({"id": setor, "nome": nome})

    agentes = []
    for ident, p in perfis.items():
        agentes.append({
            "id": ident,
            "regiao": regiao_de.get(ident, ""),
            "nome": p.nome,
            "cargo": p.cargo,
            "modelo": (modelo_de(ident) if modelo_de else None) or None,
            # Perfil nao tem limiar: o campo fica de fora e a rede usa 0,5.
        })

    declaracoes = [(i, a) for i, p in perfis.items() for a in p.interlocutores if a != TODOS]
    declaradas = set(declaracoes)
    sinapses = sorted({tuple(sorted(par)) for par in declaracoes})
    reciprocas = sorted({tuple(sorted(par)) for par in declaracoes if par[::-1] in declaradas})
    return {
        "regioes": regioes,
        "agentes": agentes,
        "sinapses": [list(par) for par in sinapses],
        "reciprocas": [list(par) for par in reciprocas],
        "declaraTodos": [i for i, p in perfis.items() if TODOS in p.interlocutores],
    }


def resumir(texto: str, limite: int = LIMITE_TEXTO) -> str:
    corrido = " ".join((texto or "").split())
    return corrido if len(corrido) <= limite else corrido[: limite - 3].rstrip() + "..."


def evento_da_mensagem(mensagem: Mensagem, agentes: Iterable[str]) -> dict[str, Any] | None:
    """Traduz uma mensagem do barramento para a tela.

    Devolve {"acao": "registrar" | "estimular", "dados": {...}} ou None quando
    a mensagem nao tem o que mostrar na rede:

    - de agente para agente: registrar, com o tipo e a prioridade exatos;
    - informe (ou broadcast): registrar para a rede inteira, `para` = null;
    - de fora (painel, sistema, usuario) para um agente: estimular a partir
      dele. Sem afinidade: nao ha dado real de relevancia, os outros acendem
      quando participarem das mensagens;
    - de agente para fora (a entrega volta ao painel): registrar com `para`
      = null. Nao cruza sinapse, mas o agente acende e a troca entra na ficha
      dele - e o unico sinal na tela de que a pergunta feita ali foi atendida;
    - de agente para ele mesmo (o mediador na propria reuniao): nada.
    """
    conhecidos = set(agentes)
    de, para = mensagem.remetente, mensagem.destinatario
    texto = resumir(mensagem.assunto or mensagem.conteudo)

    if de not in conhecidos:
        if para in conhecidos:
            return {"acao": "estimular", "dados": {"no": para, "texto": texto}}
        return None

    if para == de:
        return None
    if mensagem.tipo == Tipo.INFORME or para not in conhecidos:
        para = None

    return {
        "acao": "registrar",
        "dados": {
            "tipo": mensagem.tipo.value,
            "de": de,
            "para": para,
            "prioridade": mensagem.prioridade.value,
            "texto": texto,
        },
    }


def chave_de_sinapse(a: str, b: str) -> str:
    """Chave de peso do kit: os dois ids em ordem alfabetica, separados por '|'."""
    x, y = sorted((a, b))
    return f"{x}|{y}"


def validar_pesos(bruto: Any, agentes: Iterable[str]) -> dict[str, float]:
    """Filtra o que veio do navegador: chave 'a|b' de agentes reais, valor em [0, 1]."""
    if not isinstance(bruto, dict):
        raise ValueError("pesos devem ser um objeto {\"a|b\": peso}")
    conhecidos = set(agentes)
    limpos: dict[str, float] = {}
    for chave, valor in list(bruto.items())[:MAX_PESOS]:
        partes = str(chave).split("|")
        if len(partes) != 2 or partes[0] == partes[1] or not set(partes) <= conhecidos:
            continue
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            continue
        if valor != valor:  # NaN
            continue
        limpos[chave_de_sinapse(*partes)] = min(1.0, max(0.0, float(valor)))
    return limpos


class ArquivoPesos:
    """Pesos aprendidos, num JSON com escrita atomica.

    Grava num temporario da mesma pasta e troca com os.replace: se o processo
    cair no meio, fica o arquivo antigo inteiro - nunca um JSON pela metade
    que zeraria o que a rede aprendeu.
    """

    def __init__(self, caminho: str | Path) -> None:
        self.caminho = Path(caminho)
        self._lock = threading.Lock()

    def carregar(self, agentes: Iterable[str]) -> dict[str, float]:
        try:
            bruto = json.loads(self.caminho.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        try:
            return validar_pesos(bruto, agentes)
        except ValueError:
            return {}

    def salvar(self, pesos: dict[str, float]) -> None:
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        dados = json.dumps(pesos, ensure_ascii=False, sort_keys=True, indent=1)
        with self._lock:
            descritor, temporario = tempfile.mkstemp(
                dir=self.caminho.parent, prefix=".pesos-", suffix=".tmp"
            )
            try:
                with os.fdopen(descritor, "w", encoding="utf-8") as arquivo:
                    arquivo.write(dados)
                os.replace(temporario, self.caminho)
            except BaseException:
                Path(temporario).unlink(missing_ok=True)
                raise
