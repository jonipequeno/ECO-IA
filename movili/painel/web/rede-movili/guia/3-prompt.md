# Prompt para a interface em forma de rede neural

Prompt completo, com os dados da topologia já embutidos — copie de uma vez e cole em ferramenta de geração de interface (v0, Lovable, Claude, Cursor) ou entregue a um designer. No fim, um complemento amarra o resultado aos tokens deste sistema.

Todos os números vêm de `movili/agentes/` e `movili/core/mensagem.py`, extraídos por script. Regenere com:

```
python -c "
import sys; sys.path.insert(0,'.')
from movili import agentes as q
p = q.todos_os_perfis()
d = [(i,a) for i,x in p.items() for a in x.interlocutores if a != '*']
e = {tuple(sorted(t)) for t in d}
print(len(p),'agentes |',len(d),'declaracoes |',len(e),'arestas')"
```

## O prompt (copie daqui até o fim da seção)

Projete a interface de um painel que mostra uma empresa de software operada por 20 agentes de IA trabalhando juntos, em tempo real.

A metáfora central é uma rede neural viva — e ela é literal, não decorativa. Não é um organograma, não é um fluxograma, não é um grafo estático. Cada agente é um neurônio; as conexões entre eles são sinapses com peso; uma demanda que entra é um estímulo que propaga em ondas; o que dá certo reforça a sinapse, e ela fica permanentemente mais forte. A interface precisa deixar isso visível sem uma única legenda explicando.

### Os sete estados que a tela precisa expressar

1. **Repouso.** A rede está viva mas parada. As sinapses são tênues, os nós respiram devagar, em fases levemente diferentes para não pulsar em uníssono.
2. **Estímulo.** Uma demanda entra por um ponto. Um pulso nasce ali e se espalha.
3. **Ativação.** Cada neurônio tem um limiar. Os que têm afinidade com o estímulo ultrapassam esse limiar e acendem — com halo proporcional à intensidade, não binário. Os que ficam abaixo permanecem apagados e visivelmente inertes.
4. **Propagação.** A luz corre pela sinapse, do neurônio de origem ao de destino. A velocidade e a espessura do traço vêm do peso daquela conexão. Sinapse forte conduz rápido e grosso; sinapse fraca conduz devagar e fino.
5. **Entrega.** O neurônio termina o trabalho, pulsa uma vez e devolve pela mesma sinapse, em sentido contrário e em outro tom.
6. **Reforço.** A sinapse que carregou trabalho útil engrossa e clareia — e fica assim. A topologia de hoje é diferente da de ontem, e isso precisa ser perceptível ao longo das sessões.
7. **Atrofia.** Sinapse que passa muito tempo sem uso afina até quase sumir, sem nunca desaparecer de todo.

### A rede: 20 neurônios em 12 regiões

O número depois do nome é o grau — quantas sinapses o nó tem. Use isso como o tamanho do nó. A rede é assimétrica de propósito: `comercial` tem 11 sinapses e `prospeccao` tem 4, e essa diferença precisa saltar aos olhos.

```
REGIÃO              NEURÔNIO           PAPEL                                  GRAU
socios              socio_estrategia   Helena Vasconcelos — CSO                  5
                    socio_tecnologia   Gustavo Ribeiro — CTO                     6
diretoria           diretor            Ricardo Menezes — CEO                     9
produto             produto            Juliana Prado — Product Manager           9
                    projetos           Vinicius Rocha — Gerente de Projetos      7
                    design             Felipe Moraes — UX/UI                     4
engenharia          dev_backend        Rafael Andrade — Arquiteto/Backend       10
                    dev_frontend       Camila Reis — Frontend                    6
                    dev_mobile         Bruno Tavares — Mobile/DevOps/QA          7
dados               dados              Aline Ferraz — BI                         8
marketing           marketing          Larissa Monteiro — Head                   9
                    seo                Diego Barros — SEO                        4
                    copy               Marina Duarte — Copywriter                4
comercial           prospeccao         Thiago Nunes — SDR                        4
                    comercial          Eduardo Lima — Closer                    11
financeiro          financeiro         Patricia Souza — Controller               9
juridico            juridico           Roberto Aguiar — Contratos/LGPD           6
seguranca           seguranca          Daniel Okamoto — CISO/AppSec              6
pessoas             rh                 Sofia Nogueira — People                   5
sucesso_do_cliente  cs                 Marcelo Brito — Customer Success          5
```

### As 67 sinapses

Desenhe exatamente estas ligações. São 67 arestas entre 20 nós — 35% das ligações possíveis, então a rede é densa no centro e esgarçada na borda.

