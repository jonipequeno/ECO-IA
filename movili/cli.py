"""Interface de linha de comando do ecossistema Movili."""

from __future__ import annotations

import argparse
import sys
import textwrap
from pathlib import Path

from . import agentes as quadro
from . import fluxos as processos
from .config import carregar
from .core.orquestrador import Ecossistema, Etapa, Fluxo
from .llm.base import LLMIndisponivel

VERSAO = "1.0.0"

FAIXA = "=" * 72


def _cabecalho(titulo: str) -> None:
    print(f"\n{FAIXA}\n  {titulo}\n{FAIXA}")


def _montar(args: argparse.Namespace, somente: list[str] | None = None) -> Ecossistema:
    cfg = carregar(
        backend_forcado=args.backend,
        modelo_forcado=args.modelo,
        perfil_hardware=args.perfil,
    )
    return Ecossistema(
        cfg,
        verboso=not args.silencioso,
        persistir=not args.sem_banco,
        somente=somente,
    )


def _finalizar(eco: Ecossistema, resultado, args: argparse.Namespace) -> int:
    if resultado.consolidacao:
        _cabecalho("CONSOLIDACAO DA DIRETORIA")
        print(resultado.consolidacao)

    destino = args.salvar or eco.config.workspace
    caminhos = eco.salvar(resultado, destino)
    print(f"\nRelatorio:  {caminhos['relatorio']}")
    print(f"Conversas:  {caminhos['conversas']}")

    metricas = eco.metricas()
    if metricas:
        total = sum(m["chamadas"] for m in metricas.values())
        tokens = sum(m["tokens_entrada"] + m["tokens_saida"] for m in metricas.values())
        print(f"Uso:        {total} chamadas de modelo, ~{tokens} tokens")
    eco.encerrar()
    return 0


# ---------------------------------------------------------------------
# Comandos
# ---------------------------------------------------------------------
def cmd_status(args: argparse.Namespace) -> int:
    cfg = carregar(backend_forcado=args.backend, modelo_forcado=args.modelo,
                   perfil_hardware=args.perfil)
    eco = Ecossistema(cfg, verboso=False, persistir=False)

    _cabecalho("STATUS DOS BACKENDS")
    algum = False
    for nome, info in eco.roteador.status().items():
        marca = "ONLINE " if info["online"] else "OFFLINE"
        algum = algum or (info["online"] and nome != "simulado")
        print(f"\n[{marca}] {nome} ({info['tipo']}) - {info['url']}")
        print(f"          modelo padrao: {info['modelo_padrao']}")
        modelos = info.get("modelos") or []
        if modelos:
            print(f"          modelos carregados ({len(modelos)}):")
            for m in modelos[:25]:
                print(f"            - {m}")
            if len(modelos) > 25:
                print(f"            ... e mais {len(modelos) - 25}")
        elif info["online"]:
            print("          nenhum modelo baixado ainda")

    _cabecalho("ROTEAMENTO POR AGENTE")
    for ident in eco.agentes:
        backend, modelo = cfg.modelo_do_agente(ident)
        print(f"  {ident:<14} {backend or '(fallback)':<10} {modelo or '(padrao do backend)'}")

    if not algum:
        print(
            "\nNenhum backend real esta no ar. Suba um deles:\n"
            "  Ollama    -> ollama serve   (e ./scripts/baixar_modelos.sh essenciais)\n"
            "  LM Studio -> aba Developer > Start Server (porta 1234)\n"
            "Para testar o encanamento sem modelo: movili <comando> --backend simulado"
        )
        return 1
    return 0


def cmd_equipe(args: argparse.Namespace) -> int:
    _cabecalho("MOVILI TECNOLOGIA - QUADRO DE FUNCIONARIOS")
    print(quadro.organograma())

    if args.detalhe:
        perfil = quadro.perfil_de(args.detalhe)
        _cabecalho(perfil.cracha())
        print(f"\nMISSAO\n{textwrap.fill(perfil.missao, 72)}")
        print("\nESPECIALIDADES")
        for e in perfil.especialidades:
            print(f"  - {e}")
        print("\nRESPONSABILIDADES")
        for r in perfil.responsabilidades:
            print(f"  - {r}")
        print("\nKPIs")
        for k in perfil.kpis:
            print(f"  - {k}")
        print(f"\nTemperatura: {perfil.temperatura} | Limite de tokens: {perfil.max_tokens}")
    else:
        print(f"\n{len(quadro.REGISTRO)} funcionarios ativos.")
        print("Detalhe de um deles:  movili equipe --detalhe dev_backend")
    return 0


