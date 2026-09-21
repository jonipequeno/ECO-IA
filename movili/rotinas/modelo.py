"""Agendamento e definicao de uma rotina da empresa."""

from __future__ import annotations

import calendar
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Literal

DIAS = ["segunda", "terca", "quarta", "quinta", "sexta", "sabado", "domingo"]
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]

TipoAcao = Literal["fluxo", "reuniao", "agente", "manutencao"]


@dataclass(frozen=True)
class Agendamento:
    """Quando uma rotina dispara.

    Os conjuntos vazios significam "qualquer": `dias_da_semana` vazio e
    `dias_do_mes` vazio quer dizer todo dia. Quando os dois sao preenchidos,
    a data precisa satisfazer os DOIS (ex.: primeira segunda-feira do mes).
    """

    hora: int = 9
    minuto: int = 0
    dias_da_semana: frozenset[int] = frozenset()   # 0 = segunda ... 6 = domingo
    dias_do_mes: frozenset[int] = frozenset()      # 1..31; 31 cai no ultimo dia do mes
    meses: frozenset[int] = frozenset()            # 1..12

    def __post_init__(self) -> None:
        if not 0 <= self.hora <= 23:
            raise ValueError(f"hora fora de 0..23: {self.hora}")
        if not 0 <= self.minuto <= 59:
            raise ValueError(f"minuto fora de 0..59: {self.minuto}")
        if any(d < 0 or d > 6 for d in self.dias_da_semana):
            raise ValueError("dia da semana fora de 0..6 (0 = segunda)")
        if any(d < 1 or d > 31 for d in self.dias_do_mes):
            raise ValueError("dia do mes fora de 1..31")
        if any(m < 1 or m > 12 for m in self.meses):
            raise ValueError("mes fora de 1..12")

    # ------------------------------------------------------------------
    def _dia_do_mes_casa(self, quando: datetime) -> bool:
        if not self.dias_do_mes:
            return True
        if quando.day in self.dias_do_mes:
            return True
        # Dia 31 (ou 30, 29) em mes curto cai no ultimo dia, senao a rotina
        # simplesmente nunca rodaria em fevereiro.
        ultimo = calendar.monthrange(quando.year, quando.month)[1]
        return quando.day == ultimo and any(d > ultimo for d in self.dias_do_mes)

    def casa(self, quando: datetime) -> bool:
        """A data/hora exata satisfaz o agendamento (ignorando segundos)?"""
        if self.meses and quando.month not in self.meses:
            return False
        if self.dias_da_semana and quando.weekday() not in self.dias_da_semana:
            return False
        if not self._dia_do_mes_casa(quando):
            return False
        return quando.hour == self.hora and quando.minute == self.minuto

    def proximo_disparo(self, depois: datetime, limite_dias: int = 400) -> datetime | None:
        """Primeiro instante valido estritamente depois de `depois`.

        Devolve None se nada casar dentro de `limite_dias` - protege contra
        agendamento impossivel (ex.: 30 de fevereiro) em vez de girar para sempre.
        """
        candidato = depois.replace(second=0, microsecond=0) + timedelta(minutes=1)
        alvo = candidato.replace(hour=self.hora, minute=self.minuto)
        if alvo < candidato:
            alvo += timedelta(days=1)

        fim = depois + timedelta(days=limite_dias)
        while alvo <= fim:
            if self.casa(alvo):
                return alvo
            alvo += timedelta(days=1)
        return None

    def descrever(self) -> str:
        horario = f"{self.hora:02d}:{self.minuto:02d}"
        partes: list[str] = []
        if self.dias_da_semana:
            nomes = [DIAS[d] for d in sorted(self.dias_da_semana)]
            if set(self.dias_da_semana) == {0, 1, 2, 3, 4}:
                partes.append("de segunda a sexta")
            elif len(nomes) == 1:
                partes.append(f"toda {nomes[0]}")
            else:
                partes.append(f"{', '.join(nomes[:-1])} e {nomes[-1]}")
        if self.dias_do_mes:
            dias = ", ".join(f"dia {d}" for d in sorted(self.dias_do_mes))
            partes.append(dias)
        if self.meses:
            partes.append("em " + ", ".join(MESES[m - 1] for m in sorted(self.meses)))
        if not partes:
            partes.append("todo dia")
        return f"{' '.join(partes)} as {horario}"


@dataclass
class Rotina:
    """Um compromisso fixo da empresa: o que roda, quando e com quem."""

    id: str
    nome: str
    descricao: str
    agendamento: Agendamento
    tipo: TipoAcao
    # conforme o tipo: nome do fluxo, tema da reuniao, ou instrucao ao agente
    alvo: str = ""
    participantes: list[str] = field(default_factory=list)
    agente: str = ""
    rodadas: int = 1
    briefing: str = ""
    ativa: bool = True

    def __post_init__(self) -> None:
        if self.tipo == "fluxo" and not self.alvo:
            raise ValueError(f"rotina '{self.id}': tipo 'fluxo' exige o nome do fluxo em alvo")
        if self.tipo == "agente" and not self.agente:
            raise ValueError(f"rotina '{self.id}': tipo 'agente' exige o id do funcionario")
        if self.tipo == "reuniao" and not self.alvo:
            raise ValueError(f"rotina '{self.id}': tipo 'reuniao' exige o tema em alvo")

    def resumo(self) -> str:
        return f"{self.nome} — {self.agendamento.descrever()}"
