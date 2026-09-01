# Dois pulsos oficiais (America/Sao_Paulo)

Isto não é diário de pesquisa. **Pesquisa sem publicação = pulso morto de venda.**
Feature sem teste = pulso morto de produto.
**Unittest / fila sem cursor-agent = pulso morto.** `AGENT: off` nunca é SUCCESS.

| Relógio | Nome | Função | Script | Timer UTC |
|---|---|---|---|---|
| **11:30** | venda | 1 publicação real fora do X (blog, comentário, lista) + plantar D+8 de MKT | `launch/sell.sh` → `agent -p --trust --force` | `14:30` |
| **23:30** | produto | 1 feature no ar + unittest + plantar D+8 de produto | `launch/heartbeat.sh` → `agent -p --trust --force` | `02:30` |

Os scripts param no vermelho do unittest **antes** de chamar o agent. Sem binário `agent`/`cursor-agent` no PATH = `PULSE_FAIL` (exit 1).

O unit systemd do pulso precisa de `TimeoutStartSec` longo (1–2h). Default 90s mata o agent.

X **esquenta**. Um post calmo do ship ou da venda. Sem reply farm. Sem Zernio até o warmup. Telegram depois.

Todo fim de pulso planta **duas** tarefas no D+8: uma de produto, uma de venda. A janela nunca acaba num recado.

## 11:30 — venda

```
00  cron 11:30 → launch/sell.sh
01  ler CEO.md + VENUES.md + QUEUE.md
02  track-report (visitas / pay_click)
03  chamar cursor-agent (print + trust + force)
04  UM destino da roleta (não a lista inteira)
05  publicar o link com UTM  OU  gravar a fila se o canal pediu humano
06  RESEARCH.md: o que saiu, não o que “poderia”
07  plantar D+8 de vendas em SALES-7D.md
08  PROGRESS.md (sem PII)
```

Sem agent, sem publicação e sem linha na fila = falhou. Anotar não conta.

## 23:30 — produto

```
00  cron 23:30 → launch/heartbeat.sh
01  CEO.md + PAYMENT.md + HARNESS.md
02  ROADMAP-7D.md
03  unittest. Vermelho = para
04  chamar cursor-agent (print + trust + force)
05  SHIP
06  plantar D+8 de produto
07  sales-watch. CELEBRATE → texto na fila (X no Mac)
08  track-report + tokens_pulso
```

## Como o robô se aprimora

O pulso da manhã **usa** a pesquisa: escolhe o próximo lugar em `VENUES.md`, publica, vê se `utm_content` gerou `visit` no dia seguinte. Se não gerou, mata o canal e planta outro. O da noite faz o mesmo com feature. D+8 é obrigatório nos dois.

Fila: `ceo/QUEUE.md` + `data/sell-queue.jsonl` na VPS. Mac acorda → esgota X. VPS nunca segura cookie de X.
