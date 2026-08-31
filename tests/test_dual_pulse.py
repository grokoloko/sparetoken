"""Two official pulses: 11:30 sell, 23:30 ship. Both plant a D+8 task."""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HB = (ROOT / "ceo" / "HEARTBEAT.md").read_text(encoding="utf-8")
SELL = (ROOT / "ceo" / "launch" / "sell.sh").read_text(encoding="utf-8")
VENUES = (ROOT / "ceo" / "VENUES.md").read_text(encoding="utf-8")


class DualPulseTest(unittest.TestCase):
    def test_two_clocks_are_official(self):
        self.assertIn("11:30", HB)
        self.assertIn("23:30", HB)
        self.assertIn("venda", HB.lower())
        self.assertIn("produto", HB.lower())

    def test_morning_script_exists_and_forbids_git(self):
        self.assertIn("git is forbidden", SELL)
        self.assertIn("VENUES", SELL)

    def test_venues_are_not_x_replies(self):
        self.assertIn("utm_", VENUES.lower())
        self.assertNotIn("reply farm", VENUES.lower())
        self.assertIn("warmup", VENUES.lower())
