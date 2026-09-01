# Launch · track-report

Métricas first-party. Sem pixel de terceiro. Sem PII.

Eventos: `visit` · `pay_click` · `claim_ok`  
Campos: `utm_source/medium/campaign/content` + `code` só se `wdtsot-XXXX`.

0. `GET /api/track/summary` — os mesmos totais, sem UTM, sem código. É o que a landing mostra.
1. `SELECT event, utm_source, utm_content, COUNT(*) FROM track_events GROUP BY 1,2,3`
2. Uma linha em `PROGRESS.md`: visitas, cliques Pix, claims. Sem lista de códigos.
3. Se visit>0 e pay_click=0: o rail da LP não está vendendo — próximo ship é copy, não feature nova.
4. Se UTM de pNNN não aparece: o post não está linkando o canônico. Consertar `POSTS.md`.
