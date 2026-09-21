"""Cofre do Obsidian: projetos viram notas, notas do usuario viram memoria."""

from __future__ import annotations

import json
from pathlib import Path

from movili.core.obsidian import PASTA_GERADA, CofreObsidian, nome_de_arquivo
from movili.core.orquestrador import Etapa, Fluxo


def _rodar(eco, projeto="obs-teste"):
    fluxo = Fluxo(
        nome="Teste do cofre",
        descricao="duas etapas",
        etapas=[
            Etapa(agente="dev_backend", instrucao="Proponha a arquitetura."),
            Etapa(agente="financeiro", instrucao="Precifique.", usa_saida_de=["dev_backend"]),
        ],
    )
    return eco.executar_fluxo(fluxo, "app de logistica", projeto=projeto)


def test_nome_de_arquivo_remove_o_que_quebra_windows_e_links():
    assert nome_de_arquivo('a/b:c*d?"e<f>g|h#i^j[k]l') == "a b c d e f g h i j k l"
    assert nome_de_arquivo("   ...  ") == "sem-titulo"
    assert len(nome_de_arquivo("x" * 300)) == 90


def test_salvar_exporta_projeto_com_links(eco_pequeno):
    resultado = _rodar(eco_pequeno)
    caminhos = eco_pequeno.salvar(resultado)

    nota = caminhos["obsidian"]
    assert nota.is_file()
    texto = nota.read_text(encoding="utf-8")
    assert texto.startswith("---\ntipo: \"projeto\"")
    assert "[[obs-teste - 01 - Rafael Andrade|01. Rafael Andrade]]" in texto
    assert "## Decisao da diretoria" in texto  # o diretor consolidou

    raiz = Path(eco_pequeno.config.obsidian)
    entregas = sorted((raiz / PASTA_GERADA / "Entregas" / "obs-teste").glob("*.md"))
    assert [e.stem for e in entregas] == [
        "obs-teste - 01 - Rafael Andrade",
        "obs-teste - 02 - Patricia Souza",
    ]  # a consolidacao do diretor vai na nota do projeto, nao e etapa
    assert "Projeto: [[obs-teste]] · Autor: [[Rafael Andrade]]" in entregas[0].read_text(
        encoding="utf-8"
    )
    ficha = raiz / PASTA_GERADA / "Equipe" / "Rafael Andrade.md"
    assert "## Missao" in ficha.read_text(encoding="utf-8")
    assert (raiz / "Inicio.md").is_file()


def test_reexportar_substitui_entregas_mas_preserva_ficha_editada(eco_pequeno):
    eco_pequeno.salvar(_rodar(eco_pequeno))
    raiz = Path(eco_pequeno.config.obsidian)
    ficha = raiz / PASTA_GERADA / "Equipe" / "Rafael Andrade.md"
    ficha.write_text("anotacao do usuario", encoding="utf-8")
    sobra = raiz / PASTA_GERADA / "Entregas" / "obs-teste" / "obs-teste - 09 - Ninguem.md"
    sobra.write_text("etapa que nao existe mais", encoding="utf-8")

    eco_pequeno.salvar(_rodar(eco_pequeno))

    assert ficha.read_text(encoding="utf-8") == "anotacao do usuario"
    assert not sobra.exists()


def test_frontmatter_escapa_valores(tmp_path):
    cofre = CofreObsidian(tmp_path)
    nota = cofre.exportar({
        "projeto": "p1", "fluxo": "x", "briefing": 'cliente: "ACME"\nsegunda linha',
        "etapas": [], "consolidacao": "",
    })
    cabecalho = nota.read_text(encoding="utf-8").split("---")[1]
    for linha in cabecalho.strip().splitlines():
        chave, _, valor = linha.partition(": ")
        json.loads(valor)  # todo valor e JSON, portanto YAML valido


def test_sem_cofre_configurado_salvar_nao_escreve(eco_pequeno, tmp_path):
    eco_pequeno.config.obsidian = ""
    caminhos = eco_pequeno.salvar(_rodar(eco_pequeno))
    assert "obsidian" not in caminhos
    assert eco_pequeno.cofre() is None


def test_exportar_workspace_pula_json_quebrado(eco_pequeno):
    eco_pequeno.salvar(_rodar(eco_pequeno, "p-bom"))
    quebrado = Path(eco_pequeno.config.workspace) / "p-quebrado"
    quebrado.mkdir(parents=True)
    (quebrado / "resultado.json").write_text("{ truncado", encoding="utf-8")

    notas = eco_pequeno.cofre().exportar_workspace(eco_pequeno.config.workspace)
    assert [n.stem for n in notas] == ["p-bom"]


def test_indexar_so_notas_do_usuario_e_so_o_que_mudou(eco_pequeno):
    eco_pequeno.salvar(_rodar(eco_pequeno))  # gera notas em Movili/, que nao devem entrar
    cofre = eco_pequeno.cofre()
    precos = cofre.raiz / "Conhecimento" / "Precos.md"
    precos.write_text("Hora de desenvolvimento senior: R$ 180. Margem minima 35%.", encoding="utf-8")
    (cofre.raiz / ".obsidian").mkdir()
    (cofre.raiz / ".obsidian" / "lixo.md").write_text("config interna", encoding="utf-8")

    c = cofre.indexar(eco_pequeno.semantica)
    assert c["indexadas"] == 2  # Inicio.md e Precos.md
    assert set(eco_pequeno.semantica.documentos("nota")) == {"Inicio.md", "Conhecimento/Precos.md"}

    assert cofre.indexar(eco_pequeno.semantica)["iguais"] == 2

    precos.write_text("Hora de desenvolvimento senior: R$ 200.", encoding="utf-8")
    c = cofre.indexar(eco_pequeno.semantica)
    assert (c["indexadas"], c["iguais"]) == (1, 1)

    achados = eco_pequeno.semantica.buscar("hora de desenvolvimento senior", minimo=0.0)
    trechos = " ".join(a.trecho for a in achados)
    assert "R$ 200" in trechos and "R$ 180" not in trechos


def test_nota_apagada_sai_da_memoria(eco_pequeno):
    cofre = eco_pequeno.cofre()
    cofre.preparar()
    nota = cofre.raiz / "Conhecimento" / "cliente_x.md"
    nota.write_text("Cliente X paga em 60 dias.", encoding="utf-8")
    cofre.indexar(eco_pequeno.semantica)

    nota.unlink()
    c = cofre.indexar(eco_pequeno.semantica)
    assert c["removidas"] == 1
    achados = eco_pequeno.semantica.buscar("cliente x paga em 60 dias", minimo=0.0)
    assert all("60 dias" not in a.trecho for a in achados)


def test_limpar_memoria_forca_reindexar_notas(eco_pequeno):
    cofre = eco_pequeno.cofre()
    cofre.preparar()
    cofre.indexar(eco_pequeno.semantica)
    eco_pequeno.semantica.limpar()
    assert cofre.indexar(eco_pequeno.semantica)["indexadas"] == 1
