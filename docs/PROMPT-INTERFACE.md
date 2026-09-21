# Prompt para a interface em forma de rede neural

Prompt pronto para colar em ferramenta de geração de interface (v0, Lovable, Claude,
Cursor) ou entregar a um designer. Está fundamentado na topologia real do projeto — os
números, nomes e tipos abaixo saem de `movili/agentes/` e `movili/core/mensagem.py`, não
são inventados.

Depois do prompt há uma seção com as variações (imagem estática, Figma) e os dados
completos para colar junto.

---

## O prompt

> Projete a interface de um painel que mostra uma empresa de software operada por 20
> agentes de IA trabalhando juntos, em tempo real.
>
> **A metáfora central é uma rede neural viva — e ela é literal, não decorativa.**
> Não é um organograma, não é um fluxograma, não é um grafo estático. Cada agente é um
> neurônio; as conexões entre eles são sinapses com peso; uma demanda que entra é um
> estímulo que propaga em ondas; o que dá certo reforça a sinapse, e ela fica
> permanentemente mais forte. A interface precisa deixar isso visível sem uma única
> legenda explicando.
>
> ### Os sete estados que a tela precisa expressar
>
> 1. **Repouso.** A rede está viva mas parada. As sinapses são tênues, os nós respiram
>    devagar, em fases levemente diferentes para não pulsar em uníssono.
> 2. **Estímulo.** Uma demanda entra por um ponto. Um pulso nasce ali e se espalha.
> 3. **Ativação.** Cada neurônio tem um limiar. Os que têm afinidade com o estímulo
>    ultrapassam esse limiar e acendem — com halo proporcional à intensidade, não
>    binário. Os que ficam abaixo permanecem apagados e visivelmente inertes.
> 4. **Propagação.** A luz corre pela sinapse, do neurônio de origem ao de destino. A
>    velocidade e a espessura do traço vêm do peso daquela conexão. Sinapse forte conduz
>    rápido e grosso; sinapse fraca conduz devagar e fino.
> 5. **Entrega.** O neurônio termina o trabalho, pulsa uma vez e devolve pela mesma
>    sinapse, em sentido contrário e em outro tom.
> 6. **Reforço.** A sinapse que carregou trabalho útil engrossa e clareia — e **fica
>    assim**. A topologia de hoje é diferente da de ontem, e isso precisa ser perceptível
>    ao longo das sessões.
> 7. **Atrofia.** Sinapse que passa muito tempo sem uso afina até quase sumir, sem nunca
>    desaparecer de todo.
>
> ### Layout
>
> Grafo de força dirigida, agrupado por setor. Os setores são **regiões de gravidade**,
> não caixas com borda: os nós de um mesmo setor se atraem e formam um agrupamento
> orgânico, com limites difusos. Nada de retângulos aninhados.
>
> O tamanho do nó vem do grau (quantas sinapses ele tem). A rede é assimétrica de
> propósito — há concentradores óbvios e há periferia.
>
> A área da rede ocupa o corpo da tela. Em volta, o mínimo: um cabeçalho fino com o
> estado do sistema, e um painel lateral que só aparece quando algo é selecionado. Nada
> de cercar o grafo com cartões.
>
> ### Cor e movimento
>
> Base escura por padrão, com tema claro equivalente (não um mero inverso). A cor
> carrega **significado**, nunca enfeite:
>
> - intensidade da luz = intensidade da ativação
> - espessura e brilho da sinapse = peso aprendido
> - matiz = natureza do que trafega (tarefa, entrega, pergunta, decisão, alerta)
>
> Sugestão de base, para manter coerência com o produto: fundo `#0e1117`, superfície
> `#161b22`, borda `#2a3441`, texto `#e6edf3`, acento `#4f9cf9`, sucesso `#3fb950`,
> atenção `#d29922`, erro `#f85149`.
>
> O movimento é contínuo e lento no repouso, rápido e direcional na propagação. Nada de
> animação que compete com a leitura. Respeite `prefers-reduced-motion`: sem movimento,
> a mesma informação precisa continuar legível por cor, espessura e opacidade.
>
> ### Interação
>
> - Passar o mouse num neurônio: nome, cargo, modelo que ele usa, ativação atual, e as
>   sinapses dele realçadas enquanto o resto da rede recua.
> - Clicar num neurônio: painel lateral com a ficha e um campo para falar direto com ele.
> - Passar o mouse numa sinapse: peso atual e as últimas trocas que passaram por ali.
> - Uma linha do tempo para rebobinar a propagação e ver a onda de novo, passo a passo.
> - Filtro por tipo de mensagem, que apaga o que não interessa em vez de esconder.
>
> ### Restrições técnicas
>
> - 60 fps com 20 nós e 86 arestas animando ao mesmo tempo.
> - SVG ou Canvas, sem biblioteca pesada de grafo.
> - Funciona a partir de 360px de largura: no celular, a rede continua sendo a tela
>   principal, com o painel lateral virando folha inferior.
> - Contraste mínimo 4.5:1 em todo texto, nos dois temas.
> - Nenhuma informação transmitida só por cor.
>
> ### O que não fazer
>
> - Organograma hierárquico com o chefe no topo. A rede não tem topo.
> - Iconografia batida de "IA": cérebro azul brilhante, placa de circuito, chuva de
>   código verde, hexágonos.
> - Grafo bonito e estático. Se não pulsa, propaga e engrossa, não cumpriu o pedido.
> - Nós todos iguais. A assimetria é o dado.
> - Texto sobre o grafo. Rótulo aparece na interação, não permanentemente.

