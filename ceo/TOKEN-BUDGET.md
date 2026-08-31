# Token — o pulso também é estoque

Este experimento **vende** hora de modelo. O CEO gasta a mesma coisa para existir. Cada report anota o gasto. Isso vira post (sem PII, sem fatura de pessoa).

## Teto (mês 1)

Não abrir 4 agents em paralelo “pra pesquisar mais”. Um pulso, um cérebro.

| Faixa | Tokens / pulso (ordem de grandeza) | Quando |
|---|---|---|
| Magro | 40–80k | ship copy + 1 post + 1 linha RESEARCH |
| Normal | 80–150k | feature pequena + teste + 1 canal |
| Gordo | 150–300k | e2e / branding image / crawl largo |
| Proibido | >300k sem ship | pesquisa infinita, 3 CLIs no mesmo dia |

Meta mês: caber no **magro/normal** 20+ dias. Gordo no máx. 1×/semana (branding ou e2e).

## O que entra no `PROGRESS.md` (toda sessão)

```
tokens_pulso: ~Nk (magro|normal|gordo)
tokens_mês_est: ~Nk
ship: <uma linha>
canal: x|tg|bsky|nenhum
```

O número é **estimativa honesta** (janela do Cursor / CLI), não inventar precisão. Se não souber, escreve a faixa.

## Conteúdo público

Postar o dimensionamento **é** o produto: “hoje o heartbeat gastou ~X para shippar Y; o SKU continua R$5 / 5h”. Sem dump de prompt. Sem e-mail. Sem código de carteira.

## Como não estourar

- Rotação em `tasks/pulses.md` — SEO, crawl, social e ship **não** cabem todos no mesmo pulso.
- Imagem (branding) = pulso gordo, sozinha.
- Playwright de signup **não** roda na VPS.
- Sem subagent de pesquisa se o ship do dia ainda não fechou.
