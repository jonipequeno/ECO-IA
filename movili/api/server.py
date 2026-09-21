"""API HTTP do ecossistema Movili (FastAPI).

Opcional: a CLI e a ponte OpenJarvis funcionam sem isto. Use quando quiser
integrar o ecossistema a um painel, a um CRM ou a outro sistema.

    pip install -r requirements-api.txt
    movili api --porta 8000
    # docs interativas em http://localhost:8000/docs
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .. import agentes as quadro
from .. import fluxos as processos
from ..config import carregar
from ..core.orquestrador import Ecossistema
from ..jarvis.conversa import Jarvis
from ..llm.base import LLMIndisponivel

app = FastAPI(
    title="Movili Tecnologia - Ecossistema de Agentes",
    description="Empresa de software operada por agentes de IA locais (Ollama / LM Studio).",
    version="1.0.0",
)

_eco: Ecossistema | None = None
_jarvis: Jarvis | None = None


def obter_eco() -> Ecossistema:
    global _eco, _jarvis
    if _eco is None:
        _eco = Ecossistema(carregar(), verboso=False)
        _jarvis = Jarvis(_eco, frases=6)
    return _eco


def obter_jarvis() -> Jarvis:
    obter_eco()
    assert _jarvis is not None
    return _jarvis


# ---------------------------------------------------------------------
class PedidoAgente(BaseModel):
    instrucao: str = Field(..., description="A tarefa para o funcionario")
    projeto: str = ""


class PedidoFluxo(BaseModel):
    briefing: str
    projeto: str = ""


class PedidoReuniao(BaseModel):
    tema: str
    participantes: list[str] | None = None
    rodadas: int = 2


class PedidoJarvis(BaseModel):
    mensagem: str


class PedidoBusca(BaseModel):
    consulta: str
    limite: int = 5
    minimo: float = 0.25
    agente: str | None = None
    projeto: str | None = None


# ---------------------------------------------------------------------
@app.get("/")
def raiz() -> dict[str, Any]:
    return {
        "empresa": "Movili Tecnologia",
        "agentes": len(quadro.REGISTRO),
        "fluxos": sorted(processos.REGISTRO),
        "docs": "/docs",
    }


@app.get("/equipe")
def equipe() -> list[dict[str, Any]]:
    return [
        {
            "id": ident,
            "nome": p.nome,
            "cargo": p.cargo,
            "setor": p.setor,
            "senioridade": p.senioridade,
            "especialidades": p.especialidades,
            "kpis": p.kpis,
        }
        for ident, p in quadro.todos_os_perfis().items()
    ]


@app.get("/status")
def status() -> dict[str, Any]:
    return obter_eco().roteador.status()


@app.get("/fluxos")
def fluxos() -> list[dict[str, Any]]:
    return [
        {"nome": n, "descricao": d, "etapas": q,
         "ordem": [e.agente for e in processos.obter(n).etapas]}
        for n, d, q in processos.listar()
    ]


@app.post("/agente/{ident}")
def falar_com_agente(ident: str, pedido: PedidoAgente) -> dict[str, Any]:
    eco = obter_eco()
    if ident not in eco:
        raise HTTPException(404, f"agente '{ident}' nao existe")
    try:
        r = eco.delegar(ident, pedido.instrucao, projeto=pedido.projeto or "api")
    except LLMIndisponivel as exc:
        raise HTTPException(503, str(exc)) from exc
    return {"agente": r.agente, "nome": r.nome_agente, "cargo": r.cargo,
            "entrega": r.entrega, "duracao_s": round(r.duracao_s, 1)}


@app.post("/fluxo/{nome}")
def executar_fluxo(nome: str, pedido: PedidoFluxo) -> dict[str, Any]:
    if nome not in processos.REGISTRO:
        raise HTTPException(404, f"fluxo '{nome}' nao existe")
    eco = obter_eco()
    try:
        r = eco.executar_fluxo(processos.obter(nome), pedido.briefing, projeto=pedido.projeto)
    except LLMIndisponivel as exc:
        raise HTTPException(503, str(exc)) from exc
    eco.salvar(r)
    return r.to_dict()


@app.post("/reuniao")
def reuniao(pedido: PedidoReuniao) -> dict[str, Any]:
    eco = obter_eco()
    try:
        r = eco.reuniao(pedido.tema, participantes=pedido.participantes, rodadas=pedido.rodadas)
    except LLMIndisponivel as exc:
        raise HTTPException(503, str(exc)) from exc
    eco.salvar(r)
    return r.to_dict()


@app.post("/atender")
def atender(pedido: PedidoFluxo) -> dict[str, Any]:
    eco = obter_eco()
    try:
        r = eco.atender(pedido.briefing, projeto=pedido.projeto or "api")
    except LLMIndisponivel as exc:
        raise HTTPException(503, str(exc)) from exc
    eco.salvar(r)
    return r.to_dict()


@app.post("/jarvis")
def jarvis(pedido: PedidoJarvis) -> dict[str, Any]:
    resposta = obter_jarvis().responder(pedido.mensagem)
    return {"acao": resposta["acao"], "fala": resposta["fala"]}


@app.get("/memoria")
def memoria_status() -> dict[str, Any]:
    eco = obter_eco()
    if eco.semantica is None:
        raise HTTPException(503, "memoria semantica desligada em config/modelos.yaml")
    return {"assinatura": eco.semantica.assinatura, **eco.semantica.estatisticas()}


@app.post("/memoria/buscar")
def memoria_buscar(pedido: PedidoBusca) -> list[dict[str, Any]]:
    eco = obter_eco()
    if eco.semantica is None:
        raise HTTPException(503, "memoria semantica desligada em config/modelos.yaml")
    achados = eco.semantica.buscar(
        pedido.consulta, limite=pedido.limite, minimo=pedido.minimo,
        agente=pedido.agente, projeto=pedido.projeto,
    )
    return [
        {
            "trecho": a.trecho,
            "similaridade": round(a.similaridade, 4),
            "projeto": a.projeto,
            "agente": a.agente,
            "titulo": a.titulo,
            "criado_em": a.criado_em,
        }
        for a in achados
    ]
