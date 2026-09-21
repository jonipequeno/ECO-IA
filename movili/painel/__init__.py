"""Painel web do ecossistema: acompanhar a Movili trabalhando em tempo real."""

from .servidor import Central, TarefaInvalida, servir

__all__ = ["Central", "TarefaInvalida", "servir"]
