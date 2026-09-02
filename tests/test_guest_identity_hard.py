"""Guest tunnel identity-hard contract (prompt-attack / operator PII)."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class GuestIdentityHardTest(unittest.TestCase):
    def test_guest_agents_has_hard_block(self):
        text = (ROOT / "tunnel" / "guest-AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("IDENTITY-HARD", text)
        self.assertIn("dry refusal", text)
        self.assertIn("Never reveal", text)
        self.assertNotRegex(text, r"(?i)if you insist|as a last resort")

    def test_run_agent_wires_harden(self):
        sh = (ROOT / "run-agent.sh").read_text(encoding="utf-8")
        self.assertIn("guest_identity_harden.py", sh)
        self.assertIn("GIT_AUTHOR_NAME", sh)
        self.assertIn("agent-guest", sh)

    def test_harden_script_writes_guest_git_and_agents(self):
        script = ROOT / "scripts" / "guest_identity_harden.py"
        src = ROOT / "tunnel" / "guest-AGENTS.md"
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp) / "workspace"
            out = subprocess.check_output(
                ["python3", str(script), str(ws), str(src)],
                text=True,
            )
            data = json.loads(out)
            self.assertTrue(data["ok"])
            agents = (ws / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("IDENTITY-HARD", agents)
            rule = ws / ".cursor" / "rules" / "identity-hard.mdc"
            self.assertTrue(rule.is_file())
            name = subprocess.check_output(
                ["git", "config", "user.name"], cwd=str(ws), text=True
            ).strip()
            email = subprocess.check_output(
                ["git", "config", "user.email"], cwd=str(ws), text=True
            ).strip()
            self.assertEqual(name, "sparetoken-guest")
            self.assertEqual(email, "guest@sparetoken.local")

    def test_validate_script_passes(self):
        rc = subprocess.call(
            ["python3", str(ROOT / "scripts" / "validate_guest_privacy.py")],
        )
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
