"""OpenJarvis - camada conversacional (voz e ponte OpenAI) do ecossistema Movili."""

from .conversa import Jarvis
from .ponte import servir
from .sessao import SessaoJarvis
from .voz import detectar_escuta, detectar_fala, diagnostico

__all__ = [
    "Jarvis",
    "SessaoJarvis",
    "servir",
    "detectar_escuta",
    "detectar_fala",
    "diagnostico",
]
