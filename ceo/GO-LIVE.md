# Go-live — o que está de pé / o que vai pra Oracle

Sem senha neste arquivo. Cofre = `.anon-secrets/` no Mac (gitignored).

## Meta do primeiro heartbeat real

1. Código do cérebro no GitHub (`sparetoken-shop`) — heartbeat D0 / 0.2.9.
2. App no ar: https://sparetoken.shop · prateleira de cards · reseller **fuzzy** (nome, não alias).
3. Primeiro post público além do GitHub: sessão X **@sparetoken** no Mac (Playwright). Telegram ainda em aberto.
4. 10 vendas **pelo bot** no mês 1. Anônimo.

## Onde cada coisa mora

| Recurso | Onde | Vai pra Oracle? |
|---|---|---|
| Loja / pagar / relógio | VPS canônica `…/wdtsot` = live | Já está. `server.py`/`pay.py` **iguais** ao Mac |
| Cérebro `ceo/` | só Mac, uncommitted | **Sim, no próximo passo** — scp/git, sem cron até “publique” |
| Sessão X + senha + cookies | `.anon-secrets/` + `.anon-chrome-social/` | **Não.** Cookie na VPS queima a conta |
| Mint conta.vc | Chrome local + skill | **Não.** VPS só lê `/pay/fuzzy` |
| Primeiro post | Mac, sessão salva | Oracle **manda** o texto; o post sai daqui |
| Zernio | ainda não | Depois do warmup (3–7d), aí sim API na VPS |

## Próximo passo (Oracle) — ainda sem commit do CEO

1. Copiar `ceo/` (e só isso) pro guest/workspace da VPS, **leitura + dry `launch/heartbeat.sh`**.
2. Não ligar cron. Não levar `.anon-*`. Não tocar `pay.py`.
3. Voltar ao Mac: commit da orientação do CEO no `sparetoken-shop` quando o humano mandar.

## Primeiro post (quando o pulso for real)

Texto do ship + `https://sparetoken.shop/?utm_source=x&utm_medium=social&utm_campaign=heartbeat`. Sem PII. Sem “dono”. Sem segundo Pix. Sem Zernio no dia 0 desta conta.
