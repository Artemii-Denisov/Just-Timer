import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from timer_app.utils.sound import SOUND_PRESETS, play_sound_by_type


class TestSound(unittest.TestCase):
    def test_presets_exist(self):
        self.assertIn("Дзынь (Ding)", SOUND_PRESETS)
        self.assertIn("Короткий сигнал (Beep)", SOUND_PRESETS)
        self.assertIn("Колокольчики (Chimes)", SOUND_PRESETS)
        self.assertIn("Уведомление (Notify)", SOUND_PRESETS)
        self.assertIn("Та-да! (Tada)", SOUND_PRESETS)

    def test_play_does_not_crash(self):
        # Проверяем, что вызов не выбрасывает исключений
        from timer_app.utils.sound import play_round_sound, play_finish_sound
        try:
            play_sound_by_type("Дзынь (Ding)")
            play_round_sound("Короткий сигнал (Beep)")
            play_finish_sound("Дзынь (Ding)")
        except Exception as e:
            self.fail(f"Sound functions raised {e}")


if __name__ == "__main__":
    unittest.main()
