import io
import sys
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from voice import EvanVoice


class OptionalVoiceTests(unittest.TestCase):
    def test_missing_tts_dependency_does_not_raise(self):
        output = io.StringIO()
        with patch.dict(sys.modules, {"pyttsx3": None}):
            with redirect_stdout(output):
                EvanVoice().speak("Olá")

        self.assertIn("modo texto continuará funcionando", output.getvalue())


if __name__ == "__main__":
    unittest.main()
