import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from wdtsot_statusline import format_statusline, minutes_label, remaining_label


class StatuslineTest(unittest.TestCase):
    def test_minutes(self):
        self.assertEqual(minutes_label(0), "0 min")
        self.assertEqual(minutes_label(59), "0 min")
        self.assertEqual(minutes_label(60), "1 min")
        self.assertEqual(minutes_label(217), "3 min")

    def test_remaining_friendly(self):
        self.assertEqual(remaining_label(0), "as 5h acabaram")
        self.assertEqual(remaining_label(90), "1 min restantes")
        self.assertEqual(remaining_label(3600), "1h restantes")
        self.assertEqual(remaining_label(17425), "4h 50 min restantes")

    def test_two_lines_like_web(self):
        text = format_statusline(
            {
                "block_code": "wdtsot-XVCD",
                "remaining_seconds": 17425,
                "used_seconds": 575,
                "line_used_seconds": 349,
                "chat_count": 6,
                "processing": False,
            }
        )
        self.assertIn("wdtsot-XVCD · GROK 4.6", text)
        self.assertIn("4h 50 min restantes", text)
        self.assertIn("5 min nesta linha", text)
        self.assertIn("6 chats · 9 min / 5h", text)
        self.assertNotIn("GROK processando", text)
        self.assertNotIn("ctx", text)

    def test_context_percent(self):
        text = format_statusline(
            {"block_code": "wdtsot-XVCD", "remaining_seconds": 100, "used_seconds": 0, "chat_count": 1},
            {"context_window": {"used_percentage": 34.5}},
        )
        self.assertIn("ctx 34%", text)

    def test_context_clamped(self):
        high = format_statusline({}, {"context_window": {"used_percentage": 140}})
        self.assertIn("ctx 100%", high)
        low = format_statusline({}, {"context_window": {"used_percentage": -3}})
        self.assertIn("ctx 0%", low)


if __name__ == "__main__":
    unittest.main()
