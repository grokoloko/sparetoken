import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from clock import (
    ClockError,
    end_processing,
    ensure_can_chat,
    open_chat,
    rename_chat,
    snapshot,
    start_another,
    start_processing,
    use_chat,
)
from credits import HOURS_5
from db import connect, credit_wallet, get_or_create_session


class PaidClockTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.conn = connect(Path(self.tmp.name) / "t.sqlite")
        self.row = get_or_create_session(self.conn, "token-clock-abcdefghij", "sid-clock")
        credit_wallet(self.conn, self.row["id"], HOURS_5)

    def tearDown(self):
        self.conn.close()
        self.tmp.cleanup()

    def test_idle_tab_does_not_consume(self):
        t0 = 1_000_000.0
        start = snapshot(self.conn, self.row["id"], now=t0)
        later = snapshot(self.conn, self.row["id"], now=t0 + 10 * 60)
        self.assertEqual(start["remaining_seconds"], HOURS_5)
        self.assertEqual(later["remaining_seconds"], HOURS_5)
        self.assertEqual(later["session_status"], "idle")

    def test_only_processing_window_counts(self):
        t0 = 1_000_000.0
        start_processing(self.conn, self.row["id"], now=t0, channel="web", label="web")
        snap = end_processing(self.conn, self.row["id"], now=t0 + 90)
        self.assertEqual(snap["used_seconds"], 90)
        self.assertEqual(snap["remaining_seconds"], HOURS_5 - 90)
        idle = snapshot(self.conn, self.row["id"], now=t0 + 3600)
        self.assertEqual(idle["used_seconds"], 90)

    def test_two_chats_sum_to_wallet(self):
        t0 = 2_000_000.0
        start_processing(self.conn, self.row["id"], now=t0, channel="web", label="web-1")
        end_processing(self.conn, self.row["id"], now=t0 + 60)
        start_another(self.conn, self.row["id"], now=t0 + 61)
        start_processing(self.conn, self.row["id"], now=t0 + 70, channel="ssh", label="ssh-1")
        snap = end_processing(self.conn, self.row["id"], now=t0 + 130)
        self.assertEqual(snap["used_seconds"], 120)
        self.assertGreaterEqual(len(snap["chats"]), 2)
        per = {c["label"]: c["used_seconds"] for c in snap["chats"]}
        self.assertIn(60, per.values())

    def test_zero_stops_and_blocks_chat(self):
        t0 = 3_000_000.0
        start_processing(self.conn, self.row["id"], now=t0)
        snap = end_processing(self.conn, self.row["id"], now=t0 + HOURS_5)
        self.assertEqual(snap["remaining_seconds"], 0)
        self.assertTrue(snap["exhausted"])
        with self.assertRaises(ClockError):
            start_processing(self.conn, self.row["id"], now=t0 + HOURS_5 + 10)
        with self.assertRaises(ClockError):
            ensure_can_chat(self.conn, self.row["id"], now=t0 + HOURS_5 + 20)

    def test_warn_under_five_minutes(self):
        t0 = 4_000_000.0
        start_processing(self.conn, self.row["id"], now=t0)
        snap = snapshot(self.conn, self.row["id"], now=t0 + HOURS_5 - 90)
        self.assertTrue(snap["warn"])
        self.assertEqual(snap["remaining_seconds"], 90)

    def test_return_url_uses_block_when_present(self):
        snap = snapshot(self.conn, self.row["id"])
        self.assertTrue(snap["return_url"].startswith("https://wdtsot.shop"))

    def test_start_another_always_new_line(self):
        t0 = 5_000_000.0
        start_processing(self.conn, self.row["id"], now=t0, channel="web", label="web")
        end_processing(self.conn, self.row["id"], now=t0 + 10)
        first = snapshot(self.conn, self.row["id"], now=t0 + 11)
        second = start_another(self.conn, self.row["id"], now=t0 + 12)
        self.assertEqual(len(second["chats"]), len(first["chats"]) + 1)
        self.assertNotEqual(second["active_chat_id"], first["active_chat_id"])
        self.assertTrue(second["chats"][0]["label"].startswith("Chat "))

    def test_rename_and_use_keep_wallet(self):
        t0 = 6_000_000.0
        start_processing(self.conn, self.row["id"], now=t0, channel="web", label="web")
        end_processing(self.conn, self.row["id"], now=t0 + 40)
        other = start_another(self.conn, self.row["id"], now=t0 + 41)
        old = [c for c in other["chats"] if c["id"] != other["active_chat_id"]][0]
        named = rename_chat(self.conn, self.row["id"], old["id"], "Pauta", now=t0 + 42)
        labels = {c["id"]: c["label"] for c in named["chats"]}
        self.assertEqual(labels[old["id"]], "Pauta")
        used = use_chat(self.conn, self.row["id"], old["id"], now=t0 + 43)
        self.assertEqual(used["active_chat_id"], old["id"])
        self.assertEqual(used["used_seconds"], 40)


if __name__ == "__main__":
    unittest.main()
