# Guia de uso

## Primeiro dia

```bash
./scripts/instalar.sh completo
source .venv/bin/activate

ollama serve &                            # em outro terminal, de preferência
./scripts/baixar_modelos.sh essenciais

movili status                             # confirma backend e modelos
python scripts/verificar.py               # diagnóstico da estrutura
movili equipe                             # conheça o time
```

---

## Falar com uma pessoa

```bash
movili agente financeiro "precifique um projeto de 1200 horas com squad de 4 pessoas"
movili agente seguranca "modele as ameaças de uma API pública de pagamentos"
movili agente copy "3 headlines para a landing de modernização de legado"
movili agente projetos "cronograma de 16 semanas para um app com backend e admin"
```

O agente pode acionar colegas sozinho durante a entrega. O relatório mostra quem foi
chamado e o que respondeu.

---

## Rodar um processo completo

```bash
movili fluxo novo-projeto "transportadora com 80 caminhões quer app de roteirização \
  e rastreamento, integrado ao ERP Protheus, prazo de 4 meses"
```

O que acontece, em ordem: o comercial qualifica e traduz em briefing técnico → o
arquiteto propõe arquitetura e estima horas → a PM define MVP e critérios de aceite →
segurança modela ameaças → design especifica as telas → frontend e mobile estimam em
paralelo → o PMO monta cronograma e riscos → RH confere capacidade → o financeiro
precifica com a conta aberta → o jurídico aponta cláusulas → o comercial monta a
proposta final → o CEO aprova, ajusta ou reprova.

Saída em `workspace/<projeto>/`:

| Arquivo | Conteúdo |
|---|---|
| `relatorio.md` | todas as entregas em ordem, com a consolidação do CEO |
| `resultado.json` | o mesmo, estruturado, para integrar em outro sistema |
| `conversas.json` | o tráfego completo do barramento, para auditoria |

---

## Convocar uma reunião

```bash
movili reuniao "vale a pena criar um produto SaaS próprio?" --rodadas 3
movili reuniao "revisão de segurança do trimestre" --setor engenharia
movili reuniao "proposta do cliente X está abaixo da margem" \
  --participantes comercial,financeiro,diretor,socio_estrategia
```

Setores disponíveis: `socios`, `diretoria`, `produto`, `engenharia`, `dados`,
`marketing`, `comercial`, `financeiro`, `juridico`, `seguranca`, `pessoas`,
`sucesso_do_cliente`.

Na primeira rodada cada um traz a posição da sua área. Da segunda em diante, responde a
quem citou sua área, diz onde discorda e assume um compromisso. O CEO fecha com a ata.

> **Custo.** Uma reunião de 3 rodadas com 8 participantes são 25 chamadas de modelo.
> Em `qwen3:8b` num notebook, conte alguns minutos. Comece com `--rodadas 2` e um
> `--setor` em vez da empresa inteira.

---

## Deixar a diretoria decidir

```bash
movili atender "cliente quer integrar ERP com marketplace em 90 dias"
movili atender "queda de 30% no tráfego orgânico no último mês" --maximo 4
```

O CEO faz a triagem, escala quem precisa atuar, roda e consolida.

---

## Fazer a empresa lembrar

```bash
ollama pull nomic-embed-text      # habilita a memória semântica
```

A partir daí, cada entrega é indexada e o trabalho anterior relevante entra no contexto
das próximas tarefas automaticamente. Você vê acontecendo no progresso:

```
>> Patricia Souza (Controller e Gerente Financeira Senior) trabalhando...
   (recuperou memoria de projetos anteriores)
```

```bash
movili memoria status                                    # o que está indexado
movili memoria buscar "precificação de logística"        # consulta direta
movili memoria buscar "cláusula de SLA" --agente juridico
movili memoria indexar --projeto frota-2026              # reindexa projeto antigo
movili memoria indexar --arquivo docs/contrato-modelo.md # ensina um documento à casa
movili memoria limpar --projeto teste
```

**Calibrando o limiar.** O padrão é `0.55`. Se a memória nunca aparecer, baixe para
`0.45`; se vier coisa fora de contexto, suba para `0.6`. Teste o efeito antes de mudar
a configuração:

```bash
movili memoria buscar "<assunto>" --minimo 0.45
```

**Trocou de modelo de embedding?** `movili memoria status` avisa quantos trechos ficaram
invisíveis — vetores de modelos diferentes não são comparáveis. Reindexe os projetos que
importam com `movili memoria indexar --projeto <nome>`.

**Desligar:** `MOVILI_EMBEDDINGS=0` ou `embeddings.habilitado: false` em
`config/modelos.yaml`.

---

## Deixar a empresa rodar sozinha

```bash
movili rotinas             # o calendário de fábrica
movili rotinas proximas    # o que vem por aí
movili rotinas agenda      # deixa de pé; executa na hora marcada
```

A `agenda` fica checando e dispara cada rotina no horário. Deixe num `tmux`, num
`systemd --user` ou num container — a última execução fica gravada, então reiniciar não
faz nada rodar duas vezes.

Para disparar uma fora de hora (útil para testar antes de confiar o horário a ela):

```bash
movili rotinas rodar --rotina pipeline
```

**Ajustando o ritmo.** As rotinas ficam em `movili/rotinas/catalogo.py`. O agendamento é
um `Agendamento(hora, minuto, dias_da_semana, dias_do_mes, meses)` — conjunto vazio quer
dizer "qualquer". Alguns exemplos:

