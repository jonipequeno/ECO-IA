# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Idioma: tudo em português do Brasil

Esta é a convenção mais importante do repositório, e a que se perde primeiro por hábito.

**Português em tudo**: nomes de classes, funções, variáveis, parâmetros, docstrings,
comentários, mensagens de erro, saída de CLI, textos de teste, README, docs e mensagens de
commit. `Barramento`, não `Bus`. `executar_fluxo`, não `run_flow`. `remetente`, não `sender`.

**Acentuação segue o tipo de arquivo**, e a regra é absoluta nos dois sentidos:

| Onde | Acento | Abrange |
|---|---|---|
| `.py` e `.yaml` | **nunca** | identificadores, docstrings, comentários, prompts dos agentes, saída de CLI, `config/` |
| `.md` e o HTML do painel | **sempre** | README, `docs/`, texto renderizado ao usuário |

Ou seja: `memoria`, `execucao`, `duracao_s`, e também `"Responda SEMPRE em portugues do
Brasil"` dentro de um prompt e `print("Relatorio: ...")` numa saída. Medido sobre a árvore
inteira: zero linhas acentuadas em `.py` e `.yaml`; 35–43% no README e em `docs/`. Misturar
as duas formas quebra busca e consistência.

**Única exceção**: regex que casa fala do usuário precisa das letras acentuadas — veja
`PADRAO_CHAMADA` em `movili/jarvis/conversa.py`, que reconhece "chama a **Patrícia**". Isso
é dado de entrada, não texto do projeto. Traço longo (`—`) em saída ao usuário é estilo, não
acento, e já é usado no código.

Inglês só onde o protocolo externo exige: `role`/`content` do formato de chat,
`do_GET`/`do_POST` da `http.server`, `model`/`messages`/`choices` da API compatível com
OpenAI.

---

## Comandos

```bash
python -m pytest tests -q                          # suíte completa (~227 testes)
python -m pytest tests/test_rotinas.py -q          # um arquivo
python -m pytest tests/test_rag.py::test_indexar_e_recuperar -q   # um teste
python -m pytest tests -q -k "curinga or catch_up" # por nome

python scripts/verificar.py                        # diagnóstico: estrutura, backends, modelos faltando
python -m movili status                            # backends e roteamento (sai com 1 se nenhum backend real no ar)
python -m movili --backend simulado demo           # passeio de ponta a ponta; teste de fumaça
make ajuda                                         # todos os atalhos
```

Não há linter configurado. `pyproject.toml` declara `[tool.ruff] line-length = 100` como
alvo de estilo, mas o ruff não está instalado nem roda em CI (não há CI neste repositório).

**Os testes rodam inteiramente no backend `simulado`** — sem GPU, sem modelo baixado, sem
rede. Qualquer teste novo precisa manter isso: use as fixtures `eco` / `eco_pequeno` do
`tests/conftest.py`, que já forçam `backend_forcado="simulado"` e um banco em `tmp_path`.

Para exercitar a CLI à mão sem modelo:

```bash
python -m movili --backend simulado fluxo prospeccao "briefing de teste"
```

---

## Arquitetura

Quatro camadas; cada uma só conhece a de baixo.

```
CLI · Painel web · OpenJarvis (voz) · Ponte OpenAI · API REST
                        ↓
                  Orquestrador  (fluxos, reuniões, triagem)
                        ↓
   Agente (persona) · Barramento · Memória · RAG · Ferramentas
                        ↓
        Roteador de LLM → Ollama · LM Studio · Simulado
```

**`movili/agentes/`** é o organograma: um arquivo por funcionário, cada um exportando `ID`
e uma função `perfil()` que devolve um `Perfil`. O `__init__.py` é a fonte única de verdade
— `REGISTRO`, `SETORES`, `ORQUESTRADOR`, `CONSELHO`. Orquestrador, CLI, painel, ponte e
triagem automática leem daqui.

**`movili/core/orquestrador.py`** é o centro. `Ecossistema` monta a empresa inteira e
oferece cinco modos: `delegar` (um agente), `em_paralelo`, `executar_fluxo` (etapas com
dependência declarada em `usa_saida_de`), `reuniao` (rodadas de debate com ata final) e
`atender` (o CEO faz a triagem e escala o time).

**O barramento é o que faz o ecossistema conversar.** Não é uma fila linear de chamadas:
agentes publicam e assinam tópicos, e podem se acionar no meio da própria entrega
escrevendo `@colega {pedido}` — `Agente.handoffs()` extrai, o orquestrador despacha, até 2
níveis de profundidade.

`docs/ARQUITETURA.md` detalha cada camada e o porquê de cada escolha.

---

## Armadilhas específicas deste repositório

Cada uma destas já causou um bug real aqui. Os testes que as cobrem citam o motivo.

### Ciclo de importação entre `core` e `agentes`

`movili.agentes` importa `movili.core.agente`, o que dispara `movili/core/__init__.py`, que
importa `movili.core.orquestrador`, que importa `movili.agentes` de volta. O ciclo só é
tolerável porque **nada de `movili.agentes` é avaliado em tempo de import** dentro do
orquestrador.

Por isso os defaults de "quem coordena" (`Fluxo.consolidador`, `delegar(remetente=)`,
`reuniao(mediador=)`) guardam a sentinela `PADRAO` e só viram `quadro.ORQUESTRADOR` quando
usados. **Nunca use `quadro.X` como valor padrão de parâmetro ou de campo de dataclass em
`orquestrador.py`.** `tests/test_importacao.py` importa o pacote em nove ordens diferentes,
cada uma em subprocess — é a única forma de pegar esse ciclo.

