import unittest
from unittest.mock import Mock

from modes import _farewell


class FarewellTests(unittest.TestCase):
    def test_uses_name_saved_in_memory(self):
        brain = Mock()
        brain.memory.find_similar_memory.return_value = {"valor": "Ana"}

        self.assertEqual("Até logo, Ana.", _farewell(brain))
        brain.memory.find_similar_memory.assert_called_once_with("fato", "meu nome")

    def test_uses_default_name_when_memory_is_missing(self):
        brain = Mock()
        brain.memory.find_similar_memory.return_value = None

        self.assertEqual("Até logo, Edivan.", _farewell(brain))

    def test_uses_default_name_when_saved_name_is_blank(self):
        brain = Mock()
        brain.memory.find_similar_memory.return_value = {"valor": " "}

        self.assertEqual("Até logo, Edivan.", _farewell(brain))


if __name__ == "__main__":
    unittest.main()
