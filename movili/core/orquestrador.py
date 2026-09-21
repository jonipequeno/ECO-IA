"""Ecossistema: monta a empresa, roteia demandas e faz os agentes conversarem."""

from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

from .. import agentes as quadro
from ..config import Config
from ..llm.router import RoteadorLLM
from .agente import Agente, Perfil
from .barramento import Barramento
from .ferramentas import CaixaDeFerramentas
from .memoria import MemoriaCorporativa
from .mensagem import Mensagem, Prioridade, Tipo
from .obsidian import CofreObsidian, Ficha
from .rag import MemoriaSemantica

JSON_LISTA = re.compile(r"\[[^\[\]]*\]", re.DOTALL)

# Sentinela para "quem coordena o ecossistema", resolvida em tempo de execucao.
#
# Nao da para usar quadro.ORQUESTRADOR como valor padrao aqui: movili.agentes
# importa movili.core.agente, o que dispara movili/core/__init__.py; se este
# modulo for carregado nesse meio do caminho, os defaults seriam avaliados com
# movili.agentes ainda pela metade e quebrariam com AttributeError.
PADRAO = "__orquestrador_padrao__"


def _resolver(ident: str | None) -> str | None:
    """Troca a sentinela pelo orquestrador real do quadro."""
    return quadro.ORQUESTRADOR if ident == PADRAO else ident


def _ficha_do_quadro(ident: str) -> Ficha | None:
    """Ficha do funcionario para o cofre do Obsidian (resolvida so quando usada)."""
    if ident not in quadro.REGISTRO:
        return None
    p = quadro.perfil_de(ident)
    return Ficha(id=p.id, nome=p.nome, cargo=p.cargo, setor=p.setor, missao=p.missao)


@dataclass
class Etapa:
    """Um passo de um fluxo de trabalho."""

    agente: str
    instrucao: str
    usa_saida_de: list[str] = field(default_factory=list)
    tipo: Tipo = Tipo.TAREFA
    paralelo_com: list[str] = field(default_factory=list)
    rotulo: str = ""

    def titulo(self) -> str:
        return self.rotulo or self.instrucao[:70]


@dataclass
class Fluxo:
    """Processo interno da empresa (ex.: novo projeto, campanha, prospeccao)."""

    nome: str
    descricao: str
    etapas: list[Etapa]
    consolidador: str | None = PADRAO
    instrucao_consolidacao: str = (
        "Consolide as entregas acima em um plano unico e executavel da Movili. "
        "Resolva as contradicoes entre as areas explicitamente - nao repita o que "
        "cada um disse, decida."
    )


@dataclass
class ResultadoEtapa:
    agente: str
    nome_agente: str
    cargo: str
    instrucao: str
    entrega: str
    duracao_s: float = 0.0


@dataclass
class ResultadoFluxo:
    fluxo: str
    projeto: str
    briefing: str
    etapas: list[ResultadoEtapa] = field(default_factory=list)
    consolidacao: str = ""
    iniciado_em: str = ""
    concluido_em: str = ""

    def por_agente(self, ident: str) -> str:
        return "\n\n".join(e.entrega for e in self.etapas if e.agente == ident)

    def to_dict(self) -> dict[str, Any]:
        return {
            "fluxo": self.fluxo,
            "projeto": self.projeto,
            "briefing": self.briefing,
            "iniciado_em": self.iniciado_em,
            "concluido_em": self.concluido_em,
            "etapas": [
                {
                    "agente": e.agente,
                    "nome": e.nome_agente,
                    "cargo": e.cargo,
                    "instrucao": e.instrucao,
                    "entrega": e.entrega,
                    "duracao_s": round(e.duracao_s, 1),
                }
                for e in self.etapas
            ],
            "consolidacao": self.consolidacao,
        }

    def markdown(self) -> str:
        linhas = [
            f"# {self.fluxo}",
            "",
            f"**Projeto:** {self.projeto}  ",
            f"**Iniciado:** {self.iniciado_em}  ",
            f"**Concluido:** {self.concluido_em}",
            "",
            "## Briefing",
            "",
            self.briefing,
            "",
        ]
        for i, e in enumerate(self.etapas, 1):
            linhas += [
                f"## {i}. {e.nome_agente} - {e.cargo}",
                "",
                f"> **Tarefa:** {e.instrucao}",
                "",
                e.entrega,
                "",
            ]
        if self.consolidacao:
            linhas += ["## Consolidacao da diretoria", "", self.consolidacao, ""]
        return "\n".join(linhas)


