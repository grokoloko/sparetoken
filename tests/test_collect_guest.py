"""SSH guest gate: only the block code / resume token. No name, phone, email."""

from __future__ import annotations

import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from collect_guest import build_payload  # noqa: E402


SRC = (Path(__file__).resolve().parents[1] / "scripts" / "collect_guest.py").read_text(
    encoding="utf-8"
)
GATE = (Path(__file__).resolve().parents[1] / "tunnel-gate.py").read_text(encoding="utf-8")
AGENT = (Path(__file__).resolve().parents[1] / "run-agent.sh").read_text(encoding="utf-8")


class CollectGuestTest(unittest.TestCase):
    def test_block_code_is_the_only_identity(self):
        self.assertEqual(build_payload("wdtsot-7K2M"), {"block_code": "wdtsot-7K2M"})
        self.assertEqual(build_payload("7K2M"), {"block_code": "wdtsot-7K2M"})

    def test_resume_token_still_works(self):
        token = "session-20260830-185012-06be14"
        self.assertEqual(build_payload(token), {"resume": token})

    def test_empty_means_new_pix_not_a_name(self):
        self.assertEqual(build_payload(""), {})
        self.assertEqual(build_payload("   "), {})

    def test_payload_never_carries_pii_keys(self):
        payload = build_payload("wdtsot-7K2M")
        self.assertNotIn("name", payload)
        self.assertNotIn("whatsapp", payload)
        self.assertNotIn("email", payload)

    def test_source_does_not_prompt_for_civil_identity(self):
        blob = SRC.lower()
        self.assertNotIn('ask("nome', blob)
        self.assertNotIn("whatsapp (com ddd)", blob)
        self.assertNotIn('ask("email', blob)


class SshSurfaceTest(unittest.TestCase):
    def test_gate_ready_copy_is_code_only(self):
        self.assertNotIn("WhatsApp + código", GATE)
        self.assertIn("código do bloco", GATE.lower())

    def test_agent_does_not_append_phone_or_email_to_guests_log(self):
        self.assertNotIn('"whatsapp": guest.get("whatsapp"', AGENT)
        self.assertNotIn('"email": guest.get("email"', AGENT)
