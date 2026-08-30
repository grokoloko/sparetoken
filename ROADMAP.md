# Roadmap — fechar o MVP

Versão atual: **0.2.8** (relógio: mesma carteira, sem herdar texto).

Ordem fixa. Não pular para skills store, dashboard ou app nativo.

---

## Plano fechado — resume + relógio (web e SSH)

Três camadas. As duas experiências usam as mesmas.

| Camada | O que é | Web | SSH |
|---|---|---|---|
| **Código** | as 5h | `?code=wdtsot-XXXX` | cole o código no Nome (já libera pós-login) |
| **Linha** | minutos daquela sessão | id do chat (`YgU5…`) | `ssh-session-…` |
| **Resume** | reabre o **texto** da linha | `?code=…&resume=<id>` | `ssh -t agent-guest@wdtsot.shop resume <session-id\|uuid>` |

Regras que não negociar:

- `?code=` sozinho = mesma carteira, linha nova, **sem** herdar texto.
- `&resume=` = mesma carteira, **esta** linha. Só aí as bolhas voltam — quando o fio estiver gravado nesse id.
- Clique na lista do relógio = só o balde de tempo. Sem inbox, busca, exportar, reabrir pelo menu.
- SSH novo sem resume = outra linha no mesmo código.
- SSH `resume` = mesma linha + mesmo workspace. Tempo continua do restante. Não ganha hora extra.
- Statusline do terminal = o relógio da web em duas linhas: código, ctx N%, restante, minutos desta linha, N chats, total / 5h.
- Padrão da statusline: `scripts/wdtsot_statusline.py`. O CLI lê `logs/wdtsot.json` (o watch atualiza). Não consultar sqlite de dentro do sandbox.

Na web o relógio não reabre texto. Clique, `?code=` e `&resume=` só escolhem o balde de tempo. SSH `resume` é que devolve o workspace.

---

## 0.2.0 — Pagar, provar, contar horas

Três peças. Nesta ordem.

### 1. Link de pagamento — feito

Não construir gateway do zero. Um link (Pix / Mercado Pago / equivalente) para **R$5 = 5h**.

- Um SKU só. Sem plano, sem recorrência.
- Na landing, o card R$5 deixa de ser “checkout em alpha” e vira o link real.
- Cada clique gera um `purchases` row: `status=pending`, `amount_brl=5`, `seconds_purchased=18000`, `payment_reference=…`.
- Webhook ou retorno do provedor marca `paid`. **Nunca** marcar `paid` sem evidência.
- Sem crédito fantasma se o pagamento falhar ou for abandonado.

Aceitável no 0.2.0: link hospedado do provedor + webhook mínimo.  
Não aceitável: botão que “simula” pagamento.

### 2. Identificação fallback de quem pagou — feito

O cookie anônimo não basta para “isso é meu bloco de 5h” depois que a pessoa fecha o browser ou abre o SSH.

Fallback simples, nesta prioridade:

1. **E-mail ou WhatsApp** já coletados no gate SSH (e, no web, um campo curto no retorno do pagamento).
2. **Código do bloco** — um token curto (ex. `wdtsot-7K2M`) mostrado depois do pagamento, gravado em `purchases.payment_reference` / tabela de entitlement.
3. Cookie, se ainda existir — só como atalho, não como fonte da verdade.

Quem chega com e-mail/WhatsApp/código válido **libera a sessão paga**.  
Mesmo identificador = mesmo `credit_wallets` (o bloco de 18 000s).  
Não criar carteira nova a cada aba.

Isso é o “fallback”: se o cookie sumiu, a pessoa ainda retoma o que comprou.

### 3. Contador de horas + retomar / outra sessão no mesmo bloco — feito no web

A matemática **já existe** em `credits.py`. Falta ligar na vida real.

Relógio (web e, se der, no banner do SSH):

- **usado** = `consumed_seconds` (+ elapsed se status=active)
- **faltando** = `purchased_seconds - usado` → `04:51:32`
- Só anda com sessão **ativa**. Pause / disconnect congela.

Ações do usuário, no mesmo bloco de 5h:

| Ação | Efeito |
|---|---|
| **Retomar** | `ai_sessions.status=active`, continua o mesmo relógio |
| **Pausar** | settle + `paused`. Saldo intacto |
| **Começar outra** | nova `ai_sessions` (chat ou SSH) **desconta o mesmo wallet**. Não é outra compra |
| **Saldo zero** | não inicia. Convite a comprar de novo (mesmo link de R$5) |

