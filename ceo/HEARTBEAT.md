# Dois pulsos oficiais (America/Sao_Paulo)

Isto não é diário de pesquisa. **Pesquisa sem publicação = pulso morto de venda.**  
Feature sem teste = pulso morto de produto.

| Relógio | Nome | Função | Script | Timer UTC |
|---|---|---|---|---|
| **11:30** | venda | 1 publicação real fora do X (blog, comentário, lista) + plantar D+8 de MKT | `launch/sell.sh` | `14:30` |
| **23:30** | produto | 1 feature no ar + unittest + plantar D+8 de produto | `launch/heartbeat.sh` | `02:30` |

X **esquenta**. Um post calmo do ship ou da venda. Sem reply farm. Sem Zernio até o warmup. Telegram depois.

Todo fim de pulso planta **duas** tarefas no D+8: uma de produto, uma de venda. A janela nunca acaba num recado.

## 11:30 — venda

```
00  cron 11:30 → launch/sell.sh
00b Cursor Agent (`run-cursor-agent.sh sell`)
01  ler CEO.md + VENUES.md + QUEUE.md
02  track-report (visitas / pay_click)
03  UM destino da roleta (não a lista inteira)
04  publicar o link com UTM  OU  gravar a fila se o canal pediu humano
05  RESEARCH.md: o que saiu, não o que “poderia”
06  plantar D+8 de vendas em SALES-7D.md
07  PROGRESS.md (sem PII)
07b git-as-sparetoken.sh commit + push-alive se a tree estiver dirty
```

Sem publicação e sem linha na fila = falhou. Anotar não conta.

## 23:30 — produto

```
00  cron 23:30 → launch/heartbeat.sh
01  CEO.md + PAYMENT.md + HARNESS.md
02  ROADMAP-7D.md
03  unittest. Vermelho = para
03b Cursor Agent (`run-cursor-agent.sh heartbeat`) — sem agent o pulso morreu
04  SHIP
04b git-as-sparetoken.sh commit + push-alive se a tree estiver dirty
05  plantar D+8 de produto
06  sales-watch. CELEBRATE → texto na fila (X no Mac)
07  track-report + tokens_pulso
```

## Como o robô se aprimora

O pulso da manhã **usa** a pesquisa: escolhe o próximo lugar em `VENUES.md`, publica, vê se `utm_content` gerou `visit` no dia seguinte. Se não gerou, mata o canal e planta outro. O da noite faz o mesmo com feature. D+8 é obrigatório nos dois.

Fila: `ceo/QUEUE.md` + `data/sell-queue.jsonl` na VPS. Mac acorda → esgota X. VPS nunca segura cookie de X.
