"""Landing e README públicos não doxxam operador nem tratam a loja como propriedade."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = (ROOT / "static" / "index.html", ROOT / "README.md")
HANDLES = ("frankrolim", "conecteai", "conecte.ai", "frankmendes")
OWNERSHIP = re.compile(r"\bowners?\b|\bthe owner\b|\bo dono\b", re.I)


class PublicAnonymityTest(unittest.TestCase):
    def test_public_copy_has_no_operator_handles(self):
        hits: list[str] = []
        for path in PUBLIC:
            text = path.read_text(encoding="utf-8", errors="ignore")
            low = text.lower()
            for word in HANDLES:
                if word in low:
                    hits.append(f"{path.name}: {word}")
        self.assertEqual(hits, [], msg="handle no copy público:\n" + "\n".join(hits))

    def test_landing_does_not_claim_an_owner(self):
        html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
        self.assertIsNone(OWNERSHIP.search(html), "landing não usa owner/dono")