class Ecossistema:
    """A Movili Tecnologia inteira, em memoria."""

    def __init__(
        self,
        config: Config,
        *,
        verboso: bool = True,
        persistir: bool = True,
        somente: Iterable[str] | None = None,
    ) -> None:
        self.config = config
        self.verboso = verboso
        self.roteador = RoteadorLLM(
            config.backends, config.ordem_fallback, tentativas=config.tentativas
        )
        self.barramento = Barramento(verboso=False)
        self.ferramentas = CaixaDeFerramentas(config.workspace)
        self.memoria = MemoriaCorporativa(config.caminho_db) if persistir else None
        self.semantica = self._montar_semantica(persistir)

        ids = list(somente) if somente else list(quadro.REGISTRO)
        self.agentes: dict[str, Agente] = {}
        for ident in ids:
            perfil = quadro.perfil_de(ident)
            backend, modelo = config.modelo_do_agente(ident)
            perfil.backend = backend or perfil.backend
            perfil.modelo = modelo or perfil.modelo
            self.agentes[ident] = Agente(
                perfil,
                self.roteador,
                self.barramento,
                empresa=config.empresa,
                ferramentas=self.ferramentas,
                memoria=self.memoria,
            )
        self.ao_falar: Callable[[str, str, str], None] | None = None

    def _montar_semantica(self, persistir: bool) -> MemoriaSemantica | None:
        """Liga a memoria semantica, se configurada. Falhar aqui nao derruba a empresa."""
        cfg = self.config.embeddings or {}
        if not persistir or not cfg.get("habilitado", False):
            return None
        try:
            return MemoriaSemantica(
                self.roteador,
                self.config.caminho_db,
                modelo=cfg.get("modelo", "nomic-embed-text"),
                backend=cfg.get("backend"),
            )
        except Exception as exc:  # banco travado, disco cheio: segue sem memoria
            self._log(f"   (memoria semantica indisponivel: {exc})")
            return None

    # ------------------------------------------------------------------
    # Utilitarios
    # ------------------------------------------------------------------
    def __contains__(self, ident: str) -> bool:
        return ident in self.agentes

    def agente(self, ident: str) -> Agente:
        if ident not in self.agentes:
            raise KeyError(
                f"agente '{ident}' nao esta ativo. Ativos: {', '.join(sorted(self.agentes))}"
            )
        return self.agentes[ident]

    def diretorio(self, exceto: str | None = None) -> dict[str, str]:
        """Mapa id -> 'Nome, Cargo' entregue aos agentes para que se acionem."""
        return {
            ident: f"{a.perfil.nome}, {a.perfil.cargo}"
            for ident, a in self.agentes.items()
            if ident != exceto
        }

    def _log(self, texto: str) -> None:
        if self.verboso:
            print(texto, flush=True)

    def _anunciar(self, ident: str, instrucao: str, entrega: str) -> None:
        if self.ao_falar is not None:
            self.ao_falar(ident, instrucao, entrega)

    # ------------------------------------------------------------------
    # Execucao de um agente
    # ------------------------------------------------------------------
    def delegar(
        self,
        ident: str,
        instrucao: str,
        *,
        contexto: str = "",
        projeto: str = "",
        remetente: str = PADRAO,
        tipo: Tipo = Tipo.TAREFA,
        prioridade: Prioridade = Prioridade.NORMAL,
        thread: str = "",
        propagar_handoff: bool = False,
        profundidade: int = 0,
    ) -> ResultadoEtapa:
        """Manda uma tarefa para um agente, registra no barramento e devolve a entrega."""
        remetente = _resolver(remetente) or quadro.ORQUESTRADOR
        agente = self.agente(ident)
        inicio = datetime.now(timezone.utc)

        tarefa = self.barramento.enviar(
            remetente,
            ident,
            instrucao[:80],
            instrucao,
            tipo=tipo,
            prioridade=prioridade,
            thread=thread,
            projeto=projeto,
        )
        self._log(f"\n>> {agente.perfil.nome} ({agente.perfil.cargo}) trabalhando...")

        contexto = self._com_memoria(contexto, instrucao, ident, projeto)
        entrega = agente.responder(
            instrucao, contexto=contexto, colegas=self.diretorio(exceto=ident)
        )
        duracao = (datetime.now(timezone.utc) - inicio).total_seconds()

        self.barramento.enviar(
            ident,
            remetente,
            f"Re: {tarefa.assunto}",
            entrega,
            tipo=Tipo.ENTREGA,
            thread=tarefa.thread,
            projeto=projeto,
        )
        if self.memoria is not None and projeto:
            self.memoria.salvar_entregavel(projeto, ident, tarefa.assunto, entrega)
        self._indexar(entrega, ident, projeto, tarefa.assunto, tarefa.id)

        self._log(f"<< {agente.perfil.nome} concluiu em {duracao:.1f}s")
        self._anunciar(ident, instrucao, entrega)

        if propagar_handoff and profundidade < 2:
            self._executar_handoffs(agente, entrega, projeto, tarefa.thread, profundidade)
        return ResultadoEtapa(
            agente=ident,
            nome_agente=agente.perfil.nome,
            cargo=agente.perfil.cargo,
            instrucao=instrucao,
            entrega=entrega,
            duracao_s=duracao,
        )

    def _com_memoria(self, contexto: str, instrucao: str, ident: str, projeto: str) -> str:
        """Acrescenta ao contexto o que a empresa ja produziu sobre o assunto."""
        if self.semantica is None:
            return contexto
        cfg = self.config.embeddings or {}
        bloco = self.semantica.contexto(
            f"{instrucao}\n{contexto[:800]}",
            limite=int(cfg.get("trechos_por_consulta", 3)),
            minimo=float(cfg.get("similaridade_minima", 0.35)),
            excluir_projeto=projeto or None,
        )
        if not bloco:
            return contexto
        self._log("   (recuperou memoria de projetos anteriores)")
        return f"{bloco}\n\n---\n\n{contexto}" if contexto else bloco

    def _indexar(self, entrega: str, ident: str, projeto: str, titulo: str, referencia: str) -> None:
        """Guarda a entrega no indice semantico para as proximas execucoes."""
        if self.semantica is None or not (self.config.embeddings or {}).get("indexar_entregas", True):
            return
        try:
            self.semantica.indexar(
                entrega, origem="entrega", referencia=referencia,
                projeto=projeto, agente=ident, titulo=titulo,
            )
        except Exception as exc:  # indexar e melhoria, nao pode quebrar a entrega
            self._log(f"   (nao foi possivel indexar a entrega: {exc})")

    def _executar_handoffs(
        self, origem: Agente, entrega: str, projeto: str, thread: str, profundidade: int
    ) -> list[ResultadoEtapa]:
        """Executa os acionamentos '@colega {pedido}' que o agente emitiu."""
        resultados: list[ResultadoEtapa] = []
        for destino, pedido in origem.handoffs(entrega)[:2]:
            if destino not in self.agentes or destino == origem.id:
                continue
            self._log(f"   -> {origem.perfil.nome} acionou @{destino}: {pedido}")
            resultados.append(
                self.delegar(
                    destino,
                    pedido,
                    contexto=f"Pedido de {origem.perfil.nome} ({origem.perfil.cargo}):\n{entrega[:1500]}",
                    projeto=projeto,
                    remetente=origem.id,
                    tipo=Tipo.PERGUNTA,
                    thread=thread,
                    propagar_handoff=True,
                    profundidade=profundidade + 1,
                )
            )
        return resultados

    def em_paralelo(
        self,
        pedidos: list[tuple[str, str]],
        *,
        contexto: str = "",
        projeto: str = "",
        thread: str = "",
        max_workers: int = 3,
    ) -> list[ResultadoEtapa]:
        """Roda varios agentes ao mesmo tempo (util quando nao ha dependencia).

        Atencao: com um unico backend local, paralelismo alto enfileira no
        servidor de modelo. 2 ou 3 e o ponto util na maioria das maquinas.
        """
        if not pedidos:
            return []
        if len(pedidos) == 1:
            ident, instrucao = pedidos[0]
            return [self.delegar(ident, instrucao, contexto=contexto, projeto=projeto, thread=thread)]

        with ThreadPoolExecutor(max_workers=max(1, min(max_workers, len(pedidos)))) as pool:
            futuros = [
                pool.submit(
                    self.delegar, ident, instrucao,
                    contexto=contexto, projeto=projeto, thread=thread,
                )
                for ident, instrucao in pedidos
            ]
            return [f.result() for f in futuros]

    # ------------------------------------------------------------------
    # Fluxos
    # ------------------------------------------------------------------
    def executar_fluxo(
        self, fluxo: Fluxo, briefing: str, *, projeto: str = "", consolidar: bool = True
    ) -> ResultadoFluxo:
        projeto = projeto or f"{fluxo.nome.lower().replace(' ', '-')}-{datetime.now():%Y%m%d-%H%M}"
        resultado = ResultadoFluxo(
            fluxo=fluxo.nome,
            projeto=projeto,
            briefing=briefing,
            iniciado_em=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )
        thread = f"fluxo-{projeto}"
        self._log(f"\n{'=' * 70}\nFLUXO: {fluxo.nome}\nPROJETO: {projeto}\n{'=' * 70}")

        saidas: dict[str, str] = {}
        pendentes = list(fluxo.etapas)
        executadas: set[int] = set()

        for indice, etapa in enumerate(pendentes):
            if indice in executadas or etapa.agente not in self.agentes:
                if etapa.agente not in self.agentes:
                    self._log(f"   (pulando etapa de @{etapa.agente}: agente inativo)")
                continue

            grupo = [(indice, etapa)]
            if etapa.paralelo_com:
                for j, outra in enumerate(pendentes):
                    if j > indice and outra.agente in etapa.paralelo_com and outra.agente in self.agentes:
                        grupo.append((j, outra))

            contexto = self._montar_contexto(briefing, saidas, etapa)
            if len(grupo) == 1:
                res = self.delegar(
                    etapa.agente, etapa.instrucao, contexto=contexto,
                    projeto=projeto, thread=thread, tipo=etapa.tipo,
                )
                resultado.etapas.append(res)
                saidas[etapa.agente] = res.entrega
                executadas.add(indice)
            else:
                lote = self.em_paralelo(
                    [(e.agente, e.instrucao) for _, e in grupo],
                    contexto=contexto, projeto=projeto, thread=thread,
                )
                for res in lote:
                    resultado.etapas.append(res)
                    saidas[res.agente] = res.entrega
                executadas.update(i for i, _ in grupo)

        consolidador = _resolver(fluxo.consolidador)
        if consolidar and consolidador and consolidador in self.agentes:
            contexto = self._montar_contexto(briefing, saidas, None)
            res = self.delegar(
                consolidador,
                fluxo.instrucao_consolidacao,
                contexto=contexto,
                projeto=projeto,
                thread=thread,
                tipo=Tipo.DECISAO,
                remetente="sistema",
            )
            resultado.consolidacao = res.entrega

        resultado.concluido_em = datetime.now(timezone.utc).isoformat(timespec="seconds")
        return resultado

    def _montar_contexto(
        self, briefing: str, saidas: dict[str, str], etapa: Etapa | None, limite: int = 2600
    ) -> str:
        partes = [f"BRIEFING ORIGINAL\n{briefing}"]
        if etapa is not None and etapa.usa_saida_de:
            fontes = [i for i in etapa.usa_saida_de if i in saidas]
        else:
            fontes = list(saidas)
        for ident in fontes:
            a = self.agentes.get(ident)
            titulo = f"{a.perfil.nome} ({a.perfil.cargo})" if a else ident
            partes.append(f"ENTREGA DE {titulo}\n{saidas[ident][:limite]}")
        return "\n\n---\n\n".join(partes)

    # ------------------------------------------------------------------
    # Reuniao: os agentes conversam entre si de verdade
    # ------------------------------------------------------------------
    def reuniao(
        self,
        tema: str,
        *,
        participantes: list[str] | None = None,
        rodadas: int = 2,
        projeto: str = "",
        mediador: str | None = PADRAO,
    ) -> ResultadoFluxo:
        """Mesa redonda: cada agente ouve o que os anteriores disseram e responde.

        Diferente do fluxo, aqui nao ha ordem de dependencia - ha debate. Na
        segunda rodada em diante cada um pode concordar, discordar ou pedir algo
        a um colega.
        """
        mediador = _resolver(mediador)
        presentes = [i for i in (participantes or list(self.agentes)) if i in self.agentes]
        if mediador and mediador in self.agentes and mediador in presentes:
            presentes = [mediador] + [i for i in presentes if i != mediador]

        projeto = projeto or f"reuniao-{datetime.now():%Y%m%d-%H%M}"
        thread = f"reuniao-{projeto}"
        resultado = ResultadoFluxo(
            fluxo=f"Reuniao: {tema}",
            projeto=projeto,
            briefing=tema,
            iniciado_em=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )
        self._log(f"\n{'=' * 70}\nREUNIAO: {tema}\nPresentes: {', '.join(presentes)}\n{'=' * 70}")

        ata: list[str] = []
        for rodada in range(1, rodadas + 1):
            self._log(f"\n--- Rodada {rodada} de {rodadas} ---")
            for ident in presentes:
                agente = self.agente(ident)
                if rodada == 1:
                    instrucao = (
                        f"Reuniao interna da Movili sobre: {tema}\n\n"
                        "Traga a sua posicao sob a otica da SUA area, em ate 12 linhas. "
                        "Seja concreto: numero, prazo, requisito ou risco. Termine indicando "
                        "o que voce precisa de qual colega."
                    )
                else:
                    instrucao = (
                        f"Reuniao interna da Movili sobre: {tema}\n\n"
                        "Voce ja ouviu os colegas (ata abaixo). Agora, em ate 10 linhas: "
                        "(a) responda diretamente a quem citou a sua area, "
                        "(b) diga onde voce discorda e por que, "
                        "(c) feche com o compromisso que a SUA area assume."
                    )
                contexto = "ATA ATE AQUI\n" + "\n\n".join(ata[-8:]) if ata else ""
                res = self.delegar(
                    ident, instrucao, contexto=contexto, projeto=projeto,
                    thread=thread, tipo=Tipo.DECISAO if ident == mediador else Tipo.INFORME,
                    remetente=mediador or "sistema",
                )
                resultado.etapas.append(res)
                ata.append(f"[{agente.perfil.nome} - {agente.perfil.cargo}]\n{res.entrega[:1800]}")

        if mediador and mediador in self.agentes:
            res = self.delegar(
                mediador,
                (
                    "Encerre a reuniao. Produza a ATA FINAL com: decisoes tomadas, "
                    "divergencias que ficaram em aberto, responsavel e prazo de cada acao, "
                    "e o que a empresa NAO vai fazer agora."
                ),
                contexto="ATA COMPLETA\n" + "\n\n".join(ata),
                projeto=projeto,
                thread=thread,
                tipo=Tipo.DECISAO,
                remetente="sistema",
            )
            resultado.consolidacao = res.entrega

        resultado.concluido_em = datetime.now(timezone.utc).isoformat(timespec="seconds")
        return resultado

    # ------------------------------------------------------------------
    # Triagem automatica: o diretor decide quem atua
    # ------------------------------------------------------------------
    def triagem(self, demanda: str, maximo: int = 6) -> list[str]:
        """Pede ao diretor a lista de agentes que devem atuar nesta demanda."""
        diretor = self.agentes.get(quadro.ORQUESTRADOR)
        if diretor is None:
            return list(self.agentes)[:maximo]

        catalogo = "\n".join(f"- {i}: {d}" for i, d in self.diretorio().items())
        instrucao = (
            f"Demanda que chegou na Movili:\n{demanda}\n\n"
            f"Equipe disponivel:\n{catalogo}\n\n"
            f"Escolha no maximo {maximo} agentes que precisam atuar, na ordem de atuacao. "
            "Responda SOMENTE com um array JSON de identificadores, sem explicacao. "
            'Exemplo: ["comercial", "dev_backend", "financeiro"]'
        )
        texto = diretor.responder(instrucao, temperatura=0.2, max_tokens=300, registrar=False)

        escolhidos: list[str] = []
        achado = JSON_LISTA.search(texto)
        if achado:
            try:
                escolhidos = [str(x) for x in json.loads(achado.group(0))]
            except json.JSONDecodeError:
                escolhidos = []
        if not escolhidos:  # o modelo nao respeitou o formato: extrai por mencao
            escolhidos = [i for i in self.agentes if re.search(rf"\b{re.escape(i)}\b", texto)]

        validos = [i for i in escolhidos if i in self.agentes and i != quadro.ORQUESTRADOR]
        return validos[:maximo] or [i for i in self.agentes if i != quadro.ORQUESTRADOR][:maximo]

    def atender(self, demanda: str, *, projeto: str = "", maximo: int = 6) -> ResultadoFluxo:
        """Modo automatico: o diretor triagem, delega e consolida."""
        self._log("\n>> Diretoria fazendo a triagem da demanda...")
        escolhidos = self.triagem(demanda, maximo=maximo)
        self._log(f"   Equipe escalada: {', '.join(escolhidos)}")

        etapas = [
            Etapa(
                agente=ident,
                instrucao=(
                    "Atenda esta demanda na sua area de responsabilidade. Entregue trabalho "
                    "pronto, no formato de entrega definido para o seu cargo."
                ),
                rotulo=f"Atuacao de {ident}",
            )
            for ident in escolhidos
        ]
        fluxo = Fluxo(
            nome="Atendimento de demanda",
            descricao="Triagem automatica pela diretoria",
            etapas=etapas,
        )
        return self.executar_fluxo(fluxo, demanda, projeto=projeto)

    # ------------------------------------------------------------------
    # Saida
    # ------------------------------------------------------------------
    def salvar(self, resultado: ResultadoFluxo, destino: str | Path | None = None) -> dict[str, Path]:
        """Grava relatorio, JSON e o trafego do barramento.

        Sem `destino`, usa o workspace configurado - nao um "workspace"
        relativo ao diretorio atual. Painel, rotinas, API e demo chamam sem
        destino, e escreviam ao lado de onde o processo foi iniciado,
        ignorando MOVILI_WORKSPACE e config/modelos.yaml.
        """
        pasta = Path(destino or self.config.workspace) / resultado.projeto
        pasta.mkdir(parents=True, exist_ok=True)
        md = pasta / "relatorio.md"
        js = pasta / "resultado.json"
        conversas = pasta / "conversas.json"
        md.write_text(resultado.markdown(), encoding="utf-8")
        js.write_text(json.dumps(resultado.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        self.barramento.exportar(conversas)
        caminhos = {"relatorio": md, "resultado": js, "conversas": conversas}

        cofre = self.cofre()
        if cofre is not None:
            try:
                caminhos["obsidian"] = cofre.exportar(resultado.to_dict())
            except OSError as exc:  # cofre sincronizado travado, disco cheio: o relatorio ja saiu
                self._log(f"   (nao foi possivel gravar no cofre do Obsidian: {exc})")
        return caminhos

    def cofre(self) -> CofreObsidian | None:
        """O cofre do Obsidian configurado, ou None se estiver desligado."""
        if not self.config.obsidian:
            return None
        return CofreObsidian(self.config.obsidian, fichas=_ficha_do_quadro)

    def metricas(self) -> dict[str, dict[str, int]]:
        return dict(self.roteador.metricas)

    def encerrar(self) -> None:
        if self.memoria is not None:
            self.memoria.fechar()
        if self.semantica is not None:
            self.semantica.fechar()
