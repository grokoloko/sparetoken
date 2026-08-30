import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db import (
    append_chat_turn,
    connect,
    get_or_create_session,
    list_chat_turns,
    refund_free_message,
    try_consume_free_message,
)


class SessionDbTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.conn = connect(Path(self.tmp.name) / "t.sqlite")

    def tearDown(self):
        self.conn.close()
        self.tmp.cleanup()

    def test_anonymous_session_and_fifty_prompts(self):
        row = get_or_create_session(self.conn, "token-abc-1234567890", "sid1")
        self.assertEqual(row["free_messages_limit"], 50)
        self.assertEqual(row["free_messages_used"], 0)
        for i in range(50):
            ok, used, limit = try_consume_free_message(self.conn, row["id"])
            self.assertTrue(ok)
            self.assertEqual(used, i + 1)
            self.assertEqual(limit, 50)
        ok, used, limit = try_consume_free_message(self.conn, row["id"])
        self.assertFalse(ok)
        self.assertEqual(used, 50)

    def test_same_token_resumes_same_session(self):
        a = get_or_create_session(self.conn, "same-token-abcdefghij", "sid-a")
        b = get_or_create_session(self.conn, "same-token-abcdefghij", "sid-other")
        self.assertEqual(a["id"], b["id"])

    def test_refund_restores_a_message(self):
        row = get_or_create_session(self.conn, "token-refund-1234567", "sid-r")
        try_consume_free_message(self.conn, row["id"])
        remaining = refund_free_message(self.conn, row["id"])
        self.assertEqual(remaining, 50)

    def test_chat_turns_persist_per_line(self):
        append_chat_turn(self.conn, "chat-a", "user", "oi")
        append_chat_turn(self.conn, "chat-a", "assistant", "olá")
        append_chat_turn(self.conn, "chat-b", "user", "outro")
        a = list_chat_turns(self.conn, "chat-a")
        b = list_chat_turns(self.conn, "chat-b")
        self.assertEqual([(t["role"], t["body"]) for t in a], [("user", "oi"), ("assistant", "olá")])
        self.assertEqual([t["body"] for t in b], ["outro"])


if __name__ == "__main__":
    unittest.main()