### O backend `simulado` nunca entra no fallback automático

Ele existe para validar o encanamento sem GPU e só roda se pedido explicitamente
(`--backend simulado`). Colocá-lo em `ordem_fallback` mascararia um Ollama fora do ar com
uma resposta falsa. As respostas dele vêm marcadas como `[RESPOSTA SIMULADA]` de propósito.

Sua vetorização é **hashing léxico, não semântico** — serve para exercitar o RAG, não para
avaliar qualidade de busca. A escala de similaridade dele não é a do modelo real; testes que
dependem de limiar devem fixá-lo explicitamente.

### Vetores de modelos diferentes não são comparáveis

`MemoriaSemantica` grava a assinatura `<backend>/<modelo>` de cada trecho e a busca filtra
por ela. Cosseno entre espaços vetoriais diferentes devolve um número que não significa
nada. Ao mexer no RAG, preserve esse filtro.

Referências no índice passam por `_padrao_de_referencia()`, que escapa `%`, `_` e a barra
de escape antes do `LIKE`. Sem isso, indexar `docs/a_b.md` apaga silenciosamente os trechos
de `docs/aXb.md`.

### Flags globais da CLI precisam vir antes do subcomando

`argparse` não aceita opção do parser principal depois do subcomando. `movili --projeto X
fluxo ...` funciona; `movili fluxo ... --projeto X` não. Quando um subcomando precisa da
mesma opção nas duas posições, ele declara a própria cópia com `dest` distinto — veja
`--projeto`/`projeto_memoria` em `cmd_memoria`. Um `dest` igual com default `None` apagaria
o valor global.

### Servidores precisam de encerramento ordenado

Painel (`movili/painel/`) e agenda (`movili/rotinas/agenda.py`) rodam trabalho em outra
thread enquanto a CLI fecha o SQLite no `finally`. Ambos param o trabalho **antes** de
devolver o controle: `Central.encerrar()` e `Agenda.parar()`. A espera usa
`threading.Event.wait()`, não `sleep()`, para acordar na hora.

### Filas sem leitor precisam de teto

`Barramento._caixas` e `Agente._pendentes` acumulam mensagens que ninguém lê no fluxo normal
(os agentes recebem por callback). São `deque` com `maxlen` justamente por isso — o painel
roda por horas. Não troque por lista.

### Erro previsto não imprime traceback

No painel, `TarefaInvalida` termina a tarefa com mensagem limpa; só exceção inesperada
deixa rastro no log. Log cheio de traceback de erro esperado é log que ninguém lê.

---

## Dependências: o núcleo não tem

A única dependência obrigatória é **PyYAML** (e mesmo ela é importada com fallback para
JSON em `config.py`). Toda a camada HTTP — clientes de LLM, ponte OpenAI, painel web — usa
`urllib` e `http.server` da biblioteca padrão.

`fastapi` e `pydantic` aparecem **apenas** em `movili/api/`, e são importados lá dentro.
Os motores de voz (`piper`, `faster-whisper`, `sounddevice`) são detectados em tempo de
execução e degradam para texto/teclado quando ausentes.

Antes de adicionar qualquer dependência, verifique se a stdlib resolve. O painel usa SSE em
vez de WebSocket exatamente por isso.

---

## Adicionar coisas

**Um funcionário novo** — quatro passos, e os testes de estrutura cobrem cada um:

1. `movili/agentes/<id>.py` com `ID` e `perfil()`; copie a estrutura de uma ficha existente
   (missão, especialidades, responsabilidades, KPIs, estilo, `formato_entrega`).
2. Registre em `movili/agentes/__init__.py`: importe o módulo, acrescente a `_MODULOS` na
   posição do organograma e inclua o id em `SETORES`.
3. Acrescente a regra em `config/modelos.yaml → roteamento` e nos `perfis_hardware`.
4. Rode a suíte. `test_estrutura.py` valida nome próprio, missão, KPIs, cobertura dos
   setores e se os colegas citados em `interlocutores` existem; `test_config.py` valida que
   todo agente tem modelo configurado e que o perfil `especializado` cobre o quadro.

**Um fluxo novo** — `movili/fluxos/<nome>.py` com uma função `fluxo()`, registrado em
`fluxos/__init__.py`. `test_estrutura.py` garante que toda etapa aciona agente existente e
que nenhuma etapa depende de alguém que ainda não atuou.

**Uma rotina nova** — em `movili/rotinas/catalogo.py`. Tipos: `fluxo`, `reuniao`, `agente`,
`manutencao` (este último não gasta modelo de linguagem).

---

## Configuração

Três níveis, o de baixo sobrescreve o de cima:

1. `config/empresa.yaml` (contexto institucional que entra no prompt de todo agente,
   incluindo as "regras da casa", que têm efeito comportamental real) e
   `config/modelos.yaml` (backends, roteamento por agente, perfis de hardware, catálogo de
   44 modelos, embeddings).
2. Perfil de hardware: `--perfil leve|equilibrado|especializado|maximo`.
3. Variáveis de ambiente (`MOVILI_*`, veja `.env.example`) e flags de CLI.

O padrão de fábrica é `qwen3:8b` em todos os agentes. `docs/MODELOS.md` justifica cada
escolha de modelo por função.

---

## Git

Desenvolver e empurrar na branch `claude/sharp-mendel-icv9g3`. Mensagens de commit em
português, explicando **por que** e não só o quê — as deste repositório nomeiam os defeitos
encontrados durante o trabalho e a medição que os comprovou. Não criar PR sem pedido
explícito.
