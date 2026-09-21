"""Rotinas: o calendario interno da Movili - o que a empresa faz sozinha."""

from .agenda import Agenda, Execucao
from .catalogo import REGISTRO, catalogo, obter
from .modelo import Agendamento, Rotina

__all__ = ["Agenda", "Execucao", "Agendamento", "Rotina", "REGISTRO", "catalogo", "obter"]
