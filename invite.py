"""Invite link = the same wallet code. No email. No second checkout."""

from __future__ import annotations

import re

SHOP = "https://sparetoken.shop"
_CODE = re.compile(r"^wdtsot-[A-Za-z0-9]{3,16}$")


def normalize_code(raw: str | None) -> str | None:
    code = (raw or "").strip()
    if not _CODE.match(code):
        return None
    return code


def invite_url(code: str | None) -> str | None:
    """The invite is /?code=WALLET. Same string as login. Nothing else."""
    clean = normalize_code(code)
    if not clean:
        return None
    return f"{SHOP}/?code={clean}"
