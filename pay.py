"""Unique conta.vc charges + public-page proof. Never credit an Open link."""

from __future__ import annotations

import os
import re
import secrets
import sqlite3
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path

import credits
from db import (
    bind_identity,
    consume_pay_link,
    credit_wallet,
    identity_session,
    idle_pay_links,
    insert_pending_purchase,
    latest_block_code,
    listed_pay_links,
    mark_pay_link,
    mark_purchase_paid,
    pending_purchase,
    purchase_by_pay_url,
    purchase_by_reference,
    reserve_pay_link,
    session_by_id,
    upsert_pay_link,
    wallet,
)

ROOT = Path(__file__).resolve().parent
LINKS_FILE = Path(os.environ.get("WDTSOT_LINKS_FILE", str(ROOT / "data" / "conta-links.txt")))
FALLBACK_PAY_URL = os.environ.get(
    "WDTSOT_PAY_URL",
    "https://app.conta.vc/pay/fuzzy/c/Y_saWXtd37j5fMagI3klioK95ZyBd9iSMMB-ggzI5gI",
)
PAY_URL = FALLBACK_PAY_URL
SKU = "wdtsot-5h"
PRODUCT_DESCRIPTION = "wdtsot · 5h · 4.6 High Fast"
AMOUNT_BRL = 5.0
SECONDS = credits.HOURS_5
CODE_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
CONTA_URL_RE = re.compile(
    r"https://app\.conta\.vc/pay/fuzzy/c/[A-Za-z0-9_-]+"
)
InspectFn = Callable[[str], dict]


class PayError(ValueError):
    pass


def new_block_code() -> str:
    body = "".join(secrets.choice(CODE_ALPHABET) for _ in range(4))
    return f"wdtsot-{body}"


def normalize_block_code(raw: str | None) -> str | None:
    if not raw:
        return None
    text = re.sub(r"\s+", "", str(raw)).strip().upper().replace("_", "-")
    if text.startswith("WDTSOT-"):
        text = "wdtsot-" + text[7:]
    elif re.fullmatch(r"[23456789ABCDEFGHJKLMNPQRSTUVWXYZ]{4}", text):
        text = f"wdtsot-{text}"
    if re.fullmatch(r"wdtsot-[23456789ABCDEFGHJKLMNPQRSTUVWXYZ]{4}", text):
        return text
    return None


def parse_contact(raw: str | None) -> tuple[str, str] | None:
    text = (raw or "").strip()
    if not text:
        return None
    if "@" in text:
        email = text.lower()
        if EMAIL_RE.match(email) and len(email) <= 120:
            return "email", email
        raise PayError("e-mail inválido")
    digits = re.sub(r"\D", "", text)
    if len(digits) == 10 or len(digits) == 11:
        digits = "55" + digits
    if 12 <= len(digits) <= 15:
        return "whatsapp", digits
    raise PayError("use um e-mail ou WhatsApp com DDD")


def parse_charge_html(html: str) -> dict:
    """Read the public /pay page. Open = still unpaid."""
    if re.search(r"link\s+closed", html, re.I) or re.search(
        r">\s*(Closed|Paid|Settled)\s*<", html, re.I
    ):
        return {"status": "closed"}
    if re.search(r">\s*Open\s*<", html) or "Generate PIX" in html:
        return {"status": "open"}
    if re.search(r'"paused"\s*:\s*true', html):
        return {"status": "dead"}
    if "charge" in html and "amountCents" in html:
        return {"status": "closed"}
    return {"status": "unknown"}


def normalize_pay_url(raw: str | None) -> str | None:
    if not raw:
        return None
    match = CONTA_URL_RE.search(str(raw))
    return match.group(0) if match else None


def inspect_charge(url: str) -> dict:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "wdtsot-pay/0.2", "Accept": "text/html"},
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            html = resp.read().decode("utf-8", "replace")
            code = resp.getcode()
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return {"status": "dead"}
        return {"status": "unknown"}
    except (urllib.error.URLError, TimeoutError, OSError):
        return {"status": "unknown"}
    if code != 200:
        return {"status": "unknown"}
    return parse_charge_html(html)


def load_links_file(path: Path | None = None) -> list[str]:
    target = path or LINKS_FILE
    if not target.is_file():
        return [FALLBACK_PAY_URL]
    urls: list[str] = []
    for line in target.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = CONTA_URL_RE.search(line)
        if match and match.group(0) not in urls:
            urls.append(match.group(0))
    return urls or [FALLBACK_PAY_URL]


def sync_pool(conn: sqlite3.Connection, path: Path | None = None) -> list[str]:
    urls = load_links_file(path)
    for url in urls:
        upsert_pay_link(conn, url)
    return urls


