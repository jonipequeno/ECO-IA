"""Painel web: ver a Movili trabalhando em tempo real.

A pagina principal e a Rede Movili: a empresa como uma rede neural viva, com
o trafego do barramento correndo pelas sinapses (kit em web/rede-movili/,
dados em painel/rede.py). A pagina anterior - organograma, feed completo das
mensagens e disparo de fluxos e reunioes - segue em /classico.

Usa apenas a biblioteca padrao - nenhuma dependencia nova, mesma escolha da
ponte do OpenJarvis.
"""

from __future__ import annotations

import json
import mimetypes
import queue
import threading
import time
import traceback
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from .. import agentes as quadro
from .. import fluxos as processos
from ..core.mensagem import Mensagem
from ..core.orquestrador import Ecossistema
from ..llm.base import LLMIndisponivel
from ..rotinas.agenda import Agenda
from . import rede

WEB = Path(__file__).parent / "web"
KIT = WEB / "rede-movili"
LIMITE_CORPO = 512 * 1024
MAX_EVENTOS = 400          # historico mantido para quem abre o painel depois
MAX_FILA_CLIENTE = 500     # eventos enfileirados por aba aberta
MAX_EVENTOS_REDE = 1000    # o que uma aba que caiu consegue recuperar ao voltar
BATIMENTO_REDE = 15        # segundos entre comentarios de heartbeat no SSE da rede
ENCERRANDO = {"evento": "encerrando"}
TIPOS_KIT = {
    ".js": "application/javascript", ".css": "text/css", ".json": "application/json",
    ".html": "text/html", ".md": "text/markdown", ".ts": "text/plain",
    ".woff2": "font/woff2", ".woff": "font/woff", ".svg": "image/svg+xml",
}


class TarefaInvalida(ValueError):
    """Pedido malformado que chegou ate o worker. Erro esperado, nao um bug."""


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class Tarefa:
    """Um trabalho disparado pelo painel."""

    id: str
    tipo: str
    descricao: str
    estado: str = "na fila"          # na fila | executando | concluida | erro
    criada_em: str = field(default_factory=_agora)
    concluida_em: str = ""
    projeto: str = ""
    erro: str = ""
    resultado: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "tipo": self.tipo, "descricao": self.descricao,
            "estado": self.estado, "criada_em": self.criada_em,
            "concluida_em": self.concluida_em, "projeto": self.projeto,
            "erro": self.erro,
        }