```
comercial-copy          comercial-cs            comercial-dados
comercial-dev_backend   comercial-financeiro    comercial-juridico
comercial-marketing     comercial-produto       comercial-projetos
comercial-prospeccao    comercial-socio_estrategia
copy-marketing          copy-prospeccao         copy-seo
cs-dados                cs-dev_mobile           cs-diretor
cs-produto
dados-financeiro        dados-juridico          dados-marketing
dados-produto           dados-seguranca         dados-seo
design-dev_frontend     design-dev_mobile       design-marketing
design-produto
dev_backend-dev_frontend    dev_backend-dev_mobile      dev_backend-diretor
dev_backend-financeiro      dev_backend-produto         dev_backend-projetos
dev_backend-rh              dev_backend-seguranca       dev_backend-socio_tecnologia
dev_frontend-dev_mobile     dev_frontend-marketing      dev_frontend-projetos
dev_frontend-seo
dev_mobile-diretor      dev_mobile-projetos     dev_mobile-seguranca
diretor-financeiro      diretor-juridico        diretor-projetos
diretor-rh              diretor-socio_estrategia    diretor-socio_tecnologia
financeiro-juridico     financeiro-marketing    financeiro-rh
financeiro-socio_estrategia financeiro-socio_tecnologia
juridico-prospeccao     juridico-seguranca
marketing-prospeccao    marketing-seo           marketing-socio_estrategia
produto-projetos        produto-rh              produto-seguranca
produto-socio_tecnologia
projetos-rh
seguranca-socio_tecnologia
socio_estrategia-socio_tecnologia
```

Duas características da topologia que a visualização precisa preservar:

- **19 dessas ligações são recíprocas** — os dois lados se declararam mutuamente. São as conexões mais fortes da casa (`comercial↔financeiro`, `dev_backend↔dev_frontend`, `marketing↔seo`, `socio_estrategia↔socio_tecnologia`). Desenhe-as visivelmente mais espessas desde o estado de repouso.
- **O CEO (`diretor`) é o único que se declara conectado a todos.** As 9 sinapses listadas acima são só as que os outros declararam com ele. Trate-o como um nó capaz de alcançar qualquer região — talvez com sinapses latentes, quase invisíveis, que só acendem quando usadas.

### Layout

Grafo de força dirigida, agrupado por região. As regiões são campos de gravidade, não caixas com borda: os nós de uma mesma região se atraem e formam um agrupamento orgânico, com limites difusos. Nada de retângulos aninhados.

A área da rede ocupa o corpo da tela. Em volta, o mínimo: um cabeçalho fino com o estado do sistema, e um painel lateral que só aparece quando algo é selecionado. Nada de cercar o grafo com cartões.

### O que trafega pelas sinapses

Nove tipos de mensagem, e o matiz do pulso vem do tipo:

```
briefing    demanda entrando na empresa
tarefa      atribuição direta a um agente
entrega     resultado de uma tarefa
pergunta    um agente pedindo informação a outro
resposta    retorno de uma pergunta
revisao     crítica ou aprovação de uma entrega
decisao     deliberação da liderança
alerta      risco, bloqueio ou erro
informe     comunicado geral (dispara para toda a rede de uma vez)
```

Quatro prioridades — `baixa`, `normal`, `alta`, `critica` — que modulam a intensidade e a velocidade do pulso.

### Cor e movimento

Base escura por padrão, com tema claro equivalente (não um mero inverso). A cor carrega significado, nunca enfeite:

- intensidade da luz = intensidade da ativação
- espessura e brilho da sinapse = peso aprendido
- matiz = tipo da mensagem que está passando

Paleta do produto, para manter coerência: fundo `#0e1117`, superfície `#161b22`, borda `#2a3441`, texto `#e6edf3`, acento `#4f9cf9`, sucesso `#3fb950`, atenção `#d29922`, erro `#f85149`.

O movimento é contínuo e lento no repouso, rápido e direcional na propagação. Nada de animação que compete com a leitura. Respeite `prefers-reduced-motion`: sem movimento, a mesma informação precisa continuar legível por cor, espessura e opacidade.

### Interação

- Passar o mouse num neurônio: nome, cargo, modelo que ele usa, ativação atual, e as sinapses dele realçadas enquanto o resto da rede recua.
- Clicar num neurônio: painel lateral com a ficha e um campo para falar direto com ele.
- Passar o mouse numa sinapse: peso atual e as últimas trocas que passaram por ali.
- Uma linha do tempo para rebobinar a propagação e ver a onda de novo, passo a passo.
- Filtro por tipo de mensagem, que apaga o que não interessa em vez de esconder.

### Restrições técnicas

- 60 fps com 20 nós e 67 arestas animando ao mesmo tempo.
- SVG ou Canvas, sem biblioteca pesada de grafo.
- Funciona a partir de 360px de largura: no celular, a rede continua sendo a tela principal, com o painel lateral virando folha inferior.
- Contraste mínimo 4.5:1 em todo texto, nos dois temas.
- Nenhuma informação transmitida só por cor.

### O que não fazer

