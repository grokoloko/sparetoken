#!/usr/bin/env python3
"""SSH gate: block code or resume token. JSON on stdout, prompts on stderr.

No name. No WhatsApp. No email. The wallet code is the login.
"""
from __future__ import annotations

import json
import re
import sys

SESSION_RE = re.compile(r"^session-\d{8}-\d{6}-[0-9a-f]{6}$", re.I)
UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.I,
)
BLOCK_RE = re.compile(r"^wdtsot-[23456789ABCDEFGHJKLMNPQRSTUVWXYZ]{4}$")
PAY_RE = re.compile(r"https://app\.conta\.vc/pay/fuzzy/c/[A-Za-z0-9_-]+")


def parse_resume_token(raw: str) -> str | None:
    s = (raw or "").strip().strip("'\"")
    s = re.sub(r"^(resume|--resume|-r)\s+", "", s, flags=re.I).strip().strip("'\"")
    if SESSION_RE.match(s) or UUID_RE.match(s):
        return s
    return None


def parse_block_code(raw: str) -> str | None:
    s = re.sub(r"\s+", "", raw or "").strip().upper().replace("_", "-")
    if s.startswith("WDTSOT-"):
        s = "wdtsot-" + s[7:]
    elif re.fullmatch(r"[23456789ABCDEFGHJKLMNPQRSTUVWXYZ]{4}", s):
        s = f"wdtsot-{s}"
    if BLOCK_RE.fullmatch(s):
        return s
    return None


def parse_pay_url(raw: str) -> str | None:
    match = PAY_RE.search(raw or "")
    return match.group(0) if match else None


def build_payload(raw: str) -> dict:
    text = (raw or "").strip()
    if not text:
        return {}
    token = parse_resume_token(text)
    if token:
        return {"resume": token}
    block = parse_block_code(text)
    if block:
        return {"block_code": block}
    url = parse_pay_url(text)
    if url:
        return {"pay_url": url}
    return {}


def ask(label: str) -> str:
    sys.stderr.write(label)
    sys.stderr.flush()
    line = sys.stdin.readline()
    if not line:
        return ""
    return line.strip()


def main() -> None:
    sys.stderr.write("\n")
    sys.stderr.write("=== spare tokens · GROK 4.6 High Fast ===\n")
    sys.stderr.write("O login é o código do bloco. Sem nome. Sem telefone. Sem e-mail.\n")
    sys.stderr.write("wdtsot-XXXX ou o link do Pix. Enter vazio = um Pix Open.\n")
    sys.stderr.write("session-id / UUID retoma o chat.\n")
    sys.stderr.write("\n")
    raw = ask("código do bloco (wdtsot-XXXX) ou Enter: ")
    payload = build_payload(raw)
    if raw and not payload:
        sys.stderr.write("não reconheci. use wdtsot-XXXX, o link do Pix, ou Enter.\n")
        payload = {}
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.stderr.write("\nCancelado.\n")
        sys.exit(1)
