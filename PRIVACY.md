# Privacy

This file is the contract. The landing page is a summary. If they disagree, believe this.

sparetoken is an experiment in sharing leftover AI compute. Sharing a **token of time** is the product. Sharing **your prompt, your keys, or someone else’s keys** is not.

## What we promise

1. **We do not sell conversations.** No broker, no training-data side deal, no “we improve the model with your chats” clause.
2. **We do not show your prompt to another visitor.** There is no public feed of other people’s chats.
3. **We do not hide a system prompt that harvests credentials.** The guest workspace gets a visible `AGENTS.md` that says the opposite: do not read host config, do not save other people’s keys, do not exfiltrate `.env` / `auth.json` / SSH keys.
4. **Host secrets that are not the shared Cursor token stay off the guest mount.** Google Workspace (`~/.config/gws`), Wrangler, and `~/.ssh` must not appear inside the bubblewrap home.
5. **Request bodies and cookies are not written to the app log.** `server.py` overrides `log_message` for that reason.

## What we actually store today

| Data | Where | Why |
|---|---|---|
| Anonymous cookie `wdtsot_sid` | browser + `user_sessions` | count the 50 free web messages |
| Free web turns | `turns` (role + timestamp, **no body**) | count, not a diary |
| Paid web resume | `chat_turns.body` + `data/chats/<id>/` on the VPS | so `?code=&resume=` can reopen **your** thread |
| In-memory web history | process RAM, last 16 turns | continuity inside one server process |
| SSH gate (block code only) | `guest-sessions/guests.jsonl` on the VPS | the `wdtsot-XXXX` that claimed the paid block |
| SSH transcripts | that session’s `cursor-state/` only | Cursor needs them to resume **your** session |
| Pix / conta.vc | charge URL + open/closed status | credit 5h after you pay, once |
| First-party events `visit` / `pay_click` / `claim_ok` | `track_events` (UTM + optional `wdtsot-XXXX`) | count landings and Pix clicks. No email. No phone. No third-party pixel. `GET /api/track/summary` exposes **counts only** — no codes, no UTM dump. |

The public git tree does **not** contain the SQLite, `guests.jsonl`, or any chat body.

## What is not private yet (do not over-claim)

- **Web:** if you are on a paid block and we store resume text, that text lives on our VPS disk. It is yours, not a public diary — and it is still on our disk. Delete-on-request is not automated yet.
- **SSH:** the agent binary still needs the host Cursor login (`~/.config/cursor`) to spend the shared token. A guest with a shell inside that namespace can *try* to read that file. We deny it in the Cursor allowlist and we do not mount unrelated secrets. Dumping the raw host credential is a bug we are closing, not a feature. Do not paste other people’s keys into the session either.
- **Auth is incomplete.** `agent-guest` currently accepts an empty password; the gate after login asks only for the block code. A leaked `wdtsot-XXXX` is still the wallet.

## SSH tunnel — how credentials are supposed to work

```
internet
  → ssh agent-guest@sparetoken.shop
  → ForceCommand (no bash)
  → collect the block code (wdtsot-XXXX)   ← the wallet, not your civil name
  → bubblewrap
       home is a tmpfs
       only ~/.local (agent binary) and ~/.config/cursor (shared token) are remounted
       ~/.config/gws, ~/.ssh, wrangler: not mounted
       your workspace is the only writable tree
  → Cursor agent --sandbox enabled --trust
       AGENTS.md in the workspace forbids reading host config or saving third-party secrets
```

There is **no** second, hidden prompt that copies your messages to the founder. Session metadata (duration, model, block code) is logged so we can credit the 5 hours. Prompt text from SSH stays in that session folder.

If you find a path where a guest can read `gws`, Wrangler, or another user’s workspace, that is a vulnerability — see [SECURITY.md](SECURITY.md).

## Your keys, not ours

If you paste an OpenAI key, a `.pem`, or someone else’s Cursor login into the chat or the SSH workspace, we cannot unread it. Don’t. The shared token is already paid for. The agent should refuse to persist host or third-party credentials. If it doesn’t, file a private report.
