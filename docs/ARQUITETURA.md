# Arquitetura

O ecossistema tem quatro camadas. Cada uma só conhece a de baixo.

```
   CLI  ·  OpenJarvis (voz)  ·  Ponte OpenAI  ·  API REST
                        ↓
                  Orquestrador
        fluxos · reuniões · triagem · paralelismo
                        ↓
  Agente (persona) · Barramento · Memória · RAG · Ferramentas
                        ↓
          Roteador de LLM  →  Ollama · LM Studio · Simulado
```

---

## Camada de LLM (`movili/llm/`)

### `base.py`
Contratos comuns (`ProvedorLLM`, `Mensagem`, `Resposta`) e o transporte HTTP em
`urllib` da biblioteca padrão — **nenhuma dependência externa**. Traduz erro de rede,
HTTP e timeout em duas exceções com mensagem acionável: `LLMError` e `LLMIndisponivel`.

`limpar_raciocinio()` remove os blocos `<think>…</think>` do Qwen3 em modo reasoning,
inclusive bloco aberto sem fechar (nesse caso descarta o resto, para nunca vazar
raciocínio interno no relatório ou na fala do Jarvis).

### `ollama.py` e `lmstudio.py`
Dois provedores, duas APIs: `/api/chat` nativo do Ollama e `/v1/chat/completions`
compatível com OpenAI. Ambos normalizam para a mesma `Resposta`, com contagem de tokens.
O provedor do LM Studio serve para qualquer servidor compatível — vLLM, llama.cpp server,
text-generation-webui em modo OpenAI — bastando apontar a URL.

### `router.py`
Decide qual backend atende cada agente:

1. usa o backend preferido do agente (`config/modelos.yaml`);
2. se ele estiver fora do ar, cai para o próximo da ordem de fallback;
3. registra métricas de uso (chamadas e tokens) por agente.

Distingue os dois tipos de falha: `LLMIndisponivel` (backend fora do ar) troca de backend
imediatamente, sem repetir; `LLMError` (erro de resposta) tenta de novo com espera
crescente antes de desistir. Quando nada responde, a exceção final diz exatamente o que
subir — `ollama serve` ou Developer → Start Server.

O `ProvedorSimulado` existe para validar o encanamento sem GPU. Ele **não entra no
fallback automático** de propósito: só roda com `--backend simulado`, para nunca
mascarar um Ollama fora do ar com uma resposta falsa.

---

## Núcleo (`movili/core/`)

### `mensagem.py`
A unidade de comunicação: remetente, destinatário, assunto, conteúdo, **tipo**
(briefing, tarefa, entrega, pergunta, resposta, revisão, decisão, alerta, informe),
prioridade, **thread** e projeto. `responder()` preserva thread e projeto — é o que
mantém o fio de uma conversa entre várias áreas.

### `barramento.py`
Pub/sub thread-safe com histórico auditável. Agentes assinam o próprio id; `*` é
broadcast para a empresa toda (menos o remetente). Observadores veem todo o tráfego —
usado por log, auditoria e exportação. `exportar()` grava o histórico completo em JSON.

### `memoria.py`
Dois níveis. `MemoriaCurta` é a janela deslizante de turnos de um agente, injetada no
prompt. `MemoriaCorporativa` é o SQLite compartilhado: mensagens, conhecimento
chave-valor por escopo e entregáveis por projeto.

### `ferramentas.py`
Ferramentas sem depender de *function calling* nativo: o agente emite um bloco JSON e o
executor resolve. Funciona igual nos dois backends, com qualquer modelo aberto.

Duas decisões de segurança:
- **Sem `eval`.** `calcular()` percorre a AST e só aceita operadores aritméticos —
  `__import__('os').system('ls')` levanta `ValueError`.
- **Sandbox.** `salvar_arquivo` resolve o caminho e recusa qualquer coisa fora do
  workspace, incluindo `../`.

### `rag.py`
A memória semântica: o que faz a empresa lembrar do que já produziu.

**Fatiamento.** `fatiar()` quebra o texto em trechos de ~1200 caracteres com 150 de
sobreposição, cortando em fim de parágrafo, quebra de linha ou fim de frase — nessa
ordem de preferência, de trás para frente a partir do limite. A sobreposição evita
perder uma decisão que cai exatamente na emenda entre dois trechos.

**Busca.** Cosseno em Python puro sobre vetores guardados como JSON no mesmo SQLite.
Sem banco vetorial externo: para o volume de uma software house (milhares de trechos,
não milhões), uma varredura linear resolve em milissegundos e economiza uma dependência
de infraestrutura inteira. Se a base crescer a ponto de isso pesar, o ponto de troca é
só a função `buscar()`.

**Procedência.** Cada trecho guarda a assinatura `<backend>/<modelo>` que o produziu, e
a busca filtra por ela. Sem isso, trocar de modelo de embedding contamina o índice em
silêncio: o cosseno entre vetores de espaços diferentes retorna um número, e o número
não significa nada. `estatisticas()` reporta quantos trechos ficaram inativos por
mudança de procedência.

**Degradação.** `buscar()` devolve `[]` se o backend de embedding não responder — a
empresa segue trabalhando sem memória. `indexar()`, ao contrário, levanta
`LLMIndisponivel` dizendo qual `ollama pull` falta: indexar em silêncio sem gravar nada
seria pior do que falhar.

