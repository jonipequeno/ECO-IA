"""OpenJarvis - camada conversacional (voz e ponte OpenAI) do ecossistema Movili."""

from .conversa import Jarvis
from .despertar import PALAVRA_PADRAO, contem_palavra, detectar_despertar, remover_palavra
from .ponte import servir
from .sessao import SessaoJarvis
from .voz import detectar_escuta, detectar_fala, diagnostico

__all__ = [
    "Jarvis",
    "SessaoJarvis",
    "servir",
    "detectar_escuta",
    "detectar_fala",
    "detectar_despertar",
    "contem_palavra",
    "remover_palavra",
    "diagnostico",
    "PALAVRA_PADRAO",
]
