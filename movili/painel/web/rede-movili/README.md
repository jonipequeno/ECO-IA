Sistema visual do painel que mostra a Movili operada por 20 agentes de IA como uma rede neural viva, em obsidiana bioluminescente: a rede ocupa a tela inteira sobre um fundo quase preto com reflexo violeta, cada neurônio acende na cor do tráfego que está processando, e a interface é vidro por cima. A metáfora é literal: cada agente é um neurônio, cada ligação é uma sinapse com peso, uma demanda que entra é um estímulo que propaga em ondas, e o que dá certo reforça a sinapse de vez. A tela precisa deixar isso visível sem uma legenda explicando.

## Princípios

- **Estados antes de estética.** Uma rede bonita e parada falhou. Repouso, estímulo, ativação, propagação, entrega, reforço e atrofia têm, cada um, uma forma de aparecer (veja a seção Os sete estados).
- **A assimetria é o dado.** `comercial` tem 11 sinapses e `prospeccao` tem 4: o raio vem de `raio-grau-*` e a diferença salta aos olhos. Nunca iguale neurônios.
- **Luz carrega significado.** Intensidade da luz = ativação. Espessura, brilho e fluxo de partículas da sinapse = peso aprendido. Matiz = tipo da mensagem: no cometa que atravessa a sinapse e na coroa de quem a processa. O violeta de `acento` é só seleção e foco; a névoa das regiões e o plâncton são o único tom ambiente.
- **Nada só por cor.** Todo tipo tem glifo e palavra, toda prioridade tem barras e palavra, todo estado tem texto.
- **É um grafo que se toca.** Como a visão de grafo de um app de notas (a referência é o Obsidian): arrasta-se um neurônio e a física responde, arrasta-se o fundo, aproxima-se com roda ou pinça, e os nomes aparecem com o zoom.
- **A rede não tem topo.** Nada de organograma, nada de chefe no alto. O layout é força dirigida e as regiões são campos de gravidade.

## Conteúdo e voz

- Português do Brasil, frase curta, caixa de frase. Sem ponto de exclamação, sem emoji.
- Botões no infinitivo ou substantivo curto: "Enviar", "Ao vivo", "Ligar todos", "Centralizar".
- Pessoa em `corpo` ou `titulo` (Eduardo Lima), identificador em `leitura` (`comercial`, `dev_backend`). O id de agente aparece sempre como está no código, com sublinhado.
- Números como num console de bordo, em `leitura`: ativação e limiar em porcentagem inteira ("72%", "limiar 50%"); peso com duas casas e vírgula ("0,64"); tempo relativo como "−00:04,2" ou "há 4 s".
- Os nove tipos se escrevem Briefing, Tarefa, Entrega, Pergunta, Resposta, Revisão, Decisão, Alerta, Informe; as prioridades, Baixa, Normal, Alta, Crítica. Os ids ficam sem acento (`revisao`, `critica`), os rótulos com.
- Estados do sistema: Ao vivo, Reprodução, Pausado, Desconectado. Enquanto um neurônio está aceso, a ficha e a dica dizem o que ele está "processando", com o selo do tipo.
- Rótulo sobre a rede só na interação: ponteiro, foco, seleção ou zoom a partir de `zoom-rotulos`. Nunca permanente no zoom inicial.

## Fundamentos visuais

### Cor

Tema escuro primeiro. Obsidiana: `fundo` #0b0a10, `superficie` #15141c, `superficie-2` #1f1d28, `borda` #2b2936, `texto` #ece9f5, `texto-suave` #a7a2b8, `acento` #8b6cf6. Tudo que flutua sobre a rede é `vidro` (a superfície a 92%, com desfoque `desfoque-vidro`).

- Texto principal em `texto` sobre `fundo`, `superficie`, `superficie-2` ou `vidro`; secundário em `texto-suave` nas mesmas bases, com 4,5:1 ou mais mesmo com um neurônio aceso atrás do vidro.
- `acento` é seleção e foco: anel do neurônio selecionado, aro violeta dos vizinhos e sinapses realçadas quando algo está em foco, anel de foco, cabeça e trecho percorrido da linha do tempo, botão Enviar. Nunca é tipo de mensagem.
- `sucesso`, `atencao` e `erro` são estados do sistema no cabeçalho, sempre com a palavra ao lado. Na rede aparecem só como apelidos de tipos (entrega, alerta).
- `borda` é fio decorativo e fica abaixo de 3:1 de propósito; controles usam `borda-controle`.

