"""Camada de modelos locais: Ollama e LM Studio."""

from .base import LLMError, LLMIndisponivel, Mensagem, ProvedorLLM, Resposta
from .lmstudio import LMStudioProvider
from .ollama import OllamaProvider
from .router import ConfigBackend, ProvedorSimulado, RoteadorLLM

__all__ = [
    "LLMError",
    "LLMIndisponivel",
    "Mensagem",
    "ProvedorLLM",
    "Resposta",
    "OllamaProvider",
    "LMStudioProvider",
    "RoteadorLLM",
    "ConfigBackend",
    "ProvedorSimulado",
]
