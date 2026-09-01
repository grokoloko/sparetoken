"""Marketplace shelf: one R$5 card, a how-it-works rail — never 'alias'."""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
CSS = (ROOT / "static" / "styles.css").read_text(encoding="utf-8")
JS = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
SERVER = (ROOT / "server.py").read_text(encoding="utf-8")


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

    def test_shelf_is_one_buy_card_not_a_dashed_twin(self):
        self.assertIn('id="mercado"', HTML)
        self.assertIn('class="shelf"', HTML)
        self.assertIn("shelf-card", HTML)
        self.assertIn('data-reseller="fuzzy"', HTML)
        self.assertIn("fuzzy", HTML)
        self.assertNotIn("shelf-card-open", HTML)
        self.assertNotIn("seu nome de reseller", HTML.lower())

    def test_shelf_rail_explains_without_a_second_sku(self):
        self.assertIn("shelf-rail", HTML)
        self.assertIn("wdtsot-", HTML)
        self.assertIn("?code=", HTML)

    def test_experiment_is_market_and_self_evolving_agent(self):
        blob = HTML.lower()
        self.assertIn("self-evolving", blob)
        self.assertIn("marketplace", blob)

    def test_market_section_invites(self):
        self.assertIn("10 links", HTML)
        self.assertIn("23:30", HTML)

    def test_design_tokens_file_exists(self):
        tokens = Path(__file__).resolve().parents[1] / "static" / "tokens.css"
        self.assertTrue(tokens.is_file())
        self.assertIn("--paper", tokens.read_text(encoding="utf-8"))
        self.assertIn("tokens.css", CSS)

    def test_outbound_shop_links_keep_utm_hooks(self):
        self.assertIn("utm_source", HTML)
        self.assertIn("data-track", HTML)

    def test_claim_is_code_only_not_civil_identity(self):
        self.assertNotIn("claim-contact", HTML)
        self.assertNotIn("whatsapp", HTML.lower())
        self.assertNotIn("e-mail ou", HTML.lower())

    def test_hero_rotates_three_lines(self):
        self.assertIn("we deserve to share our tokens", HTML.lower())
        self.assertIn("r$0,50 por 30 minutos", HTML.lower())
        self.assertIn("pay quickly with pix and get going", HTML.lower())
        self.assertIn("hero-line", HTML)

    def test_three_short_agents_open_the_same_chat(self):
        self.assertIn('data-brief="mkt"', HTML)
        self.assertIn('data-brief="copy"', HTML)
        self.assertIn('data-brief="viral"', HTML)
        self.assertIn("is-live", HTML)
        self.assertIn("const BRIEFS", JS)
        self.assertNotIn("R$10", HTML)
        self.assertEqual(HTML.count('id="pay"'), 1)

    def test_click_tally_is_public_counts_only(self):
        self.assertIn('id="pulso-tally"', HTML)
        self.assertIn("/api/track/summary", JS)
        self.assertIn("/api/track/summary", SERVER)
        self.assertIn("track.summarize", SERVER)

    def test_faq_is_machine_citable_without_a_second_sku(self):
        self.assertIn("application/ld+json", HTML)
        self.assertIn("FAQPage", HTML)
        self.assertIn('id="faq"', HTML)
        faq = HTML.split('id="faq"', 1)[1].lower()
        self.assertIn("r$5", faq)
        self.assertNotIn("plano mensal", faq)
        self.assertNotIn("reseller alias", faq)
