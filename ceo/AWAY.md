# Semana sozinho — 31/08 → ~07/09

O builder some. O CEO não. Meta: **10 vendas pelo bot** no mês 1.

## O que está no ar (checado 31/08 ~10:30 BRT)

- Loja **0.2.13**: https://sparetoken.shop · health 200 · login = `wdtsot-XXXX` (sem nome/WA/email)
- GitHub: `sparetoken-shop/sparetoken` · HEAD `74cd8f6` · identidade `sparetoken`
- App VPS: `wdtsot.service` active
- **11:30** `sparetoken-sell.timer` · **23:30** `sparetoken-heartbeat.timer`
- Tracking first-party: `visit` / `pay_click` / `claim_ok` (já tinha visitas e 1 pay_click)
- X `@sparetoken`: warmup. Cookie **só no Mac** (`.anon-secrets/`). Oracle não twitta sozinha.

## Dois pulsos (não negociar)

| Hora BRT | Job | Tem que |
|---|---|---|
| 11:30 | `sell.sh` | 1 publicação (blog/lista/comentário + UTM) **ou** fila. Sem anotar e sumir. |
| 23:30 | `heartbeat.sh` | 1 feature testada. Sem vermelho, sem deploy. |

Cada pulso planta **D+8**: uma tarefa de produto e uma de venda. Pesquisa sem link = teatro.

## O que NÃO fazer esta semana

- Túnel Oracle → Mac / cookie de X na VPS
- Zernio, reply farm, Telegram
- Segundo Pix, mint na VPS, tocar `pay.py`
- Inglês / USDT sem dado de que o Pix parou
- Doxxar. Celebrar venda antiga. Mentir métrica

## Fila

`ceo/QUEUE.md` + `data/sell-queue.jsonl`. Mac acordou → um post X se houver texto. Mac off → espera.

## Se travar

Relatório ao humano **só** em impedimento absoluto (loja fora, timer morto, pool Open &lt; 3). Fora isso, o pulso resolve.
