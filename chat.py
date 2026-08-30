"""Wrap the existing Cursor Agent CLI in ask mode. Never use a shell."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import threading
from pathlib import Path
from typing import Callable, Iterator

MODEL = os.environ.get("WDTSOT_MODEL", "cursor-grok-4.6-high-fast")
AGENT_BIN = os.environ.get(
    "WDTSOT_AGENT_BIN",
    os.environ.get("AGENT_BIN", "/home/ubuntu/.local/bin/agent"),
)
REAL_HOME = os.environ.get("REAL_HOME", "/home/ubuntu")
SYSTEM_HINT = (
    "You are the WDTSOT assistant (GROK 4.6 High Fast). "
    "WDTSOT means 'we deserve to share our tokens.' "
    "Be concise, warm, and useful. Answer in the visitor's language. "
    "Do not mention API keys, SSH secrets, auth tokens, or internal paths. "
    "Do not claim to process payments. "
    "You are in a short public experiment — prefer practical help over speeches."
)


class ChatError(RuntimeError):
    pass


def _agent_env() -> dict[str, str]:
    env = os.environ.copy()
    for key in (
        "CURSOR_ASKPASS_SECRET",
        "CURSOR_ASKPASS_SOCKET",
        "CURSOR_CONVERSATION_ID",
        "GUEST_INFO_JSON",
        "SUDO_ASKPASS",
    ):
        env.pop(key, None)
    env["HOME"] = REAL_HOME
    env["TERM"] = "dumb"
    env["NO_COLOR"] = "1"
    return env


def find_agent() -> str:
    if os.path.isfile(AGENT_BIN) and os.access(AGENT_BIN, os.X_OK):
        return AGENT_BIN
    found = shutil.which("agent") or shutil.which("cursor-agent")
    if not found:
        raise ChatError("cursor agent binary is not available on this host")
    return found


def build_prompt(user_text: str, history: list[tuple[str, str]] | None = None) -> str:
    parts = [SYSTEM_HINT, ""]
    if history:
        parts.append("Recent conversation:")
        for role, text in history[-6:]:
            label = "Visitor" if role == "user" else "Assistant"
            parts.append(f"{label}: {text}")
        parts.append("")
    parts.append("Visitor:")
    parts.append(user_text.strip())
    parts.append("")
    parts.append("Assistant:")
    return "\n".join(parts)


def _assistant_text(event: dict) -> str:
    message = event.get("message")
    if not isinstance(message, dict):
        return ""
    content = message.get("content")
    if isinstance(content, str):
        return content
    parts: list[str] = []
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict) and item.get("type") in {"text", "output_text"}:
                text = item.get("text")
                if isinstance(text, str) and text:
                    parts.append(text)
    return "".join(parts)


def iter_assistant_deltas(events: Iterator[object]) -> Iterator[str]:
    """Yield only new assistant text. Ignore system/user/thinking/result echoes."""
    emitted = ""
    saw_assistant = False
    for event in events:
        if not isinstance(event, dict):
            continue
        etype = event.get("type")
        if etype == "assistant":
            piece = _assistant_text(event)
            if not piece:
                continue
            saw_assistant = True
            if piece == emitted or (emitted.startswith(piece) and emitted):
                continue
            if emitted and piece.startswith(emitted):
                delta = piece[len(emitted) :]
                if delta:
                    yield delta
                emitted = piece
                continue
            yield piece
            emitted += piece
            continue
        if etype == "result" and not saw_assistant:
            result = event.get("result")
            if isinstance(result, str) and result:
                yield result
                emitted = result


def _iter_stream_json(proc: subprocess.Popen) -> Iterator[str]:
    assert proc.stdout is not None

    def events() -> Iterator[object]:
        for raw in proc.stdout:
            line = raw.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue

    yield from iter_assistant_deltas(events())


def stream_reply(
    user_text: str,
    workspace: Path,
    history: list[tuple[str, str]] | None = None,
    timeout: int = 120,
    on_pid: Callable[[int], None] | None = None,
) -> Iterator[str]:
    agent = find_agent()
    workspace.mkdir(parents=True, exist_ok=True)
    readme = workspace / "README.txt"
    if not readme.exists():
        readme.write_text(
            "Isolated WDTSOT web-chat workspace. Ask mode only.\n",
            encoding="utf-8",
        )
    prompt = build_prompt(user_text, history)
    cmd = [
        agent,
        "-p",
        "--mode",
        "ask",
        "--trust",
        "--sandbox",
        "enabled",
        "--model",
        MODEL,
        "--output-format",
        "stream-json",
        "--stream-partial-output",
        "--workspace",
        str(workspace),
        "--",
        prompt,
    ]
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=_agent_env(),
        cwd=str(workspace),
    )
    if on_pid:
        on_pid(proc.pid)

    stderr_chunks: list[str] = []

    def _drain_err() -> None:
        if proc.stderr:
            stderr_chunks.append(proc.stderr.read() or "")

    err_thread = threading.Thread(target=_drain_err, daemon=True)
    err_thread.start()

    produced = False
    try:
        for chunk in _iter_stream_json(proc):
            produced = True
            yield chunk
        code = proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        raise ChatError("the model took too long")
    finally:
        if proc.poll() is None:
            proc.kill()
        err_thread.join(timeout=2)

    if code not in (0, None) and not produced:
        err = "".join(stderr_chunks).strip()
        raise ChatError(err or f"agent exited with {code}")
