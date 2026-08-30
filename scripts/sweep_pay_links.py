#!/usr/bin/env python3
"""Inspect conta.vc charges and take Closed links out of site/SSH rotation."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from db import connect  # noqa: E402
from pay import sweep_pool  # noqa: E402


def main() -> int:
    conn = connect(ROOT / "data" / "wdtsot.sqlite")
    counts = sweep_pool(conn)
    print(f"open={counts['open']} closed={counts['closed']} dead={counts['dead']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
