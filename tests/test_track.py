"""First-party visit / pay_click / claim_ok — no PII, no third-party pixel."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db import connect
from track import ALLOWED_EVENTS, record_event, sanitize_payload


class TrackSanitizeTest(unittest.TestCase):
    def test_keeps_known_event_and_short_utms(self):
        clean = sanitize_payload(
            {
                "event": "visit",
                "utm_source": "x",
                "utm_medium": "social",
                "utm_campaign": "heartbeat",
                "utm_content": "p004",
                "code": "wdtsot-7K2M",
                "email": "nope@example.com",
                "contact": "11999990000",
            }
        )
        self.assertEqual(clean["event"], "visit")
        self.assertEqual(clean["utm_source"], "x")
        self.assertEqual(clean["utm_content"], "p004")
        self.assertEqual(clean["code"], "wdtsot-7K2M")
        self.assertNotIn("email", clean)
        self.assertNotIn("contact", clean)

    def test_drops_unknown_event_and_garbage_code(self):
        clean = sanitize_payload({"event": "hack", "code": "DROP TABLE", "utm_source": "x" * 200})
        self.assertIsNone(clean)

    def test_allowed_events_are_the_three_we_need(self):
        self.assertEqual(ALLOWED_EVENTS, frozenset({"visit", "pay_click", "claim_ok"}))


class TrackDbTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.conn = connect(Path(self.tmp.name) / "t.sqlite")

    def tearDown(self):
        self.conn.close()
        self.tmp.cleanup()

    def test_record_visit_then_count(self):
        ok = record_event(
            self.conn,
            {"event": "visit", "utm_source": "x", "utm_content": "p004"},
        )
        self.assertTrue(ok)
        n = self.conn.execute("SELECT COUNT(*) FROM track_events").fetchone()[0]
        self.assertEqual(n, 1)
        row = self.conn.execute(
            "SELECT event, utm_source, utm_content, code FROM track_events"
        ).fetchone()
        self.assertEqual(tuple(row), ("visit", "x", "p004", None))

    def test_refuse_pii_payload(self):
        ok = record_event(self.conn, {"event": "visit", "contact": "hi@x.com"})
        self.assertTrue(ok)
        stored = dict(self.conn.execute("SELECT * FROM track_events").fetchone())
        self.assertNotIn("hi@x.com", str(stored))
