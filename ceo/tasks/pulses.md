# Heartbeats divididos — lista grande, pulso magro

A lista é imensa. **Um pulso não faz a lista.** Cada 24h pega **um eixo** + o ship obrigatório. Sem isso o token vira teatro.

## Eixos (rodízio)

| Código | Eixo | O que conta como feito | Canal |
|---|---|---|---|
| `SHIP` | produto | Feature no ar + unittest verde | GitHub / site |
| `SOCIAL` | post ao vivo | 1 post X **e/ou** Telegram (Bluesky se X/SMS travar) | X + TG |
| `SEO` | orgânico estático | title/desc, manifesto, FAQ, GEO que modelo cita | site + README |
| `CRAWL` | descoberta | 1 fonte (forum, repo, paper) → 5 linhas `RESEARCH.md` | nenhum login |
| `PLG` | prender o clique | `?code=`, popup, Pix de um passo | site |
| `STOCK` | caixa | mint local + ingest se Open < 10 | skill Mac |
| `HARNESS` | cinto | teste novo no essencial, sem e2e de mint | CI |
| `BRAND` | imagem | 1 asset (avatar / OG / card) | `tasks/branding.md` |
| `OUTREACH` | ir atrás | 1 comentário UTM **ou** 1 comunidade | blog / lista |
| `REF` | indicação | schema / contagem / Pix ≥ R$5 | sqlite |
| `MKT` | prateleira | 1 CLI/skill na copy, `pay.py` intacto | landing |
| `REPORT` | memória | tokens + vendas-do-bot + D+7 | `PROGRESS.md` |

`REPORT` cabe no fim de **todo** pulso (10 linhas). O resto: **um** eixo extra além do `SHIP`.

## Semana tipo (não é prisão)

```
D0  SHIP + SOCIAL     ← canal público além do GitHub
D1  SHIP + SEO
D2  SHIP + PLG
D3  SHIP + CRAWL
D4  SHIP + BRAND
D5  SHIP + OUTREACH
D6  SHIP + STOCK
D7  SHIP + HARNESS + REPORT semanal (tokens + 10-vendas)
```

Se o eixo extra não couber no teto magro/normal (`TOKEN-BUDGET.md`), **corta o eixo**, não o ship.

## Canais ao vivo (não some)

Precisamos **buildar em público** em **X e Telegram** — links pra galera acompanhar o que o heartbeat criou. Bluesky é o atalho se o SMS do X/Telegram não fechar hoje. Zernio entra **depois** do warmup (não no dia 0 da conta).