---

## Os dados reais, para colar junto

Cole isto no fim do prompt para a interface sair com a topologia verdadeira:

```
20 agentes em 12 setores:

socios              Helena Vasconcelos (CSO), Gustavo Ribeiro (CTO)
diretoria           Ricardo Menezes (CEO)
produto             Juliana Prado (PM), Vinicius Rocha (PMO), Felipe Moraes (UX/UI)
engenharia          Rafael Andrade (arquiteto/backend), Camila Reis (frontend),
                    Bruno Tavares (mobile/DevOps/QA)
dados               Aline Ferraz (BI)
marketing           Larissa Monteiro (head), Diego Barros (SEO), Marina Duarte (copy)
comercial           Thiago Nunes (SDR), Eduardo Lima (closer)
financeiro          Patricia Souza (controller)
juridico            Roberto Aguiar (contratos/LGPD)
seguranca           Daniel Okamoto (CISO/AppSec)
pessoas             Sofia Nogueira (People)
sucesso do cliente  Marcelo Brito (CS)

86 conexões declaradas, 22,6% das ligações possíveis.

Grau de cada nó (tamanho visual):
  comercial 15 · marketing 13 · dev_backend 13 · produto 13 · financeiro 12
  diretor 9 · ... · rh 5 (o menor)

Tipos de mensagem que trafegam pelas sinapses (matiz):
  briefing · tarefa · entrega · pergunta · resposta · revisao · decisao · alerta · informe

Prioridades (intensidade): baixa · normal · alta · critica
```

---

## Variações

**Para gerador de imagem** (Midjourney, Ideogram): corte as seções de interação e
restrições técnicas, e acrescente no fim:

> Visualização de tela única, vista de cima, fundo escuro quase preto. Rede orgânica
> assimétrica de 20 nós luminosos agrupados em regiões difusas, ligados por filamentos
> de espessura desigual. Alguns nós intensamente acesos com halo, outros apagados.
> Rastros de luz correndo por alguns filamentos. Estética de instrumento científico, não
> de ficção científica. Sem texto, sem ícones, sem cérebro.

**Para Figma / design estático**: peça três quadros em vez de um — repouso, meio da
propagação e depois do reforço — lado a lado. A diferença entre o primeiro e o terceiro
quadro é o que prova que a ideia funciona.

**Para gerador de código**: acrescente o stack desejado e peça arquivo único sem build,
se quiser espelhar o painel atual (`movili/painel/web/index.html`, HTML + CSS + JS puro,
sem dependência).

---

## Por que o prompt é assim

Três decisões que fazem diferença no resultado:

**Estados antes de estética.** Ferramenta de geração entrega grafo bonito e morto se você
pedir "interface de rede neural". Descrever os sete estados força o movimento a carregar
informação.

**Dados reais no prompt.** Com os nomes, setores e graus verdadeiros, a saída já nasce
com a assimetria certa. Sem eles, vem um grafo simétrico de nós genéricos.

**Lista do que evitar.** Metade do trabalho de um prompt visual é fechar as portas
óbvias. "Cérebro azul brilhante" e "organograma com o chefe no topo" são exatamente para
onde a ferramenta vai sozinha.