### Os nove matizes do tráfego

Cada tipo tem um token `msg-*`, usado no cometa, na coroa de quem o processa, no glifo do selo, na pílula do filtro e na marca da linha do tempo: briefing ciano, tarefa azul, entrega verde (`sucesso`), pergunta magenta, resposta rosa, revisão lima, decisão âmbar, alerta vermelho-coral (`erro`) e informe neutro, que fala com todos. Pares relacionados são vizinhos no círculo cromático e no glifo: pergunta e resposta (magenta e rosa, losango vazio e cheio), entrega e revisão (verde e lima), briefing e tarefa (ciano e azul). No claro, os mesmos matizes viram pigmento, escuros o bastante para 3,4:1 ou mais.

Nove categorias passam do que a cor sozinha separa: sob deuteranopia, entrega e resposta se confundem, e tarefa e pergunta também. Por isso o glifo é obrigatório em todo lugar onde o matiz aparece.

### Luz no escuro, tinta no claro

O tema claro é equivalente, não o inverso. No escuro, a rede é bioluminescente: a ativação é luz somada ao fundo (composição aditiva). O núcleo acende em `ativacao`, branco, e a coroa em volta cresce até `halo-max` vezes o raio na cor do tráfego que o neurônio está processando. No claro, a rede é um registro em papel: o núcleo escurece em `ativacao`, tinta, e a coroa vira de um a três anéis concêntricos na cor do tipo, como curvas de nível. A sinapse reforçada clareia no escuro e escurece no claro. Os cometas, no claro, levam um contorno da cor de `fundo` para não se fundir à linha.

### Neurônio

- Raio = `raio-grau-<grau>` (3,6 × grau^0,7). Na tela pequena, tudo escala junto (de 0,72 a 1,1), e o zoom escala o resto.
- Em repouso, um ponto sólido de grafo em `neuronio` (3,3:1 ou mais sobre `fundo`), com um reflexo interno que respira. No claro, com um aro fino em `neuronio-contorno`.
- Acima do limiar (`limiar-padrao`, ou o do perfil): núcleo e coroa na proporção da ativação, apagando com `decaimento-ativacao`. Abaixo do limiar: só um anel fino treme.
- Selecionado: anel `acento` com `traco-selecao`, afastado 4px, com brilho violeta. Vizinho de quem está em foco: aro violeta fino. Nenhum neurônio tem cor própria.

### Sinapse

- Fina, como num grafo de notas: largura de `traco-sinapse-min` a `traco-sinapse-max` e cor de `sinapse-fraca` a `sinapse-forte`, pelo peso.
- Fluxo de repouso: até `particulas-max` partículas atravessam a sinapse, em número e velocidade proporcionais ao peso (de `fluxo-lento` a `fluxo-rapido`). Uma sinapse forte tem mais vida, mesmo parada.
- Conduzindo, vira um filamento de luz na cor do tipo que passa.
- Peso inicial `peso-reciproca` (os dois lados se declararam, mais espessa desde o repouso) ou `peso-unilateral`.
- Latentes: o `diretor` declara todos, então as 10 ligações que ninguém declarou com ele ficam em `sinapse-latente`, quase invisíveis; tracejadas quando uma das pontas está em foco; acesas ao conduzir.
- Plasticidade em `taxa-reforco`, `meia-vida-atrofia` e `peso-piso` (veja Os sete estados).

### Pulso

- Um cometa: rastro que decai de `opacidade-rastro` a zero, quatro faíscas soltas da cauda e o glifo do tipo na cabeça, com núcleo quente nos glifos cheios. Raio = `pulso-<prioridade>`.
- Tempo de travessia interpolado pelo peso entre `travessia-fraca` e `travessia-forte`, dividido por `fator-<prioridade>`.
- Prioridade nunca muda a cor. Crítica é maior, mais rápida e com rastro mais longo, não vermelha.

### Plâncton e névoa

