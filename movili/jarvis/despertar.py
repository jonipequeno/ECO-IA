"""Palavra de despertar do OpenJarvis.

Sem isto o Jarvis so escuta quando voce manda. Com isto ele fica em espera e
acorda ao ouvir o proprio nome - e volta a dormir depois de um silencio.

Tres detectores, na ordem de preferencia, todos detectados em tempo de
execucao como o resto da camada de voz:

  1. openwakeword  - modelo dedicado, barato em CPU, roda continuo
  2. transcricao   - reaproveita o STT ja configurado em janelas curtas
  3. tecla         - sem microfone: Enter acorda

O casamento da palavra e tolerante de proposito: transcricao de audio curto
erra com frequencia ("jarves", "darvis", "jarvis," com pontuacao), e exigir
igualdade exata faria o usuario repetir o nome varias vezes.
"""

from __future__ import annotations

import difflib
import re
import time
import unicodedata

from .voz import MotorEscuta, Teclado

PALAVRA_PADRAO = "jarvis"

# Limiar escolhido por medicao, nao por palpite. Com as confusoes plausiveis do
# Whisper para "jarvis" em pt-BR (jarves, darvis, javis, jarviz, jarbis) contra
# palavras comuns do idioma, a folga fica entre 0.769 ("jardins", o melhor falso
# positivo) e 0.833 (o pior verdadeiro que vale manter). 0.80 fica no meio.
#
# A 0.75, "jardins" acordava o Jarvis. Acordar sozinho incomoda mais do que
# perder uma chamada, entao o corte pende para o conservador: "jarvez" (0.667)
# fica de fora de proposito.
SEMELHANCA_MINIMA = 0.80


def normalizar(texto: str) -> str:
    """Minusculas, sem acento e sem pontuacao - para comparar palavra a palavra."""
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFD", texto.lower())
        if unicodedata.category(c) != "Mn"
    )
    return re.sub(r"[^\w\s]", " ", sem_acento).strip()


def contem_palavra(texto: str, palavra: str, minimo: float = SEMELHANCA_MINIMA) -> bool:
    """A transcricao contem a palavra de despertar, tolerando erro de STT?

    Compara termo a termo em vez do texto inteiro: numa frase longa, a
    semelhanca global se dilui e a palavra passaria despercebida.
    """
    alvo = normalizar(palavra)
    if not alvo:
        return False

    termos = normalizar(texto).split()
    if not termos:
        return False
    if alvo in termos:
        return True

    # Palavra de despertar com mais de um termo ("ola movili"): compara janelas
    # do mesmo tamanho, senao nunca casaria termo a termo.
    tamanho = len(alvo.split())
    for i in range(len(termos) - tamanho + 1):
        janela = " ".join(termos[i : i + tamanho])
        if difflib.SequenceMatcher(None, janela, alvo).ratio() >= minimo:
            return True
    return False


def remover_palavra(texto: str, palavra: str) -> str:
    """Tira o nome do inicio do comando: 'Jarvis, chama a Patricia' -> 'chama a Patricia'."""
    alvo = normalizar(palavra)
    tamanho = len(alvo.split())
    bruto = texto.strip()

    termos_originais = bruto.split()
    termos_norm = normalizar(bruto).split()
    if len(termos_norm) < tamanho:
        return bruto

    inicio = " ".join(termos_norm[:tamanho])
    if inicio == alvo or difflib.SequenceMatcher(None, inicio, alvo).ratio() >= SEMELHANCA_MINIMA:
        restante = " ".join(termos_originais[tamanho:]).strip()
        return restante.lstrip(",.;:!? ").strip()
    return bruto


# =====================================================================
class Detector:
    """Interface comum dos detectores de despertar."""

    nome = "nenhum"
    disponivel = False

    def esperar(self, timeout: float | None = None) -> str | None:
        """Bloqueia ate ouvir a palavra.

        Devolve o que veio DEPOIS dela na mesma fala (para o usuario poder
        dizer "Jarvis, chama a Patricia" de uma vez), string vazia se so
        ouviu o nome, ou None se o timeout estourou.
        """
        raise NotImplementedError

    def __repr__(self) -> str:  # pragma: no cover - conveniencia de debug
        return f"<Despertar {self.nome}>"


