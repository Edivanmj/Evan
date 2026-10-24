import json
import time
import unittest

from hearing import EvanHearing


class SilentStream:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


class SilentAudio:
    def RawInputStream(self, **_kwargs):
        return SilentStream()

    def query_devices(self):
        return []


class SilentRecognizer:
    def __init__(self, _model, _sample_rate):
        pass

    def AcceptWaveform(self, _data):
        return False

    def FinalResult(self):
        return json.dumps({"text": ""})


class HearingTests(unittest.TestCase):
    def test_silent_microphone_does_not_block_past_timeout(self):
        hearing = EvanHearing.__new__(EvanHearing)
        hearing._sd = SilentAudio()
        hearing._kaldi_recognizer = SilentRecognizer
        hearing.model = object()
        hearing.sample_rate = 16000
        hearing.primary_mic_id = None
        hearing.backup_mic_id = None

        started = time.monotonic()
        result = hearing.listen_once(seconds=0.05)
        elapsed = time.monotonic() - started

        self.assertEqual("", result)
        self.assertLess(elapsed, 0.5)

    def test_nonpositive_listen_duration_is_rejected(self):
        hearing = EvanHearing.__new__(EvanHearing)

        with self.assertRaises(ValueError):
            hearing.listen_once(seconds=0)


class NamedAudio(SilentAudio):
    def query_devices(self, device=None):
        devices = [
            {"name": "Mapeador de som", "max_input_channels": 2},
            {"name": "Microfone (Steam Streaming Micr", "max_input_channels": 8},
            {"name": "Microfone (ELITE 06)", "max_input_channels": 1},
            {"name": "Alto-falantes", "max_input_channels": 0},
        ]
        return devices if device is None else devices[device]


class RecordingRecognizer(SilentRecognizer):
    calls = []

    def __init__(self, _model, _sample_rate, *grammar):
        RecordingRecognizer.calls.append(grammar)


def make_hearing(**settings):
    hearing = EvanHearing.__new__(EvanHearing)
    hearing._sd = NamedAudio()
    hearing._kaldi_recognizer = RecordingRecognizer
    hearing.model = object()
    hearing.sample_rate = 16000
    hearing.primary_mic_id = settings.get("id")
    hearing.backup_mic_id = None
    hearing.primary_mic_name = settings.get("name")
    hearing.backup_mic_name = None
    return hearing


class MicrophoneSelectionTests(unittest.TestCase):
    def test_saved_name_wins_over_a_stale_id(self):
        hearing = make_hearing(name="Microfone (ELITE 06)", id=1)
        self.assertEqual(2, hearing._candidate_devices()[0])

    def test_old_config_with_only_an_id_still_works(self):
        hearing = make_hearing(id=0)
        self.assertEqual(0, hearing._candidate_devices()[0])

    def test_virtual_steam_microphone_is_not_a_fallback(self):
        candidates = make_hearing(name="Microfone (ELITE 06)")._candidate_devices()
        self.assertNotIn(1, candidates)

    def test_grammar_is_passed_to_the_recognizer_and_unk_is_dropped(self):
        RecordingRecognizer.calls = []
        hearing = make_hearing(name="Microfone (ELITE 06)")
        hearing.listen_once(seconds=0.05, grammar=["status", "[unk]"])
        self.assertEqual(1, len(RecordingRecognizer.calls[0]))
        self.assertEqual("status", EvanHearing._clean("[unk] status [unk]"))


if __name__ == "__main__":
    unittest.main()
