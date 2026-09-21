/* @ds-bundle: {"format":4,"namespace":"MoviliRede","components":[{"name":"Rede"},{"name":"Neuronio"},{"name":"Sinapse"},{"name":"Pulso"},{"name":"Tela"},{"name":"Cabecalho"},{"name":"PainelAgente"},{"name":"Dica"},{"name":"LinhaDoTempo"},{"name":"FiltroTipos"},{"name":"SeloTipo"},{"name":"SeloPrioridade"},{"name":"MedidorAtivacao"}]} */
/* Rede Movili: JavaScript puro, sem dependências. Expõe window.MoviliRede. */
(function () {
  'use strict';
  var doc = document;
  var TAU = Math.PI * 2;

  /* =====================================================================
     Topologia: extraída de movili/agentes/ (20 agentes, 12 regiões, 67 sinapses)
     ===================================================================== */
  var REGIOES = [
    { id: 'socios', nome: 'Sócios' },
    { id: 'diretoria', nome: 'Diretoria' },
    { id: 'produto', nome: 'Produto' },
    { id: 'engenharia', nome: 'Engenharia' },
    { id: 'dados', nome: 'Dados' },
    { id: 'marketing', nome: 'Marketing' },
    { id: 'comercial', nome: 'Comercial' },
    { id: 'financeiro', nome: 'Financeiro' },
    { id: 'juridico', nome: 'Jurídico' },
    { id: 'seguranca', nome: 'Segurança' },
    { id: 'pessoas', nome: 'Pessoas' },
    { id: 'sucesso_do_cliente', nome: 'Sucesso do cliente' }
  ];
  var AGENTES = [
    { id: 'socio_estrategia', regiao: 'socios', nome: 'Helena Vasconcelos', cargo: 'CSO', grau: 5 },
    { id: 'socio_tecnologia', regiao: 'socios', nome: 'Gustavo Ribeiro', cargo: 'CTO', grau: 6 },
    { id: 'diretor', regiao: 'diretoria', nome: 'Ricardo Menezes', cargo: 'CEO', grau: 9 },
    { id: 'produto', regiao: 'produto', nome: 'Juliana Prado', cargo: 'Product Manager', grau: 9 },
    { id: 'projetos', regiao: 'produto', nome: 'Vinicius Rocha', cargo: 'Gerente de Projetos', grau: 7 },
    { id: 'design', regiao: 'produto', nome: 'Felipe Moraes', cargo: 'UX/UI', grau: 4 },
    { id: 'dev_backend', regiao: 'engenharia', nome: 'Rafael Andrade', cargo: 'Arquiteto/Backend', grau: 10 },
    { id: 'dev_frontend', regiao: 'engenharia', nome: 'Camila Reis', cargo: 'Frontend', grau: 6 },
    { id: 'dev_mobile', regiao: 'engenharia', nome: 'Bruno Tavares', cargo: 'Mobile/DevOps/QA', grau: 7 },
    { id: 'dados', regiao: 'dados', nome: 'Aline Ferraz', cargo: 'BI', grau: 8 },
    { id: 'marketing', regiao: 'marketing', nome: 'Larissa Monteiro', cargo: 'Head de Marketing', grau: 9 },
    { id: 'seo', regiao: 'marketing', nome: 'Diego Barros', cargo: 'SEO', grau: 4 },
    { id: 'copy', regiao: 'marketing', nome: 'Marina Duarte', cargo: 'Copywriter', grau: 4 },
    { id: 'prospeccao', regiao: 'comercial', nome: 'Thiago Nunes', cargo: 'SDR', grau: 4 },
    { id: 'comercial', regiao: 'comercial', nome: 'Eduardo Lima', cargo: 'Closer', grau: 11 },
    { id: 'financeiro', regiao: 'financeiro', nome: 'Patricia Souza', cargo: 'Controller', grau: 9 },
    { id: 'juridico', regiao: 'juridico', nome: 'Roberto Aguiar', cargo: 'Contratos/LGPD', grau: 6 },
    { id: 'seguranca', regiao: 'seguranca', nome: 'Daniel Okamoto', cargo: 'CISO/AppSec', grau: 6 },
    { id: 'rh', regiao: 'pessoas', nome: 'Sofia Nogueira', cargo: 'People', grau: 5 },
    { id: 'cs', regiao: 'sucesso_do_cliente', nome: 'Marcelo Brito', cargo: 'Customer Success', grau: 5 }
  ];
  var LISTA_SINAPSES =
    'comercial-copy comercial-cs comercial-dados comercial-dev_backend comercial-financeiro comercial-juridico ' +
    'comercial-marketing comercial-produto comercial-projetos comercial-prospeccao comercial-socio_estrategia ' +
    'copy-marketing copy-prospeccao copy-seo cs-dados cs-dev_mobile cs-diretor cs-produto ' +
    'dados-financeiro dados-juridico dados-marketing dados-produto dados-seguranca dados-seo ' +
    'design-dev_frontend design-dev_mobile design-marketing design-produto ' +
    'dev_backend-dev_frontend dev_backend-dev_mobile dev_backend-diretor dev_backend-financeiro dev_backend-produto ' +
    'dev_backend-projetos dev_backend-rh dev_backend-seguranca dev_backend-socio_tecnologia ' +
    'dev_frontend-dev_mobile dev_frontend-marketing dev_frontend-projetos dev_frontend-seo ' +
    'dev_mobile-diretor dev_mobile-projetos dev_mobile-seguranca ' +
    'diretor-financeiro diretor-juridico diretor-projetos diretor-rh diretor-socio_estrategia diretor-socio_tecnologia ' +
    'financeiro-juridico financeiro-marketing financeiro-rh financeiro-socio_estrategia financeiro-socio_tecnologia ' +
    'juridico-prospeccao juridico-seguranca marketing-prospeccao marketing-seo marketing-socio_estrategia ' +
    'produto-projetos produto-rh produto-seguranca produto-socio_tecnologia projetos-rh ' +
    'seguranca-socio_tecnologia socio_estrategia-socio_tecnologia';
  /* 19 sinapses são recíprocas; o prompt nomeia só estas 4. As outras 15 saem do script em movili/agentes/. */
  var RECIPROCAS_CONHECIDAS = [
    ['comercial', 'financeiro'], ['dev_backend', 'dev_frontend'], ['marketing', 'seo'], ['socio_estrategia', 'socio_tecnologia']
  ];
  /* Quem declara interlocutores = '*' alcança todos: as ligações não declaradas pelo outro lado ficam latentes. */
  var DECLARA_TODOS = ['diretor'];

  function chave(a, b) { return a < b ? a + '|' + b : b + '|' + a; }

  function montarTopologia(dados) {
    dados = dados || {};
    var regioes = (dados.regioes || REGIOES).map(function (r) { return { id: r.id, nome: r.nome }; });
    var agentes = (dados.agentes || AGENTES).map(function (a) {
      var c = {}; for (var k in a) c[k] = a[k]; return c;
    });
    var pares = dados.sinapses || LISTA_SINAPSES.split(' ').map(function (s) { return s.split('-'); });
    var rec = {};
    (dados.reciprocas || RECIPROCAS_CONHECIDAS).forEach(function (p) { rec[chave(p[0], p[1])] = true; });
    var porId = {};
    agentes.forEach(function (a, i) { a.indice = i; a.grauCalculado = 0; porId[a.id] = a; });
    var sinapses = [], porChave = {};
    pares.forEach(function (p) {
      var k = chave(p[0], p[1]);
      if (porChave[k] || !porId[p[0]] || !porId[p[1]] || p[0] === p[1]) return;
      var s = { chave: k, a: p[0], b: p[1], natureza: rec[k] ? 'reciproca' : 'unilateral' };
      porChave[k] = s; sinapses.push(s);
      porId[p[0]].grauCalculado++; porId[p[1]].grauCalculado++;
    });
    agentes.forEach(function (a) { if (!a.grau) a.grau = a.grauCalculado; });
    (dados.declaraTodos || DECLARA_TODOS).forEach(function (id) {
      if (!porId[id]) return;
      agentes.forEach(function (o) {
        if (o.id === id) return;
        var k = chave(id, o.id);
        if (porChave[k]) return;
        var s = { chave: k, a: id, b: o.id, natureza: 'latente' };
        porChave[k] = s; sinapses.push(s);
      });
    });
    var vizinhos = {};
    agentes.forEach(function (a) { vizinhos[a.id] = {}; });
    sinapses.forEach(function (s) { vizinhos[s.a][s.b] = s; vizinhos[s.b][s.a] = s; });
    var nomeRegiao = {};
    regioes.forEach(function (r) { nomeRegiao[r.id] = r.nome; });
    return { regioes: regioes, agentes: agentes, porId: porId, sinapses: sinapses, porChave: porChave, vizinhos: vizinhos, nomeRegiao: nomeRegiao };
  }

  /* =====================================================================
     Tipos de mensagem (movili/core/mensagem.py) e prioridades
     ===================================================================== */
  var TIPOS = [
    { id: 'briefing', rotulo: 'Briefing', descricao: 'Demanda entrando na empresa', glifo: 'anel' },
    { id: 'tarefa', rotulo: 'Tarefa', descricao: 'Atribuição direta a um agente', glifo: 'seta' },
    { id: 'entrega', rotulo: 'Entrega', descricao: 'Resultado de uma tarefa', glifo: 'circulo' },
    { id: 'pergunta', rotulo: 'Pergunta', descricao: 'Um agente pedindo informação a outro', glifo: 'losango-vazado' },
    { id: 'resposta', rotulo: 'Resposta', descricao: 'Retorno de uma pergunta', glifo: 'losango' },
    { id: 'revisao', rotulo: 'Revisão', descricao: 'Crítica ou aprovação de uma entrega', glifo: 'quadrado' },
    { id: 'decisao', rotulo: 'Decisão', descricao: 'Deliberação da liderança', glifo: 'barra' },
    { id: 'alerta', rotulo: 'Alerta', descricao: 'Risco, bloqueio ou erro', glifo: 'triangulo' },
    { id: 'informe', rotulo: 'Informe', descricao: 'Comunicado geral para toda a rede', glifo: 'asterisco' }
  ];
  var TIPO = {};
  TIPOS.forEach(function (t) { TIPO[t.id] = t; });
  /* Mensagens que fecham um ciclo de trabalho útil: reforçam a sinapse ao chegar. */
  var UTEIS = { entrega: true, resposta: true, revisao: true, decisao: true };

  var PRIORIDADES = [
    { id: 'baixa', rotulo: 'Baixa', nivel: 1 },
    { id: 'normal', rotulo: 'Normal', nivel: 2 },
    { id: 'alta', rotulo: 'Alta', nivel: 3 },
    { id: 'critica', rotulo: 'Crítica', nivel: 4 }
  ];
  var PRIORIDADE = {};
  PRIORIDADES.forEach(function (p) { PRIORIDADE[p.id] = p; });

  /* =====================================================================
     Utilidades
     ===================================================================== */
  function clamp(x, a, b) { return x < a ? a : x > b ? b : x; }
  function lerp(a, b, t) { return a + (b - a) * t; }
  function aproximar(atual, alvo, passo) {
    if (atual < alvo) return Math.min(alvo, atual + passo);
    return Math.max(alvo, atual - passo);
  }
  function hashTexto(s) {
    var h = 2166136261;
    for (var i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); }
    return (h >>> 0) / 4294967295;
  }
  function aleatorio(semente) {
    var a = semente >>> 0;
    return function () {
      a = (a + 0x6D2B79F5) >>> 0;
      var t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function curvaBezier(x1, y1, x2, y2) {
    function a(p1, p2) { return 1 - 3 * p2 + 3 * p1; }
    function b(p1, p2) { return 3 * p2 - 6 * p1; }
    function c(p1) { return 3 * p1; }
    function calc(t, p1, p2) { return ((a(p1, p2) * t + b(p1, p2)) * t + c(p1)) * t; }
    function deriv(t, p1, p2) { return 3 * a(p1, p2) * t * t + 2 * b(p1, p2) * t + c(p1); }
    return function (x) {
      if (x <= 0) return 0;
      if (x >= 1) return 1;
      var t = x;
      for (var i = 0; i < 6; i++) {
        var d = deriv(t, x1, x2);
        if (Math.abs(d) < 1e-6) break;
        t -= (calc(t, x1, x2) - x) / d;
      }
      t = clamp(t, 0, 1);
      return calc(t, y1, y2);
    };
  }
  function el(tag, attrs, filhos) {
    var e = doc.createElement(tag);
    if (attrs) for (var k in attrs) {
      var v = attrs[k];
      if (v == null || v === false) continue;
      if (k === 'texto') e.textContent = v;
      else if (k === 'classe') e.className = v;
      else if (k.slice(0, 2) === 'on' && typeof v === 'function') e.addEventListener(k.slice(2), v);
      else e.setAttribute(k, v === true ? '' : v);
    }
    if (filhos) (Array.isArray(filhos) ? filhos : [filhos]).forEach(function (f) {
      if (f == null || f === false) return;
      e.appendChild(typeof f === 'string' ? doc.createTextNode(f) : f);
    });
    return e;
  }
  var SVGNS = 'http://www.w3.org/2000/svg';
  function svg(tag, attrs) {
    var e = doc.createElementNS(SVGNS, tag);
    if (attrs) for (var k in attrs) if (attrs[k] != null) e.setAttribute(k, attrs[k]);
    return e;
  }
  function limpar(e) { while (e.firstChild) e.removeChild(e.firstChild); return e; }

  /* Cor: '#rgb', '#rgba', '#rrggbb', '#rrggbbaa', 'rgb()', 'rgba()' -> [r, g, b, a] */
  function lerCor(txt) {
    if (!txt) return null;
    var s = String(txt).trim().toLowerCase();
    var m;
    if (s[0] === '#') {
      var h = s.slice(1);
      if (h.length === 3 || h.length === 4) h = h.split('').map(function (c) { return c + c; }).join('');
      if (h.length !== 6 && h.length !== 8) return null;
      var n = [];
      for (var i = 0; i < h.length; i += 2) n.push(parseInt(h.slice(i, i + 2), 16));
      if (n.some(isNaN)) return null;
      return [n[0], n[1], n[2], n.length > 3 ? n[3] / 255 : 1];
    }
    if ((m = s.match(/^rgba?\(([^)]+)\)$/))) {
      var p = m[1].replace(/\//g, ' ').split(/[\s,]+/).filter(Boolean);
      if (p.length < 3) return null;
      var alfa = p.length > 3 ? (p[3].indexOf('%') > 0 ? parseFloat(p[3]) / 100 : parseFloat(p[3])) : 1;
      return [parseFloat(p[0]), parseFloat(p[1]), parseFloat(p[2]), alfa];
    }
    return null;
  }
  function css(c, alfa) {
    var a = (alfa == null ? 1 : alfa) * (c[3] == null ? 1 : c[3]);
    return 'rgba(' + Math.round(c[0]) + ',' + Math.round(c[1]) + ',' + Math.round(c[2]) + ',' + clamp(a, 0, 1).toFixed(3) + ')';
  }
  function misturar(c1, c2, t) {
    return [lerp(c1[0], c2[0], t), lerp(c1[1], c2[1], t), lerp(c1[2], c2[2], t), lerp(c1[3], c2[3], t)];
  }
  function luminancia(c) {
    var f = function (v) { v /= 255; return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
    return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2]);
  }
  function pct(v) { return Math.round(clamp(v, 0, 1) * 100) + '%'; }
  function decimal(v) { return (Math.round(v * 100) / 100).toFixed(2).replace('.', ','); }
  function relogio(ms) {
    var neg = ms < 0; ms = Math.abs(ms);
    var s = Math.floor(ms / 1000), m = Math.floor(s / 60), d = Math.floor((ms % 1000) / 100);
    return (neg ? '−' : '') + String(m).padStart(2, '0') + ':' + String(s % 60).padStart(2, '0') + ',' + d;
  }
  function movimentoReduzido() {
    return !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  }

  /* =====================================================================
     Tokens: lidos das variáveis CSS de tokens.css; os valores abaixo são o tema escuro
     ===================================================================== */
  var PADRAO_COR = {
    'fundo': '#0b0a10', 'superficie': '#15141c', 'vidro': '#15141ceb', 'superficie-2': '#1f1d28', 'borda': '#2b2936',
    'borda-controle': '#6d6882', 'texto': '#ece9f5', 'texto-suave': '#a7a2b8', 'acento': '#8b6cf6', 'sobre-acento': '#0b0a10',
    'sucesso': '#3ddc97', 'atencao': '#f2b84b', 'erro': '#ff5d73',
    'ativacao': '#f6f3ff', 'neuronio': '#6a6484', 'neuronio-contorno': '#6d6882',
    'sinapse-forte': '#a49ec0', 'sinapse-fraca': '#26242f', 'sinapse-latente': '#18171f', 'campo-regiao': '#a58bff0c',
    'plancton': '#c9bdff',
    'msg-briefing': '#40e2f3', 'msg-tarefa': '#65adff', 'msg-entrega': '#3ddc97', 'msg-pergunta': '#eb76e9',
    'msg-resposta': '#ff9fc4', 'msg-revisao': '#cfef54', 'msg-decisao': '#ffb04a', 'msg-alerta': '#ff5d73', 'msg-informe': '#d5d1e6'
  };
  var PADRAO_NUM = {
    'traco-sinapse-min': 0.5, 'traco-sinapse-max': 3, 'traco-contorno': 1.5, 'traco-selecao': 2, 'traco-rastro': 2, 'traco-onda': 1.5,
    'raio-grau-4': 9.5, 'raio-grau-5': 11.1, 'raio-grau-6': 12.6, 'raio-grau-7': 14.1, 'raio-grau-8': 15.4,
    'raio-grau-9': 16.8, 'raio-grau-10': 18, 'raio-grau-11': 19.3, 'halo-max': 3.2, 'respiro-escala': 0.03,
    'pulso-baixa': 4, 'pulso-normal': 5, 'pulso-alta': 6.5, 'pulso-critica': 8,
    'particulas-max': 3, 'particula-raio': 1.3, 'plancton-quantidade': 72,
    'respiracao': 5200, 'travessia-forte': 420, 'travessia-fraca': 1800, 'fluxo-lento': 7200, 'fluxo-rapido': 3000,
    'onda-estimulo': 1400, 'onda-informe': 900,
    'pulso-entrega': 600, 'reforco': 900, 'decaimento-ativacao': 2600, 'transicao-ui': 160,
    'fator-baixa': 0.6, 'fator-normal': 1, 'fator-alta': 1.5, 'fator-critica': 2.2,
    'opacidade-recuo': 0.15, 'opacidade-apagado': 0.14, 'opacidade-rastro': 0.9,
    'peso-piso': 0.06, 'peso-unilateral': 0.3, 'peso-reciproca': 0.55, 'peso-latente': 0.03,
    'taxa-reforco': 0.12, 'meia-vida-atrofia': 10, 'limiar-padrao': 0.5,
    'altura-cabecalho': 44, 'altura-linha-tempo': 48, 'largura-painel': 360, 'margem-flutuante': 12,
    'zoom-min': 0.5, 'zoom-max': 3, 'zoom-rotulos': 1.6
  };
  var PADRAO_CURVA = {
    'curva-saida': [0.2, 0, 0, 1], 'curva-travessia': [0.45, 0, 0.25, 1], 'curva-respiro': [0.37, 0, 0.63, 1]
  };

  function lerTokens(raiz) {
    var cs = getComputedStyle(raiz && raiz.isConnected ? raiz : doc.documentElement);
    var t = { cor: {}, num: {}, curva: {}, fonte: {} };
    Object.keys(PADRAO_COR).forEach(function (n) {
      t.cor[n] = lerCor(cs.getPropertyValue('--' + n)) || lerCor(PADRAO_COR[n]);
    });
    Object.keys(PADRAO_NUM).forEach(function (n) {
      var v = parseFloat(cs.getPropertyValue('--' + n));
      t.num[n] = isFinite(v) ? v : PADRAO_NUM[n];
    });
    Object.keys(PADRAO_CURVA).forEach(function (n) {
      var m = cs.getPropertyValue('--' + n).match(/cubic-bezier\(([^)]+)\)/);
      var p = m ? m[1].split(',').map(parseFloat) : PADRAO_CURVA[n];
      if (p.length !== 4 || p.some(function (x) { return !isFinite(x); })) p = PADRAO_CURVA[n];
      t.curva[n] = curvaBezier(p[0], p[1], p[2], p[3]);
    });
    t.fonte.sans = cs.getPropertyValue('--font-sans').trim() || 'system-ui, sans-serif';
    t.fonte.mono = cs.getPropertyValue('--font-mono').trim() || 'ui-monospace, monospace';
    /* Escuro: a ativação é luz somada ao fundo. Claro: é tinta sobre papel. Mesmo dado, outro mecanismo. */
    t.modo = luminancia(t.cor.fundo) < 0.4 ? 'luz' : 'tinta';
    return t;
  }
  function raioDoGrau(tokens, grau) {
    var g = clamp(Math.round(grau), 4, 11);
    var v = tokens.num['raio-grau-' + g];
    return isFinite(v) ? v : 3.6 * Math.pow(grau, 0.7);
  }

  /* Observa troca de tema (data-theme em qualquer ancestral, classe ou esquema do sistema). */
  function observarTema(cb) {
    var agendado = false;
    function disparar() {
      if (agendado) return; agendado = true;
      requestAnimationFrame(function () { agendado = false; cb(); });
    }
    /* Dois observadores: observe() repetido no mesmo nó substituiria as opções do primeiro. */
    var moTema = new MutationObserver(disparar);
    moTema.observe(doc.documentElement, { attributes: true, subtree: true, attributeFilter: ['data-theme'] });
    var moRaiz = new MutationObserver(disparar);
    moRaiz.observe(doc.documentElement, { attributes: true, attributeFilter: ['class', 'style'] });
    var mqs = [];
    if (window.matchMedia) {
      ['(prefers-color-scheme: dark)', '(prefers-reduced-motion: reduce)'].forEach(function (q) {
        var mq = window.matchMedia(q);
        if (mq.addEventListener) { mq.addEventListener('change', disparar); mqs.push(mq); }
      });
    }
    return function () { moTema.disconnect(); moRaiz.disconnect(); mqs.forEach(function (mq) { mq.removeEventListener('change', disparar); }); };
  }

  /* Um relógio só para todos os canvas animados da página. */
  var Relogio = (function () {
    var inscritos = [], raf = 0;
    function passo(agora) {
      raf = 0;
      var vivos = inscritos.slice();
      vivos.forEach(function (f) { f(agora); });
      if (inscritos.length) raf = requestAnimationFrame(passo);
    }
    return {
      inscrever: function (f) { if (inscritos.indexOf(f) < 0) inscritos.push(f); if (!raf) raf = requestAnimationFrame(passo); },
      cancelar: function (f) { var i = inscritos.indexOf(f); if (i >= 0) inscritos.splice(i, 1); }
    };
  })();

  /* =====================================================================
     Glifos: a forma é do tipo de mensagem, para nada depender só da cor.
     Vazio = aberto/aguardando; cheio = resolvido; traço = direção ou irradiação.
     ===================================================================== */
  var GLIFO_GIRA = { seta: true, barra: true };
  function caminhoGlifo(ctx, glifo, s) {
    ctx.beginPath();
    switch (glifo) {
      case 'anel': ctx.arc(0, 0, s * 0.79, 0, TAU); return { traco: s * 0.42 };
      case 'seta': ctx.moveTo(-s * 0.5, -s * 0.92); ctx.lineTo(s * 0.46, 0); ctx.lineTo(-s * 0.5, s * 0.92); return { traco: s * 0.44 };
      case 'circulo': ctx.arc(0, 0, s * 0.92, 0, TAU); return { cheio: true };
      case 'losango-vazado': ctx.moveTo(0, -s * 0.95); ctx.lineTo(s * 0.95, 0); ctx.lineTo(0, s * 0.95); ctx.lineTo(-s * 0.95, 0); ctx.closePath(); return { traco: s * 0.36 };
      case 'losango': ctx.moveTo(0, -s * 1.1); ctx.lineTo(s * 1.1, 0); ctx.lineTo(0, s * 1.1); ctx.lineTo(-s * 1.1, 0); ctx.closePath(); return { cheio: true };
      case 'quadrado': ctx.rect(-s * 0.8, -s * 0.8, s * 1.6, s * 1.6); return { cheio: true };
      case 'barra': ctx.rect(-s * 0.32, -s * 1.05, s * 0.64, s * 2.1); return { cheio: true };
      case 'triangulo': ctx.moveTo(0, -s * 1.02); ctx.lineTo(s * 1.08, s * 0.84); ctx.lineTo(-s * 1.08, s * 0.84); ctx.closePath(); return { cheio: true };
      case 'asterisco':
        for (var i = 0; i < 3; i++) {
          var a = Math.PI / 2 + i * Math.PI / 3;
          ctx.moveTo(Math.cos(a) * s, Math.sin(a) * s); ctx.lineTo(-Math.cos(a) * s, -Math.sin(a) * s);
        }
        return { traco: s * 0.36, redondo: true };
    }
    ctx.arc(0, 0, s, 0, TAU); return { cheio: true };
  }
  /* recorte: contorno na cor do fundo, para o glifo não se confundir com a linha embaixo (tema claro). */
  function desenharGlifo(ctx, glifo, x, y, s, angulo, cor, recorte) {
    ctx.save();
    ctx.translate(x, y);
    if (GLIFO_GIRA[glifo]) ctx.rotate(angulo || 0);
    var info = caminhoGlifo(ctx, glifo, s);
    ctx.lineJoin = 'miter'; ctx.miterLimit = 4;
    ctx.lineCap = info.redondo ? 'round' : 'butt';
    if (recorte) {
      ctx.strokeStyle = recorte;
      ctx.lineWidth = (info.traco || 0) + 3;
      ctx.stroke();
    }
    if (info.cheio) { ctx.fillStyle = cor; ctx.fill(); }
    else { ctx.strokeStyle = cor; ctx.lineWidth = info.traco; ctx.stroke(); }
    ctx.restore();
  }
  /* Versão SVG, para a interface em DOM. A cor segue o tema: style fill/stroke = var(--msg-…). */
  function glifoSVG(tipoOuGlifo, tamanho, corCss) {
    var t = TIPO[tipoOuGlifo];
    var glifo = t ? t.glifo : tipoOuGlifo;
    var cor = corCss || (t ? 'var(--msg-' + t.id + ')' : 'currentColor');
    var tam = tamanho || 10;
    var raiz = svg('svg', { viewBox: '-1.25 -1.25 2.5 2.5', width: tam, height: tam, 'aria-hidden': 'true', focusable: 'false', 'class': 'mr-glifo' });
    var cheio = 'fill:' + cor + ';stroke:none';
    function traco(w, extra) { return 'fill:none;stroke:' + cor + ';stroke-width:' + w + (extra || ''); }
    var f;
    switch (glifo) {
      case 'anel': f = svg('circle', { r: 0.79, style: traco(0.42) }); break;
      case 'seta': f = svg('path', { d: 'M-0.5 -0.92 L0.46 0 L-0.5 0.92', style: traco(0.44, ';stroke-linejoin:miter') }); break;
      case 'circulo': f = svg('circle', { r: 0.92, style: cheio }); break;
      case 'losango-vazado': f = svg('path', { d: 'M0 -0.95 L0.95 0 L0 0.95 L-0.95 0Z', style: traco(0.36, ';stroke-linejoin:miter') }); break;
      case 'losango': f = svg('path', { d: 'M0 -1.1 L1.1 0 L0 1.1 L-1.1 0Z', style: cheio }); break;
      case 'quadrado': f = svg('rect', { x: -0.8, y: -0.8, width: 1.6, height: 1.6, style: cheio }); break;
      case 'barra': f = svg('rect', { x: -0.32, y: -1.05, width: 0.64, height: 2.1, style: cheio }); break;
      case 'triangulo': f = svg('path', { d: 'M0 -1.02 L1.08 0.84 L-1.08 0.84Z', style: cheio }); break;
      case 'asterisco':
        f = svg('path', { d: 'M0 -1 L0 1 M0.866 -0.5 L-0.866 0.5 M0.866 0.5 L-0.866 -0.5', style: traco(0.36, ';stroke-linecap:round') });
        break;
      default: f = svg('circle', { r: 0.9, style: cheio });
    }
    raiz.appendChild(f);
    return raiz;
  }

  /* =====================================================================
     Desenho (canvas). Escuro: bioluminescência, luz somada ao fundo (composição aditiva).
     Claro: tinta sobre papel. Usado pela Rede e pelos avulsos.
     ===================================================================== */
  var GLIFO_CHEIO = { circulo: true, losango: true, quadrado: true, barra: true, triangulo: true };
  function corTipo(tk, tipo) { return tk.cor['msg-' + tipo] || tk.cor['msg-briefing']; }

  /* e: {ativacao, disparou, tipo, tremor, respiro 0..1, entrega 0..1 (ou -1), selecionado, realce 0..1, alfa} */
  function desenharNeuronio(ctx, tk, x, y, r, e) {
    var c = tk.cor, n = tk.num, luz = tk.modo === 'luz';
    var v = e.disparou ? clamp(e.ativacao || 0, 0, 1) : 0;
    var cor = corTipo(tk, e.tipo || 'briefing');
    ctx.save();
    ctx.globalAlpha = e.alfa == null ? 1 : e.alfa;
    if (v > 0.01) {
      var R = r * (1 + (n['halo-max'] - 1) * v);
      if (luz) {
        /* coroa de luz na cor do tráfego que o neurônio está processando */
        ctx.globalCompositeOperation = 'lighter';
        var g = ctx.createRadialGradient(x, y, r * 0.4, x, y, R);
        g.addColorStop(0, css(misturar(cor, c.ativacao, 0.35), 0.6 * v));
        g.addColorStop(0.4, css(cor, 0.24 * v));
        g.addColorStop(1, css(cor, 0));
        ctx.fillStyle = g;
        ctx.beginPath(); ctx.arc(x, y, R, 0, TAU); ctx.fill();
        ctx.globalCompositeOperation = 'source-over';
      } else {
        /* tinta: aguada na cor do tipo e anéis concêntricos, como curvas de nível */
        var g2 = ctx.createRadialGradient(x, y, r, x, y, R);
        g2.addColorStop(0, css(cor, 0.16 * v));
        g2.addColorStop(1, css(cor, 0));
        ctx.fillStyle = g2;
        ctx.beginPath(); ctx.arc(x, y, R, 0, TAU); ctx.fill();
        var aneis = v > 0.66 ? 3 : v > 0.33 ? 2 : 1;
        ctx.lineWidth = n['traco-contorno'] * 0.8;
        for (var k = 1; k <= aneis; k++) {
          ctx.strokeStyle = css(cor, (0.85 * v) / k);
          ctx.beginPath(); ctx.arc(x, y, r + (R - r) * (k / (aneis + 0.5)), 0, TAU); ctx.stroke();
        }
      }
    }
    if (luz) {
      var gn = ctx.createRadialGradient(x - r * 0.28, y - r * 0.28, 0, x, y, r);
      if (v > 0) {
        gn.addColorStop(0, css(misturar(c.neuronio, c.ativacao, Math.min(1, 0.3 + v))));
        gn.addColorStop(1, css(misturar(c.neuronio, cor, 0.8 * v)));
      } else {
        /* repouso: um ponto sólido de grafo, com um reflexo interno que respira */
        gn.addColorStop(0, css(misturar(c.neuronio, c.ativacao, 0.16 + 0.12 * (e.respiro || 0))));
        gn.addColorStop(1, css(c.neuronio));
      }
      ctx.fillStyle = gn;
    } else {
      ctx.fillStyle = css(v > 0 ? misturar(c.neuronio, c.ativacao, 0.3 + 0.7 * v) : c.neuronio);
    }
    ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.fill();
    if (!luz && v <= 0) {
      ctx.strokeStyle = css(c['neuronio-contorno']);
      ctx.lineWidth = 1;
      ctx.beginPath(); ctx.arc(x, y, Math.max(0.5, r - 0.5), 0, TAU); ctx.stroke();
    }
    if (e.tremor > 0.01) {
      ctx.strokeStyle = css(c.ativacao, 0.55 * e.tremor);
      ctx.lineWidth = 1;
      ctx.beginPath(); ctx.arc(x, y, r + 2.5, 0, TAU); ctx.stroke();
    }
    if (e.entrega != null && e.entrega >= 0 && e.entrega < 1) {
      /* entrega: um pulso único e uma explosão de faíscas verdes */
      var pe = tk.curva['curva-saida'](e.entrega), ce = c['msg-entrega'], resto = 1 - e.entrega;
      if (luz) ctx.globalCompositeOperation = 'lighter';
      ctx.strokeStyle = css(ce, resto);
      ctx.lineWidth = 2;
      ctx.beginPath(); ctx.arc(x, y, r + 2 + r * 1.3 * pe, 0, TAU); ctx.stroke();
      ctx.fillStyle = css(ce, 0.9 * resto);
      for (var i = 0; i < 7; i++) {
        var a = i * TAU / 7 + 0.35, dd = r + 4 + r * 2 * pe;
        ctx.beginPath(); ctx.arc(x + Math.cos(a) * dd, y + Math.sin(a) * dd, 1.7 * (1 - 0.5 * pe), 0, TAU); ctx.fill();
      }
      ctx.globalCompositeOperation = 'source-over';
    }
    if (e.realce > 0) {
      ctx.strokeStyle = css(c.acento, e.realce);
      ctx.lineWidth = n['traco-contorno'];
      ctx.beginPath(); ctx.arc(x, y, r + 2.5, 0, TAU); ctx.stroke();
    }
    if (e.selecionado) {
      if (luz) {
        ctx.globalCompositeOperation = 'lighter';
        var gs = ctx.createRadialGradient(x, y, r, x, y, r + 16);
        gs.addColorStop(0, css(c.acento, 0.45));
        gs.addColorStop(1, css(c.acento, 0));
        ctx.fillStyle = gs;
        ctx.beginPath(); ctx.arc(x, y, r + 16, 0, TAU); ctx.fill();
        ctx.globalCompositeOperation = 'source-over';
      }
      ctx.strokeStyle = css(c.acento);
      ctx.lineWidth = n['traco-selecao'];
      ctx.beginPath(); ctx.arc(x, y, r + 4 + n['traco-selecao'] / 2, 0, TAU); ctx.stroke();
    }
    ctx.restore();
  }

  function estiloSinapse(tk, peso, natureza) {
    var c = tk.cor, n = tk.num;
    if (natureza === 'latente' && peso <= n['peso-latente'] + 0.01) {
      return { cor: c['sinapse-latente'], largura: n['traco-sinapse-min'], latente: true };
    }
    var w = clamp(peso, 0, 1);
    return {
      cor: misturar(c['sinapse-fraca'], c['sinapse-forte'], w),
      largura: n['traco-sinapse-min'] + (n['traco-sinapse-max'] - n['traco-sinapse-min']) * w
    };
  }
  /* s: {peso, natureza, flash 0..1, ativa: cor do tipo que está passando, realce 0..1, alfa, tracejada} */
  function desenharSinapse(ctx, tk, x1, y1, x2, y2, s) {
    var est = estiloSinapse(tk, s.peso, s.natureza);
    var cor = est.cor, larg = est.largura, c = tk.cor, luz = tk.modo === 'luz';
    if (s.flash > 0) { cor = misturar(cor, c.ativacao, 0.6 * s.flash); larg += 1.4 * s.flash; }
    if (s.realce) { cor = misturar(cor, c.acento, 0.8 * s.realce); larg = Math.max(larg, 1.2); }
    ctx.save();
    ctx.globalAlpha = s.alfa == null ? 1 : s.alfa;
    ctx.lineCap = 'round';
    if (s.tracejada) ctx.setLineDash([2, 5]);
    ctx.strokeStyle = css(cor);
    ctx.lineWidth = larg;
    ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
    if (s.ativa) {
      /* conduzindo: a sinapse vira um filamento de luz na cor do tipo */
      ctx.setLineDash([]);
      if (luz) ctx.globalCompositeOperation = 'lighter';
      ctx.strokeStyle = css(s.ativa, luz ? 0.14 : 0.1);
      ctx.lineWidth = larg + 7;
      ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
      ctx.strokeStyle = css(s.ativa, luz ? 0.6 : 0.65);
      ctx.lineWidth = Math.max(1, larg * 0.8);
      ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
    }
    ctx.restore();
  }
  /* Fluxo de repouso: partículas pela sinapse, em número e velocidade proporcionais ao peso. */
  function desenharFluxo(ctx, tk, x1, y1, x2, y2, peso, t, semente, alfa) {
    var n = tk.num, c = tk.cor, luz = tk.modo === 'luz';
    var w = clamp(peso, 0, 1), qtd = Math.round(n['particulas-max'] * w);
    if (qtd < 1) return;
    var periodo = lerp(n['fluxo-lento'], n['fluxo-rapido'], w);
    var cor = luz ? misturar(c['sinapse-forte'], c.ativacao, 0.55) : c['sinapse-forte'];
    var raio = n['particula-raio'] * (0.8 + 0.7 * w);
    ctx.save();
    if (luz) ctx.globalCompositeOperation = 'lighter';
    for (var k = 0; k < qtd; k++) {
      var f = ((t / periodo + k / qtd + semente) % 1 + 1) % 1;
      var s = k % 2 ? 1 - f : f;
      ctx.fillStyle = css(cor, Math.sin(Math.PI * f) * (0.3 + 0.6 * w) * (alfa == null ? 1 : alfa) * (luz ? 1 : 0.8));
      ctx.beginPath(); ctx.arc(x1 + (x2 - x1) * s, y1 + (y2 - y1) * s, raio, 0, TAU); ctx.fill();
    }
    ctx.restore();
  }

  function tamanhoPulso(tk, prioridade) {
    var n = tk.num;
    return n['pulso-' + prioridade] || n['pulso-normal'];
  }
  /* Pulso em trânsito: um cometa. Rastro e faíscas na cor do tipo, glifo na cabeça. p = 0..1 do percurso. */
  function desenharPulso(ctx, tk, x1, y1, x2, y2, p, tipo, prioridade, alfa, semente) {
    var c = tk.cor, n = tk.num, luz = tk.modo === 'luz';
    var cor = corTipo(tk, tipo);
    var s = tamanhoPulso(tk, prioridade), escala = s / n['pulso-normal'];
    var e = tk.curva['curva-travessia'](clamp(p, 0, 1));
    var dx = x2 - x1, dy = y2 - y1, L = Math.sqrt(dx * dx + dy * dy) || 1, ux = dx / L, uy = dy / L;
    var hx = x1 + dx * e, hy = y1 + dy * e;
    var rastro = clamp((46 * escala) / L, 0.06, 0.65), ec = Math.max(0, e - rastro);
    var tx = x1 + dx * ec, ty = y1 + dy * ec;
    ctx.save();
    ctx.globalAlpha = alfa == null ? 1 : alfa;
    if (luz) ctx.globalCompositeOperation = 'lighter';
    if (Math.abs(hx - tx) + Math.abs(hy - ty) > 0.5) {
      var g = ctx.createLinearGradient(tx, ty, hx, hy);
      g.addColorStop(0, css(cor, 0));
      g.addColorStop(1, css(cor, n['opacidade-rastro']));
      ctx.strokeStyle = g;
      ctx.lineWidth = n['traco-rastro'] * escala;
      ctx.lineCap = 'round';
      ctx.beginPath(); ctx.moveTo(tx, ty); ctx.lineTo(hx, hy); ctx.stroke();
    }
    /* faíscas soltas da cauda: deterministas, a reprodução mostra as mesmas */
    for (var k = 1; k <= 4; k++) {
      var fk = e - rastro * (k / 4.5);
      if (fk <= 0) break;
      var jit = Math.sin((semente || 0) * 13.1 + k * 2.3 + p * 9) * 3.4 * escala;
      ctx.fillStyle = css(cor, (1 - k / 5) * 0.85);
      ctx.beginPath(); ctx.arc(x1 + dx * fk - uy * jit, y1 + dy * fk + ux * jit, Math.max(0.5, (1.6 - k * 0.22) * escala), 0, TAU); ctx.fill();
    }
    if (luz) {
      var gb = ctx.createRadialGradient(hx, hy, 0, hx, hy, s * 3.8);
      gb.addColorStop(0, css(cor, 0.5));
      gb.addColorStop(1, css(cor, 0));
      ctx.fillStyle = gb;
      ctx.beginPath(); ctx.arc(hx, hy, s * 3.8, 0, TAU); ctx.fill();
    }
    ctx.globalCompositeOperation = 'source-over';
    var glifo = TIPO[tipo] ? TIPO[tipo].glifo : 'circulo', ang = Math.atan2(dy, dx);
    desenharGlifo(ctx, glifo, hx, hy, s, ang, css(cor), luz ? null : css(c.fundo));
    if (luz && GLIFO_CHEIO[glifo]) desenharGlifo(ctx, glifo, hx, hy, s * 0.42, ang, css(misturar(cor, c.ativacao, 0.8)), null);
    ctx.restore();
  }
  /* Sem movimento: a sinapse em uso fica tingida inteira e o glifo para no meio, apontando o sentido. */
  function desenharPulsoEstatico(ctx, tk, x1, y1, x2, y2, tipo, prioridade, alfa) {
    var c = tk.cor, n = tk.num;
    var cor = corTipo(tk, tipo);
    var s = tamanhoPulso(tk, prioridade);
    ctx.save();
    ctx.globalAlpha = (alfa == null ? 1 : alfa) * 0.9;
    ctx.strokeStyle = css(cor);
    ctx.lineWidth = n['traco-rastro'] * (s / n['pulso-normal']);
    ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
    ctx.globalAlpha = alfa == null ? 1 : alfa;
    desenharGlifo(ctx, TIPO[tipo] ? TIPO[tipo].glifo : 'circulo', (x1 + x2) / 2, (y1 + y2) / 2, s, Math.atan2(y2 - y1, x2 - x1), css(cor), css(c.fundo));
    ctx.restore();
  }
  function desenharOnda(ctx, tk, x, y, raio, p, tipo, estatica) {
    var c = tk.cor, n = tk.num;
    var cor = corTipo(tk, tipo);
    ctx.save();
    var a = estatica ? 0.75 : Math.pow(1 - clamp(p, 0, 1), 1.4) * 0.9;
    if (tk.modo === 'luz' && !estatica) {
      ctx.globalCompositeOperation = 'lighter';
      ctx.globalAlpha = a * 0.16;
      ctx.strokeStyle = css(cor);
      ctx.lineWidth = 14;
      ctx.beginPath(); ctx.arc(x, y, raio, 0, TAU); ctx.stroke();
      ctx.globalCompositeOperation = 'source-over';
    }
    ctx.globalAlpha = a;
    ctx.strokeStyle = css(cor);
    ctx.lineWidth = n['traco-onda'];
    if (estatica) ctx.setLineDash([3, 4]);
    ctx.beginPath(); ctx.arc(x, y, raio, 0, TAU); ctx.stroke();
    ctx.restore();
  }
  /* Plâncton: duas profundidades de pontos que sobem devagar. Brilham mais com a atividade da rede
     e piscam na cor da onda quando ela passa, como plâncton de verdade diante de um distúrbio. */
  function criarPlancton(qtd, semente) {
    var rnd = aleatorio(semente || 11), lista = [];
    for (var i = 0; i < qtd; i++) {
      lista.push({ u: rnd(), v: rnd(), z: rnd() < 0.55 ? 0.35 : 0.8, fase: rnd() * TAU, vel: 0.004 + rnd() * 0.01, osc: 0.4 + rnd() * 0.9 });
    }
    return lista;
  }
  function desenharPlancton(ctx, tk, lista, W, H, t, deslX, deslY, atividade, ondas, reduzir) {
    var c = tk.cor, luz = tk.modo === 'luz';
    ctx.save();
    if (luz) ctx.globalCompositeOperation = 'lighter';
    for (var i = 0; i < lista.length; i++) {
      var m = lista[i];
      var u = m.u, v = m.v, brilho = 1;
      if (!reduzir) {
        v = ((m.v - (t / 1000) * m.vel) % 1 + 1) % 1;
        u = m.u + 0.006 * Math.sin((t / 1000) * m.osc + m.fase);
        brilho = 0.65 + 0.35 * Math.sin((t / 700) * m.osc + m.fase * 2);
      }
      var x = ((u * W + deslX * m.z * 0.35) % W + W) % W;
      var y = ((v * H + deslY * m.z * 0.35) % H + H) % H;
      var a = (0.08 + 0.2 * m.z) * (0.55 + 0.45 * atividade) * brilho, tam = 0.6 + 1.1 * m.z, cor = c.plancton;
      for (var k = 0; k < ondas.length; k++) {
        var o = ondas[k], d = Math.sqrt((x - o.x) * (x - o.x) + (y - o.y) * (y - o.y));
        var b = Math.exp(-Math.pow((d - o.r) / 30, 2)) * (1 - o.p);
        if (b > 0.02) { a += 0.5 * b; tam += 1.2 * b; cor = misturar(cor, o.cor, Math.min(1, b * 1.5)); }
      }
      ctx.fillStyle = css(cor, Math.min(0.9, a) * (luz ? 1 : 0.45));
      ctx.beginPath(); ctx.arc(x, y, tam, 0, TAU); ctx.fill();
    }
    ctx.restore();
  }
  function segmento(pa, pb, ra, rb) {
    var dx = pb.x - pa.x, dy = pb.y - pa.y, L = Math.sqrt(dx * dx + dy * dy) || 1;
    var ux = dx / L, uy = dy / L;
    return { x1: pa.x + ux * ra, y1: pa.y + uy * ra, x2: pb.x - ux * rb, y2: pb.y - uy * rb };
  }
  function distSegmento(px, py, x1, y1, x2, y2) {
    var dx = x2 - x1, dy = y2 - y1, L2 = dx * dx + dy * dy || 1;
    var u = clamp(((px - x1) * dx + (py - y1) * dy) / L2, 0, 1);
    var qx = x1 + u * dx - px, qy = y1 + u * dy - py;
    return Math.sqrt(qx * qx + qy * qy);
  }

  /* =====================================================================
     Física: força dirigida com regiões como campos de gravidade (sem caixas).
     Molas mais curtas para sinapses mais pesadas: o que a rede aprende aproxima os nós.
     Roda em lote para o layout inicial e ao vivo quando um nó é arrastado.
     ===================================================================== */
  function criarFisica(topo, pesos, largura, altura, op) {
    op = op || {};
    var nos = topo.agentes, N = nos.length;
    var A = clamp(largura / Math.max(1, altura), 0.45, 2.8);
    var rnd = aleatorio(op.semente || 20);
    var ordem = {};
    topo.regioes.forEach(function (r, i) { ordem[r.id] = i; });
    var R = topo.regioes.length || 1;
    var idx = {};
    nos.forEach(function (a, i) { idx[a.id] = i; });
    var raioN = nos.map(function (a) { return (op.raio ? op.raio(a) : 12) / Math.max(1, altura); });
    var P = nos.map(function (a) {
      var ant = op.anterior && op.anterior[a.id];
      if (ant) return { x: ant.u * A, y: ant.v, vx: 0, vy: 0, fixo: false };
      var ang = ((ordem[a.regiao] || 0) / R) * TAU - Math.PI / 2 + (rnd() - 0.5) * 0.35;
      var rr = 0.28 + rnd() * 0.1;
      return { x: A / 2 + Math.cos(ang) * rr * Math.max(1, A * 0.8), y: 0.5 + Math.sin(ang) * rr, vx: 0, vy: 0, fixo: false };
    });
    var ligas = [];
    function montarLigas(pz) {
      ligas = [];
      topo.sinapses.forEach(function (s) {
        var w = pz[s.chave] == null ? 0.3 : pz[s.chave];
        if (s.natureza === 'latente' && w < 0.1) return;
        if (idx[s.a] == null || idx[s.b] == null) return;
        ligas.push({ i: idx[s.a], j: idx[s.b], w: clamp(w, 0, 1) });
      });
    }
    montarLigas(pesos || {});
    var esp = Math.sqrt(20 / N);
    var kRep = 0.0015 * esp * esp, kMola = 0.09, kReg = 0.05, kCentro = 0.03, L0 = 0.2 * esp;
    function passo(alfa) {
      var i, j, cx = {}, cy = {}, cn = {};
      for (i = 0; i < N; i++) {
        var rg = nos[i].regiao;
        cx[rg] = (cx[rg] || 0) + P[i].x; cy[rg] = (cy[rg] || 0) + P[i].y; cn[rg] = (cn[rg] || 0) + 1;
      }
      for (i = 0; i < N; i++) {
        var pi = P[i], ai = nos[i];
        for (j = i + 1; j < N; j++) {
          var pj = P[j];
          var dx = pj.x - pi.x, dy = pj.y - pi.y;
          var d2 = dx * dx + dy * dy + 1e-4, d = Math.sqrt(d2);
          var f = (kRep * alfa * (ai.regiao === nos[j].regiao ? 0.7 : 1.35)) / d2;
          var fx = (dx / d) * f, fy = (dy / d) * f;
          pi.vx -= fx; pi.vy -= fy; pj.vx += fx; pj.vy += fy;
        }
        var rcx = cx[ai.regiao] / cn[ai.regiao], rcy = cy[ai.regiao] / cn[ai.regiao];
        pi.vx += (rcx - pi.x) * kReg * alfa; pi.vy += (rcy - pi.y) * kReg * alfa;
        /* centro anisotrópico: puxa mais no eixo curto, para a rede ocupar a proporção da área */
        pi.vx += ((A / 2 - pi.x) * kCentro * alfa) / (A * A); pi.vy += (0.5 - pi.y) * kCentro * alfa * A;
        /* contorno elíptico macio */
        var ex0 = (pi.x - A / 2) / (A / 2), ey0 = (pi.y - 0.5) / 0.5, rho = Math.sqrt(ex0 * ex0 + ey0 * ey0);
        if (rho > 0.9) {
          var exc = (rho - 0.9) * 0.3;
          pi.vx -= (ex0 / rho) * exc * (A / 2); pi.vy -= (ey0 / rho) * exc * 0.5;
        }
      }
      for (var l = 0; l < ligas.length; l++) {
        var lg = ligas[l], p1 = P[lg.i], p2 = P[lg.j];
        var ddx = p2.x - p1.x, ddy = p2.y - p1.y, dd = Math.sqrt(ddx * ddx + ddy * ddy) || 1e-3;
        var alvo = L0 * (1.25 - 0.55 * lg.w);
        var fm = (kMola * (0.45 + lg.w) * alfa * (dd - alvo)) / dd;
        p1.vx += ddx * fm; p1.vy += ddy * fm; p2.vx -= ddx * fm; p2.vy -= ddy * fm;
      }
      for (i = 0; i < N; i++) {
        if (P[i].fixo) { P[i].vx = P[i].vy = 0; continue; }
        P[i].x += P[i].vx; P[i].y += P[i].vy;
        P[i].vx *= 0.55; P[i].vy *= 0.55;
      }
      for (i = 0; i < N; i++) for (j = i + 1; j < N; j++) {
        var q1 = P[i], q2 = P[j];
        var ex = q2.x - q1.x, ey = q2.y - q1.y, ed = Math.sqrt(ex * ex + ey * ey) || 1e-3;
        var min = (raioN[i] + raioN[j]) * 1.9 + 0.022;
        if (ed < min) {
          var m = ((min - ed) / ed) * 0.5;
          var m1 = q1.fixo ? 0 : q2.fixo ? 2 * m : m, m2 = q2.fixo ? 0 : q1.fixo ? 2 * m : m;
          q1.x -= ex * m1; q1.y -= ey * m1; q2.x += ex * m2; q2.y += ey * m2;
        }
      }
    }
    return {
      A: A,
      passo: passo,
      pesos: montarLigas,
      fixar: function (id, u, v) { var p = P[idx[id]]; if (!p) return; p.fixo = true; p.x = u * A; p.y = v; p.vx = p.vy = 0; },
      soltar: function (id) { var p = P[idx[id]]; if (p) p.fixo = false; },
      exportar: function () {
        var pos = {};
        nos.forEach(function (a, k) { pos[a.id] = { u: P[k].x / A, v: P[k].y }; });
        return { pos: pos, A: A };
      }
    };
  }
  function calcularLayout(topo, pesos, largura, altura, op) {
    op = op || {};
    var f = criarFisica(topo, pesos, largura, altura, op);
    var iter = op.iteracoes || 400, a0 = op.alfa == null ? 1 : op.alfa;
    for (var it = 0; it < iter; it++) f.passo(a0 * Math.pow(0.02, it / iter));
    return f.exportar();
  }
  /* Ajuste fixo do layout normalizado à área útil: escala uniforme, centralizado. */
  function calcularAjuste(res, W, H, m, folga) {
    var minx = Infinity, maxx = -Infinity, miny = Infinity, maxy = -Infinity, id;
    for (id in res.pos) {
      var x = res.pos[id].u * res.A, y = res.pos[id].v;
      if (x < minx) minx = x; if (x > maxx) maxx = x;
      if (y < miny) miny = y; if (y > maxy) maxy = y;
    }
    var bw = Math.max(1e-3, maxx - minx), bh = Math.max(1e-3, maxy - miny);
    var aw = Math.max(10, W - m.esquerda - m.direita - folga * 2), ah = Math.max(10, H - m.topo - m.base - folga * 2);
    var s = Math.min(aw / bw, ah / bh);
    return { s: s, A: res.A, minx: minx, miny: miny, ox: m.esquerda + folga + (aw - bw * s) / 2, oy: m.topo + folga + (ah - bh * s) / 2 };
  }
  function paraMundo(aj, u, v) { return { x: aj.ox + (u * aj.A - aj.minx) * aj.s, y: aj.oy + (v - aj.miny) * aj.s }; }
  function doMundo(aj, x, y) { return { u: ((x - aj.ox) / aj.s + aj.minx) / aj.A, v: (y - aj.oy) / aj.s + aj.miny }; }
  function encaixar(res, W, H, m, folga) {
    var aj = calcularAjuste(res, W, H, m, folga), out = {};
    for (var id in res.pos) out[id] = paraMundo(aj, res.pos[id].u, res.pos[id].v);
    return out;
  }

  /* =====================================================================
     Motor: o estado da rede é função do tempo. Por isso dá para rebobinar.
     ===================================================================== */
  function excitacao(dt, pico, retencao, tau) {
    if (dt < 0) return 0;
    var subida = 180;
    if (dt < subida) return pico * (dt / subida);
    if (dt < subida + retencao) return pico;
    return pico * Math.exp(-(dt - subida - retencao) / tau);
  }

  function Motor(topo, op) {
    this.topo = topo;
    this.dia = (op && op.diaMs) || 86400000;
    this.eventos = [];
    this.estimulos = [];
    this.reforcos = {};
    this.apos = {};
    this.peso0 = {};
    this.limiares = {};
    this.seq = 0;
    this.pos = {};
    this.alcances = {};
    this.tk = null;
  }
  Motor.prototype.iniciar = function (tk, pesosSalvos) {
    var self = this, n = tk.num;
    this.tk = tk;
    this.topo.sinapses.forEach(function (s) {
      if (!self.reforcos[s.chave]) self.reforcos[s.chave] = [];
      if (self.peso0[s.chave] != null) return;
      var salvo = pesosSalvos && pesosSalvos[s.chave];
      self.peso0[s.chave] = salvo != null ? salvo
        : s.natureza === 'reciproca' ? n['peso-reciproca']
        : s.natureza === 'latente' ? n['peso-latente'] : n['peso-unilateral'];
    });
    this.topo.agentes.forEach(function (a) {
      self.limiares[a.id] = a.limiar != null ? a.limiar : n['limiar-padrao'];
    });
  };
  Motor.prototype.definirPosicoes = function (pos) {
    this.pos = pos;
    this.alcances = {};
  };
  Motor.prototype.distancia = function (a, b) {
    var p = this.pos[a], q = this.pos[b];
    if (!p || !q) return 0;
    return Math.sqrt((p.x - q.x) * (p.x - q.x) + (p.y - q.y) * (p.y - q.y));
  };
  Motor.prototype.alcance = function (id) {
    if (this.alcances[id] != null) return this.alcances[id];
    var self = this, m = 1;
    this.topo.agentes.forEach(function (a) { m = Math.max(m, self.distancia(id, a.id)); });
    return (this.alcances[id] = m);
  };
  /* Peso da sinapse no instante t: reforços somados e atrofia contínua até o piso.
     Guarda o peso logo após cada reforço, para a consulta ser O(log n) em sessões longas. */
  Motor.prototype.piso = function (k) {
    var s = this.topo.porChave[k], n = this.tk.num;
    return s && s.natureza === 'latente' ? n['peso-latente'] : n['peso-piso'];
  };
  Motor.prototype.recalcular = function (k, desde) {
    var n = this.tk.num, piso = this.piso(k), meia = n['meia-vida-atrofia'] * this.dia;
    var lista = this.reforcos[k], apos = this.apos[k] || (this.apos[k] = []);
    var w = desde > 0 ? apos[desde - 1] : this.peso0[k], tAnt = desde > 0 ? lista[desde - 1] : 0;
    for (var i = desde; i < lista.length; i++) {
      w = piso + (w - piso) * Math.pow(0.5, Math.max(0, lista[i] - tAnt) / meia);
      w = w + n['taxa-reforco'] * (1 - w);
      apos[i] = w; tAnt = lista[i];
    }
    apos.length = lista.length;
  };
  Motor.prototype.peso = function (k, t) {
    var n = this.tk.num, piso = this.piso(k), meia = n['meia-vida-atrofia'] * this.dia;
    var lista = this.reforcos[k] || [], apos = this.apos[k] || [];
    var lo = 0, hi = lista.length;
    while (lo < hi) { var m = (lo + hi) >> 1; if (lista[m] <= t) lo = m + 1; else hi = m; }
    var i = lo - 1;
    var w = i >= 0 ? apos[i] : (this.peso0[k] == null ? piso : this.peso0[k]);
    var tAnt = i >= 0 ? lista[i] : 0;
    return piso + (w - piso) * Math.pow(0.5, Math.max(0, t - tAnt) / meia);
  };
  Motor.prototype.pesos = function (t) {
    var self = this, out = {};
    this.topo.sinapses.forEach(function (s) { out[s.chave] = self.peso(s.chave, t); });
    return out;
  };
  Motor.prototype.flash = function (k, t) {
    var d = this.tk.num['reforco'], lista = this.reforcos[k] || [], f = 0;
    for (var i = lista.length - 1; i >= 0; i--) {
      var dt = t - lista[i];
      if (dt < 0) continue;
      if (dt > d) break;
      f = Math.max(f, 1 - dt / d);
    }
    return f;
  };
  Motor.prototype.indiceDesde = function (t) {
    var lo = 0, hi = this.eventos.length;
    while (lo < hi) { var mid = (lo + hi) >> 1; if (this.eventos[mid].t < t) lo = mid + 1; else hi = mid; }
    return lo;
  };
  Motor.prototype.garantirSinapse = function (a, b) {
    var k = chave(a, b), topo = this.topo;
    if (topo.porChave[k]) return k;
    var s = { chave: k, a: a, b: b, natureza: 'latente' };
    topo.porChave[k] = s; topo.sinapses.push(s);
    topo.vizinhos[a][b] = s; topo.vizinhos[b][a] = s;
    this.reforcos[k] = [];
    this.peso0[k] = this.tk.num['peso-latente'];
    return k;
  };
  Motor.prototype.registrar = function (ev, agora) {
    var n = this.tk.num;
    var e = {
      id: ++this.seq, t: ev.t != null ? ev.t : agora, tipo: TIPO[ev.tipo] ? ev.tipo : 'informe',
      de: ev.de || null, para: ev.para || null, prioridade: PRIORIDADE[ev.prioridade] ? ev.prioridade : 'normal',
      texto: ev.texto || '', origem: ev.origem || null
    };
    if (e.de && !this.topo.porId[e.de]) e.de = null;
    if (e.tipo === 'informe') e.para = '*';
    else if (e.para && !this.topo.porId[e.para]) e.para = null;
    e.inicio = e.t + (e.tipo === 'entrega' ? n['pulso-entrega'] * 0.5 : 0);
    e.dur = 0;
    if (e.de && e.para && e.para !== '*' && e.de !== e.para) {
      e.chave = this.garantirSinapse(e.de, e.para);
      var w = this.peso(e.chave, e.inicio);
      var base = lerp(n['travessia-fraca'], n['travessia-forte'], clamp((w - n['peso-piso']) / (1 - n['peso-piso']), 0, 1));
      e.dur = base / (n['fator-' + e.prioridade] || 1);
      if (UTEIS[e.tipo]) {
        var lista = this.reforcos[e.chave], tr = e.inicio + e.dur, i = lista.length;
        while (i > 0 && lista[i - 1] > tr) i--;
        lista.splice(i, 0, tr);
        this.recalcular(e.chave, i);
      }
    } else if (e.para === '*') {
      e.dur = n['onda-informe'];
    }
    var j = this.eventos.length;
    while (j > 0 && this.eventos[j - 1].t > e.t) j--;
    this.eventos.splice(j, 0, e);
    return e;
  };
  Motor.prototype.estimular = function (e, agora) {
    var est = { id: ++this.seq, t: e.t != null ? e.t : agora, no: e.no, afinidade: {}, texto: e.texto || '' };
    for (var k in (e.afinidade || {})) est.afinidade[k] = e.afinidade[k];
    if (est.afinidade[est.no] == null) est.afinidade[est.no] = 1;
    var i = this.estimulos.length;
    while (i > 0 && this.estimulos[i - 1].t > est.t) i--;
    this.estimulos.splice(i, 0, est);
    this.registrar({ t: est.t, tipo: 'briefing', de: null, para: est.no, prioridade: e.prioridade || 'alta', texto: est.texto, origem: e.origem || 'externo' }, agora);
    return est;
  };
  Motor.prototype.chegada = function (ev, id) {
    if (ev.para === '*') {
      if (!ev.de || id === ev.de) return null;
      return ev.t + 120 + (this.distancia(ev.de, id) / this.alcance(ev.de)) * ev.dur;
    }
    if (ev.para === id && ev.de) return ev.inicio + ev.dur;
    if (ev.para === id && !ev.de) return ev.t;
    return null;
  };
  /* {v, disparou, tremor, tipo}: disparou = passou do limiar (acende); abaixo dele, só um tremor.
     tipo = o tráfego que mais o excita agora: a coroa de luz toma essa cor. */
  Motor.prototype.ativacao = function (id, t) {
    var n = this.tk.num, tau = n['decaimento-ativacao'], lim = this.limiares[id];
    var melhor = 0, disparou = false, tremor = 0, tipo = 'briefing', i, v;
    for (i = this.estimulos.length - 1; i >= 0; i--) {
      var e = this.estimulos[i];
      if (e.t > t) continue;
      if (t - e.t > 45000) break;
      var aff = e.afinidade[id] || 0;
      var dt = t - (e.t + (this.distancia(e.no, id) / this.alcance(e.no)) * n['onda-estimulo']);
      if (dt < 0) continue;
      if (aff >= lim) { v = excitacao(dt, aff, 2400, tau); if (v > melhor) { melhor = v; disparou = true; tipo = 'briefing'; } }
      else if (aff > 0) { v = excitacao(dt, aff * 0.6, 0, tau * 0.3); if (v > tremor) tremor = v; }
    }
    for (i = this.indiceDesde(t - 45000); i < this.eventos.length; i++) {
      var ev = this.eventos[i];
      if (ev.t > t) break;
      if (!ev.de) continue;
      /* quem pede (tarefa, pergunta) fica aceso esperando; quem recebe uma tarefa fica aceso trabalhando */
      var espera = ev.tipo === 'tarefa' || ev.tipo === 'pergunta' ? 3600 : 1200;
      if (ev.de === id) {
        v = excitacao(t - ev.t, 0.8, espera, tau);
        if (v >= melhor) { melhor = v; disparou = true; tipo = ev.tipo; }
      }
      var ch = this.chegada(ev, id);
      if (ch != null && t >= ch) {
        v = excitacao(t - ch, ev.para === '*' ? 0.45 : 0.74, ev.para === '*' ? 200 : espera, tau);
        if (v >= melhor) { melhor = v; disparou = true; tipo = ev.tipo; }
      }
    }
    return { v: melhor, disparou: disparou, tremor: tremor, tipo: tipo };
  };
  Motor.prototype.pulsos = function (t) {
    var res = [], self = this;
    for (var i = this.indiceDesde(t - 15000); i < this.eventos.length; i++) {
      var ev = this.eventos[i];
      if (ev.t > t) break;
      if (!ev.de) continue;
      if (ev.para === '*') {
        Object.keys(this.topo.vizinhos[ev.de]).forEach(function (alvo) {
          var ch = self.chegada(ev, alvo);
          if (t >= ev.t && t < ch) res.push({ ev: ev, de: ev.de, para: alvo, chave: chave(ev.de, alvo), p: (t - ev.t) / (ch - ev.t) });
        });
      } else if (ev.chave && t >= ev.inicio && t < ev.inicio + ev.dur) {
        res.push({ ev: ev, de: ev.de, para: ev.para, chave: ev.chave, p: (t - ev.inicio) / ev.dur });
      }
    }
    return res;
  };
  Motor.prototype.ondas = function (t) {
    var n = this.tk.num, res = [];
    for (var i = this.estimulos.length - 1; i >= 0; i--) {
      var e = this.estimulos[i];
      if (e.t > t) continue;
      var p = (t - e.t) / n['onda-estimulo'];
      if (p > 1.15) break;
      res.push({ no: e.no, p: Math.min(1, p), tipo: 'briefing' });
    }
    for (var j = this.indiceDesde(t - n['onda-informe'] * 1.2); j < this.eventos.length; j++) {
      var ev = this.eventos[j];
      if (ev.t > t) break;
      if (ev.para === '*' && ev.de) res.push({ no: ev.de, p: Math.min(1, (t - ev.t) / ev.dur), tipo: 'informe' });
    }
    return res;
  };
  Motor.prototype.entrega = function (id, t) {
    var d = this.tk.num['pulso-entrega'];
    for (var i = this.indiceDesde(t - d); i < this.eventos.length; i++) {
      var ev = this.eventos[i];
      if (ev.t > t) break;
      if (ev.tipo === 'entrega' && ev.de === id) return (t - ev.t) / d;
    }
    return -1;
  };
  Motor.prototype.trocas = function (filtro, t, max) {
    var res = [];
    for (var i = this.indiceDesde(t + 1) - 1; i >= 0 && res.length < (max || 5); i--) {
      var ev = this.eventos[i];
      if (filtro(ev)) res.push(ev);
    }
    return res;
  };

  /* =====================================================================
     Demonstração: duas propagações reais pela topologia, em alternância.
     Passos: [ms desde o estímulo, tipo, de, para, prioridade, texto]
     ===================================================================== */
  var CENARIOS = [
    {
      titulo: 'Lead pede orçamento de um app de agendamento', entrada: 'comercial', duracao: 20000,
      afinidade: {
        comercial: 1, produto: 0.86, financeiro: 0.72, dev_backend: 0.64, diretor: 0.62, projetos: 0.6, design: 0.58,
        juridico: 0.56, seguranca: 0.53, prospeccao: 0.44, socio_tecnologia: 0.42, dev_mobile: 0.4, dados: 0.38,
        dev_frontend: 0.36, socio_estrategia: 0.34, marketing: 0.3, cs: 0.22, copy: 0.12, seo: 0.08, rh: 0.06
      },
      passos: [
        [900, 'tarefa', 'comercial', 'produto', 'alta', 'Escopo inicial do app de agendamento'],
        [1300, 'pergunta', 'comercial', 'financeiro', 'normal', 'Faixa de preço para 12 semanas?'],
        [2400, 'tarefa', 'produto', 'design', 'normal', 'Fluxo de agendamento em 3 telas'],
        [2600, 'pergunta', 'produto', 'dev_backend', 'normal', 'Integração com WhatsApp é viável?'],
        [2900, 'tarefa', 'produto', 'projetos', 'normal', 'Cronograma preliminar'],
        [3700, 'pergunta', 'dev_backend', 'seguranca', 'normal', 'Dados de agenda pedem que cuidados?'],
        [4300, 'resposta', 'financeiro', 'comercial', 'normal', 'Faixa aprovada dentro da margem'],
        [5200, 'resposta', 'seguranca', 'dev_backend', 'normal', 'Criptografar telefone e histórico'],
        [5600, 'alerta', 'seguranca', 'dev_mobile', 'critica', 'Biblioteca de SMS com falha conhecida'],
        [6200, 'resposta', 'dev_backend', 'produto', 'normal', 'Viável, duas semanas de integração'],
        [6700, 'entrega', 'design', 'produto', 'normal', 'Wireframes v1'],
        [7300, 'entrega', 'projetos', 'produto', 'normal', 'Cronograma de 12 semanas'],
        [8400, 'entrega', 'produto', 'comercial', 'alta', 'Escopo e estimativa'],
        [9400, 'tarefa', 'comercial', 'juridico', 'normal', 'Minuta do contrato'],
        [10900, 'revisao', 'juridico', 'comercial', 'normal', 'Cláusula de dados ajustada'],
        [12000, 'decisao', 'diretor', 'comercial', 'alta', 'Aprovado: enviar a proposta'],
        [13400, 'informe', 'diretor', null, 'baixa', 'Proposta enviada ao cliente']
      ]
    },
    {
      titulo: 'Cliente relata falha no login do app', entrada: 'cs', duracao: 16000,
      afinidade: {
        cs: 1, dev_mobile: 0.9, dados: 0.7, dev_backend: 0.68, seguranca: 0.58, produto: 0.55, dev_frontend: 0.46,
        socio_tecnologia: 0.45, projetos: 0.4, diretor: 0.34, comercial: 0.3, design: 0.2, juridico: 0.18,
        financeiro: 0.12, marketing: 0.1, rh: 0.05, copy: 0.05, seo: 0.05, prospeccao: 0.05, socio_estrategia: 0.1
      },
      passos: [
        [900, 'tarefa', 'cs', 'dev_mobile', 'critica', 'Reproduzir a falha no login'],
        [1300, 'pergunta', 'cs', 'dados', 'alta', 'Quantas sessões foram afetadas?'],
        [2500, 'pergunta', 'dev_mobile', 'dev_backend', 'alta', 'O token está expirando antes da hora?'],
        [3300, 'resposta', 'dados', 'cs', 'normal', 'Uma em cada 25 sessões desde ontem'],
        [4100, 'resposta', 'dev_backend', 'dev_mobile', 'alta', 'Relógio do servidor adiantado'],
        [4700, 'alerta', 'dev_mobile', 'seguranca', 'alta', 'Tokens aceitos fora da janela de validade'],
        [5800, 'revisao', 'seguranca', 'dev_mobile', 'alta', 'Correção aprovada'],
        [6700, 'entrega', 'dev_mobile', 'cs', 'alta', 'Correção publicada'],
        [7600, 'pergunta', 'cs', 'produto', 'baixa', 'Incluir aviso de sessão no roadmap?'],
        [8600, 'resposta', 'produto', 'cs', 'baixa', 'Entra no próximo ciclo'],
        [9600, 'informe', 'cs', null, 'baixa', 'Incidente de login encerrado']
      ]
    }
  ];

  /* =====================================================================
     Rede: o canvas vivo em tela cheia, com a interação de um grafo de notas:
     zoom (roda ou pinça), arrastar a vista, arrastar neurônios com física viva.
     Um botão por neurônio garante teclado, leitor de tela e toque.
     ===================================================================== */
  var contadorId = 0;
  function uid(p) { return 'mr-' + p + '-' + (++contadorId); }
  function conjunto(lista) {
    if (!lista) return null;
    var s = {}; lista.forEach(function (x) { s[x] = true; }); return s;
  }

  function Rede(props) {
    props = props || {};
    var raiz = el('div', { 'class': 'mr-rede', role: 'group', 'aria-roledescription': 'rede neural',
      'aria-label': props.rotulo || 'Rede de agentes. Tab percorre os agentes; Enter abre a ficha; Esc limpa a seleção; + e − aproximam; 0 centraliza.' });
    var canvas = el('canvas', { 'aria-hidden': 'true' });
    var camada = el('div', { 'class': 'mr-rede-nos' });
    var dica = el('div', { 'class': 'mr-dica mr-vidro', role: 'tooltip', id: uid('dica'), hidden: true });
    var aviso = el('div', { 'class': 'mr-sr', 'aria-live': 'polite' });
    raiz.appendChild(canvas); raiz.appendChild(camada);
    var ctx = canvas.getContext('2d');

    var topo = montarTopologia(props.dados);
    var motor = new Motor(topo, { diaMs: props.diaMs || (props.demo === false ? 86400000 : 60000) });
    var tk = lerTokens(null);
    motor.iniciar(tk, props.pesos);
    var reduzir = false;
    var margem = { topo: 16, direita: 16, base: 16, esquerda: 16 };
    if (props.margens) for (var mk in props.margens) margem[mk] = props.margens[mk];
    var W = 0, H = 0, dpr = 1, escalaNo = 1;
    var fisica = null, ajuste = null, alfaVivo = 0, pos = {}, origem = null, tTrans = -1;
    var vista = { k: 1, x: 0, y: 0 }, animVista = null;
    var arrasto = null, panoramica = null, pinca = null, ponteiros = {}, suprimirClique = false;
    var t0 = performance.now();
    var modo = 'ao-vivo', tVista = 0, tocando = false, tocarDesde = 0, tocarBase = 0;
    var foco = null, focoVisto = null, fatorFoco = 0, selecionado = null;
    var filtro = conjunto(props.filtro);
    var botoes = {}, transformacoes = {}, fase = {}, membros = {}, sementes = {}, pesoMolas = {};
    var plancton = [];
    topo.regioes.forEach(function (r) { membros[r.id] = []; });
    topo.agentes.forEach(function (a) {
      fase[a.id] = hashTexto(a.id);
      (membros[a.regiao] = membros[a.regiao] || []).push(a.id);
    });
    var demo = props.demo === false ? null : criarDemo(props.cenarios || CENARIOS);
    var rodando = false, visivel = true, ultimo = 0, ultimoDesenho = 0, ultimaNotificacao = 0, ultimaDica = 0, ultimasMolas = 0;
    var anunciadoAte = 0, pararTema = null, ro = null, io = null, atividade = 0;

    var controles = props.controles === false ? null : criarControles();
    raiz.appendChild(dica); raiz.appendChild(aviso);
    if (controles) raiz.appendChild(controles);

    function lerMovimento() {
      reduzir = props.reduzirMovimento === true || (props.reduzirMovimento !== false && movimentoReduzido());
      if (reduzir) raiz.setAttribute('data-movimento-reduzido', ''); else raiz.removeAttribute('data-movimento-reduzido');
    }
    lerMovimento();

    function agora() { return performance.now() - t0; }
    function tempoVista() {
      if (modo === 'ao-vivo') return agora();
      if (tocando) {
        var t = tocarBase + (performance.now() - tocarDesde);
        if (t >= agora()) { modo = 'ao-vivo'; tocando = false; notificar(); return agora(); }
        return t;
      }
      return tVista;
    }
    function raio(id) { return raioDoGrau(tk, topo.porId[id].grau) * escalaNo; }
    function semente(k) { return sementes[k] != null ? sementes[k] : (sementes[k] = hashTexto(k)); }

    function criarDemo(cenarios) {
      var i = 0, proximo = 1500;
      return function (t) {
        if (t > proximo + 30000) proximo = t + 1000;
        var guarda = 0;
        while (t + 2000 >= proximo && guarda++ < 4) {
          var c = cenarios[i % cenarios.length]; i++;
          var ini = proximo;
          motor.estimular({ t: ini, no: c.entrada, afinidade: c.afinidade, texto: c.titulo, prioridade: 'alta' }, t);
          c.passos.forEach(function (p) {
            motor.registrar({ t: ini + p[0], tipo: p[1], de: p[2], para: p[3], prioridade: p[4], texto: p[5] }, t);
          });
          proximo = ini + (c.duracao || 16000);
        }
      };
    }

    /* ---------- vista: tela = mundo × k + (x, y) ---------- */
    function paraTela(p) { return { x: p.x * vista.k + vista.x, y: p.y * vista.k + vista.y }; }
    function telaParaMundo(x, y) { return { x: (x - vista.x) / vista.k, y: (y - vista.y) / vista.k }; }
    function zoomEm(x, y, f) {
      var n = tk.num, k2 = clamp(vista.k * f, n['zoom-min'], n['zoom-max']);
      f = k2 / vista.k;
      vista.x = x - (x - vista.x) * f; vista.y = y - (y - vista.y) * f; vista.k = k2;
      animVista = null; ultimoDesenho = 0;
    }
    function centralizar() {
      animVista = { de: { k: vista.k, x: vista.x, y: vista.y }, t0: performance.now() };
    }
    function criarControles() {
      var c = el('div', { 'class': 'mr-rede-controles mr-vidro', role: 'group', 'aria-label': 'Zoom da rede' });
      var mais = botaoIcone('Aproximar (+)', 'mais'), menos = botaoIcone('Afastar (−)', 'menos'), centro = botaoIcone('Centralizar (0)', 'centralizar');
      mais.addEventListener('click', function () { zoomEm(W / 2, H / 2, 1.3); });
      menos.addEventListener('click', function () { zoomEm(W / 2, H / 2, 1 / 1.3); });
      centro.addEventListener('click', centralizar);
      c.appendChild(mais); c.appendChild(menos); c.appendChild(centro);
      if (props.topoControles != null) c.style.top = props.topoControles + 'px';
      return c;
    }

    /* ---------- botões dos neurônios: foco, clique e arrasto ---------- */
    function rotuloNo(a) {
      var at = motor.ativacao(a.id, tempoVista());
      var v = at.disparou ? at.v : 0;
      return a.nome + ', ' + a.cargo + ', ' + (topo.nomeRegiao[a.regiao] || a.regiao) + '. Ativação ' + pct(v) +
        (v >= motor.limiares[a.id] ? ', acima do limiar' : ', abaixo do limiar') + '. ' + a.grau + ' sinapses.';
    }
    topo.agentes.forEach(function (a) {
      var b = el('button', { type: 'button', 'class': 'mr-no', 'data-id': a.id, 'aria-describedby': dica.id, 'aria-pressed': 'false' });
      b.addEventListener('pointerenter', function (ev) { if (ev.pointerType === 'mouse' && !panoramica) focar({ tipo: 'no', id: a.id }); });
      b.addEventListener('pointerleave', function (ev) {
        if (ev.pointerType === 'mouse' && !arrasto && foco && foco.id === a.id && doc.activeElement !== b) focar(null);
      });
      b.addEventListener('focus', function () { b.setAttribute('aria-label', rotuloNo(a)); focar({ tipo: 'no', id: a.id, teclado: true }); });
      b.addEventListener('blur', function () { if (foco && foco.id === a.id && !arrasto) focar(null); });
      b.addEventListener('pointerdown', function (ev) {
        if (ev.button > 0 || !fisica) return;
        try { b.setPointerCapture(ev.pointerId); } catch (e) { /* sem captura */ }
        arrasto = { id: a.id, pointerId: ev.pointerId, x0: ev.clientX, y0: ev.clientY, movido: false };
      });
      b.addEventListener('pointermove', function (ev) {
        if (!arrasto || arrasto.pointerId !== ev.pointerId) return;
        var dx = ev.clientX - arrasto.x0, dy = ev.clientY - arrasto.y0;
        if (!arrasto.movido && Math.abs(dx) + Math.abs(dy) > 4) { arrasto.movido = true; raiz.setAttribute('data-arrastando', ''); }
        if (!arrasto.movido) return;
        var q = coordenadas(ev), w = telaParaMundo(q.x, q.y), nv = doMundo(ajuste, w.x, w.y);
        fisica.fixar(a.id, nv.u, nv.v);
        alfaVivo = Math.max(alfaVivo, 0.3);
        if (!foco || foco.id !== a.id) focar({ tipo: 'no', id: a.id });
      });
      function soltar(ev) {
        if (!arrasto || arrasto.pointerId !== ev.pointerId) return;
        var movido = arrasto.movido;
        fisica.soltar(arrasto.id);
        arrasto = null;
        raiz.removeAttribute('data-arrastando');
        if (movido) { suprimirClique = true; alfaVivo = Math.max(alfaVivo, 0.2); }
      }
      b.addEventListener('pointerup', soltar);
      b.addEventListener('pointercancel', soltar);
      b.addEventListener('click', function () {
        if (suprimirClique) { suprimirClique = false; return; }
        selecionar(selecionado === a.id ? null : a.id, true);
      });
      b.setAttribute('aria-label', a.nome + ', ' + a.cargo);
      botoes[a.id] = b;
      camada.appendChild(b);
    });
    function posicionarBotoes() {
      topo.agentes.forEach(function (a) {
        var p = pos[a.id], b = botoes[a.id];
        if (!p) return;
        var s = paraTela(p), r = Math.max(12, raio(a.id) * vista.k + 4);
        var tr = 'translate(' + (s.x - r).toFixed(1) + 'px,' + (s.y - r).toFixed(1) + 'px)', tam = Math.round(r * 2) + 'px';
        if (transformacoes[a.id] === tr + tam) return;
        transformacoes[a.id] = tr + tam;
        b.style.width = b.style.height = tam;
        b.style.transform = tr;
      });
    }

    /* ---------- medidas, layout e física ---------- */
    function areaUtil() {
      return { w: Math.max(40, W - margem.esquerda - margem.direita), h: Math.max(40, H - margem.topo - margem.base) };
    }
    function folga() { return raioDoGrau(tk, 11) * escalaNo + 6; }
    function medir() {
      var r = raiz.getBoundingClientRect();
      var w = Math.round(r.width), h = Math.round(r.height);
      if (w < 20 || h < 20) return;
      var nd = Math.min(2, window.devicePixelRatio || 1);
      if (w === W && h === H && nd === dpr && fisica) return;
      var antes = W && H ? W / H : 0;
      W = w; H = h; dpr = nd;
      canvas.width = Math.round(W * dpr); canvas.height = Math.round(H * dpr);
      tk = lerTokens(raiz); motor.tk = tk;
      escalaNo = clamp(Math.min(W, H) / 520, 0.72, 1.1);
      if (!plancton.length) plancton = criarPlancton(Math.round(tk.num['plancton-quantidade']), 11);
      var mudou = !fisica || !antes || Math.abs(Math.log((W / H) / antes)) > 0.2;
      if (mudou) recalcularLayout(!fisica);
      else { var res = fisica.exportar(); ajuste = calcularAjuste(res, W, H, margem, folga()); atualizarPosicoes(); posicionarBotoes(); }
      iniciar();
    }
    function recalcularLayout(primeira) {
      var area = areaUtil(), pz = motor.pesos(tempoVista());
      var opR = function (a) { return raioDoGrau(tk, a.grau) * escalaNo; };
      var anterior = fisica ? fisica.exportar().pos : null;
      var res = calcularLayout(topo, pz, area.w, area.h, { anterior: anterior, iteracoes: primeira ? 420 : 180, alfa: primeira ? 1 : 0.35, semente: 20, raio: opR });
      var antigo = pos;
      fisica = criarFisica(topo, pz, area.w, area.h, { anterior: res.pos, raio: opR });
      pesoMolas = pz;
      ajuste = calcularAjuste(res, W, H, margem, folga());
      if (!primeira && Object.keys(antigo).length) { origem = antigo; tTrans = performance.now(); }
      atualizarPosicoes();
      posicionarBotoes();
    }
    function atualizarPosicoes() {
      if (!fisica || !ajuste) return;
      var res = fisica.exportar(), novo = {}, id;
      for (id in res.pos) novo[id] = paraMundo(ajuste, res.pos[id].u, res.pos[id].v);
      if (tTrans >= 0 && origem) {
        var pt = clamp((performance.now() - tTrans) / 600, 0, 1), e = tk.curva['curva-saida'](pt);
        for (id in novo) { var o = origem[id] || novo[id]; novo[id] = { x: lerp(o.x, novo[id].x, e), y: lerp(o.y, novo[id].y, e) }; }
        if (pt >= 1) tTrans = -1;
      }
      pos = novo;
      motor.definirPosicoes(pos);
    }
    /* o que a rede aprende muda as molas: quem trabalha junto se aproxima devagar */
    function atualizarMolas() {
      var pz = motor.pesos(tempoVista()), mudou = false;
      for (var k in pz) if (Math.abs((pesoMolas[k] || 0) - pz[k]) > 0.01) { mudou = true; break; }
      if (!mudou) return;
      pesoMolas = pz;
      fisica.pesos(pz);
      alfaVivo = Math.max(alfaVivo, 0.03);
    }

    /* ---------- laço de quadros ---------- */
    function iniciar() {
      if (rodando || !visivel || !W) return;
      rodando = true; ultimo = 0;
      Relogio.inscrever(quadro);
    }
    function parar() {
      if (!rodando) return;
      rodando = false;
      Relogio.cancelar(quadro);
    }
    function quadro(ts) {
      if (!raiz.isConnected) { parar(); return; }
      var dt = ultimo ? Math.min(100, ts - ultimo) : 16;
      ultimo = ts;
      if (demo) demo(agora());
      var arrastando = !!(arrasto && arrasto.movido);
      var viva = alfaVivo > 0.002 || arrastando;
      if (viva && fisica) {
        fisica.passo(Math.max(alfaVivo, arrastando ? 0.12 : 0));
        alfaVivo *= 0.965;
        if (alfaVivo <= 0.002) alfaVivo = 0;
      }
      if (fisica && ts - ultimasMolas > 1000) { ultimasMolas = ts; atualizarMolas(); }
      if (animVista) {
        var pv = clamp((performance.now() - animVista.t0) / 450, 0, 1), ev = tk.curva['curva-saida'](pv);
        vista.k = lerp(animVista.de.k, 1, ev); vista.x = lerp(animVista.de.x, 0, ev); vista.y = lerp(animVista.de.y, 0, ev);
        if (pv >= 1) animVista = null;
      }
      var interagindo = viva || animVista || panoramica || pinca || tTrans >= 0;
      if (reduzir && !interagindo && ts - ultimoDesenho < 240 && fatorFoco === (foco ? 1 : 0)) return;
      atualizarPosicoes();
      posicionarBotoes();
      desenhar(reduzir ? 1000 : dt);
      ultimoDesenho = ts;
      if (ts - ultimaNotificacao > 250) { ultimaNotificacao = ts; notificar(); anunciar(); }
      if (arrastando) dica.hidden = true;
      else if (foco && ts - ultimaDica > 250) { ultimaDica = ts; atualizarDica(); }
      else if (foco && interagindo) posicionarDica();
    }

    function desenhar(dt) {
      var t = tempoVista();
      var c = tk.cor, n = tk.num, k = vista.k;
      fatorFoco = aproximar(fatorFoco, foco ? 1 : 0, dt / n['transicao-ui']);
      if (foco) focoVisto = foco;
      var f = fatorFoco > 0 ? foco || focoVisto : null;
      var recuo = lerp(1, n['opacidade-recuo'], fatorFoco);
      var sf = f && f.tipo === 'sinapse' ? topo.porChave[f.chave] : null;
      function vizinho(id) {
        var s = f && !sf ? topo.vizinhos[f.id][id] : null;
        return !!(s && s.natureza !== 'latente');
      }
      function noRelevante(id) {
        if (!f) return true;
        if (sf) return id === sf.a || id === sf.b;
        return id === f.id || vizinho(id);
      }
      function sinapseRelevante(s) {
        if (!f) return true;
        if (sf) return s.chave === sf.chave;
        return s.a === f.id || s.b === f.id;
      }

      /* ativação de todos, antes de desenhar: o plâncton acende com a atividade */
      var lista = topo.agentes.map(function (a) { return { a: a, at: motor.ativacao(a.id, t) }; });
      var acesos = 0;
      lista.forEach(function (it) { if (it.at.disparou && it.at.v >= 0.2) acesos++; });
      atividade = lerp(atividade, acesos / Math.max(1, lista.length), 0.08);
      var ondas = motor.ondas(t);

      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.globalAlpha = 1;
      ctx.globalCompositeOperation = 'source-over';
      ctx.fillStyle = css(c.fundo);
      ctx.fillRect(0, 0, W, H);

      /* 0. plâncton, em coordenadas de tela, com paralaxe */
      var ondasTela = [];
      ondas.forEach(function (o) {
        var p0 = pos[o.no];
        if (!p0) return;
        var s0 = paraTela(p0);
        ondasTela.push({ x: s0.x, y: s0.y, r: lerp(raio(o.no), motor.alcance(o.no) + 40, o.p) * k, p: o.p, cor: corTipo(tk, o.tipo) });
      });
      desenharPlancton(ctx, tk, plancton, W, H, reduzir ? 0 : t, vista.x, vista.y, atividade, reduzir ? [] : ondasTela, reduzir);

      /* daqui em diante, coordenadas do mundo */
      ctx.setTransform(dpr * k, 0, 0, dpr * k, dpr * vista.x, dpr * vista.y);

      /* 1. campos das regiões: névoa, sem borda */
      topo.regioes.forEach(function (rg) {
        var ids = membros[rg.id];
        if (!ids || !ids.length) return;
        var cx = 0, cy = 0;
        ids.forEach(function (id) { cx += pos[id].x; cy += pos[id].y; });
        cx /= ids.length; cy /= ids.length;
        var R = 0;
        ids.forEach(function (id) { R = Math.max(R, Math.sqrt(Math.pow(pos[id].x - cx, 2) + Math.pow(pos[id].y - cy, 2)) + raio(id)); });
        R += 34 * escalaNo;
        var g = ctx.createRadialGradient(cx, cy, 0, cx, cy, R);
        g.addColorStop(0, css(c['campo-regiao'], recuo));
        g.addColorStop(0.6, css(c['campo-regiao'], 0.6 * recuo));
        g.addColorStop(1, css(c['campo-regiao'], 0));
        ctx.fillStyle = g;
        ctx.beginPath(); ctx.arc(cx, cy, R, 0, TAU); ctx.fill();
      });

      /* 2. sinapses: espessura, brilho e fluxo = peso aprendido */
      var pulsos = motor.pulsos(t);
      var ativas = {};
      pulsos.forEach(function (pl) {
        if (filtro && !filtro[pl.ev.tipo]) return;
        ativas[pl.chave] = corTipo(tk, pl.ev.tipo);
      });
      topo.sinapses.forEach(function (s) {
        var pa = pos[s.a], pb = pos[s.b];
        if (!pa || !pb) return;
        var w = motor.peso(s.chave, t);
        var rel = sinapseRelevante(s);
        var latente = s.natureza === 'latente' && w <= n['peso-latente'] + 0.01;
        var focada = f && rel && !sf;
        if (latente && !ativas[s.chave] && !focada) {
          desenharSinapse(ctx, tk, pa.x, pa.y, pb.x, pb.y, { peso: w, natureza: s.natureza, alfa: f ? recuo : 1 });
          return;
        }
        desenharSinapse(ctx, tk, pa.x, pa.y, pb.x, pb.y, {
          peso: w, natureza: s.natureza, flash: motor.flash(s.chave, t), ativa: ativas[s.chave] || null,
          realce: f && rel ? fatorFoco : 0, alfa: rel ? 1 : recuo, tracejada: latente && !ativas[s.chave]
        });
        if (!reduzir && !latente) {
          var sg = segmento(pa, pb, raio(s.a), raio(s.b));
          desenharFluxo(ctx, tk, sg.x1, sg.y1, sg.x2, sg.y2, w, t, semente(s.chave), rel ? 1 : recuo);
        }
      });

      /* 3. ondas de estímulo (briefing) e de informe */
      ondas.forEach(function (o) {
        var p0 = pos[o.no];
        if (!p0) return;
        var r0 = raio(o.no);
        if (reduzir) { if (o.p < 1) desenharOnda(ctx, tk, p0.x, p0.y, r0 * 2.3, 0, o.tipo, true); return; }
        desenharOnda(ctx, tk, p0.x, p0.y, lerp(r0, motor.alcance(o.no) + 40, o.p), o.p, o.tipo, false);
      });

      /* 4. pulsos: cometas; matiz e glifo = tipo, tamanho e velocidade = prioridade */
      pulsos.forEach(function (pl) {
        var pa = pos[pl.de], pb = pos[pl.para];
        if (!pa || !pb) return;
        var s = topo.porChave[pl.chave];
        var alfa = (filtro && !filtro[pl.ev.tipo] ? n['opacidade-apagado'] : 1) * (s && sinapseRelevante(s) ? 1 : recuo);
        var sg = segmento(pa, pb, raio(pl.de), raio(pl.para));
        if (reduzir) desenharPulsoEstatico(ctx, tk, sg.x1, sg.y1, sg.x2, sg.y2, pl.ev.tipo, pl.ev.prioridade, alfa);
        else desenharPulso(ctx, tk, sg.x1, sg.y1, sg.x2, sg.y2, pl.p, pl.ev.tipo, pl.ev.prioridade, alfa, pl.ev.id);
      });

      /* 5. neurônios: tamanho = grau; luz (ou tinta) = ativação; coroa = tráfego */
      lista.sort(function (x, y) { return (x.at.disparou ? x.at.v : 0) - (y.at.disparou ? y.at.v : 0); });
      lista.forEach(function (it) {
        var a = it.a, p = pos[a.id];
        if (!p) return;
        var r = raio(a.id), resp = 0;
        if (!reduzir) {
          resp = Math.sin(TAU * (t / n['respiracao'] + fase[a.id]));
          r *= 1 + n['respiro-escala'] * resp;
        }
        var realce = 0;
        if (f && !sf) realce = a.id === f.id ? fatorFoco : vizinho(a.id) ? 0.55 * fatorFoco : 0;
        desenharNeuronio(ctx, tk, p.x, p.y, r, {
          ativacao: it.at.v, disparou: it.at.disparou, tipo: it.at.tipo, tremor: it.at.tremor, respiro: (resp + 1) / 2,
          entrega: reduzir ? -1 : motor.entrega(a.id, t), selecionado: selecionado === a.id, realce: realce,
          alfa: noRelevante(a.id) ? 1 : recuo
        });
      });

      /* 6. rótulos, em coordenadas de tela: na interação e, com zoom, todos */
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      var rot = {};
      if (selecionado) rot[selecionado] = 'forte';
      if (f && fatorFoco > 0.02) {
        if (sf) { rot[sf.a] = 'forte'; rot[sf.b] = 'forte'; }
        else {
          rot[f.id] = 'forte';
          Object.keys(topo.vizinhos[f.id]).forEach(function (v) {
            if (topo.vizinhos[f.id][v].natureza !== 'latente' && !rot[v]) rot[v] = 'suave';
          });
        }
      }
      var zr = n['zoom-rotulos'], alfaZoom = clamp((k - (zr - 0.3)) / 0.6, 0, 1);
      if (alfaZoom > 0) topo.agentes.forEach(function (a) { if (!rot[a.id]) rot[a.id] = 'zoom'; });
      ctx.font = '400 11px ' + tk.fonte.mono;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';
      ctx.lineJoin = 'round';
      Object.keys(rot).forEach(function (id) {
        var p = pos[id];
        if (!p) return;
        var s = paraTela({ x: p.x, y: p.y + raio(id) }), y = s.y + (selecionado === id ? 10 : 6);
        var tipoR = rot[id];
        var alfa = tipoR === 'forte' ? (selecionado === id ? 1 : fatorFoco) : tipoR === 'suave' ? fatorFoco : alfaZoom * (f ? recuo : 0.9);
        if (tipoR === 'suave' && alfaZoom > 0) alfa = Math.max(alfa, alfaZoom * 0.9);
        if (alfa <= 0.01) return;
        ctx.globalAlpha = alfa;
        ctx.lineWidth = 4;
        ctx.strokeStyle = css(c.fundo);
        ctx.strokeText(id, s.x, y);
        ctx.fillStyle = css(tipoR === 'forte' ? c.texto : c['texto-suave']);
        ctx.fillText(id, s.x, y);
      });
      ctx.globalAlpha = 1;
    }

    /* ---------- foco, dica e seleção ---------- */
    function focar(novo) {
      foco = novo;
      if (!novo) { dica.hidden = true; return; }
      atualizarDica();
    }
    function dadosAgente(id) {
      var a = topo.porId[id], t = tempoVista(), at = motor.ativacao(id, t);
      return {
        id: a.id, nome: a.nome, cargo: a.cargo, regiao: a.regiao, regiaoNome: topo.nomeRegiao[a.regiao] || a.regiao,
        grau: a.grau, modelo: a.modelo || null, ativacao: at.disparou ? at.v : at.tremor, disparou: at.disparou,
        tipo: at.disparou ? at.tipo : null, limiar: motor.limiares[id], sinapses: sinapsesDe(id), trocas: trocasDe(id, 6)
      };
    }
    function sinapsesDe(id) {
      var t = tempoVista(), n = tk.num, out = [];
      Object.keys(topo.vizinhos[id]).forEach(function (v) {
        var s = topo.vizinhos[id][v], w = motor.peso(s.chave, t);
        if (s.natureza === 'latente' && w <= n['peso-latente'] + 0.01) return;
        out.push({ id: v, nome: topo.porId[v].nome, peso: w, natureza: s.natureza });
      });
      out.sort(function (x, y) { return y.peso - x.peso; });
      return out;
    }
    function trocaPlana(ev, t) {
      return {
        id: ev.id, t: ev.t, idade: t - ev.t, tipo: ev.tipo, prioridade: ev.prioridade, texto: ev.texto,
        de: ev.de, para: ev.para, deNome: ev.de ? topo.porId[ev.de].nome : (ev.origem === 'voce' ? 'Você' : 'Entrada'),
        paraNome: ev.para === '*' ? 'toda a rede' : ev.para ? topo.porId[ev.para].nome : ''
      };
    }
    function trocasDe(id, max) {
      var t = tempoVista();
      return motor.trocas(function (ev) { return ev.de === id || ev.para === id; }, t, max || 6).map(function (ev) { return trocaPlana(ev, t); });
    }
    function atualizarDica() {
      if (!foco) return;
      var t = tempoVista();
      if (foco.tipo === 'no') {
        var d = dadosAgente(foco.id);
        preencherDica(dica, { tipo: 'neuronio', agente: d, ativacao: d.ativacao, limiar: d.limiar, modelo: d.modelo, grau: d.grau, regiao: d.regiaoNome, trafego: d.tipo });
      } else {
        var s = topo.porChave[foco.chave];
        if (!s) return;
        preencherDica(dica, {
          tipo: 'sinapse', a: topo.porId[s.a], b: topo.porId[s.b], peso: motor.peso(s.chave, t), natureza: s.natureza,
          trocas: motor.trocas(function (ev) { return ev.chave === s.chave; }, t, 3).map(function (ev) { return trocaPlana(ev, t); })
        });
      }
      dica.hidden = false;
      posicionarDica();
    }
    function posicionarDica() {
      if (!foco || dica.hidden) return;
      var w = dica.offsetWidth, h = dica.offsetHeight, x, y;
      if (foco.tipo === 'no') {
        var p = pos[foco.id];
        if (!p) return;
        var s = paraTela(p), r = raio(foco.id) * vista.k + 14;
        x = s.x + r; y = s.y - h / 2;
        if (x + w > W - 8) x = s.x - r - w;
      } else {
        x = foco.x + 16; y = foco.y + 16;
        if (x + w > W - 8) x = foco.x - 16 - w;
        if (y + h > H - 8) y = foco.y - 16 - h;
      }
      x = clamp(x, 8, Math.max(8, W - w - 8));
      y = clamp(y, margem.topo > 40 ? margem.topo - 8 : 8, Math.max(8, H - h - 8));
      dica.style.transform = 'translate(' + Math.round(x) + 'px,' + Math.round(y) + 'px)';
    }
    function sinapseEm(xt, yt) {
      var t = tempoVista(), n = tk.num, melhor = null, w = telaParaMundo(xt, yt), dm = 7 / vista.k;
      for (var id in pos) {
        var p = pos[id];
        if (Math.sqrt((p.x - w.x) * (p.x - w.x) + (p.y - w.y) * (p.y - w.y)) < raio(id) + 4 / vista.k) return null;
      }
      topo.sinapses.forEach(function (s) {
        var pa = pos[s.a], pb = pos[s.b];
        if (!pa || !pb) return;
        if (s.natureza === 'latente' && motor.peso(s.chave, t) <= n['peso-latente'] + 0.01) return;
        var d = distSegmento(w.x, w.y, pa.x, pa.y, pb.x, pb.y);
        if (d < dm) { dm = d; melhor = s; }
      });
      return melhor;
    }
    function coordenadas(ev) {
      var r = raiz.getBoundingClientRect();
      return { x: ev.clientX - r.left, y: ev.clientY - r.top };
    }

    /* ---------- gestos no vazio: arrastar a vista, pinça, roda ---------- */
    raiz.addEventListener('wheel', function (ev) {
      if (props.roda === 'ctrl' && !ev.ctrlKey && !ev.metaKey) return;
      ev.preventDefault();
      var q = coordenadas(ev), dy = ev.deltaY * (ev.deltaMode === 1 ? 16 : 1);
      zoomEm(q.x, q.y, Math.exp(-dy * (Math.abs(dy) > 40 ? 0.0015 : 0.01)));
    }, { passive: false });
    function valores(o) { return Object.keys(o).map(function (k) { return o[k]; }); }
    function iniciarPinca() {
      var ps = valores(ponteiros);
      var d = Math.sqrt(Math.pow(ps[0].x - ps[1].x, 2) + Math.pow(ps[0].y - ps[1].y, 2)) || 1;
      pinca = { d0: d, k0: vista.k, mx0: (ps[0].x + ps[1].x) / 2, my0: (ps[0].y + ps[1].y) / 2, vx0: vista.x, vy0: vista.y };
      panoramica = null;
    }
    canvas.addEventListener('pointerdown', function (ev) {
      var q = coordenadas(ev);
      ponteiros[ev.pointerId] = q;
      try { canvas.setPointerCapture(ev.pointerId); } catch (e) { /* sem captura */ }
      var qtd = Object.keys(ponteiros).length;
      if (qtd === 2) iniciarPinca();
      else if (qtd === 1) panoramica = { id: ev.pointerId, x0: q.x, y0: q.y, vx: vista.x, vy: vista.y, movido: false };
    });
    canvas.addEventListener('pointermove', function (ev) {
      var q = coordenadas(ev);
      if (ponteiros[ev.pointerId]) ponteiros[ev.pointerId] = q;
      if (pinca && Object.keys(ponteiros).length >= 2) {
        var ps = valores(ponteiros);
        var d = Math.sqrt(Math.pow(ps[0].x - ps[1].x, 2) + Math.pow(ps[0].y - ps[1].y, 2)) || 1;
        var mx = (ps[0].x + ps[1].x) / 2, my = (ps[0].y + ps[1].y) / 2, n = tk.num;
        var k2 = clamp(pinca.k0 * d / pinca.d0, n['zoom-min'], n['zoom-max']);
        var wx = (pinca.mx0 - pinca.vx0) / pinca.k0, wy = (pinca.my0 - pinca.vy0) / pinca.k0;
        vista.k = k2; vista.x = mx - wx * k2; vista.y = my - wy * k2; animVista = null;
        return;
      }
      if (panoramica && panoramica.id === ev.pointerId) {
        var dx = q.x - panoramica.x0, dy = q.y - panoramica.y0;
        if (!panoramica.movido && Math.abs(dx) + Math.abs(dy) > 4) { panoramica.movido = true; raiz.setAttribute('data-arrastando', ''); focar(null); }
        if (panoramica.movido) { vista.x = panoramica.vx + dx; vista.y = panoramica.vy + dy; animVista = null; }
        return;
      }
      if (ev.pointerType !== 'mouse') return;
      var s = sinapseEm(q.x, q.y);
      if (s) { foco = { tipo: 'sinapse', chave: s.chave, x: q.x, y: q.y }; atualizarDica(); }
      else if (foco && foco.tipo === 'sinapse') focar(null);
    });
    function fimPonteiro(ev) {
      var q = coordenadas(ev);
      delete ponteiros[ev.pointerId];
      if (pinca) { if (Object.keys(ponteiros).length < 2) pinca = null; panoramica = null; return; }
      if (!panoramica || panoramica.id !== ev.pointerId) return;
      var clique = !panoramica.movido;
      panoramica = null;
      raiz.removeAttribute('data-arrastando');
      if (!clique || ev.type !== 'pointerup') return;
      var s = sinapseEm(q.x, q.y);
      if (s && ev.pointerType !== 'mouse') { foco = { tipo: 'sinapse', chave: s.chave, x: q.x, y: q.y }; atualizarDica(); return; }
      if (!s) { focar(null); if (selecionado) selecionar(null, true); }
    }
    canvas.addEventListener('pointerup', fimPonteiro);
    canvas.addEventListener('pointercancel', fimPonteiro);
    canvas.addEventListener('pointerleave', function (ev) { if (ev.pointerType === 'mouse' && !panoramica && foco && foco.tipo === 'sinapse') focar(null); });
    canvas.addEventListener('dblclick', function () { centralizar(); });
    raiz.addEventListener('keydown', function (ev) {
      if (ev.target && ev.target.closest && ev.target.closest('.mr-rede-controles')) return;
      if (ev.key === '+' || ev.key === '=') { ev.preventDefault(); zoomEm(W / 2, H / 2, 1.3); }
      else if (ev.key === '-' || ev.key === '_') { ev.preventDefault(); zoomEm(W / 2, H / 2, 1 / 1.3); }
      else if (ev.key === '0') { ev.preventDefault(); centralizar(); }
      else if (ev.key === 'Escape') { focar(null); if (selecionado) { var b = botoes[selecionado]; selecionar(null, true); if (b) b.focus(); } }
    });
    function selecionar(id, doUsuario) {
      if (id && !topo.porId[id]) id = null;
      if (selecionado && botoes[selecionado]) botoes[selecionado].setAttribute('aria-pressed', 'false');
      selecionado = id;
      if (id) botoes[id].setAttribute('aria-pressed', 'true');
      if (props.aoSelecionar) props.aoSelecionar(id ? dadosAgente(id) : null, !!doUsuario);
    }

    /* ---------- estado, avisos e tempo ---------- */
    function estado() {
      var t = tempoVista(), ag = agora(), ativos = 0, fila = 0;
      topo.agentes.forEach(function (a) { var at = motor.ativacao(a.id, t); if (at.disparou && at.v >= 0.2) ativos++; });
      for (var i = motor.eventos.length - 1; i >= 0 && motor.eventos[i].t > ag; i--) fila++;
      return {
        modo: modo, tocando: tocando, t: t, agora: ag, ativos: ativos, fila: fila, emVoo: motor.pulsos(t).length,
        agentes: topo.agentes.length, zoom: vista.k,
        sinapses: topo.sinapses.filter(function (s) { return s.natureza !== 'latente'; }).length
      };
    }
    function notificar() { if (props.aoMudarEstado) props.aoMudarEstado(estado()); }
    function anunciar() {
      if (modo !== 'ao-vivo') return;
      var ag = agora();
      motor.estimulos.forEach(function (e) {
        if (e.t > anunciadoAte && e.t <= ag) {
          var a = topo.porId[e.no];
          aviso.textContent = 'Nova demanda entrou por ' + (a ? a.nome + ' (' + a.id + ')' : e.no) + ': ' + e.texto + '.';
        }
      });
      anunciadoAte = ag;
    }
    function irPara(t) { tVista = clamp(t, 0, agora()); modo = 'reproducao'; tocando = false; notificar(); }
    function passo(dir) {
      var t = tempoVista(), lim = agora(), marcos = [];
      motor.eventos.forEach(function (e) {
        if (e.t > lim || (filtro && !filtro[e.tipo])) return;
        marcos.push(e.chave ? e.inicio + e.dur * 0.55 : e.t + 350);
      });
      marcos.sort(function (a, b) { return a - b; });
      var alvo = null, i;
      if (dir > 0) { for (i = 0; i < marcos.length; i++) if (marcos[i] > t + 30) { alvo = marcos[i]; break; } }
      else { for (i = marcos.length - 1; i >= 0; i--) if (marcos[i] < t - 30) { alvo = marcos[i]; break; } }
      if (alvo != null) irPara(Math.min(alvo, lim));
    }

    /* ---------- ciclo de vida ---------- */
    pararTema = observarTema(function () { tk = lerTokens(raiz); motor.tk = tk; lerMovimento(); ultimoDesenho = 0; });
    if (window.ResizeObserver) { ro = new ResizeObserver(medir); ro.observe(raiz); }
    if (window.IntersectionObserver) {
      io = new IntersectionObserver(function (es) { visivel = es[es.length - 1].isIntersecting; if (visivel) iniciar(); else parar(); });
      io.observe(raiz);
    }
    requestAnimationFrame(function () { if (raiz.isConnected) medir(); });

    var controle = {
      topologia: topo,
      tipos: TIPOS,
      estimular: function (e) { return motor.estimular(e, agora()); },
      registrar: function (ev) { return motor.registrar(ev, agora()); },
      falar: function (id, texto) {
        return motor.estimular({ no: id, afinidade: {}, texto: texto, origem: 'voce', prioridade: 'alta' }, agora());
      },
      selecionar: function (id) { selecionar(id || null, false); },
      selecionado: function () { return selecionado; },
      filtrar: function (tipos) { filtro = conjunto(tipos); },
      pausar: function () { if (modo === 'ao-vivo') { tVista = agora(); modo = 'pausado'; } else { tVista = tempoVista(); } tocando = false; notificar(); },
      tocar: function () { if (modo === 'ao-vivo') return; tocarBase = tempoVista(); tocarDesde = performance.now(); tocando = true; modo = 'reproducao'; notificar(); },
      irPara: irPara,
      aoVivo: function () { modo = 'ao-vivo'; tocando = false; notificar(); },
      passo: passo,
      estado: estado,
      agora: agora,
      eventos: function (ini, fim) {
        var t = tempoVista();
        return motor.eventos.filter(function (e) { return e.t >= ini && e.t <= fim; }).map(function (e) { return trocaPlana(e, t); });
      },
      agente: dadosAgente,
      sinapsesDe: sinapsesDe,
      trocasDe: trocasDe,
      pesos: function () { return motor.pesos(tempoVista()); },
      zoom: function (f) { zoomEm(W / 2, H / 2, f || 1.3); },
      centralizar: centralizar,
      vista: function () { return { k: vista.k, x: vista.x, y: vista.y }; },
      reorganizar: function () { recalcularLayout(false); },
      margens: function (m) {
        var mudou = false;
        for (var k in m) if (margem[k] !== m[k]) { margem[k] = m[k]; mudou = true; }
        if (mudou && fisica) recalcularLayout(false);
      },
      destruir: function () {
        parar();
        if (ro) ro.disconnect();
        if (io) io.disconnect();
        if (pararTema) pararTema();
      }
    };
    raiz.controle = controle;
    return raiz;
  }

  /* =====================================================================
     Ícones de controle: formas geométricas em SVG, traço em currentColor.
     ===================================================================== */
  function icone(d, extra) {
    var s = svg('svg', { width: 16, height: 16, viewBox: '0 0 16 16', 'aria-hidden': 'true', focusable: 'false' });
    (Array.isArray(d) ? d : [d]).forEach(function (p) { s.appendChild(svg('path', p)); });
    return s;
  }
  var ICONES = {
    tocar: function () { return icone({ d: 'M5 3.2 L12.5 8 L5 12.8Z', fill: 'currentColor' }); },
    pausar: function () { return icone([{ d: 'M4.5 3.5h2.5v9h-2.5z', fill: 'currentColor' }, { d: 'M9 3.5h2.5v9h-2.5z', fill: 'currentColor' }]); },
    anterior: function () { return icone([{ d: 'M4 3.5v9', stroke: 'currentColor', 'stroke-width': 1.5, fill: 'none' }, { d: 'M12.5 3.5 L6 8 L12.5 12.5Z', fill: 'currentColor' }]); },
    proximo: function () { return icone([{ d: 'M12 3.5v9', stroke: 'currentColor', 'stroke-width': 1.5, fill: 'none' }, { d: 'M3.5 3.5 L10 8 L3.5 12.5Z', fill: 'currentColor' }]); },
    fechar: function () { return icone({ d: 'M4 4 L12 12 M12 4 L4 12', stroke: 'currentColor', 'stroke-width': 1.5, fill: 'none' }); },
    mais: function () { return icone({ d: 'M8 3.5v9 M3.5 8h9', stroke: 'currentColor', 'stroke-width': 1.5, fill: 'none' }); },
    menos: function () { return icone({ d: 'M3.5 8h9', stroke: 'currentColor', 'stroke-width': 1.5, fill: 'none' }); },
    centralizar: function () {
      return icone([{ d: 'M8 4.5a3.5 3.5 0 1 0 0 7a3.5 3.5 0 1 0 0-7z', stroke: 'currentColor', 'stroke-width': 1.5, fill: 'none' },
        { d: 'M8 1.5v2.5 M8 12v2.5 M1.5 8h2.5 M12 8h2.5', stroke: 'currentColor', 'stroke-width': 1.5, fill: 'none' }]);
    },
    tema: function () {
      return icone([{ d: 'M8 2.25a5.75 5.75 0 1 0 0 11.5a5.75 5.75 0 1 0 0-11.5z', stroke: 'currentColor', 'stroke-width': 1.5, fill: 'none' },
        { d: 'M8 2.25a5.75 5.75 0 0 1 0 11.5z', fill: 'currentColor' }]);
    }
  };
  function botaoIcone(rotulo, iconeNome) {
    return el('button', { type: 'button', 'class': 'mr-botao-icone', 'aria-label': rotulo, title: rotulo }, [ICONES[iconeNome]()]);
  }
  function alternarTema() {
    var h = doc.documentElement;
    h.setAttribute('data-theme', (h.getAttribute('data-theme') || 'escuro') === 'claro' ? 'escuro' : 'claro');
  }
  function idade(ms) {
    if (ms < 1500) return 'agora';
    if (ms < 60000) return 'há ' + Math.round(ms / 1000) + ' s';
    if (ms < 3600000) return 'há ' + Math.round(ms / 60000) + ' min';
    return 'há ' + Math.round(ms / 3600000) + ' h';
  }

  /* =====================================================================
     Selos: tipo (glifo + palavra), prioridade (barras + palavra), medidor
     ===================================================================== */
  function SeloTipo(props) {
    props = props || {};
    var t = TIPO[props.tipo] || TIPO.informe;
    var e = el('span', { 'class': 'mr-selo rotulo', 'data-tipo': t.id });
    e.appendChild(glifoSVG(t.id, props.tamanho || 10));
    if (props.compacto) {
      e.setAttribute('data-compacto', '');
      e.setAttribute('role', 'img');
      e.setAttribute('aria-label', t.rotulo);
      e.setAttribute('title', t.rotulo + ': ' + t.descricao.toLowerCase());
    } else {
      e.appendChild(el('span', { texto: t.rotulo }));
    }
    return e;
  }
  function barrasPrioridade(nivel) {
    var s = svg('svg', { width: 14, height: 10, viewBox: '0 0 14 10', 'aria-hidden': 'true', focusable: 'false' });
    for (var i = 0; i < 4; i++) {
      var h = 3 + i * 2.2;
      s.appendChild(svg('rect', { x: i * 3.5 + 0.5, y: 9.5 - h, width: 2.5, height: h, rx: 0.5, 'class': i < nivel ? 'mr-barra-on' : 'mr-barra-off' }));
    }
    return s;
  }
  function SeloPrioridade(props) {
    props = props || {};
    var p = PRIORIDADE[props.prioridade] || PRIORIDADE.normal;
    var e = el('span', { 'class': 'mr-prioridade rotulo', 'data-prioridade': p.id });
    e.appendChild(barrasPrioridade(p.nivel));
    if (props.compacto) { e.setAttribute('role', 'img'); e.setAttribute('aria-label', 'Prioridade ' + p.rotulo.toLowerCase()); }
    else e.appendChild(el('span', { texto: p.rotulo }));
    return e;
  }
  function MedidorAtivacao(props) {
    props = props || {};
    var e = el('div', { 'class': 'mr-medidor' });
    var rot = el('span', { 'class': 'rotulo mr-suave' });
    var val = el('span', { 'class': 'leitura' });
    var trilho = el('div', { 'class': 'mr-medidor-trilho', role: 'meter', 'aria-valuemin': '0', 'aria-valuemax': '100' });
    var barra = el('div', { 'class': 'mr-medidor-valor' });
    var lim = el('div', { 'class': 'mr-medidor-limiar' });
    var nota = el('span', { 'class': 'leitura mr-suave' });
    trilho.appendChild(barra); trilho.appendChild(lim);
    e.appendChild(el('div', { 'class': 'mr-medidor-linha' }, [rot, val]));
    e.appendChild(trilho);
    e.appendChild(nota);
    function render() {
      var v = clamp(props.valor || 0, 0, 1), l = props.limiar == null ? 0.5 : props.limiar, acima = v >= l;
      rot.textContent = props.rotulo || 'Ativação';
      val.textContent = pct(v);
      barra.style.width = (v * 100).toFixed(1) + '%';
      lim.style.left = (l * 100).toFixed(1) + '%';
      trilho.setAttribute('aria-label', props.rotulo || 'Ativação');
      trilho.setAttribute('aria-valuenow', String(Math.round(v * 100)));
      trilho.setAttribute('aria-valuetext', pct(v) + ', ' + (acima ? 'acima' : 'abaixo') + ' do limiar de ' + pct(l));
      nota.textContent = (acima ? 'acima' : 'abaixo') + ' do limiar · ' + pct(l);
      if (acima) e.setAttribute('data-acima', ''); else e.removeAttribute('data-acima');
    }
    render();
    e.controle = { atualizar: function (p) { for (var k in p) props[k] = p[k]; render(); } };
    return e;
  }

  /* =====================================================================
     Filtro por tipo: apaga o que não interessa, não esconde.
     ===================================================================== */
  function FiltroTipos(props) {
    props = props || {};
    var ativos = conjunto(props.ativos || TIPOS.map(function (t) { return t.id; }));
    var e = el('div', { 'class': 'mr-filtro', role: 'group', 'aria-label': 'Filtrar mensagens por tipo' });
    var chips = {};
    TIPOS.forEach(function (t) {
      var b = el('button', { type: 'button', 'class': 'mr-chip rotulo', 'aria-pressed': 'true', title: t.descricao });
      b.style.setProperty('--tipo-cor', 'var(--msg-' + t.id + ')');
      b.appendChild(glifoSVG(t.id, 10));
      b.appendChild(el('span', { 'class': 'mr-chip-rotulo', texto: t.rotulo }));
      b.addEventListener('click', function () { ativos[t.id] = !ativos[t.id]; sync(); emitir(); });
      chips[t.id] = b;
      e.appendChild(b);
    });
    var todos = el('button', { type: 'button', 'class': 'mr-chip rotulo', 'data-todos': '', texto: 'Ligar todos' });
    todos.addEventListener('click', function () { TIPOS.forEach(function (t) { ativos[t.id] = true; }); sync(); emitir(); chips[TIPOS[0].id].focus(); });
    e.appendChild(todos);
    function lista() { return TIPOS.filter(function (t) { return ativos[t.id]; }).map(function (t) { return t.id; }); }
    function sync() {
      TIPOS.forEach(function (t) { chips[t.id].setAttribute('aria-pressed', ativos[t.id] ? 'true' : 'false'); });
      todos.hidden = lista().length === TIPOS.length;
    }
    function emitir() { if (props.aoMudar) props.aoMudar(lista()); }
    sync();
    e.controle = { ativos: lista, definir: function (l) { ativos = conjunto(l || TIPOS.map(function (t) { return t.id; })); sync(); } };
    return e;
  }

  /* =====================================================================
     Dica: ficha curta de um neurônio ou de uma sinapse, sob o ponteiro ou em foco.
     ===================================================================== */
  var NATUREZA = { reciproca: 'Recíproca', unilateral: 'Unilateral', latente: 'Latente' };
  var SEPARADOR = { reciproca: ' ↔ ', unilateral: ' — ', latente: ' ⋯ ' };
  function linhaDL(dl, rotulo, valor, classeValor) {
    dl.appendChild(el('dt', { 'class': 'rotulo', texto: rotulo }));
    dl.appendChild(el('dd', { 'class': classeValor || 'leitura', texto: valor }));
  }
  function preencherDica(e, d) {
    limpar(e);
    d = d || {};
    if (d.tipo === 'sinapse' && d.a && d.b) {
      e.appendChild(el('div', { 'class': 'mr-dica-cab' }, [
        el('span', { 'class': 'leitura', texto: d.a.id + (SEPARADOR[d.natureza] || ' — ') + d.b.id }),
        el('span', { 'class': 'rotulo mr-suave', texto: d.a.nome + ' e ' + d.b.nome })
      ]));
      var dl = el('dl', { 'class': 'mr-dica-linhas' });
      linhaDL(dl, 'Peso atual', decimal(d.peso || 0));
      linhaDL(dl, 'Ligação', NATUREZA[d.natureza] || '—', 'rotulo');
      e.appendChild(dl);
      var ul = el('ul', { 'class': 'mr-dica-trocas', 'aria-label': 'Últimas trocas' });
      if (d.trocas && d.trocas.length) {
        d.trocas.forEach(function (tr) {
          var t = TIPO[tr.tipo] || TIPO.informe;
          ul.appendChild(el('li', null, [
            glifoSVG(t.id, 10),
            el('div', { 'class': 'mr-min0' }, [
              el('div', { 'class': 'rotulo mr-suave mr-trunca', texto: t.rotulo + ' · de ' + (tr.de || 'entrada') + (tr.idade != null ? ' · ' + idade(tr.idade) : '') }),
              el('div', { 'class': 'corpo mr-duas-linhas', texto: tr.texto || '' })
            ])
          ]));
        });
      } else {
        ul.appendChild(el('li', { 'class': 'rotulo mr-suave', texto: 'Nenhuma troca recente.' }));
      }
      e.appendChild(ul);
      return e;
    }
    var a = d.agente || {};
    e.appendChild(el('div', { 'class': 'mr-dica-cab' }, [
      el('span', { 'class': 'corpo mr-dica-nome', texto: a.nome || '' }),
      el('span', { 'class': 'rotulo mr-suave', texto: [a.cargo, d.regiao || a.regiaoNome].filter(Boolean).join(' · ') })
    ]));
    var dl2 = el('dl', { 'class': 'mr-dica-linhas' });
    linhaDL(dl2, 'Agente', a.id || '—');
    linhaDL(dl2, 'Modelo', d.modelo || a.modelo || '—');
    linhaDL(dl2, 'Grau', String(d.grau || a.grau || '—'));
    if (d.trafego && TIPO[d.trafego] && (d.ativacao || 0) >= 0.05) {
      dl2.appendChild(el('dt', { 'class': 'rotulo', texto: 'Processando' }));
      dl2.appendChild(el('dd', null, [SeloTipo({ tipo: d.trafego })]));
    }
    e.appendChild(dl2);
    e.appendChild(MedidorAtivacao({ valor: d.ativacao || 0, limiar: d.limiar == null ? 0.5 : d.limiar, rotulo: 'Ativação atual' }));
    return e;
  }
  function Dica(props) {
    var e = el('div', { 'class': 'mr-dica', role: 'tooltip', 'data-estatica': '' });
    preencherDica(e, props || {});
    e.controle = { atualizar: function (p) { preencherDica(e, p); } };
    return e;
  }

  /* =====================================================================
     Painel do agente: lateral a partir de 720px, folha inferior abaixo disso.
     ===================================================================== */
  function PainelAgente(props) {
    props = props || {};
    var e = el('aside', { 'class': 'mr-painel', 'data-modo': props.modo || 'lateral' });
    var idNome = uid('nome');
    e.setAttribute('aria-labelledby', idNome);
    var nome = el('h2', { 'class': 'titulo', id: idNome });
    var fechar = botaoIcone('Fechar ficha', 'fechar');
    var cargo = el('p', { 'class': 'corpo mr-suave' });
    var ident = el('p', { 'class': 'leitura mr-suave' });
    var cab = el('header', { 'class': 'mr-painel-cab' }, [nome, fechar,
      el('div', { style: 'grid-column: 1 / -1' }, [cargo, ident])]);
    var num = el('span', { 'class': 'leitura-destaque' });
    var estadoAt = el('span', { 'class': 'rotulo mr-suave' });
    var medidor = MedidorAtivacao({ valor: 0, limiar: 0.5, rotulo: 'Ativação atual' });
    var dl = el('dl', { 'class': 'mr-dica-linhas' });
    var trafego = el('div', { 'class': 'mr-trafego' });
    var blocoAt = el('section', { 'class': 'mr-painel-bloco', 'aria-label': 'Ativação' }, [
      el('div', { 'class': 'mr-leitura-grande' }, [num, estadoAt]), trafego, medidor, dl]);
    var listaS = el('ul', { 'class': 'mr-lista' });
    var listaT = el('ul', { 'class': 'mr-lista' });
    var idS = uid('sinapses'), idT = uid('trocas');
    var blocoS = el('section', { 'class': 'mr-painel-bloco', 'aria-labelledby': idS }, [el('h3', { 'class': 'secao', id: idS, texto: 'Sinapses' }), listaS]);
    var blocoT = el('section', { 'class': 'mr-painel-bloco', 'aria-labelledby': idT }, [el('h3', { 'class': 'secao', id: idT, texto: 'Últimas trocas' }), listaT]);
    var corpo = el('div', { 'class': 'mr-painel-corpo' }, [blocoAt, blocoS, blocoT]);
    var idCampo = uid('campo');
    var rotCampo = el('label', { 'for': idCampo, 'class': 'rotulo' });
    var campo = el('textarea', { id: idCampo, 'class': 'mr-campo corpo', rows: '1', placeholder: 'Mensagem direta' });
    var enviar = el('button', { type: 'submit', 'class': 'mr-botao rotulo', 'data-primario': '', texto: 'Enviar' });
    var erroEnvio = el('p', { 'class': 'rotulo mr-painel-erro', role: 'alert', hidden: true });
    var form = el('form', { 'class': 'mr-painel-composer' }, [rotCampo, el('div', { 'class': 'mr-painel-composer-linha' }, [campo, enviar]), erroEnvio]);
    e.appendChild(el('div', { 'class': 'mr-painel-alca', 'aria-hidden': 'true' }));
    e.appendChild(cab); e.appendChild(corpo); e.appendChild(form);
    /* aoEnviar pode devolver uma Promise: enquanto corre, Enviar fica desabilitado;
       se falhar, o texto volta ao campo e a ficha avisa em `erro`. */
    form.addEventListener('submit', function (ev) {
      ev.preventDefault();
      var txt = campo.value.trim();
      if (!txt || enviar.disabled) { campo.focus(); return; }
      erroEnvio.hidden = true;
      var r = props.aoEnviar ? props.aoEnviar(txt, props.agente) : null;
      campo.value = '';
      if (r && typeof r.then === 'function') {
        enviar.disabled = true;
        r.then(function () { enviar.disabled = false; }, function (err) {
          enviar.disabled = false;
          if (!campo.value) campo.value = txt;
          erroEnvio.textContent = 'Não foi possível enviar. ' + (err && err.message ? err.message : 'Tente de novo.');
          erroEnvio.hidden = false;
          campo.focus();
        });
      }
    });
    campo.addEventListener('keydown', function (ev) {
      if (ev.key === 'Enter' && !ev.shiftKey) { ev.preventDefault(); form.requestSubmit ? form.requestSubmit() : enviar.click(); }
    });
    fechar.addEventListener('click', function () { if (props.aoFechar) props.aoFechar(); });
    e.addEventListener('keydown', function (ev) { if (ev.key === 'Escape' && props.aoFechar) { ev.stopPropagation(); props.aoFechar(); } });
    var assinaturaS = '', assinaturaT = '', idAtual = null, ultimoTipo = undefined;
    function render() {
      var a = props.agente;
      if (!a) return;
      if (a.id !== idAtual) { idAtual = a.id; campo.value = ''; erroEnvio.hidden = true; assinaturaS = assinaturaT = ''; }
      nome.textContent = a.nome;
      cargo.textContent = a.cargo;
      var reg = a.regiaoNome || a.regiao || '';
      var semAcento = function (s) { return String(s).normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z]/g, ''); };
      ident.textContent = a.id + (reg && semAcento(reg) !== semAcento(a.id) ? ' · ' + reg : '');
      rotCampo.textContent = 'Falar com ' + a.nome.split(' ')[0];
      var v = a.ativacao || 0, l = a.limiar == null ? 0.5 : a.limiar;
      num.textContent = pct(v);
      estadoAt.textContent = v >= l ? 'acima do limiar' : 'abaixo do limiar';
      var tipoAtual = a.tipo && TIPO[a.tipo] && v >= 0.05 ? a.tipo : null;
      if (tipoAtual !== ultimoTipo) {
        ultimoTipo = tipoAtual;
        limpar(trafego);
        if (tipoAtual) { trafego.appendChild(el('span', { 'class': 'rotulo mr-suave', texto: 'processando' })); trafego.appendChild(SeloTipo({ tipo: tipoAtual })); }
      }
      medidor.controle.atualizar({ valor: v, limiar: l });
      limpar(dl);
      linhaDL(dl, 'Modelo', a.modelo || '—');
      linhaDL(dl, 'Grau', String(a.grau));
      var sin = a.sinapses || [];
      var sigS = sin.map(function (s) { return s.id + Math.round(s.peso * 100); }).join();
      if (sigS !== assinaturaS) {
        assinaturaS = sigS;
        limpar(listaS);
        sin.forEach(function (s) {
          var trilho = el('div', { 'class': 'mr-peso-trilho', 'aria-hidden': 'true' }, [el('div', { 'class': 'mr-peso-valor', style: 'width:' + (clamp(s.peso, 0, 1) * 100).toFixed(1) + '%' })]);
          listaS.appendChild(el('li', { 'class': 'mr-lista-sinapse' }, [
            el('div', { 'class': 'mr-trunca' }, [
              el('div', { 'class': 'corpo mr-trunca', texto: s.nome }),
              el('div', { 'class': 'leitura mr-suave', texto: (SEPARADOR[s.natureza] || ' — ').trim() + ' ' + s.id + (s.natureza === 'reciproca' ? ' · recíproca' : s.natureza === 'latente' ? ' · latente' : '') })
            ]),
            trilho,
            el('span', { 'class': 'leitura', style: 'text-align:right', 'aria-label': 'peso ' + decimal(s.peso), texto: decimal(s.peso) })
          ]));
        });
        if (!sin.length) listaS.appendChild(el('li', { 'class': 'rotulo mr-suave', texto: 'Nenhuma sinapse.' }));
      }
      var trs = a.trocas || [];
      var sigT = trs.map(function (x) { return x.id; }).join() + '|' + trs.map(function (x) { return idade(x.idade); }).join();
      if (sigT !== assinaturaT) {
        assinaturaT = sigT;
        limpar(listaT);
        trs.forEach(function (tr) {
          var t = TIPO[tr.tipo] || TIPO.informe;
          var sentido = tr.de === a.id ? '→ ' + (tr.para === '*' ? 'toda a rede' : tr.paraNome) : '← ' + tr.deNome;
          listaT.appendChild(el('li', { 'class': 'mr-lista-troca' }, [
            glifoSVG(t.id, 10),
            el('div', { 'class': 'rotulo mr-suave', texto: t.rotulo + ' · ' + sentido + ' · ' + idade(tr.idade) }),
            el('span'),
            el('p', { 'class': 'corpo', texto: tr.texto })
          ]));
        });
        if (!trs.length) listaT.appendChild(el('li', { 'class': 'rotulo mr-suave', texto: 'Nenhuma troca ainda.' }));
      }
    }
    render();
    e.controle = {
      atualizar: function (p) { for (var k in p) props[k] = p[k]; render(); },
      focarCampo: function () { campo.focus(); }
    };
    return e;
  }

  /* =====================================================================
     Cabeçalho: fino, só o estado do sistema.
     ===================================================================== */
  var ESTADOS = { 'ao-vivo': 'Ao vivo', reproducao: 'Reprodução', pausado: 'Pausado', desconectado: 'Desconectado' };
  function Cabecalho(props) {
    props = props || {};
    var e = el('header', { 'class': 'mr-cabecalho' });
    var marca = el('span', { 'class': 'mr-marca rotulo' }, [el('b', { texto: 'Movili' }), el('span', { 'class': 'mr-suave', texto: 'Rede' })]);
    var txtEstado = el('span');
    var estado = el('span', { 'class': 'mr-estado rotulo', role: 'status' }, [el('span', { 'class': 'mr-estado-ponto', 'aria-hidden': 'true' }), txtEstado]);
    var tempo = el('span', { 'class': 'leitura mr-suave mr-cabecalho-tempo' });
    var cont = el('span', { 'class': 'mr-contadores leitura' });
    var tema = botaoIcone('Alternar tema claro e escuro', 'tema');
    tema.addEventListener('click', function () { if (props.aoAlternarTema) props.aoAlternarTema(); else alternarTema(); });
    e.appendChild(marca); e.appendChild(estado); e.appendChild(tempo); e.appendChild(cont); e.appendChild(tema);
    function contador(v, rotulo, sec, prefixo) {
      var s = el('span', { 'class': sec ? 'mr-contador-sec' : null });
      if (prefixo) { s.appendChild(doc.createTextNode(rotulo + ' ')); s.appendChild(el('b', { texto: String(v) })); }
      else { s.appendChild(el('b', { texto: String(v) })); s.appendChild(doc.createTextNode(' ' + rotulo)); }
      return s;
    }
    var ultimoEstado = null;
    function render() {
      var est = ESTADOS[props.estado] ? props.estado : 'ao-vivo';
      estado.setAttribute('data-estado', est);
      if (est !== ultimoEstado) { txtEstado.textContent = ESTADOS[est]; ultimoEstado = est; }
      tempo.textContent = (est === 'reproducao' || est === 'pausado') && props.tempo != null ? relogio(props.tempo) : '';
      limpar(cont);
      cont.appendChild(contador(props.agentes == null ? 20 : props.agentes, 'agentes', true));
      cont.appendChild(contador(props.sinapses == null ? 67 : props.sinapses, 'sinapses', true));
      cont.appendChild(contador(props.ativos || 0, (props.ativos === 1 ? 'ativo' : 'ativos'), false));
      cont.appendChild(contador(props.fila || 0, 'fila', false, true));
    }
    render();
    e.controle = { atualizar: function (p) { for (var k in p) props[k] = p[k]; render(); } };
    return e;
  }

  /* =====================================================================
     Linha do tempo: rebobinar a propagação e ver a onda de novo, passo a passo.
     ===================================================================== */
  function LinhaDoTempo(props) {
    props = props || {};
    var e = el('div', { 'class': 'mr-linha', role: 'group', 'aria-label': 'Linha do tempo da propagação' });
    var bAnt = botaoIcone('Passo anterior', 'anterior');
    var bPlay = botaoIcone('Reproduzir', 'tocar');
    var bProx = botaoIcone('Próximo passo', 'proximo');
    var trilho = el('div', { 'class': 'mr-trilho' });
    var marcas = el('div', { 'aria-hidden': 'true' });
    var passado = el('div', { 'class': 'mr-trilho-passado' });
    var cabeca = el('div', { 'class': 'mr-cabeca', role: 'slider', tabindex: '0', 'aria-label': 'Posição na linha do tempo' });
    trilho.appendChild(el('div', { 'class': 'mr-trilho-base' }));
    trilho.appendChild(passado); trilho.appendChild(marcas); trilho.appendChild(cabeca);
    var tempo = el('span', { 'class': 'mr-linha-tempo leitura' });
    var bVivo = el('button', { type: 'button', 'class': 'mr-botao rotulo', 'aria-pressed': 'true', texto: 'Ao vivo' });
    e.appendChild(bAnt); e.appendChild(bPlay); e.appendChild(bProx); e.appendChild(trilho); e.appendChild(tempo); e.appendChild(bVivo);
    var arrastando = false, assinatura = '';
    function ini() { return props.ini == null ? 0 : props.ini; }
    function fim() { return props.fim == null ? 30000 : props.fim; }
    function tDoX(clientX) {
      var r = trilho.getBoundingClientRect();
      return ini() + clamp((clientX - r.left) / Math.max(1, r.width), 0, 1) * (fim() - ini());
    }
    function frac(t) { return clamp((t - ini()) / Math.max(1, fim() - ini()), 0, 1); }
    function emitir(nome, arg) { if (props[nome]) props[nome](arg); }
    bAnt.addEventListener('click', function () { emitir('aoPasso', -1); });
    bProx.addEventListener('click', function () { emitir('aoPasso', 1); });
    bPlay.addEventListener('click', function () { emitir(props.tocando ? 'aoPausar' : 'aoTocar'); });
    bVivo.addEventListener('click', function () { emitir('aoVoltarAoVivo'); });
    trilho.addEventListener('pointerdown', function (ev) {
      arrastando = true;
      trilho.setPointerCapture(ev.pointerId);
      emitir('aoMudar', tDoX(ev.clientX));
      cabeca.focus({ preventScroll: true });
    });
    trilho.addEventListener('pointermove', function (ev) { if (arrastando) emitir('aoMudar', tDoX(ev.clientX)); });
    trilho.addEventListener('pointerup', function () { arrastando = false; });
    trilho.addEventListener('pointercancel', function () { arrastando = false; });
    cabeca.addEventListener('keydown', function (ev) {
      var pos = props.posicao == null ? fim() : props.posicao;
      if (ev.key === 'ArrowLeft' || ev.key === 'ArrowDown') { ev.preventDefault(); if (ev.shiftKey) emitir('aoMudar', Math.max(ini(), pos - 1000)); else emitir('aoPasso', -1); }
      else if (ev.key === 'ArrowRight' || ev.key === 'ArrowUp') { ev.preventDefault(); if (ev.shiftKey) emitir('aoMudar', Math.min(fim(), pos + 1000)); else emitir('aoPasso', 1); }
      else if (ev.key === 'Home') { ev.preventDefault(); emitir('aoMudar', ini()); }
      else if (ev.key === 'End') { ev.preventDefault(); emitir('aoVoltarAoVivo'); }
      else if (ev.key === ' ' || ev.key === 'Enter') { ev.preventDefault(); emitir(props.tocando ? 'aoPausar' : 'aoTocar'); }
    });
    function render() {
      var evs = props.eventos || [], filtro = props.filtro;
      var sig = evs.map(function (x) { return x.id; }).join() + '|' + ini() + '|' + (filtro ? Object.keys(filtro).join() : '');
      if (sig !== assinatura) {
        assinatura = sig;
        limpar(marcas);
        evs.forEach(function (x) {
          if (x.t < ini() || x.t > fim()) return;
          var m = glifoSVG(x.tipo, 10);
          m.setAttribute('class', 'mr-glifo mr-marca-evento');
          m.style.left = (frac(x.t) * 100).toFixed(2) + '%';
          if (filtro && !filtro[x.tipo]) m.setAttribute('data-apagado', '');
          marcas.appendChild(m);
        });
      }
      var pos = props.aoVivo || props.posicao == null ? fim() : props.posicao;
      var f = frac(pos);
      cabeca.style.left = (f * 100).toFixed(2) + '%';
      passado.style.width = (f * 100).toFixed(2) + '%';
      var rel = pos - fim();
      tempo.textContent = props.aoVivo ? 'agora' : relogio(rel);
      cabeca.setAttribute('aria-valuemin', '0');
      cabeca.setAttribute('aria-valuemax', String(Math.round((fim() - ini()) / 1000)));
      cabeca.setAttribute('aria-valuenow', String(Math.round((pos - ini()) / 1000)));
      var perto = null;
      evs.forEach(function (x) { if (x.t <= pos && (!perto || x.t > perto.t)) perto = x; });
      cabeca.setAttribute('aria-valuetext', (props.aoVivo ? 'Ao vivo' : relogio(rel) + ' em relação a agora') +
        (perto ? '. Último evento: ' + (TIPO[perto.tipo] ? TIPO[perto.tipo].rotulo : perto.tipo) + ', ' + (perto.de || 'entrada') + ' para ' + (perto.para === '*' ? 'todos' : perto.para) + '.' : ''));
      bVivo.setAttribute('aria-pressed', props.aoVivo ? 'true' : 'false');
      var nomePlay = props.tocando ? 'Pausar' : 'Reproduzir';
      if (bPlay.getAttribute('aria-label') !== nomePlay) {
        bPlay.setAttribute('aria-label', nomePlay); bPlay.title = nomePlay;
        limpar(bPlay).appendChild(ICONES[props.tocando ? 'pausar' : 'tocar']());
      }
    }
    render();
    e.controle = { atualizar: function (p) { for (var k in p) props[k] = p[k]; render(); } };
    return e;
  }

  /* =====================================================================
     Canvas avulsos: um neurônio, uma sinapse, um pulso. Mesmo desenho da Rede.
     ===================================================================== */
  var tokensCache = null, pararTemaGlobal = null;
  function tokensCompartilhados() {
    if (!tokensCache) {
      tokensCache = lerTokens(null);
      if (!pararTemaGlobal) pararTemaGlobal = observarTema(function () { tokensCache = null; });
    }
    return tokensCache;
  }
  function canvasAvulso(largura, altura, rotulo, desenho) {
    var cv = el('canvas', { role: 'img', 'aria-label': rotulo });
    cv.style.width = largura + 'px';
    cv.style.height = altura + 'px';
    var ctx = cv.getContext('2d'), dpr = 0, t0 = performance.now(), jaConectado = false, ultimo = 0;
    function passo(ts) {
      if (!cv.isConnected) { if (jaConectado) Relogio.cancelar(passo); return; }
      jaConectado = true;
      var reduzir = movimentoReduzido();
      if (reduzir && ts - ultimo < 400) return;
      ultimo = ts;
      var d = Math.min(2, window.devicePixelRatio || 1);
      if (d !== dpr) { dpr = d; cv.width = Math.round(largura * dpr); cv.height = Math.round(altura * dpr); }
      var tk = tokensCompartilhados();
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
      ctx.fillStyle = css(tk.cor.fundo);
      ctx.fillRect(0, 0, largura, altura);
      desenho(ctx, tk, reduzir ? 0 : ts - t0, reduzir);
    }
    Relogio.inscrever(passo);
    return cv;
  }
  var ROTULO_ESTADO_NO = {
    repouso: 'em repouso', inerte: 'abaixo do limiar', ativo: 'ativo', entregando: 'entregando',
    selecionado: 'selecionado', realcado: 'vizinho do foco', recuado: 'recuado'
  };
  function Neuronio(props) {
    props = props || {};
    var estado = props.estado || 'repouso', grau = props.grau || 9, tipo = TIPO[props.tipo] ? props.tipo : 'briefing';
    var at = props.ativacao == null ? (estado === 'ativo' ? 0.7 : estado === 'entregando' || estado === 'selecionado' ? 0.55 : 0) : props.ativacao;
    var tam = props.tamanho || 96;
    var rotulo = props.rotulo || 'Neurônio de grau ' + grau + ', ' + (ROTULO_ESTADO_NO[estado] || estado) + (at ? ', ativação ' + pct(at) : '');
    return canvasAvulso(tam, tam, rotulo, function (ctx, tk, t, reduzir) {
      var n = tk.num, r = raioDoGrau(tk, grau) * (props.escala || 1), resp = 0;
      if (!reduzir) { resp = Math.sin(TAU * t / n['respiracao']); r *= 1 + n['respiro-escala'] * resp; }
      var tremor = 0, entrega = -1;
      if (estado === 'inerte' && !reduzir) tremor = excitacao(t % 3200 - 400, 0.35, 0, 700);
      if (estado === 'inerte' && reduzir) tremor = 0.2;
      if (estado === 'entregando') entrega = reduzir ? 0.35 : ((t % 2400) / n['pulso-entrega']);
      desenharNeuronio(ctx, tk, tam / 2, tam / 2, r, {
        ativacao: at, disparou: at > 0, tipo: estado === 'entregando' ? 'entrega' : tipo, tremor: tremor, respiro: (resp + 1) / 2,
        entrega: entrega < 1 ? entrega : -1, selecionado: estado === 'selecionado', realce: estado === 'realcado' ? 1 : 0,
        alfa: estado === 'recuado' ? n['opacidade-recuo'] : 1
      });
    });
  }
  function Sinapse(props) {
    props = props || {};
    var larg = props.largura || 200, alt = props.altura || 48;
    var natureza = props.natureza || 'unilateral', estado = props.estado || 'repouso';
    var rotulo = props.rotulo || 'Sinapse ' + (NATUREZA[natureza] || natureza).toLowerCase() + ', ' + estado;
    return canvasAvulso(larg, alt, rotulo, function (ctx, tk, t, reduzir) {
      var n = tk.num;
      var peso = props.peso == null ? (natureza === 'reciproca' ? n['peso-reciproca'] : natureza === 'latente' ? n['peso-latente'] : n['peso-unilateral']) : props.peso;
      var flash = 0, alfa = 1, realce = 0, ativa = false;
      if (estado === 'reforcando') {
        var ciclo = reduzir ? 1200 : t % 2600, novo = peso + n['taxa-reforco'] * (1 - peso);
        flash = reduzir ? 0 : Math.max(0, 1 - ciclo / n['reforco']);
        peso = ciclo < 200 ? peso : lerp(peso, novo, clamp((ciclo - 200) / n['reforco'], 0, 1));
      } else if (estado === 'atrofiando') {
        var c2 = reduzir ? 0.7 : (t % 5200) / 4200;
        peso = lerp(peso, n['peso-piso'], clamp(c2, 0, 1));
      } else if (estado === 'recuada') alfa = n['opacidade-recuo'];
      else if (estado === 'realcada') realce = 1;
      else if (estado === 'ativa') ativa = true;
      var r = raioDoGrau(tk, 4) * 0.8, y = alt / 2, x1 = r + 3, x2 = larg - r - 3;
      var latente = natureza === 'latente' && peso <= n['peso-latente'] + 0.01;
      desenharSinapse(ctx, tk, x1, y, x2, y, { peso: peso, natureza: natureza, flash: flash, alfa: alfa, realce: realce, ativa: ativa ? corTipo(tk, 'tarefa') : null, tracejada: latente && realce > 0 });
      if (!reduzir && !latente && !ativa) desenharFluxo(ctx, tk, x1 + r, y, x2 - r, y, peso, t, hashTexto(rotulo), alfa);
      if (ativa) {
        var dur = lerp(n['travessia-fraca'], n['travessia-forte'], clamp((peso - n['peso-piso']) / (1 - n['peso-piso']), 0, 1));
        var p = reduzir ? 0.5 : (t % (dur + 500)) / dur;
        if (p < 1) {
          if (reduzir) desenharPulsoEstatico(ctx, tk, x1 + r, y, x2 - r, y, 'tarefa', 'normal', 1);
          else desenharPulso(ctx, tk, x1 + r, y, x2 - r, y, p, 'tarefa', 'normal', 1, 3);
        }
      }
      [x1, x2].forEach(function (x) { desenharNeuronio(ctx, tk, x, y, r, { ativacao: 0, disparou: false, alfa: alfa }); });
    });
  }
  function Pulso(props) {
    props = props || {};
    var tipo = TIPO[props.tipo] ? props.tipo : 'tarefa', prioridade = PRIORIDADE[props.prioridade] ? props.prioridade : 'normal';
    var larg = props.largura || 220, alt = props.altura || 44;
    var rotulo = props.rotulo || 'Pulso de ' + TIPO[tipo].rotulo.toLowerCase() + ', prioridade ' + PRIORIDADE[prioridade].rotulo.toLowerCase();
    return canvasAvulso(larg, alt, rotulo, function (ctx, tk, t, reduzir) {
      var n = tk.num, peso = props.peso == null ? n['peso-reciproca'] : props.peso;
      var r = raioDoGrau(tk, 4) * 0.75, y = alt / 2, x1 = r + 3, x2 = larg - r - 3;
      desenharSinapse(ctx, tk, x1, y, x2, y, { peso: peso, natureza: 'unilateral', ativa: corTipo(tk, tipo) });
      var base = lerp(n['travessia-fraca'], n['travessia-forte'], clamp((peso - n['peso-piso']) / (1 - n['peso-piso']), 0, 1));
      var dur = base / (n['fator-' + prioridade] || 1);
      var atraso = tipo === 'entrega' ? n['pulso-entrega'] * 0.5 : 0;
      var ciclo = dur + atraso + 700, tc = (t + hashTexto(tipo + prioridade) * ciclo) % ciclo, p = (tc - atraso) / dur;
      if (reduzir) desenharPulsoEstatico(ctx, tk, x1 + r, y, x2 - r, y, tipo, prioridade, 1);
      else if (p >= 0 && p < 1) desenharPulso(ctx, tk, x1 + r, y, x2 - r, y, p, tipo, prioridade, 1, hashTexto(tipo) * 10);
      var chegada = reduzir ? -1 : tc - atraso - dur;
      desenharNeuronio(ctx, tk, x1, y, r, { ativacao: 0.5, disparou: true, tipo: tipo, entrega: tipo === 'entrega' && !reduzir ? tc / n['pulso-entrega'] : -1 });
      desenharNeuronio(ctx, tk, x2, y, r, { ativacao: chegada >= 0 ? excitacao(chegada, 0.6, 0, 300) : 0, disparou: chegada >= 0, tipo: tipo });
    });
  }

  /* =====================================================================
     Tela: a rede em tela cheia; cabeçalho, filtro, linha do tempo e ficha são vidro por cima.
     ===================================================================== */
  function Tela(props) {
    props = props || {};
    var janela = 30000, fimJanela = 0, conectado = props.conectado !== false;
    var e = el('div', { 'class': 'mr-tela' });
    var cab = Cabecalho({ estado: 'ao-vivo', aoAlternarTema: props.aoAlternarTema });
    var area = el('div', { 'class': 'mr-area' });
    var rede;
    var painel = PainelAgente({
      modo: 'auto',
      aoFechar: function () { var id = rede.controle.selecionado(); rede.controle.selecionar(null); var b = id && rede.querySelector('[data-id="' + id + '"]'); if (b) b.focus(); },
      aoEnviar: function (txt, ag) { if (ag) rede.controle.falar(ag.id, txt); return props.aoEnviar ? props.aoEnviar(txt, ag) : null; }
    });
    painel.hidden = true;
    var filtro = FiltroTipos({
      aoMudar: function (tipos) {
        var todos = tipos.length === TIPOS.length;
        rede.controle.filtrar(todos ? null : tipos);
        linha.controle.atualizar({ filtro: todos ? null : conjunto(tipos) });
      }
    });
    var linha = LinhaDoTempo({
      aoMudar: function (t) { rede.controle.irPara(t); },
      aoTocar: function () { rede.controle.tocar(); },
      aoPausar: function () { rede.controle.pausar(); },
      aoVoltarAoVivo: function () { rede.controle.aoVivo(); },
      aoPasso: function (d) { rede.controle.passo(d); }
    });
    function medidas() {
      var cs = getComputedStyle(e);
      var num = function (n, p) { var v = parseFloat(cs.getPropertyValue('--' + n)); return isFinite(v) ? v : p; };
      return { cab: num('altura-cabecalho', 44), linha: num('altura-linha-tempo', 48), margem: num('margem-flutuante', 12) };
    }
    var m0 = medidas();
    rede = Rede({
      demo: props.demo !== false, dados: props.dados, pesos: props.pesos, cenarios: props.cenarios, diaMs: props.diaMs,
      reduzirMovimento: props.reduzirMovimento, roda: props.roda,
      margens: { topo: m0.cab + 16, direita: 16, base: m0.linha + 64, esquerda: 16 },
      topoControles: m0.cab + m0.margem,
      aoSelecionar: function (ag) {
        if (ag) { painel.controle.atualizar({ agente: ag }); painel.hidden = false; e.setAttribute('data-painel', ''); }
        else { painel.hidden = true; e.removeAttribute('data-painel'); }
        requestAnimationFrame(ajustarMargens);
        if (props.aoSelecionar) props.aoSelecionar(ag);
      },
      aoMudarEstado: function (st) {
        var vivo = st.modo === 'ao-vivo';
        if (vivo) fimJanela = st.agora;
        cab.controle.atualizar({
          estado: !conectado ? 'desconectado' : vivo ? 'ao-vivo' : st.tocando ? 'reproducao' : st.modo === 'pausado' ? 'pausado' : 'reproducao',
          tempo: st.t - st.agora, ativos: st.ativos, fila: st.fila, agentes: st.agentes, sinapses: st.sinapses
        });
        var ini = fimJanela - janela;
        linha.controle.atualizar({
          eventos: rede.controle.eventos(Math.max(0, ini), Math.min(fimJanela, st.agora)),
          ini: ini, fim: fimJanela, posicao: st.t, aoVivo: vivo, tocando: vivo || st.tocando
        });
        var sel = rede.controle.selecionado();
        if (sel && !painel.hidden) painel.controle.atualizar({ agente: rede.controle.agente(sel) });
        if (props.aoMudarEstado) props.aoMudarEstado(st);
      }
    });
    /* A rede se reencaixa no espaço que o vidro deixa livre: ao lado da ficha, ou acima da folha no celular. */
    function ajustarMargens() {
      var m = medidas(), aberto = !painel.hidden;
      var folha = aberto && e.getBoundingClientRect().width < 720;
      var base = m.linha + 64, direita = 16;
      if (aberto && folha) base = m.linha + painel.offsetHeight + 24;
      else if (aberto) direita = painel.offsetWidth + m.margem * 2 + 8;
      rede.controle.margens({ base: base, direita: direita });
    }
    if (window.ResizeObserver) new ResizeObserver(function () { requestAnimationFrame(ajustarMargens); }).observe(e);
    area.appendChild(rede);
    e.appendChild(cab); e.appendChild(area); e.appendChild(filtro); e.appendChild(painel); e.appendChild(linha);
    e.controle = {
      rede: rede.controle, cabecalho: cab.controle, painel: painel.controle, linha: linha.controle, filtro: filtro.controle,
      /* false enquanto o fluxo de eventos do servidor estiver fora: o cabeçalho mostra Desconectado */
      conexao: function (ok) {
        conectado = ok !== false;
        if (!conectado) cab.controle.atualizar({ estado: 'desconectado' });
      }
    };
    return e;
  }

  /* =====================================================================
     API pública: window.MoviliRede
     ===================================================================== */
  var api = {
    Rede: Rede, Neuronio: Neuronio, Sinapse: Sinapse, Pulso: Pulso, Tela: Tela, Cabecalho: Cabecalho,
    PainelAgente: PainelAgente, Dica: Dica, LinhaDoTempo: LinhaDoTempo, FiltroTipos: FiltroTipos,
    SeloTipo: SeloTipo, SeloPrioridade: SeloPrioridade, MedidorAtivacao: MedidorAtivacao,
    tipos: TIPOS, prioridades: PRIORIDADES, cenarios: CENARIOS,
    topologia: montarTopologia, glifo: glifoSVG, lerTokens: lerTokens, calcularLayout: calcularLayout,
    desenho: { neuronio: desenharNeuronio, sinapse: desenharSinapse, pulso: desenharPulso, onda: desenharOnda, glifo: desenharGlifo },
    alternarTema: alternarTema
  };
  var alvoGlobal = window.MoviliRede || (window.MoviliRede = {});
  for (var nome in api) alvoGlobal[nome] = api[nome];
})();
