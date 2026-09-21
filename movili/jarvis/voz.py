"""Camada de voz do OpenJarvis: escuta (STT) e fala (TTS), tudo local.

Nada aqui e obrigatorio: se nenhum motor estiver instalado, o Jarvis cai
para teclado + texto e continua funcionando. Os motores sao detectados em
tempo de execucao, na ordem de preferencia.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path


# =====================================================================
# Fala (TTS)
# =====================================================================
class MotorFala:
    nome = "nenhum"
    disponivel = False

    def falar(self, texto: str) -> None:
        raise NotImplementedError

    def __repr__(self) -> str:  # pragma: no cover
        return f"<TTS {self.nome}>"


class SemFala(MotorFala):
    """Modo texto: apenas imprime. Usado quando nao ha TTS instalado."""

    nome = "texto"
    disponivel = True

    def falar(self, texto: str) -> None:
        print(f"[jarvis] {texto}")


class PiperTTS(MotorFala):
    """Piper: TTS neural local, rapido e com vozes em portugues do Brasil.

    Instalacao: pip install piper-tts
    Voz pt-BR:  python -m piper.download_voices pt_BR-faber-medium
    """

    nome = "piper"

    def __init__(self, voz: str | None = None) -> None:
        self.binario = shutil.which("piper")
        self.voz = voz or os.getenv("MOVILI_VOZ_PIPER", "pt_BR-faber-medium")
        self.player = self._descobrir_player()
        self.disponivel = bool(self.binario and self.player)

    @staticmethod
    def _descobrir_player() -> list[str] | None:
        for cmd in (["paplay"], ["aplay", "-q"], ["afplay"], ["play", "-q"]):
            if shutil.which(cmd[0]):
                return cmd
        return None

    def falar(self, texto: str) -> None:
        if not self.disponivel:
            print(f"[jarvis] {texto}")
            return
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            destino = tmp.name
        try:
            subprocess.run(
                [self.binario, "--model", self.voz, "--output_file", destino],
                input=texto.encode("utf-8"),
                check=True,
                capture_output=True,
                timeout=120,
            )
            subprocess.run([*self.player, destino], check=False, capture_output=True, timeout=300)
        except (subprocess.SubprocessError, OSError) as exc:
            print(f"[jarvis: falha no piper, caindo para texto: {exc}]")
            print(f"[jarvis] {texto}")
        finally:
            Path(destino).unlink(missing_ok=True)


class SistemaTTS(MotorFala):
    """TTS nativo do sistema operacional: 'say' (macOS) ou 'espeak-ng' (Linux)."""

    nome = "sistema"

    def __init__(self) -> None:
        self.comando: list[str] | None = None
        if shutil.which("say"):
            self.comando = ["say", "-v", os.getenv("MOVILI_VOZ_SAY", "Luciana")]
        elif shutil.which("espeak-ng"):
            self.comando = ["espeak-ng", "-v", "pt-br", "-s", "165"]
        elif shutil.which("espeak"):
            self.comando = ["espeak", "-v", "pt-br", "-s", "165"]
        self.disponivel = self.comando is not None

    def falar(self, texto: str) -> None:
        if not self.comando:
            print(f"[jarvis] {texto}")
            return
        try:
            subprocess.run([*self.comando, texto], check=False, capture_output=True, timeout=300)
        except (subprocess.SubprocessError, OSError):
            print(f"[jarvis] {texto}")


# =====================================================================
# Escuta (STT)
# =====================================================================
class MotorEscuta:
    nome = "nenhum"
    disponivel = False

    def ouvir(self, segundos: int = 8) -> str:
        raise NotImplementedError

    def __repr__(self) -> str:  # pragma: no cover
        return f"<STT {self.nome}>"


class Teclado(MotorEscuta):
    """Sem microfone: o usuario digita. Sempre disponivel."""

    nome = "teclado"
    disponivel = True

    def ouvir(self, segundos: int = 8) -> str:
        try:
            return input("voce> ").strip()
        except (EOFError, KeyboardInterrupt):
            return "/sair"


class FasterWhisper(MotorEscuta):
    """faster-whisper + sounddevice: transcricao local do microfone.

    Instalacao: pip install faster-whisper sounddevice numpy
    O modelo baixa sozinho na primeira execucao (padrao: 'small').
    """

    nome = "faster-whisper"

    def __init__(self, modelo: str | None = None) -> None:
        self.modelo_nome = modelo or os.getenv("MOVILI_WHISPER", "small")
        self._modelo = None
        self._sd = None
        try:
            import sounddevice  # type: ignore
            from faster_whisper import WhisperModel  # type: ignore
        except ImportError:
            self.disponivel = False
            return
        self._sd = sounddevice
        self._classe = WhisperModel
        self.disponivel = True

    def _carregar(self):
        if self._modelo is None:
            print(f"[jarvis: carregando whisper '{self.modelo_nome}'...]")
            self._modelo = self._classe(self.modelo_nome, device="auto", compute_type="int8")
        return self._modelo

    def ouvir(self, segundos: int = 8) -> str:
        if not self.disponivel:
            return ""
        import numpy as np  # type: ignore

        taxa = 16000
        print(f"[jarvis: ouvindo por {segundos}s...]")
        audio = self._sd.rec(int(segundos * taxa), samplerate=taxa, channels=1, dtype="int16")
        self._sd.wait()

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            caminho = tmp.name
        try:
            with wave.open(caminho, "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(taxa)
                wav.writeframes(np.asarray(audio).tobytes())
            segmentos, _info = self._carregar().transcribe(caminho, language="pt", vad_filter=True)
            return " ".join(s.text for s in segmentos).strip()
        finally:
            Path(caminho).unlink(missing_ok=True)


class WhisperCpp(MotorEscuta):
    """whisper.cpp via binario 'whisper-cli', para quem ja tem compilado."""

    nome = "whisper.cpp"

    def __init__(self, modelo: str | None = None) -> None:
        self.binario = shutil.which("whisper-cli") or shutil.which("whisper.cpp")
        self.modelo = modelo or os.getenv("MOVILI_WHISPER_CPP_MODEL", "")
        self.gravador = shutil.which("arecord") or shutil.which("rec")
        self.disponivel = bool(self.binario and self.modelo and self.gravador)

    def ouvir(self, segundos: int = 8) -> str:
        if not self.disponivel:
            return ""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            caminho = tmp.name
        try:
            print(f"[jarvis: ouvindo por {segundos}s...]")
            subprocess.run(
                [self.gravador, "-f", "S16_LE", "-r", "16000", "-c", "1",
                 "-d", str(segundos), caminho],
                check=False, capture_output=True, timeout=segundos + 15,
            )
            saida = subprocess.run(
                [self.binario, "-m", self.modelo, "-f", caminho, "-l", "pt", "-nt"],
                check=False, capture_output=True, timeout=180,
            )
            return saida.stdout.decode("utf-8", errors="replace").strip()
        except (subprocess.SubprocessError, OSError) as exc:
            print(f"[jarvis: falha no whisper.cpp: {exc}]")
            return ""
        finally:
            Path(caminho).unlink(missing_ok=True)


# =====================================================================
# Deteccao automatica
# =====================================================================
def detectar_fala(preferido: str = "auto") -> MotorFala:
    """Escolhe o motor de TTS disponivel, na ordem: piper > sistema > texto."""
    candidatos: list[MotorFala]
    if preferido == "piper":
        candidatos = [PiperTTS()]
    elif preferido == "sistema":
        candidatos = [SistemaTTS()]
    elif preferido == "texto":
        return SemFala()
    else:
        candidatos = [PiperTTS(), SistemaTTS()]
    for motor in candidatos:
        if motor.disponivel:
            return motor
    return SemFala()


def detectar_escuta(preferido: str = "auto") -> MotorEscuta:
    """Escolhe o motor de STT disponivel, na ordem: faster-whisper > whisper.cpp > teclado."""
    candidatos: list[MotorEscuta]
    if preferido == "whisper":
        candidatos = [FasterWhisper()]
    elif preferido == "whisper.cpp":
        candidatos = [WhisperCpp()]
    elif preferido == "teclado":
        return Teclado()
    else:
        candidatos = [FasterWhisper(), WhisperCpp()]
    for motor in candidatos:
        if motor.disponivel:
            return motor
    return Teclado()


def diagnostico() -> dict[str, dict[str, bool | str]]:
    """Relatorio do que esta instalado, usado por 'movili jarvis --diagnostico'."""
    motores = {
        "tts_piper": PiperTTS(),
        "tts_sistema": SistemaTTS(),
        "stt_faster_whisper": FasterWhisper(),
        "stt_whisper_cpp": WhisperCpp(),
    }
    return {
        nome: {"motor": m.nome, "disponivel": bool(m.disponivel)}
        for nome, m in motores.items()
    }
