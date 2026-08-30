# sparetoken — contexto para agentes

Você está no MVP **sparetoken** / WDTSOT (*we deserve to share our tokens.*).

Marca: https://sparetoken.shop · alias: https://wdtsot.shop.

**Anonimato inviolável.** Sem founder público. Sem empresa. Sem push em conta pessoal. Leia `.cursor/rules/anonimato.mdc` antes de qualquer git/GitHub/Origin.

1. Leia `PRIVACY.md` (o contrato de prompt e credencial). Depois `README.md` e `ROADMAP.md`.
2. Leia `CHANGELOG.md` + `VERSION` antes de versionar.
3. Não quebre o que está no ar. Não invente pagamento, crédito ou URL.
4. Não escreva exploit/PoC da superfície pública. Só fechar porta. Ver `SECURITY.md`.
5. Memória operacional com PII de cliente **não** mora neste git. Não recriar `MEMORY.md` com telefone, Pix ou e-mail de gente.

Código mínimo. Reuse o que já funciona. Teste de verdade.

## Privacidade (não negociar)

- Prompt do visitante não é produto. Não vender, não publicar, não mostrar para outro visitante.
- Sem prompt escondido que colha chave, cookie, `.env` ou `auth.json`.
- Túnel SSH: não montar `~/.config` inteiro. Só o que o binário do agent precisa. GWS, Wrangler e `~/.ssh` ficam de fora.
- Sessão guest recebe `tunnel/guest-AGENTS.md` como `AGENTS.md` do workspace — regra visível, não um segundo prompt secreto.

## Relógio no SSH (statusline)

O terminal usa o mesmo relógio da web, não um dashboard.

- Script canônico: `scripts/wdtsot_statusline.py` (cópia em `/opt/cursor-agent-tunnel/wdtsot_statusline.py`).
- `run-agent.sh` grava `statusLine` em `cli-config.json` de toda sessão guest.
- Fonte: `logs/wdtsot.json`, atualizado pelo `tunnel-gate.py watch`.
- Tom: `código · GROK 4.6 · ctx N%` / `4h 50 min restantes · 5 min nesta linha · N chats · 9 min / 5h`.
- Não mostrar inbox, custo em dólar, tokens brutos ou path do workspace na statusline.
