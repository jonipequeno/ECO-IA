"""Provedor LM Studio (servidor local compativel com a API OpenAI)."""

from __future__ import annotations

from typing import Any, Iterable

from .base import LLMError, LLMIndisponivel, Mensagem, ProvedorLLM, Resposta, limpar_raciocinio


class LMStudioProvider(ProvedorLLM):
    """Cliente do LM Studio. Padrao: http://localhost:1234/v1.

    Serve tambem para qualquer servidor compativel com /v1/chat/completions
    (vLLM, llama.cpp server, text-generation-webui em modo OpenAI).
    """

    nome = "lmstudio"

    def __init__(self, base_url: str, modelo: str, timeout: int = 300, api_key: str = "lm-studio") -> None:
        super().__init__(base_url, modelo, timeout)
        self.api_key = api_key

    def _post(self, caminho: str, payload: dict[str, Any]) -> dict[str, Any]:
        # LM Studio ignora a chave, mas alguns proxies compativeis exigem o header.
        import json
        import urllib.error
        import urllib.request

        url = f"{self.base_url}{caminho}"
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            corpo = exc.read().decode("utf-8", errors="replace")[:500]
            raise LLMError(f"[lmstudio] HTTP {exc.code} em {url}: {corpo}") from exc
        except urllib.error.URLError as exc:
            raise LLMIndisponivel(f"[lmstudio] backend inacessivel em {url}: {exc.reason}") from exc
        except TimeoutError as exc:
            raise LLMIndisponivel(f"[lmstudio] timeout de {self.timeout}s em {url}") from exc

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
            "temperature": temperatura,
            "max_tokens": max_tokens,
            "stream": False,
        }
        if formato_json:
            payload["response_format"] = {"type": "json_object"}

        dados = self._post("/chat/completions", payload)
        try:
            conteudo = dados["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError(f"[lmstudio] resposta sem choices[0].message.content: {dados}") from exc

        uso = dados.get("usage") or {}
        return Resposta(
            conteudo=limpar_raciocinio(conteudo or ""),
            modelo=dados.get("model", payload["model"]),
            provedor=self.nome,
            tokens_entrada=int(uso.get("prompt_tokens") or 0),
            tokens_saida=int(uso.get("completion_tokens") or 0),
            bruto=dados,
        )

    def disponivel(self) -> bool:
        try:
            self._get("/models")
            return True
        except LLMIndisponivel:
            return False

    def modelos(self) -> list[str]:
        dados = self._get("/models")
        return sorted(m.get("id", "") for m in dados.get("data", []))
