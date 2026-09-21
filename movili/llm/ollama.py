"""Provedor Ollama (endpoint nativo /api/chat)."""

from __future__ import annotations

from typing import Any, Iterable

from .base import LLMError, LLMIndisponivel, Mensagem, ProvedorLLM, Resposta, limpar_raciocinio


class OllamaProvider(ProvedorLLM):
    """Cliente do Ollama. Padrao: http://localhost:11434 com qwen3:8b."""

    nome = "ollama"

    def chat(
        self,
        mensagens: Iterable[Mensagem | dict[str, str]],
        *,
        modelo: str | None = None,
        temperatura: float = 0.7,
        max_tokens: int = 2048,
        formato_json: bool = False,
    ) -> Resposta:
        payload: dict[str, Any] = {
            "model": modelo or self.modelo,
            "messages": self._normalizar(mensagens),
            "stream": False,
            "options": {
                "temperature": temperatura,
                "num_predict": max_tokens,
            },
        }
        if formato_json:
            payload["format"] = "json"

        dados = self._post("/api/chat", payload)
        try:
            conteudo = dados["message"]["content"]
        except (KeyError, TypeError) as exc:
            raise LLMError(f"[ollama] resposta sem campo message.content: {dados}") from exc

        return Resposta(
            conteudo=limpar_raciocinio(conteudo),
            modelo=dados.get("model", payload["model"]),
            provedor=self.nome,
            tokens_entrada=int(dados.get("prompt_eval_count") or 0),
            tokens_saida=int(dados.get("eval_count") or 0),
            bruto=dados,
        )

    def disponivel(self) -> bool:
        try:
            self._get("/api/tags")
            return True
        except LLMIndisponivel:
            return False

    def modelos(self) -> list[str]:
        dados = self._get("/api/tags")
        return sorted(m.get("name", "") for m in dados.get("models", []))

    def tem_modelo(self, modelo: str) -> bool:
        """True se o modelo (com ou sem tag) ja foi baixado no Ollama."""
        alvo = modelo if ":" in modelo else f"{modelo}:latest"
        disponiveis = self.modelos()
        return alvo in disponiveis or any(m.split(":")[0] == modelo.split(":")[0] for m in disponiveis)
