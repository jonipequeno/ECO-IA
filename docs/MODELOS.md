# Guia de modelos — qual usar para cada função

Este guia detalha as escolhas de modelo do ecossistema. A configuração viva fica em
`config/modelos.yaml`; use `movili modelos` para navegar pelo catálogo na CLI.

> **Sobre as tags.** Os nomes seguem o registro público do Ollama
> (<https://ollama.com/library>). Tags mudam com o tempo: o script de download pula
> o que não existir mais e avisa no fim, em vez de falhar. Se um modelo não baixar,
> confira a tag atual na biblioteca.

---

## 1. O padrão: por que `qwen3:8b`

É o modelo de fábrica de **todos os 20 agentes**, e o motivo é simples: ele é o melhor
equilíbrio entre quatro coisas que este ecossistema exige ao mesmo tempo.

| Requisito | Por que importa aqui |
|---|---|
| Português do Brasil natural | os agentes escrevem proposta, contrato, copy e ata |
| Seguir instrução longa | o prompt de sistema tem persona, KPIs, formato de entrega e diretório de colegas |
| Uso de ferramenta | o financeiro calcula, todos gravam entregáveis no workspace |
| Custo de execução | uma reunião de 3 rodadas com 8 agentes são 27 chamadas de modelo |

Em ~6 GB de RAM, ele roda em máquina comum e sustenta as quatro coisas. Modelos
menores quebram na terceira (uso de ferramenta); modelos maiores tornam uma reunião
inviável no notebook.

**Modo reasoning:** o Qwen3 emite blocos `<think>…</think>`. O ecossistema remove esses
blocos automaticamente (`movili/llm/base.py::limpar_raciocinio`) — o raciocínio não vaza
para o relatório nem para a resposta falada do Jarvis.

---

## 2. Onde trocar o padrão compensa

### Engenharia → modelo de código

Modelo generalista escreve código *plausível*; modelo de código escreve código que
compila. Para os três devs, a segurança e a analista de dados, a troca vale mais do que
qualquer outra do ecossistema.

| Agente | Modelo | Nota |
|---|---|---|
| `dev_backend` | `qwen3-coder:30b-a3b` | MoE com ~3b de parâmetros ativos: qualidade de modelo grande na velocidade de um pequeno. É o melhor aberto para trabalho agêntico com ferramenta. |
| `dev_frontend`, `dev_mobile` | `qwen2.5-coder:14b` | melhor custo-benefício absoluto em código real |
| `seguranca` | `qwen2.5-coder:14b` | precisa **ler** código e arquitetura pelo ângulo do atacante |
| `dados` | `qwen2.5-coder:14b` + `sqlcoder:15b` | modelagem dimensional; `sqlcoder` para SQL puro complexo |

### Financeiro → modelo de raciocínio

O financeiro abre memória de cálculo linha a linha. Modelo generalista erra aritmética
encadeada e "arredonda" premissa no meio da conta.

`deepseek-r1:14b` pensa passo a passo e mantém as premissas coerentes do começo ao fim.
Em 16 GB, `deepseek-r1:8b`. Alternativa de segunda opinião: `phi4:14b`.

### Copy, design e CS → modelo de escrita

`gemma3:12b` tem a prosa mais natural em português do Brasil entre os modelos abertos
médios. Para copy — onde o texto é o produto — isso vale mais do que pontuação em
benchmark de raciocínio. Em 27b (`gemma3:27b`) ganha nuance de marca, e o modelo também
lê imagem, útil para analisar criativo de anúncio.

### Prospecção → modelo de texto curto

`mistral-nemo:12b` é forte em e-mail curto e cadência comercial, justamente o formato
do SDR. Em modelo maior, o cold e-mail sai longo demais e perde taxa de resposta.

### Jurídico → modelo formal de contexto longo

`mistral-small:24b` sustenta texto jurídico longo e formal em português sem perder o fio
— o jurídico redige cláusula, não bullet point.

### Sócios, diretoria, produto e PMO → nuance de decisão

`qwen3:14b`. A diferença para o 8b aparece exatamente onde esses papéis trabalham:
arbitrar entre áreas que discordam, enxergar consequência de segunda ordem e sintetizar
dez entregas em uma decisão. Em workstation, `llama3.3:70b` nos sócios e no CEO.

---

## 3. Perfis de hardware

```bash
./scripts/baixar_modelos.sh especializado
movili fluxo novo-projeto "..." --perfil especializado
```

| Perfil | RAM/VRAM | Estratégia |
|---|---|---|
| `leve` | 8 GB | `qwen3:4b` na maioria, `qwen2.5-coder:7b` na engenharia, `gemma3:4b` no copy |
| `equilibrado` | 16 GB | `qwen3:8b` + `qwen2.5-coder:14b` + `deepseek-r1:8b` + `gemma3:12b` |
| `especializado` | 24–32 GB | o melhor modelo por função (seção 2) |
| `maximo` | 48 GB+ | `qwen3:32b`, `llama3.3:70b`, `qwen2.5-coder:32b`, `deepseek-r1:32b` |

Você também pode trocar caso a caso, sem perfil:

```bash
movili agente dev_backend "refatore o módulo de faturamento" --modelo qwen3-coder:30b-a3b
```

---

## 4. Catálogo por categoria

### Generalistas — estratégia, escrita, conversa

| Modelo | RAM | Usar para |
|---|---|---|
| `qwen3:0.6b` | ~1 GB | classificação e roteamento de mensagem |
| `qwen3:1.7b` | ~2 GB | resumo curto, triagem de caixa de entrada |
| `qwen3:4b` | ~3 GB | perfil leve: todos os agentes em 8 GB |
| **`qwen3:8b`** | ~6 GB | **padrão da casa** |
| `qwen3:14b` | ~10 GB | sócios, diretoria, produto, PMO, marketing, comercial |
| `qwen3:30b-a3b` | ~19 GB | MoE: qualidade alta com velocidade de pequeno, ótimo em CPU |
| `qwen3:32b` | ~20 GB | melhor generalista aberto que cabe em GPU de 24 GB |
| `gemma3:4b` / `12b` / `27b` | 3–17 GB | copy, design e CS; o 12b é o ponto ideal |
| `llama3.1:8b` | ~5 GB | alternativa com function calling nativo maduro |
| `llama3.2:3b` | ~2 GB | sumarização em lote |
| `llama3.3:70b` | ~43 GB | síntese executiva em workstation |
| `mistral-nemo:12b` | ~7 GB | prospecção, e-mail curto |
| `mistral-small:24b` | ~14 GB | jurídico, texto longo e formal |
| `phi4:14b` | ~9 GB | raciocínio lógico compacto |
| `granite3.3:8b` | ~5 GB | RAG corporativo, resposta ancorada em documento |

### Raciocínio — conta, análise, auditoria

| Modelo | RAM | Usar para |
|---|---|---|
| `deepseek-r1:8b` | ~5 GB | financeiro em 16 GB |
| **`deepseek-r1:14b`** | ~9 GB | **financeiro: memória de cálculo aberta** |
| `deepseek-r1:32b` | ~20 GB | auditoria de número, viabilidade complexa |
| `qwq:32b` | ~20 GB | problema lógico longo — lento, use quando a resposta importa mais que o tempo |

### Código

| Modelo | RAM | Usar para |
|---|---|---|
| `qwen2.5-coder:1.5b` | ~1 GB | autocomplete/FIM no editor — não use como agente |
| `qwen2.5-coder:7b` | ~5 GB | frontend e mobile em 16 GB |
| **`qwen2.5-coder:14b`** | ~9 GB | **melhor custo-benefício para os devs e SQL** |
| `qwen2.5-coder:32b` | ~20 GB | código de produção, revisão de arquitetura |
| **`qwen3-coder:30b-a3b`** | ~19 GB | **arquiteto backend: MoE rápido, forte em ferramenta** |
| `deepseek-coder-v2:16b` | ~9 GB | refatoração, linguagens menos comuns |
| `codegemma:7b` | ~5 GB | geração de trecho, conversão entre linguagens |
| `starcoder2:7b` | ~4 GB | base legada com muita linguagem diferente |
| `sqlcoder:15b` | ~9 GB | SQL puro complexo |

### Embeddings — memória da empresa

Estes não conversam: eles vetorizam texto para a busca semântica que faz os agentes
lembrarem de projetos anteriores. Sem um deles baixado, o ecossistema roda normalmente,
só sem memória entre execuções.

Trocar de modelo de embedding **invalida o índice existente** — vetores de modelos
diferentes não são comparáveis. O ecossistema detecta isso e avisa em
`movili memoria status`; reindexe com `movili memoria indexar --projeto <nome>`.

| Modelo | RAM | Usar para |
|---|---|---|
| **`nomic-embed-text`** | ~0.3 GB | **padrão: rápido, 8k de contexto, bom em português** |
| `mxbai-embed-large` | ~0.7 GB | mais precisão quando a base cresce |
| `bge-m3` | ~1.2 GB | multilíngue e busca híbrida (denso + esparso) |
| `all-minilm` | ~0.1 GB | protótipo e teste |

### Visão

| Modelo | RAM | Usar para |
|---|---|---|
| `llama3.2-vision:11b` | ~8 GB | design e marketing: mockup e criativo de anúncio |
| `llava:13b` | ~8 GB | descrição geral de imagem e print de tela |
| `minicpm-v:8b` | ~6 GB | OCR, leitura de nota e contrato escaneado |
| `moondream` | ~2 GB | triagem rápida de imagem |

### Leves — apoio e automação

| Modelo | RAM | Usar para |
|---|---|---|
| `llama3.2:1b` | ~1 GB | classificar prioridade de mensagem no barramento |
| `smollm2:1.7b` | ~1.5 GB | extrair campos estruturados de texto curto |
| `gemma3:1b` | ~1 GB | título e tag de thread |

---

## 5. LM Studio

O LM Studio usa ids com hífen (`qwen3-8b`) em vez de dois-pontos (`qwen3:8b`).
Confirme o id exato carregado no app:

```bash
movili status --backend lmstudio
```

Se o id diferir do configurado, ajuste `backends.lmstudio.modelo_padrao` em
`config/modelos.yaml` ou use `--modelo` na linha de comando.

Qualquer outro servidor compatível com `/v1/chat/completions` (vLLM, llama.cpp server,
text-generation-webui em modo OpenAI) funciona pelo mesmo provedor — basta apontar a URL:

```bash
MOVILI_LMSTUDIO_URL=http://192.168.0.20:8000/v1 movili status --backend lmstudio
```

---

## 6. Ajuste fino por agente

Cada ficha funcional em `movili/agentes/` define `temperatura` e `max_tokens` próprios.
A lógica é direta: quem precisa de precisão trabalha frio, quem precisa de criatividade
trabalha quente.

| Agente | Temperatura | Motivo |
|---|---|---|
| `financeiro` | 0.25 | conta não pode variar entre execuções |
| `juridico` | 0.25 | redação de cláusula é precisa |
| `seguranca`, `dados` | 0.30 | achado técnico é factual |
| `dev_backend` | 0.30 | arquitetura estável e reproduzível |
| `projetos` | 0.35 | cronograma é aritmética de dependência |
| `produto`, `dev_frontend`, `dev_mobile` | 0.40–0.45 | código e escopo com alguma folga |
| `marketing`, `prospeccao` | 0.70 | precisa gerar ângulos diferentes |
| `copy` | 0.85 | variação é o produto — três headlines distintas por entrega |
