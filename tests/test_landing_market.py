"""Tonight's heartbeat: marketplace signal is on the official landing."""

from __future__ import annotations

import unittest
from pathlib import Path

HTML = (Path(__file__).resolve().parents[1] / "static" / "index.html").read_text(encoding="utf-8")


class LandingMarketTest(unittest.TestCase):
    def test_brand_is_spare_tokens(self):
        self.assertIn("<title>spare tokens", HTML.lower())
        self.assertIn(">spare tokens<", HTML.lower())

    def test_nav_leads_with_marketplace(self):
        nav = HTML.split("<nav", 1)[1].split("</nav>", 1)[0]
        self.assertLess(nav.find("#mercado"), nav.find("#preco"))
        self.assertIn("#mercado", nav)
        self.assertIn("#terminal", nav)

    def test_reseller_alias_fuzzy(self):
        self.assertIn("reseller alias", HTML.lower())
        self.assertIn("fuzzy", HTML)

    def test_market_section_invites(self):
        self.assertIn('id="mercado"', HTML)
        self.assertIn("?code=", HTML)
        self.assertIn("10 links", HTML)
        self.assertIn("23:30", HTML)
