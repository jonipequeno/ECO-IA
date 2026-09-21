/**
 * Rede Movili: obsidiana bioluminescente. Componentes em JavaScript puro, sem build e sem dependências.
 * Cada componente é uma função que recebe props e devolve um HTMLElement pronto para inserir.
 * Os interativos expõem métodos em `elemento.controle`.
 * Requer tokens.css e components/bundle.css na página; o bundle publica window.MoviliRede.
 */

export type TipoMensagem =
  | 'briefing' | 'tarefa' | 'entrega' | 'pergunta' | 'resposta'
  | 'revisao' | 'decisao' | 'alerta' | 'informe';
export type Prioridade = 'baixa' | 'normal' | 'alta' | 'critica';
export type Natureza = 'reciproca' | 'unilateral' | 'latente';
export type Glifo = 'anel' | 'seta' | 'circulo' | 'losango-vazado' | 'losango' | 'quadrado' | 'barra' | 'triangulo' | 'asterisco';

export interface Agente { id: string; regiao: string; nome: string; cargo: string; grau?: number; modelo?: string; limiar?: number }
export interface Regiao { id: string; nome: string }
export interface DadosTopologia {
  regioes?: Regiao[];
  agentes?: Agente[];
  /** Pares [a, b]. Padrão: as 67 sinapses de movili/agentes/. */
  sinapses?: [string, string][];
  /** Pares recíprocos (os dois lados se declararam). Padrão: os 4 que o prompt nomeia. */
  reciprocas?: [string, string][];
  /** Agentes que declaram interlocutores = '*'. Padrão: ['diretor']. */
  declaraTodos?: string[];
}
export interface Evento { tipo: TipoMensagem; de: string | null; para: string | null; prioridade?: Prioridade; texto?: string; t?: number }
export interface Estimulo { no: string; afinidade?: Record<string, number>; texto?: string; prioridade?: Prioridade; t?: number }
export interface Troca { id: number; t: number; idade: number; tipo: TipoMensagem; prioridade: Prioridade; texto: string; de: string | null; para: string | null; deNome: string; paraNome: string }
export interface SinapseDoAgente { id: string; nome: string; peso: number; natureza: Natureza }
export interface FichaAgente {
  id: string; nome: string; cargo: string; regiao: string; regiaoNome: string; grau: number; modelo: string | null;
  ativacao: number; disparou: boolean; limiar: number;
  /** Tráfego que o acende agora (cor da coroa); null quando apagado. */
  tipo: TipoMensagem | null;
  sinapses: SinapseDoAgente[]; trocas: Troca[];
}
export interface EstadoRede {
  modo: 'ao-vivo' | 'pausado' | 'reproducao'; tocando: boolean; t: number; agora: number;
  ativos: number; fila: number; emVoo: number; agentes: number; sinapses: number; zoom: number;
}

