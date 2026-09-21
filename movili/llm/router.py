"""Roteador de LLM: escolhe o backend por agente, com fallback automatico."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Iterable

from .base import LLMError, LLMIndisponivel, Mensagem, ProvedorLLM, Resposta
from .lmstudio import LMStudioProvider
from .ollama import OllamaProvider

PROVEDORES = {
    "ollama": OllamaProvider,
    "lmstudio": LMStudioProvider,
}


class ProvedorSimulado(ProvedorLLM):
    """Backend de teste: nao chama modelo nenhum.

    Existe para validar o encanamento do ecossistema (barramento, fluxos,
    handoffs) sem GPU. O texto devolvido e um marcador explicito - nunca
    deve ser confundido com saida real de um modelo.
    """

    nome = "simulado"

    def __init__(self, base_url: str = "", modelo: str = "simulado", timeout: int = 1) -> None:
        super().__init__(base_url or "http://simulado", modelo, timeout)
        self.chamadas: list[list[dict[str, str]]] = []

    def chat(
        self,
        mensagens: Iterable[Mensagem | dict[str, str]],
        *,
        modelo: str | None = None,
        temperatura: float = 0.7,
        max_tokens: int = 2048,
        formato_json: bool = False,
    ) -> Resposta:
        normalizadas = self._normalizar(mensagens)
        self.chamadas.append(normalizadas)
        ultima = normalizadas[-1]["content"] if normalizadas else ""
        cargo = "agente"
        for m in normalizadas:
            if m["role"] == "system":
                primeira_linha = m["content"].strip().splitlines()[0]
                cargo = primeira_linha[:120]
                break
        corpo = (
            "[RESPOSTA SIMULADA - nenhum modelo foi executado]\n"
            f"Persona: {cargo}\n"
            f"Demanda recebida ({len(ultima)} caracteres): {ultima[:280]}"
        )
        if formato_json:
            corpo = '{"simulado": true, "resumo": "execucao sem modelo real"}'
        return Resposta(
            conteudo=corpo,
            modelo="simulado",
            provedor=self.nome,
            tokens_entrada=sum(len(m["content"]) // 4 for m in normalizadas),
            tokens_saida=len(corpo) // 4,
        )

    def disponivel(self) -> bool:
        return True

    def modelos(self) -> list[str]:
        return ["simulado"]


@dataclass
class ConfigBackend:
    """Configuracao de um backend declarada em config/modelos.yaml."""

    tipo: str
    base_url: str
    modelo_padrao: str
    timeout: int = 300
    habilitado: bool = True

    def construir(self) -> ProvedorLLM:
        if self.tipo == "simulado":
            return ProvedorSimulado(modelo=self.modelo_padrao)
        classe = PROVEDORES.get(self.tipo)
        if classe is None:
            raise ValueError(
                f"backend '{self.tipo}' desconhecido; use um de: {', '.join(sorted(PROVEDORES))}"
            )
        return classe(self.base_url, self.modelo_padrao, self.timeout)


class RoteadorLLM:
    """Mantem os backends vivos e decide qual atende cada agente.

    Regras:
      1. usa o backend preferido do agente (config/modelos.yaml);
      2. se ele estiver fora do ar, cai para o proximo da ordem de fallback;
      3. registra metricas de uso por agente para o painel financeiro.
    """

    def __init__(
        self,
        backends: dict[str, ConfigBackend],
        ordem_fallback: list[str] | None = None,
        tentativas: int = 2,
    ) -> None:
        self.configs = {n: c for n, c in backends.items() if c.habilitado}
        if not self.configs:
            raise ValueError("nenhum backend habilitado em config/modelos.yaml")
        self.ordem_fallback = [n for n in (ordem_fallback or list(self.configs)) if n in self.configs]
        self.tentativas = max(1, tentativas)
        self._instancias: dict[str, ProvedorLLM] = {}
        self.metricas: dict[str, dict[str, int]] = {}

    # --- ciclo de vida ------------------------------------------------
    def provedor(self, nome: str) -> ProvedorLLM:
        if nome not in self._instancias:
            self._instancias[nome] = self.configs[nome].construir()
        return self._instancias[nome]

    def status(self) -> dict[str, dict[str, object]]:
        """Diagnostico de todos os backends configurados."""
        resultado: dict[str, dict[str, object]] = {}
        for nome, cfg in self.configs.items():
            prov = self.provedor(nome)
            online = prov.disponivel()
            info: dict[str, object] = {
                "tipo": cfg.tipo,
                "url": cfg.base_url,
                "modelo_padrao": cfg.modelo_padrao,
                "online": online,
            }
            if online:
                try:
                    info["modelos"] = prov.modelos()
                except LLMError as exc:
                    info["modelos"] = []
                    info["erro"] = str(exc)
            resultado[nome] = info
        return resultado

    # --- execucao -----------------------------------------------------
    def gerar(
        self,
        mensagens: list[Mensagem | dict[str, str]],
        *,
        agente: str = "desconhecido",
        backend: str | None = None,
        modelo: str | None = None,
        temperatura: float = 0.7,
        max_tokens: int = 2048,
        formato_json: bool = False,
    ) -> Resposta:
        candidatos = self._candidatos(backend)
        erros: list[str] = []

        for nome in candidatos:
            prov = self.provedor(nome)
            modelo_alvo = modelo if (backend in (None, nome) or modelo) else None
            for tentativa in range(self.tentativas):
                try:
                    resposta = prov.chat(
                        mensagens,
                        modelo=modelo_alvo or self.configs[nome].modelo_padrao,
                        temperatura=temperatura,
                        max_tokens=max_tokens,
                        formato_json=formato_json,
                    )
                except LLMIndisponivel as exc:
                    erros.append(str(exc))
                    break  # backend fora do ar: nao adianta repetir, troca de backend
                except LLMError as exc:
                    erros.append(str(exc))
                    if tentativa + 1 < self.tentativas:
                        time.sleep(1.5 * (tentativa + 1))
                        continue
                    break
                else:
                    self._registrar(agente, resposta)
                    return resposta

        raise LLMIndisponivel(
            "nenhum backend respondeu. Verifique se o Ollama (ollama serve) ou o "
            "LM Studio (Developer > Start Server) estao rodando.\nDetalhes:\n  - "
            + "\n  - ".join(erros or ["sem backends candidatos"])
        )

    def _candidatos(self, backend: str | None) -> list[str]:
        if backend and backend in self.configs:
            return [backend] + [n for n in self.ordem_fallback if n != backend]
        return list(self.ordem_fallback)

    def _registrar(self, agente: str, resposta: Resposta) -> None:
        m = self.metricas.setdefault(
            agente, {"chamadas": 0, "tokens_entrada": 0, "tokens_saida": 0}
        )
        m["chamadas"] += 1
        m["tokens_entrada"] += resposta.tokens_entrada
        m["tokens_saida"] += resposta.tokens_saida
