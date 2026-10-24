import tempfile
import unittest
from pathlib import Path

from brain import EvanBrain
from memory import MemoryStore


class EpisodeTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db = str(Path(self.temp_dir.name) / "memory.db")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_brain_records_turns_in_buffer_and_database(self):
        brain = EvanBrain(db_path=self.db)
        brain.handle("oi")

        self.assertEqual(2, len(brain.short_term))
        episodes = brain.memory.recent_episodes()
        self.assertEqual(["usuario", "evan"], [e["role"] for e in episodes])

    def test_short_term_buffer_is_limited(self):
        brain = EvanBrain(db_path=self.db)
        for _ in range(12):
            brain.handle("oi")
        self.assertEqual(10, len(brain.short_term))

    def test_episodes_do_not_pollute_fact_search(self):
        store = MemoryStore(self.db)
        store.save_episode("s1", "usuario", "meu cachorro se chama Rex")
        self.assertEqual([], store.search_memories("cachorro Rex"))

    def test_old_database_is_migrated_and_deduplicated(self):
        import sqlite3

        conn = sqlite3.connect(self.db)
        conn.execute(
            "CREATE TABLE memories (id INTEGER PRIMARY KEY AUTOINCREMENT, tipo TEXT NOT NULL,"
            " chave TEXT NOT NULL, valor TEXT NOT NULL, fonte TEXT NOT NULL,"
            " data_criacao TEXT NOT NULL, data_atualizacao TEXT NOT NULL)"
        )
        for valor in ("Python é legal", "python e legal", "Outra coisa"):
            conn.execute(
                "INSERT INTO memories (tipo,chave,valor,fonte,data_criacao,data_atualizacao)"
                " VALUES ('fato','Python',?, 'usuario','x','x')", (valor,))
        conn.commit()
        conn.close()

        store = MemoryStore(self.db)
        self.assertEqual(2, store.count_memories())
        self.assertTrue(store.search_memories("python legal"))
        self.assertTrue(list(Path(self.temp_dir.name).glob("backup_antes_fts_*.db")))


if __name__ == "__main__":
    unittest.main()
