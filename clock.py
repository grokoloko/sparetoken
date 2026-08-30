"""Paid-block clock. Time moves only while the model is processing."""

from __future__ import annotations

import secrets
import sqlite3

import credits
from db import (
    add_chat_processed,
    chats_for_wallet,
    close_usage_slice,
    current_ai_session,
    current_open_slice,
    insert_ai_session,
    insert_usage_slice,
    latest_block_code,
    next_chat_label,
    set_ai_session,
    set_chat_label,
    set_wallet_consumed,
    touch_ai_session,
    wallet,
    wallet_chat,
)

WARN_SECONDS = 5 * 60
SITE = "https://wdtsot.shop"


class ClockError(ValueError):
    pass


def _now_pair(now: float | None) -> float:
    from db import now as db_now

    return float(now if now is not None else db_now())


def _live_open(conn: sqlite3.Connection, session_id: str, ts: float) -> int:
    row = current_open_slice(conn, session_id)
    if not row:
        return 0
    return max(0, int(ts - float(row["started_at"])))


def _ensure_chat(
    conn: sqlite3.Connection,
    session_id: str,
    channel: str,
    label: str | None,
    ts: float,
    chat_id: str | None = None,
) -> sqlite3.Row:
    if chat_id:
        existing = conn.execute("SELECT * FROM ai_sessions WHERE id = ?", (chat_id,)).fetchone()
        if existing:
            return existing
        return insert_ai_session(
            conn, chat_id, session_id, ts, status="idle", channel=channel, label=label
        )
    row = current_ai_session(conn, session_id)
    if row and str(row["channel"] or "web") == channel:
        return row
    return insert_ai_session(
        conn,
        secrets.token_urlsafe(12),
        session_id,
        ts,
        status="idle",
        channel=channel,
        label=label or channel,
    )


def snapshot(conn: sqlite3.Connection, session_id: str, now: float | None = None) -> dict:
    ts = _now_pair(now)
    w = wallet(conn, session_id)
    purchased = int(w["purchased_seconds"])
    consumed = int(w["consumed_seconds"]) + _live_open(conn, session_id, ts)
    remaining = credits.remaining_seconds(purchased, consumed)
    used = max(0, purchased - remaining)
    row = current_ai_session(conn, session_id)
    open_slice = current_open_slice(conn, session_id)
    status = "processing" if open_slice else "idle"
    exhausted = purchased > 0 and remaining <= 0
    code = latest_block_code(conn, session_id)
    chats = []
    for chat in chats_for_wallet(conn, session_id):
        extra = 0
        if open_slice and open_slice["chat_id"] == chat["id"]:
            extra = _live_open(conn, session_id, ts)
        used_chat = int(chat["processed_seconds"] or 0) + extra
        chats.append(
            {
                "id": chat["id"],
                "channel": chat["channel"] or "web",
                "label": chat["label"] or chat["channel"] or "web",
                "used_seconds": used_chat,
                "used_clock": credits.format_hms(used_chat),
                "processing": bool(extra),
            }
        )
    return {
        "purchased_seconds": purchased,
        "used_seconds": used,
        "remaining_seconds": remaining,
        "remaining_clock": credits.format_hms(remaining),
        "used_clock": credits.format_hms(used),
        "paid": remaining > 0,
        "exhausted": exhausted,
        "session_status": status if purchased else "none",
        "warn": 0 < remaining <= WARN_SECONDS,
        "block_code": code,
        "return_url": f"{SITE}/?code={code}" if code else SITE,
        "chats": chats,
        "processing": bool(open_slice),
        "active_chat_id": str(row["id"]) if row else None,
    }


def start_processing(
    conn: sqlite3.Connection,
    session_id: str,
    now: float | None = None,
    *,
    channel: str = "web",
    label: str | None = None,
    chat_id: str | None = None,
) -> dict:
    ts = _now_pair(now)
    snap = snapshot(conn, session_id, ts)
    if snap["purchased_seconds"] <= 0:
        raise ClockError("ainda não há bloco pago nesta sessão")
    if snap["remaining_seconds"] <= 0:
        raise ClockError("as 5h deste bloco acabaram. pague R$5 para outro.")
    if current_open_slice(conn, session_id):
        return snapshot(conn, session_id, ts)
    chat = _ensure_chat(conn, session_id, channel, label, ts, chat_id)
    set_ai_session(conn, chat["id"], status="processing", started_at=ts, paused_at=None)
    insert_usage_slice(
        conn, secrets.token_urlsafe(12), session_id, str(chat["id"]), channel, ts
    )
    return snapshot(conn, session_id, ts)


