import tempfile
import unittest
from pathlib import Path

from memory import MemoryStore


class MemoryStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.store = MemoryStore(str(Path(self.temp_dir.name) / "memory.db"))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_correction_only_updates_an_exact_normalized_key(self):
        longer_key = self.store.save_memory(
            "fato", "meu nome do cachorro", "Rex"
        )

        self.assertIsNone(self.store.find_similar_memory("fato", "meu nome"))

        corrected = self.store.save_memory(
            "fato", "meu nome", "Ada", replace_existing=True
        )

        self.assertNotEqual(longer_key["id"], corrected["id"])
        self.assertEqual("Rex", self.store.find_similar_memory(
            "fato", "meu nome do cachorro"
        )["valor"])

    def test_duplicate_save_and_correction_return_current_memory(self):
        created = self.store.save_memory("fato", "meu nome", "Edivan")
        duplicate = self.store.save_memory("fato", "meu nome", "EDIVAN")

        self.assertEqual(created["id"], duplicate["id"])
        self.assertEqual(1, len(self.store.list_memories()))

        corrected = self.store.save_memory(
            "fato", "meu nome", "Edivan Mendonça", replace_existing=True
        )

        self.assertEqual(created["id"], corrected["id"])
        self.assertEqual("Edivan Mendonça", corrected["valor"])
        self.assertEqual("Edivan Mendonça", self.store.list_memories()[0]["valor"])

    def test_search_uses_words_instead_of_partial_substrings(self):
        self.store.save_memory(
            "fato", "projeto", "Cartografia e mapas digitais"
        )

        self.assertEqual([], self.store.search_memories("cart"))
        self.assertEqual(
            "projeto",
            self.store.search_memories("mapas digitais")[0]["chave"],
        )

    def test_delete_memory_by_id(self):
        memory = self.store.save_memory("fato", "cor favorito", "azul")

        self.assertTrue(self.store.delete_memory_by_id(memory["id"]))
        self.assertFalse(self.store.delete_memory_by_id(memory["id"]))
        self.assertEqual([], self.store.list_memories())


if __name__ == "__main__":
    unittest.main()
