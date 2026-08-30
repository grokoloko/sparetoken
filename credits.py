"""Paid session credit accounting. Time is consumed only while a session is active."""

from __future__ import annotations

HOURS_5 = 5 * 3600  # 18_000


def remaining_seconds(purchased: int, consumed: int) -> int:
    return max(0, int(purchased) - int(consumed))


def consume(purchased: int, consumed: int, elapsed: int) -> tuple[int, int]:
    """Apply elapsed active seconds. Returns (new_consumed, remaining)."""
    elapsed = max(0, int(elapsed))
    room = remaining_seconds(purchased, consumed)
    applied = min(elapsed, room)
    new_consumed = int(consumed) + applied
    return new_consumed, remaining_seconds(purchased, new_consumed)


def settle_active(
    purchased: int,
    consumed: int,
    started_at: float,
    now: float,
) -> tuple[int, int]:
    """Settle an active timer up to now. Disconnect/pause uses this, then stops."""
    elapsed = max(0, int(now - started_at))
    return consume(purchased, consumed, elapsed)


def can_use(purchased: int, consumed: int) -> bool:
    return remaining_seconds(purchased, consumed) > 0


def format_hms(seconds: int) -> str:
    seconds = max(0, int(seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"
