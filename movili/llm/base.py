"""Contratos base para provedores de LLM locais (Ollama / LM Studio)."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Iterable


class LLMError(RuntimeError):
    """Falha de comunicacao ou de resposta de um provedor de LLM."""


class LLMIndisponivel(LLMError):
    """O backend nao esta no ar ou nao respondeu no tempo esperado."""


@dataclass
class Mensagem:
    """Mensagem no formato chat (role/content) aceito pelos dois backends."""

    role: str
    content: str

    def to_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass
class Resposta:
    """Resposta normalizada de qualquer provedor."""

    conteudo: str
    modelo: str
    provedor: str
    tokens_entrada: int = 0
    tokens_saida: int = 0
    bruto: dict[str, Any] = field(default_factory=dict)

    @property
    def tokens_total(self) -> int:
        return self.tokens_entrada + self.tokens_saida


class ProvedorLLM:
    """Interface comum. Implementacoes: OllamaProvider e LMStudioProvider."""

    nome = "base"

    def __init__(self, base_url: str, modelo: str, timeout: int = 300) -> None:
        self.base_url = base_url.rstrip("/")
        self.modelo = modelo
        self.timeout = timeout

    # --- API publica -------------------------------------------------
    def chat(
        self,
        mensagens: Iterable[Mensagem | dict[str, str]],
        *,
        modelo: str | None = None,
        temperatura: float = 0.7,
        max_tokens: int = 2048,
        formato_json: bool = False,
    ) -> Resposta:
        raise NotImplementedError

    def disponivel(self) -> bool:
        raise NotImplementedError

    def modelos(self) -> list[str]:
        raise NotImplementedError

    # --- utilitarios compartilhados ----------------------------------
    @staticmethod
    def _normalizar(mensagens: Iterable[Mensagem | dict[str, str]]) -> list[dict[str, str]]:
        saida: list[dict[str, str]] = []
        for m in mensagens:
            if isinstance(m, Mensagem):
                saida.append(m.to_dict())
            elif isinstance(m, dict):
                saida.append({"role": m["role"], "content": m["content"]})
            else:  # pragma: no cover - uso incorreto da API
                raise TypeError(f"mensagem invalida: {type(m)!r}")
        return saida

    def _post(self, caminho: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}{caminho}"
        dados = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=dados,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:  # resposta com status de erro
            corpo = exc.read().decode("utf-8", errors="replace")[:500]
            raise LLMError(f"[{self.nome}] HTTP {exc.code} em {url}: {corpo}") from exc
        except urllib.error.URLError as exc:
            raise LLMIndisponivel(f"[{self.nome}] backend inacessivel em {url}: {exc.reason}") from exc
        except TimeoutError as exc:
            raise LLMIndisponivel(f"[{self.nome}] timeout de {self.timeout}s em {url}") from exc
        except json.JSONDecodeError as exc:
            raise LLMError(f"[{self.nome}] resposta nao e JSON valido: {exc}") from exc

    def _get(self, caminho: str) -> dict[str, Any]:
        url = f"{self.base_url}{caminho}"
        req = urllib.request.Request(url, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise LLMIndisponivel(f"[{self.nome}] backend inacessivel em {url}: {exc}") from exc


def limpar_raciocinio(texto: str) -> str:
    """Remove blocos <think>...</think> que o Qwen3 emite em modo reasoning."""

    if "<think>" not in texto:
        return texto.strip()

    saida: list[str] = []
    restante = texto
    while "<think>" in restante:
        antes, _, depois = restante.partition("<think>")
        saida.append(antes)
        _, fechou, restante = depois.partition("</think>")
        if not fechou:  # bloco aberto sem fechar: descarta o resto
            restante = ""
    saida.append(restante)
    return "".join(saida).strip()