- `plancton-quantidade` pontos de `plancton` sobem devagar em duas profundidades, com paralaxe quando a vista anda. Brilham mais quanto mais neurônios estão acesos e piscam na cor da onda quando ela passa, como plâncton diante de um distúrbio.
- Cada região tem uma névoa de `campo-regiao`, sem borda. As duas coisas são ambiente: recuam com o foco e nunca carregam dado sozinhas.

### Tipografia

Sora para pessoas, cargos, rótulos e mensagens: geométrica e larga, futurista sem ficção científica. Space Mono para toda medida e todo identificador, como num console de bordo. As duas no Google Fonts.

- `titulo`: nome do agente na ficha, um por tela.
- `secao`: cabeçalho de bloco na ficha e na dica.
- `corpo`: texto das trocas, campo de mensagem.
- `rotulo`: filtros, selos, botões, cabeçalho.
- `leitura-destaque`: a ativação atual na ficha, um número por tela.
- `leitura`: pesos, porcentagens, horários, contadores e ids, inclusive sobre a rede.

Sem rede, as pilhas de fonte caem para `system-ui` e `ui-monospace`; para ficar sem dependência externa, sirva os arquivos das duas fontes junto de `index.html`.

### Espaço, raio, vidro e brilho

- Base de 4px: `espaco-1` a `espaco-6`. Gutter lateral no celular: `espaco-4` (16px). Nada rola na horizontal, exceto a fileira de filtros dentro dela mesma.
- Cantos macios: `raio-1` (campo, trilho), `raio-2` (dica, botões), `raio-3` (ficha flutuante, folha, grupo de zoom), `raio-pilula` (filtros, botão Ao vivo, trilhos).
- Vidro: fundo `vidro`, desfoque `desfoque-vidro`, fio `borda`, `sombra-flutuante` (ou `sombra-folha`). No escuro, a sombra leva um brilho violeta fraco; no claro, só sombra.
- Brilho: `brilho-acento` no que está ligado (Enviar, cabeça da linha do tempo). As pílulas do filtro brilham de leve na cor do próprio tipo quando ligadas.
- Foco: `anel-foco`, 2px na cor do fundo e 2px sólidos de `acento` (4,4:1 ou mais no escuro, 4,8:1 ou mais no claro), em todo controle e em cada neurônio.

### Layout

- A rede ocupa a tela inteira, até atrás do vidro. Por cima: o cabeçalho de `altura-cabecalho` no topo, a linha do tempo de `altura-linha-tempo` na base, a fileira de filtros em pílula logo acima dela e o grupo de zoom no canto superior direito, a `margem-flutuante` das bordas.
- Força dirigida, agrupada por região: nós da mesma região se atraem. Sinapses mais pesadas são molas mais curtas, então quem trabalha junto se aproxima devagar, ao vivo, e o layout da próxima sessão já parte do que a rede aprendeu.
- A ficha do agente só aparece com seleção: vidro flutuante de `largura-painel` à direita a partir de `quebra-folha`; abaixo disso, folha inferior flutuante até `altura-folha`. A rede se reencaixa no espaço livre e continua sendo a tela, a partir de `largura-minima`.
- Camadas: `z-controles`, `z-painel`, `z-dica`.

### Interação

- Ponteiro ou foco num neurônio: ele e os vizinhos ficam, com aro e sinapses em `acento`; o resto recua para `opacidade-recuo`. Aparecem os ids dele e dos vizinhos e a dica.
- Arrastar um neurônio: a física acorda e os vizinhos acompanham pelas molas; ao soltar, ele volta a assentar.
- Arrastar o fundo move a vista; roda ou pinça aproximam entre `zoom-min` e `zoom-max`; duplo clique ou a tecla 0 centralizam. No painel em tela cheia, a roda aproxima direto; embutida numa página, use `roda: 'ctrl'` para a página continuar rolando.
- A partir de `zoom-rotulos`, todos os ids aparecem sob os neurônios, esmaecendo na entrada.

### Movimento

Contínuo e lento no repouso: respiração de `respiracao` com fase diferente por neurônio (amplitude `respiro-escala`), fluxo de partículas e plâncton. Rápido e direcional na propagação. Transições em `transicao-ui` com `curva-saida`; cometas em `curva-travessia`. Nada compete com a leitura: com algo em foco, o resto recua.

