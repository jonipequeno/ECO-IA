"""Agente base: um funcionario senior da Movili Tecnologia."""

from __future__ import annotations

import re
from collections import deque
from dataclasses import dataclass, field
from typing import Any

from ..llm.router import RoteadorLLM
from .barramento import Barramento
from .ferramentas import CaixaDeFerramentas
from .memoria import MemoriaCorporativa, MemoriaCurta
from .mensagem import Mensagem, Prioridade, Tipo

# Teto da fila de mensagens nao lidas de um agente. Ninguem chama pendentes()
# no fluxo normal, entao sem teto a lista guardaria a sessao inteira.
LIMITE_PENDENTES = 200

BLOCO_HANDOFF = re.compile(
    r"@(?P<destino>[a-z0-9_]+)\s*\{(?P<assunto>[^}]{1,160})\}", re.IGNORECASE
)


@dataclass
class Perfil:
    """Ficha funcional do agente - e o que o torna um 'funcionario'."""

    id: str
    nome: str
    cargo: str
    setor: str
    senioridade: str = "Senior"
    missao: str = ""
    especialidades: list[str] = field(default_factory=list)
    responsabilidades: list[str] = field(default_factory=list)
    kpis: list[str] = field(default_factory=list)
    estilo: str = "objetivo, tecnico e orientado a resultado"
    interlocutores: list[str] = field(default_factory=list)
    ferramentas: list[str] = field(default_factory=list)
    # roteamento de modelo
    backend: str | None = None
    modelo: str | None = None
    temperatura: float = 0.6
    max_tokens: int = 2048
    formato_entrega: str = ""

    def cracha(self) -> str:
        return f"{self.nome} - {self.cargo} ({self.senioridade}) | {self.setor}"


