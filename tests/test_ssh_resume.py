import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from ssh_resume import (
    RESUME_RECONNECT,
    heaviest_ssh_line,
    parse_resume_answer,
    prior_ssh_lines,
    resume_token,
    ssh_resume_cmd,
)


class SshResumeTest(unittest.TestCase):
    def test_token_strips_ssh_prefix(self):
        self.assertEqual(resume_token("ssh-session-20260830-185012-06be14"), "session-20260830-185012-06be14")
        self.assertEqual(resume_token("session-20260830-185012-06be14"), "session-20260830-185012-06be14")

    def test_resume_cmd(self):
        self.assertEqual(
            ssh_resume_cmd("ssh-session-20260830-185012-06be14"),
            "ssh -t agent-guest@wdtsot.shop resume session-20260830-185012-06be14",
        )
        self.assertEqual(ssh_resume_cmd(""), "")

    def test_prior_skips_current_and_web(self):
        chats = [
            {"id": "ssh-session-now", "channel": "ssh", "used_seconds": 10},
            {"id": "web-1", "channel": "web", "used_seconds": 99},
            {"id": "ssh-session-old", "channel": "ssh", "used_seconds": 7000},
            {"id": "ssh-session-mid", "channel": "ssh", "used_seconds": 40},
        ]
        prior = prior_ssh_lines(chats, "session-now")
        self.assertEqual([c["id"] for c in prior], ["ssh-session-old", "ssh-session-mid"])

    def test_yes_picks_heaviest(self):
        lines = [
            {"id": "ssh-session-short", "used_seconds": 80},
            {"id": "ssh-session-long", "used_seconds": 7132},
        ]
        self.assertEqual(heaviest_ssh_line(lines)["id"], "ssh-session-long")
        self.assertEqual(parse_resume_answer("s", lines)["id"], "ssh-session-long")
        self.assertEqual(parse_resume_answer("2", lines)["id"], "ssh-session-long")
        self.assertEqual(parse_resume_answer("session-short", lines)["id"], "ssh-session-short")
        self.assertIsNone(parse_resume_answer("n", lines))
        self.assertIsNone(parse_resume_answer("", lines))

    def test_reconnect_exit_code(self):
        self.assertEqual(RESUME_RECONNECT, 10)


if __name__ == "__main__":
    unittest.main()
