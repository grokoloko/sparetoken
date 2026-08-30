import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from chat import iter_assistant_deltas


def ev(*lines: str):
    return [json.loads(x) for x in lines]


class StreamParseTest(unittest.TestCase):
    def test_ignores_user_system_thinking_and_duplicates(self):
        events = ev(
            '{"type":"system","subtype":"init","apiKeySource":"login"}',
            '{"type":"user","message":{"role":"user","content":[{"type":"text","text":"SECRET PROMPT"}]}}',
            '{"type":"thinking","subtype":"delta","text":"thinking out loud"}',
            '{"type":"assistant","message":{"role":"assistant","content":[{"type":"text","text":"wdtsot."}]}}',
            '{"type":"assistant","message":{"role":"assistant","content":[{"type":"text","text":"wdtsot."}]}}',
            '{"type":"result","subtype":"success","result":"wdtsot."}',
        )
        text = "".join(iter_assistant_deltas(events))
        self.assertEqual(text, "wdtsot.")
        self.assertNotIn("SECRET", text)
        self.assertNotIn("login", text)
        self.assertNotIn("thinking", text)

    def test_incremental_then_full(self):
        events = ev(
            '{"type":"assistant","message":{"content":[{"type":"text","text":"wd"}]}}',
            '{"type":"assistant","message":{"content":[{"type":"text","text":"wdtsot."}]}}',
        )
        self.assertEqual("".join(iter_assistant_deltas(events)), "wdtsot.")


if __name__ == "__main__":
    unittest.main()