### `agente.py`
O `Perfil` é a ficha funcional (nome, cargo, missão, KPIs, estilo, formato de entrega,
temperatura, modelo). O `Agente` monta o prompt de sistema a partir dela **mais** o
contexto da empresa **mais** o diretório de colegas, e roda o loop de ferramentas.

O diretório de colegas é o que permite o handoff: o agente vê `@id: Nome, Cargo` de todo
mundo e pode escrever `@colega {pedido}` no fim da entrega.

### `orquestrador.py`
O `Ecossistema` monta a empresa inteira e oferece cinco modos:

| Modo | O que faz |
|---|---|
| `delegar` | um agente, uma tarefa, ida e volta registradas no barramento |
| `em_paralelo` | vários agentes ao mesmo tempo (2–3 é o útil com um backend local) |
| `executar_fluxo` | processo com ordem e dependência explícita entre etapas |
| `reuniao` | mesa redonda com N rodadas de debate e ata final |
| `atender` | triagem automática: a diretoria escolhe quem atua |

Antes de cada delegação, `_com_memoria()` consulta o índice semântico e injeta os
trechos relevantes de **outros** projetos no contexto (o projeto em andamento é
excluído: o que interessa é o que a empresa fez antes). Depois da entrega,
`_indexar()` devolve o resultado ao índice. Falha na indexação é registrada e
engolida — melhoria não pode derrubar entrega.

O contexto de cada etapa é montado por `_montar_contexto`: briefing original mais as
entregas das etapas declaradas em `usa_saida_de` (ou todas, se não declarar), truncadas
para caber na janela do modelo.

---

## OpenJarvis (`movili/jarvis/`)

### `conversa.py`
Interpreta a intenção **por regra primeiro**, gastando modelo só quando precisa. A ordem
importa:

1. `@id` explícito;
2. chamada com verbo ("chama a Patricia", "fala com o jurídico");
3. reunião;
4. fluxo por palavra-chave;
5. menção solta — só por nome próprio, ou por id que não seja palavra comum.

O passo 5 vem depois de 3 e 4 de propósito: vários ids são palavras do dia a dia
(`produto`, `design`, `dados`), e "quero uma campanha para o produto novo" não é um
pedido para falar com a Product Manager.

Toda resposta injeta o estilo falado: N frases curtas, sem markdown, sem lista numerada.
Entregas longas passam por `_resumir_para_voz`, que começa pela conclusão e avisa que o
relatório completo ficou no workspace.

### `voz.py`
Motores detectados em tempo de execução, com degradação em cascata:

| Camada | 1ª opção | 2ª opção | Fallback |
|---|---|---|---|
| TTS | `piper` | `say` / `espeak-ng` | imprime na tela |
| STT | `faster-whisper` | `whisper.cpp` | teclado |

Nenhum é obrigatório. Falha de um motor no meio da execução cai para texto em vez de
derrubar a sessão.

### `ponte.py`
Servidor HTTP em `http.server` da biblioteca padrão que fala o protocolo
`/v1/chat/completions`. Cada agente vira um "modelo" (`movili-financeiro`,
`movili-seguranca`, …), mais `movili-jarvis` (roteia sozinho) e `movili-empresa`
(triagem completa).

Isso inverte a relação usual: em vez de o ecossistema consumir um modelo, **qualquer
cliente de modelo passa a consumir o ecossistema** — um app de voz, o LM Studio, uma
instalação externa do OpenJarvis ou qualquer integração que já fale OpenAI.

### Ordem de importação

`movili.agentes` importa `movili.core.agente`, e `movili.core.orquestrador` importa
`movili.agentes` de volta. O ciclo é tolerável **desde que nada de `movili.agentes`
seja avaliado em tempo de import** dentro do orquestrador — senão o módulo ainda está
pela metade quando o valor é lido.

Por isso os defaults de "quem coordena" (`Fluxo.consolidador`, `delegar(remetente=…)`,
`reuniao(mediador=…)`) guardam a sentinela `PADRAO` e só viram `quadro.ORQUESTRADOR`
quando são usados. `tests/test_importacao.py` importa o pacote em nove ordens
diferentes, cada uma num interpretador limpo — é a única forma de pegar ciclo de
import antes do usuário.

---

## Configuração (`movili/config.py`)

Três níveis, o de baixo sobrescreve o de cima:

1. `config/empresa.yaml` e `config/modelos.yaml`;
2. perfil de hardware (`--perfil especializado`);
3. variáveis de ambiente e flags de CLI (`--backend`, `--modelo`).

---

## Por que não usamos um framework de agentes

O ecossistema não usa LangChain, CrewAI ou AutoGen. Três motivos:

1. **Dependência.** O núcleo roda com PyYAML e nada mais. Um framework de agentes traz
   dezenas de pacotes transitivos para resolver um problema que aqui cabe em `urllib`.
2. **Controle do prompt.** A persona é o produto deste projeto. Camada de abstração em
   cima do prompt significa não saber exatamente o que o modelo recebeu.
3. **Modelos abertos.** Vários frameworks assumem function calling nativo confiável.
   Com modelos abertos de 8b a 14b isso é irregular; o protocolo de bloco JSON funciona
   em todos.
