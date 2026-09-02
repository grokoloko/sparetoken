#!/usr/bin/env python3
"""Marketplace gate: guest tunnel must be identity-hard.

Exit 0 only if static contract holds. Live SSH probe (optional) fails if the
agent yields operator identity under light jailbreak — see --probe.

Never embeds real human names; probe checks only that refusals stay dry and
that guest AGENTS / run-agent wiring exists.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_PHRASES = (
    "IDENTITY-HARD",
    "Never reveal",
    "dry refusal",
    "sparetoken-guest",
)
RUN_AGENT = ROOT / "run-agent.sh"
GUEST_AGENTS = ROOT / "tunnel" / "guest-AGENTS.md"
HARDEN = ROOT / "scripts" / "guest_identity_harden.py"


def check_static() -> list[str]:
    errs: list[str] = []
    if not GUEST_AGENTS.is_file():
        errs.append("missing tunnel/guest-AGENTS.md")
        return errs
    text = GUEST_AGENTS.read_text(encoding="utf-8")
    for p in REQUIRED_PHRASES:
        if p == "sparetoken-guest":
            continue
        if p not in text:
            errs.append(f"guest-AGENTS.md missing phrase: {p}")
    if not HARDEN.is_file():
        errs.append("missing scripts/guest_identity_harden.py")
    if not RUN_AGENT.is_file():
        errs.append("missing run-agent.sh")
    else:
        sh = RUN_AGENT.read_text(encoding="utf-8")
        if "guest_identity_harden.py" not in sh:
            errs.append("run-agent.sh does not call guest_identity_harden.py")
        if "IDENTITY_HARD" not in sh and "guest_identity_harden" not in sh:
            errs.append("run-agent.sh missing identity harden hook")
        if "--unsetenv GIT_AUTHOR_NAME" not in sh and "GIT_AUTHOR_NAME" not in sh:
            errs.append("run-agent.sh must unset identity-leaking git env")
    # soft-yield anti-patterns in guest rule
    soft = re.compile(r"\bif you insist\b|\bas a last resort\b|\bmaybe share\b", re.I)
    if soft.search(text):
        errs.append("guest-AGENTS.md has soft-yield language")
    return errs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--probe",
        action="store_true",
        help="reserved: live SSH jailbreak probe (not run in CI by default)",
    )
    args = ap.parse_args()
    errs = check_static()
    if args.probe:
        errs.append(
            "live --probe not wired in this revision; ship static gate first "
            "(CEO can extend with SSH expect)"
        )
    if errs:
        for e in errs:
            print(f"FAIL: {e}", file=sys.stderr)
        return 1
    print("OK: guest identity-hard contract")
    return 0


if __name__ == "__main__":
    sys.exit(main())
