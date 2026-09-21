"""Agenda: executa as rotinas da empresa na hora marcada."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable, Iterable

from .. import fluxos as processos
from ..core.orquestrador import Ecossistema, ResultadoFluxo
from ..llm.base import LLMIndisponivel
from .catalogo import catalogo
from .modelo import Rotina

ESCOPO = "rotinas"

# Se a agenda ficou parada e a hora de uma rotina passou, ela ainda roda se o
# atraso couber nesta janela. Passou disso, e melhor pular do que despejar uma
# semana de dailies atrasadas de uma vez quando a maquina liga.
JANELA_ATRASO = timedelta(hours=6)


@dataclass
class Execucao:
    """O que aconteceu numa disparada de rotina."""

    rotina: str
    inicio: datetime
    fim: datetime | None = None
    estado: str = "executando"        # executando | concluida | erro | pulada
    projeto: str = ""
    erro: str = ""
    detalhe: str = ""

    @property
    def duracao_s(self) -> float:
        return (self.fim - self.inicio).total_seconds() if self.fim else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "rotina": self.rotina,
            "inicio": self.inicio.isoformat(timespec="seconds"),
            "fim": self.fim.isoformat(timespec="seconds") if self.fim else "",
            "estado": self.estado,
            "projeto": self.projeto,
            "erro": self.erro,
            "detalhe": self.detalhe,
            "duracao_s": round(self.duracao_s, 1),
        }


class Agenda:
    """O relogio da empresa.

    Mantem quando cada rotina rodou pela ultima vez (no SQLite da memoria
    corporativa, para sobreviver ao restart) e dispara as que venceram.
    """

    def __init__(
        self,
        eco: Ecossistema,
        rotinas: Iterable[Rotina] | None = None,
        *,
        janela_atraso: timedelta = JANELA_ATRASO,
        relogio: Callable[[], datetime] | None = None,
    ) -> None:
        self.eco = eco
        self.rotinas = {r.id: r for r in (rotinas if rotinas is not None else catalogo())}
        self.janela_atraso = janela_atraso
        self.agora = relogio or datetime.now      # injetavel para teste
        self.historico: list[Execucao] = []
        self._parar = threading.Event()
        self._memoria_local: dict[str, str] = {}  # usado quando nao ha SQLite

    # ------------------------------------------------------------------
    # Estado persistido
    # ------------------------------------------------------------------
    def _chave(self, ident: str) -> str:
        return f"rotina:{ident}:ultima_execucao"

    def ultima_execucao(self, ident: str) -> datetime | None:
        bruto = (
            self.eco.memoria.recordar(self._chave(ident))
            if self.eco.memoria is not None
            else self._memoria_local.get(self._chave(ident))
        )
        if not bruto:
            return None
        try:
            return datetime.fromisoformat(str(bruto))
        except ValueError:
            return None

    def _registrar_execucao(self, ident: str, quando: datetime) -> None:
        valor = quando.isoformat(timespec="seconds")
        if self.eco.memoria is not None:
            self.eco.memoria.lembrar(self._chave(ident), valor, autor="agenda", escopo=ESCOPO)
        else:
            self._memoria_local[self._chave(ident)] = valor

    # ------------------------------------------------------------------
    # Quando roda o que
    # ------------------------------------------------------------------
    def proximo_de(self, rotina: Rotina, depois: datetime | None = None) -> datetime | None:
        """Proxima hora marcada da rotina, contada a partir da ultima execucao."""
        base = depois or self.ultima_execucao(rotina.id) or self.agora()
        return rotina.agendamento.proximo_disparo(base)

    def proximas(self, quantidade: int = 10) -> list[tuple[Rotina, datetime]]:
        """Agenda futura, em ordem cronologica."""
        agora = self.agora()
        itens: list[tuple[Rotina, datetime]] = []
        for rotina in self.rotinas.values():
            if not rotina.ativa:
                continue
            quando = rotina.agendamento.proximo_disparo(agora)
            if quando is not None:
                itens.append((rotina, quando))
        itens.sort(key=lambda par: par[1])
        return itens[:quantidade]

    def devidas(self, agora: datetime | None = None) -> list[Rotina]:
        """Rotinas cuja hora ja passou e que ainda nao rodaram nela.

        Se a agenda ficou parada, adianta os horarios vencidos de uma vez ate
        chegar ao ultimo - nao um por passada. Com checagem a cada 30s, uma
        maquina desligada por um mes levaria 15 minutos para se acertar.
        """
        agora = agora or self.agora()
        vencidas: list[Rotina] = []
        for rotina in self.rotinas.values():
            if not rotina.ativa:
                continue
            marcada = self._horario_pendente(rotina, agora)
            if marcada is not None:
                vencidas.append(rotina)
        return vencidas

    def _horario_pendente(self, rotina: Rotina, agora: datetime) -> datetime | None:
        """Ultimo horario vencido que ainda vale a pena rodar, ou None.

        Os horarios vencidos fora da janela sao marcados como pulados aqui
        mesmo, para nao virarem uma fila de disparos velhos.
        """
        ultima = self.ultima_execucao(rotina.id)
        if ultima is None:
            # Agenda nova: so pega o que acabou de vencer. Senao, a primeira
            # execucao dispararia o calendario inteiro de imediato.
            base = agora - self.janela_atraso
        else:
            base = ultima

        pendente: datetime | None = None
        # O teto evita laco longo se alguem configurar uma rotina de minuto em
        # minuto e a agenda ficar meses parada.
        for _ in range(500):
            marcada = rotina.agendamento.proximo_disparo(base)
            if marcada is None or marcada > agora:
                break
            if agora - marcada <= self.janela_atraso:
                pendente = marcada
                break
            # Vencida demais: registra o pulo e continua adiantando.
            self._registrar_execucao(rotina.id, marcada)
            self.historico.append(
                Execucao(rotina.id, marcada, marcada, "pulada",
                         detalhe=f"atraso de {agora - marcada} acima da janela")
            )
            base = marcada
        return pendente

    # ------------------------------------------------------------------
    # Execucao
    # ------------------------------------------------------------------
    def executar(self, rotina: Rotina | str, *, registrar: bool = True) -> Execucao:
        """Roda uma rotina agora, independente do horario."""
        if isinstance(rotina, str):
            rotina = self.rotinas.get(rotina) or _do_catalogo(rotina)
        execucao = Execucao(rotina.id, self.agora())
        self.historico.append(execucao)

        try:
            resultado = self._despachar(rotina)
        except LLMIndisponivel as exc:
            execucao.estado, execucao.erro = "erro", str(exc)
        except Exception as exc:
            execucao.estado = "erro"
            execucao.erro = f"{type(exc).__name__}: {exc}"
        else:
            execucao.estado = "concluida"
            if isinstance(resultado, ResultadoFluxo):
                execucao.projeto = resultado.projeto
                execucao.detalhe = f"{len(resultado.etapas)} entregas"
                self.eco.salvar(resultado)
            elif isinstance(resultado, str):
                execucao.detalhe = resultado[:200]

        execucao.fim = self.agora()
        if registrar and execucao.estado == "concluida":
            self._registrar_execucao(rotina.id, execucao.fim)
        return execucao

    def _despachar(self, rotina: Rotina) -> ResultadoFluxo | str:
        projeto = f"rotina-{rotina.id}-{self.agora():%Y%m%d}"

        if rotina.tipo == "fluxo":
            return self.eco.executar_fluxo(
                processos.obter(rotina.alvo), rotina.briefing or rotina.descricao,
                projeto=projeto,
            )
        if rotina.tipo == "reuniao":
            presentes = [i for i in rotina.participantes if i in self.eco] or None
            return self.eco.reuniao(
                rotina.alvo, participantes=presentes,
                rodadas=rotina.rodadas, projeto=projeto,
            )
        if rotina.tipo == "agente":
            if rotina.agente not in self.eco:
                raise KeyError(f"rotina '{rotina.id}': agente '{rotina.agente}' nao esta ativo")
            return self.eco.delegar(
                rotina.agente, rotina.alvo, projeto=projeto, remetente="agenda"
            ).entrega
        if rotina.tipo == "manutencao":
            return self._manutencao(rotina)
        raise ValueError(f"tipo de rotina desconhecido: {rotina.tipo}")

    def _manutencao(self, rotina: Rotina) -> str:
        """Tarefas de casa que nao gastam modelo de linguagem."""
        if rotina.alvo == "memoria":
            if self.eco.semantica is None:
                return "memoria semantica desligada: nada a fazer"
            s = self.eco.semantica.estatisticas()
            aviso = ""
            if s["inativos"]:
                aviso = (
                    f" ATENCAO: {s['inativos']} trecho(s) de outro modelo de embedding "
                    "estao invisiveis para a busca; reindexe-os."
                )
            return (
                f"{s['trechos']} trechos em {len(s['projetos'])} projetos, "
                f"procedencia {self.eco.semantica.assinatura}.{aviso}"
            )
        raise ValueError(f"manutencao desconhecida: {rotina.alvo}")

    # ------------------------------------------------------------------
    # Laco
    # ------------------------------------------------------------------
    def rodar(self, intervalo: float = 30.0, ao_executar: Callable[[Execucao], None] | None = None) -> None:
        """Fica de pe checando a agenda. Encerra com parar() ou Ctrl+C."""
        self._parar.clear()
        while not self._parar.is_set():
            for rotina in self.devidas():
                if self._parar.is_set():
                    break
                execucao = self.executar(rotina)
                if ao_executar is not None:
                    ao_executar(execucao)
            # Espera interrompivel: parar() acorda na hora, sem esperar o ciclo.
            self._parar.wait(intervalo)

    def parar(self) -> None:
        self._parar.set()

    @property
    def rodando(self) -> bool:
        return not self._parar.is_set()


def _do_catalogo(ident: str) -> Rotina:
    from .catalogo import obter

    return obter(ident)
