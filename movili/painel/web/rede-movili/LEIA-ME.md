# Kit Rede Movili

Os arquivos do design system Rede Movili prontos para o painel em `movili/painel/web/rede-movili/`, gerados em 21/09/2026.

| Arquivo | O que é |
| --- | --- |
| `tokens.css` | Variáveis de design compiladas de `tokens.json`: temas escuro e claro, tipografia, espaços, tempos |
| `bundle.css` | Estilos dos componentes; importa Sora e Space Mono do Google Fonts |
| `bundle.js` | Componentes em JavaScript puro, sem build e sem dependências; publica `window.MoviliRede` |
| `index.d.ts` | A API documentada em tipos |
| `tokens.json` | A fonte dos tokens |
| `README.md` | As regras visuais e de voz |
| `guia/` | Os sete estados, a topologia de referência e o prompt de geração |
| `exemplo.html` | A tela completa em modo demonstração; abra no navegador |
| `PROMPT-INTEGRACAO.md` | O prompt para um agente de código integrar o kit ao painel |

Ordem de carga: `tokens.css`, `bundle.css`, `bundle.js`. O `<html>` recebe `data-theme="escuro"` ou `"claro"`.

Não edite estes arquivos no projeto: mudanças visuais voltam para o design system, que gera um kit novo.
