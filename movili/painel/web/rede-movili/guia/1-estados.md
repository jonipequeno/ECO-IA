# Os sete estados

Como cada estado aparece, com os tokens e as fórmulas que a `Rede` usa. O estado da rede é função do tempo: dados os eventos e os pesos iniciais, o quadro no instante t é sempre o mesmo. É isso que deixa a linha do tempo rebobinar a onda com fidelidade, pesos incluídos.

## 1. Repouso

A rede está viva, mas parada.

- Cada neurônio é um ponto de grafo em `neuronio` e respira: raio × (1 + `respiro-escala` × sen(2π · (t / `respiracao` + fase))), com a fase tirada do id. Ninguém pulsa em uníssono; o reflexo interno clareia de leve no pico.
- Sinapses no peso atual, finas. Por elas correm round(`particulas-max` × peso) partículas, de `fluxo-lento` a `fluxo-rapido`: a sinapse forte tem mais vida mesmo parada.
- Ao fundo, `plancton-quantidade` pontos de `plancton` sobem devagar em duas profundidades; brilham mais quanto mais neurônios estão acesos.
- Regiões como névoa `campo-regiao`. Nenhum rótulo no zoom inicial.

## 2. Estímulo

Uma demanda entra por um ponto: `rede.controle.estimular({ no, afinidade, texto })`.

- Um anel de `msg-briefing` nasce no neurônio de entrada e cresce até passar do mais distante em `onda-estimulo`, com opacidade (1 − p)^1,4. No escuro, leva um brilho largo e fraco; no claro, só o traço de `traco-onda`.
- O plâncton que a frente da onda cruza pisca na cor dela, como plâncton de verdade diante de um distúrbio.
- A onda chega a cada neurônio em t₀ + (distância ÷ alcance) × `onda-estimulo`.
- A entrada vira um evento Briefing na linha do tempo e é anunciada na região `aria-live`.

## 3. Ativação

Cada neurônio tem um limiar: o do perfil ou `limiar-padrao`.

- Quando a onda chega e a afinidade passa do limiar, o neurônio acende: sobe em 180 ms até a afinidade, segura 2,4 s e apaga com constante `decaimento-ativacao`.
- Abaixo do limiar, fica apagado e visivelmente inerte: o contorno treme até 60% da afinidade e volta em um terço do tempo.
- Coroa: raio × (1 + (`halo-max` − 1) × ativação), opacidade proporcional, nunca binária, na cor do tráfego que mais o excita agora (ciano do briefing que o acendeu, azul de uma tarefa, magenta de uma pergunta). O núcleo acende branco em `ativacao`; no claro, escurece em tinta e a coroa vira anéis na cor do tipo.
- Participar de uma mensagem acende de novo: quem manda chega a 0,8 e quem recebe a 0,74. Tarefa e pergunta seguram 3,6 s (quem pediu espera, quem recebeu trabalha); o resto, 1,2 s.

## 4. Propagação

Cada mensagem: `rede.controle.registrar({ tipo, de, para, prioridade, texto })`.

- Tempo de travessia = interpolação de `travessia-fraca` (peso no piso) a `travessia-forte` (peso 1), dividido por `fator-<prioridade>`.
- O pulso é um cometa: a cabeça anda com `curva-travessia`; o rastro tem cerca de 46px × escala da prioridade e decai de `opacidade-rastro` a zero; quatro faíscas se soltam da cauda.
- Glifo e matiz do tipo, raio `pulso-<prioridade>`, núcleo quente nos glifos cheios. Seta e barra giram com o sentido.
- A sinapse vira um filamento de luz na cor do tipo enquanto conduz. Uma latente do `diretor` aparece só nesse momento.

## 5. Entrega

- O neurônio que termina pulsa uma vez: um anel de `msg-entrega` sai da borda e cresce até 2,3 vezes o raio em `pulso-entrega`, soltando sete faíscas.
- Na metade desse tempo, o pulso de entrega parte pela mesma sinapse, no sentido contrário ao da tarefa, em `msg-entrega` e com o glifo círculo cheio.

## 6. Reforço

- Ao chegar uma entrega, resposta, revisão ou decisão, a sinapse que a carregou ganha peso ← peso + `taxa-reforco` × (1 − peso).
- Por `reforco`, ela clareia na direção de `ativacao` e fica 1,4px mais larga; depois assenta mais espessa, mais clara e com mais partículas que antes, de vez.
- O peso é a mola do layout (comprimento ∝ 1,25 − 0,55 × peso). Ao vivo, a física acorda de leve a cada reforço e quem trabalha junto se aproxima devagar.
- Persistência: guarde `rede.controle.pesos()` ao fim da sessão e passe em `Rede({ pesos })` na próxima; o layout de amanhã já parte do que a rede aprendeu.

## 7. Atrofia

- Sem uso, o peso cai: piso + (peso − piso) × 0,5^(Δt ÷ `meia-vida-atrofia`).
- O piso é `peso-piso` para as declaradas e `peso-latente` para as latentes. A sinapse afina até quase sumir, sem sumir, e perde as partículas.
- Na demonstração, um dia dura 60 s, para a atrofia caber numa sessão.

## Informe

Um comunicado geral sai do remetente para a rede inteira de uma vez: uma onda de `msg-informe` em `onda-informe`, pulsos por todas as sinapses do remetente chegando junto com ela, e um reconhecimento breve (0,45 por 200 ms) em cada neurônio que a onda alcança.

## Interação

- **Ponteiro ou foco num neurônio**: ele, as sinapses dele e os vizinhos ficam, com aro e sinapses em `acento`; o resto recua para `opacidade-recuo` em `transicao-ui`. Aparecem os ids dele (em `texto`) e dos vizinhos (em `texto-suave`) e a dica com nome, cargo, modelo, o que está processando, ativação e grau.
- **Arrastar um neurônio**: ele fica preso ao ponteiro, a física acorda e os vizinhos acompanham pelas molas; ao soltar, ele volta a assentar. A dica some durante o arrasto.
- **Vista**: arrastar o fundo move; roda, pinça, + e − aproximam entre `zoom-min` e `zoom-max`; duplo clique ou 0 centralizam. A partir de `zoom-rotulos`, os ids de todos aparecem.
- **Ponteiro numa sinapse**: ela fica, o resto recua; a dica mostra o peso e as últimas três trocas.
- **Clique ou Enter**: seleciona (anel `acento`) e abre a ficha. Esc limpa.
- **Filtro**: os pulsos dos tipos desligados caem para `opacidade-apagado`, na rede e na linha do tempo.
- **Linha do tempo**: arrastar, passo a passo (cada passo para no meio de uma mensagem), reproduzir até alcançar o presente, voltar ao vivo.

## Sem movimento

Com `prefers-reduced-motion`, a rede redesenha quatro vezes por segundo e nada anda sozinho: sem respiração, sem partículas, plâncton parado; o cometa vira a sinapse inteira tingida no matiz do tipo com o glifo parado no meio, apontando o sentido; a onda vira um anel tracejado ao redor da entrada; coroa e núcleo continuam proporcionais à ativação. Cor, espessura, opacidade e glifo seguem carregando tudo. Arrastar e aproximar continuam: são gestos da pessoa.
