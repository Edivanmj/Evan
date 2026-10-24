import unittest

from commands import (
    chamou_evan,
    corrigir_comando_por_voz,
    remover_nome_evan,
    voice_grammar,
)


class VoiceCommandTests(unittest.TestCase):
    def test_voice_aliases_are_normalized(self):
        self.assertEqual("qual sua missao", corrigir_comando_por_voz("missão"))
        self.assertEqual("status", corrigir_comando_por_voz("painel do sistema"))

    def test_name_detection_requires_a_name_at_the_start(self):
        self.assertTrue(chamou_evan("EVA, missão"))
        self.assertFalse(chamou_evan("a novela da Eva"))
        self.assertFalse(chamou_evan("ela está ouvindo"))

    def test_name_removal_handles_recognized_variants(self):
        self.assertEqual("missão", remover_nome_evan("EVA, missão"))
        self.assertEqual("sair", remover_nome_evan("E van sair"))
        self.assertEqual("a novela da Eva", remover_nome_evan("a novela da Eva"))

    def test_grammar_has_commands_with_and_without_name(self):
        grammar = voice_grammar()
        for phrase in ("status", "eva status", "evan missão", "eva", "[unk]"):
            self.assertIn(phrase, grammar)

    def test_risky_one_word_aliases_were_removed(self):
        self.assertEqual("esta", corrigir_comando_por_voz("esta"))
        self.assertEqual("sai", corrigir_comando_por_voz("sai"))


if __name__ == "__main__":
    unittest.main()
