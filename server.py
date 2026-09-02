#!/usr/bin/env python3
"""WDTSOT MVP HTTP server — static site + anonymous chat + health."""

from __future__ import annotations

import json
import os
import secrets
import threading
import time
from collections import defaultdict, deque
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import chat
import clock
import credits
import invite
import pay
import track
from db import (
    append_chat_turn,
    connect,
    get_or_create_session,
    latest_block_code,
    list_chat_turns,
    refund_free_message,
    try_consume_free_message,
    wallet,
    wallet_chat,
)

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
DATA = Path(os.environ.get("WDTSOT_DATA", str(ROOT / "data")))
HOST = os.environ.get("WDTSOT_HOST", "0.0.0.0")
PORT = int(os.environ.get("WDTSOT_PORT", "8787"))
COOKIE = "wdtsot_sid"
CHAT_COOKIE = "wdtsot_chat"
MAX_PROMPT = 4000
IP_LIMIT = (20, 60)  # 20 / minute
SESSION_LIMIT = (8, 60)

DB = connect(DATA / "wdtsot.sqlite")
DB_LOCK = threading.Lock()
AGENT_SEM = threading.Semaphore(2)
RATE: dict[str, deque[float]] = defaultdict(deque)
RATE_LOCK = threading.Lock()
HISTORY: dict[str, list[tuple[str, str]]] = defaultdict(list)
HIST_LOCK = threading.Lock()


def _allow(key: str, limit: tuple[int, int]) -> bool:
    n, window = limit
    now = time.time()
    with RATE_LOCK:
        q = RATE[key]
        while q and now - q[0] > window:
            q.popleft()
        if len(q) >= n:
            return False
        q.append(now)
        return True


def _new_token() -> str:
    return secrets.token_urlsafe(24)


