#!/usr/bin/env python3
"""Append unique Open conta.vc charge URLs to the rotation file."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pay import CONTA_URL_RE, inspect_charge, load_links_file  # noqa: E402

LINKS = ROOT / "data" / "conta-links.txt"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--append", nargs="+", metavar="URL")
    parser.add_argument("--file", type=Path, default=LINKS)
    args = parser.parse_args()
    if not args.append:
        parser.error("passe uma ou mais URLs com --append")

    existing = set(load_links_file(args.file)) if args.file.is_file() else set()
    added: list[str] = []
    skipped: list[str] = []
    for raw in args.append:
        match = CONTA_URL_RE.search(raw.strip())
        if not match:
            print(f"ignora (URL inválida): {raw}", file=sys.stderr)
            continue
        url = match.group(0)
        if url in existing:
            skipped.append(url)
            continue
        ev = inspect_charge(url)
        if ev.get("status") != "open":
            print(f"ignora (status={ev.get('status')}): {url}", file=sys.stderr)
            continue
        existing.add(url)
        added.append(url)

    if added:
        args.file.parent.mkdir(parents=True, exist_ok=True)
        prior = args.file.read_text(encoding="utf-8") if args.file.is_file() else ""
        with args.file.open("a", encoding="utf-8") as fh:
            if prior and not prior.endswith("\n"):
                fh.write("\n")
            for url in added:
                fh.write(url + "\n")

    print(f"added={len(added)} skipped={len(skipped)} stock={len(existing)}")
    for url in added:
        print(url)
    return 0 if added or skipped else 2


if __name__ == "__main__":
    raise SystemExit(main())
