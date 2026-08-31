# Go-live — estado real (31/08)

Sem senha neste arquivo. Cofre X = `.anon-secrets/` no Mac (gitignored). Semana do builder: `AWAY.md`.

## No ar

1. App: https://sparetoken.shop · SKU R$5 · 5h · fuzzy · código do bloco = login
2. Repo: https://github.com/sparetoken-shop/sparetoken
3. X: @sparetoken (warmup). Telegram: depois
4. Meta mês 1: **10 vendas pelo bot**

## Onde mora

| Recurso | Onde |
|---|---|
| Loja / pagar / relógio | VPS `…/wdtsot` · `wdtsot.service` |
| Cérebro `ceo/` | git + VPS (cópia). Cron **ligado** |
| 11:30 venda | `sparetoken-sell.timer` → `sell.sh` |
| 23:30 produto | `sparetoken-heartbeat.timer` → `heartbeat.sh` |
| Sessão X | Mac only. VPS escreve fila |
| Mint conta.vc | Chrome local + skill. VPS só lê |

## Proibido na VPS

Git write. Cookie de X. Zernio. Segundo gateway. Playwright em `charge/new`.