def sweep_pool(
    conn: sqlite3.Connection,
    inspect: InspectFn | None = None,
    path: Path | None = None,
) -> dict:
    """Take Closed/dead charges out of rotation. Returns counts."""
    look = inspect or inspect_charge
    sync_pool(conn, path)
    closed = 0
    dead = 0
    open_n = 0
    for row in listed_pay_links(conn):
        if row["status"] in ("consumed", "dead"):
            continue
        ev = look(row["url"])
        status = ev.get("status")
        if status == "closed":
            consume_pay_link(conn, row["url"])
            closed += 1
        elif status == "dead":
            mark_pay_link(conn, row["url"], "dead")
            dead += 1
        elif status == "open":
            open_n += 1
    return {"closed": closed, "dead": dead, "open": open_n}


def next_open_url(
    conn: sqlite3.Connection,
    inspect: InspectFn | None = None,
    path: Path | None = None,
) -> str | None:
    look = inspect or inspect_charge
    sweep_pool(conn, look, path)
    for row in idle_pay_links(conn):
        ev = look(row["url"])
        if ev.get("status") == "open":
            return str(row["url"])
    return None


def _allocate_link(
    conn: sqlite3.Connection,
    session_id: str,
    inspect: InspectFn,
    path: Path | None = None,
) -> str:
    sweep_pool(conn, inspect, path)
    for row in idle_pay_links(conn):
        ev = inspect(row["url"])
        status = ev.get("status")
        if status == "open":
            reserve_pay_link(conn, row["url"], session_id)
            return str(row["url"])
        if status == "closed":
            consume_pay_link(conn, row["url"])
            continue
        if status == "dead":
            mark_pay_link(conn, row["url"], "dead")
    raise PayError("estoque de Pix esgotado. o founder ainda não colocou links Open novos.")


def start_checkout(
    conn: sqlite3.Connection,
    session_id: str,
    inspect: InspectFn | None = None,
    links_file: Path | None = None,
) -> dict:
    existing = pending_purchase(conn, session_id)
    if existing:
        return {
            "pay_url": existing["pay_url"] or FALLBACK_PAY_URL,
            "block_code": existing["payment_reference"],
            "amount_brl": float(existing["amount_brl"] or AMOUNT_BRL),
            "seconds": int(existing["seconds_purchased"] or SECONDS),
            "status": "pending",
        }
    pay_url = _allocate_link(conn, session_id, inspect or inspect_charge, links_file)
    for _ in range(8):
        code = new_block_code()
        if purchase_by_reference(conn, code) is None:
            insert_pending_purchase(
                conn,
                secrets.token_urlsafe(16),
                session_id,
                AMOUNT_BRL,
                SECONDS,
                code,
                pay_url,
            )
            return {
                "pay_url": pay_url,
                "block_code": code,
                "amount_brl": AMOUNT_BRL,
                "seconds": SECONDS,
                "status": "pending",
            }
    raise PayError("não consegui gerar o código do bloco")


def _remaining(conn: sqlite3.Connection, session_id: str) -> int:
    w = wallet(conn, session_id)
    return credits.remaining_seconds(w["purchased_seconds"], w["consumed_seconds"])


def _session_payload(conn: sqlite3.Connection, session_id: str) -> dict:
    row = session_by_id(conn, session_id)
    if not row:
        raise PayError("sessão não encontrada")
    remaining = _remaining(conn, session_id)
    return {
        "session_id": session_id,
        "public_token": row["public_token"],
        "block_code": latest_block_code(conn, session_id),
        "remaining_seconds": remaining,
        "remaining_clock": credits.format_hms(remaining),
        "paid": remaining > 0,
    }


def _apply_paid(conn: sqlite3.Connection, purchase: sqlite3.Row) -> sqlite3.Row:
    if purchase["status"] == "paid":
        return purchase
    updated = mark_purchase_paid(conn, purchase["id"])
    if not updated or updated["status"] != "paid":
        raise PayError("não consegui confirmar esse pagamento")
    seconds = int(updated["seconds_purchased"] or SECONDS)
    credit_wallet(conn, updated["session_id"], seconds)
    if updated["pay_url"]:
        consume_pay_link(conn, updated["pay_url"])
    return updated


def _bind_contact(
    conn: sqlite3.Connection,
    parsed: tuple[str, str] | None,
    session_id: str,
) -> str:
    if not parsed:
        return session_id
    existing = identity_session(conn, parsed[0], parsed[1])
    if existing:
        owner = str(existing["id"])
        if owner == session_id or _remaining(conn, owner) > 0:
            return owner
        conn.execute(
            "UPDATE identities SET session_id = ? WHERE kind = ? AND value = ?",
            (session_id, parsed[0], parsed[1]),
        )
        conn.commit()
        return session_id
    return bind_identity(
        conn, secrets.token_urlsafe(12), parsed[0], parsed[1], session_id
    )


