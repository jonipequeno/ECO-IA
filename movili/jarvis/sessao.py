"""Loop de conversa do OpenJarvis: escuta, pensa, fala, repete."""

from __future__ import annotations

import time

from ..core.orquestrador import Ecossistema
from .conversa import Jarvis
from .despertar import PALAVRA_PADRAO, Detector, detectar_despertar
from .voz import MotorEscuta, MotorFala, Teclado, detectar_escuta, detectar_fala


class SessaoJarvis:
    """Une o Jarvis aos motores de voz e roda o ciclo de conversa."""

    def __init__(
        self,
        eco: Ecossistema,
        *,
        tts: str = "auto",
        stt: str = "auto",
        frases: int = 4,
        segundos_escuta: int = 8,
        porta_voz: str | None = None,
        palavra_despertar: str | None = None,
        despertar: str = "auto",
        janela_conversa: float = 25.0,
    ) -> None:
        self.fala: MotorFala = detectar_fala(tts)
        self.escuta: MotorEscuta = detectar_escuta(stt)
        self.segundos = segundos_escuta
        self.palavra = palavra_despertar or PALAVRA_PADRAO
        # So monta o detector quando a palavra foi pedida: sem ela, o Jarvis
        # escuta direto, como antes.
        self.detector: Detector | None = (
            detectar_despertar(self.escuta, self.palavra, despertar)
            if palavra_despertar is not None else None
        )
        # Depois de responder, segue ouvindo por este tempo - quem esta numa
        # conversa nao quer repetir o nome a cada frase.
        self.janela_conversa = janela_conversa
        self.jarvis = Jarvis(
            eco,
            frases=frases,
            voz_ativa=self.fala.nome != "texto",
            porta_voz=porta_voz or "diretor",
        )

    @property
    def modo(self) -> str:
        base = f"escuta={self.escuta.nome} fala={self.fala.nome}"
        if self.detector is not None:
            base += f" despertar={self.detector.nome}:'{self.palavra}'"
        return base

    def _dizer(self, texto: str) -> None:
        if not texto:
            return
        if self.fala.nome == "texto":
            print(f"\njarvis> {texto}\n")
        else:
            print(f"\njarvis> {texto}\n")
            self.fala.falar(texto)

    def _ouvir(self) -> str:
        if isinstance(self.escuta, Teclado):
            return self.escuta.ouvir()
        texto = self.escuta.ouvir(self.segundos)
        if texto:
            print(f"voce> {texto}")
        return texto

    def rodar(self) -> int:
        print(f"\n[OpenJarvis ativo - {self.modo}]")
        if self.detector is not None:
            return self._rodar_com_despertar()

        self._dizer(self.jarvis.saudacao())
        while True:
            entrada = self._ouvir()
            if not entrada:
                continue
            resposta = self.jarvis.responder(entrada)
            self._dizer(resposta["fala"])
            if resposta["acao"] == "sair":
                return 0

    def _rodar_com_despertar(self) -> int:
        """Espera o nome, atende, e segue ouvindo por um tempo antes de dormir."""
        assert self.detector is not None
        print(f"[em espera — diga '{self.palavra}' para acordar]")

        while True:
            comando = self.detector.esperar()
            if comando is None:          # Ctrl+C ou fim da entrada
                return 0

            self._dizer(self.jarvis.saudacao() if not comando else "")
            acordado_ate = time.monotonic() + self.janela_conversa

            while True:
                # A fala pode ter vindo junto do nome ("Jarvis, chama a Patricia").
                entrada = comando or self._ouvir()
                comando = ""
                if not entrada:
                    if time.monotonic() >= acordado_ate:
                        break        # silencio: volta a dormir
                    continue

                resposta = self.jarvis.responder(entrada)
                self._dizer(resposta["fala"])
                if resposta["acao"] == "sair":
                    return 0
                acordado_ate = time.monotonic() + self.janela_conversa

            print(f"[voltando a dormir — diga '{self.palavra}' de novo]")

    def uma_volta(self, texto: str) -> str:
        """Um unico turno (usado por testes e pela ponte HTTP)."""
        return self.jarvis.responder(texto)["fala"]