- Organograma hierárquico com o chefe no topo. A rede não tem topo.
- Iconografia batida de "IA": cérebro azul brilhante, placa de circuito, chuva de código verde, hexágonos.
- Grafo bonito e estático. Se não pulsa, propaga e engrossa, não cumpriu o pedido.
- Nós todos iguais. A assimetria é o dado — respeite os graus da tabela.
- Texto sobre o grafo. Rótulo aparece na interação, não permanentemente.

## Complemento: amarrar ao design system

Acrescente ao fim do prompt quando o resultado precisar seguir este sistema, na direção obsidiana bioluminescente (os valores vêm de `tokens.json`). Ele troca a paleta do produto do prompt:

```
Use o design system Rede Movili: obsidiana bioluminescente, com a interação de uma visão de grafo de notas.
Escuro primeiro: fundo #0b0a10, superfície #15141c, vidro #15141c a 92% com desfoque de 18px, borda #2b2936,
texto #ece9f5, texto suave #a7a2b8, acento violeta #8b6cf6 (só seleção e foco), sucesso #3ddc97, atenção #f2b84b, erro #ff5d73.
Claro equivalente: fundo #faf9fd, superfície #ffffff, texto #1c1a24, texto suave #5b566d, acento #6a4fe0.
A rede ocupa a tela inteira; cabeçalho (44px), filtros em pílula, linha do tempo (48px) e ficha (360px) são vidro por cima.
Neurônio parado = ponto sólido #6a6484. Aceso = núcleo branco #f6f3ff e coroa de até 3,2× o raio na cor do tráfego
que ele processa (no claro: núcleo de tinta e anéis concêntricos na cor do tipo).
Matiz e glifo por tipo (escuro / claro): briefing anel #40e2f3 / #007887 · tarefa seta #65adff / #1c65c8 ·
entrega círculo cheio = sucesso · pergunta losango vazado #eb76e9 / #9b259b · resposta losango cheio #ff9fc4 / #c95a8b ·
revisão quadrado #cfef54 / #607700 · decisão barra #ffb04a / #a45e00 · alerta triângulo = erro · informe asterisco #d5d1e6 / #646073.
Raio do nó = 3,6 × grau^0,7 (grau 4 = 9,5px, grau 11 = 19,3px).
Sinapse fina: 0,5px a 3px e de #26242f a #a49ec0 pelo peso, com até 3 partículas correndo (7,2 s a 3 s por travessia);
conduzindo, vira filamento na cor do tipo. Peso inicial 0,55 recíproca, 0,30 unilateral, 0,03 latente;
reforço += 0,12 × (1 − peso); atrofia com meia-vida de 10 dias até 0,06.
Pulso = cometa com faíscas: raio 4 / 5 / 6,5 / 8px por prioridade; travessia de 1800ms a 420ms, dividida por 0,6 / 1 / 1,5 / 2,2.
Fundo com 72 pontos de plâncton que sobem, acendem com a atividade e piscam quando a onda passa.
Interação de grafo: arrastar nós com física, arrastar o fundo, zoom de 0,5× a 3× (rótulos de todos a partir de 1,6×),
foco destaca o nó e os vizinhos em violeta e recua o resto para 15%.
Tipografia: Sora para texto, Space Mono para números e ids.
```

## Variações

**Para gerador de imagem (Midjourney, Ideogram):** corte as seções de interação, restrições técnicas e a lista de arestas — gerador de imagem não segue topologia explícita. Mantenha os sete estados e acrescente:

> Visualização de tela única, vista de cima, fundo escuro quase preto. Rede orgânica assimétrica de 20 nós luminosos agrupados em regiões difusas, ligados por filamentos de espessura desigual. Alguns nós intensamente acesos com halo, outros apagados. Rastros de luz correndo por alguns filamentos. Um nó claramente mais conectado que os outros, e alguns na periferia com uma ou duas ligações. Estética de instrumento científico, não de ficção científica. Sem texto, sem ícones, sem cérebro.

**Para Figma / design estático:** peça três quadros em vez de um — repouso, meio da propagação e depois do reforço — lado a lado. A diferença entre o primeiro e o terceiro quadro é o que prova que a ideia funciona.

**Para gerador de código:** acrescente o stack desejado. Se quiser espelhar o painel atual (`movili/painel/web/index.html`), peça arquivo único em HTML + CSS + JS puro, sem build e sem dependência.

## Por que o prompt é assim

**Estados antes de estética.** Ferramenta de geração entrega grafo bonito e morto se você pedir "interface de rede neural". Descrever os sete estados força o movimento a carregar informação.

**Topologia explícita, não adjetivo.** "Rede assimétrica" produz um grafo simétrico de nós genéricos. A tabela de graus e a lista das 67 arestas produzem a rede real — com `comercial` e `dev_backend` como concentradores e `copy`, `seo`, `design` e `prospeccao` na borda.

**Lista do que evitar.** Metade do trabalho de um prompt visual é fechar as portas óbvias. "Cérebro azul brilhante" e "organograma com o chefe no topo" são exatamente para onde a ferramenta vai sozinha.