Com `prefers-reduced-motion`, nada anda sozinho e a mesma informação continua legível: sem respiração, sem fluxo, sem plâncton à deriva; a sinapse em uso fica tingida no matiz do tipo com o glifo parado no meio, apontando o sentido; a onda vira um anel tracejado; coroa e núcleo continuam proporcionais. Arrastar e aproximar continuam, porque são gestos da pessoa.

### Os sete estados, em resumo

| Estado | O que se vê |
| --- | --- |
| Repouso | Pontos de grafo respirando em fases diferentes, sinapses finas pelo peso com partículas correndo, plâncton subindo |
| Estímulo | Anel de `msg-briefing` nasce no ponto de entrada e cruza a rede em `onda-estimulo`; o plâncton pisca em ciano quando ele passa |
| Ativação | Quem tem afinidade passa do limiar e acende, com coroa proporcional na cor do tráfego; quem não tem fica apagado e só treme |
| Propagação | Cometa com glifo e matiz do tipo corre pela sinapse, que vira filamento de luz, na velocidade do peso e da prioridade |
| Entrega | O neurônio pulsa uma vez e solta faíscas em `msg-entrega`, e o cometa volta pela mesma sinapse, no sentido contrário |
| Reforço | A sinapse que carregou trabalho útil clareia por `reforco` e fica mais espessa, com mais partículas, de vez |
| Atrofia | Sem uso, a sinapse afina pela `meia-vida-atrofia` até `peso-piso`, perde as partículas e nunca some |

O detalhe de cada um, com as fórmulas, está na seção Os sete estados; a rede completa, na seção Topologia.

## Acessibilidade

- Texto com 4,5:1 ou mais nos dois temas, em todas as bases que a nota do token cita, inclusive `vidro` sobre um neurônio aceso. Marcas com significado (neurônio em repouso, sinapse forte, glifos, anel de foco, borda de controle) com 3:1 ou mais. Exceções deliberadas e anotadas: `borda` (fio decorativo), `sinapse-fraca` e `sinapse-latente` (o dado é justamente quase sumir; o peso exato está na dica).
- Cada neurônio é um botão: Tab percorre, Enter abre a ficha, Esc limpa, + e − aproximam, 0 centraliza. O nome acessível traz cargo, região, ativação e grau.
- Linha do tempo como `slider`, filtro como botões de alternância, medidor como `meter`, estado do cabeçalho como `status`, grupo de zoom com botões rotulados.
- Alvos de toque com 24px ou mais; a área de toque do neurônio cresce com o zoom.

## Iconografia

- Sem biblioteca de ícones. Os tipos de mensagem são nove glifos geométricos (`MoviliRede.glifo(tipo)`, no SVG inline, ou o `SeloTipo`): anel, seta, círculo, losango vazado, losango cheio, quadrado, barra, triângulo e asterisco. Vazio = aberto; cheio = resolvido; traço = direção ou irradiação. Seta e barra giram com o sentido do cometa; o triângulo fica sempre em pé.
- Controles (reproduzir, pausar, passo, fechar, tema, aproximar, afastar, centralizar) são formas simples em SVG inline, traço de 1,5px em `currentColor`.
- Sem logotipo nas fontes deste sistema: a marca aparece como "Movili" em texto, peso 600, ao lado de "Rede" em `texto-suave`.

## O que não fazer

- Organograma com o chefe no topo, ou o `diretor` no centro por decreto. A rede não tem topo.
- Iconografia batida de IA: cérebro azul brilhante, placa de circuito, chuva de código verde, hexágonos, faíscas de "inteligência".
- Neon de ficção científica sem significado: grade em perspectiva, glitch, brilho em tudo. Aqui só brilha o que está ativo, ligado ou selecionado.
- Grafo bonito e estático. Se não pulsa, propaga e engrossa, não cumpriu o pedido.
- Nós todos iguais ou sinapses todas iguais.
- Texto permanente sobre o grafo no zoom inicial, cartões opacos em volta do grafo, caixas em volta das regiões.
- Vidro sem desfoque ou mais transparente que `vidro`: o texto perde o contraste sobre um neurônio aceso.
- Cor de tipo em neurônio parado, região, prioridade ou estado da interface; violeta de `acento` como tipo de mensagem.
- Esconder o que o filtro desliga: apague para `opacidade-apagado`.
