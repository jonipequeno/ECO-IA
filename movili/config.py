"""Carregamento de configuracao do ecossistema (YAML + variaveis de ambiente)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:  # PyYAML e o formato preferido; JSON funciona como alternativa
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]

from .llm.router import ConfigBackend

RAIZ = Path(__file__).resolve().parent.parent
DIR_CONFIG = RAIZ / "config"

# Variaveis de ambiente reconhecidas (todas opcionais).
ENV_OLLAMA_URL = "MOVILI_OLLAMA_URL"
ENV_LMSTUDIO_URL = "MOVILI_LMSTUDIO_URL"
ENV_MODELO = "MOVILI_MODELO_PADRAO"
ENV_BACKEND = "MOVILI_BACKEND_PADRAO"
ENV_TIMEOUT = "MOVILI_TIMEOUT"
ENV_DB = "MOVILI_DB"
ENV_WORKSPACE = "MOVILI_WORKSPACE"
ENV_EMBEDDINGS = "MOVILI_EMBEDDINGS"      # "0" desliga a memoria semantica
ENV_MODELO_EMBED = "MOVILI_MODELO_EMBEDDING"
ENV_OBSIDIAN = "MOVILI_OBSIDIAN"          # pasta do cofre; vazio desliga


def _ler_arquivo(caminho: Path) -> dict[str, Any]:
    if not caminho.is_file():
        raise FileNotFoundError(f"arquivo de configuracao ausente: {caminho}")
    texto = caminho.read_text(encoding="utf-8")
    if caminho.suffix in {".yaml", ".yml"}:
        if yaml is None:
            raise RuntimeError(
                "PyYAML nao esta instalado. Rode 'pip install pyyaml' ou use config em JSON."
            )
        return yaml.safe_load(texto) or {}
    return json.loads(texto)


@dataclass
class Config:
    """Configuracao completa do ecossistema."""

    empresa: dict[str, Any] = field(default_factory=dict)
    backends: dict[str, ConfigBackend] = field(default_factory=dict)
    ordem_fallback: list[str] = field(default_factory=list)
    roteamento: dict[str, dict[str, Any]] = field(default_factory=dict)
    catalogo: dict[str, Any] = field(default_factory=dict)
    perfis_hardware: dict[str, Any] = field(default_factory=dict)
    embeddings: dict[str, Any] = field(default_factory=dict)
    caminho_db: str = "data/movili.db"
    workspace: str = "workspace"
    obsidian: str = ""  # pasta do cofre do Obsidian; vazio desliga a exportacao
    tentativas: int = 2

    def modelo_do_agente(self, agente: str) -> tuple[str | None, str | None]:
        """Devolve (backend, modelo) configurados para um agente."""
        regra = self.roteamento.get(agente) or self.roteamento.get("padrao") or {}
        return regra.get("backend"), regra.get("modelo")

    def aplicar_perfil_hardware(self, nome: str) -> "Config":
        """Troca os modelos de todos os agentes pelo preset de hardware escolhido.

        Presets ficam em config/modelos.yaml -> perfis_hardware (ex.: 'leve',
        'equilibrado', 'completo'). Util para rodar o mesmo ecossistema em um
        notebook de 8 GB ou em uma workstation de 48 GB.
        """
        preset = self.perfis_hardware.get(nome)
        if preset is None:
            disponiveis = ", ".join(sorted(self.perfis_hardware)) or "nenhum"
            raise KeyError(f"perfil de hardware '{nome}' nao existe. Disponiveis: {disponiveis}")

        mapa = preset.get("agentes") or {}
        padrao = preset.get("modelo_padrao")
        for agente, regra in self.roteamento.items():
            novo = mapa.get(agente, padrao)
            if novo:
                regra["modelo"] = novo
        if padrao:
            for cfg in self.backends.values():
                cfg.modelo_padrao = padrao
        return self


def carregar(
    dir_config: str | Path | None = None,
    *,
    backend_forcado: str | None = None,
    modelo_forcado: str | None = None,
    perfil_hardware: str | None = None,
) -> Config:
    """Le config/empresa.yaml e config/modelos.yaml e aplica os overrides."""
    base = Path(dir_config) if dir_config else DIR_CONFIG
    empresa = _ler_arquivo(base / "empresa.yaml")
    modelos = _ler_arquivo(base / "modelos.yaml")

    timeout_padrao = int(os.getenv(ENV_TIMEOUT, modelos.get("timeout", 300)))
    backends: dict[str, ConfigBackend] = {}
    for nome, dados in (modelos.get("backends") or {}).items():
        url = dados.get("base_url", "")
        if nome == "ollama":
            url = os.getenv(ENV_OLLAMA_URL, url)
        elif nome == "lmstudio":
            url = os.getenv(ENV_LMSTUDIO_URL, url)
        backends[nome] = ConfigBackend(
            tipo=dados.get("tipo", nome),
            base_url=url,
            modelo_padrao=os.getenv(ENV_MODELO, dados.get("modelo_padrao", "qwen3:8b")),
            timeout=int(dados.get("timeout", timeout_padrao)),
            habilitado=bool(dados.get("habilitado", True)),
        )

    if not backends:
        raise ValueError("config/modelos.yaml nao declarou nenhum backend")

    ordem = list(modelos.get("ordem_fallback") or backends.keys())
    backend_env = os.getenv(ENV_BACKEND)
    escolhido = backend_forcado or backend_env
    if escolhido:
        if escolhido not in backends:
            raise KeyError(
                f"backend '{escolhido}' nao existe em config/modelos.yaml. "
                f"Disponiveis: {', '.join(sorted(backends))}"
            )
        ordem = [escolhido] + [n for n in ordem if n != escolhido]

    roteamento = {k: dict(v) for k, v in (modelos.get("roteamento") or {}).items()}
    if escolhido:
        for regra in roteamento.values():
            regra["backend"] = escolhido
    if modelo_forcado:
        for regra in roteamento.values():
            regra["modelo"] = modelo_forcado
        for cfg in backends.values():
            cfg.modelo_padrao = modelo_forcado

    cfg = Config(
        empresa=empresa.get("empresa", empresa),
        backends=backends,
        ordem_fallback=ordem,
        roteamento=roteamento,
        catalogo=modelos.get("catalogo") or {},
        embeddings=modelos.get("embeddings") or {},
        perfis_hardware=modelos.get("perfis_hardware") or {},
        caminho_db=os.getenv(ENV_DB, modelos.get("banco", "data/movili.db")),
        workspace=os.getenv(ENV_WORKSPACE, modelos.get("workspace", "workspace")),
        obsidian=os.getenv(ENV_OBSIDIAN, modelos.get("obsidian") or "").strip(),
        tentativas=int(modelos.get("tentativas", 2)),
    )

    desligar = os.getenv(ENV_EMBEDDINGS)
    if desligar is not None and desligar.strip().lower() in {"0", "false", "nao", "no"}:
        cfg.embeddings["habilitado"] = False
    modelo_embed = os.getenv(ENV_MODELO_EMBED)
    if modelo_embed:
        cfg.embeddings["modelo"] = modelo_embed
    if escolhido == "simulado":
        # no modo simulado a vetorizacao tambem e simulada, pelo mesmo provedor
        cfg.embeddings["backend"] = "simulado"

    if perfil_hardware:
        cfg.aplicar_perfil_hardware(perfil_hardware)
    if modelo_forcado:  # o override manual vence o preset de hardware
        for regra in cfg.roteamento.values():
            regra["modelo"] = modelo_forcado
    return cfg
