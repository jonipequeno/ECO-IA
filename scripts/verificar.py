#!/usr/bin/env python3
"""Verificacao rapida do ambiente: backends, modelos, agentes e fluxos.

    python scripts/verificar.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from movili import agentes as quadro  # noqa: E402
from movili import fluxos as processos  # noqa: E402
from movili.config import carregar  # noqa: E402
from movili.llm.router import RoteadorLLM  # noqa: E402


def main() -> int:
    print("=" * 70)
    print(" Movili Tecnologia - verificacao do ambiente")
    print("=" * 70)

    cfg = carregar()
    print(f"\n[config] empresa: {cfg.empresa.get('nome')}")
    print(f"[config] workspace: {cfg.workspace} | banco: {cfg.caminho_db}")

    print(f"\n[equipe] {len(quadro.REGISTRO)} funcionarios")
    for setor, ids in quadro.SETORES.items():
        print(f"         {setor:<20} {len(ids)} pessoa(s)")

    emb = cfg.embeddings or {}
    if emb.get("habilitado"):
        print(f"[config] memoria semantica: {emb.get('modelo')} "
              f"(minimo {emb.get('similaridade_minima')})")
    else:
        print("[config] memoria semantica: desligada")

    print(f"\n[fluxos] {len(processos.REGISTRO)} processos internos")
    for nome, _desc, etapas in processos.listar():
        print(f"         {nome:<22} {etapas} etapas")

    # todo agente referenciado em algum fluxo precisa existir
    problemas = []
    for nome in processos.REGISTRO:
        for etapa in processos.obter(nome).etapas:
            if etapa.agente not in quadro.REGISTRO:
                problemas.append(f"fluxo '{nome}' aciona agente inexistente: {etapa.agente}")
    # todo agente precisa de regra de roteamento (ou herda 'padrao')
    for ident in quadro.REGISTRO:
        if ident not in cfg.roteamento and "padrao" not in cfg.roteamento:
            problemas.append(f"agente '{ident}' sem modelo configurado")

    roteador = RoteadorLLM(cfg.backends, cfg.ordem_fallback)
    print("\n[backends]")
    online = False
    for nome, info in roteador.status().items():
        marca = "ONLINE " if info["online"] else "OFFLINE"
        print(f"         [{marca}] {nome:<10} {info['url']}")
        if info["online"] and nome != "simulado":
            online = True
            faltando = _modelos_faltando(cfg, info.get("modelos") or [])
            if faltando:
                print(f"                    modelos configurados que faltam baixar: {', '.join(sorted(faltando))}")

    if problemas:
        print("\n[PROBLEMAS]")
        for p in problemas:
            print(f"  - {p}")
        return 1

    print("\n[ok] estrutura consistente.")
    if not online:
        print("[aviso] nenhum backend real no ar. Suba o Ollama (ollama serve) ou o LM Studio.")
        print("        Para testar sem modelo: movili <comando> --backend simulado")
        return 0
    return 0


def _modelos_faltando(cfg, instalados: list[str]) -> set[str]:
    base = {m.split(":")[0] for m in instalados}
    desejados = {r.get("modelo") for r in cfg.roteamento.values() if r.get("modelo")}
    if (cfg.embeddings or {}).get("habilitado"):
        desejados.add(cfg.embeddings.get("modelo", "nomic-embed-text"))
    return {m for m in desejados if m and m not in instalados and m.split(":")[0] not in base}


if __name__ == "__main__":
    raise SystemExit(main())
