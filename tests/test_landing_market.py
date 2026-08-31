"""Marketplace shelf: R$5 cards, reseller names — never 'alias' on the public box."""

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

    def test_public_copy_never_says_reseller_alias(self):
        self.assertNotIn("reseller alias", HTML.lower())
        self.assertNotIn("alias:", HTML.lower())

    def test_shelf_is_marketplace_cards(self):
        self.assertIn('id="mercado"', HTML)
        self.assertIn('class="shelf"', HTML)
        self.assertIn("shelf-card", HTML)
        self.assertIn('data-reseller="fuzzy"', HTML)
        self.assertIn("reseller", HTML.lower())
        self.assertIn("fuzzy", HTML)

    def test_market_section_invites(self):
        self.assertIn("?code=", HTML)
        self.assertIn("10 links", HTML)
        self.assertIn("23:30", HTML)