class Central:
    """Estado compartilhado do painel: eventos, assinantes e fila de trabalho.

    Um unico worker executa as tarefas em serie, de proposito: com um backend
    local, disparar tres fluxos ao mesmo tempo so enfileira no servidor de
    modelo e deixa tudo mais lento.
    """

    def __init__(self, eco: Ecossistema) -> None:
        self.eco = eco
        self.eventos: list[dict[str, Any]] = []
        self.tarefas: dict[str, Tarefa] = {}
        self.ordem_tarefas: list[str] = []
        self._assinantes: list[queue.Queue] = []
        self._lock = threading.RLock()
        self._fila: queue.Queue[str | None] = queue.Queue()
        self._encerrando = False
        # Fluxo da Rede Movili: separado do /api/eventos porque tem id
        # incremental (Last-Event-ID) e so carrega o que a rede desenha.
        self._rede: deque[tuple[int, dict[str, Any]]] = deque(maxlen=MAX_EVENTOS_REDE)
        self._seq_rede = 0
        self._assinantes_rede: list[queue.Queue] = []
        # Aba que disparou a tarefa em execucao: ela ja acendeu a onda sozinha
        # ao enviar, entao ignora o estimulo que volta com o proprio id.
        self._cliente_atual: str | None = None
        self.pesos = rede.ArquivoPesos(Path(eco.config.caminho_db).parent / "rede-pesos.json")

        self._worker = threading.Thread(target=self._processar, daemon=True)
        self._worker.start()
        self.agenda = Agenda(eco)
        eco.barramento.observar(self._do_barramento)

    # --- eventos ------------------------------------------------------
    def _do_barramento(self, mensagem: Mensagem) -> None:
        convertido = rede.evento_da_mensagem(mensagem, self.eco.agentes)
        if convertido is not None:
            if convertido["acao"] == "estimular" and self._cliente_atual:
                convertido["cliente"] = self._cliente_atual
            self.emitir_rede(convertido)

        agente = self.eco.agentes.get(mensagem.remetente)
        self.emitir("mensagem", {
            "id": mensagem.id,
            "de": mensagem.remetente,
            "nome": agente.perfil.nome if agente else mensagem.remetente,
            "cargo": agente.perfil.cargo if agente else "",
            "para": mensagem.destinatario,
            "assunto": mensagem.assunto,
            "conteudo": mensagem.conteudo,
            "tipo": mensagem.tipo.value,
            "prioridade": mensagem.prioridade.value,
            "projeto": mensagem.projeto,
            "em": mensagem.criada_em,
        })

    def emitir(self, tipo: str, dados: dict[str, Any]) -> None:
        evento = {"evento": tipo, "em": _agora(), **dados}
        with self._lock:
            self.eventos.append(evento)
            del self.eventos[:-MAX_EVENTOS]
            assinantes = list(self._assinantes)
        for fila in assinantes:
            try:
                fila.put_nowait(evento)
            except queue.Full:
                pass  # aba lenta ou abandonada: perde evento, nao trava o servidor

    def assinar(self) -> queue.Queue:
        fila: queue.Queue = queue.Queue(maxsize=MAX_FILA_CLIENTE)
        with self._lock:
            self._assinantes.append(fila)
        return fila

    def desassinar(self, fila: queue.Queue) -> None:
        with self._lock:
            if fila in self._assinantes:
                self._assinantes.remove(fila)

    # --- rede ---------------------------------------------------------
    def emitir_rede(self, evento: dict[str, Any]) -> int:
        """Publica um evento da rede com id incremental. Devolve o id."""
        with self._lock:
            self._seq_rede += 1
            item = (self._seq_rede, evento)
            self._rede.append(item)
            assinantes = list(self._assinantes_rede)
        for fila in assinantes:
            try:
                fila.put_nowait(item)
            except queue.Full:
                pass
        return item[0]

    def assinar_rede(self, ultimo_id: int | None) -> queue.Queue:
        """Assina a rede. Com `ultimo_id`, reenvia o que a aba perdeu enquanto caiu.

        Sem ele (aba nova), nada do passado e reenviado: a tela nao recebe
        horario e poria o trafego antigo no agora da rede.
        """
        fila: queue.Queue = queue.Queue(maxsize=MAX_FILA_CLIENTE)
        with self._lock:
            if ultimo_id is not None:
                for item in self._rede:
                    if item[0] > ultimo_id:
                        try:
                            fila.put_nowait(item)
                        except queue.Full:
                            break
            self._assinantes_rede.append(fila)
        return fila

    def desassinar_rede(self, fila: queue.Queue) -> None:
        with self._lock:
            if fila in self._assinantes_rede:
                self._assinantes_rede.remove(fila)

    # --- tarefas ------------------------------------------------------
    def agendar(self, tipo: str, descricao: str, **extras: Any) -> Tarefa:
        if self._encerrando:
            raise TarefaInvalida("o painel esta encerrando e nao aceita novos trabalhos")
        tarefa = Tarefa(id=uuid.uuid4().hex[:10], tipo=tipo, descricao=descricao)
        tarefa.__dict__["extras"] = extras
        with self._lock:
            self.tarefas[tarefa.id] = tarefa
            self.ordem_tarefas.append(tarefa.id)
        self._fila.put(tarefa.id)
        self.emitir("tarefa", tarefa.to_dict())
        return tarefa

    def _processar(self) -> None:
        while True:
            tarefa_id = self._fila.get()
            if tarefa_id is None:      # sentinela de encerramento
                return
            tarefa = self.tarefas.get(tarefa_id)
            if tarefa is None:
                continue
            tarefa.estado = "executando"
            self.emitir("tarefa", tarefa.to_dict())
            self._cliente_atual = tarefa.__dict__.get("extras", {}).get("cliente")
            try:
                self._executar(tarefa)
                tarefa.estado = "concluida"
            except (LLMIndisponivel, TarefaInvalida) as exc:
                # Erros previstos: a mensagem ja diz o que houve, sem stack trace.
                tarefa.estado, tarefa.erro = "erro", str(exc)
            except Exception as exc:
                # Inesperado: o rastro vai para o log do servidor, senao nao ha
                # como depurar um worker que roda em segundo plano. Imprime
                # ANTES de marcar o estado: quem espera o "erro" (outra thread)
                # ja pode ler o log e nao achar o rastro ainda.
                traceback.print_exc()
                tarefa.erro = f"{type(exc).__name__}: {exc}"
                tarefa.estado = "erro"
            self._cliente_atual = None
            tarefa.concluida_em = _agora()
            self.emitir("tarefa", tarefa.to_dict())

    def _executar(self, tarefa: Tarefa) -> None:
        extras = tarefa.__dict__.get("extras", {})
        if tarefa.tipo == "agente":
            r = self.eco.delegar(extras["agente"], extras["texto"],
                                 projeto="painel", remetente="painel")
            tarefa.projeto = "painel"
            tarefa.resultado = {"entrega": r.entrega, "agente": r.agente}
            return

        # Fluxo, reuniao e triagem entram pela diretoria: e ela quem distribui
        # as etapas (o remetente padrao do delegar e o orquestrador).
        if tarefa.tipo in {"fluxo", "reuniao", "atender"}:
            self.emitir_rede({"acao": "estimular", "dados": {
                "no": quadro.ORQUESTRADOR, "texto": rede.resumir(extras.get("texto", "")),
            }})

        if tarefa.tipo == "fluxo":
            resultado = self.eco.executar_fluxo(
                processos.obter(extras["fluxo"]), extras["texto"]
            )
        elif tarefa.tipo == "reuniao":
            resultado = self.eco.reuniao(extras["texto"], rodadas=int(extras.get("rodadas", 2)))
        elif tarefa.tipo == "atender":
            resultado = self.eco.atender(extras["texto"])
        else:
            raise TarefaInvalida(f"tipo de tarefa desconhecido: {tarefa.tipo}")

        tarefa.projeto = resultado.projeto
        caminhos = self.eco.salvar(resultado)
        tarefa.resultado = {
            "consolidacao": resultado.consolidacao,
            "etapas": len(resultado.etapas),
            "relatorio": str(caminhos["relatorio"]),
        }

    def encerrar(self, timeout: float = 30.0) -> bool:
        """Para de aceitar trabalho e espera o que esta em andamento terminar.

        Precisa rodar ANTES de Ecossistema.encerrar(): o worker roda em outra
        thread e, se o SQLite fechar no meio de uma entrega, a tarefa morre com
        o banco ja fechado. Devolve False se o timeout estourou.
        """
        if self._encerrando:
            return not self._worker.is_alive()
        self._encerrando = True
        with self._lock:
            pendentes = [
                self.tarefas[i] for i in self.ordem_tarefas
                if self.tarefas[i].estado == "na fila"
            ]
        for tarefa in pendentes:
            tarefa.estado = "erro"
            tarefa.erro = "cancelada: o painel foi encerrado"
            tarefa.concluida_em = _agora()

        self._fila.put(None)
        self._worker.join(timeout=timeout)
        parou = not self._worker.is_alive()

        with self._lock:
            for fila in self._assinantes:
                try:
                    fila.put_nowait({"evento": "encerrando", "em": _agora()})
                except queue.Full:
                    pass
            self._assinantes.clear()
            for fila in self._assinantes_rede:
                try:
                    fila.put_nowait(ENCERRANDO)
                except queue.Full:
                    pass
            self._assinantes_rede.clear()
        return parou

    # --- leitura ------------------------------------------------------
    def estado(self) -> dict[str, Any]:
        perfis = quadro.todos_os_perfis()
        with self._lock:
            tarefas = [self.tarefas[i].to_dict() for i in self.ordem_tarefas[-30:]]
            eventos = list(self.eventos[-120:])
        return {
            "empresa": self.eco.config.empresa.get("nome", "Movili Tecnologia"),
            "setores": {
                setor: [
                    {"id": i, "nome": perfis[i].nome, "cargo": perfis[i].cargo,
                     "ativo": i in self.eco.agentes,
                     "modelo": (self.eco.config.modelo_do_agente(i)[1] or "-")}
                    for i in ids if i in perfis
                ]
                for setor, ids in quadro.SETORES.items()
            },
            "fluxos": [{"nome": n, "descricao": d, "etapas": q}
                       for n, d, q in processos.listar()],
            "memoria": self._memoria(),
            "rotinas": self._rotinas(),
            "metricas": self.eco.metricas(),
            "tarefas": tarefas,
            "eventos": eventos,
        }

    def _rotinas(self) -> list[dict[str, Any]]:
        """Proximos compromissos do calendario interno."""
        try:
            return [
                {
                    "id": r.id,
                    "nome": r.nome,
                    "quando": q.isoformat(timespec="minutes"),
                    "descricao": r.agendamento.descrever(),
                }
                for r, q in self.agenda.proximas(5)
            ]
        except Exception:
            return []   # a agenda e informativa aqui: nunca derruba o painel

    def _memoria(self) -> dict[str, Any]:
        if self.eco.semantica is None:
            return {"ligada": False}
        try:
            s = self.eco.semantica.estatisticas()
        except Exception:
            return {"ligada": False}
        return {"ligada": True, "trechos": s["trechos"],
                "projetos": len(s["projetos"]), "inativos": s["inativos"],
                "assinatura": self.eco.semantica.assinatura}

    def backends(self) -> dict[str, Any]:
        return self.eco.roteador.status()


