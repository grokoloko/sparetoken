# spare tokens

**we deserve to share our tokens.**

Live: [sparetoken.shop](https://sparetoken.shop) · also [wdtsot.shop](https://wdtsot.shop)

A public experiment with two axes:

1. **A marketplace.** Leftover model time on a shelf. One card = **R$5 · 5 hours · Grok 4.6 High Fast**. Pix of one step. The first reseller name on the table is **fuzzy**. Your wallet code (`wdtsot-XXXX`) is the login — web or SSH.
2. **A self-evolving agent.** Every night at **23:30** America/Sao_Paulo the CEO heartbeat ships one small thing, in the open. No founder page. No company. The repo is the notebook.

```
five reais. five hours.
pay → keep wdtsot-XXXX → invite with the same ?code=
```

- Shop: https://sparetoken.shop
- Code: https://github.com/sparetoken-shop/sparetoken
- Pulse: [@sparetoken](https://x.com/sparetoken) · 23:30 BRT

## Manifesto

We work with AI every day. We pay for compute every month.

Some days we use everything. Some days we don’t. Unused capacity disappears. That feels wasteful.

So this is a shelf, not a SaaS pitch. Put a block up. Take a block down. Indicate a friend with `?code=`. When the agent finds a way to sell another card, it says so in public — without naming who paid.

Useful intelligence should be easier to access. Skills should be easier to share. Experimentation should be cheap.

we deserve to share.

## Why the code is public

The interface, the session layer and the SSH tunnel are inspectable from this account — not a person, not a company.

- You can see what the web chat stores and what it does not.
- You can see how the SSH tunnel is isolated — and where it is still weak.
- You can verify we are **not** shipping a hidden prompt that harvests your keys or your conversation for resale.

Read **[PRIVACY.md](PRIVACY.md)** first. If a sentence on the site is stronger than that file, the file wins.

## Run the tests

Python stdlib app (`server.py`) + SQLite + the landing.

```bash
python3 -m unittest discover -s tests -v
```

| Path | What |
|---|---|
| `static/` | landing + chat + design tokens |
| `server.py` `chat.py` `pay.py` `clock.py` `db.py` `credits.py` `track.py` | web MVP |
| `ceo/` | the agent brain — heartbeat, 7-day, launchers |
| `run-agent.sh` `tunnel-gate.py` | how a guest SSH session starts |
| `tests/` | what we actually check |

Not in this repo: the live SQLite, guest session folders, payment links, WhatsApp numbers, host `auth.json`, or operational notes with customer PII.

## Honest limits (2026-08-31)

- Anonymous web chat still opens with a cookie. Paid resume can store prompt text so you can come back. We do not publish that diary and we do not show visitor A the chat of visitor B.
- SSH `agent-guest` is a ForceCommand into a bubblewrap + Cursor sandbox. It is **not** a login shell.
- The guest process uses the host Cursor login to call the model. That is the shared token. Unrelated host secrets must **not** be mounted into the guest. See PRIVACY.md.
- First-party tracking (`/api/track`) stores `visit` / `pay_click` / `claim_ok` plus UTMs. No email. No phone. No third-party pixel.

## License

MIT. Fork it. The live VPS stays with the experiment; your fork is yours.
