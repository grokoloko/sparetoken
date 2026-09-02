"""The invite link is the same wallet code. No email. No second checkout."""

from __future__ import annotations

import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from invite import SHOP, invite_url

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
JS = (ROOT / "static" / "app.js").read_text(encoding="utf-8")


class InviteUrlTest(unittest.TestCase):
    def test_same_code_is_the_invite(self):
        url = invite_url("wdtsot-7K2M")
        self.assertEqual(url, f"{SHOP}/?code=wdtsot-7K2M")
        self.assertIn("wdtsot-7K2M", url)

    def test_strips_spaces_keeps_the_wallet(self):
        self.assertEqual(invite_url("  wdtsot-XVCD  "), f"{SHOP}/?code=wdtsot-XVCD")

    def test_garbage_email_and_pix_url_are_not_invites(self):
        self.assertIsNone(invite_url(""))
        self.assertIsNone(invite_url("amigo@mail.com"))
        self.assertIsNone(invite_url("https://app.conta.vc/pay/fuzzy/c/xxxx"))
        self.assertIsNone(invite_url("DROP TABLE"))

    def test_url_never_grows_a_second_sku_or_contact(self):
        url = invite_url("wdtsot-7K2M")
        self.assertNotIn("email", url)
        self.assertNotIn("whatsapp", url)
        self.assertNotIn("amount", url)
        self.assertNotIn("fuzzy", url)
        self.assertTrue(url.startswith("https://sparetoken.shop/?code="))


class InviteSurfaceTest(unittest.TestCase):
    def test_landing_has_manda_este_link_slot(self):
        self.assertIn('id="invite-wrap"', HTML)
        self.assertIn("manda este link", HTML.lower())
        self.assertIn('id="invite-url"', HTML)
        self.assertIn('id="invite-copy"', HTML)

    def test_js_builds_the_same_shop_code_url(self):
        self.assertIn("https://sparetoken.shop/?code=", JS)
        self.assertIn("invite_url", JS)

    def test_faq_says_invite_is_the_block_code(self):
        blob = HTML.lower()
        self.assertIn("como indico", blob)
        self.assertIn("?code=", blob)
        self.assertNotIn("whatsapp", blob)
