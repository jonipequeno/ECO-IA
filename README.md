# ECO-IA — Ecossistema de Agentes da Movili Tecnologia

Uma **empresa de desenvolvimento de software inteira**, operada por 20 agentes de IA
que se comportam como funcionários seniores da Movili Tecnologia — e que **conversam
entre si**, discordam, se acionam e fecham entregas em conjunto.

Roda **100% local**, sem nuvem e sem chave de API, em **Ollama** e **LM Studio**.
Modelo padrão de fábrica: **`qwen3:8b`**.

```bash
./scripts/instalar.sh completo
ollama serve                                  # em outro terminal
./scripts/baixar_modelos.sh essenciais
movili status

movili fluxo novo-projeto "app de logística para transportadora com 80 caminhões"
movili reuniao "vale a pena entrar no mercado de saúde?" --rodadas 3
movili jarvis                                 # conversa por voz com a empresa
```

---

## Sumário

- [O quadro de funcionários](#o-quadro-de-funcionários)
- [Como eles conversam](#como-eles-conversam)
- [Processos internos (fluxos)](#processos-internos-fluxos)
- [Memória da empresa](#memória-da-empresa)
- [Rotinas: o calendário interno](#rotinas-o-calendário-interno)
- [Painel web](#painel-web)
- [OpenJarvis — a camada conversacional](#openjarvis--a-camada-conversacional)
- [Instalação](#instalação)
- [Modelos do Ollama: qual usar para quê](#modelos-do-ollama-qual-usar-para-quê)
- [Comandos](#comandos)
- [Configuração](#configuração)
- [Arquitetura](#arquitetura)
- [API HTTP](#api-http)
- [Docker](#docker)
- [Testes](#testes)

---

## O quadro de funcionários

20 agentes, cada um com nome próprio, cargo, missão, especialidades, KPIs e um
estilo de trabalho — inclusive o de discordar dos colegas quando tem base para isso.

### Conselho de sócios
| ID | Pessoa | Cargo |
|---|---|---|
| `socio_estrategia` | **Helena Vasconcelos** | Sócia-fundadora e Chief Strategy Officer |
| `socio_tecnologia` | **Gustavo Ribeiro** | Sócio-fundador e CTO |

### Diretoria
| ID | Pessoa | Cargo |
|---|---|---|
| `diretor` | **Ricardo Menezes** | CEO e Diretor de Operações — orquestra o ecossistema |

### Produto
| ID | Pessoa | Cargo |
|---|---|---|
| `produto` | **Juliana Prado** | Product Manager Sênior — decide **o quê** e por quê |
| `projetos` | **Vinicius Rocha** | Gerente de Projetos Sênior (PMO) — cuida do **como** e **quando** |
| `design` | **Felipe Moraes** | UX/UI Designer Sênior e guardião do design system |

### Engenharia (os três desenvolvedores)
| ID | Pessoa | Cargo |
|---|---|---|
| `dev_backend` | **Rafael Andrade** | Arquiteto de Software e Dev Backend Sênior |
| `dev_frontend` | **Camila Reis** | Desenvolvedora Frontend Sênior e UI Engineer |
| `dev_mobile` | **Bruno Tavares** | Dev Mobile Sênior, DevOps e QA |

### Marketing
| ID | Pessoa | Cargo |
|---|---|---|
| `marketing` | **Larissa Monteiro** | Head de Marketing |
| `seo` | **Diego Barros** | Especialista em SEO Sênior |
| `copy` | **Marina Duarte** | Copywriter Sênior e Content Strategist |

### Comercial
| ID | Pessoa | Cargo |
|---|---|---|
| `prospeccao` | **Thiago Nunes** | SDR Sênior e Especialista em Prospecção Outbound |
| `comercial` | **Eduardo Lima** | Executivo Comercial Sênior (Closer) |

### Apoio
| ID | Pessoa | Cargo |
|---|---|---|
| `financeiro` | **Patricia Souza** | Controller e Gerente Financeira Sênior |
| `juridico` | **Roberto Aguiar** | Advogado Sênior — Contratos, LGPD e Compliance |
| `seguranca` | **Daniel Okamoto** | Head de Segurança da Informação (CISO e AppSec) |
| `dados` | **Aline Ferraz** | Analista de Dados e BI Sênior |
| `rh` | **Sofia Nogueira** | Head de People e Cultura |
| `cs` | **Marcelo Brito** | Customer Success Manager Sênior |

```bash
movili equipe                        # organograma completo
movili equipe --detalhe financeiro   # ficha funcional de uma pessoa
```

---

## Como eles conversam

Não é uma fila de chamadas em sequência. Existe um **barramento de mensagens** —
o "Slack interno" da empresa — e quatro formas de interação:

**1. Handoff espontâneo.** Todo agente conhece os colegas e pode acioná-los no meio
da própria entrega, escrevendo `@colega {o que preciso}`. O orquestrador detecta,
despacha e devolve a resposta para a thread original.

```
Diego (SEO): ...fechei o mapa de palavras-chave.
             @copy {escreva os títulos das 5 páginas do cluster de logística}
             @dev_frontend {preciso de SSR nas páginas de cluster, CLS abaixo de 0.1}
```

**2. Fluxo de trabalho.** Um processo interno com ordem e dependência explícita:
cada etapa recebe as entregas de quem veio antes. Veja [Processos internos](#processos-internos-fluxos).

**3. Reunião.** Mesa redonda com várias rodadas. Na primeira, cada um traz a posição da
sua área; da segunda em diante cada um responde a quem citou sua área, diz onde discorda
e fecha com o compromisso que assume. O CEO encerra com a ata final.

```bash
movili reuniao "vamos migrar todos os clientes para squad mensal?" --rodadas 3
movili reuniao "revisão de segurança do trimestre" --setor engenharia
```

**4. Triagem automática.** Você joga uma demanda e a diretoria decide sozinha quem
precisa atuar, em que ordem, e consolida tudo numa decisão só.

```bash
movili atender "cliente quer integrar ERP com marketplace em 90 dias"
```

Toda conversa fica gravada: `workspace/<projeto>/conversas.json` tem o tráfego completo
do barramento, e `relatorio.md` tem as entregas em ordem.

---

## Processos internos (fluxos)

| Fluxo | Etapas | Quem atua, em ordem |
|---|---|---|
| `novo-projeto` | 12 | comercial → dev_backend → produto → segurança → design → frontend → mobile → **projetos** → rh → financeiro → jurídico → comercial |
| `produto-mvp` | 8 | produto → design → dev_backend → frontend → mobile → segurança → projetos → dados |
| `campanha` | 8 | marketing → seo → copy → design → frontend → dados → financeiro → comercial |
| `prospeccao` | 5 | prospecção → copy → jurídico → comercial → financeiro |
| `diagnostico` | 7 | dev_backend → mobile → dados → segurança → produto → jurídico → financeiro |
| `pos-venda` | 6 | cs → dados → produto → mobile → comercial → financeiro |
| `decisao-estrategica` | 6 | diretor → financeiro → marketing → comercial → **sócio CTO** → **sócia CSO** |

Todo fluxo termina com a consolidação do CEO, que resolve as contradições entre as áreas
em vez de só empilhar as entregas.

```bash
movili fluxos                                              # lista todos
movili fluxo campanha "lançamento do serviço de squad dedicada para e-commerce"
movili fluxo decisao-estrategica "abrir uma unidade de produto SaaS próprio"
```

---

## Memória da empresa

Sem memória, toda execução começa do zero: o financeiro reprecifica do nada um projeto
igual ao que a casa entregou mês passado. O ecossistema indexa cada entrega num índice
vetorial e recupera o trabalho anterior relevante antes de cada tarefa.

```bash
ollama pull nomic-embed-text      # é só isso; sem ele o resto roda igual

movili fluxo novo-projeto "app de roteirização para transportadora"
# ... semanas depois, outro cliente do mesmo setor:
movili fluxo novo-projeto "sistema de rastreamento de frota para distribuidora"
#   >> Patricia Souza (Controller e Gerente Financeira Senior) trabalhando...
#      (recuperou memoria de projetos anteriores)
```

O agente recebe os trechos com a procedência — quem escreveu, em que projeto, com que
relevância — e é instruído a dizer quando está reaproveitando uma decisão anterior.

```bash
movili memoria status
movili memoria buscar "precificação de projeto de logística" --limite 5
movili memoria buscar "cláusula de SLA" --agente juridico
movili memoria indexar --projeto frota-2026        # reindexa um projeto antigo
movili memoria indexar --arquivo docs/contrato-modelo.md
movili memoria limpar --projeto teste
```

**Como funciona:** cada entrega é fatiada em trechos de ~1200 caracteres com
sobreposição (cortando em fim de parágrafo quando dá), vetorizada e guardada no mesmo
SQLite. A busca é cosseno em Python puro — sem banco vetorial externo. O projeto em
andamento é excluído da busca: o que interessa é o que a empresa fez **antes**.

**Procedência dos vetores.** Cada trecho guarda qual backend e modelo o produziu, e a
busca só compara vetores da mesma procedência — cosseno entre espaços vetoriais
diferentes não significa nada. Se você trocar de modelo de embedding, `movili memoria
status` avisa quantos trechos ficaram invisíveis e você reindexa.

**Se degrada em vez de quebrar.** Sem o modelo de embedding baixado, a busca devolve
vazio e a empresa segue trabalhando sem memória. Indexar, aí sim, dá erro — dizendo
exatamente qual `ollama pull` falta.

Ajuste em `config/modelos.yaml → embeddings`, ou desligue com `MOVILI_EMBEDDINGS=0`.

---

## Rotinas: o calendário interno

Até aqui a empresa só trabalhava quando você mandava. As rotinas dão a ela um ritmo
próprio — daily, revisão de pipeline, fecho financeiro, conselho trimestral.

```bash
movili rotinas                          # o calendário de fábrica
movili rotinas proximas                 # o que vem por aí, e quando cada uma rodou
movili rotinas rodar --rotina daily     # dispara uma agora, fora de hora
movili rotinas agenda                   # deixa de pé, executando na hora marcada
```

| Rotina | Quando | O que faz |
|---|---|---|
| `daily` | seg–sex, 09:00 | produto e engenharia alinham avanço, bloqueio e risco de prazo |
| `pipeline` | segunda, 10:00 | comercial, prospecção, marketing e financeiro revisam o funil |
| `seguranca` | quarta, 14:00 | segurança e engenharia revisam exposição e o que vai a produção |
| `saude-financeira` | sexta, 16:00 | Patricia fecha a semana: margem, caixa e recebíveis em risco |
| `fechamento-mensal` | dia 1, 09:00 | diretoria fecha o mês contra a meta e ajusta o próximo |
| `conselho` | dia 1 de jan/abr/jul/out | os sócios revisam a tese da empresa |
| `higiene-memoria` | domingo, 03:00 | manutenção do índice semântico — **não gasta modelo** |

Edite `movili/rotinas/catalogo.py` para ajustar o ritmo à sua operação.

**A agenda sobrevive ao restart.** A última execução de cada rotina fica no SQLite, então
desligar a máquina não faz a daily rodar duas vezes.

**E não acumula fila.** Se a agenda ficou parada, os horários vencidos há mais de 6 horas
são marcados como pulados em vez de disparados — ligar a máquina depois de um mês fora não
despeja trinta dailies atrasadas. O acerto acontece numa passada só.

Os próximos cinco compromissos também aparecem no [painel web](#painel-web).

---

## Painel web

O terminal mostra uma linha por agente. O painel mostra a empresa **conversando**:
cada mensagem do barramento aparece no navegador no instante em que é publicada.

```bash
movili painel          # http://127.0.0.1:8080
```

Três colunas:

| Coluna | O que faz |
|---|---|
| **Equipe** | organograma por setor, com o modelo de cada pessoa; clique em alguém para falar direto |
| **Barramento ao vivo** | cada tarefa, entrega, pergunta e decisão conforme acontece, com tipo e remetente |
| **Dar trabalho à casa** | dispara triagem, fluxo, reunião ou pergunta a uma pessoa; acompanha a fila, os próximos compromissos e o uso de modelo |

O feed usa Server-Sent Events — sem polling, sem WebSocket, sem framework. O
servidor é `http.server` da biblioteca padrão, mesma escolha da ponte do OpenJarvis:
**nenhuma dependência nova**.

Os trabalhos entram numa fila com um único worker, de propósito: com um backend local,
disparar três fluxos ao mesmo tempo só enfileira no servidor de modelo e deixa tudo mais
lento. Ao encerrar com Ctrl+C, o painel espera o trabalho em andamento terminar antes de
devolver o controle — senão o banco fecharia no meio de uma entrega.

```bash
movili painel --host 0.0.0.0 --porta 8080    # acessível na rede local
```

> O painel não tem autenticação. Ele é uma ferramenta de trabalho local: exponha em
> `0.0.0.0` apenas em rede confiável.

---

## OpenJarvis — a camada conversacional

O **OpenJarvis** é a recepção falada do ecossistema. Ele entende o que você quer,
chama a pessoa certa da casa (ou a empresa inteira) e devolve a resposta em linguagem
falada, curta o bastante para ouvir.

```bash
movili jarvis --diagnostico    # mostra quais motores de voz estão instalados
movili jarvis                  # inicia a conversa
```

```
jarvis> Jarvis na escuta. A Movili tem 20 pessoas disponíveis agora.
você>   chama a Patrícia e pergunta a margem de um projeto de duzentos mil
jarvis> Patricia Souza responde: com custo de time em cento e oitenta por hora
        e mil e cem horas, a margem fica em quarenta e três por cento...
você>   convoca uma reunião sobre entrar no mercado de saúde
jarvis> [roda a reunião e resume a ata em voz]
```

**Motores de voz** — todos opcionais e detectados em tempo de execução. Sem nenhum
deles, o Jarvis funciona em modo texto:

| Camada | Preferência 1 | Preferência 2 | Fallback |
|---|---|---|---|
| Fala (TTS) | `piper` (voz neural pt-BR) | `say` / `espeak-ng` | imprime na tela |
| Escuta (STT) | `faster-whisper` | `whisper.cpp` | teclado |

```bash
pip install -r requirements-voz.txt
python -m piper.download_voices pt_BR-faber-medium
```

### Ponte OpenAI-compatível

O Jarvis também expõe a empresa como se fosse um servidor de modelos. Qualquer cliente
que já fala com Ollama, LM Studio ou OpenAI — inclusive uma instalação externa do
OpenJarvis, um app de voz no celular ou o próprio LM Studio — pode apontar para cá:

```bash
movili ponte                      # http://127.0.0.1:8123/v1
```

```bash
curl http://127.0.0.1:8123/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"movili-financeiro","messages":[{"role":"user","content":"qual a margem mínima?"}]}'
```

Cada agente vira um "modelo" selecionável:

| Modelo | O que faz |
|---|---|
| `movili-jarvis` | recepção: interpreta e roteia sozinha |
| `movili-empresa` | a diretoria escala o time todo e consolida |
| `movili-<agente>` | fala direto com um funcionário (`movili-seguranca`, `movili-copy`, …) |

> A ponte usa só a biblioteca padrão do Python — não precisa de FastAPI.

---

## Instalação

**Requisitos:** Python 3.10+ e pelo menos um backend local (Ollama ou LM Studio).

```bash
git clone https://github.com/jonipequeno/ECO-IA.git
cd ECO-IA
./scripts/instalar.sh completo     # cria .venv, instala tudo, prepara .env
source .venv/bin/activate
```

### Ollama

```bash
# instale em https://ollama.com/download
ollama serve                              # deixa rodando
./scripts/baixar_modelos.sh essenciais    # qwen3:8b + coder + embeddings
movili status
```

### LM Studio

1. Baixe o modelo `qwen3-8b` pela busca do app.
2. Aba **Developer** → **Start Server** (porta 1234).
3. `movili status --backend lmstudio`

O roteador tenta o Ollama primeiro e cai para o LM Studio automaticamente se ele
estiver fora do ar — e vice-versa, com `--backend lmstudio`.

### Sem backend nenhum

Para testar o encanamento (fluxos, handoffs, relatórios) sem executar modelo:

```bash
movili --backend simulado fluxo prospeccao "vender squad para transportadoras"
```

As respostas vêm marcadas como `[RESPOSTA SIMULADA]` — nunca se confundem com saída real.

---

## Modelos do Ollama: qual usar para quê

O catálogo completo está em `config/modelos.yaml` e é navegável pela CLI:

```bash
movili modelos                  # catálogo inteiro + perfis de hardware
movili modelos --grupo codigo   # só os modelos de código
```

### O melhor modelo aberto para cada função

| Função | Modelo recomendado | Por quê |
|---|---|---|
| Padrão de toda a casa | **`qwen3:8b`** | melhor relação qualidade/custo em pt-BR e uso de ferramenta |
| Arquiteto backend | `qwen3-coder:30b-a3b` | MoE: qualidade de 30b com custo de 3b ativo, forte em agente |
| Frontend / Mobile / Segurança | `qwen2.5-coder:14b` | melhor custo-benefício em código real |
| Analista de dados | `qwen2.5-coder:14b` (+ `sqlcoder:15b` para SQL puro) | modelagem dimensional e SQL |
| Financeiro | `deepseek-r1:14b` | raciocínio passo a passo — memória de cálculo consistente |
| Jurídico | `mistral-small:24b` | texto longo e formal, forte em português |
| Copy / Design / CS | `gemma3:12b` | a escrita mais natural em pt-BR entre os modelos médios |
| Prospecção | `mistral-nemo:12b` | textos curtos, e-mail frio e cadência |
| Sócios / Diretoria / Produto / PMO | `qwen3:14b` | nuance de decisão e síntese executiva |
| Embeddings — memória da empresa | **`nomic-embed-text`** | rápido, 8k de contexto, bom em português — é o que faz os agentes lembrarem de projetos anteriores |
| Visão (mockup, OCR) | `llama3.2-vision:11b` / `minicpm-v:8b` | análise de criativo e leitura de documento |

### Perfis de hardware

Um comando troca o modelo de todos os agentes de uma vez:

| Perfil | RAM/VRAM | O que faz |
|---|---|---|
| `leve` | 8 GB | `qwen3:4b` na maioria, `qwen2.5-coder:7b` na engenharia |
| `equilibrado` | 16 GB | `qwen3:8b` + coder dedicado + `deepseek-r1:8b` no financeiro |
| `especializado` | 24–32 GB | **o melhor modelo para cada função** (tabela acima) |
| `maximo` | 48 GB+ | `qwen3:32b`, `llama3.3:70b`, `qwen2.5-coder:32b` |

```bash
./scripts/baixar_modelos.sh especializado
movili fluxo novo-projeto "..." --perfil especializado
```

Grupos de download disponíveis: `essenciais`, `leve`, `equilibrado`, `especializado`,
`maximo`, `codigo`, `generalistas`, `raciocinio`, `embeddings`, `visao`, `leves`, `todos`.

```bash
./scripts/baixar_modelos.sh --listar
```

> Modelos cuja tag não exista mais no registro são pulados com aviso, sem derrubar o
> download dos demais. Confira as tags atuais em <https://ollama.com/library>.

---

## Comandos

```bash
movili status                                    # backends, modelos e roteamento
movili equipe [--detalhe <id>]                   # organograma e fichas
movili modelos [--grupo <g>]                     # catálogo de modelos
movili fluxos                                    # processos internos

movili agente <id> "<tarefa>"                    # fala com um funcionário
movili fluxo <nome> "<briefing>"                 # executa um processo
movili reuniao "<tema>" [--rodadas N] [--setor X]
movili atender "<demanda>"                       # a diretoria escala o time
movili chat                                      # modo conversa por texto

movili memoria status                            # estado do índice semântico
movili memoria buscar "<consulta>" [--agente X] [--minimo 0.5]
movili memoria indexar {--projeto X | --arquivo Y}
movili memoria limpar [--projeto X]

movili rotinas [listar|proximas|rodar|agenda]     # calendário interno
movili painel [--porta 8080]                     # painel web ao vivo
movili jarvis [--diagnostico]                    # conversa por voz
movili ponte [--porta 8123]                      # API OpenAI-compatível
movili api [--porta 8000]                        # API REST (requer FastAPI)
```

**Flags globais:** `--backend {ollama,lmstudio,simulado}` · `--modelo qwen3:14b` ·
`--perfil especializado` · `--projeto nome` · `--salvar pasta` · `--silencioso` · `--sem-banco`

---

## Configuração

### `config/empresa.yaml` — o "manual do funcionário"

Todo agente recebe este contexto no prompt de sistema: posicionamento, público-alvo,
stack padrão, tom de voz, custo/hora, margem mínima e as **regras da casa** — por
exemplo, "nenhum preço vai ao cliente sem validação do financeiro". Edite este arquivo
para adaptar o ecossistema à realidade da sua empresa.

### `config/modelos.yaml` — backends, roteamento e catálogo

Backends, ordem de fallback, o modelo de cada agente, os perfis de hardware e o
catálogo comentado de 44 modelos abertos.

### `.env` — sobrescreve tudo

```bash
MOVILI_BACKEND_PADRAO=lmstudio
MOVILI_MODELO_PADRAO=qwen3:14b
MOVILI_OLLAMA_URL=http://192.168.0.10:11434
```

---

## Arquitetura

```
movili/
├── llm/                 camada de modelos locais
│   ├── base.py          contratos, limpeza de <think> do Qwen3
│   ├── ollama.py        /api/chat nativo
│   ├── lmstudio.py      /v1/chat/completions (compatível OpenAI)
│   └── router.py        fallback entre backends + métricas por agente
├── core/
│   ├── mensagem.py      unidade de comunicação (tipo, prioridade, thread)
│   ├── barramento.py    pub/sub thread-safe com histórico auditável
│   ├── memoria.py       janela curta por agente + SQLite corporativo
│   ├── ferramentas.py   calculadora segura, workspace sandbox
│   ├── rag.py           memória semântica: fatiamento, cosseno, procedência
│   ├── agente.py        persona, prompt de sistema, loop de ferramentas
│   └── orquestrador.py  fluxos, reuniões, triagem, paralelismo
├── agentes/             20 fichas funcionais (uma por arquivo)
├── fluxos/              7 processos internos
├── rotinas/             calendário interno: agendamento, catálogo e agenda
├── painel/              painel web ao vivo (SSE, stdlib, sem dependência)
├── jarvis/              OpenJarvis: voz, conversa e ponte OpenAI
├── api/                 API REST opcional (FastAPI)
└── cli.py               interface de linha de comando
```

**Decisões de projeto:**

- **Zero dependência obrigatória além do PyYAML.** A camada de LLM usa `urllib` da
  biblioteca padrão. FastAPI e os motores de voz são extras opcionais.
- **Falha explícita.** Se nenhum backend responde, o erro diz exatamente o que subir.
  O backend `simulado` nunca entra no fallback automático — ele só roda se for pedido,
  para não mascarar um Ollama fora do ar.
- **Ferramentas sem `function calling` nativo.** O agente emite um bloco JSON e o
  executor resolve. Funciona igual nos dois backends, com qualquer modelo aberto.
- **Sandbox no workspace.** A ferramenta de escrita recusa caminhos fora do workspace.
- **Sem `eval`.** A calculadora do financeiro usa AST com operadores permitidos.
- **Degradação, não quebra.** Memória semântica indisponível, motor de voz ausente ou
  indexação falhando nunca derrubam a entrega — o ecossistema segue e avisa.

---

## API HTTP

```bash
pip install -r requirements-api.txt
movili api --porta 8000        # docs interativas em /docs
```

| Rota | Método | O que faz |
|---|---|---|
| `/equipe` | GET | fichas de todos os funcionários |
| `/status` | GET | estado dos backends |
| `/fluxos` | GET | processos disponíveis |
| `/agente/{id}` | POST | fala com um funcionário |
| `/fluxo/{nome}` | POST | executa um processo |
| `/reuniao` | POST | convoca uma reunião |
| `/atender` | POST | triagem automática |
| `/jarvis` | POST | um turno de conversa |
| `/memoria` | GET | estado do índice semântico |
| `/memoria/buscar` | POST | busca na memória da empresa |

---

## Docker

```bash
docker compose up -d                  # sobe Ollama + baixa qwen3:8b + o ecossistema
docker compose exec movili movili status
docker compose exec movili movili fluxo novo-projeto "sua demanda aqui"
```

Portas publicadas: `8080` (painel), `8000` (API) e `8123` (ponte OpenJarvis).
Para GPU NVIDIA, descomente o bloco `deploy.resources` no `docker-compose.yml`.

---

## Testes

```bash
make teste        # ou: python -m pytest tests -q
```

180 testes rodando no backend simulado — sem GPU, sem modelo baixado, sem rede.
Cobrem estrutura do quadro, consistência dos fluxos (inclusive se uma etapa depende
de alguém que ainda não atuou), roteamento de modelos, barramento, memória, sandbox
das ferramentas, fallback entre backends, a memória semântica (fatiamento, cosseno
degenerado, isolamento de procedência, degradação sem backend), o painel (validação de
entrada, fila de trabalho, encerramento ordenado), o agendamento das rotinas (mês curto,
ano bissexto, trimestre, catch-up depois de uma parada longa) e a interpretação de
intenção do Jarvis. Nove ordens de importação diferentes rodam em subprocess, para pegar ciclo de
import antes que o usuário pegue.

```bash
python scripts/verificar.py    # diagnóstico do ambiente e modelos faltando
```

---

## Licença

MIT — veja [LICENSE](LICENSE).
