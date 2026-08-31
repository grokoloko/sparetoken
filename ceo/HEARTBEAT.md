# Heartbeat v1 — um pulso / 24h às **23:30** (America/Sao_Paulo)

Horário oficial. Uma feature no ar por pulso. **Pulso sem feature = pulso morto.**

O cron na Oracle roda `launch/heartbeat.sh` (unittest + carimbo). O `cursor-agent` da VPS **não** entra no cron enquanto o login for conta pessoal — alma = anônimo. O cérebro vive; o CLI pessoal não.

## Loop

```
00  cron 23:30 America/Sao_Paulo → launch/heartbeat.sh
01  ler CEO.md (modelo de pensamento) + PAYMENT.md + docs/CONTA-CHARGES.md
02  mostrar ROADMAP-7D.md inteiro
03  20–40 min de pesquisa → append RESEARCH.md
04  TDD no essencial (unittest). Vermelho = para
05  SHIP a feature do dia D (obrigatório)
06  re-rodar testes; se jornada: rascunho em tests/e2e/
07  deploy se verde e se não toca o pagar
08  plantar a feature do D+7
09  UM eixo extra (SOCIAL/SEO/CRAWL/…) — ver tasks/pulses.md. Não a lista inteira.
10  se canal existir: 1 post do ship (X+TG juntos quando os dois existirem)
11  linha em PROGRESS.md com tokens_pulso
12  rolar a janela
13  próxima chamada em 24h
```

Se o 05 não aconteceu, não role a janela. Não “compense” com um tweet.

## Janela rolante

Sempre 7 dias à frente. D+7 = próxima ideia. Referral e mint de charges não saem da mesa até existirem.

## Launch (quando publicar)

`launch/heartbeat.sh` + `launch/AGENTS.md`. Depois um agent por CLI, mesmo cérebro (`CEO.md`).
