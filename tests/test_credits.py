import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from credits import (
    HOURS_5,
    can_use,
    consume,
    format_hms,
    remaining_seconds,
    settle_active,
)


class CreditLogicTest(unittest.TestCase):
    def test_five_hours_is_18000_seconds(self):
        self.assertEqual(HOURS_5, 18_000)

    def test_start_5h_consume_10m_remaining_4h50m(self):
        purchased = HOURS_5
        consumed, remaining = consume(purchased, 0, 10 * 60)
        self.assertEqual(consumed, 600)
        self.assertEqual(remaining, 4 * 3600 + 50 * 60)
        self.assertEqual(format_hms(remaining), "04:50:00")

    def test_disconnect_does_not_keep_consuming(self):
        purchased = HOURS_5
        started = 1_000_000.0
        paused_at = started + 10 * 60
        consumed, remaining = settle_active(purchased, 0, started, paused_at)
        self.assertEqual(remaining, 4 * 3600 + 50 * 60)

        # wait / stay disconnected for a day
        later = paused_at + 24 * 3600
        still = remaining_seconds(purchased, consumed)
        self.assertEqual(still, remaining)
        self.assertEqual(still, remaining_seconds(purchased, consumed))
        _ = later  # unused wall-clock must not be applied after pause

    def test_reconnect_continues_from_remaining(self):
        purchased = HOURS_5
        consumed, remaining = consume(purchased, 0, 10 * 60)
        self.assertEqual(remaining, 4 * 3600 + 50 * 60)

        resume_at = time.time()
        after = resume_at + 5 * 60
        consumed, remaining = settle_active(purchased, consumed, resume_at, after)
        self.assertEqual(consumed, 15 * 60)
        self.assertEqual(remaining, 4 * 3600 + 45 * 60)

    def test_zero_balance_stops_paid_usage(self):
        purchased = HOURS_5
        consumed, remaining = consume(purchased, 0, HOURS_5)
        self.assertEqual(remaining, 0)
        self.assertFalse(can_use(purchased, consumed))

        consumed, remaining = consume(purchased, consumed, 120)
        self.assertEqual(consumed, HOURS_5)
        self.assertEqual(remaining, 0)

    def test_over_consume_clamps(self):
        consumed, remaining = consume(100, 90, 50)
        self.assertEqual(consumed, 100)
        self.assertEqual(remaining, 0)


if __name__ == "__main__":
    unittest.main()
