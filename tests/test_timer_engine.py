import unittest
import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from timer_app.core.timer_engine import TimerEngine


class TestTimerEngine(unittest.TestCase):
    def test_initial_state(self):
        engine = TimerEngine(initial_duration=300)
        self.assertEqual(engine.initial_duration, 300)
        self.assertEqual(engine.remaining, 300)
        self.assertFalse(engine.is_running)
        self.assertFalse(engine.is_finished)

    def test_start_and_pause(self):
        engine = TimerEngine(initial_duration=10)
        engine.start()
        self.assertTrue(engine.is_running)

        time.sleep(0.05)
        rem, finished = engine.tick()
        self.assertLess(rem, 10)
        self.assertFalse(finished)

        engine.pause()
        self.assertFalse(engine.is_running)

    def test_toggle(self):
        engine = TimerEngine(initial_duration=10)
        running = engine.toggle()
        self.assertTrue(running)
        self.assertTrue(engine.is_running)

        running = engine.toggle()
        self.assertFalse(running)
        self.assertFalse(engine.is_running)

    def test_reset(self):
        engine = TimerEngine(initial_duration=10)
        engine.start()
        time.sleep(0.05)
        engine.tick()
        engine.reset()

        self.assertFalse(engine.is_running)
        self.assertEqual(engine.remaining, 10)
        self.assertFalse(engine.is_finished)

    def test_set_and_adjust_duration(self):
        engine = TimerEngine(initial_duration=300)
        engine.set_duration(600)
        self.assertEqual(engine.initial_duration, 600)
        self.assertEqual(engine.remaining, 600)

        engine.adjust_duration(60)
        self.assertEqual(engine.initial_duration, 660)

        engine.adjust_duration(-1000)
        self.assertGreaterEqual(engine.initial_duration, 1.0)

    def test_finish_detection(self):
        engine = TimerEngine(initial_duration=0.1)
        engine.start()
        time.sleep(0.12)
        rem, is_finished = engine.tick()

        self.assertEqual(rem, 0.0)
        self.assertTrue(is_finished)
        self.assertTrue(engine.is_finished)
        self.assertFalse(engine.is_running)

    def test_rounds_progression(self):
        # 3 раунда по 0.05 сек
        engine = TimerEngine(initial_duration=0.05, total_rounds=3)
        engine.start()

        # Раунд 1 -> 2
        time.sleep(0.06)
        rem, event = engine.tick()
        self.assertTrue(event)
        self.assertEqual(engine.last_event, "round_next")
        self.assertEqual(engine.current_round, 2)

        # Раунд 2 -> 3
        time.sleep(0.06)
        rem, event = engine.tick()
        self.assertTrue(event)
        self.assertEqual(engine.last_event, "round_next")
        self.assertEqual(engine.current_round, 3)

        # Раунд 3 -> финал
        time.sleep(0.06)
        rem, event = engine.tick()
        self.assertTrue(event)
        self.assertEqual(engine.last_event, "all_finished")
        self.assertTrue(engine.is_finished)

    def test_rounds_with_rest(self):
        # 2 раунда по 0.05 сек с отдыхом 0.05 сек
        engine = TimerEngine(initial_duration=0.05, total_rounds=2, rest_duration=0.05)
        engine.start()

        # Раунд 1 -> отдых
        time.sleep(0.06)
        rem, event = engine.tick()
        self.assertTrue(event)
        self.assertEqual(engine.last_event, "round_rest")
        self.assertTrue(engine.is_rest)
        self.assertEqual(engine.current_round, 1)

        # Отдых -> Раунд 2
        time.sleep(0.06)
        rem, event = engine.tick()
        self.assertTrue(event)
        self.assertEqual(engine.last_event, "round_next")
        self.assertFalse(engine.is_rest)
        self.assertEqual(engine.current_round, 2)


if __name__ == "__main__":
    unittest.main()
