import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from llm import LocalLanguageModel, LocalModelError


class LocalLanguageModelTests(unittest.TestCase):
    def test_discovers_first_gguf_in_alphabetical_order(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            model_dir = Path(temp_dir)
            second = model_dir / "z-model.gguf"
            first = model_dir / "a-model.gguf"
            second.touch()
            first.touch()

            with patch("llm.DEFAULT_MODEL_DIR", model_dir):
                with patch.dict(os.environ, {}, clear=True):
                    model = LocalLanguageModel()

            self.assertEqual(first.resolve(), model.model_path)

    def test_environment_path_overrides_discovery_and_accepts_relative_paths(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            model_file = Path(temp_dir) / "chosen.gguf"
            model_file.touch()
            with patch("llm.BASE_DIR", Path(temp_dir)):
                with patch.dict(os.environ, {"EVAN_MODEL_PATH": "chosen.gguf"}):
                    model = LocalLanguageModel()

            self.assertEqual(model_file.resolve(), model.model_path)

    def test_missing_explicit_model_path_is_reported(self):
        with patch.dict(os.environ, {"EVAN_MODEL_PATH": "missing.gguf"}):
            model = LocalLanguageModel()

        self.assertTrue(model.available)
        with self.assertRaisesRegex(LocalModelError, "não existe"):
            model.generate("Olá")

    def test_generates_chat_with_history_and_memory_context(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            model_file = Path(temp_dir) / "model.gguf"
            model_file.touch()
            model = LocalLanguageModel(model_file)
            calls = {}

            class FakeLlama:
                def __init__(self, **kwargs):
                    calls["init"] = kwargs

                def create_chat_completion(self, **kwargs):
                    calls["completion"] = kwargs
                    return {
                        "choices": [
                            {"message": {"content": "  Olá! Como posso ajudar?  "}}
                        ]
                    }

            fake_runtime = SimpleNamespace(Llama=FakeLlama)
            with patch.dict("sys.modules", {"llama_cpp": fake_runtime}):
                response = model.generate(
                    "Olá",
                    history=[("usuario", "Bom dia"), ("evan", "Bom dia!")],
                    memories=[{"chave": "nome", "valor": "Ana", "fonte": "usuario"}],
                )

        self.assertEqual("Olá! Como posso ajudar?", response)
        messages = calls["completion"]["messages"]
        self.assertEqual(["system", "user", "assistant", "user"], [
            message["role"] for message in messages
        ])
        self.assertIn("Ana", messages[0]["content"])
        self.assertEqual(256, calls["completion"]["max_tokens"])

    def test_brain_routes_unmatched_explanation_to_local_model(self):
        from brain import EvanBrain

        with tempfile.TemporaryDirectory() as temp_dir:
            model_file = Path(temp_dir) / "model.gguf"
            model_file.touch()
            brain = EvanBrain(db_path=str(Path(temp_dir) / "memory.db"))
            brain.local_llm = LocalLanguageModel(model_file)

            def reply_to_explanation(**kwargs):
                self.assertEqual(
                    "Me explique em uma frase o que é a Lua.",
                    kwargs["messages"][-1]["content"],
                )
                return {
                    "choices": [
                        {"message": {"content": "A Lua é o satélite natural da Terra."}}
                    ]
                }

            fake = SimpleNamespace(
                create_chat_completion=reply_to_explanation
            )
            brain.local_llm._llama = fake

            response = brain.handle("Me explique em uma frase o que é a Lua.")

        self.assertIn("satélite natural", response)

    def test_brain_routes_unmatched_knowledge_question_to_local_model(self):
        from brain import EvanBrain

        with tempfile.TemporaryDirectory() as temp_dir:
            model_file = Path(temp_dir) / "model.gguf"
            model_file.touch()
            brain = EvanBrain(db_path=str(Path(temp_dir) / "memory.db"))
            brain.local_llm = LocalLanguageModel(model_file)

            def reply_to_knowledge_question(**kwargs):
                self.assertEqual(
                    "O que você sabe sobre a Lua?",
                    kwargs["messages"][-1]["content"],
                )
                return {
                    "choices": [{"message": {"content": "A Lua orbita a Terra."}}]
                }

            brain.local_llm._llama = SimpleNamespace(
                create_chat_completion=reply_to_knowledge_question
            )

            response = brain.handle("O que você sabe sobre a Lua?")

        self.assertIn("orbita a Terra", response)


if __name__ == "__main__":
    unittest.main()
