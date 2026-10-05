import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from timer_app.utils.time_parser import parse_time_input, format_time


class TestTimeParser(unittest.TestCase):
    def test_numbers(self):
        self.assertEqual(parse_time_input("15"), 900)
        self.assertEqual(parse_time_input("5"), 300)
        self.assertEqual(parse_time_input("0.5"), 30)

    def test_colon_format(self):
        self.assertEqual(parse_time_input("10:00"), 600)
        self.assertEqual(parse_time_input("05:30"), 330)
        self.assertEqual(parse_time_input("1:00:00"), 3600)
        self.assertEqual(parse_time_input("01:15:30"), 4530)

    def test_text_units(self):
        self.assertEqual(parse_time_input("15m"), 900)
        self.assertEqual(parse_time_input("45s"), 45)
        self.assertEqual(parse_time_input("1h"), 3600)
        self.assertEqual(parse_time_input("1h 15m"), 4500)
        self.assertEqual(parse_time_input("1ч 30м"), 5400)
        self.assertEqual(parse_time_input("20 мин"), 1200)

    def test_format_time(self):
        self.assertEqual(format_time(900, show_hours=True), "00:15:00")
        self.assertEqual(format_time(900, show_hours=False), "15:00")
        self.assertEqual(format_time(3665, show_hours=False), "01:01:05")

    def test_invalid_input(self):
        self.assertIsNone(parse_time_input(""))
        self.assertIsNone(parse_time_input("abc"))
        self.assertIsNone(parse_time_input("1:2:3:4"))


if __name__ == "__main__":
    unittest.main()