def cmd_modelos(args: argparse.Namespace) -> int:
    cfg = carregar()
    _cabecalho("CATALOGO DE MODELOS ABERTOS DO OLLAMA")
    total = 0
    for grupo, dados in cfg.catalogo.items():
        if args.grupo and grupo != args.grupo:
            continue
        print(f"\n### {grupo.upper()} - {dados.get('descricao', '')}")
        for m in dados.get("modelos", []):
            total += 1
            print(f"\n  {m['nome']:<24} {m.get('ram', ''):>10}")
            print(f"    {textwrap.fill(m.get('usar_para', ''), 66, subsequent_indent='    ')}")

    _cabecalho("PERFIS DE HARDWARE")
    for nome, dados in cfg.perfis_hardware.items():
        print(f"\n  --perfil {nome}")
        print(f"    {dados.get('descricao', '')}")
        print(f"    modelo padrao: {dados.get('modelo_padrao')}")
        for agente, modelo in (dados.get("agentes") or {}).items():
            print(f"      {agente:<14} -> {modelo}")

    print(f"\n{total} modelos no catalogo.")
    print("Baixar um grupo:  ./scripts/baixar_modelos.sh essenciais")
    print("Baixar tudo:      ./scripts/baixar_modelos.sh todos")
    return 0


def cmd_fluxos(args: argparse.Namespace) -> int:
    _cabecalho("PROCESSOS INTERNOS DA MOVILI")
    for nome, descricao, n in processos.listar():
        print(f"\n  {nome}  ({n} etapas)")
        print(f"    {textwrap.fill(descricao, 66, subsequent_indent='    ')}")
        fluxo = processos.obter(nome)
        print("    Ordem: " + " -> ".join(e.agente for e in fluxo.etapas))
    print('\nExecutar:  movili fluxo novo-projeto "briefing do cliente aqui"')
    return 0


def cmd_agente(args: argparse.Namespace) -> int:
    eco = _montar(args, somente=[args.id])
    agente = eco.agente(args.id)
    _cabecalho(f"{agente.perfil.nome} - {agente.perfil.cargo}")
    try:
        resultado = eco.delegar(args.id, args.instrucao, projeto=args.projeto or "avulso")
    except LLMIndisponivel as exc:
        print(f"\nERRO: {exc}", file=sys.stderr)
        return 1
    print(f"\n{resultado.entrega}")
    eco.encerrar()
    return 0


def cmd_fluxo(args: argparse.Namespace) -> int:
    fluxo = processos.obter(args.nome)
    eco = _montar(args)
    try:
        resultado = eco.executar_fluxo(fluxo, args.briefing, projeto=args.projeto or "")
    except LLMIndisponivel as exc:
        print(f"\nERRO: {exc}", file=sys.stderr)
        return 1
    return _finalizar(eco, resultado, args)


def cmd_reuniao(args: argparse.Namespace) -> int:
    participantes = args.participantes.split(",") if args.participantes else None
    if args.setor:
        participantes = quadro.SETORES.get(args.setor)
        if participantes is None:
            print(f"setor '{args.setor}' nao existe. Disponiveis: {', '.join(quadro.SETORES)}",
                  file=sys.stderr)
            return 1
        participantes = [quadro.ORQUESTRADOR] + participantes

    eco = _montar(args)
    try:
        resultado = eco.reuniao(
            args.tema,
            participantes=participantes,
            rodadas=args.rodadas,
            projeto=args.projeto or "",
        )
    except LLMIndisponivel as exc:
        print(f"\nERRO: {exc}", file=sys.stderr)
        return 1
    return _finalizar(eco, resultado, args)


def cmd_atender(args: argparse.Namespace) -> int:
    eco = _montar(args)
    try:
        resultado = eco.atender(args.demanda, projeto=args.projeto or "", maximo=args.maximo)
    except LLMIndisponivel as exc:
        print(f"\nERRO: {exc}", file=sys.stderr)
        return 1
    return _finalizar(eco, resultado, args)


