"""Landing e README públicos não doxxam operador nem tratam a loja como propriedade."""

from __future__ import annotations

import hashlib
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = (ROOT / "static" / "index.html", ROOT / "README.md")
# sha256 of lowercase tokens that must never appear in public copy
HANDLE_HASHES = {
    "de6841936ca330c9a6e80947003cd2b147d4f7bbd104e3fcb63fc6653fc5a43d",
    "5bed5ac500b937b593ef863a50019f23ade8800cb3e206c3dad93c94ba4eb934",
    "4f655b6d700b103da8ddf1b3cf86c09fd0f354dad239f159faaf55765edea06c",
    "0f55bd5449be803ff864437f40887c250a9137ce2fd6f44735eb85f2f8d16b70",
}
OWNERSHIP = re.compile(r"\bowners?\b|\bthe owner\b|\bo dono\b", re.I)
TOKEN = re.compile(r"[a-z0-9][a-z0-9.\-_]{2,40}")


def _sha(word: str) -> str:
    return hashlib.sha256(word.encode()).hexdigest()


class PublicAnonymityTest(unittest.TestCase):
    def test_public_copy_has_no_operator_handles(self):
        hits: list[str] = []
        for path in PUBLIC:
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
            for token in set(TOKEN.findall(text)):
                if _sha(token) in HANDLE_HASHES:
                    hits.append(path.name)
        self.assertEqual(hits, [], msg="token pessoal no copy público")

    def test_landing_does_not_claim_an_owner(self):
        html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
        self.assertIsNone(OWNERSHIP.search(html), "landing não usa owner/dono")
