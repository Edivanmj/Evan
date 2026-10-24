VOICE_ID = 0
VOICE_RATE = 175
VOICE_VOLUME = 1.0


class EvanVoice:
    def __init__(self, face=None):
        self.face = face
        self._missing_dependency_reported = False

    def _prepare_text(self, text: str) -> str:
        if not text:
            return ""

        # Evita falar textos gigantes
        if len(text) > 350:
            text = "Resposta grande exibida no terminal."

        # Pausas leves para parecer menos robótico
        text = text.replace(". ", ".  ")
        text = text.replace("? ", "?  ")
        text = text.replace("! ", "!  ")
        text = text.replace(": ", ":  ")

        return text

    def speak(self, text: str) -> None:
        text = self._prepare_text(text)

        if not text:
            return

        try:
            import pyttsx3

            if self.face:
                self.face.speaking()

            engine = pyttsx3.init()
            voices = engine.getProperty("voices")

            if voices and VOICE_ID < len(voices):
                engine.setProperty("voice", voices[VOICE_ID].id)

            engine.setProperty("rate", VOICE_RATE)
            engine.setProperty("volume", VOICE_VOLUME)

            engine.say(text)
            engine.runAndWait()
            engine.stop()

        except ImportError as erro:
            if not self._missing_dependency_reported:
                print(
                    "[AVISO DE VOZ] pyttsx3 não está instalado. "
                    "O modo texto continuará funcionando sem áudio."
                )
                self._missing_dependency_reported = True
        except Exception as erro:
            print(f"[ERRO DE VOZ] {erro}")

        finally:
            if self.face:
                self.face.idle()