class Agente:
    """Funcionario de IA: tem persona, memoria, ferramentas e fala com colegas."""

    def __init__(
        self,
        perfil: Perfil,
        roteador: RoteadorLLM,
        barramento: Barramento,
        *,
        empresa: dict[str, Any] | None = None,
        ferramentas: CaixaDeFerramentas | None = None,
        memoria: MemoriaCorporativa | None = None,
        max_turnos_ferramenta: int = 3,
        limite_pendentes: int = LIMITE_PENDENTES,
    ) -> None:
        self.perfil = perfil
        self.roteador = roteador
        self.barramento = barramento
        self.empresa = empresa or {}
        self.ferramentas = ferramentas
        self.memoria_longa = memoria
        self.memoria = MemoriaCurta()
        self.max_turnos_ferramenta = max_turnos_ferramenta
        self.barramento.assinar(perfil.id, self._receber)
        self.limite_pendentes = limite_pendentes
        self._pendentes: deque[Mensagem] = deque(maxlen=limite_pendentes)

    # ------------------------------------------------------------------
    # Identidade
    # ------------------------------------------------------------------
    @property
    def id(self) -> str:
        return self.perfil.id

    @property
    def nome(self) -> str:
        return self.perfil.nome

    def __repr__(self) -> str:  # pragma: no cover - conveniencia de debug
        return f"<Agente {self.perfil.id}: {self.perfil.cargo}>"

    def prompt_sistema(self, colegas: dict[str, str] | None = None) -> str:
        p = self.perfil
        emp = self.empresa
        partes: list[str] = []

        partes.append(
            f"Voce e {p.nome}, {p.cargo} ({p.senioridade}) da {emp.get('nome', 'Movili Tecnologia')}, "
            f"atuando no setor de {p.setor}. Voce NAO e um assistente generico: voce e uma pessoa "
            f"da equipe, com opiniao tecnica propria, e responde como tal."
        )

        if emp:
            partes.append(
                "CONTEXTO DA EMPRESA\n"
                f"- Empresa: {emp.get('nome', 'Movili Tecnologia')}\n"
                f"- Segmento: {emp.get('segmento', 'desenvolvimento de software sob medida')}\n"
                f"- Posicionamento: {emp.get('posicionamento', '')}\n"
                f"- Publico-alvo: {emp.get('publico_alvo', '')}\n"
                f"- Stack padrao: {emp.get('stack', '')}\n"
                f"- Tom de voz: {emp.get('tom_de_voz', '')}"
            )

        if p.missao:
            partes.append(f"SUA MISSAO\n{p.missao}")
        if p.especialidades:
            partes.append("SUAS ESPECIALIDADES\n- " + "\n- ".join(p.especialidades))
        if p.responsabilidades:
            partes.append("SUAS RESPONSABILIDADES\n- " + "\n- ".join(p.responsabilidades))
        if p.kpis:
            partes.append("VOCE E COBRADO POR ESTES KPIs\n- " + "\n- ".join(p.kpis))

        if colegas:
            linhas = [f"- @{ident}: {desc}" for ident, desc in colegas.items() if ident != p.id]
            partes.append(
                "SEUS COLEGAS (voce pode e deve acionar quem for necessario)\n"
                + "\n".join(linhas)
                + "\n\nPara acionar um colega, escreva no fim da resposta uma linha no formato:\n"
                "@id_do_colega {o que voce precisa dele, em uma frase}\n"
                "Use no maximo 2 acionamentos por resposta e so quando a entrega depender disso."
            )

        if self.ferramentas and p.ferramentas:
            manual = self.ferramentas.manual(p.ferramentas)
            if manual:
                partes.append(manual)

        partes.append(
            "COMO VOCE TRABALHA\n"
            f"- Estilo: {p.estilo}.\n"
            "- Responda SEMPRE em portugues do Brasil.\n"
            "- Va direto ao ponto: sem saudacao longa, sem repetir a pergunta.\n"
            "- Entregue trabalho pronto para uso, nao sugestoes vagas.\n"
            "- Assuma premissas explicitas quando faltar informacao, e diga quais sao.\n"
            "- Discorde de colegas quando tiver base tecnica para isso."
        )

        if p.formato_entrega:
            partes.append(f"FORMATO DA SUA ENTREGA\n{p.formato_entrega}")

        return "\n\n".join(x for x in partes if x.strip())

    # ------------------------------------------------------------------
    # Comunicacao
    # ------------------------------------------------------------------
    def _receber(self, mensagem: Mensagem) -> None:
        """Callback do barramento: apenas enfileira, nao processa."""
        if mensagem.remetente != self.id:
            self._pendentes.append(mensagem)
            if self.memoria_longa is not None:
                self.memoria_longa.salvar_mensagem(mensagem.to_dict())

    def pendentes(self, limpar: bool = True) -> list[Mensagem]:
        itens = list(self._pendentes)
        if limpar:
            self._pendentes.clear()
        return itens

    def enviar(
        self,
        destinatario: str,
        assunto: str,
        conteudo: str,
        *,
        tipo: Tipo = Tipo.TAREFA,
        prioridade: Prioridade = Prioridade.NORMAL,
        thread: str = "",
        projeto: str = "",
        anexos: dict[str, Any] | None = None,
    ) -> Mensagem:
        return self.barramento.enviar(
            self.id,
            destinatario,
            assunto,
            conteudo,
            tipo=tipo,
            prioridade=prioridade,
            thread=thread,
            projeto=projeto,
            anexos=anexos,
        )

    # ------------------------------------------------------------------
    # Raciocinio
    # ------------------------------------------------------------------
    def responder(
        self,
        instrucao: str,
        *,
        contexto: str = "",
        colegas: dict[str, str] | None = None,
        temperatura: float | None = None,
        max_tokens: int | None = None,
        usar_memoria: bool = True,
        registrar: bool = True,
    ) -> str:
        """Executa um turno de trabalho do agente e devolve a entrega."""
        sistema = self.prompt_sistema(colegas)
        mensagens: list[dict[str, str]] = [{"role": "system", "content": sistema}]
        if usar_memoria:
            mensagens.extend(self.memoria.como_mensagens())

        pedido = instrucao if not contexto else f"CONTEXTO\n{contexto}\n\nSUA TAREFA\n{instrucao}"
        mensagens.append({"role": "user", "content": pedido})

        resposta = self.roteador.gerar(
            mensagens,
            agente=self.id,
            backend=self.perfil.backend,
            modelo=self.perfil.modelo,
            temperatura=self.perfil.temperatura if temperatura is None else temperatura,
            max_tokens=self.perfil.max_tokens if max_tokens is None else max_tokens,
        )
        texto = resposta.conteudo
        texto = self._resolver_ferramentas(mensagens, texto)

        if registrar:
            self.memoria.registrar("user", pedido)
            self.memoria.registrar("assistant", texto)
        return texto

    def _resolver_ferramentas(self, mensagens: list[dict[str, str]], texto: str) -> str:
        """Loop de ferramentas: executa chamadas ate o agente concluir."""
        if not self.ferramentas or not self.perfil.ferramentas:
            return texto

        for _ in range(self.max_turnos_ferramenta):
            chamada = self.ferramentas.extrair_chamada(texto)
            if chamada is None:
                return texto
            resultado = self.ferramentas.executar(chamada["ferramenta"], chamada["args"])
            mensagens.append({"role": "assistant", "content": texto})
            mensagens.append(
                {
                    "role": "user",
                    "content": (
                        f"RESULTADO DA FERRAMENTA {chamada['ferramenta']}:\n{resultado}\n\n"
                        "Use o resultado e conclua sua entrega. Nao chame a mesma ferramenta de novo "
                        "sem necessidade."
                    ),
                }
            )
            texto = self.roteador.gerar(
                mensagens,
                agente=self.id,
                backend=self.perfil.backend,
                modelo=self.perfil.modelo,
                temperatura=self.perfil.temperatura,
                max_tokens=self.perfil.max_tokens,
            ).conteudo
        return texto

    # ------------------------------------------------------------------
    # Trabalho sobre uma mensagem recebida
    # ------------------------------------------------------------------
    def processar(
        self,
        mensagem: Mensagem,
        *,
        colegas: dict[str, str] | None = None,
        publicar: bool = True,
    ) -> Mensagem:
        """Le uma mensagem, produz a entrega e devolve (publicando no barramento)."""
        contexto = (
            f"Mensagem de {mensagem.remetente} ({mensagem.tipo.value}, "
            f"prioridade {mensagem.prioridade.value})\n"
            f"Projeto: {mensagem.projeto or 'n/d'}\n"
            f"Assunto: {mensagem.assunto}"
        )
        texto = self.responder(mensagem.conteudo, contexto=contexto, colegas=colegas)
        entrega = mensagem.responder(self.id, texto, tipo=Tipo.ENTREGA)
        entrega.projeto = mensagem.projeto

        if self.memoria_longa is not None and mensagem.projeto:
            self.memoria_longa.salvar_entregavel(
                mensagem.projeto, self.id, mensagem.assunto, texto
            )
        if publicar:
            self.barramento.publicar(entrega)
        return entrega

    def handoffs(self, texto: str) -> list[tuple[str, str]]:
        """Extrai acionamentos '@colega {pedido}' emitidos na resposta."""
        return [(m.group("destino").lower(), m.group("assunto").strip()) for m in BLOCO_HANDOFF.finditer(texto)]