class DespertarPorTecla(Detector):
    """Sem microfone: Enter acorda. Sempre disponivel."""

    nome = "tecla"
    disponivel = True

    def __init__(self, palavra: str = PALAVRA_PADRAO) -> None:
        self.palavra = palavra

    def esperar(self, timeout: float | None = None) -> str | None:
        try:
            entrada = input("[dormindo - Enter para falar] ").strip()
        except (EOFError, KeyboardInterrupt):
            return None
        # Quem digitou o nome quis so acordar, nao mandar "jarvis" ao CEO.
        return remover_palavra(entrada, self.palavra) if entrada else ""


class DespertarPorTranscricao(Detector):
    """Reaproveita o STT configurado, ouvindo em janelas curtas.

    Nao exige dependencia nova: se o Jarvis ja transcreve, ja sabe despertar.
    Em compensacao gasta CPU transcrevendo silencio, entao a janela e curta.
    """

    nome = "transcricao"

    def __init__(
        self,
        escuta: MotorEscuta,
        palavra: str = PALAVRA_PADRAO,
        janela: int = 3,
    ) -> None:
        self.escuta = escuta
        self.palavra = palavra
        self.janela = max(1, janela)
        # Com o teclado nao faz sentido: quem digita nao precisa de palavra.
        self.disponivel = escuta.disponivel and not isinstance(escuta, Teclado)

    def esperar(self, timeout: float | None = None) -> str | None:
        limite = None if timeout is None else time.monotonic() + timeout
        while limite is None or time.monotonic() < limite:
            texto = self.escuta.ouvir(self.janela)
            if texto and contem_palavra(texto, self.palavra):
                return remover_palavra(texto, self.palavra)
        return None


class DespertarOpenWakeWord(Detector):
    """openWakeWord: modelo dedicado, ordens de grandeza mais barato que transcrever.

    Instalacao: pip install openwakeword sounddevice numpy
    A palavra precisa ter modelo treinado ('alexa', 'hey jarvis', 'hey mycroft'...).
    """

    nome = "openwakeword"

    def __init__(self, modelo: str = "hey_jarvis", limiar: float = 0.5) -> None:
        self.modelo_nome = modelo
        self.limiar = limiar
        self._modelo = None
        self._sd = None
        try:
            import sounddevice  # type: ignore
            from openwakeword.model import Model  # type: ignore
        except ImportError:
            self.disponivel = False
            return
        self._sd = sounddevice
        self._classe = Model
        self.disponivel = True

    def _carregar(self):
        if self._modelo is None:
            self._modelo = self._classe(wakeword_models=[self.modelo_nome])
        return self._modelo

    def esperar(self, timeout: float | None = None) -> str | None:
        if not self.disponivel:
            return None
        import numpy as np  # type: ignore

        taxa, bloco = 16000, 1280   # 80 ms, o quadro que o openWakeWord espera
        modelo = self._carregar()
        limite = None if timeout is None else time.monotonic() + timeout

        with self._sd.InputStream(samplerate=taxa, channels=1, dtype="int16",
                                  blocksize=bloco) as fluxo:
            while limite is None or time.monotonic() < limite:
                audio, _estourou = fluxo.read(bloco)
                pontuacoes = modelo.predict(np.asarray(audio).flatten())
                if any(p >= self.limiar for p in pontuacoes.values()):
                    modelo.reset()
                    return ""      # so o nome: o comando vem na escuta seguinte
        return None


def detectar_despertar(
    escuta: MotorEscuta,
    palavra: str = PALAVRA_PADRAO,
    preferido: str = "auto",
) -> Detector:
    """Escolhe o detector disponivel, na ordem openwakeword > transcricao > tecla."""
    if preferido == "tecla":
        return DespertarPorTecla(palavra)
    if preferido == "openwakeword":
        candidatos: list[Detector] = [DespertarOpenWakeWord()]
    elif preferido == "transcricao":
        candidatos = [DespertarPorTranscricao(escuta, palavra)]
    else:
        candidatos = [DespertarOpenWakeWord(), DespertarPorTranscricao(escuta, palavra)]

    for detector in candidatos:
        if detector.disponivel:
            return detector
    return DespertarPorTecla(palavra)
