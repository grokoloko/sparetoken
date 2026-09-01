"""The living repo must land on GitHub as sparetoken-shop after every correction."""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CI = (ROOT / ".github" / "workflows" / "test.yml").read_text(encoding="utf-8")
HELPER = ROOT / "ceo" / "launch" / "git-as-sparetoken.sh"
RULE = ROOT / ".cursor" / "rules" / "github-vivo.mdc"
AGENTS = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
HB_PROMPT = (ROOT / "ceo" / "launch" / "prompts" / "heartbeat.txt").read_text(encoding="utf-8")
SELL_PROMPT = (ROOT / "ceo" / "launch" / "prompts" / "sell.txt").read_text(encoding="utf-8")
JS = (ROOT / "static" / "app.js").read_text(encoding="utf-8")


class GitHubAliveTest(unittest.TestCase):
    def test_ci_runs_on_every_push_not_just_main(self):
        self.assertNotIn("branches: [main]", CI)
        self.assertIn("unittest", CI)
        self.assertIn("python3 -m unittest discover -s tests -v", CI)

    def test_ci_rejects_personal_git_author(self):
        self.assertIn("sparetoken-shop@users.noreply.github.com", CI)
        self.assertIn("github.event_name == 'push'", CI)

    def test_publish_helper_uses_shop_identity_and_deploy_key(self):
        self.assertTrue(HELPER.is_file(), "ceo/launch/git-as-sparetoken.sh missing")
        text = HELPER.read_text(encoding="utf-8")
        self.assertIn("sparetoken-shop@users.noreply.github.com", text)
        self.assertIn("GIT_SSH_COMMAND", text)
        self.assertIn("sparetoken_shop_ed25519", text)
        self.assertIn("git push", text)
        self.assertNotIn("frankrolim", text)
        self.assertNotIn("gh auth", text)

    def test_pulse_prompts_require_commit_and_push(self):
        for name, text in (("heartbeat", HB_PROMPT), ("sell", SELL_PROMPT)):
            with self.subTest(pulse=name):
                self.assertIn("git-as-sparetoken.sh", text)
                self.assertIn("dirty", text.lower())
                self.assertIn("push", text.lower())

    def test_correction_session_rule_is_absolute(self):
        self.assertTrue(RULE.is_file(), ".cursor/rules/github-vivo.mdc missing")
        text = RULE.read_text(encoding="utf-8")
        self.assertIn("alwaysApply: true", text)
        self.assertIn("github.com/sparetoken-shop/sparetoken", text)
        self.assertIn("git-as-sparetoken.sh", text)
        self.assertNotIn("só local", text)

    def test_agents_md_says_correction_goes_to_github(self):
        blob = AGENTS.lower()
        self.assertIn("github-vivo", blob)
        self.assertIn("sparetoken-shop", blob)

    def test_hero_js_still_rotates_three_lines(self):
        self.assertIn("function rotateHero", JS)
        self.assertIn("prefers-reduced-motion", JS)
        self.assertIn("hero-line-text", JS)