Testes obrigatórios (já cobertos em unidade; repetir em integração):

1. Compra 5h, usa 10 min, sai → resta 4h50.
2. Espera um dia desconectado → continua 4h50.
3. Retoma ou abre outra sessão no mesmo bloco → segue de 4h50.
4. Zera → para. Sem uso pago extra.

UI: o artefato de terminal da homepage deixa de ser só decoração — mostra o relógio **real** de quem tem bloco. Quem não pagou continua vendo o mock + as 50 mensagens.

SSH: se possível, imprimir `remaining HH:MM:SS` no hello do `run-agent.sh` e settle no `finalize-session.py`. Cuidado: é infra compartilhada. Backup antes. Não quebrar o gate.

---

## 0.2.9 — Mínimo de segurança (próximo, antes de mais venda)

A superfície pública já gasta o Cursor da VPS. Auditoria operacional fica fora deste git (PII). Não pular o resto disto para Twitter.

Ordem:

1. **WhatsApp libera token.** OTP (Dexter / canal que já temos) antes de `/api/chat` pago **e** antes do agent SSH. Código do bloco sozinho não basta se o link vazou.
2. **Matar ou amarrar as 50 msgs anônimas.** Hoje cada cookie/preview cria uma carteira nova. Ou some o grátis, ou exige WhatsApp até pra 1 prompt.
3. **SSH sem senha vazia.** `agent-guest` + `Accepted none` já autenticou IPs AWS que não são o founder. Gate (nome/WA/email) vem *depois* do login. Auth tem que ser *antes* do agent subir.
4. **`?code=` é segredo.** Não deixar carteira paga em querystring pública sem bind de WhatsApp. Link compartilhado = carteira compartilhada.
5. **`/api/health` sem SSH/modelo.** Crawler não precisa do mapa.
6. **Log de verdade:** `$host` + `$remote_addr` no nginx; app loga `X-Forwarded-For`, não `127.0.0.1`.
7. **Rate na criação de sessão.** Preview do WhatsApp/iMessage não deve mintar 50 msgs.

Não escrever PoC de ataque. Só fechar a porta.

---

## 0.3.0 — DNS + HTTPS canônico

**Feito** para `wdtsot.shop` e `sparetoken.shop` (Let's Encrypt, mesmo app). Túnel trycloudflare aposentado.

Sobra: tratar `sparetoken.shop` como marca; `wdtsot.shop` como alias até o cutover.

---

## Depois do MVP (anotado 2026-08-30 — não agora)

Ordem de foco, sem pular o resto do 0.2.9:

1. **Bot-CEO no Twitter** — e-mail novo, conta nova, sem nome pessoal/empresa. Posta ao vivo o build anônimo do sparetoken.shop. Este é o experimento viral.
2. **Open source** — repo público: [github.com/sparetoken-shop/sparetoken](https://github.com/sparetoken-shop/sparetoken). Sem handle de pessoa. Sem empresa.
3. **Self-evolving agent** até o fundador autônomo buildar o marketplace: ensinar outros founders a instalar o SSH na VPS e compartilhar tokens de CLI (Cursor, Claude Code, Codex, Anthropic, Meta, …). Cada um publica 10+ links conta.vc e vende sessão.
4. **Indicação** — quem divulga sparetoken.shop recebe comissão **diária, autônoma, Pix conta.vc**.
5. **Forks longe** (só depois de ver o viral): skills+tokens, on-prem AI, revenda de API com markup mínimo.

Ainda fora: dashboard, mensalidade, K8s, Redis, segundo banco.

---

## Fora deste recorte imediato

- Marketplace de skills (teaser já está) — volta no item 3 acima
- Cupom / afiliado genérico — o modelo é a indicação Pix, não um SaaS de cupom
- Repo público: [github.com/sparetoken-shop/sparetoken](https://github.com/sparetoken-shop/sparetoken).

---

## Como versionar

- `VERSION` = semver `MAJOR.MINOR.PATCH`
- Cada entrega: bump + parágrafo no `CHANGELOG.md` (Keep a Changelog)
- Tag git `v0.2.0` quando o 0.2.0 estiver testável no ar
- 0.1.x = correção do que já está no ar (chat, nginx, copy)
- 0.2.0 = pagamento + fallback + relógio (esta página)
- 1.0.0 = DNS no ar + pago estável + SSH e web no mesmo bloco, sem túnel improvisado

Mensagem de commit: o **porquê**, em 1–2 frases. Sem “wip” solto no `main` da memória.