class Handler(BaseHTTPRequestHandler):
    server_version = "wdtsot/1.0"

    def log_message(self, fmt: str, *args) -> None:
        # Do not log request bodies or cookies.
        sys_stderr = __import__("sys").stderr
        path = urlparse(self.path).path
        sys_stderr.write("%s %s %s\n" % (self.address_string(), self.command, path))

    def _client_ip(self) -> str:
        xff = self.headers.get("X-Forwarded-For", "")
        if xff:
            return xff.split(",")[0].strip()[:80]
        return self.client_address[0]

    def _send(
        self,
        code: int,
        body: bytes,
        content_type: str,
        extra: list[tuple[str, str]] | None = None,
        cookie: str | None = None,
    ) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Cache-Control", "no-store" if content_type.startswith("application/json") else "public, max-age=120")
        if cookie:
            if isinstance(cookie, (list, tuple)):
                for item in cookie:
                    self.send_header("Set-Cookie", item)
            else:
                self.send_header("Set-Cookie", cookie)
        for k, v in extra or []:
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, code: int, payload: dict, cookie: str | list[str] | None = None) -> None:
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._send(code, raw, "application/json; charset=utf-8", cookie=cookie)

    def _cookie_secure(self) -> str:
        proto = (self.headers.get("X-Forwarded-Proto") or "").split(",")[0].strip()
        return "; Secure" if proto == "https" else ""

    def _cookie_header(self, token: str) -> str:
        return f"{COOKIE}={token}; Path=/; HttpOnly; SameSite=Lax; Max-Age=31536000{self._cookie_secure()}"

    def _chat_cookie_header(self, chat_id: str) -> str:
        return (
            f"{CHAT_COOKIE}={chat_id}; Path=/; HttpOnly; SameSite=Lax; Max-Age=31536000"
            f"{self._cookie_secure()}"
        )

    def _jar(self) -> SimpleCookie:
        jar = SimpleCookie()
        if "Cookie" in self.headers:
            jar.load(self.headers["Cookie"])
        return jar

    def _chat_cookie(self) -> str:
        jar = self._jar()
        return jar[CHAT_COOKIE].value if CHAT_COOKIE in jar else ""

    def _pack_cookies(self, token: str | None, chat_id: str | None, *, force_sid: bool = False) -> list[str] | None:
        out: list[str] = []
        if token and force_sid:
            out.append(self._cookie_header(token))
        if chat_id:
            out.append(self._chat_cookie_header(chat_id))
        return out or None

    def _session(self):
        jar = self._jar()
        token = jar[COOKIE].value if COOKIE in jar else ""
        created = False
        if not token or len(token) < 16:
            token = _new_token()
            created = True
        sid = token[:32]
        with DB_LOCK:
            row = get_or_create_session(DB, token, sid)
            w = wallet(DB, row["id"])
            block = latest_block_code(DB, row["id"])
        remaining_msgs = max(0, int(row["free_messages_limit"]) - int(row["free_messages_used"]))
        remaining_s = credits.remaining_seconds(w["purchased_seconds"], w["consumed_seconds"])
        return row, token, created, remaining_msgs, remaining_s, block

    def _bind_chat(
        self,
        wallet_id: str,
        *,
        fresh: bool = False,
        resume_id: str | None = None,
    ) -> tuple[dict, str | None]:
        snap = clock.snapshot(DB, wallet_id)
        wanted = self._chat_cookie()
        resume_id = (resume_id or "").strip()
        if resume_id and wallet_chat(DB, wallet_id, resume_id):
            if snap.get("active_chat_id") != resume_id and snap.get("paid"):
                snap = clock.use_chat(DB, wallet_id, resume_id)
            return snap, resume_id
        if snap.get("exhausted"):
            return snap, wanted if wanted and wallet_chat(DB, wallet_id, wanted) else snap.get("active_chat_id")
        if not snap.get("paid"):
            return snap, None
        if wanted and wallet_chat(DB, wallet_id, wanted) and not fresh:
            if snap.get("active_chat_id") != wanted:
                snap = clock.use_chat(DB, wallet_id, wanted)
            return snap, wanted
        if fresh:
            snap = clock.start_another(DB, wallet_id)
        return snap, snap.get("active_chat_id")

    def _with_active(self, snap: dict, chat_id: str | None) -> dict:
        if chat_id:
            snap = dict(snap)
            snap["active_chat_id"] = chat_id
        return snap

    def _session_body(
        self,
        row,
        remaining_msgs,
        snap,
        block,
        *,
        messages: list | None = None,
        resumed: bool = False,
    ) -> dict:
        code = snap["block_code"] or block
        chat_id = snap.get("active_chat_id")
        resume_url = (
            f"https://wdtsot.shop/?code={code}&resume={chat_id}" if code and chat_id else snap["return_url"]
        )
        return {
            "ok": True,
            "model": "GROK 4.6 High Fast",
            "remaining_messages": remaining_msgs,
            "message_limit": int(row["free_messages_limit"]),
            "remaining_seconds": snap["remaining_seconds"],
            "remaining_clock": snap["remaining_clock"],
            "used_seconds": snap["used_seconds"],
            "used_clock": snap["used_clock"],
            "paid": snap["paid"],
            "exhausted": snap["exhausted"],
            "warn": snap["warn"],
            "session_status": snap["session_status"],
            "processing": snap["processing"],
            "block_code": code,
            "invite_url": invite.invite_url(code),
            "return_url": snap["return_url"],
            "resume_url": resume_url,
            "chats": snap["chats"],
            "active_chat_id": chat_id,
            "resumed": resumed,
            "messages": messages or [],
            "pay_url": pay.PAY_URL,
            "ssh": "ssh -t agent-guest@wdtsot.shop",
        }

    def do_HEAD(self) -> None:
        self.do_GET()

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path in {"/api/health", "/health"}:
            self._json(
                200,
                {
                    "ok": True,
                    "service": "sparetoken",
                    "model": chat.MODEL,
                    "ssh": "ssh agent-guest@wdtsot.shop",
                },
            )
            return
        if path == "/api/track/summary":
            with DB_LOCK:
                counts = track.summarize(DB)
            self._json(200, {"ok": True, **counts})
            return
        if path == "/api/session":
            row, token, created, remaining_msgs, remaining_s, block = self._session()
            q = parse_qs(urlparse(self.path).query)
            code = (q.get("code") or [""])[0]
            resume = (q.get("resume") or [""])[0].strip()
            fresh = (q.get("fresh") or [""])[0] in {"1", "true", "yes"}
            cookies: list[str] = []
            if created:
                cookies.append(self._cookie_header(token))
            with DB_LOCK:
                if code:
                    try:
                        result = pay.claim(DB, row["id"], contact="", code=code, pay_url="")
                    except pay.PayError:
                        result = None
                    if result and result.get("paid"):
                        row = get_or_create_session(DB, result["public_token"], result["session_id"])
                        token = result["public_token"]
                        created = True
                        cookies = [self._cookie_header(token)]
                snap, chat_id = self._bind_chat(row["id"], fresh=fresh and not resume, resume_id=resume)
            if chat_id:
                cookies.append(self._chat_cookie_header(chat_id))
            self._json(
                200,
                self._session_body(
                    row,
                    remaining_msgs,
                    self._with_active(snap, chat_id),
                    block,
                    messages=[],
                    resumed=False,
                ),
                cookie=cookies or None,
            )
            return
        self._static(path)

    def _read_json(self, max_len: int) -> dict | None:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0 or length > max_len:
            return None
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None
        return payload if isinstance(payload, dict) else None

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/track":
            self._track()
            return
        if path == "/api/pay":
            self._pay()
            return
        if path == "/api/claim":
            self._claim()
            return
        if path == "/api/clock":
            self._clock()
            return
        if path != "/api/chat":
            self._json(404, {"ok": False, "error": "not found"})
            return
        if not _allow(f"ip:{self._client_ip()}", IP_LIMIT) or not _allow(
            f"sess:{self.headers.get('Cookie', '')[:40]}", SESSION_LIMIT
        ):
            self._json(429, {"ok": False, "error": "calma. tente de novo em um minuto."})
            return
        payload = self._read_json(MAX_PROMPT + 512)
        if payload is None:
            self._json(400, {"ok": False, "error": "pedido inválido"})
            return
        text = str(payload.get("message") or "").strip()
        if not text:
            self._json(400, {"ok": False, "error": "escreva alguma coisa"})
            return
        if len(text) > MAX_PROMPT:
            self._json(400, {"ok": False, "error": "mensagem longa demais"})
            return
        row, token, created, remaining_msgs, remaining_s, _block = self._session()
        with DB_LOCK:
            snap, chat_id = self._bind_chat(row["id"])
        paid = snap["purchased_seconds"] > 0
        if paid:
            try:
                with DB_LOCK:
                    clock.ensure_can_chat(DB, row["id"])
                    snap = clock.start_processing(
                        DB, row["id"], channel="web", label="web", chat_id=chat_id
                    )
                    chat_id = snap.get("active_chat_id") or chat_id
            except clock.ClockError as exc:
                self._json(
                    402,
                    {
                        "ok": False,
                        "error": str(exc),
                        "exhausted": True,
                        "remaining_seconds": 0,
                        "remaining_clock": "00:00:00",
                        "pay_url": pay.PAY_URL,
                    },
                    cookie=self._cookie_header(token) if created else None,
                )
                return
        if not paid and remaining_msgs <= 0:
            self._json(
                402,
                {
                    "ok": False,
                    "error": "você usou as 50 mensagens desta experiência. pague R$5 para liberar 5h.",
                    "remaining_messages": 0,
                    "pay_url": pay.PAY_URL,
                },
                cookie=self._cookie_header(token) if created else None,
            )
            return
        remaining = remaining_msgs
        if not paid:
            with DB_LOCK:
                ok, used, limit = try_consume_free_message(DB, row["id"])
            if not ok:
                self._json(
                    402,
                    {
                        "ok": False,
                        "error": "você usou as 50 mensagens desta experiência. pague R$5 para liberar 5h.",
                        "remaining_messages": 0,
                        "pay_url": pay.PAY_URL,
                    },
                )
                return
            remaining = max(0, limit - used)
        hist_key = chat_id or row["id"]
        with DB_LOCK:
            prior = list_chat_turns(DB, hist_key, limit=16) if chat_id else []
        with HIST_LOCK:
            hist = [(t["role"], t["body"]) for t in prior] if prior else list(HISTORY[hist_key])
            HISTORY[hist_key] = hist + [("user", text[:MAX_PROMPT])]
            if len(HISTORY[hist_key]) > 16:
                HISTORY[hist_key] = HISTORY[hist_key][-16:]
            hist = list(HISTORY[hist_key][:-1])
        if chat_id:
            with DB_LOCK:
                append_chat_turn(DB, chat_id, "user", text[:MAX_PROMPT])

        workspace = DATA / "chats" / hist_key
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Accel-Buffering", "no")
        if created:
            self.send_header("Set-Cookie", self._cookie_header(token))
        if chat_id:
            self.send_header("Set-Cookie", self._chat_cookie_header(chat_id))
        self.end_headers()

        assembled: list[str] = []

        def write_event(obj: dict) -> None:
            raw = f"data: {json.dumps(obj, ensure_ascii=False)}\n\n".encode("utf-8")
            self.wfile.write(raw)
            self.wfile.flush()

        write_event(
            {
                "remaining_messages": remaining,
                "remaining_seconds": snap["remaining_seconds"],
                "remaining_clock": snap["remaining_clock"],
                "paid": snap["paid"],
            }
        )
        if not AGENT_SEM.acquire(timeout=25):
            write_event({"error": "muita gente ao mesmo tempo. tente de novo em instantes."})
            write_event({"done": True, "remaining_messages": remaining, "remaining_clock": snap["remaining_clock"]})
            return
        try:
            for chunk in chat.stream_reply(text, workspace, history=hist):
                if chunk:
                    assembled.append(chunk)
                    write_event({"text": chunk})
            reply = "".join(assembled).strip()
            if not reply:
                write_event({"text": "não consegui responder agora. tente de novo."})
            else:
                with HIST_LOCK:
                    HISTORY[hist_key].append(("assistant", reply[:8000]))
                    if len(HISTORY[hist_key]) > 16:
                        HISTORY[hist_key] = HISTORY[hist_key][-16:]
                if chat_id:
                    with DB_LOCK:
                        append_chat_turn(DB, chat_id, "assistant", reply[:8000])
        except chat.ChatError:
            if not paid:
                with DB_LOCK:
                    remaining = refund_free_message(DB, row["id"])
            write_event({"error": "o modelo não respondeu desta vez. tente de novo.", "remaining_messages": remaining})
        except BrokenPipeError:
            if paid:
                with DB_LOCK:
                    clock.end_processing(DB, row["id"])
            return
        except Exception:
            if not paid:
                with DB_LOCK:
                    remaining = refund_free_message(DB, row["id"])
            write_event({"error": "algo quebrou do nosso lado. já vamos olhar.", "remaining_messages": remaining})
        finally:
            AGENT_SEM.release()
            if paid:
                with DB_LOCK:
                    snap = clock.end_processing(DB, row["id"])
        try:
            with DB_LOCK:
                snap = clock.snapshot(DB, row["id"])
            write_event(
                {
                    "done": True,
                    "remaining_messages": remaining,
                    "remaining_seconds": snap["remaining_seconds"],
                    "remaining_clock": snap["remaining_clock"],
                    "exhausted": snap["exhausted"],
                    "warn": snap["warn"],
                }
            )
        except BrokenPipeError:
            return

    def _track(self) -> None:
        if not _allow(f"track:{self._client_ip()}", (40, 60)):
            self._json(429, {"ok": False, "error": "calma."})
            return
        payload = self._read_json(2048) or {}
        with DB_LOCK:
            ok = track.record_event(DB, payload)
        self._json(200 if ok else 400, {"ok": ok})

    def _pay(self) -> None:
        if not _allow(f"pay:{self._client_ip()}", SESSION_LIMIT):
            self._json(429, {"ok": False, "error": "calma. tente de novo em um minuto."})
            return
        row, token, created, remaining_msgs, remaining_s, block = self._session()
        try:
            with DB_LOCK:
                checkout = pay.start_checkout(DB, row["id"])
        except pay.PayError as exc:
            self._json(400, {"ok": False, "error": str(exc)})
            return
        self._json(
            200,
            {
                "ok": True,
                "pay_url": checkout["pay_url"],
                "block_code": checkout["block_code"],
                "amount_brl": checkout["amount_brl"],
                "seconds": checkout["seconds"],
                "status": checkout["status"],
                "paid": remaining_s > 0,
                "remaining_messages": remaining_msgs,
                "remaining_seconds": remaining_s,
                "remaining_clock": credits.format_hms(remaining_s),
            },
            cookie=self._cookie_header(token) if created else None,
        )

    def _claim(self) -> None:
        if not _allow(f"claim:{self._client_ip()}", SESSION_LIMIT):
            self._json(429, {"ok": False, "error": "calma. tente de novo em um minuto."})
            return
        payload = self._read_json(2048)
        if payload is None:
            self._json(400, {"ok": False, "error": "pedido inválido"})
            return
        row, token, created, _msgs, _secs, _block = self._session()
        try:
            with DB_LOCK:
                result = pay.claim(
                    DB,
                    row["id"],
                    contact=str(payload.get("contact") or ""),
                    code=str(payload.get("code") or ""),
                    pay_url=str(payload.get("pay_url") or ""),
                )
        except pay.PayError as exc:
            self._json(400, {"ok": False, "error": str(exc)})
            return
        switch = result["public_token"] != token
        cookies: list[str] = []
        if created or switch:
            cookies.append(self._cookie_header(result["public_token"]))
        with DB_LOCK:
            snap, chat_id = self._bind_chat(result["session_id"], fresh=True)
        if chat_id:
            cookies.append(self._chat_cookie_header(chat_id))
        snap = self._with_active(snap, chat_id)
        self._json(
            200,
            {
                "ok": True,
                "model": "GROK 4.6 High Fast",
                "paid": snap["paid"],
                "block_code": snap["block_code"] or result["block_code"],
                "invite_url": invite.invite_url(snap["block_code"] or result["block_code"]),
                "remaining_seconds": snap["remaining_seconds"],
                "remaining_clock": snap["remaining_clock"],
                "used_clock": snap["used_clock"],
                "exhausted": snap["exhausted"],
                "session_status": snap["session_status"],
                "processing": snap["processing"],
                "return_url": snap["return_url"],
                "resume_url": (
                    f"https://wdtsot.shop/?code={snap['block_code'] or result['block_code']}&resume={chat_id}"
                    if (snap.get("block_code") or result.get("block_code")) and chat_id
                    else snap["return_url"]
                ),
                "chats": snap["chats"],
                "active_chat_id": snap.get("active_chat_id"),
            },
            cookie=cookies or None,
        )

    def _clock(self) -> None:
        if not _allow(f"clock:{self._client_ip()}", (30, 60)):
            self._json(429, {"ok": False, "error": "calma. tente de novo em um minuto."})
            return
        payload = self._read_json(512)
        if payload is None:
            payload = {}
        action = str(payload.get("action") or "tick")
        row, token, created, remaining_msgs, _secs, _block = self._session()
        chat_id = self._chat_cookie()
        try:
            with DB_LOCK:
                if action == "new":
                    snap = clock.start_another(DB, row["id"])
                    chat_id = snap.get("active_chat_id") or chat_id
                elif action == "rename":
                    snap = clock.rename_chat(
                        DB,
                        row["id"],
                        str(payload.get("id") or chat_id or ""),
                        str(payload.get("title") or payload.get("label") or ""),
                    )
                elif action in {"use", "select"}:
                    snap = clock.use_chat(DB, row["id"], str(payload.get("id") or ""))
                    chat_id = snap.get("active_chat_id") or chat_id
                elif action == "pause":
                    snap = clock.end_processing(DB, row["id"])
                else:
                    snap = clock.snapshot(DB, row["id"])
                    if not (chat_id and wallet_chat(DB, row["id"], chat_id)):
                        chat_id = snap.get("active_chat_id")
        except clock.ClockError as exc:
            self._json(402, {"ok": False, "error": str(exc), "exhausted": True, "pay_url": pay.PAY_URL})
            return
        cookies: list[str] = []
        if created:
            cookies.append(self._cookie_header(token))
        if chat_id:
            cookies.append(self._chat_cookie_header(chat_id))
        snap = self._with_active(snap, chat_id)
        code = snap.get("block_code")
        resume_url = (
            f"https://wdtsot.shop/?code={code}&resume={chat_id}" if code and chat_id else snap.get("return_url")
        )
        self._json(
            200,
            {
                "ok": True,
                "model": "GROK 4.6 High Fast",
                "paid": snap["paid"],
                "exhausted": snap["exhausted"],
                "warn": snap["warn"],
                "session_status": snap["session_status"],
                "processing": snap["processing"],
                "remaining_seconds": snap["remaining_seconds"],
                "remaining_clock": snap["remaining_clock"],
                "used_seconds": snap["used_seconds"],
                "used_clock": snap["used_clock"],
                "block_code": snap["block_code"],
                "invite_url": invite.invite_url(snap.get("block_code")),
                "return_url": snap["return_url"],
                "resume_url": resume_url,
                "chats": snap["chats"],
                "active_chat_id": snap.get("active_chat_id"),
                "remaining_messages": remaining_msgs,
            },
            cookie=cookies or None,
        )

    def _static(self, path: str) -> None:
        if path == "/":
            rel = "index.html"
        else:
            rel = path.lstrip("/")
        candidate = (STATIC / rel).resolve()
        if not str(candidate).startswith(str(STATIC.resolve())) or not candidate.is_file():
            self._json(404, {"ok": False, "error": "not found"})
            return
        data = candidate.read_bytes()
        ctype = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "text/javascript; charset=utf-8",
            ".svg": "image/svg+xml",
            ".json": "application/json; charset=utf-8",
            ".txt": "text/plain; charset=utf-8",
            ".ico": "image/x-icon",
            ".woff2": "font/woff2",
        }.get(candidate.suffix, "application/octet-stream")
        extra = []
        if candidate.suffix == ".html":
            extra.append(
                (
                    "Content-Security-Policy",
                    "default-src 'self'; img-src 'self' data:; style-src 'self' https://fonts.googleapis.com; "
                    "font-src https://fonts.gstatic.com; connect-src 'self'; frame-ancestors 'none'",
                )
            )
        self._send(200, data, ctype, extra=extra)


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"wdtsot listening on {HOST}:{PORT}", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
