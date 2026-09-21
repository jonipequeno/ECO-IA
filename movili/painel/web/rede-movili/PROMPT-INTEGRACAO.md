# Prompt de integração da Rede Movili ao projeto

**Como usar:** descompacte o kit `rede-movili-kit.zip` dentro de `movili/painel/web/`, para os arquivos ficarem em `movili/painel/web/rede-movili/`. Depois abra o Claude Code (ou o Cursor) na raiz do repositório e cole o prompt abaixo inteiro. O prompt também vai dentro do kit, em `rede-movili/PROMPT-INTEGRACAO.md`.

```
Você vai integrar o design system "Rede Movili" ao painel do projeto Movili: a tela que mostra a empresa operada por 20 agentes de IA como uma rede neural viva (obsidiana bioluminescente, com a interação de uma visão de grafo). O design system já está pronto e vem num kit em movili/painel/web/rede-movili/. Seu trabalho é ligar o kit aos dados reais do projeto, sem redesenhar nada.

## O que vem no kit (não edite estes arquivos)

movili/painel/web/rede-movili/
  tokens.css     variáveis de design: cores dos temas escuro e claro, tipografia, espaços, tempos
  bundle.css     estilos dos componentes (importa Sora e Space Mono do Google Fonts)
  bundle.js      componentes em JavaScript puro, sem build e sem dependências; publica window.MoviliRede
  index.d.ts     a API documentada em tipos: leia antes de escrever código
  tokens.json    a fonte dos tokens
  README.md      as regras visuais e de voz
  guia/          os sete estados, a topologia de referência e o prompt de geração
  exemplo.html   a tela completa em modo demonstração: abra no navegador para ver o alvo

Se faltar algo no kit para a integração funcionar, não altere bundle.js, bundle.css, tokens.css nem tokens.json: anote na lista de pendências do relatório final. As mudanças visuais voltam para o design system, não para o kit.

## Passo 0: entenda antes de mexer

1. Leia index.d.ts, README.md e guia/1-estados.md do kit, e abra exemplo.html.
2. Mapeie o projeto e escreva um resumo curto antes de editar qualquer coisa:
   - movili/painel/web/index.html: o que o painel atual mostra e faz, de onde tira os dados e como (endpoint, WebSocket, SSE ou polling).
   - O servidor Python que serve o painel: framework, rotas e como serve arquivos estáticos.
   - movili/core/mensagem.py: a estrutura da mensagem (campos de tipo, prioridade, remetente, destinatário, conteúdo e horário) e os valores exatos dos 9 tipos e das 4 prioridades.
   - movili/agentes/: todos_os_perfis() e os campos de cada perfil (id, nome, cargo, região, interlocutores, modelo e limiar, se existirem).
   - Onde as mensagens entre agentes são criadas ou despachadas, para saber onde se inscrever nelas.
   - Como uma demanda externa entra (por exemplo, um lead chegando pelo WhatsApp, se o projeto já tiver essa entrada).
3. Liste as funções do painel atual que não têm lugar óbvio na nova tela. Não apague nenhuma função sem me perguntar.

## Passo 1: carregar o kit no painel

- Sirva a pasta rede-movili/ como arquivos estáticos. Se o painel precisa continuar arquivo único, embuta os três arquivos no index.html em <style> e <script> (o bundle não contém a sequência de fechamento de script).
- Ordem: tokens.css, bundle.css, bundle.js. O <html> recebe data-theme="escuro" (padrão) ou "claro".
- html e body com altura 100% e margem 0; o contêiner da tela com height: 100dvh (100vh de reserva).
- As classes tipográficas do tokens.css (.titulo, .secao, .corpo, .rotulo, .leitura, .leitura-destaque) são globais: confira se não colidem com o CSS antigo do painel. O CSS antigo que conflitar sai.

## Passo 2: topologia real

Crie GET /api/rede/topologia (ou o equivalente no padrão de rotas do projeto), montado a partir de todos_os_perfis(), no formato de DadosTopologia do index.d.ts:

  {
    "regioes":      [{"id": "comercial", "nome": "Comercial"}, ...],
    "agentes":      [{"id": "comercial", "regiao": "comercial", "nome": "Eduardo Lima", "cargo": "Closer", "modelo": ..., "limiar": ...}, ...],
    "sinapses":     [["comercial", "copy"], ...],
    "reciprocas":   [["comercial", "financeiro"], ...],
    "declaraTodos": ["diretor"]
  }

Regras:
- sinapses = pares únicos das declarações (i, a) com a != '*'. reciprocas = pares em que (i, a) e (a, i) foram declarados. declaraTodos = quem tem interlocutores == '*'.
- Hoje devem sair 20 agentes, 86 declarações, 67 sinapses e 19 recíprocas. Se o código disser outra coisa, confie no código e registre a diferença no relatório.
- Não invente campos. Sem modelo no perfil, modelo = null (a ficha mostra "—"). Sem limiar, omita o campo (vale 0,5).
- Se o perfil não tiver região, nome ou cargo, use esta referência:
    socios: socio_estrategia (Helena Vasconcelos, CSO), socio_tecnologia (Gustavo Ribeiro, CTO)
    diretoria: diretor (Ricardo Menezes, CEO)
    produto: produto (Juliana Prado, Product Manager), projetos (Vinicius Rocha, Gerente de Projetos), design (Felipe Moraes, UX/UI)
    engenharia: dev_backend (Rafael Andrade, Arquiteto/Backend), dev_frontend (Camila Reis, Frontend), dev_mobile (Bruno Tavares, Mobile/DevOps/QA)
    dados: dados (Aline Ferraz, BI)
    marketing: marketing (Larissa Monteiro, Head de Marketing), seo (Diego Barros, SEO), copy (Marina Duarte, Copywriter)
    comercial: prospeccao (Thiago Nunes, SDR), comercial (Eduardo Lima, Closer)
    financeiro: financeiro (Patricia Souza, Controller)
    juridico: juridico (Roberto Aguiar, Contratos/LGPD)
    seguranca: seguranca (Daniel Okamoto, CISO/AppSec)
    pessoas: rh (Sofia Nogueira, People)
    sucesso_do_cliente: cs (Marcelo Brito, Customer Success)
  Nomes das regiões: Sócios, Diretoria, Produto, Engenharia, Dados, Marketing, Comercial, Financeiro, Jurídico, Segurança, Pessoas, Sucesso do cliente.

## Passo 3: tráfego ao vivo

Cada mensagem entre agentes vira um evento na rede:

  rede.registrar({ tipo: tipo, de: remetente, para: destinatario, prioridade: prioridade, texto: resumo })

- tipo: um dos 9 ids exatos, em minúsculas e sem acento: briefing, tarefa, entrega, pergunta, resposta, revisao, decisao, alerta, informe. Converta o enum de mensagem.py para esses ids.
- prioridade: baixa, normal, alta ou critica.
- de e para: ids de agente. Informe vai para a rede inteira: para = null.
- texto: um resumo de até 140 caracteres (o assunto, se houver). Nada de dado sensível de cliente.
- Não mande horário: o evento entra no agora da rede.
- Uma demanda que chega de fora, sem agente remetente, não é registrar. É:
    rede.estimular({ no: idDoAgenteQueRecebe, texto: resumo })
  que dispara a onda de estímulo. Não invente afinidades: sem um dado real de relevância, passe só o nó de entrada; os outros acendem quando participam das mensagens.
- Reforço e atrofia das sinapses são automáticos no bundle. O backend não calcula pesos.

Transporte: use o que o painel já usa. Se não houver nada em tempo real, crie um SSE em GET /api/rede/eventos (text/event-stream, um evento JSON por mensagem, id incremental para retomar com Last-Event-ID, comentário de heartbeat a cada 15 s) e consuma com EventSource. Nenhuma dependência nova no front; no Python, só a biblioteca padrão ou o que o projeto já usa.

Queda de conexão: chame tela.controle.conexao(false) quando o stream cair (erro do EventSource ou do socket) e tela.controle.conexao(true) quando ele voltar. O cabeçalho mostra "Desconectado" nesse intervalo e a rede continua navegável.

## Passo 4: a tela

Substitua a interface antiga por:

  var tela = MoviliRede.Tela({
    demo: false,
    dados: topologia,              // Passo 2
    pesos: pesosSalvos,            // Passo 6; {} na primeira vez
    aoEnviar: enviarMensagem,      // Passo 5; devolve a Promise do envio
    aoAlternarTema: alternarTema   // troca data-theme no <html> e guarda a escolha
  });
  document.getElementById('app').appendChild(tela);
  var rede = tela.controle.rede;

- demo: false sempre em produção. O parâmetro roda fica no padrão ('direta'): o painel é tela cheia e a roda do mouse aproxima.
- Tema: padrão escuro; guarde a escolha em localStorage, dentro de try/catch.
- Nada de CSS novo por cima dos componentes. Se algo precisar mudar visualmente, vai para a lista de pendências.

## Passo 5: falar direto com um agente

aoEnviar(texto, agente) usa o mesmo caminho que o projeto já tem para mandar uma mensagem a um agente (procure; se não existir, crie POST /api/agentes/<id>/mensagens) e devolve a Promise desse envio, rejeitando em qualquer resposta fora de 2xx. Enquanto ela corre, o botão Enviar fica desabilitado; se rejeitar, a ficha devolve o texto ao campo e mostra o aviso de erro, sozinha. A rede já acende a onda no agente quando a mensagem sai; as respostas chegam pelo stream do Passo 3.

## Passo 6: a rede que aprende entre sessões

- Ao abrir: GET /api/rede/pesos devolve {"a|b": peso}, com os dois ids em ordem alfabética separados por "|". Passe o resultado em pesos.
- Durante o uso: a cada 60 s e no pagehide (navigator.sendBeacon), POST /api/rede/pesos com rede.pesos().
- Guarde num JSON no servidor (por exemplo, movili/painel/pesos.json), com escrita atômica (arquivo temporário e rename) e valores entre 0 e 1.
- É isso que faz a topologia de hoje ser diferente da de ontem.

## Passo 7: fontes

O bundle.css importa Sora e Space Mono do Google Fonts. Se o painel precisa funcionar sem internet, baixe os arquivos woff2 das duas (licença OFL) para rede-movili/fonts/ e declare os @font-face num CSS seu, carregado depois do bundle.css, sem editar o kit. Sem as fontes, o painel cai para as fontes do sistema, sem quebrar.

## Critérios de aceite

- A rede mostra os 20 agentes e as 67 sinapses reais; as recíprocas saem mais grossas; o diretor tem as sinapses latentes.
- Uma mensagem de teste entre dois agentes faz o cometa atravessar a sinapse certa, com o glifo e a cor do tipo; uma entrega volta no sentido contrário e reforça a sinapse.
- Uma demanda externa dispara a onda a partir do agente de entrada.
- Ao recarregar a página, os pesos aprendidos continuam: as sinapses reforçadas seguem mais grossas.
- Clicar num neurônio abre a ficha com nome, cargo, modelo (ou "—"), sinapses e últimas trocas, e o campo envia de verdade.
- Desligar o servidor mostra "Desconectado"; religar volta a "Ao vivo" sem recarregar.
- Funciona a 360px, no tema claro, pelo teclado (Tab, Enter, Esc, +, −, 0) e com prefers-reduced-motion.
- Nenhum erro no console e nenhuma dependência nova no front.

## Testes

- Python: testes para a topologia (as contagens acima), para o conversor de mensagem (os 9 tipos, as 4 prioridades, informe para todos, demanda externa) e para salvar e carregar pesos.
- Manual: percorra os critérios de aceite com o servidor rodando e anote o resultado de cada um.

## Relatório final

Liste: arquivos criados e alterados; como rodar; decisões que você tomou; diferenças entre o código e a referência (contagens, campos ausentes); funções do painel antigo que ficaram sem lugar; e pendências para o design system (o que faltou no kit), sem ter editado o kit.
```
