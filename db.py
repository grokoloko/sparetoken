"""SQLite persistence for anonymous sessions and credit wallets."""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path

FREE_MESSAGE_LIMIT = 50
SCHEMA = """
CREATE TABLE IF NOT EXISTS user_sessions (
    id TEXT PRIMARY KEY,
    public_token TEXT UNIQUE NOT NULL,
    created_at REAL NOT NULL,
    last_seen_at REAL NOT NULL,
    free_messages_used INTEGER NOT NULL DEFAULT 0,
    free_messages_limit INTEGER NOT NULL DEFAULT 50,
    display_name TEXT
);

CREATE TABLE IF NOT EXISTS credit_wallets (
    session_id TEXT PRIMARY KEY,
    purchased_seconds INTEGER NOT NULL DEFAULT 0,
    consumed_seconds INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (session_id) REFERENCES user_sessions(id)
);

CREATE TABLE IF NOT EXISTS ai_sessions (
    id TEXT PRIMARY KEY,
    user_session_id TEXT NOT NULL,
    started_at REAL,
    paused_at REAL,
    status TEXT NOT NULL DEFAULT 'paused',
    channel TEXT NOT NULL DEFAULT 'web',
    label TEXT,
    processed_seconds INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (user_session_id) REFERENCES user_sessions(id)
);

CREATE TABLE IF NOT EXISTS usage_slices (
    id TEXT PRIMARY KEY,
    wallet_session_id TEXT NOT NULL,
    chat_id TEXT NOT NULL,
    channel TEXT NOT NULL,
    started_at REAL NOT NULL,
    ended_at REAL,
    seconds INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (wallet_session_id) REFERENCES user_sessions(id)
);

CREATE TABLE IF NOT EXISTS purchases (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    amount_brl REAL,
    seconds_purchased INTEGER,
    status TEXT NOT NULL,
    payment_reference TEXT,
    pay_url TEXT,
    created_at REAL NOT NULL,
    FOREIGN KEY (session_id) REFERENCES user_sessions(id)
);

CREATE TABLE IF NOT EXISTS pay_links (
    url TEXT PRIMARY KEY,
    charge_code TEXT,
    status TEXT NOT NULL DEFAULT 'idle',
    reserved_session_id TEXT,
    reserved_at REAL,
    created_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS turns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    created_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS chat_turns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id TEXT NOT NULL,
    role TEXT NOT NULL,
    body TEXT NOT NULL,
    created_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS identities (
    id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    value TEXT NOT NULL,
    session_id TEXT NOT NULL,
    created_at REAL NOT NULL,
    UNIQUE(kind, value),
    FOREIGN KEY (session_id) REFERENCES user_sessions(id)
);

CREATE TABLE IF NOT EXISTS customers (
    session_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at REAL NOT NULL,
    FOREIGN KEY (session_id) REFERENCES user_sessions(id)
);

CREATE INDEX IF NOT EXISTS idx_purchases_ref ON purchases(payment_reference);
CREATE INDEX IF NOT EXISTS idx_purchases_session ON purchases(session_id, status);
CREATE INDEX IF NOT EXISTS idx_identities_session ON identities(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_turns_chat ON chat_turns(chat_id, id);
"""


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(SCHEMA)
    purchase_cols = {row[1] for row in conn.execute("PRAGMA table_info(purchases)")}
    if "pay_url" not in purchase_cols:
        conn.execute("ALTER TABLE purchases ADD COLUMN pay_url TEXT")
    session_cols = {row[1] for row in conn.execute("PRAGMA table_info(user_sessions)")}
    if "display_name" not in session_cols:
        conn.execute("ALTER TABLE user_sessions ADD COLUMN display_name TEXT")
    ai_cols = {row[1] for row in conn.execute("PRAGMA table_info(ai_sessions)")}
    if "channel" not in ai_cols:
        conn.execute("ALTER TABLE ai_sessions ADD COLUMN channel TEXT NOT NULL DEFAULT 'web'")
    if "label" not in ai_cols:
        conn.execute("ALTER TABLE ai_sessions ADD COLUMN label TEXT")
    if "processed_seconds" not in ai_cols:
        conn.execute("ALTER TABLE ai_sessions ADD COLUMN processed_seconds INTEGER NOT NULL DEFAULT 0")
    conn.execute(
        """CREATE TABLE IF NOT EXISTS chat_turns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT NOT NULL,
            role TEXT NOT NULL,
            body TEXT NOT NULL,
            created_at REAL NOT NULL
        )"""
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_turns_chat ON chat_turns(chat_id, id)")
    conn.commit()
    return conn


def now() -> float:
    return time.time()


def get_or_create_session(conn: sqlite3.Connection, token: str, session_id: str) -> sqlite3.Row:
    row = conn.execute(
        "SELECT * FROM user_sessions WHERE public_token = ?", (token,)
    ).fetchone()
    if row:
        conn.execute(
            "UPDATE user_sessions SET last_seen_at = ? WHERE id = ?",
            (now(), row["id"]),
        )
        conn.commit()
        return conn.execute(
            "SELECT * FROM user_sessions WHERE id = ?", (row["id"],)
        ).fetchone()
    ts = now()
    conn.execute(
        """INSERT INTO user_sessions
           (id, public_token, created_at, last_seen_at, free_messages_used, free_messages_limit)
           VALUES (?, ?, ?, ?, 0, ?)""",
        (session_id, token, ts, ts, FREE_MESSAGE_LIMIT),
    )
    conn.execute(
        "INSERT INTO credit_wallets (session_id, purchased_seconds, consumed_seconds) VALUES (?, 0, 0)",
        (session_id,),
    )
    conn.commit()
    return conn.execute(
        "SELECT * FROM user_sessions WHERE id = ?", (session_id,)
    ).fetchone()


def wallet(conn: sqlite3.Connection, session_id: str) -> sqlite3.Row:
    row = conn.execute(
        "SELECT * FROM credit_wallets WHERE session_id = ?", (session_id,)
    ).fetchone()
    if row:
        return row
    conn.execute(
        "INSERT INTO credit_wallets (session_id, purchased_seconds, consumed_seconds) VALUES (?, 0, 0)",
        (session_id,),
    )
    conn.commit()
    return conn.execute(
        "SELECT * FROM credit_wallets WHERE session_id = ?", (session_id,)
    ).fetchone()


def try_consume_free_message(conn: sqlite3.Connection, session_id: str) -> tuple[bool, int, int]:
    row = conn.execute(
        "SELECT free_messages_used, free_messages_limit FROM user_sessions WHERE id = ?",
        (session_id,),
    ).fetchone()
    if not row:
        return False, 0, 0
    used, limit = int(row["free_messages_used"]), int(row["free_messages_limit"])
    if used >= limit:
        return False, used, limit
    conn.execute(
        "UPDATE user_sessions SET free_messages_used = free_messages_used + 1, last_seen_at = ? WHERE id = ?",
        (now(), session_id),
    )
    conn.execute(
        "INSERT INTO turns (session_id, role, created_at) VALUES (?, 'user', ?)",
        (session_id, now()),
    )
    conn.commit()
    return True, used + 1, limit


def refund_free_message(conn: sqlite3.Connection, session_id: str) -> int:
    conn.execute(
        """UPDATE user_sessions
           SET free_messages_used = MAX(free_messages_used - 1, 0)
           WHERE id = ?""",
        (session_id,),
    )
    conn.commit()
    row = conn.execute(
        "SELECT free_messages_used, free_messages_limit FROM user_sessions WHERE id = ?",
        (session_id,),
    ).fetchone()
    if not row:
        return 0
    return max(0, int(row["free_messages_limit"]) - int(row["free_messages_used"]))


def session_by_id(conn: sqlite3.Connection, session_id: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM user_sessions WHERE id = ?", (session_id,)
    ).fetchone()


def pending_purchase(conn: sqlite3.Connection, session_id: str) -> sqlite3.Row | None:
    return conn.execute(
        """SELECT * FROM purchases
           WHERE session_id = ? AND status = 'pending'
           ORDER BY created_at DESC LIMIT 1""",
        (session_id,),
    ).fetchone()


def purchase_by_reference(conn: sqlite3.Connection, reference: str) -> sqlite3.Row | None:
    if not reference:
        return None
    return conn.execute(
        "SELECT * FROM purchases WHERE payment_reference = ?", (reference,)
    ).fetchone()


def purchase_by_pay_url(conn: sqlite3.Connection, url: str) -> sqlite3.Row | None:
    if not url:
        return None
    return conn.execute(
        """SELECT * FROM purchases
           WHERE pay_url = ?
           ORDER BY created_at DESC LIMIT 1""",
        (url,),
    ).fetchone()


def listed_pay_links(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return list(conn.execute("SELECT * FROM pay_links ORDER BY created_at ASC"))


def insert_pending_purchase(
    conn: sqlite3.Connection,
    purchase_id: str,
    session_id: str,
    amount_brl: float,
    seconds_purchased: int,
    payment_reference: str,
    pay_url: str | None = None,
) -> sqlite3.Row:
    conn.execute(
        """INSERT INTO purchases
           (id, session_id, amount_brl, seconds_purchased, status, payment_reference, pay_url, created_at)
           VALUES (?, ?, ?, ?, 'pending', ?, ?, ?)""",
        (purchase_id, session_id, amount_brl, seconds_purchased, payment_reference, pay_url, now()),
    )
    conn.commit()
    row = purchase_by_reference(conn, payment_reference)
    assert row is not None
    return row


def upsert_pay_link(conn: sqlite3.Connection, url: str) -> None:
    conn.execute(
        """INSERT INTO pay_links (url, status, created_at)
           VALUES (?, 'idle', ?)
           ON CONFLICT(url) DO NOTHING""",
        (url, now()),
    )
    conn.commit()


def idle_pay_links(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return list(
        conn.execute(
            """SELECT * FROM pay_links
               WHERE status = 'idle'
               ORDER BY created_at ASC"""
        )
    )


def reserve_pay_link(conn: sqlite3.Connection, url: str, session_id: str) -> None:
    conn.execute(
        """UPDATE pay_links
           SET status = 'reserved', reserved_session_id = ?, reserved_at = ?
           WHERE url = ? AND status = 'idle'""",
        (session_id, now(), url),
    )
    conn.commit()


def consume_pay_link(conn: sqlite3.Connection, url: str) -> None:
    conn.execute(
        "UPDATE pay_links SET status = 'consumed' WHERE url = ?",
        (url,),
    )
    conn.commit()


def mark_pay_link(conn: sqlite3.Connection, url: str, status: str) -> None:
    conn.execute("UPDATE pay_links SET status = ? WHERE url = ?", (status, url))
    conn.commit()


def mark_purchase_paid(conn: sqlite3.Connection, purchase_id: str) -> sqlite3.Row | None:
    row = conn.execute("SELECT * FROM purchases WHERE id = ?", (purchase_id,)).fetchone()
    if not row or row["status"] == "paid":
        return row
    conn.execute(
        "UPDATE purchases SET status = 'paid' WHERE id = ? AND status = 'pending'",
        (purchase_id,),
    )
    conn.commit()
    return conn.execute("SELECT * FROM purchases WHERE id = ?", (purchase_id,)).fetchone()


def credit_wallet(conn: sqlite3.Connection, session_id: str, seconds: int) -> sqlite3.Row:
    wallet(conn, session_id)
    conn.execute(
        """UPDATE credit_wallets
           SET purchased_seconds = purchased_seconds + ?
           WHERE session_id = ?""",
        (int(seconds), session_id),
    )
    conn.commit()
    return wallet(conn, session_id)


def latest_block_code(conn: sqlite3.Connection, session_id: str) -> str | None:
    paid = conn.execute(
        """SELECT payment_reference FROM purchases
           WHERE session_id = ? AND status = 'paid' AND payment_reference IS NOT NULL
           ORDER BY created_at DESC LIMIT 1""",
        (session_id,),
    ).fetchone()
    if paid and paid["payment_reference"]:
        return str(paid["payment_reference"])
    pending = pending_purchase(conn, session_id)
    if pending and pending["payment_reference"]:
        return str(pending["payment_reference"])
    return None


def identity_session(conn: sqlite3.Connection, kind: str, value: str) -> sqlite3.Row | None:
    row = conn.execute(
        "SELECT session_id FROM identities WHERE kind = ? AND value = ?",
        (kind, value),
    ).fetchone()
    if not row:
        return None
    return session_by_id(conn, row["session_id"])


def current_ai_session(conn: sqlite3.Connection, user_session_id: str) -> sqlite3.Row | None:
    return conn.execute(
        """SELECT * FROM ai_sessions
           WHERE user_session_id = ?
           ORDER BY COALESCE(started_at, 0) DESC LIMIT 1""",
        (user_session_id,),
    ).fetchone()


def insert_ai_session(
    conn: sqlite3.Connection,
    session_id: str,
    user_session_id: str,
    started_at: float,
    status: str = "idle",
    channel: str = "web",
    label: str | None = None,
) -> sqlite3.Row:
    conn.execute(
        """INSERT INTO ai_sessions
           (id, user_session_id, started_at, paused_at, status, channel, label, processed_seconds)
           VALUES (?, ?, ?, NULL, ?, ?, ?, 0)""",
        (session_id, user_session_id, started_at, status, channel, label),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM ai_sessions WHERE id = ?", (session_id,)).fetchone()
    assert row is not None
    return row


def set_ai_session(
    conn: sqlite3.Connection,
    session_id: str,
    *,
    status: str,
    started_at: float | None = None,
    paused_at: float | None = None,
) -> None:
    conn.execute(
        """UPDATE ai_sessions
           SET status = ?, started_at = COALESCE(?, started_at), paused_at = ?
           WHERE id = ?""",
        (status, started_at, paused_at, session_id),
    )
    conn.commit()


def chat_by_id(conn: sqlite3.Connection, chat_id: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM ai_sessions WHERE id = ?", (chat_id,)).fetchone()


def wallet_chat(conn: sqlite3.Connection, wallet_session_id: str, chat_id: str) -> sqlite3.Row | None:
    return conn.execute(
        """SELECT * FROM ai_sessions
           WHERE id = ? AND user_session_id = ?""",
        (chat_id, wallet_session_id),
    ).fetchone()


def set_chat_label(conn: sqlite3.Connection, chat_id: str, label: str) -> None:
    conn.execute("UPDATE ai_sessions SET label = ? WHERE id = ?", (label, chat_id))
    conn.commit()


def touch_ai_session(conn: sqlite3.Connection, chat_id: str, started_at: float) -> None:
    conn.execute(
        "UPDATE ai_sessions SET started_at = ? WHERE id = ?",
        (started_at, chat_id),
    )
    conn.commit()


def next_chat_label(conn: sqlite3.Connection, wallet_session_id: str) -> str:
    n = conn.execute(
        "SELECT COUNT(*) FROM ai_sessions WHERE user_session_id = ?",
        (wallet_session_id,),
    ).fetchone()[0]
    return f"Chat {int(n) + 1}"


def set_wallet_consumed(conn: sqlite3.Connection, session_id: str, consumed: int) -> None:
    conn.execute(
        "UPDATE credit_wallets SET consumed_seconds = ? WHERE session_id = ?",
        (int(consumed), session_id),
    )
    conn.commit()


def add_chat_processed(conn: sqlite3.Connection, chat_id: str, seconds: int) -> None:
    conn.execute(
        """UPDATE ai_sessions
           SET processed_seconds = processed_seconds + ?
           WHERE id = ?""",
        (int(seconds), chat_id),
    )
    conn.commit()


def chats_for_wallet(conn: sqlite3.Connection, wallet_session_id: str) -> list[sqlite3.Row]:
    return list(
        conn.execute(
            """SELECT * FROM ai_sessions
               WHERE user_session_id = ?
               ORDER BY COALESCE(started_at, 0) DESC""",
            (wallet_session_id,),
        )
    )


def current_open_slice(conn: sqlite3.Connection, wallet_session_id: str) -> sqlite3.Row | None:
    return conn.execute(
        """SELECT * FROM usage_slices
           WHERE wallet_session_id = ? AND ended_at IS NULL
           ORDER BY started_at DESC LIMIT 1""",
        (wallet_session_id,),
    ).fetchone()


def insert_usage_slice(
    conn: sqlite3.Connection,
    slice_id: str,
    wallet_session_id: str,
    chat_id: str,
    channel: str,
    started_at: float,
) -> sqlite3.Row:
    conn.execute(
        """INSERT INTO usage_slices
           (id, wallet_session_id, chat_id, channel, started_at, ended_at, seconds)
           VALUES (?, ?, ?, ?, ?, NULL, 0)""",
        (slice_id, wallet_session_id, chat_id, channel, started_at),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM usage_slices WHERE id = ?", (slice_id,)).fetchone()
    assert row is not None
    return row


def close_usage_slice(
    conn: sqlite3.Connection,
    slice_id: str,
    ended_at: float,
    seconds: int,
) -> None:
    conn.execute(
        """UPDATE usage_slices
           SET ended_at = ?, seconds = ?
           WHERE id = ? AND ended_at IS NULL""",
        (ended_at, int(seconds), slice_id),
    )
    conn.commit()


def set_session_name(conn: sqlite3.Connection, session_id: str, name: str) -> None:
    conn.execute(
        "UPDATE user_sessions SET display_name = ? WHERE id = ?",
        (name.strip(), session_id),
    )
    conn.commit()


def upsert_customer(conn: sqlite3.Connection, session_id: str, name: str) -> None:
    conn.execute(
        """INSERT INTO customers (session_id, name, created_at)
           VALUES (?, ?, ?)
           ON CONFLICT(session_id) DO UPDATE SET name = excluded.name""",
        (session_id, name.strip(), now()),
    )
    conn.commit()


def bind_identity(
    conn: sqlite3.Connection,
    identity_id: str,
    kind: str,
    value: str,
    session_id: str,
) -> str:
    """Attach identity to session. If it already exists, return the original session_id."""
    existing = identity_session(conn, kind, value)
    if existing:
        return str(existing["id"])
    conn.execute(
        """INSERT INTO identities (id, kind, value, session_id, created_at)
           VALUES (?, ?, ?, ?, ?)""",
        (identity_id, kind, value, session_id, now()),
    )
    conn.commit()
    return session_id


TURN_KEEP = 40


def append_chat_turn(conn: sqlite3.Connection, chat_id: str, role: str, body: str) -> None:
    text = (body or "")[:8000]
    if not chat_id or not text:
        return
    conn.execute(
        """INSERT INTO chat_turns (chat_id, role, body, created_at)
           VALUES (?, ?, ?, ?)""",
        (chat_id, role, text, now()),
    )
    ids = [
        row["id"]
        for row in conn.execute(
            "SELECT id FROM chat_turns WHERE chat_id = ? ORDER BY id ASC",
            (chat_id,),
        )
    ]
    if len(ids) > TURN_KEEP:
        conn.execute(
            f"DELETE FROM chat_turns WHERE id IN ({','.join('?' * (len(ids) - TURN_KEEP))})",
            ids[: len(ids) - TURN_KEEP],
        )
    conn.commit()


def list_chat_turns(conn: sqlite3.Connection, chat_id: str, limit: int = TURN_KEEP) -> list[dict]:
    rows = conn.execute(
        """SELECT role, body, created_at FROM chat_turns
           WHERE chat_id = ?
           ORDER BY id DESC LIMIT ?""",
        (chat_id, max(1, int(limit))),
    ).fetchall()
    out = [{"role": r["role"], "body": r["body"], "created_at": r["created_at"]} for r in rows]
    out.reverse()
    return out