def end_processing(
    conn: sqlite3.Connection,
    session_id: str,
    now: float | None = None,
) -> dict:
    ts = _now_pair(now)
    row = current_open_slice(conn, session_id)
    if not row:
        return snapshot(conn, session_id, ts)
    elapsed = max(0, int(ts - float(row["started_at"])))
    w = wallet(conn, session_id)
    purchased = int(w["purchased_seconds"])
    already = int(w["consumed_seconds"])
    applied = min(elapsed, credits.remaining_seconds(purchased, already))
    close_usage_slice(conn, row["id"], ts, applied)
    add_chat_processed(conn, str(row["chat_id"]), applied)
    set_wallet_consumed(conn, session_id, already + applied)
    set_ai_session(conn, str(row["chat_id"]), status="idle", paused_at=ts)
    return snapshot(conn, session_id, ts)


def open_chat(
    conn: sqlite3.Connection,
    session_id: str,
    *,
    channel: str = "web",
    label: str | None = None,
    chat_id: str | None = None,
    now: float | None = None,
) -> dict:
    ts = _now_pair(now)
    snap = snapshot(conn, session_id, ts)
    if snap["remaining_seconds"] <= 0:
        raise ClockError("as 5h deste bloco acabaram. pague R$5 para outro.")
    _ensure_chat(conn, session_id, channel, label, ts, chat_id)
    return snapshot(conn, session_id, ts)


def ensure_can_chat(conn: sqlite3.Connection, session_id: str, now: float | None = None) -> dict:
    ts = _now_pair(now)
    snap = snapshot(conn, session_id, ts)
    if snap["remaining_seconds"] <= 0 and snap["purchased_seconds"] > 0:
        raise ClockError("as 5h deste bloco acabaram. pague R$5 para outro.")
    return snap


def resume(conn: sqlite3.Connection, session_id: str, now: float | None = None) -> dict:
    """Compatibility: does not start a wall-clock. Use start_processing for AI time."""
    return snapshot(conn, session_id, now)


def pause(conn: sqlite3.Connection, session_id: str, now: float | None = None) -> dict:
    return end_processing(conn, session_id, now)


def start_another(conn: sqlite3.Connection, session_id: str, now: float | None = None) -> dict:
    ts = _now_pair(now)
    snap = snapshot(conn, session_id, ts)
    if snap["remaining_seconds"] <= 0:
        raise ClockError("as 5h deste bloco acabaram. pague R$5 para outro.")
    end_processing(conn, session_id, ts)
    label = next_chat_label(conn, session_id)
    insert_ai_session(
        conn,
        secrets.token_urlsafe(12),
        session_id,
        ts,
        status="idle",
        channel="web",
        label=label,
    )
    return snapshot(conn, session_id, ts)


def rename_chat(
    conn: sqlite3.Connection,
    session_id: str,
    chat_id: str,
    label: str,
    now: float | None = None,
) -> dict:
    ts = _now_pair(now)
    row = wallet_chat(conn, session_id, chat_id)
    if not row:
        raise ClockError("esse chat não é deste código")
    title = " ".join((label or "").split())[:80]
    if not title:
        raise ClockError("escreva um nome")
    set_chat_label(conn, chat_id, title)
    return snapshot(conn, session_id, ts)


def use_chat(
    conn: sqlite3.Connection,
    session_id: str,
    chat_id: str,
    now: float | None = None,
) -> dict:
    """Switch the time bucket. Does not restore messages."""
    ts = _now_pair(now)
    snap = snapshot(conn, session_id, ts)
    if snap["remaining_seconds"] <= 0:
        raise ClockError("as 5h deste bloco acabaram. pague R$5 para outro.")
    row = wallet_chat(conn, session_id, chat_id)
    if not row:
        raise ClockError("esse chat não é deste código")
    end_processing(conn, session_id, ts)
    touch_ai_session(conn, chat_id, ts)
    return snapshot(conn, session_id, ts)
