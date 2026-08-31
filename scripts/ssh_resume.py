"""Helpers to reconnect an SSH line after a drop. No I/O, no host paths."""

from __future__ import annotations

RESUME_RECONNECT = 10
SSH_HOST = "wdtsot.shop"


def resume_token(chat_or_session_id: str) -> str:
    raw = (chat_or_session_id or "").strip()
    if raw.startswith("ssh-"):
        return raw[4:]
    return raw


def ssh_resume_cmd(chat_or_session_id: str, host: str = SSH_HOST) -> str:
    token = resume_token(chat_or_session_id)
    if not token:
        return ""
    return f"ssh -t agent-guest@{host} resume {token}"


def current_ssh_chat_id(ssh_id: str) -> str:
    ssh_id = (ssh_id or "").strip()
    if not ssh_id:
        return ""
    if ssh_id.startswith("ssh-"):
        return ssh_id
    return f"ssh-{ssh_id}"


def prior_ssh_lines(
    chats: list | None,
    current_ssh_id: str,
    *,
    limit: int = 5,
) -> list[dict]:
    current = current_ssh_chat_id(current_ssh_id)
    out: list[dict] = []
    for chat in chats or []:
        if (chat.get("channel") or "") != "ssh":
            continue
        cid = str(chat.get("id") or "")
        if not cid or cid == current:
            continue
        out.append(chat)
        if len(out) >= limit:
            break
    return out


def heaviest_ssh_line(chats: list | None) -> dict | None:
    rows = list(chats or [])
    if not rows:
        return None
    return max(rows, key=lambda c: int(c.get("used_seconds") or 0))


def parse_resume_answer(answer: str, lines: list) -> dict | None:
    """None = stay on the new line. dict = chosen prior chat."""
    raw = (answer or "").strip().lower()
    if not raw or raw in {"n", "nao", "não", "no"}:
        return None
    if raw.isdigit():
        idx = int(raw)
        if 1 <= idx <= len(lines):
            return lines[idx - 1]
        return None
    if raw in {"s", "sim", "y", "yes"}:
        return heaviest_ssh_line(lines)
    want = resume_token(raw)
    for chat in lines:
        if resume_token(str(chat.get("id") or "")) == want:
            return chat
    return None
