"""First-party click / land events. No email, no phone, no third-party pixel."""

from __future__ import annotations

import re
import time
from typing import Any

ALLOWED_EVENTS = frozenset({"visit", "pay_click", "claim_ok"})
_UTM = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
_CODE = re.compile(r"^wdtsot-[A-Za-z0-9]{3,16}$")
_UTM_KEYS = ("utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term")


def sanitize_payload(raw: dict[str, Any] | None) -> dict[str, str] | None:
    if not isinstance(raw, dict):
        return None
    event = str(raw.get("event") or "").strip().lower()
    if event not in ALLOWED_EVENTS:
        return None
    out: dict[str, str] = {"event": event}
    for key in _UTM_KEYS:
        val = str(raw.get(key) or "").strip()[:64]
        if val and _UTM.match(val):
            out[key] = val
    code = str(raw.get("code") or "").strip()
    if _CODE.match(code):
        out["code"] = code
    return out


def record_event(conn, raw: dict[str, Any] | None) -> bool:
    clean = sanitize_payload(raw)
    if not clean:
        return False
    conn.execute(
        """
        INSERT INTO track_events (
            event, utm_source, utm_medium, utm_campaign, utm_content, utm_term, code, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            clean["event"],
            clean.get("utm_source"),
            clean.get("utm_medium"),
            clean.get("utm_campaign"),
            clean.get("utm_content"),
            clean.get("utm_term"),
            clean.get("code"),
            time.time(),
        ),
    )
    conn.commit()
    return True


def summarize(conn) -> dict[str, int]:
    """Public click tallies. Counts only — no codes, no UTM, no PII."""
    out = {event: 0 for event in ("visit", "pay_click", "claim_ok")}
    for event, n in conn.execute("SELECT event, COUNT(*) FROM track_events GROUP BY 1"):
        if event in out:
            out[event] = int(n)
    return out
