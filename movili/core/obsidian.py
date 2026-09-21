"""Cofre do Obsidian: a memoria da empresa em notas que o usuario le e edita.

Dois sentidos:

- exportar: cada projeto vira uma nota com links para as entregas de cada
  funcionario, e cada funcionario tem a sua ficha. No grafo do Obsidian da
  para ver quem trabalhou em que e quais projetos se parecem.
- indexar: as notas que o USUARIO escreve (precos, clientes, padroes da casa,
  contratos modelo) entram na memoria semantica e passam a ser consultadas
  pelos agentes durante o trabalho.

O cofre e so uma pasta de arquivos .md - nao precisa de plugin nem de API do
Obsidian. O que a empresa gera fica em PASTA_GERADA; o resto e do usuario e
nunca e sobrescrito.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

# Tudo que o ecossistema escreve fica aqui dentro. Fora dela, as notas sao do
# usuario. A separacao evita indexar de novo o que ja esta na memoria (as
# entregas entram no indice no momento em que sao produzidas).
PASTA_GERADA = "Movili"

# Pastas que o proprio Obsidian (ou o sistema) cria e que nao sao notas.
IGNORAR = {".obsidian", ".trash", ".git"}

ORIGEM_NOTA = "nota"

# Caracteres que o Windows nao aceita em nome de arquivo, mais os que quebram
# link do Obsidian ([[...]], # de cabecalho, ^ de bloco, | de apelido).
_PROIBIDOS = re.compile(r'[\\/:*?"<>|#^\[\]]+')


def nome_de_arquivo(texto: str, limite: int = 90) -> str:
    """Nome seguro para arquivo e para [[link]] do Obsidian."""
    limpo = _PROIBIDOS.sub(" ", texto)
    limpo = re.sub(r"\s+", " ", limpo).strip(" .")
    return limpo[:limite].rstrip(" .") or "sem-titulo"


def _frontmatter(dados: dict[str, Any]) -> str:
    """Cabecalho YAML das notas.

    Cada valor sai como JSON, que e YAML valido: aspas, dois-pontos e quebras
    de linha dentro do valor ficam escapados sem precisar do PyYAML.
    """
    linhas = ["---"]
    for chave, valor in dados.items():
        linhas.append(f"{chave}: {json.dumps(valor, ensure_ascii=False)}")
    linhas.append("---")
    return "\n".join(linhas)


def _citar(texto: str) -> str:
    return "\n".join(f"> {linha}" if linha else ">" for linha in texto.splitlines())


@dataclass
class Ficha:
    """O que o cofre precisa saber de um funcionario."""

    id: str
    nome: str
    cargo: str
    setor: str = ""
    missao: str = ""


class CofreObsidian:
    """Le e escreve no cofre do Obsidian."""

    def __init__(self, raiz: str | Path, fichas: Callable[[str], Ficha | None] | None = None) -> None:
        self.raiz = Path(raiz)
        self._fichas = fichas or (lambda _ident: None)

    # ------------------------------------------------------------------
    # Estrutura
    # ------------------------------------------------------------------
    @property
    def gerada(self) -> Path:
        return self.raiz / PASTA_GERADA

    def preparar(self) -> None:
        """Cria o cofre com a nota de boas-vindas, se ainda nao existir."""
        for pasta in (self.raiz / "Conhecimento", self.gerada / "Projetos",
                      self.gerada / "Entregas", self.gerada / "Equipe"):
            pasta.mkdir(parents=True, exist_ok=True)
        inicio = self.raiz / "Inicio.md"
        if not inicio.exists():
            inicio.write_text(NOTA_INICIO, encoding="utf-8")

    def notas_do_usuario(self) -> list[Path]:
        """Notas .md escritas pelo usuario (fora da pasta gerada), em ordem."""
        if not self.raiz.is_dir():
            return []
        achadas = []
        for caminho in self.raiz.rglob("*.md"):
            partes = caminho.relative_to(self.raiz).parts
            if partes[0] == PASTA_GERADA or any(p in IGNORAR for p in partes):
                continue
            achadas.append(caminho)
        return sorted(achadas)

    def referencia(self, caminho: Path) -> str:
        """Identificador estavel da nota no indice: caminho relativo ao cofre."""
        return caminho.relative_to(self.raiz).as_posix()

    # ------------------------------------------------------------------
    # Exportacao: empresa -> cofre
    # ------------------------------------------------------------------
    def exportar(self, resultado: dict[str, Any]) -> Path:
        """Grava um projeto (formato de ResultadoFluxo.to_dict) no cofre.

        Reexportar o mesmo projeto substitui as notas dele - elas sao geradas.
        Devolve o caminho da nota do projeto.
        """
        self.preparar()
        projeto = resultado.get("projeto") or "sem-projeto"
        nome_projeto = nome_de_arquivo(projeto)
        pasta_entregas = self.gerada / "Entregas" / nome_projeto
        pasta_entregas.mkdir(parents=True, exist_ok=True)
        for antiga in pasta_entregas.glob("*.md"):
            antiga.unlink()  # a etapa pode ter mudado de numero ou de autor

        fluxo = resultado.get("fluxo", "")
        data = (resultado.get("concluido_em") or resultado.get("iniciado_em") or "")[:10]
        # tag do Obsidian so aceita letra, numero, '-', '_' e '/'
        tag_fluxo = re.sub(r"[^a-z0-9_]+", "-", fluxo.lower()).strip("-")[:40].rstrip("-") or "avulso"

        links_entregas: list[str] = []
        participantes: list[str] = []
        for i, etapa in enumerate(resultado.get("etapas") or [], 1):
            ident = etapa.get("agente", "")
            nome = etapa.get("nome") or ident
            if nome not in participantes:
                participantes.append(nome)
            self._garantir_ficha(ident, nome, etapa.get("cargo", ""))

            titulo = nome_de_arquivo(f"{nome_projeto} - {i:02d} - {nome}")
            links_entregas.append(f"- [[{titulo}|{i:02d}. {nome}]] - {etapa.get('cargo', '')}")
            corpo = [
                _frontmatter({
                    "tipo": "entrega",
                    "projeto": projeto,
                    "agente": ident,
                    "cargo": etapa.get("cargo", ""),
                    "etapa": i,
                    "duracao_s": etapa.get("duracao_s", 0),
                    "data": data,
                    "tags": ["movili/entrega", f"agente/{ident}", f"fluxo/{tag_fluxo}"],
                }),
                "",
                f"# {i:02d}. {nome}",
                "",
                f"Projeto: [[{nome_projeto}]] · Autor: [[{nome_de_arquivo(nome)}]]",
                "",
                "## Tarefa",
                "",
                _citar(etapa.get("instrucao", "")),
                "",
                "## Entrega",
                "",
                etapa.get("entrega", ""),
                "",
            ]
            (pasta_entregas / f"{titulo}.md").write_text("\n".join(corpo), encoding="utf-8")

        corpo = [
            _frontmatter({
                "tipo": "projeto",
                "projeto": projeto,
                "fluxo": fluxo,
                "iniciado_em": resultado.get("iniciado_em", ""),
                "concluido_em": resultado.get("concluido_em", ""),
                "participantes": participantes,
                "tags": ["movili/projeto", f"fluxo/{tag_fluxo}"],
            }),
            "",
            f"# {projeto}",
            "",
            f"**Processo:** {fluxo}  ",
            f"**Data:** {data}",
            "",
            "## Briefing",
            "",
            resultado.get("briefing", ""),
            "",
            "## Entregas",
            "",
            *links_entregas,
            "",
        ]
        if resultado.get("consolidacao"):
            corpo += ["## Decisao da diretoria", "", resultado["consolidacao"], ""]
        nota = self.gerada / "Projetos" / f"{nome_projeto}.md"
        nota.write_text("\n".join(corpo), encoding="utf-8")
        return nota

    def exportar_workspace(self, workspace: str | Path) -> list[Path]:
        """Exporta todos os projetos ja salvos no workspace (resultado.json)."""
        notas = []
        for arquivo in sorted(Path(workspace).glob("*/resultado.json")):
            try:
                dados = json.loads(arquivo.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue  # arquivo truncado de uma execucao interrompida
            notas.append(self.exportar(dados))
        return notas

    def _garantir_ficha(self, ident: str, nome: str, cargo: str) -> None:
        """Cria a nota do funcionario uma unica vez - depois ela e do usuario."""
        nota = self.gerada / "Equipe" / f"{nome_de_arquivo(nome)}.md"
        if nota.exists():
            return
        ficha = self._fichas(ident) or Ficha(id=ident, nome=nome, cargo=cargo)
        corpo = [
            _frontmatter({
                "tipo": "funcionario",
                "agente": ficha.id,
                "cargo": ficha.cargo,
                "setor": ficha.setor,
                "tags": ["movili/equipe"],
            }),
            "",
            f"# {ficha.nome}",
            "",
            f"**Cargo:** {ficha.cargo}  ",
            f"**Setor:** {ficha.setor}",
            "",
        ]
        if ficha.missao:
            corpo += ["## Missao", "", ficha.missao, ""]
        corpo += [
            "## Entregas",
            "",
            "As entregas deste funcionario aparecem nos links de entrada desta nota.",
            "",
        ]
        nota.write_text("\n".join(corpo), encoding="utf-8")

    # ------------------------------------------------------------------
    # Indexacao: cofre -> memoria semantica
    # ------------------------------------------------------------------
    def indexar(self, semantica) -> dict[str, int]:
        """Leva as notas do usuario para a memoria semantica.

        So reindexa nota que mudou, e tira do indice nota que foi apagada ou
        renomeada - senao os agentes seguiriam citando um preco que o usuario
        ja corrigiu.
        """
        contagem = {"indexadas": 0, "iguais": 0, "removidas": 0, "trechos": 0}
        vistas: set[str] = set()
        for caminho in self.notas_do_usuario():
            referencia = self.referencia(caminho)
            vistas.add(referencia)
            texto = caminho.read_text(encoding="utf-8", errors="replace")
            trechos = semantica.indexar_se_mudou(
                f"# {caminho.stem}\n\n{texto}",
                origem=ORIGEM_NOTA,
                referencia=referencia,
                titulo=caminho.stem,
            )
            if trechos is None:
                contagem["iguais"] += 1
            else:
                contagem["indexadas"] += 1
                contagem["trechos"] += trechos

        for referencia in semantica.documentos(ORIGEM_NOTA):
            if referencia not in vistas:
                semantica.remover_documento(ORIGEM_NOTA, referencia)
                contagem["removidas"] += 1
        return contagem


NOTA_INICIO = """# Cofre da Movili

Este cofre e a memoria da Movili Tecnologia em notas que voce le e edita.

## Como funciona

- **Movili/** e escrita pela empresa. Cada projeto que os agentes executam vira uma
  nota em *Movili/Projetos*, com links para a entrega de cada funcionario em
  *Movili/Entregas* e para a ficha dele em *Movili/Equipe*. Abra o grafo (Ctrl+G)
  para ver quem trabalhou em que.
- **Conhecimento/** (e qualquer outra pasta fora de *Movili*) e sua. Escreva aqui
  o que a empresa precisa saber: tabela de precos, clientes, padroes tecnicos,
  contratos modelo, decisoes antigas. Depois rode:

      movili obsidian indexar

  e os agentes passam a consultar essas notas quando trabalham.

## Comandos

    movili obsidian status      # o que tem no cofre e o que ja esta na memoria
    movili obsidian exportar    # leva para ca os projetos ja salvos no workspace
    movili obsidian indexar     # leva as suas notas para a memoria da empresa

Os projetos novos entram aqui sozinhos, ao final de cada fluxo ou reuniao.
"""
