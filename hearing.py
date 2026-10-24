import json
import queue
import time
from pathlib import Path

from config import SETTINGS_PATH, VOSK_MODEL_PATH

# Dispositivos virtuais que nunca devem ser usados como microfone reserva.
IGNORED_DEVICE_NAMES = ("steam streaming",)
# Tempo extra concedido assim que a pessoa começa a falar (evita frase cortada).
SPEECH_GRACE_SECONDS = 4.0


class EvanHearing:
    def __init__(self, model_path: str | Path = VOSK_MODEL_PATH):
        try:
            import sounddevice as sd
            from vosk import KaldiRecognizer, Model
        except ImportError as erro:
            raise RuntimeError(
                "O modo de audição requer sounddevice e vosk. "
                "Instale as dependências com: pip install -r requirements.txt"
            ) from erro

        self._sd = sd
        self._kaldi_recognizer = KaldiRecognizer
        self.model_path = Path(model_path)
        if not self.model_path.is_absolute():
            self.model_path = Path(__file__).resolve().parent / self.model_path
        self.sample_rate = 16000

        self.primary_mic_id: int | None = None
        self.backup_mic_id: int | None = None
        self.primary_mic_name: str | None = None
        self.backup_mic_name: str | None = None

        self._load_microphone_settings()

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Modelo de voz não encontrado em: {self.model_path}"
            )

        self.model = Model(str(self.model_path))

    # ---------- configuração do microfone ----------

    def _load_microphone_settings(self):
        if not SETTINGS_PATH.exists():
            return

        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as file:
                settings = json.load(file)

            primary_id = settings.get("primary_mic_id")
            backup_id = settings.get("backup_mic_id")
            self.primary_mic_id = int(primary_id) if primary_id is not None else None
            self.backup_mic_id = int(backup_id) if backup_id is not None else None
            self.primary_mic_name = settings.get("primary_mic_name") or None
            self.backup_mic_name = settings.get("backup_mic_name") or None
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as erro:
            print(f"[AVISO] Não consegui carregar configuração do microfone: {erro}")

    def _show_active_microphone(self, device_id: int):
        try:
            device_info = self._sd.query_devices(device_id)
            print(f"[MICROFONE ATIVO] ID {device_id} - {device_info['name']}")
        except (IndexError, TypeError, ValueError) as erro:
            print(f"[AVISO] Não consegui ler o microfone ID {device_id}: {erro}")

    def _input_devices(self) -> list[tuple[int, str]]:
        try:
            devices = self._sd.query_devices()
        except Exception as erro:
            print(f"[ERRO AO LISTAR MICROFONES] {erro}")
            return []
        return [
            (device_id, str(device.get("name", "")))
            for device_id, device in enumerate(devices)
            if device.get("max_input_channels", 0) > 0
        ]

    @staticmethod
    def _find_device_by_name(name: str | None, inputs: list[tuple[int, str]]):
        """Acha o ID atual de um microfone pelo nome (os IDs mudam entre execuções)."""
        if not name:
            return None
        wanted = name.lower().strip()
        for device_id, device_name in inputs:
            current = device_name.lower().strip()
            if wanted in current or current in wanted:
                return device_id
        return None

    def _candidate_devices(self) -> list:
        inputs = self._input_devices()
        candidates: list = []

        def add(device_id):
            if device_id is not None and device_id not in candidates:
                candidates.append(device_id)

        for name, saved_id in (
            (getattr(self, "primary_mic_name", None), self.primary_mic_id),
            (getattr(self, "backup_mic_name", None), self.backup_mic_id),
        ):
            if name:
                add(self._find_device_by_name(name, inputs))
            else:
                add(saved_id)  # configuração antiga, só com número

        candidates.append(None)  # dispositivo padrão do sistema
        for device_id, device_name in inputs:
            if any(bad in device_name.lower() for bad in IGNORED_DEVICE_NAMES):
                continue
            add(device_id)
        return candidates

    # ---------- reconhecimento ----------

    def _make_recognizer(self, grammar: list[str] | None):
        if grammar:
            return self._kaldi_recognizer(
                self.model, self.sample_rate, json.dumps(grammar, ensure_ascii=False)
            )
        return self._kaldi_recognizer(self.model, self.sample_rate)

    @staticmethod
    def _clean(text: str) -> str:
        return " ".join(w for w in (text or "").split() if w != "[unk]").strip()

    def _listen_with_device(
        self, device_id: int | None, seconds: float, grammar: list[str] | None = None
    ) -> str:
        audio_queue = queue.Queue()

        def callback(indata, frames, time_info, status):
            if status:
                print(f"[MICROFONE] {status}")
            audio_queue.put(bytes(indata))

        recognizer = self._make_recognizer(grammar)

        with self._sd.RawInputStream(
            samplerate=self.sample_rate,
            blocksize=4000,
            dtype="int16",
            channels=1,
            device=device_id,
            callback=callback,
        ):
            deadline = time.monotonic() + seconds
            speech_started = False

            while time.monotonic() < deadline:
                try:
                    data = audio_queue.get(
                        timeout=min(0.25, max(0.01, deadline - time.monotonic()))
                    )
                except queue.Empty:
                    continue

                if recognizer.AcceptWaveform(data):
                    text = self._clean(json.loads(recognizer.Result()).get("text", ""))
                    if text:
                        return text
                elif not speech_started and hasattr(recognizer, "PartialResult"):
                    partial = json.loads(recognizer.PartialResult()).get("partial", "")
                    if self._clean(partial):
                        # Começou a falar: dá tempo para terminar a frase.
                        speech_started = True
                        deadline = max(
                            deadline, time.monotonic() + SPEECH_GRACE_SECONDS
                        )

        return self._clean(json.loads(recognizer.FinalResult()).get("text", ""))

    def listen_once(self, seconds: float = 6, grammar: list[str] | None = None) -> str:
        """Escuta uma fala. Com 'grammar' (lista de frases), só reconhece essas frases."""
        if seconds <= 0:
            raise ValueError("O tempo de escuta precisa ser maior que zero.")

        print("EVAN está ouvindo... fale agora.")

        errors = []
        for device_id in self._candidate_devices():
            try:
                if device_id is not None:
                    self._show_active_microphone(device_id)
                else:
                    print("[MICROFONE ATIVO] dispositivo padrão do sistema")
                return self._listen_with_device(device_id, seconds, grammar)
            except Exception as erro:
                errors.append(f"{device_id if device_id is not None else 'padrão'}: {erro}")
                print(f"[ERRO NO MICROFONE {device_id if device_id is not None else 'PADRÃO'}] {erro}")

        print("[ERRO] Nenhum microfone disponível. " + " | ".join(errors))
        return ""
