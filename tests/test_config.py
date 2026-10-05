import unittest
import os
import tempfile
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from timer_app.config import ConfigManager, DEFAULT_CONFIG


class TestConfigManager(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_config = os.path.join(self.tmp_dir.name, "test_config.json")

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_default_values(self):
        cm = ConfigManager(self.tmp_config)
        self.assertEqual(cm.get("initial_time"), 900)
        self.assertEqual(cm.get("theme"), "Тёмная (Dark)")

    def test_save_and_reload(self):
        cm = ConfigManager(self.tmp_config)
        cm.set("initial_time", 1800)
        cm.set("theme", "Киберпанк")
        cm.save()

        # Загружаем новый экземпляр из того же файла
        cm2 = ConfigManager(self.tmp_config)
        self.assertEqual(cm2.get("initial_time"), 1800)
        self.assertEqual(cm2.get("theme"), "Киберпанк")


if __name__ == "__main__":
    unittest.main()
