# Security

This repo is the public copy of a **live** experiment at [sparetoken.shop](https://sparetoken.shop).

## Please do this

- Read [PRIVACY.md](PRIVACY.md) and the tunnel script (`run-agent.sh`) before assuming isolation.
- If a guest can read host credentials, another guest’s workspace, or dump the host Cursor `auth.json`, open a **private** report — never a public issue with a working exploit.
- Fixes belong in this repo. Proof-of-concept exploits against the live VPS do not.

## Please do not do this

- Do not publish a working exploit, scanner, or credential dump against sparetoken.shop / wdtsot.shop / the Oracle host.
- Do not brute the empty-password SSH in public write-ups. We already know `Accepted none` is on the 0.2.9 list.
- Do not open a public issue that contains someone else’s prompt, WhatsApp, or payment link.

## What we will fix first

1. Host secrets other than the shared Cursor token must not be in the guest mount.
2. WhatsApp (or equivalent) before paid chat and before the agent starts — roadmap 0.2.9.
3. No hidden harvest prompt. Ever.