/* ---------- Rede ---------- */
export interface RedeProps {
  /** true (padrão): roda as duas propagações de demonstração em alternância. */
  demo?: boolean;
  dados?: DadosTopologia;
  /** Pesos aprendidos em sessões anteriores, por chave 'a|b' (ordem alfabética). */
  pesos?: Record<string, number>;
  /** Tipos visíveis; os demais pulsos apagam para opacidade-apagado. */
  filtro?: TipoMensagem[];
  margens?: { topo?: number; direita?: number; base?: number; esquerda?: number };
  /** Padrão: segue prefers-reduced-motion. */
  reduzirMovimento?: boolean;
  /** Duração de um "dia" para a atrofia. Padrão: 86 400 000 ms; 60 000 ms na demonstração. */
  diaMs?: number;
  rotulo?: string;
  /** 'direta' (padrão, painel em tela cheia): a roda aproxima. 'ctrl': só Ctrl + roda e pinça, para a página rolar. */
  roda?: 'direta' | 'ctrl';
  /** Grupo de zoom em vidro no canto superior direito. Padrão: true. */
  controles?: boolean;
  /** Distância do grupo de zoom ao topo, em px (abaixo de um cabeçalho). */
  topoControles?: number;
  aoSelecionar?: (agente: FichaAgente | null, doUsuario: boolean) => void;
  /** Chamado a cada 250 ms com o resumo para o cabeçalho e a linha do tempo. */
  aoMudarEstado?: (estado: EstadoRede) => void;
}
export interface ControleRede {
  estimular(e: Estimulo): unknown;
  registrar(e: Evento): unknown;
  falar(id: string, texto: string): unknown;
  selecionar(id: string | null): void;
  selecionado(): string | null;
  filtrar(tipos: TipoMensagem[] | null): void;
  pausar(): void; tocar(): void; aoVivo(): void;
  irPara(t: number): void;
  passo(direcao: 1 | -1): void;
  estado(): EstadoRede;
  agora(): number;
  eventos(ini: number, fim: number): Troca[];
  agente(id: string): FichaAgente;
  sinapsesDe(id: string): SinapseDoAgente[];
  trocasDe(id: string, max?: number): Troca[];
  /** Pesos atuais, para persistir e passar em RedeProps.pesos na próxima sessão. */
  pesos(): Record<string, number>;
  margens(m: { topo?: number; direita?: number; base?: number; esquerda?: number }): void;
  /** Aproxima (fator > 1) ou afasta (< 1) em torno do centro, entre zoom-min e zoom-max. */
  zoom(fator?: number): void;
  /** Volta ao zoom 1 e ao enquadramento inicial, com transição. */
  centralizar(): void;
  /** tela = mundo × k + (x, y). */
  vista(): { k: number; x: number; y: number };
  reorganizar(): void;
  destruir(): void;
}
export declare function Rede(props?: RedeProps): HTMLDivElement & { controle: ControleRede };

/* ---------- Avulsos em canvas ---------- */
export interface NeuronioProps {
  grau?: number;
  estado?: 'repouso' | 'inerte' | 'ativo' | 'entregando' | 'realcado' | 'selecionado' | 'recuado';
  ativacao?: number;
  /** Tráfego que o acende: dá a cor da coroa. Padrão: 'briefing'. */
  tipo?: TipoMensagem;
  tamanho?: number;
  escala?: number;
  rotulo?: string;
}
export declare function Neuronio(props?: NeuronioProps): HTMLCanvasElement;
export interface SinapseProps {
  peso?: number;
  natureza?: Natureza;
  estado?: 'repouso' | 'reforcando' | 'atrofiando' | 'realcada' | 'recuada' | 'ativa';
  largura?: number;
  altura?: number;
  rotulo?: string;
}
export declare function Sinapse(props?: SinapseProps): HTMLCanvasElement;
export interface PulsoProps { tipo?: TipoMensagem; prioridade?: Prioridade; peso?: number; largura?: number; altura?: number; rotulo?: string }
export declare function Pulso(props?: PulsoProps): HTMLCanvasElement;

/* ---------- Tela e partes ---------- */
export interface TelaProps extends Pick<RedeProps, 'demo' | 'dados' | 'pesos' | 'reduzirMovimento' | 'diaMs' | 'roda'> {
  aoSelecionar?: (agente: FichaAgente | null) => void;
  /** Devolva a Promise do envio: enquanto corre, Enviar fica desabilitado; se rejeitar, o texto volta ao campo com um aviso. */
  aoEnviar?: (texto: string, agente: FichaAgente) => void | Promise<unknown>;
  /** false começa com o cabeçalho em Desconectado. Padrão: true. */
  conectado?: boolean;
  aoMudarEstado?: (estado: EstadoRede) => void;
  aoAlternarTema?: () => void;
}
export declare function Tela(props?: TelaProps): HTMLDivElement & { controle: {
  rede: ControleRede; cabecalho: Atualizavel<CabecalhoProps>; painel: Atualizavel<PainelAgenteProps>; linha: Atualizavel<LinhaDoTempoProps>;
  filtro: { ativos(): TipoMensagem[]; definir(t: TipoMensagem[] | null): void };
  /** false quando o fluxo de eventos do servidor cai (cabeçalho em Desconectado); true quando volta. */
  conexao(conectado: boolean): void;
} };

export interface Atualizavel<P> { atualizar(p: Partial<P>): void }