def cmd_chat(args: argparse.Namespace) -> int:
    eco = _montar(args)
    _cabecalho("MOVILI TECNOLOGIA - MODO CONVERSA")
    print(quadro.organograma())
    print(
        "\nComandos:\n"
        "  @id <mensagem>        fala com um funcionario especifico\n"
        "  /reuniao <tema>       convoca reuniao com a empresa toda\n"
        "  /equipe               mostra o organograma\n"
        "  /sair                 encerra\n"
        "  <mensagem>            a diretoria faz a triagem e escala o time"
    )
    while True:
        try:
            entrada = input("\nvoce> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not entrada:
            continue
        if entrada in {"/sair", "/quit", "/exit"}:
            break
        try:
            if entrada == "/equipe":
                print(quadro.organograma())
            elif entrada.startswith("/reuniao "):
                res = eco.reuniao(entrada[9:].strip(), rodadas=args.rodadas)
                print(f"\n--- ATA FINAL ---\n{res.consolidacao}")
            elif entrada.startswith("@"):
                ident, _, msg = entrada[1:].partition(" ")
                if ident not in eco:
                    print(f"nao temos '{ident}' na casa. Veja /equipe.")
                    continue
                res = eco.delegar(ident, msg or "Apresente-se e diga como pode ajudar.")
                print(f"\n{res.nome_agente}:\n{res.entrega}")
            else:
                res = eco.atender(entrada, maximo=args.maximo)
                print(f"\n--- DECISAO DA DIRETORIA ---\n{res.consolidacao}")
        except LLMIndisponivel as exc:
            print(f"ERRO: {exc}", file=sys.stderr)
        except KeyError as exc:
            print(f"ERRO: {exc}", file=sys.stderr)
    eco.encerrar()
    return 0


def cmd_memoria(args: argparse.Namespace) -> int:
    # aceita tanto "movili memoria indexar --projeto X" quanto "movili --projeto X memoria ..."
    projeto = getattr(args, "projeto_memoria", None) or args.projeto
    eco = _montar(args)
    try:
        if eco.semantica is None:
            print(
                "A memoria semantica esta desligada.\n"
                "Ligue em config/modelos.yaml (embeddings.habilitado: true) e baixe o "
                "modelo com:\n  ollama pull nomic-embed-text",
                file=sys.stderr,
            )
            return 1

        if args.acao == "status":
            s = eco.semantica.estatisticas()
            _cabecalho("MEMORIA SEMANTICA DA MOVILI")
            print(f"  trechos indexados: {s['trechos']}")
            print(f"  procedencia atual: {eco.semantica.assinatura}")
            if s["inativos"]:
                print(
                    f"  ATENCAO: {s['inativos']} trecho(s) foram indexados por outro "
                    "backend/modelo e estao invisiveis para a busca atual.\n"
                    "           Reindexe-os ou volte ao modelo anterior."
                )
            if s["projetos"]:
                print("\n  por projeto:")
                for projeto, n in list(s["projetos"].items())[:15]:
                    print(f"    {projeto:<34} {n:>4} trechos")
            if s["agentes"]:
                print("\n  por agente:")
                for agente, n in list(s["agentes"].items())[:20]:
                    print(f"    {agente:<34} {n:>4} trechos")
            if not s["trechos"]:
                print("\n  Nada indexado ainda. Rode um fluxo, ou indexe um projeto:")
                print("    movili memoria indexar --projeto <nome>")

        elif args.acao == "buscar":
            if not args.consulta:
                print("informe o que buscar: movili memoria buscar \"<consulta>\"", file=sys.stderr)
                return 1
            achados = eco.semantica.buscar(
                args.consulta, limite=args.limite, minimo=args.minimo,
                agente=args.agente, projeto=args.so_projeto,
            )
            _cabecalho(f"BUSCA: {args.consulta}")
            if not achados:
                print("  nada encontrado acima da similaridade minima.")
                print(f"  (tente --minimo menor que {args.minimo})")
            for a in achados:
                print(f"\n{a.citacao()}")

        elif args.acao == "indexar":
            if args.arquivo:
                caminho = Path(args.arquivo)
                if not caminho.is_file():
                    print(f"arquivo nao encontrado: {caminho}", file=sys.stderr)
                    return 1
                n = eco.semantica.indexar(
                    caminho.read_text(encoding="utf-8"),
                    origem="arquivo", referencia=str(caminho),
                    projeto=projeto or "", titulo=caminho.name,
                )
                print(f"{n} trecho(s) indexado(s) de {caminho}")
            elif projeto:
                if eco.memoria is None:
                    print("o banco esta desligado (--sem-banco)", file=sys.stderr)
                    return 1
                n = eco.semantica.indexar_entregaveis(eco.memoria, projeto)
                print(f"{n} trecho(s) indexado(s) do projeto '{projeto}'")
            else:
                print("informe --projeto <nome> ou --arquivo <caminho>", file=sys.stderr)
                return 1

        elif args.acao == "limpar":
            n = eco.semantica.limpar(projeto)
            alvo = f"do projeto '{projeto}'" if projeto else "de toda a memoria"
            print(f"{n} trecho(s) removido(s) {alvo}")
    except LLMIndisponivel as exc:
        print(f"\nERRO: {exc}", file=sys.stderr)
        return 1
    finally:
        eco.encerrar()
    return 0


def cmd_jarvis(args: argparse.Namespace) -> int:
    from .jarvis import diagnostico as diag_voz
    from .jarvis.sessao import SessaoJarvis

    if args.diagnostico:
        _cabecalho("OPENJARVIS - MOTORES DE VOZ")
        for nome, info in diag_voz().items():
            marca = "OK       " if info["disponivel"] else "ausente  "
            print(f"  [{marca}] {nome:<20} motor: {info['motor']}")
        print(
            "\nInstalar o que falta:\n"
            "  TTS  ->  pip install piper-tts && python -m piper.download_voices pt_BR-faber-medium\n"
            "           (ou apt install espeak-ng, que ja serve como alternativa)\n"
            "  STT  ->  pip install faster-whisper sounddevice numpy\n"
            "\nSem nenhum deles o Jarvis roda em modo texto, digitando e lendo na tela."
        )
        return 0

    eco = _montar(args)
    sessao = SessaoJarvis(
        eco,
        tts=args.tts,
        stt=args.stt,
        frases=args.frases,
        segundos_escuta=args.segundos,
        porta_voz=args.porta_voz,
    )
    try:
        return sessao.rodar()
    finally:
        eco.encerrar()


def cmd_ponte(args: argparse.Namespace) -> int:
    from .jarvis.ponte import servir

    eco = _montar(args)
    try:
        servir(eco, host=args.host, porta=args.porta, frases=args.frases)
    finally:
        eco.encerrar()
    return 0


def cmd_painel(args: argparse.Namespace) -> int:
    from .painel.servidor import servir

    eco = _montar(args)
    try:
        servir(eco, host=args.host, porta=args.porta)
    finally:
        eco.encerrar()
    return 0


def cmd_api(args: argparse.Namespace) -> int:
    try:
        import uvicorn
    except ImportError:
        print(
            "A API precisa de dependencias extras:\n  pip install -r requirements-api.txt",
            file=sys.stderr,
        )
        return 1
    uvicorn.run("movili.api.server:app", host=args.host, port=args.porta, reload=False)
    return 0


# ---------------------------------------------------------------------
def construir_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="movili",
        description="Ecossistema de agentes de IA da Movili Tecnologia (Ollama + LM Studio).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """
            exemplos:
              movili status
              movili equipe --detalhe financeiro
              movili modelos --grupo codigo
              movili agente copy "escreva a headline da nova landing de squad dedicada"
              movili fluxo novo-projeto "app de logistica para transportadora com 80 caminhoes"
              movili reuniao "vamos entrar no mercado de saude?" --rodadas 3
              movili atender "cliente quer integrar ERP com marketplace em 90 dias"
              movili chat
              movili jarvis --diagnostico
              movili jarvis                  # conversa por voz
              movili painel                  # acompanhe a empresa ao vivo no navegador
              movili ponte                   # expoe a empresa como API OpenAI
              movili memoria status
              movili memoria buscar "precificacao de projeto de logistica"
            """
        ),
    )
    p.add_argument("--version", action="version", version=f"movili {VERSAO}")
    p.add_argument("--backend", choices=["ollama", "lmstudio", "simulado"],
                   help="forca o backend de todos os agentes")
    p.add_argument("--modelo", help="forca um modelo para todos os agentes (ex: qwen3:14b)")
    p.add_argument("--perfil", help="preset de hardware: leve, equilibrado, especializado, maximo")
    p.add_argument("--projeto", help="identificador do projeto (agrupa entregas e memoria)")
    p.add_argument("--salvar", help="pasta de saida dos relatorios (padrao: workspace/)")
    p.add_argument("--silencioso", action="store_true", help="nao imprime o progresso")
    p.add_argument("--sem-banco", action="store_true", dest="sem_banco",
                   help="nao grava nada no SQLite")

    sub = p.add_subparsers(dest="comando", required=True)

    s = sub.add_parser("status", help="checa Ollama e LM Studio e mostra o roteamento")
    s.set_defaults(func=cmd_status)

    s = sub.add_parser("equipe", help="mostra o organograma e as fichas dos funcionarios")
    s.add_argument("--detalhe", help="id do agente para ver a ficha completa")
    s.set_defaults(func=cmd_equipe)

    s = sub.add_parser("modelos", help="catalogo de modelos do Ollama e o uso recomendado")
    s.add_argument("--grupo", help="essenciais, generalistas, raciocinio, codigo, embeddings, visao, leves")
    s.set_defaults(func=cmd_modelos)

    s = sub.add_parser("fluxos", help="lista os processos internos disponiveis")
    s.set_defaults(func=cmd_fluxos)

    s = sub.add_parser("agente", help="fala com um funcionario especifico")
    s.add_argument("id", help="identificador do agente (veja: movili equipe)")
    s.add_argument("instrucao", help="a tarefa")
    s.set_defaults(func=cmd_agente)

    s = sub.add_parser("fluxo", help="executa um processo interno de ponta a ponta")
    s.add_argument("nome", choices=sorted(processos.REGISTRO))
    s.add_argument("briefing", help="a demanda que entra no processo")
    s.set_defaults(func=cmd_fluxo)

    s = sub.add_parser("reuniao", help="convoca uma reuniao entre os agentes")
    s.add_argument("tema")
    s.add_argument("--participantes", help="ids separados por virgula")
    s.add_argument("--setor", help=f"convoca um setor inteiro: {', '.join(quadro.SETORES)}")
    s.add_argument("--rodadas", type=int, default=2, help="rodadas de debate (padrao: 2)")
    s.set_defaults(func=cmd_reuniao)

    s = sub.add_parser("atender", help="a diretoria faz a triagem e escala o time sozinha")
    s.add_argument("demanda")
    s.add_argument("--maximo", type=int, default=6, help="maximo de agentes escalados")
    s.set_defaults(func=cmd_atender)

    s = sub.add_parser("chat", help="modo conversa interativo com a empresa")
    s.add_argument("--rodadas", type=int, default=2)
    s.add_argument("--maximo", type=int, default=5)
    s.set_defaults(func=cmd_chat)

    s = sub.add_parser("memoria", help="memoria semantica: o que a empresa ja produziu")
    s.add_argument("acao", choices=["status", "buscar", "indexar", "limpar"])
    s.add_argument("consulta", nargs="?", help="texto a buscar (acao 'buscar')")
    s.add_argument("--limite", type=int, default=5, help="quantos trechos devolver")
    s.add_argument("--minimo", type=float, default=0.25, help="similaridade minima (0 a 1)")
    s.add_argument("--agente", help="restringe a busca a um funcionario")
    s.add_argument("--so-projeto", dest="so_projeto", help="restringe a busca a um projeto")
    s.add_argument("--arquivo", help="indexa um arquivo de texto ou markdown")
    # dest proprio: um --projeto com default None aqui sobrescreveria o global
    s.add_argument("--projeto", dest="projeto_memoria",
                   help="projeto alvo de 'indexar' e 'limpar'")
    s.set_defaults(func=cmd_memoria, projeto_memoria=None)

    s = sub.add_parser("jarvis", help="conversa por voz com a empresa (OpenJarvis)")
    s.add_argument("--tts", default="auto", choices=["auto", "piper", "sistema", "texto"],
                   help="motor de fala (padrao: detecta o que estiver instalado)")
    s.add_argument("--stt", default="auto", choices=["auto", "whisper", "whisper.cpp", "teclado"],
                   help="motor de escuta (padrao: detecta; sem microfone usa teclado)")
    s.add_argument("--frases", type=int, default=4, help="tamanho da resposta falada")
    s.add_argument("--segundos", type=int, default=8, help="duracao de cada escuta")
    s.add_argument("--porta-voz", dest="porta_voz", default="diretor",
                   help="quem responde quando a pergunta e aberta")
    s.add_argument("--diagnostico", action="store_true",
                   help="so mostra quais motores de voz estao instalados")
    s.set_defaults(func=cmd_jarvis)

    s = sub.add_parser("ponte", help="ponte OpenAI-compativel para clientes de voz externos")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--porta", type=int, default=8123)
    s.add_argument("--frases", type=int, default=6)
    s.set_defaults(func=cmd_ponte)

    s = sub.add_parser("painel", help="painel web: acompanhe a empresa trabalhando ao vivo")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--porta", type=int, default=8080)
    s.set_defaults(func=cmd_painel)

    s = sub.add_parser("api", help="sobe a API HTTP do ecossistema")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--porta", type=int, default=8000)
    s.set_defaults(func=cmd_api)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = construir_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except KeyboardInterrupt:
        print("\ninterrompido.", file=sys.stderr)
        return 130
    except (KeyError, ValueError, FileNotFoundError) as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
