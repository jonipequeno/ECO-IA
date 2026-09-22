"""Provedor Ollama (endpoint nativo /api/chat)."""

from __future__ import annotations

from typing import Any, Iterable

from .base import LLMError, LLMIndisponivel, Mensagem, ProvedorLLM, Resposta, limpar_raciocinio


class OllamaProvider(ProvedorLLM):
    """Cliente do Ollama. Padrao: http://localhost:11434 com qwen3:8b."""

    nome = "ollama"
    # False manda "think": false - o modelo responde direto, sem gerar o
    # raciocinio que limpar_raciocinio() jogaria fora. Ver ConfigBackend.
    raciocinio = False

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
            "think": bool(self.raciocinio),
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

    def embeddings(self, textos: list[str], *, modelo: str | None = None) -> list[list[float]]:
        """Vetoriza via /api/embed (endpoint em lote do Ollama).

        Cai para /api/embeddings, um texto por vez, em versoes antigas que
        ainda nao tem o endpoint em lote.
        """
        if not textos:
            return []
        alvo = modelo or "nomic-embed-text"
        try:
            dados = self._post("/api/embed", {"model": alvo, "input": textos})
        except LLMError as exc:
            if "404" not in str(exc):
                raise
            return [self._embedding_unico(t, alvo) for t in textos]

        vetores = dados.get("embeddings")
        if not isinstance(vetores, list) or len(vetores) != len(textos):
            raise LLMError(f"[ollama] /api/embed devolveu {type(vetores)} inesperado para {alvo}")
        return [[float(x) for x in v] for v in vetores]

    def _embedding_unico(self, texto: str, modelo: str) -> list[float]:
        dados = self._post("/api/embeddings", {"model": modelo, "prompt": texto})
        vetor = dados.get("embedding")
        if not isinstance(vetor, list):
            raise LLMError(f"[ollama] /api/embeddings sem campo 'embedding' para {modelo}")
        return [float(x) for x in vetor]

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
