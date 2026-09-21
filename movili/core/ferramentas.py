"""Ferramentas que os agentes podem acionar durante o trabalho.

O contrato e simples e independente de 'function calling' nativo: o agente
emite um bloco JSON e o executor resolve. Funciona igual no Ollama e no
LM Studio, com qualquer modelo aberto.
"""

from __future__ import annotations

import ast
import json
import operator
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

BLOCO_FERRAMENTA = re.compile(
    r"```(?:ferramenta|tool|json)?\s*(\{.*?\})\s*```", re.DOTALL | re.IGNORECASE
)

_OPERADORES = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def calcular(expressao: str) -> float:
    """Avalia uma expressao aritmetica sem usar eval().

    Usado pelo agente financeiro para orcamento, margem, payback e ROI.
    """

    def _aval(no: ast.AST) -> float:
        if isinstance(no, ast.Expression):
            return _aval(no.body)
        if isinstance(no, ast.Constant):
            if isinstance(no.value, (int, float)):
                return float(no.value)
            raise ValueError(f"constante nao numerica: {no.value!r}")
        if isinstance(no, ast.BinOp) and type(no.op) in _OPERADORES:
            return _OPERADORES[type(no.op)](_aval(no.left), _aval(no.right))
        if isinstance(no, ast.UnaryOp) and type(no.op) in _OPERADORES:
            return _OPERADORES[type(no.op)](_aval(no.operand))
        raise ValueError(f"expressao nao permitida: {ast.dump(no)[:80]}")

    arvore = ast.parse(expressao.replace(",", "."), mode="eval")
    return _aval(arvore)


@dataclass
class Ferramenta:
    nome: str
    descricao: str
    parametros: str
    executar: Callable[..., Any]

    def assinatura(self) -> str:
        return f"- {self.nome}({self.parametros}): {self.descricao}"


class CaixaDeFerramentas:
    """Registro de ferramentas disponiveis para um agente."""

    def __init__(self, workspace: str | Path = "workspace") -> None:
        self.workspace = Path(workspace)
        self.workspace.mkdir(parents=True, exist_ok=True)
        self._registro: dict[str, Ferramenta] = {}
        self._registrar_padrao()

    def _registrar_padrao(self) -> None:
        self.registrar(
            Ferramenta(
                "calcular",
                "Resolve uma conta aritmetica (orcamento, margem, ROI, payback).",
                "expressao: str",
                lambda expressao: calcular(str(expressao)),
            )
        )
        self.registrar(
            Ferramenta(
                "salvar_arquivo",
                "Grava um entregavel no workspace do projeto.",
                "caminho: str, conteudo: str",
                self._salvar_arquivo,
            )
        )
        self.registrar(
            Ferramenta(
                "ler_arquivo",
                "Le um arquivo ja produzido por outro agente no workspace.",
                "caminho: str",
                self._ler_arquivo,
            )
        )
        self.registrar(
            Ferramenta(
                "listar_workspace",
                "Lista os arquivos existentes no workspace.",
                "subpasta: str = ''",
                self._listar,
            )
        )

    # --- implementacoes padrao ---------------------------------------
    def _resolver(self, caminho: str) -> Path:
        alvo = (self.workspace / str(caminho).lstrip("/")).resolve()
        raiz = self.workspace.resolve()
        if raiz != alvo and raiz not in alvo.parents:
            raise ValueError("caminho fora do workspace nao e permitido")
        return alvo

    def _salvar_arquivo(self, caminho: str, conteudo: str) -> str:
        alvo = self._resolver(caminho)
        alvo.parent.mkdir(parents=True, exist_ok=True)
        alvo.write_text(str(conteudo), encoding="utf-8")
        return f"gravado: {alvo.relative_to(self.workspace.resolve())} ({len(str(conteudo))} chars)"

    def _ler_arquivo(self, caminho: str) -> str:
        alvo = self._resolver(caminho)
        if not alvo.is_file():
            return f"arquivo inexistente: {caminho}"
        return alvo.read_text(encoding="utf-8")[:8000]

    def _listar(self, subpasta: str = "") -> list[str]:
        base = self._resolver(subpasta) if subpasta else self.workspace.resolve()
        if not base.is_dir():
            return []
        return sorted(
            str(p.relative_to(self.workspace.resolve()))
            for p in base.rglob("*")
            if p.is_file()
        )

    # --- API ----------------------------------------------------------
    def registrar(self, ferramenta: Ferramenta) -> None:
        self._registro[ferramenta.nome] = ferramenta

    def disponiveis(self, nomes: list[str] | None = None) -> list[Ferramenta]:
        if nomes is None:
            return list(self._registro.values())
        return [self._registro[n] for n in nomes if n in self._registro]

    def manual(self, nomes: list[str] | None = None) -> str:
        ferramentas = self.disponiveis(nomes)
        if not ferramentas:
            return ""
        linhas = [f.assinatura() for f in ferramentas]
        return (
            "FERRAMENTAS DISPONIVEIS\n"
            + "\n".join(linhas)
            + "\n\nPara usar, emita UM bloco assim (e nada depois dele):\n"
            '```ferramenta\n{"ferramenta": "nome", "args": {"param": "valor"}}\n```\n'
            "O resultado volta para voce na proxima mensagem."
        )

    def extrair_chamada(self, texto: str) -> dict[str, Any] | None:
        """Encontra a chamada de ferramenta emitida pelo modelo, se houver."""
        for bloco in BLOCO_FERRAMENTA.findall(texto):
            try:
                dados = json.loads(bloco)
            except json.JSONDecodeError:
                continue
            if isinstance(dados, dict) and dados.get("ferramenta") in self._registro:
                return {"ferramenta": dados["ferramenta"], "args": dados.get("args") or {}}
        return None

    def executar(self, nome: str, args: dict[str, Any]) -> str:
        ferramenta = self._registro.get(nome)
        if ferramenta is None:
            return f"ERRO: ferramenta '{nome}' nao existe."
        try:
            resultado = ferramenta.executar(**args)
        except TypeError as exc:
            return f"ERRO: argumentos invalidos para '{nome}': {exc}"
        except Exception as exc:  # ferramenta falhou: o agente precisa saber
            return f"ERRO ao executar '{nome}': {exc}"
        if isinstance(resultado, (dict, list)):
            return json.dumps(resultado, ensure_ascii=False)
        return str(resultado)
