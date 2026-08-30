# sparetoken

**we deserve to share our tokens.**

Live: [sparetoken.shop](https://sparetoken.shop) · alias [wdtsot.shop](https://wdtsot.shop)

This is a public experiment, not a SaaS pitch. We pay for compute every month. Some days we use it. Some days we don’t. Unused capacity disappears. So we sell a leftover block: **R$5 · 5 hours · Grok 4.6 High Fast**, in the browser or over SSH.

Code: [github.com/sparetoken-shop/sparetoken](https://github.com/sparetoken-shop/sparetoken)

## Manifesto

We work with AI every day. We pay for compute every month.

Some days we use everything. Some days we don’t. Either way, unused capacity disappears.

That feels wasteful.

Useful intelligence should be easier to access. Skills should be easier to share. Experimentation should be cheap.

we deserve to share.

## Why the code is public

The interface, the session layer and the SSH tunnel are inspectable from this account — not a person, not a company.

- You can see what the web chat stores and what it does not.
- You can see how the SSH tunnel is isolated — and where it is still weak.
- You can verify we are **not** shipping a hidden prompt that harvests your keys or your conversation for resale.

Read **[PRIVACY.md](PRIVACY.md)** first. If a sentence on the site is stronger than that file, the file wins.

## What is in here

Python stdlib app (`server.py`) + SQLite schema + the landing + tests.

```bash
python3 -m unittest discover -s tests -v
```

| Path | What |
|---|---|
| `static/` | landing + chat |
| `server.py` `chat.py` `pay.py` `clock.py` `db.py` `credits.py` | web MVP |
| `run-agent.sh` `tunnel-gate.py` | how a guest SSH session starts |
| `tests/` | what we actually check |

Not in this repo: the live SQLite, guest session folders, payment links, WhatsApp numbers, host `auth.json`, or operational notes with customer PII.

## Honest limits (2026-08-30)

- Anonymous web chat still opens with a cookie. Paid resume can store prompt text so you can come back. We do not publish that diary and we do not show visitor A the chat of visitor B.
- SSH `agent-guest` is a ForceCommand into a bubblewrap + Cursor sandbox. It is **not** a login shell. It is also **not** finished auth — empty password is on the 0.2.9 list.
- The guest process uses the host Cursor login to call the model. That is the shared token. Unrelated host secrets (Google Workspace, Wrangler, SSH keys) must **not** be mounted into the guest. See PRIVACY.md.

## License

MIT. Fork it. The live VPS is ours; your fork is yours.
