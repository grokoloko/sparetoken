#!/usr/bin/env python3
"""Bind a named customer to a closed conta.vc charge and credit 5h."""

from __future__ import annotations

import argparse
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from db import (  # noqa: E402
    connect,
    get_or_create_session,
    identity_session,
    set_session_name,
    upsert_customer,
)
from pay import claim, parse_contact  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True)
    parser.add_argument("--contact", required=True)
    parser.add_argument("--pay-url", required=True)
    parser.add_argument("--db", type=Path, default=ROOT / "data" / "wdtsot.sqlite")
    args = parser.parse_args()

    parsed = parse_contact(args.contact)
    if not parsed:
        print("contato inválido", file=sys.stderr)
        return 2

    conn = connect(args.db)
    existing = identity_session(conn, parsed[0], parsed[1])
    if existing:
        session_id = str(existing["id"])
    else:
        session_id = secrets.token_urlsafe(24)
        get_or_create_session(conn, session_id, session_id)

    result = claim(
        conn,
        session_id,
        contact=args.contact,
        pay_url=args.pay_url,
    )
    owner = result["session_id"]
    set_session_name(conn, owner, args.name)
    upsert_customer(conn, owner, args.name)
    print(
        f"name={args.name}\n"
        f"session_id={owner}\n"
        f"block_code={result['block_code']}\n"
        f"remaining={result['remaining_clock']}\n"
        f"paid={result['paid']}\n"
        f"identity={parsed[0]}:{parsed[1]}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