export interface CabecalhoProps {
  estado?: 'ao-vivo' | 'reproducao' | 'pausado' | 'desconectado';
  /** Em reprodução ou pausa: deslocamento em ms em relação a agora (negativo). */
  tempo?: number;
  agentes?: number; sinapses?: number; ativos?: number; fila?: number;
  aoAlternarTema?: () => void;
}
export declare function Cabecalho(props?: CabecalhoProps): HTMLElement & { controle: Atualizavel<CabecalhoProps> };

export interface PainelAgenteProps {
  agente?: FichaAgente;
  /** 'lateral' (padrão), 'folha' (celular) ou 'auto' (decide pela largura da Tela). */
  modo?: 'lateral' | 'folha' | 'auto';
  /** Pode devolver uma Promise: se rejeitar, o texto volta ao campo e a ficha mostra o aviso em `erro`. */
  aoEnviar?: (texto: string, agente: FichaAgente) => void | Promise<unknown>;
  aoFechar?: () => void;
}
export declare function PainelAgente(props?: PainelAgenteProps): HTMLElement & { controle: Atualizavel<PainelAgenteProps> & { focarCampo(): void } };

export type DicaProps =
  | { tipo: 'neuronio'; agente: Agente & { regiaoNome?: string }; ativacao: number; limiar?: number; modelo?: string; grau?: number; regiao?: string; trafego?: TipoMensagem | null }
  | { tipo: 'sinapse'; a: Agente; b: Agente; peso: number; natureza: Natureza; trocas?: Partial<Troca>[] };
export declare function Dica(props: DicaProps): HTMLDivElement & { controle: { atualizar(p: DicaProps): void } };

export interface LinhaDoTempoProps {
  eventos?: Troca[];
  ini?: number; fim?: number; posicao?: number;
  aoVivo?: boolean; tocando?: boolean;
  filtro?: Record<string, boolean> | null;
  aoMudar?: (t: number) => void;
  aoTocar?: () => void; aoPausar?: () => void; aoVoltarAoVivo?: () => void;
  aoPasso?: (direcao: 1 | -1) => void;
}
export declare function LinhaDoTempo(props?: LinhaDoTempoProps): HTMLDivElement & { controle: Atualizavel<LinhaDoTempoProps> };

export interface FiltroTiposProps { ativos?: TipoMensagem[]; aoMudar?: (ativos: TipoMensagem[]) => void }
export declare function FiltroTipos(props?: FiltroTiposProps): HTMLDivElement & { controle: { ativos(): TipoMensagem[]; definir(t: TipoMensagem[] | null): void } };

/* ---------- Selos ---------- */
export interface SeloTipoProps { tipo: TipoMensagem; compacto?: boolean; tamanho?: number }
export declare function SeloTipo(props: SeloTipoProps): HTMLSpanElement;
export interface SeloPrioridadeProps { prioridade: Prioridade; compacto?: boolean }
export declare function SeloPrioridade(props: SeloPrioridadeProps): HTMLSpanElement;
export interface MedidorAtivacaoProps { valor: number; limiar?: number; rotulo?: string }
export declare function MedidorAtivacao(props: MedidorAtivacaoProps): HTMLDivElement & { controle: Atualizavel<MedidorAtivacaoProps> };

declare global {
  interface Window {
    MoviliRede: {
      Rede: typeof Rede; Neuronio: typeof Neuronio; Sinapse: typeof Sinapse; Pulso: typeof Pulso;
      Tela: typeof Tela; Cabecalho: typeof Cabecalho; PainelAgente: typeof PainelAgente; Dica: typeof Dica;
      LinhaDoTempo: typeof LinhaDoTempo; FiltroTipos: typeof FiltroTipos;
      SeloTipo: typeof SeloTipo; SeloPrioridade: typeof SeloPrioridade; MedidorAtivacao: typeof MedidorAtivacao;
      tipos: { id: TipoMensagem; rotulo: string; descricao: string; glifo: Glifo }[];
      prioridades: { id: Prioridade; rotulo: string; nivel: number }[];
      topologia(dados?: DadosTopologia): unknown;
      glifo(tipo: TipoMensagem | Glifo, tamanho?: number, corCss?: string): SVGSVGElement;
      alternarTema(): void;
    };
  }
}