def _confirm_pending(
    conn: sqlite3.Connection,
    purchase: sqlite3.Row,
    inspect: InspectFn,
) -> sqlite3.Row:
    url = purchase["pay_url"] or FALLBACK_PAY_URL
    ev = inspect(url)
    if ev.get("status") == "closed":
        return _apply_paid(conn, purchase)
    if ev.get("status") == "open":
        raise PayError("esse Pix ainda está Open. pague e volte para liberar.")
    raise PayError("não confirmei o fechamento desse charge. tente de novo em instantes.")


def _unclaimed_closed(
    conn: sqlite3.Connection,
    inspect: InspectFn,
    path: Path | None = None,
) -> list[str]:
    """Closed stock that nobody has a purchase for yet (paid a shared link)."""
    sync_pool(conn, path)
    found: list[str] = []
    for row in listed_pay_links(conn):
        url = str(row["url"])
        if purchase_by_pay_url(conn, url):
            continue
        ev = inspect(url)
        status = ev.get("status")
        if status == "closed":
            found.append(url)
        elif status == "dead":
            mark_pay_link(conn, url, "dead")
    return found


def _new_purchase_for_url(conn: sqlite3.Connection, session_id: str, url: str) -> sqlite3.Row:
    for _ in range(8):
        code = new_block_code()
        if purchase_by_reference(conn, code) is None:
            return insert_pending_purchase(
                conn,
                secrets.token_urlsafe(16),
                session_id,
                AMOUNT_BRL,
                SECONDS,
                code,
                url,
            )
    raise PayError("não consegui gerar o código do bloco")


def _attach_closed_charge(
    conn: sqlite3.Connection,
    session_id: str,
    url: str,
    inspect: InspectFn,
) -> sqlite3.Row:
    ev = inspect(url)
    if ev.get("status") == "open":
        raise PayError("esse Pix ainda está Open. pague e volte para liberar.")
    if ev.get("status") != "closed":
        raise PayError("não confirmei o fechamento desse charge. tente de novo em instantes.")

    existing = purchase_by_pay_url(conn, url)
    if existing:
        if existing["status"] == "pending":
            return _apply_paid(conn, existing)
        return existing
    purchase = _new_purchase_for_url(conn, session_id, url)
    return _apply_paid(conn, purchase)


def claim(
    conn: sqlite3.Connection,
    session_id: str,
    contact: str | None = None,
    code: str | None = None,
    pay_url: str | None = None,
    inspect: InspectFn | None = None,
    links_file: Path | None = None,
) -> dict:
    """Resume a paid block, or confirm a pending purchase after the Pix.

    Pending credit requires the assigned conta.vc page to no longer be Open.
    A closed stock URL with no purchase yet (paid a shared link) can be
    claimed with contact, or with that URL. Contact alone only resumes an
    identity that already paid, unless exactly one unclaimed closed charge
    exists.
    """
    look = inspect or inspect_charge
    parsed = parse_contact(contact) if (contact or "").strip() else None
    block = normalize_block_code(code)
    url = None if block else (normalize_pay_url(pay_url) or normalize_pay_url(code))
    if not parsed and not block and not url:
        raise PayError("informe o código do bloco (wdtsot-XXXX) ou o link do Pix")

    identified = identity_session(conn, parsed[0], parsed[1]) if parsed else None
    if identified and _remaining(conn, identified["id"]) > 0:
        return _session_payload(conn, str(identified["id"]))

    purchase = purchase_by_reference(conn, block) if block else None
    if block and purchase is None:
        raise PayError("não achei esse código do bloco")

    if purchase is not None:
        owner = str(purchase["session_id"])
        if purchase["status"] == "pending":
            _confirm_pending(conn, purchase, look)
        _bind_contact(conn, parsed, owner)
        return _session_payload(conn, owner)

    local_pending = pending_purchase(conn, session_id)
    if local_pending:
        _confirm_pending(conn, local_pending, look)
        _bind_contact(conn, parsed, session_id)
        return _session_payload(conn, session_id)

    if url:
        known = set(load_links_file(links_file))
        sync_pool(conn, links_file)
        if url not in known:
            raise PayError("esse link não é um charge wdtsot")
        existing = purchase_by_pay_url(conn, url)
        if existing and existing["status"] == "paid":
            owner = str(existing["session_id"])
            if owner == session_id:
                _bind_contact(conn, parsed, owner)
                return _session_payload(conn, owner)
            raise PayError("esse Pix já foi usado em outro bloco")
        attached = _attach_closed_charge(conn, session_id, url, look)
        owner = str(attached["session_id"])
        _bind_contact(conn, parsed, owner)
        return _session_payload(conn, owner)

    if parsed:
        closed = _unclaimed_closed(conn, look, links_file)
        if len(closed) == 1:
            attached = _attach_closed_charge(conn, session_id, closed[0], look)
            _bind_contact(conn, parsed, session_id)
            return _session_payload(conn, str(attached["session_id"]))
        if len(closed) > 1:
            raise PayError("tem mais de um Pix fechado. cole o link que você pagou.")

    raise PayError("não achei um pagamento para liberar. pague e volte com o código.")
