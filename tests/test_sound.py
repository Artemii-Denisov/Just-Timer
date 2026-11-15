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

    def test_generate_wav_tone(self):
        import wave
        from timer_app.utils.sound import _generate_wav_tone

        wav_path = _generate_wav_tone([(1046.5, 0.05), (0.0, 0.02), (880.0, 0.05)], "unit_test_tone.wav")
        self.assertIsNotNone(wav_path)
        self.assertTrue(os.path.exists(wav_path))
        try:
            with wave.open(wav_path, "rb") as wf:
                self.assertEqual(wf.getnchannels(), 1)
                self.assertEqual(wf.getsampwidth(), 2)
                self.assertGreater(wf.getnframes(), 0)
        finally:
            if wav_path and os.path.exists(wav_path):
                os.remove(wav_path)


if __name__ == "__main__":
    unittest.main()