class _Handler(BaseHTTPRequestHandler):
    central: Central
    server_version = "MoviliPainel/1.0"

    def log_message(self, formato: str, *args: Any) -> None:
        return

    # --- utilitarios --------------------------------------------------
    def _json(self, codigo: int, corpo: Any) -> None:
        dados = json.dumps(corpo, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(dados)))
        self.end_headers()
        self.wfile.write(dados)

    def _erro(self, codigo: int, mensagem: str) -> None:
        self._json(codigo, {"erro": mensagem})

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
    def do_GET(self) -> None:  # noqa: N802
        rota = self.path.split("?")[0].rstrip("/") or "/"
        if rota in {"/", "/index.html"}:
            self._pagina()
        elif rota in {"/classico", "/classico.html"}:
            self._pagina("classico.html")
        elif rota.startswith("/rede-movili/"):
            self._estatico(rota[len("/rede-movili/"):])
        elif rota == "/api/rede/topologia":
            eco = self.central.eco
            self._json(200, rede.topologia(lambda i: eco.config.modelo_do_agente(i)[1]))
        elif rota == "/api/rede/eventos":
            self._stream_rede()
        elif rota == "/api/rede/pesos":
            self._json(200, self.central.pesos.carregar(quadro.REGISTRO))
        elif rota == "/api/estado":
            self._json(200, self.central.estado())
        elif rota == "/api/backends":
            self._json(200, self.central.backends())
        elif rota == "/api/eventos":
            self._stream()
        elif rota.startswith("/api/tarefa/"):
            tarefa = self.central.tarefas.get(rota.rsplit("/", 1)[-1])
            if tarefa is None:
                self._erro(404, "tarefa nao encontrada")
            else:
                self._json(200, {**tarefa.to_dict(), "resultado": tarefa.resultado})
        else:
            self._erro(404, f"rota nao encontrada: {rota}")

    def do_POST(self) -> None:  # noqa: N802
        rota = self.path.split("?")[0].rstrip("/")
        if rota == "/api/rede/pesos":
            self._salvar_pesos()
            return
        if rota != "/api/executar":
            self._erro(404, f"rota nao encontrada: {self.path}")
            return
        corpo = self._corpo()
        if corpo is None:
            self._erro(400, "corpo JSON ausente ou invalido")
            return

        tipo = str(corpo.get("tipo") or "")
        texto = str(corpo.get("texto") or "").strip()
        if not texto:
            self._erro(400, "informe o texto da demanda")
            return
        cliente = str(corpo.get("cliente") or "")[:40] or None

        if tipo == "agente":
            agente = str(corpo.get("agente") or "")
            if agente not in self.central.eco:
                self._erro(400, f"agente '{agente}' nao esta ativo")
                return
            perfil = self.central.eco.agente(agente).perfil
            tarefa = self.central.agendar(
                "agente", f"{perfil.nome}: {texto[:60]}", agente=agente, texto=texto,
                cliente=cliente,
            )
        elif tipo == "fluxo":
            nome = str(corpo.get("fluxo") or "")
            if nome not in processos.REGISTRO:
                self._erro(400, f"fluxo '{nome}' nao existe")
                return
            tarefa = self.central.agendar("fluxo", f"{nome}: {texto[:60]}",
                                          fluxo=nome, texto=texto)
        elif tipo == "reuniao":
            rodadas = max(1, min(int(corpo.get("rodadas") or 2), 4))
            tarefa = self.central.agendar("reuniao", f"Reuniao: {texto[:60]}",
                                          texto=texto, rodadas=rodadas)
        elif tipo == "atender":
            tarefa = self.central.agendar("atender", f"Triagem: {texto[:60]}", texto=texto)
        else:
            self._erro(400, "tipo deve ser: agente, fluxo, reuniao ou atender")
            return

        self._json(202, tarefa.to_dict())

    def _salvar_pesos(self) -> None:
        """Recebe rede.pesos() do navegador (a cada 60 s e no pagehide, via sendBeacon)."""
        corpo = self._corpo()
        if corpo is None:
            self._erro(400, "corpo JSON ausente ou invalido")
            return
        try:
            pesos = rede.validar_pesos(corpo, quadro.REGISTRO)
        except ValueError as exc:
            self._erro(400, str(exc))
            return
        try:
            self.central.pesos.salvar(pesos)
        except OSError as exc:
            self._erro(500, f"nao foi possivel gravar os pesos: {exc}")
            return
        self._json(200, {"salvos": len(pesos)})

    # --- entrega ------------------------------------------------------
    def _pagina(self, nome: str = "index.html") -> None:
        arquivo = WEB / nome
        if not arquivo.is_file():
            self._erro(500, f"painel/web/{nome} nao encontrado no pacote")
            return
        dados = arquivo.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(dados)))
        self.end_headers()
        self.wfile.write(dados)

    def _estatico(self, relativo: str) -> None:
        """Serve um arquivo do kit Rede Movili, sem deixar sair da pasta dele."""
        raiz = KIT.resolve()
        try:
            alvo = (raiz / relativo).resolve()
            alvo.relative_to(raiz)
        except (ValueError, OSError):
            self._erro(404, "arquivo nao encontrado")
            return
        if not alvo.is_file():
            self._erro(404, "arquivo nao encontrado")
            return
        # No Windows o mimetypes le o registro, que as vezes diz text/plain
        # para .js - e o navegador recusa o script. Os tipos do kit sao fixos.
        tipo = TIPOS_KIT.get(alvo.suffix.lower()) or mimetypes.guess_type(alvo.name)[0] \
            or "application/octet-stream"
        if tipo.startswith("text/") or tipo in {"application/javascript", "application/json"}:
            tipo += "; charset=utf-8"
        dados = alvo.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(dados)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(dados)

    def _stream_rede(self) -> None:
        """SSE da Rede Movili: um evento JSON por mensagem, com id para retomar.

        O EventSource devolve o ultimo id recebido no cabecalho Last-Event-ID
        quando reconecta; o que a aba perdeu no intervalo e reenviado.
        """
        try:
            ultimo = int(self.headers.get("Last-Event-ID") or "")
        except ValueError:
            ultimo = None
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        fila = self.central.assinar_rede(ultimo)
        try:
            self.wfile.write(b"retry: 3000\n: conectado\n\n")
            self.wfile.flush()
            while True:
                try:
                    item = fila.get(timeout=BATIMENTO_REDE)
                except queue.Empty:
                    bloco = ": batimento\n\n"
                else:
                    if item is ENCERRANDO:
                        return
                    ident, evento = item
                    bloco = f"id: {ident}\ndata: {json.dumps(evento, ensure_ascii=False)}\n\n"
                self.wfile.write(bloco.encode("utf-8"))
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass  # aba fechada
        finally:
            self.central.desassinar_rede(fila)

    def _stream(self) -> None:
        """Server-Sent Events: o painel recebe cada mensagem do barramento."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        fila = self.central.assinar()
        try:
            while True:
                try:
                    evento = fila.get(timeout=20)
                    bloco = f"data: {json.dumps(evento, ensure_ascii=False)}\n\n"
                except queue.Empty:
                    bloco = ": ping\n\n"   # mantem a conexao viva atras de proxy
                self.wfile.write(bloco.encode("utf-8"))
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass  # aba fechada
        finally:
            self.central.desassinar(fila)


def servir(eco: Ecossistema, host: str = "127.0.0.1", porta: int = 8080) -> None:
    """Sobe o painel. Encerra com Ctrl+C."""
    central = Central(eco)
    _Handler.central = central
    servidor = ThreadingHTTPServer((host, porta), _Handler)
    servidor.daemon_threads = True
    print(
        f"\nPainel da Movili no ar em http://{host}:{porta}\n"
        f"  {len(eco.agentes)} funcionarios ativos | {len(processos.REGISTRO)} fluxos\n"
        f"  O trafego do barramento aparece ao vivo conforme os agentes trabalham.\n"
        f"\nCtrl+C para encerrar.\n"
    )
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nencerrando o painel...")
    finally:
        servidor.shutdown()
        servidor.server_close()
        # Espera o trabalho em andamento antes de devolver o controle a CLI,
        # que vai fechar o banco logo em seguida.
        if not central.encerrar():
            print("  (um trabalho ainda estava rodando e foi interrompido)")
