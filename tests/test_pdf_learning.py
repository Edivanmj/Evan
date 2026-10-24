import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from brain import EvanBrain
from memory import MemoryStore
from pdf_learning import learn_pdf, split_text


class FakePage:
    def __init__(self, text):
        self.text = text

    def extract_text(self):
        return self.text


class FakePdf:
    def __init__(self, _path):
        self.pages = [
            FakePage(
                "A astronomia estuda estrelas distantes e descreve planetas "
                "que orbitam outras estrelas."
            ),
            FakePage(None),
        ]


class PdfLearningTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.store = MemoryStore(str(Path(self.temp_dir.name) / "memory.db"))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_split_text_respects_maximum_size_even_for_long_words(self):
        parts = split_text("alpha " + ("x" * 14) + " omega", max_size=6)

        self.assertTrue(parts)
        self.assertTrue(all(len(part) <= 6 for part in parts))
        self.assertEqual("alpha", parts[0])

    @patch("pdf_learning.PdfReader", FakePdf)
    def test_learning_saves_extractable_pages_and_brain_cites_them(self):
        pdf_path = Path(self.temp_dir.name) / "astronomia.pdf"
        pdf_path.touch()

        saved_count = learn_pdf(pdf_path, memory=self.store)
        response = EvanBrain(db_path=self.store.db_path).handle(
            "o que o PDF explica sobre astronomia?"
        )

        self.assertGreater(saved_count, 0)
        self.assertIn("astronomia", response.lower())
        self.assertIn("astronomia.pdf, página 1", response)
        self.assertNotIn("página 2", response)

    @patch("pdf_learning.PdfReader", FakePdf)
    def test_pdf_question_does_not_return_a_fixed_unrelated_answer(self):
        pdf_path = Path(self.temp_dir.name) / "astronomia.pdf"
        pdf_path.touch()
        learn_pdf(pdf_path, memory=self.store)

        response = EvanBrain(db_path=self.store.db_path).handle(
            "me explique o PDF sobre culinária"
        )

        self.assertIn("Não encontrei esse assunto", response)
        self.assertNotIn("missão principal do EVAN", response)

    @patch("pdf_learning.PdfReader", FakePdf)
    def test_summary_uses_the_stored_pdf_text(self):
        pdf_path = Path(self.temp_dir.name) / "astronomia.pdf"
        pdf_path.touch()
        learn_pdf(pdf_path, memory=self.store)

        response = EvanBrain(db_path=self.store.db_path).handle("resuma o PDF")

        self.assertIn("astronomia", response.lower())
        self.assertIn("astronomia.pdf, página 1", response)
        self.assertNotIn("conversar, aprender, lembrar e evoluir", response)

    @patch("pdf_learning.PdfReader", FakePdf)
    def test_knowledge_question_uses_pdf_text_not_project_defaults(self):
        pdf_path = Path(self.temp_dir.name) / "astronomia.pdf"
        pdf_path.touch()
        learn_pdf(pdf_path, memory=self.store)

        response = EvanBrain(db_path=self.store.db_path).handle(
            "o que você sabe sobre astronomia?"
        )

        self.assertIn("estuda estrelas", response)
        self.assertIn("astronomia.pdf, página 1", response)

    @patch("pdf_learning.PdfReader", FakePdf)
    def test_quiz_uses_learned_pdf_text(self):
        pdf_path = Path(self.temp_dir.name) / "astronomia.pdf"
        pdf_path.touch()
        learn_pdf(pdf_path, memory=self.store)

        response = EvanBrain(db_path=self.store.db_path).handle(
            "me faça perguntas sobre o PDF"
        )

        self.assertIn("estrelas", response.lower())
        self.assertIn("astronomia.pdf, página 1", response)
        self.assertNotIn("O que significa EVAN OS?", response)


if __name__ == "__main__":
    unittest.main()
