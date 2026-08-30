#!/usr/bin/env python3
"""WDTSOT pay wall + processing clock for the SSH guest tunnel."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

WDTSOT = Path(
    os.environ.get(
        "WDTSOT_ROOT",
        "/home/ubuntu/development/guest-sessions/session-20260829-212831-83c1eb/workspace/wdtsot",
    )
)
sys.path.insert(0, str(WDTSOT))

from db import (  # noqa: E402
    connect,
    get_or_create_session,
    identity_session,
    purchase_by_reference,
    session_by_id,
    set_session_name,
    upsert_customer,
)
import clock  # noqa: E402
import pay  # noqa: E402

DB_PATH = Path(os.environ.get("WDTSOT_DATA", str(WDTSOT / "data"))) / "wdtsot.sqlite"


def _err(msg: str) -> None:
    sys.stderr.write(msg + "\n")
    sys.stderr.flush()


def _ask(label: str) -> str:
    sys.stderr.write(label)
    sys.stderr.flush()
    line = sys.stdin.readline()
    if not line:
        sys.exit(1)
    return line.strip()


def _conn():
    return connect(DB_PATH)


def _guest() -> dict:
    raw = os.environ.get("GUEST_INFO_JSON") or "{}"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {}
    start = Path(os.environ.get("LOG_DIR") or ".") / "session.start.json"
    if start.is_file():
        try:
            rec = json.loads(start.read_text(encoding="utf-8"))
            data = {**(rec.get("guest") or {}), **data}
        except Exception:
            pass
    return data


def _resolve_session(conn, guest: dict, ssh_id: str):
    block = pay.normalize_block_code(guest.get("block_code") or guest.get("name"))
    if block:
        purchase = purchase_by_reference(conn, block)
        if purchase:
            found = session_by_id(conn, str(purchase["session_id"]))
            if found:
                return found
    for kind, key in (("whatsapp", "whatsapp"), ("email", "email")):
        value = (guest.get(key) or "").strip()
        if not value:
            continue
        try:
            parsed = pay.parse_contact(value)
        except pay.PayError:
            continue
        if parsed and parsed[0] == kind:
            found = identity_session(conn, parsed[0], parsed[1])
            if found:
                return found
    return get_or_create_session(conn, ssh_id, ssh_id)


def _write_map(session_id: str, snap: dict, ssh_id: str | None = None) -> None:
    logs = Path(os.environ.get("LOG_DIR") or ".")
    logs.mkdir(parents=True, exist_ok=True)
    ssh_id = ssh_id or os.environ.get("SESSION_ID") or ""
    chats = snap.get("chats") or []
    line = None
    if ssh_id:
        want = f"ssh-{ssh_id}"
        line = next((c for c in chats if c.get("id") == want), None)
    payload = {
        "wdtsot_session_id": session_id,
        "block_code": snap.get("block_code"),
        "remaining_clock": snap.get("remaining_clock"),
        "remaining_seconds": snap.get("remaining_seconds"),
        "used_clock": snap.get("used_clock"),
        "used_seconds": snap.get("used_seconds"),
        "chat_count": len(chats),
        "line_id": (line or {}).get("id"),
        "line_label": (line or {}).get("label"),
        "line_used_seconds": (line or {}).get("used_seconds") or 0,
        "processing": snap.get("processing"),
        "return_url": snap.get("return_url"),
    }
    (logs / "wdtsot.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _show_ready(snap: dict) -> None:
    _err("")
    _err(f"GROK 4.6 High Fast · código {snap.get('block_code') or '—'}")
    _err(f"processamento restante: {snap['remaining_clock']}  (usado {snap['used_clock']})")
    _err(f"voltar: {snap['return_url']}")
    _err("Guarde o código. WhatsApp + código retomam as 5h na web e no SSH.")
    _err("")


def _try_claim(conn, session_id: str, contact: str, code: str, pay_url: str | None) -> dict | None:
    try:
        return pay.claim(conn, session_id, contact=contact, code=code, pay_url=pay_url or "")
    except pay.PayError as exc:
        _err(str(exc))
        return None


def gate() -> int:
    ssh_id = os.environ.get("SESSION_ID") or ""
    if not ssh_id:
        _err("sessão SSH sem id")
        return 2
    guest = _guest()
    conn = _conn()
    row = _resolve_session(conn, guest, ssh_id)
    session_id = str(row["id"])
    name = (guest.get("name") or "").strip()
    if name and not pay.normalize_block_code(name):
        set_session_name(conn, session_id, name)
        upsert_customer(conn, session_id, name)
    contact = (guest.get("whatsapp") or guest.get("email") or "").strip()
    incoming_code = pay.normalize_block_code(guest.get("block_code") or guest.get("name"))

    snap = clock.snapshot(conn, session_id)
    if snap["remaining_seconds"] <= 0 and incoming_code:
        result = _try_claim(conn, session_id, contact, incoming_code, None)
        if result and result.get("paid"):
            session_id = result["session_id"]
            snap = clock.snapshot(conn, session_id)

    if snap["remaining_seconds"] <= 0:
        try:
            checkout = pay.start_checkout(conn, session_id)
        except pay.PayError as exc:
            _err(str(exc))
            return 3
        _err("")
        _err("=== wdtsot · GROK 4.6 High Fast · R$5 / 5h ===")
        _err("Pague ESTE Pix, espere confirmar, depois digite o código do bloco.")
        _err(f"Pix: {checkout['pay_url']}")
        _err(f"Código do bloco: {checkout['block_code']}")
        _err("As 5h só andam enquanto o GROK processa — não enquanto você digita.")
        _err("Se já tem um código pago (wdtsot-XXXX), cole ele agora.")
        _err("")
        for _ in range(8):
            ans = _ask("Já pagou? (código wdtsot-XXXX ou sim): ")
            typed = pay.normalize_block_code(ans)
            if typed:
                code, url = typed, None
            elif ans.lower() in {"s", "sim", "yes", "y", "paguei"}:
                code, url = checkout["block_code"], checkout["pay_url"]
            else:
                _err("cole o código do bloco (wdtsot-XXXX) ou escreva sim.")
                continue
            result = _try_claim(conn, session_id, contact, code, url)
            if result and result.get("paid"):
                session_id = result["session_id"]
                snap = clock.snapshot(conn, session_id)
                break
        else:
            _err("não confirmei o Pix. saia e tente de novo com o mesmo WhatsApp ou o código.")
            return 4

    if name and not pay.normalize_block_code(name):
        set_session_name(conn, session_id, name)
    clock.open_chat(
        conn,
        session_id,
        channel="ssh",
        label=ssh_id,
        chat_id=f"ssh-{ssh_id}",
    )
    snap = clock.snapshot(conn, session_id)
    _write_map(session_id, snap, ssh_id)
    _show_ready(snap)
    return 0


def watch() -> int:
    data = json.loads((Path(os.environ["LOG_DIR"]) / "wdtsot.json").read_text(encoding="utf-8"))
    wallet_id = data["wdtsot_session_id"]
    ssh_id = os.environ.get("SESSION_ID") or "ssh"
    conn = _conn()
    state = Path(os.environ["CURSOR_STATE"])
    last_mtime = 0.0
    busy = False
    idle_since = time.time()
    last_map = 0.0
    try:
        while True:
            time.sleep(1.2)
            newest = last_mtime
            if state.is_dir():
                for path in state.rglob("*"):
                    try:
                        newest = max(newest, path.stat().st_mtime)
                    except OSError:
                        continue
            now = time.time()
            if newest > last_mtime + 0.01:
                last_mtime = newest
                idle_since = now
                if not busy:
                    clock.start_processing(
                        conn,
                        wallet_id,
                        channel="ssh",
                        label=ssh_id,
                        chat_id=f"ssh-{ssh_id}",
                    )
                    busy = True
            elif busy and now - idle_since >= 6:
                clock.end_processing(conn, wallet_id)
                busy = False
            if now - last_map >= 2:
                _write_map(wallet_id, clock.snapshot(conn, wallet_id), ssh_id)
                last_map = now
    except KeyboardInterrupt:
        pass
    finally:
        clock.end_processing(conn, wallet_id)
    return 0


def finalize() -> int:
    path = Path(os.environ.get("LOG_DIR") or ".") / "wdtsot.json"
    if not path.is_file():
        return 0
    data = json.loads(path.read_text(encoding="utf-8"))
    conn = _conn()
    snap = clock.end_processing(conn, data["wdtsot_session_id"])
    data.update(
        {
            "remaining_clock": snap["remaining_clock"],
            "used_clock": snap["used_clock"],
            "chats": snap["chats"],
        }
    )
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    _err(
        f"wdtsot {snap.get('block_code') or ''}: {snap['used_clock']} processadas · "
        f"restam {snap['remaining_clock']}"
    )
    return 0


def main() -> int:
    cmd = (sys.argv[1] if len(sys.argv) > 1 else "gate").strip()
    if cmd == "watch":
        return watch()
    if cmd == "finalize":
        return finalize()
    return gate()


if __name__ == "__main__":
    raise SystemExit(main())