```python
Agendamento(hora=9, dias_da_semana=frozenset({0,1,2,3,4}))   # de segunda a sexta, 09:00
Agendamento(hora=14, dias_da_semana=frozenset({2}))          # toda quarta, 14:00
Agendamento(hora=9, dias_do_mes=frozenset({1}))              # todo dia 1º
Agendamento(hora=18, dias_do_mes=frozenset({31}))            # último dia do mês
Agendamento(hora=9, dias_do_mes=frozenset({1}),
            meses=frozenset({1,4,7,10}))                     # trimestral
```

Dia 31 cai no último dia em meses curtos — senão a rotina nunca rodaria em fevereiro.
Quando dia da semana e dia do mês são combinados, a data precisa satisfazer os dois.

---

## Acompanhar pelo navegador

```bash
movili painel                    # http://127.0.0.1:8080
```

Dispare um trabalho pela coluna da direita e veja o barramento encher: cada tarefa que
a diretoria distribui, cada entrega que volta, cada pergunta de um agente para outro,
no instante em que acontece.

Clicar numa pessoa do organograma abre a aba "Pessoa" já com ela selecionada — atalho
para perguntar algo direto a um funcionário sem sair do painel.

`Ctrl+Enter` na caixa de texto envia sem tirar a mão do teclado.

Para acompanhar de outro dispositivo na mesma rede:

```bash
movili painel --host 0.0.0.0
```

Sem autenticação — só faça isso em rede confiável.

---

## Conversar por voz

```bash
movili jarvis --diagnostico     # o que está instalado
movili jarvis                   # inicia
movili jarvis --stt teclado     # digita e ouve a resposta
movili jarvis --frases 6        # respostas faladas um pouco mais longas
```

Para deixá-lo em espera, acordando só ao ouvir o nome:

```bash
movili jarvis --palavra              # acorda com "jarvis"
movili jarvis --palavra movili       # troca a palavra
```

Ele segue ouvindo por 25 segundos depois de responder, então numa conversa você não repete
o nome a cada frase. `--janela 40` estica isso.

Frases que funcionam:

- "chama a Patrícia e pergunta a margem de um projeto de duzentos mil"
- "monta uma proposta para um app de logística"
- "convoca uma reunião sobre entrar no mercado de saúde"
- "quem trabalha aqui"
- "Jarvis, chama a Patrícia" (com a palavra de despertar ligada, tudo numa fala só)
- "sair"

---

## Ligar um cliente externo

```bash
movili ponte --porta 8123
```

Aponte qualquer cliente OpenAI-compatível para `http://127.0.0.1:8123/v1` e escolha o
"modelo": `movili-jarvis`, `movili-empresa` ou `movili-<agente>`.

```python
from openai import OpenAI

cliente = OpenAI(base_url="http://127.0.0.1:8123/v1", api_key="nao-usada")
r = cliente.chat.completions.create(
    model="movili-seguranca",
    messages=[{"role": "user", "content": "revise a arquitetura de autenticação por JWT"}],
)
print(r.choices[0].message.content)
```

---

## Ajustar a empresa à sua realidade

Edite `config/empresa.yaml`: nome, posicionamento, público-alvo, stack, tom de voz,
custo/hora, margem mínima, metas e **regras da casa**. Todo agente passa a operar com
esse contexto.

As regras da casa têm efeito prático. Com

```yaml
regras_da_casa:
  - Nenhum preço é comunicado ao cliente sem validação do financeiro
```

o comercial passa a acionar a Patricia antes de fechar qualquer número — não porque
alguém programou o fluxo, mas porque a regra está no prompt dele.

---

## Trocar de modelo

```bash
movili fluxo novo-projeto "..." --perfil especializado       # melhor por função
movili reuniao "..." --modelo qwen3:14b                      # um modelo para todos
movili agente dev_backend "..." --modelo qwen3-coder:30b-a3b # só nesta chamada
movili status --backend lmstudio                             # trocar de backend
```

Veja [MODELOS.md](MODELOS.md) para a justificativa de cada escolha.

---

## Problemas comuns

**"nenhum backend respondeu"** — o Ollama não está rodando (`ollama serve`) ou o LM
Studio não iniciou o servidor (Developer → Start Server). Confirme com `movili status`.

**"model not found"** — o modelo configurado não foi baixado. `movili status` lista o que
existe; `python scripts/verificar.py` aponta o que falta. Baixe com
`./scripts/baixar_modelos.sh <grupo>`.

**Resposta com `<think>`** — não deveria acontecer: o ecossistema limpa esses blocos. Se
aparecer, abra uma issue com o modelo e o comando usados.

**Muito lento** — use `--perfil leve`, reduza `--rodadas`, limite `--maximo` na triagem
ou escolha um `--setor` em vez da empresa toda.

**Fluxo travou no meio** — cada etapa tem timeout de 300s (ajustável em
`MOVILI_TIMEOUT`). Modelo grande em CPU pode estourar; reduza o modelo ou aumente o
timeout.

**Testar sem modelo nenhum** — `--backend simulado` valida todo o encanamento sem
executar modelo. As respostas vêm marcadas como `[RESPOSTA SIMULADA]`, e a vetorização
também é simulada (hashing lexical, não semântico) — serve para exercitar o RAG, não
para avaliar a qualidade da busca.

**A memória nunca aparece** — confira nesta ordem: `movili memoria status` mostra
trechos indexados? Se `inativos` for maior que zero, você trocou de modelo de embedding
e precisa reindexar. Se houver trechos ativos, o limiar está alto demais: teste com
`movili memoria buscar "<assunto>" --minimo 0.45` e ajuste
`embeddings.similaridade_minima`.
