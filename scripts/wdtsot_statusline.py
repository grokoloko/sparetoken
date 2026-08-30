#!/usr/bin/env python3
"""WDTSOT SSH status line — same clock as the web button, one glance.

Reads logs/wdtsot.json (kept fresh by tunnel-gate watch). Does not query sqlite
from inside the guest sandbox. Stdin payload supplies context_window.used_percentage.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def minutes_label(seconds: int | None) -> str:
    n = max(0, int(seconds or 0) // 60)
    return "1 min" if n == 1 else f"{n} min"


def remaining_label(seconds: int | None, clock: str | None = None) -> str:
    if seconds is None:
        return f"{clock} restantes" if clock else "sem relógio"
    s = max(0, int(seconds))
    h, rem = divmod(s, 3600)
    m = rem // 60
    if s <= 0:
        return "as 5h acabaram"
    if h and m:
        return f"{h}h {m} min restantes"
    if h:
        return f"{h}h restantes"
    if m:
        return f"{m} min restantes"
    return "menos de 1 min"


def context_label(payload: dict | None) -> str:
    if not payload:
        return ""
    window = payload.get("context_window") or {}
    pct = window.get("used_percentage")
    if pct is None:
        return ""
    try:
        n = int(float(pct))
    except (TypeError, ValueError):
        return ""
    n = max(0, min(100, n))
    return f" · ctx {n}%"


def format_statusline(data: dict, payload: dict | None = None) -> str:
    code = data.get("block_code") or "wdtsot"
    rest = remaining_label(data.get("remaining_seconds"), data.get("remaining_clock"))
    line = minutes_label(data.get("line_used_seconds"))
    total = minutes_label(data.get("used_seconds"))
    n = int(data.get("chat_count") or 0)
    noun = "chat" if n == 1 else "chats"
    busy = " · GROK processando" if data.get("processing") else ""
    ctx = context_label(payload)
    line1 = f"{code} · GROK 4.6{ctx}{busy}"
    if n:
        line2 = f"{rest} · {line} nesta linha · {n} {noun} · {total} / 5h"
    else:
        line2 = f"{rest} · {total} / 5h"
    return f"{line1}\n{line2}"


def _clock_path() -> Path:
    logs = Path(os.environ.get("LOG_DIR") or "")
    if logs.is_dir():
        return logs / "wdtsot.json"
    session = Path(os.environ.get("SESSION_DIR") or "")
    if session.is_dir():
        return session / "logs" / "wdtsot.json"
    return Path("wdtsot.json")


def main() -> int:
    payload = None
    try:
        raw = sys.stdin.read()
        if raw.strip():
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                payload = parsed
    except Exception:
        payload = None
    path = _clock_path()
    if not path.is_file():
        sys.stdout.write(f"wdtsot · GROK 4.6{context_label(payload)}\nsem relógio neste terminal\n")
        return 0
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        sys.stdout.write(f"wdtsot · GROK 4.6{context_label(payload)}\nrelógio indisponível\n")
        return 0
    if not isinstance(data, dict):
        data = {}
    sys.stdout.write(format_statusline(data, payload) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
