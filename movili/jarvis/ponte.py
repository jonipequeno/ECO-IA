"""Ponte OpenAI-compativel: liga o ecossistema a qualquer cliente de voz.

Sobe um servidor HTTP que fala o protocolo /v1/chat/completions. Assim,
qualquer cliente que ja conversa com Ollama, LM Studio ou OpenAI - incluindo
uma instalacao externa do OpenJarvis, um app de voz ou o proprio LM Studio -
pode apontar para ca e conversar com a Movili inteira em vez de com um
modelo solto.

Usa apenas a biblioteca padrao: nao exige FastAPI.
"""

from __future__ import annotations

import json
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .. import agentes as quadro
from ..core.orquestrador import Ecossistema
from .conversa import Jarvis

LIMITE_CORPO = 2 * 1024 * 1024  # 2 MB


def _modelos_expostos() -> list[dict[str, Any]]:
    """Cada agente vira um 'modelo' selecionavel, mais o Jarvis e a empresa toda."""
    agora = int(time.time())
    itens = [
        {"id": "movili-jarvis", "object": "model", "created": agora, "owned_by": "movili",
         "description": "Recepcao conversacional: roteia para quem for necessario."},
        {"id": "movili-empresa", "object": "model", "created": agora, "owned_by": "movili",
         "description": "A diretoria faz a triagem e escala o time todo."},
    ]
    for ident, fabrica in quadro.REGISTRO.items():
        p = fabrica()
        itens.append({
            "id": f"movili-{ident}",
            "object": "model",
            "created": agora,
            "owned_by": "movili",
            "description": f"{p.nome} - {p.cargo}",
        })
    return itens


class _Handler(BaseHTTPRequestHandler):
    eco: Ecossistema
    jarvis: Jarvis
    server_version = "MoviliJarvisBridge/1.0"

    # --- utilitarios --------------------------------------------------
    def log_message(self, formato: str, *args: Any) -> None:  # silencia o log padrao
        return

    def _responder(self, codigo: int, corpo: dict[str, Any]) -> None:
        dados = json.dumps(corpo, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(dados)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(dados)

    def _erro(self, codigo: int, mensagem: str) -> None:
        self._responder(codigo, {"error": {"message": mensagem, "type": "movili_error"}})

    def _corpo(self) -> dict[str, Any] | None:
        try:
            tamanho = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            return None
        if tamanho <= 0 or tamanho > LIMITE_CORPO:
            return None
        try:
            return json.loads(self.rfile.read(tamanho).decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None

    # --- rotas --------------------------------------------------------
    def do_OPTIONS(self) -> None:  # noqa: N802 - assinatura da stdlib
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        if self.path.rstrip("/") in {"/v1/models", "/models"}:
            self._responder(200, {"object": "list", "data": _modelos_expostos()})
        elif self.path.rstrip("/") in {"", "/health", "/v1"}:
            self._responder(200, {
                "servico": "Movili OpenJarvis Bridge",
                "agentes": len(self.eco.agentes),
                "endpoints": ["/v1/models", "/v1/chat/completions"],
            })
        else:
            self._erro(404, f"rota nao encontrada: {self.path}")

    def do_POST(self) -> None:  # noqa: N802
        if self.path.rstrip("/") not in {"/v1/chat/completions", "/chat/completions"}:
            self._erro(404, f"rota nao encontrada: {self.path}")
            return

        corpo = self._corpo()
        if corpo is None:
            self._erro(400, "corpo JSON ausente, invalido ou grande demais")
            return

        mensagens = corpo.get("messages") or []
        if not isinstance(mensagens, list) or not mensagens:
            self._erro(400, "campo 'messages' obrigatorio")
            return

        ultima = ""
        for m in reversed(mensagens):
            if isinstance(m, dict) and m.get("role") == "user":
                ultima = str(m.get("content") or "")
                break
        if not ultima:
            self._erro(400, "nenhuma mensagem de usuario encontrada")
            return

        modelo = str(corpo.get("model") or "movili-jarvis")
        try:
            texto = self._despachar(modelo, ultima)
        except Exception as exc:  # devolve erro no formato OpenAI em vez de 500 cru
            self._erro(502, f"falha ao processar: {exc}")
            return

        self._responder(200, {
            "id": f"chatcmpl-{uuid.uuid4().hex[:16]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": modelo,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": texto},
                "finish_reason": "stop",
            }],
            "usage": {"prompt_tokens": len(ultima) // 4,
                      "completion_tokens": len(texto) // 4,
                      "total_tokens": (len(ultima) + len(texto)) // 4},
        })

    def _despachar(self, modelo: str, texto: str) -> str:
        alvo = modelo.removeprefix("movili-")
        if alvo in self.eco:
            return self.eco.delegar(alvo, texto, projeto="jarvis-bridge", remetente="jarvis").entrega
        if alvo == "empresa":
            resultado = self.eco.atender(texto, projeto="jarvis-bridge")
            return resultado.consolidacao or resultado.markdown()
        return self.jarvis.responder(texto)["fala"]


def servir(eco: Ecossistema, host: str = "127.0.0.1", porta: int = 8123, frases: int = 6) -> None:
    """Sobe a ponte. Encerra com Ctrl+C."""
    _Handler.eco = eco
    _Handler.jarvis = Jarvis(eco, frases=frases)
    servidor = ThreadingHTTPServer((host, porta), _Handler)
    print(
        f"\nPonte OpenJarvis no ar em http://{host}:{porta}/v1\n"
        f"  Agentes expostos como modelos: {len(eco.agentes) + 2}\n"
        f"  Aponte seu cliente de voz (OpenJarvis, LM Studio, qualquer app OpenAI-compativel)\n"
        f"  para essa URL e escolha o 'modelo':\n"
        f"    movili-jarvis   -> recepcao que roteia sozinha\n"
        f"    movili-empresa  -> a diretoria escala o time todo\n"
        f"    movili-<agente> -> fala direto com um funcionario (ex: movili-financeiro)\n"
        f"\nCtrl+C para encerrar.\n"
    )
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nencerrando a ponte...")
    finally:
        servidor.shutdown()
        servidor.server_close()
