# Topologia

A rede real, extraída de `movili/agentes/`: 20 neurônios em 12 regiões, 67 sinapses. É isso que a `Rede` desenha quando não recebe `dados`.

## Neurônios

O grau é o número de sinapses declaradas e define o raio (`raio-grau-*`). A contagem foi refeita a partir da lista de sinapses e bate com a tabela.

| Região | Neurônio | Papel | Grau | Raio |
| --- | --- | --- | --- | --- |
| socios | `socio_estrategia` | Helena Vasconcelos, CSO | 5 | 11,1px |
| socios | `socio_tecnologia` | Gustavo Ribeiro, CTO | 6 | 12,6px |
| diretoria | `diretor` | Ricardo Menezes, CEO | 9 | 16,8px |
| produto | `produto` | Juliana Prado, Product Manager | 9 | 16,8px |
| produto | `projetos` | Vinicius Rocha, Gerente de Projetos | 7 | 14,1px |
| produto | `design` | Felipe Moraes, UX/UI | 4 | 9,5px |
| engenharia | `dev_backend` | Rafael Andrade, Arquiteto/Backend | 10 | 18px |
| engenharia | `dev_frontend` | Camila Reis, Frontend | 6 | 12,6px |
| engenharia | `dev_mobile` | Bruno Tavares, Mobile/DevOps/QA | 7 | 14,1px |
| dados | `dados` | Aline Ferraz, BI | 8 | 15,4px |
| marketing | `marketing` | Larissa Monteiro, Head | 9 | 16,8px |
| marketing | `seo` | Diego Barros, SEO | 4 | 9,5px |
| marketing | `copy` | Marina Duarte, Copywriter | 4 | 9,5px |
| comercial | `prospeccao` | Thiago Nunes, SDR | 4 | 9,5px |
| comercial | `comercial` | Eduardo Lima, Closer | 11 | 19,3px |
| financeiro | `financeiro` | Patricia Souza, Controller | 9 | 16,8px |
| juridico | `juridico` | Roberto Aguiar, Contratos/LGPD | 6 | 12,6px |
| seguranca | `seguranca` | Daniel Okamoto, CISO/AppSec | 6 | 12,6px |
| pessoas | `rh` | Sofia Nogueira, People | 5 | 11,1px |
| sucesso_do_cliente | `cs` | Marcelo Brito, Customer Success | 5 | 11,1px |

Concentradores: `comercial` (11) e `dev_backend` (10). Na borda: `design`, `seo`, `copy` e `prospeccao` (4).

## As 67 sinapses

67 de 190 ligações possíveis (35%): densa no centro, esgarçada na borda.

```
comercial-copy            comercial-cs              comercial-dados
comercial-dev_backend     comercial-financeiro      comercial-juridico
comercial-marketing       comercial-produto         comercial-projetos
comercial-prospeccao      comercial-socio_estrategia
copy-marketing            copy-prospeccao           copy-seo
cs-dados                  cs-dev_mobile             cs-diretor
cs-produto
dados-financeiro          dados-juridico            dados-marketing
dados-produto             dados-seguranca           dados-seo
design-dev_frontend       design-dev_mobile         design-marketing
design-produto
dev_backend-dev_frontend  dev_backend-dev_mobile    dev_backend-diretor
dev_backend-financeiro    dev_backend-produto       dev_backend-projetos
dev_backend-rh            dev_backend-seguranca     dev_backend-socio_tecnologia
dev_frontend-dev_mobile   dev_frontend-marketing    dev_frontend-projetos
dev_frontend-seo
dev_mobile-diretor        dev_mobile-projetos       dev_mobile-seguranca
diretor-financeiro        diretor-juridico          diretor-projetos
diretor-rh                diretor-socio_estrategia  diretor-socio_tecnologia
financeiro-juridico       financeiro-marketing      financeiro-rh
financeiro-socio_estrategia                         financeiro-socio_tecnologia
juridico-prospeccao       juridico-seguranca
marketing-prospeccao      marketing-seo             marketing-socio_estrategia
produto-projetos          produto-rh                produto-seguranca
produto-socio_tecnologia
projetos-rh
seguranca-socio_tecnologia
socio_estrategia-socio_tecnologia
```

## Recíprocas

19 sinapses são recíprocas: os dois lados se declararam. Começam em `peso-reciproca` e aparecem mais espessas desde o repouso. Estas quatro são conhecidas:

- `comercial` ↔ `financeiro`
- `dev_backend` ↔ `dev_frontend`
- `marketing` ↔ `seo`
- `socio_estrategia` ↔ `socio_tecnologia`

As outras 15 saem dos perfis. Este script conta tudo e lista os 19 pares; o esperado é 20 agentes, 86 declarações (67 + 19), 67 arestas, 19 recíprocas:

```
python -c "
import sys; sys.path.insert(0,'.')
from movili import agentes as q
p = q.todos_os_perfis()
d = [(i,a) for i,x in p.items() for a in x.interlocutores if a != '*']
s = set(d)
e = {tuple(sorted(t)) for t in d}
r = sorted({tuple(sorted(t)) for t in d if t[::-1] in s})
print(len(p),'agentes |',len(d),'declaracoes |',len(e),'arestas |',len(r),'reciprocas')
print(r)"
```

Passe a lista para a rede: `MoviliRede.Rede({ dados: { reciprocas: [['comercial', 'financeiro'], …] } })`.

## Latentes do diretor

O `diretor` é o único que declara `interlocutores = '*'`. As 9 sinapses dele na lista são as que os outros declararam: `cs`, `dev_backend`, `dev_mobile`, `financeiro`, `juridico`, `projetos`, `rh`, `socio_estrategia`, `socio_tecnologia`.

As outras 10 ficam latentes, em `sinapse-latente` e `peso-latente`: `produto`, `design`, `dev_frontend`, `dados`, `marketing`, `seo`, `copy`, `prospeccao`, `comercial`, `seguranca`. Acendem quando carregam uma mensagem e, se o trabalho for útil, são reforçadas como qualquer outra: a latente que o diretor usa de verdade vai aparecendo.

## Tráfego

Os nove tipos vêm de `movili/core/mensagem.py`:

| Tipo | Significado | Glifo |
| --- | --- | --- |
| `briefing` | demanda entrando na empresa | anel |
| `tarefa` | atribuição direta a um agente | seta |
| `entrega` | resultado de uma tarefa | círculo cheio |
| `pergunta` | um agente pedindo informação a outro | losango vazado |
| `resposta` | retorno de uma pergunta | losango cheio |
| `revisao` | crítica ou aprovação de uma entrega | quadrado |
| `decisao` | deliberação da liderança | barra |
| `alerta` | risco, bloqueio ou erro | triângulo |
| `informe` | comunicado geral, para toda a rede de uma vez | asterisco |

Prioridades: `baixa`, `normal`, `alta`, `critica`.
