"""Loop de conversa do OpenJarvis: escuta, pensa, fala, repete."""

from __future__ import annotations

from ..core.orquestrador import Ecossistema
from .conversa import Jarvis
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
    ) -> None:
        self.fala: MotorFala = detectar_fala(tts)
        self.escuta: MotorEscuta = detectar_escuta(stt)
        self.segundos = segundos_escuta
        self.jarvis = Jarvis(
            eco,
            frases=frases,
            voz_ativa=self.fala.nome != "texto",
            porta_voz=porta_voz or "diretor",
        )

    @property
    def modo(self) -> str:
        return f"escuta={self.escuta.nome} fala={self.fala.nome}"

    def _dizer(self, texto: str) -> None:
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
        self._dizer(self.jarvis.saudacao())
        while True:
            entrada = self._ouvir()
            if not entrada:
                continue
            resposta = self.jarvis.responder(entrada)
            self._dizer(resposta["fala"])
            if resposta["acao"] == "sair":
                return 0

    def uma_volta(self, texto: str) -> str:
        """Um unico turno (usado por testes e pela ponte HTTP)."""
        return self.jarvis.responder(texto)["fala"]
